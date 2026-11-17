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
    if (locatedOnly && !structure.atlas && !structure.radiology_assistant) return false;
    return !text || structure.name.toLowerCase().includes(text.trim().toLowerCase());
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

  function draw() {
    const body = $('rows');
    body.replaceChildren();
    if (!current) return;
    const shown = current.structures.filter(structure => Locator.visible(structure, $('filter').value, $('located').checked));
    for (const structure of shown) body.append(el('tr', {}, el('th', { scope: 'row' }, structure.name), atlasCell(structure), sourceCell(structure)));
    const counts = current.counts;
    $('summary').textContent = counts.either + ' of ' + counts.requirements + ' reportable structures have a locator ('
      + counts.atlas + ' in the atlas, ' + counts.radiology_assistant + ' in Radiology Assistant). Showing ' + shown.length + '.';
  }

  async function load(identifier) {
    const row = index.investigations.find(item => item.investigation_id === identifier) || index.investigations[0];
    $('investigation').value = row.investigation_id;
    current = await (await fetch(row.file)).json();
    draw();
  }

  fetch('index.json').then(response => response.json()).then(data => {
    index = data;
    $('policy').textContent = data.policy;
    $('credit').textContent = 'Stanford MSK MRI Atlas: ' + data.sources.atlas.author + ', xrayhead.com. ' + data.sources.atlas.reuse
      + ' Radiology Assistant: ' + data.sources.radiology_assistant.reuse;
    for (const row of data.investigations) {
      $('investigation').append(el('option', { value: row.investigation_id }, row.investigation_id.replace('ra.', '').replace(/-/g, ' ') + ' (' + row.either + '/' + row.requirements + ')'));
    }
    $('investigation').addEventListener('change', event => load(event.target.value));
    $('filter').addEventListener('input', draw);
    $('located').addEventListener('change', draw);
    return load(new URLSearchParams(location.search).get('i'));
  }).catch(() => { $('summary').textContent = 'The locator files could not be loaded.'; });
}

if (typeof module === 'object') module.exports = Locator; else start();
