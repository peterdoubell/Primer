/* Source-backed observations are selected explicitly; no findings are defaults. */
window.PrimerStructuredReporting = (() => {
  const clone = value => JSON.parse(JSON.stringify(value));
  const own = (value, key) => Object.prototype.hasOwnProperty.call(value || {}, key);
  const dictionary = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const present = value => value !== undefined && value !== null && value !== '';
  const title = value => String(value).replaceAll('_', ' ').replace(/^./, character => character.toUpperCase());
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const button = (text, action, className = 'rad-choice') => {
    const node = element('button', text, className);
    node.type = 'button';
    node.onclick = action;
    return node;
  };
  const choose = (node, active) => node.setAttribute('aria-pressed', String(Boolean(active)));
  const descriptorForm = form => form.descriptor_form || form;
  const contextValue = (context, descriptor, slot) => {
    if (slot.context_key && own(context, slot.context_key)) return context[slot.context_key];
    if (own(context, descriptor.id + '.' + slot.id)) return context[descriptor.id + '.' + slot.id];
    return context?.[descriptor.id]?.[slot.id];
  };
  const validValue = (slot, value) => {
    if (!present(value)) return false;
    if (slot.kind === 'choice') return (slot.options || []).some(option => option.value === value);
    if (slot.kind === 'number') return typeof value === 'number' && Number.isFinite(value) &&
      (slot.minimum === undefined || value >= slot.minimum) && (slot.maximum === undefined || value <= slot.maximum);
    return typeof value === 'string' && value.trim().length > 0 && value.length <= 4000 && !/[\x00-\x1f\x7f\[\]]|_{2,}|\b(?:TODO|TBD)\b/i.test(value);
  };
  function descriptorText(descriptor, values = {}, context = {}) {
    if (!dictionary(values)) return {text: '', missing: [{descriptor_id: descriptor.id, label: 'Invalid finding details'}]};
    const resolved = {}, missing = [];
    for (const key of Object.keys(values)) if (!(descriptor.slots || []).some(slot => slot.id === key)) missing.push({descriptor_id: descriptor.id, slot_id: key, label: 'Unrecognised detail'});
    for (const slot of descriptor.slots || []) {
      const supplied = contextValue(context, descriptor, slot);
      const value = present(supplied) ? supplied : values[slot.id];
      if (!validValue(slot, value)) {
        if (slot.required !== false) missing.push({descriptor_id: descriptor.id, slot_id: slot.id, label: slot.label || descriptor.label});
      } else resolved[slot.id] = slot.kind === 'context' ? value.trim() : value;
    }
    if (missing.length) return {text: '', missing};
    const text = (descriptor.segments || [{text: descriptor.text || ''}]).map(segment => own(segment, 'slot') ? (resolved[segment.slot] ?? '') : segment.text || '').join('');
    return {text: text.trim(), missing};
  }
  function findingActive(finding, chosen, section, chain = new Set()) {
    if (chain.has(finding.id)) return false;
    return !(finding.requires_any || []).length || finding.requires_any.some(id => {
      const parent = section.findings.find(item => item.id === id);
      return own(chosen, id) && parent && findingActive(parent, chosen, section, new Set([...chain, finding.id]));
    });
  }
  function blockedNormals(investigation, selections) {
    const blocked = new Set();
    for (const section of investigation?.sections || []) {
      const chosen = selections?.[section.id]?.findings || {};
      for (const finding of section.findings) if (own(chosen, finding.id) && findingActive(finding, chosen, section)) {
        for (const id of finding.invalidates_normal || []) blocked.add(id);
      }
    }
    return blocked;
  }
  function compose(form, state = {}, context = {}) {
    const schema = descriptorForm(form);
    const investigation = (schema.investigations || []).find(item => item.id === state.investigation_id);
    if (!investigation) return {text: '', missing: [], complete: false, selected_count: 0};
    if (own(state, 'selections') && !dictionary(state.selections)) return {text: '', missing: [{label: 'Invalid report selections'}], complete: false, selected_count: 0};
    const grouped = new Map(), missing = [], blocked = blockedNormals(investigation, state.selections);
    for (const key of Object.keys(state.selections || {})) if (!(investigation.sections || []).some(section => section.id === key)) missing.push({section_id: key, label: 'Unrecognised section'});
    let selectedCount = 0;
    for (const section of investigation.sections || []) {
      const selected = state.selections?.[section.id] ?? {}, lines = [];
      if ((own(state.selections, section.id) && !dictionary(state.selections[section.id])) || (own(selected, 'findings') && !dictionary(selected.findings))) { missing.push({section_id: section.id, label: 'Invalid selections for ' + section.label}); continue; }
      if (Object.keys(selected).some(key => !['normal', 'not_assessed', 'findings'].includes(key)) || ['normal', 'not_assessed'].some(key => own(selected, key) && typeof selected[key] !== 'boolean') || [Boolean(selected.normal), Boolean(selected.not_assessed), Object.keys(selected.findings || {}).length > 0].filter(Boolean).length > 1 || (selected.normal && !section.normal)) {
        missing.push({section_id: section.id, label: 'Review conflicting selections for ' + section.label}); continue;
      }
      for (const key of Object.keys(selected.findings || {})) if (!(section.findings || []).some(finding => finding.id === key)) missing.push({section_id: section.id, finding_id: key, label: 'Unrecognised finding'});
      if (selected.normal && blocked.has(section.id)) { missing.push({section_id:section.id,label:"Normal conflicts with a related finding: " + section.label}); continue; }
      if (selected.normal && section.normal) {
        const result = descriptorText(section.normal, {}, context);
        lines.push(result.text); missing.push(...result.missing); selectedCount++;
      } else if (selected.not_assessed) {
        lines.push(section.label + ': not assessed.'); selectedCount++;
      } else {
        const exclusive = new Set();
        for (const finding of section.findings || []) {
          if (!own(selected.findings, finding.id)) continue;
          if (!findingActive(finding, selected.findings, section)) { missing.push({label:'Inactive detail: ' + finding.label}); continue; }
          if (finding.exclusive_group) { if (exclusive.has(finding.exclusive_group)) missing.push({label:'Conflicting findings: ' + section.label}); exclusive.add(finding.exclusive_group); }
          const result = descriptorText(finding, selected.findings[finding.id], context);
          lines.push(result.text); missing.push(...result.missing); selectedCount++;
        }
      }
      const linesWithText = lines.filter(Boolean);
      if (linesWithText.length) {
        const key = section.report_section_id || section.id;
        if (!grouped.has(key)) grouped.set(key, {label: section.report_section_label || section.label, lines: []});
        const group = grouped.get(key);
        for (const line of linesWithText) if (!group.lines.includes(line)) group.lines.push(line);
      }
    }
    return {text: [...grouped.values()].map(group => group.label + '\n' + group.lines.join('\n')).join('\n\n'), missing, complete: selectedCount > 0 && missing.length === 0, selected_count: selectedCount};
  }
  function selectControl(label, options, value, change) {
    const control = element('select');
    control.setAttribute('aria-label', label);
    const empty = element('option', 'Select…'); empty.value = ''; control.append(empty);
    options.forEach(item => { const option = element('option', item.label); option.value = String(item.value); control.append(option); });
    control.value = present(value) ? String(value) : '';
    control.onchange = () => change(control.value === '' ? undefined : options.find(item => String(item.value) === control.value)?.value);
    return control;
  }
  /* Exact values are selected, never inferred from an unreviewed zero. Common values
     take one menu; the digit picker permits values beyond that menu without typing. */
  function numberControl(label, value, schema, change) {
    const wrapper = element('div', undefined, 'rad-number-picker');
    const min = schema.minimum ?? (schema.exclusiveMinimum !== undefined ? schema.exclusiveMinimum : -Infinity);
    const max = schema.maximum;
    const integer = schema.type === 'integer';
    const unit = schema.unit || '';
    const step = !integer && /cm|ng\/ml/i.test(unit) ? .1 : 1;
    const commonMax = Math.min(max ?? (step === .1 ? 15 : 100), step === .1 ? 15 : 100);
    const acceptable = n => Number.isFinite(n) && n >= min && (max === undefined || n <= max) &&
      (schema.exclusiveMinimum === undefined || n > schema.exclusiveMinimum) &&
      (schema.exclusiveMaximum === undefined || n < schema.exclusiveMaximum) && (!integer || Number.isInteger(n));
    const values = [];
    for (let n = Math.max(0, min); n <= commonMax + step / 2; n += step) {
      const candidate = Number(n.toFixed(3));
      if (acceptable(candidate)) values.push(candidate);
    }
    if (present(value) && acceptable(value) && !values.includes(value)) values.push(value);
    values.sort((a, b) => a - b);
    const picker = selectControl(label, [...values.map(n => ({value: n, label: String(n) + (unit ? ' ' + unit : '')})), {value: 'exact', label: 'Exact value…'}], value, selected => {
      if (selected === 'exact') { exact.hidden = false; return; }
      exact.hidden = true; change(selected);
    });
    const exact = element('div', undefined, 'rad-number-exact'); exact.hidden = true;
    const readout = element('span', 'Select each digit', 'rad-number-value');
    const digits = element('div', undefined, 'rad-number-digits');
    let whole = [null], fraction = [], negative = false;
    if (present(value)) {
      const parts = Math.abs(value).toString().split('.');
      whole = parts[0].split('').map(Number); fraction = (parts[1] || '').split('').map(Number); negative = value < 0;
    }
    const emit = () => {
      if (whole.some(v => v === null) || fraction.some(v => v === null)) { readout.textContent = 'Select each digit'; change(undefined); return; }
      const number = Number((negative ? '-' : '') + whole.join('') + (fraction.length ? '.' + fraction.join('') : ''));
      readout.textContent = String(number) + (unit ? ' ' + unit : '');
      if (!acceptable(number)) { readout.textContent += ' — outside permitted range'; change(undefined); return; }
      change(number);
    };
    const drawDigits = () => {
      digits.replaceChildren();
      if (min < 0) digits.append(selectControl(label + ' sign', [{value: false, label: '+'}, {value: true, label: '−'}], negative, value => { negative = value === true; emit(); }));
      const digit = (list, index, part) => selectControl(label + ' ' + part + ' digit ' + (index + 1), Array.from({length: 10}, (_, n) => ({value: n, label: String(n)})), list[index], value => { list[index] = value ?? null; emit(); });
      whole.forEach((_, i) => digits.append(digit(whole, i, 'whole')));
      if (fraction.length) digits.append(element('span', '.', 'rad-decimal-point'));
      fraction.forEach((_, i) => digits.append(digit(fraction, i, 'decimal')));
    };
    exact.append(digits, readout, button('+ whole digit', () => { whole.unshift(null); drawDigits(); emit(); }, 'rad-small-button'));
    if (!integer) exact.append(button('+ decimal digit', () => { fraction.push(null); drawDigits(); emit(); }, 'rad-small-button'));
    exact.append(button('Clear value', () => { whole = [null]; fraction = []; picker.value = ''; exact.hidden = true; change(undefined); }, 'rad-small-button'));
    drawDigits(); wrapper.append(picker, exact); return wrapper;
  }
  async function request(path, data) {
    const response = await fetch('/api/radiology/reporting/' + path, {method: data === undefined ? 'GET' : 'POST', headers: {'Content-Type': 'application/json'}, ...(data === undefined ? {} : {body: JSON.stringify(data)})});
    const payload = await response.json();
    if (!response.ok) throw Error(payload.error?.message || payload.error?.code || 'Reporting service unavailable');
    return payload;
  }
  function render(form, options = {}) {
    const schema = descriptorForm(form), root = element('section', undefined, 'rad-structured rad-descriptor-sheet');
    let context = clone(options.contextValues || {}), state = clone(options.initialState || {}), copying = false;
    if (state.descriptor_state) state = {...state, ...state.descriptor_state};
    if (!state.calculator_inputs && Array.isArray(state.calculations)) state.calculator_inputs = Object.fromEntries(state.calculations.map(item => [item.calculator_id, item.inputs]));
    state = {schema_version: '1.0', investigation_id: options.investigationId || state.investigation_id || schema.selected_investigation_id || form.selected_investigation_id || (schema.investigations?.length === 1 ? schema.investigations[0].id : ''), selections: state.selections || {}, calculator_inputs: state.calculator_inputs || {}};
    const allowedCalculators = new Set(form.calculator_ids || schema.calculator_ids || []);
    for (const id of Object.keys(state.calculator_inputs)) if (!allowedCalculators.has(id)) delete state.calculator_inputs[id];
    const calculations = new Map(), calculatorControllers = new Map(), pending = new Set();
    const heading = element('div', undefined, 'rad-sheet-heading'), actions = element('div', undefined, 'rad-sheet-actions');
    const normal = button('Use normal findings', () => {
      fillNormal();
      drawSections(); update(true);
    }, 'rad-small-button');
    const clear = button('Clear', () => { state.selections = {}; state.calculator_inputs = {}; calculations.clear(); drawSections(); drawCalculators(); update(true); }, 'rad-small-button');
    actions.append(normal, clear); heading.append(element('h3', 'Report findings'), actions); root.append(heading);
    normal.title = 'Fill unselected structures only; retain existing findings.';
    const groupNavigation = element('nav', undefined, 'rad-group-navigation'); groupNavigation.setAttribute('aria-label', 'Anatomical groups'); root.append(groupNavigation);
    const investigationPicker = element('div', undefined, 'rad-investigation-picker');
    if (!options.investigationId && (schema.investigations || []).length > 1) {
      investigationPicker.setAttribute('role', 'group'); investigationPicker.setAttribute('aria-label', 'Examination');
      for (const item of schema.investigations) {
        const choice = button(item.title, () => { if (state.investigation_id === item.id) return; state.investigation_id = item.id; state.selections = {}; state.calculator_inputs = {}; calculations.clear(); drawSections(); drawCalculators(); update(true); });
        choice.dataset.investigationId = item.id; investigationPicker.append(choice);
      }
      root.append(investigationPicker);
    }
    const sheet = element('div', undefined, 'rad-report-sheet'), fields = element('div', undefined, 'rad-report-fields'), descriptorFields = element('div'), calculatorFields = element('div');
    const draft = element('aside', undefined, 'rad-report-preview'), preview = element('pre', '', 'rad-report-text'), feedback = element('p', '', 'rad-report-feedback');
    feedback.setAttribute('role', 'status'); preview.setAttribute('aria-label', 'Report draft');
    const copy = button('Copy report', async () => {
      if (copying) return;
      copying = true; update();
      try {
        await root.flush(); const report = reportResult();
        if (!report.complete) throw Error('Complete the selected findings before copying.');
        if (options.onCopy) await options.onCopy(root.getState(), report.text);
        else await navigator.clipboard.writeText(report.text);
        feedback.textContent = 'Report copied.';
      } catch (error) { feedback.textContent = error.message || 'Copy unavailable. Select the report text to copy it.'; }
      finally { copying = false; copy.disabled = !reportResult().complete; }
    }, 'btn rad-copy-report');
    actions.append(copy); draft.append(element('h4', 'Report draft'), preview, feedback); fields.append(descriptorFields, calculatorFields); sheet.append(fields, draft); root.append(sheet);
    const investigation = () => (schema.investigations || []).find(item => item.id === state.investigation_id);
    const selected = section => state.selections[section.id] || {normal: false, not_assessed: false, findings: {}};
    function fillNormal(group) {
      const blocked = blockedNormals(investigation(), state.selections);
      for (const section of investigation()?.sections || []) {
        const value = selected(section);
        if (section.normal && !section.exclude_from_bulk_normal && (!group || section.group === group) && !blocked.has(section.id) && !value.normal && !value.not_assessed && !Object.keys(value.findings || {}).length) state.selections[section.id] = {normal:true,findings:{}};
      }
    }
    const changeSection = (section, value) => {
      let changed;
      do { changed = false; for (const finding of section.findings) if (own(value.findings, finding.id) && !findingActive(finding, value.findings, section)) {delete value.findings[finding.id];changed=true;} } while (changed);
      state.selections[section.id] = value;
      for (const id of blockedNormals(investigation(), state.selections)) if (state.selections[id]?.normal) delete state.selections[id];
      drawSections(); update(true);
    };
    function drawSlots(descriptor, values, target) {
      if (!dictionary(values)) { target.append(element('p', 'Clear this finding and select its details again.', 'rad-missing-detail')); return; }
      if (!(descriptor.slots || []).length) return;
      const slots = element('div', undefined, 'rad-followups');
      for (const slot of descriptor.slots) {
        const row = element('div', undefined, 'rad-followup'); row.append(element('span', slot.label || 'Detail', 'rad-field-label'));
        const supplied = contextValue(context, descriptor, slot), value = present(supplied) ? supplied : values[slot.id];
        const change = next => {
          if (slot.context_key) delete context[slot.context_key];
          delete context[descriptor.id + '.' + slot.id];
          if (context[descriptor.id]) delete context[descriptor.id][slot.id];
          if (next === undefined) delete values[slot.id]; else values[slot.id] = next; update(true);
        };
        if (slot.kind === 'choice') {
          const choices = element('div', undefined, 'rad-choices'); choices.setAttribute('role', 'group'); choices.setAttribute('aria-label', slot.label || 'Detail');
          for (const item of slot.options || []) {
            const choice = button(item.label, () => { change(value === item.value ? undefined : item.value); drawSections(); }); choice.dataset.radFocus = 'slot:' + descriptor.id + ':' + slot.id + ':' + item.value; choose(choice, value === item.value); choices.append(choice);
          }
          row.append(choices);
        } else if (slot.kind === 'number') row.append(numberControl(slot.label || 'Measurement', value, slot, change));
        else row.append(element('span', present(value) ? String(value) : 'Awaiting linked ' + (slot.label || 'detail').toLowerCase(), present(value) ? 'rad-linked-value' : 'rad-missing-detail'));
        slots.append(row);
      }
      target.append(slots);
    }
    function drawSections() {
      const focusKey = document.activeElement?.dataset?.radFocus;
      descriptorFields.replaceChildren(); groupNavigation.replaceChildren();
      const exam = investigation();
      if (!exam) { descriptorFields.append(element('p', 'Choose the examination above.')); return; }
      const blocked = blockedNormals(exam, state.selections); let lastGroup = null;
      root.classList?.toggle('rad-anatomic-sheet', exam.presentation === 'anatomic_rows');
      for (const section of exam.sections || []) {
        if (section.group && section.group !== lastGroup) {
          lastGroup = section.group;
          const groupHeader = element('div', undefined, 'rad-anatomic-group');
          groupHeader.append(element('h4', section.group), button('Normal remaining', () => {fillNormal(section.group);drawSections();update(true);}, 'rad-small-button'));
          descriptorFields.append(groupHeader);
          groupNavigation.append(button(section.group, () => groupHeader.scrollIntoView?.({behavior:'smooth',block:'start'}), 'rad-small-button'));
        }
        const panel = element('section', undefined, 'rad-report-section'), sectionState = selected(section);
        panel.dataset.sectionId = section.id;
        const row = element('div', undefined, 'rad-section-heading'); row.append(element(section.group ? 'h5' : 'h4', section.label));
        const quick = element('div', undefined, 'rad-choices');
        if (section.normal) {
          const normalChoice = button('Normal', () => changeSection(section, {normal: !sectionState.normal, not_assessed: false, findings: {}}));
          normalChoice.disabled = blocked.has(section.id); if (normalChoice.disabled) normalChoice.title = 'A selected related finding excludes this normal statement.'; normalChoice.dataset.radFocus = 'normal:' + section.id; choose(normalChoice, sectionState.normal); quick.append(normalChoice);
        }
        const unassessed = button('Not assessed', () => changeSection(section, {normal: false, not_assessed: !sectionState.not_assessed, findings: {}}));
        unassessed.dataset.radFocus = 'unassessed:' + section.id; choose(unassessed, sectionState.not_assessed); quick.append(unassessed); row.append(quick); panel.append(row);
        const choices = element('div', undefined, 'rad-finding-choices');
        for (const finding of section.findings || []) {
          if (!findingActive(finding, sectionState.findings, section)) continue;
          const active = own(sectionState.findings, finding.id), item = element('div', undefined, 'rad-finding');
          const choice = button(finding.label || finding.text, () => {
            const next = {normal: false, not_assessed: false, findings: {...sectionState.findings}};
            if (active) delete next.findings[finding.id];
            else {
              if (finding.exclusive_group) for (const peer of section.findings || []) if (peer.exclusive_group === finding.exclusive_group) delete next.findings[peer.id];
              next.findings[finding.id] = {};
            }
            changeSection(section, next);
          });
          choice.dataset.radFocus = 'finding:' + finding.id; choose(choice, active); item.append(choice); if (active) drawSlots(finding, sectionState.findings[finding.id], item); choices.append(item);
        }
        panel.append(choices); descriptorFields.append(panel);
      }
      if (focusKey) [...(descriptorFields.querySelectorAll?.('[data-rad-focus]') || [])].find(node => node.dataset.radFocus === focusKey)?.focus();
    }
    function reportResult() {
      const result = compose(schema, state, context);
      const completeCalculations = [...allowedCalculators].map(id => calculations.get(id)).filter(value => value?.status === 'complete');
      const parts = [result.text, ...completeCalculations.map(value => 'CALCULATED ASSESSMENT\n' + (value.summary || value.category || '') + (value.version ? ' (' + value.version + ')' : ''))].filter(Boolean);
      const incompleteCalculators = [...allowedCalculators].filter(id => Object.values(state.calculator_inputs[id] || {}).some(present) && calculations.get(id)?.status !== 'complete');
      const missing = [...result.missing, ...incompleteCalculators.map(id => ({calculator_id: id, label: title(id)}))];
      return {...result, missing, text: parts.join('\n\n'), complete: missing.length === 0 && (result.selected_count > 0 || completeCalculations.length > 0)};
    }
    function update(notify = false) {
      for (const node of investigationPicker.children) choose(node, node.dataset.investigationId === state.investigation_id);
      normal.disabled = !(investigation()?.sections || []).some(section => section.normal);
      const result = reportResult();
      preview.textContent = result.text || 'Select findings to build the report.';
      copy.disabled = copying || !result.complete;
      const remaining = (investigation()?.sections || []).filter(section => { const value = selected(section); return !value.normal && !value.not_assessed && !Object.keys(value.findings || {}).length; }).length;
      feedback.textContent = result.missing.length ? 'Choose remaining details: ' + result.missing.map(item => item.label).join(', ') : remaining ? remaining + ' unselected ' + (remaining === 1 ? 'section' : 'sections') + ' — omitted from report.' : '';
      if (notify && options.onChange) options.onChange(root.getState());
    }
    function track(promise) { pending.add(promise); promise.finally(() => pending.delete(promise)); return promise; }
    function drawCalculators() {
      for (const controller of calculatorControllers.values()) controller.dispose();
      calculatorControllers.clear(); calculatorFields.replaceChildren();
      if (!investigation()) return;
      for (const id of allowedCalculators) {
        const inputs = state.calculator_inputs[id] ||= {};
        const linked = options.calculatorInputs?.[id] || context.calculator_inputs?.[id];
        if (linked) Object.assign(inputs, linked);
        const controller = calculator(id, inputs, options.request || request, (result, changed) => {
          if (result) calculations.set(id, result); else calculations.delete(id);
          update(changed);
        }, track);
        calculatorControllers.set(id, controller); calculatorFields.append(controller.node);
      }
    }
    root.getState = () => {
      const snapshot = clone(state);
      for (const section of investigation()?.sections || []) for (const finding of section.findings || []) {
        const values = snapshot.selections[section.id]?.findings?.[finding.id];
        if (!values) continue;
        for (const slot of finding.slots || []) { const value = contextValue(context, finding, slot); if (present(value)) values[slot.id] = value; }
      }
      return {...snapshot, descriptor_version: form.descriptor_version || schema.version || schema.schema_hash, descriptor_state: {investigation_id: snapshot.investigation_id, selections: snapshot.selections}, calculations: Object.entries(snapshot.calculator_inputs).filter(([, inputs]) => Object.values(inputs).some(present)).map(([calculator_id, inputs]) => ({calculator_id, inputs}))};
    };
    root.getReport = () => reportResult().text;
    root.getReportResult = () => clone(reportResult());
    root.flush = async () => { while (pending.size) await Promise.all([...pending]); return root.getReportResult(); };
    root.updateContext = values => { context = clone(values || {}); calculations.clear(); drawSections(); drawCalculators(); update(true); };
    root.dispose = () => { for (const controller of calculatorControllers.values()) controller.dispose(); };
    drawSections(); drawCalculators(); update(); return root;
  }
  function calculator(id, inputs, send, onResult, track) {
    const panel = element('section', undefined, 'rad-structured-calculator'), heading = element('h4', 'Calculation'), controls = element('div'), result = element('p', 'Loading calculation…', 'rad-calculation-result');
    const bar = element('div', undefined, 'rad-section-heading');
    bar.append(heading, button('Clear calculation', () => { for (const key of Object.keys(inputs)) delete inputs[key]; if (schema) { draw(); run(true); } }, 'rad-small-button'));
    panel.append(bar, controls, result);
    let sequence = 0, disposed = false, inFlight = false, definitions;
    const resolve = property => property?.$ref ? resolve(definitions[property.$ref.split('/').pop()]) : property?.anyOf ? resolve(property.anyOf.find(candidate => candidate.type !== 'null')) : property;
    const visible = key => {
      if (id === 'acr_tirads_2017' && inputs.adult_applicability_confirmed === false) return key === 'adult_applicability_confirmed';
      if (id === 'pirads_v2_1' && inputs.treatment_naive === false) return key === 'treatment_naive';
      if (id === 'acr_tirads_2017' && ['cystic_or_almost_cystic', 'spongiform'].includes(inputs.composition) && ['echogenicity', 'shape', 'margin', 'echogenic_foci'].includes(key)) return false;
      if (id === 'pirads_v2_1') {
        if (key === 't2_score') return inputs.t2_adequate === true;
        if (key === 'dwi_score') return inputs.dwi_adequate === true;
        if (key === 'dce') return inputs.dwi_adequate === false || (inputs.zone === 'PZ' && inputs.dwi_score === 3);
      }
      if (id === 'cadrads_2_0' && key === 'plaque_burden' && inputs.plaque_present === false) return false;
      if (id === 'cadrads_2_0' && key === 'bypassed_segments_excluded') return inputs.grafts_present === true;
      return true;
    };
    let schema, config;
    const run = (changed = false) => {
      const generation = ++sequence; inFlight = true; onResult(null, changed); result.textContent = 'Calculating…';
      const payload = clone(inputs);
      track((async () => {
        try {
          const response = await send('calculators/' + id + '/calculate', {inputs: payload});
          if (disposed || generation !== sequence) return;
          inFlight = false;
          result.textContent = response.status === 'complete' ? (response.summary || response.category) : response.status === 'not_applicable' ? 'Not applicable to these selections.' : 'Select remaining calculation descriptors.';
          result.title = (response.limitations || []).join('\n'); onResult(response, false);
        } catch (error) { if (!disposed && generation === sequence) { inFlight = false; result.textContent = error.message || 'Calculation unavailable'; onResult(null, false); } }
      })());
    };
    const change = (key, value, redraw = true) => {
      if (value === undefined) delete inputs[key]; else inputs[key] = value;
      for (const other of Object.keys(schema.properties || {})) if (!visible(other)) delete inputs[other];
      if (redraw) draw(); run(true);
    };
    const draw = () => {
      controls.replaceChildren();
      for (const [key, raw] of Object.entries(schema.properties || {})) {
        if (!visible(key)) continue;
        const property = resolve(raw), name = raw.title || title(key), row = element('div', undefined, 'rad-calculation-field');
        row.append(element('span', name, 'rad-field-label'));
        const enumValues = property.type === 'array' ? resolve(property.items)?.enum : property.enum || (property.type === 'boolean' ? [true, false] : property.type === 'integer' && property.minimum !== undefined && property.maximum - property.minimum <= 10 ? Array.from({length: property.maximum - property.minimum + 1}, (_, i) => property.minimum + i) : null);
        if (enumValues) {
          const choices = element('div', undefined, 'rad-choices'); choices.setAttribute('role', 'group'); choices.setAttribute('aria-label', name);
          for (const value of enumValues) {
            const choice = button(typeof value === 'boolean' ? value ? 'Yes' : 'No' : title(value), () => {
              if (property.type !== 'array') { change(key, inputs[key] === value ? undefined : value); return; }
              let next = Array.isArray(inputs[key]) ? [...inputs[key]] : [];
              next = next.includes(value) ? next.filter(item => item !== value) : [...next, value];
              if (value === 'none' && next.includes(value)) next = ['none']; else if (value !== 'none') next = next.filter(item => item !== 'none');
              if (key === 'modifiers' && String(value).startsWith('I') && next.includes(value)) next = next.filter(item => !String(item).startsWith('I') || item === value);
              change(key, next.length ? next : undefined);
            }); choose(choice, property.type === 'array' ? (inputs[key] || []).includes(value) : inputs[key] === value); choices.append(choice);
          }
          row.append(choices);
        } else if (['integer', 'number'].includes(property.type)) {
          const unit = key.endsWith('_cm') ? 'cm' : key.endsWith('_mm') ? 'mm' : key.endsWith('_pct') ? '%' : key === 'psa_ng_ml' ? 'ng/ml' : '';
          row.append(numberControl(name, inputs[key], {...property, unit}, value => change(key, value, false)));
        } else row.append(element('span', present(inputs[key]) ? String(inputs[key]) : 'Awaiting linked value', 'rad-linked-value'));
        if (raw.description) row.title = raw.description; controls.append(row);
      }
    };
    track((async () => {
      try {
        config = await send('calculators/' + id);
        if (disposed) return;
        schema = config.input_schema; definitions = schema.$defs || {};
        heading.textContent = config.title + (config.version ? ' · ' + config.version : '');
        draw();
        if ((config.sources || []).length) {
          const references = element('details', undefined, 'rad-calculation-references'); references.append(element('summary', 'References'));
          for (const source of config.sources) {
            if (!/^https?:\/\//.test(source.url || '')) continue;
            const link = element('a', source.title); link.href = source.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; references.append(link);
          }
          panel.append(references);
        }
        run();
      } catch (error) { if (!disposed) { result.textContent = error.message || 'Calculation unavailable'; inFlight = false; onResult(null, false); } }
    })());
    return {node: panel, busy: () => inFlight, dispose: () => { disposed = true; sequence++; }};
  }
  return {render, compose, descriptorText};
})();
