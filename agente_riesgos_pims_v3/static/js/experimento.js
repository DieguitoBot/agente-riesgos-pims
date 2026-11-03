let evaluacionActual = null;
let planEnEdicion = null;
const estadosPlan = {propuesto: "Propuesto", en_revision: "En revisión", aprobado: "Aprobado", en_curso: "En curso", verificado: "Verificado", descartado: "Descartado"};

async function solicitarGestion(url, opciones) {
    const r = await fetch(url, opciones);
    const datos = await r.json();
    if (!r.ok) throw new Error(datos.error || "No se pudo acceder a PIMS v3.");
    return datos;
}

function reiniciarGestion() {
    evaluacionActual = null;
    document.getElementById("acciones-experimento").hidden = true;
    document.getElementById("panel-comparacion").hidden = true;
}

async function cargarHistorial() {
    const estado = document.getElementById("estado-historial");
    const cuerpo = document.getElementById("lista-historial");
    try {
        const datos = await solicitarGestion("/api/experimento/evaluaciones");
        cuerpo.replaceChildren();
        for (const item of datos.evaluaciones) {
            const fila = document.createElement("tr");
            fila.setAttribute("role", "row");
            for (const [titulo, valor] of [["Fecha", new Date(item.creado).toLocaleString("es")], ["Escenario", item.titulo], ["Riesgos", item.riesgos]]) {
                const celda = document.createElement("td"); celda.dataset.label = titulo; celda.setAttribute("role", "cell");
                celda.textContent = valor;
                if (titulo === "Escenario") {
                    const origen = document.createElement("small"); origen.className = "origen-ensayo";
                    origen.textContent = ({referencia_aprobada: "Referencia de la versión aprobada", demostracion: "Demostración ficticia sin IA"})[item.procedencia] || "Evaluación con IA";
                    celda.appendChild(origen);
                }
                fila.appendChild(celda);
            }
            const celda = document.createElement("td"); celda.dataset.label="Acción"; celda.setAttribute("role","cell");
            const abrir = document.createElement("button"); abrir.type = "button"; abrir.textContent = "Abrir evaluación";
            abrir.addEventListener("click", async () => {
                abrir.disabled = true;
                try {
                    const detalle = await solicitarGestion(`/api/experimento/evaluaciones/${item.id}`);
                    document.getElementById("descripcion").value = detalle.resultado.descripcion;
                    document.getElementById("probabilidad").value = detalle.resultado.probabilidad;
                    document.getElementById("impacto").value = detalle.resultado.impacto;
                    document.getElementById("rol_privacidad").value = detalle.resultado.rol_privacidad;
                    document.querySelectorAll('fieldset input[type="checkbox"]').forEach(c => { c.checked = detalle.resultado.categorias.includes(c.value); });
                    presentarResultado({...detalle.resultado, experimento_id: item.id});
                    cambiarPestana("medidas", true);
                } catch (error) { estado.textContent = error.message; }
                finally { abrir.disabled = false; }
            });
            celda.appendChild(abrir); fila.appendChild(celda); cuerpo.appendChild(fila);
        }
        estado.textContent = datos.evaluaciones.length ? `${datos.evaluaciones.length} evaluaciones guardadas.` : "Todavía no hay evaluaciones. Genera un análisis para iniciar la comparación.";
    } catch (error) { estado.textContent = error.message; }
}

async function cargarEvaluacionActual(id) {
    if (!id) return;
    try {
        const detalle = await solicitarGestion(`/api/experimento/evaluaciones/${id}`);
        if (ultimoResultado?.experimento_id !== id) return;
        evaluacionActual = detalle;
        document.getElementById("acciones-experimento").hidden = false;
        document.getElementById("evaluacion-guardada").textContent = `Evaluación guardada · ${new Date(detalle.creado).toLocaleString("es")}`;
        for (const [elemento, formato] of [["descargar-tabla","csv"],["descargar-experimental","txt"],["descargar-base","base"]]) {
            document.getElementById(elemento).href = `/api/experimento/evaluaciones/${id}/reporte?formato=${formato}`;
        }
        enriquecerPlanes(); mostrarComparacion(detalle);
    } catch (error) {
        errorBox.textContent = error.message; errorBox.classList.remove("oculto");
    }
}

