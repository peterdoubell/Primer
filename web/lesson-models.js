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
        const stepLabels = [...root.querySelectorAll('[data-model-speak]')]
          .map(label => label.getAttribute('aria-label') || label.textContent.trim()).filter(Boolean);
        const controlsText = [...new Set([...root.querySelectorAll('button:not(.speak-btn), input[type="range"]')]
          .map(control => control.getAttribute('aria-label') || control.getAttribute('aria-valuetext') ||
            control.textContent.trim()).filter(Boolean))];
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
        node('span', { class: 'sequence-step-label', 'data-model-speak': true }, step.label),
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

  function renderMakeTen(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const first = Math.round(clampNumber(props.first, 1, 9, 8));
    const second = Math.round(clampNumber(props.second, 1, 9, 5));
    let moved = 0;
    let swapped = false;
    const board = node('div', { class: 'make-ten-scene', 'aria-hidden': 'true' });
    const tenFrame = node('div', { class: 'make-ten-frame' });
    const bank = node('div', { class: 'make-ten-bank' });
    board.append(tenFrame, bank);

    function values() {
      return swapped
        ? { base: second, add: first, baseClass: 'is-green', addClass: 'is-blue' }
        : { base: first, add: second, baseClass: 'is-blue', addClass: 'is-green' };
    }

    const moveButton = node('button', { type: 'button', class: 'btn small' }, 'Move one into the ten-frame');
    const swapButton = node('button', { type: 'button', class: 'btn ghost small' }, 'Swap addends');
    const resetButton = node('button', { type: 'button', class: 'btn ghost small' }, 'Reset');

    function refresh(announce) {
      const current = values();
      const needed = 10 - current.base;
      const left = current.add - moved;
      tenFrame.replaceChildren();
      bank.replaceChildren();
      for (let index = 0; index < 10; index += 1) {
        let counterClass = '';
        if (index < current.base) counterClass = current.baseClass;
        else if (index < current.base + moved) counterClass = current.addClass;
        tenFrame.append(node('span', { class: 'make-ten-cell' },
          counterClass ? node('span', { class: 'make-ten-counter ' + counterClass }) : null));
      }
      for (let index = 0; index < left; index += 1) {
        bank.append(node('span', { class: 'make-ten-counter ' + current.addClass }));
      }
      moveButton.disabled = moved >= needed;
      frame.readout.textContent = moved >= needed
        ? current.base + ' + ' + current.add + ' = 10 + ' + left + ' = ' + (current.base + current.add) + '.'
        : current.base + ' + ' + current.add + ' = ' + (current.base + current.add) +
          '. The ten-frame has ' + (current.base + moved) + '; ' + left + ' counters are waiting.';
      if (announce) {
        frame.status.textContent = moved >= needed
          ? 'The ten-frame is full. ' + left + ' counters remain, so the total is ten plus ' + left + '.'
          : 'Moved one counter. The frame now holds ' + (current.base + moved) + '.';
      }
    }

    moveButton.addEventListener('click', () => {
      const current = values();
      if (moved < 10 - current.base) moved += 1;
      refresh(true);
    });
    swapButton.addEventListener('click', () => {
      swapped = !swapped;
      moved = 0;
      refresh(false);
      const current = values();
      frame.status.textContent = 'The addends swapped places: ' + current.base + ' + ' + current.add +
        '. Their total is still ' + (current.base + current.add) + '.';
    });
    resetButton.addEventListener('click', () => {
      swapped = false;
      moved = 0;
      refresh(false);
      frame.status.textContent = 'The counters are back at the start. Fill the friendly ten again.';
    });

    frame.canvas.classList.add('make-ten-canvas');
    frame.canvas.append(board);
    frame.controls.append(node('div', { class: 'model-button-row' }, moveButton, swapButton, resetButton));
    refresh(false);
    return frame.root;
  }

  const LIGHT_PATHS = {
    prism: {
      label: 'Prism',
      readout: 'Prism · white light bends and spreads into a continuous range of colours.',
      status: 'A prism separates colours already present in white light; it does not paint the light.',
    },
    mirror: {
      label: 'Mirror',
      readout: 'Mirror · incoming and reflected light leave at matching angles.',
      status: 'A smooth mirror sends reflected light in an orderly direction. An eye sees the image only when that light reaches it.',
    },
    toy: {
      label: 'Toy',
      readout: 'Toy · light scatters in many directions, and a small part reaches the eye.',
      status: 'An ordinary object is visible when light from a source reflects from it into an eye.',
    },
  };

  function renderLightPaths(item, hooks) {
    const frame = modelFrame(item, hooks);
    let selected = 'prism';
    const picture = svgNode('svg', {
      viewBox: '0 0 640 280', class: 'light-path-svg', 'aria-hidden': 'true', focusable: 'false',
    });
    const optionButtons = {};
    const optionRow = node('div', { class: 'model-option-row', role: 'group', 'aria-label': 'Choose what light meets' });

    function lampParts() {
      return [
        svgNode('circle', { cx: 64, cy: 140, r: 25, class: 'light-source-glow' }),
        svgNode('circle', { cx: 64, cy: 140, r: 11, class: 'light-source' }),
        svgNode('line', { x1: 64, y1: 151, x2: 64, y2: 222, class: 'light-stand' }),
      ];
    }

    function whiteRay(x1, y1, x2, y2) {
      const geometry = { x1, y1, x2, y2 };
      return [
        svgNode('line', { ...geometry, class: 'light-white-ray-outline' }),
        svgNode('line', { ...geometry, class: 'light-white-ray' }),
      ];
    }

    function draw(announce) {
      picture.replaceChildren();
      picture.append(svgNode('rect', { x: 8, y: 8, width: 624, height: 264, rx: 18, class: 'light-path-field' }));
      lampParts().forEach(part => picture.append(part));
      if (selected === 'prism') {
        const gradientId = 'lesson-spectrum-' + nextModelId;
        const defs = svgNode('defs');
        const gradient = svgNode('linearGradient', { id: gradientId, x1: '0%', y1: '0%', x2: '0%', y2: '100%' });
        [['0%', '#d95842'], ['18%', '#e79732'], ['36%', '#e8c94d'], ['54%', '#6fae66'],
          ['72%', '#4f8fbd'], ['100%', '#755a9d']].forEach(([offset, color]) =>
          gradient.append(svgNode('stop', { offset, 'stop-color': color })));
        defs.append(gradient);
        picture.append(defs,
          ...whiteRay(78, 140, 288, 140),
          svgNode('polygon', { points: '320,58 270,222 370,222', class: 'light-prism' }),
          svgNode('polygon', { points: '342,140 604,150 604,238', fill: 'url(#' + gradientId + ')', class: 'light-spectrum' }),
          svgNode('rect', { x: 604, y: 38, width: 16, height: 214, rx: 4, class: 'light-screen' }));
      } else if (selected === 'mirror') {
        picture.append(
          ...whiteRay(78, 140, 320, 220),
          svgNode('line', { x1: 320, y1: 220, x2: 562, y2: 140, class: 'light-reflected-ray' }),
          svgNode('line', { x1: 224, y1: 220, x2: 416, y2: 220, class: 'light-mirror' }),
          svgNode('line', { x1: 320, y1: 164, x2: 320, y2: 262, class: 'light-normal' }),
          svgNode('path', { d: 'M548 140 Q566 124 584 140 Q566 156 548 140 Z', class: 'light-eye' }),
          svgNode('circle', { cx: 566, cy: 140, r: 5, class: 'light-pupil' }));
      } else {
        picture.append(
          ...whiteRay(78, 140, 304, 140),
          svgNode('rect', { x: 304, y: 98, width: 76, height: 84, rx: 17, class: 'light-toy' }),
          svgNode('line', { x1: 380, y1: 140, x2: 552, y2: 82, class: 'light-reflected-ray' }),
          svgNode('line', { x1: 380, y1: 140, x2: 520, y2: 150, class: 'light-scatter-ray' }),
          svgNode('line', { x1: 380, y1: 140, x2: 500, y2: 228, class: 'light-scatter-ray' }),
          svgNode('path', { d: 'M540 82 Q558 66 576 82 Q558 98 540 82 Z', class: 'light-eye' }),
          svgNode('circle', { cx: 558, cy: 82, r: 5, class: 'light-pupil' }));
      }
      Object.entries(optionButtons).forEach(([name, button]) => {
        const active = name === selected;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      frame.readout.textContent = LIGHT_PATHS[selected].readout;
      if (announce) frame.status.textContent = LIGHT_PATHS[selected].status;
    }

    Object.entries(LIGHT_PATHS).forEach(([name, detail]) => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => { selected = name; draw(true); },
      }, detail.label);
      optionButtons[name] = button;
      optionRow.append(button);
    });
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        selected = 'prism';
        draw(false);
        frame.status.textContent = 'Back to the prism and white light.';
      },
    }, 'Reset');

    frame.canvas.classList.add('light-path-canvas');
    frame.canvas.append(picture);
    frame.controls.append(optionRow, node('div', { class: 'model-button-row' }, resetButton));
    draw(false);
    return frame.root;
  }

  function traceJamSandwich(included) {
    let bread = false;
    let jam = false;
    let closed = false;
    let served = false;
    const ranStepIds = [];
    const commands = ['bread', 'jam', 'close', 'serve'];
    for (let index = 0; index < commands.length; index += 1) {
      const command = commands[index];
      if (!included.has(command)) continue;
      let problem = '';
      if (command === 'bread') bread = true;
      else if (command === 'jam') {
        if (!bread) problem = 'there is no bread to spread jam on';
        else jam = true;
      } else if (command === 'close') {
        if (!bread) problem = 'there are no bread slices to put together';
        else if (!jam) problem = 'the jam step was left out';
        else closed = true;
      } else if (command === 'serve') {
        if (!closed) problem = 'the sandwich is not put together yet';
        else served = true;
      }
      if (problem) return { ranStepIds, stoppedAt: index, success: false,
        message: 'Step ' + (index + 1) + ' stopped: ' + problem + '.' };
      ranStepIds.push(command);
    }
    return served && jam
      ? { ranStepIds, stoppedAt: null, success: true,
        message: 'The algorithm worked: every necessary step ran in a usable order.' }
      : { ranStepIds, stoppedAt: null, success: false,
        message: 'The listed steps finished, but they did not produce a served jam sandwich.' };
  }

  function renderAlgorithmTracer(item, hooks) {
    const frame = modelFrame(item, hooks);
    const steps = [
      { id: 'bread', label: 'Get two bread slices' },
      { id: 'jam', label: 'Spread jam on one slice' },
      { id: 'close', label: 'Put the slices together' },
      { id: 'serve', label: 'Serve the sandwich' },
    ];
    const included = new Set(steps.map(step => step.id));
    const list = node('ol', { class: 'algorithm-step-list', 'aria-label': 'Sandwich algorithm steps' });
    const track = node('div', { class: 'algorithm-track', 'aria-hidden': 'true' });
    const tiles = [];
    const buttons = {};
    steps.forEach(() => {
      const tile = node('span', { class: 'algorithm-tile' });
      tiles.push(tile);
      track.append(tile);
    });

    function selectionSummary() {
      const leftOut = steps.filter(step => !included.has(step.id)).map(step => step.label);
      return included.size + ' of 4 necessary steps ' + (included.size === 1 ? 'is' : 'are') + ' included. ' +
        (leftOut.length ? 'Left out: ' + leftOut.join('; ') + '.' : 'No steps are left out.');
    }

    function resetProgress() {
      tiles.forEach((tile, index) => {
        tile.classList.remove('is-passed');
        tile.classList.toggle('is-omitted', !included.has(steps[index].id));
      });
      frame.readout.textContent = selectionSummary();
    }

    steps.forEach((step, index) => {
      const toggle = node('button', {
        type: 'button', class: 'btn ghost small algorithm-toggle',
        'aria-label': 'Include step: ' + step.label, 'aria-pressed': 'true',
        onclick: () => {
          if (included.has(step.id)) included.delete(step.id);
          else included.add(step.id);
          const active = included.has(step.id);
          toggle.setAttribute('aria-pressed', active ? 'true' : 'false');
          toggle.textContent = active ? 'Included' : 'Left out';
          resetProgress();
          frame.status.textContent = 'Step ' + (index + 1) + ', “' + step.label + '”, is now ' +
            (active ? 'included.' : 'left out. Run the algorithm to see the consequence.');
        },
      }, 'Included');
      buttons[step.id] = toggle;
      list.append(node('li', { class: 'algorithm-step' },
        node('span', { class: 'algorithm-step-label', 'data-model-speak': true }, step.label), toggle));
    });

    const runButton = node('button', {
      type: 'button', class: 'btn gold', onclick: () => {
        const result = traceJamSandwich(included);
        tiles.forEach((tile, index) => tile.classList.toggle('is-passed', result.ranStepIds.includes(steps[index].id)));
        const ranCount = result.ranStepIds.length;
        frame.readout.textContent = result.success
          ? 'All four included steps ran. The jam sandwich is served. No steps are left out.'
          : ranCount + ' included ' + (ranCount === 1 ? 'step ran. ' : 'steps ran. ') +
            (result.stoppedAt == null ? 'The algorithm ended incomplete. ' :
              'Step ' + (result.stoppedAt + 1) + ' stopped. ') + selectionSummary();
        frame.status.textContent = result.message;
      },
    }, 'Run the algorithm');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost', onclick: () => {
        steps.forEach(step => {
          included.add(step.id);
          buttons[step.id].setAttribute('aria-pressed', 'true');
          buttons[step.id].textContent = 'Included';
        });
        resetProgress();
        frame.status.textContent = 'All four necessary steps are included again.';
      },
    }, 'Reset');

    frame.canvas.classList.add('algorithm-canvas');
    frame.canvas.append(track);
    frame.controls.append(list, node('div', { class: 'model-button-row' }, runButton, resetButton));
    resetProgress();
    return frame.root;
  }

  const LIFE_CYCLES = {
    frog: {
      label: 'Frog',
      stages: [
        ['Eggs', 'Jelly-coated eggs develop underwater.'],
        ['Tadpole', 'A legless tadpole swims with its tail.'],
        ['Froglet', 'A froglet has four legs and a shrinking tail.'],
        ['Adult frog', 'An adult has no tail; adults can produce the next eggs.'],
      ],
      change: 'Frogs undergo metamorphosis: their body form changes greatly as they develop.',
    },
    butterfly: {
      label: 'Butterfly',
      stages: [
        ['Egg', 'An adult lays an egg on a suitable plant.'],
        ['Caterpillar', 'The feeding larva grows and sheds its skin.'],
        ['Chrysalis', 'Inside the pupa, the body reorganises.'],
        ['Adult butterfly', 'The winged adult can lay eggs for a new generation.'],
      ],
      change: 'Butterflies also undergo metamorphosis, including a pupal chrysalis stage.',
    },
    dog: {
      label: 'Dog',
      stages: [
        ['Newborn puppy', 'A newborn is small and depends on its mother.'],
        ['Growing puppy', 'Its body and proportions change gradually.'],
        ['Young dog', 'The young dog continues growing and learning.'],
        ['Adult dog', 'Adults can produce puppies for a new generation.'],
      ],
      change: 'Dogs grow gradually without metamorphosis, but every generation still has a life cycle.',
    },
  };

  function renderLifeCycle(item, hooks) {
    const frame = modelFrame(item, hooks);
    let species = 'frog';
    let stageIndex = 0;
    const cycle = node('ol', { class: 'life-cycle-ring', 'aria-label': 'Stages in the selected life cycle' });
    const speciesButtons = {};
    const speciesRow = node('div', { class: 'model-option-row', role: 'group', 'aria-label': 'Choose an animal' });

    function refresh(announce) {
      const detail = LIFE_CYCLES[species];
      cycle.replaceChildren();
      detail.stages.forEach(([label], index) => {
        const active = index === stageIndex;
        cycle.append(node('li', {
          class: 'life-cycle-stage', 'aria-current': active ? 'step' : null,
        }, node('div', {
          class: 'life-cycle-stage-card' + (active ? ' is-current' : ''),
        }, node('span', { class: 'life-cycle-number', 'aria-hidden': 'true' }, String(index + 1)),
        node('span', { 'data-model-speak': true }, label))));
      });
      Object.entries(speciesButtons).forEach(([name, button]) => {
        const active = name === species;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      const current = detail.stages[stageIndex];
      frame.readout.textContent = detail.label + ' · stage ' + (stageIndex + 1) + ' of 4 · ' +
        current[0] + '. ' + current[1] + ' ' + detail.change;
      if (announce) {
        frame.status.textContent = current[0] + '. ' + current[1] +
          (stageIndex === 3 ? ' The cycle continues into a new generation.' : ' Next comes ' + detail.stages[stageIndex + 1][0] + '.');
      }
    }

    Object.entries(LIFE_CYCLES).forEach(([name, detail]) => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => {
          species = name;
          stageIndex = 0;
          refresh(false);
          frame.status.textContent = detail.label + ' selected. This diagram starts with ' + detail.stages[0][0] + '.';
        },
      }, detail.label);
      speciesButtons[name] = button;
      speciesRow.append(button);
    });
    const nextButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => {
        const previous = stageIndex;
        stageIndex = (stageIndex + 1) % 4;
        refresh(false);
        const detail = LIFE_CYCLES[species];
        const current = detail.stages[stageIndex];
        const newBeginning = species === 'frog' ? 'egg cluster' : species === 'dog' ? 'puppy' : 'egg';
        frame.status.textContent = previous === 3
          ? 'Adults reproduce and a new ' + newBeginning +
            ' begins the next generation. The adult does not turn back into the young stage.'
          : current[0] + '. ' + current[1] +
            (stageIndex === 3 ? ' The next transition is reproduction into a new generation.'
              : ' Next comes ' + detail.stages[stageIndex + 1][0] + '.');
      },
    }, 'Next stage');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        species = 'frog';
        stageIndex = 0;
        refresh(false);
        frame.status.textContent = 'Back to frog eggs, where this diagram starts.';
      },
    }, 'Reset');

    frame.canvas.classList.add('life-cycle-canvas');
    frame.canvas.append(cycle);
    frame.controls.append(speciesRow, node('div', { class: 'model-button-row' }, nextButton, resetButton));
    refresh(false);
    return frame.root;
  }

  function renderFractionEquivalence(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const numerator = Math.round(clampNumber(props.numerator, 1, 7, 2));
    const denominator = Math.round(clampNumber(props.denominator, 2, 8, 3));
    const maxFactor = Math.round(clampNumber(props.max_factor, 2, 4, 4));
    let factor = 1;
    const board = node('div', { class: 'fraction-equivalence-board', 'aria-hidden': 'true' });
    const reference = node('div', { class: 'fraction-row' },
      node('b', {}, 'Original whole'), node('div', { class: 'fraction-bar' }));
    const transformed = node('div', { class: 'fraction-row' },
      node('b', {}, 'Same whole, split again'), node('div', { class: 'fraction-bar' }));
    const equation = node('div', { class: 'fraction-equation' });
    const factorButtons = {};
    const optionRow = node('div', {
      class: 'model-option-row', role: 'group', 'aria-label': 'Choose how many pieces replace each original part',
    });

    function fillBar(bar, shaded, parts) {
      bar.replaceChildren();
      bar.style.setProperty('--fraction-parts', parts);
      for (let index = 0; index < parts; index += 1) {
        bar.append(node('span', { class: 'fraction-piece' + (index < shaded ? ' is-shaded' : '') }));
      }
    }

    function refresh(announce) {
      const newNumerator = numerator * factor;
      const newDenominator = denominator * factor;
      fillBar(reference.lastElementChild, numerator, denominator);
      fillBar(transformed.lastElementChild, newNumerator, newDenominator);
      equation.textContent = numerator + '/' + denominator + ' = ' + newNumerator + '/' + newDenominator;
      Object.entries(factorButtons).forEach(([value, button]) => {
        const active = Number(value) === factor;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      frame.readout.textContent = numerator + '/' + denominator + ' = ' + newNumerator + '/' + newDenominator +
        '. That is ' + numerator + ' over ' + denominator + ' equals ' + newNumerator + ' over ' + newDenominator +
        '. The whole and shaded amount stay the same; only the number and names of equal pieces change.';
      if (announce) {
        frame.status.textContent = factor === 1
          ? 'Back to the original equal parts. Both bars name the same fraction in the same way.'
          : 'Each original part was split into ' + factor + ' equal pieces. The shaded amount did not change.';
      }
    }

    for (let value = 1; value <= maxFactor; value += 1) {
      const label = value === 1 ? 'Original' : 'Split each part into ' + value;
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => { factor = value; refresh(true); },
      }, label);
      factorButtons[value] = button;
      optionRow.append(button);
    }
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        factor = 1;
        refresh(false);
        frame.status.textContent = 'The bars are back to the original partition.';
      },
    }, 'Reset');

    board.append(reference, transformed, equation);
    frame.canvas.classList.add('fraction-equivalence-canvas');
    frame.canvas.append(board);
    frame.controls.append(optionRow, node('div', { class: 'model-button-row' }, resetButton));
    refresh(false);
    return frame.root;
  }

  const FIRST_TEN_ELEMENTS = [null,
    { symbol: 'H', name: 'hydrogen' }, { symbol: 'He', name: 'helium' },
    { symbol: 'Li', name: 'lithium' }, { symbol: 'Be', name: 'beryllium' },
    { symbol: 'B', name: 'boron' }, { symbol: 'C', name: 'carbon' },
    { symbol: 'N', name: 'nitrogen' }, { symbol: 'O', name: 'oxygen' },
    { symbol: 'F', name: 'fluorine' }, { symbol: 'Ne', name: 'neon' },
  ];

  function renderAtomElementBuilder(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const authored = {
      protons: Math.round(clampNumber(props.protons, 1, 10, 6)),
      neutrons: Math.round(clampNumber(props.neutrons, 0, 12, 6)),
      electrons: Math.round(clampNumber(props.electrons, 0, 10, 6)),
    };
    const values = { ...authored };
    const scene = node('div', { class: 'atom-builder-scene', 'aria-hidden': 'true' });
    const atom = node('div', { class: 'atom-diagram' });
    const nucleus = node('div', { class: 'atom-nucleus' });
    const symbol = node('strong', { class: 'atom-symbol' });
    const sceneLabel = node('span', { class: 'atom-scene-label' }, 'Schematic bookkeeping model · not to scale');
    const steppers = {};

    function chargeValue() {
      return values.protons - values.electrons;
    }

    function chargeText() {
      const charge = chargeValue();
      if (charge === 0) return 'neutral atom';
      return (charge > 0 ? '+' + charge : '−' + Math.abs(charge)) + ' ion';
    }

    function draw() {
      const element = FIRST_TEN_ELEMENTS[values.protons];
      atom.querySelectorAll('.atom-electron').forEach(electron => electron.remove());
      nucleus.replaceChildren();
      for (let index = 0; index < values.protons; index += 1) {
        nucleus.append(node('span', { class: 'nuclear-particle is-proton' }, 'p'));
      }
      for (let index = 0; index < values.neutrons; index += 1) {
        nucleus.append(node('span', { class: 'nuclear-particle is-neutron' }, 'n'));
      }
      for (let index = 0; index < values.electrons; index += 1) {
        const inner = index < 2;
        const place = inner ? index : index - 2;
        const count = inner ? Math.min(values.electrons, 2) : Math.max(values.electrons - 2, 1);
        const electron = node('span', { class: 'atom-electron' });
        electron.style.setProperty('--electron-angle', (360 * place / count) + 'deg');
        electron.style.setProperty('--electron-radius', inner ? '68px' : '91px');
        atom.append(electron);
      }
      symbol.textContent = element.symbol;
      Object.entries(steppers).forEach(([kind, controls]) => {
        const low = kind === 'protons' ? 1 : 0;
        const high = kind === 'neutrons' ? 12 : 10;
        controls.value.textContent = String(values[kind]);
        controls.remove.disabled = values[kind] <= low;
        controls.add.disabled = values[kind] >= high;
      });
      frame.readout.textContent = element.name[0].toUpperCase() + element.name.slice(1) + ' (' + element.symbol + ') · ' +
        values.protons + ' protons · ' + values.neutrons + ' neutrons · ' + values.electrons +
        ' electrons · mass number ' + (values.protons + values.neutrons) + ' · ' + chargeText() +
        '. Proton count defines the element. The rings organize electron counts; they are not paths that electrons orbit. ' +
        'This schematic bookkeeping model does not predict whether a nucleus or ion is stable.';
    }

    function change(kind, amount) {
      const before = FIRST_TEN_ELEMENTS[values.protons];
      values[kind] += amount;
      draw();
      const after = FIRST_TEN_ELEMENTS[values.protons];
      if (kind === 'protons') {
        frame.status.textContent = 'The proton count changed, so the element changed from ' + before.name + ' to ' +
          after.name + '. This is a hypothetical nuclear change, not an ordinary chemical reaction.';
      } else if (kind === 'neutrons') {
        frame.status.textContent = 'The neutron count changed. It is still ' + after.name + ', now with mass number ' +
          (values.protons + values.neutrons) + '.';
      } else {
        frame.status.textContent = 'The electron count changed. It is still ' + after.name + ', now a ' + chargeText() + '.';
      }
    }

    function stepper(kind, label) {
      const singular = label.endsWith('s') ? label.slice(0, -1).toLowerCase() : label.toLowerCase();
      const remove = node('button', {
        type: 'button', class: 'btn ghost small', 'aria-label': 'Remove one ' + singular,
        onclick: () => change(kind, -1),
      }, '−');
      const add = node('button', {
        type: 'button', class: 'btn ghost small', 'aria-label': 'Add one ' + singular,
        onclick: () => change(kind, 1),
      }, '+');
      const value = node('output', { class: 'atom-stepper-value', 'aria-label': label + ' count' });
      steppers[kind] = { remove, add, value };
      return node('div', { class: 'atom-stepper' }, node('b', {}, label),
        node('div', { class: 'atom-stepper-buttons' }, remove, value, add));
    }

    atom.append(node('span', { class: 'atom-shell is-inner' }),
      node('span', { class: 'atom-shell is-outer' }), nucleus, symbol);
    scene.append(atom, sceneLabel);
    const neutralButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => {
        values.electrons = values.protons;
        draw();
        frame.status.textContent = 'Electrons now equal protons, so the atom is electrically neutral.';
      },
    }, 'Make neutral');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        Object.assign(values, authored);
        draw();
        const element = FIRST_TEN_ELEMENTS[authored.protons];
        frame.status.textContent = 'The particle counts are back at the authored ' + element.name + '-' +
          (authored.protons + authored.neutrons) + ' example.';
      },
    }, 'Reset');

    frame.canvas.classList.add('atom-builder-canvas');
    frame.canvas.append(scene);
    frame.controls.append(node('div', { class: 'atom-stepper-grid' },
      stepper('protons', 'Protons'), stepper('neutrons', 'Neutrons'), stepper('electrons', 'Electrons')),
    node('div', { class: 'model-button-row' }, neutralButton, resetButton));
    draw();
    return frame.root;
  }

  const CELL_SPECIMENS = {
    onion: {
      label: 'Onion bulb epidermis', className: 'is-onion',
      structures: ['Cell wall', 'Cell membrane', 'Cytoplasm', 'Stained nucleus'],
      description: 'Cell walls and stained nuclei are visible; chloroplasts are not expected in bulb epidermis.',
    },
    leaf: {
      label: 'Green leaf', className: 'is-leaf',
      structures: ['Cell wall', 'Cell membrane', 'Cytoplasm', 'Chloroplasts', 'Nucleus'],
      description: 'Cell walls and many chloroplasts are visible in these photosynthetic cells.',
    },
    cheek: {
      label: 'Cheek', className: 'is-cheek',
      structures: ['Cell membrane', 'Cytoplasm', 'Stained nucleus'],
      description: 'Flattened irregular cells have membranes and nuclei, but no cell walls or chloroplasts.',
    },
  };

  function renderCellMicroscope(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const authoredSpecimen = CELL_SPECIMENS[props.start_specimen] ? props.start_specimen : 'onion';
    const authoredMagnification = [40, 100, 400].includes(Number(props.start_magnification))
      ? Number(props.start_magnification) : 100;
    let specimen = authoredSpecimen;
    let magnification = authoredMagnification;
    let contrast = false;
    let labels = false;
    const field = node('div', { class: 'microscope-field', 'aria-hidden': 'true' });
    const fieldNote = node('span', { class: 'microscope-field-note' }, 'Schematic microscope view');
    const legend = node('div', {
      class: 'microscope-legend', role: 'list', 'aria-label': 'Structures present in this specimen',
    });
    const specimenButtons = {};
    const magnificationButtons = {};
    const specimenRow = node('div', { class: 'model-option-row', role: 'group', 'aria-label': 'Choose a specimen' });
    const magnificationRow = node('div', {
      class: 'model-option-row', role: 'group', 'aria-label': 'Choose total magnification',
    });
    const views = {
      40: { cells: 25, columns: 5, phrase: 'many small apparent cells' },
      100: { cells: 9, columns: 3, phrase: 'several medium apparent cells' },
      400: { cells: 4, columns: 2, phrase: 'a few large apparent cells' },
    };

    function drawCell(detail) {
      const cell = node('span', { class: 'microscope-cell' });
      cell.append(node('span', { class: 'cell-nucleus' }));
      if (specimen === 'leaf') {
        for (let index = 0; index < 7; index += 1) cell.append(node('span', { class: 'cell-chloroplast' }));
      }
      return cell;
    }

    function refresh(announce) {
      const detail = CELL_SPECIMENS[specimen];
      const view = views[magnification];
      field.replaceChildren();
      field.className = 'microscope-field ' + detail.className + (contrast ? ' has-contrast' : '');
      field.style.setProperty('--cell-columns', view.columns);
      for (let index = 0; index < view.cells; index += 1) field.append(drawCell(detail));
      legend.replaceChildren(...detail.structures.map(structure => node('span', { role: 'listitem' }, structure)));
      legend.hidden = !labels;
      Object.entries(specimenButtons).forEach(([name, button]) => {
        const active = name === specimen;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      Object.entries(magnificationButtons).forEach(([value, button]) => {
        const active = Number(value) === magnification;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      contrastButton.setAttribute('aria-pressed', contrast ? 'true' : 'false');
      contrastButton.textContent = contrast ? 'Contrast improved' : 'Improve contrast';
      labelsButton.setAttribute('aria-pressed', labels ? 'true' : 'false');
      labelsButton.textContent = labels ? 'Hide structure list' : 'Show structure list';
      frame.readout.textContent = detail.label + ' · ' + magnification + '× total magnification · contrast ' +
        (contrast ? 'improved' : 'unchanged') + '. This schematic shows ' + view.phrase + '. ' + detail.description +
        ' Structures present in this specimen: ' + detail.structures.join(', ') + '. ' +
        ' Higher magnification enlarges the image and shows fewer cells; it does not make the cells grow or guarantee more detail.';
      if (announce) frame.status.textContent = detail.label + ' selected. ' + detail.description;
    }

    Object.entries(CELL_SPECIMENS).forEach(([name, detail]) => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => { specimen = name; refresh(true); },
      }, detail.label.replace(' epidermis', ''));
      specimenButtons[name] = button;
      specimenRow.append(button);
    });
    [40, 100, 400].forEach(value => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => {
          magnification = value;
          refresh(false);
          frame.status.textContent = 'The image is now shown at ' + value +
            ' times total magnification. Apparent size changed; actual cell size did not.';
        },
      }, value + '×');
      magnificationButtons[value] = button;
      magnificationRow.append(button);
    });
    const contrastButton = node('button', {
      type: 'button', class: 'btn small', 'aria-pressed': 'false', onclick: () => {
        contrast = !contrast;
        refresh(false);
        frame.status.textContent = contrast
          ? 'Contrast is stronger, so existing boundaries stand out. No new structure or size was created.'
          : 'Contrast is back to its original level.';
      },
    }, 'Improve contrast');
    const labelsButton = node('button', {
      type: 'button', class: 'btn ghost small', 'aria-pressed': 'false', onclick: () => {
        labels = !labels;
        refresh(false);
        frame.status.textContent = labels ? 'The structure list is visible below the field.' : 'The structure list is hidden.';
      },
    }, 'Show structure list');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        specimen = authoredSpecimen;
        magnification = authoredMagnification;
        contrast = false;
        labels = false;
        refresh(false);
        frame.status.textContent = 'The microscope is back to the authored specimen and magnification.';
      },
    }, 'Reset');

    frame.canvas.classList.add('cell-microscope-canvas');
    frame.canvas.append(node('div', { class: 'cell-microscope-scene' }, field, fieldNote, legend));
    frame.controls.append(specimenRow, magnificationRow,
      node('div', { class: 'model-button-row' }, contrastButton, labelsButton, resetButton));
    refresh(false);
    return frame.root;
  }

  const COUNTEREXAMPLE_STATES = {
    forward: {
      readout: 'Forward claim: all squares are rectangles. Every square has four right angles, so every square belongs inside the rectangle family.',
      status: 'The forward claim follows from the definitions: a square meets every requirement for a rectangle.',
    },
    reverse: {
      readout: 'Reversed claim to test: all rectangles are squares. The first claim did not promise this reverse direction. Look for a rectangle without four equal sides.',
      status: 'Reversing “all squares are rectangles” makes a new claim. It needs its own test.',
    },
    counterexample: {
      readout: 'Counterexample found: the long shape has four right angles, so it is a rectangle, but its sides are not all equal, so it is not a square. One counterexample disproves the reversed universal claim.',
      status: 'The long non-square rectangle disproves “all rectangles are squares.” It does not change the true forward claim.',
    },
  };

  function renderCounterexampleLab(item, hooks) {
    const frame = modelFrame(item, hooks);
    let state = 'forward';
    const scene = node('div', { class: 'counterexample-scene is-forward', 'aria-hidden': 'true' });
    const rectangleSet = node('div', { class: 'counterexample-rectangle-set' });
    const squareSet = node('div', { class: 'counterexample-square-set' });
    for (let index = 0; index < 4; index += 1) squareSet.append(node('span', { class: 'logic-square' }));
    const longRectangle = node('span', { class: 'logic-long-rectangle' });
    rectangleSet.append(squareSet, longRectangle);
    scene.append(rectangleSet);
    const stateButtons = {};
    const stateRow = node('div', { class: 'model-option-row', role: 'group', 'aria-label': 'Choose a reasoning step' });

    function refresh(announce) {
      scene.className = 'counterexample-scene is-' + state;
      Object.entries(stateButtons).forEach(([name, button]) => {
        const active = name === state;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      frame.readout.textContent = COUNTEREXAMPLE_STATES[state].readout;
      if (announce) frame.status.textContent = COUNTEREXAMPLE_STATES[state].status;
    }

    [['forward', 'Follow the forward claim'], ['reverse', 'Test the reverse'],
      ['counterexample', 'Reveal the counterexample']].forEach(([name, label]) => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => { state = name; refresh(true); },
      }, label);
      stateButtons[name] = button;
      stateRow.append(button);
    });
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        state = 'forward';
        refresh(false);
        frame.status.textContent = 'Back to the true forward claim: all squares are rectangles.';
      },
    }, 'Reset');

    frame.canvas.classList.add('counterexample-canvas');
    frame.canvas.append(scene);
    frame.controls.append(stateRow, node('div', { class: 'model-button-row' }, resetButton));
    refresh(false);
    return frame.root;
  }

  function renderFunctionComposition(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const authored = {
      fSlope: Math.round(clampNumber(props.f_slope, -3, 3, 2)) || 2,
      fIntercept: Math.round(clampNumber(props.f_intercept, -5, 5, 0)),
      gSlope: Math.round(clampNumber(props.g_slope, -3, 3, 1)) || 1,
      gIntercept: Math.round(clampNumber(props.g_intercept, -5, 5, -1)),
      xMin: Math.round(clampNumber(props.x_min, -8, 7, -5)),
      xMax: Math.round(clampNumber(props.x_max, -7, 8, 5)),
      startX: Math.round(clampNumber(props.start_x, -8, 8, 5)),
    };
    if (authored.xMin >= authored.xMax) {
      authored.xMin = -5;
      authored.xMax = 5;
    }
    authored.startX = Math.max(authored.xMin, Math.min(authored.xMax, authored.startX));
    let x = authored.startX;
    let order = 'f-then-g';
    const pipeline = node('div', { class: 'function-pipeline', 'aria-hidden': 'true' });
    const graph = svgNode('svg', {
      viewBox: '0 0 560 250', class: 'function-graph', 'aria-hidden': 'true', focusable: 'false',
    });
    const scene = node('div', { class: 'function-composition-scene' }, pipeline, graph);
    const orderButtons = {};
    const orderRow = node('div', {
      class: 'model-option-row', role: 'group', 'aria-label': 'Choose the order of the two functions',
    });

    function f(value) { return authored.fSlope * value + authored.fIntercept; }
    function g(value) { return authored.gSlope * value + authored.gIntercept; }
    function result(value, selectedOrder) {
      return selectedOrder === 'f-then-g' ? g(f(value)) : f(g(value));
    }
    function signed(value) {
      if (value === 0) return '';
      return value > 0 ? ' + ' + value : ' − ' + Math.abs(value);
    }
    function formula(name, slope, intercept) {
      const coefficient = slope === 1 ? '' : slope === -1 ? '−' : String(slope);
      return name + '(x) = ' + coefficient + 'x' + signed(intercept);
    }
    function drawGraph() {
      graph.replaceChildren();
      graph.append(svgNode('rect', { x: 28, y: 16, width: 504, height: 206, rx: 12, class: 'function-graph-field' }));
      const sampleOutputs = [];
      for (let value = authored.xMin; value <= authored.xMax; value += 1) {
        sampleOutputs.push(result(value, 'f-then-g'), result(value, 'g-then-f'));
      }
      const yMin = Math.floor(Math.min(0, ...sampleOutputs)) - 1;
      const yMax = Math.ceil(Math.max(0, ...sampleOutputs)) + 1;
      const mapX = value => 44 + (value - authored.xMin) * 472 / (authored.xMax - authored.xMin);
      const mapY = value => 210 - (value - yMin) * 182 / (yMax - yMin);
      for (let index = 0; index <= 8; index += 1) {
        const gx = 44 + index * 59;
        graph.append(svgNode('line', { x1: gx, y1: 28, x2: gx, y2: 210, class: 'function-grid-line' }));
      }
      for (let index = 0; index <= 6; index += 1) {
        const gy = 28 + index * (182 / 6);
        graph.append(svgNode('line', { x1: 44, y1: gy, x2: 516, y2: gy, class: 'function-grid-line' }));
      }
      if (authored.xMin <= 0 && authored.xMax >= 0) {
        graph.append(svgNode('line', { x1: mapX(0), y1: 28, x2: mapX(0), y2: 210, class: 'function-axis' }));
      }
      if (yMin <= 0 && yMax >= 0) {
        graph.append(svgNode('line', { x1: 44, y1: mapY(0), x2: 516, y2: mapY(0), class: 'function-axis' }));
      }
      const orders = ['f-then-g', 'g-then-f'];
      orders.forEach(candidate => {
        graph.append(svgNode('line', {
          x1: mapX(authored.xMin), y1: mapY(result(authored.xMin, candidate)),
          x2: mapX(authored.xMax), y2: mapY(result(authored.xMax, candidate)),
          class: 'function-composition-line' + (candidate === order ? ' is-selected' : ' is-comparison'),
        }));
      });
      graph.append(svgNode('circle', {
        cx: mapX(x), cy: mapY(result(x, order)), r: 7, class: 'function-current-point',
      }));
    }
    function refresh(announce) {
      const firstName = order === 'f-then-g' ? 'f' : 'g';
      const secondName = order === 'f-then-g' ? 'g' : 'f';
      const firstValue = order === 'f-then-g' ? f(x) : g(x);
      const finalValue = result(x, order);
      const comparisonOrder = order === 'f-then-g' ? 'g-then-f' : 'f-then-g';
      const comparisonValue = result(x, comparisonOrder);
      pipeline.replaceChildren(
        node('span', { class: 'function-value-card' }, String(x)),
        node('span', { class: 'function-arrow' }, '→'),
        node('span', { class: 'function-machine-card' }, firstName),
        node('span', { class: 'function-value-card' }, String(firstValue)),
        node('span', { class: 'function-arrow' }, '→'),
        node('span', { class: 'function-machine-card' }, secondName),
        node('span', { class: 'function-value-card is-result' }, String(finalValue)),
      );
      Object.entries(orderButtons).forEach(([name, button]) => {
        const active = name === order;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      slider.value = String(x);
      slider.setAttribute('aria-valuetext', 'Input x equals ' + x);
      drawGraph();
      const expression = order === 'f-then-g' ? 'g(f(' + x + '))' : 'f(g(' + x + '))';
      const comparisonExpression = order === 'f-then-g' ? 'f(g(' + x + '))' : 'g(f(' + x + '))';
      frame.readout.textContent = formula('f', authored.fSlope, authored.fIntercept) + '; ' +
        formula('g', authored.gSlope, authored.gIntercept) + '. Selected order: apply ' + firstName +
        ', then ' + secondName + '. ' + expression + ' = ' + finalValue + '; the other order gives ' +
        comparisonExpression + ' = ' + comparisonValue +
        '. Composition is not commutative in general: changing the order can change the output.';
      if (announce) {
        frame.status.textContent = 'Applied ' + firstName + ' first and ' + secondName +
          ' second. The final output is ' + finalValue + '.';
      }
    }

    [['f-then-g', 'Apply f, then g'], ['g-then-f', 'Apply g, then f']].forEach(([name, label]) => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => { order = name; refresh(true); },
      }, label);
      orderButtons[name] = button;
      orderRow.append(button);
    });
    const slider = node('input', {
      type: 'range', min: authored.xMin, max: authored.xMax, step: 1, value: x,
      'aria-label': 'Input x', oninput: event => { x = Number(event.target.value); refresh(false); },
    });
    const sliderLabel = node('label', { class: 'model-slider' },
      node('span', { class: 'model-slider-title' }, 'Choose the input'), slider,
      node('span', { class: 'model-slider-ends' },
        node('span', {}, String(authored.xMin)), node('span', {}, String(authored.xMax))));
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        x = authored.startX;
        order = 'f-then-g';
        refresh(false);
        frame.status.textContent = 'The input and function order are back to their authored starting values.';
      },
    }, 'Reset');
    frame.canvas.classList.add('function-composition-canvas');
    frame.canvas.append(scene);
    frame.controls.append(orderRow, sliderLabel, node('div', { class: 'model-button-row' }, resetButton));
    refresh(false);
    return frame.root;
  }

  const CARDIOPULMONARY_ROUTE = [
    {
      name: 'Venae cavae to right atrium', state: 'Lower-oxygen blood', className: 'is-lower',
      detail: 'Systemic veins return blood from the body to the right atrium.',
    },
    {
      name: 'Right ventricle', state: 'Lower-oxygen blood', className: 'is-lower',
      detail: 'The right ventricle receives that blood and pumps it toward the lungs.',
    },
    {
      name: 'Pulmonary artery', state: 'Lower-oxygen blood', className: 'is-lower',
      detail: 'The pulmonary artery carries blood away from the heart to the lungs.',
    },
    {
      name: 'Lung capillaries', state: 'Oxygen level rises', className: 'is-changing',
      detail: 'Oxygen diffuses from alveolar air into blood down a partial-pressure gradient.',
    },
    {
      name: 'Pulmonary veins', state: 'Higher-oxygen blood', className: 'is-higher',
      detail: 'Pulmonary veins carry blood from the lungs toward the left atrium.',
    },
    {
      name: 'Left atrium', state: 'Higher-oxygen blood', className: 'is-higher',
      detail: 'The left atrium receives the pulmonary venous return.',
    },
    {
      name: 'Left ventricle', state: 'Higher-oxygen blood', className: 'is-higher',
      detail: 'The left ventricle pumps blood into the systemic circulation.',
    },
    {
      name: 'Aorta and body capillaries', state: 'Oxygen is delivered', className: 'is-changing',
      detail: 'The aorta distributes blood; at tissue capillaries, oxygen moves into tissues.',
    },
    {
      name: 'Systemic veins', state: 'Lower-oxygen blood', className: 'is-lower',
      detail: 'Systemic veins collect the return flow and lead back to the venae cavae.',
    },
  ];

  function renderCirculationRoute(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const authoredStep = Math.round(clampNumber(props.start_step, 0, CARDIOPULMONARY_ROUTE.length - 1, 0));
    const authoredOxygen = props.show_oxygenation !== false;
    let step = authoredStep;
    let showOxygen = authoredOxygen;
    const route = node('ol', {
      class: 'circulation-route', 'aria-label': 'Cardiopulmonary circulation route in order',
    });

    function refresh(announce) {
      route.replaceChildren();
      CARDIOPULMONARY_ROUTE.forEach((station, index) => {
        const current = index === step;
        route.append(node('li', {
          class: 'circulation-station ' + (showOxygen ? station.className + ' ' : '') +
            (current ? 'is-current' : ''),
          'aria-current': current ? 'step' : null,
        }, node('span', { class: 'circulation-step-number', 'aria-hidden': 'true' }, String(index + 1)),
        node('span', { class: 'circulation-station-copy' },
          node('strong', { 'data-model-speak': true }, station.name),
          showOxygen ? node('small', {}, station.state) : null)));
      });
      oxygenButton.setAttribute('aria-pressed', showOxygen ? 'true' : 'false');
      oxygenButton.textContent = showOxygen ? 'Hide diagram oxygen cues' : 'Show diagram oxygen cues';
      const station = CARDIOPULMONARY_ROUTE[step];
      const next = CARDIOPULMONARY_ROUTE[(step + 1) % CARDIOPULMONARY_ROUTE.length];
      frame.readout.textContent = 'Step ' + (step + 1) + ' of ' + CARDIOPULMONARY_ROUTE.length + ': ' +
        station.name + '. ' + station.state + '. ' + station.detail + ' Next: ' + next.name +
        '. This schematic route follows one complete circuit. Arteries carry blood away from the heart and veins carry ' +
        'blood toward it, regardless of oxygen level.';
      if (announce) frame.status.textContent = 'Now tracing ' + station.name + '. ' + station.detail;
    }

    const backButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        step = (step + CARDIOPULMONARY_ROUTE.length - 1) % CARDIOPULMONARY_ROUTE.length;
        refresh(true);
      },
    }, 'Previous stop');
    const nextButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => {
        const completed = step === CARDIOPULMONARY_ROUTE.length - 1;
        step = (step + 1) % CARDIOPULMONARY_ROUTE.length;
        refresh(false);
        frame.status.textContent = completed
          ? 'The circuit is complete and continues at the right side of the heart.'
          : 'Now tracing ' + CARDIOPULMONARY_ROUTE[step].name + '. ' + CARDIOPULMONARY_ROUTE[step].detail;
      },
    }, 'Next stop');
    const oxygenButton = node('button', {
      type: 'button', class: 'btn small', 'aria-pressed': String(showOxygen), onclick: () => {
        showOxygen = !showOxygen;
        refresh(false);
        frame.status.textContent = showOxygen
          ? 'Diagram oxygen cues are shown with words and border patterns.'
          : 'Diagram oxygen cues are hidden; the full state remains in the text readout.';
      },
    }, 'Hide diagram oxygen cues');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        step = authoredStep;
        showOxygen = authoredOxygen;
        refresh(false);
        frame.status.textContent = 'The route is back to its authored starting stop.';
      },
    }, 'Reset');
    frame.canvas.classList.add('circulation-route-canvas');
    frame.canvas.append(route);
    frame.controls.append(node('div', { class: 'model-button-row' },
      backButton, nextButton, oxygenButton, resetButton));
    refresh(false);
    return frame.root;
  }

  const TRUTH_OPERATORS = {
    and: { label: 'AND', apply: (p, q) => p && q,
      rule: 'AND is true only when both propositions are true.' },
    or: { label: 'OR', apply: (p, q) => p || q,
      rule: 'Inclusive OR is true when at least one proposition is true.' },
    implies: { label: 'IMPLIES', apply: (p, q) => !p || q,
      rule: 'Material implication is false only when the first proposition is true and the second is false.' },
  };

  function renderTruthTable(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const authored = {
      operator: TRUTH_OPERATORS[props.start_operator] ? props.start_operator : 'implies',
      p: props.start_p !== false,
      q: props.start_q === true,
    };
    let operator = authored.operator;
    let p = authored.p;
    let q = authored.q;
    const table = node('table', { class: 'truth-table' });
    const operatorButtons = {};
    const operatorRow = node('div', {
      class: 'model-option-row', role: 'group', 'aria-label': 'Choose a logical operator',
    });

    function truth(value) { return value ? 'True' : 'False'; }
    function refresh(announce) {
      const detail = TRUTH_OPERATORS[operator];
      table.replaceChildren(
        node('caption', {}, detail.label + ' truth table'),
        node('thead', {}, node('tr', {},
          node('th', { scope: 'col' }, 'P'), node('th', { scope: 'col' }, 'Q'),
          node('th', { scope: 'col' }, detail.label))),
        node('tbody', {}, ...[[true, true], [true, false], [false, true], [false, false]].map(([rowP, rowQ]) => {
          const current = rowP === p && rowQ === q;
          return node('tr', { class: current ? 'is-current' : '', 'aria-current': current ? 'true' : null },
            node('td', {}, truth(rowP)), node('td', {}, truth(rowQ)),
            node('td', { class: detail.apply(rowP, rowQ) ? 'is-true' : 'is-false' },
              truth(detail.apply(rowP, rowQ))));
        })),
      );
      Object.entries(operatorButtons).forEach(([name, button]) => {
        const active = name === operator;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      pButton.setAttribute('aria-pressed', p ? 'true' : 'false');
      pButton.textContent = 'P is ' + truth(p);
      qButton.setAttribute('aria-pressed', q ? 'true' : 'false');
      qButton.textContent = 'Q is ' + truth(q);
      const result = detail.apply(p, q);
      frame.readout.textContent = 'P is ' + truth(p) + '; Q is ' + truth(q) + '. P ' + detail.label +
        ' Q is ' + truth(result) + '. ' + detail.rule +
        ' A truth table checks every possible truth-value pair; it does not decide whether P or Q is factually true.';
      if (announce) frame.status.textContent = 'The highlighted row now evaluates to ' + truth(result) + '.';
    }

    Object.entries(TRUTH_OPERATORS).forEach(([name, detail]) => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => { operator = name; refresh(true); },
      }, detail.label);
      operatorButtons[name] = button;
      operatorRow.append(button);
    });
    const pButton = node('button', {
      type: 'button', class: 'btn small', 'aria-pressed': String(p), onclick: () => {
        p = !p;
        refresh(true);
      },
    }, 'P is ' + truth(p));
    const qButton = node('button', {
      type: 'button', class: 'btn small', 'aria-pressed': String(q), onclick: () => {
        q = !q;
        refresh(true);
      },
    }, 'Q is ' + truth(q));
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        operator = authored.operator;
        p = authored.p;
        q = authored.q;
        refresh(false);
        frame.status.textContent = 'The operator and proposition values are back to their authored settings.';
      },
    }, 'Reset');
    frame.canvas.classList.add('truth-table-canvas');
    frame.canvas.append(table);
    frame.controls.append(operatorRow, node('div', { class: 'model-button-row' }, pButton, qButton, resetButton));
    refresh(false);
    return frame.root;
  }

  const STRUCTURE_SHAPES = ['is-square', 'is-circle', 'is-triangle', 'is-diamond', 'is-hexagon'];

  function renderStackQueue(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const authored = {
      mode: props.start_mode === 'queue' ? 'queue' : 'stack',
      capacity: Math.round(clampNumber(props.capacity, 3, 8, 6)),
      count: Math.round(clampNumber(props.initial_count, 0, 8, 3)),
    };
    authored.count = Math.min(authored.capacity, authored.count);
    let mode = authored.mode;
    let nextSerial = authored.count + 1;
    let items = Array.from({ length: authored.count }, (_, index) => makeItem(index + 1));
    let lastAction = 'No operation yet.';
    const scene = node('div', { class: 'stack-queue-scene', 'aria-hidden': 'true' });
    const modeButtons = {};
    const modeRow = node('div', {
      class: 'model-option-row', role: 'group', 'aria-label': 'Choose a data structure',
    });

    function makeItem(serial) {
      return {
        serial,
        label: 'item ' + serial,
        symbol: String.fromCharCode(65 + ((serial - 1) % 26)),
        shape: STRUCTURE_SHAPES[(serial - 1) % STRUCTURE_SHAPES.length],
      };
    }
    function refresh(announce) {
      const nextRemoval = items.length ? (mode === 'stack' ? items[items.length - 1] : items[0]) : null;
      scene.className = 'stack-queue-scene is-' + mode;
      scene.replaceChildren(
        node('span', { class: 'structure-marker is-remove' }, mode === 'stack' ? 'remove top' : 'remove front'),
        node('div', { class: 'structure-track' }, ...items.map(entry =>
          node('span', { class: 'structure-token ' + entry.shape }, entry.symbol))),
        node('span', { class: 'structure-marker is-add' }, mode === 'stack' ? 'add at top' : 'add at rear'),
      );
      Object.entries(modeButtons).forEach(([name, button]) => {
        const active = name === mode;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      addButton.disabled = items.length >= authored.capacity;
      removeButton.disabled = items.length === 0;
      const orderText = items.length ? items.map(entry => entry.label).join(', ') : 'empty';
      const rule = mode === 'stack'
        ? 'A stack is last-in, first-out: add and remove at the top.'
        : 'A queue is first-in, first-out: add at the rear and remove at the front.';
      frame.readout.textContent = (mode === 'stack' ? 'Stack' : 'Queue') + ' · ' + items.length + ' of ' +
        authored.capacity + ' places used · oldest-to-newest order: ' + orderText + '. ' + rule +
        (nextRemoval ? ' Next removal: ' + nextRemoval.label + '. ' : ' There is nothing to remove. ') + lastAction;
      if (announce) frame.status.textContent = lastAction;
    }

    [['stack', 'Stack'], ['queue', 'Queue']].forEach(([name, label]) => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false', onclick: () => {
          mode = name;
          lastAction = 'The same items remain in order; insertion and removal now follow the ' +
            label.toLowerCase() + ' rule.';
          refresh(true);
        },
      }, label);
      modeButtons[name] = button;
      modeRow.append(button);
    });
    const addButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => {
        const added = makeItem(nextSerial);
        nextSerial += 1;
        items.push(added);
        lastAction = (mode === 'stack' ? 'Pushed ' : 'Enqueued ') + added.label +
          (mode === 'stack' ? ' at the top.' : ' at the rear.');
        refresh(true);
      },
    }, 'Add item');
    const removeButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => {
        const removed = mode === 'stack' ? items.pop() : items.shift();
        lastAction = (mode === 'stack' ? 'Popped ' : 'Dequeued ') + removed.label +
          (mode === 'stack' ? ', the newest item.' : ', the oldest item.');
        refresh(true);
      },
    }, 'Remove next');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        mode = authored.mode;
        nextSerial = authored.count + 1;
        items = Array.from({ length: authored.count }, (_, index) => makeItem(index + 1));
        lastAction = 'The structure is back to its authored items and mode.';
        refresh(true);
      },
    }, 'Reset');
    frame.canvas.classList.add('stack-queue-canvas');
    frame.canvas.append(scene);
    frame.controls.append(modeRow, node('div', { class: 'model-button-row' }, addButton, removeButton, resetButton));
    refresh(false);
    return frame.root;
  }

  const MATRIX_TRANSFORMS = {
    identity: {
      label: 'Identity', matrix: [[1, 0], [0, 1]], determinant: 1,
    },
    'x-stretch': {
      label: 'Stretch x by 2', matrix: [[2, 0], [0, 1]], determinant: 2,
    },
    'x-shear': {
      label: 'Shear x by y', matrix: [[1, 1], [0, 1]], determinant: 1,
    },
    'y-reflection': {
      label: 'Reflect across x-axis', matrix: [[1, 0], [0, -1]], determinant: -1,
    },
    'x-projection': {
      label: 'Project onto x-axis', matrix: [[1, 0], [0, 0]], determinant: 0,
    },
  };

  function renderMatrixTransform(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const authoredTransform = MATRIX_TRANSFORMS[props.start_transform] ? props.start_transform : 'x-shear';
    let selected = authoredTransform;
    const original = svgNode('svg', {
      viewBox: '0 0 300 280', class: 'matrix-grid', 'aria-hidden': 'true', focusable: 'false',
    });
    const transformed = svgNode('svg', {
      viewBox: '0 0 300 280', class: 'matrix-grid', 'aria-hidden': 'true', focusable: 'false',
    });
    const transformButtons = {};
    const transformRow = node('div', {
      class: 'model-option-row', role: 'group', 'aria-label': 'Choose a matrix transformation',
    });

    function applyMatrix(matrix, point) {
      return [
        matrix[0][0] * point[0] + matrix[0][1] * point[1],
        matrix[1][0] * point[0] + matrix[1][1] * point[1],
      ];
    }
    function drawGrid(svg, matrix) {
      svg.replaceChildren();
      const map = point => [150 + point[0] * 48, 140 - point[1] * 48];
      const segment = (from, to, className) => {
        const start = map(applyMatrix(matrix, from));
        const end = map(applyMatrix(matrix, to));
        svg.append(svgNode('line', {
          x1: start[0], y1: start[1], x2: end[0], y2: end[1], class: className,
        }));
      };
      const arrow = (point, className) => {
        const start = map([0, 0]);
        const end = map(applyMatrix(matrix, point));
        svg.append(svgNode('line', {
          x1: start[0], y1: start[1], x2: end[0], y2: end[1], class: className,
        }));
        svg.append(svgNode('circle', { cx: end[0], cy: end[1], r: 5, class: className + '-tip' }));
      };
      svg.append(svgNode('rect', { x: 8, y: 8, width: 284, height: 264, rx: 14, class: 'matrix-grid-field' }));
      for (let grid = -2; grid <= 2; grid += 1) {
        segment([grid, -2], [grid, 2], grid === 0 ? 'matrix-axis-line' : 'matrix-grid-line');
        segment([-2, grid], [2, grid], grid === 0 ? 'matrix-axis-line' : 'matrix-grid-line');
      }
      const square = [[0, 0], [1, 0], [1, 1], [0, 1]].map(point => {
        const mapped = map(applyMatrix(matrix, point));
        return mapped[0] + ',' + mapped[1];
      }).join(' ');
      svg.append(svgNode('polygon', { points: square, class: 'matrix-unit-square' }));
      arrow([1, 0], 'matrix-basis-one');
      arrow([0, 1], 'matrix-basis-two');
      arrow([1, 1], 'matrix-vector-v');
    }
    function formatMatrix(matrix) {
      return '[[' + matrix[0].join(', ') + '], [' + matrix[1].join(', ') + ']]';
    }
    function formatVector(vector) {
      return '(' + vector.join(', ') + ')';
    }
    function refresh(announce) {
      const detail = MATRIX_TRANSFORMS[selected];
      const image = applyMatrix(detail.matrix, [1, 1]);
      drawGrid(original, MATRIX_TRANSFORMS.identity.matrix);
      drawGrid(transformed, detail.matrix);
      Object.entries(transformButtons).forEach(([name, button]) => {
        const active = name === selected;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      const invertibility = detail.determinant === 0
        ? 'The plane collapses to a line, so the map is not invertible.'
        : 'The determinant is nonzero, so the map is invertible.';
      const orientation = detail.determinant < 0
        ? 'The negative sign reverses orientation. '
        : detail.determinant > 0 ? 'Orientation is preserved. ' : '';
      frame.readout.textContent = 'A = ' + formatMatrix(detail.matrix) + '. v = (1, 1) maps to Av = ' +
        formatVector(image) + '. det(A) = ' + detail.determinant + ', so signed area is multiplied by ' +
        detail.determinant + ' and ordinary area by ' + Math.abs(detail.determinant) + '. ' + orientation + invertibility;
      if (announce) frame.status.textContent = detail.label + ' selected. ' + invertibility;
    }

    Object.entries(MATRIX_TRANSFORMS).forEach(([name, detail]) => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => { selected = name; refresh(true); },
      }, detail.label);
      transformButtons[name] = button;
      transformRow.append(button);
    });
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        selected = authoredTransform;
        refresh(false);
        frame.status.textContent = 'The matrix is back to the authored starting transform.';
      },
    }, 'Reset');
    frame.canvas.classList.add('matrix-transform-canvas');
    frame.canvas.append(node('div', { class: 'matrix-transform-scene' },
      node('div', { class: 'matrix-panel' }, node('strong', { 'data-model-speak': true }, 'Original plane'), original),
      node('span', { class: 'matrix-map-arrow', 'aria-hidden': 'true' }, '→'),
      node('div', { class: 'matrix-panel' }, node('strong', { 'data-model-speak': true }, 'Transformed plane'), transformed)));
    frame.controls.append(transformRow, node('div', { class: 'model-button-row' }, resetButton));
    refresh(false);
    return frame.root;
  }

  const VENTURI_THROATS = {
    'full-area': { label: 'Full area', area: 4, ratio: 1, speed: 1, drop: 0 },
    'half-area': { label: 'Half area', area: 2, ratio: 0.5, speed: 2, drop: 1.5 },
    'quarter-area': { label: 'Quarter area', area: 1, ratio: 0.25, speed: 4, drop: 7.5 },
  };

  function renderVenturiFlow(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const authoredThroat = VENTURI_THROATS[props.start_throat] ? props.start_throat : 'half-area';
    let selected = authoredThroat;
    const diagram = svgNode('svg', {
      viewBox: '0 0 640 270', class: 'venturi-diagram', 'aria-hidden': 'true', focusable: 'false',
    });
    const throatButtons = {};
    const throatRow = node('div', {
      class: 'model-option-row', role: 'group', 'aria-label': 'Choose the throat cross-sectional area',
    });
    const metrics = node('div', { class: 'venturi-metrics' });

    function drawVenturi(detail) {
      diagram.replaceChildren();
      const center = 166;
      const wideHalf = 58;
      const throatHalf = Math.max(16, wideHalf * detail.ratio);
      const top = 'M48,' + (center - wideHalf) + ' L206,' + (center - wideHalf) +
        ' L276,' + (center - throatHalf) + ' L364,' + (center - throatHalf) +
        ' L434,' + (center - wideHalf) + ' L592,' + (center - wideHalf);
      const bottom = 'M48,' + (center + wideHalf) + ' L206,' + (center + wideHalf) +
        ' L276,' + (center + throatHalf) + ' L364,' + (center + throatHalf) +
        ' L434,' + (center + wideHalf) + ' L592,' + (center + wideHalf);
      const fluid = top + ' L592,' + (center + wideHalf) + ' L434,' + (center + wideHalf) +
        ' L364,' + (center + throatHalf) + ' L276,' + (center + throatHalf) +
        ' L206,' + (center + wideHalf) + ' L48,' + (center + wideHalf) + ' Z';
      diagram.append(svgNode('path', { d: fluid, class: 'venturi-fluid' }));
      diagram.append(svgNode('path', { d: top, class: 'venturi-wall' }));
      diagram.append(svgNode('path', { d: bottom, class: 'venturi-wall' }));
      [[112, 44], [320, 44 + detail.speed * 11], [490, 44]].forEach(([x, length], index) => {
        diagram.append(svgNode('line', {
          x1: x - length / 2, y1: center, x2: x + length / 2, y2: center,
          class: index === 1 ? 'venturi-flow-arrow is-throat' : 'venturi-flow-arrow',
        }));
        diagram.append(svgNode('polygon', {
          points: (x + length / 2) + ',' + center + ' ' + (x + length / 2 - 10) + ',' +
            (center - 6) + ' ' + (x + length / 2 - 10) + ',' + (center + 6),
          class: index === 1 ? 'venturi-arrowhead is-throat' : 'venturi-arrowhead',
        }));
      });
      const throatColumnTop = 34 + detail.drop * 8;
      [[120, 34, center - wideHalf], [320, throatColumnTop, center - throatHalf],
        [520, 34, center - wideHalf]].forEach(([x, y, tubeTop], index) => {
        diagram.append(svgNode('line', { x1: x, y1: tubeTop, x2: x, y2: 22, class: 'venturi-tap' }));
        diagram.append(svgNode('line', {
          x1: x, y1: tubeTop - 1, x2: x, y2: y, class: index === 1 ? 'venturi-column is-throat' : 'venturi-column',
        }));
        diagram.append(svgNode('circle', {
          cx: x, cy: y, r: 5, class: index === 1 ? 'venturi-column-cap is-throat' : 'venturi-column-cap',
        }));
      });
    }
    function metric(label, value) {
      return node('div', { class: 'venturi-metric' }, node('small', {}, label), node('strong', {}, value));
    }
    function refresh(announce) {
      const detail = VENTURI_THROATS[selected];
      drawVenturi(detail);
      Object.entries(throatButtons).forEach(([name, button]) => {
        const active = name === selected;
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      metrics.replaceChildren(
        metric('Wide section', '4 cm² · 1 m/s'),
        metric('Throat', detail.area + ' cm² · ' + detail.speed + ' m/s'),
        metric('Ideal pressure drop', detail.drop + ' kPa'),
      );
      frame.readout.textContent = 'For this steady, horizontal, incompressible-water model with negligible viscosity and other losses, volume flow rate Q = 400 cm³/s. Continuity gives v = Q/A: the 4 cm² wide section moves at 1 m/s, and the ' +
        detail.area + ' cm² throat moves at ' + detail.speed + ' m/s. For horizontal ideal water flow, Bernoulli gives a throat pressure drop of ' +
        detail.drop + ' kPa relative to the wide section. Real viscous flow loses energy, so downstream pressure recovery is not perfect.';
      if (announce) frame.status.textContent = detail.label + ' selected: throat speed ' + detail.speed +
        ' m/s and ideal pressure drop ' + detail.drop + ' kPa.';
    }

    Object.entries(VENTURI_THROATS).forEach(([name, detail]) => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'false',
        onclick: () => { selected = name; refresh(true); },
      }, detail.label + ' (' + detail.area + ' cm²)');
      throatButtons[name] = button;
      throatRow.append(button);
    });
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        selected = authoredThroat;
        refresh(false);
        frame.status.textContent = 'The throat is back to its authored starting area.';
      },
    }, 'Reset');
    frame.canvas.classList.add('venturi-flow-canvas');
    frame.canvas.append(node('div', { class: 'venturi-scene' }, diagram, metrics));
    frame.controls.append(throatRow, node('div', { class: 'model-button-row' }, resetButton));
    refresh(false);
    return frame.root;
  }

  const GENE_EXPRESSION_STEPS = [
    'Gene off', 'Gene on', 'RNA transcribed', 'Mature mRNA exported',
    'AUG translated: Met', 'GAA translated: Glu', 'UUU translated: Phe', 'UAA read: stop and release',
  ];

  function renderGeneExpression(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const authoredStage = props.start_gene_state === 'on' ? 1 : 0;
    let stage = authoredStage;
    const scene = node('div', { class: 'gene-expression-scene' });
    const progress = node('ol', { class: 'gene-expression-progress', 'aria-label': 'Gene expression stages' });
    const DNA = '5′-ATG GAA TTT TAA-3′';
    const RNA = '5′-AUG GAA UUU UAA-3′';
    const codons = ['AUG', 'GAA', 'UUU', 'UAA'];
    const aminoAcids = ['Met', 'Glu', 'Phe'];

    function refresh(announce) {
      const translated = Math.max(0, Math.min(3, stage - 3));
      const stopRead = stage === 7;
      progress.replaceChildren(...GENE_EXPRESSION_STEPS.map((label, index) => node('li', {
        class: index < stage ? 'is-complete' : index === stage ? 'is-current' : '',
        'aria-current': index === stage ? 'step' : null,
      }, label)));
      const dnaCard = node('div', { class: 'gene-molecule gene-dna ' + (stage >= 1 ? 'is-active' : '') },
        node('small', {}, 'Coding DNA strand'), node('strong', { 'data-model-speak': true }, DNA));
      const rnaCard = node('div', { class: 'gene-molecule gene-rna ' + (stage >= 2 ? 'is-active' : 'is-muted') },
        node('small', {}, stage >= 3 ? 'Mature mRNA in cytoplasm' : 'RNA in nucleus'),
        node('strong', { 'data-model-speak': true }, stage >= 2 ? RNA : 'RNA not made yet'));
      const codonRow = node('div', { class: 'gene-codon-row' }, ...codons.map((codon, index) => node('span', {
        class: 'gene-codon ' + (index < translated || (index === 3 && stopRead) ? 'is-read' : ''),
      }, codon)));
      const peptide = node('div', { class: 'gene-peptide' },
        node('small', {}, 'Peptide'),
        node('strong', { 'data-model-speak': true }, translated
          ? aminoAcids.slice(0, translated).join('–') + (stopRead ? ' · released' : '')
          : 'No amino acids joined yet'));
      scene.replaceChildren(
        node('div', { class: 'gene-nucleus' }, node('span', { class: 'gene-compartment-label' }, 'Nucleus'),
          dnaCard, stage < 3 ? rnaCard : null),
        node('span', { class: 'gene-pore ' + (stage >= 3 ? 'is-active' : ''), 'aria-hidden': 'true' }, '→'),
        node('div', { class: 'gene-cytoplasm' }, node('span', { class: 'gene-compartment-label' }, 'Cytoplasm'),
          stage >= 3 ? rnaCard : null,
          stage >= 3 ? codonRow : node('p', { class: 'gene-awaiting-rna' }, 'No mRNA in the cytoplasm yet.'),
          peptide),
      );
      geneButton.disabled = stage !== 0;
      transcribeButton.disabled = stage !== 1;
      exportButton.disabled = stage !== 2;
      translateButton.disabled = stage < 3 || stage >= 7;
      translateButton.textContent = stage === 6 ? 'Read stop codon' : 'Translate next codon';
      const currentCodon = stage >= 4 ? codons[Math.min(3, stage - 4)] : 'none yet';
      const currentPeptide = translated ? aminoAcids.slice(0, translated).join('–') : 'none yet';
      frame.readout.textContent = 'Step ' + (stage + 1) + ' of ' + GENE_EXPRESSION_STEPS.length + ': ' +
        GENE_EXPRESSION_STEPS[stage] + '. Coding DNA ' + DNA + '; mRNA ' + RNA + '; product Met–Glu–Phe, then stop. ' +
        'The mRNA matches the coding DNA strand except that U replaces T; RNA polymerase reads the opposite template strand. ' +
        'Current codon: ' + currentCodon + '; current peptide: ' + currentPeptide + '. DNA remains in the nucleus and translation occurs in the cytoplasm. ' +
        'The on/off switch is a simplified regulation control. This bounded example follows a continuous coding sequence and omits introns, the 5′ cap and poly(A) tail.';
      if (announce) frame.status.textContent = GENE_EXPRESSION_STEPS[stage] + '.';
    }

    const geneButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => { stage = 1; refresh(true); },
    }, 'Switch gene on');
    const transcribeButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => { stage = 2; refresh(true); },
    }, 'Transcribe');
    const exportButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => { stage = 3; refresh(true); },
    }, 'Export mature mRNA');
    const translateButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => { stage = Math.min(7, stage + 1); refresh(true); },
    }, 'Translate next codon');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        stage = authoredStage;
        refresh(false);
        frame.status.textContent = 'Gene expression is back to its authored starting state.';
      },
    }, 'Reset');
    frame.canvas.classList.add('gene-expression-canvas');
    frame.canvas.append(scene, progress);
    frame.controls.append(node('div', { class: 'model-button-row' },
      geneButton, transcribeButton, exportButton, translateButton, resetButton));
    refresh(false);
    return frame.root;
  }

  const TCP_TRACE_EVENTS = [
    {
      title: 'Ready to send', ack: 'No ACK yet',
      detail: 'Four one-byte teaching segments are queued at the sender.',
    },
    {
      title: 'Segment 1 received', ack: 'ACK 2',
      detail: 'The receiver accepts segment 1 and cumulatively acknowledges the next expected teaching segment, 2.',
    },
    {
      title: 'Segment 2 lost', ack: 'ACK remains 2',
      detail: 'Segment 2 is dropped in the network, so the receiver still expects 2.',
    },
    {
      title: 'Segment 3 buffered', ack: 'Duplicate ACK 2 · 1 of 2',
      detail: 'Segment 3 arrives out of order. The receiver buffers it and repeats ACK 2 because the gap remains.',
    },
    {
      title: 'Segment 4 buffered', ack: 'Duplicate ACK 2 · 2 of 2',
      detail: 'Segment 4 also arrives out of order and is buffered. A second duplicate ACK 2 is sent.',
    },
    {
      title: 'Retransmission timeout', ack: 'Still ACK 2',
      detail: 'Only two duplicate acknowledgements arrived. In this simplified classic scenario that is not the three needed for fast retransmit, so the sender waits for its retransmission timer.',
    },
    {
      title: 'Segment 2 retransmitted', ack: 'ACK 2 until receipt',
      detail: 'The sender retransmits the missing segment 2 after the timeout.',
    },
    {
      title: 'Gap filled; stream released', ack: 'ACK 5',
      detail: 'Segment 2 arrives, making segments 1 through 4 contiguous. The receiver releases the ordered stream and acknowledges the next expected teaching segment, 5.',
    },
  ];

  function renderTcpPacketTracer(item, hooks) {
    const frame = modelFrame(item, hooks);
    let step = 0;
    const scene = node('div', { class: 'tcp-trace-scene' });
    const eventList = node('ol', { class: 'tcp-event-list', 'aria-label': 'TCP transfer events' });
    const packetTrack = node('div', { class: 'tcp-packet-track', 'aria-hidden': 'true' });
    const ackBadge = node('strong', { class: 'tcp-ack-badge', 'data-model-speak': true });

    function packetState(number) {
      if (number === 1) return step >= 1 ? 'is-delivered' : 'is-sender';
      if (number === 2) {
        if (step >= 7) return 'is-delivered';
        if (step === 6) return 'is-retransmitting';
        if (step >= 2) return 'is-lost';
        return 'is-sender';
      }
      if (number === 3) {
        if (step >= 7) return 'is-delivered';
        if (step >= 3) return 'is-buffered';
        return 'is-sender';
      }
      if (step >= 7) return 'is-delivered';
      if (step >= 4) return 'is-buffered';
      return 'is-sender';
    }
    function refresh(announce) {
      const event = TCP_TRACE_EVENTS[step];
      packetTrack.replaceChildren(...[1, 2, 3, 4].map(number => node('span', {
        class: 'tcp-packet tcp-packet-' + number + ' ' + packetState(number),
      }, String(number))));
      eventList.replaceChildren(...TCP_TRACE_EVENTS.map((entry, index) => node('li', {
        class: index < step ? 'is-complete' : index === step ? 'is-current' : '',
        'aria-current': index === step ? 'step' : null,
      }, entry.title)));
      ackBadge.textContent = event.ack;
      scene.replaceChildren(
        node('div', { class: 'tcp-endpoint-row' },
          node('span', {}, 'Sender'), node('span', {}, 'Network / receiver'), node('span', {}, 'Application')),
        packetTrack,
        node('div', { class: 'tcp-ack-row' }, node('span', {}, 'Receiver response'), ackBadge),
      );
      backButton.disabled = step === 0;
      nextButton.disabled = step === TCP_TRACE_EVENTS.length - 1;
      nextButton.textContent = step === 4 ? 'Advance to timeout' : step === 5 ? 'Retransmit segment 2' : 'Send next event';
      frame.readout.textContent = 'Event ' + (step + 1) + ' of ' + TCP_TRACE_EVENTS.length + ': ' + event.title + '. ' +
        event.detail + ' ' + event.ack + '. The labels 1–4 are pedagogical one-byte sequence positions; real TCP segments usually carry many bytes, sequence and acknowledgement numbers count byte positions, and an ACK names the next byte expected.';
      if (announce) frame.status.textContent = event.title + '. ' + event.ack + '.';
    }

    const backButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => { step = Math.max(0, step - 1); refresh(true); },
    }, 'Previous event');
    const nextButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => {
        step = Math.min(TCP_TRACE_EVENTS.length - 1, step + 1);
        refresh(true);
      },
    }, 'Next event');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        step = 0;
        refresh(false);
        frame.status.textContent = 'The trace is back before the first send.';
      },
    }, 'Reset');
    frame.canvas.classList.add('tcp-packet-canvas');
    frame.canvas.append(scene, eventList);
    frame.controls.append(node('div', { class: 'model-button-row' }, backButton, nextButton, resetButton));
    refresh(false);
    return frame.root;
  }

  function renderHeatEquation(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const cellCount = Math.round(clampNumber(props.cells, 9, 9, 9));
    const hotIndex = Math.round(clampNumber(props.hot_cell, 4, 4, 4)) - 1;
    const rate = clampNumber(props.diffusion_percent, 20, 20, 20) / 100;
    const maxSteps = Math.round(clampNumber(props.max_steps, 10, 10, 10));
    const history = [];
    const initial = Array(cellCount).fill(0);
    initial[hotIndex] = 100;
    history.push(initial);
    for (let count = 0; count < maxSteps; count += 1) {
      const old = history[history.length - 1];
      const next = old.map((value, index) => {
        const left = index === 0 ? old[index] : old[index - 1];
        const right = index === old.length - 1 ? old[index] : old[index + 1];
        return value + rate * (left - 2 * value + right);
      });
      history.push(next);
    }
    let step = 0;
    const strip = node('div', { class: 'heat-cell-grid', 'aria-hidden': 'true' });
    const metrics = node('div', { class: 'heat-equation-metrics' });

    function number(value) {
      return Math.abs(value) < 0.0005 ? '0.00' : value.toFixed(2);
    }
    function refresh(announce) {
      const values = history[step];
      const total = values.reduce((sum, value) => sum + value, 0);
      const maximum = Math.max(...values);
      strip.replaceChildren(...values.map((value, index) => {
        const fill = node('span', { class: 'heat-cell-fill' });
        fill.style.height = Math.max(4, value) + '%';
        return node('span', { class: 'heat-cell ' + (index === hotIndex ? 'is-origin' : '') },
          fill, node('small', {}, String(index + 1)));
      }));
      metrics.replaceChildren(
        node('span', {}, node('small', {}, 'Step'), node('strong', { 'data-model-speak': true }, step + ' / ' + maxSteps)),
        node('span', {}, node('small', {}, 'Total'), node('strong', {}, number(total))),
        node('span', {}, node('small', {}, 'Maximum'), node('strong', {}, number(maximum))),
      );
      previousButton.disabled = step === 0;
      nextButton.disabled = step === maxSteps;
      frame.readout.textContent = 'Cell temperature excesses: [' + values.map(number).join(', ') + ']. ' +
        'This dimensionless forward-Euler teaching model uses simultaneous updates, insulated no-flux boundaries, and r = 0.20. ' +
        'Because r ≤ 0.50 the one-dimensional stencil is stable here, and total heat is conserved at 100. ' +
        'It approximates diffusion on a grid; it is not an exact continuum solution or a claim of finite physical propagation speed.';
      if (announce) frame.status.textContent = 'Diffusion step ' + step + '. Maximum ' + number(maximum) +
        '; conserved total ' + number(total) + '.';
    }

    const previousButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        step = Math.max(0, step - 1);
        refresh(true);
      },
    }, 'Previous step');
    const nextButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => {
        step = Math.min(maxSteps, step + 1);
        refresh(true);
      },
    }, 'Diffuse one step');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        step = 0;
        refresh(false);
        frame.status.textContent = 'The insulated strip is back to one hot fourth cell.';
      },
    }, 'Reset');
    frame.canvas.classList.add('heat-equation-canvas');
    frame.canvas.append(node('div', { class: 'heat-equation-scene' }, strip, metrics));
    frame.controls.append(node('div', { class: 'model-button-row' }, previousButton, nextButton, resetButton));
    refresh(false);
    return frame.root;
  }

  const COMPLEXITY_CERTIFICATE_CLAUSES = [
    { label: 'A ∨ ¬B ∨ D', terms: [['A', true], ['B', false], ['D', true]] },
    { label: '¬A ∨ C', terms: [['A', false], ['C', true]] },
    { label: 'B ∨ ¬C ∨ D', terms: [['B', true], ['C', false], ['D', true]] },
    { label: '¬D ∨ A', terms: [['D', false], ['A', true]] },
  ];

  function renderComplexityCertificate(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const startN = Math.round(clampNumber(props.start_n, 4, 20, 4));
    const maxN = Math.round(clampNumber(props.max_n, startN, 20, 20));
    let n = startN;
    let assignment = { A: true, B: true, C: true, D: true };
    const growth = node('div', { class: 'complexity-growth-list' });
    const certificate = node('div', { class: 'complexity-certificate-scene' });
    const clauseList = node('ol', { class: 'complexity-certificate-list', 'aria-label': 'Clause results' });
    const variableRow = node('div', { class: 'model-option-row', role: 'group', 'aria-label': 'Proposed Boolean certificate' });
    const variableButtons = {};
    const nControl = node('input', {
      type: 'range', min: startN, max: maxN, step: 1, value: n,
      'aria-label': 'Input size n',
      oninput: event => { n = Number(event.target.value); refresh(false); },
    });

    function clauseResult(clause) {
      return clause.terms.some(([name, positive]) => positive ? assignment[name] : !assignment[name]);
    }
    function growthRow(label, count, className) {
      const bar = node('span', { class: 'complexity-growth-bar ' + className });
      const scale = Math.max(4, Math.min(100, Math.log2(count + 1) / maxN * 100));
      bar.style.width = scale + '%';
      return node('div', { class: 'complexity-growth-row' },
        node('span', { class: 'complexity-growth-label' }, label),
        node('span', { class: 'complexity-growth-track', 'aria-hidden': 'true' }, bar),
        node('strong', {}, count.toLocaleString('en-US')));
    }
    function refresh(announce) {
      const linear = n;
      const square = n * n;
      const exponential = Math.pow(2, n);
      nControl.value = String(n);
      nControl.setAttribute('aria-valuetext', 'n equals ' + n + '. Linear ' + linear +
        ', square ' + square + ', two to the n ' + exponential.toLocaleString('en-US') + '.');
      growth.replaceChildren(
        growthRow('n', linear, 'is-linear'),
        growthRow('n²', square, 'is-square'),
        growthRow('2ⁿ', exponential, 'is-exponential'),
      );
      Object.entries(variableButtons).forEach(([name, button]) => {
        const value = assignment[name];
        button.textContent = name + ' = ' + (value ? 'True' : 'False');
        button.setAttribute('aria-pressed', value ? 'true' : 'false');
        button.classList.toggle('is-selected', value);
      });
      const results = COMPLEXITY_CERTIFICATE_CLAUSES.map(clauseResult);
      clauseList.replaceChildren(...COMPLEXITY_CERTIFICATE_CLAUSES.map((clause, index) => node('li', {
        class: results[index] ? 'is-true' : 'is-false',
      }, node('span', {}, '(' + clause.label + ')'), node('strong', {}, results[index] ? 'True' : 'False'))));
      const allTrue = results.every(Boolean);
      frame.readout.textContent = 'At n = ' + n + ': n = ' + linear.toLocaleString('en-US') +
        ', n² = ' + square.toLocaleString('en-US') + ', and 2ⁿ = ' + exponential.toLocaleString('en-US') + '. ' +
        'The bars share a logarithmic display scale, while the written counts are exact. These are representative growth functions: polynomial examples do not prove that every problem has a polynomial algorithm. ' +
        'Checking this supplied certificate takes work proportional to the displayed formula size; finding one is a different task. ' +
        'The proposed assignment currently makes ' + results.filter(Boolean).length + ' of 4 clauses true. P versus NP remains open.';
      if (announce) frame.status.textContent = 'Certificate changed: ' + results.filter(Boolean).length +
        ' of 4 clauses are true; the whole formula is ' + (allTrue ? 'satisfied.' : 'not satisfied.');
    }

    ['A', 'B', 'C', 'D'].forEach(name => {
      const button = node('button', {
        type: 'button', class: 'btn small model-option', 'aria-pressed': 'true', onclick: () => {
          assignment[name] = !assignment[name];
          refresh(true);
        },
      }, name + ' = True');
      variableButtons[name] = button;
      variableRow.append(button);
    });
    const verifyButton = node('button', {
      type: 'button', class: 'btn small', onclick: () => {
        const passed = COMPLEXITY_CERTIFICATE_CLAUSES.filter(clauseResult).length;
        frame.status.textContent = 'Verification complete: ' + passed + ' of 4 clauses are true. ' +
          (passed === 4 ? 'This supplied assignment satisfies the formula.' : 'This assignment is not a certificate for satisfiability.');
      },
    }, 'Verify supplied certificate');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        n = startN;
        assignment = { A: true, B: true, C: true, D: true };
        refresh(false);
        frame.status.textContent = 'The chart and satisfying supplied certificate are reset.';
      },
    }, 'Reset');
    certificate.append(
      node('p', { class: 'complexity-formula', 'data-model-speak': true },
        '(A ∨ ¬B ∨ D) ∧ (¬A ∨ C) ∧ (B ∨ ¬C ∨ D) ∧ (¬D ∨ A)'),
      variableRow, clauseList,
    );
    frame.canvas.classList.add('complexity-certificate-canvas');
    frame.canvas.append(node('div', { class: 'complexity-model-scene' }, growth, certificate));
    frame.controls.append(node('label', { class: 'model-range-control' },
      node('span', {}, 'Compare growth at input size n'), nControl),
    node('div', { class: 'model-button-row' }, verifyButton, resetButton));
    refresh(false);
    return frame.root;
  }

  function renderMorphogenGradient(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const cellCount = Math.round(clampNumber(props.cells, 11, 11, 11));
    const source = clampNumber(props.source, 100, 100, 100);
    const retention = 1 - clampNumber(props.decay_percent, 20, 20, 20) / 100;
    const lowThreshold = clampNumber(props.low_threshold, 30, 30, 30);
    const highThreshold = clampNumber(props.high_threshold, 65, 65, 65);
    let selected = 0;
    let flat = false;
    const row = node('div', { class: 'morphogen-cell-row', 'aria-hidden': 'true' });
    const legend = node('div', { class: 'morphogen-fate-legend' });
    const inspectControl = node('input', {
      type: 'range', min: 1, max: cellCount, step: 1, value: 1,
      'aria-label': 'Inspect a cell', oninput: event => {
        selected = Number(event.target.value) - 1;
        refresh(false);
      },
    });

    function concentrations() {
      return Array.from({ length: cellCount }, (_, index) => flat ? 50 : source * Math.pow(retention, index));
    }
    function fate(value) {
      if (value >= highThreshold) return { key: 'high', label: 'High-threshold fate' };
      if (value >= lowThreshold) return { key: 'middle', label: 'Middle-band fate' };
      return { key: 'low', label: 'Below-threshold fate' };
    }
    function refresh(announce) {
      const values = concentrations();
      const fates = values.map(fate);
      row.replaceChildren(...values.map((value, index) => node('span', {
        class: 'morphogen-cell fate-' + fates[index].key + (index === selected ? ' is-selected' : ''),
      }, node('strong', {}, String(index + 1)), node('small', {}, value.toFixed(1)))));
      const counts = ['high', 'middle', 'low'].map(key => fates.filter(item => item.key === key).length);
      legend.replaceChildren(
        node('span', { class: 'fate-high' }, node('strong', {}, 'High'), ' ≥ 65 · ' + counts[0] + ' cells'),
        node('span', { class: 'fate-middle' }, node('strong', {}, 'Middle'), ' 30–<65 · ' + counts[1] + ' cells'),
        node('span', { class: 'fate-low' }, node('strong', {}, 'Low'), ' < 30 · ' + counts[2] + ' cells'),
      );
      inspectControl.value = String(selected + 1);
      inspectControl.setAttribute('aria-valuetext', 'Cell ' + (selected + 1) + ', concentration ' +
        values[selected].toFixed(2) + ', ' + fates[selected].label + '.');
      flattenButton.setAttribute('aria-pressed', flat ? 'true' : 'false');
      flattenButton.textContent = flat ? 'Restore gradient' : 'Flatten to 50';
      frame.readout.textContent = 'Cell ' + (selected + 1) + ' has model concentration ' +
        values[selected].toFixed(3) + ' and the ' + fates[selected].label + '. ' +
        (flat ? 'Every cell has the same 50-unit signal, so this one-signal fixed-threshold model gives one middle fate everywhere. ' :
          'The fixed profile is 100 × 0.80^i for zero-based position i; classification uses unrounded values. ') +
        'The 65 and 30 cutoffs are illustrative thresholds in an idealized static one-dimensional model. Real developmental fate can depend on exposure history, receptors, noise, feedback and other signals.';
      if (announce) frame.status.textContent = flat ?
        'The signal is flat at 50: all 11 cells have the middle fate in this simplified model.' :
        'The decaying gradient is restored: 2 high, 4 middle and 5 low cells.';
    }

    const flattenButton = node('button', {
      type: 'button', class: 'btn small', 'aria-pressed': 'false', onclick: () => {
        flat = !flat;
        refresh(true);
      },
    }, 'Flatten to 50');
    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        selected = 0;
        flat = false;
        refresh(false);
        frame.status.textContent = 'The original gradient and first selected cell are restored.';
      },
    }, 'Reset');
    frame.canvas.classList.add('morphogen-gradient-canvas');
    frame.canvas.append(node('div', { class: 'morphogen-gradient-scene' },
      node('div', { class: 'morphogen-source', 'data-model-speak': true }, 'Localized source · 100'), row, legend));
    frame.controls.append(node('label', { class: 'model-range-control' },
      node('span', {}, 'Inspect cell 1–11'), inspectControl),
    node('div', { class: 'model-button-row' }, flattenButton, resetButton));
    refresh(false);
    return frame.root;
  }

  const CT_REFERENCE_INSERTS = [
    { label: 'Air reference', hu: -1000 },
    { label: 'Low-density foam', hu: -700 },
    { label: 'Fat-equivalent polymer', hu: -100 },
    { label: 'Water', hu: 0 },
    { label: 'Soft-tissue-equivalent resin', hu: 40 },
    { label: 'Dense mineral insert', hu: 1000 },
  ];

  function renderCtWindow(item, hooks) {
    const frame = modelFrame(item, hooks);
    const props = item.props || {};
    const authoredLevel = clampNumber(props.level, 40, 40, 40);
    const authoredWidth = clampNumber(props.width, 400, 400, 400);
    let level = authoredLevel;
    let width = authoredWidth;
    const insertGrid = node('div', { class: 'ct-phantom-grid' });
    const rangeSummary = node('div', { class: 'ct-window-range', 'data-model-speak': true });
    const levelControl = node('input', {
      type: 'range', min: -1000, max: 1000, step: 10, value: level,
      'aria-label': 'Window level', oninput: event => { level = Number(event.target.value); refresh(false); },
    });
    const widthControl = node('input', {
      type: 'range', min: 2, max: 2000, step: 2, value: width,
      'aria-label': 'Window width', oninput: event => { width = Number(event.target.value); refresh(false); },
    });

    function windowValue(hu) {
      const lower = level - 0.5 - (width - 1) / 2;
      const upper = level - 0.5 + (width - 1) / 2;
      if (width <= 1) return hu <= level - 0.5 ? 0 : 255;
      if (hu <= lower) return 0;
      if (hu > upper) return 255;
      return Math.max(0, Math.min(255,
        ((hu - (level - 0.5)) / (width - 1) + 0.5) * 255));
    }
    function refresh(announce) {
      const lower = level - 0.5 - (width - 1) / 2;
      const upper = level - 0.5 + (width - 1) / 2;
      const blackThrough = Math.floor(lower);
      const whiteFrom = Math.ceil(upper);
      insertGrid.replaceChildren(...CT_REFERENCE_INSERTS.map(insert => {
        const output = windowValue(insert.hu);
        const swatch = node('span', { class: 'ct-insert-swatch', 'aria-hidden': 'true' });
        swatch.style.background = 'rgb(' + output.toFixed(3) + ', ' + output.toFixed(3) + ', ' + output.toFixed(3) + ')';
        return node('div', { class: 'ct-insert' }, swatch,
          node('span', {}, node('strong', {}, insert.label), node('small', {}, insert.hu + ' HU → ' + Math.round(output) + ' / 255')));
      }));
      rangeSummary.textContent = 'Level ' + level + ' · Width ' + width +
        ' · black through ' + blackThrough + ' HU · white from ' + whiteFrom + ' HU';
      levelControl.value = String(level);
      widthControl.value = String(width);
      levelControl.setAttribute('aria-valuetext', 'Window level ' + level + ' Hounsfield units');
      widthControl.setAttribute('aria-valuetext', 'Window width ' + width + ' Hounsfield units');
      frame.readout.textContent = 'DICOM LINEAR VOI with MONOCHROME2 maps low output to black and high output to white. ' +
        'Its linear branch uses width − 1 and level − 0.5: at level ' + level + ' and width ' + width +
        ', integer values through ' + blackThrough + ' HU are black and values from ' + whiteFrom + ' HU are white. ' +
        'Windowing changes only the display mapping, not stored HU or the acquisition. This is a synthetic phantom teaching display, not patient data and not a diagnosis.';
      if (announce) frame.status.textContent = 'Window reset to level ' + level + ' and width ' + width + '.';
    }

    const resetButton = node('button', {
      type: 'button', class: 'btn ghost small', onclick: () => {
        level = authoredLevel;
        width = authoredWidth;
        refresh(true);
      },
    }, 'Reset');
    frame.canvas.classList.add('ct-window-canvas');
    frame.canvas.append(node('div', { class: 'ct-window-scene' },
      node('p', { class: 'ct-phantom-label' }, 'Synthetic HU reference phantom'), insertGrid, rangeSummary));
    frame.controls.append(
      node('label', { class: 'model-range-control' }, node('span', {}, 'Window level'), levelControl),
      node('label', { class: 'model-range-control' }, node('span', {}, 'Window width'), widthControl),
      node('div', { class: 'model-button-row' }, resetButton),
    );
    refresh(false);
    return frame.root;
  }

  const RENDERERS = Object.freeze({
    counter: renderCounter,
    'shape-explorer': renderShapeExplorer,
    'shadow-lab': renderShadowLab,
    'sequence-runner': renderSequenceRunner,
    'make-ten': renderMakeTen,
    'light-paths': renderLightPaths,
    'algorithm-tracer': renderAlgorithmTracer,
    'life-cycle': renderLifeCycle,
    'fraction-equivalence-lab': renderFractionEquivalence,
    'atom-element-builder': renderAtomElementBuilder,
    'cell-microscope': renderCellMicroscope,
    'counterexample-lab': renderCounterexampleLab,
    'function-composition-lab': renderFunctionComposition,
    'circulation-route-lab': renderCirculationRoute,
    'truth-table-lab': renderTruthTable,
    'stack-queue-lab': renderStackQueue,
    'matrix-transform-lab': renderMatrixTransform,
    'venturi-flow-lab': renderVenturiFlow,
    'gene-expression-stepper': renderGeneExpression,
    'tcp-packet-tracer': renderTcpPacketTracer,
    'heat-equation-lab': renderHeatEquation,
    'complexity-certificate-lab': renderComplexityCertificate,
    'morphogen-gradient-lab': renderMorphogenGradient,
    'ct-window-lab': renderCtWindow,
  });

  window.PrimerLessonModels = Object.freeze({
    render(item, hooks) {
      const renderer = item && RENDERERS[item.renderer];
      return renderer ? renderer(item, hooks) : null;
    },
    supported: Object.freeze(Object.keys(RENDERERS)),
  });
}());
