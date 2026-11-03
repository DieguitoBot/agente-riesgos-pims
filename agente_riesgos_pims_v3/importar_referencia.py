"""Copia un resultado aprobado al laboratorio sin escribir en la versión aprobada."""
import json
from pathlib import Path
from experimento import guardar_evaluacion, listar_evaluaciones

BASE=Path(__file__).resolve().parent
RUTA=BASE.parent/'.datos/prueba_api_funcional.json'

if __name__=='__main__':
    if any(e['procedencia']=='referencia_aprobada' for e in listar_evaluaciones()):
        print('La referencia aprobada ya está en el historial; no se duplica.')
    elif not RUTA.is_file():
        raise SystemExit('No está disponible el JSON del ensayo aprobado. Genera una evaluación desde el laboratorio.')
    else:
        resultado=json.loads(RUTA.read_text())
        identificador=guardar_evaluacion(resultado,procedencia='referencia_aprobada')
        print('Referencia copiada al laboratorio:',identificador)
