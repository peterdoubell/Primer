'use strict';
async function load() {
  const get = id => document.getElementById(id);
  const data = await (await fetch('case.json')).json();
  const response = await fetch('ct.gz');
  if (!response.ok) throw Error('Missing CT');
  const bytes = await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)), b=>b.toString(16).padStart(2,'0')).join('');
  if (digest !== data.ct_sha256) throw Error('CT differs from source');
  const ct = new Int16Array(bytes);
  const [width,height,depth] = data.shape;
  if (ct.length !== width*height*depth) throw Error('CT extent differs');
  const rows = data.contours.map(row => {
    const values = row.coordinates.map(Number), points = [];
    for (let i=0;i<values.length;i+=3) points.push(values.slice(i,i+3));
    return {plane:row.plane,points};
  });
  const all = rows.flatMap(row=>row.points);
  const low = [0,1,2].map(axis=>Math.min(...all.map(point=>point[axis])));
  const high = [0,1,2].map(axis=>Math.max(...all.map(point=>point[axis])));
  const centre = low.map((value,i)=>(value+high[i])/2);
  const scale = 380 / Math.hypot(...high.map((value,i)=>value-low[i]));
  const canvas = get('ct'), spatial = get('contours');
  canvas.width=width; canvas.height=height;
  const slider=get('slice');
  slider.min=data.crop_origin[2];slider.max=data.crop_origin[2]+depth-1;
  slider.value=rows[Math.floor(rows.length/2)].plane;
  function path(context, points, project, color) {
    context.strokeStyle=color;context.beginPath();
    points.forEach((point,i)=>{
      const [x,y]=project(point);
      if (i===0) context.moveTo(x,y); else context.lineTo(x,y);
    });
    context.closePath();context.stroke();
  }
  function draw() {
    const plane=slider.valueAsNumber, offset=(plane-data.crop_origin[2])*width*height;
    const windowWidth=Number(get('window').value), windowCentre=windowWidth===400?50:70;
    const context=canvas.getContext('2d'), pixels=context.createImageData(width,height);
    for (let i=0;i<width*height;i++) {
      const value=255*((ct[offset+i]-windowCentre)/windowWidth+.5);
      pixels.data[4*i]=pixels.data[4*i+1]=pixels.data[4*i+2]=value;pixels.data[4*i+3]=255;
    }
    context.putImageData(pixels,0,0);context.lineWidth=.6;
    const selected=rows.filter(row=>row.plane===plane);
    if (get('overlay').checked) for (const row of selected)
      path(context,row.points,p=>[0,1].map(axis=>(p[axis]-data.source_origin[axis])/data.spacing[axis]-data.crop_origin[axis]+.5),'#ffb823');
    const model=spatial.getContext('2d');model.fillStyle='#111a20';model.fillRect(0,0,640,480);
    const yaw=Number(get('rotation').value)*Math.PI/180, pitch=Number(get('tilt').value)*Math.PI/180;
    function project(point) {
      const [x,y,z]=point.map((value,i)=>value-centre[i]);
      const horizontal=Math.cos(yaw)*x-Math.sin(yaw)*y, back=Math.sin(yaw)*x+Math.cos(yaw)*y;
      return [320+scale*horizontal,240-scale*(Math.cos(pitch)*z-Math.sin(pitch)*back)];
    }
    model.lineWidth=1;
    for (const row of rows) path(model,row.points,project,'#a07834');
    model.lineWidth=2;
    for (const row of selected) path(model,row.points,project,'#55eeea');
    get('status').textContent='CT slice '+plane+' · '+selected.length+' source outline'+(selected.length===1?'':'s')+' on this plane · 75 outlines in the 3D stack.';
  }
  for (const id of ['slice','window','overlay','rotation','tilt']) get(id).addEventListener('input',draw);
  slider.disabled=false;draw();
}
load().catch(()=>{document.getElementById('status').textContent='The source case could not be loaded. Reload to retry.';});
