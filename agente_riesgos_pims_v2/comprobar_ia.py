"""Prueba real desde tu terminal: genera un reporte solo si Ollama responde válidamente."""
import argparse
import json
import sys
import time
from pathlib import Path
from skills.evaluacion_riesgo import evaluar_riesgo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo', help='Modelo local instalado; por defecto OLLAMA_MODEL.')
    parser.add_argument('--entrada', type=Path, default=Path(__file__).with_name('ejemplo_solicitud.json'))
    parser.add_argument('--salida', type=Path, default=Path('reporte_ia.txt'))
    args = parser.parse_args()
    try:
        datos = json.loads(args.entrada.read_text(encoding='utf-8'))
        inicio = time.monotonic()
        resultado = evaluar_riesgo(datos['descripcion'], datos['probabilidad'], datos['impacto'],
                                  datos.get('categorias'), datos.get('rol_privacidad', 'no_definido'), args.modelo)
        print(f"Tiempo total: {time.monotonic() - inicio:.1f} segundos")
        if not resultado['reporte_ia_generado']:
            print('No se generó reporte de IA: ' + resultado['mensaje'], file=sys.stderr)
            return 1
        args.salida.write_text(resultado['reporte_texto'], encoding='utf-8')
        print('Reporte de IA guardado en ' + str(args.salida.resolve()))
        print(f"Referencias verificadas: ISO {len(resultado['referencias_iso'])}; "
              f"ley {len(resultado['referencias_ley'])}; RAG {len(resultado['referencias_rag'])}")
        print('RAG: ' + resultado['estado_rag'])
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
