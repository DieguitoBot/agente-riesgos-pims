from hashlib import sha256
import re
from pathlib import Path
import time

import experimento as gestion

from flask import Flask, render_template, request, jsonify, Response, make_response
from knowledge.documento_iso import leer_secciones
from knowledge.documento_ley import leer_articulos, AVISO
from knowledge.controles_iso import CONTROLES
from db.repositorio import inventario, BaseNoDisponible
from llm.ollama_client import consultar_estado
from skills.evaluacion_riesgo import evaluar_riesgo
from seguridad_documental import acceso_documental

app = Flask(__name__)
# El lanzador local no usa debug: recargar HTML editado sin retener plantillas antiguas.
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.route("/")
def inicio():
    versiones = {
        nombre: sha256((Path(app.static_folder) / nombre).read_bytes()).hexdigest()[:16]
        for nombre in ('css/style.css', 'js/app.js', 'css/experimento.css', 'js/experimento.js')
    }
    respuesta = make_response(render_template("index.html", versiones=versiones))
    respuesta.cache_control.no_store = True
    return respuesta


@app.get('/api/documentos')
@acceso_documental
def api_documentos():
    try:
        return jsonify(almacenamiento='PostgreSQL', documentos=inventario())
    except BaseNoDisponible:
        return jsonify(error='Base documental no disponible.'), 503


@app.get('/api/fuente-rag/<huella>/<int:fragmento>')
@acceso_documental
def fuente_rag(huella, fragmento):
    if not re.fullmatch(r'[0-9a-f]{64}', huella):
        return jsonify(error='Huella inválida.'), 404
    from db.repositorio import leer_fuente_rag
    try:
        fuente = leer_fuente_rag(huella, str(fragmento))
    except BaseNoDisponible:
        return jsonify(error='Base documental no disponible.'), 503
    if not fuente:
        return jsonify(error='Fuente o versión no disponible en el corpus vigente.'), 404
    return jsonify(fuente=fuente, sha256=huella)


@app.route("/api/status")
def api_status():
    return jsonify(consultar_estado())


