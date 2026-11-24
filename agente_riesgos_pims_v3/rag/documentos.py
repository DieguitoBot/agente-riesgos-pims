"""Fragmentos legibles, con solapamiento entre oraciones y procedencia por página."""
import re
from pathlib import Path
import pymupdf


def dividir(texto, tamano=1400, paso=1150):
    texto = re.sub(r"\s+", " ", texto).strip()
    if not texto:
        return []
    # Cortar por oraciones o palabras; nunca crear una cola aislada de pocos caracteres.
    fragmentos = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + tamano, len(texto))
        if fin < len(texto):
            candidatos = [m.end() for m in re.finditer(r'[.!?;]\s+', texto[inicio:fin])]
            cortes = [c for c in candidatos if c >= tamano // 2]
            fin = inicio + cortes[-1] if cortes else texto.rfind(" ", inicio + tamano // 2, fin)
            if fin <= inicio:
                fin = min(inicio + tamano, len(texto))
            if len(texto) - fin < 180:
                fin = len(texto)
        fragmentos.append(texto[inicio:fin].strip())
        if fin == len(texto):
            break
        proximo = max(inicio + 1, fin - max(0, tamano - paso))
        espacio = texto.find(" ", proximo, fin)
        inicio = espacio + 1 if espacio >= 0 else fin
    return fragmentos


def leer_documentos(carpeta):
    raiz = Path(carpeta)
    if not raiz.exists():
        return []
    salida = []
    for p in sorted(raiz.rglob("*")):
        if (not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(raiz.resolve())
                or p.suffix.lower() not in (".pdf", ".txt", ".md", ".docx")):
            continue
        nombre = str(p.relative_to(raiz))
        if p.parent.name == 'pims_unsa' and p.suffix.lower() != '.docx':
            continue  # Instrucciones de operación no son evidencia del PIMS.
        if p.suffix.lower() == '.docx':
            from knowledge.documento_pims import leer_docx
            doc = leer_docx(p)
            controles = {r['codigo']:r for r in doc['metadatos'].get('controles_soa',[])}
            metadatos = {k:v for k,v in doc['metadatos'].items() if k != 'controles_soa'}
            numero = 0
            for bloque in doc['bloques']:
                if bloque['seccion'] == 'Cabecera':
                    continue
                texto = (doc['metadatos']['codigo_documental'] + ' · ' + bloque['seccion'] + '\n'
                         + (bloque['cabecera'] + '\n' if 'cabecera' in bloque else '') + bloque['texto'])
                for parte, s in enumerate(dividir(texto), 1):
                    numero += 1
                    control = controles.get(bloque['texto'].split(' | ')[0])
                    extra = dict(control_soa=control['codigo'],aplicabilidad_soa=control['aplicabilidad'],
                                 estado_control=control['estado']) if control else {}
                    salida.append(dict(metadatos, **extra, archivo=nombre, pagina=None,
                                       fragmento=numero, texto=s, seccion=bloque['seccion'],
                                       localizador=bloque['localizador'] + f'/parte/{parte}'))
            continue
        if p.suffix.lower() == ".pdf":
            cache_ocr = p.parent.parent / ".ocr_cache" / f"{p.name}.json"
            if cache_ocr.exists():
                import json
                datos_ocr = json.loads(cache_ocr.read_text(encoding="utf-8"))
                with pymupdf.open(p) as doc:
                    bloques = []
                    for n, pagina in enumerate(doc, 1):
                        txt = pagina.get_text(sort=True).strip() or datos_ocr.get(str(n), "")
                        bloques.append((n, txt))
            else:
                with pymupdf.open(p) as doc:
                    bloques = [(n, pagina.get_text(sort=True)) for n, pagina in enumerate(doc, 1)]
        else:
            # Preservar los artículos/secciones en Markdown antes de fragmentar.
            bloques = [(None, b) for b in re.split(r'(?m)(?=^#{1,6} )', p.read_text(encoding="utf-8"))]
        for pagina, bloque in bloques:
            for s in dividir(bloque):
                if len(s) < 180 or len(s.split()) < 25:
                    continue
                salida.append(dict(archivo=nombre, pagina=pagina,
                                   fragmento=len(salida) + 1, texto=s))
    return salida
