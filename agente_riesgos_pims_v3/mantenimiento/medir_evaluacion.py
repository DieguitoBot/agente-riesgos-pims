"""Perfil local real, sin migraciones. Guarda UNA evaluación en el historial.

Desde V3: python -m mantenimiento.medir_evaluacion
Emite solo tiempos y comprobaciones; nunca imprime normativa ni credenciales.
Requiere la configuración habitual de la aplicación en el entorno o .env.
"""
import json
from time import perf_counter

from app import app
from mantenimiento.metricas import capturar


def main():
    cliente = app.test_client()
    entrada = dict(
        descripcion=('Caso ficticio TRA-001 / ACT-001 / RIE-001: el sistema de matrícula '
                     'permite acceso a expedientes académicos por permisos excesivos de '
                     'cuentas de prueba. No consta revisión de permisos.'),
        probabilidad=3, impacto=4, categorias=['Identificación'],
        rol_privacidad='responsable', exigir_ia=True)
    inicio = perf_counter()
    with capturar() as etapas:
        respuesta = cliente.post('/api/evaluar', json=entrada)
    resultado = respuesta.get_json()
    resumen = dict(http=respuesta.status_code, segundos=perf_counter()-inicio,
                   etapas=etapas, evaluacion_id=resultado.get('experimento_id'),
                   ia=resultado.get('reporte_ia_generado', False),
                   puntaje=resultado.get('puntaje'), nivel=resultado.get('nivel'))
    if respuesta.status_code == 200:
        resumen['fuentes_recuperadas'] = len(resultado.get('fuentes_rag', []))
        resumen['referencias_verificadas'] = {
            tipo: len(resultado.get('referencias_'+tipo, [])) for tipo in ('iso', 'ley', 'rag')}
        identificador = resultado.get('experimento_id')
        if identificador:
            resumen['exportaciones'] = {}
            for formato in ('txt', 'base', 'csv', 'html'):
                r = cliente.get(f'/api/experimento/evaluaciones/{identificador}/reporte?formato={formato}')
                resumen['exportaciones'][formato] = dict(http=r.status_code, bytes=len(r.data))
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0 if respuesta.status_code == 200 and resumen['ia'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
