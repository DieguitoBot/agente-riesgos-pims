"""Abre pgAdmin local con la conexión existente de V3, sin migrar PostgreSQL."""
import json
import os
from pathlib import Path
import subprocess
import sys

from dotenv import dotenv_values
from psycopg.conninfo import conninfo_to_dict

BASE = Path(__file__).resolve().parent
PRIVADO = BASE / 'datos' / 'pgadmin'


def main():
    os.umask(0o077)
    ejecutable = PRIVADO / 'venv' / 'bin' / 'pgadmin4'
    cli = ejecutable.with_name('pgadmin4-cli')
    if not ejecutable.exists():
        sys.exit('Instala pgAdmin en datos/pgadmin/venv; consulta README.md.')
    valores = dotenv_values(BASE / '.env')
    conexion = conninfo_to_dict(os.environ.get('PIMS_DATABASE_URL') or
                                valores.get('PIMS_DATABASE_URL') or '')
    if conexion.get('dbname') != 'pims_riesgos_experimental':
        sys.exit('No se encontró la conexión de V3 a su base experimental.')
    if (BASE / 'datos/postgres_demo/PG_VERSION').exists():
        from preparar_demo import iniciar_cluster
        iniciar_cluster()
    from db.repositorio import conectar
    with conectar() as con:
        con.execute('SELECT 1').fetchone()
    PRIVADO.mkdir(parents=True, exist_ok=True, mode=0o700)
    PRIVADO.chmod(0o700)
    configuracion = PRIVADO / 'config_9_10.py'
    if not configuracion.exists():
        with configuracion.open('x') as archivo:
            archivo.write(
                'SERVER_MODE = False\n'
                "DEFAULT_SERVER = '127.0.0.1'\n"
                'DEFAULT_SERVER_PORT = 5050\n'
                f'DATA_DIR = {str(PRIVADO / "estado_9_10")!r}\n'
                'MASTER_PASSWORD_REQUIRED = False\n'
                'USE_OS_SECRET_STORAGE = False\n'
                'UPGRADE_CHECK_ENABLED = False\n'
                'LLM_ENABLED = False\n'
                "SESSION_COOKIE_NAME = 'pims_pgadmin_session'\n"
            )
    entorno = dict(os.environ, CONFIG_DISTRO_FILE_PATH=str(configuracion))
    marca = PRIVADO / 'conexion_importada_9_10'
    if not marca.exists():
        servidores = PRIVADO / 'servidores.json'
        if not servidores.exists():
            servidor = dict(Name='PIMS V3 — PostgreSQL', Group='PIMS UNSA',
                            Host=conexion.get('host', 'localhost'),
                            Port=int(conexion.get('port', 5432)),
                            MaintenanceDB=conexion['dbname'],
                            Username=conexion.get('user', ''), SSLMode='prefer',
                            Comment='Conexión de V3. Simulación académica.')
            with servidores.open('x') as archivo:
                json.dump({'Servers': {'1': servidor}}, archivo, ensure_ascii=False)
        subprocess.run([str(cli), 'setup-db'], env=entorno, check=True)
        subprocess.run([str(cli), 'load-servers', str(servidores)],
                       env=entorno, check=True)
        marca.touch(exist_ok=False)
    print('Visor PostgreSQL: http://127.0.0.1:5050', flush=True)
    os.execve(str(ejecutable), [str(ejecutable)], entorno)


if __name__ == '__main__':
    main()
