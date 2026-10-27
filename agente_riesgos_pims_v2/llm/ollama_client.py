"""Cliente HTTP de Ollama. No instala, descarga ni ejecuta modelos."""
import json
import logging

import requests

from config import obtener_configuracion, obtener_modelo
from prompts.riesgo_prompt import ESQUEMA_ANALISIS, construir_esquema, construir_mensajes

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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
        if not isinstance(valor, list) or ('maxItems' in esquema and len(valor) > esquema['maxItems']):
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


def validar_vinculos_documentales(analisis, contexto):
    """Pide reparación antes de que el reporte pierda citas inválidas al filtrarse."""
    riesgos = {r['riesgo'] for r in analisis['riesgos_identificados']}
    descripcion = ' '.join(contexto.get('descripcion', '').casefold().split())
    for campo, origen, identificador, clave, cita_campo, maximo in (
            ('referencias_rag', 'contexto_rag', 'fuente_id', 'id', 'cita', 240),
            ('referencias_ley', 'contexto_legal', 'articulo', 'articulo', 'cita_normativa', 160),
            ('referencias_iso', 'contexto_documental', 'control', 'control', 'cita_normativa', 160)):
        fuentes = {f[clave]: f for f in contexto.get(origen, {}).get('fragmentos', [])}
        for ref in analisis.get(campo, []):
            fuente = fuentes.get(ref[identificador])
            cita = ' '.join(ref[cita_campo].split())
            evidencia = ' '.join(ref['evidencia'].casefold().split())
            motivo = None
            if not fuente:
                motivo = 'fuente no recuperada'
            elif not 20 <= len(cita) <= maximo or cita not in ' '.join(fuente['texto'].split()):
                motivo = 'la cita no pertenece a la fuente o tiene una longitud inválida'
            elif ref['riesgo'] not in riesgos:
                motivo = 'el nombre del riesgo no coincide con los riesgos identificados'
            elif len(evidencia) < 8 or evidencia not in descripcion:
                motivo = 'la evidencia no es literal del escenario'
            if motivo:
                raise OllamaError(f"Referencia inválida en {campo}: {ref[identificador]}. "
                                  f"Motivo: {motivo}. "
                                  "Selecciona una cita literal de ESA fuente y usa el nombre exacto "
                                  "del riesgo y evidencia literal del escenario; omítela si no aplica.")


def analizar_con_ollama(contexto):
    config = _configuracion(contexto.get('modelo_solicitado'))
    mensajes = construir_mensajes(contexto)
    # Repetir solo errores de formato; un timeout no provoca otra espera completa.
    for intento in range(2):
        logger.info('Generando análisis con %s (intento %s/2).', config['modelo'], intento + 1)
        solicitud = {
            "model": config["modelo"], "messages": mensajes,
            "stream": False, "format": construir_esquema(contexto),
            "options": {"temperature": 0, "num_predict": config["num_predict"], "num_ctx": config["num_ctx"]},
            "keep_alive": "10m",
        }
        if config['modelo'].split(':')[0] in ('qwen3', 'qwen3.5'):
            # Evitar que el presupuesto se consuma en razonamiento previo al JSON.
            solicitud['think'] = False
            solicitud['options'].update(temperature=0.2, presence_penalty=0)
        respuesta = _solicitar("POST", "/api/chat", config, json=solicitud)
        try:
            if not isinstance(respuesta, dict) or respuesta.get("done") is False:
                raise OllamaError("Ollama devolvió una respuesta incompleta.")
            if respuesta.get("done_reason") == "length":
                raise OllamaError("Ollama alcanzó el límite de generación sin completar el análisis.")
            mensaje = respuesta.get("message")
            if not isinstance(mensaje, dict):
                raise OllamaError("Ollama devolvió una respuesta sin mensaje válido.")
            analisis = recuperar_analisis(mensaje.get("content"))
            descripcion = " ".join(contexto.get("descripcion", "").casefold().split())
            for riesgo in analisis['riesgos_identificados']:
                evidencia = " ".join(riesgo['evidencia'].casefold().split())
                if len(evidencia) < 8 or evidencia not in descripcion:
                    raise OllamaError("Un riesgo contiene evidencia que no aparece literalmente en el escenario: "
                                      + json.dumps(riesgo['evidencia'], ensure_ascii=False)
                                      + ". Copia un tramo continuo del escenario, sin resumirlo ni añadir palabras.")
            validar_vinculos_documentales(analisis, contexto)
            return analisis
        except OllamaError as exc:
            logger.warning('El intento %s no superó la validación: %s', intento + 1, exc)
            if intento:
                raise OllamaError(f"No se obtuvo un análisis válido tras dos intentos: {exc}") from exc
            # Reparar el contrato conservando las fuentes; no degradar a un informe sin RAG.
            mensajes = construir_mensajes(contexto) + [{
                'role': 'user',
                'content': "Repite el análisis detallado. El intento anterior falló: " + str(exc)
                    + " Usa evidencia literal del escenario, todos los campos del contrato y listas vacías"
                    + " cuando no haya sustento. Mantén las fuentes anteriores. Evita repeticiones."
            }]


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
