'use strict';

const get = id => document.getElementById(id);
const planes = [...document.querySelectorAll('[data-axis]')];
const displayAxes = [[2,1],[2,0],[0,1]];
let atlas, samples, labels, point;

async function readNifti(row, shape) {
  const response = await fetch(row.file);
  if (!response.ok) throw Error('Source NIfTI unavailable');
  const bytes = await response.arrayBuffer();
  const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))]
    .map(value => value.toString(16).padStart(2,'0')).join('');
  if (hash !== row.sha256) throw Error('Source NIfTI checksum differs');
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  const raw = await new Response(stream).arrayBuffer();
  const header = new DataView(raw);
  const dtype = header.getInt16(70,true), offset = header.getFloat32(108,true);
  if (header.getInt32(0,true) !== 348 || dtype !== row.datatype || offset !== row.offset ||
      shape.some((value,i) => header.getInt16(42 + 2*i,true) !== value)) {
    throw Error('Unexpected source geometry');
  }
  const count = shape.reduce((a,b)=>a*b,1);
  const bit64 = dtype === 64;
  if (raw.byteLength !== offset + count * (bit64 ? 8 : 2)) throw Error('Unexpected source extent');
  return bit64
    ? Float64Array.from({length:count},(_,i)=>header.getFloat64(offset+i*8,true))
    : Uint16Array.from({length:count},(_,i)=>header.getUint16(offset+i*2,true));
}

function index([i,j,k]) {
  return i + atlas.shape[0] * (j + atlas.shape[1] * k);
}

function drawPlane(plane, white) {
  const axis = Number(plane.dataset.axis), [u,v] = displayAxes[axis];
  const canvas = plane.querySelector('canvas'), frame = plane.querySelector('.frame');
  const width = atlas.shape[u], height = atlas.shape[v];
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d'), image = context.createImageData(width,height);
  const coordinate = [...point], outline = get('contours').checked;
  const slider = plane.querySelector('input');
  slider.value = point[axis];
  slider.setAttribute('aria-valuetext','Section '+point[axis]+' of '+(atlas.shape[axis]-1));
  const stride = [1,atlas.shape[0],atlas.shape[0]*atlas.shape[1]];
  for (let y=0;y<height;y++) {
    coordinate[v]=y;
    for (let x=0;x<width;x++) {
      coordinate[u]=x;
      const sampleIndex = index(coordinate), label = labels[sampleIndex];
      const boundary = outline && label && (x===0 || y===0 || x===width-1 || y===height-1 ||
        labels[sampleIndex-stride[u]] !== label || labels[sampleIndex+stride[u]] !== label ||
        labels[sampleIndex-stride[v]] !== label || labels[sampleIndex+stride[v]] !== label);
      const gray = samples[sampleIndex] / white * 255;
      const color = boundary ? atlas.labels[label].color : [gray,gray,gray];
      image.data.set([...color,255],4*(x+width*y));
    }
  }
  context.putImageData(image,0,0);
  frame.style.setProperty('--x',(point[u]+.5)*100/width+'%');
  frame.style.setProperty('--y',(point[v]+.5)*100/height+'%');
}

function draw() {
  const white = get('white').valueAsNumber;
  get('white-value').textContent = white;
  for (const plane of planes) drawPlane(plane,white);
  const i = index(point);
  const world = atlas.affineRASmm.slice(0,3).map(row =>
    (row[3] + point.reduce((sum,value,j)=>sum+value*row[j],0)).toFixed(2));
  get('sample').textContent = 'Voxel '+point.join(', ')+' · RAS '+world.join(', ')+
    ' mm · T2 source intensity '+samples[i]+' · '+(atlas.labels[labels[i]]?.name || 'Outside labelled regions');
}

async function start() {
  get('retry').hidden = true;
  get('sections').hidden = true;
  get('status').textContent = 'Verifying the original MRI and label files…';
  try {
    const response = await fetch('atlas.json');
    if (!response.ok) throw Error('Atlas inventory unavailable');
    atlas = await response.json();
    [samples,labels] = await Promise.all([readNifti(atlas.files.mri,atlas.shape),readNifti(atlas.files.mask,atlas.shape)]);
    point = [...atlas.initialPoint];
    for (const plane of planes) {
      const axis = Number(plane.dataset.axis);
      plane.querySelector('input').max = atlas.shape[axis]-1;
    }
    draw();
    get('sections').hidden = false;
    get('status').textContent = 'Original T2 volume and source labels verified.';
  } catch {
    get('status').textContent = 'The MRI or label files could not be verified.';
    get('retry').hidden = false;
  }
}

for (const plane of planes) {
  const axis = Number(plane.dataset.axis), [u,v] = displayAxes[axis];
  const slider = plane.querySelector('input');
  slider.addEventListener('input',() => {
    point[axis] = slider.valueAsNumber;
    draw();
  });
  plane.querySelector('canvas').addEventListener('click',event => {
    const bounds = event.currentTarget.getBoundingClientRect();
    point[u] = Math.max(0,Math.min(atlas.shape[u]-1,Math.floor((event.clientX-bounds.left)*atlas.shape[u]/bounds.width)));
    point[v] = Math.max(0,Math.min(atlas.shape[v]-1,Math.floor((event.clientY-bounds.top)*atlas.shape[v]/bounds.height)));
    draw();
  });
}
get('contours').addEventListener('input',draw);
get('white').addEventListener('input',draw);
get('retry').addEventListener('click',start);
start();
