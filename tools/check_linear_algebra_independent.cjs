'use strict';
// Fixed repository module; stdin contains bounded numerical fixtures, never paths.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const file=path.join(__dirname,'..','web','linear-algebra-lab.js');
const bytes=fs.readFileSync(file),api=require(file);
const allowed=new Set(['rational','analyze','multiply','apply','power','maps','system','space','kernel','spectrum','orbit','planes','projection3D']);
function numerical(){
const requests=JSON.parse(fs.readFileSync(0,'utf8'));
if(!Array.isArray(requests)||requests.length>500)throw Error('Expected bounded fixture list.');
const freeze=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};
const results=requests.map(r=>{if(!allowed.has(r.method))throw Error('Unknown scientific method.');let args=r.args||[];if(r.nonfinite){if(r.method!=='rational'||!['NaN','Infinity','-Infinity'].includes(r.nonfinite))throw Error('Unknown nonfinite fixture.');args=[Number(r.nonfinite)];}try{return {id:r.id,result:api[r.method](...freeze(args))};}catch(error){return {id:r.id,error:{name:error.name,message:error.message}};}});
if(!bytes.equals(fs.readFileSync(file)))throw Error('Source changed during verification.');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
process.stdout.write(JSON.stringify({sourceSHA256:sha(bytes),purePrefixSHA256:sha(Buffer.from(bytes.toString().split('function render(')[0])),results}));
}

// Self-contained: suitable for page.locator('[data-linalg-lab]').evaluate(captureSnapshot).
function captureSnapshot(root){
  const state=root.linalg.getState(),station=state.station,panel=root.querySelector(`[data-linalg-panel="${station}"]`);
  const attrs=node=>Object.fromEntries(Array.from(node.attributes).map(a=>[a.name,a.value]));
  const plots=Array.from(panel.querySelectorAll('[data-linalg-plot]')).map(svg=>({id:svg.getAttribute('data-linalg-plot'),viewBox:svg.getAttribute('viewBox').split(/\s+/).map(Number),domain:JSON.parse(svg.getAttribute('data-axis-domain')),projection:svg.hasAttribute('data-projection')?JSON.parse(svg.getAttribute('data-projection')):null,primitives:Array.from(svg.querySelectorAll('[data-world]')).map(node=>({tag:node.tagName,attrs:attrs(node)})),text:Array.from(svg.querySelectorAll('text')).map(node=>{const b=node.getBBox();return{text:node.textContent,x:b.x,y:b.y,width:b.width,height:b.height,attrs:attrs(node)};})}));
  return {station,state,model:root.linalg.getModels()[station],error:panel.getAttribute('data-error'),text:panel.textContent,paragraphs:Array.from(panel.querySelectorAll('[data-linalg-output] > p')).map(p=>p.textContent),plots,tables:Array.from(panel.querySelectorAll('table')).map(table=>({caption:table.querySelector('caption')?.textContent,rows:Array.from(table.querySelectorAll('tbody tr')).map(row=>Array.from(row.children).map(cell=>cell.textContent))})),controls:Array.from(panel.querySelectorAll('[data-linalg-control]')).map(node=>({key:node.getAttribute('data-linalg-control'),value:node.value,type:node.type,disabled:node.disabled})),documentOverflow:document.documentElement.scrollWidth>innerWidth+1,rootWidth:root.getBoundingClientRect().width};
}

