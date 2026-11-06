'use strict';
const get=id=>document.getElementById(id);
let volume,rows,position,generation=0,current=null;
const requestedSegment = new URLSearchParams(location.search).get('segment');
const initialIndex = [...get('segment').options].findIndex(option => option.dataset.source === requestedSegment);
if (initialIndex >= 0) {
  get('segment').value = initialIndex;
  document.querySelectorAll('.layer').forEach((input,index) => {input.checked = index === initialIndex;});
}
const cache=new Map();
const returnTargets = {
  'ra.solid-renal-masses':['radiology','Renal mass reporting reference'],
  'rad.4.kidney':['node','Kidney lesson'],
  'ra.ct-pancreatic-cancer':['radiology','Pancreatic cancer reporting reference'],
  'rad.5.pancreas-tumour':['node','Pancreatic tumour lesson'],
  'ra.ct-abdominal-trauma':['radiology','Abdominal trauma reference'],
  'ra.ct-bowel-ischaemia':['radiology','Bowel ischaemia reference'],
};
const from = new URLSearchParams(location.search).get('from');
if (Object.hasOwn(returnTargets, from)) {
  const [route,label] = returnTargets[from];
  get('return-context').href = '/app/#/' + route + '/' + from;
  get('return-context').textContent = 'Return to ' + label;
  get('return-context').hidden = false;
}
async function decode(row,Type){
  if(!cache.has(row.file)){
    const task=(async()=>{
      const response=await fetch(row.file);
      if(!response.ok)throw Error('Missing source chunk');
      const raw=await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
      const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(v=>v.toString(16).padStart(2,'0')).join('');
      if(raw.byteLength!==row.decodedBytes||hash!==row.decodedSHA256)throw Error('Source chunk differs');
      if(Type===Uint8Array)return new Uint8Array(raw);
      const view=new DataView(raw);
      return Int16Array.from({length:raw.byteLength/2},(_,i)=>view.getInt16(i*2,true));
    })();
    cache.set(row.file,task);
    task.catch(()=>{if(cache.get(row.file)===task)cache.delete(row.file);});
    while(cache.size>4)cache.delete(cache.keys().next().value);
  }
  return cache.get(row.file);
}
async function draw(){
  const token=++generation,canvas=get('ct'),slice=get('slice').valueAsNumber;
  current=null;canvas.hidden=true;get('sample').textContent='';get('retry').hidden=true;
  const black=get('black').valueAsNumber,white=get('white').valueAsNumber;
  if(!Number.isFinite(black)||!Number.isFinite(white)||white<=black){get('status').textContent='Use finite display values with white greater than black.';return;}
  const segment=rows[Number(get('segment').value)].sourceSegment;
  get('section').textContent=(slice+1)+' / '+volume.shape[2];
  get('identity').textContent=segment.name+' · source layer '+segment.layer+', value '+segment.value;
  get('status').textContent='Loading verified CT and labels…';
  try{
    const chunk=volume.chunks.find(row=>slice>=row.firstSlice&&slice<row.firstSlice+row.slices);
    const [ct,labels]=await Promise.all([decode(chunk.ct,Int16Array),decode(chunk.labels,Uint8Array)]);
    if(token!==generation)return;
    const [width,height]=volume.shape,layers=volume.labelLayers,offset=(slice-chunk.firstSlice)*width*height;
    const flipX=volume.sourceAffineLPS[0][0]<0,flipY=volume.sourceAffineLPS[1][1]<0;
    const index=(x,y)=>offset+(flipX?width-1-x:x)+width*(flipY?height-1-y:y);
    const inside=(x,y)=>x>=0&&y>=0&&x<width&&y<height&&labels[layers*index(x,y)+segment.layer]===segment.value;
    canvas.width=width;canvas.height=height;
    const context=canvas.getContext('2d'),image=context.createImageData(width,height),overlay=get('overlay').checked;
    for(let y=0;y<height;y++)for(let x=0;x<width;x++){
      const gray=255*(ct[index(x,y)]-black)/(white-black);
      const edge=overlay&&inside(x,y)&&[[x-1,y],[x+1,y],[x,y-1],[x,y+1]].some(([i,j])=>!inside(i,j));
      image.data.set(edge?[242,191,80,255]:[gray,gray,gray,255],4*(x+width*y));
    }
    context.putImageData(image,0,0);
    canvas.style.aspectRatio=Math.abs(width*volume.sourceAffineLPS[0][0]/(height*volume.sourceAffineLPS[1][1]));
    current={ct,index,inside,slice,flipX,flipY};canvas.hidden=false;
    get('status').textContent='Verified source section '+(slice+1)+'.';
  }catch{if(token===generation){get('status').textContent='CT or labels could not be verified.';get('retry').hidden=false;}}
}
function selectSegment(){
  const selected=Number(get('segment').value),segment=rows[selected].sourceSegment;
  const layers=[...document.querySelectorAll('.layer')];
  layers.forEach((input,i)=>{input.checked=i===selected;});
  layers[selected].dispatchEvent(new Event('input'));
  get('slice').value=Math.round((segment.bounds[0][2]+segment.bounds[1][2])/2);
  draw();
}
async function start(){
  try{
    [volume,rows]=await Promise.all(['volume','surfaces'].map(async name=>{
      const response=await fetch(name+'.json');
      if(!response.ok)throw Error('Missing source metadata');
      const bytes=await response.arrayBuffer();
      const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(value=>value.toString(16).padStart(2,'0')).join('');
      if(digest!==document.querySelector('main').dataset[name+'Sha256'])throw Error('Source metadata differs');
      return JSON.parse(new TextDecoder().decode(bytes));
    }));
    const requested = new URLSearchParams(location.search).get('segment');
    if (requested !== null) {
      const index = rows.findIndex(row => row.sourceSegment.layer + ':' + row.sourceSegment.value === requested);
      if (index >= 0) get('segment').value = index;
      else get('request-note').textContent = 'The requested segment is unavailable in this phase. Showing the default vessel; choose another source label.';
    }
    get('slice').min=0;get('slice').max=volume.shape[2]-1;get('slice').disabled=false;
    selectSegment();
  }catch{volume=undefined;rows=undefined;get('slice').disabled=true;get('status').textContent='Source metadata could not be verified.';get('retry').hidden=false;}
}
for(const id of ['slice','black','white','overlay'])get(id).addEventListener('input',()=>{if(volume)draw();});
get('segment').addEventListener('change',()=>{if(volume){get('request-note').textContent='';selectSegment();}});
get('retry').addEventListener('click',()=>volume?draw():start());
get('ct').addEventListener('keydown',event=>{
  if(!current||!['ArrowLeft','ArrowRight'].includes(event.key))return;
  event.preventDefault();if(event.key==='ArrowLeft')get('slice').stepDown();else get('slice').stepUp();draw();
});
get('ct').addEventListener('click',event=>{
  if(!current)return;
  const box=event.currentTarget.getBoundingClientRect(),[w,h]=volume.shape;
  const x=Math.min(w-1,Math.max(0,Math.floor((event.clientX-box.left)*w/box.width))),y=Math.min(h-1,Math.max(0,Math.floor((event.clientY-box.top)*h/box.height)));
  const voxel=[current.flipX?w-1-x:x,current.flipY?h-1-y:y,current.slice];
  const world=volume.sourceAffineLPS.slice(0,3).map(row=>row[3]+voxel.reduce((sum,v,i)=>sum+v*row[i],0));
  get('sample').textContent='Source voxel '+voxel.join(', ')+' · intensity '+current.ct[current.index(x,y)]+' · selected label '+(current.inside(x,y)?'present':'absent')+' · LPS '+world.map(v=>v.toFixed(2)).join(', ')+' mm.';
});
start();
