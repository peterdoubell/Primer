'use strict';

const KNOWLEDGE_DOMAINS = [
  { id: 'formal', title: 'Formal sciences', mark: '∴', color: '#526fa0',
    description: 'Number, logic, computation and the structures they share.', subjects: ['math', 'cs'] },
  { id: 'natural', title: 'Natural sciences', mark: '✳', color: '#427562',
    description: 'Matter, motion, living systems, Earth and the wider universe.',
    subjects: ['physics', 'chemistry', 'biology', 'earth'] },
  { id: 'applied', title: 'Applied sciences', mark: '⚙', color: '#9b6945',
    description: 'Building, designing, cultivating and caring for living systems.',
    subjects: ['engineering', 'design', 'environment', 'health', 'radiology'] },
  { id: 'society', title: 'Society & institutions', mark: '⚖', color: '#9a5f61',
    description: 'How people learn, govern, trade and organise themselves.',
    subjects: ['history', 'mind', 'business', 'civics', 'education'] },
  { id: 'culture', title: 'Language, arts & media', mark: '✦', color: '#8b6191',
    description: 'How people create, communicate and interpret meaning.', subjects: ['language', 'arts', 'media'] },
];
const DOS_POSTERS = 'https://store.dftba.com/products/';
const DOS_MAPS = [
  ['math', 'Map of Mathematics', DOS_POSTERS + 'map-of-mathematics-poster'],
  ['physics', 'Map of Physics', DOS_POSTERS + 'map-of-physics-poster'],
  ['chemistry', 'Map of Chemistry', DOS_POSTERS + 'map-of-chemistry-poster'],
  ['biology', 'Map of Biology', DOS_POSTERS + 'map-of-biology-poster'],
  ['earth', 'Map of the Night Sky', DOS_POSTERS + 'domain-of-science-map-of-the-night-sky-poster'],
  ['cs', 'Map of Computer Science (Patreon)', 'https://www.patreon.com/ScienceMaps/posts/map-of-computer-14252506'],
  ['engineering', 'Map of Engineering', DOS_POSTERS + 'the-map-of-engineering-poster'],
  ['health', 'Map of Medicine', DOS_POSTERS + 'map-of-medicine'],
];

let knowledgeMapStage = null;
const mapHref = (...parts) => hashFor('maps', [...(parts.length ? parts : ['world', 'all']), knowledgeMapStage ?? 0]);

function mapEmblem(mark, variant) {
  return el('span', { class: 'km-emblem km-emblem-' + variant, 'aria-hidden': 'true' },
    el('span', { html: '<svg viewBox="0 0 80 80" fill="none" stroke="currentColor">'
      + '<circle cx="40" cy="40" r="36" stroke-dasharray="1 4"/><circle cx="40" cy="40" r="30"/>'
      + '<path d="M40 3v11m0 52v11M3 40h11m52 0h11M15 15l7 7m36 36 7 7m0-50-7 7M22 58l-7 7"/>'
      + '<path d="M40 17 63 40 40 63 17 40Z" opacity=".45"/></svg>' }),
    el('span', { class: 'km-emblem-mark' }, mark));
}

function mapTile({ title, href, note, mark, variant = 'point', image, detail, color }) {
  const link = el('a', { class: 'km-tile km-tile-' + variant, href,
    style: color ? '--map-accent:' + color : null },
    image || mapEmblem(mark, variant),
    el('span', { class: 'km-tile-copy' }, note ? el('span', { class: 'km-label' }, note) : null,
      el('strong', {}, title), detail ? el('span', { class: 'km-detail' }, detail) : null),
    el('span', { class: 'km-arrow', 'aria-hidden': 'true' }, '↗'));
  return link;
}

function mapTerritory(title, note, tiles, color) {
  return el('section', { class: 'km-territory', style: color ? '--map-accent:' + color : null },
    el('header', {}, note ? el('span', { class: 'km-label' }, note) : null, el('h3', {}, title)),
    el('div', { class: 'km-grid' }, ...tiles));
}

function mapReferences(subjects) {
  const sources = DOS_MAPS.filter(([id]) => subjects.some(subject => id === subject.id));
  const external = (title, href) => el('a', { href, target: '_blank', rel: 'noopener noreferrer' }, title + ' ↗');
  return el('aside', { class: 'km-sources', 'aria-label': 'Map references' },
    el('p', {}, 'Cartographic inspiration from ', external('Dominic Walliman’s Domain of Science', 'https://dosmaps.com/'), '.'),
    sources.length ? el('ul', {}, ...sources.map(([, title, href]) => el('li', {}, external(title, href)))) : null);
}

function knowledgeMapIndex(graph) {
  const nodesById = new Map(graph.nodes.map(node => [node.id, node]));
  const subjects = new Map(graph.domains.map(subject => [subject.id, { ...subject, nodes: [], connections: new Set() }]));
  const domains = KNOWLEDGE_DOMAINS.map(domain => ({ ...domain,
    subjects: domain.subjects.map(id => subjects.get(id)).filter(Boolean) }));
  const domainBySubject = new Map(domains.flatMap(domain => domain.subjects.map(subject => [subject.id, domain])));
  const unfiled = [...subjects.values()].filter(subject => !domainBySubject.has(subject.id));
  if (unfiled.length) {
    const other = { id: 'other', title: 'Other subjects', mark: '⊕', color: '#667581',
      description: 'Further areas of study in the Primer curriculum.', subjects: unfiled };
    domains.push(other);
    unfiled.forEach(subject => domainBySubject.set(subject.id, other));
  }

  const onward = new Map();
  for (const node of graph.nodes) {
    const subject = subjects.get(node.domain);
    subject.nodes.push(node);
    for (const prerequisite of node.prereqs || []) {
      if (!onward.has(prerequisite)) onward.set(prerequisite, []);
      onward.get(prerequisite).push(node);
      const source = subjects.get(nodesById.get(prerequisite)?.domain);
      if (source && source !== subject) {
        source.connections.add(subject);
        subject.connections.add(source);
      }
    }
  }
  return { nodesById, subjects, domains: domains.filter(domain => domain.subjects.length), domainBySubject, onward };
}

function moduleMapTile(node, subject, note = learningStage(node.stage).name) {
  return mapTile({ title: node.title, href: mapHref('module', node.id), note,
    mark: subject.icon || '✦', color: subject.color });
}

