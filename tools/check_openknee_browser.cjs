#!/usr/bin/env node
'use strict';
// Isolated loopback QA only. No source images or geometry are changed.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');
const {createEvidenceDirectory,loopbackQaUrl}=require('./qa-browser.cjs');
const base=loopbackQaUrl(process.argv[2]),out=createEvidenceDirectory(),root=path.resolve(__dirname,'..');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'web/anatomy/openknee-oks003/manifest.json')));
const region=manifest.regions.knee,parts=region.parts.map(p=>({...manifest.parts[p.id],...p}));
const byFile=new Map(parts.map(p=>[p.file,p]));
const sha=data=>createHash('sha256').update(data).digest('hex');
const evidence={status:'running',sourceHashes:{},layers:[],isolated:[],transport:[],sourceSwitches:[],errors:[],qualification:'Engineering rendering/transport QA only; source correspondence and source-radiologist observations are not independent clinical certification.'};
(async()=>{
 const browser=await chromium.launch({headless:true});let page;
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1080},reducedMotion:'reduce',hasTouch:true});
  assert.equal((await context.request.post(base+'/api/profile',{data:{name:'OpenKnee QA',age:35,hours_per_week:3,breadth:'balanced',domains:['radiology']}})).status(),200);
  await context.request.post(base+'/api/profile/settings',{data:{speak:false}});
  const files=['app.js','styles.css','radiology-detailed-anatomy.js','anatomy/openknee-oks003/manifest.json','anatomy/msk-mri-knee/manifest.json','anatomy/msk-atlas/manifest.json'];
  for(const file of files){const r=await context.request.get(base+'/app/'+file);assert.equal(r.status(),200);const h=sha(await r.body());assert.equal(h,sha(fs.readFileSync(path.join(root,'web',file))));evidence.sourceHashes[file]=h;}
  assert.equal(parts.length,16);assert.equal(parts.reduce((n,p)=>n+p.triangles,0),307024);
  assert.equal(manifest.coordinate_system.basis,'RAS');assert.equal(region.side,'left');assert.equal(manifest.clinical_image_pair.available,false);
  const rawPattern=/\.(?:nrrd|nii|dcm|dicom|mha|mhd|raw|nifti)(?:\.gz)?(?:$|[?#])/i;
  const rawFiles=[];function walk(dir){for(const e of fs.readdirSync(dir,{withFileTypes:true})){const f=path.join(dir,e.name);if(e.isDirectory())walk(f);else if(rawPattern.test(f))rawFiles.push(f);}}
  walk(path.join(root,'web'));assert.deepEqual(rawFiles,[],'Research MRI volumes are not in the served static tree');
  page=await context.newPage();page.setDefaultTimeout(60000);
  const requested=[],rawRequests=[],transportTasks=[],transportErrors=[];
  page.on('pageerror',e=>evidence.errors.push(e.message));
  page.on('request',r=>{const p=new URL(r.url()).pathname;if(byFile.has(p))requested.push(p);if(rawPattern.test(r.url()))rawRequests.push(r.url());});
  page.on('response',r=>{const part=byFile.get(new URL(r.url()).pathname);if(!part)return;transportTasks.push((async()=>{
   assert.equal(r.status(),200);const headers=await r.allHeaders();assert.equal(headers['content-encoding'],'gzip');assert.equal(headers['content-type'],'application/octet-stream');
   const bytes=await r.body();assert.equal(bytes.readUInt32LE(0),0x44335042);assert.equal(bytes.length,part.decoded_bytes);assert.equal(bytes.readUInt32LE(4),part.vertices);assert.equal(bytes.readUInt32LE(8),part.triangles*3);assert.equal(sha(bytes),part.decoded_sha256);
   evidence.transport.push({id:part.id,decodedBytes:bytes.length,decodedSha256:sha(bytes),triangles:part.triangles});
  })().catch(e=>transportErrors.push(String(e.stack||e))));});
  await page.goto(base+'/#/radiology/ra.mri-knee');await page.getByRole('tab',{name:'3D anatomy',exact:true}).click();
  const source=page.getByRole('combobox',{name:'Knee anatomy source',exact:true});
  const model=page.locator('.rad-desk-panel:not([hidden]) .detailed-anatomy');
  assert.equal(await source.inputValue(),'malaya-mri','Original default remains unchanged');await ready('malaya-mri');
  await switchSource('openknee-oks003');
  assert.equal(Number(await model.getAttribute('data-meshes')),16);assert.equal(Number(await model.getAttribute('data-triangles')),307024);
  assert.deepEqual([...new Set(requested)].sort(),parts.filter(p=>p.layer==='bone').map(p=>p.file).sort(),'Only four bones requested initially');
  evidence.initialBoneRequests=[...new Set(requested)];
  assert.deepEqual(await model.locator('[data-part]').evaluateAll(es=>es.map(e=>e.dataset.part).sort()),parts.map(p=>p.id).sort());
  const note=await model.locator('.detailed-anatomy-note').textContent();
  for(const text of ['25-year-old female cadaveric donor','Native RAS millimeter','not co-registered','not separately delineated','0.5 mm','clinical certification','CC BY-SA 3.0 Unported'])assert.ok(note.includes(text),'Visible source limitation: '+text);
  assert.equal(await model.getByRole('link',{name:manifest.license,exact:true}).getAttribute('href'),manifest.license_url);
  await capture('openknee-default-desktop');
  const loaded=new Set(['bone']);
  for(const [layer,label] of region.layers){
   await layerSelect(layer,label);loaded.add(layer);
   const ids=parts.filter(p=>p.layer===layer).map(p=>p.id).sort();
   assert.deepEqual(await model.locator('[data-part]:visible').evaluateAll(es=>es.map(e=>e.dataset.part).sort()),ids);
   assert.ok(requested.every(f=>loaded.has(byFile.get(f).layer)),'No future layer fetched early');
   evidence.layers.push({layer,objects:ids.length,...await pixelStats()});await capture('openknee-layer-'+layer);
  }
  await Promise.all(transportTasks);assert.deepEqual(transportErrors,[]);
  assert.deepEqual([...new Set(requested)].sort(),parts.map(p=>p.file).sort());assert.equal(new Set(evidence.transport.map(p=>p.id)).size,16);
  await layerSelect('all','Together');await capture('openknee-together-desktop');
  for(const [button,label] of [['Anterior','Anterior'],['Lateral','Left lateral'],['Medial','Right lateral'],['Superior','Superior']]){
   await model.getByRole('button',{name:button,exact:true}).click();await settled();assert.match(await model.locator('.detailed-anatomy-orientation').textContent(),new RegExp('^left · '+label+'$'));
  }
  await model.getByRole('button',{name:'Reset',exact:true}).click();await settled();assert.equal(await model.locator('canvas').getAttribute('data-view'),'-0.22,0.10');
  const selectedScreens=new Set(['oks003-fmc','oks003-tbc-l','oks003-tbc-m','oks003-mns-m','oks003-mns-l','oks003-acl']);
  for(const part of parts){
   const label=region.layers.find(([l])=>l===part.layer)[1];await layerSelect(part.layer,label);
   await model.locator('[data-part="'+part.id+'"]').focus();await page.keyboard.press('Enter');
   await model.getByRole('button',{name:'Isolate',exact:true}).click();await settled();
   assert.equal(await model.locator('canvas').getAttribute('data-cropped'),'false');assert.equal(await model.locator('.detailed-anatomy-selected').textContent(),part.name);
   const pixels=await pixelStats();evidence.isolated.push({id:part.id,name:part.name,triangles:part.triangles,...pixels});
   if(selectedScreens.has(part.id)){
    await model.getByRole('button',{name:'Superior',exact:true}).click();await settled();await capture(part.id+'-isolated-superior');
    await page.setViewportSize({width:390,height:844});await settled();await noOverflow();await pixelStats();await capture(part.id+'-isolated-mobile');await page.setViewportSize({width:1440,height:1080});await settled();
   }
   if(part.id==='oks003-acl'){
    await model.getByRole('button',{name:'Anterior',exact:true}).click();await settled();
    const canvas=model.locator('canvas'),before=await canvas.evaluate(c=>c.toDataURL());await canvas.focus();await page.keyboard.press('ArrowRight');await settled();assert.notEqual(await canvas.evaluate(c=>c.toDataURL()),before);assert.match(await model.locator('.detailed-anatomy-orientation').textContent(),/Rotated view/);
   }
   await model.getByRole('button',{name:'Reset',exact:true}).click();await settled();assert.equal(await model.locator('canvas').getAttribute('data-layer'),'bone');assert.equal(await model.locator('canvas').getAttribute('data-view'),'-0.22,0.10');
  }
  await model.getByRole('button',{name:'Full structures',exact:true}).click();await settled();assert.equal(await model.locator('canvas').getAttribute('data-cropped'),'false');await pixelStats();await capture('openknee-full-structures');
  await model.getByRole('button',{name:'Reset',exact:true}).click();await settled();assert.equal(await model.locator('canvas').getAttribute('data-cropped'),'true');
  await page.setViewportSize({width:390,height:844});await settled();await noOverflow();await capture('openknee-default-mobile');
  await switchSource('malaya-mri');assert.equal(Number(await model.getAttribute('data-meshes')),30);assert.ok((await model.locator('[data-part]').evaluateAll(es=>es.map(e=>e.dataset.part))).every(id=>id.startsWith('um-knee-')));await pixelStats();
  await switchSource('z-anatomy');assert.ok((await model.locator('[data-part]').evaluateAll(es=>es.map(e=>e.dataset.part))).every(id=>id.startsWith('za-')));await pixelStats();
  await switchSource('openknee-oks003');assert.equal(Number(await model.getAttribute('data-meshes')),16);assert.ok((await model.locator('[data-part]').evaluateAll(es=>es.map(e=>e.dataset.part))).every(id=>id.startsWith('oks003-')));await pixelStats();await capture('openknee-return-mobile');
  await Promise.all(transportTasks);assert.deepEqual(transportErrors,[]);assert.deepEqual(rawRequests,[]);assert.deepEqual(evidence.errors,[]);
  for(const [file,digest]of Object.entries(evidence.sourceHashes))assert.equal(sha(fs.readFileSync(path.join(root,'web',file))),digest,file+': frozen source');
  evidence.rawStaticFiles=0;evidence.rawScanRequests=0;evidence.sourceMeshes=16;evidence.sourceTriangles=307024;evidence.status='passed';
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(evidence,null,2)+'\n');console.log('PASS OpenKnee:16 decoded meshes/307024 facets,5 layers,16 isolated objects,left-side presets,mobile,three-provider disposal/no overlay. '+out);
  async function settled(){await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));}
  async function ready(atlas){await page.waitForFunction(atlas=>{const m=document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy');if(m?.dataset.error)throw new Error(m.textContent);return m?.dataset.atlas===atlas&&m.dataset.ready==='true'&&m.querySelector('canvas')?.dataset.rendered==='true';},atlas,{timeout:120000});await settled();}
  async function switchSource(atlas){const previous=await model.getAttribute('data-atlas'),old=await model.locator('canvas').elementHandle();await source.selectOption(atlas);await ready(atlas);await page.waitForFunction(c=>!c.isConnected&&c.getContext('webgl').isContextLost(),old);assert.equal(await page.locator('.rad-anatomy-model-host .detailed-anatomy').count(),1);evidence.sourceSwitches.push({from:previous,to:atlas,oldContextDisposed:true,singleProvider:true});}
  async function layerSelect(layer,label){await model.getByRole('button',{name:label,exact:true}).click();await page.waitForFunction(layer=>document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy canvas')?.dataset.layer===layer,layer);await settled();}
  async function pixelStats(){await settled();const result=await model.locator('canvas').evaluate(c=>{const gl=c.getContext('webgl'),a=new Uint8Array(c.width*c.height*4);gl.readPixels(0,0,c.width,c.height,gl.RGBA,gl.UNSIGNED_BYTE,a);let pixels=0;for(let i=3;i<a.length;i+=4)if(a[i]>20)pixels++;return{pixels,error:gl.getError()};});assert.equal(result.error,0);assert.ok(result.pixels>100,'Visible native source geometry');return result;}
  async function noOverflow(){assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
  async function capture(name){await model.locator('.detailed-anatomy-stage').evaluate(e=>e.scrollIntoView({block:'center',behavior:'instant'}));await settled();await page.screenshot({path:path.join(out,name+'.png'),animations:'disabled',timeout:30000});}
 }catch(error){evidence.status='failed';evidence.failure=String(error.stack||error);if(page)await page.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify(evidence,null,2)+'\n');throw error;}finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
