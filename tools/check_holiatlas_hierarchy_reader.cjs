'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto'),{chromium}=require('playwright');
const ROOT=path.join(__dirname,'..'),OUT=path.join(ROOT,'docs/holiatlas-hierarchy-review-20261025/reader'),fixture=JSON.parse(fs.readFileSync(0,'utf8'));
assert.equal(new URL(fixture.url).hostname,'127.0.0.1');
const prefix='/app/anatomy/holiatlas/',url=fixture.url+prefix+'index.html',hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const oracle=JSON.parse(fs.readFileSync(path.join(ROOT,'docs/holiatlas-hierarchy-review-20261025/reader-oracle.json'))),fineOracle=JSON.parse(fs.readFileSync(path.join(ROOT,'docs/holiatlas-source-review-20261023/reader-oracle.json'))),registry=JSON.parse(fs.readFileSync(path.join(ROOT,'data/radiology/holiatlas-reference.json')));
const headers={Authorization:'Basic '+Buffer.from(fixture.username+':'+fixture.password).toString('base64')};
const pinnedFiles=['web/app.js','web/index.html','primer/server.py','primer/source_native_inspectors.py','primer/holiatlas_reference.py','data/radiology/holiatlas-reference.json','web/anatomy/holiatlas/config.json','web/anatomy/holiatlas/hierarchy.json','web/anatomy/holiatlas/viewer.js','web/anatomy/holiatlas/viewer.css','web/anatomy/holiatlas/index.html','tools/check_holiatlas_hierarchy_reader.py','tools/check_holiatlas_hierarchy_reader.cjs','tools/anatomy_sources/build_holiatlas_hierarchy_oracle.py','docs/holiatlas-hierarchy-review-20261025/reader-oracle.json','docs/holiatlas-source-review-20261023/reader-oracle.json'];
const initialPins=Object.fromEntries(pinnedFiles.map(f=>[f,hash(fs.readFileSync(path.join(ROOT,f)))]));
for(const f of ['web/anatomy/holiatlas/config.json','web/anatomy/holiatlas/hierarchy.json'])assert.equal(initialPins[f],oracle.inputSHA256[f]);
assert.equal(oracle.allGenerated,true);assert.equal(oracle.counts.nativePlaneCases,2934);assert.equal(Object.keys(registry.files).length,846);
const shell=fs.readFileSync(path.join(ROOT,'web/index.html'),'utf8'),scripts=[...shell.matchAll(/<script src="\/app\/([\w-]+\.js)(?:\?[^"<>]*)?"><\/script>/g)].map(m=>m[1]),bundle=Buffer.from("'use strict';\n"+scripts.map(n=>fs.readFileSync(path.join(ROOT,'web',n),'utf8')).join('\n;\n'));
const proof={scope:'Actual authenticated application and source reader, isolated synthetic learner storage; full independent native-volume oracle coverage.',productionVerified:false,clinicalApproval:false,allPassed:false,startedAtUTC:new Date().toISOString(),startupSHA256:hash(bundle),authentication:[],servedMetadata:{},desktopCases:[],gpu:[],mobileCases:[],wrapperCases:[],fixedScale:[],recovery:[],errors:[],sourceSHA256:initialPins};
fs.mkdirSync(OUT,{recursive:true});
function save(){const p=path.join(OUT,'proof.json'),tmp=p+'.tmp';fs.writeFileSync(tmp,JSON.stringify(proof,null,2)+'\n');fs.renameSync(tmp,p);}
save();
const caseKey=c=>[c.level,c.code,c.component,c.contrast,Number(c.outline)].join(':');
const representative=(level,code)=>oracle.cases.find(c=>c.level===level&&c.code===code&&c.component===0&&c.contrast==='T1'&&!c.outline);
const fineCase={level:'fine',code:80,component:0,contrast:'T1',outline:false,overlay:true};

async function ready(frame,c){
  await frame.waitForFunction(c=>{
    const r=window.HoliAtlasReader;
    if(!r||document.body.dataset.ready!=='true'||r.state.level!==c.level||r.state.code!==c.code||r.state.component!==c.component||r.state.contrast!==c.contrast||r.mesh?.key!==c.level+':'+c.code)return false;
    if(document.querySelector('#outline').checked!==c.outline||!document.querySelector('#overlay').checked)return false;
    return [0,1,2].every(axis=>{try{const p=JSON.parse(document.querySelector('#plane'+axis).dataset.source);return p.level===c.level&&p.code===c.code&&p.contrast===c.contrast&&p.outline===c.outline&&p.index===r.state.ijk[axis]&&(!c.focusSourceIJK||p.index===c.focusSourceIJK[axis]);}catch{return false;}});
  },c,{timeout:120000});
}

