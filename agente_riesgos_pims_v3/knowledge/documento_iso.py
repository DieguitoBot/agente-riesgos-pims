"""Recuperación local por temas; conserva trazabilidad del Markdown OCR del usuario."""
import hashlib
import re
import unicodedata
from pathlib import Path

from knowledge.controles_iso import catalogo_para_rol

DOCUMENTO = Path(__file__).resolve().parents[2] / 'ISO_IEC_27701_2025.md'
TEMAS = {
    'A.1.2.6': ['bienestar','salud','eipd','evaluacion de impacto'],
    'A.1.2.9': ['tratamiento','inventario','registro de tratamientos'],
    'A.3.5': ['bienestar','salud','clasifica','socioeconomic'],
    'A.3.8': ['cuenta','identidad','credenciales'],
    'A.1.4.9': ['elimina','disposicion','supresion','retencion'],
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
    if ruta is None:
        from db.repositorio import leer_norma
        return leer_norma("iso")
    texto = (ruta or DOCUMENTO).read_text(encoding='utf-8')
    lineas = texto.splitlines()
    # Limitar al cuerpo del anexo B: excluir índices y tablas de correspondencia.
    inicio = next(i for i, l in enumerate(lineas) if l.strip() == '## Annex B')
    fin = next((i for i in range(inicio + 1, len(lineas))
                if re.match(r'^## Annex [C-F]\b', lineas[i])), len(lineas))
    patron = re.compile(r'^(?:#{1,6}\s*)?(B[.,][123](?:[.,]\d+){1,2})[._]?\s+([A-Za-z].*)$')
    encabezados, pagina = [], None
    correcciones = {'B.14.4': 'B.1.4.4'}
    for i, linea in enumerate(lineas[:fin]):
        marca = re.search(r'<!-- Page (\d+) -->', linea)
        if marca:
            pagina = int(marca[1])
        candidata = linea
        corregida = None
        for original, canonico in correcciones.items():
            if re.match(r'^(?:#{1,6}\s*)?' + re.escape(original) + r'\s', linea):
                candidata = linea.replace(original, canonico, 1)
                corregida = original + ' → ' + canonico
        match = patron.match(candidata)
        if i > inicio and match:
            encabezados.append((i, match[1].replace(',', '.'), pagina, corregida))
    secciones = {}
    huella = hashlib.sha256((ruta or DOCUMENTO).read_bytes()).hexdigest()
    def fragmento(i, siguiente, codigo, pagina, correccion=None):
        return dict(seccion=codigo, pagina=pagina, linea=i + 1,
            texto='\n'.join(lineas[i:siguiente]).strip(), archivo=(ruta or DOCUMENTO).name,
            sha256=huella, version='2025', categoria='normativa', privado=True,
            estado_ocr='Pendiente de cotejo con PDF autorizado', correccion_ocr=correccion)
    for n, (i, codigo, pagina, corregida) in enumerate(encabezados):
        siguiente = encabezados[n + 1][0] if n + 1 < len(encabezados) else fin
        bloque = '\n'.join(lineas[i:siguiente]).strip()
        if re.search(r'^Control\s*$', bloque, re.M) and 'Implementation guidance' in bloque:
            secciones[codigo] = fragmento(i, siguiente, codigo, pagina, corregida)
    # Cuerpo principal: no confundir índice ni referencias cruzadas con cláusulas.
    inicio_a = next((i for i,l in enumerate(lineas) if l.strip() == '## Annex A'), inicio)
    numericos = [(i,m[1]) for i,l in enumerate(lineas[:inicio_a])
                 if (m := re.match(r'^(?:#{1,6}\s*)?([4-9](?:\.\d+){1,2})[.]?\s+[A-Z][A-Za-z ]+\s*$',l))
                 and not re.search(r'\.{3}|_{2}',l)]
    for n,(i,codigo) in enumerate(numericos):
        if codigo not in ('4.3','6.1.2','6.1.3','8.2','8.3'):
            continue
        siguiente = numericos[n+1][0] if n+1<len(numericos) else inicio_a
        pagina = next((int(m[1]) for l in reversed(lineas[:i+1]) if (m:=re.search(r'<!-- Page (\d+) -->',l))),None)
        secciones[codigo] = fragmento(i,siguiente,codigo,pagina,
            'Etiquetas de subapartados dañadas; conservar texto y cotejar enumeración' if codigo=='6.1.3' else None)
    # Conservar cada tabla A completa con su procedencia. El OCR impide atribuir
    # de forma fiable todos sus renglones: no fabricar controles A individuales.
    tablas = [(i,m[1]) for i,l in enumerate(lineas[inicio_a:inicio],inicio_a)
              if (m:=re.match(r'^Table (A[.]([123]))\s*[—–-]',l))]
    for n,(i,codigo) in enumerate(tablas):
        siguiente = tablas[n+1][0] if n+1<len(tablas) else inicio
        pagina = next((int(m[1]) for l in reversed(lineas[:i+1]) if (m:=re.search(r'<!-- Page (\d+) -->',l))),None)
        secciones[codigo] = fragmento(i,siguiente,codigo,pagina,'Códigos/tablas deteriorados por OCR; revisar PDF')
    return secciones, huella


def recuperar_contexto(descripcion, rol):
    try:
        secciones, huella = leer_secciones()
    except (OSError, UnicodeError, StopIteration):
        return dict(estado='no_disponible', fragmentos=[], sha256=None,
                    mensaje='No se pudo consultar la ISO en PostgreSQL. No hay sustento documental disponible.')
    texto = normalizar(descripcion)
    candidatos = []
    for codigo, control in catalogo_para_rol(rol).items():
        puntos = sum(1 for palabra in TEMAS.get(codigo, []) if palabra in texto)
        seccion = secciones.get(control['guia'])
        if puntos and seccion:
            # Limitar contexto, señalando explícitamente cualquier truncamiento.
            candidatos.append((puntos, dict(seccion, control=codigo, nombre=control['nombre'],
                texto=seccion['texto'][:1800], truncado=len(seccion['texto']) > 1800)))
    candidatos.sort(key=lambda item: (-item[0], item[1]['control']))
    fragmentos = [item[1] for item in candidatos[:8]]
    return dict(estado='recuperado' if fragmentos else 'sin_coincidencias', fragmentos=fragmentos,
        fundamentos=[{k:v for k,v in secciones[c].items() if k!='texto'} for c in ('4.3','6.1.2','6.1.3','8.2','8.3','A.1','A.2','A.3') if c in secciones],
        sha256=huella, mensaje='Fuente OCR aportada por el usuario; verificar ambigüedades con el PDF. '
        'Selección temática de guías; no demuestra exhaustividad normativa.')
