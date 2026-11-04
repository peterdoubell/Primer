'use strict';
(async function () {
  const select = document.querySelector('#plane');
  const slider = document.querySelector('#slice');
  const overlay = document.querySelector('#overlay');
  const manifest = await (await fetch('manifest.json')).json();
  const volumes = {};
  await Promise.all(Object.entries(manifest).map(async ([name, layer]) => {
    const response = await fetch(layer.file);
    if (!response.ok) throw Error('Missing volume');
    const stream = response.body.pipeThrough(new DecompressionStream('gzip'));
    volumes[name] = new Uint8Array(await new Response(stream).arrayBuffer());
    if (volumes[name].length !== layer.bytes) throw Error('Incomplete volume');
  }));
  const dimensions = [182,218,182];
  const positions = [129,123,96];
  const colors = [null,[242,82,87],[77,171,245],[255,199,61]];
  const labels = ['Outside the segmented compartments', 'Necrotic core', 'Non-enhancing or edematous tumour', 'Contrast-enhancing tumour'];
  const canvases = {};
  const markers = {};
  function planeAxes() {
    return [0,1,2].filter(i => i !== Number(select.value));
  }
  function bound(value, axis) {
    return Math.max(0, Math.min(dimensions[axis] - 1, value));
  }
  for (const [key,title] of Object.entries({t1:'T1 pre-contrast',t1ce:'T1 post-contrast',t2:'T2',flair:'FLAIR'})) {
    const figure = document.createElement('figure');
    const caption = document.createElement('figcaption');
    caption.textContent = title;
    const canvas = document.createElement('canvas');
    canvas.setAttribute('aria-label',title);
    const view = document.createElement('div');
    view.className = 'slice-view';
    const marker = document.createElement('span');
    marker.className = 'locator';
    marker.setAttribute('aria-hidden', 'true');
    markers[key] = marker;
    canvas.tabIndex = 0;
    canvas.setAttribute('aria-describedby', 'locate-help point');
    canvas.addEventListener('click', event => {
      const [h,v] = planeAxes();
      const rect = canvas.getBoundingClientRect();
      positions[h] = bound(Math.floor((event.clientX - rect.left) * canvas.width / rect.width), h);
      positions[v] = bound(canvas.height - 1 - Math.floor((event.clientY - rect.top) * canvas.height / rect.height), v);
      draw();
    });
    canvas.addEventListener('keydown', event => {
      const [h,v] = planeAxes();
      const step = {ArrowLeft:[h,-1], ArrowRight:[h,1], ArrowDown:[v,-1], ArrowUp:[v,1]}[event.key];
      if (!step) return;
      event.preventDefault();
      positions[step[0]] = bound(positions[step[0]] + step[1], step[0]);
      draw();
    });
    view.append(canvas, marker);
    figure.append(caption, view);
    document.querySelector('main').append(figure);
    canvases[key] = canvas;
  }
  function draw() {
    const axis = Number(select.value);
    const [horizontal,vertical] = planeAxes();
    const [i,j,k] = positions;
    const label = volumes.mask[i + dimensions[0] * (j + dimensions[1] * k)];
    // The source NIfTI sform maps this LAS voxel grid into RAS millimetres.
    document.dispatchEvent(new CustomEvent('mri-section', {
      detail: {axis, coordinate: [90-i, j-126, k-72][axis]}
    }));
    document.querySelector('#point').textContent =
      'MNI152 (R, A, S): ' + [90-i, j-126, k-72].join(', ') + ' mm · ' + labels[label];
    const orientation = ['P → A, superior up','R → L, superior up','R → L, anterior up'][axis];
    document.querySelector('#status').textContent = orientation;
    slider.max = dimensions[axis]-1;
    slider.value = positions[axis];
    document.querySelector('#index').textContent = positions[axis];
    for (const [key,canvas] of Object.entries(canvases)) {
      canvas.width = dimensions[horizontal];
      canvas.height = dimensions[vertical];
      markers[key].style.left = (100 * (positions[horizontal] + 0.5) / canvas.width) + '%';
      markers[key].style.top = (100 * (canvas.height - 0.5 - positions[vertical]) / canvas.height) + '%';
      const ctx = canvas.getContext('2d');
      const pixels = ctx.createImageData(canvas.width,canvas.height);
      const xyz = positions.slice();
      for (let y=0;y<canvas.height;y++) for (let x=0;x<canvas.width;x++) {
        xyz[horizontal] = x;
        xyz[vertical] = canvas.height-1-y;
        const voxel = xyz[0]+182*(xyz[1]+218*xyz[2]);
        const intensity = volumes[key][voxel];
        const color = overlay.checked && colors[volumes.mask[voxel]];
        const pixel = 4*(x+y*canvas.width);
        for(let c=0;c<3;c++) pixels.data[pixel+c] = color ? Math.round((58*intensity+42*color[c])/100) : intensity;
        pixels.data[pixel+3] = 255;
      }
      ctx.putImageData(pixels,0,0);
    }
  }
  slider.min=0;
  slider.oninput=()=>{positions[Number(select.value)]=Number(slider.value);draw();};
  select.onchange=overlay.onchange=draw;
  draw();
})().catch(()=>{document.querySelector('#status').textContent='Image loading failed. Reload to retry.';});
