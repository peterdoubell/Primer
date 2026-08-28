/* The Primer — front-end application. Vanilla JS, no build step.
   Accessible (keyboard, ARIA, focus, reduced-motion, dark mode), age-adaptive,
   hash-routed, and game-like. */
'use strict';

// A hosted copy keeps its reader for a month, and then the cookie lapses —
// mid-quiz, as often as not. The server answers 401 rather than summoning the
// browser's own credential box, so it falls to the app to walk the reader to
// the book's sign-in page and remember where they were. Anything else shows
// them the generic "lost its train of thought" card, from which the only
// escape is a reload they have no reason to try.
function toSignIn() {
  const here = location.pathname + location.search + location.hash;
  location.assign('/sign-in?next=' + encodeURIComponent(here));
}

const api = {
  async get(path) { const r = await fetch(path); if (r.status === 401) return toSignIn(), new Promise(() => {}); if (!r.ok) throw await r.json().catch(() => ({ error: r.statusText })); return r.json(); },
  async post(path, body) { const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }); if (r.status === 401) return toSignIn(), new Promise(() => {}); if (!r.ok) throw await r.json().catch(() => ({ error: r.statusText })); return r.json(); },
};

const S = { state: null, domains: [], view: 'today', stage: 2, speak: true, curriculum: null, restoreFocus: null, readerTitle: null };
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
  // A head and shoulders: whose book this is.
  account: '<circle cx="12" cy="8.6" r="3.4"/><path d="M5 20c1-4 4-6 7-6s6 2 7 6"/>',
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

/* ---------------- haptics ----------------
   A book you hold should sometimes answer the hand that holds it. On devices
   with a vibration motor (Android; iOS ignores navigator.vibrate and loses
   nothing) the book taps back at the moments that already have a voice and a
   colour: a right answer, a wrong one, a ceremony. Three vocabulary items
   only — a grammar, not a drum kit — and all of it under prefers-reduced-
   motion, which is the closest thing the platform has to "please don't". */
const HAPTICS = {
  ok: [12],                     // a nod
  no: [50],                     // a firmer, single "hm"
  fanfare: [15, 60, 15, 60, 40] // the confetti, felt
};
function haptic(kind) {
  try {
    if (!navigator.vibrate) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    navigator.vibrate(HAPTICS[kind] || []);
  } catch (e) { /* a silent motor is never worth an error */ }
}

function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('show'), 2600); }

/* ---------------- speech ----------------
   Everything the book says goes through one queue. Long text is cut into
   sentence-bounded chunks and chained utterance to utterance: the 3,500-
   character ceiling that used to sit here (and again in speakArticle) stopped
   the book mid-clause at roughly 5% of a real article, with no way to resume.

   speakSeq is what makes chaining safe. speechSynthesis.cancel() fires `onend`
   on the utterance it kills, so a naive chain restarts itself the instant it is
   silenced — navigate away mid-read and the book keeps reading the page you
   left. Every stop bumps the sequence, and a chunk that finishes under a stale
   sequence drops the rest of its queue on the floor. */
const SPEAK_CHUNK = 1200;
let speakSeq = 0;
// Whatever the voice leaves lit — a pulsing speaker button, the paragraph it is
// reading, the article's transport row — is only true while it is talking. The
// article read registers its own restorer here so that a stop from anywhere
// (the voice toggle, a navigation, a caption read in the lightbox) puts the
// page back rather than leaving a dead Pause button behind.
let _voiceRestore = null;

// Cut text into pieces no longer than SPEAK_CHUNK, never mid-sentence. A
// boundary inside a clause is exactly what made the old truncation sound like
// a fault rather than an ending.
function splitForSpeech(text) {
  const clean = String(text == null ? '' : text).replace(/\s+/g, ' ').trim();
  if (!clean) return [];
  if (clean.length <= SPEAK_CHUNK) return [clean];
  const sentences = clean.match(/[^.!?\u2026]+(?:[.!?\u2026]+["\')\]]*|$)/g) || [clean];
  const out = [];
  let buf = '';
  for (const s of sentences) {
    let piece = s.trim();
    // One "sentence" longer than a whole chunk — a run-on caption, a list of
    // dates with no full stop in it. Fall back to word boundaries rather than
    // cutting a word in half.
    while (piece.length > SPEAK_CHUNK) {
      let cut = piece.lastIndexOf(' ', SPEAK_CHUNK);
      if (cut < SPEAK_CHUNK * 0.5) cut = SPEAK_CHUNK;
      if (buf) { out.push(buf); buf = ''; }
      out.push(piece.slice(0, cut).trim());
      piece = piece.slice(cut).trim();
    }
    if (!piece) continue;
    if (buf && buf.length + 1 + piece.length > SPEAK_CHUNK) { out.push(buf); buf = piece; }
    else buf = buf ? buf + ' ' + piece : piece;
  }
  if (buf) out.push(buf);
  return out;
}

// The only place an utterance is ever built. `parts` is spoken in order;
// onChunk(i) fires as each one begins and onEnd() once the last has finished —
// and neither fires again once a newer read or a stop has taken the voice.
function speakParts(parts, opts) {
  const o = opts || {};
  stopSpeaking();                       // bumps speakSeq, silences the old queue
  const seq = speakSeq;
  let i = 0;
  const next = () => {
    if (seq !== speakSeq) return;       // superseded: this queue is over
    if (i >= parts.length) { if (o.onEnd) o.onEnd(); return; }
    const k = i++;
    if (o.onChunk) o.onChunk(k);
    try {
      const u = new SpeechSynthesisUtterance(parts[k]);
      u.rate = S.stage <= 1 ? 0.9 : 0.98; u.pitch = 1.04;
      // onerror as well as onend, or one refused chunk ends the whole article.
      u.onend = next; u.onerror = next;
      speechSynthesis.speak(u);
    } catch (e) { if (o.onEnd) o.onEnd(); }
  };
  next();
}
function speakText(text, onEnd) {
  const parts = splitForSpeech(text);
  if (!parts.length) { if (onEnd) onEnd(); return; }
  speakParts(parts, { onEnd: onEnd });
}
function maybeSpeak(text, maxStage = 1) { if (S.speak && S.stage <= maxStage) speakText(text); }
function stopSpeaking() {
  speakSeq++;
  // cancel() on a paused engine leaves Chrome's queue wedged: the next speak()
  // is accepted and never sounds. Clearing the paused flag afterwards, on an
  // empty queue, costs nothing and is what makes Pause → Stop → Read work.
  try { speechSynthesis.cancel(); if (speechSynthesis.paused) speechSynthesis.resume(); } catch (e) {}
  // A queue that is dropped rather than finished never runs its onEnd, so the
  // marks it left have to be cleared from here or they stay lit forever.
  document.querySelectorAll('.speak-btn.speaking').forEach(b => b.classList.remove('speaking'));
  document.querySelectorAll('.reading-now').forEach(b => b.classList.remove('reading-now'));
  if (_voiceRestore) { const put = _voiceRestore; _voiceRestore = null; put(); }
}
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
    // The pulse is added *after* the call: speakText stops whatever was
    // talking first, and stopSpeaking clears every .speaking mark on the page —
    // including, if it were added first, this one.
    onclick: () => { const t = typeof getText === 'function' ? getText() : getText; speakText(t, () => b.classList.remove('speaking')); b.classList.add('speaking'); } }, glyph('speak', 16));
  return b;
}

/* ---------------- routing (hash-based) ---------------- */
function hashFor(view, arg) {
  if (view === 'node') return '#/node/' + encodeURIComponent(arg);
  // The short sitting is a route, not a mode flag, so it survives a reload and
  // can be linked to — a reader who has five minutes on a bus has them again
  // tomorrow.
  if (view === 'review' && arg === 'short') return '#/review/short';
  if (view === 'reader') { const a = typeof arg === 'string' ? { title: arg } : (arg || {});
    return '#/read/' + encodeURIComponent(a.title || '') + (a.node ? '/' + encodeURIComponent(a.node) : ''); }
  return '#/' + view;
}
// 'journey' — the view's real route name, as the sidebar and routes table
// spell it. This list said 'journal' (the API endpoint's name, not the
// view's), so the Journey nav button silently "corrected" itself to Today on
// every click and the view was unreachable by any path.
const KNOWN_VIEWS = new Set(['today', 'atlas', 'review', 'library-search', 'story',
                             'journey', 'roadmap', 'library', 'node', 'read', 'reader', 'account']);
