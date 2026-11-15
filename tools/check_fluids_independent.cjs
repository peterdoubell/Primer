'use strict';
// Fixed repository input; stdin accepts numerical test cases, never filesystem paths.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const source = path.join(__dirname, '..', 'web', 'fluids-lab.js');
const bytes = fs.readFileSync(source);
const api = require(source);
const allowed = new Set(['continuity', 'hydrostatics', 'pistons', 'hull', 'pipe', 'blasiusSolve', 'boundaryLayer', 'settling', 'joukowski', 'plume']);
function numerical() {
const requests = JSON.parse(fs.readFileSync(0, 'utf8'));
if (!Array.isArray(requests) || requests.length > 500) throw new Error('Expected bounded numerical request list.');
const results = requests.map(request => {
  if (!allowed.has(request.method)) throw new Error('Unknown scientific API.');
  try {
    const result = api[request.method](request.input || {});
    const samplesAt = request.probes ? request.probes.map(value => result.at(value)) : undefined;
    return {id: request.id, result: {...result, samplesAt}};
  } catch (error) { return {id: request.id, error: {name: error.name, message: error.message}}; }
});
if (!bytes.equals(fs.readFileSync(source))) throw new Error('Source changed while checking.');
process.stdout.write(JSON.stringify({sourceSHA256: crypto.createHash('sha256').update(bytes).digest('hex'), results}));
}

