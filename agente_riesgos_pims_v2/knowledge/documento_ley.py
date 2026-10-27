"""Recuperación de artículos del Markdown aportado; soporte para riesgos, no dictamen legal."""
import hashlib
import re
from pathlib import Path
from knowledge.documento_iso import normalizar

DOCUMENTO = Path(__file__).resolve().parents[2] / 'Ley-29733.md'
TEMAS = {
    '5': ['consentimiento', 'autorizacion'],
    '6': ['finalidad', 'publicidad', 'marketing'],
    '7': ['excesiv', 'innecesari', 'recolecta', 'recopila'],
    '8': ['conserva', 'retencion', 'sin plazo', 'indefinid', 'actualiza'],
    '9': ['acceso', 'permis', 'publico', 'cifrad', 'contrasena', 'respaldo'],
    '11': ['internacional', 'extranjero', 'transfronteriz'],
    '16': ['seguridad', 'acceso', 'autentic', 'cifrad', 'respaldo'],
    '17': ['comparte', 'compartid', 'divulga', 'enlace publico', 'correo'],
    '18': ['informa', 'aviso', 'consentimiento'],
    '20': ['rectifica', 'supresion', 'solicitud', 'derechos'],
}
AVISO = ('Texto aportado por el usuario, pendiente de cotejo con una versión oficial consolidada. '
         'Contiene concordancias históricas al reglamento de 2013; no se usan como normativa vigente. '
         'Las relaciones propuestas sirven para evaluar riesgos, no para certificar cumplimiento legal.')


def leer_articulos(ruta=None):
    ruta = ruta or DOCUMENTO
    texto = ruta.read_text(encoding='utf-8')
    lineas = texto.splitlines()
    patron = re.compile(r'^(?:#{1,6}\s*)?Artículo\s+(\d+)\.\s*(.*)$')
    encabezados = [(i, m[1], m[2]) for i, l in enumerate(lineas) if (m := patron.match(l))]
    articulos = {}
    for pos, (i, numero, titulo) in enumerate(encabezados):
        fin = encabezados[pos + 1][0] if pos + 1 < len(encabezados) else len(lineas)
        # Quitar concordancias históricas y encabezados del título siguiente.
        bloque = []
        for linea in lineas[i:fin]:
            if linea.startswith('CONCORDANCIAS:') or re.match(r'^## (?:TÍTULO|DISPOSICIONES)', linea):
                break
            bloque.append(linea)
        articulos[numero] = dict(articulo=numero, titulo=titulo, linea=i + 1,
                                archivo=ruta.name, texto='\n'.join(bloque).strip())
    return articulos, hashlib.sha256(texto.encode()).hexdigest()


def recuperar_contexto_legal(descripcion):
    try:
        articulos, huella = leer_articulos()
    except (OSError, UnicodeError):
        return dict(estado='no_disponible', fragmentos=[], sha256=None, mensaje=AVISO)
    texto = normalizar(descripcion)
    candidatos = [(sum(p in texto for p in palabras), numero)
                  for numero, palabras in TEMAS.items() if numero in articulos]
    candidatos.sort(key=lambda par: (-par[0], int(par[1])))
    elegidos = [numero for puntos, numero in candidatos if puntos]
    # El artículo 14 da contexto a las excepciones al consentimiento, sin proponer una brecha adicional.
    if '5' in elegidos and '14' in articulos:
        elegidos.append('14')
    fragmentos = [dict(articulos[n], texto=articulos[n]['texto'][:1800],
                      truncado=len(articulos[n]['texto']) > 1800) for n in elegidos]
    return dict(estado='recuperado' if fragmentos else 'sin_coincidencias',
                fragmentos=fragmentos, sha256=huella, mensaje=AVISO)


def validar_referencias(analisis, contexto, disponible):
    referencias, avisos = [], []
    fragmentos = {f['articulo']: f for f in contexto.get('contexto_legal', {}).get('fragmentos', [])}
    riesgos = {r['riesgo'] for r in analisis['riesgos_identificados']}
    for item in analisis.get('referencias_ley', []) if disponible else []:
        fragmento = fragmentos.get(item['articulo'])
        cita = ' '.join(item['cita_normativa'].split())
        if (not fragmento or not 20 <= len(cita) <= 160
                or cita not in ' '.join(fragmento['texto'].split())
                or cita in (' '.join(fragmento['texto'].splitlines()[0].split()), fragmento['titulo'])
                or item['riesgo'] not in riesgos
                or not item['evidencia'].strip()
                or item['evidencia'].casefold() not in contexto['descripcion'].casefold()):
            avisos.append('Se omitió una referencia legal sin artículo recuperado, cita verificable o hecho vinculado al riesgo.')
            continue
        referencias.append(dict(item, titulo=fragmento['titulo'], archivo=fragmento['archivo'],
            linea=fragmento['linea'], fuente='/api/fuente-ley/' + item['articulo'],
            estado='Posible brecha relacionada con el riesgo; pendiente de verificación'))
    return referencias, avisos
