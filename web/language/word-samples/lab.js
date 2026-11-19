import { frequentForms, localWindow, tokenize, traceWords } from './counts.mjs';

const get = id => document.getElementById(id);
const curve = get('curve');
let chapters = [];
let chapter;
let chapterWords = [];
let words = [];
let trace = [];
let answerGiven = false;

function chart(count) {
  const ctx = curve.getContext('2d');
  const width = curve.clientWidth;
  const height = curve.clientHeight;
  if (!width || !height) return;
  const scale = window.devicePixelRatio || 1;
  curve.width = Math.round(width * scale);
  curve.height = Math.round(height * scale);
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  const left = 43, right = width - 17, top = 14, bottom = height - 42;
  const x = number => left + (right - left) * number / words.length;
  const y = ratio => bottom - (bottom - top) * ratio;
  ctx.font = '12px system-ui';
  ctx.fillStyle = '#344638';
  ctx.textAlign = 'right';
  ctx.strokeStyle = '#c3cbbb';
  for (let tick = 0; tick <= 4; tick++) {
    const ratio = tick / 4;
    ctx.beginPath();
    ctx.moveTo(left,y(ratio));
    ctx.lineTo(right,y(ratio));
    ctx.stroke();
    ctx.fillText(Math.round(100 * ratio) + '%',left - 5,y(ratio) + 4);
  }
  ctx.textAlign = 'center';
  for (let i = 0; i <= 4; i++) {
    const value = Math.round(words.length * i / 4);
    ctx.fillText(String(value),x(value),bottom + 15);
  }
  ctx.fillText('Number of words counted', (left + right) / 2, height - 6);
  function line(key, colour, dash) {
    ctx.strokeStyle = colour;
    ctx.setLineDash(dash);
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    let started = false;
    for (let i = 0; i < count; i++) {
      const value = trace[i][key];
      if (value === null) continue;
      if (started) ctx.lineTo(x(i + 1),y(value));
      else ctx.moveTo(x(i + 1),y(value));
      started = true;
    }
    ctx.stroke();
    if (started) {
      ctx.fillStyle = colour;
      ctx.beginPath();
      ctx.arc(x(count),y(trace[count - 1][key]),3,0,2*Math.PI);
      ctx.fill();
    }
    ctx.setLineDash([]);
  }
  line('ratio','#28634d',[]);
  line('meanLocalRatio','#9b4a28',[6,4]);
}

function displaySample(count) {
  const beginning = words[0].start;
  const end = words.at(-1).end;
  const passage = get('passage');
  if (count === 0) {
    passage.textContent = chapter.text.slice(beginning, end);
    return;
  }
  const current = words[count - 1];
  const mark = document.createElement('mark');
  mark.textContent = current.text;
  passage.replaceChildren(chapter.text.slice(beginning,current.start), mark,
    chapter.text.slice(current.end,end));
  // Keep the highlighted token in view inside the passage without moving the page.
  const box = passage.getBoundingClientRect();
  const target = mark.getBoundingClientRect();
  if (target.top < box.top || target.bottom > box.bottom) {
    passage.scrollTop += target.top - box.top - box.height / 2;
  }
}

function updateCount() {
  const count = get('cursor').valueAsNumber;
  const result = trace[count - 1];
  get('counted').textContent = count + ' / ' + words.length;
  get('types').textContent = result?.types ?? 0;
  get('ratio').textContent = result ? (result.ratio * 100).toFixed(1) + '%' : '—';
  get('local-ratio').textContent = result?.meanLocalRatio != null
    ? (result.meanLocalRatio * 100).toFixed(1) + '%' : 'After ' + localWindow + ' words';
  get('current').textContent = result ? 'Word ' + count + ' is “' + words[count-1].text + '”. '
    + (result.count === 1 ? 'Its first appearance adds a new form.' :
      'Its first appearance was at word ' + (result.first + 1) + '. It has now appeared ' + result.count + ' times.') : '';
  get('question').textContent = count === words.length ? 'Every word in this sample has been counted.'
    : 'Word ' + (count + 1) + ' is “' + words[count].text + '”. Is this its first appearance in this sample?';
  get('new').disabled = get('repeat').disabled = count === words.length || answerGiven;
  get('next').disabled = get('finish').disabled = count === words.length;
  const rows = frequentForms(words, count).slice(0,10).map(([form,total]) => {
    const row = document.createElement('tr');
    const name = document.createElement('th');
    name.scope = 'row'; name.textContent = form;
    row.append(name); row.insertCell().textContent = total;
    return row;
  });
  get('frequent').replaceChildren(...rows);
  displaySample(count);
  chart(count);
}

function seek(count) {
  get('cursor').value = count;
  answerGiven = false;
  get('feedback').textContent = '';
  updateCount();
}

