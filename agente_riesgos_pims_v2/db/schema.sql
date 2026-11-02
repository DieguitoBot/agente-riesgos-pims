-- Ejecutar únicamente en la base/proyecto dedicado al agente de riesgos.
CREATE SCHEMA IF NOT EXISTS pims_riesgos;
REVOKE ALL ON SCHEMA pims_riesgos FROM PUBLIC;
CREATE TABLE IF NOT EXISTS pims_riesgos.documentos (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    clave text UNIQUE NOT NULL,
    categoria text NOT NULL CHECK (categoria IN ('normativa','institucional','proyecto','reporte','evidencia')),
    titulo text NOT NULL,
    sha256 text NOT NULL CHECK (length(sha256) = 64),
    contenido text NOT NULL,
    original bytea NOT NULL,
    metadatos jsonb NOT NULL DEFAULT '{}',
    actualizado timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS pims_riesgos.fragmentos (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    documento_id bigint NOT NULL REFERENCES pims_riesgos.documentos(id) ON DELETE CASCADE,
    tipo text NOT NULL CHECK (tipo IN ('iso','ley','rag')),
    codigo text NOT NULL,
    datos jsonb NOT NULL,
    UNIQUE(documento_id, tipo, codigo)
);
CREATE INDEX IF NOT EXISTS fragmentos_tipo ON pims_riesgos.fragmentos(tipo);
ALTER TABLE pims_riesgos.documentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE pims_riesgos.fragmentos ENABLE ROW LEVEL SECURITY;
-- Sin acceso anónimo ni políticas públicas. El lector dedicado recibe una política explícita.
REVOKE ALL ON ALL TABLES IN SCHEMA pims_riesgos FROM PUBLIC;

ALTER TABLE pims_riesgos.fragmentos ADD COLUMN IF NOT EXISTS embedding double precision[];
ALTER TABLE pims_riesgos.fragmentos ADD COLUMN IF NOT EXISTS modelo_embedding text;