function parseHash() {
  const h = (location.hash || '#/today').replace(/^#\/?/, '');
  const parts = h.split('/').map(decodeURIComponent);
  const view = parts[0] || 'today';
  if (view === 'node') return { view, arg: parts[1] };
  if (view === 'review') return { view, arg: parts[1] === 'short' ? 'short' : null };
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
  // And silence the voice. Read-aloud can now run for the length of a whole
  // article, so leaving the page mid-read used to mean the book carried on
  // reading a page that no longer existed, marking paragraphs in a detached
  // DOM. Views that speak on arrival do so after this, from their own render.
  stopSpeaking();
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
  const routes = { today: renderToday, atlas: renderAtlas, review: renderReview, 'library-search': renderSearch, roadmap: renderRoadmap, library: renderLibrary, journey: renderJourney, story: renderStory, node: renderNode, reader: renderReader, account: renderAccount };
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
    // The one surface that never turned a page. A reader eight thousand words
    // into an article, or three questions into a quiz, saw the same masthead in
    // the tab as on the day they opened the book; with two copies open they had
    // no way to tell them apart. The heading the view already computed for the
    // accessible name is exactly the right words, so it does both jobs.
    setTitle(h ? h.textContent : null);
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
const TITLE_ROOT = 'The Primer';
function setTitle(leaf) {
  const t = (leaf || '').trim();
  document.title = t && t !== TITLE_ROOT ? t + ' · ' + TITLE_ROOT
                                         : TITLE_ROOT + ' — A Living Book of All Knowledge';
}

/* ---------------- the world coming and going ----------------
   The book's whole premise is that it works with no wire at all, and until now
   it never once said so: every disconnection was discovered by a failed
   request and reported as a generic apology, which reads like a fault. Losing
   the network is not a fault in this artifact. It is a condition, and the book
   should be the one to mention it first — calmly, and without implying the
   reader has lost anything, because they have not. */
function offlineBand() {
  let band = $('#offline-band');
  if (navigator.onLine) { if (band) band.remove(); return; }
  if (band) return;
  // Mounted empty and filled after it has landed — the same rule every other
  // live region in this file obeys: a role="status" node inserted with its
  // text already inside it is announced unreliably, or not at all.
  band = el('div', { id: 'offline-band', class: 'offline-band', role: 'status' });
  // Mounted into the shell rather than the page, so a route change does not
  // take it down while it is still true.
  const book = $('#book') || $('#root');
  if (!book) return;
  book.prepend(band);
  setTimeout(() => band.append(glyph('shelf', 14),
    ' The book is on its own for a while — no wire, no signal. Everything already bound in is still here, and it will reach out again when the world comes back.'), 30);
}
window.addEventListener('offline', () => { offlineBand(); });
// And once on arrival: opening the book already off the wire is the commonest
// case of all, and it fires no event. This early tick alone was not enough —
// renderShell() rebuilds #root wholesale, so a band mounted before the shell
// existed was thrown away with the spinner it stood beside; renderShell now
// re-checks after every rebuild (see its tail), and this tick covers pages
// that never build a shell at all, like onboarding.
window.addEventListener('DOMContentLoaded', () => setTimeout(offlineBand, 400));
window.addEventListener('online', () => { offlineBand(); toast('The world is back. The book will fetch what it was missing.'); });

/* ---------------- the reader's place ----------------
   The article view is the only page a reader can be eight thousand words into,
   and every route change rebuilds #page from nothing. Following a link and
   coming back therefore landed them at character zero of a page they had
   already read half of — the cost of curiosity, charged every time.

   Two details this has to get right. First, the window is the scroller on this
   layout (#page carries no overflow of its own and #sidebar is sticky at
   100vh), so `page.scrollTop` is a no-op here: the offset has to be taken from
   and given back to the document. Second, the place is recorded continuously
   rather than at the moment of leaving — the theme toggle rebuilds #page with
   no navigation at all, and that collapses the document and takes the scroll
   offset with it before any teardown hook could read it. */
const readerScroll = new Map();
function docScrollTop() { return window.scrollY || document.documentElement.scrollTop || 0; }
window.addEventListener('scroll', () => {
  if (S.view !== 'reader' || !S.readerTitle) return;
  readerScroll.set(S.readerTitle, docScrollTop());
}, { passive: true });

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

// Webkit will not expose a filled-track pseudo, so the fill is painted by a
// CSS variable the input keeps in sync with its own value. Shared by every
// range slider in the app, not only onboarding's.
function syncRangeFill(input) {
  const min = +input.min || 0, max = +input.max || 100, v = +input.value;
  input.style.setProperty('--range-fill', (100 * (v - min) / (max - min)) + '%');
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
function speakBtnAlways(getText) { const b = btn({ class: 'speak-btn', 'aria-label': 'Read aloud', onclick: () => { speakText(typeof getText === 'function' ? getText() : getText, () => b.classList.remove('speaking')); b.classList.add('speaking'); } }, glyph('speak', 16)); return b; }

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
      'FINDING YOUR LEVEL · ' + domainById(domain).name + ' · ' + STAGE_NAMES[stage] +
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
    /* This is, for most readers over six, the FIRST thing the book ever does
       with them — it fires 700ms after onboarding. It used to end on ★☆☆ and
       "This level is still ahead of you", which makes the opening beat of the
       whole product a failure verdict on a check the reader cannot fail.
       A placement is a measurement, not a performance, and a star rating is
       the wrong instrument for it: three stars for landing high implies one
       star for landing low, and where a reader starts is not an achievement.
       The mark is a compass now, and both outcomes are the same good news
       said twice — the book knows where to open. */
    splash.append(el('div', { class: 'stars', style: 'color:var(--gold)' }, glyph('atlas', 38)),
      el('p', {}, r.passed
        ? 'You are comfortable at ' + STAGE_NAMES[stage] + ' level in ' + domainById(domain).name + '. That is worth knowing, and now the book knows it.'
        : 'The book has found where to open in ' + domainById(domain).name + ' — a little below ' + STAGE_NAMES[stage] + ', so the ground is solid under you. Nothing here was a check you could fail.'));
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
    // "XP" is a two-letter acronym off an arcade cabinet, pinned over the page
    // of a three-year-old who cannot read it and a graduate who should not have
    // to. The mechanic underneath is Kim's and Okafor's and is untouched: only
    // the word the reader sees changes, to one the rest of this book would use.
    // Growth, because the ladder the reader climbs is Seedling to Forest.
    el('div', { class: 'stat' }, el('span', {}, 'Growth'), el('b', { id: 'stat-xp' }, p.xp || 0)),
    el('div', { class: 'stat' }, el('span', {}, 'Streak'), el('b', { id: 'stat-streak' }, String(p.streak || 0), glyph('flame', 13))),
  ));
  sidebar.append(el('div', { class: 'chrome-row', role: 'group', 'aria-label': 'Reading settings' },
    speakToggle(),
    themeToggle(),
    accountToggle(),
  ));
  book.append(sidebar, el('main', { id: 'page' }));
  const skip = btn({ class: 'skip-link', onclick: () => { const m = $('#page'); if (m) { m.setAttribute('tabindex', '-1'); m.focus(); } } }, 'Skip to content');
  $('#root').append(skip, book);
  // The shell was just rebuilt from nothing; if the world is still away, the
  // band must come back with it — this is the only path that can restore it
  // for a reader who opened the book already offline.
  offlineBand();
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
function accountToggle() {
  return btn({ id: 'account-toggle', class: 'chrome-toggle',
    'aria-label': 'Account — sign in with Google and set your level by subject',
    'aria-current': S.view === 'account' ? 'page' : null,
    onclick: () => go('account') },
    el('span', { class: 'tt-icon', 'aria-hidden': 'true' }, glyph('account', 15)),
    el('span', { class: 'tt-label' }, 'Account'));
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
// A reader who cannot see the lines fill in hears that node instead, so it
// speaks in the book's voice and names what is coming: "Loading" told them
// neither. Callers that know the subject pass it; the rest get the page.
function skeleton(lines, subject) {
  const box = el('div', {
    class: 'book-skeleton', role: 'status',
    'aria-label': 'The book is writing ' + (subject || 'this page') + '…'
  });
  const widths = ['62%', '96%', '88%', '94%', '71%'];
  for (let i = 0; i < (lines || 5); i++) {
    box.append(el('i', { class: i === 0 ? 'sk-head' : '', style: 'width:' + widths[i % widths.length] }));
  }
  return box;
}
function loading(page, subject) { page.append(skeleton(5, subject)); }
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
// What the book says about its own refusals. Round 5 demoted the backend
// string to fine print, which kept the DON'T PANIC lede intact but still put
// "no such node" — and, on any non-JSON failure, "Internal Server Error" —
// on the page in the reader's own hands. A machine tag is not fine print; it
// is a different book. So the front end keeps the book's half of the
// vocabulary, and anything it does not recognise is said in the book's words
// instead of the server's. The diagnosis is not lost: it goes to the console.
const SAID = {
  'no such node': 'That lesson is not among these pages.',
  'not found': 'That page is not on the shelf.',
  'unknown catalog key': 'That volume is not in the book\u2019s catalogue.',
  'unknown quiz token': 'That paper has been set aside — ask for a fresh one.',
  'unknown generator': 'That drill is not one the book knows how to set.',
};
function saidFor(e) {
  const tag = e && typeof e.error === 'string' ? e.error.toLowerCase() : '';
  if (!tag) return '';
  // Recognised or not said at all. A rule that tried to *infer* whether a
  // string was in voice — long enough, has a verb — would let the next
  // untranslated tag through, and a JS exception message already arrives here
  // by one path (the boot fallback below passes e.message). An allowlist
  // cannot be surprised.
  return SAID[tag] || '';
}
function errCard(e, retry) {
  // The lede leads, and the second line is the book explaining itself in its
  // own words or saying nothing at all.
  if (e && e.error) console.warn('[primer]', e.error);
  // "Likely the network, never you" is a kind guess. When the book can see for
  // itself that there is no network, it should stop guessing and say so — and
  // say the thing that matters, which is that nothing is out of reach that was
  // ever really in hand.
  const said = saidFor(e) || (navigator.onLine ? '' :
    'The book is on its own just now — no wire, no signal. Everything already bound in is still yours to read.');
  const c = el('div', { class: 'card err-card', role: 'alert' },
    el('div', { class: 'dont-panic', 'aria-hidden': 'true' }, 'DON’T PANIC'),
    el('p', { class: 'err-lede' }, said || 'The Book has briefly lost its train of thought — likely the network, never you.'),
    el('p', { class: 'muted err-note' }, 'Everything you have learned is safely written down.'));
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

/* ---------------- appointments ----------------
   The engine makes dated appointments with the reader: a lesson proved once
   cannot be sealed until a spaced window has elapsed, and the deck names the
   next moment it has anything to say. Every one of those arrives here as a
   UNIX timestamp from a server that is not in the reader's timezone, so the
   two rules below hold everywhere one is printed.

   Format through toLocale*, never by hand. And an appointment that has come
   round is not one that was missed: the book says "ready now", never "ready
   yesterday", because a reader who arrives late has lost nothing at all. */
// "about 1 minutes" is the sort of sentence that tells a reader a machine
// wrote the page. One helper, used everywhere a count meets a noun.
function plural(n, word) { return n + ' ' + word + (Math.abs(n) === 1 ? '' : 's'); }
function readyNow(ts) { return ts == null || ts * 1000 <= Date.now(); }
function dayStart(d) { const x = new Date(d); x.setHours(0, 0, 0, 0); return x; }
// Only time components, so toLocaleString renders the clock alone — and the
// reader's own clock, twelve- or twenty-four-hour as their locale has it.
function clockTime(d) { return d.toLocaleString(undefined, { hour: 'numeric', minute: '2-digit' }); }
// A moment, to the minute: this is a gate opening, and the minute is the point.
function whenReady(ts) {
  const d = new Date(ts * 1000);
  const days = Math.round((dayStart(d) - dayStart(new Date())) / 86400000);
  if (days <= 0) return 'today at ' + clockTime(d);
  if (days === 1) return 'tomorrow at ' + clockTime(d);
  if (days < 7) return d.toLocaleDateString(undefined, { weekday: 'long' }) + ' at ' + clockTime(d);
  return d.toLocaleDateString(undefined, { month: 'long', day: 'numeric' });
}
// A day, loosely: for a deck that refills overnight the hour is noise.
function whenDay(ts) {
  const d = new Date(ts * 1000);
  const days = Math.round((dayStart(d) - dayStart(new Date())) / 86400000);
  if (days <= 0) return 'later today';
  if (days === 1) return 'tomorrow';
  if (days < 7) return 'on ' + d.toLocaleDateString(undefined, { weekday: 'long' });
  return 'on ' + d.toLocaleDateString(undefined, { month: 'long', day: 'numeric' });
}

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

// A day should end with a tomorrow — but only a truthful one. Every clause is
// assembled from data that actually exists and a clause with nothing behind it
// is not written at all, so a reader on their very first evening never meets
// "Tomorrow: , , and this becomes a 1-day streak". Everything named here is
// something WAITING; nothing here is a thing lost by not coming back, because
// a book that bills the reader for their absence is not one they reopen.
function tomorrowLine(tm) {
  if (!tm) return '';
  const parts = [];
  if (tm.due_tomorrow > 0) {
    parts.push(tm.due_tomorrow === 1 ? 'one card comes back'
      : tm.due_tomorrow + ' cards come back');
  }
  if (tm.next_ready != null) {
    // Bounded by the end of tomorrow at source, so it is either later today or
    // tomorrow — and it may already have elapsed, because pending_proofs never
    // nulls a past appointment and neither does this. Elapsed means READY, and
    // the clock is dropped rather than printed as a date that has gone by.
    const d = new Date(tm.next_ready * 1000);
    parts.push(readyNow(tm.next_ready) ? 'a lesson is ready to be sealed'
      : dayStart(d) <= dayStart(new Date())
        ? 'a lesson can be sealed later today, from ' + clockTime(d)
        : 'a lesson can be sealed from ' + clockTime(d));
  }
  const streak = tm.streak_next | 0;
  if (streak >= 2) {
    // "This becomes a 1-day streak" is not news; a milestone one day out is.
    const ms = tm.milestone;
    parts.push(ms && ms.away === 1
      ? 'this becomes a ' + streak + '-day streak — your ' + ms.days + '-day mark'
      : 'this becomes a ' + streak + '-day streak');
  }
  let out = '';
  if (parts.length) {
    const last = parts.pop();
    out = 'Tomorrow: ' + (parts.length ? parts.join(', ') + ', and ' + last : last) + '.';
  }
  // A deck whose next card falls further out than tomorrow is still something
  // waiting — it simply is not waiting TOMORROW, and filing it under a
  // "Tomorrow:" lead would be the exact kind of untruth this line exists to
  // avoid. It gets a sentence of its own, or it gets none.
  if (!(tm.due_tomorrow > 0) && tm.next_due != null) {
    out += (out ? ' ' : '') + 'The deck opens again ' + whenDay(tm.next_due) + '.';
  }
  return out;
}

// The reader who was gone is welcomed by what still stands, never by what was
// lost. No broken streak, no "don't let it slip again", no urging of any kind:
// this is a children's book, the reader may be five, and a book that scolds is
// a book that is not opened again. Every clause is strictly backward-looking —
// how long, what is still theirs, where the place was kept — and a clause with
// no data behind it is simply not written.
function returnCard(a) {
  const lines = ['You have been away ' + a.days_away + ' days, and I kept your place.'];
  if (a.standing) lines.push(a.standing === 1
    ? 'One topic you proved still stands, exactly as you left it.'
    : a.standing + ' topics you proved still stand, exactly as you left them.');
  if (a.chapter_title) lines.push('Your chapter is waiting at “' + a.chapter_title + '”.');
  if (a.best_streak >= 2) lines.push('Your longest run was ' + a.best_streak + ' days — that record is yours whatever happens next.');
  const text = lines.join(' ');
  const card = el('div', { class: 'card return-card' },
    el('div', { class: 'kicker' }, glyph('story', 15), ' The book kept your place'),
    el('p', { class: 'return-text' }, text));
  if (a.last_seen) card.append(el('p', { class: 'muted return-when' },
    'You were last here on ' + new Date(a.last_seen * 1000).toLocaleDateString(undefined,
      { weekday: 'long', month: 'long', day: 'numeric' }) + '.'));
  if (S.stage <= 1) card.append(el('div', { class: 'return-speak' }, speakBtn(() => text, 'Read this aloud')));
  return card;
}

async function renderToday(page) {
  const t = await guard(page, () => api.get('/api/today'));
  if (!t) return;
  const p = t.profile;
  const hour = new Date().getHours();
  const greet = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  // The book kept the reader's place. `absence` is null whenever there is
  // nothing honest to say — a first afternoon, or a gap older than the events
  // log can vouch for — and a day or two away is not an absence at all.
  const away = t.absence && t.absence.days_away >= 3 ? t.absence : null;
  // Once per return, not on every load for a week: the same sessionStorage
  // guard the milestone ceremony uses, keyed on the reader's own local date.
  const returnKey = 'return-' + new Date().toLocaleDateString('en-CA');
  const welcome = !!away && !sessionStorage.getItem(returnKey);
  if (welcome) sessionStorage.setItem(returnKey, '1');
  page.append(pagehead(welcome ? 'Welcome back, ' + p.name : greet + ', ' + p.name, "Today's Reading",
    p.stage_name + ' — ' + p.stage_span + '. ' + (t.mastered ? t.mastered + ' topics mastered so far.' : 'Your journey begins now.')));
  if (welcome) page.append(returnCard(away));
  page.append(pronounLine());

  // Daily quest checklist
  const quest = el('div', { class: 'quest', role: 'group', 'aria-label': "Today's quest" });
  Object.entries(t.quest).forEach(([qkey, q]) => {
    q.key = qkey;
    // A count that fills, not a checkbox that flips. `goal` is what the day
    // asks for and `done_count` how much of it is behind the reader, so the
    // widget meant to represent the day's work stops hiding it: a reader who
    // reviewed 1 of 40 cards was being shown a completed tile and a crown.
    //
    // An excused step keeps the hint it always had. The book already explains
    // an empty deck ("Deck is clear — nothing due", or how to start one), and
    // rendering that step as "0 of 0" would read like a broken counter rather
    // than the good news it is, on exactly the days a new reader most needs
    // encouraging.
    //
    // `excused` is the server's word and only the server's: a step can have a
    // goal of zero and still be DONE (the reader learned the last lesson on the
    // frontier this morning), and drawing that as "nothing waiting" would take
    // the day's work back off them. Read the flag, never re-derive it.
    const goal = q.goal | 0;
    const dc = Math.min(q.done_count | 0, goal);
    const counted = !q.excused && goal > 0;
    const status = q.excused ? (q.hint || 'nothing waiting today')
      : counted ? dc + ' of ' + goal
      : q.done ? 'done' : 'today';
    // What this step costs, in minutes. The book had never told a reader what
    // it was asking of them — not for a card, not for a quiz, not for the
    // evening — which makes every ask an open-ended one, and an open-ended ask
    // is the easiest thing in the world to put off. Server-priced (see the
    // pace block in /api/today) so the tile and the deck quote one number.
    const mins = (t.pace && t.pace.steps && t.pace.steps[q.key]) || 0;
    const item = el('div', { class: 'quest-item' + (q.done ? ' done' : q.excused ? ' excused' : '') },
      el('span', { class: 'tick', 'aria-hidden': 'true' }, q.done ? '✓' : q.excused ? '—' : '✓'),
      el('span', { class: 'qt' }, el('b', {}, q.label), status
        + (mins ? ' · about ' + mins + ' min' : '')));
    if (counted) {
      // The same role="img" + aria-label pattern the mastery bars use: a bar
      // that is aria-hidden says "58%" only to people who can see it.
      item.append(el('div', { class: 'bar quest-bar', role: 'img',
        'aria-label': q.label + ': ' + dc + ' of ' + goal + ' done' },
        el('span', { style: `width:${Math.round(100 * dc / goal)}%` })));
    }
    quest.append(item);
  });
  page.append(quest);
  // The evening's whole cost, said once, plus the smallest door into it.
  // "Minimum effective dose" is a real idea and it needs a real control: a
  // reader with five minutes previously had to either take on the entire day
  // or take on nothing, and between those two the honest answer is nothing.
  if (t.pace && t.quest_done !== t.quest_total) {
    const row = el('div', { class: 'pace-row' });
    if (t.pace.minutes_left) {
      row.append(el('span', { class: 'pace-total' },
        glyph('target', 14), ' Tonight asks about ' + plural(t.pace.minutes_left, 'minute') + ' of you.'));
    }
    // Offering a smaller door when the room is already small is noise, and
    // "the rest keep" is a promise about cards that do not exist. The short
    // sitting appears only when it is genuinely shorter than the day.
    if (t.pace.short_minutes && t.pace.minutes_left > t.pace.short_minutes) {
      row.append(btn({ class: 'btn ghost small', onclick: () => {
        if (t.pace.short_kind === 'review') go('review', 'short');
        else if (t.lessons && t.lessons.length) go('node', t.lessons[0].id);
        else go('review', 'short');
      } }, 'I only have a few minutes'));
      row.append(el('span', { class: 'muted pace-note' },
        t.pace.short_kind === 'review'
          ? plural(t.pace.short_cards, 'card') + ', about ' + plural(t.pace.short_minutes, 'minute') + '.'
            + (t.pace.short_cards < (t.deck && t.deck.due || 0) ? ' The rest keep.' : '')
          : 'One lesson quiz, about ' + plural(t.pace.short_minutes, 'minute') + '.'));
    }
    // The book says which kind of number it just gave. An estimate presented
    // as a measurement is the sort of small lie this file has twice had to
    // back out of; it costs one clause to be straight about it.
    row.append(el('span', { class: 'muted pace-note' }, t.pace.measured
      ? 'Timed from how long these usually take you.'
      : t.pace.partly
        ? 'Partly timed from your own sittings — the rest the book still estimates.'
        : 'A first estimate — the book will time you and correct itself.'));
    page.append(row);
  }
  if (t.quest_done === t.quest_total) {
    page.append(el('div', { class: 'quest-crown' }, glyph('crown', 17), ' Today\'s quest complete — ' + t.xp_today + ' growth today. Beautifully done.'));
    // The crown used to end in a full stop. A day should have a tomorrow.
    const tl = tomorrowLine(t.tomorrow);
    if (tl) page.append(el('p', { class: 'tomorrow-line' }, tl));
  }
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

  // The appointments that did not fit today's page. Named rather than dropped:
  // the cap on resumed lessons protects the shape of the day, and it should not
  // also cost the reader the knowledge that the work is there and still theirs.
  if (t.pending && t.pending.length) {
    page.append(sectionLabel('Waiting to be proved'));
    const pr = el('div', { class: 'refresh-row' });
    t.pending.forEach(w => pr.append(btn({ class: 'req-chip pending-chip', onclick: () => go('node', w.id) },
      '◐ ' + w.title + ' · ' + (readyNow(w.ready_at) ? 'ready now' : 'ready ' + whenReady(w.ready_at)))));
    page.append(pr);
  }

  // Refresh chips (deck-driven mastery decay)
  if (t.refresh && t.refresh.length) {
    page.append(sectionLabel('Worth refreshing'));
    const rr = el('div', { class: 'refresh-row' });
    t.refresh.forEach(r => rr.append(btn({ class: 'req-chip', onclick: () => go('node', r.id) }, '↻ ' + r.title)));
    page.append(rr);
  }

  const row = el('div', { class: 'grid two', style: 'margin-top:20px' });
  row.append(
    actionCard([glyph('review', 17), ' Review'],
      t.deck.due ? t.deck.due + ' cards ready to strengthen your memory.'
        // Not a dead end: an empty deck has a next moment, and the book knows it.
        : t.deck.next_due != null ? 'Every card is filed. The next one comes back ' + whenDay(t.deck.next_due) + '.'
        : 'No cards due. Master lessons to build your deck.', () => go('review'),
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
  // A lesson standing one earned pass short of mastery already has a dated
  // appointment, and until now the book never mentioned it — leaving the
  // reader's own open loop a coin flip to reappear. Only a resumed lesson
  // carries these keys; a fresh one has none of them at all.
  if (n.resume) {
    c.classList.add('resume');
    const ready = readyNow(n.ready_at);
    const passes = n.passes | 0;
    c.append(el('p', { class: 'resume-note' + (ready ? ' ready' : '') },
      el('b', {}, 'You started this one'),
      passes > 1 ? 'Proved ' + passes + ' times. ' : 'Proved once. ',
      ready ? 'Ready to seal now ✦' : 'It can be sealed after ' + whenReady(n.ready_at) + '.'));
  }
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

// Page turns inside the last minute. Held at module scope so it survives the
// modal being closed and reopened, which is exactly how the spam happens.
let _pageTurns = [];
function pageTurnIsCheap() {
  const now = Date.now();
  _pageTurns = _pageTurns.filter(ts => now - ts < 60000);
  _pageTurns.push(now);
  return _pageTurns.length > 3;
}
function openStory(s, canAdvance, needs, onClose) {
  openModal({
    label: s.title, dismissable: true, dark: true, onClose: onClose || null,
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
            if (r.advanced) {
              // A reader placed into the middle of the curriculum can have a
              // dozen chapters standing open at once, and an identical confetti
              // storm paid out a dozen times in two minutes teaches the hand
              // that gold is a spam key. Above three page turns in a minute the
              // XP is still granted and still said out loud; only the animation
              // stops repeating, so the ceremony keeps meaning something.
              const cheap = pageTurnIsCheap();
              if (!cheap) { confetti(); if (r.xp_gained) flyXP(r.xp_gained); }
              toast('The next chapter has opened ✦'
                + (cheap && r.xp_gained ? ' +' + r.xp_gained + ' growth' : ''));
            }
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
function renderLessonMedia(items) {
  if (!Array.isArray(items) || !items.length) return null;
  const media = el('div', { class: 'lesson-media' });
  items.forEach(item => {
    if (item && item.kind === 'illustration') {
      if (!item.src || !item.alt) return;
      const image = el('img', {
        src: item.src,
        srcset: item.srcset || null,
        sizes: item.srcset ? '(max-width: 720px) calc(100vw - 36px), 960px' : null,
        alt: item.alt,
        width: item.width || 1600,
        height: item.height || 1000,
        loading: 'eager',
        decoding: 'async',
        fetchpriority: 'high',
      });
      const figure = el('figure', { class: 'card lesson-illustration' }, image);
      if (item.caption) figure.append(el('figcaption', {}, item.caption));
      media.append(figure);
      return;
    }
    if (item.kind === 'model' && window.PrimerLessonModels) {
      const model = window.PrimerLessonModels.render(item, {
        speakButton: S.stage <= 2 ? (getText, label) => speakBtn(getText, label) : null,
      });
      if (model) media.append(model);
    }
  });
  return media.childElementCount ? media : null;
}

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
  // A lesson with one earned pass has mastered_at still NULL, so none of the
  // three branches above are true and this page used to say nothing whatever
  // about the most time-sensitive fact the book holds: that this lesson has an
  // appointment. `faded`/`ever_proven` are excluded deliberately — a lapsed
  // node's lifetime pass count is stale evidence, and reading it back as
  // progress toward a seal would promise a gate that has re-shut.
  else if (n.mastery_detail && !n.faded && !n.ever_proven
           && (n.mastery_detail.passes | 0) >= 1
           && (n.mastery_detail.passes | 0) < ((n.opens_chapter && n.passes_needed) || n.mastery_detail.passes_needed || 2)) {
    const md = n.mastery_detail;
    const need = (n.opens_chapter && n.passes_needed) || md.passes_needed || 2;
    // mastery_detail nulls ready_at once it has elapsed, which means ready NOW.
    const ready = readyNow(md.ready_at);
    page.append(el('div', { class: 'card', style: 'border-color:var(--gold)' },
      el('b', {}, '◐ You started this one — ' + md.passes + ' of ' + need + ' passes'),
      el('p', { class: 'muted', style: 'margin:6px 0 0' }, ready
        ? 'The waiting is over: pass it once more and it is sealed.'
        : 'The two passes have to sit a little apart, so the book can tell it stuck. This one can be sealed after ' + whenReady(md.ready_at) + '.')));
  }

  // Child-voiced mini-lesson for the youngest readers.
  if (n.kid_text && S.stage <= 1) {
    const kt = el('div', { class: 'card', style: 'font-size:19px;line-height:1.7' },
      el('div', { class: 'speak-row' }, speakBtn(() => n.kid_text, 'Read the lesson aloud'), el('b', { style: 'font-family:var(--sans);font-size:13px;color:var(--gold-ink)' }, 'THE BOOK SAYS')),
      el('div', {}, n.kid_text));
    page.append(kt);
    maybeSpeak(n.kid_text);
  }

  const lessonMedia = renderLessonMedia(n.lesson_media);
  if (lessonMedia) {
    page.append(sectionLabel(S.stage <= 1 ? 'Try it' : 'Explore the idea'), lessonMedia);
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
  // Why the quiz is dead used to live in a native `title=` on a *disabled*
  // button — which most browsers refuse to show at all, and no touch device
  // has ever shown. The only explanation the reader could get was one they
  // could not get. It is a sentence on the page now, in the book's hand.
  const actions = el('div', { style: 'display:flex;gap:12px;flex-wrap:wrap;margin-top:26px' },
    btn({ class: 'btn gold', disabled: canAssess ? null : '',
      onclick: canAssess ? () => startQuiz(nodeId) : null }, glyph('quill', 16), ' Take the quiz'),
    n.practice ? btn({ class: 'btn', disabled: canAssess ? null : '',
      onclick: canAssess ? () => startPractice(nodeId, n.practice, n.stage) : null }, glyph('target', 16), ' Practice') : null,
    n.articles && n.articles.length ? btn({ class: 'btn ghost', onclick: () => go('reader', { title: n.articles[0], node: nodeId }) }, glyph('story', 16), ' Start reading') : null);
  page.append(actions);
  if (!canAssess) page.append(el('p', { class: 'muted locked-why', style: 'margin-top:10px' },
    glyph('lock', 14), ' Questions wait until this lesson is open to you. You are welcome to read it meanwhile — the book will not set questions on what it has not yet taught you.'));
}

/* ---------------- Reader + tutor ---------------- */
async function renderReader(page, arg) {
  const title = typeof arg === 'string' ? arg : arg.title;
  const nodeId = typeof arg === 'object' ? arg.node : null;
  // Claim the scroll memory for this article before the first scroll event can
  // fire, or the outgoing article's remembered place is overwritten with this
  // one's — which is precisely the case the memory exists to serve.
  S.readerTitle = title;
  // And READ the remembered place in the same breath, because claiming the
  // title is only half the job. renderRoute has just emptied #page, so the
  // document has collapsed to a toolbar, a skeleton and the tutor panel; the
  // browser clamps the scroll offset to whatever that short page allows and
  // fires a scroll event for it — after this function has returned to its
  // first await, and therefore against THIS article's slot. Reading the value
  // after the fetch read that clamp back: a never-visited article opened 533px
  // down its own page, and returning to one genuinely remembered at 1212 landed
  // at 533 and overwrote the 1212 with it. Measured in the browser, both.
  // Captured here, nothing between the claim and the read can fire.
  const wantScroll = readerScroll.get(title) || 0;
  // "Check yourself" stood here for articles with no curriculum node. It was
  // machine-made cloze over raw article prose, hand-audited at 55% defective,
  // and is withdrawn: the book does not ask questions no person wrote. Read
  // aloud and the tutor already cover "check what I just read".
  const bar = el('div', { style: 'display:flex;gap:10px;align-items:center;margin-bottom:14px;flex-wrap:wrap' },
    btn({ class: 'btn ghost small', onclick: () => history.length > 1 ? history.back() : go(nodeId ? 'node' : 'today', nodeId) }, '← Back'),
    nodeId ? btn({ class: 'btn gold small', onclick: () => startQuiz(nodeId) }, glyph('quill', 14), ' Quiz me on this') : null,
    readAloudControls());
  page.append(bar);
  const layout = el('div', { id: 'reader-layout' });
  const art = el('article', { id: 'article', tabindex: '-1' }); art.append(skeleton(7, title));
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
    attachPictureHandlers(art);
    // Where the page came from, said as a book says it. "(live)" is a word
    // about wires; "copied in from Wikipedia as you turned to it" is the same
    // fact, keeps the attribution Wikipedia is owed, and is a sentence.
    const badge = a.source === 'zim' ? 'from your shelf' : a.source === 'cache' ? 'from your library' : 'copied in from Wikipedia as you turned to it';
    // .reader-source: the book's own footnote about where the page came from,
    // not a sentence of the article. articleBlocks skips it, so read-aloud does
    // not end a twenty-minute reading with "from your shelf".
    art.append(el('p', { class: 'muted reader-source', style: 'margin-top:30px;border-top:1px solid var(--rule);padding-top:10px' }, '✦ ' + badge + (a.simple ? ' · Simple English' : '')));
    // Back to where the eye was, once the article has been laid out. This is
    // safe to do in a single frame because fix_img stamps an intrinsic width
    // and height on every image (render.py), so nothing reflows underneath the
    // reader afterwards. `wantScroll` was read at the top of this function, not
    // here — see the note there; by now the slot holds a layout artefact rather
    // than a place anybody read to. A first visit wants 0, which is the right
    // answer: the top of an article nobody has opened before.
    const want = wantScroll;
    requestAnimationFrame(() => {
      const max = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
      window.scrollTo(0, Math.min(want, max));
    });
  } catch (e) { art.innerHTML = ''; art.append(errCard(e, () => renderReader(page, arg))); }
}
/* ---------------- articleBlocks(): what the article actually says ----------------
   SHARED HELPER. Written here for read-aloud; its second caller is the tutor's
   section-grounding, which has to agree with read-aloud about what "the
   article" is or the panel answers about text the reader was never shown.

   CONTRACT
     articleBlocks(root)  ->  [{ el: Element, text: string }, ...]

       root    optional Element to read. Defaults to #article; if that is not
               on the page the result is [] — never null, never a throw.
       order   document order.
       el      the live element, so a caller may mark it (read-aloud toggles
               .reading-now on it), measure it against the viewport, or scroll
               to it.
       text    its innerText: whitespace collapsed, citation markers removed,
               trimmed. Never the empty string — empty blocks are dropped, so
               `.length` is a true count of how much there is to read.

   WHAT COUNTS AS A BLOCK — h1, h2, h3, p, li: the tags render.py's allowlist
   leaves running prose in. h1 is the article's own title, which is the right
   first thing to say aloud.

   WHAT IS DROPPED, and why each one earns its place:
     - innerText, never textContent. textContent ignores CSS, which is why the
       old read-aloud spoke everything the rules at styles.css:490 hide.
     - offsetParent === null: anything not rendered at all, the inside of a
       folded navbox included.
     - Navigation dressed as prose — the infobox, the topic sidebar, the footer
       navboxes, the contents list. This is the ninety seconds of the Classical
       mechanics sidebar that used to come before the first sentence.
     - Banners addressed to editors rather than readers: "History of art" opened
       by announcing "This article may be too long to read and navigate
       comfortably".
     - Citation apparatus: the reference list, and the [17] markers inside a
       sentence, which are read out as bare numbers mid-clause.
     - Tables. _wrap_tables puts every one inside .table-scroll, and a table
       read as a flat stream of cells is noise to both callers.
     - A block containing another block (li > p, nested lists) is kept whole and
       its descendants dropped, so no sentence is delivered twice. */
const ARTICLE_BLOCK_TAGS = 'h1, h2, h3, p, li';
const ARTICLE_SKIP = [
  '.navbar', '.mw-editsection', '.mw-empty-elt', '.mw-jump-link',
  '.infobox', '.sidebar', '.vertical-navbox', '.navbox', '.toc', '#toc', '.gallery',
  '.ambox', '.mbox', '.ombox', '.tmbox', '.metadata', '.noprint', '.hatnote',
  '.reflist', '.refbegin', '.mw-references-columns', '.citation-comment', 'ol.references',
  'table', '.table-scroll', 'details.primer-navbox',
  '.reader-source',   // the book's own "from your shelf" footer, not the article
].join(',');
const CITATION_MARK = /\[\s*(?:\d+|[a-z]|note \d+|citation needed|edit|clarify|who\?|when\?)\s*\]/gi;
function articleBlocks(root) {
  const host = root || $('#article');
  if (!host) return [];
  const out = [];
  let kept = null;   // candidates arrive in document order, so an ancestor is
                     // always the most recently kept element
  host.querySelectorAll(ARTICLE_BLOCK_TAGS).forEach(e => {
    if (kept && kept.contains(e)) return;
    if (e.closest(ARTICLE_SKIP)) return;
    if (e.offsetParent === null) return;
    const text = String(e.innerText || '').replace(CITATION_MARK, '').replace(/\s+/g, ' ').trim();
    if (!text) return;
    kept = e;
    out.push({ el: e, text: text });
  });
  return out;
}

/* Blocks in, utterances out: about SPEAK_CHUNK characters each, never cut
   mid-sentence, each carrying the elements it is reading so the page can mark
   them. Short blocks merge so a bulleted list is not forty separate utterances
   with a pause between each. */
function speechChunks(blocks) {
  const out = [];
  let cur = null;
  const flush = () => { if (cur) out.push(cur); cur = null; };
  for (const b of blocks) {
    const pieces = splitForSpeech(b.text);
    if (!pieces.length) continue;
    if (pieces.length > 1) {   // one block longer than a chunk, split on its own
      flush();
      pieces.forEach(t => out.push({ text: t, els: [b.el] }));
      continue;
    }
    const t = pieces[0];
    if (cur && cur.text.length + 2 + t.length <= SPEAK_CHUNK) {
      // A heading runs straight into the paragraph beneath it unless the join
      // closes the clause: "Early life. In 1879…", not "Early life In 1879…".
      cur.text += (/[.!?…:;,]$/.test(cur.text) ? ' ' : '. ') + t;
      cur.els.push(b.el);
    } else { flush(); cur = { text: t, els: [b.el] }; }
  }
  flush();
  return out;
}

/* ---------------- read-aloud that reads the article ----------------
   What this was: speakText($('#article').textContent.slice(0, 3500)) —
   truncated once here and again inside the utterance. textContent ignores CSS,
   so the book read every maintenance banner, every navbox and the whole topic
   sidebar before reaching the first sentence, then stopped mid-clause at
   character 3,500 (about 5% of a real article) with no way to resume.

   For a reader at stage 0-1 this control is not a convenience, it is the only
   route into the page, so it is now a transport rather than a fire-and-forget
   button: articleBlocks decides what the article says, the queue in `speech`
   chains it to the end, the block being read is marked so a finger can follow
   it down the page, and the row carries Pause/Resume and Stop (WCAG 1.4.2 — a
   twenty-minute read must be stoppable without leaving the page). */
function inViewport(e) {
  const r = e.getBoundingClientRect();
  return r.bottom > 0 && r.top < (window.innerHeight || document.documentElement.clientHeight);
}
function readAloudControls() {
  const reduce = () => { try { return matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; } };
  // Mounted empty and written into later: a live region that arrives with its
  // text already inside it is announced unreliably, or not at all.
  const status = el('span', { class: 'read-status', role: 'status', 'aria-live': 'polite' });
  const play = btn({ class: 'btn small' });
  const stop = btn({ class: 'btn ghost small hidden', onclick: () => { stopSpeaking(); status.textContent = 'Stopped.'; } }, 'Stop');
  let reading = false, paused = false;
  let follow = true, autoScrollUntil = 0, onScroll = null, here = null;

  function label(...kids) { play.replaceChildren(...kids.filter(k => k != null)); }
  function setIdle(msg) {
    reading = false; paused = false;
    label(glyph('speak', 16), ' Read aloud');
    stop.classList.add('hidden');
    // Stop is about to vanish from under whoever pressed it; hiding a focused
    // element drops focus to <body>, which on this page is the top of an
    // eight-thousand-word article.
    if (document.activeElement === stop) play.focus();
    if (onScroll) { window.removeEventListener('scroll', onScroll); onScroll = null; }
    here = null;
    status.textContent = msg || '';
  }
  function unmark() { document.querySelectorAll('#article .reading-now').forEach(e => e.classList.remove('reading-now')); }

  function begin() {
    const blocks = articleBlocks();
    if (!blocks.length) { status.textContent = 'There is nothing to read on this page yet.'; return; }
    // Start where the reader is looking rather than at the title. They may have
    // scrolled to a section, or been put back at their remembered place by the
    // scroll memory — either way, jumping to the top of an eight-thousand-word
    // article to begin reading is not what the button was pressed for.
    let from = 0;
    if (docScrollTop() > 40) {
      const at = blocks.findIndex(b => b.el.getBoundingClientRect().bottom > 0);
      if (at > 0) from = at;
    }
    const parts = speechChunks(blocks.slice(from));
    follow = true; here = null;
    speakParts(parts.map(c => c.text), {
      onChunk: k => {
        unmark();
        parts[k].els.forEach(e => e.classList.add('reading-now'));
        here = parts[k].els[0];
        if (follow && here) {
          // Our own smooth scroll fires scroll events for the better part of a
          // second; without this window every read would decide on its first
          // chunk that the reader had taken the page.
          autoScrollUntil = Date.now() + (reduce() ? 150 : 900);
          try { here.scrollIntoView({ behavior: reduce() ? 'auto' : 'smooth', block: 'center' }); }
          catch (e) { here.scrollIntoView(); }
        }
      },
      onEnd: () => { unmark(); setIdle('Finished reading.'); },
    });
    // Registered after speakParts, which cleared the previous read's marks and
    // with them any restorer left over from it.
    _voiceRestore = () => { unmark(); setIdle(''); };
    reading = true; paused = false;
    label('Pause');
    stop.classList.remove('hidden');
    status.textContent = 'Reading aloud.';
    onScroll = () => {
      if (Date.now() < autoScrollUntil) return;
      // The reader has taken the page: stop dragging it out from under them.
      // And if they scroll back to where the voice is, they have asked to be
      // followed again.
      follow = !!(here && inViewport(here));
    };
    window.addEventListener('scroll', onScroll, { passive: true });
  }
  play.addEventListener('click', () => {
    if (!reading) { begin(); return; }
    try {
      if (paused) { speechSynthesis.resume(); paused = false; label('Pause'); status.textContent = 'Reading aloud.'; }
      else { speechSynthesis.pause(); paused = true; label('Resume'); status.textContent = 'Paused.'; }
    } catch (e) { stopSpeaking(); }
  });
  setIdle('');
  return el('span', { class: 'read-aloud' }, play, stop, status);
}

/* ---------------- the picture is not a trap ----------------
   render.py rewrites every link it cannot resolve to an article — File:,
   Category:, Special:, citation anchors, and the wrapper around very nearly
   every image — into a live `<a href="#">` with no handler at all (see its
   _SanitizedTagPass). Touching one emptied the hash, which parseHash resolves
   to `today`, which wipes the page. So the most instinctive gesture on the
   reading page deleted the page: `History of art` alone carries 470 such
   anchors, 316 of them wrapped around its pictures.

   For a pre-reader the images ARE the article, so the gesture is not a misfire
   to be swallowed — it is the reader asking for the picture. One delegated
   listener catches it and answers with the picture at full size and its
   caption read aloud. The a.primer-wikilink handlers are left exactly as they
   are; this runs behind them. */
function attachPictureHandlers(art) {
  // A "dead" anchor is one that goes nowhere: no href, or a bare fragment.
  // Real external links (render.py keeps those, with target=_blank) are none
  // of our business and must keep working.
  const dead = a => {
    if (a.classList.contains('primer-wikilink')) return false;
    const href = a.getAttribute('href') || '';
    return !href || href.startsWith('#');
  };
  const pictureIn = (target, a) =>
    (target && target.tagName === 'IMG') ? target : (a ? a.querySelector('img') : null);
  art.addEventListener('click', e => {
    const a = e.target.closest ? e.target.closest('a') : null;
    if (a && !dead(a)) return;
    const img = pictureIn(e.target, a);
    if (a) e.preventDefault();          // the ejection, stopped
    if (img) openLightbox(img, a || img);
  });
  art.addEventListener('keydown', e => {
    if (e.key !== 'Enter' && e.key !== ' ' && e.key !== 'Spacebar') return;
    const a = e.target.closest ? e.target.closest('a') : null;
    if (a && !dead(a)) return;
    // Enter on an anchor already fires a click, so answering it here as well
    // would open the picture twice. Space on an anchor scrolls instead of
    // activating, and a bare <img> answers to neither key on its own, so both
    // are needed everywhere except that one case.
    if (a && e.key === 'Enter') return;
    const img = pictureIn(e.target, a);
    if (!img) return;
    e.preventDefault();
    openLightbox(img, a || img);
  });
  // A picture with no anchor around it is not a trap, but a five-year-old will
  // touch it just the same — and an <img> is not focusable, so without this it
  // would be reachable by finger and by nothing else.
  art.querySelectorAll('img').forEach(im => {
    if (im.closest('a')) return;
    im.setAttribute('tabindex', '0');
    im.setAttribute('role', 'button');
    if (!im.getAttribute('alt')) im.setAttribute('aria-label', 'Picture — open it larger');
    im.classList.add('tappable');
  });
}
function openLightbox(img, opener) {
  // The caption a sighted reader can see belongs to the figure, not to the
  // <img>; alt text is the fallback, and a decorative image may carry neither.
  const fig = img.closest('figure, .thumb, .thumbinner, .gallerybox, .infobox');
  const capEl = fig ? fig.querySelector('figcaption, .thumbcaption') : null;
  const caption = ((capEl ? capEl.textContent : '') || img.getAttribute('alt') || '').trim();
  // openModal restores focus to whatever held it when the dialog opened, and a
  // tap leaves that on <body> — which would strand a keyboard reader at the top
  // of an eight-thousand-word article on Escape. Give the picture focus first
  // and Escape puts them back on the picture they opened.
  if (opener && opener.focus) {
    try { opener.focus({ preventScroll: true }); } catch (e) { opener.focus(); }
  }
  openModal({
    label: caption ? 'Picture — ' + caption : 'Picture',
    dismissable: true, dismissLabel: 'Close picture',
    build: (modal, close) => {
      modal.classList.add('wide');
      const box = el('div', { class: 'lightbox' });
      // Wikipedia ships most of its diagrams as black line-work marked
      // `skin-invert` and leaves the inversion to the skin. Both filter rules
      // are scoped to #article, so a diagram lifted out of the article and into
      // the overlay would go back to being black ink on the night page —
      // present, and invisible. The class travels with the picture.
      const big = el('img', { src: img.currentSrc || img.getAttribute('src') || '',
        alt: img.getAttribute('alt') || caption || '' });
      if (img.classList.contains('skin-invert')) big.classList.add('skin-invert');
      box.append(big);
      if (caption) {
        box.append(el('div', { class: 'cap' },
          speakBtn(() => caption, 'Read the caption aloud'),
          el('p', {}, caption)));
      }
      box.append(btn({ class: 'btn gold', style: 'margin-top:18px', onclick: close }, 'Close the picture'));
      modal.append(box);
      // The pre-reader hears what the picture is without having to find the
      // speaker first. maybeSpeak, not speakText: a reader who turned the
      // voice off is not spoken to.
      if (caption) maybeSpeak(caption);
    }
  });
}

function buildTutor(title) {
  const log = el('div', { id: 'tutor-log', 'aria-live': 'polite', 'aria-label': 'Conversation with the book' });
  const messages = [];
  let tutorFails = 0;  // consecutive-failure count drives the escalating reassurance below
  const panel = el('section', { id: 'tutor', 'aria-label': 'Ask the Book' },
    el('div', { class: 'th' }, el('span', { class: 'mark', 'aria-hidden': 'true' }, glyph('spark', 18)), el('b', {}, 'Ask the Book'),
      el('small', {}, S.state.tutor_engine === 'claude' ? 'Your patient tutor is listening' : 'Your Socratic guide'),
      // Honest about the wire: when the Claude engine answers, questions leave
      // the device. Said once, quietly, where the reader asks them — and said
      // ITEM BY ITEM, because "nothing else leaves the book" was already not
      // quite true (the reading level travels, as the tutor's register) and
      // would become plainly false the moment the reader's name did. A
      // disclosure is a promise about a wire; it has to name what is on it, or
      // every later thing put on that wire is a promise quietly broken.
      S.state.tutor_engine === 'claude'
        ? el('div', { class: 'tutor-disclosure' }, 'Your question travels to Claude (Anthropic) to be answered, and takes with it this conversation, the title and a passage of what you are reading, your first name, and your reading level. Nothing else leaves the book — not your lessons, not your streak, not anything else it has written down about you. ',
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
  // The paper's own clock, started when it is handed over. See the note on
  // the deck's: untrusted, non-load-bearing, and the only reason the book can
  // ever say "about four minutes" and mean this reader's four minutes.
  const startedAt = Date.now();
  let i = 0, correct = 0; const answers = [], confidences = [], oks = []; let confidence = null;
  // Ceremonies queue rather than collide. A stage ascension used to be fired on
  // a bare 900ms timer; with a page turn now also on offer in the same splash,
  // that timer could drop a second dialog on top of the chapter the reader had
  // just opened — and three overlapping animations is the one shape the
  // reduced-motion path cannot express either. So the ascension is HELD while
  // the reader takes the page turn, and released when they are done with it —
  // or when they close the splash having chosen not to.
  let heldAscension = null, turningPage = false, splashClosed = false;
  function releaseAscension(delay) {
    if (!heldAscension) return;
    const a = heldAscension; heldAscension = null;
    setTimeout(() => stageAscension(a), delay);
  }
  openModal({
    label: (String(title).toLowerCase().includes(String(kind).toLowerCase())
            ? title : title + ' ' + kind), dismissable: true, dismissLabel: 'Close quiz',
    build: (modal, close) => { drawQuestion(modal, close); },
    // Closing the splash without turning the page must not cost the reader the
    // promotion ceremony altogether — it is a real change to their book.
    onClose: () => { splashClosed = true; if (!turningPage) releaseAscension(300); },
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
      /* Committing an answer is irreversible and expensive: pick() posts to
         /api/quiz/check, commit_answer locks the item, and a wrong one calls
         burn_item, which removes it from this node's mastery evidence for
         seven days. On a 58px chip under a five-year-old's thumb that was one
         unconfirmed touch. Below stage 2 the first tap now only *chooses* — it
         echoes the choice aloud and lights a large Check button — and the
         reader commits when they mean to. Stage 2 and up keep one-tap, which
         is the rhythm an older reader already expects. Nothing about scoring,
         the sitting token, or when the answer is graded changes: only when the
         POST happens. */
      const twoBeat = S.stage <= 1;
      let picked = null, pickedVal = null;
      const checkIt = twoBeat ? btn({ class: 'btn gold check-it', disabled: '',
        style: 'width:100%;margin-top:14px',
        onclick: () => {
          if (!picked) return;
          checkIt.disabled = true;
          // Drop the chosen mark before the verdict marks land, or the button
          // ends up wearing both "✓ Chosen" and "✗".
          picked.classList.remove('selected');
          pick(picked, pickedVal, q, boxEl, card, modal, close);
        } }, glyph('known', 18), ' Check it') : null;
      q.choices.forEach(ch => {
        const b = btn({ class: 'choice', onclick: () => {
          if (!twoBeat) { pick(b, ch, q, boxEl, card, modal, close); return; }
          // Choosing another before Check simply moves the selection.
          boxEl.querySelectorAll('.choice').forEach(x => x.classList.remove('selected'));
          b.classList.add('selected');
          picked = b; pickedVal = ch;
          checkIt.disabled = false;
          // Deliberately not aria-pressed: mutually exclusive options announce
          // as independent switches that way. The "✓ Chosen" mark rides inside
          // the button, so it travels in the accessible name, and the live
          // region says the same thing out loud for a reader who is listening.
          maybeSpeak(ch);
          tell(card, 'You chose ' + ch + '. Press “Check it” when you are ready.');
        } }, ch, el('span', { class: 'sel-mark' }, '✓ Chosen'));
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
      if (checkIt) card.append(checkIt);
    } else if (q.kind === 'order') {
      /* Tap the items into sequence — a produced answer, not a recognised one.
         Dropping the last chip used to submit the whole arrangement on the
         spot: posted, locked by commit_answer, and a wrong order burned out of
         this node's mastery evidence for seven days, all without the reader
         ever saying they were done. It also left "↺ Start over" dead from the
         exact moment it could first have been useful. Arranging and committing
         are two beats now — and this restores a control the card was already
         drawing rather than inventing one. Universal, every stage: nobody
         benefits from having their last tap read as a final answer. */
      const chosen = [];
      const tray = el('div', { class: 'order-tray', role: 'group', 'aria-label': 'Tap in order' });
      const slot = el('div', { class: 'order-slot', 'aria-live': 'polite',
        'aria-label': 'Your order so far' });
      const check = btn({ class: 'btn gold', disabled: '',
        onclick: () => submitOrder(chosen, q, card, modal, close) }, 'Check');
      const startOver = btn({ class: 'btn ghost small', onclick: () => {
        chosen.length = 0; tray.querySelectorAll('button').forEach(b => b.disabled = false); redraw();
        const first = tray.querySelector('.order-chip:not(:disabled)');
        if (first) first.focus();
      } }, '↺ Start over');
      const redraw = () => {
        slot.innerHTML = '';
        chosen.forEach(v => slot.append(el('span', { class: 'order-chip placed' }, v)));
        if (!chosen.length) slot.append(el('span', { class: 'muted' }, 'Tap them in order…'));
        check.disabled = chosen.length !== q.items.length;
      };
      q.items.forEach(v => {
        const b = btn({ class: 'order-chip', onclick: () => {
          if (b.disabled) return;
          b.disabled = true; chosen.push(v); redraw();
          // Disabling the chip we just used must not dump focus to <body> —
          // and when it was the last one there is no next chip, so the place
          // to land is the control that finishes the job.
          const nxt = tray.querySelector('.order-chip:not(:disabled)');
          (nxt || check).focus();
        } }, v);
        tray.append(b);
      });
      // Mount the live region first, then fill it. Calling redraw() before the
      // append meant the slot arrived in the document already containing its
      // instruction — announced once on insert, and unreliably thereafter.
      card.append(slot, tray, el('div', { class: 'order-actions' }, check, startOver));
      redraw();
    } else if (q.kind === 'short') {
      // Constructed response: the reader must produce the idea, not spot it.
      const ta = el('textarea', { rows: '4', 'aria-label': 'Your answer',
        placeholder: 'Explain it in your own words…',
        style: 'width:100%;padding:12px;font-size:17px;font-family:var(--serif);border:1px solid var(--rule);border-radius:8px;background:var(--field);color:var(--ink)' });
      if (confidenceRow) card.append(el('p', { class: 'muted', style: 'margin:2px 0 6px' }, 'How sure are you?'), confidenceRow);
      card.append(ta, btn({ class: 'btn gold', style: 'margin-top:10px', onclick: () => submitShort(ta, q, card, modal, close) }, 'Check my answer'));
      setTimeout(() => ta.focus(), 40);
    } else if (q.kind === 'tally') {
      /* Count by touching — the fourth answering gesture, and the first new
         thing the reader's hands have learned to do in the whole assessment
         path. Every object is a real <button>, so finger and keyboard reach it
         by the same route and neither needs a special case. Pressing one
         catches it; the running total goes to a live region of its own — never
         the buttons re-announcing themselves — and is said aloud for a reader
         who cannot yet read it. One large button commits the count.

         The committed answer is a number string, so _numeric_equal grades it
         with no scoring change at all. Until this branch existed a tally item
         fell through to the numeric text input below: a five-year-old asked to
         type the numeral she is being tested on recognising. `answer` is
         String(items.length) — there is no separate count field, and the
         length must never reach the accessible name of a token or the paper
         gives itself away. */
      const items = Array.isArray(q.items) ? q.items : [];
      const counter = el('div', { class: 'tally-count', role: 'status', 'aria-live': 'polite' });
      const tray = el('div', { class: 'tally-tray', role: 'group', 'aria-label': 'Touch each one to count it' });
      const tokens = [];
      const tallied = () => tokens.filter(t => t.classList.contains('caught')).length;
      const refresh = spoken => {
        const n = tallied();
        counter.textContent = n === 0 ? 'None counted yet' : n + ' counted';
        // maybeSpeak, not speakText: the book is talking without being asked
        // to, and a reader who turned the voice off is not spoken to.
        if (spoken) maybeSpeak(String(n));
      };
      items.forEach(it => {
        const t = btn({ class: 'tally-token', 'aria-pressed': 'false',
          // Every token carries the same name on purpose. A positional one
          // ("item 7 of 9") would read the answer out to the reader who most
          // needs the count to be their own work; aria-pressed is what tells
          // the caught ones from the rest.
          'aria-label': 'One to count',
          onclick: () => {
            // Pressing a caught one again lets it go. A miscount has to be
            // undoable, or the only way back is to abandon the question.
            const on = !t.classList.contains('caught');
            t.classList.toggle('caught', on);
            t.setAttribute('aria-pressed', on ? 'true' : 'false');
            refresh(true);
          } },
          el('span', { class: 'tk-face', 'aria-hidden': 'true' }, String(it)),
          el('span', { class: 'tk-mark', 'aria-hidden': 'true' }, '✓'));
        tokens.push(t); tray.append(t);
      });
      if (confidenceRow) card.append(el('p', { class: 'muted', style: 'margin:2px 0 6px' }, 'How sure are you?'), confidenceRow);
      // Mount the live region, then fill it: one that arrives with its text
      // already inside is announced unreliably, or not at all.
      card.append(counter, tray,
        btn({ class: 'btn gold tally-commit', onclick: () => submitTally(tokens, q, card, modal, close) },
            'That is how many'));
      refresh(false);
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
    // Check and Start over go down with the chips: once the answer is on its
    // way to be graded, neither of them has anything left to do.
    card.querySelectorAll('.order-chip, .order-actions button').forEach(c => c.disabled = true);
    holdFocus(card, 'Checking…');
    const m = await mark(q, chosen.join(' '));
    card.querySelector('.order-slot').classList.add(m.correct ? 'correct' : 'wrong');
    // Never colour-only: always state the verdict in words as well.
    tell(card, m.correct ? '✓ That is the right order.'
                         : 'Not quite — the right order is: ' + m.answer);
    reveal(m.correct, { ...q, answer: m.answer }, chosen.join(' '), card, modal, close);
  }

  async function submitTally(tokens, q, card, modal, close) {
    const n = tokens.filter(t => t.classList.contains('caught')).length;
    // Committing zero is a wrong answer that burns the item out of this node's
    // mastery evidence for seven days. The other produced-answer types nudge
    // rather than post an empty one; so does this.
    if (!n) {
      nudge(card, 'Touch each one first — then press the button.');
      if (tokens.length) tokens[0].focus();
      return;
    }
    tokens.forEach(t => t.disabled = true);
    card.querySelectorAll('.tally-commit').forEach(b => b.disabled = true);
    holdFocus(card, 'Checking…');
    const m = await mark(q, String(n));
    const tray = card.querySelector('.tally-tray');
    if (tray) tray.classList.add(m.correct ? 'correct' : 'wrong');
    // Never colour-only: the verdict is always stated in words as well.
    tell(card, m.correct ? '✓ Correct — there are ' + n + '.'
                         : (m.answer ? 'Not quite — there are ' + m.answer + '.' : 'Not quite.'));
    reveal(m.correct, { ...q, answer: m.answer, explain: m.explain || q.explain }, String(n), card, modal, close);
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
    haptic(ok ? 'ok' : 'no');
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
    let msg = '', msgTone = 'neutral', ascension = null, xp = 0, calibration = null, storyUnlocked = null;
    if (nodeId && !isRetry) {
      // A retry of only the missed items must not be scored as a fresh
      // attempt — otherwise failing then re-answering 5 of 6 posts 100%.
      try {
        if (kind === 'quiz') {
          const r = await api.post('/api/quiz/submit', { node_id: nodeId, answers, make_cards: true, confidence: confidences, token, seconds: (Date.now() - startedAt) / 1000 });
          xp = r.mastery.xp_gained || 0; ascension = r.ascension; calibration = r.calibration;
          // null unless THIS lesson is the one the open chapter was waiting for.
          storyUnlocked = r.story_unlocked || null;
          if (r.mastery.newly_mastered) { msg = r.mastery.proven
            ? '✦ Mastered! You have proved this one — it is now truly yours.'
            : '✦ Mastered! This lesson is now complete.'; msgTone = 'good'; }
          else if (r.mastery.proven) msg = 'Reviewed — already proved.';
          else if (r.mastery.mastered) msg = 'The book assumed you knew this. Pass it once more, a day or two apart, to prove it.';
          // The only loss-framed sentence in the product, and it fires at the
          // moment a reader is least able to hear it. Slipping is what memory
          // does; the book knows that and built a whole deck around it.
          else if (r.mastery.lost_mastery) { msg = 'This one has drifted out of reach for now — which is what memory does, and why the book keeps a deck. One more good pass brings it back.'; msgTone = 'warn'; }
          else {
            // "Come back in a day or two" was a guess, and on a young reader's
            // six-hour proving window it was the wrong guess by a day and a
            // half of credit they had already earned. record_attempt now
            // returns the exact moment, and — unlike mastery_detail — it does
            // not null an elapsed one, so a past timestamp means ready NOW and
            // is never printed as a date that has gone by.
            // The splash above correctly hides its percentage from a young
            // reader (`if (!young)`) and this line, three branches later, printed
            // one anyway. (Only printed — a verification pass confirmed no speech
            // path ever carried this string.) A four-year-old still has no use
            // for eighty per cent on screen.
            // Deliberately no terminal punctuation on either branch: the
            // appointment clause below joins onto this with an em dash, and
            // the first draft of the young wording ended in a full stop, so
            // the book said "You are getting there. — you have proved it
            // once." Caught in the browser, on the very first failed quiz.
            msg = young
              ? (r.mastery.level >= 0.67 ? 'Nearly there'
                 : r.mastery.level >= 0.34 ? 'You are getting there'
                 : 'A good start, and the book has written it down')
              : 'Progress: ' + Math.round(r.mastery.level * 100) + '% toward mastery';
            const ra = r.mastery.ready_at;
            if (ra == null) msg += '.';
            else if (readyNow(ra)) msg += ' — you have proved it once already, so the next pass seals it.';
            else msg += ' — you have proved it once. Pass it again after ' + whenReady(ra) + ' and it is sealed.';
          }
          if (r.cards_added) msg += ' ' + r.cards_added + ' review card' + (r.cards_added > 1 ? 's' : '') + ' added.';
          if (r.mastery.newly_mastered) celebrate();
        } else {
          const r = await api.post('/api/attempt', { node_id: nodeId, answers, token, seconds: (Date.now() - startedAt) / 1000 });
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
    if (xp) { splash.append(el('p', { style: 'color:var(--gold-ink);font-weight:700;font-size:18px' }, '+' + xp + ' growth')); flyXP(xp); }
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
    // The page turns where it was earned — but the READER turns it. Advancing
    // is a write, and a chapter that opens itself is a chapter nobody chose to
    // read; openStory already owns the POST, the ceremony and the XP fly-up.
    if (storyUnlocked) {
      splash.append(el('p', { class: 'page-turned' },
        '✦ “' + storyUnlocked.title + '” — chapter ' + storyUnlocked.number + ' of your story is open.'));
      controls.append(btn({ class: 'btn gold page-turn', onclick: () => {
        turningPage = true;
        close();
        openStory(storyUnlocked.chapter, true, null,
          () => { turningPage = false; releaseAscension(900); });
      } }, glyph('story', 16), ' The page has turned — read it'));
    }
    // The stakes were real and undisclosed: a missed question stops being
    // evidence for this node for seven days. Told plainly, at the only moment
    // it is true, and framed as what it actually is — the book declining to be
    // convinced by a question it has just answered for you.
    // Not for a pre-reader: it is a paragraph about evidence and proof, and
    // the five-year-old it would be read aloud to has no use for it.
    // Practice papers burn missed items exactly as quizzes do (the server
    // spends the item either way) — a disclosure gated on quizzes alone left
    // practice burning silently, which is the undisclosed-stakes bug again.
    if (missedIdx.length && !isRetry && (kind === 'quiz' || kind === 'practice') && !young) {
      // Both numbers written out rather than run through plural(): that helper
      // fixes the count and the noun, and this sentence carries the number
      // three more times after them — "The 1 question … that question … that
      // one" is the same machine-wrote-this tell in a longer coat.
      splash.append(el('p', { class: 'muted burn-note' }, missedIdx.length === 1
        ? 'The question you missed has stepped aside for a week — once the book has shown you an answer, that question cannot be its proof that you know it. Every other question still counts, and so will that one, later.'
        : 'The ' + missedIdx.length + ' questions you missed have stepped aside for a week — once the book has shown you an answer, a question cannot be its proof that you know it. Every other question still counts, and so will those, later.'));
    }
    if (missedIdx.length) controls.append(btn({ class: 'btn', onclick: () => { const retry = missedIdx.map(k => questions[k]); close(); runQuestions({ title, questions: retry, nodeId, kind, stage, isRetry: true }); } }, '↻ Retry the ' + missedIdx.length + ' you missed'));
    controls.append(btn({ class: 'btn ghost', onclick: close }, 'Close'));
    if (nodeId) controls.append(btn({ class: 'btn gold', onclick: () => { close(); go('node', nodeId); } }, 'Back to lesson'));
    splash.append(controls);
    modal.append(splash);
    if (young) maybeSpeak('You got ' + correct + ' out of ' + questions.length + '. ' + (score >= 0.7 ? 'Wonderful work!' : 'Good try — let us practice a little more.'));
    // Strictly sequenced: page turn first, stage ceremony behind it. With no
    // page turn on offer this is the same 900ms beat it always was.
    if (ascension) {
      heldAscension = ascension;
      // A reader who closed the splash while the submit was still in flight has
      // no page turn left to wait behind — release rather than swallow it.
      if (!storyUnlocked || splashClosed) releaseAscension(900);
    }
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
  const p = el('div', { class: 'xp-pop' }, '+' + xp + ' growth');
  document.body.append(p); setTimeout(() => p.remove(), 1500);
}
function celebrate() { confetti(); }
function confetti() {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  // Two ceremonies can now land within a second of each other (mastery, then
  // the page it turned). One storm is a celebration; two overlaid is noise.
  if (document.querySelector('.confetti')) return;
  haptic('fanfare');  // behind both guards above: one storm, one shudder
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
    'Every field, from preschool roots to the graduate frontier. Golden tiles are open to you now and fill as you master them; locked tiles show exactly what will unlock them. Click any to begin.'));
  // The wall of locks is the honest shape of a whole education, and it should
  // read as an invitation rather than a verdict. One line, in the Guide's
  // register: the scale is the point, and it is survivable.
  page.append(el('p', { class: 'epigraph' },
    'Yes, it is an enormous amount. Every reader who ever finished started with exactly one tile.'));
  quickAccess(page, g);

  /* The 250KB the page already fetches carries eight distinct states per node
     — mastery, proven, ever_proven, faded, assumed, assumed_stale, unlocked,
     mastered — and this view used to collapse all of them into three tile
     classes and throw the rest away. So a topic sitting at 0.79 rendered
     identically to one never opened, and on day one 315 of 353 tiles were an
     undifferentiated grey wall. Nothing below needs a single server change:
     it reads what is already on the wire, and gives the reader a way to cut
     the map down to the handful of tiles that are theirs to work on today. */
  const mine = new Set((S.state && S.state.profile && S.state.profile.domains) || []);
  const FILTERS = [
    ['All fields', () => true],
    // An empty domains list means "every field" to the server, so this option
    // is only offered when the reader actually chose a shelf.
    mine.size ? ['My fields', n => mine.has(n.domain)] : null,
    ['Open now', n => n.unlocked && !n.mastered],
    ['Nearly there', n => (n.mastery || 0) >= 0.5 && (n.mastery || 0) < 0.8],
    ['Faded', n => !!n.faded],
  ].filter(Boolean);

  // Exactly one filter applies at a time, which makes this a radiogroup with a
  // roving tabindex — not a row of aria-pressed toggles, which announce as
  // independent switches. Same pattern, and the same reasoning, as the
  // confidence row in the quiz.
  const bar = el('div', { class: 'atlas-filters', role: 'radiogroup', 'aria-label': 'Which tiles to show' });
  FILTERS.forEach(([label, test], k) => {
    const b = btn({ class: 'btn ghost small filter-opt' + (k === 0 ? ' picked' : ''),
      role: 'radio', 'aria-checked': k === 0 ? 'true' : 'false',
      tabindex: k === 0 ? '0' : '-1',
      onkeydown: e => {
        if (!['ArrowDown', 'ArrowRight', 'ArrowUp', 'ArrowLeft', 'Home', 'End'].includes(e.key)) return;
        e.preventDefault();
        const all = [...bar.querySelectorAll('[role=radio]')];
        const cur = all.indexOf(e.currentTarget);
        const dir = (e.key === 'ArrowDown' || e.key === 'ArrowRight') ? 1 : -1;
        const nxt = e.key === 'Home' ? all[0]
                  : e.key === 'End' ? all[all.length - 1]
                  : all[(cur + dir + all.length) % all.length];
        nxt.focus(); nxt.click();
      },
      onclick: () => {
        bar.querySelectorAll('[role=radio]').forEach(x => {
          x.classList.remove('picked'); x.setAttribute('aria-checked', 'false'); x.setAttribute('tabindex', '-1'); });
        b.classList.add('picked'); b.setAttribute('aria-checked', 'true'); b.setAttribute('tabindex', '0');
        paint(test, label);
      } }, label, el('span', { class: 'filter-mark' }, '✓ Showing'));
    bar.append(b);
  });
  // Mounted empty, filled after it has landed in the document: a live region
  // that arrives with its text already inside it is announced unreliably or
  // not at all.
  const live = el('div', { class: 'atlas-live', role: 'status', 'aria-live': 'polite' });
  const board = el('div', { class: 'atlas-board' });
  page.append(bar, live, board);

  function paint(test, label) {
    board.innerHTML = '';
    let shown = 0;
    g.domains.forEach(d => {
      // Filtering only ever reduces the render — a domain with nothing left in
      // it drops out rather than standing as an empty heading.
      const dnodes = g.nodes.filter(n => n.domain === d.id && test(n));
      if (!dnodes.length) return;
      shown += dnodes.length;
      board.append(domainBlock(d, dnodes));
    });
    if (!shown) board.append(emptyLeaf('atlas', 'Nothing in that state — yet',
      'No tile answers to that just now. Choose “All fields” to see the whole map again.'));
    live.textContent = '';
    setTimeout(() => { live.textContent = label + ' — showing ' + shown + ' of ' + g.nodes.length + ' topics.'; }, 30);
  }

  // Six cells, one per stage, from counts the payload already computes and
  // this page used to reduce to a single total. Progress by stage is the fact
  // a reader actually wants: which band they are in, and which gate is shut.
  function stageStrip(d) {
    const said = d.stages.map(s => STAGE_NAMES[s.stage] + ' ' + s.mastered + ' of ' + s.total
      + (s.open ? ', open' : ', gate not open yet'));
    const strip = el('div', { class: 'stage-strip', role: 'img',
      'aria-label': 'By stage — ' + said.join('; ') });
    d.stages.forEach(s => {
      const pct = s.total ? Math.round(100 * s.mastered / s.total) : 0;
      strip.append(el('span', { class: 'ss-cell' + (s.open ? '' : ' shut'),
        title: STAGE_NAMES[s.stage] + ' — ' + s.mastered + ' of ' + s.total + ' mastered'
             + (s.open ? '' : ' · gate not open yet') },
        el('i', { style: 'width:' + pct + '%' }),
        el('b', {}, STAGE_NAMES[s.stage].slice(0, 2))));
    });
    return strip;
  }

  function nodeTile(n) {
    const pct = Math.round((n.mastery || 0) * 100);
    const cls = n.mastered ? 'mastered' : (n.unlocked ? 'available' : 'locked');
    // The last node of a field is where the field itself stops knowing —
    // the one tile on this page that nobody has finished. It should not
    // look like one more padlock among forty.
    const frontier = /\.5\.frontier$/.test(n.id);
    // State is never carried by colour alone: each tile takes a drawn mark and
    // says the same thing in words in its accessible name.
    const marks = [];
    const said = [n.title];
    said.push(n.mastered ? 'mastered'
            : !n.unlocked ? 'locked'
            : pct > 0 ? pct + '% mastered'
            : 'open, not started');
    if (n.faded) { marks.push('◐'); said.push('faded — proved once, and it has slipped since'); }
    if (n.assumed) {
      marks.push('◇');
      said.push(n.assumed_stale ? 'assumed from your placement, and that credit has expired'
                                : 'assumed from your placement, not yet proved');
    }
    if (frontier) said.push('the frontier of this field');
    if (cls === 'locked') said.push('open it to see what unlocks it');
    return btn({
      class: 'node-dot ' + cls + (frontier ? ' frontier' : '') + (n.faded ? ' faded' : '')
             + (n.assumed ? ' assumed' : '') + (n.assumed_stale ? ' assumed-stale' : ''),
      // Per-element geometry, not a themed token: --m is how far this one tile
      // has come, and the gold fills to exactly that point.
      style: '--m:' + pct + '%',
      title: frontier ? 'The edge of what is known — where learning becomes research.'
                      : (n.unlock_requirements ? n.unlock_requirements.join('; ') : (n.goal || '')),
      'aria-label': said.join(' — '),
      onclick: () => { if (n.unlocked || n.mastered) go('node', n.id); else lockedPeek(n); } },
      n.title,
      marks.length ? el('span', { class: 'dot-mark', 'aria-hidden': 'true' }, ' ' + marks.join('')) : null);
  }

  function domainBlock(d, dnodes) {
    const block = el('section', { class: 'domain-block', 'aria-label': d.name });
    const total = d.stages.reduce((s, x) => s + x.total, 0);
    // Across 353 tiles the one that matters is the first open, unmastered tile
    // in the field, and finding it used to be a scan by eye. Focus travels with
    // the scroll so a keyboard reader arrives on the tile, not merely near it.
    let frontierTile = null;
    const jump = btn({ class: 'btn ghost small frontier-jump',
      'aria-label': 'Jump to your frontier in ' + d.name,
      onclick: () => {
        if (!frontierTile) return;
        frontierTile.focus({ preventScroll: true });
        frontierTile.scrollIntoView({ block: 'center',
          behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
      } }, '→ My frontier');
    block.append(el('div', { class: 'domain-head' },
      // Same daylight-hex lift as the lesson-card domain tag: themed via
      // --domain-lift so the ten curriculum colours survive the night palette.
      el('div', { class: 'ic', style: `background:color-mix(in srgb, ${d.color}, white var(--domain-lift, 0%))`, 'aria-hidden': 'true' }, domainMark(d, 20)),
      el('div', { class: 'dh-text' }, el('h3', {}, d.name),
        el('div', { class: 'tag' }, d.mastered + ' / ' + total + ' mastered — ' + (d.tagline || '')),
        stageStrip(d)),
      jump));
    for (let s = 0; s < 6; s++) {
      const nodes = dnodes.filter(n => n.stage === s);
      if (!nodes.length) continue;
      const row = el('div', { class: 'stage-row' });
      row.append(el('div', { class: 'stage-label' }, STAGE_NAMES[s]));
      const nr = el('div', { class: 'node-row' });
      nodes.forEach(n => {
        const tile = nodeTile(n);
        if (!frontierTile && n.unlocked && !n.mastered) frontierTile = tile;
        nr.append(tile);
      });
      row.append(nr); block.append(row);
    }
    // A field with nothing open in it gets no button rather than a dead one.
    if (!frontierTile) jump.remove();
    return block;
  }

  paint(FILTERS[0][1], FILTERS[0][0]);
}
// Quick access — the specialist field as an index rather than a ladder.
//
// Radiology is postgraduate: its tiles are locked for almost every reader,
// which makes the ordinary route through the Atlas useless for reviewing the
// material itself. This panel is the other route — lesson, quiz and each source
// article, one click from the top of the page, whatever the gates say.
//
// It began as a flat list of five modules. At eighty-odd it would be a wall, so
// it is now what a reference work of this size actually needs: an index, filed
// by section, searchable, with the sections closed until asked for. The lock
// state stays visible on every row, because a shortcut that looks like progress
// is a lie about what the reader has done.
function quickAccess(page, g) {
  const d = g.domains.find(x => x.id === 'radiology');
  if (!d) return;
  const nodes = g.nodes.filter(n => n.domain === 'radiology');
  if (!nodes.length) return;
  const sections = [];
  nodes.forEach(n => {
    const name = n.section || 'Other';
    let sec = sections.find(x => x.name === name);
    if (!sec) sections.push(sec = { name: name, nodes: [] });
    sec.nodes.push(n);
  });
  const locked = nodes.filter(n => !n.unlocked && !n.mastered).length;

  const box = el('section', { class: 'quick-access', 'aria-label': 'Quick access — ' + d.name });
  box.append(el('div', { class: 'qa-head' },
    el('div', { class: 'ic', style: `background:color-mix(in srgb, ${d.color}, white var(--domain-lift, 0%))`, 'aria-hidden': 'true' }, domainMark(d, 18)),
    el('div', {}, el('h3', {}, 'Quick access · ' + d.name),
      el('div', { class: 'tag' }, plural(nodes.length, 'module') + ' across '
        + plural(sections.length, 'section') + ' — open any lesson, quiz or article directly, locked or not.'))));

  // The honest door out of the lock, offered only while there is something
  // locked to open. See POST /api/domain/open: it credits the general-spine
  // groundwork as ASSUMED, never as proved.
  if (locked) box.append(el('div', { class: 'qa-open' },
    btn({ class: 'btn gold small', onclick: () => openField(d, locked) },
      glyph('spark', 15), ' Open this field — I already have the grounding'),
    el('span', { class: 'muted' }, plural(locked, 'module') + ' still gated on the general spine.')));

  const search = el('input', { type: 'search', class: 'qa-search',
    placeholder: 'Filter modules — “stroke”, “LI-RADS”, “paediatric”…',
    'aria-label': 'Filter radiology modules' });
  const count = el('div', { class: 'qa-count', role: 'status', 'aria-live': 'polite' });
  box.append(search, count);

  const groups = [];
  sections.forEach(sec => {
    const wrap = el('details', { class: 'qa-section' });
    const sum = el('summary', {}, el('b', {}, sec.name),
      el('span', { class: 'qa-n' }, String(sec.nodes.length)));
    wrap.append(sum);
    const rows = sec.nodes.map(n => {
      const state = n.mastered ? ['mastered', '✓ mastered'] : (n.unlocked ? ['available', 'open'] : ['locked', 'locked']);
      const row = el('div', { class: 'qa-row' });
      row.append(el('div', { class: 'qa-title' },
        el('b', {}, n.title), el('span', { class: 'qa-state ' + state[0] }, state[1]),
        n.goal ? el('p', { class: 'muted' }, n.goal) : null));
      row.append(el('div', { class: 'qa-acts' },
        // Eighty identical "Lesson" buttons read as eighty identical buttons to
        // anyone listening; the module name has to travel with each.
        btn({ class: 'btn small', 'aria-label': 'Lesson — ' + n.title, onclick: () => go('node', n.id) }, 'Lesson'),
        btn({ class: 'btn ghost small', 'aria-label': 'Quiz — ' + n.title, onclick: () => startQuiz(n.id) }, glyph('quill', 14), ' Quiz')));
      const arts = el('div', { class: 'qa-arts' });
      (n.articles || []).forEach(a => arts.append(btn({ class: 'node-dot',
        'aria-label': 'Read “' + a + '” — ' + n.title,
        onclick: () => go('reader', { title: a, node: n.id }) }, a)));
      if (arts.children.length) row.append(arts);
      wrap.append(row);
      return { row: row, hay: (n.title + ' ' + sec.name + ' ' + (n.goal || '')).toLowerCase() };
    });
    groups.push({ wrap: wrap, rows: rows });
    box.append(wrap);
  });

  function filter() {
    const q = search.value.trim().toLowerCase();
    let shown = 0;
    groups.forEach(gr => {
      let here = 0;
      gr.rows.forEach(r => {
        const hit = !q || r.hay.includes(q);
        r.row.hidden = !hit;
        if (hit) here++;
      });
      gr.wrap.hidden = here === 0;
      // A search that leaves a section closed has hidden its own results.
      if (q) gr.wrap.open = here > 0;
      shown += here;
    });
    count.textContent = q
      ? shown + (shown === 1 ? ' module matches “' : ' modules match “') + search.value.trim() + '”.'
      : '';
  }
  search.addEventListener('input', filter);
  page.append(box);
}

// Opening a specialist field. The confirmation is not a formality: the reader
// is about to be credited with work they have not done here, and the book says
// so plainly before it does it, in the same words the tiles will then use.
function openField(d, locked) {
  openModal({ label: 'Open ' + d.name, dismissable: true, build: (modal, close) => {
    modal.append(el('h2', { style: 'margin-top:0' }, glyph('spark', 20), ' Open ' + d.name + '?'));
    modal.append(el('p', {}, 'This field begins where the general spine ends. Its '
      + plural(locked, 'module') + ' wait on anatomy, physiology and physics from the ten fields — '
      + 'grounding you may well already have.'));
    modal.append(el('p', { class: 'muted' },
      'Say so and the book will take you at your word: it marks that groundwork '
      + '“assumed, not yet proved”, exactly as a placement check would, and opens '
      + 'the field. Nothing is recorded as mastered, no growth is paid, and you can '
      + 'prove any of it later — at which point the assumption gives way to the real thing.'));
    // An assumption the book has never seen proved lapses at six months
    // (ASSUMED_CREDIT_LIFE). Saying so now costs one sentence; finding the
    // field quietly shut half a year later, having been told nothing, is the
    // kind of small betrayal this book does not do.
    modal.append(el('p', { class: 'muted' },
      'In six months the book will ask again, as it does with any assumption it '
      + 'has not seen proved. One click reopens it.'));
    const row = el('div', { style: 'display:flex;gap:10px;margin-top:18px' });
    const go_ = btn({ class: 'btn gold', onclick: async () => {
      go_.disabled = true;
      try {
        const r = await api.post('/api/domain/open', { domain: d.id });
        close();
        toast(d.name + ' is open — ' + plural(r.opened, 'module') + ' of ' + r.total + ' ready.');
        S.state = await api.get('/api/state');
        renderShell(); renderRoute();
      } catch (e) {
        go_.disabled = false;
        toast('The book could not open that field just now — nothing is lost, and you can ask again.');
      }
    } }, 'Open the field');
    row.append(go_, btn({ class: 'btn ghost', onclick: close }, 'Not yet'));
    modal.append(row);
  } });
}
function lockedPeek(n) {
  openModal({ label: n.title + ' locked', dismissable: true, build: (modal, close) => {
    modal.append(el('h2', { style: 'margin-top:0' }, glyph('lock', 20), ' ' + n.title));
    modal.append(el('p', { class: 'muted' }, n.goal || ''));
    modal.append(el('p', { style: 'font-family:var(--sans);font-weight:600;margin-bottom:6px' }, 'To unlock this:'));
    const box = el('div', {});
    // Every requirement here used to be an inert chip: the reader was told the
    // name of a lesson and then left to hunt for it by eye across 353 tiles.
    // The node carries the real prerequisite ids all along (annotated_graph
    // copies the whole node), so the ones that name a lesson become buttons
    // that go to it — the pattern the "Worth refreshing" row already uses.
    const byId = new Map();
    ((S.curriculum && S.curriculum.nodes) || []).forEach(x => byId.set(x.id, x));
    const jumps = (n.prereqs || []).filter(p => {
      const pn = byId.get(p);
      // A prerequisite already mastered is not what is standing in the way.
      return pn && !pn.mastered;
    });
    jumps.forEach(p => box.append(btn({ class: 'req-chip req-jump',
      onclick: () => { close(); go('node', p); } },
      'Master “' + byId.get(p).title + '”',
      el('span', { class: 'go-mark', 'aria-hidden': 'true' }, '→'))));
    // Prose requirements with no lesson behind them — "Master 4 more Seedling
    // topics" is a statement about the stage gate, not a tile — stay inert.
    // The "Master “X”" strings the server writes are exactly the prereqs
    // rendered as buttons above, so they are dropped rather than said twice.
    (n.unlock_requirements || ['Keep progressing in this field.']).forEach(r => {
      if (jumps.length && /^Master\s+“/.test(r)) return;
      box.append(el('span', { class: 'req-chip' }, r));
    });
    modal.append(box, btn({ class: 'btn gold', style: 'margin-top:16px', onclick: close }, 'Got it'));
  } });
}

/* ---------------- how the book studies you ----------------
   Benchmark 12 asks that the learner be taught HOW to learn, not only what.
   The product had exactly one sentence of that, at the top of this page, and
   a reader could use the deck for a year without ever being told why the book
   insists on a gap, why the cards are shuffled between subjects, why it asks
   how sure they are, or what happens to a question they miss. All four are
   real, all four are already implemented, and a reader who understands them
   grades themselves more honestly — so the explanation is not decoration, it
   is part of the instrument.

   A <details> rather than a permanent wall of text: the reader who wants it
   opens it, and it is closed for the reader who has read it once. Native
   disclosure semantics, so keyboard and screen reader get it for free. */
function studyNote() {
  const d = el('details', { class: 'study-note' });
  d.append(el('summary', {}, glyph('spark', 14), ' How the book studies you'));
  [
    ['Remembering beats re-reading.', 'Reading a page again feels like learning and mostly is not. Being asked, and having to dig the answer out yourself, is what moves it. That is why the book asks before it tells — and why writing your answer down before you turn a card is worth the four seconds.'],
    ['The gap is the point.', 'The book waits a day or two before it will seal a lesson, and it brings a card back just as you are about to lose it. Practising something you already have fresh in mind is comfortable and teaches almost nothing. A little forgetting, then a little effort, is the whole trick.'],
    ['The deck shuffles on purpose.', 'Cards from different subjects are mixed together rather than blocked into neat runs. Blocked practice feels smoother and holds worse: mixing forces you to work out which kind of thing this is, which is what you will have to do when it matters.'],
    ['Knowing what you know.', 'The book asks how sure you are, and afterwards tells you how well you judged it. Being confidently wrong is the most expensive state to be in, and it is invisible until somebody measures it.'],
    ['A question you miss steps aside.', 'When you get one wrong the book shows you the answer straight away — and then that particular question cannot count as proof you know the thing for the next week. Not a penalty: it is simply no longer evidence once you have been told. Other questions still count, and so does that one, a week from now.'],
  ].forEach(([h, body]) => d.append(el('p', {}, el('b', {}, h), ' ' + body)));
  return d;
}

/* ---------------- Review ---------------- */
async function renderReview(page, arg) {
  const short = arg === 'short';
  const data = await guard(page, () => api.get('/api/review/due?limit=30' + (short ? '&dose=short' : '')));
  if (!data) return;
  // A day with a bottom. `goal` is the day's ask, priced by the same server
  // function the quest tile is priced by — a deck that stopped at a different
  // number from the one the tile promised would be worse than one that never
  // stopped. Zero means the deck is excused, not that the day is done.
  const goal = data.goal | 0;
  let bottom = goal > 0 ? Math.min(goal, data.cards.length) : data.cards.length;
  page.append(pagehead('Spaced repetition', 'Strengthen What You Know',
    'The book brings back what you are about to forget, exactly when you are about to forget it. ' + data.stats.due + ' of ' + data.stats.total + ' cards are due.'
    + (bottom < data.cards.length
       ? (short ? ' You asked for a short sitting, so the book asks for ' + bottom + ' of them — the rest keep.'
                : ' Today the book asks for ' + bottom + ' of them.')
       : '')));
  // A short sitting is a smaller door into the same room, and the reader
  // should be able to see the room from it.
  if (short && data.stats.due > bottom) {
    page.append(el('p', { class: 'muted', style: 'margin-top:-6px' },
      btn({ class: 'btn ghost small', onclick: () => go('review') },
        'I have longer after all — show me the whole day')));
  }
  page.append(studyNote());
  // An empty deck is good news, and the page should sound like it knows that
  // — one Guide-flavored wink, then the honest reason to come back.
  if (!data.cards.length) {
    page.append(emptyLeaf('review', 'The deck rests ✦',
      'Every card is exactly where it should be — filed, remembered, mostly harmless. '
      + (data.stats.next_due != null
        ? 'The next one comes back ' + whenDay(data.stats.next_due) + '.'
        : 'Learn something new today and the book will have more to bring back tomorrow.')));
    return;
  }
  // The deck is a physical thing: the card you are on sits on top of the ones
  // still to come, and the stack visibly thins as you work through it. "Card
  // 3 of 24" tells you the same fact, but you have to read it.
  const deck = el('div', { class: 'deck' });
  page.append(deck);
  let idx = 0;
  let _cardShownAt = 0;
  let stage = null;
  function draw() {
    _cardShownAt = Date.now();
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
      'Card ' + (idx + 1) + ' of '
        + (bottom < data.cards.length ? bottom + ' for today' : String(data.cards.length))
        + (c.article ? ' · ' + c.article : ''));
    stage.append(progress);
    // The count above says where the bottom is; the bar shows it coming.
    stage.append(el('div', { class: 'bar deck-bar', role: 'img',
      'aria-label': idx + ' of ' + bottom + ' turned' },
      el('span', { style: `width:${Math.round(100 * idx / Math.max(bottom, 1))}%` })));
    // Every card announces its own count — including the first, which used
    // to leave the reader parked on #page hearing only the generic page
    // label while every later card said "Card N of M". The 20ms delay lands
    // after renderRoute's own page.focus(), so the specific label wins.
    setTimeout(() => progress.focus(), 20);
    // Where the answer and the grading buttons will go. Mounted empty and
    // filled later, so assistive tech has a region to announce into.
    var answerRegion = el('div', { class: 'reveal-region', role: 'status', 'aria-live': 'polite' });
    /* Hear the question, hear the answers, touch one. Flip-and-rate-yourself is
       the weakest retrieval act there is even for an adult, and for a reader at
       stage 0-1 it is not an act at all: nothing on the card could be read, the
       back was written and never spoken, and the four grades were English words
       asking a five-year-old to appraise her own memory. Below stage 2 the card
       asks her to produce the answer first — every part of it out loud, because
       this is the surface her whole streak is built on and she has never been
       able to work it. Stage 2 and up are untouched: SM-2 self-grading is the
       rhythm an older reader already has.

       The distractor is drawn from the deck in hand, preferring a sibling from
       the same node or article (due_cards interleaves them, learner.py:1097) —
       a card from a wildly different topic makes the choice free. */
    const distractor = S.stage <= 1 && data.cards.length > 1 ? distractorFor(c) : null;
    const opts = distractor ? (Math.random() < 0.5 ? [c.back, distractor] : [distractor, c.back]) : null;
    const askAloud = () => opts ? c.front + '. Is it ' + opts[0] + ', or ' + opts[1] + '?' : c.front;
    const promptRow = el('div', { class: 'speak-row' }, S.stage <= 2 ? speakBtn(askAloud, 'Read the card aloud') : null, el('div', { class: 'q-prompt', style: 'min-height:60px;flex:1' }, c.front));
    stage.append(promptRow);
    answerRegion.className = 'q-explain reveal-region';
    answerRegion.style.fontSize = '16px';
    // With two answers on offer the reader's job is to choose one, so the way
    // out becomes the quiet control and the answers become the loud ones.
    const showBtn = btn({ class: 'btn js-show-answer ' + (opts ? 'ghost small' : 'gold'), style: opts ? null : 'width:100%',
      onclick: () => { showBtn.disabled = true; revealBack(c, answerRegion, null, writeIn && writeIn.value.trim()); } },
      'Show answer ', el('kbd', { class: 'key-hint', 'aria-hidden': 'true' }, 'space'));
    if (opts) {
      const recallRow = el('div', { class: 'recall-row', role: 'group', 'aria-label': 'Which one is it?' });
      opts.forEach((text, k) => {
        const b = btn({ class: 'recall-opt',
          onclick: () => answerRecall(c, b, recallRow, answerRegion, sameText(text, c.back)) },
          el('span', { class: 'ro-key', 'aria-hidden': 'true' }, String(k + 1)),
          el('span', { class: 'ro-text' }, text));
        recallRow.append(b);
      });
      stage.append(el('p', { class: 'muted recall-ask' }, 'Which one is it?'), recallRow);
    }
    /* Flip-and-rate-yourself is, in the words of the comment above this one,
       the weakest retrieval act there is — and until now stage 2 and up got
       nothing else. The fix below stage 2 was a forced choice; a forced choice
       for an adult would be *worse*, because recognising one of two answers is
       easier than recalling one. So the older reader is asked to produce
       instead: say it, or write it, before the card turns. Writing is optional
       on purpose — saying it out loud is real retrieval and the book cannot
       hear it — but the field is there, and what the reader put in it is shown
       beside the answer, so the self-grade that follows is a comparison rather
       than a memory of having felt confident. */
    let writeIn = null;
    if (!opts && S.stage >= 2) {
      writeIn = el('input', { type: 'text', class: 'recall-write', 'aria-label': 'Your answer, before you turn the card',
        placeholder: 'Say it out loud, or write it here…',
        onkeydown: e => { if (e.key === 'Enter' && !showBtn.disabled) { e.preventDefault(); showBtn.click(); } } });
      stage.append(writeIn);
    }
    stage.append(showBtn);
    stage.append(answerRegion);
    // One utterance, not two: the question and the two answers travel together
    // so the queue is never cancelled halfway by the second call.
    if (S.stage <= 1) maybeSpeak(askAloud());
  }
  /* A session that ends because it is FINISHED is the strongest single
     predictor of the book being opened again tomorrow, and an infinite queue
     can never end that way — a two-hundred-card backlog just becomes a wall to
     fail against. So the day has a floor and a ceiling: when the ask is met and
     cards remain, the deck says so and offers the way out first. */
  function stopPanel() {
    // A fresh node, never an innerHTML mutation: the settle animation only
    // plays for an element ENTERING the DOM, so mutating the card in place
    // would leave "Keep going" resuming into an animation that never fires.
    const panel = el('div', { class: 'card deck-card deck-stop' });
    if (stage) stage.replaceWith(panel); else deck.append(panel);
    stage = panel;
    // The stack behind the card still has to show what is genuinely left.
    deck.dataset.depth = String(Math.max(0, Math.min(2, data.cards.length - idx)));
    const left = Math.max(0, (data.stats.due || data.cards.length) - idx);
    const head = el('h3', { class: 'stop-head', tabindex: '-1' }, 'A good place to stop ✦');
    panel.append(el('div', { class: 'el-mark', 'aria-hidden': 'true' }, glyph('crown', 30)), head,
      el('p', { class: 'muted stop-body' },
        'That is ' + idx + (idx === 1 ? ' card' : ' cards') + ' turned — every one of them a little harder to forget.'
        + (left ? ' ' + left + ' more are waiting, and they will still be here tomorrow.' : '')));
    const out = btn({ class: 'btn gold', onclick: () => go('today') }, 'Close the deck');
    // The way out takes focus. Defaulting to "Keep going" would quietly turn a
    // stopping point into an upsell, which is the opposite of the point.
    panel.append(el('div', { class: 'stop-row' }, out,
      btn({ class: 'btn ghost', onclick: () => { bottom = data.cards.length; draw(); } }, 'Keep going')));
    setTimeout(() => out.focus(), 20);
  }
  const sameText = (a, b) => String(a == null ? '' : a).trim().toLowerCase() === String(b == null ? '' : b).trim().toLowerCase();
  function writeInFor(st) { return st ? st.querySelector('.recall-write') : null; }
  function distractorFor(c) {
    const others = data.cards.filter(x => x.id !== c.id && !sameText(x.back, c.back));
    if (!others.length) return null;
    const kin = others.filter(x => (c.node_id && x.node_id === c.node_id) || (c.article && x.article === c.article));
    const pool = kin.length ? kin : others;
    return pool[Math.floor(Math.random() * pool.length)].back;
  }
  function answerRecall(c, chosen, row, region, ok) {
    // Never colour-only: the chosen button takes a ✓ or ✗, and when it is wrong
    // the right one is marked too, so the card teaches rather than only scores.
    row.querySelectorAll('.recall-opt').forEach(b => {
      b.disabled = true;
      const isKey = sameText(b.querySelector('.ro-text').textContent, c.back);
      if (b === chosen) { b.classList.add(ok ? 'correct' : 'wrong'); b.prepend(ok ? '✓ ' : '✗ '); }
      else if (!ok && isKey) { b.classList.add('correct'); b.prepend('✓ '); }
    });
    const show = stage.querySelector('.js-show-answer');
    if (show) show.disabled = true;
    haptic(ok ? 'ok' : 'no');
    revealBack(c, region, ok ? 4 : 2);
  }
  function revealBack(c, region, decided, wrote) {
    // Write into the region that is already on the page rather than inserting a
    // pre-filled one: a live region that arrives with its text already in it is
    // announced unreliably, or not at all.
    region.textContent = c.back;
    // What the reader actually produced, set beside the key. Appended AFTER
    // the region's own text so the live announcement leads with the answer.
    if (wrote) {
      const mine = el('p', { class: 'muted wrote-line' }, 'You said: ' + wrote);
      region.append(mine);
    }
    if (writeInFor(stage)) writeInFor(stage).disabled = true;
    // Whichever route turned the card — a produced answer or "Show answer" —
    // the choice is over, so the row goes down here rather than at each caller.
    if (stage) stage.querySelectorAll('.recall-opt').forEach(b => { b.disabled = true; });
    // The front is spoken when the card is drawn; the back was written and
    // never said, which left the flip — the whole point of the deck — silent
    // for the reader who cannot read it. maybeSpeak, not speakText: this is the
    // book talking unprompted, and the voice toggle governs it.
    if (S.stage <= 1) maybeSpeak(decided == null ? c.back
      : (decided >= 4 ? 'Yes. ' + c.back : 'Not yet. It is ' + c.back));
    let row;
    if (decided != null) {
      // She produced the answer, so the grade is already settled. What is left
      // is the beat that lets her see and hear it before the deck moves on.
      row = el('div', { class: 'grade-row', role: 'group', 'aria-label': 'When you are ready' },
        btn({ class: 'btn gold js-next-card', style: 'width:100%', onclick: () => grade(c, decided) },
          'Next card ✦ ', el('kbd', { class: 'key-hint', 'aria-hidden': 'true' }, 'space')));
    } else if (S.stage <= 1) {
      // The two-glyph pair already written for the quiz confidence row. Four
      // words rating your own memory is not a judgement a five-year-old can
      // make, let alone read.
      row = el('div', { class: 'grade-row', role: 'group', 'aria-label': 'Did you know it?' },
        btn({ class: 'btn small grade-btn grade-hard', onclick: () => grade(c, 2) },
          glyph('unsure', 18), ' Not yet ', el('kbd', { class: 'key-hint', 'aria-hidden': 'true' }, '1')),
        btn({ class: 'btn small grade-btn grade-good', onclick: () => grade(c, 4) },
          glyph('known', 18), ' I knew it ', el('kbd', { class: 'key-hint', 'aria-hidden': 'true' }, '2')));
    } else {
      const grades = [[0, 'Blank', 'grade-blank'], [3, 'Hard', 'grade-hard'], [4, 'Good', 'grade-good'], [5, 'Easy', 'grade-easy']];
      row = el('div', { class: 'grade-row', role: 'group', 'aria-label': 'How well did you recall?' });
      grades.forEach(([q, label, cls], k) => row.append(btn({ class: 'btn small grade-btn ' + cls, onclick: () => grade(c, q) },
        label + ' ', el('kbd', { class: 'key-hint', 'aria-hidden': 'true' }, String(k + 1)))));
    }
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
      if (show) { e.preventDefault(); show.click(); return; }
      // Once the card is turned, the same key is the way on to the next one.
      const nxt = stage.querySelector('.js-next-card:not([disabled])');
      if (nxt) { e.preventDefault(); nxt.click(); }
    } else if (/^[1-4]$/.test(e.key)) {
      // There are three layouts now, not one: four self-grades at stage 2 and
      // up, two glyphed ones below it, and — before the card is turned — the
      // two produced answers. Indexing the four grade class names positionally
      // did nothing at all on either of the other two, silently.
      const graded = stage.querySelectorAll('.grade-btn');
      const opts = graded.length ? graded : stage.querySelectorAll('.recall-opt');
      const b = opts[+e.key - 1];
      if (b && !b.disabled) { e.preventDefault(); b.click(); }
    }
  }
  // One live handler at a time: the end-of-deck path re-enters renderReview
  // without passing through renderRoute, so clear any predecessor here.
  if (_reviewKeyHandler) document.removeEventListener('keydown', _reviewKeyHandler);
  _reviewKeyHandler = onKey;
  document.addEventListener('keydown', onKey);
  async function grade(c, q) {
    let r;
    // How long this card took, so the book can eventually tell this reader
    // how long five of them will take *them*. Clamped and discarded server
    // side if it is not a plausible reading; nothing about the schedule, the
    // grade or the XP depends on it.
    const took = _cardShownAt ? (Date.now() - _cardShownAt) / 1000 : null;
    try {
      r = await api.post('/api/review', { card_id: c.id, quality: q, seconds: took });
    } catch (e) {
      toast('The book could not file that one — the card stays right where it is. Nothing is lost.');
      return;  // never silently drop the card
    }
    if (r.xp_gained) flyXP(r.xp_gained);
    if (r.next_days >= 1) toast('Back in ' + Math.round(r.next_days) + (r.next_days < 2 ? ' day' : ' days'));
    else toast('Back again in a few minutes — this one is still settling.');
    idx++;
    if (idx >= bottom && idx < data.cards.length) { stopPanel(); refreshStats(); return; }
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
      const src = r.source === 'live' ? 'Wikipedia' : (String(r.source).includes('simple') ? 'Simple English' : 'Your shelf');
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
async function surprise() { try { const r = await api.get('/api/random'); if (r.title) go('reader', r.title); } catch (e) { toast('The dice need a shelf to land on — the book is not carrying a volume yet.'); } }

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

/* ---------------- account ----------------
   Google sign-in is a layer inside the password gate, not a replacement for
   it: signing in keeps a profile safe across devices and browsers, but the
   book opens and works with none at all. Whoever a session belongs to sees
   this page render the same either way — signed out, freshly signed in with
   an empty profile of their own, or a claimant of the one profile this copy
   started with. */
async function renderAccount(page) {
  const acct = await guard(page, () => api.get('/api/account'));
  if (!acct) return;
  page.append(pagehead('Whose book this is', 'Account',
    'Sign in with Google to keep this profile — its mastery, its streak, its ' +
    'story — tied to your account rather than just this browser. The book ' +
    'still opens, and still remembers, with no account at all.'));

  const idCard = el('div', { class: 'card' });
  if (acct.signed_in) {
    const who = acct.name || acct.email || 'a Google account';
    idCard.append(
      el('p', {}, 'Signed in as ', el('b', {}, who),
        acct.name && acct.email ? ' (' + acct.email + ')' : ''),
      btn({ class: 'btn ghost', onclick: async () => {
        try { await api.post('/api/account/sign-out'); toast('Signed out.'); boot(); }
        catch (e) { toast('That did not take just now — try once more.'); }
      } }, 'Sign out'));
    if (acct.claimable) {
      idCard.append(
        el('p', { class: 'muted', style: 'margin-top:14px' },
          'This copy still holds its original, un-claimed profile — the one ' +
          'every reader here had before accounts existed. Claim it to make ' +
          'it permanently, only yours.'),
        btn({ class: 'btn gold', onclick: () => claimModal(() => boot()) },
          'Claim this profile'));
    }
  } else {
    idCard.append(
      el('p', { class: 'muted' },
        'Not signed in. Without an account, this profile lives in this ' +
        'browser alone — sign in to keep it safe if you ever change devices.'),
      btn({ class: 'btn gold', onclick: () => {
        location.assign('/auth/google/start?next=' + encodeURIComponent('#/account'));
      } }, 'Sign in with Google'));
  }
  page.append(idCard);

  page.append(sectionLabel('Level, by subject'));
  page.append(el('p', { class: 'epigraph' },
    'The book places you by age at the start, and by what you go on to prove. ' +
    'Slide a subject ahead or behind that on its own — the rest keep the ' +
    'level everything else uses.'));

  const prof = S.state.profile;
  const chosen = new Set(prof.domains || []);
  const domains = chosen.size ? S.domains.filter(d => chosen.has(d.id)) : S.domains;
  if (!domains.length) {
    page.append(emptyLeaf('path', 'No subjects chosen yet',
      'Choose a field from your profile and its slider will appear here.'));
    return;
  }
  const domainStage = Object.assign({}, (prof.settings || {}).domain_stage || {});
  async function save(domainId, stage) {
    domainStage[domainId] = stage;
    try {
      await api.post('/api/profile/settings', { domain_stage: domainStage });
      S.state = await api.get('/api/state');
    } catch (e) { toast('That level did not save just now — try nudging it again.'); }
  }
  const slidersCard = el('div', { class: 'card' });
  domains.forEach(d => {
    const current = Number.isFinite(domainStage[d.id]) ? domainStage[d.id] : (prof.stage || 0);
    const out = el('b', {}, STAGE_NAMES[current]);
    const input = el('input', {
      type: 'range', min: 0, max: 5, step: 1, value: current,
      'aria-label': d.name + ' level', 'aria-valuetext': STAGE_NAMES[current],
      oninput: e => {
        syncRangeFill(e.target);
        const v = +e.target.value;
        out.textContent = STAGE_NAMES[v];
        e.target.setAttribute('aria-valuetext', STAGE_NAMES[v]);
      },
      onchange: e => save(d.id, +e.target.value),
    });
    slidersCard.append(el('label', { class: 'field', style: 'margin-bottom:16px;display:block' },
      el('span', { style: 'display:flex;justify-content:space-between;align-items:center' },
        el('span', {}, domainMark(d, 15), ' ' + d.name), out),
      input));
  });
  slidersCard.querySelectorAll('input[type=range]').forEach(syncRangeFill);
  page.append(slidersCard);
}

function claimModal(onDone) {
  openModal({
    label: 'Claim this profile', dismissable: true,
    build: (modal, close) => {
      let value = '';
      const input = el('input', {
        type: 'password', 'aria-label': 'The access word', autocomplete: 'off',
        placeholder: 'The book’s access word',
        oninput: e => { value = e.target.value; err.textContent = ''; },
        onkeydown: e => { if (e.key === 'Enter') { e.preventDefault(); submit(); } },
      });
      const err = el('p', { class: 'muted', style: 'color:var(--accent)' });
      async function submit() {
        try {
          await api.post('/api/account/claim', { password: value });
          close();
          toast('This profile is now yours to keep.');
          onDone();
        } catch (e) {
          err.textContent = (e && e.error) || 'That did not work — try again.';
        }
      }
      modal.append(
        el('div', { class: 'kicker' }, 'One-way'),
        el('h2', { style: 'margin-top:4px' }, 'Make this profile yours'),
        el('p', { class: 'muted' },
          'Enter the book’s own access word once more, as proof you are meant ' +
          'to keep this history — not a new password, the same one that let you in.'),
        el('label', { class: 'field' }, input), err,
        el('div', { style: 'display:flex;gap:10px;margin-top:14px' },
          btn({ class: 'btn ghost', onclick: close }, 'Not now'),
          btn({ class: 'btn gold', style: 'flex:1', onclick: submit }, 'Claim it')));
      setTimeout(() => input.focus(), 0);
    },
  });
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
// Shelf room, said the way a person says it. 0.94 GB is a number off a
// manifest; "about a gigabyte" is what you tell someone deciding.
function shelfRoom(gb) {
  const n = Number(gb) || 0;
  // "About a gigabyte" for a 0.4 GB volume is a small lie, and the book does
  // not tell those; below a gigabyte the honest, decision-shaped answer is
  // that it is under one.
  if (n < 1) return 'under a gigabyte';
  if (n < 10) return 'about ' + (Math.round(n * 10) / 10) + ' GB';
  return 'about ' + Math.round(n) + ' GB';
}
async function renderLibrary(page) {
  const data = await guard(page, () => api.get('/api/library'));
  if (!data) return;
  page.append(pagehead('The book contains other books', 'The Shelf',
    'Whole libraries can be bound into this one and kept — every page of them yours, with no wire and no one\u2019s permission. Choose what you would like the book to carry.'));
  page.append(el('p', { class: 'epigraph' }, 'A vault does not ask permission to remember. Once shelved, always at hand — no wire required.'));
  const st = data.status;
  page.append(el('div', { class: 'card' },
    el('b', {}, glyph('shelf', 16), ' On your shelf: ' + (st.archives.length || 'no') + ' volume' + (st.archives.length === 1 ? '' : 's')),
    // Room and page-count stay: a reader deciding whether to give up sixty
    // gigabytes of their machine is owed the number. It is the register
    // around the number that had to change — "Installed", "archive", "MB".
    el('p', { class: 'muted', style: 'margin:4px 0 0' }, st.archives.map(a => a.title + ' — ' + a.articles.toLocaleString() + ' entries, ' + shelfRoom(a.size_mb / 1024) + ' of room').join(' · ') || 'Nothing bound in yet.'),
    el('p', { class: 'muted', style: 'margin:6px 0 0' }, st.cached_articles === 1
      ? 'One further page has been copied down from your reading and kept.'
      : st.cached_articles.toLocaleString() + ' further pages have been copied down from your reading and kept.')));
  // A download can run for minutes to hours, polled by wiping and rebuilding
  // this whole page every 3s — the same shape of update Look Up's results
  // and the tutor's replies already learned to announce, just never carried
  // here: a screen-reader user watching a download had no way to know it was
  // moving, or had finished, until they happened to re-visit the page.
  const say = el('div', { class: 'lib-live', role: 'status', 'aria-live': 'polite' });
  page.append(say);
  data.catalog.forEach(item => {
    const c = el('div', { class: 'card lib-item' });
    // The catalogue blurb ends in its own "~110 GB."; the button beside it now
    // says the same thing in the book's words, and saying it twice in two
    // registers is exactly the seam this round is closing.
    const meta = el('div', { class: 'meta' }, el('b', {}, item.title),
      el('p', {}, String(item.blurb).replace(/\s*~[\d.]+\s*GB\.?\s*$/, '')));
    const right = el('div', {});
    if (item.installed) right.append(el('span', { class: 'badge installed' }, '✓ On your shelf'));
    else if (item.download && item.download.status === 'downloading') {
      const pct = item.download.total ? Math.round(100 * item.download.bytes / item.download.total) : 0;
      right.append(el('span', { class: 'badge big' }, 'Copying in — ' + pct + '%'), el('div', { class: 'bar', style: 'width:120px;margin-top:6px' }, el('span', { style: `width:${pct}%` })));
    } else right.append(btn({ class: 'btn small', onclick: () => downloadArchive(item.key) }, 'Copy it in · ' + shelfRoom(item.approx_gb)));
    c.append(meta, right); page.append(c);
  });
  // A colophon, which is what a book calls the note about where its pages came
  // from. The names stay — Wikipedia and Kiwix are owed attribution, and the
  // book is not in the business of pretending it wrote the encyclopedia — but
  // they are set as a credit rather than as a system requirements panel.
  page.append(el('p', { class: 'muted colophon', style: 'margin-top:14px' },
    'These volumes are copied in from Wikipedia and its sister works, carried by the Kiwix project, which keeps them free for anyone to hold. The complete English edition with pictures asks for about 110 GB of room; without pictures, about 60; the Simple English edition, one to three.'));
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
    setTimeout(() => { say.textContent = 'Copying in: ' + named.join(', '); }, 30);
    setTimeout(() => { if (S.view === 'library') renderRoute(); }, 3000);
  }
}
async function downloadArchive(key) {
  try {
    const r = await api.post('/api/library/download', { key });
    // The refusal reason ("unknown catalog key", "could not resolve download
    // URL (offline?)") is a note between the book and its own machinery. The
    // reader gets the book's sentence; the diagnosis goes to the console,
    // where whoever is debugging can still read it.
    if (r.error) { console.warn('[primer] shelf refused:', r.error); toast('The book could not begin that volume just now — nothing is lost, and you can ask again.'); return; }
    toast('The book has begun copying it in. Go on reading — it copies while you read.'); renderRoute();
  }
  catch (e) { toast('The shelf is out of reach — likely the network, never you. The book will fetch it when you are back online.'); }
}

/* ---------------- accessible modal ---------------- */
let _modalStack = [];
function closeBtn(close) { return btn({ class: 'modal-close', 'aria-label': 'Close', title: 'Close (Esc)', onclick: close }, '×'); }
function openModal({ label, build, dismissable = false, dismissLabel = 'Close', dark = false, onClose = null }) {
  const prevFocus = document.activeElement;
  const ov = el('div', { id: 'overlay' });
  const modal = el('div', { class: 'modal', role: 'dialog', 'aria-modal': 'true', 'aria-label': label || 'Dialog', tabindex: '-1' });
  // Same story as the chapter card: the dark modal is a chrome surface, and
  // hardcoding its brown left it behind when the night palette turned.
  if (dark) modal.classList.add('on-dark');
  // Fires once, however the dialog was dismissed — button, Escape, or the
  // scrim. Ceremonies queue on this: a stage ascension that arrives while the
  // reader is mid-chapter has to wait for the chapter, not land on top of it.
  let closed = false;
  function close() {
    ov.remove(); _modalStack = _modalStack.filter(m => m !== entry);
    document.removeEventListener('keydown', onKey);
    if (prevFocus && prevFocus.focus) prevFocus.focus();
    if (!closed) { closed = true; if (onClose) onClose(); }
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