async function choose(frame,c){
  if(await frame.locator('#source-level').inputValue()!==c.level)await frame.locator('#source-level').selectOption(c.level);
  if(await frame.locator('#structure').inputValue()!==String(c.code))await frame.locator('#structure').selectOption(String(c.code));
  if(await frame.locator('#component').inputValue()!==String(c.component))await frame.locator('#component').selectOption(String(c.component));
  if(await frame.locator('#contrast').inputValue()!==c.contrast)await frame.locator('#contrast').selectOption(c.contrast);
  await frame.locator('#overlay').setChecked(true);await frame.locator('#outline').setChecked(c.outline);
  if(c.focusSourceIJK&&!await frame.evaluate(ijk=>JSON.stringify(HoliAtlasReader.state.ijk)===JSON.stringify(ijk),c.focusSourceIJK))await frame.locator('#focus').click();
  await ready(frame,c);
}

async function pixels(frame,c){
  const actual=await frame.evaluate(async()=>Promise.all([0,1,2].map(async axis=>{const canvas=document.querySelector('#plane'+axis),raw=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;return {axis,sha256:Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),x=>x.toString(16).padStart(2,'0')).join(''),width:canvas.width,height:canvas.height,pixels:canvas.width*canvas.height,source:JSON.parse(canvas.dataset.source)};})));
  for(const p of actual){
    const key=c.level==='fine'?[c.code,c.component,c.contrast,p.axis].join(':'):[c.level,c.code,c.component,c.contrast,p.axis,Number(c.outline)].join(':');
    const expected=(c.level==='fine'?fineOracle:oracle).pixels[key];assert(expected,'Missing oracle '+key);
    assert.equal(p.sha256,expected.sha256,'Native plane '+key);assert.deepEqual([p.height,p.width,4],expected.shape,key+' shape');
    assert.equal(p.source.level,c.level);assert.equal(p.source.code,c.code);assert.equal(p.source.contrast,c.contrast);assert.equal(p.source.outline,c.outline);assert.equal(p.source.overlay,true);
    if(c.focusSourceIJK)assert.equal(p.source.index,c.focusSourceIJK[p.axis]);
  }
  return actual.map(p=>({axis:p.axis,sha256:p.sha256,pixels:p.pixels,index:p.source.index}));
}

async function gpu(frame,level,code){
  const actual=await frame.evaluate(async()=>{const hash=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b)),x=>x.toString(16).padStart(2,'0')).join(''),g=HoliAtlasReader.gpu();return {key:HoliAtlasReader.mesh.key,positionSHA256:await hash(g.positions.buffer),indexSHA256:await hash(g.indices.buffer),vertices:HoliAtlasReader.mesh.vertices,triangles:HoliAtlasReader.mesh.triangles};});
  assert.equal(actual.key,level+':'+code);const expected=level==='fine'?fineOracle.meshes[String(code)]:oracle.meshes[level+':'+code];
  for(const key of ['positionSHA256','indexSHA256','vertices','triangles'])assert.equal(actual[key],expected[key],level+':'+code+' '+key);
  return {level,code,...actual};
}

