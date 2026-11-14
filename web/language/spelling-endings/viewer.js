'use strict';

// The practice words encode pronunciation properties explicitly. Spelling alone
// does not reliably identify a short vowel, silent e, or final-syllable stress.
const examples = [
  {base: 'hope', silentE: true},
  {base: 'hop', shortVowel: true},
  {base: 'cry'},
  {base: 'play'},
  {base: 'mix', shortVowel: true},
  {base: 'help', shortVowel: true},
];
const questions = [
  [{base: 'bake', silentE: true}, 'ing'],
  [{base: 'stop', shortVowel: true}, 'ed'],
  [{base: 'copy'}, 'ed'],
  [{base: 'carry'}, 'ing'],
  [{base: 'fix', shortVowel: true}, 'ed'],
  [{base: 'look'}, 'ing'],
  [{base: 'smile', silentE: true}, 'ed'],
  [{base: 'tap', shortVowel: true}, 'ing'],
];

function spell(word, ending) {
  const {base, silentE, shortVowel} = word;
  const last = base.at(-1);
  if (silentE) return {rule: 'drop', stem: base.slice(0, -1), note: 'Drop the silent e.'};
  if (/[^aeiou]y$/.test(base)) {
    return ending === 'ed'
      ? {rule: 'y', stem: base.slice(0, -1) + 'i', note: 'Change the final y to i.'}
      : {rule: 'y', stem: base, note: 'Keep the y before -ing.'};
  }
  if (shortVowel && /[aeiou][^aeiouwxy]$/.test(base)) {
    return {rule: 'double', stem: base + last, note: 'Double the final ' + last + '.'};
  }
  return {rule: 'plain', stem: base, note: 'Keep the base spelling.'};
}

const get = id => document.getElementById(id);
const word = get('word');
const ending = get('ending');
const answer = get('answer');
const next = get('next');
const check = get('check');
const feedback = get('feedback');
let question = 0;
let solved = false;

function example() {
  const entry = examples[word.selectedIndex];
  const suffix = ending.value;
  const result = spell(entry, suffix);
  for (const step of document.querySelectorAll('#map li')) {
    if (step.dataset.rule === result.rule) step.setAttribute('aria-current', 'step');
    else step.removeAttribute('aria-current');
  }
  get('worked').textContent = entry.base + ' + -' + suffix + ' gives ' + result.stem + suffix + '. ' + result.note;
  get('base-tile').textContent = result.stem;
  get('ending-tile').textContent = suffix;
  get('word-tile').textContent = result.stem + suffix;
}

function prompt() {
  const [entry, suffix] = questions[question];
  solved = false;
  get('prompt').textContent = 'Word ' + (question + 1) + ' of ' + questions.length + '. Add -' + suffix + ' to ' + entry.base + '.';
  answer.value = '';
  answer.disabled = false;
  check.hidden = false;
  next.hidden = true;
  feedback.textContent = '';
}

get('game').addEventListener('submit', event => {
  event.preventDefault();
  if (solved) return;
  const [entry, suffix] = questions[question];
  const result = spell(entry, suffix);
  if (answer.value.trim().toLowerCase() !== result.stem + suffix) {
    feedback.textContent = result.note + ' Try again.';
    answer.focus();
    return;
  }
  solved = true;
  feedback.textContent = 'Correct. ' + result.note;
  answer.disabled = true;
  check.hidden = true;
  next.textContent = question + 1 === questions.length ? 'Play again' : 'Next word';
  next.hidden = false;
  next.focus();
});
next.addEventListener('click', () => {
  question = (question + 1) % questions.length;
  prompt();
  answer.focus();
});

for (const entry of examples) {
  word.add(new Option(entry.base, entry.base));
  const row = get('table').insertRow();
  const heading = document.createElement('th');
  heading.scope = 'row';
  heading.textContent = entry.base;
  row.append(heading);
  for (const suffix of ['ing', 'ed']) row.insertCell().textContent = spell(entry, suffix).stem + suffix;
}
word.addEventListener('change', example);
ending.addEventListener('change', example);
example();
prompt();
