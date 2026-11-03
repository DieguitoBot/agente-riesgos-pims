"""Pruebas del laboratorio; las pruebas SQL revierten todos sus cambios."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from app import app
import experimento as lab
from db.repositorio import conectar, BaseNoDisponible


def resultado_demo():
    return {'descripcion': 'Caso sintético: acceso público a un archivo de prueba.',
            'reporte_ia_generado': True, 'llm_disponible': True, 'puntaje': 16,
            'reporte_texto': 'REPORTE ORIGINAL DE PRUEBA\n',
            'analisis_ia': {'riesgos_identificados': [dict(riesgo='Acceso público', evidencia='acceso público',
                amenaza='Consulta por terceros', vulnerabilidad='Permisos abiertos', dano_personas='Exposición',
                medida_concreta='Restringir permisos', verificacion='Probar acceso sin autorización', prioridad='alta')]},
            'referencias_iso': [{'riesgo':'Acceso público','codigo':'A.3.9','archivo':'iso.md','cita_normativa':'Cita sintética para pruebas'}],
            'referencias_ley': [], 'referencias_rag': [], 'alertas_contenido': ['Aviso de prueba']}


def plan_valido(**cambios):
    datos=dict(version=1, estado='propuesto', responsable='', area='', medida='Restringir permisos',
               verificacion='Comprobar acceso', fecha_inicio=None, fecha_fin=None,
               evidencia_verificacion='', verificado_por='', fecha_verificacion=None,
               probabilidad_residual=None, impacto_residual=None,
               actividades=[dict(descripcion='Revisar permisos',responsable='',fecha_fin=None,completada=False)])
    datos.update(cambios)
    return datos


class TestValidacion(unittest.TestCase):
    def test_propuesta_sin_asignaciones_inventadas(self):
        p=lab.validar_plan(plan_valido())
        self.assertEqual(p['responsable'],'')
        self.assertIsNone(p['probabilidad_residual'])

    def test_verificado_exige_evidencia_verificador_y_fecha(self):
        with self.assertRaises(ValueError):
            lab.validar_plan(plan_valido(estado='verificado',responsable='Equipo de prueba'))

    def test_aprobar_exige_responsable(self):
        with self.assertRaises(ValueError): lab.validar_plan(plan_valido(estado='aprobado'))

    def test_fecha_final_antes_del_inicio(self):
        with self.assertRaises(ValueError):
            lab.validar_plan(plan_valido(fecha_inicio='2026-11-10',fecha_fin='2026-11-01'))

    def test_residual_debe_estar_completo_y_verificado(self):
        for valores in [dict(probabilidad_residual=2),dict(probabilidad_residual=2,impacto_residual=3),
                        dict(probabilidad_residual=True,impacto_residual=3)]:
            with self.subTest(valores=valores),self.assertRaises(ValueError): lab.validar_plan(plan_valido(**valores))

    def test_verificacion_con_actividades_pendientes_se_rechaza(self):
        with self.assertRaises(ValueError):
            lab.validar_plan(plan_valido(estado='verificado',responsable='Equipo',
                evidencia_verificacion='Ensayo documentado',verificado_por='Revisor',fecha_verificacion=date.today().isoformat()))

    def test_verificacion_completa_admite_reevaluacion(self):
        p=lab.validar_plan(plan_valido(estado='verificado',responsable='Equipo',
            evidencia_verificacion='Registro de prueba',verificado_por='Revisor',fecha_verificacion=date.today().isoformat(),
            actividades=[dict(descripcion='Ensayo',responsable='Equipo',completada=True)],
            probabilidad_residual=2,impacto_residual=3))
        self.assertEqual(lab.residual(p),'2 × 3 = 6/25')

    def test_entradas_no_validas(self):
        for datos in (None,[],{},plan_valido(version=True),plan_valido(estado='inventado'),
                      plan_valido(actividades=[{}]),plan_valido(fecha_fin='no-fecha')):
            with self.subTest(datos=datos),self.assertRaises(ValueError): lab.validar_plan(datos)

    def test_conexion_administrativa_no_disponible_en_la_app(self):
        with self.assertRaises(BaseNoDisponible):
            with conectar(admin=True): pass

    def test_conexion_a_base_aprobada_se_rechaza_antes_de_consultar(self):
        con=MagicMock();con.info.dbname='pims_riesgos'
        with patch('psycopg.connect') as abrir,patch.dict(os.environ,{'PIMS_DATABASE_URL':'dbname=pims_riesgos'}):
            abrir.return_value.__enter__.return_value=con
            with self.assertRaises(BaseNoDisponible):
                with conectar(): pass
        con.execute.assert_not_called()

    def test_demo_es_ficticia_y_no_se_atribuye_a_ia(self):
        from demo import crear_resultado_demo
        r=crear_resultado_demo()
        self.assertFalse(r['reporte_ia_generado'])
        self.assertFalse(r['llm_disponible'])
        self.assertEqual(r['modo'],'demostracion')
        self.assertFalse(r['referencias_iso'] or r['referencias_ley'] or r['referencias_rag'])
        self.assertEqual(len(r['analisis_ia']['riesgos_identificados']),2)

    def test_guardar_reglas_locales_no_crea_evaluacion(self):
        r=resultado_demo();r['reporte_ia_generado']=False
        with patch('experimento.conectar') as abrir,self.assertRaises(ValueError): lab.guardar_evaluacion(r)
        abrir.assert_not_called()


class TestAPIExperimental(unittest.TestCase):
    def setUp(self): self.cliente=app.test_client()

    def test_evaluacion_valida_devuelve_id_guardado(self):
        with patch('app.evaluar_riesgo',return_value=resultado_demo()),patch('experimento.guardar_evaluacion',return_value='id-prueba'):
            r=self.cliente.post('/api/evaluar',json={'descripcion':'caso'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['experimento_id'],'id-prueba')

    def test_fallo_de_persistencia_no_finge_guardado(self):
        with patch('app.evaluar_riesgo',return_value=resultado_demo()),patch('experimento.guardar_evaluacion',side_effect=BaseNoDisponible('prueba')):
            r=self.cliente.post('/api/evaluar',json={'descripcion':'caso'})
        self.assertEqual(r.status_code,503)

    def test_conflicto_de_edicion_devuelve_409(self):
        with patch('experimento.actualizar_plan',side_effect=lab.Conflicto('versión antigua')):
            r=self.cliente.put('/api/experimento/planes/1',json=plan_valido())
        self.assertEqual(r.status_code,409)

    def test_id_invalido_y_formato_no_permitido(self):
        self.assertEqual(self.cliente.get('/api/experimento/evaluaciones/no-es-uuid').status_code,404)
        self.assertEqual(self.cliente.get('/api/experimento/evaluaciones/no-es-uuid/reporte?formato=html').status_code,400)

    def test_scripts_y_elementos_estan_sincronizados(self):
        import re
        html=self.cliente.get('/').get_data(as_text=True)
        ids=re.findall(r'id="([^"]+)"',html)
        self.assertEqual(len(ids),len(set(ids)))
        for archivo in ('app.js','experimento.js'):
            js=(Path(app.static_folder)/'js'/archivo).read_text()
            requeridos=set(re.findall(r'getElementById\("([^"]+)"\)',js))
            self.assertFalse(requeridos-set(ids),requeridos-set(ids))
        self.assertIn('Versión experimental',html)


@unittest.skipUnless(os.getenv('PIMS_TEST_EXPERIMENTO')=='1','Requiere la base experimental local')
class TestPersistenciaReal(unittest.TestCase):
    def setUp(self):
        self.contexto=conectar();self.con=self.contexto.__enter__()
        self.con.execute('SELECT 1')
        @contextmanager
        def transaccion():
            with self.con.transaction(): yield self.con
        self.parche=patch('experimento.conectar',transaccion);self.parche.start()
        self.r=resultado_demo();self.id=lab.guardar_evaluacion(self.r,1.2,'prueba_rollback')

    def tearDown(self):
        self.parche.stop();self.con.rollback();self.contexto.__exit__(None,None,None)

    def test_guardado_separa_original_plan_y_actividades(self):
        e=lab.obtener_evaluacion(self.id)
        self.assertEqual(e['reporte_base'],self.r['reporte_texto'])
        self.assertEqual(len(e['planes']),1)
        p=e['planes'][0]
        self.assertEqual(p['estado'],'propuesto');self.assertEqual(p['responsable'],'')
        self.assertEqual(len(p['referencias']),1);self.assertEqual(len(p['actividades']),1)
        self.assertIn(self.id,[r['id'] for r in lab.listar_evaluaciones()])

    def test_edicion_persiste_y_original_permanece_identico(self):
        e=lab.obtener_evaluacion(self.id);p=e['planes'][0]
        nuevo=lab.actualizar_plan(p['id'],plan_valido(responsable='Equipo de ensayo',estado='aprobado',fecha_fin='2026-12-01'))
        self.assertEqual(nuevo['version'],2)
        self.assertEqual(lab.obtener_evaluacion(self.id)['resultado'],self.r)
        self.assertEqual(self.con.execute('SELECT count(*) FROM gestitel_experimental.cambios WHERE tratamiento_id=%s',(p['id'],)).fetchone()[0],1)
        self.assertIn('Equipo de ensayo',lab.reporte_experimental(lab.obtener_evaluacion(self.id)))

    def test_edicion_con_version_antigua_no_sobrescribe(self):
        p=lab.obtener_evaluacion(self.id)['planes'][0]
        lab.actualizar_plan(p['id'],plan_valido(responsable='Primera edición'))
        with self.assertRaises(lab.Conflicto): lab.actualizar_plan(p['id'],plan_valido(responsable='Edición obsoleta'))
        self.assertEqual(lab.obtener_evaluacion(self.id)['planes'][0]['responsable'],'Primera edición')

    def test_csv_conserva_campos_y_neutraliza_formulas(self):
        e=lab.obtener_evaluacion(self.id);e['planes'][0]['responsable']='=PRUEBA()'
        csv=lab.exportar_csv(e)
        self.assertIn("'=PRUEBA()",csv);self.assertIn('A.3.9',csv)
        self.assertTrue(csv.startswith('\ufeff'))

    def test_permisos_no_modifican_corpus_ni_base_aprobada(self):
        existe_base_aprobada = self.con.execute("SELECT 1 FROM pg_database WHERE datname='pims_riesgos'").fetchone()
        if existe_base_aprobada:
            self.assertFalse(self.con.execute("SELECT has_database_privilege(current_user,'pims_riesgos','CONNECT')").fetchone()[0])
        self.assertFalse(self.con.execute("SELECT has_table_privilege(current_user,'pims_riesgos.documentos','UPDATE')").fetchone()[0])
        self.assertFalse(self.con.execute("SELECT has_table_privilege(current_user,'gestitel_experimental.evaluaciones','UPDATE')").fetchone()[0])
        self.assertTrue(self.con.execute("SELECT has_table_privilege(current_user,'gestitel_experimental.tratamientos','UPDATE')").fetchone()[0])

    def test_api_descarga_original_y_tabla(self):
        c=app.test_client()
        for formato in ('base','txt','csv'):
            r=c.get(f'/api/experimento/evaluaciones/{self.id}/reporte?formato={formato}')
            self.assertEqual(r.status_code,200)
            self.assertIn('attachment',r.headers['Content-Disposition'])
        self.assertEqual(c.get(f'/api/experimento/evaluaciones/{self.id}/reporte?formato=base').get_data(as_text=True),self.r['reporte_texto'])


if __name__=='__main__': unittest.main()