function enriquecerPlanes() {
    if (!evaluacionActual || ultimoResultado?.experimento_id !== evaluacionActual.id) return;
    for (const fila of document.getElementById("medidas-por-riesgo").children) {
        const codigo = fila.querySelector(".tratamiento-codigo")?.textContent;
        const plan = evaluacionActual.planes.find(p => p.codigo === codigo);
        if (!plan) continue;
        const celdas = fila.children;
        celdas[1].replaceChildren(); parrafo(celdas[1], plan.medida);
        celdas[2].replaceChildren(); parrafo(celdas[2], plan.verificacion);
        celdas[3].replaceChildren();
        const estado = document.createElement("span"); estado.className = "tratamiento-estado";
        estado.dataset.estado = plan.estado; estado.textContent = estadosPlan[plan.estado]; celdas[3].appendChild(estado);
        for (const texto of [`Responsable: ${plan.responsable || "por asignar"}`, `Plazo: ${plan.fecha_fin || "por acordar"}`, `${plan.actividades.filter(a => a.completada).length}/${plan.actividades.length} actividades completadas`,
             plan.probabilidad_residual !== null ? `Residual: ${plan.probabilidad_residual * plan.impacto_residual}/25` : "Residual: pendiente de reevaluación"]) {
            const p = document.createElement("p"); p.className = "detalle-seguimiento"; p.textContent = texto; celdas[3].appendChild(p);
        }
        celdas[0].querySelector(".fuentes-plan")?.remove();
        const fuentes = document.createElement("p"); fuentes.className = "fuentes-plan";
        fuentes.textContent = "Fuentes cotejadas: " + (plan.referencias.map(r => `${r.tipo} ${r.codigo}`).join(" · ") || "sin relación verificada");
        celdas[0].appendChild(fuentes);
        const editar = document.createElement("button"); editar.type = "button"; editar.className = "editar-plan";
        editar.textContent = "Editar plan"; editar.setAttribute("aria-label", `Editar plan ${codigo}`);
        editar.addEventListener("click", () => abrirPlan(plan)); celdas[3].appendChild(editar);
    }
}

function mostrarComparacion(detalle) {
    const c = detalle.comparacion;
    const tabla = document.createElement("table");
    const cabecera = document.createElement("thead"); const titulos = document.createElement("tr");
    for (const texto of ["Aspecto", "Reporte original", "PIMS v3"]) {
        const th = document.createElement("th"); th.scope = "col"; th.textContent = texto; titulos.appendChild(th);
    }
    cabecera.appendChild(titulos); tabla.appendChild(cabecera);
    const cuerpo = document.createElement("tbody");
    for (const valores of [
        ["Riesgos identificados", c.riesgos, c.riesgos],
        ["Citas verificadas", Object.values(c.referencias_verificadas).reduce((a,b) => a+b,0), "Las mismas, vinculadas a cada plan"],
        ["Evaluación recuperable al recargar", "No", "Sí"],
        ["Actividades del plan", "Sin registro persistente", c.actividades],
        ["Responsables asignados", "Sin seguimiento", `${c.con_responsable}/${c.riesgos}`],
        ["Plazos acordados", "Sin seguimiento", `${c.con_plazo}/${c.riesgos}`],
        ["Planes verificados con evidencia", "Sin seguimiento", `${c.verificados}/${c.riesgos}`],
        ["Alertas del análisis", c.alertas_ia.length, "Se conservan para revisión"]
    ]) {
        const fila = document.createElement("tr"); valores.forEach((valor,i) => {
            const celda = document.createElement(i ? "td" : "th"); if (!i) celda.scope="row";
            celda.textContent = valor; fila.appendChild(celda);
        }); cuerpo.appendChild(fila);
    }
    tabla.appendChild(cuerpo); document.getElementById("metricas-comparacion").replaceChildren(tabla);
    document.getElementById("panel-comparacion").hidden = false;
}

