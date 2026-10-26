"""Extrae texto de PDF, TXT y Markdown; conserva archivo y página."""
import re
from pathlib import Path
import fitz


def dividir(texto, tamano=1100, paso=900):
    texto = re.sub(r"\s+", " ", texto).strip()
    return [texto[i:i + tamano] for i in range(0, len(texto), paso) if texto[i:i + tamano].strip()]


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
            with fitz.open(p) as doc:
                for n, pagina in enumerate(doc, 1):
                    for j, s in enumerate(dividir(pagina.get_text())):
                        salida.append(dict(archivo=nombre, pagina=n, fragmento=j + 1, texto=s))
        else:
            for j, s in enumerate(dividir(p.read_text(encoding="utf-8"))):
                salida.append(dict(archivo=nombre, pagina=None, fragmento=j + 1, texto=s))
    return salida
