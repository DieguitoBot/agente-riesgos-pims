"""
Módulo preparado para una integración posterior con un modelo local de embeddings.

En este primer avance no se fuerza una dependencia concreta porque el modelo
local todavía debe definirse con el equipo/docente.

La función mantiene una interfaz simple para que después se pueda implementar
con sentence-transformers u otra alternativa local.
"""

def generar_embedding(texto):
    raise NotImplementedError(
        "El modelo local de embeddings todavía no ha sido configurado."
    )
