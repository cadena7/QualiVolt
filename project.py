"""Proyectos portables: referencias relativas a mediciones, ajustes y selección."""
import json
import os
import uuid
from pathlib import Path
from datetime import datetime


def save_project(path, source, config, channels, interval, notes):
    target = Path(path).resolve()
    try:
        relative = os.path.relpath(Path(source).resolve(), target.parent)
    except ValueError:
        relative = str(Path(source).resolve())
    content = dict(format='qualivolt-project', version=1, source=relative,
                   config=config, channels=channels,
                   interval=[v.isoformat() for v in interval] if interval else None, notes=notes)
    temporary = target.with_name(f'.project-{uuid.uuid4().hex}.tmp')
    try:
        temporary.write_text(json.dumps(content,ensure_ascii=False,indent=2),encoding='utf-8')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def read_project(path):
    target = Path(path).resolve()
    content = json.loads(target.read_text(encoding='utf-8'))
    if content.get('format') != 'qualivolt-project' or content.get('version') != 1:
        raise ValueError('Formato de proyecto no compatible.')
    if not isinstance(content.get('config'),dict) or not isinstance(content.get('channels'),list):
        raise ValueError('Configuración de proyecto inválida.')
    content['source'] = (target.parent / content['source']).resolve()
    if not content['source'].is_file():
        raise ValueError('No se encuentra la medición del proyecto. Conserva su carpeta y los archivos HED/PER junto al proyecto.')
    if content.get('interval'):
        content['interval'] = [datetime.fromisoformat(v) for v in content['interval']]
        if len(content['interval'])!=2 or content['interval'][0]>content['interval'][1]:
            raise ValueError('Intervalo de proyecto inválido.')
    return content
