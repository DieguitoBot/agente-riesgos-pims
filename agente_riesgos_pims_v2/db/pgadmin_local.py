"""Configura y abre pgAdmin del proyecto: python -m db.pgadmin_local [--preparar]."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from db.local import DATOS, SOCKET, CLUSTER, binario, iniciar


def preparar():
    entorno = DATOS / 'pgadmin-venv'
    python = entorno / 'bin/python'
    paquetes = list(entorno.glob('lib/python*/site-packages/pgadmin4'))
    if not python.exists() or not paquetes:
        raise SystemExit('Instala pgadmin4 en .datos/pgadmin-venv antes de iniciar.')
    paquete = paquetes[0]
    generados = paquete / 'pgadmin/static/js/generated'
    requeridos = ('style.css','vendor.react.js','vendor.main.js','vendor.others.js',
                  'vendor.sqleditor.js','pgadmin_commons.js','app.bundle.js','browser_nodes.js')
    faltantes = [nombre for nombre in requeridos if not (generados / nombre).is_file()]
    if faltantes:
        raise SystemExit('La instalación de pgAdmin está incompleta: faltan recursos de interfaz: '
                         + ', '.join(faltantes) + '. Consulta db/OPERACION.txt antes de iniciar.')
    estado = DATOS / 'pgadmin'
    estado.mkdir(mode=0o700, exist_ok=True)
    configuracion = {
        'SERVER_MODE': False,
        'DEFAULT_SERVER': '127.0.0.1',
        'DEFAULT_SERVER_PORT': 5050,
        'ALLOWED_HOSTS': ['127.0.0.1', 'localhost'],
        'DATA_DIR': str(estado),
        'MASTER_PASSWORD_REQUIRED': False,
        'USE_OS_SECRET_STORAGE': False,
        'UPGRADE_CHECK_ENABLED': False,
        'DEFAULT_BINARY_PATHS': {'pg': str(Path(binario('pg_dump')).parent)},
    }
    (paquete / 'config_local.py').write_text(
        '# Configuración exclusiva del agente PIMS; generada por db.pgadmin_local.\n' +
        '\n'.join(f'{clave} = {valor!r}' for clave, valor in configuracion.items()) + '\n')
    subprocess.run([str(python), str(paquete / 'setup.py'), 'setup-db'], check=True)
    servicio = estado / 'pg_service.conf'
    servicio.write_text(f'[pims_local]\nhost={SOCKET}\nport=55439\ndbname=pims_riesgos\nuser=pims_admin\nsslmode=disable\n')
    os.environ['PGSERVICEFILE'] = str(servicio)
    marca = estado / 'conexion_pims_importada'
    if not marca.exists():
        servidores = estado / 'servidores.json'
        servidores.write_text(json.dumps({'Servers': {'1': {
            'Name': 'PIMS - Riesgos (local)', 'Group': 'Agente de riesgos PIMS',
            'Host': str(SOCKET), 'Port': 55439, 'MaintenanceDB': 'pims_riesgos',
            'Username': 'pims_admin', 'SSLMode': 'disable', 'Service': 'pims_local',
            'ConnectionParameters': {'sslmode': 'disable', 'connect_timeout': 5},
            'DBRestriction': 'pims_riesgos',
            'Comment': 'Instancia privada de este proyecto. Conexión por socket local.'
        }}}, ensure_ascii=False, indent=2))
        subprocess.run([str(python), str(paquete / 'setup.py'), 'load-servers', str(servidores)], check=True)
        marca.touch(mode=0o600)
    return python, paquete


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparar', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    python, paquete = preparar()
    if args.preparar:
        return
    resultado = subprocess.run([binario('pg_ctl'), '-D', str(CLUSTER), 'status'], capture_output=True)
    if resultado.returncode != 0:
        iniciar()
    print('pgAdmin del agente: http://127.0.0.1:5050', flush=True)
    os.execv(str(python), [str(python), str(paquete / 'pgAdmin4.py')])


if __name__ == '__main__':
    main()
