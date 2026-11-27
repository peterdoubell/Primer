// Structure source locator: reads the generated locator files and lists, per reportable
// structure, where the named external sources show it. Nothing here claims coverage.
const Locator = {
  planeNames: { ax: 'axial', cor: 'coronal', sag: 'sagittal' },
  // [3,4,5,9] -> "3–5, 9"
  ranges(numbers) {
    const out = [];
    for (let i = 0; i < numbers.length; i += 1) {
      let j = i;
      while (j + 1 < numbers.length && numbers[j + 1] === numbers[j] + 1) j += 1;
      out.push(i === j ? String(numbers[i]) : numbers[i] + '–' + numbers[j]);
      i = j;
    }
    return out.join(', ');
  },
  slices(planes) {
    return ['ax', 'cor', 'sag'].filter(plane => planes[plane])
      .map(plane => Locator.planeNames[plane] + ' ' + Locator.ranges(planes[plane])).join('; ');
  },
  matchNote(match) {
    return { same_name: 'Labelled under this name', reviewed_synonym: 'Labelled under another name',
      named_parts_only: 'Only named parts are labelled' }[match] || '';
  },
  visible(structure, text, locatedOnly) {
    if (locatedOnly && !structure.atlas && !structure.radiology_assistant && !structure.native_examples?.length && !structure.source_panels?.length) return false;
    const words = [structure.name, ...(structure.native_examples || []).map(example =>
      'node ' + example.source_node_id + ' ' + example.primary_station),
      ...(structure.source_panels || []).map(example => example.target_name + ' ' + example.label)].join(' ').toLowerCase();
    return !text || words.includes(text.trim().toLowerCase());
  },
  nativeUrl(value) {
    if (typeof value !== 'string') return null;
    const match = /^\/app\/anatomy\/lynos-pat9\/(?:index|surfaces)\.html\?node=(\d{1,2})$/.exec(value);
    return match && Number(match[1]) >= 1 && Number(match[1]) <= 44 ? value : null;
  },
  panelUrl(value) {
    return typeof value === 'string' && /^\/app\/radiology\/acute-abdomen-panels\/index\.html\?target=acute_abdomen\.[a-z0-9_.]+&panel=[a-z0-9-]+$/.test(value) ? value : null;
  },
  safeUrl(url, prefix) { return typeof url === 'string' && url.startsWith(prefix) ? url : null; },
};

