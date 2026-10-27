# Agente de evaluación de riesgos de privacidad

Proyecto académico PIMS: **Prompt → Asistente → Skill → Resultado funcional**.
El código está en `agente_riesgos_pims_v2/`. Evalúa escenarios, calcula una matriz
de riesgo, consulta Ollama local y propone medidas con referencias verificables.

## Instalación desde un clon del repositorio

Requisitos: Python 3.10 o superior. Ollama y un modelo local instalado son
necesarios para generar el reporte desde la interfaz. Node.js es opcional y solo
se usa para comprobar la sintaxis JavaScript.

Desde la raíz del repositorio, en Linux/macOS:

```bash
cd agente_riesgos_pims_v2
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-rag.txt
bash iniciar.sh
```

En Windows PowerShell:

```powershell
cd agente_riesgos_pims_v2
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-rag.txt
.\.venv\Scripts\python.exe iniciar_local.py
```

El lanzador muestra la dirección local y abre el navegador. Comprueba los modelos
con `ollama list`; si no hay servicio, ejecuta `ollama serve` en otra terminal.
El modelo predeterminado es `qwen2.5:3b`; puedes elegir uno ya instalado en la web.
El proyecto no descarga modelos automáticamente. No carga archivos `.env`.

## Activar el RAG

Con Ollama iniciado, desde `agente_riesgos_pims_v2/`:

```bash
ollama pull qwen2.5:3b
ollama pull embeddinggemma
.venv/bin/python -m rag.indexar
.venv/bin/python comprobar_ia.py --entrada ejemplo_calidad_rag.json
```

En Windows usa `.\.venv\Scripts\python.exe`. El índice se genera localmente y
no se sube a Git. Reindexa al cambiar los documentos, el modelo de embeddings o
la versión de segmentación. La búsqueda combina embeddings FAISS y términos;
el reporte distingue fuentes recuperadas de citas verificadas usadas por la IA.
Sin dependencias o índice, la aplicación informa que el RAG no está disponible.

## Documentos locales

Conservar esta estructura:

```text
raiz-del-repositorio/
  Ley-29733.md
  ISO_IEC_27701_2025.md   # copia local autorizada, excluida de Git
  agente_riesgos_pims_v2/
```

El documento ISO original contiene restricciones de reproducción y no se incluye
en el paquete de publicación. Cada integrante debe colocar su copia autorizada
con ese nombre. El lector espera el formato OCR descrito en los tests; otro
Markdown puede requerir adaptar el lector. Sin documentos, la aplicación informa
la falta de sustento local; no fabrica referencias.

## Verificación

Desde `agente_riesgos_pims_v2/` en Linux/macOS:

```bash
.venv/bin/python -m unittest discover -s tests -v
node --check static/js/app.js
.venv/bin/python comprobar_ia.py
```

En Windows sustituir `.venv/bin/python` por `.\.venv\Scripts\python.exe`.
Las pruebas ISO usan un documento sintético y no necesitan la copia privada.
Las pruebas legales usan el Markdown incluido en el repositorio. Las respuestas de IA de
los tests están simuladas; `comprobar_ia.py` requiere Ollama real. No confundir una
suite aprobada con una evaluación de calidad del modelo.

## Alcance y colaboración

No implementa auditoría, certificación legal, orquestador, comunicación entre
agentes ni PostgreSQL. Incluye RAG local con embeddings y FAISS, además de
recuperación temática para referencias ISO y legales.
La matriz es una convención académica del proyecto.

- [Mejoras y validación de calidad del RAG](docs/CALIDAD_REPORTES_RAG.md).
- [Diagnóstico y pendientes](docs/REVISION.md).
- [Acuerdos para contribuir](CONTRIBUTING.md).
- [Documentación funcional y API](agente_riesgos_pims_v2/README.md).
- [Identidad, activación y proceso de la Skill](agente_riesgos_pims_v2/PROMPT_SKILL.md).

GitHub permite compartir el código; cada integrante ejecuta Flask y Ollama en su
equipo. Subir el repositorio no publica automáticamente la aplicación web.
