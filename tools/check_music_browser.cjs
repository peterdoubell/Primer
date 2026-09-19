#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'), fs=require('node:fs'), path=require('node:path');
const {chromium}=require('playwright');
const base=process.argv[2]||'http://127.0.0.1:8794';
const out=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'primer-music-qa-'));
const nodes=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/curriculum/09-arts.json'),'utf8')).nodes.filter(n=>n.music_grade);
(async()=>{
 const browser=await chromium.launch({headless:true});const errors=[],results=[];
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1100},reducedMotion:'reduce'});
  page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{
   const Native=window.AudioContext;window.__musicAudio={created:0,closed:0,notes:[]};
   window.AudioContext=class extends Native {
    constructor(...args){super(...args);window.__musicAudio.created++;}
    createOscillator(){const o=super.createOscillator();const start=o.start.bind(o);o.start=at=>{window.__musicAudio.notes.push(o.frequency.value);start(at);};return o;}
    close(){window.__musicAudio.closed++;return super.close();}
   };
  });
  await page.goto(base+'/#/node/arts.2.music-reading');
  await page.locator('.music-grade-path a').first().waitFor();
  assert.equal(await page.locator('.music-grade-path a').count(),8);
  await page.locator('.music-grade-path a').first().click();
  assert.ok(page.url().endsWith('/arts.2.music-grade-1'));
  for(const n of nodes){
   if(page.url()!==base+'/#/node/'+n.id)await page.goto(base+'/#/node/'+n.id);
   await page.getByRole('heading',{name:n.title,exact:true}).waitFor();
   await page.waitForFunction(grade=>document.querySelector('.music-grade-path [aria-current=page]')?.textContent==='Grade '+grade && document.querySelectorAll('.music-unit').length===3, n.music_grade);
   const study=page.locator('.music-study'),lab=page.locator('.music-listening');
   await lab.waitFor();
   await page.waitForFunction(()=>{const i=document.querySelector('.lesson-illustration img');return i&&i.complete&&i.naturalWidth>0;});
   assert.equal(await study.locator('.music-unit').count(),3);
   assert.equal(await study.locator('.music-practice-grid section').count(),4);
   assert.equal(await study.locator('[aria-current="page"]').textContent(),'Grade '+n.music_grade);
   const before=await page.evaluate(()=>window.__musicAudio.created);
   assert.ok(await lab.getByRole('status').innerText().then(t=>t.includes('Ready')));
   assert.equal(await page.evaluate(()=>window.__musicAudio.created),before);
   for(const key of ['A','B']){
    await lab.getByRole('button',{name:'Play '+key,exact:true}).click();
    await page.waitForFunction(k=>document.querySelector('.music-listening [role=status]').textContent==='Playing '+k+'.',key);
    assert.ok((await page.evaluate(()=>window.__musicAudio.notes)).every(Number.isFinite));
    await lab.getByRole('button',{name:'Stop',exact:true}).click();
    assert.equal(await lab.getByRole('status').innerText(),'Stopped.');
   }
   const reveal=lab.getByRole('button',{name:'Show explanation',exact:true});await reveal.focus();await page.keyboard.press('Enter');
   assert.ok(await lab.locator('.music-audio-answer').isVisible());
   await lab.getByRole('button',{name:'Hide explanation',exact:true}).click();
   for(const width of [1440,390]){
    await page.setViewportSize({width,height:1100});
    await page.getByRole('button',{name:'View notation and listening',exact:true}).click();
    const image=page.locator('.lesson-illustration img'),box=await image.boundingBox();
    assert.ok(box.x>=-1&&box.x+box.width<=width+1,n.id+' image bounds');
    const controls=await lab.locator('button').all();for(const b of controls){const r=await b.boundingBox();assert.ok(r.x>=-1&&r.x+r.width<=width+1,n.id+' control bounds');}
    await page.locator('.lesson-illustration').screenshot({path:path.join(out,'grade-'+n.music_grade+'-'+width+'.png')});
    if(width===390)await lab.screenshot({path:path.join(out,'grade-'+n.music_grade+'-audio-mobile.png')});
   }
   await page.locator('.lesson-illustration img').click();await page.locator('[role=dialog]').waitFor();await page.keyboard.press('Escape');
   await lab.getByRole('button',{name:'Play A',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('.music-listening [role=status]').textContent==='Playing A.');
   const closed=await page.evaluate(()=>window.__musicAudio.closed);
   await page.goto(base+'/#/node/arts.2.music-reading');
   await page.waitForFunction(count=>window.__musicAudio.closed>count,closed);
   results.push({grade:n.music_grade,status:'pass'});
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({results,errors},null,2));console.log('PASS eight grades: route links, study tasks, audio A/B/stop, keyboard reveal, cleanup, desktop/mobile, image viewer. '+out);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
