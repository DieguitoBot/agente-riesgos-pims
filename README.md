# Agente PIMS V3 — Evaluación y gestión de riesgos de privacidad

**V3 es la única aplicación mantenida de este repositorio.** Incluye evaluación
con Ollama local, recuperación documental desde PostgreSQL, planes de tratamiento,
actividades, historial de cambios y exportación de reportes y CSV.

## Instalación nueva en Ubuntu

```bash
sudo apt install python3-venv postgresql
cd agente_riesgos_pims_v3
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-rag.txt
.venv/bin/python preparar_demo.py
bash iniciar.sh
```

Abre http://127.0.0.1:8180 (el lanzador indica otro puerto si está ocupado).
La preparación inicial genera una base privada, credenciales locales y un caso
**ficticio sin IA**. No reemplaza un `.env` existente. El corpus inicial está vacío:
ver [la guía V3](agente_riesgos_pims_v3/README.md) para cargar las fuentes autorizadas.

## Si ya usabas V3

Conserva `agente_riesgos_pims_v3/.env`, su carpeta `datos/` y el clúster que
indica el DSN. Usa un entorno propio de V3. **No ejecutes una preparación nueva**.
Los nombres internos `pims_riesgos_experimental`, `pims_experimental_app` y
`gestitel_experimental` permanecen por compatibilidad con tus evaluaciones y planes.
El servidor se inicia con `bash iniciar.sh` desde la carpeta V3.

Si tus datos viven en el clúster privado de la raíz `.datos/`, debes mantenerlo:
la limpieza del código no elimina ni migra automáticamente tus bases locales.
Consulta [operación y migración](docs/OPERACION_V3.md) antes de actualizar.

## API e integración

- `POST /api/evaluar`: descripción, probabilidad e impacto (enteros 1–5), rol y modelo opcional.
- `GET /api/status`: disponibilidad de Ollama.
- `GET /api/documentos`: inventario PostgreSQL.
- `/api/experimento/evaluaciones` y `/api/experimento/planes/...`: historial y seguimiento.

Se conservan estas rutas para no romper clientes existentes. El orquestador es
un proyecto externo y debe configurar `RIESGOS_URL=http://127.0.0.1:8180`
(o el puerto efectivamente anunciado). No está integrado automáticamente.

## Verificación

Desde `agente_riesgos_pims_v3`:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest tests_experimento -v
PIMS_TEST_EXPERIMENTO=1 .venv/bin/python -m unittest tests_experimento -v
node --check static/js/app.js
node --check static/js/experimento.js
```

Las pruebas SQL requieren una base V3 preparada y revierten sus registros sintéticos.
El núcleo IA requiere Ollama y documentos autorizados. No se incluyen normativa
privada, bases de datos, credenciales ni modelos. Ningún resultado certifica
cumplimiento normativo; las decisiones requieren revisión humana.
