"""Lectura PostgreSQL; no usa archivos documentales como respaldo implícito."""
import os
from pathlib import Path
from contextlib import contextmanager


class BaseNoDisponible(OSError):
    pass


@contextmanager
def conectar(admin=False):
    try:
        import psycopg
        from dotenv import load_dotenv
    except ImportError as exc:
        raise BaseNoDisponible('Instala las dependencias PostgreSQL de requirements.txt.') from exc
    try:
        load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=False)
        variable = 'PIMS_DATABASE_ADMIN_URL' if admin else 'PIMS_DATABASE_URL'
        url = os.getenv(variable)
        if not url:
            raise BaseNoDisponible(f'Configura {variable} para la base exclusiva del agente.')
        with psycopg.connect(url, connect_timeout=5, prepare_threshold=None) as conexion:
            yield conexion
    except psycopg.Error as exc:
        # No exponer DSN, contraseñas o detalles de infraestructura en la API.
        raise BaseNoDisponible('No se pudo acceder a PostgreSQL del agente de riesgos.') from exc


def leer_norma(tipo):
    with conectar() as con:
        filas = con.execute('''SELECT f.codigo, f.datos, d.sha256
            FROM pims_riesgos.fragmentos f JOIN pims_riesgos.documentos d ON d.id=f.documento_id
            WHERE f.tipo=%s ORDER BY f.id''', (tipo,)).fetchall()
    if not filas:
        raise BaseNoDisponible('Norma todavía no migrada a PostgreSQL.')
    return {codigo: datos for codigo, datos, _ in filas}, filas[0][2]


def leer_fragmentos():
    with conectar() as con:
        return [fila[0] for fila in con.execute(
            "SELECT datos FROM pims_riesgos.fragmentos WHERE tipo='rag' ORDER BY id").fetchall()]


def inventario():
    with conectar() as con:
        return [dict(clave=c, categoria=t, sha256=h, fragmentos=n) for c,t,h,n in con.execute('''
            SELECT d.clave,d.categoria,d.sha256,count(f.id) FROM pims_riesgos.documentos d
            LEFT JOIN pims_riesgos.fragmentos f ON f.documento_id=d.id
            GROUP BY d.id ORDER BY d.categoria,d.clave''').fetchall()]


def leer_vectores(modelo):
    with conectar() as con:
        return con.execute("""SELECT datos,embedding FROM pims_riesgos.fragmentos
            WHERE tipo='rag' AND modelo_embedding=%s AND embedding IS NOT NULL ORDER BY id""",
            (modelo,)).fetchall()
