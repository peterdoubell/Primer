'use strict';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {chromium}=require('playwright'),ROOT=path.join(__dirname,'..'),OUT=path.join(ROOT,'docs/plane-shapes-review-20261023');
const files=['styles.css','spatial-models.js','spatial-module-objects.js'];
const binding=JSON.parse(fs.readFileSync(path.join(ROOT,'data/module-models.json'))).models.find(x=>x.node_id==='math.0.shapes');
const item={title:binding.title,instructions:binding.instructions,props:{scenario:'module.'+binding.node_id,family:binding.family,context:binding.context,mode:binding.mode,lesson:'Shapes All Around'}};
const html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Shapes model verification</title><link rel="stylesheet" href="/styles.css"><body><main style="max-width:900px;margin:auto;padding:12px"></main><script src="/spatial-models.js"></script><script src="/spatial-module-objects.js"></script><script>document.querySelector("main").append(PrimerModuleObjects.render('+JSON.stringify(item)+'));</script></body></html>';
const server=http.createServer((req,res)=>{
 if(req.url==='/'){res.setHeader('Content-Type','text/html');return res.end(html);}
 const name=req.url.slice(1);if(!files.includes(name)){res.statusCode=404;return res.end();}
 res.setHeader('Content-Type',name.endsWith('.js')?'text/javascript':'text/css');res.end(fs.readFileSync(path.join(ROOT,'web',name)));
});
(async()=>{
 fs.mkdirSync(OUT,{recursive:true});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true}),proof={scope:'Actual shared spatial renderer with the shipped lesson binding; standalone harness, not an authenticated production lesson',sourceSHA256:{},cases:[],allPassed:false};
 for(const name of [...files.map(f=>'web/'+f),'data/module-models.json'])proof.sourceSHA256[name]=crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,name))).digest('hex');
 try{
  for(const width of [390,1440]){
   const page=await browser.newPage({viewport:{width,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));
   await page.goto('http://127.0.0.1:'+server.address().port);await page.locator('svg.spatial-svg').waitFor();
   let states=0;
   for(const [shape,count] of [['circle',0],['triangle',3],['square',4],['rectangle',4]]){
    await page.getByLabel(/^Choose a shape/).selectOption(shape);
    assert.match(await page.locator('.spatial-readout').textContent(),new RegExp(shape==='circle'?'no corners':count+' corners|4 square corners'));
    for(const turn of ['0','90','225','360'])for(const size of ['0.5','1','1.5']){
     for(const [key,value] of [['turn',turn],['size',size]]){
      await page.locator('[data-parameter="'+key+'"]').fill(value);await page.locator('[data-parameter="'+key+'"]').dispatchEvent('input');
     }
     assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
     const geometry=await page.locator('svg.spatial-svg').evaluate(svg=>{
      const box=svg.viewBox.baseVal,bounds=svg.querySelector('g').getBBox();
      return {inside:bounds.x>=box.x&&bounds.y>=box.y&&bounds.x+bounds.width<=box.width&&bounds.y+bounds.height<=box.height,lines:svg.querySelectorAll('line').length};
     });assert(geometry.inside,JSON.stringify({width,shape,turn,size,geometry}));states++;
    }
    await page.screenshot({path:path.join(OUT,shape+'-'+width+'.png'),fullPage:true});
   }
   await page.getByRole('button',{name:'Reset model',exact:true}).click();assert.match(await page.locator('.spatial-readout').textContent(),/Circle: no straight sides and no corners/);
   const svg=page.locator('svg.spatial-svg');await svg.focus();await page.keyboard.press('ArrowRight');
   assert.equal(await page.getByLabel('Camera orientation',{exact:true}).textContent(),'Turn 10° · Tilt -25° · Zoom 100%');
   assert.deepEqual(errors,[]);proof.cases.push({width,states,reset:true,keyboardCamera:true,noOverflow:true,pageErrors:errors});await page.close();
  }
  proof.allPassed=true;fs.writeFileSync(path.join(OUT,'browser-proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
