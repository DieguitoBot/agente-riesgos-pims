"""Importación inicial explícita e idempotente: python -m db.migrar [--inventario]."""
import argparse
import hashlib
import json
from pathlib import Path

from db.repositorio import conectar, inventario

BASE = Path(__file__).resolve().parents[1]
RAIZ = BASE.parent


def preparar():
    # Lista cerrada dentro de este repositorio: nunca recorre carpetas de otros agentes.
    from knowledge.documento_iso import leer_secciones
    from knowledge.documento_ley import leer_articulos
    from rag.documentos import leer_documentos
    import pymupdf
    rutas = [RAIZ / 'ISO_IEC_27701_2025.md', RAIZ / 'Ley-29733.md']
    rutas += sorted((BASE / 'knowledge/documentos').glob('*'))
    rutas += [RAIZ / n for n in ('Contexto.txt','InstruccionesAgente','ESTADO_VALIDACION.md','README.md','CONTRIBUTING.md')]
    rutas += sorted((RAIZ / 'docs').glob('*.md'))
    rutas += sorted(BASE.glob('*.md')) + sorted((BASE / 'knowledge').glob('*.md'))
    rutas += sorted(BASE.glob('reporte_*.txt')) + sorted(RAIZ.glob('Captura desde *.png'))
    fragmentos_rag = leer_documentos(BASE / 'knowledge/documentos')
    salida = []
    for ruta in rutas:
        if not ruta.exists():
            continue
        if ruta.is_symlink() or not ruta.resolve().is_relative_to(RAIZ):
            raise ValueError('Fuente fuera del proyecto o enlace simbólico.')
        original = ruta.read_bytes()
        clave = str(ruta.relative_to(RAIZ))
        categoria, fragmentos = 'proyecto', []
        if ruta.suffix == '.pdf':
            with pymupdf.open(ruta) as doc:
                contenido = '\n'.join(p.get_text(sort=True) for p in doc)
            if not contenido.strip():
                raise ValueError(f'PDF sin texto extraíble: {clave}; requiere OCR.')
        elif ruta.suffix == '.png':
            contenido, categoria = '', 'evidencia'
        else:
            contenido = original.decode('utf-8')
        if ruta == RAIZ / 'ISO_IEC_27701_2025.md':
            categoria = 'normativa'
            secciones, _ = leer_secciones(ruta)
            if not secciones:
                raise ValueError('No se encontraron secciones ISO.')
            fragmentos = [('iso', c, f) for c, f in secciones.items()]
        elif ruta == RAIZ / 'Ley-29733.md':
            categoria = 'normativa'
            articulos, _ = leer_articulos(ruta)
            if not articulos:
                raise ValueError('No se encontraron artículos de la ley.')
            fragmentos = [('ley', c, f) for c, f in articulos.items()]
        elif ruta.parent == BASE / 'knowledge/documentos':
            categoria = 'normativa' if ruta.name == 'ley_29733.md' else 'institucional'
            fragmentos = [('rag', str(f['fragmento']), f) for f in fragmentos_rag if f['archivo'] == ruta.name]
        elif ruta.name.startswith('reporte_'):
            categoria = 'reporte'
        salida.append((clave,categoria,ruta.stem,hashlib.sha256(original).hexdigest(),contenido,original,
                       {'fuente_original':clave,'verificacion':'pendiente','formato':ruta.suffix,
                        'uso':'consulta' if fragmentos else 'archivo'},fragmentos))
    return salida


def migrar():
    from psycopg.types.json import Jsonb
    documentos = preparar()  # Extraer antes de iniciar la transacción.
    with conectar(admin=True) as con:
        con.execute((BASE / 'db/schema.sql').read_text())
        for clave,categoria,titulo,huella,contenido,original,meta,fragmentos in documentos:
            fila = con.execute('''INSERT INTO pims_riesgos.documentos
                (clave,categoria,titulo,sha256,contenido,original,metadatos) VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(clave) DO UPDATE SET categoria=excluded.categoria,titulo=excluded.titulo,
                sha256=excluded.sha256,contenido=excluded.contenido,original=excluded.original,
                metadatos=excluded.metadatos,actualizado=now() RETURNING id''',
                (clave,categoria,titulo,huella,contenido,original,Jsonb(meta))).fetchone()
            claves = [tipo + ':' + codigo for tipo,codigo,_ in fragmentos]
            con.execute("DELETE FROM pims_riesgos.fragmentos WHERE documento_id=%s AND NOT (tipo || ':' || codigo = ANY(%s))", (fila[0], claves))
            for tipo,codigo,datos in fragmentos:
                con.execute('''INSERT INTO pims_riesgos.fragmentos(documento_id,tipo,codigo,datos)
                    VALUES (%s,%s,%s,%s) ON CONFLICT(documento_id,tipo,codigo) DO UPDATE SET
                    embedding=CASE WHEN pims_riesgos.fragmentos.datos=excluded.datos THEN pims_riesgos.fragmentos.embedding ELSE NULL END,
                    modelo_embedding=CASE WHEN pims_riesgos.fragmentos.datos=excluded.datos THEN pims_riesgos.fragmentos.modelo_embedding ELSE NULL END,
                    datos=excluded.datos''', (fila[0],tipo,codigo,Jsonb(datos)))
    return len(documentos)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventario', action='store_true')
    args = parser.parse_args()
    if args.inventario:
        print(json.dumps(inventario(), ensure_ascii=False, indent=2))
    else:
        print('Documentos migrados:', migrar())
