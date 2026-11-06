'use strict';

const get = id => document.getElementById(id);
const mri = get('mri'), stack = get('stack');
const sourceHash = '5c75d02cdc2ba844a720957dcacea3cdb685f32426312cdca4d1536c44fb52a5';
const chunks = new Map();
const states = new Map();
let source, outlines, generation = 0, current = null;

async function hash(bytes) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))]
    .map(byte => byte.toString(16).padStart(2,'0')).join('');
}

function selectedSequence() {
  return source.sequences[get('sequence').value];
}

function sourceWindow() {
  const frame = selectedSequence().frames[get('slice').valueAsNumber];
  const centre = Number(frame.sourceWindowCenter), width = Number(frame.sourceWindowWidth);
  get('black').value = centre - .5 - (width - 1)/2;
  get('white').value = centre - .5 + (width - 1)/2;
}

function buildOutlines() {
  const sequence = source.sequences.postcontrast;
  if (sequence.sourceMetadata.SeriesInstanceUID !== source.annotation.referencedSeries) throw Error('Referenced series differs');
  return source.annotation.contours.map(row => {
    const frame = sequence.frames[row.sliceIndex];
    if (frame.sopUID !== row.sopUID) throw Error('Referenced image differs');
    const origin = frame.imagePositionPatient.map(Number);
    const orientation = frame.imageOrientationPatient.map(Number);
    const spacing = frame.pixelSpacingRowColumn.map(Number);
    const column = orientation.slice(0,3).map(value => value * spacing[1]);
    const line = orientation.slice(3).map(value => value * spacing[0]);
    const dot = (a,b) => a.reduce((sum,value,i) => sum + value*b[i],0);
    const cc = dot(column,column), rr = dot(line,line), cr = dot(column,line);
    const determinant = cc*rr-cr*cr;
    const numbers = row.originalLPSStrings.map(Number), points = [];
    if (numbers.length !== 3*row.pointCount) throw Error('Contour point count differs');
    for (let i=0;i<numbers.length;i+=3) points.push(numbers.slice(i,i+3));
    const pixels = points.map(point => {
      const delta = point.map((value,i) => value-origin[i]);
      const c = dot(delta,column), r = dot(delta,line);
      const x = (rr*c-cr*r)/determinant, y = (cc*r-cr*c)/determinant;
      const residual = Math.hypot(...delta.map((value,i) => value-x*column[i]-y*line[i]));
      if (!(residual < .001 && x >= -.5 && x < 511.5 && y >= -.5 && y < 511.5)) throw Error('Contour plane differs');
      return [x+.5,y+.5];
    });
    return {...row,points,pixels};
  });
}

function stroke(context,points,project,color) {
  context.strokeStyle = color;
  context.beginPath();
  for (const [i,point] of points.entries()) {
    const [x,y] = project(point);
    if (i) context.lineTo(x,y);
    else context.moveTo(x,y);
  }
  context.closePath();
  context.stroke();
}

