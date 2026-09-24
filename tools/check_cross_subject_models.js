#!/usr/bin/env node
'use strict';

// Load the shipped builders and renderer registry; no teaching calculations are
// replaced by mocks. The small DOM below only supplies browser element methods.
const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ROOT = path.resolve(__dirname, '..');
const CROSS_SPATIAL = ['arts.2.color-theory', 'cs.5.quantum'];
const CONCEPTS = ['arts.1.beat', 'lang.2.etymology', 'lang.2.poetry', 'lang.2.novels', 'lang.2.research', 'lang.2.speaking', 'lang.2.grammar', 'lang.2.paragraphs', 'lang.0.phonics', 'lang.1.handwriting', 'lang.0.speaking', 'lang.1.childrens-lit', 'lang.1.writing-stories', 'lang.1.dictionary', 'lang.1.vocabulary', 'lang.1.spelling', 'lang.1.sentences', 'lang.0.rhymes', 'lang.0.stories', 'earth.5.frontier', 'earth.5.earth-systems', 'earth.5.cosmology', 'earth.5.astrobiology', 'earth.4.planetary', 'earth.4.climatology', 'earth.4.oceanatmos', 'earth.4.geophysics', 'earth.4.astrophysics', 'earth.3.astronomy', 'earth.3.ecology-earth', 'earth.3.climate-sci', 'earth.3.space-exploration', 'earth.2.geology', 'earth.2.oceans', 'earth.2.atmosphere', 'earth.2.environment', 'earth.2.planets', 'earth.2.stars', 'earth.0.weather', 'earth.1.solar-system', 'earth.0.land-water', 'earth.1.water-cycle', 'earth.1.rocks', 'cs.4.security', 'cs.4.systems', 'cs.5.deep-learning', 'cs.5.distributed', 'cs.5.pl-theory', 'cs.5.frontier', 'cs.4.algorithms-adv', 'cs.4.ml', 'cs.4.theory', 'cs.3.web', 'cs.2.internet', 'cs.4.os', 'cs.4.databases-adv', 'cs.3.versioncontrol', 'cs.3.oop', 'cs.3.hardware', 'cs.2.bigo-intro', 'cs.3.algorithms', 'cs.1.blocks', 'cs.2.programming', 'cs.1.parts', 'cs.3.databases', 'cs.2.data-types', 'cs.2.debugging', 'cs.2.functions', 'cs.0.sorting', 'cs.0.patterns', 'chem.3.bonding', 'chem.4.inorganic', 'chem.3.organic-intro', 'chem.2.reactions-intro', 'chem.3.reactions', 'chem.2.periodic', 'chem.2.acids', 'chem.0.materials', 'chem.1.materials-props', 'chem.5.materials', 'chem.1.changes', 'chem.4.electrochem', 'chem.5.biochem', 'chem.5.frontier', 'chem.4.analytical', 'chem.5.compchem', 'chem.2.mixtures', 'chem.3.atomic-structure', 'chem.3.gases', 'chem.3.energy', 'chem.4.physical', 'chem.3.stoichiometry', 'chem.0.mixing', 'chem.0.water-states', 'chem.1.matter', 'bio.1.health', 'bio.3.microbiology', 'bio.5.immunology', 'bio.5.frontier', 'bio.4.neuro', 'bio.4.physiology', 'bio.4.ethology', 'bio.4.genomics', 'bio.5.comp-bio', 'bio.5.systems-bio', 'bio.3.ecology', 'bio.3.botany', 'bio.4.biochem', 'bio.3.evolution', 'bio.4.evo-bio', 'bio.1.human-body', 'bio.2.digestion', 'bio.2.reproduction', 'bio.0.animals', 'bio.1.habitats', 'bio.0.body', 'bio.0.seasons', 'bio.0.living', 'bio.2.classification', 'bio.2.ecosystems', 'bio.2.microbes', 'bio.0.plants', 'bio.1.plants-parts', 'bio.2.photosynthesis', 'bio.1.food-chains', 'math.5.diffgeo', 'math.5.complex-analysis', 'math.5.logic', 'math.5.frontier', 'math.5.abstract', 'math.5.measure', 'math.5.functional', 'math.5.numerical', 'math.4.diffeq', 'math.4.discrete', 'math.4.numtheory', 'math.4.analysis', 'math.4.prob-theory', 'math.3.euclid', 'math.4.complex', 'math.4.diff-calc', 'math.4.int-calc', 'math.3.probability', 'math.3.statistics', 'math.3.precalc', 'math.3.polynomials', 'math.3.trig', 'math.3.expo-logs', 'math.3.sequences', 'math.3.systems', 'math.3.quadratics', 'math.3.linear', 'math.3.slope', 'math.2.primes', 'math.2.ratio', 'math.2.exponents', 'math.2.data', 'math.2.prealgebra', 'math.2.decimals', 'math.2.order-ops', 'math.2.percent', 'math.2.coordinates', 'math.1.measurement', 'math.1.time', 'math.1.fractions-intro', 'math.1.multiplication', 'math.1.division', 'math.1.subtraction', 'math.1.place-value', 'math.0.compare', 'math.0.patterns', 'math.0.numbers20', 'cs.1.binary', 'hist.3.economics-intro', 'lang.4.linguistics', 'mind.5.logic-advanced'];
const EXISTING_SPATIAL = ['math.2.geometry', 'math.3.vectors', 'math.4.multivar', 'math.5.topology',
  'phys.4.em-maxwell', 'phys.4.solid-state', 'earth.1.seasons', 'earth.3.earth-science',
  'chem.2.molecules', 'chem.4.organic', 'chem.4.quantum-chem', 'bio.3.cell-bio'];
const plain = value => JSON.parse(JSON.stringify(value));
const equal = (actual, expected, message) => assert.deepEqual(plain(actual), plain(expected), message);
const near = (a, b, tolerance = 1e-8) => assert.ok(Number.isFinite(a) && Number.isFinite(b) &&
  Math.abs(a - b) <= tolerance, `${a} differs from ${b}`);

