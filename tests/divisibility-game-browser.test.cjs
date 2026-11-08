'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
const root=path.join(__dirname,'..'),model=JSON.parse(fs.readFileSync(path.join(root,'web/learning-games/divisibility/model.json')));
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});
  await page.setContent('<main><section id="game"></section></main>');
  await page.addStyleTag({path:path.join(root,'web/styles.css')});
  await page.addStyleTag({path:path.join(root,'web/module-mission.css')});
  await page.addScriptTag({path:path.join(root,'web/learning-games/divisibility/game.js')});
  await page.evaluate(m=>window.PrimerDivisibility.mount(document.querySelector('#game'),m),model);
  assert.equal(await page.getByRole('button',{name:'Check answer',exact:true}).isEnabled(),false);
  await page.getByRole('button',{name:'No',exact:true}).click();
  await page.getByRole('button',{name:'Check answer',exact:true}).click();
  assert.match(await page.getByRole('status').first().innerText(),/Try again/);
  assert.equal(await page.getByRole('button',{name:'Continue',exact:true}).isVisible(),false);
  for(const name of ['Yes','Yes','No','Not enough information','Yes','No']){
   await page.getByRole('button',{name,exact:true}).click();
   await page.getByRole('button',{name:'Check answer',exact:true}).click();
   await page.getByRole('button',{name:'Continue',exact:true}).click();
  }
  assert.match(await page.locator('#game').innerText(),/Case solved!/);
  assert.equal(await page.locator('progress').evaluate(e=>e.value),6);
  await page.getByText('Experiment with your own number',{exact:true}).click();
  await page.getByLabel('Whole number').fill('9007199254740993');
  await page.getByRole('button',{name:'Test my number'}).click();
  assert.match(await page.getByRole('status').last().innerText(),/Does not divide evenly/);
  await page.getByLabel('Whole number').fill('1e3');
  await page.getByRole('button',{name:'Test my number'}).click();
  assert.match(await page.getByRole('status').last().innerText(),/decimal digits/);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.getByRole('button',{name:'Play again'}).click();
  assert.equal(await page.locator('progress').evaluate(e=>e.value),0);
  const integrated=await browser.newPage();
  const allowed={
   '/app/learning-games/divisibility/model.json':['application/json',JSON.stringify(model)],
   '/app/learning-games/divisibility/game.js':['text/javascript',fs.readFileSync(path.join(root,'web/learning-games/divisibility/game.js'),'utf8')],
  };
  await integrated.route('http://primer-fixture.local/**',route=>{
   const asset=allowed[new URL(route.request().url()).pathname];
   return route.fulfill({status:200,contentType:asset?asset[0]:'text/html',body:asset?asset[1]:'<main></main>'});
  });
  await integrated.goto('http://primer-fixture.local/');
  const appSource=fs.readFileSync(path.join(root,'web/app.js'),'utf8');
  const helpers=appSource.slice(appSource.indexOf('function el('),appSource.indexOf('/* ---------------- drawn glyphs'));
  await integrated.addScriptTag({content:helpers+`
    const S={state:{profile:{}}};
    function renderTeachingLesson(){return null;}
    async function renderNode(page){page.append(el('h1',{},'Factors'),el('nav',{},'Path'),
      el('div',{},el('article',{class:'lesson-card'},'Reading')),el('div',{},btn({},'Take the quiz')));}
  `});
  await integrated.addScriptTag({path:path.join(root,'web/module-mission.js')});
  await integrated.evaluate(()=>renderNode(document.querySelector('main'),'math.2.primes'));
  assert.equal(await integrated.locator('.divisibility-game').count(),1);
  assert.equal(await integrated.getByRole('button',{name:'Check answer',exact:true}).count(),1);
  assert.match(await integrated.locator('main').innerText(),/Last-Digit Detective/);
  await integrated.evaluate(async()=>{
    const retired=document.createElement('main');await renderNode(retired,'math.2.primes');
    if(retired.querySelector('.divisibility-game'))throw new Error('Detached route mounted a game');
  });
  await integrated.close();
  console.log('Mobile playthrough, retry gating, sandbox, exact large integer and replay passed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
