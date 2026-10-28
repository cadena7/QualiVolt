"""Importador de exportaciones TopView, sin modificar los archivos originales."""
import csv
import math
import statistics
from datetime import datetime
from pathlib import Path


def load_csv(path):
    raw = Path(path).read_bytes()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1252')
    lines = text.splitlines()
    delimiter = lines.pop(0)[4:] if lines and lines[0].startswith('sep=') else '|'
    rows = csv.reader(lines, delimiter=delimiter)
    headers = next(rows)
    while headers and not headers[-1]:
        headers.pop()
    times, values = [], []
    for number, row in enumerate(rows, 3):
        if not row or not any(row):
            continue
        while len(row) > len(headers) and row[-1] == '':
            row.pop()
        if len(row) != len(headers):
            raise ValueError(f'Fila {number}: cantidad de columnas incorrecta')
        stamp = row[0].replace('p. m.', 'PM').replace('a. m.', 'AM')
        # Interpretación de 12 horas independiente del idioma del sistema.
        suffix = stamp[-2:]
        date = datetime.strptime(stamp[:-3], '%d/%m/%Y %I:%M:%S')
        if suffix not in ('AM', 'PM'):
            raise ValueError(f'Fila {number}: hora no reconocida')
        if suffix == 'PM':
            date = date.replace(hour=date.hour + 12)
        if times and date <= times[-1]:
            raise ValueError(f'Fila {number}: tiempo duplicado o fuera de orden')
        times.append(date)
        parsed = [float(v.replace(',', '.')) if v.strip() else math.nan for v in row[1:]]
        values.append(parsed)
    if not times:
        raise ValueError('El archivo no contiene mediciones')
    return headers[1:], times, values


def suggested_frequency(headers, values):
    if 'freq_Avg [Hz]' not in headers:
        return None
    column = headers.index('freq_Avg [Hz]')
    valid = [r[column] for r in values if math.isfinite(r[column]) and r[column] > 0]
    if not valid:
        return None
    median = statistics.median(valid)
    return min((50, 60), key=lambda f: abs(f-median)) if 45 <= median <= 65 else None
