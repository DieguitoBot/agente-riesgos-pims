# Agente PIMS v3 · Gestión de riesgos

Nueva versión en una carpeta y una base PostgreSQL independientes.
La aplicación aprobada sigue en `../agente_riesgos_pims_v2/`, normalmente en
<http://127.0.0.1:8080>. PIMS v3 abre en <http://127.0.0.1:8180>.

## Primera prueba desde un clon nuevo (Linux)

Instala Python 3.10 o superior y los binarios de PostgreSQL (`initdb`, `pg_ctl`).
En Ubuntu/Debian están disponibles mediante `sudo apt install python3-venv postgresql`.
Desde la raíz del repositorio:

```bash
cd agente_riesgos_pims_v3
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python preparar_demo.py
bash iniciar.sh
```

Abre la dirección mostrada, normalmente <http://127.0.0.1:8180>. En
**Historial y comparación → Abrir evaluación** encontrarás un caso ficticio
con dos riesgos. Puedes editar responsables, fechas y actividades, guardar,
recargar y descargar el CSV y los reportes. Esta demostración no necesita
Ollama, credenciales previas, la base aprobada ni la copia privada de ISO.
Está identificada como **demostración sin IA** y no contiene citas normativas.

El clúster de demostración vive en `datos/postgres_demo`, usa un socket privado
`datos/socket_demo` y puerto lógico 55440, sin escucha TCP. `bash iniciar.sh`
lo reinicia si está detenido. No modifica el PostgreSQL del sistema ni los
clústeres de otras carpetas. Las credenciales se generan localmente en `.env`.
El instalador se niega a reemplazar una configuración ya existente.

Para generar análisis nuevos instala e inicia Ollama y el modelo indicado en la
interfaz. La demostración tiene un corpus vacío: para evaluar con fuentes
normativas debes preparar una copia de una base con documentos autorizados,
como se explica abajo. La rama no incluye esas bases ni resultados privados.

## Probar ahora

Desde esta carpeta:

```bash
bash iniciar.sh
```

Si aún no se ha preparado la base:

```bash
../agente_riesgos_pims_v2/.venv/bin/python preparar_experimento.py
bash iniciar.sh
```

Ollama y el PostgreSQL privado deben estar iniciados. El lanzador usa el entorno `.venv` de esta carpeta o, si no existe,
el instalado en la versión aprobada para evitar duplicar dependencias. La base, credenciales,
código de aplicación y puerto son propios de este PIMS v3.

1. En **Historial y comparación**, pulsa **Abrir evaluación** sobre uno de los ensayos guardados.
2. En **Tratamiento de riesgos**, pulsa **Editar plan**.
3. Asigna responsable, área, fechas, estado y actividades según el caso.
4. Guarda y recarga la página; vuelve a abrir la evaluación desde el historial.
5. Descarga la **tabla CSV**, el **reporte con plan** y el **reporte original**.
6. En **Historial y comparación**, revisa el resumen de los campos añadidos.

También puedes generar un caso nuevo desde **Evaluación**: un resultado válido
de Ollama se guarda con su análisis y una propuesta de plan por riesgo.
La generación puede tardar varios minutos. Las respuestas de reglas locales no se guardan como resultados de IA.
El ejemplo ficticio se importa por separado y conserva su etiqueta de demostración.

## Gestión de evaluaciones y planes

Se implementa un subconjunto funcional inspirado en los conceptos de
`core_riskevaluation`, `core_risktreatment` y `core_risktreatmentactivity`:

| Tabla del esquema `gestitel_experimental` | Contenido |
| --- | --- |
| `evaluaciones` | Resultado original, reporte base, fecha y procedencia del ensayo. |
| `tratamientos` | Riesgo, hecho, amenaza, vulnerabilidad, medida, verificación, referencias, responsable, área, plazos, estado y valoración residual. |
| `actividades` | Tareas del plan, responsable, plazo y estado de ejecución declarado. |
| `cambios` | Instantáneas anteriores y posteriores de cada edición del plan. |

Los identificadores internos de la base y del esquema se conservan por
compatibilidad con los registros existentes; el nombre de la aplicación es
**Agente PIMS v3**.

