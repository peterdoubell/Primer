import { align, containsWords, prompts, tokens } from './compare.mjs';

const get = (id) => document.getElementById(id);
const keys = ['nicolay', 'hay'];
const catalogHash = '830e47b09146373c4f71012a1e011da75d512af19e6c98af20be36680dd36ab8';
let catalog,
  question = 0;
const nativeSize = { nicolay: false, hay: false };
const bandIndex = { nicolay: 0, hay: 0 };
const views = {};
function el(tag, text) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  return n;
}
function passage(key, ix) {
  const w = catalog.witnesses[key],
    spec = w.passages[ix];
  return w.transcript.slice(spec.start, spec.end).trim();
}
function markDifferences(text, ts, shared) {
  const frag = new DocumentFragment();
  let at = 0;
  for (const [i, t] of ts.entries()) {
    frag.append(
      text.slice(at, t.start),
      shared.has(i) ? document.createTextNode(t.text) : el('mark', t.text)
    );
    at = t.end;
  }
  frag.append(text.slice(at));
  return frag;
}
function drawPhoto(key) {
  const v = views[key],
    ix = Number(get('passage').value),
    witness = catalog.witnesses[key];
  const bands = witness.passages[ix].bands,
    band = bands[bandIndex[key]],
    page = witness.pages[band.page - 1];
  const whole = get('framing').value === 'page';
  const top = whole ? 0 : Math.max(0, band.top - 15),
    bottom = whole ? page.height : Math.min(page.height, band.bottom + 15);
  v.photo.style.width = nativeSize[key] ? page.width + 'px' : '100%';
  v.photo.style.aspectRatio = page.width + ' / ' + (bottom - top);
  v.image.style.top = (-100 * top) / (bottom - top) + '%';
  if (v.image.getAttribute('src') !== page.image) v.image.src = page.image;
  v.image.alt = witness.title + ', page ' + page.number + ' of 2, Lincoln’s handwriting.';
  v.outline.style.top = (100 * (band.top - top)) / (bottom - top) + '%';
  v.outline.style.height = (100 * (band.bottom - band.top)) / (bottom - top) + '%';
  v.caption.textContent = 'Page ' + page.number + ' of 2 · ' + catalog.passages[ix];
  v.size.textContent = nativeSize[key] ? 'Fit page width' : 'Read at native size';
  v.size.setAttribute('aria-pressed', String(nativeSize[key]));
  v.other.hidden = bands.length < 2;
  if (bands.length > 1) v.other.textContent = 'Read the lines on page ' + bands[1 - bandIndex[key]].page;
  v.original.href = page.source;
  const detail = witness.passages[ix].revision;
  v.revision.hidden = !detail || detail.page !== band.page;
  if (!v.revision.hidden) {
    const [left, y0, right, y1] = detail.box;
    v.note.textContent = detail.description;
    v.cut.style.aspectRatio = right - left + ' / ' + (y1 - y0);
    v.cut.style.maxWidth = (right - left) * 1.5 + 'px';
    v.cutImage.src = page.image;
    v.cutImage.alt = detail.description;
    v.cutImage.style.width = (100 * page.width) / (right - left) + '%';
    v.cutImage.style.left = (-100 * left) / (right - left) + '%';
    v.cutImage.style.top = (-100 * y0) / (y1 - y0) + '%';
  }
  v.scroller.scrollLeft = 0;
}
function makeWitness(key) {
  const witness = catalog.witnesses[key],
    section = el('section');
  section.className = 'witness ' + key;
  const heading = el('h2', witness.title),
    text = el('blockquote');
  const figure = el('figure');
  figure.className = 'facsimile';
  const scroller = el('div');
  scroller.className = 'page-scroll';
  scroller.tabIndex = 0;
  scroller.setAttribute('role', 'region');
  scroller.setAttribute('aria-label', witness.title + ' manuscript image');
  const photo = el('div');
  photo.className = 'photo';
  const image = el('img'),
    outline = el('span');
  outline.className = 'band';
  outline.setAttribute('aria-hidden', 'true');
  photo.append(image, outline);
  scroller.append(photo);
  const caption = el('figcaption');
  figure.append(scroller, caption);
  const choices = el('div');
  choices.className = 'choices';
  const size = el('button'),
    other = el('button'),
    original = el('a', 'Original page image');
  size.type = other.type = 'button';
  size.addEventListener('click', () => {
    nativeSize[key] = !nativeSize[key];
    drawPhoto(key);
  });
  other.addEventListener('click', () => {
    bandIndex[key] = 1 - bandIndex[key];
    drawPhoto(key);
  });
  choices.append(size, other);
  const revision = el('details');
  const cut = el('div');
  cut.className = 'detail-cut';
  const cutImage = el('img'),
    note = el('p');
  cut.append(cutImage);
  revision.append(el('summary', 'Inspect a handwritten correction'), cut, note);
  section.append(heading, text, figure, choices, revision, original);
  get('witnesses').append(section);
  views[key] = {
    text,
    scroller,
    photo,
    image,
    outline,
    caption,
    size,
    other,
    original,
    revision,
    cut,
    cutImage,
    note
  };
  const complete = el('section');
  complete.append(el('h3', witness.title));
  const full = el('p', witness.transcript);
  full.className = 'complete-text';
  const source = el('a', 'Library of Congress transcription');
  source.href = witness.transcriptURL;
  complete.append(full, source);
  get('complete').append(complete);
}
function render(resetPages = false) {
  const ix = Number(get('passage').value),
    punctuation = get('unit').value === 'punct',
    matchCase = get('case').value === 'exact';
  const texts = keys.map((k) => passage(k, ix));
  const lists = texts.map((text) => tokens(text, punctuation, matchCase)),
    matched = align(...lists);
  const countRows = keys.map((k, i) => {
    if (resetPages) bandIndex[k] = 0;
    views[k].text.replaceChildren(
      markDifferences(texts[i], lists[i], new Set(matched.map((pair) => pair[i])))
    );
    drawPhoto(k);
    const tr = el('tr'),
      th = el('th', catalog.witnesses[k].title);
    th.scope = 'row';
    tr.append(
      th,
      el('td', matched.length),
      el('td', lists[i].length - matched.length),
      el('td', lists[i].length)
    );
    return tr;
  });
  get('counts').replaceChildren(...countRows);
  const gaps = [];
  let previous = [-1, -1];
  for (const pair of [...matched, lists.map((list) => list.length)]) {
    const readings = pair.map((end, side) => {
      const first = previous[side] + 1;
      if (first === end) return '';
      return texts[side].slice(lists[side][first].start, lists[side][end - 1].end);
    });
    if (readings.some(Boolean)) {
      const tr = el('tr'),
        th = el('th', previous[0] < 0 ? 'Start of passage' : lists[0][previous[0]].text);
      th.scope = 'row';
      tr.append(th, ...readings.map((reading) => el('td', reading || '—')));
      gaps.push(tr);
    }
    previous = pair;
  }
  get('no-variants').hidden = gaps.length > 0;
  get('variants').hidden = gaps.length === 0;
  get('variant-rows').replaceChildren(...gaps);
  get('back').disabled = ix === 0;
  get('next').disabled = ix === catalog.passages.length - 1;
  get('status').textContent =
    ix +
    1 +
    ' of ' +
    catalog.passages.length +
    ' · ' +
    catalog.passages[ix] +
    '. ' +
    matched.length +
    ' matching ' +
    (punctuation ? 'tokens' : 'words') +
    ' in order.';
}
function setPassage(ix) {
  get('passage').value = String(ix);
  render(true);
}
function ask() {
  const q = prompts[question];
  get('feedback').textContent = '';
  get('question').textContent =
    'In “' + catalog.passages[q.passage] + '”, which draft uses the words “' + q.phrase + '”?';
  get('answers').replaceChildren(
    ...['Nicolay only', 'Hay only', 'Both'].map((text, choice) => {
      const btn = el('button', text);
      btn.type = 'button';
      btn.addEventListener('click', () => {
        const present = keys.map((k) => containsWords(passage(k, q.passage), q.phrase));
        const correct = present.every(Boolean) ? 2 : present[0] ? 0 : 1;
        get('feedback').textContent =
          choice === correct
            ? 'Correct. ' +
              (choice === 2 ? 'Both drafts contain “' : text + ' contains “') +
              q.phrase +
              '” in this passage.'
            : 'Look at the corresponding lines in both manuscripts and try again.';
        setPassage(q.passage);
      });
      return btn;
    })
  );
}
get('passage').addEventListener('change', () => render(true));
for (const id of ['unit', 'case', 'framing']) get(id).addEventListener('change', () => render());
get('back').addEventListener('click', () => setPassage(Number(get('passage').value) - 1));
get('next').addEventListener('click', () => setPassage(Number(get('passage').value) + 1));
get('show-reading').addEventListener('click', () => setPassage(prompts[question].passage));
get('new-question').addEventListener('click', () => {
  question = (question + 1) % prompts.length;
  ask();
  setPassage(prompts[question].passage);
});
async function start() {
  const res = await fetch('witnesses.json');
  if (!res.ok) throw Error('Missing manuscripts');
  const raw = await res.arrayBuffer(),
    hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', raw)), (v) =>
      v.toString(16).padStart(2, '0')
    ).join('');
  if (hash !== catalogHash) throw Error('Manuscript index differs');
  catalog = JSON.parse(new TextDecoder().decode(raw));
  get('passage').replaceChildren(...catalog.passages.map((name, i) => new Option(name, String(i))));
  keys.forEach(makeWitness);
  get('options').disabled = false;
  get('comparisons').hidden = false;
  get('new-question').disabled = get('show-reading').disabled = false;
  ask();
  setPassage(0);
}
start().catch(() => {
  get('status').textContent = 'The manuscripts could not be verified. Reload to try again.';
});
