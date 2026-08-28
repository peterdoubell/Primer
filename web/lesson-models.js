/* The Primer's small, local lesson manipulatives.
   These models explain an idea; they never call the API or award mastery. */
(function () {
  'use strict';

  const SVG_NS = 'http://www.w3.org/2000/svg';
  let nextModelId = 0;

  function node(tag, attrs = {}, ...children) {
    const out = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (value == null || value === false) continue;
      if (key === 'class') out.className = value;
      else if (key.startsWith('on') && typeof value === 'function') out.addEventListener(key.slice(2), value);
      else if (value === true) out.setAttribute(key, '');
      else out.setAttribute(key, value);
    }
    for (const child of children) {
      if (child == null) continue;
      out.append(child.nodeType ? child : document.createTextNode(child));
    }
    return out;
  }

  function svgNode(tag, attrs = {}) {
    const out = document.createElementNS(SVG_NS, tag);
    for (const [key, value] of Object.entries(attrs)) out.setAttribute(key, value);
    return out;
  }

  function modelFrame(item, hooks) {
    const serial = ++nextModelId;
    const titleId = 'lesson-model-title-' + serial;
    const instructionsId = 'lesson-model-instructions-' + serial;
    const root = node('section', {
      class: 'card lesson-model',
      'aria-labelledby': titleId,
      'aria-describedby': instructionsId,
      'data-renderer': item.renderer,
    });
    const canvas = node('div', { class: 'model-canvas' });
    const controls = node('div', { class: 'model-controls' });
    const readout = node('p', { class: 'model-readout' });
    // This starts empty so a screen reader hears it only after the reader acts.
    const status = node('p', {
      class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true',
    });
    const heading = node('div', { class: 'model-heading-row' },
      node('h3', { id: titleId }, item.title));
    root.append(
      heading,
      node('p', { id: instructionsId, class: 'model-instructions' }, item.instructions),
      canvas, controls, readout, status,
    );
    if (hooks && typeof hooks.speakButton === 'function') {
      const spokenText = () => {
        const stepLabels = [...root.querySelectorAll('.sequence-step-label')]
          .map(label => label.textContent.trim()).filter(Boolean);
        const controlsText = [...new Set([...root.querySelectorAll('button:not(.speak-btn)')]
          .map(button => button.textContent.trim()).filter(Boolean))];
        return [item.title, item.instructions,
          stepLabels.length ? 'Current steps: ' + stepLabels.join(', ') + '.' : '',
          controlsText.length ? 'Controls: ' + controlsText.join(', ') + '.' : '',
          readout.textContent, status.textContent].filter(Boolean).join(' ');
      };
      heading.prepend(hooks.speakButton(spokenText, 'Read this activity aloud'));
    }
    return { root, canvas, controls, readout, status };
  }

  function clampNumber(value, low, high, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? Math.max(low, Math.min(high, parsed)) : fallback;
  }

  function renderCounter(item, hooks) {
    const frame = modelFrame(item, hooks);
    const total = Math.round(clampNumber((item.props || {}).total, 1, 20, 10));
    const counted = new Set();
    let mixed = false;
    const tray = node('div', {
      class: 'model-counter-scene', role: 'group',
      'aria-label': total + ' pebbles. Touch each pebble once as you count.',
    });
    const pebbles = [];

    function refreshPebbles() {
      pebbles.forEach((pebble, index) => {
        const isCounted = counted.has(index);
        pebble.classList.toggle('is-counted', isCounted);
        pebble.setAttribute('aria-pressed', isCounted ? 'true' : 'false');
        pebble.setAttribute('aria-label', 'Pebble ' + (index + 1) +
          (isCounted ? ', already counted' : ', not counted yet'));
      });
      frame.readout.textContent = counted.size + ' of ' + total + ' pebbles touched.';
    }

    for (let index = 0; index < total; index += 1) {
      const pebble = node('button', {
        type: 'button', class: 'model-pebble', 'aria-pressed': 'false',
        'aria-label': 'Pebble ' + (index + 1) + ', not counted yet',
        onclick: () => {
          if (counted.has(index)) {
            frame.status.textContent = 'That pebble already has its one number word.';
            return;
          }
          counted.add(index);
          refreshPebbles();
          frame.status.textContent = counted.size === total
            ? 'You touched every pebble once. The last number tells how many are in the whole set: ' + total + '.'
            : 'Counted ' + counted.size + '. Choose a pebble that has not been touched yet.';
        },
      }, node('span', { class: 'pebble-surface', 'aria-hidden': 'true' }));
      pebble.style.setProperty('--pebble-index', index);
      pebbles.push(pebble);
      tray.append(pebble);
    }

    const mixButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => {
        mixed = !mixed;
        tray.classList.toggle('is-mixed', mixed);
        mixButton.textContent = mixed ? 'Line them up' : 'Mix the same ' + total;
        frame.status.textContent = 'The same ' + total + ' pebbles moved. Their places changed; how many there are did not.';
      },
    }, 'Mix the same ' + total);
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        counted.clear();
        mixed = false;
        tray.classList.remove('is-mixed');
        mixButton.textContent = 'Mix the same ' + total;
        refreshPebbles();
        frame.status.textContent = 'Ready to count again. Give each pebble one number word.';
      },
    }, 'Reset');

    frame.canvas.classList.add('counter-canvas');
    frame.canvas.append(tray);
    frame.controls.append(node('div', { class: 'model-button-row counter-button-row' }, mixButton, resetButton));
    refreshPebbles();
    return frame.root;
  }

  const SHAPES = {
    circle: { label: 'Circle', sides: 'one curved edge', corners: 0 },
    triangle: { label: 'Triangle', sides: '3 straight sides', corners: 3 },
    square: { label: 'Square', sides: '4 equal straight sides', corners: 4 },
  };

  function renderShapeExplorer(item, hooks) {
    const frame = modelFrame(item, hooks);
    let selected = 'circle';
    let markCorners = false;
    const picture = svgNode('svg', {
      viewBox: '0 0 320 260', class: 'shape-model-svg', 'aria-hidden': 'true', focusable: 'false',
    });
    const optionRow = node('div', { class: 'model-option-row', role: 'group', 'aria-label': 'Choose a shape' });
    const optionButtons = {};
    const cornerButton = node('button', { type: 'button', class: 'btn small', 'aria-pressed': 'false' }, 'Show corners');

    function drawShape(announce) {
      picture.replaceChildren();
      picture.append(svgNode('rect', { x: 18, y: 18, width: 284, height: 224, rx: 18, class: 'shape-model-field' }));
      let shape;
      let corners = [];
      if (selected === 'circle') {
        shape = svgNode('circle', { cx: 160, cy: 130, r: 82, class: 'model-shape-line' });
      } else if (selected === 'triangle') {
        shape = svgNode('polygon', { points: '160,35 56,215 264,215', class: 'model-shape-line' });
        corners = [[160, 35], [56, 215], [264, 215]];
      } else {
        shape = svgNode('rect', { x: 62, y: 32, width: 196, height: 196, rx: 2, class: 'model-shape-line' });
        corners = [[62, 32], [258, 32], [258, 228], [62, 228]];
      }
      picture.append(shape);
      if (markCorners) {
        corners.forEach(([cx, cy]) => picture.append(svgNode('circle', { cx, cy, r: 9, class: 'shape-corner' })));
      }
      Object.entries(optionButtons).forEach(([name, button]) => {
        const active = name === selected;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      const facts = SHAPES[selected];
      frame.readout.textContent = facts.label + ' · ' + facts.sides + ' · ' + facts.corners +
        (facts.corners === 1 ? ' corner' : ' corners');
      if (announce) {
        frame.status.textContent = facts.label + ': ' + facts.sides + ' and ' + facts.corners +
          (facts.corners === 1 ? ' corner.' : ' corners.');
      }
    }

    Object.entries(SHAPES).forEach(([name, facts]) => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => { selected = name; drawShape(true); },
      }, facts.label);
      optionButtons[name] = button;
      optionRow.append(button);
    });
    cornerButton.addEventListener('click', () => {
      markCorners = !markCorners;
      cornerButton.setAttribute('aria-pressed', markCorners ? 'true' : 'false');
      cornerButton.textContent = markCorners ? 'Hide corners' : 'Show corners';
      drawShape(false);
      frame.status.textContent = selected === 'circle'
        ? 'A circle has no corners to mark. Its edge curves all the way around.'
        : (markCorners ? 'Corner marks are on.' : 'Corner marks are off.') + ' Count where two sides meet.';
    });
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        selected = 'circle'; markCorners = false;
        cornerButton.setAttribute('aria-pressed', 'false');
        cornerButton.textContent = 'Show corners';
        drawShape(false);
        frame.status.textContent = 'Back to the circle.';
      },
    }, 'Reset');

    frame.canvas.classList.add('shape-canvas');
    frame.canvas.append(picture);
    frame.controls.append(optionRow, node('div', { class: 'model-button-row' }, cornerButton, resetButton));
    drawShape(false);
    return frame.root;
  }

  function renderShadowLab(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const start = Math.round(clampNumber(props.start_position, 0, 100, 45));
    let lampOn = true;
    const picture = svgNode('svg', {
      viewBox: '0 0 640 280', class: 'shadow-model-svg', 'aria-hidden': 'true', focusable: 'false',
    });
    const field = svgNode('rect', { x: 8, y: 8, width: 624, height: 264, rx: 18, class: 'shadow-model-field' });
    const table = svgNode('line', { x1: 24, y1: 220, x2: 612, y2: 220, class: 'shadow-table-line' });
    const glow = svgNode('circle', { cx: 60, cy: 140, r: 32, class: 'shadow-lamp-glow' });
    const lamp = svgNode('g', { class: 'shadow-lamp' });
    lamp.append(
      svgNode('circle', { cx: 60, cy: 140, r: 13 }),
      svgNode('line', { x1: 60, y1: 153, x2: 60, y2: 210 }),
      svgNode('line', { x1: 40, y1: 218, x2: 80, y2: 218 }),
    );
    const topRay = svgNode('line', { class: 'shadow-ray' });
    const bottomRay = svgNode('line', { class: 'shadow-ray' });
    const blocker = svgNode('g', { class: 'shadow-blocker' });
    // A plain opaque card keeps the projection honest: its top and bottom are
    // exactly the two boundary points used to calculate the cast rectangle.
    blocker.append(svgNode('rect', { x: -16, y: 100, width: 32, height: 80, rx: 5 }));
    const screen = svgNode('rect', { x: 575, y: 20, width: 36, height: 232, rx: 5, class: 'shadow-screen' });
    const shadow = svgNode('rect', { x: 584, width: 18, rx: 9, class: 'shadow-cast' });
    picture.append(field, glow, topRay, bottomRay, table, screen, shadow, lamp, blocker);

    const sliderId = 'shadow-position-' + nextModelId;
    const slider = node('input', {
      id: sliderId, type: 'range', min: 0, max: 100, step: 1, value: start,
      'aria-valuetext': start + ' of 100, about halfway',
    });
    const sliderLabel = node('label', { class: 'model-slider', for: sliderId },
      node('span', { class: 'model-slider-title' }, 'Move the blocker'), slider,
      node('span', { class: 'model-slider-ends', 'aria-hidden': 'true' },
        node('span', {}, 'Near lamp'), node('span', {}, 'Near screen')),
    );
    // This is an action button rather than a persistent toggle control, so its
    // changing label supplies the complete instruction without a conflicting
    // pressed/not-pressed announcement.
    const lampButton = node('button', { type: 'button', class: 'btn small' }, 'Turn lamp off');

    function positionWords(value) {
      if (value < 34) return 'nearer the lamp';
      if (value > 66) return 'nearer the screen';
      return 'about halfway';
    }

    function updateShadow(announce) {
      const value = Number(slider.value);
      const objectX = 245 + value * 2.25;
      const sourceX = 60;
      const sourceY = 140;
      const screenX = 584;
      const scale = (screenX - sourceX) / (objectX - sourceX);
      const top = sourceY - 40 * scale;
      const height = 80 * scale;
      const size = height > 180 ? 'large' : height > 130 ? 'medium-sized' : 'small';
      blocker.setAttribute('transform', 'translate(' + objectX.toFixed(1) + ' 0)');
      topRay.setAttribute('x1', sourceX); topRay.setAttribute('y1', sourceY);
      topRay.setAttribute('x2', screenX); topRay.setAttribute('y2', top.toFixed(1));
      bottomRay.setAttribute('x1', sourceX); bottomRay.setAttribute('y1', sourceY);
      bottomRay.setAttribute('x2', screenX); bottomRay.setAttribute('y2', (top + height).toFixed(1));
      shadow.setAttribute('y', top.toFixed(1));
      shadow.setAttribute('height', height.toFixed(1));
      [glow, topRay, bottomRay, shadow].forEach(part => { part.style.display = lampOn ? '' : 'none'; });
      picture.classList.toggle('is-lamp-off', !lampOn);
      slider.style.setProperty('--range-fill', value + '%');
      const place = positionWords(value);
      slider.setAttribute('aria-valuetext', value + ' of 100, ' + place);
      frame.readout.textContent = lampOn
        ? 'Lamp on · blocker ' + place + ' · ' + size + ' shadow'
        : 'Lamp off · no cast shadow';
      if (announce) {
        frame.status.textContent = lampOn
          ? 'The blocker is ' + place + ', so its shadow on the screen is ' + size + '.'
          : 'The lamp is off. With no light reaching the screen, this setup makes no shadow.';
      }
    }

    slider.addEventListener('input', () => updateShadow(true));
    lampButton.addEventListener('click', () => {
      lampOn = !lampOn;
      lampButton.textContent = lampOn ? 'Turn lamp off' : 'Turn lamp on';
      updateShadow(true);
    });
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        lampOn = true; slider.value = String(start);
        lampButton.textContent = 'Turn lamp off';
        updateShadow(false);
        frame.status.textContent = 'The lamp and blocker are back where they started.';
      },
    }, 'Reset');

    frame.canvas.classList.add('shadow-canvas');
    frame.canvas.append(picture);
    frame.controls.append(sliderLabel, node('div', { class: 'model-button-row' }, lampButton, resetButton));
    updateShadow(false);
    return frame.root;
  }

  function runPackBag(order) {
    let bagOpen = false;
    let bookInside = false;
    let carried = false;
    for (let index = 0; index < order.length; index += 1) {
      const command = order[index];
      let problem = '';
      if (command === 'open') {
        if (bagOpen) problem = 'the bag is already open';
        else bagOpen = true;
      } else if (command === 'book') {
        if (!bagOpen) problem = 'the bag is closed, so the book cannot go in';
        else if (bookInside) problem = 'the book is already inside';
        else bookInside = true;
      } else if (command === 'close') {
        if (!bagOpen) problem = 'the bag is already closed';
        else bagOpen = false;
      } else if (command === 'carry') {
        if (bagOpen) problem = 'the bag is still open';
        else if (!bookInside) problem = 'the book is not inside yet';
        else carried = true;
      } else {
        problem = 'that instruction is not part of this task';
      }
      if (problem) {
        return {
          progress: index,
          success: false,
          message: 'Step ' + (index + 1) + ' could not run: ' + problem + '.',
        };
      }
    }
    return carried && bookInside && !bagOpen
      ? { progress: order.length, success: true,
        message: 'It worked. Each step prepared the next one, and the bag is ready to carry.' }
      : { progress: order.length, success: false,
        message: 'Those steps ran, but the packed bag is not ready to carry yet.' };
  }

  function renderSequenceRunner(item, hooks) {
    const frame = modelFrame(item, hooks);
    const steps = [
      { id: 'open', label: 'Open the bag' },
      { id: 'book', label: 'Put the book in' },
      { id: 'close', label: 'Close the bag' },
      { id: 'carry', label: 'Carry the bag' },
    ];
    const byId = Object.fromEntries(steps.map(step => [step.id, step]));
    const startOrder = ['close', 'open', 'carry', 'book'];
    let order = startOrder.slice();
    const list = node('ol', { class: 'model-sequence-list', 'aria-label': 'Steps to put in order' });
    const rows = {};
    const track = node('div', { class: 'sequence-track', 'aria-hidden': 'true' });
    const tiles = [];
    for (let index = 0; index < 4; index += 1) {
      const tile = node('span', { class: 'sequence-tile' });
      tiles.push(tile); track.append(tile);
    }
    const marker = node('span', { class: 'sequence-beetle' });
    const goal = node('span', { class: 'sequence-goal' });
    track.append(marker, goal);

    function paintProgress(progress) {
      tiles.forEach((tile, index) => tile.classList.toggle('is-passed', index < progress));
      marker.style.left = (4 + progress * 21.5) + '%';
      frame.readout.textContent = progress === 4
        ? 'All four steps ran in order. The packed bag is ready.'
        : progress === 0 ? 'The runner is waiting at the start.'
          : progress + ' of 4 steps ran before the sequence stopped.';
    }

    function refreshList() {
      order.forEach((id, index) => {
        const row = rows[id];
        row.earlier.disabled = index === 0;
        row.later.disabled = index === order.length - 1;
        list.append(row.element);
      });
      paintProgress(0);
    }

    function move(id, delta) {
      const from = order.indexOf(id);
      const to = from + delta;
      if (to < 0 || to >= order.length) return;
      [order[from], order[to]] = [order[to], order[from]];
      refreshList();
      // Re-appending an existing row preserves its state but some engines
      // release focus while moving it. Put focus back on the same action, or
      // on its counterpart when the action has just reached that edge.
      const own = delta < 0 ? rows[id].earlier : rows[id].later;
      const counterpart = delta < 0 ? rows[id].later : rows[id].earlier;
      (own.disabled ? counterpart : own).focus();
      frame.status.textContent = 'Moved “' + byId[id].label + '” ' + (delta < 0 ? 'earlier' : 'later') +
        '. Run the steps when the order looks right.';
    }

    steps.forEach(step => {
      const earlier = node('button', {
        type: 'button', class: 'btn ghost small model-move',
        'aria-label': 'Move ' + step.label + ' earlier',
        onclick: () => move(step.id, -1),
      }, 'Earlier');
      const later = node('button', {
        type: 'button', class: 'btn ghost small model-move',
        'aria-label': 'Move ' + step.label + ' later',
        onclick: () => move(step.id, 1),
      }, 'Later');
      const element = node('li', { class: 'sequence-step', 'data-step-id': step.id },
        node('span', { class: 'sequence-step-label' }, step.label),
        node('span', { class: 'sequence-step-controls' }, earlier, later));
      rows[step.id] = { element, earlier, later };
    });

    const runButton = node('button', {
      type: 'button', class: 'btn gold', onclick: () => {
        const result = runPackBag(order);
        paintProgress(result.progress);
        frame.status.textContent = result.message;
      },
    }, 'Run the steps');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost', onclick: () => {
        order = startOrder.slice();
        refreshList();
        frame.status.textContent = 'The steps are mixed up again.';
      },
    }, 'Mix them again');

    frame.canvas.classList.add('sequence-canvas');
    frame.canvas.append(track);
    frame.controls.append(list, node('div', { class: 'model-button-row' }, runButton, resetButton));
    refreshList();
    return frame.root;
  }

  const RENDERERS = Object.freeze({
    counter: renderCounter,
    'shape-explorer': renderShapeExplorer,
    'shadow-lab': renderShadowLab,
    'sequence-runner': renderSequenceRunner,
  });

  window.PrimerLessonModels = Object.freeze({
    render(item, hooks) {
      const renderer = item && RENDERERS[item.renderer];
      return renderer ? renderer(item, hooks) : null;
    },
    supported: Object.freeze(Object.keys(RENDERERS)),
  });
}());