@app.route("/api/evaluar", methods=["POST"])
def api_evaluar():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Envía un objeto JSON válido con los datos de evaluación."}), 400
    inicio = time.monotonic()
    try:
        resultado = evaluar_riesgo(
            descripcion=datos.get("descripcion"),
            probabilidad=datos.get("probabilidad"),
            impacto=datos.get("impacto"),
            categorias=datos.get("categorias"),
            rol_privacidad=datos.get("rol_privacidad", "no_definido"),
            modelo=datos.get("modelo"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if datos.get("exigir_ia") is True and not resultado["llm_disponible"]:
        return jsonify(error=resultado["mensaje"], codigo="ia_no_disponible",
                       resultado_preliminar=resultado), 503
    if resultado.get('reporte_ia_generado'):
        try:
            resultado['experimento_id'] = gestion.guardar_evaluacion(
                resultado, time.monotonic() - inicio)
        except BaseNoDisponible:
            return jsonify(error='El análisis terminó, pero no pudo guardarse en PIMS v3. Intenta de nuevo.'), 503
    return jsonify(resultado)


@app.get('/api/fuente-iso/<codigo>')
@acceso_documental
def fuente_iso(codigo):
    control = CONTROLES.get(codigo)
    if not control and not re.fullmatch(r'(?:4\.3|6\.1\.[23]|8\.[23]|[AB]\.[123](?:\.\d+){0,2})',codigo):
        return jsonify(error='Control no incluido en el catálogo.'), 404
    try:
        seccion=control['guia'] if control else codigo
        huella=request.args.get('sha256')
        if huella:
            if not re.fullmatch(r'[a-f0-9]{64}',huella):return jsonify(error='Huella inválida.'),400
            from db.repositorio import leer_seccion_iso
            fragmento=leer_seccion_iso(seccion,huella)
        else:
            secciones, huella = leer_secciones()
            fragmento = secciones.get(seccion)
    except BaseNoDisponible:
        return jsonify(error='Base documental no disponible.'), 503
    except (OSError, UnicodeError, StopIteration):
        fragmento = None
    if not fragmento:
        return jsonify(error='Sección no disponible en PostgreSQL.'), 404
    texto = (f"Fuente: {fragmento['archivo']} · página OCR {fragmento['pagina']} · línea {fragmento['linea']}\n"
             f"SHA256: {huella}\nTexto OCR aportado por el usuario, pendiente de cotejo con el PDF.\n\n"
             + fragmento['texto'])
    return Response(texto, content_type='text/plain; charset=utf-8',
                    headers={'X-Content-Type-Options': 'nosniff'})


@app.get('/api/fuente-ley/<numero>')
def fuente_ley(numero):
    try:
        articulos, huella = leer_articulos()
        articulo = articulos.get(numero)
    except (OSError, UnicodeError):
        articulo = None
    if not articulo:
        return jsonify(error='Artículo no disponible en PostgreSQL.'), 404
    return Response(f"Fuente: {articulo['archivo']} · línea {articulo['linea']}\nSHA256: {huella}\n{AVISO}\n\n{articulo['texto']}",
                    content_type='text/plain; charset=utf-8', headers={'X-Content-Type-Options': 'nosniff'})


@app.errorhandler(gestion.NoEncontrado)
def no_encontrado(error):
    return jsonify(error=str(error)), 404


@app.errorhandler(gestion.Conflicto)
def conflicto(error):
    return jsonify(error=str(error)), 409


@app.get('/api/experimento/evaluaciones')
def historial():
    try:
        return jsonify(evaluaciones=gestion.listar_evaluaciones())
    except BaseNoDisponible:
        return jsonify(error='La base de PIMS v3 no está disponible.'), 503


@app.get('/api/experimento/evaluaciones/<evaluacion>')
def detalle_experimental(evaluacion):
    try:
        detalle = gestion.obtener_evaluacion(evaluacion)
        detalle['comparacion'] = gestion.comparar(detalle)
        return jsonify(detalle)
    except BaseNoDisponible:
        return jsonify(error='La base de PIMS v3 no está disponible.'), 503


@app.put('/api/experimento/planes/<int:plan_id>')
def editar_plan(plan_id):
    try:
        return jsonify(gestion.actualizar_plan(plan_id, request.get_json(silent=True)))
    except gestion.Conflicto:
        raise
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except BaseNoDisponible:
        return jsonify(error='No se pudo guardar el plan.'), 503


@app.get('/api/experimento/evaluaciones/<evaluacion>/reporte')
def exportar_experimento(evaluacion):
    formato = request.args.get('formato', 'txt')
    if formato not in ('txt', 'base', 'csv', 'html'):
        return jsonify(error='Formato no admitido.'), 400
    try:
        detalle = gestion.obtener_evaluacion(evaluacion)
    except BaseNoDisponible:
        return jsonify(error='La base de PIMS v3 no está disponible.'), 503
    if formato=='html':
        from skills.reporte import preparar_reporte
        resultado=dict(detalle['resultado'])
        resultado.setdefault('evaluacion_id',detalle['id'])
        resultado.setdefault('fecha_evaluacion',detalle['creado'])
        return render_template('reporte.html',documento=preparar_reporte(resultado),
                               resultado=resultado,planes=detalle['planes'])
    contenido = (gestion.exportar_csv(detalle) if formato == 'csv' else
                 detalle['reporte_base'] if formato == 'base' else gestion.reporte_experimental(detalle))
    extension = 'csv' if formato == 'csv' else 'txt'
    return Response(contenido, content_type=('text/csv' if formato == 'csv' else 'text/plain')+'; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="pims-v3-{detalle["id"]}-{formato}.{extension}"',
                             'X-Content-Type-Options': 'nosniff'})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8180)
