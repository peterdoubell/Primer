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
  });

  window.PrimerLessonModels = Object.freeze({
    render(item, hooks) {
      const renderer = item && RENDERERS[item.renderer];
      return renderer ? renderer(item, hooks) : null;
    },
    supported: Object.freeze(Object.keys(RENDERERS)),
  });
}());
