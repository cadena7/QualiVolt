"""Análisis descriptivo local y reporte vectorial PDF; no emite dictámenes normativos."""
import math
import re
import statistics
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPageSize, QPdfWriter, QPen, QTextDocument

from branding import APP_NAME, AUTHOR
from typography import FONT_FAMILY, load_fonts
REFERENCES = [
    ('IEEE 519-2022', 'Referencia para el control de la distorsión armónica de voltaje y corriente en el punto de acoplamiento común (PCC).', 'https://ieeexplore.ieee.org/document/9926021'),
    ('IEEE 1159-2019', 'Guía para el monitoreo de calidad de la energía y la interpretación de las variaciones eléctricas.', 'https://standards.ieee.org/ieee/1159/6124/'),
    ('ANSI/NEMA C84.1-2020 (R2025)', 'Referencia de tensiones nominales y tolerancias de operación en sistemas eléctricos de 60 Hz.', 'https://blog.ansi.org/ansi/ansi-c84-1-2020-electric-voltage-ratings-60-hz/'),
    ('México: Código de Red, RES/550/2021', 'Marco de referencia mexicano para los requisitos técnicos de conexión y calidad de la potencia en el Sistema Eléctrico Nacional.', 'https://sidof.segob.gob.mx/notas/5639920'),
]


def percentile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return None
    pos = (len(ordered)-1)*fraction
    lo, hi = math.floor(pos), math.ceil(pos)
    return ordered[lo] + (ordered[hi]-ordered[lo])*(pos-lo)


def emphasize_finding(note):
    """Destaca valores de un hallazgo, conservando escapado el texto."""
    return re.sub(r'(?<![\w.])\d+(?:\.\d+)?(?:\s*(?:%|Hz))?',
                  lambda match: f'<b>{match.group()}</b>', escape(note))


def power_axis(unit, maximum):
    """Unidad de ingeniería y escala redondeada para magnitudes de potencia."""
    divisor = 1_000_000 if maximum >= 1_000_000 else 1000 if maximum >= 1000 else 1
    label = ('M' if divisor == 1_000_000 else 'k' if divisor == 1000 else '') + unit
    scaled = maximum/divisor
    if scaled <= 0:
        return divisor,label,1.0
    raw = scaled/4
    base = 10**math.floor(math.log10(raw))
    step = next(n*base for n in (1,2,2.5,5,10) if n*base >= raw)
    return divisor,label,step*4


def load_report_fonts():
    """Carga la misma fuente que utiliza la interfaz."""
    load_fonts()


class Analysis:
    def __init__(self, data):
        self.headers, self.times, self.rows = data
        self.indices = {name: i for i, name in enumerate(self.headers)}

    def series(self, name):
        if name not in self.indices:
            return []
        # Solo magnitudes no negativas para estas gráficas. Se conserva la posición temporal.
        return [v if math.isfinite(v) and v >= 0 else math.nan
                for v in (row[self.indices[name]] for row in self.rows)]

    def stats(self, name):
        valid = [v for v in self.series(name) if math.isfinite(v)]
        if not valid:
            return None
        return min(valid), statistics.mean(valid), percentile(valid, .95), max(valid), len(valid)

    def spectrum(self, phase):
        fundamental = self.series(f'har01{phase}_Avg [{phase[0]}]'.replace('[I]', '[A]'))
        output = []
        counts = []
        for order in range(2, 50):
            name = f'har{order:02}{phase}_Avg [{"V" if phase[0]=="V" else "A"}]'
            harmonic = self.series(name)
            pairs = [(h, f) for h, f in zip(harmonic, fundamental)
                     if math.isfinite(h) and math.isfinite(f) and f > 0]
            # Razón de RMS temporales, no THD ni percentil normativo.
            value = 100*math.sqrt(sum(h*h for h, _ in pairs)/sum(f*f for _, f in pairs)) if pairs else math.nan
            output.append(value)
            counts.append(len(pairs))
        return output, counts

    def findings(self):
        notes = []
        for prefix, label in [('thdV', 'voltaje'), ('thdI', 'corriente')]:
            results = [(self.stats(f'{prefix}{phase}_Avg [%]'), phase) for phase in (1, 2, 3)]
            results = [(s,p) for s,p in results if s]
            if results:
                stats, phase = max(results, key=lambda pair: pair[0][3])
                notes.append(f'Distorsión de {label}: el mayor THD promedio de intervalo fue {stats[3]:.3f} % en fase {phase}. El 95 % de los registros válidos de esa fase quedó en {stats[2]:.3f} % o menos.')
        freq = self.stats('freq_Avg [Hz]')
        if freq:
            notes.append(f'Frecuencia: los promedios registrados estuvieron entre {freq[0]:.3f} y {freq[3]:.3f} Hz, con una media de {freq[1]:.3f} Hz.')
        for phase in ('V1', 'V2', 'V3'):
            values, counts = self.spectrum(phase)
            valid = [(v, n+2) for n,v in enumerate(values) if math.isfinite(v)]
            if valid:
                value, order = max(valid)
                notes.append(f'{phase}: el armónico con mayor presencia fue el orden {order}, con {value:.3f} % respecto a la fundamental en el resumen del período.')
        return notes


