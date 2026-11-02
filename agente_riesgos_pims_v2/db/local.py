"""Clúster privado: python -m db.local iniciar|detener. No modifica servicios del sistema."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

BASE = Path(__file__).resolve().parents[1]
DATOS = BASE.parent / '.datos'
CLUSTER = DATOS / 'postgres'
SOCKET = DATOS / 'socket'


def binario(nombre):
    ruta = shutil.which(nombre)
    if ruta:
        return ruta
    candidatos = sorted(Path('/usr/lib/postgresql').glob(f'*/bin/{nombre}'), reverse=True)
    if not candidatos:
        raise RuntimeError('Instala los binarios de PostgreSQL antes de iniciar.')
    return str(candidatos[0])


def ejecutar(nombre, *args):
    subprocess.run([binario(nombre), *map(str, args)], check=True)


def iniciar():
    DATOS.mkdir(mode=0o700, exist_ok=True)
    SOCKET.mkdir(mode=0o700, exist_ok=True)
    if not (CLUSTER / 'PG_VERSION').exists():
        ejecutar('initdb', '-D', CLUSTER, '-U', 'pims_admin', '--auth-local=trust', '--auth-host=reject', '--encoding=UTF8', '--no-locale')
    estado = subprocess.run([binario('pg_ctl'), '-D', str(CLUSTER), 'status'], capture_output=True)
    if estado.returncode != 0:
        ejecutar('pg_ctl', '-D', CLUSTER, '-l', DATOS / 'postgres.log', '-o',
                 f"-k {SOCKET} -p 55439 -c listen_addresses=''", '-w', 'start')
    import psycopg
    parametros = dict(host=str(SOCKET), port=55439, user='pims_admin', dbname='postgres')
    with psycopg.connect(**parametros, autocommit=True) as con:
        if not con.execute("SELECT 1 FROM pg_database WHERE datname='pims_riesgos'").fetchone():
            con.execute('CREATE DATABASE pims_riesgos')
        if not con.execute("SELECT 1 FROM pg_roles WHERE rolname='pims_lector'").fetchone():
            con.execute('CREATE ROLE pims_lector LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE')
        con.execute('REVOKE ALL ON DATABASE pims_riesgos FROM PUBLIC')
        con.execute('GRANT CONNECT ON DATABASE pims_riesgos TO pims_lector')
    parametros['dbname'] = 'pims_riesgos'
    with psycopg.connect(**parametros) as con:
        con.execute((BASE / 'db/schema.sql').read_text())
        con.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
        con.execute('GRANT USAGE ON SCHEMA pims_riesgos TO pims_lector')
        con.execute('GRANT SELECT ON ALL TABLES IN SCHEMA pims_riesgos TO pims_lector')
        for tabla in ('documentos','fragmentos'):
            if not con.execute('SELECT 1 FROM pg_policies WHERE schemaname=%s AND tablename=%s AND policyname=%s',
                               ('pims_riesgos',tabla,'lectura_agente')).fetchone():
                con.execute(f'CREATE POLICY lectura_agente ON pims_riesgos.{tabla} FOR SELECT TO pims_lector USING (true)')
    archivo = BASE / '.env'
    if not archivo.exists():
        from psycopg.conninfo import make_conninfo
        admin = make_conninfo(**parametros)
        parametros['user'] = 'pims_lector'
        lector = make_conninfo(**parametros)
        fd = os.open(archivo, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as salida:
            salida.write(f'PIMS_DATABASE_URL="{lector}"\nPIMS_DATABASE_ADMIN_URL="{admin}"\n')
    print('PostgreSQL privado iniciado. Configuración existente conservada; consulta .env.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion', choices=['iniciar','detener'])
    args = parser.parse_args()
    if args.accion == 'iniciar':
        iniciar()
    else:
        ejecutar('pg_ctl', '-D', CLUSTER, '-w', 'stop')