async function renderer() {
  const assert = require('node:assert/strict');
  const {chromium} = require('playwright');
  const root = path.join(__dirname, '..');
  const output = path.join(root, 'docs/fluids-fidelity-review-20261016/independent-review');
  const oracles = JSON.parse(fs.readFileSync(path.join(output, 'renderer-oracles.json'), 'utf8'));
  const write = process.argv.includes('--write-proof');
  const hash = value => crypto.createHash('sha256').update(value).digest('hex');
  const proof = {sourceSHA256: hash(bytes), oracleSHA256: hash(fs.readFileSync(path.join(output, 'renderer-oracles.json'))), scope: 'Independent standalone mount and rendered SVG coordinate/control audit. Actual authenticated reader delivery is checked separately.', cases: [], errors: [], screenshots: [], allPassed: false};
  const near = (a,b,label,rel=2e-8,absolute=1e-9) => assert.ok(Number.isFinite(a) && Math.abs(a-b) <= absolute + rel*Math.abs(b), `${label}: ${a} != ${b}`);
  const browser = await chromium.launch({headless:true});
  try {
    for (const width of [390,1440]) {
      const page = await browser.newPage({viewport:{width,height:1000}});
      page.on('pageerror', error=>proof.errors.push(String(error)));
      await page.setContent('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font-family:Arial,sans-serif;margin:16px}main{max-width:1100px;margin:auto}button,input,select{font:inherit}[hidden]{display:none!important}</style><main></main></html>');
      await page.addScriptTag({content:bytes.toString('utf8')});
      await page.evaluate(()=>document.querySelector('main').append(window.PrimerFluidsLab.render({title:'Independent fluids rendering check',props:{scenario:'phys.4.fluids'}})));
      async function state(name, station, edits={}) {
        await page.locator('[data-fluids-action="reset"]').click();
        await page.locator('[data-fluids-control="station"]').selectOption(station);
        for (const [field,value] of Object.entries(edits)) {
          const input=page.locator(`[data-fluids-control="${station}.${field}"]`);
          await input.fill(String(value)); await input.dispatchEvent('change');
        }
        const snapshot=await page.evaluate(station=>{
          const root=document.querySelector('[data-fluids-lab]'),panel=root.querySelector(`[data-fluids-panel="${station}"]`);
          const attributes=element=>Object.fromEntries(Array.from(element.attributes).map(a=>[a.name,a.value]));
          return {state:root.fluids.getState(),models:root.fluids.getModels(),text:panel.textContent,error:panel.getAttribute('data-error'),plots:Array.from(panel.querySelectorAll('svg')).map(svg=>({domain:JSON.parse(svg.getAttribute('data-axis-domain')),title:svg.getAttribute('data-fluids-plot'),series:Array.from(svg.querySelectorAll('[data-fluids-series]')).map(node=>({tag:node.tagName,attrs:attributes(node)})),geometry:Array.from(svg.querySelectorAll('[data-fluids-cylinder],[data-fluids-piston],[data-fluids-hull],[data-fluids-submerged],[data-fluids-probe],[data-fluids-pressure-arrow],[data-fluids-speed-arrow],[data-fluids-speed-zero],[data-fluids-head]')).map(node=>({tag:node.tagName,attrs:attributes(node)}))})),overflow:document.documentElement.scrollWidth>innerWidth+1,controlValues:Object.fromEntries(Array.from(panel.querySelectorAll('input')).map(n=>[n.getAttribute('data-fluids-control'),n.valueAsNumber]))};
        },station);
        assert.equal(snapshot.error,null,name); assert.equal(snapshot.overflow,false,name+' horizontal overflow');
        for (const [field,value] of Object.entries(edits)) {assert.equal(snapshot.state[station][field],value);assert.equal(snapshot.controlValues[station+'.'+field],value);}
        const m=snapshot.models[station],checked=[];
        const decode=(x,y,d)=>[d.x[0]+(x-d.left)/(d.right-d.left)*(d.x[1]-d.x[0]),d.y[0]+(d.bottom-y)/(d.bottom-d.top)*(d.y[1]-d.y[0])];
        const series=(id,expected)=>{
          const plot=snapshot.plots.find(p=>p.series.some(s=>s.attrs['data-fluids-series']===id)); assert.ok(plot,id);
          const node=plot.series.find(s=>s.attrs['data-fluids-series']===id);
          const points=node.attrs.points.trim().split(/\s+/).map(s=>s.split(',').map(Number)).map(([x,y])=>decode(x,y,plot.domain));
          assert.equal(points.length,expected.length,id+' complete samples');
          points.forEach((p,i)=>{near(p[0],expected[i][0],id+' x',3e-8,1e-9);near(p[1],expected[i][1],id+' y',3e-8,1e-8);});checked.push({series:id,points:points.length});
        };
        if(station==='continuity') {
          const a=Math.sqrt(m.areaIn/Math.PI)*1000,b=Math.sqrt(m.areaThroat/Math.PI)*1000;
          const upper=[[0,a],[.2,a],[.35,b],[.55,b],[.7,a],[.9,a]];
          series('venturi-upper',upper);series('venturi-lower',upper.map(([x,y])=>[x,-y]));
          const plot=snapshot.plots[0],heads=snapshot.plots[1];
          for(let i=0;i<3;i++) {
            const section=m.sections[i],speed=m.flow/section.area;
            if(speed===0)assert.ok(plot.geometry.some(g=>g.attrs['data-fluids-speed-zero']===section.name));
            else {
              const arrow=plot.geometry.find(g=>g.attrs['data-fluids-speed-arrow']===section.name).attrs;
              const from=decode(Number(arrow.x1),Number(arrow.y1),plot.domain),to=decode(Number(arrow.x2),Number(arrow.y2),plot.domain);
              near(to[0]-from[0],speed*.015,'common speed gain in SI seconds');near(from[1],0,'arrow baseline');near(to[1],0,'arrow baseline');
            }
            const h=heads.geometry.find(g=>g.attrs['data-fluids-head']===section.name).attrs;
            const top=decode(Number(h.x2),Number(h.y2),heads.domain),bottom=decode(Number(h.x1),Number(h.y1),heads.domain);
            near(top[0],i,'head section index');near(bottom[1],0,'common head datum');near(top[1],section.gauge/(m.rho*m.g),'pressure head SVG endpoint');
          }
          if(name==='exact-quiz'){near(m.inletSpeed,2,'quiz2m/s');near(m.throatSpeed,8,'quiz8m/s');near(m.pressureDrop,30000,'quiz30kPa');assert.ok(snapshot.text.includes('30 kPa'));}
          if(!m.singlePhaseAllowed)assert.ok(snapshot.text.includes('violates'));
          checked.push({speedAndHeadMarkers:6});
        }
        if (station==='hydrostatics') {
          const h=(m.ambientPressure-m.topPressure)/(m.rho*m.g);
          const rows=Array.from({length:51},(_,i)=>{const z=h*i/50;return [(m.ambientPressure-m.rho*m.g*z)/1000,z];});
          series('absolute-pressure',rows);series('gauge-pressure',rows.map(([p,z])=>[p-m.ambientPressure/1000,z]));
          if(m.topPressure<m.vaporPressure)assert.ok(snapshot.text.includes('violates'));
        }
        if (station==='pistons'||station==='hull') {
          const plot=snapshot.plots[0],d=plot.domain;
          near((d.right-d.left)/(d.x[1]-d.x[0]),(d.bottom-d.top)/(d.y[1]-d.y[0]),'equal geometric metre axes');
          if(station==='pistons') {
            for(const side of ['input','output']) {
              const rect=plot.geometry.find(g=>g.attrs['data-fluids-cylinder']===side).attrs;
              const radius=Math.sqrt((side==='input'?m.areaIn:m.areaOut)/Math.PI);
              near(Number(rect.height)*(d.y[1]-d.y[0])/(d.bottom-d.top),2*radius,'physical cylinder diameter');
              const line=plot.geometry.find(g=>g.attrs['data-fluids-piston']===side).attrs;
              near(decode(Number(line.x1),Number(line.y1),d)[0],side==='input'?m.strokeIn:1.1+m.areaIn*m.strokeIn/m.areaOut,'piston face displacement');
            }
          } else {
            const rect=plot.geometry.find(g=>g.attrs['data-fluids-hull']).attrs;
            near(Number(rect.width)*(d.x[1]-d.x[0])/(d.right-d.left),m.length,'physical hull length');
            near(Number(rect.height)*(d.y[1]-d.y[0])/(d.bottom-d.top),m.height,'physical hull height');
            const submerged=plot.geometry.find(g=>g.attrs['data-fluids-submerged']).attrs;
            near(Number(submerged.height)*(d.y[1]-d.y[0])/(d.bottom-d.top),Math.min(m.height,(m.dryMass+m.cargoMass+m.retainedWaterMass)/(m.rho*m.length*m.width)),'physical draft');
          }
          checked.push({geometry:station});
        }
        if(station==='pipe') {
          const values=Array.from({length:201},(_,i)=>{const r=m.radius*(i-100)/100;return [m.pressureDrop*(m.radius*m.radius-r*r)/(4*m.mu*m.length),r*1000];});
          series('pipe-velocity',values);
          series('annular-flux',Array.from({length:101},(_,i)=>{const r=m.radius*i/100;return [r*1000,2*Math.PI*r*m.pressureDrop*(m.radius*m.radius-r*r)/(4*m.mu*m.length)];}));
          series('pipe-shear',Array.from({length:101},(_,i)=>{const r=m.radius*i/100;return [r*1000,-m.pressureDrop*r/(2*m.length)];}));
        }
        if(station==='boundary') {
          const scale=Math.sqrt(m.nu*m.x/m.speed);
          series('blasius-u',oracles.blasius.map(p=>[p.fp*m.speed,p.eta*scale*1000]));
          series('boundary-growth',Array.from({length:101},(_,i)=>{const x=m.x*(.25+3.75*i/100);return [x,oracles.eta99*Math.sqrt(m.nu*x/m.speed)*1000];}));
        }
        if(station==='settling') {
          const tau=2*m.particleDensity*m.radius*m.radius/(9*m.mu),vt=2*m.radius*m.radius*(m.particleDensity-m.fluidDensity)*m.g/(9*m.mu);
          series('settling-velocity',Array.from({length:121},(_,i)=>{const q=Math.max(5,snapshot.state.settling.timeFactor)*i/120;return [q*tau,-vt*Math.expm1(-q)];}));
          near(m.time,snapshot.state.settling.timeFactor*tau,'control nondimensional time mapped to seconds');
        }
        if(station==='lift') {
          assert.ok(snapshot.text.includes('blue is the upper airfoil surface; coral is the lower surface'), 'visible Cp surface legend');
          const R=1+m.epsilon,left=-1-2*m.epsilon,leftMap=left+1/left,scale=m.chord/(2-leftMap);
          const outline=Array.from({length:361},(_,i)=>{const t=2*Math.PI*i/360,x=-m.epsilon+R*Math.cos(t),y=R*Math.sin(t),r2=x*x+y*y;return [(x+x/r2-leftMap)*scale,(y-y/r2)*scale];});
          series('airfoil-outline',outline);
          series('upper-Cp',m.surface.filter(p=>p.theta<Math.PI).map(p=>[p.x/m.chord,p.Cp]));
          series('lower-Cp',m.surface.filter(p=>p.theta>Math.PI).map(p=>[p.x/m.chord,p.Cp]));
          const plot=snapshot.plots[0],d=plot.domain;
          near((d.right-d.left)/(d.x[1]-d.x[0]),(d.bottom-d.top)/(d.y[1]-d.y[0]),'airfoil equal axes');
          for(const arrow of plot.geometry) {
            const a=arrow.attrs,theta=Number(a['data-source-theta']),p=m.surface.find(p=>p.theta===theta);assert.ok(p);
            const from=decode(Number(a.x1),Number(a.y1),d),to=decode(Number(a.x2),Number(a.y2),d),gain=Number(a['data-pressure-gain']);
            near(from[0],p.x,'pressure arrow origin x');near(from[1],p.y,'pressure arrow origin y');
            near(to[0]-from[0],-p.Cp*m.dynamicPressure*p.nx*gain,'traction vector x');near(to[1]-from[1],-p.Cp*m.dynamicPressure*p.ny*gain,'traction vector y');
          }
          checked.push({pressureArrows:plot.geometry.length});
        }
        if(station==='plume') {
          const ratios=Array.from({length:101},(_,i)=>16**(i/100));
          series('plume-u',ratios.map(r=>[r,r**(-1/3)]));series('plume-b',ratios.map(r=>[r,r]));series('plume-re',ratios.map(r=>[r,r**(2/3)]));
        }
        proof.cases.push({name,width,station,edits,checked,horizontalOverflow:false,controlValues:snapshot.controlValues});
        if(write&&name==='baseline') {const file=`independent-${width}-${station}.png`;await page.locator(`[data-fluids-panel="${station}"]`).screenshot({path:path.join(output,file)});proof.screenshots.push({file,sha256:hash(fs.readFileSync(path.join(output,file)))});}
      }
      for(const station of ['continuity','hydrostatics','pistons','hull','pipe','boundary','settling','lift','plume']) await state('baseline',station);
      await state('exact-quiz','continuity',{flow:.0008});
      await state('zero-flow','continuity',{flow:0});
      await state('vapor-limit-violated','continuity',{flow:.001,rho:1500,ambientPressure:50000,inletGauge:0});
      await page.locator('[data-fluids-preset="continuity-800"]').click();
      assert.deepEqual(await page.evaluate(()=>{const root=document.querySelector('[data-fluids-lab]'),m=root.fluids.getModels().continuity;return [root.querySelector('[data-fluids-control="continuity.flow"]').valueAsNumber,m.inletSpeed,m.throatSpeed,m.pressureDrop];}),[.0008,2,8,30000]);
      await state('retained-water-upper-bound','hull',{retainedWaterMass:1000});
      const retained=page.locator('[data-fluids-control="hull.retainedWaterMass"]');
      await retained.fill('1001');await retained.dispatchEvent('change');
      const rejected=await page.evaluate(()=>{const root=document.querySelector('[data-fluids-lab]'),panel=root.querySelector('[data-fluids-panel="hull"]');return {error:panel.getAttribute('data-error'),plots:panel.querySelectorAll('svg').length,model:root.fluids.getModels().hull};});
      assert.ok(rejected.error.includes('whole-box capacity upper bound'));assert.equal(rejected.plots,0);assert.equal(rejected.model.error,rejected.error);
      proof.cases.push({name:'retained-water-impossible-volume-rejected',width,station:'hull',checked:[{invalidModelCleared:true,error:rejected.error}],horizontalOverflow:false});
      for(const [name,station,edits] of [['negative-height','hydrostatics',{topPressure:150000}],['vacuum-bound','hydrostatics',{topPressure:0}],['pressure-lowered','hydrostatics',{ambientPressure:80000}],['inverse-area-ratio','pistons',{areaIn:.004,areaOut:.002,strokeIn:.1}],['overloaded','hull',{retainedWaterMass:600}],['neutral','hull',{cargoMass:800}],['reverse','pipe',{pressureDrop:-2}],['zero','pipe',{pressureDrop:0}],['radius-doubled','pipe',{radius:.01}],['viscosity20','pipe',{mu:.02}],['downstream4','boundary',{x:2}],['probe-wall','boundary',{probeEta:0}],['rise','settling',{particleDensity:700}],['neutral','settling',{particleDensity:1000}],['viscosity20','settling',{mu:.02}],['negative-lift','lift',{alphaDegrees:-5}],['zero-lift','lift',{alphaDegrees:0}],['thin-limit','lift',{epsilon:.05,alphaDegrees:10}],['reference','plume',{height:1}],['height16','plume',{height:16}]]) await state(name,station,edits);
      await page.locator('[data-fluids-action="enlarge"]').click();
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
      await page.locator('[data-fluids-action="reset"]').click();
      assert.deepEqual(await page.evaluate(()=>document.querySelector('[data-fluids-lab]').fluids.getState()),JSON.parse(JSON.stringify(api.defaults)));
      await page.close();
    }
    assert.deepEqual(proof.errors,[]);assert.ok(bytes.equals(fs.readFileSync(source)),'source changed during browser verification');proof.allPassed=true;
    if(write)fs.writeFileSync(path.join(output,'renderer-review.json'),JSON.stringify(proof,null,2)+'\n');
    process.stdout.write(JSON.stringify({sourceSHA256:proof.sourceSHA256,allPassed:true,cases:proof.cases.length,plots:proof.cases.flatMap(c=>c.checked).length,pageErrors:proof.errors.length,writeProof:write})+'\n');
  } finally {await browser.close();}
}
if(process.argv.includes('--browser'))renderer().catch(error=>{console.error(error);process.exitCode=1;});else numerical();
