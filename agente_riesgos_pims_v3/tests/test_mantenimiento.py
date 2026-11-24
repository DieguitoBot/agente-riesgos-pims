"""Seguridad documental y regresiones del contrato público con fuentes sintéticas."""
from copy import deepcopy
from pathlib import Path
import os
from unittest import TestCase
from unittest.mock import patch
from uuid import UUID

from app import app
from db.repositorio import BaseNoDisponible
from mantenimiento.metricas import capturar, medir
from tests.test_ollama_client import ANALISIS


class TestSeguridadDocumental(TestCase):
    rutas = ('/api/documentos', '/api/fuente-rag/'+'a'*64+'/1', '/api/fuente-iso/A.3.9')

    def setUp(self):
        self.cliente = app.test_client()
        entorno = patch.dict(os.environ, {'PIMS_DOCUMENTOS_TOKEN': '', 'PIMS_DOCUMENTOS_LOCAL': '1'})
        entorno.start()
        self.addCleanup(entorno.stop)

    def test_remoto_rechazado_antes_de_consultar_fuentes(self):
        with patch('app.inventario') as inventario, \
             patch('db.repositorio.leer_fuente_rag') as rag, \
             patch('app.leer_secciones') as iso:
            for ruta in self.rutas:
                for cabeceras in ({}, {'X-Forwarded-For': '127.0.0.1'},
                                  {'Authorization': 'Bearer incorrecto'}):
                    r = self.cliente.get(ruta, headers=cabeceras,
                                         environ_overrides={'REMOTE_ADDR': '192.0.2.10'})
                    self.assertEqual(r.status_code, 401)
                    self.assertEqual(r.get_json(), {'error': 'Acceso documental no autorizado.'})
                    self.assertIn('no-store', r.headers['Cache-Control'])
            inventario.assert_not_called()
            rag.assert_not_called()
            iso.assert_not_called()

    def test_local_y_token_remoto_conservan_enlaces_y_contenido(self):
        fuente = dict(archivo='sintetico.md', pagina=None, linea=1, texto='Fuente sintética de prueba')
        with patch('app.inventario', return_value=[]), \
             patch('db.repositorio.leer_fuente_rag', return_value=fuente), \
             patch('app.leer_secciones', return_value=({'B.3.9': fuente}, 'a'*64)), \
             patch('db.repositorio.leer_seccion_iso', return_value=fuente):
            for host, remoto in (('localhost','127.0.0.1'), ('127.0.0.1','127.0.0.2'), ('[::1]','::1')):
                for ruta in self.rutas:
                    r = self.cliente.get(ruta, base_url='http://'+host,
                                         environ_overrides={'REMOTE_ADDR': remoto})
                    self.assertEqual(r.status_code, 200)
                    self.assertIn('no-store', r.headers['Cache-Control'])
            with patch.dict(os.environ, {'PIMS_DOCUMENTOS_TOKEN': 'token-sintetico-prueba'}):
                for ruta in (*self.rutas, '/api/fuente-iso/A.3.9?sha256='+'a'*64):
                    r = self.cliente.get(ruta, headers={'Authorization': 'Bearer token-sintetico-prueba'},
                                         environ_overrides={'REMOTE_ADDR': '192.0.2.10'})
                    self.assertEqual(r.status_code, 200)
                self.assertEqual(self.cliente.get('/api/documentos?token=token-sintetico-prueba',
                    environ_overrides={'REMOTE_ADDR': '192.0.2.10'}).status_code, 401)

    def test_host_origen_y_proxy_no_convierten_remoto_en_local(self):
        for cabeceras in ({'Host':'externo.example'}, {'Origin':'https://externo.example'},
                          {'Forwarded':'for=192.0.2.10'}, {'X-Forwarded-Host':'localhost'},
                          {'X-Forwarded-For':'192.0.2.10'}):
            self.assertEqual(self.cliente.get('/api/documentos', headers=cabeceras).status_code, 401)

    def test_proxy_puede_exigir_token_incluso_en_loopback(self):
        with patch.dict(os.environ, {'PIMS_DOCUMENTOS_LOCAL': '0',
                                    'PIMS_DOCUMENTOS_TOKEN': 'token-sintetico-prueba'}), \
             patch('app.inventario', return_value=[]):
            self.assertEqual(self.cliente.get('/api/documentos').status_code, 401)
            self.assertEqual(self.cliente.get('/api/documentos', headers={
                'Authorization': 'Bearer token-sintetico-prueba'}).status_code, 200)

    def test_errores_sql_no_exponen_detalles(self):
        with patch('app.inventario', side_effect=BaseNoDisponible('secreto-interno')), \
             patch('db.repositorio.leer_fuente_rag', side_effect=BaseNoDisponible('secreto-interno')), \
             patch('app.leer_secciones', side_effect=BaseNoDisponible('secreto-interno')), \
             patch('db.repositorio.leer_seccion_iso', side_effect=BaseNoDisponible('secreto-interno')):
            for ruta in (*self.rutas, '/api/fuente-iso/A.3.9?sha256='+'a'*64):
                r = self.cliente.get(ruta)
                self.assertEqual(r.status_code, 503)
                self.assertNotIn('secreto-interno', r.get_data(as_text=True))


