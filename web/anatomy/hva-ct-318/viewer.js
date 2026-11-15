'use strict';
const get=id=>document.getElementById(id);
let volume,generation=0,current;
const cache=new Map();
const from = new URLSearchParams(location.search).get('from');
const referenceNames = {'ra.liver-masses':'liver mass reporting', 'ra.liver-lirads':'LI-RADS reporting'};
if (Object.hasOwn(referenceNames, from)) {
  get('return-context').href = '/app/#/radiology/' + from;
  get('return-context').textContent = 'Return to ' + referenceNames[from];
  get('return-context').hidden = false;
}
async function digest(bytes){
 return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(value=>value.toString(16).padStart(2,'0')).join('');
}
async function metadata(name){
 const response=await fetch(name+'.json');
 if(!response.ok)throw Error('Missing metadata');
 const bytes=await response.arrayBuffer();
 if(await digest(bytes)!==document.querySelector('main').dataset[name+'Sha256'])throw Error('Metadata differs');
 return JSON.parse(new TextDecoder().decode(bytes));
}
function chunkData(row,kind){
 if(!cache.has(row.file)){
  const task=(async()=>{
   const response=await fetch(row.file);
   if(!response.ok)throw Error('Missing CT or labels');
   const bytes=await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
   if(bytes.byteLength!==row.decodedBytes||await digest(bytes)!==row.sha256)throw Error('Source samples differ');
   if(kind==='labels')return new Uint8Array(bytes);
   const view=new DataView(bytes);
   return Float32Array.from({length:bytes.byteLength/4},(_,i)=>view.getFloat32(4*i,true));
  })();
  cache.set(row.file,task);
  task.catch(()=>{if(cache.get(row.file)===task)cache.delete(row.file);});
  while(cache.size>4)cache.delete(cache.keys().next().value);
 }
 return cache.get(row.file);
}
function resize(){
 const image=get('ct');
 if(!image.hidden)image.style.width=get('zoom').value==='fit'?'100%':image.width*Number(get('zoom').value)+'px';
}
async function draw(){
 const attempt=++generation,canvas=get('ct');
 current=null;canvas.hidden=true;get('sample').textContent='';get('retry').hidden=true;
 const slice=get('slice').valueAsNumber,region=Number(get('region').value);
 const black=get('black').valueAsNumber,white=get('white').valueAsNumber;
 get('section').textContent=(slice+1)+' / '+volume.shape[2];
 if(!Number.isFinite(black)||!Number.isFinite(white)||white<=black){get('status').textContent='Use finite display values with white greater than black.';return;}
 get('status').textContent='Loading verified source section…';
 try{
  const chunk=volume.chunks.find(row=>slice>=row.firstSlice&&slice<row.firstSlice+row.slices);
  const [stored,labels]=await Promise.all([chunkData(chunk.ct,'mri'),chunkData(chunk.labels,'labels')]);
  if(attempt!==generation)return;
  const [width,height]=volume.shape,offset=(slice-chunk.firstSlice)*width*height;
  const index=(x,y)=>offset+width-1-x+width*(height-1-y);
  const labelAt=(x,y)=>x<0||y<0||x>=width||y>=height?0:labels[index(x,y)];
  const valueAt=(x,y)=>stored[index(x,y)]*volume.sourceScaling.slope+volume.sourceScaling.intercept;
  const context=canvas.getContext('2d'),pixels=context.createImageData(width,height),overlay=get('overlay').checked;
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
   const label=labelAt(x,y),gray=255*(valueAt(x,y)-black)/(white-black);
   const boundary=overlay&&label&&(region===0||label===region)&&[[x-1,y],[x+1,y],[x,y-1],[x,y+1]].some(([i,j])=>labelAt(i,j)!==label);
   pixels.data.set(boundary?[...volume.colors[label-1],255]:[gray,gray,gray,255],4*(x+width*y));
  }
  context.putImageData(pixels,0,0);
  current={slice,index,labelAt,valueAt};
  canvas.hidden=false;resize();
  get('status').textContent='Verified source section '+(slice+1)+'.';
 }catch{if(attempt===generation){get('status').textContent='Source samples could not be verified.';get('retry').hidden=false;}}
}
function regionChanged(){
 const selected=Number(get('region').value);
 const layers=[...document.querySelectorAll('.layer')];
 layers.forEach((input,i)=>{input.checked=selected===0||selected===i+1;});
 layers[0].dispatchEvent(new Event('input'));
 if(volume)draw();
}
async function start(){
 get('retry').hidden=true;
 try{
  volume=await metadata('volume');
  get('slice').value=volume.initialSlice;
  get('slice').max=volume.shape[2]-1;get('slice').disabled=false;regionChanged();
 }catch{volume=null;get('status').textContent='Source metadata could not be verified.';get('retry').hidden=false;}
}
get('region').addEventListener('change',regionChanged);
for(const id of ['slice','black','white','overlay'])get(id).addEventListener('input',()=>{if(volume)draw();});
get('zoom').addEventListener('change',resize);
get('retry').addEventListener('click',()=>volume?draw():start());
get('ct').addEventListener('keydown',event=>{
 if(!current||!['ArrowLeft','ArrowRight'].includes(event.key))return;
 event.preventDefault();if(event.key==='ArrowLeft')get('slice').stepDown();else get('slice').stepUp();draw();
});
get('ct').addEventListener('click',event=>{
 if(!current)return;
 const box=event.currentTarget.getBoundingClientRect(),[width,height]=volume.shape;
 const x=Math.min(width-1,Math.max(0,Math.floor((event.clientX-box.left)*width/box.width)));
 const y=Math.min(height-1,Math.max(0,Math.floor((event.clientY-box.top)*height/box.height)));
 const point=[width-1-x,height-1-y,current.slice];
 const world=volume.sourceAffine.slice(0,3).map(row=>row[3]+point.reduce((sum,value,i)=>sum+value*row[i],0));
 get('sample').textContent='Source voxel '+point.join(', ')+' · scaled intensity '+current.valueAt(x,y)+' · label '+current.labelAt(x,y)+' · RAS '+world.map(value=>value.toFixed(2)).join(', ')+' mm.';
});
start();
