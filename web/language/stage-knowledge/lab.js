'use strict';

const plays = {
  macbeth: {
    title: 'Macbeth',
    source: 'https://www.gutenberg.org/cache/epub/1795/pg1795.html',
    scenes: [
      {
        label: 'Act 1, scene 5',
        title: 'A welcome rehearsed',
        event: 'A messenger has announced that Duncan is coming to Inverness. Alone with Macbeth, Lady Macbeth urges him to greet their guest with an innocent face.',
        figures: ['Lady Macbeth', 'Macbeth'],
        speaker: 'Lady Macbeth',
        line: 'look like the innocent flower',
        perspectives: [
          ['Audience', 'Has heard Lady Macbeth say that Duncan will never see tomorrow’s sun and now hears her advise Macbeth how to greet him.'],
          ['Lady Macbeth', 'Knows who is coming. Her instructions distinguish the face Macbeth will show from the intent she wants him to hide.'],
          ['Macbeth', 'Hears the instructions and says that they will speak further. His final decision is still ahead.'],
          ['Duncan', 'Is absent from this exchange. He has no access to what Lady Macbeth has just said.'],
        ],
        prompt: 'What does this exchange give the audience before Duncan arrives?',
        options: [
          'A reason to read an outward welcome as a possible deception',
          'Proof that Duncan has already discovered the danger',
          'Proof that Macbeth has already made his final decision',
        ],
        correct: 0,
        feedback: 'The instruction teaches the audience to watch the difference between a welcoming face and a hidden intention. Macbeth’s decision remains open.',
      },
      {
        label: 'Act 1, scene 6',
        title: 'Duncan arrives at Inverness',
        event: 'Duncan arrives with his party. He praises the setting before Lady Macbeth enters to greet him.',
        figures: ['Duncan', 'Banquo'],
        speaker: 'Duncan',
        line: 'This castle hath a pleasant seat',
        perspectives: [
          ['Audience', 'Has heard the private exchange. The earlier threat makes Duncan’s praise ominous.'],
          ['Duncan', 'Praises the location and air. His words give the audience a public sign of ease.'],
          ['Banquo', 'Agrees that the air is delicate and points to the birds nesting at the castle. He did not hear the Macbeths’ exchange.'],
        ],
        prompt: 'Why can this line feel more threatening to the audience than it does to Duncan?',
        options: [
          'Duncan is openly accusing his hosts',
          'The audience heard the private threat in the previous scene',
          'Banquo has warned Duncan about the plot',
        ],
        correct: 1,
        feedback: 'Duncan talks about the castle’s setting. The audience brings information from the previous scene to the same words. That difference creates dramatic irony.',
      },
      {
        label: 'Act 1, scene 7',
        title: 'Macbeth makes his decision',
        event: 'Macbeth first says they should go no further. Lady Macbeth challenges him and explains how she will get Duncan’s attendants drunk. Macbeth then agrees.',
        figures: ['Macbeth', 'Lady Macbeth'],
        speaker: 'Macbeth',
        line: 'I am settled and bend up / Each corporal agent to this terrible feat.',
        perspectives: [
          ['Audience', 'Has heard his hesitation and now hears him commit to the murder. The danger has become a plan.'],
          ['Macbeth', 'Has changed his mind. His line commits his whole body to carrying out the deed.'],
          ['Lady Macbeth', 'Hears his decision. The two have discussed getting the attendants drunk and assigning the blame to them.'],
          ['Duncan', 'Remains offstage. The conversation supplies no evidence that he learns of the plan.'],
        ],
        prompt: 'What changes when Macbeth says he is settled?',
        options: [
          'Duncan hears the plan and leaves the castle',
          'Macbeth has already carried out the deed',
          'Macbeth has moved from hesitation to commitment',
        ],
        correct: 2,
        feedback: 'The threat was already available to the audience. Macbeth now commits to acting on it, while Duncan still has no access to the conversation.',
      },
    ],
  },
  twelfth: {
    title: 'Twelfth Night',
    source: 'https://www.gutenberg.org/cache/epub/1526/pg1526.html',
    scenes: [
      {
        label: 'Act 1, scene 2',
        title: 'Viola asks for a disguise',
        event: 'After the shipwreck, Viola asks a captain who helped her ashore to hide her identity and help her enter Orsino’s service.',
        figures: ['Viola', 'Captain'],
        speaker: 'Viola',
        line: 'Conceal me what I am',
        perspectives: [
          ['Audience', 'Hears Viola ask for the disguise. It can later connect the messenger Cesario to the person making the request.'],
          ['Viola', 'Knows the disguise is a plan and chooses to ask the Captain for help.'],
          ['Captain', 'Hears the request and agrees to help keep her identity secret.'],
          ['Orsino and Olivia', 'Are absent. Neither hears how this disguise was arranged.'],
        ],
        prompt: 'What will the audience bring to a later scene with Cesario?',
        options: [
          'The knowledge that Olivia arranged the disguise',
          'The knowledge that Cesario is the identity Viola has adopted',
          'The knowledge that Orsino heard Viola propose the disguise',
        ],
        correct: 1,
        feedback: 'The audience has heard Viola make the plan. Later characters can act on the disguise without knowing how it came about.',
      },
      {
        label: 'Act 1, scene 5',
        title: 'Olivia sends a ring after Cesario',
        event: 'Cesario has left after delivering Orsino’s message. Olivia speaks alone about her reaction to the messenger and then summons Malvolio to take a ring after him.',
        figures: ['Olivia'],
        speaker: 'Olivia',
        line: 'may one catch the plague?',
        perspectives: [
          ['Audience', 'Knows who Cesario really is. It also hears Olivia’s attraction emerge after Cesario leaves.'],
          ['Olivia', 'Thinks she has been speaking with a young man. She compares her sudden attraction to catching an illness.'],
          ['Viola as Cesario', 'Has left the room. She cannot hear the speech that explains why Olivia sends a ring.'],
        ],
        prompt: 'What can the audience explain when Olivia sends the ring?',
        options: [
          'Why Olivia wants another encounter with Cesario',
          'How Olivia discovered Viola’s identity',
          'Why Orsino sent a ring with his messenger',
        ],
        correct: 0,
        feedback: 'The audience hears Olivia acknowledge her own attraction. The ring provides a reason to call the messenger back.',
      },
      {
        label: 'Act 2, scene 2',
        title: 'Viola works out what the ring means',
        event: 'Malvolio delivers the ring as though Cesario left it behind. After he exits, Viola reasons from the message and her memory of the meeting.',
        figures: ['Viola'],
        speaker: 'Viola',
        line: 'I am the man',
        perspectives: [
          ['Audience', 'Already knows Olivia’s motive because it heard her after Cesario left in Act 1, scene 5.'],
          ['Viola', 'Knows she left no ring. Comparing the story with what happened, she infers that Olivia loves Cesario.'],
          ['Malvolio', 'Carries out Olivia’s order and leaves before Viola voices her inference.'],
        ],
        prompt: 'Which piece of information lets Viola reinterpret Malvolio’s errand?',
        options: [
          'She heard Olivia tell Malvolio why she sent him',
          'She has just seen Sebastian wearing the same clothes',
          'She remembers leaving no ring for Malvolio to return',
        ],
        correct: 2,
        feedback: 'Viola compares the claim with what she did. That lets her infer the motive that Olivia’s speech gave the audience earlier.',
      },
      {
        label: 'Act 5, scene 1',
        title: 'Two people appear together',
        event: 'Sebastian enters while Viola, still appearing as Cesario, is already present with Orsino and Olivia. The resemblance is visible to everyone there.',
        figures: ['Viola', 'Sebastian', 'Orsino', 'Olivia'],
        speaker: 'Orsino',
        line: 'One face, one voice, one habit, and two persons',
        perspectives: [
          ['Audience', 'Has followed Viola and Sebastian separately. Their appearance together lets everyone onstage see that there are two people.'],
          ['Orsino', 'Sees two people with the same face, voice and dress. He can now question earlier impressions of Cesario.'],
          ['Olivia', 'Can see both people at once. The twins’ ensuing exchange helps clarify which one she has married.'],
          ['Viola and Sebastian', 'Can see someone who resembles the sibling each feared lost. Their ensuing questions test the recognition.'],
        ],
        prompt: 'What new evidence can the characters now share with the audience?',
        options: [
          'Orsino was present when Viola asked for a disguise',
          'There are two lookalikes, both visible at the same time',
          'The ring was left by Cesario during the first meeting',
        ],
        correct: 1,
        feedback: 'Their simultaneous presence makes a single-person explanation untenable. The twins then compare details of their history to confirm who is who.',
      },
    ],
  },
};

