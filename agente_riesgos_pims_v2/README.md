# Agente de evaluación de riesgos de privacidad · v2

Python + Flask + HTML/CSS/JavaScript. Esta versión trabaja de manera independiente:
identifica riesgos, compara valoraciones y propone medidas; no se conecta con otros
agentes ni realiza auditorías o decisiones legales.

Para instalar desde cero, consulta la [guía del repositorio](../README.md).

## Iniciar

```bash
cd agente_riesgos_pims_v2
bash iniciar.sh
```

El lanzador reutiliza el entorno existente, elige un puerto libre entre 8080 y 8100
y abre el navegador. Para aplicar cambios, detén solo la terminal de la v2 con
Ctrl+C, vuelve a iniciar y recarga la página. También admite `--sin-navegador` y
`--port 8080`. No detiene otras aplicaciones.

Ollama debe estar funcionando con un modelo local instalado. Comprueba en tu
terminal `ollama list`; si el servicio no está iniciado, usa `ollama serve`.
La pantalla comprueba el servicio y permite elegir cualquiera de los modelos
instalados. La elección se aplica a esa solicitud, sin cambiar variables globales.
No se descargan modelos automáticamente.

| Variable | Predeterminado |
| --- | --- |
| OLLAMA_URL | http://127.0.0.1:11434 |
| OLLAMA_MODEL | qwen2.5:3b |
| OLLAMA_TIMEOUT | 300 segundos por solicitud de generación |

No se lee `.env` automáticamente. Ejemplo con un modelo instalado distinto:

```bash
OLLAMA_MODEL='nombre:etiqueta' ./iniciar.sh
```

## Reporte de IA

El modelo genera un análisis JSON: hechos, vulnerabilidades, amenazas, daños a las
personas, medidas, prioridad, verificación, valoración propia y referencias.
Python valida su estructura, calcula puntajes y comprueba las citas normativas;
construye el reporte descargable a partir de ese análisis, sin otra llamada al LLM.
La pantalla permite descargar el texto completo. La descarga conserva el escenario
evaluado aunque después cambies el formulario.

La interfaz exige una respuesta de IA válida. Un timeout, modelo ausente o respuesta
inválida muestra el motivo y permite elegir otro modelo o reintentar. No ofrece un
reporte básico como si fuera IA. La API conserva el respaldo de reglas para sus
consumidores anteriores, con un origen explícito.

Se redujo la generación a un máximo de 3 riesgos, 2 indicadores solicitados y 3
referencias por norma. Se usan hasta 4 fragmentos ISO de 2.200 caracteres, hasta 3
artículos legales de 1.800 caracteres y, cuando se recupera consentimiento, el
artículo 14 para contextualizar excepciones. Se informa el truncamiento. El contexto
de Ollama es de 12.288 tokens, la salida máxima de 4.000, temperatura 0 y permanencia
del modelo en memoria de 10 minutos. Esto limita trabajo y repeticiones; la latencia
real depende del modelo, CPU/GPU y memoria, y no se garantiza un tiempo fijo.

