'use strict';
async function load() {
  const grid = await (await fetch('grid.json')).json();
  const {shape, origin} = grid;
  async function array(name, Type) {
    const response = await fetch(name + '.gz');
    if (!response.ok) throw Error('Missing source array');
    const stream = response.body.pipeThrough(new DecompressionStream('gzip'));
    const bytes = await new Response(stream).arrayBuffer();
    const digest = new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));
    const hex = Array.from(digest,b=>b.toString(16).padStart(2,'0')).join('');
    if (hex !== grid.decodedSHA256[name]) throw Error('Source array checksum differs');
    const data = new Type(bytes);
    if (data.length !== shape[0]*shape[1]*shape[2]) throw Error('Incomplete source array');
    return data;
  }
  const [ct,mask] = await Promise.all([array('ct',Int16Array), array('mask',Uint8Array)]);
  const point = (grid.initialVoxel || [193,161,232]).map((v,i) => v-origin[i]);
  const stride = [1,shape[0],shape[0]*shape[1]];
  const windowControl = document.querySelector('#window');
  const outline = document.querySelector('#outline');
  const views = [];
  function render() {
    const width = Number(windowControl.value), centre = width === 400 ? 50 : 70;
    for (const {canvas,slider,axis,h,v} of views) {
      slider.value = point[axis];
      const ctx = canvas.getContext('2d'), image = ctx.createImageData(canvas.width,canvas.height);
      for (let y=0;y<canvas.height;y++) for (let x=0;x<canvas.width;x++) {
        const index = point[axis]*stride[axis]+(shape[h]-1-x)*stride[h]+(shape[v]-1-y)*stride[v];
        const intensity = 255*((ct[index]-centre)/width+.5);
        const label = mask[index];
        // Compare only in-plane neighbours inside the crop, avoiding wrapped rows.
        const edge = outline.checked && label && (
          (x > 0 && mask[index+stride[h]] !== label) ||
          (x+1 < canvas.width && mask[index-stride[h]] !== label) ||
          (y > 0 && mask[index+stride[v]] !== label) ||
          (y+1 < canvas.height && mask[index-stride[v]] !== label));
        const tumourEdge = edge && label === 2;
        const offset=4*(x+y*canvas.width);
        image.data[offset]=edge?255:intensity;
        image.data[offset+1]=tumourEdge?82:edge?184:intensity;
        image.data[offset+2]=tumourEdge?87:edge?35:intensity;
        image.data[offset+3]=255;
      }
      ctx.putImageData(image,0,0);
      ctx.strokeStyle='#55eeea';
      ctx.beginPath();
      ctx.arc(shape[h]-.5-point[h],shape[v]-.5-point[v],3.5,0,2*Math.PI);
      ctx.stroke();
    }
    const index=point.reduce((sum,value,i)=>sum+value*stride[i],0);
    const description = grid.labels ? grid.labels[mask[index]] : (mask[index]?'inside':'outside')+' the supplied liver label.';
    document.querySelector('#point').textContent=(grid.labels?'RAS grid voxel (':'Source voxel (')+point.map((x,i)=>x+origin[i]).join(', ')+') · CT value '+ct[index]+' · '+description;
  }
  for (const [name,axis,h,v] of [['Axial',2,0,1],['Coronal',1,0,2],['Sagittal',0,1,2]]) {
    const figure=document.createElement('figure'), canvas=document.createElement('canvas');
    const label=document.createElement('label'), slider=document.createElement('input');
    slider.type='range'; slider.min=0; slider.max=shape[axis]-1;
    label.append(name+' slice ',slider);
    canvas.width=shape[h]; canvas.height=shape[v]; canvas.setAttribute('aria-label',name+' liver CT');
    if (grid.spacing) canvas.style.aspectRatio = (shape[h]*grid.spacing[h])+' / '+(shape[v]*grid.spacing[v]);
    canvas.onclick=event=>{
      const rect=canvas.getBoundingClientRect();
      const sample=(position,size,extent)=>Math.min(extent-1,Math.max(0,Math.floor(position*extent/size)));
      point[h]=shape[h]-1-sample(event.clientX-rect.left,rect.width,shape[h]);
      point[v]=shape[v]-1-sample(event.clientY-rect.top,rect.height,shape[v]);
      render();
    };
    slider.oninput=()=>{point[axis]=slider.valueAsNumber;render();};
    const caption=document.createElement('figcaption');
    caption.textContent=axis===2?'Right to left · anterior up':axis===1?'Right to left · superior up':'Anterior to posterior · superior up';
    figure.append(label,canvas,caption);document.querySelector('.views').append(figure);
    views.push({canvas,slider,axis,h,v});
  }
  windowControl.onchange=outline.onchange=render;
  render();
}
load().catch(()=>{document.querySelector('#point').textContent='The CT could not be loaded. Reload the page to retry.';});
