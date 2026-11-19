/* The player for learning sequences: one idea, a few small checked steps.

   The teaching loop is always the same — the book introduces an idea, shows it
   on a worked example, asks the reader to predict, checks what they said,
   explains the outcome, and ends by asking them to use the idea somewhere new.
   What changes is what the reader's hands do at each step.

   Nothing here knows an answer.  Every response is sent to the server, which
   holds the authored model; this file only draws what comes back.  It is
   study, and it says so: finishing a sequence is never called mastery.  */
(function (scope) {
  'use strict';
  const V = scope.PrimerLearningVisuals;
  const h = V.node;

  /* The reader's own helpers, when this runs inside the book. Each is optional
     so that the player can also be mounted alone, in a test page. */
  const app = {
    // The reader's age when the book knows it. A new reader's stage is 0 until
    // placement whatever their age, so stage alone cannot say who is young.
    age() { try { return Number(S.state.profile.age); } catch (e) { return NaN; } },
    speakNow(words) { try { if (typeof speakText === 'function') speakText(words); } catch (e) { /* no voice */ } },
    speakMaybe(words) { try { if (typeof maybeSpeak === 'function') maybeSpeak(words, 1); } catch (e) { /* no voice */ } },
    speaker(getText, label) {
      try { if (typeof speakBtn === 'function') return speakBtn(getText, label); } catch (e) { /* fall through */ }
      const b = h('button', { type: 'button', class: 'speak-btn', 'aria-label': label || 'Read aloud' }, '🔊');
      b.addEventListener('click', () => {
        try { speechSynthesis.cancel(); speechSynthesis.speak(new SpeechSynthesisUtterance(typeof getText === 'function' ? getText() : getText)); } catch (e) { /* no voice */ }
      });
      return b;
    },
    mark(ok) {
      try { if (typeof verdictMark === 'function') return verdictMark(ok); } catch (e) { /* fall through */ }
      return h('span', { class: 'verdict-mark', 'aria-hidden': 'true' }, ok ? '✓' : '✗');
    },
    buzz(kind) { try { if (typeof haptic === 'function') haptic(kind); } catch (e) { /* silent */ } },
    growth(xp) { try { if (typeof flyXP === 'function') flyXP(xp); if (typeof refreshStats === 'function') refreshStats(); } catch (e) { /* silent */ } },
    calm() { try { return typeof reducedMotion === 'function' ? reducedMotion() : matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; } },
  };

  async function request(method, path, body) {
    const response = await fetch(path, method === 'GET' ? {} : {
      method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
    if (response.status === 401 && typeof toSignIn === 'function') { toSignIn(); return new Promise(() => {}); }
    const payload = await response.json().catch(() => ({ error: response.statusText }));
    if (!response.ok) throw Object.assign({ status: response.status }, payload);
    return payload;
  }
  const button = (attrs, ...kids) => h('button', Object.assign({ type: 'button' }, attrs), ...kids);
  const settled = beat => beat.kind !== 'step' || beat.state.status === 'solved' || beat.state.status === 'revealed';
  let serial = 0;
  const uid = prefix => prefix + '-' + (++serial);

  /* ------------------------------------------------------------ widgets
     Each returns { node, response(), mark(marks), lock(solution, fresh) }.
     response() is whatever the reader has assembled so far; the server decides
     whether it is complete.  lock() freezes the widget on the right answer:
     `fresh` means the reader has just produced it, so their own work stays. */

  function choiceWidget(beat, ctx) {
    const multi = !!beat.multi, chosen = new Set(), buttons = new Map();
    const box = h('div', { class: 'q-choices lg-choices', role: multi ? 'group' : 'radiogroup',
      'aria-label': multi ? 'Choose every one that holds' : 'Choose one' });
    const refresh = () => buttons.forEach((b, id) => {
      const on = chosen.has(id);
      b.classList.toggle('selected', on);
      b.setAttribute('aria-checked', on ? 'true' : 'false');
      if (!multi) b.setAttribute('tabindex', on || (!chosen.size && b === box.querySelector('.choice:not(:disabled)')) ? '0' : '-1');
    });
    beat.options.forEach(option => {
      const b = button({ class: 'choice lg-choice', role: multi ? 'checkbox' : 'radio', 'aria-checked': 'false' },
        h('span', { class: 'lg-choice-text' }, option.text), h('span', { class: 'sel-mark' }, ' ✓ Chosen'));
      b.addEventListener('click', () => {
        if (multi) { if (chosen.has(option.id)) chosen.delete(option.id); else chosen.add(option.id); }
        else { chosen.clear(); chosen.add(option.id); }
        b.classList.remove('wrong');
        refresh();
        if (ctx.young) app.speakMaybe(option.text);
        ctx.changed();
      });
      if (!multi) b.addEventListener('keydown', event => {
        if (!['ArrowDown', 'ArrowRight', 'ArrowUp', 'ArrowLeft'].includes(event.key)) return;
        event.preventDefault();
        const live = [...buttons.values()].filter(x => !x.disabled), at = live.indexOf(b);
        const next = live[(at + (event.key === 'ArrowDown' || event.key === 'ArrowRight' ? 1 : -1) + live.length) % live.length];
        next.focus(); next.click();
      });
      buttons.set(option.id, b);
      box.append(ctx.young ? h('div', { class: 'choice-row' }, b, app.speaker(() => option.text, 'Say this answer')) : b);
    });
    refresh();
    const flag = (id, ok) => {
      const b = buttons.get(id);
      if (!b) return;
      b.querySelectorAll('.verdict-mark').forEach(m => m.remove());
      b.classList.remove('selected'); b.classList.toggle('correct', ok); b.classList.toggle('wrong', !ok);
      b.prepend(app.mark(ok));
    };
    return {
      node: box,
      response: () => multi ? { choices: [...chosen] } : { choice: [...chosen][0] || '' },
      mark(marks) {
        // A wrong single choice is struck and set aside: the same wrong
        // answer cannot be offered twice.  In a select-all step only the
        // statements that do not hold are struck.
        const wrong = multi ? (marks.wrong || []) : [...chosen];
        wrong.forEach(id => { flag(id, false); chosen.delete(id); if (!multi) buttons.get(id).disabled = true; });
        refresh();
      },
      lock(solution) {
        const right = new Set(multi ? solution.choices : [solution.choice]);
        buttons.forEach((b, id) => { if (right.has(id)) flag(id, true); else b.classList.remove('selected'); b.disabled = true; b.setAttribute('aria-checked', right.has(id) ? 'true' : 'false'); });
      },
    };
  }

  function compareWidget(beat, ctx) {
    const inner = choiceWidget(beat, ctx);
    const panels = h('div', { class: 'lg-pair lg-compare' }, ...beat.panels.map(panel =>
      h('figure', { class: 'lg-pair-side' }, V.draw(panel, ctx.visual),
        h('figcaption', { class: 'muted' }, panel.side === 'left' ? 'First' : 'Second'))));
    return Object.assign({}, inner, { node: h('div', {}, panels, inner.node) });
  }

  function cluesWidget(beat, ctx) {
    const inner = choiceWidget(beat, ctx);
    const list = h('ul', { class: 'lg-clues' });
    const count = h('p', { class: 'muted lg-clue-count', role: 'status', 'aria-live': 'polite' });
    function draw(done) {
      const open = new Map(((done && done.clues) || beat.state.clues || []).map(c => [c.id, c]));
      const enough = new Set((done && done.enough) || []);
      list.replaceChildren(...beat.clues.map(clue => {
        const shown = open.get(clue.id);
        if (shown) return h('li', { class: 'lg-clue lg-clue-open' + (enough.has(clue.id) ? ' lg-clue-needed' : '') },
          h('b', {}, clue.label + ': '), shown.text, enough.has(clue.id) ? ' ' : null,
          enough.has(clue.id) ? h('span', { class: 'lg-tag' }, 'enough to decide') : null);
        const b = button({ class: 'btn ghost small', disabled: done ? '' : null }, 'Turn over: ' + clue.label);
        b.addEventListener('click', async () => {
          b.disabled = true;
          try {
            const result = await ctx.post('clue', { clue: clue.id });
            beat.state = result.state; draw(); ctx.changed();
            const fresh = list.querySelector('.lg-clue-open:last-of-type');
            if (ctx.young && fresh) app.speakMaybe(fresh.textContent);
          } catch (error) { b.disabled = false; ctx.trouble(error); }
        });
        return h('li', { class: 'lg-clue' }, b);
      }));
      const turned = (beat.state.clues || []).length;
      count.textContent = done ? '' : turned ? 'Turned over: ' + turned + ' of ' + beat.clues.length + '. Fewer is better.'
        : 'Nothing turned over yet. Each clue you turn over counts.';
    }
    draw();
    return Object.assign({}, inner, {
      node: h('div', {}, list, count, inner.node),
      // A right outcome reached before the evidence is in is not struck out:
      // the choice may well be right, it simply is not yet supported.
      mark(marks) { if (!marks.unsupported) inner.mark(marks); },
      lock(solution) { inner.lock(solution); draw(solution); },
    });
  }

  function orderWidget(beat, ctx) {
    const placed = [], chips = new Map();
    const slot = h('ol', { class: 'order-slot lg-order-slot', 'aria-label': 'Your order so far' });
    const tray = h('div', { class: 'order-tray lg-order-tray', role: 'group', 'aria-label': 'Tap these in order' });
    const again = button({ class: 'btn ghost small' }, '↺ Start over');
    const ends = beat.ends && beat.ends.length === 2 ? h('p', { class: 'muted lg-ends' }, 'From “' + beat.ends[0] + '” to “' + beat.ends[1] + '”.') : null;
    function draw(marks) {
      slot.replaceChildren();
      if (!placed.length) slot.append(h('li', { class: 'muted lg-order-empty' }, 'Tap them in order…'));
      placed.forEach((id, index) => {
        const item = beat.items.find(i => i.id === id);
        const chip = button({ class: 'order-chip placed lg-chip', 'aria-label': 'Position ' + (index + 1) + ': ' + item.text + '. Tap to take it back.' }, item.text);
        if (marks && marks[index] !== undefined) { chip.classList.add(marks[index] ? 'lg-right' : 'lg-wrong'); chip.prepend(app.mark(marks[index])); }
        chip.addEventListener('click', () => {
          placed.splice(index, 1); chips.get(id).disabled = false; draw(); ctx.changed(); chips.get(id).focus();
        });
        slot.append(h('li', {}, chip));
      });
    }
    beat.items.forEach(item => {
      const chip = button({ class: 'order-chip lg-chip' }, item.text);
      chip.addEventListener('click', () => {
        chip.disabled = true; placed.push(item.id); draw(); ctx.changed();
        if (ctx.young) app.speakMaybe(item.text);
        const next = tray.querySelector('.order-chip:not(:disabled)');
        (next || ctx.checkButton()).focus();
      });
      chips.set(item.id, chip);
      tray.append(ctx.young ? h('span', { class: 'order-chip-wrap' }, chip, app.speaker(() => item.text, 'Say this one')) : chip);
    });
    again.addEventListener('click', () => {
      placed.length = 0; chips.forEach(c => { c.disabled = false; }); draw(); ctx.changed();
      const first = tray.querySelector('.order-chip'); if (first) first.focus();
    });
    draw();
    return {
      node: h('div', {}, ends, slot, tray, h('div', { class: 'order-actions' }, again)),
      response: () => ({ order: placed.slice() }),
      mark(marks) { draw(marks.placed); },
      lock(solution) {
        placed.splice(0, placed.length, ...solution.order);
        draw(solution.order.map(() => true));
        slot.querySelectorAll('button').forEach(b => { b.disabled = true; });
        chips.forEach(c => { c.disabled = true; }); again.disabled = true; tray.hidden = true; again.hidden = true;
      },
    };
  }

  function matchWidget(beat, ctx) {
    const pairs = new Map(), lefts = new Map(), rights = new Map();
    let active = null, flagged = new Set(), locked = false;
    const leftCol = h('div', { class: 'lg-match-col', role: 'group', 'aria-label': 'First, choose one of these' });
    const rightCol = h('div', { class: 'lg-match-col', role: 'group', 'aria-label': 'Then choose its partner' });
    const summary = h('ul', { class: 'lg-match-summary', 'aria-label': 'Pairs made so far' });
    const text = (list, id) => list.find(x => x.id === id).text;
    function draw() {
      const order = [...pairs.keys()];
      lefts.forEach((b, id) => {
        const n = order.indexOf(id);
        b.setAttribute('aria-pressed', active === id ? 'true' : 'false');
        b.classList.toggle('lg-paired', n >= 0); b.classList.toggle('lg-wrong', flagged.has(id));
        b.querySelector('.lg-badge').textContent = n >= 0 ? String(n + 1) : '';
      });
      rights.forEach((b, id) => {
        const left = order.find(l => pairs.get(l) === id), n = order.indexOf(left);
        b.classList.toggle('lg-paired', n >= 0); b.classList.toggle('lg-wrong', flagged.has(left));
        b.querySelector('.lg-badge').textContent = n >= 0 ? String(n + 1) : '';
      });
      summary.replaceChildren(...order.map((left, n) => h('li', { class: flagged.has(left) ? 'lg-wrong' : locked ? 'lg-right' : '' },
        locked || flagged.has(left) ? app.mark(!flagged.has(left)) : null,
        (n + 1) + '. ' + text(beat.lefts, left) + ' — ' + text(beat.rights, pairs.get(left)))));
    }
    beat.lefts.forEach(item => {
      const b = button({ class: 'lg-match-item', 'aria-pressed': 'false' }, h('span', { class: 'lg-badge', 'aria-hidden': 'true' }), item.text);
      b.addEventListener('click', () => {
        flagged.delete(item.id);
        if (pairs.has(item.id)) { pairs.delete(item.id); active = item.id; } else active = active === item.id ? null : item.id;
        if (ctx.young) app.speakMaybe(item.text);
        draw(); ctx.changed();
      });
      lefts.set(item.id, b); leftCol.append(b);
    });
    beat.rights.forEach(item => {
      const b = button({ class: 'lg-match-item' }, h('span', { class: 'lg-badge', 'aria-hidden': 'true' }), item.text);
      b.addEventListener('click', () => {
        const holder = [...pairs.keys()].find(l => pairs.get(l) === item.id);
        if (active) { if (holder) pairs.delete(holder); flagged.delete(active); pairs.set(active, item.id); active = null; }
        else if (holder) { pairs.delete(holder); flagged.delete(holder); active = holder; }
        else { ctx.say('Choose one from the first list, then its partner.', 'nudge'); return; }
        if (ctx.young) app.speakMaybe(item.text);
        draw(); ctx.changed();
        if (!active) { const next = [...lefts.entries()].find(([id]) => !pairs.has(id)); (next ? next[1] : ctx.checkButton()).focus(); }
      });
      rights.set(item.id, b); rightCol.append(b);
    });
    draw();
    return {
      node: h('div', {}, h('div', { class: 'lg-match' }, leftCol, rightCol), summary),
      response: () => ({ pairs: Object.fromEntries(pairs) }),
      mark(marks) { flagged = new Set(marks.wrong || []); draw(); },
      lock(solution) {
        pairs.clear(); flagged.clear(); active = null; locked = true;
        beat.lefts.forEach(item => pairs.set(item.id, solution.pairs[item.id]));
        draw(); lefts.forEach(b => { b.disabled = true; }); rights.forEach(b => { b.disabled = true; });
      },
    };
  }

  function groupWidget(beat, ctx) {
    const placed = new Map(), rows = new Map();
    const list = h('div', { class: 'lg-group' });
    beat.items.forEach(item => {
      const id = uid('lg-item'), choices = new Map();
      const set = h('div', { class: 'lg-group-bins', role: 'radiogroup', 'aria-labelledby': id });
      beat.bins.forEach(bin => {
        const b = button({ class: 'lg-bin', role: 'radio', 'aria-checked': 'false' }, bin.text);
        b.addEventListener('click', () => {
          placed.set(item.id, bin.id); row.classList.remove('lg-wrong');
          row.querySelectorAll('.verdict-mark').forEach(m => m.remove());
          choices.forEach((x, key) => x.setAttribute('aria-checked', key === bin.id ? 'true' : 'false'));
          ctx.changed();
        });
        choices.set(bin.id, b); set.append(b);
      });
      const label = h('span', { class: 'lg-group-item', id }, item.text);
      const row = h('div', { class: 'lg-group-row' }, ctx.young ? h('span', { class: 'lg-group-say' }, label, app.speaker(() => item.text, 'Say this one')) : label, set);
      rows.set(item.id, { row, choices, label });
      list.append(row);
    });
    return {
      node: list,
      response: () => ({ bins: Object.fromEntries(placed) }),
      mark(marks) {
        rows.forEach(({ row, label }, id) => {
          row.querySelectorAll('.verdict-mark').forEach(m => m.remove());
          const wrong = (marks.wrong || []).includes(id);
          row.classList.toggle('lg-wrong', wrong);
          if (wrong) label.prepend(app.mark(false));
        });
      },
      lock(solution) {
        rows.forEach(({ row, choices, label }, id) => {
          row.classList.remove('lg-wrong'); row.classList.add('lg-right');
          row.querySelectorAll('.verdict-mark').forEach(m => m.remove()); label.prepend(app.mark(true));
          choices.forEach((b, key) => { b.setAttribute('aria-checked', key === solution.bins[id] ? 'true' : 'false'); b.disabled = true; });
        });
      },
    };
  }

  function fillWidget(beat, ctx) {
    const inputs = [], parts = beat.frame.split('__');
    const line = h('p', { class: 'lg-frame' });
    // Name each blank by the sentence it completes, so a screen reader hears
    // "Missing value in: The last … digits", not a bare "Missing value".
    const spoken = parts.map(part => part.trim()).join(' … ').trim();
    const picks = beat.choices ? h('div', { class: 'lg-taps', role: 'group', 'aria-label': 'Tap your answer' }) : null;
    parts.forEach((part, index) => {
      if (part) line.append(h('span', {}, part));
      if (index === parts.length - 1) return;
      const input = h('input', { type: 'text', class: 'lg-blank', autocomplete: 'off', autocapitalize: 'off', spellcheck: 'false',
        inputmode: beat.numeric ? 'decimal' : 'text',
        'aria-label': (parts.length > 2 ? 'Missing value ' + (index + 1) + ' of ' + (parts.length - 1) : 'Missing value') + ' in: ' + spoken,
        size: beat.numeric ? '5' : '12' });
      if (picks) { input.readOnly = true; input.tabIndex = -1; input.setAttribute('aria-hidden', 'true'); }
      input.addEventListener('input', () => { input.removeAttribute('aria-invalid'); ctx.changed(); });
      input.addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); ctx.check(); } });
      inputs.push(input); line.append(input);
    });
    if (picks) beat.choices.forEach(choice => {
      const b = button({ class: 'lg-tap', 'aria-pressed': 'false' }, choice);
      b.addEventListener('click', () => {
        inputs[0].value = choice; inputs[0].removeAttribute('aria-invalid');
        picks.querySelectorAll('.lg-tap').forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
        if (ctx.young) app.speakMaybe(choice);
        ctx.changed();
      });
      picks.append(ctx.young ? h('span', { class: 'order-chip-wrap' }, b, app.speaker(() => choice, 'Say this answer')) : b);
    });
    return {
      node: h('div', {}, line, picks),
      response: () => ({ values: inputs.map(input => input.value.trim()) }),
      mark(marks) {
        (marks.right || []).forEach((ok, index) => { if (!ok && inputs[index]) inputs[index].setAttribute('aria-invalid', 'true'); });
        if (picks) picks.querySelectorAll('[aria-pressed="true"]').forEach(b => { b.disabled = true; b.setAttribute('aria-pressed', 'false'); b.classList.add('lg-wrong'); });
        if (!picks) { const first = inputs.find(input => input.getAttribute('aria-invalid')); if (first) { first.focus(); first.select(); } }
      },
      lock(solution, fresh) {
        inputs.forEach((input, index) => { if (!fresh || !input.value) input.value = solution.values[index]; input.disabled = true; input.removeAttribute('aria-invalid'); input.classList.add('lg-right'); });
        if (picks) picks.querySelectorAll('button').forEach(b => { b.disabled = true; });
      },
    };
  }

  function editWidget(beat, ctx) {
    const edits = new Map(), cells = [];
    let open = null;
    const row = h('div', { class: 'lg-tokens', role: 'group', 'aria-label': 'Tap a part to change it' });
    const panel = h('div', { class: 'lg-edit-panel' });
    const count = h('p', { class: 'muted', role: 'status', 'aria-live': 'polite' });
    const limit = beat.limit || 1;
    function draw() {
      cells.forEach(({ node, token, position }) => {
        if (!token.alts.length) return;
        const value = edits.get(position);
        node.replaceChildren(value === undefined ? token.text : value,
          value === undefined ? '' : h('span', { class: 'lg-changed-note' }, ' (was ' + token.text + ')'));
        node.classList.toggle('lg-changed', value !== undefined);
        node.setAttribute('aria-expanded', open === position ? 'true' : 'false');
      });
      count.textContent = 'Changes used: ' + edits.size + ' of ' + limit + '.';
      panel.replaceChildren();
      if (open === null) return;
      const { token, position } = cells[open - 1];
      const choose = value => {
        if (value !== null && !edits.has(position) && edits.size >= limit) {
          ctx.say(limit === 1 ? 'You may change one part only. Put the other one back first.'
            : 'You may change at most ' + limit + ' parts. Put one back first.', 'nudge');
          return;
        }
        if (value === null) edits.delete(position); else edits.set(position, value);
        open = null; draw(); ctx.changed(); cells[position - 1].node.focus();
      };
      panel.append(h('p', { class: 'muted' }, 'Change “' + token.text + '” to:'),
        h('div', { class: 'lg-edit-options' }, ...token.alts.map(alt => {
          const b = button({ class: 'lg-tap' + (edits.get(position) === alt ? ' lg-current' : '') }, alt);
          b.addEventListener('click', () => choose(alt));
          return b;
        }), (() => { const b = button({ class: 'btn ghost small' }, 'Keep “' + token.text + '”'); b.addEventListener('click', () => choose(null)); return b; })()));
      const first = panel.querySelector('button'); if (first) first.focus();
    }
    beat.tokens.forEach((token, index) => {
      const position = index + 1;
      const node = token.alts.length ? button({ class: 'lg-token lg-token-open', 'aria-expanded': 'false' }, token.text)
        : h('span', { class: 'lg-token' }, token.text);
      if (token.alts.length) node.addEventListener('click', () => { open = open === position ? null : position; draw(); });
      cells.push({ node, token, position }); row.append(node);
    });
    draw();
    return {
      node: h('div', {}, h('p', { class: 'lg-aim' }, beat.aim), row, count, panel),
      response: () => ({ edits: Object.fromEntries([...edits].map(([position, value]) => [String(position), value])) }),
      mark() { /* the feedback says what the change produced */ },
      lock(solution, fresh) {
        if (!fresh) { edits.clear(); Object.entries(solution.edits).forEach(([position, value]) => edits.set(Number(position), value)); }
        open = null; draw();
        cells.forEach(({ node, token }) => { if (token.alts.length) node.disabled = true; });
      },
    };
  }

  function exploreWidget(beat, ctx) {
    const values = Object.fromEntries(beat.params.map(p => [p.id, p.start])), sliders = new Map();
    const readout = h('dl', { class: 'lg-readout', 'aria-live': 'polite' });
    const view = h('div', { class: 'lg-view' });
    const decimals = p => (String(p.step).split('.')[1] || '').length;
    const compute = override => {
      const scope = Object.assign({}, values, override || {});
      beat.outputs.forEach(o => { try { scope[o.id] = V.evaluate(o.expr, scope); } catch (e) { scope[o.id] = NaN; } });
      return scope;
    };
    function draw() {
      const scope = compute();
      readout.replaceChildren(...beat.outputs.flatMap(o => [h('dt', {}, o.label), h('dd', {}, V.shown(scope[o.id]) + (o.unit ? ' ' + o.unit : ''))]));
      const spec = /^(bars|plot)\s+(\w+)\s+over\s+(\w+)$/.exec(beat.view || '');
      const param = spec && beat.params.find(p => p.id === spec[3]), out = spec && beat.outputs.find(o => o.id === spec[2]);
      view.replaceChildren();
      const graph = /^graph\s+(.+?)\s+x=(-?[\d.]+)\.\.(-?[\d.]+)$/.exec(beat.view || '');
      if (graph) {
        // A curve in x, redrawn with the controls where the reader has put them.
        view.append(V.plot({ fn: x => V.evaluate(graph[1], Object.assign({}, scope, { x })),
          x: [Number(graph[2]), Number(graph[3])], label: graph[1].replace(/\*/g, '·') }));
        return;
      }
      if (!param || !out) return;
      if (spec[1] === 'plot') {
        view.append(V.plot({ fn: x => compute({ [param.id]: x })[out.id], x: [param.min, param.max], label: out.label, variable: param.label }, values[param.id]));
        return;
      }
      const count = Math.round((param.max - param.min) / param.step) + 1, stride = Math.ceil(count / 16), list = [];
      let now = -1;
      for (let i = 0; i < count; i += stride) {
        const x = Number((param.min + i * param.step).toFixed(6));
        if (Math.abs(x - values[param.id]) < param.step * stride / 2 + 1e-9 && now < 0) now = list.length;
        list.push({ label: String(x), value: compute({ [param.id]: x })[out.id] });
      }
      view.append(V.bars({ bars: list, unit: out.unit }, now));
    }
    const controls = h('div', { class: 'lg-controls' });
    beat.params.forEach(p => {
      const id = uid('lg-param'), output = h('output', { for: id, class: 'lg-param-value' });
      const slider = h('input', { type: 'range', id, min: p.min, max: p.max, step: p.step, value: p.start });
      const show = () => { const text = Number(values[p.id]).toFixed(decimals(p)) + (p.unit ? ' ' + p.unit : ''); output.textContent = text; slider.setAttribute('aria-valuetext', text); };
      const set = value => {
        values[p.id] = Number(Math.min(p.max, Math.max(p.min, value)).toFixed(6));
        slider.value = values[p.id]; show(); draw(); ctx.changed();
      };
      slider.addEventListener('input', () => set(Number(slider.value)));
      const less = button({ class: 'lg-nudge', 'aria-label': 'Lower ' + p.label }, '−'), more = button({ class: 'lg-nudge', 'aria-label': 'Raise ' + p.label }, '+');
      less.addEventListener('click', () => set(values[p.id] - p.step));
      more.addEventListener('click', () => set(values[p.id] + p.step));
      sliders.set(p.id, { slider, less, more, show });
      controls.append(h('div', { class: 'lg-control' }, h('label', { for: id }, p.label), h('div', { class: 'lg-control-row' }, less, slider, more, output)));
      show();
    });
    draw();
    return {
      node: h('div', {}, h('p', { class: 'lg-aim' }, beat.aim), controls, view, readout),
      response: () => ({ values: Object.assign({}, values) }),
      mark() { /* the feedback reports the read-out that was checked */ },
      lock(solution, fresh) {
        if (!fresh) Object.assign(values, solution.values);
        sliders.forEach(({ slider, less, more, show }, id) => { slider.value = values[id]; show(); slider.disabled = less.disabled = more.disabled = true; });
        draw();
      },
    };
  }

  function buildWidget(beat, ctx) {
    const picked = [], pieces = new Map();
    const limit = beat.max_slots || beat.bank.length;
    const slot = h('ol', { class: 'order-slot lg-order-slot', 'aria-label': 'What you have built so far' });
    const bank = h('div', { class: 'order-tray lg-order-tray', role: 'group', 'aria-label': 'Pieces to build with' });
    function draw(marks) {
      slot.replaceChildren();
      if (!picked.length) slot.append(h('li', { class: 'muted lg-order-empty' }, 'Tap the pieces you need…'));
      picked.forEach((id, index) => {
        const chip = button({ class: 'order-chip placed lg-chip', 'aria-label': pieces.get(id).textContent + '. Tap to take it back.' }, pieces.get(id).textContent);
        if (marks && marks[index] !== undefined && marks[index] !== null) { chip.classList.add(marks[index] ? 'lg-right' : 'lg-wrong'); chip.prepend(app.mark(marks[index])); }
        chip.addEventListener('click', () => { picked.splice(index, 1); pieces.get(id).disabled = false; draw(); ctx.changed(); pieces.get(id).focus(); });
        slot.append(h('li', {}, chip));
      });
    }
    beat.bank.forEach(piece => {
      const chip = button({ class: 'order-chip lg-chip' }, piece.text);
      chip.addEventListener('click', () => {
        if (picked.length >= limit) { ctx.say('That is as many pieces as this needs. Take one back to swap it.', 'nudge'); return; }
        chip.disabled = true; picked.push(piece.id); draw(); ctx.changed();
        if (ctx.young) app.speakMaybe(piece.text);
        const next = bank.querySelector('.order-chip:not(:disabled)');
        (picked.length >= limit || !next ? ctx.checkButton() : next).focus();
      });
      pieces.set(piece.id, chip); bank.append(chip);
    });
    draw();
    return {
      node: h('div', {}, slot, bank),
      response: () => ({ tokens: picked.slice() }),
      mark(marks) { draw(marks.placed); },
      lock(solution, fresh) {
        if (!fresh) picked.splice(0, picked.length, ...solution.tokens);
        draw(picked.map(() => true));
        slot.querySelectorAll('button').forEach(b => { b.disabled = true; });
        pieces.forEach(c => { c.disabled = true; }); bank.hidden = true;
      },
    };
  }

  function reflectWidget(beat, ctx) {
    const area = h('textarea', { class: 'lg-reflect', rows: '4', 'aria-label': 'Your explanation', placeholder: 'Explain it in your own words…' });
    const model = h('div', { class: 'lg-model' });
    area.addEventListener('input', () => ctx.changed());
    return {
      node: h('div', {}, area, model),
      response: () => ({ text: area.value }),
      mark() { area.focus(); },
      lock(solution) {
        area.disabled = true;
        model.replaceChildren(h('p', { class: 'lg-model-label' }, 'A model answer'), h('p', {}, solution.model));
      },
    };
  }

  const WIDGETS = { predict: choiceWidget, select: choiceWidget, compare: compareWidget, clues: cluesWidget,
    order: orderWidget, match: matchWidget, group: groupWidget, fill: fillWidget, edit: editWidget,
    explore: exploreWidget, build: buildWidget, reflect: reflectWidget };

  /* ------------------------------------------------------------- player */

  function mount(root, data, hooks) {
    hooks = hooks || {};
    const nodeId = data.node_id, base = '/api/learning-games/' + encodeURIComponent(nodeId) + '/';
    let seq = data.current, index = 0, showAll = false;
    const titleId = uid('lg-title');
    root.classList.add('lg-play');
    root.setAttribute('aria-labelledby', titleId);
    root.replaceChildren();
    // Spoken prompts, larger targets and nothing to type: for the youngest
    // modules, and for any sequence a young child opens.
    const young = () => seq.level <= 1 || app.age() < 8;
    const steps = () => seq.beats.filter(beat => beat.kind === 'step');
    const done = () => steps().filter(settled).length;
    const post = (action, body) => request('POST', base + action, Object.assign({ sequence: seq.slug }, body || {}));
    const art = () => {
      const media = data.art;
      if (!media || !media.src) return null;
      return h('figure', { class: 'lg-art' }, h('img', { src: media.src, alt: media.alt || '', loading: 'lazy' }),
        media.caption ? h('figcaption', { class: 'muted' }, media.caption) : null);
    };

    const head = h('div', { class: 'lg-head' });
    const picker = h('div', { class: 'lg-picker' });
    const bar = h('progress', { class: 'lg-progress-bar', max: '1', value: '0', 'aria-label': 'Steps finished in this activity' });
    const counter = h('p', { class: 'lg-counter muted', role: 'status', 'aria-live': 'polite' });
    const dots = h('ol', { class: 'lg-dots', 'aria-label': 'Steps' });
    const stage = h('div', { class: 'lg-stage' });
    const back = button({ class: 'btn ghost small lg-back' }, 'Back');
    const forward = button({ class: 'btn gold lg-forward' }, 'Continue');
    const whole = button({ class: 'btn ghost small lg-whole' });
    const nav = h('div', { class: 'lg-nav' }, back, forward, whole);
    root.append(head, picker, h('div', { class: 'lg-progress' }, bar, counter, dots), stage, nav);

    function drawHead() {
      root.classList.toggle('lg-young', young());
      const statusText = seq.status === 'completed' ? 'Studied' : seq.done ? 'In progress' : 'New';
      head.replaceChildren(
        h('div', { class: 'lg-head-line' }, h('span', { class: 'lg-kicker' }, 'LEARN BY DOING'),
          h('span', { class: 'lg-status lg-status-' + seq.status }, statusText)),
        h('h3', { id: titleId }, seq.title),
        h('p', { class: 'lg-objective' }, h('b', {}, young() ? 'You will learn: ' : 'Objective: '), seq.objective),
        h('p', { class: 'muted lg-note' }, 'Study activity. It builds the idea step by step; the module quiz is what proves it.',
          seq.origin && seq.origin.kind === 'derived' ? ' Every statement here comes from this module’s reporting reference.' : '',
          seq.origin && seq.origin.review_by ? ' Written for Primer and not yet checked by a ' + seq.origin.review_by + '.' : ''));
      if (young()) head.querySelector('h3').after(h('div', { class: 'speak-row' },
        app.speaker(() => seq.title + '. ' + seq.objective, 'Read this aloud'), h('span', { class: 'muted' }, 'Listen')));
    }
    // Keep the header and the activity list honest as steps are settled,
    // rather than leaving them on what was true when the page opened.
    function tally() {
      const entry = data.sequences.find(item => item.slug === seq.slug), finished = done();
      seq.done = finished;
      if (seq.completed) seq.status = 'completed'; else if (finished && seq.status === 'new') seq.status = 'started';
      if (entry) { entry.done = finished; entry.status = seq.status; }
      drawHead(); drawPicker();
    }
    function drawPicker() {
      picker.replaceChildren();
      if (data.sequences.length < 2) return;
      const list = h('ol', { class: 'lg-picker-list', 'aria-label': 'Activities in this module' });
      data.sequences.forEach((entry, n) => {
        const state = entry.status === 'completed' ? 'studied' : entry.done ? entry.done + ' of ' + entry.steps + ' done' : 'new';
        const b = button({ class: 'lg-pick' + (entry.slug === seq.slug ? ' lg-pick-now' : ''), 'aria-current': entry.slug === seq.slug ? 'true' : null },
          h('span', { class: 'lg-pick-n', 'aria-hidden': 'true' }, entry.status === 'completed' ? '✓' : String(n + 1)),
          h('span', {}, h('b', {}, entry.title), h('small', {}, state)));
        b.addEventListener('click', () => { if (entry.slug !== seq.slug) open(entry.slug); });
        list.append(h('li', {}, b));
      });
      picker.append(h('p', { class: 'muted lg-picker-label' }, data.sequences.length + ' activities in this module'), list);
    }
    async function open(slug, focus = true) {
      stage.replaceChildren(h('p', { class: 'muted' }, 'Opening…'));
      try {
        const fresh = await request('GET', '/api/learning-games/' + encodeURIComponent(nodeId) + '?sequence=' + encodeURIComponent(slug));
        data = fresh; seq = fresh.current; index = startIndex(); showAll = false;
        drawHead(); drawPicker(); render(focus);
      } catch (error) { trouble(error, () => open(slug)); }
    }
    function startIndex() {
      if (data.locked) return 0;
      if (seq.finished_run) return seq.beats.length;
      const at = seq.beats.findIndex(beat => beat.id === seq.cursor);
      return at < 0 ? 0 : at;
    }
    function trouble(error, retry) {
      const locked = error && error.status === 409 && error.unlock_requirements;
      const message = locked ? 'This lesson has closed again for now: ' + error.unlock_requirements.join('; ') + '.'
        : 'The book could not be reached just now. Nothing you have done is lost.';
      const live = stage.querySelector('.lg-live');
      if (live && !retry) { live.className = 'lg-live lg-live-nudge'; live.textContent = message; return; }
      const again = button({ class: 'btn' }, 'Try again');
      again.addEventListener('click', () => (retry ? retry() : render(true)));
      stage.replaceChildren(h('p', { role: 'alert' }, message), again);
    }

    function showBeat(beat, lead) {
      const title = beat.kind === 'intro' ? (young() ? 'The idea' : 'The idea') : 'See it work';
      const section = h('section', { class: 'lg-beat lg-show', 'data-beat': beat.id },
        h('h4', { tabindex: '-1', class: 'lg-beat-title' }, title));
      if (young()) section.append(h('div', { class: 'speak-row' }, app.speaker(() => beat.say || beat.text, 'Read this aloud')));
      section.append(h('p', { class: 'lg-text' }, beat.text));
      const drawn = V.draw(beat.visual, { art }) || (beat.kind === 'intro' && !beat.visual ? art() : null);
      if (drawn) section.append(h('div', { class: 'lg-visual' }, drawn));
      if (lead && young()) app.speakMaybe(beat.say || beat.text);
      return section;
    }

    function stepBeat(beat, lead) {
      const number = steps().indexOf(beat) + 1;
      const heading = h('h4', { tabindex: '-1', class: 'lg-beat-title' },
        beat.transfer ? 'Use it somewhere new' : 'Step ' + number + ' of ' + steps().length, ' ',
        h('span', { class: 'lg-kind' }, beat.label));
      const live = h('div', { class: 'lg-live', role: 'status', 'aria-live': 'polite' });
      const hints = h('ul', { class: 'lg-hints', 'aria-label': 'Hints' });
      const after = h('div', { class: 'lg-after' });
      const check = button({ class: 'btn gold lg-check' }, beat.type === 'reflect' ? 'Compare with a model answer' : young() ? 'Check it' : 'Check');
      const hint = button({ class: 'btn ghost small lg-hint' });
      const show = button({ class: 'btn ghost small lg-show-me' }, 'Show me');
      const actions = h('div', { class: 'lg-actions' }, check, hint, show);
      const section = h('section', { class: 'lg-beat lg-step' + (beat.transfer ? ' lg-transfer' : ''), 'data-beat': beat.id }, heading);
      const spoken = () => beat.say || (beat.prompt + (beat.options ? '. ' + beat.options.map(o => o.text).join(', ') : ''));
      const prompt = h('p', { class: 'lg-prompt' }, beat.prompt);
      section.append(young() ? h('div', { class: 'lg-prompt-row' }, app.speaker(spoken, 'Read the question aloud'), prompt) : prompt);
      const drawn = V.draw(beat.visual, { art });
      if (drawn) section.append(h('div', { class: 'lg-visual' }, drawn));
      let busy = false;
      const say = (words, tone) => {
        live.className = 'lg-live lg-live-' + (tone || 'note');
        live.textContent = '';
        // Written a beat later so the same sentence is announced a second time.
        setTimeout(() => { live.textContent = words; }, 30);
      };
      const ctx = { young: young(), visual: { art }, changed: () => { if (!busy) check.disabled = false; },
        post: (action, body) => post(action, Object.assign({ step: beat.id }, body || {})),
        say, check: () => run(), checkButton: () => check, trouble: error => trouble(error) };
      const widget = WIDGETS[beat.type](beat, ctx);
      section.append(h('div', { class: 'lg-widget' }, widget.node), actions, hints, live, after);

      function drawHints() {
        hints.replaceChildren(...beat.state.hints_shown.map(text => h('li', {}, h('b', {}, 'Hint: '), text)));
        const left = beat.hints - beat.state.hints_shown.length;
        hint.hidden = settled(beat) || left <= 0;
        hint.textContent = beat.state.hints_shown.length ? 'Another hint' : 'Hint';
        show.hidden = settled(beat) || !beat.state.can_reveal;
      }
      function finish(fresh, feedback, verdict) {
        widget.lock(beat.state.solution, fresh);
        check.hidden = true; drawHints();
        section.classList.add(beat.state.status === 'solved' ? 'lg-solved' : 'lg-revealed');
        const why = button({ class: 'btn ghost small lg-why', 'aria-expanded': 'false' }, 'Why?');
        const reason = h('div', { class: 'lg-reason', hidden: '' }, h('p', {}, beat.state.why));
        why.addEventListener('click', () => {
          const opening = reason.hidden; reason.hidden = !opening; why.setAttribute('aria-expanded', opening ? 'true' : 'false');
          if (opening && young()) app.speakNow(beat.state.why);
        });
        after.replaceChildren();
        if (beat.state.why) after.append(why, reason);
        if (beat.state.status === 'revealed') { reason.hidden = false; why.setAttribute('aria-expanded', 'true'); }
        if (fresh) {
          const lead = verdict === null ? '' : beat.state.status === 'revealed' ? 'Here is how it goes. '
            : young() ? 'Yes! ' : 'Correct. ';
          say((lead + (feedback || '')).trim() || 'Done.', beat.state.status === 'solved' ? 'right' : 'note');
          if (young()) app.speakMaybe((lead + (feedback || '')).trim());
        }
        if (fresh) tally();
        progress(); drawNav();
        if (fresh && !showAll) setTimeout(() => forward.focus(), 60);
      }
      async function run() {
        if (busy || settled(beat)) return;
        busy = true; check.disabled = true; say('Checking…', 'note');
        try {
          const result = await post('check', { step: beat.id, response: widget.response() });
          beat.state = result.state;
          if (result.completed) seq.completed = result.completed;
          if (result.incomplete) { say(result.feedback, 'nudge'); check.disabled = false; }
          else if (result.correct === false) {
            widget.mark(result.marks || {});
            const lead = young() ? 'Not yet. ' : 'Not quite. ';
            say(lead + (result.feedback || 'Have another look.'), 'wrong');
            if (young()) app.speakMaybe(lead + (result.feedback || ''));
            app.buzz('no'); drawHints();
          } else {
            app.buzz('ok');
            finish(true, result.feedback, result.correct);
            if (result.completed && result.completed.xp_gained) app.growth(result.completed.xp_gained);
          }
        } catch (error) { check.disabled = false; trouble(error); }
        busy = false;
      }
      check.addEventListener('click', run);
      check.disabled = beat.type !== 'explore';
      hint.addEventListener('click', async () => {
        hint.disabled = true;
        try {
          const result = await post('hint', { step: beat.id });
          beat.state = result.state; drawHints();
          const latest = beat.state.hints_shown[beat.state.hints_shown.length - 1];
          if (latest && young()) app.speakNow(latest);
          if (hints.lastElementChild) hints.lastElementChild.setAttribute('tabindex', '-1'), hints.lastElementChild.focus();
        } catch (error) { trouble(error); }
        hint.disabled = false;
      });
      show.addEventListener('click', async () => {
        show.disabled = true;
        try {
          const result = await post('reveal', { step: beat.id });
          beat.state = result.state;
          if (result.completed) seq.completed = result.completed;
          finish(true, '', undefined);
        } catch (error) { show.disabled = false; trouble(error); }
      });
      drawHints();
      if (settled(beat)) finish(false);
      if (lead && young() && !settled(beat)) app.speakMaybe(spoken());
      return section;
    }

    function completion() {
      const c = seq.completed || {}, section = h('section', { class: 'lg-beat lg-done' });
      section.append(h('h4', { tabindex: '-1', class: 'lg-beat-title' }, young() ? 'You did it!' : 'Activity complete'),
        h('p', { class: 'lg-done-label' }, h('span', { class: 'lg-status lg-status-completed' }, 'Studied'),
          ' ', c.steps ? c.first_try + ' of ' + c.steps + ' right first time' + (c.with_help ? ', ' + c.with_help + ' shown by the book' : '') + '.' : ''));
      if (c.xp_gained) section.append(h('p', { class: 'lg-growth' }, '+' + c.xp_gained + ' growth'));
      if (c.cards_added) section.append(h('p', { class: 'muted' }, c.cards_added + (c.cards_added === 1 ? ' review card' : ' review cards') + ' added from the steps that took more than one try.'));
      section.append(h('p', { class: 'lg-text' }, c.message || ''), h('p', { class: 'muted lg-note' }, c.study_note || data.study_note));
      const acts = h('div', { class: 'lg-actions' });
      if (c.next_sequence) { const b = button({ class: 'btn gold' }, 'Next: ' + c.next_sequence.title); b.addEventListener('click', () => open(c.next_sequence.slug)); acts.append(b); }
      if (c.has_quiz && typeof startQuiz === 'function') { const b = button({ class: c.next_sequence ? 'btn' : 'btn gold' }, 'Take the quiz'); b.addEventListener('click', () => startQuiz(nodeId)); acts.append(b); }
      if (c.practice && typeof startPractice === 'function') { const b = button({ class: 'btn' }, 'Practise'); b.addEventListener('click', () => startPractice(nodeId, c.practice, data.stage)); acts.append(b); }
      const again = button({ class: 'btn ghost' }, 'Play again');
      again.addEventListener('click', async () => { again.disabled = true; try { await post('restart'); await open(seq.slug); } catch (error) { again.disabled = false; trouble(error); } });
      acts.append(again);
      section.append(acts);
      const more = (data.activities || []).filter(a => ['model', 'activity', 'reference'].includes(a.kind));
      if (more.length) {
        const list = h('ul', { class: 'lg-more' });
        more.forEach(activity => {
          let control;
          if (activity.kind === 'activity') control = h('a', { href: activity.href }, activity.label);
          else {
            control = button({ class: 'lg-link' }, activity.label);
            control.addEventListener('click', () => {
              if (activity.kind === 'reference' && typeof go === 'function') { go('radiology', nodeId); return; }
              const target = hooks.page && hooks.page.querySelector('.lesson-media');
              if (target) { target.setAttribute('tabindex', '-1'); target.scrollIntoView({ block: 'start' }); target.focus({ preventScroll: true }); }
            });
          }
          list.append(h('li', {}, control));
        });
        section.append(h('p', { class: 'lg-more-label' }, 'More ways to explore this idea'), list);
      }
      if (young()) app.speakMaybe('You did it! ' + (c.message || ''));
      return section;
    }

    function progress() {
      const total = steps().length, finished = done();
      bar.max = Math.max(1, total); bar.value = finished;
      const at = index >= seq.beats.length ? null : seq.beats[index];
      counter.textContent = data.locked ? 'Questions open with this lesson.'
        : showAll ? finished + ' of ' + total + ' steps done.'
        : !at ? 'All ' + total + ' steps done.'
        : at.kind === 'step' ? 'Step ' + (steps().indexOf(at) + 1) + ' of ' + total + '. ' + finished + ' done.'
        : (at.kind === 'intro' ? 'The idea' : 'A worked example') + ', then ' + total + ' steps.';
      const reach = seq.beats.findIndex(beat => !settled(beat));
      dots.replaceChildren(...seq.beats.map((beat, i) => {
        const open = reach < 0 || i <= reach, label = beat.kind === 'step' ? 'Step ' + (steps().indexOf(beat) + 1) : beat.kind === 'intro' ? 'The idea' : 'Worked example';
        const state = beat.kind !== 'step' ? '' : beat.state.status === 'solved' ? ', done' : beat.state.status === 'revealed' ? ', shown' : '';
        const b = button({ class: 'lg-dot' + (settled(beat) && beat.kind === 'step' ? ' lg-dot-done' : '') + (i === index && !showAll ? ' lg-dot-now' : ''),
          'aria-label': label + state, 'aria-current': i === index && !showAll ? 'step' : null, disabled: open ? null : '' },
          beat.kind === 'step' ? (settled(beat) ? '✓' : String(steps().indexOf(beat) + 1)) : beat.kind === 'intro' ? 'i' : 'e');
        b.addEventListener('click', () => { showAll = false; index = i; render(true); });
        return h('li', {}, b);
      }));
    }
    function drawNav() {
      const last = index >= seq.beats.length, at = last ? null : seq.beats[index];
      back.disabled = showAll || index === 0;
      forward.hidden = showAll || last || data.locked && index >= seq.beats.length - 1;
      forward.disabled = !last && at && !settled(at);
      forward.textContent = at && index === seq.beats.length - 1 ? 'Finish' : at && at.kind === 'intro' ? 'See it work' : at && at.kind === 'demo' ? 'Start the steps' : 'Continue';
      whole.textContent = showAll ? 'One step at a time' : 'Show the whole activity';
      whole.hidden = data.locked;
    }
    function render(focus) {
      stage.replaceChildren();
      if (showAll) {
        seq.beats.forEach(beat => stage.append(beat.kind === 'step' ? stepBeat(beat, false) : showBeat(beat, false)));
        if (seq.completed && done() === steps().length) stage.append(completion());
      } else if (index >= seq.beats.length) stage.append(completion());
      else {
        const beat = seq.beats[index];
        stage.append(beat.kind === 'step' ? stepBeat(beat, focus) : showBeat(beat, focus));
        if (!data.locked) post('cursor', { beat: beat.id }).catch(() => {});
      }
      if (data.locked) stage.append(h('p', { class: 'muted locked-why lg-locked' },
        'The checked steps open when this lesson does' + ((data.unlock_requirements || []).length ? ': ' + data.unlock_requirements.join('; ') + '.' : '.')
        + ' You are welcome to read the idea meanwhile.'));
      progress(); drawNav();
      if (focus) { const heading = stage.querySelector('.lg-beat-title'); if (heading) heading.focus({ preventScroll: showAll }); }
    }
    back.addEventListener('click', () => { index = Math.max(0, index - 1); render(true); });
    forward.addEventListener('click', () => { index = Math.min(seq.beats.length, index + 1); render(true); });
    whole.addEventListener('click', () => { showAll = !showAll; render(true); });
    if (app.calm()) root.classList.add('lg-calm');
    index = startIndex();
    drawHead(); drawPicker(); render(false);
    return { open, get sequence() { return seq.slug; } };
  }

  const api = Object.freeze({ mount, request });
  scope.PrimerLearningGames = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
