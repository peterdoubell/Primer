(function (root) {
  'use strict';
  const planeAxes = [[1, 2], [0, 2], [0, 1]];
  const flatIndex = (p, shape) => p[0] + shape[0] * (p[1] + shape[1] * p[2]);
  const world = (p, m) => m.affine.slice(0, 3).map(row => row[3] + row.slice(0, 3).reduce((sum, x, i) => sum + x * p[i], 0));
  const sourceToPixel = (p, axis, m) => {
    const [a, b] = planeAxes[axis];
    return [m.affine[a][a] > 0 ? p[a] + 0.5 : m.shape[a] - p[a] - 0.5,
      m.affine[b][b] > 0 ? m.shape[b] - p[b] - 0.5 : p[b] + 0.5];
  };
  const pixelToSource = (pixel, axis, slice, m) => {
    const [a, b] = planeAxes[axis], p = [0, 0, 0];
    p[axis] = slice;
    p[a] = m.affine[a][a] > 0 ? pixel[0] : m.shape[a] - 1 - pixel[0];
    p[b] = m.affine[b][b] > 0 ? m.shape[b] - 1 - pixel[1] : pixel[1];
    return p;
  };
  function decodeNative(bytes, payload, shape) {
    const count = shape.reduce((a, b) => a * b, 1);
    if (payload.codec === 'native-u8-gzip') {
      if (bytes.byteLength !== count) throw Error('Original label array length mismatch');
      return bytes.slice();
    }
    const output = new Uint8Array(count * 4), view = new DataView(output.buffer);
    if (payload.codec === 'native-f32-row-xor-byte-shuffle-gzip') {
      if (bytes.byteLength !== count * 4) throw Error('Original MRI array length mismatch');
      let previous = 0;
      for (let i = 0; i < count; i++) {
        if (i % shape[0] === 0) previous = 0;
        const difference = (bytes[i] | bytes[count + i] << 8 | bytes[2 * count + i] << 16 | bytes[3 * count + i] << 24) >>> 0;
        previous = (difference ^ previous) >>> 0;
        view.setUint32(i * 4, previous, true);
      }
    } else if (payload.codec === 'native-f32-dictionary-u8-gzip') {
      const n = payload.dictionary_entries;
      if (!Number.isInteger(n) || n < 1 || n > 256 || bytes.byteLength !== n * 4 + count) throw Error('Original probability dictionary length mismatch');
      const dictionary = new DataView(bytes.buffer, bytes.byteOffset, n * 4);
      for (let i = 0; i < count; i++) {
        const code = bytes[n * 4 + i];
        if (code >= n) throw Error('Original probability dictionary code invalid');
        view.setUint32(i * 4, dictionary.getUint32(code * 4, true), true);
      }
    } else throw Error('Unknown native transport');
    return output;
  }
  function decodeMesh(bytes, metadata) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    if (bytes.byteLength < 12 || String.fromCharCode(...bytes.slice(0, 4)) !== 'BP3D') throw Error('Source model format invalid');
    const n = view.getUint32(4, true), indices = view.getUint32(8, true);
    if (n !== metadata.vertices || indices !== metadata.triangles * 3 || bytes.byteLength !== 12 + n * 24 + indices * 4) throw Error('Complete source model length mismatch');
    const positions = new Float32Array(n * 3), faces = new Uint32Array(indices);
    for (let i = 0; i < positions.length; i++) {
      positions[i] = view.getFloat32(12 + i * 4, true);
      if (!Number.isFinite(positions[i])) throw Error('Source model coordinate invalid');
    }
    for (let i = 0; i < indices; i++) {
      faces[i] = view.getUint32(12 + n * 24 + i * 4, true);
      if (faces[i] >= n) throw Error('Source model index invalid');
    }
    return {positions, faces};
  }
  async function decodeMeshResponse(responseBytes, metadata, inflateGzip, sha256) {
    const bytes = responseBytes instanceof Uint8Array ? responseBytes : new Uint8Array(responseBytes);
    const isBP3D = bytes.byteLength >= 4 && bytes[0] === 66 && bytes[1] === 80 && bytes[2] === 51 && bytes[3] === 68;
    let decoded;
    if (isBP3D) {
      // Browsers transparently inflate the existing Content-Encoding:gzip
      // source-model route. This branch requires the original decoded hash
      // and exact BP3D header/length/count checks; it never applies to arrays.
      decoded = bytes;
    } else {
      if (await sha256(bytes) !== metadata.sha256) throw Error('Compressed source model hash mismatch');
      decoded = await inflateGzip(bytes);
    }
    if (await sha256(decoded) !== metadata.decoded_sha256) throw Error('Decoded source model hash mismatch');
    return decodeMesh(decoded, metadata);
  }
  function meshSection(mesh, axis, coordinate) {
    const [a, b] = planeAxes[axis], lines = new Map(), coplanar = new Map();
    function key(p, q) {
      if (p[0] > q[0] || (p[0] === q[0] && p[1] > q[1])) [p, q] = [q, p];
      return p.join(',') + ':' + q.join(',');
    }
    function add(p, q, planar) {
      p = [p[a], p[b]]; q = [q[a], q[b]];
      if (p[0] === q[0] && p[1] === q[1]) return;
      const k = key(p, q);
      if (planar) {
        const item = coplanar.get(k);
        coplanar.set(k, {line: [p, q], count: item ? item.count + 1 : 1});
      } else lines.set(k, [p, q]);
    }
    for (let i = 0; i < mesh.faces.length; i += 3) {
      const points = [0, 1, 2].map(k => Array.from(mesh.positions.subarray(mesh.faces[i + k] * 3, mesh.faces[i + k] * 3 + 3)));
      const delta = points.map(p => p[axis] - coordinate), zeros = delta.filter(x => x === 0).length;
      if (zeros === 3) {
        for (const [u, v] of [[0, 1], [1, 2], [2, 0]]) add(points[u], points[v], true);
      } else if (zeros === 2) {
        const p = points.filter((_, k) => delta[k] === 0); add(p[0], p[1], false);
      } else if (Math.min(...delta) < 0 && Math.max(...delta) > 0) {
        const intersections = [];
        for (const [u, v] of [[0, 1], [1, 2], [2, 0]]) {
          if ((delta[u] <= 0 && delta[v] > 0) || (delta[v] <= 0 && delta[u] > 0)) {
            const fraction = -delta[u] / (delta[v] - delta[u]);
            intersections.push(points[u].map((x, k) => x + fraction * (points[v][k] - x)));
          }
        }
        if (intersections.length !== 2) throw Error('Ambiguous original model intersection');
        add(intersections[0], intersections[1], false);
      }
    }
    for (const [k, item] of coplanar) if (item.count === 1) lines.set(k, item.line);
    return Array.from(lines.values());
  }
  const api = {flatIndex, world, sourceToPixel, pixelToSource, decodeNative, decodeMesh, decodeMeshResponse, meshSection, planeAxes};
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.PrimerBrainFineNative = api;
  if (!root.document) return;
  const $ = id => document.getElementById(id), canvases = [0, 1, 2].map(axis => $('plane-' + axis));
  const arrays = new Map(), promises = new Map(), meshes = new Map(), sectionCache = new Map();
  let manifest, cursor = [0, 0, 0], image = null, loadVersion = 0, meshReady = false, commonReady = false;
  const digest = async raw => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', raw)), x => x.toString(16).padStart(2, '0')).join('');
  const inflateGzip = async bytes => new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
  async function load(payload, isMesh = false) {
    if (arrays.has(payload.file)) return arrays.get(payload.file);
    if (promises.has(payload.file)) return promises.get(payload.file);
    const promise = (async () => {
      const response = await fetch(payload.file);
      if (!response.ok) throw Error('Source asset HTTP ' + response.status);
      const body = await response.arrayBuffer();
      let result;
      if (isMesh) result = await decodeMeshResponse(body, payload, inflateGzip, digest);
      else {
        if (await digest(body) !== payload.sha256) throw Error('Compressed source hash mismatch');
        const inflated = await inflateGzip(body), decoded = decodeNative(inflated, payload, manifest.shape);
        if (await digest(decoded) !== payload.decoded_sha256) throw Error('Decoded original sample/model hash mismatch');
        result = payload.codec === 'native-u8-gzip' ? decoded : new DataView(decoded.buffer);
      }
      arrays.set(payload.file, result);
      return result;
    })();
    promises.set(payload.file, promise);
    try { return await promise; } finally { promises.delete(payload.file); }
  }
  function labelName(label) {
    const row = manifest.source_labels[label];
    return row ? row.name + (row.hemisphere === 'l' ? ' (left)' : row.hemisphere === 'r' ? ' (right)' : '') : 'Unknown original label ' + label;
  }
  function selectedTargets() {
    return manifest.targets.filter(x => $('structure').value === 'all' || String(x.label) === $('structure').value);
  }
  function blankPresentation(message) {
    for (const canvas of canvases) {
      canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
      canvas.dataset.ready = 'false';
      delete canvas.dataset.sourceSlice;
      delete canvas.dataset.modelSegments;
    }
    $('values').textContent = '';
    $('position').textContent = '';
    $('status').textContent = message;
  }
  function clearViews(message) { image = null; blankPresentation(message); }
  function readout() {
    if (!image) return;
    const i = flatIndex(cursor, manifest.shape), labels = arrays.get(manifest.labels.file), ras = world(cursor, manifest);
    const source = cursor.map((x, a) => x + manifest.native_roi_start[a]);
    $('position').textContent = 'Original source voxel [' + source.join(', ') + '] · RAS [' + ras.map(x => x.toFixed(2)).join(', ') + '] mm';
    $('values').replaceChildren();
    for (const text of ['MRI source value: ' + image.getFloat32(i * 4, true).toPrecision(8) + ' (source units)',
      'Original best-label ID ' + labels[i] + ': ' + labelName(labels[i]), ...Object.values(manifest.probabilities).map(p =>
        labelName(p.label) + ' probability: ' + arrays.get(p.file).getFloat32(i * 4, true).toPrecision(6))]) {
      const item = document.createElement('li'); item.textContent = text; $('values').append(item);
    }
  }
  function sectionFor(target, axis, coordinate) {
    const key = target.id + ':' + axis + ':' + coordinate;
    if (!sectionCache.has(key)) sectionCache.set(key, meshSection(meshes.get(target.id), axis, coordinate));
    return sectionCache.get(key);
  }
  function draw() {
    if (!image || !manifest) return;
    const low = Number($('low').value), high = Number($('high').value);
    if ($('low').value.trim() === '' || $('high').value.trim() === '' || !Number.isFinite(low) || !Number.isFinite(high) || high <= low) { blankPresentation('Set two finite display limits with maximum greater than minimum.'); return; }
    const targets = selectedTargets(), colors = new Map(targets.map(t => [t.label, t.color.match(/[a-f0-9]{2}/gi).map(x => parseInt(x, 16))]));
    const labels = arrays.get(manifest.labels.file), overlay = $('overlay').value;
    for (let axis = 0; axis < 3; axis++) {
      const canvas = canvases[axis], [a, b] = planeAxes[axis], w = manifest.shape[a], h = manifest.shape[b], ctx = canvas.getContext('2d');
      canvas.width = w; canvas.height = h;
      const pixels = ctx.createImageData(w, h);
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const p = pixelToSource([x, y], axis, cursor[axis], manifest), i = flatIndex(p, manifest.shape);
        const value = image.getFloat32(i * 4, true), gray = Math.max(0, Math.min(255, Math.round(255 * (value - low) / (high - low)))), offset = 4 * (x + w * y);
        let color = colors.get(labels[i]), opacity = 0.25;
        if (overlay === 'probability') {
          let maximum = -1;
          for (const target of targets) {
            const probability = arrays.get(manifest.probabilities[target.label].file).getFloat32(i * 4, true);
            if (probability > maximum) { maximum = probability; color = colors.get(target.label); }
          }
          opacity = 0.65 * Math.max(0, maximum);
        }
        for (let channel = 0; channel < 3; channel++) pixels.data[offset + channel] = (overlay === 'labels' || overlay === 'probability') && color ? Math.round(gray * (1 - opacity) + color[channel] * opacity) : gray;
        pixels.data[offset + 3] = 255;
      }
      ctx.putImageData(pixels, 0, 0);
      let segments = 0;
      if (overlay === 'mesh' && meshReady) {
        const coordinate = world(cursor, manifest)[axis];
        for (const target of targets) {
          ctx.strokeStyle = target.color; ctx.lineWidth = 0.45; ctx.beginPath();
          const lines = sectionFor(target, axis, coordinate); segments += lines.length;
          for (const line of lines) {
            const points = line.map(point => {
              const p = cursor.slice();
              p[a] = (point[0] - manifest.affine[a][3]) / manifest.affine[a][a];
              p[b] = (point[1] - manifest.affine[b][3]) / manifest.affine[b][b];
              return sourceToPixel(p, axis, manifest);
            });
            ctx.moveTo(...points[0]); ctx.lineTo(...points[1]);
          }
          ctx.stroke();
        }
      }
      if ($('crosshair').checked) {
        const [x, y] = sourceToPixel(cursor, axis, manifest);
        ctx.strokeStyle = '#65d7ff'; ctx.lineWidth = 0.25; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
      }
      canvas.dataset.ready = 'true'; canvas.dataset.sourceSlice = cursor[axis] + manifest.native_roi_start[axis];
      canvas.dataset.modelSegments = segments; canvas.dataset.axis = axis;
      canvas.setAttribute('aria-label', ['Sagittal', 'Coronal', 'Axial'][axis] + ' native source section; click or use arrow keys to set linked crosshairs. Page Up and Page Down change this section.');
      $('slice-' + axis).value = cursor[axis]; $('number-' + axis).value = cursor[axis] + manifest.native_roi_start[axis];
      $('plane-position-' + axis).textContent = 'RAS ' + 'XYZ'[axis] + '=' + world(cursor, manifest)[axis].toFixed(2) + ' mm';
    }
    $('status').textContent = $('statistic').value === 'iqr' ? 'MRI interquartile range · source intersubject intensity spread' : 'MRI population median · source group reference';
    readout();
  }
  function setCursor(next) {
    cursor = next.map((x, a) => Math.min(manifest.shape[a] - 1, Math.max(0, Math.round(x)))); draw();
  }
  async function changeImage() {
    if (!manifest) return;
    const version = ++loadVersion, key = $('statistic').value + '-' + $('contrast').value, payload = manifest.contrasts[key];
    clearViews('Loading and checking unchanged native ' + key + ' samples…');
    try {
      const loaded = await load(payload);
      if (version !== loadVersion) return;
      image = loaded; $('low').value = payload.display_window[0].toPrecision(8); $('high').value = payload.display_window[1].toPrecision(8); draw();
    } catch (error) { if (version === loadVersion) clearViews('Native source could not load: ' + error.message); }
  }
  async function initialize() {
    try {
      const response = await fetch('/app/anatomy/brain-fine-massp2/manifest.json');
      if (!response.ok) throw Error('Source manifest HTTP ' + response.status);
      manifest = await response.json();
      if (manifest.shape.length !== 3 || manifest.shape.some(x => !Number.isInteger(x) || x < 1) || manifest.shape.reduce((a, b) => a * b, 1) > 2000000 || manifest.targets.length !== 6) throw Error('Unexpected scoped source grid');
      for (const target of manifest.targets) {
        const option = document.createElement('option'); option.value = target.label; option.textContent = target.name; $('structure').append(option);
        const legend = document.createElement('span'); legend.textContent = target.name; legend.style.borderColor = target.color; $('legend').append(legend);
      }
      for (let axis = 0; axis < 3; axis++) {
        $('slice-' + axis).max = manifest.shape[axis] - 1;
        $('number-' + axis).min = manifest.native_roi_start[axis]; $('number-' + axis).max = manifest.native_roi_stop_exclusive[axis] - 1;
      }
      cursor = manifest.targets.find(t => t.label === 11).center_indices.slice();
      await Promise.all([load(manifest.labels), ...Object.values(manifest.probabilities).map(p => load(p))]);
      commonReady = true;
      for (const control of document.querySelectorAll('[data-source-control]')) control.disabled = false;
      await changeImage();
      await loadMeshes();
      draw();
      root.PrimerBrainFineNative.state = () => ({cursor: cursor.slice(), sourceVoxel: cursor.map((x, a) => x + manifest.native_roi_start[a]), key: $('statistic').value + '-' + $('contrast').value, ready: !!image && canvases.every(c => c.dataset.ready === 'true'), meshReady});
    } catch (error) { clearViews('Native source could not load: ' + error.message); }
  }
  async function loadMeshes() {
    try {
      await Promise.all(manifest.targets.map(async target => meshes.set(target.id, await load(target.mesh, true))));
      meshReady = true; $('mesh-option').disabled = false;
      $('mesh-status').textContent = 'All six complete source joint meshes checked; every original triangle retained.';
    } catch (error) { $('mesh-status').textContent = 'Direct source model sections unavailable: ' + error.message; }
  }
  $('contrast').addEventListener('change', changeImage); $('statistic').addEventListener('change', changeImage);
  $('structure').addEventListener('change', () => {
    const target = manifest.targets.find(t => String(t.label) === $('structure').value);
    if (target) setCursor(target.center_indices); else draw();
  });
  for (const id of ['overlay', 'crosshair', 'low', 'high']) $(id).addEventListener('change', draw);
  $('window-reset').addEventListener('click', () => { const p = manifest.contrasts[$('statistic').value + '-' + $('contrast').value]; $('low').value = p.display_window[0].toPrecision(8); $('high').value = p.display_window[1].toPrecision(8); draw(); });
  $('retry').addEventListener('click', () => {
    if (!commonReady) { location.reload(); return; }
    changeImage();
    if (!meshReady) loadMeshes().then(draw);
  });
  for (let axis = 0; axis < 3; axis++) {
    $('slice-' + axis).addEventListener('input', event => { const p = cursor.slice(); p[axis] = Number(event.target.value); setCursor(p); });
    $('number-' + axis).addEventListener('change', event => {
      if (event.target.value.trim() === '' || !Number.isFinite(Number(event.target.value))) { draw(); return; }
      const p = cursor.slice(); p[axis] = Number(event.target.value) - manifest.native_roi_start[axis]; setCursor(p);
    });
    const canvas = canvases[axis];
    canvas.addEventListener('pointerdown', event => {
      if (!image) return;
      const rect = canvas.getBoundingClientRect(), [a, b] = planeAxes[axis];
      const pixel = [Math.min(manifest.shape[a] - 1, Math.max(0, Math.floor((event.clientX - rect.left) / rect.width * manifest.shape[a]))),
        Math.min(manifest.shape[b] - 1, Math.max(0, Math.floor((event.clientY - rect.top) / rect.height * manifest.shape[b])))];
      setCursor(pixelToSource(pixel, axis, cursor[axis], manifest)); canvas.focus();
    });
    canvas.addEventListener('keydown', event => {
      if (!image) return;
      const [a, b] = planeAxes[axis], p = cursor.slice(), step = event.shiftKey ? 5 : 1;
      if (event.key === 'ArrowLeft') p[a] -= Math.sign(manifest.affine[a][a]) * step;
      else if (event.key === 'ArrowRight') p[a] += Math.sign(manifest.affine[a][a]) * step;
      else if (event.key === 'ArrowUp') p[b] += Math.sign(manifest.affine[b][b]) * step;
      else if (event.key === 'ArrowDown') p[b] -= Math.sign(manifest.affine[b][b]) * step;
      else if (event.key === 'PageUp') p[axis] += step;
      else if (event.key === 'PageDown') p[axis] -= step;
      else return;
      event.preventDefault(); setCursor(p);
    });
  }
  initialize();
})(typeof window !== 'undefined' ? window : globalThis);
