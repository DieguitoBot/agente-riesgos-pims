"""Validación REAL por HTTP/SQL/Ollama. Evidencias privadas en datos/validacion_pims.

Ejecutar con Flask iniciado: .venv/bin/python validar_pims.py
No inicializa bases ni modifica planes. Las evaluaciones válidas quedan en historial.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import shutil
import time

import requests

BASE = Path(__file__).resolve().parent
CASOS = [
    ('Acceso no autorizado a expedientes académicos',
     'Caso ficticio TRA-001 / ACT-001 / RIE-001: el sistema de matrícula permite acceso a expedientes académicos por permisos excesivos de cuentas de prueba. No consta revisión de permisos.', 3, 4),
    ('Exposición durante matrícula',
     'Caso ficticio TRA-001: una hoja de matrícula con nombres y correos de estudiantes de prueba está expuesta mediante un enlace público. Se requiere restringir la publicación.', 4, 4),
    ('Acceso a bienestar',
     'Caso ficticio TRA-002 / ACT-002 / RIE-002: cuentas de prueba sin autorización acceden a expedientes de bienestar con datos socioeconómicos y de salud ficticios por permisos excesivos.', 3, 5),
    ('Conservación excesiva',
     'Caso ficticio TRA-003 / ACT-003 / RIE-003: el historial de préstamos de estudiantes de prueba se conserva por tiempo indefinido, sin plazo ni eliminación definida.', 3, 3),
    ('Divulgación a terceros',
     'Caso ficticio TRA-001: se envía información académica de estudiantes de prueba a terceros por correo personal sin autorización y sin cifrado.', 4, 5),
]


def guardar(ruta, datos):
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8180')
    parser.add_argument('--repetir', action='store_true')
    parser.add_argument('--caso', type=int, choices=range(1, 6))
    parser.add_argument('--salida',type=Path,help='Directorio de evidencias dentro de datos/')
    args = parser.parse_args()
    from urllib.parse import urlsplit
    if urlsplit(args.url).hostname not in ('localhost', '127.0.0.1', '::1'):
        parser.error('Usa una instancia local de prueba.')
    salida = (args.salida or BASE / 'datos/validacion_pims').resolve()
    if not salida.is_relative_to((BASE/'datos').resolve()):
        parser.error('Las evidencias privadas deben permanecer dentro de datos/.')
    salida.mkdir(parents=True, exist_ok=True)
    sesion = requests.Session()
    sesion.trust_env = False
    def get(ruta):
        r = sesion.get(args.url + ruta, timeout=60)
        r.raise_for_status()
        return r

    entorno = dict(fecha=datetime.now(timezone.utc).isoformat(),
                   pagina=get('/').status_code, ollama=get('/api/status').json(),
                   documentos=get('/api/documentos').json(),
                   historial=get('/api/experimento/evaluaciones').status_code)
    entorno['http_adicional'] = {
        'javascript': get('/static/js/app.js').status_code,
        'javascript_planes': get('/static/js/experimento.js').status_code,
        'css': get('/static/css/style.css').status_code,
        'entrada_invalida': sesion.post(args.url+'/api/evaluar', json={}, timeout=30).status_code,
        'edicion_invalida': sesion.put(args.url+'/api/experimento/planes/0', json=[], timeout=30).status_code,
        'fuente_inexistente': sesion.get(args.url+'/api/fuente-rag/'+'0'*64+'/1', timeout=30).status_code,
    }
    entorno['cotejo_versiones_anteriores'] = []
    for anterior in sorted((BASE/'datos/validacion_pims_inicial').glob('caso_[1-5].json')):
        for ref in json.loads(anterior.read_text()).get('respuesta', {}).get('referencias_rag', []):
            if ref.get('fuente'):
                fuente = get(ref['fuente']).json()['fuente']
                entorno['cotejo_versiones_anteriores'].append(dict(
                    caso=anterior.stem, sha256=ref['sha256'],
                    cotejada=ref['cita'] in ' '.join(fuente['texto'].split())))
    guardar(salida / 'entorno.json', entorno)
    from db.repositorio import leer_fragmentos
    from rag.recuperar_contexto import recuperar_contexto_rag, seleccionar, ampliar_consulta
    fs = leer_fragmentos()
    consultas = {}
    for d in entorno['documentos']['documentos']:
        meta = d.get('metadatos', {})
        if not meta.get('codigo_documental'):
            continue
        q = meta['codigo_documental'] + ' ' + meta['titulo']
        r = recuperar_contexto_rag(q)
        consultas[meta['codigo_documental']] = dict(consulta=q, estado=r['estado'],
            recuperado=any(f.get('codigo_documental') == meta['codigo_documental'] for f in r['fragmentos']),
            fuentes=r['fragmentos'])
    guardar(salida / 'consultas_documentales.json', consultas)
    print('Documentos recuperables:', sum(r['recuperado'] for r in consultas.values()), '/', len(consultas), flush=True)

    # Comparación reproducible del buscador léxico con el lector y selector de HEAD.
    # No altera Git, datos ni configuración. No mide calidad generativa anterior.
    modulos = []
    for nombre in ('documentos', 'recuperar_contexto'):
        codigo = subprocess.check_output(['git', 'show', f'HEAD:agente_riesgos_pims_v3/rag/{nombre}.py'], cwd=BASE)
        archivo = salida / f'{nombre}_antes.py'
        archivo.write_bytes(codigo)
        spec = importlib.util.spec_from_file_location(f'{nombre}_antes', archivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        modulos.append(modulo)
    antes_fs = modulos[0].leer_documentos(BASE / 'knowledge/documentos')
    comparacion = []
    for titulo, descripcion, _, _ in CASOS:
        t = time.monotonic()
        antes = modulos[1].seleccionar(modulos[1].ampliar_consulta(descripcion), antes_fs, [], 12)
        antes_s = time.monotonic() - t
        t = time.monotonic()
        despues = seleccionar(ampliar_consulta(descripcion), fs, [], 12, incluir_metodologia=True)
        comparacion.append(dict(caso=titulo, antes_segundos=antes_s, despues_segundos=time.monotonic()-t,
            antes_archivos=[f['archivo'] for f in antes], despues_archivos=[f['archivo'] for f in despues],
            antes_pims=sum(f['archivo'].endswith('.docx') for f in antes),
            despues_pims=sum(bool(f.get('codigo_documental')) for f in despues)))
    guardar(salida / 'comparacion_lexica.json', comparacion)
    resultados = []
    for n, (titulo, descripcion, p, i) in enumerate(CASOS, 1):
        archivo = salida / f'caso_{n}.json'
        entrada = dict(descripcion=descripcion, probabilidad=p, impacto=i,
                       categorias=['Datos ficticios'], rol_privacidad='responsable', exigir_ia=True)
        if args.caso and args.caso != n:
            if archivo.exists():
                resultados.append(json.loads(archivo.read_text()))
            continue
        if archivo.exists() and not args.repetir:
            previo = json.loads(archivo.read_text())
            if previo.get('http') == 200 and previo.get('entrada') == entrada:
                resultados.append(previo)
                continue
        t = time.monotonic()
        print('Evaluación real', n, titulo, flush=True)
        if archivo.exists():
            archivo_previo = salida / ('previos_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'))
            archivo_previo.mkdir(exist_ok=True)
            shutil.copy2(archivo, archivo_previo / archivo.name)
        resultado = dict(caso=n, titulo=titulo, entrada=entrada)
        try:
            r = sesion.post(args.url + '/api/evaluar', json=entrada, timeout=1900)
            resultado.update(http=r.status_code, segundos=time.monotonic()-t, respuesta=r.json())
            guardar(archivo, resultado)  # Conservar la evaluación incluso si falla una comprobación posterior.
            datos = resultado['respuesta']
            if r.status_code == 200:
                resultado['calculo_correcto'] = datos['puntaje'] == p*i
                fuentes = {f['id']: f for f in datos['fuentes_rag']}
                resultado['citas_literales'] = all(' '.join(ref['cita'].split()) in
                    ' '.join(fuentes[ref['fuente_id']]['texto'].split()) for ref in datos['referencias_rag'])
                cotejos = []
                for ref in datos['referencias_rag']:
                    if ref.get('fuente'):
                        fuente = get(ref['fuente']).json()['fuente']
                        cotejos.append(ref['cita'] in ' '.join(fuente['texto'].split()))
                resultado['cotejos_sql'] = cotejos
                if datos.get('experimento_id'):
                    ruta = '/api/experimento/evaluaciones/' + datos['experimento_id']
                    detalle = get(ruta).json()
                    resultado['planes'] = detalle['planes']
                    resultado['exportaciones'] = {}
                    for formato in ('base', 'txt', 'csv','html'):
                        reporte = get(ruta + '/reporte?formato=' + formato).text
                        (salida / (f'caso_{n}_{formato}.'+('html' if formato=='html' else 'txt'))).write_text(reporte, encoding='utf-8')
                        resultado['exportaciones'][formato] = len(reporte)
                    resultado['original_intacto'] = get(ruta+'/reporte?formato=base').text == datos['reporte_texto']
            guardar(archivo, resultado)
            resultados.append(resultado)
            print('Caso', n, 'HTTP', r.status_code, 'segundos', round(resultado['segundos'], 2),
                  'citas', len(datos.get('referencias_rag', [])), flush=True)
        except requests.RequestException as exc:
            resultado.update(error=str(exc), segundos=time.monotonic()-t)
            guardar(archivo, resultado)
            resultados.append(resultado)
    guardar(salida / 'resultados.json', resultados)
    comprobaciones = []
    for resultado in resultados:
        if args.caso and resultado['caso'] != args.caso:
            continue
        datos = resultado.get('respuesta', {})
        refs = datos.get('referencias_rag', [])
        ok = (resultado.get('http') == 200 and not resultado.get('error')
              and datos.get('llm_disponible') is True
              and resultado.get('calculo_correcto') is True
              and resultado.get('citas_literales') is True and bool(refs)
              and any(ref.get('codigo_documental') for ref in refs)
              and bool(resultado.get('cotejos_sql')) and all(resultado['cotejos_sql'])
              and resultado.get('original_intacto') is True)
        comprobaciones.append(dict(caso=resultado['caso'], validacion_tecnica=bool(ok),
                                   estado_revision=datos.get('estado_revision')))
    correcto = (len(comprobaciones) == (1 if args.caso else 5)
                and all(c['validacion_tecnica'] for c in comprobaciones)
                and len(consultas) == 10 and all(c['recuperado'] for c in consultas.values()))
    guardar(salida / 'resumen_validacion.json', dict(correcto=correcto, casos=comprobaciones,
           limite='Validación técnica; no valida semántica, aprobación ni conformidad ISO.'))
    print('Evidencias en', salida, flush=True)
    if not correcto:
        raise SystemExit('Validación técnica incompleta; consulta las evidencias y errores registrados.')


if __name__ == '__main__':
    main()
