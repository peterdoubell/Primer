'use strict';

(() => {
  const sibilants = new Set(['s','z','ʃ','ʒ','tʃ','dʒ']);
  const otherVoiceless = new Set(['p','t','k','f','θ','h']);
  const suffixes = ['ɪz','s','z'];
  const rule = sound => sibilants.has(sound) ? 0 : otherVoiceless.has(sound) ? 1 : 2;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {ending: sound => suffixes[rule(sound)]};
    return;
  }
  const examples = [['cat','t'],['dog','ɡ'],['horse','s'],['key','i'],['watch','tʃ'],['judge','dʒ'],['book','k'],['bell','l'],['rose','z'],['moth','θ'],['dish','ʃ']];
  const challenges = [['wug','ɡ',true],['niff','f',true],['tass','s',true],['judge','dʒ',false],['key','i',false],['book','k',false]];
  const get = id => document.getElementById(id);
  const select = get('example');
  const rules = [...get('rules').children];
  for (const [index,[noun,sound]] of examples.entries()) {
    const option = document.createElement('option');
    option.value = index;
    option.textContent = `${noun} ends in [${sound}]`;
    select.append(option);
    const row = document.createElement('tr');
    for (const value of [noun,`[${sound}]`,`[${suffixes[rule(sound)]}]`]) {
      const cell = document.createElement('td');cell.textContent = value;row.append(cell);
    }
    get('examples').append(row);
  }
  function explain() {
    const [noun,sound] = examples[Number(select.value)];
    const selected = rule(sound);
    rules.forEach((item,index) => item.classList.toggle('selected',index===selected));
    get('result').textContent = `${noun} ends in [${sound}]. Rule ${selected+1} gives [${suffixes[selected]}].`;
  }
  let index = 0;
  function showQuestion() {
    const [noun,sound,invented] = challenges[index];
    get('prompt').textContent = `${invented ? 'Invented noun' : 'Noun'}: ${noun}. Its last sound is [${sound}]. Which suffix sound follows?`;
    get('feedback').textContent = '';
  }
  select.addEventListener('change',explain);
  for (const button of document.querySelectorAll('[data-answer]')) {
    button.addEventListener('click',() => {
      const [,sound] = challenges[index];
      const selected = rule(sound);
      get('feedback').textContent = button.dataset.answer===suffixes[selected]
        ? `Correct. Rule ${selected+1} gives [${suffixes[selected]}].`
        : `Try again. Check rule ${selected+1} for the final sound [${sound}].`;
    });
  }
  get('next').addEventListener('click',() => {index=(index+1)%challenges.length;showQuestion();});
  explain();showQuestion();
})();
