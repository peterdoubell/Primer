'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const fixture=JSON.parse(fs.readFileSync(0,'utf8')),url=new URL(fixture.url);assert.equal(url.hostname,'127.0.0.1');assert.equal(url.protocol,'http:');
const ROOT=path.resolve(__dirname,'..'),OUT=path.join(ROOT,'docs/coordinate-plane-review-20261028/reader');fs.mkdirSync(OUT,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),auth={Authorization:'Basic '+Buffer.from(fixture.username+':'+fixture.password).toString('base64')};
const files=['web/coordinate-plane-core.js','web/coordinate-plane-lab.js','web/coordinate-plane-lab.css','web/coordinate-plane-spatial.js','web/algebra-functions-core.js','web/spatial-models.js','web/spatial-module-objects.js','web/lesson-state.js','web/lesson-models.js','web/index.html','primer/server.py','primer/curriculum.py','data/curriculum/01-mathematics.json','data/module-models.json','tools/check_coordinate_plane_reader.py','tools/check_coordinate_plane_reader.cjs'];
async function inspect(lab){
 const result=await lab.evaluate(e=>{
  const scene=e.coordinatePlane.getScene(),state=scene.model.state,svg=e.querySelector('[data-coordinate-graph]'),scale=Number(svg.dataset.gain);
  const expected=PrimerSpatial.build('module.math.2.coordinates',state),spatial=document.querySelector('[data-scenario="module.math.2.coordinates"]');
  if(spatial.querySelector('.spatial-readout').textContent!==expected.readout||spatial.querySelector('.spatial-note').textContent!==expected.note)throw Error('Linked chart differs');
  for(const node of svg.querySelectorAll('[data-coordinate-marker]')){const p=scene.points.find(p=>p.id===node.dataset.coordinateMarker.split('/')[0]);if(Math.abs((+node.getAttribute('cx')-340)/scale-p.x)>1e-10||Math.abs((320-node.getAttribute('cy'))/scale-p.y)>1e-10)throw Error('Flat marker differs');}
  for(const point of scene.points)if(![...e.querySelectorAll('tbody tr')].some(row=>row.cells[1].textContent===point.label&&row.cells[2].textContent===point.xText&&row.cells[3].textContent===point.yText))throw Error('Exact table differs');
  for(const p of expected.primitives.filter(p=>p.coordinate_kind==='construction')){const segment=scene.segments.find(s=>s.id===p.segmentId);for(let i=0;i<2;i++)for(let axis=0;axis<2;axis++)if(Math.abs(p.points[i][axis]/scene.gain-[segment.from,segment.to][i][axis])>1e-10||p.points[i][2]!==0)throw Error('Spatial coordinate differs');}
  for(const text of svg.querySelectorAll('text')){const b=text.getBBox();if(b.x<0||b.y<0||b.x+b.width>680||b.y+b.height>650)throw Error('Annotation outside graph: '+text.textContent);}
  return{state,linked:true,exactPointTable:true,geometryVerified:true,primitives:expected.primitives.length,speech:e.getModelSpeech(),overflow:document.documentElement.scrollWidth>innerWidth+1};
 });assert(!result.overflow);return result;
}
(async()=>{const browser=await chromium.launch({headless:true});const proof={allPassed:false,syntheticLoopback:true,productionVerified:false,profileAge:15,errors:[],cases:[],sourceSHA256:Object.fromEntries(files.map(n=>[n,sha(fs.readFileSync(path.join(ROOT,n)))]))};try{
 const scope=JSON.parse(fs.readFileSync(path.join(ROOT,'docs/coordinate-plane-review-20261028/initial-scope.json'))),current=JSON.parse(fs.readFileSync(path.join(ROOT,'data/curriculum/01-mathematics.json'))).nodes.find(n=>n.id==='math.2.coordinates');
 assert.deepEqual(current.quiz,scope.originalNode.quiz);assert.deepEqual(current.prereqs,scope.originalNode.prereqs);assert.deepEqual(current.lesson_media[0],scope.originalNode.lesson_media[0]);
 for(const width of [390,1440]){
  const context=await browser.newContext({viewport:{width,height:1000}});await context.route(url.origin+'/**',route=>route.continue({headers:{...route.request().headers(),...auth}}));
  assert.equal((await context.request.post(url.origin+'/api/profile',{headers:{...auth,Origin:url.origin},data:{name:'Synthetic coordinate QA',age:15,domains:['math']}})).status(),200);
  assert.equal((await context.request.post(url.origin+'/api/profile/settings',{headers:{...auth,Origin:url.origin},data:{speak:false}})).status(),200);
  const page=await context.newPage();page.on('pageerror',e=>proof.errors.push(e.message));await page.goto(url.origin+'/app/#/node/math.2.coordinates');
  const lab=page.locator('.coordinate-plane-lab'),companion=page.locator('[data-scenario="module.math.2.coordinates"]');await lab.waitFor();await companion.waitFor();
  const image=page.locator('img[src*="math-2-coordinates-"]').first();await image.scrollIntoViewIfNeeded();await page.waitForFunction(e=>e.complete&&e.naturalWidth>0,await image.elementHandle());
  const states=[],poses=[];for(const id of await lab.locator('[data-coordinate-presets] option').evaluateAll(nodes=>nodes.map(n=>n.value).filter(Boolean))){await lab.locator('[data-coordinate-presets]').selectOption(id);states.push({preset:id,...await inspect(lab)});}
  const before=await inspect(lab),input=lab.locator('[data-coordinate-field=x]');await input.fill('1/0');await input.press('Enter');assert.equal(await input.getAttribute('aria-invalid'),'true');assert.deepEqual((await inspect(lab)).state,before.state);assert.equal(await lab.evaluate(e=>e.getModelSpeech()),before.speech);await input.press('Escape');
  await input.fill('1/3');await input.press('Enter');assert.equal(await page.evaluate(()=>document.activeElement.dataset.coordinateField),'x');await inspect(lab);
  const accepted=await lab.evaluate(e=>e.coordinatePlane.getState());for(const name of ['Reset view','Rotate left','Rotate right','Tilt up','Tilt down','Zoom in','Zoom out']){await companion.getByRole('button',{name,exact:true}).click();assert.deepEqual((await inspect(lab)).state,accepted);poses.push(name);}
  await companion.getByRole('button',{name:'Reset model',exact:true}).click();assert.deepEqual((await inspect(lab)).state,await page.evaluate(()=>PrimerCoordinatePlaneCore.defaults()));
  if(width===390){const table=lab.locator('.coordinate-table');await table.focus();await table.press('ArrowRight');await page.waitForFunction(e=>e.scrollLeft>0,await table.elementHandle());}
  await lab.screenshot({path:path.join(OUT,width+'-activity.png')});await companion.screenshot({path:path.join(OUT,width+'-spatial.png')});
  for(const [name,graph] of [['flat',lab.locator('.coordinate-plot')],['spatial',companion.locator('.spatial-canvas')]]){await graph.evaluate(e=>window.scrollBy(0,e.getBoundingClientRect().top-160));await graph.screenshot({path:path.join(OUT,width+'-'+name+'-graph.png')});}
  proof.cases.push({width,states,poses,originalIllustrationLoaded:true,assessmentsPreserved:true,invalidDraftPreserved:true,cameraPreservedState:true,resetSynchronized:true,keyboardTableScroll:true});console.log(JSON.stringify({width,states:states.length}));await context.close();
 }
 assert.deepEqual(proof.errors,[]);for(const[file,h]of Object.entries(proof.sourceSHA256))assert.equal(sha(fs.readFileSync(path.join(ROOT,file))),h);
 proof.allPassed=true;fs.writeFileSync(path.join(OUT,'proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify({allPassed:true,cases:proof.cases.length}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