function checkAnswer(prediction) {
  const index = get('cursor').valueAsNumber;
  if (index >= trace.length || answerGiven) return;
  const result = trace[index];
  const newForm = result.count === 1;
  get('feedback').textContent = (newForm === prediction ? 'Correct. ' : 'Look again. ') +
    (newForm ? 'This is the first occurrence of “' + words[index].form + '” in the sample.' :
      '“' + words[index].form + '” first appeared at word ' + (result.first + 1) + '.');
  answerGiven = true;
  updateCount();
}

function showIllustration(index) {
  const figure = chapter.illustrations[index];
  get('illustration').value = index;
  get('picture').sizes = '(max-width: 50rem) 90vw, (max-width: 78rem) 45vw, 36rem';
  get('picture').srcset = figure.file + ' 800w, ' + figure.large + ' 1600w';
  get('picture').src = figure.file;
  get('picture').alt = figure.alt;
  get('picture').width = figure.width;
  get('picture').height = figure.height;
  get('caption').textContent = figure.alt;
}

function changeSample(illustrationIndex) {
  const start = get('start');
  const size = Math.min(Number(get('size').value),chapterWords.length);
  start.max = chapterWords.length - size + 1;
  if (Number.isInteger(illustrationIndex)) {
    const anchor = chapter.illustrations[illustrationIndex].offset;
    let position = chapterWords.findIndex(word=>word.start >= anchor);
    if (position < 0) position = chapterWords.length - 1;
    start.value = Math.max(1, Math.min(Number(start.max), position + 1 - Math.floor(size / 2)));
  }
  const first = start.valueAsNumber - 1;
  words = chapterWords.slice(first, first + size);
  trace = traceWords(words);
  get('cursor').max = words.length;
  get('range').textContent = (first + 1) + '–' + (first + size) + ' of ' + chapterWords.length;
  const midpoint = words[Math.floor(size / 2)].start;
  const closest = chapter.illustrations.reduce((best, figure, i, figures) =>
    Math.abs(figure.offset - midpoint) < Math.abs(figures[best].offset - midpoint) ? i : best, 0);
  showIllustration(Number.isInteger(illustrationIndex) ? illustrationIndex : closest);
  seek(Math.min(get('cursor').valueAsNumber, words.length));
}

function changeChapter(resetStart) {
  chapter = chapters[Number(get('chapter').value)];
  chapterWords = tokenize(chapter.text, get('case').value === 'keep');
  if (resetStart) get('start').value = 1;
  get('illustration').replaceChildren(...chapter.illustrations.map((figure,i) =>
    new Option('Illustration ' + (i+1) + ' of ' + chapter.illustrations.length, i)));
  changeSample();
}

get('chapter').addEventListener('change',()=>changeChapter(true));
get('case').addEventListener('change',()=>changeChapter(false));
get('size').addEventListener('change',()=>changeSample());
get('start').addEventListener('input',()=>changeSample());
get('cursor').addEventListener('input',()=>seek(get('cursor').valueAsNumber));
get('next').addEventListener('click',()=>seek(get('cursor').valueAsNumber+1));
get('finish').addEventListener('click',()=>seek(words.length));
get('new').addEventListener('click',()=>checkAnswer(true));
get('repeat').addEventListener('click',()=>checkAnswer(false));
get('illustration').addEventListener('change',()=>changeSample(Number(get('illustration').value)));

async function start() {
  try {
    const response = await fetch('corpus.json');
    if (!response.ok) throw Error('Source text unavailable.');
    const data = await response.arrayBuffer();
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', data)),
      byte => byte.toString(16).padStart(2, '0')).join('');
    if (digest !== '4dfd4a9a0ea646b6b6f8e4ca67a2400574350647ec7358901a2c1705fa7b4a65') throw Error('Source corpus differs from the edition.');
    chapters = JSON.parse(new TextDecoder().decode(data)).chapters;
    if (chapters.length !== 12 || chapters.some(c=>!c.text || !c.illustrations.length)) throw Error('Incomplete corpus.');
    get('chapter').replaceChildren(...chapters.map((c,i)=>new Option(c.number + '. ' + c.title, i)));
    get('activity').hidden = false;
    get('sample-controls').disabled = false;
    get('load-status').textContent = '12 source chapters · ' +
      chapters.reduce((total,c)=>total+c.illustrations.length,0) + ' chapter illustrations by John Tenniel';
    changeChapter(true);
    seek(25);
    const watcher = new ResizeObserver(()=>chart(get('cursor').valueAsNumber));
    watcher.observe(curve);
  } catch {
    get('load-status').textContent = 'The source text could not be loaded. Reload to try again.';
  }
}
start();
