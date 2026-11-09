# Validación de V3 como única aplicación

- Suite del motor/API/RAG/mantenimiento: 91 pruebas, 87 aprobadas y 4 SQL omitidas.
- Suite de gestión: 23 pruebas, 17 aprobadas y 6 SQL omitidas.
- Sintaxis de JavaScript (ambos scripts), Bash y diff sin errores.
- Extracción real desde las fuentes trasladadas: 18 documentos y 1968 fragmentos.
- PostgreSQL 16.2 en modo monousuario: creación de los dos esquemas y seis tablas,
  concesiones SQL verificadas (edición de tratamientos permitida, escritura de corpus denegada).

El entorno de revisión no permite crear sockets: no se pudo iniciar un servidor
PostgreSQL conectado ni ejecutar las diez pruebas SQL transaccionales. La revisión
monousuario comprueba DDL y permisos, no sustituye esas pruebas. Tampoco se ejecutó
Ollama ni se revisó contenido generado con un modelo real.

Antes de cerrar la validación en Ubuntu: iniciar el clúster existente, ejecutar las
pruebas SQL de tests_experimento, abrir un plan, editarlo, recargar y exportar CSV.
Las cuatro pruebas de lectura adicionales necesitan corpus ISO y Ley autorizado.
No se ha tocado ninguna base de datos del equipo del usuario ni sus archivos locales.
