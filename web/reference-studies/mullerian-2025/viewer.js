'use strict';
const get=id=>document.getElementById(id);
const selection=get('figure'),image=get('image'),status=get('status'),retry=get('retry');
const cache=new Map();
let figures=null;
let generation=0;
function resize(){
  if(image.hidden)return;
  image.style.width=get('zoom').value==='fit'?'100%':Number(get('zoom').value)*image.naturalWidth+'px';
}
async function showFigure(){
  const attempt=++generation;
  selection.disabled=true;image.hidden=true;retry.hidden=true;
  status.textContent='Loading verified source figure…';
  try{
    if(!figures){
      const response=await fetch('figures.json');
      if(!response.ok)throw Error('Missing figure manifest');
      const manifest=await response.json();
      figures=manifest.figures;
      selection.replaceChildren(...figures.map(item=>new Option(item.title,item.id)));
    }
    const item=figures.find(item=>item.id===selection.value);
    if(!cache.has(item.id)){
      const response=await fetch(item.file);
      if(!response.ok)throw Error('Missing image');
      const bytes=await response.arrayBuffer();
      const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
      if(hash!==item.sha256)throw Error('Source figure checksum differs');
      const reader=new FileReader();
      const dataURL=await new Promise((resolve,reject)=>{
        reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(Error('Image decoding failed'));
        reader.readAsDataURL(new Blob([bytes],{type:'image/png'}));
      });
      cache.set(item.id,dataURL);
    }
    if(attempt!==generation)return;
    image.alt=item.title+' · complete published figure including schematics and clinical panels';
    image.src=cache.get(item.id);
    await image.decode();
    if(attempt!==generation)return;
    if(image.naturalWidth!==item.width||image.naturalHeight!==item.height)throw Error('Source image dimensions differ');
    image.hidden=false;resize();
    image.parentElement.scrollTo(0,0);
    get('caption').textContent=item.caption;
    status.textContent='Original Figure '+item.id+' · '+item.width+' × '+item.height+' source pixels.';
  }catch(error){
    if(attempt!==generation)return;
    status.textContent='The source figure could not be loaded. Retry to check the source files again.';
    retry.hidden=false;
  }finally{
    if(attempt===generation)selection.disabled=false;
  }
}
selection.onchange=showFigure;
get('zoom').onchange=resize;
retry.onclick=showFigure;
showFigure();
