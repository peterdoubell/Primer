'use strict';
const {chromium}=require('playwright');
const fs=require('node:fs/promises');
const path=require('node:path');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
(async()=>{
  const root=path.resolve(__dirname,'../web/reference-studies/mullerian-2025');
  const browser=await chromium.launch();
  try{
    const page=await browser.newPage({viewport:{width:320,height:900}});
    let corrupt=true;
    await page.route('http://localhost:4100/**',async route=>{
      const file=path.basename(new URL(route.request().url()).pathname);
      const asset=file==='radiology-detailed-anatomy.js'?path.join(root,'../../',file):path.join(root,file);
      let body=await fs.readFile(asset);
      if(file.endsWith('Fig9_HTML.png')&&corrupt){body=Buffer.from(body);body[body.length-1]^=1;corrupt=false;}
      const contentType=file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':file.endsWith('.json')?'application/json':'image/png';
      await route.fulfill({body,contentType});
    });
    await page.goto('http://localhost:4100/index.html');
    await page.getByRole('button',{name:'Retry figure'}).waitFor();
    assert.ok(await page.locator('#image').isHidden());
    await page.getByRole('button',{name:'Retry figure'}).click();
    await page.locator('#status').filter({hasText:'Original Figure 9'}).waitFor();
    const figures=JSON.parse(await fs.readFile(path.join(root,'figures.json'))).figures;
    for(const figure of figures){
      await page.selectOption('#figure',figure.id);
      await page.locator('#status').filter({hasText:'Original Figure '+figure.id}).waitFor();
      const data=(await page.locator('#image').getAttribute('src')).split(',')[1];
      assert.equal(crypto.createHash('sha256').update(Buffer.from(data,'base64')).digest('hex'),figure.sha256);
      for(const scale of ['fit','1','2']){
        await page.selectOption('#zoom',scale);
        const size=await page.locator('#image').evaluate(image=>({width:image.getBoundingClientRect().width,native:image.naturalWidth,parent:image.parentElement.clientWidth}));
        assert.ok(Math.abs(size.width-(scale==='fit'?size.parent:Number(scale)*figure.width))<1);
        assert.equal(size.native,figure.width);
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      }
    }
    console.log('Corrupted image rejected; retry recovered; all original image hashes and nine zoom states passed at 320px.');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