El esquema `pims_riesgos` contiene una copia del corpus aprobado. El usuario de
la aplicación puede leerlo, pero solo escribe en las tablas de seguimiento.
No tiene permiso de conexión a la base aprobada. Se rechaza cualquier conexión
que no apunte a `pims_riesgos_experimental`, y la aplicación no admite conexión
administrativa. La preparación se ejecuta por separado y no se repite al iniciar.

No se importa todo `gestitel_base_de_datos.sql` ni se conecta a la plataforma
Gestitel. La integración real necesitaría acordar sus estados, usuarios,
activos, periodos y permisos. Se conserva la matriz académica actual de 1 a 5:
la diferencia del umbral 12 respecto a Gestitel sigue documentada en
[la referencia analizada](../docs/REFERENCIA_GESTITEL.md).

## Qué mejora el reporte

El reporte original se conserva sin editar. El reporte ampliado añade una tabla
resumen y el detalle vigente de cada plan: responsables, fechas, actividades,
referencias y evidencia de verificación. La tabla CSV permite comparar y revisar
los planes en una hoja de cálculo.

La mejora demostrable es **organización, persistencia y seguimiento**. El motor
IA, sus fuentes, sus validaciones y su matriz son los de la copia aprobada.
Tener más campos no demuestra mayor precisión normativa. La comparación dentro
de cada evaluación usa exactamente el mismo análisis original; las asignaciones
vacías se muestran como pendientes y no cuentan como información completada.

El estado **Verificado** requiere evidencia, verificador, fecha y actividades
completadas. Las cifras residuales son opcionales, se introducen juntas y solo
se admiten después de verificar la medida. Los conflictos entre dos ventanas
se rechazan con HTTP 409 para evitar que se pierda una edición.

## Comparar sin volver a generar el análisis

El historial puede incluir la referencia real de la versión aprobada, copiada
leyendo su JSON original. La copia no modifica ese archivo:

```bash
../agente_riesgos_pims_v2/.venv/bin/python importar_referencia.py
```

El ejemplo ficticio tiene procedencia `demostracion`.
El ensayo nuevo tiene procedencia `ollama_experimental`; la referencia copiada,
`referencia_aprobada`. Los cambios de un plan se guardan aparte del resultado IA.

## Ver las tablas en pgAdmin

En pgAdmin registra una conexión adicional con los mismos host/socket y puerto
de **PIMS - Riesgos (local)**, usuario administrativo local `pims_admin` y base
**pims_riesgos_experimental**. Explora **Schemas → gestitel_experimental → Tables**.
Las credenciales de la aplicación están en `.env`, fuera de Git.

## Verificación

```bash
../agente_riesgos_pims_v2/.venv/bin/python -m unittest tests_experimento -v
PIMS_TEST_EXPERIMENTO=1 ../agente_riesgos_pims_v2/.venv/bin/python -m unittest tests_experimento -v
node --check static/js/app.js
node --check static/js/experimento.js
../agente_riesgos_pims_v2/.venv/bin/python verificar_aislamiento.py --base-datos
```

La suite incluye 23 pruebas. Las seis SQL usan transacciones que revierten sus
registros sintéticos. La comprobación de aislamiento coteja los archivos de la
base aprobada contra `BASE_APROBADA.json`, las huellas del corpus y los permisos.
La prueba de navegador está en `pruebas_navegador.cjs`. En este equipo se puede
repetir mientras estén disponibles las dependencias temporales:

```bash
NODE_PATH=/tmp/pims-experimental-browser/node_modules PLAYWRIGHT_BROWSERS_PATH=/tmp/pims-experimental-browsers node pruebas_navegador.cjs
```

Prueba edición y recarga y restaura los valores del plan al terminar; registra
esas revisiones en el historial de PIMS v3. Requiere una evaluación guardada.
Los informes de ensayo y las capturas quedan en `datos/`, ignorado por Git.
La comprobación no equivale a una revisión normativa del contenido generado.

Las modificaciones de PIMS v3 se mantienen en esta carpeta. Para seguir
trabajando con la versión aprobada usa su dirección y sus lanzadores habituales.