function start() {
  const $ = id => document.getElementById(id);
  const el = (tag, attrs, ...children) => {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs || {})) node.setAttribute(key, value);
    node.append(...children);
    return node;
  };
  let index = null;
  let current = null;

  function atlasCell(structure) {
    const cell = el('td');
    const atlas = structure.atlas;
    if (!atlas) { cell.append(el('span', { class: 'none' }, 'No label found')); return cell; }
    const list = el('ul');
    for (const label of atlas.labels) {
      const planes = (index.atlas_labels[atlas.region] || {})[label] || {};
      list.append(el('li', {}, label, el('small', {}, 'Slices: ' + Locator.slices(planes))));
    }
    const href = index.sources.atlas.page + encodeURIComponent(atlas.region);
    cell.append(el('a', { href, rel: 'noopener noreferrer', target: '_blank' },
      'Open the ' + atlas.region.replace('_', ' ') + ' atlas'), list,
    el('small', {}, Locator.matchNote(atlas.match) + (atlas.in_requirement_modality_scope ? '.' : '. The atlas is MRI; this structure is reported on another modality.')));
    return cell;
  }

  function sourceCell(structure) {
    const cell = el('td');
    const entries = structure.radiology_assistant || [];
    if (!entries.length) { cell.append(el('span', { class: 'none' }, 'Not named in the cited articles')); return cell; }
    const list = el('ul');
    for (const entry of entries) {
      const href = Locator.safeUrl(entry.url, 'https://radiologyassistant.nl/');
      if (!href) continue;
      const item = el('li', {}, el('a', { href, rel: 'noopener noreferrer', target: '_blank' }, entry.heading || 'Section'),
        entry.named_in === 'text' ? ' (named in this section’s text)' : '');
      const figure = Locator.safeUrl(entry.figure, 'https://radiologyassistant.nl/assets/');
      if (figure) {
        item.append(el('img', { src: figure, alt: 'Radiology Assistant figure from the section “' + entry.heading + '”', loading: 'lazy', referrerpolicy: 'no-referrer' }),
          el('small', {}, 'Figure: Radiology Assistant; authors credited in the linked article.'));
      }
      list.append(item);
    }
    cell.append(list);
    return cell;
  }

  function nativeCell(structure) {
    const cell = el('td');
    if (!structure.native_examples?.length) {
      cell.append(el('span', { class: 'none' }, 'No directly matched primary assignment'));
      return cell;
    }
    const list = el('ul');
    for (const example of structure.native_examples) {
      const ct = Locator.nativeUrl(example.ct_url), model = Locator.nativeUrl(example.model_url);
      if (!ct || !model) continue;
      const row = el('li', {},
        el('a', { href: ct }, 'Node ' + example.source_node_id + ' CT'), ' · ',
        el('a', { href: model }, '3D'),
        el('small', {}, example.primary_station));
      if (example.secondary_station) row.append(el('small', {}, 'Secondary: ' + example.secondary_station));
      if (example.tertiary_station) row.append(el('small', {}, 'Tertiary: ' + example.tertiary_station));
      list.append(row);
    }
    cell.append(list);
    return cell;
  }

  function sourceContext() {
    const context = $('native-context');
    context.replaceChildren();
    const source = current.native_source;
    context.hidden = !source;
    $('native-source-heading').hidden = !source;
    if (!source) return;
    const omitted = el('details', {}, el('summary', {}, 'Source assignments excluded from direct station matches'));
    const list = el('ul');
    for (const row of source.omitted_primary_assignments) {
      list.append(el('li', {}, 'Mask ' + row.sourceMaskValue + ': ' + row.primaryStationLiteral + ' (' + row.reason + ').'));
    }
    omitted.append(list);
    context.append(el('h2', {}, 'LyNoS individual node examples'),
      el('p', {}, source.note), omitted,
      el('p', {}, el('a', { href: source.source_url, target: '_blank', rel: 'noopener noreferrer' }, 'Bouget and colleagues · LyNoS Pat9'),
        ' · ', el('a', { href: source.license_url, target: '_blank', rel: 'noopener noreferrer' }, source.license)));
  }

  function panelCell(structure) {
    const cell = el('td'), entries = structure.source_panels || [];
    if (!entries.length) { cell.append(el('span', {class:'none'}, 'No reviewed local source match')); return cell; }
    const list = el('ul');
    for (const entry of entries) {
      const href = Locator.panelUrl(entry.url);
      if (!href) continue;
      list.append(el('li', {}, el('a', {href}, entry.target_name), el('small', {}, entry.label + ' · partial source example')));
    }
    cell.append(list); return cell;
  }

  function draw() {
    const body = $('rows');
    body.replaceChildren();
    if (!current) return;
    const shown = current.structures.filter(structure => Locator.visible(structure, $('filter').value, $('located').checked));
    for (const structure of shown) {
      const row = el('tr', {}, el('th', { scope: 'row' }, structure.name), atlasCell(structure), sourceCell(structure));
      if (current.native_source) row.append(nativeCell(structure));
      if (current.source_panel_rows) row.append(panelCell(structure));
      body.append(row);
    }
    const counts = current.counts;
    const total = current.structures.filter(row => row.atlas || row.radiology_assistant || row.native_examples?.length || row.source_panels?.length).length;
    const native = current.structures.filter(row => row.native_examples?.length).length;
    $('summary').textContent = total + ' of ' + counts.requirements + ' reportable structures have a locator ('
      + counts.atlas + ' in the atlas, ' + counts.radiology_assistant + ' in Radiology Assistant'
      + (native ? ', ' + native + ' with LyNoS node examples' : '')
      + (current.source_panel_rows ? ', ' + current.source_panel_rows + ' with selected local examples' : '') + '). Showing ' + shown.length + '.';
  }

  async function load(identifier) {
    const row = index.investigations.find(item => item.investigation_id === identifier) || index.investigations[0];
    $('investigation').value = row.investigation_id;
    $('return-link').href = '/app/#/radiology/' + encodeURIComponent(row.investigation_id);
    $('return-link').textContent = 'Return to reporting reference';
    current = await (await fetch(row.file)).json();
    sourceContext();
    $('panel-source-heading').hidden = !current.source_panel_rows;
    $('panel-context').hidden = !current.source_panel_rows;
    $('panel-context').textContent = current.source_panel_note || '';
    draw();
  }

  fetch('index.json').then(response => response.json()).then(data => {
    index = data;
    $('policy').textContent = data.policy;
    $('credit').textContent = 'Stanford MSK MRI Atlas: ' + data.sources.atlas.author + ', xrayhead.com. ' + data.sources.atlas.reuse
      + ' Radiology Assistant: ' + data.sources.radiology_assistant.reuse;
    for (const row of data.investigations) {
      $('investigation').append(el('option', { value: row.investigation_id }, row.investigation_id.replace('ra.', '').replace(/-/g, ' ') + ' (' + (row.located_structures ?? row.either) + '/' + row.requirements + ')'));
    }
    $('investigation').addEventListener('change', event => load(event.target.value));
    $('filter').addEventListener('input', draw);
    $('located').addEventListener('change', draw);
    return load(new URLSearchParams(location.search).get('i'));
  }).catch(() => { $('summary').textContent = 'The locator files could not be loaded.'; });
}

if (typeof module === 'object') module.exports = Locator; else start();
