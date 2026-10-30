'use strict';
(async function () {
  const $ = id => document.getElementById(id), C = window.SPLNativeCoordinates;
  const canvas = $('mri'), ctx = canvas.getContext('2d', {willReadFrequently: true});
  const unmarked=$('mri-unmarked'),unmarkedContext=unmarked.getContext('2d');
  function hideComparison(){unmarked.hidden=true;unmarked.dataset.ready='false';delete unmarked.dataset.state;$('unmarked-panel').hidden=true;}
  const surface = $('mesh'), gl = surface.getContext('webgl2', {antialias: true, preserveDrawingBuffer: true});
  const sha = async bytes => [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(value => value.toString(16).padStart(2, '0')).join('');
  const payload = row => window.SPLSourcePayload.fetchPayload(row);
  let manifest, imageRow, image, labelData, labelPromise, labelInverse, spec, loadID = 0, meshID = 0;
  let program, visible = [], azimuth = Math.PI/2, elevation = .2, zoom = 1, drag, renderState;
  const meshCache = new Map(), pendingMeshes = new Map(), focusPoints = new Map();
  const controls = [...document.querySelectorAll('select,input,button')].filter(control => control.id !== 'retry');
  const enable = value => controls.forEach(control => {control.disabled = !value;});
  const selected = () => Number($('structure').value);
  const labelFor = code => manifest.labels.find(row => row.code === code);
  function validateManifest(value) {
    const rowOK = row => row && /^[A-Za-z0-9_.-]+$/.test(row.file) && Number.isSafeInteger(row.byteLength) && row.byteLength > 0 &&
      /^[a-f0-9]{64}$/.test(row.gzipSHA256) && /^[a-f0-9]{64}$/.test(row.decodedSHA256);
    if (!value || value.schemaVersion !== 1 || value.sourceCommit !== 'bec24db25aad5f7600e2df3becfb1f883e61ff56' ||
        value.sourceCoordinateSystem !== 'RAS' || value.sourceCoordinateUnits !== 'mm' ||
        ['clinicalApproval', 'completeReportingAnatomyApproved', 'normalPopulationAtlas', 'currentPatientRegistration', 'newFittedTransforms'].some(key => value[key] !== false) ||
        Object.keys(value.volumes || {}).sort().join(',') !== 'T1,T2' || !rowOK(value.labelVolume) ||
        !Array.isArray(value.labels) || value.labels.length !== 12 || new Set(value.labels.map(row => row.code)).size !== 12 ||
        !Array.isArray(value.meshes) || value.meshes.length !== 12 || !Array.isArray(value.labelMeshes) || value.labelMeshes.length !== 12) throw Error('Source manifest scope differs');
    for (const row of [value.labelVolume, ...Object.values(value.volumes)]) {
      if (!rowOK(row)) throw Error('Invalid source payload descriptor');
      C.shapeOf(row); C.validateAffine(row.voxelToRAS); C.inverse(row.voxelToRAS);
      const bytes = row.shape.reduce((a, b) => a*b) * (row === value.labelVolume ? 2 : 4);
      if (row.byteLength !== bytes || row.dtype !== (row === value.labelVolume ? '<i2' : '<f4') || row.storageOrder !== 'F') throw Error('Native sample type, order or length differs');
    }
    for (const row of value.labels) {
      if (!Number.isInteger(row.code) || row.code <= 0 || typeof row.name !== 'string' || !row.name ||
          !Array.isArray(row.color) || row.color.length !== 3 || !row.color.every(v => Number.isInteger(v) && v >= 0 && v <= 255)) throw Error('Invalid source label');
      for (const group of [value.meshes, value.labelMeshes]) {
        const meshes = group.filter(mesh => mesh.code === row.code);
        if (meshes.length !== 1 || !rowOK(meshes[0])) throw Error('Source surface inventory differs');
        if (meshes[0].coordinateSystem !== 'RAS' || meshes[0].positionsAlreadyRAS !== true || meshes[0].spaceUnits !== 'mm' ||
            JSON.stringify(meshes[0].sourceAffine) !== JSON.stringify([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])) throw Error('Source model coordinate convention differs');
      }
    }
    return value;
  }
  async function labels() {
    if (labelData) return labelData;
    if (!labelPromise) labelPromise = payload(manifest.labelVolume).then(raw => {
      labelData = new Int16Array(raw); labelInverse = C.inverse(manifest.labelVolume.voxelToRAS); return labelData;
    }).catch(error => {labelPromise = null; throw error;});
    return labelPromise;
  }
  function defaultWindow() {
    if (Array.isArray(imageRow.defaultWindow) && imageRow.defaultWindow.length === 2 &&
        imageRow.defaultWindow.every(Number.isFinite) && imageRow.defaultWindow[1] > imageRow.defaultWindow[0]) {
      return {center: (imageRow.defaultWindow[0]+imageRow.defaultWindow[1])/2, width: imageRow.defaultWindow[1]-imageRow.defaultWindow[0]};
    }
    const preset = imageRow.displayWindow;
    if (preset && Number.isFinite(preset.center) && Number.isFinite(preset.width) && preset.width > 0) return preset;
    let low = Infinity, high = -Infinity;
    for (const value of image) if (Number.isFinite(value)) {low = Math.min(low, value); high = Math.max(high, value);}
    if (!Number.isFinite(low) || !(high > low)) throw Error('MRI has no finite display range');
    return {center: (low + high)/2, width: high - low};
  }
  function resetWindow() {
    if (!image) return;
    const window = defaultWindow(); $('centre').value = String(window.center); $('width').value = String(window.width); drawMRI();
  }
  function planeChanged() {
    if (!image) return;
    const first = C.planeSpec(imageRow, $('plane').value, 0), maximum = imageRow.shape[first.fixed] - 1;
    $('slice').max = String(maximum); $('slice').value = String(Math.min(maximum, Number($('slice').value)));
    drawMRI();
  }
  function drawMRI() {
    if (!image || !labelData) return;
    delete canvas.dataset.cursor;
    $('cursor').textContent = 'Move over the image to inspect the original MRI sample, source RAS coordinates and nearest label voxel.';
    const center = Number($('centre').value), width = Number($('width').value);
    if ($('centre').value === '' || $('width').value === '' || !Number.isFinite(center) || !Number.isFinite(width) || width <= 0) {
      canvas.hidden = true; canvas.dataset.ready = 'false'; hideComparison(); delete canvas.dataset.state;
      $('status').textContent = 'Enter a finite display centre and positive width.';
      $('cursor').textContent = 'Choose a valid display window before inspecting a source sample.'; return;
    }
    spec = C.planeSpec(imageRow, $('plane').value, Number($('slice').value));
    canvas.width = spec.width; canvas.height = spec.height;
    canvas.style.setProperty('--physical-ratio', String(spec.width*spec.spacing[0]/(spec.height*spec.spacing[1])));
    const rgba = new Uint8ClampedArray(spec.width*spec.height*4), plain=new Uint8ClampedArray(spec.width*spec.height*4), palette = new Map(manifest.labels.map(row => [row.code, row.color]));
    const overlay = $('overlay').value, code = selected(), low = center-width/2;
    for (let y = 0; y < spec.height; y++) for (let x = 0; x < spec.width; x++) {
      const voxel = C.pixelVoxel(spec, x, y), value = image[C.offset(imageRow.shape, voxel)];
      const world = C.transform(imageRow.voxelToRAS, voxel), labelVoxel = C.nearestVoxel(labelInverse, world, manifest.labelVolume.shape);
      const label = labelVoxel ? labelData[C.offset(manifest.labelVolume.shape, labelVoxel)] : null;
      const color = palette.get(label), grey = Number.isFinite(value) ? Math.max(0, Math.min(255, Math.floor(255*(value-low)/width))) : 0;
      const tint = color && (overlay === 'all' || overlay === 'selected' && label === code), offset = 4*(x+spec.width*y);
      for (let channel = 0; channel < 3; channel++) rgba[offset+channel] = tint ? Math.round(.55*grey+.45*color[channel]) : grey;
      rgba[offset+3] = 255;plain[offset]=plain[offset+1]=plain[offset+2]=grey;plain[offset+3]=255;
    }
    ctx.putImageData(new ImageData(rgba, spec.width, spec.height), 0, 0);
    canvas.hidden = false; canvas.dataset.ready = 'true';
    canvas.dataset.state = JSON.stringify({contrast: $('contrast').value, plane: spec.plane, slice: spec.slice, center, width, overlay, label: code, spec});
    const compare=$('compare-unmarked').checked;$('mri-pair').classList.toggle('paired',compare);
    if(compare){unmarked.width=spec.width;unmarked.height=spec.height;unmarked.style.setProperty('--physical-ratio',canvas.style.getPropertyValue('--physical-ratio'));unmarkedContext.putImageData(new ImageData(plain,spec.width,spec.height),0,0);unmarked.hidden=false;unmarked.dataset.ready='true';unmarked.dataset.state=JSON.stringify({...JSON.parse(canvas.dataset.state),overlay:'off'});$('unmarked-panel').hidden=false;}else hideComparison();
    const middle = C.pixelVoxel(spec, Math.floor(spec.width/2), Math.floor(spec.height/2));
    const world = C.transform(imageRow.voxelToRAS, middle), coordinate = {axial: 2, coronal: 1, sagittal: 0}[spec.plane];
    $('slice-value').textContent = spec.slice + ' / ' + (imageRow.shape[spec.fixed]-1);
    const [left, right, top, bottom] = spec.edgeLabels;
    $('orientation').textContent = 'Left → right: ' + left + ' → ' + right + ' · top → bottom: ' + top + ' → ' + bottom +
      ' · source RAS ' + ['x', 'y', 'z'][coordinate] + ' = ' + world[coordinate].toFixed(3) + ' mm';
    $('status').textContent = $('contrast').value + ' · native ' + imageRow.shape.join(' × ') + ' samples · ' +
      spec.spacing.join(' × ') + ' mm pixel spacing · original scalar values; display window only';
  }
  function point(event) {
    if (!image || canvas.hidden || !spec) return;
    const box = canvas.getBoundingClientRect(), style = getComputedStyle(canvas);
    const px = name => Number.parseFloat(style[name]) || 0;
    const left = px('borderLeftWidth')+px('paddingLeft'), right = px('borderRightWidth')+px('paddingRight');
    const top = px('borderTopWidth')+px('paddingTop'), bottom = px('borderBottomWidth')+px('paddingBottom');
    const contentWidth = box.width-left-right, contentHeight = box.height-top-bottom;
    if (!(contentWidth > 0 && contentHeight > 0)) return;
    const x = Math.min(spec.width-1, Math.max(0, Math.floor((event.clientX-box.left-left)*spec.width/contentWidth)));
    const y = Math.min(spec.height-1, Math.max(0, Math.floor((event.clientY-box.top-top)*spec.height/contentHeight)));
    const probe = C.probe(imageRow, image, manifest.labelVolume, labelData, C.pixelVoxel(spec, x, y));
    const name = probe.label === null ? 'outside label grid' : labelFor(probe.label)?.name || 'other original label';
    $('cursor').textContent = 'MRI (i,j,k) ' + probe.voxel.join(', ') + ' · stored value ' + probe.value +
      ' · RAS mm (' + probe.ras.map(value => value.toFixed(3)).join(', ') + ') · nearest label voxel ' +
      (probe.labelVoxel ? probe.labelVoxel.join(', ') : 'none') + ' · label ' + probe.label + ': ' + name;
    canvas.dataset.cursor = JSON.stringify(probe);
  }
  function focusStructure() {
    if (!image || !labelData) return;
    const code = selected(), row = labelFor(code), shape = manifest.labelVolume.shape;
    $('fornix-outlier').hidden = code !== 3007;
    if (!focusPoints.has(code)) {
      let count = 0, sum = [0, 0, 0];
      for (let index = 0; index < labelData.length; index++) if (labelData[index] === code) {
        const p = [index % shape[0], Math.floor(index/shape[0]) % shape[1], Math.floor(index/(shape[0]*shape[1]))];
        count++; for (let axis = 0; axis < 3; axis++) sum[axis] += p[axis];
      }
      if (!count) throw Error('Selected original label is empty');
      const center = sum.map(value => value/count); let best = Infinity, point;
      for (let index = 0; index < labelData.length; index++) if (labelData[index] === code) {
        const p = [index % shape[0], Math.floor(index/shape[0]) % shape[1], Math.floor(index/(shape[0]*shape[1]))];
        const distance = p.reduce((total, value, axis) => total+(value-center[axis])**2, 0);
        if (distance < best) {best = distance; point = p;}
      }
      focusPoints.set(code, {voxel: point, ras: C.transform(manifest.labelVolume.voxelToRAS, point), count});
    }
    const focus = focusPoints.get(code), native = C.nearestVoxel(C.inverse(imageRow.voxelToRAS), focus.ras, imageRow.shape);
    if (!native) {$('status').textContent = 'This label focus lies outside the original MRI field of view.'; return;}
    const target = C.planeSpec(imageRow, $('plane').value, 0);
    $('slice').value = String(native[target.fixed]); planeChanged();
    $('source-note').textContent = row.name + ' · original label ' + code + ' · ' + focus.count.toLocaleString() +
      ' source label voxels. Find structure in MRI selects an original label sample near its centroid; this is not a normative volume measurement.';
    if (code === 3007) $('source-note').textContent += ' The left-fornix label includes a retained isolated voxel at RAS (−2, −39, −4) mm whose continuity with the tract is unvalidated. Its exposed face centres reach 12.24 mm from the publisher surface; this sampled distance is not a continuous Hausdorff bound. Use “Inspect retained fornix outlier” to locate it.';
    if (code === 3005) $('source-note').textContent += ' Some original right-fornix surface vertices lie up to 7.17 mm from the categorical label boundary. The two representations are not interchangeable anatomical ground truth.';
  }
  function inspectFornixOutlier() {
    if (!image || !labelData || selected() !== 3007) return;
    const ras = [-2, -39, -4], labelVoxel = C.nearestVoxel(labelInverse, ras, manifest.labelVolume.shape);
    if (!labelVoxel || labelData[C.offset(manifest.labelVolume.shape, labelVoxel)] !== 3007) throw Error('Reviewed fornix outlier no longer matches the original source');
    const voxel = C.nearestVoxel(C.inverse(imageRow.voxelToRAS), ras, imageRow.shape);
    if (!voxel) throw Error('Reviewed fornix outlier leaves the native MRI field');
    const plane = C.planeSpec(imageRow, $('plane').value, 0);
    $('slice').value = String(voxel[plane.fixed]); planeChanged();
    const probe = C.probe(imageRow, image, manifest.labelVolume, labelData, voxel);
    canvas.dataset.cursor = JSON.stringify(probe);
    $('cursor').textContent = 'Retained isolated left-fornix source label at RAS (−2, −39, −4) mm. Nearest native MRI voxel (' +
      voxel.join(', ') + ') has value ' + probe.value + ' and nearest label ' + probe.label + '. The source label is preserved; biological tract continuity is not established.';
  }
  function shader(type, source) {
    const result = gl.createShader(type); gl.shaderSource(result, source); gl.compileShader(result);
    if (!gl.getShaderParameter(result, gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(result)); return result;
  }
  function initGL() {
    if (!gl) throw Error('WebGL2 unavailable; the native MRI and labels remain available.');
    program = gl.createProgram();
    gl.attachShader(program, shader(gl.VERTEX_SHADER, `#version 300 es
precision highp float;
in vec3 position; uniform vec3 center,right,up,forward; uniform float scale,distance,aspect; out vec3 worldPosition;
void main(){worldPosition=position;vec3 p=(position-center)*scale;float z=distance-dot(p,forward);gl_Position=vec4(2.0*dot(p,right)/aspect,2.0*dot(p,up),1.002002*z-.2002002,z);}`));
    gl.attachShader(program, shader(gl.FRAGMENT_SHADER, `#version 300 es
precision highp float;in vec3 worldPosition;uniform vec3 tint;out vec4 color;
void main(){vec3 n=normalize(cross(dFdx(worldPosition),dFdy(worldPosition)));float light=.25+.75*abs(dot(n,normalize(vec3(.3,.5,1.0))));color=vec4(tint*light,1.0);}`));
    gl.transformFeedbackVaryings(program, ['worldPosition'], gl.INTERLEAVED_ATTRIBS); gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error(gl.getProgramInfoLog(program));
  }
  async function loadMesh(row) {
    if (meshCache.has(row.file)) return meshCache.get(row.file);
    if (pendingMeshes.has(row.file)) return pendingMeshes.get(row.file);
    const job = (async () => {
      const raw = await payload(row), header = new DataView(raw);
      if (new TextDecoder().decode(raw.slice(0, 4)) !== 'HVX1' || header.getUint32(4, true) !== row.vertexCount ||
          header.getUint32(8, true) !== row.triangleCount || header.getUint32(12, true) !== 0 ||
          raw.byteLength !== 16+12*row.vertexCount+12*row.triangleCount) throw Error('Original surface transport differs');
      const positions = new Float32Array(raw, 16, row.vertexCount*3), indices = new Uint32Array(raw, 16+row.vertexCount*12, row.triangleCount*3);
      if (await sha(positions.buffer.slice(positions.byteOffset, positions.byteOffset+positions.byteLength)) !== row.positionByteSHA256 ||
          await sha(indices.buffer.slice(indices.byteOffset, indices.byteOffset+indices.byteLength)) !== row.indexByteSHA256) throw Error('Original surface array identity differs');
      if (indices.some(index => index >= row.vertexCount) || positions.some(value => !Number.isFinite(value))) throw Error('Invalid original surface geometry');
      const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
      const positionBuffer = gl.createBuffer(), indexBuffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer); gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
      const location = gl.getAttribLocation(program, 'position'); gl.enableVertexAttribArray(location); gl.vertexAttribPointer(location, 3, gl.FLOAT, false, 0, 0);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);
      const bounds = [[Infinity, Infinity, Infinity], [-Infinity, -Infinity, -Infinity]];
      for (let i = 0; i < positions.length; i++) {const axis = i % 3; bounds[0][axis] = Math.min(bounds[0][axis], positions[i]); bounds[1][axis] = Math.max(bounds[1][axis], positions[i]);}
      const result = {row, vao, positionBuffer, indexBuffer, bounds}; meshCache.set(row.file, result); return result;
    })();
    pendingMeshes.set(row.file, job); try {return await job;} finally {pendingMeshes.delete(row.file);}
  }
  function draw3D() {
    if (!visible.length || surface.hidden || !program) return;
    const ratio = Math.min(devicePixelRatio, 2), width = Math.max(1, Math.round(surface.clientWidth*ratio)), height = Math.max(1, Math.round(surface.clientHeight*ratio));
    surface.width = width; surface.height = height; gl.viewport(0, 0, width, height); gl.clearColor(.03, .05, .08, 1); gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.useProgram(program); gl.enable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE);
    const low = [0, 1, 2].map(axis => Math.min(...visible.map(mesh => mesh.bounds[0][axis])));
    const high = [0, 1, 2].map(axis => Math.max(...visible.map(mesh => mesh.bounds[1][axis])));
    const center = low.map((value, axis) => (value+high[axis])/2), scale = 2/Math.max(...low.map((value, axis) => high[axis]-value));
    const radius = Math.hypot(...low.map((value, axis) => (high[axis]-value)*scale/2)), aspect = width/height;
    const distance = radius*Math.sqrt(1+(2/(.9*Math.min(aspect, 1)))**2)*zoom;
    const forward = [Math.cos(elevation)*Math.cos(azimuth), Math.cos(elevation)*Math.sin(azimuth), Math.sin(elevation)];
    const right = [-Math.sin(azimuth), Math.cos(azimuth), 0];
    const up = [-Math.sin(elevation)*Math.cos(azimuth), -Math.sin(elevation)*Math.sin(azimuth), Math.cos(elevation)];
    for (const [key, value] of Object.entries({center, right, up, forward})) gl.uniform3fv(gl.getUniformLocation(program, key), value);
    for (const [key, value] of Object.entries({scale, distance, aspect})) gl.uniform1f(gl.getUniformLocation(program, key), value);
    for (const mesh of visible) {
      gl.bindVertexArray(mesh.vao); gl.uniform3fv(gl.getUniformLocation(program, 'tint'), labelFor(mesh.row.code).color.map(value => value/255));
      gl.drawElements(gl.TRIANGLES, mesh.row.triangleCount*3, gl.UNSIGNED_INT, 0);
    }
    if (gl.getError() !== gl.NO_ERROR) throw Error('WebGL source surface draw failed');
    renderState = {center, scale, radius, aspect, distance, azimuth, elevation, zoom, right, up, forward};
    surface.dataset.ready = 'true'; surface.dataset.parts = visible.map(mesh => mesh.row.code).join(',');
    const labelBoundaries = $('surface-kind').value === 'label';
    $('mesh-status').textContent = visible.length + (labelBoundaries ? ' source-label cell boundaries · ' : ' publisher surfaces · ') +
      visible.reduce((sum, mesh) => sum+mesh.row.triangleCount, 0).toLocaleString() + ' triangles · source RAS millimetres; camera fitted to visible structures';
    $('surface-note').textContent = labelBoundaries ? 'Every exposed cell face of each selected source label is retained, including small components and cavities. The block-like surface reflects the 1 mm categorical grid; it is not a smoother anatomical contour.' :
      'These are the producer’s original processed surfaces, not boundaries extracted from the displayed labels. The fornix objects differ substantially from the label map. Compare representations without treating agreement or disagreement as a patient finding.';
  }
  async function chooseMeshes() {
    if (!manifest || !program) return;
    const id = ++meshID; surface.hidden = true; surface.dataset.ready = 'false'; delete surface.dataset.error;
    $('retry-3d').hidden = true;
    $('mesh-status').textContent = 'Loading original source surfaces…';
    try {
      const group = $('surface-kind').value === 'label' ? manifest.labelMeshes : manifest.meshes;
      const rows = group.filter(row => $('surface-scope').value === 'all' || row.code === selected());
      const meshes = await Promise.all(rows.map(loadMesh)); if (id !== meshID) return;
      visible = meshes; surface.hidden = false; draw3D();
    } catch (error) {if (id === meshID) {surface.dataset.error = error.message; $('mesh-status').textContent = error.message; $('retry-3d').hidden = false;}}
  }
  async function loadSource() {
    if (!manifest) return;
    const id = ++loadID; image = null; imageRow = null; canvas.hidden = true; canvas.dataset.ready = 'false'; hideComparison();
    delete canvas.dataset.cursor; delete canvas.dataset.state; $('retry').hidden = true; $('cursor').textContent = 'Loading original source samples…';
    $('status').textContent = 'Loading and checking native ' + $('contrast').value + ' MRI and source labels…';
    try {
      const row = manifest.volumes[$('contrast').value], [raw] = await Promise.all([payload(row), labels()]);
      if (id !== loadID) return;
      imageRow = row; image = new Float32Array(raw); resetWindow(); planeChanged(); focusStructure();
      $('cursor').textContent = 'Move over the image to inspect the original MRI sample, source RAS coordinates and nearest label voxel.';
    } catch (error) {if (id === loadID) {$('status').textContent = error.message; $('cursor').textContent = 'No source sample is available until the load succeeds.'; $('retry').hidden = false;}}
  }
  function enlarge(button, view) {
    button.onclick = () => {
      const on = view.closest('section').classList.toggle('enlarged'); button.setAttribute('aria-pressed', String(on));
      button.textContent = on ? 'Close enlargement' : view === canvas ? 'Enlarge image' : 'Enlarge 3D'; draw3D();
    };
  }
  async function loadManifest() {
    enable(false); $('retry').hidden = true;
    try {
      const response = await fetch('manifest.json'); if (!response.ok) throw Error('Source metadata request failed: ' + response.status);
      manifest = validateManifest(await response.json()); $('structure').replaceChildren(); $('legend').replaceChildren();
      for (const row of manifest.labels) {
        $('structure').add(new Option(row.name + ' · ' + row.code, String(row.code)));
        const label = document.createElement('span'), swatch = document.createElement('i'); swatch.className = 'swatch'; swatch.style.background = 'rgb(' + row.color.join(',') + ')';
        label.append(swatch, document.createTextNode(row.name)); $('legend').append(label);
      }
      try {initGL();} catch (error) {$('mesh-status').textContent = error.message;}
      enable(true); chooseMeshes(); await loadSource();
    } catch (error) {manifest = null; $('status').textContent = error.message; $('retry').hidden = false;}
  }
  $('contrast').onchange = loadSource; $('retry').onclick = () => manifest ? loadSource() : loadManifest();
  $('compare-unmarked').onchange=drawMRI;
  $('structure').onchange = () => {focusStructure(); drawMRI(); chooseMeshes();}; $('focus').onclick = focusStructure;
  $('fornix-outlier').onclick = inspectFornixOutlier;
  $('plane').onchange = () => {planeChanged(); focusStructure();};
  for (const id of ['slice', 'centre', 'width', 'overlay']) $(id).oninput = drawMRI;
  $('reset-window').onclick = resetWindow; $('surface-scope').onchange = chooseMeshes;
  $('surface-kind').onchange = chooseMeshes;
  $('retry-3d').onclick = chooseMeshes;
  canvas.onpointermove = point; canvas.onpointerdown = point;
  canvas.onkeydown = event => {if (['ArrowUp', 'ArrowDown'].includes(event.key)) {
    event.preventDefault(); $('slice').value = String(Math.min(Number($('slice').max), Math.max(0, Number($('slice').value)+(event.key === 'ArrowUp' ? 1 : -1)))); drawMRI();
  }};
  function camera(az, el) {azimuth = az; elevation = el; zoom = 1; draw3D();}
  $('anterior').onclick = () => camera(Math.PI/2, 0); $('left-view').onclick = () => camera(Math.PI, 0);
  $('superior').onclick = () => camera(Math.PI/2, Math.PI/2); $('reset-3d').onclick = () => camera(Math.PI/2, .2);
  surface.onpointerdown = event => {drag = [event.clientX, event.clientY]; surface.setPointerCapture(event.pointerId); surface.focus();};
  surface.onpointermove = event => {if (drag) {azimuth -= (event.clientX-drag[0])*.01; elevation = Math.max(-Math.PI/2, Math.min(Math.PI/2, elevation+(event.clientY-drag[1])*.01)); drag = [event.clientX, event.clientY]; draw3D();}};
  surface.onpointerup = surface.onpointercancel = () => {drag = null;};
  surface.onwheel = event => {event.preventDefault(); zoom = Math.min(3, Math.max(.4, zoom+event.deltaY*.002)); draw3D();};
  surface.onkeydown = event => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '-'].includes(event.key)) return; event.preventDefault();
    if (event.key === 'ArrowLeft') azimuth += .15; if (event.key === 'ArrowRight') azimuth -= .15;
    if (event.key === 'ArrowUp') elevation = Math.min(Math.PI/2, elevation+.15); if (event.key === 'ArrowDown') elevation = Math.max(-Math.PI/2, elevation-.15);
    if (event.key === '+') zoom = Math.max(.4, zoom-.1); if (event.key === '-') zoom = Math.min(3, zoom+.1); draw3D();
  };
  window.addEventListener('resize', draw3D); enlarge($('enlarge-mri'), canvas); enlarge($('enlarge-3d'), surface);
  window.SPLNativeReference = {
    state: () => ({contrast: $('contrast').value, imageState: canvas.dataset.state ? JSON.parse(canvas.dataset.state) : null,
      renderState, visible: visible.map(mesh => ({code: mesh.row.code, file: mesh.row.file, bounds: mesh.bounds, vertices: mesh.row.vertexCount, triangles: mesh.row.triangleCount}))}),
    probe: voxel => image ? C.probe(imageRow, image, manifest.labelVolume, labelData, voxel) : null,
    gpuReadback: async () => {
      const rows = [];
      if (!gl || !program) return rows;
      gl.useProgram(program);
      for (const mesh of meshCache.values()) {
        const positions = new Float32Array(mesh.row.vertexCount*3), indices = new Uint32Array(mesh.row.triangleCount*3);
        gl.bindBuffer(gl.ARRAY_BUFFER, mesh.positionBuffer); gl.getBufferSubData(gl.ARRAY_BUFFER, 0, positions);
        gl.bindVertexArray(mesh.vao); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, mesh.indexBuffer); gl.getBufferSubData(gl.ELEMENT_ARRAY_BUFFER, 0, indices);
        const feedback = gl.createTransformFeedback(), outputBuffer = gl.createBuffer(), world = new Float32Array(positions.length);
        gl.bindTransformFeedback(gl.TRANSFORM_FEEDBACK, feedback); gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER, outputBuffer);
        gl.bufferData(gl.TRANSFORM_FEEDBACK_BUFFER, world.byteLength, gl.STREAM_READ); gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER, 0, outputBuffer);
        gl.enable(gl.RASTERIZER_DISCARD); gl.beginTransformFeedback(gl.POINTS); gl.drawArrays(gl.POINTS, 0, mesh.row.vertexCount);
        gl.endTransformFeedback(); gl.disable(gl.RASTERIZER_DISCARD); gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER, 0, null);
        gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER, outputBuffer); gl.getBufferSubData(gl.TRANSFORM_FEEDBACK_BUFFER, 0, world);
        if (gl.getError() !== gl.NO_ERROR) throw Error('GPU readback failed');
        rows.push({code: mesh.row.code, file: mesh.row.file, positionSHA256: await sha(positions.buffer), indexSHA256: await sha(indices.buffer),
          worldSHA256: await sha(world.buffer), positionByteLength: positions.byteLength, indexByteLength: indices.byteLength});
        gl.deleteBuffer(outputBuffer); gl.deleteTransformFeedback(feedback);
      }
      draw3D(); return rows;
    },
  };
  await loadManifest();
})();
