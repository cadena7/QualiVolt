"""Temas compartidos por la interfaz y las gráficas."""
from PySide6.QtGui import QColor, QPalette
import pyqtgraph as pg

THEMES = {
    'light': dict(window='#f3f6fa', panel='#ffffff', plot='#ffffff', text='#223047',
                  muted='#64748b', border='#d6dee9', hover='#e9f0fa', accent='#2563eb',
                  curves=['#2563eb', '#c45d16', '#008571', '#9333b8', '#c02664', '#657523']),
    'dark': dict(window='#151b25', panel='#202938', plot='#111820', text='#e6edf7',
                 muted='#9eadc2', border='#354256', hover='#2b3950', accent='#77a8ff',
                 curves=['#77a8ff', '#ffb36b', '#51d6b7', '#c4a0ff', '#ff90bc', '#e0d773']),
}


def apply_palette(app, theme):
    c = THEMES[theme]
    palette = QPalette()
    for role, color in [(QPalette.Window,c['window']), (QPalette.WindowText,c['text']),
                        (QPalette.Base,c['panel']), (QPalette.AlternateBase,c['hover']),
                        (QPalette.Text,c['text']), (QPalette.Button,c['panel']),
                        (QPalette.ButtonText,c['text']), (QPalette.ToolTipBase,c['panel']),
                        (QPalette.ToolTipText,c['text']), (QPalette.Highlight,'#2563eb'),
                        (QPalette.HighlightedText,'#ffffff'), (QPalette.Link,c['accent']),
                        (QPalette.PlaceholderText,c['muted'])]:
        palette.setColor(role,QColor(color))
    for role in (QPalette.Text,QPalette.ButtonText,QPalette.WindowText):
        palette.setColor(QPalette.Disabled,role,QColor(c['muted']))
    app.setPalette(palette)
    app.setStyleSheet(f'''
        QPushButton, QToolButton {{ padding: 6px 10px; border: 1px solid {c['border']};
            border-radius: 6px; background: {c['panel']}; color: {c['text']}; }}
        QPushButton:hover, QToolButton:hover {{ background: {c['hover']}; border-color: {c['accent']}; }}
        QPushButton:disabled, QToolButton:disabled {{ color: {c['muted']}; }}
        QLineEdit, QComboBox, QDoubleSpinBox {{ padding: 5px; border: 1px solid {c['border']};
            border-radius: 5px; background: {c['panel']}; color: {c['text']}; }}
        QTreeWidget {{ border: 1px solid {c['border']}; border-radius: 6px; padding: 4px;
            background: {c['panel']}; color: {c['text']}; }}
        QTreeWidget::item {{ padding: 2px; }}
        QTreeWidget::item:selected {{ background: #2563eb; color: white; }}
        QMenu {{ background: {c['panel']}; color: {c['text']}; border: 1px solid {c['border']}; }}
        QMenu::item {{ padding: 6px 22px; }}
        QMenu::item:selected, QMenuBar::item:selected {{ background: {c['hover']}; }}
        QMenu::item:disabled {{ color: {c['muted']}; }}
        QToolTip {{ background: {c['panel']}; color: {c['text']}; border: 1px solid {c['border']}; }}
    ''')


def style_graph(graph, theme):
    c = THEMES[theme]
    graph.setBackground(c['plot'])
    graph.showGrid(x=True,y=True,alpha=.14)
    for side in ('left','bottom'):
        axis = graph.getAxis(side)
        axis.setPen(pg.mkPen(c['muted']))
        axis.setTextPen(pg.mkPen(c['text']))
        axis.setLabel(axis.labelText, units=axis.labelUnits, color=c['text'])
    graph.plotItem.titleLabel.setText(graph.plotItem.titleLabel.text, color=c['text'])
    legend = graph.plotItem.legend
    if legend:
        legend.setLabelTextColor(c['text'])
        for _, label in legend.items:
            label.setText(label.text, color=c['text'])
        legend.setBrush(pg.mkBrush(c['panel']))
        legend.setPen(pg.mkPen(c['border']))
    for index,curve in enumerate(graph.plotItem.listDataItems()):
        if hasattr(curve, 'setPen'):
            curve.setPen(pg.mkPen(c['curves'][index % len(c['curves'])],width=1.8))
