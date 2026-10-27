# Revisión del proyecto — 19 de octubre de 2026

Nota posterior: los puntos C.1, C.4 (ISO) y C.5 se abordan en la entrega
[Calidad de reportes RAG](CALIDAD_REPORTES_RAG.md). Este documento conserva
el diagnóstico histórico; las mejoras opcionales no forman parte de esa entrega.

## A. Estado general

La v2 es una skill funcional especializada con interfaz Flask y Ollama local.
Supera el mínimo del primer avance. No necesita más arquitectura para cumplirlo.
Se respetó la indicación de diagnosticar antes de modificar la lógica de negocio.

## B. Qué está correctamente implementado

- `evaluar_riesgo()` es reutilizable y no depende de Flask.
- Python valida probabilidad e impacto, calcula la matriz y conserva la valoración
  del usuario separada de la propuesta del modelo.
- Prompt, esquema JSON, cliente HTTP, conocimiento, skill y presentación están separados.
- La API diferencia errores de entrada, respuesta IA y respaldo por reglas.
- La interfaz exige IA válida y permite elegir modelo y descargar el reporte.
- Las referencias normativas se cotejan con fragmentos recuperados y se filtran
  por rol, evidencia y riesgo. Se conserva trazabilidad documental.
- FAISS y embeddings están aislados y no bloquean el funcionamiento.

## C. Errores y limitaciones encontrados

1. **Evidencia inventada en el análisis detallado.**
   `llm/ollama_client.py`, `validar_analisis()` y retorno de
   `recuperar_analisis()` dentro de `analizar_con_ollama()` (aprox. líneas 85–134):
   validan estructura, pero no cotejan la evidencia de cada riesgo con el escenario.
   Una respuesta de prueba con «Se filtraron diez millones de registros, hecho
   inventado.» se acepta. El formato breve sí realiza ese cotejo. El filtro de
   referencias no subsana el riesgo narrativo aceptado.
   Solución: validar también las evidencias del formato detallado contra el
   contexto antes de publicarlo; activar el reintento controlado ante discrepancia.
   Añadir prueba de regresión a través de la API. Esto verifica procedencia literal,
   pero no garantiza por sí solo la veracidad de toda la interpretación.

2. **Negaciones ignoradas en el respaldo.**
   `skills/evaluacion_riesgo.py`, `_detectar_riesgos()` (aprox. líneas 81–92):
   «Los datos no están publicados en internet y no se usan dispositivos USB.»
   produce exposición y transferencia insegura al forzar indisponibilidad de IA.
   Solución: agregar casos negativos y limitar reglas a indicios explícitos,
   manteniendo abstención ante ambigüedad. Afecta al respaldo de la API, no a un
   reporte de IA válido de la interfaz.

3. **Instalación no reproducible para compañeros.**
   El README de la v2 utilizaba rutas de Diego y un entorno de la v1 que no está
   en este workspace. Se corrigieron los comandos y se añadió una guía raíz.

4. **Tests acoplados a documentos locales.**
   `tests/test_documento_iso.py`, `test_complementos.py` y `test_reporte_ley.py`
   dependen directa o indirectamente del OCR original. El clon sin esa copia no
   reproduce los 50 éxitos. Separar pruebas con pequeños documentos sintéticos
   de las pruebas de integración con fuentes autorizadas antes de configurar CI.

5. **Límite de indicadores contradictorio.**
   `prompts/riesgo_prompt.py`: la identidad pide hasta 5 indicadores y al final
   fija 2, mientras que el esquema admite 3. Unificar el límite en las instrucciones,
   el esquema y la documentación para evitar rechazos o resultados inconsistentes.

## D. Correcciones prioritarias

Antes de afirmar que el agente descarta hechos inventados en todos sus formatos,
corregir el punto C.1. Antes de presentar el respaldo como capaz de interpretar
negaciones, corregir C.2. Antes de una demostración, ejecutar la prueba con Ollama
real y registrar modelo, duración y resultado. La instalación ya está documentada;
queda probarla en el equipo de otro integrante.

## E. Mejoras opcionales dentro del alcance

| Prioridad | Complemento | Criterio de aceptación |
| --- | --- | --- |
| Alta | Rúbrica de probabilidad e impacto 1–5 | Cada nivel tiene criterio y ejemplo; dos integrantes justifican un caso con la misma guía |
| Alta | Casos positivos, negativos y ambiguos | Incluir controles existentes, negaciones, falta de información e instrucciones dentro del escenario |
| Media | Límite de descripción y categorías | API e interfaz rechazan excesos antes de invocar el modelo; probar los límites |
| Media | Exportación JSON con versión del contrato | Conserva la evaluación descargada y permite reutilización futura sin conectar otros agentes |
| Media | Guion de exposición | Muestra prompt, llamada directa a skill, web, reporte y error controlado |
| Posterior | CI reproducible | Tests sintéticos sin Ollama ni documento ISO completo; integración documental por separado |

No se recomienda añadir historial con base de datos ni más pantallas antes de
resolver la validación y acordar la rúbrica. Los criterios numéricos deben ser
convenciones explícitas del equipo, no atribuirse a ISO.

## F. Qué no necesitamos todavía

Orquestador, conexión con Agente 8, MCP, PostgreSQL, FAISS obligatorio, frameworks
multiagente, Docker, microservicios ni autenticación empresarial. Tampoco ejecutar
controles, emitir dictámenes legales o implementar auditorías de otros agentes.

## G. Cumplimiento académico

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| De Prompt a Skill | Cumple | `prompts/riesgo_prompt.py` y `skills/evaluacion_riesgo.py` |
| Creación de Skill | Cumple | Activación, entradas, pasos y salidas en `PROMPT_SKILL.md` |
| Construcción de asistente | Cumple | Identidad, instrucciones, conocimiento y cliente local |
| Skill funcional especializada | Cumple con limitaciones | API y 50 pruebas; inferencia real pendiente de verificar aquí |

## H. Archivos recomendados para siguientes cambios

- `agente_riesgos_pims_v2/llm/ollama_client.py`: evidencia del formato detallado.
- `agente_riesgos_pims_v2/prompts/riesgo_prompt.py`: límite único de indicadores.
- `agente_riesgos_pims_v2/skills/evaluacion_riesgo.py`: reglas y límites de entradas.
- `agente_riesgos_pims_v2/tests/test_ollama_client.py`, `tests/test_skill.py` y
  `tests/test_api.py`: regresiones de esas correcciones.
- `agente_riesgos_pims_v2/tests/test_documento_iso.py`, `tests/test_complementos.py`
  y `tests/test_reporte_ley.py`: separar fixtures sintéticos e integración documental.
- `agente_riesgos_pims_v2/templates/index.html`: ayuda de rúbrica y límites,
  coordinada con la validación del servidor.
- `docs/RUBRICA.md` y `docs/CASOS_DEMO.md`: documentos propuestos, aún no creados.

## I. Verificación realizada

En el entorno `.venv` de la v2, `python -m unittest discover -s tests -v`:
**50 pruebas aprobadas**. `node --check static/js/app.js`: aprobado.
Se reprodujeron C.1 y C.2 con respuestas simuladas. La consulta local de estado
no pudo conectar con Ollama; no se verificó generación real ni latencia del modelo.
No se realizó una prueba visual interactiva en navegador ni una auditoría normativa.

## J. Conclusión

Es una base apta para el primer avance académico si se explican las limitaciones.
Para una demostración estable conviene resolver la evidencia del formato detallado
y probar Ollama en el equipo de exposición. El mejor complemento inmediato es
mejorar fiabilidad, criterios y colaboración, manteniendo el alcance del agente.
