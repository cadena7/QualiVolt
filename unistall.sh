#!/usr/bin/env bash
set -euo pipefail

# El entorno contiene las dependencias instaladas por install.sh.
# No desinstalar Python ni paquetes de otros entornos.
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd -- "$PROJECT_DIR"

if [[ -L .venv ]]; then
    echo 'No se elimina .venv porque es un enlace simbólico.' >&2
    exit 1
fi

if [[ ! -e .venv ]]; then
    echo 'No hay entorno .venv que eliminar. El código y los archivos se conservan.'
    exit 0
fi

if [[ ! -d .venv || ! -f .venv/pyvenv.cfg ]]; then
    echo 'No se elimina .venv: no se reconoce como un entorno virtual de Python.' >&2
    exit 1
fi

VENV_TARGET="$(cd -- .venv && pwd -P)"
if [[ "$VENV_TARGET" != "$PROJECT_DIR/.venv" ]]; then
    echo 'No se elimina el entorno porque su ruta apunta fuera del proyecto.' >&2
    exit 1
fi

echo 'Eliminando el entorno virtual y sus dependencias…'
if ! rm -rf -- "$VENV_TARGET"; then
    echo 'No se pudo eliminar todo el entorno. Cierra la app y vuelve a ejecutar este script.' >&2
    exit 1
fi
echo 'Entorno eliminado. Se conservan el código, las mediciones y los reportes.'
echo 'Para volver a instalar: bash install.sh'
