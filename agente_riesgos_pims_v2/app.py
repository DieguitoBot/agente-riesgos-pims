from flask import Flask, render_template, request, jsonify, Response
from knowledge.documento_iso import leer_secciones
from knowledge.documento_ley import leer_articulos, AVISO
from knowledge.controles_iso import CONTROLES
from llm.ollama_client import consultar_estado
from skills.evaluacion_riesgo import evaluar_riesgo

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify(consultar_estado())


@app.route("/api/evaluar", methods=["POST"])
def api_evaluar():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Envía un objeto JSON válido con los datos de evaluación."}), 400
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
    return jsonify(resultado)


@app.get('/api/fuente-iso/<codigo>')
def fuente_iso(codigo):
    control = CONTROLES.get(codigo)
    if not control:
        return jsonify(error='Control no incluido en el catálogo.'), 404
    try:
        secciones, huella = leer_secciones()
        fragmento = secciones.get(control['guia'])
    except (OSError, UnicodeError, StopIteration):
        fragmento = None
    if not fragmento:
        return jsonify(error='Sección no disponible en el Markdown local.'), 404
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
        return jsonify(error='Artículo no disponible en el Markdown local.'), 404
    return Response(f"Fuente: {articulo['archivo']} · línea {articulo['linea']}\nSHA256: {huella}\n{AVISO}\n\n{articulo['texto']}",
                    content_type='text/plain; charset=utf-8', headers={'X-Content-Type-Options': 'nosniff'})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
