"""Lectura PostgreSQL; no usa archivos documentales como respaldo implícito."""
from mantenimiento.metricas import medir
import os
from pathlib import Path
from contextlib import contextmanager


class BaseNoDisponible(OSError):
    pass


# La base actual separa texto y procedencia en columnas. El esquema histórico
# conservaba esos campos dentro de datos. Las columnas presentes prevalecen y
# los NULL no borran metadatos históricos. to_jsonb permite leer ambos esquemas
# sin modificar el corpus ni exigir columnas que una instalación antigua no tiene.
DATOS_FRAGMENTO_SQL = """jsonb_build_object('pagina', NULL) || f.datos ||
    jsonb_strip_nulls(to_jsonb(f) - ARRAY[
        'id', 'documento_id', 'tipo', 'codigo', 'datos',
        'embedding', 'modelo_embedding', 'busqueda'
    ]::text[])"""
DATOS_CON_FUENTE_SQL = """jsonb_build_object('sha256', d.sha256,
    'categoria', d.categoria, 'version', d.metadatos->>'version',
    'clave_documento', d.clave) || """ + DATOS_FRAGMENTO_SQL


@contextmanager
def conectar(admin=False):
    if admin:
        raise BaseNoDisponible('La aplicación experimental no usa la conexión administrativa.')
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
            if conexion.info.dbname != 'pims_riesgos_experimental':
                raise BaseNoDisponible('La aplicación experimental solo puede usar su base aislada.')
            yield conexion
    except psycopg.Error as exc:
        # No exponer DSN, contraseñas o detalles de infraestructura en la API.
        raise BaseNoDisponible('No se pudo acceder a PostgreSQL del agente de riesgos.') from exc


@medir('postgresql.leer_norma')
def leer_norma(tipo):
    with conectar() as con:
        filas = con.execute(f'''SELECT f.codigo, {DATOS_FRAGMENTO_SQL}, d.sha256
            FROM pims_riesgos.fragmentos f JOIN pims_riesgos.documentos d ON d.id=f.documento_id
            WHERE f.tipo=%s ORDER BY f.id''', (tipo,)).fetchall()
    if not filas:
        raise BaseNoDisponible('Norma todavía no migrada a PostgreSQL.')
    return {codigo: datos for codigo, datos, _ in filas}, filas[0][2]


@medir('postgresql.leer_fragmentos')
def leer_fragmentos():
    with conectar() as con:
        return [fila[0] for fila in con.execute(f"""
            SELECT {DATOS_CON_FUENTE_SQL} FROM pims_riesgos.fragmentos f
            JOIN pims_riesgos.documentos d ON d.id=f.documento_id
            WHERE f.tipo='rag' ORDER BY f.id""").fetchall()]


@medir('postgresql.inventario')
def inventario():
    with conectar() as con:
        return [dict(clave=c, categoria=t, sha256=h, fragmentos=n, metadatos=m,
                     indexados=indexados) for c,t,h,n,m,indexados in con.execute('''
            SELECT d.clave,d.categoria,d.sha256,count(f.id),d.metadatos,
                count(f.id) FILTER (WHERE f.embedding IS NOT NULL)
            FROM pims_riesgos.documentos d
            LEFT JOIN pims_riesgos.fragmentos f ON f.documento_id=d.id
            GROUP BY d.id ORDER BY d.categoria,d.clave''').fetchall()]


@medir('postgresql.leer_fuente_rag')
def leer_fuente_rag(huella, codigo):
    with conectar() as con:
        fila = con.execute(f'''SELECT {DATOS_CON_FUENTE_SQL}
            FROM pims_riesgos.fragmentos f JOIN pims_riesgos.documentos d ON d.id=f.documento_id
            WHERE d.sha256=%s AND f.tipo='rag' AND f.codigo=%s''', (huella, codigo)).fetchone()
        if not fila:
            fila = con.execute('''SELECT f.datos FROM pims_riesgos.versiones_documentales v,
                LATERAL jsonb_array_elements(v.fragmentos) AS f(datos)
                WHERE v.sha256=%s AND f.datos->>'fragmento'=%s LIMIT 1''', (huella, codigo)).fetchone()
    return fila[0] if fila else None


@medir('postgresql.leer_soa')
def leer_soa():
    with conectar() as con:
        fila=con.execute("""SELECT metadatos->'controles_soa',metadatos->>'version',sha256
            FROM pims_riesgos.documentos WHERE metadatos->>'codigo_documental'='PIMS-RIE-04'""").fetchone()
    return dict(controles=fila[0] or [],version=fila[1],sha256=fila[2]) if fila else dict(controles=[],version=None,sha256=None)


@medir('postgresql.leer_seccion_iso')
def leer_seccion_iso(codigo, huella):
    with conectar() as con:
        fila=con.execute("""SELECT f.datos FROM pims_riesgos.fragmentos f
            JOIN pims_riesgos.documentos d ON d.id=f.documento_id
            WHERE f.tipo='iso' AND f.codigo=%s AND d.sha256=%s""",(codigo,huella)).fetchone()
        if not fila:
            fila=con.execute("""SELECT f.datos FROM pims_riesgos.versiones_documentales v,
                LATERAL jsonb_array_elements(v.fragmentos) f(datos)
                WHERE v.sha256=%s AND f.datos->>'seccion'=%s AND NOT(f.datos ? 'fragmento') LIMIT 1""",(huella,codigo)).fetchone()
    return fila[0] if fila else None


@medir('postgresql.leer_vectores')
def leer_vectores(modelo):
    with conectar() as con:
        return con.execute(f"""SELECT {DATOS_CON_FUENTE_SQL}, f.embedding
            FROM pims_riesgos.fragmentos f JOIN pims_riesgos.documentos d ON d.id=f.documento_id WHERE f.tipo='rag'
            AND f.modelo_embedding=%s AND f.embedding IS NOT NULL ORDER BY f.id""",
            (modelo,)).fetchall()
