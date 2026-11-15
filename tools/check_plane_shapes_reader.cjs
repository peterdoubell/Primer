'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto'),{chromium}=require('playwright');
const fixture=JSON.parse(fs.readFileSync(0,'utf8')),origin=new URL(fixture.url),root=path.join(__dirname,'..'),out=path.join(root,'docs/plane-shapes-review-20261023');
assert.equal(origin.hostname,'127.0.0.1');assert.equal(origin.protocol,'http:');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const browser=await chromium.launch({headless:true});const proof={scope:'Authenticated shapes lesson on isolated synthetic storage',productionVerified:false,allPassed:false,cases:[]};
 try{
  const anonymous=await browser.newContext();assert.equal((await anonymous.request.get(fixture.url+'/api/curriculum/node/math.0.shapes')).status(),401);await anonymous.close();
  for(const width of [390,1440]){
   const context=await browser.newContext({viewport:{width,height:1000},extraHTTPHeaders:{Authorization:'Basic '+Buffer.from(fixture.username+':'+fixture.password).toString('base64')}});
   assert.equal((await context.request.post(fixture.url+'/api/profile',{headers:{Origin:fixture.url},data:{name:'Synthetic shapes QA',age:5,domains:['math']}})).status(),200);
   await context.request.post(fixture.url+'/api/profile/settings',{headers:{Origin:fixture.url},data:{speak:false}});
   const r=await context.request.get(fixture.url+'/api/curriculum/node/math.0.shapes');assert.equal(r.status(),200);const body=await r.json(),node=body.node||body;
   assert.equal(node.quiz,undefined);const binding=node.lesson_media.find(m=>m.renderer==='spatial-3d'&&m.props?.scenario==='module.math.0.shapes');assert.equal(binding.props.family,'plane-shapes');
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));
   await page.route('**/*',route=>new URL(route.request().url()).origin===fixture.url?route.continue():route.abort());
   await page.addInitScript(()=>{window.shapeCSP=[];document.addEventListener('securitypolicyviolation',e=>window.shapeCSP.push(e.violatedDirective));});
   const pins=[];page.on('response',r=>{if(new URL(r.url()).pathname==='/app/startup.js')pins.push(r.body().then(b=>{const text=b.toString();assert(text.includes("define('plane-shapes'"));assert(text.includes("camera:family.camera ||"));return hash(b);}));});
   await page.goto(fixture.url+'/app/#/node/math.0.shapes');const model=page.locator('.spatial-model[data-scenario="module.math.0.shapes"]');await model.waitFor();
   assert.equal(await model.locator('h3').textContent(),binding.title);assert.equal(await page.locator('[data-renderer="shape-explorer"]').count(),1);
   for(const shape of ['circle','triangle','square','rectangle']){await model.getByLabel(/^Choose a shape/).selectOption(shape);assert((await model.locator('.spatial-readout').textContent()).includes(shape[0].toUpperCase()+shape.slice(1)+':'));}
   await model.getByRole('button',{name:'Reset model',exact:true}).click();assert.match(await model.locator('.spatial-readout').textContent(),/Circle: no straight sides and no corners/);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(await page.evaluate(()=>window.shapeCSP),[]);assert.deepEqual(errors,[]);
   await model.screenshot({path:path.join(out,'reader-'+width+'.png')});const startup=await Promise.all(pins);assert(startup.length>0);proof.cases.push({width,shapes:4,originalShapeWheelPreserved:true,reset:true,noOverflow:true,CSPViolations:[],pageErrors:[],startupSHA256:startup});await context.close();
  }
  proof.allPassed=true;fs.writeFileSync(path.join(out,'reader-proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
