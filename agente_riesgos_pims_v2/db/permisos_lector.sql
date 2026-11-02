-- Precondición: crear pims_lector LOGIN con contraseña privada desde el administrador.
-- Ejecutar únicamente en el proyecto dedicado al agente.
GRANT USAGE ON SCHEMA pims_riesgos TO pims_lector;
GRANT SELECT ON ALL TABLES IN SCHEMA pims_riesgos TO pims_lector;
DROP POLICY IF EXISTS lectura_agente ON pims_riesgos.documentos;
CREATE POLICY lectura_agente ON pims_riesgos.documentos FOR SELECT TO pims_lector USING (true);
DROP POLICY IF EXISTS lectura_agente ON pims_riesgos.fragmentos;
CREATE POLICY lectura_agente ON pims_riesgos.fragmentos FOR SELECT TO pims_lector USING (true);
