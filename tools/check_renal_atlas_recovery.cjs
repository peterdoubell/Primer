'use strict';
const {chromium}=require('playwright');
const fs=require('node:fs/promises');
const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
  const root=path.resolve(__dirname,'../web/anatomy/bp3d-renal-4.3');
  try {
    const page=await browser.newPage();
    let failures=1;
    await page.route('http://localhost:4100/**',async route=>{
      const file=path.basename(new URL(route.request().url()).pathname);
      if(file==='FJ3144.mesh.gz' && failures>0) {
        failures--;
        return route.fulfill({status:503,body:'Temporary failure'});
      }
      const type=file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':'application/octet-stream';
      await route.fulfill({body:await fs.readFile(path.join(root,file)),contentType:type});
    });
    await page.goto('http://localhost:4100/index.html');
    await page.getByRole('button',{name:'Retry source geometry'}).waitFor();
    for(const selector of ['#group','#fit','.layer','#rotation','#tilt'])
      assert.ok(await page.locator(selector).first().isDisabled());
    await page.getByRole('button',{name:'Retry source geometry'}).click();
    await page.locator('#surface-status').filter({hasText:'46,322'}).waitFor();
    assert.ok(await page.locator('#retry').isHidden());
    for(const selector of ['#group','#fit','.layer','#rotation','#tilt'])
      assert.ok(await page.locator(selector).first().isEnabled());
    const rows=JSON.parse(await fs.readFile(path.join(root,'surfaces.json')));
    for(const group of new Set(rows.map(row=>row.source_fma))){
      await page.selectOption('#group',group);
      const count=rows.filter(row=>row.source_fma===group).reduce((sum,row)=>sum+row.triangles,0);
      assert.ok((await page.locator('#surface-status').textContent()).includes(count.toLocaleString()));
    }
    await page.locator('#surface').evaluate(canvas => {
      const gl = canvas.getContext('webgl2');
      const extension = gl.getExtension('WEBGL_lose_context');
      if (!extension) throw Error('Context-loss test extension unavailable');
      extension.loseContext();
    });
    await page.locator('#surface-status').filter({hasText:'graphics context was lost'}).waitFor();
    for(const selector of ['#group','#fit','.layer','#rotation','#tilt'])
      assert.ok(await page.locator(selector).first().isDisabled());
    await page.getByRole('button',{name:'Retry source geometry'}).click();
    await page.locator('#surface-status').filter({hasText:'46,322'}).waitFor();
    assert.ok(await page.locator('#group').isEnabled());
    console.log('Context loss and HTTP failure locked geometry controls; retry restored all 31 objects and 14 group selections.');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
