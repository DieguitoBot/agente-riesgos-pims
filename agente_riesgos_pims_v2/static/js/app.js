const form = document.getElementById("formRiesgo");
const resultado = document.getElementById("resultado");
let ultimoResultado = null;
const errorBox = document.getElementById("error");

function listaSeleccionada() {
    return [...document.querySelectorAll('fieldset input[type="checkbox"]:checked')]
        .map(item => item.value);
}

function llenarLista(id, elementos) {
    const lista = document.getElementById(id);
    lista.innerHTML = "";

    elementos.forEach(texto => {
        const li = document.createElement("li");
        li.textContent = texto;
        lista.appendChild(li);
    });
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    reiniciarResumen();
    cambiarPestana("evaluacion");
    ultimoResultado = null;
    document.getElementById("exportar-reporte").disabled = true;
    resultado.classList.add("oculto");
    errorBox.classList.add("oculto");

    const boton = form.querySelector('button[type="submit"]');
    boton.disabled = true;
    boton.textContent = "Analizando…";
    const progreso = document.getElementById("progreso-analisis");
    const inicio = Date.now();
    progreso.textContent = "Esperando el análisis completo de Ollama. La carga del modelo y la lectura de la ISO pueden tardar varios minutos.";
    const temporizador = setInterval(() => {
        progreso.textContent = `Esperando respuesta: ${Math.floor((Date.now() - inicio) / 1000)} segundos. El resultado se mostrará cuando termine el análisis.`;
    }, 1000);

    document.getElementById("modelo").disabled = true;
    const datos = {
        descripcion: document.getElementById("descripcion").value,
        probabilidad: Number(document.getElementById("probabilidad").value),
        impacto: Number(document.getElementById("impacto").value),
        categorias: listaSeleccionada(),
        rol_privacidad: document.getElementById("rol_privacidad").value,
        modelo: document.getElementById("modelo").value || null,
        exigir_ia: true
    };

    try {
        const respuesta = await fetch("/api/evaluar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });

        const contenido = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error((contenido.error || "No se pudo realizar la evaluación.") +
                (contenido.codigo === "ia_no_disponible" ? " No se generó un reporte de IA. Comprueba Ollama, selecciona otro modelo instalado o vuelve a evaluar." : ""));
        }

        document.getElementById("nivel").textContent = `Nivel ${contenido.nivel}`;
        document.getElementById("puntaje").textContent = `${contenido.puntaje}/25`;
        document.getElementById("justificacion").textContent = contenido.justificacion;
        document.getElementById("modo").textContent = contenido.llm_disponible
            ? `Reporte generado con IA: ${contenido.modelo}`
            : "Modo: Análisis local básico";
        document.getElementById("mensaje").textContent = contenido.mensaje;

        mostrarTarjetas("riesgos", contenido.analisis_ia.riesgos_identificados,
            "No se identificaron riesgos con la información disponible.", (tarjeta, item) => {
                parrafo(tarjeta, item.riesgo);
                parrafo(tarjeta, item.explicacion);
                for (const [campo, titulo] of Object.entries({evidencia: "Hecho del escenario",
                    amenaza: "Amenaza", vulnerabilidad: "Vulnerabilidad", dano_personas: "Daño posible a las personas",
                    medida_concreta: "Medida propuesta", verificacion: "Cómo verificar la medida", prioridad: "Prioridad propuesta"})) {
                    if (item[campo]) parrafo(tarjeta, `${titulo}: ${item[campo]}`);
                }
            });
        llenarLista("consecuencias", contenido.analisis_ia.consecuencias.length
            ? contenido.analisis_ia.consecuencias : ["Consulta las consecuencias descritas en la justificación del informe breve."]);
        llenarLista("recomendaciones", contenido.recomendaciones);

        mostrarComplemento(contenido);
        ultimoResultado = contenido;
        document.getElementById("exportar-reporte").disabled = false;
        const doc = contenido.documentacion_iso;
        document.getElementById("fuente-documental").textContent = doc
            ? `Documento ISO: ${doc.estado}. Secciones recuperadas: ${doc.secciones.map(s => s.seccion).join(", ") || "ninguna"}. ${doc.mensaje}` : "";
        resultado.classList.remove("oculto");
        actualizarResumen(contenido);
        cambiarPestana("resultados", true);

    } catch (error) {
        document.getElementById("resumen-estado").textContent = "Sin resultado";
        cambiarPestana("evaluacion", true);
        errorBox.textContent = error.message;
        errorBox.classList.remove("oculto");
    } finally {
        clearInterval(temporizador);
        progreso.textContent = "";
        boton.disabled = false;
        document.getElementById("modelo").disabled = false;
        boton.textContent = "Evaluar riesgo";
    }
});


