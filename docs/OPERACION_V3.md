# Operación y actualización a V3 única

## Antes de actualizar un equipo existente

1. Detén la aplicación, no borres `.datos/`, `datos/` ni `.env`.
2. Respalda con `pg_dump -Fc` la base indicada en el `.env` de V3, usando sus
   parámetros de conexión. Conserva también `.env` y las carpetas de datos en
   una ubicación privada. No publiques respaldos ni credenciales.
3. Crea `.venv` dentro de V3 e instala sus dos requirements.
4. Comprueba que el PostgreSQL al que apunta V3 siga iniciado.

Si V3 apunta al clúster histórico de la raíz, inícialo sin recrearlo:

```bash
# Desde la raíz. Ajusta la versión de PostgreSQL al PG_VERSION del clúster.
/usr/lib/postgresql/14/bin/pg_ctl -D "$PWD/.datos/postgres" \
  -l "$PWD/.datos/postgres.log" \
  -o "-k $PWD/.datos/socket -p 55439 -c listen_addresses=''" -w start
```

Usa `pg_ctl status` antes; no inicies dos instancias sobre el mismo directorio.
No es necesario renombrar la base, los esquemas o los roles para utilizar V3.
No se eliminan automáticamente bases locales: no están versionadas en Git.

## Instancia nueva

`preparar_demo.py` crea `datos/postgres_demo`, socket privado `datos/socket_demo`
y puerto lógico 55440, sin TCP. El lanzador reinicia este clúster si está detenido.
Inicialmente hay un caso ficticio y corpus vacío. Carga los documentos según el
README V3 para realizar evaluaciones fundamentadas.

## Importar un corpus histórico (opcional, una sola vez)

Para quien todavía no tenga base V3, `preparar_experimento.py --env-origen /ruta/privada/origen.env`
lee un archivo de credenciales elegido explícitamente. La base origen debe ser
`pims_riesgos`, en el socket `.datos/socket` de este repositorio. Crea la base V3,
copia el corpus y verifica sus huellas. No cambia el origen ni sobrescribe `.env`.
No se requiere conservar el código anterior. Mantener el PostgreSQL de origen
activo durante la importación; después V3 opera sobre su propia base.

## Mantenimiento del corpus

Las instalaciones nuevas incluyen `PIMS_DATABASE_ADMIN_URL` apuntando solo a V3.
En instalaciones existentes, agrégalo con la cuenta propietaria de esa base antes
de ejecutar migraciones o embeddings. La aplicación HTTP sigue usando únicamente
`PIMS_DATABASE_URL` y no admite `conectar(admin=True)`.

En pgAdmin puede registrarse el mismo host/socket, puerto y nombre de base del
DSN de V3. No se necesita instalar ni ejecutar un pgAdmin adicional del proyecto.
