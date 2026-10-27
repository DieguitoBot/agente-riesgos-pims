"""Recuperación local por temas; conserva trazabilidad del Markdown OCR del usuario."""
import hashlib
import re
import unicodedata
from pathlib import Path

from knowledge.controles_iso import catalogo_para_rol

DOCUMENTO = Path(__file__).resolve().parents[2] / 'ISO_IEC_27701_2025.md'
TEMAS = {
    'A.1.2.2': ['finalidad', 'proposito', 'publicidad', 'marketing'],
    'A.1.2.3': ['consentimiento', 'base legal', 'autorizacion'],
    'A.1.3.10': ['solicitud', 'derechos', 'rectificacion', 'supresion'],
    'A.1.4.2': ['excesiv', 'innecesari', 'recopila', 'recolecta'],
    'A.1.4.8': ['conserva', 'indefinid', 'retencion', 'sin plazo', 'egresa', 'elimina'],
    'A.2.2.2': ['contrato', 'proveedor', 'cliente', 'encargado'],
    'A.2.4.3': ['devol', 'elimina', 'conserva', 'contrato'],
    'A.3.7': ['envia', 'transfer', 'correo', 'comparte', 'compartid'],
    'A.3.9': ['acceso', 'permis', 'publico', 'compartid', 'roles', 'cuenta'],
    'A.3.23': ['contrasena', 'autentic', 'misma cuenta', 'compartid'],
    'A.3.24': ['copia', 'respaldo', 'backup', 'recuper', 'perdida'],
    'A.3.25': ['registra', 'registro', 'trazabilidad', 'log', 'acceso'],
    'A.3.26': ['cifrad', 'criptograf', 'texto plano', 'usb'],
}


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold())
                   if unicodedata.category(c) != 'Mn')


def leer_secciones(ruta=None):
    texto = (ruta or DOCUMENTO).read_text(encoding='utf-8')
    lineas = texto.splitlines()
    # Limitar al cuerpo del anexo B: excluir índices y tablas de correspondencia.
    inicio = next(i for i, l in enumerate(lineas) if l.strip() == '## Annex B')
    fin = next((i for i in range(inicio + 1, len(lineas))
                if re.match(r'^## Annex [C-F]\b', lineas[i])), len(lineas))
    patron = re.compile(r'^(?:#{1,6}\s*)?(B[.,][123](?:[.,]\d+){1,2})[._]?\s+([A-Za-z].*)$')
    encabezados = []
    pagina = None
    for i, linea in enumerate(lineas[:fin]):
        marca = re.search(r'<!-- Page (\d+) -->', linea)
        if marca:
            pagina = int(marca[1])
        match = patron.match(linea)
        if i > inicio and match:
            encabezados.append((i, match[1].replace(',', '.'), pagina))
    secciones = {}
    for n, (i, codigo, pagina) in enumerate(encabezados):
        siguiente = encabezados[n + 1][0] if n + 1 < len(encabezados) else fin
        bloque = '\n'.join(lineas[i:siguiente]).strip()
        # Solo secciones reconocidas que contienen el control y su guía.
        if re.search(r'^Control\s*$', bloque, re.M) and 'Implementation guidance' in bloque:
            secciones[codigo] = dict(seccion=codigo, pagina=pagina, linea=i + 1,
                texto=bloque, archivo=(ruta or DOCUMENTO).name)
    return secciones, hashlib.sha256(texto.encode()).hexdigest()


def recuperar_contexto(descripcion, rol):
    try:
        secciones, huella = leer_secciones()
    except (OSError, UnicodeError, StopIteration):
        return dict(estado='no_disponible', fragmentos=[], sha256=None,
                    mensaje='No se pudo leer el Markdown ISO. No hay sustento documental local disponible.')
    texto = normalizar(descripcion)
    candidatos = []
    for codigo, control in catalogo_para_rol(rol).items():
        puntos = sum(1 for palabra in TEMAS.get(codigo, []) if palabra in texto)
        seccion = secciones.get(control['guia'])
        if puntos and seccion:
            # Limitar contexto, señalando explícitamente cualquier truncamiento.
            candidatos.append((puntos, dict(seccion, control=codigo, nombre=control['nombre'],
                texto=seccion['texto'][:2200], truncado=len(seccion['texto']) > 2200)))
    candidatos.sort(key=lambda item: (-item[0], item[1]['control']))
    fragmentos = [item[1] for item in candidatos]
    return dict(estado='recuperado' if fragmentos else 'sin_coincidencias', fragmentos=fragmentos,
        sha256=huella, mensaje='Fuente OCR aportada por el usuario; verificar ambigüedades con el PDF. '
        'Selección por temas sobre un catálogo parcial; no demuestra exhaustividad normativa.')
