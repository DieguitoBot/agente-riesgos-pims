#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -f .env ]]; then
    echo 'Prepara la demostración: .venv/bin/python preparar_demo.py (consulta README.md)'
    exit 1
fi
if [[ -x .venv/bin/python ]]; then
    interprete=.venv/bin/python
else
    echo 'Crea el entorno virtual según README.md.'
    exit 1
fi
if [[ -f datos/postgres_demo/PG_VERSION ]]; then
    "$interprete" -c 'from preparar_demo import iniciar_cluster; iniciar_cluster()'
fi
exec "$interprete" iniciar_local.py "$@"