async function healthy(page,frame=page){
  assert(await frame.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Reader horizontal overflow');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'App horizontal overflow');
  assert.deepEqual(await frame.evaluate(()=>window.hierarchyCSP),[]);assert.deepEqual(await page.evaluate(()=>window.hierarchyCSP),[]);
  assert.deepEqual(await frame.evaluate(()=>HoliAtlasReader.stats.errors),[]);
  assert(await frame.evaluate(()=>HoliAtlasReader.stats.cacheBytes<=16*1024*1024));
}

async function context(browser,width){
  const ctx=await browser.newContext({viewport:{width,height:1000},extraHTTPHeaders:headers});
  await ctx.addInitScript(()=>{window.hierarchyCSP=[];document.addEventListener('securitypolicyviolation',e=>window.hierarchyCSP.push(e.violatedDirective));});
  const page=await ctx.newPage(),pending=[];
  page.on('pageerror',e=>proof.errors.push(String(e)));
  await page.route('**/*',route=>new URL(route.request().url()).origin===fixture.url?route.continue():route.abort());
  page.on('response',response=>{
    const name=new URL(response.url()).pathname;
    if(name==='/app/startup.js')pending.push(response.body().then(raw=>assert(raw.equals(bundle))).catch(e=>proof.errors.push(String(e))));
    // Large compressed meshes can be evicted from Chromium's inspector cache.
    // Their exact geometry is checked through real GPU buffers against the
    // independent source oracle; the reader also checks compressed/decoded SHA.
    if(name.startsWith(prefix)&&response.status()===200){const file=name.slice(prefix.length);if(registry.files[file]&&/\.(html|css|js|json|txt)$/.test(file))pending.push(response.body().then(raw=>{assert.equal(hash(raw),registry.files[file].sha256,file);proof.servedMetadata[file]=hash(raw);}).catch(e=>proof.errors.push(file+': '+String(e))));}
  });
  return {ctx,page,pending};
}

async function checkFixedScale(page){
  const expectedCenter=[.25,-17.75,18.25],expectedScale=new Float32Array([Math.hypot(90.5,108.5,90.5)*1.08])[0];
  await page.locator('#fixed-scale').check();
  for(const c of [representative('composition',1),representative('tissue',4),representative('organ',1)]){
    await choose(page,c);assert.match(await page.locator('#mesh-note').textContent(),/Fixed full-source frame/);
    const uniform=await page.locator('#mesh').evaluate(canvas=>{const gl=canvas.getContext('webgl2'),program=gl.getParameter(gl.CURRENT_PROGRAM);return {center:Array.from(gl.getUniform(program,gl.getUniformLocation(program,'center'))),scale:gl.getUniform(program,gl.getUniformLocation(program,'scale'))};});
    assert.deepEqual(uniform.center,expectedCenter);assert.equal(uniform.scale,expectedScale);proof.fixedScale.push({level:c.level,code:c.code,...uniform});
  }
  await page.locator('#fixed-scale').uncheck();assert.match(await page.locator('#mesh-note').textContent(),/Camera fits the selection/);
  const fit=await page.locator('#mesh').evaluate(canvas=>{const gl=canvas.getContext('webgl2'),p=gl.getParameter(gl.CURRENT_PROGRAM);return {center:Array.from(gl.getUniform(p,gl.getUniformLocation(p,'center'))),expectedCenter:Array.from(new Float32Array(HoliAtlasReader.mesh.center)),scale:gl.getUniform(p,gl.getUniformLocation(p,'scale')),expectedScale:new Float32Array([HoliAtlasReader.mesh.scale])[0]};});
  assert.deepEqual(fit.center,fit.expectedCenter);assert.equal(fit.scale,fit.expectedScale);proof.fixedScale.push({mode:'fit-selection',...fit});
}

async function wrappers(browser,width){
  const {ctx,page,pending}=await context(browser,width);
  assert.equal((await ctx.request.post(fixture.url+'/api/profile',{headers:{Origin:fixture.url},data:{name:'Synthetic hierarchy QA',age:30,domains:['radiology']}})).status(),200);
  assert.equal((await ctx.request.post(fixture.url+'/api/profile/settings',{headers:{Origin:fixture.url},data:{speak:false}})).status(),200);
  async function inspect(section,entry){
    assert.equal(await section.count(),1);await section.getByRole('button',{name:'Inspect source brain templates and cell boundaries inline',exact:true}).click();
    const iframe=section.locator('iframe');await iframe.waitFor();const frame=await(await iframe.elementHandle()).contentFrame();
    await ready(frame,fineCase);const c=representative('composition',1);await choose(frame,c);const native=await pixels(frame,c),mesh=await gpu(frame,c.level,c.code);
    await frame.locator('#outline').check();const outlined={...c,outline:true};await ready(frame,outlined);const outlinePixels=await pixels(frame,outlined);
    await healthy(page,frame);await Promise.all(pending);await section.screenshot({path:path.join(OUT,entry+'-'+width+'.png')});
    proof.wrapperCases.push({entry,width,level:c.level,code:c.code,pixels:native,outlinePixels,mesh,noOverflow:true,CSPViolations:[]});
    await section.getByRole('button',{name:'Close source viewer',exact:true}).click();assert.equal(await section.locator('iframe').count(),0);save();console.log('Application wrapper',entry,width);
  }
  await page.goto(fixture.url+'/app/#radiology/ra.brain-anatomy');
  for(const [tab,entry]of [[/^Images and MRI sources$/,'images'],[/^3D anatomy/,'model']]){await page.getByRole('tab',{name:tab}).click();await inspect(page.locator('.source-native-inspector:visible').filter({has:page.locator('a[href="'+prefix+'index.html"]')}),entry);}
  await page.getByRole('tab',{name:'Step by step',exact:true}).click();await page.getByRole('button',{name:'Original source context',exact:true}).click();
  await inspect(page.locator('.rad-walk .source-native-inspector:visible').filter({has:page.locator('a[href="'+prefix+'index.html"]')}),'walkthrough');
  await page.goto(fixture.url+'/app/#/node/rad.5.brain-anatomy');let gallery=page.locator('.lesson-source-gallery').filter({has:page.getByRole('button',{name:/^Load original native source inspections$/})});await gallery.waitFor({timeout:60000});gallery=page.getByRole('region',{name:await gallery.getAttribute('aria-label'),exact:true});
  await gallery.getByRole('button',{name:/^Load original /}).click();await gallery.getByText(/Original .+ loaded\./).waitFor();await gallery.locator('details > summary').click();
  await inspect(gallery.locator('.source-native-inspector').filter({has:page.locator('a[href="'+prefix+'index.html"]')}),'lesson');
  await Promise.all(pending);await ctx.close();
}

async function invalidWindowRace(browser){
  const {ctx,page,pending}=await context(browser,390);await page.goto(url);await ready(page,fineCase);
  let release,observed,finished,held=false;const gate=new Promise(r=>release=r),seen=new Promise(r=>observed=r),done=new Promise(r=>finished=r);
  await page.route('**/*.pack',async route=>{if(held)return route.continue();held=true;observed();try{const response=await route.fetch(),body=await response.body(),headers=response.headers();await gate;await route.fulfill({status:response.status(),headers,body});}catch{}finally{finished();}});
  await page.locator('#source-level').selectOption('composition');
  await Promise.race([seen,new Promise((_,reject)=>setTimeout(()=>reject(Error('Expected pending source range was not observed')),30000))]);
  await page.locator('#low').fill('400');await page.locator('#low').dispatchEvent('change');
  await page.locator('#source-level').selectOption('structure');await page.locator('#structure').selectOption('8');
  async function blank(){await page.waitForFunction(()=>document.body.dataset.ready==='error');return page.evaluate(()=>({level:HoliAtlasReader.state.level,code:HoliAtlasReader.state.code,mesh:HoliAtlasReader.mesh,gpu:HoliAtlasReader.gpu(),blankPlanes:[0,1,2].every(a=>{const c=document.querySelector('#plane'+a);return c.getContext('2d').getImageData(0,0,c.width,c.height).data.every(v=>v===0);}),status:document.querySelector('#status').textContent}));}
  const before=await blank();assert.equal(before.level,'structure');assert.equal(before.code,8);assert.equal(before.mesh,null);assert.equal(before.gpu,null);assert(before.blankPlanes);assert.match(before.status,/finite window/);
  release();await done;await page.unroute('**/*.pack');await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const after=await blank();assert.equal(after.mesh,null);assert.equal(after.gpu,null);assert(after.blankPlanes);assert.equal(after.code,8);
  await page.screenshot({path:path.join(OUT,'invalid-window-cleared-390.png'),fullPage:true});
  await page.locator('#low').fill('2');await page.locator('#low').dispatchEvent('change');await page.locator('#retry').click();
  const c=representative('structure',8);await ready(page,c);const native=await pixels(page,c),mesh=await gpu(page,c.level,c.code);await healthy(page);
  await page.screenshot({path:path.join(OUT,'invalid-window-recovered-390.png'),fullPage:true});
  proof.recovery.push({fault:'Delayed old source followed by invalid window and source-level/region change',pendingRangeObserved:held,invalidStateClearedBeforeAndAfterOldResponse:true,latestSelection:c,pixels:native,mesh,nativePixelsExact:true});save();await Promise.all(pending);await ctx.close();
}

(async()=>{
  const browser=await chromium.launch({headless:true});
  try{
    const anonymous=await browser.newContext();const hierarchy=JSON.parse(fs.readFileSync(path.join(ROOT,'web/anatomy/holiatlas/hierarchy.json')));
    for(const asset of ['index.html','config.json','manifest.json','labels.json','hierarchy.json',hierarchy.levels.structure.sourceClasses[0].mesh.file,hierarchy.levels.composition.sourceClasses[0].mesh.file,'T1-axis-0-part-0.pack']){const r=await anonymous.request.get(fixture.url+prefix+asset);assert.equal(r.status(),401);proof.authentication.push({asset,status:401});}await anonymous.close();save();
    const desktop=await context(browser,1440),page=desktop.page;await page.goto(url);await ready(page,fineCase);const checkedMeshes=new Set(),componentCoverage=new Set();
    for(const c of oracle.cases){
      await choose(page,c);const native=await pixels(page,c);proof.desktopCases.push({key:caseKey(c),...c,pixels:native});componentCoverage.add([c.level,c.code,c.component].join(':'));
      const key=c.level+':'+c.code;if(!checkedMeshes.has(key)){proof.gpu.push(await gpu(page,c.level,c.code));checkedMeshes.add(key);await healthy(page);save();console.log('Desktop source',key,'view cases',proof.desktopCases.length);}
      if(proof.desktopCases.length%50===0){save();console.log('Desktop progress',proof.desktopCases.length,'/',oracle.cases.length);}
    }
    assert.equal(proof.desktopCases.length,978);assert.equal(proof.desktopCases.reduce((n,c)=>n+c.pixels.length,0),2934);assert.equal(checkedMeshes.size,79);assert.equal(componentCoverage.size,741);proof.componentFocusCoverage=componentCoverage.size;
    await checkFixedScale(page);await choose(page,{...representative('composition',1),outline:true});await page.screenshot({path:path.join(OUT,'composition-outline-1440.png'),fullPage:true});await healthy(page);await Promise.all(desktop.pending);await desktop.ctx.close();save();
    const mobile=await context(browser,390);await mobile.page.goto(url);await ready(mobile.page,fineCase);
    for(const c of [fineCase,representative('structure',18),representative('tissue',4),representative('organ',1),representative('composition',1)]){await choose(mobile.page,c);const native=await pixels(mobile.page,c),mesh=await gpu(mobile.page,c.level,c.code);await healthy(mobile.page);await mobile.page.screenshot({path:path.join(OUT,c.level+'-390.png'),fullPage:true});proof.mobileCases.push({...c,pixels:native,mesh,noOverflow:true,CSPViolations:[]});save();}
    await Promise.all(mobile.pending);await mobile.ctx.close();
    for(const width of [390,1440])await wrappers(browser,width);
    await invalidWindowRace(browser);
    assert.equal(proof.wrapperCases.length,8);assert.equal(proof.mobileCases.length,5);assert.deepEqual(proof.errors,[]);
    for(const name of ['index.html','viewer.js','viewer.css','config.json','manifest.json','labels.json','hierarchy.json'])assert.equal(proof.servedMetadata[name],registry.files[name].sha256,name+' served identity');
    for(const [f,pin]of Object.entries(initialPins))assert.equal(hash(fs.readFileSync(path.join(ROOT,f))),pin,'Source changed during browser check: '+f);
    proof.allPassed=true;proof.completedAtUTC=new Date().toISOString();proof.summary={desktopViewCases:proof.desktopCases.length,desktopNativePlaneCases:2934,desktopNativePixels:proof.desktopCases.flatMap(c=>c.pixels).reduce((n,p)=>n+p.pixels,0),gpuSelections:proof.gpu.length,componentFoci:proof.componentFocusCoverage,mobileLevels:proof.mobileCases.length,applicationEntries:proof.wrapperCases.length,authenticationChecks:proof.authentication.length,invalidWindowRecoveryCases:proof.recovery.length};save();console.log(JSON.stringify({allPassed:true,...proof.summary}));
  }finally{await browser.close();}
})().catch(error=>{proof.errors.push(String(error.stack||error));save();console.error(error);process.exitCode=1;});
