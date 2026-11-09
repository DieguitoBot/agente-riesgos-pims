"""Mantenimiento explícito; nunca usado por las rutas HTTP."""
from contextlib import contextmanager
from pathlib import Path
import os
import shutil
import psycopg
from psycopg import sql
from dotenv import load_dotenv

NOMBRE = 'pims_riesgos_experimental'
ROL = 'pims_experimental_app'

def binario(nombre):
    ruta = shutil.which(nombre)
    candidatos = sorted(Path('/usr/lib/postgresql').glob(f'*/bin/{nombre}'), reverse=True)
    if ruta: return ruta
    if candidatos: return str(candidatos[0])
    raise SystemExit('Instala los binarios de PostgreSQL.')

def habilitar_lectura(con):
    con.execute(sql.SQL('GRANT USAGE ON SCHEMA pims_riesgos TO {}').format(sql.Identifier(ROL)))
    con.execute(sql.SQL('GRANT SELECT ON ALL TABLES IN SCHEMA pims_riesgos TO {}').format(sql.Identifier(ROL)))
    for tabla in ('documentos', 'fragmentos'):
        if not con.execute('SELECT 1 FROM pg_policies WHERE schemaname=%s AND tablename=%s AND policyname=%s', ('pims_riesgos', tabla, 'lectura_v3')).fetchone():
            con.execute(sql.SQL('CREATE POLICY lectura_v3 ON pims_riesgos.{} FOR SELECT TO {} USING (true)').format(sql.Identifier(tabla), sql.Identifier(ROL)))

@contextmanager
def conectar_admin():
    load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=False)
    url = os.getenv('PIMS_DATABASE_ADMIN_URL')
    if not url: raise ValueError('Configura PIMS_DATABASE_ADMIN_URL únicamente para mantenimiento de V3.')
    with psycopg.connect(url, connect_timeout=5) as con:
        if con.info.dbname != NOMBRE:
            raise ValueError('El mantenimiento solo admite la base de V3.')
        yield con
