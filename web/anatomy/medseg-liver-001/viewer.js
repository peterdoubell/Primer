import {FetchPool,fingerprint,nativeReader,planes,verifiedBytes} from '../segthy-001/native-volume.mjs';
import {meshView} from '../segthy-001/mesh-view.mjs';
const MANIFEST_SHA256 = 'acd937199d16170d8aaf707e744212774a2d5131003590ee8083c055a32273a8';
const $=id=>document.getElementById(id),axisNames=['I','J','K'];
const exams={
 'ct.liver-mass':['Liver mass CT study','/app/#/radiology/ct.liver-mass'],
 'ct.liver-lirads':['LI-RADS CT study','/app/#/radiology/ct.liver-lirads'],
 'ct.liver-lirads-calculated':['Calculated LI-RADS CT study','/app/#/radiology/ct.liver-lirads-calculated'],
 'ct.chest-abdomen-pelvis':['CT chest, abdomen and pelvis study','/app/#/radiology/ct.chest-abdomen-pelvis']
};
const read=(row,signal)=>verifiedBytes(row,signal,import.meta.url),canvas=$('ct-image'),ctx=canvas.getContext('2d');
const mesh=meshView($('mesh-canvas'),$('mesh-locator'),$('mesh-status'),{yaw:$('yaw'),pitch:$('pitch'),zoom:$('zoom'),yawValue:$('yaw-value'),pitchValue:$('pitch-value'),reset:$('reset-orbit'),retry:$('retry-mesh')},read);
const indices=['i','j','k'].map($),format=(n,d=2)=>n.toLocaleString('en-US',{maximumFractionDigits:d});
let record,reader,label,position,frame,crop,byCode,bySegment,exam='ct.liver-mass',controller,ticket=0;
function links(){
 const query=new URLSearchParams({segment:label.segment,plane:$('plane').value,display:$('display').value,focus:'label',exam});
 $('permalink').href='index.html?'+query.toString()+location.hash;
 $('assembly').href='/app/radiology/liver-segment-assembly/index.html?'+new URLSearchParams({segment:label.segment,exam}).toString();
}
function controls(){
 const axes=planes[$('plane').value];
 $('slice').max=record.shape[axes.normal]-1;$('slice').value=position[axes.normal];
 $('slice-value').textContent=axisNames[axes.normal]+' '+position[axes.normal]+' / '+(record.shape[axes.normal]-1);
 indices.forEach((input,i)=>{input.min=0;input.max=record.shape[i]-1;input.value=position[i];});
 mesh.locator({axes,position:[...position],spacing:record.spacingMm});
 if(label)links();
}
function choose(next,focus){
 label=next;if(next)$('setup').textContent='';$('segment').value=next?.segment??'';$('focus').disabled=!next;$('permalink').hidden=!next;$('assembly').hidden=!next;
 $('evidence').textContent=next?`Original code ${next.code} · ${next.sourceName} · ${format(next.voxelCount,0)} source cells · ${format(next.voxelCount*record.spacingMm.reduce((a,b)=>a*b)/1000,3)} mL in this source mask.`:'No source segment selected. Choose one of the nine published labels.';
 $('surface-title').textContent=next?next.name+' · matching source mask in 3D':'Matching source mask in 3D';
 mesh.load(record,next||{voxelCount:0});if(next&&focus)position=[...next.focus];controls();return loadSection();
}
function bounds(){
 if($('field').value==='full'||!label)return{x:0,y:0,width:frame.width,height:frame.height};
 const {horizontal:h,vertical:v}=frame.axes,[low,high]=label.boundsIndex;
 const mh=Math.ceil(12/record.spacingMm[h]),mv=Math.ceil(12/record.spacingMm[v]);
 const x=Math.max(0,low[h]-mh),y=Math.max(0,frame.height-1-high[v]-mv);
 return{x,y,width:Math.min(frame.width,high[h]+mh+1)-x,height:Math.min(frame.height,frame.height-low[v]+mv)-y};
}
function describe(){
 if(!frame||!crop)return;
 const{horizontal:h,vertical:v}=frame.axes,sx=position[h],sy=frame.height-1-position[v],i=sx+sy*frame.width;
 const row=byCode.get(frame.labels[i]),world=record.affine.slice(0,3).map(r=>r[3]+position.reduce((sum,p,k)=>sum+p*r[k],0));
 $('voxel').textContent=`I, J, K = ${position.join(', ')} · stored CT ${frame.image[i]} · original label ${frame.labels[i]}${row?': '+row.name:' (background)'}. Header RAS (mm): ${world.map(v=>format(v,3)).join(', ')}.`;
 const overlay=$('crosshair');overlay.replaceChildren();overlay.setAttribute('viewBox',`0 0 ${crop.width} ${crop.height}`);
 const local=sx-crop.x,x=($('orientation').value==='radiology'?crop.width-1-local:local)+.5,y=sy-crop.y+.5;
 if(x>=0&&x<crop.width&&y>=0&&y<crop.height){const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',`M${x-5} ${y}h3 m4 0h3 M${x} ${y-5}v3 m0 4v3`);path.setAttribute('stroke','#ffe08f');path.setAttribute('fill','none');path.setAttribute('stroke-width','1');overlay.append(path);}
}
function render(){
 if(!frame)return;
 const low=$('low').valueAsNumber,high=$('high').valueAsNumber,display=$('display').value;
 if(display!=='map'&&!(Number.isFinite(low)&&Number.isFinite(high)&&high>low)){crop=null;$('image-frame').hidden=true;$('voxel').textContent='';$('section-status').textContent='Set a finite white point above the black point.';return;}
 crop=bounds();canvas.width=crop.width;canvas.height=crop.height;
 const raster=ctx.createImageData(crop.width,crop.height),counts=new Map(),w=frame.width;
 for(let y=0;y<crop.height;y++)for(let x=0;x<crop.width;x++){
  const sx=crop.x+($('orientation').value==='radiology'?crop.width-1-x:x),sy=crop.y+y,i=sx+sy*w,dst=4*(x+y*crop.width),code=frame.labels[i];
  if(code)counts.set(code,(counts.get(code)||0)+1);
  let colour=null;
  if(display==='map')colour=code?byCode.get(code).color:[13,20,27];
  else if(display==='outline'&&label&&code===label.code&&(sx===0||sy===0||sx===w-1||sy===frame.height-1||frame.labels[i-1]!==code||frame.labels[i+1]!==code||frame.labels[i-w]!==code||frame.labels[i+w]!==code))colour=label.color;
  if(colour)raster.data.set(colour,dst);else raster.data[dst]=raster.data[dst+1]=raster.data[dst+2]=255*(frame.image[i]-low)/(high-low);
  raster.data[dst+3]=255;
 }
 ctx.putImageData(raster,0,0);$('image-frame').style.aspectRatio=`${crop.width*frame.spacing[0]} / ${crop.height*frame.spacing[1]}`;
 const letters=$('orientation').value==='radiology'?{ij:['A','R','P','L'],ik:['S','R','I','L'],jk:['S','A','I','P']}[$('plane').value]:['+'+axisNames[frame.axes.vertical],'−'+axisNames[frame.axes.horizontal],'−'+axisNames[frame.axes.vertical],'+'+axisNames[frame.axes.horizontal]];
 ['top-edge','left-edge','bottom-edge','right-edge'].forEach((id,i)=>{$(id).textContent=letters[i];});$('image-frame').hidden=false;
 $('section-status').textContent=`${crop.width} × ${crop.height} native cells in view · ${label?format((counts.get(label.code)||0)*frame.spacing[0]*frame.spacing[1])+' mm² of '+label.name.toLowerCase()+' in view':'no source segment selected'}. Source samples verified.`;
 const rows=[];
 for(const[code,n]of[...counts].sort((a,b)=>b[1]-a[1])){const part=byCode.get(code),row=document.createElement('tr'),th=document.createElement('th'),td=document.createElement('td'),button=document.createElement('button'),swatch=document.createElement('span');th.scope='row';button.type='button';swatch.className='swatch';swatch.style.backgroundColor='rgb('+part.color.join(',')+')';button.append(swatch,document.createTextNode(part.name));button.addEventListener('click',()=>choose(part,false));th.append(button);td.textContent=format(n*frame.spacing[0]*frame.spacing[1]);row.append(th,td);rows.push(row);}
 $('key').replaceChildren(...rows);describe();if(label)links();
}
async function loadSection(){
 if(!reader)return;controller?.abort();controller=new AbortController();const generation=++ticket,{signal}=controller;$('retry').hidden=true;
 if(frame&&frame.axes===planes[$('plane').value]&&frame.fixed===position[frame.axes.normal]){render();return;}
 frame=null;crop=null;$('image-frame').hidden=true;$('key').replaceChildren();$('voxel').textContent='';$('section-status').textContent='Verifying the original CT section…';
 try{const next=await reader.section($('plane').value,position,signal);if(generation!==ticket||signal.aborted)return;frame=next;render();}catch{if(generation!==ticket||signal.aborted)return;$('retry').hidden=false;$('section-status').textContent='The source section could not be verified. Retry the section.';}
}
function go(next){position=next;controls();loadSection();}
$('segment').addEventListener('change',()=>choose(bySegment.get($('segment').value),true));
$('focus').addEventListener('click',()=>{if(label)go([...label.focus]);});
$('plane').addEventListener('change',()=>go([...position]));
$('slice').addEventListener('input',()=>{const next=[...position];next[planes[$('plane').value].normal]=$('slice').valueAsNumber;go(next);});
$('go').addEventListener('click',()=>{const next=indices.map(i=>i.valueAsNumber);if(!next.every((n,k)=>Number.isInteger(n)&&n>=0&&n<record.shape[k])){$('voxel').textContent='Enter an integer source index within every displayed range.';return;}go(next);});
for(const id of['display','orientation','field'])$(id).addEventListener('change',render);
for(const id of['low','high'])$(id).addEventListener('input',render);
$('retry').addEventListener('click',loadSection);
canvas.addEventListener('click',event=>{if(!frame||!crop)return;const box=canvas.getBoundingClientRect(),x=Math.min(crop.width-1,Math.max(0,Math.floor((event.clientX-box.left)*crop.width/box.width))),y=Math.min(crop.height-1,Math.max(0,Math.floor((event.clientY-box.top)*crop.height/box.height)));position[frame.axes.horizontal]=crop.x+($('orientation').value==='radiology'?crop.width-1-x:x);position[frame.axes.vertical]=frame.height-1-crop.y-y;controls();describe();});
canvas.addEventListener('keydown',event=>{if(!frame||!['ArrowLeft','ArrowRight'].includes(event.key))return;event.preventDefault();const next=[...position],normal=frame.axes.normal;next[normal]=Math.min(record.shape[normal]-1,Math.max(0,next[normal]+(event.key==='ArrowRight'?1:-1)));go(next);});
async function start(){
 const response=await fetch('manifest.json');if(!response.ok)throw Error('Missing source inventory');const bytes=await response.arrayBuffer();if(await fingerprint(bytes)!==MANIFEST_SHA256)throw Error('The source inventory differs');record=JSON.parse(new TextDecoder().decode(bytes));
 reader=nativeReader(record,new FetchPool(3),read,36*1024*1024);byCode=new Map(record.labels.map(l=>[l.code,l]));bySegment=new Map(record.labels.map(l=>[l.segment,l]));
 const query=new URLSearchParams(location.search),keys=['segment','plane','display','focus','exam'],duplicate=keys.some(k=>query.getAll(k).length>1),requested=(query.get('segment')??'4a').toLowerCase(),requestedPlane=query.get('plane')??'ij',requestedDisplay=query.get('display')??'outline',requestedExam=query.get('exam')??'ct.liver-mass';
 const valid=!duplicate&&bySegment.has(requested)&&Object.hasOwn(planes,requestedPlane)&&['outline','raw','map'].includes(requestedDisplay)&&(!query.has('focus')||query.get('focus')==='label')&&Object.hasOwn(exams,requestedExam);
 if(Object.hasOwn(exams,requestedExam))exam=requestedExam;const destination=exams[exam];$('return').href=destination[1];$('return').textContent='← '+destination[0];
 $('plane').value=Object.hasOwn(planes,requestedPlane)?requestedPlane:'ij';$('display').value=['outline','raw','map'].includes(requestedDisplay)?requestedDisplay:'outline';
 $('segment').replaceChildren(...record.labels.map(l=>new Option(l.name+' · original code '+l.code,l.segment)));
 $('case-meta').textContent=`Original grid ${record.shape.join(' × ')}; native sampling ${record.spacingMm.map(n=>format(n,6)).join(' × ')} mm. Both coded qform and sform agree and declare increasing I/J/K toward right/anterior/superior. Radiological mode puts source right on the left for axial/coronal views and source anterior on the left for sagittal views. Header coordinates are not registration to the current patient.`;
 position=record.shape.map(n=>Math.floor(n/2));$('selection').disabled=false;$('workspace').inert=false;$('setup').textContent=valid?'':'This link does not identify one published source segment and view. Choose a source label; segment IV is offered only as 4A and 4B separately.';await choose(valid?bySegment.get(requested):null,true);if(['#ct','#map','#surface'].includes(location.hash))requestAnimationFrame(()=>document.querySelector(location.hash)?.scrollIntoView({block:'start'}));
}
start().catch(()=>{$('setup').textContent='The source case inventory could not be verified. Reload to retry.';});
