const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
(async()=>{
 const b=await chromium.launch({args:['--enable-unsafe-swiftshader']});
 try{
  const p=await b.newPage(),errors=[],root=path.resolve('web/anatomy/liver-regions-mri');
  let metadataFailure=true,pixelFailure=true;
  p.on('pageerror',error=>errors.push(error.message));
  await p.route('https://liver.test/**',route=>{
   const file=path.basename(new URL(route.request().url()).pathname);
   if(metadataFailure&&file==='volume.json'){metadataFailure=false;return route.fulfill({body:'{}'});}
   if(pixelFailure&&/^mri-\d+.gz$/.test(file)){pixelFailure=false;return route.fulfill({body:Buffer.from('corrupt')});}
   return route.fulfill({body:fs.readFileSync(path.join(root,file)),contentType:file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':file.endsWith('.css')?'text/css':'application/octet-stream'});
  });
  await p.goto('https://liver.test/index.html');
  const retry=p.getByRole('button',{name:'Retry MRI',exact:true});
  await retry.waitFor();assert.ok(await p.locator('#mri').isHidden());
  await p.locator('#surface-status').filter({hasText:/source triangles visible/}).waitFor();
  await p.locator('#region').selectOption('2');
  const rows=JSON.parse(fs.readFileSync(path.join(root,'surfaces.json')));
  await p.locator('#surface-status').filter({hasText:rows[1].triangles.toLocaleString()+' source triangles visible'}).waitFor();
  await retry.click();
  await p.locator('#status').filter({hasText:'Source samples could not be verified.'}).waitFor();
  assert.ok(await p.locator('#mri').isHidden());
  await retry.click();await p.locator('#status').filter({hasText:/^Verified source section/}).waitFor();
  assert.ok(await p.locator('#mri').isVisible());
  assert.equal(await p.locator('#region').inputValue(),'2');
  assert.deepEqual(errors,[]);
  console.log('Metadata and pixel corruption rejected; independent3D selection and MRI retry passed.');
 }finally{await b.close();}
})().catch(error=>{console.error(error);process.exitCode=1});
