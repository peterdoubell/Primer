const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
(async()=>{
 const b=await chromium.launch();try{
 const p=await b.newPage({viewport:{width:390,height:900}}),errors=[];
 p.on('pageerror',e=>errors.push(e.message));
 await p.route('https://scope.test/**',r=>{const file=path.basename(new URL(r.request().url()).pathname);assert.ok(['index.html','viewer.css','core.js','viewer.js'].includes(file));return r.fulfill({body:fs.readFileSync(path.join('web/language/quantifier-scope',file)),contentType:file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':'text/html'});});
 await p.goto('https://scope.test/index.html');
 await p.locator('#link-0-0').waitFor();
 await p.locator('#example').selectOption('0');
 let previous=0;
 for(let i=0;i<512;i++){
  const mask=i^(i>>1),change=mask^previous;
  if(change){const bit=Math.log2(change);await p.locator('#link-'+Math.floor(bit/3)+'-'+bit%3).check({trial:true});await p.locator('#link-'+Math.floor(bit/3)+'-'+bit%3).click();}
  previous=mask;
  const actual=await p.evaluate(()=>({each:document.getElementById('each-result').textContent,one:document.getElementById('one-result').textContent,edges:[...document.querySelectorAll('#edges line')].map(e=>[Number(e.dataset.child),Number(e.dataset.tree)]),checks:[...document.querySelectorAll('input[type=checkbox]')].map(e=>e.checked)}));
  const pairs=[];for(let bit=0;bit<9;bit++)if(Math.floor(mask/2**bit)%2)pairs.push([Math.floor(bit/3),bit%3]);
  const each=new Set(pairs.map(([c])=>c)).size===3,one=[0,1,2].some(t=>pairs.filter(([,tree])=>tree===t).length===3);
  assert.equal(actual.each.startsWith('True:'),each);assert.equal(actual.one.startsWith('True:'),one);assert.deepEqual(actual.edges,pairs);
  assert.equal(actual.checks.reduce((m,on,bit)=>m+(on?2**bit:0),0),mask);
 }
 for(const [preset,challenge]of [['273','only-each'],['73','both'],['0','neither']]){await p.locator('#example').selectOption(preset);await p.locator('#challenge').selectOption(challenge);await p.locator('#check').click();assert.match(await p.locator('#feedback').textContent(),/^Scene matches/);await p.locator('#link-0-0').click();assert.equal(await p.locator('#feedback').textContent(),'');}
 await p.locator('#challenge').selectOption('only-one');await p.locator('#check').click();assert.match(await p.locator('#feedback').textContent(),/No scene/);
 await p.locator('#example').selectOption('273');await p.locator('#link-0-1').focus();await p.keyboard.press('Space');assert.ok(await p.locator('#link-0-1').isChecked());
 for(const width of [320,390,1440]){await p.setViewportSize({width,height:1000});assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
 
 assert.deepEqual(errors,[]);console.log('All 512 rendered relations, SVG edges, challenges, stale-state clearing, keyboard and responsive layouts passed.');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
