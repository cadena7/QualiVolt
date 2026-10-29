"""QualiVolt: explorador de calidad de energía para Python y Qt."""
import json
import math
import statistics
import sys
from pathlib import Path
from PySide6 import QtWidgets as Q
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QKeySequence, QPainter, QFont, QActionGroup
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
import pyqtgraph as pg
from reader import load_csv, suggested_frequency, channel_value
from binary_reader import load_binary, pair_paths, read_header
from branding import APP_NAME, AUTHOR, APP_VERSION, RELEASE_DATE_LABEL
from typography import apply_ui_font
from appearance import THEMES, apply_palette, style_graph
from study_view import StudyControls, SpectrumView


class ChannelTree(Q.QTreeWidget):
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            item = self.itemAt(event.position().toPoint())
            if item is not None and item.data(0, Qt.UserRole):
                item.setSelected(not item.isSelected())
            event.accept()
            return
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        event.accept()


class Window(Q.QMainWindow):
    def __init__(self):
        super().__init__()
        apply_ui_font(Q.QApplication.instance())
        self.setWindowTitle(f'{APP_NAME} · Calidad de energía')
        self.resize(1250, 780)
        self.data = None
        self.interval = None
        self.project_notes = ''
        self.extra_graphs = []
        self.cursor_lines = []
        self.plotted_channels = []
        self.settings = QSettings(QSettings.defaultFormat(), QSettings.UserScope, 'QualiVolt', 'QualiVolt')
        self.theme = self.settings.value('appearance/theme', 'light')
        if self.theme not in THEMES:
            self.theme = 'light'
        pg.setConfigOptions(antialias=True)
        file_menu = self.menuBar().addMenu('&Archivo')
        def action(menu, text, callback, shortcut=None):
            item = menu.addAction(text, callback)
            if shortcut:
                item.setShortcut(shortcut)
            return item
        action(file_menu, 'Abrir grabación…', self.open_file, QKeySequence.Open)
        action(file_menu, 'Abrir proyecto…', self.open_project)
        self.project_save_action = action(file_menu, 'Guardar proyecto…', self.save_project)
        self.close_action = action(file_menu, 'Cerrar grabación', self.close_recording, QKeySequence.Close)
        file_menu.addSeparator()
        self.config_action = action(file_menu, 'Configuración del proyecto…', self.configure)
        self.save_action = action(file_menu, 'Guardar configuración…', self.save_config, QKeySequence.Save)
        export_menu = file_menu.addMenu('Exportar')
        self.report_action = action(export_menu, 'Informe PDF…', self.create_report)
        self.png_action = action(export_menu, 'Gráfica visible en PNG…', self.export_graph_png)
        self.channels_png_action = action(export_menu, 'Un PNG por canal…', self.export_channels_png)
        file_menu.addSeparator()
        self.preview_action = action(file_menu, 'Vista previa de impresión…', self.preview_graph)
        self.print_action = action(file_menu, 'Imprimir gráfica…', self.print_graph, QKeySequence.Print)
        file_menu.addSeparator()
        action(file_menu, 'Salir', self.close, QKeySequence.Quit)
        appearance_menu = self.menuBar().addMenu('Apariencia')
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_actions = {}
        for key, title in [('light', 'Tema claro'), ('dark', 'Tema oscuro')]:
            item = appearance_menu.addAction(title)
            item.setCheckable(True)
            self.theme_group.addAction(item)
            self.theme_actions[key] = item
            item.triggered.connect(lambda checked=False, theme=key: self.set_theme(theme))
        help_menu = self.menuBar().addMenu('Ayuda')
        help_menu.addAction('Guía de uso', self.show_guide)
        help_menu.addSeparator()
        help_menu.addAction('Acerca de · About', self.show_about)
        root = Q.QWidget()
        layout = Q.QVBoxLayout(root)
        bar = Q.QHBoxLayout()
        for title, callback in [('Abrir grabación', self.open_file), ('Configuración', self.configure), ('Guardar configuración…', self.save_config), ('Generar informe', self.create_report), ('Guía de uso', self.show_guide)]:
            button = Q.QPushButton(title)
            button.clicked.connect(callback)
            bar.addWidget(button)
        layout.addLayout(bar)
        self.info = Q.QLabel('Abre una grabación HED/PER del PQA820 o una exportación CSV para comenzar.')
        self.info.setTextFormat(Qt.PlainText)
        self.info.setWordWrap(True)
        layout.addWidget(self.info)
        split = Q.QSplitter()
        panel = Q.QWidget()
        left = Q.QVBoxLayout(panel)
        self.search = Q.QLineEdit()
        self.search.setPlaceholderText('Buscar canal: thd, V1, har05…')
        self.search.textChanged.connect(self.filter_channels)
        left.addWidget(self.search)
        self.channels = ChannelTree()
        self.channels.setHeaderHidden(True)
        self.channels.setSelectionMode(Q.QAbstractItemView.ExtendedSelection)
        self.channels.itemSelectionChanged.connect(self.plot)
        left.addWidget(self.channels)
        selection_help = Q.QLabel('Selección múltiple: Ctrl + clic (Cmd en macOS), o clic derecho para añadir/quitar un canal sin perder los demás.')
        selection_help.setWordWrap(True)
        left.addWidget(selection_help)
        split.addWidget(panel)
        self.graph = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem(utcOffset=0)})
        self.graph.setBackground('#142031')
        self.graph.showGrid(x=True, y=True, alpha=.2)
        self.graph.addLegend()
        self.graph.setLabel('bottom', 'Fecha y hora local del registro')
        self.graph.scene().sigMouseMoved.connect(lambda pos: self.track_cursor(self.graph,pos))
        graph_panel = Q.QWidget()
        graph_layout = Q.QVBoxLayout(graph_panel)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_toolbar = Q.QHBoxLayout()
        graph_toolbar.addWidget(Q.QLabel('Gráfica de canales seleccionados'))
        graph_toolbar.addStretch()
        self.export_png_button = Q.QToolButton()
        self.export_png_button.setText('Exportar PNG')
        self.export_png_button.setPopupMode(Q.QToolButton.MenuButtonPopup)
        self.export_png_button.clicked.connect(self.export_graph_png)
        png_menu = Q.QMenu(self.export_png_button)
        png_menu.addAction('Gráfica visible', self.export_graph_png)
        png_menu.addAction('Un PNG por canal seleccionado…', self.export_channels_png)
        self.export_png_button.setMenu(png_menu)
        self.export_png_button.setEnabled(False)
        graph_toolbar.addWidget(self.export_png_button)
        graph_layout.addLayout(graph_toolbar)
        self.study_controls = StudyControls(self)
        graph_layout.addWidget(self.study_controls)
        self.cursor_label = Q.QLabel('Mueve el cursor para consultar valores sincronizados.')
        self.cursor_label.setWordWrap(True)
        graph_layout.addWidget(self.cursor_label)
        self.chart_tabs = Q.QTabWidget()
        trend_panel = Q.QWidget()
        self.trend_layout = Q.QVBoxLayout(trend_panel)
        self.trend_layout.setContentsMargins(0,0,0,0)
        self.trend_layout.addWidget(self.graph,1)
        scroll = Q.QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(trend_panel)
        self.chart_tabs.addTab(scroll,'Tendencias sincronizadas')
        self.spectrum = SpectrumView(self)
        self.chart_tabs.addTab(self.spectrum,'Espectro armónico')
        graph_layout.addWidget(self.chart_tabs, 1)
        split.addWidget(graph_panel)
        split.setSizes([310, 900])
        layout.addWidget(split, 1)
        self.summary = Q.QLabel('Selecciona varios canales con Ctrl/Cmd; cada unidad tendrá su panel sincronizado.')
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.footer = Q.QLabel(
            f'{APP_NAME} · Créditos: {AUTHOR} · Versión {APP_VERSION} · Fecha de versión: {RELEASE_DATE_LABEL}')
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setWordWrap(True)
        self.footer.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.footer.setContentsMargins(8, 8, 8, 4)
        layout.addWidget(self.footer)
        self.setCentralWidget(root)
        self.set_theme(self.theme, persist=False)
        self.update_file_actions()

    def set_theme(self, theme, persist=True):
        self.theme = theme
        apply_palette(Q.QApplication.instance(), theme)
        self.theme_actions[theme].setChecked(True)
        style_graph(self.graph, theme)
        for graph in self.extra_graphs:
            style_graph(graph,theme)
        self.spectrum.refresh()
        if persist:
            self.settings.setValue('appearance/theme', theme)

    def track_cursor(self, graph, position):
        if not self.data or not graph.sceneBoundingRect().contains(position):
            return
        from bisect import bisect_left
        from datetime import timezone
        point=graph.plotItem.vb.mapSceneToView(position)
        headers,times,rows=self.scoped_data()
        stamps=[t.replace(tzinfo=timezone.utc).timestamp() for t in times]
        if not stamps:return
        index=min(bisect_left(stamps,point.x()),len(stamps)-1)
        if index and abs(stamps[index-1]-point.x())<abs(stamps[index]-point.x()):index-=1
        for line in self.cursor_lines:line.setPos(stamps[index])
        values=[]
        for name in self.plotted_channels[:5]:
            value=channel_value(name,rows[index][headers.index(name)])
            values.append(f'{name}: {value:.5g}' if math.isfinite(value) else f'{name}: no definido')
        self.cursor_label.setText(f'{times[index]} · '+' | '.join(values))

    def visible_graph(self):
        return self.spectrum.graph if self.chart_tabs.currentIndex()==1 else self.graph

    def update_file_actions(self):
        for item in (self.close_action, self.config_action, self.save_action, self.report_action, self.project_save_action):
            item.setEnabled(self.data is not None)
        for item in (self.png_action, self.channels_png_action, self.print_action, self.preview_action):
            item.setEnabled(bool(self.plotted_channels))

    def close_recording(self):
        self.data = None
        self.interval = None
        self.project_notes = ''
        self.study_controls.setEnabled(False)
        for graph in self.extra_graphs:
            self.trend_layout.removeWidget(graph);graph.close();graph.deleteLater()
        self.extra_graphs=[]
        self.spectrum.refresh()
        self.plotted_channels = []
        self.config = {}
        self.channels.clear()
        self.search.clear()
        self.graph.clear()
        self.graph.setLabel('left', '')
        self.export_png_button.setEnabled(False)
        self.setWindowTitle(f'{APP_NAME} · Calidad de energía')
        self.info.setText('Abre una grabación HED/PER del PQA820 o una exportación CSV para comenzar.')
        self.summary.setText('Selecciona varios canales con Ctrl/Cmd; cada unidad tendrá su panel sincronizado.')
        self.update_file_actions()

    def paint_graph(self, printer):
        from pyqtgraph.exporters import ImageExporter
        from PySide6.QtCore import QRectF
        exporter = ImageExporter(self.visible_graph().plotItem)
        exporter.parameters()['width'] = 2400
        image = exporter.export(toBytes=True)
        painter = QPainter(printer)
        if not painter.isActive():
            raise OSError('No se pudo iniciar la impresión.')
        try:
            viewport = painter.viewport()
            factor = viewport.width()/720
            painter.scale(factor, factor)
            height = viewport.height()/factor
            title_font = QFont(self.font().family(), 14, QFont.DemiBold)
            title_font.setPixelSize(18)
            painter.setFont(title_font)
            painter.drawText(QRectF(0,0,720,65), Qt.AlignLeft | Qt.TextWordWrap,
                self.config.get('titulo_proyecto') or self.path.stem)
            available = QRectF(0,75,720,height-125)
            size = image.size().scaled(int(available.width()), int(available.height()), Qt.KeepAspectRatio)
            painter.drawImage(QRectF((720-size.width())/2,75,size.width(),size.height()), image)
            footer_font = QFont(self.font().family(), 8)
            footer_font.setPixelSize(11)
            painter.setFont(footer_font)
            painter.drawText(QRectF(0,height-35,720,30), Qt.AlignCenter,
                f'{APP_NAME} · {AUTHOR} · v{APP_VERSION}')
        finally:
            painter.end()

    def print_graph(self):
        if not self.plotted_channels:
            return
        printer = QPrinter(QPrinter.HighResolution)
        printer.setDocName(self.config.get('titulo_proyecto') or self.path.stem)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle('Imprimir gráfica visible')
        if dialog.exec() == Q.QDialog.Accepted:
            try:
                self.paint_graph(printer)
            except Exception as exc:
                Q.QMessageBox.critical(self, 'No se pudo imprimir', str(exc))

    def preview_graph(self):
        if not self.plotted_channels:
            return
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintPreviewDialog(printer, self)
        dialog.setWindowTitle('Vista previa · gráfica visible')
        dialog.resize(950, 750)
        def paint(printer):
            try:
                self.paint_graph(printer)
            except Exception as exc:
                Q.QMessageBox.critical(self, 'No se pudo preparar la impresión', str(exc))
        dialog.paintRequested.connect(paint)
        dialog.exec()

    def export_graph_png(self):
        if not self.plotted_channels:
            return
        target, _ = Q.QFileDialog.getSaveFileName(self, 'Exportar gráfica visible',
            str(self.path.with_suffix('.graph.png')), 'Imagen PNG (*.png)')
        if not target:
            return
        if not target.lower().endswith('.png'):
            target += '.png'
        try:
            self.save_plot_png(self.visible_graph().plotItem, target)
        except Exception as exc:
            Q.QMessageBox.critical(self, 'No se pudo exportar la gráfica', str(exc))
            return
        Q.QMessageBox.information(self, 'PNG guardado', f'Gráfica guardada en:\n{target}')

    @staticmethod
    def save_plot_png(plot_item, target):
        from pyqtgraph.exporters import ImageExporter
        exporter = ImageExporter(plot_item)
        exporter.parameters()['width'] = 2400
        exporter.parameters()['antialias'] = True
        result = exporter.export(toBytes=True)
        if result.isNull() or not result.save(str(target), 'PNG'):
            raise OSError('No se pudo guardar la imagen PNG.')

    def export_channels_png(self):
        if not self.plotted_channels:
            return
        folder = Q.QFileDialog.getExistingDirectory(self, 'Guardar un PNG por canal', str(self.path.parent))
        if not folder:
            return
        import re
        from datetime import timezone
        headers, times, rows = self.data
        x = [t.replace(tzinfo=timezone.utc).timestamp() for t in times]
        current_range = self.graph.viewRange()[0]
        saved = 0
        try:
            for name in self.plotted_channels:
                graph = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem(utcOffset=0)})
                try:
                    graph.resize(1100, 650)
                    graph.setBackground('#142031')
                    graph.setTitle(name)
                    graph.showGrid(x=True, y=True, alpha=.2)
                    graph.setLabel('bottom', 'Fecha y hora local del registro')
                    unit = name.split(' [')[-1].rstrip(']') if ' [' in name else 'adimensional'
                    graph.setLabel('left', unit)
                    column = headers.index(name)
                    graph.plot(x, [channel_value(name,row[column]) for row in rows], pen=pg.mkPen('#66c4ff', width=1.5), connect='finite')
                    graph.setXRange(*current_range, padding=0)
                    graph.plotItem.vb.enableAutoRange(axis='y', enable=True)
                    graph.plotItem.vb.updateAutoRange()
                    style_graph(graph, self.theme)
                    # Mantener exportaciones previas; numerar cuando se repite un nombre.
                    stem = re.sub(r'[^\w.-]+', '_', f'{self.path.stem}_{name}').strip('_')
                    target = Path(folder)/f'{stem}.png'
                    index = 2
                    while target.exists():
                        target = Path(folder)/f'{stem}_{index}.png'
                        index += 1
                    self.save_plot_png(graph.plotItem, target)
                    saved += 1
                finally:
                    graph.close()
        except Exception as exc:
            Q.QMessageBox.critical(self, 'Exportación interrumpida', f'Se guardaron {saved} imágenes.\n{exc}')
            return
        Q.QMessageBox.information(self, 'Gráficas guardadas', f'Se guardaron {saved} imágenes PNG en:\n{folder}')

    def create_report(self):
        if not self.data:
            Q.QMessageBox.information(self, 'Informe PDF', 'Abre primero una grabación.')
            return
        from analysis_report import AUTHOR, export_report
        dialog = Q.QDialog(self)
        dialog.setWindowTitle('Informe automático de calidad de la energía')
        layout = Q.QFormLayout(dialog)
        site = Q.QLineEdit(self.config.get('titulo_proyecto') or self.path.stem)
        site.setMaxLength(120)
        responsible = Q.QLineEdit(AUTHOR)
        responsible.setMaxLength(100)
        point = Q.QComboBox()
        point.addItems(['Salida de transformador', 'Tablero principal', 'Tablero secundario', 'Carga individual'])
        point.setCurrentText(self.config.get('punto_medicion','Salida de transformador'))
        layout.addRow('Título de proyecto', site)
        layout.addRow('Responsable del análisis', responsible)
        layout.addRow('Punto de medición', point)
        note = Q.QLabel('Incluye resumen, tendencias, THD, armónicos y referencias IEEE/ANSI/México.\n'
            'Los créditos del programa siempre incluyen a Edgar Omar Cadena Zepeda.\n'
            'El análisis es descriptivo: no declara cumplimiento normativo.')
        note.setWordWrap(True)
        layout.addRow(note)
        buttons = Q.QDialogButtonBox(Q.QDialogButtonBox.Ok | Q.QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        if not dialog.exec():
            return
        self.config['titulo_proyecto'] = site.text().strip() or self.path.stem
        self.config['punto_medicion'] = point.currentText()
        self.update_info()
        import tempfile
        from report_preview import ReportPreview
        try:
            with tempfile.TemporaryDirectory(prefix='qualivolt-report-') as folder:
                temporary = Path(folder) / 'report.pdf'
                Q.QApplication.setOverrideCursor(Qt.WaitCursor)
                try:
                    export_report(temporary, self.scoped_data(), self.config, self.path,
                        {'sitio':site.text(), 'responsable':responsible.text(), 'punto':point.currentText()})
                finally:
                    Q.QApplication.restoreOverrideCursor()
                preview = ReportPreview(temporary, self.path.with_suffix('.report.pdf'), self)
                try:
                    preview.exec()
                finally:
                    from shiboken6 import delete
                    preview.view.setDocument(None)
                    preview.document.close()
                    delete(preview)
        except Exception as exc:
            Q.QMessageBox.critical(self, 'No se pudo preparar el informe', str(exc))

    def show_about(self):
        dialog = Q.QDialog(self)
        dialog.setWindowTitle(f'Acerca de {APP_NAME} · HT PQA820')
        dialog.resize(670, 630)
        layout = Q.QVBoxLayout(dialog)
        content = Q.QTextBrowser()
        content.setOpenExternalLinks(True)
        content.setHtml(
            f'<h2>{APP_NAME}</h2>'
            '<p>Lector y analizador de archivos de mediciones del instrumento de '
            'calidad de la energía <b>HT Instruments PQA820</b>.</p>'
            '<p>Permite visualizar y analizar voltajes, corrientes, frecuencia, potencias, '
            'distorsión armónica total (THD) y armónicos individuales.</p>'
            '<p><b>Créditos</b><br>Edgar Omar Cadena Zepeda</p>'
            '<p>Desarrollado en Python para Windows, macOS y Ubuntu.</p>'
            '<p>Lee exportaciones CSV de TopView y grabaciones HED/PER compatibles del HT PQA820 '
            'directamente, sin necesidad de abrir TopView.</p>'
            '<h3>Especificaciones del instrumento HT PQA820</h3>'
            '<ul>'
            '<li>Análisis de sistemas monofásicos y trifásicos.</li>'
            '<li>Tensión CA/CC: máximo 415 V ±10 %, según el fabricante.</li>'
            '<li>Corriente CA/CC: máximo 1000 A; depende de la pinza utilizada.</li>'
            '<li>Armónicos de tensión y corriente hasta el orden 49 y THD.</li>'
            '<li>Potencia y energía activa, reactiva y aparente; factor de potencia y cos φ.</li>'
            '<li>Corriente de neutro y desequilibrio de tensión.</li>'
            '<li>Anomalías de tensión: resolución de 10 ms a 50 Hz.</li>'
            '<li>Hasta 383 parámetros simultáneos.</li>'
            '<li>Período de integración seleccionable: 5 segundos a 60 minutos.</li>'
            '<li>Memoria interna: 8 MB; autonomía de registro orientativa de 30 días '
            'con integración de 10 minutos y máximo de parámetros.</li>'
            '<li>Comunicación USB y Wi-Fi; categoría de medición CAT IV 300 V.</li>'
            '</ul>'
            '<p>Estas características corresponden al instrumento. Las funciones disponibles '
            'en esta app dependen de los datos disponibles y del formato compatible.</p>'
            '<p><a href="https://www.ht-instruments.com/en/products/power-quality-analyzers/wifi/pqa820/">'
            'Sitio oficial de HT Instruments · PQA820</a></p>'
        )
        layout.addWidget(content)
        buttons = Q.QDialogButtonBox(Q.QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def show_guide(self):
        dialog = Q.QDialog(self)
        dialog.setWindowTitle(f'Guía de uso · {APP_NAME}')
        dialog.resize(720, 610)
        layout = Q.QVBoxLayout(dialog)
        text = Q.QTextBrowser()
        text.setHtml('''
            <h2>Guía de uso</h2>
            <h3>1. Abrir una grabación</h3>
            <p>Pulsa <b>Abrir grabación</b> y selecciona el archivo HED del HT PQA820.
            Para un CSV de TopView, cambia el filtro del diálogo a CSV. Para binarios, conserva HED y PER
            con el mismo nombre en la misma carpeta. No se requiere un CSV acompañante.
            Los originales se conservan sin cambios.</p>
            <p>La app muestra los canales disponibles de la grabación, sus fechas
            y el intervalo entre registros.</p>
            <h3>2. Validar el sistema</h3>
            <p>Revisa la frecuencia nominal (50 o 60 Hz), el tipo de conexión,
            la referencia de las mediciones y la tensión nominal del sistema. La frecuencia nominal
            del análisis inicia en <b>60 Hz</b> por la configuración de trabajo del usuario,
            aunque el instrumento pueda mantener su ajuste de fábrica en 50 Hz.
            La frecuencia medida se conserva sin cambios. El valor inicial de <b>220 V</b>
            debe confirmarse para cada instalación. En sistemas trifásicos, el nominal
            del sistema es fase-fase, aunque las mediciones sean fase-neutro.
            En monofásico puedes elegir nominal fase-neutro o fase-fase.
            La referencia de las mediciones es un dato independiente.</p>
            <p>Selecciona una tensión común o escribe un valor personalizado.
            Las relaciones TC/TP solo se guardan como metadatos: no reescalan el CSV.
            Puedes volver a este diálogo con <b>Configuración</b>.</p>
            <h3>3. Elegir canales</h3>
            <p>Expande los grupos por función: voltajes promedio, corrientes de fases
            y neutro, THD de corriente y voltaje, frecuencia y potencias.
            Al final encontrarás <b>Todos los canales</b>.</p>
            <p>Busca por nombre o función, por ejemplo <b>V1</b>, <b>THD</b> o <b>har05</b>.
            Usa Ctrl (o Cmd según la plataforma) para seleccionar varios canales
            de distintas unidades: cada unidad tendrá su panel sincronizado. Avg es promedio, Max es máximo y Min es mínimo.</p>
            <h3>4. Explorar las gráficas</h3>
            <p>Usa la rueda del ratón para acercar o alejar y arrastra para desplazarte.
            El menú contextual de la gráfica ofrece opciones de visualización.
            Debajo aparecen mínimo, media y máximo de cada canal seleccionado
            para el intervalo aplicado. Usa Aplicar o Usar zoom para actualizar el análisis.</p>
            <p>Los THD están en porcentaje. Los armónicos individuales conservan
            su amplitud en A o V. Las horas corresponden al reloj del equipo,
            sin conversión de zona horaria. Los factores de potencia no definidos
            se muestran como huecos en las gráficas y no participan en sus estadísticas.</p>
            <p>En la parte superior de la gráfica, pulsa <b>Exportar PNG</b> para guardar
            la vista actual con sus canales y zoom. La flecha del botón ofrece
            <b>Un PNG por canal seleccionado</b>, para guardar imágenes individuales
            del mismo intervalo visible. Las imágenes se exportan a 2400 píxeles de ancho.</p>
            <h3>5. Guardar la configuración</h3>
            <p>Pulsa <b>Guardar configuración…</b> para guardar un archivo JSON separado.
            La recarga automática de ese archivo todavía no está implementada.</p>
            <p>Las series agregadas del CSV no permiten reconstruir formas de onda
            ni eventos breves que no se hayan exportado.</p>
            <h3>6. Exportar un informe PDF</h3>
            <p>Al abrir una grabación, escribe el <b>Título de proyecto</b> en la configuración.
            Puedes modificarlo después con <b>Configuración</b>. Se utiliza como título del informe
            y se guarda junto con los ajustes al exportar la configuración JSON.</p>
            <p>Pulsa <b>Informe PDF</b>, revisa el título, responsable y punto de medición,
            y abre la vista previa integrada. Ahí puedes recorrer las páginas, ajustar el zoom,
            guardar el PDF o imprimirlo. Incluye tus créditos, tendencias, THD, espectros
            armónicos y un resumen automático local. Evalúa el intervalo aplicado, o toda la grabación si pulsas Todo.
            Las referencias IEEE, ANSI y Código de Red se explican con sus limitaciones;
            no se emite un dictamen de cumplimiento. En el reporte se excluyen valores
            negativos y no finitos de las magnitudes no negativas; los originales no cambian.</p>
        ''')
        layout.addWidget(text)
        buttons = Q.QDialogButtonBox(Q.QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def open_file(self):
        path, _ = Q.QFileDialog.getOpenFileName(self, 'Abrir cabecera HED · requiere su PER en la misma carpeta', '', 'Grabación PQA820 (*.HED *.hed);;Exportación TopView CSV (*.csv *.CSV)')
        if not path:
            return
        try:
            data = load_csv(path) if Path(path).suffix.lower() == '.csv' else load_binary(path)
            system = None
            if Path(path).suffix.lower() != '.csv':
                system = read_header(pair_paths(path)[0]).get('sistema_sugerido')
        except Exception as exc:
            Q.QMessageBox.critical(self, 'No se pudo abrir', str(exc))
            return
        self.data, self.path = data, Path(path)
        self.interval = None
        self.project_notes = ''
        self.study_controls.load()
        self.config = {'titulo_proyecto': self.path.stem, 'frecuencia_hz': 60, 'sistema': system or 'Sin confirmar', 'tension_nominal_v': 220, 'referencia': 'Fase-neutro', 'referencia_nominal': 'Fase-fase' if system else 'Sin confirmar', 'relacion_tc': 1, 'relacion_tp': 1}
        self.configure()
        self.populate_channels(data[0])
        self.filter_channels(self.search.text())
        self.update_info()

    def populate_channels(self, headers):
        groups = [
            ('Voltajes promedio · fase-neutro', lambda c: c in [f'V{i}_Avg [V]' for i in (1, 2, 3)]),
            ('Voltajes promedio · fase-fase', lambda c: c in [f'V{i}_Avg [V]' for i in ('12', '23', '31')]),
            ('Corriente de consumo · fases y neutro', lambda c: c in [f'I{i}_Avg [A]' for i in ('1', '2', '3', 'n')]),
            ('Distorsión total de corriente · THD (%)', lambda c: c.startswith('thdI')),
            ('Distorsión total de voltaje · THD (%)', lambda c: c.startswith('thdV')),
            ('Frecuencia promedio', lambda c: c.startswith('freq_Avg')),
            ('Potencia activa promedio', lambda c: c.startswith(('Pt', 'P1', 'P2', 'P3')) and '_Avg [W]' in c),
            ('Factor de potencia promedio', lambda c: c.startswith(('Pf', 'dpf')) and '_Avg' in c),
            ('Desequilibrio promedio', lambda c: c.startswith('u2_Avg')),
            ('Armónicos de corriente · amplitud (A)', lambda c: c.startswith('har') and '_Avg [A]' in c),
            ('Armónicos de voltaje · amplitud (V)', lambda c: c.startswith('har') and '_Avg [V]' in c),
            ('Energías acumuladas' + (' (calculadas)' if self.path.suffix.lower() != '.csv' else ''), lambda c: c.startswith(('Ea','Er','Es')) and '_Avg [' in c),
            ('Todos los canales · lista completa', lambda c: True),
        ]
        self.channels.blockSignals(True)
        self.channels.clear()
        first = None
        for index, (label, matches) in enumerate(groups):
            names = [c for c in headers if matches(c)]
            if not names:
                continue
            group = Q.QTreeWidgetItem(self.channels, [f'{label} ({len(names)})'])
            group.setFlags(group.flags() & ~Qt.ItemIsSelectable)
            for name in names:
                leaf = Q.QTreeWidgetItem(group, [name])
                leaf.setData(0, Qt.UserRole, name)
                if first is None:
                    first = leaf
            group.setExpanded(index < 6)
        self.channels.blockSignals(False)
        if first:
            self.channels.setCurrentItem(first)

    def update_info(self):
        h, t, v = self.data
        intervals = [(b-a).total_seconds() for a,b in zip(t,t[1:])]
        period = f'{statistics.median(intervals):g} s' if intervals else 'sin determinar'
        source = 'Archivo CSV' if self.path.suffix.lower() == '.csv' else 'Grabación PQA820'
        title = self.config.get('titulo_proyecto') or self.path.stem
        self.setWindowTitle(f'{APP_NAME} · {title}')
        self.info.setText(f'Proyecto: {title}\n{self.path.name}\n{source} · {len(t):,} registros · {len(h)} canales · {t[0]} → {t[-1]} · intervalo mediano {period}\nConfiguración: {self.config}')

    def configure(self):
        if not self.data:
            return
        dialog = Q.QDialog(self)
        dialog.setWindowTitle('Validar sistema analizado')
        form = Q.QFormLayout(dialog)
        project_title = Q.QLineEdit(self.config.get('titulo_proyecto') or self.path.stem)
        project_title.setMaxLength(120)
        project_title.setPlaceholderText('Nombre del sitio o estudio')
        form.addRow('Título de proyecto', project_title)
        measured_hint = suggested_frequency(self.data[0], self.data[2])
        measured_text = f'Referencia aproximada según mediciones: {measured_hint} Hz.' if measured_hint else 'Referencia de frecuencia medida no disponible.'
        note = Q.QLabel('Nominal del análisis: 60 Hz por defecto, editable a 50 Hz.\n'
            'Es independiente del ajuste del instrumento, que puede quedar en 50 Hz.\n'
            + measured_text + '\n'
            '220 V nominal y mediciones fase-neutro son valores iniciales, no datos de cabecera.\n'
            'En trifásico, el nominal del sistema es fase-fase.\n'
            'Las relaciones se guardan como metadatos; no reescalan las mediciones.')
        form.addRow(note)
        fields = {}
        for key, label, options in [('frecuencia_hz', 'Frecuencia nominal del análisis (Hz)', ['Sin confirmar', '50', '60']), ('sistema', 'Sistema', ['Sin confirmar', 'Monofásico', 'Trifásico 3 hilos', 'Trifásico 4 hilos']), ('referencia', 'Referencia de las mediciones', ['Fase-neutro', 'Fase-fase']), ('referencia_nominal', 'Referencia del nominal del sistema', ['Sin confirmar', 'Fase-neutro', 'Fase-fase'])]:
            widget = Q.QComboBox()
            widget.addItems(options)
            widget.setCurrentText(str(self.config.get(key)) if self.config.get(key) is not None else 'Sin confirmar')
            fields[key] = widget
            form.addRow(label, widget)
        presets = Q.QComboBox()
        presets.addItems(['Personalizado', '110', '115', '120', '127', '208', '220', '230', '240', '277', '380', '400', '415', '440', '480', '600', '690'])
        nominal_text = f'{self.config["tension_nominal_v"]:g}'
        presets.setCurrentText(nominal_text if presets.findText(nominal_text) >= 0 else 'Personalizado')
        form.addRow('Tensiones nominales comunes (V)', presets)
        for key, label in [('tension_nominal_v', 'Tensión nominal del sistema (V); 0 = pendiente'), ('relacion_tc', 'Relación TC (primario/secundario)'), ('relacion_tp', 'Relación TP (primario/secundario)')]:
            widget = Q.QDoubleSpinBox()
            widget.setDecimals(3)
            widget.setRange(0 if key == 'tension_nominal_v' else .001, 1000000)
            widget.setValue(self.config[key])
            fields[key] = widget
            form.addRow(label, widget)
        def apply_preset(text):
            if text != 'Personalizado':
                fields['tension_nominal_v'].setValue(float(text))
        def sync_preset(value):
            text = f'{value:g}'
            presets.blockSignals(True)
            presets.setCurrentText(text if presets.findText(text) >= 0 else 'Personalizado')
            presets.blockSignals(False)
        presets.currentTextChanged.connect(apply_preset)
        fields['tension_nominal_v'].valueChanged.connect(sync_preset)
        nominal_hint = Q.QLabel()
        nominal_hint.setWordWrap(True)
        form.addRow(nominal_hint)
        def sync_system(system):
            reference = fields['referencia_nominal']
            previous = reference.currentText()
            reference.clear()
            if system.startswith('Trifásico'):
                reference.addItem('Fase-fase')
                reference.setEnabled(False)
                nominal_hint.setText('El nominal corresponde a fase-fase. La referencia de las mediciones se conserva por separado; no se convierten ni reescalan sus valores.')
            elif system == 'Monofásico':
                reference.addItems(['Fase-neutro', 'Fase-fase'])
                reference.setCurrentText(previous if previous in ('Fase-neutro', 'Fase-fase') else 'Fase-neutro')
                reference.setEnabled(True)
                nominal_hint.setText('Selecciona si el nominal monofásico corresponde a fase-neutro o fase-fase.')
            else:
                reference.addItem('Sin confirmar')
                reference.setEnabled(False)
                nominal_hint.setText('Selecciona el sistema para definir la referencia de su tensión nominal.')
        fields['sistema'].currentTextChanged.connect(sync_system)
        sync_system(fields['sistema'].currentText())
        buttons = Q.QDialogButtonBox(Q.QDialogButtonBox.Ok | Q.QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec():
            self.config['titulo_proyecto'] = project_title.text().strip() or self.path.stem
            for key, widget in fields.items():
                self.config[key] = widget.currentText() if isinstance(widget, Q.QComboBox) else widget.value()
        self.update_info()

    def scoped_data(self):
        if not self.interval:
            return self.data
        headers,times,rows=self.data
        pairs=[(t,r) for t,r in zip(times,rows) if self.interval[0]<=t<=self.interval[1]]
        return headers,[t for t,r in pairs],[r for t,r in pairs]

    def save_project(self):
        if not self.data:
            return
        from project import save_project
        notes,accepted=Q.QInputDialog.getMultiLineText(self,'Notas del proyecto','Notas del estudio',self.project_notes)
        if not accepted:
            return
        self.project_notes=notes
        path,_=Q.QFileDialog.getSaveFileName(self,'Guardar proyecto',str(self.path.with_suffix('.qvp')),'Proyecto QualiVolt (*.qvp)')
        if path:
            if not path.lower().endswith('.qvp'): path += '.qvp'
            try:
                save_project(path,self.path,self.config,self.plotted_channels,self.interval,self.project_notes)
            except Exception as exc:
                Q.QMessageBox.critical(self,'No se pudo guardar el proyecto',str(exc))

    def open_project(self):
        from project import read_project
        path,_=Q.QFileDialog.getOpenFileName(self,'Abrir proyecto','','Proyecto QualiVolt (*.qvp)')
        if not path:
            return
        try:
            content=read_project(path)
            source=content['source']
            data=load_csv(source) if source.suffix.lower()=='.csv' else load_binary(source)
            interval=content.get('interval')
            if interval and not any(interval[0]<=t<=interval[1] for t in data[1]):
                raise ValueError('El intervalo guardado no contiene mediciones.')
            required={'frecuencia_hz','sistema','tension_nominal_v','referencia','referencia_nominal','relacion_tc','relacion_tp'}
            if not required.issubset(content['config']):
                raise ValueError('Faltan ajustes del sistema en el proyecto.')
        except Exception as exc:
            Q.QMessageBox.critical(self,'No se pudo abrir el proyecto',str(exc));return
        self.data,self.path,self.config=data,source,content['config']
        self.interval=tuple(interval) if interval else None
        self.project_notes=str(content.get('notes',''))
        self.study_controls.load()
        self.populate_channels(data[0])
        self.channels.blockSignals(True)
        self.channels.clearSelection()
        chosen=set(content['channels'])
        for i in range(self.channels.topLevelItemCount()):
            group=self.channels.topLevelItem(i)
            for j in range(group.childCount()):
                item=group.child(j)
                if item.data(0,Qt.UserRole) in chosen:
                    item.setSelected(True);chosen.discard(item.data(0,Qt.UserRole))
        self.channels.blockSignals(False)
        self.search.clear();self.plot();self.update_info()

    def save_config(self):
        if not self.data:
            return
        path, _ = Q.QFileDialog.getSaveFileName(self, 'Guardar configuración', str(self.path.with_suffix('.analysis.json')), 'JSON (*.json)')
        if path:
            try:
                Path(path).write_text(json.dumps({'archivo': self.path.name, 'configuracion': self.config}, ensure_ascii=False, indent=2), encoding='utf-8')
            except OSError as exc:
                Q.QMessageBox.critical(self, 'Error al guardar', str(exc))

    def filter_channels(self, query):
        for i in range(self.channels.topLevelItemCount()):
            group = self.channels.topLevelItem(i)
            visible = False
            for j in range(group.childCount()):
                item = group.child(j)
                matches = query.casefold() in item.text(0).casefold() or query.casefold() in group.text(0).casefold()
                item.setHidden(not matches)
                visible |= matches
            group.setHidden(not visible)
            if query and visible:
                group.setExpanded(True)

    def plot(self):
        self.graph.clear()
        self.cursor_lines=[]
        self.plotted_channels = []
        self.export_png_button.setEnabled(False)
        self.update_file_actions()
        if not self.data:
            return
        headers, times, rows = self.scoped_data()
        selected = list(dict.fromkeys(item.data(0, Qt.UserRole) for item in self.channels.selectedItems() if item.data(0, Qt.UserRole)))
        for graph in self.extra_graphs:
            self.trend_layout.removeWidget(graph);graph.close();graph.deleteLater()
        self.extra_graphs=[]
        groups={}
        for name in selected:
            unit=name.split(' [')[-1].rstrip(']') if ' [' in name else 'adimensional'
            groups.setdefault(unit,[]).append(name)
        from datetime import timezone
        x=[t.replace(tzinfo=timezone.utc).timestamp() for t in times]
        summaries=[]
        for index,(unit,names) in enumerate(groups.items()):
            if index==0:
                graph=self.graph
            else:
                graph=pg.PlotWidget(axisItems={'bottom':pg.DateAxisItem(utcOffset=0)})
                graph.addLegend();graph.setXLink(self.graph)
                graph.scene().sigMouseMoved.connect(lambda pos, g=graph:self.track_cursor(g,pos))
                self.trend_layout.addWidget(graph,1);self.extra_graphs.append(graph);graph.show()
            graph.setMinimumHeight(190 if len(groups)>1 else 260)
            graph.setLabel('left',unit)
            graph.setLabel('bottom','Fecha y hora del registro')
            for n,name in enumerate(names):
                y=[channel_value(name,r[headers.index(name)]) for r in rows]
                graph.plot(x,y,name=name,pen=pg.mkPen(THEMES[self.theme]['curves'][n%6],width=1.8),connect='finite')
                valid=[v for v in y if math.isfinite(v)]
                if valid:
                    summaries.append(f'{name}: mín {min(valid):.5g} · media {statistics.mean(valid):.5g} · máx {max(valid):.5g}')
            graph.plotItem.vb.enableAutoRange(axis=pg.ViewBox.YAxis,enable=True)
            style_graph(graph,self.theme)
            line=pg.InfiniteLine(angle=90,movable=False,pen=pg.mkPen(THEMES[self.theme]['muted'],style=Qt.DashLine))
            graph.addItem(line,ignoreBounds=True);self.cursor_lines.append(line)
        self.plotted_channels=selected
        if selected:
            self.graph.plotItem.vb.autoRange(padding=.05)
            self.graph.plotItem.vb.enableAutoRange(axis=pg.ViewBox.XAxis,enable=True)
        style_graph(self.graph,self.theme)
        self.spectrum.refresh()
        self.export_png_button.setEnabled(bool(selected))
        self.update_file_actions()
        self.summary.setMaximumHeight(100)
        self.summary.setToolTip('\n'.join(summaries))
        summaries=summaries[:4]+[f'Intervalo analizado: {times[0]} → {times[-1]} · {len(times)} registros']
        self.summary.setText('\n'.join(summaries))


if __name__ == '__main__':
    app = Q.QApplication(sys.argv)
    app.setStyle('Fusion')
    window = Window()
    window.show()
    sys.exit(app.exec())
