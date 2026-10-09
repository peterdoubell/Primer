'use strict';
(async () => {
  const data = JSON.parse(document.getElementById('dataset').textContent);
  const byId = id => document.getElementById(id);
  const series = byId('series'), temporal = byId('temporal'), slider = byId('frame');
  const center = byId('center'), width = byId('width'), canvas = byId('view');
  const decoded = new Map();
  const sha = async raw => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', raw)), b => b.toString(16).padStart(2, '0')).join('');
  let pixels, selected, frames = [], current, request = 0;
  async function sourcePixels(s) {
    if (!/^series-[0-9]{4}\.bin\.gz$/.test(s.file)) throw Error('Invalid source transport path');
    if (!decoded.has(s.uid)) decoded.set(s.uid, (async () => {
      const response = await fetch('./' + s.file);
      if (!response.ok) throw Error('Original source series could not load');
      const compressed = await response.arrayBuffer();
      if (await sha(compressed) !== s.compressed_sha256) throw Error('Source compressed transport changed');
      const raw = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
      if (raw.byteLength !== s.decoded_bytes || await sha(raw) !== s.decoded_int16_le_sha256) throw Error('Original source scalar payload changed');
      return new DataView(raw);
    })().catch(error => { decoded.delete(s.uid); throw error; }));
    return decoded.get(s.uid);
  }
  data.series.forEach((s, i) => series.add(new Option(s.number + ' · ' + s.description + ' · ' + s.frames.length + ' frames', String(i))));
  const sourceWindow = () => { center.value = current.window_center; width.value = current.window_width; };
  function redraw(resetWindow) {
    current = frames[Number(slider.value)];
    if (!current) return;
    if (resetWindow && !byId('lock-window').checked) sourceWindow();
    const c = Number(center.value), w = Number(width.value);
    if (!Number.isFinite(c) || !Number.isFinite(w) || w < 1) return;
    canvas.width = current.columns; canvas.height = current.rows;
    const physicalAspect = (current.columns * current.spacing[1]) / (current.rows * current.spacing[0]);
    canvas.style.aspectRatio = String(physicalAspect);
    canvas.style.width = '100%'; canvas.style.height = 'auto';
    const ctx = canvas.getContext('2d'); const image = ctx.createImageData(current.columns, current.rows);
    for (let i = 0; i < current.rows * current.columns; i++) {
      const source = pixels.getInt16(current.offset + i * 2, true);
      const value = w === 1 ? (source > c - .5 ? 255 : 0)
        : Math.round(Math.max(0, Math.min(255, ((source - (c - .5)) / (w - 1) + .5) * 255)));
      image.data.set([value, value, value, 255], i * 4);
    }
    ctx.putImageData(image, 0, 0);
    canvas.dataset.sop = current.sop; canvas.dataset.sourceOffset = current.offset;
    canvas.dataset.sourceRows = current.rows; canvas.dataset.sourceColumns = current.columns;
    byId('ordinal').textContent = (Number(slider.value) + 1) + ' / ' + frames.length;
    byId('previous').disabled = Number(slider.value) === 0;
    byId('next').disabled = Number(slider.value) === frames.length - 1;
    byId('geometry').textContent = 'Source instance ' + current.instance + '; temporal identifier ' + current.temporal
      + '; acquisition time ' + (current.acquisition_time || 'not supplied') + '; trigger time ' + (current.trigger_time ?? 'not supplied')
      + '; ImageType ' + current.image_type.join('/') + '. LPS position: ' + current.position.join(', ')
      + ' mm; source orientation: ' + current.orientation.join(', ') + '; reconstructed pixel spacing: ' + current.spacing.join(' × ') + ' mm.';
  }
  function chooseTemporal() {
    frames = selected.frames.filter(f => temporal.value === 'all' || f.temporal === temporal.value);
    slider.max = Math.max(0, frames.length - 1); slider.value = 0;
    current = frames[0]; sourceWindow(); redraw(false);
  }
  async function chooseSeries() {
    const token = ++request, choice = data.series[Number(series.value)];
    byId('status').textContent = 'Loading and verifying complete original series…';
    current = null; frames = []; canvas.width = 0; canvas.height = 0;
    const controls = [temporal, slider, center, width, byId('source-window'), byId('previous'), byId('next')];
    controls.forEach(i => { i.disabled = true; });
    try { const values = await sourcePixels(choice); if (token !== request) return; pixels = values; selected = choice; }
    catch (error) { if (token === request) byId('status').textContent = error.message; return; }
    temporal.replaceChildren(new Option('All original frames', 'all'));
    [...new Set(selected.frames.map(f => f.temporal))].filter(t => t !== 'not supplied')
      .sort((a, b) => Number(a) - Number(b)).forEach(t => temporal.add(new Option('Source temporal position ' + t, t)));
    chooseTemporal();
    [temporal, slider, center, width, byId('source-window')].forEach(i => { i.disabled = false; });
    byId('status').textContent = selected.frames.length + ' verified frames in this source series. Complete study: '
      + data.series.length + ' series; ' + data.source_frames + ' frames; ' + data.source_pixel_samples + ' original int16 samples retained.';
  }
  series.addEventListener('change', chooseSeries); temporal.addEventListener('change', chooseTemporal);
  slider.addEventListener('input', () => redraw(true));
  [center, width].forEach(i => i.addEventListener('input', () => redraw(false)));
  byId('source-window').addEventListener('click', () => { sourceWindow(); redraw(false); });
  for (const [id, delta] of [['previous', -1], ['next', 1]]) byId(id).addEventListener('click', () => {
    slider.value = Math.max(0, Math.min(frames.length - 1, Number(slider.value) + delta)); redraw(true);
  });
  canvas.addEventListener('pointermove', event => {
    if (!current) return;
    const box = canvas.getBoundingClientRect(); const x = Math.floor((event.clientX - box.left) / box.width * current.columns);
    const y = Math.floor((event.clientY - box.top) / box.height * current.rows);
    if (x < 0 || y < 0 || x >= current.columns || y >= current.rows) return;
    const value = pixels.getInt16(current.offset + (y * current.columns + x) * 2, true);
    byId('sample').textContent = 'Original stored int16 sample: row ' + y + ', column ' + x + ' = ' + value + '. No physical ADC/concentration unit inferred.';
  });
  series.value = String(Math.max(0, data.series.findIndex(s => s.number === 4))); await chooseSeries();
})().catch(error => { document.getElementById('status').textContent = 'The original source study could not load: ' + error.message; });