function parrafo(contenedor, texto) {
    const p = document.createElement("p");
    p.textContent = texto;
    contenedor.appendChild(p);
}

function mostrarTarjetas(id, elementos, vacio, renderizar) {
    const contenedor = document.getElementById(id);
    contenedor.replaceChildren();
    if (!elementos.length) parrafo(contenedor, vacio);
    elementos.forEach(item => {
        const tarjeta = document.createElement("article");
        tarjeta.className = "detalle-riesgo";
        renderizar(tarjeta, item);
        contenedor.appendChild(tarjeta);
    });
}

function mostrarComplemento(contenido) {
    document.getElementById("estado-rag").textContent = contenido.estado_rag || "Estado de recuperación no informado.";
    mostrarTarjetas("aplicaciones-rag", contenido.referencias_rag || [],
        "El modelo no vinculó medidas con citas RAG verificables en esta evaluación.", (tarjeta, ref) => {
            parrafo(tarjeta, `${ref.fuente_id} · ${ref.riesgo}`);
            parrafo(tarjeta, `Hecho: ${ref.evidencia}`);
            parrafo(tarjeta, `Cita: “${ref.cita}”`);
            parrafo(tarjeta, `Aplicación propuesta: ${ref.aplicacion}`);
            parrafo(tarjeta, `${ref.archivo} · Página: ${ref.pagina ?? "No aplica"} · ${ref.estado}`);
        });
    mostrarTarjetas("fuentes-rag", contenido.fuentes_rag || [],
        "Esta evaluación no incluye fuentes recuperadas por RAG.", (tarjeta, fuente) => {
            parrafo(tarjeta, `${fuente.id || ""} · ${fuente.archivo || "Documento sin nombre"}`);
            if (fuente.texto) {
                const detalle = document.createElement("details");
                const titulo = document.createElement("summary");
                titulo.textContent = "Leer fragmento recuperado";
                detalle.appendChild(titulo);
                parrafo(detalle, fuente.texto);
                tarjeta.appendChild(detalle);
            }
            parrafo(tarjeta, `Página: ${fuente.pagina ?? "No indicada"} · Fragmento: ${fuente.fragmento ?? "No indicado"}`);
        });

    const ia = contenido.valoracion_ia;
    const valorada = ia && ia.puntaje !== null;
    document.getElementById("valoracion-ia").textContent = valorada
        ? `Probabilidad ${ia.probabilidad}/5 · Impacto ${ia.impacto}/5 · ${ia.puntaje}/25 · Nivel ${ia.nivel}`
        : (ia ? "Información insuficiente para proponer cifras." :
            (contenido.formato_ia === "breve" ? "Informe breve de IA sin valoración numérica." : "Opinión IA no disponible en modo básico."));
    document.getElementById("comparacion-ia").textContent = valorada
        ? (ia.coincide_con_usuario ? "La IA coincide con tu valoración."
            : `La IA propone una valoración diferente. Diferencia de puntaje: ${ia.diferencia_puntaje > 0 ? "+" : ""}${ia.diferencia_puntaje}. Tu valoración se conserva.`)
        : "";
    llenarLista("motivos-ia", ia ? [
        `Probabilidad: ${ia.justificacion_probabilidad}`, `Impacto: ${ia.justificacion_impacto}`
    ] : []);
    document.getElementById("confianza-ia").textContent = ia
        ? `Confianza declarada por el modelo: ${ia.confianza}. Estimación orientativa para revisión humana.` : "";
    llenarLista("datos-faltantes", ia ? (ia.datos_faltantes.length ? ia.datos_faltantes : ["El modelo no indicó datos adicionales."]) : [contenido.formato_ia === "breve" ? "Reintenta el análisis detallado para obtener cifras y referencias verificadas." : "Se requiere una respuesta válida de Ollama."]);
    mostrarTarjetas("indicadores", contenido.indicadores_riesgo || [],
        "No hay indicadores específicos sustentados en este análisis.", (tarjeta, item) => {
            parrafo(tarjeta, `${item.indicador} · ${item.riesgo}`);
            parrafo(tarjeta, `Indicio del escenario: “${item.evidencia}”`);
            parrafo(tarjeta, `Cálculo: ${item.formula}`);
            parrafo(tarjeta, `Fuente: ${item.fuente_datos} · Frecuencia propuesta: ${item.frecuencia}`);
            parrafo(tarjeta, `Umbral propuesto: ${item.umbral_propuesto} · Valor actual: pendiente de medición`);
        });
    mostrarTarjetas("referencias-iso", contenido.referencias_iso || [],
        "No se establecieron relaciones sustentadas con el catálogo. Esto no acredita cumplimiento.", (tarjeta, item) => {
            parrafo(tarjeta, `${item.codigo} · ${item.nombre} · Guía ${item.guia}`);
            parrafo(tarjeta, `Riesgo: ${item.riesgo} · ${item.estado}`);
            parrafo(tarjeta, `Indicio del escenario: “${item.evidencia}”`);
            parrafo(tarjeta, item.motivo);
            if (item.cita_normativa) parrafo(tarjeta, `Cita del documento: “${item.cita_normativa}”`);
            if (item.archivo) parrafo(tarjeta, `Fuente: ${item.archivo} · página OCR ${item.pagina} · línea ${item.linea}`);
            parrafo(tarjeta, `Por verificar: ${item.evidencia_requerida}`);
            parrafo(tarjeta, `Rol: ${item.rol} · ${item.aplicabilidad}`);
            const enlace = document.createElement("a");
            enlace.href = item.fuente;
            enlace.textContent = "Ver sección del Markdown utilizado";
            enlace.target = "_blank";
            enlace.rel = "noopener noreferrer";
            tarjeta.appendChild(enlace);
        });
    document.getElementById("fuente-legal").textContent = contenido.documentacion_ley
        ? `Documento legal: ${contenido.documentacion_ley.estado}. ${contenido.documentacion_ley.mensaje}` : "";
    mostrarTarjetas("referencias-ley", contenido.referencias_ley || [],
        "No se establecieron relaciones legales con sustento documental en este análisis.", (tarjeta, item) => {
            parrafo(tarjeta, `Artículo ${item.articulo} · ${item.titulo}`);
            parrafo(tarjeta, `Riesgo: ${item.riesgo} · ${item.estado}`);
            parrafo(tarjeta, `Hecho: “${item.evidencia}”`);
            parrafo(tarjeta, item.motivo);
            parrafo(tarjeta, `Cita: “${item.cita_normativa}”`);
            parrafo(tarjeta, `Por verificar: ${item.evidencia_requerida}`);
            parrafo(tarjeta, `${item.archivo} · línea ${item.linea}`);
            const enlace = document.createElement("a");
            enlace.href = item.fuente;
            enlace.textContent = "Ver artículo utilizado";
            enlace.target = "_blank";
            enlace.rel = "noopener noreferrer";
            tarjeta.appendChild(enlace);
        });
    llenarLista("avisos-revision", contenido.avisos_revision || []);
}


