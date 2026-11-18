'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
const root=path.join(__dirname,'..'),model=JSON.parse(fs.readFileSync(path.join(root,'web/learning-games/divisibility/model.json')));
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
 try{
  // The open number bench on a phone-sized screen.
  const page=await browser.newPage({viewport:{width:390,height:844}});
  await page.setContent('<main><section id="game"></section></main>');
  await page.addStyleTag({path:path.join(root,'web/styles.css')});
  await page.addStyleTag({path:path.join(root,'web/module-mission.css')});
  await page.addScriptTag({path:path.join(root,'web/learning-games/divisibility/game.js')});
  await page.evaluate(m=>window.PrimerDivisibility.mount(document.querySelector('#game'),m),model);
  assert.match(await page.locator('#game').innerText(),/Test any number/);
  await page.getByRole('button',{name:'Test my number'}).click();
  assert.match(await page.getByRole('status').innerText(),/Divides evenly/);
  await page.getByLabel('Whole number').fill('9007199254740993');
  await page.getByRole('button',{name:'Test my number'}).click();
  assert.match(await page.getByRole('status').innerText(),/Does not divide evenly/);
  await page.getByLabel('Whole number').fill('1e3');
  await page.getByLabel('Whole number').press('Enter');
  assert.match(await page.getByRole('status').innerText(),/decimal digits/);
  await page.getByLabel('Divide by').selectOption('125');
  await page.getByLabel('Whole number').fill('1000');
  await page.getByRole('button',{name:'Test my number'}).click();
  assert.match(await page.getByRole('status').innerText(),/Divides evenly/);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  // Inside a module: the bench mounts after the learn-by-doing section, and
  // still mounts when the learning-sequence service cannot be reached.
  const integrated=await browser.newPage();
  const allowed={
   '/app/learning-games/divisibility/model.json':['application/json',JSON.stringify(model)],
   '/app/learning-games/divisibility/game.js':['text/javascript',fs.readFileSync(path.join(root,'web/learning-games/divisibility/game.js'),'utf8')],
  };
  await integrated.route('http://primer-fixture.local/**',route=>{
   const url=new URL(route.request().url());
   if(url.pathname.startsWith('/api/'))return route.fulfill({status:503,contentType:'application/json',body:'{"error":"unavailable"}'});
   const asset=allowed[url.pathname];
   return route.fulfill({status:200,contentType:asset?asset[0]:'text/html',body:asset?asset[1]:'<main></main>'});
  });
  await integrated.goto('http://primer-fixture.local/');
  const appSource=fs.readFileSync(path.join(root,'web/app.js'),'utf8');
  const helpers=appSource.slice(appSource.indexOf('function el('),appSource.indexOf('/* ---------------- drawn glyphs'));
  const teaching=appSource.slice(appSource.indexOf('function renderTeachingLesson('),appSource.indexOf('async function renderNode('));
  await integrated.addScriptTag({content:helpers+teaching+`
    const S={state:{profile:{}}};
    async function renderNode(page){page.append(el('h1',{},'Factors'),el('nav',{},'Path'),
      el('div',{},el('article',{class:'lesson-card'},'Reading')),el('div',{},btn({},'Take the quiz')));}
  `});
  await integrated.addScriptTag({path:path.join(root,'web/module-mission.js')});
  await integrated.evaluate(()=>renderNode(document.querySelector('main'),'math.2.primes'));
  assert.equal(await integrated.locator('.divisibility-game').count(),1);
  await integrated.getByRole('button',{name:'Test my number'}).waitFor();
  await integrated.getByText('The activity could not load. Your lesson is still available.').waitFor();
  assert.equal(await integrated.evaluate(()=>document.querySelector('.lg-play').nextElementSibling.classList.contains('divisibility-game')),true,
    'The bench follows the learn-by-doing section');
  assert.equal(await integrated.getByRole('button',{name:'Try again'}).count(),1);
  await integrated.evaluate(async()=>{
    const retired=document.createElement('main');await renderNode(retired,'math.2.primes');
    if(retired.querySelector('.divisibility-game'))throw new Error('Detached route mounted a game');
  });
  await integrated.close();
  console.log('Bench arithmetic on mobile, Enter key, divisor choice, sandboxed module mount and unavailable-service fallback passed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
