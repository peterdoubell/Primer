/* The Primer — front-end application. Vanilla JS, no build step.
   Accessible (keyboard, ARIA, focus, reduced-motion, dark mode), age-adaptive,
   hash-routed, and game-like. */
'use strict';

const api = {
  async get(path) { const r = await fetch(path); if (!r.ok) throw await r.json().catch(() => ({ error: r.statusText })); return r.json(); },
  async post(path, body) { const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }); if (!r.ok) throw await r.json().catch(() => ({ error: r.statusText })); return r.json(); },
};

const S = { state: null, domains: [], view: 'today', stage: 2, speak: true, curriculum: null, restoreFocus: null };
// The review deck's document-level keydown handler, held here so leaving the
// page can remove it deterministically — its old self-removal only fired on
// the *next* keypress after the deck was gone.
let _reviewKeyHandler = null;
const $ = (s, r = document) => r.querySelector(s);
const STAGE_NAMES = ['Seedling', 'Sprout', 'Sapling', 'Tree', 'Grove', 'Forest'];

function el(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null) continue;
    if (k === 'class') e.className = v;
    else if (k === 'html') e.innerHTML = v;
    else if (k === 'dataset') Object.assign(e.dataset, v);
    else if (k.startsWith('on') && typeof v === 'function') e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const kid of kids) { if (kid == null) continue; e.append(kid.nodeType ? kid : document.createTextNode(kid)); }
  return e;
}
// Semantic button helper — everything clickable is a real <button>.
function btn(props, ...kids) { return el('button', { type: 'button', ...props }, ...kids); }

/* ---------------- drawn glyphs ----------------
   Emoji were standing in for iconography: they render as a different picture
   on every platform (and as full-colour cartoons beside a page of engraved
   serif type), so the one part of the interface meant to be wordless was the
   least controlled thing on screen. These are drawn instead — one stroke
   weight, one geometry, inheriting currentColor so they gild in day mode and
   phosphoresce at night. Each is a plain noun a child can name aloud, which
   is the only test an icon in this book has to pass. */
const GLYPHS = {
  // A sun clearing a horizon rule.
  today: '<circle cx="12" cy="12" r="4.2"/><path d="M3 20h18"/><path d="M12 3.2v2M12 19v1.2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M3.2 12h2M18.8 12h2M5.2 18.8l1.4-1.4M17.4 6.6l1.4-1.4"/>',
  // A compass rose: the whole map, oriented.
  atlas: '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
  // Return: the loop that brings a thing back.
  review: '<path d="M20 12a8 8 0 1 1-2.7-6"/><path d="M20 4v5h-5"/>',
  // A lens over the page.
  lookup: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.4 15.4L21 21"/>',
  // An open book with a spark rising from the gutter — the Primer itself.
  story: '<path d="M3 5.5c3-1.2 6-1.2 9 0v13c-3-1.2-6-1.2-9 0z"/><path d="M21 5.5c-3-1.2-6-1.2-9 0v13c3-1.2 6-1.2 9 0z"/><path d="M12 3.6l.9-1.8.9 1.8 1.8.9-1.8.9-.9 1.8-.9-1.8-1.8-.9z"/>',
  // The chronicle itself: a spine of days with the moments marked on it.
  // (Distinct on purpose from `path`, which forks forward — this one only
  // ever runs backward, and an earlier draft of it read as a capital A.)
  journey: '<path d="M7 3.5v17"/><circle cx="7" cy="7" r="2"/><circle cx="7" cy="12.5" r="2"/><circle cx="7" cy="18" r="2"/><path d="M11.5 7h8M11.5 12.5h6M11.5 18h7"/>',
  // A branching path: the plan, forking forward.
  path: '<path d="M6 21V9"/><circle cx="6" cy="6" r="2.4"/><path d="M6 12h6a3 3 0 0 0 3-3V8"/><circle cx="15" cy="5.6" r="2.2"/><path d="M6 17h9a3 3 0 0 0 3-3v-1"/><circle cx="18" cy="10.6" r="2.2"/>',
  // A flame, for the streak. Drawn rather than 🔥 so it sits at the same
  // stroke weight as everything else on the line instead of shouting.
  flame: '<path d="M12 2.8c.6 3.4 3 4.6 4.4 6.6a7 7 0 1 1-11.4 5.4c0-3 1.6-4.7 3-6.2.3 1 .9 1.8 1.7 2.3.5-3.4 1.3-6 2.3-8.1z"/><path d="M12 20a3.4 3.4 0 0 0 3.4-3.4c0-1.7-1.4-2.7-2.3-4-1 1.3-2.4 2.1-2.4 4A3.3 3.3 0 0 0 12 20z"/>',
  // A speaker with one arc: read this aloud.
  speak: '<path d="M4 9.5h3.5L12 5.5v13L7.5 14.5H4z"/><path d="M15.6 9.4a4 4 0 0 1 0 5.2"/><path d="M18 7a7.5 7.5 0 0 1 0 10"/>',
  // The same speaker, struck through: the voice is off.
  mute: '<path d="M4 9.5h3.5L12 5.5v13L7.5 14.5H4z"/><path d="M16 10l5 4M21 10l-5 4"/>',
  // A nib: write it back in your own words.
  quill: '<path d="M4 20s1.2-4.6 4.6-8S17 5 20 4c-.6 3.4-2.4 8.6-5.8 11.4S4 20 4 20z"/><path d="M9 15c1.6-2.4 3.6-4.2 6-5.6"/>',
  // A closed padlock: not yet, rather than never.
  lock: '<rect x="4.8" y="10.5" width="14.4" height="9.7" rx="2"/><path d="M8.2 10.5V7.8a3.8 3.8 0 0 1 7.6 0v2.7"/>',
  // A crescent: a chapter set aside for later.
  moon: '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.6 8.6 0 1 0 10.5 10.5z"/>',
  // A target: aim, practice, calibration.
  target: '<circle cx="12" cy="12" r="8.2"/><circle cx="12" cy="12" r="4.4"/><circle cx="12" cy="12" r="1"/>',
  // A die mid-roll: take me somewhere unplanned.
  dice: '<rect x="4.2" y="4.2" width="15.6" height="15.6" rx="3.2"/><circle cx="9" cy="9" r="1.1"/><circle cx="15" cy="15" r="1.1"/><circle cx="15" cy="9" r="1.1"/><circle cx="9" cy="15" r="1.1"/>',
  // A globe: the whole encyclopedia, not just your shelf.
  globe: '<circle cx="12" cy="12" r="8.6"/><path d="M3.4 12h17.2"/><path d="M12 3.4c2.4 2.4 3.6 5.4 3.6 8.6S14.4 18.2 12 20.6c-2.4-2.4-3.6-5.4-3.6-8.6S9.6 5.8 12 3.4z"/>',
  // A laurel-less crown: the day is complete.
  crown: '<path d="M4 17.5h16"/><path d="M4 8.5l3.4 3.2L12 5.8l4.6 5.9L20 8.5v6.2H4z"/>',
  // Slabs on a shelf — archives, not paperbacks.
  shelf: '<path d="M3 20h18"/><rect x="4.5" y="7" width="3.6" height="11"/><rect x="9.6" y="4.5" width="3.6" height="13.5"/><rect x="14.7" y="9" width="3.6" height="9"/>',
  // A question mark, drawn — the young reader's "not sure". The 🤔 it
  // replaces rendered as a full-colour cartoon amid engraved stroke icons,
  // the same breach the padlock fix removed.
  unsure: '<path d="M8.4 9.2a3.6 3.6 0 1 1 5.4 3.1c-1.1.7-1.8 1.5-1.8 2.9"/><circle cx="12" cy="18.8" r="0.9" fill="currentColor" stroke="none"/>',
  // A four-point star, drawn. The unknown-domain tag used the typeface's
  // '✦' — a text character standing in among stroke marks, which is the
  // same one-geometry breach the emoji purge removed everywhere else.
  spark: '<path d="M12 3.4c.9 4.1 2.6 5.8 6.7 6.7-4.1.9-5.8 2.6-6.7 6.7-.9-4.1-2.6-5.8-6.7-6.7 4.1-.9 5.8-2.6 6.7-6.7z"/><path d="M18.2 15.4c.4 1.8 1.1 2.5 2.9 2.9-1.8.4-2.5 1.1-2.9 2.9-.4-1.8-1.1-2.5-2.9-2.9 1.8-.4 2.5-1.1 2.9-2.9z"/>',
  // A single stroke of certainty: the check, for "I know it".
  known: '<path d="M4.5 13l5 5L19.5 6.5"/>',
};
function glyph(name, size) {
  const s = size || 20;
  // aria-hidden: every one of these sits beside its own visible text label,
  // so announcing it again would only make the nav twice as long to hear.
  return el('span', { class: 'glyph', 'aria-hidden': 'true',
    html: '<svg viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="none" '
        + 'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
        + 'stroke-linejoin="round">' + GLYPHS[name] + '</svg>' });
}
// The fallback for an unknown domain must not break the two systems every
// real domain obeys: icons are drawn glyph-adjacent marks (not emoji), and
// colours come from the theme so the tag stays legible when the night
// palette turns. '⊕' + hardcoded brown did neither.
const domainById = id => S.domains.find(d => d.id === id) || { name: id, color: 'var(--edge)', icon: '' };
// Authored domains ship their own character; the fallback has none, so it is
// drawn in the book's own hand rather than borrowed from the running text.
function domainMark(d, size) { return d.icon ? d.icon : glyph('spark', size || 15); }
function esc(s) { return (s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('show'), 2600); }

/* ---------------- speech ---------------- */
function speakText(text, onEnd) {
  try {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(String(text).slice(0, 3500));
    u.rate = S.stage <= 1 ? 0.9 : 0.98; u.pitch = 1.04;
    if (onEnd) u.onend = onEnd;
    speechSynthesis.speak(u);
  } catch (e) { if (onEnd) onEnd(); }
}
function maybeSpeak(text, maxStage = 1) { if (S.speak && S.stage <= maxStage) speakText(text); }
function stopSpeaking() { try { speechSynthesis.cancel(); } catch (e) {} }
// WCAG 1.4.2: any audio that starts automatically must be stoppable. The
// reader can silence the book entirely, and a stop button appears while it
// is speaking.
function setSpeakEnabled(on) {
  S.speak = on;
  if (!on) stopSpeaking();
  localStorage.setItem('primer-speak', on ? '1' : '0');
  api.post('/api/profile/settings', { speak: on }).catch(() => {});
  const b = $('#speak-toggle');
  if (b) {
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
    b.setAttribute('aria-label', on ? 'Voice on — turn the reading voice off' : 'Voice off — turn the reading voice on');
    b.querySelector('.tt-label').textContent = on ? 'Voice on' : 'Voice off';
    b.querySelector('.tt-icon').replaceChildren(glyph(on ? 'speak' : 'mute', 15));
  }
}
function speakToggle() {
  const b = btn({ id: 'speak-toggle', class: 'chrome-toggle', 'aria-pressed': S.speak ? 'true' : 'false',
    'aria-label': S.speak ? 'Voice on — turn the reading voice off' : 'Voice off — turn the reading voice on',
    onclick: () => setSpeakEnabled(!S.speak) },
    el('span', { class: 'tt-icon', 'aria-hidden': 'true' }, glyph(S.speak ? 'speak' : 'mute', 15)),
    el('span', { class: 'tt-label' }, S.speak ? 'Voice on' : 'Voice off'));
  return b;
}
function speakBtn(getText, label) {
  const b = btn({ class: 'speak-btn', 'aria-label': label || 'Read aloud',
    onclick: () => { const t = typeof getText === 'function' ? getText() : getText; b.classList.add('speaking'); speakText(t, () => b.classList.remove('speaking')); } }, glyph('speak', 16));
  return b;
}

/* ---------------- routing (hash-based) ---------------- */
function hashFor(view, arg) {
  if (view === 'node') return '#/node/' + encodeURIComponent(arg);
  if (view === 'reader') { const a = typeof arg === 'string' ? { title: arg } : (arg || {});
    return '#/read/' + encodeURIComponent(a.title || '') + (a.node ? '/' + encodeURIComponent(a.node) : ''); }
  return '#/' + view;
}
// 'journey' — the view's real route name, as the sidebar and routes table
// spell it. This list said 'journal' (the API endpoint's name, not the
// view's), so the Journey nav button silently "corrected" itself to Today on
// every click and the view was unreachable by any path.
const KNOWN_VIEWS = new Set(['today', 'atlas', 'review', 'library-search', 'story',
                             'journey', 'roadmap', 'library', 'node', 'read', 'reader']);
