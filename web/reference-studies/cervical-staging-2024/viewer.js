'use strict';

const get = id => document.getElementById(id);
const focus = get('focus'), figure = get('figure'), zoom = get('zoom');
const image = get('image'), caption = get('caption'), status = get('status'), retry = get('retry');
let figures, generation = 0;

function resize() {
  if (!image.hidden) image.style.width = zoom.value === 'fit' ? '100%' : Number(zoom.value) * image.naturalWidth + 'px';
}

function filterFigures() {
  const previous = figure.value || '4';
  const rows = figures.filter(row => focus.value === 'all' || row.topics.includes(focus.value));
  figure.replaceChildren(...rows.map(row => new Option(row.number + ' · ' + row.title,row.number)));
  if (rows.some(row => String(row.number) === previous)) figure.value = previous;
}

async function fetchImage(row) {
  const response = await fetch(row.file);
  if (!response.ok) throw Error('Source image missing');
  const bytes = await response.arrayBuffer();
  const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))]
    .map(byte => byte.toString(16).padStart(2,'0')).join('');
  if (digest !== row.sha256) throw Error('Source image checksum differs');
  const type = row.file.endsWith('.png') ? 'image/png' : 'image/jpeg';
  return new Promise((resolve,reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(new Blob([bytes],{type}));
  });
}

async function show() {
  const attempt = ++generation;
  image.hidden = true;
  caption.textContent = '';
  retry.hidden = true;
  status.textContent = 'Loading verified source figure…';
  try {
    if (!figures) {
      const response = await fetch('figures.json');
      if (!response.ok) throw Error('Figure inventory missing');
      const manifest = await response.json();
      if (manifest.figures.length !== 11) throw Error('Figure inventory differs');
      if (attempt !== generation) return;
      figures = manifest.figures;
      filterFigures();
      figure.disabled = false;
    }
    const row = figures.find(row => row.number === Number(figure.value));
    const data = await fetchImage(row);
    if (attempt !== generation) return;
    image.alt = 'Figure ' + row.number + ' · ' + row.title;
    image.src = data;
    await image.decode();
    if (attempt !== generation) return;
    if (image.naturalWidth !== row.width || image.naturalHeight !== row.height) throw Error('Source dimensions differ');
    image.hidden = false;
    resize();
    get('viewport').scrollTo(0,0);
    caption.textContent = row.note;
    status.textContent = 'Figure ' + row.number + ' · ' + row.width + ' × ' + row.height + ' embedded pixels.';
  } catch {
    if (attempt !== generation) return;
    status.textContent = 'The source figure could not be verified.';
    retry.hidden = false;
  }
}

focus.addEventListener('change',() => {
  if (figures) filterFigures();
  show();
});
figure.addEventListener('change',show);
zoom.addEventListener('change',resize);
retry.addEventListener('click',show);
show();
