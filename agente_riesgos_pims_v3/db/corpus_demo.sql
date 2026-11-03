-- Corpus vacío para probar seguimiento sin distribuir normativa privada.
CREATE SCHEMA pims_riesgos;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
CREATE TABLE pims_riesgos.documentos (
    id bigint PRIMARY KEY, clave text NOT NULL, categoria text NOT NULL,
    sha256 text NOT NULL, contenido text NOT NULL DEFAULT ''
);
CREATE TABLE pims_riesgos.fragmentos (
    id bigint PRIMARY KEY, documento_id bigint REFERENCES pims_riesgos.documentos(id),
    tipo text NOT NULL, codigo text NOT NULL, datos jsonb NOT NULL,
    embedding double precision[], modelo_embedding text
);
CREATE TABLE pims_riesgos.controles_iso (codigo text PRIMARY KEY);
GRANT USAGE ON SCHEMA pims_riesgos TO pims_experimental_app;
GRANT SELECT ON ALL TABLES IN SCHEMA pims_riesgos TO pims_experimental_app;
