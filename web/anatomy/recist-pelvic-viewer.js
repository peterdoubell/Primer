'use strict';

(() => {
  const get = id => document.getElementById(id);
  const canvas = get('ct');
  const context = canvas.getContext('2d');
  const slider = get('section');
  const plane = get('plane');
  // Both source grids index left, anterior, superior. Each display starts
  // at the top-left corner, with the superior/anterior direction at the top.
  const layouts = {
    axial: { normal: 2, horizontal: 0, vertical: 1, directions: ['A', 'P', 'R', 'L'] },
    coronal: { normal: 1, horizontal: 0, vertical: 2, directions: ['S', 'I', 'R', 'L'] },
    sagittal: { normal: 0, horizontal: 1, vertical: 2, directions: ['S', 'I', 'P', 'A'] },
  };
  let source;
  let ct;
  let labels;
  let shape;
  let visibleFrame;
  let nodalLabels;
  let lastSections = {};

  async function verify(bytes, expected) {
    const actual = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
      byte => byte.toString(16).padStart(2, '0')).join('');
    if (actual !== expected) throw Error('Source checksum differs.');
  }

  async function fetchBytes(file) {
    const response = await fetch(file);
    if (!response.ok) throw Error('Source file unavailable.');
    return response.arrayBuffer();
  }

  async function readVolume(row) {
    const packed = await fetchBytes(row.file);
    if (packed.byteLength !== row.bytes) throw Error('Source gzip size differs.');
    await verify(packed, row.compressedSHA256);
    const stream = new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip'));
    const bytes = await new Response(stream).arrayBuffer();
    const count = shape.reduce((product, size) => product * size, 1);
    if (bytes.byteLength !== row.decodedBytes || bytes.byteLength !== 2 * count) {
      throw Error('Source grid size differs.');
    }
    await verify(bytes, row.decodedSHA256);
    return new DataView(bytes);
  }

  function displayFrame(layout, fixed) {
    const { normal, horizontal, vertical, directions } = layout;
    const strides = [1, shape[0], shape[0] * shape[1]];
    const fullWidth = shape[horizontal];
    const fullHeight = shape[vertical];
    const centre = nodalLabels.get(Number(get('node').value)).displayIndexXYZ;
    const closeUp = get('view-size').value === 'detail';
    const width = closeUp ? Math.min(fullWidth, Math.round(100 / source.spacingXYZMm[horizontal])) : fullWidth;
    const height = closeUp ? Math.min(fullHeight, Math.round(100 / source.spacingXYZMm[vertical])) : fullHeight;
    const x0 = Math.max(0, Math.min(fullWidth - width, centre[horizontal] - Math.floor(width / 2)));
    const displayY = fullHeight - 1 - centre[vertical];
    const y0 = Math.max(0, Math.min(fullHeight - height, displayY - Math.floor(height / 2)));
    const start = fixed * strides[normal] + x0 * strides[horizontal]
      + (fullHeight - 1 - y0) * strides[vertical];
    const index = (x, y) => start + x * strides[horizontal] - y * strides[vertical];
    return { normal, horizontal, vertical, directions, fixed, width, height, index };
  }

  function hu(index) {
    return source.ctRescaleSlope * ct.getInt16(2 * index, true) + source.ctRescaleIntercept;
  }

  function draw() {
    if (!ct) return;
    const black = get('black').valueAsNumber;
    const white = get('white').valueAsNumber;
    get('pixel').textContent = '';
    if (!(white > black)) {
      visibleFrame = null;
      get('image-wrap').hidden = true;
      get('status').textContent = 'Set a white point above the black point.';
      return;
    }

    const frame = displayFrame(layouts[plane.value], slider.valueAsNumber);
    const { width, height, horizontal, vertical, normal, fixed, index, directions } = frame;
    const overlay = get('overlay').value;
    const selected = Number(get('node').value);
    const displayLabels = overlay === 'all' ? nodalLabels
      : overlay === 'selected' ? new Map([[selected, nodalLabels.get(selected)]]) : new Map();
    function mask(x, y) {
      if (x < 0 || y < 0 || x >= width || y >= height) return 0;
      return labels.getInt16(2 * index(x, y), true);
    }
    canvas.width = width;
    canvas.height = height;
    canvas.style.aspectRatio = (width * source.spacingXYZMm[horizontal]) + ' / '
      + (height * source.spacingXYZMm[vertical]);
    const raster = context.createImageData(width, height);
    let selectedSamples = 0;
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const label = mask(x, y);
        const row = displayLabels.get(label);
        const boundary = row && (mask(x - 1, y) !== label || mask(x + 1, y) !== label
          || mask(x, y - 1) !== label || mask(x, y + 1) !== label);
        const gray = 255 * (hu(index(x, y)) - black) / (white - black);
        const offset = 4 * (x + y * width);
        raster.data[offset] = boundary ? row.color[0] : gray;
        raster.data[offset + 1] = boundary ? row.color[1] : gray;
        raster.data[offset + 2] = boundary ? row.color[2] : gray;
        raster.data[offset + 3] = 255;
        if (row) selectedSamples += 1;
      }
    }
    context.putImageData(raster, 0, 0);
    visibleFrame = frame;
    ['top', 'bottom', 'left', 'right'].forEach((side, i) => {
      get('direction-' + side).textContent = directions[i];
    });
    canvas.setAttribute('aria-label', plane.value + ' CT. ' + directions[0] + ' at top, '
      + directions[2] + ' at left.');
    get('section-value').textContent = (fixed + 1) + ' / ' + shape[normal];
    const sourceIndex = fixed + (normal === 2 ? source.sourceZStart : 0);
    get('status').textContent = 'Verified ' + plane.value + ' section · source index ' + sourceIndex
      + (overlay === 'off' ? ' · Plain CT' : ' · ' + selectedSamples.toLocaleString() + ' samples in displayed masks');
    get('image-wrap').hidden = false;
  }

  function selectPlane() {
    const axis = layouts[plane.value].normal;
    const centre = nodalLabels.get(Number(get('node').value)).displayIndexXYZ;
    slider.max = shape[axis] - 1;
    slider.value = lastSections[plane.value] ?? centre[axis];
    draw();
  }

  async function start() {
    get('retry').hidden = true;
    get('status').textContent = 'Verifying CT samples and label volume…';
    try {
      const metadata = await fetchBytes('source.json');
      await verify(metadata, document.querySelector('main').dataset.sourceSha256);
      source = JSON.parse(new TextDecoder().decode(metadata));
      if (source.nativeIndexAxes.join(',') !== 'left,anterior,superior') throw Error('Source axes differ.');
      shape = source.shapeSliceRowColumn.toReversed();
      [ct, labels] = await Promise.all([readVolume(source.volumes.ct), readVolume(source.volumes.labels)]);
      nodalLabels = new Map(source.nodalLabels.map(node => [node.label, node]));
      get('node').replaceChildren(...source.nodalLabels.map(node => new Option(node.name, node.label)));
      get('controls').disabled = false;
      selectPlane();
    } catch {
      get('controls').disabled = true;
      get('status').textContent = 'The CT and labels could not be verified.';
      get('retry').hidden = false;
    }
  }

  plane.addEventListener('change', selectPlane);
  get('node').addEventListener('change', () => {
    lastSections = {};
    selectPlane();
  });
  slider.addEventListener('input', () => {
    lastSections[plane.value] = slider.valueAsNumber;
    draw();
  });
  for (const id of ['black', 'white', 'overlay', 'view-size']) get(id).addEventListener('input', draw);
  get('retry').addEventListener('click', start);
  canvas.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'ArrowLeft') slider.stepDown();
    else slider.stepUp();
    slider.dispatchEvent(new Event('input'));
  });
  canvas.addEventListener('click', event => {
    if (!visibleFrame) return;
    const bounds = canvas.getBoundingClientRect();
    const { width, height, index } = visibleFrame;
    const x = Math.floor((event.clientX - bounds.left) * width / bounds.width);
    const y = Math.floor((event.clientY - bounds.top) * height / bounds.height);
    if (x < 0 || y < 0 || x >= width || y >= height) return;
    const sample = index(x, y);
    const label = labels.getInt16(2 * sample, true);
    const node = nodalLabels.get(label);
    get('pixel').textContent = hu(sample) + ' HU'
      + (node ? ' · ' + node.name : label ? ' · Other source label ' + label : '');
  });
  start();
})();
