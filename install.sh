#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if [[ -x .venv/bin/python ]]; then
    PYTHON=.venv/bin/python
elif [[ -x .venv/Scripts/python.exe ]]; then
    PYTHON=.venv/Scripts/python.exe
else
    if command -v python3 >/dev/null 2>&1; then
        BASE_PYTHON=python3
    elif command -v python >/dev/null 2>&1; then
        BASE_PYTHON=python
    else
        echo 'Instala Python 3.11 o posterior y vuelve a ejecutar este script.' >&2
        exit 1
    fi
    "$BASE_PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Se requiere Python 3.11 o posterior")'
    if ! "$BASE_PYTHON" -m venv .venv; then
        echo 'No se pudo crear el entorno. En Ubuntu, instala python3-venv e inténtalo de nuevo.' >&2
        exit 1
    fi
    if [[ -x .venv/bin/python ]]; then
        PYTHON=.venv/bin/python
    else
        PYTHON=.venv/Scripts/python.exe
    fi
fi

"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Se requiere Python 3.11 o posterior; recrea .venv con una versión compatible")'
echo 'Preparando dependencias…'
"$PYTHON" -m pip install -r requirements.txt
echo 'Instalación completa. Ejecuta: bash runme.sh'

