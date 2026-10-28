"""Vista previa integrada del PDF y acciones de guardado e impresión."""
from pathlib import Path
import shutil
import uuid
from PySide6 import QtWidgets as Q
from PySide6.QtCore import QSize, QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPrintSupport import QPrinter, QPrintDialog


class ReportPreview(Q.QDialog):
    def __init__(self, pdf_path, suggested_path, parent=None):
        super().__init__(parent)
        self.pdf_path = Path(pdf_path)
        self.suggested_path = Path(suggested_path)
        self.setWindowTitle('Vista previa del reporte · QualiVolt')
        self.resize(1050, 850)
        layout = Q.QVBoxLayout(self)
        self.document = QPdfDocument(self)
        error = self.document.load(str(self.pdf_path))
        if error != QPdfDocument.Error.None_:
            self.document.close()
            raise OSError('No se pudo abrir la vista previa del informe.')
        bar = Q.QHBoxLayout()
        bar.addWidget(Q.QLabel(f'{self.document.pageCount()} páginas'))
        zoom = Q.QComboBox()
        zoom.addItems(['Ajustar ancho', 'Página completa', '75 %', '100 %', '125 %', '150 %'])
        bar.addWidget(zoom)
        bar.addStretch()
        for label, callback in [('Guardar PDF…', self.save_pdf), ('Imprimir…', self.print_pdf), ('Cerrar', self.reject)]:
            button = Q.QPushButton(label)
            button.clicked.connect(callback)
            bar.addWidget(button)
        layout.addLayout(bar)
        self.view = QPdfView(self)
        self.view.setDocument(self.document)
        self.view.setPageMode(QPdfView.PageMode.MultiPage)
        self.view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        layout.addWidget(self.view, 1)
        self.status = Q.QLabel('Revisa el reporte y elige si deseas guardarlo o imprimirlo.')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        def change_zoom(text):
            if text == 'Ajustar ancho':
                self.view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            elif text == 'Página completa':
                self.view.setZoomMode(QPdfView.ZoomMode.FitInView)
            else:
                self.view.setZoomMode(QPdfView.ZoomMode.Custom)
                self.view.setZoomFactor(float(text.split()[0])/100)
        zoom.currentTextChanged.connect(change_zoom)
        self.finished.connect(lambda _: self.document.close())

    def save_pdf(self):
        target, _ = Q.QFileDialog.getSaveFileName(self, 'Guardar informe PDF', str(self.suggested_path), 'Informe PDF (*.pdf)')
        if not target:
            return
        if not target.lower().endswith('.pdf'):
            target += '.pdf'
        target = Path(target)
        temporary = target.with_name(f'.report-{uuid.uuid4().hex}.pdf')
        try:
            shutil.copyfile(self.pdf_path, temporary)
            temporary.replace(target)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            Q.QMessageBox.critical(self, 'No se pudo guardar el informe', str(exc))
            return
        self.suggested_path = target
        self.status.setText(f'PDF guardado en: {target}')

    def paint_pdf(self, printer):
        painter = QPainter(printer)
        if not painter.isActive():
            raise OSError('No se pudo iniciar la impresión del reporte.')
        try:
            count = self.document.pageCount()
            first, last = 0, count-1
            if printer.printRange() == QPrinter.PrintRange.PageRange:
                first = max(0, printer.fromPage()-1)
                last = min(count-1, printer.toPage()-1)
            for index in range(first, last+1):
                if index > first and not printer.newPage():
                    raise OSError('La impresora no pudo crear la siguiente página.')
                viewport = painter.viewport()
                page = self.document.pagePointSize(index)
                # Renderizar a ~250 dpi sin depender de la resolución física de la impresora.
                size = QSize(round(page.width()*250/72), round(page.height()*250/72))
                image = self.document.render(index, size)
                if image.isNull():
                    raise OSError(f'No se pudo preparar la página {index+1}.')
                fitted = image.size().scaled(viewport.size(), Qt.KeepAspectRatio)
                rect = QRectF(viewport.x()+(viewport.width()-fitted.width())/2,
                              viewport.y()+(viewport.height()-fitted.height())/2,
                              fitted.width(), fitted.height())
                painter.drawImage(rect, image)
        finally:
            painter.end()

    def print_pdf(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setDocName(self.suggested_path.stem)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle('Imprimir reporte')
        dialog.setMinMax(1, self.document.pageCount())
        dialog.setOption(QPrintDialog.PrintDialogOption.PrintPageRange, True)
        if dialog.exec() != Q.QDialog.Accepted:
            return
        try:
            self.paint_pdf(printer)
        except Exception as exc:
            Q.QMessageBox.critical(self, 'No se pudo imprimir el reporte', str(exc))
            return
        self.status.setText('Reporte enviado a impresión.')