function parseHash() {
  const h = (location.hash || '#/today').replace(/^#\/?/, '');
  const parts = h.split('/').map(decodeURIComponent);
  const view = parts[0] || 'today';
  if (view === 'node') return { view, arg: parts[1] };
  if (view === 'read') return { view: 'reader', arg: { title: parts[1], node: parts[2] || null } };
  // `reader` is the internal name for the article view and needs a title. Typed
  // on its own it rendered a blank page with no message and focus on an empty
  // <main> — a dead end with nothing to act on.
  if (view === 'reader' && !parts[1]) return { view: 'library-search', arg: null };
  if (!KNOWN_VIEWS.has(view)) return { view: 'today', arg: null, corrected: true };
  return { view, arg: null };
}
function go(view, arg) { location.hash = hashFor(view, arg); } // triggers hashchange → render
function renderRoute() {
  if (!S.state || !S.state.onboarded) return;
  // Any navigation unmounts whatever view was up — drop the review deck's
  // document listener now rather than lazily on the next keypress.
  if (_reviewKeyHandler) { document.removeEventListener('keydown', _reviewKeyHandler); _reviewKeyHandler = null; }
  const { view, arg, corrected } = parseHash();
  // Falling back to Today while leaving the address bar on a bogus route left
  // no nav item marked current, and a reload landed nowhere.
  if (corrected) { location.replace('#/' + view); return; }
  S.view = view;
  document.querySelectorAll('.navbtn').forEach(b => {
    const active = b.dataset.nav === view;
    b.classList.toggle('active', active);
    if (active) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
  });
  const routes = { today: renderToday, atlas: renderAtlas, review: renderReview, 'library-search': renderSearch, roadmap: renderRoadmap, library: renderLibrary, journey: renderJourney, story: renderStory, node: renderNode, reader: renderReader };
  const page = $('#page'); if (!page) return;
  page.innerHTML = ''; page.scrollTop = 0;
  // Keyboard users must land on the new view, not back at the document top.
  page.setAttribute('tabindex', '-1');
  const rendered = (routes[view] || renderToday)(page, arg);
  // Focus after the view exists so screen readers announce the new page, not an
  // empty container.
  Promise.resolve(rendered).finally(() => {
    const h1 = page.querySelector('#article h1');
    const h = h1 || page.querySelector('.pagehead h2');
    page.setAttribute('aria-label', h ? h.textContent : view);
    // A control that caused this rebuild (the theme toggle) keeps focus, so the
    // reader is not thrown back to the top of the page for changing a setting.
    const restore = S.restoreFocus && $('#' + S.restoreFocus);
    S.restoreFocus = null;
    if (restore) { restore.focus(); restore.scrollIntoView({ block: 'nearest' }); }
    // Never pull focus out of an open dialog: a background repaint must not
    // break out of something that claims aria-modal.
    else if (!_modalStack.length) page.focus({ preventScroll: true });
  });
}
window.addEventListener('hashchange', renderRoute);

/* ---------------- bootstrap ---------------- */
async function boot() {
  S.state = await api.get('/api/state');
  S.domains = S.state.domains;
  applyTheme(localStorage.getItem('primer-theme'));
  if (!S.state.onboarded) return renderOnboarding();
  // stage 0 is falsy — `||` would silently promote a preschooler to stage 2
  S.stage = Number.isFinite(S.state.profile.stage) ? S.state.profile.stage : 2;
  const localSpeak = localStorage.getItem('primer-speak');
  S.speak = localSpeak !== null ? localSpeak === '1' : (S.state.profile.settings?.speak !== false);
  renderShell();
  if (!location.hash || location.hash === '#') location.hash = '#/today';
  else renderRoute();
  // Ask once, after the book is on screen, if we do not actually know.
  setTimeout(askPronounsIfUnknown, 600);
}
function applyTheme(theme) {
  if (theme === 'dark' || theme === 'light') document.documentElement.setAttribute('data-theme', theme);
  else document.documentElement.removeAttribute('data-theme');
}

/* ---------------- onboarding ---------------- */
function renderOnboarding() {
  const root = $('#root');
  const sel = new Set(['math', 'language', 'biology', 'physics', 'history']);
  let step = 0;
  // pronouns: the frame story speaks about the reader, so it has to know how.
  // Two sets are offered and one has to be pre-selected for the radiogroup to
  // have a starting point; the reader changes it here, or later from Today.
  const data = { name: '', age: 8, hours_per_week: 6, breadth: 'balanced', pronouns: 'she', domains: [...sel] };

  function draw() {
    root.innerHTML = '';
    const wrap = el('div', { class: 'onboard', role: 'main', style: 'max-width:640px;margin:0 auto;min-height:100vh;display:flex;flex-direction:column;justify-content:center;padding:40px 24px' });
    const card = el('div', { class: 'card', role: 'group', 'aria-label': 'Set up your book', style: 'background:var(--paper);color:var(--ink);padding:34px' });
    // Each step replaces the whole screen. Without this, focus fell to <body>
    // on every Next and every Back.
    if (step > 0) setTimeout(() => {
      const h = card.querySelector('h1, h2');
      if (h) { h.setAttribute('tabindex', '-1'); h.focus(); }
    }, 20);
    // A four-step form with no sense of length reads as indefinite — a
    // reader can't tell "almost done" from "just started." Numbered like
    // chapters, in keeping with the book's own idiom, not a progress bar.
    const ROMAN = ['I', 'II', 'III', 'IV'];
    card.append(el('div', { class: 'onboard-steps', 'aria-hidden': 'true' },
      ...ROMAN.map((r, i) => el('span', { class: 'onboard-step' + (i === step ? ' on' : i < step ? ' done' : '') }, r))));

    if (step === 0) {
      const nameInput = el('input', { type: 'text', id: 'ob-name', placeholder: 'What shall the book call you?', value: data.name, oninput: e => data.name = e.target.value });
      card.append(
        el('div', { class: 'onboard-mark', 'aria-hidden': 'true' }, glyph('story', 56)),
        el('h1', { style: 'text-align:center;font-size:32px;margin:6px 0 2px' }, 'The Primer'),
        el('p', { style: 'text-align:center;color:var(--ink-soft);margin-top:0' }, 'A living book that teaches you everything — from your first letters to the frontier of what humankind knows.'),
        el('p', { class: 'dropcap', style: 'margin-top:18px;line-height:1.7' }, 'Welcome, reader. This book will grow with you over the next five to ten years, carrying you from preschool wonder to graduate-level mastery in whichever fields you choose. First, the book would like to know you.'),
        field('Your name', nameInput, 'ob-name'),
        el('div', { style: 'display:flex;gap:10px;align-items:center' },
          speakBtnAlways(() => 'Welcome, reader. This book will teach you everything. First, what is your name?'),
          btn({ class: 'btn gold', style: 'flex:1', onclick: () => { if (!data.name.trim()) data.name = 'Reader'; step = 1; draw(); } }, 'Begin →')),
      );
      setTimeout(() => nameInput.focus(), 30);
    } else if (step === 1) {
      const ageOut = el('b', { id: 'ageout' }, data.age + ' years');
      const hrsOut = el('b', { id: 'hrsout' }, data.hours_per_week + ' hrs / week');
      card.append(
        el('h2', { style: 'margin-top:0' }, 'Where are you starting?'),
        el('p', { class: 'muted' }, 'The book meets you exactly where you are — there is no wrong answer.'),
        // 3–120: the book is for anyone, and a grandparent reading it beside a
        // grandchild should not find themselves off the end of the scale. The
        // fill helper is proportional, so the wider span needs nothing else.
        field2('Age', ageOut, el('input', { type: 'range', min: 3, max: 120, value: data.age, 'aria-label': 'Age',
          'aria-valuetext': data.age + ' years',
          oninput: e => { syncRangeFill(e.target); data.age = +e.target.value; ageOut.textContent = data.age + ' years'; e.target.setAttribute('aria-valuetext', data.age + ' years'); } })),
        field2('Time to read & learn each week', hrsOut, el('input', { type: 'range', min: 2, max: 30, value: data.hours_per_week, 'aria-label': 'Hours per week',
          'aria-valuetext': data.hours_per_week + ' hours per week',
          oninput: e => { syncRangeFill(e.target); data.hours_per_week = +e.target.value; hrsOut.textContent = data.hours_per_week + ' hrs / week'; e.target.setAttribute('aria-valuetext', data.hours_per_week + ' hours per week'); } })),
        pronounChoice(),
        navRow(() => { step = 0; draw(); }, () => { step = 2; draw(); }),
      );
    } else if (step === 2) {
      card.append(
        el('h2', { style: 'margin-top:0' }, 'How wide is your ambition?'),
        el('p', { class: 'muted' }, 'How much of human knowledge do you want to master? This sets the length of your journey.'),
        breadthChoice(),
        navRow(() => { step = 1; draw(); }, () => { step = 3; draw(); }),
      );
    } else if (step === 3) {
      card.append(
        el('h2', { style: 'margin-top:0' }, 'Where shall we go deepest?'),
        el('p', { class: 'muted' }, 'Choose the fields you most want to carry all the way to the frontier. You can still explore everything — these just get priority.'),
        domainPicker(),
        // The typographic '✦' is a character from the running text standing in
        // among drawn marks; the spark glyph is the same idea in the icon
        // system's own hand and one stroke weight. (Same swap below on every
        // other button that carried it.)
        navRow(() => { step = 2; draw(); }, finish, ['Open the book ', glyph('spark', 15)]),
      );
    }
    wrap.append(card); root.append(wrap);
    // Paint each slider's filled portion once it is in the document.
    card.querySelectorAll('input[type=range]').forEach(syncRangeFill);
  }
  function field(label, input, id) { const l = el('label', { class: 'field', for: id }); l.append(el('span', {}, label), input); return l; }
  // Webkit will not expose a filled-track pseudo, so the fill is painted by a
// CSS variable the input keeps in sync with its own value.
function syncRangeFill(input) {
  const min = +input.min || 0, max = +input.max || 100, v = +input.value;
  input.style.setProperty('--range-fill', (100 * (v - min) / (max - min)) + '%');
}
function field2(label, out, input) { const l = el('label', { class: 'field' }); const head = el('span', { style: 'display:flex;justify-content:space-between' }, el('span', {}, label), out); l.append(head, input); return l; }
  function navRow(back, next, nextLabel = 'Continue →') {
    return el('div', { style: 'display:flex;gap:10px;margin-top:20px' },
      btn({ class: 'btn ghost', onclick: back }, '← Back'),
      btn({ class: 'btn gold', style: 'flex:1', onclick: next }, ...[].concat(nextLabel)));
  }
  // The frame story is written *about* the reader, so it needs a pronoun for
  // them. Asked plainly, beside age, in the same radiogroup idiom as the
  // breadth chooser — roving tabindex, arrows and Home/End, aria-checked, and
  // a written ✓ mark so the choice reads without relying on the border colour.
  function pronounChoice() {
    const opts = [['she', 'she / her'], ['he', 'he / him']];
    const wrap = el('div', { style: 'display:block;margin-bottom:16px;font-family:var(--sans);font-size:13px;color:var(--ink-soft)' },
      el('span', { style: 'display:block;margin-bottom:5px;font-weight:600;letter-spacing:0.3px' }, 'The book will call you'));
    const box = el('div', { class: 'pronoun-row', role: 'radiogroup', 'aria-label': 'The book will call you' });
    opts.forEach(([id, label]) => {
      box.append(btn({ class: 'card pick' + (data.pronouns === id ? ' picked' : ''), role: 'radio',
        tabindex: data.pronouns === id ? '0' : '-1',
        'aria-checked': data.pronouns === id ? 'true' : 'false',
        onkeydown: e => {
          if (!['ArrowDown', 'ArrowRight', 'ArrowUp', 'ArrowLeft', 'Home', 'End'].includes(e.key)) return;
          e.preventDefault();
          const all = [...box.querySelectorAll('[role=radio]')];
          const cur = all.indexOf(e.currentTarget);
          const dir = (e.key === 'ArrowDown' || e.key === 'ArrowRight') ? 1 : -1;
          const nxt = e.key === 'Home' ? all[0]
                    : e.key === 'End' ? all[all.length - 1]
                    : all[(cur + dir + all.length) % all.length];
          nxt.focus(); nxt.click();
        },
        onclick: () => { data.pronouns = id; box.querySelectorAll('[role=radio]').forEach((n, i) => {
          const on = opts[i][0] === id;
          n.setAttribute('aria-checked', on ? 'true' : 'false');
          n.setAttribute('tabindex', on ? '0' : '-1');
          n.classList.toggle('picked', on);
        }); } },
        el('b', {}, label),
        el('span', { class: 'pick-mark', 'aria-hidden': 'true' }, '✓ Chosen')));
    });
    wrap.append(box);
    return wrap;
  }
  function breadthChoice() {
    const opts = [['focused', 'Focused', 'A few fields, mastered completely. The shortest path to expertise.'],
      ['balanced', 'Balanced', 'A deep spine of chosen fields, with broad literacy across the rest.'],
      ['polymath', 'Polymath', 'Everything, everywhere, to the highest level. The longest, richest road.']];
    const box = el('div', { class: 'grid', role: 'radiogroup', 'aria-label': 'Breadth', style: 'gap:10px;margin-top:10px' });
    opts.forEach(([id, name, desc]) => {
      // Checked state is carried by a class plus a written "✓ Chosen" mark,
      // not inline colour mutation alone: a 1.5px border shift is the kind of
      // colour-only cue SC 1.4.1 exists for, and the mark reads in any palette.
      const c = btn({ class: 'card pick' + (data.breadth === id ? ' picked' : ''), role: 'radio', tabindex: data.breadth === id ? '0' : '-1',
        // Home/End are part of the ARIA radiogroup pattern, not extras: a
        // keyboard reader expects the ends of the group to be one key away.
        onkeydown: e => {
          if (!['ArrowDown', 'ArrowRight', 'ArrowUp', 'ArrowLeft', 'Home', 'End'].includes(e.key)) return;
          e.preventDefault();
          const all = [...box.querySelectorAll('[role=radio]')];
          const cur = all.indexOf(e.currentTarget);
          const dir = (e.key === 'ArrowDown' || e.key === 'ArrowRight') ? 1 : -1;
          const nxt = e.key === 'Home' ? all[0]
                    : e.key === 'End' ? all[all.length - 1]
                    : all[(cur + dir + all.length) % all.length];
          nxt.focus(); nxt.click();
        },
        'aria-checked': data.breadth === id ? 'true' : 'false',
        onclick: () => { data.breadth = id; box.querySelectorAll('[role=radio]').forEach((n, i) => { const on = opts[i][0] === id; n.setAttribute('aria-checked', on ? 'true' : 'false'); n.setAttribute('tabindex', on ? '0' : '-1'); n.classList.toggle('picked', on); }); } },
        el('b', { style: 'font-size:17px' }, name), el('p', { class: 'muted', style: 'margin:5px 0 0' }, desc),
        // aria-hidden: aria-checked already tells assistive tech; the written
        // mark is for eyes that would otherwise be squinting at border weight.
        el('span', { class: 'pick-mark', 'aria-hidden': 'true' }, '✓ Chosen'));
      box.append(c);
    });
    return box;
  }
  function domainPicker() {
    const box = el('div', { class: 'chip-row', role: 'group', 'aria-label': 'Deep domains', style: 'margin-top:12px' });
    S.domains.forEach(d => {
      const chip = btn({ class: 'chip' + (sel.has(d.id) ? ' on' : ''), 'aria-pressed': sel.has(d.id) ? 'true' : 'false',
        onclick: () => { if (sel.has(d.id)) sel.delete(d.id); else sel.add(d.id); chip.classList.toggle('on'); chip.setAttribute('aria-pressed', sel.has(d.id) ? 'true' : 'false'); data.domains = [...sel]; } }, domainMark(d, 15), ' ' + d.name);
      box.append(chip);
    });
    return box;
  }
  async function finish() {
    data.domains = [...sel];
    try {
      await api.post('/api/profile', data);
      S.state = await api.get('/api/state');
      S.stage = Number.isFinite(S.state.profile.stage) ? S.state.profile.stage : 2;
      renderShell();
      location.hash = '#/today'; renderRoute();
      toast('Welcome, ' + data.name + '. Your book is open.');
      // The book now starts everyone at the beginning, so this offer is the
      // only route to a level that fits — gating it on S.stage would mean it
      // never appeared at all. Age decides whether to *ask*, never where to
      // start: someone past the first stages is invited to be measured.
      if (data.age >= 6) setTimeout(() => offerPlacement(data.domains), 700);
    } catch (e) { toast('The book could not save that just now — try once more.'); }
  }
  draw();
}
function speakBtnAlways(getText) { const b = btn({ class: 'speak-btn', 'aria-label': 'Read aloud', onclick: () => { b.classList.add('speaking'); speakText(typeof getText === 'function' ? getText() : getText, () => b.classList.remove('speaking')); } }, glyph('speak', 16)); return b; }

/* ---------------- placement check ---------------- */
function offerPlacement(domains) {
  const domain = (domains && domains[0]) || 'math';
  const d = domainById(domain);
  openModal({
    label: 'Check your level', dismissable: true,
    build: (modal, close) => {
      modal.append(
        el('div', { class: 'kicker' }, 'Optional'),
        el('h2', { style: 'margin-top:4px' }, 'Shall the book check your level?'),
        el('p', { class: 'muted' }, 'The book starts at the beginning and assumes nothing. A few questions in ' + d.name +
          ' can place you by what you actually know — you can skip this and do it any time.'),
        el('div', { style: 'display:flex;gap:10px;margin-top:16px' },
          btn({ class: 'btn ghost', style: 'flex:1', onclick: close }, 'Skip for now'),
          btn({ class: 'btn gold', style: 'flex:1', onclick: () => { close(); runPlacement(domain, S.stage); } }, 'Check my level →')));
    }
  });
}

async function runPlacement(domain, stage) {
  // Placement had neither of the fixes the quiz path got: no heading to move
  // focus to, no live region, and `modal.innerHTML = ''` on every question —
  // so focus fell to <body> from the second question onward.
  const ov = spinnerOverlay('Preparing a few questions…');
  let data;
  try { data = await api.get('/api/placement/next?domain=' + encodeURIComponent(domain) + '&stage=' + stage + '&n=5'); }
  catch (e) { ov.remove(); toast('The book cannot reach its questions just now — try again in a moment. Nothing is lost.'); return; }
  ov.remove();
  if (!data.questions.length) { toast('The book has no questions at that level yet — nothing to prove today, nothing lost.'); return; }
  const answers = [];
  let i = 0;
  openModal({
    label: 'Placement check', dismissable: true, dismissLabel: 'Stop',
    build: (modal, close) => draw(modal, close)
  });
  function draw(modal, close) {
    const q = data.questions[i];
    modal.innerHTML = ''; modal.append(closeBtn(close));
    const progress = el('div', { class: 'q-progress', tabindex: '-1',
      role: 'heading', 'aria-level': '2' },
      'PLACEMENT · ' + domainById(domain).name + ' · ' + STAGE_NAMES[stage] +
      ' — ' + (i + 1) + ' of ' + data.questions.length);
    modal.append(progress);
    if (i > 0 && q.kind === 'choice') setTimeout(() => progress.focus(), 20);
    const card = el('div', { class: 'q-card' });
    if (S.stage <= 2 || q.say) card.append(el('div', { class: 'speak-row' }, speakBtn(() => q.say || q.prompt, 'Read aloud')));
    card.append(el('div', { class: 'q-prompt' }, q.prompt));
    if (q.kind === 'choice') {
      const box = el('div', { class: 'q-choices' });
      q.choices.forEach(ch => box.append(btn({ class: 'choice', onclick: () => next(ch, modal, close) }, ch)));
      card.append(box);
    } else {
      const inp = el('input', { type: 'text', 'aria-label': 'Your answer', placeholder: 'Your answer',
        style: 'padding:12px;font-size:20px;text-align:center;width:60%',
        onkeydown: e => { if (e.key === 'Enter') next(inp.value, modal, close); } });
      card.append(el('div', { class: 'q-numeric' }, inp, btn({ class: 'btn gold', onclick: () => next(inp.value, modal, close) }, 'Check')));
      setTimeout(() => inp.focus(), 40);
    }
    card.append(btn({ class: 'btn ghost small', style: 'margin-top:14px', onclick: () => next('', modal, close) }, "I don't know yet"));
    modal.append(card);
    if (S.stage <= 1) maybeSpeak(q.say || q.prompt);
  }
  async function next(ans, modal, close) {
    answers.push(String(ans));
    i++;
    if (i < data.questions.length) return draw(modal, close);
    // A bare unlabelled spinner here used to wipe the focused control from the
    // still-open, aria-modal dialog — focus fell to <body>, the Tab trap could
    // no longer match it, and nothing announced that the check was being
    // scored. The same failure mode was already fixed for per-question
    // grading via holdFocus(); mirrored here for the final submit.
    modal.innerHTML = '';
    const status = el('div', { class: 'spinner', role: 'status', 'aria-label': 'Scoring your answers…', tabindex: '-1' });
    modal.append(status);
    status.focus();
    let r;
    try { r = await api.post('/api/placement/submit', { domain, stage, answers, token: data.token || '' }); }
    catch (e) { close(); toast('The book could not mark this one — likely the network, never you. Your answers are safe; try again in a moment.'); return; }
    modal.innerHTML = ''; modal.append(closeBtn(close));
    const head = el('h2', { tabindex: '-1', class: 'result-heading' }, 'What the book learned about you');
    modal.append(head);
    setTimeout(() => head.focus(), 30);
    const splash = el('div', { class: 'result-splash' });
    splash.append(el('div', { class: 'stars', style: 'color:var(--gold)' }, r.passed ? '★★★' : '★☆☆'),
      el('p', {}, r.passed
        ? 'Comfortable at ' + STAGE_NAMES[stage] + ' level in ' + domainById(domain).name + '.'
        : 'This level is still ahead of you — the book will start you lower and build up.'));
    if (r.suggest_stage != null && !r.settled) {
      splash.append(el('p', { class: 'muted' }, r.passed ? 'Let\'s try one level higher.' : 'Let\'s try one level down.'),
        btn({ class: 'btn gold', onclick: () => { close(); runPlacement(domain, r.suggest_stage); } }, 'Continue →'));
    } else {
      splash.append(el('p', { class: 'result-msg' }, 'The book has placed you. You can re-check any time.'),
        btn({ class: 'btn gold', onclick: async () => { close(); S.state = await api.get('/api/state'); S.stage = Number.isFinite(S.state.profile.stage) ? S.state.profile.stage : 2; document.body.dataset.stage = S.stage; renderShell(); renderRoute(); } }, 'Open my book ', glyph('spark', 15)));
    }
    modal.append(splash);
  }
}

/* ---------------- shell ---------------- */
function renderShell() {
  const p = S.state.profile;
  document.body.dataset.stage = p.stage;
  $('#root').innerHTML = '';
  const book = el('div', { id: 'book' });
  // Icons are deliberately distinct — four near-identical book glyphs are no
  // help to a child who cannot read the labels.
  const nav = [['today', 'today', 'Today'], ['atlas', 'atlas', 'The Atlas'], ['review', 'review', 'Review'],
    ['library-search', 'lookup', 'Look Up'], ['story', 'story', 'Your Story'], ['journey', 'journey', 'Journey'],
    ['roadmap', 'path', 'Your Path'], ['library', 'shelf', 'The Shelf']];
  const sidebar = el('nav', { id: 'sidebar', 'aria-label': 'Main' },
    el('div', { class: 'brand' }, el('div', { class: 'mark', 'aria-hidden': 'true' }, glyph('story', 34)), el('h1', {}, 'The Primer'),
      el('div', { class: 'sub' }, p.title || p.stage_name)));
  // The nav and the stats each get a container. Without them every button,
  // the brand and every stat chip were bare siblings of one flex parent, so
  // the narrow-screen rule (`flex-wrap: wrap`) had nothing to wrap *as* — it
  // shuffled all fourteen into a ragged grid with "Today" beside the title.
  const navlist = el('div', { class: 'navlist' });
  nav.forEach(([id, ic, label]) => {
    const b = btn({ class: 'navbtn', dataset: { nav: id }, onclick: () => go(id) },
      el('span', { class: 'ic', 'aria-hidden': 'true' }, glyph(ic)), el('span', { class: 'label' }, label));
    // A pre-reader hears where they are going: focus or hover speaks the label.
    if (p.stage <= 1) {
      const say = () => maybeSpeak(label);
      b.addEventListener('focus', say);
      b.addEventListener('mouseenter', say);
    }
    navlist.append(b);
  });
  // Keep the trailing fade honest: drop it once the strip is scrolled out.
  const syncNavFade = () => {
    const atEnd = navlist.scrollLeft + navlist.clientWidth >= navlist.scrollWidth - 2;
    navlist.classList.toggle('at-end', atEnd);
  };
  navlist.addEventListener('scroll', syncNavFade, { passive: true });
  if (window._navFadeResize) window.removeEventListener('resize', window._navFadeResize);
  window._navFadeResize = syncNavFade;
  window.addEventListener('resize', syncNavFade);
  setTimeout(syncNavFade, 0);
  sidebar.append(navlist);
  sidebar.append(el('div', { class: 'spacer' }));
  // The foot of the spine holds two different kinds of thing: the record (who
  // you are, what you have earned) and the chrome (voice, light). They were
  // one undifferentiated stack, so the toggles read as two more stats and sat
  // hard against the bottom edge. Separated into their own row, ruled off, and
  // set side by side — settings look like settings, not like a score.
  sidebar.append(el('div', { class: 'statrow' },
    el('div', { class: 'stat' }, el('span', {}, 'Reader'), el('b', {}, p.name)),
    el('div', { class: 'stat' }, el('span', {}, 'Mastered'), el('b', { id: 'stat-mastered' }, '—')),
    el('div', { class: 'stat' }, el('span', {}, 'XP'), el('b', { id: 'stat-xp' }, p.xp || 0)),
    el('div', { class: 'stat' }, el('span', {}, 'Streak'), el('b', { id: 'stat-streak' }, String(p.streak || 0), glyph('flame', 13))),
  ));
  sidebar.append(el('div', { class: 'chrome-row', role: 'group', 'aria-label': 'Reading settings' },
    speakToggle(),
    themeToggle(),
  ));
  book.append(sidebar, el('main', { id: 'page' }));
  const skip = btn({ class: 'skip-link', onclick: () => { const m = $('#page'); if (m) { m.setAttribute('tabindex', '-1'); m.focus(); } } }, 'Skip to content');
  $('#root').append(skip, book);
  refreshStats();
}
function effectiveTheme() {
  const set = document.documentElement.getAttribute('data-theme');
  if (set) return set;
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
function themeToggle() {
  const b = btn({ id: 'theme-toggle', class: 'chrome-toggle', 'aria-label': 'Switch between day and night reading', onclick: () => {
    // Toggle relative to what the reader actually sees, so the first press
    // always visibly changes the page (even when following the OS setting).
    const next = effectiveTheme() === 'dark' ? 'light' : 'dark';
    applyTheme(next); localStorage.setItem('primer-theme', next);
    // Some engines don't fully invalidate custom properties on an attribute
    // change, so elements can keep the old theme's colours. Rebuilding the view
    // guarantees every node resolves the new tokens.
    if (S.state && S.state.onboarded) {
      S.restoreFocus = 'theme-toggle';   // honoured once the view has rebuilt
      renderShell(); renderRoute();
    } else paint();
  } }, el('span', { class: 'tt-icon', 'aria-hidden': 'true' }, '☾'), el('span', { class: 'tt-label' }, ''));
  function paint() {
    const now = effectiveTheme();
    b.querySelector('.tt-label').textContent = now === 'dark' ? 'Night' : 'Day';
    b.querySelector('.tt-icon').textContent = now === 'dark' ? '☾' : '☀';
  }
  paint();
  return b;
}
async function refreshStats() {
  try {
    const t = await api.get('/api/today');
    if ($('#stat-mastered')) $('#stat-mastered').textContent = t.mastered;
    if ($('#stat-xp')) $('#stat-xp').textContent = t.profile.xp;
    if ($('#stat-streak')) $('#stat-streak').replaceChildren(String(t.profile.streak || 0), glyph('flame', 13));
  } catch (e) { }
}
// A spinner says "wait"; ruled lines filling in say "the page is being
// written." It also holds roughly the shape of what arrives, so the layout
// does not jump when it does. Announcement is unchanged: one status node.
function skeleton(lines) {
  const box = el('div', { class: 'book-skeleton', role: 'status', 'aria-label': 'Loading' });
  const widths = ['62%', '96%', '88%', '94%', '71%'];
  for (let i = 0; i < (lines || 5); i++) {
    box.append(el('i', { class: i === 0 ? 'sk-head' : '', style: 'width:' + widths[i % widths.length] }));
  }
  return box;
}
function loading(page) { page.append(skeleton(5)); }
// An empty state is an unwritten leaf, not a missing feature: the page that
// is waiting for the reader gets the same care as the page that has arrived.
function emptyLeaf(glyphName, title, body) {
  return el('div', { class: 'empty-leaf' },
    el('div', { class: 'el-mark', 'aria-hidden': 'true' }, glyph(glyphName, 34)),
    el('h3', {}, title),
    el('p', { class: 'muted' }, body));
}
// "no profile" is not a failure — it is the book's honest answer when there is
// nobody in it yet. The demo runs on ephemeral storage, so a reader mid-session
// can find the record gone; every data endpoint then answers 400 {"no profile"}
// and the whole app used to meet them with DON'T PANIC. A missing reader is an
// unwritten first page: go and write it. Genuine network/server trouble is a
// different animal and keeps the Guide's error card.
function isNoProfile(e) { return !!e && typeof e.error === 'string' && /no profile/i.test(e.error); }
function toOnboarding() {
  if (S.state) S.state.onboarded = false;   // stops renderRoute from repainting behind us
  renderOnboarding();
}
async function guard(page, fn) {
  loading(page);
  try { const v = await fn(); page.innerHTML = ''; return v; }
  catch (e) {
    page.innerHTML = '';
    if (isNoProfile(e)) { toOnboarding(); return null; }
    page.append(errCard(e, () => renderRoute()));
    return null;
  }
}
// The Guide's first and best advice, in large friendly letters. An error in a
// book for children should reassure before it explains: nothing the reader
// did, nothing lost, and a clear way onward.
function errCard(e, retry) {
  // The reassuring lede always leads; the backend's terse string ("no such
  // node", a bare statusText) is demoted to fine print — a raw server error
  // as the headline undid the whole DON'T PANIC register.
  const c = el('div', { class: 'card err-card', role: 'alert' },
    el('div', { class: 'dont-panic', 'aria-hidden': 'true' }, 'DON’T PANIC'),
    el('p', { class: 'err-lede' }, 'The Book has briefly lost its train of thought — likely the network, never you.'),
    el('p', { class: 'muted err-note' }, 'Everything you have learned is safely written down.' + (e && e.error ? ' (' + e.error + ')' : '')));
  if (retry) c.append(btn({ class: 'btn ghost small', onclick: retry }, 'Try again'));
  return c;
}
function pagehead(kicker, title, sub) {
  // Deliberately no colour parameter: passing a domain colour here produced
  // unthemed text that failed contrast in 7 of 10 domains.
  const head = el('div', { class: 'pagehead' },
    el('div', { class: 'kicker' }, kicker),
    el('h2', {}, title), sub ? el('p', {}, sub) : null);
  if (S.stage <= 1) {
    // A pre-reader must be able to hear every page, not just articles.
    const row = el('div', { style: 'display:flex;align-items:center;gap:8px;margin-top:8px' },
      speakBtn(() => [kicker, title, sub].filter(Boolean).join('. '), 'Read this page aloud'),
      el('span', { class: 'muted' }, 'Read this page to me'));
    head.append(row);
  }
  return head;
}
// A running head, not a bare caption: the label sits on a hairline that runs
// out to the margin, which is how a book divides a page and how an atlas
// divides a plate. Cheap to draw, and it gives the long scrolling views an
// architecture they did not have.
function sectionLabel(text) { return el('h3', { class: 'section-label' }, el('span', {}, text)); }

/* ---------------- Today ---------------- */

// The book speaks about the reader by name and pronoun all through the frame
// story, so getting this wrong is not cosmetic — it misgenders someone in
// their own book, on every page, until they can correct it. Two things follow:
// the reader is ASKED when the book does not know (a retired or missing
// value), never defaulted into one silently, and the choice is reachable
// afterwards from Today rather than being frozen at onboarding.
async function setPronouns(v) {
  await api.post('/api/profile/settings', { pronouns: v });
  S.state = await api.get('/api/state');
}
function pronounLine() {
  const cur = (S.state.profile && S.state.profile.pronouns) || 'she';
  const row = el('p', { class: 'pronoun-line' },
    el('span', {}, 'The book calls you '));
  [['she', 'she / her'], ['he', 'he / him']].forEach(([id, label]) => {
    const b = btn({ class: 'pronoun-swap' + (cur === id ? ' on' : ''),
      'aria-pressed': cur === id ? 'true' : 'false',
      onclick: async () => {
        try { await setPronouns(id); toast('The book will say ' + label + ' from here on.'); renderRoute(); }
        catch (e) { toast('Could not change that just now — nothing is lost.'); }
      } }, label);
    row.append(b);
  });
  return row;
}
function askPronounsIfUnknown() {
  if (!S.state || !S.state.profile || S.state.profile.pronouns_set) return;
  openModal({ label: 'How should the book speak about you?', build: (modal, close) => {
    modal.append(el('div', { class: 'ceremony' },
      el('div', { class: 'seal', 'aria-hidden': 'true' }, glyph('story', 40)),
      el('div', { class: 'sub' }, 'ONE SMALL THING'),
      el('h2', {}, 'How should the book speak about you?'),
      el('p', { class: 'muted' }, 'Your story is written about you by name, so the book needs to know which words to use. You can change this any time from Today.')));
    const row = el('div', { style: 'display:flex;gap:10px;justify-content:center;margin-top:6px' });
    [['she', 'she / her'], ['he', 'he / him']].forEach(([id, label]) => {
      row.append(btn({ class: 'btn gold', onclick: async () => {
        try { await setPronouns(id); close(); toast('Thank you — the book will say ' + label + '.'); renderRoute(); }
        catch (e) { toast('Could not save that just now — try once more.'); }
      } }, label));
    });
    modal.append(row);
  } });
}

async function renderToday(page) {
  const t = await guard(page, () => api.get('/api/today'));
  if (!t) return;
  const p = t.profile;
  const hour = new Date().getHours();
  const greet = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  page.append(pagehead(greet + ', ' + p.name, "Today's Reading",
    p.stage_name + ' — ' + p.stage_span + '. ' + (t.mastered ? t.mastered + ' topics mastered so far.' : 'Your journey begins now.')));
  page.append(pronounLine());

  // Daily quest checklist
  const quest = el('div', { class: 'quest', role: 'group', 'aria-label': "Today's quest" });
  Object.values(t.quest).forEach(q => {
    // The book already explains an empty deck ("Deck is clear — nothing due",
    // or how to start one). Nothing read that hint, so the step rendered as
    // "0 waiting" — which reads like a broken counter rather than the good
    // news it is, on exactly the days a new reader most needs encouraging.
    const status = q.done ? 'done'
      : q.hint ? q.hint
      : q.count != null ? q.count + ' waiting'
      : 'today';
    quest.append(el('div', { class: 'quest-item' + (q.done ? ' done' : q.excused ? ' excused' : '') },
      el('span', { class: 'tick', 'aria-hidden': 'true' }, q.done ? '✓' : q.excused ? '—' : '✓'),
      el('span', { class: 'qt' }, el('b', {}, q.label), status)));
  });
  page.append(quest);
  if (t.quest_done === t.quest_total) page.append(el('div', { class: 'quest-crown' }, glyph('crown', 17), ' Today\'s quest complete — ' + t.xp_today + ' XP earned today. Beautifully done.'));
  if (t.streak_milestone && !sessionStorage.getItem('milestone-' + t.streak_milestone)) {
    sessionStorage.setItem('milestone-' + t.streak_milestone, '1');
    setTimeout(() => streakCeremony(t.streak_milestone), 500);
  } else if (t.streak >= 2) {
    // The streak is the one number a reader checks daily and feels something
    // about. As a grey line of muted text it read like a footnote to the
    // quest tiles above it; as a struck badge it reads like something held.
    const rests = t.freezes_left < 2
      ? ' · ' + t.freezes_left + ' rest day' + (t.freezes_left === 1 ? '' : 's') + ' left' : '';
    page.append(el('div', { class: 'streak-badge' },
      glyph('flame', 16),
      el('b', {}, t.streak + '-day streak'),
      rests ? el('span', { class: 'rests' }, rests) : null));
  }

  // Story chapter — served at every stage, gated by proven mastery.
  if (t.story) {
    const s = t.story;
    const sc = el('div', { class: 'card chapter-card' });
    sc.append(
      el('div', { class: 'kicker', style: 'color:var(--gold-bright)' }, t.story_title + ' · Chapter ' + (t.story_progress + 1)),
      el('h3', { class: 'chapter-title' }, s.title),
      el('p', { class: 'chapter-lede' }, s.text[0]),
      btn({ class: 'btn gold', style: 'margin-top:8px', onclick: () => openStory(s, t.story_can_advance, t.story_needs) }, glyph('story', 18), ' Read the chapter'));
    if (t.story_can_advance) sc.append(el('p', { style: 'color:var(--gold-bright);font-family:var(--sans);font-size:13px;margin:10px 0 0' }, '✦ You have earned the next chapter.'));
    else if (t.story_needs) {
      const n = t.story_needs;
      let waiting = n.faded ? storyWaitingText(n) : 'The next chapter opens when you prove ' + storyWaitingText(n) + '.';
      if (n.ready_at) waiting += ' · ready ' + new Date(n.ready_at * 1000).toLocaleDateString(undefined, { weekday: 'long' });
      sc.append(el('p', { class: 'chapter-waiting' }, waiting));
    }
    page.append(sc);
  }

  page.append(sectionLabel('Your lessons for today'));
  const grid = el('div', { class: 'grid auto' });
  if (!t.lessons.length) grid.append(el('p', { class: 'muted' }, 'You have mastered every unlocked lesson — open the Atlas to go deeper, or Look Up anything you are curious about.'));
  t.lessons.forEach(n => grid.append(lessonCard(n)));
  page.append(grid);

  // Refresh chips (deck-driven mastery decay)
  if (t.refresh && t.refresh.length) {
    page.append(sectionLabel('Worth refreshing'));
    const rr = el('div', { class: 'refresh-row' });
    t.refresh.forEach(r => rr.append(btn({ class: 'req-chip', onclick: () => go('node', r.id) }, '↻ ' + r.title)));
    page.append(rr);
  }

  const row = el('div', { class: 'grid two', style: 'margin-top:20px' });
  row.append(
    actionCard([glyph('review', 17), ' Review'], t.deck.due ? t.deck.due + ' cards ready to strengthen your memory.' : 'No cards due. Master lessons to build your deck.', () => go('review'),
      (() => {
        const done = t.deck.total ? Math.round(100 * (t.deck.total - t.deck.due) / t.deck.total) : 0;
        return el('div', { class: 'bar', role: 'img',
          'aria-label': done + '% of today\'s deck reviewed' },
          el('span', { style: `width:${Math.min(100, done)}%` }));
      })()),
    actionCard([glyph('lookup', 17), ' Follow your curiosity'], 'The whole encyclopedia is inside this book. Look up anything at all.', () => go('library-search'),
      btn({ class: 'btn ghost small', style: 'margin-top:6px', onclick: surprise }, glyph('dice', 16), ' Surprise me')));
  page.append(row);
}
function actionCard(title, body, onclick, extra) {
  const c = el('div', { class: 'card lesson-card' });
  // `title` may be a string or a list of nodes (a drawn glyph plus its label),
  // so spread it rather than handing an array to a text node.
  const parts = Array.isArray(title) ? title : [title];
  c.append(el('h3', { style: 'margin:0 0 8px' }, btn({ class: 'unstyled card-open', onclick }, ...parts)),
    el('p', { class: 'muted' }, body), extra || null);
  return c;
}
function lessonCard(n) {
  const d = domainById(n.domain);
  // A card is a region with a link inside — never a <button> wrapping buttons,
  // which is invalid and produces a run-on accessible name.
  const c = el('div', { class: 'card lesson-card' });
  const open = el('h3', { style: 'font-size:18px;margin:0' },
    btn({ class: 'unstyled card-open', onclick: () => go('node', n.id) }, n.title));
  c.append(
    el('span', { class: 'stagepill' }, STAGE_NAMES[n.stage]),
    // Domain hexes are authored for daylight in the curriculum JSON. Rather
    // than re-authoring ten files per theme, --domain-lift raises the fill
    // toward white at night (0% by day) so --on-fill keeps its contrast.
    el('span', { class: 'domain-tag', style: `background:color-mix(in srgb, ${d.color}, white var(--domain-lift, 0%))` }, domainMark(d, 14), ' ' + d.name),
    open,
    el('p', { class: 'goal' }, n.goal || ''));
  if (S.stage <= 1) {
    const sp = speakBtn(() => n.title + '. ' + (n.goal || ''), 'Say ' + n.title);
    sp.style.cssText = 'position:absolute;bottom:10px;right:10px';
    c.append(sp);
  }
  if (n.mastery) {
    // The bar was aria-hidden with nothing said in its place, so "58% mastered"
    // existed only for people who could see it.
    const pct = Math.round(n.mastery * 100);
    c.append(el('div', { class: 'bar', role: 'img',
      'aria-label': pct + '% mastered' }, el('span', { style: `width:${pct}%` })));
  }
  return c;
}

/* ---------------- story overlay ---------------- */
// A faded node's lifetime pass count is stale evidence — say the true thing
// ("proved once, needs a refresh") instead of a pass count that implies the
// page is nearly open when the gate is actually shut.
// The spoken variant of a chapter. The quiz bank carries q.say for exactly
// this reason; frame.json's chapters carry nothing, so a five-year-old had a
// nine-hundred-word chapter (story.friendship among them) read at them whole.
// For the stages that are actually listening, the spoken take is the opening
// movement plus the prompt — the part a young listener has to act on — and
// the printed page is unchanged, still there to be read at leisure.
function chapterSay(s) {
  const full = (s.text || []).join(' ');
  if (S.stage > 1 || full.length <= 420) return full;
  const opening = [];
  let n = 0;
  for (const par of s.text) { opening.push(par); n += par.length; if (n >= 320) break; }
  return opening.join(' ') + (s.prompt ? ' ' + s.prompt : '');
}
function storyWaitingText(n) {
  if (n.faded) return 'You proved “' + n.title + '” once — refresh it and the page turns.';
  return '“' + n.title + '” — ' + n.passes + ' of ' + n.passes_needed + ' passes';
}

function openStory(s, canAdvance, needs) {
  openModal({
    label: s.title, dismissable: true, dark: true,
    build: (modal, close) => {
      modal.append(el('div', { class: 'kicker', style: 'color:var(--gold-bright)' }, 'A Chapter'),
        el('h2', { class: 'chapter-title', style: 'margin-top:4px' }, s.title));
      // An illuminated opening: the first letter of a chapter is set large and
      // gold, the way the Primer's own pages would ink it.
      s.text.forEach((par, i) => modal.append(
        el('p', { class: 'story-par' + (i === 0 ? ' story-first' : '') }, par)));
      modal.append(el('div', { class: 'story-fleuron', 'aria-hidden': 'true' }, '❦'));
      modal.append(el('p', { class: 'story-prompt' }, s.prompt));
      const controls = el('div', { style: 'display:flex;gap:10px;margin-top:18px;flex-wrap:wrap' },
        btn({ class: 'btn ghost small', style: 'color:var(--gold-bright);border-color:var(--gold)', onclick: () => speakText(chapterSay(s)) }, glyph('speak', 16), ' Read aloud'));
      if (canAdvance) {
        // The lesson is genuinely mastered — turning the page is earned.
        controls.append(btn({ class: 'btn gold', style: 'flex:1', onclick: async () => {
          try {
            const r = await api.post('/api/story/advance', {});
            close();
            if (r.advanced) { confetti(); if (r.xp_gained) flyXP(r.xp_gained); toast('The next chapter has opened ✦'); }
            refreshStats();
            renderRoute();
          } catch (e) { close(); toast('The page would not turn just now — nothing is lost, and the chapter is still waiting. Try again in a moment.'); }
        } }, 'Turn the page ', glyph('spark', 15)));
      } else if (s.leads_to) {
        controls.append(btn({ class: 'btn gold', style: 'flex:1', onclick: () => { close(); go('node', s.leads_to); } }, "Let's learn it →"));
        if (needs) modal.append(el('p', { style: 'color:var(--gold-bright);font-family:var(--sans);font-size:13px;margin-top:12px' },
          needs.faded ? storyWaitingText(needs) : 'This page turns when you prove ' + storyWaitingText(needs) + '.'));
      } else {
        // The epilogue: the arc is complete, so there is nothing to learn next.
        controls.append(btn({ class: 'btn gold', style: 'flex:1', onclick: close }, 'Close the book ', glyph('spark', 15)));
      }
      modal.append(controls);
      if (S.stage <= 1) maybeSpeak(chapterSay(s));
    }
  });
}

/* ---------------- Node / lesson ---------------- */
async function renderNode(page, nodeId) {
  const n = await guard(page, () => api.get('/api/curriculum/node/' + nodeId));
  if (!n) return;
  const d = domainById(n.domain);
  // pagehead's kicker is also its spoken text, so it stays a string: the
  // fallback contributes no mark here rather than a character to mispronounce.
  page.append(pagehead((d.icon ? d.icon + ' ' : '') + d.name + ' · ' + STAGE_NAMES[n.stage], n.title, n.goal || ''));

  if (n.proven) {
    page.append(el('div', { class: 'card', style: 'border-color:var(--green);background:var(--tint-green)' },
      el('b', { style: 'color:var(--green-ink)' }, '✓ You have proved this one. Revisit it any time, or push further in the Atlas.')));
  } else if (n.mastered) {
    // Placement credit — honest about the difference.
    const d = n.mastery_detail || {};
    const need = (n.opens_chapter && n.passes_needed) || d.passes_needed || 2;
    let line = 'The book assumed you already know this, so it opened the lessons beyond it.';
    line += need === 1
      ? ' Pass it once to prove it' + (d.passes ? ' — ' + Math.min(d.passes, 1) + ' of 1 so far.' : '.')
      : ' Pass it twice, a couple of days apart, to prove it' +
        (d.passes ? ' — ' + d.passes + ' of 2 passes so far.' : '.');
    page.append(el('div', { class: 'card', style: 'border-color:var(--gold)' },
      el('b', {}, '◐ Assumed, not yet proved'), el('p', { class: 'muted', style: 'margin:6px 0 0' }, line)));
  }
  else if (!n.unlocked && n.unlock_requirements && n.unlock_requirements.length) {
    const box = el('div', { class: 'card' }, el('b', {}, glyph('lock', 16), ' Not yet open'), el('p', { class: 'muted', style: 'margin:4px 0 6px' }, 'To unlock this lesson:'));
    const reqs = el('div', {}); n.unlock_requirements.forEach(r => reqs.append(el('span', { class: 'req-chip' }, r))); box.append(reqs);
    page.append(box);
  }

  // Child-voiced mini-lesson for the youngest readers.
  if (n.kid_text && S.stage <= 1) {
    const kt = el('div', { class: 'card', style: 'font-size:19px;line-height:1.7' },
      el('div', { class: 'speak-row' }, speakBtn(() => n.kid_text, 'Read the lesson aloud'), el('b', { style: 'font-family:var(--sans);font-size:13px;color:var(--gold-ink)' }, 'THE BOOK SAYS')),
      el('div', {}, n.kid_text));
    page.append(kt);
    maybeSpeak(n.kid_text);
  }

  const young = S.stage <= 1;
  page.append(sectionLabel(young ? 'Look and see' : 'Read'));
  const cards = el('div', { class: 'grid auto' });
  n.article_cards.forEach(a => {
    const c = el('div', { class: 'card lesson-card' });
    const openA = btn({ class: 'unstyled card-open', onclick: () => go('reader', { title: a.title, node: nodeId }) });
    if (a.thumb) c.append(el('img', { src: '/api/image?url=' + encodeURIComponent(a.thumb), alt: a.title,
      style: 'width:100%;height:' + (young ? '160px' : '120px') + ';object-fit:cover;border-radius:6px;margin-bottom:8px',
      loading: 'lazy', onerror: function () { this.style.display = 'none'; } }));
    c.append(el('h3', { style: 'font-size:' + (young ? '19px' : '17px') + ';margin:0 0 6px' }, openA));
    openA.append(a.title);
    // Young readers get a short, spoken invitation rather than a dense blurb.
    if (young) c.append(el('p', { class: 'muted' }, 'Tap to see the pictures and hear about it.'));
    else c.append(el('p', { class: 'muted' }, (a.summary || 'Open to read.').slice(0, 150) + '…'));
    cards.append(c);
  });
  page.append(cards);

  if (n.opens_chapter) {
    page.append(el('p', { class: 'muted', style: 'margin-top:14px;color:var(--gold-ink)' },
      glyph('story', 15), ' Proving this opens “' + n.opens_chapter.title + '” — chapter ' + n.opens_chapter.number + ' of your story.'));
  }
  const canAssess = n.unlocked || n.mastered;
  const lockedTitle = canAssess ? null : 'Unlock this lesson before taking its quiz or practice.';
  const actions = el('div', { style: 'display:flex;gap:12px;flex-wrap:wrap;margin-top:26px' },
    btn({ class: 'btn gold', disabled: canAssess ? null : '', title: lockedTitle,
      onclick: canAssess ? () => startQuiz(nodeId) : null }, glyph('quill', 16), ' Take the quiz'),
    n.practice ? btn({ class: 'btn', disabled: canAssess ? null : '', title: lockedTitle,
      onclick: canAssess ? () => startPractice(nodeId, n.practice, n.stage) : null }, glyph('target', 16), ' Practice') : null,
    n.articles && n.articles.length ? btn({ class: 'btn ghost', onclick: () => go('reader', { title: n.articles[0], node: nodeId }) }, glyph('story', 16), ' Start reading') : null);
  page.append(actions);
}

/* ---------------- Reader + tutor ---------------- */
async function renderReader(page, arg) {
  const title = typeof arg === 'string' ? arg : arg.title;
  const nodeId = typeof arg === 'object' ? arg.node : null;
  // "Check yourself" stood here for articles with no curriculum node. It was
  // machine-made cloze over raw article prose, hand-audited at 55% defective,
  // and is withdrawn: the book does not ask questions no person wrote. Read
  // aloud and the tutor already cover "check what I just read".
  const bar = el('div', { style: 'display:flex;gap:10px;align-items:center;margin-bottom:14px;flex-wrap:wrap' },
    btn({ class: 'btn ghost small', onclick: () => history.length > 1 ? history.back() : go(nodeId ? 'node' : 'today', nodeId) }, '← Back'),
    nodeId ? btn({ class: 'btn gold small', onclick: () => startQuiz(nodeId) }, glyph('quill', 14), ' Quiz me on this') : null,
    btn({ class: 'btn small', onclick: () => speakArticle() }, glyph('speak', 16), ' Read aloud'));
  page.append(bar);
  const layout = el('div', { id: 'reader-layout' });
  const art = el('article', { id: 'article', tabindex: '-1' }); art.append(skeleton(7));
  layout.append(art, buildTutor(title));
  page.append(layout);
  try {
    const a = await api.get('/api/article?title=' + encodeURIComponent(title));
    art.innerHTML = '<h1>' + esc(a.title) + '</h1>' + a.rendered;
    art.querySelectorAll('a.primer-wikilink').forEach(link => {
      const t0 = link.getAttribute('data-primer-title');
      if (t0) link.setAttribute('href', hashFor('reader', { title: t0, node: nodeId }));
      const goLink = e => { e.preventDefault(); const t = link.getAttribute('data-primer-title'); if (t) go('reader', { title: t, node: nodeId }); };
      link.addEventListener('click', goLink);
      link.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') goLink(e); });
    });
    const badge = a.source === 'zim' ? 'from your shelf' : a.source === 'cache' ? 'from your library' : 'from Wikipedia (live)';
    art.append(el('p', { class: 'muted', style: 'margin-top:30px;border-top:1px solid var(--rule);padding-top:10px' }, '✦ ' + badge + (a.simple ? ' · Simple English' : '')));
  } catch (e) { art.innerHTML = ''; art.append(errCard(e, () => renderReader(page, arg))); }
}
function speakArticle() { const t = $('#article'); if (t) speakText(t.textContent.slice(0, 3500)); }

function buildTutor(title) {
  const log = el('div', { id: 'tutor-log', 'aria-live': 'polite', 'aria-label': 'Conversation with the book' });
  const messages = [];
  let tutorFails = 0;  // consecutive-failure count drives the escalating reassurance below
  const panel = el('section', { id: 'tutor', 'aria-label': 'Ask the Book' },
    el('div', { class: 'th' }, el('span', { class: 'mark', 'aria-hidden': 'true' }, glyph('spark', 18)), el('b', {}, 'Ask the Book'),
      el('small', {}, S.state.tutor_engine === 'claude' ? 'Your patient tutor is listening' : 'Your Socratic guide'),
      // Honest about the wire: when the Claude engine answers, questions
      // leave the device. Said once, quietly, where the reader asks them.
      S.state.tutor_engine === 'claude'
        ? el('div', { class: 'tutor-disclosure' }, 'Questions travel to Claude (Anthropic) to be answered — nothing else leaves the book. ',
            btn({ class: 'unstyled tutor-optout', onclick: async function () {
              // One tap keeps every question local: flips the reader setting
              // the server honors in tutor.ask(allow_remote=False).
              try {
                await api.post('/api/profile/settings', { tutor_remote_ok: false });
                S.state = await api.get('/api/state');
                toast('Done — the book will answer with its own voice from here on.');
                renderRoute();
              } catch (e) { toast('That setting did not take just now — the fault is the wire, never you. Try it once more.'); }
            } }, 'Keep answers in the book'))
        : null),
    log);
  function push(role, text, cls) {
    const wrap = el('div', { class: 'msg ' + (cls || role) }, text);
    if (role === 'book' && cls !== 'think' && S.stage <= 2) { const s = speakBtn(() => text, 'Read aloud'); s.style.cssText = 'width:28px;height:28px;font-size:13px;margin-top:6px'; wrap.append(el('div', {}, s)); }
    log.append(wrap); log.scrollTop = log.scrollHeight; return wrap;
  }
  const intro = "I'm here as you read “" + title + "”. Ask me anything — why, how, what if — and I'll help you think it through.";
  push('book', intro);
  const input = el('input', { type: 'text', 'aria-label': 'Ask the book a question', placeholder: 'Ask the book…', onkeydown: e => { if (e.key === 'Enter') send(); } });
  async function send() {
    const q = input.value.trim(); if (!q) return; input.value = '';
    push('me', q); messages.push({ role: 'user', content: q });
    const thinking = push('book', el('span', { class: 'think-dots', 'aria-label': 'The book is thinking' }, el('i', {}), el('i', {}), el('i', {})), 'book think');
    const excerpt = ($('#article') ? $('#article').textContent : '').slice(0, 2400);
    try {
      const r = await api.post('/api/tutor', { messages, title, excerpt });
      thinking.remove(); tutorFails = 0; push('book', r.reply); messages.push({ role: 'assistant', content: r.reply });
      maybeSpeak(r.reply);
    } catch (e) {
      thinking.remove();
      // One dropped thought is a shrug; a dead wire deserves the DON'T PANIC
      // register — reassure, name the likely cause, and stop looping the
      // same one-liner at a reader whose tutor is persistently unreachable.
      tutorFails++;
      push('book', tutorFails < 2
        ? 'I lost my thought — ask me again?'
        : "Don't panic — my voice is not reaching you just now, which is almost certainly the network and never you. Everything you have read and learned is safely written down; keep reading, and ask me again when the book reconnects.");
    }
  }
  panel.append(el('div', { class: 'composer' }, input, btn({ onclick: send }, 'Ask')));
  return panel;
}

/* ---------------- Practice & Quiz ---------------- */
async function startPractice(nodeId, gen, stage) {
  try {
    const cap = stage <= 1 ? 5 : 6;
    const data = await api.get(`/api/practice/${gen}?n=${cap}&level=${stage || 1}&node_id=${encodeURIComponent(nodeId || '')}`);
    runQuestions({ title: 'Practice', questions: data.questions, nodeId, kind: 'practice', stage, token: data.token || '' });
  } catch (e) { toast('The practice page would not open just now — try once more. Nothing is lost.'); }
}
async function startQuiz(nodeId) {
  const ov = spinnerOverlay('Composing your quiz…');
  try {
    // Five graded questions, plus the unmarked one to write at the end — the
    // same six on screen as before. Asking for six graded from a bank of ten
    // meant two spaced sittings shared 60% of their paper by arithmetic alone.
    const cap = 5;
    const data = await api.get('/api/quiz/' + nodeId + '?n=' + cap);
    ov.remove();
    if (!data.questions.length) {
      // Never dead-end: fall back to the node's practice generator.
      try {
        const node = await api.get('/api/curriculum/node/' + nodeId);
        if (node.practice) return startPractice(nodeId, node.practice, node.stage);
      } catch (e) {}
      toast('Nothing to quiz here yet — try reading first.');
      return;
    }
    runQuestions({ title: data.title, questions: data.questions, nodeId, kind: 'quiz', stage: data.stage, token: data.token });
  } catch (e) { ov.remove(); toast('This quiz lives beyond your shelf — the book will fetch it when you are back online.'); }
}
// Mounted empty, filled once it is in the document: a live region that arrives
// with its text already inside it is announced unreliably or not at all — the
// same fix every other status node in this file already carries.
function spinnerOverlay(msg) {
  const box = el('div', { class: 'modal', role: 'status', style: 'text-align:center' });
  const ov = el('div', { id: 'overlay' }, box);
  document.body.append(ov);
  setTimeout(() => { box.append(el('div', { class: 'spinner' }), el('p', { class: 'muted' }, msg)); }, 30);
  return ov;
}

function runQuestions({ title, questions, nodeId, kind, stage, isRetry = false, token = '' }) {
  const young = (stage != null ? stage : S.stage) <= 1;
  let i = 0, correct = 0; const answers = [], confidences = [], oks = []; let confidence = null;
  openModal({
    label: (String(title).toLowerCase().includes(String(kind).toLowerCase())
            ? title : title + ' ' + kind), dismissable: true, dismissLabel: 'Close quiz',
    build: (modal, close) => { drawQuestion(modal, close); }
  });

  function normalize(s) { return String(s).trim().toLowerCase().replace(/\s+/g, ''); }
  function nudge(card, msg, field) {
    const region = card.querySelector('.q-live');
    if (!region) return;
    region.className = 'q-live q-nudge';
    // Re-announce even when the text is identical: writing the same string is
    // no DOM change at all, so pressing Check twice was guaranteed silence.
    region.textContent = '';
    setTimeout(() => { region.textContent = msg; }, 30);
    if (field) {
      if (!region.id) region.id = 'nudge-' + Math.random().toString(36).slice(2, 8);
      field.setAttribute('aria-describedby', region.id);
      field.setAttribute('aria-invalid', 'true');
    }
  }
  // The paper ships without its answer key, so the book marks each answer.
  async function mark(q, given) {
    // A retry batch carries no server token (its paper was already redeemed
    // by the first pass's submit) — grade it locally against the answer the
    // first pass already revealed to this reader for exactly these items.
    if (!token) return { correct: normalize(given) === normalize(q.answer || ''), answer: q.answer || '', explain: q.explain || '' };
    try {
      return await api.post('/api/quiz/check', { token, id: q.id, answer: String(given) });
    } catch (e) {
      return { correct: false, answer: '', explain: q.explain || '', offline: true };
    }
  }
  function drawQuestion(modal, close) {
    const q = questions[i]; confidence = null;
    modal.innerHTML = '';
    modal.append(closeBtn(close));
    // The heading is the question's identity; sending focus here announces the
    // new question and starts the tab order at the top of it. Emptying the modal
    // while "Next →" had focus used to drop focus to <body>, so every question
    // of the commonest type cost a full re-tab from the document start.
    const progress = el('div', { class: 'q-progress', tabindex: '-1',
      role: 'heading', 'aria-level': '2' },
      (String(title).toLowerCase() === String(kind).toLowerCase()
        ? kind.toUpperCase() : kind.toUpperCase() + ' · ' + title) +
      ' — ' + (i + 1) + ' of ' + questions.length);
    modal.append(progress);
    // Only claim focus here when nothing else in the card will: the produced
    // response branches focus their own field, and two moves 20ms apart cut the
    // heading announcement in half.
    const selfFocusing = q.kind === 'short' || q.kind === 'numeric';
    if (i > 0 && !selfFocusing) setTimeout(() => progress.focus(), 20);
    const card = el('div', { class: 'q-card' });
    // Feedback goes *into* this, which is on the page before there is anything
    // to say. A live region inserted with its text already inside it is
    // announced unreliably or not at all — which made every verdict, every
    // explanation and every nudge silent to a screen reader.
    const say = el('div', { class: 'q-live', role: 'status', 'aria-live': 'polite' });
    const speakSource = () => (q.say || (q.prompt + '. ' + (q.choices ? q.choices.join(', ') : '')));
    if (S.stage <= 2 || q.say) card.append(el('div', { class: 'speak-row' }, speakBtn(speakSource, 'Read the question aloud')));
    card.append(el('div', { class: 'q-prompt' }, q.prompt));
    if (young || q.say) maybeSpeak(speakSource());

    // Optional confidence (metacognition) for older learners on quizzes.
    let confidenceRow = null;
    if (kind === 'quiz') {
      // Mutually exclusive options are a radiogroup, not a row of toggles:
      // aria-pressed buttons read as independent switches. Roving tabindex +
      // arrow keys, mirroring the onboarding breadth chooser.
      confidenceRow = el('div', { class: 'confidence', role: 'radiogroup', 'aria-label': 'How sure are you?' });
      (young ? [[[glyph('unsure', 18), ' Not sure'], 1], [[glyph('known', 18), ' I know it'], 3]]
             : [['Guess', 1], ['Unsure', 2], ['Sure', 3]]).forEach(([lab, v], k) =>
        confidenceRow.append(btn({ class: 'btn ghost small conf-opt', role: 'radio',
          'aria-checked': 'false', tabindex: k === 0 ? '0' : '-1',
          // Arrows plus Home/End, the full ARIA radiogroup pattern.
          onkeydown: e => {
            if (!['ArrowDown', 'ArrowRight', 'ArrowUp', 'ArrowLeft', 'Home', 'End'].includes(e.key)) return;
            e.preventDefault();
            const all = [...confidenceRow.querySelectorAll('[role=radio]')];
            const cur = all.indexOf(e.currentTarget);
            const dir = (e.key === 'ArrowDown' || e.key === 'ArrowRight') ? 1 : -1;
            const nxt = e.key === 'Home' ? all[0]
                      : e.key === 'End' ? all[all.length - 1]
                      : all[(cur + dir + all.length) % all.length];
            nxt.focus(); nxt.click();
          },
          onclick: (e) => {
            confidence = v;
            confidenceRow.querySelectorAll('[role=radio]').forEach(b => {
              b.classList.remove('picked'); b.setAttribute('aria-checked', 'false'); b.setAttribute('tabindex', '-1'); });
            // The wash alone was a colour-only cue; the class carries a written
            // mark with it so the choice reads without seeing the fill.
            e.currentTarget.classList.add('picked');
            e.currentTarget.setAttribute('aria-checked', 'true');
            e.currentTarget.setAttribute('tabindex', '0');
          } }, ...[].concat(lab), el('span', { class: 'conf-mark' }, '✓ Chosen'))));
    }

    if (q.kind === 'choice') {
      const boxEl = el('div', { class: 'q-choices', role: 'group', 'aria-label': 'Answers' });
      q.choices.forEach(ch => {
        const b = btn({ class: 'choice', onclick: () => { pick(b, ch, q, boxEl, card, modal, close); } }, ch);
        b._value = ch;   // never re-read textContent
        if (q.speak_choices) {
          // The speaker sits beside the choice, not inside it: a button may not
          // contain another button, and it would garble the accessible name.
          const row = el('div', { class: 'choice-row' }, b, speakInline(ch));
          boxEl.append(row);
        } else {
          boxEl.append(b);
        }
      });
      if (confidenceRow) card.append(el('p', { class: 'muted', style: 'margin:2px 0 6px' }, 'How sure are you?'), confidenceRow);
      card.append(boxEl);
    } else if (q.kind === 'order') {
      // Tap the items into sequence — a produced answer, not a recognised one.
      const chosen = [];
      const tray = el('div', { class: 'order-tray', role: 'group', 'aria-label': 'Tap in order' });
      const slot = el('div', { class: 'order-slot', 'aria-live': 'polite',
        'aria-label': 'Your order so far' });
      const redraw = () => {
        slot.innerHTML = '';
        chosen.forEach(v => slot.append(el('span', { class: 'order-chip placed' }, v)));
        if (!chosen.length) slot.append(el('span', { class: 'muted' }, 'Tap them in order…'));
      };
      q.items.forEach(v => {
        const b = btn({ class: 'order-chip', onclick: () => {
          if (b.disabled) return;
          b.disabled = true; chosen.push(v); redraw();
          if (chosen.length === q.items.length) { submitOrder(chosen, q, card, modal, close); return; }
          // Disabling the chip we just used must not dump focus to <body>.
          const nxt = tray.querySelector('.order-chip:not(:disabled)');
          if (nxt) nxt.focus();
        } }, v);
        tray.append(b);
      });
      // Mount the live region first, then fill it. Calling redraw() before the
      // append meant the slot arrived in the document already containing its
      // instruction — announced once on insert, and unreliably thereafter.
      card.append(slot, tray,
        btn({ class: 'btn ghost small', style: 'margin-top:10px', onclick: () => {
          chosen.length = 0; tray.querySelectorAll('button').forEach(b => b.disabled = false); redraw();
        } }, '↺ Start over'));
      redraw();
    } else if (q.kind === 'short') {
      // Constructed response: the reader must produce the idea, not spot it.
      const ta = el('textarea', { rows: '4', 'aria-label': 'Your answer',
        placeholder: 'Explain it in your own words…',
        style: 'width:100%;padding:12px;font-size:17px;font-family:var(--serif);border:1px solid var(--rule);border-radius:8px;background:var(--field);color:var(--ink)' });
      if (confidenceRow) card.append(el('p', { class: 'muted', style: 'margin:2px 0 6px' }, 'How sure are you?'), confidenceRow);
      card.append(ta, btn({ class: 'btn gold', style: 'margin-top:10px', onclick: () => submitShort(ta, q, card, modal, close) }, 'Check my answer'));
      setTimeout(() => ta.focus(), 40);
    } else {
      const inp = el('input', { type: 'text', inputmode: 'decimal', 'aria-label': 'Your answer', placeholder: 'Your answer', style: 'padding:12px;font-size:20px;text-align:center;width:60%', onkeydown: e => { if (e.key === 'Enter') submitNum(inp, q, card, modal, close); } });
      if (confidenceRow) card.append(el('p', { class: 'muted', style: 'margin:2px 0 6px' }, 'How sure are you?'), confidenceRow);
      card.append(el('div', { class: 'q-numeric' }, inp, btn({ class: 'btn gold', onclick: () => submitNum(inp, q, card, modal, close) }, 'Check')));
      setTimeout(() => inp.focus(), 40);
    }
    card.append(say);
    modal.append(card);
  }
  function speakInline(text) { const b = btn({ class: 'speak-btn', style: 'width:30px;height:30px;font-size:14px', 'aria-label': 'Say ' + text, onclick: e => { e.stopPropagation(); speakText(text); } }, glyph('speak', 16)); return b; }
  async function pick(b, ch, q, boxEl, card, modal, close) {
    boxEl.querySelectorAll('.choice').forEach(x => x.disabled = true);
    holdFocus(card, 'Checking…');
    const m = await mark(q, ch);
    // The verdict must never be colour-only: mark the buttons with ✓/✗ as
    // well as tint, and always say the verdict in words in the live region —
    // even when the question ships no explanation.
    b.classList.add(m.correct ? 'correct' : 'wrong');
    b.prepend((m.correct ? '✓ ' : '✗ '));
    if (!m.correct && m.answer) boxEl.querySelectorAll('.choice').forEach(x => {
      if (normalize(x._value) === normalize(m.answer)) { x.classList.add('correct'); x.prepend('✓ '); } });
    const key = m.answer || q.answer || '';
    tell(card, m.correct ? '✓ Correct.'
                         : ('Not quite' + (key ? ' — the answer is ' + key + '.' : '.')));
    reveal(m.correct, { ...q, answer: m.answer, explain: m.explain || q.explain }, ch, card, modal, close);
  }
  async function submitOrder(chosen, q, card, modal, close) {
    card.querySelectorAll('.order-chip').forEach(c => c.disabled = true);
    holdFocus(card, 'Checking…');
    const m = await mark(q, chosen.join(' '));
    card.querySelector('.order-slot').classList.add(m.correct ? 'correct' : 'wrong');
    // Never colour-only: always state the verdict in words as well.
    tell(card, m.correct ? '✓ That is the right order.'
                         : 'Not quite — the right order is: ' + m.answer);
    reveal(m.correct, { ...q, answer: m.answer }, chosen.join(' '), card, modal, close);
  }

  async function submitShort(ta, q, card, modal, close) {
    const given = ta.value.trim();
    // The book answers back only once the reader has committed to something.
    if (!given) { nudge(card, 'Write what you think first — then the book will answer.', ta); ta.focus(); return; }
    ta.removeAttribute('aria-invalid');
    ta.disabled = true;
    holdFocus(card, 'Checking…');
    const m = await mark(q, given);
    ta.style.borderColor = m.correct ? 'var(--green)' : 'var(--accent)';
    tell(card, m.correct ? '✓ You covered the main ideas.'
                         : 'Compare your answer with the model answer below.');
    reveal(m.correct, { ...q, answer: m.answer, explain: m.explain || q.explain }, given, card, modal, close);
  }

  async function submitNum(inp, q, card, modal, close) {
    const given = String(inp.value).trim();
    if (!given) { nudge(card, 'Put down your best answer first.', inp); inp.focus(); return; }
    inp.removeAttribute('aria-invalid');
    inp.disabled = true;
    holdFocus(card, 'Checking…');
    const m = await mark(q, given);
    inp.style.borderColor = m.correct ? 'var(--green)' : 'var(--accent)';
    // A green border was the whole verdict here (SC 1.4.1), and with no
    // explain to reveal the live region stayed on 'Checking…' forever
    // (SC 4.1.3). The other three answer types all say it in words; so does
    // this one now.
    tell(card, m.correct ? '✓ Correct.'
                         : (m.answer ? 'Not quite — the answer is ' + m.answer + '.' : 'Not quite.'));
    if (!m.correct && m.answer) inp.value = given + '  →  ' + m.answer;
    reveal(m.correct, { ...q, answer: m.answer, explain: m.explain || q.explain }, given, card, modal, close);
  }
  function holdFocus(card, msg) {
    const region = card.querySelector('.q-live');
    if (!region) return;
    // Disabling the control that has focus drops it to <body> — and the round
    // trip to mark the answer is a whole network hop long, so on any real
    // connection the dialog spends every question with focus outside itself.
    // The trap cannot help: with activeElement on body it matches neither the
    // first nor the last focusable, so Tab walks straight out of the dialog.
    region.className = 'q-live q-checking';
    region.textContent = msg;
    region.setAttribute('tabindex', '-1');
    region.focus();
  }
  function tell(card, msg, append) {
    const region = card.querySelector('.q-live');
    if (!region) return;
    region.className = 'q-live q-explain';
    region.textContent = append && region.textContent
      ? region.textContent + ' ' + msg : msg;
  }
  function reveal(ok, q, given, card, modal, close) {
    if (ok) correct++;
    oks.push(!!ok);
    // Always submit the learner's real response. Echoing the canonical key on a
    // correct answer would reduce the server's scoring to rubber-stamping the
    // client's own verdict.
    answers.push(given || '');
    confidences.push(confidence || 0);
    // The key never ships with the paper, but once it's revealed for *this*
    // item — right now, to this reader — remember it on the shared question
    // object so a later retry of just the missed ones can be graded without
    // a server token (the original paper's token is spent by then).
    if (q.answer) questions[i].answer = q.answer;
    if (confidence) {
      const mis = (confidence === 3 && !ok) || (confidence === 1 && ok);
      tell(card, mis ? (ok ? 'You knew more than you thought!'
                           : 'Confident but wrong — worth another look.')
                     : 'Well calibrated.', true);
    }
    if (q.explain) tell(card, (ok ? '✓ ' : 'The answer: ') + q.explain, true);
    const nextBtn = btn({ class: 'btn gold', style: 'width:100%;margin-top:16px', onclick: () => next(modal, close) },
      i + 1 < questions.length ? 'Next →' : 'See results');
    card.append(nextBtn);
    setTimeout(() => nextBtn.focus(), 20);   // disabling the choices must not blank focus
    if (ok && !young) toast(praise());
    if (ok && young) tell(card, pickYoungPraise(), true);
    if (young) maybeSpeak(ok ? pickYoungPraise() : 'Not quite. The answer is ' + q.answer);
  }
  function next(modal, close) { i++; if (i < questions.length) drawQuestion(modal, close); else finish(modal, close); }
  async function finish(modal, close) {
    const score = correct / questions.length;
    modal.innerHTML = ''; modal.append(closeBtn(close));
    // Emptying the modal while "See results" had focus left it on <body> —
    // inside a dialog still claiming aria-modal, so the trap could not even
    // wrap. The results screen was never announced. This is the fix already
    // made for the end of the review deck, in the path readers travel most.
    const splashHead = el('h2', { tabindex: '-1', class: 'result-heading' }, 'What the book made of it');
    modal.append(splashHead);
    setTimeout(() => splashHead.focus(), 30);
    const stars = score >= 0.9 ? '★★★' : score >= 0.7 ? '★★☆' : score >= 0.4 ? '★☆☆' : '☆☆☆';
    const splash = el('div', { class: 'result-splash' });
    splash.append(el('div', { class: 'stars', style: 'color:var(--gold)' }, stars));
    if (!young) splash.append(el('div', { class: 'score' }, Math.round(score * 100) + '%'));
    splash.append(el('p', {}, correct + ' of ' + questions.length + ' correct.'));
    let msg = '', msgTone = 'neutral', ascension = null, xp = 0, calibration = null;
    if (nodeId && !isRetry) {
      // A retry of only the missed items must not be scored as a fresh
      // attempt — otherwise failing then re-answering 5 of 6 posts 100%.
      try {
        if (kind === 'quiz') {
          const r = await api.post('/api/quiz/submit', { node_id: nodeId, answers, make_cards: true, confidence: confidences, token });
          xp = r.mastery.xp_gained || 0; ascension = r.ascension; calibration = r.calibration;
          if (r.mastery.newly_mastered) { msg = r.mastery.proven
            ? '✦ Mastered! You have proved this one — it is now truly yours.'
            : '✦ Mastered! This lesson is now complete.'; msgTone = 'good'; }
          else if (r.mastery.proven) msg = 'Reviewed — already proved.';
          else if (r.mastery.mastered) msg = 'The book assumed you knew this. Pass it once more, a day or two apart, to prove it.';
          else if (r.mastery.lost_mastery) { msg = 'This one has slipped — master it again to lock it back in.'; msgTone = 'warn'; }
          else msg = 'Progress: ' + Math.round(r.mastery.level * 100) + '% toward mastery' + (r.mastery.level >= 0.8 ? ' — come back in a day or two to lock it in.' : '.');
          if (r.cards_added) msg += ' ' + r.cards_added + ' review card' + (r.cards_added > 1 ? 's' : '') + ' added.';
          if (r.mastery.newly_mastered) celebrate();
        } else {
          const r = await api.post('/api/attempt', { node_id: nodeId, answers, token });
          xp = r.xp_gained || 0; ascension = r.ascension;
          msg = 'Set down in the Book.' + (r.newly_mastered ? ' ✦ Mastered!' : '');
          if (r.newly_mastered) { msgTone = 'good'; celebrate(); }
        }
      } catch (e) {
        msg = 'Held in the margin for now — the book will copy it into the record the moment it can. Nothing is lost.';
      }
    } else if (isRetry) {
      msg = 'Good — those are the ones that needed another look.';
    }
    if (xp) { splash.append(el('p', { style: 'color:var(--gold-ink);font-weight:700;font-size:18px' }, '+' + xp + ' XP')); flyXP(xp); }
    if (calibration && calibration.total) {
      let cal;
      if (calibration.overconfident > calibration.total / 3) cal = 'You were sure on ' + calibration.overconfident + ' you got wrong — worth a second look.';
      else if (calibration.underconfident > calibration.total / 3) cal = 'You knew ' + calibration.underconfident + ' better than you thought. Trust yourself a little more.';
      else cal = 'Your sense of what you know was well calibrated.';
      splash.append(el('p', { class: 'muted' }, glyph('target', 15), ' ' + cal));
    }
    splash.append(el('p', { class: 'result-msg result-msg-' + msgTone }, msg));
    // Productive failure: retry the ones you missed. Use the verdict each
    // item was actually graded with — re-deriving it here from a string
    // comparison would both miss items the server never sent an answer key
    // for and mis-flag short-answer items the server graded as "close enough"
    // (a fuzzy match, not an exact one) as if they'd been missed.
    const missedIdx = oks.map((ok, k) => ok ? -1 : k).filter(k => k >= 0);
    const controls = el('div', { style: 'display:flex;gap:10px;justify-content:center;margin-top:18px;flex-wrap:wrap' });
    if (missedIdx.length) controls.append(btn({ class: 'btn', onclick: () => { const retry = missedIdx.map(k => questions[k]); close(); runQuestions({ title, questions: retry, nodeId, kind, stage, isRetry: true }); } }, '↻ Retry the ' + missedIdx.length + ' you missed'));
    controls.append(btn({ class: 'btn ghost', onclick: close }, 'Close'));
    if (nodeId) controls.append(btn({ class: 'btn gold', onclick: () => { close(); go('node', nodeId); } }, 'Back to lesson'));
    splash.append(controls);
    modal.append(splash);
    if (young) maybeSpeak('You got ' + correct + ' out of ' + questions.length + '. ' + (score >= 0.7 ? 'Wonderful work!' : 'Good try — let us practice a little more.'));
    if (ascension) setTimeout(() => stageAscension(ascension), 900);
    refreshStats();
  }
  function praise() { return ['Well reasoned.', 'Yes!', 'Exactly.', 'Good thinking.', 'That is it.'][Math.floor(Math.random() * 5)]; }
  function pickYoungPraise() { return ['You did it!', 'Yes! Great job!', 'Wonderful!', 'You got it!', 'Brilliant!'][Math.floor(Math.random() * 5)]; }
}

/* ---------------- celebrations ---------------- */
function flyXP(xp) {
  // Centering lives inside the keyframes: an animated transform replaces the
  // inline one wholesale, so an inline translateX(-50%) silently vanished on
  // the first frame and the badge sat half its width right of centre.
  const p = el('div', { class: 'xp-pop' }, '+' + xp + ' XP');
  document.body.append(p); setTimeout(() => p.remove(), 1500);
}
function celebrate() { confetti(); }
function confetti() {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const box = el('div', { class: 'confetti', 'aria-hidden': 'true' });
  // Drawn from the live palette rather than a hardcoded list, so by day the
  // pieces are inked paper and by night they are phosphor sparks — the same
  // ceremony, in whichever light the book is currently being read.
  const cs = getComputedStyle(document.documentElement);
  const colors = ['--gold-bright', '--accent-2', '--link', '--green', '--gold']
    .map(v => cs.getPropertyValue(v).trim());
  for (let k = 0; k < 60; k++) box.append(el('i', { style: `left:${Math.random() * 100}%;background:${colors[k % 5]};animation-duration:${1.6 + Math.random() * 1.4}s;animation-delay:${Math.random() * 0.4}s` }));
  document.body.append(box); setTimeout(() => box.remove(), 3600);
}
function streakCeremony(days) {
  confetti();
  openModal({ label: 'Streak milestone', dismissable: true, build: (modal, close) => {
    modal.append(el('div', { class: 'ceremony' },
      el('div', { class: 'seal', 'aria-hidden': 'true' }, glyph('flame', 42)),
      el('div', { class: 'sub' }, 'A HABIT IS FORMING'),
      el('h2', {}, days + ' days in a row'),
      el('p', { class: 'muted' }, 'The book has been open every day. That steadiness, more than any single lesson, is what carries you to the frontier.'),
      btn({ class: 'btn gold', onclick: close }, 'Keep going ', glyph('spark', 15))));
    maybeSpeak('Wonderful! You have read for ' + days + ' days in a row.', 2);
  } });
}

function stageAscension(info) {
  confetti();
  openModal({
    label: 'You have advanced', dismissable: true,
    build: (modal, close) => {
      modal.append(el('div', { class: 'ceremony' },
        el('div', { class: 'seal', 'aria-hidden': 'true' }, glyph('spark', 42)),
        el('div', { class: 'sub' }, 'A NEW STAGE OPENS'),
        el('h2', {}, 'You are now a ' + info.name),
        el('p', { class: 'muted' }, info.title + ' — new lessons across your fields have unlocked. The book has grown with you.'),
        btn({ class: 'btn gold', onclick: close }, 'Onward ', glyph('spark', 15))));
      maybeSpeak('Congratulations! You are now a ' + info.name + '. New lessons have opened.', 2);
    }
  });
  // refresh sidebar rank label
  api.get('/api/state').then(st => {
    S.state = st;
    if (st.profile) {
      S.stage = Number.isFinite(st.profile.stage) ? st.profile.stage : 2;
      document.body.dataset.stage = st.profile.stage;
      // Repainting the page behind an open ceremony used to pull focus onto
      // #page, so Tab walked the whole background while the dialog still
      // claimed aria-modal. On a fast localhost the race was invisible; at
      // 250ms it happened every time. Skipping renderRoute() entirely while
      // a modal was open "fixed" that by leaving #page permanently blank —
      // renderShell() wipes and rebuilds an empty <main id="page">, and
      // nothing ever filled it back in once the modal(s) closed on a route
      // that hadn't changed. renderRoute() already refuses to steal focus
      // from an open dialog on its own (see its own guard below), so it is
      // safe — and necessary — to always call it here.
      renderShell();
      renderRoute();
    }
  }).catch(() => {});
}

/* ---------------- Atlas ---------------- */
async function renderAtlas(page) {
  const g = await guard(page, () => api.get('/api/curriculum'));
  if (!g) return;
  S.curriculum = g;
  page.append(pagehead('The whole journey', 'The Atlas',
    'Every field, from preschool roots to the graduate frontier. Golden tiles are open to you now; locked tiles show exactly what will unlock them. Click any to begin.'));
  // The wall of locks is the honest shape of a whole education, and it should
  // read as an invitation rather than a verdict. One line, in the Guide's
  // register: the scale is the point, and it is survivable.
  page.append(el('p', { class: 'epigraph' },
    'Yes, it is an enormous amount. Every reader who ever finished started with exactly one tile.'));
  g.domains.forEach(d => {
    const block = el('section', { class: 'domain-block', 'aria-label': d.name });
    const total = d.stages.reduce((s, x) => s + x.total, 0);
    block.append(el('div', { class: 'domain-head' },
      // Same daylight-hex lift as the lesson-card domain tag: themed via
      // --domain-lift so the ten curriculum colours survive the night palette.
      el('div', { class: 'ic', style: `background:color-mix(in srgb, ${d.color}, white var(--domain-lift, 0%))`, 'aria-hidden': 'true' }, domainMark(d, 20)),
      el('div', {}, el('h3', {}, d.name), el('div', { class: 'tag' }, d.mastered + ' / ' + total + ' mastered — ' + (d.tagline || '')))));
    for (let s = 0; s < 6; s++) {
      const nodes = g.nodes.filter(n => n.domain === d.id && n.stage === s);
      if (!nodes.length) continue;
      const row = el('div', { class: 'stage-row' });
      row.append(el('div', { class: 'stage-label' }, STAGE_NAMES[s]));
      const nr = el('div', { class: 'node-row' });
      nodes.forEach(n => {
        const cls = n.mastered ? 'mastered' : (n.unlocked ? 'available' : 'locked');
        // The last node of a field is where the field itself stops knowing —
        // the one tile on this page that nobody has finished. It should not
        // look like one more padlock among forty.
        const frontier = /\.5\.frontier$/.test(n.id);
        const label = n.title + (cls === 'locked' && n.unlock_requirements ? ' — locked' : '')
                    + (frontier ? ' — the frontier of this field' : '');
        nr.append(btn({ class: 'node-dot ' + cls + (frontier ? ' frontier' : ''),
          title: frontier ? 'The edge of what is known — where learning becomes research.'
                          : (n.unlock_requirements ? n.unlock_requirements.join('; ') : (n.goal || '')),
          'aria-label': label,
          onclick: () => { if (n.unlocked || n.mastered) go('node', n.id); else lockedPeek(n); } }, n.title));
      });
      row.append(nr); block.append(row);
    }
    page.append(block);
  });
}
function lockedPeek(n) {
  openModal({ label: n.title + ' locked', dismissable: true, build: (modal, close) => {
    modal.append(el('h2', { style: 'margin-top:0' }, glyph('lock', 20), ' ' + n.title));
    modal.append(el('p', { class: 'muted' }, n.goal || ''));
    modal.append(el('p', { style: 'font-family:var(--sans);font-weight:600;margin-bottom:6px' }, 'To unlock this:'));
    const box = el('div', {}); (n.unlock_requirements || ['Keep progressing in this field.']).forEach(r => box.append(el('span', { class: 'req-chip' }, r)));
    modal.append(box, btn({ class: 'btn gold', style: 'margin-top:16px', onclick: close }, 'Got it'));
  } });
}

/* ---------------- Review ---------------- */
async function renderReview(page) {
  const data = await guard(page, () => api.get('/api/review/due?limit=30'));
  if (!data) return;
  page.append(pagehead('Spaced repetition', 'Strengthen What You Know',
    'The book brings back what you are about to forget, exactly when you are about to forget it. ' + data.stats.due + ' of ' + data.stats.total + ' cards are due.'));
  // An empty deck is good news, and the page should sound like it knows that
  // — one Guide-flavored wink, then the honest reason to come back.
  if (!data.cards.length) { page.append(emptyLeaf('review', 'The deck rests ✦', 'Every card is exactly where it should be — filed, remembered, mostly harmless. Learn something new today and the book will have more to bring back tomorrow.')); return; }
  // The deck is a physical thing: the card you are on sits on top of the ones
  // still to come, and the stack visibly thins as you work through it. "Card
  // 3 of 24" tells you the same fact, but you have to read it.
  const deck = el('div', { class: 'deck' });
  page.append(deck);
  let idx = 0;
  let stage = null;
  function draw() {
    const c = data.cards[idx];
    // A fresh .deck-card per card, never innerHTML into the old node: the
    // settle animation lives on the element, and CSS only plays it when the
    // element enters the DOM — mutating children restarts nothing, so the
    // deck's signature settle used to fire once per session and then go dead
    // for cards 2..N. Replacing the node makes every card actually land.
    const fresh = el('div', { class: 'card deck-card' });
    if (stage) stage.replaceWith(fresh); else deck.append(fresh);
    stage = fresh;
    const left = data.cards.length - idx - 1;
    // Two drawn layers sit behind the card, so there are exactly three states
    // to say: none left, one left, more than one. Emitting a 3 as well made
    // depths 2 and 3 render identically — a level the CSS could not show.
    deck.dataset.depth = String(Math.max(0, Math.min(2, left)));
    const progress = el('div', { class: 'q-progress', tabindex: '-1',
      role: 'heading', 'aria-level': '2' },
      'Card ' + (idx + 1) + ' of ' + data.cards.length + (c.article ? ' · ' + c.article : ''));
    stage.append(progress);
    // Every card announces its own count — including the first, which used
    // to leave the reader parked on #page hearing only the generic page
    // label while every later card said "Card N of M". The 20ms delay lands
    // after renderRoute's own page.focus(), so the specific label wins.
    setTimeout(() => progress.focus(), 20);
    // Where the answer and the grading buttons will go. Mounted empty and
    // filled later, so assistive tech has a region to announce into.
    var answerRegion = el('div', { class: 'reveal-region', role: 'status', 'aria-live': 'polite' });
    const promptRow = el('div', { class: 'speak-row' }, S.stage <= 2 ? speakBtn(() => c.front, 'Read aloud') : null, el('div', { class: 'q-prompt', style: 'min-height:60px;flex:1' }, c.front));
    stage.append(promptRow);
    answerRegion.className = 'q-explain reveal-region';
    answerRegion.style.fontSize = '16px';
    const showBtn = btn({ class: 'btn gold js-show-answer', style: 'width:100%',
      onclick: () => { showBtn.disabled = true; revealBack(c, answerRegion); } },
      'Show answer ', el('kbd', { class: 'key-hint', 'aria-hidden': 'true' }, 'space'));
    stage.append(showBtn);
    stage.append(answerRegion);
    if (S.stage <= 1) maybeSpeak(c.front);
  }
  function revealBack(c, region) {
    // Write into the region that is already on the page rather than inserting a
    // pre-filled one: a live region that arrives with its text already in it is
    // announced unreliably, or not at all.
    region.textContent = c.back;
    const grades = [[0, 'Blank', 'grade-blank'], [3, 'Hard', 'grade-hard'], [4, 'Good', 'grade-good'], [5, 'Easy', 'grade-easy']];
    const row = el('div', { style: 'display:flex;gap:8px;margin-top:16px', role: 'group', 'aria-label': 'How well did you recall?' });
    grades.forEach(([q, label, cls], k) => row.append(btn({ class: 'btn small ' + cls, onclick: () => grade(c, q) },
      label + ' ', el('kbd', { class: 'key-hint', 'aria-hidden': 'true' }, String(k + 1)))));
    stage.append(row);
    setTimeout(() => row.querySelector('button').focus(), 20);
  }
  // The deck at the speed of thought: space turns the card, 1-4 grade it —
  // the convention every serious deck tool has taught reviewers' hands.
  // Buttons stay the visible truth; the keys are a faster route to them, so
  // focus, announcement and disabled-state all keep working unchanged.
  function onKey(e) {
    // Belt-and-braces: renderRoute removes this deterministically on any
    // navigation; this guard covers re-renders that bypass the router.
    if (!stage || !document.contains(stage)) { document.removeEventListener('keydown', onKey); if (_reviewKeyHandler === onKey) _reviewKeyHandler = null; return; }
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    if (e.key === ' ') {
      const show = stage.querySelector('.js-show-answer:not([disabled])');
      if (show) { e.preventDefault(); show.click(); }
    } else if (/^[1-4]$/.test(e.key)) {
      const gradeBtns = stage.querySelectorAll('.grade-blank, .grade-hard, .grade-good, .grade-easy');
      const b = gradeBtns[+e.key - 1];
      if (b) { e.preventDefault(); b.click(); }
    }
  }
  // One live handler at a time: the end-of-deck path re-enters renderReview
  // without passing through renderRoute, so clear any predecessor here.
  if (_reviewKeyHandler) document.removeEventListener('keydown', _reviewKeyHandler);
  _reviewKeyHandler = onKey;
  document.addEventListener('keydown', onKey);
  async function grade(c, q) {
    let r;
    try {
      r = await api.post('/api/review', { card_id: c.id, quality: q });
    } catch (e) {
      toast('The book could not file that one — the card stays right where it is. Nothing is lost.');
      return;  // never silently drop the card
    }
    if (r.xp_gained) flyXP(r.xp_gained);
    if (r.next_days >= 1) toast('Back in ' + Math.round(r.next_days) + (r.next_days < 2 ? ' day' : ' days'));
    else toast('Back again in a few minutes — this one is still settling.');
    idx++;
    if (idx < data.cards.length) draw();
    else {
      page.innerHTML = '';
      renderReview(page);
      // The end of the deck is still a re-render, and it was the one that
      // dropped focus to <body> — it never goes through renderRoute.
      setTimeout(() => {
        const h = page.querySelector('h2, .pagehead h2');
        if (h) { h.setAttribute('tabindex', '-1'); h.focus(); }
        else { page.setAttribute('tabindex', '-1'); page.focus(); }
      }, 30);
      // The empty-deck state gets a whole Guide-flavoured line; the moment
      // the reader actually earns it was two flat words. It is the end of a
      // sitting, and the book should sound like it noticed.
      toast('The deck is closed for now ✦ Every card you turned is a little harder to forget.');
      refreshStats();
    }
  }
  draw();
}

/* ---------------- Search / Look up ---------------- */
async function renderSearch(page) {
  page.append(pagehead('The whole encyclopedia, inside this book', 'Look Up Anything',
    'Millions of articles. Search a person, a place, an idea — and follow the links wherever they lead.'));
  page.append(el('p', { class: 'epigraph' }, 'Don’t panic. Whatever it is, the book has almost certainly heard of it.'));
  const input = el('input', { type: 'search', 'aria-label': 'Search', placeholder: 'Search for anything…', autofocus: true });
  const box = el('div', { id: 'searchbox' }, el('span', { class: 'mag', 'aria-hidden': 'true' }, glyph('lookup', 18)), input);
  const results = el('div', { class: 'card', role: 'region', 'aria-label': 'Results', style: 'padding:0;overflow:hidden' });
  // Results arrive asynchronously into a plain landmark, so a screen reader
  // heard nothing at all on a top-level nav destination — not the count, not
  // "No matches", not the failure notice (WCAG 4.1.3). Mounted empty and
  // filled later, the same way every other live region in this file is: one
  // that arrives already containing its text is announced unreliably or not
  // at all.
  const say = el('div', { class: 'search-live', role: 'status', 'aria-live': 'polite' });
  page.append(box, say, results, btn({ class: 'btn ghost small', style: 'margin-top:14px', onclick: surprise }, glyph('dice', 16), ' Surprise me'));
  let timer;
  // Typing searches the shelf only (instant); Enter also asks Wikipedia.
  input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => runSearch(input.value, results, false, say), 200); });
  input.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return;
    const t = input.value.trim();
    if (t) runSearch(t, results, true, say);
  });
  setTimeout(() => input.focus(), 30);
}
// Typing fires one request per 200ms pause, and the shelf answers faster than
// Wikipedia does — so an earlier, slower query could land after a later one and
// overwrite fresher results with staler ones. Only the most recent request is
// allowed to write; the rest are read and dropped.
let _searchSeq = 0;
async function runSearch(q, results, live = false, say = null) {
  const tell = msg => { if (say) say.textContent = msg; };
  const seq = ++_searchSeq;
  q = q.trim(); if (q.length < 2) { results.innerHTML = ''; tell(''); return; }
  try {
    const data = await api.get('/api/search?q=' + encodeURIComponent(q) + (live ? '&live=true' : ''));
    if (seq !== _searchSeq) return;
    results.innerHTML = '';
    if (!data.results.length) {
      tell('No matches on your shelf.');
      results.append(el('div', { class: 'search-result' }, el('span', { class: 'muted' }, 'No matches on your shelf.')));
      if (!live) results.append(btn({ class: 'search-result', style: 'display:block;width:100%;text-align:left', onclick: () => runSearch(q, results, true, say) }, el('b', {}, glyph('globe', 16), ' Search all of Wikipedia for “' + q + '”')));
      return;
    }
    // The count is the thing a screen-reader user cannot get any other way:
    // sighted readers see the list length at a glance.
    tell(data.results.length + (data.results.length === 1 ? ' result for ' : ' results for ') + q);
    data.results.forEach(r => {
      const src = r.source === 'live' ? 'Wikipedia' : (String(r.source).includes('simple') ? 'Simple Wiki' : 'Your shelf');
      results.append(btn({ class: 'search-result', style: 'display:block;width:100%;text-align:left', onclick: () => go('reader', r.title) },
        el('b', {}, r.title), ' ', el('span', { class: 'src' }, src)));
    });
  } catch (e) {
    if (seq !== _searchSeq) return;
    results.innerHTML = '';
    tell('The index has wandered off — likely the network, never you. Ask again in a moment.');
    results.append(el('div', { class: 'search-result' }, el('span', { class: 'muted' }, 'The index has wandered off — likely the network, never you. Ask again in a moment.')));
  }
}
async function surprise() { try { const r = await api.get('/api/random'); if (r.title) go('reader', r.title); } catch (e) { toast('The dice need a shelf to land on — download an archive first.'); } }

