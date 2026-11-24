"""Importación inicial explícita e idempotente: python -m db.migrar [--inventario]."""
import argparse
import hashlib
import json
from pathlib import Path

from db.repositorio import inventario
from db.admin import conectar_admin

BASE = Path(__file__).resolve().parents[1]
RAIZ = BASE.parent


def preparar():
    # Lista cerrada dentro de este repositorio: nunca recorre carpetas de otros agentes.
    from knowledge.documento_iso import leer_secciones
    from knowledge.documento_ley import leer_articulos
    from rag.documentos import leer_documentos
    import pymupdf
    rutas = [RAIZ / 'ISO_IEC_27701_2025.md', RAIZ / 'Ley-29733.md']
    rutas += sorted(p for p in (BASE / 'knowledge/documentos').glob('*') if p.is_file())
    rutas += sorted((BASE / 'knowledge/documentos/pims_unsa').glob('*.docx'))
    rutas += [RAIZ / n for n in ('Contexto.txt','InstruccionesAgente','ESTADO_VALIDACION.md','README.md','CONTRIBUTING.md')]
    rutas += sorted((RAIZ / 'docs').glob('*.md'))
    rutas += sorted(BASE.glob('*.md')) + sorted((BASE / 'knowledge').glob('*.md'))
    rutas += sorted(BASE.glob('reporte_*.txt')) + sorted(RAIZ.glob('Captura desde *.png'))
    fragmentos_rag = leer_documentos(BASE / 'knowledge/documentos')
    salida, codigos_pims = [], {}
    for ruta in rutas:
        if not ruta.is_file():
            continue
        if ruta.is_symlink() or not ruta.resolve().is_relative_to(RAIZ):
            raise ValueError('Fuente fuera del proyecto o enlace simbólico.')
        original = ruta.read_bytes()
        clave = str(ruta.relative_to(RAIZ))
        categoria, fragmentos, meta_pims = 'proyecto', [], {}
        if ruta.suffix == '.docx':
            from knowledge.documento_pims import leer_docx
            doc = leer_docx(ruta)
            contenido, meta_pims = doc['contenido'], doc['metadatos']
            codigo = meta_pims['codigo_documental']
            if codigo in codigos_pims:
                if codigos_pims[codigo] != meta_pims['sha256']:
                    raise ValueError(f'Dos fuentes distintas para el mismo código PIMS: {codigo}')
                continue
            codigos_pims[codigo] = meta_pims['sha256']
        elif ruta.suffix == '.pdf':
            cache_ocr = BASE / 'knowledge/.ocr_cache' / f'{ruta.name}.json'
            if cache_ocr.exists():
                datos_ocr = json.loads(cache_ocr.read_text(encoding='utf-8'))
                with pymupdf.open(ruta) as doc:
                    contenido = '\n'.join(p.get_text(sort=True).strip() or datos_ocr.get(str(n), '') for n, p in enumerate(doc, 1))
            else:
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
            from rag.documentos import dividir
            numero = 0
            for codigo, fuente in secciones.items():
                for parte, texto in enumerate(dividir(fuente['texto']), 1):
                    numero += 1
                    datos = dict(fuente, texto=texto, fragmento=numero,
                                 localizador=f"línea/{fuente['linea']}/sección/{codigo}/parte/{parte}",
                                 tipo_fuente='iso', titulo=f'ISO/IEC 27701:2025 · {codigo}')
                    fragmentos.append(('rag', str(numero), datos))
            meta_pims = dict(version='2025', privado=True, extractor='iso-v2',
                             estado_ocr='Cotejo PDF pendiente; correcciones de identificador registradas')
        elif ruta == RAIZ / 'Ley-29733.md':
            categoria = 'normativa'
            articulos, _ = leer_articulos(ruta)
            if not articulos:
                raise ValueError('No se encontraron artículos de la ley.')
            fragmentos = [('ley', c, f) for c, f in articulos.items()]
        elif ruta.is_relative_to(BASE / 'knowledge/documentos'):
            categoria = ('proyecto' if meta_pims else
                         'normativa' if ruta.name == 'ley_29733.md' else 'institucional')
            nombre = str(ruta.relative_to(BASE / 'knowledge/documentos'))
            fragmentos = [('rag', str(f['fragmento']), f) for f in fragmentos_rag if f['archivo'] == nombre]
        elif ruta.name.startswith('reporte_'):
            categoria = 'reporte'
        salida.append((clave,categoria,meta_pims.get('titulo', ruta.stem),hashlib.sha256(original).hexdigest(),contenido,original,
                       {'fuente_original':clave,'verificacion':'pendiente','formato':ruta.suffix,
                        'uso':'consulta' if fragmentos else 'archivo', **meta_pims},fragmentos))
    return salida


