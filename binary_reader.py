"""Lector experimental del perfil PQA820 1.15 observado en grabaciones reales.

No depende de CSV ni de nombres de archivo para decodificar las mediciones.
"""
from datetime import datetime, timedelta
from pathlib import Path


# Perfil de configuración contrastado con los dos reportes oficiales locales.
# Es una sugerencia del perfil completo, no una decodificación universal del modo.
_KNOWN_4WIRE_CONFIG = bytes.fromhex(
    '32000103e86400000000640000000000010000000000000030ffffffff170010'
    'ffffffffffff07ffffffffffffc7000000000000dc')


def suggested_system_from_header(header):
    signature = header[51:56] + header[61:72] + header[77:79] + header[103:138]
    return 'Trifásico 4 hilos' if signature == _KNOWN_4WIRE_CONFIG else None


def channel_layout():
    layout = []
    def triplet(base, unit=''):
        layout.extend(f'{base}_{s}' + (f' [{unit}]' if unit else '') for s in ('Avg', 'Max', 'Min'))
    for name in ('V1', 'V2', 'V3', 'V12', 'V23', 'V31'):
        triplet(name, 'V')
    triplet('freq', 'Hz')
    for name in ('In', 'I1', 'I2', 'I3'):
        triplet(name, 'A')
    for sign in ('+', '-'):
        for prefix, unit in (('P', 'W'), ('Qi', 'VAR'), ('Qc', 'VAR'), ('S', 'VA')):
            for phase in ('t', '1', '2', '3'):
                base = prefix[0] + phase + prefix[1:] + sign
                triplet(base, unit)
        for prefix in ('Pf', 'dpf'):
            for phase in ('t', '1', '2', '3'):
                for kind in ('i', 'c'):
                    triplet(prefix + phase + kind + sign)
    triplet('u2', '%')
    layout.extend([None] * 3)  # Bloque adicional de desequilibrio sin validar.
    for name in ('V1', 'V2', 'V3', 'I1', 'I2', 'I3'):
        unit = 'V' if name.startswith('V') else 'A'
        layout.append(f'thd{name}_Avg [%]')
        layout.append(f'dc{name}_Avg [{unit}]')
        layout.extend(f'har{i:02}{name}_Avg [{unit}]' for i in range(1, 50))
    layout.extend([None] * 2)  # Campos finales no identificados.
    assert len(layout) == 539
    return layout


def energy_layout():
    result = []
    for prefix, energy, unit in (('P','Ea','Wh'), ('Qi','Er','VARh'), ('Qc','Er','VARh'), ('S','Es','VAh')):
        for phase in ('t','1','2','3'):
            for sign in ('+','-'):
                suffix = phase + prefix[1:] + sign
                result.append((energy + suffix + '_Avg ['+unit+']',
                               prefix[0] + suffix + '_Avg ['+{'Wh':'W','VARh':'VAR','VAh':'VA'}[unit]+']'))
    return result


def read_header(path):
    b = Path(path).read_bytes()
    if len(b) != 195 or b[:4] != bytes.fromhex('2f000102') or b[13:21].strip() != b'PQA820':
        raise ValueError('Cabecera no compatible: se requiere el perfil PQA820 de 195 bytes.')
    # Las máscaras definen qué cantidades están presentes. No adivinar otro perfil.
    if b[103:131].hex() != '00000000000030ffffffff170010ffffffffffff07ffffffffffffc7':
        raise ValueError('Configuración de canales binarios aún no compatible.')
    start = datetime(2000+b[56], b[57], b[58], b[59], b[60])
    period = int.from_bytes(b[75:77], 'big')
    count = int.from_bytes(b[79:83], 'big')
    if not 1 <= period <= 3600 or not count:
        raise ValueError('Intervalo o cantidad de registros inválidos en HED.')
    return {'inicio': start, 'intervalo_s': period, 'registros': count,
            'modelo': 'PQA820', 'perfil': 'experimental-539',
            'sistema_sugerido': suggested_system_from_header(b)}


def pair_paths(path):
    path = Path(path)
    siblings = {p.suffix.lower(): p for p in path.parent.iterdir() if p.stem.casefold() == path.stem.casefold()}
    if '.hed' not in siblings or '.per' not in siblings:
        raise ValueError('Se necesitan los archivos HED y PER con el mismo nombre en la misma carpeta.')
    return siblings['.hed'], siblings['.per']


def load_binary(path):
    hed, per = pair_paths(path)
    meta = read_header(hed)
    raw = per.read_bytes()
    required = meta['registros'] * 1617
    if len(raw) != ((required + 511)//512)*512 or any(x != 255 for x in raw[required:]):
        raise ValueError('Archivo PER incompleto o estructura no compatible con el perfil de 1617 bytes.')
    layout = channel_layout()
    columns = [(i, name) for i, name in enumerate(layout) if name is not None]
    values = []
    for row in range(meta['registros']):
        data = []
        for i, name in columns:
            offset = row*1617 + i*3
            word = raw[offset:offset+3]
            mantissa = int.from_bytes(word[:2], 'big', signed=True)
            exponent = int.from_bytes(word[2:], 'big', signed=True)
            if word == b'\xff\xff\x00':
                value = -1.0
            elif not -9 <= exponent <= 9:
                raise ValueError(f'Codificación no compatible: registro {row+1}, canal {name}.')
            else:
                value = mantissa * 10.0**exponent
            data.append(value)
        values.append(data)
    # Energía acumulada desde el primer intervalo: potencia promedio × horas.
    # Se conserva precisión completa; TopView redondea estas columnas al exportar.
    headers = [name for _, name in columns]
    energies = energy_layout()
    indices = [headers.index(power) for _, power in energies]
    totals = [0.0] * len(energies)
    for row in values:
        for j,index in enumerate(indices):
            totals[j] += row[index] * meta['intervalo_s']/3600
        row.extend(totals)
    headers.extend(name for name,_ in energies)
    times = [meta['inicio'] + timedelta(seconds=i*meta['intervalo_s']) for i in range(meta['registros'])]
    return headers, times, values