/* ---------------- Roadmap ---------------- */
async function renderRoadmap(page) {
  const r = await guard(page, () => api.get('/api/roadmap'));
  if (!r) return;
  page.append(pagehead(r.breadth_label, 'Your Path', r.note));
  // The Plan, spoken plainly: a whole education is a civilizational span of
  // time, and the page should carry that weight without ever making it feel
  // like a debt. One quiet epigraph does the work.
  page.append(el('p', { class: 'epigraph' },
    'The Plan is long, and the Plan holds — one reading at a time.'));
  const head = el('div', { class: 'grid three' });
  head.append(
    statCard(r.estimated_years, 'years, as the Plan foresees', r.within_promise ? 'var(--green-ink)' : 'var(--accent)'),
    statCard(r.nodes_mastered + ' / ' + r.nodes_total, 'topics mastered', 'var(--gold-ink)'),
    statCard(r.hours_per_week + 'h', 'per week', 'var(--accent-2)'),
    statCard(r.total_hours ? r.total_hours.toLocaleString() : '—', 'hours in the whole plan', 'var(--ink-soft)'));
  page.append(head);
  page.append(el('div', { style: 'margin:18px 0' },
    btn({ class: 'btn ghost small', onclick: () => offerPlacement(S.state.profile.domains) },
      glyph('target', 16), ' Check my level again')));
  page.append(sectionLabel('The Plan, year by year'));
  const tl = el('div', { class: 'timeline' });
  r.timeline.forEach(y => tl.append(el('div', { class: 'tl-year' }, el('div', { class: 'yr' }, 'Year ' + y.year), el('div', { class: 'ms' }, y.milestones.join(' · ')))));
  // The Plan ends where plans must: at the edge of the known. A terminus
  // marker, hollow where the year-dots are solid.
  tl.append(el('div', { class: 'tl-year tl-end' }, el('div', { class: 'yr' }, 'The Frontier'),
    el('div', { class: 'ms muted' }, 'Where the known ends, and your own work begins.')));
  page.append(tl);
  if (r.stages.length) {
    page.append(sectionLabel('What remains, epoch by epoch'));
    const g = el('div', { class: 'grid two' });
    r.stages.forEach(s => g.append(el('div', { class: 'card' }, el('b', {}, s.name + ' — ' + s.span), el('p', { class: 'muted', style: 'margin:4px 0 0' }, s.nodes_remaining + ' topics · ~' + s.hours_remaining + ' hours'))));
    page.append(g);
  }
}
function statCard(big, label, color) { return el('div', { class: 'card', style: 'text-align:center' }, el('div', { style: `font-size:40px;color:${color};font-weight:600` }, big), el('div', { class: 'muted' }, label)); }

