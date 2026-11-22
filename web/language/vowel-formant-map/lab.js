import { comparison, languages, plotPosition, readTokens, selectTokens, speakerKey, summaries } from './data.mjs';

const get = id => document.getElementById(id);
const controls = ['speaking','l1','vowel','speaker','word','method'];
const palette = { 'En|En':'#186b65', 'Sp|En':'#ae4c22', 'En|Sp':'#6552a3', 'Sp|Sp':'#336fa5' };
const chart = get('space');
const number = value => new Intl.NumberFormat('en', {maximumFractionDigits:2}).format(value);
const summaryName = row => languages[row.speaking] + ' · L1 ' + languages[row.l1] + ' · code ' + row.vowel;
const colour = token => palette[token.l1 + '|' + token.speaking];
let all = [];
let selected = [];
let grouped = [];
let picked = 0;
let plotted = [];
let drawing = false;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function draw() {
  const width = chart.clientWidth;
  const height = chart.clientHeight;
  const ratio = window.devicePixelRatio || 1;
  chart.width = Math.round(width * ratio);
  chart.height = Math.round(height * ratio);
  const context = chart.getContext('2d');
  context.setTransform(ratio,0,0,ratio,0,0);
  const box = {left:51,right:width-16,top:24,bottom:height-45};
  const point = (f1,f2) => plotPosition(f1,f2,box);
  context.fillStyle = '#fffdfa';
  context.fillRect(0,0,width,height);
  context.font = '12px system-ui';
  context.lineWidth = 1;
  for (const f2 of [500,1000,1500,2000,2500,3000]) {
    const {x} = point(0,f2);
    context.strokeStyle = '#dce2e5';
    context.beginPath(); context.moveTo(x,box.top); context.lineTo(x,box.bottom); context.stroke();
    context.fillStyle = '#354d59'; context.textAlign = 'center';
    context.fillText(f2.toString(),x,box.bottom+17);
  }
  for (const f1 of [0,500,1000,1500,2000]) {
    const {y} = point(f1,3400);
    context.strokeStyle = '#dce2e5';
    context.beginPath(); context.moveTo(box.left,y); context.lineTo(box.right,y); context.stroke();
    context.fillStyle = '#354d59'; context.textAlign = 'right';
    context.fillText(f1.toString(),box.left-6,y+4);
  }
  context.fillStyle = '#263844'; context.textAlign = 'left';
  context.fillText('F1 (Hz) ↓',4,14);
  context.textAlign = 'center';
  context.fillText('← F2 (Hz)',(box.left+box.right)/2,height-8);
  plotted = selected.map(token => point(token.f1,token.f2));
  context.globalAlpha = .17;
  selected.forEach((token,index) => {
    context.fillStyle = colour(token);
    context.beginPath(); context.arc(plotted[index].x,plotted[index].y,1.9,0,2*Math.PI); context.fill();
  });
  context.globalAlpha = 1;
  grouped.forEach(row => {
    const {x,y} = point(row.f1,row.f2);
    context.strokeStyle = 'white'; context.lineWidth = 6;
    context.beginPath(); context.moveTo(x-6,y); context.lineTo(x+6,y); context.moveTo(x,y-6); context.lineTo(x,y+6); context.stroke();
    context.strokeStyle = colour(row); context.lineWidth = 2.5; context.stroke();
    if (grouped.length <= 12) {
      context.fillStyle = colour(row); context.textAlign = 'left';
      context.fillText(row.vowel,x+8,y-7);
    }
  });
  if (selected[picked]) {
    const {x,y} = plotted[picked];
    context.beginPath(); context.arc(x,y,6,0,2*Math.PI);
    context.strokeStyle = '#101d28'; context.lineWidth = 2; context.stroke();
    context.beginPath(); context.arc(x,y,3.8,0,2*Math.PI);
    context.strokeStyle = 'white'; context.lineWidth = 1.5; context.stroke();
  }
  chart.setAttribute('aria-label', selected.length.toLocaleString('en') + ' measured vowel tokens and '
    + grouped.length + ' group summaries. F2 increases left and F1 increases downward.');
}

