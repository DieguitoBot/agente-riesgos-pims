"""Comprueba archivos aprobados y, opcionalmente, el corpus de la base original."""
import argparse
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-datos',action='store_true')
    args=parser.parse_args()
    referencia=json.loads((BASE/'BASE_APROBADA.json').read_text())
    origen=BASE.parent/referencia['carpeta_origen']
    diferentes=[n for n,h in referencia['sha256'].items()
                if not (origen/n).is_file() or hashlib.sha256((origen/n).read_bytes()).hexdigest()!=h]
    reporte={'archivos_comprobados':len(referencia['sha256']),'archivos_aprobados_sin_cambios':not diferentes,
             'archivos_diferentes':diferentes}
    if args.base_datos:
        from dotenv import dotenv_values
        import psycopg
        from preparar_experimento import huella_corpus
        valores=dotenv_values(origen/'.env')
        with psycopg.connect(valores['PIMS_DATABASE_ADMIN_URL']) as con:
            if con.info.dbname!='pims_riesgos': raise SystemExit('Base de origen no reconocida.')
            actual=huella_corpus(con)
        inicial=json.loads((BASE/'datos/base_verificada.json').read_text())
        reporte['corpus_aprobado_sin_cambios']=json.loads(json.dumps(actual))==inicial['huellas_aprobada_antes']
        from db.repositorio import conectar
        with conectar() as con:
            reporte['base_experimental']=con.info.dbname
            reporte['rol_experimental_sin_acceso_a_base_aprobada']=not con.execute(
                "SELECT has_database_privilege(current_user,'pims_riesgos','CONNECT')").fetchone()[0]
            reporte['corpus_experimental_solo_lectura']=not con.execute(
                "SELECT has_table_privilege(current_user,'pims_riesgos.fragmentos','UPDATE')").fetchone()[0]
    (BASE/'datos').mkdir(mode=0o700,exist_ok=True)
    (BASE/'datos/aislamiento_verificado.json').write_text(json.dumps(reporte,indent=2))
    print(json.dumps(reporte,indent=2))
    if diferentes or any(v is False for v in reporte.values() if isinstance(v,bool)):
        raise SystemExit(1)


if __name__=='__main__': main()
