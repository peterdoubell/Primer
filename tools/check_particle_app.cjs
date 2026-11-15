'use strict';
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'docs/physics-particle-review-20261102/reader');
const fixture=JSON.parse(fs.readFileSync(0,'utf8')),origin=new URL(fixture.url).origin;
assert.equal(new URL(origin).hostname,'127.0.0.1');fs.mkdirSync(D,{recursive:true});
const auth={Authorization:'Basic '+Buffer.from(fixture.username+':'+fixture.password).toString('base64')};
(async()=>{
 const b=await chromium.launch({headless:true}),cases=[],errors=[];let independentMounts=0,staleResponseChecks=0;
 try{
  for(const width of [390,1440]){
   const c=await b.newContext({viewport:{width,height:1000}});
   await c.route(origin+'/**',r=>r.continue({headers:{...r.request().headers(),...auth}}));
   await c.route('**/*',r=>new URL(r.request().url()).origin===origin?r.fallback():r.abort());
   const p=await c.newPage();p.setDefaultTimeout(120000);p.on('pageerror',e=>errors.push(e.message));
   await c.request.post(origin+'/api/profile',{headers:{...auth,Origin:origin},data:{name:'Synthetic particle QA',age:30,domains:['physics']}});
   await c.request.post(origin+'/api/profile/settings',{headers:{...auth,Origin:origin},data:{speak:false}});
   await p.goto(origin+'/app/#/node/phys.4.particles');
   const root=p.locator('.physics-particle-lab');await root.waitFor();assert.equal(await root.count(),1);
   const role=k=>root.locator('[data-particle-role="'+k+'"]');
   for(const fraction of [0,.01,.3027394222947579,.5,.99,1])for(const cosine of [-1,0,1]){
    for(const[k,v]of Object.entries({fraction,cosine}))if(await role(k).isEnabled()){
     await role(k).fill(String(v));await role(k).dispatchEvent('change');
    }
    await role('rotate').click();await role('tilt').click();
    const row=await root.evaluate(r=>({...r.particleReview,
     lines:[...r.querySelectorAll('[data-vector]')].map(e=>({name:e.dataset.vector,source:JSON.parse(e.dataset.source),...Object.fromEntries(['x1','y1','x2','y2'].map(k=>[k,Number(e.getAttribute(k))]))})),
     zeroVectors:[...r.querySelectorAll('[data-zero-vector]')].map(e=>e.dataset.zeroVector),
     overflow:document.documentElement.scrollWidth>innerWidth+1}));
    assert(!row.overflow);assert(row.displayed);assert(row.audit.numbersBalance);
    if(fraction===0)assert(row.zeroVectors.includes('electron'));
    if(fraction===1){assert(row.zeroVectors.includes('neutrino'));assert(row.event.zeroNeutrinoEnergyLimit);}
    if(fraction===.3027394222947579&&cosine===-1){assert(row.zeroVectors.includes('proton'));assert.equal(row.event.protonDirectionResolved,false);assert((await role('limit').textContent()).includes('below numerical direction resolution'));}
    cases.push({width,...row});
   }
   await role('reset').click();await role('rotate').click();await role('face').click();
   assert(await root.evaluate(r=>r.particleReview.yaw===0&&Math.abs(r.particleReview.pitch-(r.particleReview.state.azimuth-Math.PI/2))<1e-15));
   const scale=await role('momentum').evaluate(e=>{const line=[...e.querySelectorAll('line')].find(l=>Number(l.getAttribute('y1'))===445);return{length:Number(line.getAttribute('x2'))-Number(line.getAttribute('x1')),label:e.querySelector('text').textContent};});
   assert.equal(scale.length,180);assert.equal(scale.label,'1 MeV/c');
   await role('fraction').fill('1');await role('fraction').dispatchEvent('change');
   for(const k of ['cosine','azimuth','face'])assert(await role(k).isDisabled());
   await role('reset').click();assert(await role('cosine').isEnabled());
   for(const invalid of ['', '-1','2']){await role('fraction').fill(invalid);await role('fraction').dispatchEvent('change');assert.equal(await role('fraction').inputValue(),'0.5');}
   for(const channel of ['1','2','3']){
    await role('channel').selectOption(channel);assert(await role('kinematics').isHidden());assert.equal(await root.locator('[data-vector]').count(),0);
    const audit=await root.evaluate(r=>r.particleReview.audit);assert.equal(audit.checksPass,false);
    if(channel==='1')assert.equal(audit.differences.electronLepton,1);
    else if(channel==='2'){assert(audit.numbersBalance);assert(audit.restEnergyBudgetMeV<0);}
    else {assert.equal(audit.differences.baryonThirds,-3);assert.equal(audit.differences.chargeThirds,0);assert.equal(audit.differences.electronLepton,0);assert(audit.restEnergyBudgetMeV>0);}
   }
   await role('channel').selectOption('0');await role('reset').click();
   assert((await root.evaluate(r=>r.getModelSpeech())).includes('momentum'));
   await p.addStyleTag({content:'#sidebar {position:relative !important}'});
   await root.screenshot({path:path.join(D,'reader-'+width+'.png')});
   const multi=await p.evaluate(async()=>{
    const item={props:{scenario:'phys.4.particles'}},a=PrimerParticleLab.render(item),b=PrimerParticleLab.render(item);
    document.body.append(a,b);await new Promise(resolve=>requestAnimationFrame(resolve));
    const input=a.querySelector('[data-particle-role="fraction"]');input.value='.25';input.dispatchEvent(new Event('change'));
    const separate=a.particleReview.state.fraction===.25&&b.particleReview.state.fraction===.5;
    a.remove();b.remove();await new Promise(resolve=>requestAnimationFrame(resolve));
    return separate&&a.dataset.disposed==='true'&&b.dataset.disposed==='true'&&PrimerParticleLab.render({props:{scenario:'phys.5.qft'}})===null;
   });assert(multi);independentMounts+=2;
   await root.evaluate(r=>window.removedParticle=r);await p.goto(origin+'/app/#/node/phys.5.condensed');
   await p.waitForFunction(()=>removedParticle.dataset.disposed==='true');
   await p.locator('.physics-condensed-lab').waitFor();
   await p.goto(origin+'/app/#/node/phys.4.particles');try{await root.waitFor({timeout:30000});}catch(e){fs.writeFileSync(path.join(D,'failure.json'),JSON.stringify({width,url:p.url(),errors,body:await p.locator('body').innerText()},null,2));await p.screenshot({path:path.join(D,'failure.png'),fullPage:true});throw e;}assert.equal(await role('fraction').inputValue(),'0.5');
   for(const failure of [false,true]){
    let requested,release,finished;const seen=new Promise(r=>requested=r),hold=new Promise(r=>release=r),done=new Promise(r=>finished=r);
    const endpoint=origin+'/api/curriculum/node/phys.5.condensed';
    const delayed=async route=>{
     const response=failure?null:await route.fetch({headers:{...route.request().headers(),...auth}});
     requested();await hold;
     if(failure)await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Synthetic delayed failure'})});
     else await route.fulfill({response});
     finished();
    };
    await p.route(endpoint,delayed);
    await p.goto(origin+'/app/#/node/phys.5.condensed');await seen;
    await p.goto(origin+'/app/#/node/phys.4.particles');await root.waitFor();
    release();await done;await p.waitForLoadState('networkidle');
    const observed=await p.evaluate(()=>({particle:document.querySelectorAll('.physics-particle-lab').length,condensed:document.querySelectorAll('.physics-condensed-lab').length,title:document.querySelector('#page .pagehead h2')?.textContent||null}));
    if(observed.particle!==1||observed.condensed!==0){const diag=path.join(D,'../diagnostics');fs.mkdirSync(diag,{recursive:true});fs.writeFileSync(path.join(diag,'stale-route-observed-failure.json'),JSON.stringify({width,failure,observed,appSHA256:crypto.createHash('sha256').update(fs.readFileSync(path.join(R,'web/app.js'))).digest('hex')},null,2)+'\n');}
    assert.equal(observed.particle,1);assert.equal(observed.condensed,0);assert.equal(observed.title,'Particle Physics');
    staleResponseChecks++;await p.unroute(endpoint,delayed);
   }
   await c.close();
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(D,'browser-cases.json'),JSON.stringify(cases,null,2)+'\n');
  const sources=['web/physics-particle-core.js','web/physics-particle-ledger.js','web/physics-particle-lab.js','web/physics-particle-lab.css','web/lesson-models.js','web/index.html','web/app.js','primer/curriculum.py','data/curriculum/03-physics.json'];
  fs.writeFileSync(path.join(D,'browser-proof.json'),JSON.stringify({allPassed:true,authenticatedSyntheticApp:true,productionLearnerWrites:false,productionAuthenticatedReaderVerified:false,cases:cases.length,independentMounts,routeReopenChecks:2,staleResponseChecks,errors,sourceSHA256:Object.fromEntries(sources.map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(R,n))).digest('hex')])),wholeGoalComplete:false},null,2)+'\n');
  console.log({allPassed:true,cases:cases.length,independentMounts,routeReopenChecks:2});
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
