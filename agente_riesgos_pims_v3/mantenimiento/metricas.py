"""Medición optativa por contexto; nunca registra fuentes, prompts ni credenciales.

Las etapas anidadas se solapan: no sumar padres e hijos. Sin capturar() no se
cronometra ni se modifica la respuesta API o el resultado persistido.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from time import perf_counter

_actual = ContextVar('metricas_pims', default=None)


@contextmanager
def capturar():
    datos = {}
    token = _actual.set(datos)
    try:
        yield datos
    finally:
        _actual.reset(token)


def medir(etapa):
    def decorar(funcion):
        @wraps(funcion)
        def medida(*args, **kwargs):
            datos = _actual.get()
            if datos is None:
                return funcion(*args, **kwargs)
            inicio = perf_counter()
            try:
                return funcion(*args, **kwargs)
            finally:
                registro = datos.setdefault(etapa, {'segundos': 0.0, 'llamadas': 0})
                registro['segundos'] += perf_counter() - inicio
                registro['llamadas'] += 1
        return medida
    return decorar
