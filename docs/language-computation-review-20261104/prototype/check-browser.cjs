'use strict';
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const D=__dirname;
(async()=>{
 const browser=await chromium.launch({headless:true}),parses=[],probabilities=[],evaluations=[],errors=[];let mounts=0,remounts=0,taskCases=0,practiceChecks=0;
 try{
  for(const width of [390,1440]){
   const p=await browser.newPage({viewport:{width,height:1000}});p.on('pageerror',e=>errors.push(e.message));
   await p.route('**/*',r=>{const u=new URL(r.request().url()),name=u.pathname.slice(1);assert.equal(u.origin,'http://127.0.0.1:4021');assert(['index.html','core.js','lab.js','lab.css'].includes(name));return r.fulfill({body:fs.readFileSync(path.join(D,name)),contentType:name.endsWith('.html')?'text/html':name.endsWith('.css')?'text/css':'text/javascript'});});
   await p.goto('http://127.0.0.1:4021/index.html');const lab=p.locator('.language-computation-lab'),role=k=>lab.locator('[data-role="'+k+'"]'),station=k=>lab.locator('[data-station="'+k+'"]');await lab.waitFor();
   assert.equal(await lab.count(),1);assert.equal(await lab.evaluate(r=>r.languageReview.parser.completed),0);
   for(const id of ['simple','attachment','two-attachments','word-order','unknown']){
    await role('sentence').selectOption(id);assert.equal(await lab.evaluate(r=>r.languageReview.parser.completed),0);
    await role('step').click();assert.equal(await lab.evaluate(r=>r.languageReview.parser.completed),1);
    await role('finish').click();assert(await lab.evaluate(r=>{const m=r.languageReview.parser;if(!m.layout)return true;const e=r.querySelector('[data-role="tree"]'),v=e.parentElement,x=m.layout.positions[0].x*e.getBoundingClientRect().width/m.layout.width-v.scrollLeft;return x>=0&&x<=v.clientWidth;}));const count=await lab.evaluate(r=>r.languageReview.parser.count);
    const ranks=count?Array.from({length:count},(_,i)=>i):[0];
    for(const rank of ranks){
     if(rank)await role('next-tree').click();
     const record=await lab.evaluate(r=>({...r.languageReview.parser,nodes:[...r.querySelectorAll('[data-tree-node]')].map(e=>({source:JSON.parse(e.dataset.source),x:Number(e.getAttribute('x')),y:Number(e.getAttribute('y')),text:e.textContent})),edges:[...r.querySelectorAll('[data-tree-edge]')].map(e=>({ids:e.dataset.treeEdge,coords:['x1','y1','x2','y2'].map(k=>Number(e.getAttribute(k)))})),chartText:r.querySelector('[data-role="chart"]').innerText,chartRows:[...r.querySelector('[data-role="chart"]').querySelectorAll('tbody tr')].map(tr=>[...tr.children].map(td=>td.textContent)),overflow:document.documentElement.scrollWidth>innerWidth+1}));
     assert(!record.overflow);assert.equal(record.rank,rank);assert.equal(record.completed,record.events.length);if(!count)assert.equal(record.nodes.length,0);parses.push({width,id,...record});
    }
    await role('parse-guess').fill(String(count+1));await role('check-parse').click();assert((await role('parse-feedback').innerText()).startsWith('Try again.'));
    await role('parse-guess').fill(String(count));await role('check-parse').click();assert((await role('parse-feedback').innerText()).startsWith('Correct.'));practiceChecks+=2;
    if(count){await role('start-tree').click();assert.equal(await role('tree').evaluate(e=>e.parentElement.scrollLeft),0);await role('end-tree').click();assert(await role('tree').evaluate(e=>Math.abs(e.parentElement.scrollLeft-(e.parentElement.scrollWidth-e.parentElement.clientWidth))<1));await role('center-tree').click();}await role('reset-parse').click();assert.equal(await lab.locator('[data-tree-node]').count(),0);assert.equal(await lab.evaluate(r=>r.languageReview.parser.completed),0);
   }
   await role('sentence-text').fill('we heard a bird');await role('use-sentence').click();assert.equal(await role('sentence').inputValue(),'custom');assert.equal(await lab.evaluate(r=>r.languageReview.parser.text),'we heard a bird');
   await role('sentence-text').fill('WE <img>');await role('use-sentence').click();assert((await role('parse-error').innerText()).startsWith('Input not applied.'));assert.equal(await lab.evaluate(r=>r.languageReview.parser.text),'we heard a bird');assert.equal(await lab.locator('img').count(),0);
   await role('sentence').selectOption('attachment');await role('finish').click();await lab.screenshot({path:path.join(D,'parser-'+width+'.png')});
   await station('corpus').click();
   for(const corpus of ['varied','foxHeavy'])for(const alpha of ['0','1','2'])for(const history of ['<s>','the','fox','bird','cat','dog','rests','<unk>']){
    await role('corpus').selectOption(corpus);await role('alpha').selectOption(alpha);await role('history').selectOption(history);
    const record=await lab.evaluate(r=>({...r.languageReview.lm,barRects:[...r.querySelectorAll('[data-probability-bar]')].map(e=>({word:e.dataset.probabilityBar,source:JSON.parse(e.dataset.source),coords:['x','y','width','height'].map(k=>Number(e.getAttribute(k)))})),mapLines:[...r.querySelectorAll('[data-transition]')].map(e=>({word:e.dataset.transition,coords:['x1','y1','x2','y2'].map(k=>Number(e.getAttribute(k))),dash:e.getAttribute('stroke-dasharray')})),tableRows:[...r.querySelector('[data-role="prediction-table"]').querySelectorAll('tbody tr')].map(tr=>[...tr.children].map(td=>td.textContent)),trainingRows:[...r.querySelector('[data-role="sentences"]').querySelectorAll('tbody tr')].map(tr=>[...tr.children].map(td=>td.textContent)),mapTexts:[...r.querySelector('[data-role="map"]').querySelectorAll('text')].map(e=>e.textContent),overflow:document.documentElement.scrollWidth>innerWidth+1}));
    assert(!record.overflow);assert.equal(record.corpusId,corpus);assert.equal(record.history,history);assert.equal(record.alphaHalves,Number(alpha));
    if(record.rowDefined){assert.equal(record.barRects.length,8);for(const answer of new Set([record.mostLikely[0],record.mostLikely.at(-1)])){await role('next-guess').selectOption(answer);await role('check-next').click();assert((await role('next-feedback').innerText()).startsWith('Correct.'));practiceChecks++;}
     const wrong=record.vocabulary.find(x=>!record.mostLikely.includes(x));if(wrong){await role('next-guess').selectOption(wrong);await role('check-next').click();assert((await role('next-feedback').innerText()).startsWith('Try again.'));practiceChecks++;}}
    else{assert.equal(record.barRects.length,0);assert.equal(record.mapLines.length,0);assert(await role('check-next').isDisabled());}
    probabilities.push({width,...record});
   }
   await role('corpus').selectOption('varied');await role('history').selectOption('the');await role('alpha').selectOption('1');await lab.screenshot({path:path.join(D,'corpus-'+width+'.png')});
   await station('ambiguity').click();
   for(const answer of ['sense','morphology','tokenization','coreference','pos']){
    await role('task-guess').selectOption(answer==='sense'?'pos':'sense');await role('check-task').click();assert((await role('task-feedback').innerText()).startsWith('Try again.'));
    await role('task-guess').selectOption(answer);await role('check-task').click();assert((await role('task-feedback').innerText()).startsWith('Correct.'));taskCases++;practiceChecks+=2;await role('next-task').click();
   }
   assert.equal(await lab.evaluate(r=>r.languageReview.task.index),0);await lab.screenshot({path:path.join(D,'ambiguity-'+width+'.png')});
   await station('evaluation').click();
   async function capture(name){const r=await lab.evaluate(root=>({...root.languageReview.evaluation,rects:[...root.querySelectorAll('[data-metric-bar]')].map(e=>({name:e.dataset.metricBar,fraction:e.dataset.fraction,coords:['x','y','width','height'].map(k=>Number(e.getAttribute(k)))})),table:root.querySelector('[data-role="metrics"]').innerText,matrixRows:[...root.querySelector('[data-role="confusion"]').querySelectorAll('tbody tr')].map(tr=>[...tr.children].map(td=>td.textContent)),confusion:root.querySelector('[data-role="confusion"]').innerText,overflow:document.documentElement.scrollWidth>innerWidth+1}));assert(!r.overflow);evaluations.push({width,name,...r});}
   for(const preset of ['default-counts','negative-counts','empty-counts']){await role(preset).click();await capture(preset);await role('metric-guess').selectOption('recall');await role('check-metric').click();assert((await role('metric-feedback').innerText()).startsWith('Correct.'));practiceChecks++;}
   for(const counts of [{tp:1,fp:2,fn:3,tn:4},{tp:4,fp:0,fn:6,tn:0}]){for(const [k,v]of Object.entries(counts)){await role(k).fill(String(v));await role(k).dispatchEvent('change');}await capture(JSON.stringify(counts));}
   for(const k of ['tp','fp','fn','tn'])for(const invalid of ['', '-1','1.5','101']){const before=await role(k).inputValue();await role(k).fill(invalid);await role(k).dispatchEvent('change');assert.equal(await role(k).inputValue(),before);}
   await role('negative-counts').click();await lab.screenshot({path:path.join(D,'evaluation-'+width+'.png')});assert((await lab.evaluate(r=>r.getModelSpeech())).includes('classifier'));
   assert(await p.evaluate(async()=>{
    const a=PrimerLanguageComputationLab.render({props:{scenario:'lang.5.comp-ling'}}),b=PrimerLanguageComputationLab.render({props:{scenario:'lang.5.comp-ling'}});document.body.append(a,b);await new Promise(r=>requestAnimationFrame(r));
    const select=a.querySelector('[data-role="sentence"]');select.value='simple';select.dispatchEvent(new Event('change'));const independent=a.languageReview.parser.text==='we saw a fox'&&b.languageReview.parser.text==='we saw a fox with a telescope';a.remove();b.remove();await new Promise(r=>requestAnimationFrame(r));return independent&&a.dataset.disposed==='true'&&b.dataset.disposed==='true'&&PrimerLanguageComputationLab.render({props:{scenario:'lang.4.linguistics'}})===null;
   }));mounts+=2;
   assert(await lab.evaluate(async r=>{r.remove();await new Promise(x=>requestAnimationFrame(x));return r.dataset.disposed==='true';}));
   await p.evaluate(()=>document.querySelector('main').append(PrimerLanguageComputationLab.render({props:{scenario:'lang.5.comp-ling'}})));assert.equal(await lab.evaluate(r=>r.languageReview.parser.completed),0);remounts++;
   await p.close();
  }
  assert.deepEqual(errors,[]);const proof={allPassed:true,parserCases:parses.length,probabilityCases:probabilities.length,evaluationCases:evaluations.length,ambiguityCases:taskCases,practiceFeedbackChecks:practiceChecks,independentMounts:mounts,standaloneRemounts:remounts,errors,scope:'Standalone prototype',applicationIntegrated:false,productionLearnerWrites:false,wholeGoalComplete:false};
  for(const [name,value]of Object.entries({'parser-browser-cases.json':parses,'probability-browser-cases.json':probabilities,'evaluation-browser-cases.json':evaluations,'browser-proof.json':proof}))fs.writeFileSync(path.join(D,name),JSON.stringify(value,null,2)+'\n');console.log(proof);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
