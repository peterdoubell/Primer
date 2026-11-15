const scenes = [
  {
    time: '18:00', title: 'The archive',
    lena: 'Lena checked the display before the doors closed. A letter rested in the glass case.',
    ivo: 'Ivo checked the door latch before closing. He could see a letter in the glass case.',
  },
  {
    time: '18:04', title: 'Four minutes later',
    lena: 'Water was dripping onto the case. Lena lifted the letter out and put it on the high shelf, clear of the drip.',
    ivo: 'Outside in the corridor, Ivo fetched a bucket after hearing water drip.',
    observesMove: ['lena'],
  },
  {
    time: '18:07', title: 'The empty case',
    lena: 'In the supply room, Lena searched for a cloth to dry the case.',
    ivo: 'Ivo came back with the bucket. The glass case was empty and its lid was wet.',
  },
  {
    time: '18:09', title: 'A dry place',
    lena: 'Lena found a cloth and headed back towards the archive.',
    ivo: 'Ivo turned away from the drip. On the high shelf, he saw the letter lying dry.',
  },
  {
    time: '18:12', title: 'An account',
    lena: 'Back in the archive, Lena pointed to the shelf. “I moved the letter before the water reached it,” she said.',
    ivo: 'Lena came in with a cloth. “I moved the letter before the water reached it,” she told Ivo.',
    both: 'Lena returned with a cloth and pointed to the shelf. “I moved the letter before the water reached it,” she told Ivo.',
    hearsAccount: true,
  },
  {
    time: '18:15', title: 'After the drip',
    lena: 'With the cloth beside the case, Lena made a note to report the leak.',
    ivo: 'Ivo set the bucket under the drip and left the letter where it was.',
  },
];

const orders = {
  chronological: [0, 1, 2, 3, 4, 5],
  absence: [2, 0, 1, 3, 4, 5],
  discovery: [3, 2, 0, 1, 4, 5],
};
const get = id => document.getElementById(id);
const order = get('order');
const view = get('view');
const previous = get('previous');
const next = get('next');
const feedback = get('feedback');
let current = 0;

function element(tag, text) {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
}

function render() {
  const telling = orders[order.value];
  const focus = view.value;
  const scene = scenes[telling[current]];
  get('scene-time').textContent = 'Scene ' + (current + 1) + ' of ' + telling.length + ' · ' + scene.time;
  get('reading-title').textContent = scene.title;
  get('scene-text').textContent = focus === 'both' ? (scene.both || scene.lena + ' ' + scene.ivo) : scene[focus];
  previous.disabled = current === 0;
  next.disabled = current === telling.length - 1;
  feedback.textContent = '';
  get('timeline').replaceChildren(...scenes.map((event, index) => {
    const node = element('li', event.time);
    if (index === telling[current]) node.setAttribute('aria-current', 'step');
    return node;
  }));
  get('sequence').replaceChildren(...telling.map((index, position) => {
    const row = document.createElement('tr');
    const heading = element('th', position + 1);
    heading.scope = 'row';
    row.append(heading, element('td', scenes[index].time),
      element('td', position === current ? 'Current scene' : position < current ? 'Earlier in this telling' : 'Later in this telling'));
    if (position === current) row.setAttribute('aria-current', 'step');
    return row;
  }));
}

function assess(answer) {
  const focus = view.value;
  const available = orders[order.value].slice(0, current + 1).map(index => scenes[index]);
  const witnessed = available.find(scene => scene.observesMove?.includes(focus === 'both' ? 'lena' : focus));
  const reported = available.find(scene => scene.hearsAccount);
  const correct = (witnessed || reported ? 'lena' : 'unknown') === answer;
  const reason = witnessed ? 'At ' + witnessed.time + ', this telling shows Lena moving the letter.'
    : reported ? 'At ' + reported.time + ', Lena tells Ivo she moved the letter. That identifies her through her account.'
    : 'The scenes shown so far give no direct observation or account of the move.';
  feedback.textContent = (correct ? 'Supported. ' : 'Try again. ') + reason;
}

for (const selector of [order, view]) selector.addEventListener('change', () => {
  current = 0;
  render();
});
previous.addEventListener('click', () => {
  current--;
  render();
  if (previous.disabled) next.focus();
});
next.addEventListener('click', () => {
  current++;
  render();
  if (next.disabled) previous.focus();
});
for (const button of get('answers').querySelectorAll('button')) {
  button.addEventListener('click', () => assess(button.dataset.answer));
}
render();
