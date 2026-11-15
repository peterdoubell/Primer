const {chromium}=require('playwright'),fs=require('fs'),assert=require('assert/strict');
(async()=>{
 const f=JSON.parse(fs.readFileSync(0,'utf8'));assert.ok(/^http:\/\/127\.0\.0\.1:\d+$/.test(f.url));
 const b=await chromium.launch({args:['--enable-unsafe-swiftshader']});try{
 const auth={Authorization:'Basic '+Buffer.from(f.username+':'+f.password).toString('base64')};
 const c=await b.newContext({httpCredentials:{username:f.username,password:f.password},viewport:{width:390,height:900}});
 assert.ok((await c.request.post(f.url+'/api/profile',{headers:{...auth,Origin:f.url},data:{name:'Synthetic hepatic source links',age:30,domains:['radiology']}})).ok());
 await c.route(f.url+'/**',r=>r.continue({headers:{...r.request().headers(),...auth}}));
 const p=await c.newPage(),errors=[],bindings=JSON.parse(fs.readFileSync('docs/hepatic-vessel-navigation/bindings.json'));p.on('pageerror',e=>errors.push(e.message));
 for(const [route,id]of [['node','rad.4.liver'],['radiology','ra.liver-masses'],['radiology','ra.liver-lirads']]){
  await p.goto(f.url+'/app/#/'+route+'/'+id);
  const panel=p.getByRole('region',{name:'Liver region source study',exact:true});await panel.waitFor();
  assert.match(await panel.textContent(),/different person/);assert.match(await panel.textContent(),/not registered/);
  const urls=await panel.locator('a').evaluateAll(a=>a.map(e=>({text:e.textContent,href:e.href})));
  assert.equal(urls.filter(row => !['phlf-center2-24','hva-ct-318'].some(atlas => new URL(row.href).pathname.startsWith('/app/anatomy/'+atlas+'/'))).length,5);
  for(const row of bindings){
   const url=urls.find(u=>u.text===row.title);assert.ok(url);assert.equal(new URL(url.href).searchParams.get('from'),id);
   await p.goto(url.href);
   await p.locator('#status').filter({hasText:/^Verified source section/}).waitFor();
   assert.equal(await p.locator('#segment option:checked').getAttribute('data-source'),row.layer+':'+row.value);
   await p.locator('#surface-status').filter({hasText:row.triangles.toLocaleString()+' source triangles visible'}).waitFor();
   const actual=await p.locator('#surface').evaluate(async canvas=>{
    const gl=canvas.getContext('webgl2'),program=gl.getParameter(gl.CURRENT_PROGRAM),a=gl.getAttribLocation(program,'position');gl.bindBuffer(gl.ARRAY_BUFFER,gl.getVertexAttrib(a,gl.VERTEX_ATTRIB_ARRAY_BUFFER_BINDING));
    const v=new Uint8Array(gl.getBufferParameter(gl.ARRAY_BUFFER,gl.BUFFER_SIZE)),i=new Uint8Array(gl.getBufferParameter(gl.ELEMENT_ARRAY_BUFFER,gl.BUFFER_SIZE));gl.getBufferSubData(gl.ARRAY_BUFFER,0,v);gl.getBufferSubData(gl.ELEMENT_ARRAY_BUFFER,0,i);const bytes=new Uint8Array(v.length+i.length);bytes.set(v);bytes.set(i,v.length);return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
   });assert.equal(actual,row.modelSHA256);
   assert.equal(await p.locator('#return-context').getAttribute('href'),'/app/#/'+route+'/'+id);
   await p.locator('#return-context').click();await panel.waitFor();
  }
 }
 assert.deepEqual(errors,[]);console.log('Twelve hepatic source entry/return paths passed; all four exact GPU models and source selections verified from each liver reference.');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
