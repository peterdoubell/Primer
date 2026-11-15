'use strict';
const get=id=>document.getElementById(id);
const selection=get('figure'),image=get('image'),status=get('status'),retry=get('retry');
const cache=new Map();
const related=get('related-figures');
let figures=null;
let generation=0;
function resize(){
  if(image.hidden)return;
  image.style.width=get('zoom').value==='fit'?'100%':Number(get('zoom').value)*image.naturalWidth+'px';
}
async function showFigure(){
  const attempt=++generation;
  selection.disabled=true;image.hidden=true;retry.hidden=true;
  get('caption').textContent='';
  get('label-key').replaceChildren();
  get('article').hidden=true;
  related.hidden=true;
  related.replaceChildren();
  status.textContent='Loading verified source figure…';
  try{
    if(!figures){
      const response=await fetch('figures.json');
      if(!response.ok)throw Error('Missing figure manifest');
      const raw=await response.arrayBuffer();
      const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),b=>b.toString(16).padStart(2,'0')).join('');
      if(hash!==document.querySelector('main').dataset.figuresSha256)throw Error('Figure inventory differs');
      const manifest=JSON.parse(new TextDecoder().decode(raw));
      figures=manifest.figures;
      selection.replaceChildren(...figures.map(item=>new Option(item.title,item.id)));
      const requested=new URLSearchParams(location.search).get('figure');
      if(figures.some(item=>item.id===requested))selection.value=requested;
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
        reader.readAsDataURL(new Blob([bytes],{type:item.mimeType}));
      });
      cache.set(item.id,dataURL);
    }
    if(attempt!==generation)return;
    image.alt=item.alt;
    image.src=cache.get(item.id);
    await image.decode();
    if(attempt!==generation)return;
    if(image.naturalWidth!==item.width||image.naturalHeight!==item.height)throw Error('Source image dimensions differ');
    image.hidden=false;resize();
    image.parentElement.scrollTo(0,0);
    get('caption').textContent=item.caption;
    const source=get('article');
    source.hidden=false;
    source.href=item.articleUrl;
    source.textContent=item.credit+' · original Figure '+item.figureNumber;
    get('label-key').replaceChildren(...item.labels.map(([mark,structure])=>{
      const row=document.createElement('tr');
      const label=document.createElement('th');label.scope='row';label.textContent=mark;
      const name=document.createElement('td');name.textContent=structure;
      row.append(label,name);return row;
    }));
    for(const id of item.related || []){
      const comparison=figures.find(figure=>figure.id===id);
      if(!comparison)continue;
      const link=document.createElement('a');
      const query=new URLSearchParams(location.search);
      query.set('figure',id);
      link.href='?'+query.toString();
      link.textContent=comparison.title;
      const line=document.createElement('p');
      line.append(link);
      related.append(line);
    }
    related.hidden=!related.childElementCount;
    status.textContent='Original Figure '+item.figureNumber+' · '+item.width+' × '+item.height+' source pixels.';
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
