'use strict';
const $=id=>document.getElementById(id);
let manifest,selected,media;
function link(text,url){const a=document.createElement('a');a.textContent=text;a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}
function show(asset){
 if(media?.tagName==='VIDEO'){media.pause();media.removeAttribute('src');media.load();}
 selected=asset;$('title').textContent=asset.title;$('viewport').replaceChildren();
 media=document.createElement(asset.kind==='video'?'video':'img');media.src=asset.path;
 if(asset.kind==='video'){media.controls=true;media.preload='metadata';media.playsInline=true;media.setAttribute('aria-label',asset.title);}else{media.alt=asset.title;media.style.width='100%';}
 media.addEventListener('error',()=>{$('status').textContent='Media unavailable. Run the documented local preparation command; source evidence remains in the manifest.';});
 $('viewport').append(media);$('cine').hidden=asset.kind!=='video';
 for(const id of ['fit','native','zoom'])$(id).disabled=asset.kind==='video';
 if(asset.kind==='video'){$('frame').max=asset.frames-1;$('frame').value=0;$('time').textContent=`${asset.frames} exported frames; acquisition timing unverified.`;}
 const source=manifest.sources[asset.source];
 $('limits').textContent=asset.limits;$('changes').textContent=asset.changes;
 $('credit').replaceChildren(document.createTextNode(`${source.authors.join(', ')}. `),link(source.title,source.url),document.createTextNode(' · '),link(source.license,source.license_url));
 $('provenance').textContent=JSON.stringify({source:asset.source,pmc_version:source.pmc_version,sha256:asset.sha256,bytes:asset.bytes,dimensions:asset.dimensions,review_status:asset.review_status},null,2);
 for(const b of $('list').children)b.setAttribute('aria-current',String(b.dataset.id===asset.id));
 $('status').textContent=`${asset.kind==='video'?'Cine':'Image'} selected: ${asset.title}. Review candidate.`;
}
function filter(){const step=$('step').value,assets=manifest.assets.filter(a=>step==='all'||a.steps.includes(Number(step)));$('list').replaceChildren();for(const a of assets){const b=document.createElement('button');b.textContent=a.title;b.dataset.id=a.id;b.onclick=()=>show(a);$('list').append(b);}show(assets[0]);}
$('step').onchange=filter;$('fit').onclick=()=>{media.style.width='100%';};$('native').onclick=()=>{media.style.width=selected.dimensions[0]+'px';$('zoom').value=100;};$('zoom').oninput=()=>{media.style.width=(selected.dimensions[0]*Number($('zoom').value)/100)+'px';};
$('frame').oninput=()=>{const i=Number($('frame').value),time=selected.presentation_times[i];media.pause();media.currentTime=time;$('time').textContent=`Requested frame ${i+1}/${selected.frames} at exported time ${time.toFixed(6)} s. Browser seek is approximate.`;};
fetch('manifest.json').then(r=>{if(!r.ok)throw Error('Manifest load failed');return r.json();}).then(m=>{manifest=m;for(const gap of m.open_gaps){const li=document.createElement('li');li.textContent=gap;$('gaps').append(li);}filter();}).catch(e=>{$('status').textContent=e.message;});