function moduleMapTerritories(node, detail, subject, index, stage = 5) {
  const status = node.mastered ? 'Mastered' : node.unlocked ? 'Open lesson' : 'Lesson · groundwork required';
  const lessonHref = hashFor('node', node.id);
  const visual = (detail.lesson_media || []).find(item => item.kind === 'illustration' && item.src);
  const image = visual ? el('img', { class: 'km-image', src: visual.src, srcset: visual.srcset,
    sizes: visual.srcset ? '(max-width: 600px) 80vw, 380px' : null, alt: '', decoding: 'async',
    onerror: event => event.currentTarget.replaceWith(mapEmblem(subject.icon || '✦', 'lesson')) }) : null;
  const lesson = mapTile({ title: node.title, href: lessonHref, note: status, image,
    mark: subject.icon || '✦', color: subject.color, detail: node.goal, variant: 'lesson' });
  const tiles = [mapTerritory('The lesson', 'Start here', [lesson], subject.color)];
  const cards = new Map((detail.article_cards || []).map(article => [article.title, article]));
  if ((node.articles || []).length) {
    tiles.push(mapTerritory('Read around the topic', 'Articles', node.articles.map(title => {
      const thumb = cards.get(title)?.thumb;
      return mapTile({ title, href: hashFor('reader', { title, node: node.id }), note: 'Read article',
        mark: '¶', variant: 'article', color: subject.color, image: thumb ? el('img', {
          class: 'km-image', src: '/api/image?url=' + encodeURIComponent(thumb), alt: '', loading: 'lazy',
          onerror: event => event.currentTarget.replaceWith(mapEmblem('¶', 'article')),
        }) : null });
    }), subject.color));
  }
  const relatedTile = related => {
    const relatedSubject = index.subjects.get(related.domain);
    return moduleMapTile(related, relatedSubject, relatedSubject.name);
  };
  const prerequisites = (node.prereqs || []).map(id => index.nodesById.get(id)).filter(n => n && n.stage <= stage);
  if (prerequisites.length) tiles.push(mapTerritory('What this builds on', 'Prerequisite modules', prerequisites.map(relatedTile)));
  const onward = (index.onward.get(node.id) || []).filter(n => n.stage <= stage);
  if (onward?.length) tiles.push(mapTerritory('Where this leads', 'Modules that build on this', onward.map(relatedTile)));
  return tiles;
}

