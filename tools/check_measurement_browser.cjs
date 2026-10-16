'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'docs/measurement-fidelity-review-20261016/browser');
fs.mkdirSync(out,{recursive:true});
const media=JSON.parse(fs.readFileSync(path.join(root,'data/curriculum/03-physics.json'))).nodes.find(n=>n.id==='phys.4.experiment').lesson_media.find(m=>m.renderer==='physics-concept-lab');
const near=(a,b,r=1e-8)=>assert.ok(Math.abs(a-b)<=r*Math.max(1,Math.abs(b)),`${a} != ${b}`);
const digest=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function qr(rows){const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),u=rows.map(r=>1/r.sigma),x=rows.map(r=>r.x/r.sigma),y=rows.map(r=>r.y/r.sigma),r00=Math.sqrt(dot(u,u)),q0=u.map(v=>v/r00),r01=dot(q0,x),z=x.map((v,i)=>v-r01*q0[i]),r11=Math.sqrt(dot(z,z)),q1=z.map(v=>v/r11),slope=dot(q1,y)/r11;return {slope,intercept:(dot(q0,y)-r01*slope)/r00};}
(async()=>{const browser=await chromium.launch({headless:true}),proof={scope:'Standalone current renderer and supplied model-frame contract; no authenticated or production flow claim',sourceSHA256:digest(path.join(root,'web/measurement-lab.js')),curriculumSHA256:digest(path.join(root,'data/curriculum/03-physics.json')),states:[],errors:[],controlChecks:0};try{
 for(const width of [390,1440]){
  const page=await browser.newPage({viewport:{width,height:1000}});page.on('pageerror',e=>proof.errors.push(e.message));
  await page.setContent('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:12px"><main style="max-width:1100px;margin:auto" id="root"></main></body></html>');await page.addStyleTag({path:path.join(root,'web/styles.css')});await page.addScriptTag({path:path.join(root,'web/measurement-lab.js')});
  await page.evaluate(item=>document.querySelector('main').append(window.PrimerMeasurementLab.render(item)),media);
  async function station(key){await page.locator('[data-measurement-control="station"]').selectOption(key);}
  async function set(key,value){const w=page.locator('[data-measurement-control="'+key+'"]');if(await w.evaluate(e=>e.tagName==='SELECT'))await w.selectOption(String(value));else if(await w.getAttribute('type')==='checkbox')await w.setChecked(Boolean(value));else{await w.fill(String(value));await w.dispatchEvent('change');}proof.controlChecks++;}
  async function capture(name){
   const state=await page.locator('[data-measurement-lab]').evaluate(e=>e.measurement.getState());
   const graphics=await page.locator('[data-measurement-panel="'+state.station+'"] [data-measurement-plot]').evaluateAll(svgs=>svgs.map(svg=>({title:svg.dataset.measurementPlot,domain:JSON.parse(svg.dataset.axisDomain),points:[...svg.querySelectorAll('[data-fit-point]')].map(e=>({i:Number(e.dataset.fitPoint),x:Number(e.getAttribute('cx')),y:Number(e.getAttribute('cy'))})),bars:[...svg.querySelectorAll('[data-fit-errorbar]')].map(e=>({i:Number(e.dataset.fitErrorbar),x1:+e.getAttribute('x1'),x2:+e.getAttribute('x2'),y1:+e.getAttribute('y1'),y2:+e.getAttribute('y2')})),residuals:[...svg.querySelectorAll('[data-fit-residual]')].map(e=>({i:+e.dataset.fitResidual,x:+e.getAttribute('cx'),y:+e.getAttribute('cy')})),lines:[...svg.querySelectorAll('[data-fit-line],[data-bound-line],[data-repeat-floor]')].map(e=>({kind:e.dataset.fitLine||e.dataset.boundLine||'floor',x1:+e.getAttribute('x1'),x2:+e.getAttribute('x2'),y1:+e.getAttribute('y1'),y2:+e.getAttribute('y2')})),variance:[...svg.querySelectorAll('[data-variance-index]')].map(e=>({i:+e.dataset.varianceIndex,y:+e.getAttribute('y'),h:+e.getAttribute('height')})),curves:[...svg.querySelectorAll('[data-repeat-curve]')].map(e=>({kind:e.dataset.repeatCurve,points:e.getAttribute('points').split(' ').map(x=>x.split(',').map(Number))})),texts:[...svg.querySelectorAll('text')].map(e=>{const b=e.getBBox(),m=svg.getScreenCTM().inverse().multiply(e.getScreenCTM()),points=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(([x,y])=>new DOMPoint(x,y).matrixTransform(m)),xs=points.map(p=>p.x),ys=points.map(p=>p.y);return{text:e.textContent,x:Math.min(...xs),y:Math.min(...ys),w:Math.max(...xs)-Math.min(...xs),h:Math.max(...ys)-Math.min(...ys)}})})));
   const map=(g,x,y)=>[g.domain.left+(x-g.domain.x[0])/(g.domain.x[1]-g.domain.x[0])*(g.domain.right-g.domain.left),g.domain.bottom-(y-g.domain.y[0])/(g.domain.y[1]-g.domain.y[0])*(g.domain.bottom-g.domain.top)];
   for(const g of graphics)for(const t of g.texts)assert.ok(t.x>=-1&&t.x+t.w<=681&&t.y>=-1&&t.y+t.h<=361,`${g.title}: text bounds ${JSON.stringify(t)}`);
   let checked=0;
   if(state.station==='fit'){
    const s=state.fit,noise=[-.7,.25,.9,-.35,.5,-.8,.1,.65,-.45,.3,-.15,.75],rows=noise.map((r,i)=>({x:i,y:1+.5*i+s.offset+.5*s.acceleration*i*i+s.scatter*r+(i===8?s.outlier:0),sigma:s.sigma*(s.heterogeneous?1+i/11:1)})),fit=s.mode==='reference'?{intercept:1,slope:.5}:qr(rows),g=graphics[0],resid=graphics[1];
    assert.equal(g.points.length,12);assert.equal(g.bars.length,12);assert.equal(resid.residuals.length,12);
    for(const p of g.points){const expected=map(g,rows[p.i].x,rows[p.i].y);near(p.x,expected[0]);near(p.y,expected[1]);assert.ok(p.x>=g.domain.left&&p.x<=g.domain.right&&p.y>=g.domain.top&&p.y<=g.domain.bottom);checked++;}
    for(const b of g.bars){const r=rows[b.i],lo=map(g,r.x,r.y-r.sigma),hi=map(g,r.x,r.y+r.sigma);near(b.x1,lo[0]);near(b.x2,hi[0]);near(b.y1,lo[1]);near(b.y2,hi[1]);assert.ok(b.y1<=g.domain.bottom&&b.y2>=g.domain.top);checked++;}
    for(const p of resid.residuals){const r=rows[p.i],expected=map(resid,r.x,(r.y-fit.intercept-fit.slope*r.x)/r.sigma);near(p.x,expected[0]);near(p.y,expected[1]);checked++;}
    const line=g.lines.find(x=>x.kind==='fitted'),a=map(g,0,fit.intercept),b=map(g,11,fit.intercept+11*fit.slope);near(line.x1,a[0]);near(line.y1,a[1]);near(line.x2,b[0]);near(line.y2,b[1]);checked++;
   }else if(state.station==='propagation'){
    const s=state.propagation,g=graphics[0],gradient=s.operation==='sum'?[1,1]:s.operation==='difference'?[1,-1]:s.operation==='ratio'?[1/s.b,-s.a/s.b**2]:[4*Math.PI**2/s.b**2,-8*Math.PI**2*s.a/s.b**3];const A=gradient[0]*s.ua,B=gradient[1]*s.ub,vals=[A*A,B*B,2*A*B*s.rho,A*A+B*B+2*A*B*s.rho];
    assert.equal(g.variance.length,4);for(const b of g.variance){const zero=map(g,b.i,0)[1],y=map(g,b.i,vals[b.i])[1];near(b.y,Math.min(zero,y));near(b.h,Math.abs(y-zero));checked++;}
   }else if(state.station==='bounds'){
    const s=state.bounds,g=graphics[0],f=(a,b)=>s.operation==='sum'?a+b:s.operation==='difference'?a-b:s.operation==='ratio'?a/b:4*Math.PI**2*a/b**2,ends=[f(s.a-s.da,s.b-s.db),f(s.a-s.da,s.b+s.db),f(s.a+s.da,s.b-s.db),f(s.a+s.da,s.b+s.db)],line=g.lines.find(x=>x.kind==='exact'),a=map(g,Math.min(...ends),1),b=map(g,Math.max(...ends),1);near(line.x1,a[0]);near(line.y1,a[1]);near(line.x2,b[0]);near(line.y2,b[1]);checked++;
   }else if(state.station==='repeats'){
    const s=state.repeats,g=graphics[0];for(const curve of g.curves){assert.equal(curve.points.length,400);curve.points.forEach((p,i)=>{const n=i+1,q=s.resolutionMode==='included-in-scatter'?0:s.resolution**2/12/(s.resolutionMode==='independent-uniform'?n:1),u=curve.kind==='scatter'?s.readingStd/Math.sqrt(n):Math.sqrt(s.readingStd**2/n+s.calibrationStd**2+q),v=map(g,n,u);near(p[0],v[0]);near(p[1],v[1]);checked++;});}
   }
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'No page horizontal overflow');
   proof.states.push({width,name,station:state.station,geometryChecks:checked,plotCount:graphics.length,allPlotTextInsideViewBox:true,noHorizontalPageOverflow:true});
  }
  await capture('authored fit');
  for(const name of ['Small reduced χ²','Hidden common offset','Wrong constant-speed model','Keep a large outlier']){await page.getByRole('button',{name,exact:true}).click();await capture(name);}
  await set('fit.mode','reference');await capture('fixed-reference comparison');
  await station('propagation');for(const name of ['Independent voltage sum','Speed: 1% and 2%','Shared offset cancels','Period: 1% gives 2%']){await page.getByRole('button',{name,exact:true}).click();await capture(name);}
  await page.getByRole('button',{name:'Speed: 1% and 2%',exact:true}).click();for(const rho of [-1,-.4,0,.7,1]){await set('propagation.rho',rho);await capture('speed covariance '+rho);}
  await station('bounds');for(const name of ['Small speed bounds','Large denominator range','Equal voltage bounds']){await page.getByRole('button',{name,exact:true}).click();await capture(name);}
  await station('repeats');for(const name of ['Use five-reading example','400 readings, uncorrected bias','Correct offset, retain uncertainty','Identical rounding phase','Independent rounding phases']){await page.getByRole('button',{name,exact:true}).click();await capture(name);}
  // Exercise every native numeric field and option; intentionally invalid domains
  // display an error without retaining a stale plot or throwing a page error.
  for(const key of ['fit','propagation','bounds','repeats']){
   await station(key);await page.getByRole('button',{name:'Enlarge plots',exact:true}).click();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.ok(await page.locator('[data-measurement-panel="'+key+'"] [data-measurement-plot]').first().evaluate(e=>e.getBoundingClientRect().width>=899));await page.getByRole('button',{name:'Fit plots',exact:true}).click();
   const numeric=await page.locator('[data-measurement-panel="'+key+'"] input[type=number]').evaluateAll(inputs=>inputs.map(e=>({key:e.dataset.measurementControl,value:e.value,min:e.min,max:e.max})));
   for(const row of numeric){await set(row.key,row.max);const output=page.locator('[data-measurement-panel="'+key+'"]');if(!await output.getAttribute('data-error'))await capture(row.key+' maximum');else assert.equal(await output.locator('svg').count(),0);await set(row.key,row.value);}
  }
  await station('propagation');await set('propagation.b','');assert.match(await page.locator('[data-measurement-panel="propagation"]').textContent(),/Invalid input/);assert.equal(await page.locator('[data-measurement-panel="propagation"] svg').count(),0);await set('propagation.b',2);await capture('blank input recovery');
  await station('bounds');await page.getByRole('button',{name:'Small speed bounds',exact:true}).click();await set('bounds.db',2);assert.equal(await page.locator('[data-measurement-panel="bounds"] svg').count(),0);await set('bounds.db',.04);await capture('denominator-domain recovery');
  await page.getByRole('button',{name:'Reset workbench',exact:true}).click();assert.deepEqual(await page.locator('[data-measurement-lab]').evaluate(e=>e.measurement.getState()),require(path.join(root,'web/measurement-lab.js')).defaults);await capture('reset');
  const accessible=await page.locator('[data-measurement-lab] input,[data-measurement-lab] select').evaluateAll(inputs=>inputs.every(e=>Boolean(e.labels?.length)));assert.equal(accessible,true);
  for(const key of ['fit','propagation','bounds','repeats']){await station(key);await page.locator('[data-measurement-lab]').screenshot({path:path.join(out,key+'-'+width+'.png')});}
  await page.locator('[data-measurement-control="station"]').focus();await page.keyboard.press('Home');await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');assert.ok(await page.locator('[role=status]').textContent());
  await page.evaluate(item=>{const div=document.createElement('section'),canvas=document.createElement('div'),controls=document.createElement('div'),readout=document.createElement('p'),status=document.createElement('p');div.append(canvas,controls,readout,status);document.querySelector('main').append(window.PrimerMeasurementLab.render(item,{}, {root:div,canvas,controls,readout,status}));},media);
  assert.equal(await page.locator('[data-measurement-lab]').count(),2);assert.equal(await page.evaluate(()=>{const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);return ids.length===new Set(ids).size;}),true);assert.equal(await page.evaluate(()=>window.PrimerMeasurementLab.render({props:{scenario:'phys.3.nuclear'}})),null);await page.close();
 }
 assert.deepEqual(proof.errors,[]);proof.geometryChecks=proof.states.reduce((s,x)=>s+x.geometryChecks,0);proof.allPassed=true;fs.writeFileSync(path.join(out,'proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify({states:proof.states.length,geometryChecks:proof.geometryChecks,controlChecks:proof.controlChecks,pageErrors:proof.errors.length}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
