'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const fixture=JSON.parse(fs.readFileSync(0,'utf8')),u=new URL(fixture.url);assert.equal(u.hostname,'127.0.0.1');assert.equal(u.protocol,'http:');
const R=path.resolve(__dirname,'..'),O=path.join(R,'docs/nextbrain-reader-review-20261027/lesson');fs.mkdirSync(O,{recursive:true});
const auth={Authorization:'Basic '+Buffer.from(fixture.username+':'+fixture.password).toString('base64')};
(async()=>{const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const proof={allPassed:false,syntheticLoopback:true,productionLearnerWrites:false,errors:[],mounts:[],files:{}};try{
for(const n of ['web/app.js','primer/server.py','primer/source_native_inspectors.py','primer/nextbrain_reference.py','data/radiology/nextbrain-reference.json','tools/check_nextbrain_lesson.py','tools/check_nextbrain_lesson.cjs'])proof.files[n]=crypto.createHash('sha256').update(fs.readFileSync(path.join(R,n))).digest('hex');
for(const width of [390,1440]){const context=await browser.newContext({viewport:{width,height:1000}});
await context.route(fixture.url+'/**',route=>route.continue({headers:{...route.request().headers(),...auth}}));
context.on('request',req=>{if(new URL(req.url()).origin!==fixture.url)assert(!req.headers().authorization);});
assert.equal((await context.request.post(fixture.url+'/api/profile',{headers:{...auth,Origin:fixture.url},data:{name:'Synthetic NextBrain reader QA',age:30,domains:['radiology']}})).status(),200);
assert.equal((await context.request.post(fixture.url+'/api/profile/settings',{headers:{...auth,Origin:fixture.url},data:{speak:false}})).status(),200);
const page=await context.newPage();page.on('pageerror',e=>proof.errors.push(e.message));await page.goto(fixture.url+'/app/#/node/rad.5.brain-anatomy');await page.getByRole('button',{name:'Load original native source inspections',exact:true}).click();
const details=page.locator('.lesson-source-gallery details').filter({has:page.locator('a[href="/app/anatomy/nextbrain/index.html"]')});await details.locator('summary').click();
const card=details.locator('.source-native-inspector').filter({has:page.locator('a[href="/app/anatomy/nextbrain/index.html"]')});await card.getByRole('button',{name:'Inspect ex vivo MRI, labels and source boundaries inline',exact:true}).click();
const frame=card.frameLocator('iframe');await frame.locator('body[data-planes-ready="19"][data-mesh-ready="19"]').waitFor({timeout:180000});assert((await frame.locator('#meaning').innerText()).includes('Pons-corticopontine-pontocerebellar-fibers'));
await frame.locator('#structure').selectOption('29');await frame.locator('body[data-planes-ready="29"][data-mesh-ready="29"]').waitFor({timeout:180000});
await card.screenshot({path:path.join(O,'lesson-'+width+'.png')});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
await card.getByRole('button',{name:'Close source viewer',exact:true}).click();assert.equal(await card.locator('iframe').count(),0);proof.mounts.push({width,nodeId:'rad.5.brain-anatomy',selected:[19,29],openedAndClosed:true,remotePayloadsVerified:true,credentialScope:'loopback app origin only'});await context.close();}
assert.deepEqual(proof.errors,[]);proof.allPassed=true;fs.writeFileSync(path.join(O,'proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify({allPassed:true,mounts:proof.mounts.length}));}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
