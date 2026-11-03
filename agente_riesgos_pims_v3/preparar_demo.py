"""Prepara una demostración autónoma sin leer la base aprobada ni sus credenciales."""
import json
import os
from pathlib import Path
import secrets
import subprocess

import psycopg
from psycopg.conninfo import make_conninfo
from preparar_experimento import binario, NOMBRE, ROL

BASE=Path(__file__).resolve().parent
DATOS=BASE/'datos'
CLUSTER=DATOS/'postgres_demo'
SOCKET=DATOS/'socket_demo'


def iniciar_cluster():
    DATOS.mkdir(mode=0o700,exist_ok=True)
    SOCKET.mkdir(mode=0o700,exist_ok=True)
    if not (CLUSTER/'PG_VERSION').exists():
        subprocess.run([binario('initdb'),'-D',str(CLUSTER),'-U','pims_demo_admin',
                        '--auth-local=trust','--auth-host=reject','--encoding=UTF8','--no-locale'],check=True)
    estado=subprocess.run([binario('pg_ctl'),'-D',str(CLUSTER),'status'],capture_output=True)
    if estado.returncode:
        subprocess.run([binario('pg_ctl'),'-D',str(CLUSTER),'-l',str(DATOS/'postgres_demo.log'),
                        '-o',f"-k {SOCKET} -p 55440 -c listen_addresses=''",'-w','start'],check=True)


def main():
    os.umask(0o077)
    if (BASE/'.env').exists():
        print('Ya hay una configuración; no se reemplaza. Usa bash iniciar.sh.')
        return
    iniciar_cluster()
    parametros=dict(host=str(SOCKET),port=55440,user='pims_demo_admin',dbname='postgres')
    clave=secrets.token_urlsafe(32)
    from psycopg import sql
    with psycopg.connect(**parametros,autocommit=True) as con:
        if con.execute('SELECT 1 FROM pg_database WHERE datname=%s',(NOMBRE,)).fetchone():
            raise SystemExit('Existe una preparación incompleta; no se sobrescriben sus tablas.')
        con.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE').format(sql.Identifier(ROL),sql.Literal(clave)))
        con.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(NOMBRE)))
        con.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(NOMBRE)))
        con.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(NOMBRE),sql.Identifier(ROL)))
    parametros['dbname']=NOMBRE
    with psycopg.connect(**parametros) as con:
        con.execute((BASE/'db/corpus_demo.sql').read_text())
        con.execute((BASE/'db/experimento.sql').read_text())
    dsn=make_conninfo(**dict(parametros,user=ROL,password=clave))
    fd=os.open(BASE/'.env',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as salida:
        salida.write('PIMS_DATABASE_URL='+json.dumps(dsn)+'\n')
        salida.write('PIMS_MODO_DEMO=1\n')
    from demo import crear_resultado_demo
    from experimento import guardar_evaluacion
    id_demo=guardar_evaluacion(crear_resultado_demo(),procedencia='demostracion')
    print('Demostración preparada con un ejemplo ficticio:',id_demo)
    print('Inicia con bash iniciar.sh y abre Historial y comparación.')


if __name__=='__main__': main()