class TextNode {
  constructor(text) { this.nodeType = 3; this.textContent = String(text); }
}
class Element {
  constructor(tag) {
    this.nodeType = 1;
    this.tagName = tag.toLowerCase();
    this.attributes = new Map();
    this.children = [];
    this.listeners = new Map();
    this.style = {};
    this.dataset = {};
    this.value = '';
    this.checked = false;
    this.classList = {
      contains: name => (this.getAttribute('class') || '').split(/\s+/).includes(name),
      add: (...names) => this.setAttribute('class', [this.getAttribute('class') || '', ...names].join(' ').trim()),
      toggle: (name, force) => {
        const names = new Set((this.getAttribute('class') || '').split(/\s+/).filter(Boolean));
        const enabled = force === undefined ? !names.has(name) : Boolean(force);
        if (enabled) names.add(name); else names.delete(name);
        this.setAttribute('class', [...names].join(' '));
        return enabled;
      },
    };
  }
  setAttribute(key, value) {
    const text = String(value);
    this.attributes.set(key, text);
    if (['id', 'value', 'type', 'min', 'max', 'step'].includes(key)) this[key] = text;
    if (key === 'checked') this.checked = true;
  }
  getAttribute(key) { return this.attributes.has(key) ? this.attributes.get(key) : null; }
  set className(value) { this.setAttribute('class', value); }
  get className() { return this.getAttribute('class') || ''; }
  append(...children) { this.children.push(...children.map(child => child && child.nodeType ? child : new TextNode(child))); }
  prepend(...children) { this.children.unshift(...children); }
  replaceChildren(...children) { this.children = []; this.append(...children); }
  get textContent() { return this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this.children = value === '' ? [] : [new TextNode(value)]; }
  addEventListener(type, listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(listener);
  }
  dispatch(type) {
    const event = { type, target: this, currentTarget: this, preventDefault() {} };
    (this.listeners.get(type) || []).forEach(listener => listener.call(this, event));
  }
}
const document = {
  createElement: tag => new Element(tag),
  createElementNS: (_namespace, tag) => new Element(tag),
  createTextNode: value => new TextNode(value),
};
const context = vm.createContext({ window: {}, document });
for (const file of ['spatial-models.js', 'spatial-math.js', 'spatial-physical.js', 'spatial-molecular.js',
  'spatial-cross-subject.js', 'concept-models.js', 'lesson-models.js']) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, 'web', file), 'utf8'), context, { filename: file });
}
const spatial = context.window.PrimerSpatial;
const concepts = context.window.PrimerConceptModels;
for (const word of ['import', 'export', 'portable']) {
  const d = concepts.build('lang.2.etymology', { word }).data;
  equal(d.route[0], ['Latin', 'portare']); equal(d.route[d.route.length - 1], ['English', word]);
  if (word === 'portable') equal(d.route, [['Latin', 'portare'], ['Late Latin', 'portabilis'], ['French', 'portable'], ['English', 'portable']]);
  else { assert.equal(d.route.length, 3); assert.equal(d.route[1][1], word === 'import' ? 'importare' : 'exportare'); }
}
for (const foot of ['iamb', 'trochee', 'anapest', 'dactyl']) for (let feet = 1; feet <= 4; feet++) {
  const d = concepts.build('lang.2.poetry', { foot, feet }).data;
  const pattern = { iamb: '01', trochee: '10', anapest: '001', dactyl: '100' }[foot];
  assert.equal(d.stresses.map(Number).join(''), pattern.repeat(feet));
  assert.equal(d.syllables, pattern.length * feet); assert.equal(d.stresses.filter(Boolean).length, feet);
  equal(d.groups.flatMap(g => Array.from({ length: g.end - g.start }, (_, i) => g.start + i)), Array.from({ length: d.syllables }, (_, i) => i));
}
for (let chapter = 1; chapter <= 4; chapter++) for (const perspective of ['reader', 'mina']) {
  const d = concepts.build('lang.2.novels', { chapter, perspective }).data;
  assert.equal(d.gap, chapter === 2); assert.equal(d.knownEvents.length, chapter);
  assert.equal(d.knowledge, chapter >= (perspective === 'reader' ? 2 : 3) ? 'Leo made the map' : 'Mapmaker unknown');
  equal(d.selected, concepts.build('lang.2.novels', { chapter, perspective: 'reader' }).data.selected);
  assert.equal(d.selected.place, ['Village', 'Village', 'City library', 'Hidden garden'][chapter - 1]);
}
for (const third of ['copy', 'independent']) for (const question of ['opening', 'cost']) for (const inspect of ['A', 'B', 'C']) {
  const d = concepts.build('lang.2.research', { third, question, inspect }).data;
  const parent = Object.fromEntries(d.edges.map(([source, child]) => [child, source]));
  const rootOf = id => parent[id] ? rootOf(parent[id]) : id;
  equal(d.roots, Object.fromEntries(['A', 'B', 'C'].map(id => [id, rootOf(id)])));
  assert.equal(d.origins, new Set(['A', 'B', 'C'].map(rootOf)).size); assert.equal(d.origins, third === 'copy' ? 1 : 2);
  assert.equal(d.relevant, question === 'opening');
}
for (const audience of ['new', 'familiar']) for (const explanation of [false, true]) for (const signposts of [false, true]) {
  const d = concepts.build('lang.2.speaking', { audience, explanation, signposts }).data;
  assert.equal(d.rows.length, explanation ? 4 : 3); assert.equal(d.rows.some(r => r.role === 'Explanation'), explanation);
  assert.equal(d.spoken.includes('For example:'), signposts);
  equal(d.rows, concepts.build('lang.2.speaking', { audience, explanation, signposts: !signposts }).data.rows);
  assert.equal(d.rows.find(r => r.role === 'Example').lines[0], '“Cat” comes before “Catch”');
}
for (const subject of ['fox', 'foxes']) for (const verb of ['jumps', 'jump']) for (const focus of ['subject', 'predicate', 'pp']) {
  const d = concepts.build('lang.2.grammar', { subject, verb, focus }).data;
  assert.equal(d.agreement, { fox: 'jumps', foxes: 'jump' }[subject] === verb);
  assert.equal(d.sentence, 'The ' + subject + ' ' + verb + ' over logs.');
  assert.equal(d.tree.children[0].label, 'NP'); assert.equal(d.tree.children[1].label, 'VP');
  equal(d.tree.children[1].children[1], { label: 'PP', children: ['over', 'logs'] });
  equal(d.tree, concepts.build('lang.2.grammar', { subject, verb, focus: 'subject' }).data.tree);
}
for (const evidence of ['schedule', 'badges']) for (const explanation of [false, true]) for (const order of ['claim-first', 'detail-first']) {
  const d = concepts.build('lang.2.paragraphs', { evidence, explanation, order }).data;
  assert.equal(d.relevant, evidence === 'schedule'); assert.equal(d.rows.length, explanation ? 4 : 3);
  assert.equal(d.rows.some(r => r.role === 'Explanation'), explanation);
  assert.equal(d.rows[0].role, order === 'claim-first' ? 'Claim' : 'Detail');
  equal(d.rows.map(r => r.lines.join(' ')).sort(), concepts.build('lang.2.paragraphs', { evidence, explanation, order: 'claim-first' }).data.rows.map(r => r.lines.join(' ')).sort());
}
for (const word of ['cat', 'mat', 'sat']) for (let step = 0; step <= 3; step++) {
  const d = concepts.build('lang.0.phonics', { word, step }).data;
  equal(d.sounds, { cat: ['k', 'æ', 't'], mat: ['m', 'æ', 't'], sat: ['s', 'æ', 't'] }[word]);
  assert.equal(d.prefix.length, step); assert.equal(d.prefix, word.substring(0, step)); assert.equal(d.complete, step === 3);
}
for (const letter of ['i', 't']) for (let step = 0; step <= 2; step++) for (const guides of [false, true]) {
  const d = concepts.build('lang.1.handwriting', { letter, step, guides }).data;
  assert.equal(d.completed.length, step); equal(d.completed, d.strokes.slice(0, step));
  assert.equal(d.strokes[0].y2, 240); assert.equal(d.strokes[0].y1, letter === 'i' ? 160 : 95);
  equal(d.strokes, concepts.build('lang.1.handwriting', { letter, step, guides: !guides }).data.strokes);
  if (letter === 'i') { assert.equal(d.strokes[1].kind, 'dot'); assert.ok(d.strokes[1].y < d.strokes[0].y1); }
  else { assert.equal(d.strokes[1].y1, d.strokes[1].y2); assert.ok(d.strokes[1].x1 < d.strokes[1].x2); }
}
for (const question of ['toy', 'place']) for (const reply of ['train', 'park', 'clarify']) {
  const d = concepts.build('lang.0.speaking', { question, reply }).data;
  assert.equal(d.related, { toy: 'train', place: 'park' }[question] === reply);
  assert.equal(d.clarification, reply === 'clarify'); if (d.clarification) assert.equal(d.followup, 'I mean today.');
  if (!d.related && !d.clarification) assert.ok(d.followup.startsWith('I meant'));
}
for (const detail of ['return', 'asks', 'declines']) for (const claim of ['act', 'reward', 'always']) {
  const d = concepts.build('lang.1.childrens-lit', { detail, claim }).data;
  assert.equal(d.passage[0], 'Ari returns a lost purse.');
  if (claim === 'always') assert.equal(d.status, 'Not established by one event');
  if (claim === 'act') assert.equal(d.status, 'Supported interpretation');
  if (claim === 'reward') assert.equal(d.status, { return: 'Motive is not stated', asks: 'Plausible, not proved', declines: 'This detail pushes against it' }[detail]);
  equal(d.passage, concepts.build('lang.1.childrens-lit', { detail, claim: 'act' }).data.passage);
}
for (const action of ['help', 'wait']) for (const ending of ['resolved', 'open']) for (let part = 1; part <= 3; part++) {
  const d = concepts.build('lang.1.writing-stories', { action, ending, part }).data;
  assert.equal(d.resolved, part === 3 && ending === 'resolved');
  assert.equal(d.objectState, part === 1 ? 'Kite flying' : part === 3 && ending === 'resolved' ? 'Kite recovered' : 'Kite stuck');
  assert.equal(d.parts.length, 3); assert.equal(d.parts[1][1], action === 'help' ? 'Leo asks an adult for help.' : 'Leo waits and watches.');
  if (ending === 'open') assert.equal(d.parts[2][1], 'The kite remains stuck.');
  else assert.ok(d.parts[2].join(' ').includes(action === 'help' ? 'long pole' : 'wind changes'));
}
const dictionaryOrder = ['bat', 'can', 'cat', 'catch', 'cater', 'cattle'];
for (const first of dictionaryOrder) for (const second of dictionaryOrder) for (let reveal = 0; reveal <= 7; reveal++) {
  const d = concepts.build('lang.1.dictionary', { first, second, reveal }).data;
  assert.equal(d.order, Math.sign(dictionaryOrder.indexOf(first) - dictionaryOrder.indexOf(second)));
  let prefix = 0; for (; prefix < Math.min(first.length, second.length) && first.charAt(prefix) === second.charAt(prefix); prefix++);
  assert.equal(d.decisive, prefix); assert.equal(d.decided, reveal > prefix);
  if (first === second && reveal <= first.length) assert.equal(d.decided, false);
}
for (const word of ['walked', 'strolled', 'trudged']) for (const scene of ['leisure', 'mud', 'unknown']) {
  const d = concepts.build('lang.1.vocabulary', { word, scene }).data;
  assert.equal(d.sentence, 'Mina ' + word + ' home.');
  assert.equal(d.features[0], { walked: 'Not specified', strolled: 'Unhurried', trudged: 'Slow' }[word]);
  equal(d.features, concepts.build('lang.1.vocabulary', { word, scene: 'unknown' }).data.features);
  equal(d.scene, concepts.build('lang.1.vocabulary', { word: 'walked', scene }).data.scene);
}
for (const word of ['ship', 'fish', 'chat', 'much', 'thin', 'this']) for (let sound = 1; sound <= 3; sound++) {
  const d = concepts.build('lang.1.spelling', { word, sound }).data;
  assert.equal(d.groups.join(''), word); assert.equal(d.sounds.length, 3); assert.equal(d.letters, 4); assert.equal(d.selected, sound - 1);
  equal(d.groups, { ship: ['sh', 'i', 'p'], fish: ['f', 'i', 'sh'], chat: ['ch', 'a', 't'], much: ['m', 'u', 'ch'], thin: ['th', 'i', 'n'], this: ['th', 'i', 's'] }[word]);
  const covered = d.spans.flatMap(span => Array.from({ length: span.length }, (_, i) => span.start + i)); equal(covered, [0, 1, 2, 3]);
}
assert.notEqual(concepts.build('lang.1.spelling', { word: 'thin' }).data.sounds[0], concepts.build('lang.1.spelling', { word: 'this' }).data.sounds[0]);
for (const subject of ['dog', 'kitten']) for (const action of ['runs', 'jumps']) for (const verb of [false, true]) for (const capital of [false, true]) for (const stop of [false, true]) {
  const d = concepts.build('lang.1.sentences', { subject, action, verb, capital, stop }).data;
  assert.equal(d.written, (capital ? 'The ' : 'the ') + subject + (verb ? ' ' + action : '') + (stop ? '.' : ''));
  assert.equal(d.ready, verb && capital && stop); equal(d.checks.map(c => c.pass), [verb, capital, stop]);
  if (!verb) assert.equal(d.predicate, '');
}
for (const first of ['cat', 'sun', 'bee', 'blue']) for (const second of ['hat', 'run', 'tree', 'shoe', 'cup']) {
  const d = concepts.build('lang.0.rhymes', { first, second }).data;
  assert.equal(d.rhyme, { cat: 'hat', sun: 'run', bee: 'tree', blue: 'shoe' }[first] === second);
  assert.equal(d.first[0] + d.first[1], first); assert.equal(d.second[0] + d.second[1], second);
  if (first === 'blue' && second === 'shoe') { assert.equal(d.rhyme, true); assert.equal(d.sameLetters, false); }
}
for (const story of ['key', 'hat']) for (let event = 1; event <= 3; event++) for (const clue of ['who', 'where', 'what']) {
  const d = concepts.build('lang.0.stories', { story, event, clue }).data;
  assert.equal(d.who, story === 'key' ? 'Mina' : 'Duck'); assert.equal(d.events.length, 3);
  assert.equal(d.selected, d.events[event - 1]); assert.equal(d.answer, clue === 'what' ? d.selected : d[clue]);
  assert.equal(d.objectStates[event - 1], (story === 'key' ? ['Key missing', 'Key still missing', 'Key found'] : ['Hat blown away', 'Hat still in the air', 'Hat recovered'])[event - 1]);
}
for (const amplitude of [0, .05, .1, .15, .2]) for (let phase = 0; phase <= 360; phase += 30) for (const polarization of ['plus', 'cross']) for (let angle = 0; angle <= 90; angle += 15) {
  const d = concepts.build('earth.5.frontier', { amplitude, phase, polarization, angle }).data;
  const theta = angle * Math.PI / 180, expected = amplitude * Math.sin(phase * Math.PI / 180) * (polarization === 'plus' ? Math.cos(2 * theta) : Math.sin(2 * theta));
  near(d.signal, expected); near(d.matrix[0] * d.matrix[3] - d.matrix[1] * d.matrix[2], 1 - d.h ** 2 / 4);
  near(d.ring.reduce((sum, p) => sum + p.x, 0), 0); near(d.ring.reduce((sum, p) => sum + p.y, 0), 0);
  d.ring.forEach((p, i) => { const a = i * Math.PI / 8; const projection = (p.x - Math.cos(a)) * Math.cos(a) + (p.y - Math.sin(a)) * Math.sin(a); near(projection, d.h / 2 * (polarization === 'plus' ? Math.cos(2 * a) : Math.sin(2 * a))); });
  assert.ok(Math.abs(d.signal) <= amplitude + 1e-12);
}
for (const feedback of [false, true]) for (let forcing = -10; forcing <= 10; forcing += 5) for (let initialTemperature = 230; initialTemperature <= 310; initialTemperature += 10) for (let year = 0; year <= 40; year += 5) {
  const d = concepts.build('earth.5.earth-systems', { feedback, forcing, initialTemperature, year }).data;
  near(d.records[0].temperature, initialTemperature); near(d.selected.temperature, d.records[year].temperature);
  const t = d.selected.temperature, a = feedback ? t < 260 ? .6 : t > 280 ? .3 : .6 - .015 * (t - 260) : .3;
  near(d.reflectivity, a); near(d.netFlux, 340 * (1 - a) + forcing - .61 * 5.670374419e-8 * t ** 4);
  d.records.forEach(row => assert.ok(row.temperature >= 230 && row.temperature <= 310));
}
// Independent fine-step Euler integration checks the production RK4 trajectory.
for (const feedback of [false, true]) for (const forcing of [-10, 0, 10]) for (const initialTemperature of [230, 260, 270, 280, 310]) {
  let reference = initialTemperature;
  for (let step = 0; step < 40000; step++) {
    const albedo = !feedback || reference >= 280 ? .3 : reference <= 260 ? .6 : .6 - .015 * (reference - 260);
    reference += .0001 * (340 * (1 - albedo) + forcing - .61 * 5.670374419e-8 * reference ** 4);
  }
  const d = concepts.build('earth.5.earth-systems', { feedback, forcing, initialTemperature, year: 40 }).data;
  assert.ok(Math.abs(d.selected.temperature - reference) < .01, 'RK4 agrees with independent fine-step Euler');
}
for (const forcing of [-10, 0, 10]) {
  const cold = concepts.build('earth.5.earth-systems', { feedback: true, forcing, initialTemperature: 230, year: 40 }).data;
  const warm = concepts.build('earth.5.earth-systems', { feedback: true, forcing, initialTemperature: 310, year: 40 }).data;
  assert.ok(warm.selected.temperature - cold.selected.temperature > 30);
  near(cold.selected.temperature, ((136 + forcing) / (.61 * 5.670374419e-8)) ** .25, .01);
  near(warm.selected.temperature, ((238 + forcing) / (.61 * 5.670374419e-8)) ** .25, .01);
}
for (let matter = 10; matter <= 100; matter += 10) for (let scale = .25; scale <= 2; scale += .25) {
  const d = concepts.build('earth.5.cosmology', { matter, scale }).data, r = d.selected, m = matter / 100;
  near(r.expansion ** 2, m / scale ** 3 + 1 - m); near(r.matterFraction + r.vacuumFraction, 1);
  near(r.q, r.matterFraction / 2 - r.vacuumFraction);
  if (scale === 1) { near(r.expansion, 1); near(r.matterFraction, m); }
  if (matter === 100) { assert.equal(d.transition, null); near(r.q, .5); }
  else near(m / d.transition ** 3, 2 * (1 - m));
  d.records.slice(1).forEach((row, i) => { assert.ok(row.expansion < d.records[i].expansion); assert.ok(row.matterFraction <= d.records[i].matterFraction); });
}
for (let prior = 1; prior <= 50; prior++) for (let sensitivity = 50; sensitivity <= 100; sensitivity += 10) for (let specificity = 50; specificity <= 100; specificity += 10) {
  const d = concepts.build('earth.5.astrobiology', { prior, sensitivity, specificity }).data;
  near(d.tp + d.fn, prior * 100); near(d.fp + d.tn, (100 - prior) * 100);
  near(d.tp + d.fn + d.fp + d.tn, 10000);
  near(d.tp / d.living, sensitivity / 100); near(d.tn / d.lifeless, specificity / 100);
  near(d.posterior, 1 / (1 + (100 - prior) * (100 - specificity) / (prior * sensitivity)));
  assert.ok(d.posterior >= 0 && d.posterior <= 1);
  if (specificity === 100) near(d.posterior, 1);
}
near(concepts.build('earth.5.astrobiology', { prior: 1, sensitivity: 90, specificity: 90 }).data.posterior, 1 / 12);
for (const mass of ['0.1', '1', '5']) for (let radius = .5; radius <= 3; radius += .5) for (let temperature = 100; temperature <= 1000; temperature += 100) for (const molecule of ['2', '4', '28', '44']) {
  const d = concepts.build('earth.4.planetary', { mass, radius, temperature, molecule }).data;
  near(d.escape ** 2 * 1e6 * 6.371e6 * radius / (2 * 3.986e14 * Number(mass)), 1);
  near(d.rms ** 2 * 1e6 * Number(molecule) * 1.66053906660e-27 / (3 * 1.380649e-23 * temperature), 1);
  near(d.jeans / (1.5 * d.speedRatio ** 2), 1); assert.ok(d.jeans > 0);
}
for (let rate = 10; rate <= 50; rate += 10) for (let zero = 10; zero <= 50; zero += 10) for (const response of ['0.3', '0.45', '0.6']) for (let year = 0; year <= 60; year += 5) {
  const d = concepts.build('earth.4.climatology', { rate, zero, response, year }).data;
  const elapsed = Math.min(year, zero), currentRate = year < zero ? rate * (zero - year) / zero : 0;
  near(d.selected.rate, currentRate); near(d.selected.cumulative, elapsed * (rate + currentRate) / 2);
  near(d.warming, d.selected.cumulative * Number(response) / 1000); near(d.finalCumulative, rate * zero / 2);
  d.records.slice(1).forEach((row, i) => { assert.ok(row.cumulative >= d.records[i].cumulative); near(row.cumulative - d.records[i].cumulative, (row.rate + d.records[i].rate) / 2); });
}
for (let latitude = -60; latitude <= 60; latitude += 15) for (let pressure = -4; pressure <= 4; pressure++) {
  const d = concepts.build('earth.4.oceanatmos', { latitude, pressure }).data;
  if (!latitude) { assert.equal(d.valid, false); equal([d.northVelocity, d.coriolis], [null, null]); }
  else { assert.equal(d.valid, true); near(d.pressure + d.coriolis, 0); near(d.f * d.northVelocity, -pressure * 1e-4); near(d.northVelocity, -concepts.build('earth.4.oceanatmos', { latitude: -latitude, pressure }).data.northVelocity); }
}
for (let distance = 0; distance <= 500; distance += 50) for (let speed = 4; speed <= 8; speed++) for (const ratio of ['0.5', '0.6', '0.7']) for (const liquid of [false, true]) {
  const d = concepts.build('earth.4.geophysics', { distance, speed, ratio, liquid }).data;
  near(d.pTime * speed, distance);
  if (liquid) equal([d.sSpeed, d.sTime, d.lag, d.inferred], [null, null, null, null]);
  else { near(d.sTime * speed * Number(ratio), distance); near(d.lag, distance * (1 - Number(ratio)) / (speed * Number(ratio))); near(d.inferred, distance); assert.ok(d.sTime >= d.pTime); }
}
for (let temperature = 3000; temperature <= 12000; temperature += 500) for (let redshift = 0; redshift <= 2; redshift += .25) {
  const d = concepts.build('earth.4.astrophysics', { temperature, redshift }).data;
  near(d.peak * temperature, 2.897771955e6); near(d.observedPeak / d.peak, 1 + redshift);
  d.wavelengths.forEach((wavelength, i) => {
    const emittedWavelength = wavelength / (1 + redshift), c2 = 1.438776877e7;
    const expected = (d.peak / emittedWavelength) ** 5 * Math.expm1(c2 / (d.peak * temperature)) / Math.expm1(c2 / (emittedWavelength * temperature));
    near(d.observed[i], expected); assert.ok(d.observed[i] >= 0 && d.observed[i] <= 1 + 1e-8);
    assert.ok(d.emitted[i] >= 0 && d.emitted[i] <= 1 + 1e-8);
    if (!redshift) near(d.emitted[i], d.observed[i]);
  });
}
const redshiftedWarm = concepts.build('earth.4.astrophysics', { temperature: 6000, redshift: 1 }).data;
const nearbyCool = concepts.build('earth.4.astrophysics', { temperature: 3000, redshift: 0 }).data;
redshiftedWarm.observed.forEach((value, i) => near(value, nearbyCool.observed[i]));
for (let temperature = 3000; temperature <= 30000; temperature += 1000) for (const radius of ['0.01', '0.1', '1', '10', '100']) {
  const d = concepts.build('earth.3.astronomy', { temperature, radius }).data;
  near(d.luminosity / Number(radius) ** 2 / (temperature / 5772) ** 4, 1);
  near(10 ** d.logLuminosity / d.luminosity, 1); assert.ok(d.logLuminosity >= -6 && d.logLuminosity <= 7);
  if (temperature <= 15000) near(concepts.build('earth.3.astronomy', { temperature: 2 * temperature, radius }).data.luminosity / d.luminosity, 16);
}
for (const seasonal of [false, true]) for (let capacity = 50; capacity <= 300; capacity += 50) for (let demand = 50; demand <= 150; demand += 25) for (let month = 1; month <= 12; month++) {
  const d = concepts.build('earth.3.ecology-earth', { seasonal, capacity, demand, month }).data;
  let previous = 0, rain = 0, losses = 0;
  d.records.forEach((row, i) => {
    assert.equal(row.rain, seasonal ? i < 4 ? 300 : 0 : 100);
    assert.equal(row.drainage, Math.max(0, previous + row.rain - capacity));
    assert.equal(row.actualET, Math.min(demand, previous + row.rain - row.drainage));
    assert.equal(row.stored, previous + row.rain - row.drainage - row.actualET);
    assert.ok(row.stored >= 0 && row.stored <= capacity); assert.equal(row.unmet, demand - row.actualET);
    rain += row.rain; losses += row.drainage + row.actualET; previous = row.stored;
  });
  assert.equal(rain, 1200); assert.equal(rain, losses + d.stored);
  assert.equal(d.totalET + d.totalDrainage + d.stored, 1200); equal(d.selected, d.records[month - 1]);
}
assert.equal(concepts.build('earth.3.ecology-earth', { seasonal: false, capacity: 150, demand: 100, month: 1 }).data.dryMonths, 0);
assert.equal(concepts.build('earth.3.ecology-earth', { seasonal: true, capacity: 150, demand: 100, month: 1 }).data.dryMonths, 8);
for (let albedo = 0; albedo <= 80; albedo += 10) for (let infrared = 0; infrared <= 100; infrared += 10) for (let solar = 1000; solar <= 1600; solar += 100) {
  const d = concepts.build('earth.3.climate-sci', { albedo, infrared, solar }).data, epsilon = infrared / 100;
  near(d.absorbed, solar * (100 - albedo) / 400); near(d.outgoing, d.absorbed);
  near(d.emitted, d.absorbed + d.downward); near(d.downward + d.upward, epsilon * d.emitted);
  near(d.direct, (1 - epsilon) * d.emitted); near(5.670374419e-8 * d.temperature ** 4, d.emitted);
  near(d.temperature / d.bare, (1 / (1 - epsilon / 2)) ** .25);
  if (infrared === 0) assert.equal(d.atmosphere, null);
  else near(2 * 5.670374419e-8 * d.atmosphere ** 4, d.emitted);
}
for (let dry = 1; dry <= 10; dry++) for (let propellant = 0; propellant <= 30; propellant++) for (let exhaust = 1; exhaust <= 5; exhaust += .5) for (const burn of [0, 25, 50, 75, 100]) {
  const d = concepts.build('earth.3.space-exploration', { dry, propellant, exhaust, burn }).data;
  near(d.initial, d.remaining + d.expelled); near(d.remaining, dry + propellant * (1 - burn / 100));
  near(Math.exp(d.delta / exhaust), (dry + propellant) / d.remaining);
  near(Math.exp(d.full / exhaust), 1 + propellant / dry);
  assert.ok(d.remaining >= dry && d.delta >= 0 && d.delta <= d.full + 1e-8);
  if (!burn || !propellant) assert.equal(d.delta, 0);
  if (burn === 100) near(d.delta, d.full);
}
for (const boundary of ['divergent', 'convergent', 'transform']) for (let steps = 0; steps <= 6; steps++) {
  const d = concepts.build('earth.2.geology', { boundary, steps }).data;
  near(d.gap, boundary === 'transform' ? 2 : 2 + (boundary === 'divergent' ? 1 : -1) * steps / 6);
  near(d.offset, boundary === 'transform' ? steps / 3 : 0);
  near(d.a[0] + d.b[0], 0); near(d.a[1] + d.b[1], 0);
  assert.ok(d.a[0] < 0 && d.b[0] > 0);
}
for (let moon = 0; moon <= 180; moon += 15) for (let observer = 0; observer < 360; observer += 15) {
  const d = concepts.build('earth.2.oceans', { moon, observer }).data, rad = Math.PI / 180;
  const cosine = Math.cos(2 * moon * rad) + .4, sine = Math.sin(2 * moon * rad);
  near(d.local, cosine * Math.cos(2 * observer * rad) + sine * Math.sin(2 * observer * rad));
  near(d.range, 2 * Math.hypot(cosine, sine)); assert.ok(d.range >= 1.2 - 1e-8 && d.range <= 2.8 + 1e-8);
  near(d.samples[0], d.samples[72]); near(d.samples.slice(0, 72).reduce((sum, value) => sum + value, 0), 0);
  d.samples.forEach(value => assert.ok(Math.abs(value) <= d.amplitude + 1e-8));
  if (moon === 0 || moon === 180) near(d.range, 2.8);
  if (moon === 90) near(d.range, 1.2);
}
for (let shift = 0; shift <= 4; shift++) for (let departure = -8; departure <= 8; departure++) for (let year = 1; year <= 30; year++) {
  const d = concepts.build('earth.2.atmosphere', { shift, departure, year }).data;
  assert.equal(d.mean, 10 + shift); assert.equal(d.today, 10 + shift + departure);
  assert.equal(d.records.length, 30); assert.equal(d.selected, 8 + shift + (year - 1) % 5);
  near(d.records.reduce((sum, value) => sum + value, 0) / 30, d.mean);
  equal(d.records, concepts.build('earth.2.atmosphere', { shift, departure: 0, year }).data.records);
}
for (const prevention of [0, 25, 50, 75, 100]) for (let cleanup = 0; cleanup <= 8; cleanup++) for (let steps = 0; steps <= 8; steps++) {
  const d = concepts.build('earth.2.environment', { prevention, cleanup, steps }).data;
  const incoming = 8 - prevention * .08, expected = Math.max(0, 20 + steps * (incoming - cleanup));
  assert.equal(d.stock, expected); assert.equal(d.collected, 20 + incoming * steps - expected);
  assert.equal(d.added, incoming * steps); assert.equal(d.avoided, (8 - incoming) * steps);
  assert.equal(d.stock + d.collected, 20 + d.added);
  equal(d.history, Array.from({ length: steps + 1 }, (_, i) => Math.max(0, 20 + i * (incoming - cleanup))));
}
const planetDiameters = [4879, 12104, 12756, 6792, 142984, 120536, 51118, 49528];
for (let first = 0; first < 8; first++) for (let second = 0; second < 8; second++) {
  const d = concepts.build('earth.2.planets', { first: String(first), second: String(second) }).data;
  equal(d.diameters, [planetDiameters[first], planetDiameters[second]]);
  near(d.ratio, planetDiameters[second] / planetDiameters[first]);
  near(d.volumeRatio, Math.pow(planetDiameters[second], 3) / Math.pow(planetDiameters[first], 3));
  near(d.radii[1] / d.radii[0], d.ratio); assert.equal(Math.max(...d.radii), 72);
}
for (let luminosity = 1; luminosity <= 8; luminosity++) for (let distance = 1; distance <= 8; distance++) {
  const d = concepts.build('earth.2.stars', { luminosity, distance }).data;
  near(d.flux * distance * distance, luminosity); assert.equal(d.spreadingArea, distance * distance);
  d.samples.forEach((value, i) => near(value * (i + 1) ** 2, luminosity));
  if (distance <= 4) near(concepts.build('earth.2.stars', { luminosity, distance: 2 * distance }).data.flux, d.flux / 4);
}
near(concepts.build('earth.2.stars', { luminosity: 4, distance: 2 }).data.flux, concepts.build('earth.2.stars', { luminosity: 1, distance: 1 }).data.flux);
const weatherValues = { temperature: [20, 8, -3, 15], rain: [0, 3, 0, 0], snow: [0, 0, 3, 0], wind: [8, 20, 10, 36] };
for (let day = 0; day < 4; day++) for (const [metric, expected] of Object.entries(weatherValues)) {
  const d = concepts.build('earth.0.weather', { day: String(day), metric }).data;
  equal(d.values, expected); assert.equal(d.selected[metric], expected[day]);
  assert.ok(d.values.every(value => value >= d.minimum && value <= d.maximum));
  assert.equal(d.unit, { temperature: '°C', rain: 'mm', snow: 'cm', wind: 'km/h' }[metric]);
}
const solarReference = [.39, .72, 1, 1.52, 5.2, 9.54, 19.2, 30.06];
for (let planet = 0; planet < 8; planet++) for (const scale of ['order', 'distance']) {
  const d = concepts.build('earth.1.solar-system', { planet: String(planet), scale }).data;
  equal(d.distances, solarReference); assert.equal(d.distance, solarReference[planet]);
  d.positions.forEach((position, i) => near(position, scale === 'order' ? (i + 1) / 8 : solarReference[i] / solarReference[7]));
  assert.equal(d.group, planet < 4 ? 'Rocky planet' : planet < 6 ? 'Gas giant' : 'Ice giant');
}
for (const basin of [false, true]) for (let start = 0; start <= 6; start++) for (let steps = 0; steps <= 6; steps++) {
  const routes = basin ? [[0], [1, 0], [2, 3], [3], [4, 3], [5, 6], [6]] : [[0], [1, 0], [2, 1, 0], [3, 2, 1, 0], [4, 5, 6], [5, 6], [6]];
  const d = concepts.build('earth.0.land-water', { basin, start, steps }).data;
  equal(d.path, routes[start]); equal(d.traveled, routes[start].slice(0, steps + 1));
  assert.equal(d.position, routes[start][Math.min(steps, routes[start].length - 1)]);
  assert.equal(d.stopped, steps >= routes[start].length - 1);
  d.path.slice(1).forEach((position, i) => assert.ok(d.heights[position] < d.heights[d.path[i]]));
}
for (let amount = 0; amount <= 8; amount++) for (const infiltration of [0, 25, 50, 75, 100]) for (let stage = 0; stage <= 6; stage++) {
  const d = concepts.build('earth.1.water-cycle', { amount, infiltration, stage }).data;
  const ground = amount * infiltration / 100;
  const expected = [[20, 0, 0, 0, 0], [20 - amount, amount, 0, 0, 0], [20 - amount, 0, amount, 0, 0], [20 - amount, 0, 0, amount, 0], [20 - amount, 0, 0, amount - ground, ground], [20 - ground, 0, 0, 0, ground], [20, 0, 0, 0, 0]][stage];
  equal(['surface', 'vapour', 'cloud', 'land', 'ground'].map(key => d.stores[key]), expected);
  assert.equal(d.total, 20); assert.ok(Object.values(d.stores).every(value => value >= 0));
}
const rockExpected = {
  igneous: ['sediment', null, 'metamorphic', 'magma', null],
  sedimentary: ['sediment', null, 'metamorphic', 'magma', null],
  metamorphic: ['sediment', null, 'metamorphic', 'magma', null],
  sediment: [null, 'sedimentary', null, 'magma', null],
  magma: [null, null, null, null, 'igneous'],
};
for (const [material, expected] of Object.entries(rockExpected)) ['weathering', 'consolidate', 'metamorphism', 'melt', 'cool'].forEach((process, i) => {
  const d = concepts.build('earth.1.rocks', { material, process }).data;
  assert.equal(d.result, expected[i]); assert.equal(d.valid, expected[i] !== null);
});
for (let first = 0; first < 16; first++) for (let second = 0; second < 16; second++) for (let key = 0; key < 16; key++) {
  const d = concepts.build('cs.4.security', { first, second, key }).data;
  assert.equal(d.c1 ^ key, first); assert.equal(d.c2 ^ key, second);
  assert.equal(d.difference, first ^ second); assert.equal(d.messageXor, d.difference);
}
for (let index = -1; index <= 4; index++) for (const alive of [false, true]) for (const action of ['read', 'write']) for (let value = 0; value <= 99; value++) {
  const d = concepts.build('cs.4.systems', { index, alive, action, value }).data;
  const valid = alive && index >= 0 && index < 4;
  assert.equal(d.valid, valid); assert.equal(d.formation, alive && index >= 0);
  assert.equal(d.result, valid ? action === 'read' ? [10, 20, 30, 40][index] : value : null);
  assert.equal(d.address, alive && index >= 0 ? ['0x1000', '0x1004', '0x1008', '0x100c', '0x1010'][index] : null);
  d.values.forEach((actual, i) => assert.equal(actual, !alive ? null : valid && action === 'write' && i === index ? value : [10, 20, 30, 40][i]));
}
for (let query = -3; query <= 3; query += .5) for (let third = 0; third <= 10; third++) for (const causal of [false, true]) {
  const d = concepts.build('cs.5.deep-learning', { query, third, causal }).data;
  const raw = [Math.exp(-query), 1, causal ? 0 : Math.exp(query)], total = raw.reduce((a, b) => a + b, 0);
  d.weights.forEach((weight, i) => near(weight, raw[i] / total));
  near(d.weights.reduce((a, b) => a + b, 0), 1);
  near(d.result, (2 * raw[0] + 5 * raw[1] + third * raw[2]) / total);
  if (causal) { assert.equal(d.weights[2], 0); near(d.result, concepts.build('cs.5.deep-learning', { query, third: 0, causal }).data.result); }
}
for (let first = 0; first < 32; first++) for (let second = 0; second < 32; second++) {
  const d = concepts.build('cs.5.distributed', { first, second }).data;
  const a = [1, 2, 3, 4, 5].filter(i => first & (2 ** (i - 1))), b = [1, 2, 3, 4, 5].filter(i => second & (2 ** (i - 1)));
  equal(d.first, a); equal(d.second, b); equal(d.overlap, a.filter(i => b.includes(i)));
  assert.ok(d.overlap.length >= d.lowerBound); assert.equal(d.lowerBound, Math.max(0, a.length + b.length - 5));
  if (a.length >= 3 && b.length >= 3) assert.ok(d.overlap.length >= 1);
}
for (const argument of ['0', '2', '5', 'true', 'false']) for (let offset = -2; offset <= 3; offset++) for (let stage = 0; stage <= 2; stage++) {
  const d = concepts.build('cs.5.pl-theory', { argument, offset, stage }).data;
  const valid = !['true', 'false'].includes(argument);
  assert.equal(d.valid, valid); assert.equal(d.result, valid ? Number(argument) + offset : null);
  assert.equal(d.terms.length, valid ? 3 : 1); assert.equal(d.argumentType, valid ? 'Int' : 'Bool');
  if (valid && stage === 2) assert.equal(d.displayed, String(Number(argument) + offset));
}
for (let limit = 0; limit <= 5; limit++) for (let bound = 0; bound <= 6; bound++) for (const repaired of [false, true]) {
  const d = concepts.build('cs.5.frontier', { limit, bound, repaired }).data;
  const fails = !repaired && bound >= limit + 1;
  assert.equal(Boolean(d.violation), fails); assert.equal(d.safeWithinBound, !fails);
  d.levels.forEach((states, depth) => equal(states, Array.from({ length: Math.min(depth, limit + (repaired ? 0 : 1)) + 1 }, (_, i) => i)));
  if (fails) { assert.equal(d.violation.depth, limit + 1); equal(d.violation.path, Array.from({ length: limit + 2 }, (_, i) => i)); }
}
for (let ab = 1; ab <= 9; ab++) for (let ac = 1; ac <= 9; ac++) for (let bc = 1; bc <= 9; bc++) for (let steps = 0; steps <= 4; steps++) {
  const d = concepts.build('cs.4.algorithms-adv', { ab, ac, bc, steps }).data;
  const shortest = [0, ab, Math.min(ac, ab + bc), Math.min(ab + 5, ac + 2, ab + bc + 2)];
  assert.equal(d.settled.length, steps);
  d.settled.forEach((node, i) => {
    assert.equal(d.distances[node], shortest[node]);
    assert.equal(d.trace[i].distances[node], shortest[node]);
    if (i) assert.ok(shortest[d.settled[i - 1]] <= shortest[node]);
  });
  if (d.path.length) {
    assert.equal(d.path[0], 0); assert.equal(d.path[d.path.length - 1], 3);
    let sum = 0;
    d.path.slice(1).forEach((node, i) => { sum += d.edges.find(edge => edge.from === d.path[i] && edge.to === node).cost; });
    assert.equal(sum, d.distances[3]);
  }
  if (steps === 4) equal(d.distances, shortest);
}
for (let rateIndex = 1; rateIndex <= 12; rateIndex++) for (let steps = 0; steps <= 8; steps++) for (let shift = 0; shift <= 4; shift++) {
  const rate = rateIndex * .02, d = concepts.build('cs.4.ml', { rate, steps, shift }).data;
  const expected = 2 * (1 - (1 - 28 * rate / 3) ** steps);
  near(d.weight, expected);
  near(d.trainingLoss, 14 / 3 * (expected - 2) ** 2);
  near(d.heldoutLoss, ((4 * expected - 8 - shift) ** 2 + (5 * expected - 10 - shift) ** 2) / 2);
  assert.equal(d.trajectory.length, steps + 1);
  assert.equal(d.weight, concepts.build('cs.4.ml', { rate, steps, shift: 0 }).data.weight, 'Held-out data cannot enter training');
}
assert.ok(concepts.build('cs.4.ml', { rate: .24, steps: 8, shift: 0 }).data.trainingLoss > 56 / 3);
assert.match(concepts.build('cs.4.ml', { rate: .1, steps: 8, shift: 0 }).readout, /Training MSE=[1-9].*e-/);
for (const word of ['', '01', '1101', '010', '111', '00101']) for (let steps = 0; steps <= 5; steps++) {
  const d = concepts.build('cs.4.theory', { word, steps }).data;
  const prefix = word.slice(0, steps);
  assert.equal(d.accepted, prefix.endsWith('01'));
  assert.equal(d.state, prefix.endsWith('01') ? 2 : prefix.endsWith('0') ? 1 : 0);
  assert.equal(d.finished, steps >= word.length);
  assert.equal(d.prefix + d.remaining, word);
  assert.equal(d.trace.length, Math.min(steps, word.length) + 1);
  d.trace.forEach((state, i) => {
    const part = word.slice(0, i);
    assert.equal(state, part.endsWith('01') ? 2 : part.endsWith('0') ? 1 : 0);
  });
}
for (let count = 0; count <= 9; count++) for (const theme of ['gold', 'blue', 'plain']) for (const enabled of [false, true]) {
  const d = concepts.build('cs.3.web', { count, theme, enabled }).data;
  assert.equal(d.count, count); assert.equal(d.next, (count + 1) % 10);
  assert.match(d.background, /^#[0-9a-f]{6}$/);
}
for (const site of ['atlas', 'book']) for (const cached of [false, true]) for (let stage = 0; stage <= 4; stage++) {
  const d = concepts.build('cs.2.internet', { site, cached, stage }).data;
  assert.equal(d.address, stage >= 1 ? site === 'atlas' ? '192.0.2.10' : '192.0.2.20' : null);
  assert.equal(d.dnsQueries, stage >= 1 && !cached ? 1 : 0);
  assert.equal(d.requests, stage >= 3 ? 1 : 0); assert.equal(d.responses, stage === 4 ? 1 : 0);
  assert.equal(d.tls, stage >= 2);
}
for (const policy of ['rr', 'fcfs']) for (let quantum = 1; quantum <= 4; quantum++) {
  const d = concepts.build('cs.4.os', { policy, quantum }).data;
  const expected = policy === 'fcfs' ? 'AAABBBBBCC' : { 1: 'ABCABCABBB', 2: 'AABBCCABBB', 3: 'AAABBBCCBB', 4: 'AAABBBBCCB' }[quantum];
  assert.equal(d.timeline.join(''), expected);
  assert.equal(d.timeline.length, 10);
  d.jobs.forEach(job => {
    assert.equal(d.timeline.filter(id => id === job.id).length, job.burst);
    assert.equal(job.first, expected.indexOf(job.id)); assert.equal(job.completion, expected.lastIndexOf(job.id) + 1);
    assert.equal(job.waiting, job.completion - job.burst); assert.equal(job.remaining, 0);
  });
  assert.equal(d.switches, Array.from(expected).slice(1).filter((id, i) => id !== expected[i]).length);
}
for (let amount = 0; amount <= 8; amount++) for (const failure of [false, true]) for (const atomic of [false, true]) {
  const d = concepts.build('cs.4.databases-adv', { amount, failure, atomic }).data;
  assert.equal(d.rolledBack, failure && atomic);
  assert.equal(d.finalA, failure && atomic ? 8 : 8 - amount);
  assert.equal(d.finalB, failure ? 2 : 2 + amount);
  assert.equal(d.total, failure && !atomic ? 10 - amount : 10);
  assert.equal(d.pendingA, 8 - amount); assert.equal(d.pendingB, failure ? 2 : 2 + amount);
}
for (let leftLine = 0; leftLine <= 3; leftLine++) for (let rightLine = 0; rightLine <= 3; rightLine++) for (const same of [false, true]) for (const resolution of ['none', 'left', 'right']) {
  const d = concepts.build('cs.3.versioncontrol', { leftLine, rightLine, same, resolution }).data;
  equal(d.base, ['A', 'B', 'C'], 'Merge preserves common ancestor');
  const conflict = leftLine > 0 && leftLine === rightLine && !same;
  equal(d.conflicts, conflict ? [leftLine] : []);
  assert.equal(d.unresolved, conflict && resolution === 'none' ? 1 : 0);
  for (let i = 0; i < 3; i++) {
    assert.equal(d.left[i], leftLine === i + 1 ? 'X' : d.base[i]);
    assert.equal(d.right[i], rightLine === i + 1 ? same ? 'X' : 'Y' : d.base[i]);
    const expected = conflict && leftLine === i + 1 ? resolution === 'none' ? null : resolution === 'left' ? 'X' : 'Y' : rightLine === i + 1 ? same ? 'X' : 'Y' : leftLine === i + 1 ? 'X' : d.base[i];
    assert.equal(d.merged[i], expected);
  }
}
for (let first = 0; first <= 5; first++) for (let second = 0; second <= 5; second++) for (const boosted of [false, true]) {
  const d = concepts.build('cs.3.oop', { first, second, boosted }).data;
  assert.equal(d.firstPoints, first); assert.equal(d.secondPoints, second);
  assert.equal(d.firstScore, first + (boosted ? 3 : 0)); assert.equal(d.secondScore, second);
  assert.equal(d.firstClass, boosted ? 'BonusScore' : 'Score');
  const changed = concepts.build('cs.3.oop', { first: (first + 1) % 6, second, boosted: !boosted }).data;
  assert.equal(changed.secondPoints, d.secondPoints); assert.equal(changed.secondScore, d.secondScore);
}
for (const a of [0, 1]) for (const b of [0, 1]) for (const carry of [0, 1]) {
  const d = concepts.build('cs.3.hardware', { a, b, carry }).data;
  assert.equal(d.total, a + b + carry);
  assert.equal(d.sum, (a + b + carry) % 2); assert.equal(d.carryOut, Math.floor((a + b + carry) / 2));
  assert.equal(d.x, Number(a !== b)); assert.equal(d.p, Number(Boolean(a && b)));
  assert.equal(d.q, Number(Boolean(d.x && carry)));
}
for (let size = 4; size <= 32; size += 4) for (let target = 0; target <= 33; target++) {
  const d = concepts.build('cs.2.bigo-intro', { size, target }).data;
  const found = target >= 1 && target <= size;
  assert.equal(d.linearFound, found); assert.equal(d.binaryFound, found);
  assert.equal(d.linear.length, found ? target : size);
  assert.ok(d.binary.length <= Math.floor(Math.log2(size)) + 1);
  let low = 1, high = size;
  d.binary.forEach(row => {
    assert.equal(row.low, low); assert.equal(row.high, high);
    assert.equal(row.value, Math.floor((low + high) / 2));
    if (row.value < target) low = row.value + 1;
    else if (row.value > target) high = row.value - 1;
  });
  if (found) assert.equal(d.binary[d.binary.length - 1].value, target);
  else assert.ok(low > high);
}
assert.ok(concepts.build('cs.2.bigo-intro', { size: 32, target: 1 }).data.binary.length > 1);
for (const input of ['mixed', 'sorted', 'reverse', 'ties']) for (let stage = 0; stage <= 4; stage++) {
  const d = concepts.build('cs.3.algorithms', { input, stage }).data;
  const expected = Array.from(d.source).sort((a, b) => a.value - b.value || a.id - b.id);
  equal(d.result, expected, 'Stable merged result');
  assert.equal(new Set(d.result.map(item => item.id)).size, 4);
  assert.equal(d.shownComparisons, stage < 3 ? 0 : stage === 3 ? 2 : d.comparisons);
  assert.equal(d.comparisons, input === 'mixed' || input === 'ties' ? 5 : 4);
  for (const pair of [d.left, d.right]) assert.ok(pair[0].value <= pair[1].value);
}
for (let repeats = 0; repeats <= 4; repeats++) for (let star = 0; star <= 4; star++) for (let jump = 1; jump <= 3; jump++) {
  const d = concepts.build('cs.1.blocks', { repeats, star, jump }).data;
  assert.equal(d.before, repeats);
  assert.equal(d.matched, repeats === star);
  assert.equal(d.position, repeats + (repeats === star ? jump : 0));
  assert.equal(d.path.length, repeats + 1);
  d.path.forEach((position, i) => assert.equal(position, i));
}
for (let threshold = 0; threshold <= 9; threshold++) for (let iterations = 0; iterations <= 3; iterations++) {
  const d = concepts.build('cs.2.programming', { threshold, iterations }).data;
  const values = [2, 5, 8];
  assert.equal(d.total, values.slice(0, iterations).filter(value => value > threshold).reduce((a, b) => a + b, 0));
  d.trace.forEach((row, i) => {
    assert.equal(row.value, values[i]);
    assert.equal(row.completed, i < iterations);
    assert.equal(row.accepted, i < iterations ? values[i] > threshold : null);
    assert.equal(row.total, i < iterations ? values.slice(0, i + 1).filter(value => value > threshold).reduce((a, b) => a + b, 0) : null);
  });
}
assert.equal(concepts.build('cs.2.programming', { threshold: 5, iterations: 3 }).data.total, 8);
assert.equal(concepts.build('cs.1.blocks', { repeats: 4, star: 2, jump: 3 }).data.position, 4);
for (let input = 0; input <= 9; input++) for (const operation of ['double', 'increment']) for (let step = 0; step <= 3; step++) {
  const d = concepts.build('cs.1.parts', { input, operation, step }).data;
  const expected = operation === 'double' ? 2 * input : input + 1;
  assert.equal(d.result, expected);
  assert.equal(d.memory, step === 0 ? null : step === 1 ? input : expected);
  assert.equal(d.processor, step >= 2 ? expected : null);
  assert.equal(d.output, step === 3 ? expected : null);
}
for (let minimum = 0; minimum <= 100; minimum += 10) for (const group of ['all', 'A', 'B']) for (const descending of [false, true]) {
  const d = concepts.build('cs.3.databases', { minimum, group, descending }).data;
  assert.equal(d.rows.map(row => row.id).join(','), '1,2,3,4,5,6');
  const wanted = d.rows.filter(row => row.score >= minimum && (group === 'all' || row.group === group));
  assert.equal(d.result.map(row => row.id).sort().join(','), wanted.map(row => row.id).sort().join(','));
  d.result.slice(1).forEach((row, i) => { const previous = d.result[i]; assert.ok(descending ? previous.score >= row.score : previous.score <= row.score); if (previous.score === row.score) assert.ok(previous.id < row.id); });
}
assert.equal(concepts.build('cs.3.databases', { minimum: 70, group: 'all', descending: true }).data.result.map(row => row.name).join(','), 'Bee,Ant,Elk');
for (const leftType of ['number', 'text']) for (const rightType of ['number', 'text']) for (let left = 0; left <= 9; left++) for (let right = 0; right <= 9; right++) {
  const d = concepts.build('cs.2.data-types', { left, right, leftType, rightType }).data;
  assert.equal(d.valid, leftType === rightType);
  assert.equal(d.result, leftType !== rightType ? null : leftType === 'number' ? left + right : String(left) + String(right));
  if (!d.valid) assert.equal(d.output, 'TypeError');
  if (leftType === 'text' && rightType === 'text') assert.equal(d.result.length, 2);
}
for (const fixed of [false, true]) for (let n = 0; n <= 6; n++) {
  const d = concepts.build('cs.2.debugging', { fixed, n }).data;
  assert.equal(d.expected, n * (n + 1) / 2);
  assert.equal(d.total, fixed ? n * (n + 1) / 2 : n * Math.max(0, n - 1) / 2);
  assert.equal(d.trace.length, fixed ? n : Math.max(0, n - 1));
  d.trace.forEach((row, i) => { assert.equal(row.i, i + 1); assert.equal(row.total, (i + 1) * (i + 2) / 2); });
  assert.equal(d.cases.filter(row => row.expected === row.actual).length, fixed ? 7 : 1);
}
for (const operation of ['double', 'add', 'square']) for (let first = -3; first <= 6; first++) for (let second = -3; second <= 6; second++) {
  const d = concepts.build('cs.2.functions', { operation, first, second }).data;
  const expected = n => operation === 'double' ? n * 2 : operation === 'add' ? n + 3 : n ** 2;
  assert.equal(d.firstResult, expected(first)); assert.equal(d.secondResult, expected(second));
  const swapped = concepts.build('cs.2.functions', { operation, first: second, second: first }).data;
  assert.equal(swapped.firstResult, d.secondResult); assert.equal(swapped.secondResult, d.firstResult);
}
for (const rule of ['size', 'color', 'shape']) for (let count = 0; count <= 6; count++) {
  const d = concepts.build('cs.0.sorting', { rule, count }).data;
  assert.equal(d.output.map(x => x.id).sort().join(''), 'ABCDEF');
  for (let i = 1; i < count; i++) assert.ok(d.output[i - 1][rule] <= d.output[i][rule]);
  assert.equal(d.output.slice(count).map(x => x.id).join(''), d.items.slice(count).map(x => x.id).join(''));
}
for (const unit of ['AB', 'ABB', 'AAB', 'ABC']) for (let repeats = 1; repeats <= 4; repeats++) {
  const d = concepts.build('cs.0.patterns', { unit, repeats }).data;
  assert.equal(d.length, unit.length * repeats); assert.equal(d.next, unit[0]);
  d.sequence.forEach((letter, i) => assert.equal(letter, unit[i % unit.length]));
}
for (const material of ['salt', 'copper', 'iodine']) for (const liquid of [false, true]) for (const field of [false, true]) {
  const d = concepts.build('chem.3.bonding', { material, liquid, field }).data;
  assert.equal(d.mobile, material === 'copper' || (material === 'salt' && liquid));
  assert.equal(d.conducting, field && d.mobile);
  assert.equal(d.drift, d.conducting ? 12 : 0);
}
for (let chelates = 0; chelates <= 3; chelates++) for (let oxidation = 2; oxidation <= 4; oxidation++) for (const mono of ['ammonia', 'chloride']) {
  const d = concepts.build('chem.4.inorganic', { chelates, oxidation, mono }).data;
  assert.equal(d.monodentate + 2 * chelates, 6); assert.equal(d.donors, 6);
  assert.equal(d.ligandCount, 6 - chelates);
  assert.equal(d.charge, mono === 'ammonia' ? oxidation : oxidation - 6 + 2 * chelates);
}
const hydrogenWording = concepts.build('chem.2.periodic', { atomicNumber: 1 }).readout;
assert.ok(hydrogenWording.includes('1 proton and, in a neutral atom, 1 electron.'));
assert.ok(hydrogenWording.includes('1 outer-shell electron.'));
for (let carbons = 4; carbons <= 8; carbons++) for (const branched of [false, true]) {
  const d = concepts.build('chem.3.organic-intro', { carbons, branched }).data;
  assert.equal(d.edges.length, carbons - 1); assert.equal(d.hydrogens, 2 * carbons + 2);
  assert.equal(d.degree.reduce((a, b) => a + b, 0), 2 * (carbons - 1));
  assert.equal(d.degree.filter(n => n === 3).length, branched ? 1 : 0);
  d.hydrogenCounts.forEach((h, i) => assert.equal(h + d.degree[i], 4));
  const visited = new Set([0]);
  for (let i = 0; i < carbons; i++) d.edges.forEach(([a, b]) => { if (visited.has(a)) visited.add(b); if (visited.has(b)) visited.add(a); });
  assert.equal(visited.size, carbons);
}
for (const closed of [false, true]) for (let progress = 0; progress <= 100; progress += 10) {
  const d = concepts.build('chem.2.reactions-intro', { closed, progress }).data;
  near(d.total, 100); near(d.gas, 4.4 * progress / 100);
  near(d.nongas + d.retained, d.reading); near(d.reading + d.escaped, 100);
  near(d.reading, closed ? 100 : 100 - .044 * progress);
}
for (let extent = 0; extent <= 4; extent++) {
  const d = concepts.build('chem.3.reactions', { extent }).data;
  assert.equal(d.zinc + d.zincIon, 4); assert.equal(d.copper + d.copperIon, 4);
  assert.equal(2 * d.zincIon + 2 * d.copperIon, 8);
  assert.equal(d.electrons, 2 * extent); assert.equal(d.zincIon, d.copper);
}
const expectedGroups = [1, 18, 1, 2, 13, 14, 15, 16, 17, 18, 1, 2, 13, 14, 15, 16, 17, 18];
for (let atomicNumber = 1; atomicNumber <= 18; atomicNumber++) {
  const d = concepts.build('chem.2.periodic', { atomicNumber }).data, atom = d.selected;
  assert.equal(atom.z, atomicNumber); assert.equal(atom.group, expectedGroups[atomicNumber - 1]);
  assert.equal(atom.shells.reduce((sum, n) => sum + n, 0), atomicNumber);
  assert.equal(atom.period, atomicNumber <= 2 ? 1 : atomicNumber <= 10 ? 2 : 3);
  assert.equal(atom.outer, atomicNumber <= 2 ? atomicNumber : atomicNumber <= 10 ? atomicNumber - 2 : atomicNumber - 10);
  assert.equal(new Set(d.elements.map(e => e.period + ':' + e.column)).size, 18);
}
for (let ph = 0; ph <= 14; ph++) for (let reference = 0; reference <= 14; reference++) {
  const d = concepts.build('chem.2.acids', { ph, reference }).data;
  near(d.hydronium / 10 ** -ph, 1); near(d.hydroxide / 10 ** (ph - 14), 1);
  near(d.hydronium * d.hydroxide / 1e-14, 1);
  near(d.ratio / (d.hydronium / 10 ** -reference), 1);
  near(d.ratio * concepts.build('chem.2.acids', { ph: reference, reference: ph }).data.ratio, 1);
}
const tinyDiffusion = concepts.build('chem.5.materials', { temperature: 500, barrier: 160, time: 20 });
assert.ok(tinyDiffusion.data.length > 0 && tinyDiffusion.data.length < .01);
assert.ok(tinyDiffusion.readout.includes(tinyDiffusion.data.length.toExponential(2) + ' micrometres'));
for (const object of ['spoon', 'cup', 'button']) for (const material of ['wood', 'steel', 'plastic']) {
  const d = concepts.build('chem.0.materials', { object, material }).data;
  assert.equal(d.object, object); assert.equal(d.material, material);
}
for (const clear of [false, true]) for (const flexible of [false, true]) for (const rain of [false, true]) {
  const d = concepts.build('chem.1.materials-props', { clear, flexible, rain }).data;
  equal(d.matches, [!flexible, !clear && !rain, true, !clear && !flexible]);
}
for (let temperature = 500; temperature <= 1200; temperature += 50) for (let barrier = 80; barrier <= 160; barrier += 10) for (let time = 0; time <= 400; time += 20) {
  const d = concepts.build('chem.5.materials', { temperature, barrier, time }).data;
  near(d.coefficient / (1e-6 * Math.exp(-barrier * 1000 / (8.314462618 * temperature))), 1);
  near(d.length ** 2, 4 * d.coefficient * time * 1e12);
  near(d.logCoefficient, Math.log10(d.coefficient));
  assert.ok(d.curve.every((value, i) => value >= -24 && value <= -9 && (!i || value > d.curve[i - 1])));
  if (time === 0) assert.equal(d.length, 0);
  if (time && time <= 100) near(concepts.build('chem.5.materials', { temperature, barrier, time: time * 4 }).data.length, d.length * 2);
}
for (const process of ['melting', 'reaction']) for (let stage = 0; stage <= 2; stage++) {
  const d = concepts.build('chem.1.changes', { process, stage }).data;
  assert.equal(d.hydrogenAtoms, 8); assert.equal(d.oxygenAtoms, 4);
  assert.equal(d.water, process === 'melting' ? 4 : 4 - 2 * stage);
  assert.equal(d.hydrogen, process === 'melting' ? 0 : 2 * stage);
  assert.equal(d.oxygen, process === 'melting' ? 0 : stage);
}
for (let left = -3; left <= 0; left++) for (let right = -3; right <= 0; right++) for (let temperature = 273; temperature <= 333; temperature += 5) {
  const d = concepts.build('chem.4.electrochem', { left, right, temperature }).data;
  near(d.voltage, 8.314462618 * temperature / (2 * 96485.33212) * Math.log(d.rightConcentration / d.leftConcentration));
  assert.equal(d.direction, Math.sign(right - left));
  near(d.voltage, -concepts.build('chem.4.electrochem', { left: right, right: left, temperature }).data.voltage);
  if (left === right) assert.equal(d.voltage, 0);
}
for (let h = 0; h <= 20; h++) for (let j = 0; j <= 16; j++) for (const mechanism of ['competitive', 'noncompetitive']) {
  const substrate = h / 2, inhibitor = j / 2, d = concepts.build('chem.5.biochem', { substrate, inhibitor, mechanism }).data;
  const expected = mechanism === 'competitive' ? substrate / (2 + inhibitor + substrate) : substrate / ((2 + substrate) * (1 + inhibitor / 2));
  near(d.rate, expected);
  assert.ok(d.rate >= 0 && d.rate <= d.reference + 1e-12);
  assert.ok(d.curve.every((v, i) => v <= d.vmax && (!i || v >= d.curve[i - 1])));
  near(concepts.build('chem.5.biochem', { substrate: d.km, inhibitor, mechanism }).data.rate, d.vmax / 2);
  if (!inhibitor) near(d.rate, d.reference);
  if (!substrate) assert.equal(d.rate, 0);
  if (mechanism === 'competitive') assert.equal(d.vmax, 1);
  else assert.equal(d.km, 2);
}
for (let economy = 50; economy <= 100; economy += 10) for (let yieldValue = 0; yieldValue <= 100; yieldValue += 10) for (let solvent = 0; solvent <= 500; solvent += 50) for (let recovery = 0; recovery <= 100; recovery += 10) {
  const d = concepts.build('chem.5.frontier', { economy, yield: yieldValue, solvent, recovery }).data;
  near(d.product + d.waste + d.recovered, d.input);
  near(d.product, economy * yieldValue / 100);
  assert.ok(d.product >= 0 && d.waste >= 0 && d.recovered >= 0);
  if (!yieldValue) { assert.equal(d.eFactor, null); assert.equal(d.grossPMI, null); }
  else { near(d.grossPMI, d.eFactor + 1 + d.recovered / d.product); near(d.eFactor * d.product, d.waste); }
}
for (let concentration = 0; concentration <= 10; concentration++) for (let path = 1; path <= 3; path++) for (let b = 0; b <= 10; b++) for (const correct of [false, true]) {
  const blank = b / 10, d = concepts.build('chem.4.analytical', { concentration, path, blank, correct }).data;
  near(d.inferred, concentration + (correct ? 0 : blank / (.1 * path)));
  near(-Math.log10(d.transmittance), d.measured);
  assert.ok(d.transmittance > 0 && d.transmittance <= 1);
}
for (let alpha = 2; alpha <= 30; alpha++) for (let c = -8; c <= 8; c++) {
  const centre = c / 4, d = concepts.build('chem.5.compchem', { alpha, centre }).data;
  assert.ok(d.energy >= .5 - 1e-12);
  near(d.energy - .5, (d.a - 1) ** 2 / (4 * d.a) + centre ** 2 / 2);
  near(d.energy, d.kinetic + d.potential);
}
for (const alpha of [2, 10, 30]) for (const centre of [-2, 0, .5]) {
  const a = alpha / 10, d = concepts.build('chem.5.compchem', { alpha, centre }).data;
  let norm = 0, kinetic = 0, potential = 0;
  for (let i = 0; i <= 5600; i++) {
    const x = -14 + i * .005, rho = Math.sqrt(a / Math.PI) * Math.exp(-a * (x - centre) ** 2), weight = .005 * (i === 0 || i === 5600 ? .5 : 1);
    norm += rho * weight;
    kinetic += .5 * a * a * (x - centre) ** 2 * rho * weight;
    potential += .5 * x * x * rho * weight;
  }
  near(norm, 1, 1e-9); near(kinetic, d.kinetic, 1e-9); near(potential, d.potential, 1e-9);
}
for (let water = 100; water <= 500; water += 100) for (let solute = 0; solute <= 20; solute++) for (let sand = 0; sand <= 10; sand++) for (const filter of [false, true]) {
  const d = concepts.build('chem.2.mixtures', { water, solute, sand, filter }).data;
  assert.equal(d.dissolved + d.excess, solute);
  assert.ok(d.dissolved <= d.capacity && d.dissolved >= 0 && d.excess >= 0);
  equal(d.vessel.map((v, i) => v + d.residue[i]), [d.dissolved, d.excess, sand]);
  assert.equal(d.vessel[0], Math.min(solute, water / 25));
  assert.equal(d.residue[0], 0);
  if (filter) equal(d.vessel.slice(1), [0, 0]);
  else equal(d.residue, [0, 0, 0]);
}
for (let protons = 1; protons <= 10; protons++) for (let neutrons = 0; neutrons <= 12; neutrons++) for (let electrons = 0; electrons <= 12; electrons++) {
  const d = concepts.build('chem.3.atomic-structure', { protons, neutrons, electrons }).data;
  assert.equal(d.mass, protons + neutrons);
  assert.equal(d.charge, protons - electrons);
  assert.equal(d.symbol, ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne'][protons - 1]);
}
for (let volume = 5; volume <= 30; volume++) for (let temperature = 200; temperature <= 600; temperature += 10) for (let amount = 1; amount <= 5; amount++) {
  const d = concepts.build('chem.3.gases', { volume, temperature, amount }).data;
  near(d.pressure * volume / (temperature * amount), 8.314462618);
  assert.ok(d.curve.every((p, i) => p > 0 && (!i || p < d.curve[i - 1])));
  near(d.curve[0] / d.curve[50], 6);
}
for (let change = -60; change <= 60; change += 10) for (let barrier = 20; barrier <= 80; barrier += 10) for (const catalyst of [false, true]) {
  const d = concepts.build('chem.3.energy', { change, barrier, catalyst }).data;
  near(d.forward - d.reverse, change);
  assert.ok(d.forward > 0 && d.reverse > 0 && d.active <= d.peak);
  near(d.peak - d.active, catalyst ? barrier / 2 : 0);
}
for (let initialB = 0; initialB <= 10; initialB++) for (let power = -2; power <= 2; power++) for (let progress = 0; progress <= 100; progress += 10) {
  const d = concepts.build('chem.4.physical', { initialB, power, progress }).data;
  near(d.a + d.b, 10);
  near(d.equilibriumB / (10 - d.equilibriumB), 2 ** power);
  assert.ok(d.a >= 0 && d.b >= 0);
  if (!progress) near(d.b, initialB);
  if (progress === 100) { near(d.q, d.k); assert.equal(d.direction, 'balanced'); }
  else if (d.q === null) assert.equal(d.direction, 'towards A');
  else if (Math.abs(d.q - d.k) > 1e-10) assert.equal(d.direction, d.q < d.k ? 'towards B' : 'towards A');
}
for (let hydrogen = 1; hydrogen <= 6; hydrogen++) for (let oxygen = 1; oxygen <= 6; oxygen++) for (let water = 1; water <= 6; water++) {
  const d = concepts.build('chem.3.stoichiometry', { hydrogen, oxygen, water }).data;
  equal(d.left, [hydrogen * 2, oxygen * 2]);
  equal(d.right, [water * 2, water]);
  assert.equal(d.balanced, hydrogen === water && water === oxygen * 2);
  equal(d.difference, [2 * (water - hydrogen), water - 2 * oxygen]);
}
for (const material of ['salt', 'sand', 'oil']) for (const resting of [false, true]) {
  const d = concepts.build('chem.0.mixing', { material, resting }).data;
  assert.equal(d.layer, material === 'oil' && resting);
  assert.equal(d.sediment, material === 'sand' && resting);
  assert.equal(d.dispersed, material === 'salt' || !resting);
}
for (let stage = 0; stage <= 4; stage++) {
  const d = concepts.build('chem.0.water-states', { stage }).data;
  assert.equal(d.counts.reduce((sum, n) => sum + n, 0), 12);
  assert.equal(d.counts.filter(n => n > 0).length, stage % 2 ? 2 : 1);
  if (stage % 2 === 0) assert.equal(d.counts[stage / 2], 12);
}
for (const phase of ['solid', 'liquid', 'gas']) for (let width = 140; width <= 300; width += 10) {
  const d = concepts.build('chem.1.matter', { phase, width }).data;
  assert.equal(d.count, 12);
  assert.ok(d.width <= width && d.height <= 180 && d.height > 0);
  assert.ok(Math.abs(d.area - (phase === 'gas' ? width * 180 : 9600)) < 1e-9);
  if (phase === 'solid') { assert.equal(d.width, 100); assert.equal(d.height, 96); }
  else assert.equal(d.width, width);
}
for (let stage = 0; stage <= 5; stage++) for (const contact of [false, true]) {
  const d = concepts.build('bio.1.health', { stage, contact }).data;
  assert.equal(d.returned, contact && stage >= 4);
  assert.equal(d.particles, stage < 4 ? 12 : contact ? 6 : 0);
}
for (let percent = 0; percent <= 100; percent++) for (let generation = 0; generation <= 6; generation++) for (const drug of [false, true]) {
  const d = concepts.build('bio.3.microbiology', { percent, generation, drug }).data;
  let r = percent, s = 100 - percent;
  for (let i = 0; i < generation; i++) { r *= drug ? 1.2 : 1.8; s *= drug ? .25 : 2; }
  assert.ok(Math.abs(d.selected.total - r - s) < 1e-9);
  assert.ok(Math.abs(d.selected.fraction - r / (r + s)) < 1e-12);
  assert.ok(d.history.every(v => v.fraction >= 0 && v.fraction <= 1 && v.total > 0));
}
for (let a = 0; a <= 20; a++) for (let b = 0; b <= 20; b++) for (let kd = 1; kd <= 10; kd++) {
  const f = concepts.build('bio.5.immunology', { a, b, kd }).data.fractions;
  assert.ok(Math.abs(f.reduce((sum, v) => sum + v, 0) - 1) < 1e-12);
  assert.ok(f.every(v => v >= 0 && v <= 1));
  assert.ok(Math.abs(f[0] - f[2] * a / kd) < 1e-12);
  assert.ok(Math.abs(f[1] - f[2] * b / 5) < 1e-12);
  if (b < 20) assert.ok(concepts.build('bio.5.immunology', { a, b: b + 1, kd }).data.fractions[0] <= f[0]);
}
for (let q = 0; q <= 20; q++) for (let t = 0; t <= 10; t++) for (const intervention of [false, true]) for (const mechanism of ['linear', 'saturating']) {
  const input = q / 4, tolerance = t / 10, d = concepts.build('bio.5.frontier', { input, tolerance, intervention, mechanism }).data;
  assert.equal(d.x, intervention ? input : 1);
  assert.equal(d.compatible[mechanism === 'linear' ? 0 : 1], true);
  if (!intervention || input === 0 || input === 1) assert.ok(d.compatible.every(Boolean));
  else if (tolerance === 0) assert.equal(d.compatible.filter(Boolean).length, 1);
  assert.ok(d.low <= d.observed && d.high >= d.observed);
}
for (let tenths = 0; tenths <= 30; tenths++) for (const tau of [5, 20, 30]) for (const refractory of [0, 5, 10]) {
  const drive = tenths / 10, d = concepts.build('bio.4.neuro', { drive, tau, refractory }).data;
  const rise = drive > 1 ? -tau * Math.log(1 - 1 / drive) : null;
  const count = rise === null || rise > 100 ? 0 : Math.floor((100 - rise) / (rise + refractory)) + 1;
  assert.equal(d.spikes.length, count);
  assert.ok(d.points.every(([t, v]) => t >= 0 && t <= 100 && v >= -1e-12 && v <= 1 + 1e-12));
  if (rise !== null) assert.ok(Math.abs(d.rise - rise) < 1e-10);
}
for (const [drive, tau, refractory] of [[1.5, 20, 5], [3, 5, 0], [.9, 10, 5]]) {
  let v = 0, blockedUntil = 0; const spikes = [], dt = .001;
  for (let i = 0; i < 100000; i++) {
    const t = (i + 1) * dt;
    if (t < blockedUntil) continue;
    v += dt * (drive - v) / tau;
    if (v >= 1) { spikes.push(t); v = 0; blockedUntil = t + refractory; }
  }
  const d = concepts.build('bio.4.neuro', { drive, tau, refractory }).data;
  assert.equal(d.spikes.length, spikes.length);
  spikes.forEach((t, i) => assert.ok(Math.abs(t - d.spikes[i]) < .1));
}
for (let p50 = 10; p50 <= 50; p50++) for (let cooperativity = 10; cooperativity <= 40; cooperativity++) {
  const d = concepts.build('bio.4.physiology', { pressure: p50, p50, cooperativity }).data;
  assert.equal(d.selected, .5); assert.equal(d.curve[0], 0);
  assert.ok(d.curve.every((v, i) => v >= 0 && v <= 1 && (!i || v >= d.curve[i - 1])));
  assert.ok(d.difference >= 0 && d.difference <= 1);
  if (cooperativity === 10) d.curve.forEach((v, p) => assert.ok(Math.abs(v - p / (p50 + p)) < 1e-12));
}
for (let depletion = 2; depletion <= 10; depletion++) {
  let previous = 0;
  for (let travel = 1; travel <= 20; travel++) {
    const d = concepts.build('bio.4.ethology', { travel, depletion, residence: 0 }).data;
    assert.equal(d.selected, 0); assert.ok(d.optimum > previous && d.optimum < 40); previous = d.optimum;
    const derivative = 100 / depletion * Math.exp(-d.optimum / depletion);
    assert.ok(Math.abs(derivative - d.best) < 1e-10);
    for (let i = 0; i <= 400; i++) {
      const t = i / 10, rate = 100 * (1 - Math.exp(-t / depletion)) / (travel + t);
      assert.ok(rate <= d.best + 1e-10, 'Computed marginal-value optimum dominates the independent residence grid');
    }
  }
}
for (let depth = 1; depth <= 8; depth++) for (let alternate = 0; alternate <= 8; alternate++) for (const filter of [false, true]) {
  const d = concepts.build('bio.4.genomics', { depth, alternate, filter }).data;
  const used = depth - Number(filter), supporting = Math.min(alternate, used);
  assert.equal(d.usable, used); assert.equal(d.support, supporting);
  assert.equal(d.fraction, used ? supporting / used : null);
  assert.equal(d.reads.filter(r => r.flagged).length, 1);
  assert.ok(d.reads.every(r => r.sequence.length === 8));
}
for (const sequence of ['ACGTAC', 'ACTTAC', 'ACGTTAC', 'ACGAC', 'AGCTAC', 'AAAAAA']) for (let gap = 1; gap <= 3; gap++) for (let mismatch = 1; mismatch <= 5; mismatch++) {
  const d = concepts.build('bio.5.comp-bio', { sequence, gap, mismatch }).data;
  let best = Infinity, ways = 0;
  const enumerate = (i, j, cost) => {
    if (cost > best) return;
    if (i === d.reference.length && j === sequence.length) { if (cost < best) { best = cost; ways = 0; } ways++; return; }
    if (i < d.reference.length && j < sequence.length) enumerate(i + 1, j + 1, cost + (d.reference[i] === sequence[j] ? 0 : mismatch));
    if (i < d.reference.length) enumerate(i + 1, j, cost + gap);
    if (j < sequence.length) enumerate(i, j + 1, cost + gap);
  };
  enumerate(0, 0, 0);
  assert.equal(d.cost, best); assert.equal(d.ways, ways);
  assert.equal(d.first.replaceAll('-', ''), d.reference); assert.equal(d.second.replaceAll('-', ''), sequence);
  assert.equal(d.first.length, d.second.length);
  let scored = 0;
  for (let i = 0; i < d.first.length; i++) scored += d.first[i] === '-' || d.second[i] === '-' ? gap : d.first[i] === d.second[i] ? 0 : mismatch;
  assert.equal(scored, best);
}
for (const production of [0, 6, 10]) for (const removal of [10, 50, 100]) for (const threshold of [1, 4, 10]) for (const feedback of [false, true]) {
  const d = concepts.build('bio.5.systems-bio', { production, removal, threshold, feedback }).data;
  const residual = production / (feedback ? 1 + (d.equilibrium / threshold) ** 2 : 1) - removal / 100 * d.equilibrium;
  assert.ok(Math.abs(residual) < 1e-9);
  assert.ok(d.values.every((v, i) => v >= -1e-10 && v <= d.open[i] + 1e-6 && (!i || v >= d.values[i - 1] - 1e-10)));
  if (!feedback) assert.ok(d.values.every((v, i) => Math.abs(v - d.open[i]) < 1e-6));
}
for (const threshold of [1, 4, 10]) {
  let x = 0; const h = .0001;
  for (let i = 0; i < 100000; i++) x += h * (10 / (1 + (x / threshold) ** 2) - .1 * x);
  const d = concepts.build('bio.5.systems-bio', { production: 10, removal: 10, threshold, feedback: true }).data;
  assert.ok(Math.abs(x - d.final) < .001, 'Feedback integration agrees with a fine-step independent Euler method');
}
for (const initial of [0, 5, 50, 100]) for (const capacity of [10, 50, 100]) for (const rate of [0, 30, 100]) {
  const m = concepts.build('bio.3.ecology', { initial, capacity, rate });
  let n = initial;
  const f = value => rate / 100 * value * (1 - value / capacity), h = .01;
  for (let i = 0; i < 2000; i++) {
    const k1 = f(n), k2 = f(n + h * k1 / 2), k3 = f(n + h * k2 / 2), k4 = f(n + h * k3);
    n += h * (k1 + 2 * k2 + 2 * k3 + k4) / 6;
  }
  assert.ok(Math.abs(m.data.final - n) < 1e-5, 'Closed-form logistic trajectory agrees with independent RK4 integration');
  assert.ok(Math.abs(m.data.values[0] - initial) < 1e-10);
  assert.ok(m.data.values.every(v => v >= -1e-10 && v <= Math.max(initial, capacity) + 1e-10));
}
for (let opening = 0; opening <= 100; opening++) for (let humidity = 0; humidity <= 100; humidity++) {
  const d = concepts.build('bio.3.botany', { opening, humidity }).data;
  assert.equal(d.carbon, opening / 100);
  assert.ok(Math.abs(d.water * 10000 - opening * (100 - humidity)) < 1e-9);
  assert.ok(d.water <= d.carbon + 1e-12 && d.water >= 0);
  if (humidity === 100 || opening === 0) assert.equal(d.water, 0);
}
for (let km = 1; km <= 50; km++) for (const vmax of [10, 50, 100]) for (const substrate of [0, km, 100]) {
  const d = concepts.build('bio.4.biochem', { km, vmax, substrate }).data;
  assert.ok(Math.abs(d.velocity * (km + substrate) - vmax * substrate) < 1e-9);
  assert.ok(d.velocity >= 0 && d.velocity < vmax);
  if (substrate === km) assert.equal(d.velocity, vmax / 2);
  assert.ok(d.curve.every((v, i) => !i || v >= d.curve[i - 1]));
}
for (let percent = 0; percent <= 100; percent++) for (const environment of ['a', 'b', 'equal']) for (let generation = 0; generation <= 12; generation++) {
  const m = concepts.build('bio.3.evolution', { percent, environment, generation });
  const a = percent * (environment === 'a' ? 2 ** generation : 1), b = (100 - percent) * (environment === 'b' ? 2 ** generation : 1);
  assert.ok(Math.abs(m.data.p - a / (a + b)) < 1e-12, 'Selection agrees with independently propagated reproductive weights');
  assert.ok(Math.abs(m.data.p + m.data.q - 1) < 1e-12);
  assert.ok(m.data.history.every(p => p >= 0 && p <= 1));
  if (!percent || percent === 100 || environment === 'equal') assert.ok(Math.abs(m.data.p - percent / 100) < 1e-12);
}
for (let percent = 0; percent <= 100; percent++) for (let inbreeding = 0; inbreeding <= 100; inbreeding++) {
  const m = concepts.build('bio.4.evo-bio', { percent, inbreeding });
  const [aa, ab, bb] = m.data.genotype, p = percent / 100;
  assert.ok(m.data.genotype.every(v => v >= -1e-12 && v <= 1 + 1e-12));
  assert.ok(Math.abs(aa + ab + bb - 1) < 1e-12);
  assert.ok(Math.abs((2 * aa + ab) / 2 - p) < 1e-12, 'Counting allele copies recovers the fixed frequency');
  assert.ok(ab <= m.data.baseline[1] + 1e-12);
  if (!inbreeding) assert.deepEqual(plain(m.data.genotype), plain(m.data.baseline));
  if (inbreeding === 100) { assert.ok(Math.abs(aa - p) < 1e-12); assert.equal(ab, 0); assert.ok(Math.abs(bb - (1 - p)) < 1e-12); }
}
for (let step = 0; step <= 7; step++) for (const oxygen of [false, true]) {
  const m = concepts.build('bio.1.human-body', { step, oxygen });
  assert.equal(m.data.name, ['Right heart', 'Lungs', 'Left heart', 'Body tissues'][step % 4]);
  assert.equal(m.data.rich, [1, 2, 5, 6].includes(step));
  assert.equal(m.data.lap, step < 4 ? 0 : 1);
  assert.ok(m.readout.includes(oxygen ? 'oxygen.' : 'labels are hidden'));
}
for (const [material, route] of Object.entries({ glucose: ['Small intestine', 'Portal blood', 'Liver', 'Body tissues'],
  co2: ['Body cells', 'Blood', 'Lungs', 'Exhaled air'], urea: ['Liver', 'Blood', 'Kidneys', 'Urine'],
  residue: ['Small intestine', 'Colon', 'Rectum', 'Outside the body'] })) for (let step = 0; step <= 3; step++) {
  const m = concepts.build('bio.2.digestion', { material, step });
  assert.deepEqual(plain(m.data.nodes), route);
  assert.deepEqual(plain(m.data.traversed), route.slice(0, step + 1));
  assert.equal(m.data.current, route[step]);
}
for (let haploid = 1; haploid <= 3; haploid++) {
  let expectedCells = 1;
  for (let divisions = 0; divisions <= 3; divisions++) {
    const m = concepts.build('bio.2.reproduction', { haploid, divisions });
    assert.equal(m.data.cells, expectedCells);
    assert.equal(m.data.diploid, haploid + haploid);
    assert.equal(m.data.total / m.data.cells, haploid + haploid);
    expectedCells += expectedCells;
  }
}
for (const [feature, expected] of Object.entries({ six: ['beetle'], eight: ['spider'], wings: ['beetle', 'sparrow'], none: ['trout'] })) {
  for (const count of [false, true]) {
    const model = concepts.build('bio.0.animals', { feature, count });
    assert.deepEqual(plain(model.data.matches), expected);
    assert.deepEqual(plain(model.data.animals.map(a => a.legs)), [6, 8, 2, 0]);
    assert.ok(model.readout.includes(count ? 'Leg counts:' : 'labels are hidden'));
  }
}
for (const pool of [false, true]) for (const woodland of [false, true]) for (const route of [false, true]) {
  const model = concepts.build('bio.1.habitats', { pool, woodland, route });
  const locations = [pool ? 'pool' : null, woodland ? 'woodland' : null].filter(Boolean);
  const reachable = route && locations.includes('pool') && locations.includes('woodland');
  assert.equal(model.data.connected, reachable);
  assert.equal(model.data.available, locations.length);
  assert.equal(model.data.missing.length, [pool, woodland, route].filter(v => !v).length);
}
const sensoryPairs = { sight: ['Light', 'Eye'], hearing: ['Vibration', 'Ear'], smell: ['Airborne molecules', 'Nose'], taste: ['Dissolved molecules', 'Tongue'], touch: ['Gentle pressure', 'Skin'] };
for (const [sense, expected] of Object.entries(sensoryPairs)) for (let step = 0; step < 3; step++) {
  const model = concepts.build('bio.0.body', { sense, step });
  assert.deepEqual([model.data.stimulus, model.data.organ], expected);
  assert.equal(model.data.reached, step + 1);
  assert.ok(model.readout.includes(model.data.stages[step]));
}
const northSeasons = ['Winter', 'Winter', 'Spring', 'Spring', 'Spring', 'Summer', 'Summer', 'Summer', 'Autumn', 'Autumn', 'Autumn', 'Winter'];
for (let month = 1; month <= 12; month++) {
  const north = concepts.build('bio.0.seasons', { month, hemisphere: 'north' });
  const south = concepts.build('bio.0.seasons', { month, hemisphere: 'south' });
  assert.equal(north.data.season, northSeasons[month - 1]);
  assert.equal(south.data.season, northSeasons[(month + 5) % 12]);
  assert.equal(north.data.season, south.data.opposite);
  assert.equal(south.data.season, north.data.opposite);
}
for (const specimen of ['plant', 'seed', 'flame', 'robot', 'rock']) for (const inside of [false, true]) {
  const model = concepts.build('bio.0.living', { specimen, inside });
  assert.equal(model.data.alive, ['plant', 'seed'].includes(specimen));
  assert.equal(model.data.cells, ['plant', 'seed'].includes(specimen));
  assert.ok(model.readout.includes(inside ? 'cells' : 'Look inside'));
}
const taxa = ['salmon', 'frog', 'mouse', 'bat', 'lizard', 'pigeon'];
const clades = { mammals: ['mouse', 'bat'], reptiles: ['lizard', 'pigeon'], amniotes: ['mouse', 'bat', 'lizard', 'pigeon'],
  tetrapods: ['frog', 'mouse', 'bat', 'lizard', 'pigeon'], vertebrates: taxa };
for (const first of taxa) for (const second of taxa) for (const flight of [false, true]) {
  const d = concepts.build('bio.2.classification', { first, second, flight }).data;
  const expected = first === second ? first : Object.keys(clades).find(group => clades[group].includes(first) && clades[group].includes(second));
  assert.equal(d.common, expected);
  assert.equal(d.same, first === second);
  assert.equal(concepts.build('bio.2.classification', { first: second, second: first }).data.common, expected, 'Comparison is symmetric');
  for (const path of [d.firstPath, d.secondPath]) { assert.equal(new Set(path).size, path.length); assert.equal(path[path.length - 1], 'vertebrates'); }
}
const allFoodRoutes = { foxes: [['grass', 'rabbits', 'foxes'], ['grass', 'mice', 'foxes']], owls: [['grass', 'mice', 'owls']] };
for (const removed of ['none', 'grass', 'rabbits', 'mice', 'foxes', 'owls']) for (const target of ['foxes', 'owls']) {
  const d = concepts.build('bio.2.ecosystems', { removed, target }).data;
  equal(d.routes, allFoodRoutes[target].filter(path => !path.includes(removed)));
  assert.ok(d.active.every(edge => !edge.includes(removed)));
  for (const route of d.routes) for (let i = 1; i < route.length; i++) assert.ok(d.active.some(edge => edge[0] === route[i - 1] && edge[1] === route[i]));
}
for (let sugar = 0; sugar <= 6; sugar++) for (let steps = 0; steps <= 6; steps++) for (const yeast of [false, true]) {
  const d = concepts.build('bio.2.microbes', { sugar, steps, yeast }).data;
  assert.ok(d.consumed >= 0 && d.consumed <= steps && d.left >= 0);
  assert.equal(d.consumed + d.left, sugar);
  assert.equal(d.ethanol * 2 + d.gas + 6 * d.left, 6 * sugar, 'Carbon conservation');
  assert.equal(d.ethanol * 6 + 12 * d.left, 12 * sugar, 'Hydrogen conservation');
  assert.equal(d.ethanol + 2 * d.gas + 6 * d.left, 6 * sugar, 'Oxygen conservation');
  assert.equal(d.ethanol, d.gas);
  if (!yeast) assert.equal(d.consumed, 0); else assert.equal(d.consumed, Math.min(sugar, steps));
}
for (let step = 0; step <= 4; step++) for (const water of [false, true]) for (const warmth of [false, true]) for (const light of [false, true]) {
  const d = concepts.build('bio.0.plants', { step, water, warmth, light }).data;
  assert.equal(d.stage, water ? warmth ? step : Math.min(step, 1) : 0);
  assert.equal(d.pale, !light && d.stage >= 3);
  assert.equal(concepts.build('bio.0.plants', { step, water, warmth, light: !light }).data.stage, d.stage, 'Light does not prevent bean germination');
}
for (const part of ['roots', 'stem', 'leaves', 'flower']) for (const flow of [false, true]) {
  const model = concepts.build('bio.1.plants-parts', { part, flow });
  assert.ok(model.data.job.length > 50);
  assert.ok(model.readout.includes(flow ? 'soil → roots → stem → leaves' : 'hidden'));
}
for (let carbon = 0; carbon <= 18; carbon++) for (let water = 0; water <= 18; water++) for (const light of [false, true]) {
  const d = concepts.build('bio.2.photosynthesis', { carbon, water, light }).data;
  assert.ok(Number.isInteger(d.sugar) && d.sugar >= 0 && d.carbonLeft >= 0 && d.waterLeft >= 0);
  assert.equal(6 * d.sugar + d.carbonLeft, carbon, 'Conserve carbon atoms');
  assert.equal(12 * d.sugar + 2 * d.waterLeft, 2 * water, 'Conserve hydrogen atoms');
  assert.equal(6 * d.sugar + 2 * d.oxygen + 2 * d.carbonLeft + d.waterLeft, 2 * carbon + water, 'Conserve oxygen atoms');
  assert.equal(d.oxygen, d.sugar * 6);
  if (light) assert.ok(d.carbonLeft < 6 || d.waterLeft < 6, 'Maximum whole batches');
  else assert.equal(d.sugar, 0);
}
for (let energy = 100; energy <= 1000; energy += 100) for (let percent = 5; percent <= 20; percent += 5) {
  const d = concepts.build('bio.1.food-chains', { energy, percent }).data;
  near(d.levels[0], energy);
  for (let i = 0; i < 2; i++) { near(d.levels[i + 1] / d.levels[i], percent / 100); near(d.levels[i], d.levels[i + 1] + d.other[i]); }
  near(d.other[0] + d.other[1] + d.levels[2], energy);
}
for (let angle = 15; angle <= 150; angle += 15) for (let radius = 1; radius <= 4; radius += .5) {
  const d = concepts.build('math.5.diffgeo', { angle, radius }).data;
  near(d.area / (4 * Math.PI * radius * radius), angle / 720);
  near(d.curvature * d.area, d.excess);
  near(d.angleSum * Math.PI / 180 - Math.PI, d.excess);
  // Integrate R² cos(latitude) dlatitude dlongitude over the spherical patch.
  let area = 0;
  for (let j = 0; j < 2048; j++) area += radius * radius * Math.cos((j + .5) * Math.PI / 4096) * Math.PI / 4096 * angle * Math.PI / 180;
  near(d.area, area, 2e-6);
}
for (let radius = .5; radius <= 3; radius += .5) for (let a = -2; a <= 2; a++) for (let b = -2; b <= 2; b++) for (const clockwise of [false, true]) {
  const d = concepts.build('math.5.complex-analysis', { radius, a, b, clockwise }).data;
  if (radius === 2 && b !== 0) { assert.equal(d.onPath, true); assert.equal(d.imaginary, null); continue; }
  assert.equal(d.onPath, false);
  // Direct periodic quadrature of f(z(t)) z′(t), independent of residue selection.
  let real = 0, imaginary = 0;
  for (let k = 0; k < 1024; k++) {
    const t = (k + .5) * 2 * Math.PI / 1024, x = radius * Math.cos(t), y = radius * Math.sin(t);
    const denominator = (x - 2) ** 2 + y * y;
    const u = a * x / radius ** 2 + (b ? b * (x - 2) / denominator : 0);
    const v = -a * y / radius ** 2 - (b ? b * y / denominator : 0);
    real += (-u * y - v * x) * 2 * Math.PI / 1024;
    imaginary += (u * x - v * y) * 2 * Math.PI / 1024;
  }
  near(real, 0); near(d.imaginary, (clockwise ? -1 : 1) * imaginary);
}
for (let row = 1; row <= 6; row++) for (let mask = 0; mask < 64; mask++) {
  const d = concepts.build('math.5.logic', { ['row' + row]: mask }).data;
  equal(d.rows[row - 1], Array.from({ length: 6 }, (_, i) => Math.floor(mask / 2 ** i) % 2));
  for (let i = 0; i < 6; i++) {
    assert.equal(d.diagonal[i] + d.rows[i][i], 1);
    assert.notDeepEqual(plain(d.diagonal), plain(d.rows[i]));
    assert.equal(d.members.includes(i + 1), Boolean(d.diagonal[i]));
  }
}
// Independent sieve checks every finite experiment and selected value.
const primeSieve = Array(3702).fill(true); primeSieve[0] = primeSieve[1] = false;
for (let p = 2; p < primeSieve.length; p++) if (primeSieve[p])
  for (let multiple = p * 2; multiple < primeSieve.length; multiple += p) primeSieve[multiple] = false;
for (let bound = 0; bound <= 60; bound++) for (let selected = 0; selected <= 60; selected++) {
  const d = concepts.build('math.5.frontier', { bound, selected }).data;
  assert.equal(d.checked.length, bound + 1);
  for (const row of [...d.checked, d.selected]) {
    assert.equal(row.value, row.n * row.n + row.n + 41);
    assert.equal(row.prime, primeSieve[row.value]);
    if (!row.prime) assert.equal(row.value % row.divisor, 0);
  }
  assert.equal(d.counterexamples.length > 0, bound >= 40);
}
const registry = context.window.PrimerLessonModels;
equal([...spatial.supported].sort(), [...EXISTING_SPATIAL, ...CROSS_SPATIAL].sort());
equal([...concepts.supported].sort(), [...CONCEPTS].sort());
assert.ok(registry.supported.includes('spatial-3d'));
assert.ok(registry.supported.includes('concept-lab'));

const nodes = fs.readdirSync(path.join(ROOT, 'data/curriculum')).filter(file => /^\d.*\.json$/.test(file))
  .flatMap(file => JSON.parse(fs.readFileSync(path.join(ROOT, 'data/curriculum', file), 'utf8')).nodes);
const entries = nodes.flatMap(node => (node.lesson_media || [])
  .filter(item => item.kind === 'model').map(item => ({ node, item })));
const crossEntries = entries.filter(({ node, item }) =>
  CROSS_SPATIAL.includes(node.id) && item.renderer === 'spatial-3d' || item.renderer === 'concept-lab');
equal(crossEntries.map(({ node }) => node.id).sort(), [...CROSS_SPATIAL, ...CONCEPTS].sort(),
  'Exactly the registered cross-subject lessons must bind the models');
for (const { node, item } of crossEntries) {
  equal(item.props, { scenario: node.id });
  assert.equal(item.renderer, CROSS_SPATIAL.includes(node.id) ? 'spatial-3d' : 'concept-lab');
}
assert.equal(entries.filter(({ item }) => !['spatial-3d', 'concept-lab'].includes(item.renderer)).length,
  70, 'All 70 earlier lesson models remain reachable');
const page = fs.readFileSync(path.join(ROOT, 'web/index.html'), 'utf8');
const scripts = [...page.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["']/g)].map(match => match[1]);
for (const file of ['spatial-cross-subject.js', 'concept-models.js']) {
  assert.equal(scripts.filter(src => src === '/app/' + file).length, 1, file + ': loaded exactly once');
  assert.ok(scripts.indexOf('/app/' + file) < scripts.indexOf('/app/lesson-models.js'), file + ': loaded before registry');
}
assert.ok(scripts.indexOf('/app/spatial-models.js') < scripts.indexOf('/app/spatial-cross-subject.js'));

let buildChecks = 0;
let controlChecks = 0;
let interactionChecks = 0;
function finiteNumbers(value, location = '') {
  if (typeof value === 'number') assert.ok(Number.isFinite(value), location + ': finite number');
  else if (value && typeof value === 'object') Object.entries(value).forEach(([key, child]) => finiteNumbers(child, location + '.' + key));
}
function verify(api, id, supplied) {
  const result = api.build(id, supplied);
  assert.ok(result, id + ': build exists');
  finiteNumbers(result, id);
  equal(result, api.build(id, supplied), id + ': deterministic rebuild');
  for (const key of ['readout', 'note']) assert.ok(typeof result[key] === 'string' && result[key].trim(), id + ': ' + key);
  assert.ok(Array.isArray(result.legend) && result.legend.length, id + ': legend');
  if (api === spatial) {
    assert.ok(result.primitives.length > 0 && result.primitives.length <= 3000, id + ': geometry budget');
    for (const primitive of result.primitives) {
      assert.ok(['polygon', 'line', 'sphere', 'label'].includes(primitive.kind));
      assert.ok(primitive.points.length > 0);
      for (const point of primitive.points) assert.ok(point.length === 3 && point.every(Number.isFinite));
      if (primitive.kind === 'sphere') assert.ok(primitive.radius > 0);
      if (primitive.width != null) assert.ok(primitive.width > 0);
      if (primitive.opacity != null) assert.ok(primitive.opacity >= 0 && primitive.opacity <= 1);
    }
  }
  buildChecks += 1;
  return result;
}
const teaching = result => JSON.stringify({ data: result.data, primitives: result.primitives,
  readout: result.readout, note: result.note, legend: result.legend });
const controlValues = control => control.options ? control.options.map(option => option.value)
  : control.type === 'toggle' ? [false, true] : [control.min, (control.min + control.max) / 2, control.max];
for (const [api, ids] of [[spatial, CROSS_SPATIAL], [concepts, CONCEPTS]]) {
  for (const id of ids) {
    const initial = verify(api, id);
    const controls = api.controls(id);
    assert.ok(controls.length, id + ': controls exist');
    assert.equal(new Set(controls.map(control => control.key)).size, controls.length, id + ': unique controls');
    equal(verify(api, id, { unknown: 'ignored' }), initial, id + ': unknown state keys ignored');
    for (const control of controls) {
      const versions = controlValues(control).map(value => verify(api, id, { ...initial.state, [control.key]: value }));
      assert.ok(versions.some(result => teaching(result) !== teaching(initial)), id + ': meaningful ' + control.key);
      const invalid = control.options ? ['missing', 'constructor', '__proto__', null, {}]
        : control.type === 'toggle' ? ['false', 0, 1, null, {}] : [NaN, Infinity, -Infinity, 'not a number', {}];
      for (const value of invalid) equal(verify(api, id, { [control.key]: value }), initial, id + ': invalid ' + control.key);
      if (!control.options && control.type !== 'toggle') {
        near(verify(api, id, { [control.key]: -Number.MAX_VALUE }).state[control.key], control.min);
        near(verify(api, id, { [control.key]: Number.MAX_VALUE }).state[control.key], control.max);
      }
      equal(verify(api, id, Object.create({ [control.key]: controlValues(control)[0] })), initial,
        id + ': inherited state cannot override defaults');
      controlChecks += 1;
    }
  }
  for (const id of ['missing', 'constructor', 'toString', '__proto__', null, true, [], {}]) {
    assert.equal(api.build(id), null);
    assert.equal(api.render({ props: { scenario: id } }), null);
    assert.equal(api.controls(id).length, 0);
  }
}
for (const item of [null, {}, { props: null }, { props: [] }, { props: {} },
  { props: { scenario: CONCEPTS[0], price: 10 } }, { props: { scenario: CONCEPTS[0], url: 'https://example.com/model.js' } }]) {
  assert.equal(concepts.render(item), null, 'Malformed concept props fail closed');
}

// Quantity is independently evaluated at every posted price and every demand
// shift. A price change stays on the same curves; a shift moves only demand.
for (let tempo = 30; tempo <= 120; tempo += 10) {
  for (const division of ['1', '2', '4']) {
    const d = concepts.build('arts.1.beat', { tempo, division }).data;
    assert.equal(d.beats.length, 4);
    assert.equal(d.notes.length, 4 * Number(division));
    near(d.duration, 240 / tempo);
    near(d.noteSeconds * Number(division), d.beatSeconds);
    d.notes.forEach((t, i) => near(t, i * 60 / (tempo * Number(division))));
    d.beats.forEach((t, i) => near(t, d.notes[i * Number(division)]));
    assert.ok(d.notes.at(-1) < d.duration);
  }
}

const economyId = 'hist.3.economics-intro';
for (let demandShift = -20; demandShift <= 20; demandShift += 4) {
  let previous;
  for (let price = 0; price <= 40; price += 1) {
    const model = verify(concepts, economyId, { price, demandShift });
    const data = model.data;
    near(data.demanded, 100 + demandShift - 2 * price);
    near(data.supplied, 20 + 2 * price);
    near(data.equilibrium.price, (80 + demandShift) / 4);
    near(data.equilibrium.quantity, 20 + 2 * data.equilibrium.price);
    near(data.equilibrium.quantity, 100 + demandShift - 2 * data.equilibrium.price);
    near(data.shortage, Math.max(0, data.demanded - data.supplied));
    near(data.surplus, Math.max(0, data.supplied - data.demanded));
    assert.equal(data.balance, data.shortage ? 'shortage' : data.surplus ? 'surplus' : 'equilibrium');
    if (previous) equal(data.curves, previous, 'Posted price does not shift the curves');
    previous = data.curves;
    for (const [name, sign, intercept] of [['supply', 1, 20], ['demand', -1, 100 + demandShift]]) {
      assert.ok(data.curves[name].length > 1);
      data.curves[name].forEach(point => near(point.quantity, intercept + sign * 2 * point.price));
    }
  }
}
const lowDemand = concepts.build(economyId, { demandShift: -20 }).data;
const highDemand = concepts.build(economyId, { demandShift: 20 }).data;
equal(lowDemand.curves.supply, highDemand.curves.supply, 'Demand shift leaves supply fixed');
assert.ok(highDemand.equilibrium.price > lowDemand.equilibrium.price);
assert.ok(highDemand.equilibrium.quantity > lowDemand.equilibrium.quantity);

// The two trees must preserve word order and change the direct parent of the
// same PP. Their explicit structure establishes attachment independently of prose.
const expectedTokens = ['I', 'saw', 'the', 'person', 'with', 'the', 'telescope'];
function leaves(tree) { return typeof tree === 'string' ? [tree] : tree.children.flatMap(leaves); }
function ppParents(tree, parent = null) {
  return (tree.label === 'PP' ? [parent.label] : []).concat((tree.children || []).flatMap(child => ppParents(child, tree)));
}
const parses = ['verb', 'noun'].map(attachment => {
  const data = verify(concepts, 'lang.4.linguistics', { attachment }).data;
  equal(data.tokens, expectedTokens);
  equal(leaves(data.tree), expectedTokens, 'Parse terminals preserve every token in order');
  equal(ppParents(data.tree), [attachment === 'verb' ? 'VP' : 'NP']);
  assert.equal(data.attachmentTarget, attachment === 'verb' ? 'VP' : 'NP');
  assert.ok(data.parse.trim() && data.interpretation.trim());
  return data;
});
assert.notEqual(parses[0].parse, parses[1].parse);
assert.notEqual(parses[0].interpretation, parses[1].interpretation);

// Enumerate every valuation and every outgoing relation, including the empty
// relation, a self-loop, and inaccessible worlds whose truth must not leak in.
for (let truthBits = 0; truthBits < 8; truthBits += 1) for (let edgeBits = 0; edgeBits < 8; edgeBits += 1) {
  const state = {};
  for (let i = 0; i < 3; i += 1) { state['p' + i] = Boolean(truthBits & (1 << i)); state['edge' + i] = Boolean(edgeBits & (1 << i)); }
  const data = verify(concepts, 'mind.5.logic-advanced', state).data;
  const successors = [0, 1, 2].filter(i => state['edge' + i]);
  const witnesses = successors.filter(i => state['p' + i]).map(i => 'w' + i);
  const counterexamples = successors.filter(i => !state['p' + i]).map(i => 'w' + i);
  assert.equal(data.currentWorld, 'w0');
  assert.equal(data.localP, state.p0);
  equal(data.successors, successors.map(i => 'w' + i));
  equal(data.edges, successors.map(i => ({ from: 'w0', to: 'w' + i })));
  equal(data.witnesses, witnesses);
  equal(data.counterexamples, counterexamples);
  assert.equal(data.boxP, counterexamples.length === 0);
  assert.equal(data.diamondP, witnesses.length > 0);
  equal(data.worlds.map(world => ({ id: world.id, truth: world.truth, current: world.current, accessible: world.accessible })),
    [0, 1, 2].map(i => ({ id: 'w' + i, truth: state['p' + i], current: i === 0, accessible: state['edge' + i] })));
}

// Check actual cube edges and eye rays, including all endpoints of the allowed
// depth/focal grids. This does not infer correctness from the formula's label.
const COLORS = { blue: '#3e7085', coral: '#b96652', gold: '#b98a2f' };
const primitives = (scene, kind, color) => scene.primitives.filter(p => p.kind === kind && p.color === color);
const subtract = (a, b) => a.map((value, index) => value - b[index]);
function perspectiveWidth(depth, focal) {
  const scene = spatial.build('arts.2.color-theory', { depth, focal });
  const points = primitives(scene, 'line', COLORS.coral).flatMap(edge => edge.points);
  return Math.max(...points.map(point => point[0])) - Math.min(...points.map(point => point[0]));
}
for (let depthStep = 0; depthStep <= 12; depthStep += 1) for (let focalStep = 0; focalStep <= 10; focalStep += 1) {
  const scene = verify(spatial, 'arts.2.color-theory', { depth: 3.2 + 0.2 * depthStep, focal: 1 + 0.1 * focalStep });
  const { depth, focal } = scene.state;
  const physical = primitives(scene, 'line', COLORS.blue).filter(edge => edge.width === 2.5);
  const projected = primitives(scene, 'line', COLORS.coral).filter(edge => edge.width === 3);
  const rays = primitives(scene, 'line', COLORS.gold).filter(ray => ray.width === 1.2);
  assert.equal(physical.length, 12);
  assert.equal(projected.length, 12);
  assert.equal(rays.length, 8);
  physical.forEach((edge, index) => {
    near(Math.hypot(...subtract(edge.points[1], edge.points[0])), 1.2);
    edge.points.forEach((point, end) => {
      const imagePoint = projected[index].points[end];
      assert.ok(point[2] > focal && focal > 0);
      near(imagePoint[0], focal * point[0] / point[2]);
      near(imagePoint[1], focal * point[1] / point[2]);
      near(imagePoint[2], focal);
    });
  });
  rays.forEach(ray => {
    assert.equal(ray.points.length, 3);
    const [eye, imagePoint, point] = ray.points;
    equal(eye, [0, 0, 0]);
    imagePoint.forEach((value, axis) => near(value, focal / point[2] * point[axis]));
  });
  const vertices = physical.flatMap(edge => edge.points);
  near(Math.min(...vertices.map(point => point[2])), depth - 0.6);
  near(Math.max(...vertices.map(point => point[2])), depth + 0.6);
  for (const axis of [0, 1, 2]) near(Math.max(...vertices.map(point => point[axis])) - Math.min(...vertices.map(point => point[axis])), 1.2);
  // A physical edge in the depth direction projects onto a line through the
  // vanishing point (0, 0, f), even though neither endpoint is at that point.
  physical.forEach((edge, index) => {
    if (Math.abs(edge.points[0][2] - edge.points[1][2]) < 1e-8) return;
    const [a, b] = projected[index].points;
    near(a[0] * b[1] - a[1] * b[0], 0);
  });
}
assert.ok(perspectiveWidth(3.2, 1.6) > perspectiveWidth(5.6, 1.6), 'Depth shrinks the image');
near(perspectiveWidth(3.6, 2), 2 * perspectiveWidth(3.6, 1), 1e-8);

function blochValues(scene) {
  const markers = primitives(scene, 'sphere', COLORS.coral);
  assert.equal(markers.length, 1);
  const [x, z, minusY] = markers[0].points[0];
  const match = scene.readout.match(/P\(0\).*?= ([\d.]+)%; P\(1\) = ([\d.]+)%.*?P\(\+\).*?= ([\d.]+)%; P\(−\) = ([\d.]+)%/);
  assert.ok(match, 'Both complementary measurement probabilities must be explicit');
  const probabilities = match.slice(1).map(value => Number(value) / 100);
  return { vector: [x, -minusY, z], probabilities };
}
for (let polar = 0; polar <= 180; polar += 15) for (let phase = 0; phase <= 360; phase += 15) {
  const scene = verify(spatial, 'cs.5.quantum', { polar, phase });
  const { vector, probabilities: [p0, p1, pPlus, pMinus] } = blochValues(scene);
  const theta = polar * Math.PI / 180, phi = phase * Math.PI / 180;
  const expected = [Math.sin(theta) * Math.cos(phi), Math.sin(theta) * Math.sin(phi), Math.cos(theta)];
  vector.forEach((value, axis) => near(value, expected[axis]));
  near(Math.hypot(...vector), 1);
  near(p0, (1 + vector[2]) / 2, 0.000501);
  near(pPlus, (1 + vector[0]) / 2, 0.000501);
  near(p0 + p1, 1);
  near(pPlus + pMinus, 1);
  [p0, p1, pPlus, pMinus].forEach(probability => assert.ok(probability >= 0 && probability <= 1));
  const stateShaft = primitives(scene, 'line', COLORS.coral).filter(line => line.width === 4);
  equal(stateShaft[0].points[0], [0, 0, 0]);
  stateShaft.at(-1).points.at(-1).forEach((value, axis) => near(value, [vector[0], vector[2], -vector[1]][axis]));
}
for (const polar of [0, 180]) {
  const initial = spatial.build('cs.5.quantum', { polar, phase: 0 });
  for (const phase of [45, 90, 180, 270, 360]) {
    const changed = spatial.build('cs.5.quantum', { polar, phase });
    equal(changed.primitives, initial.primitives, 'Phase is physically irrelevant at either pole');
    equal(blochValues(changed).probabilities, blochValues(initial).probabilities);
  }
}
for (const polar of [30, 60, 90, 150]) for (const phase of [30, 60, 90, 120, 150]) {
  const forward = blochValues(spatial.build('cs.5.quantum', { polar, phase }));
  const reflected = blochValues(spatial.build('cs.5.quantum', { polar, phase: 360 - phase }));
  equal(forward.probabilities, reflected.probabilities, 'Z and X probabilities cannot resolve the sign of Y');
  near(forward.vector[0], reflected.vector[0]);
  near(forward.vector[1], -reflected.vector[1]);
  near(forward.vector[2], reflected.vector[2]);
  assert.ok(Math.abs(forward.vector[1] - reflected.vector[1]) > 0.1);
}

function descendants(root, predicate) {
  if (!root || root.nodeType !== 1) return [];
  return (predicate(root) ? [root] : []).concat(root.children.flatMap(child => descendants(child, predicate)));
}
function one(root, predicate, description) {
  const matches = descendants(root, predicate);
  assert.equal(matches.length, 1, description + ': exactly one element');
  return matches[0];
}
const classElement = (root, name) => one(root, el => el.classList.contains(name), name);
function serialize(element) {
  if (element.nodeType === 3) return element.textContent;
  return { tag: element.tagName, attributes: [...element.attributes.entries()].sort(),
    children: element.children.map(serialize) };
}
function controlState(root) {
  return descendants(root, el => el.getAttribute('data-parameter') !== null)
    .map(el => ({ key: el.getAttribute('data-parameter'), value: String(el.value), pressed: el.getAttribute('aria-pressed') }));
}
function assertAccessibleReferences(root) {
  const elements = descendants(root, () => true);
  const ids = elements.map(el => el.getAttribute('id')).filter(Boolean);
  assert.equal(new Set(ids).size, ids.length, 'Rendered model IDs are unique');
  for (const el of elements) for (const attr of ['aria-labelledby', 'aria-describedby', 'for']) {
    for (const id of (el.getAttribute(attr) || '').split(/\s+/).filter(Boolean)) {
      assert.ok(ids.includes(id), attr + ' points at an existing element: ' + id);
    }
  }
  for (const el of elements) for (const [name, value] of el.attributes) {
    if (['points', 'd', 'cx', 'cy', 'r', 'x', 'y', 'x1', 'x2', 'y1', 'y2', 'width', 'height'].includes(name)) {
      assert.doesNotMatch(value, /\b(?:NaN|Infinity)\b/, 'Finite rendered SVG attribute');
    }
  }
}
for (const { node, item } of crossEntries) {
  const api = item.renderer === 'concept-lab' ? concepts : spatial;
  let speak;
  const root = registry.render(item, { speakButton: callback => {
    speak = callback;
    return document.createElement('button');
  } });
  assert.ok(root, node.id + ': renderer is reachable through the shipped registry');
  assert.equal(root.getAttribute('data-renderer'), item.renderer);
  assert.equal(root.getAttribute('data-scenario'), node.id);
  const canvas = classElement(root, 'model-canvas');
  const readout = classElement(root, 'model-readout');
  const status = classElement(root, 'model-status');
  const reset = one(root, el => el.tagName === 'button' && el.textContent === 'Reset model', 'reset button');
  const initial = api.build(node.id);
  const initialCanvas = serialize(canvas);
  const initialControls = controlState(root);
  assert.equal(readout.textContent, initial.readout);
  assert.equal(status.textContent, '', 'Status starts silent');
  if (node.id === 'cs.3.web') {
    const preview = one(root, el => el.getAttribute('data-action') === 'web-preview', 'Working HTML preview');
    const counter = one(root, el => el.getAttribute('data-web-counter') === 'true', 'Live counter');
    const enabled = one(root, el => el.getAttribute('data-parameter') === 'enabled', 'Counter handler switch');
    preview.dispatch('click'); assert.equal(counter.textContent, 'Preview counter: 1');
    enabled.dispatch('click'); preview.dispatch('click'); assert.equal(counter.textContent, 'Preview counter: 1');
    enabled.dispatch('click');
    for (let i = 0; i < 9; i++) preview.dispatch('click');
    assert.equal(counter.textContent, 'Preview counter: 0');
    reset.dispatch('click');
  }
  assert.equal(status.getAttribute('aria-live'), 'polite');
  assert.equal(typeof speak, 'function');
  assert.ok(speak().includes(initial.readout));
  assertAccessibleReferences(root);
  if (node.id === 'cs.2.programming') {
    const code = ['total = 0', 'for value in [2, 5, 8]:', 'if value > 4:', 'total += value'];
    const xs = code.map(text => Number(one(canvas, el => el.tagName === 'text' && el.textContent === text, 'Indented code statement').getAttribute('x')));
    equal(xs, [32, 32, 60, 88], 'Python nesting uses explicit coordinates, not collapsed leading whitespace');
  }
  if (node.id === 'math.2.data') {
    // Mean/median lines can span y=70..230. Values must stay above that band.
    equal(descendants(canvas, el => el.tagName === 'text' && el.getAttribute('y') === '55')
      .map(el => el.textContent), initial.data.values.map(String), 'Chart values stay above summary lines');
  }
  assert.equal(descendants(canvas, el => el.tagName === 'svg').length, 1);
  assert.ok(descendants(canvas, el => ['line', 'polyline', 'polygon', 'circle', 'ellipse', 'path', 'rect'].includes(el.tagName)).length >= 3,
    node.id + ': explanatory SVG geometry');
  for (const control of api.controls(node.id)) {
    const input = one(root, el => el.getAttribute('data-parameter') === control.key, node.id + ': ' + control.key);
    const value = controlValues(control).find(option => option !== initial.state[control.key]);
    if (control.type === 'toggle') input.dispatch('click');
    else { input.value = String(value); input.dispatch(control.options ? 'change' : 'input'); }
    const expected = api.build(node.id, { [control.key]: value });
    if (node.id === 'math.3.euclid') {
      const { a, b } = expected.state, unit = 230 / (a + b);
      const triangles = descendants(canvas, el => el.tagName === 'polygon');
      equal(triangles.length, 4);
      for (const triangle of triangles) {
        const points = triangle.getAttribute('points').split(' ').map(pair => pair.split(',').map(Number));
        const area = Math.abs(points.reduce((sum, p, i) => {
          const next = points[(i + 1) % 3]; return sum + p[0] * next[1] - next[0] * p[1];
        }, 0)) / 2;
        near(area, a * b * unit * unit / 2);
        const lengths = points.map((p, i) => { const next = points[(i + 1) % 3]; return Math.hypot(p[0] - next[0], p[1] - next[1]) / unit; }).sort((a, b) => a - b);
        const sides = [a, b, Math.hypot(a, b)].sort((a, b) => a - b);
        lengths.forEach((length, i) => near(length, sides[i]));
      }
    }
    assert.equal(readout.textContent, expected.readout, node.id + ': control updates the visible explanation');
    assert.equal(status.textContent, expected.readout, node.id + ': interaction announces the current result');
    assert.ok(speak().includes(expected.readout), node.id + ': narration follows state');
    assert.notDeepEqual(serialize(canvas), initialCanvas, node.id + ': control updates SVG');
    if (control.type === 'toggle') assert.equal(input.getAttribute('aria-pressed'), String(value));
    else assert.equal(String(input.value), String(expected.state[control.key]));
    if (node.id === 'lang.4.linguistics') {
      assert.equal(classElement(root, 'concept-parse').textContent, expected.data.parse);
      assert.ok(speak().includes(expected.data.parse), 'Narration includes the full parse');
    }
    assertAccessibleReferences(root);
    reset.dispatch('click');
    assert.equal(readout.textContent, initial.readout, node.id + ': reset restores explanation');
    equal(serialize(canvas), initialCanvas, node.id + ': reset restores geometry');
    equal(controlState(root), initialControls, node.id + ': reset restores controls');
    interactionChecks += 1;
  }
  console.log('COVER ' + node.id);
}
for (const renderer of ['missing', 'constructor', 'toString', '__proto__']) assert.equal(registry.render({ renderer }), null);

for (let value = 0; value < 16; value++) {
  const state = Object.fromEntries([8, 4, 2, 1].map(weight => ['bit' + weight, Boolean(value & weight)]));
  const data = verify(concepts, 'cs.1.binary', state).data;
  assert.equal(data.decimal, value);
  assert.equal(data.binary, value.toString(2).padStart(4, '0'));
  assert.equal(data.places.reduce((sum, place) => sum + place.contribution, 0), value);
}
for (let top = 0; top <= 10; top++) for (let bottom = 0; bottom <= 10; bottom++) {
  const data = verify(concepts, 'math.0.compare', { top, bottom }).data;
  assert.equal(data.matched, Math.min(top, bottom));
  assert.equal(data.difference, Math.abs(top - bottom));
  assert.equal(data.relation, top === bottom ? '=' : top > bottom ? '>' : '<');
}
for (let number = 0; number <= 20; number++) {
  const data = verify(concepts, 'math.0.numbers20', { number }).data;
  assert.equal(data.tens * 10 + data.ones, number);
  assert.equal(data.first + data.second, number);
  assert.ok(data.first <= 10 && data.second <= 10 && data.ones < 10);
}
for (const rule of ['ab', 'abb', 'grow']) for (let steps = 1; steps <= 6; steps++) {
  const data = verify(concepts, 'math.0.patterns', { rule, steps }).data;
  const unit = rule === 'ab' ? ['circle', 'square'] : ['circle', 'square', 'square'];
  equal(data.terms, Array.from({length: steps}, (_, i) => rule === 'grow' ? i + 1 : unit[i % unit.length]));
  assert.equal(data.next, rule === 'grow' ? steps + 1 : unit[steps % unit.length]);
}
for (let stay = 0; stay <= 10; stay++) for (let removed = 0; removed <= 10; removed++) {
  const data = verify(concepts, 'math.1.subtraction', { stay, removed }).data;
  assert.equal(data.start - removed, stay);
  assert.equal(data.result, stay);
}
for (let number = 0; number < 1000; number++) {
  const state = { hundreds: Math.floor(number / 100), tens: Math.floor(number / 10) % 10, ones: number % 10 };
  const data = verify(concepts, 'math.1.place-value', state).data;
  assert.equal(data.number, number);
  equal(data.parts, [state.hundreds * 100, state.tens * 10, state.ones]);
}
for (let rows = 0; rows <= 12; rows++) for (let columns = 0; columns <= 12; columns++) {
  const data = verify(concepts, 'math.1.multiplication', { rows, columns }).data;
  assert.equal(data.product, rows * columns);
  assert.equal(data.product, concepts.build('math.1.multiplication', { rows: columns, columns: rows }).data.product);
}
for (let total = 0; total <= 36; total++) for (let groups = 1; groups <= 6; groups++) {
  const data = verify(concepts, 'math.1.division', { total, groups }).data;
  assert.equal(data.quotient * groups + data.remainder, total);
  assert.ok(Number.isInteger(data.quotient) && data.quotient >= 0);
  assert.ok(data.remainder >= 0 && data.remainder < groups);
}
for (let start = 0; start <= 4; start++) for (let length = 1; length <= 8; length++) {
  const data = verify(concepts, 'math.1.measurement', { start, length }).data;
  assert.equal(data.end - start, length);
  assert.equal(data.millimetres, length * 10);
  assert.ok(data.end <= 12);
}
for (let hour = 0; hour < 24; hour++) for (let minute = 0; minute < 60; minute += 5) {
  const data = verify(concepts, 'math.1.time', { hour, minute }).data;
  assert.equal(data.hourAngle, (hour % 12) * 30 + minute * .5);
  assert.equal(data.minuteAngle, minute * 6);
  assert.equal(data.digital, String(hour).padStart(2, '0') + ':' + String(minute).padStart(2, '0'));
}
for (let day = 1; day <= 30; day++) {
  const data = verify(concepts, 'math.1.time', { day }).data;
  assert.equal(data.weekdayIndex, new Date(Date.UTC(2026, 8, day)).getUTCDay());
}
for (let quarters = 0; quarters <= 4; quarters++) {
  const data = verify(concepts, 'math.1.fractions-intro', { quarters }).data;
  assert.equal(data.value, quarters / 4);
  assert.equal(data.wholeHalves, quarters % 2 === 0);
}
for (let percent = 0; percent <= 100; percent++) for (let whole = 0; whole <= 200; whole += 10) {
  const data = verify(concepts, 'math.2.percent', { percent, whole }).data;
  near(data.amount, whole * percent / 100);
  near(data.numerator / data.denominator, percent / 100);
  assert.ok(Number.isInteger(data.numerator) && Number.isInteger(data.denominator) && data.denominator > 0);
}
for (let x = -5; x <= 5; x++) for (let y = -5; y <= 5; y++) {
  const data = verify(concepts, 'math.2.coordinates', { x, y }).data;
  const expected = !x && !y ? 'at the origin' : !x ? 'on the y-axis' : !y ? 'on the x-axis' :
    'in quadrant ' + ({'1,1':'I','-1,1':'II','-1,-1':'III','1,-1':'IV'}[[Math.sign(x), Math.sign(y)].join(',')]);
  assert.equal(data.location, expected);
}
for (let a = 0; a <= 99; a++) for (let b = 0; b <= 99; b++) {
  const data = verify(concepts, 'math.2.decimals', { a, b }).data;
  assert.equal(data.total, a + b);
  near(Number(data.sum), (a + b) / 100);
  assert.equal(data.carryTenths, (a % 10 + b % 10) >= 10 ? 1 : 0);
  assert.equal(data.carryWhole, a + b >= 100 ? 1 : 0);
}
for (let a = 0; a <= 9; a++) for (let b = 0; b <= 9; b++) for (let c = 1; c <= 9; c++) for (const grouped of [false, true]) {
  const data = verify(concepts, 'math.2.order-ops', { a, b, c, grouped }).data;
  assert.equal(data.inner, grouped ? a + b : b * c);
  assert.equal(data.result, grouped ? (a + b) * c : a + b * c);
}
const primesTo60 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59];
for (let number = 1; number <= 60; number++) for (let divisor = 1; divisor <= 60; divisor++) {
  const data = verify(concepts, 'math.2.primes', { number, divisor }).data;
  assert.equal(data.classification, number === 1 ? 'neither prime nor composite' : primesTo60.includes(number) ? 'prime' : 'composite');
  equal(data.factors, Array.from({length: number}, (_, i) => i + 1).filter(i => number % i === 0));
  assert.equal(data.quotient * divisor + data.remainder, number);
  assert.ok(data.remainder >= 0 && data.remainder < divisor);
}
for (let a = 1; a <= 5; a++) for (let b = 1; b <= 5; b++) for (let scale = 1; scale <= 6; scale++) {
  const data = verify(concepts, 'math.2.ratio', { a, b, scale }).data;
  assert.equal(data.a, a * scale); assert.equal(data.b, b * scale);
  assert.equal(data.a * b, data.b * a); near(data.fractionA, data.a / data.total);
}
for (let base = 1; base <= 6; base++) for (let exponent = 0; exponent <= 5; exponent++) {
  const data = verify(concepts, 'math.2.exponents', { base, exponent }).data;
  let product = 1; const powers = [product];
  for (let i = 0; i < exponent; i++) { product *= base; powers.push(product); }
  equal(data.powers, powers); assert.equal(data.result, product);
}
const dataCases = [[3, 4, 5, 6, 18], [18, 6, 5, 4, 3], [0, 0, 0, 0, 20], [20, 20, 0, 0, 0]];
for (let value = 0; value <= 20; value++) {
  dataCases.push(Array(5).fill(value));
  for (let index = 0; index < 5; index++) { const values = [3, 4, 5, 6, 18]; values[index] = value; dataCases.push(values); }
}
for (const values of dataCases) {
  const state = Object.fromEntries('abcde'.split('').map((key, i) => [key, values[i]]));
  const data = verify(concepts, 'math.2.data', state).data;
  const sorted = [...values].sort((a, b) => a - b);
  equal(data.sorted, sorted); assert.equal(data.median, sorted[2]);
  near(data.mean * 5, values.reduce((sum, value) => sum + value, 0));
}
for (let x = -5; x <= 5; x++) for (let a = -3; a <= 3; a++) for (let b = -5; b <= 5; b++) {
  const data = verify(concepts, 'math.2.prealgebra', { x, a, b }).data;
  assert.equal(data.product, a * x); assert.equal(data.result, a * x + b);
}
for (let a = 1; a <= 6; a++) for (let b = -6; b <= 6; b++) for (let c = -12; c <= 12; c++) {
  for (let step = 0; step <= 2; step++) {
    const d = verify(concepts, 'math.3.linear', { a, b, c, step }).data;
    near(a * d.solution + b, c);
    equal(d.difference, c - b);
  }
}
for (let rise = -4; rise <= 4; rise++) for (let run = 1; run <= 4; run++) for (let intercept = -3; intercept <= 3; intercept++) {
  const d = verify(concepts, 'math.3.slope', { rise, run, intercept }).data;
  near((d.y2 - d.y1) / (d.x2 - d.x1), rise / run);
  near(d.y1, intercept);
  near(d.slope * d.x2 + intercept, d.y2);
}
for (let m1 = -2; m1 <= 2; m1++) for (let m2 = -2; m2 <= 2; m2++) for (let b1 = -3; b1 <= 3; b1++) for (let b2 = -3; b2 <= 3; b2++) {
  const d = verify(concepts, 'math.3.systems', { m1, m2, b1, b2 }).data;
  if (m1 === m2) { equal(d.kind, b1 === b2 ? 'infinite' : 'none'); equal(d.x, null); equal(d.y, null); }
  else { equal(d.kind, 'one'); near(m1 * d.x + b1, d.y); near(m2 * d.x + b2, d.y); }
}
for (let h = -2; h <= 2; h++) for (let k = -4; k <= 4; k++) for (let a = 1; a <= 3; a++) for (const down of [false, true]) {
  const d = verify(concepts, 'math.3.quadratics', { h, k, a, down }).data;
  const coefficient = down ? -a : a;
  equal(d.roots.length, k === 0 ? 1 : k * coefficient < 0 ? 2 : 0);
  near(d.a * h * h + d.b * h + d.c, k);
  d.roots.forEach(x => near(coefficient * (x - h) ** 2 + k, 0));
  if (d.roots.length === 2) near(d.roots[0] + d.roots[1], 2 * h);
}
for (let angle = 0; angle <= 360; angle += 15) {
  const d = verify(concepts, 'math.3.trig', { angle }).data;
  near(d.sine ** 2 + d.cosine ** 2, 1);
  if (angle === 90 || angle === 270) equal(d.tangent, null);
  else near(d.tangent * d.cosine, d.sine);
  if (angle % 90 === 0) {
    equal(d.cosine, [1, 0, -1, 0, 1][angle / 90]);
    equal(d.sine, [0, 1, 0, -1, 0][angle / 90]);
  }
}
for (let base = 2; base <= 5; base++) for (let exponent = -3; exponent <= 3; exponent++) {
  const d = verify(concepts, 'math.3.expo-logs', { base, exponent }).data;
  let expected = 1; for (let i = 0; i < Math.abs(exponent); i++) expected *= base;
  near(d.value, exponent < 0 ? 1 / expected : expected); near(d.recovered, exponent);
}
for (const mode of ['arithmetic', 'geometric']) for (let first = 1; first <= 4; first++) for (let step = 1; step <= 4; step++) for (let count = 1; count <= 6; count++) {
  const d = verify(concepts, 'math.3.sequences', { mode, first, step, count }).data;
  const values = [first]; for (let i = 1; i < count; i++) values.push(mode === 'arithmetic' ? values[i - 1] + step : values[i - 1] * step);
  equal(d.values, values); equal(d.sum, values.reduce((a, b) => a + b, 0));
  if (mode === 'arithmetic') near(d.sum, count * (values[0] + values[count - 1]) / 2);
  else near(d.sum, step === 1 ? count * first : first * (step ** count - 1) / (step - 1));
}
for (let target = 2; target <= 12; target++) for (const cumulative of [false, true]) {
  const d = verify(concepts, 'math.3.probability', { target, cumulative }).data;
  const frequencies = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1];
  equal(d.count, cumulative ? frequencies.slice(0, target - 1).reduce((a, b) => a + b, 0) : frequencies[target - 2]);
  near(d.probability, d.count / 36); equal(d.outcomes.length, 36);
}
for (let centre = 0; centre <= 10; centre++) for (let spread = 0; spread <= 4; spread++) for (let outlier = 0; outlier <= 12; outlier++) for (const sample of [false, true]) {
  const d = verify(concepts, 'math.3.statistics', { centre, spread, outlier, sample }).data;
  near(d.mean, centre + outlier / 5);
  near(d.deviations.reduce((a, b) => a + b, 0), 0);
  const expectedSS = 10 * spread * spread + 4 * spread * outlier + .8 * outlier * outlier;
  near(d.squaredSum, expectedSS); near(d.sd ** 2, expectedSS / (sample ? 4 : 5));
}
for (const mode of ['hole', 'jump']) for (let a = 1; a <= 3; a++) for (let closeness = 0; closeness <= 3; closeness++) for (let point = 0; point <= 6; point++) {
  const d = verify(concepts, 'math.3.precalc', { mode, a, closeness, point }).data;
  if (mode === 'hole') {
    near(d.left, (d.leftX ** 2 - a * a) / (d.leftX - a));
    near(d.right, (d.rightX ** 2 - a * a) / (d.rightX - a)); equal(d.limit, 2 * a);
  } else { equal(d.limit, null); equal(d.leftLimit, a); equal(d.rightLimit, a + 2); }
}
for (let r1 = -2; r1 <= 2; r1++) for (let r2 = -2; r2 <= 2; r2++) for (let r3 = -2; r3 <= 2; r3++) for (const negative of [false, true]) {
  const d = verify(concepts, 'math.3.polynomials', { r1, r2, r3, negative }).data;
  for (let x = -3; x <= 3; x += .5) near(d.a * x ** 3 + d.b * x ** 2 + d.c * x + d.constant, (negative ? -1 : 1) * (x - r1) * (x - r2) * (x - r3));
  equal(d.distinct.reduce((sum, r) => sum + r.multiplicity, 0), 3);
}
for (let a = 1; a <= 5; a++) for (let b = 1; b <= 5; b++) for (const rearranged of [false, true]) {
  const d = verify(concepts, 'math.3.euclid', { a, b, rearranged }).data;
  near(d.total - d.triangles, d.remaining); near(d.hypotenuse ** 2, d.remaining);
}
for (let real = -3; real <= 3; real++) for (let imaginary = -3; imaginary <= 3; imaginary++) for (let turns = 0; turns <= 4; turns++) for (let scale = 1; scale <= 2; scale++) {
  const d = verify(concepts, 'math.4.complex', { real, imaginary, turns, scale }).data;
  const angle = turns * Math.PI / 2;
  near(d.real, scale * (real * Math.cos(angle) - imaginary * Math.sin(angle)));
  near(d.imaginary, scale * (real * Math.sin(angle) + imaginary * Math.cos(angle)));
  near(d.resultModulus, scale * d.modulus);
}
for (const mode of ['square', 'absolute']) for (let x = -2; x <= 2; x += .5) for (let closeness = 0; closeness <= 3; closeness++) for (const left of [false, true]) {
  const d = verify(concepts, 'math.4.diff-calc', { mode, x, closeness, left }).data;
  near(d.secant, (d.otherY - d.y) / d.h);
  if (mode === 'absolute' && x === 0) { equal(d.derivative, null); near(d.secant, left ? -1 : 1); }
  else near(d.derivative, mode === 'square' ? 2 * x : Math.sign(x));
}
for (let shift = 0; shift <= 3; shift++) for (let end = 1; end <= 6; end++) for (let count = 2; count <= 20; count += 2) for (const method of ['left', 'midpoint', 'right']) {
  const d = verify(concepts, 'math.4.int-calc', { shift, end, count, method }).data;
  near(d.exact, end * ((-shift) + (end - shift)) / 2);
  near(d.error, method === 'midpoint' ? 0 : (method === 'left' ? -1 : 1) * end * end / (2 * count));
  near(d.rectangles.reduce((sum, r) => sum + r.width, 0), end); near(d.endpointSlope, end - shift);
}
for (let rate = .5; rate <= 2; rate += .5) for (let initial = 1; initial <= 4; initial++) for (let steps = 2; steps <= 16; steps += 2) {
  const d = verify(concepts, 'math.4.diffeq', { rate, initial, steps }).data;
  equal(d.values.length, steps + 1); near(d.values[0], initial);
  for (let i = 1; i <= steps; i++) near(d.values[i], d.values[i - 1] - rate * d.values[i - 1] * d.h);
  near(d.exact, initial / Math.exp(rate * 2)); near(d.error, Math.abs(d.values[steps] - d.exact));
}
for (let mask = 0; mask < 64; mask++) {
  const pairs = ['01', '02', '03', '12', '13', '23'], state = Object.fromEntries(pairs.map((p, i) => ['e' + p, Boolean(mask & (1 << i))]));
  const d = verify(concepts, 'math.4.discrete', state).data;
  const search = (v, remaining) => !remaining.length || remaining.some(([a, b], i) => (a === v || b === v) && search(a === v ? b : a, remaining.filter((_, j) => i !== j)));
  equal(d.possible, [0, 1, 2, 3].some(v => search(v, d.edges)));
  equal(d.degrees.reduce((a, b) => a + b, 0), d.edges.length * 2);
  if (d.possible && d.edges.length) {
    equal(d.walk.length, d.edges.length + 1);
    const used = d.walk.slice(1).map((v, i) => [d.walk[i], v].sort().join('')).sort();
    equal(used, d.edges.map(e => [...e].sort().join('')).sort());
  }
}
for (let a = 1; a <= 40; a++) for (let b = 1; b <= 40; b++) {
  const d = verify(concepts, 'math.4.numtheory', { a, b }).data;
  let greatest = 1; for (let k = 1; k <= Math.min(a, b); k++) if (a % k === 0 && b % k === 0) greatest = k;
  equal(d.gcd, greatest); equal(a * d.x + b * d.y, greatest);
  d.divisions.forEach(row => { equal(row.dividend, row.q * row.divisor + row.remainder); assert.ok(row.remainder >= 0 && row.remainder < row.divisor); });
}
for (let a = 0; a <= 3; a++) for (let ei = 1; ei <= 8; ei++) for (let di = 1; di <= 20; di++) {
  const epsilon = ei / 4, delta = di / 20, d = verify(concepts, 'math.4.analysis', { a, epsilon, delta }).data;
  equal(d.works, 40 * a * di + di * di <= 100 * ei);
  if (!d.works) { const h = (delta + Math.sqrt(a * a + epsilon) - a) / 2; assert.ok(h < delta && (a + h) ** 2 - a * a > epsilon); }
  assert.ok(2 * a * d.safeDelta + d.safeDelta ** 2 <= epsilon + 1e-12);
}
for (let n = 1; n <= 10; n++) for (let percent = 0; percent <= 100; percent += 10) for (let cutoff = 0; cutoff <= 10; cutoff++) {
  const d = verify(concepts, 'math.4.prob-theory', { n, percent, cutoff }).data;
  near(d.probabilities.reduce((a, b) => a + b, 0), 1);
  near(d.probabilities.reduce((sum, p, k) => sum + p * k, 0), d.mean);
  near(d.probabilities.reduce((sum, p, k) => sum + p * (k - d.mean) ** 2, 0), d.variance);
  near(d.cumulative, d.probabilities.filter((_, k) => k <= cutoff).reduce((a, b) => a + b, 0));
}
for (let n = 2; n <= 12; n++) for (let g = 0; g <= 11; g++) for (let steps = 0; steps <= 12; steps++) {
  const d = verify(concepts, 'math.5.abstract', { n, g, steps }).data;
  let gcd = 1; for (let k = 1; k <= n; k++) if (n % k === 0 && g % k === 0) gcd = k;
  equal(d.order, n / gcd); equal(d.current, steps * g % n);
  equal(new Set(d.orbit).size, d.order);
  for (const a of d.orbit) for (const b of d.orbit) assert.ok(d.orbit.includes((a + b) % n));
}
for (let stage = 0; stage <= 5; stage++) for (const varying of [false, true]) {
  const d = verify(concepts, 'math.5.measure', { stage, varying }).data;
  near(d.length, varying ? .5 + 2 ** (-stage - 1) : (2 / 3) ** stage);
  equal(d.layers[stage].length, 2 ** stage);
  d.layers.forEach((layer, k) => layer.forEach(([a, b], i) => { assert.ok(a >= 0 && b <= 1 && b > a); if (i) assert.ok(a > layer[i - 1][1]); if (k) assert.ok(d.layers[k - 1].some(([x, y]) => a >= x - 1e-12 && b <= y + 1e-12)); }));
}
for (let terms = 1; terms <= 12; terms++) for (let perturb = -1; perturb <= 1; perturb += .25) {
  const d = verify(concepts, 'math.5.functional', { terms, perturb }).data;
  near(d.errorSquared - d.optimalErrorSquared, perturb ** 2);
  // Independent midpoint quadrature checks the analytic L² residual formula.
  let integral = 0; const count = 4096;
  for (let j = 0; j < count; j++) { const x = -Math.PI + (j + .5) * 2 * Math.PI / count;
    const approximation = d.coefficients.reduce((sum, c, i) => sum + c * Math.sin((i + 1) * x), 0) + perturb * Math.sin(x);
    integral += (x - approximation) ** 2 * 2 / count;
  }
  near(integral, d.errorSquared, 3e-5);
}
for (let start = -2; start <= 2; start += .25) for (let iterations = 0; iterations <= 10; iterations++) {
  const result = verify(concepts, 'math.5.numerical', { start, iterations }), d = result.data, f = x => x ** 3 - 2 * x + 2;
  assert.ok(result.readout.includes('error ≤ 1/' + 2 ** (iterations + 1)), 'Certified bounds must not be rounded downward');
  assert.ok(f(d.bracket[0]) <= 0 && f(d.bracket[1]) >= 0);
  near(d.errorBound, 2 ** (-iterations - 1));
  d.newton.slice(1).forEach((x, i) => near(x, d.newton[i] - f(d.newton[i]) / (3 * d.newton[i] ** 2 - 2), 1e-6));
  if (start === 0) equal(d.last, iterations % 2);
}
console.log(`Verified ${CONCEPTS.length + CROSS_SPATIAL.length} cross-subject models, ${controlChecks} meaningful controls, ${buildChecks} finite deterministic builds, ` +
  `${interactionChecks} rendered control changes and resets, exact geometry, and semantic invariants.`);
