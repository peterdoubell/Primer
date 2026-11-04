'use strict';
// Every row is an entry in the miniature dictionary. The two example sentences
// deliberately use ordinary words so a reader can reason from the definition.
const entries = [
  ['bud','A small part of a plant that can open into a flower or leaf.','A pink flower opened from the bud.','We carried water in the bud.'],
  ['bug','A small insect.','A bug crawled up the stem.','She unlocked the gate with a bug.'],
  ['cap','A soft hat.','He pulled his cap over his hair.','The cap swam to the bottom of the pond.'],
  ['cape','A piece of clothing that hangs from the shoulders.','Her cape fluttered behind her as she ran.','We poured milk into a cape.'],
  ['cat','A small animal with whiskers that often purrs.','Our cat curled up on my lap.','I sharpened my cat before drawing.'],
  ['catch','To stop and hold something that is moving.','I stretched out my hands to catch the ball.','I used a spoon to catch a picture on paper.'],
  ['den','A sheltered place where a wild animal lives.','The fox rested in its den.','We tied our shoes with a den.'],
  ['dew','Drops of water that form on cool surfaces.','The morning dew sparkled on the grass.','He wore dew to keep his feet warm.'],
  ['dig','To make a hole by moving earth.','We used a spade to dig in the garden.','I used a comb to dig my hair.'],
  ['fin','A part of a fish that helps it move or balance in water.','A fin broke the surface as the fish turned.','The apple grew on a fin.'],
  ['fir','A tree with needles and cones.','The fir kept its green needles in winter.','We drank the fir from a cup.'],
  ['fit','To be the right size or shape.','These boots fit my feet.','The clouds fit loudly in the sky.']
];
const pageSize = 3;
const byId = id => document.getElementById(id);
const map = byId('pages'), entry = byId('entry'), choices = byId('choices');
const next = byId('next'), feedback = byId('feedback');
let round = 0;
let target;
function button(text, action) {
  const node = document.createElement('button');
  node.type = 'button';
  node.textContent = text;
  node.addEventListener('click', action);
  return node;
}
function openPage(first, last) {
  if (!entry.hidden || !next.hidden) return;
  const [word, definition, example, distractor] = target;
  if (word < first || word > last) {
    feedback.textContent = word < first
      ? 'Look earlier. “' + word + '” comes before “' + first + '”, the first entry on this page.'
      : 'Look later. “' + word + '” comes after “' + last + '”, the last entry on this page.';
    return;
  }
  for (const node of map.children) node.disabled = true;
  byId('heading').textContent = word;
  byId('definition').textContent = definition;
  entry.hidden = false;
  feedback.textContent = 'You found the page. Read the entry and choose a sentence.';
  choices.replaceChildren();
  for (const sentence of (round % 2 ? [example,distractor] : [distractor,example])) {
    choices.append(button(sentence, () => {
      if (sentence !== example) {
        feedback.textContent = 'Try again. Look for a sentence that uses “' + word + '” to mean “' + definition.replace(/\.$/,'').toLowerCase() + '”.';
        return;
      }
      feedback.textContent = 'That fits the entry! ' + example;
      for (const node of choices.children) node.disabled = true;
      next.hidden = false;
      next.focus();
    }));
  }
  byId('heading').focus();
}
function start() {
  // A stride coprime to twelve visits every entry before repeating.
  target = entries[(3 + round * 5) % entries.length];
  byId('prompt').textContent = 'Which page holds “' + target[0] + '”?';
  entry.hidden = true;
  next.hidden = true;
  feedback.textContent = '';
  for (const node of map.children) node.disabled = false;
}
for (let i = 0; i < entries.length; i += pageSize) {
  const first = entries[i][0], last = entries[i + pageSize - 1][0];
  const name = document.createElement('small');
  name.textContent = 'Page ' + (i / pageSize + 1);
  const node = button(first + ' – ' + last, () => openPage(first,last));
  node.prepend(name);
  map.append(node);
}
next.addEventListener('click', () => { round++; start(); map.firstElementChild.focus(); });
start();