/* ---------------- Journey (journal) ---------------- */
async function renderJourney(page) {
  const j = await guard(page, () => api.get('/api/journal'));
  if (!j) return;
  page.append(pagehead('The story of your learning', 'Your Journey',
    'Every topic you have truly mastered and every stage you have climbed — the record of who you are becoming.'));
  // The chronicle register: this page is the reader's own historical record,
  // and it should sound like one — set down, not displayed.
  page.append(el('p', { class: 'epigraph' }, 'Set down in the Book, in the order it happened.'));
  if (j.best_streak > 0) {
    page.append(el('p', { class: 'muted', style: 'margin-top:-8px' },
      glyph('flame', 15), ' Best streak: ' + j.best_streak + ' day' + (j.best_streak === 1 ? '' : 's') +
      ' — kept even after a streak breaks, so it never disappears.'));
  }
  if (!j.items.length) { page.append(emptyLeaf('journey', 'Your journey begins ✦', 'Nothing is written here yet — which is how every chronicle starts. Master your first lesson and the book will set it down.')); return; }
  const tl = el('div', { class: 'timeline' });
  j.items.forEach(it => {
    if (it.kind === 'ascension') {
      // An ascension is an epoch boundary in the chronicle, not one more
      // entry — inscribed larger, ringed in gold, the timeline's punctuation.
      tl.append(el('div', { class: 'tl-year tl-epoch' }, el('div', { class: 'yr' }, '✦ A New Epoch'), el('div', { class: 'ms' }, el('span', { class: 'jbadge' }, glyph('crown', 15)), 'You became a ' + it.name + ' — ' + (it.title || ''))));
    } else if (it.kind === 'chapter') {
      tl.append(el('div', { class: 'tl-year' }, el('div', { class: 'yr' }, 'Chapter ' + (it.number || '')), el('div', { class: 'ms' }, el('span', { class: 'jbadge' }, glyph('story', 15)), it.title || 'A chapter of your story')));
    } else {
      const d = it.domain ? domainById(it.domain) : { icon: '✓', name: '' };
      tl.append(el('div', { class: 'tl-year' }, el('div', { class: 'yr' }, d.name || 'Mastered'), el('div', { class: 'ms' }, el('span', { class: 'jbadge' }, '✓'), it.title || it.node_id)));
    }
  });
  page.append(tl);
}