class TestContratoMantenimiento(TestCase):
    def test_api_remota_conserva_entrada_salida_identidad_y_persistencia(self):
        entrada = dict(descripcion='Datos sin control de acceso', probabilidad=4, impacto=4,
                       categorias=['Salud'], rol_privacidad='responsable', exigir_ia=True)
        with patch('db.repositorio.conectar', side_effect=BaseNoDisponible('sin SQL real')), \
             patch('skills.evaluacion_riesgo.analizar_con_ollama', return_value=deepcopy(ANALISIS)), \
             patch('app.gestion.guardar_evaluacion', side_effect=lambda r, d: r['evaluacion_id']) as guardar:
            r = app.test_client().post('/api/evaluar', json=entrada,
                                     environ_overrides={'REMOTE_ADDR': '192.0.2.10'})
        self.assertEqual(r.status_code, 200)
        resultado = r.get_json()
        for campo, valor in entrada.items():
            if campo != 'exigir_ia':
                self.assertEqual(resultado[campo], valor)
        self.assertEqual((resultado['puntaje'],resultado['nivel']), (16,'Alto'))
        self.assertTrue(resultado['llm_disponible'])
        self.assertEqual(resultado['evaluacion_id'], resultado['experimento_id'])
        UUID(resultado['evaluacion_id'])
        self.assertTrue({'agente','skill','analisis_ia','modo','modelo','mensaje','reporte_texto',
                         'documentacion_iso','referencias_iso','referencias_rag','documentacion_soa',
                         'fecha_evaluacion','version_reporte'} <= resultado.keys())
        guardar.assert_called_once()
        self.assertNotIn('etapas', resultado)
        with patch('app.consultar_estado', return_value=dict(ollama=True, skill='evaluar_riesgo')):
            estado = app.test_client().get('/api/status', environ_overrides={'REMOTE_ADDR':'192.0.2.10'})
        self.assertEqual(estado.status_code, 200)
        self.assertEqual(estado.get_json()['skill'], 'evaluar_riesgo')

    def test_expediente_solo_contiene_diez_docx(self):
        carpeta = Path(__file__).resolve().parents[1]/'knowledge/documentos/pims_unsa'
        archivos = list(carpeta.iterdir())
        self.assertEqual(len(archivos), 10)
        self.assertTrue(all(p.suffix == '.docx' for p in archivos))

    def test_medicion_optativa_anidada_y_excepciones(self):
        @medir('prueba')
        def ejecutar(fallar=False):
            if fallar:
                raise ValueError('previsto')
            return 42
        self.assertEqual(ejecutar(),42)
        with capturar() as exterior:
            ejecutar()
            with capturar() as interior:
                with self.assertRaises(ValueError):
                    ejecutar(True)
            ejecutar()
        self.assertEqual(exterior['prueba']['llamadas'],2)
        self.assertEqual(interior['prueba']['llamadas'],1)
        self.assertGreaterEqual(exterior['prueba']['segundos'],0)