function verifySnapshots(snapshots){
  const assert=require('node:assert/strict'),cp=require('node:child_process');
  if(!Array.isArray(snapshots)||snapshots.length>500)throw Error('Expected bounded snapshot list.');
  const scientific='/Users/peter/Documents/ChatGPT/Primer/.research/runtime-grade-py312-20261008/bin/python';
  let python='python3';
  if(process.env.PRIMER_INDEPENDENT_PYTHON===scientific)python=scientific;
  else if(process.env.PRIMER_INDEPENDENT_PYTHON&&process.env.PRIMER_INDEPENDENT_PYTHON!=='python3')throw Error('Use python3 or the configured scientific Python runtime.');
  const states=snapshots.map((s,i)=>({id:i,station:s.station,state:s.state}));
  const expected=JSON.parse(cp.execFileSync(python,[path.join(__dirname,'check_linear_algebra_independent.py'),'--snapshot-oracles'],{input:JSON.stringify(states),encoding:'utf8',timeout:60000,maxBuffer:64*1024*1024}));
  const num=value=>{if(typeof value==='number')return value;const p=String(value).split('/');return Number(p[0])/Number(p[1]||1);};
  const near=(a,b,label,relative=2e-11,absolute=1e-9)=>assert.ok(Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=absolute+relative*Math.max(Math.abs(a),Math.abs(b)),`${label}: ${a} != ${b}`);
  const subset=(actual,want,label)=>{if(Array.isArray(want)){assert.ok(Array.isArray(actual),label);assert.equal(actual.length,want.length,label+' length');want.forEach((v,i)=>subset(actual[i],v,label+'['+i+']'));}else if(want&&typeof want==='object'){for(const[k,v]of Object.entries(want))subset(actual[k],v,label+'.'+k);}else assert.equal(actual,want,label);};
  const receipt={cases:[],allPassed:false,method:expected.method};
  for(let i=0;i<snapshots.length;i++){
    const snapshot=snapshots[i],oracle=expected.oracles[i],label=(snapshot.id||i)+' '+snapshot.station;
    assert.equal(snapshot.documentOverflow,false,label+' document overflow');
    if(oracle.error){assert.ok(snapshot.error,label+' invalid domain must be reported');assert.equal(snapshot.plots.length,0,label+' stale geometry cleared');assert.equal(snapshot.tables.length,0,label+' stale tables cleared');receipt.cases.push({id:snapshot.id||i,station:snapshot.station,invalidInputRejected:true});continue;}
    assert.equal(snapshot.error,null,label+' unexpected renderer error');subset(snapshot.model,oracle.facts,label+' independent exact model facts');
    for(const paragraph of snapshot.paragraphs||[])assert.ok(!(paragraph.includes('≈')&&paragraph.includes(' exactly.')),label+' approximate value labelled exact');
    for(const control of snapshot.controls){const field=control.key.split('.')[1],value=snapshot.state[snapshot.station][field];if(control.type==='range')near(Number(control.value),Number(value),label+' camera/control value');else assert.equal(control.value,String(value),label+' control value');}
    assert.deepEqual(snapshot.plots.map(p=>p.id).sort(),Object.keys(oracle.plots).sort(),label+' actual plot inventory');
    let primitives=0,points=0;
    for(const plot of snapshot.plots){
      const series=oracle.plots[plot.id],domain=plot.domain;
      for(const text of plot.text.filter(t=>/^[-+−]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?$/i.test(t.text))){assert.ok(text.x>=plot.viewBox[0]-1&&text.x+text.width<=plot.viewBox[0]+plot.viewBox[2]+1,label+' numeric SVG label clipped: '+text.text);}
      assert.ok(domain.x[1]>domain.x[0]&&domain.y[1]>domain.y[0],label+' finite nonzero axis ranges');
      if(domain.equalUnits)near((domain.right-domain.left)/(domain.x[1]-domain.x[0]),(domain.bottom-domain.top)/(domain.y[1]-domain.y[0]),label+' equal coordinate scales');
      const P=plot.projection?.matrix;
      if(P){assert.equal(plot.projection.kind,'orthographic');for(let a=0;a<3;a++)for(let b=0;b<3;b++)near(P[a].reduce((s,x,j)=>s+x*P[b][j],0),a===b?1:0,label+' orthonormal camera');const state=snapshot.state[snapshot.station];near(plot.projection.yaw,Number(state.yaw),label+' yaw');near(plot.projection.pitch,Number(state.pitch),label+' pitch');}
      const names=plot.primitives.map(p=>p.attrs['data-series']);assert.equal(new Set(names).size,names.length,label+' unique series ids');assert.deepEqual(names.slice().sort(),Object.keys(series).sort(),label+' complete actual series '+plot.id);
      for(const primitive of plot.primitives){
        const name=primitive.attrs['data-series'],target=series[name],world=JSON.parse(primitive.attrs['data-world']),exact=JSON.parse(primitive.attrs['data-exact-world']);let wanted=target.world.map(p=>p.map(num));assert.equal(world.length,wanted.length,label+' world point count '+name);assert.equal(exact.length,wanted.length);
        if(target.unordered){const unused=wanted.slice();wanted=world.map(p=>{let best=0,distance=Infinity;unused.forEach((q,j)=>{const d=p.reduce((sum,v,k)=>sum+(v-q[k])**2,0);if(d<distance){distance=d;best=j;}});return unused.splice(best,1)[0];});}
        const actual=primitive.tag.toLowerCase()==='circle'?[[Number(primitive.attrs.cx),Number(primitive.attrs.cy)]]:primitive.attrs.points.trim().split(/\s+/).map(pair=>pair.split(',').map(Number));assert.equal(actual.length,wanted.length,label+' actual SVG vertices '+name);
        wanted.forEach((p,j)=>{assert.equal(world[j].length,p.length);p.forEach((value,k)=>{near(world[j][k],value,label+' independent world '+name,2e-11,1e-9);near(num(exact[j][k]),value,label+' exact/world metadata '+name,2e-11,1e-9);});const projected=P?P.slice(0,2).map(row=>row.reduce((s,x,k)=>s+x*p[k],0)):p;const x=domain.left+(projected[0]-domain.x[0])/(domain.x[1]-domain.x[0])*(domain.right-domain.left),y=domain.bottom-(projected[1]-domain.y[0])/(domain.y[1]-domain.y[0])*(domain.bottom-domain.top);near(actual[j][0],x,label+' actual SVG x '+name,2e-10,1e-6);near(actual[j][1],y,label+' actual SVG y '+name,2e-10,1e-6);assert.ok(actual[j][0]>=domain.left-1e-5&&actual[j][0]<=domain.right+1e-5&&actual[j][1]>=domain.top-1e-5&&actual[j][1]<=domain.bottom+1e-5,label+' clipped plotted point '+name);points++;});
        if(snapshot.station==='orbits'&&name.startsWith('norm-')&&name!=='norm-history'){const n=Number(primitive.attrs['data-iteration']);assert.equal(primitive.attrs['data-exact-norm-squared'],oracle.facts.points[n].normSquared,label+' exact squared norm at plotted point');}
        primitives++;
      }
    }
    if(snapshot.station==='kernel'){
      assert.equal(snapshot.plots[0].projection,null,label+' no fictitious 4D spatial projection');assert.match(snapshot.text,/neither 4D geometry nor a projection/);assert.ok(!snapshot.text.includes('ordinary area factor'),label+' determinant is not 2D area factor');if(snapshot.state.kernel.kind==='4x4')assert.match(snapshot.text,/4D volume/);
      const table=snapshot.tables.find(t=>t.caption==='All coordinate values, exactly');assert.ok(table);assert.equal(table.rows.length,4);table.rows.forEach((row,j)=>{assert.equal(row[1],oracle.facts.baseInput[j]);assert.equal(row[2],oracle.facts.input[j]);if(j<oracle.facts.rows)assert.equal(row[3],oracle.facts.output[j]);else assert.match(row[3],/Not a coordinate/);});
    }
    if(snapshot.station==='orbits'){
      const table=snapshot.tables.find(t=>t.caption==='Complete finite orbit');assert.ok(table);assert.equal(table.rows.length,oracle.facts.points.length);table.rows.forEach((row,j)=>{assert.equal(row[0],String(j));assert.equal(row[1],oracle.facts.points[j].value.join(', '));assert.equal(row[2],oracle.facts.points[j].normSquared);});assert.match(snapshot.text,/No orbit normalization/);assert.equal(snapshot.text.includes('A zero slow-mode coefficient is an exceptional start.'),snapshot.state.orbits.kind.startsWith('decay-'),label+' slow-mode exception limited to decay models');
    }
    if(snapshot.station==='spectrum'&&snapshot.state.spectrum.kind==='rotation')assert.match(snapshot.text,/no nonzero real eigenvector/);
    receipt.cases.push({id:snapshot.id||i,station:snapshot.station,primitives,projectedPoints:points,exactModelAndWorldGeometry:true});
  }
  receipt.allPassed=true;return receipt;
}