function drawStack() {
  if (!outlines) return;
  const context = stack.getContext('2d');
  const points = outlines.flatMap(row => row.points);
  const low = [0,1,2].map(axis => Math.min(...points.map(point => point[axis])));
  const high = [0,1,2].map(axis => Math.max(...points.map(point => point[axis])));
  const centre = low.map((value,i) => (value+high[i])/2);
  const scale = 355/Math.hypot(...high.map((value,i) => value-low[i]));
  const yaw = get('yaw').valueAsNumber*Math.PI/180, pitch = get('pitch').valueAsNumber*Math.PI/180;
  function projectDirection([x,y,z]) {
    const horizontal = Math.cos(yaw)*x-Math.sin(yaw)*y;
    const depth = Math.sin(yaw)*x+Math.cos(yaw)*y;
    return [horizontal,-Math.cos(pitch)*z+Math.sin(pitch)*depth];
  }
  function project(point) {
    const [x,y] = projectDirection(point.map((value,i) => value-centre[i]));
    return [320+scale*x,220+scale*y];
  }
  context.fillStyle = '#111a20';
  context.fillRect(0,0,640,480);
  const active = current?.key === 'postcontrast' ? current.slice : null;
  context.lineWidth = 1;
  for (const row of outlines) if (row.sliceIndex !== active) stroke(context,row.points,project,'#ac995e');
  context.lineWidth = 2;
  const highlighted = outlines.filter(row => row.sliceIndex === active);
  for (const row of highlighted) stroke(context,row.points,project,'#6ef0ed');

  // Patient-space triad uses the original DICOM LPS directions.
  context.font = '15px system-ui';
  context.textAlign = 'center';
  for (const [axis,label] of [[[1,0,0],'L'],[[0,1,0],'P'],[[0,0,1],'S']]) {
    const [x,y] = projectDirection(axis);
    context.strokeStyle = '#dbe8ec';
    context.beginPath();context.moveTo(54,410);context.lineTo(54+30*x,410+30*y);context.stroke();
    context.fillStyle = '#dbe8ec';context.fillText(label,54+43*x,415+43*y);
  }
  context.beginPath();context.moveTo(440,435);context.lineTo(440+10*scale,435);context.stroke();
  context.textAlign = 'left';context.fillText('10 mm',440,460);
  get('contour-status').textContent = current?.key === 'postcontrast'
    ? '27 original post-contrast outlines · ' + highlighted.length + ' on the displayed section.'
    : '27 original post-contrast outlines. Select a verified post-contrast section to highlight its contour plane.';
  stack.hidden = false;
}

function remember() {
  if (!source) return;
  states.set(get('sequence').value,{
    slice: get('slice').valueAsNumber,
    black: get('black').value,
    white: get('white').value,
  });
}

function chunkSamples(chunk) {
  if (!chunks.has(chunk.file)) {
    const task = (async () => {
      const response = await fetch(chunk.file);
      if (!response.ok) throw Error('Source MRI unavailable');
      const bytes = await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
      if (bytes.byteLength !== chunk.decodedBytes || await hash(bytes) !== chunk.sha256) throw Error('Source MRI checksum differs');
      const view = new DataView(bytes);
      return Int16Array.from({length:bytes.byteLength/2},(_,i) => view.getInt16(i*2,true));
    })();
    chunks.set(chunk.file,task);
    task.catch(() => {if (chunks.get(chunk.file) === task) chunks.delete(chunk.file);});
    while (chunks.size > 3) chunks.delete(chunks.keys().next().value);
  }
  return chunks.get(chunk.file);
}

async function draw() {
  const attempt = ++generation;
  current = null;mri.hidden = true;get('sample').textContent = '';get('retry').hidden = true;
  drawStack();
  const key = get('sequence').value, sequence = selectedSequence();
  const slice = get('slice').valueAsNumber;
  const black = get('black').valueAsNumber, white = get('white').valueAsNumber;
  remember();
  get('section').textContent = (slice+1)+' / '+sequence.frames.length;
  if (!Number.isFinite(black) || !Number.isFinite(white) || white <= black) {
    get('status').textContent = 'Enter finite display values with white greater than black.';
    return;
  }
  get('status').textContent = 'Loading verified source section…';
  try {
    const chunk = sequence.chunks.find(row => slice >= row.firstSlice && slice < row.firstSlice+row.slices);
    const samples = await chunkSamples(chunk);
    if (attempt !== generation) return;
    const [width,height] = sequence.shape;
    const offset = (slice-chunk.firstSlice)*width*height;
    const context = mri.getContext('2d'), image = context.createImageData(width,height);
    for (let i=0;i<width*height;i++) {
      const gray = 255*(samples[offset+i]-black)/(white-black);
      image.data[4*i] = image.data[4*i+1] = image.data[4*i+2] = gray;
      image.data[4*i+3] = 255;
    }
    context.putImageData(image,0,0);
    context.lineWidth = .8;
    if (key === 'postcontrast' && get('overlay').checked) {
      for (const row of outlines) if (row.sliceIndex === slice) stroke(context,row.pixels,point => point,'#ffe278');
    }
    mri.style.aspectRatio = (width*sequence.pixelSpacingRowColumnMM[1])/(height*sequence.pixelSpacingRowColumnMM[0]);
    current = {key,slice,samples,offset,frame:sequence.frames[slice]};
    mri.hidden = false;
    get('status').textContent = 'Verified '+(key === 'postcontrast' ? 'post-contrast' : 'T2')+' section '+(slice+1)+' of '+sequence.frames.length+'.';
    drawStack();
  } catch {
    if (attempt !== generation) return;
    get('status').textContent = 'The source section could not be verified. Retry to load it again.';
    get('retry').hidden = false;
  }
}

