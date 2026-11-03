CREATE SCHEMA gestitel_experimental;
REVOKE ALL ON SCHEMA gestitel_experimental FROM PUBLIC;

CREATE TABLE gestitel_experimental.evaluaciones (
    id uuid PRIMARY KEY,
    creado timestamptz NOT NULL DEFAULT now(),
    titulo text NOT NULL,
    procedencia text NOT NULL,
    duracion_segundos double precision NOT NULL,
    resultado jsonb NOT NULL,
    reporte_base text NOT NULL
);
CREATE TABLE gestitel_experimental.tratamientos (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    evaluacion_id uuid NOT NULL REFERENCES gestitel_experimental.evaluaciones(id),
    codigo text NOT NULL,
    riesgo text NOT NULL,
    hecho text NOT NULL,
    amenaza text NOT NULL,
    vulnerabilidad text NOT NULL,
    dano text NOT NULL,
    medida text NOT NULL,
    verificacion text NOT NULL,
    prioridad text NOT NULL,
    referencias jsonb NOT NULL DEFAULT '[]',
    responsable text NOT NULL DEFAULT '',
    area text NOT NULL DEFAULT '',
    fecha_inicio date,
    fecha_fin date,
    estado text NOT NULL DEFAULT 'propuesto' CHECK (estado IN ('propuesto','en_revision','aprobado','en_curso','verificado','descartado')),
    evidencia_verificacion text NOT NULL DEFAULT '',
    verificado_por text NOT NULL DEFAULT '',
    fecha_verificacion date,
    probabilidad_residual integer CHECK (probabilidad_residual BETWEEN 1 AND 5),
    impacto_residual integer CHECK (impacto_residual BETWEEN 1 AND 5),
    version integer NOT NULL DEFAULT 1,
    actualizado timestamptz NOT NULL DEFAULT now(),
    UNIQUE(evaluacion_id, codigo),
    CHECK (fecha_inicio IS NULL OR fecha_fin IS NULL OR fecha_fin >= fecha_inicio),
    CHECK ((probabilidad_residual IS NULL) = (impacto_residual IS NULL))
);
CREATE TABLE gestitel_experimental.actividades (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tratamiento_id bigint NOT NULL REFERENCES gestitel_experimental.tratamientos(id),
    orden integer NOT NULL,
    descripcion text NOT NULL,
    responsable text NOT NULL DEFAULT '',
    fecha_fin date,
    completada boolean NOT NULL DEFAULT false
);
CREATE TABLE gestitel_experimental.cambios (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tratamiento_id bigint NOT NULL REFERENCES gestitel_experimental.tratamientos(id),
    creado timestamptz NOT NULL DEFAULT now(),
    antes jsonb NOT NULL,
    despues jsonb NOT NULL
);
CREATE INDEX ON gestitel_experimental.tratamientos(evaluacion_id);
CREATE INDEX ON gestitel_experimental.actividades(tratamiento_id);
GRANT USAGE ON SCHEMA gestitel_experimental TO pims_experimental_app;
GRANT SELECT, INSERT ON gestitel_experimental.evaluaciones, gestitel_experimental.cambios TO pims_experimental_app;
GRANT SELECT, INSERT, UPDATE ON gestitel_experimental.tratamientos TO pims_experimental_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON gestitel_experimental.actividades TO pims_experimental_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA gestitel_experimental TO pims_experimental_app;
