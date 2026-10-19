#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ -x .venv/bin/python ]]; then
    interprete=.venv/bin/python
elif [[ -x ../agente_riesgos_pims/.venv/bin/python ]]; then
    interprete=../agente_riesgos_pims/.venv/bin/python
else
    interprete=python3
fi
exec "$interprete" iniciar_local.py "$@"