/* ---------------- Your Story ---------------- */
async function renderStory(page) {
  const st = await guard(page, () => api.get('/api/story'));
  if (!st) return;
  page.append(pagehead('The book that is being written about you', st.title, st.about));
  const earned = st.chapters.filter(c => c.read && !c.set_aside).length;
  const total = st.chapters.filter(c => !c.set_aside).length;
  page.append(el('p', { class: 'muted', style: 'margin-top:-8px' },
    earned + ' of ' + total + ' chapters earned.'));
  st.chapters.forEach((c, i) => {
    if (c.set_aside) {
      page.append(el('div', { class: 'card card-quiet' },
        el('div', { class: 'kicker' }, 'Chapter ' + (i + 1) + ' · set aside'),
        btn({ class: 'unstyled card-open', onclick: () => openStory(c, false, null) },
          el('h3', { style: 'font-size:18px;margin:0' }, glyph('moon', 16), ' ' + c.title)),
        el('p', { class: 'muted' }, 'This one belongs to a field you did not choose — open it any time.')));
    } else if (c.read) {
      const card = el('div', { class: 'card lesson-card' });
      card.append(el('div', { class: 'kicker' }, 'Chapter ' + (i + 1) + ' · read'),
        btn({ class: 'unstyled card-open', onclick: () => openStory(c, false, null) },
          el('h3', { style: 'font-size:19px' }, glyph('story', 17), ' ' + c.title)),
        el('p', { class: 'muted' }, (c.text[0] || '').slice(0, 120) + '…'));
      page.append(card);
    } else if (c.current) {
      // The chapter you are on is the one always-dark surface in the page
      // flow, so it uses the same chrome vars as the spine and the tutor
      // panel. It was hardcoded brown, which left it the one muddy tile on
      // an otherwise phosphor page once the night palette turned.
      const card = el('div', { class: 'card story-current' });
      card.append(el('div', { class: 'kicker' }, 'Chapter ' + (i + 1) + ' · you are here'),
        el('h3', {}, c.title),
        el('p', {}, (c.text[0] || '').slice(0, 160) + '…'),
        btn({ class: 'btn gold', style: 'margin-top:8px', onclick: () => openStory(c, st.can_advance, st.needs) }, glyph('story', 16), ' Read this chapter'));
      if (st.needs && !st.can_advance) card.append(el('p', { class: 'story-needs' },
        st.needs.faded ? storyWaitingText(st.needs) : 'Opens when you prove ' + storyWaitingText(st.needs) + '.'));
      page.append(card);
    } else {
      page.append(el('div', { class: 'card card-quiet' },
        el('div', { class: 'kicker' }, 'Chapter ' + (i + 1)),
        el('h3', { style: 'font-size:18px' }, glyph('lock', 17), ' Not yet written'),
        el('p', { class: 'muted' }, 'Keep learning — this page is waiting for you.')));
    }
  });
}