def export_report(path, data, config, source, context=None):
    load_report_fonts()
    context = context or {}
    project_title = str(config.get('titulo_proyecto') or context.get('sitio') or Path(source).stem)
    analysis = Analysis(data)
    writer = QPdfWriter(str(path))
    writer.setPageSize(QPageSize(QPageSize.A4))
    writer.setResolution(96)
    writer.setTitle(f'{APP_NAME} · {project_title} · Informe de calidad de la energía')
    writer.setCreator(f'{APP_NAME} · {AUTHOR}')
    painter = QPainter(writer)
    if not painter.isActive():
        raise OSError('No se pudo iniciar la escritura del PDF')
    width, height = writer.width(), writer.height()
    scale = width/720
    painter.scale(scale, scale)
    page_height = height/scale
    page = 0
    colors = ['#1675b6', '#d05b21', '#19865e', '#8955b5']

    def html(content, rect):
        doc = QTextDocument()
        doc.setDefaultFont(QFont(FONT_FAMILY, 10))
        doc.setDefaultStyleSheet('h2, h3 { font-weight: 600; } b, strong, th { font-weight: 700; }')
        doc.setHtml(content)
        doc.setTextWidth(rect.width())
        if doc.size().height() > rect.height()+1:
            raise ValueError('El contenido excede la página del informe; acorta los datos descriptivos.')
        painter.save()
        painter.translate(rect.topLeft())
        doc.drawContents(painter, QRectF(0,0,rect.width(),rect.height()))
        painter.restore()

    def new_page(title):
        nonlocal page
        if page:
            writer.newPage()
        page += 1
        painter.fillRect(QRectF(0,0,720,60), QColor('#142c43'))
        painter.setPen(QColor('white'))
        painter.setFont(QFont(FONT_FAMILY, 17, QFont.DemiBold))
        painter.drawText(QRectF(20,10,680,40), Qt.AlignVCenter, title)
        painter.setPen(QColor('#526478'))
        painter.setFont(QFont(FONT_FAMILY, 8))
        painter.drawText(QRectF(20,page_height-30,680,24), Qt.AlignLeft | Qt.AlignVCenter,
                         f'{APP_NAME} | {AUTHOR} | Análisis orientativo | {page}')

    def chart(title, names, rect, unit):
        plot = QRectF(rect.x()+55,rect.y()+35,rect.width()-70,rect.height()-(100 if len(names)>3 else 83))
        series = [(name, analysis.series(name)) for name in names]
        valid = [v for _,vs in series for v in vs if math.isfinite(v)]
        axis_unit = unit
        power = unit in ('W','var','VA')
        factor = unit == 'sin unidad'
        power_top = 1.0
        if valid and power:
            divisor,axis_unit,power_top = power_axis(unit,max(valid))
            series = [(name,[v/divisor for v in values]) for name,values in series]
            valid = [v for _,vs in series for v in vs if math.isfinite(v)]
        html(f'<b>{escape(title)}</b> <span style="color:#526478">({axis_unit})</span>', QRectF(rect.x(),rect.y(),rect.width(),28))
        if not valid:
            html('Sin datos válidos disponibles.',plot)
            return
        lower, upper = min(valid), max(valid)
        padding = max((upper-lower)*.08, abs(upper)*.01, .01)
        lower, upper = lower-padding,upper+padding
        if power:
            lower, upper = 0.0,power_top
        elif factor:
            lower, upper = 0.0, max(1.0,max(valid)*1.05) if max(valid)>1 else 1.0
        painter.setFont(QFont(FONT_FAMILY,8))
        for k in range(5):
            y=plot.bottom()-k*plot.height()/4
            painter.setPen(QPen(QColor('#dce3e9'),.7))
            painter.drawLine(QPointF(plot.left(),y),QPointF(plot.right(),y))
            painter.setPen(QColor('#334455'))
            tick = lower+(upper-lower)*k/4
            if power or factor:
                step = (upper-lower)/4
                decimals = min(8,max(0,math.ceil(-math.log10(step))+1))
                tick_text = f'{tick:.{decimals}f}'.rstrip('0').rstrip('.') if decimals else f'{tick:.0f}'
            else:
                tick_text = f'{tick:.3g}'
            painter.drawText(QRectF(rect.x(),y-8,50,18),Qt.AlignRight,tick_text)
        t = analysis.times
        duration = max((t[-1]-t[0]).total_seconds(),1)
        for n,(name,values) in enumerate(series):
            painter.setPen(QPen(QColor(colors[n%len(colors)]),1))
            previous=None
            for stamp,value in zip(t,values):
                if not math.isfinite(value):
                    previous=None
                    continue
                point=QPointF(plot.left()+(stamp-t[0]).total_seconds()/duration*plot.width(),plot.bottom()-(value-lower)/(upper-lower)*plot.height())
                if previous is not None:
                    painter.drawLine(previous,point)
                previous=point
            painter.drawText(QRectF(plot.x()+(n%3)*190,plot.bottom()+22+(n//3)*17,190,18),Qt.AlignLeft,name.split('_')[0])
        painter.setPen(QColor('#334455'))
        painter.drawText(QRectF(plot.x(),plot.bottom()+4,210,18),Qt.AlignLeft,t[0].strftime('%d/%m %H:%M'))
        painter.drawText(QRectF(plot.right()-210,plot.bottom()+4,210,18),Qt.AlignRight,t[-1].strftime('%d/%m %H:%M'))

    def spectrum_chart(phase, rect):
        values,counts=analysis.spectrum(phase)
        valid=[v for v in values if math.isfinite(v)]
        html(f'<b>{phase} · órdenes 2-49</b>',QRectF(rect.x(),rect.y(),rect.width(),26))
        if not valid:
            html('Sin señal suficiente para calcular el espectro.',QRectF(rect.x(),rect.y()+35,rect.width(),50))
            return
        plot=QRectF(rect.x()+48,rect.y()+30,rect.width()-60,rect.height()-80)
        top=max(max(valid)*1.12,.1)
        painter.setFont(QFont(FONT_FAMILY,8))
        for k in range(4):
            y=plot.bottom()-k*plot.height()/3
            painter.setPen(QPen(QColor('#dce3e9'),.7))
            painter.drawLine(QPointF(plot.left(),y),QPointF(plot.right(),y))
            painter.setPen(QColor('#334455'))
            painter.drawText(QRectF(rect.x(),y-8,44,18),Qt.AlignRight,f'{top*k/3:.2g}%')
        step=plot.width()/48
        for n,value in enumerate(values):
            if math.isfinite(value):
                barheight=value/top*plot.height()
                painter.fillRect(QRectF(plot.x()+n*step,plot.bottom()-barheight,step*.75,barheight),QColor(colors[int(phase[-1])-1]))
            if n==0 or (n+2)%5==0 or n==47:
                painter.setPen(QColor('#334455'))
                painter.drawText(QRectF(plot.x()+n*step-8,plot.bottom()+3,26,16),Qt.AlignCenter,str(n+2))
        painter.drawText(QRectF(plot.x(),plot.bottom()+22,plot.width(),22),Qt.AlignLeft,
                         f'Registros utilizados por orden: {min(counts)}-{max(counts)} de {len(analysis.rows)}.')

    try:
        source=Path(source)
        new_page('Informe de calidad de la energía')
        html(f'<h2>{escape(project_title)}</h2>'
             f'<p><b>Autor del programa y créditos:</b> {AUTHOR}<br>'
             f'<b>Responsable del análisis:</b> {escape(context.get("responsable") or AUTHOR)}<br>'
             f'<b>Instrumento:</b> HT Instruments PQA820<br>'
             f'<b>Archivo:</b> {escape(source.name)}<br>'
             f'<b>Período:</b> {analysis.times[0]} a {analysis.times[-1]}<br>'
             f'<b>Datos:</b> {len(analysis.rows):,} registros; {len(analysis.headers)} canales<br>'
             f'<b>Ubicación:</b> {escape(context.get("punto", "Sin confirmar"))}</p>'
             '<h3>Lo más relevante de la medición</h3><p>Resumen de las tendencias y armónicos '
             'observados durante toda la grabación.</p>'
             + ''.join(f'<p>• {emphasize_finding(note)}</p>' for note in analysis.findings())
             + '<h3>Cómo leer las gráficas</h3><p>Las tendencias muestran cómo cambia cada magnitud '
             'con el tiempo. Los espectros permiten identificar los órdenes armónicos con mayor presencia '
             'en cada fase.</p>',
             QRectF(20,75,680,page_height-120))

        new_page('Tendencias · voltaje y corriente')
        chart('Voltaje fase-neutro promedio',[f'V{i}_Avg [V]' for i in (1,2,3)],QRectF(20,80,680,255),'V')
        chart('Voltaje fase-fase promedio',[f'V{i}_Avg [V]' for i in ('12','23','31')],QRectF(20,350,680,255),'V')
        chart('Corrientes promedio',[f'I{i}_Avg [A]' for i in (1,2,3)],QRectF(20,620,680,235),'A')

        new_page('Potencias y factor de potencia')
        html('Valores totales promedio por intervalo. Las curvas + y − conservan los sentidos de flujo '
             'del registro; i identifica componente inductiva y c, capacitiva.',QRectF(20,75,680,65))
        chart('Potencia activa total',['Pt+_Avg [W]','Pt-_Avg [W]'],QRectF(20,145,680,180),'W')
        chart('Potencia reactiva total',['Qti+_Avg [VAR]','Qtc+_Avg [VAR]','Qti-_Avg [VAR]','Qtc-_Avg [VAR]'],QRectF(20,335,680,190),'var')
        chart('Potencia aparente total',['St+_Avg [VA]','St-_Avg [VA]'],QRectF(20,535,680,180),'VA')
        chart('Factor de potencia total',['Pfti+_Avg','Pftc+_Avg','Pfti-_Avg','Pftc-_Avg'],QRectF(20,725,680,190),'sin unidad')

        new_page('Tendencias · THD y frecuencia')
        chart('THD de voltaje promedio',[f'thdV{i}_Avg [%]' for i in (1,2,3)],QRectF(20,80,680,255),'%')
        chart('THD de corriente promedio',[f'thdI{i}_Avg [%]' for i in (1,2,3)],QRectF(20,350,680,255),'%')
        chart('Frecuencia promedio',['freq_Avg [Hz]'],QRectF(20,620,680,235),'Hz')

        for kind,label in [('V','voltaje'),('I','corriente')]:
            new_page(f'Espectro armónico · {label}')
            html('Cada barra representa un armónico como porcentaje de la fundamental. '
                 'Las barras más altas muestran los órdenes con mayor presencia durante la grabación.',QRectF(20,75,680,100))
            for phase in (1,2,3):
                spectrum_chart(f'{kind}{phase}',QRectF(20,180+(phase-1)*235,680,225))

        new_page('Resumen de valores · configuración')
        chosen=['V1_Avg [V]','V2_Avg [V]','V3_Avg [V]','In_Avg [A]','I1_Avg [A]','I2_Avg [A]','I3_Avg [A]','freq_Avg [Hz]']
        table='<table width="100%" cellspacing="5"><tr><th>Canal</th><th>Mín.</th><th>Media</th><th>P95</th><th>Máx.</th><th>Válidos</th></tr>'
        for name in chosen:
            stats=analysis.stats(name)
            if stats:
                table+='<tr><td>'+escape(name)+'</td>'+''.join(f'<td>{v:.4g}</td>' for v in stats[:4])+f'<td>{stats[4]}</td></tr>'
        table+='</table>'
        intervals=[(b-a).total_seconds() for a,b in zip(analysis.times,analysis.times[1:])]
        period=statistics.median(intervals) if intervals else None
        gaps=sum(v!=period for v in intervals) if intervals else 0
        config_labels = {'frecuencia_hz': 'Frecuencia nominal del análisis (Hz)',
            'sistema': 'Sistema', 'tension_nominal_v': 'Tensión nominal del sistema (V)',
            'referencia': 'Referencia de las mediciones', 'referencia_nominal': 'Referencia del nominal',
            'relacion_tc': 'Relación TC', 'relacion_tp': 'Relación TP'}
        config_labels['punto_medicion'] = 'Punto de medición'
        settings=''.join(f'<li>{escape(config_labels.get(k,str(k)))}: {escape(str(v))}</li>' for k,v in config.items() if k != 'titulo_proyecto')
        html(table+f'<h3>Configuración declarada</h3><ul>{settings}</ul>'
             f'<p>Separación habitual entre registros: {period} s. Intervalos con otra duración: {gaps}.</p>'
             '<h3>Cómo se obtienen los resultados</h3>'
             '<p><b>Mínimo, media y máximo:</b> son el valor más bajo, el promedio y el valor '
             'más alto de las mediciones válidas del período analizado.</p>'
             '<p><b>P95:</b> es un valor de referencia por debajo del cual se encuentra '
             'aproximadamente el 95 % de las mediciones válidas. Por ejemplo, un P95 de THD de 8 % '
             'indica que aproximadamente 95 de cada 100 registros tuvieron un THD de 8 % o menor. '
             'Este ejemplo explica la lectura del dato; no es un límite permitido.</p>'
             '<p><b>Porcentaje de armónicos:</b> compara la intensidad de cada armónico con la señal '
             'principal de 50 o 60 Hz, llamada fundamental. Una barra de 5 % indica una amplitud '
             'equivalente al 5 % de la fundamental en el resumen del período. Se comparan los mismos '
             'registros para ambas señales, dando mayor peso a las amplitudes más grandes.</p>'
             '<p><b>Datos utilizados:</b> los cálculos incluyen los registros del intervalo elegido '
             'con valores numéricos válidos y no negativos. Los ceros se conservan. Para expresar '
             'un armónico en porcentaje, también debe existir una fundamental mayor que cero. '
             'Las mediciones originales no se modifican.</p>',
             QRectF(20,80,680,page_height-125))

        new_page('Referencias técnicas')
        references=''.join(f'<h3>{escape(title)}</h3><p>{escape(description)}</p>'
                           f'<p style="font-size:8pt">{escape(url)}</p>' for title,description,url in REFERENCES)
        html(references,
             QRectF(20,75,680,page_height-120))
    finally:
        painter.end()
    return page