const {get, rows} = Kit;
const playSelect = get('play');
const navigation = get('scenes');
const form = get('question');
let sceneIndex = 0;

function element(tag, text) {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
}

function renderScene(moveFocus = false) {
  const play = plays[playSelect.value];
  const scene = play.scenes[sceneIndex];
  get('scene-location').textContent = scene.label;
  get('scene-heading').textContent = scene.title;
  get('event').textContent = scene.event;
  get('stage').replaceChildren(...scene.figures.map(figure => element('li', figure)));
  get('speaker').textContent = scene.speaker;
  get('line').textContent = scene.line.replace(' / ', '\n');
  get('source').textContent = 'Read ' + play.title;
  get('source').href = play.source + '#:~:text=' + encodeURIComponent(scene.line.split(' / ')[0]);
  get('prompt').textContent = scene.prompt;
  get('answers').replaceChildren(...scene.options.map((option, index) => {
    const label = element('label', '');
    const radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'interpretation';
    radio.value = index;
    radio.required = true;
    label.append(radio, element('span', option));
    return label;
  }));
  get('feedback').textContent = '';
  get('perspectives').open = false;
  rows(get('evidence'), scene.perspectives);

  navigation.replaceChildren(...play.scenes.map((item, index) => {
    const button = element('button', item.label);
    button.type = 'button';
    if (index === sceneIndex) button.setAttribute('aria-current', 'step');
    button.addEventListener('click', () => {
      sceneIndex = index;
      renderScene(true);
    });
    return button;
  }));

  if (moveFocus) get('scene-heading').focus();
}

playSelect.addEventListener('change', () => {
  sceneIndex = 0;
  renderScene();
});

form.addEventListener('input', () => {
  get('feedback').textContent = '';
});

form.addEventListener('submit', event => {
  event.preventDefault();
  const scene = plays[playSelect.value].scenes[sceneIndex];
  const selected = Number(new FormData(form).get('interpretation'));
  get('feedback').textContent = selected === scene.correct
    ? scene.feedback
    : 'Try again. Open the comparison below if you want to check who heard the relevant information.';
});

renderScene();