/* ---------------- Library ---------------- */
async function renderLibrary(page) {
  const data = await guard(page, () => api.get('/api/library'));
  if (!data) return;
  page.append(pagehead('The book contains other books', 'The Shelf',
    'Download knowledge archives to hold them forever, offline, inside the Primer. The complete Wikipedia lives here.'));
  page.append(el('p', { class: 'epigraph' }, 'A vault does not ask permission to remember. Once shelved, always at hand — no wire required.'));
  const st = data.status;
  page.append(el('div', { class: 'card' },
    el('b', {}, glyph('shelf', 16), ' Installed now: ' + st.archives.length + ' archive' + (st.archives.length === 1 ? '' : 's')),
    el('p', { class: 'muted', style: 'margin:4px 0 0' }, st.archives.map(a => a.title + ' (' + a.articles.toLocaleString() + ' articles, ' + a.size_mb + ' MB)').join(' · ') || 'None yet.'),
    el('p', { class: 'muted', style: 'margin:6px 0 0' }, st.cached_articles + ' more articles saved from your online reading.')));
  // A download can run for minutes to hours, polled by wiping and rebuilding
  // this whole page every 3s — the same shape of update Look Up's results
  // and the tutor's replies already learned to announce, just never carried
  // here: a screen-reader user watching a download had no way to know it was
  // moving, or had finished, until they happened to re-visit the page.
  const say = el('div', { class: 'lib-live', role: 'status', 'aria-live': 'polite' });
  page.append(say);
  data.catalog.forEach(item => {
    const c = el('div', { class: 'card lib-item' });
    const meta = el('div', { class: 'meta' }, el('b', {}, item.title), el('p', {}, item.blurb));
    const right = el('div', {});
    if (item.installed) right.append(el('span', { class: 'badge installed' }, '✓ On your shelf'));
    else if (item.download && item.download.status === 'downloading') {
      const pct = item.download.total ? Math.round(100 * item.download.bytes / item.download.total) : 0;
      right.append(el('span', { class: 'badge big' }, 'Downloading ' + pct + '%'), el('div', { class: 'bar', style: 'width:120px;margin-top:6px' }, el('span', { style: `width:${pct}%` })));
    } else right.append(btn({ class: 'btn small', onclick: () => downloadArchive(item.key) }, '↓ ' + item.approx_gb + ' GB'));
    c.append(meta, right); page.append(c);
  });
  page.append(el('p', { class: 'muted', style: 'margin-top:14px' }, 'Archives come from the Kiwix project. The full English Wikipedia with images is ~110 GB; text-only is ~60 GB; Simple English is ~1–3 GB.'));
  const downloading = data.downloads.filter(d => d.status === 'downloading');
  if (downloading.length) {
    const named = downloading.map(d => {
      const entry = data.catalog.find(c => c.key === d.key);
      const pct = d.total ? Math.round(100 * d.bytes / d.total) : 0;
      return (entry ? entry.title : d.key) + ' ' + pct + '%';
    });
    // A live region inserted with its text already inside it is announced
    // unreliably or not at all — mount empty (above), fill after the node
    // has actually landed in the document.
    setTimeout(() => { say.textContent = 'Downloading: ' + named.join(', '); }, 30);
    setTimeout(() => { if (S.view === 'library') renderRoute(); }, 3000);
  }
}
async function downloadArchive(key) {
  try {
    const r = await api.post('/api/library/download', { key });
    // The refusal reason ("unknown catalog key", "not enough room on disk")
    // is useful, but it is not the sentence a reader should meet first: the
    // book explains, then quotes itself. Every other failure path in this
    // file already leads with reassurance; this one printed the backend
    // string verbatim as the whole message.
    if (r.error) { toast('The shelf could not start that download — nothing is lost. (' + r.error + ')'); return; }
    toast('Download started — it continues in the background.'); renderRoute();
  }
  catch (e) { toast('The shelf is out of reach — likely the network, never you. The book will fetch it when you are back online.'); }
}

