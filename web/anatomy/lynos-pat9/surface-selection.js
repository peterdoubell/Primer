'use strict';

(() => {
  const select = document.getElementById('node');
  const details = document.getElementById('station-details');
  const retry = document.getElementById('retry-stations');
  const ctLink = document.getElementById('return-to-ct');
  const sourcePin = document.querySelector('main').dataset.sourceSha256;
  const url = new URL(location.href);
  const requested = url.searchParams.get('node');
  const labels = Array.from({ length: 44 }, (_, index) => index + 1);
  const initial = requested && /^\d{1,2}$/.test(requested) && labels.includes(Number(requested))
    ? Number(requested) : 7;
  let stations = new Map();

  // The shared renderer associates controls with manifest rows in DOM order.
  // Attach its nodal inputs before the next deferred script starts.
  const nodeLayers = document.getElementById('source-node-layers');
  const controls = labels.map(label => {
    const control = document.createElement('input');
    control.type = 'checkbox';
    control.className = 'layer';
    control.checked = label === initial;
    return control;
  });
  nodeLayers.replaceChildren(...controls);

  function updateCTLink(label) {
    ctLink.href = 'index.html?node=' + label;
  }

  function paragraph(prefix, literal) {
    const line = document.createElement('p');
    const name = document.createElement('strong');
    name.textContent = prefix + ' ';
    const source = document.createElement('code');
    source.textContent = literal;
    line.append(name, source);
    return line;
  }

  function renderSelected() {
    const label = Number(select.value);
    const row = stations.get(label);
    if (!row) return;
    controls.forEach((control, index) => { control.checked = labels[index] === label; });
    controls[label - 1].dispatchEvent(new Event('input'));
    updateCTLink(label);
    url.searchParams.set('node', label);
    history.replaceState(null, '', url);
    const fields = [
      paragraph('Primary station', row.primaryStationLiteral),
      ...(row.secondaryStationLiteral ? [paragraph('Secondary station', row.secondaryStationLiteral)] : []),
      ...(row.tertiaryStationLiteral ? [paragraph('Tertiary station', row.tertiaryStationLiteral)] : []),
    ];
    if (label === 19) {
      const warning = document.createElement('p');
      warning.textContent = 'The source pairs the 11L code with the descriptor Right. Both are shown as supplied.';
      fields.push(warning);
    }
    details.replaceChildren(...fields);
  }

  async function loadStations() {
    retry.hidden = true;
    details.textContent = 'Verifying the authors’ station assignments…';
    try {
      const response = await fetch('source.json');
      if (!response.ok) throw Error('Source metadata unavailable');
      const bytes = await response.arrayBuffer();
      const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
        byte => byte.toString(16).padStart(2, '0')).join('');
      if (digest !== sourcePin) throw Error('Source metadata checksum differs');
      const rows = JSON.parse(new TextDecoder().decode(bytes)).nodalLabels;
      if (!Array.isArray(rows) || rows.length !== labels.length
          || !rows.every((row, index) => row.label === labels[index])) {
        throw Error('Node labels differ');
      }
      stations = new Map(rows.map(row => [row.label, row]));
      const options = rows.map(row => new Option(
        row.name + ' · ' + row.primaryStationLiteral.split(' - ')[0], row.label));
      select.replaceChildren(...options);
      select.value = initial;
      select.disabled = false;
      renderSelected();
    } catch {
      details.textContent = 'The station assignments could not be verified.';
      retry.hidden = false;
    }
  }

  // Hide inactive legend rows while retaining the shared renderer's
  // source colours and draw state for all the selectable surfaces.
  document.addEventListener('DOMContentLoaded', () => {
    const legend = document.querySelector('.region-key');
    if (!legend) return;
    const layers = [...document.querySelectorAll('.layer')];
    const showVisibleKeys = () => {
      [...legend.children].forEach((item, index) => { item.hidden = !layers[index]?.checked; });
    };
    legend.setAttribute('aria-label', 'Visible source regions');
    const observer = new MutationObserver(showVisibleKeys);
    observer.observe(legend, { childList: true });
    showVisibleKeys();
  }, { once: true });

  updateCTLink(initial);
  select.addEventListener('change', renderSelected);
  retry.addEventListener('click', loadStations);
  loadStations();
})();
