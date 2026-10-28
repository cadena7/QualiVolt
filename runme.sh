#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if [[ -x .venv/bin/python ]]; then
    PYTHON=.venv/bin/python
elif [[ -x .venv/Scripts/python.exe ]]; then
    PYTHON=.venv/Scripts/python.exe
else
    echo 'Falta el entorno virtual. Ejecuta primero: bash install.sh' >&2
    exit 1
fi

exec "$PYTHON" app.py "$@"