// Overview copy describes the territory. Individual topics and all arrows come
// from Primer's curriculum, including their actual stage and prerequisite IDs.
const MAP_SUBJECTS = {
  math: ['Patterns, quantities, shapes and change', 'Count and compare|Calculate and measure|Number and space|Algebra and proof|Calculus and structures|Abstraction and frontiers'],
  language: ['Communicate, imagine and interpret', 'Sounds and stories|Read and write|Meaning and expression|Literature and language|Linguistics and interpretation|Language research'],
  physics: ['Matter, motion, energy and interactions', 'Push, light and heat|Motion and energy|Forces and waves|Physical laws|Models and experiments|Quantum fields and spacetime'],
  biology: ['Living systems, from cells to ecosystems', 'Living things|Bodies and habitats|Cells and ecosystems|Genes and evolution|Molecules and systems|Life at the frontier'],
  chemistry: ['What matter is made of and how it changes', 'Materials and mixing|Properties and change|Atoms and reactions|Bonds and quantities|Chemical systems|Molecular research'],
  cs: ['Information, algorithms and computation', 'Steps and patterns|Algorithms and computers|Programming and debugging|Software and data|Computation and systems|Complexity and intelligence'],
  history: ['Evidence about people and societies through time', 'Family and past|Time and place|Civilizations and exchange|Revolutions and institutions|Historical interpretation|Global histories and debates'],
  earth: ['Earth’s processes and the wider universe', 'Land, sky and weather|Planetary cycles|Earth and the cosmos|Climate and exploration|Planetary and cosmic science|Earth systems and cosmic frontiers'],
  arts: ['Making and interpreting visual, musical and performing forms', 'Color, sound and movement|Make and perform|Composition and notation|Style and harmony|Analysis and aesthetics|Craft and artistic inquiry'],
  mind: ['Thought, knowledge, society and ethical questions', 'Feelings and choices|Thinking and cooperation|Minds and questions|Logic, psychology and ethics|Knowledge and cognition|Philosophical frontiers'],
  radiology: ['Images reveal internal structures and signals', 'Light and hidden shapes|Views and layers|Pixels and echoes|Transmission and signals|Reconstruction and uncertainty|Clinical imaging references'],
  engineering: ['Model, test and improve designed systems', 'Build and try|Materials and prototypes|Mechanisms and feedback|Structures and energy|Models and reliability|Design under uncertainty'],
  health: ['Wellbeing, populations and evidence', 'Notice and ask|Messages and shared spaces|Claims and population counts|Epidemiology and equity|Causal questions and evidence|Evaluation and implementation'],
  environment: ['Landscapes, agriculture and resource cycles', 'Living places and seeds|Soil and food|Farms and water|Nutrients and tradeoffs|Resilience and field evidence|Sustainability and adaptation'],
  design: ['Places and experiences shaped around human needs', 'Spaces and shelters|Plans and prototypes|Scale and accessibility|Climate and communication|Performance and evaluation|Participatory design research'],
  business: ['Choices, enterprises, markets and institutions', 'Needs and work|Exchange and resources|Markets and public goods|Enterprises and policy|Models and evidence|Econometrics and strategy'],
  civics: ['Rights, rules, public power and collective decisions', 'Turns and community|Decisions and rights|Institutions and evidence|Reasoning and participation|Constitutional design|Governance and reform'],
  education: ['How people learn and how teaching can help', 'Wonder and practice|Remember and explain|Plan and adapt|Lessons and transfer|Measurement and evidence|Learning research'],
  media: ['How messages are made, circulated and understood', 'Messages and stories|Authorship and expression|Sources and framing|Journalism and platforms|Institutions and audiences|Effects and governance'],
};
const MAP_BRIDGES = [
  ['Shapes become shelters', 'math.0.shapes', 'design.0.shelters'],
  ['Plants become gardens', 'bio.0.plants', 'env.0.seeds'],
  ['Compare movement', 'math.0.compare', 'phys.1.motion'],
  ['Represent numbers', 'math.1.place-value', 'cs.1.binary'],
  ['Test material properties', 'phys.1.magnets', 'chem.1.materials-props'],
  ['Account for resources', 'math.1.subtraction', 'business.1.resources'],
  ['Molecules power life', 'chem.2.molecules', 'bio.2.photosynthesis'],
  ['Waves locate boundaries', 'phys.2.waves', 'img.2.echoes'],
  ['Motion becomes mechanisms', 'phys.1.machines', 'eng.2.mechanisms'],
  ['Steps become feedback systems', 'cs.1.algorithms', 'eng.2.systems'],
  ['Trace the water budget', 'earth.1.water-cycle', 'env.2.water'],
  ['Rhythm shapes poetry', 'arts.1.beat', 'lang.2.poetry'],
  ['Societies shape stories', 'hist.1.ancient', 'lang.2.mythology'],
  ['Evidence supports fair hearings', 'lang.2.research', 'civics.2.evidence-hearings'],
  ['Check claims and sources', 'lang.2.research', 'media.2.verification'],
  ['Plan and monitor learning', 'mind.2.study-skills', 'education.2.study-plan'],
  ['Society shapes wellbeing', 'mind.2.society', 'health.3.determinants'],
  ['Organize visual information', 'arts.3.design', 'design.3.communication'],
  ['Model building performance', 'eng.3.energy-design', 'design.4.performance'],
  ['Model language computationally', 'cs.3.algorithms', 'lang.5.comp-ling'],
  ['Physiology informs interpretation', 'bio.4.physiology', 'rad.3.contrast'],
];
const MAP_NS = 'http://www.w3.org/2000/svg';
let mapArtworkPromise;
function mapSvg(tag, props = {}, ...children) {
  const element = document.createElementNS(MAP_NS, tag);
  Object.entries(props).forEach(([name, value]) => element.setAttribute(name, value));
  children.forEach(child => element.append(child.nodeType ? child : document.createTextNode(child)));
  return element;
}
function mapTextLines(text, width) {
  const words = String(text || '').split(/\s+/);
  const lines = [''];
  for (const word of words) {
    const last = lines.length - 1;
    if (lines[last] && lines[last].length + word.length + 1 > width) lines.push(word);
    else lines[last] += (lines[last] ? ' ' : '') + word;
  }
  return lines;
}
function mapText(parent, text, x, y, width = 35, className = 'km-svg-copy', lineHeight = 23) {
  const lines = mapTextLines(text, width);
  const node = mapSvg('text', { x, y, class: className });
  lines.forEach((line, i) => node.append(mapSvg('tspan', { x, dy: i ? lineHeight : 0 }, line)));
  parent.append(node);
  return lines.length * lineHeight;
}
function mapSvgLink(parent, href, title) {
  const link = mapSvg('a', { href, tabindex: 0, 'aria-label': title, class: 'km-svg-link' });
  link.append(mapSvg('title', {}, title));
  parent.append(link);
  return link;
}
function mapDrawing(parent, subject, x, y, width, height, href) {
  const link = mapSvgLink(parent, href, subject.name + ' illustrated map');
  link.append(mapSvg('use', { href: '#plate-' + subject.id, x, y, width, height }));
  return link;
}
function mapScene(title, subtitle, width, height, artwork) {
  const svg = mapSvg('svg', { xmlns: MAP_NS, viewBox: `0 0 ${width} ${height}`, width, height,
    class: 'km-scene', role: 'group', 'aria-label': title + ' illustrated knowledge map' });
  const defs = mapSvg('defs', {}, mapSvg('marker', { id: 'km-arrowhead', viewBox: '0 0 10 10',
    refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto-start-reverse' },
  mapSvg('path', { d: 'M0 0 10 5 0 10Z', fill: '#647d75' })));
  if (artwork) for (const definition of artwork.querySelectorAll('svg > defs > *')) defs.append(document.importNode(definition, true));
  if (artwork) for (const symbol of artwork.querySelectorAll('symbol')) {
    const copy = document.importNode(symbol, true);
    copy.id = 'plate-' + symbol.id;
    defs.append(copy);
  }
  svg.append(defs, mapSvg('rect', { width, height, fill: '#fbf7ed' }),
    mapSvg('rect', { x: 18, y: 18, width: width - 36, height: height - 36, rx: 12, fill: 'none', stroke: '#b7c2b3' }));
  mapText(svg, 'PRIMER / AN ILLUSTRATED ATLAS OF KNOWLEDGE', 52, 58, 100, 'km-svg-kicker', 16);
  const heading = mapText(svg, title, 52, 112, Math.floor(width / 25), 'km-svg-title', 43);
  mapText(svg, subtitle, 54, 123 + heading, Math.floor(width / 12), 'km-svg-copy', 24);
  return svg;
}
function mapCurve(parent, from, to, key, label) {
  const group = mapSvg('g', { class: 'km-connection', 'data-connection': key,
    'data-from': from.id, 'data-to': to.id });
  const direction = to.x >= from.x ? 1 : -1;
  const bend = Math.max(80, Math.abs(to.x - from.x) * .45);
  const pathId = 'km-edge-' + parent.childElementCount;
  group.append(mapSvg('path', { id: pathId, d: `M${from.x} ${from.y} C${from.x + direction * bend} ${from.y},${to.x - direction * bend} ${to.y},${to.x} ${to.y}`,
    fill: 'none', stroke: '#647d75', 'stroke-width': 2.5, 'marker-end': 'url(#km-arrowhead)' }),
    mapSvg('title', {}, label));
  if (/^\d+$/.test(key)) group.append(mapSvg('text', { class: 'km-edge-label' },
    mapSvg('textPath', { href: '#' + pathId, startOffset: '50%', 'text-anchor': 'middle' }, label)));
  parent.append(group);
}
function mapBridges(index, stage, domain) {
  return MAP_BRIDGES.flatMap(([label, from, to]) => {
    const source = index.nodesById.get(from), target = index.nodesById.get(to);
    if (!source || !target || source.stage > stage || target.stage > stage || !target.prereqs.includes(source.id)) return [];
    if (domain && !domain.subjects.some(subject => [source.domain, target.domain].includes(subject.id))) return [];
    return [{ label, source, target }];
  });
}
// Coordinates describe the fixed geography of each commissioned atlas plate.
// The same landmarks are retained while the learning level adds live detail.
const MAP_LANDMARKS = {
  math: { domain: 'formal', point: [.24, .47], crop: [0, 0, .56, 1], world: [.14, .21] },
  cs: { domain: 'formal', point: [.76, .47], crop: [.44, 0, .56, 1], world: [.35, .28] },
  physics: { domain: 'natural', point: [.23, .23], crop: [0, 0, .57, .58], world: [.70, .14] },
  chemistry: { domain: 'natural', point: [.76, .23], crop: [.43, 0, .57, .58], world: [.81, .28] },
  biology: { domain: 'natural', point: [.24, .76], crop: [0, .42, .57, .58], world: [.91, .31] },
  earth: { domain: 'natural', point: [.77, .76], crop: [.43, .42, .57, .58], world: [.54, .13] },
  engineering: { domain: 'applied', point: [.24, .24], crop: [0, 0, .55, .58], world: [.78, .51] },
  design: { domain: 'applied', point: [.76, .24], crop: [.45, 0, .55, .58], world: [.79, .73] },
  environment: { domain: 'applied', point: [.17, .76], crop: [0, .43, .43, .57], world: [.93, .64] },
  health: { domain: 'applied', point: [.50, .78], crop: [.28, .43, .44, .57], world: [.73, .91] },
  radiology: { domain: 'applied', point: [.84, .76], crop: [.57, .43, .43, .57], world: [.91, .85] },
  history: { domain: 'society', point: [.23, .23], crop: [0, 0, .55, .58], world: [.31, .85] },
  mind: { domain: 'society', point: [.76, .23], crop: [.45, 0, .55, .58], world: [.65, .74] },
  business: { domain: 'society', point: [.17, .76], crop: [0, .43, .43, .57], world: [.49, .83] },
  civics: { domain: 'society', point: [.50, .78], crop: [.28, .43, .44, .57], world: [.44, .68] },
  education: { domain: 'society', point: [.84, .76], crop: [.57, .43, .43, .57], world: [.67, .92] },
  language: { domain: 'culture', point: [.23, .27], crop: [0, 0, .55, .65], world: [.16, .72] },
  arts: { domain: 'culture', point: [.50, .76], crop: [.15, .35, .70, .65], world: [.09, .53] },
  media: { domain: 'culture', point: [.77, .27], crop: [.45, 0, .55, .65], world: [.15, .88] },
};
const WORLD_TERRITORIES = {
  formal: { point: [.19, .23], radius: [.20, .24], label: [65, 222], width: 850, columns: 2 },
  natural: { point: [.77, .24], radius: [.23, .25], label: [1250, 222], width: 1060, columns: 2 },
  culture: { point: [.17, .72], radius: [.20, .25], label: [65, 1975], width: 700, columns: 1 },
  society: { point: [.47, .81], radius: [.20, .17], label: [850, 1975], width: 690, columns: 1 },
  applied: { point: [.83, .73], radius: [.18, .25], label: [1650, 1975], width: 680, columns: 1 },
};
function mapRaster(parent, asset, x, y, width, height, subjects = [], fallbackFrame = { x, y, width, height }) {
  const group = mapSvg('g', { class: 'km-artwork-layer' });
  const image = mapSvg('image', { href: '/app/knowledge-art/' + asset + '.webp', x, y, width, height,
    preserveAspectRatio: 'xMidYMid meet', class: 'km-artwork' });
  image.append(mapSvg('title', {}, 'Original illustrated ' + asset + ' knowledge landscape'));
  group.append(image);
  image.addEventListener('error', () => {
    image.remove();
    const columns = Math.max(1, Math.ceil(Math.sqrt(subjects.length)));
    const rows = Math.max(1, Math.ceil(subjects.length / columns));
    subjects.forEach((subject, i) => group.append(mapSvg('use', { href: '#plate-' + subject.id,
      x: fallbackFrame.x + i % columns * fallbackFrame.width / columns, y: fallbackFrame.y + Math.floor(i / columns) * fallbackFrame.height / rows,
      width: fallbackFrame.width / columns, height: fallbackFrame.height / rows })));
    group.dispatchEvent(new CustomEvent('map-artwork-error', { bubbles: true }));
  }, { once: true });
  parent.append(group);
  return group;
}
function mapSubjectLandscape(parent, subject, x, y, width, height, href) {
  const landmark = MAP_LANDMARKS[subject.id];
  if (!landmark) return mapDrawing(parent, subject, x, y, width, height, href);
  const link = parent.localName === 'a' ? parent : mapSvgLink(parent, href, subject.name + ' illustrated learning landscape');
  const [cx, cy, cw, ch] = landmark.crop;
  const crop = mapSvg('svg', { x, y, width, height, viewBox: `${cx * 1536} ${cy * 1024} ${cw * 1536} ${ch * 1024}`,
    preserveAspectRatio: 'xMidYMid slice', overflow: 'hidden' });
  mapRaster(crop, landmark.domain, 0, 0, 1536, 1024, [subject], { x: cx * 1536, y: cy * 1024, width: cw * 1536, height: ch * 1024 });
  link.append(crop);
  return link;
}
function mapLessonLandmarks(subject, stage) {
  // One persistent landmark per introduced level gives the overview a legible
  // cumulative spine. Every module remains in the full subject map and index.
  const landmarks = [];
  for (let level = 0; level <= stage; level++) {
    const node = subject.nodes.find(item => item.stage === level);
    if (node) landmarks.push(node);
  }
  return landmarks;
}
function mapSubjectCallout(svg, subject, stage, x, y, width, anchor) {
  const group = mapSvg('g', { class: 'km-landscape-callout km-subject-island', 'data-subject': subject.id });
  svg.append(group);
  const title = mapSvgLink(group, mapHref('subject', subject.id), subject.name + ' subject map');
  const chars = Math.max(24, Math.floor(width / 13));
  let at = y;
  at += mapText(title, subject.name, x, at, chars, 'km-svg-heading', 29) + 8;
  const content = MAP_SUBJECTS[subject.id] || [subject.tagline, ''];
  at += mapText(group, content[0], x, at, Math.floor(width / 10.5), 'km-svg-copy', 24) + 20;
  const landmarks = mapLessonLandmarks(subject, stage);
  landmarks.forEach(node => {
    const link = mapSvgLink(group, mapHref('module', node.id), node.title + ' module map');
    link.setAttribute('data-landmark', node.id);
    mapText(link, STAGE_NAMES[node.stage].toUpperCase(), x, at, 30, 'km-svg-small', 17);
    at += 24;
    at += mapText(link, '↗ ' + node.title, x, at, chars, 'km-svg-topic', 25) + 13;
  });
  const current = landmarks[landmarks.length - 1];
  if (current) {
    at += 7;
    at += mapText(group, current.goal || '', x, at, Math.floor(width / 10.5), 'km-svg-copy', 24);
  }
  if (anchor) {
    const edge = x < anchor.x ? x + width + 10 : x - 10;
    group.insertBefore(mapSvg('path', { d: `M${edge} ${y + 20}Q${(edge + anchor.x) / 2} ${y + 20} ${anchor.x} ${anchor.y}`,
      class: 'km-callout-leader', fill: 'none', stroke: subject.color, 'stroke-width': 2 }), group.firstChild);
    group.append(mapSvg('circle', { cx: anchor.x, cy: anchor.y, r: 7, fill: '#fbf7ed', stroke: subject.color, 'stroke-width': 3 }));
  }
  return at - y;
}
function overviewScene(index, stage, domain, artwork) {
  if (domain) return domainLandscapeScene(index, stage, domain, artwork);
  const width = 2400, height = 2445;
  const svg = mapScene('A landscape of knowledge', 'Follow the paths between ideas · explore through ' + STAGE_NAMES[stage], width, height, artwork);
  const image = { x: 50, y: 390, width: 2300, height: 1533 };
  mapRaster(svg, 'world', image.x, image.y, image.width, image.height, [...index.subjects.values()]);
  mapText(svg, 'Illustrated overview', 65, 1949, 50, 'km-svg-small');
  const positions = new Map();
  for (const subject of index.subjects.values()) {
    const point = MAP_LANDMARKS[subject.id]?.world;
    if (point) positions.set(subject.id, { x: image.x + point[0] * image.width, y: image.y + point[1] * image.height, id: subject.id });
  }
  const paths = mapSvg('g', { class: 'km-connections km-landscape-connections' });
  svg.append(paths);
  const bridges = mapBridges(index, stage).filter(bridge => positions.has(bridge.source.domain) && positions.has(bridge.target.domain));
  bridges.forEach((bridge, i) => mapCurve(paths, positions.get(bridge.source.domain), positions.get(bridge.target.domain), String(i), bridge.label));
  index.domains.forEach(domain => {
    const region = WORLD_TERRITORIES[domain.id];
    if (!region) return;
    const hotspot = mapSvgLink(svg, mapHref('domain', domain.id), 'Explore ' + domain.title + ' in the illustration');
    hotspot.classList.add('km-region-hotspot');
    hotspot.append(mapSvg('ellipse', { cx: image.x + region.point[0] * image.width, cy: image.y + region.point[1] * image.height,
      rx: region.radius[0] * image.width, ry: region.radius[1] * image.height, fill: 'transparent', stroke: 'transparent', 'stroke-width': 4 }));
    const [x, y] = region.label;
    const heading = mapSvgLink(svg, mapHref('domain', domain.id), domain.title + ' domain map');
    mapText(heading, domain.title, x, y, 45, 'km-svg-domain', 30);
    svg.append(mapSvg('path', { d: `M${x} ${y + 12}h${region.width}`, stroke: domain.color, 'stroke-width': 3 }));
    domain.subjects.forEach((subject, i) => {
      const sx = x + (i % region.columns) * region.width / region.columns;
      const sy = y + 49 + Math.floor(i / region.columns) * 69;
      const group = mapSvg('g', { class: 'km-subject-island km-landscape-label', 'data-subject': subject.id });
      svg.append(group);
      const link = mapSvgLink(group, mapHref('subject', subject.id), subject.name + ' subject map');
      mapText(link, subject.name + ' ↗', sx, sy, Math.floor(region.width / region.columns / 13), 'km-svg-topic', 24);
      mapText(group, MAP_SUBJECTS[subject.id]?.[1].split('|')[stage] || subject.tagline, sx, sy + 28,
        Math.floor(region.width / region.columns / 10), 'km-svg-focus', 20);
    });
  });
  mapText(svg, 'Connections grow with your learning', 850, 1060, 34, 'km-svg-heading', 30);
  mapText(svg, 'Select a named bridge below to trace a prerequisite from one subject into another.', 850, 1107, 43, 'km-svg-copy', 27);
  return { svg, bridges };
}
function domainLandscapeScene(index, stage, domain, artwork) {
  const width = 2580, height = 2990;
  const svg = mapScene(domain.title, domain.description + ' · through ' + STAGE_NAMES[stage], width, height, artwork);
  const image = { x: 430, y: 330, width: 1720, height: 1147 };
  mapRaster(svg, domain.id, image.x, image.y, image.width, image.height, domain.subjects);
  mapText(svg, 'Illustrated overview', image.x, image.y + image.height + 28, 50, 'km-svg-small');
  const positions = new Map();
  domain.subjects.forEach(subject => {
    const point = MAP_LANDMARKS[subject.id]?.point || [.5, .5];
    positions.set(subject.id, { x: image.x + point[0] * image.width, y: image.y + point[1] * image.height, id: subject.id });
  });
  const paths = mapSvg('g', { class: 'km-connections km-landscape-connections' });
  svg.append(paths);
  const bridges = mapBridges(index, stage, domain);
  const external = [...new Set(bridges.flatMap(bridge => [bridge.source.domain, bridge.target.domain]))]
    .filter(id => !positions.has(id));
  if (external.length) {
    mapText(svg, 'PATHS INTO OTHER DOMAINS', 65, 2490, 70, 'km-svg-kicker');
    external.forEach((id, i) => {
      const subject = index.subjects.get(id);
      const x = 65 + i % 3 * 825, y = 2540 + Math.floor(i / 3) * 72;
      const group = mapSvg('g', { class: 'km-landscape-label', 'data-subject': id });
      svg.append(group);
      const link = mapSvgLink(group, mapHref('subject', id), subject.name + ' subject map');
      mapText(link, subject.name + ' ↗', x, y, 58, 'km-svg-topic', 24);
      positions.set(id, { x: x + 15, y: y - 10, id });
    });
  }
  bridges.forEach((bridge, i) => mapCurve(paths, positions.get(bridge.source.domain), positions.get(bridge.target.domain), String(i), bridge.label));
  const slots = domain.subjects.length <= 2 ? [[65, 390, 350], [2185, 390, 330]]
    : domain.subjects.length === 3 ? [[65, 390, 350], [920, 1590, 740], [2185, 390, 330]]
    : [[65, 390, 350], [2185, 390, 330], [65, 1590, 650], [920, 1590, 740], [1835, 1590, 650]];
  const ordered = domain.subjects.length === 4 ? [slots[0], slots[1], slots[2], slots[4]] : slots;
  domain.subjects.forEach((subject, i) => {
    const anchor = positions.get(subject.id);
    const hotspot = mapSvgLink(svg, mapHref('subject', subject.id), 'Explore ' + subject.name + ' in the illustration');
    hotspot.classList.add('km-region-hotspot');
    hotspot.setAttribute('data-subject', subject.id);
    hotspot.append(mapSvg('ellipse', { cx: anchor.x, cy: anchor.y, rx: 245, ry: 210, fill: 'transparent', stroke: 'transparent', 'stroke-width': 4 }));
    const [x, y, boxWidth] = ordered[i] || [920, 1590, 740];
    mapSubjectCallout(svg, subject, stage, x, y, boxWidth, anchor);
  });
  if (domain.subjects.length <= 2) {
    mapText(svg, 'Shared foundations', 750, 1680, 60, 'km-svg-heading');
    mapText(svg, 'Each level adds another learning landmark. Open a subject to explore the full web of topics, explanations and prerequisites.', 750, 1730, 90, 'km-svg-copy', 28);
  }
  return { svg, bridges };
}
function subjectScene(subject, index, stage, artwork) {
  const groups = [];
  for (let at = 0; at <= stage; at++) {
    const nodes = subject.nodes.filter(node => node.stage === at);
    const sections = new Map();
    nodes.forEach(node => {
      const key = node.section || STAGE_NAMES[at];
      if (!sections.has(key)) sections.set(key, []);
      sections.get(key).push(node);
    });
    sections.forEach((items, label) => groups.push({ stage: at, label, nodes: items }));
  }
  const columnWidth = 395, columns = Math.min(4, Math.max(3, groups.length));
  const width = 80 + columns * columnWidth;
  const rows = [];
  for (let i = 0; i < groups.length; i += columns) rows.push(groups.slice(i, i + columns));
  const rowHeights = rows.map(row => 180 + Math.max(...row.map(g => g.nodes.reduce((height, node) =>
    height + Math.max(100, mapTextLines(node.title, 30).length * 25 + 52), 0))));
  const heroHeight = Math.max(1250, 1110 + Math.max(...mapLessonLandmarks(subject, stage).map(item => mapTextLines(item.goal, Math.floor((width - 170) / 21)).length * 27)));
  const height = heroHeight + 25 + rowHeights.reduce((sum, value) => sum + value, 0);
  const content = MAP_SUBJECTS[subject.id] || [subject.tagline, ''];
  const svg = mapScene(subject.name, content[0] + ' · through ' + STAGE_NAMES[stage], width, height, artwork);
  const landmark = subject.nodes.find(n => n.stage === stage) || subject.nodes[0];
  mapSubjectLandscape(svg, subject, 50, 215, width - 100, 650, mapHref('module', landmark.id));
  const calloutWidth = (width - 170) / 2;
  const representative = mapLessonLandmarks(subject, stage);
  const lessons = [representative[0], representative[representative.length - 1]].filter((item, i, items) => item && items.indexOf(item) === i);
  lessons.forEach((item, i) => {
    const x = 60 + i * (calloutWidth + 50);
    const link = mapSvgLink(svg, mapHref('module', item.id), item.title + ' module map');
    mapText(link, STAGE_NAMES[item.stage].toUpperCase(), x, 918, 35, 'km-svg-kicker');
    const used = mapText(link, item.title + ' ↗', x, 958, Math.floor(calloutWidth / 13), 'km-svg-heading', 30);
    mapText(svg, item.goal || '', x, 978 + used, Math.floor(calloutWidth / 10.5), 'km-svg-copy', 27);
  });
  mapText(svg, 'Illustrated overview', 60, 890, 50, 'km-svg-small');
  mapText(svg, 'THE SUBJECT IN DEPTH', 60, heroHeight - 43, 70, 'km-svg-kicker');
  const paths = mapSvg('g', { class: 'km-connections' });
  svg.append(paths);
  const positions = new Map();
  let y = heroHeight;
  rows.forEach((row, rowIndex) => {
    row.forEach((group, col) => {
      const x = 45 + col * columnWidth;
      svg.append(mapSvg('path', { d: `M${x + 14} ${y + 14}h335M${x + 14} ${y + 14}v${rowHeights[rowIndex] - 50}`, fill: 'none', stroke: subject.color, 'stroke-opacity': .4, 'stroke-width': 2 }));
      mapText(svg, STAGE_NAMES[group.stage].toUpperCase(), x + 22, y + 34, 30, 'km-svg-kicker');
      const headingHeight = mapText(svg, group.label, x + 22, y + 67, 27, 'km-svg-heading', 25);
      let nodeY = y + 83 + headingHeight;
      group.nodes.forEach(node => {
        const itemHeight = Math.max(100, mapTextLines(node.title, 30).length * 25 + 52);
        positions.set(node.id, { x: x + 16, y: nodeY + 28, id: node.id });
        const link = mapSvgLink(svg, mapHref('module', node.id), node.title + ' module map');
        link.setAttribute('data-topic', node.id);
        link.append(mapSvg('rect', { x: x + 16, y: nodeY - 7, width: 333, height: itemHeight - 14,
          rx: 3, fill: '#fbf7ed', stroke: 'none' }), mapSvg('circle', { cx: x + 16, cy: nodeY + 28, r: 5, fill: subject.color }));
        const used = mapText(link, node.title, x + 32, nodeY + 21, 30, 'km-svg-topic', 25);
        mapText(link, 'Explore idea ↗', x + 32, nodeY + 29 + used, 40, 'km-svg-small', 20);
        nodeY += itemHeight;
      });
    });
    y += rowHeights[rowIndex];
  });
  for (const [id, to] of positions) {
    for (const prerequisite of index.nodesById.get(id).prereqs || []) {
      const from = positions.get(prerequisite);
      if (from) mapCurve(paths, { ...from, x: from.x + 333 }, to, prerequisite + '/' + id, index.nodesById.get(prerequisite).title + ' → ' + index.nodesById.get(id).title);
    }
  }
  return { svg, bridges: mapBridges(index, stage).filter(b => [b.source.domain, b.target.domain].includes(subject.id)) };
}
function moduleScene(node, detail, subject, index, stage, artwork) {
  const prerequisites = (node.prereqs || []).map(id => index.nodesById.get(id)).filter(n => n && n.stage <= stage);
  const onward = (index.onward.get(node.id) || []).filter(n => n.stage <= stage);
  const articles = node.articles || [];
  const cardHeight = item => Math.max(100, mapTextLines(item.title, 29).length * 24 + 55);
  const columnHeight = items => items.reduce((sum, item) => sum + cardHeight(item) + 15, 0);
  const readingY = 812 + mapTextLines(node.goal, 61).length * 26;
  const articlesHeight = articles.reduce((sum, title) => sum + mapTextLines('↗ ' + title, 47).length * 24 + 28, 0);
  const height = Math.max(1130, 360 + Math.max(columnHeight(prerequisites), columnHeight(onward)), readingY + 100 + articlesHeight);
  const svg = mapScene(node.title, subject.name + ' · ' + STAGE_NAMES[node.stage] + ' module · connections through ' + STAGE_NAMES[stage], 1720, height, artwork);
  const paths = mapSvg('g', { class: 'km-connections' });
  svg.append(paths);
  mapText(svg, 'WHAT THIS BUILDS ON', 60, 240, 38, 'km-svg-kicker');
  mapText(svg, 'WHERE THIS LEADS', 1280, 240, 38, 'km-svg-kicker');
  const anchor = { x: 860, y: 480, id: node.id };
  const connect = (nodes, x, foundation) => {
    let top = 275;
    nodes.forEach(item => {
      const height = cardHeight(item);
      const at = { x: foundation ? x + 325 : x, y: top + height / 2, id: item.id };
      mapCurve(paths, foundation ? at : anchor, foundation ? anchor : at, item.id, foundation ? item.title + ' supports this module' : 'This module supports ' + item.title);
      const link = mapSvgLink(svg, mapHref('module', item.id), item.title + ' module map');
      link.setAttribute('data-topic', item.id);
      link.append(mapSvg('rect', { x, y: top, width: 330, height, rx: 15, fill: '#f4f1e4', stroke: '#b1c0ad' }));
      const used = mapText(link, item.title, x + 17, top + 30, 29, 'km-svg-topic', 24);
      mapText(link, STAGE_NAMES[item.stage] + ' ↗', x + 17, top + 40 + used, 35, 'km-svg-small', 20);
      top += height + 15;
    });
  };
  connect(prerequisites, 60, true); connect(onward, 1280, false);
  if (!prerequisites.length) mapText(svg, 'No earlier modules listed at this level.', 60, 292, 27);
  if (!onward.length) mapText(svg, 'Raise the level to explore later connections.', 1280, 292, 28);
  svg.append(mapSvg('path', { d: 'M540 230H1180M540 725H1180', stroke: subject.color, 'stroke-opacity': .45, 'stroke-width': 2 }));
  const visual = (detail.lesson_media || []).find(item => item.kind === 'illustration' && item.src);
  const link = mapSvgLink(svg, hashFor('node', node.id), 'Open lesson ' + node.title);
  if (visual) {
    const image = mapSvg('image', { href: largestSrcFromSet(visual.srcset, visual.src), x: 600, y: 264, width: 520, height: 310, preserveAspectRatio: 'xMidYMid meet' });
    image.addEventListener('error', () => { image.remove(); mapSubjectLandscape(link, subject, 560, 260, 600, 330, hashFor('node', node.id)); }, { once: true });
    link.append(image);
  } else mapSubjectLandscape(link, subject, 560, 260, 600, 330, hashFor('node', node.id));
  mapText(link, node.title, 610, 610, 41, 'km-svg-heading', 30);
  mapText(link, 'Open the lesson ↗', 610, 691, 50, 'km-svg-topic');
  mapText(svg, node.goal || '', 540, 776, 61, 'km-svg-copy', 26);
  mapText(svg, 'READ INTO THE IDEA', 550, readingY, 50, 'km-svg-kicker');
  let articleY = readingY + 48;
  articles.forEach(title => {
    const article = mapSvgLink(svg, hashFor('reader', { title, node: node.id }), 'Read ' + title);
    articleY += mapText(article, '↗ ' + title, 550, articleY, 47, 'km-svg-topic', 24) + 28;
  });
  return { svg, bridges: [] };
}
async function renderKnowledgeMaps(page, [level, id, selectedStage] = []) {
  if (level === 'world') level = undefined;
  const navigation = _readerContextSeq;
  loading(page);
  let index, domain, subject, node, detail, artwork;
  try {
    if (!mapArtworkPromise) mapArtworkPromise = fetch('/app/knowledge-illustrations.svg').then(response => {
      if (!response.ok) throw new Error('Illustrations could not load');
      return response.text();
    }).then(raw => {
      const document = new DOMParser().parseFromString(raw, 'image/svg+xml');
      if (document.querySelector('parsererror')) throw new Error('Illustrations could not load');
      return document;
    }).catch(error => { mapArtworkPromise = null; throw error; });
    [index, artwork] = await Promise.all([
      S.knowledgeMapIndex || api.get('/api/curriculum').then(knowledgeMapIndex), mapArtworkPromise,
    ]);
    if (navigation !== _readerContextSeq) return;
    S.knowledgeMapIndex = index;
    if (level === 'domain') domain = index.domains.find(entry => entry.id === id);
    if (level === 'module') node = index.nodesById.get(id);
    if (node) detail = await api.get('/api/curriculum/node/' + encodeURIComponent(node.id));
    if (level === 'subject' || node) subject = index.subjects.get(node?.domain || id);
    if (subject) domain = index.domainBySubject.get(subject.id);
  } catch (error) {
    if (navigation !== _readerContextSeq) return;
    if (isNoProfile(error)) { toOnboarding(); return; }
    page.replaceChildren(errCard(error, () => renderRoute()));
    return;
  }
  if (navigation !== _readerContextSeq) return;
  page.replaceChildren();
  if (level && !domain) {
    page.append(pagehead('Primer · Knowledge Atlas', 'Map unavailable', 'Choose a domain or subject from the knowledge maps.'),
      el('a', { href: mapHref() }, 'Knowledge maps'));
    return;
  }
  const initialStage = /^[0-5]$/.test(selectedStage || '') ? Number(selectedStage)
    : knowledgeMapStage ?? Math.max(node?.stage || 0, Number.isInteger(S.stage) ? S.stage : 2);
  knowledgeMapStage = Math.min(5, Math.max(0, initialStage));
  const title = node?.title || subject?.name || domain?.title || 'Knowledge maps';
  const trail = el('nav', { class: 'km-breadcrumb', 'aria-label': 'Map location' });
  page.append(trail, pagehead(node ? 'Module map' : subject ? 'Subject map' : domain ? 'Domain map' : 'Primer · Illustrated knowledge atlas',
    title, 'Explore the illustrations, trace the connections, and follow a topic into its lesson.'));

  const stageReadout = el('strong', { id: 'km-stage-readout' });
  const stageHelp = el('p', { class: 'km-stage-help', id: 'km-stage-help' });
  const slider = el('input', { id: 'km-stage', type: 'range', min: 0, max: 5, step: 1, value: knowledgeMapStage,
    'aria-label': 'Explore through learning level', 'aria-describedby': 'km-stage-help', oninput: event => changeStage(Number(event.target.value)) });
  const stageButtons = learningStages().map(stage => btn({ class: 'km-stage-stop', onclick: () => changeStage(stage.i) }, stage.name));
  const levelControl = el('section', { class: 'km-level-control', 'aria-label': 'Map learning level' },
    el('label', { for: 'km-stage' }, 'Grow the map ', stageReadout), slider,
    el('div', { class: 'km-stage-stops' }, ...stageButtons), stageHelp);
  const artworkStatus = el('p', { class: 'km-artwork-status', role: 'status', hidden: '' });
  const sceneHost = el('div', { class: 'km-scene-host' });
  sceneHost.addEventListener('map-artwork-error', () => {
    artworkStatus.hidden = false;
    artworkStatus.replaceChildren('The landscape illustration could not load. ', btn({ class: 'btn ghost small', onclick: () => renderRoute() }, 'Retry illustration'));
  });
  const viewport = el('div', { class: 'km-viewport', tabindex: 0, role: 'region', 'aria-label': 'Illustrated map canvas',
    'aria-describedby': 'km-map-help' }, sceneHost);
  const output = el('output', { class: 'km-scale', 'aria-live': 'polite' }, '100%');
  let zoom = 100, currentScene, selectedBridge = null;
  const less = btn({ class: 'btn ghost small', 'aria-label': 'Zoom out', onclick: () => setZoom(zoom - 25) }, '−');
  const more = btn({ class: 'btn ghost small', 'aria-label': 'Zoom in', onclick: () => setZoom(zoom + 25) }, '+');
  const connections = el('input', { type: 'checkbox', checked: '', onchange: () => {
    sceneHost.classList.toggle('km-hide-connections', !connections.checked);
  } });
  const toolbar = el('div', { class: 'km-toolbar' },
    el('p', { id: 'km-map-help' }, 'Labels and illustrations open maps or lessons. Zoom in and scroll to explore.'),
    el('div', { class: 'km-controls' }, less, output, more,
      btn({ class: 'btn ghost small', onclick: () => { setZoom(100); viewport.scrollTo(0, 0); } }, 'Fit map'),
      btn({ class: 'btn ghost small', onclick: () => setZoom(Math.round(currentScene.svg.viewBox.baseVal.width / viewport.clientWidth * 100)) }, 'Read size'),
      el('label', {}, connections, ' Connections')));
  const sheet = el('section', { class: 'km-sheet' }, toolbar, artworkStatus, viewport);
  const bridgesPanel = el('section', { class: 'km-bridges', 'aria-label': 'Connections between subjects' });
  const textIndex = el('details', { class: 'km-text-index' }, el('summary', {}, 'Browse the wiki index'));
  const search = el('input', { type: 'search', 'aria-label': 'Search this map', placeholder: 'Find a topic in this map…', oninput: paintIndex });
  search.hidden = Boolean(node);
  const indexBody = el('div', { class: 'km-index-body' });
  textIndex.append(search, indexBody);
  page.append(levelControl, sheet, bridgesPanel, textIndex, mapReferences(subject ? [subject] : domain?.subjects || [...index.subjects.values()]));

  function setZoom(value) {
    zoom = Math.min(800, Math.max(25, value));
    currentScene.svg.style.width = zoom + '%';
    output.textContent = zoom + '%';
    less.disabled = zoom === 25; more.disabled = zoom === 800;
  }
  function highlightSubject(subjectId) {
    currentScene.svg.querySelectorAll('.km-connection').forEach(edge => {
      edge.classList.toggle('km-traced', subjectId ? [edge.dataset.from, edge.dataset.to].includes(subjectId) : edge.dataset.connection === selectedBridge);
    });
  }
  function paint() {
    artworkStatus.hidden = true;
    selectedBridge = null;
    stageReadout.textContent = 'through ' + STAGE_NAMES[knowledgeMapStage];
    slider.value = knowledgeMapStage;
    syncRangeFill(slider);
    slider.setAttribute('aria-valuetext', STAGE_NAMES[knowledgeMapStage]);
    stageButtons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === knowledgeMapStage)));
    stageHelp.textContent = 'Includes every earlier level. ' + stageLabel(knowledgeMapStage)
      + (node && node.stage > knowledgeMapStage ? '. This ' + STAGE_NAMES[node.stage] + ' module stays in view while you explore its foundations.' : '.');
    trail.replaceChildren(el('a', { href: hashFor('atlas') }, 'The Atlas'));
    if (level) trail.append(el('a', { href: mapHref() }, 'Knowledge maps'));
    if (subject) trail.append(el('a', { href: mapHref('domain', domain.id) }, domain.title));
    if (node) trail.append(el('a', { href: mapHref('subject', subject.id) }, subject.name));
    currentScene = node ? moduleScene(node, detail, subject, index, knowledgeMapStage, artwork)
      : subject ? subjectScene(subject, index, knowledgeMapStage, artwork)
      : overviewScene(index, knowledgeMapStage, domain, artwork);
    sceneHost.replaceChildren(currentScene.svg);
    setZoom(zoom);
    currentScene.svg.addEventListener('pointerover', event => highlightSubject(event.target.closest('[data-subject],[data-topic]')?.dataset.subject || event.target.closest('[data-topic]')?.dataset.topic));
    currentScene.svg.addEventListener('focusin', event => highlightSubject(event.target.closest('[data-subject],[data-topic]')?.dataset.subject || event.target.closest('[data-topic]')?.dataset.topic));
    currentScene.svg.addEventListener('pointerleave', () => highlightSubject(null));
    currentScene.svg.addEventListener('focusout', () => highlightSubject(null));
    bridgesPanel.replaceChildren();
    if (currentScene.bridges.length) {
      bridgesPanel.append(el('h3', {}, 'Ideas that meet'), el('p', {}, 'Each bridge follows a prerequisite between two Primer modules. Select one to trace it and open the connected lessons.'));
      const grid = el('div', { class: 'km-bridge-grid' });
      currentScene.bridges.forEach((bridge, i) => {
        const button = btn({ class: 'km-bridge-trace', 'aria-pressed': 'false', onclick: () => {
          connections.checked = true; sceneHost.classList.remove('km-hide-connections');
          const selected = button.getAttribute('aria-pressed') !== 'true';
          bridgesPanel.querySelectorAll('[aria-pressed]').forEach(item => item.setAttribute('aria-pressed', 'false'));
          selectedBridge = selected ? String(i) : null;
          button.setAttribute('aria-pressed', String(selected));
          currentScene.svg.querySelectorAll('.km-connection').forEach(edge => edge.classList.toggle('km-traced', selected && edge.dataset.connection === String(i)));
          viewport.scrollIntoView({ block: 'nearest' });
        } }, bridge.label);
        grid.append(el('article', { class: 'km-bridge' }, subject ? el('strong', {}, bridge.label) : button,
          el('p', {}, index.subjects.get(bridge.source.domain).name + ' → ' + index.subjects.get(bridge.target.domain).name),
          el('a', { href: mapHref('module', bridge.source.id) }, bridge.source.title), ' → ',
          el('a', { href: mapHref('module', bridge.target.id) }, bridge.target.title)));
      });
      bridgesPanel.append(grid);
    }
    paintIndex();
  }
  function changeStage(value) {
    knowledgeMapStage = value;
    history.replaceState(null, '', mapHref(level || 'world', id || 'all'));
    paint();
  }
  function paintIndex() {
    const terms = search.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    let nodes = subject ? subject.nodes : domain ? domain.subjects.flatMap(s => s.nodes) : [...index.nodesById.values()];
    nodes = nodes.filter(item => item.stage <= knowledgeMapStage && terms.every(term => (item.title + ' ' + (item.goal || '')).toLocaleLowerCase().includes(term)));
    indexBody.replaceChildren(el('p', { role: 'status' }, plural(nodes.length, 'module') + ' through ' + STAGE_NAMES[knowledgeMapStage]));
    if (node) indexBody.append(...moduleMapTerritories(node, detail, subject, index, knowledgeMapStage));
    else indexBody.append(el('div', { class: 'km-grid' }, ...nodes.map(item => moduleMapTile(item, index.subjects.get(item.domain)))));
  }
  paint();
}