def migrar(claves=None):
    from psycopg.types.json import Jsonb
    documentos = preparar()  # Extraer antes de iniciar la transacción.
    if claves:
        documentos = [d for d in documentos if d[0] in claves or Path(d[0]).name in claves
                       or d[6].get('codigo_documental') in claves]
        if not documentos:
            raise ValueError('No se encontraron las fuentes solicitadas; no se modifica PostgreSQL.')
    with conectar_admin() as con:
        con.execute((BASE / 'db/schema.sql').read_text())
        from db.admin import habilitar_lectura
        habilitar_lectura(con)
        for clave,categoria,titulo,huella,contenido,original,meta,fragmentos in documentos:
            if meta.get('codigo_documental'):
                anterior = con.execute("SELECT clave FROM pims_riesgos.documentos WHERE metadatos->>'codigo_documental'=%s",
                                       (meta['codigo_documental'],)).fetchone()
                if anterior:
                    clave = anterior[0]  # Renombrar la fuente no duplica el documento.
            # Archivar fuentes de cualquier categoría antes de sustituir sus bytes.
            con.execute('''INSERT INTO pims_riesgos.versiones_documentales
                    (clave,sha256,original,metadatos,fragmentos)
                    SELECT d.clave,d.sha256,d.original,d.metadatos,
                        COALESCE(jsonb_agg(f.datos ORDER BY f.id) FILTER (WHERE f.id IS NOT NULL), '[]'::jsonb)
                    FROM pims_riesgos.documentos d
                    LEFT JOIN pims_riesgos.fragmentos f ON f.documento_id=d.id
                    WHERE d.clave=%s AND d.sha256<>%s GROUP BY d.id
                    ON CONFLICT(clave,sha256) DO NOTHING''', (clave, huella))
            fila = con.execute('''INSERT INTO pims_riesgos.documentos
                (clave,categoria,titulo,sha256,contenido,original,metadatos) VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(clave) DO UPDATE SET categoria=excluded.categoria,titulo=excluded.titulo,
                sha256=excluded.sha256,contenido=excluded.contenido,original=excluded.original,
                metadatos=excluded.metadatos,actualizado=CASE WHEN
                (pims_riesgos.documentos.sha256,pims_riesgos.documentos.metadatos) IS DISTINCT FROM
                (excluded.sha256,excluded.metadatos) THEN now() ELSE pims_riesgos.documentos.actualizado END RETURNING id''',
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
    parser.add_argument('--simular', action='store_true', help='Validar extracción sin conexión ni escrituras SQL')
    parser.add_argument('--solo', nargs='+', help='Actualizar únicamente códigos o rutas/nombres indicados')
    args = parser.parse_args()
    if args.simular:
        print(json.dumps([dict(clave=d[0], categoria=d[1], sha256=d[3],
                               metadatos=d[6], fragmentos=len(d[7])) for d in preparar()],
                         ensure_ascii=False, indent=2))
    elif args.inventario:
        print(json.dumps(inventario(), ensure_ascii=False, indent=2))
    else:
        print('Documentos procesados:', migrar(args.solo))
