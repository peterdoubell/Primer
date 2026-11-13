const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
(async()=>{
 const b=await chromium.launch({args:['--enable-unsafe-swiftshader']});
 try{
  const fixture=JSON.parse(fs.readFileSync(0,'utf8'));
  assert.ok(/^http:\/\/127\.0\.0\.1:\d+$/.test(fixture.url), 'Synthetic profile checks require loopback');
  const auth={Authorization:'Basic '+Buffer.from(fixture.username+':'+fixture.password).toString('base64')};
  const context=await b.newContext({httpCredentials:{username:fixture.username,password:fixture.password},viewport:{width:390,height:900}});
  assert.ok((await context.request.post(fixture.url+'/api/profile',{headers:{...auth,Origin:fixture.url},data:{name:'Synthetic liver region study',age:30,domains:['radiology']}})).ok());
  await context.route(fixture.url+'/**',r=>r.continue({headers:{...r.request().headers(),...auth}}));
  const p=await context.newPage(),errors=[];
  p.on('pageerror',e=>errors.push(e.message));
  await p.goto(fixture.url+'/app/#/node/rad.4.liver');
  await p.getByRole('link',{name:'Inspect liver regions on source MRI'}).click();
  const ready=()=>p.locator('#status').filter({hasText:/^Verified source section/}).waitFor();
  await ready();await p.locator('#surface-status').filter({hasText:/source triangles visible/}).waitFor();
  const expected=JSON.parse(fs.readFileSync(path.resolve('docs/liver-regions-integration/expected-raster-hashes.json')));
  for(const row of expected){
   await p.locator('#region').selectOption(String(row.region));
   await p.locator('#overlay').setChecked(row.overlay);
   await p.locator('#slice').fill(String(row.slice));await ready();
   const hash=await p.locator('#mri').evaluate(async canvas=>{
    const pixels=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
    return [...new Uint8Array(await crypto.subtle.digest('SHA-256',pixels))].map(v=>v.toString(16).padStart(2,'0')).join('');
   });
   assert.equal(hash,row.sha256,JSON.stringify(row));
  }
  const models=JSON.parse(fs.readFileSync(path.resolve('web/anatomy/liver-regions-mri/surfaces.json')));
  for(const row of models){
   await p.locator('#region').selectOption(String(row.label));await ready();
   const hash=await p.locator('#surface').evaluate(async canvas=>{
    const gl=canvas.getContext('webgl2'),program=gl.getParameter(gl.CURRENT_PROGRAM),a=gl.getAttribLocation(program,'position');
    gl.bindBuffer(gl.ARRAY_BUFFER,gl.getVertexAttrib(a,gl.VERTEX_ATTRIB_ARRAY_BUFFER_BINDING));
    const v=new Uint8Array(gl.getBufferParameter(gl.ARRAY_BUFFER,gl.BUFFER_SIZE)),i=new Uint8Array(gl.getBufferParameter(gl.ELEMENT_ARRAY_BUFFER,gl.BUFFER_SIZE));
    gl.getBufferSubData(gl.ARRAY_BUFFER,0,v);gl.getBufferSubData(gl.ELEMENT_ARRAY_BUFFER,0,i);
    const bytes=new Uint8Array(v.length+i.length);bytes.set(v);bytes.set(i,v.length);
    return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
   });
   assert.equal(hash,row.sha256);
  }
  for(const zoom of ['fit','1','2']){await p.locator('#zoom').selectOption(zoom);assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
  await p.locator('#white').fill('0');assert.ok(await p.locator('#mri').isHidden());
  await p.locator('#white').fill('1800');await ready();
  for(const width of [320,390,1440]){await p.setViewportSize({width,height:900});assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
  for(const id of ['ra.liver-masses','ra.liver-lirads']){
    await p.goto(fixture.url+'/app/#/radiology/'+id);
    await p.getByRole('link',{name:'Inspect liver regions on source MRI'}).click();
    await ready();
    assert.equal(await p.locator('#return-context').getAttribute('href'),'/app/#/radiology/'+id);
  }
  assert.deepEqual(errors,[]);
  console.log('All76 MRI planes,9 label-outline states,8 exact GPU models, source scaling, zoom and responsive layouts passed.');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
