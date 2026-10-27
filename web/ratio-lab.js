(function (host) {
  'use strict';
  let serial = 0;
  const titles = { scale: 'Scale both parts', compare: 'Compare two ratios', share: 'Share a total', missing: 'Find the other amount', rate: 'Identical books and unit rates', recipe: 'Scale a recipe', map: 'Map distance to ground distance', model: 'Model length and unit conversion', mapCompare: 'Compare two map scales' };
  const presets = [
    ['flour', '2 : 3 recipe, scaled by 3', { mode: 'scale', a: '2', b: '3', c: '3' }],
    ['map', '8 cm at 5 km per cm', { mode: 'map', a: '5', target: '8' }],
    ['eggs', '9 eggs for 12 → 20 servings', { mode: 'recipe', a: '12', b: '9', target: '20' }],
    ['car', '4.8 m car at scale 1 : 24', { mode: 'model', a: '24', b: '4.8' }],
    ['paint', '40 litres shared 3 : 5', { mode: 'share', a: '3', b: '5', target: '40' }],
    ['missing', '7 : 3, with A = 91', { mode: 'missing', a: '7', b: '3', target: '91' }],
    ['drink', '450 ml shared 2 : 7', { mode: 'share', a: '2', b: '7', target: '450' }],
    ['books', '6 books weigh 2.4 kg; find 10 books', { mode: 'rate', a: '6', b: '2.4', target: '10' }],
    ['maps', '1 cm : 200 m versus 1 cm : 50 m', { mode: 'mapCompare', a: '200', b: '50', target: '1000' }],
    ['class', 'Class shares in ratio 3 : 4', { mode: 'share', a: '3', b: '4', target: '28' }],
    ['equal', '2 : 3 and 6 : 9', { mode: 'compare', a: '2', b: '3', c: '6', d: '9' }],
    ['addition', 'Adding 3 changes 2 : 3 to 5 : 6', { mode: 'compare', a: '2', b: '3', c: '5', d: '6' }],
    ['third', 'An exact one-third scale factor', { mode: 'recipe', a: '3', b: '2', target: '1' }],
    ['half', 'Scale down by one half', { mode: 'scale', a: '2', b: '3', c: '0.5' }],
    ['zero', 'A zero batch does not define a new ratio', { mode: 'scale', a: '2', b: '3', c: '0' }],
    ['absent', 'One ingredient has zero parts', { mode: 'share', a: '0', b: '5', target: '40' }],
    ['undefined', 'Why 0 : 0 is undefined', { mode: 'share', a: '0', b: '0', target: '40' }],
  ];
  function render(item, hooks = {}) {
    if (item?.renderer !== 'concept-lab' || item?.props?.scenario !== 'math.2.ratio' || Object.keys(item.props).length !== 1) return null;
    const c = host.PrimerRatioCore, q = host.PrimerDecimalCore;
    if (!c || !q) return null;
    const E = (tag, attrs = {}, ...children) => { const n = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v)); for (const x of children.flat()) if (x != null) n.append(x.nodeType ? x : document.createTextNode(String(x))); return n; };
    const S = (tag, attrs = {}, text) => { const n = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v)); if (text !== undefined) n.textContent = text; return n; };
    let state = c.defaults(), model = c.build(state), enlarged = false;
    const root = E('section', { class: 'card lesson-model ratio-workbench' });
    const heading = E('h3', { id: 'ratio-title-' + ++serial }, 'Ratios, rates and scale'); root.setAttribute('aria-labelledby', heading.id);
    const operation = E('select', { 'data-ratio-mode': '' }, Object.entries(titles).map(([k, v]) => E('option', { value: k }, v)));
    const preset = E('select', { 'data-ratio-preset': '' }, E('option', { value: '' }, 'Choose a worked example'), presets.map(([k, v]) => E('option', { value: k }, v)));
    const zoom = E('button', { type: 'button', 'data-ratio-zoom': '', 'aria-pressed': 'false' }, 'Enlarge diagrams');
    const reset = E('button', { type: 'button', 'data-ratio-reset': '' }, 'Reset');
    const controls = E('div', { class: 'ratio-controls' }), error = E('p', { role: 'alert', 'data-ratio-error': '' }), output = E('div', { 'data-ratio-result': '' });
    root.append(heading, E('p', {}, 'Keep the order of the parts and track the units. Exact values appear in the ledger; each chart names its own unit and scale.'), E('div', { class: 'ratio-actions' }, E('label', {}, 'Investigation', operation), E('label', {}, 'Worked example', preset), reset, zoom), controls, error, output);
    function createControls() {
      controls.replaceChildren();
      for (const [key, label] of c.fields[state.mode]) {
        const input = E('input', { type: 'text', inputmode: 'decimal', 'data-ratio-control': key }); input.value = state[key];
        input.addEventListener('change', () => {
          try {
            const candidate = { ...state };
            for (const field of controls.querySelectorAll('input')) candidate[field.dataset.ratioControl] = field.value;
            const accepted = c.build(candidate); state = candidate; model = accepted;
            for (const field of controls.querySelectorAll('input')) field.removeAttribute('aria-invalid');
            refresh();
          } catch (e) { input.setAttribute('aria-invalid', 'true'); error.textContent = e.message + ' Results still use the last accepted inputs.'; }
        });
        input.addEventListener('keydown', event => {
          if (event.key === 'Enter') { event.preventDefault(); input.dispatchEvent(new Event('change')); }
          if (event.key === 'Escape') { createControls(); controls.querySelector('[data-ratio-control="' + key + '"]').focus(); error.textContent = ''; }
        });
        controls.append(E('label', {}, label, input));
      }
    }
    function chart(data, index) {
      const rational = p => q.q(p.n, p.d);
      const max = data.unit === 'fraction of its own whole' ? q.q(1) : data.rows.map(r => rational(r.amount)).reduce((a, b) => q.compare(a, b) > 0 ? a : b, q.q(0));
      const extent = max.n ? max : q.q(1), height = 115 + data.rows.length * 48;
      const svg = S('svg', { viewBox: '0 0 800 ' + height, role: 'img', 'aria-label': data.title + '. Horizontal axis: ' + data.unit + '.', 'data-ratio-plot': index });
      const title = S('title', {}, data.title + '; every bar starts at zero.'); svg.append(title);
      const x0 = 185, width = 555;
      for (let i = 0; i <= 2; i++) {
        const x = x0 + width * i / 2, value = q.pack(q.div(q.mul(extent, q.q(i)), q.q(2)));
        svg.append(S('line', { x1: x, x2: x, y1: 45, y2: height - 45, stroke: '#c4cec3' }));
        const label = value.value === 0 ? '0' : '≈ ' + Number(value.value.toPrecision(5));
        svg.append(S('text', { x, y: 27, 'text-anchor': i === 2 ? 'end' : i === 0 ? 'start' : 'middle', 'data-exact-tick': value.exact }, label));
      }
      data.rows.forEach((row, i) => {
        const y = 52 + i * 48, ratio = q.div(rational(row.amount), extent), length = Number(ratio.n) / Number(ratio.d) * width;
        svg.append(S('text', { x: 170, y: y + 19, 'text-anchor': 'end' }, row.label));
        if (length) svg.append(S('rect', { x: x0, y, width: length, height: 27, fill: row.role === 'A' ? '#247c83' : row.role === 'B' ? '#bc6347' : '#5a695a', 'data-exact-amount': row.amount.fraction, 'data-ratio-bar': i }));
        else svg.append(S('circle', { cx: x0, cy: y + 13.5, r: 3, fill: '#263d38', 'data-exact-amount': '0', 'data-ratio-zero': i }));
      });
      svg.append(S('text', { x: x0, y: height - 10 }, 'Horizontal axis: ' + data.unit));
      const table = E('table', {}, E('caption', {}, data.title + ' — exact quantities'), E('thead', {}, E('tr', {}, E('th', { scope: 'col' }, 'Quantity'), E('th', { scope: 'col' }, 'Exact value'), E('th', { scope: 'col' }, 'Unit'))), E('tbody', {}, data.rows.map(row => E('tr', {}, E('th', { scope: 'row' }, row.label), E('td', {}, row.amount.exact), E('td', {}, data.unit)))));
      return E('section', { class: 'ratio-panel' }, E('h4', {}, data.title), E('p', {}, 'Axis unit: ' + data.unit + '. Every bar starts at zero.'), E('div', { class: 'ratio-viewport', tabindex: '0', role: 'region', 'aria-label': data.title + ' scrollable diagram' }, svg), E('p', { class: 'ratio-chart-note' }, 'Bar lengths use the exact ratios on one linear axis within this chart. Tick text is rounded; the ledger gives exact values. Zero amounts are marked at the origin. Use horizontal scrolling on a small screen.'), E('div', { class: 'ratio-table' }, table));
    }
    function refresh() {
      operation.value = state.mode; error.textContent = ''; output.replaceChildren();
      output.append(E('h4', {}, titles[state.mode]), E('p', { class: 'ratio-accepted' }, 'Accepted inputs: ' + c.fields[state.mode].map(([k, label]) => label + ' = ' + model.inputs[k].exact).join('; ')));
      if (model.status === 'undefined') output.append(E('p', { class: 'ratio-undefined' }, model.reason));
      else {
        output.append(E('ol', { class: 'ratio-steps' }, model.steps.map(s => E('li', {}, s))));
        if (state.mode === 'scale') output.append(E('p', { class: 'ratio-equation' }, model.inputs.a.exact + ' : ' + model.inputs.b.exact + ' → ' + model.resultA.exact + ' : ' + model.resultB.exact + '. Total = ' + model.total.exact + '.'));
        for (let i = 0; i < model.charts.length; i++) output.append(chart(model.charts[i], i));
        output.append(E('p', { class: 'ratio-note' }, model.note));
      }
      size();
    }
    function size() { root.classList.toggle('ratio-enlarged', enlarged); zoom.textContent = enlarged ? 'Fit diagrams' : 'Enlarge diagrams'; zoom.setAttribute('aria-pressed', String(enlarged)); }
    operation.addEventListener('change', () => { state = c.defaults(operation.value); model = c.build(state); preset.value = ''; createControls(); refresh(); });
    preset.addEventListener('change', () => { const p = presets.find(p => p[0] === preset.value); if (!p) return; state = { ...c.defaults(p[2].mode), ...p[2] }; model = c.build(state); createControls(); refresh(); });
    reset.onclick = () => { state = c.defaults(); model = c.build(state); enlarged = false; preset.value = ''; createControls(); refresh(); };
    zoom.onclick = () => { enlarged = !enlarged; size(); };
    root.getModelSpeech = () => titles[state.mode] + '. ' + [...output.querySelectorAll('p,li,caption,th,td')].map(n => n.textContent).join(' ');
    root.ratioModel = () => model;
    if (hooks.speakButton) heading.prepend(hooks.speakButton(root.getModelSpeech, 'Read this activity aloud'));
    createControls(); refresh(); return root;
  }
  const api = Object.freeze({ render, presets, titles });
  if (host) host.PrimerRatioLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window === 'undefined' ? null : window);
