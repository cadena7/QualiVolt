"""Intervalos de estudio y espectro interactivo."""
import math
from datetime import timezone
from PySide6 import QtWidgets as Q
from PySide6.QtCore import Qt
import pyqtgraph as pg
from analysis_report import Analysis
from appearance import style_graph, THEMES


class StudyControls(Q.QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        layout = Q.QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.start, self.end = Q.QDateTimeEdit(), Q.QDateTimeEdit()
        for widget in (self.start,self.end):
            widget.setDisplayFormat('dd/MM/yyyy HH:mm:ss')
            widget.setCalendarPopup(True)
        layout.addWidget(Q.QLabel('Desde'))
        layout.addWidget(self.start)
        layout.addWidget(Q.QLabel('Hasta'))
        layout.addWidget(self.end)
        for text,callback in [('Aplicar',self.apply),('Usar zoom',self.use_zoom),('Todo',self.reset)]:
            button=Q.QPushButton(text);button.clicked.connect(callback);layout.addWidget(button)
        self.setEnabled(False)

    def load(self):
        self.setEnabled(True)
        times=self.owner.data[1]
        for widget in (self.start,self.end):
            widget.setMinimumDateTime(times[0]);widget.setMaximumDateTime(times[-1])
        start,end=self.owner.interval or (times[0],times[-1])
        self.start.setDateTime(start);self.end.setDateTime(end)

    def apply(self):
        start=self.start.dateTime().toPython();end=self.end.dateTime().toPython()
        if start>end or not any(start<=t<=end for t in self.owner.data[1]):
            Q.QMessageBox.information(self,'Intervalo','Selecciona un intervalo que contenga mediciones.');return
        self.owner.interval=(start,end)
        self.owner.plot()

    def reset(self):
        if self.owner.data:
            self.owner.interval=None;self.load();self.owner.plot()

    def use_zoom(self):
        from datetime import datetime
        lo,hi=self.owner.graph.viewRange()[0]
        self.start.setDateTime(datetime.fromtimestamp(lo,timezone.utc).replace(tzinfo=None))
        self.end.setDateTime(datetime.fromtimestamp(hi,timezone.utc).replace(tzinfo=None))
        self.apply()


class SpectrumView(Q.QWidget):
    def __init__(self,owner):
        super().__init__();self.owner=owner
        layout=Q.QVBoxLayout(self);bar=Q.QHBoxLayout()
        self.phase=Q.QComboBox();self.phase.addItems(['V1','V2','V3','I1','I2','I3'])
        self.mode=Q.QComboBox();self.mode.addItems(['Porcentaje de fundamental','Amplitud RMS del período'])
        bar.addWidget(Q.QLabel('Fase'));bar.addWidget(self.phase);bar.addWidget(self.mode)
        layout.addLayout(bar)
        self.graph=pg.PlotWidget();layout.addWidget(self.graph)
        self.details=Q.QLabel();self.details.setWordWrap(True);layout.addWidget(self.details)
        self.phase.currentTextChanged.connect(self.refresh);self.mode.currentTextChanged.connect(self.refresh)
        self.graph.scene().sigMouseMoved.connect(self.hover)
        self.values=[]

    def refresh(self):
        self.graph.clear();self.values=[]
        if not self.owner.data:
            self.details.setText('Abre una grabación.');return
        analysis=Analysis(self.owner.scoped_data());phase=self.phase.currentText()
        if self.mode.currentIndex()==0:
            values,counts=analysis.spectrum(phase);self.unit='% de fundamental'
        else:
            values=[];counts=[];self.unit='V' if phase[0]=='V' else 'A'
            for order in range(2,50):
                series=analysis.series(f'har{order:02}{phase}_Avg [{self.unit}]')
                valid=[v for v in series if math.isfinite(v)]
                values.append(math.sqrt(sum(v*v for v in valid)/len(valid)) if valid else math.nan);counts.append(len(valid))
        self.values=values;self.counts=counts
        color=THEMES[self.owner.theme]['curves'][int(phase[-1])-1]
        valid=[(i+2,v) for i,v in enumerate(values) if math.isfinite(v)]
        if valid:
            self.graph.addItem(pg.BarGraphItem(x=[i for i,v in valid],height=[v for i,v in valid],width=.7,brush=color,pen=None))
        self.graph.setLabel('bottom','Orden armónico');self.graph.setLabel('left',self.unit)
        style_graph(self.graph,self.owner.theme)
        self.graph.autoRange()
        self.details.setText(f'{phase} · {len(analysis.times)} registros del intervalo. Pasa el cursor sobre una barra para consultar su valor.')

    def hover(self,position):
        if not self.values or not self.graph.sceneBoundingRect().contains(position):return
        order=round(self.graph.plotItem.vb.mapSceneToView(position).x())
        if 2<=order<=49:
            value=self.values[order-2]
            text=f'{value:.4g} {self.unit}' if math.isfinite(value) else 'sin datos válidos'
            self.details.setText(f'{self.phase.currentText()} · h{order}: {text} · {self.counts[order-2]} registros válidos')
