"""Cliente HTTP de Ollama. No instala, descarga ni ejecuta modelos."""
import json

import requests

from config import obtener_configuracion, obtener_modelo
from prompts.riesgo_prompt import ESQUEMA_ANALISIS, construir_esquema, construir_mensajes, objeto, TEXTO


ESQUEMA_BREVE = objeto({
    'informe': TEXTO,
    'riesgos': {'type': 'array', 'maxItems': 3, 'items': objeto({
        'riesgo': TEXTO, 'evidencia': TEXTO, 'medida': TEXTO,
    })},
})


class OllamaError(Exception):
    """Fallo controlado que permite activar las reglas locales."""


def _configuracion(modelo=None):
    try:
        return obtener_configuracion(modelo)
    except ValueError as exc:
        raise OllamaError(str(exc)) from exc


def _solicitar(metodo, ruta, config, **kwargs):
    try:
        with requests.Session() as session:
            # El servicio local no utiliza proxies ni credenciales del entorno.
            session.trust_env = False
            response = session.request(
                metodo, config["url"] + ruta,
                timeout=(min(3, config["timeout"]), config["timeout"] if metodo == "POST" else min(3, config["timeout"])),
                allow_redirects=False, **kwargs,
            )
            if response.status_code == 404 and metodo == "POST":
                raise OllamaError(
                    f"El modelo {config['modelo']} no está instalado o la ruta de Ollama no existe. "
                    f"Comprueba ollama list; instala manualmente con: ollama pull {config['modelo']}."
                )
            if not 200 <= response.status_code < 300:
                raise OllamaError(f"Ollama devolvió un error HTTP {response.status_code}.")
            return response.json()
    except requests.Timeout as exc:
        raise OllamaError(f"Ollama no completó la respuesta en {config['timeout']:g} segundos. El análisis documental puede tardar más; revisa la carga del equipo o aumenta OLLAMA_TIMEOUT.") from exc
    except requests.ConnectionError as exc:
        raise OllamaError("No se pudo conectar con Ollama local. Comprueba el servicio (ollama serve), la URL y los permisos de conexión.") from exc
    except (requests.RequestException, ValueError) as exc:
        raise OllamaError("No se pudo obtener una respuesta JSON válida del servicio Ollama.") from exc


def _validar_campo(valor, esquema, ruta):
    """Valida el subconjunto JSON Schema del contrato sin dependencias nuevas."""
    tipo = esquema['type']
    if isinstance(tipo, list):
        if valor is None and 'null' in tipo:
            return None
        tipo = next(t for t in tipo if t != 'null')
    if tipo == 'object':
        if not isinstance(valor, dict) or any(k not in valor for k in esquema['required']):
            raise OllamaError(f'Ollama devolvió campos incompletos en {ruta}.')
        return {k: _validar_campo(valor[k], sub, ruta + '.' + k)
                for k, sub in esquema['properties'].items() if k in valor}
    if tipo == 'array':
        if not isinstance(valor, list) or len(valor) > esquema.get('maxItems', 100):
            raise OllamaError(f'Ollama devolvió una lista inválida en {ruta}.')
        return [_validar_campo(v, esquema['items'], ruta) for v in valor]
    if tipo == 'integer':
        if type(valor) is not int or not esquema['minimum'] <= valor <= esquema['maximum']:
            raise OllamaError(f'Ollama devolvió una cifra inválida en {ruta}.')
        return valor
    if tipo == 'string':
        if not isinstance(valor, str) or not valor.strip():
            raise OllamaError(f'Ollama devolvió texto inválido en {ruta}.')
        valor = valor.strip()
        if 'enum' in esquema and valor not in esquema['enum']:
            raise OllamaError(f'Ollama devolvió una opción inválida en {ruta}.')
        return valor
    raise OllamaError('Tipo de análisis no admitido.')


def validar_analisis(datos):
    # Compatibilidad con respuestas anteriores sin referencias RAG.
    esquema = dict(ESQUEMA_ANALISIS, required=[k for k in ESQUEMA_ANALISIS['required'] if k != 'referencias_rag'])
    resultado = _validar_campo(datos, esquema, 'análisis')
    opinion = resultado['opinion_llm']
    if (opinion['probabilidad'] is None) != (opinion['impacto'] is None):
        raise OllamaError('La valoración IA debe incluir ambas cifras o ambas nulas.')
    return resultado


def recuperar_analisis(texto):
    """Recupera JSON puro, cercado o rodeado de texto; nunca ejecuta contenido."""
    if not isinstance(texto, str):
        raise OllamaError("Ollama no devolvió contenido de texto.")
    try:
        datos = json.loads(texto)
    except ValueError:
        inicio = texto.find("{")
        if inicio < 0:
            raise OllamaError("Ollama no devolvió un JSON recuperable.")
        try:
            datos, _ = json.JSONDecoder().raw_decode(texto[inicio:])
        except ValueError as exc:
            raise OllamaError("Ollama devolvió JSON inválido. Se requiere repetir el análisis.") from exc
    return validar_analisis(datos)


