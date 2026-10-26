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
  const MAX_REPEAT_INSTANCES = 50;
  function expandRepeated(investigation, selections = {}) {
    const sections = [], values = {...selections}, missing = [];
    for (const section of investigation?.sections || []) {
      sections.push(section);
      const selected = selections[section.id];
      if (!dictionary(selected) || !own(selected, 'instances')) continue;
      const instances = selected.instances;
      if (!section.repeatable || !Array.isArray(instances) || instances.length > MAX_REPEAT_INSTANCES ||
          Object.keys(selected).some(key => !['normal','not_assessed','findings','instances'].includes(key)) ||
          (own(selected,'findings') && !dictionary(selected.findings)) || ['normal','not_assessed'].some(key => own(selected,key) && typeof selected[key] !== 'boolean') ||
          selected.normal || selected.not_assessed || Object.keys(selected.findings || {}).length) {
        missing.push({section_id:section.id,label:'Invalid entries for ' + section.label}); values[section.id] = {}; continue;
      }
      values[section.id] = {};
      instances.forEach((instance,index) => {
        const id = section.id + '@' + (index+1), label = (section.repeat_label || section.label) + ' ' + (index+1);
        sections.push({...section,id,label,normal:null,repeat_instance_label:label}); values[id] = instance;
        if (dictionary(instance) && !instance.not_assessed && !Object.keys(instance.findings || {}).length)
          missing.push({section_id:section.id,label:'Complete or remove ' + label});
      });
    }
    return {investigation:{...investigation,sections},selections:values,missing};
  }
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
    const expanded = expandRepeated(investigation, selections || {});
    investigation = expanded.investigation; selections = expanded.selections;
    const blocked = new Set();
    for (const section of investigation?.sections || []) {
      const chosen = selections?.[section.id]?.findings || {};
      for (const finding of section.findings) if (own(chosen, finding.id) && findingActive(finding, chosen, section)) {
        for (const id of finding.invalidates_normal || []) blocked.add(id);
      }
    }
    return blocked;
  }
  function descriptorCalculationJobs(form, state = {}) {
    const exam=(descriptorForm(form).investigations || []).find(item=>item.id===state.investigation_id), selections=state.selections || {}, jobs=[];
    if(!exam || !dictionary(selections)) return jobs;
    for(const section of exam.sections || []) {
      const selected=selections[section.id] || {};
      if(!dictionary(selected) || selected.normal || selected.not_assessed) continue;
      const records=own(selected,'instances') ? (section.repeatable && Array.isArray(selected.instances) ? selected.instances.map((record,index)=>({record,index})) : []) : [{record:selected,index:null}];
      for(const {record,index} of records) {
        if(!dictionary(record) || record.normal || record.not_assessed || !dictionary(record.findings || {})) continue;
        for(const spec of section.calculations || []) {
          if(!spec.trigger_any.some(id=>own(record.findings,id))) continue;
          const label=index===null ? section.label : (section.repeat_label || section.label)+' '+(index+1);
          const job={calculator_id:spec.calculator_id,label:spec.label || spec.calculator_id,binding_id:section.id+':'+(index===null?'single':index+1)+':'+spec.calculator_id,context_label:label,section_id:section.id,instance_index:index,instance_label:index===null?null:label,inputs:{}};
          const issues=[];
          for(const [name,rule] of Object.entries(spec.inputs || {})) {
            const values=[];let missing=false,failed=false;
            for(const source of rule.sources || []) {
              const target=source.section_id ? selections[source.section_id] : record;
              if(!dictionary(target) || target.normal || target.not_assessed || target.instances?.length || !dictionary(target.findings || {})) {missing=true;continue;}
              const payload=target.findings?.[source.finding_id];
              if(!dictionary(payload)) {missing=true;continue;}
              let value=source.slot_id ? payload[source.slot_id] : source.value;
              if(!present(value)) {missing=true;continue;}
              if(source.map) {
                const key=typeof value==='string'||typeof value==='boolean'||(typeof value==='number'&&Number.isFinite(value)) ? String(value) : null;
                if(key===null || !own(source.map,key)) {failed=true;issues.push({code:'unmapped_calculation_input',input:name,finding_id:source.finding_id});continue;}
                value=source.map[key];
              }
              values.push(clone(value));
            }
            if(failed || (rule.all_required && missing) || !values.length) continue;
            let value;
            if((rule.aggregate || 'first')==='max') {
              if(values.some(item=>typeof item!=='number'||!Number.isFinite(item))) {issues.push({code:'invalid_calculation_aggregate',input:name});continue;}
              value=Math.max(...values);
            } else if((rule.aggregate || 'first')==='first') {
              if(values.some(item=>JSON.stringify(item)!==JSON.stringify(values[0]))) {issues.push({code:'conflicting_calculation_inputs',input:name});continue;}
              value=values[0];
            } else {issues.push({code:'unsupported_calculation_aggregate',input:name});continue;}
            if(own(rule,'scale')) {
              if(typeof value!=='number'||!Number.isFinite(value)||typeof rule.scale!=='number'||!Number.isFinite(rule.scale)||!Number.isFinite(value*rule.scale)) {issues.push({code:'invalid_calculation_scale',input:name});continue;}
              value*=rule.scale;
            }
            job.inputs[name]=clone(value);
          }
          if(issues.length) job.input_issues=issues;
          for(const rule of spec.skip_when || []) if(own(job.inputs,rule.input)&&rule.values.some(value=>JSON.stringify(value)===JSON.stringify(job.inputs[rule.input]))) {job.not_applicable=true;job.message=rule.message;break;}
          jobs.push(job);
        }
      }
    }
    return jobs;
  }
  function sectionScopeActive(section, selections = {}) {
    const scope=section.requires_scope;if(!scope)return true;
    const control=selections[scope.section_id],payload=control?.findings?.[scope.finding_id];
    return dictionary(control)&&!control.normal&&!control.not_assessed&&dictionary(payload)&&scope.values.includes(payload[scope.slot_id]);
  }
  function sectionHasSelection(value) {
    return !dictionary(value)||Object.keys(value).some(key=>!['normal','not_assessed','findings','instances'].includes(key))
      ||['normal','not_assessed'].some(key=>own(value,key)&&typeof value[key]!=='boolean')
      ||(own(value,'findings')&&!dictionary(value.findings))||(own(value,'instances')&&!Array.isArray(value.instances))
      ||Boolean(value.normal||value.not_assessed||Object.keys(value.findings || {}).length||value.instances?.length);
  }
  function compose(form, state = {}, context = {}) {
    const schema = descriptorForm(form);
    let investigation = (schema.investigations || []).find(item => item.id === state.investigation_id);
    if (!investigation) return {text: '', missing: [], complete: false, selected_count: 0};
    if (own(state, 'selections') && !dictionary(state.selections)) return {text: '', missing: [{label: 'Invalid report selections'}], complete: false, selected_count: 0};
    const grouped = new Map(), missing = [];
    for (const key of Object.keys(state.selections || {})) if (!(investigation.sections || []).some(section => section.id === key)) missing.push({section_id: key, label: 'Unrecognised section'});
    const scoped = (investigation.sections || []).filter(section => {
      if(sectionScopeActive(section,state.selections || {}))return true;
      if(sectionHasSelection(own(state.selections,section.id)?state.selections[section.id]:{}))missing.push({section_id:section.id,label:'Selection outside the acquired scope: '+section.label});
      return false;
    });
    investigation={...investigation,sections:scoped};
    const expanded = expandRepeated(investigation, state.selections || {});
    investigation = expanded.investigation; state = {...state,selections:expanded.selections}; missing.push(...expanded.missing);
    const blocked = blockedNormals(investigation, state.selections);
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
          const result = descriptorText(finding, selected.findings[finding.id], section.repeat_instance_label ? {} : context);
          if (finding.report !== false) {lines.push(result.text);selectedCount++;} missing.push(...result.missing);
        }
      }
      let linesWithText = lines.filter(Boolean);
      if (section.repeat_instance_label && !selected.not_assessed && linesWithText.length)
        linesWithText = [section.repeat_instance_label + ':\n' + linesWithText.join('\n')];
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
    const allowedCalculators = new Set([...(form.calculator_ids || []), ...(schema.calculator_ids || [])]);
    for (const id of Object.keys(state.calculator_inputs)) if (!allowedCalculators.has(id)) delete state.calculator_inputs[id];
    const calculations = new Map(), calculatorControllers = new Map(), pending = new Set();
    const boundCalculations = new Map(), boundNodes = new Map(); let disposed = false;
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
        if (sectionScopeActive(section,state.selections) && section.normal && !section.exclude_from_bulk_normal && (!group || section.group === group) && !blocked.has(section.id) && !value.normal && !value.not_assessed && !Object.keys(value.findings || {}).length && !(value.instances || []).length) state.selections[section.id] = {normal:true,findings:{}};
      }
    }
    const changeSection = (section, value) => {
      const records = Array.isArray(value.instances) ? value.instances : [value];
      for (const record of records) {
        if (!dictionary(record?.findings)) continue;
        let changed;
        do { changed = false; for (const finding of section.findings) if (own(record.findings, finding.id) && !findingActive(finding, record.findings, section)) {delete record.findings[finding.id];changed=true;} } while (changed);
      }
      state.selections[section.id] = value;
      for (const id of blockedNormals(investigation(), state.selections)) if (state.selections[id]?.normal) delete state.selections[id];
      drawSections(); update(true);
    };
    function drawSlots(descriptor, values, target, focusPrefix = '') {
      if (!dictionary(values)) { target.append(element('p', 'Clear this finding and select its details again.', 'rad-missing-detail')); return; }
      if (!(descriptor.slots || []).length) return;
      const slots = element('div', undefined, 'rad-followups');
      for (const slot of descriptor.slots) {
        const row = element('div', undefined, 'rad-followup'); row.append(element('span', slot.label || 'Detail', 'rad-field-label'));
        const supplied = focusPrefix ? undefined : contextValue(context, descriptor, slot), value = present(supplied) ? supplied : values[slot.id];
        const change = next => {
          if (!focusPrefix) {
            if (slot.context_key) delete context[slot.context_key];
            delete context[descriptor.id + '.' + slot.id];
            if (context[descriptor.id]) delete context[descriptor.id][slot.id];
          }
          if (next === undefined) delete values[slot.id]; else values[slot.id] = next; update(true);
        };
        if (slot.kind === 'choice') {
          const choices = element('div', undefined, 'rad-choices'); choices.setAttribute('role', 'group'); choices.setAttribute('aria-label', slot.label || 'Detail');
          for (const item of slot.options || []) {
            const choice = button(item.label, () => { change(value === item.value ? undefined : item.value); drawSections(); }); choice.dataset.radFocus = 'slot:' + focusPrefix + descriptor.id + ':' + slot.id + ':' + item.value; choose(choice, value === item.value); choices.append(choice);
          }
          row.append(choices);
        } else if (slot.kind === 'number') row.append(numberControl(slot.label || 'Measurement', value, slot, change));
        else row.append(element('span', present(value) ? String(value) : 'Awaiting linked ' + (slot.label || 'detail').toLowerCase(), present(value) ? 'rad-linked-value' : 'rad-missing-detail'));
        slots.append(row);
      }
      target.append(slots);
    }
    function drawFindingChoices(section, sectionState, target, onChange, focusPrefix = '') {
      if (!dictionary(sectionState) || (own(sectionState,'findings') && !dictionary(sectionState.findings))) {
        target.append(element('p','Clear this entry and select its findings again.','rad-missing-detail')); return;
      }
      const chosen = sectionState.findings || {}, choices = element('div', undefined, 'rad-finding-choices');
      for (const finding of section.findings || []) {
        if (!findingActive(finding, chosen, section)) continue;
        const active = own(chosen, finding.id), item = element('div', undefined, 'rad-finding');
        const choice = button(finding.label || finding.text, () => {
          const next = {normal:false,not_assessed:false,findings:{...chosen}};
          if (active) delete next.findings[finding.id];
          else {
            if (finding.exclusive_group) for (const peer of section.findings || []) if (peer.exclusive_group === finding.exclusive_group) delete next.findings[peer.id];
            next.findings[finding.id] = {};
          }
          onChange(next);
        });
        choice.dataset.radFocus = 'finding:' + focusPrefix + finding.id; choose(choice,active); item.append(choice);
        if (active) drawSlots(finding,chosen[finding.id],item,focusPrefix);
        choices.append(item);
      }
      target.append(choices);
    }
    const boundKey = (section,index,spec) => section.id+':'+(index===null?'single':index+1)+':'+spec.calculator_id;
    function appendBoundNodes(section,index,target) {
      for(const spec of section.calculations || []) {
        const node=element('div',undefined,'rad-bound-calculation');node.setAttribute('role','status');node.hidden=true;
        boundNodes.set(boundKey(section,index,spec),node);target.append(node);
      }
    }
    function drawBoundStatus() {
      for(const [key,node] of boundNodes) {
        const entry=boundCalculations.get(key);node.replaceChildren();node.hidden=!entry;if(!entry)continue;
        const result=entry.result,label=entry.job.label;
        let message=label+': calculating…';
        if(result?.status==='complete') message=label+': '+(result.summary || result.category);
        else if(result?.status==='not_applicable') message=label+': '+(result.limitations?.at(-1) || entry.job.message || 'Not applicable to these selections.');
        else if(result?.status==='incomplete') message=label+': choose '+(result.missing_inputs || []).map(title).join(', ')+'.';
        else if(result?.status==='error') message=label+': '+(entry.error || 'Review the selected calculation inputs.');
        node.append(element('p',message,'rad-calculation-result'));
        if(result?.status==='error') node.append(button('Retry calculation',()=>{boundCalculations.delete(key);update();},'rad-small-button'));
        if(result?.sources?.length) {
          const details=element('details',undefined,'rad-calculation-references');details.append(element('summary','Calculation reference'));
          for(const source of result.sources) {const link=element('a',source.title || source.url);link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';details.append(link);}
          node.append(details);
        }
      }
    }
    function syncBoundCalculations() {
      const jobs=compose(schema,state,context).missing.length ? [] : descriptorCalculationJobs(schema,materializedState());
      const keys=new Set(jobs.map(job=>job.binding_id));
      for(const [key,entry] of boundCalculations) if(!keys.has(key)) {pending.delete(entry.pending);boundCalculations.delete(key);}
      for(const job of jobs) {
        const signature=JSON.stringify({inputs:job.inputs,issues:job.input_issues,not_applicable:job.not_applicable,message:job.message});
        if(boundCalculations.get(job.binding_id)?.signature===signature)continue;
        pending.delete(boundCalculations.get(job.binding_id)?.pending);
        const entry={job,signature,result:null};boundCalculations.set(job.binding_id,entry);
        if(job.input_issues?.length) {entry.result={status:'error'};entry.error='Review conflicting or unmapped inputs.';continue;}
        if(job.not_applicable) {entry.result={status:'not_applicable',limitations:[job.message]};continue;}
        const current=()=>!disposed&&boundCalculations.get(job.binding_id)===entry;
        const work=Promise.resolve().then(()=>(options.request || request)('calculators/'+job.calculator_id+'/calculate',{inputs:job.inputs})).then(result=>{
          if(!current())return;entry.result=result;update();
        }).catch(error=>{if(!current())return;entry.result={status:'error'};entry.error=error.message || 'Calculation unavailable.';update();});
        entry.pending=work;track(work);
      }
      drawBoundStatus();
      return jobs;
    }
    function drawSections() {
      const focusKey = document.activeElement?.dataset?.radFocus;
      descriptorFields.replaceChildren(); groupNavigation.replaceChildren(); boundNodes.clear();
      const exam = investigation();
      if (!exam) { descriptorFields.append(element('p', 'Choose the examination above.')); return; }
      const blocked = blockedNormals(exam, state.selections); let lastGroup = null;
      root.classList?.toggle('rad-anatomic-sheet', exam.presentation === 'anatomic_rows');
      for (const section of exam.sections || []) {
        if (!sectionScopeActive(section,state.selections)) continue;
        if (section.group && section.group !== lastGroup) {
          lastGroup = section.group;
          const groupHeader = element('div', undefined, 'rad-anatomic-group');
          groupHeader.append(element('h4', section.group));
          if (exam.sections.some(row => row.group === section.group && sectionScopeActive(row,state.selections) && row.normal && !row.exclude_from_bulk_normal)) groupHeader.append(button('Normal remaining', () => {fillNormal(section.group);drawSections();update(true);}, 'rad-small-button'));
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
        if (section.repeatable) {
          const instances = sectionState.instances || [];
          if (Array.isArray(instances)) instances.forEach((instance,index) => {
            const entry = element('div',undefined,'rad-repeat-instance'), label = (section.repeat_label || section.label) + ' ' + (index+1);
            const entryHeading = element('div',undefined,'rad-section-heading');
            entryHeading.append(element('h6',label),button('Remove ' + label,()=>{
              const remaining = [...instances]; remaining.splice(index,1); changeSection(section,{instances:remaining});
            },'rad-small-button')); entry.append(entryHeading);
            drawFindingChoices(section,instance,entry,next=>{
              const revised = [...instances]; revised[index] = next; changeSection(section,{instances:revised});
            },section.id+'@'+index+':'); appendBoundNodes(section,index,entry); panel.append(entry);
          });
          else panel.append(element('p','Clear these entries and select their findings again.','rad-missing-detail'));
          // A single-record API client may use the original findings shape.
          if (Object.keys(sectionState.findings || {}).length) drawFindingChoices(section,sectionState,panel,next=>changeSection(section,next));
          const add = button('Add ' + (section.repeat_label || section.label).toLowerCase(),()=>{
            const prior = Array.isArray(instances) ? [...instances] : [];
            if (Object.keys(sectionState.findings || {}).length) prior.push({findings:clone(sectionState.findings)});
            prior.push({findings:{}}); changeSection(section,{instances:prior});
          },'rad-small-button');
          add.disabled = !Array.isArray(instances) || instances.length + (Object.keys(sectionState.findings || {}).length ? 1 : 0) >= MAX_REPEAT_INSTANCES;
          if (add.disabled) add.title = 'At most ' + MAX_REPEAT_INSTANCES + ' entries are supported in this section.';
          panel.append(add);
        } else drawFindingChoices(section,sectionState,panel,next=>changeSection(section,next));
        if (!section.repeatable || Object.keys(sectionState.findings || {}).length) appendBoundNodes(section,null,panel);
        descriptorFields.append(panel);
      }
      if (focusKey) [...(descriptorFields.querySelectorAll?.('[data-rad-focus]') || [])].find(node => node.dataset.radFocus === focusKey)?.focus();
    }
    function reportResult() {
      const result = compose(schema, state, context);
      const completeCalculations = [...allowedCalculators].map(id => calculations.get(id)).filter(value => value?.status === 'complete');
      const jobs=result.missing.length ? [] : descriptorCalculationJobs(schema,materializedState()), boundResults=jobs.map(job=>({job,result:boundCalculations.get(job.binding_id)?.result}));
      const completeBound=boundResults.filter(entry=>entry.result?.status==='complete');
      const parts = [result.text, ...completeCalculations.map(value => 'CALCULATED ASSESSMENT\n' + (value.summary || value.category || '') + (value.version ? ' (' + value.version + ')' : '')),
        ...completeBound.map(({job,result:value})=>'CALCULATED ASSESSMENT\n'+job.context_label+': '+(value.summary || value.category || '')+(value.version?' ('+value.version+')':''))].filter(Boolean);
      const incompleteCalculators = [...allowedCalculators].filter(id => Object.values(state.calculator_inputs[id] || {}).some(present) && !['complete','not_applicable'].includes(calculations.get(id)?.status));
      const duplicateCalculators = [...new Set(jobs.map(job=>job.calculator_id))].filter(id=>Object.values(state.calculator_inputs[id] || {}).some(present));
      const missing = [...result.missing, ...incompleteCalculators.map(id => ({calculator_id: id, label: title(id)})),
        ...boundResults.filter(entry=>!['complete','not_applicable'].includes(entry.result?.status)).map(({job})=>({binding_id:job.binding_id,label:job.context_label+' — '+job.label})),
        ...duplicateCalculators.map(id=>({calculator_id:id,label:'Clear the separate '+title(id)+' calculation'}))];
      return {...result, missing, text: parts.join('\n\n'), complete: missing.length === 0 && (result.selected_count > 0 || completeCalculations.length > 0 || completeBound.length > 0)};
    }
    function update(notify = false) {
      if(notify)for(const section of investigation()?.sections || [])if(!sectionScopeActive(section,state.selections))delete state.selections[section.id];
      syncBoundCalculations();
      for (const node of investigationPicker.children) choose(node, node.dataset.investigationId === state.investigation_id);
      normal.disabled = !(investigation()?.sections || []).some(section => section.normal);
      const result = reportResult();
      preview.textContent = result.text || 'Select findings to build the report.';
      copy.disabled = copying || !result.complete;
      const remaining = (investigation()?.sections || []).filter(section => { if(!sectionScopeActive(section,state.selections))return false; const value = selected(section); return !value.normal && !value.not_assessed && !Object.keys(value.findings || {}).length && !(value.instances || []).some?.(entry => entry?.not_assessed || Object.keys(entry?.findings || {}).length); }).length;
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
        const bound = investigation().sections.some(section => (section.calculations || []).some(spec => spec.calculator_id === id));
        const boundElsewhere = (schema.investigations || []).some(item => item.sections.some(section => (section.calculations || []).some(spec => spec.calculator_id === id)));
        if ((bound || boundElsewhere) && !Object.values(inputs).some(present)) continue;
        const controller = calculator(id, inputs, options.request || request, (result, changed) => {
          if (result) calculations.set(id, result); else calculations.delete(id);
          update(changed);
        }, track);
        calculatorControllers.set(id, controller); calculatorFields.append(controller.node);
      }
    }
    function materializedState() {
      const snapshot = clone(state);
      for (const section of investigation()?.sections || []) for (const finding of section.findings || []) {
        const values = snapshot.selections[section.id]?.findings?.[finding.id];
        if (!values) continue;
        for (const slot of finding.slots || []) { const value = contextValue(context, finding, slot); if (present(value)) values[slot.id] = value; }
      }
      return snapshot;
    }
    root.getState = () => {
      const snapshot = materializedState();
      return {...snapshot, descriptor_version: form.descriptor_version || schema.version || schema.schema_hash, descriptor_state: {investigation_id: snapshot.investigation_id, selections: snapshot.selections}, calculations: Object.entries(snapshot.calculator_inputs).filter(([, inputs]) => Object.values(inputs).some(present)).map(([calculator_id, inputs]) => ({calculator_id, inputs}))};
    };
    root.getReport = () => reportResult().text;
    root.getReportResult = () => clone(reportResult());
    root.flush = async () => { while (pending.size) await Promise.all([...pending]); return root.getReportResult(); };
    root.updateContext = values => { context = clone(values || {}); calculations.clear(); for(const entry of boundCalculations.values()) pending.delete(entry.pending); boundCalculations.clear(); drawSections(); drawCalculators(); update(true); };
    root.dispose = () => { disposed=true;for(const entry of boundCalculations.values()) pending.delete(entry.pending);boundCalculations.clear();for (const controller of calculatorControllers.values()) controller.dispose(); };
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
  return {render, compose, descriptorText, descriptorCalculationJobs};
})();