Se incluye el contrato JSON tanto en `format` como en el prompt, siguiendo la
[documentación de Ollama](https://docs.ollama.com/capabilities/structured-outputs).
Una respuesta mal formada o truncada permite un único reintento con un contrato
breve (informe narrativo, riesgos, hechos y medidas), de hasta 1.800 tokens de salida.
Ese informe sigue siendo generado por IA y se identifica como `formato_ia: "breve"`;
no incluye valoración numérica de IA, indicadores ni referencias normativas verificadas.
Las cifras y referencias no se reconstruyen mediante reglas. No se
repiten automáticamente errores de conexión ni timeouts. En el peor caso dos
solicitudes pueden consumir aproximadamente dos veces el timeout configurado.
La pantalla muestra tiempo transcurrido y espera el análisis completo, sin streaming.

## Conocimiento documental y controles específicos

Se leen los documentos junto a la carpeta del proyecto:

- `../ISO_IEC_27701_2025.md`: Markdown OCR. Recuperación temática del anexo B sobre
  un catálogo parcial de 13 controles del anexo A, filtrado por rol.
- `../Ley-29733.md`: recuperación temática de artículos para explicar riesgos de
  privacidad. No constituye una versión oficial consolidada verificada.

Cada referencia se vincula a un riesgo y a un hecho literal del escenario. Las
citas se cotejan con el fragmento que recibió el modelo. Se descartan códigos,
artículos, citas o hechos inventados en las referencias. El reporte incluye fuentes,
líneas, páginas OCR para ISO y SHA256 de ambos documentos. Una cita válida acredita
procedencia textual; la interpretación requiere revisión humana.

El reporte identifica el control específico, por ejemplo A.3.9 (Permisos de acceso),
su guía B.3.9, la posible brecha y la evidencia necesaria para comprobarla. El anexo A
contiene controles; el B guía su implementación. No se declara un anexo completo
"vulnerado" ni una no conformidad confirmada basándose solo en el relato.

El documento legal incluye concordancias históricas al reglamento de 2013; estas
se excluyen de los fragmentos recuperados. El reglamento aprobado por D.S.
016-2024-JUS entró en vigor el 31 de marzo de 2025, según la
[Autoridad Nacional de Protección de Datos Personales](https://www.gob.pe/institucion/anpd/campa%C3%B1as/128319-nuevo-reglamento-de-proteccion-de-datos-personales).
Su texto no está incorporado a esta versión: no se inventan artículos del nuevo
reglamento ni se certifica actualidad de todo el Markdown del usuario.

La selección temática y el catálogo son parciales; una lista vacía no demuestra
cumplimiento. No hay embeddings, FAISS ni búsqueda semántica.
Fuente del catálogo de códigos/temas:
[BSI, revisión 2025, páginas 24–32](https://www.bsigroup.com/siteassets/pdf/th-th/products-and-services/th-as-cross-lg-ict-dt-iso27701-mp-iso27701revisionwebinar-1125.pdf).
Los temas españoles son resúmenes propios.

## API

`POST /api/evaluar`:

```json
{
  "descripcion": "La universidad almacena DNI sin control de acceso y sin plazo de conservación.",
  "probabilidad": 3,
  "impacto": 4,
  "categorias": ["Identificación"],
  "rol_privacidad": "responsable",
  "modelo": "qwen2.5:3b",
  "exigir_ia": true
}
```

`modelo` es opcional; usa la configuración del servidor si se omite o es null.
`rol_privacidad` admite responsable, encargado, ambos o no_definido. Las entradas
inválidas devuelven 400 antes de generar texto.

La respuesta conserva los campos anteriores y añade:

- `referencias_ley`: relaciones con artículos y citas verificadas.
- `documentacion_ley`: estado, artículos recuperados y huella documental.
- `reporte_texto`: reporte completo listo para exportar.
- `reporte_ia_generado`: true únicamente cuando el análisis proviene del modelo.

`exigir_ia: true` devuelve 503 y `codigo: "ia_no_disponible"` ante un fallo del LLM,
con `resultado_preliminar` identificado como reglas. Sin ese parámetro se conserva
HTTP 200 y `modo: "reglas_locales"`. El respaldo no tiene valoración IA ni referencias
normativas generadas. `GET /api/status` lista modelos; `/api/fuente-iso/<codigo>` y
`/api/fuente-ley/<numero>` muestran las secciones utilizadas como texto plano.

Matriz académica: probabilidad × impacto, ambos 1–5; 1–5 Bajo, 6–11 Medio,
12–19 Alto, 20–25 Crítico. Python conserva la valoración del usuario y calcula
separadamente la opinión IA. La matriz no es una escala prescrita por ISO.

## Comprobar y generar desde la terminal

```bash
# Desde agente_riesgos_pims_v2/, con el entorno instalado:
.venv/bin/python comprobar_ia.py
```

Este comando analiza `ejemplo_solicitud.json` con Ollama real, mide la duración y
guarda `reporte_ia.txt` únicamente si hay análisis IA válido. Admite `--modelo`,
`--entrada archivo.json` y `--salida reporte.txt`. Sale con código 1 si falla; no
reemplaza la salida con reglas ni elimina un reporte anterior.

Verificación automatizada:

```bash
.venv/bin/python -m unittest discover -s tests -v
node --check static/js/app.js
```

La suite completa requiere los documentos locales indicados arriba, incluido el
OCR ISO original que no se distribuye con el código.

50 pruebas aprobadas: recuperación de documentos, citas inventadas, roles,
reporte con ley, valoración, selección de modelo, API estricta y compatible,
recuperación de informe breve, rechazo de hechos inventados y errores de red. Las respuestas LLM están simuladas.
En la revisión del 19 de octubre de 2026 no se pudo conectar con Ollama local;
no se verificó inferencia real. Usa `comprobar_ia.py`
en tu terminal para verificar el modelo y su latencia real.
