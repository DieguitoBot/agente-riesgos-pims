# Probar Agente PIMS v3 con el equipo

Rama: `mejora/gestion-riesgos-v3`.

Esta rama contiene la versión actual y PIMS v3 en
`agente_riesgos_pims_v3/`. Para conservar tu instalación habitual,
clona la rama en una carpeta nueva. No es necesario modificar una base existente.

## Instalación de la demostración (Linux o WSL)

Requiere Git, Python 3.10+ con `venv` y binarios de PostgreSQL. En Ubuntu/Debian:

```bash
sudo apt install git python3-venv postgresql
```

Después:

```bash
git clone --branch mejora/gestion-riesgos-v3 --single-branch https://github.com/DieguitoBot/agente-riesgos-pims.git agente-riesgos-pims-v3
cd agente-riesgos-pims-v3/agente_riesgos_pims_v3
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python preparar_demo.py
bash iniciar.sh
```

Abre la dirección que muestra la terminal, normalmente
<http://127.0.0.1:8180>. Si el puerto está ocupado, el lanzador muestra otro.
El PostgreSQL de la demostración tiene su propio directorio y socket, sin
escucha TCP. No se modifica el servicio PostgreSQL del sistema.

La preparación crea credenciales locales y un ejemplo ficticio con dos riesgos.
No necesita el archivo `.env` de otro integrante ni Ollama para probar el
seguimiento. El ejemplo está identificado como **demostración sin IA**.

## Recorrido que debe probar cada integrante

1. Abre **Historial y comparación → Abrir evaluación**.
2. En **Tratamiento de riesgos**, abre **Editar plan**.
3. Introduce un responsable de prueba, área y fecha; cambia el estado a **En revisión**.
4. Añade una actividad y guarda el plan.
5. Recarga la página y vuelve a abrir la evaluación: los cambios deben seguir ahí.
6. Descarga **tabla CSV**, **reporte con plan** y **reporte original**.
7. Revisa la comparación. El original debe conservarse; el ampliado añade el seguimiento.

Para probar la validación, intenta marcar un plan **Verificado** sin evidencia:
la aplicación debe rechazarlo. También exige verificador, fecha, responsable y
actividades completadas. Las cifras residuales se introducen juntas y tras
verificar el plan.

## Pruebas automáticas

Desde la carpeta de PIMS v3:

```bash
PIMS_TEST_EXPERIMENTO=1 .venv/bin/python -m unittest tests_experimento -v
```

Las 23 pruebas incluyen persistencia y conflictos de edición; los registros
sintéticos de las pruebas SQL se revierten. La demostración guardada permanece.
Node.js es opcional y permite comprobar la sintaxis de los scripts:

```bash
node --check static/js/app.js
node --check static/js/experimento.js
```

## Generar reportes nuevos con IA y fuentes

La demostración prueba la interfaz y el seguimiento; no incluye normativa ni
un corpus de documentos. Para generar análisis nuevos con IA se necesita Ollama
y un modelo local. Para comparar reportes con fuentes también se necesita una
base documental propia con copias autorizadas; consulta el
[README dPIMS v3](../agente_riesgos_pims_v3/README.md).

Las bases locales, `.env`, resultados de ensayos, copia privada ISO y SQL original
del ingeniero no se distribuyen por Git. El código y la demostración ficticia
permiten probar la nueva funcionalidad sin esos archivos.

## Reiniciar y comunicar resultados

Detén la aplicación con Ctrl+C. Para volver a abrirla ejecuta `bash iniciar.sh`;
el lanzador inicia el clúster de demostración si está detenido, sin reimportar.

Al compartir un fallo indica la rama/commit, el paso que hiciste, el resultado
esperado y el mensaje que apareció. Usa datos ficticios en las capturas y casos.
