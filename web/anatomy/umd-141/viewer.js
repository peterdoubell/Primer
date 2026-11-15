'use strict';
async function loadMRI(){
  const get=id=>document.getElementById(id);
  const [full,crop]=await Promise.all(['full-mri.json','grid.json'].map(async file=>{
    const response=await fetch(file);
    if(!response.ok)throw Error('Source manifest unavailable');
    return response.json();
  }));
  const pending=new Map();
  async function decode(file,expected,Type){
    const response=await fetch(file);
    if(!response.ok)throw Error('Source samples unavailable');
    const bytes=await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
    if(hash!==expected)throw Error('Source checksum differs');
    return new Type(bytes);
  }
  const mask=await decode('mask.gz',crop.decodedSHA256.mask,Uint8Array);
  if(mask.length!==crop.shape.reduce((a,b)=>a*b,1))throw Error('Source label extent differs');
  const canvas=get('mri'),ctx=canvas.getContext('2d'),slider=get('slice'),status=get('status');
  const [width,height,depth]=full.shape;
  canvas.width=width;canvas.height=height;
  slider.min=0;slider.max=depth-1;slider.step=1;slider.value=11;slider.disabled=false;
  const colors=[[0,0,0],[255,199,61],[77,171,245],[242,82,87],[178,121,241]];
  let generation=0,current=null;
  function labelAt(x,y,k){
    const [i,j,z]=[x-crop.origin[0],y-crop.origin[1],k-crop.origin[2]];
    if(i<0||j<0||z<0||i>=crop.shape[0]||j>=crop.shape[1]||z>=crop.shape[2])return 0;
    return mask[i+crop.shape[0]*(j+crop.shape[1]*z)];
  }
  function samples(chunk){
    if(!pending.has(chunk.file)){
      const task=decode(chunk.file,chunk.sha256,Int16Array).then(data=>{
        if(data.length*2!==chunk.decodedBytes)throw Error('Source MRI extent differs');
        return data;
      }).catch(error=>{pending.delete(chunk.file);throw error;});
      pending.set(chunk.file,task);
    }
    return pending.get(chunk.file);
  }
  async function draw(){
    const attempt=++generation,k=slider.valueAsNumber;
    canvas.hidden=true;current=null;get('sample').textContent='';get('plane').textContent=k;
    const black=get('black').valueAsNumber,white=get('white').valueAsNumber;
    if(!get('black').validity.valid||!get('white').validity.valid||!Number.isFinite(black)||!Number.isFinite(white)||white<=black){
      status.textContent='Use valid display values, with white greater than black.';return;
    }
    status.textContent='Loading acquired source section…';
    try{
      const chunk=full.chunks.find(c=>k>=c.firstPlane&&k<c.firstPlane+c.planes);
      const data=await samples(chunk);
      if(attempt!==generation)return;
      const startX=get('focus').checked?crop.origin[0]:0,startY=get('focus').checked?crop.origin[1]:0;
      const viewWidth=get('focus').checked?crop.shape[0]:width,viewHeight=get('focus').checked?crop.shape[1]:height;
      canvas.width=viewWidth;canvas.height=viewHeight;
      const image=ctx.createImageData(viewWidth,viewHeight),offset=(k-chunk.firstPlane)*width*height;
      for(let row=0;row<viewHeight;row++)for(let column=0;column<viewWidth;column++){
        const x=startX+column,y=startY+row;
        const value=data[offset+x+width*y],gray=255*(value-black)/(white-black);
        const label=labelAt(x,y,k);
        const boundary=get('overlay').checked&&label&&[[x-1,y],[x+1,y],[x,y-1],[x,y+1]].some(([i,j])=>labelAt(i,j,k)!==label);
        const pixel=4*(column+viewWidth*row);
        for(let c=0;c<3;c++)image.data[pixel+c]=boundary?colors[label][c]:gray;
        image.data[pixel+3]=255;
      }
      ctx.putImageData(image,0,0);current={data,offset,k,startX,startY};canvas.hidden=false;
      status.textContent='Acquired source section '+k+' · 5 mm thickness · original source samples.';
    }catch(error){
      if(attempt===generation)status.textContent='Source loading failed. Change the section to retry.';
    }
  }
  canvas.onclick=event=>{
    if(!current)return;
    const r=canvas.getBoundingClientRect();
    const x=current.startX+Math.min(canvas.width-1,Math.max(0,Math.floor((event.clientX-r.left)*canvas.width/r.width)));
    const y=current.startY+Math.min(canvas.height-1,Math.max(0,Math.floor((event.clientY-r.top)*canvas.height/r.height)));
    get('sample').textContent='Source pixel ('+[x,y,current.k].join(', ')+') · value '+current.data[current.offset+x+width*y]+' · '+crop.labels[labelAt(x,y,current.k)];
  };
  canvas.onkeydown=event=>{
    if(!['ArrowLeft','ArrowRight'].includes(event.key))return;
    event.preventDefault();slider.value=Math.min(depth-1,Math.max(0,slider.valueAsNumber+(event.key==='ArrowRight'?1:-1)));draw();
  };
  for(const id of ['slice','overlay','black','white','focus'])get(id).addEventListener('input',draw);
  draw();
}
loadMRI().catch(()=>{document.getElementById('status').textContent='The source MRI could not be initialized. Reload to retry.';});
