"""Navegador real: reproduce respuesta Ollama guardada; usa historial/planes/HTML reales.

POST /api/evaluar se reproduce para no duplicar IA. Se restaura el plan nuevo editado.
Evidencias privadas en datos/consolidacion/visual; requiere playwright y Chromium.
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',default='http://127.0.0.1:8185');args=p.parse_args()
    caso=json.loads((BASE/'datos/consolidacion/funcional/caso_1.json').read_text())
    assert caso['http']==200 and caso['respuesta']['llm_disponible']
    r=caso['respuesta'];entrada=caso['entrada'];ident=r['experimento_id']
    salida=BASE/'datos/consolidacion/visual';salida.mkdir(parents=True,exist_ok=True)
    ev=dict(errores_js=[],formulario_reproduce_respuesta_real=True,nuevo_llm_en_navegador=False,anchos=[])
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        page=browser.new_page(viewport=dict(width=1440,height=1000),locale='es-PE')
        page.on('pageerror',lambda e:ev['errores_js'].append(str(e)))
        def responder(route):
            enviado=route.request.post_data_json
            assert enviado['descripcion']==entrada['descripcion']
            assert enviado['probabilidad']==entrada['probabilidad'] and enviado['impacto']==entrada['impacto']
            ev['entrada_formulario']=enviado;route.fulfill(status=200,json=r)
        page.route('**/api/evaluar',responder)
        page.goto(args.url,wait_until='networkidle')
        page.locator('#descripcion').fill(entrada['descripcion'])
        page.locator('#probabilidad').select_option(str(entrada['probabilidad']))
        page.locator('#impacto').select_option(str(entrada['impacto']))
        page.locator('#rol_privacidad').select_option('responsable')
        page.locator('#formRiesgo button[type=submit]').click()
        page.locator('#resultado').wait_for(state='visible')
        assert ident in page.locator('#ficha-reporte').inner_text()
        assert '12/25' in page.locator('#puntaje').inner_text()
        page.screenshot(path=str(salida/'resultados_1440.png'))
        page.locator('#referencias-iso').scroll_into_view_if_needed();page.screenshot(path=str(salida/'referencias_iso_1440.png'))
        page.locator('#tab-historial').click()
        page.locator(f'button[data-evaluacion-id="{ident}"]').click()
        page.get_by_role('button',name='Editar plan R-01',exact=True).wait_for()
        detalle=page.request.get(args.url+'/api/experimento/evaluaciones/'+ident).json();original=detalle['planes'][0]
        try:
            page.get_by_role('button',name='Editar plan R-01',exact=True).click()
            page.locator('#plan-responsable').fill('Equipo ficticio de validación visual');page.locator('#plan-estado').select_option('en_revision')
            with page.expect_response(lambda res:res.request.method=='PUT' and res.url.endswith('/planes/'+str(original['id']))) as guardar:
                page.locator('#guardar-plan').click()
            assert guardar.value.status==200;page.locator('#dialogo-plan').wait_for(state='hidden')
            actual=page.request.get(args.url+'/api/experimento/evaluaciones/'+ident).json()
            assert next(p for p in actual['planes'] if p['id']==original['id'])['responsable']=='Equipo ficticio de validación visual'
            assert actual['reporte_base']==detalle['reporte_base'];ev['edicion_sql']=True
        finally:
            actual=page.request.get(args.url+'/api/experimento/evaluaciones/'+ident).json();vigente=next(p for p in actual['planes'] if p['id']==original['id'])
            if vigente['version']!=original['version']:
                restaurar=page.request.put(args.url+'/api/experimento/planes/'+str(original['id']),data=dict(original,version=vigente['version']))
                assert restaurar.status==200;ev['plan_restaurado']=True
        for ancho in (900,390):
            page.set_viewport_size(dict(width=ancho,height=950));page.locator('#tab-resultados').click();page.locator('#resultado').scroll_into_view_if_needed()
            dim=page.evaluate('({ventana:innerWidth,contenido:document.documentElement.scrollWidth})')
            assert dim['contenido']<=dim['ventana'],dim;ev['anchos'].append(dim)
            page.screenshot(path=str(salida/f'resultados_{ancho}.png'))
        reporte=browser.new_page(viewport=dict(width=1200,height=1000))
        reporte.goto(args.url+'/api/experimento/evaluaciones/'+ident+'/reporte?formato=html',wait_until='networkidle')
        assert reporte.locator('h1').inner_text().startswith('Informe de evaluación')
        assert reporte.locator('article').inner_text().count('6. Controles y aplicabilidad')==1
        reporte.screenshot(path=str(salida/'reporte_html.png'));reporte.pdf(path=str(salida/'reporte_impreso.pdf'),format='A4',print_background=True)
        reporte.set_viewport_size(dict(width=390,height=950));dim=reporte.evaluate('({ventana:innerWidth,contenido:document.documentElement.scrollWidth})')
        assert dim['contenido']<=dim['ventana'],dim;ev['html_movil']=dim
        assert not ev['errores_js'],ev['errores_js'];ev.update(correcto=True,eval_id=ident,reporte_base_intacto=True,impresion_pdf=True)
        browser.close()
    (salida/'resultado.json').write_text(json.dumps(ev,ensure_ascii=False,indent=2));print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