/* ---------------- accessible modal ---------------- */
let _modalStack = [];
function closeBtn(close) { return btn({ class: 'modal-close', 'aria-label': 'Close', title: 'Close (Esc)', onclick: close }, '×'); }
function openModal({ label, build, dismissable = false, dismissLabel = 'Close', dark = false }) {
  const prevFocus = document.activeElement;
  const ov = el('div', { id: 'overlay' });
  const modal = el('div', { class: 'modal', role: 'dialog', 'aria-modal': 'true', 'aria-label': label || 'Dialog', tabindex: '-1' });
  // Same story as the chapter card: the dark modal is a chrome surface, and
  // hardcoding its brown left it behind when the night palette turned.
  if (dark) modal.classList.add('on-dark');
  function close() {
    ov.remove(); _modalStack = _modalStack.filter(m => m !== entry);
    document.removeEventListener('keydown', onKey);
    if (prevFocus && prevFocus.focus) prevFocus.focus();
  }
  const entry = { ov, close };
  _modalStack.push(entry);
  if (dismissable) modal.append(closeBtn(close));
  build(modal, close);
  ov.append(modal); document.body.append(ov);
  if (dismissable) ov.addEventListener('click', e => { if (e.target === ov) close(); });
  function onKey(e) {
    if (_modalStack[_modalStack.length - 1] !== entry) return;
    if (e.key === 'Escape' && dismissable) { e.preventDefault(); close(); }
    if (e.key === 'Tab') {
      // Disabled and hidden controls cannot take focus; including them made
      // `first`/`last` unfocusable, so preventDefault() would strand Tab.
      const f = [...modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')]
        // closest(), not the element's own attribute: a control inside an
        // aria-hidden wrapper is just as invisible to AT as one marked itself,
        // and counting it as tabbable puts a phantom at either end of the trap.
        .filter(x => !x.disabled && !x.closest('[aria-hidden="true"]')
                  // Not offsetParent: that is null for any position:fixed
                  // control inside the dialog, which would silently fall out
                  // of the trap and break the first/last wrap. A box on the
                  // page is the actual question being asked.
                  && x.getClientRects().length > 0);
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  }
  document.addEventListener('keydown', onKey);
  setTimeout(() => { const f = modal.querySelector('button:not(.modal-close), input, [href]'); (f || modal).focus(); }, 30);
  return entry;
}

boot().catch(e => {
  // A boot that fails only because there is no reader yet is not an error at
  // all — send them to the first page instead of the error card. This needs
  // the domain list to draw its picker, so it only applies once we have one.
  if (isNoProfile(e) && S.domains.length) return toOnboarding();
  // The very first page a reader might ever meet must keep the DON'T PANIC
  // register too: reuse the Guide's error card, with the raw error demoted to
  // fine print rather than shouted as the headline.
  const root = $('#root');
  root.innerHTML = '';
  root.append(el('div', { style: 'max-width:560px;margin:12vh auto 0;padding:0 20px' },
    errCard({ error: String((e && (e.error || e.message)) || e) }, () => location.reload())));
});