document.getElementById("exportar-reporte").addEventListener("click", () => {
    if (!ultimoResultado) return;
    const r = ultimoResultado;
    const texto = r.reporte_texto;
    const url = URL.createObjectURL(new Blob([texto], {type: "text/plain;charset=utf-8"}));
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = "reporte-riesgos-privacidad.txt";
    enlace.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
});


async function comprobarOllama() {
    const estado = document.getElementById("estado-ollama");
    const boton = document.getElementById("comprobar-ollama");
    boton.disabled = true;
    estado.textContent = "Comprobando conexión con Ollama…";
    const resumenServicio = document.getElementById("servicio-resumen");
    resumenServicio.textContent = "Comprobando servicio…";
    resumenServicio.dataset.estado = "pendiente";
    try {
        const respuesta = await fetch("/api/status");
        if (!respuesta.ok) throw new Error(`El servidor respondió HTTP ${respuesta.status}.`);
        const datos = await respuesta.json();
        const selector = document.getElementById("modelo");
        const seleccionado = selector.value;
        selector.replaceChildren();
        const modelos = [...new Set([datos.modelo, ...(datos.modelos_instalados || [])])].filter(Boolean);
        modelos.forEach(modelo => {
            const opcion = document.createElement("option");
            opcion.value = modelo;
            opcion.textContent = modelo;
            selector.appendChild(opcion);
        });
        selector.value = modelos.includes(seleccionado) ? seleccionado : datos.modelo;
        estado.textContent = `${datos.mensaje} Modelo configurado: ${datos.modelo}.`;
        resumenServicio.textContent = datos.ollama ? "● Ollama disponible" : "● Revisar Ollama";
        resumenServicio.dataset.estado = datos.ollama ? "activo" : "error";
        if (datos.ollama) {
            estado.textContent += ` Tiempo de espera: ${datos.timeout_segundos || "según configuración"} segundos. Servicio disponible; la generación se comprueba al evaluar.`;
        } else if (datos.servicio_disponible) {
            estado.textContent += ` Modelos instalados: ${(datos.modelos_instalados || []).join(", ") || "ninguno"}.`;
        }
    } catch (error) {
        estado.textContent = `No se pudo comprobar el estado: ${error.message}`;
        resumenServicio.textContent = "● Servicio sin verificar";
        resumenServicio.dataset.estado = "error";
    } finally {
        boton.disabled = false;
    }
}
document.getElementById("comprobar-ollama").addEventListener("click", comprobarOllama);
comprobarOllama();


