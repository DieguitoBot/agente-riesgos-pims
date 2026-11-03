# Agente de evaluación de riesgos de privacidad

Proyecto académico PIMS: **escenario → evaluación → fuentes → medidas → reporte**.
Flask presenta la interfaz; Python calcula la matriz y valida el análisis de
Ollama. PostgreSQL almacena los documentos, fragmentos y embeddings del agente.

## Probar la versión experimental con el equipo

La rama `mejora/laboratorio-gestitel-equipo` incluye el laboratorio en otra
carpeta, con historial, planes, actividades y descargas CSV. Sigue la
[guía para clonar y probar la rama](docs/PROBAR_RAMA_EXPERIMENTAL.md).
Incluye una demostración ficticia que funciona sin la base privada ni Ollama.

## Ejecutar en este equipo

Desde la raíz del repositorio:

```bash
cd agente_riesgos_pims_v2
.venv/bin/python -m db.local iniciar
bash iniciar.sh
```

Abre la dirección que muestra el lanzador, normalmente
<http://127.0.0.1:8080>. Escoge `qwen3.5:4b-q4_K_M`, describe el caso y pulsa
**Evaluar riesgo**. La generación puede tardar varios minutos según el equipo.
Ollama debe estar iniciado: `ollama list` muestra los modelos instalados;
si el servicio está detenido, ejecuta `ollama serve` en otra terminal.

No necesitas volver a importar documentos ni generar embeddings para cada prueba.
La aplicación carga `agente_riesgos_pims_v2/.env`; las variables ya definidas
en la terminal tienen prioridad. No publiques ese archivo ni `.datos/`.

## Visualizar la base de datos

En otra terminal, desde `agente_riesgos_pims_v2/`:

```bash
bash abrir_pgadmin.sh
```

Abre <http://127.0.0.1:5050>. Despliega:

**Agente de riesgos PIMS → PIMS - Riesgos (local) → Databases → pims_riesgos →
Schemas → pims_riesgos → Tables**.

Clic derecho en una tabla → **View/Edit Data → All Rows**.
`documentos` contiene las fuentes; `fragmentos`, los extractos, su procedencia y
embeddings; `controles_iso`, el catálogo disponible en la base actual.
La evaluación automática utiliza un catálogo temático parcial de 13 controles;
tener más controles almacenados no significa que se consulten todos.
El inventario también está disponible en <http://127.0.0.1:8080/api/documentos>.

## Instalación en otro equipo

Requiere Python 3.10+, binarios de PostgreSQL y Ollama. Los lanzadores de
PostgreSQL y pgAdmin incluidos están preparados para Linux y usan un clúster
privado del proyecto; no configuran el servicio PostgreSQL del sistema.

```bash
cd agente_riesgos_pims_v2
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-rag.txt
ollama pull qwen3.5:4b-q4_K_M
ollama pull embeddinggemma
.venv/bin/python -m db.local iniciar
```

Para una **base nueva vacía**, coloca la copia autorizada
`ISO_IEC_27701_2025.md` junto al README raíz y conserva `Ley-29733.md` y
`knowledge/documentos/`. Después importa y genera los embeddings:

```bash
.venv/bin/python -m db.migrar
.venv/bin/python -m rag.indexar
bash iniciar.sh
```

`db.migrar` es el importador del formato histórico. No lo ejecutes sobre la base
actual normalizada ni sobre documentos editados desde pgAdmin: requiere adaptar
la escritura antes de reimportar en ese esquema. La lectura y la indexación
admiten tanto el formato histórico JSON como las columnas de la base actual.
Para trasladar la base actual a otro equipo, usa una copia de seguridad y su
restauración. La instalación separada de pgAdmin está descrita en
[db/OPERACION.txt](agente_riesgos_pims_v2/db/OPERACION.txt).

La copia ISO no se distribuye en Git. Una vez importadas las fuentes, la
aplicación consulta PostgreSQL y no necesita leer los PDF o Markdown para evaluar.
FAISS se conserva únicamente para herramientas y pruebas del índice histórico.

## Pruebas y demostración

Desde `agente_riesgos_pims_v2/`:

```bash
PIMS_BUSQUEDA_SEMANTICA=0 .venv/bin/python -m unittest discover -s tests -v
PIMS_TEST_LECTURA=1 .venv/bin/python -m unittest tests.test_postgres_lectura -v
node --check static/js/app.js
.venv/bin/python -u comprobar_ia.py --entrada ejemplo_calidad_rag.json
```

Las primeras pruebas usan IA simulada. Las pruebas de lectura consultan
PostgreSQL sin modificar el corpus. El último comando usa Ollama real y guarda
`reporte_ia.txt` solo si la respuesta supera la validación.

La matriz es una convención académica del proyecto. Las citas verificadas
acreditan procedencia textual; el análisis y las medidas requieren revisión.
La herramienta no certifica cumplimiento, no ejecuta las medidas y no guarda un
historial de evaluaciones: descarga el reporte antes de recargar la página.

- [Guía para probar y explicar el agente](docs/GUIA_DEMOSTRACION.md).
- [Qué aporta la base de referencia de Gestitel](docs/REFERENCIA_GESTITEL.md).
- [Documentación funcional y API](agente_riesgos_pims_v2/README.md).
- [Operación de PostgreSQL y pgAdmin](agente_riesgos_pims_v2/db/OPERACION.txt).
- [Proceso de evaluación](agente_riesgos_pims_v2/PROMPT_SKILL.md).
- [Acuerdos para contribuir](CONTRIBUTING.md).

Cada integrante ejecuta Flask, PostgreSQL y Ollama en su equipo. Subir el código
a GitHub no publica la aplicación ni incluye la base local.
