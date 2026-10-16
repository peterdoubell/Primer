'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require('playwright');
const {captureSnapshot,verifySnapshots}=require('./check_linear_algebra_independent.cjs');
const fixture=JSON.parse(fs.readFileSync(0,'utf8')),origin=new URL(fixture.url);
assert.equal(origin.hostname,'127.0.0.1');assert.equal(origin.protocol,'http:');assert.equal(origin.pathname,'/');
assert.equal(origin.username,'');assert.equal(origin.password,'');
const base=origin.origin,root=path.resolve(__dirname,'..'),out=path.join(root,'docs/linear-algebra-fidelity-review-20261016/reader');
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const fileHash=name=>hash(fs.readFileSync(path.join(root,name)));
const authored=JSON.parse(fs.readFileSync(path.join(root,'data/curriculum/01-mathematics.json'))).nodes.find(n=>n.id==='math.4.linalg');
const companion=authored.lesson_media.find(m=>m.renderer==='linear-algebra-lab');
const original=authored.lesson_media.filter(m=>m.renderer!=='linear-algebra-lab');
const shell=fs.readFileSync(path.join(root,'web/index.html'),'utf8');
const scriptNames=[...shell.matchAll(/<script src="\/app\/([\w-]+\.js)(?:\?[^"<>]*)?"><\/script>/g)].map(m=>m[1]);
assert.equal(scriptNames.filter(n=>n==='linear-algebra-lab.js').length,1);
const bundle=Buffer.from("'use strict';\n"+scriptNames.map(n=>fs.readFileSync(path.join(root,'web',n),'utf8')).join('\n;\n'));
const stations=['maps','systems','planes','space','kernel','spectrum','orbits'];
const matrices=[['Identity',[[1,0],[0,1]],1],['Stretch x by 2',[[2,0],[0,1]],2],['Shear x by y',[[1,1],[0,1]],1],['Reflect across x-axis',[[1,0],[0,-1]],-1],['Project onto x-axis',[[1,0],[0,0]],0]];
const near=(a,b,label)=>assert(Math.abs(a-b)<1e-8,`${label}: ${a} != ${b}`);
const signedArea=points=>points.reduce((s,p,i)=>{const q=points[(i+1)%points.length];return s+p[0]*q[1]-p[1]*q[0];},0)/2;
const value=x=>{if(typeof x==='number')return x;const [a,b]=String(x).split('/').map(Number);return a/(b===undefined?1:b);};
const vector=x=>x.map(value),dot=(a,b)=>a.reduce((v,x,i)=>v+x*b[i],0),apply=(A,v)=>A.map(r=>dot(r,v));
const approx=(a,b,label)=>assert(Math.abs(a-b)<=2e-8*Math.max(1,Math.abs(a),Math.abs(b)),`${label}: ${a} != ${b}`);
function vectorEqual(actual,expected,label){assert.equal(actual.length,expected.length,label);actual.forEach((v,i)=>approx(v,expected[i],label+' coordinate '+i));}
function verifyGeometry(snapshot){
 const state=snapshot.state,m=snapshot.activeModel,A=m.matrix?.map(vector),primitives=snapshot.plots.flatMap(p=>p.primitives);let vertices=0;
 const find=series=>{const p=primitives.find(p=>p.series===series);assert(p,'Missing rendered series '+series);return p.world;};
 for(const plot of snapshot.plots){
  const d=plot.domain;assert(d.x[1]>d.x[0]&&d.y[1]>d.y[0]);
  if(d.equalUnits)approx((d.right-d.left)/(d.x[1]-d.x[0]),(d.bottom-d.top)/(d.y[1]-d.y[0]),'equal-unit axes');
  let projection=null;
  if(plot.projection){const a=state[state.station].yaw*Math.PI/180,b=state[state.station].pitch*Math.PI/180;
   projection=[[Math.cos(a),-Math.sin(a),0],[Math.sin(b)*Math.sin(a),Math.sin(b)*Math.cos(a),Math.cos(b)]];
   for(let i=0;i<2;i++)vectorEqual(plot.projection.matrix[i],projection[i],'declared camera matrix');
  }
  for(const p of plot.primitives){assert.equal(p.world.length,p.pixels.length);
   for(let i=0;i<p.world.length;i++){
    const world=p.world[i];assert(world.every(Number.isFinite));const projected=projection?apply(projection,world):world;
    const pixel=[d.left+(projected[0]-d.x[0])/(d.x[1]-d.x[0])*(d.right-d.left),d.bottom-(projected[1]-d.y[0])/(d.y[1]-d.y[0])*(d.bottom-d.top)];
    vectorEqual(p.pixels[i],pixel,'actual SVG '+p.series);assert(pixel[0]>=d.left-1e-6&&pixel[0]<=d.right+1e-6&&pixel[1]>=d.top-1e-6&&pixel[1]<=d.bottom+1e-6,'Rendered data leaves calibrated plot');vertices++;
   }
  }
 }
 if(state.station==='maps'){
  const st=state.maps,actualA=[[value(st.a00),value(st.a01)],[value(st.a10),value(st.a11)]],B=[[value(st.b00),value(st.b01)],[value(st.b10),value(st.b11)]],x=[value(st.x),value(st.y)];
  const corners=[[0,0],[1,0],[1,1],[0,1]];find('mapped-square').forEach((p,i)=>vectorEqual(p,apply(actualA,corners[i]),'mapped unit square'));
  vectorEqual(find('output')[0],apply(actualA,x),'column sum endpoint');vectorEqual(find('AB-path')[2],apply(actualA,apply(B,x)),'AB acts B first');vectorEqual(find('BA-path')[2],apply(B,apply(actualA,x)),'BA acts A first');
 }else if(state.station==='systems'){
  for(let i=0;i<2;i++)for(const p of find('equation-'+i))approx(dot(A[i],p),value(m.rhs[i]),'general-form line');
  if(m.classification==='none')assert(!primitives.some(p=>p.series==='solution'));
  else for(let i=0;i<2;i++)approx(dot(A[i],find('solution')[0]),value(m.rhs[i]),'displayed common solution');
 }else if(state.station==='planes'){
  for(let i=0;i<3;i++)for(const p of find('plane-'+i))approx(dot(A[i],p),value(m.rhs[i]),'finite affine plane polygon');
  for(const series of ['common-line','chosen-solution'])for(const p of primitives.filter(p=>p.series===series).flatMap(p=>p.world))for(let i=0;i<3;i++)approx(dot(A[i],p),value(m.rhs[i]),'common affine constraint');
  if(m.classification==='none')assert(!primitives.some(p=>['common-line','chosen-solution'].includes(p.series)));
 }else if(state.station==='space'){
  for(let i=0;i<8;i++)vectorEqual(find('mapped-corner-'+i)[0],apply(A,[i&1,(i>>1)&1,(i>>2)&1]),'actual mapped cube corner');
  for(let i=0;i<3;i++)vectorEqual(find('column-'+i)[1],A.map(row=>row[i]),'actual matrix column');
  vectorEqual(find('output')[0],apply(A,[state.space.c1,state.space.c2,state.space.c3].map(value)),'3D output');
  if(m.rank===2)for(const p of find('image-plane-patch'))approx(dot(vector(m.imagePlaneNormal),p),0,'image plane through origin');
 }else if(state.station==='kernel'){
  for(let i=0;i<4;i++)vectorEqual(find('input-tip-'+i)[0],[i+1-.12,value(m.input[i])],'all four input coordinates');
  const output=apply(A,vector(m.input));for(let i=0;i<m.rows;i++)vectorEqual(find('output-tip-'+i)[0],[i+1+.12,output[i]],'all actual codomain coordinates');
  assert.equal(primitives.filter(p=>p.series.startsWith('output-tip-')).length,m.rows);
  approx(dot(vector(m.input),vector(m.input)),value(m.inputNormSquared),'full input norm squared');
 }else if(state.station==='spectrum'){
  const vectors=m.eigenspaces.flatMap(e=>e.basis.map(v=>({v:vector(v),lambda:value(e.value)})));
  assert.equal(primitives.filter(p=>/^eigenvector-\d+$/.test(p.series)).length,vectors.length);
  vectors.forEach((e,i)=>{vectorEqual(find('eigenvector-'+i)[1],e.v,'real eigenvector');vectorEqual(find('eigenimage-'+i)[1],apply(A,e.v),'real eigenimage');vectorEqual(apply(A,e.v),e.v.map(v=>v*e.lambda),'eigenpair residual');});
  vectorEqual(find('probe-image')[1],apply(A,Array(m.rows).fill(1)),'general probe image');
 }else if(state.station==='orbits'){
  let x=[state.orbits.x,state.orbits.y].map(value);const norms=[];
  for(let n=0;n<=state.orbits.n;n++){vectorEqual(find('orbit-'+n)[0],x,'actual orbit '+n);const norm=Math.hypot(...x);norms.push(norm);vectorEqual(find('norm-'+n)[0],[n,norm],'actual Euclidean norm '+n);x=apply(A,x);}
  assert.equal(primitives.filter(p=>/^orbit-\d+$/.test(p.series)).length,state.orbits.n+1);
  if(state.orbits.kind==='decay-nonnormal'&&value(state.orbits.x)===0&&value(state.orbits.y)===1&&state.orbits.n>=3){assert(norms[1]>norms[0]);assert.equal(norms.indexOf(Math.max(...norms)),3);}
 }
 return {primitiveCount:primitives.length,actualSVGVerticesChecked:vertices,independentProjectionAndMatrixResidualChecksPassed:true};
}
async function preservedSPLSmoke(context,page,width){
 const prefix='/app/anatomy/spl-nac-limbic/',registry=JSON.parse(fs.readFileSync(path.join(root,'data/radiology/spl-limbic-reference.json'))),manifest=JSON.parse(fs.readFileSync(path.join(root,'web/anatomy/spl-nac-limbic/manifest.json'))),oracle=JSON.parse(fs.readFileSync(path.join(root,'docs/spl-limbic-source-review-20261016/viewer/pixel-oracles.json')));
 assert.equal(fileHash('web/anatomy/spl-nac-limbic/manifest.json'),oracle.manifestSHA256);
 const expectedRows=[...Object.values(manifest.volumes),manifest.labelVolume,...manifest.labelMeshes,...manifest.meshes],byFile=Object.fromEntries(expectedRows.map(r=>[r.file,r])),pending=[],deliveryErrors=[];
 const observe=response=>{const pathname=new URL(response.url()).pathname;if(!pathname.startsWith(prefix))return;const name=pathname.slice(prefix.length);try{assert.equal(response.status(),200);assert.equal(response.headers()['cache-control'],'private, no-store');if(name==='index.html')assert(response.headers()['content-security-policy'].includes("frame-ancestors 'self'"));}catch(error){deliveryErrors.push(error.message);}if(byFile[name])return;pending.push(response.body().then(raw=>assert.equal(hash(raw),registry.files[name].sha256)).catch(error=>deliveryErrors.push(error.message)));};
 page.on('response',observe);
 const bindings=[];
 for(const identifier of ['ra.brain-anatomy','ra.mri-epilepsy','ra.mri-dementia']){const response=await context.request.get(base+'/api/radiology/modules/'+identifier);assert.equal(response.status(),200);const ref=(await response.json()).radiology_reference,item=ref.source_native_inspectors.find(r=>r.id==='spl-nac-limbic-native-reference');assert.deepEqual(item,registry.inspectors['spl-nac-limbic-native-reference']);assert(ref.reporting.checklist.length&&ref.report_templates.length&&ref.walkthrough.steps.length);if(identifier!=='ra.brain-anatomy')assert(ref.source_native_inspectors.some(r=>r.id==='hippunfold-hcp101006-registered-reference'));bindings.push(identifier);}
 await page.goto(base+'/app/#radiology/ra.brain-anatomy');await page.getByRole('tab',{name:/^3D anatomy/}).click();
 const section=page.locator('.source-native-inspector:visible').filter({has:page.locator('a[href="'+prefix+'index.html"]')});assert.equal(await section.count(),1);
 await section.getByRole('button',{name:'Inspect native SPL MRI and limbic surfaces inline',exact:true}).click();const iframe=section.locator('iframe');await iframe.waitFor();const frame=await(await iframe.elementHandle()).contentFrame();
 const waitMRI=contrast=>frame.waitForFunction(c=>document.querySelector('#mri')?.dataset.ready==='true'&&JSON.parse(document.querySelector('#mri').dataset.state).contrast===c,contrast,{timeout:120000});
 const waitMeshes=()=>frame.waitForFunction(()=>document.querySelector('#mesh')?.dataset.ready==='true'&&window.SPLNativeReference.state().visible.length===12,null,{timeout:60000});
 await waitMRI('T1');await waitMeshes();const pixels=[];
 for(const contrast of ['T1','T2']){if(contrast==='T2'){await frame.selectOption('#contrast',contrast);await waitMRI(contrast);}for(const plane of ['axial','coronal','sagittal']){await frame.selectOption('#structure','17');await frame.selectOption('#plane',plane);await frame.click('#reset-window');for(const kind of ['focus','fornix-source-outlier']){if(kind==='fornix-source-outlier'){await frame.selectOption('#structure','3007');await frame.click('#fornix-outlier');}const expected=oracle.fixtures.find(f=>f.contrast===contrast&&f.plane===plane&&f.name===kind&&(kind!=='focus'||f.label===17));const actual=await frame.evaluate(async()=>{const c=document.querySelector('#mri'),raw=c.getContext('2d').getImageData(0,0,c.width,c.height).data;return{sha256:[...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(x=>x.toString(16).padStart(2,'0')).join(''),pixels:c.width*c.height};});assert.equal(actual.sha256,expected.rgbaSHA256);pixels.push({contrast,plane,kind,...actual});}}}
 await frame.selectOption('#surface-kind','publisher');await waitMeshes();assert.match(await frame.locator('#surface-note').textContent(),/fornix objects differ substantially/);
 const gpu=await frame.evaluate(()=>window.SPLNativeReference.gpuReadback());assert.equal(gpu.length,24);for(const row of [...manifest.labelMeshes,...manifest.meshes]){const actual=gpu.find(r=>r.file===row.file);assert.equal(actual.positionSHA256,row.positionByteSHA256);assert.equal(actual.indexSHA256,row.indexByteSHA256);assert.equal(actual.worldSHA256,row.positionByteSHA256);}
 await frame.locator('#mesh').focus();const before=await frame.evaluate(()=>window.SPLNativeReference.state().renderState.azimuth);await page.keyboard.press('ArrowRight');assert.notEqual(await frame.evaluate(()=>window.SPLNativeReference.state().renderState.azimuth),before);
 assert.equal(await frame.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);assert.deepEqual(await frame.evaluate(()=>window.linalgCSP),[]);
 await iframe.scrollIntoViewIfNeeded();await section.screenshot({path:path.join(out,'preserved-spl-'+width+'.png')});await Promise.all(pending);assert.deepEqual(deliveryErrors,[]);const deliveries=await frame.evaluate(()=>window.splReaderDeliveries);assert.deepEqual(await frame.evaluate(()=>window.splReaderDeliveryErrors),[]);assert.deepEqual(Object.keys(deliveries).sort(),expectedRows.map(r=>r.file).sort());for(const row of expectedRows){const d=deliveries[row.file];assert.equal(d.status,200);assert([row.gzipSHA256,row.decodedSHA256].includes(d.sha256));assert.equal(d.bytes,d.sha256===row.gzipSHA256?row.gzipBytes:row.byteLength);}
 await section.getByRole('button',{name:'Close source viewer',exact:true}).click();assert.equal(await section.locator('iframe').count(),0);page.off('response',observe);
 return{width,investigation:'ra.brain-anatomy',entryPoint:'3D anatomy and original source context',bindingsChecked:bindings,pixels,gpuMeshes:gpu.length,gpu,actualPayloads:deliveries,registrySHA256:fileHash('data/radiology/spl-limbic-reference.json'),manifestSHA256:oracle.manifestSHA256,keyboardRotation:true,originalReportsAndHippUnfoldReferencesRetained:true,productionVerified:false,historical24CaseReceiptReusedAsCurrent:false};
}
(async()=>{
 fs.mkdirSync(out,{recursive:true});const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const allSnapshots=[];
 const proof={scope:'Actual authenticated linear-algebra lesson on isolated synthetic loopback storage',productionVerified:false,wholeModuleComplete:false,independentMathematicsEstablishedByThisReaderCheck:false,
  sourceSHA256:Object.fromEntries(['web/linear-algebra-lab.js','web/lesson-models.js','web/index.html','web/app.js','web/math-eigenspace.js','web/math-eigenspace.css','data/curriculum/01-mathematics.json','primer/curriculum.py','tools/check_linear_algebra_independent.cjs','tools/check_linear_algebra_independent.py'].map(p=>[p,fileHash(p)])),authentication:[],readerCases:[],errors:[]};
 try{
  const anonymous=await browser.newContext();
  for(const asset of ['/app/linear-algebra-lab.js','/app/startup.js','/api/curriculum/node/math.4.linalg']){const r=await anonymous.request.get(base+asset);assert.equal(r.status(),401);proof.authentication.push({asset,status:r.status()});}
  await anonymous.close();
  for(const width of [390,1440]){
   const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce',extraHTTPHeaders:{Authorization:'Basic '+Buffer.from(fixture.username+':'+fixture.password).toString('base64')}});
   const profile=await context.request.post(base+'/api/profile',{headers:{Origin:base},data:{name:'Synthetic linear algebra QA',age:30,domains:['math','radiology']}});assert.equal(profile.status(),200);
   await context.request.post(base+'/api/profile/settings',{headers:{Origin:base},data:{speak:false}});
   const response=await context.request.get(base+'/api/curriculum/node/math.4.linalg');assert.equal(response.status(),200);const body=await response.json(),node=body.node||body;
   assert.equal(node.id,authored.id);assert.equal(node.quiz,undefined);assert.equal(node.question_count,10);
   for(const item of authored.lesson_media)assert.deepEqual(node.lesson_media.find(m=>m.id===item.id),item);
   for(const q of authored.quiz)for(const key of ['prompt','explain'])assert(!JSON.stringify(node).includes(q[key]));
   const script=await context.request.get(base+'/app/linear-algebra-lab.js');assert.equal(script.status(),200);assert.equal(hash(await script.body()),proof.sourceSHA256['web/linear-algebra-lab.js']);
   const page=await context.newPage(),errors=[],external=[],pendingBundles=[],states=[],speech=[],oldMaps=[];
   await page.route('**/*',route=>{if(new URL(route.request().url()).origin!==base){external.push(route.request().url());return route.abort();}return route.continue();});
   await page.addInitScript(()=>{window.linalgCSP=[];window.linalgSpoken=[];window.splReaderDeliveries={};window.splReaderDeliveryErrors=[];const originalFetch=window.fetch.bind(window);window.fetch=async(...args)=>{const response=await originalFetch(...args),prefix='/app/anatomy/spl-nac-limbic/',pathname=new URL(response.url).pathname;if(pathname.startsWith(prefix)&&pathname.endsWith('.gz')){try{const raw=await response.clone().arrayBuffer();window.splReaderDeliveries[pathname.slice(prefix.length)]={status:response.status,bytes:raw.byteLength,sha256:[...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(x=>x.toString(16).padStart(2,'0')).join('')};}catch(error){window.splReaderDeliveryErrors.push(String(error));}}return response;};document.addEventListener('securitypolicyviolation',e=>window.linalgCSP.push({directive:e.violatedDirective,blocked:e.blockedURI}));Object.defineProperty(speechSynthesis,'speak',{configurable:true,value:u=>{window.linalgSpoken.push(u.text);setTimeout(()=>u.onend?.(),0);}});});
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   page.on('response',r=>{if(new URL(r.url()).pathname==='/app/startup.js')pendingBundles.push(r.body().then(raw=>{assert(raw.equals(bundle));proof.startupBundle={bytes:raw.length,sha256:hash(raw),currentSourceBytesEqual:true};}).catch(e=>errors.push('Startup identity: '+e.message)));});
   await page.goto(base+'/app/#/node/math.4.linalg');
   const model=page.locator('.lesson-model[data-renderer="linear-algebra-lab"][data-linalg-lab]');await model.waitFor();
   await page.waitForFunction(()=>document.querySelector('[data-linalg-lab]')?.dataset.linalgReady==='true');assert.equal(await model.count(),1);
   assert.equal(await model.locator('.model-heading-row h3').textContent(),companion.title);assert.equal(await model.locator('.model-instructions').textContent(),companion.instructions);
   const plate=original.find(m=>m.kind==='illustration');await page.waitForFunction(src=>[...document.images].some(image=>image.getAttribute('src')===src&&image.complete&&image.naturalWidth>0),plate.src);
   const prior=page.locator('.lesson-model[data-renderer="matrix-transform-lab"]');assert.equal(await prior.count(),1);
   for(const[label,A,det]of matrices){await prior.getByRole('button',{name:label,exact:true}).click();for(const angle of [0,45,90]){
    await prior.locator('[data-eigen-angle]').fill(String(angle));await prior.locator('[data-eigen-angle]').dispatchEvent('input');
    const got=await prior.evaluate(el=>({vectors:[...el.querySelectorAll('[data-eigen-vector]')].map(e=>({role:e.dataset.eigenVector,x1:+e.getAttribute('x1'),y1:+e.getAttribute('y1'),x2:+e.getAttribute('x2'),y2:+e.getAttribute('y2')})),ticks:[...el.querySelectorAll('.math-eigen-svg text')].map(e=>({text:e.textContent,x:+e.getAttribute('x'),y:+e.getAttribute('y')})),squares:[...el.querySelectorAll('.matrix-unit-square')].map(e=>e.getAttribute('points').split(' ').map(p=>p.split(',').map(Number))),spaces:el.querySelector('.math-eigen-spaces').textContent}));
    const t0=got.ticks.find(t=>t.text==='0'&&t.y===373),t1=got.ticks.find(t=>t.text==='1'&&t.y===373),scale=t1.x-t0.x;
    const v=angle===0?[1,0]:angle===90?[0,1]:[Math.cos(Math.PI/4),Math.sin(Math.PI/4)],Av=A.map(r=>r[0]*v[0]+r[1]*v[1]);
    const image=got.vectors.find(v=>v.role==='image');near((image.x2-t0.x)/scale,Av[0],'old fixed-map x');near((195-image.y2)/scale,Av[1],'old fixed-map y');near(signedArea(got.squares[1])/signedArea(got.squares[0]),det,'old signed area');assert.match(got.spaces,/Rank \+ nullity = 2/);
    oldMaps.push({label,angle,determinant:det,actualSVGImageAndSignedAreaVerified:true});
   }}
   const choose=station=>model.locator('[data-linalg-control="station"]').selectOption(station);
   assert.deepEqual(await model.locator('[data-linalg-control="station"] option').evaluateAll(options=>options.map(o=>o.value)),stations);
   const check=async label=>{
    const result=await model.evaluate(el=>{const state=el.linalg.getState(),panel=el.querySelector('[data-linalg-panel="'+state.station+'"]');const plots=[...panel.querySelectorAll('svg[data-linalg-plot]')];return {state,readout:el.querySelector('.model-readout').textContent,error:panel.dataset.error||null,visible:!panel.hidden,activeModel:el.linalg.getModels()[state.station],plots:plots.map(svg=>({name:svg.dataset.linalgPlot,viewBox:svg.getAttribute('viewBox'),domain:JSON.parse(svg.dataset.axisDomain),projection:svg.dataset.projection?JSON.parse(svg.dataset.projection):null,primitives:[...svg.querySelectorAll('[data-world]')].map(p=>({series:p.dataset.series,world:JSON.parse(p.dataset.world),pixels:p.tagName==='circle'?[[+p.getAttribute('cx'),+p.getAttribute('cy')]]:p.getAttribute('points').trim().split(/\s+/).map(pair=>pair.split(',').map(Number))})),invalidNumericGeometry:[...svg.querySelectorAll('*')].some(n=>[...n.attributes].some(a=>/(?:NaN|Infinity)/.test(a.value)))})),overflow:document.documentElement.scrollWidth>innerWidth+1};});
    assert.equal(result.error,null);assert(result.visible);assert.equal(result.overflow,false);assert(result.readout.trim());assert(!/NaN|Infinity/.test(result.readout));assert(result.plots.length>0);assert(result.plots.every(p=>!p.invalidNumericGeometry));const geometry=verifyGeometry(result),independentSnapshot=await model.evaluate(captureSnapshot);independentSnapshot.id=width+':'+label+':'+allSnapshots.length;allSnapshots.push(independentSnapshot);states.push({label,state:result.state,readout:result.readout,activeModel:result.activeModel,plots:result.plots.map(({primitives,...plot})=>({...plot,primitiveSHA256:hash(Buffer.from(JSON.stringify(primitives))),primitiveCount:primitives.length})),geometry,noHorizontalOverflow:true});return result;
   };
   await check('authored state');
   for(const station of stations){
    await choose(station);await check(station+' selected');
    const presets=await model.locator('[data-linalg-panel="'+station+'"] [data-linalg-preset]').evaluateAll(nodes=>nodes.map(n=>n.dataset.linalgPreset));
    assert(presets.length>0,'Each station must expose declared source fixtures');
    for(const preset of presets){await model.locator('[data-linalg-preset="'+preset+'"]').click();await check(preset);}
    const kinds=model.locator('[data-linalg-control="'+station+'.kind"]');
    if(await kinds.count())for(const kind of await kinds.locator('option').evaluateAll(options=>options.map(o=>o.value))){await kinds.selectOption(kind);await check(station+' kind '+kind);}
    if(station==='space'){await model.locator('[data-linalg-preset="space-plane"]').click();for(const action of ['space-face','space-edge']){await model.locator('[data-linalg-action="'+action+'"]').click();await check(action);}}
    if(station==='orbits'){
     await kinds.selectOption('eigenpower');for(const [field,value]of [['x','1'],['y','0']]){const input=model.locator('[data-linalg-control="orbits.'+field+'"]');await input.fill(value);await input.dispatchEvent('change');}
     const n=model.locator('[data-linalg-control="orbits.n"]');for(const value of [0,100]){await n.evaluate((e,v)=>{e.value=String(v);e.dispatchEvent(new Event('input',{bubbles:true}));},value);await check('orbits eigenvalue4 n='+value);}
    }
    if(station==='spectrum'){await kinds.selectOption('tri235');await check('spectrum 3D camera fixture');}
    const yaw=model.locator('[data-linalg-control="'+station+'.yaw"]');
    if(await yaw.count()&&await yaw.isEnabled()){const previous=await yaw.inputValue();await yaw.focus();await page.keyboard.press('ArrowRight');assert.notEqual(await yaw.inputValue(),previous);await check(station+' camera keyboard rotation');}
    await model.locator('[data-linalg-action="enlarge"]').click();await check(station+' enlarged');
    const region=model.locator('[data-linalg-panel="'+station+'"] svg[data-linalg-plot]').first().locator('..');
    if(await region.evaluate(e=>e.scrollWidth>e.clientWidth)){await region.focus();await page.keyboard.press('ArrowRight');await page.waitForFunction(e=>e.scrollLeft>0,await region.elementHandle());}
    await model.locator('[data-linalg-action="enlarge"]').click();await check(station+' fitted');
    await page.evaluate(()=>{window.linalgSpoken=[];});const speechButton=model.getByRole('button',{name:'Read this activity aloud',exact:true});await speechButton.focus();await page.keyboard.press('Enter');
    await page.waitForFunction(()=>!document.querySelector('[data-linalg-lab] .speak-btn').classList.contains('speaking'));
    const spoken=await page.evaluate(()=>window.linalgSpoken.join(' ')),readout=await model.locator('.model-readout').textContent();assert(spoken.replace(/\s+/g,' ').includes(readout.replace(/\s+/g,' ')));if(station==='kernel'){const active=await model.evaluate(el=>el.linalg.getModels().kernel);for(const tuple of [active.input,active.output])assert(spoken.includes('('+tuple.join(', ')+')'),'Actual read-aloud must retain all input/output coordinates');}
    speech.push({station,readoutIncluded:true,allInputAndOutputCoordinatesSpoken:station==='kernel'?true:undefined,characters:spoken.length});
    await model.screenshot({path:path.join(out,station+'-'+width+'.png')});
   }
   for(const station of ['maps','systems','planes','space','kernel','orbits']){
    await choose(station);if(station==='planes')await model.locator('[data-linalg-control="planes.kind"]').selectOption('dependent');const panel=model.locator('[data-linalg-panel="'+station+'"]'),input=panel.locator('input[type="text"]:enabled').first();const saved=await input.inputValue();
    await input.fill('not-a-number');await input.dispatchEvent('change');assert(await panel.getAttribute('data-error'));assert.equal(await input.getAttribute('aria-invalid'),'true');assert.equal(await panel.locator('svg').count(),0);assert((await model.locator('.model-readout').textContent()).includes('Invalid input'));
    const rejectedSnapshot=await model.evaluate(captureSnapshot);rejectedSnapshot.id=width+':'+station+':invalid';allSnapshots.push(rejectedSnapshot);
    states.push({label:station+' invalid rational input',station,invalidValueRejected:true,staleGeometryRemoved:true});
    await input.fill(saved);await input.dispatchEvent('change');await check(station+' valid recovery');
   }
   await model.locator('[data-linalg-action="reset"]').click();await check('reset');
   assert(await model.locator('input,select').evaluateAll(nodes=>nodes.every(n=>n.labels?.length>0)));
   const preservedSPL=await preservedSPLSmoke(context,page,width);proof.lastNetworkObservation={width,errors,external};await Promise.all(pendingBundles);assert(pendingBundles.length>0);assert.deepEqual(errors,[]);assert.deepEqual(external,[]);assert.deepEqual(await page.evaluate(()=>window.linalgCSP),[]);
   proof.readerCases.push({width,states,speech,preservedOldFiveMaps:oldMaps,preservedSPL,originalIllustrationLoaded:true,quizAnswersNotExposedByPublicNodeAPI:true,currentStartupBundleExact:true,CSPViolations:[],pageErrors:[],externalRequests:[]});await context.close();
  }
  proof.independentRenderedCoordinateVerification=verifySnapshots(allSnapshots);assert(proof.independentRenderedCoordinateVerification.allPassed);
  fs.writeFileSync(path.join(out,'snapshots.json'),JSON.stringify(allSnapshots)+'\n');
  proof.snapshotsSHA256=fileHash('docs/linear-algebra-fidelity-review-20261016/reader/snapshots.json');
  for(const[name,pin]of Object.entries(proof.sourceSHA256))assert.equal(fileHash(name),pin,'Source changed during reader check: '+name);
  proof.totalStates=proof.readerCases.reduce((n,c)=>n+c.states.length,0);proof.speechCases=proof.readerCases.reduce((n,c)=>n+c.speech.length,0);proof.allPassed=true;
  fs.writeFileSync(path.join(out,'proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify({actualReaderStates:proof.totalStates,speechCases:proof.speechCases,oldMapStates:proof.readerCases.reduce((n,c)=>n+c.preservedOldFiveMaps.length,0),startupBytes:proof.startupBundle.bytes,productionVerified:false}));
 }catch(error){fs.writeFileSync(path.join(out,'partial-proof.json'),JSON.stringify({...proof,failure:String(error),snapshotCount:allSnapshots.length},null,2)+'\n');fs.writeFileSync(path.join(out,'partial-snapshots.json'),JSON.stringify(allSnapshots)+'\n');throw error;}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
