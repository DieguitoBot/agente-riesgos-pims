"""Crea una base experimental aislada a partir de una lectura de la base aprobada."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from dotenv import dotenv_values

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent
NOMBRE = 'pims_riesgos_experimental'
ROL = 'pims_experimental_app'


def binario(nombre):
    encontrado = shutil.which(nombre)
    candidatos = sorted(Path('/usr/lib/postgresql').glob(f'*/bin/{nombre}'), reverse=True)
    if encontrado:
        return encontrado
    if candidatos:
        return str(candidatos[0])
    raise SystemExit('No se encuentran los binarios de PostgreSQL.')


def huella_corpus(con):
    salida = {}
    for tabla in ('documentos', 'fragmentos', 'controles_iso'):
        if not con.execute('SELECT to_regclass(%s)', ('pims_riesgos.'+tabla,)).fetchone()[0]:
            salida[tabla] = (0, None)
            continue
        salida[tabla] = con.execute(sql.SQL(
            'SELECT count(*), md5(string_agg(md5(to_jsonb(t)::text),\'\' ORDER BY to_jsonb(t)::text)) '
            'FROM pims_riesgos.{} t').format(sql.Identifier(tabla))).fetchone()
    return salida


def main():
    os.umask(0o077)
    (BASE / 'datos').mkdir(mode=0o700, exist_ok=True)
    archivo = BASE / '.env'
    if archivo.exists():
        print('La configuración experimental ya existe; no se reemplaza ni se reimporta.')
        return
    valores = dotenv_values(RAIZ / 'agente_riesgos_pims_v2/.env')
    parametros = conninfo_to_dict(valores.get('PIMS_DATABASE_ADMIN_URL') or '')
    if (parametros.get('dbname') != 'pims_riesgos'
            or parametros.get('host') != str(RAIZ / '.datos/socket')):
        raise SystemExit('Se requiere la base privada local aprobada; no se opera sobre otro servidor.')
    with psycopg.connect(**parametros) as con:
        antes = huella_corpus(con)
    control = dict(parametros, dbname='postgres')
    clave = secrets.token_urlsafe(32)
    with psycopg.connect(**control, autocommit=True) as con:
        if con.execute('SELECT 1 FROM pg_database WHERE datname=%s', (NOMBRE,)).fetchone():
            raise SystemExit('Ya existe la base experimental sin configuración; revisar antes de continuar.')
        if con.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (ROL,)).fetchone():
            raise SystemExit('Ya existe el rol experimental; revisar antes de continuar.')
        con.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE').format(
            sql.Identifier(ROL), sql.Literal(clave)))
        con.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(NOMBRE)))
        con.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(NOMBRE)))
        con.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(NOMBRE), sql.Identifier(ROL)))
    entorno = os.environ.copy()
    for campo, variable in (('host','PGHOST'),('port','PGPORT'),('user','PGUSER'),('password','PGPASSWORD')):
        if campo in parametros:
            entorno[variable] = str(parametros[campo])
    entorno['PGDATABASE'] = 'pims_riesgos'
    respaldo = BASE / 'datos/corpus_inicial.dump'
    subprocess.run([binario('pg_dump'), '-Fc', '--no-owner', '--no-acl', '--schema=pims_riesgos',
                    '--file', str(respaldo)], env=entorno, check=True)
    entorno['PGDATABASE'] = NOMBRE
    subprocess.run([binario('pg_restore'), '--no-owner', '--no-acl', '--exit-on-error',
                    '--dbname', NOMBRE, str(respaldo)], env=entorno, check=True)
    destino = dict(parametros, dbname=NOMBRE)
    with psycopg.connect(**destino) as con:
        con.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
        con.execute(sql.SQL('GRANT USAGE ON SCHEMA pims_riesgos TO {}').format(sql.Identifier(ROL)))
        con.execute(sql.SQL('GRANT SELECT ON ALL TABLES IN SCHEMA pims_riesgos TO {}').format(sql.Identifier(ROL)))
        for tabla in ('documentos','fragmentos','controles_iso'):
            if not con.execute('SELECT to_regclass(%s)', ('pims_riesgos.'+tabla,)).fetchone()[0]:
                continue
            con.execute(sql.SQL('CREATE POLICY lectura_experimental ON pims_riesgos.{} FOR SELECT TO {} USING (true)').format(
                sql.Identifier(tabla), sql.Identifier(ROL)))
        con.execute((BASE / 'db/experimento.sql').read_text())
        copia = huella_corpus(con)
    with psycopg.connect(**parametros) as con:
        despues = huella_corpus(con)
    if antes != despues or antes != copia:
        raise SystemExit('La comprobación del corpus no coincide; no se activa la configuración experimental.')
    app = dict(destino, user=ROL, password=clave)
    dsn = make_conninfo(**app)
    fd = os.open(archivo, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write('PIMS_DATABASE_URL=' + json.dumps(dsn) + '\n')
    (BASE / 'datos/base_verificada.json').write_text(json.dumps({
        'base_aprobada': 'pims_riesgos', 'base_experimental': NOMBRE,
        'huellas_aprobada_antes': antes, 'huellas_aprobada_despues': despues,
        'huellas_copia': copia, 'coinciden': True}, indent=2))
    print('Base experimental creada; corpus copiado y base aprobada verificada sin cambios.')


if __name__ == '__main__':
    main()
