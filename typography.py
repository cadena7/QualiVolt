"""Fuente compartida por la interfaz y los reportes de QualiVolt."""
from pathlib import Path
from PySide6.QtGui import QFont, QFontDatabase

FONT_FAMILY = 'Geist'
_loaded = False


def load_fonts():
    global _loaded
    if _loaded:
        return
    folder = Path(__file__).resolve().parent / 'assets' / 'fonts' / 'Geist'
    for name in ('Geist-Regular.ttf', 'Geist-SemiBold.ttf', 'Geist-Bold.ttf'):
        font_id = QFontDatabase.addApplicationFont(str(folder / name))
        if font_id < 0 or FONT_FAMILY not in QFontDatabase.applicationFontFamilies(font_id):
            raise RuntimeError(f'No se pudo cargar {name}. Conserva assets/fonts/Geist junto al código.')
    _loaded = True


def apply_ui_font(app):
    load_fonts()
    app.setFont(QFont(FONT_FAMILY, 10))
