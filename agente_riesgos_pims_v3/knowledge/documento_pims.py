"""Lectura DOCX sin conversión: conserva tablas y localizadores del XML original.

Un localizador identifica párrafo o fila, nunca una página renderizada de Word.
Los metadatos describen lo declarado por el documento, no una validación ISO.
"""
import hashlib
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
CODIGO = r'PIMS-RIE-\d{2}[AB]?'


def _texto(nodo):
    return ' '.join(''.join(t.text or '' for t in p.findall('.//w:t', NS))
                    for p in nodo.findall('.//w:p', NS)).strip()


def leer_docx(ruta):
    ruta = Path(ruta)
    original = ruta.read_bytes()
    with ZipFile(ruta) as archivo:
        cuerpo = ET.fromstring(archivo.read('word/document.xml')).find('w:body', NS)
    if cuerpo is None:
        raise ValueError(f'DOCX sin cuerpo: {ruta.name}')
    bloques, tablas, parrafos = [], [], []
    seccion, numero_tabla = 'Cabecera', 0
    for posicion, nodo in enumerate(cuerpo, 1):
        if nodo.tag == '{%s}p' % NS['w']:
            texto = ''.join(t.text or '' for t in nodo.findall('.//w:t', NS)).strip()
            if not texto:
                continue
            parrafos.append(texto)
            if re.match(r'^\d+\.\s', texto):
                seccion = texto
            bloques.append(dict(texto=texto, seccion=seccion,
                                localizador=f'cuerpo/{posicion}/parrafo'))
        elif nodo.tag == '{%s}tbl' % NS['w']:
            numero_tabla += 1
            filas = [[_texto(c) for c in fila.findall('w:tc', NS)]
                     for fila in nodo.findall('w:tr', NS)]
            tablas.append(filas)
            for numero, fila in enumerate(filas, 1):
                bloques.append(dict(texto=' | '.join(fila), seccion=seccion,
                                    cabecera=' | '.join(filas[0]),
                                    localizador=f'cuerpo/{posicion}/tabla/{numero_tabla}/fila/{numero}'))
    campos = {fila[0]: fila[1] for tabla in tablas for fila in tabla
              if len(fila) == 2 and fila[0] in (
                  'Código', 'Versión', 'Fecha', 'Responsable', 'Elaboración', 'Aprobación',
                  'Aprobación institucional', 'Clasificación', 'Referencias', 'Referencias de trabajo')}
    codigo = campos.get('Código')
    if not codigo or not re.fullmatch(CODIGO, codigo) or not ruta.name.startswith(codigo + '_'):
        raise ValueError(f'Código documental ausente o incompatible: {ruta.name}')
    contenido = '\n'.join(b['texto'] for b in bloques)
    meta = dict(codigo_documental=codigo, titulo=parrafos[1] if len(parrafos) > 1 else codigo,
                version=campos.get('Versión'), fecha=campos.get('Fecha'),
                responsable=campos.get('Responsable', campos.get('Elaboración')),
                aprobacion=campos.get('Aprobación', campos.get('Aprobación institucional')),
                clasificacion=campos.get('Clasificación'),
                referencias_normativas_declaradas=campos.get('Referencias de trabajo', campos.get('Referencias')),
                validacion_normativa='pendiente de cotejo con fuente autorizada',
                simulado='SIMULAD' in contenido.upper() or 'DATOS FICTICIOS' in contenido.upper(),
                relaciones=sorted(set(re.findall(r'\b(?:PIMS-RIE-\d{2}[AB]?|TRA-\d{3}|ACT-\d{3}|RIE-\d{3}|ACC-\d{3}|A\.[123](?:\.\d+){1,2})\b', contenido))),
                sha256=hashlib.sha256(original).hexdigest())
    if codigo == 'PIMS-RIE-04':
        claves = ('codigo','nombre','aplicabilidad','justificacion','riesgos','estado','evidencia','acciones','observaciones','fuente')
        meta['controles_soa'] = [dict(zip(claves, fila)) for tabla in tablas
            if tabla and tabla[0][:3] == ['Control','Nombre resumido','Aplicabilidad']
            for fila in tabla[1:] if len(fila) == len(claves)]
    return dict(metadatos=meta, contenido=contenido, bloques=bloques, tablas=tablas)
