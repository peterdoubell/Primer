'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const fixture=JSON.parse(fs.readFileSync(0,'utf8')),url=new URL(fixture.url);assert.equal(url.hostname,'127.0.0.1');assert.equal(url.protocol,'http:');
const ROOT=path.resolve(__dirname,'..'),OUT=path.join(ROOT,'docs/algebra-functions-review-20261027/reader');fs.mkdirSync(OUT,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),auth={Authorization:'Basic '+Buffer.from(fixture.username+':'+fixture.password).toString('base64')};
const ids=['math.3.linear','math.3.slope','math.3.quadratics','math.3.polynomials'];
const files=['web/algebra-functions-core.js','web/algebra-functions-lab.js','web/algebra-functions-lab.css','web/algebra-functions-spatial.js','web/spatial-models.js','web/spatial-module-objects.js','web/lesson-state.js','web/lesson-models.js','web/index.html','primer/server.py','primer/curriculum.py','data/curriculum/01-mathematics.json','data/module-models.json','tools/check_algebra_functions_reader.py','tools/check_algebra_functions_reader.cjs'];
async function inspect(lab,companion){
 const result=await lab.evaluate(e=>{
  const api=e.algebraFunctions,state=api.getState(),model=api.getModel(),scene=api.getScene(),svg=e.querySelector('[data-algebra-graph]'),b=scene.bounds;const viewport=e.querySelector('.algebra-viewport');if(!e.classList.contains('algebra-enlarged')&&viewport.scrollHeight>viewport.clientHeight+1)throw Error('Standard graph is vertically clipped');
  const gain=620/Math.max(b.xmax-b.xmin,b.ymax-b.ymin),cx=(b.xmin+b.xmax)/2,cy=(b.ymin+b.ymax)/2;
  const X=x=>405+(x-cx)*gain,Y=y=>365-(y-cy)*gain,tolerance=Math.max(1e-7,16*Number.EPSILON*Math.max(1,Math.abs(cx),Math.abs(cy))*gain);
  let vertices=0;function near(a,z){if(Math.abs(a-z)>tolerance)throw Error('Rendered coordinate differs: '+a+' / '+z+' tolerance '+tolerance);vertices++;}
  const paths=[...svg.querySelectorAll('[data-algebra-curve]')];let expectedPaths=0;
  for(const curve of scene.curves)for(let i=0;i<curve.paths.length;i++){
   expectedPaths++;const element=paths.find(n=>n.dataset.algebraCurve===curve.id&&Number(n.dataset.pathIndex)===i);if(!element)throw Error('Curve path missing');
   const values=element.getAttribute('d').match(/[-+]?(?:\d*\.)?\d+(?:e[-+]?\d+)?/gi).map(Number),p=curve.paths[i];if(values.length!==p.length*2)throw Error('Wrong curve coordinate count');
   p.forEach((v,j)=>{near(values[j*2],X(v[0]));near(values[j*2+1],Y(v[1]));});
  }
  if(paths.length!==expectedPaths)throw Error('Unexpected curve path');
  for(const line of scene.lines.filter(l=>l.segment)){
   const element=[...svg.querySelectorAll('[data-algebra-line]')].find(n=>n.dataset.algebraLine===line.id);if(!element)throw Error('Line missing');const[a,z]=line.segment;near(+element.getAttribute('x1'),X(a[0]));near(+element.getAttribute('y1'),Y(a[1]));near(+element.getAttribute('x2'),X(z[0]));near(+element.getAttribute('y2'),Y(z[1]));if(element.getAttribute('stroke-linecap')!=='round')throw Error('Closed-window point contacts need visible caps');
  }
  for(const point of scene.markerGroups){const element=[...svg.querySelectorAll('[data-algebra-point]')].find(n=>n.dataset.algebraPoint===point.pointIds.join('|'));if(!element)throw Error('Point missing');near(+element.getAttribute('cx'),X(point.x));near(+element.getAttribute('cy'),Y(point.y));}
  for(const axis of ['x','y']){const ticks=[...svg.querySelectorAll('[data-algebra-tick='+axis+']')];if(ticks.length!==5||new Set(ticks.map(n=>n.textContent)).size!==5)throw Error('Axis ticks are not distinct');for(const tick of ticks){const factor=Number(svg.dataset.tickFactor),offset=Number(svg.getAttribute('data-offset-'+axis)),actual=Number(tick.dataset.coordinate),scaled=(actual-offset)/factor,shown=Number(tick.textContent),bound=scaled===0?0:.500001*10**(Math.floor(Math.log10(Math.abs(scaled)))-2);if(Math.abs(scaled-shown)>bound+1e-13)throw Error('Axis multiplier/offset is inconsistent');}}
  for(const text of svg.querySelectorAll('text')){const box=text.getBBox();if(box.x < -.01||box.x+box.width>770.01||box.y < -.01||box.y+box.height>755.01)throw Error('Graph annotation leaves its canvas: '+text.textContent+' '+JSON.stringify({x:box.x,y:box.y,w:box.width,h:box.height}));}
  const expected=window.PrimerSpatial.build('module.'+model.lessonId,state),spatial=document.querySelector('[data-scenario="module.'+model.lessonId+'"]');
  if(!spatial||spatial.querySelector('.spatial-readout').textContent!==expected.readout||spatial.querySelector('.spatial-note').textContent!==expected.note)throw Error('Linked3D state differs from the accepted workbench');
  const fieldTable=[...e.querySelectorAll('table')].at(-1)?.textContent||'';for(const p of scene.points)if(p.exact&&(!fieldTable.includes(p.xText)||!fieldTable.includes(p.yText)))throw Error('Exact special-point coordinates absent');
  return{state,modelKind:model.kind,summary:model.summary,vertices,curves:scene.curves.length,lines:scene.lines.length,markers:scene.points.length,bounds:b,view:api.getView(),speech:e.getModelSpeech(),overflow:document.documentElement.scrollWidth>innerWidth+1,exactPointTable:true,distinctTicks:true,linked:true};
 });assert(!result.overflow);return result;
}
(async()=>{const browser=await chromium.launch({headless:true});const proof={allPassed:false,syntheticLoopback:true,productionVerified:false,profileAge:15,errors:[],cases:[],sourceSHA256:Object.fromEntries(files.map(n=>[n,sha(fs.readFileSync(path.join(ROOT,n)))]))};try{
 const scope=JSON.parse(fs.readFileSync(path.join(ROOT,'docs/algebra-functions-review-20261027/initial-scope.json'))),current=JSON.parse(fs.readFileSync(path.join(ROOT,'data/curriculum/01-mathematics.json'))).nodes;
 for(const n of scope.originalNodes){const now=current.find(x=>x.id===n.id);for(const k of ['quiz','prereqs','practice'])assert.deepEqual(now[k],n[k]);assert.deepEqual(now.lesson_media[0],n.lesson_media[0]);}
 for(const width of [390,1440])for(const id of ids){
  const context=await browser.newContext({viewport:{width,height:1100}});await context.route(url.origin+'/**',r=>r.continue({headers:{...r.request().headers(),...auth}}));
  assert.equal((await context.request.post(url.origin+'/api/profile',{headers:{...auth,Origin:url.origin},data:{name:'Synthetic linked algebra QA',age:15,domains:['math']}})).status(),200);
  assert.equal((await context.request.post(url.origin+'/api/profile/settings',{headers:{...auth,Origin:url.origin},data:{speak:false}})).status(),200);
  const page=await context.newPage();page.on('pageerror',e=>proof.errors.push(e.message));await page.goto(url.origin+'/app/#/node/'+id);
  const lab=page.locator('[data-algebra-lesson="'+id+'"]'),companion=page.locator('[data-scenario="module.'+id+'"]');await lab.waitFor();await companion.waitFor();
  assert(await page.locator('img[src*="'+id.replaceAll('.','-')+'-"]').first().evaluate(e=>e.complete&&e.naturalWidth>0));
  const cases=[],poses=[];const presets=await lab.locator('[data-algebra-presets] option').evaluateAll(nodes=>nodes.map(n=>n.value).filter(Boolean));
  for(const preset of presets){await lab.locator('[data-algebra-presets]').selectOption(preset);cases.push({preset,...await inspect(lab,companion)});}
  await lab.locator('[data-algebra-reset]').click();const before=await inspect(lab,companion),input=lab.locator('input[data-algebra-field]').first(),key=await input.getAttribute('data-algebra-field');
  await input.fill('not-a-number');await input.press('Enter');assert.equal(await input.getAttribute('aria-invalid'),'true');assert.deepEqual(await lab.evaluate(e=>e.algebraFunctions.getState()),before.state);assert.equal(await lab.evaluate(e=>e.getModelSpeech()),before.speech);await input.press('Escape');assert.equal(await input.getAttribute('aria-invalid'),null);
  await input.fill('2');await input.press('Enter');assert.equal(await page.evaluate(()=>document.activeElement?.dataset.algebraField),key);await inspect(lab,companion);
  const accepted=await lab.evaluate(e=>e.algebraFunctions.getState());for(const name of ['Reset view','Rotate left','Rotate right','Tilt up','Tilt down','Zoom in','Zoom out']){await companion.getByRole('button',{name,exact:true}).click();assert.deepEqual(await lab.evaluate(e=>e.algebraFunctions.getState()),accepted);poses.push({name,...await inspect(lab,companion)});}
  await companion.getByRole('button',{name:'Reset model',exact:true}).click();assert.deepEqual(await lab.evaluate(e=>e.algebraFunctions.getModel().state),await page.evaluate(id=>PrimerAlgebraFunctionsCore.model(id,{}).state,id));await inspect(lab,companion);
  if(id==='math.3.quadratics'){
   await lab.evaluate(e=>e.setModelState({a:'1/1000',b:'1000',c:'1/1000'}));await lab.locator('[data-algebra-view-control=focus]').selectOption('root1');const radius=lab.locator('[data-algebra-view-control=radius]');await radius.fill('1e-12');await radius.press('Enter');cases.push({preset:'tiny-root-focus',...await inspect(lab,companion)});assert((await lab.locator('[data-algebra-axis-origin]').innerText()).includes('Δx'));
   const focus=await lab.evaluate(e=>e.algebraFunctions.getState());await radius.fill('0');await radius.press('Enter');assert.equal(await radius.getAttribute('aria-invalid'),'true');assert.deepEqual(await lab.evaluate(e=>e.algebraFunctions.getState()),focus);await radius.press('Escape');
   await lab.locator('.algebra-plot-panel').screenshot({path:path.join(OUT,width+'-focused-root.png')});
   const graph=lab.locator('.algebra-viewport');await graph.evaluate(e=>window.scrollBy(0,e.getBoundingClientRect().top-150));await graph.screenshot({path:path.join(OUT,width+'-focused-graph.png')});
   const pointTable=lab.locator('.algebra-point-table').locator('..');await pointTable.evaluate(e=>{e.scrollLeft=0;window.scrollBy(0,e.getBoundingClientRect().top-150);});await pointTable.screenshot({path:path.join(OUT,width+'-focused-table-left.png')});await pointTable.evaluate(e=>{e.scrollLeft=e.scrollWidth-e.clientWidth;});await pointTable.screenshot({path:path.join(OUT,width+'-focused-table-right.png')});
  }
  const previous=await lab.evaluate(e=>e.algebraFunctions.getState());await lab.locator('[data-algebra-enlarge]').click();assert.deepEqual(await lab.evaluate(e=>e.algebraFunctions.getState()),previous);const viewport=lab.locator('.algebra-viewport');await viewport.focus();await viewport.press('ArrowRight');await page.waitForFunction(el=>el.scrollLeft>0,await viewport.elementHandle());await lab.locator('[data-algebra-enlarge]').click();
  if(width===390){const table=lab.locator('.algebra-table-scroll').first();await table.focus();await table.press('ArrowRight');await page.waitForFunction(el=>el.scrollLeft>0,await table.elementHandle());}
  await lab.locator('[data-algebra-reset]').click();await lab.screenshot({path:path.join(OUT,width+'-'+id+'-workbench.png')});const fullGraph=lab.locator('.algebra-viewport');await fullGraph.evaluate(e=>window.scrollBy(0,e.getBoundingClientRect().top-150));await fullGraph.screenshot({path:path.join(OUT,width+'-'+id+'-complete-graph.png')});await companion.screenshot({path:path.join(OUT,width+'-'+id+'-spatial.png')});
  proof.cases.push({width,lesson:id,states:cases,poses,originalIllustrationLoaded:true,assessmentsPreserved:true,invalidDraftPreservesBothViews:true,acceptedEditRetainsFocus:true,modelResetSynchronizesBothViews:true,cameraPreservesAcceptedState:true,keyboardHorizontalScroll:true});fs.writeFileSync(path.join(OUT,'proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify({lesson:id,width,states:cases.length}));await context.close();
 }
 assert.deepEqual(proof.errors,[]);for(const [file,digest]of Object.entries(proof.sourceSHA256))assert.equal(sha(fs.readFileSync(path.join(ROOT,file))),digest,'Source changed during browser verification: '+file);
 proof.allPassed=true;fs.writeFileSync(path.join(OUT,'proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify({allPassed:true,lessons:4,cases:proof.cases.length,states:proof.cases.reduce((n,c)=>n+c.states.length,0)}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
