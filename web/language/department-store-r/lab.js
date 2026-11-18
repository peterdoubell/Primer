import { largestChange, observations, REPLIES, STORES } from './model.mjs';

const get = id => document.getElementById(id);
const word = get('word');
const measure = get('measure');
const percent = proportion => (100 * proportion).toFixed(1) + '%';

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function storeBars(group, wordPosition) {
  const store = element('div', undefined, 'store');
  store.append(element('h3', group.name + ' · ' + group.interviews + ' interviews'));
  group.replies.forEach((row, index) => {
    const line = element('div', undefined, 'reply');
    const value = percent(row.proportion);
    const meter = element('meter', undefined, index ? 'repeat' : 'first');
    meter.min = 0;
    meter.max = 1;
    meter.value = row.proportion;
    meter.setAttribute('aria-label', group.name + ', ' + REPLIES[index] + ', “' + wordPosition + '”');
    line.append(element('span', REPLIES[index], 'reply-label'), meter,
      element('span', value + ' · ' + row.part + '/' + row.whole, 'value'));
    store.append(line);
  });
  return store;
}

function counts(groups) {
  return groups.flatMap(group => group.replies.map((row, index) => {
    const tr = element('tr');
    const heading = element('th', group.name + ' · ' + (index ? 'repeat' : 'first reply'));
    heading.scope = 'row';
    tr.append(heading, ...[row.present, row.absent, row.doubtful, row.missing].map(value => element('td', value)));
    return tr;
  }));
}

function render() {
  const position = word.value;
  const wordTitle = '“' + position + '”';
  const mode = measure.value;
  const pronounced = mode === 'pronounced';
  const groups = observations(position, mode);
  get('formula').textContent = pronounced
    ? 'Divide pronounced /r/ by the sum of pronounced /r/ and no constricted /r/. Leave out doubtful and missing tokens.'
    : 'Divide all clear tokens by the number of interviews at that store. Each interview offered at most one token at this word and reply position.';
  get('chart-caption').textContent = (pronounced ? 'Pronounced /r/ among clear tokens' : 'Clear tokens among all interviews') + ' in ' + wordTitle;
  get('chart').replaceChildren(...groups.map(group => storeBars(group, position)));
  get('counts-caption').textContent = 'Labov’s token counts for ' + wordTitle;
  get('counts').replaceChildren(...counts(groups));
  get('prompt').textContent = pronounced
    ? 'Which store shows the largest increase in the share with pronounced /r/ from first reply to careful repetition of ' + wordTitle + '?'
    : 'Which store shows the largest drop in the share of clear tokens from first reply to careful repetition of ' + wordTitle + '?';
  get('feedback').textContent = '';
}

get('answers').replaceChildren(...STORES.map((store, index) => {
  const button = element('button', store.name);
  button.type = 'button';
  button.addEventListener('click', () => {
    const mode = measure.value;
    const best = largestChange(observations(word.value, mode), mode);
    const comparison = best.name + ' changes from ' + percent(best.first) + ' to ' + percent(best.repeat)
      + ', a change of ' + (best.points > 0 ? '+' : '−') + Math.abs(best.points).toFixed(1) + ' percentage points.';
    get('feedback').textContent = (index === best.index ? 'Correct. ' : 'Compare the differences between the two replies. ') + comparison;
  });
  return button;
}));
for (const control of [word, measure]) control.addEventListener('change', render);
render();