def analizar_con_ollama(contexto):
    config = _configuracion(contexto.get('modelo_solicitado'))
    mensajes = construir_mensajes(contexto)
    # Repetir solo errores de formato; un timeout no provoca otra espera completa.
    for intento in range(2):
        solicitud = {
            "model": config["modelo"], "messages": mensajes,
            "stream": False, "format": construir_esquema(contexto),
            "options": {"temperature": 0, "num_predict": 5200, "num_ctx": 12288},
            "keep_alive": "10m",
        }
        if config['modelo'].split(':')[0] in ('qwen3', 'qwen3.5'):
            # Evitar que el presupuesto se consuma en razonamiento previo al JSON.
            solicitud['think'] = False
            solicitud['options'].update(temperature=0.2, presence_penalty=0,
                                        num_predict=3600)
        respuesta = _solicitar("POST", "/api/chat", config, json=solicitud)
        try:
            if not isinstance(respuesta, dict) or respuesta.get("done") is False:
                raise OllamaError("Ollama devolvió una respuesta incompleta.")
            if respuesta.get("done_reason") == "length":
                raise OllamaError("Ollama alcanzó el límite de generación sin completar el análisis.")
            mensaje = respuesta.get("message")
            if not isinstance(mensaje, dict):
                raise OllamaError("Ollama devolvió una respuesta sin mensaje válido.")
            try:
                analisis = recuperar_analisis(mensaje.get("content"))
                descripcion = " ".join(contexto.get("descripcion", "").casefold().split())
                for riesgo in analisis['riesgos_identificados']:
                    evidencia = " ".join(riesgo['evidencia'].casefold().split())
                    if len(evidencia) < 8 or evidencia not in descripcion:
                        raise OllamaError("Un riesgo contiene evidencia que no aparece literalmente en el escenario: "
                                          + json.dumps(riesgo['evidencia'], ensure_ascii=False)
                                          + ". Copia un tramo continuo del escenario, sin resumirlo ni añadir palabras.")
                return analisis
            except OllamaError as error_detallado:
                if not intento:
                    raise
                try:
                    return recuperar_informe_breve(mensaje.get("content"), contexto)
                except OllamaError:
                    raise error_detallado
        except OllamaError as exc:
            if intento:
                raise OllamaError(f"No se obtuvo un análisis válido tras dos intentos: {exc}") from exc
            # Reparar el contrato conservando las fuentes; no degradar a un informe sin RAG.
            mensajes = construir_mensajes(contexto) + [{
                'role': 'user',
                'content': "Repite el análisis detallado. El intento anterior falló: " + str(exc)
                    + " Usa evidencia literal del escenario, todos los campos del contrato y listas vacías"
                    + " cuando no haya sustento. Mantén las fuentes anteriores. Evita repeticiones."
            }]


def recuperar_informe_breve(texto, contexto):
    if not isinstance(texto, str):
        raise OllamaError('El informe breve no contiene texto.')
    try:
        inicio = texto.find('{')
        if inicio < 0:
            raise ValueError('Sin JSON')
        datos, _ = json.JSONDecoder().raw_decode(texto[inicio:])
    except ValueError as exc:
        raise OllamaError('El informe breve no contiene JSON válido.') from exc
    datos = _validar_campo(datos, ESQUEMA_BREVE, 'informe breve')
    riesgos = []
    for item in datos['riesgos']:
        if item['evidencia'].casefold() not in contexto.get('descripcion', '').casefold():
            raise OllamaError('El informe breve contiene un hecho no presente en el escenario.')
        riesgos.append(dict(riesgo=item['riesgo'], evidencia=item['evidencia'],
                            explicacion='Desarrollo en la justificación del informe breve.',
                            medida_concreta=item['medida']))
    return dict(riesgos_identificados=riesgos, consecuencias=[], justificacion=datos['informe'],
                recomendaciones=[i['medida'] for i in datos['riesgos']],
                opinion_llm=None,
                referencias_iso=[], referencias_ley=[], indicadores_riesgo=[], formato_ia='breve')



def consultar_estado():
    """Comprueba servicio y modelo instalado; no genera texto ni carga el modelo."""
    modelo = obtener_modelo()
    try:
        config = _configuracion()
        datos = _solicitar("GET", "/api/tags", config)
        if not isinstance(datos, dict) or not isinstance(datos.get("models"), list):
            raise OllamaError("Ollama devolvió una lista de modelos inválida.")
        nombre = modelo if ":" in modelo.rsplit("/", 1)[-1] else modelo + ":latest"
        instalado = any(isinstance(x, dict) and nombre in (x.get("name"), x.get("model")) for x in datos["models"])
        modelos = sorted({x.get("name") or x.get("model") for x in datos["models"]
                          if isinstance(x, dict) and isinstance(x.get("name") or x.get("model"), str)})
        mensaje = "Ollama disponible; modelo instalado." if instalado else (
            f"El modelo no está instalado. Ejecuta manualmente: ollama pull {modelo}."
        )
        return {"ollama": instalado, "servicio_disponible": True, "modelo": modelo,
                "skill": "evaluar_riesgo", "mensaje": mensaje, "modelos_instalados": modelos,
                "timeout_segundos": config["timeout"]}
    except OllamaError as exc:
        return {"ollama": False, "servicio_disponible": False, "modelo": modelo,
                "skill": "evaluar_riesgo", "mensaje": str(exc)}
