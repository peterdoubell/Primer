/* Local 3D geometry, projected into SVG. No GPU, downloads, or animation loop. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const scenes = Object.create(null);
  const colors = Object.freeze({ blue: '#3e7085', teal: '#317e78', gold: '#b98a2f',
    coral: '#b96652', plum: '#876888', green: '#5c7754', ink: '#263b46' });
  const cameraStart = Object.freeze({ yaw: -28, pitch: 18, zoom: 1 });
  let serial = 0;
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
  const finitePoint = p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite);
  const subtract = (a, b) => a.map((v, i) => v - b[i]);
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const length = p => Math.hypot(...p);

  function element(tag, attrs = {}, text, svg = false) {
    const el = svg ? document.createElementNS(NS, tag) : document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, String(value)));
    if (text != null) el.textContent = text;
    return el;
  }
  function shade(hex, light) {
    if (!/^#[0-9a-f]{6}$/i.test(hex)) return hex;
    return '#' + [1, 3, 5].map(i => Math.round(clamp(parseInt(hex.slice(i, i + 2), 16) * light,
      0, 255)).toString(16).padStart(2, '0')).join('');
  }
  function geometry() {
    const primitives = [];
    function add(kind, points, color, options = {}) {
      if (!points.every(finitePoint)) throw new Error('Non-finite 3D geometry');
      if (primitives.length >= 3000) throw new Error('3D scene exceeds geometry limit');
      primitives.push({ kind, points, color, ...options });
    }
    const g = {
      colors,
      polygon(points, color, options) { add('polygon', points, color, options); },
      line(points, color, options) { add('line', points, color, options); },
      sphere(center, radius, color, options) {
        if (!Number.isFinite(radius) || radius <= 0) throw new Error('Invalid 3D radius');
        add('sphere', [center], color, { ...options, radius });
      },
      label(point, text, color = colors.ink) { add('label', [point], color, { text }); },
      mesh(surface, nu, nv, color, options = {}) {
        if (!Number.isInteger(nu) || !Number.isInteger(nv) || nu < 1 || nv < 1 || nu * nv > 1600) {
          throw new Error('Invalid 3D mesh resolution');
        }
        const grid = Array.from({ length: nu + 1 }, (_, i) =>
          Array.from({ length: nv + 1 }, (_, j) => surface(i / nu, j / nv)));
        for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
          g.polygon([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]], color, options);
        }
      },
      box(center, size, color, options) {
        const points = [[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]]
          .map(v => v.map((x, i) => center[i] + x * size[i] / 2));
        [[0,3,2,1],[4,5,6,7],[0,1,5,4],[3,7,6,2],[0,4,7,3],[1,2,6,5]]
          .forEach(indices => g.polygon(indices.map(i => points[i]), color, options));
      },
      arrow(start, end, color, options = {}) {
        const delta = subtract(end, start), len = length(delta);
        if (len < 1e-8) return;
        // Segment the shaft so nearby surfaces can occlude its far end.
        for (let i = 0; i < 12; i++) g.line([i / 12, (i + 1) / 12].map(t =>
          start.map((v, j) => v + delta[j] * t)), color, { width: 3, ...options });
        const unit = delta.map(v => v / len);
        const side = cross(unit, Math.abs(unit[1]) < .9 ? [0,1,0] : [1,0,0]);
        const sideLen = length(side), head = Math.min(.16, len * .23);
        const base = end.map((v, i) => v - head * unit[i]);
        const perpendicular = cross(unit, side).map(v => v / sideLen);
        const ring = Array.from({ length: 6 }, (_, i) => base.map((v, j) => v + head * .48 *
          (side[j] / sideLen * Math.cos(i * Math.PI / 3) + perpendicular[j] * Math.sin(i * Math.PI / 3))));
        ring.forEach((p, i) => g.polygon([p, ring[(i + 1) % 6], end], color));
      },
    };
    return { g, primitives };
  }
  function normalizeState(spec, supplied = {}) {
    const state = { ...spec.initial };
    spec.controls.forEach(control => {
      const value = Object.prototype.hasOwnProperty.call(supplied, control.key) ? supplied[control.key] : state[control.key];
      if (control.options) {
        if (control.options.some(option => option.value === value)) state[control.key] = value;
      } else {
        const numeric = Number(value);
        if (Number.isFinite(numeric)) {
          const stepped = control.min + Math.round((numeric - control.min) / control.step) * control.step;
          state[control.key] = Number(clamp(stepped, control.min, control.max).toFixed(8));
        }
      }
    });
    return state;
  }
  function build(id, supplied) {
    if (!Object.prototype.hasOwnProperty.call(scenes, id)) return null;
    const spec = scenes[id], state = normalizeState(spec, supplied);
    const { g, primitives } = geometry();
    const explanation = spec.build(state, g);
    return { state, primitives, ...explanation };
  }
  function rotate(point, camera) {
    const yaw = camera.yaw * Math.PI / 180, pitch = camera.pitch * Math.PI / 180;
    const x = point[0] * Math.cos(yaw) + point[2] * Math.sin(yaw);
    const z = -point[0] * Math.sin(yaw) + point[2] * Math.cos(yaw);
    return [x, point[1] * Math.cos(pitch) - z * Math.sin(pitch),
      point[1] * Math.sin(pitch) + z * Math.cos(pitch)];
  }

  function render(item, hooks = {}) {
    const id = item.props && item.props.scenario;
    if (!Object.prototype.hasOwnProperty.call(scenes, id)) return null;
    const spec = scenes[id], uid = 'spatial-' + ++serial;
    const initialCamera = { ...cameraStart, ...spec.camera };
    // A host may open the model on a chosen state, e.g. the landmark of a reporting step.
    const initialState = hooks.state && typeof hooks.state === 'object' ? { ...hooks.state } : {};
    let current = build(id, initialState), camera = { ...initialCamera }, pendingFrame = null;
    let drag = null;
    // Start with the authored scene's framing; only shrink an unusually large
    // state enough to keep it visible. Explicit user zoom is never auto-fitted.
    const bounds = current.primitives.filter(p => p.kind !== 'label').flatMap(p =>
      p.points.flatMap(point => p.radius ? [-1, 1].map(sign => point.map(v => v + sign * p.radius)) : [point]));
    const center = [0, 1, 2].map(axis =>
      (Math.min(...bounds.map(p => p[axis])) + Math.max(...bounds.map(p => p[axis]))) / 2);
    const radius = Math.max(.1, ...current.primitives.filter(p => p.kind !== 'label')
      .flatMap(p => p.points.map(v => length(subtract(v, center)) + (p.radius || 0))));
    const root = element('section', { class: 'card lesson-model spatial-model',
      'data-renderer': 'spatial-3d', 'data-scenario': id, 'aria-labelledby': uid + '-title' });
    const heading = element('div', { class: 'model-heading-row' });
    heading.append(element('h3', { id: uid + '-title' }, item.title),
      element('span', { class: 'spatial-badge' }, 'Interactive 3D'));
    const instructions = element('p', { class: 'model-instructions', id: uid + '-instructions' }, item.instructions);
    const canvas = element('div', { class: 'model-canvas spatial-canvas' });
    const svg = element('svg', { viewBox: '0 0 600 420', class: 'spatial-svg',
      tabindex: '0', role: 'group', 'aria-label': 'Rotatable 3D view: ' + item.title,
      'aria-describedby': uid + '-help ' + uid + '-readout' }, null, true);
    const help = element('p', { id: uid + '-help', class: 'spatial-help' },
      'Drag to rotate · Arrow keys rotate · + / − zoom · Home restores the view. All actions also have buttons.');
    const controls = element('div', { class: 'model-controls spatial-controls' });
    const readout = element('p', { id: uid + '-readout', class: 'model-readout spatial-readout' });
    const note = element('p', { class: 'spatial-note' });
    const status = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    const legend = element('ul', { class: 'spatial-legend', 'aria-label': 'Model key' });
    const parameterControls = new Map();
    const orientation = element('output', { class: 'spatial-orientation', 'aria-label': 'Camera orientation' });
    function draw() {
      pendingFrame = null;
      const requestedScale = 175 / radius * camera.zoom;
      const extents = current.primitives.filter(p => p.kind !== 'label')
        .flatMap(p => p.points.map(point => ({ point: rotate(subtract(point, center), camera), radius: p.radius || 0 })));
      const fitScale = Math.min(282 / Math.max(.1, ...extents.map(p => Math.abs(p.point[0]) + p.radius)),
        192 / Math.max(.1, ...extents.map(p => Math.abs(p.point[1]) + p.radius)));
      const scale = camera.zoom <= 1 ? Math.min(requestedScale, fitScale) : requestedScale;
      const project = p => { const r = rotate(subtract(p, center), camera); return [300 + r[0] * scale, 210 - r[1] * scale, r[2]]; };
      const group = element('g', {}, null, true);
      const labels = [];
      // A curve can pass both in front of and behind a surface. Sorting an entire
      // loop at its average depth incorrectly paints its far side over the hole.
      const ordered = current.primitives.flatMap(p => p.kind === 'line' && p.points.length > 2
        ? p.points.slice(1).map((point, i) => ({ ...p, points: [p.points[i], point] })) : [p])
        .map(p => ({ ...p, projected: p.points.map(project) }))
        .sort((a, b) => a.projected.reduce((sum, v) => sum + v[2], 0) / a.projected.length -
          b.projected.reduce((sum, v) => sum + v[2], 0) / b.projected.length);
      ordered.forEach(p => {
        const pts = p.projected, options = { opacity: p.opacity == null ? 1 : p.opacity };
        if (p.kind === 'label') { labels.push(p); return; }
        if (p.kind === 'sphere') {
          group.append(element('circle', { ...options, cx: pts[0][0], cy: pts[0][1], r: p.radius * scale,
            fill: p.color, stroke: shade(p.color, .7), 'stroke-width': 1.1 }, null, true));
          group.append(element('circle', { cx: pts[0][0] - p.radius * scale * .23,
            cy: pts[0][1] - p.radius * scale * .25, r: p.radius * scale * .44,
            fill: '#fff', opacity: .17 * options.opacity }, null, true));
        } else if (p.kind === 'polygon') {
          // Lighting needs a normal in one unit system. Pixel-scaled x/y mixed
          // with world-space depth flattens almost every face's apparent shade.
          const n = rotate(cross(subtract(p.points[1], p.points[0]), subtract(p.points[2], p.points[0])), camera);
          const brightness = .78 + .25 * Math.abs(n[2]) / (length(n) || 1);
          group.append(element('polygon', { ...options, points: pts.map(v => v.slice(0, 2).join(',')).join(' '),
            fill: shade(p.color, brightness), stroke: p.stroke === false ? 'none' : (p.stroke || shade(p.color, .65)),
            'stroke-width': p.width || .55, 'stroke-linejoin': 'round' }, null, true));
        } else {
          group.append(element('polyline', { ...options, points: pts.map(v => v.slice(0, 2).join(',')).join(' '),
            fill: 'none', stroke: p.color, 'stroke-width': p.width || 2,
            'stroke-dasharray': p.dashed ? '6 4' : 'none', 'stroke-linecap': 'round' }, null, true));
        }
      });
      // Screen-space callouts keep annotations legible on small screens and when
      // rotation projects distinct points onto the same place. Conservative text
      // bounds also work on the initial render, before the SVG is connected.
      const placed = [];
      labels.sort((a, b) => a.projected[0][1] - b.projected[0][1]).forEach(p => {
        const [anchorX, anchorY] = p.projected[0];
        const width = Math.min(560, p.text.length * 16), height = 28;
        let best, bestScore = Infinity;
        for (const dy of [0, -34, 34, -68, 68, -102, 102, -136, 136]) {
          for (const dx of [0, -48, 48, -96, 96]) {
            const x = clamp(anchorX + dx, width / 2 + 12, 588 - width / 2);
            const y = clamp(anchorY + dy, height + 12, 408);
            const box = { left: x - width / 2, right: x + width / 2, top: y - height, bottom: y + 5 };
            const overlaps = placed.filter(other => box.left < other.right + 5 && box.right + 5 > other.left &&
              box.top < other.bottom + 5 && box.bottom + 5 > other.top).length;
            const score = overlaps * 1e6 + Math.hypot(x - anchorX, y - anchorY);
            if (score < bestScore) { best = { x, y, box }; bestScore = score; }
          }
        }
        placed.push(best.box);
        if (Math.hypot(best.x - anchorX, best.y - anchorY) > 12 &&
            anchorX >= 8 && anchorX <= 592 && anchorY >= 8 && anchorY <= 412) {
          group.append(element('line', { x1: anchorX, y1: anchorY, x2: best.x, y2: best.y - 12,
            stroke: p.color, opacity: .65, 'stroke-width': 1.2, 'aria-hidden': 'true' }, null, true));
        }
        group.append(element('text', { x: best.x, y: best.y,
          class: 'spatial-label', 'text-anchor': 'middle' }, p.text, true));
      });
      svg.replaceChildren(element('title', {}, item.title, true), group);
      orientation.textContent = 'Turn ' + Math.round(camera.yaw) + '° · Tilt ' + Math.round(camera.pitch) +
        '° · Zoom ' + Math.round(camera.zoom * 100) + '%' + (scale < requestedScale ? ' · Auto-fit' : '');
      root.dataset.view = [camera.yaw, camera.pitch, camera.zoom].join(',');
    }
    function changeView(yaw, pitch, zoom, announce = true) {
      camera = { yaw: ((yaw + 180) % 360 + 360) % 360 - 180,
        pitch: clamp(pitch, -85, 85), zoom: clamp(zoom, .65, 2) };
      draw();
      if (announce) status.textContent = orientation.textContent + '. ' + current.readout;
    }
    function refresh(announce) {
      current = build(id, current.state);
      parameterControls.forEach(({ input, output, control }) => {
        input.value = current.state[control.key];
        if (output) {
          output.textContent = current.state[control.key] + (control.unit || '');
          input.setAttribute('aria-valuetext', output.textContent);
        }
      });
      readout.textContent = current.readout;
      note.textContent = current.note || '';
      legend.replaceChildren(...(current.legend || []).map(entry => {
        const li = element('li');
        const swatch = element('span', { class: 'spatial-swatch', 'aria-hidden': 'true' });
        swatch.style.backgroundColor = entry.color;
        li.append(swatch, document.createTextNode(entry.label)); return li;
      }));
      draw();
      if (announce) status.textContent = current.readout;
    }
    spec.controls.forEach(control => {
      const label = element('label', { class: 'spatial-parameter', for: uid + '-' + control.key });
      const title = element('span', {}, control.label);
      let input, output;
      if (control.options) {
        input = element('select', { id: uid + '-' + control.key, 'data-parameter': control.key });
        control.options.forEach(option => input.append(element('option', { value: option.value }, option.label)));
      } else {
        output = element('output', { for: uid + '-' + control.key });
        title.append(output);
        input = element('input', { id: uid + '-' + control.key, type: 'range', min: control.min,
          max: control.max, step: control.step, 'data-parameter': control.key });
      }
      const update = () => {
        current.state[control.key] = control.options ? input.value : Number(input.value);
        refresh(true);
      };
      input.addEventListener(control.options ? 'change' : 'input', update);
      label.append(title, input); controls.append(label);
      parameterControls.set(control.key, { input, output, control });
    });
    const cameraButtons = element('div', { class: 'model-button-row spatial-camera-controls',
      role: 'group', 'aria-label': '3D camera controls' });
    function button(text, fn) {
      const b = element('button', { type: 'button', class: 'btn ghost small' }, text);
      b.addEventListener('click', fn); cameraButtons.append(b);
    }
    button('Rotate left', () => changeView(camera.yaw - 15, camera.pitch, camera.zoom));
    button('Rotate right', () => changeView(camera.yaw + 15, camera.pitch, camera.zoom));
    button('Tilt up', () => changeView(camera.yaw, camera.pitch + 15, camera.zoom));
    button('Tilt down', () => changeView(camera.yaw, camera.pitch - 15, camera.zoom));
    button('Zoom in', () => changeView(camera.yaw, camera.pitch, camera.zoom + .15));
    button('Zoom out', () => changeView(camera.yaw, camera.pitch, camera.zoom - .15));
    button('Reset view', () => changeView(initialCamera.yaw, initialCamera.pitch, initialCamera.zoom));
    button('Reset model', () => { current = build(id, initialState); camera = { ...initialCamera }; refresh(true); });
    svg.addEventListener('keydown', event => {
      const actions = {
        ArrowLeft: () => changeView(camera.yaw - 10, camera.pitch, camera.zoom),
        ArrowRight: () => changeView(camera.yaw + 10, camera.pitch, camera.zoom),
        ArrowUp: () => changeView(camera.yaw, camera.pitch + 10, camera.zoom),
        ArrowDown: () => changeView(camera.yaw, camera.pitch - 10, camera.zoom),
        '+': () => changeView(camera.yaw, camera.pitch, camera.zoom + .15),
        '=': () => changeView(camera.yaw, camera.pitch, camera.zoom + .15),
        '-': () => changeView(camera.yaw, camera.pitch, camera.zoom - .15),
        Home: () => changeView(initialCamera.yaw, initialCamera.pitch, initialCamera.zoom),
      };
      if (Object.prototype.hasOwnProperty.call(actions, event.key)) { event.preventDefault(); actions[event.key](); }
    });
    svg.addEventListener('pointerdown', event => {
      if (event.button !== 0 || !event.isPrimary) return;
      svg.focus({ preventScroll: true });
      svg.setPointerCapture(event.pointerId);
      drag = { id: event.pointerId, x: event.clientX, y: event.clientY, ...camera };
    });
    svg.addEventListener('pointermove', event => {
      if (!drag || event.pointerId !== drag.id) return;
      camera.yaw = drag.yaw + (event.clientX - drag.x) * .45;
      camera.pitch = clamp(drag.pitch + (event.clientY - drag.y) * .4, -85, 85);
      if (pendingFrame == null) pendingFrame = requestAnimationFrame(() => {
        pendingFrame = null;
        if (root.isConnected) draw();
      });
    });
    function endDrag(event) {
      if (!drag || event.pointerId !== drag.id) return;
      drag = null;
      if (svg.hasPointerCapture(event.pointerId)) svg.releasePointerCapture(event.pointerId);
      if (pendingFrame != null) { cancelAnimationFrame(pendingFrame); pendingFrame = null; }
      changeView(camera.yaw, camera.pitch, camera.zoom);
    }
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(name => svg.addEventListener(name, endDrag));
    if (typeof hooks.speakButton === 'function') {
      heading.prepend(hooks.speakButton(() => [item.title, item.instructions, current.readout, current.note].filter(Boolean).join(' '),
        'Read this 3D activity aloud'));
    }
    canvas.append(svg, orientation);
    root.append(heading, instructions, canvas, help, cameraButtons, controls, legend, readout, note, status);
    refresh(false);
    // Values pass through the same validation as the visible controls.
    root.setModelState = (values, announce = false) => {
      if (!values || typeof values !== 'object') return;
      Object.assign(current.state, values);
      refresh(announce);
    };
    return root;
  }
  window.PrimerSpatial = Object.freeze({
    register(map) {
      Object.entries(map).forEach(([id, spec]) => {
        if (Object.prototype.hasOwnProperty.call(scenes, id)) throw new Error('Duplicate spatial scene: ' + id);
        scenes[id] = spec;
      });
    },
    render, build, rotate,
    get supported() { return Object.keys(scenes); },
    controls(id) { return Object.prototype.hasOwnProperty.call(scenes, id) ? scenes[id].controls : []; },
  });
}());