module.exports={captureSnapshot,verifySnapshots};

async function browserReview(){
  const assert=require('node:assert/strict'),{chromium}=require('playwright');
  const ROOT=path.join(__dirname,'..'),OUT=path.join(ROOT,'docs/linear-algebra-fidelity-review-20261016/independent-review'),write=process.argv.includes('--write-proof');
  const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
  if(write)fs.mkdirSync(OUT,{recursive:true});
  const report={sourceSHA256:sha(bytes),scope:'Independent standalone actual SVG/world geometry and exact table verification, from ordinary control states. Authenticated reader verification is separate.',snapshots:[],screenshots:[],pageErrors:[],allPassed:false};
  const browser=await chromium.launch({headless:true});
  try{
    for(const width of [390,1440]){
      const page=await browser.newPage({viewport:{width,height:1000}});page.on('pageerror',e=>report.pageErrors.push(String(e)));
      await page.setContent('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font-family:Arial,sans-serif;margin:16px}main{max-width:1100px;margin:auto;min-width:0}[hidden]{display:none!important}</style><main></main></html>');
      await page.addScriptTag({content:bytes.toString()});await page.evaluate(()=>document.querySelector('main').append(PrimerLinearAlgebraLab.render({props:{scenario:'math.4.linalg'}})));
      const root=page.locator('[data-linalg-lab]');
      async function capture(name){const snapshot=await root.evaluate(captureSnapshot);snapshot.id=width+':'+snapshot.station+':'+name;report.snapshots.push(snapshot);return snapshot;}
      async function state(station,edits={},name='default'){
        await page.locator('[data-linalg-action="reset"]').click();await page.selectOption('[data-linalg-control="station"]',station);
        for(const [key,value] of Object.entries(edits)){
          const input=page.locator(`[data-linalg-control="${station}.${key}"]`);if(await input.isDisabled())continue;
          const tag=await input.evaluate(e=>e.tagName);if(tag==='SELECT')await input.selectOption(String(value));else{await input.fill(String(value));await input.dispatchEvent((await input.getAttribute('type'))==='range'?'input':'change');}
        }
        const snapshot=await capture(name);
        if(write&&name==='default'&&['space','kernel','orbits'].includes(station)){const png=`independent-${width}-${station}.png`;await page.locator(`[data-linalg-panel="${station}"]`).screenshot({path:path.join(OUT,png)});report.screenshots.push({file:png,sha256:sha(fs.readFileSync(path.join(OUT,png)))});}
        return snapshot;
      }
      for(const station of ['maps','systems','planes','space','kernel','spectrum','orbits'])await state(station);
      for(const [name,edits]of [['composition',{a00:1,a01:1,a10:0,a11:1,x:0,y:1}],['negative',{a00:1,a01:0,a10:0,a11:-1,x:-2,y:3}],['rank-one',{a00:1,a01:2,a10:2,a11:4,x:-2,y:1}],['zero',{a00:0,a01:0,a10:0,a11:0}],['tiny-fraction',{a00:'1e-12',a01:0,a10:0,a11:1,x:'1e-12',y:0}]])await state('maps',edits,name);
      for(const [name,edits]of [['minus4',{k:-4}],['unique',{k:0}],['distant',{k:'4001/1000'}],['very-distant',{k:'4000000000001/1000000000000'}],['infinite',{k:4,rhs2:2,free:8}]])await state('systems',edits,name);
      for(const kind of ['unique','dependent','coincident','inconsistent','parallel'])await state('planes',{kind,s:4,t:-4,yaw:-60,pitch:35},kind);
      for(const [name,edits]of [['positive',{t:'1/8'}],['negative',{t:'-1/8'}],['near-plane',{t:'1/1000000000000'}],['large-coefficients',{t:4,c1:-4,c2:4,c3:-4}],['repeated',{kind:'repeated'}],['line',{kind:'rank1'}],['zero',{kind:'zero'}]])await state('space',edits,name);
      await state('space');for(const action of ['space-face','space-edge']){await page.locator(`[data-linalg-action="${action}"]`).click();await capture(action);}
      for(const kind of ['4x4','3x4','2x4'])await state('kernel',{kind,s:-8,t:8},kind);
      for(const kind of ['diag35','tri235','tri124','identity','shear','rotation','eigenpower','decay-diagonal','decay-nonnormal','reflection'])await state('spectrum',{kind,yaw:90,pitch:0},kind);
      for(const [name,edits]of [['n2',{n:2}],['n3',{n:3}],['late',{n:100}],['fast',{x:1,y:0,n:100}],['slow',{x:25,y:1,n:30}],['zero',{x:0,y:0,n:100}],['eigenpower',{kind:'eigenpower',x:1,y:0,n:3}],['eigenpower100',{kind:'eigenpower',x:1,y:0,n:100}],['rotation',{kind:'rotation',x:1,y:0,n:4}],['rotation100',{kind:'rotation',x:3,y:4,n:100}],['identity100',{kind:'identity',x:1,y:1,n:100}],['shear',{kind:'shear',x:0,y:1,n:20}],['reflection',{kind:'reflection',x:1,y:0,n:4}],['n0',{n:0}]])await state('orbits',edits,name);
      for(const [station,setup,field,value]of [['maps',{},'a00','1/0'],['systems',{},'k','bad'],['planes',{kind:'coincident'},'s','5'],['space',{},'t','5'],['kernel',{},'s','9'],['orbits',{},'x','bad']]){await state(station,setup,'before-invalid');const input=page.locator(`[data-linalg-control="${station}.${field}"]`);await input.fill(value);await input.dispatchEvent('change');await capture('invalid');await state(station,{},'recovered');}
      await page.locator('[data-linalg-action="enlarge"]').click();await capture('enlarged');await page.locator('[data-linalg-action="enlarge"]').click();await capture('fit');
      await page.close();
    }
    report.verification=verifySnapshots(report.snapshots);assert.deepEqual(report.pageErrors,[]);assert.ok(bytes.equals(fs.readFileSync(file)),'source changed during standalone verification');report.allPassed=true;
    if(write){const decoded=Buffer.from(JSON.stringify(report.snapshots)+'\n'),encoded=require('node:zlib').gzipSync(decoded,{level:9});fs.writeFileSync(path.join(OUT,'renderer-snapshots.json.gz'),encoded);const {snapshots,...compact}=report;compact.snapshotArchive={file:'renderer-snapshots.json.gz',encoding:'gzip',decodedFormat:'JSON snapshot array',decodedSHA256:sha(decoded),decodedBytes:decoded.length,storedSHA256:sha(encoded),storedBytes:encoded.length};compact.states=snapshots.map(s=>({id:s.id,station:s.station,state:s.state[s.station]}));fs.writeFileSync(path.join(OUT,'renderer-review.json'),JSON.stringify(compact,null,2)+'\n');}
    console.log(JSON.stringify({allPassed:true,sourceSHA256:report.sourceSHA256,cases:report.snapshots.length,geometryPoints:report.verification.cases.reduce((n,c)=>n+(c.projectedPoints||0),0),invalidCases:report.verification.cases.filter(c=>c.invalidInputRejected).length}));
  }finally{await browser.close();}
}
if(require.main===module){if(process.argv.includes('--browser'))browserReview().catch(e=>{console.error(e);process.exitCode=1;});else numerical();}
