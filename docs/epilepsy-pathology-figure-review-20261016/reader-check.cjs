/* Verify the actual reader against an explicitly isolated loopback fixture. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'../..'),fixture=JSON.parse(fs.readFileSync(0,'utf8'));
assert.equal(new URL(fixture.url).hostname,'127.0.0.1');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const rows=JSON.parse(fs.readFileSync(path.join(ROOT,'data/radiology/radiology-open-images.json')))['ra.mri-epilepsy'];
assert.equal(rows.length,6);const bySrc=Object.fromEntries(rows.map(r=>[r.src,r]));
const stepPlan=JSON.parse(fs.readFileSync(path.join(__dirname,'reporting-step-patch-plan.json')));
const shell=fs.readFileSync(path.join(ROOT,'web/index.html'),'utf8');
const scripts=[...shell.matchAll(/<script src="\/app\/([\w-]+\.js)(?:\?[^"<>]*)?"><\/script>/g)].map(m=>m[1]);
const bundle=Buffer.from("'use strict';\n"+scripts.map(n=>fs.readFileSync(path.join(ROOT,'web',n),'utf8')).join('\n;\n'));
const proof={scope:'Six exact published images in actual authenticated loopback synthetic reporting, walkthrough and lesson readers',productionVerified:false,cases:[],imageBodies:{},startupBundle:{bytes:bundle.length,sha256:hash(bundle)},errors:[]};
const sourcePaths=['web/app.js','web/index.html','primer/module_media.py','data/radiology/radiology-open-images.json','data/radiology/radiology-asset-evidence.json','data/radiology/reporting-steps/neuroradiology.json','data/radiology/radiology-static-rasters.json',...rows.map(r=>'web/'+r.src.slice(5))];
proof.sourceSHA256=Object.fromEntries(sourcePaths.map(p=>[p,hash(fs.readFileSync(path.join(ROOT,p)))]));
async function inspectImage(page,container,row,{caption=false}={}){
 const img=container.locator('img[src="'+row.src+'"]');assert.equal(await img.count(),1);await img.scrollIntoViewIfNeeded();
 await img.evaluate(async im=>{await im.decode();});
 const natural=await img.evaluate(im=>({width:im.naturalWidth,height:im.naturalHeight,full:im.dataset.fullSrc,objectFit:getComputedStyle(im).objectFit,filter:getComputedStyle(im).filter,opacity:getComputedStyle(im).opacity,rectangle:{width:im.getBoundingClientRect().width,height:im.getBoundingClientRect().height}}));
 assert.equal(natural.width,row.width);assert.equal(natural.height,row.height);assert.equal(natural.full,row.src);assert.equal(natural.filter,'none');assert.equal(natural.opacity,'1');
 assert(Math.abs(natural.rectangle.width/natural.rectangle.height-row.width/row.height)<.01 || ['contain','scale-down'].includes(natural.objectFit),JSON.stringify({id:row.id,...natural}));
 if(caption){const figure=img.locator('xpath=ancestor::figure[1]');assert((await figure.innerText()).includes(row.caption));assert((await figure.innerText()).includes(row.attribution));assert((await figure.innerText()).includes(row.limits));await figure.locator('details.rad-source-caption > summary').click();assert((await figure.innerText()).includes(row.source_caption_full));}
 await img.click();const modal=page.getByRole('dialog');await modal.waitFor();const large=modal.locator('.lightbox img');await large.evaluate(async im=>{await im.decode();});
 assert.equal(await large.getAttribute('src'),row.src);assert.equal(await large.evaluate(im=>im.naturalWidth),row.width);
 await modal.getByRole('button',{name:'Read labels at full size',exact:true}).click();
 await modal.evaluate(async el=>{await Promise.all(el.getAnimations({subtree:true}).filter(a=>a.effect?.getTiming().iterations!==Infinity).map(a=>a.finished.catch(()=>{})));await new Promise(requestAnimationFrame);});
 assert.equal(await large.evaluate(im=>Math.round(im.getBoundingClientRect().width)),row.width);
 const scroller=modal.locator('.lightbox-image-scroll');assert(await scroller.evaluate(el=>el.scrollWidth>el.clientWidth));
 await scroller.focus();await page.keyboard.press('End');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await modal.getByRole('button',{name:'Fit the whole image',exact:true}).click();await modal.getByRole('button',{name:'Close the picture',exact:true}).click();
 assert.equal(await page.getByRole('dialog').count(),0);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 return {id:row.id,naturalWidth:row.width,naturalHeight:row.height,exactOriginalFullSize:true,captionExpanded:caption,unfiltered:true,noHorizontalPageOverflow:true};
}
(async()=>{const browser=await chromium.launch({headless:true});try{
 for(const width of [390,1440]){
  const context=await browser.newContext({viewport:{width,height:1000},extraHTTPHeaders:{Authorization:'Basic '+Buffer.from(fixture.username+':'+fixture.password).toString('base64')}});
  await context.addInitScript(()=>{window.epilepsyCSP=[];document.addEventListener('securitypolicyviolation',e=>window.epilepsyCSP.push({directive:e.violatedDirective,blocked:e.blockedURI}));});
  const profile=await context.request.post(fixture.url+'/api/profile',{headers:{Origin:fixture.url},data:{name:'Synthetic epilepsy figure QA',age:30,domains:['radiology']}});assert.equal(profile.status(),200);
  const page=await context.newPage(),errors=[],responses=[];let bundleSeen=false;
  page.on('pageerror',e=>errors.push(e.message));page.on('response',res=>{const name=new URL(res.url()).pathname;if(name==='/app/startup.js')responses.push(res.body().then(raw=>{assert(raw.equals(bundle));bundleSeen=true;}).catch(e=>errors.push(e.message)));if(bySrc[name])responses.push(res.body().then(raw=>{assert.equal(res.status(),200);assert.equal(hash(raw),bySrc[name].sha256);proof.imageBodies[name]={sha256:hash(raw),bytes:raw.length};}).catch(e=>errors.push(e.message)));});
  await page.goto(fixture.url+'/app/#radiology/ra.mri-epilepsy');await page.getByRole('tab',{name:'Images and registered MRI',exact:true}).click();
  const panel=page.locator('[role="tabpanel"]:visible');for(const row of rows)proof.cases.push({width,surface:'reporting-images',...await inspectImage(page,panel,row,{caption:true})});
  const hipp=panel.locator('.source-native-inspector').filter({has:page.locator('a[href="/app/anatomy/hippunfold-hcp101006-registered/index.html"]')});
  await hipp.getByRole('button',{name:'Inspect registered hippocampal MRI and surfaces inline',exact:true}).click();const frame=await(await hipp.locator('iframe').elementHandle()).contentFrame();await frame.locator('#mri[data-ready="true"]').waitFor({timeout:60000});await frame.locator('#mesh[data-ready="true"]').waitFor({timeout:60000});assert.deepEqual(await frame.evaluate(()=>window.epilepsyCSP),[]);await hipp.getByRole('button',{name:'Close source viewer',exact:true}).click();
  await page.getByRole('tab',{name:'Step by step',exact:true}).click();for(const change of stepPlan){await page.locator('.rad-walk-step').filter({hasText:change.expected_step_label}).click();const walk=page.locator('.rad-walk-figures:visible');for(const id of change.proposed_after){const row=rows.find(r=>r.id===id);if(row)proof.cases.push({width,surface:'walkthrough',step:change.expected_step_label,...await inspectImage(page,walk,row)});}}
  await page.goto(fixture.url+'/app/#/node/rad.5.epilepsy-mri');const gallery=page.getByRole('region',{name:'Original source figures',exact:true});await gallery.getByRole('button',{name:'Load original source figures',exact:true}).click();await gallery.getByText(/Original source figures loaded/).waitFor();await gallery.locator('details > summary').first().click();
  for(const row of rows)proof.cases.push({width,surface:'lesson-gallery',...await inspectImage(page,gallery,row,{caption:true})});
  assert.equal(await page.getByRole('region',{name:'Registered hippocampal MRI and source surfaces',exact:true}).count(),1);
  await Promise.all(responses);assert(bundleSeen);assert.deepEqual(errors,[]);assert.deepEqual(await page.evaluate(()=>window.epilepsyCSP),[]);await context.close();
 }
 assert.equal(Object.keys(proof.imageBodies).length,6);assert.equal(proof.cases.length,36);
 for(const [p,digest]of Object.entries(proof.sourceSHA256))assert.equal(hash(fs.readFileSync(path.join(ROOT,p))),digest,p+' changed during proof');
 proof.timestamp=new Date().toISOString();proof.caseCount=proof.cases.length;proof.hippUnfoldInspectorPreserved=true;
 process.stdout.write(JSON.stringify(proof,null,2)+'\n');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
