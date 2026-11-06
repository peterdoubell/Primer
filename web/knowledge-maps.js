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

const mapHref = (...parts) => hashFor('maps', parts.length ? parts : null);

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

function mapPoster(title, subtitle, territories, level) {
  const poster = el('div', { class: 'km-poster km-poster-' + (level || 'world') },
    el('header', { class: 'km-plate' },
      el('div', {}, el('span', { class: 'km-label' }, 'Primer · Knowledge Atlas'),
        el('p', { class: 'km-plate-title' }, title), el('p', {}, subtitle)),
      mapEmblem('N', 'compass')),
    el('div', { class: 'km-territories' }, ...territories),
    el('div', { class: 'km-imprint', 'aria-hidden': 'true' }, 'PRIMER CARTOGRAPHY', '  ◆  ', 'CURRICULUM EDITION'));
  const viewport = el('div', { class: 'km-viewport', tabindex: '0', role: 'region',
    'aria-label': title + ' map canvas', 'aria-describedby': 'km-instructions' }, poster);
  const scale = el('output', { class: 'km-scale', 'aria-live': 'polite' }, '100%');
  const minus = btn({ class: 'btn ghost small', 'aria-label': 'Zoom out', onclick: () => zoomTo(zoom - 25) }, '−');
  const plus = btn({ class: 'btn ghost small', 'aria-label': 'Zoom in', onclick: () => zoomTo(zoom + 25) }, '+');
  let zoom = 100;

  function zoomTo(value) {
    const ratio = value / zoom;
    const left = (viewport.scrollLeft + viewport.clientWidth / 2) * ratio - viewport.clientWidth / 2;
    const top = viewport.scrollTop * ratio;
    if (zoom === 100) poster.style.setProperty('--map-width', viewport.clientWidth + 'px');
    zoom = value;
    poster.style.setProperty('--map-zoom', value / 100);
    if (value === 100) poster.style.removeProperty('--map-width');
    viewport.scrollTo(left, top);
    scale.textContent = value + '%';
    minus.disabled = value <= 50;
    plus.disabled = value >= 200;
  }

  return el('section', { class: 'km-sheet', 'aria-label': 'Interactive map' },
    el('div', { class: 'km-toolbar' },
      el('p', { id: 'km-instructions' }, 'Select a label or illustration to follow it. Scroll to explore the sheet.'),
      el('div', { class: 'km-controls', role: 'group', 'aria-label': 'Map scale' },
        minus, scale, plus, btn({ class: 'btn ghost small', onclick: () => {
          zoomTo(100);
          viewport.scrollTo(0, 0);
        } }, 'Reset view'))),
    viewport);
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

function subjectMapTile(subject) {
  return mapTile({ title: subject.name, href: mapHref('subject', subject.id),
    note: plural(subject.nodes.length, 'module'), mark: subject.icon || '✦',
    detail: subject.tagline, color: subject.color, variant: 'subject' });
}

function moduleMapTile(node, subject, note = learningStage(node.stage).name) {
  return mapTile({ title: node.title, href: mapHref('module', node.id), note,
    mark: subject.icon || '✦', color: subject.color });
}

function subjectMapTerritories(subject) {
  const groups = new Map();
  const ordered = subject.nodes.slice().sort((a, b) => a.stage - b.stage);
  for (const node of ordered) {
    const stage = learningStage(node.stage);
    const title = node.section || (node.strand === 'music' ? 'Music' : stage.name);
    const key = node.section ? 'section:' + node.section : node.strand === 'music' ? 'music' : 'stage:' + node.stage;
    if (!groups.has(key)) groups.set(key, { title, nodes: [] });
    groups.get(key).nodes.push(node);
  }
  const territories = [...groups.values()].map(({ title, nodes }) =>
    mapTerritory(title, plural(nodes.length, 'module'), nodes.map(node => moduleMapTile(node, subject)), subject.color));
  if (subject.connections.size) {
    const connected = [...subject.connections].sort((a, b) => a.name.localeCompare(b.name));
    territories.push(mapTerritory('Connected subjects', 'Linked by module prerequisites', connected.map(subjectMapTile)));
  }
  return territories;
}

function moduleMapTerritories(node, detail, subject, index) {
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
  const prerequisites = (node.prereqs || []).map(id => index.nodesById.get(id)).filter(Boolean);
  if (prerequisites.length) tiles.push(mapTerritory('What this builds on', 'Prerequisite modules', prerequisites.map(relatedTile)));
  const onward = index.onward.get(node.id);
  if (onward?.length) tiles.push(mapTerritory('Where this leads', 'Modules that build on this', onward.map(relatedTile)));
  return tiles;
}

async function renderKnowledgeMaps(page, [level, id] = []) {
  const navigation = _readerContextSeq;
  loading(page);
  let index, domain, subject, node, detail;
  try {
    index = S.knowledgeMapIndex || knowledgeMapIndex(await api.get('/api/curriculum'));
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
  const trail = el('nav', { class: 'km-breadcrumb', 'aria-label': 'Map location' },
    el('a', { href: hashFor('atlas') }, 'The Atlas'));
  if (level) trail.append(el('a', { href: mapHref() }, 'Knowledge maps'));
  if (subject) trail.append(el('a', { href: mapHref('domain', domain.id) }, domain.title));
  if (node) trail.append(el('a', { href: mapHref('subject', subject.id) }, subject.name));
  page.append(trail);

  if (level && !domain) {
    page.append(pagehead('Primer · Knowledge Atlas', 'Map unavailable', 'Choose a domain or subject from the knowledge maps.'));
    return;
  }

  const title = node?.title || subject?.name || domain?.title || 'Knowledge maps';
  const subtitle = node ? subject.name + ' · ' + stageLabel(node.stage)
    : subject ? plural(subject.nodes.length, 'module') + ' across the Primer curriculum'
    : domain ? domain.description
    : plural(index.domains.length, 'domain') + ' · ' + plural(index.subjects.size, 'subject')
      + ' · ' + plural(index.nodesById.size, 'module');
  const kicker = node ? 'Module map' : subject ? 'Subject map' : domain ? 'Domain map' : 'Primer · Knowledge Atlas';
  page.append(pagehead(kicker, title, subtitle));

  let territories;
  if (node) territories = moduleMapTerritories(node, detail, subject, index);
  else if (subject) territories = subjectMapTerritories(subject);
  else if (domain) territories = [mapTerritory('Subjects', plural(domain.subjects.length, 'subject'),
    domain.subjects.map(subjectMapTile), domain.color)];
  else territories = index.domains.map(entry => mapTerritory(entry.title, 'Domain', [
    mapTile({ title: 'Explore ' + entry.title, href: mapHref('domain', entry.id), mark: entry.mark,
      detail: entry.description, color: entry.color, variant: 'domain' }),
    ...entry.subjects.map(subjectMapTile),
  ], entry.color));

  page.append(mapPoster(title, subtitle, territories, level));
  if (!node) page.append(mapReferences(subject ? [subject] : domain?.subjects || []));
}