function agregarActividad(actividad = {}) {
    const fila = document.createElement("div"); fila.className = "actividad-plan";
    for (const [campo,titulo,tipo] of [["descripcion","Descripción","textarea"],["responsable","Responsable","text"],["fecha_fin","Plazo","date"]]) {
        const label = document.createElement("label"); label.textContent = titulo;
        const input = document.createElement(tipo === "textarea" ? "textarea" : "input");
        if (tipo !== "textarea") input.type = tipo;
        input.dataset.campo = campo; input.value = actividad[campo] || "";
        if (campo === "descripcion") { input.required=true; input.maxLength=3000; }
        if (campo === "responsable") input.maxLength=160;
        label.appendChild(input); fila.appendChild(label);
    }
    const label = document.createElement("label"); const check = document.createElement("input");
    check.type="checkbox"; check.dataset.campo="completada"; check.checked=!!actividad.completada;
    label.append(check, document.createTextNode("Actividad completada")); fila.appendChild(label);
    const quitar = document.createElement("button"); quitar.type="button"; quitar.className="boton-secundario";
    quitar.textContent="Quitar actividad"; quitar.addEventListener("click", () => fila.remove()); fila.appendChild(quitar);
    document.getElementById("lista-actividades").appendChild(fila);
}

function abrirPlan(plan) {
    planEnEdicion = plan;
    document.getElementById("titulo-editar-plan").textContent = `Editar ${plan.codigo}`;
    document.getElementById("nombre-riesgo-plan").textContent = plan.riesgo;
    const campos={responsable:"responsable",area:"area",inicio:"fecha_inicio",fin:"fecha_fin",estado:"estado",medida:"medida",verificacion:"verificacion",evidencia:"evidencia_verificacion",verificador:"verificado_por","fecha-verificacion":"fecha_verificacion",probabilidad:"probabilidad_residual",impacto:"impacto_residual"};
    for (const [id,campo] of Object.entries(campos)) document.getElementById(`plan-${id}`).value=plan[campo] ?? "";
    document.getElementById("lista-actividades").replaceChildren(); plan.actividades.forEach(agregarActividad);
    document.getElementById("error-plan").textContent="";
    document.getElementById("dialogo-plan").showModal();
}

document.getElementById("form-plan").addEventListener("submit", async evento => {
    evento.preventDefault();
    const boton=document.getElementById("guardar-plan"); boton.disabled=true;
    const datos={version:planEnEdicion.version, actividades:[]};
    const campos={responsable:"responsable",area:"area",inicio:"fecha_inicio",fin:"fecha_fin",estado:"estado",medida:"medida",verificacion:"verificacion",evidencia:"evidencia_verificacion",verificador:"verificado_por","fecha-verificacion":"fecha_verificacion"};
    for (const [id,campo] of Object.entries(campos)) datos[campo]=document.getElementById(`plan-${id}`).value;
    for (const [id,campo] of [["probabilidad","probabilidad_residual"],["impacto","impacto_residual"]]) {
        const valor=document.getElementById(`plan-${id}`).value; datos[campo]=valor ? Number(valor) : null;
    }
    for (const fila of document.querySelectorAll(".actividad-plan")) {
        const actividad={}; fila.querySelectorAll("[data-campo]").forEach(input => { actividad[input.dataset.campo]=input.type === "checkbox" ? input.checked : input.value; });
        datos.actividades.push(actividad);
    }
    try {
        await solicitarGestion(`/api/experimento/planes/${planEnEdicion.id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(datos)});
        document.getElementById("dialogo-plan").close(); await cargarEvaluacionActual(evaluacionActual.id);
    } catch (error) { document.getElementById("error-plan").textContent=error.message; }
    finally { boton.disabled=false; }
});
document.getElementById("agregar-actividad").addEventListener("click",() => agregarActividad());
document.getElementById("cerrar-plan").addEventListener("click",() => document.getElementById("dialogo-plan").close());
document.getElementById("recargar-historial").addEventListener("click",cargarHistorial);
void cargarHistorial();