function inspect() {
  const token = selected[picked];
  get('token').value = picked;
  get('previous').disabled = !token || picked === 0;
  get('next').disabled = !token || picked === selected.length-1;
  if (!token) {
    get('token-detail').textContent = 'No tokens match these filters.';
    return;
  }
  const description = number(picked+1) + ' of ' + number(selected.length) + ' · source row ' + token.row
    + ' · word “' + token.word + '” · code ' + token.vowel + ' · ' + languages[token.speaking]
    + ' spoken by ' + token.speaker + ' (L1 ' + languages[token.l1] + ') · F1 ' + token.f1
    + ' Hz · F2 ' + token.f2 + ' Hz · duration ' + token.length*10 + ' ms.';
  get('token-detail').textContent = description;
  get('token').setAttribute('aria-valuetext',description);
  const id = [token.speaking,token.l1,token.vowel].join('|');
  for (const row of get('summaries').rows) row.toggleAttribute('data-picked',row.dataset.summary === id);
}

function inspectAt(index) {
  picked = Math.max(0,Math.min(selected.length-1,index));
  inspect();
  draw();
}

function comparisonQuestion() {
  get('feedback').textContent = '';
  const first = grouped.find(row => row.id === get('first').value);
  const second = grouped.find(row => row.id === get('second').value);
  get('question').textContent = first && second
    ? 'Which summary has the higher ' + get('formant').value.toUpperCase() + ' value?'
    : 'Choose tokens that supply at least two group summaries.';
}

function render() {
  const filters = Object.fromEntries(controls.map(id => [id,get(id).value]));
  selected = selectTokens(all,filters);
  grouped = summaries(selected,filters.method);
  picked = 0;
  get('navigation').disabled = selected.length === 0;
  get('token').max = Math.max(0,selected.length-1);
  get('denominator').textContent = filters.method === 'speakers'
    ? 'For each formant, take a median within each contributing speaker, then the median across those speaker medians. Each speaker contributes one value. The table also shows how many vowel tokens they supplied.'
    : 'For each formant, take the median of all matching vowel tokens in that language, L1 and source-code group. Speakers with more matching tokens contribute more observations.';
  get('summary-caption').textContent = filters.method === 'speakers'
    ? 'Median of speaker medians'
    : 'Medians across tokens';
  get('summaries').replaceChildren(...grouped.map(row => {
    const tr = element('tr');
    tr.dataset.summary = row.id;
    const name = element('th',summaryName(row)); name.scope = 'row';
    tr.append(name,...[row.tokens,row.speakers,row.f1,row.f2].map(value => element('td',number(value))));
    return tr;
  }));
  const pairGroups = [...new Map(selected.map(row => [[row.l1,row.speaking].join('|'),row])).values()];
  get('legend').replaceChildren(...pairGroups.map(row => {
    const label = element('span');
    const swatch = element('i'); swatch.style.background = colour(row); swatch.setAttribute('aria-hidden','true');
    label.append(swatch,document.createTextNode(languages[row.speaking] + ' · L1 ' + languages[row.l1]));
    return label;
  }));
  for (const [index,id] of ['first','second'].entries()) {
    const previous = get(id).value;
    get(id).replaceChildren(...grouped.map(row => new Option(summaryName(row),row.id)));
    get(id).value = grouped.some(row => row.id === previous) ? previous : grouped[Math.min(index,grouped.length-1)]?.id || '';
  }
  get('comparison').disabled = grouped.length < 2;
  comparisonQuestion();
  inspect();
  draw();
  get('status').textContent = number(selected.length) + ' of 55,978 original tokens shown · '
    + new Set(selected.map(speakerKey)).size + ' speakers · ' + grouped.length + ' summaries.';
}

