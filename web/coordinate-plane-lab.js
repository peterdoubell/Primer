(function (host) {
  'use strict';
  let serial = 0;
  function render(item, hooks = {}) {
    if (item?.renderer !== 'coordinate-plane-lab' || item?.props?.scenario !== 'math.2.coordinates' || Object.keys(item.props).length !== 1) return null;
    const c = host.PrimerCoordinatePlaneCore, geometry = host.PrimerCoordinatePlaneSpatial;
    if (!c || !geometry) return null;
    const E = (tag, attrs = {}, ...children) => { const el = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v)); for (const child of children.flat()) el.append(child?.nodeType ? child : document.createTextNode(String(child))); return el; };
    const S = (tag, attrs = {}, text) => { const el = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v)); if (text !== undefined) el.textContent = text; return el; };
    const uid = 'coordinate-plane-' + ++serial, bus = host.PrimerLessonStateBus;
    let scene = geometry.scene(c.defaults()), signature = '';
    const root = E('section', { class: 'card lesson-model coordinate-plane-lab', 'aria-labelledby': uid + '-title' });
    const title = E('h3', { id: uid + '-title' }, item.title || 'Explore the coordinate plane');
    const examples = c.presets(), chooser = E('select', { 'aria-label': 'Worked example', 'data-coordinate-presets': '' }, E('option', { value: '' }, 'Choose an example'), examples.map(p => E('option', { value: p.id }, p.label)));
    const reset = E('button', { type: 'button' }, 'Reset'), controls = E('div', { class: 'coordinate-controls' });
    const error = E('p', { role: 'alert', 'data-coordinate-error': '' }), readout = E('p', { 'data-coordinate-result': '' });
    const plot = E('div', { class: 'coordinate-plot' }), tableHost = E('div', { class: 'coordinate-table', tabindex: '0', 'aria-label': 'Exact point coordinates' });
    const note = E('p', {}), live = E('p', { class: 'coordinate-live', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    root.append(title, E('p', {}, item.instructions || 'Plot ordered pairs, then compare movements, reflections, distances and rectangles.'), E('div', { class: 'coordinate-actions' }, E('label', {}, 'Worked example', chooser), reset), controls, error, readout, plot, tableHost, note, live);
    function fields() {
      const s = scene.model.state;
      const result = [{ key: 'mode', label: 'Construction', options: [['plot', 'Plot and exchange coordinates'], ['translate', 'Move a point'], ['reflect', 'Reflect or turn a point'], ['distance', 'Measure distance'], ['rectangle', 'Complete a rectangle']] }, { key: 'x', label: 'P: x coordinate' }, { key: 'y', label: 'P: y coordinate' }];
      if (s.mode === 'translate') result.push({ key: 'dx', label: 'Horizontal movement (right +, left −)' }, { key: 'dy', label: 'Vertical movement (up +, down −)' });
      if (s.mode === 'reflect') result.push({ key: 'reflection', label: 'Transformation', options: [['x-axis', 'Reflect across the x-axis'], ['y-axis', 'Reflect across the y-axis'], ['diagonal', 'Reflect across y = x'], ['origin', 'Half-turn about the origin']] });
      if (s.mode === 'distance' || s.mode === 'rectangle') result.push({ key: 'qx', label: 'Q: x coordinate' }, { key: 'qy', label: 'Q: y coordinate' });
      return result;
    }
    function refreshControls() {
      const descriptor = fields(), nextSignature = JSON.stringify(descriptor);
      if (signature !== nextSignature) {
        signature = nextSignature; controls.replaceChildren();
        for (const f of descriptor) {
          const id = uid + '-' + f.key;
          const input = f.options ? E('select', { id, 'data-coordinate-field': f.key }, f.options.map(([value, label]) => E('option', { value }, label))) : E('input', { id, type: 'text', inputmode: 'text', autocomplete: 'off', spellcheck: 'false', 'data-coordinate-field': f.key });
          input.onchange = () => commit(input);
          input.onkeydown = event => { if (event.key === 'Enter') { event.preventDefault(); commit(input); } else if (event.key === 'Escape') { event.preventDefault(); refreshControls(); error.textContent = ''; } };
          controls.append(E('label', { for: id }, f.label, input));
        }
        controls.append(E('p', { class: 'coordinate-hint' }, 'Enter integers, decimals or fractions such as −1/2 (use the minus key). Magnitude ≤ 1000; reduced denominator ≤ 1000. Press Enter to apply.'));
      }
      for (const input of controls.querySelectorAll('[data-coordinate-field]')) { input.value = scene.model.state[input.dataset.coordinateField]; input.removeAttribute('aria-invalid'); }
    }
    function commit(input) {
      const state = { ...scene.model.state }, key = input.dataset.coordinateField;
      try {
        for (const el of controls.querySelectorAll('[data-coordinate-field]')) state[el.dataset.coordinateField] = el.value;
        accept(state, true); chooser.value = ''; controls.querySelector('[data-coordinate-field="' + key + '"]')?.focus();
      } catch (e) { input.setAttribute('aria-invalid', 'true'); error.textContent = e.message + ' Both charts and the calculations retain the last accepted values. Escape restores those values.'; }
    }
    function draw() {
      const e = scene.extent, scale = 280 / e, X = x => 340 + x * scale, Y = y => 320 - y * scale;
      const svg = S('svg', { viewBox: '0 0 680 650', role: 'img', 'aria-label': 'Coordinate plane with equal x and y scales. Exact named coordinates follow in the table.', 'data-coordinate-graph': '', 'data-gain': scale, 'data-extent': e });
      svg.append(S('title', {}, scene.model.readout), S('rect', { x: 60, y: 40, width: 560, height: 560, fill: '#fcfaf4' }));
      for (const t of scene.ticks) {
        svg.append(S('line', { x1: X(t), x2: X(t), y1: 40, y2: 600, stroke: t === 0 ? '#243c45' : '#d2ddd7', 'stroke-width': t === 0 ? 2 : 1 }), S('line', { x1: 60, x2: 620, y1: Y(t), y2: Y(t), stroke: t === 0 ? '#243c45' : '#d2ddd7', 'stroke-width': t === 0 ? 2 : 1 }));
        svg.append(S('text', { x: X(t), y: 625, 'text-anchor': 'middle' }, t), S('text', { x: 48, y: Y(t) + 5, 'text-anchor': 'end' }, t));
      }
      svg.append(S('text', { x: 638, y: 325 }, 'x'), S('text', { x: 335, y: 25 }, 'y'));
      if (scene.model.state.mode === 'reflect' && scene.model.state.reflection !== 'origin') {
        const kind = scene.model.state.reflection, p = kind === 'x-axis' ? [[-e, 0], [e, 0]] : kind === 'y-axis' ? [[0, -e], [0, e]] : [[-e, -e], [e, e]];
        svg.append(S('line', { x1: X(p[0][0]), y1: Y(p[0][1]), x2: X(p[1][0]), y2: Y(p[1][1]), stroke: '#876888', 'stroke-width': 3, 'stroke-dasharray': '8 5' }));
      }
      for (const segment of scene.segments) svg.append(S('line', { x1: X(segment.from[0]), y1: Y(segment.from[1]), x2: X(segment.to[0]), y2: Y(segment.to[1]), stroke: segment.id === 'straight-distance' ? '#bb6248' : '#2a7b75', 'stroke-width': 3, 'data-coordinate-segment': segment.id }));
      scene.markers.forEach((p, i) => {
        const label = 'M' + (i + 1);
        svg.append(S('circle', { cx: X(p.x), cy: Y(p.y), r: 5, fill: '#b08625', stroke: '#fff', 'stroke-width': 1, 'data-coordinate-marker': p.ids.join('/') }), S('text', { x: X(p.x) + 9, y: Y(p.y) - 9, 'font-weight': 'bold' }, label));
      });
      plot.replaceChildren(svg);
      const body = E('tbody');
      for (const p of scene.points) body.append(E('tr', {}, E('td', {}, 'M' + (scene.markers.findIndex(g => g.ids.includes(p.id)) + 1)), E('th', { scope: 'row' }, p.label), E('td', {}, p.xText), E('td', {}, p.yText), E('td', {}, c.location(p.xText, p.yText))));
      tableHost.replaceChildren(E('table', {}, E('caption', {}, 'Exact coordinates (shared markers keep every point name)'), E('thead', {}, E('tr', {}, ['Marker', 'Point', 'x', 'y', 'Location'].map(t => E('th', { scope: 'col' }, t)))), body));
    }
    function accept(raw, announce = false, shared = false) {
      const next = geometry.scene(raw); scene = next; error.textContent = ''; refreshControls(); draw();
      readout.textContent = scene.model.readout; note.textContent = scene.model.note + ' Both axes use equal scales. The view fits all named points; grid spacing is ' + scene.step + ' units. Use the exact coordinate table when points are too close to distinguish on screen.';
      if (announce) live.textContent = scene.model.readout;
      if (!shared) bus?.publish('math.2.coordinates', root, { ...scene.model.state });
      return { ...scene.model.state };
    }
    chooser.onchange = () => { const p = examples.find(p => p.id === chooser.value); if (p) accept(p.state, true); };
    reset.onclick = () => { chooser.value = ''; accept(c.defaults(), true); };
    root.getModelSpeech = () => scene.model.readout + ' ' + scene.model.note;
    root.setModelState = (raw, announce = false, shared = false) => { chooser.value = ''; return accept(raw, announce, shared); };
    root.coordinatePlane = { getModel: () => scene.model, getScene: () => scene, getState: () => ({ ...scene.model.state }) };
    if (hooks.speakButton) title.prepend(hooks.speakButton(root.getModelSpeech, 'Read this activity aloud'));
    bus?.join('math.2.coordinates', root, raw => root.setModelState(raw, false, true)); accept(c.defaults()); return root;
  }
  const api = Object.freeze({ render });
  if (host) host.PrimerCoordinatePlaneLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window === 'undefined' ? null : window);
