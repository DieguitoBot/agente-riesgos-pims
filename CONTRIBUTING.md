# Colaboración del equipo

Mantener el alcance de `Contexto.txt`: agente especializado de evaluación inicial
de riesgos, sin implementar las responsabilidades de otros agentes.

## Distribución propuesta en el contexto

| Integrante | Área | Archivos principales |
| --- | --- | --- |
| 1 | Identidad, instrucciones y contrato | `PROMPT_SKILL.md`, `prompts/` |
| 2 | Evaluación, validación y reporte | `skills/`, `llm/`, `config.py` |
| 3 | API e interfaz | `app.py`, `templates/`, `static/`, lanzadores |
| 4 | Conocimiento, casos y documentación | `knowledge/`, `tests/`, `docs/` |

Las rutas de código son relativas a `agente_riesgos_pims_v2/`. Esta tabla recoge
la división propuesta, no atribuye tareas ya aceptadas por personas concretas.
Coordinar cambios que atraviesen áreas, especialmente el contrato de respuesta
que comparten prompt, cliente, skill e interfaz.

## Flujo de cambios

1. Acordar una tarea y sus archivos antes de editar.
2. Crear una rama desde `main`: `git switch -c mejora/descripcion-corta`.
3. Mantener el cambio limitado a la tarea; añadir pruebas cuando corrija lógica.
4. Ejecutar las comprobaciones del README y describir sus resultados.
5. Subir la rama y abrir un pull request; otro integrante revisa antes de fusionar.

Describir en el pull request el problema, el cambio, los archivos afectados y la
validación. No añadir datos personales reales, entornos virtuales, credenciales ni
documentos cuya distribución no esté autorizada. Usar escenarios ficticios.

Los siguientes trabajos requieren acuerdo posterior del equipo/docente:
integración con Agente 8, orquestador, MCP, persistencia compartida y FAISS.
Proponer una medida no significa ejecutarla, auditarla ni certificar cumplimiento.
