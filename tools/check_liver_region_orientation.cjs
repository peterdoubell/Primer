const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
(async()=>{const b=await chromium.launch({args:['--enable-unsafe-swiftshader']});try{
const p=await b.newPage({viewport:{width:390,height:1000}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.route('https://liver.test/**',r=>{const n=path.basename(new URL(r.request().url()).pathname);return r.fulfill({body:fs.readFileSync(path.join('web/anatomy/liver-regions-mri',n)),contentType:n.endsWith('.js')?'text/javascript':n.endsWith('.css')?'text/css':n.endsWith('.html')?'text/html':'application/octet-stream'});});
await p.goto('https://liver.test/index.html');await p.locator('#surface-status').filter({hasText:/source triangles visible/}).waitFor();
for(const yaw of [-180,-90,-45,0,25,45,90,180])for(const pitch of [-90,-45,0,15,45,90]){
 await p.locator('#rotation').fill(String(yaw));await p.locator('#tilt').fill(String(pitch));
 const actual=await p.evaluate(()=>{const c=document.querySelector('#surface'),g=c.getContext('webgl2'),p=g.getParameter(g.CURRENT_PROGRAM);return {yaw:g.getUniform(p,g.getUniformLocation(p,'yaw')),pitch:g.getUniform(p,g.getUniformLocation(p,'pitch')),axes:[...document.querySelectorAll('.surface-orientation line')].map(e=>({name:e.dataset.axis,x:(Number(e.getAttribute('x2'))-110)/60,y:(90-Number(e.getAttribute('y2')))/60,z:Number(e.dataset.depth)}))};});
 // Independently transform the three patient unit vectors through yaw and pitch.
 const angle=yaw*Math.PI/180,tilt=pitch*Math.PI/180;
 assert.ok(Math.abs(actual.yaw-angle)<1e-6&&Math.abs(actual.pitch-tilt)<1e-6);
 for(const [i,v] of [[1,0,0],[0,1,0],[0,0,1]].entries()){
  const horizontal=[Math.cos(angle),-Math.sin(angle),0],depth=[Math.sin(angle),Math.cos(angle),0];
  const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),d=dot(depth,v);
  const expected=[dot(horizontal,v),Math.cos(tilt)*v[2]-Math.sin(tilt)*d,Math.sin(tilt)*v[2]+Math.cos(tilt)*d];
  for(const [k,key]of ['x','y','z'].entries())assert.ok(Math.abs(actual.axes[i][key]-expected[k])<1e-12);
 }
}
for(const selected of ['0','1','4','8']){await p.locator('#region').selectOption(selected);const keys=await p.locator('.region-key li').allTextContents();assert.equal(keys.length,8);assert.equal(keys.filter(s=>s.endsWith('— shown')).length,selected==='0'?8:1);}
await p.locator('#rotation').fill('25');await p.locator('#tilt').fill('15');await p.locator('#region').selectOption('0');
await p.locator('#status').filter({hasText:/^Verified source section/}).waitFor();
await p.setViewportSize({width:1440,height:1000});
await p.setViewportSize({width:320,height:900});assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
const lost=p.locator('#surface');await lost.evaluate(c=>{const ext=c.getContext('webgl2').getExtension('WEBGL_lose_context');window.recover=()=>ext.restoreContext();ext.loseContext();});
await p.locator('.surface-orientation').waitFor({state:'hidden'});assert.equal(await p.locator('.region-key li').count(),0);
await p.evaluate(()=>window.recover());await p.locator('#surface-status').filter({hasText:/source triangles visible/}).waitFor();assert.equal(await p.locator('.surface-orientation line').count(),3);assert.equal(await p.locator('.region-key li').count(),8);
assert.deepEqual(errors,[]);console.log('48 rotations match shader uniforms and independent patient-axis projection; colour key, mobile layout and context recovery passed.');
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