function selectSequence() {
  const key = get('sequence').value, sequence = selectedSequence(), previous = states.get(key);
  get('slice').max = sequence.frames.length-1;
  get('slice').value = previous?.slice ?? sequence.initialSlice;
  if (previous) {get('black').value = previous.black;get('white').value = previous.white;}
  else sourceWindow();
  get('overlay').disabled = key !== 'postcontrast';
  get('sequence-note').textContent = sequence.sourceMetadata.SeriesDescription + ' · ' +
    sequence.pixelSpacingRowColumnMM.map(value => value+' mm').join(' × ') + ' in-plane · ' +
    sequence.sliceThicknessMM + ' mm thickness · approximately ' + Number(sequence.centreSpacingMM.toFixed(3)) + ' mm between slice centres.';
  draw();
}

async function start() {
  get('controls').disabled = true;get('retry').hidden = true;
  try {
    const response = await fetch('source.json');
    if (!response.ok) throw Error('Source inventory missing');
    const bytes = await response.arrayBuffer();
    if (await hash(bytes) !== sourceHash) throw Error('Source inventory checksum differs');
    source = JSON.parse(new TextDecoder().decode(bytes));
    outlines = buildOutlines();
    get('controls').disabled = false;
    selectSequence();
  } catch {
    get('status').textContent = 'The source inventory could not be verified.';
    get('retry').hidden = false;
  }
}

get('sequence').addEventListener('change',selectSequence);
for (const id of ['slice','black','white','overlay']) get(id).addEventListener('input',draw);
get('source-window').addEventListener('click',() => {sourceWindow();draw();});
for (const id of ['yaw','pitch']) get(id).addEventListener('input',drawStack);
get('retry').addEventListener('click',() => source ? draw() : start());
mri.addEventListener('keydown',event => {
  if (!current || !['ArrowLeft','ArrowRight'].includes(event.key)) return;
  event.preventDefault();
  if (event.key === 'ArrowLeft') get('slice').stepDown();
  else get('slice').stepUp();
  draw();
});
mri.addEventListener('click',event => {
  if (!current) return;
  const bounds = mri.getBoundingClientRect(), {samples,offset,frame} = current;
  const x = Math.floor((event.clientX-bounds.left)*512/bounds.width), y = Math.floor((event.clientY-bounds.top)*512/bounds.height);
  if (x < 0 || y < 0 || x >= 512 || y >= 512) return;
  const direction = frame.imageOrientationPatient.map(Number), spacing = frame.pixelSpacingRowColumn.map(Number);
  const lps = frame.imagePositionPatient.map((value,i) => Number(value)+x*spacing[1]*direction[i]+y*spacing[0]*direction[i+3]);
  get('sample').textContent = 'Column '+(x+1)+', row '+(y+1)+' · source intensity '+samples[offset+x+512*y]+
    ' · LPS '+lps.map(value => value.toFixed(2)).join(', ')+' mm.';
});
start();
