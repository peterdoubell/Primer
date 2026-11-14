'use strict';

(() => {
  const get = id => document.getElementById(id);
  const canvas = get('mri');
  const from = new URLSearchParams(location.search).get('from');
  if (['ra.liver-masses','ra.liver-lirads'].includes(from)) {
    const back = get('study-return');
    back.href = '/app/#/radiology/' + from;
    back.textContent = from === 'ra.liver-masses' ? 'Return to liver mass reporting' : 'Return to LI-RADS reporting';
  }
  const controls = ['slice','black','white','show-tumour','show-regions'];
  const cache = new Map();
  let volume;
  let generation = 0;

  async function digest(buffer) {
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', buffer)), byte => byte.toString(16).padStart(2,'0')).join('');
  }

  async function readChunk(row) {
    if (!cache.has(row.file)) {
      const task = (async () => {
        const response = await fetch(row.file);
        if (!response.ok) throw new Error('Source chunk unavailable');
        const raw = await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
        if (raw.byteLength !== row.decodedBytes || await digest(raw) !== row.sha256) throw new Error('Source chunk differs');
        return raw;
      })();
      cache.set(row.file, task);
      task.catch(() => { if (cache.get(row.file) === task) cache.delete(row.file); });
      while (cache.size > 9) cache.delete(cache.keys().next().value);
    }
    return cache.get(row.file);
  }

  async function draw() {
    const attempt = ++generation;
    const slice = get('slice').valueAsNumber;
    const black = get('black').valueAsNumber;
    const white = get('white').valueAsNumber;
    get('section').textContent = `${slice + 1} / ${volume.shape[2]}`;
    canvas.hidden = true;
    get('overlap').textContent = '';
    get('retry').hidden = true;
    if (!Number.isFinite(black) || !Number.isFinite(white) || white <= black) {
      get('status').textContent = 'Set the white point above the black point.';
      return;
    }
    get('status').textContent = 'Verifying source section…';
    try {
      const chunk = volume.chunks.find(row => slice >= row.firstSlice && slice < row.firstSlice + row.slices);
      const [image, labels, lesion] = await Promise.all([chunk.mri,chunk.regions,chunk.tumour].map(readChunk));
      if (attempt !== generation) return;
      const samples = new DataView(image), regions = new Uint8Array(labels), tumour = new Uint8Array(lesion);
      const [width,height] = volume.shape;
      const offset = (slice - chunk.firstSlice) * width * height;
      const index = (x,y) => offset + x + width * (height - 1 - y);
      const inside = (x,y) => x>=0 && x<width && y>=0 && y<height;
      const label = (array,x,y) => inside(x,y) ? array[index(x,y)] : 0;
      const edge = (array,x,y,value) => label(array,x-1,y)!==value || label(array,x+1,y)!==value || label(array,x,y-1)!==value || label(array,x,y+1)!==value;
      const context = canvas.getContext('2d'), pixels = context.createImageData(width,height);
      const showTumour = get('show-tumour').checked, showRegions = get('show-regions').checked;
      const counts = [0,0];
      for (let y=0;y<height;y++) for (let x=0;x<width;x++) {
        const at=index(x,y), code=regions[at];
        if (tumour[at] && (code===6 || code===7)) counts[code-6]++;
        const gray = 255 * (samples.getUint16(2*at,true)-black)/(white-black);
        let color = [gray,gray,gray];
        if (showRegions && (code===6 || code===7) && edge(regions,x,y,code)) color = code===6 ? [110,231,244] : [245,198,102];
        if (showTumour && tumour[at] && edge(tumour,x,y,1)) color = [255,115,140];
        pixels.data.set([...color,255],4*(x+width*y));
      }
      context.putImageData(pixels,0,0);
      canvas.hidden = false;
      get('overlap').textContent = `Tumour pixels on this section. Region 6: ${counts[0]}. Region 7: ${counts[1]}.`;
      get('status').textContent = `Verified source section ${slice+1}.`;
    } catch {
      if (attempt === generation) {
        get('status').textContent = 'The source section could not be verified.';
        get('retry').hidden = false;
      }
    }
  }

  async function start() {
    get('retry').hidden = true;
    try {
      const response = await fetch('volume.json');
      if (!response.ok) throw new Error('Source inventory unavailable');
      const raw = await response.arrayBuffer();
      if (await digest(raw) !== document.querySelector('main').dataset.volumeSha256) throw new Error('Source inventory differs');
      volume = JSON.parse(new TextDecoder().decode(raw));
      get('slice').value = volume.initialSlice;
      get('slice').disabled = false;
      get('black').value = volume.window[0];
      get('white').value = volume.window[1];
      await draw();
    } catch {
      get('status').textContent = 'The source inventory could not be verified.';
      get('retry').hidden = false;
    }
  }
  for (const id of controls) get(id).addEventListener('input', () => { if (volume) draw(); });
  get('retry').addEventListener('click', () => volume ? draw() : start());
  start();
})();
