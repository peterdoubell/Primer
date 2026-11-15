'use strict';
(async () => {
  const data = JSON.parse(document.getElementById('dataset').textContent);
  const byId = id => document.getElementById(id);
  const sha = async b => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', b)), v => v.toString(16).padStart(2, '0')).join('');
  async function decode(row) {
    if (!/^source-(?:image|label)\.bin\.gz$/.test(row.file)) throw Error('Invalid source array path');
    const response = await fetch('./' + row.file);
    if (!response.ok) throw Error('Original source array could not load');
    const received = await response.arrayBuffer();
    let raw;
    // HTTP gzip may already have been decoded by the browser. Either path
    // must end with the exact independently reviewed original scalar hash.
    if (received.byteLength === row.bytes && await sha(received) === row.raw_source_voxel_sha256) raw = received;
    else {
      if (await sha(received) !== row.compressed_sha256) throw Error('Source transport changed');
      raw = await new Response(new Blob([received]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    }
    if (raw.byteLength !== row.bytes || await sha(raw) !== row.raw_source_voxel_sha256) throw Error('Original complete scalar array changed');
    const view = new DataView(raw);
    const sample = row.datatype === 2 ? i => view.getUint8(i) : row.datatype === 4 ? i => view.getInt16(i*2, true)
      : row.datatype === 512 ? i => view.getUint16(i*2, true) : null;
    if (!sample) throw Error('Unreviewed scalar type');
    return sample;
  }
  const [image, mask] = await Promise.all([decode(data.image), decode(data.mask)]);
  const dims = data.image.dimensions, canvas = byId('view'), slider = byId('slice'), plane = byId('plane');
  const center = byId('center'), width = byId('width');
  let current;
  const at = p => p[0] + dims[0] * (p[1] + dims[1] * p[2]);
  function redraw() {
    const axis = Number(plane.value), axes = [0,1,2].filter(a => a !== axis);
    const w = dims[axes[0]], h = dims[axes[1]], level = Number(slider.value);
    const c = Number(center.value), ww = Number(width.value);
    if (!Number.isFinite(c) || !Number.isFinite(ww) || ww < 1) return;
    const coords = (x,y) => { const p=[0,0,0];p[axis]=level;p[axes[0]]=x;p[axes[1]]=y;return p; };
    canvas.width=w;canvas.height=h;
    const affine=data.image.selected_affine;
    const pitch = axes.map(a => Math.hypot(affine[0][a],affine[1][a],affine[2][a]));
    canvas.style.aspectRatio=String(w*pitch[0]/(h*pitch[1]));
    const ctx=canvas.getContext('2d'), pixels=ctx.createImageData(w,h);
    for (let y=0;y<h;y++) for (let x=0;x<w;x++) {
      const p=coords(x,y), index=at(p), v=image(index);
      const gray=ww===1?(v>c-.5?255:0):Math.round(Math.max(0,Math.min(255,((v-(c-.5))/(ww-1)+.5)*255)));
      let border=false;
      if (byId('overlay').checked && mask(index)===1) {
        border=[[x-1,y],[x+1,y],[x,y-1],[x,y+1]].some(([a,b]) => a<0||b<0||a>=w||b>=h||mask(at(coords(a,b)))===0);
      }
      pixels.data.set(border?[255,210,40,255]:[gray,gray,gray,255],4*(x+w*y));
    }
    ctx.putImageData(pixels,0,0);current={axis,axes,coords,w,h};
    canvas.dataset.axis=axis;canvas.dataset.sourceIndex=level;canvas.dataset.originalImage=data.image.raw_source_voxel_sha256;
    byId('ordinal').textContent=level+' / '+(dims[axis]-1);
    byId('geometry').textContent='Native source axis '+axis+', index '+level+'. Dimensions '+dims.join(' × ')+'. Declared source spacing '+data.image.pixdim.slice(1,4).join(' × ')+' mm. Complete source plane retained; display aspect follows its declared basis lengths.';
  }
  function changePlane() {const axis=Number(plane.value);slider.max=dims[axis]-1;slider.value=data.initial_indices[axis];redraw();}
  function reset() {center.value=data.initial_window[0];width.value=data.initial_window[1];plane.value='2';byId('overlay').checked=false;changePlane();}
  plane.addEventListener('change',changePlane);slider.addEventListener('input',redraw);
  for (const item of [center,width,byId('overlay')]) item.addEventListener('input',redraw);
  byId('reset').addEventListener('click',reset);
  canvas.addEventListener('pointermove',event=>{
    if (!current) return;
    const box=canvas.getBoundingClientRect(),x=Math.floor((event.clientX-box.left)/box.width*current.w),y=Math.floor((event.clientY-box.top)/box.height*current.h);
    if (x<0||y<0||x>=current.w||y>=current.h)return;
    const p=current.coords(x,y),index=at(p);const position=data.image.selected_affine.slice(0,3).map(row=>row[3]+row[0]*p[0]+row[1]*p[1]+row[2]*p[2]);
    byId('sample').textContent='Original source IJK '+p.join(', ')+': stored T2 value '+image(index)+'; source label '+mask(index)+'; image-declared RAS '+position.map(x=>x.toFixed(4)).join(', ')+' mm. No quantitative ADC unit inferred.';
  });
  byId('context').textContent=data.case_context;
  byId('correspondence').textContent='Producer image/mask table association retained. Maximum difference between their declared grid corners: '+data.source_grid_corner_difference_mm+' mm. '+(data.selected_source_affines_bit_identical?'Selected exported affines are bit-identical.':'Their declared transforms are not bit-identical; no fitted replacement is used.')+' Independent anatomical registration remains unapproved.';
  byId('provenance').textContent=JSON.stringify({image:data.image.provenance,mask:data.mask.provenance},null,2);
  byId('credit').textContent=data.attribution;
  reset();byId('status').textContent='Complete original T2 and annotation storage verified: '+data.source_voxels+' source samples. Original source values unchanged.';
})().catch(error=>{document.getElementById('status').textContent='Source arrays could not load: '+error.message;});
