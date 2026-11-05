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
  let point = (grid.initialVoxel || [193,161,232]).map((v,i) => v-origin[i]);
  const stride = [1,shape[0],shape[0]*shape[1]];
  const windowControl = document.querySelector('#window');
  const outline = document.querySelector('#outline');
  const views = [];
  const organControl = document.querySelector('#organ');
  if (organControl) {
    organControl.addEventListener('change', () => {
      point = grid.centers[Number(organControl.value)].map((value,i)=>value-origin[i]);
      measurement = null;
      render();
      organControl.dispatchEvent(new Event('organ-positioned'));
    });
  }
  const ruler = document.querySelector('#ruler');
  let measurement = null;
  function drawCaliper(ctx, axis, h, v) {
    if (!measurement || measurement.axis !== axis || measurement.start[axis] !== point[axis]) return;
    const {start,end} = measurement;
    const x = p => shape[h] - .5 - p[h];
    const y = p => shape[v] - .5 - p[v];
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = .55;
    ctx.beginPath();
    if (end) {
      ctx.moveTo(x(start),y(start));
      ctx.lineTo(x(end),y(end));
    }
    for (const endpoint of end ? [start,end] : [start]) {
      ctx.moveTo(x(endpoint)-1.5,y(endpoint));
      ctx.lineTo(x(endpoint)+1.5,y(endpoint));
      ctx.moveTo(x(endpoint),y(endpoint)-1.5);
      ctx.lineTo(x(endpoint),y(endpoint)+1.5);
    }
    ctx.stroke();
  }
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
        const color = grid.colors?.[label] || (label === 2 ? [255,82,87] : [255,184,35]);
        const offset=4*(x+y*canvas.width);
        image.data[offset]=edge?color[0]:intensity;
        image.data[offset+1]=edge?color[1]:intensity;
        image.data[offset+2]=edge?color[2]:intensity;
        image.data[offset+3]=255;
      }
      ctx.putImageData(image,0,0);
      ctx.lineWidth=1;
      ctx.strokeStyle='#55eeea';
      ctx.beginPath();
      ctx.arc(shape[h]-.5-point[h],shape[v]-.5-point[v],3.5,0,2*Math.PI);
      ctx.stroke();
      drawCaliper(ctx,axis,h,v);
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
    canvas.width=shape[h]; canvas.height=shape[v]; canvas.setAttribute('aria-label',name+' '+(grid.organ || 'liver')+' CT');
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
  if (ruler) {
    const plane = ruler.querySelector('#ruler-plane');
    const start = ruler.querySelector('#ruler-start');
    const end = ruler.querySelector('#ruler-end');
    const clear = ruler.querySelector('#ruler-clear');
    const reading = ruler.querySelector('#ruler-reading');
    const describe = p => '(' + p.map((v,i)=>v+origin[i]).join(', ') + ')';
    function updateRuler() {
      clear.disabled = !measurement;
      end.disabled = !measurement || point[measurement.axis] !== measurement.start[measurement.axis];
      if (!measurement) {
        reading.textContent = 'Choose the first margin.';
        return;
      }
      const {axis,start:a,end:b} = measurement;
      const slice = a[axis] + origin[axis];
      const location = plane.selectedOptions[0].textContent + ' slice ' + slice;
      if (b) {
        const mm = Math.hypot(...a.map((value,i)=>(value-b[i])*grid.spacing[i]));
        reading.textContent = location + ' · ' + mm.toFixed(2) + ' mm between voxel centres ' + describe(a) + ' and ' + describe(b) + '.';
      } else {
        reading.textContent = location + ' · start ' + describe(a) + '. ' +
          (end.disabled ? 'Return to this slice to mark the end.' : 'Choose the opposite margin.');
      }
    }
    start.onclick = () => {
      measurement = {axis:Number(plane.value),start:point.slice(),end:null};
      render(); updateRuler();
    };
    end.onclick = () => { measurement.end = point.slice(); render(); updateRuler(); };
    clear.onclick = plane.onchange = () => { measurement = null; render(); updateRuler(); };
    document.querySelector('.views').addEventListener('input',updateRuler);
    document.querySelector('.views').addEventListener('click',updateRuler);
    organControl?.addEventListener('organ-positioned', updateRuler);
    ruler.disabled = false;
  }
  windowControl.onchange=outline.onchange=render;
  render();
}
load().catch(()=>{document.querySelector('#point').textContent='The CT could not be loaded. Reload the page to retry.';});
