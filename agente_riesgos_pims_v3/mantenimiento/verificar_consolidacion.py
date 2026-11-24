"""Auditoría posterior de solo lectura y comparación sobre resultados congelados.

No importa fuentes ni altera registros. Evidencias privadas en datos/consolidacion/.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import requests

from db.repositorio import conectar,inventario,leer_norma
from rag.recuperar_contexto import recuperar_contexto_rag
from skills.reporte import generar_reporte
BASE=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',default='http://127.0.0.1:8185');args=p.parse_args()
    salida=BASE/'datos/consolidacion';func=salida/'funcional'
    antes=json.loads((salida/'base_antes.json').read_text());documentos=inventario()
    with conectar() as con:
        con.execute('SET TRANSACTION READ ONLY')
        actuales={str(i):(h,r) for i,h,r in con.execute('SELECT id,md5(resultado::text),md5(reporte_base) FROM gestitel_experimental.evaluaciones').fetchall()}
        assert all(actuales[e['id']]==(e['resultado'],e['reporte']) for e in antes['evaluaciones'])
        grupos=con.execute('''SELECT d.categoria,count(DISTINCT d.id),count(f.id),count(f.embedding)
            FROM pims_riesgos.documentos d LEFT JOIN pims_riesgos.fragmentos f ON d.id=f.documento_id
            GROUP BY d.categoria ORDER BY d.categoria''').fetchall()
        archivos=con.execute('SELECT count(*) FROM pims_riesgos.versiones_documentales').fetchone()[0]
        duplicados=con.execute("SELECT sha256,array_agg(clave) FROM pims_riesgos.documentos GROUP BY sha256 HAVING count(*)>1").fetchall()
        originales=con.execute("SELECT count(*) FROM pims_riesgos.documentos WHERE sha256<>encode(sha256(original),'hex')").fetchone()[0]
    iso,huella_iso=leer_norma('iso');ley,huella_ley=leer_norma('ley')
    assert huella_iso==hashlib.sha256((BASE.parent/'ISO_IEC_27701_2025.md').read_bytes()).hexdigest()
    assert len([d for d in documentos if d['sha256']==huella_iso])==1 and originales==0
    sesion=requests.Session();sesion.trust_env=False
    def get(ruta):
        r=sesion.get(args.url+ruta,timeout=90);r.raise_for_status();return r
    spec=importlib.util.spec_from_file_location('reporte_anterior',BASE/'datos/consolidacion_antes/reporte_anterior.py')
    modulo=importlib.util.module_from_spec(spec);spec.loader.exec_module(modulo)
    resumen=dict(base='pims_riesgos_experimental',evaluaciones_previas=len(antes['evaluaciones']),historial_previo_intacto=True,
        documentos=len(documentos),categorias=[dict(categoria=c,documentos=n,fragmentos=f,vectores=v) for c,n,f,v in grupos],
        versiones_archivadas=archivos,originales_sha_validos=True,duplicados_heredados=[dict(sha256=h,claves=claves) for h,claves in duplicados],
        iso=dict(sha256=huella_iso,secciones=len(iso),guias_b=sum(c.startswith('B.') for c in iso),
                 rag=next(d for d in documentos if d['sha256']==huella_iso)['indexados']),casos=[],consultas=[])
    for n in range(1,6):
        actual=json.loads((func/f'caso_{n}.json').read_text());viejo=json.loads((BASE/f'datos/consolidacion_antes/caso_{n}.json').read_text())
        r=actual['respuesta'];anterior=viejo.get('respuesta',{})
        assert actual['http']==200 and r['evaluacion_id']==r['experimento_id']
        assert r['puntaje']==r['probabilidad']*r['impacto']
        controles=[]
        for ref in r['referencias_iso']:
            assert ' '.join(ref['cita_normativa'].split()) in ' '.join(iso[ref['guia']]['texto'].split())
            assert ref['sha256']==huella_iso
            assert ' '.join(ref['cita_normativa'].split()) in ' '.join(get(ref['fuente']).text.split())
            controles.append(dict(codigo=ref['codigo'],decision_soa=ref.get('decision_soa'),estado=ref.get('estado_implementacion')))
        for ref in r['referencias_ley']:
            assert ' '.join(ref['cita_normativa'].split()) in ' '.join(ley[ref['articulo']]['texto'].split())
        fuentes={f['id']:f for f in r['fuentes_rag']}
        for ref in r['referencias_rag']:
            assert ' '.join(ref['cita'].split()) in ' '.join(fuentes[ref['fuente_id']]['texto'].split())
        ruta='/api/experimento/evaluaciones/'+r['experimento_id']
        detalle=get(ruta).json();assert detalle['reporte_base']==r['reporte_texto']
        for formato in ('base','txt','csv','html'):
            texto=get(ruta+'/reporte?formato='+formato).text
            extension='html' if formato=='html' else 'txt'
            (func/f'caso_{n}_{formato}.{extension}').write_text(texto)
            if formato=='html':assert 'IMPLEMENTACIÓN ACADÉMICA SIMULADA' in texto
            if formato=='csv':assert 'Trazabilidad documental' in texto
        previo=modulo.generar_reporte(r);nuevo=generar_reporte(r)
        campos={'identificador':lambda t:r['evaluacion_id'] in t,
                'version_formato':lambda t:'PIMS-RIE-06 / 1.0' in t,
                'encabezado_academico':lambda t:'IMPLEMENTACIÓN ACADÉMICA SIMULADA' in t,
                'resumen_ejecutivo':lambda t:bool(re.search(r'(?mi)^1[.] Resumen ejecutivo',t)),
                'objetivo_alcance':lambda t:bool(re.search(r'(?mi)^2[.] Objetivo y alcance',t)),
                'conclusiones':lambda t:bool(re.search(r'(?mi)^9[.] Conclusiones',t))}
        metrica={k:dict(antes=fn(previo),despues=fn(nuevo)) for k,fn in campos.items()}
        (func/f'caso_{n}_estructura_actual.txt').write_text(nuevo)
        resumen['casos'].append(dict(caso=n,id=r['experimento_id'],entrada_identica=actual['entrada']==viejo.get('entrada'),
            puntaje_antes=anterior.get('puntaje'),puntaje_despues=r['puntaje'],nivel=r['nivel'],segundos_antes=viejo.get('segundos'),segundos_despues=actual['segundos'],
            referencias_iso_antes=len(anterior.get('referencias_iso',[])),referencias_iso_despues=len(r['referencias_iso']),
            referencias_ley=len(r['referencias_ley']),referencias_rag=len(r['referencias_rag']),
            categorias_citadas=dict(Counter('implementacion_pims' if f.get('codigo_documental') else f.get('categoria','desconocida') for f in r['referencias_rag'])),
            controles=controles,alertas_antes=len(anterior.get('alertas_contenido',[])),alertas_despues=len(r['alertas_contenido']),
            calculo_correcto=True,citas_literales_correctas=True,original_intacto=True,comparacion_formato_sobre_mismo_analisis=metrica))
    consultas=[('ISO 6.1.3 privacy risk treatment statement applicability','6.1.3'),('ISO Annex B B.3.9 access rights','B.3.9'),
        ('PIMS-RIE-01 metodología evaluación riesgos','PIMS-RIE-01'),('PIMS-RIE-02 matriz permisos RIE-001','PIMS-RIE-02'),
        ('PIMS-RIE-04 declaración aplicabilidad controles propuestos','PIMS-RIE-04'),('PIMS-RIE-03 plan tratamiento ACC-005','PIMS-RIE-03'),
        ('PIMS-RIE-05A inventario activos flujos','PIMS-RIE-05A'),('PIMS-RIE-05B registro tratamientos','PIMS-RIE-05B')]
    for consulta,objetivo in consultas:
        r=recuperar_contexto_rag(consulta)
        resumen['consultas'].append(dict(consulta=consulta,objetivo=objetivo,recuperado=any(f.get('seccion')==objetivo or f.get('codigo_documental')==objetivo for f in r['fragmentos']),
            fuentes=[dict(archivo=f['archivo'],seccion=f.get('seccion'),codigo=f.get('codigo_documental'),fragmento=f['fragmento'],categoria=f.get('categoria')) for f in r['fragmentos']]))
    (salida/'auditoria_final.json').write_text(json.dumps(resumen,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in resumen.items() if k not in ('casos','consultas')},ensure_ascii=False,indent=2))
    for caso in resumen['casos']:print('Caso',caso['caso'],'puntaje',caso['puntaje_despues'],'ISO',caso['referencias_iso_despues'],'mismo análisis/formato',caso['comparacion_formato_sobre_mismo_analisis'])
    for c in resumen['consultas']:print(c['objetivo'],'recuperado',c['recuperado'])

if __name__=='__main__':main()
