const phrases = [
  {
    name: 'Arriving at a shop', situation: 'You enter a bakery in the morning. Greet the person at the counter.',
    french: 'Bonjour !', english: 'Hello!', distractors: ['Au revoir !', 'Bonne nuit !'],
  },
  {
    name: 'Asking for repetition', situation: 'The speaker answers quickly. Ask politely for the same words again.',
    french: 'Pouvez-vous répéter, s’il vous plaît ?', english: 'Can you repeat that, please?',
    distractors: ['Pouvez-vous attendre, s’il vous plaît ?', 'Pouvez-vous écrire votre nom ?'],
  },
  {
    name: 'Asking for slower speech', situation: 'You heard the words, but the person is speaking too fast. Ask them to slow down.',
    french: 'Pouvez-vous parler plus lentement ?', english: 'Can you speak more slowly?',
    distractors: ['Pouvez-vous parler plus fort ?', 'Pouvez-vous fermer la porte ?'],
  },
  {
    name: 'Ordering at a café', situation: 'Order a coffee politely at the counter.',
    french: 'Je voudrais un café, s’il vous plaît.', english: 'I’d like a coffee, please.',
    distractors: ['Je voudrais l’addition, s’il vous plaît.', 'Je voudrais un verre d’eau, s’il vous plaît.'],
  },
  {
    name: 'Asking for directions', situation: 'You are looking for the train station. Ask where it is.',
    french: 'Excusez-moi, où est la gare ?', english: 'Excuse me, where is the train station?',
    distractors: ['Excusez-moi, où est la pharmacie ?', 'Excusez-moi, à quelle heure part le train ?'],
  },
  {
    name: 'Checking a direction', situation: 'Your companion points left at a junction. Say that the station is to the left.',
    french: 'La gare est à gauche.', english: 'The station is on the left.',
    distractors: ['La gare est à droite.', 'La gare est tout droit.'],
  },
  {
    name: 'Paying at a restaurant', situation: 'You have finished your meal. Ask for the bill.',
    french: 'L’addition, s’il vous plaît.', english: 'The bill, please.',
    distractors: ['Le menu, s’il vous plaît.', 'Une autre fourchette, s’il vous plaît.'],
  },
  {
    name: 'Leaving the shop', situation: 'You are leaving the shop. Say goodbye.',
    french: 'Au revoir !', english: 'Goodbye!',
    distractors: ['Enchanté !', 'Bienvenue !'],
  },
];
const get = id => document.getElementById(id);
const prompt = get('prompt');
const answers = get('answers');
const result = get('result');
const next = get('next');
const restart = get('restart');
const speak = get('speak');
const audioStatus = get('audio-status');
let queue;
let passed;
let misses;
let answered = false;

function node(tag, text) {
  const element = document.createElement(tag);
  element.textContent = text;
  return element;
}

function updateProgress() {
  get('progress').textContent = passed.size + ' of ' + phrases.length + ' exchanges answered correctly.';
  get('progress-rows').replaceChildren(...phrases.map((phrase, id) => {
    const row = document.createElement('tr');
    const title = node('th', phrase.name);
    title.scope = 'row';
    const label = passed.has(id) ? 'Answered correctly' : misses.has(id) ? 'Coming back' : 'To practise';
    row.append(title, node('td', label));
    return row;
  }));
}

function showExchange(focus = false) {
  window.speechSynthesis?.cancel();
  answered = false;
  result.replaceChildren();
  audioStatus.textContent = '';
  next.hidden = true;
  speak.hidden = true;
  restart.hidden = queue.length !== 0;
  answers.replaceChildren();
  const id = queue[0];
  if (id === undefined) {
    prompt.textContent = 'Practice complete';
    get('situation').textContent = 'You answered each exchange correctly at least once.';
  } else {
    const card = phrases[id];
    prompt.textContent = card.name;
    get('situation').textContent = card.situation;
    const choices = [...card.distractors];
    choices.splice((id + (misses.get(id) || 0)) % 3, 0, card.french);
    for (const choice of choices) {
      const button = node('button', choice);
      button.type = 'button';
      button.lang = 'fr';
      button.addEventListener('click', () => answer(id, choice, button));
      answers.append(button);
    }
  }
  updateProgress();
  if (focus) prompt.focus();
}

function answer(id, choice, selected) {
  if (answered || queue[0] !== id) return;
  answered = true;
  const card = phrases[id];
  const correct = choice === card.french;
  queue.shift();
  if (correct) {
    passed.add(id);
  } else {
    misses.set(id, (misses.get(id) || 0) + 1);
    queue.splice(Math.min(2, queue.length), 0, id);
  }
  for (const button of answers.querySelectorAll('button')) button.disabled = true;
  selected.dataset.selected = '';
  const line = node('p', correct ? 'That fits the exchange.' : 'That choice has a different meaning. This exchange will return.');
  const phrase = node('strong', card.french);
  phrase.lang = 'fr';
  const translation = node('p', '');
  translation.append(phrase, document.createTextNode(' — ' + card.english));
  result.append(line, translation);
  speak.hidden = !window.speechSynthesis || !window.SpeechSynthesisUtterance;
  speak.onclick = () => read(card.french);
  next.hidden = false;
  next.textContent = queue.length ? 'Next exchange' : 'See practice summary';
  updateProgress();
  next.focus();
}

function read(text) {
  const voices = window.speechSynthesis.getVoices();
  const voice = voices.find(candidate => candidate.lang.toLowerCase() === 'fr-fr') ||
    voices.find(candidate => candidate.lang.toLowerCase().startsWith('fr'));
  if (!voice) {
    audioStatus.textContent = 'A French system voice is unavailable on this device.';
    return;
  }
  window.speechSynthesis.cancel();
  audioStatus.textContent = '';
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = voice;
  utterance.lang = voice.lang;
  utterance.rate = 0.85;
  utterance.onerror = event => {
    if (event.error !== 'canceled' && event.error !== 'interrupted') audioStatus.textContent = 'Audio could not play.';
  };
  window.speechSynthesis.speak(utterance);
}

function start(focus) {
  queue = phrases.map((_, id) => id);
  passed = new Set();
  misses = new Map();
  showExchange(focus);
}
next.addEventListener('click', () => showExchange(true));
restart.addEventListener('click', () => start(true));
start(false);
