'use strict';
const $=id=>document.getElementById(id);
let inventory,current,selected,generation=0;
async function sha(bytes){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');}
function choose(location){
  selected=location;
  const [x,y,w,h]=location.rect;
  for(const [name,value] of Object.entries({x,y,width:w,height:h}))$('box').setAttribute(name,value);
  $('selection').textContent=location.title;
  $('meaning').textContent=location.structure_or_observation+' · '+location.representation+'. Publisher annotation locator; independent anatomical validation remains pending.';
  $('coordinates').textContent=`Original pixel rectangle: x ${x}–${x+w-1}, y ${y}–${y+h-1}. This does not specify a physical measurement or anatomical extent.`;
  $('inset').width=w;$('inset').height=h;
  $('inset').getContext('2d').drawImage($('original'),x,y,w,h,0,0,w,h);
  for(const button of $('locations').children)button.setAttribute('aria-pressed',String(button.dataset.id===location.id));
  $('status').textContent=current.title+' · '+location.title;
  window.SourceLabelReview={current,selected,inventory};
}
async function show(){
  const request=++generation;const row=inventory.images[Number($('figure').value)];window.SourceLabelReview=null;
  $('original').hidden=$('locator').hidden=$('detail').hidden=true;$('locations').replaceChildren();$('status').textContent='Checking original figure bytes…';
  try{
    const response=await fetch(row.file);if(!response.ok)throw Error('Original source unavailable');
    const bytes=await response.arrayBuffer();if(await sha(bytes)!==row.sha256)throw Error('Original figure hash differs');
    const url=URL.createObjectURL(new Blob([bytes],{type:'image/jpeg'}));const image=new Image();image.src=url;
    try{await image.decode();if(image.naturalWidth!==row.dimensions[0]||image.naturalHeight!==row.dimensions[1])throw Error('Original source dimensions differ');if(request!==generation){URL.revokeObjectURL(url);return;}
      const previous=$('original').src;$('original').src=url;$('original').alt=row.title+'; unchanged original publisher panels';await $('original').decode();if(request!==generation){URL.revokeObjectURL(url);return;}current=row;if(previous.startsWith('blob:'))URL.revokeObjectURL(previous);
    }catch(error){URL.revokeObjectURL(url);throw error;}
    $('locator').setAttribute('viewBox','0 0 '+row.dimensions.join(' '));
    for(const location of row.locations){const b=document.createElement('button');b.textContent=location.title;b.dataset.id=location.id;b.onclick=()=>choose(location);$('locations').append(b);}
    $('limits').textContent=row.limits;
    const a=document.createElement('a');a.href=row.source_url;a.textContent=row.source_id+' · source article and figure caption';
    const license=document.createElement('a');license.href=row.source_metadata.license_url;license.textContent=row.source_metadata.license;
    $('credit').replaceChildren(document.createTextNode(row.source_metadata.authors.join(', ')+' · '+row.source_metadata.title+' · '),a,document.createTextNode(' · '),license,document.createTextNode(' · Original figure unmodified; locator interface and pixel inset are additions.'));
    $('original').hidden=$('detail').hidden=false;$('locator').hidden=!$('overlay').checked;choose(row.locations[0]);
  }catch(error){if(request===generation)$('status').textContent=error.message;}
}
$('figure').onchange=show;$('overlay').onchange=()=>{$('locator').hidden=!$('overlay').checked;};
(async()=>{inventory=await (await fetch('manifest.json')).json();for(const [i,row] of inventory.images.entries())$('figure').append(new Option(row.title,i));await show();})().catch(error=>{$('status').textContent=error.message;});
