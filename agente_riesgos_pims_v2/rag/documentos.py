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
        if not p.is_file() or p.is_symlink() or p.suffix.lower() not in (".pdf", ".txt", ".md"):
            continue
        nombre = str(p.relative_to(raiz))
        if p.suffix.lower() == ".pdf":
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
