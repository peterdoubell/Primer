#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');
const {createEvidenceDirectory,loopbackQaUrl} = require('./qa-browser.cjs');
const base=loopbackQaUrl(process.argv[2]),out=createEvidenceDirectory(),root=path.resolve(__dirname,'..');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'web/anatomy/msk-atlas/manifest.json')));
const region=manifest.regions.ankle,parts=region.parts.map(p=>({...manifest.parts[p.id],...p}));
const pedal=parts.filter(p=>p.layer==='bone'&&!['Tibia.r','Fibula.r'].includes(p.name));
const sha=data=>createHash('sha256').update(data).digest('hex');
const evidence={status:'running',sourceHashes:{},errors:[],checks:[],qualification:'Rendering/framing verification only. Native adult right-sided surface geometry remains clinically unapproved and does not supply every plantar plate or tendon sheath.'};
(async()=>{
 const browser=await chromium.launch({headless:true});let page;
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1080},reducedMotion:'reduce',hasTouch:true});
  assert.equal((await context.request.post(base+'/api/profile',{data:{name:'Whole-foot browser QA',age:35,hours_per_week:3,breadth:'balanced',domains:['radiology']}})).status(),200);
  await context.request.post(base+'/api/profile/settings',{data:{speak:false}});
  const sourceFiles=['app.js','radiology-detailed-anatomy.js','anatomy/msk-atlas/manifest.json'];
  for(const file of sourceFiles){const r=await context.request.get(base+'/app/'+file);assert.equal(r.status(),200);const hash=sha(await r.body());assert.equal(hash,sha(fs.readFileSync(path.join(root,'web',file))));evidence.sourceHashes[file]=hash;}
  const detail=await(await context.request.get(base+'/api/radiology/modules/ra.mri-diabetic-foot')).json();
  assert.equal(detail.radiology_reference.spatial_model.family,'foot');
  assert.equal(detail.radiology_reference.spatial_model.source_view,'whole-foot');
  const broad=await(await context.request.get(base+'/api/curriculum/node/rad.5.marrow-muscle')).json();
  assert.equal(broad.radiology_reference.spatial_model.family,'longbone');
  const fetched=new Set(),unwanted=[];page=await context.newPage();page.setDefaultTimeout(60000);
  page.on('pageerror',error=>evidence.errors.push(error.message));
  page.on('request',request=>{const p=new URL(request.url()).pathname;if(p.startsWith('/app/anatomy/msk-atlas/')&&p.endsWith('.bin'))fetched.add(p);if(p.startsWith('/app/anatomy/msk-mri-ankle/'))unwanted.push(p);});
  await page.goto(base+'/#/radiology/ra.mri-diabetic-foot');
  await page.getByRole('tab',{name:'3D anatomy',exact:true}).click();
  const model=page.locator('.rad-desk-panel:not([hidden]) .detailed-anatomy');
  await page.waitForFunction(()=>{const m=document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy');return m?.dataset.ready==='true'&&m.querySelector('canvas')?.dataset.rendered==='true';});
  assert.equal(await model.getAttribute('data-family'),'ankle');
  assert.equal(await model.getAttribute('data-atlas'),'z-anatomy');
  assert.equal(await model.getAttribute('data-view-preset'),'whole-foot');
  assert.match(await model.locator('h3').textContent(),/Adult right foot/);
  assert.match(await model.innerText(),/Adult right-foot reference only/);
  assert.match(await model.innerText(),/does not supply all plantar plates, tendon sheaths/);
  assert.equal(await model.getByRole('link',{name:manifest.license,exact:true}).getAttribute('href'),manifest.license_url);
  assert.equal(await page.getByRole('combobox',{name:'Ankle anatomy source',exact:true}).count(),0,'Do not offer MRI ankle subset as a whole-foot source');
  assert.equal(Number(await model.getAttribute('data-meshes')),parts.length);
  assert.equal(Number(await model.getAttribute('data-triangles')),parts.reduce((n,p)=>n+p.triangles,0));
  assert.deepEqual([...fetched].sort(),[...new Set(parts.map(p=>p.file))].sort(),'All original region parts are retained without new geometry');
  assert.deepEqual(unwanted,[]);
  const range=JSON.parse(await model.getAttribute('data-crop-range')),bounds=JSON.parse(await model.getAttribute('data-focus-bounds'));
  assert.deepEqual(JSON.parse(await model.getAttribute('data-focus-part-ids')).sort(),pedal.map(p=>p.id).sort());
  assert.equal(pedal.length,27);
  assert.deepEqual(range,[Math.min(...pedal.map(p=>p.bounds[0][1]))-.5,Math.max(...pedal.map(p=>p.bounds[1][1]))+.5]);
  for(const part of pedal)for(let axis=0;axis<3;axis++){assert.ok(bounds[0][axis]<part.bounds[0][axis]);assert.ok(bounds[1][axis]>part.bounds[1][axis]);}
  assert.equal(await model.locator('.detailed-anatomy-orientation').textContent(),'Right side · Superior');
  assert.equal(await model.locator('.detailed-anatomy-crop-status').textContent(),'Whole-foot region');
  const canvas=model.locator('canvas');
  await pixels('whole-foot-bones');await capture('whole-foot-default-desktop');
  const before=await canvas.evaluate(c=>c.toDataURL());await canvas.focus();await page.keyboard.press('ArrowRight');await settled();
  assert.notEqual(await canvas.evaluate(c=>c.toDataURL()),before);
  await model.getByRole('button',{name:'Reset',exact:true}).click();await settled();
  assert.equal(await canvas.getAttribute('data-view'),'0.00,1.57');
  await model.getByRole('button',{name:'Full structures',exact:true}).click();await settled();
  assert.equal(await canvas.getAttribute('data-cropped'),'false');
  assert.equal(await model.locator('.detailed-anatomy-crop-status').textContent(),'Uncropped source');
  await model.getByRole('button',{name:'Reset',exact:true}).click();await settled();
  assert.equal(await canvas.getAttribute('data-cropped'),'true');
  for(const name of ['Cartilage surfaces','Tendon sheaths','Together']){
   await model.getByRole('button',{name,exact:true}).click();await settled();await pixels(name);
  }
  await capture('whole-foot-together-desktop');
  await model.getByRole('button',{name:'Bones',exact:true}).click();await settled();
  const targets=pedal.filter(p=>/^Distal phalanx/.test(p.name)||p.name==='Sesamoid bones of foot.r');
  for(const part of targets){
   await model.locator('[data-part="'+part.id+'"]').focus();await page.keyboard.press('Enter');
   await model.getByRole('button',{name:'Isolate',exact:true}).click();await settled();
   assert.equal(await canvas.getAttribute('data-cropped'),'false');
   assert.equal(await model.locator('[data-part][aria-pressed="true"]').getAttribute('data-part'),part.id);
   await pixels(part.name);
   if(part.name==='Sesamoid bones of foot.r')await capture('paired-sesamoids-isolated');
   await model.getByRole('button',{name:'Reset',exact:true}).click();await settled();
  }
  await page.setViewportSize({width:390,height:844});await settled();await noOverflow();
  await pixels('mobile-whole-foot');await capture('whole-foot-default-mobile');
  await model.getByRole('button',{name:'Together',exact:true}).click();await settled();await noOverflow();await capture('whole-foot-together-mobile');
  const old=await canvas.elementHandle();
  await page.goto(base+'/#/radiology/ra.mri-ankle');await page.getByRole('tab',{name:'3D anatomy',exact:true}).click();
  await page.waitForFunction(c=>!c.isConnected&&c.getContext('webgl').isContextLost(),old);
  const ankle=page.locator('.rad-desk-panel:not([hidden]) .detailed-anatomy');
  await page.waitForFunction(()=>{const m=document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy');return m?.dataset.ready==='true'&&m.querySelector('canvas')?.dataset.rendered==='true';});
  assert.equal(await ankle.getAttribute('data-view-preset'),null);
  assert.equal(await page.getByRole('combobox',{name:'Ankle anatomy source',exact:true}).inputValue(),'z-anatomy');
  assert.equal(await ankle.locator('canvas').getAttribute('data-view'),'-0.22,0.10');
  assert.equal(await ankle.locator('.detailed-anatomy-crop-status').textContent(),'Cropped to region');
  for(const file of sourceFiles)assert.equal(sha(fs.readFileSync(path.join(root,'web',file))),evidence.sourceHashes[file]);
  assert.deepEqual(evidence.errors,[]);
  evidence.status='passed';evidence.sourcePartCount=parts.length;evidence.pedalFocusObjects=27;evidence.range=range;evidence.focusBounds=bounds;evidence.pedalBones=pedal.map(p=>({id:p.id,name:p.name,bounds:p.bounds}));evidence.mriAnkleSubsetRequests=0;evidence.broadLessonUnchanged=true;evidence.ankleDefaultUnchanged=true;evidence.oldWebGLDisposed=true;
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(evidence,null,2)+'\n');console.log('PASS whole-foot:27pedal objects, exact source region retained, toes/sesamoids isolation, crop/reset/mobile, old context disposed. '+out);
  async function settled(){await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));}
  async function pixels(label){await settled();const stats=await canvas.evaluate(c=>{const gl=c.getContext('webgl'),data=new Uint8Array(c.width*c.height*4);gl.readPixels(0,0,c.width,c.height,gl.RGBA,gl.UNSIGNED_BYTE,data);let pixels=0;for(let i=3;i<data.length;i+=4)if(data[i]>20)pixels++;return{pixels,error:gl.getError()};});assert.equal(stats.error,0);assert.ok(stats.pixels>100,label+': source geometry visible');evidence.checks.push({label,...stats});}
  async function capture(name){await model.locator('.detailed-anatomy-stage').evaluate(e=>e.scrollIntoView({block:'center',behavior:'instant'}));await settled();await page.screenshot({path:path.join(out,name+'.png'),animations:'disabled'});}
  async function noOverflow(){assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
 }catch(error){evidence.status='failed';evidence.failure=String(error.stack||error);if(page)await page.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify(evidence,null,2)+'\n');throw error;}finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