// Navegación accesible con teclado y paneles independientes.
function cambiarPestana(nombre, enfocar = false) {
    document.querySelectorAll('[role="tab"]').forEach(tab => {
        const activo = tab.id === `tab-${nombre}`;
        tab.setAttribute("aria-selected", String(activo));
        tab.tabIndex = activo ? 0 : -1;
        document.getElementById(tab.getAttribute("aria-controls")).hidden = !activo;
        if (activo && enfocar) tab.focus();
    });
}
const pestanas = [...document.querySelectorAll('[role="tab"]')];
pestanas.forEach((tab, indice) => {
    tab.addEventListener("click", () => cambiarPestana(tab.id.replace("tab-", "")));
    tab.addEventListener("keydown", evento => {
        let siguiente;
        if (evento.key === "ArrowRight") siguiente = (indice + 1) % pestanas.length;
        if (evento.key === "ArrowLeft") siguiente = (indice + pestanas.length - 1) % pestanas.length;
        if (evento.key === "Home") siguiente = 0;
        if (evento.key === "End") siguiente = pestanas.length - 1;
        if (siguiente === undefined) return;
        evento.preventDefault();
        cambiarPestana(pestanas[siguiente].id.replace("tab-", ""), true);
    });
});
document.querySelectorAll("[data-ir-evaluacion]").forEach(boton => {
    boton.addEventListener("click", () => {
        cambiarPestana("evaluacion");
        document.getElementById("descripcion").focus();
    });
});

function reiniciarResumen() {
    document.getElementById("resumen-estado").textContent = "Analizando…";
    document.getElementById("resumen-nivel").textContent = "—";
    document.getElementById("resumen-puntaje").textContent = "Matriz: probabilidad × impacto";
    document.getElementById("resumen-riesgos").textContent = "—";
    document.getElementById("resumen-medidas").textContent = "—";
    document.getElementById("vacio-resultados").hidden = false;
    document.getElementById("vacio-medidas").hidden = false;
    document.getElementById("contenido-medidas").classList.add("oculto");
}

function actualizarResumen(contenido) {
    document.getElementById("resumen-estado").textContent = "Completado";
    document.getElementById("resumen-nivel").textContent = contenido.nivel;
    document.getElementById("resumen-puntaje").textContent = `${contenido.puntaje} de 25 · Tu valoración`;
    document.getElementById("resumen-riesgos").textContent = contenido.analisis_ia.riesgos_identificados.length;
    document.getElementById("resumen-medidas").textContent = contenido.recomendaciones.length;
    document.getElementById("vacio-resultados").hidden = true;
    document.getElementById("vacio-medidas").hidden = true;
    document.getElementById("contenido-medidas").classList.remove("oculto");
    document.getElementById("buscar-tratamiento").value = "";
    mostrarTratamiento();
}

function mostrarTratamiento() {
    const riesgos = ultimoResultado?.analisis_ia?.riesgos_identificados || [];
    const consulta = document.getElementById("buscar-tratamiento").value.trim().toLocaleLowerCase("es");
    const cuerpo = document.getElementById("medidas-por-riesgo");
    cuerpo.replaceChildren();
    let visibles = 0;
    riesgos.forEach((item, indice) => {
        const codigo = `R-${String(indice + 1).padStart(2, "0")}`;
        if (![codigo, item.riesgo, item.medida_concreta, item.prioridad]
            .some(valor => String(valor || "").toLocaleLowerCase("es").includes(consulta))) return;
        visibles++;
        const fila = document.createElement("tr");
        const valores = [codigo, item.riesgo, item.prioridad || "Por definir",
            item.medida_concreta || "Pendiente de definir",
            item.verificacion || "Pendiente de definir",
            item.medida_concreta ? "Propuesta · por revisar" : "Sin propuesta específica",
            "Pendiente de reevaluación"];
        valores.forEach(valor => {
            const celda = document.createElement("td");
            celda.textContent = valor;
            fila.appendChild(celda);
        });
        cuerpo.appendChild(fila);
    });
    if (!visibles) {
        const fila = document.createElement("tr");
        const celda = document.createElement("td");
        celda.colSpan = 7;
        celda.textContent = riesgos.length ? "No hay propuestas que coincidan con la búsqueda."
            : "No se identificaron riesgos para desglosar. Revisa las recomendaciones generales.";
        fila.appendChild(celda);
        cuerpo.appendChild(fila);
    }
    document.getElementById("tratamiento-conteo").textContent = `Mostrando ${visibles} de ${riesgos.length} riesgos.`;
}
document.getElementById("buscar-tratamiento").addEventListener("input", mostrarTratamiento);
