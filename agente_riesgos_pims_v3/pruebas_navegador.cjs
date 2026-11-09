const {chromium} = require('playwright');
const fs = require('fs');
const base=process.env.PIMS_LAB_URL || 'http://127.0.0.1:8180';
const destino=require('path').join(__dirname,'datos');
const assert=(cond,m)=>{if(!cond) throw new Error(m);};
(async()=>{
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errores=[];page.on('pageerror',e=>errores.push(e.message));
 let original=null, evaluacion=null;
 try {
  await page.goto(base,{waitUntil:'networkidle'});
  await page.getByRole('tab',{name:'04 · Historial y comparación'}).click();
  await page.getByRole('button',{name:'Abrir evaluación'}).first().waitFor();
  const lista=await (await page.request.get(base+'/api/experimento/evaluaciones')).json();
  evaluacion=lista.evaluaciones[0].id;
  const detalle=await (await page.request.get(base+'/api/experimento/evaluaciones/'+evaluacion)).json();
  original=detalle.planes[0];
  await page.getByRole('button',{name:'Abrir evaluación'}).first().click();
  await page.getByRole('button',{name:'Editar plan R-01',exact:true}).waitFor();
  await page.locator('.tabla-tratamiento').evaluate(el=>el.scrollIntoView({block:'start'}));
  await page.screenshot({path:destino+'/tabla_escritorio.png'});
  await page.getByRole('button',{name:'Editar plan R-01',exact:true}).click();
  await page.locator('#plan-responsable').fill('Equipo de ensayo de interfaz');
  await page.locator('#plan-area').fill('Prueba experimental');
  await page.locator('#plan-fin').fill('2026-12-15');
  await page.locator('#plan-estado').selectOption('en_revision');
  const respuesta=page.waitForResponse(r=>r.url().endsWith('/api/experimento/planes/'+original.id)&&r.request().method()==='PUT');
  await page.locator('#guardar-plan').click();
  assert((await respuesta).status()===200,'No se guardó el plan');
  await page.locator('#dialogo-plan').waitFor({state:'hidden'});
  await page.reload({waitUntil:'networkidle'});
  await page.getByRole('tab',{name:'04 · Historial y comparación'}).click();
  await page.getByRole('button',{name:'Abrir evaluación'}).first().click();
  await page.getByRole('button',{name:'Editar plan R-01',exact:true}).waitFor();
  assert(await page.locator('#medidas-por-riesgo').innerText().then(t=>t.includes('Equipo de ensayo de interfaz')),'La edición no sobrevivió a la recarga');
  const actual=await (await page.request.get(base+'/api/experimento/evaluaciones/'+evaluacion)).json();
  const plan=actual.planes.find(p=>p.id===original.id);
  const restaurar=await page.request.put(base+'/api/experimento/planes/'+original.id,{data:{...original,version:plan.version}});
  assert(restaurar.status()===200,'No se restauró el plan de prueba');
  original=null;
  await page.reload({waitUntil:'networkidle'});
  await page.getByRole('tab',{name:'04 · Historial y comparación'}).click();
  await page.getByRole('button',{name:'Abrir evaluación'}).first().click();
  await page.getByRole('button',{name:'Editar plan R-01',exact:true}).waitFor();
  const descargar=page.waitForEvent('download');await page.locator('#descargar-tabla').click();
  const archivo=await descargar;await archivo.saveAs(destino+'/tabla_prueba_navegador.csv');
  const reporteBase=await (await page.request.get(base+'/api/experimento/evaluaciones/'+evaluacion+'/reporte?formato=base')).text();
  assert(reporteBase===detalle.reporte_base,'El reporte original fue modificado');
  await page.getByRole('tab',{name:'04 · Historial y comparación'}).click();
  assert(await page.locator('#panel-comparacion').isVisible(),'No aparece comparación');
  await page.locator('#panel-comparacion').scrollIntoViewIfNeeded();
  await page.screenshot({path:destino+'/comparacion_escritorio.png'});
  await page.getByRole('tab',{name:'03 · Tratamiento de riesgos'}).click();
  for(const ancho of [900,390]) {
    await page.setViewportSize({width:ancho,height:900});
    await page.locator('.tabla-tratamiento').evaluate(el=>el.scrollIntoView({block:'start'}));
    const anchos=await page.evaluate(()=>({ventana:innerWidth,contenido:document.documentElement.scrollWidth}));
    assert(anchos.contenido<=anchos.ventana,`Desbordamiento horizontal: ${JSON.stringify(anchos)}`);
    await page.screenshot({path:destino+`/tabla_${ancho}.png`});
  }
  await page.getByRole('button',{name:'Editar plan R-01',exact:true}).click();
  assert(await page.locator('#dialogo-plan').isVisible(),'No abre el editor móvil');
  await page.screenshot({path:destino+'/editor_movil.png'});
  await page.locator('#cerrar-plan').click();
  await page.getByRole('tab',{name:'04 · Historial y comparación'}).click();
  const historialAncho=await page.evaluate(()=>({ventana:innerWidth,contenido:document.documentElement.scrollWidth}));
  assert(historialAncho.contenido<=historialAncho.ventana,'Historial móvil desbordado');
  await page.locator('#lista-historial').evaluate(el=>el.scrollIntoView({block:'start'}));
  await page.screenshot({path:destino+'/historial_movil.png'});
  assert(errores.length===0,'Errores JavaScript: '+errores.join('; '));
  fs.writeFileSync(destino+'/prueba_navegador.json',JSON.stringify({correcto:true,errores,guardado_y_recarga:true,descarga_csv:true,original_intacto:true,editor_movil:true,historial_movil:true,anchos:[1440,900,390]},null,2));
  console.log('Navegador: historial, edición, persistencia al recargar, restauración, CSV, comparación y vistas 1440/900/390 correctos.');
 } finally {
  if(original&&evaluacion) {
   const d=await (await page.request.get(base+'/api/experimento/evaluaciones/'+evaluacion)).json();
   const p=d.planes.find(p=>p.id===original.id);
   if(p.version!==original.version) await page.request.put(base+'/api/experimento/planes/'+original.id,{data:{...original,version:p.version}});
  }
  await browser.close();
 }
})().catch(e=>{console.error(e);process.exit(1);});