async function digest(bytes) {
  const value = await crypto.subtle.digest('SHA-256',bytes);
  return [...new Uint8Array(value)].map(byte => byte.toString(16).padStart(2,'0')).join('');
}

async function load() {
  get('retry').hidden = true;
  get('status').textContent = 'Verifying the source table…';
  try {
    const metadataResponse = await fetch('source.json');
    if (!metadataResponse.ok) throw Error('Source metadata did not load.');
    const metadata = await metadataResponse.json();
    if (metadata.sourceSHA256 !== '787f99e8d2aa6e0025ba2a864a1f797d1270a5dfafd3cfd06eb76740090a38b6'
        || metadata.asset !== 'vowels.txt.gz' || metadata.rows !== 55978) throw Error('Source metadata differs.');
    const response = await fetch(metadata.asset);
    if (!response.ok) throw Error('The source table did not load.');
    const compressed = await response.arrayBuffer();
    if (compressed.byteLength !== metadata.compressedBytes ||
        await digest(compressed) !== metadata.compressedSHA256) throw Error('The compressed source differs.');
    const raw = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    if (raw.byteLength !== metadata.sourceBytes || await digest(raw) !== metadata.sourceSHA256) throw Error('The source table differs.');
    all = readTokens(new TextDecoder().decode(raw));
    if (all.length !== 55978) throw Error('The source row count differs.');
    get('vowel').replaceChildren(new Option('All source codes',''), ...[...new Set(all.map(row => row.vowel))].sort()
      .map(code => new Option(code,code)));
    get('vowel').value = 'ih';
    const speakers = [...new Map(all.map(token => [speakerKey(token),token])).values()];
    get('speaker').replaceChildren(new Option('All speakers',''), ...speakers.map(row =>
      new Option(languages[row.l1] + ' L1 · ' + row.speaker,speakerKey(row))));
    get('filters').disabled = false;
    render();
  } catch {
    get('status').textContent = 'The original vowel table could not be verified. Retry to load it.';
    get('retry').hidden = false;
  }
}

for (const id of controls) get(id).addEventListener(id === 'word' ? 'input' : 'change',render);
for (const id of ['first','second','formant']) get(id).addEventListener('change',comparisonQuestion);
get('token').addEventListener('input',() => inspectAt(Number(get('token').value)));
get('previous').addEventListener('click',() => inspectAt(picked-1));
get('next').addEventListener('click',() => inspectAt(picked+1));
for (const answer of ['first','second','tie']) get('answer-'+answer).addEventListener('click',() => {
  const first = grouped.find(row => row.id === get('first').value);
  const second = grouped.find(row => row.id === get('second').value);
  const formant = get('formant').value;
  const describe = row => summaryName(row) + ' = ' + number(row[formant]) + ' Hz ('
    + number(row.tokens) + ' tokens; ' + row.speakers + ' speakers)';
  get('feedback').textContent = (comparison(first,second,formant) === answer ? 'Correct. ' : 'Check the two values. ')
    + describe(first) + '. ' + describe(second) + '.';
});
chart.addEventListener('click',event => {
  if (!selected.length) return;
  const bounds = chart.getBoundingClientRect();
  const x = event.clientX-bounds.left, y = event.clientY-bounds.top;
  let best = Infinity, index = 0;
  plotted.forEach((point,i) => {
    const distance = (point.x-x)**2+(point.y-y)**2;
    if (distance < best) { best = distance; index = i; }
  });
  inspectAt(index);
  chart.focus();
});
chart.addEventListener('keydown',event => {
  if (!selected.length || !['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
  event.preventDefault();
  if (event.key === 'Home') inspectAt(0);
  else if (event.key === 'End') inspectAt(selected.length-1);
  else inspectAt(picked+(event.key === 'ArrowRight' ? 1 : -1));
});
window.addEventListener('resize',() => {
  if (drawing) return;
  drawing = true;
  requestAnimationFrame(() => { draw(); drawing = false; });
});
get('retry').addEventListener('click',load);
load();
