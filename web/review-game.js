/* Memory Garden — a quiet game built on the Primer's real review schedule.
   This module owns only its mounted subtree. Answers typed here never leave
   the browser; ratings use the dedicated revision-checked game endpoint. */
(function () {
  'use strict';

  async function render(page, ctx) {
    const { el, btn, api, glyph, speakBtn, stopSpeaking, go, whenDay } = ctx;
    const young = Number(ctx.stage) <= 1;
    const root = el('section', { class: 'memory-game' + (young ? ' memory-game-young' : ''),
      'aria-label': 'Memory Garden spaced repetition game' });
    page.append(root);
    const alive = () => root.isConnected && page.contains(root) && (!ctx.isCurrent || ctx.isCurrent());
    let data = null, requested = 5, loadSeq = 0, cards = [], results = [];
    let index = 0, shownAt = 0, phase = 'loading', saving = false, earned = 0;
    let cardHost, gardenHost, roundStatus, grades = [], revealButton, nextButton;

    function focus(node) {
      // Routing also moves focus. The task must still own this node when the
      // callback runs: a response or animation frame must not hijack a new page.
      const activeWhenScheduled = document.activeElement;
      requestAnimationFrame(() => {
        if (!alive() || !root.contains(node)) return;
        const activeNow = document.activeElement;
        // A reader may already have clicked into their answer while this
        // frame waited. Their newer focus wins over our explanatory heading.
        if (activeNow !== activeWhenScheduled && root.contains(activeNow)
          && (activeNow.matches('input, textarea, select, button, a[href], [contenteditable="true"]')
            || activeNow.isContentEditable)) return;
        node.focus();
      });
    }
    function heading(text, tag = 'h2') {
      return el(tag, { tabindex: '-1' }, text);
    }
    function speech(text, label) {
      return speakBtn(() => text, label);
    }
    function stopVoice() { if (stopSpeaking) stopSpeaking(); }
    function duePhrase(timestamp) {
      if (timestamp == null || !Number.isFinite(Number(timestamp))) return 'at its next scheduled visit';
      const date = new Date(Number(timestamp) * 1000);
      const now = new Date();
      const sameDay = date.toDateString() === now.toDateString();
      const day = sameDay ? 'today' : 'on ' + date.toLocaleDateString(undefined, { month: 'short', day: 'numeric',
        ...(date.getFullYear() !== now.getFullYear() ? { year: 'numeric' } : {}) });
      return day + ' at ' + date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
    }
    function plant(state, number) {
      const drawing = state === 'grown'
        ? '<path d="M35 76V30M35 61C16 63 12 48 14 44c14 0 21 6 21 17M35 49c17 1 24-10 24-15-15-1-23 5-24 15"/><g class="mg-petals"><ellipse cx="35" cy="21" rx="7" ry="12"/><ellipse cx="35" cy="21" rx="7" ry="12" transform="rotate(60 35 28)"/><ellipse cx="35" cy="21" rx="7" ry="12" transform="rotate(120 35 28)"/></g><circle class="mg-flower-heart" cx="35" cy="28" r="6"/>'
        : state === 'watered'
          ? '<path d="M35 76V51M35 62c-13 1-19-6-19-12 12-1 19 4 19 12M35 55c12 1 18-5 18-11-11-1-18 4-18 11"/><path class="mg-water" d="M52 19c-2 4-5 7-5 10a5 5 0 0 0 10 0c0-3-3-6-5-10Z"/>'
          : '<path class="mg-seed" d="M29 71c0-8 12-13 12-5 0 9-12 13-12 5Z"/>';
      return el('div', { class: 'mg-plot mg-plot-' + state, 'aria-hidden': 'true' },
        el('span', { class: 'mg-plot-number' }, String(number)),
        el('span', { class: 'mg-plant', html: '<svg viewBox="0 0 70 92" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + drawing + '<path class="mg-soil" d="M12 79c12-4 34-4 46 0M20 85h30"/></svg>' }));
    }
    function garden(total, saved) {
      const bed = el('div', { class: 'mg-garden', role: 'img',
        'aria-label': saved.filter(r => !r.early).length + ' of ' + total + ' reviews saved; '
          + saved.filter(r => !r.early && r.quality >= 3).length + ' flowers grown.' });
      for (let i = 0; i < total; i++) {
        const r = saved[i];
        bed.append(plant(!r || r.early ? 'seed' : r.quality >= 3 ? 'grown' : 'watered', i + 1));
      }
      return bed;
    }
    function countFor(d) {
      const available = Array.isArray(d.cards) ? d.cards.length : 0;
      const ask = Number(d.goal);
      return Math.max(0, Math.min(requested, available, ask > 0 ? ask : requested));
    }
    function frame() {
      root.replaceChildren();
      root.append(el('header', { class: 'mg-heading pagehead' },
        el('p', { class: 'mg-eyebrow kicker' }, glyph('review', 16), 'SPACED REPETITION'),
        heading('Memory Garden'),
        el('p', { class: 'mg-deck' }, young
          ? 'Remember a little. Help your garden grow.'
          : 'A little remembering. A little growing. Come back when your memories are ready.')));
    }
    async function load() {
      const seq = ++loadSeq;
      phase = 'loading';
      frame();
      root.append(el('p', { class: 'mg-load', role: 'status' }, 'Finding the memories ready for a visit…'));
      try {
        const loaded = await api.get('/api/review/due?limit=30&dose=' + (requested === 5 ? 'short' : 'full'));
        if (!alive() || seq !== loadSeq) return;
        if (!loaded || loaded.error || !Array.isArray(loaded.cards)) throw new Error('Unavailable review deck');
        data = loaded;
        lobby();
      } catch (err) {
        if (!alive() || seq !== loadSeq) return;
        phase = 'load-error';
        frame();
        root.append(el('div', { class: 'mg-empty' }, heading('The garden could not open', 'h3'),
          el('p', { role: 'alert' }, 'Your memories are still safe. Please try loading the garden again.'),
          btn({ class: 'btn gold mg-retry', onclick: load }, 'Try again')));
      }
    }
    function empty() {
      phase = 'empty';
      const hasCards = Number(data.stats && data.stats.total) > 0;
      const title = heading(hasCards ? 'Let your memories rest' : 'Your garden begins with a lesson', 'h3');
      const next = data.stats && data.stats.next_due;
      root.append(el('div', { class: 'mg-empty' },
        el('div', { class: 'mg-empty-mark', 'aria-hidden': 'true' }, glyph(hasCards ? 'moon' : 'spark', 34)),
        title,
        el('p', {}, hasCards ? 'Nothing is due right now. Rest between visits is part of remembering.'
          : 'Complete a lesson or save a memory card. When it is due, it will be ready to grow here.'),
        next != null ? el('p', { class: 'mg-next-due' }, 'Your next memory returns ' + whenDay(next) + '.') : null,
        el('div', { class: 'mg-actions' },
          btn({ class: 'btn gold', onclick: () => go('atlas') }, 'Explore a lesson'),
          btn({ class: 'btn ghost', onclick: load }, 'Check for due cards'),
          btn({ class: 'btn ghost mg-classic', onclick: () => go('review') }, 'Classic review'))));
    }
    function lobby() {
      phase = 'lobby';
      frame();
      if (!data.cards.length) { empty(); return; }
      const n = countFor(data);
      const due = Number(data.stats && data.stats.due) || data.cards.length;
      const preview = el('section', { class: 'mg-welcome', 'aria-label': 'Choose a garden round' });
      const copy = el('div', { class: 'mg-welcome-copy' },
        el('p', { class: 'mg-eyebrow' }, due + (due === 1 ? ' MEMORY READY' : ' MEMORIES READY')),
        heading(young ? 'Let’s visit ' + n + ' memories' : 'Give ' + n + ' memories room to grow', 'h3'),
        el('p', {}, young ? 'Listen. Say what you remember. Turn the card and see how you did. A grown-up can help.'
          : 'Recall an answer before turning the card. Then tell the book how it felt. Your rating sets the next visit.'),
        el('p', { class: 'mg-kind-note' }, 'Choose your pace. A little space between visits helps memories grow.'));
      const choices = el('fieldset', { class: 'mg-round-options' }, el('legend', {}, 'Choose your round'));
      [5, 10].forEach(nominal => {
        choices.append(btn({ class: 'mg-round-choice', 'aria-pressed': String(requested === nominal),
          onclick: () => { if (requested !== nominal) { requested = nominal; load(); } } },
          el('strong', {}, nominal === 5 ? 'Little garden' : 'Growing garden'),
          el('span', {}, 'Up to ' + nominal + ' cards')));
      });
      copy.append(choices,
        btn({ class: 'btn gold mg-start', onclick: start }, 'Start ' + n + '-card round', glyph('spark', 18)));
      if (n < requested) copy.append(el('p', { class: 'mg-note' }, 'A ' + n + '-card round fits the cards due and your daily review goal.'));
      preview.append(copy, el('div', { class: 'mg-preview' }, garden(n, []),
        el('p', { class: 'mg-garden-caption' }, 'One plot for each memory you visit.')));
      root.append(preview,
        el('ol', { class: 'mg-how', 'aria-label': 'How to play' },
          el('li', {}, el('span', {}, '01'), el('strong', {}, 'Remember'), el('p', {}, 'Say it, think it, or write it.')),
          el('li', {}, el('span', {}, '02'), el('strong', {}, 'Compare'), el('p', {}, 'Turn the card. Rate your own recall.')),
          el('li', {}, el('span', {}, '03'), el('strong', {}, 'Return'), el('p', {}, 'The book schedules your next visit.'))),
        btn({ class: 'btn ghost small mg-classic', onclick: () => go('review') }, 'Classic review'));
    }
    function start() {
      if (phase !== 'lobby') return;
      stopVoice();
      cards = data.cards.slice(0, countFor(data));
      results = []; index = 0; earned = 0;
      frame();
      roundStatus = el('div', { class: 'mg-round-status' });
      gardenHost = el('div', { class: 'mg-round-garden' });
      cardHost = el('div', { class: 'mg-card-host' });
      root.append(roundStatus, gardenHost, cardHost,
        el('div', { class: 'mg-footer' }, el('span', {}, 'Remember first, then compare. Take the time you need.'),
          btn({ class: 'btn ghost small mg-leave', onclick: () => { stopVoice(); go('today'); } }, 'Finish for now')));
      drawCard();
    }
    function progress() {
      const saved = results.filter(r => !r.early).length;
      roundStatus.replaceChildren(el('span', {}, 'Your memory garden'),
        el('strong', { class: 'mg-progress-text' }, results.length + ' / ' + cards.length + ' visited'),
        el('span', { class: 'mg-earned' }, earned + ' XP earned'));
      gardenHost.replaceChildren(garden(cards.length, results));
      gardenHost.dataset.saved = String(saved);
    }
    function drawCard() {
      if (!alive()) return;
      stopVoice();
      if (index >= cards.length) { complete(); return; }
      phase = 'recall'; saving = false; grades = []; nextButton = null;
      shownAt = Date.now();
      progress();
      const card = cards[index];
      const panel = el('article', { class: 'mg-card', 'aria-label': 'Memory ' + (index + 1) + ' of ' + cards.length });
      const title = heading(card.front, 'h3'); title.className = 'mg-question';
      panel.append(el('div', { class: 'mg-card-top' },
        el('span', { class: 'mg-eyebrow' }, 'MEMORY ' + (index + 1) + ' OF ' + cards.length),
        speech(card.front, 'Read the question aloud')));
      if (card.article) panel.append(el('p', { class: 'mg-source' }, card.article));
      panel.append(title, el('p', { class: 'mg-recall-help' }, young ? 'Say your answer out loud. It is okay to be unsure.' : 'Before you turn the card, bring the answer to mind.'));
      let writing = null;
      if (!young) {
        const id = 'memory-answer-' + index;
        writing = el('textarea', { id, class: 'mg-recall-input', rows: '2',
          placeholder: 'An idea, a few words, or your explanation…', autocomplete: 'off', spellcheck: 'true' });
        panel.append(el('label', { for: id, class: 'mg-input-label' }, 'Write what you remember (optional)'), writing);
      }
      const answer = el('div', { class: 'mg-answer-region', 'aria-live': 'polite' });
      revealButton = btn({ class: 'btn gold mg-reveal', onclick: () => {
        if (phase !== 'recall' || !alive()) return;
        phase = 'revealed'; stopVoice(); revealButton.disabled = true; revealButton.hidden = true;
        if (writing) writing.readOnly = true;
        const answerTitle = heading(young ? 'Here is the answer' : 'Compare with the answer', 'h4');
        answer.append(el('div', { class: 'mg-answer' },
          el('div', { class: 'mg-answer-title' }, answerTitle, speech(card.back, 'Read the answer aloud')),
          el('p', { class: 'mg-answer-text' }, card.back)),
          el('p', { class: 'mg-grade-prompt' }, young ? 'Did you remember it? You choose.' : 'How well did you recall it? This is your own rating.'));
        const row = el('div', { class: 'mg-grades', role: 'group', 'aria-label': 'Rate your own recall' });
        const options = young
          ? [[2, 'Not yet', 'Let’s practise again', 'unsure'], [4, 'I remembered', 'I knew the answer', 'known']]
          : [[2, 'Again', 'I missed it', 'review'], [3, 'Hard', 'Recalled with effort', 'unsure'], [4, 'Remembered', 'Recalled correctly', 'known'], [5, 'Easy', 'Recalled easily', 'spark']];
        grades = options.map(([quality, label, hint, icon], k) => {
          const b = btn({ class: 'mg-grade mg-grade-' + quality, dataset: { quality },
            onclick: () => save(card, quality, label, panel, row) }, glyph(icon, 22),
            el('strong', {}, label), el('span', {}, hint), el('kbd', { 'aria-hidden': 'true' }, String(k + 1)));
          row.append(b); return b;
        });
        answer.append(row);
        focus(answerTitle);
      } }, 'Turn the card', el('kbd', { 'aria-hidden': 'true' }, 'Space'));
      panel.append(revealButton, answer);
      cardHost.replaceChildren(panel);
      focus(title);
    }
    async function save(card, quality, label, panel, row) {
      if (!alive() || saving || phase !== 'revealed') return;
      saving = true;
      grades.forEach(b => { b.disabled = true; });
      let status = panel.querySelector('.mg-save-status');
      if (!status) { status = el('div', { class: 'mg-save-status', role: 'status', 'aria-live': 'polite' }); panel.append(status); }
      status.textContent = 'Saving your visit…';
      try {
        const response = await api.post('/api/review/game', { card_id: card.id, quality,
          seconds: Math.max(0, (Date.now() - shownAt) / 1000),
          expected_due: card.due, expected_reviews: card.reviews || 0 });
        if (!alive() || !cardHost.contains(panel)) return;
        // The existing endpoint reports a missing card with HTTP 200. Neither
        // it nor malformed output is a saved memory or a reason to advance.
        if (!response || response.error || String(response.id) !== String(card.id)
          || (response.accepted !== true && response.stale !== true && response.early !== true)) {
          const missing = response && response.error === 'no such card';
          throw new Error(missing ? 'missing-card' : 'save-failed');
        }
        const early = response.accepted !== true || response.stale === true || response.early === true;
        const xp = early ? 0 : Math.max(0, Number(response.xp_gained) || 0);
        results.push({ quality, label, early, xp, next_due: response.next_due });
        earned += xp;
        phase = 'feedback'; saving = false;
        row.setAttribute('aria-label', 'Your rating: ' + label);
        grades.forEach(b => { if (Number(b.dataset.quality) === quality) b.classList.add('mg-chosen'); });
        progress();
        status.className = 'mg-save-status mg-feedback' + (early ? ' mg-feedback-early' : '');
        const feedbackTitle = heading(early ? 'This memory was already visited' : quality >= 3 ? 'A memory takes root' : 'A little more care for this one', 'h4');
        status.replaceChildren(feedbackTitle,
          el('p', {}, early ? 'Another review already updated this memory. This visit earns no new review credit or XP.'
            : quality >= 3 ? 'Your recall rating is saved. ' + (xp ? '+' + xp + ' XP earned.' : 'No XP was awarded for this visit.')
              : 'Your “' + label + '” rating is saved. No XP earned. Read the answer, then give this memory time to settle.'),
          el('p', { class: 'mg-return-date' }, 'This memory returns ' + duePhrase(response.next_due) + '.'));
        nextButton = btn({ class: 'btn gold mg-next', onclick: () => {
          if (phase !== 'feedback') return;
          index++; drawCard();
        } }, index + 1 >= cards.length ? 'See my garden' : 'Next memory', glyph('spark', 17));
        status.append(nextButton);
        focus(feedbackTitle);
        // A saved response must never be treated as failed because chrome
        // refresh or decorative feedback failed after the server committed it.
        if (xp && ctx.flyXP && !(ctx.reducedMotion && ctx.reducedMotion())) { try { ctx.flyXP(xp); } catch (_) {} }
        if (ctx.refreshStats) Promise.resolve().then(() => { if (alive()) return ctx.refreshStats(); }).catch(() => {});
      } catch (err) {
        if (!alive() || !cardHost.contains(panel)) return;
        saving = false;
        grades.forEach(b => { b.disabled = false; });
        status.className = 'mg-save-status mg-save-error';
        status.replaceChildren(el('p', { role: 'alert' }, err.message === 'missing-card'
          ? 'This card is no longer in your deck. Reload the garden to pick up the current due cards.'
          : 'We could not confirm that your rating saved. The card stays here. Try your rating again; an already-saved visit will not earn duplicate XP.'),
          btn({ class: 'btn ghost small', onclick: load }, 'Reload garden'));
      }
    }
    async function complete() {
      phase = 'complete'; stopVoice(); progress();
      const saved = results.filter(r => !r.early);
      const flowers = saved.filter(r => r.quality >= 3).length;
      const title = heading('A good place to let things grow', 'h3');
      const panel = el('section', { class: 'mg-complete' },
        el('p', { class: 'mg-eyebrow' }, 'ROUND COMPLETE'), title,
        el('p', {}, young ? 'You gave your memories a little care. They will be here when it is time to return.'
          : 'Your visits are saved. Leave some space between now and the next time you recall them.'),
        el('div', { class: 'mg-summary' },
          el('div', {}, el('strong', {}, String(saved.length)), el('span', {}, 'reviews saved')),
          el('div', {}, el('strong', {}, String(flowers)), el('span', {}, 'flowers grown')),
          el('div', {}, el('strong', {}, String(earned)), el('span', {}, 'XP earned'))));
      const timings = el('div', { class: 'mg-schedule' }, heading('Your next visits', 'h4'));
      const times = new Map();
      saved.forEach(r => { const text = duePhrase(r.next_due); times.set(text, (times.get(text) || 0) + 1); });
      if (times.size) {
        const list = el('ul');
        times.forEach((n, text) => list.append(el('li', {}, n + (n === 1 ? ' memory returns ' : ' memories return ') + text + '.')));
        timings.append(list);
      } else timings.append(el('p', {}, 'No new reviews were recorded. The existing schedules stay in place.'));
      if (results.some(r => r.early)) timings.append(el('p', { class: 'mg-note' }, 'Already-visited cards earned no new credit.'));
      const actions = el('div', { class: 'mg-actions' }, btn({ class: 'btn gold', onclick: () => go('today') }, 'Finish for today'));
      const remaining = el('p', { class: 'mg-note', role: 'status' }, 'Checking when your garden needs you again…');
      panel.append(timings, actions, remaining);
      cardHost.replaceChildren(panel); focus(title);
      try {
        const fresh = await api.get('/api/review/due?limit=30&dose=' + (requested === 5 ? 'short' : 'full'));
        if (!alive() || phase !== 'complete' || !cardHost.contains(panel)) return;
        if (!fresh || fresh.error || !Array.isArray(fresh.cards)) throw new Error('Unavailable review deck');
        // A round never loops over its just-rated cards. Continuing fetches
        // the due deck again; even a lapse must wait for its real due time.
        if (fresh.cards.length) {
          remaining.textContent = (Number(fresh.stats && fresh.stats.due) || fresh.cards.length) + ' more memories are due. You can stop here or choose another small round.';
          actions.append(btn({ class: 'btn ghost mg-continue', onclick: () => { data = fresh; lobby(); focus(root.querySelector('h3')); } }, 'Choose another round'));
        } else {
          const next = fresh.stats && fresh.stats.next_due;
          remaining.textContent = next != null ? 'Nothing else is due now. Your next memory returns ' + whenDay(next) + '.'
            : 'Nothing else is due now. Your garden can rest.';
        }
      } catch (_) {
        if (alive() && cardHost.contains(panel)) {
          remaining.textContent = 'Your reviews are saved. We could not check the remaining deck.';
          actions.append(btn({ class: 'btn ghost', onclick: load }, 'Check due cards'));
        }
      }
    }
    // Local shortcuts disappear with this subtree. Native button Space/Enter
    // remains native; typing and assistive-technology modifier keys are untouched.
    root.addEventListener('keydown', e => {
      if (e.defaultPrevented || e.repeat || e.metaKey || e.ctrlKey || e.altKey || e.shiftKey || saving) return;
      const target = e.target;
      if (target && (target.closest('input, textarea, select') || target.isContentEditable)) return;
      if (e.key === ' ' && !(target && target.closest('button, a'))) {
        const control = phase === 'recall' ? revealButton : phase === 'feedback' ? nextButton : null;
        if (control && !control.disabled) { e.preventDefault(); control.click(); }
      }
      if (phase === 'revealed' && /^[1-4]$/.test(e.key)) {
        const control = grades[Number(e.key) - 1];
        if (control && !control.disabled) { e.preventDefault(); control.click(); }
      }
    });
    await load();
  }

  window.PrimerReviewGame = { render };
}());
