/* Small, deterministic concept models. These local activities never award mastery. */
(function () {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  const colors = Object.freeze({ paper: '#f5efdf', ink: '#263b46', blue: '#3e7085',
    teal: '#317e78', gold: '#b98a2f', coral: '#b96652', plum: '#876888' });
  let serial = 0;
  const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const numberText = value => String(Number(value.toFixed(2)));
  const smallLengthText = value => value !== 0 && value < .01 ? value.toExponential(2) : numberText(value);
  const truthText = value => value ? 'true' : 'false';
  const phrase = (label, ...children) => ({ label, children });
  const bracket = tree => typeof tree === 'string' ? tree :
    '[' + tree.label + ' ' + tree.children.map(bracket).join(' ') + ']';
  const leaves = tree => typeof tree === 'string' ? [tree] : tree.children.flatMap(leaves);

  const specs = {
    'arts.1.beat': {
      title: 'More notes do not mean a faster beat',
      instructions: 'Keep four beats. Change the tempo, then split each beat into two or four equal notes. Compare their spacing on the same eight-second ruler; clap the beat and speak the subdivisions.',
      initial: { tempo: 60, division: '2' },
      controls: [{ key: 'tempo', label: 'Beat tempo (beats per minute)', min: 30, max: 120, step: 10 },
        { key: 'division', label: 'Equal notes in each beat', options: ['1', '2', '4'].map(value => ({ value, label: value })) }],
      calculate(s) {
        const division = Number(s.division), beatSeconds = 60 / s.tempo;
        const beats = Array.from({ length: 4 }, (_, i) => i * beatSeconds);
        const notes = Array.from({ length: 4 * division }, (_, i) => i * beatSeconds / division);
        return { data: { beats, notes, beatSeconds, noteSeconds: beatSeconds / division, duration: 4 * beatSeconds, division },
          readout: s.tempo + ' beats per minute: one beat lasts ' + numberText(beatSeconds) + ' seconds. ' + division + ' equal notes per beat gives ' + notes.length + ' notes in four beats. The four-beat span lasts ' + numberText(4 * beatSeconds) + ' seconds.',
          note: 'A silent timing diagram, not a recording or a test of your performance. Each circle marks a note onset; the final boundary marks the end of the fourth beat, not another note. Splitting a beat changes note spacing without changing beat tempo. This example uses equal subdivisions in simple meter; actual melodies also use unequal durations, rests, pitch and expressive timing. All rows share a fixed eight-second scale.',
          legend: [{ label: 'Blue: four steady beats', color: colors.blue }, { label: 'Gold: note onsets', color: colors.gold }],
          sources: [{ label: 'Open Music Theory: simple meter', url: 'https://viva.pressbooks.pub/openmusictheory/chapter/simple-meter-and-time-signatures/' }] };
      },
    },
    'lang.2.etymology': {
      title: 'Related words can travel by different routes',
      instructions: 'Compare import, export and portable. Follow the recorded language route and notice the French step for portable. Treat the shared root as history, not a complete modern definition.',
      initial: { word: 'portable' },
      controls: [{ key: 'word', label: 'Word history to trace', options: ['import', 'export', 'portable'].map(value => ({ value, label: value })) }],
      calculate(s) {
        const routes = { import: [['Latin', 'portare'], ['Latin', 'importare'], ['English', 'import']], export: [['Latin', 'portare'], ['Latin', 'exportare'], ['English', 'export']], portable: [['Latin', 'portare'], ['Late Latin', 'portabilis'], ['French', 'portable'], ['English', 'portable']] };
        const senses = { import: 'bring goods in from abroad', export: 'send goods to another country', portable: 'able to be carried or moved' };
        const formation = { import: 'Latin in- (assimilated to im-) adds an inward sense to portare.', export: 'Latin ex- adds an outward sense to portare.', portable: 'Late Latin portabilis expresses capability; French portable intervenes before English.' };
        return { data: { word: s.word, route: routes[s.word], sense: senses[s.word] },
          readout: 'Trace ' + s.word + ': ' + routes[s.word].map(([language, form]) => language + ' ' + form).join(' to ') + '. Latin portare means to carry. ' + formation[s.word] + ' One current sense: ' + senses[s.word] + '.',
          note: 'Selected historical routes summarized from the linked dictionary entries, not timelines to scale or dates of invention. The shared Latin verb is a historical connection, not proof based on similar spelling. Import also developed senses involving significance; its English history is not simply today’s goods-trade meaning projected backward. Only one ordinary current sense is displayed for each word. Modern meanings, additional senses and technical uses require contemporary usage evidence. The diagram distinguishes derivation within Latin from transmission between languages and does not claim that English coined these words by attaching prefixes to its own word port.',
          legend: [{ label: 'Blue: historical language and form', color: colors.blue }, { label: 'Gold: the English endpoint', color: colors.gold }],
          sources: [{ label: 'Etymonline: ' + s.word, url: 'https://www.etymonline.com/word/' + s.word }] };
      },
    },
    'lang.2.poetry': {
      title: 'A metrical foot is a pattern, not a syllable count',
      instructions: 'Choose a foot pattern and repeat it. Compare patterns with the same number of syllables but different stress positions, then count feet separately from syllables.',
      initial: { foot: 'iamb', feet: 3 },
      controls: [{ key: 'foot', label: 'Foot pattern', options: ['iamb', 'trochee', 'anapest', 'dactyl'].map(value => ({ value, label: value })) }, { key: 'feet', label: 'Feet in the model line', min: 1, max: 4, step: 1 }],
      calculate(s) {
        const pattern = { iamb: [false, true], trochee: [true, false], anapest: [false, false, true], dactyl: [true, false, false] }[s.foot];
        const stresses = Array.from({ length: s.feet }, () => pattern).flat(), groups = Array.from({ length: s.feet }, (_, i) => ({ start: i * pattern.length, end: (i + 1) * pattern.length }));
        return { data: { foot: s.foot, pattern, stresses, groups, feet: s.feet, syllables: stresses.length },
          readout: s.foot + ': ' + pattern.map(v => v ? 'stressed' : 'unstressed').join(', ') + '. Repeat this foot ' + s.feet + (s.feet === 1 ? ' time' : ' times') + ': ' + stresses.length + ' syllables, ' + s.feet + ' feet. Each foot in these selected patterns has one stressed syllable. Changing stress position can change the foot even when the syllable count stays the same.',
          note: 'Idealized repeating patterns for English accentual-syllabic meter. The x mark means unstressed and / means stressed. Tall gold marks and short blue marks encode those categories; their heights are not measured loudness, pitch, duration or a stress ratio. Horizontal spacing fits the line into the diagram and is not a time axis. These patterns are not an automatic scansion of a poem: actual verse can substitute feet, omit syllables and support more than one reading. Foot boundaries need not coincide with word boundaries. Meter, rhyme and imagery are distinct; neither rhyme nor imagery is inferred from this pattern. Other poetic traditions organize meter differently.',
          legend: [{ label: 'Gold /: stressed syllable', color: colors.gold }, { label: 'Blue x: unstressed syllable', color: colors.blue }],
          sources: [{ label: 'Academy of American Poets: meter and metrical feet', url: 'https://poets.org/glossary/meter' }] };
      },
    },
    'lang.2.novels': {
      title: 'Readers and characters can know different things',
      instructions: 'Move through four invented chapters. Switch between the reader’s information and Mina’s information. Track when the setting, goal and knowledge change.',
      initial: { chapter: 2, perspective: 'reader' },
      controls: [{ key: 'chapter', label: 'Chapter reached', min: 1, max: 4, step: 1 }, { key: 'perspective', label: 'Whose knowledge?', options: [{ value: 'reader', label: 'Reader' }, { value: 'mina', label: 'Mina' }] }],
      calculate(s) {
        const chapters = [
          { event: 'Mina finds an unsigned map.', place: 'Village', goal: 'Identify the mapmaker', reader: 'Mapmaker unknown', mina: 'Mapmaker unknown' },
          { event: 'A separate scene shows Leo drawing it.', place: 'Village', goal: 'Identify the mapmaker', reader: 'Leo made the map', mina: 'Mapmaker unknown' },
          { event: 'Mina recognizes Leo’s initials.', place: 'City library', goal: 'Find Leo', reader: 'Leo made the map', mina: 'Leo made the map' },
          { event: 'Leo and Mina reach the hidden garden.', place: 'Hidden garden', goal: 'Explore the garden', reader: 'Leo made the map', mina: 'Leo made the map' },
        ];
        const selected = chapters[s.chapter - 1], knowledge = selected[s.perspective], gap = selected.reader !== selected.mina;
        return { data: { chapter: s.chapter, perspective: s.perspective, selected, knowledge, gap, knownEvents: chapters.slice(0, s.chapter).map(c => c.event) },
          readout: 'Chapter ' + s.chapter + ': ' + selected.event + ' Mina’s location: ' + selected.place + '. Mina’s current goal: ' + selected.goal + '. ' + (s.perspective === 'reader' ? 'Reader' : 'Mina') + ' knows: ' + knowledge + '. ' + (gap ? 'The reader knows who made the map, but Mina does not yet know. That gap can create anticipation.' : 'Reader and Mina have the same stated information about the mapmaker at this point.'),
          note: 'An original miniature narrative, not a summary of a published novel. Chapter 2 reveals information in a separate scene while Mina stays in the village; reading that scene does not give Mina access to it. The tracker exposes only events up to the selected chapter. Knowledge here means information explicitly supplied by these invented scenes; guesses, unreliable narration and unstated beliefs are not modeled. A knowledge gap is one possible source of dramatic irony, not a guarantee of a particular reader reaction. Changing perspective changes the displayed information, not the events. Use this method alongside the novel you are actually reading.',
          legend: [{ label: 'Gold: chapter reached', color: colors.gold }, { label: 'Blue: Mina’s location and goal', color: colors.blue }, { label: 'Teal: information available to the selected perspective', color: colors.teal }], sources: [] };
      },
    },
    'lang.2.research': {
      title: 'Three agreeing pages may repeat just one source',
      instructions: 'Trace where each page gets its claim. Change the third source from a copy to an independent record, then ask whether any source answers your actual question.',
      initial: { third: 'copy', question: 'opening', inspect: 'B' },
      controls: [{ key: 'third', label: 'Origin of source C', options: [{ value: 'copy', label: 'C copies B' }, { value: 'independent', label: 'C uses an independent record' }] }, { key: 'question', label: 'Research question', options: [{ value: 'opening', label: 'When did the bridge open?' }, { value: 'cost', label: 'How much did the bridge cost?' }] }, { key: 'inspect', label: 'Inspect source', options: ['A', 'B', 'C'].map(value => ({ value, label: value })) }],
      calculate(s) {
        const edges = s.third === 'copy' ? [['A', 'B'], ['B', 'C']] : [['A', 'B']], roots = { A: 'A', B: 'A', C: s.third === 'copy' ? 'A' : 'C' }, origins = new Set(Object.values(roots)).size;
        const provenance = { A: 'A is the archive record where this branch of the claim originates.', B: 'B repeats A; it is not an additional independent record.', C: s.third === 'copy' ? 'C repeats B, which repeats A. Trace the claim back through both links.' : 'C is stipulated to use a separately created independent record, not a different website repeating A.' }[s.inspect];
        const relevant = s.question === 'opening';
        return { data: { edges, roots, origins, inspect: s.inspect, independent: s.third === 'independent', relevant, provenance },
          readout: 'Invented example: A, B and C all report that a bridge opened in 2000. Three agreeing documents trace to ' + origins + (origins === 1 ? ' original record. ' : ' independent original records. ') + 'Inspect ' + s.inspect + ': ' + provenance + ' ' + (relevant ? 'The reported opening year is relevant to the opening question, but still needs verification.' : 'None of these statements gives the construction cost. Agreement about a date cannot answer a cost question.'),
          note: 'The bridge, date and documents are fictional. An arrow points from a source to a document that copies its claim; it is a provenance link, not evidence that the claim is true. Independence is explicitly stipulated here, not inferred from different authors, domains or logos. Real independence requires checking how records were produced and whether they share an underlying source. The number of origins is not a confidence percentage: even independent records can be mistaken or irrelevant. Investigate provenance, purpose, date, context and the precise question before drawing conclusions.',
          legend: [{ label: 'Blue arrows: a claim is copied along this link', color: colors.blue }, { label: 'Gold: source being inspected', color: colors.gold }], sources: [] };
      },
    },
    'lang.2.speaking': {
      title: 'Help listeners follow the steps in your explanation',
      instructions: 'Prepare a short talk about sorting a book list. Change the audience, add or omit the explanation, and compare the talk with and without spoken signposts.',
      initial: { audience: 'new', explanation: true, signposts: true },
      controls: [{ key: 'audience', label: 'Audience background', options: [{ value: 'new', label: 'New to alphabetical sorting' }, { value: 'familiar', label: 'Already knows alphabetical sorting' }] }, { key: 'explanation', label: 'Include the explanatory connection', type: 'toggle' }, { key: 'signposts', label: 'Include spoken signposts', type: 'toggle' }],
      calculate(s) {
        const rows = [{ role: 'Claim', signpost: 'First', lines: ['I sort my book list', 'to help me find titles.'] }, { role: 'Example', signpost: 'For example', lines: ['“Cat” comes before “Catch”', 'in alphabetical order.'] }, { role: 'Explanation', signpost: 'Here is why', lines: s.audience === 'new' ? ['Compare letters left to right.', 'A matching shorter word is first.'] : ['The shared prefix is “Cat”.', 'The shorter title sorts first.'] }, { role: 'Takeaway', signpost: 'Remember', lines: ['Match the beginning,', 'then check what comes next.'] }].filter(r => s.explanation || r.role !== 'Explanation');
        const spoken = rows.map(r => (s.signposts ? r.signpost + ': ' : '') + r.lines.join(' ')).join(' ');
        return { data: { rows, spoken, signposts: s.signposts, audience: s.audience, explanation: s.explanation },
          readout: 'Audience ' + (s.audience === 'new' ? 'new to alphabetical sorting' : 'already familiar with alphabetical sorting') + '. Spoken signposts ' + (s.signposts ? 'included' : 'omitted') + '. Your talk: ' + spoken + ' ' + (s.explanation ? 'The explanation connects the example to the sorting method.' : 'Without the explanation, listeners must supply the connection themselves.'),
          note: 'An original short speaking plan, not a measured prediction of listener comprehension or persuasion. Cat and Catch are example titles with a shared prefix. A beginner may need the procedure explained; a familiar audience can use the shorter technical reference. This audience toggle represents stated prior knowledge, not assumptions based on age or identity. Signposts make transitions explicit but do not add evidence or guarantee clarity. The diagram always names each part for planning; only the optional signpost phrases are part of the spoken version. No microphone, voice-quality grading, speech-rate target or mastery scoring is used.',
          legend: [{ label: 'Blue: claim and takeaway', color: colors.blue }, { label: 'Gold: concrete example', color: colors.gold }, { label: 'Teal: explanation', color: colors.teal }], sources: [] };
      },
    },
    'lang.2.grammar': {
      title: 'The subject controls agreement inside a nested clause',
      instructions: 'Change the subject and verb independently. Inspect the subject, predicate or prepositional phrase. Notice that logs is plural but does not control this verb.',
      initial: { subject: 'fox', verb: 'jumps', focus: 'subject' },
      controls: [{ key: 'subject', label: 'Subject noun', options: ['fox', 'foxes'].map(value => ({ value, label: value })) }, { key: 'verb', label: 'Present-tense verb form', options: ['jumps', 'jump'].map(value => ({ value, label: value })) }, { key: 'focus', label: 'Inspect constituent', options: [{ value: 'subject', label: 'Noun phrase: subject' }, { value: 'predicate', label: 'Verb phrase: predicate' }, { value: 'pp', label: 'Prepositional phrase' }] }],
      calculate(s) {
        const subject = 'The ' + s.subject, predicate = s.verb + ' over logs', agreement = (s.subject === 'fox') === (s.verb === 'jumps');
        const tree = phrase('Clause', phrase('NP', 'The', s.subject), phrase('VP', s.verb, phrase('PP', 'over', 'logs')));
        const explanation = { subject: 'The ' + s.subject + ' is a noun phrase functioning as subject. Its head noun controls agreement here.', predicate: predicate + ' is the verb phrase functioning as predicate. It contains the verb and the prepositional phrase.', pp: 'Over logs is a prepositional phrase nested inside the predicate. Logs is not the subject of jump.' }[s.focus];
        return { data: { subject, predicate, verb: s.verb, focus: s.focus, tree, agreement, sentence: subject + ' ' + predicate + '.' },
          readout: subject + ' ' + predicate + '. ' + (agreement ? 'Subject and verb agree.' : 'Agreement mismatch in this standard English statement: use ' + (s.subject === 'fox' ? 'jumps' : 'jump') + ' with ' + subject + '.') + ' ' + explanation,
          note: 'A simplified constituent analysis of a small present-tense standard English example. NP names a phrase form; subject names its function. VP functions as predicate, with an optional prepositional adjunct in this example. The prepositional phrase is always present in this model to make nesting visible. The head noun fox/foxes controls the verb, not the noun logs. Singular third-person fox takes jumps; plural foxes takes jump. A structural diagram can still locate an agreement error; showing a tree does not certify grammaticality. Other constructions, dialects, languages, tenses and competing syntactic analyses are outside this activity.',
          legend: [{ label: 'Gold: selected constituent', color: colors.gold }, { label: 'Blue: constituent boundaries', color: colors.blue }],
          sources: [{ label: 'Naval Postgraduate School: subject–verb agreement', url: 'https://nps.edu/web/gwc/subject/verb-agreement' }] };
      },
    },
    'lang.2.paragraphs': {
      title: 'Evidence must connect to the paragraph’s claim',
      instructions: 'Choose a supporting detail and toggle the explanation. Rearrange the same sentences. Does changing the order repair evidence that is unrelated to the claim?',
      initial: { evidence: 'schedule', explanation: true, order: 'claim-first' },
      controls: [{ key: 'evidence', label: 'Supporting detail', options: [{ value: 'schedule', label: 'Members’ availability' }, { value: 'badges', label: 'Badge color' }] }, { key: 'explanation', label: 'Explain why availability matters', type: 'toggle' }, { key: 'order', label: 'Sentence order', options: [{ value: 'claim-first', label: 'Claim, detail, explanation, conclusion' }, { value: 'detail-first', label: 'Detail, claim, conclusion, explanation' }] }],
      calculate(s) {
        const rows = [{ role: 'Claim', lines: ['Our club should meet', 'after school.'] }, { role: 'Detail', lines: s.evidence === 'schedule' ? ['Eight of ten members', 'are free then.'] : ['Our club badges', 'are blue.'] }, { role: 'Explanation', lines: ['Members need free time', 'in order to attend.'] }, { role: 'Conclusion', lines: ['That time could help', 'more members attend.'] }];
        const indices = (s.order === 'claim-first' ? [0, 1, 2, 3] : [1, 0, 3, 2]).filter(i => s.explanation || i !== 2), displayed = indices.map(i => rows[i]);
        const relevant = s.evidence === 'schedule', diagnosis = !relevant ? 'Badge color does not support the time choice.' : s.explanation ? 'The reason for relevance is explicit.' : 'The reader must supply the connection.';
        return { data: { rows: displayed, relevant, explanation: s.explanation, diagnosis },
          readout: 'Invented club example: ' + displayed.map(r => r.lines.join(' ')).join(' ') + ' ' + diagnosis + ' Changing order does not change which detail is relevant.',
          note: 'All club details and counts are invented for this writing exercise, not survey evidence. Availability is relevant to attendance; badge color is not evidence for a meeting time. Even the relevant count does not prove that after school is the best choice: the two unavailable members, room access and other constraints remain unknown. Explanation makes a link explicit but cannot turn an unrelated fact into support. The two orders invite comparison, not a universal rule that every paragraph must start with a topic sentence or contain exactly four sentences. No automatic writing-quality or mastery score is produced.',
          legend: [{ label: 'Blue: claim and conclusion', color: colors.blue }, { label: 'Gold: detail offered as evidence', color: colors.gold }, { label: 'Teal: explanatory connection', color: colors.teal }],
          sources: [{ label: 'Purdue: paragraph unity, coherence and development', url: 'https://owl.purdue.edu/owl/general_writing/academic_writing/paragraphs_and_paragraphing/paragraphing.html' }] };
      },
    },
    'lang.0.phonics': {
      title: 'Blend the sounds in their written order',
      instructions: 'Choose a word. With an adult, say its sounds rather than its letter names. Move one step at a time, join the sounds, then say the whole word.',
      initial: { word: 'cat', step: 1 },
      controls: [{ key: 'word', label: 'Word to blend', options: ['cat', 'mat', 'sat'].map(value => ({ value, label: value })) }, { key: 'step', label: 'Sounds included in the blend', min: 0, max: 3, step: 1 }],
      calculate(s) {
        const sounds = [{ cat: 'k', mat: 'm', sat: 's' }[s.word], 'æ', 't'], prefix = s.word.slice(0, s.step), meaning = { cat: 'an animal', mat: 'a small floor covering', sat: 'was sitting' }[s.word];
        return { data: { word: s.word, sounds, step: s.step, prefix, complete: s.step === 3, meaning },
          readout: 'Word to practice: ' + s.word + '. ' + (s.step === 0 ? 'Get ready to blend from left to right.' : s.step < 3 ? 'Join the first ' + s.step + (s.step === 1 ? ' sound. ' : ' sounds. ') + 'The highlighted letters show how far you have reached, not a new whole word.' : 'All three sounds are joined. Say ' + s.word + ': ' + meaning + '.') + ' Ask an adult to model the sounds; do not spell aloud using letter names.',
          note: 'A visual guide for adult-supported oral blending, not an audio pronunciation lesson or speech assessment. In these common English pronunciations, C in cat represents /k/, A represents /æ/, and T represents /t/. The small slash labels are broad phonetic notation for the adult. Changing C to M or S changes the first sound while the ending stays the same. Partial written blends are not taught as separate words. A normal reading voice may pronounce whole words but may misread isolated letters or phonetic symbols; it is not used as evidence of correct sound production. Avoid adding an extra vowel to consonants. Accents and other words can have different sound–letter mappings. No recording or mastery scoring occurs.',
          legend: [{ label: 'Gold: sounds included so far', color: colors.gold }, { label: 'Blue: sounds still to join', color: colors.blue }],
          sources: [{ label: 'Reading Rockets: phonemic awareness and blending', url: 'https://www.readingrockets.org/reading-101/reading-and-writing-basics/phonological-and-phonemic-awareness' }] };
      },
    },
    'lang.1.handwriting': {
      title: 'Build a letter with ordered strokes and guides',
      instructions: 'Choose lowercase i or t. Follow the numbered strokes, lifting between them. Toggle the guides to compare where the stem begins and where it rests.',
      initial: { letter: 'i', step: 1, guides: true },
      controls: [{ key: 'letter', label: 'Lowercase letter', options: ['i', 't'].map(value => ({ value, label: value })) }, { key: 'step', label: 'Completed strokes', min: 0, max: 2, step: 1 }, { key: 'guides', label: 'Show alignment guides', type: 'toggle' }],
      calculate(s) {
        const strokes = s.letter === 'i' ? [{ kind: 'line', x1: 210, y1: 160, x2: 210, y2: 240 }, { kind: 'dot', x: 210, y: 130 }] : [{ kind: 'line', x1: 210, y1: 95, x2: 210, y2: 240 }, { kind: 'line', x1: 180, y1: 160, x2: 240, y2: 160 }];
        const instruction = s.step === 0 ? 'Start at 1. Move down.' : s.step === 1 ? s.letter === 'i' ? 'Lift. Add the dot at 2.' : 'Lift. Cross left to right at 2.' : 'Compare the finished letter.';
        return { data: { strokes, completed: strokes.slice(0, s.step), step: s.step, guides: s.guides, letter: s.letter, instruction },
          readout: 'Lowercase ' + s.letter + ', ' + s.step + ' of 2 strokes completed. ' + instruction + ' The stem ends on the baseline. ' + (s.letter === 'i' ? 'The short stem begins at the middle guide; its dot sits above it.' : 'The tall stem begins at the top guide; the cross stroke is at the middle guide.') + ' Alignment guides ' + (s.guides ? 'shown.' : 'hidden.'),
          note: 'One simple unjoined print style, shown enlarged. Letter shapes and stroke conventions vary by school, typeface and writing system; these are examples, not the only correct forms. The dashed trace shows the intended letter; solid strokes show progress. Numbers indicate order and arrows indicate direction. A dot is placed after lifting the pen, not connected by an ink line. The guide toggle changes only the display, not letter geometry. Copy comfortably on paper if useful; this model does not capture handwriting, evaluate grip, prescribe posture or score motor skills. Practice quality is not equated with speed.',
          legend: [{ label: 'Blue: completed strokes', color: colors.blue }, { label: 'Gold: start of the next stroke', color: colors.gold }, { label: 'Dashed: the complete letter to compare', color: colors.ink }], sources: [] };
      },
    },
    'lang.0.speaking': {
      title: 'A reply connects to the question you heard',
      instructions: 'Change the question and choose a reply. Watch how a follow-up can continue the conversation or clear up what was meant.',
      initial: { question: 'toy', reply: 'train' },
      controls: [{ key: 'question', label: 'First speaker asks about', options: [{ value: 'toy', label: 'Which toy?' }, { value: 'place', label: 'Which place?' }] }, { key: 'reply', label: 'Second speaker replies', options: [{ value: 'train', label: 'The toy train.' }, { value: 'park', label: 'At the park.' }, { value: 'clarify', label: 'Which day do you mean?' }] }],
      calculate(s) {
        const question = s.question === 'toy' ? 'Which toy did you play with?' : 'Where did you play?', reply = { train: 'The toy train.', park: 'At the park.', clarify: 'Which day do you mean?' }[s.reply];
        const related = (s.question === 'toy' && s.reply === 'train') || (s.question === 'place' && s.reply === 'park'), clarification = s.reply === 'clarify';
        const followup = clarification ? 'I mean today.' : related ? s.question === 'toy' ? 'What did your train do?' : 'What did you do there?' : s.question === 'toy' ? 'I meant which toy, not where.' : 'I meant where, not which toy.';
        const outcome = clarification ? 'Clarify, then answer.' : related ? 'The reply answers this question.' : 'Try the question again.';
        return { data: { question, reply, followup, related, clarification, outcome },
          readout: 'First speaker: ' + question + ' Second speaker: ' + reply + ' First speaker follows up: ' + followup + ' ' + outcome,
          note: 'An original practice conversation, not a rule for judging a person’s social ability. A toy answer supplies a thing; a place answer supplies a location. Asking what the speaker means is a useful conversational repair, not a wrong answer. A mismatch can arise because the question was unclear or heard differently. Many other replies, communication methods and turn-taking patterns are valid. No recording, speech recognition, compulsory eye contact or social score is used.',
          legend: [{ label: 'Blue: first speaker', color: colors.blue }, { label: 'Teal: second speaker', color: colors.teal }, { label: 'Gold: follow-up or clarification', color: colors.gold }], sources: [] };
      },
    },
    'lang.1.childrens-lit': {
      title: 'What the story says is not everything we infer',
      instructions: 'Read the tiny passage. Change the extra detail and the claim you want to discuss. Ask which part of the text supports the claim, and what remains unknown.',
      initial: { detail: 'return', claim: 'act' },
      controls: [{ key: 'detail', label: 'Detail in the passage', options: [{ value: 'return', label: 'Returns the purse' }, { value: 'asks', label: 'Also asks about a reward' }, { value: 'declines', label: 'Also declines a reward' }] }, { key: 'claim', label: 'Claim to discuss', options: [{ value: 'act', label: 'Returning it was honest' }, { value: 'reward', label: 'Ari wanted a reward' }, { value: 'always', label: 'Ari is always honest' }] }],
      calculate(s) {
        const extra = { return: 'The owner thanks Ari.', asks: 'Ari asks, “Is there a reward?”', declines: 'Ari says, “No reward, thanks.”' }[s.detail];
        const claim = { act: 'Returning it was honest.', reward: 'Ari wanted a reward.', always: 'Ari is always honest.' }[s.claim];
        const status = s.claim === 'act' ? 'Supported interpretation' : s.claim === 'always' ? 'Not established by one event' : s.detail === 'asks' ? 'Plausible, not proved' : s.detail === 'declines' ? 'This detail pushes against it' : 'Motive is not stated';
        const explanation = s.claim === 'act' ? 'Returning someone else’s property supports calling this action honest. The motive may still be uncertain.' : s.claim === 'always' ? 'One return cannot establish how Ari behaves at every other time.' : s.detail === 'asks' ? 'Asking about a reward suggests interest, but does not prove the full reason for returning the purse.' : s.detail === 'declines' ? 'Declining the offered reward weakens this reading, although the passage does not reveal every private thought.' : 'The return alone does not tell us whether Ari wanted a reward.';
        return { data: { passage: ['Ari returns a lost purse.', extra], claim, status, explanation },
          readout: 'Passage: Ari returns a lost purse. ' + extra + ' Claim: ' + claim + ' ' + status + '. ' + explanation,
          note: 'An original miniature passage for practicing evidence-based discussion, not a quotation from a classic book. Apply the same questions to the book you are reading: what does the text say, what am I inferring, and what alternative reading remains possible? Labels describe the support available in this deliberately limited passage; they are not scores or universal judgments about character. New context could change the interpretation.',
          legend: [{ label: 'Blue: words in the passage', color: colors.blue }, { label: 'Gold: a reader’s claim', color: colors.gold }], sources: [] };
      },
    },
    'lang.1.writing-stories': {
      title: 'An action connects a problem to its ending',
      instructions: 'Change what Leo does when the kite gets stuck, then choose whether the ending resolves the problem. Follow the resulting beginning, middle and end.',
      initial: { action: 'help', ending: 'resolved', part: 2 },
      controls: [{ key: 'action', label: 'Leo’s response to the problem', options: [{ value: 'help', label: 'Ask an adult for help' }, { value: 'wait', label: 'Wait and watch' }] }, { key: 'ending', label: 'Kind of ending', options: [{ value: 'resolved', label: 'Kite recovered' }, { value: 'open', label: 'Problem still open' }] }, { key: 'part', label: 'Inspect story part', min: 1, max: 3, step: 1 }],
      calculate(s) {
        const ending = s.ending === 'resolved' ? s.action === 'help' ? ['An adult frees the kite', 'with a long pole.'] : ['The wind changes.', 'The kite floats free.'] : s.action === 'help' ? ['The adult is still helping.', 'The kite remains stuck.'] : ['Leo is still waiting.', 'The kite remains stuck.'];
        const parts = [['Leo flies a kite.', 'It rises above the garden.'], ['The kite catches in a tree.', s.action === 'help' ? 'Leo asks an adult for help.' : 'Leo waits and watches.'], ending];
        const resolved = s.part === 3 && s.ending === 'resolved', objectState = s.part === 1 ? 'Kite flying' : resolved ? 'Kite recovered' : 'Kite stuck';
        return { data: { parts, part: s.part, resolved, objectState },
          readout: 'Your story: ' + parts.flat().join(' ') + ' Inspect part ' + s.part + ': ' + parts[s.part - 1].join(' ') + ' Current state: ' + objectState + '. ' + (s.ending === 'open' ? 'This ending leaves the problem open; a reader may wonder what happens next.' : 'This invented ending connects the outcome to help or a change in the wind.'),
          note: 'An original branching writing example, not a prediction that waiting or asking for help always frees a kite. The writer chooses both the response and the imagined ending. Keeping an ending open is a valid choice, not an error. A beginning–middle–end organizer helps track changes; it is not a requirement that every story have exactly three events, a solved problem or chronological narration. The activity offers no instructions for climbing trees or retrieving objects near hazards. Use it to plan your own story, not as an automated quality score.',
          legend: [{ label: 'Gold: the part being inspected', color: colors.gold }, { label: 'Blue: the other story parts', color: colors.blue }], sources: [] };
      },
    },
    'lang.1.dictionary': {
      title: 'The first different letter decides the order',
      instructions: 'Choose two words. Reveal their letters from left to right. If all letters so far match, keep looking; a shorter matching word comes first.',
      initial: { first: 'catch', second: 'cater', reveal: 3 },
      controls: [{ key: 'first', label: 'First word to compare', options: ['bat', 'can', 'cat', 'catch', 'cater', 'cattle'].map(value => ({ value, label: value })) }, { key: 'second', label: 'Second word to compare', options: ['bat', 'can', 'cat', 'catch', 'cater', 'cattle'].map(value => ({ value, label: value })) }, { key: 'reveal', label: 'Positions inspected (END counts as a position)', min: 0, max: 7, step: 1 }],
      calculate(s) {
        let decisive = 0;
        while (decisive < Math.max(s.first.length, s.second.length) && s.first[decisive] === s.second[decisive]) decisive++;
        const order = s.first === s.second ? 0 : s.first < s.second ? -1 : 1, decided = s.reveal > decisive;
        const outcome = !decided ? 'Keep looking: no decision yet.' : order === 0 ? 'These are the same word.' : (order < 0 ? s.first : s.second) + ' comes first.';
        return { data: { first: s.first, second: s.second, decisive, order, decided, outcome, reveal: s.reveal },
          readout: 'Compare ' + s.first + ' with ' + s.second + '. Inspect ' + s.reveal + ' positions. ' + outcome + (decided ? order === 0 ? ' Both words end after the same letters.' : 'Position ' + (decisive + 1) + ' decides: ' + (s.first[decisive] || 'END') + ' compared with ' + (s.second[decisive] || 'END') + '.' : ' Matching earlier letters cannot settle the order.'),
          note: 'A small lowercase English dictionary-order example. Compare letters from left to right; at the first difference, the earlier alphabet letter wins. If one word ends while all its letters match the other word’s beginning, the shorter word comes first. END is a boundary marker, not an extra letter. Revealing more positions after a decision never reverses it. Equal words are equal, not arbitrarily ranked. This is not a full dictionary search engine or a universal collation rule: capitalization, spaces, hyphens, accents and other writing systems are outside this checked word set.',
          legend: [{ label: 'Gold: the position that decides', color: colors.gold }, { label: 'Blue: inspected matching positions', color: colors.blue }], sources: [] };
      },
    },
    'lang.1.vocabulary': {
      title: 'A more precise word adds a different picture',
      instructions: 'Change the movement word, then change the scene. Compare what the verb tells you with the clues in the scene. Explain your choice: there may be more than one useful wording.',
      initial: { word: 'walked', scene: 'leisure' },
      controls: [{ key: 'word', label: 'Movement word', options: ['walked', 'strolled', 'trudged'].map(value => ({ value, label: value })) }, { key: 'scene', label: 'Scene clues', options: [{ value: 'leisure', label: 'A relaxed afternoon' }, { value: 'mud', label: 'A difficult muddy path' }, { value: 'unknown', label: 'No extra clues yet' }] }],
      calculate(s) {
        const meanings = { walked: ['Not specified', 'Not specified', 'Walking'], strolled: ['Unhurried', 'Relaxed manner', 'Walking'], trudged: ['Slow', 'With effort', 'Walking'] };
        const scenes = { leisure: ['Mina has plenty of time.', 'She enjoys the flowers.'], mud: ['Mina’s boots sink in mud.', 'Each step takes work.'], unknown: ['Mina is going home.', 'We know nothing else yet.'] };
        return { data: { sentence: 'Mina ' + s.word + ' home.', features: meanings[s.word], scene: scenes[s.scene], word: s.word },
          readout: 'Scene: ' + scenes[s.scene].join(' ') + ' Your sentence: Mina ' + s.word + ' home. Pace: ' + meanings[s.word][0] + '. Manner or effort: ' + meanings[s.word][1] + '. ' + (s.word === 'walked' ? 'Walked leaves these details open; a general word can be the honest choice.' : 'This verb adds detail. Does the scene support it, or are you adding something the reader does not yet know?'),
          note: 'These are ordinary literal senses of three English movement verbs, not numerical speed or effort measurements. Walked does not specify a particular pace or mood. Strolled suggests an unhurried, relaxed manner; trudged emphasizes slow, effortful progress. A precise word is not automatically a better word: it can add unsupported detail. The scene is independent of the selected word so learners can discuss fit without a rigid right/wrong score. Figurative senses and unusual literary uses are not evaluated. The sentences and scenes are original examples.',
          legend: [{ label: 'Blue: details supplied by the word', color: colors.blue }, { label: 'Gold: independent scene clues', color: colors.gold }],
          sources: [{ label: 'Cambridge: distinctions among movement verbs', url: 'https://dictionaryblog.cambridge.org/2015/03/25/the-way-we-move-verbs-for-walking-and-running/' }, { label: 'Cambridge: trudge', url: 'https://dictionary.cambridge.org/dictionary/english/trudge' }] };
      },
    },
    'lang.1.spelling': {
      title: 'One sound can need two letters',
      instructions: 'Choose a word and inspect each sound in order. Follow its connection to the letters that spell it. Count sounds separately from letters.',
      initial: { word: 'ship', sound: 1 },
      controls: [{ key: 'word', label: 'Word to explore', options: ['ship', 'fish', 'chat', 'much', 'thin', 'this'].map(value => ({ value, label: value })) }, { key: 'sound', label: 'Inspect sound number', min: 1, max: 3, step: 1 }],
      calculate(s) {
        const entries = { ship: [['sh', 'i', 'p'], ['ʃ', 'ɪ', 'p']], fish: [['f', 'i', 'sh'], ['f', 'ɪ', 'ʃ']], chat: [['ch', 'a', 't'], ['tʃ', 'æ', 't']], much: [['m', 'u', 'ch'], ['m', 'ʌ', 'tʃ']], thin: [['th', 'i', 'n'], ['θ', 'ɪ', 'n']], this: [['th', 'i', 's'], ['ð', 'ɪ', 's']] };
        const [groups, sounds] = entries[s.word], selected = s.sound - 1;
        let offset = 0;
        const spans = groups.map(group => { const span = { start: offset, length: group.length }; offset += group.length; return span; });
        return { data: { word: s.word, groups, sounds, spans, selected, letters: s.word.length },
          readout: 'Word: ' + s.word + '. It has 3 sounds and ' + s.word.length + ' letters in these pronunciations. Sound ' + s.sound + ' is spelled ' + groups[selected].toUpperCase().split('').join(' ') + ', ' + groups[selected].length + (groups[selected].length === 1 ? ' letter.' : ' letters working together.') + ' Say the whole word, then listen for that sound.',
          note: 'Each sound box is one phoneme; each letter tile is one written letter. SH, CH and TH are two-letter graphemes in these examples. The /tʃ/ sound in chat and much is a single affricate phoneme despite its two-symbol transcription. TH represents different sounds in thin /θ/ and this /ð/. Slashes show broad phonetic notation for adults, not extra letters to spell. Common English pronunciations are modeled; accents can differ. This is a small checked word set, not a rule that every two adjacent letters make one sound or that all English words have three phonemes. Ask an adult to model isolated sounds: a text-to-speech voice may read phonetic symbols unreliably. No microphone, pronunciation scoring or automatic spelling inference is used.',
          legend: [{ label: 'Gold: the selected sound and its letters', color: colors.gold }, { label: 'Blue: the other sound–spelling groups', color: colors.blue }],
          sources: [{ label: 'Reading Rockets: phoneme–grapheme spelling maps', url: 'https://www.readingrockets.org/topics/early-literacy-development/articles/how-spelling-supports-reading' }] };
      },
    },
    'lang.1.sentences': {
      title: 'A full stop cannot finish an incomplete idea',
      instructions: 'Build a short statement. Add or remove its action, capital letter and full stop. Notice the difference between a complete clause and its written boundaries.',
      initial: { subject: 'dog', action: 'runs', verb: true, capital: false, stop: false },
      controls: [{ key: 'subject', label: 'Who is the sentence about?', options: ['dog', 'kitten'].map(value => ({ value, label: value })) }, { key: 'action', label: 'Choose an action', options: ['runs', 'jumps'].map(value => ({ value, label: value })) }, { key: 'verb', label: 'Include the action', type: 'toggle' }, { key: 'capital', label: 'Start with a capital letter', type: 'toggle' }, { key: 'stop', label: 'End with a full stop', type: 'toggle' }],
      calculate(s) {
        const subject = (s.capital ? 'The ' : 'the ') + s.subject, predicate = s.verb ? s.action : '', written = subject + (predicate ? ' ' + predicate : '') + (s.stop ? '.' : '');
        const checks = [{ label: 'Complete idea', pass: s.verb }, { label: 'Capital at the start', pass: s.capital }, { label: 'Full stop at the end', pass: s.stop }];
        return { data: { subject, predicate, written, checks, ready: checks.every(c => c.pass) },
          readout: 'You wrote: ' + written + ' Selected action: ' + s.action + (s.verb ? ', included. ' : ', not included. ') + checks.map(c => c.label + ': ' + (c.pass ? 'yes' : 'not yet')).join('. ') + '. ' + (!s.verb ? 'Naming the animal alone leaves this statement unfinished, even with a capital and full stop.' : 'The subject and action make a complete clause; capital letters and punctuation mark it in writing.'),
          note: 'A builder for these simple declarative English statements only. The subject is a noun phrase and the predicate is a finite intransitive verb, so no additional object is required here. Capitalization and punctuation do not supply a missing predicate. Conversely, missing punctuation does not erase the clause’s grammatical structure. Questions, commands with implied subjects, dialogue fragments, headings, tense changes and complex clauses need other patterns; this is not a universal sentence validator. The selected action is unused when its toggle is off. No mastery is awarded.',
          legend: [{ label: 'Blue: subject', color: colors.blue }, { label: 'Teal: predicate or a satisfied check', color: colors.teal }, { label: 'Coral: something still needed', color: colors.coral }],
          sources: [{ label: 'University of Michigan: sentence fragments', url: 'https://lsa.umich.edu/sweetland/undergraduates/writing-guides/sentence-fragments-comma-splices-run-ons.html' }] };
      },
    },
    'lang.0.rhymes': {
      title: 'Rhyme is a sound match, not a spelling match',
      instructions: 'Say the two words aloud. Change either word and listen to the ending. Can different letters make the same ending sound?',
      initial: { first: 'cat', second: 'hat' },
      controls: [{ key: 'first', label: 'First word', options: ['cat', 'sun', 'bee', 'blue'].map(value => ({ value, label: value })) }, { key: 'second', label: 'Compare with', options: ['hat', 'run', 'tree', 'shoe', 'cup'].map(value => ({ value, label: value })) }],
      calculate(s) {
        const words = { cat: ['c', 'at', 'at'], hat: ['h', 'at', 'at'], sun: ['s', 'un', 'un'], run: ['r', 'un', 'un'], bee: ['b', 'ee', 'ee'], tree: ['tr', 'ee', 'ee'], blue: ['bl', 'ue', 'oo'], shoe: ['sh', 'oe', 'oo'], cup: ['c', 'up', 'up'] };
        const first = words[s.first], second = words[s.second], rhyme = first[2] === second[2], sameLetters = first[1] === second[1];
        return { data: { first, second, rhyme, sameLetters },
          readout: 'Say: ' + s.first + '. ' + s.second + '. ' + (rhyme ? 'They rhyme: their ending sounds match.' : 'They do not rhyme: their ending sounds differ.') + (rhyme && !sameLetters ? ' Notice that blue and shoe rhyme even though their endings use different letters.' : ''),
          note: 'These one-syllable English examples compare the vowel and all sounds after it. The colored letter groups show spellings of those ending sounds, not one letter per sound. The small sound hints (at, un, ee, oo, up) are informal pronunciation reminders, not a phonetic alphabet or universal spelling rules. An adult or the reading voice can say the complete words; speech quality depends on the available voice. These examples use common English pronunciations; rhymes can vary with dialect. Rhyme and rhythm are different: matching endings does not specify a beat. This activity does not record or assess pronunciation.',
          legend: [{ label: 'Teal: matching ending sounds', color: colors.teal }, { label: 'Coral: a different ending sound', color: colors.coral }],
          sources: [{ label: 'Academy of American Poets: rhyme', url: 'https://poets.org/glossary/rhyme' }] };
      },
    },
    'lang.0.stories': {
      title: 'Keep track of who, where and what happens',
      instructions: 'Choose a tiny story. Move through its three events, then highlight who, where or what to find that kind of story clue.',
      initial: { story: 'key', event: 1, clue: 'what' },
      controls: [{ key: 'story', label: 'Tiny story', options: [{ value: 'key', label: 'Mina’s missing key' }, { value: 'hat', label: 'Duck’s flying hat' }] }, { key: 'event', label: 'Story event', min: 1, max: 3, step: 1 }, { key: 'clue', label: 'Look for a clue', options: [{ value: 'who', label: 'Who?' }, { value: 'where', label: 'Where?' }, { value: 'what', label: 'What happened?' }] }],
      calculate(s) {
        const story = s.story === 'key' ? { who: 'Mina', where: 'In the garden', events: ['Mina loses her key.', 'She searches under leaves.', 'She finds her key.'], objectStates: ['Key missing', 'Key still missing', 'Key found'] } : { who: 'Duck', where: 'Beside the pond', events: ['Wind blows Duck’s hat away.', 'Duck follows the flying hat.', 'The hat lands. Duck gets it.'], objectStates: ['Hat blown away', 'Hat still in the air', 'Hat recovered'] };
        const selected = story.events[s.event - 1], answer = s.clue === 'what' ? selected : story[s.clue];
        return { data: { ...story, selected, answer, event: s.event, clue: s.clue },
          readout: story.who + '. ' + story.where + '. Event ' + s.event + ' of 3: ' + selected + ' ' + story.objectStates[s.event - 1] + '. The ' + s.clue + ' clue is: ' + answer,
          note: 'Two original, deliberately short stories. The same character and setting continue while events change. Numbered events show what happens first, next and last in these stories; a missing object has not been recovered during the search. This is a listening and retelling aid, not a rule that all stories have three events or must be narrated chronologically. Highlighting a clue does not change the story. No quiz result or mastery is awarded.',
          legend: [{ label: 'Gold: the clue you are looking for', color: colors.gold }, { label: 'Teal: the current event', color: colors.teal }], sources: [] };
      },
    },
    'earth.5.frontier': {
      title: 'Detector orientation selects gravitational-wave response',
      instructions: 'Inspect a transverse ring of freely falling test masses. Change polarization, phase and detector orientation to compare stretching with the differential arm response.',
      initial: { amplitude: .2, phase: 90, polarization: 'plus', angle: 0 },
      controls: [{ key: 'amplitude', label: 'Exaggerated strain amplitude', min: 0, max: .2, step: .05 }, { key: 'phase', label: 'Wave phase', min: 0, max: 360, step: 30, unit: '°' }, { key: 'polarization', label: 'Linear polarization', options: [{ value: 'plus', label: 'Plus' }, { value: 'cross', label: 'Cross' }] }, { key: 'angle', label: 'First detector arm angle', min: 0, max: 90, step: 15, unit: '°' }],
      calculate(s) {
        const h = s.amplitude * Math.sin(s.phase * Math.PI / 180), psi = s.polarization === 'plus' ? 0 : Math.PI / 4, c = Math.cos(2 * psi), v = Math.sin(2 * psi);
        const matrix = [1 + h * c / 2, h * v / 2, h * v / 2, 1 - h * c / 2];
        const point = angle => { const x = Math.cos(angle), y = Math.sin(angle); return { x: matrix[0] * x + matrix[1] * y, y: matrix[2] * x + matrix[3] * y }; };
        const theta = s.angle * Math.PI / 180, signal = h * Math.cos(2 * (theta - psi));
        return { data: { h, matrix, signal, ring: Array.from({ length: 16 }, (_, i) => point(i * Math.PI / 8)), arms: [point(theta), point(theta + Math.PI / 2)] },
          readout: s.polarization + ' polarization, phase ' + s.phase + '°, deliberately exaggerated amplitude ' + s.amplitude + ', first arm angle ' + s.angle + '°. Instantaneous h=' + numberText(h) + '; first-order differential arm strain ' + numberText(signal) + '. A zero response may reflect phase or orientation, not absence of a wave.',
          note: 'A wave travels perpendicular to this page. General relativity has two transverse tensor polarizations, plus and cross, related by a 45° rotation. The displacement map is I+(h/2)[[cos(2ψ),sin(2ψ)],[sin(2ψ),−cos(2ψ)]], with ψ=0° or 45°. For orthogonal unit arms at θ and θ+90°, the first-order differential fractional length change is h cos[2(θ−ψ)]. Strain is vastly exaggerated for visibility. The drawn linear displacement approximation and first-order readout neglect higher-order corrections; exact lengths of the drawn arms can differ from that readout at order h² and higher. This is not an astrophysical-amplitude waveform, source simulation, detector noise model or detection claim. Directional antenna response away from perpendicular incidence and finite light-travel-time effects are omitted.',
          legend: [{ label: 'Blue: displaced test masses; dashed: unperturbed ring', color: colors.blue }, { label: 'Gold/coral: first/second detector arms', color: colors.gold }],
          sources: [{ label: 'LIGO: polarization and detector response', url: 'https://lscsoft.docs.ligo.org/lalsuite/lal/group___simulate_coherent_g_w__h.html' }] };
      },
    },
    'earth.5.earth-systems': {
      title: 'Ice–albedo feedback can create two stable climates',
      instructions: 'Compare cold and warm initial states under identical forcing. Toggle temperature-dependent albedo to isolate how feedback changes the long-term outcome.',
      initial: { initialTemperature: 260, forcing: 0, year: 20, feedback: true },
      controls: [{ key: 'initialTemperature', label: 'Initial global temperature', min: 230, max: 310, step: 10, unit: 'K' }, { key: 'forcing', label: 'Constant added energy flux', min: -10, max: 10, step: 5, unit: 'W/m²' }, { key: 'year', label: 'Inspect model year', min: 0, max: 40, step: 5 }, { key: 'feedback', label: 'Temperature-dependent ice–albedo feedback', type: 'toggle' }],
      calculate(s) {
        const albedo = t => s.feedback ? .6 - .3 * Math.max(0, Math.min(1, (t - 260) / 20)) : .3;
        const flux = t => 340 * (1 - albedo(t)) + s.forcing - .61 * 5.670374419e-8 * t ** 4;
        const rate = t => flux(t) / 10, dt = .25;
        let temperature = s.initialTemperature;
        const records = [{ year: 0, temperature }];
        for (let year = 1; year <= 40; year++) {
          for (let step = 0; step < 4; step++) {
            const k1 = rate(temperature), k2 = rate(temperature + dt * k1 / 2), k3 = rate(temperature + dt * k2 / 2), k4 = rate(temperature + dt * k3);
            temperature += dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6;
          }
          records.push({ year, temperature });
        }
        const selected = records[s.year], reflectivity = albedo(selected.temperature), netFlux = flux(selected.temperature);
        return { data: { records, selected, reflectivity, netFlux },
          readout: 'Initial ' + s.initialTemperature + ' K, added flux ' + s.forcing + ' W/m², feedback ' + (s.feedback ? 'on' : 'off: albedo fixed at 0.3') + '. At model year ' + s.year + ': ' + numberText(selected.temperature) + ' K, albedo ' + numberText(reflectivity) + ', net heating ' + numberText(netFlux) + ' W/m². These are idealized trajectories, not climate projections.',
          note: 'A zero-dimensional mechanism model: C dT/dt=1360(1−α)/4+F−0.61σT⁴, σ=5.670374419×10⁻⁸ W m⁻² K⁻⁴. Effective heat capacity C=10 W year m⁻² K⁻¹; time is in years. With feedback, α=0.6 below 260 K, decreases linearly to 0.3 at 280 K, and stays 0.3 above 280 K. Warming then reduces reflection and increases absorbed sunlight. These chosen thresholds and emissivity illustrate multiple equilibria, not measured global ice fractions or a calibrated modern-Earth forecast. With feedback off, α=0.3 at every temperature. Integration uses fourth-order Runge–Kutta with quarter-year steps. Geography, clouds, water vapor, circulation, latent heat and carbon-cycle feedback are omitted; no real-world tipping threshold or date is inferred.',
          legend: [{ label: 'Blue: temperature trajectory', color: colors.blue }, { label: 'Gold: inspected model year', color: colors.gold }],
          sources: [{ label: 'NYU: zero-dimensional energy balance and ice–albedo feedback', url: 'https://math.nyu.edu/~kleeman/zero_dim_ebm.html' }] };
      },
    },
    'earth.5.cosmology': {
      title: 'Expansion can accelerate while H decreases',
      instructions: 'Change the present matter fraction in a flat matter-plus-Λ universe. Inspect the expansion rate and acceleration at different scale factors.',
      initial: { matter: 30, scale: 1 },
      controls: [{ key: 'matter', label: 'Present matter density fraction', min: 10, max: 100, step: 10, unit: '%' }, { key: 'scale', label: 'Scale factor a (present = 1)', min: .25, max: 2, step: .25 }],
      calculate(s) {
        const m = s.matter / 100, vacuum = 1 - m;
        const at = a => { const matterDensity = m / a ** 3, total = matterDensity + vacuum; return { a, expansion: Math.sqrt(total), matterFraction: matterDensity / total, vacuumFraction: vacuum / total, q: (.5 * matterDensity - vacuum) / total }; };
        const selected = at(s.scale), transition = vacuum ? Math.cbrt(m / (2 * vacuum)) : null;
        return { data: { selected, transition, records: Array.from({ length: 71 }, (_, i) => at(.25 + i * .025)) },
          readout: 'Present matter fraction ' + s.matter + '%, Λ fraction ' + (100 - s.matter) + '%. At a=' + s.scale + ', H/H₀=' + numberText(selected.expansion) + '; q=' + numberText(selected.q) + ' (' + (selected.q < -1e-12 ? 'accelerating' : selected.q > 1e-12 ? 'decelerating' : 'acceleration transition') + '). ' + (transition === null ? 'With no Λ, q stays 0.5: no acceleration transition.' : 'Acceleration begins beyond a=' + numberText(transition) + '.'),
          note: 'A homogeneous, spatially flat expanding model with pressureless matter and a positive cosmological constant; radiation and curvature are omitted. H=ȧ/a, H²/H₀²=Ωm₀/a³+ΩΛ₀ and Ωm₀+ΩΛ₀=1. The deceleration parameter is q=−aä/ȧ²=Ωm(a)/2−ΩΛ(a). Negative q means ä>0, not that H must increase. Matter dilutes as a⁻³ while Λ density stays constant; their fractions relative to the epoch’s critical density change. Acceleration starts when matter density is twice Λ density, not at equal densities. The scale factor is not time, and the graph does not infer cosmic age, distances or measured cosmological parameters. No radiation-era, inflation or structure-formation calculation is included.',
          legend: [{ label: 'Blue: H/H₀ versus scale factor', color: colors.blue }, { label: 'Gold: selected epoch', color: colors.gold }, { label: 'Teal/plum: matter/Λ fractions at that epoch', color: colors.teal }],
          sources: [{ label: 'Friedmann expansion and dark-energy acceleration', url: 'https://ned.ipac.caltech.edu/level5/March08/Frieman/Frieman2.html' }] };
      },
    },
    'earth.5.astrobiology': {
      title: 'A positive signal is not the probability of life',
      instructions: 'Change an assumed life prior and the reliability of a hypothetical biosignature test. Count biological and abiotic positive signals before interpreting a detection.',
      initial: { prior: 1, sensitivity: 90, specificity: 90 },
      controls: [{ key: 'prior', label: 'Assumed life prior', min: 1, max: 50, step: 1, unit: '%' }, { key: 'sensitivity', label: 'Positive signal if life exists', min: 50, max: 100, step: 10, unit: '%' }, { key: 'specificity', label: 'Negative signal if life is absent', min: 50, max: 100, step: 10, unit: '%' }],
      calculate(s) {
        const living = 100 * s.prior, lifeless = 10000 - living;
        const tp = living * s.sensitivity / 100, fn = living - tp, tn = lifeless * s.specificity / 100, fp = lifeless - tn, posterior = tp / (tp + fp);
        return { data: { living, lifeless, tp, fn, tn, fp, posterior },
          readout: 'Hypothetical ensemble of 10,000 worlds; assumed life prior ' + s.prior + '%, sensitivity ' + s.sensitivity + '%, specificity ' + s.specificity + '%. Positive signals: ' + numberText(tp) + ' with life and ' + numberText(fp) + ' without life. Conditional probability of life after a positive signal: ' + numberText(100 * posterior) + '%. These are assumed test properties, not measured alien frequencies.',
          note: 'A binary Bayesian teaching model, not a life-detection claim. Expected counts use an invented ensemble of 10,000 worlds. P(life|positive)=P(positive|life)P(life) / [P(positive|life)P(life)+P(positive|no life)P(no life)]. Specificity is P(negative|no life), not confidence in a positive detection. A 100% posterior here follows only from assuming zero abiotic false positives; it is not empirical proof. Real inference must assess stellar, geological, chemical, instrument and contamination context, uncertain priors and alternative abiotic explanations. The equal-sized table cells encode categories, not population areas. The bar below counts only positive signals.',
          legend: [{ label: 'Teal: biological positive signals', color: colors.teal }, { label: 'Coral: abiotic positive signals', color: colors.coral }],
          sources: [{ label: 'NASA: a Bayesian framework for biosignature assessment', url: 'https://www.giss.nasa.gov/pubs/abs/ca07620h.html' }] };
      },
    },
    'earth.4.planetary': {
      title: 'Thermal motion competes with gravitational binding',
      instructions: 'Compare escape speed with molecular thermal speed at an upper-atmosphere level. Vary gravity, temperature and molecular mass without assuming a sharp retention threshold.',
      initial: { mass: '1', radius: 1, temperature: 500, molecule: '2' },
      controls: [{ key: 'mass', label: 'Planet mass in Earth masses', options: ['0.1', '1', '5'].map(value => ({ value, label: value })) }, { key: 'radius', label: 'Escape-level radius in Earth radii', min: .5, max: 3, step: .5 }, { key: 'temperature', label: 'Upper-atmosphere temperature', min: 100, max: 1000, step: 100, unit: 'K' }, { key: 'molecule', label: 'Particle mass (approximate)', options: [{ value: '2', label: 'H₂: 2 u' }, { value: '4', label: 'He: 4 u' }, { value: '28', label: 'N₂: 28 u' }, { value: '44', label: 'CO₂: 44 u' }] }],
      calculate(s) {
        const gm = 3.986e14 * Number(s.mass), radius = 6.371e6 * s.radius, particleMass = 1.66053906660e-27 * Number(s.molecule), thermalEnergy = 1.380649e-23 * s.temperature;
        const escape = Math.sqrt(2 * gm / radius) / 1000, rms = Math.sqrt(3 * thermalEnergy / particleMass) / 1000, jeans = gm * particleMass / (radius * thermalEnergy);
        return { data: { escape, rms, jeans, speedRatio: escape / rms },
          readout: 'Planet mass ' + s.mass + ' Earth masses, escape-level radius ' + s.radius + ' Earth radii, upper-atmosphere temperature ' + s.temperature + ' K, particle mass ' + s.molecule + ' u. Escape speed ' + numberText(escape) + ' km/s; RMS thermal speed ' + numberText(rms) + ' km/s; Jeans parameter λ=' + numberText(jeans) + '. This ratio of binding energy to kT is not a binary retained/lost verdict.',
          note: 'A local spherical-gravity and ideal-gas comparison, not a planetary atmosphere lifetime prediction. Escape speed is √(2GM/r); RMS thermal speed is √(3kT/m); λ=GMm/(rkT)=1.5(v_escape/v_rms)². The radius is the distance from the planet center at the chosen escape level, and the temperature is upper-atmosphere gas temperature, not surface temperature. Rounded Earth reference GM=3.986×10¹⁴ m³/s² and radius=6371 km are used. Molecular masses are approximate. A Maxwellian has a speed distribution, so RMS speed is not a cutoff; direction, density and collisions matter. Jeans escape rates, hydrodynamic escape, nonthermal loss, replenishment, chemistry and time are omitted. Arbitrary mass/radius choices are comparisons, not confirmed stable planets.',
          legend: [{ label: 'Blue: gravitational escape speed', color: colors.blue }, { label: 'Gold: RMS molecular speed', color: colors.gold }],
          sources: [{ label: 'Thermal atmospheric escape and the Jeans parameter', url: 'https://arxiv.org/abs/1009.5110' }] };
      },
    },
    'earth.4.climatology': {
      title: 'Falling emissions still add to cumulative CO₂',
      instructions: 'Choose a linear emissions decline to zero. Compare annual emissions, cumulative emissions and an illustrative CO₂-only warming response.',
      initial: { rate: 40, zero: 30, response: '0.45', year: 20 },
      controls: [{ key: 'rate', label: 'Initial emissions rate', min: 10, max: 50, step: 10, unit: 'GtCO₂/yr' }, { key: 'zero', label: 'Years until emissions reach zero', min: 10, max: 50, step: 10 }, { key: 'response', label: 'Assumed response per 1000 GtCO₂', options: ['0.3', '0.45', '0.6'].map(value => ({ value, label: value + '°C' })) }, { key: 'year', label: 'Inspect scenario year', min: 0, max: 60, step: 5 }],
      calculate(s) {
        const at = year => { const t = Math.min(year, s.zero); return { rate: s.rate * Math.max(0, 1 - year / s.zero), cumulative: s.rate * (t - t * t / (2 * s.zero)) }; };
        const selected = at(s.year), records = Array.from({ length: 61 }, (_, year) => at(year)), warming = selected.cumulative * Number(s.response) / 1000;
        return { data: { selected, records, warming, finalCumulative: s.rate * s.zero / 2 },
          readout: 'Initial rate ' + s.rate + ' GtCO₂/yr, linear decline to zero after ' + s.zero + ' years, assumed response ' + s.response + '°C per 1000 GtCO₂. Year ' + s.year + ': rate ' + numberText(selected.rate) + ' GtCO₂/yr, cumulative added CO₂ ' + numberText(selected.cumulative) + ' GtCO₂, illustrative added CO₂-only warming ' + numberText(warming) + '°C. Total scenario emissions at zero: ' + numberText(s.rate * s.zero / 2) + ' GtCO₂.',
          note: 'An invented future trajectory, not current emissions data, a dated carbon budget or a full climate forecast. The rate declines linearly and cumulative emissions are its exact integral; no negative emissions occur. Warming uses a constant assumed transient climate response to cumulative CO₂ emissions (TCRE). The three response choices illustrate sensitivity, not probability bounds. CO₂-induced warming is approximately related to cumulative emissions; the exactly flat response after zero is an idealization, not a claim that all climate variables stop changing. Historical warming, non-CO₂ forcing, feedback detail, carbon-cycle uncertainty and zero-emissions commitment are excluded. Quantities are GtCO₂, not GtC. Delaying zero increases the area under the rate curve even if the final rate is identical.',
          legend: [{ label: 'Blue: annual CO₂ emissions', color: colors.blue }, { label: 'Teal: cumulative CO₂ emissions', color: colors.teal }, { label: 'Gold: inspected year', color: colors.gold }],
          sources: [{ label: 'IPCC AR6: cumulative emissions and warming', url: 'https://www.ipcc.ch/report/ar6/wg1/chapter/summary-for-policymakers/' }] };
      },
    },
    'earth.4.oceanatmos': {
      title: 'Geostrophic flow balances pressure and rotation',
      instructions: 'Reverse latitude or pressure acceleration. Compare the pressure and Coriolis accelerations with the perpendicular geostrophic velocity.',
      initial: { latitude: 45, pressure: 2 },
      controls: [{ key: 'latitude', label: 'Latitude (north positive)', min: -60, max: 60, step: 15, unit: '°' }, { key: 'pressure', label: 'Eastward pressure acceleration', min: -4, max: 4, step: 1, unit: '×10⁻⁴ m/s²' }],
      calculate(s) {
        const f = 2 * 7.292115e-5 * Math.sin(s.latitude * Math.PI / 180), pressure = s.pressure * 1e-4, valid = s.latitude !== 0, northVelocity = valid ? -pressure / f : null, coriolis = valid ? f * northVelocity : null;
        return { data: { f, pressure, valid, northVelocity, coriolis },
          readout: 'Latitude ' + s.latitude + '°, eastward pressure acceleration ' + s.pressure + '×10⁻⁴ m/s². ' + (valid ? 'Geostrophic northward velocity ' + numberText(northVelocity) + ' m/s; negative means southward. Eastward Coriolis acceleration ' + numberText(coriolis * 1e4) + '×10⁻⁴ m/s² exactly opposes pressure acceleration.' : 'At the equator f=0: this geostrophic inversion is unavailable, including when zero forcing leaves velocity unconstrained.'),
          note: 'A local steady, frictionless, straight-isobar geostrophic approximation. East is x, north is y; f=2Ωsin(latitude), and the zonal balance is 0=a_pressure+f v, so v=−a_pressure/f. A pressure acceleration toward east corresponds to pressure decreasing eastward. Coriolis acceleration balances pressure acceleration, not velocity. The pressure/Coriolis arrows use one scale; the velocity arrow uses a separate scale because their units differ. Real flow near the equator, in boundary layers, around curved systems or with large acceleration requires additional dynamics. This is not Ekman transport, a weather forecast or a universal model of surface winds and currents.',
          legend: [{ label: 'Blue: pressure acceleration', color: colors.blue }, { label: 'Coral: Coriolis acceleration', color: colors.coral }, { label: 'Gold: geostrophic velocity', color: colors.gold }],
          sources: [{ label: 'NOAA: geostrophic trajectory equations', url: 'https://www.ready.noaa.gov/documents/Tutorial_2022/view/traj_eqns.html' }] };
      },
    },
    'earth.4.geophysics': {
      title: 'Arrival-time gaps constrain distance, not direction',
      instructions: 'Compare P and S travel times through a uniform medium. Change distance and wave speeds, then test what is lost when the path is liquid.',
      initial: { distance: 200, speed: 6, ratio: '0.6', liquid: false },
      controls: [{ key: 'distance', label: 'Source-to-station path length', min: 0, max: 500, step: 50, unit: 'km' }, { key: 'speed', label: 'P-wave speed', min: 4, max: 8, step: 1, unit: 'km/s' }, { key: 'ratio', label: 'Solid S/P speed ratio', options: ['0.5', '0.6', '0.7'].map(value => ({ value, label: value })) }, { key: 'liquid', label: 'Uniform liquid path: no shear propagation', type: 'toggle' }],
      calculate(s) {
        const pTime = s.distance / s.speed, sSpeed = s.liquid ? null : s.speed * Number(s.ratio), sTime = s.liquid ? null : s.distance / sSpeed, lag = s.liquid ? null : sTime - pTime;
        const inferred = s.liquid ? null : lag / (1 / sSpeed - 1 / s.speed);
        return { data: { pTime, sSpeed, sTime, lag, inferred },
          readout: 'Path ' + s.distance + ' km, P speed ' + s.speed + ' km/s, solid S/P ratio ' + s.ratio + ', medium ' + (s.liquid ? 'liquid' : 'solid') + '. P travel time ' + numberText(pTime) + ' s. ' + (s.liquid ? 'No propagating direct S wave in this liquid model; S–P lag and distance inferred from that lag are unavailable. The solid speed ratio is unused.' : 'S travel time ' + numberText(sTime) + ' s; S–P lag ' + numberText(lag) + ' s; inferred path length ' + numberText(inferred) + ' km. One station does not determine source direction.'),
          note: 'Straight paths and constant known velocities in a uniform medium; t=d/v and d=(tS−tP)/(1/vS−1/vP). These are path lengths, not automatically epicentral distances. The plotted travel times assume a known source origin time; the S–P difference cancels it. P waves propagate through solids and liquids; direct shear waves do not propagate through an ideal liquid. A missing observed S arrival alone does not prove liquid: source radiation, detection limits and path effects matter. Real Earth location uses multiple stations, layered velocity models, depth and uncertainty. Refraction, converted phases, attenuation and waveform amplitudes are not modeled. This is not a seismic warning or hazard tool.',
          legend: [{ label: 'Blue: P travel time', color: colors.blue }, { label: 'Coral: S travel time in solid', color: colors.coral }, { label: 'Gold: selected path length', color: colors.gold }],
          sources: [{ label: 'USGS: seismographs and earthquake location', url: 'https://www.usgs.gov/programs/earthquake-hazards/seismographs-keeping-track-earthquakes' }, { label: 'USGS: P and S paths through Earth', url: 'https://www.usgs.gov/media/images/p-wave-and-s-wave-paths-through-earth' }] };
      },
    },
    'earth.4.astrophysics': {
      title: 'A redder spectrum need not mean a cooler source',
      instructions: 'Change source temperature and redshift separately. Compare emitted and observed wavelength spectra, each normalized to its own peak.',
      initial: { temperature: 6000, redshift: 1 },
      controls: [{ key: 'temperature', label: 'Source effective temperature', min: 3000, max: 12000, step: 500, unit: 'K' }, { key: 'redshift', label: 'Redshift z', min: 0, max: 2, step: .25 }],
      calculate(s) {
        const peak = 2.897771955e6 / s.temperature, observedPeak = peak * (1 + s.redshift);
        const logPlanck = wavelength => -5 * Math.log(wavelength) - Math.log(Math.expm1(1.438776877e7 / (wavelength * s.temperature))), normalization = logPlanck(peak);
        const wavelengths = Array.from({ length: 121 }, (_, i) => 100 + i * 3400 / 120), emitted = wavelengths.map(w => Math.exp(logPlanck(w) - normalization)), observed = wavelengths.map(w => Math.exp(logPlanck(w / (1 + s.redshift)) - normalization));
        return { data: { peak, observedPeak, wavelengths, emitted, observed, apparentTemperature: s.temperature / (1 + s.redshift) },
          readout: 'Source ' + s.temperature + ' K, z=' + s.redshift + ': emitted wavelength peak ' + numberText(peak) + ' nm; observed peak ' + numberText(observedPeak) + ' nm. Wavelengths multiply by 1+z. The normalized observed shape matches an unredshifted ideal blackbody at ' + numberText(s.temperature / (1 + s.redshift)) + ' K; the source itself has not cooled.',
          note: 'Planck spectra per unit wavelength, independently normalized to peak one. Wien’s wavelength law uses approximately 2.89777×10⁶ nm K. Peaks of spectra per frequency or per logarithmic interval differ; this graph is explicitly per wavelength. The redshift transformation changes wavelength by 1+z. Normalization deliberately removes absolute brightness: it does not model luminosity distance, cosmological dimming or received flux. A pure normalized blackbody shape cannot distinguish source temperature from redshift; known spectral lines and independent information can help. Real stellar spectra have lines, atmospheres and dust effects. No velocity is inferred from z, and v=cz is not assumed at these redshifts.',
          legend: [{ label: 'Blue: emitted shape, peak normalized', color: colors.blue }, { label: 'Gold: observed shape, peak normalized', color: colors.gold }],
          sources: [{ label: 'NASA: Planck radiation and Wien’s law', url: 'https://imagine.gsfc.nasa.gov/educators/gammaraybursts/imagine/page18.html' }, { label: 'NASA: cosmological wavelength redshift', url: 'https://science.nasa.gov/wp-content/uploads/2024/08/7page45.pdf' }] };
      },
    },
    'earth.3.astronomy': {
      title: 'Temperature alone cannot tell a star’s luminosity',
      instructions: 'Change effective temperature and radius independently. Locate the result on a temperature–luminosity diagram and compare constant-radius guides.',
      initial: { temperature: 6000, radius: '1' },
      controls: [{ key: 'temperature', label: 'Effective temperature', min: 3000, max: 30000, step: 1000, unit: 'K' }, { key: 'radius', label: 'Radius in solar radii', options: ['0.01', '0.1', '1', '10', '100'].map(value => ({ value, label: value + ' solar radii' })) }],
      calculate(s) {
        const radius = Number(s.radius), luminosity = radius ** 2 * (s.temperature / 5772) ** 4, logLuminosity = Math.log10(luminosity);
        const luminosityText = luminosity >= 10000 || luminosity < .01 ? luminosity.toExponential(2) : numberText(luminosity);
        return { data: { radius, luminosity, logLuminosity, luminosityText },
          readout: 'Effective temperature ' + s.temperature + ' K, radius ' + radius + ' solar radii: luminosity ≈ ' + luminosityText + ' solar luminosities. L/L☉ = (R/R☉)²(T/5772 K)⁴. At unchanged temperature, doubling radius gives four times the luminosity; at unchanged radius, doubling temperature gives sixteen times the luminosity.',
          note: 'A spherical effective-temperature/bolometric-luminosity relationship, not a stellar evolution solver. The solar temperature normalization is 5772 K. Both axes are logarithmic and temperature decreases to the right, following H–R diagram convention. Guides hold radius fixed; they are not evolutionary tracks or a main-sequence population. A cool large star can emit much more than a hot compact star. Arbitrary radius/temperature combinations are mathematical comparisons, not guarantees of a stable star. Age, mass, composition and evolutionary history are not uniquely determined here. Luminosity is total emitted power, not apparent brightness at Earth; distance and dust are omitted. Markers are not physical star sizes or colors.',
          legend: [{ label: 'Blue: selected constant-radius guide', color: colors.blue }, { label: 'Gold: selected star parameters', color: colors.gold }, { label: 'Teal: solar reference', color: colors.teal }],
          sources: [{ label: 'Ohio State Astronomy: the H–R diagram', url: 'https://www.astronomy.ohio-state.edu/pogge.1/Ast162/Unit1/hrdiag.html' }, { label: 'IAU: nominal solar conversion constants', url: 'https://arxiv.org/abs/1510.07674' }] };
      },
    },
    'earth.3.ecology-earth': {
      title: 'Equal annual rain can give different dry seasons',
      instructions: 'Keep annual rainfall fixed while changing its timing. Compare soil-water storage and actual evapotranspiration with monthly demand.',
      initial: { seasonal: true, capacity: 150, demand: 100, month: 7 },
      controls: [{ key: 'seasonal', label: 'Concentrate rain into four months', type: 'toggle' }, { key: 'capacity', label: 'Soil-water storage capacity', min: 50, max: 300, step: 50, unit: 'mm' }, { key: 'demand', label: 'Monthly evapotranspiration demand', min: 50, max: 150, step: 25, unit: 'mm' }, { key: 'month', label: 'Inspect month', min: 1, max: 12, step: 1 }],
      calculate(s) {
        let stored = 0, totalET = 0, totalDrainage = 0;
        const records = Array.from({ length: 12 }, (_, i) => {
          const rain = s.seasonal ? i < 4 ? 300 : 0 : 100, available = stored + rain, drainage = Math.max(0, available - s.capacity), filled = Math.min(s.capacity, available), actualET = Math.min(s.demand, filled);
          stored = filled - actualET; totalET += actualET; totalDrainage += drainage;
          return { rain, stored, drainage, actualET, unmet: s.demand - actualET };
        });
        const selected = records[s.month - 1], dryMonths = records.filter(row => row.unmet > 0).length;
        return { data: { records, selected, totalET, totalDrainage, stored, dryMonths, totalRain: 1200 },
          readout: (s.seasonal ? 'Four rainy months' : 'Even monthly rain') + ', capacity ' + s.capacity + ' mm, monthly demand ' + s.demand + ' mm. Both patterns total 1200 mm/year. Month ' + s.month + ': rain ' + selected.rain + ', actual ET ' + selected.actualET + ', unmet demand ' + selected.unmet + ', end-month soil water ' + selected.stored + ' mm. Year balance: 1200 = ET ' + totalET + ' + drainage ' + totalDrainage + ' + final storage ' + stored + ' mm. Demand is unmet in ' + dryMonths + ' months.',
          note: 'An invented one-bucket water balance, not a biome classifier, irrigation recommendation or reproduction of NOAA’s operational model. Storage starts empty. Within each model month, rain fills the bucket, excess immediately drains out, then evapotranspiration removes up to the stated demand. This coarse ordering is an explicit approximation; real rain and ET vary within a month. Depths are water amounts per area, not soil thickness. ET combines evaporation and transpiration. Demand is prescribed, not estimated from temperature or vegetation. Snow, roots, groundwater return, infiltration limits, nutrients, fire and species adaptation are omitted. Annual rain alone cannot establish ecological water availability; soil storage and timing matter. Month numbers do not specify a hemisphere or real site.',
          legend: [{ label: 'Blue bars: monthly rain', color: colors.blue }, { label: 'Gold line: actual monthly ET', color: colors.gold }, { label: 'Teal line: end-month storage', color: colors.teal }],
          sources: [{ label: 'NOAA CPC: soil-moisture water-balance modeling', url: 'https://www.cpc.ncep.noaa.gov/soilmst/descrip.shtml' }] };
      },
    },
    'earth.3.climate-sci': {
      title: 'A warmer surface can still balance space',
      instructions: 'Change reflected sunlight and infrared absorption. Compare surface emission with the energy that actually escapes to space at equilibrium.',
      initial: { albedo: 30, infrared: 80, solar: 1400 },
      controls: [{ key: 'albedo', label: 'Reflected sunlight (albedo)', min: 0, max: 80, step: 10, unit: '%' }, { key: 'infrared', label: 'Layer infrared absorptivity/emissivity', min: 0, max: 100, step: 10, unit: '%' }, { key: 'solar', label: 'Incident solar flux before spherical averaging', min: 1000, max: 1600, step: 100, unit: 'W/m²' }],
      calculate(s) {
        const sigma = 5.670374419e-8, epsilon = s.infrared / 100, absorbed = s.solar * (1 - s.albedo / 100) / 4;
        const emitted = absorbed / (1 - epsilon / 2), downward = epsilon * emitted / 2, direct = (1 - epsilon) * emitted;
        const temperature = (emitted / sigma) ** .25, bare = (absorbed / sigma) ** .25, atmosphere = epsilon ? temperature / 2 ** .25 : null;
        return { data: { absorbed, emitted, downward, direct, upward: downward, outgoing: direct + downward, temperature, celsius: temperature - 273.15, bare, atmosphere },
          readout: 'Albedo ' + s.albedo + '%, infrared absorptivity ' + s.infrared + '%, solar flux ' + s.solar + ' W/m²: surface ' + numberText(temperature) + ' K (' + numberText(temperature - 273.15) + '°C), versus ' + numberText(bare) + ' K without infrared absorption. Absorbed sunlight ' + numberText(absorbed) + ' W/m² equals outgoing ' + numberText(direct + downward) + ' W/m². Surface emission ' + numberText(emitted) + ' balances sunlight plus downward infrared ' + numberText(downward) + '.',
          note: 'A single-layer grey radiative-equilibrium teaching model, not a climate forecast or CO₂-to-temperature calculator. Incoming sunlight is averaged over a sphere by dividing by four; reflected energy leaves before the modeled surface absorption. The atmosphere is transparent to this incoming radiation, absorbs a fixed infrared fraction ε, and emits infrared upward and downward. Surface emissivity is one. At ε=0, layer temperature is unconstrained by this radiative balance and is represented as unavailable, not zero kelvin. Internal radiative exchange does not create energy or mean that net heat flows from cold to hot. Clouds, convection, latent heat, wavelength detail, feedbacks, heat capacity and regional variations are omitted. The controls are independent assumptions, not a calibrated mapping from greenhouse-gas concentration.',
          legend: [{ label: 'Gold: absorbed sunlight', color: colors.gold }, { label: 'Blue: surface infrared', color: colors.blue }, { label: 'Coral: layer infrared', color: colors.coral }],
          sources: [{ label: 'UBC: single-layer imperfect greenhouse model', url: 'https://c21.phas.ubc.ca/article/simple-earth-climate-model-single-layer-imperfect-greenhouse-atmosphere/' }] };
      },
    },
    'earth.3.space-exploration': {
      title: 'Rocket velocity change depends on mass ratio',
      instructions: 'Vary dry mass, propellant and exhaust speed. Burn part of the propellant and track the vehicle mass, expelled mass and ideal velocity change.',
      initial: { dry: 2, propellant: 8, exhaust: 3, burn: 50 },
      controls: [{ key: 'dry', label: 'Dry vehicle and payload mass', min: 1, max: 10, step: 1, unit: 't' }, { key: 'propellant', label: 'Initial propellant mass', min: 0, max: 30, step: 1, unit: 't' }, { key: 'exhaust', label: 'Effective exhaust speed', min: 1, max: 5, step: .5, unit: 'km/s' }, { key: 'burn', label: 'Fraction of initial propellant expelled', min: 0, max: 100, step: 25, unit: '%' }],
      calculate(s) {
        const initial = s.dry + s.propellant, expelled = s.propellant * s.burn / 100, remaining = initial - expelled, ratio = initial / remaining;
        const delta = s.exhaust * Math.log(ratio), full = s.exhaust * Math.log(initial / s.dry);
        return { data: { initial, expelled, remaining, ratio, delta, full, propellantLeft: s.propellant - expelled },
          readout: 'Dry mass ' + s.dry + ' t, initial propellant ' + s.propellant + ' t, effective exhaust speed ' + s.exhaust + ' km/s, burn ' + s.burn + '%. Initial mass ' + initial + ' t = remaining vehicle ' + numberText(remaining) + ' t + expelled propellant ' + numberText(expelled) + ' t. Ideal Δv = vₑ ln(m₀/m) = ' + numberText(delta) + ' km/s. Expelling all propellant would give ' + numberText(full) + ' km/s.',
          note: 'The ideal rocket equation for a single nonrelativistic, constant-effective-exhaust-speed burn in one direction, without external forces. Δv is a velocity change, not altitude, range or proof of reaching orbit; the vehicle may already have velocity. Gravity and aerodynamic losses, steering, finite thrust, staging and structural feasibility are excluded. Propellant includes all expelled reaction mass, not only chemical fuel. Exhaust is expelled relative to the vehicle; no surrounding air is needed for momentum exchange. Dry mass remains on board throughout. Zero propellant or zero burn gives zero Δv. This accounting model is not an engine construction or launch plan.',
          legend: [{ label: 'Blue: dry vehicle and payload', color: colors.blue }, { label: 'Gold: propellant on board', color: colors.gold }, { label: 'Coral: expelled propellant', color: colors.coral }],
          sources: [{ label: 'NASA Glenn: ideal rocket equation', url: 'https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/ideal-rocket-equation/' }] };
      },
    },
    'earth.2.geology': {
      title: 'Read the relative motion at a boundary',
      instructions: 'Move two markers attached to neighboring plates. Compare separation across the boundary with sliding along it.',
      initial: { boundary: 'divergent', steps: 3 },
      controls: [{ key: 'boundary', label: 'Relative plate motion', options: [{ value: 'divergent', label: 'Divergent: move apart' }, { value: 'convergent', label: 'Convergent: move together' }, { value: 'transform', label: 'Transform: slide past' }] }, { key: 'steps', label: 'Motion steps', min: 0, max: 6, step: 1 }],
      calculate(s) {
        const t = s.steps / 6, direction = s.boundary === 'divergent' ? 1 : -1;
        const a = s.boundary === 'transform' ? [-1, t] : [-1 - direction * t / 2, 0], b = s.boundary === 'transform' ? [1, -t] : [1 + direction * t / 2, 0];
        const gap = b[0] - a[0], offset = Math.abs(b[1] - a[1]);
        const outcome = { divergent: 'Separation increases', convergent: 'Separation decreases', transform: 'Sliding offset increases' }[s.boundary];
        return { data: { a, b, gap, offset, outcome },
          readout: s.boundary + ' boundary, ' + s.steps + ' motion steps. Across-boundary marker separation ' + numberText(gap) + '; along-boundary offset ' + numberText(offset) + ' in arbitrary diagram units. ' + (s.steps ? outcome + '.' : 'Markers are at their initial positions; advance the steps to see the selected motion.'),
          note: 'A top-down kinematic model of marker positions, not a cross-section or deformation simulation. Open rings show starting positions; solid markers are attached to plates. The central dashed line indicates boundary direction, not an opening filled with empty space. Divergent motion can form new crust at spreading centers; convergent motion may involve subduction or continental collision; transform motion slides plates past each other. These outcomes depend on setting and are not simulated here. Earthquakes can occur at all three boundary types. Marker steps and distances are arbitrary, not real rates, hazard predictions or a model of the mantle’s flow.',
          legend: [{ label: 'Blue: marker on plate A', color: colors.blue }, { label: 'Gold: marker on plate B', color: colors.gold }, { label: 'Open rings: starting positions', color: colors.ink }],
          sources: [{ label: 'USGS: understanding plate motions', url: 'https://pubs.usgs.gov/gip/dynamic/understanding.html' }] };
      },
    },
    'earth.2.oceans': {
      title: 'Why spring and neap tidal ranges differ',
      instructions: 'Change the Sun–Moon angle and inspect a direction around Earth. Compare the combined idealized tidal profile and its high-to-low range.',
      initial: { moon: 0, observer: 0 },
      controls: [{ key: 'moon', label: 'Sun–Moon angle at Earth', min: 0, max: 180, step: 15, unit: '°' }, { key: 'observer', label: 'Direction around Earth', min: 0, max: 345, step: 15, unit: '°' }],
      calculate(s) {
        const rad = Math.PI / 180, height = angle => Math.cos(2 * (angle - s.moon) * rad) + .4 * Math.cos(2 * angle * rad);
        const amplitude = Math.sqrt(1.16 + .8 * Math.cos(2 * s.moon * rad)), local = height(s.observer), samples = Array.from({ length: 73 }, (_, i) => height(i * 5));
        const phase = s.moon === 0 || s.moon === 180 ? 'Spring alignment' : s.moon === 90 ? 'Neap alignment' : 'Intermediate';
        return { data: { amplitude, range: 2 * amplitude, local, samples, phase },
          readout: 'Sun–Moon angle ' + s.moon + '°: ' + phase + '. Idealized high-to-low range ' + numberText(2 * amplitude) + ' relative units. Direction ' + s.observer + '° has height ' + numberText(local) + ' relative to the model’s mean. At 0° and 180° the range is 2.8; at 90° it is 1.2, not zero.',
          note: 'An idealized equilibrium-style angular profile, not a tide table or a prediction for any coast. Lunar and solar second-harmonic terms are cos(2(θ−φ)) and 0.4cos(2θ); the solar weight is an approximate teaching value. Units are relative, not metres. The graph samples directions around Earth at fixed alignment, not elapsed hours; it does not assert a universal daily tide pattern. Real tides depend on coastlines, depth, resonance, orbital distances, inclination and timing lags. Spring refers to a larger tidal range, not the season. Bodies, separations and the observer marker are not drawn to physical scale. This activity is not suitable for boating or coastal safety decisions.',
          legend: [{ label: 'Blue: combined angular tide profile', color: colors.blue }, { label: 'Gold: inspected direction', color: colors.gold }],
          sources: [{ label: 'NOAA: spring and neap tides', url: 'https://oceanservice.noaa.gov/facts/springtide.html' }, { label: 'NOAA: relative lunar and solar tidal effects', url: 'https://tidesandcurrents.noaa.gov/restles3.html' }] };
      },
    },
    'earth.2.atmosphere': {
      title: 'One cold day is not a climate average',
      instructions: 'Compare a day with an invented 30-year reference for that calendar date. Change the reference climate and today’s departure independently.',
      initial: { shift: 2, departure: -4, year: 15 },
      controls: [{ key: 'shift', label: 'Shift all reference years', min: 0, max: 4, step: 1, unit: '°C' }, { key: 'departure', label: 'Today’s departure from the reference', min: -8, max: 8, step: 1, unit: '°C' }, { key: 'year', label: 'Inspect reference year', min: 1, max: 30, step: 1 }],
      calculate(s) {
        const records = Array.from({ length: 30 }, (_, i) => 10 + s.shift + [-2, -1, 0, 1, 2][i % 5]), mean = records.reduce((sum, value) => sum + value, 0) / 30, today = mean + s.departure;
        return { data: { records, mean, today, selected: records[s.year - 1] },
          readout: 'Thirty invented daily mean temperatures for the same calendar date average ' + mean + '°C. Reference year ' + s.year + ': ' + records[s.year - 1] + '°C. Today, outside that reference period: ' + today + '°C, a departure of ' + s.departure + '°C. Changing today does not rewrite the reference observations.',
          note: 'An arithmetic teaching example, not observed climate data, a forecast or a climate-change attribution model. The 30 points are daily means on the same date in 30 different invented years, not 30 consecutive days. Climate normals commonly summarize 30-year records; actual products use quality control and may smooth daily normals. Climate includes variability and many variables, not just a mean. The shift control translates the entire invented reference record, not a warming rate or evidence of a real trend. A single unusually cold or hot day is compatible with many long-term climates.',
          legend: [{ label: 'Blue: reference observations', color: colors.blue }, { label: 'Teal: 30-year mean', color: colors.teal }, { label: 'Gold: today / inspected year', color: colors.gold }],
          sources: [{ label: 'NOAA NCEI: climate normals', url: 'https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals' }] };
      },
    },
    'earth.2.environment': {
      title: 'Stop new pollution and track existing waste',
      instructions: 'Compare reducing new waste with collecting waste already in the environment. Track the remaining stock and the material moved into managed storage.',
      initial: { prevention: 50, cleanup: 4, steps: 4 },
      controls: [{ key: 'prevention', label: 'Reduce the incoming waste source', min: 0, max: 100, step: 25, unit: '%' }, { key: 'cleanup', label: 'Collection capacity per step', min: 0, max: 8, step: 1 }, { key: 'steps', label: 'Elapsed steps', min: 0, max: 8, step: 1 }],
      calculate(s) {
        const inflow = 8 * (1 - s.prevention / 100), history = [20]; let stock = 20, collected = 0;
        for (let i = 0; i < s.steps; i++) { const removal = Math.min(s.cleanup, stock + inflow); stock += inflow - removal; collected += removal; history.push(stock); }
        const added = inflow * s.steps, avoided = (8 - inflow) * s.steps;
        return { data: { inflow, history, stock, collected, added, avoided },
          readout: 'Source reduction ' + s.prevention + '%, collection capacity ' + s.cleanup + ', steps ' + s.steps + ': new waste ' + inflow + ' per step, ' + added + ' added in total. Environmental stock ' + stock + '; collected into managed storage ' + collected + '. Actual material balance: 20 + ' + added + ' = ' + stock + ' + ' + collected + '. Avoided generation compared with the unreduced source: ' + avoided + '.',
          note: 'An invented, perfectly mixed waste-stock accounting model, not a cleanup plan or toxicity assessment. Twenty arbitrary material units are initially present; the unreduced source adds eight per step. Each step adds new waste before collection, capped by available material. Collected waste is transferred to managed storage, not destroyed; later treatment and disposal are outside this model. Avoided generation is a counterfactual comparison, not an existing physical store. There is no natural decay, downstream transport, variable collection efficiency, cost or ecological response. Preventing new waste does not by itself remove legacy waste. Real interventions require identifying the pollutant and setting-specific evidence.',
          legend: [{ label: 'Blue: waste remaining in environment', color: colors.blue }, { label: 'Gold: inspected endpoint', color: colors.gold }],
          sources: [{ label: 'US EPA: pollution prevention and source reduction', url: 'https://www.epa.gov/p2/learn-about-pollution-prevention' }] };
      },
    },
    'earth.2.planets': {
      title: 'Compare worlds on one size scale',
      instructions: 'Choose two planets. Their circular outlines share a diameter scale; compare the diameter ratio with the much larger change in spherical volume.',
      initial: { first: '2', second: '4' },
      controls: ['first', 'second'].map((key, i) => ({ key, label: i ? 'Planet B' : 'Planet A', options: ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'].map((label, index) => ({ value: String(index), label })) })),
      calculate(s) {
        const names = ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'], diameters = [4879, 12104, 12756, 6792, 142984, 120536, 51118, 49528];
        const a = Number(s.first), b = Number(s.second), ratio = diameters[b] / diameters[a], volumeRatio = ratio ** 3, largest = Math.max(diameters[a], diameters[b]);
        return { data: { names: [names[a], names[b]], diameters: [diameters[a], diameters[b]], radii: [diameters[a], diameters[b]].map(d => 72 * d / largest), ratio, volumeRatio },
          readout: 'A: ' + names[a] + ', diameter ' + diameters[a] + ' km. B: ' + names[b] + ', diameter ' + diameters[b] + ' km. B/A diameter ≈ ' + smallLengthText(ratio) + '; spherical volume ≈ ' + smallLengthText(volumeRatio) + '. Both outlines share one scale.',
          note: 'NASA JPL reference diameters, rounded in kilometres. Outlines compare physical diameters, not distances, mass, density or apparent sizes in the sky. Both are rescaled together when the pair changes. Spherical volume scales as diameter cubed; real planets are not perfect spheres, so the volume ratio is an approximation based on the listed diameters. A larger volume does not imply the same ratio of mass. Rings, atmospheres and surface features are not drawn; colors identify A and B, not appearance. Gas and ice giants do not have Earth-like solid surfaces.',
          legend: [{ label: 'Blue: planet A', color: colors.blue }, { label: 'Gold: planet B', color: colors.gold }],
          sources: [{ label: 'NASA JPL: Solar System sizes and distances', url: 'https://www.jpl.nasa.gov/_edu/pdfs/scaless_reference.pdf' }] };
      },
    },
    'earth.2.stars': {
      title: 'A brighter-looking star need not emit more',
      instructions: 'Change emitted light and distance independently. Compare received light at different distances from the same idealized star.',
      initial: { luminosity: 4, distance: 2 },
      controls: [{ key: 'luminosity', label: 'Emitted light L (relative units)', min: 1, max: 8, step: 1 }, { key: 'distance', label: 'Distance d (relative units)', min: 1, max: 8, step: 1 }],
      calculate(s) {
        const flux = s.luminosity / s.distance ** 2, samples = Array.from({ length: 8 }, (_, i) => s.luminosity / (i + 1) ** 2);
        return { data: { flux, samples, spreadingArea: s.distance ** 2 },
          readout: 'Emitted light L=' + s.luminosity + ', distance d=' + s.distance + ': received light L/d²=' + numberText(flux) + ' relative units. Light is spread across ' + s.distance ** 2 + ' times the area at distance 1. Doubling distance would reduce received light to one quarter, without changing emission.',
          note: 'An ideal point source emitting equally in all directions through transparent space. Received light means energy per receiving area per time, normalized so L=1 at d=1 gives 1; the physical formula is L/(4πd²). Relative units remove the common 4π factor. This is flux, not the logarithmic magnitude scale or the surface brightness of a resolved image. Dust absorption, atmosphere, variable stars and cosmological effects are excluded. Emitted light is independent of the distance control. The Sun is one star among many in the Milky Way; apparent brightness alone cannot establish another star’s luminosity or distance.',
          legend: [{ label: 'Blue: flux versus distance', color: colors.blue }, { label: 'Gold: selected observation', color: colors.gold }],
          sources: [{ label: 'NASA: light and the inverse-square relationship', url: 'https://imagine.gsfc.nasa.gov/features/yba/M31_velocity/lightcurve/more.html' }] };
      },
    },
    'earth.0.weather': {
      title: 'Weather has more than one measurement',
      instructions: 'Choose an example day and compare temperature, rain, snowfall or wind across four invented observations.',
      initial: { day: '0', metric: 'temperature' },
      controls: [{ key: 'day', label: 'Example day', options: ['Dry and bright', 'Rain and breeze', 'Snow and breeze', 'Dry and windy'].map((label, i) => ({ value: String(i), label: 'Day ' + (i + 1) + ': ' + label })) },
        { key: 'metric', label: 'Compare a measurement', options: [{ value: 'temperature', label: 'Temperature (°C)' }, { value: 'rain', label: 'Rain (mm)' }, { value: 'snow', label: 'New snowfall (cm)' }, { value: 'wind', label: 'Wind speed (km/h)' }] }],
      calculate(s) {
        const observations = [{ name: 'Dry and bright', temperature: 20, rain: 0, snow: 0, wind: 8 }, { name: 'Rain and breeze', temperature: 8, rain: 3, snow: 0, wind: 20 }, { name: 'Snow and breeze', temperature: -3, rain: 0, snow: 3, wind: 10 }, { name: 'Dry and windy', temperature: 15, rain: 0, snow: 0, wind: 36 }];
        const units = { temperature: '°C', rain: 'mm', snow: 'cm', wind: 'km/h' }, names = { temperature: 'Temperature', rain: 'Rain', snow: 'New snowfall', wind: 'Wind speed' };
        const selected = observations[Number(s.day)], values = observations.map(row => row[s.metric]);
        return { data: { observations, selected, values, unit: units[s.metric], name: names[s.metric], minimum: s.metric === 'temperature' ? -5 : 0, maximum: s.metric === 'temperature' ? 25 : s.metric === 'wind' ? 40 : 4 },
          readout: 'Day ' + (Number(s.day) + 1) + ': ' + selected.name + '. Temperature ' + selected.temperature + '°C, rain ' + selected.rain + ' mm, new snowfall ' + selected.snow + ' cm, wind ' + selected.wind + ' km/h. Comparing ' + names[s.metric] + ': ' + values.join(', ') + ' ' + units[s.metric] + ' for days 1–4.',
          note: 'Invented observations for comparison, not live weather, a forecast or a causal simulation. Temperature and wind are sample readings; rain and new snowfall are totals over each example day. Conditions such as wind and rain can occur together. Snow depth in centimetres and rainfall depth in millimetres are different measurements; this activity does not convert snowfall to liquid-water equivalent. A single surface-temperature reading cannot determine precipitation type. Four examples do not establish a climate trend.',
          legend: [{ label: 'Gold: selected day', color: colors.gold }, { label: 'Blue: other days', color: colors.blue }],
          sources: [{ label: 'US National Weather Service: weather observations', url: 'https://www.weather.gov/abq/observations' }] };
      },
    },
    'earth.1.solar-system': {
      title: 'Planet order is not a distance scale',
      instructions: 'Select a planet and switch between an order diagram and a linear distance scale. Watch the inner planets crowd together.',
      initial: { planet: '2', scale: 'order' },
      controls: [{ key: 'planet', label: 'Selected planet', options: ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'].map((label, i) => ({ value: String(i), label })) }, { key: 'scale', label: 'Diagram spacing', options: [{ value: 'order', label: 'Order only: equal spacing' }, { value: 'distance', label: 'Linear Sun distance (AU)' }] }],
      calculate(s) {
        const names = ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'], distances = [.39, .72, 1, 1.52, 5.2, 9.54, 19.2, 30.06], index = Number(s.planet);
        const positions = distances.map((distance, i) => s.scale === 'distance' ? distance / 30.06 : (i + 1) / 8);
        return { data: { names, distances, positions, index, name: names[index], distance: distances[index], group: index < 4 ? 'Rocky planet' : index < 6 ? 'Gas giant' : 'Ice giant' },
          readout: names[index] + ' is planet ' + (index + 1) + ' from the Sun, at approximately ' + distances[index] + ' AU. ' + (s.scale === 'order' ? 'Equal spacing preserves order but does not represent distances.' : 'Linear spacing represents approximate Sun distances; inner planets are crowded near the origin.'),
          note: 'Approximate reference distances from NASA JPL, not current positions. One AU is about 150 million kilometres, close to Earth’s mean Sun distance. Actual orbits are elliptical and planets are not arranged along one line. Marker sizes and colors are diagram symbols, not planet diameter or surface appearance. The equal-spacing view is ordinal only. The linear view measures from the Sun, not from Earth; Neptune is not the edge of the Solar System.',
          legend: [{ label: 'Gold: selected planet', color: colors.gold }, { label: 'Blue: other planet positions', color: colors.blue }],
          sources: [{ label: 'NASA JPL: Solar System sizes and distances', url: 'https://www.jpl.nasa.gov/_edu/pdfs/scaless_reference.pdf' }] };
      },
    },
    'earth.0.land-water': {
      title: 'Where will the raindrop go?',
      instructions: 'Choose where rain lands. Advance its downhill route, then add a basin and compare where it stops.',
      initial: { start: 4, basin: false, steps: 0 },
      controls: [{ key: 'start', label: 'Rain position', min: 0, max: 6, step: 1 }, { key: 'basin', label: 'Add a central basin', type: 'toggle' }, { key: 'steps', label: 'Downhill steps', min: 0, max: 6, step: 1 }],
      calculate(s) {
        const heights = s.basin ? [0, 3, 5, 1, 5, 3, 0] : [0, 2, 4, 6, 4, 2, 0], path = [s.start];
        while (true) {
          const here = path[path.length - 1];
          const lower = [here - 1, here + 1].filter(i => i >= 0 && i < 7 && heights[i] < heights[here]);
          if (!lower.length) break;
          lower.sort((a, b) => heights[a] - heights[b] || a - b); path.push(lower[0]);
        }
        const traveled = path.slice(0, s.steps + 1), position = traveled[traveled.length - 1], stopped = traveled.length === path.length;
        const status = !stopped ? 'Still on the slope' : position === 0 || position === 6 ? 'Reached the sea' : 'Stopped in the basin';
        return { data: { heights, path, traveled, position, stopped, status },
          readout: 'Rain at position ' + s.start + ', ' + (s.basin ? 'basin' : 'ridge') + ' landscape, ' + s.steps + ' requested steps: ' + traveled.join(' → ') + '. ' + status + '. Completed downhill moves: ' + (traveled.length - 1) + '.',
          note: 'An invented one-dimensional surface route, not a flood forecast. Each move goes to a strictly lower neighboring position; equal downhill choices go left by a demo convention. Real divides can send water in different directions. Heights are relative, not metres. A closed depression stops this route, but real basins may fill, overflow, evaporate or drain underground. This model excludes those processes, infiltration, erosion and time-dependent flow. Steps stop advancing when there is no lower neighbor.',
          legend: [{ label: 'Teal: land profile', color: colors.teal }, { label: 'Blue: traveled route', color: colors.blue }, { label: 'Gold ring: rain starts here', color: colors.gold }],
          sources: [{ label: 'USGS: watersheds and drainage basins', url: 'https://www.usgs.gov/water-science-school/science/watersheds-and-drainage-basins' }] };
      },
    },
    'earth.1.water-cycle': {
      title: 'Follow water without losing any',
      instructions: 'Move part of a surface-water store through one possible route. Change how much travels and how much soaks into the ground, then compare all five stores.',
      initial: { amount: 6, infiltration: 50, stage: 3 },
      controls: [{ key: 'amount', label: 'Water units taking this route', min: 0, max: 8, step: 1 }, { key: 'infiltration', label: 'Share soaking into the ground', min: 0, max: 100, step: 25, unit: '%' },
        { key: 'stage', label: 'Route stage', min: 0, max: 6, step: 1 }],
      calculate(s) {
        const stores = { surface: 20, vapour: 0, cloud: 0, land: 0, ground: 0 }, soaked = s.amount * s.infiltration / 100;
        if (s.stage >= 1) { stores.surface -= s.amount; stores.vapour += s.amount; }
        if (s.stage >= 2) { stores.vapour -= s.amount; stores.cloud += s.amount; }
        if (s.stage >= 3) { stores.cloud -= s.amount; stores.land += s.amount; }
        if (s.stage >= 4) { stores.land -= soaked; stores.ground += soaked; }
        if (s.stage >= 5) { stores.surface += stores.land; stores.land = 0; }
        if (s.stage >= 6) { stores.surface += stores.ground; stores.ground = 0; }
        const names = ['Surface water at the start', 'Evaporation: liquid to vapour', 'Condensation: liquid droplets form', 'Rain reaches land', 'Some water infiltrates the ground', 'Remaining surface water runs off', 'Groundwater returns to surface water'];
        return { data: { stores, soaked, total: Object.values(stores).reduce((a, b) => a + b, 0), name: names[s.stage] },
          readout: 'Route amount ' + s.amount + ', infiltration ' + s.infiltration + '%, stage ' + s.stage + ': ' + names[s.stage] + '. Surface ' + numberText(stores.surface) + ', vapour ' + numberText(stores.vapour) + ', cloud ' + numberText(stores.cloud) + ', land surface ' + numberText(stores.land) + ', groundwater ' + numberText(stores.ground) + '. Total remains 20 water units.',
          note: 'A closed bookkeeping example, not Earth’s actual reservoir sizes or rates. Units are arbitrary water amounts, not indivisible droplets. Water vapour is invisible gas; cloud droplets are liquid. This chosen route omits cloud ice and snow. Evaporation needs energy; condensation releases energy; gravity helps precipitation and downhill flow. Steps are separated to inspect them, but real processes occur concurrently, have many branches and need not begin at surface water. Infiltration can remain in soil or become groundwater; here it enters one combined ground store. Plants, ice storage, recharge delays and many return paths are omitted. No water is created or destroyed.',
          legend: [{ label: 'Blue: water stores', color: colors.blue }, { label: 'Gold: current transfer', color: colors.gold }],
          sources: [{ label: 'USGS Water Science School: water cycle', url: 'https://www.usgs.gov/special-topics/water-science-school/water-cycle' }] };
      },
    },
    'earth.1.rocks': {
      title: 'Choose a process, not a compulsory cycle',
      instructions: 'Choose starting material and a process. Compare the resulting material, or identify why that direct route is outside this simple model.',
      initial: { material: 'igneous', process: 'weathering' },
      controls: [{ key: 'material', label: 'Starting material', options: ['igneous', 'sedimentary', 'metamorphic', 'sediment', 'magma'].map(value => ({ value, label: value[0].toUpperCase() + value.slice(1) })) },
        { key: 'process', label: 'Process', options: [{ value: 'weathering', label: 'Weather and erode' }, { value: 'consolidate', label: 'Compact and cement' }, { value: 'metamorphism', label: 'Heat/pressure without melting' }, { value: 'melt', label: 'Melt' }, { value: 'cool', label: 'Cool and crystallize' }] }],
      calculate(s) {
        const rock = ['igneous', 'sedimentary', 'metamorphic'].includes(s.material);
        let result = null;
        if (s.process === 'weathering' && rock) result = 'sediment';
        if (s.process === 'consolidate' && s.material === 'sediment') result = 'sedimentary';
        if (s.process === 'metamorphism' && rock) result = 'metamorphic';
        if (s.process === 'melt' && s.material !== 'magma') result = 'magma';
        if (s.process === 'cool' && s.material === 'magma') result = 'igneous';
        const processes = { weathering: 'weathering and erosion', consolidate: 'compaction and cementation', metamorphism: 'heat/pressure without melting', melt: 'melting', cool: 'cooling and crystallization' };
        return { data: { result, valid: result !== null, processName: processes[s.process] },
          readout: s.material + ' + ' + processes[s.process] + ': ' + (result ? result + '. ' + (s.process === 'metamorphism' ? 'The rock changes while remaining solid.' : s.process === 'melt' ? 'Molten material is not metamorphic rock.' : '') : 'No direct route is included for this pair. That is a limit of this model, not a claim that conditions can have no effect.'),
          note: 'Rock groups describe origin, not a unique appearance; the textures are schematic cues, not an identification key. Weathering can make sediment; compaction/cementation can form sedimentary rock; solid-state change can form metamorphic rock; melting makes molten material and crystallization forms igneous rock. Any rock type can weather, metamorphose or melt under suitable conditions. A rock can change within the metamorphic group without changing its group name. This model omits intermediate steps, chemical sedimentary rocks, fluids, transport/deposition detail and timescales. Sediment is not the same as soil, which also includes water, air and organic material.',
          legend: [{ label: 'Blue: starting material', color: colors.blue }, { label: 'Gold: chosen process', color: colors.gold }, { label: 'Teal: modeled product', color: colors.teal }],
          sources: [{ label: 'USGS: many pathways through the rock cycle', url: 'https://www.usgs.gov/educational-resources/whats-new-weeks-9-12' }] };
      },
    },
    'cs.4.security': {
      title: 'A reused XOR pad cancels out',
      instructions: 'Change either four-bit message or the shared pad. Compare the XOR of the ciphertexts with the XOR of the messages.',
      initial: { first: 5, second: 9, key: 6 },
      controls: [{ key: 'first', label: 'Message 1', min: 0, max: 15, step: 1 }, { key: 'second', label: 'Message 2', min: 0, max: 15, step: 1 }, { key: 'key', label: 'Pad reused for both messages', min: 0, max: 15, step: 1 }],
      calculate(s) {
        const c1 = s.first ^ s.key, c2 = s.second ^ s.key, difference = c1 ^ c2;
        return { data: { c1, c2, difference, messageXor: s.first ^ s.second },
          readout: 'Messages ' + s.first + ' and ' + s.second + ', shared pad ' + s.key + ': ciphertexts ' + c1 + ' and ' + c2 + '. Their XOR is ' + difference + ', exactly the XOR of the two messages. The reused pad cancels.',
          note: 'Four-bit teaching arithmetic, not a usable encryption system. For C1=M1 XOR K and C2=M2 XOR K, C1 XOR C2=M1 XOR M2. This exposes a relationship, not necessarily both complete messages; knowing one message reveals the other. A true one-time pad requires a secret, uniformly random pad as long as the message, never reused. The displayed, manually chosen pad does not meet that security model. Encryption alone does not provide integrity. These claims concern pad reuse, not a blanket ban on reusing keys in every cryptographic construction.',
          legend: [{ label: 'Blue: plaintext', color: colors.blue }, { label: 'Gold: reused pad', color: colors.gold }, { label: 'Teal: ciphertext', color: colors.teal }],
          sources: [{ label: 'Stanford CS144: one-time pads and reuse', url: 'https://www.scs.stanford.edu/10au-cs144/notes/l15.pdf' }] };
      },
    },
    'cs.4.systems': {
      title: 'An address is not enough for valid access',
      instructions: 'Select an array index and attempt a read or write. Compare a live element, the one-past position and an expired object.',
      initial: { index: 1, alive: true, action: 'write', value: 25 },
      controls: [{ key: 'index', label: 'Array index', min: -1, max: 4, step: 1 }, { key: 'alive', label: 'Array lifetime is active', type: 'toggle' },
        { key: 'action', label: 'Attempted operation', options: [{ value: 'read', label: 'Read' }, { value: 'write', label: 'Write' }] }, { key: 'value', label: 'Value requested for a write', min: 0, max: 99, step: 1 }],
      calculate(s) {
        const formation = s.alive && s.index >= 0 && s.index <= 4, valid = s.alive && s.index >= 0 && s.index < 4;
        const values = s.alive ? [10, 20, 30, 40] : [null, null, null, null];
        if (valid && s.action === 'write') values[s.index] = s.value;
        const result = valid ? values[s.index] : null, address = formation ? '0x' + (4096 + 4 * s.index).toString(16) : null;
        const status = !s.alive ? 'Expired object' : s.index < 0 ? 'Outside the array' : s.index === 4 ? 'One-past: access forbidden' : 'Valid element access';
        return { data: { formation, valid, values, result, address, status },
          readout: s.action + ' at index ' + s.index + '; lifetime ' + (s.alive ? 'active' : 'ended') + '; requested write value ' + s.value + '. ' + status + '. ' + (valid ? 'Result ' + result + '.' : 'Operation refused by this teaching model; no value is read or written.') + (s.action === 'read' ? ' The write-value control is unused for reads.' : ''),
          note: 'A C11-style bounds/lifetime example, assuming a four-element array of four-byte integers at a fictional address. The four-byte size is an assumption, not a universal sizeof(int). Forming one-past a live array is allowed; dereferencing it is not. No pointer is formed outside the array/one-past range or after lifetime ends. The demo checks before access and never executes unsafe C; real invalid C access has undefined behavior, not a guaranteed clean error. Expired contents are shown as unavailable. Every control change starts a fresh illustrative array, not a persistent memory edit. Alignment, provenance details and concurrent access are omitted.',
          legend: [{ label: 'Blue: live array cells', color: colors.blue }, { label: 'Gold: selected valid element', color: colors.gold }, { label: 'Coral: refused access', color: colors.coral }],
          sources: [{ label: 'C11 draft: object lifetime and pointer arithmetic', url: 'https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf' }] };
      },
    },
    'cs.5.deep-learning': {
      title: 'Attention mixes values, not just scores',
      instructions: 'Change the scalar query and third value. Apply a causal mask to exclude the future position, then compare weights and the weighted output.',
      initial: { query: 1, third: 8, causal: false },
      controls: [{ key: 'query', label: 'Scalar query q', min: -3, max: 3, step: .5 }, { key: 'third', label: 'Third value', min: 0, max: 10, step: 1 }, { key: 'causal', label: 'Mask the future third position', type: 'toggle' }],
      calculate(s) {
        const keys = [-1, 0, 1], values = [2, 5, s.third], scores = keys.map(key => s.query * key);
        const allowed = [true, true, !s.causal], maximum = Math.max(...scores.filter((_, i) => allowed[i]));
        const exps = scores.map((score, i) => allowed[i] ? Math.exp(score - maximum) : 0), total = exps.reduce((a, b) => a + b, 0);
        const weights = exps.map(value => value / total), result = weights.reduce((sum, weight, i) => sum + weight * values[i], 0);
        return { data: { keys, values, scores, allowed, weights, result },
          readout: 'q=' + s.query + ', third value=' + s.third + ', causal mask ' + truthText(s.causal) + '. Weights ' + weights.map(value => numberText(value * 100) + '%').join(', ') + '; weighted output ' + numberText(result) + '.' + (s.causal ? ' The third value contributes zero because its position is masked.' : ''),
          note: 'One query and one attention head with scalar keys and values: dk=1, so the usual square-root scaling is 1. Softmax normalizes query–key scores, then weights multiply values. The query is at the second position; a causal mask excludes the third. Subtracting the largest allowed score before exponentiation improves numerical stability without changing softmax. Percentages are rounded and may not sum to exactly 100 on screen. No learned projections, training, multiple heads, residual blocks or language generation are simulated. Attention weights are not probabilities that statements are true, nor a complete explanation of a model’s reasoning.',
          legend: [{ label: 'Blue: allowed attention weights', color: colors.blue }, { label: 'Coral: masked position', color: colors.coral }, { label: 'Teal: weighted value output', color: colors.teal }],
          sources: [{ label: 'Attention Is All You Need, section 3.2', url: 'https://arxiv.org/html/1706.03762v7' }] };
      },
    },
    'cs.5.distributed': {
      title: 'Why two majorities must overlap',
      instructions: 'Select two replica sets with five-bit masks. Compare their actual intersection with the overlap guaranteed by their sizes.',
      initial: { first: 7, second: 28 },
      controls: [{ key: 'first', label: 'Set A mask (bits 0–4 select replicas 1–5)', min: 0, max: 31, step: 1 }, { key: 'second', label: 'Set B mask', min: 0, max: 31, step: 1 }],
      calculate(s) {
        const first = [], second = [], overlap = [];
        for (let i = 0; i < 5; i++) { if (s.first & (1 << i)) first.push(i + 1); if (s.second & (1 << i)) second.push(i + 1); if ((s.first & s.second) & (1 << i)) overlap.push(i + 1); }
        const lowerBound = Math.max(0, first.length + second.length - 5), majorities = first.length >= 3 && second.length >= 3;
        return { data: { first, second, overlap, lowerBound, majorities },
          readout: 'Masks A=' + s.first + ', B=' + s.second + '. Sets {' + first.join(',') + '} and {' + second.join(',') + '}; shared replicas {' + overlap.join(',') + '}. Sizes guarantee at least ' + lowerBound + ' shared replica(s); actual overlap ' + overlap.length + '. Both are majorities: ' + truthText(majorities) + '.',
          note: 'Fixed membership of five replicas. For any two sets, intersection size is at least |A|+|B|−5, bounded below by zero. Two sets of at least three therefore overlap. Smaller sets may still overlap, but their sizes alone may not guarantee it. An empty set is not a quorum. This set-theoretic property is necessary in many quorum protocols but does not by itself implement consensus or prove linearizability: terms, log rules, versions, failure assumptions and membership changes matter. No replicas, network traffic or commits are simulated.',
          legend: [{ label: 'Blue: set A', color: colors.blue }, { label: 'Gold: set B', color: colors.gold }, { label: 'Teal: intersection', color: colors.teal }], sources: [] };
      },
    },
    'cs.5.pl-theory': {
      title: 'Type-check before reducing the term',
      instructions: 'Apply an integer function to a chosen argument, then reveal substitution and arithmetic. A Boolean argument is rejected by this type rule.',
      initial: { argument: '5', offset: 1, stage: 2 },
      controls: [{ key: 'argument', label: 'Argument', options: ['0', '2', '5', 'true', 'false'].map(value => ({ value, label: value })) }, { key: 'offset', label: 'Integer added by the function', min: -2, max: 3, step: 1 }, { key: 'stage', label: 'Reduction stage', min: 0, max: 2, step: 1 }],
      calculate(s) {
        const valid = !['true', 'false'].includes(s.argument), result = valid ? Number(s.argument) + s.offset : null;
        const terms = ['(λx:Int. x + (' + s.offset + ')) ' + s.argument, s.argument + ' + (' + s.offset + ')', String(result)];
        return { data: { valid, result, terms: valid ? terms : [terms[0]], displayed: valid ? terms[s.stage] : 'Type error: expected Int', argumentType: valid ? 'Int' : 'Bool' },
          readout: 'Argument ' + s.argument + ', offset ' + s.offset + ', requested stage ' + s.stage + '. ' + (valid ? 'Type Int. ' + ['Apply the function.', 'Beta reduction substitutes the integer for x.', 'Arithmetic reduction gives ' + result + '.'][s.stage] : 'Bool does not match the Int parameter; the typed evaluator refuses reduction.'),
          note: 'A tiny simply typed lambda calculus with integer literals, Boolean literals and integer addition. There is no implicit Boolean-to-integer coercion. For these closed integer arguments, beta reduction substitutes without variable capture; addition then reduces to an integer. All displayed valid steps preserve Int. This example does not establish type safety for arbitrary languages, effects or implementations, and does not claim that all ill-typed untyped terms are unevaluable. Terms are rendered as text; no user code is evaluated.',
          legend: [{ label: 'Blue: typed term', color: colors.blue }, { label: 'Gold: current reduction stage', color: colors.gold }, { label: 'Coral: rejected application', color: colors.coral }], sources: [] };
      },
    },
    'cs.5.frontier': {
      title: 'A bounded check is not an unbounded proof',
      instructions: 'Check a counter’s safety rule across every increment/reset sequence up to a chosen depth. Compare a faulty boundary with its repair.',
      initial: { limit: 3, bound: 3, repaired: false },
      controls: [{ key: 'limit', label: 'Safety limit', min: 0, max: 5, step: 1 }, { key: 'bound', label: 'Search depth', min: 0, max: 6, step: 1 }, { key: 'repaired', label: 'Use strict counter < limit guard', type: 'toggle' }],
      calculate(s) {
        const levels = [[0]], paths = new Map([[0, [0]]]); let violation = null;
        for (let depth = 1; depth <= s.bound; depth++) {
          const next = new Set();
          for (const value of levels[depth - 1]) {
            const increment = (s.repaired ? value < s.limit : value <= s.limit) ? value + 1 : value;
            for (const destination of [increment, 0]) {
              next.add(destination);
              if (!paths.has(destination)) paths.set(destination, [...paths.get(value), destination]);
              if (destination > s.limit && !violation) violation = { depth, value: destination, path: paths.get(destination) };
            }
          }
          levels.push([...next].sort((a, b) => a - b));
        }
        return { data: { levels, violation, safeWithinBound: !violation },
          readout: 'Property: counter ≤ ' + s.limit + ', initially 0. Guard uses ' + (s.repaired ? '<' : '≤') + '; depth ' + s.bound + '. ' + (violation ? 'Counterexample at step ' + violation.depth + ': ' + violation.path.join(' → ') + '.' : 'No counterexample through this depth. This result alone is not an unbounded proof.'),
          note: 'Exhaustive reachability of a finite counter model with two actions: guarded increment and reset to zero. Each row contains states reachable after exactly that many actions; duplicate paths to a state are merged. The displayed witness is a shortest path to the first violating state. With the faulty ≤ guard, failure first becomes reachable at limit+1; a shallower check misses it. The repaired < guard preserves the bound, but the bounded search result is still reported only for its explored scope. This verifies a specified toy property, not an implementation, liveness, an adequate specification or AI alignment.',
          legend: [{ label: 'Blue: reachable states', color: colors.blue }, { label: 'Coral: a counterexample exists', color: colors.coral }, { label: 'Gold: bounded evidence only', color: colors.gold }], sources: [] };
      },
    },
    'cs.4.algorithms-adv': {
      title: 'When is a shortest distance final?',
      instructions: 'Change positive edge costs, then advance Dijkstra’s algorithm. Each step finalizes the nearest unsettled node and relaxes its outgoing edges.',
      initial: { ab: 4, ac: 2, bc: 1, steps: 4 },
      controls: [{ key: 'ab', label: 'Cost A → B', min: 1, max: 9, step: 1 }, { key: 'ac', label: 'Cost A → C', min: 1, max: 9, step: 1 },
        { key: 'bc', label: 'Cost B → C', min: 1, max: 9, step: 1 }, { key: 'steps', label: 'Finalization steps', min: 0, max: 4, step: 1 }],
      calculate(s) {
        const edges = [{ from: 0, to: 1, cost: s.ab }, { from: 0, to: 2, cost: s.ac }, { from: 1, to: 2, cost: s.bc }, { from: 1, to: 3, cost: 5 }, { from: 2, to: 3, cost: 2 }];
        const distances = [0, Infinity, Infinity, Infinity], previous = [null, null, null, null], settled = [], trace = [];
        for (let step = 0; step < s.steps; step++) {
          let u = -1;
          for (let i = 0; i < 4; i++) if (!settled.includes(i) && (u === -1 || distances[i] < distances[u])) u = i;
          if (u < 0 || !Number.isFinite(distances[u])) break;
          settled.push(u);
          edges.filter(edge => edge.from === u).forEach(edge => {
            const candidate = distances[u] + edge.cost;
            if (candidate < distances[edge.to]) { distances[edge.to] = candidate; previous[edge.to] = u; }
          });
          trace.push({ node: u, distances: distances.map(value => Number.isFinite(value) ? value : null) });
        }
        const path = [];
        if (Number.isFinite(distances[3])) { let node = 3; while (node !== null) { path.unshift(node); node = previous[node]; } }
        const final = settled.includes(3);
        return { data: { edges, distances: distances.map(value => Number.isFinite(value) ? value : null), previous, settled, trace, path, final },
          readout: 'Costs A→B=' + s.ab + ', A→C=' + s.ac + ', B→C=' + s.bc + ', B→D=5, C→D=2. After ' + s.steps + ' steps, settled: ' + (settled.map(i => 'ABCD'[i]).join(', ') || 'none') + '. D: ' + (path.length ? (final ? 'final' : 'tentative') + ' cost ' + distances[3] + ' via ' + path.map(i => 'ABCD'[i]).join(' → ') : 'not yet discovered') + '.',
          note: 'Directed edges, positive costs, source A. A dash means no discovered route, not a numeric zero or proof of unreachability. Relaxation replaces a tentative distance only with a cheaper route. Equal distances are settled in A–D order; equal alternative routes keep the first predecessor. With nonnegative edge weights, finalizing the nearest unsettled node is valid. Negative edges violate that guarantee. Highlighted routes can still be tentative until D is settled. The fixed four-node graph illustrates the invariant, not all graph algorithms or measured runtime.',
          legend: [{ label: 'Gold fill: finalized node', color: colors.gold }, { label: 'Gold edges: current route to D', color: colors.gold }, { label: 'Blue: other directed edges', color: colors.blue }], sources: [] };
      },
    },
    'cs.4.ml': {
      title: 'Training loss is not the whole evaluation',
      instructions: 'Fit y = wx by gradient descent. Change the step size and update count, then shift only the held-out targets to compare the two errors.',
      initial: { rate: .1, steps: 4, shift: 0 },
      controls: [{ key: 'rate', label: 'Learning rate', min: .02, max: .24, step: .02 }, { key: 'steps', label: 'Training updates', min: 0, max: 8, step: 1 },
        { key: 'shift', label: 'Held-out target shift', min: 0, max: 4, step: 1 }],
      calculate(s) {
        const training = [[1, 2], [2, 4], [3, 6]], heldout = [[4, 8 + s.shift], [5, 10 + s.shift]];
        const mse = (pairs, weight) => pairs.reduce((sum, [x, y]) => sum + (weight * x - y) ** 2, 0) / pairs.length;
        let weight = 0;
        const trajectory = [{ step: 0, weight, training: mse(training, weight), heldout: mse(heldout, weight) }];
        for (let step = 1; step <= s.steps; step++) {
          const gradient = training.reduce((sum, [x, y]) => sum + 2 * x * (weight * x - y), 0) / training.length;
          weight -= s.rate * gradient;
          trajectory.push({ step, weight, training: mse(training, weight), heldout: mse(heldout, weight) });
        }
        const last = trajectory[trajectory.length - 1];
        return { data: { training, heldout, trajectory, weight, trainingLoss: last.training, heldoutLoss: last.heldout },
          readout: 'Learning rate ' + numberText(s.rate) + ', ' + s.steps + ' updates: w≈' + numberText(weight) + '. Training MSE=' + smallLengthText(last.training) + '; held-out MSE=' + smallLengthText(last.heldout) + ' with target shift ' + s.shift + '. Held-out examples never enter the gradient.',
          note: 'Synthetic one-parameter regression with no intercept, initialized at w=0. Training pairs are (1,2), (2,4), (3,6); held-out pairs are (4,8+shift), (5,10+shift). Mean squared error averages squared residuals. The update uses only the three training pairs; changing held-out targets must not change learned weights. The graph’s vertical scale adjusts to include all displayed errors. Large learning rates can increase loss; more updates are not automatically better. A zero-shift test set follows the same exact rule by construction, not evidence of real-world generalization. This example does not represent all machine-learning methods.',
          legend: [{ label: 'Blue: training MSE', color: colors.blue }, { label: 'Gold: held-out MSE', color: colors.gold }], sources: [] };
      },
    },
    'cs.4.theory': {
      title: 'Recognize the suffix 01 with three states',
      instructions: 'Choose a binary string, then consume its symbols one at a time. Use the transition table to predict the next state.',
      initial: { word: '1101', steps: 4 },
      controls: [{ key: 'word', label: 'Input string', options: [{ value: '', label: 'Empty string ε' }, ...['01', '1101', '010', '111', '00101'].map(value => ({ value, label: value }))] },
        { key: 'steps', label: 'Symbols to consume', min: 0, max: 5, step: 1 }],
      calculate(s) {
        const consumed = Math.min(s.steps, s.word.length), prefix = s.word.slice(0, consumed), remaining = s.word.slice(consumed);
        const transitions = [[1, 0], [1, 2], [1, 0]], trace = [0];
        let state = 0;
        for (const symbol of prefix) { state = transitions[state][Number(symbol)]; trace.push(state); }
        const accepted = state === 2, finished = consumed === s.word.length;
        return { data: { state, prefix, remaining, consumed, accepted, finished, trace, transitions },
          readout: 'Input ' + (s.word || 'ε') + '; requested steps ' + s.steps + ', consumed ' + consumed + ' of ' + s.word.length + '. Trace: ' + trace.map(value => 'q' + value).join(' → ') + '. ' + (finished ? 'Full input ' + (accepted ? 'accepted' : 'rejected') + '.' : 'Prefix ' + (accepted ? 'ends in 01' : 'does not end in 01') + '; the full input is not finished.') + (s.steps > s.word.length ? ' Extra requested steps do not invent input symbols.' : ''),
          note: 'A deterministic finite automaton over {0,1}, starting in q0. State q1 means the consumed prefix ends in 0; q2 means it ends in 01; q0 covers the other prefixes, including ε. Only q2 is accepting, and acceptance of the full input is decided at its end. The trace and prefix are displayed for teaching; the machine itself needs only its current state, not an unbounded stored history. The table defines all six transitions. This regular-language example does not model a Turing machine or establish decidability of arbitrary problems.',
          legend: [{ label: 'Gold: current state and table row', color: colors.gold }, { label: 'Double circle q2: accepting state', color: colors.teal }, { label: 'Blue: transition rules', color: colors.blue }], sources: [] };
      },
    },
    'cs.3.web': {
      title: 'Structure, style and behavior are different layers',
      instructions: 'Press the working preview button, change its appearance, then turn off its counter handler. The native button remains keyboard-focusable.',
      initial: { count: 0, theme: 'gold', enabled: true },
      controls: [{ key: 'count', label: 'Set the counter directly', min: 0, max: 9, step: 1 },
        { key: 'theme', label: 'Preview background', options: [{ value: 'gold', label: 'Gold' }, { value: 'blue', label: 'Blue' }, { value: 'plain', label: 'Plain' }] },
        { key: 'enabled', label: 'Enable the preview counter handler', type: 'toggle' }],
      calculate(s) {
        return { data: { count: s.count, next: (s.count + 1) % 10, background: s.theme === 'gold' ? '#ecd39b' : s.theme === 'blue' ? '#c5dfe8' : '#f5efdf' },
          readout: 'Counter ' + s.count + '; background ' + s.theme + '; counter handler ' + (s.enabled ? 'enabled: the next activation sets ' + ((s.count + 1) % 10) : 'off: activation leaves the count unchanged') + '.',
          note: 'The preview is a real HTML button with type=button, scoped presentation styles and a local JavaScript click handler. Native keyboard focus and activation come from the button element; this non-submit button has no default counter behavior. The switch disables only this example’s counter handler, not JavaScript throughout the browser. CSS changes appearance without changing the count. The decimal counter cycles from 9 to 0; the slider can set it directly. Plain is a neutral lesson style, not a claim that all site or browser CSS has disappeared. No requests, forms or stored learner data are involved.',
          legend: [{ label: 'Blue: HTML structure', color: colors.blue }, { label: 'Gold: CSS presentation', color: colors.gold }, { label: 'Teal: JavaScript behavior', color: colors.teal }], sources: [] };
      },
    },
    'cs.2.internet': {
      title: 'A name lookup is not a page request',
      instructions: 'Step through a fictional HTTPS visit. Compare a fresh name lookup with a valid cached address; both still need the page request.',
      initial: { site: 'atlas', cached: false, stage: 0 },
      controls: [{ key: 'site', label: 'Fictional destination', options: [{ value: 'atlas', label: 'atlas.example' }, { value: 'book', label: 'book.example' }] },
        { key: 'cached', label: 'A valid DNS address is already cached', type: 'toggle' }, { key: 'stage', label: 'Visit stage', min: 0, max: 4, step: 1 }],
      calculate(s) {
        const hostname = s.site + '.example', address = s.site === 'atlas' ? '192.0.2.10' : '192.0.2.20';
        const dnsQueries = s.stage >= 1 && !s.cached ? 1 : 0, requests = s.stage >= 3 ? 1 : 0, responses = s.stage >= 4 ? 1 : 0;
        const events = ['Enter https://' + hostname, s.cached ? 'Use the valid cached address' : 'Ask DNS for the address', 'Establish authenticated TLS', 'Send HTTPS GET /', 'Receive the page response'];
        return { data: { hostname, address: s.stage >= 1 ? address : null, dnsQueries, requests, responses, tls: s.stage >= 2, events },
          readout: hostname + '; valid address cache ' + (s.cached ? 'present' : 'absent') + '; stage ' + s.stage + ': ' + events[s.stage] + '. Address ' + (s.stage >= 1 ? address : 'not yet obtained') + '. DNS queries ' + dnsQueries + ', page requests ' + requests + ', responses ' + responses + '.',
          note: 'Fictional .example names and documentation-only IP addresses; no real network request is made. DNS supplies an address, not HTML. A valid cached address can avoid a DNS query, but not the page request in this example. We assume a new successful HTTPS connection, a valid certificate, no page cache, no redirects and a one-response page. Resolver chains, transport handshakes, assets, failures and connection reuse are omitted. TLS authenticates the server name and encrypts traffic in transit; it does not establish that the page’s claims are trustworthy.',
          legend: [{ label: 'Gold outline: current stage', color: colors.gold }, { label: 'Blue: completed or current steps', color: colors.blue }, { label: 'Faded: future steps', color: colors.ink }], sources: [] };
      },
    },
    'cs.4.os': {
      title: 'Share one CPU between three jobs',
      instructions: 'Compare first-come-first-served with round robin. Change the time quantum and inspect first response, completion and waiting times.',
      initial: { policy: 'rr', quantum: 2 },
      controls: [{ key: 'policy', label: 'Scheduling policy', options: [{ value: 'rr', label: 'Round robin' }, { value: 'fcfs', label: 'First come, first served' }] },
        { key: 'quantum', label: 'Round-robin quantum', min: 1, max: 4, step: 1 }],
      calculate(s) {
        const jobs = [{ id: 'A', burst: 3 }, { id: 'B', burst: 5 }, { id: 'C', burst: 2 }].map(job => ({ ...job, remaining: job.burst, first: null, completion: null }));
        const queue = jobs.slice(), timeline = [];
        while (queue.length) {
          const job = queue.shift();
          if (job.first === null) job.first = timeline.length;
          const duration = s.policy === 'fcfs' ? job.remaining : Math.min(s.quantum, job.remaining);
          for (let i = 0; i < duration; i++) timeline.push(job.id);
          job.remaining -= duration;
          if (job.remaining) queue.push(job); else job.completion = timeline.length;
        }
        jobs.forEach(job => { job.waiting = job.completion - job.burst; });
        const switches = timeline.slice(1).filter((id, i) => id !== timeline[i]).length;
        return { data: { jobs, timeline, switches },
          readout: (s.policy === 'rr' ? 'Round robin, quantum ' + s.quantum : 'First come, first served; quantum ' + s.quantum + ' is unused') + '. All jobs arrive at time 0 in A, B, C order. ' + jobs.map(job => job.id + ': first response ' + job.first + ', completion ' + job.completion + ', waiting ' + job.waiting).join('; ') + '. ' + switches + ' switches between different jobs.',
          note: 'One CPU, fixed CPU bursts A=3, B=5, C=2, simultaneous arrivals, no I/O, priorities or switching overhead. A time cell represents one unit of CPU work. Response is time until first execution; completion equals turnaround because arrivals are zero; waiting is completion minus burst. A quantum boundary with the same job continuing is not counted as a switch. Smaller quanta can improve first response while adding switches; this idealized trace does not estimate a real operating system’s performance.',
          legend: [{ label: 'A: three work units', color: colors.blue }, { label: 'B: five work units', color: colors.plum }, { label: 'C: two work units', color: colors.gold }], sources: [] };
      },
    },
    'cs.4.databases-adv': {
      title: 'Two writes, one all-or-nothing change',
      instructions: 'Move counters from A to B, and interrupt the operation after subtracting from A. Compare an atomic transaction with two independent writes.',
      initial: { amount: 3, failure: true, atomic: true },
      controls: [{ key: 'amount', label: 'Counters to move', min: 0, max: 8, step: 1 }, { key: 'failure', label: 'Interrupt after the first write', type: 'toggle' }, { key: 'atomic', label: 'Wrap both writes in one transaction', type: 'toggle' }],
      calculate(s) {
        const pendingA = 8 - s.amount, pendingB = s.failure ? 2 : 2 + s.amount;
        const rolledBack = s.failure && s.atomic, finalA = rolledBack ? 8 : pendingA, finalB = rolledBack ? 2 : pendingB;
        const outcome = rolledBack ? 'Aborted and rolled back' : s.failure ? 'Stopped after first write' : s.atomic ? 'Committed together' : 'Both independent writes finished';
        return { data: { pendingA, pendingB, finalA, finalB, total: finalA + finalB, rolledBack, outcome },
          readout: 'Move ' + s.amount + ' counters; interruption ' + truthText(s.failure) + '; atomic transaction ' + truthText(s.atomic) + '. ' + outcome + '. Final A=' + finalA + ', B=' + finalB + ', total=' + (finalA + finalB) + ' (initial total 10).',
          note: 'An atomicity example using hypothetical counters, not real records. The interruption occurs after the debit and before the credit. In a transaction, that interruption aborts and rolls back the uncommitted debit; without a transaction, the first independent write remains. A successful transaction publishes both changes together in this simplified model. Zero counters can hide a partial-write bug because totals remain equal. Isolation, durability, validation, retries and replication are separate concerns not simulated here. No database or learner record is changed.',
          legend: [{ label: 'Blue: original counters', color: colors.blue }, { label: 'Teal: final state', color: colors.teal }, { label: 'Coral: interrupted operation', color: colors.coral }], sources: [] };
      },
    },
    'cs.3.versioncontrol': {
      title: 'Merge against the common ancestor',
      instructions: 'Edit a line on each branch. Compare both versions with the base, then resolve any incompatible edits explicitly.',
      initial: { leftLine: 1, rightLine: 2, same: false, resolution: 'none' },
      controls: [{ key: 'leftLine', label: 'Left edit line (0 = no edit)', min: 0, max: 3, step: 1 },
        { key: 'rightLine', label: 'Right edit line (0 = no edit)', min: 0, max: 3, step: 1 },
        { key: 'same', label: 'Both branches use replacement X', type: 'toggle' },
        { key: 'resolution', label: 'Decision for conflicting lines', options: [{ value: 'none', label: 'Leave unresolved' }, { value: 'left', label: 'Choose left version' }, { value: 'right', label: 'Choose right version' }] }],
      calculate(s) {
        const base = ['A', 'B', 'C'], left = base.slice(), right = base.slice();
        if (s.leftLine) left[s.leftLine - 1] = 'X';
        if (s.rightLine) right[s.rightLine - 1] = s.same ? 'X' : 'Y';
        const conflicts = [];
        const merged = base.map((value, i) => {
          if (left[i] === right[i]) return left[i];
          if (left[i] === value) return right[i];
          if (right[i] === value) return left[i];
          conflicts.push(i + 1);
          return s.resolution === 'left' ? left[i] : s.resolution === 'right' ? right[i] : null;
        });
        const unresolved = merged.filter(value => value === null).length;
        return { data: { base, left, right, merged, conflicts, unresolved },
          readout: 'Left edit: ' + (s.leftLine ? 'line ' + s.leftLine + ' → X' : 'none') + '. Right edit: ' + (s.rightLine ? 'line ' + s.rightLine : 'none') + '; replacement ' + (s.same ? 'X' : 'Y') + '. Conflict decision: ' + s.resolution + '. ' + (conflicts.length ? 'Both branches changed line ' + conflicts.join(', ') + ' differently. ' + (unresolved ? 'A decision is still required; there is no complete merged file.' : 'The selected version resolves this conflict.') : 'No incompatible line edits; the conflict decision is unused.') + ' Result: ' + merged.map(value => value === null ? '?' : value).join(', ') + '.',
          note: 'A simplified line-aligned three-way merge: unchanged on one branch means take the other change; equal changes combine; different changes to the same line require a decision. Base and branch versions remain unchanged when resolving the result. This is not Git’s full text-merge algorithm: insertions, deletions, renames, overlapping hunks and semantic conflicts are omitted. A clean merge does not prove correctness; tests and review are still needed. Choosing a side here affects only conflicting lines, not the whole file. No repository is modified.',
          legend: [{ label: 'Blue: preserved base and branch versions', color: colors.blue }, { label: 'Teal: resolved result', color: colors.teal }, { label: 'Coral ?: unresolved conflict', color: colors.coral }], sources: [] };
      },
    },
    'cs.3.oop': {
      title: 'Shared classes, separate object state',
      instructions: 'Change the points stored in each object. Switch object A to the subclass and observe which score method it uses.',
      initial: { first: 2, second: 4, boosted: false },
      controls: [{ key: 'first', label: 'Object A points', min: 0, max: 5, step: 1 }, { key: 'second', label: 'Object B points', min: 0, max: 5, step: 1 },
        { key: 'boosted', label: 'Object A uses BonusScore subclass', type: 'toggle' }],
      calculate(s) {
        class Score { constructor(points) { this.points = points; } score() { return this.points; } }
        class BonusScore extends Score { score() { return this.points + 3; } }
        const a = s.boosted ? new BonusScore(s.first) : new Score(s.first), b = new Score(s.second);
        return { data: { firstPoints: a.points, secondPoints: b.points, firstScore: a.score(), secondScore: b.score(), firstClass: s.boosted ? 'BonusScore' : 'Score' },
          readout: 'Object A is ' + (s.boosted ? 'BonusScore' : 'Score') + ', stores ' + a.points + ' points and returns ' + a.score() + ' from score(). Object B is Score, stores ' + b.points + ' points and returns ' + b.score() + '. Their fields are separate.',
          note: 'Both instances store their own points field. BonusScore inherits the constructor and overrides score() to return points + 3 without changing stored points. Calling the same method name dispatches according to the object class. This model constructs fresh local instances for each control change; switching class is not an in-place mutation of a real object type. It illustrates inheritance and independent state, not every object-oriented design or a recommendation to prefer inheritance over composition.',
          legend: [{ label: 'Blue: base Score behavior', color: colors.blue }, { label: 'Plum: BonusScore override', color: colors.plum }, { label: 'Teal: returned value, not stored state', color: colors.teal }], sources: [] };
      },
    },
    'cs.3.hardware': {
      title: 'Build one bit of an adder',
      instructions: 'Set two input bits and a carry-in. Follow the intermediate gates to see how the result becomes a sum bit and a carry-out.',
      initial: { a: 1, b: 1, carry: 0 },
      controls: [{ key: 'a', label: 'Input bit a', min: 0, max: 1, step: 1 }, { key: 'b', label: 'Input bit b', min: 0, max: 1, step: 1 }, { key: 'carry', label: 'Carry-in bit c', min: 0, max: 1, step: 1 }],
      calculate(s) {
        const x = s.a ^ s.b, p = s.a & s.b, q = x & s.carry, sum = x ^ s.carry, carryOut = p | q;
        return { data: { x, p, q, sum, carryOut, total: 2 * carryOut + sum },
          readout: s.a + ' + ' + s.b + ' + carry-in ' + s.carry + ' = ' + (2 * carryOut + sum) + '. Sum bit ' + sum + ', carry-out ' + carryOut + ': binary ' + carryOut + sum + '. The carry-out has weight 2; the sum bit has weight 1.',
          note: 'An ideal Boolean full adder. XOR is 1 when exactly one of its two inputs is 1; AND requires both; OR requires at least one. The two half-adder paths are combined with OR for the carry-out. Carry-in comes from a lower-order bit when adders are chained; it is an input here. Gates are shown as equations, not transistor circuits. Propagation delay, voltage, power, clocking and storage are excluded. This is arithmetic logic, not a complete CPU.',
          legend: [{ label: 'Blue: gate equations', color: colors.blue }, { label: 'Teal: output bits', color: colors.teal }], sources: [] };
      },
    },
    'cs.2.bigo-intro': {
      title: 'Count the checks in two searches',
      instructions: 'Search the sorted integers from 1 to n. Change the list size and target, and compare actual checked items rather than elapsed time.',
      initial: { size: 16, target: 16 },
      controls: [{ key: 'size', label: 'List size n', min: 4, max: 32, step: 4 }, { key: 'target', label: 'Target value', min: 0, max: 33, step: 1 }],
      calculate(s) {
        const values = Array.from({ length: s.size }, (_, i) => i + 1), linear = [], binary = [];
        let linearFound = false, binaryFound = false;
        for (const value of values) { linear.push(value); if (value === s.target) { linearFound = true; break; } }
        let low = 0, high = values.length - 1;
        while (low <= high) {
          const mid = Math.floor((low + high) / 2), value = values[mid];
          binary.push({ low: low + 1, high: high + 1, value });
          if (value === s.target) { binaryFound = true; break; }
          if (value < s.target) low = mid + 1; else high = mid - 1;
        }
        return { data: { values, linear, binary, linearFound, binaryFound },
          readout: 'Search 1…' + s.size + ' for ' + s.target + ': ' + (binaryFound ? 'found' : 'not present') + '. Linear search checks ' + linear.length + ' items; binary search checks ' + binary.length + '. Binary probes: ' + binary.map(row => row.value).join(' → ') + '.',
          note: 'One check means inspecting one candidate item, not one machine instruction or a measured duration. Linear search here scans until equality or the end; binary search uses sorted order and a lower-middle pivot. Sorting cost is excluded. Binary search is not faster for every target: linear search finds the first item in one check. Worst-case growth is linear versus logarithmic, but this display counts this particular run. Targets 0 and values above n are absent. Both algorithms run locally on the same fixed sorted list.',
          legend: [{ label: 'Blue: linear checks', color: colors.blue }, { label: 'Teal: binary checks', color: colors.teal }], sources: [] };
      },
    },
    'cs.3.algorithms': {
      title: 'Split, solve the halves, then merge',
      instructions: 'Choose a four-item input, then reveal the recursive split and merge stages. A merge compares the front remaining item of each sorted half.',
      initial: { input: 'mixed', stage: 4 },
      controls: [{ key: 'input', label: 'Input order', options: [{ value: 'mixed', label: 'Mixed: 7, 2, 5, 1' }, { value: 'sorted', label: 'Sorted: 1, 2, 5, 7' }, { value: 'reverse', label: 'Reverse: 7, 5, 2, 1' }, { value: 'ties', label: 'Ties: 2, 1, 2, 1' }] },
        { key: 'stage', label: 'Reveal stage: input to merged result', min: 0, max: 4, step: 1 }],
      calculate(s) {
        const values = { mixed: [7, 2, 5, 1], sorted: [1, 2, 5, 7], reverse: [7, 5, 2, 1], ties: [2, 1, 2, 1] }[s.input];
        const source = values.map((value, id) => ({ value, id }));
        let comparisons = 0;
        function merge(a, b) {
          let i = 0, j = 0; const result = [];
          while (i < a.length && j < b.length) { comparisons++; result.push(a[i].value <= b[j].value ? a[i++] : b[j++]); }
          return result.concat(a.slice(i), b.slice(j));
        }
        const left = merge([source[0]], [source[1]]), right = merge([source[2]], [source[3]]), pairComparisons = comparisons;
        const result = merge(left, right);
        const shownComparisons = s.stage < 3 ? 0 : s.stage === 3 ? pairComparisons : comparisons;
        const labels = ['Original input', 'Split into two halves', 'Single items are sorted', 'Merge each pair', 'Merge the sorted halves'];
        return { data: { source, left, right, result, comparisons, shownComparisons, label: labels[s.stage] },
          readout: values.join(', ') + ' · stage ' + s.stage + ': ' + labels[s.stage] + '. ' + shownComparisons + ' value comparisons completed.' + (s.stage === 4 ? ' Result: ' + result.map(item => item.value).join(', ') + '.' : ' Later rows are not yet revealed.'),
          note: 'An expanded view of a recursive merge sort, not the chronological call stack: sibling branches are grouped by depth. A one-item list needs no comparison. Equal values are taken from the left half first, preserving their original order; letter tags identify original items. Only comparisons between values are counted, not copies or loop tests. This four-item trace explains the operation but is not a timing benchmark or evidence by itself for asymptotic complexity.',
          legend: [{ label: 'Blue: input and split groups', color: colors.blue }, { label: 'Teal: sorted groups', color: colors.teal }, { label: 'Gold outline: revealed stage', color: colors.gold }], sources: [] };
      },
    },
    'cs.1.blocks': {
      title: 'Repeat, then test the condition',
      instructions: 'Choose how many steps to repeat and where the star sits. The jump happens only if the character lands on the star after the loop.',
      initial: { repeats: 2, star: 2, jump: 2 },
      controls: [{ key: 'repeats', label: 'Repeat one step', min: 0, max: 4, step: 1 },
        { key: 'star', label: 'Star position', min: 0, max: 4, step: 1 },
        { key: 'jump', label: 'Jump distance if on star', min: 1, max: 3, step: 1 }],
      calculate(s) {
        let position = 0;
        const path = [position];
        for (let i = 0; i < s.repeats; i++) { position++; path.push(position); }
        const before = position, matched = position === s.star;
        if (matched) position += s.jump;
        return { data: { before, matched, position, path },
          readout: 'Start at 0. Repeat ' + s.repeats + ' one-step moves to reach ' + before + '. Star at ' + s.star + ': condition ' + truthText(matched) + '. ' + (matched ? 'Jump ' + s.jump + ' steps to ' + position + '.' : 'Skip the ' + s.jump + '-step jump; stay at ' + position + '.'),
          note: 'The condition is checked once, after the repeat block. Passing over the star earlier does not trigger a jump. Zero repeats means no loop moves, but the condition still runs. The star stays in place; jumping does not repeat the condition. This is a small deterministic block program, not a Scratch editor or an animation of a physical jump.',
          legend: [{ label: 'Blue: repeated moves', color: colors.blue }, { label: 'Gold triangle: star target', color: colors.gold }, { label: 'Teal: final position', color: colors.teal }], sources: [] };
      },
    },
    'cs.2.programming': {
      title: 'Trace a filtered running total',
      instructions: 'Change the threshold and how many loop iterations have run. Compare each value with the threshold before updating total.',
      initial: { threshold: 4, iterations: 3 },
      controls: [{ key: 'threshold', label: 'Add values strictly greater than', min: 0, max: 9, step: 1 },
        { key: 'iterations', label: 'Completed iterations', min: 0, max: 3, step: 1 }],
      calculate(s) {
        let total = 0;
        const trace = [2, 5, 8].map((value, i) => {
          const completed = i < s.iterations, accepted = value > s.threshold;
          if (completed && accepted) total += value;
          return { value, completed, accepted: completed ? accepted : null, total: completed ? total : null };
        });
        return { data: { trace, total },
          readout: 'After ' + s.iterations + ' of 3 iterations, total = ' + total + '. Only values strictly greater than ' + s.threshold + ' are added; equal values are skipped. ' + (s.iterations === 0 ? 'The loop has not run; total is initialized to zero.' : trace.filter(row => row.completed).map(row => row.value + (row.accepted ? ' added' : ' skipped') + ' → total ' + row.total).join('; ') + '.'),
          note: 'Python-style code over the fixed list [2, 5, 8]. Each completed iteration binds value, tests >, and optionally updates total; the table records the result after that whole iteration. A pending row is not a false comparison or a zero total. Changing a control recomputes the trace from the initialization. No user code is evaluated and no learner state is saved.',
          legend: [{ label: 'Teal: added value', color: colors.teal }, { label: 'Coral: skipped value', color: colors.coral }, { label: 'Faded: pending iteration', color: colors.blue }], sources: [] };
      },
    },
    'cs.1.parts': {
      title: 'Follow a value through the computer',
      instructions: 'Choose an input and instruction, then advance the snapshots from input to memory, processing and output.',
      initial: { input: 3, operation: 'double', step: 0 },
      controls: [{ key: 'input', label: 'Input value', min: 0, max: 9, step: 1 },
        { key: 'operation', label: 'Processor instruction', options: [{ value: 'double', label: 'Double the value' }, { value: 'increment', label: 'Add one' }] },
        { key: 'step', label: 'Snapshot: input → store → compute → display', min: 0, max: 3, step: 1 }],
      calculate(s) {
        const result = s.operation === 'double' ? s.input * 2 : s.input + 1;
        const memory = s.step === 0 ? null : s.step === 1 ? s.input : result, processor = s.step >= 2 ? result : null, output = s.step === 3 ? result : null;
        return { data: { result, memory, processor, output },
          readout: 'Input ' + s.input + '; instruction: ' + (s.operation === 'double' ? 'double' : 'add one') + '. ' + ['Input is ready; memory and output have not received it.', 'The input has been copied into working memory.', 'The processor reads the input, computes ' + result + ' and writes that result to memory.', 'The display receives the result ' + result + ' from memory.'][s.step],
          note: 'A simplified sequential computer, not a timing diagram of a particular processor. Input supplies data; working memory holds a value; the processor follows an instruction; output presents the result. The compute snapshot includes reading, computing and writing back, so the memory box now contains the result. A blank box means not yet available, not numeric zero. Working memory here is not long-term storage. Real systems include registers, caches, buses, peripherals and many overlapping operations. Changing a control recomputes this illustrative run; it does not operate the device or persist learner data.',
          legend: [{ label: 'Gold outline: current stage', color: colors.gold }, { label: 'Blue: a value available at this snapshot', color: colors.blue }], sources: [] };
      },
    },
    'cs.3.databases': {
      title: 'A query changes the view, not the stored rows',
      instructions: 'Choose a minimum score and group, then order the matching rows. Compare the result with the unchanged source table.',
      initial: { minimum: 50, group: 'all', descending: true },
      controls: [{ key: 'minimum', label: 'Minimum score', min: 0, max: 100, step: 10 },
        { key: 'group', label: 'Group filter', options: [{ value: 'all', label: 'All groups' }, { value: 'A', label: 'Group A' }, { value: 'B', label: 'Group B' }] },
        { key: 'descending', label: 'Highest score first', type: 'toggle' }],
      calculate(s) {
        const rows = [{ id: 1, name: 'Owl', group: 'A', score: 10 }, { id: 2, name: 'Fox', group: 'B', score: 40 },
          { id: 3, name: 'Ant', group: 'A', score: 70 }, { id: 4, name: 'Bee', group: 'B', score: 90 },
          { id: 5, name: 'Elk', group: 'B', score: 70 }, { id: 6, name: 'Yak', group: 'A', score: 20 }];
        const result = rows.filter(row => row.score >= s.minimum && (s.group === 'all' || row.group === s.group))
          .sort((a, b) => (s.descending ? b.score - a.score : a.score - b.score) || a.id - b.id);
        return { data: { rows, result },
          readout: 'Keep score ≥ ' + s.minimum + (s.group === 'all' ? ' in any group' : ' and group ' + s.group) + '; order score ' + (s.descending ? 'descending' : 'ascending') + ', then ID ascending for ties. ' + result.length + ' rows returned: ' + (result.map(row => row.name + ' ' + row.score).join(', ') || 'none') + '. The source still contains all six rows.',
          note: 'A deterministic SELECT-style example over fictional records. WHERE selects rows satisfying the conditions; ORDER BY controls presentation; neither deletes or updates source records. The >= comparison includes the boundary. Equal scores use the original unique ID as an explicit secondary ordering key, not an assumed database default. This local model is not a live database connection and executes no user-supplied SQL. NULLs, joins, grouping, permissions, transactions and indexes are outside this introductory query.',
          legend: [{ label: 'Blue: unchanged source table', color: colors.blue }, { label: 'Teal: selected, ordered result', color: colors.teal }], sources: [] };
      },
    },
    'cs.2.data-types': {
      title: 'The same digits can mean numbers or text',
      instructions: 'Choose the values and types on each side of +. Compare arithmetic, concatenation and an incompatible-type error.',
      initial: { left: 2, right: 3, leftType: 'number', rightType: 'number' },
      controls: [{ key: 'left', label: 'Left digit', min: 0, max: 9, step: 1 }, { key: 'leftType', label: 'Left type', options: [{ value: 'number', label: 'Integer' }, { value: 'text', label: 'String' }] },
        { key: 'right', label: 'Right digit', min: 0, max: 9, step: 1 }, { key: 'rightType', label: 'Right type', options: [{ value: 'number', label: 'Integer' }, { value: 'text', label: 'String' }] }],
      calculate(s) {
        const valid = s.leftType === s.rightType;
        const result = !valid ? null : s.leftType === 'number' ? s.left + s.right : String(s.left) + String(s.right);
        const leftLiteral = s.leftType === 'text' ? '"' + s.left + '"' : String(s.left), rightLiteral = s.rightType === 'text' ? '"' + s.right + '"' : String(s.right);
        const output = !valid ? 'TypeError' : s.leftType === 'text' ? '"' + result + '"' : String(result);
        return { data: { valid, result, leftLiteral, rightLiteral, output },
          readout: leftLiteral + ' + ' + rightLiteral + ' gives ' + output + '. ' + (!valid ? 'An integer and a string cannot be added directly under this rule; no result value is produced.' : s.leftType === 'number' ? 'Integer addition combines numeric quantities.' : 'String concatenation joins characters without adding their numeric meanings. Quotes mark a string literal; they are not characters in the value.'),
          note: 'A small Python-style subset for integer+integer and string+string. Mixed integer/string operands give a TypeError, not automatic conversion. Other languages may choose different coercion rules; this is not a universal definition of +. The model only selects single-digit operands, though addition can produce two digits and concatenation always produces two characters. Booleans, lists, floating-point values and explicit conversions are outside this comparison. Values are computed locally with typed branches, not evaluated as user-supplied code.',
          legend: [{ label: 'Blue: integer operand', color: colors.blue }, { label: 'Plum: string operand', color: colors.plum }, { label: 'Coral: incompatible types', color: colors.coral }], sources: [] };
      },
    },
    'cs.2.debugging': {
      title: 'A passing example can hide a boundary bug',
      instructions: 'The program should add every integer from 1 through n. Try n=0 and positive inputs, then repair the loop boundary and compare the results.',
      initial: { n: 4, fixed: false },
      controls: [{ key: 'n', label: 'Test input n', min: 0, max: 6, step: 1 }, { key: 'fixed', label: 'Include the endpoint: use ≤', type: 'toggle' }],
      calculate(s) {
        function run(n) {
          let total = 0; const trace = [];
          for (let i = 1; s.fixed ? i <= n : i < n; i++) { total += i; trace.push({ i, total }); }
          return { total, trace };
        }
        const result = run(s.n), expected = s.n * (s.n + 1) / 2;
        const cases = Array.from({ length: 7 }, (_, n) => ({ n, expected: n * (n + 1) / 2, actual: run(n).total }));
        return { data: { ...result, expected, passes: result.total === expected, cases },
          readout: 'Loop condition: i ' + (s.fixed ? '≤' : '<') + ' n. For n=' + s.n + ', expected sum ' + expected + ', actual sum ' + result.total + ': ' + (result.total === expected ? 'PASS.' : 'FAIL.') + ' The loop visits ' + (result.trace.map(row => row.i).join(', ') || 'no values') + '. Tests 0 through 6: ' + cases.filter(row => row.expected === row.actual).length + ' of 7 pass.',
          note: 'The specification includes the endpoint n. The buggy condition i<n omits it for every positive test here; i≤n repairs that boundary. At n=0 both versions correctly perform no iterations and return zero, so this passing edge case alone cannot reveal the bug. The expected result uses the independent arithmetic identity n(n+1)/2. Passing a finite test set is evidence, not a proof for every input. This bounded integer example omits overflow, input validation and language-specific syntax; fixing one program does not establish correctness of unrelated programs.',
          legend: [{ label: 'Blue: loop values and running totals', color: colors.blue }, { label: 'Teal/coral: passing/failing comparison', color: colors.teal }], sources: [] };
      },
    },
    'cs.2.functions': {
      title: 'Define once, call with different arguments',
      instructions: 'Choose a function body, then pass two different arguments. Both calls reuse the same definition, but each has its own local parameter value.',
      initial: { operation: 'double', first: 2, second: 5 },
      controls: [{ key: 'operation', label: 'Function body', options: [{ value: 'double', label: 'return 2 × n' }, { value: 'add', label: 'return n + 3' }, { value: 'square', label: 'return n × n' }] },
        { key: 'first', label: 'Argument for call A', min: -3, max: 6, step: 1 }, { key: 'second', label: 'Argument for call B', min: -3, max: 6, step: 1 }],
      calculate(s) {
        const apply = n => s.operation === 'double' ? 2 * n : s.operation === 'add' ? n + 3 : n * n;
        const body = { double: 'return 2 × n', add: 'return n + 3', square: 'return n × n' }[s.operation];
        return { data: { body, firstResult: apply(s.first), secondResult: apply(s.second) },
          readout: 'Definition f(n): ' + body + '. Call A passes argument ' + s.first + ', binds its local n to ' + s.first + ' and returns ' + apply(s.first) + '. Call B passes argument ' + s.second + ', binds its own n to ' + s.second + ' and returns ' + apply(s.second) + '. Changing one argument does not change the other call.',
          note: 'Executable arithmetic behind language-neutral pseudocode. The parameter n is a name in the definition; an argument is the value supplied by a particular call. Return sends a value back to the caller; it is not the same operation as printing. These examples are pure deterministic functions: no shared mutable state, input/output effects or randomness. Not every real function has those properties. The two lanes illustrate separate calls and local bindings, not necessarily parallel execution.',
          legend: [{ label: 'Blue: supplied argument and local binding', color: colors.blue }, { label: 'Teal: returned result', color: colors.teal }], sources: [] };
      },
    },
    'cs.0.sorting': {
      title: 'One collection, different sorting rules',
      instructions: 'Choose a rule, then bring more objects into the sorted group. The objects stay the same; their order changes.',
      initial: { rule: 'size', count: 3 },
      controls: [{ key: 'rule', label: 'Sort by', options: [{ value: 'size', label: 'Size: small to large' }, { value: 'color', label: 'Colour: blue, gold, plum' }, { value: 'shape', label: 'Shape: circle, square, triangle' }] },
        { key: 'count', label: 'Objects included in the sorted group', min: 0, max: 6, step: 1 }],
      calculate(s) {
        const items = [{ id: 'A', size: 3, color: 0, shape: 0 }, { id: 'B', size: 1, color: 1, shape: 2 }, { id: 'C', size: 2, color: 2, shape: 1 },
          { id: 'D', size: 1, color: 0, shape: 0 }, { id: 'E', size: 3, color: 2, shape: 2 }, { id: 'F', size: 2, color: 1, shape: 1 }];
        const sorted = items.slice(0, s.count).sort((a, b) => a[s.rule] - b[s.rule] || a.id.localeCompare(b.id));
        const output = [...sorted, ...items.slice(s.count)];
        return { data: { items, output }, readout: 'Rule: ' + { size: 'small to large', color: 'blue, then gold, then plum', shape: 'circle, then square, then triangle' }[s.rule] + '. ' + s.count + ' objects included. Current order: ' + output.map(item => item.id).join(', ') + '. ' + (s.count === 6 ? 'All six are sorted by the chosen rule.' : 'Only the highlighted group is sorted; the rest is waiting.'),
          note: 'Letters identify objects so you can follow the same object between rows. Size, colour and shape are independent properties. Colour and shape have the displayed chosen order, not an inherently correct ranking. Equal-key objects keep their original order. Each step inserts the next original object into the sorted prefix; it is not a count of individual comparisons or swaps. This activity introduces ordering, not a performance claim about sorting algorithms.',
          legend: [{ label: 'Gold outline: the sorted group', color: colors.gold }, { label: 'Letters: object identity, not the sorting rule', color: colors.ink }], sources: [] };
      },
    },
    'cs.0.patterns': {
      title: 'A short rule can make a long pattern',
      instructions: 'Choose a repeating unit and how many copies to show. Predict the next symbol before reading the answer.',
      initial: { unit: 'AB', repeats: 3 },
      controls: [{ key: 'unit', label: 'Repeating unit', options: ['AB', 'ABB', 'AAB', 'ABC'].map(value => ({ value, label: value })) },
        { key: 'repeats', label: 'Copies of the unit', min: 1, max: 4, step: 1 }],
      calculate(s) {
        const sequence = s.unit.repeat(s.repeats).split('');
        return { data: { sequence, next: s.unit[0], length: sequence.length },
          readout: 'Repeat ' + s.unit + ' ' + s.repeats + ' times: ' + sequence.join(' ') + '. ' + sequence.length + ' symbols. The next symbol is ' + s.unit[0] + ' because a new copy of the unit begins.',
          note: 'Each letter has a matching colour and shape, so colour is not the only clue. This model explicitly chooses a repeating rule. A short observed sequence by itself could fit many other rules; the displayed continuation follows this chosen one. Repetition is one kind of pattern, not every kind of pattern.',
          legend: [{ label: 'A: blue circle', color: colors.blue }, { label: 'B: gold square', color: colors.gold }, { label: 'C: plum triangle', color: colors.plum }], sources: [] };
      },
    },
    'chem.3.bonding': {
      title: 'Conduction needs mobile charge carriers',
      instructions: 'Compare salt, copper and molecular iodine. Change solid to liquid and apply a field to see which charged particles can drift.',
      initial: { material: 'salt', liquid: false, field: false },
      controls: [{ key: 'material', label: 'Material', options: [{ value: 'salt', label: 'Sodium chloride: ionic' }, { value: 'copper', label: 'Copper: metallic' }, { value: 'iodine', label: 'Iodine: molecular covalent' }] },
        { key: 'liquid', label: 'Liquid rather than solid', type: 'toggle' }, { key: 'field', label: 'Apply an electric field', type: 'toggle' }],
      calculate(s) {
        const mobile = s.material === 'copper' || (s.material === 'salt' && s.liquid);
        const carrier = s.material === 'copper' ? 'electrons' : s.material === 'salt' ? 'ions' : 'none';
        const conducting = mobile && s.field;
        return { data: { mobile, carrier, conducting, drift: conducting ? 12 : 0 },
          readout: (s.liquid ? 'Liquid ' : 'Solid ') + { salt: 'sodium chloride', copper: 'copper', iodine: 'molecular iodine' }[s.material] + ', field ' + (s.field ? 'on' : 'off') + '. ' + (s.material === 'copper' ? 'Delocalised electrons can move through the metal in either state.' : s.material === 'salt' ? s.liquid ? 'The ions can move through the melt.' : 'The ions are held in the solid lattice and cannot carry a sustained bulk current in this ideal model.' : 'Neutral I₂ molecules provide no mobile charged carriers in this simplified comparison.') + (conducting ? ' A directed drift carries current.' : mobile ? ' Without a field there is no directed drift, even though carriers are mobile.' : ' Applying a field does not create mobile carriers here.'),
          note: 'Qualitative bulk models, not measured conductivity or an experiment to perform. Salt contains oppositely charged ions; copper contains positive atomic cores and delocalised electrons; iodine contains neutral I₂ molecules with covalent bonds internally and intermolecular attractions between molecules. Field arrows point right: positive ions drift right, negative ions and electrons left. Offsets exaggerate drift and are not speeds, trajectories or time evolution. Thermal motion, electrode reactions, defects and small leakage currents are omitted. Molecular iodine is a poor conductor, not a model for every covalent substance: graphite and semiconductors are important counterexamples. The samples are compared at their own solid/liquid conditions, not a common temperature. Do not heat or electrically test these substances from this diagram.',
          legend: [{ label: 'Blue/plum: positive/negative ions', color: colors.blue }, { label: 'Gold dots: mobile electrons in metal', color: colors.gold }], sources: [] };
      },
    },
    'chem.4.inorganic': {
      title: 'Count donor atoms, not just ligands',
      instructions: 'Replace pairs of monodentate ligands with neutral bidentate en. Compare ligand count, coordination number and complex charge.',
      initial: { chelates: 1, oxidation: 3, mono: 'ammonia' },
      controls: [{ key: 'chelates', label: 'Bidentate en ligands', min: 0, max: 3, step: 1 },
        { key: 'oxidation', label: 'Metal oxidation state', min: 2, max: 4, step: 1 },
        { key: 'mono', label: 'Remaining monodentate ligands', options: [{ value: 'ammonia', label: 'Neutral NH₃' }, { value: 'chloride', label: 'Chloride Cl⁻' }] }],
      calculate(s) {
        const monodentate = 6 - 2 * s.chelates, ligandCount = s.chelates + monodentate, ligandCharge = s.mono === 'chloride' ? -monodentate : 0;
        const charge = s.oxidation + ligandCharge;
        return { data: { monodentate, ligandCount, ligandCharge, charge, donors: 6 },
          readout: s.chelates + ' bidentate en ligands contribute ' + (2 * s.chelates) + ' donor atoms; ' + monodentate + ' monodentate ' + (s.mono === 'ammonia' ? 'NH₃' : 'Cl⁻') + ' ligands contribute ' + monodentate + '. Total: ' + ligandCount + ' ligands, but coordination number 6. Metal oxidation state +' + s.oxidation + ' plus ligand charge ' + ligandCharge + ' gives complex charge ' + (charge > 0 ? '+' : '') + charge + '.',
          note: 'Formal six-coordinate bookkeeping for a hypothetical metal M, not a claim that every chosen complex is stable or synthesizable. Ethane-1,2-diamine (en) is neutral and binds through two nitrogen donor atoms; NH₃ is neutral and monodentate; Cl⁻ is −1 and monodentate here. Coordination number counts donor atoms directly bonded to M, not molecules, and oxidation state differs from net complex charge. The circular layout is a connectivity ledger, not a hexagonal molecular geometry or an octahedral projection. Pair arcs identify donors on the same en ligand; they are not extra metal–ligand bonds. Solvent, counterions, stereoisomers, ligand-field splitting, equilibria and alternative binding modes are omitted.',
          legend: [{ label: 'Plum pairs: two N donors from one en ligand', color: colors.plum }, { label: 'Blue: one donor from a monodentate ligand', color: colors.blue }], sources: [] };
      },
    },
    'chem.3.organic-intro': {
      title: 'Same formula, different carbon connections',
      instructions: 'Choose a carbon count, then compare a straight chain with a branched example. Each carbon has four bonds when its attached hydrogens are included.',
      initial: { carbons: 4, branched: false },
      controls: [{ key: 'carbons', label: 'Carbon atoms', min: 4, max: 8, step: 1 }, { key: 'branched', label: 'Branch the carbon skeleton', type: 'toggle' }],
      calculate(s) {
        const backbone = s.carbons - (s.branched ? 1 : 0);
        const edges = Array.from({ length: backbone - 1 }, (_, i) => [i, i + 1]);
        if (s.branched) edges.push([1, s.carbons - 1]);
        const degree = Array(s.carbons).fill(0);
        edges.forEach(([a, b]) => { degree[a]++; degree[b]++; });
        const hydrogenCounts = degree.map(n => 4 - n), hydrogens = hydrogenCounts.reduce((a, b) => a + b, 0);
        return { data: { backbone, edges, degree, hydrogenCounts, hydrogens },
          readout: s.carbons + ' carbon atoms and ' + hydrogens + ' hydrogen atoms: C' + s.carbons + 'H' + hydrogens + '. ' + (s.branched ? 'The branched example has one carbon joined to three other carbons.' : 'The unbranched example has no carbon joined to more than two other carbons.') + ' Changing the connectivity, not just turning the drawing, produces a constitutional isomer with the same formula.',
          note: 'Acyclic saturated hydrocarbons (alkanes), single bonds only. Each labelled group contains one carbon and its attached hydrogens: CH₃ means three C–H bonds, CH₂ two, and CH one. C–C bonds are the connecting lines; each carbon has total bond order four. The formula CₙH₂ₙ₊₂ follows from a connected carbon tree with n−1 C–C bonds. The two drawings are selected constitutional isomers, not every possible isomer for a given formula. Zigzags and branch angles are layout choices, not bond angles, molecular motion or a three-dimensional conformation. Rings, multiple bonds, stereochemistry and property predictions are outside this model.',
          legend: [{ label: 'Blue groups: one carbon with attached hydrogens', color: colors.blue }, { label: 'Gold: carbon bonded to three carbons', color: colors.gold }], sources: [] };
      },
    },
    'chem.2.reactions-intro': {
      title: 'Escaping gas is not disappearing matter',
      instructions: 'Advance a hypothetical gas-producing reaction. Compare open and closed boundaries and include escaped gas in the mass ledger. Gas formation alone is not proof of a chemical reaction: boiling can also produce gas.',
      initial: { progress: 50, closed: true },
      controls: [{ key: 'progress', label: 'Reaction completed (%)', min: 0, max: 100, step: 10 }, { key: 'closed', label: 'Closed system boundary', type: 'toggle' }],
      calculate(s) {
        const gas = 4.4 * s.progress / 100, nongas = 100 - gas, retained = s.closed ? gas : 0, escaped = s.closed ? 0 : gas;
        return { data: { gas, nongas, retained, escaped, reading: nongas + retained, total: nongas + retained + escaped },
          readout: (s.closed ? 'Closed' : 'Open') + ' boundary, reaction ' + s.progress + '% complete. Balance reading for retained contents: ' + numberText(nongas + retained) + ' g; escaped gas: ' + numberText(escaped) + ' g. Retained plus escaped mass is always 100 g.',
          note: 'A hypothetical reaction starts with 100 g of contents and converts at most 4.4 g into gas. The container is tared out; buoyancy, evaporation, incoming air, gas dissolution and experimental error are omitted. The remaining material and gas are portions of the same original atoms, not additional matter. In the closed case gas stays inside the weighed boundary; in the open case the model lets all produced gas leave. The progress control selects a mass-balanced snapshot, not a predicted reaction rate. This is not an instruction to seal a gas-producing reaction: pressure can make sealed containers dangerous.',
          legend: [{ label: 'Blue: non-gas contents', color: colors.blue }, { label: 'Gold: gas retained', color: colors.gold }, { label: 'Plum: gas outside the boundary', color: colors.plum }], sources: [] };
      },
    },
    'chem.3.reactions': {
      title: 'Redox transfers electrons without losing atoms',
      instructions: 'Advance the zinc–copper reaction in whole bookkeeping steps. Compare species counts with the electrons lost and gained.',
      initial: { extent: 1 },
      controls: [{ key: 'extent', label: 'Reaction units completed', min: 0, max: 4, step: 1 }],
      calculate(s) {
        return { data: { zinc: 4 - s.extent, zincIon: s.extent, copperIon: 4 - s.extent, copper: s.extent, electrons: 2 * s.extent },
          readout: s.extent + ' reaction units completed. Zinc metal remaining: ' + (4 - s.extent) + '; Zn²⁺ formed: ' + s.extent + '. Cu²⁺ remaining: ' + (4 - s.extent) + '; copper metal formed: ' + s.extent + '. Zinc loses ' + (2 * s.extent) + ' electrons and copper ions gain the same number. Four zinc atoms and four copper atoms remain in total.',
          note: 'Net ionic reaction Zn(s) + Cu²⁺(aq) → Zn²⁺(aq) + Cu(s). Each completed unit changes zinc oxidation state from 0 to +2 and copper from +2 to 0. Counts represent illustrative reaction units, not measured concentrations or isolated atoms floating in a metal. Spectator counterions, solvent, surfaces and transport are omitted; the full solution remains electrically neutral. The displayed electron total is cumulative transfer bookkeeping, not free electrons accumulating in solution. The control does not predict elapsed time, rate, equilibrium conversion or electrical work.',
          legend: [{ label: 'Blue: metal forms', color: colors.blue }, { label: 'Teal: dissolved ion forms', color: colors.teal }, { label: 'Gold: equal electron transfer', color: colors.gold }], sources: [] };
      },
    },
    'chem.2.periodic': {
      title: 'The table records a repeating electron pattern',
      instructions: 'Move through the first 18 elements. Compare the row, highlighted column and electron counts in occupied shells.',
      initial: { atomicNumber: 11 },
      controls: [{ key: 'atomicNumber', label: 'Atomic number', min: 1, max: 18, step: 1 }],
      calculate(s) {
        const symbols = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar'];
        const names = ['Hydrogen', 'Helium', 'Lithium', 'Beryllium', 'Boron', 'Carbon', 'Nitrogen', 'Oxygen', 'Fluorine', 'Neon', 'Sodium', 'Magnesium', 'Aluminium', 'Silicon', 'Phosphorus', 'Sulfur', 'Chlorine', 'Argon'];
        const elements = symbols.map((symbol, i) => {
          const z = i + 1, shells = z <= 2 ? [z] : z <= 10 ? [2, z - 2] : [2, 8, z - 10];
          const outer = shells[shells.length - 1], column = z === 2 ? 7 : outer - 1;
          return { z, symbol, name: names[i], shells, outer, column, period: shells.length, group: [1, 2, 13, 14, 15, 16, 17, 18][column] };
        });
        const selected = elements[s.atomicNumber - 1];
        return { data: { elements, selected },
          readout: selected.name + ' (' + selected.symbol + '): ' + selected.z + ' proton' + (selected.z === 1 ? '' : 's') + ' and, in a neutral atom, ' + selected.z + ' electron' + (selected.z === 1 ? '' : 's') + '. Shell counts: ' + selected.shells.join(', ') + '. Period ' + selected.period + ', group ' + selected.group + '. ' + (selected.z === 2 ? 'Helium has only two outer electrons, but its first shell is full; it belongs with the noble gases.' : selected.outer + ' outer-shell electron' + (selected.outer === 1 ? '' : 's') + '.'),
          note: 'Neutral ground-state atoms, first 18 elements only. A period tracks the highest occupied principal electron shell. These main-group columns show a repeating outer-electron pattern, with helium explicitly exceptional. Hydrogen shares one outer electron with group 1 but is chemically unlike the alkali metals. Shell totals are bookkeeping, not circular electron trajectories or a picture of orbitals. The third shell can hold more than eight electrons in later elements; this 2,8,8 pattern is not a general filling rule. Similar outer structures help explain family behaviour but do not make properties identical. The omitted transition-metal columns are not shown.',
          legend: [{ label: 'Gold: selected atom', color: colors.gold }, { label: 'Teal: other displayed atoms in its group', color: colors.teal }], sources: [] };
      },
    },
    'chem.2.acids': {
      title: 'One pH step is a tenfold change',
      instructions: 'Compare two pH values. Watch the hydronium ratio, not just the distance between the markers.',
      initial: { ph: 3, reference: 7 },
      controls: [{ key: 'ph', label: 'Sample pH', min: 0, max: 14, step: 1 }, { key: 'reference', label: 'Reference pH', min: 0, max: 14, step: 1 }],
      calculate(s) {
        const ratio = 10 ** (s.reference - s.ph), hydronium = 10 ** -s.ph, hydroxide = 10 ** (s.ph - 14);
        const comparison = s.ph === s.reference ? 'The hydronium activities are equal.' : s.ph < s.reference ? 'The sample has ' + (1 / (10 ** (s.ph - s.reference))).toExponential(0) + ' times the reference hydronium activity.' : 'The sample has 1/' + (1 / ratio).toExponential(0) + ' of the reference hydronium activity.';
        return { data: { ratio, hydronium, hydroxide, difference: s.reference - s.ph },
          readout: 'Sample pH ' + s.ph + '; reference pH ' + s.reference + '. ' + comparison + ' Sample is ' + (s.ph < 7 ? 'acidic' : s.ph > 7 ? 'basic' : 'neutral') + ' under the stated conditions.',
          note: 'pH=−log₁₀(aH₃O⁺). The displayed dimensionless activities are approximated as concentrations divided by 1 mol/L in an ideal dilute solution. At 25 °C, this model takes pKw=14, so aH₃O⁺×aOH⁻=10⁻¹⁴ and neutrality is pH 7. Activities and concentrations diverge in nonideal solutions; neutral pH also changes with temperature. The 0–14 slider is an introductory range, not an absolute limit on pH. pH alone does not measure total acid content, buffering or hazard. Never taste or touch unknown substances to test acidity.',
          legend: [{ label: 'Gold: sample pH', color: colors.gold }, { label: 'Plum: reference pH', color: colors.plum }], sources: [] };
      },
    },
    'chem.0.materials': {
      title: 'The object is not the material',
      instructions: 'Choose an object and then change what it is made from. Keep one choice fixed while changing the other.',
      initial: { object: 'spoon', material: 'wood' },
      controls: [{ key: 'object', label: 'Object', options: [{ value: 'spoon', label: 'Spoon' }, { value: 'cup', label: 'Cup' }, { value: 'button', label: 'Button' }] },
        { key: 'material', label: 'Material', options: [{ value: 'wood', label: 'Wood' }, { value: 'steel', label: 'Stainless steel' }, { value: 'plastic', label: 'Opaque plastic' }] }],
      calculate(s) {
        const names = { wood: 'wood', steel: 'stainless steel', plastic: 'opaque plastic' };
        const observations = { wood: 'Wood can show grain: lines from how a tree grew.', steel: 'Polished steel can reflect light. It is a metal.', plastic: 'Plastic can be coloured and shaped. Not all plastic looks the same.' };
        return { data: { object: s.object, material: s.material }, readout: 'This is a ' + s.object + ' made from ' + names[s.material] + '. ' + observations[s.material],
          note: 'An object is a thing, such as a spoon; a material is the stuff it is made from. These are simplified examples of solid objects. Water and air are also materials, even though they cannot keep these shapes by themselves. Colour alone cannot identify a material. The pictured finishes are examples, not properties of every sample; real objects may combine several materials.',
          legend: [{ label: 'Gold with grain: example wood finish', color: colors.gold }, { label: 'Blue with highlight: example steel finish', color: colors.blue }, { label: 'Coral: example opaque plastic finish', color: colors.coral }], sources: [] };
      },
    },
    'chem.1.materials-props': {
      title: 'The right material depends on the job',
      instructions: 'Choose properties your design needs. Compare the samples: a match must meet every selected requirement.',
      initial: { clear: true, flexible: false, rain: false },
      controls: [{ key: 'clear', label: 'Need a clear view', type: 'toggle' }, { key: 'flexible', label: 'Need it to bend easily', type: 'toggle' }, { key: 'rain', label: 'Need to block rain', type: 'toggle' }],
      calculate(s) {
        const samples = [{ name: 'Clear acrylic pane', properties: [true, false, true] }, { name: 'Cotton cloth', properties: [false, true, false] },
          { name: 'Clear PE film', properties: [true, true, true] }, { name: 'Thick steel sheet', properties: [false, false, true] }];
        const requirements = [s.clear, s.flexible, s.rain];
        const matches = samples.map(sample => requirements.every((needed, i) => !needed || sample.properties[i]));
        const needs = ['clear view', 'easy bending', 'rain blocking'].filter((_, i) => requirements[i]);
        return { data: { samples, requirements, matches }, readout: 'Needs: ' + (needs.join(', ') || 'none') + '. ' + matches.filter(Boolean).length + ' samples meet all selected requirements: ' + samples.filter((_, i) => matches[i]).map(x => x.name).join(', ') + '.',
          note: 'Qualitative sample comparisons, not engineering specifications: an intact clear acrylic pane, untreated woven cotton cloth, intact clear polyethylene (PE) film and a thick steel sheet. Thickness, coatings, weave and damage change performance. A clear view means seeing a sharp image, not merely letting some light through. Blocking rain is not the same as blocking water vapour. Strength, heat, durability, cost and environmental impact are not scored, so a match is a candidate to investigate, not a universally best material. With no requirements, every sample qualifies.',
          legend: [{ label: 'Yes/no: observed sample property', color: colors.blue }, { label: 'Teal row: meets every chosen need', color: colors.teal }], sources: [] };
      },
    },
    'chem.5.materials': {
      title: 'Heating changes diffusion exponentially',
      instructions: 'Explore a hypothetical dopant in a solid. Compare the diffusion coefficient and characteristic penetration scale as temperature, barrier and time change.',
      initial: { temperature: 800, barrier: 120, time: 100 },
      controls: [{ key: 'temperature', label: 'Temperature (K)', min: 500, max: 1200, step: 50 },
        { key: 'barrier', label: 'Activation energy (kJ/mol)', min: 80, max: 160, step: 10 },
        { key: 'time', label: 'Diffusion time (s)', min: 0, max: 400, step: 20 }],
      calculate(s) {
        const coefficient = 1e-6 * Math.exp(-s.barrier * 1000 / (8.314462618 * s.temperature));
        const length = 2 * Math.sqrt(coefficient * s.time) * 1e6;
        const logD = temperature => -6 - s.barrier * 1000 / (8.314462618 * temperature * Math.LN10);
        return { data: { coefficient, length, logCoefficient: logD(s.temperature), curve: Array.from({ length: 71 }, (_, i) => logD(500 + 10 * i)) },
          readout: 'D = ' + coefficient.toExponential(2) + ' m²/s. Characteristic scale 2√(Dt) = ' + smallLengthText(length) + ' micrometres. Four times the duration gives twice this length at fixed temperature and material parameters.',
          note: 'Single Arrhenius regime, D=D₀ exp(−Q/RT), with illustrative D₀=10⁻⁶ m²/s and Q converted from kJ/mol to J/mol. Parameters are not fitted to a real dopant or material. The scale 2√(Dt) describes diffusion-profile spreading, not a sharp front, mean displacement or maximum atom travel distance. The graph uses a base-10 logarithmic vertical axis, so one vertical unit means a tenfold change in D. No phase changes, concentration dependence, grain-boundary pathways, trapping or finite boundaries are modelled. Actual semiconductor processing needs measured parameters and boundary conditions.',
          legend: [{ label: 'Teal: diffusion coefficient at each temperature', color: colors.teal }, { label: 'Gold: selected temperature', color: colors.gold }],
          sources: [{ label: 'NIMS: diffusion equation and characteristic length', url: 'https://diffusion.nims.go.jp/' }] };
      },
    },
    'chem.1.changes': {
      title: 'A change of state or a new substance?',
      instructions: 'Compare melting with water decomposition. Move through the snapshots and count atoms before and after; look for changes in which atoms are joined.',
      initial: { process: 'melting', stage: 0 },
      controls: [{ key: 'process', label: 'Process', options: [{ value: 'melting', label: 'Melting ice' }, { value: 'reaction', label: 'Decomposing water' }] },
        { key: 'stage', label: 'Snapshot', min: 0, max: 2, step: 1 }],
      calculate(s) {
        const extent = s.process === 'reaction' ? s.stage : 0;
        const water = 4 - 2 * extent, hydrogen = 2 * extent, oxygen = extent;
        return { data: { water, hydrogen, oxygen, hydrogenAtoms: 2 * water + 2 * hydrogen, oxygenAtoms: water + 2 * oxygen },
          readout: (s.process === 'melting' ? ['Ice: water molecules stay joined in an ordered arrangement.', 'Partly melted: some water molecules have left the ordered arrangement.', 'Liquid water: the arrangement changes, but every molecule is still H₂O.'][s.stage] : 'After reaction: ' + water + ' H₂O, ' + hydrogen + ' H₂ and ' + oxygen + ' O₂ molecules. Chemical bonds have ' + (extent ? 'changed.' : 'not yet changed.')) + ' Both snapshots contain 8 hydrogen atoms and 4 oxygen atoms.',
          note: 'Circles are atoms and short lines show bonds inside molecules. Positions are schematic, not a scale model of ice structure or molecular motion. Melting changes intermolecular arrangement without splitting H₂O. Decomposition uses 2 H₂O → 2 H₂ + O₂ and requires an energy input, such as electrical energy; ordinary melting does not produce these gases. Discrete snapshots count completed reaction events, not elapsed time or a reaction mechanism. This is not an experiment to perform: hydrogen–oxygen mixtures can be explosive.',
          legend: [{ label: 'Blue O: oxygen atom', color: colors.blue }, { label: 'Gold H: hydrogen atom', color: colors.gold }], sources: [] };
      },
    },
    'chem.4.electrochem': {
      title: 'The same electrodes can still make a voltage',
      instructions: 'Set the zinc-ion concentrations on the left and right. Swap them to reverse polarity, or make them equal to remove the concentration driving force.',
      initial: { left: -2, right: -1, temperature: 298 },
      controls: [{ key: 'left', label: 'Left Zn²⁺ concentration: 10 to this power M', min: -3, max: 0, step: 1 },
        { key: 'right', label: 'Right Zn²⁺ concentration: 10 to this power M', min: -3, max: 0, step: 1 },
        { key: 'temperature', label: 'Temperature (K)', min: 273, max: 333, step: 5 }],
      calculate(s) {
        const voltage = 8.314462618 * s.temperature / (2 * 96485.33212) * Math.LN10 * (s.right - s.left), direction = Math.sign(voltage);
        return { data: { voltage, direction, leftConcentration: 10 ** s.left, rightConcentration: 10 ** s.right },
          readout: 'Right minus left potential: ' + numberText(voltage * 1000) + ' mV. ' + (direction === 0 ? 'Equal activities give zero concentration-cell voltage in this model.' : 'If an external conducting path is connected, electrons flow ' + (direction > 0 ? 'left to right. Left zinc oxidises; right zinc ions are reduced.' : 'right to left. Right zinc oxidises; left zinc ions are reduced.')),
          note: 'Ideal Zn(s)/Zn²⁺ concentration cell: Eright−Eleft=(RT/2F) ln(aRight/aLeft), with activities approximated by concentrations divided by the 1 M standard state. Pure zinc activities are one and both standard electrode potentials cancel. A salt bridge completes ionic conduction, not electron transport; its junction potential is neglected. The displayed value is an equilibrium open-circuit prediction, not loaded terminal voltage, current, power or a time simulation. Nonideality, electrode kinetics, resistance and concentration changes during operation are omitted. The liquid tint is schematic, not the colour of zinc-ion solutions.',
          legend: [{ label: 'Gold arrow: possible external electron-flow direction', color: colors.gold }, { label: 'Plum: ionic salt bridge', color: colors.plum }],
          sources: [{ label: 'OpenStax: concentration cells and the Nernst equation', url: 'https://openstax.org/books/chemistry-2e/pages/17-4-potential-free-energy-and-equilibrium' }] };
      },
    },
    'chem.5.biochem': {
      title: 'More substrate does not overcome every inhibitor',
      instructions: 'Compare competitive and pure noncompetitive inhibition against the same uninhibited enzyme. Inspect rates at different substrate and inhibitor levels.',
      initial: { substrate: 4, inhibitor: 2, mechanism: 'competitive' },
      controls: [{ key: 'substrate', label: 'Substrate concentration (model units)', min: 0, max: 10, step: .5 },
        { key: 'inhibitor', label: 'Free inhibitor concentration (model units)', min: 0, max: 8, step: .5 },
        { key: 'mechanism', label: 'Inhibition mechanism', options: [{ value: 'competitive', label: 'Competitive' }, { value: 'noncompetitive', label: 'Pure noncompetitive' }] }],
      calculate(s) {
        const factor = 1 + s.inhibitor / 2, km = s.mechanism === 'competitive' ? 2 * factor : 2, vmax = s.mechanism === 'competitive' ? 1 : 1 / factor;
        const rate = substrate => vmax * substrate / (km + substrate);
        return { data: { factor, km, vmax, rate: rate(s.substrate), reference: s.substrate / (2 + s.substrate), curve: Array.from({ length: 101 }, (_, i) => rate(i / 10)) },
          readout: 'Initial rate ' + numberText(rate(s.substrate)) + ', versus uninhibited ' + numberText(s.substrate / (2 + s.substrate)) + ' in model rate units. Apparent Km=' + numberText(km) + '; high-substrate limit=' + numberText(vmax) + '. ' + (s.mechanism === 'competitive' ? 'Competitive inhibition raises apparent Km but leaves the limiting rate unchanged.' : 'Pure noncompetitive inhibition lowers the limiting rate without changing apparent Km.'),
          note: 'Reversible initial-rate models with baseline Vmax=1, Km=2 and Ki=2 in illustrative units. Competitive binding excludes substrate binding. Pure noncompetitive inhibition assumes equal inhibitor affinity for free enzyme and enzyme–substrate complex and no turnover from the inhibited complex; it is a special case, not every allosteric mechanism. Free inhibitor is held fixed; substrate depletion, cooperativity and time-dependent inhibition are omitted. These curves are not measured enzyme data, treatment advice or dose predictions. The high-substrate limit is an asymptote, not a value reached at a finite slider setting.',
          legend: [{ label: 'Dashed: uninhibited enzyme', color: colors.ink }, { label: 'Teal: inhibited rate curve', color: colors.teal }, { label: 'Gold: inspected substrate level', color: colors.gold }],
          sources: [{ label: 'Assay Guidance Manual: enzyme inhibition mechanisms', url: 'https://www.ncbi.nlm.nih.gov/books/NBK92001/' }] };
      },
    },
    'chem.5.frontier': {
      title: 'Yield, atom economy and waste answer different questions',
      instructions: 'Compare hypothetical routes using a one-batch mass ledger. Change theoretical product fraction, isolated yield and solvent recovery.',
      initial: { economy: 80, yield: 90, solvent: 300, recovery: 50 },
      controls: [{ key: 'economy', label: 'Route atom economy (%)', min: 50, max: 100, step: 10 },
        { key: 'yield', label: 'Isolated yield (% of theoretical product)', min: 0, max: 100, step: 10 },
        { key: 'solvent', label: 'Solvent input (g)', min: 0, max: 500, step: 50 },
        { key: 'recovery', label: 'Solvent recovered for reuse (%)', min: 0, max: 100, step: 10 }],
      calculate(s) {
        const product = s.economy * s.yield / 100, recovered = s.solvent * s.recovery / 100, waste = 100 - product + s.solvent - recovered, input = 100 + s.solvent;
        return { data: { product, recovered, waste, input, eFactor: product ? waste / product : null, grossPMI: product ? input / product : null },
          readout: 'Atom economy ' + s.economy + '%; isolated yield ' + s.yield + '%. From 100 g stoichiometric feed and ' + s.solvent + ' g solvent: ' + numberText(product) + ' g product, ' + numberText(waste) + ' g waste, ' + numberText(recovered) + ' g recovered solvent. ' + (product ? 'Waste/product E-factor ' + numberText(waste / product) + '; gross input/product ' + numberText(input / product) + '.' : 'No isolated product: waste/product and input/product ratios are undefined.'),
          note: 'Hypothetical stoichiometric routes: the chosen atom economy sets theoretical product mass from 100 g reactant feed. Isolated yield reduces that product; every non-product feed component is counted as waste, with no feed recovery. Solvent passes unchanged into waste or a recovered stream. Recovered solvent is not counted as waste at this batch boundary, but is included in gross input. Thus gross input/product equals E+1+recovered/product, not necessarily E+1. Recovery energy, toxicity, water, catalysts, upstream production and life-cycle effects are omitted. Lower mass waste alone does not establish a safer or more sustainable process.',
          legend: [{ label: 'Teal: isolated product', color: colors.teal }, { label: 'Coral: waste', color: colors.coral }, { label: 'Gold: recovered solvent, not waste at this boundary', color: colors.gold }],
          sources: [{ label: 'ACS: green chemistry and engineering metrics', url: 'https://www.acs.org/green-chemistry-sustainability/research-innovation/engineerings-metrics.html' }] };
      },
    },
    'chem.4.analytical': {
      title: 'A blank signal can masquerade as analyte',
      instructions: 'Generate a toy absorbance measurement, then infer concentration with or without subtracting a matching blank.',
      initial: { concentration: 4, path: 1, blank: .3, correct: false },
      controls: [{ key: 'concentration', label: 'True toy concentration (model units)', min: 0, max: 10, step: 1 },
        { key: 'path', label: 'Optical path length (cm)', min: 1, max: 3, step: 1 },
        { key: 'blank', label: 'Background absorbance', min: 0, max: 1, step: .1 },
        { key: 'correct', label: 'Subtract matching blank', type: 'toggle' }],
      calculate(s) {
        const slope = .1 * s.path, analyte = slope * s.concentration, measured = analyte + s.blank, used = measured - (s.correct ? s.blank : 0), inferred = used / slope;
        return { data: { slope, analyte, measured, used, inferred, transmittance: 10 ** -measured },
          readout: 'Raw absorbance ' + numberText(measured) + '; transmitted light ' + numberText(100 * 10 ** -measured) + '%. ' + (s.correct ? 'After blank subtraction: ' : 'Without blank subtraction: ') + numberText(used) + ' absorbance gives inferred concentration ' + numberText(inferred) + ', versus true toy value ' + s.concentration + '.',
          note: 'Beer–Lambert toy model A=εlc with invented ε=0.1 per concentration unit per cm, plus additive background absorbance. The same path length is used for calibration and sample. Blank subtraction assumes a perfectly matched blank; no noise, scattering, chemical change, stray light or detector limits are included. Inferred values above the plotted 0–10 calibration range are extrapolations, not validated measurements. Absorbance is logarithmic: doubling absorbance does not halve transmitted intensity.',
          legend: [{ label: 'Teal: analyte-only calibration', color: colors.teal }, { label: 'Gold: signal used for inference at true concentration', color: colors.gold }],
          sources: [{ label: 'IUPAC: Beer–Lambert law', url: 'https://goldbook.iupac.org/terms/view/B00626' }] };
      },
    },
    'chem.5.compchem': {
      title: 'Variational energy balances localisation and spread',
      instructions: 'Vary the width parameter and centre of a normalised Gaussian trial state. Find the lowest energy in the harmonic-oscillator model.',
      initial: { alpha: 20, centre: .5 },
      controls: [{ key: 'alpha', label: 'Gaussian α × 10 (larger = narrower)', min: 2, max: 30, step: 1 },
        { key: 'centre', label: 'Trial-state centre q (oscillator units)', min: -2, max: 2, step: .25 }],
      calculate(s) {
        const a = s.alpha / 10, kinetic = a / 4, potential = 1 / (4 * a) + s.centre ** 2 / 2, energy = kinetic + potential;
        return { data: { a, kinetic, potential, energy, variance: 1 / (2 * a), curve: Array.from({ length: 57 }, (_, i) => { const v = .2 + i * .05; return (v + 1 / v) / 4 + s.centre ** 2 / 2; }) },
          readout: 'Kinetic energy ' + numberText(kinetic) + ', potential energy ' + numberText(potential) + ', total ' + numberText(energy) + ' ħω. Position variance ' + numberText(1 / (2 * a)) + '. The global minimum is 0.5 ħω at α=1 and q=0; the plotted slice keeps q=' + s.centre + ' fixed.',
          note: 'Dimensionless harmonic oscillator H=−½d²/dx²+x²/2 with trial ψ=(α/π)¼ exp[−α(x−q)²/2]. Analytic expectation E=(α+1/α)/4+q²/2. Narrowing raises kinetic energy; spreading raises potential energy. This trial family happens to include the exact ground state, unlike most molecular approximations. The variational upper bound applies to this specified Hamiltonian, not to experimental molecular energies under an incomplete physical model. This is a closed-form trial-state calculation, not an electronic-structure package or convergence proof for real molecules.',
          legend: [{ label: 'Teal: energy versus α at fixed centre', color: colors.teal }, { label: 'Gold: chosen trial state', color: colors.gold }, { label: 'Dashed: exact ground-state lower bound', color: colors.ink }],
          sources: [{ label: 'McCullagh Lab: Gaussian variational oscillator calculations', url: 'https://mccullaghlab.github.io/physical_chemistry/quantum_mechanics/harmonic_oscillator_using_variational_method.html' }] };
      },
    },
    'chem.2.mixtures': {
      title: 'A filter separates particles, not dissolved material',
      instructions: 'Add a model solute and insoluble sand to water. Change the water amount, then pass the equilibrated mixture through an ideal filter.',
      initial: { water: 200, solute: 10, sand: 3, filter: false },
      controls: [{ key: 'water', label: 'Water volume (mL)', min: 100, max: 500, step: 100 },
        { key: 'solute', label: 'Model solute added (g)', min: 0, max: 20, step: 1 },
        { key: 'sand', label: 'Insoluble sand added (g)', min: 0, max: 10, step: 1 },
        { key: 'filter', label: 'Apply ideal filtration', type: 'toggle' }],
      calculate(s) {
        const capacity = 4 * s.water / 100, dissolved = Math.min(s.solute, capacity), excess = s.solute - dissolved;
        const vessel = [dissolved, s.filter ? 0 : excess, s.filter ? 0 : s.sand], residue = [0, s.filter ? excess : 0, s.filter ? s.sand : 0];
        return { data: { capacity, dissolved, excess, vessel, residue },
          readout: 'At this water amount, at most ' + capacity + ' g of the model solute dissolves. ' + dissolved + ' g is dissolved and ' + excess + ' g remains solid. ' + (s.filter ? 'The filtrate still contains all ' + dissolved + ' g of dissolved solute; the filter holds ' + (excess + s.sand) + ' g of solids.' : 'The unfiltered vessel contains both the liquid and any undissolved material, including ' + s.sand + ' g of sand.'),
          note: 'Invented solute with fixed solubility 4 g per 100 mL water at one fixed temperature, not a real salt’s measured value. Dissolution is assumed complete up to this limit before filtering. The ideal filter retains all solid particles and passes all liquid, with no adsorption, trapped liquid, evaporation or loss. Sand is treated as entirely insoluble. Dissolved solute remains present even if the filtrate looks clear. Water volume is solvent volume, not a calculated final solution volume.',
          legend: [{ label: 'Teal: dissolved solute', color: colors.teal }, { label: 'Gold: undissolved solute', color: colors.gold }, { label: 'Coral: sand', color: colors.coral }], sources: [] };
      },
    },
    'chem.3.atomic-structure': {
      title: 'Element, isotope and charge count different things',
      instructions: 'Change protons, neutrons and electrons independently. Notice which changes the element, the mass number or the charge.',
      initial: { protons: 6, neutrons: 6, electrons: 6 },
      controls: [{ key: 'protons', label: 'Protons', min: 1, max: 10, step: 1 },
        { key: 'neutrons', label: 'Neutrons', min: 0, max: 12, step: 1 },
        { key: 'electrons', label: 'Electrons', min: 0, max: 12, step: 1 }],
      calculate(s) {
        const symbols = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne'], names = ['Hydrogen', 'Helium', 'Lithium', 'Beryllium', 'Boron', 'Carbon', 'Nitrogen', 'Oxygen', 'Fluorine', 'Neon'];
        const mass = s.protons + s.neutrons, charge = s.protons - s.electrons;
        return { data: { symbol: symbols[s.protons - 1], name: names[s.protons - 1], mass, charge },
          readout: names[s.protons - 1] + ': atomic number Z=' + s.protons + ', mass number A=' + mass + ', charge ' + (charge > 0 ? '+' : '') + charge + ' elementary-charge units. ' + (charge === 0 ? 'Equal proton and electron counts give a neutral atom.' : charge > 0 ? 'Fewer electrons than protons give a positive ion.' : 'More electrons than protons give a negative ion.'),
          note: 'A counting model, not a stability or orbital calculation. The sliders include hypothetical nuclei and ions that may be unbound or short-lived; no stability is implied. Mass number counts nucleons and is not the measured atomic mass or the periodic table’s isotope-weighted average. The inventory bars do not depict particle size, position or electron trajectories. Changing neutron count keeps the element; changing proton count does not.',
          legend: [{ label: 'Coral: protons (+)', color: colors.coral }, { label: 'Gold: neutrons (0)', color: colors.gold }, { label: 'Teal: electrons (−)', color: colors.teal }], sources: [] };
      },
    },
    'chem.3.gases': {
      title: 'Pressure depends on what you hold fixed',
      instructions: 'Change volume, absolute temperature or amount. The pressure–volume curve holds the selected temperature and amount fixed.',
      initial: { volume: 15, temperature: 300, amount: 1 },
      controls: [{ key: 'volume', label: 'Volume (L)', min: 5, max: 30, step: 1 },
        { key: 'temperature', label: 'Absolute temperature (K)', min: 200, max: 600, step: 10 },
        { key: 'amount', label: 'Amount (mol)', min: 1, max: 5, step: 1 }],
      calculate(s) {
        const nrt = s.amount * 8.314462618 * s.temperature;
        return { data: { pressure: nrt / s.volume, nrt, curve: Array.from({ length: 51 }, (_, i) => nrt / (5 + i / 2)) },
          readout: 'P = nRT/V = ' + numberText(nrt / s.volume) + ' kPa. PV = ' + numberText(nrt) + ' kPa·L. At fixed amount and temperature, doubling volume halves pressure; heating at fixed volume instead raises pressure.',
          note: 'Ideal-gas equation with R=8.314462618 kPa·L/(mol·K), absolute pressure and kelvin temperature. Real gases deviate, especially near condensation or at high density. The curve is a set of equilibrium states, not a time trace or a prediction of the temperature during rapid compression. No microscopic collisions or heat-transfer dynamics are simulated.',
          legend: [{ label: 'Teal: fixed-n, fixed-T pressure–volume curve', color: colors.teal }, { label: 'Gold: selected state', color: colors.gold }],
          sources: [{ label: 'OpenStax: the ideal gas law', url: 'https://openstax.org/books/chemistry-2e/pages/9-2-relating-pressure-volume-amount-and-temperature-the-ideal-gas-law' }] };
      },
    },
    'chem.3.energy': {
      title: 'A lower barrier does not change the energy endpoints',
      instructions: 'Set reaction energy change and the barrier above the higher endpoint. Compare an alternative catalysed pathway.',
      initial: { change: -30, barrier: 60, catalyst: false },
      controls: [{ key: 'change', label: 'Product minus reactant energy (kJ/mol)', min: -60, max: 60, step: 10 },
        { key: 'barrier', label: 'Barrier above higher endpoint (kJ/mol)', min: 20, max: 80, step: 10 },
        { key: 'catalyst', label: 'Show lower-barrier pathway', type: 'toggle' }],
      calculate(s) {
        const peak = Math.max(0, s.change) + s.barrier, active = Math.max(0, s.change) + s.barrier * (s.catalyst ? .5 : 1);
        return { data: { peak, active, forward: active, reverse: active - s.change },
          readout: 'Forward barrier ' + active + ', reverse barrier ' + (active - s.change) + ' kJ/mol. Endpoint change remains ' + s.change + ' kJ/mol. ' + (s.change < 0 ? 'Products lie lower in energy.' : s.change > 0 ? 'Products lie higher in energy.' : 'Products and reactants have equal energy in this diagram.'),
          note: 'An invented one-step reaction-energy profile with reactants at zero. The alternative pathway halves the excess barrier above the higher endpoint; it is not a measured catalyst effect. Reaction coordinate is not time or distance. The endpoints do not move when catalysis is selected, and catalysis does not change the equilibrium constant. No rate constant is calculated: temperature, prefactors and mechanism also matter. This energy sketch alone does not determine Gibbs energy or spontaneity.',
          legend: [{ label: 'Grey dashed: original pathway', color: colors.ink }, { label: 'Teal: selected pathway', color: colors.teal }, { label: 'Gold: product energy', color: colors.gold }],
          sources: [{ label: 'OpenStax: catalysis and reaction-energy diagrams', url: 'https://openstax.org/books/chemistry-2e/pages/12-7-catalysis' }] };
      },
    },
    'chem.4.physical': {
      title: 'Equilibrium fixes a ratio, not equal amounts',
      instructions: 'For a closed A ⇌ B system, change the starting composition and equilibrium constant. Inspect intermediate compositions on the way to equilibrium.',
      initial: { initialB: 2, power: 1, progress: 50 },
      controls: [{ key: 'initialB', label: 'Initial B (mol; total A+B = 10)', min: 0, max: 10, step: 1 },
        { key: 'power', label: 'Equilibrium constant K = 2 to this power', min: -2, max: 2, step: 1 },
        { key: 'progress', label: 'Fraction of composition adjustment (%)', min: 0, max: 100, step: 10 }],
      calculate(s) {
        const k = 2 ** s.power, equilibriumB = 10 * k / (1 + k), b = s.initialB + (equilibriumB - s.initialB) * s.progress / 100, a = 10 - b;
        const q = a === 0 ? null : b / a, direction = Math.abs(b - equilibriumB) < 1e-10 ? 'balanced' : b < equilibriumB ? 'towards B' : 'towards A';
        return { data: { k, equilibriumB, a, b, q, direction },
          readout: 'K=' + k + '. Current A=' + numberText(a) + ', B=' + numberText(b) + ' mol; Q=B/A ' + (q === null ? 'has no finite value because A is absent' : '=' + numberText(q)) + '. Net thermodynamic direction: ' + direction + '. Equilibrium B=' + numberText(equilibriumB) + ' mol.',
          note: 'Ideal one-to-one interconversion with a conserved total of 10 mol, fixed temperature/volume for each chosen K and activities represented by concentrations. K is varied to compare hypothetical systems; changing starting amounts alone does not change K. The progress control interpolates composition, not elapsed time or a rate law. At equilibrium forward and reverse processes continue at equal rates; amounts are equal only when K=1. Pure-component boundary states have limiting reaction quotients, not numerical infinities displayed as measurements.',
          legend: [{ label: 'Teal: A', color: colors.teal }, { label: 'Gold: B', color: colors.gold }],
          sources: [{ label: 'OpenStax: equilibrium and reaction quotient', url: 'https://openstax.org/books/chemistry-2e/pages/13-3-shifting-equilibria-le-chateliers-principle' }] };
      },
    },
    'chem.3.stoichiometry': {
      title: 'Balance atoms by changing coefficients, not formulas',
      instructions: 'Adjust the amounts of H₂, O₂ and H₂O. Match both elemental ledgers; a balanced ratio need not be the smallest whole-number ratio.',
      initial: { hydrogen: 1, oxygen: 1, water: 1 },
      controls: [{ key: 'hydrogen', label: 'H₂ coefficient', min: 1, max: 6, step: 1 },
        { key: 'oxygen', label: 'O₂ coefficient', min: 1, max: 6, step: 1 },
        { key: 'water', label: 'H₂O coefficient', min: 1, max: 6, step: 1 }],
      calculate(s) {
        const left = [2 * s.hydrogen, 2 * s.oxygen], right = [2 * s.water, s.water], difference = left.map((v, i) => right[i] - v), balanced = difference.every(v => v === 0);
        return { data: { left, right, difference, balanced },
          readout: s.hydrogen + ' H₂ + ' + s.oxygen + ' O₂ → ' + s.water + ' H₂O. ' + (balanced ? 'Both atom counts match. ' + (s.oxygen === 1 ? 'This is the smallest whole-number ratio.' : 'Divide every coefficient by ' + s.oxygen + ' for the smallest whole-number ratio.') : 'Not balanced: products minus reactants gives H ' + difference[0] + ', O ' + difference[1] + '. A negative difference means fewer atoms on the product side.'),
          note: 'Coefficients count representative molecules or proportional amounts in moles; subscripts define the species and are never edited. Atom counts alone do not establish reaction rate, conditions or actual yield. This ledger describes an equation, not a safe experiment or a model of molecular collisions. Hydrogen and oxygen mixtures can be explosive; do not attempt this reaction.',
          legend: [{ label: 'Teal: reactant atom count', color: colors.teal }, { label: 'Gold: product atom count', color: colors.gold }], sources: [] };
      },
    },
    'chem.0.mixing': {
      title: 'Mixed together does not always mean dissolved',
      instructions: 'Choose a small addition to water. Compare just after stirring with after resting.',
      initial: { material: 'sand', resting: false },
      controls: [{ key: 'material', label: 'Add to water', options: [{ value: 'sand', label: 'Sand' }, { value: 'salt', label: 'Salt' }, { value: 'oil', label: 'Oil' }] },
        { key: 'resting', label: 'Let the mixture rest', type: 'toggle' }],
      calculate(s) {
        const outcome = s.material === 'salt' ? 'Dissolved salt stays spread through the water' : s.material === 'sand' ? s.resting ? 'Sand settles to the bottom' : 'Stirring lifts sand through the water' : s.resting ? 'Oil droplets rejoin a separate upper layer' : 'Stirring breaks oil into temporary droplets';
        return { data: { outcome, dispersed: s.material === 'salt' || !s.resting, layer: s.material === 'oil' && s.resting, sediment: s.material === 'sand' && s.resting },
          readout: outcome + '. ' + (s.material === 'salt' ? (s.resting ? 'Resting does not make dissolved salt settle.' : 'The small salt addition is below its solubility limit.') : 'Stirring changes distribution, not whether this material dissolves.'),
          note: 'A qualitative water-mixture comparison, not a timed simulation. Sand represents insoluble grains; the oil is less dense than water and no emulsifier is present. A small amount of table salt dissolves as ions, not visible grains. Symbols show where material is, not its actual size or number. Salt has not vanished when the solution looks clear. This activity is virtual: never mix unknown household chemicals.',
          legend: [{ label: 'Blue: water', color: colors.blue }, { label: 'Gold: sand, salt symbols or oil as labelled', color: colors.gold }],
          sources: [{ label: 'OpenStax: dissolution and immiscible liquids', url: 'https://openstax.org/books/chemistry-2e/pages/11-1-the-dissolution-process' }] };
      },
    },
    'chem.0.water-states': {
      title: 'Water changes arrangement, not identity',
      instructions: 'Move from ice through melting, liquid water and boiling to vapour. Each little bent symbol still represents water.',
      initial: { stage: 2 },
      controls: [{ key: 'stage', label: 'Stage along a heating path', min: 0, max: 4, step: 1 }],
      calculate(s) {
        const names = ['Ice', 'Ice and liquid: melting', 'Liquid water', 'Liquid and vapour: boiling', 'Water vapour'];
        const counts = [[12, 0, 0], [6, 6, 0], [0, 12, 0], [0, 6, 6], [0, 0, 12]][s.stage];
        return { data: { name: names[s.stage], counts },
          readout: names[s.stage] + '. Twelve representative water symbols remain twelve: ' + counts[0] + ' in the solid region, ' + counts[1] + ' in liquid and ' + counts[2] + ' in vapour. Move backwards to represent cooling and condensation/freezing.',
          note: 'Schematic snapshots of heating pure water at ordinary atmospheric pressure, not equal time or equal energy steps. Melting and boiling can contain two phases at once. Molecules retain their identity; their arrangement and motion change. Spacing, density and number are not to scale. Water vapour is invisible; a visible white steam cloud consists of tiny liquid droplets. The imagined system retains its water, unlike an open kettle. Do not handle boiling water to imitate this virtual activity.',
          legend: [{ label: 'Each symbol: one blue oxygen and two gold hydrogens', color: colors.blue }],
          sources: [{ label: 'OpenStax: phases of matter', url: 'https://openstax.org/books/chemistry-2e/pages/1-2-phases-and-classification-of-matter' }] };
      },
    },
    'chem.1.matter': {
      title: 'Shape and volume answer different questions',
      instructions: 'Change the container width while keeping the amount of material. Compare a solid, liquid and gas.',
      initial: { phase: 'solid', width: 220 },
      controls: [{ key: 'phase', label: 'State of matter', options: ['solid', 'liquid', 'gas'].map(value => ({ value, label: value[0].toUpperCase() + value.slice(1) })) },
        { key: 'width', label: 'Container width (diagram units)', min: 140, max: 300, step: 10 }],
      calculate(s) {
        const width = s.phase === 'solid' ? 100 : s.width, height = s.phase === 'solid' ? 96 : s.phase === 'liquid' ? 9600 / s.width : 180;
        return { data: { width, height, area: width * height, count: 12 },
          readout: s.phase === 'solid' ? 'The solid keeps its 100 × 96 shape while the container changes to width ' + s.width + '.' : s.phase === 'liquid' ? 'The liquid spreads to width ' + s.width + ' and depth ' + numberText(height) + '; its cross-section area stays 9600.' : 'The gas spreads throughout the container: width ' + s.width + ', height 180. The same amount now occupies area ' + width * height + '.',
          note: 'A two-dimensional cross-section with fixed depth into the page: area represents volume. Solid and liquid are treated as incompressible; gas fills its sealed container. Twelve symbols represent the same amount within each comparison, not literal particles or equal masses across phases. No forces, pressure, phase transition or realistic molecular sizes are calculated. Real solids and liquids can compress slightly. Container resizing stands for comparing containers; it is not a simulation of pouring or a moving wall.',
          legend: [{ label: 'Teal: occupied region', color: colors.teal }, { label: 'Blue dots: representative particles', color: colors.blue }],
          sources: [{ label: 'OpenStax: shape and volume of matter', url: 'https://openstax.org/books/chemistry-2e/pages/1-2-phases-and-classification-of-matter' }] };
      },
    },
    'bio.1.health': {
      title: 'Soap loosens; rinsing carries material away',
      instructions: 'Follow the washing sequence, then explore why touching a dirty surface afterwards matters.',
      initial: { stage: 5, contact: false },
      controls: [{ key: 'stage', label: 'Washing stage', min: 0, max: 5, step: 1 },
        { key: 'contact', label: 'Touch a dirty surface after rinsing', type: 'toggle' }],
      calculate(s) {
        const stages = ['Before washing', 'Wet hands', 'Lather with soap', 'Scrub for at least 20 seconds', 'Rinse under running water', 'Dry with a clean towel or air dryer'];
        const returned = s.contact && s.stage >= 4;
        return { data: { stage: stages[s.stage], returned, particles: s.stage < 4 ? 12 : returned ? 6 : 0 },
          readout: 'Stage ' + s.stage + ': ' + stages[s.stage] + '. ' + (returned ? 'Contact can transfer material back onto washed hands.' : s.contact ? 'The later contact happens only after rinsing; it has not happened at this stage.' : 'Move through every stage; a slider does not replace real washing.'),
          note: 'Wet hands with clean running water, add soap, and lather backs, between fingers and under nails. Scrub for at least 20 seconds, rinse and dry. Friction and soap help loosen material; water carries it away. The dots are a diagram of transferable material, not measured germ counts or a prediction of disinfection. No visible dots does not mean sterile hands: microbes can remain invisible.',
          legend: [{ label: 'Gold dots: illustrative transferable material, not germ counts', color: colors.gold }, { label: 'Blue: water; pale circles: lather', color: colors.blue }],
          sources: [{ label: 'CDC: community handwashing steps', url: 'https://www.cdc.gov/handwashing' }] };
      },
    },
    'bio.3.microbiology': {
      title: 'Selection changes both composition and abundance',
      instructions: 'Start with existing resistant and susceptible lineages. Compare their abundance and resistant fraction with and without exposure.',
      initial: { percent: 10, generation: 3, drug: true },
      controls: [{ key: 'percent', label: 'Initial resistant fraction (%)', min: 0, max: 100, step: 1 },
        { key: 'generation', label: 'Selection rounds', min: 0, max: 6, step: 1 },
        { key: 'drug', label: 'Antimicrobial exposure', type: 'toggle' }],
      calculate(s) {
        const resistantFactor = s.drug ? 1.2 : 1.8, susceptibleFactor = s.drug ? .25 : 2;
        const history = Array.from({ length: 7 }, (_, t) => {
          const resistant = s.percent * resistantFactor ** t, susceptible = (100 - s.percent) * susceptibleFactor ** t;
          return { resistant, susceptible, total: resistant + susceptible, fraction: resistant / (resistant + susceptible) };
        });
        const selected = history[s.generation];
        return { data: { history, selected, resistantFactor, susceptibleFactor },
          readout: 'Round ' + s.generation + ': resistant ' + numberText(selected.resistant) + ', susceptible ' + numberText(selected.susceptible) + ', total ' + numberText(selected.total) + ' abundance units. Resistant fraction: ' + numberText(selected.fraction * 100) + '%. ' + (s.percent === 0 ? 'Selection cannot create the absent resistant lineage here.' : 'A rising fraction does not necessarily mean the total population grows.'),
          note: 'Hypothetical lineage-abundance indices start at total 100, not literal fractional microbes. Each round multiplies resistant/susceptible abundance by 1.2/0.25 under exposure, or 1.8/2 without it. These invented factors illustrate selection and an assumed resistance cost, not any particular drug or pathogen. No mutation, horizontal transfer, density limit or immune response is included. This is not a treatment, dose or survival prediction.',
          legend: [{ label: 'Plum: resistant fraction', color: colors.plum }, { label: 'Gold: selected round', color: colors.gold }],
          sources: [{ label: 'OpenStax: selection and drug resistance', url: 'https://openstax.org/books/microbiology/pages/14-5-drug-resistance' }] };
      },
    },
    'bio.5.immunology': {
      title: 'Affinity and abundance jointly determine occupancy',
      instructions: 'Let two monovalent antibody fragments compete for the same epitope. Change free concentrations and A’s dissociation constant.',
      initial: { a: 8, b: 8, kd: 4 },
      controls: [{ key: 'a', label: 'Free fragment A concentration (model units)', min: 0, max: 20, step: 1 },
        { key: 'b', label: 'Free fragment B concentration (model units)', min: 0, max: 20, step: 1 },
        { key: 'kd', label: 'A dissociation constant Kd (lower = tighter)', min: 1, max: 10, step: 1 }],
      calculate(s) {
        const a = s.a / s.kd, b = s.b / 5, z = 1 + a + b, fractions = [a / z, b / z, 1 / z];
        return { data: { fractions },
          readout: 'A-bound: ' + numberText(fractions[0] * 100) + '%. B-bound: ' + numberText(fractions[1] * 100) + '%. Unoccupied: ' + numberText(fractions[2] * 100) + '%. B has fixed Kd=5; the three fractions sum to 100%.',
          note: 'Equilibrium mass-action competition at one mutually exclusive site, with weights A/KdA, B/KdB and 1 for an empty site. Free concentrations are held fixed; all quantities use illustrative units. Lower Kd means stronger intrinsic affinity. No ligand depletion, bivalent avidity, multiple epitopes or immune effector mechanisms are included. Occupancy is not a measure of protection or a clinical outcome. Antibodies targeting different epitopes need not compete this way.',
          legend: [{ label: 'Teal: A-bound', color: colors.teal }, { label: 'Plum: B-bound', color: colors.plum }, { label: 'Paper: unoccupied', color: colors.ink }],
          sources: [{ label: 'NCBI Bookshelf: antibody affinity and avidity', url: 'https://www.ncbi.nlm.nih.gov/books/NBK26884/' }] };
      },
    },
    'bio.5.frontier': {
      title: 'Choose an experiment where predictions separate',
      instructions: 'Two invented mechanisms agree at baseline. Change the tested input and uncertainty band to see whether one observation distinguishes them.',
      initial: { input: 3, tolerance: .2, mechanism: 'saturating', intervention: true },
      controls: [{ key: 'input', label: 'Proposed test input', min: 0, max: 5, step: .25 },
        { key: 'tolerance', label: 'Observation half-width (bounded error)', min: 0, max: 1, step: .1 },
        { key: 'mechanism', label: 'Generate toy observation using', options: [{ value: 'saturating', label: 'Saturating hypothesis' }, { value: 'linear', label: 'Linear hypothesis' }] },
        { key: 'intervention', label: 'Test proposed input instead of baseline 1', type: 'toggle' }],
      calculate(s) {
        const x = s.intervention ? s.input : 1, predictions = [2 * x, 4 * x / (1 + x)], observed = predictions[s.mechanism === 'linear' ? 0 : 1];
        const low = Math.max(0, observed - s.tolerance), high = observed + s.tolerance, compatible = predictions.map(v => v >= low - 1e-12 && v <= high + 1e-12);
        return { data: { x, predictions, observed, low, high, compatible },
          readout: 'Tested input ' + x + ': linear predicts ' + numberText(predictions[0]) + ', saturating predicts ' + numberText(predictions[1]) + '. Toy observation band [' + numberText(low) + ', ' + numberText(high) + ']. Compatible hypotheses: ' + compatible.map((yes, i) => yes ? ['linear', 'saturating'][i] : '').filter(Boolean).join(' and ') + '. ' + (!s.intervention ? 'Proposed input ' + s.input + ' is not being tested yet.' : ''),
          note: 'Invented hypotheses y=2x and y=4x/(1+x), not measurements or a model of a specific organism. The selected hypothesis generates an exact centre with an adjustable bounded-error band, not a confidence interval or likelihood. Both agree at x=0 and x=1: more precision there cannot distinguish them. Excluding one of these two hypotheses does not prove the other uniquely true; other mechanisms may fit. This illustrates discriminating experiment design, not a full identifiability analysis.',
          legend: [{ label: 'Teal: linear prediction', color: colors.teal }, { label: 'Plum: saturating prediction', color: colors.plum }, { label: 'Gold: toy observation band', color: colors.gold }],
          sources: [{ label: 'Raue et al.: identifiability and experimental information', url: 'https://pubmed.ncbi.nlm.nih.gov/19505944/' }] };
      },
    },
    'bio.4.neuro': {
      title: 'Leak, threshold and reset shape a spike train',
      instructions: 'Change constant drive, membrane time constant and refractory duration. Compare subthreshold charging with repeated firing.',
      initial: { drive: 1.5, tau: 20, refractory: 5 },
      controls: [{ key: 'drive', label: 'Constant drive (normalised)', min: 0, max: 3, step: .1 },
        { key: 'tau', label: 'Membrane time constant (ms)', min: 5, max: 30, step: 1 },
        { key: 'refractory', label: 'Refractory duration (ms)', min: 0, max: 10, step: 1 }],
      calculate(s) {
        const rise = s.drive > 1 ? s.tau * Math.log(s.drive / (s.drive - 1)) : null, period = rise === null ? null : rise + s.refractory;
        const spikes = []; if (rise !== null) for (let t = rise; t <= 100; t += period) spikes.push(t);
        const voltage = t => { if (rise === null) return s.drive * (1 - Math.exp(-t / s.tau));
          const phase = t % period; return phase < rise ? s.drive * (1 - Math.exp(-phase / s.tau)) : 0; };
        const points = Array.from({ length: 201 }, (_, i) => [i / 2, voltage(i / 2)]);
        spikes.forEach(t => points.push([t, 1], [t, 0])); points.sort((a, b) => a[0] - b[0]);
        return { data: { rise, period, spikes, points, frequency: period === null ? 0 : 1000 / period },
          readout: spikes.length + ' spikes in the displayed 100 ms. ' + (rise === null ? 'Drive at or below 1 cannot cross the threshold from rest in this model.' :
            'First threshold crossing: ' + numberText(rise) + ' ms. Long-run firing rate: ' + numberText(1000 / period) + ' spikes/s.'),
          note: 'Leaky integrate-and-fire model: τ dv/dt = drive − v, rest/reset 0 and threshold 1. Voltage is normalised, not millivolts. After crossing, voltage resets and is held at zero for the chosen refractory duration. Spikes are events, not a simulated sodium/potassium waveform. No adaptation, synapses or noise is included. The long-run rate is not the displayed-window spike count divided by 0.1 seconds.',
          legend: [{ label: 'Teal: subthreshold voltage and reset', color: colors.teal }, { label: 'Gold: threshold and spike events', color: colors.gold }],
          sources: [{ label: 'EPFL: integrate-and-fire models', url: 'https://neuronaldynamics.epfl.ch/online/Ch1.S3.html' }] };
      },
    },
    'bio.4.physiology': {
      title: 'Binding tightly is not the same as unloading well',
      instructions: 'Adjust affinity and cooperativity, then compare binding at high and low oxygen pressures. Inspect any point on the curve.',
      initial: { pressure: 26, p50: 26, cooperativity: 28 },
      controls: [{ key: 'pressure', label: 'Inspect oxygen pressure (model units)', min: 0, max: 100, step: 1 },
        { key: 'p50', label: 'Half-saturation pressure P50', min: 10, max: 50, step: 1 },
        { key: 'cooperativity', label: 'Hill coefficient × 10', min: 10, max: 40, step: 1 }],
      calculate(s) {
        const n = s.cooperativity / 10, saturation = p => p ** n / (s.p50 ** n + p ** n), high = saturation(80), low = saturation(20);
        return { data: { n, selected: saturation(s.pressure), high, low, difference: high - low, curve: Array.from({ length: 101 }, (_, p) => saturation(p)) },
          readout: 'At pressure ' + s.pressure + ': ' + numberText(saturation(s.pressure) * 100) + '% binding. At reference pressures 80 and 20: ' + numberText(high * 100) + '% and ' + numberText(low * 100) + '%, a difference of ' + numberText((high - low) * 100) + ' percentage points. P50 always gives half saturation.',
          note: 'Hill approximation θ = pⁿ/(P50ⁿ+pⁿ), inspired by cooperative oxygen binding to haemoglobin. Pressures and reference points are illustrative model units, not patient measurements or clinical thresholds. Lower P50 means higher affinity. n=1 gives a noncooperative curve; n>1 introduces a sigmoidal response. The difference between two equilibrium saturations is not total oxygen delivery, which also depends on haemoglobin concentration, flow and other factors. pH, temperature, carbon dioxide and kinetics are omitted.',
          legend: [{ label: 'Teal: binding fraction', color: colors.teal }, { label: 'Gold: inspected pressure', color: colors.gold }, { label: 'Plum markers: reference pressures 20 and 80', color: colors.plum }],
          sources: [{ label: 'OpenStax: cooperative oxygen transport', url: 'https://openstax.org/books/biology-2e/pages/39-4-transport-of-gases-in-human-bodily-fluids' }] };
      },
    },
    'bio.4.ethology': {
      title: 'Travel time changes when a forager should leave',
      instructions: 'Set travel time and patch depletion, then choose a residence time. Compare its average gain with the model’s best departure time.',
      initial: { travel: 5, depletion: 5, residence: 8 },
      controls: [{ key: 'travel', label: 'Travel time between patches', min: 1, max: 20, step: 1 },
        { key: 'depletion', label: 'Patch gain time constant', min: 2, max: 10, step: 1 },
        { key: 'residence', label: 'Inspect residence time', min: 0, max: 40, step: 1 }],
      calculate(s) {
        const gain = t => 100 * (1 - Math.exp(-t / s.depletion)), marginal = t => 100 / s.depletion * Math.exp(-t / s.depletion), rate = t => gain(t) / (t + s.travel);
        let lo = 0, hi = 100;
        for (let i = 0; i < 60; i++) { const mid = (lo + hi) / 2; if (marginal(mid) * (mid + s.travel) > gain(mid)) lo = mid; else hi = mid; }
        const optimum = (lo + hi) / 2, best = rate(optimum);
        return { data: { optimum, best, selected: rate(s.residence), marginal: marginal(s.residence), curve: Array.from({ length: 81 }, (_, i) => rate(i / 2)) },
          readout: 'At residence ' + s.residence + ': average gain ' + numberText(rate(s.residence)) + ' per total time unit, marginal gain ' + numberText(marginal(s.residence)) + ' per patch-time unit. Model optimum: leave at ' + numberText(optimum) + ', where marginal and average gains agree (' + numberText(best) + ').',
          note: 'Marginal-value model with identical renewed patches, gain G(t)=100(1−exp(−t/τ)) and average gain G(t)/(travel+t). Travel yields no food; there is no predation, energy cost, uncertainty or competition. Units are illustrative. This is an optimality prediction under explicit assumptions, not a claim that animals calculate derivatives or always maximise this one objective. Longer travel makes staying longer worthwhile in this model.',
          legend: [{ label: 'Teal: average gain including travel', color: colors.teal }, { label: 'Plum: optimal departure', color: colors.plum }, { label: 'Gold: selected residence time', color: colors.gold }],
          sources: [{ label: 'Charnov: the marginal value theorem', url: 'https://pubmed.ncbi.nlm.nih.gov/1273796/' }] };
      },
    },
    'bio.4.genomics': {
      title: 'Read support is evidence, not a genotype by itself',
      instructions: 'Change the read depth and alternate-base support at one site. Include or exclude the flagged low-quality read and compare the usable evidence.',
      initial: { depth: 6, alternate: 3, filter: true },
      controls: [{ key: 'depth', label: 'Reads covering this site', min: 1, max: 8, step: 1 },
        { key: 'alternate', label: 'Requested alternate-supporting reads', min: 0, max: 8, step: 1 },
        { key: 'filter', label: 'Exclude flagged low-quality read', type: 'toggle' }],
      calculate(s) {
        const alt = Math.min(s.alternate, s.depth), reads = Array.from({ length: s.depth }, (_, i) => ({
          sequence: i < alt ? 'ACGCACGT' : 'ACGTACGT', alternate: i < alt, flagged: i === s.depth - 1, included: !(s.filter && i === s.depth - 1),
        }));
        const usable = reads.filter(r => r.included), support = usable.filter(r => r.alternate).length, fraction = usable.length ? support / usable.length : null;
        return { data: { reads, alt, usable: usable.length, support, fraction },
          readout: usable.length ? support + ' of ' + usable.length + ' usable reads support C at position 4: ' + numberText(fraction * 100) + '% read fraction. ' +
            (s.alternate > s.depth ? 'Requested support is capped at the available depth. ' : '') + 'This does not by itself establish a genotype or biological allele frequency.' : 'No usable reads remain after filtering. The fraction is undefined; there is no basis for a call.',
          note: 'A tiny pre-aligned pileup with one deliberately flagged last read. All other bases are identical and strand/mapping effects are omitted. Real callers use base and mapping qualities, duplicates, local sequence context and genotype likelihoods. Removing a read can raise or lower the observed fraction depending on which base it carries. Small-sample fractions are not certainty, and no clinical interpretation or variant call is made here.',
          legend: [{ label: 'Gold: alternate base C at site 4', color: colors.gold }, { label: 'Faded last row: excluded low-quality read', color: colors.ink }],
          sources: [{ label: 'GATK: coverage and quality-filtered depth', url: 'https://gatk.broadinstitute.org/hc/en-us/articles/360037593971-Coverage' }] };
      },
    },
    'bio.5.comp-bio': {
      title: 'An optimal alignment depends on its cost model',
      instructions: 'Compare short DNA sequences. Change mismatch and gap costs, then inspect the minimum-cost matrix and one optimal traceback.',
      initial: { sequence: 'ACTTAC', mismatch: 2, gap: 1 },
      controls: [{ key: 'sequence', label: 'Comparison sequence', options: ['ACGTAC', 'ACTTAC', 'ACGTTAC', 'ACGAC', 'AGCTAC', 'AAAAAA'].map(value => ({ value, label: value })) },
        { key: 'mismatch', label: 'Mismatch cost', min: 1, max: 5, step: 1 }, { key: 'gap', label: 'Cost per gap character', min: 1, max: 3, step: 1 }],
      calculate(s) {
        const reference = 'ACGTAC', target = s.sequence, m = reference.length, n = target.length;
        const matrix = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0)), ways = Array.from({ length: m + 1 }, () => Array(n + 1).fill(1));
        for (let i = 0; i <= m; i++) matrix[i][0] = i * s.gap;
        for (let j = 0; j <= n; j++) matrix[0][j] = j * s.gap;
        for (let i = 1; i <= m; i++) for (let j = 1; j <= n; j++) {
          const costs = [matrix[i - 1][j - 1] + (reference[i - 1] === target[j - 1] ? 0 : s.mismatch), matrix[i - 1][j] + s.gap, matrix[i][j - 1] + s.gap];
          matrix[i][j] = Math.min(...costs);
          ways[i][j] = costs.reduce((sum, cost, k) => sum + (cost === matrix[i][j] ? [ways[i - 1][j - 1], ways[i - 1][j], ways[i][j - 1]][k] : 0), 0);
        }
        let i = m, j = n, first = '', second = ''; const path = [[i, j]];
        while (i || j) {
          if (i && j && matrix[i][j] === matrix[i - 1][j - 1] + (reference[i - 1] === target[j - 1] ? 0 : s.mismatch)) { first = reference[--i] + first; second = target[--j] + second; }
          else if (i && matrix[i][j] === matrix[i - 1][j] + s.gap) { first = reference[--i] + first; second = '-' + second; }
          else { first = '-' + first; second = target[--j] + second; }
          path.push([i, j]);
        }
        return { data: { reference, target, matrix, path, first, second, cost: matrix[m][n], ways: ways[m][n] },
          readout: 'Minimum total cost ' + matrix[m][n] + '; ' + ways[m][n] + ' optimal traceback path' + (ways[m][n] === 1 ? '' : 's') + '. One alignment: ' + first + ' / ' + second + '.',
          note: 'Global alignment by dynamic programming with match cost zero, a positive mismatch cost and a linear per-character gap cost. The top/left border pays for leading gaps; all characters are aligned. Ties prefer a diagonal step, then a gap in the comparison, then a gap in the reference. A minimum-cost alignment is conditional on these costs, not proof of evolutionary history, homology or variant correctness. Real analyses may use substitution models, affine gaps and longer sequences.',
          legend: [{ label: 'Gold cells: one optimal traceback', color: colors.gold }, { label: 'Numbers: minimum cost for each prefix pair', color: colors.ink }],
          sources: [{ label: 'EMBL-EBI: pairwise sequence alignment', url: 'https://www.ebi.ac.uk/training/online/courses/guide-to-sequence-analysis-tools/sequence-alignment/pairwise-sequence-alignment/' }] };
      },
    },
    'bio.5.systems-bio': {
      title: 'A product can repress its own production',
      instructions: 'Compare protein accumulation with and without negative autoregulation. Change production, removal and the feedback threshold.',
      initial: { production: 6, removal: 50, threshold: 4, feedback: true },
      controls: [{ key: 'production', label: 'Maximum production α', min: 0, max: 10, step: 1 },
        { key: 'removal', label: 'Removal rate γ × 100', min: 10, max: 100, step: 10 },
        { key: 'threshold', label: 'Feedback threshold K', min: 1, max: 10, step: 1 },
        { key: 'feedback', label: 'Negative feedback active', type: 'toggle' }],
      calculate(s) {
        const gamma = s.removal / 100, openLimit = s.production / gamma;
        const derivative = x => s.production / (s.feedback ? 1 + (x / s.threshold) ** 2 : 1) - gamma * x;
        let lo = 0, hi = openLimit;
        for (let i = 0; i < 60; i++) { const mid = (lo + hi) / 2; if (derivative(mid) > 0) lo = mid; else hi = mid; }
        const equilibrium = (lo + hi) / 2, values = [0], open = [0]; let x = 0; const h = .02;
        for (let i = 1; i <= 500; i++) {
          const a = derivative(x), b = derivative(x + h * a / 2), c = derivative(x + h * b / 2), e = derivative(x + h * c);
          x += h * (a + 2 * b + 2 * c + e) / 6;
          if (i % 5 === 0) { values.push(x); open.push(openLimit * (1 - Math.exp(-gamma * i * h))); }
        }
        return { data: { gamma, openLimit, equilibrium, values, open, final: x },
          readout: 'At time 10: protein ' + numberText(x) + '. Selected steady state ' + numberText(equilibrium) + '; without feedback ' + numberText(openLimit) + '. ' +
            (s.feedback ? 'Product represses further synthesis in this model.' : 'Production stays constant; removal balances it at steady state.'),
          note: 'Dimensionless one-variable model: dx/dt = α/(1+(x/K)²) − γx when feedback is on, otherwise α − γx. Both start at zero with the same α and γ. This isolates negative autoregulation; it is not a fit to experimental data, a construction protocol or a claim about response-time improvement at matched outputs. No transcription delay, mRNA, cell division or molecular noise is represented. The dashed trajectory uses no feedback; the long-term steady state need not be reached by time 10.',
          legend: [{ label: 'Teal: selected circuit', color: colors.teal }, { label: 'Dashed coral: no-feedback reference', color: colors.coral }],
          sources: [{ label: 'Rosenfeld, Elowitz and Alon: negative autoregulation', url: 'https://pubmed.ncbi.nlm.nih.gov/12417193/' }] };
      },
    },
    'bio.3.ecology': {
      title: 'Growth changes as a population approaches capacity',
      instructions: 'Change the starting population, carrying capacity and growth rate. Compare starts below, at and above capacity.',
      initial: { initial: 5, capacity: 50, rate: 30 },
      controls: [{ key: 'initial', label: 'Initial population (model units)', min: 0, max: 100, step: 1 },
        { key: 'capacity', label: 'Carrying capacity K', min: 10, max: 100, step: 10 },
        { key: 'rate', label: 'Intrinsic growth rate × 100', min: 0, max: 100, step: 5 }],
      calculate(s) {
        const r = s.rate / 100, at = t => s.initial === 0 ? 0 : s.capacity / (1 + (s.capacity / s.initial - 1) * Math.exp(-r * t));
        const values = Array.from({ length: 81 }, (_, i) => at(i / 4));
        return { data: { r, values, final: values[80], initialSlope: r * s.initial * (1 - s.initial / s.capacity) },
          readout: 'At time 20: population ' + numberText(values[80]) + '; capacity ' + s.capacity + '. ' +
            (!s.initial ? 'With no population or immigration, there is no growth.' : !r ? 'A zero growth parameter keeps the population unchanged.' : s.initial === s.capacity ? 'Starting at capacity gives an equilibrium.' : s.initial < s.capacity ? 'Growth slows as density approaches capacity.' : 'Starting above capacity produces a decline toward capacity.'),
          note: 'Continuous logistic model dN/dt = rN(1−N/K), with constant K and r and no immigration, delays, random events or age structure. Fractional values are a continuous approximation, not fractions of individual animals. Time and population units are illustrative. Capacity is not an immutable property of a real habitat. This equation approaches K without overshooting; real populations can overshoot or fluctuate.',
          legend: [{ label: 'Teal: model population', color: colors.teal }, { label: 'Gold dashed line: carrying capacity', color: colors.gold }],
          sources: [{ label: 'OpenStax: environmental limits to growth', url: 'https://openstax.org/books/biology-2e/pages/45-3-environmental-limits-to-population-growth' }] };
      },
    },
    'bio.3.botany': {
      title: 'Opening a stoma trades gas access for water loss',
      instructions: 'Set pore opening and outside humidity. Compare carbon-dioxide entry with water-vapour loss under fixed gradients.',
      initial: { opening: 70, humidity: 40 },
      controls: [{ key: 'opening', label: 'Pore opening (%)', min: 0, max: 100, step: 1 },
        { key: 'humidity', label: 'Outside relative humidity (%)', min: 0, max: 100, step: 1 }],
      calculate(s) {
        const conductance = s.opening / 100, deficit = 1 - s.humidity / 100;
        return { data: { conductance, deficit, carbon: conductance, water: conductance * deficit },
          readout: 'Relative CO₂ entry: ' + numberText(conductance * 100) + '% of the reference maximum. Relative water-vapour loss: ' + numberText(conductance * deficit * 100) + '%. ' +
            (!s.opening ? 'The model pore is closed, restricting both fluxes.' : s.humidity === 100 ? 'With equal temperatures and saturated outside air, this model has no water-vapour gradient.' : 'Opening admits gas but also provides a route for water loss.'),
          note: 'A qualitative conductance model, not measured photosynthesis or transpiration rates. Conductance is assumed proportional to opening. CO₂ gradient is held fixed; the leaf interior is saturated with water vapour, and leaf and air temperatures are equal. Humidity changes the water gradient only. Ignore cuticular loss, boundary layers and active feedback. Real guard cells respond to light, water status and CO₂; the controls prescribe opening rather than predict their response. Each flux is normalised to its own reference, so equal bars do not mean equal molar rates.',
          legend: [{ label: 'Blue: relative CO₂ entry', color: colors.blue }, { label: 'Coral: relative water loss', color: colors.coral }],
          sources: [{ label: 'OpenStax: stomata and transpiration', url: 'https://openstax.org/books/biology-2e/pages/30-5-transport-of-water-and-solutes-in-plants' }] };
      },
    },
    'bio.4.biochem': {
      title: 'More substrate eventually meets an enzyme limit',
      instructions: 'Change substrate concentration, Km and Vmax. Locate the half-maximal rate and compare it with the selected substrate concentration.',
      initial: { substrate: 20, km: 20, vmax: 80 },
      controls: [{ key: 'substrate', label: 'Substrate [S] (model units)', min: 0, max: 100, step: 1 },
        { key: 'km', label: 'Km (same concentration units)', min: 1, max: 50, step: 1 },
        { key: 'vmax', label: 'Vmax (rate units)', min: 10, max: 100, step: 10 }],
      calculate(s) {
        const velocity = s.vmax * s.substrate / (s.km + s.substrate), fraction = s.substrate / (s.km + s.substrate);
        return { data: { velocity, fraction, curve: Array.from({ length: 101 }, (_, x) => s.vmax * x / (s.km + x)) },
          readout: 'v = Vmax[S]/(Km+[S]) = ' + numberText(velocity) + ' rate units (' + numberText(fraction * 100) + '% of Vmax). At [S] = Km = ' + s.km + ', v = ' + s.vmax / 2 + '. ' +
            (!s.substrate ? 'Without substrate, the model rate is zero.' : s.substrate === s.km ? 'The selected point is exactly half-maximal.' : 'Increasing substrate approaches Vmax but does not reach it at a finite concentration in this model.'),
          note: 'Single-substrate Michaelis–Menten initial-rate model under steady-state assumptions, fixed enzyme amount and conditions, negligible product and no cooperativity or inhibition. Units are illustrative, not clinical values. Km is the half-maximal substrate concentration here; it is not generally a direct binding-affinity constant. Vmax depends on enzyme amount and catalytic turnover. This graph shows initial rate versus substrate, not substrate consumption over time or a change in reaction equilibrium.',
          legend: [{ label: 'Teal: initial-rate curve', color: colors.teal }, { label: 'Gold point: chosen substrate; dashed line: Vmax', color: colors.gold }, { label: 'Plum: half-maximal point', color: colors.plum }],
          sources: [{ label: 'NCBI Assay Guidance Manual: enzyme kinetics', url: 'https://www.ncbi.nlm.nih.gov/books/NBK92007/' }] };
      },
    },
    'bio.3.evolution': {
      title: 'Selection changes a population, not an individual',
      instructions: 'Choose the starting frequency and which inherited variant leaves more offspring. Follow the population over generations.',
      initial: { percent: 50, environment: 'a', generation: 6 },
      controls: [{ key: 'percent', label: 'Starting variant A (%)', min: 0, max: 100, step: 1 },
        { key: 'environment', label: 'Reproductive advantage', options: [{ value: 'a', label: 'Variant A favoured' }, { value: 'b', label: 'Variant B favoured' }, { value: 'equal', label: 'Neither favoured' }] },
        { key: 'generation', label: 'Inspect generation', min: 0, max: 12, step: 1 }],
      calculate(s) {
        const weights = s.environment === 'a' ? [2, 1] : s.environment === 'b' ? [1, 2] : [1, 1], history = [s.percent / 100];
        for (let i = 0; i < 12; i++) { const p = history[i]; history.push(p * weights[0] / (p * weights[0] + (1 - p) * weights[1])); }
        const p = history[s.generation];
        return { data: { weights, history, p, q: 1 - p },
          readout: 'Generation ' + s.generation + ': A ' + numberText(p * 100) + '%, B ' + numberText((1 - p) * 100) + '%. Relative reproductive contributions A:B = ' + weights.join(':') + '. ' +
            (s.percent === 0 || s.percent === 100 ? 'Selection alone cannot introduce an absent variant.' : s.environment === 'equal' ? 'Equal contributions preserve the starting frequencies here.' : 'The favoured inherited variant becomes more common over generations.'),
          note: 'A deterministic two-variant haploid or clonally inherited model: p next = p wA / (p wA + (1−p) wB). The 2:1 contribution ratio is chosen for illustration, not measured field data. There is no mutation, migration, drift, dominance or changing environment. These are frequencies, not population size or survival probabilities. Individuals do not transform into the favoured variant. Rounded display values near 0% or 100% do not prove exact loss or fixation.',
          legend: [{ label: 'Blue: variant A frequency', color: colors.blue }, { label: 'Coral: variant B frequency', color: colors.coral }, { label: 'Gold: inspected generation', color: colors.gold }],
          sources: [{ label: 'OpenStax: selection and population genetics', url: 'https://openstax.org/books/biology-2e/pages/19-2-population-genetics' }] };
      },
    },
    'bio.4.evo-bio': {
      title: 'Genotype frequencies can change while alleles do not',
      instructions: 'Set allele A’s frequency, then increase the inbreeding coefficient. Compare genotype proportions with their Hardy–Weinberg baseline.',
      initial: { percent: 50, inbreeding: 0 },
      controls: [{ key: 'percent', label: 'Allele A frequency (%)', min: 0, max: 100, step: 1 },
        { key: 'inbreeding', label: 'Inbreeding coefficient F (%)', min: 0, max: 100, step: 1 }],
      calculate(s) {
        const p = s.percent / 100, q = 1 - p, f = s.inbreeding / 100, baseline = [p * p, 2 * p * q, q * q];
        const genotype = [baseline[0] + f * p * q, baseline[1] * (1 - f), baseline[2] + f * p * q];
        return { data: { p, q, f, baseline, genotype, recovered: genotype[0] + genotype[1] / 2 },
          readout: 'AA ' + numberText(genotype[0] * 100) + '%, Aa ' + numberText(genotype[1] * 100) + '%, aa ' + numberText(genotype[2] * 100) + '%. Counting A copies gives AA + ½Aa = ' + s.percent + '%. ' +
            (f === 0 ? 'At F = 0, the genotype frequencies are p², 2pq and q².' : 'Heterozygosity is reduced or remains zero, while the allele frequency stays fixed.'),
          note: 'A single biallelic diploid locus: AA = p² + Fpq, Aa = 2pq(1−F), aa = q² + Fpq. F parameterises identity by descent relative to a reference population; it is not a percentage of related people or a health-risk estimate. Allele frequencies are held fixed to isolate genotype redistribution. Real populations may also experience selection, drift, mutation and migration. Neither letter implies dominance, harmfulness or superiority. Hardy–Weinberg is a null model, not a claim that every population satisfies its assumptions.',
          legend: [{ label: 'Dashed outlines: F = 0 baseline', color: colors.ink }, { label: 'Filled bars: selected F', color: colors.teal }],
          sources: [{ label: 'OpenStax: Hardy–Weinberg model', url: 'https://openstax.org/books/biology-2e/pages/19-1-population-evolution' },
            { label: 'Identity by descent and genotype frequencies', url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC2483716/' }] };
      },
    },
    'bio.1.human-body': {
      title: 'One blood circuit, two heart pumps',
      instructions: 'Follow a small portion of blood around the circuit. Notice where oxygen is picked up and where it is delivered.',
      initial: { step: 1, oxygen: true },
      controls: [{ key: 'step', label: 'Journey step', min: 0, max: 7, step: 1 }, { key: 'oxygen', label: 'Show relative oxygen levels', type: 'toggle' }],
      calculate(s) {
        const route = ['Right heart', 'Lungs', 'Left heart', 'Body tissues'], at = s.step % 4;
        const actions = ['Pumps blood toward the lungs.', 'Blood gains oxygen and releases carbon dioxide.', 'Pumps blood toward the body.', 'Blood delivers oxygen to body tissues.'];
        const rich = at === 1 || at === 2;
        return { data: { route, at, rich, lap: Math.floor(s.step / 4), name: route[at] },
          readout: 'Step ' + s.step + ': ' + route[at] + '. ' + actions[at] + (s.oxygen ? ' Blood leaving here has relatively ' + (rich ? 'more' : 'less') + ' oxygen.' : 'Oxygen labels are hidden; follow the directed circuit.'),
          note: 'A simplified human circulation map, not anatomical positions or a timing model. Each heart side includes an atrium and ventricle. Lower-oxygen blood is not oxygen-free and is not blue: both blood streams are red in reality. The lungs exchange gases; the heart pumps blood. Valves, coronary circulation and individual vessels are omitted. The pointer tracks one portion; the real circuit flows continuously.',
          legend: [{ label: 'Gold: tracked portion of blood', color: colors.gold }, { label: 'Arrows: direction of circulation', color: colors.teal }],
          sources: [{ label: 'OpenStax: circulation and respiration', url: 'https://openstax.org/books/concepts-biology/pages/16-3-circulatory-and-respiratory-systems' }] };
      },
    },
    'bio.2.digestion': {
      title: 'Trace materials through cooperating organs',
      instructions: 'Choose a material, then follow its route. Compare a nutrient with carbon dioxide, urea and unabsorbed residue.',
      initial: { material: 'glucose', step: 3 },
      controls: [{ key: 'material', label: 'Material to trace', options: [{ value: 'glucose', label: 'Absorbed glucose' }, { value: 'co2', label: 'Carbon dioxide' }, { value: 'urea', label: 'Urea' }, { value: 'residue', label: 'Unabsorbed residue' }] },
        { key: 'step', label: 'Route step', min: 0, max: 3, step: 1 }],
      calculate(s) {
        const paths = {
          glucose: { name: 'Glucose', nodes: ['Small intestine', 'Portal blood', 'Liver', 'Body tissues'], verbs: ['Absorb across the lining', 'Carry to the liver', 'Distribute via blood'], message: 'A nutrient can enter the blood and be used or stored.' },
          co2: { name: 'Carbon dioxide', nodes: ['Body cells', 'Blood', 'Lungs', 'Exhaled air'], verbs: ['Enter the blood', 'Carry to the lungs', 'Breathe out'], message: 'A waste from cellular metabolism leaves through the lungs.' },
          urea: { name: 'Urea', nodes: ['Liver', 'Blood', 'Kidneys', 'Urine'], verbs: ['Release into blood', 'Carry to the kidneys', 'Excrete in urine'], message: 'The liver makes urea; kidneys remove it from the blood into urine.' },
          residue: { name: 'Unabsorbed residue', nodes: ['Small intestine', 'Colon', 'Rectum', 'Outside the body'], verbs: ['Pass along the gut', 'Move and store faeces', 'Eliminate'], message: 'This material stays in the gut rather than entering the blood.' },
        };
        const path = paths[s.material];
        return { data: { ...path, current: path.nodes[s.step], traversed: path.nodes.slice(0, s.step + 1) },
          readout: path.name + ' at ' + path.nodes[s.step] + '. Traced: ' + path.nodes.slice(0, s.step + 1).join(' → ') + '. ' + path.message,
          note: 'Selected routes, not a full anatomy map or timing simulation. Glucose shown here is already digested; it may be stored or metabolised by the liver rather than immediately reaching other tissues. Urea is produced during nitrogen processing, not from unabsorbed food. Kidney filtration is followed by selective reabsorption and secretion; urine also passes through ureters and bladder. Faeces contain more than food residue. Blood circulation connects organs even where intermediate vessels are omitted.',
          legend: [{ label: 'Gold: selected route position', color: colors.gold }, { label: 'Teal: route already traced', color: colors.teal }],
          sources: [{ label: 'OpenStax: digestion and absorption', url: 'https://openstax.org/books/biology-2e/pages/34-3-digestive-system-processes' },
            { label: 'OpenStax: kidney processing', url: 'https://openstax.org/books/biology-2e/pages/41-2-the-kidneys-and-osmoregulatory-organs' }] };
      },
    },
    'bio.2.reproduction': {
      title: 'Join chromosome sets, then copy for growth',
      instructions: 'Choose a small model chromosome set. Join two gametes, then advance cell divisions and compare chromosomes per cell with the total number of cells.',
      initial: { haploid: 2, divisions: 2 },
      controls: [{ key: 'haploid', label: 'Chromosomes in each gamete', min: 1, max: 3, step: 1 },
        { key: 'divisions', label: 'Rounds of cell division', min: 0, max: 3, step: 1 }],
      calculate(s) {
        const diploid = 2 * s.haploid, cells = 2 ** s.divisions;
        return { data: { diploid, cells, total: diploid * cells },
          readout: 'Two gametes with ' + s.haploid + ' chromosomes each form a zygote with ' + diploid + '. After ' + s.divisions + ' rounds of division: ' + cells + ' cell' + (cells === 1 ? '' : 's') + ', each with ' + diploid + ' chromosomes. Growth adds cells, not extra chromosome sets to each cell.',
          note: 'An idealised diploid organism with a deliberately small chromosome number, not a human chromosome count. Gametes carry one set; fertilisation restores two. DNA must be copied before each mitotic division. Counts refer to daughter cells after division, before their next DNA replication; sticks symbolise chromosomes rather than their visible form in a living nucleus. All cells divide together here, with no death, mutation or differentiation. Actual development does not follow this simple clock.',
          legend: [{ label: 'Blue: one gamete’s chromosome set', color: colors.blue }, { label: 'Coral: the other gamete’s set', color: colors.coral }],
          sources: [{ label: 'OpenStax: sexual reproduction', url: 'https://openstax.org/books/biology-2e/pages/11-2-sexual-reproduction' },
            { label: 'OpenStax: the cell cycle', url: 'https://openstax.org/books/biology-2e/pages/10-2-the-cell-cycle' }] };
      },
    },
    'bio.0.animals': {
      title: 'Different features make different groups',
      instructions: 'Look at four animals. Change the feature used to group them: legs and wings do not give the same groups.',
      initial: { feature: 'six', count: true },
      controls: [{ key: 'feature', label: 'Find animals with', options: [{ value: 'six', label: 'Six legs' }, { value: 'eight', label: 'Eight legs' }, { value: 'wings', label: 'Wings' }, { value: 'none', label: 'No legs' }] },
        { key: 'count', label: 'Show leg counts', type: 'toggle' }],
      calculate(s) {
        const animals = [{ id: 'beetle', name: 'Ladybird beetle', legs: 6, wings: true }, { id: 'spider', name: 'Spider', legs: 8, wings: false },
          { id: 'sparrow', name: 'Sparrow', legs: 2, wings: true }, { id: 'trout', name: 'Trout', legs: 0, wings: false }];
        const matches = animals.filter(a => s.feature === 'wings' ? a.wings : a.legs === { six: 6, eight: 8, none: 0 }[s.feature]).map(a => a.id);
        return { data: { animals, matches }, readout: 'Matching examples: ' + animals.filter(a => matches.includes(a.id)).map(a => a.name).join(', ') + '. ' +
          (s.count ? 'Leg counts: ' + animals.map(a => a.name + ' ' + a.legs).join('; ') + '.' : 'Leg-count labels are hidden: count the drawn legs yourself.'),
          note: 'Four intact adult examples, not a complete animal classification. The ladybird’s flying wings fold beneath its hard wing covers. A bird has two legs and two wings; wings are not extra legs. Grouping by wings puts a bird and an insect together by a shared function, not by close ancestry. Fins are not legs. Shapes are schematic and not to the same scale.',
          legend: [{ label: 'Gold frame: matches the selected feature', color: colors.gold }, { label: 'Teal: leg-count evidence', color: colors.teal }],
          sources: [{ label: 'Smithsonian: what is an insect?', url: 'https://naturalhistory.si.edu/education/teaching-resources/life-science/what-insect' }] };
      },
    },
    'bio.1.habitats': {
      title: 'A habitat needs connected places',
      instructions: 'Explore a wood frog’s woodland and breeding pool. Remove either place or close the connecting route to see which parts of the yearly journey remain.',
      initial: { pool: true, woodland: true, route: true },
      controls: [{ key: 'pool', label: 'Breeding pool has water', type: 'toggle' }, { key: 'woodland', label: 'Woodland refuge present', type: 'toggle' },
        { key: 'route', label: 'Connecting route open', type: 'toggle' }],
      calculate(s) {
        const available = Number(s.pool) + Number(s.woodland), connected = s.pool && s.woodland && s.route;
        const missing = [!s.pool && 'water in the breeding pool', !s.woodland && 'woodland refuge', !s.route && 'an open connecting route'].filter(Boolean);
        return { data: { available, connected, missing }, readout: available + ' of 2 places available. ' +
          (connected ? 'Both places are linked: the seasonal journey is connected in this drawing.' : 'The full seasonal journey is not connected. Missing: ' + missing.join('; ') + '.'),
          note: 'A wood-frog example: adults use woodland and migrate to breeding pools. This is a small habitat-connectivity model, not a survival probability or a forecast for an actual site. The barrier simply closes this model’s route; real roads vary in how permeable and dangerous they are. Water duration, food, water quality, disease, predators and other routes also matter. Other frog species use different habitats. An open route cannot replace a missing destination.',
          legend: [{ label: 'Teal: available places and open route', color: colors.teal }, { label: 'Coral: unavailable or interrupted', color: colors.coral }],
          sources: [{ label: 'National Park Service: vernal pools', url: 'https://www.nps.gov/blri/learn/nature/vernal-pools.htm' }] };
      },
    },
    'bio.0.body': {
      title: 'From a sense organ to a perception',
      instructions: 'Choose something to notice, then follow the three steps from a stimulus to a nerve signal and a perception.',
      initial: { sense: 'sight', step: 2 },
      controls: [{ key: 'sense', label: 'Sense to explore', options: ['sight', 'hearing', 'smell', 'taste', 'touch'].map(value => ({ value, label: value[0].toUpperCase() + value.slice(1) })) },
        { key: 'step', label: 'Follow the signal', min: 0, max: 2, step: 1 }],
      calculate(s) {
        const examples = {
          sight: ['Light', 'Eye', 'See a colour'], hearing: ['Vibration', 'Ear', 'Hear a sound'],
          smell: ['Airborne molecules', 'Nose', 'Notice a smell'], taste: ['Dissolved molecules', 'Tongue', 'Notice a taste'],
          touch: ['Gentle pressure', 'Skin', 'Feel contact'],
        };
        const [stimulus, organ, perception] = examples[s.sense];
        const stages = [stimulus + ' reaches receptors in the ' + organ.toLowerCase() + '.',
          'Receptors respond; nerves carry signals toward the brain.', 'The brain processes the signals: ' + perception.toLowerCase() + '.'];
        return { data: { stimulus, organ, perception, stages, reached: s.step + 1 },
          readout: 'Step ' + (s.step + 1) + ' of 3. ' + stages[s.step],
          note: 'An ordered explanation, not a stopwatch or a medical test. Sensory pathways contain many cells and relays; the drawing does not map particular brain regions. These five familiar senses are not the only ones: balance and body-position senses also matter. Pressure is only one kind of touch stimulus. Perception combines incoming signals with context and experience.',
          legend: [{ label: 'Gold: current step', color: colors.gold }, { label: 'Teal: steps already reached', color: colors.teal }],
          sources: [{ label: 'OpenStax: sensory processes', url: 'https://openstax.org/books/biology-2e/pages/36-1-sensory-processes' }] };
      },
    },
    'bio.0.seasons': {
      title: 'One year, opposite seasonal rhythms',
      instructions: 'Move through the months and switch hemispheres. Watch a temperate deciduous tree repeat its yearly cycle.',
      initial: { month: 9, hemisphere: 'south' },
      controls: [{ key: 'month', label: 'Month of the year', min: 1, max: 12, step: 1 },
        { key: 'hemisphere', label: 'Temperate hemisphere', options: [{ value: 'south', label: 'Southern' }, { value: 'north', label: 'Northern' }] }],
      calculate(s) {
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        const north = Math.floor((s.month % 12) / 3), phase = (north + (s.hemisphere === 'south' ? 2 : 0)) % 4;
        const seasons = ['Winter', 'Spring', 'Summer', 'Autumn'], changes = ['Bare branches; resting buds', 'Buds open; new leaves grow', 'A full green canopy', 'Leaves change and fall'];
        return { data: { phase, season: seasons[phase], month: months[s.month - 1], change: changes[phase], opposite: seasons[(phase + 2) % 4] },
          readout: months[s.month - 1] + ': ' + seasons[phase].toLowerCase() + ' in this ' + s.hemisphere + 'ern temperate example. ' + changes[phase] + '. The other hemisphere has ' + seasons[(phase + 2) % 4].toLowerCase() + '.',
          note: 'A schematic deciduous tree, not a prediction for every tree or place. Month groups use meteorological seasons. Daylight and temperature help time plant changes, but species, rainfall and local climate matter; tropical wet/dry seasons and evergreen trees differ. Earth’s tilted axis produces opposite seasonal sunlight patterns in the hemispheres. The four pictures are teaching stages, not sudden changes on the first day of a month.',
          legend: [{ label: 'Gold: selected month', color: colors.gold }, { label: 'Teal: growing leaves', color: colors.teal }],
          sources: [{ label: 'NOAA: changing seasons', url: 'https://www.nesdis.noaa.gov/our-environment/solar-phenomena/changing-of-the-seasons' }] };
      },
    },
    'bio.0.living': {
      title: 'Look for more than one sign of life',
      instructions: 'Compare a plant, a resting seed, and nonliving things. Look inside to see why movement or growth alone is not enough.',
      initial: { specimen: 'plant', inside: false },
      controls: [{ key: 'specimen', label: 'Look at', options: [{ value: 'plant', label: 'Growing plant' }, { value: 'seed', label: 'Living resting seed' },
        { value: 'flame', label: 'Flame' }, { value: 'robot', label: 'Toy robot' }, { value: 'rock', label: 'Rock' }] },
        { key: 'inside', label: 'Look inside', type: 'toggle' }],
      calculate(s) {
        const specimens = {
          plant: { name: 'Growing plant', alive: true, size: 'Grows', energy: 'Uses light', cells: true },
          seed: { name: 'Living resting seed', alive: true, size: 'Can grow later', energy: 'Very little now', cells: true },
          flame: { name: 'Flame', alive: false, size: 'Can grow', energy: 'Burns fuel', cells: false },
          robot: { name: 'Toy robot', alive: false, size: 'Does not grow', energy: 'Uses a battery', cells: false },
          rock: { name: 'Rock', alive: false, size: 'Can wear away', energy: 'No metabolism', cells: false },
        };
        const specimen = specimens[s.specimen];
        return { data: specimen, readout: specimen.name + ': ' + specimen.size.toLowerCase() + '; ' + specimen.energy.toLowerCase() + '. ' +
          (s.inside ? (specimen.cells ? 'It is made of living cells. It is alive.' : 'It is not made of cells. This example is not alive.') : 'Look inside for another clue. A thing can change or use energy without being alive.'),
          note: 'The seed here is viable and dormant, not dead: life does not require obvious movement or growth at every moment. These are carefully chosen examples, not a one-question test for all cases. Living things have organized cells and linked processes such as metabolism, regulation, growth and reproduction across their life cycles. Dead tissue can still contain cell structures. Viruses need a separate discussion. The close-up is a schematic, not a microscope image or a size comparison.',
          legend: [{ label: 'Teal: organized living cells', color: colors.teal }, { label: 'Gold: inspect the evidence', color: colors.gold }],
          sources: [{ label: 'OpenStax: properties of life', url: 'https://openstax.org/books/biology-2e/pages/1-2-themes-and-concepts-of-biology' }] };
      },
    },
    'bio.2.classification': {
      title: 'Follow branches to a shared ancestor',
      instructions: 'Choose two animals and follow their highlighted branches. Compare a bat with a bird, then a bat with a mouse.',
      initial: { first: 'bat', second: 'pigeon', flight: true },
      controls: ['first', 'second'].map(key => ({ key, label: key === 'first' ? 'First animal' : 'Second animal',
        options: ['salmon', 'frog', 'mouse', 'bat', 'lizard', 'pigeon'].map(value => ({ value, label: value[0].toUpperCase() + value.slice(1) })) }))
        .concat([{ key: 'flight', label: 'Show which examples fly', type: 'toggle' }]),
      calculate(s) {
        const parents = { salmon: 'vertebrates', tetrapods: 'vertebrates', frog: 'tetrapods', amniotes: 'tetrapods',
          mammals: 'amniotes', reptiles: 'amniotes', mouse: 'mammals', bat: 'mammals', lizard: 'reptiles', pigeon: 'reptiles' };
        const path = tip => { const nodes = [tip]; while (parents[nodes[nodes.length - 1]]) nodes.push(parents[nodes[nodes.length - 1]]); return nodes; };
        const firstPath = path(s.first), secondPath = path(s.second), common = firstPath.find(node => secondPath.includes(node));
        const names = { vertebrates: 'Vertebrates', tetrapods: 'Tetrapods', amniotes: 'Amniotes', mammals: 'Mammals', reptiles: 'Reptiles, including birds' };
        const label = names[common] || common[0].toUpperCase() + common.slice(1), same = s.first === s.second;
        return { data: { parents, firstPath, secondPath, common, label, same },
          readout: same ? 'The same animal was selected twice: ' + label + '. Choose another animal to compare branches.' + (s.flight ? ' Flight is shown for bat and pigeon.' : 'Flight labels are hidden.') :
            s.first + ' and ' + s.second + ' meet at the highlighted ancestral branch of ' + label.toLowerCase() + '. ' +
            (s.flight ? 'Bat and pigeon both fly, but bat and mouse share a more recent ancestor. Flight alone does not define their group.' : 'Flight labels are hidden; compare the branching order.'),
          note: 'A pruned tree of six example vertebrates, not all animal diversity. Internal dots represent ancestral lineages, not a claim that a living frog or lizard is another living species’ ancestor. Birds are within the reptile lineage. Branch lengths and screen distances do not represent time or genetic distance. Relationships depend on common ancestry, supported by anatomical and molecular evidence; similar functions can evolve independently. Rotating a branch would not change the relationships.',
          legend: [{ label: 'Teal and blue: selected ancestry paths', color: colors.teal }, { label: 'Gold dot: most recent shared branch', color: colors.gold }],
          sources: [{ label: 'OpenStax: evolutionary relationships', url: 'https://openstax.org/books/biology-2e/pages/20-2-determining-evolutionary-relationships' }] };
      },
    },
    'bio.2.ecosystems': {
      title: 'A food web offers more than one route',
      instructions: 'Remove one member of this small food web. Trace which routes from grass still reach a selected predator.',
      initial: { removed: 'none', target: 'foxes' },
      controls: [{ key: 'removed', label: 'Remove from this example web', options: ['none', 'grass', 'rabbits', 'mice', 'foxes', 'owls'].map(value => ({ value, label: value[0].toUpperCase() + value.slice(1) })) },
        { key: 'target', label: 'Trace food routes to', options: [{ value: 'foxes', label: 'Foxes' }, { value: 'owls', label: 'Owls' }] }],
      calculate(s) {
        const edges = [['grass', 'rabbits'], ['grass', 'mice'], ['rabbits', 'foxes'], ['mice', 'foxes'], ['mice', 'owls']];
        const active = edges.filter(edge => !edge.includes(s.removed)), routes = [];
        const visit = path => { const last = path[path.length - 1]; if (last === s.target) routes.push(path);
          else active.filter(([from]) => from === last).forEach(([, to]) => visit([...path, to])); };
        if (s.removed !== 'grass') visit(['grass']);
        const prey = active.filter(([, to]) => to === s.target).map(([from]) => from);
        return { data: { edges, active, routes, prey },
          readout: (s.removed === 'none' ? 'No member removed. ' : 'Removed ' + s.removed + '. ') + routes.length + ' food route' + (routes.length === 1 ? '' : 's') +
            ' from grass to ' + s.target + ' remain in this drawing. ' + (routes.length ? routes.map(route => route.join(' → ')).join('; ') + '.' : 'No complete route remains.') +
            ' Direct prey links: ' + (prey.join(', ') || 'none') + '.',
          note: 'Arrows run from food to eater. This is a structural dependency model, not a population forecast: a remaining route does not guarantee enough food, and a missing route in this small drawing does not prove immediate extinction. Real food webs contain many more species, decomposers, changing diets, and outside inputs. Foxes here can use either rabbits or mice; owls have only the mouse route in this deliberately reduced example. Removal deletes links without inventing new feeding relationships.',
          legend: [{ label: 'Gold: complete selected food routes', color: colors.gold }, { label: 'Dashed coral: removed links or member', color: colors.coral }],
          sources: [{ label: 'OpenStax: ecosystem food webs', url: 'https://openstax.org/books/biology-2e/pages/46-1-ecology-of-ecosystems' }] };
      },
    },
    'bio.2.microbes': {
      title: 'Yeast makes the gas that raises dough',
      instructions: 'Add glucose packets and active yeast, then advance fermentation. Track the carbon dioxide, ethanol, and unused glucose.',
      initial: { sugar: 4, steps: 2, yeast: true },
      controls: [{ key: 'sugar', label: 'Glucose packets supplied', min: 0, max: 6, step: 1 },
        { key: 'steps', label: 'Reaction steps', min: 0, max: 6, step: 1 },
        { key: 'yeast', label: 'Active yeast present', type: 'toggle' }],
      calculate(s) {
        const consumed = s.yeast ? Math.min(s.sugar, s.steps) : 0, gas = consumed * 2, ethanol = consumed * 2, left = s.sugar - consumed;
        return { data: { consumed, gas, ethanol, left },
          readout: consumed + ' glucose packets used; ' + gas + ' carbon-dioxide packets and ' + ethanol + ' ethanol packets produced. ' + left + ' glucose packets remain. ' +
            (s.yeast ? gas ? 'Trapped gas bubbles can expand dough.' : 'No glucose has fermented yet.' : 'Without active yeast, this isolated mixture does not ferment.'),
          note: 'Baker’s yeast is a single-celled fungus, not a bacterium. Simplified alcoholic fermentation: C₆H₁₂O₆ → 2 C₂H₅OH + 2 CO₂, with energy captured by the cell through glycolysis. A packet represents an equal amount of molecules, not one visible gas bubble. The dough height is schematic, not a volume or timing prediction. Assume suitable moisture and temperature, oxygen-limited conditions, no other microbes, and gas held in the dough. Real microbes and fermentation pathways vary; this is one useful example, not a model of viruses.',
          legend: [{ label: 'Teal: yeast cells', color: colors.teal }, { label: 'Blue circles: gas held in dough', color: colors.blue }],
          sources: [{ label: 'OpenStax: microbial fermentation', url: 'https://openstax.org/books/microbiology/pages/8-4-fermentation' }] };
      },
    },
    'bio.0.plants': {
      title: 'From a seed to a seedling',
      instructions: 'Move through the growth steps. Compare a bean seed with and without water, suitable warmth, and light.',
      initial: { step: 4, water: true, warmth: true, light: true },
      controls: [{ key: 'step', label: 'Growth step', min: 0, max: 4, step: 1 },
        { key: 'water', label: 'Enough water', type: 'toggle' },
        { key: 'warmth', label: 'Suitable warmth', type: 'toggle' },
        { key: 'light', label: 'Light for the seedling', type: 'toggle' }],
      calculate(s) {
        const stage = !s.water ? 0 : !s.warmth ? Math.min(s.step, 1) : s.step;
        const pale = stage >= 3 && !s.light;
        const name = ['Dry seed', 'Seed takes in water', 'First root emerges', 'Shoot emerges', 'Seedling opens its leaves'][stage];
        return { data: { stage, pale, name },
          readout: name + '. ' + (!s.water ? 'Without water, this seed does not begin growing.' : !s.warmth ? 'Water can enter the seed, but conditions here are too cold for further growth.' :
            pale ? 'Stored food lets the shoot start in the dark, but it is pale and cannot keep growing healthily without light.' : stage < 3 ? 'The seed uses stored food to begin growing.' : 'The leaves can use light to make food.'),
          note: 'This is a simplified bean-seed sequence, not a clock or a prediction for every species. Assume a viable seed, oxygen, and moist—not flooded—soil. The unsuitable-temperature setting represents cold enough to prevent further germination, not merely a cool day. Light requirements for germination vary among species; this bean can start below ground. A dark-grown shoot is shown briefly using seed reserves, not as a sustainable adult plant.',
          legend: [{ label: 'Blue: roots below the soil', color: colors.blue }, { label: 'Teal: growing shoot and leaves', color: colors.teal }],
          sources: [{ label: 'University of Minnesota: seed germination', url: 'https://blog-nwcrops.extension.umn.edu/2023/05/its-magic-neat-process-of-soybean.html' }] };
      },
    },
    'bio.1.plants-parts': {
      title: 'Plant parts work together',
      instructions: 'Choose a part to highlight its job, then show the path water follows from the soil to the leaves.',
      initial: { part: 'roots', flow: true },
      controls: [{ key: 'part', label: 'Explore a plant part', options: ['roots', 'stem', 'leaves', 'flower'].map(value => ({ value, label: value[0].toUpperCase() + value.slice(1) })) },
        { key: 'flow', label: 'Show water path', type: 'toggle' }],
      calculate(s) {
        const jobs = { roots: 'Roots anchor the plant and absorb water and dissolved minerals from the soil.',
          stem: 'The stem supports the leaves and flowers. Inside it, tubes carry water, minerals, and sugars.',
          leaves: 'Leaves capture light to make sugars from carbon dioxide and water. Tiny openings exchange gases.',
          flower: 'A flower contains reproductive structures. After pollination and fertilization, ovules can develop into seeds.' };
        return { data: { job: jobs[s.part] }, readout: jobs[s.part] + (s.flow ? ' Blue arrows trace water: soil → roots → stem → leaves.' : 'Water-path arrows are hidden; select a part to examine its shape.'),
          note: 'A schematic flowering plant, not a scale drawing of a particular species. Water travels mainly upward in xylem; sugars move through phloem from sources to sinks and are not represented by the blue arrows. Roots take up minerals, but plants do not obtain their sugars by eating soil. Not every plant has flowers, and not every flower produces a seed.',
          legend: [{ label: 'Gold: selected part', color: colors.gold }, { label: 'Blue arrows: water path', color: colors.blue }],
          sources: [{ label: 'Oregon State: plant parts', url: 'https://extension.oregonstate.edu/collection/botany-basics' }] };
      },
    },
    'bio.2.photosynthesis': {
      title: 'Account for the materials in photosynthesis',
      instructions: 'Supply carbon dioxide, water, and light. Count whole batches of the simplified net reaction and track unused materials.',
      initial: { carbon: 12, water: 12, light: true },
      controls: [{ key: 'carbon', label: 'Carbon dioxide molecules supplied', min: 0, max: 18, step: 1 },
        { key: 'water', label: 'Water molecules supplied', min: 0, max: 18, step: 1 },
        { key: 'light', label: 'Light energy available', type: 'toggle' }],
      calculate(s) {
        const sugar = s.light ? Math.floor(Math.min(s.carbon, s.water) / 6) : 0, oxygen = 6 * sugar;
        const carbonLeft = s.carbon - 6 * sugar, waterLeft = s.water - 6 * sugar;
        return { data: { sugar, oxygen, carbonLeft, waterLeft, atoms: { C: s.carbon, H: s.water * 2, O: s.carbon * 2 + s.water } },
          readout: sugar + ' glucose-equivalent molecules and ' + oxygen + ' oxygen molecules. Unused: ' + carbonLeft + ' CO₂ and ' + waterLeft + ' H₂O. ' +
            (!s.light ? 'No light energy is supplied in this model.' : sugar === 0 ? 'Not enough material for one whole net-reaction batch.' : 'Each batch uses 6 CO₂ and net 6 H₂O.'),
          note: 'Net bookkeeping: 6 CO₂ + 6 H₂O + light energy → C₆H₁₂O₆ + 6 O₂. This combines many reactions; it is not a direct collision of twelve molecules or a prediction of plant growth. The immediate carbohydrate product is G3P, used to build sugars. The oxygen gas comes from water splitting; the net equation alone does not track oxygen-atom origins. Whole batches and leftover molecules are a counting exercise. Real rates also depend on enzymes, temperature, and other resources.',
          legend: [{ label: 'Blue: supplied materials', color: colors.blue }, { label: 'Teal: sugar and oxygen output', color: colors.teal }, { label: 'Gold: light energy, not matter', color: colors.gold }],
          sources: [{ label: 'OpenStax: overview of photosynthesis', url: 'https://openstax.org/books/biology-2e/pages/8-1-overview-of-photosynthesis' }] };
      },
    },
    'bio.1.food-chains': {
      title: 'Follow energy through a food chain',
      instructions: 'Start with energy stored by grass. Change the fraction reaching the next feeding level and compare the three energy bars.',
      initial: { energy: 1000, percent: 10 },
      controls: [{ key: 'energy', label: 'Energy stored by producers', min: 100, max: 1000, step: 100, unit: ' units' },
        { key: 'percent', label: 'Transfer to each next level', min: 5, max: 20, step: 5, unit: '%' }],
      calculate(s) {
        const levels = [s.energy, s.energy * s.percent / 100, s.energy * (s.percent / 100) ** 2];
        const other = [levels[0] - levels[1], levels[1] - levels[2]];
        return { data: { levels, other },
          readout: 'Grass: ' + levels[0] + ' energy units → rabbits: ' + numberText(levels[1]) + ' → foxes: ' + numberText(levels[2]) +
            '. Each transfer keeps ' + s.percent + '% at the next feeding level. Other paths receive ' + numberText(other[0]) + ' and then ' + numberText(other[1]) + ' units.',
          note: 'Arrows point from food to eater: this is energy flow, not the direction an animal chases its prey. Grass captures sunlight; the starting amount here is energy already stored in producer growth, not all incoming sunlight. The selected percentage is an illustrative assumption, not a universal 10% law. Energy not incorporated at the next level includes respiration and heat, uneaten material, and waste; decomposers use some of that material. This simple chain omits the rest of the food web. Bars share a fixed 0–1000 scale.',
          legend: [{ label: 'Teal: energy at each feeding level', color: colors.teal }, { label: 'Gold arrows: food → eater', color: colors.gold }],
          sources: [{ label: 'OpenStax: energy flow in ecosystems', url: 'https://openstax.org/books/biology-2e/pages/46-2-energy-flow-through-ecosystems' }] };
      },
    },
    'math.5.diffgeo': {
      title: 'Measure curvature from a geodesic triangle',
      instructions: 'Change the angle between two meridians and the sphere’s radius. Compare triangle area with the excess over a flat triangle’s angle sum.',
      initial: { angle: 90, radius: 2 },
      controls: [{ key: 'angle', label: 'Meridian separation α', min: 15, max: 150, step: 15, unit: '°' },
        { key: 'radius', label: 'Sphere radius R', min: 1, max: 4, step: .5 }],
      calculate(s) {
        const excess = s.angle * Math.PI / 180, curvature = 1 / s.radius ** 2, area = s.radius ** 2 * excess;
        return { data: { excess, curvature, area, angleSum: 180 + s.angle },
          readout: 'Angles 90°, 90°, ' + s.angle + '° sum to ' + (180 + s.angle) + '°. Excess E = ' + s.angle + '° = ' + numberText(excess) +
            ' radians. Radius ' + s.radius + ': K = ' + numberText(curvature) + ', area A = ' + numberText(area) + '. K × A = E.',
          note: 'Two meridians from the north pole and their shorter equatorial arc form this geodesic triangle. Its area is R²α with α in radians, and Gaussian curvature is 1/R². Gauss–Bonnet gives angle excess ∫K dA = KA. Increasing R at fixed α increases area while reducing curvature; the excess stays fixed. The sphere is drawn at a normalized size in an orthographic projection: screen angles are not surface angles. This constant-curvature example is not a model of arbitrary spacetime.',
          legend: [{ label: 'Teal: geodesic triangle', color: colors.teal }, { label: 'Gold: equatorial edge', color: colors.gold }],
          sources: [{ label: 'Hopf: spherical excess and curvature', url: 'https://pi.math.cornell.edu/~hatcher/Other/hopf-samelson.pdf' }] };
      },
    },
    'math.5.complex-analysis': {
      title: 'What a contour encloses determines its integral',
      instructions: 'Expand a circular contour around 0, change the residues at 0 and 2, and reverse its orientation. Watch for a singularity on the path.',
      initial: { radius: 1.5, a: 1, b: -1, clockwise: false },
      controls: [{ key: 'radius', label: 'Contour radius r', min: .5, max: 3, step: .5 },
        { key: 'a', label: 'Residue a at 0', min: -2, max: 2, step: 1 },
        { key: 'b', label: 'Residue b at 2', min: -2, max: 2, step: 1 },
        { key: 'clockwise', label: 'Clockwise orientation', type: 'toggle' }],
      calculate(s) {
        const direction = s.clockwise ? -1 : 1, onPath = s.radius === 2 && s.b !== 0;
        const sum = s.a + (s.radius > 2 ? s.b : 0), multiplier = onPath ? null : direction * sum;
        return { data: { direction, onPath, sum, multiplier, imaginary: onPath ? null : 2 * Math.PI * multiplier },
          readout: 'f(z) = ' + s.a + '/z + ' + s.b + '/(z−2). Radius ' + s.radius + ', ' + (s.clockwise ? 'clockwise' : 'counterclockwise') + '. ' +
            (onPath ? 'Pole at 2 lies on the path: the ordinary contour integral is undefined.' : 'Enclosed residue sum = ' + sum + '. Integral = 2πi × ' + multiplier + '.') +
            (s.a === 0 || s.b === 0 ? ' A zero coefficient removes that singular term.' : ''),
          note: 'For this rational function and a simple closed contour avoiding its poles, the integral equals 2πi times the enclosed residue sum for counterclockwise travel; clockwise travel changes the sign. Crossing a pole is not a continuous deformation within the domain. At r=2 and b≠0, no ordinary contour integral exists; no principal value is being supplied. Zero coefficients mean the corresponding term is omitted and its apparent singularity is filled in by holomorphic extension.',
          legend: [{ label: 'Blue: directed contour', color: colors.blue }, { label: 'Coral: nonzero-residue pole', color: colors.coral }, { label: 'Outline: removed singularity', color: colors.ink }],
          sources: [{ label: 'MIT: residue theorem', url: 'https://ocw.mit.edu/courses/18-04-complex-variables-with-applications-spring-2018/resources/mit18_04s18_topic8/' }] };
      },
    },
    'math.5.logic': {
      title: 'Construct the subset missing from a proposed list',
      instructions: 'Each row encodes a subset of {1,…,6}. Change any row. The diagonal rule constructs D by reversing membership on the diagonal.',
      initial: { row1: 21, row2: 42, row3: 7, row4: 56, row5: 12, row6: 51 },
      controls: Array.from({ length: 6 }, (_, i) => ({ key: 'row' + (i + 1), label: 'Subset f(' + (i + 1) + '): membership mask', min: 0, max: 63, step: 1 })),
      calculate(s) {
        const rows = Array.from({ length: 6 }, (_, i) => Array.from({ length: 6 }, (_, j) => (s['row' + (i + 1)] >> j) & 1));
        const diagonal = rows.map((row, i) => 1 - row[i]), members = diagonal.flatMap((bit, i) => bit ? [i + 1] : []);
        const describe = bits => '{' + bits.flatMap((bit, i) => bit ? [i + 1] : []).join(', ') + '}';
        return { data: { rows, diagonal, members },
          readout: rows.map((row, i) => 'f(' + (i + 1) + ')=' + describe(row)).join('; ') + '. D=' + describe(diagonal) +
            '. D differs from every row i at membership of i.',
          note: 'Bit weights from left to right are 1,2,4,8,16,32; for example mask 5 encodes {1,3}. This finite example shows that no six-row list covers all 64 subsets. The general proof does not rely on a finite experiment: for any function f:S→P(S), define D={x∈S : x∉f(x)}. If D=f(a), membership of a would give a∈D if and only if a∉D, a contradiction. Thus f is never onto. With the singleton injection, Cantor’s theorem gives |S|<|P(S)|, including infinite S. This is a set-membership argument, avoiding ambiguous binary expansions of real numbers.',
          legend: [{ label: 'Gold: diagonal memberships', color: colors.gold }, { label: 'Teal: flipped diagonal, subset D', color: colors.teal }],
          sources: [{ label: 'MIT: Cantor’s theorem and diagonal arguments', url: 'https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-spring-2015/mit6_042js15_textbook.pdf' }] };
      },
    },
    'math.5.frontier': {
      title: 'Evidence is not a universal proof',
      instructions: 'Test the conjecture that n²+n+41 is prime for every nonnegative integer. Extend the checked range and inspect a selected value.',
      initial: { bound: 20, selected: 10 },
      controls: [{ key: 'bound', label: 'Check integers from 0 through', min: 0, max: 60, step: 1 },
        { key: 'selected', label: 'Inspect integer n', min: 0, max: 60, step: 1 }],
      calculate(s) {
        const inspect = n => {
          const value = n * n + n + 41;
          let divisor = null;
          for (let k = 2; k * k <= value; k++) if (value % k === 0) { divisor = k; break; }
          return { n, value, divisor, prime: divisor === null };
        };
        const checked = Array.from({ length: s.bound + 1 }, (_, n) => inspect(n));
        const selected = inspect(s.selected), counterexamples = checked.filter(row => !row.prime);
        return { data: { checked, selected, counterexamples },
          readout: 'Checked ' + checked.length + ' integers: ' + counterexamples.length + ' counterexamples. ' +
            (counterexamples.length ? 'The universal conjecture is false.' : 'No counterexample in this finite range; this does not prove the conjecture.') +
            ' At n=' + s.selected + ', value ' + selected.value + (selected.prime ? ' is prime.' : ' = ' + selected.divisor + ' × ' + selected.value / selected.divisor + '.'),
          note: 'Each primality test here is exact: a composite positive integer has a divisor no larger than its square root. But checking finitely many n cannot establish a statement about every nonnegative integer. At n=40 the value is 1681=41², so this particular conjecture is refuted. This is a deliberately settled example of research logic, not a simulation that settles an open problem. The selected value can lie outside the checked range.',
          sources: [],
          legend: [{ label: 'Teal: prime', color: colors.teal }, { label: 'Coral: composite', color: colors.coral }, { label: 'Outline: not yet checked', color: colors.ink }] };
      },
    },
    'math.5.abstract': {
      title: 'Generate a subgroup of the cyclic group',
      instructions: 'In the additive group Z/nZ, repeatedly add g. Compare the subgroup reached with the full group.',
      initial: { n: 8, g: 2, steps: 2 },
      controls: [{ key: 'n', label: 'Group size n', min: 2, max: 12, step: 1 },
        { key: 'g', label: 'Integer representative g', min: 0, max: 11, step: 1 },
        { key: 'steps', label: 'Repeated additions', min: 0, max: 12, step: 1 }],
      calculate(s) {
        const residue = s.g % s.n, orbit = [0]; let next = residue;
        while (next !== 0) { orbit.push(next); next = (next + residue) % s.n; }
        return { data: { residue, orbit, order: orbit.length, current: s.steps * residue % s.n, generator: orbit.length === s.n },
          readout: 'In Z/' + s.n + 'Z, g = ' + residue + '. Generated subgroup: {' + [...orbit].sort((a, b) => a - b).join(', ') + '}. Order ' + orbit.length +
            '. After ' + s.steps + ' additions: ' + s.steps * residue % s.n + '. ' + (orbit.length === s.n ? 'This element generates the whole group.' : 'This is a proper subgroup.'),
          note: 'The operation is addition modulo n. The order of g is n/gcd(n,g), so g generates the whole group exactly when gcd(n,g)=1. The identity 0 has order 1. The circle represents residues, not multiplication of complex numbers; arrows represent adding the same residue.',
          legend: [{ label: 'Teal vertices: generated subgroup', color: colors.teal }, { label: 'Gold: current residue', color: colors.gold }],
          sources: [{ label: 'MIT: cyclic groups', url: 'https://ocw.mit.edu/courses/18-703-modern-algebra-spring-2013/resources/mit18_703s13_pra_l_4/' }] };
      },
    },
    'math.5.measure': {
      title: 'Finite covers and limiting measure',
      instructions: 'Remove middle gaps repeatedly. Compare removing a third of each interval with progressively smaller gaps.',
      initial: { stage: 3, varying: false },
      controls: [{ key: 'stage', label: 'Construction stage', min: 0, max: 5, step: 1 },
        { key: 'varying', label: 'Remove gaps of length 4 to minus the stage', type: 'toggle' }],
      calculate(s) {
        const layers = [[[0, 1]]];
        for (let k = 1; k <= s.stage; k++) layers.push(layers[k - 1].flatMap(([a, b]) => {
          const gap = s.varying ? 4 ** -k : (b - a) / 3, mid = (a + b) / 2;
          return [[a, mid - gap / 2], [mid + gap / 2, b]];
        }));
        const length = layers[layers.length - 1].reduce((sum, [a, b]) => sum + b - a, 0), limit = s.varying ? .5 : 0;
        return { data: { layers, length, limit, count: 2 ** s.stage },
          readout: 'Stage ' + s.stage + ': ' + 2 ** s.stage + ' closed intervals, total length ' + numberText(length) + '. Limiting Lebesgue measure = ' + limit + '.',
          note: 'The middle-third construction has remaining length (2/3)^k. Removing a middle gap of length 4^(−k) from every interval at stage k leaves length 1/2 + 2^(−k−1). Continuity of measure from above gives limiting measures 0 and 1/2. Both limiting sets are uncountable with empty interior: cardinality, topology and measure differ. A finite drawing consists of intervals; it is not the infinite limiting set.',
          legend: [{ label: 'Teal: remaining closed intervals', color: colors.teal }, { label: 'Blank gaps: removed open intervals', color: colors.paper }],
          sources: [{ label: 'Harvard: real analysis and Cantor sets', url: 'https://people.math.harvard.edu/~ctm/home/text/class/harvard/114/14/html/home/course/course.pdf' }] };
      },
    },
    'math.5.functional': {
      title: 'Orthogonal projection in a function space',
      instructions: 'Approximate f(x)=x on (−π,π) by sine functions. Add more basis functions or perturb the first coefficient away from its optimal value.',
      initial: { terms: 3, perturb: 0 },
      controls: [{ key: 'terms', label: 'Sine basis functions N', min: 1, max: 12, step: 1 },
        { key: 'perturb', label: 'Perturb first coefficient', min: -1, max: 1, step: .25 }],
      calculate(s) {
        const coefficients = Array.from({ length: s.terms }, (_, i) => 2 * (i % 2 ? -1 : 1) / (i + 1));
        const normSquared = 2 * Math.PI ** 2 / 3, captured = coefficients.reduce((a, b) => a + b * b, 0);
        const optimalErrorSquared = normSquared - captured, errorSquared = optimalErrorSquared + s.perturb ** 2;
        return { data: { coefficients, normSquared, captured, optimalErrorSquared, errorSquared },
          readout: 'Projection onto span{sin x,…,sin(' + s.terms + 'x)}. Optimal squared L² error ' + numberText(optimalErrorSquared) +
            '; after perturbing coefficient 1 by ' + s.perturb + ', squared error ' + numberText(errorSquared) + ' = optimal + perturbation².',
          note: 'Use inner product (1/π)∫₋π^π f(x)g(x)dx, making these sine functions orthonormal. For f(x)=x, coefficient n is 2(−1)^(n+1)/n and ||f||²=2π²/3. The orthogonal residual gives the best approximation in this finite span. Perturbing one coefficient adds its square to the squared error. As N grows, error tends to zero in L², not uniformly for the periodic extension; endpoint values do not affect L² classes.',
          legend: [{ label: 'Blue: target f(x)=x', color: colors.blue }, { label: 'Gold: chosen sine approximation', color: colors.gold }],
          sources: [{ label: 'MIT: orthonormal bases and Fourier series', url: 'https://ocw.mit.edu/courses/18-102-introduction-to-functional-analysis-spring-2021/resources/mit18_102s21_lec15/' }] };
      },
    },
    'math.5.numerical': {
      title: 'A certified bracket versus a Newton iteration',
      instructions: 'Solve x³−2x+2=0. Compare bisection on [−2,−1] with Newton’s method from a chosen starting point.',
      initial: { start: 0, iterations: 4 },
      controls: [{ key: 'start', label: 'Newton starting value', min: -2, max: 2, step: .25 },
        { key: 'iterations', label: 'Iterations', min: 0, max: 10, step: 1 }],
      calculate(s) {
        const f = x => x ** 3 - 2 * x + 2, brackets = [[-2, -1]], newton = [s.start]; let stopped = false;
        for (let i = 0; i < s.iterations; i++) {
          const [a, b] = brackets[brackets.length - 1], mid = (a + b) / 2;
          brackets.push(f(mid) < 0 ? [mid, b] : [a, mid]);
          if (!stopped) {
            const x = newton[newton.length - 1], derivative = 3 * x * x - 2;
            const next = x - f(x) / derivative;
            if (!Number.isFinite(next) || Math.abs(next) > 1e8) stopped = true;
            else newton.push(next);
          }
        }
        const bracket = brackets[brackets.length - 1], estimate = (bracket[0] + bracket[1]) / 2, last = newton[newton.length - 1];
        return { data: { brackets, bracket, estimate, errorBound: (bracket[1] - bracket[0]) / 2, newton, last, residual: Math.abs(f(last)), stopped },
          readout: 'After ' + s.iterations + ' iterations, the exact bisection midpoint (' + estimate + ') has certified absolute error ≤ 1/' + 2 ** (s.iterations + 1) +
            '. Newton: ' + last.toPrecision(6) + ', residual |f(x)| = ' + Math.abs(f(last)).toPrecision(4) + (stopped ? '. Iteration stopped at a numerical guard.' : '.'),
          note: 'Continuity and the sign change bracket a root; f is strictly increasing on [−2,−1], so that root is unique there. Bisection halves the bracket each step. Newton uses x−f(x)/f′(x) and can converge rapidly near a simple root, but need not converge from an arbitrary start: 0→1→0 is a cycle here. A residual is not automatically an error bound. Displayed digits are rounded; a finite iteration is not an exact root.',
          legend: [{ label: 'Teal: certified bisection intervals', color: colors.teal }, { label: 'Gold: Newton iterates', color: colors.gold }],
          sources: [{ label: 'NIST DLMF: nonlinear equations', url: 'https://dlmf.nist.gov/3.8' }] };
      },
    },
    'math.4.diffeq': {
      title: 'A differential equation and its numerical steps',
      instructions: 'Compare the exact decay y′ = −ky with Euler steps. Reduce the step size and inspect the error.',
      initial: { rate: 1, initial: 3, steps: 4 },
      controls: [{ key: 'rate', label: 'Decay rate k', min: .5, max: 2, step: .5 },
        { key: 'initial', label: 'Initial value y(0)', min: 1, max: 4, step: 1 },
        { key: 'steps', label: 'Euler steps over time 0–2', min: 2, max: 16, step: 2 }],
      calculate(s) {
        const h = 2 / s.steps, factor = 1 - s.rate * h, values = [s.initial];
        for (let i = 0; i < s.steps; i++) values.push(values[i] * factor);
        const exact = s.initial * Math.exp(-2 * s.rate), approximate = values[values.length - 1];
        return { data: { h, factor, values, exact, approximate, error: Math.abs(approximate - exact) },
          readout: 'Euler: y next = y(1−kh), with h = ' + h + ' and multiplier ' + numberText(factor) + '. At t=2, Euler gives ' + numberText(approximate) +
            ', exact y₀e^(−kt) gives ' + numberText(exact) + '; absolute error ' + numberText(Math.abs(approximate - exact)) + '.',
          note: 'The differential equation specifies the instantaneous slope, not a finite-step multiplier. Euler uses the current slope over a whole step. Exact positive decay stays positive; large steps can alternate signs or fail to decay. For this equation Euler is asymptotically stable only when 0 < kh < 2. Reducing h improves the approximation over this fixed interval.',
          legend: [{ label: 'Blue: exact exponential decay', color: colors.blue }, { label: 'Gold: Euler steps', color: colors.gold }], sources: [] };
      },
    },
    'math.4.discrete': {
      title: 'Can one walk use every edge exactly once?',
      instructions: 'Add or remove graph edges. Inspect vertex degrees and, when possible, trace an Euler trail.',
      initial: { e01: true, e02: false, e03: true, e12: true, e13: false, e23: true, step: 0 },
      controls: ['01', '02', '03', '12', '13', '23'].map(pair => ({ key: 'e' + pair, label: 'Edge ' + 'ABCD'[Number(pair[0])] + '–' + 'ABCD'[Number(pair[1])], type: 'toggle' })).concat([{ key: 'step', label: 'Trace edges up to step', min: 0, max: 6, step: 1 }]),
      calculate(s) {
        const edges = ['01', '02', '03', '12', '13', '23'].filter(pair => s['e' + pair]).map(pair => pair.split('').map(Number));
        const degrees = [0, 0, 0, 0]; edges.forEach(([a, b]) => { degrees[a]++; degrees[b]++; });
        const active = degrees.map((d, i) => d ? i : -1).filter(i => i >= 0), odd = active.filter(i => degrees[i] % 2);
        const seen = new Set(active.length ? [active[0]] : []);
        for (let pass = 0; pass < 4; pass++) edges.forEach(([a, b]) => { if (seen.has(a) || seen.has(b)) { seen.add(a); seen.add(b); } });
        const connected = active.every(i => seen.has(i)), possible = connected && [0, 2].includes(odd.length);
        const walk = [];
        if (possible && edges.length) {
          const used = new Set(), stack = [odd[0] ?? active[0]];
          while (stack.length) {
            const v = stack[stack.length - 1], next = edges.findIndex(([a, b], i) => !used.has(i) && (a === v || b === v));
            if (next < 0) walk.push(stack.pop());
            else { used.add(next); stack.push(edges[next][0] === v ? edges[next][1] : edges[next][0]); }
          }
          walk.reverse();
        }
        const traced = Math.min(s.step, edges.length), kind = !edges.length ? 'empty' : !possible ? 'none' : odd.length ? 'trail' : 'circuit';
        return { data: { edges, degrees, odd, connected, possible, walk, traced, kind },
          readout: 'Degrees A–D: ' + degrees.join(', ') + '. ' + (kind === 'empty' ? 'No edges: the empty walk is trivial.' : kind === 'none' ? 'No Euler trail.' :
            'Euler ' + kind + ': ' + walk.map(i => 'ABCD'[i]).join(' → ') + '. Trace ' + traced + '/' + edges.length + ' edges.') +
            (connected ? '' : ' Non-isolated vertices are disconnected.'),
          note: 'An undirected graph has an Euler trail precisely when its non-isolated vertices are connected and it has zero or two odd-degree vertices. Zero gives a closed circuit; two give an open trail with those endpoints. Edge crossings are not extra vertices. Isolated vertices need not be visited. The degree sum is twice the edge count.',
          legend: [{ label: 'Blue: selected edges', color: colors.blue }, { label: 'Gold: traced edges', color: colors.gold },
            { label: 'Coral vertices: odd degree', color: colors.coral }], sources: [] };
      },
    },
    'math.4.numtheory': {
      title: 'Euclid’s algorithm and Bézout’s identity',
      instructions: 'Choose two integers. Follow successive divisions and verify that their greatest common divisor is an integer combination of them.',
      initial: { a: 30, b: 18 },
      controls: [{ key: 'a', label: 'First positive integer', min: 1, max: 40, step: 1 }, { key: 'b', label: 'Second positive integer', min: 1, max: 40, step: 1 }],
      calculate(s) {
        let oldR = s.a, r = s.b, oldX = 1, x = 0, oldY = 0, y = 1;
        const divisions = [];
        while (r) {
          const q = Math.floor(oldR / r), remainder = oldR % r;
          divisions.push({ dividend: oldR, divisor: r, q, remainder });
          [oldR, r] = [r, remainder]; [oldX, x] = [x, oldX - q * x]; [oldY, y] = [y, oldY - q * y];
        }
        return { data: { gcd: oldR, x: oldX, y: oldY, divisions, coprime: oldR === 1 },
          readout: 'gcd(' + s.a + ', ' + s.b + ') = ' + oldR + '. Bézout: (' + oldX + ')×' + s.a + ' + (' + oldY + ')×' + s.b + ' = ' + oldR + '.',
          note: 'Replacing (a,b) with (b,a mod b) preserves their common divisors. Positive remainders strictly decrease, so the algorithm stops. The final nonzero remainder is the gcd. Bézout coefficients express it as ax+by. When gcd(a,b)=1 and b>1, x modulo b is a multiplicative inverse of a modulo b.',
          legend: [{ label: 'Teal: successive remainder divisions', color: colors.teal }, { label: 'Gold: final gcd', color: colors.gold }], sources: [] };
      },
    },
    'math.4.analysis': {
      title: 'An epsilon band and a delta neighbourhood',
      instructions: 'For f(x)=x² at x=a, choose an output tolerance ε and an input radius δ. Check the entire neighbourhood, not just one sampled point.',
      initial: { a: 1, epsilon: .5, delta: .1 },
      controls: [{ key: 'a', label: 'Point a', min: 0, max: 3, step: 1 },
        { key: 'epsilon', label: 'Output tolerance ε', min: .25, max: 2, step: .25 },
        { key: 'delta', label: 'Input radius δ', min: .05, max: 1, step: .05 }],
      calculate(s) {
        const bound = 2 * Math.abs(s.a) * s.delta + s.delta ** 2, works = bound <= s.epsilon + 1e-12;
        return { data: { bound, works, limit: s.a ** 2, safeDelta: Math.min(1, s.epsilon / (2 * Math.abs(s.a) + 1)) },
          readout: 'For 0 < |x−a| < ' + s.delta + ', |x²−a²| < 2|a|δ+δ² = ' + numberText(bound) + '. ε = ' + s.epsilon +
            '. This δ ' + (works ? 'works for every point in the punctured neighbourhood.' : 'is too large; points near its right boundary violate the tolerance.'),
          note: 'Write x=a+h: |x²−a²| ≤ 2|a||h|+h². For |h|<δ this is strictly below 2|a|δ+δ², so a boundary bound equal to ε is sufficient. Choosing δ=min(1, ε/(2|a|+1)) always works. The shaded input interval excludes its endpoints and h=0; the drawing shows the interval’s closure. Values are rounded in the readout.',
          legend: [{ label: 'Teal band: |output error| < ε', color: colors.teal }, { label: 'Gold strip: |x−a| < δ', color: colors.gold },
            { label: 'Blue: output error x²−a²', color: colors.blue }], sources: [] };
      },
    },
    'math.4.prob-theory': {
      title: 'A binomial random variable',
      instructions: 'Set the number of independent trials and the success probability. Inspect the distribution and its cumulative probability.',
      initial: { n: 6, percent: 50, cutoff: 3 },
      controls: [{ key: 'n', label: 'Independent trials n', min: 1, max: 10, step: 1 },
        { key: 'percent', label: 'Success probability (%)', min: 0, max: 100, step: 10 },
        { key: 'cutoff', label: 'Count successes up to k', min: 0, max: 10, step: 1 }],
      calculate(s) {
        const p = s.percent / 100, probabilities = [];
        let choose = 1;
        for (let k = 0; k <= s.n; k++) {
          if (k) choose = choose * (s.n - k + 1) / k;
          probabilities.push(choose * p ** k * (1 - p) ** (s.n - k));
        }
        const cumulative = probabilities.slice(0, s.cutoff + 1).reduce((a, b) => a + b, 0);
        return { data: { probabilities, cumulative, mean: s.n * p, variance: s.n * p * (1 - p) },
          readout: 'X ~ Binomial(' + s.n + ', ' + p + '). E[X] = ' + numberText(s.n * p) + ', Var(X) = ' + numberText(s.n * p * (1 - p)) +
            '. P(X ≤ ' + s.cutoff + ') ≈ ' + numberText(100 * cumulative) + '%.',
          note: 'The binomial model counts successes in n independent Bernoulli trials with the same probability p. Bar heights are probabilities, not sample frequencies, and sum to 1. The mean need not be an attainable integer. At p=0 or p=1 all mass is at a single outcome. Independence and constant p are essential assumptions.',
          legend: [{ label: 'Gold: outcomes ≤ k', color: colors.gold }, { label: 'Blue: outcomes > k', color: colors.blue }], sources: [] };
      },
    },
    'math.3.euclid': {
      title: 'Rearrange a proof of Pythagoras',
      instructions: 'Change the two perpendicular legs, then rearrange the same four triangles. Compare the uncovered areas.',
      initial: { a: 3, b: 4, rearranged: false },
      controls: [{ key: 'a', label: 'Leg a', min: 1, max: 5, step: 1 }, { key: 'b', label: 'Leg b', min: 1, max: 5, step: 1 },
        { key: 'rearranged', label: 'Rearrange into two squares', type: 'toggle' }],
      calculate(s) {
        const total = (s.a + s.b) ** 2, triangles = 2 * s.a * s.b, remaining = s.a ** 2 + s.b ** 2;
        return { data: { total, triangles, remaining, hypotenuse: Math.hypot(s.a, s.b) },
          readout: (s.rearranged ? 'Two uncovered squares: a² + b²' : 'One uncovered square: c²') + '. Outer area ' + total +
            ' minus four triangle areas ' + triangles + ' leaves ' + remaining + '. Thus c² = ' + s.a ** 2 + ' + ' + s.b ** 2 + ' = ' + remaining + '.',
          note: 'Both arrangements use the same square of side a+b and the same four congruent right triangles. In the tilted arrangement, each inner side is a hypotenuse and each inner angle is 90° because the two acute triangle angles sum to 90°. Subtract equal triangle areas: c² = (a+b)² − 2ab = a²+b². The algebra proves the result for all positive legs, not just these examples.',
          legend: [{ label: 'Teal: the same four triangles', color: colors.teal }, { label: 'Gold: equal uncovered area', color: colors.gold }], sources: [] };
      },
    },
    'math.4.complex': {
      title: 'Multiply: rotate and scale',
      instructions: 'Choose a complex number, then multiply it by a positive scale and a power of i. Track its real and imaginary coordinates.',
      initial: { real: 1, imaginary: 1, turns: 1, scale: 1 },
      controls: [{ key: 'real', label: 'Real part', min: -3, max: 3, step: 1 },
        { key: 'imaginary', label: 'Imaginary part', min: -3, max: 3, step: 1 },
        { key: 'turns', label: 'Counterclockwise quarter-turns', min: 0, max: 4, step: 1 },
        { key: 'scale', label: 'Positive scale factor', min: 1, max: 2, step: 1 }],
      calculate(s) {
        let real = s.real, imaginary = s.imaginary;
        for (let i = 0; i < s.turns; i++) [real, imaginary] = [-imaginary, real];
        real *= s.scale; imaginary *= s.scale;
        return { data: { real, imaginary, modulus: Math.hypot(s.real, s.imaginary), resultModulus: Math.hypot(real, imaginary) },
          readout: '(' + s.real + ' + (' + s.imaginary + ')i) × ' + s.scale + 'i^' + s.turns + ' = ' + real + ' + (' + imaginary + ')i. Rotation ' + 90 * s.turns + '°. Modulus scales by ' + s.scale + '.',
          note: 'Multiplication by i sends (a,b) to (−b,a), a 90° counterclockwise rotation on equally scaled axes. Repeating four times returns to the original number. Multiplication by a positive real scales length. Zero stays at the origin and has no defined argument.',
          legend: [{ label: 'Blue: original z', color: colors.blue }, { label: 'Coral: product', color: colors.coral }], sources: [] };
      },
    },
    'math.4.diff-calc': {
      title: 'From a secant slope to a derivative',
      instructions: 'Shrink the signed step h from either side. Compare a smooth parabola with the corner of absolute value.',
      initial: { mode: 'square', x: 1, closeness: 1, left: false },
      controls: [{ key: 'mode', label: 'Function', options: [{ value: 'square', label: 'Parabola: x squared' }, { value: 'absolute', label: 'Corner: absolute value of x' }] },
        { key: 'x', label: 'Point x', min: -2, max: 2, step: .5 },
        { key: 'closeness', label: 'Step size: 10 to minus this power', min: 0, max: 3, step: 1 },
        { key: 'left', label: 'Approach from the left', type: 'toggle' }],
      calculate(s) {
        const h = (s.left ? -1 : 1) * 10 ** -s.closeness, f = x => s.mode === 'square' ? x * x : Math.abs(x);
        const y = f(s.x), otherX = s.x + h, otherY = f(otherX);
        const secant = s.mode === 'square' ? 2 * s.x + h : (otherY - y) / h;
        const derivative = s.mode === 'square' ? 2 * s.x : s.x === 0 ? null : Math.sign(s.x);
        return { data: { h, y, otherX, otherY, secant, derivative },
          readout: 'h = ' + h + ', secant slope [f(x+h)−f(x)]/h = ' + numberText(secant) + '. ' +
            (derivative === null ? 'At the corner, left slopes approach −1 and right slopes +1: no derivative.' : 'Derivative at x = ' + s.x + ' is ' + derivative + '.'),
          note: 'For x² the difference quotient simplifies to 2x+h when h≠0 and tends to 2x. A derivative requires agreement from both sides. For |x| at zero the slopes disagree, even though the function is continuous and has a minimum. Displayed slopes are rounded; the step remains nonzero.',
          legend: [{ label: 'Blue: function', color: colors.blue }, { label: 'Gold: secant', color: colors.gold },
            { label: 'Dashed coral: tangent when it exists', color: colors.coral }], sources: [] };
      },
    },
    'math.4.int-calc': {
      title: 'Rectangles accumulate signed area',
      instructions: 'Approximate the integral of x−c from 0 to b. Change the number of rectangles and the sample point in each interval.',
      initial: { shift: 2, end: 4, count: 4, method: 'left' },
      controls: [{ key: 'shift', label: 'Zero crossing c', min: 0, max: 3, step: 1 },
        { key: 'end', label: 'Upper endpoint b', min: 1, max: 6, step: 1 },
        { key: 'count', label: 'Rectangles', min: 2, max: 20, step: 2 },
        { key: 'method', label: 'Sample position', options: [{ value: 'left', label: 'Left endpoint' }, { value: 'midpoint', label: 'Midpoint' }, { value: 'right', label: 'Right endpoint' }] }],
      calculate(s) {
        const width = s.end / s.count, offset = s.method === 'left' ? 0 : s.method === 'right' ? 1 : .5;
        const rectangles = Array.from({ length: s.count }, (_, i) => ({ start: i * width, width, height: (i + offset) * width - s.shift }));
        const sum = rectangles.reduce((a, r) => a + r.width * r.height, 0), exact = s.end ** 2 / 2 - s.shift * s.end;
        return { data: { rectangles, sum, exact, error: sum - exact, endpointSlope: s.end - s.shift },
          readout: s.count + ' ' + s.method + ' rectangles: signed sum ' + numberText(sum) + '. Exact integral b²/2 − cb = ' + numberText(exact) +
            '. Error ' + numberText(sum - exact) + '. Accumulation rate at b is f(b) = ' + (s.end - s.shift) + '.',
          note: 'Areas below the axis subtract; the integral is net signed accumulation, not total geometric area. For this increasing linear function, left sums underestimate and right sums overestimate; midpoint sums happen to be exact. More rectangles reduce endpoint-sum error. The Fundamental Theorem gives d/db ∫₀ᵇ(x−c) dx = b−c.',
          legend: [{ label: 'Teal: positive rectangle', color: colors.teal }, { label: 'Coral: negative rectangle', color: colors.coral },
            { label: 'Blue: x−c', color: colors.blue }], sources: [] };
      },
    },
    'math.3.probability': {
      title: 'Count equally likely outcomes',
      instructions: 'Choose a target sum for two fair, independent dice. Compare an exact sum with the chance of that sum or less.',
      initial: { target: 7, cumulative: false },
      controls: [{ key: 'target', label: 'Target sum', min: 2, max: 12, step: 1 },
        { key: 'cumulative', label: 'Count target or less', type: 'toggle' }],
      calculate(s) {
        const outcomes = Array.from({ length: 36 }, (_, i) => {
          const first = Math.floor(i / 6) + 1, second = i % 6 + 1, sum = first + second;
          return { first, second, sum, selected: s.cumulative ? sum <= s.target : sum === s.target };
        });
        const count = outcomes.filter(p => p.selected).length;
        return { data: { outcomes, count, probability: count / 36 },
          readout: 'P(sum ' + (s.cumulative ? '≤ ' : '= ') + s.target + ') = ' + count + '/36 ≈ ' + numberText(count / 36 * 100) + '%.',
          note: 'There are 36 equally likely ordered pairs, not 11 equally likely sums. (1, 6) and (6, 1) are different outcomes. The counting argument assumes fair dice and independent rolls; it does not apply unchanged to biased or dependent dice.',
          legend: [{ label: 'Teal: event occurs', color: colors.teal }, { label: 'Pale: outside event', color: colors.paper }], sources: [] };
      },
    },
    'math.3.statistics': {
      title: 'Centre, deviations and spread',
      instructions: 'Move the whole dataset, spread it out, or move one observation. Compare mean and standard deviation.',
      initial: { centre: 5, spread: 2, outlier: 0, sample: false },
      controls: [{ key: 'centre', label: 'Shift all observations', min: 0, max: 10, step: 1 },
        { key: 'spread', label: 'Base spacing', min: 0, max: 4, step: 1 },
        { key: 'outlier', label: 'Extra shift of E', min: 0, max: 12, step: 1 },
        { key: 'sample', label: 'Use sample standard deviation', type: 'toggle' }],
      calculate(s) {
        const values = [-2, -1, 0, 1, 2].map((v, i) => s.centre + v * s.spread + (i === 4 ? s.outlier : 0));
        const mean = values.reduce((a, b) => a + b, 0) / 5, deviations = values.map(v => v - mean);
        const squaredSum = deviations.reduce((a, b) => a + b * b, 0), divisor = s.sample ? 4 : 5;
        return { data: { values, mean, deviations, squaredSum, divisor, variance: squaredSum / divisor, sd: Math.sqrt(squaredSum / divisor) },
          readout: 'Data: ' + values.join(', ') + '. Mean = ' + numberText(mean) + '. Sum of squared deviations = ' + numberText(squaredSum) +
            '. Divide by ' + divisor + ' and take the square root: SD = ' + numberText(Math.sqrt(squaredSum / divisor)) + '.',
          note: 'Horizontal distances from the mean measure deviations; squaring prevents opposite signs cancelling. Use n for the SD of this complete population, or n−1 for the usual sample variance estimate. Taking its square root gives sample SD; it is not itself an unbiased estimator. Shifting every value preserves spread. Five constructed values do not establish a population claim.',
          legend: [{ label: 'Blue dots: observations', color: colors.blue }, { label: 'Coral line: mean', color: colors.coral },
            { label: 'Gold: distance from mean', color: colors.gold }], sources: [] };
      },
    },
    'math.3.precalc': {
      title: 'Nearby values versus the value at a point',
      instructions: 'Bring x closer from each side. Change the value at the point, then compare a removable hole with a jump.',
      initial: { mode: 'hole', a: 2, closeness: 1, point: 2 },
      controls: [{ key: 'mode', label: 'Function nearby', options: [{ value: 'hole', label: 'Removable hole: x + a nearby' }, { value: 'jump', label: 'Jump: different one-sided limits' }] },
        { key: 'a', label: 'Approach x = a', min: 1, max: 3, step: 1 },
        { key: 'closeness', label: 'Closeness: h = 10 to minus this power', min: 0, max: 3, step: 1 },
        { key: 'point', label: 'Defined value f(a)', min: 0, max: 6, step: 1 }],
      calculate(s) {
        const h = 10 ** -s.closeness, leftX = s.a - h, rightX = s.a + h;
        const left = s.mode === 'hole' ? 2 * s.a - h : s.a, right = s.mode === 'hole' ? 2 * s.a + h : s.a + 2;
        return { data: { h, leftX, rightX, left, right, leftLimit: s.mode === 'hole' ? 2 * s.a : s.a,
          rightLimit: s.mode === 'hole' ? 2 * s.a : s.a + 2, limit: s.mode === 'hole' ? 2 * s.a : null },
          readout: 'h = ' + h + ': f(' + leftX + ') = ' + left + ', f(' + rightX + ') = ' + right + '. f(a) = ' + s.point + '. ' +
            (s.mode === 'hole' ? 'Both sides approach ' + 2 * s.a + ', independently of f(a).' : 'The one-sided limits disagree; the two-sided limit does not exist.'),
          note: 'In hole mode, (x²−a²)/(x−a) = x+a only for x≠a; the chosen f(a) fills or relocates the point. In jump mode values are a to the left and a+2 to the right. Numerical proximity illustrates the formulas, not a general proof that any sampled function has a limit.',
          legend: [{ label: 'Blue: nearby graph', color: colors.blue }, { label: 'Gold dots: approaching values', color: colors.gold },
            { label: 'Coral dot: chosen f(a)', color: colors.coral }], sources: [] };
      },
    },
    'math.3.polynomials': {
      title: 'Factors, multiplicity and coefficients',
      instructions: 'Move three roots or make them coincide. Compare the factored cubic, its expanded coefficients and its graph.',
      initial: { r1: -1, r2: 0, r3: 1, negative: false, zoom: 4 },
      controls: [{ key: 'r1', label: 'Root r₁', min: -2, max: 2, step: 1 },
        { key: 'r2', label: 'Root r₂', min: -2, max: 2, step: 1 },
        { key: 'r3', label: 'Root r₃', min: -2, max: 2, step: 1 },
        { key: 'negative', label: 'Negative leading coefficient', type: 'toggle' },
        { key: 'zoom', label: 'Vertical zoom', min: 1, max: 10, step: 1 }],
      calculate(s) {
        const a = s.negative ? -1 : 1, roots = [s.r1, s.r2, s.r3];
        const b = -a * (s.r1 + s.r2 + s.r3), c = a * (s.r1 * s.r2 + s.r1 * s.r3 + s.r2 * s.r3), e = -a * s.r1 * s.r2 * s.r3;
        const distinct = [...new Set(roots)].sort((x, y) => x - y).map(root => ({ root, multiplicity: roots.filter(x => x === root).length }));
        return { data: { a, b, c, constant: e, roots, distinct },
          readout: 'p(x) = ' + a + roots.map(r => '(x − (' + r + '))').join('') + '. Expanded coefficients [x³, x², x, 1]: [' + [a, b, c, e].join(', ') + ']. ' +
            distinct.map(r => 'Root ' + r.root + ' has multiplicity ' + r.multiplicity).join('; ') + '. Vertical window: ±' + numberText(20 / s.zoom) + '.',
          note: 'Each factor vanishes at its root. Odd multiplicity crosses the axis; even multiplicity touches and turns. The leading coefficient reverses the end behaviour without moving roots. Vertical zoom helps inspect roots without changing the polynomial. The plot shows x from −3 to 3 and clips y to the labelled range: a finite window into an unbounded cubic.',
          legend: [{ label: 'Blue: cubic graph', color: colors.blue }, { label: 'Gold: distinct roots', color: colors.gold }], sources: [] };
      },
    },
    'math.3.trig': {
      title: 'Coordinates on the unit circle',
      instructions: 'Turn the radius around the circle. Read cosine as the horizontal coordinate and sine as the vertical coordinate.',
      initial: { angle: 45 },
      controls: [{ key: 'angle', label: 'Angle in degrees', min: 0, max: 360, step: 15 }],
      calculate(s) {
        const radians = s.angle * Math.PI / 180;
        const clean = x => Math.abs(x) < 1e-12 ? 0 : x;
        const cosine = clean(Math.cos(radians)), sine = clean(Math.sin(radians));
        const tangent = cosine === 0 ? null : sine / cosine;
        return { data: { radians, cosine, sine, tangent },
          readout: s.angle + '°: cos θ = ' + numberText(cosine) + ', sin θ = ' + numberText(sine) +
            ', tan θ ' + (tangent === null ? 'is undefined.' : '= ' + numberText(tangent) + '.'),
          note: 'The radius has length 1, so cos²θ + sin²θ = 1. Coordinates carry signs in each quadrant. Tangent equals sin θ / cos θ and is undefined when cos θ = 0. Values shown are rounded; 360° returns to the starting point.',
          legend: [{ label: 'Blue: unit radius', color: colors.blue }, { label: 'Gold: cosine (x)', color: colors.gold },
            { label: 'Coral: sine (y)', color: colors.coral }], sources: [] };
      },
    },
    'math.3.expo-logs': {
      title: 'Exponentials and logarithms undo each other',
      instructions: 'Choose a base and an exponent. Follow the forward map and then use the logarithm to recover the exponent.',
      initial: { base: 2, exponent: 3 },
      controls: [{ key: 'base', label: 'Base b', min: 2, max: 5, step: 1 },
        { key: 'exponent', label: 'Exponent x', min: -3, max: 3, step: 1 }],
      calculate(s) {
        const value = s.base ** s.exponent, exact = s.exponent < 0 ? '1/' + s.base ** -s.exponent : String(value);
        return { data: { value, exact, recovered: Math.log(value) / Math.log(s.base),
          table: Array.from({ length: 7 }, (_, i) => ({ exponent: i - 3, value: s.base ** (i - 3) })) },
          readout: s.base + '^(' + s.exponent + ') = ' + exact + '. log base ' + s.base + ' of ' + exact + ' = ' + s.exponent + '.',
          note: 'A logarithm asks which exponent produces a positive number. Negative exponents give reciprocals, not negative outputs. Exponent zero gives 1. Valid real logarithm bases are positive and not 1; this activity uses bases 2–5.',
          legend: [{ label: 'Blue: exponent to value', color: colors.blue }, { label: 'Teal: value back to exponent', color: colors.teal }], sources: [] };
      },
    },
    'math.3.sequences': {
      title: 'Add a difference or multiply a ratio',
      instructions: 'Compare arithmetic and geometric sequences. Change the first term, the repeated operation and the number of terms.',
      initial: { mode: 'arithmetic', first: 2, step: 2, count: 6 },
      controls: [{ key: 'mode', label: 'Sequence rule', options: [{ value: 'arithmetic', label: 'Arithmetic: add' }, { value: 'geometric', label: 'Geometric: multiply' }] },
        { key: 'first', label: 'First term', min: 1, max: 4, step: 1 },
        { key: 'step', label: 'Difference or ratio', min: 1, max: 4, step: 1 },
        { key: 'count', label: 'Number of terms', min: 1, max: 6, step: 1 }],
      calculate(s) {
        const values = Array.from({ length: s.count }, (_, i) => s.mode === 'arithmetic' ? s.first + i * s.step : s.first * s.step ** i);
        const sum = values.reduce((a, b) => a + b, 0);
        return { data: { values, sum, maximum: Math.max(...values) },
          readout: (s.mode === 'arithmetic' ? 'Add ' : 'Multiply by ') + s.step + ' each time: ' + values.join(', ') + '. Sum of these ' + s.count + ' terms = ' + sum + '.',
          note: 'Arithmetic: aₙ = a₁ + (n − 1)d. Geometric: aₙ = a₁r^(n − 1). A sequence lists terms; a series adds them. Only positive first terms and positive differences/ratios are explored here. The vertical scale adjusts to the largest term; compare numeric values, not heights across different settings.',
          legend: [{ label: 'Blue points: individual terms', color: colors.blue }, { label: 'Teal: successive-term connections', color: colors.teal }], sources: [] };
      },
    },
    'math.3.systems': {
      title: 'Where do both equations hold?',
      instructions: 'Change the slopes and intercepts of two lines. Look for a point that satisfies both equations.',
      initial: { m1: 1, b1: 1, m2: -1, b2: 3 },
      controls: [{ key: 'm1', label: 'Blue slope', min: -2, max: 2, step: 1 },
        { key: 'b1', label: 'Blue intercept', min: -3, max: 3, step: 1 },
        { key: 'm2', label: 'Coral slope', min: -2, max: 2, step: 1 },
        { key: 'b2', label: 'Coral intercept', min: -3, max: 3, step: 1 }],
      calculate(s) {
        const kind = s.m1 !== s.m2 ? 'one' : s.b1 === s.b2 ? 'infinite' : 'none';
        const x = kind === 'one' ? (s.b2 - s.b1) / (s.m1 - s.m2) : null;
        const y = x === null ? null : s.m1 * x + s.b1;
        const conclusion = kind === 'one' ? 'One solution: (' + numberText(x) + ', ' + numberText(y) + ').' :
          kind === 'infinite' ? 'Infinitely many solutions: the equations describe the same line.' : 'No solution: distinct parallel lines.';
        return { data: { kind, x, y },
          readout: 'Blue: y = ' + s.m1 + 'x + (' + s.b1 + '). Coral: y = ' + s.m2 + 'x + (' + s.b2 + '). ' + conclusion,
          note: 'At an intersection both equations give the same y for the same x. Subtracting the equations gives (m₁ − m₂)x = b₂ − b₁. Equal slopes require checking the intercepts before dividing. Displayed coordinates are rounded to two decimals.',
          legend: [{ label: 'Blue: first equation', color: colors.blue }, { label: 'Dashed coral: second equation', color: colors.coral },
            { label: 'Gold: shared solution', color: colors.gold }], sources: [] };
      },
    },
    'math.3.quadratics': {
      title: 'Vertex, turning point and roots',
      instructions: 'Move the vertex and change the opening direction. Count the points where the parabola meets y = 0.',
      initial: { h: 0, k: -4, a: 1, down: false },
      controls: [{ key: 'h', label: 'Vertex x-coordinate h', min: -2, max: 2, step: 1 },
        { key: 'k', label: 'Vertex height k', min: -4, max: 4, step: 1 },
        { key: 'a', label: 'Steepness magnitude', min: 1, max: 3, step: 1 },
        { key: 'down', label: 'Open downward', type: 'toggle' }],
      calculate(s) {
        const a = s.down ? -s.a : s.a, square = -s.k / a;
        const roots = square < 0 ? [] : square === 0 ? [s.h] : [s.h - Math.sqrt(square), s.h + Math.sqrt(square)];
        return { data: { a, square, roots, b: -2 * a * s.h, c: a * s.h * s.h + s.k },
          readout: 'y = ' + a + '(x − (' + s.h + '))² + (' + s.k + '). Vertex (' + s.h + ', ' + s.k + '). ' +
            (roots.length ? roots.length === 1 ? 'One repeated real root: ' + numberText(roots[0]) + '.' :
              'Two real roots: ' + roots.map(numberText).join(', ') + '.' : 'No real roots.'),
          note: 'Setting y = 0 gives (x − h)² = −k/a. A positive right side gives two real roots, zero gives a repeated root, and a negative value gives no real roots (complex roots still exist). Root labels are approximate; the curve is clipped to the graph window.',
          legend: [{ label: 'Blue: parabola', color: colors.blue }, { label: 'Coral: vertex', color: colors.coral },
            { label: 'Gold: real roots', color: colors.gold }], sources: [] };
      },
    },
    'math.3.linear': {
      title: 'Keep both sides equal',
      instructions: 'Choose an equation ax + b = c. Move through the same operation on both sides to isolate x.',
      initial: { a: 2, b: 3, c: 9, step: 0 },
      controls: [{ key: 'a', label: 'Coefficient a', min: 1, max: 6, step: 1 },
        { key: 'b', label: 'Constant b', min: -6, max: 6, step: 1 },
        { key: 'c', label: 'Right side c', min: -12, max: 12, step: 1 },
        { key: 'step', label: 'Solution step', min: 0, max: 2, step: 1 }],
      calculate(s) {
        const difference = s.c - s.b, solution = difference / s.a;
        const left = s.step === 0 ? s.a + 'x + (' + s.b + ')' : s.step === 1 ? s.a + 'x' : 'x';
        const right = s.step < 2 ? String(s.step === 0 ? s.c : difference) : difference + '/' + s.a;
        return { data: { difference, solution, left, right },
          readout: left + ' = ' + right + '. Unique solution x = ' + difference + '/' + s.a +
            ' (approximately ' + numberText(solution) + ').',
          note: 'Subtract b from BOTH sides, then divide BOTH sides by nonzero a. Each step preserves the solution. This activity restricts a to positive values; fractional solutions are retained exactly as a quotient.',
          legend: [{ label: 'Teal boxes: equal expressions', color: colors.teal }], sources: [] };
      },
    },
    'math.3.slope': {
      title: 'Rise, run and intercept',
      instructions: 'Change rise, run and the y-intercept. Compare the two marked points: slope is rise divided by run.',
      initial: { rise: 2, run: 3, intercept: 1 },
      controls: [{ key: 'rise', label: 'Rise', min: -4, max: 4, step: 1 },
        { key: 'run', label: 'Run', min: 1, max: 4, step: 1 },
        { key: 'intercept', label: 'Y-intercept', min: -3, max: 3, step: 1 }],
      calculate(s) {
        const slope = s.rise / s.run;
        return { data: { slope, x1: 0, y1: s.intercept, x2: s.run, y2: s.intercept + s.rise },
          readout: 'From (0, ' + s.intercept + ') to (' + s.run + ', ' + (s.intercept + s.rise) +
            '): slope = ' + s.rise + '/' + s.run + '. y = (' + s.rise + '/' + s.run + ')x + (' + s.intercept + ').',
          note: 'Moving the intercept translates the line without changing its slope. A negative rise slopes downward; zero rise is horizontal. Run is positive here: vertical lines have undefined slope and are outside this activity.',
          legend: [{ label: 'Blue: line', color: colors.blue }, { label: 'Gold: run', color: colors.gold },
            { label: 'Coral: rise', color: colors.coral }], sources: [] };
      },
    },
    'math.2.primes': {
      title: 'Which numbers divide exactly?',
      instructions: 'Choose a number and test a divisor. Inspect all its factors, then decide whether it is prime.',
      initial: { number: 24, divisor: 6 },
      controls: [{ key: 'number', label: 'Number', min: 1, max: 60, step: 1 },
        { key: 'divisor', label: 'Test divisor', min: 1, max: 60, step: 1 }],
      calculate(state) {
        const factors = Array.from({ length: state.number }, (_, i) => i + 1).filter(n => state.number % n === 0);
        const quotient = Math.floor(state.number / state.divisor), remainder = state.number % state.divisor;
        const classification = state.number === 1 ? 'neither prime nor composite' : factors.length === 2 ? 'prime' : 'composite';
        return { data: { factors, quotient, remainder, classification },
          readout: state.number + ' is ' + classification + '. Factors: ' + factors.join(', ') + '. ' +
            state.number + ' ÷ ' + state.divisor + ' gives ' + quotient + ' remainder ' + remainder + '.',
          note: 'A positive factor divides without a remainder. A prime has exactly two positive factors: 1 and itself. One has only one positive factor, so it is not prime. The selected divisor is a factor only when the remainder is zero.',
          legend: [{ label: 'Filled: factor', color: colors.teal }, { label: 'Gold border: divisor being tested', color: colors.gold }], sources: [] };
      },
    },
    'math.2.ratio': {
      title: 'Scale both parts together',
      instructions: 'Set scoops of ingredients A and B in one batch. Scale the number of batches; keep each batch in the same ratio.',
      initial: { a: 2, b: 3, scale: 3 },
      controls: [{ key: 'a', label: 'Scoops of A per batch', min: 1, max: 5, step: 1 },
        { key: 'b', label: 'Scoops of B per batch', min: 1, max: 5, step: 1 },
        { key: 'scale', label: 'Number of batches', min: 1, max: 6, step: 1 }],
      calculate(state) {
        const a = state.a * state.scale, b = state.b * state.scale;
        return { data: { a, b, total: a + b, fractionA: state.a / (state.a + state.b) },
          readout: 'One batch uses ' + state.a + ' scoops A and ' + state.b + ' scoops B. ' + state.scale +
            ' batches use ' + a + ' and ' + b + ' scoops. Ratio ' + state.a + ':' + state.b + ' = ' + a + ':' + b + '.',
          note: 'Every scoop has the same volume. Multiply both parts by the same scale factor to preserve the ratio. A:B compares the two parts; A/(A+B) compares A to the whole. Adding the same number to both parts generally does not preserve the ratio.',
          legend: [{ label: 'Ingredient A', color: colors.blue }, { label: 'Ingredient B', color: colors.teal }], sources: [] };
      },
    },
    'math.2.exponents': {
      title: 'One multiplication at each step',
      instructions: 'Change the base and exponent. Follow the chain from 1, multiplying by the base once per step.',
      initial: { base: 2, exponent: 3 },
      controls: [{ key: 'base', label: 'Positive base', min: 1, max: 6, step: 1 },
        { key: 'exponent', label: 'Exponent', min: 0, max: 5, step: 1 }],
      calculate(state) {
        const powers = Array.from({ length: state.exponent + 1 }, (_, i) => state.base ** i);
        const product = state.exponent ? Array(state.exponent).fill(state.base).join(' × ') : 'Empty product = 1';
        return { data: { powers, result: state.base ** state.exponent, product },
          readout: state.base + '^' + state.exponent + ' = ' + state.base ** state.exponent + '. ' + product + '.',
          note: 'The exponent counts factors, not an amount to multiply the base by. Starting from 1, multiply by the base once per step. With zero steps the value stays 1. This example uses positive bases; it does not define 0^0.',
          legend: [{ label: 'Successive product', color: colors.teal }], sources: [] };
      },
    },
    'math.2.data': {
      title: 'Move a value: mean versus median',
      instructions: 'Change five observations. Compare their average with the middle value after sorting.',
      initial: { a: 3, b: 4, c: 5, d: 6, e: 18 },
      controls: ['a', 'b', 'c', 'd', 'e'].map(key => ({ key, label: 'Observation ' + key.toUpperCase(), min: 0, max: 20, step: 1 })),
      calculate(state) {
        const values = ['a', 'b', 'c', 'd', 'e'].map(key => state[key]);
        const sorted = [...values].sort((a, b) => a - b), total = values.reduce((sum, value) => sum + value, 0);
        const mean = total / 5, median = sorted[2];
        return { data: { values, sorted, total, mean, median },
          readout: 'Sorted: ' + sorted.join(', ') + '. Mean = ' + total + ' ÷ 5 = ' + numberText(mean) +
            '. Median = ' + median + ', the third value after sorting.',
          note: 'Every observation contributes to the mean. The median depends on order, so moving an extreme value farther away can change the mean without changing the median. Neither summary describes all the variation. The chart scale stays fixed from 0 to 20.',
          legend: [{ label: 'Observation', color: colors.teal }, { label: 'Mean line', color: colors.blue },
            { label: 'Dashed median line', color: colors.coral }], sources: [] };
      },
    },
    'math.2.prealgebra': {
      title: 'Substitute, multiply, then add',
      instructions: 'Choose x and the constants a and b. Follow the calculation y = ax + b through the function machine.',
      initial: { x: 3, a: 2, b: 1 },
      controls: [{ key: 'x', label: 'Input x', min: -5, max: 5, step: 1 },
        { key: 'a', label: 'Multiplier a', min: -3, max: 3, step: 1 },
        { key: 'b', label: 'Add b', min: -5, max: 5, step: 1 }],
      calculate(state) {
        const product = state.a * state.x, result = product + state.b;
        return { data: { product, result }, readout: 'For x = ' + state.x + ', a = ' + state.a + ', b = ' + state.b +
          ': ax = (' + state.a + ') × (' + state.x + ') = ' + product + '. Then ' + product + ' + (' + state.b + ') = ' + result + '.',
          note: 'A variable stands for a value. Substitute x consistently, multiply by a, then add b. Here we evaluate a rule for a chosen input; we are not solving an equation for an unknown input. Negative values and zero follow the same rule.',
          legend: [{ label: 'Input and intermediate operations', color: colors.blue }, { label: 'Output', color: colors.teal }], sources: [] };
      },
    },
    'math.2.decimals': {
      title: 'Add hundredths, regroup a whole',
      instructions: 'Change two amounts in hundredths. Follow their coloured cells into the sum; a full grid is one whole.',
      initial: { a: 37, b: 48 },
      controls: [{ key: 'a', label: 'First amount', min: 0, max: 99, step: 1, unit: ' hundredths' },
        { key: 'b', label: 'Second amount', min: 0, max: 99, step: 1, unit: ' hundredths' }],
      calculate(state) {
        const total = state.a + state.b;
        const carryTenths = Math.floor((state.a % 10 + state.b % 10) / 10);
        const carryWhole = Math.floor((Math.floor(state.a / 10) + Math.floor(state.b / 10) + carryTenths) / 10);
        const display = value => Math.floor(value / 100) + '.' + String(value % 100).padStart(2, '0');
        return { data: { total, carryTenths, carryWhole, a: display(state.a), b: display(state.b), sum: display(total) },
          readout: display(state.a) + ' + ' + display(state.b) + ' = ' + display(total) + '. ' + total +
            ' hundredths make ' + Math.floor(total / 100) + ' whole and ' + total % 100 + ' hundredths. ' +
            (carryTenths ? 'Ten hundredths regroup as one tenth. ' : '') + (carryWhole ? 'Ten tenths regroup as one whole.' : ''),
          note: 'Each cell is 0.01; each row is 0.10; each full grid is 1.00. The colours preserve the two addends. Align decimal places when adding: hundredths with hundredths and tenths with tenths.',
          legend: [{ label: 'First addend', color: colors.teal }, { label: 'Second addend', color: colors.gold }], sources: [] };
      },
    },
    'math.2.order-ops': {
      title: 'Grouping changes the calculation',
      instructions: 'Change the numbers and switch parentheses on or off. Follow the tree from the inner operation to the final answer.',
      initial: { a: 2, b: 3, c: 4, grouped: false },
      controls: [{ key: 'a', label: 'First number a', min: 0, max: 9, step: 1 },
        { key: 'b', label: 'Second number b', min: 0, max: 9, step: 1 },
        { key: 'c', label: 'Third number c', min: 1, max: 9, step: 1 },
        { key: 'grouped', label: 'Group a + b in parentheses', type: 'toggle' }],
      calculate(state) {
        const inner = state.grouped ? state.a + state.b : state.b * state.c;
        const result = state.grouped ? inner * state.c : state.a + inner;
        const expression = state.grouped ? '(' + state.a + ' + ' + state.b + ') × ' + state.c : state.a + ' + ' + state.b + ' × ' + state.c;
        const first = state.grouped ? state.a + ' + ' + state.b + ' = ' + inner : state.b + ' × ' + state.c + ' = ' + inner;
        return { data: { inner, result, expression, first }, readout: expression + ' = ' + result + '. First: ' + first +
          '. Then ' + (state.grouped ? inner + ' × ' + state.c : state.a + ' + ' + inner) + ' = ' + result + '.',
          note: 'Without parentheses, multiplication binds more tightly than addition. Parentheses change which operation is inside the other. This tree demonstrates that rule for a + b × c, not every possible expression.',
          legend: [{ label: 'Inner operation: calculate first', color: colors.teal }], sources: [] };
      },
    },
    'math.2.percent': {
      title: 'Percent means out of one hundred',
      instructions: 'Change the percent and the whole amount. Compare the hundred-grid, decimal and resulting part of the whole.',
      initial: { percent: 25, whole: 80 },
      controls: [{ key: 'percent', label: 'Percent', min: 0, max: 100, step: 1 },
        { key: 'whole', label: 'Whole amount', min: 0, max: 200, step: 10 }],
      calculate(state) {
        const decimal = state.percent / 100, amount = state.whole * state.percent / 100;
        let a = state.percent, b = 100;
        while (b) { const remainder = a % b; a = b; b = remainder; }
        const numerator = state.percent / a, denominator = 100 / a;
        return { data: { decimal, amount, numerator, denominator },
          readout: state.percent + '% = ' + state.percent + '/100 = ' + numerator + '/' + denominator +
            ' = ' + decimal.toFixed(2) + '. ' + state.percent + '% of ' + state.whole + ' is ' + numberText(amount) + '.',
          note: 'The grid always has one hundred equal cells. Changing the whole changes the amount represented by each cell, not the percentage shaded. Multiply the whole by percent ÷ 100.',
          legend: [{ label: 'Selected percent', color: colors.teal }], sources: [] };
      },
    },
    'math.2.coordinates': {
      title: 'Across first, then up or down',
      instructions: 'Change x and y. Follow the dashed path from the origin to P; keep the order of the coordinates.',
      initial: { x: 3, y: 2 },
      controls: [{ key: 'x', label: 'Horizontal coordinate x', min: -5, max: 5, step: 1 },
        { key: 'y', label: 'Vertical coordinate y', min: -5, max: 5, step: 1 }],
      calculate(state) {
        const location = state.x === 0 && state.y === 0 ? 'at the origin' : state.x === 0 ? 'on the y-axis' :
          state.y === 0 ? 'on the x-axis' : 'in quadrant ' + (state.x > 0 ? state.y > 0 ? 'I' : 'IV' : state.y > 0 ? 'II' : 'III');
        return { data: { location }, readout: 'P = (' + state.x + ', ' + state.y + '), ' + location + '. From the origin, move ' +
          Math.abs(state.x) + (state.x < 0 ? ' left' : ' right') + ', then ' + Math.abs(state.y) + (state.y < 0 ? ' down.' : ' up.'),
          note: 'The ordered pair is (x, y): horizontal first, vertical second. Negative x is left; negative y is down. Points on an axis are not inside a quadrant. The dashed path explains coordinates, not the straight-line distance.',
          legend: [{ label: 'Horizontal step', color: colors.blue }, { label: 'Vertical step / point P', color: colors.teal }], sources: [] };
      },
    },
    'math.1.measurement': {
      title: 'Read the distance, not the end mark',
      instructions: 'Move the object along the ruler without changing its length, then change the length. Subtract the start mark from the end mark.',
      initial: { start: 2, length: 5 },
      controls: [{ key: 'start', label: 'Start mark (cm)', min: 0, max: 4, step: 1 },
        { key: 'length', label: 'Object length (cm)', min: 1, max: 8, step: 1 }],
      calculate(state) {
        const end = state.start + state.length;
        return { data: { end, millimetres: state.length * 10 },
          readout: 'Start ' + state.start + ' cm, end ' + end + ' cm. Length = ' + end + ' − ' + state.start +
            ' = ' + state.length + ' cm = ' + state.length * 10 + ' mm.',
          note: 'A measurement counts equal intervals between the endpoints. Moving the object does not change its length. Each centimetre contains ten millimetres. This screen ruler is a diagram, not a physically calibrated ruler.',
          legend: [{ label: 'Object', color: colors.teal }, { label: 'Endpoints', color: colors.coral }], sources: [] };
      },
    },
    'math.1.time': {
      title: 'A clock and a calendar',
      instructions: 'Change the hour and minute. Watch both clock hands move; choose a day on the September 2026 calendar.',
      initial: { hour: 9, minute: 30, day: 15 },
      controls: [{ key: 'hour', label: 'Hour (24-hour time)', min: 0, max: 23, step: 1 },
        { key: 'minute', label: 'Minute', min: 0, max: 55, step: 5 },
        { key: 'day', label: 'Day in September 2026', min: 1, max: 30, step: 1 }],
      calculate(state) {
        const hourAngle = (state.hour % 12) * 30 + state.minute / 2, minuteAngle = state.minute * 6;
        const weekdayIndex = (state.day + 1) % 7;
        const weekday = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][weekdayIndex];
        const digital = String(state.hour).padStart(2, '0') + ':' + String(state.minute).padStart(2, '0');
        return { data: { hourAngle, minuteAngle, weekdayIndex, weekday, digital },
          readout: digital + ', or ' + (state.hour % 12 || 12) + ':' + String(state.minute).padStart(2, '0') +
            (state.hour < 12 ? ' am' : ' pm') + ', on ' + weekday + ', ' + state.day + ' September 2026.',
          note: 'The long hand counts minutes; one full turn is 60 minutes. The short hand moves gradually between hours. An analogue clock alone does not distinguish am from pm. This fixed example month starts on Tuesday and has 30 days.',
          legend: [{ label: 'Short hour hand', color: colors.blue }, { label: 'Long minute hand', color: colors.teal }], sources: [] };
      },
    },
    'math.1.fractions-intro': {
      title: 'Quarters and halves of the same whole',
      instructions: 'Shade quarters. Compare the same shaded amount on a whole marked in halves.',
      initial: { quarters: 2 },
      controls: [{ key: 'quarters', label: 'Quarters shaded', min: 0, max: 4, step: 1 }],
      calculate(state) {
        const value = state.quarters / 4, wholeHalves = state.quarters % 2 === 0;
        const comparison = wholeHalves ? state.quarters + '/4 = ' + state.quarters / 2 + '/2' :
          state.quarters === 1 ? 'One quarter is less than one half.' : 'Three quarters is between one half and one whole.';
        return { data: { value, wholeHalves, comparison },
          readout: state.quarters + ' of four equal parts are shaded. ' + comparison +
            (state.quarters === 4 ? ' Four quarters make one whole.' : ''),
          note: 'Both bars represent the same-sized whole. The shaded area stays the same when partition lines change. Two quarters equal one half; a piece must be an equal share to be called a quarter.',
          legend: [{ label: 'Shaded share', color: colors.teal }], sources: [] };
      },
    },
    'math.1.multiplication': {
      title: 'Rows times columns',
      instructions: 'Change the rows and counters in each row. Count equal groups, then compare the product.',
      initial: { rows: 3, columns: 4 },
      controls: [{ key: 'rows', label: 'Rows', min: 0, max: 12, step: 1 },
        { key: 'columns', label: 'Counters per row', min: 0, max: 12, step: 1 }],
      calculate(state) {
        const product = state.rows * state.columns;
        return { data: { product }, readout: state.rows + ' rows of ' + state.columns + ' counters: ' +
          state.rows + ' × ' + state.columns + ' = ' + product + '. Turning the array gives ' + state.columns +
          ' × ' + state.rows + ', also ' + product + '.',
          note: 'Multiplication counts equal groups. Every row has the same number of counters. If either factor is zero there are no counters.',
          legend: [{ label: 'One counter', color: colors.teal }], sources: [] };
      },
    },
    'math.1.division': {
      title: 'Share equally, count the remainder',
      instructions: 'Choose a total and a number of groups. Share whole counters equally and inspect any left over.',
      initial: { total: 17, groups: 4 },
      controls: [{ key: 'total', label: 'Total counters', min: 0, max: 36, step: 1 },
        { key: 'groups', label: 'Equal groups', min: 1, max: 6, step: 1 }],
      calculate(state) {
        const quotient = Math.floor(state.total / state.groups), remainder = state.total % state.groups;
        return { data: { quotient, remainder }, readout: state.total + ' ÷ ' + state.groups + ' = ' + quotient +
          ' per group, remainder ' + remainder + '. Check: ' + state.groups + ' × ' + quotient + ' + ' + remainder + ' = ' + state.total + '.',
          note: 'These counters stay whole. Share equally until fewer counters than groups remain. A remainder is not secretly given to one group; fractions would be a different way to share. Dividing by zero is not defined, so at least one group is required.',
          legend: [{ label: 'Shared counter', color: colors.teal }, { label: 'Left over', color: colors.coral }], sources: [] };
      },
    },
    'math.1.subtraction': {
      title: 'Take away, see what stays',
      instructions: 'Choose how many counters stay and how many are removed. Read the subtraction from the whole group.',
      initial: { stay: 6, removed: 4 },
      controls: [{ key: 'stay', label: 'Counters that stay', min: 0, max: 10, step: 1 },
        { key: 'removed', label: 'Counters removed', min: 0, max: 10, step: 1 }],
      calculate(state) {
        const start = state.stay + state.removed;
        return { data: { start, result: state.stay },
          readout: start + ' − ' + state.removed + ' = ' + state.stay + '. Start with ' + start +
            ' counters, remove ' + state.removed + ', and ' + state.stay + ' remain. Check: ' +
            state.stay + ' + ' + state.removed + ' = ' + start + '.',
          note: 'The crossed counters were part of the starting group. Count only the uncrossed counters for the answer. This example keeps the result nonnegative.',
          legend: [{ label: 'Stays', color: colors.teal }, { label: 'Crossed: removed', color: colors.coral }], sources: [] };
      },
    },
    'math.1.place-value': {
      title: 'Build hundreds, tens and ones',
      instructions: 'Change each digit. Compare a hundred square, a ten rod and a single unit; read their contributions to the number.',
      initial: { hundreds: 2, tens: 4, ones: 7 },
      controls: ['hundreds', 'tens', 'ones'].map(key => ({ key, label: key[0].toUpperCase() + key.slice(1), min: 0, max: 9, step: 1 })),
      calculate(state) {
        const parts = [state.hundreds * 100, state.tens * 10, state.ones];
        const number = parts.reduce((sum, part) => sum + part, 0);
        return { data: { parts, number }, readout: state.hundreds + ' hundreds, ' + state.tens + ' tens and ' + state.ones +
          ' ones: ' + parts.join(' + ') + ' = ' + number + '.',
          note: 'One hundred contains ten tens; one ten contains ten ones. The same digit has a different value in each position. A zero holds an empty place. Groups are drawn at different scales to keep them visible; compare unit counts, not their screen area.',
          legend: [{ label: 'Hundred: 10 × 10 units', color: colors.blue },
            { label: 'Ten: 10 units', color: colors.teal }, { label: 'One unit', color: colors.gold }], sources: [] };
      },
    },
    'math.0.compare': {
      title: 'Match one to one',
      instructions: 'Change the two rows. Match one counter in the top row to one below; look for counters left over.',
      initial: { top: 6, bottom: 4 },
      controls: [{ key: 'top', label: 'Top row', min: 0, max: 10, step: 1 },
        { key: 'bottom', label: 'Bottom row', min: 0, max: 10, step: 1 }],
      calculate(state) {
        const difference = Math.abs(state.top - state.bottom), matched = Math.min(state.top, state.bottom);
        const relation = state.top === state.bottom ? '=' : state.top > state.bottom ? '>' : '<';
        return { data: { difference, matched, relation },
          readout: state.top + ' ' + relation + ' ' + state.bottom + '. ' + matched + ' pairs match. ' +
            (difference ? difference + ' counters are left over in the ' + (state.top > state.bottom ? 'top' : 'bottom') + ' row.' : 'Neither row has counters left over; the quantities are equal.'),
          note: 'We compare how many counters there are, not how much space they occupy. Every counter counts as one.',
          legend: [{ label: 'Top row', color: colors.blue }, { label: 'Bottom row', color: colors.teal }], sources: [] };
      },
    },
    'math.0.numbers20': {
      title: 'Two ten-frames',
      instructions: 'Change the number. Fill one frame of ten, then the next; find the same number on the number line.',
      initial: { number: 14 },
      controls: [{ key: 'number', label: 'Number', min: 0, max: 20, step: 1 }],
      calculate(state) {
        const tens = Math.floor(state.number / 10), ones = state.number % 10;
        return { data: { tens, ones, first: Math.min(10, state.number), second: Math.max(0, state.number - 10) },
          readout: state.number + ' = ' + tens + ' full tens and ' + ones + ' ones. ' +
            (state.number < 20 ? 'One more is ' + (state.number + 1) + '. ' : '') +
            (state.number > 0 ? 'One less is ' + (state.number - 1) + '.' : 'Zero means no counters.'),
          note: 'Each frame has ten spaces, arranged as two rows of five. Filled spaces count; empty spaces do not. The number line increases by one at every tick.',
          legend: [{ label: 'Filled space: one counter', color: colors.teal }], sources: [] };
      },
    },
    'math.0.patterns': {
      title: 'Repeat a rule, or grow',
      instructions: 'Choose a rule and reveal more steps. Predict the next step before moving the slider.',
      initial: { rule: 'ab', steps: 4 },
      controls: [{ key: 'rule', label: 'Pattern rule', options: [
        { value: 'ab', label: 'Alternate: circle, square' }, { value: 'abb', label: 'Repeat three: circle, square, square' },
        { value: 'grow', label: 'Grow: add one block' }] },
      { key: 'steps', label: 'Steps shown', min: 1, max: 6, step: 1 }],
      calculate(state) {
        const unit = state.rule === 'ab' ? ['circle', 'square'] : ['circle', 'square', 'square'];
        const at = index => state.rule === 'grow' ? index + 1 : unit[index % unit.length];
        const terms = Array.from({ length: state.steps }, (_, i) => at(i)), next = at(state.steps);
        return { data: { terms, next, unit: state.rule === 'grow' ? null : unit },
          readout: 'Shown: ' + terms.join(', ') + '. Next: ' + next + (state.rule === 'grow' ? ' blocks.' : '.') ,
          note: state.rule === 'grow' ? 'This rule adds one block at each step: 1, 2, 3, and so on. It grows rather than repeating a fixed group.' :
            'The repeating unit is ' + unit.join(', ') + '. A short sequence can fit many rules; here we follow the rule you selected.',
          legend: [{ label: 'Circle / blocks', color: colors.teal }, { label: 'Square', color: colors.blue }], sources: [] };
      },
    },
    'cs.1.binary': {
      title: 'Four bits, sixteen numbers',
      instructions: 'Switch each bit between zero and one. Follow its place value into the total.',
      initial: { bit8: true, bit4: true, bit2: false, bit1: true },
      controls: [8, 4, 2, 1].map(weight => ({ key: 'bit' + weight,
        label: weight + ' place', type: 'toggle', group: 'Binary digits' })),
      calculate(state) {
        const places = [8, 4, 2, 1].map(weight => ({ weight, bit: Number(state['bit' + weight]),
          contribution: state['bit' + weight] ? weight : 0 }));
        const decimal = places.reduce((sum, place) => sum + place.contribution, 0);
        const binary = places.map(place => place.bit).join('');
        const sum = places.map(place => place.contribution).join(' + ');
        return { data: { places, decimal, binary, sum },
          readout: binary + ' in base two = ' + sum + ' = ' + decimal + ' in base ten.',
          note: 'This is an unsigned four-bit number, from 0 to 15. A 1 includes its place value; a 0 contributes nothing. Each place to the left is worth twice as much. Leading zeros do not change the value.',
          legend: [{ label: 'Filled: bit 1, value included', color: colors.teal },
            { label: 'Outline: bit 0, value excluded', color: colors.ink }], sources: [] };
      },
    },
    'hist.3.economics-intro': {
      title: 'A price, two quantities',
      instructions: 'Move the posted price to compare how much buyers want and sellers offer. Shift demand, then find the new crossing.',
      initial: { price: 20, demandShift: 0 },
      controls: [
        { key: 'price', label: 'Posted price P', min: 0, max: 40, step: 1, unit: ' credits' },
        { key: 'demandShift', label: 'Demand shift Δ', min: -20, max: 20, step: 4, unit: ' units' },
      ],
      calculate(state) {
        // Chosen teaching schedules, in units per day at P credits per unit.
        // The control domain keeps both quantities nonnegative without clipping.
        const demandIntercept = 100 + state.demandShift;
        const demanded = demandIntercept - 2 * state.price;
        const supplied = 20 + 2 * state.price;
        const shortage = Math.max(0, demanded - supplied);
        const surplus = Math.max(0, supplied - demanded);
        const equilibrium = { price: (demandIntercept - 20) / 4,
          quantity: (demandIntercept + 20) / 2 };
        const balance = shortage ? 'shortage' : surplus ? 'surplus' : 'equilibrium';
        const curves = {
          demand: [0, 40].map(price => ({ price, quantity: demandIntercept - 2 * price })),
          supply: [0, 40].map(price => ({ price, quantity: 20 + 2 * price })),
          baselineDemand: [0, 40].map(price => ({ price, quantity: 100 - 2 * price })),
        };
        const gap = shortage ? 'Shortage: buyers want ' + shortage + ' more units than sellers offer.' :
          surplus ? 'Surplus: sellers offer ' + surplus + ' more units than buyers want.' :
            'The quantities match: this posted price is the equilibrium price.';
        return {
          data: { demandIntercept, demanded, supplied, shortage, surplus, balance, equilibrium, curves,
            equations: ['Qd = 100 + Δ − 2P', 'Qs = 20 + 2P', 'P* = 20 + Δ/4', 'Q* = 60 + Δ/2'] },
          readout: 'At P = ' + state.price + ' credits, quantity demanded is ' + demanded +
            ' and quantity supplied is ' + supplied + ' units per day. ' + gap +
            ' The curves cross at P* = ' + numberText(equilibrium.price) + ' and Q* = ' + numberText(equilibrium.quantity) + '.',
          note: 'A toy competitive market for one good, holding other influences fixed. Qd = 100 + Δ − 2P; Qs = 20 + 2P. ' +
            'Price changes move along each curve; Δ shifts demand at every price. These schedules show intended quantities, not actual sales or a forecast of price adjustment.',
          legend: [
            { label: 'Demand Qd', color: colors.blue }, { label: 'Supply Qs', color: colors.teal },
            { label: 'Equilibrium E', color: colors.gold },
            ...(state.demandShift ? [{ label: 'Dashed curve: demand at Δ = 0', color: colors.blue }] : []),
          ],
          sources: [{ label: 'OpenStax: demand, supply, and equilibrium',
            url: 'https://openstax.org/books/principles-economics-3e/pages/3-1-demand-supply-and-equilibrium-in-markets-for-goods-and-services' }],
        };
      },
    },
    'lang.4.linguistics': {
      title: 'One sentence, two structures',
      instructions: 'Keep the words fixed. Attach “with the telescope” to the seeing event or to the person, and follow the highlighted branch.',
      initial: { attachment: 'verb' },
      controls: [{ key: 'attachment', label: 'Attach the prepositional phrase to', options: [
        { value: 'verb', label: 'Verb phrase: how I saw' },
        { value: 'noun', label: 'Noun phrase: which person' },
      ] }],
      calculate(state) {
        const subject = phrase('NP', 'I');
        const verb = phrase('V', 'saw');
        const person = phrase('NP', phrase('Det', 'the'), phrase('N', 'person'));
        const pp = phrase('PP', phrase('P', 'with'),
          phrase('NP', phrase('Det', 'the'), phrase('N', 'telescope')));
        const verbAttachment = state.attachment === 'verb';
        const tree = phrase('S', subject, verbAttachment
          ? phrase('VP', phrase('VP', verb, person), pp)
          : phrase('VP', verb, phrase('NP', person, pp)));
        const interpretation = verbAttachment
          ? 'I used the telescope to see the person.'
          : 'I saw the person who had the telescope.';
        const attachmentTarget = verbAttachment ? 'VP' : 'NP';
        return {
          data: { tokens: leaves(tree), tree, parse: bracket(tree), interpretation, attachmentTarget,
            sentence: 'I saw the person with the telescope',
            attachmentMeaning: verbAttachment ? 'the seeing event' : 'the person' },
          readout: '“With the telescope” attaches to ' + attachmentTarget + ', the ' +
            (verbAttachment ? 'verb phrase. ' : 'noun phrase. ') + interpretation +
            ' The seven words and their order stay the same.',
          note: 'This is a simplified constituent analysis of two possible readings. S = sentence; NP = noun phrase; VP = verb phrase; ' +
            'PP = prepositional phrase; V = verb; Det = determiner; N = noun; P = preposition. Triangles in the diagram abbreviate subtrees. Context helps choose the intended reading.',
          legend: [{ label: 'Highlighted branch: PP attachment', color: colors.plum }],
          sources: [{ label: 'NLTK Book: sentence structure and PP attachment', url: 'https://www.nltk.org/book/ch08.html' }],
        };
      },
    },
    'mind.5.logic-advanced': {
      title: 'Possible from here',
      instructions: 'Evaluate at w0. Toggle P in each world and choose the arrows leaving w0. Compare “every accessible world” with “at least one.”',
      initial: { p0: false, p1: true, p2: false, edge0: false, edge1: true, edge2: true },
      controls: [
        { key: 'p0', label: 'P at w0 (current)', type: 'toggle', group: 'Truth of P' },
        { key: 'p1', label: 'P at w1', type: 'toggle', group: 'Truth of P' },
        { key: 'p2', label: 'P at w2', type: 'toggle', group: 'Truth of P' },
        { key: 'edge0', label: 'w0 → w0 (self-loop)', type: 'toggle', group: 'Arrows from w0' },
        { key: 'edge1', label: 'w0 → w1', type: 'toggle', group: 'Arrows from w0' },
        { key: 'edge2', label: 'w0 → w2', type: 'toggle', group: 'Arrows from w0' },
      ],
      calculate(state) {
        const worlds = [0, 1, 2].map(i => ({ id: 'w' + i, truth: state['p' + i],
          current: i === 0, accessible: state['edge' + i] }));
        const accessible = worlds.filter(world => world.accessible);
        const successors = accessible.map(world => world.id);
        const edges = successors.map(to => ({ from: 'w0', to }));
        const witnesses = accessible.filter(world => world.truth).map(world => world.id);
        const counterexamples = accessible.filter(world => !world.truth).map(world => world.id);
        // Standard Kripke semantics: universal quantification over an empty set
        // is true; existential quantification over an empty set is false.
        const boxP = accessible.every(world => world.truth);
        const diamondP = accessible.some(world => world.truth);
        const explanation = !successors.length
          ? 'There are no accessible worlds: □P is vacuously true, and ◇P is false because there is no witness.'
          : (boxP ? 'P holds at every accessible world. ' : '□P has a counterexample at ' + counterexamples.join(', ') + '. ') +
            (diamondP ? '◇P has a witness at ' + witnesses.join(', ') + '.' : 'No accessible world makes P true.');
        return {
          data: { currentWorld: 'w0', worlds, edges, successors, witnesses, counterexamples,
            boxP, diamondP, localP: state.p0,
            equations: ['□P at w0 ⇔ every v with w0Rv satisfies P',
              '◇P at w0 ⇔ some v with w0Rv satisfies P'] },
          readout: 'At w0: P is ' + truthText(state.p0) + ', □P is ' + truthText(boxP) +
            ', and ◇P is ' + truthText(diamondP) + '. Accessible worlds: ' +
            (successors.join(', ') || 'none') + '. ' + explanation,
          note: 'A three-world Kripke model for basic modal logic K. Arrows are directed accessibility relations. ' +
            '□P checks P at every direct successor; ◇P needs at least one direct successor with P. ' +
            'P at w0 affects these modal claims only when the self-loop is present. No reflexivity or symmetry is assumed.',
          legend: [{ label: 'P true', color: colors.teal }, { label: 'P false', color: colors.coral },
            { label: 'Double ring: current world w0', color: colors.ink }],
          sources: [{ label: 'Stanford Encyclopedia of Philosophy: modal logic', url: 'https://plato.stanford.edu/entries/logic-modal/' }],
        };
      },
    },
  };

  // Freeze the public descriptions so callers cannot change later builds.
  Object.values(specs).forEach(spec => {
    spec.controls.forEach(control => {
      if (control.options) {
        control.options.forEach(Object.freeze);
        Object.freeze(control.options);
      }
      Object.freeze(control);
    });
    Object.freeze(spec.controls);
    Object.freeze(spec.initial);
    Object.freeze(spec);
  });
  Object.freeze(specs);
  const supported = Object.freeze(Object.keys(specs));
  const emptyControls = Object.freeze([]);

  function build(id, supplied = {}) {
    if (typeof id !== 'string' || !own(specs, id)) return null;
    const spec = specs[id], state = { ...spec.initial };
    if (!record(supplied)) supplied = {};
    spec.controls.forEach(control => {
      if (!own(supplied, control.key)) return;
      const value = supplied[control.key];
      if (control.type === 'toggle') {
        if (typeof value === 'boolean') state[control.key] = value;
      } else if (control.options) {
        if (control.options.some(option => option.value === value)) state[control.key] = value;
      } else if ((typeof value === 'number' || (typeof value === 'string' && value.trim())) && Number.isFinite(Number(value))) {
        const stepped = control.min + Math.round((Number(value) - control.min) / control.step) * control.step;
        state[control.key] = Math.max(control.min, Math.min(control.max, stepped));
      }
    });
    return { state, ...spec.calculate(state) };
  }

  function element(tag, attrs = {}, text, svg = false) {
    const el = svg ? document.createElementNS(NS, tag) : document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, String(value)));
    if (text != null) el.textContent = text;
    return el;
  }
  const svgElement = (tag, attrs, text) => element(tag, attrs, text, true);
  function label(svg, x, y, text, attrs = {}) {
    const lines = Array.isArray(text) ? text : [text];
    const el = svgElement('text', { x, y, fill: colors.ink, 'font-size': 21,
      'font-family': 'system-ui, sans-serif', 'text-anchor': 'middle', ...attrs });
    lines.forEach((line, i) => el.append(svgElement('tspan', { x, dy: i ? 23 : 0 }, line)));
    svg.append(el);
  }
  function line(svg, x1, y1, x2, y2, attrs = {}) {
    svg.append(svgElement('line', { x1, y1, x2, y2, stroke: colors.ink, 'stroke-width': 2, ...attrs }));
  }

  function drawBeatSubdivision(svg, current) {
    const d = current.data, x = seconds => 42 + seconds * 42;
    label(svg, 210, 36, 'Four beats, split into notes');
    label(svg, 42, 81, 'BEATS', { 'text-anchor': 'start', 'font-size': 18 });
    label(svg, 42, 177, 'NOTES', { 'text-anchor': 'start', 'font-size': 18 });
    for (let second = 0; second <= 8; second++) {
      line(svg, x(second), 94, x(second), 267, { opacity: .13 });
      label(svg, x(second), 290, String(second), { 'font-size': 18 });
    }
    for (const [times, y, color] of [[d.beats, 116, colors.blue], [d.notes, 211, colors.gold]]) {
      line(svg, x(0), y, x(d.duration), y, { stroke: color });
      times.forEach((t, i) => {
        const radius = y === 116 ? 8 : Math.min(4, d.noteSeconds * 42 * .35);
        svg.append(svgElement('circle', { cx: x(t), cy: y, r: radius, fill: color }));
        if (y === 116) label(svg, x(t), y + 30, String(i + 1), { 'font-size': 18 });
      });
    }
    line(svg, x(d.duration), 96, x(d.duration), 243, { 'stroke-dasharray': '5 4' });
    label(svg, 210, 327, 'Elapsed time (seconds)', { 'font-size': 20 });
  }

  function drawEconomics(svg, current) {
    const { state, data } = current;
    const x = quantity => 60 + quantity / 120 * 324;
    const y = price => 276 - price / 40 * 226;
    [0, 20, 40].forEach(price => {
      line(svg, 60, y(price), 384, y(price), { opacity: .14 });
      label(svg, 43, y(price) + 7, String(price), { 'text-anchor': 'end', 'font-size': 20 });
    });
    [0, 60, 120].forEach(quantity => {
      line(svg, x(quantity), 50, x(quantity), 276, { opacity: .1 });
      label(svg, x(quantity), 302, String(quantity), { 'font-size': 20 });
    });
    line(svg, 60, 50, 60, 277);
    line(svg, 59, 276, 385, 276);
    label(svg, 18, 28, 'Price', { 'text-anchor': 'start' });
    label(svg, 222, 333, 'Quantity / day');
    const curve = (points, color, dashed = false) => svg.append(svgElement('polyline', {
      points: points.map(point => x(point.quantity) + ',' + y(point.price)).join(' '),
      fill: 'none', stroke: color, 'stroke-width': dashed ? 2 : 4,
      'stroke-dasharray': dashed ? '6 5' : 'none', opacity: dashed ? .5 : 1,
    }));
    if (state.demandShift) curve(data.curves.baselineDemand, colors.blue, true);
    curve(data.curves.demand, colors.blue);
    curve(data.curves.supply, colors.teal);
    line(svg, 60, y(state.price), 384, y(state.price), { 'stroke-dasharray': '5 5', opacity: .6 });
    if (data.balance !== 'equilibrium') {
      line(svg, x(data.demanded), y(state.price), x(data.supplied), y(state.price), {
        stroke: data.shortage ? colors.coral : colors.plum, 'stroke-width': 13, opacity: .35,
      });
    }
    [[data.demanded, colors.blue], [data.supplied, colors.teal]].forEach(([quantity, color]) => {
      svg.append(svgElement('circle', { cx: x(quantity), cy: y(state.price), r: 6,
        fill: color, stroke: colors.paper, 'stroke-width': 2 }));
    });
    const ex = x(data.equilibrium.quantity), ey = y(data.equilibrium.price);
    svg.append(svgElement('circle', { cx: ex, cy: ey, r: 9, fill: colors.paper,
      stroke: colors.gold, 'stroke-width': 4 }));
    label(svg, ex + 20, ey - 12, 'E', { 'font-weight': 700, 'paint-order': 'stroke',
      stroke: colors.paper, 'stroke-width': 4 });
  }

  function drawBinary(svg, current) {
    label(svg, 210, 32, 'Place value');
    current.data.places.forEach((place, index) => {
      const x = 57 + index * 102;
      label(svg, x, 72, String(place.weight), { 'font-weight': 700 });
      svg.append(svgElement('rect', { x: x - 36, y: 92, width: 72, height: 74,
        rx: 12, fill: place.bit ? colors.teal : colors.paper, stroke: colors.ink, 'stroke-width': 2 }));
      label(svg, x, 140, String(place.bit), { fill: place.bit ? colors.paper : colors.ink,
        'font-size': 32, 'font-weight': 700 });
      line(svg, x, 178, x, 203, { stroke: colors.teal });
      label(svg, x, 237, String(place.contribution), { 'font-size': 26 });
      if (index < 3) label(svg, x + 51, 237, '+');
    });
    label(svg, 210, 296, '= ' + current.data.decimal + ' in base ten', { 'font-size': 25, 'font-weight': 700 });
    label(svg, 210, 332, current.data.binary + ' in base two');
  }

  function drawEarlyMath(svg, current, id) {
    if (id === 'math.0.compare') {
      label(svg, 210, 35, 'Match the counters');
      for (let i = 0; i < current.data.matched; i++) line(svg, 39 + i * 38, 120, 39 + i * 38, 196, { opacity: .35 });
      [[current.state.top, 102, colors.blue], [current.state.bottom, 214, colors.teal]].forEach(([count, y, color]) => {
        for (let i = 0; i < count; i++) svg.append(svgElement('circle', { cx: 39 + i * 38, cy: y, r: 14, fill: color }));
      });
      label(svg, 210, 290, current.state.top + ' ' + current.data.relation + ' ' + current.state.bottom,
        { 'font-size': 34, 'font-weight': 700 });
      label(svg, 210, 331, current.data.difference + ' left over');
    } else if (id === 'math.0.numbers20') {
      label(svg, 210, 33, String(current.state.number), { 'font-size': 30, 'font-weight': 700 });
      for (let i = 0; i < 20; i++) {
        const frame = Math.floor(i / 10), slot = i % 10, x = 110 + slot % 5 * 40, y = 57 + frame * 104 + Math.floor(slot / 5) * 40;
        svg.append(svgElement('rect', { x, y, width: 40, height: 40, fill: 'none', stroke: colors.ink }));
        if (i < current.state.number) svg.append(svgElement('circle', { cx: x + 20, cy: y + 20, r: 13, fill: colors.teal }));
      }
      line(svg, 30, 291, 390, 291);
      for (let i = 0; i <= 20; i++) {
        const x = 30 + i * 18;
        line(svg, x, 284, x, 298);
        if (i % 5 === 0) label(svg, x, 330, String(i), { 'font-size': 18 });
      }
      svg.append(svgElement('circle', { cx: 30 + current.state.number * 18, cy: 291, r: 7, fill: colors.gold }));
    } else {
      label(svg, 210, 34, current.state.rule === 'grow' ? 'Add one block each step' : 'Repeat the chosen unit');
      current.data.terms.forEach((term, i) => {
        const x = 43 + i * 66;
        if (typeof term === 'number') {
          for (let j = 0; j < term; j++) svg.append(svgElement('rect', { x: x - 12, y: 222 - j * 23,
            width: 24, height: 22, fill: colors.teal, stroke: colors.paper }));
        } else if (term === 'circle') svg.append(svgElement('circle', { cx: x, cy: 184, r: 20, fill: colors.teal }));
        else svg.append(svgElement('rect', { x: x - 20, y: 164, width: 40, height: 40, fill: colors.blue }));
        label(svg, x, 274, String(i + 1), { 'font-size': 19 });
      });
      label(svg, 210, 324, 'Next: ' + current.data.next + (current.state.rule === 'grow' ? ' blocks' : ''));
    }
  }

  function drawPlaceAndSubtract(svg, current, id) {
    if (id === 'math.1.subtraction') {
      label(svg, 210, 34, 'Start with ' + current.data.start);
      for (let i = 0; i < current.data.start; i++) {
        const x = 38 + i % 10 * 38, y = 108 + Math.floor(i / 10) * 76;
        const removed = i >= current.state.stay;
        svg.append(svgElement('circle', { cx: x, cy: y, r: 14, fill: removed ? colors.paper : colors.teal,
          stroke: removed ? colors.coral : colors.teal, 'stroke-width': 2 }));
        if (removed) {
          line(svg, x - 16, y - 16, x + 16, y + 16, { stroke: colors.coral, 'stroke-width': 3 });
          line(svg, x + 16, y - 16, x - 16, y + 16, { stroke: colors.coral, 'stroke-width': 3 });
        }
      }
      label(svg, 210, 278, current.data.start + ' − ' + current.state.removed + ' = ' + current.state.stay,
        { 'font-size': 31, 'font-weight': 700 });
      label(svg, 210, 326, current.state.stay + ' stay');
    } else {
      ['Hundreds', 'Tens', 'Ones'].forEach((name, index) => label(svg, 73 + index * 137, 33, name, { 'font-size': 20 }));
      [141, 278].forEach(x => line(svg, x, 49, x, 248, { opacity: .2 }));
      for (let i = 0; i < current.state.hundreds; i++) {
        const x = 20 + i % 3 * 40, y = 68 + Math.floor(i / 3) * 54;
        svg.append(svgElement('rect', { x, y, width: 30, height: 30, fill: colors.blue, 'fill-opacity': .2, stroke: colors.blue }));
        for (let j = 1; j < 10; j++) {
          line(svg, x + j * 3, y, x + j * 3, y + 30, { stroke: colors.blue, 'stroke-width': .6 });
          line(svg, x, y + j * 3, x + 30, y + j * 3, { stroke: colors.blue, 'stroke-width': .6 });
        }
      }
      for (let i = 0; i < current.state.tens; i++) {
        const x = 158 + i % 5 * 23, y = 65 + Math.floor(i / 5) * 88;
        for (let j = 0; j < 10; j++) svg.append(svgElement('rect', { x, y: y + j * 7, width: 7, height: 7,
          fill: colors.teal, stroke: colors.paper, 'stroke-width': .7 }));
      }
      for (let i = 0; i < current.state.ones; i++) svg.append(svgElement('rect', {
        x: 305 + i % 3 * 27, y: 92 + Math.floor(i / 3) * 40, width: 7, height: 7, fill: colors.gold }));
      current.data.parts.forEach((part, index) => label(svg, 73 + index * 137, 275, String(part), { 'font-size': 28 }));
      label(svg, 210, 331, current.data.parts.join(' + ') + ' = ' + current.data.number, { 'font-size': 24 });
    }
  }

  function drawGroups(svg, current, id) {
    if (id === 'math.1.multiplication') {
      label(svg, 210, 30, current.state.rows + ' rows × ' + current.state.columns + ' per row');
      for (let r = 0; r < current.state.rows; r++) for (let c = 0; c < current.state.columns; c++) {
        svg.append(svgElement('circle', { cx: 78 + c * 24, cy: 60 + r * 19, r: 6, fill: colors.teal }));
      }
      label(svg, 210, 327, '= ' + current.data.product, { 'font-size': 30, 'font-weight': 700 });
    } else {
      label(svg, 210, 29, current.state.total + ' counters, ' + current.state.groups + ' groups');
      for (let g = 0; g < current.state.groups; g++) {
        const x = 16 + g % 3 * 136, y = 49 + Math.floor(g / 3) * 105;
        svg.append(svgElement('rect', { x, y, width: 120, height: 94, rx: 9, fill: 'none', stroke: colors.ink }));
        for (let i = 0; i < current.data.quotient; i++) svg.append(svgElement('circle', {
          cx: x + 15 + i % 6 * 18, cy: y + 10 + Math.floor(i / 6) * 11, r: 4, fill: colors.teal }));
        label(svg, x + 60, y + 87, String(current.data.quotient) + ' each', { 'font-size': 15 });
      }
      label(svg, 117, 281, 'Left over:', { 'text-anchor': 'end', 'font-size': 19 });
      for (let i = 0; i < current.data.remainder; i++) svg.append(svgElement('circle', {
        cx: 145 + i * 28, cy: 274, r: 8, fill: colors.coral }));
      if (!current.data.remainder) label(svg, 149, 281, '0');
      label(svg, 210, 331, current.state.groups + ' × ' + current.data.quotient + ' + ' + current.data.remainder + ' = ' + current.state.total);
    }
  }

  function drawMeasureTimeFraction(svg, current, id) {
    if (id === 'math.1.measurement') {
      const x = cm => 30 + cm * 30;
      label(svg, 210, 32, 'Length stays the same when moved');
      svg.append(svgElement('rect', { x: x(current.state.start), y: 95, width: current.state.length * 30,
        height: 38, rx: 5, fill: colors.teal }));
      for (const endpoint of [current.state.start, current.data.end]) line(svg, x(endpoint), 84, x(endpoint), 191, { stroke: colors.coral, 'stroke-dasharray': '4 3' });
      line(svg, 30, 190, 390, 190);
      for (let mm = 0; mm <= 120; mm++) {
        line(svg, 30 + mm * 3, 190, 30 + mm * 3, mm % 10 === 0 ? 215 : 199, { 'stroke-width': mm % 10 === 0 ? 2 : .7 });
        if (mm % 10 === 0) label(svg, 30 + mm * 3, 239, String(mm / 10), { 'font-size': 16 });
      }
      label(svg, 210, 278, current.data.end + ' − ' + current.state.start + ' = ' + current.state.length + ' cm');
      label(svg, 210, 329, current.state.length + ' cm = ' + current.data.millimetres + ' mm');
    } else if (id === 'math.1.time') {
      const cx = 104, cy = 139;
      label(svg, cx, 29, 'Clock'); label(svg, 308, 29, 'September 2026', { 'font-size': 18 });
      svg.append(svgElement('circle', { cx, cy, r: 85, fill: 'none', stroke: colors.ink, 'stroke-width': 2 }));
      for (let n = 1; n <= 12; n++) {
        const a = n * Math.PI / 6;
        label(svg, cx + 67 * Math.sin(a), cy - 67 * Math.cos(a) + 6, String(n), { 'font-size': 17 });
      }
      for (const [angle, length, color, width] of [[current.data.hourAngle, 43, colors.blue, 6], [current.data.minuteAngle, 59, colors.teal, 3]]) {
        const a = angle * Math.PI / 180;
        line(svg, cx, cy, cx + length * Math.sin(a), cy - length * Math.cos(a), { stroke: color, 'stroke-width': width, 'stroke-linecap': 'round' });
      }
      svg.append(svgElement('circle', { cx, cy, r: 5, fill: colors.ink }));
      ['S', 'M', 'T', 'W', 'T', 'F', 'S'].forEach((day, i) => label(svg, 221 + i * 28, 63, day, { 'font-size': 16 }));
      for (let day = 1; day <= 30; day++) {
        const cell = day + 1, x = 221 + cell % 7 * 28, y = 92 + Math.floor(cell / 7) * 29;
        if (day === current.state.day) svg.append(svgElement('rect', { x: x - 12, y: y - 19, width: 24, height: 26, rx: 4, fill: colors.gold, opacity: .35 }));
        label(svg, x, y, String(day), { 'font-size': 16 });
      }
      label(svg, 210, 276, current.data.digital, { 'font-size': 31, 'font-weight': 700 });
      label(svg, 210, 330, current.data.weekday + ', ' + current.state.day + ' Sep 2026', { 'font-size': 20 });
    } else {
      label(svg, 210, 32, 'The same whole, the same shaded share');
      [[4, 72], [2, 177]].forEach(([parts, y]) => {
        svg.append(svgElement('rect', { x: 50, y, width: 320 * current.data.value, height: 58, fill: colors.teal }));
        svg.append(svgElement('rect', { x: 50, y, width: 320, height: 58, fill: 'none', stroke: colors.ink, 'stroke-width': 2 }));
        for (let p = 1; p < parts; p++) line(svg, 50 + p * 320 / parts, y, 50 + p * 320 / parts, y + 58, { stroke: colors.ink, 'stroke-width': 2 });
        label(svg, 210, y + 82, parts === 4 ? current.state.quarters + '/4 shaded' : 'Whole marked in halves');
      });
      label(svg, 210, 315, current.data.wholeHalves ? current.data.comparison :
        current.state.quarters === 1 ? '1/4 < 1/2' : '1/2 < 3/4 < 1', { 'font-size': 26 });
    }
  }

  function drawPercentCoordinates(svg, current, id) {
    if (id === 'math.2.percent') {
      label(svg, 210, 30, current.state.percent + '% of ' + current.state.whole, { 'font-size': 25, 'font-weight': 700 });
      for (let i = 0; i < 100; i++) svg.append(svgElement('rect', { x: 110 + i % 10 * 20,
        y: 49 + Math.floor(i / 10) * 20, width: 20, height: 20,
        fill: i < current.state.percent ? colors.teal : colors.paper, stroke: colors.ink, 'stroke-width': .8 }));
      label(svg, 210, 287, current.state.percent + '/100 = ' + current.data.decimal.toFixed(2));
      label(svg, 210, 333, 'Amount = ' + numberText(current.data.amount), { 'font-size': 25, 'font-weight': 700 });
    } else {
      const x = value => 210 + value * 23, y = value => 170 - value * 23;
      for (let i = -5; i <= 5; i++) {
        line(svg, x(i), 55, x(i), 285, { opacity: i === 0 ? 1 : .14 });
        line(svg, 95, y(i), 325, y(i), { opacity: i === 0 ? 1 : .14 });
        label(svg, x(i), 307, String(i), { 'font-size': 14 });
        label(svg, 79, y(i) + 5, String(i), { 'font-size': 14, 'text-anchor': 'end' });
      }
      label(svg, 350, 177, 'x'); label(svg, 210, 29, 'y');
      line(svg, x(0), y(0), x(current.state.x), y(0), { stroke: colors.blue, 'stroke-width': 4, 'stroke-dasharray': '5 4' });
      line(svg, x(current.state.x), y(0), x(current.state.x), y(current.state.y), { stroke: colors.teal, 'stroke-width': 4, 'stroke-dasharray': '5 4' });
      svg.append(svgElement('circle', { cx: x(current.state.x), cy: y(current.state.y), r: 7,
        fill: colors.teal, stroke: colors.paper, 'stroke-width': 2 }));
      label(svg, 210, 340, 'P = (' + current.state.x + ', ' + current.state.y + ')', { 'font-size': 23, 'font-weight': 700 });
    }
  }

  function drawDecimalOrder(svg, current, id) {
    if (id === 'math.2.decimals') {
      label(svg, 210, 32, current.data.a + ' + ' + current.data.b, { 'font-size': 26, 'font-weight': 700 });
      for (let i = 0; i < 200; i++) {
        const frame = Math.floor(i / 100), cell = i % 100;
        svg.append(svgElement('rect', { x: 42 + frame * 188 + cell % 10 * 15, y: 86 + Math.floor(cell / 10) * 15,
          width: 15, height: 15, fill: i < current.state.a ? colors.teal : i < current.data.total ? colors.gold : colors.paper,
          stroke: colors.ink, 'stroke-width': .6 }));
      }
      label(svg, 117, 263, '100 hundredths', { 'font-size': 17 });
      label(svg, 305, 263, '100 hundredths', { 'font-size': 17 });
      label(svg, 210, 319, '= ' + current.data.sum, { 'font-size': 32, 'font-weight': 700 });
    } else {
      const grouped = current.state.grouped, innerX = grouped ? 112 : 308;
      label(svg, 210, 29, current.data.expression, { 'font-size': 25, 'font-weight': 700 });
      line(svg, 210, 96, 112, 157); line(svg, 210, 96, 308, 157);
      line(svg, innerX, 184, innerX - 48, 224, { stroke: colors.teal });
      line(svg, innerX, 184, innerX + 48, 224, { stroke: colors.teal });
      label(svg, 210, 88, grouped ? '×' : '+', { 'font-size': 31 });
      svg.append(svgElement('rect', { x: innerX - 30, y: 144, width: 60, height: 42, rx: 9, fill: colors.teal, opacity: .18 }));
      label(svg, innerX, 173, grouped ? '+' : '×', { 'font-size': 29 });
      label(svg, grouped ? 308 : 112, 173, String(grouped ? current.state.c : current.state.a), { 'font-size': 25 });
      label(svg, innerX - 48, 246, String(grouped ? current.state.a : current.state.b));
      label(svg, innerX + 48, 246, String(grouped ? current.state.b : current.state.c));
      label(svg, 210, 288, 'First: ' + current.data.first, { 'font-size': 20 });
      label(svg, 210, 333, 'Result: ' + current.data.result, { 'font-size': 26, 'font-weight': 700 });
    }
  }

  function drawAdvanced(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'math.5.frontier') {
      label(svg, 210, 27, 'n² + n + 41', { 'font-size': 25 });
      label(svg, 210, 53, 'Each cell is one integer n, starting at 0', { 'font-size': 16 });
      for (let n = 0; n <= 60; n++) {
        const x = 27 + n % 10 * 37, y = 72 + Math.floor(n / 10) * 27;
        const row = d.checked[n];
        svg.append(svgElement('rect', { x, y, width: 32, height: 23, rx: 3,
          fill: row ? row.prime ? colors.teal : colors.coral : colors.paper,
          stroke: n === s.selected ? colors.gold : colors.ink, 'stroke-width': n === s.selected ? 3 : .5 }));
        label(svg, x + 16, y + 16, String(n), { 'font-size': 12, fill: row ? colors.paper : colors.ink });
      }
      const v = d.selected;
      label(svg, 210, 294, 'n = ' + s.selected + ': ' + v.value + (v.prime ? ' is prime' : ' = ' + v.divisor + ' × ' + v.value / v.divisor), { 'font-size': 20 });
      label(svg, 210, 329, d.counterexamples.length ? 'Counterexample found: conjecture false' : 'Finite evidence ≠ universal proof', { 'font-size': 18 });
    } else if (id === 'math.5.abstract') {
      const point = r => [210 + 93 * Math.sin(r * 2 * Math.PI / s.n), 164 - 93 * Math.cos(r * 2 * Math.PI / s.n)];
      label(svg, 210, 27, 'Add ' + d.residue + ' modulo ' + s.n, { 'font-size': 24 });
      for (let i = 0; i < Math.min(s.steps, d.order); i++) {
        const [ax, ay] = point(d.orbit[i]), [bx, by] = point(d.orbit[(i + 1) % d.order]);
        const length = Math.hypot(bx - ax, by - ay);
        if (!length) continue; // Adding zero leaves the current vertex unchanged.
        const ux = (bx - ax) / length, uy = (by - ay) / length, tipX = bx - ux * 15, tipY = by - uy * 15;
        line(svg, ax, ay, tipX, tipY, { stroke: colors.gold, 'stroke-width': 2 });
        line(svg, tipX, tipY, tipX - ux * 8 - uy * 4, tipY - uy * 8 + ux * 4, { stroke: colors.gold, 'stroke-width': 2 });
        line(svg, tipX, tipY, tipX - ux * 8 + uy * 4, tipY - uy * 8 - ux * 4, { stroke: colors.gold, 'stroke-width': 2 });
      }
      for (let r = 0; r < s.n; r++) {
        const [x, y] = point(r);
        svg.append(svgElement('circle', { cx: x, cy: y, r: 13, fill: r === d.current ? colors.gold : d.orbit.includes(r) ? colors.teal : colors.paper, stroke: colors.ink }));
        label(svg, x, y + 5, String(r), { 'font-size': 14, fill: d.orbit.includes(r) && r !== d.current ? colors.paper : colors.ink });
      }
      label(svg, 210, 310, 'Order ' + d.order + ' · ' + (d.generator ? 'generator' : 'proper subgroup'), { 'font-size': 22 });
      label(svg, 210, 338, s.steps + 'g = ' + d.current + ' (mod ' + s.n + ')', { 'font-size': 18 });
    } else if (id === 'math.5.measure') {
      label(svg, 210, 27, s.varying ? 'Shrinking gaps: positive limit measure' : 'Middle thirds: zero limit measure', { 'font-size': 19 });
      d.layers.forEach((intervals, k) => {
        const y = 66 + k * 33;
        label(svg, 35, y + 12, String(k), { 'font-size': 14 });
        intervals.forEach(([a, b]) => svg.append(svgElement('rect', { x: 62 + 310 * a, y, width: 310 * (b - a), height: 16, fill: colors.teal })));
      });
      label(svg, 210, 298, 'Stage length ' + numberText(d.length), { 'font-size': 23 });
      label(svg, 210, 330, 'Limiting measure ' + d.limit + ' · not a finite stage', { 'font-size': 18 });
    } else if (id === 'math.5.functional') {
      const px = x => 210 + x * 45, py = y => 163 - y * 20;
      const approx = x => d.coefficients.reduce((sum, c, i) => sum + c * Math.sin((i + 1) * x), 0) + s.perturb * Math.sin(x);
      label(svg, 210, 27, 'Projection onto ' + s.terms + ' sine modes', { 'font-size': 23 });
      line(svg, px(-Math.PI), py(0), px(Math.PI), py(0)); line(svg, px(0), py(-5), px(0), py(5), { opacity: .3 });
      line(svg, px(-Math.PI), py(-Math.PI), px(Math.PI), py(Math.PI), { stroke: colors.blue, 'stroke-width': 2.5 });
      for (let i = 0; i < 240; i++) { const x = -Math.PI + i * Math.PI / 120, next = x + Math.PI / 120; line(svg, px(x), py(approx(x)), px(next), py(approx(next)), { stroke: colors.gold, 'stroke-width': 2 }); }
      label(svg, px(-Math.PI), 282, '−π', { 'font-size': 14 }); label(svg, px(Math.PI), 282, 'π', { 'font-size': 14 });
      label(svg, 210, 311, 'Squared L² error ' + numberText(d.errorSquared), { 'font-size': 22 });
      label(svg, 210, 338, 'Extra squared error = ' + numberText(s.perturb ** 2), { 'font-size': 18 });
    } else {
      label(svg, 210, 27, 'Bisection versus Newton', { 'font-size': 24 });
      label(svg, 111, 51, '[−2, −1] bracket', { 'font-size': 15 }); label(svg, 302, 51, 'Newton x', { 'font-size': 15 });
      d.brackets.forEach(([a, b], i) => {
        const y = 70 + i * 18;
        line(svg, 60 + (a + 2) * 110, y, 60 + (b + 2) * 110, y, { stroke: colors.teal, 'stroke-width': 7 });
        label(svg, 35, y + 5, String(i), { 'font-size': 11 });
        if (i < d.newton.length) {
          svg.append(svgElement('rect', { x: 234, y: y - 10, width: 136, height: 16, rx: 3, fill: colors.gold, 'fill-opacity': .15 }));
          label(svg, 302, y + 3, Number(d.newton[i].toPrecision(5)).toString(), { 'font-size': 13 });
        }
      });
      label(svg, 210, 298, 'Bisection error ≤ 1/' + 2 ** (s.iterations + 1), { 'font-size': 21 });
      label(svg, 210, 330, 'Newton residual ' + d.residual.toPrecision(4), { 'font-size': 19 });
    }
  }

  function drawWordHistory(svg, current) {
    const d = current.data;
    d.route.forEach(([language, form], i) => {
      const y = 12 + i * 67, color = i === d.route.length - 1 ? colors.gold : colors.blue;
      svg.append(svgElement('rect', { x: 62, y, width: 296, height: 55, rx: 8, fill: color, 'fill-opacity': .15, stroke: color }));
      label(svg, 210, y + 20, language, { 'font-size': 17 }); label(svg, 210, y + 45, form, { 'font-size': 24 });
      if (i < d.route.length - 1) {
        line(svg, 210, y + 56, 210, y + 66, { stroke: colors.blue });
        svg.append(svgElement('polyline', { points: '205,' + (y + 60) + ' 210,' + (y + 66) + ' 215,' + (y + 60), fill: 'none', stroke: colors.blue }));
      }
    });
    label(svg, 210, 293, 'One current sense', { 'font-size': 18 });
    label(svg, 210, 323, d.sense, { 'font-size': 22 });
  }

  function drawMetricalFeet(svg, current) {
    const d = current.data, width = 360 / d.syllables;
    label(svg, 210, 36, d.foot + ' · ' + d.feet + (d.feet === 1 ? ' foot' : ' feet'), { 'font-size': 27 });
    label(svg, 210, 73, 'Stress pattern in one model line', { 'font-size': 20 });
    d.stresses.forEach((strong, i) => {
      const x = 30 + (i + .5) * width, height = strong ? 75 : 32;
      svg.append(svgElement('rect', { x: x - Math.min(11, width / 4), y: 196 - height, width: Math.min(22, width / 2), height, rx: 4, fill: strong ? colors.gold : colors.blue }));
      label(svg, x, 224, strong ? '/' : 'x', { 'font-size': 23 });
    });
    d.groups.forEach((group, i) => {
      const left = 30 + group.start * width + 4, right = 30 + group.end * width - 4;
      line(svg, left, 241, right, 241, { stroke: colors.ink }); line(svg, left, 235, left, 242); line(svg, right, 235, right, 242);
      label(svg, (left + right) / 2, 266, 'Foot ' + (i + 1), { 'font-size': 18 });
    });
    label(svg, 210, 301, d.syllables + ' syllables · ' + d.feet + ' feet', { 'font-size': 23 });
    label(svg, 210, 333, 'Stress categories, not measured timing.', { 'font-size': 18 });
  }

  function drawNovelKnowledge(svg, current) {
    const d = current.data;
    for (let i = 1; i <= 4; i++) {
      const x = 72 + (i - 1) * 92;
      if (i < 4) line(svg, x + 20, 45, x + 72, 45, { stroke: colors.blue });
      svg.append(svgElement('circle', { cx: x, cy: 45, r: 20, fill: i === d.chapter ? colors.gold : colors.paper, stroke: colors.blue }));
      label(svg, x, 52, String(i), { 'font-size': 22 });
    }
    [['Mina’s location', d.selected.place, colors.blue], ['Mina’s goal', d.selected.goal, colors.blue], [d.perspective === 'reader' ? 'Reader knows' : 'Mina knows', d.knowledge, colors.teal]].forEach(([title, value, color], i) => {
      const y = 83 + i * 72;
      svg.append(svgElement('rect', { x: 24, y, width: 372, height: 63, rx: 8, fill: color, 'fill-opacity': .13, stroke: color }));
      label(svg, 210, y + 23, title, { 'font-size': 17 }); label(svg, 210, y + 49, value, { 'font-size': 23 });
    });
    label(svg, 210, 329, d.gap ? 'Reader knows more than Mina.' : 'No stated mapmaker knowledge gap.', { 'font-size': 20 });
  }

  function drawSourceOrigins(svg, current) {
    const d = current.data;
    const arrow = (x1, y1, x2, y2) => { line(svg, x1, y1, x2, y2, { stroke: colors.blue, 'stroke-width': 3 }); const a = Math.atan2(y2 - y1, x2 - x1); svg.append(svgElement('polyline', { points: [a + .5, a - .5].map(t => (x2 - 10 * Math.cos(t)) + ',' + (y2 - 10 * Math.sin(t))).join(' ' + x2 + ',' + y2 + ' '), fill: 'none', stroke: colors.blue, 'stroke-width': 3 })); };
    arrow(185, 109, 105, 169); if (!d.independent) arrow(186, 212, 234, 212);
    [['A', 130, 24, 'Archive record'], ['B', 25, 170, 'Copies A'], ['C', 235, 170, d.independent ? 'Independent' : 'Copies B']].forEach(([id, x, y, origin]) => {
      const color = d.inspect === id ? colors.gold : colors.blue;
      svg.append(svgElement('rect', { x, y, width: 160, height: 85, rx: 8, fill: color, 'fill-opacity': .15, stroke: color, 'stroke-width': d.inspect === id ? 3 : 1 }));
      label(svg, x + 80, y + 24, id + ' · opening: 2000', { 'font-size': 17 }); label(svg, x + 80, y + 60, origin, { 'font-size': 20 });
    });
    label(svg, 210, 292, '3 documents · ' + d.origins + (d.origins === 1 ? ' origin' : ' origins'), { 'font-size': 24 });
    label(svg, 210, 327, d.relevant ? 'Opening year: reported, not proved.' : 'Construction cost: unknown.', { 'font-size': 20 });
  }

  function drawAudienceExplanation(svg, current) {
    const d = current.data;
    d.rows.forEach((row, i) => {
      const y = 9 + i * 72, color = row.role === 'Example' ? colors.gold : row.role === 'Explanation' ? colors.teal : colors.blue;
      svg.append(svgElement('rect', { x: 20, y, width: 380, height: 65, rx: 7, fill: color, 'fill-opacity': .13, stroke: color }));
      label(svg, 83, y + 25, row.role, { 'font-size': 16 });
      label(svg, 83, y + 48, d.signposts ? row.signpost : 'No signpost', { 'font-size': 15 });
      row.lines.forEach((text, j) => label(svg, 273, y + 27 + j * 23, text, { 'font-size': 16 }));
    });
    label(svg, 210, 327, d.explanation ? 'Make the connection audible.' : 'The connection is left unstated.', { 'font-size': 21 });
  }

  function drawClauseConstituents(svg, current) {
    const d = current.data, color = key => d.focus === key ? colors.gold : colors.blue;
    svg.append(svgElement('rect', { x: 20, y: 16, width: 380, height: 55, rx: 8, fill: colors.blue, 'fill-opacity': .07, stroke: colors.blue }));
    label(svg, 210, 51, d.sentence, { 'font-size': 23 });
    line(svg, 210, 72, 87, 111, { stroke: colors.blue }); line(svg, 210, 72, 285, 111, { stroke: colors.blue });
    svg.append(svgElement('rect', { x: 20, y: 112, width: 135, height: 80, rx: 8, fill: color('subject'), 'fill-opacity': .15, stroke: color('subject'), 'stroke-width': d.focus === 'subject' ? 3 : 1 }));
    label(svg, 87, 138, 'NP · subject', { 'font-size': 18 }); label(svg, 87, 172, d.subject, { 'font-size': 23 });
    svg.append(svgElement('rect', { x: 170, y: 112, width: 230, height: 155, rx: 8, fill: color('predicate'), 'fill-opacity': .1, stroke: color('predicate'), 'stroke-width': d.focus === 'predicate' ? 3 : 1 }));
    label(svg, 285, 141, 'VP · predicate', { 'font-size': 20 });
    svg.append(svgElement('rect', { x: 181, y: 163, width: 88, height: 77, rx: 6, fill: colors.paper, stroke: colors.blue }));
    label(svg, 225, 188, 'Verb', { 'font-size': 17 }); label(svg, 225, 219, d.verb, { 'font-size': 23 });
    svg.append(svgElement('rect', { x: 278, y: 163, width: 110, height: 77, rx: 6, fill: colors.paper, stroke: color('pp'), 'stroke-width': d.focus === 'pp' ? 3 : 1 }));
    label(svg, 333, 188, 'PP', { 'font-size': 17 }); label(svg, 333, 219, 'over logs', { 'font-size': 20 });
    label(svg, 210, 304, d.agreement ? 'Subject and verb agree.' : 'Subject–verb mismatch.', { 'font-size': 23, fill: d.agreement ? colors.teal : colors.coral });
    label(svg, 210, 336, 'Logs is not the subject.', { 'font-size': 19 });
  }

  function drawParagraphLinks(svg, current) {
    const d = current.data;
    d.rows.forEach((row, i) => {
      const y = 9 + i * 70, color = row.role === 'Detail' ? colors.gold : row.role === 'Explanation' ? colors.teal : colors.blue;
      svg.append(svgElement('rect', { x: 24, y, width: 372, height: 63, rx: 7, fill: color, 'fill-opacity': .13, stroke: color }));
      label(svg, 89, y + 36, row.role, { 'font-size': 17 });
      row.lines.forEach((text, j) => label(svg, 274, y + 26 + j * 24, text, { 'font-size': 18 }));
      if (i < d.rows.length - 1) line(svg, 210, y + 64, 210, y + 69, { stroke: colors.blue });
    });
    label(svg, 210, 310, d.relevant ? 'The detail is relevant.' : 'The detail does not support the claim.', { 'font-size': 20 });
    label(svg, 210, 337, 'Order alone cannot repair relevance.', { 'font-size': 18 });
  }

  function drawSoundBlending(svg, current) {
    const d = current.data;
    label(svg, 210, 33, 'Join sounds, not letter names.', { 'font-size': 22 });
    [...d.word].forEach((letter, i) => {
      const x = 90 + i * 120, color = i < d.step ? colors.gold : colors.blue;
      svg.append(svgElement('rect', { x: x - 45, y: 72, width: 90, height: 77, rx: 9, fill: color, 'fill-opacity': i < d.step ? .23 : .07, stroke: color, 'stroke-width': i < d.step ? 3 : 1 }));
      label(svg, x, 125, letter, { 'font-size': 45 });
      label(svg, x, 180, '/' + d.sounds[i] + '/', { 'font-size': 25 });
      if (i < 2) line(svg, x + 45, 111, x + 75, 111, { stroke: colors.blue });
    });
    label(svg, 210, 222, d.complete ? 'Say the whole word' : 'Written blend so far', { 'font-size': 20 });
    label(svg, 210, 270, d.prefix || '—', { 'font-size': 42 });
    label(svg, 210, 316, d.complete ? d.meaning : 'Keep the sounds in this order.', { 'font-size': 21 });
  }

  function drawHandwritingStrokes(svg, current) {
    const d = current.data;
    label(svg, 210, 31, 'Lowercase ' + d.letter + ' · two strokes', { 'font-size': 23 });
    if (d.guides) [[95, 'Top'], [160, 'Middle'], [240, 'Baseline']].forEach(([y, text]) => {
      line(svg, 30, y, 370, y, { stroke: colors.ink, 'stroke-opacity': .22, 'stroke-dasharray': y === 160 ? '5 5' : 'none' });
      label(svg, 32, y - 9, text, { 'font-size': 16, 'text-anchor': 'start' });
    });
    const draw = (stroke, completed) => {
      if (stroke.kind === 'dot') svg.append(svgElement('circle', { cx: stroke.x, cy: stroke.y, r: 5, fill: completed ? colors.blue : 'none', stroke: completed ? colors.blue : colors.ink, 'stroke-opacity': completed ? 1 : .3 }));
      else line(svg, stroke.x1, stroke.y1, stroke.x2, stroke.y2, { stroke: completed ? colors.blue : colors.ink, 'stroke-width': completed ? 7 : 3, 'stroke-linecap': 'round', 'stroke-opacity': completed ? 1 : .3, 'stroke-dasharray': completed ? 'none' : '4 6' });
    };
    d.strokes.forEach(s => draw(s, false)); d.completed.forEach(s => draw(s, true));
    label(svg, 170, d.strokes[0].y1 + 10, '1', { 'font-size': 19 });
    label(svg, d.letter === 'i' ? 239 : 157, d.letter === 'i' ? 136 : 168, '2', { 'font-size': 19 });
    line(svg, 270, 183, 270, 224, { stroke: colors.blue });
    svg.append(svgElement('polyline', { points: '264,215 270,225 276,215', fill: 'none', stroke: colors.blue, 'stroke-width': 2 }));
    if (d.letter === 't') {
      line(svg, 300, 185, 345, 185, { stroke: colors.blue });
      svg.append(svgElement('polyline', { points: '337,179 347,185 337,191', fill: 'none', stroke: colors.blue, 'stroke-width': 2 }));
    }
    if (d.step < 2) { const next = d.strokes[d.step]; svg.append(svgElement('circle', { cx: next.kind === 'dot' ? next.x : next.x1, cy: next.kind === 'dot' ? next.y : next.y1, r: 9, fill: 'none', stroke: colors.gold, 'stroke-width': 3 })); }
    label(svg, 210, 290, d.instruction, { 'font-size': 22 });
    label(svg, 210, 328, 'An example print style, not a speed test.', { 'font-size': 18 });
  }

  function drawConversation(svg, current) {
    const d = current.data;
    [[d.question, '1 · Ask', colors.blue], [d.reply, '2 · Reply', colors.teal], [d.followup, '3 · Follow up', colors.gold]].forEach(([text, title, color], i) => {
      const y = 16 + i * 94;
      svg.append(svgElement('rect', { x: 24, y, width: 372, height: 77, rx: 12, fill: color, 'fill-opacity': .13, stroke: color }));
      label(svg, 210, y + 25, title, { 'font-size': 18 }); label(svg, 210, y + 56, text, { 'font-size': 22 });
      if (i < 2) line(svg, 210, y + 78, 210, y + 93, { stroke: colors.blue });
    });
    label(svg, 210, 324, d.outcome, { 'font-size': 21 });
  }

  function drawReadingEvidence(svg, current) {
    const d = current.data;
    svg.append(svgElement('rect', { x: 24, y: 18, width: 372, height: 118, rx: 9, fill: colors.blue, 'fill-opacity': .13, stroke: colors.blue }));
    label(svg, 210, 47, 'The text says', { 'font-size': 19 });
    d.passage.forEach((text, i) => label(svg, 210, 82 + i * 31, text, { 'font-size': 21 }));
    line(svg, 210, 137, 210, 167, { stroke: colors.gold, 'stroke-width': 3 });
    svg.append(svgElement('rect', { x: 24, y: 170, width: 372, height: 83, rx: 9, fill: colors.gold, 'fill-opacity': .13, stroke: colors.gold }));
    label(svg, 210, 198, 'A reader’s claim', { 'font-size': 19 }); label(svg, 210, 232, d.claim, { 'font-size': 24 });
    label(svg, 210, 289, d.status, { 'font-size': 22 });
    label(svg, 210, 330, 'What remains unknown?', { 'font-size': 21 });
  }

  function drawStoryPlanning(svg, current) {
    const d = current.data;
    d.parts.forEach((lines, i) => {
      const y = 12 + i * 95, color = i + 1 === d.part ? colors.gold : colors.blue;
      svg.append(svgElement('rect', { x: 24, y, width: 372, height: 83, rx: 8, fill: color, 'fill-opacity': .15, stroke: color, 'stroke-width': i + 1 === d.part ? 3 : 1 }));
      label(svg, 210, y + 21, ['Beginning', 'Middle', 'End'][i], { 'font-size': 17 });
      lines.forEach((text, j) => label(svg, 210, y + 47 + j * 25, text, { 'font-size': 21 }));
      if (i < 2) line(svg, 210, y + 84, 210, y + 94, { stroke: colors.blue });
    });
    label(svg, 210, 333, d.objectState, { 'font-size': 24 });
  }

  function drawDictionaryOrder(svg, current) {
    const d = current.data;
    label(svg, 210, 32, d.first + ' · ' + d.second, { 'font-size': 30 });
    label(svg, 210, 65, 'Compare from left to right', { 'font-size': 20 });
    [d.first, d.second].forEach((word, row) => {
      for (let i = 0; i < 7; i++) {
        const visible = i < d.reveal, decisive = d.decided && i === d.decisive, color = decisive ? colors.gold : colors.blue;
        svg.append(svgElement('rect', { x: 24 + i * 54, y: 94 + row * 76, width: 48, height: 55, rx: 5, fill: color, 'fill-opacity': decisive ? .25 : visible ? .12 : .03, stroke: color, 'stroke-width': decisive ? 3 : 1 }));
        label(svg, 48 + i * 54, 131 + row * 76, visible ? i < word.length ? word[i] : i === word.length ? 'END' : '—' : '?', { 'font-size': visible && i >= word.length ? 16 : 28 });
      }
    });
    label(svg, 210, 265, d.outcome, { 'font-size': 23 });
    label(svg, 210, 301, d.decided ? 'Later letters cannot change this.' : 'Matching beginnings are not enough.', { 'font-size': 20 });
    label(svg, 210, 333, 'END marks the end of a word.', { 'font-size': 18 });
  }

  function drawWordPrecision(svg, current) {
    const d = current.data;
    label(svg, 210, 39, d.sentence, { 'font-size': 29 });
    ['Pace', 'Manner / effort', 'Movement'].forEach((title, i) => {
      const y = 64 + i * 54;
      svg.append(svgElement('rect', { x: 25, y, width: 370, height: 46, rx: 6, fill: colors.blue, 'fill-opacity': .12, stroke: colors.blue }));
      label(svg, 40, y + 29, title, { 'font-size': 19, 'text-anchor': 'start' });
      label(svg, 290, y + 29, d.features[i], { 'font-size': 19 });
    });
    svg.append(svgElement('rect', { x: 25, y: 233, width: 370, height: 102, rx: 8, fill: colors.gold, 'fill-opacity': .13, stroke: colors.gold }));
    label(svg, 210, 257, 'Scene clues', { 'font-size': 18 });
    d.scene.forEach((text, i) => label(svg, 210, 286 + i * 27, text, { 'font-size': 21 }));
  }

  function drawSpellingMap(svg, current) {
    const d = current.data;
    label(svg, 210, 32, d.word, { 'font-size': 34 });
    label(svg, 210, 70, '3 sound boxes', { 'font-size': 20 });
    d.groups.forEach((group, i) => {
      const cx = 90 + i * 120, span = d.spans[i], color = i === d.selected ? colors.gold : colors.blue;
      svg.append(svgElement('rect', { x: cx - 48, y: 90, width: 96, height: 58, rx: 8, fill: color, 'fill-opacity': .17, stroke: color, 'stroke-width': i === d.selected ? 3 : 1 }));
      label(svg, cx, 128, '/' + d.sounds[i] + '/', { 'font-size': 29 });
      for (let j = span.start; j < span.start + span.length; j++) line(svg, cx, 149, 90 + j * 80, 204, { stroke: color, 'stroke-width': i === d.selected ? 3 : 1 });
    });
    [...d.word].forEach((letter, i) => {
      const span = d.spans[d.selected], selected = i >= span.start && i < span.start + span.length, color = selected ? colors.gold : colors.blue;
      svg.append(svgElement('rect', { x: 61 + i * 80, y: 206, width: 58, height: 58, rx: 7, fill: color, 'fill-opacity': .17, stroke: color, 'stroke-width': selected ? 3 : 1 }));
      label(svg, 90 + i * 80, 246, letter, { 'font-size': 34 });
    });
    label(svg, 210, 295, d.letters + ' letter tiles', { 'font-size': 23 });
    label(svg, 210, 332, 'One sound can use two letters.', { 'font-size': 20 });
  }

  function drawSentenceBuilder(svg, current) {
    const d = current.data;
    label(svg, 210, 43, d.written, { 'font-size': 31 });
    [[d.subject, 25, colors.blue], [d.predicate || 'Action missing', 217, d.predicate ? colors.teal : colors.coral]].forEach(([text, x, color]) => {
      svg.append(svgElement('rect', { x, y: 73, width: 178, height: 56, rx: 8, fill: color, 'fill-opacity': .15, stroke: color }));
      label(svg, x + 89, 109, text, { 'font-size': 22 });
    });
    d.checks.forEach((check, i) => {
      const y = 177 + i * 51, color = check.pass ? colors.teal : colors.coral;
      svg.append(svgElement('circle', { cx: 40, cy: y - 7, r: 10, fill: color }));
      label(svg, 66, y, check.label, { 'font-size': 20, 'text-anchor': 'start' });
      label(svg, 363, y, check.pass ? 'Yes' : 'Not yet', { 'font-size': 19 });
    });
    label(svg, 210, 329, d.ready ? 'A complete written statement.' : 'Try changing one part.', { 'font-size': 21 });
  }

  function drawRhymeMatch(svg, current) {
    const d = current.data;
    label(svg, 210, 32, 'Say the words. Listen to the endings.', { 'font-size': 20 });
    [d.first, d.second].forEach((word, i) => {
      const y = 66 + i * 98, color = i && !d.rhyme ? colors.coral : colors.teal;
      svg.append(svgElement('rect', { x: 53, y, width: 132, height: 65, rx: 9, fill: colors.blue, 'fill-opacity': .12, stroke: colors.blue }));
      svg.append(svgElement('rect', { x: 195, y, width: 172, height: 65, rx: 9, fill: color, 'fill-opacity': .18, stroke: color }));
      label(svg, 119, y + 45, word[0], { 'font-size': 40 });
      label(svg, 281, y + 45, word[1], { 'font-size': 40 });
      label(svg, 281, y + 85, 'Sound hint: ' + word[2], { 'font-size': 17 });
    });
    label(svg, 210, 289, d.rhyme ? 'The endings rhyme!' : 'Different ending sounds', { 'font-size': 25 });
    label(svg, 210, 323, d.rhyme && !d.sameLetters ? 'Same sound · different letters' : 'Listen, not just look.', { 'font-size': 20 });
  }

  function drawStoryClues(svg, current) {
    const d = current.data;
    [['who', 'Who?', d.who, 24], ['where', 'Where?', d.where, 216]].forEach(([key, title, text, x]) => {
      svg.append(svgElement('rect', { x, y: 18, width: 180, height: 75, rx: 8, fill: d.clue === key ? colors.gold : colors.blue, 'fill-opacity': .15, stroke: d.clue === key ? colors.gold : colors.blue, 'stroke-width': d.clue === key ? 3 : 1 }));
      label(svg, x + 90, 46, title, { 'font-size': 20 }); label(svg, x + 90, 76, text, { 'font-size': 20 });
    });
    d.events.forEach((text, i) => {
      const y = 115 + 61 * i, selected = i + 1 === d.event;
      svg.append(svgElement('rect', { x: 25, y, width: 370, height: 49, rx: 7, fill: selected ? colors.teal : colors.blue, 'fill-opacity': selected ? .2 : .05, stroke: selected && d.clue === 'what' ? colors.gold : selected ? colors.teal : colors.blue, 'stroke-width': selected ? 3 : 1 }));
      label(svg, 45, y + 31, String(i + 1), { 'font-size': 20 }); label(svg, 221, y + 31, text, { 'font-size': 19 });
      if (i < 2) line(svg, 45, y + 50, 45, y + 60, { stroke: colors.blue });
    });
    label(svg, 210, 326, d.objectStates[d.event - 1], { 'font-size': 24 });
  }

  function drawWavePolarization(svg, current) {
    const d = current.data, x = v => 210 + v * 87, y = v => 164 - v * 87;
    label(svg, 210, 29, 'Wave travels perpendicular to page', { 'font-size': 19 });
    svg.append(svgElement('circle', { cx: 210, cy: 164, r: 87, fill: 'none', stroke: colors.ink, 'stroke-dasharray': '4 5', 'stroke-opacity': .4 }));
    svg.append(svgElement('polygon', { points: d.ring.map(p => x(p.x) + ',' + y(p.y)).join(' '), fill: colors.blue, 'fill-opacity': .07, stroke: colors.blue, 'stroke-width': 2 }));
    d.ring.forEach(p => svg.append(svgElement('circle', { cx: x(p.x), cy: y(p.y), r: 4, fill: colors.blue })));
    d.arms.forEach((p, i) => { line(svg, 210, 164, x(p.x), y(p.y), { stroke: i ? colors.coral : colors.gold, 'stroke-width': 4 }); svg.append(svgElement('circle', { cx: x(p.x), cy: y(p.y), r: 6, fill: i ? colors.coral : colors.gold })); });
    label(svg, 210, 288, 'Differential strain: ' + numberText(d.signal), { 'font-size': 23 });
    label(svg, 210, 316, 'First-order response · strain exaggerated', { 'font-size': 18 });
    label(svg, 210, 340, 'Zero response does not rule out a wave', { 'font-size': 17 });
  }

  function drawIceAlbedo(svg, current) {
    const d = current.data, x = t => 60 + t * 7.5, y = t => 215 - (t - 230) * 1.8;
    label(svg, 210, 29, 'Global temperature (K)', { 'font-size': 22 });
    line(svg, 60, 64, 60, 215); line(svg, 60, 215, 360, 215);
    [230, 270, 310].forEach(t => { label(svg, 36, y(t) + 6, String(t), { 'font-size': 17 }); line(svg, 60, y(t), 360, y(t), { stroke: colors.ink, 'stroke-opacity': .13 }); });
    [0, 20, 40].forEach(t => label(svg, x(t), 239, String(t), { 'font-size': 17 }));
    svg.append(svgElement('polyline', { points: d.records.map(r => x(r.year) + ',' + y(r.temperature)).join(' '), fill: 'none', stroke: colors.blue, 'stroke-width': 3 }));
    line(svg, x(d.selected.year), 64, x(d.selected.year), 215, { stroke: colors.gold, 'stroke-dasharray': '4 4' });
    svg.append(svgElement('circle', { cx: x(d.selected.year), cy: y(d.selected.temperature), r: 5, fill: colors.gold }));
    label(svg, 210, 264, 'Elapsed model years', { 'font-size': 19 });
    label(svg, 210, 298, numberText(d.selected.temperature) + ' K · albedo ' + numberText(d.reflectivity), { 'font-size': 23 });
    label(svg, 210, 332, 'Idealized feedback, not a climate forecast', { 'font-size': 17 });
  }

  function drawCosmicExpansion(svg, current) {
    const d = current.data, x = a => 55 + (a - .25) * 310 / 1.75, y = h => 205 - h * 18;
    label(svg, 210, 28, 'H/H₀: fractional expansion rate', { 'font-size': 20 });
    line(svg, 55, 55, 55, 205); line(svg, 55, 205, 365, 205);
    [0, 4, 8].forEach(h => { label(svg, 35, y(h) + 6, String(h), { 'font-size': 17 }); line(svg, 55, y(h), 365, y(h), { stroke: colors.ink, 'stroke-opacity': .13 }); });
    [.25, 1, 2].forEach(a => label(svg, x(a), 226, String(a), { 'font-size': 17 }));
    label(svg, 210, 249, 'Scale factor a (not time)', { 'font-size': 18 });
    svg.append(svgElement('polyline', { points: d.records.map(r => x(r.a) + ',' + y(r.expansion)).join(' '), fill: 'none', stroke: colors.blue, 'stroke-width': 3 }));
    line(svg, x(d.selected.a), 55, x(d.selected.a), 205, { stroke: colors.gold, 'stroke-dasharray': '4 4' });
    svg.append(svgElement('circle', { cx: x(d.selected.a), cy: y(d.selected.expansion), r: 5, fill: colors.gold }));
    svg.append(svgElement('rect', { x: 55, y: 266, width: 310, height: 17, fill: colors.plum }));
    svg.append(svgElement('rect', { x: 55, y: 266, width: 310 * d.selected.matterFraction, height: 17, fill: colors.teal }));
    label(svg, 210, 308, 'Matter ' + numberText(d.selected.matterFraction * 100) + '% · Λ ' + numberText(d.selected.vacuumFraction * 100) + '%', { 'font-size': 19 });
    label(svg, 210, 336, 'q = ' + numberText(d.selected.q) + ' · negative means accelerating', { 'font-size': 17 });
  }

  function drawBiosignatureInference(svg, current) {
    const d = current.data;
    label(svg, 210, 30, '10,000 hypothetical worlds', { 'font-size': 22 });
    label(svg, 146, 64, 'Life', { 'font-size': 19 });
    label(svg, 302, 64, 'No life', { 'font-size': 19 });
    label(svg, 40, 116, '+', { 'font-size': 26 });
    label(svg, 40, 183, '−', { 'font-size': 26 });
    [[d.tp, 72, 79, colors.teal], [d.fp, 228, 79, colors.coral], [d.fn, 72, 146, colors.blue], [d.tn, 228, 146, colors.blue]].forEach(([count, x, y, color]) => {
      svg.append(svgElement('rect', { x, y, width: 148, height: 59, rx: 6, fill: color, 'fill-opacity': .15, stroke: color }));
      label(svg, x + 74, y + 38, numberText(count), { 'font-size': 24 });
    });
    label(svg, 210, 235, 'Among positive signals only', { 'font-size': 20 });
    svg.append(svgElement('rect', { x: 40, y: 252, width: 340, height: 24, fill: colors.coral }));
    svg.append(svgElement('rect', { x: 40, y: 252, width: 340 * d.posterior, height: 24, fill: colors.teal }));
    label(svg, 210, 308, numberText(d.posterior * 100) + '% with life', { 'font-size': 25 });
    label(svg, 210, 336, 'Conditional on the assumptions', { 'font-size': 18 });
  }

  function drawAtmosphericRetention(svg, current) {
    const d = current.data, width = value => value / 40 * 290;
    label(svg, 210, 29, 'Gravity and molecular motion compete', { 'font-size': 22 });
    label(svg, 210, 64, 'Jeans parameter λ = ' + numberText(d.jeans), { 'font-size': 24 });
    [['Escape speed', d.escape, colors.blue], ['RMS thermal speed', d.rms, colors.gold]].forEach(([name, value, color], i) => {
      const y = 112 + i * 83;
      label(svg, 30, y, name, { 'font-size': 22, 'text-anchor': 'start' });
      svg.append(svgElement('rect', { x: 30, y: y + 13, width: width(value), height: 20, fill: color }));
      label(svg, 388, y + 32, numberText(value), { 'font-size': 20, 'text-anchor': 'end' });
    });
    line(svg, 30, 243, 320, 243, { opacity: .3 });
    [0, 20, 40].forEach(value => { line(svg, 30 + width(value), 243, 30 + width(value), 248, { opacity: .4 }); label(svg, 30 + width(value), 266, String(value), { 'font-size': 16 }); });
    label(svg, 210, 289, 'Speed km/s · shared scale', { 'font-size': 19 });
    label(svg, 210, 315, 'Escape / RMS speed = ' + numberText(d.speedRatio), { 'font-size': 21 });
    label(svg, 210, 341, 'A speed distribution has no RMS cutoff', { 'font-size': 18 });
  }

  function drawCarbonTrajectory(svg, current) {
    const s = current.state, d = current.data, x = year => 60 + year / 60 * 310, yr = rate => 183 - rate / 50 * 66, yc = cumulative => 285 - cumulative / 1250 * 57;
    label(svg, 210, 28, 'Rates fall; cumulative emissions rise', { 'font-size': 23 });
    label(svg, 210, 61, 'Year ' + s.year + ' · added warming ≈ ' + numberText(d.warming) + '°C', { 'font-size': 21 });
    label(svg, 210, 95, 'Annual emissions (GtCO₂/yr)', { 'font-size': 20 });
    [0, 50].forEach(value => { line(svg, 60, yr(value), 370, yr(value), { opacity: .15 }); label(svg, 49, yr(value) + 5, String(value), { 'font-size': 15, 'text-anchor': 'end' }); });
    label(svg, 210, 212, 'Cumulative emissions (GtCO₂)', { 'font-size': 20 });
    [0, 1250].forEach(value => { line(svg, 60, yc(value), 370, yc(value), { opacity: .15 }); label(svg, 49, yc(value) + 5, String(value), { 'font-size': 15, 'text-anchor': 'end' }); });
    [['rate', yr, colors.blue], ['cumulative', yc, colors.teal]].forEach(([key, y, color]) => {
      svg.append(svgElement('polyline', { points: d.records.map((row, i) => x(i) + ',' + y(row[key])).join(' '), fill: 'none', stroke: color, 'stroke-width': 2.5 }));
      svg.append(svgElement('circle', { cx: x(s.year), cy: y(d.selected[key]), r: 5, fill: colors.gold }));
    });
    [0, 30, 60].forEach(value => label(svg, x(value), 309, String(value), { 'font-size': 17 }));
    label(svg, 210, 338, 'Scenario year · no negative emissions', { 'font-size': 19 });
  }

  function drawGeostrophicBalance(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'Pressure + Coriolis = 0', { 'font-size': 24 });
    label(svg, 210, 61, d.valid ? 'Latitude ' + s.latitude + '° · balanced flow' : 'Equator: inversion unavailable', { 'font-size': 22 });
    line(svg, 100, 178, 320, 178, { opacity: .15 }); line(svg, 210, 99, 210, 257, { opacity: .15 });
    label(svg, 90, 184, 'W', { 'font-size': 18 }); label(svg, 334, 184, 'E', { 'font-size': 18 });
    label(svg, 210, 94, 'N', { 'font-size': 18 }); label(svg, 210, 278, 'S', { 'font-size': 18 });
    const arrow = (dx, dy, color) => {
      const length = Math.hypot(dx, dy); if (!length) return;
      const x = 210 + dx, y = 178 + dy, ux = dx / length, uy = dy / length;
      line(svg, 210, 178, x, y, { stroke: color, 'stroke-width': 3 });
      svg.append(svgElement('polygon', { points: x + ',' + y + ' ' + (x - ux * 8 - uy * 4) + ',' + (y - uy * 8 + ux * 4) + ' ' + (x - ux * 8 + uy * 4) + ',' + (y - uy * 8 - ux * 4), fill: color }));
    };
    arrow(s.pressure * 20, 0, colors.blue);
    if (d.valid) { arrow(-s.pressure * 20, 0, colors.coral); arrow(0, -d.northVelocity * 7, colors.gold); }
    svg.append(svgElement('circle', { cx: 210, cy: 178, r: 3, fill: colors.ink }));
    label(svg, 210, 311, 'Velocity and acceleration: separate scales', { 'font-size': 17 });
    label(svg, 210, 340, d.valid ? 'Northward velocity: ' + numberText(d.northVelocity) + ' m/s' : 'No finite geostrophic velocity inferred', { 'font-size': 20 });
  }

  function drawSeismicTimes(svg, current) {
    const s = current.state, d = current.data, x = distance => 60 + distance / 500 * 310, y = time => 263 - time / 250 * 151;
    label(svg, 210, 28, 'Travel time through a uniform medium', { 'font-size': 22 });
    label(svg, 210, 60, s.liquid ? 'Liquid: no direct S-wave arrival' : 'S–P lag: ' + numberText(d.lag) + ' s', { 'font-size': 23 });
    label(svg, 210, 91, 'Travel time since origin (seconds)', { 'font-size': 19 });
    [0, 125, 250].forEach(value => { line(svg, 60, y(value), 370, y(value), { opacity: .15 }); label(svg, 50, y(value) + 5, String(value), { 'font-size': 16, 'text-anchor': 'end' }); });
    line(svg, x(s.distance), 108, x(s.distance), 263, { stroke: colors.gold, 'stroke-dasharray': '4 4' });
    line(svg, x(0), y(0), x(500), y(500 / s.speed), { stroke: colors.blue, 'stroke-width': 3 });
    svg.append(svgElement('circle', { cx: x(s.distance), cy: y(d.pTime), r: 5, fill: colors.blue }));
    if (!s.liquid) {
      line(svg, x(0), y(0), x(500), y(500 / d.sSpeed), { stroke: colors.coral, 'stroke-width': 3 });
      svg.append(svgElement('circle', { cx: x(s.distance), cy: y(d.sTime), r: 5, fill: colors.coral }));
    }
    [0, 250, 500].forEach(value => label(svg, x(value), 289, String(value), { 'font-size': 17 }));
    label(svg, 210, 316, 'Source-to-station path length (km)', { 'font-size': 19 });
    label(svg, 210, 341, s.liquid ? 'S–P distance inference unavailable' : 'Inferred from lag: ' + numberText(d.inferred) + ' km', { 'font-size': 20 });
  }

  function drawRedshiftSpectrum(svg, current) {
    const d = current.data, x = wavelength => 57 + (wavelength - 100) / 3400 * 315, y = value => 265 - value * 147;
    label(svg, 210, 27, 'Temperature and redshift both alter shape', { 'font-size': 21 });
    label(svg, 210, 59, 'Peaks: ' + numberText(d.peak) + ' → ' + numberText(d.observedPeak) + ' nm', { 'font-size': 22 });
    label(svg, 210, 92, 'Per-wavelength spectra · own peak = 1', { 'font-size': 18 });
    [0, .5, 1].forEach(value => { line(svg, 57, y(value), 372, y(value), { opacity: .15 }); label(svg, 47, y(value) + 5, String(value), { 'font-size': 16, 'text-anchor': 'end' }); });
    [[d.emitted, colors.blue], [d.observed, colors.gold]].forEach(([values, color]) => svg.append(svgElement('polyline', { points: values.map((value, i) => x(d.wavelengths[i]) + ',' + y(value)).join(' '), fill: 'none', stroke: color, 'stroke-width': 2.5 })));
    [[d.peak, colors.blue], [d.observedPeak, colors.gold]].forEach(([peak, color]) => svg.append(svgElement('circle', { cx: x(peak), cy: y(1), r: 4, fill: color })));
    [100, 1000, 2000, 3500].forEach(value => label(svg, x(value), 291, String(value), { 'font-size': 16 }));
    label(svg, 210, 316, 'Wavelength (nm)', { 'font-size': 20 });
    label(svg, 210, 341, 'Absolute flux is intentionally not compared', { 'font-size': 18 });
  }

  function drawStellarHR(svg, current) {
    const s = current.state, d = current.data, x = temperature => 70 + (Math.log10(30000) - Math.log10(temperature)) * 300, y = logLuminosity => 270 - (logLuminosity + 6) / 13 * 163;
    label(svg, 210, 28, 'Radius and temperature set luminosity', { 'font-size': 22 });
    label(svg, 210, 59, 'R = ' + s.radius + ' R☉ · L ≈ ' + d.luminosityText + ' L☉', { 'font-size': 23 });
    label(svg, 210, 91, 'Luminosity / solar luminosity (log scale)', { 'font-size': 17 });
    [[-6, '10⁻⁶'], [-3, '10⁻³'], [0, '1'], [3, '10³'], [6, '10⁶']].forEach(([power, text]) => { line(svg, 70, y(power), 370, y(power), { opacity: .15 }); label(svg, 60, y(power) + 5, text, { 'font-size': 16, 'text-anchor': 'end' }); });
    [.01, .1, 1, 10, 100].forEach(radius => {
      const powers = [30000, 3000].map(temperature => Math.log10(radius ** 2 * (temperature / 5772) ** 4));
      line(svg, x(30000), y(powers[0]), x(3000), y(powers[1]), { stroke: radius === d.radius ? colors.blue : colors.ink, opacity: radius === d.radius ? 1 : .15, 'stroke-width': radius === d.radius ? 3 : 1 });
    });
    svg.append(svgElement('circle', { cx: x(5772), cy: y(0), r: 4, fill: colors.teal }));
    svg.append(svgElement('circle', { cx: x(s.temperature), cy: y(d.logLuminosity), r: 6, fill: colors.gold }));
    [30000, 10000, 3000].forEach(value => label(svg, x(value), 292, String(value), { 'font-size': 17 }));
    label(svg, 210, 316, 'Temperature K · hotter ← · log scale', { 'font-size': 18 });
    label(svg, 210, 341, 'Guide radii: 0.01, 0.1, 1, 10, 100 R☉', { 'font-size': 18 });
  }

  function drawSeasonalWater(svg, current) {
    const s = current.state, d = current.data, x = i => 53 + i * 29, y = value => 256 - value / 300 * 132;
    label(svg, 210, 28, 'Same annual rain: 1200 mm', { 'font-size': 23 });
    label(svg, 210, 60, 'Month ' + s.month + ': ET ' + d.selected.actualET + ' · stored ' + d.selected.stored, { 'font-size': 21 });
    label(svg, 210, 96, 'Rain / actual ET / soil water (mm)', { 'font-size': 19 });
    [0, 150, 300].forEach(value => { line(svg, 43, y(value), 383, y(value), { opacity: .15 }); label(svg, 37, y(value) + 5, String(value), { 'font-size': 15, 'text-anchor': 'end' }); });
    svg.append(svgElement('rect', { x: x(s.month - 1) - 11, y: 115, width: 22, height: 146, fill: colors.gold, 'fill-opacity': .13 }));
    d.records.forEach((row, i) => svg.append(svgElement('rect', { x: x(i) - 7, y: y(row.rain), width: 14, height: y(0) - y(row.rain), fill: colors.blue, 'fill-opacity': .35 })));
    [['stored', colors.teal], ['actualET', colors.gold]].forEach(([key, color]) => {
      svg.append(svgElement('polyline', { points: d.records.map((row, i) => x(i) + ',' + y(row[key])).join(' '), fill: 'none', stroke: color, 'stroke-width': 2.5 }));
      d.records.forEach((row, i) => svg.append(svgElement('circle', { cx: x(i), cy: y(row[key]), r: 2.5, fill: color })));
    });
    d.records.forEach((_, i) => label(svg, x(i), 279, String(i + 1), { 'font-size': 14 }));
    label(svg, 210, 302, 'Month · soil water is end-month storage', { 'font-size': 17 });
    label(svg, 210, 336, 'Unmet demand: ' + d.dryMonths + ' of 12 months', { 'font-size': 21 });
  }

  function drawGreenhouseBalance(svg, current) {
    const d = current.data, width = value => value / 800 * 205;
    label(svg, 210, 28, 'Surface ' + numberText(d.temperature) + ' K · ' + numberText(d.celsius) + '°C', { 'font-size': 23 });
    label(svg, 210, 60, 'Without IR absorption: ' + numberText(d.bare) + ' K', { 'font-size': 20 });
    const rows = [['Absorbed sunlight', [[d.absorbed, colors.gold]]], ['Escapes to space', [[d.direct, colors.blue], [d.upward, colors.coral]]], ['Surface emission', [[d.emitted, colors.blue]]], ['Downward layer IR', [[d.downward, colors.coral]]]];
    rows.forEach(([name, segments], i) => {
      const y = 99 + i * 43; let left = 145;
      label(svg, 20, y, name, { 'font-size': 18, 'text-anchor': 'start' });
      segments.forEach(([value, color]) => { svg.append(svgElement('rect', { x: left, y: y + 7, width: width(value), height: 12, fill: color })); left += width(value); });
      label(svg, 397, y + 19, numberText(segments.reduce((sum, item) => sum + item[0], 0)), { 'font-size': 16, 'text-anchor': 'end' });
    });
    label(svg, 210, 282, 'All fluxes in W/m² · common bar scale', { 'font-size': 18 });
    label(svg, 210, 311, 'At top: absorbed = outgoing', { 'font-size': 21 });
    label(svg, 210, 340, 'At surface: sunlight + down IR = emission', { 'font-size': 18 });
  }

  function drawRocketMassRatio(svg, current) {
    const s = current.state, d = current.data, width = mass => mass / d.initial * 280;
    label(svg, 210, 29, 'Δv = vₑ ln(initial mass / current mass)', { 'font-size': 22 });
    label(svg, 210, 62, 'Ideal Δv so far: ' + numberText(d.delta) + ' km/s', { 'font-size': 24 });
    const rows = [['Initial vehicle', [[s.dry, colors.blue], [s.propellant, colors.gold]], d.initial], ['Remaining vehicle', [[s.dry, colors.blue], [d.propellantLeft, colors.gold]], d.remaining], ['Expelled propellant', [[d.expelled, colors.coral]], d.expelled]];
    rows.forEach(([name, segments, total], i) => {
      const y = 100 + i * 60; let left = 20;
      label(svg, 20, y, name, { 'font-size': 20, 'text-anchor': 'start' });
      segments.forEach(([mass, color]) => { svg.append(svgElement('rect', { x: left, y: y + 12, width: width(mass), height: 18, fill: color })); left += width(mass); });
      label(svg, 397, y + 27, numberText(total) + ' t', { 'font-size': 19, 'text-anchor': 'end' });
    });
    label(svg, 210, 288, 'Initial = remaining + expelled', { 'font-size': 21 });
    label(svg, 210, 324, 'Full-burn ideal Δv: ' + numberText(d.full) + ' km/s', { 'font-size': 21 });
  }

  function drawPlateMarkers(svg, current) {
    const s = current.state, d = current.data, point = ([x, y]) => [210 + 75 * x, 178 + 55 * y];
    label(svg, 210, 29, 'Top view · markers on moving plates', { 'font-size': 22 });
    label(svg, 210, 61, s.steps ? d.outcome : 'Starting positions · advance motion', { 'font-size': 21 });
    line(svg, 210, 93, 210, 260, { 'stroke-dasharray': '6 5', opacity: .4 });
    [[-1, 0], [1, 0]].forEach((start, i) => {
      const [sx, sy] = point(start), [x, y] = point(i ? d.b : d.a), color = i ? colors.gold : colors.blue;
      svg.append(svgElement('circle', { cx: sx, cy: sy, r: 13, fill: 'none', stroke: colors.ink, 'stroke-dasharray': '3 3', opacity: .45 }));
      line(svg, sx, sy, x, y, { stroke: color, 'stroke-width': 3 });
      svg.append(svgElement('circle', { cx: x, cy: y, r: 13, fill: color }));
      label(svg, x, y + 6, i ? 'B' : 'A', { 'font-size': 17, fill: colors.paper });
    });
    label(svg, 210, 287, 'Across-boundary gap: ' + numberText(d.gap), { 'font-size': 21 });
    label(svg, 210, 316, 'Along-boundary offset: ' + numberText(d.offset), { 'font-size': 21 });
    label(svg, 210, 341, 'Arbitrary distances · not a hazard forecast', { 'font-size': 17 });
  }

  function drawTidalAlignment(svg, current) {
    const s = current.state, d = current.data, rad = Math.PI / 180;
    label(svg, 210, 27, 'Alignment changes the tidal range', { 'font-size': 23 });
    label(svg, 210, 56, 'Sun–Moon angle ' + s.moon + '°', { 'font-size': 20 });
    const mx = 90 + 50 * Math.cos(s.moon * rad), my = 124 - 50 * Math.sin(s.moon * rad);
    svg.append(svgElement('circle', { cx: 90, cy: 124, r: 50, fill: 'none', stroke: colors.ink, opacity: .15 }));
    line(svg, 90, 124, 215, 124, { stroke: colors.gold, opacity: .6 }); line(svg, 90, 124, mx, my, { stroke: colors.blue });
    svg.append(svgElement('circle', { cx: 90, cy: 124, r: 18, fill: colors.teal, 'fill-opacity': .3, stroke: colors.teal }));
    svg.append(svgElement('circle', { cx: mx, cy: my, r: 7, fill: colors.blue }));
    svg.append(svgElement('circle', { cx: 215, cy: 124, r: 14, fill: colors.gold, 'fill-opacity': .5, stroke: colors.gold }));
    svg.append(svgElement('circle', { cx: 90 + 18 * Math.cos(s.observer * rad), cy: 124 - 18 * Math.sin(s.observer * rad), r: 4, fill: colors.gold }));
    label(svg, 90, 157, 'Earth', { 'font-size': 16 }); label(svg, 215, 157, 'Sun', { 'font-size': 16 });
    label(svg, 315, 105, d.phase, { 'font-size': 17 }); label(svg, 315, 130, 'Range ' + numberText(d.range), { 'font-size': 20 });
    label(svg, 315, 154, 'Blue dot: Moon', { 'font-size': 15 });
    label(svg, 210, 191, 'Idealized height versus direction', { 'font-size': 20 });
    const x = angle => 45 + angle / 360 * 330, y = height => 247 - height * 30;
    [-1.4, 0, 1.4].forEach(value => { line(svg, 45, y(value), 375, y(value), { opacity: .15 }); label(svg, 39, y(value) + 5, String(value), { 'font-size': 14, 'text-anchor': 'end' }); });
    svg.append(svgElement('polyline', { points: d.samples.map((value, i) => x(i * 5) + ',' + y(value)).join(' '), fill: 'none', stroke: colors.blue, 'stroke-width': 2.5 }));
    svg.append(svgElement('circle', { cx: x(s.observer), cy: y(d.local), r: 5, fill: colors.gold }));
    [0, 180, 360].forEach(value => label(svg, x(value), 312, value + '°', { 'font-size': 17 }));
    label(svg, 210, 341, 'Direction ' + s.observer + '° · height ' + numberText(d.local), { 'font-size': 21 });
  }

  function drawClimateReference(svg, current) {
    const s = current.state, d = current.data, x = i => 58 + i * 8.3, y = value => 268 - value * 7;
    label(svg, 210, 29, 'Same calendar date · 30 reference years', { 'font-size': 21 });
    label(svg, 210, 61, 'Reference ' + d.mean + '°C · today ' + d.today + '°C', { 'font-size': 23 });
    [0, 10, 20].forEach(value => { line(svg, 51, y(value), 389, y(value), { opacity: .15 }); label(svg, 43, y(value) + 6, value + '°', { 'font-size': 17, 'text-anchor': 'end' }); });
    line(svg, 51, y(d.mean), 389, y(d.mean), { stroke: colors.teal, 'stroke-width': 2, 'stroke-dasharray': '4 4' });
    d.records.forEach((value, i) => svg.append(svgElement('circle', { cx: x(i), cy: y(value), r: i + 1 === s.year ? 5 : 2.5, fill: i + 1 === s.year ? colors.gold : colors.blue })));
    line(svg, 327, 102, 327, 273, { opacity: .2 });
    svg.append(svgElement('circle', { cx: 363, cy: y(d.today), r: 7, fill: colors.gold }));
    [0, 14, 29].forEach(i => label(svg, x(i), 292, String(i + 1), { 'font-size': 16 }));
    label(svg, 363, 292, 'Today', { 'font-size': 17 });
    label(svg, 181, 317, 'Reference year (not consecutive days)', { 'font-size': 16 });
    label(svg, 210, 343, 'Inspected year ' + s.year + ': ' + d.selected + '°C', { 'font-size': 20 });
  }

  function drawWasteStock(svg, current) {
    const s = current.state, d = current.data, x = i => 58 + i * 39, y = value => 246 - value / 84 * 137;
    label(svg, 210, 28, 'New input and existing stock differ', { 'font-size': 22 });
    label(svg, 210, 60, 'Input ' + d.inflow + '/step · collect up to ' + s.cleanup, { 'font-size': 22 });
    label(svg, 210, 89, 'Waste remaining (arbitrary units)', { 'font-size': 18 });
    [0, 20, 40, 60, 80].forEach(value => { line(svg, 58, y(value), 370, y(value), { opacity: .15 }); label(svg, 45, y(value) + 5, String(value), { 'font-size': 16, 'text-anchor': 'end' }); });
    svg.append(svgElement('polyline', { points: d.history.map((value, i) => x(i) + ',' + y(value)).join(' '), fill: 'none', stroke: colors.blue, 'stroke-width': 3 }));
    d.history.forEach((value, i) => svg.append(svgElement('circle', { cx: x(i), cy: y(value), r: i === s.steps ? 6 : 3, fill: i === s.steps ? colors.gold : colors.blue })));
    [0, 2, 4, 6, 8].forEach(i => label(svg, x(i), 271, String(i), { 'font-size': 17 }));
    label(svg, 210, 295, 'Elapsed steps', { 'font-size': 18 });
    label(svg, 210, 322, 'Stock ' + d.stock + ' · managed storage ' + d.collected, { 'font-size': 21 });
    label(svg, 210, 345, 'Collected material has not disappeared', { 'font-size': 18 });
  }

  function drawPlanetSizes(svg, current) {
    const d = current.data;
    label(svg, 210, 29, 'Same diameter scale for both worlds', { 'font-size': 22 });
    d.names.forEach((name, i) => {
      const x = i ? 310 : 110, color = i ? colors.gold : colors.blue, radius = d.radii[i];
      label(svg, x, 65, (i ? 'B: ' : 'A: ') + name, { 'font-size': 22 });
      svg.append(svgElement('circle', { cx: x, cy: 157, r: radius, fill: color, 'fill-opacity': .18, stroke: color, 'stroke-width': 1.5 }));
      line(svg, x - radius, 157, x + radius, 157, { stroke: color, 'stroke-width': 1 });
      label(svg, x, 254, String(d.diameters[i]) + ' km', { 'font-size': 20 });
    });
    label(svg, 210, 290, 'B/A diameter ≈ ' + smallLengthText(d.ratio), { 'font-size': 22 });
    label(svg, 210, 324, 'B/A spherical volume ≈ ' + smallLengthText(d.volumeRatio), { 'font-size': 21 });
  }

  function drawStellarFlux(svg, current) {
    const s = current.state, d = current.data, x = distance => 58 + (distance - 1) * 45, y = flux => 263 - flux / 8 * 157;
    label(svg, 210, 28, 'Emission and received light differ', { 'font-size': 23 });
    label(svg, 210, 61, 'L = ' + s.luminosity + ' · d = ' + s.distance + ' · L/d² ≈ ' + numberText(d.flux), { 'font-size': 23, fill: colors.gold });
    label(svg, 210, 92, 'Received light (relative units)', { 'font-size': 19 });
    [0, 4, 8].forEach(value => { line(svg, 58, y(value), 373, y(value), { opacity: .2 }); label(svg, 44, y(value) + 6, String(value), { 'font-size': 17, 'text-anchor': 'end' }); });
    const curve = Array.from({ length: 141 }, (_, i) => { const distance = 1 + i / 20; return x(distance) + ',' + y(s.luminosity / distance ** 2); });
    svg.append(svgElement('polyline', { points: curve.join(' '), fill: 'none', stroke: colors.blue, 'stroke-width': 3 }));
    d.samples.forEach((flux, i) => { svg.append(svgElement('circle', { cx: x(i + 1), cy: y(flux), r: 3, fill: colors.blue })); label(svg, x(i + 1), 289, String(i + 1), { 'font-size': 17 }); });
    line(svg, x(s.distance), y(d.flux), x(s.distance), 263, { stroke: colors.gold, 'stroke-dasharray': '4 4' });
    svg.append(svgElement('circle', { cx: x(s.distance), cy: y(d.flux), r: 6, fill: colors.gold }));
    label(svg, 210, 315, 'Distance (relative units)', { 'font-size': 20 });
    label(svg, 210, 341, 'Double distance → one quarter the flux', { 'font-size': 19 });
  }

  function drawWeatherComparison(svg, current) {
    const s = current.state, d = current.data, y = value => 269 - (value - d.minimum) / (d.maximum - d.minimum) * 143;
    label(svg, 210, 28, 'Four invented weather observations', { 'font-size': 22 });
    label(svg, 210, 60, 'Day ' + (Number(s.day) + 1) + ': ' + d.selected.name, { 'font-size': 21, fill: colors.gold });
    label(svg, 210, 94, d.name + ' (' + d.unit + ')', { 'font-size': 21 });
    [d.minimum, 0, d.maximum].filter((v, i, a) => a.indexOf(v) === i).forEach(value => { line(svg, 57, y(value), 390, y(value), { opacity: value === 0 ? .6 : .15 }); label(svg, 45, y(value) + 6, String(value), { 'font-size': 17, 'text-anchor': 'end' }); });
    d.values.forEach((value, i) => {
      const x = 97 + i * 85, color = i === Number(s.day) ? colors.gold : colors.blue;
      line(svg, x, y(0), x, y(value), { stroke: color, 'stroke-width': 10 });
      svg.append(svgElement('circle', { cx: x, cy: y(value), r: 6, fill: color }));
      label(svg, x, y(value) - 13, String(value), { 'font-size': 20, fill: color });
      label(svg, x, 301, 'Day ' + (i + 1), { 'font-size': 18 });
    });
    label(svg, 210, 337, 'Compare one measurement at a time', { 'font-size': 20 });
  }

  function drawSolarDistances(svg, current) {
    const s = current.state, d = current.data, x = fraction => 30 + 350 * fraction;
    label(svg, 210, 27, s.scale === 'order' ? 'Order only · equal spacing' : 'Linear distance from the Sun', { 'font-size': 23 });
    label(svg, 210, 60, d.name + ' · ' + d.distance + ' AU · ' + d.group, { 'font-size': 19 });
    label(svg, 30, 99, 'Sun', { 'font-size': 17 });
    line(svg, 30, 130, 380, 130, { opacity: .5 }); line(svg, 30, 116, 30, 142, { stroke: colors.gold, 'stroke-width': 3 });
    d.positions.forEach((position, i) => svg.append(svgElement('circle', { cx: x(position), cy: 130, r: 4, fill: colors.blue })));
    const selectedX = x(d.positions[d.index]);
    line(svg, selectedX, 110, selectedX, 145, { stroke: colors.gold, 'stroke-width': 2 });
    svg.append(svgElement('circle', { cx: selectedX, cy: 130, r: 7, fill: colors.gold, stroke: colors.paper, 'stroke-width': 1.5 }));
    if (s.scale === 'distance') [0, 10, 20, 30].forEach(value => label(svg, x(value / 30.06), 169, String(value) + ' AU', { 'font-size': 16 }));
    else d.positions.forEach((position, i) => label(svg, x(position), 169, String(i + 1), { 'font-size': 17 }));
    d.names.forEach((name, i) => {
      const column = i < 4 ? 0 : 1, row = i % 4, left = 20 + column * 200, top = 193 + row * 37;
      if (i === d.index) svg.append(svgElement('rect', { x: left - 5, y: top - 20, width: 191, height: 33, rx: 5, fill: colors.gold, 'fill-opacity': .14 }));
      label(svg, left, top, (i + 1) + ' ' + name, { 'font-size': 17, 'text-anchor': 'start' });
      label(svg, left + 180, top, String(d.distances[i]), { 'font-size': 17, 'text-anchor': 'end' });
    });
    label(svg, 210, 339, 'Table distances in AU · sizes not to scale', { 'font-size': 18 });
  }

  function drawLandWater(svg, current) {
    const s = current.state, d = current.data, x = i => 30 + 60 * i, y = i => 260 - 24 * d.heights[i];
    label(svg, 210, 29, s.basin ? 'A basin can hold surface water' : 'Land shape guides surface water', { 'font-size': 22 });
    label(svg, 210, 61, d.status, { 'font-size': 21, fill: colors.blue });
    svg.append(svgElement('polygon', { points: '30,260 ' + d.heights.map((_, i) => x(i) + ',' + y(i)).join(' ') + ' 390,260', fill: colors.teal, 'fill-opacity': .16, stroke: colors.teal, 'stroke-width': 2 }));
    [0, 6].forEach(i => { line(svg, x(i) - 20, 260, x(i) + 20, 260, { stroke: colors.blue, 'stroke-width': 4 }); label(svg, x(i), 308, 'Sea', { 'font-size': 18 }); });
    d.heights.forEach((_, i) => { svg.append(svgElement('circle', { cx: x(i), cy: y(i), r: 3, fill: colors.teal })); label(svg, x(i), 286, String(i), { 'font-size': 15 }); });
    svg.append(svgElement('circle', { cx: x(s.start), cy: y(s.start), r: 9, fill: 'none', stroke: colors.gold, 'stroke-width': 3 }));
    if (d.traveled.length > 1) svg.append(svgElement('polyline', { points: d.traveled.map(i => x(i) + ',' + (y(i) - 7)).join(' '), fill: 'none', stroke: colors.blue, 'stroke-width': 4 }));
    const px = x(d.position), py = y(d.position) - 15;
    svg.append(svgElement('path', { d: 'M' + px + ' ' + (py - 18) + ' C' + (px - 19) + ' ' + py + ' ' + (px - 8) + ' ' + (py + 12) + ' ' + px + ' ' + (py + 12) + ' C' + (px + 8) + ' ' + (py + 12) + ' ' + (px + 19) + ' ' + py + ' ' + px + ' ' + (py - 18) + 'Z', fill: colors.blue, stroke: colors.paper, 'stroke-width': 2 }));
    label(svg, 210, 337, 'Position ' + d.position + ' · moves ' + (d.traveled.length - 1), { 'font-size': 21 });
  }

  function drawWaterStores(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 26, 'One possible water route · total 20', { 'font-size': 23 });
    const nodes = { surface: [80, 258, 'Surface water'], vapour: [80, 78, 'Water vapour'], cloud: [300, 78, 'Cloud droplets'], land: [300, 184, 'Water on land'], ground: [300, 284, 'Ground store'] };
    const arrows = [[80, 228, 80, 109, 118, 165, 'evaporate'], [145, 78, 230, 78, 185, 61, 'condense'], [300, 109, 300, 154, 354, 137, 'fall'], [300, 215, 300, 254, 352, 239, 'soak in'], [230, 197, 145, 244, 182, 212, 'run off'], [230, 284, 145, 284, 185, 307, 'return']];
    arrows.forEach(([x1, y1, x2, y2, lx, ly, text], i) => {
      const color = s.stage === i + 1 ? colors.gold : colors.blue, length = Math.hypot(x2 - x1, y2 - y1), ux = (x2 - x1) / length, uy = (y2 - y1) / length;
      line(svg, x1, y1, x2, y2, { stroke: color, 'stroke-width': s.stage === i + 1 ? 3 : 1.5 });
      svg.append(svgElement('polygon', { points: x2 + ',' + y2 + ' ' + (x2 - ux * 9 - uy * 4) + ',' + (y2 - uy * 9 + ux * 4) + ' ' + (x2 - ux * 9 + uy * 4) + ',' + (y2 - uy * 9 - ux * 4), fill: color }));
      label(svg, lx, ly, text, { 'font-size': 16, fill: color });
    });
    Object.entries(nodes).forEach(([key, [x, y, text]]) => {
      svg.append(svgElement('rect', { x: x - 65, y: y - 28, width: 130, height: 56, rx: 8, fill: colors.blue, 'fill-opacity': .08, stroke: colors.blue }));
      label(svg, x, y - 6, text, { 'font-size': key === 'cloud' ? 15 : 17 });
      label(svg, x, y + 19, numberText(d.stores[key]), { 'font-size': 24, fill: colors.blue });
    });
    label(svg, 210, 341, 'Stage ' + s.stage + ' · all stores sum to ' + d.total, { 'font-size': 21 });
  }

  function drawRockRoute(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'Different conditions, different routes', { 'font-size': 22 });
    const drawMaterial = (x, material, color) => {
      label(svg, x + 72, 79, material[0].toUpperCase() + material.slice(1), { 'font-size': 21 });
      if (material === 'magma') {
        svg.append(svgElement('path', { d: 'M' + (x + 10) + ' 169 C' + (x - 5) + ' 128 ' + (x + 28) + ' 121 ' + (x + 49) + ' 131 C' + (x + 74) + ' 80 ' + (x + 96) + ' 123 ' + (x + 131) + ' 127 C' + (x + 155) + ' 146 ' + (x + 140) + ' 193 ' + (x + 94) + ' 197 C' + (x + 64) + ' 208 ' + (x + 21) + ' 192 ' + (x + 10) + ' 169 Z', fill: colors.coral, 'fill-opacity': .25, stroke: color, 'stroke-width': 2 }));
        [149, 173].forEach(y => svg.append(svgElement('path', { d: 'M' + (x + 25) + ' ' + y + ' Q' + (x + 57) + ' ' + (y - 19) + ' ' + (x + 81) + ' ' + y + ' T' + (x + 126) + ' ' + y, fill: 'none', stroke: colors.coral, 'stroke-width': 3, opacity: .65 })));
        return;
      }
      if (material === 'sediment') {
        for (let i = 0; i < 12; i++) svg.append(svgElement('circle', { cx: x + 20 + (i % 4) * 32, cy: 117 + Math.floor(i / 4) * 31, r: 8 + i % 3, fill: color, 'fill-opacity': .5, stroke: color }));
      } else {
        svg.append(svgElement('path', { d: 'M' + (x + 8) + ' 111 L' + (x + 40) + ' 96 L' + (x + 126) + ' 108 L' + (x + 140) + ' 188 L' + (x + 96) + ' 205 L' + (x + 13) + ' 192 Z', fill: material === 'magma' ? colors.coral : color, 'fill-opacity': .18, stroke: color, 'stroke-width': 2 }));
        if (material === 'sedimentary' || material === 'metamorphic') for (let i = 0; i < 3; i++) {
          const y = 129 + i * 22;
          svg.append(svgElement('path', { d: material === 'metamorphic' ? 'M' + (x + 15) + ' ' + y + ' Q' + (x + 56) + ' ' + (y - 20) + ' ' + (x + 85) + ' ' + y + ' T' + (x + 131) + ' ' + y : 'M' + (x + 15) + ' ' + y + ' L' + (x + 130) + ' ' + y, fill: 'none', stroke: color, 'stroke-width': 3, opacity: .5 }));
        }
        if (material === 'igneous' || material === 'magma') for (let i = 0; i < 8; i++) svg.append(svgElement('circle', { cx: x + 30 + (i % 4) * 25, cy: 130 + Math.floor(i / 4) * 40, r: material === 'magma' ? 7 : 4, fill: color, 'fill-opacity': .45 }));
      }
    };
    drawMaterial(20, s.material, colors.blue);
    line(svg, 177, 151, 235, 151, { stroke: colors.gold, 'stroke-width': 3 });
    svg.append(svgElement('path', { d: 'M226 144 L235 151 L226 158', fill: 'none', stroke: colors.gold, 'stroke-width': 3 }));
    if (d.valid) drawMaterial(253, d.result, colors.teal);
    else { label(svg, 325, 137, ['No direct route', 'in this model'], { 'font-size': 18 }); }
    label(svg, 210, 258, d.processName, { 'font-size': d.processName.length > 25 ? 18 : 21, fill: colors.gold });
    label(svg, 210, 300, d.valid ? 'Modeled product: ' + d.result : 'Choose another material or process', { 'font-size': 21 });
    label(svg, 210, 338, 'Textures are cues, not rock identification', { 'font-size': 17 });
  }

  function drawPadReuse(svg, current) {
    const s = current.state, d = current.data, bits = value => value.toString(2).padStart(4, '0');
    label(svg, 210, 28, 'Four-bit XOR · deliberately reused pad', { 'font-size': 21 });
    ['Message', 'Pad', 'Ciphertext'].forEach((text, i) => label(svg, 75 + i * 135, 72, text, { 'font-size': 21 }));
    [[s.first, s.key, d.c1], [s.second, s.key, d.c2]].forEach((row, i) => row.forEach((value, j) => {
      const color = [colors.blue, colors.gold, colors.teal][j], x = 23 + j * 135, y = 93 + i * 64;
      svg.append(svgElement('rect', { x, y, width: 104, height: 43, rx: 6, fill: color, 'fill-opacity': .1, stroke: color }));
      label(svg, x + 52, y + 29, bits(value), { 'font-size': 24, fill: color });
      if (j < 2) label(svg, x + 120, y + 27, j === 0 ? '⊕' : '=', { 'font-size': 21 });
    }));
    label(svg, 210, 247, 'Ciphertext XOR: ' + bits(d.difference), { 'font-size': 23, fill: colors.teal });
    label(svg, 210, 282, 'Message XOR: ' + bits(d.messageXor), { 'font-size': 23, fill: colors.blue });
    label(svg, 210, 329, 'K ⊕ K = 0000 — the pad cancels', { 'font-size': 21 });
  }

  function drawPointerAccess(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'Four cells · assumed 4-byte integers', { 'font-size': 22 });
    d.values.forEach((value, i) => {
      const x = 35 + i * 90;
      label(svg, x + 40, 74, '[' + i + ']', { 'font-size': 22 });
      svg.append(svgElement('rect', { x, y: 89, width: 80, height: 58, rx: 6, fill: d.valid && i === s.index ? colors.gold : colors.blue, 'fill-opacity': s.alive ? .12 : .025, stroke: colors.blue }));
      label(svg, x + 40, 126, value === null ? '—' : String(value), { 'font-size': 27 });
      label(svg, x + 40, 173, s.alive ? '0x' + (4096 + 4 * i).toString(16) : 'expired', { 'font-size': 16 });
    });
    label(svg, 210, 213, 'Index ' + s.index + ' · ' + s.action + ' · ' + (d.address || 'no valid pointer'), { 'font-size': 21 });
    label(svg, 210, 255, d.status, { 'font-size': 22, fill: d.valid ? colors.blue : colors.coral });
    label(svg, 210, 299, d.valid ? 'Result: ' + d.result : 'No access performed', { 'font-size': 25 });
    label(svg, 210, 338, 'Requested write value: ' + s.value, { 'font-size': 20 });
  }

  function drawAttentionMix(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 27, 'One query · three key/value pairs', { 'font-size': 23 });
    d.weights.forEach((weight, i) => {
      const x = 80 + i * 130, color = d.allowed[i] ? colors.blue : colors.coral;
      label(svg, x, 69, 'K=' + d.keys[i] + ', V=' + d.values[i], { 'font-size': 18 });
      label(svg, x, 99, d.allowed[i] ? 'score ' + numberText(d.scores[i]) : 'masked', { 'font-size': 18, fill: color });
      line(svg, x - 34, 233, x + 34, 233, { opacity: .3 });
      svg.append(svgElement('rect', { x: x - 30, y: 233 - weight * 118, width: 60, height: weight * 118, fill: color, 'fill-opacity': .45 }));
      label(svg, x, 260, numberText(weight * 100) + '%', { 'font-size': 20, fill: color });
    });
    label(svg, 210, 304, 'Weighted output: ' + numberText(d.result), { 'font-size': 24, fill: colors.teal });
    label(svg, 210, 340, 'q=' + s.query + ' · causal mask ' + (s.causal ? 'on' : 'off'), { 'font-size': 21 });
  }

  function drawQuorumOverlap(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 27, 'Five replicas · fixed membership', { 'font-size': 24 });
    label(svg, 210, 64, 'A mask ' + s.first.toString(2).padStart(5, '0') + ' · B mask ' + s.second.toString(2).padStart(5, '0'), { 'font-size': 21 });
    ['A', 'B', 'A ∩ B'].forEach((text, row) => {
      label(svg, 40, 122 + row * 55, text, { 'font-size': 21 });
      const selected = [d.first, d.second, d.overlap][row], color = [colors.blue, colors.gold, colors.teal][row];
      for (let i = 1; i <= 5; i++) {
        const x = 90 + (i - 1) * 65;
        svg.append(svgElement('circle', { cx: x, cy: 114 + row * 55, r: 23, fill: color, 'fill-opacity': selected.includes(i) ? .23 : .025, stroke: color, 'stroke-width': selected.includes(i) ? 3 : 1 }));
        label(svg, x, 121 + row * 55, String(i), { 'font-size': 21, opacity: selected.includes(i) ? 1 : .35 });
      }
    });
    label(svg, 210, 286, 'Actual overlap: ' + d.overlap.length, { 'font-size': 24, fill: colors.teal });
    label(svg, 210, 318, 'Guaranteed by sizes: at least ' + d.lowerBound, { 'font-size': 21 });
    label(svg, 210, 345, 'Both majorities: ' + truthText(d.majorities), { 'font-size': 18 });
  }

  function drawTypedReduction(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'Int parameter · ' + d.argumentType + ' argument', { 'font-size': 24 });
    const descriptions = ['Application', 'Substitute argument for x', 'Reduce integer addition'];
    for (let i = 0; i < 3; i++) {
      const y = 55 + i * 80, color = !d.valid ? colors.coral : i === s.stage ? colors.gold : colors.blue;
      svg.append(svgElement('rect', { x: 25, y, width: 370, height: 67, rx: 7, fill: color, 'fill-opacity': .09, stroke: color }));
      label(svg, 210, y + 23, descriptions[i], { 'font-size': 19 });
      label(svg, 210, y + 51, !d.valid && i > 0 ? 'Blocked by type check' : i <= s.stage ? d.terms[i] : 'Not yet reduced', { 'font-size': i === 0 ? 19 : 22 });
    }
    label(svg, 210, 315, d.valid ? 'Every shown term has type Int' : 'Type error: Bool is not Int', { 'font-size': 22 });
    label(svg, 210, 343, 'Requested stage: ' + s.stage, { 'font-size': 18 });
  }

  function drawBoundedCheck(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'Safety: counter ≤ ' + s.limit, { 'font-size': 25 });
    label(svg, 210, 60, 'Increment guard: counter ' + (s.repaired ? '<' : '≤') + ' ' + s.limit, { 'font-size': 21 });
    label(svg, 66, 96, 'Depth', { 'font-size': 19 }); label(svg, 252, 96, 'Reachable counters', { 'font-size': 19 });
    d.levels.forEach((states, i) => {
      const y = 107 + i * 23, bad = states.some(value => value > s.limit), color = bad ? colors.coral : colors.blue;
      svg.append(svgElement('rect', { x: 27, y, width: 366, height: 21, rx: 4, fill: color, 'fill-opacity': .08 }));
      label(svg, 66, y + 17, String(i), { 'font-size': 17 }); label(svg, 252, y + 17, states.join(', '), { 'font-size': 17, fill: color });
    });
    label(svg, 210, 298, d.violation ? 'Counterexample at depth ' + d.violation.depth : 'No counterexample through ' + s.bound, { 'font-size': 22, fill: d.violation ? colors.coral : colors.gold });
    label(svg, 210, 334, d.violation ? d.violation.path.join(' → ') : 'Bounded evidence, not an unbounded proof', { 'font-size': d.violation ? 23 : 17 });
  }

  function drawShortestPath(svg, current) {
    const d = current.data, positions = [[50, 165], [200, 65], [200, 250], [365, 165]], costPositions = [[105, 93], [100, 242], [225, 165], [294, 94], [300, 257]];
    label(svg, 210, 26, 'Dijkstra from A · positive costs', { 'font-size': 22 });
    d.edges.forEach((edge, i) => {
      const a = positions[edge.from], b = positions[edge.to], length = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const ux = (b[0] - a[0]) / length, uy = (b[1] - a[1]) / length;
      const x1 = a[0] + ux * 34, y1 = a[1] + uy * 34, x2 = b[0] - ux * 34, y2 = b[1] - uy * 34;
      const inPath = d.path.some((node, j) => node === edge.from && d.path[j + 1] === edge.to), color = inPath ? colors.gold : colors.blue;
      line(svg, x1, y1, x2, y2, { stroke: color, 'stroke-width': inPath ? 3 : 1.5 });
      svg.append(svgElement('polygon', { points: x2 + ',' + y2 + ' ' + (x2 - ux * 10 - uy * 5) + ',' + (y2 - uy * 10 + ux * 5) + ' ' + (x2 - ux * 10 + uy * 5) + ',' + (y2 - uy * 10 - ux * 5), fill: color }));
      label(svg, costPositions[i][0], costPositions[i][1], String(edge.cost), { 'font-size': 21, fill: color });
    });
    positions.forEach(([x, y], i) => {
      svg.append(svgElement('circle', { cx: x, cy: y, r: 30, fill: d.settled.includes(i) ? colors.gold : colors.paper, 'fill-opacity': d.settled.includes(i) ? .2 : 1, stroke: colors.blue, 'stroke-width': 2 }));
      label(svg, x, y - 3, 'ABCD'[i], { 'font-size': 22 });
      label(svg, x, y + 19, d.distances[i] === null ? '—' : String(d.distances[i]), { 'font-size': 18 });
    });
    label(svg, 210, 312, 'Settled: ' + (d.settled.map(i => 'ABCD'[i]).join(' → ') || 'none'), { 'font-size': 21 });
    label(svg, 210, 340, 'D: ' + (d.distances[3] === null ? 'not discovered' : (d.final ? 'final' : 'tentative') + ' cost ' + d.distances[3]), { 'font-size': 22 });
  }

  function drawLearningErrors(svg, current) {
    const d = current.data;
    const maximum = Math.max(1, ...d.trajectory.flatMap(row => [row.training, row.heldout])) * 1.1;
    const x = step => 58 + step / 8 * 330, y = loss => 244 - loss / maximum * 168;
    label(svg, 210, 27, 'Gradient descent · w≈' + numberText(d.weight), { 'font-size': 23 });
    label(svg, 225, 56, 'Mean squared error · scale adjusts', { 'font-size': 18 });
    [0, maximum / 2, maximum].forEach(value => {
      line(svg, 58, y(value), 388, y(value), { opacity: .15 });
      label(svg, 50, y(value) + 5, numberText(value), { 'font-size': 14, 'text-anchor': 'end' });
    });
    [0, 4, 8].forEach(step => label(svg, x(step), 270, String(step), { 'font-size': 18 }));
    [['training', colors.blue], ['heldout', colors.gold]].forEach(([key, color]) => {
      svg.append(svgElement('polyline', { points: d.trajectory.map(row => x(row.step) + ',' + y(row[key])).join(' '), fill: 'none', stroke: color, 'stroke-width': 2.5 }));
      d.trajectory.forEach(row => svg.append(svgElement('circle', { cx: x(row.step), cy: y(row[key]), r: 3, fill: color })));
    });
    label(svg, 210, 294, 'Training updates', { 'font-size': 17 });
    label(svg, 210, 318, 'Training MSE: ' + smallLengthText(d.trainingLoss), { 'font-size': 20, fill: colors.blue });
    label(svg, 210, 344, 'Held-out MSE: ' + smallLengthText(d.heldoutLoss), { 'font-size': 20, fill: colors.gold });
  }

  function drawSuffixMachine(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 27, 'Input: ' + (s.word || 'ε') + ' · read ' + d.consumed + '/' + s.word.length, { 'font-size': 24 });
    [0, 1, 2].forEach((state, i) => {
      const x = 70 + i * 140;
      svg.append(svgElement('circle', { cx: x, cy: 89, r: 30, fill: state === d.state ? colors.gold : colors.paper, 'fill-opacity': state === d.state ? .2 : 1, stroke: state === 2 ? colors.teal : colors.blue, 'stroke-width': 2 }));
      if (state === 2) svg.append(svgElement('circle', { cx: x, cy: 89, r: 36, fill: 'none', stroke: colors.teal, 'stroke-width': 2 }));
      label(svg, x, 97, 'q' + state, { 'font-size': 25 });
      label(svg, x, 145, ['Other / start', 'Ends in 0', 'Ends in 01'][i], { 'font-size': 17 });
    });
    ['From', 'Read 0', 'Read 1'].forEach((text, i) => label(svg, 70 + i * 140, 184, text, { 'font-size': 21 }));
    d.transitions.forEach((next, row) => {
      const y = 197 + row * 31;
      svg.append(svgElement('rect', { x: 28, y, width: 364, height: 28, rx: 5, fill: row === d.state ? colors.gold : colors.blue, 'fill-opacity': row === d.state ? .18 : .045 }));
      [row, ...next].forEach((value, col) => label(svg, 70 + col * 140, y + 21, 'q' + value, { 'font-size': 21 }));
    });
    label(svg, 210, 313, d.finished ? 'Full input: ' + (d.accepted ? 'accepted' : 'rejected') : 'Prefix: ' + (d.prefix || 'ε') + ' · remaining: ' + d.remaining, { 'font-size': 21 });
    label(svg, 210, 341, 'Current state: q' + d.state, { 'font-size': 20, fill: colors.blue });
  }

  function drawWebLayers(svg, current) {
    const s = current.state;
    label(svg, 210, 27, 'One button, three responsibilities', { 'font-size': 23 });
    [['HTML', 'button type="button"', colors.blue], ['CSS', 'Background: ' + s.theme, colors.gold], ['JavaScript', s.enabled ? 'click → (count + 1) % 10' : 'Counter handler off', colors.teal]].forEach(([name, text, color], i) => {
      const y = 51 + i * 80;
      svg.append(svgElement('rect', { x: 36, y, width: 348, height: 65, rx: 8, fill: color, 'fill-opacity': .08, stroke: color }));
      label(svg, 210, y + 24, name, { 'font-size': 21, fill: color });
      label(svg, 210, y + 51, text, { 'font-size': 20 });
    });
    label(svg, 210, 312, 'Current count: ' + s.count, { 'font-size': 26, fill: colors.teal });
    label(svg, 210, 341, 'Try the working button below', { 'font-size': 18 });
  }

  function drawWebVisit(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'A fictional HTTPS visit', { 'font-size': 25 });
    d.events.forEach((event, i) => {
      const y = 49 + i * 45;
      svg.append(svgElement('rect', { x: 24, y, width: 372, height: 35, rx: 6, fill: colors.blue, 'fill-opacity': i <= s.stage ? .08 : .025, stroke: i === s.stage ? colors.gold : colors.blue, 'stroke-width': i === s.stage ? 2 : 1, 'stroke-opacity': i <= s.stage ? .8 : .2 }));
      label(svg, 210, y + 24, i + '. ' + event, { 'font-size': 19, opacity: i <= s.stage ? 1 : .45 });
    });
    label(svg, 210, 294, 'Address: ' + (d.address || 'not yet obtained'), { 'font-size': 21 });
    label(svg, 210, 331, 'DNS: ' + d.dnsQueries + ' · GET: ' + d.requests + ' · response: ' + d.responses, { 'font-size': 21 });
  }

  function drawCpuSchedule(svg, current) {
    const s = current.state, d = current.data, palette = { A: colors.blue, B: colors.plum, C: colors.gold };
    label(svg, 210, 27, 'One CPU · all jobs arrive at 0', { 'font-size': 23 });
    label(svg, 210, 57, s.policy === 'rr' ? 'Round robin · quantum ' + s.quantum : 'First come, first served', { 'font-size': 21 });
    d.timeline.forEach((id, i) => {
      svg.append(svgElement('rect', { x: 40 + i * 34, y: 82, width: 33, height: 38, fill: palette[id], 'fill-opacity': .16, stroke: palette[id] }));
      label(svg, 56.5 + i * 34, 109, id, { 'font-size': 23, fill: palette[id] });
    });
    for (let i = 0; i <= 10; i++) label(svg, 40 + i * 34, 145, String(i), { 'font-size': 16 });
    ['Job', 'First', 'Finish', 'Wait'].forEach((text, i) => label(svg, [65, 159, 252, 345][i], 187, text, { 'font-size': 20 }));
    d.jobs.forEach((job, row) => {
      line(svg, 33, 199 + row * 36, 386, 199 + row * 36, { opacity: .15 });
      [job.id, job.first, job.completion, job.waiting].forEach((value, col) => label(svg, [65, 159, 252, 345][col], 224 + row * 36, String(value), { 'font-size': 22, fill: palette[job.id] }));
    });
    label(svg, 210, 336, '10 work units · ' + d.switches + ' job switches', { 'font-size': 22 });
  }

  function drawAtomicTransfer(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'Preserve A + B = 10 counters', { 'font-size': 24 });
    [['Before', 8, 2, 48, colors.blue], ['After', d.finalA, d.finalB, 223, colors.teal]].forEach(([name, a, b, y, color]) => {
      [[35, 'A', a], [225, 'B', b]].forEach(([x, id, value]) => {
        svg.append(svgElement('rect', { x, y, width: 160, height: 59, rx: 7, fill: color, 'fill-opacity': .08, stroke: color }));
        label(svg, x + 80, y + 23, name + ' ' + id, { 'font-size': 18 });
        label(svg, x + 80, y + 48, String(value), { 'font-size': 25, fill: color });
      });
    });
    label(svg, 210, 140, '1. Subtract ' + s.amount + ' from A → ' + d.pendingA, { 'font-size': 21 });
    label(svg, 210, 174, s.failure ? 'Interrupted: credit not executed' : '2. Add ' + s.amount + ' to B → ' + d.pendingB, { 'font-size': 21, fill: s.failure ? colors.coral : colors.ink });
    label(svg, 210, 207, d.rolledBack ? 'Roll back the uncommitted debit' : s.atomic ? 'Commit both writes' : 'Each write is independent', { 'font-size': 19 });
    label(svg, 210, 314, d.outcome, { 'font-size': 22, fill: s.failure ? colors.coral : colors.teal });
    label(svg, 210, 343, 'Final total: ' + d.total, { 'font-size': 21 });
  }

  function drawThreeWayMerge(svg, current) {
    const d = current.data;
    label(svg, 210, 27, 'Compare each branch with the base', { 'font-size': 22 });
    [['Base', d.base], ['Left', d.left], ['Right', d.right], ['Merge', d.merged]].forEach(([name, values], col) => {
      const x = 24 + col * 95, color = col === 3 ? colors.teal : colors.blue;
      label(svg, x + 41, 65, name, { 'font-size': 21, fill: color });
      values.forEach((value, row) => {
        const y = 83 + row * 57, cellColor = value === null ? colors.coral : color;
        svg.append(svgElement('rect', { x, y, width: 82, height: 43, rx: 6, fill: cellColor, 'fill-opacity': .08, stroke: cellColor, 'stroke-opacity': .5 }));
        label(svg, x + 41, y + 29, (row + 1) + ': ' + (value === null ? '?' : value), { 'font-size': 23, fill: cellColor });
      });
    });
    label(svg, 210, 274, d.conflicts.length ? 'Conflicting line: ' + d.conflicts.join(', ') : 'Changes combine without conflict', { 'font-size': 21 });
    label(svg, 210, 310, d.unresolved ? 'Unresolved — choose a version' : 'Result: ' + d.merged.join(' · '), { 'font-size': 23, fill: d.unresolved ? colors.coral : colors.teal });
    label(svg, 210, 340, 'A clean merge still needs tests and review', { 'font-size': 17 });
  }

  function drawObjectState(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 26, 'Classes define methods', { 'font-size': 23 });
    [[35, 'Score', 'score() → points', colors.blue], [225, 'BonusScore', 'score() → points + 3', colors.plum]].forEach(([x, name, method, color]) => {
      svg.append(svgElement('rect', { x, y: 47, width: 160, height: 79, rx: 7, fill: color, 'fill-opacity': .08, stroke: color }));
      label(svg, x + 80, 75, name, { 'font-size': 20, fill: color });
      label(svg, x + 80, 104, method, { 'font-size': 15 });
    });
    label(svg, 210, 157, 'BonusScore extends Score', { 'font-size': 21 });
    label(svg, 210, 188, 'Instances hold separate fields', { 'font-size': 21 });
    [[35, 'A', d.firstClass, s.first, d.firstScore, s.boosted ? colors.plum : colors.blue], [225, 'B', 'Score', s.second, d.secondScore, colors.blue]].forEach(([x, name, type, points, result, color]) => {
      svg.append(svgElement('rect', { x, y: 203, width: 160, height: 110, rx: 7, fill: color, 'fill-opacity': .06, stroke: color }));
      label(svg, x + 80, 228, name + ': ' + type, { 'font-size': 19, fill: color });
      label(svg, x + 80, 259, 'points = ' + points, { 'font-size': 20 });
      label(svg, x + 80, 291, 'score() → ' + result, { 'font-size': 20, fill: colors.teal });
    });
    label(svg, 210, 340, 'Returning a bonus does not change points', { 'font-size': 17 });
  }

  function drawFullAdder(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 27, 'Full adder: a=' + s.a + ', b=' + s.b + ', c=' + s.carry, { 'font-size': 24 });
    const rows = [['x = a XOR b', s.a + ' XOR ' + s.b, d.x], ['p = a AND b', s.a + ' AND ' + s.b, d.p], ['q = x AND c', d.x + ' AND ' + s.carry, d.q], ['sum = x XOR c', d.x + ' XOR ' + s.carry, d.sum], ['carry = p OR q', d.p + ' OR ' + d.q, d.carryOut]];
    rows.forEach(([name, expression, result], i) => {
      const y = 48 + i * 43, color = i < 3 ? colors.blue : colors.teal;
      svg.append(svgElement('rect', { x: 25, y, width: 370, height: 35, rx: 6, fill: color, 'fill-opacity': .08, stroke: color, 'stroke-opacity': .3 }));
      label(svg, 37, y + 24, name, { 'font-size': 18, 'text-anchor': 'start' });
      label(svg, 298, y + 24, expression + ' = ' + result, { 'font-size': 18, fill: color });
    });
    label(svg, 210, 294, 'Binary result: ' + d.carryOut + d.sum, { 'font-size': 27, fill: colors.teal });
    label(svg, 210, 330, '2 × ' + d.carryOut + ' + ' + d.sum + ' = ' + d.total + ' in decimal', { 'font-size': 22 });
  }

  function drawSearchChecks(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 27, 'Sorted list: 1…' + s.size + ' · target ' + s.target, { 'font-size': 23 });
    [['Linear', d.linear.length, colors.blue], ['Binary', d.binary.length, colors.teal]].forEach(([name, count, color], i) => {
      const y = 58 + i * 45;
      label(svg, 28, y + 15, name, { 'font-size': 19, 'text-anchor': 'start' });
      line(svg, 105, y + 11, 329, y + 11, { stroke: color, opacity: .2 });
      svg.append(svgElement('rect', { x: 105, y, width: count * 7, height: 22, rx: 3, fill: color }));
      label(svg, 374, y + 17, String(count), { 'font-size': 21, fill: color });
    });
    label(svg, 210, 158, 'Binary: candidate interval → probe', { 'font-size': 20 });
    d.binary.forEach((row, i) => label(svg, 210, 184 + i * 22, row.low + '…' + row.high + ' → ' + row.value, { 'font-size': 18 }));
    label(svg, 210, 333, d.binaryFound ? 'Found ' + s.target : 'Target not present', { 'font-size': 23, fill: colors.teal });
  }

  function drawMergeSort(svg, current) {
    const s = current.state, d = current.data;
    const rows = [[d.source], [d.source.slice(0, 2), d.source.slice(2)], d.source.map(item => [item]), [d.left, d.right], [d.result]];
    label(svg, 210, 25, 'Merge sort · ' + d.shownComparisons + ' comparisons', { 'font-size': 22 });
    rows.forEach((groups, i) => {
      const y = 45 + i * 51, available = i <= s.stage;
      const width = groups.length === 4 ? 78 : groups.length === 2 ? 166 : 350;
      groups.forEach((group, j) => {
        const x = groups.length === 4 ? 30 + j * 94 : groups.length === 2 ? 35 + j * 184 : 35;
        svg.append(svgElement('rect', { x, y, width, height: 35, rx: 6, fill: i >= 2 ? colors.teal : colors.blue, 'fill-opacity': available ? .09 : .025, stroke: i === s.stage ? colors.gold : colors.blue, 'stroke-opacity': available ? .8 : .2, 'stroke-width': i === s.stage ? 2 : 1 }));
        label(svg, x + width / 2, y + 24, available ? group.map(item => item.value + String.fromCharCode(65 + item.id)).join('  ') : '…', { 'font-size': groups.length === 4 ? 18 : 20, fill: available && i >= 2 ? colors.teal : colors.blue });
      });
      if (i < 4) line(svg, 210, y + 38, 210, y + 47, { opacity: .35 });
    });
    label(svg, 210, 319, d.label, { 'font-size': 21 });
    label(svg, 210, 343, 'A–D identify original items, including ties', { 'font-size': 16 });
  }

  function drawBlockBranch(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'A sequence with one decision', { 'font-size': 23 });
    const blocks = [['Start: position = 0', colors.ink], ['Repeat ' + s.repeats + ' times: move 1', colors.blue], ['If position = ' + s.star + ': jump ' + s.jump, colors.gold]];
    blocks.forEach(([text, color], i) => {
      svg.append(svgElement('rect', { x: 42, y: 46 + i * 47, width: 336, height: 38, rx: 8, fill: color, 'fill-opacity': .09, stroke: color }));
      label(svg, 210, 71 + i * 47, text, { 'font-size': 20 });
    });
    label(svg, 210, 209, 'After loop: ' + d.before + ' · condition ' + truthText(d.matched), { 'font-size': 20 });
    const x = n => 35 + n * 50;
    line(svg, 35, 264, 385, 264, { stroke: colors.ink });
    for (let n = 0; n <= 7; n++) {
      svg.append(svgElement('circle', { cx: x(n), cy: 264, r: 6, fill: n <= d.before ? colors.blue : colors.paper, stroke: colors.blue }));
      label(svg, x(n), 290, String(n), { 'font-size': 18 });
    }
    svg.append(svgElement('path', { d: 'M' + x(s.star) + ' 229 l-9 16 h18 Z', fill: colors.gold }));
    svg.append(svgElement('circle', { cx: x(d.position), cy: 264, r: 12, fill: 'none', stroke: colors.teal, 'stroke-width': 3 }));
    label(svg, 210, 328, 'Final position: ' + d.position + (d.matched ? ' · jump taken' : ' · jump skipped'), { 'font-size': 22, fill: colors.teal });
  }

  function drawProgramTrace(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'One loop, changing state', { 'font-size': 24 });
    ['total = 0', 'for value in [2, 5, 8]:', 'if value > ' + s.threshold + ':', 'total += value'].forEach((text, i) => label(svg, 32 + [0, 0, 28, 56][i], 61 + i * 26, text, { 'font-size': 19, 'font-family': 'monospace', 'text-anchor': 'start' }));
    ['Value', 'Decision', 'Total after'].forEach((text, i) => label(svg, [67, 205, 340][i], 185, text, { 'font-size': 18 }));
    line(svg, 28, 194, 392, 194, { stroke: colors.blue, opacity: .4 });
    d.trace.forEach((row, i) => {
      const color = !row.completed ? colors.blue : row.accepted ? colors.teal : colors.coral;
      svg.append(svgElement('rect', { x: 28, y: 201 + i * 35, width: 364, height: 31, rx: 5, fill: color, 'fill-opacity': row.completed ? .1 : .035 }));
      [String(row.value), !row.completed ? 'Pending' : row.accepted ? 'Add' : 'Skip', row.total === null ? '—' : String(row.total)].forEach((text, col) => label(svg, [67, 205, 340][col], 223 + i * 35, text, { 'font-size': 20, fill: color, opacity: row.completed ? 1 : .6 }));
    });
    label(svg, 210, 334, s.iterations + '/3 iterations · total = ' + d.total, { 'font-size': 23 });
  }

  function drawComputerParts(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'Input → memory → processor → output', { 'font-size': 20 });
    const rows = [['Input', s.input], ['Working memory', d.memory], ['Processor result', d.processor], ['Display', d.output]];
    rows.forEach(([name, value], i) => {
      const y = 49 + i * 62;
      svg.append(svgElement('rect', { x: 35, y, width: 350, height: 47, rx: 7, fill: colors.blue, 'fill-opacity': value === null ? .025 : .08, stroke: i === s.step ? colors.gold : colors.blue, 'stroke-width': i === s.step ? 3 : 1, 'stroke-opacity': i === s.step ? 1 : .4 }));
      label(svg, 52, y + 30, name, { 'font-size': 20, 'text-anchor': 'start' });
      label(svg, 348, y + 31, value === null ? '—' : String(value), { 'font-size': 25, fill: colors.blue });
      if (i < 3) svg.append(svgElement('path', { d: 'M210 ' + (y + 49) + ' V' + (y + 60) + ' M206 ' + (y + 55) + ' L210 ' + (y + 60) + ' L214 ' + (y + 55), fill: 'none', stroke: colors.ink, 'stroke-width': 2 }));
    });
    label(svg, 210, 311, 'Instruction: ' + (s.operation === 'double' ? 'double' : 'add one'), { 'font-size': 22 });
    label(svg, 210, 338, '— means not yet available, not zero', { 'font-size': 18 });
  }

  function drawQueryResult(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'Filter rows → order the result', { 'font-size': 24 });
    label(svg, 210, 58, 'score ≥ ' + s.minimum + ' · ' + (s.group === 'all' ? 'all groups' : 'group ' + s.group) + ' · ' + (s.descending ? 'high to low' : 'low to high'), { 'font-size': 18 });
    [[d.rows, 16, 'Source', colors.blue], [d.result, 228, 'Result', colors.teal]].forEach(([rows, x, title, color]) => {
      label(svg, x + 87, 93, title, { 'font-size': 21, fill: color });
      svg.append(svgElement('rect', { x, y: 105, width: 176, height: 177, rx: 6, fill: color, 'fill-opacity': .055, stroke: color, 'stroke-opacity': .5 }));
      svg.append(svgElement('line', { x1: x + 8, x2: x + 168, y1: 133, y2: 133, stroke: color, 'stroke-opacity': .35 }));
      ['Name', 'Grp', 'Score'].forEach((heading, i) => label(svg, x + [31, 88, 142][i], 126, heading, { 'font-size': 16 }));
      rows.forEach((row, i) => [row.name, row.group, row.score].forEach((value, col) => label(svg, x + [31, 88, 142][col], 150 + i * 24, String(value), { 'font-size': 18 })));
      if (!rows.length) label(svg, x + 88, 194, 'No matching rows', { 'font-size': 17, fill: color });
    });
    label(svg, 210, 310, '6 stored · ' + d.result.length + ' returned', { 'font-size': 23 });
    label(svg, 210, 337, 'Ties: original ID ascending', { 'font-size': 18 });
  }

  function drawTypedAddition(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 29, 'Type changes what + does', { 'font-size': 25 });
    [[s.leftType, d.leftLiteral, 110], [s.rightType, d.rightLiteral, 310]].forEach(([type, literal, x]) => {
      const color = type === 'number' ? colors.blue : colors.plum;
      svg.append(svgElement('rect', { x: x - 70, y: 65, width: 140, height: 95, rx: 9, fill: color, 'fill-opacity': .1, stroke: color, 'stroke-width': 2 }));
      label(svg, x, 94, type === 'number' ? 'integer' : 'string', { 'font-size': 20, fill: color });
      label(svg, x, 137, literal, { 'font-size': 31 });
    });
    label(svg, 210, 124, '+', { 'font-size': 30 });
    label(svg, 210, 197, d.valid ? 'Result' : 'No result value', { 'font-size': 21 });
    svg.append(svgElement('rect', { x: 65, y: 213, width: 290, height: 60, rx: 8, fill: d.valid ? colors.teal : colors.coral, 'fill-opacity': .1, stroke: d.valid ? colors.teal : colors.coral }));
    label(svg, 210, 253, d.output, { 'font-size': 30, fill: d.valid ? colors.teal : colors.coral });
    label(svg, 210, 307, !d.valid ? 'Mixed types need an explicit decision' : s.leftType === 'number' ? 'Arithmetic: add quantities' : 'Concatenation: join characters', { 'font-size': 20 });
    label(svg, 210, 335, 'Python-style rules · no implicit conversion', { 'font-size': 17 });
  }

  function drawBoundaryDebugging(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'Goal: sum 1 through n', { 'font-size': 25 });
    svg.append(svgElement('rect', { x: 29, y: 45, width: 362, height: 105, rx: 8, fill: colors.ink, 'fill-opacity': .055 }));
    label(svg, 51, 72, 'sum = 0', { 'font-size': 21, 'text-anchor': 'start' });
    label(svg, 51, 104, 'for i = 1; i ' + (s.fixed ? '≤' : '<') + ' n; i = i + 1', { 'font-size': 21, 'text-anchor': 'start', fill: s.fixed ? colors.teal : colors.coral });
    label(svg, 71, 135, 'sum = sum + i', { 'font-size': 21, 'text-anchor': 'start' });
    label(svg, 210, 179, 'Trace for n = ' + s.n, { 'font-size': 21 });
    if (!d.trace.length) label(svg, 210, 224, 'No iterations · sum stays 0', { 'font-size': 21 });
    d.trace.forEach((row, i) => {
      const x = 54 + i * 62;
      svg.append(svgElement('rect', { x: x - 25, y: 193, width: 50, height: 65, rx: 5, fill: colors.blue, 'fill-opacity': .09 }));
      label(svg, x, 217, 'i=' + row.i, { 'font-size': 17 });
      label(svg, x, 246, String(row.total), { 'font-size': 20, fill: colors.blue });
    });
    label(svg, 210, 283, 'Expected ' + d.expected + ' · actual ' + d.total, { 'font-size': 23 });
    label(svg, 210, 311, d.passes ? 'This input passes' : 'This input fails', { 'font-size': 21, fill: d.passes ? colors.teal : colors.coral });
    label(svg, 210, 337, 'Test suite: ' + d.cases.filter(row => row.expected === row.actual).length + '/7 pass', { 'font-size': 18 });
  }

  function drawFunctionCalls(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, 'One definition: f(n)', { 'font-size': 25 });
    svg.append(svgElement('rect', { x: 54, y: 43, width: 312, height: 43, rx: 7, fill: colors.ink, 'fill-opacity': .06 }));
    label(svg, 210, 72, d.body, { 'font-size': 23 });
    [[s.first, d.firstResult, 'A'], [s.second, d.secondResult, 'B']].forEach(([argument, result, name], i) => {
      const y = 137 + i * 100;
      label(svg, 210, y - 27, 'Call ' + name + ': f(' + argument + ')', { 'font-size': 20 });
      svg.append(svgElement('rect', { x: 30, y: y - 10, width: 160, height: 46, rx: 7, fill: colors.blue, 'fill-opacity': .1, stroke: colors.blue }));
      label(svg, 110, y + 19, 'local n = ' + argument, { 'font-size': 21 });
      svg.append(svgElement('path', { d: 'M199 ' + (y + 13) + ' H220 M214 ' + (y + 7) + ' L220 ' + (y + 13) + ' L214 ' + (y + 19), fill: 'none', stroke: colors.ink, 'stroke-width': 2 }));
      svg.append(svgElement('rect', { x: 230, y: y - 10, width: 160, height: 46, rx: 7, fill: colors.teal, 'fill-opacity': .1, stroke: colors.teal }));
      label(svg, 310, y + 19, 'returns ' + result, { 'font-size': 21 });
    });
    label(svg, 210, 322, 'Same code · separate local values', { 'font-size': 21 });
  }

  function drawEarlyComputing(svg, current, id) {
    const s = current.state, d = current.data, palette = [colors.blue, colors.gold, colors.plum];
    function token(x, y, shape, color, radius) {
      if (shape === 0) svg.append(svgElement('circle', { cx: x, cy: y, r: radius, fill: palette[color] }));
      else if (shape === 1) svg.append(svgElement('rect', { x: x - radius, y: y - radius, width: 2 * radius, height: 2 * radius, rx: 2, fill: palette[color] }));
      else svg.append(svgElement('path', { d: 'M' + x + ' ' + (y - radius) + ' L' + (x + radius) + ' ' + (y + radius) + ' H' + (x - radius) + 'Z', fill: palette[color] }));
    }
    if (id === 'cs.0.sorting') {
      label(svg, 210, 30, 'Sort by ' + { size: 'size', color: 'colour', shape: 'shape' }[s.rule], { 'font-size': 25 });
      label(svg, 210, 62, 'Original collection', { 'font-size': 20 });
      label(svg, 210, 167, 'Sorted group → waiting objects', { 'font-size': 20 });
      if (s.count) svg.append(svgElement('rect', { x: 22, y: 185, width: s.count * 62, height: 80, rx: 8, fill: colors.gold, 'fill-opacity': .05, stroke: colors.gold, 'stroke-width': 2 }));
      [d.items, d.output].forEach((items, row) => items.forEach((item, i) => {
        const x = 53 + i * 62, y = 101 + row * 116;
        token(x, y, item.shape, item.color, 8 + item.size * 4);
        label(svg, x, y + 37, item.id, { 'font-size': 18 });
      }));
      label(svg, 210, 299, s.count + ' of 6 included · none added or lost', { 'font-size': 20 });
      label(svg, 210, 331, { size: 'Small → medium → large', color: 'Blue → gold → plum', shape: 'Circle → square → triangle' }[s.rule], { 'font-size': 20 });
    } else {
      label(svg, 210, 30, 'Repeat ' + s.unit + ' × ' + s.repeats, { 'font-size': 25 });
      label(svg, 210, 62, 'The unit', { 'font-size': 20 });
      const drawLetter = (letter, x, y) => { const n = 'ABC'.indexOf(letter); token(x, y, n, n, 13); label(svg, x, y + 33, letter, { 'font-size': 18 }); };
      s.unit.split('').forEach((letter, i) => drawLetter(letter, 210 + (i - (s.unit.length - 1) / 2) * 48, 94));
      label(svg, 210, 161, 'The repeated pattern', { 'font-size': 20 });
      for (let copy = 0; copy < s.repeats; copy++) {
        const start = copy * s.unit.length, row = Math.floor(start / 6), col = start % 6;
        svg.append(svgElement('rect', { x: 23 + col * 62, y: 178 + row * 66, width: s.unit.length * 62 - 4, height: 61, rx: 6, fill: colors.ink, 'fill-opacity': .04, stroke: colors.ink, 'stroke-opacity': .18 }));
      }
      d.sequence.forEach((letter, i) => drawLetter(letter, 52 + (i % 6) * 62, 197 + Math.floor(i / 6) * 66));
      label(svg, 210, 334, d.length + ' symbols · next: ' + d.next, { 'font-size': 22 });
    }
  }

  function drawBondingCarriers(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 29, { salt: 'Ionic salt', copper: 'Metallic copper', iodine: 'Molecular iodine' }[s.material] + ' · ' + (s.liquid ? 'liquid' : 'solid'), { 'font-size': 24 });
    label(svg, 210, 60, s.field ? 'Electric field →' : 'No applied electric field', { 'font-size': 21 });
    svg.append(svgElement('rect', { x: 42, y: 87, width: 336, height: 175, rx: 10, fill: colors.ink, 'fill-opacity': .035, stroke: colors.ink, 'stroke-opacity': .2 }));
    for (let i = 0; i < 6; i++) {
      const x = 108 + (i % 3) * 100, y = 132 + Math.floor(i / 3) * 85, positive = i % 2 === 0;
      if (s.material === 'iodine') {
        svg.append(svgElement('line', { x1: x - 13, y1: y, x2: x + 13, y2: y, stroke: colors.plum, 'stroke-width': 3 }));
        for (const dx of [-13, 13]) { svg.append(svgElement('circle', { cx: x + dx, cy: y, r: 12, fill: colors.paper, stroke: colors.plum, 'stroke-width': 2 })); label(svg, x + dx, y + 6, 'I', { 'font-size': 17, fill: colors.plum }); }
      } else {
        const shift = s.material === 'salt' ? (positive ? d.drift : -d.drift) : 0;
        if (shift) svg.append(svgElement('circle', { cx: x, cy: y, r: 19, fill: 'none', stroke: colors.ink, 'stroke-dasharray': '3 3', 'stroke-opacity': .3 }));
        svg.append(svgElement('circle', { cx: x + shift, cy: y, r: 19, fill: colors.paper, stroke: s.material === 'copper' || positive ? colors.blue : colors.plum, 'stroke-width': 2 }));
        label(svg, x + shift, y + 7, s.material === 'copper' || positive ? '+' : '−', { 'font-size': 23 });
        if (s.material === 'copper') svg.append(svgElement('circle', { cx: x + 25 - d.drift, cy: y + 27, r: 5, fill: colors.gold }));
      }
    }
    label(svg, 210, 293, d.mobile ? 'Mobile carriers: ' + d.carrier : 'No mobile charge carriers', { 'font-size': 22 });
    label(svg, 210, 326, d.conducting ? 'Directed charge drift → current' : 'No directed charge drift', { 'font-size': 21 });
  }

  function drawCoordinationLedger(svg, current) {
    const s = current.state, d = current.data, cx = 210, cy = 173;
    label(svg, 210, 29, 'Coordination number: 6', { 'font-size': 24 });
    label(svg, 210, 59, d.ligandCount + ' ligands · charge ' + (d.charge > 0 ? '+' : '') + d.charge, { 'font-size': 21 });
    const points = Array.from({ length: 6 }, (_, i) => { const a = (-90 + i * 60) * Math.PI / 180; return [cx + 74 * Math.cos(a), cy + 74 * Math.sin(a)]; });
    for (let pair = 0; pair < s.chelates; pair++) {
      const a = points[pair * 2], b = points[pair * 2 + 1], angle = (-60 + pair * 120) * Math.PI / 180;
      svg.append(svgElement('path', { d: 'M' + a.join(' ') + ' Q' + (cx + 145 * Math.cos(angle)) + ' ' + (cy + 145 * Math.sin(angle)) + ' ' + b.join(' '), fill: 'none', stroke: colors.plum, 'stroke-width': 4 }));
    }
    points.forEach(([x, y], i) => {
      const chelated = i < s.chelates * 2, color = chelated ? colors.plum : colors.blue;
      svg.append(svgElement('line', { x1: cx, y1: cy, x2: x, y2: y, stroke: color, 'stroke-width': 2 }));
      svg.append(svgElement('circle', { cx: x, cy: y, r: 17, fill: colors.paper, stroke: color, 'stroke-width': 2 }));
      label(svg, x, y + 7, chelated || s.mono === 'ammonia' ? 'N' : 'Cl', { 'font-size': 20, fill: color });
    });
    svg.append(svgElement('circle', { cx, cy, r: 24, fill: colors.gold }));
    label(svg, cx, cy + 8, 'M', { 'font-size': 25 });
    label(svg, 210, 294, s.chelates + ' × 2 + ' + d.monodentate + ' × 1 = 6 donors', { 'font-size': 21 });
    label(svg, 210, 329, 'Charge: +' + s.oxidation + ' + (' + d.ligandCharge + ') = ' + (d.charge > 0 ? '+' : '') + d.charge, { 'font-size': 20 });
  }

  function drawAlkaneConnections(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 30, 'C' + s.carbons + 'H' + d.hydrogens + ' · ' + (s.branched ? 'branched' : 'unbranched'), { 'font-size': 25 });
    label(svg, 210, 61, 'Count bonds, not bends in the drawing', { 'font-size': 19 });
    const points = Array.from({ length: d.backbone }, (_, i) => [50 + i * 320 / (d.backbone - 1), i % 2 ? 139 : 174]);
    if (s.branched) points.push([points[1][0], 246]);
    d.edges.forEach(([a, b]) => svg.append(svgElement('line', { x1: points[a][0], y1: points[a][1], x2: points[b][0], y2: points[b][1], stroke: colors.ink, 'stroke-width': 3 })));
    points.forEach(([x, y], i) => {
      svg.append(svgElement('rect', { x: x - 22, y: y - 15, width: 44, height: 30, rx: 6, fill: colors.paper }));
      label(svg, x, y + 7, d.hydrogenCounts[i] === 1 ? 'CH' : d.hydrogenCounts[i] === 2 ? 'CH₂' : 'CH₃', { 'font-size': 22, fill: d.degree[i] === 3 ? colors.gold : colors.blue });
    });
    label(svg, 210, 298, (s.carbons - 1) + ' C–C bonds + ' + d.hydrogens + ' C–H bonds', { 'font-size': 21 });
    label(svg, 210, 332, 'Every carbon: 4 bonds in total', { 'font-size': 21 });
  }

  function drawReactionAccounting(svg, current, id) {
    const d = current.data;
    if (id === 'chem.2.reactions-intro') {
      label(svg, 210, 29, 'Balance: ' + numberText(d.reading) + ' g', { 'font-size': 26 });
      label(svg, 210, 59, current.state.closed ? 'Produced gas stays inside' : 'Produced gas leaves the boundary', { 'font-size': 20 });
      const parts = [{ name: 'Non-gas', value: d.nongas, color: colors.blue }, { name: 'Gas inside', value: d.retained, color: colors.gold }, { name: 'Gas outside', value: d.escaped, color: colors.plum }];
      parts.forEach((part, i) => {
        const y = 96 + i * 54;
        label(svg, 24, y + 16, part.name, { 'font-size': 17, 'text-anchor': 'start' });
        svg.append(svgElement('rect', { x: 139, y, width: 184, height: 22, rx: 3, fill: colors.ink, 'fill-opacity': .07 }));
        svg.append(svgElement('rect', { x: 139, y, width: part.value * 1.84, height: 22, fill: part.color }));
        label(svg, 393, y + 17, numberText(part.value) + ' g', { 'font-size': 17, 'text-anchor': 'end' });
      });
      label(svg, 210, 269, 'All bars use the same 0–100 g scale', { 'font-size': 18 });
      label(svg, 210, 308, numberText(d.reading) + ' g inside + ' + numberText(d.escaped) + ' g outside', { 'font-size': 21 });
      label(svg, 210, 337, '= 100 g accounted for', { 'font-size': 21 });
    } else {
      label(svg, 210, 29, 'Zn + Cu²⁺ → Zn²⁺ + Cu', { 'font-size': 25 });
      const species = [{ name: 'Zn (metal)', count: d.zinc, color: colors.blue }, { name: 'Zn²⁺ (ions)', count: d.zincIon, color: colors.teal },
        { name: 'Cu²⁺ (ions)', count: d.copperIon, color: colors.teal }, { name: 'Cu (metal)', count: d.copper, color: colors.blue }];
      species.forEach((item, row) => {
        const y = 72 + row * 46;
        label(svg, 22, y + 8, item.name, { 'font-size': 20, 'text-anchor': 'start' });
        for (let i = 0; i < 4; i++) svg.append(svgElement('circle', { cx: 190 + i * 43, cy: y, r: 13, fill: i < item.count ? item.color : colors.paper, stroke: item.color, 'stroke-width': 2 }));
        label(svg, 379, y + 7, String(item.count), { 'font-size': 20 });
      });
      label(svg, 210, 268, 'Zn: loses ' + d.electrons + ' e⁻ · Cu²⁺: gains ' + d.electrons + ' e⁻', { 'font-size': 21, fill: colors.gold });
      label(svg, 210, 301, '4 Zn atoms + 4 Cu atoms throughout', { 'font-size': 20 });
      label(svg, 210, 332, 'Ion charge total: +8 throughout', { 'font-size': 19 });
    }
  }

  function drawPeriodicPattern(svg, current) {
    const d = current.data, selected = d.selected, x = column => 48 + column * 46;
    label(svg, 210, 29, selected.name + ' · Z = ' + selected.z, { 'font-size': 24 });
    label(svg, 210, 59, 'First 18 elements · main groups', { 'font-size': 20 });
    [1, 2, 13, 14, 15, 16, 17, 18].forEach((group, i) => label(svg, x(i), 93, String(group), { 'font-size': 15 }));
    for (let period = 1; period <= 3; period++) label(svg, 13, 130 + (period - 1) * 49, String(period), { 'font-size': 15 });
    d.elements.forEach(atom => {
      const cx = x(atom.column), y = 103 + (atom.period - 1) * 49;
      const color = atom.z === selected.z ? colors.gold : atom.group === selected.group ? colors.teal : colors.ink;
      svg.append(svgElement('rect', { x: cx - 20, y, width: 40, height: 43, rx: 4, fill: color, 'fill-opacity': atom.z === selected.z ? .35 : atom.group === selected.group ? .17 : .04, stroke: color, 'stroke-opacity': .6 }));
      label(svg, cx - 12, y + 13, String(atom.z), { 'font-size': 11 });
      label(svg, cx, y + 34, atom.symbol, { 'font-size': 22 });
    });
    label(svg, 210, 277, 'Period ' + selected.period + ' · Group ' + selected.group, { 'font-size': 20 });
    label(svg, 210, 308, 'Electrons by shell: ' + selected.shells.join(' | '), { 'font-size': 22 });
    label(svg, 210, 335, selected.z === 2 ? 'Helium: full first shell, only 2 electrons' : selected.outer + ' electron' + (selected.outer === 1 ? '' : 's') + ' in the outer occupied shell', { 'font-size': 17 });
  }

  function drawAcidityComparison(svg, current) {
    const s = current.state, d = current.data, x = ph => 35 + ph * 25;
    label(svg, 210, 30, 'pH measures a logarithm', { 'font-size': 23 });
    label(svg, 210, 60, 'Lower pH → more hydronium', { 'font-size': 19 });
    svg.append(svgElement('line', { x1: 35, x2: 385, y1: 132, y2: 132, stroke: colors.ink, 'stroke-width': 2 }));
    for (let ph = 0; ph <= 14; ph++) {
      svg.append(svgElement('line', { x1: x(ph), x2: x(ph), y1: 126, y2: 139, stroke: colors.ink }));
      if (!(ph % 2) || ph === 7) label(svg, x(ph), 160, String(ph), { 'font-size': 14 });
    }
    svg.append(svgElement('line', { x1: x(s.ph), x2: x(s.ph), y1: 92, y2: 124, stroke: colors.gold, 'stroke-width': 3 }));
    svg.append(svgElement('circle', { cx: x(s.ph), cy: 116, r: 6, fill: colors.gold }));
    svg.append(svgElement('line', { x1: x(s.reference), x2: x(s.reference), y1: 169, y2: 195, stroke: colors.plum, 'stroke-width': 3 }));
    svg.append(svgElement('circle', { cx: x(s.reference), cy: 179, r: 6, fill: colors.plum }));
    label(svg, 210, 224, 'Sample / reference = 10^(' + d.difference + ')', { 'font-size': 21 });
    label(svg, 210, 253, 'Hydronium activity ratio', { 'font-size': 18 });
    label(svg, 210, 290, 'Sample H₃O⁺: ' + d.hydronium.toExponential(0), { 'font-size': 20 });
    label(svg, 210, 321, 'Sample OH⁻: ' + d.hydroxide.toExponential(0), { 'font-size': 20 });
  }

  function drawMaterials(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'chem.0.materials') {
      label(svg, 210, 34, 'Object: ' + s.object, { 'font-size': 25 });
      const fill = s.material === 'wood' ? colors.gold : s.material === 'steel' ? colors.blue : colors.coral;
      const shape = s.object === 'spoon' ? 'M180 139 C133 125 144 69 182 64 C224 59 252 85 235 117 C230 128 221 134 218 139 L223 273 Q200 293 182 273Z' :
        s.object === 'cup' ? 'M120 98 H275 V128 H301 Q340 132 334 181 Q330 213 275 210 V270 H120Z M275 151 V186 Q307 190 308 166 Q309 147 275 151Z' :
          'M210 72 A100 100 0 1 1 209.99 72Z M188 142 A10 10 0 1 0 188.01 142Z M230 142 A10 10 0 1 0 230.01 142Z M188 185 A10 10 0 1 0 188.01 185Z M230 185 A10 10 0 1 0 230.01 185Z';
      svg.append(svgElement('path', { d: shape, fill, 'fill-rule': 'evenodd', stroke: colors.ink, 'stroke-width': 2 }));
      if (s.material === 'wood') for (let i = 0; i < 4; i++) svg.append(svgElement('path', { d: 'M' + (191 + i * 5) + ' 208 Q' + (187 + i * 5) + ' 229 ' + (193 + i * 5) + ' 253', fill: 'none', stroke: colors.ink, 'stroke-opacity': .3 }));
      if (s.material === 'steel') svg.append(svgElement('path', { d: s.object === 'cup' ? 'M135 115 L190 115 L145 140Z' : 'M172 99 L210 83 L195 119Z', fill: '#fff', opacity: .5 }));
      label(svg, 210, 324, 'Material: ' + (s.material === 'steel' ? 'stainless steel' : s.material === 'plastic' ? 'opaque plastic' : 'wood'), { 'font-size': 23 });
    } else if (id === 'chem.1.materials-props') {
      label(svg, 210, 29, 'Choose needs · compare samples', { 'font-size': 21 });
      ['Clear', 'Bends', 'Rain'].forEach((name, i) => {
        label(svg, 236 + i * 65, 62, name, { 'font-size': 16 });
        label(svg, 236 + i * 65, 83, d.requirements[i] ? 'Need' : '—', { 'font-size': 14, fill: colors.teal });
      });
      d.samples.forEach((sample, row) => {
        const y = 102 + row * 48;
        svg.append(svgElement('rect', { x: 12, y, width: 396, height: 43, rx: 5, fill: d.matches[row] ? colors.teal : colors.ink, 'fill-opacity': d.matches[row] ? .15 : .04 }));
        label(svg, 22, y + 27, sample.name, { 'font-size': 17, 'text-anchor': 'start' });
        sample.properties.forEach((value, i) => label(svg, 236 + i * 65, y + 27, value ? 'Yes' : 'No', { 'font-size': 17, fill: value ? colors.teal : colors.coral }));
      });
      const count = d.matches.filter(Boolean).length;
      label(svg, 210, 326, count + ' candidate' + (count === 1 ? '' : 's') + ' · not a final design', { 'font-size': 20 });
    } else {
      label(svg, 210, 26, 'D = ' + d.coefficient.toExponential(2) + ' m²/s', { 'font-size': 22 });
      label(svg, 210, 52, '2√(Dt) = ' + smallLengthText(d.length) + ' µm', { 'font-size': 20 });
      const x = t => 62 + (t - 500) * 310 / 700, y = log => 265 - (log + 24) * 170 / 15;
      for (const tick of [-24, -19, -14, -9]) {
        svg.append(svgElement('line', { x1: 62, x2: 372, y1: y(tick), y2: y(tick), stroke: colors.ink, 'stroke-opacity': .15 }));
        label(svg, 50, y(tick) + 5, String(tick), { 'font-size': 15, 'text-anchor': 'end' });
      }
      label(svg, 210, 79, 'log₁₀[D / (m²/s)]', { 'font-size': 17 });
      svg.append(svgElement('path', { d: d.curve.map((v, i) => (i ? 'L' : 'M') + x(500 + i * 10) + ' ' + y(v)).join(' '), fill: 'none', stroke: colors.teal, 'stroke-width': 3 }));
      svg.append(svgElement('circle', { cx: x(s.temperature), cy: y(d.logCoefficient), r: 6, fill: colors.gold }));
      for (const t of [500, 850, 1200]) label(svg, x(t), 291, String(t), { 'font-size': 16 });
      label(svg, 210, 320, 'Temperature (K)', { 'font-size': 20 });
    }
  }

  function drawPhysicalChemicalChange(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 29, s.process === 'melting' ? 'Same molecules · new arrangement' : 'Same atoms · new molecules', { 'font-size': 21 });
    function atom(x, y, symbol) {
      svg.append(svgElement('circle', { cx: x, cy: y, r: symbol === 'O' ? 13 : 10, fill: symbol === 'O' ? colors.blue : colors.gold }));
      label(svg, x, y + 5, symbol, { fill: '#fff', 'font-size': 14 });
    }
    function molecule(x, y, type) {
      const points = type === 'H₂O' ? [[x, y, 'O'], [x - 20, y + 17, 'H'], [x + 20, y + 17, 'H']] : [[x - 12, y, type === 'H₂' ? 'H' : 'O'], [x + 12, y, type === 'H₂' ? 'H' : 'O']];
      points.slice(1).forEach(p => svg.append(svgElement('line', { x1: points[0][0], y1: points[0][1], x2: p[0], y2: p[1], stroke: colors.ink, 'stroke-width': 3 })));
      points.forEach(p => atom(...p));
    }
    for (const [y, title] of [[52, 'BEFORE: 4 H₂O'], [180, 'AFTER: ' + (s.process === 'melting' ? ['ice', 'partly melted', 'liquid water'][s.stage] : d.water + ' H₂O + ' + d.hydrogen + ' H₂ + ' + d.oxygen + ' O₂')]]) {
      svg.append(svgElement('rect', { x: 15, y, width: 390, height: 111, rx: 9, fill: colors.blue, 'fill-opacity': .06, stroke: colors.blue, 'stroke-opacity': .25 }));
      label(svg, 210, y + 23, title, { 'font-size': 17 });
    }
    for (let i = 0; i < 4; i++) molecule(65 + i * 96, 112, 'H₂O');
    if (s.process === 'melting') {
      for (let i = 0; i < 4; i++) molecule(65 + i * 96 + (s.stage && i % 2 ? -9 : 0), 242 + (i < s.stage * 2 ? (i % 2 ? 12 : -9) : 0), 'H₂O');
    } else {
      const species = [...Array(d.water).fill('H₂O'), ...Array(d.hydrogen).fill('H₂'), ...Array(d.oxygen).fill('O₂')];
      species.forEach((type, i) => molecule(45 + (i + .5) * 330 / species.length, 244, type));
    }
    label(svg, 210, 325, 'Always 8 H atoms + 4 O atoms', { 'font-size': 21 });
  }

  function drawConcentrationCell(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 27, 'Eright − Eleft = ' + numberText(d.voltage * 1000) + ' mV', { 'font-size': 23 });
    label(svg, 210, 57, d.direction === 0 ? 'No net concentration driving force' : 'If connected: electrons ' + (d.direction > 0 ? 'left → right' : 'right → left'), { 'font-size': 19 });
    svg.append(svgElement('path', { d: 'M110 141 V85 H310 V141', fill: 'none', stroke: colors.ink, 'stroke-width': 2 }));
    if (d.direction) svg.append(svgElement('path', { d: d.direction > 0 ? 'M204 78 L218 85 L204 92' : 'M216 78 L202 85 L216 92', fill: 'none', stroke: colors.gold, 'stroke-width': 4 }));
    [110, 310].forEach((x, i) => {
      svg.append(svgElement('rect', { x: x - 65, y: 171, width: 130, height: 74, fill: colors.blue, 'fill-opacity': .14 }));
      svg.append(svgElement('path', { d: 'M' + (x - 65) + ' 136 V245 H' + (x + 65) + ' V136', fill: 'none', stroke: colors.ink, 'stroke-width': 2 }));
      svg.append(svgElement('rect', { x: x - 13, y: 141, width: 26, height: 83, rx: 3, fill: colors.ink, 'fill-opacity': .22, stroke: colors.ink }));
      label(svg, x, 201, 'Zn', { 'font-size': 17 });
      label(svg, x, 272, (i ? d.rightConcentration : d.leftConcentration) + ' M Zn²⁺', { 'font-size': 17 });
      label(svg, x, 301, d.direction === 0 ? 'No net drive' : ((i === 0) === (d.direction > 0) ? 'Oxidation' : 'Reduction'), { 'font-size': 18 });
    });
    svg.append(svgElement('path', { d: 'M162 191 V147 Q210 110 258 147 V191', fill: 'none', stroke: colors.plum, 'stroke-width': 6 }));
    label(svg, 210, 117, 'Salt bridge', { 'font-size': 16 });
    label(svg, 210, 333, 'Same metal · different ion activities', { 'font-size': 19 });
  }

  function drawEnzymeInhibition(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 26, s.mechanism === 'competitive' ? 'Competitive inhibition' : 'Pure noncompetitive inhibition', { 'font-size': 22 });
    [0, .5, 1].forEach(v => {
      const y = 242 - v * 170;
      svg.append(svgElement('path', { d: 'M52 ' + y + ' H370', stroke: colors.ink, 'stroke-opacity': .15 }));
      label(svg, 43, y + 5, v, { 'font-size': 16, 'text-anchor': 'end' });
    });
    for (const reference of [true, false]) svg.append(svgElement('polyline', {
      points: d.curve.map((v, i) => (52 + i * 3.18) + ',' + (242 - (reference ? i / (20 + i) : v) * 170)).join(' '),
      fill: 'none', stroke: reference ? colors.ink : colors.teal, 'stroke-width': 3, 'stroke-dasharray': reference ? '5 4' : 'none',
    }));
    svg.append(svgElement('circle', { cx: 52 + s.substrate * 31.8, cy: 242 - d.rate * 170, r: 5, fill: colors.gold }));
    [0, 5, 10].forEach((v, i) => label(svg, 52 + i * 159, 266, v, { 'font-size': 16 }));
    label(svg, 210, 295, 'Substrate (model concentration units)', { 'font-size': 18 });
    label(svg, 210, 330, 'Rate limit: ' + numberText(d.vmax) + ' · apparent Km: ' + numberText(d.km), { 'font-size': 20 });
  }

  function drawGreenChemistry(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 27, 'One-batch mass ledger', { 'font-size': 24 });
    label(svg, 210, 55, 'Input: 100 g feed + ' + s.solvent + ' g solvent', { 'font-size': 19 });
    [['Product', d.product, colors.teal], ['Waste', d.waste, colors.coral], ['Recovered solvent', d.recovered, colors.gold]].forEach(([name, mass, color], i) => {
      const y = 93 + i * 66;
      label(svg, 38, y, name, { 'font-size': 19, 'text-anchor': 'start' });
      label(svg, 382, y, numberText(mass) + ' g', { 'font-size': 19, 'text-anchor': 'end' });
      svg.append(svgElement('rect', { x: 38, y: y + 11, width: 344, height: 23, rx: 3, fill: colors.ink, 'fill-opacity': .07 }));
      svg.append(svgElement('rect', { x: 38, y: y + 11, width: 344 * mass / 600, height: 23, rx: 3, fill: color }));
    });
    label(svg, 210, 291, 'Full bar = 600 g · mass conserved', { 'font-size': 19 });
    label(svg, 210, 329, d.eFactor === null ? 'No product: E-factor undefined' : 'E-factor = ' + numberText(d.eFactor) + ' g waste / g product', { 'font-size': 18 });
  }

  function drawChemicalInference(svg, current, id) {
    const s = current.state, d = current.data, calibration = id === 'chem.4.analytical';
    label(svg, 210, 26, calibration ? 'Absorbance versus concentration' : 'Trial energy (ħω) versus α', { 'font-size': 22 });
    const maximum = calibration ? 4 : 3.5;
    [0, maximum / 2, maximum].forEach(v => {
      const y = 242 - v / maximum * 170;
      svg.append(svgElement('path', { d: 'M52 ' + y + ' H370', stroke: colors.ink, 'stroke-opacity': .15 }));
      label(svg, 44, y + 5, v, { 'font-size': 15, 'text-anchor': 'end' });
    });
    if (calibration) {
      svg.append(svgElement('path', { d: 'M52 242 L370 ' + (242 - 10 * d.slope / 4 * 170), fill: 'none', stroke: colors.teal, 'stroke-width': 3 }));
      svg.append(svgElement('circle', { cx: 52 + s.concentration * 31.8, cy: 242 - d.used / 4 * 170, r: 5, fill: colors.gold }));
    } else {
      svg.append(svgElement('polyline', { points: d.curve.map((v, i) => (52 + i * 318 / 56) + ',' + (242 - v / 3.5 * 170)).join(' '), fill: 'none', stroke: colors.teal, 'stroke-width': 3 }));
      svg.append(svgElement('path', { d: 'M52 ' + (242 - .5 / 3.5 * 170) + ' H370', stroke: colors.ink, 'stroke-dasharray': '4 4' }));
      svg.append(svgElement('circle', { cx: 52 + (d.a - .2) / 2.8 * 318, cy: 242 - d.energy / 3.5 * 170, r: 5, fill: colors.gold }));
    }
    (calibration ? [0, 5, 10] : [.2, 1.6, 3]).forEach((v, i) => label(svg, 52 + i * 159, 266, v, { 'font-size': 16 }));
    label(svg, 210, 295, calibration ? 'True concentration (model units)' : 'α (larger means narrower)', { 'font-size': 19 });
    label(svg, 210, 331, calibration ? 'Inferred concentration: ' + numberText(d.inferred) : 'E = ' + numberText(d.energy) + ' ħω ≥ 0.5 ħω', { 'font-size': 22 });
  }

  function drawMixtureSeparation(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 27, 'Where did each material go?', { 'font-size': 23 });
    label(svg, 109, 57, s.filter ? 'Filtrate' : 'Mixture vessel', { 'font-size': 19 });
    label(svg, 316, 57, 'On filter', { 'font-size': 19 });
    ['Dissolved solute', 'Undissolved solute', 'Sand'].forEach((name, i) => {
      const y = 91 + i * 66, color = [colors.teal, colors.gold, colors.coral][i];
      label(svg, 210, y, name, { 'font-size': 18 });
      [d.vessel[i], d.residue[i]].forEach((mass, side) => {
        const x = 34 + side * 207;
        svg.append(svgElement('rect', { x, y: y + 10, width: 120, height: 23, rx: 3, fill: colors.ink, 'fill-opacity': .07 }));
        svg.append(svgElement('rect', { x, y: y + 10, width: mass * 6, height: 23, rx: 3, fill: color }));
        label(svg, x + 128, y + 27, mass + ' g', { 'font-size': 15, 'text-anchor': 'start' });
      });
    });
    label(svg, 210, 291, 'Each full bar = 20 g', { 'font-size': 18 });
    label(svg, 210, 326, 'Dissolved capacity: ' + d.capacity + ' g', { 'font-size': 22 });
  }

  function drawAtomicInventory(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, d.name + ' · ' + d.symbol + '-' + d.mass, { 'font-size': 25 });
    [['Protons', s.protons, colors.coral], ['Neutrons', s.neutrons, colors.gold], ['Electrons', s.electrons, colors.teal]].forEach(([name, n, color], i) => {
      const y = 73 + i * 65;
      label(svg, 40, y, name, { 'font-size': 19, 'text-anchor': 'start' });
      label(svg, 380, y, n, { 'font-size': 20, 'text-anchor': 'end' });
      for (let j = 0; j < 12; j++) svg.append(svgElement('circle', { cx: 49 + j * 29, cy: y + 23, r: 8, fill: j < n ? color : colors.paper, stroke: color, 'stroke-opacity': j < n ? 1 : .25 }));
    });
    label(svg, 210, 285, 'Z = ' + s.protons + ' · A = ' + d.mass + ' · charge = ' + (d.charge > 0 ? '+' : '') + d.charge, { 'font-size': 23 });
    label(svg, 210, 324, 'Particle inventory, not an orbital picture', { 'font-size': 18 });
  }

  function drawChemicalConditions(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'chem.4.physical') {
      label(svg, 210, 27, 'A ⇌ B · K = ' + d.k, { 'font-size': 25 });
      [['Initial', s.initialB], ['Inspected', d.b], ['Equilibrium', d.equilibriumB]].forEach(([name, b], i) => {
        const y = 70 + i * 77, a = 10 - b;
        label(svg, 48, y, name, { 'font-size': 19, 'text-anchor': 'start' });
        label(svg, 372, y, 'A ' + numberText(a) + ' · B ' + numberText(b), { 'font-size': 17, 'text-anchor': 'end' });
        svg.append(svgElement('rect', { x: 48, y: y + 11, width: 324 * a / 10, height: 29, fill: colors.teal }));
        svg.append(svgElement('rect', { x: 48 + 324 * a / 10, y: y + 11, width: 324 * b / 10, height: 29, fill: colors.gold }));
      });
      label(svg, 210, 294, 'Net direction: ' + d.direction, { 'font-size': 21 });
      label(svg, 210, 329, 'A + B = 10 mol throughout', { 'font-size': 21 });
    } else if (id === 'chem.3.gases') {
      label(svg, 210, 26, 'Pressure (kPa) · fixed n and T', { 'font-size': 22 });
      const maximum = Math.ceil(d.nrt / 5 / 100) * 100;
      [0, maximum / 2, maximum].forEach(v => {
        const y = 245 - v / maximum * 175;
        svg.append(svgElement('path', { d: 'M62 ' + y + ' H370', stroke: colors.ink, 'stroke-opacity': .15 }));
        label(svg, 54, y + 5, v, { 'font-size': 14, 'text-anchor': 'end' });
      });
      svg.append(svgElement('polyline', { points: d.curve.map((p, i) => (62 + i * 308 / 50) + ',' + (245 - p / maximum * 175)).join(' '), fill: 'none', stroke: colors.teal, 'stroke-width': 3 }));
      svg.append(svgElement('circle', { cx: 62 + (s.volume - 5) / 25 * 308, cy: 245 - d.pressure / maximum * 175, r: 5, fill: colors.gold }));
      [5, 17.5, 30].forEach((v, i) => label(svg, 62 + i * 154, 270, v, { 'font-size': 16 }));
      label(svg, 210, 297, 'Volume (L)', { 'font-size': 20 });
      label(svg, 210, 332, 'Selected P = ' + numberText(d.pressure) + ' kPa', { 'font-size': 22 });
    } else {
      label(svg, 210, 27, 'Energy landscape, not a time trace', { 'font-size': 21 });
      const y = v => 250 - (v + 60) / 220 * 180;
      [-60, 0, 60, 120].forEach(v => {
        svg.append(svgElement('path', { d: 'M55 ' + y(v) + ' H365', stroke: colors.ink, 'stroke-opacity': .13 }));
        label(svg, 47, y(v) + 5, v, { 'font-size': 14, 'text-anchor': 'end' });
      });
      for (const [peak, color, dash] of [[d.peak, colors.ink, '5 5'], [d.active, colors.teal, 'none']]) {
        svg.append(svgElement('path', { d: 'M55 ' + y(0) + ' H95 C145 ' + y(0) + ' 155 ' + y(peak) + ' 210 ' + y(peak) + ' C265 ' + y(peak) + ' 275 ' + y(s.change) + ' 325 ' + y(s.change) + ' H365', fill: 'none', stroke: color, 'stroke-width': 3, 'stroke-dasharray': dash }));
      }
      svg.append(svgElement('circle', { cx: 365, cy: y(s.change), r: 5, fill: colors.gold }));
      label(svg, 92, 278, 'Reactants', { 'font-size': 17 }); label(svg, 330, 278, 'Products', { 'font-size': 17 });
      label(svg, 210, 307, 'Endpoint change: ' + s.change + ' kJ/mol', { 'font-size': 21 });
      label(svg, 210, 333, 'Forward barrier: ' + d.forward + ' kJ/mol', { 'font-size': 18 });
    }
  }

  function drawAtomLedger(svg, current) {
    const s = current.state, d = current.data;
    label(svg, 210, 28, s.hydrogen + ' H₂ + ' + s.oxygen + ' O₂ → ' + s.water + ' H₂O', { 'font-size': 25 });
    ['Hydrogen atoms', 'Oxygen atoms'].forEach((name, i) => {
      const y = 76 + i * 108;
      label(svg, 35, y, name, { 'font-size': 19, 'text-anchor': 'start' });
      [d.left[i], d.right[i]].forEach((n, side) => {
        label(svg, 35, y + 28 + side * 28, side ? 'Out' : 'In', { 'font-size': 16, 'text-anchor': 'start' });
        for (let j = 0; j < n; j++) svg.append(svgElement('circle', { cx: 91 + j * 23, cy: y + 22 + side * 28, r: 7, fill: side ? colors.gold : colors.teal }));
        label(svg, 388, y + 28 + side * 28, n, { 'font-size': 17 });
      });
    });
    label(svg, 210, 293, d.balanced ? 'Both elements conserved' : 'Both rows must match', { 'font-size': 23 });
    label(svg, 210, 329, 'Change coefficients · keep H₂O intact', { 'font-size': 18 });
  }

  function drawIntroChemistry(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'chem.0.water-states') {
      label(svg, 210, 26, d.name, { 'font-size': 22 });
      ['Solid', 'Liquid', 'Vapour'].forEach((name, phase) => {
        const left = 28 + phase * 128;
        svg.append(svgElement('rect', { x: left, y: 67, width: 108, height: 177, rx: 8, fill: phase === 1 ? colors.blue : colors.paper, 'fill-opacity': .08, stroke: colors.ink, 'stroke-opacity': .3 }));
        label(svg, left + 54, 55, name, { 'font-size': 18 });
        for (let i = 0; i < d.counts[phase]; i++) {
          const x = left + 21 + i % 3 * 32 + (phase === 2 ? (i % 2 ? 3 : -3) : 0), y = phase === 2 ? 77 + (Math.floor(i / 3) + .5) / Math.ceil(d.counts[phase] / 3) * 155 + (i % 3 - 1) * 4 : 220 - Math.floor(i / 3) * 23 + (phase === 1 ? i % 2 * 3 : 0);
          svg.append(svgElement('path', { d: 'M' + (x - 5) + ' ' + (y - 5) + ' L' + x + ' ' + y + ' L' + (x + 5) + ' ' + (y - 5), fill: 'none', stroke: colors.blue, 'stroke-width': 3, 'stroke-linecap': 'round' }));
          svg.append(svgElement('circle', { cx: x, cy: y, r: 3, fill: colors.blue }));
          [-5, 5].forEach(dx => svg.append(svgElement('circle', { cx: x + dx, cy: y - 5, r: 2, fill: colors.gold })));
        }
        label(svg, left + 54, 269, d.counts[phase] + ' symbols', { 'font-size': 17 });
      });
      label(svg, 210, 305, 'Different arrangement · same H₂O', { 'font-size': 20 });
      label(svg, 210, 333, 'Vapour itself is invisible', { 'font-size': 18 });
    } else if (id === 'chem.1.matter') {
      label(svg, 210, 26, s.phase[0].toUpperCase() + s.phase.slice(1) + ': same amount, new container', { 'font-size': 19 });
      const left = 210 - s.width / 2, x = 210 - d.width / 2, top = 251 - d.height;
      svg.append(svgElement('rect', { x: left, y: 71, width: s.width, height: 180, fill: 'none', stroke: colors.ink, 'stroke-width': 2 }));
      svg.append(svgElement('rect', { x, y: top, width: d.width, height: d.height, fill: colors.teal, 'fill-opacity': .16, stroke: colors.teal }));
      for (let i = 0; i < 12; i++) svg.append(svgElement('circle', { cx: x + d.width * ((i % 4 + .5) / 4), cy: top + d.height * ((Math.floor(i / 4) + .5) / 3), r: 4, fill: colors.blue }));
      label(svg, 210, 282, 'Occupied area: ' + numberText(d.area), { 'font-size': 21 });
      label(svg, 210, 312, s.phase === 'solid' ? 'Shape and volume stay fixed' : s.phase === 'liquid' ? 'Shape changes; volume stays fixed' : 'Shape and volume follow the container', { 'font-size': 19 });
      label(svg, 210, 337, 'Fixed depth into the page', { 'font-size': 16 });
    } else {
      label(svg, 210, 26, 'Water + ' + s.material + (s.resting ? ' · after resting' : ' · just stirred'), { 'font-size': 22 });
      svg.append(svgElement('rect', { x: 80, y: 100, width: 260, height: 151, fill: colors.blue, 'fill-opacity': .14 }));
      svg.append(svgElement('path', { d: 'M80 66 V251 H340 V66', fill: 'none', stroke: colors.ink, 'stroke-width': 2 }));
      if (d.layer) svg.append(svgElement('rect', { x: 81, y: 100, width: 258, height: 24, fill: colors.gold, 'fill-opacity': .6 }));
      else for (let i = 0; i < 12; i++) {
        const x = 109 + i % 4 * 66, y = d.sediment ? 234 + Math.floor(i / 4) * 5 : 128 + Math.floor(i / 4) * 42 + i % 2 * 8;
        if (s.material === 'salt') {
          svg.append(svgElement('circle', { cx: x, cy: y, r: 9, fill: colors.gold, 'fill-opacity': .3, stroke: colors.gold }));
          label(svg, x, y + 4, i % 2 ? '−' : '+', { 'font-size': 14 });
        } else svg.append(svgElement('ellipse', { cx: x, cy: y, rx: s.material === 'oil' ? 11 : 5, ry: s.material === 'oil' ? 8 : 2, fill: colors.gold, 'fill-opacity': .7 }));
      }
      label(svg, 210, 285, s.material === 'salt' ? 'Dissolved ions, not visible grains' : d.layer ? 'Oil reforms a layer' : d.sediment ? 'Sand forms sediment' : s.material === 'oil' ? 'Temporary oil droplets' : 'Suspended sand grains', { 'font-size': 20 });
      label(svg, 210, 328, s.material === 'salt' ? 'Clear does not mean empty' : 'Mixing is not the same as dissolving', { 'font-size': 19 });
    }
  }

  function drawBiologyEvidence(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'bio.1.health') {
      label(svg, 210, 25, ['Before washing', 'Wet', 'Lather', 'Scrub ≥20 seconds', 'Rinse', 'Dry'][s.stage], { 'font-size': 23 });
      svg.append(svgElement('path', { d: 'M165 230 Q135 210 140 165 L125 141 Q120 130 130 125 Q139 120 147 134 L160 150 L160 86 Q160 70 172 70 Q183 70 183 86 L183 127 L185 60 Q185 45 198 45 Q210 45 210 60 L210 127 L214 67 Q214 52 225 52 Q237 52 237 68 L236 134 L241 94 Q244 80 254 84 Q265 89 260 107 L251 184 Q250 223 231 236 L229 254 H164 Z', fill: colors.coral, 'fill-opacity': .2, stroke: colors.coral, 'stroke-width': 2 }));
      ['M162 171 Q180 180 180 206', 'M187 160 Q215 176 239 160', 'M187 199 Q211 188 234 195'].forEach(path => svg.append(svgElement('path', { d: path, fill: 'none', stroke: colors.coral, 'stroke-opacity': .6 })));
      if (s.stage === 1 || s.stage === 4) for (let i = 0; i < 5; i++) svg.append(svgElement('path', { d: 'M' + (275 + i * 12) + ' 87 l-18 74', stroke: colors.blue, 'stroke-width': 3, 'stroke-dasharray': '7 5' }));
      if (s.stage === 2 || s.stage === 3) for (let i = 0; i < 18; i++) svg.append(svgElement('circle', { cx: 152 + i % 6 * 18, cy: 139 + Math.floor(i / 6) * 22, r: 11, fill: colors.paper, 'fill-opacity': .8, stroke: colors.blue, 'stroke-opacity': .4 }));
      for (let i = 0; i < d.particles; i++) svg.append(svgElement('circle', { cx: 176 + i % 4 * 14, cy: 144 + Math.floor(i / 4) * 18, r: 3.5, fill: colors.gold }));
      label(svg, 210, 286, d.returned ? 'Contact transfers material back' : s.stage >= 4 ? 'Rinsing carries material away' : 'Loosen material before rinsing', { 'font-size': 19 });
      label(svg, 210, 328, 'No dots ≠ sterile hands', { 'font-size': 21 });
    } else if (id === 'bio.5.immunology') {
      label(svg, 210, 26, 'One site: three possible states', { 'font-size': 22 });
      const names = ['A-bound', 'B-bound', 'Unoccupied'], fills = [colors.teal, colors.plum, colors.paper];
      d.fractions.forEach((v, i) => {
        const y = 62 + i * 68;
        label(svg, 38, y, names[i], { 'font-size': 18, 'text-anchor': 'start' });
        label(svg, 378, y, numberText(v * 100) + '%', { 'font-size': 18, 'text-anchor': 'end' });
        svg.append(svgElement('rect', { x: 38, y: y + 10, width: 340, height: 25, rx: 3, fill: colors.ink, 'fill-opacity': .06, stroke: colors.ink, 'stroke-opacity': .2 }));
        svg.append(svgElement('rect', { x: 38, y: y + 10, width: 340 * v, height: 25, rx: 3, fill: fills[i], stroke: colors.ink, 'stroke-opacity': .4 }));
      });
      label(svg, 210, 292, 'Weights A/KdA : B/KdB : 1', { 'font-size': 21 });
      label(svg, 210, 327, 'Occupancy is not protection', { 'font-size': 20 });
    } else {
      const resistance = id === 'bio.3.microbiology', max = resistance ? 1 : 12;
      label(svg, 210, 25, resistance ? 'Resistant fraction across rounds' : 'Test where predictions differ', { 'font-size': 21 });
      [0, max / 2, max].forEach(v => {
        const y = 243 - v / max * 175;
        svg.append(svgElement('path', { d: 'M52 ' + y + ' H370', stroke: colors.ink, 'stroke-opacity': .15 }));
        label(svg, 43, y + 5, resistance ? v * 100 + '%' : v, { 'font-size': 15, 'text-anchor': 'end' });
      });
      const curve = (points, color) => svg.append(svgElement('polyline', { points: points.map(([x, y]) => (52 + x * 318) + ',' + (243 - y / max * 175)).join(' '), fill: 'none', stroke: color, 'stroke-width': 3 }));
      if (resistance) {
        curve(d.history.map((v, i) => [i / 6, v.fraction]), colors.plum);
        svg.append(svgElement('circle', { cx: 52 + s.generation * 53, cy: 243 - d.selected.fraction * 175, r: 5, fill: colors.gold }));
      } else {
        curve(Array.from({ length: 101 }, (_, i) => [i / 100, i / 10]), colors.teal);
        curve(Array.from({ length: 101 }, (_, i) => [i / 100, 4 * i / (20 + i)]), colors.plum);
        const x = 52 + d.x / 5 * 318, y1 = 243 - d.low / 12 * 175, y2 = 243 - d.high / 12 * 175;
        svg.append(svgElement('path', { d: 'M' + x + ' ' + y1 + ' V' + y2 + ' M' + (x - 7) + ' ' + y1 + ' h14 M' + (x - 7) + ' ' + y2 + ' h14', stroke: colors.gold, 'stroke-width': 3 }));
        svg.append(svgElement('circle', { cx: x, cy: 243 - d.observed / 12 * 175, r: 4, fill: colors.gold }));
      }
      [0, resistance ? 3 : 2.5, resistance ? 6 : 5].forEach((v, i) => label(svg, 52 + i * 159, 265, v, { 'font-size': 16 }));
      label(svg, 210, 292, resistance ? 'Selection rounds' : 'Input (illustrative units)', { 'font-size': 19 });
      label(svg, 210, 329, resistance ? 'Total: ' + numberText(d.selected.total) + ' abundance units' : d.compatible.filter(Boolean).length + ' of 2 hypotheses compatible', { 'font-size': 19 });
    }
  }

  function drawNeuroPhysiologyBehaviour(svg, current, id) {
    const s = current.state, d = current.data;
    const neuro = id === 'bio.4.neuro', physiology = id === 'bio.4.physiology';
    label(svg, 210, 25, neuro ? 'Charge → threshold → reset' : physiology ? 'Cooperativity shapes oxygen binding' : 'Average gain includes travel time', { 'font-size': 20 });
    const maximum = neuro || physiology ? 1 : Math.ceil(d.best / 5) * 5;
    [0, maximum / 2, maximum].forEach(v => {
      const y = 244 - v / maximum * 172;
      svg.append(svgElement('path', { d: 'M52 ' + y + ' H370', stroke: colors.ink, 'stroke-opacity': .15 }));
      label(svg, 44, y + 5, physiology ? v * 100 + '%' : numberText(v), { 'font-size': 15, 'text-anchor': 'end' });
    });
    if (neuro) {
      svg.append(svgElement('path', { d: 'M52 72 H370', stroke: colors.gold, 'stroke-dasharray': '5 4' }));
      svg.append(svgElement('polyline', { points: d.points.map(([t, v]) => (52 + t * 3.18) + ',' + (244 - v * 172)).join(' '), fill: 'none', stroke: colors.teal, 'stroke-width': 2 }));
      d.spikes.forEach(t => svg.append(svgElement('path', { d: 'M' + (52 + t * 3.18) + ' 56 v10', stroke: colors.gold, 'stroke-width': 2 })));
    } else {
      svg.append(svgElement('polyline', { points: d.curve.map((v, i) => (52 + i * 318 / (d.curve.length - 1)) + ',' + (244 - v / maximum * 172)).join(' '), fill: 'none', stroke: colors.teal, 'stroke-width': 3 }));
      const markers = physiology ? [[20, d.low, colors.plum], [80, d.high, colors.plum], [s.pressure, d.selected, colors.gold]] :
        [[d.optimum * 2.5, d.best, colors.plum], [s.residence * 2.5, d.selected, colors.gold]];
      markers.forEach(([x, v, color]) => svg.append(svgElement('circle', { cx: 52 + x * 3.18, cy: 244 - v / maximum * 172, r: color === colors.gold ? 4 : 6, fill: color, stroke: colors.ink, 'stroke-width': .5 })));
    }
    [0, neuro || physiology ? 50 : 20, neuro || physiology ? 100 : 40].forEach((v, i) => label(svg, 52 + i * 159, 266, v, { 'font-size': 16 }));
    label(svg, 210, 290, neuro ? 'Time (ms)' : physiology ? 'Oxygen pressure (model units)' : 'Residence time', { 'font-size': 18 });
    label(svg, 210, 331, neuro ? d.spikes.length + ' spikes in 100 ms' : physiology ? 'Binding: ' + numberText(d.selected * 100) + '%' : 'Best departure: ' + numberText(d.optimum), { 'font-size': 22 });
  }

  function drawMolecularComputation(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'bio.4.genomics') {
      label(svg, 210, 25, 'Position 4: reference T → alternate C', { 'font-size': 19 });
      const row = (sequence, y, name, faded) => {
        label(svg, 64, y + 17, name, { 'font-size': 15, 'text-anchor': 'end', opacity: faded ? .4 : 1 });
        [...sequence].forEach((base, j) => {
          svg.append(svgElement('rect', { x: 81 + j * 34, y, width: 30, height: 21, rx: 3, fill: j === 3 && base === 'C' ? colors.gold : colors.paper,
            stroke: j === 3 ? colors.gold : colors.ink, 'stroke-opacity': .25, opacity: faded ? .3 : 1 }));
          label(svg, 96 + j * 34, y + 16, base, { 'font-size': 16, 'font-family': 'monospace', opacity: faded ? .35 : 1 });
        });
      };
      row('ACGTACGT', 40, 'Ref', false);
      d.reads.forEach((r, i) => row(r.sequence, 72 + i * 23, 'R' + (i + 1) + (r.flagged ? '*' : ''), !r.included));
      label(svg, 210, 290, '* Last read: low quality', { 'font-size': 17 });
      label(svg, 210, 328, d.fraction === null ? 'No usable coverage' : d.support + '/' + d.usable + ' support C · ' + numberText(d.fraction * 100) + '%', { 'font-size': 22 });
    } else if (id === 'bio.5.comp-bio') {
      label(svg, 210, 24, 'Minimum global-alignment cost: ' + d.cost, { 'font-size': 19 });
      ['∅', ...d.target].forEach((base, j) => label(svg, 97 + j * 36, 49, base, { 'font-size': 16, 'font-family': 'monospace' }));
      d.matrix.forEach((row, i) => {
        label(svg, 64, 75 + i * 28, i ? d.reference[i - 1] : '∅', { 'font-size': 16, 'font-family': 'monospace' });
        row.forEach((cost, j) => {
          svg.append(svgElement('rect', { x: 80 + j * 36, y: 56 + i * 28, width: 34, height: 26,
            fill: d.path.some(([pi, pj]) => pi === i && pj === j) ? colors.gold : colors.paper, 'fill-opacity': .3, stroke: colors.ink, 'stroke-opacity': .12 }));
          label(svg, 97 + j * 36, 75 + i * 28, cost, { 'font-size': 15 });
        });
      });
      label(svg, 210, 276, 'ref ' + d.first, { 'font-size': 19, 'font-family': 'monospace' });
      label(svg, 210, 301, 'qry ' + d.second, { 'font-size': 19, 'font-family': 'monospace' });
      label(svg, 210, 332, d.ways + ' optimal path' + (d.ways === 1 ? '' : 's') + '; one shown', { 'font-size': 18 });
    } else {
      label(svg, 210, 25, 'Product feeds back on synthesis', { 'font-size': 20 });
      const limit = Math.max(1, d.openLimit);
      [0, limit / 2, limit].forEach(v => {
        const y = 242 - v / limit * 172;
        svg.append(svgElement('path', { d: 'M58 ' + y + ' H370', stroke: colors.ink, 'stroke-opacity': .15 }));
        label(svg, 49, y + 5, numberText(v), { 'font-size': 16, 'text-anchor': 'end' });
      });
      for (const [values, color, dashed] of [[d.open, colors.coral, true], [d.values, colors.teal, false]]) {
        svg.append(svgElement('polyline', { points: values.map((v, i) => (58 + i * 312 / 100) + ',' + (242 - v / limit * 172)).join(' '),
          fill: 'none', stroke: color, 'stroke-width': 3, 'stroke-dasharray': dashed ? '7 4' : 'none' }));
      }
      [0, 5, 10].forEach((t, i) => label(svg, 58 + i * 156, 266, t, { 'font-size': 16 }));
      label(svg, 210, 291, 'Time (model units)', { 'font-size': 18 });
      label(svg, 210, 331, 'Protein at t=10: ' + numberText(d.final), { 'font-size': 22 });
    }
  }

  function drawPlantPopulationEnzyme(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'bio.3.botany') {
      label(svg, 210, 26, 'Guard cells control a shared pore', { 'font-size': 20 });
      for (const side of [-1, 1]) {
        const g = svgElement('g', { transform: 'translate(210 0) scale(' + side + ' 1)' }), inner = d.conductance * 22;
        g.append(svgElement('path', { d: 'M' + inner + ' 78 C' + (inner + 83) + ' 73 ' + (inner + 83) + ' 213 ' + inner + ' 208 Q' + (inner + d.conductance * 23) + ' 143 ' + inner + ' 78 Z', fill: colors.teal, 'fill-opacity': .25, stroke: colors.teal, 'stroke-width': 2 }));
        for (const y of [104, 130, 156, 182]) g.append(svgElement('ellipse', { cx: inner + 39, cy: y, rx: 8, ry: 5, fill: colors.teal, 'fill-opacity': .65 }));
        svg.append(g);
      }
      label(svg, 210, 231, s.opening ? 'Pore open: ' + s.opening + '%' : 'Pore closed', { 'font-size': 18 });
      label(svg, 210, 257, 'CO₂ entry: ' + numberText(d.carbon * 100) + '%', { 'font-size': 18 });
      svg.append(svgElement('rect', { x: 60, y: 267, width: 300 * d.carbon, height: 11, rx: 3, fill: colors.blue }));
      label(svg, 210, 308, 'Water loss: ' + numberText(d.water * 100) + '%', { 'font-size': 18 });
      svg.append(svgElement('rect', { x: 60, y: 319, width: 300 * d.water, height: 11, rx: 3, fill: colors.coral }));
    } else {
      const ecology = id === 'bio.3.ecology', values = ecology ? d.values : d.curve;
      label(svg, 210, 25, ecology ? 'Population approaches a fixed K' : 'Initial rate approaches Vmax', { 'font-size': 21 });
      for (const value of [0, 50, 100]) {
        const y = 244 - value * 1.7;
        svg.append(svgElement('path', { d: 'M50 ' + y + ' H370', stroke: colors.ink, 'stroke-opacity': .15 }));
        label(svg, 43, y + 5, value, { 'font-size': 16, 'text-anchor': 'end' });
      }
      const limit = ecology ? s.capacity : s.vmax;
      svg.append(svgElement('path', { d: 'M50 ' + (244 - limit * 1.7) + ' H370', stroke: colors.gold, 'stroke-width': 2, 'stroke-dasharray': '6 4' }));
      svg.append(svgElement('polyline', { points: values.map((v, i) => (50 + i * 320 / (values.length - 1)) + ',' + (244 - v * 1.7)).join(' '), fill: 'none', stroke: colors.teal, 'stroke-width': 3 }));
      if (!ecology) {
        svg.append(svgElement('circle', { cx: 50 + s.km * 3.2, cy: 244 - s.vmax / 2 * 1.7, r: 6, fill: colors.plum }));
        svg.append(svgElement('circle', { cx: 50 + s.substrate * 3.2, cy: 244 - d.velocity * 1.7, r: 4, fill: colors.gold, stroke: colors.ink }));
      }
      [0, ecology ? 10 : 50, ecology ? 20 : 100].forEach((n, i) => label(svg, 50 + i * 160, 267, n, { 'font-size': 16 }));
      label(svg, 210, 291, ecology ? 'Time (model units)' : 'Substrate (model units)', { 'font-size': 18 });
      label(svg, 210, 332, ecology ? 'N(20) = ' + numberText(d.final) + ' · K = ' + s.capacity : 'v = ' + numberText(d.velocity) + ' · Vmax = ' + s.vmax, { 'font-size': 21 });
    }
  }

  function drawEvolution(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'bio.3.evolution') {
      label(svg, 210, 26, 'Inherited variants across generations', { 'font-size': 20 });
      for (const p of [0, .5, 1]) {
        const y = 245 - p * 185;
        svg.append(svgElement('path', { d: 'M50 ' + y + ' H370', stroke: colors.ink, 'stroke-opacity': .15 }));
        label(svg, 43, y + 5, p * 100 + '%', { 'font-size': 15, 'text-anchor': 'end' });
      }
      for (const [key, color] of [['a', colors.blue], ['b', colors.coral]]) {
        const points = d.history.map((p, i) => (50 + i * 320 / 12) + ',' + (245 - (key === 'a' ? p : 1 - p) * 185)).join(' ');
        svg.append(svgElement('polyline', { points, fill: 'none', stroke: color, 'stroke-width': 3, 'stroke-dasharray': key === 'b' ? '7 4' : 'none' }));
      }
      const x = 50 + s.generation * 320 / 12;
      svg.append(svgElement('path', { d: 'M' + x + ' 52 V250', stroke: colors.gold, 'stroke-width': 2, 'stroke-dasharray': '3 4' }));
      svg.append(svgElement('circle', { cx: x, cy: 245 - d.p * 185, r: 5, fill: colors.gold, stroke: colors.ink }));
      for (const generation of [0, 6, 12]) label(svg, 50 + generation * 320 / 12, 267, generation, { 'font-size': 16 });
      label(svg, 210, 291, 'Generation', { 'font-size': 18 });
      label(svg, 210, 329, 'Selected A: ' + numberText(d.p * 100) + '%', { 'font-size': 22 });
    } else {
      label(svg, 210, 27, 'Same allele pool, different pairings', { 'font-size': 20 });
      ['AA', 'Aa', 'aa'].forEach((name, i) => {
        const y = 79 + i * 62;
        label(svg, 46, y + 20, name, { 'font-size': 21 });
        svg.append(svgElement('rect', { x: 87, y, width: d.genotype[i] * 286, height: 26, fill: colors.teal, 'fill-opacity': .65 }));
        svg.append(svgElement('rect', { x: 87, y: y - 3, width: d.baseline[i] * 286, height: 32, fill: 'none', stroke: colors.ink, 'stroke-width': 1.5, 'stroke-dasharray': '4 3' }));
        label(svg, 373, y - 9, numberText(d.genotype[i] * 100) + '%', { 'font-size': 17, 'text-anchor': 'end' });
      });
      label(svg, 210, 260, 'Allele pool: A and a', { 'font-size': 18 });
      svg.append(svgElement('rect', { x: 48, y: 273, width: 324 * d.p, height: 22, fill: colors.blue }));
      svg.append(svgElement('rect', { x: 48 + 324 * d.p, y: 273, width: 324 * d.q, height: 22, fill: colors.coral }));
      label(svg, 210, 328, 'A ' + s.percent + '% · a ' + (100 - s.percent) + '%', { 'font-size': 22 });
    }
  }

  function drawBodyReproduction(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'bio.1.human-body') {
      label(svg, 210, 27, 'Heart → lungs → heart → body', { 'font-size': 20 });
      const positions = [[90, 177], [210, 91], [330, 177], [210, 263]];
      positions.forEach(([x, y], i) => {
        const [nx, ny] = positions[(i + 1) % 4], dx = nx - x, dy = ny - y;
        const trim = 1 / Math.sqrt((dx / 72) ** 2 + (dy / 42) ** 2);
        biologyArrow(svg, x + dx * trim, y + dy * trim, nx - dx * trim, ny - dy * trim, colors.teal);
        svg.append(svgElement('ellipse', { cx: x, cy: y, rx: 68, ry: 38, fill: colors.paper,
          stroke: i === d.at ? colors.gold : colors.teal, 'stroke-width': i === d.at ? 4 : 1 }));
        label(svg, x, y - 3, d.route[i], { 'font-size': 19 });
        label(svg, x, y + 20, s.oxygen ? (i === 1 || i === 2 ? 'More O₂' : 'Less O₂') : ['Pump', 'Gas exchange', 'Pump', 'O₂ delivery'][i], { 'font-size': 15 });
      });
      label(svg, 210, 182, 'Two pumps', { 'font-size': 16 });
      label(svg, 210, 333, 'Blood leaving: ' + d.name.toLowerCase(), { 'font-size': 19 });
    } else if (id === 'bio.2.digestion') {
      label(svg, 210, 27, d.name, { 'font-size': 22 });
      d.nodes.forEach((name, i) => {
        const y = 43 + i * 72;
        svg.append(svgElement('rect', { x: 67, y, width: 286, height: 41, rx: 12, fill: colors.paper,
          stroke: i === s.step ? colors.gold : i < s.step ? colors.teal : colors.ink, 'stroke-opacity': i <= s.step ? 1 : .25,
          'stroke-width': i === s.step ? 3 : 1 }));
        label(svg, 210, y + 27, name, { 'font-size': 20 });
        if (i < 3) {
          biologyArrow(svg, 46, y + 34, 46, y + 76, i < s.step ? colors.teal : colors.gold);
          label(svg, 210, y + 62, d.verbs[i], { 'font-size': 17 });
        }
      });
      label(svg, 210, 334, 'Step ' + (s.step + 1) + ' of 4', { 'font-size': 18 });
    } else {
      label(svg, 210, 25, 'Fertilisation combines two sets', { 'font-size': 21 });
      const chromosomeCell = (x, y, radius, sets) => {
        svg.append(svgElement('circle', { cx: x, cy: y, r: radius, fill: colors.paper, stroke: colors.teal, 'stroke-width': 1.5 }));
        sets.forEach((color, row) => {
          for (let i = 0; i < s.haploid; i++) {
            const xx = x + (i - (s.haploid - 1) / 2) * radius * .43, yy = y + (row - (sets.length - 1) / 2) * radius * .62;
            svg.append(svgElement('path', { d: 'M' + xx + ' ' + (yy - radius * .2) + ' v' + (radius * .4), stroke: color,
              'stroke-width': Math.max(1.5, radius * .12), 'stroke-linecap': 'round' }));
          }
        });
      };
      chromosomeCell(101, 91, 39, [colors.blue]); chromosomeCell(319, 91, 39, [colors.coral]);
      label(svg, 101, 148, s.haploid + ' chromosomes', { 'font-size': 17 });
      label(svg, 319, 148, s.haploid + ' chromosomes', { 'font-size': 17 });
      biologyArrow(svg, 143, 100, 188, 163, colors.blue); biologyArrow(svg, 277, 100, 232, 163, colors.coral);
      chromosomeCell(210, 195, 35, [colors.blue, colors.coral]);
      label(svg, 210, 252, 'Zygote: ' + d.diploid + ' chromosomes', { 'font-size': 20 });
      for (let i = 0; i < d.cells; i++) chromosomeCell(210 + (i - (d.cells - 1) / 2) * 43, 286, 16, [colors.blue, colors.coral]);
      label(svg, 210, 333, d.cells + ' cell' + (d.cells === 1 ? '' : 's') + ' · ' + d.diploid + ' chromosomes in each', { 'font-size': 19 });
    }
  }

  function drawAnimalHabitats(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'bio.0.animals') {
      label(svg, 210, 25, 'Compare the visible features', { 'font-size': 20 });
      d.animals.forEach((a, index) => {
        const x = 18 + (index % 2) * 197, y = 40 + Math.floor(index / 2) * 146;
        const match = d.matches.includes(a.id), g = svgElement('g', { transform: 'translate(' + (x + 91) + ' ' + (y + 67) + ')' });
        svg.append(svgElement('rect', { x, y, width: 186, height: 136, rx: 14, fill: colors.paper, stroke: match ? colors.gold : colors.ink, 'stroke-width': match ? 3 : 1, 'stroke-opacity': match ? 1 : .2 }));
        label(svg, x + 93, y + 23, a.name, { 'font-size': 18 });
        if (a.id === 'beetle' || a.id === 'spider') {
          const pairs = a.legs / 2;
          for (let j = 0; j < pairs; j++) for (const side of [-1, 1]) {
            const yy = -17 + j * 10, endpoint = -30 + j * (60 / (pairs - 1));
            g.append(svgElement('path', { d: 'M' + (side * 10) + ' ' + yy + ' L' + (side * 30) + ' ' + (yy - 6) + ' L' + (side * 46) + ' ' + endpoint,
              fill: 'none', stroke: colors.ink, 'stroke-width': 3, 'stroke-linecap': 'round' }));
          }
          g.append(svgElement('ellipse', { cx: 0, cy: a.id === 'beetle' ? 4 : 14, rx: 22, ry: 27, fill: a.id === 'beetle' ? colors.coral : colors.plum }));
          g.append(svgElement('ellipse', { cx: 0, cy: -20, rx: 13, ry: 13, fill: colors.ink }));
          if (a.id === 'beetle') {
            g.append(svgElement('path', { d: 'M0 -16 V30', stroke: colors.ink, 'stroke-width': 2 }));
            for (const xx of [-10, 10]) for (const yy of [-2, 14]) g.append(svgElement('circle', { cx: xx, cy: yy, r: 4, fill: colors.ink }));
          }
        } else if (a.id === 'sparrow') {
          for (const xx of [-5, 12]) g.append(svgElement('path', { d: 'M' + xx + ' 12 V33 l-7 3 m7 -3 l7 3', fill: 'none', stroke: colors.coral, 'stroke-width': 3 }));
          g.append(svgElement('path', { d: 'M-23 5 L-54 -3 L-44 17 Z', fill: colors.plum }));
          g.append(svgElement('ellipse', { cx: 0, cy: 1, rx: 31, ry: 21, fill: colors.plum }));
          g.append(svgElement('path', { d: 'M-14 -5 Q14 -17 18 9 Q-3 23 -14 -5', fill: colors.paper, stroke: colors.plum, 'stroke-width': 2 }));
          g.append(svgElement('circle', { cx: 26, cy: -18, r: 17, fill: colors.plum }));
          g.append(svgElement('path', { d: 'M40 -20 L55 -15 L40 -10 Z', fill: colors.gold }));
          g.append(svgElement('circle', { cx: 30, cy: -22, r: 3, fill: colors.ink }));
        } else {
          g.append(svgElement('path', { d: 'M-35 0 L-60 -21 L-60 21 Z M-12 -14 L2 -34 L17 -14 M0 14 L10 31 L22 13', fill: colors.teal, 'fill-opacity': .6 }));
          g.append(svgElement('ellipse', { cx: 2, cy: 0, rx: 43, ry: 21, fill: colors.blue, 'fill-opacity': .5, stroke: colors.blue }));
          g.append(svgElement('path', { d: 'M23 -15 Q10 0 23 15', fill: 'none', stroke: colors.blue, 'stroke-width': 2 }));
          g.append(svgElement('circle', { cx: 32, cy: -4, r: 3, fill: colors.ink }));
        }
        svg.append(g);
        label(svg, x + 93, y + 123, s.count ? a.legs + ' legs' : match ? 'Matches' : 'Does not match', { 'font-size': 17, fill: colors.teal });
      });
    } else {
      label(svg, 210, 28, 'Wood frog: two places, one journey', { 'font-size': 19 });
      svg.append(svgElement('rect', { x: 191, y: 62, width: 38, height: 194, fill: colors.ink, 'fill-opacity': .12 }));
      svg.append(svgElement('ellipse', { cx: 95, cy: 155, rx: 70, ry: 74, fill: s.woodland ? colors.teal : colors.coral, 'fill-opacity': .09, stroke: s.woodland ? colors.teal : colors.coral }));
      svg.append(svgElement('ellipse', { cx: 324, cy: 155, rx: 70, ry: 74, fill: s.pool ? colors.blue : colors.coral, 'fill-opacity': s.pool ? .22 : .07, stroke: s.pool ? colors.blue : colors.coral }));
      for (const xx of [62, 96, 127]) {
        svg.append(svgElement('path', { d: 'M' + xx + ' 190 V118 m0 24 l-14 -15 m14 26 l16 -17', fill: 'none', stroke: s.woodland ? colors.coral : colors.ink, 'stroke-opacity': s.woodland ? 1 : .15, 'stroke-width': 4 }));
        if (s.woodland) svg.append(svgElement('ellipse', { cx: xx, cy: 117, rx: 22, ry: 29, fill: colors.teal, 'fill-opacity': .4 }));
      }
      if (s.pool) for (let i = 0; i < 3; i++) svg.append(svgElement('path', { d: 'M278 ' + (136 + i * 18) + ' q12 -6 24 0 t24 0 t24 0', fill: 'none', stroke: colors.blue, 'stroke-width': 2 }));
      else svg.append(svgElement('path', { d: 'M289 126 L317 160 L297 187 M317 160 L348 145 L354 188', stroke: colors.coral, fill: 'none', 'stroke-width': 2 }));
      svg.append(svgElement('path', { d: 'M133 203 Q210 246 285 203', fill: 'none', stroke: s.route ? colors.teal : colors.coral, 'stroke-width': 5, 'stroke-dasharray': s.route ? 'none' : '7 6' }));
      if (!s.route) svg.append(svgElement('path', { d: 'M193 211 L227 240 M227 211 L193 240', stroke: colors.coral, 'stroke-width': 5 }));
      label(svg, 95, 57, 'Woodland', { 'font-size': 20 }); label(svg, 324, 57, 'Breeding pool', { 'font-size': 20 });
      label(svg, 95, 251, s.woodland ? 'Refuge present' : 'Refuge absent', { 'font-size': 17 });
      label(svg, 324, 251, s.pool ? 'Water present' : 'Pool dry', { 'font-size': 17 });
      label(svg, 210, 293, s.route ? 'Connecting route open' : 'Connecting route closed', { 'font-size': 20 });
      label(svg, 210, 328, d.connected ? 'Seasonal journey connected' : 'Full journey not connected', { 'font-size': 20 });
    }
  }

  function drawSensesSeasons(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'bio.0.body') {
      label(svg, 210, 28, 'Notice → signal → perception', { 'font-size': 20 });
      const rows = [[d.stimulus, d.organ], ['Nerve signals', 'Travel toward the brain'], ['Brain processing', d.perception]];
      rows.forEach(([heading, detail], i) => {
        const y = 49 + i * 88, reached = i <= s.step;
        svg.append(svgElement('rect', { x: 22, y, width: 376, height: 70, rx: 16,
          fill: reached ? (i === s.step ? colors.gold : colors.teal) : colors.ink,
          'fill-opacity': reached ? .12 : .025, stroke: i === s.step ? colors.gold : reached ? colors.teal : colors.ink,
          'stroke-width': i === s.step ? 3 : 1, 'stroke-opacity': reached ? 1 : .2 }));
        svg.append(svgElement('circle', { cx: 52, cy: y + 35, r: 15, fill: reached ? colors.teal : colors.paper, stroke: colors.teal }));
        label(svg, 52, y + 41, i + 1, { fill: reached ? colors.paper : colors.ink, 'font-size': 17 });
        label(svg, 225, y + 27, heading, { 'font-size': 21 });
        label(svg, 225, y + 52, detail, { 'font-size': 18 });
        if (i < 2) biologyArrow(svg, 210, y + 73, 210, y + 84, i < s.step ? colors.teal : colors.gold);
      });
      label(svg, 210, 333, 'An ordered pathway, not a clock', { 'font-size': 17 });
    } else {
      label(svg, 210, 27, d.month + ' · ' + d.season, { 'font-size': 22 });
      for (let i = 0; i < 12; i++) {
        svg.append(svgElement('rect', { x: 19 + i * 32, y: 42, width: 28, height: 28, rx: 5,
          fill: s.month === i + 1 ? colors.gold : colors.paper, stroke: colors.gold }));
        label(svg, 33 + i * 32, 62, i + 1, { 'font-size': 15 });
      }
      svg.append(svgElement('path', { d: 'M190 257 Q205 209 203 127 L215 127 Q214 211 232 257 Z', fill: colors.coral, 'fill-opacity': .7 }));
      const tips = [[139, 137], [165, 112], [205, 96], [250, 114], [280, 146]];
      tips.forEach(([x, y], i) => {
        svg.append(svgElement('path', { d: 'M210 216 Q' + (210 + (x - 210) / 2) + ' 170 ' + x + ' ' + y,
          fill: 'none', stroke: colors.coral, 'stroke-width': 5, 'stroke-linecap': 'round' }));
        if (d.phase === 0) svg.append(svgElement('ellipse', { cx: x, cy: y, rx: 4, ry: 7, fill: colors.plum }));
        else {
          const radius = d.phase === 1 ? 17 : 35;
          svg.append(svgElement('ellipse', { cx: x, cy: y, rx: radius, ry: radius * 1.1,
            fill: d.phase === 3 ? (i % 2 ? colors.coral : colors.gold) : colors.teal, 'fill-opacity': .4, stroke: d.phase === 3 ? colors.gold : colors.teal }));
          if (d.phase === 3) svg.append(svgElement('ellipse', { cx: x + 5, cy: 213 + i * 8, rx: 9, ry: 4, transform: 'rotate(25 ' + (x + 5) + ' ' + (213 + i * 8) + ')', fill: colors.gold }));
        }
      });
      svg.append(svgElement('path', { d: 'M100 258 H320 M201 258 L173 274 M207 258 L195 277 M217 258 L242 276', stroke: colors.coral, 'stroke-width': 2, fill: 'none' }));
      label(svg, 210, 299, d.change, { 'font-size': 19 });
      label(svg, 210, 329, 'Other hemisphere: ' + d.opposite.toLowerCase(), { 'font-size': 18 });
    }
  }

  function drawLifeSystems(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'bio.0.living') {
      label(svg, 210, 28, d.name, { 'font-size': 25 });
      if (s.inside) {
        svg.append(svgElement('rect', { x: 38, y: 72, width: 146, height: 151, rx: 14, fill: colors.teal, 'fill-opacity': .04, stroke: colors.gold, 'stroke-width': 2 }));
        if (d.cells) {
          for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
            const x = 48 + j * 44, y = 83 + i * 44;
            svg.append(svgElement('rect', { x, y, width: 38, height: 38, rx: 7, fill: colors.teal, 'fill-opacity': .13, stroke: colors.teal, 'stroke-width': 2 }));
            svg.append(svgElement('circle', { cx: x + 12, cy: y + 23, r: 5, fill: colors.plum }));
          }
        } else if (s.specimen === 'robot') {
          svg.append(svgElement('path', { d: 'M58 111 H164 V191 H58Z M111 111 V145 H164 M58 165 H111 V191', fill: 'none', stroke: colors.gold, 'stroke-width': 3 }));
          [[58, 111], [164, 145], [111, 191]].forEach(([x, y]) => svg.append(svgElement('rect', { x: x - 9, y: y - 10, width: 18, height: 20, fill: colors.blue, stroke: colors.ink })));
        } else if (s.specimen === 'rock') {
          ['M48 91 L99 81 L116 132 L79 155 L47 135Z', 'M104 82 L174 94 L165 153 L118 134Z', 'M47 141 L78 160 L102 211 L48 213Z',
            'M83 158 L120 139 L165 158 L173 211 L108 211Z'].forEach((path, i) => svg.append(svgElement('path', { d: path, fill: i % 2 ? colors.blue : colors.plum, 'fill-opacity': .2, stroke: colors.blue })));
        } else {
          for (let i = 0; i < 6; i++) {
            const x = 67 + i % 2 * 83, y = 102 + Math.floor(i / 2) * 44;
            line(svg, x - 10, y - 4, x + 10, y + 4, { stroke: colors.ink });
            [[x - 10, y - 4], [x + 10, y + 4]].forEach(([cx, cy]) => svg.append(svgElement('circle', { cx, cy, r: 6, fill: colors.coral })));
            svg.append(svgElement('circle', { cx: x, cy: y, r: 5, fill: colors.ink }));
          }
        }
        label(svg, 111, 244, d.cells ? 'Cells (schematic)' : s.specimen === 'robot' ? 'Circuit, not cells' : s.specimen === 'rock' ? 'Mineral grains' : 'Hot gases, not cells', { 'font-size': 14 });
      } else if (s.specimen === 'plant') {
        const group = svgElement('g', { transform: 'translate(6 65) scale(.5)' }); botanyPlant(group, 4, false, '', false); svg.append(group);
      } else if (s.specimen === 'seed') {
        svg.append(svgElement('path', { d: 'M85 87 C130 55 169 118 148 173 C132 211 87 210 69 168 C48 126 62 99 85 87Z', fill: colors.coral, 'fill-opacity': .65, stroke: colors.coral, 'stroke-width': 2 }));
        svg.append(svgElement('path', { d: 'M111 106 C88 122 91 160 114 178', fill: 'none', stroke: colors.paper, 'stroke-width': 5 }));
      } else if (s.specimen === 'flame') {
        svg.append(svgElement('path', { d: 'M110 71 C134 105 107 113 149 141 C182 182 142 221 111 219 C55 212 51 174 74 147 C67 179 93 163 87 144 C77 117 106 111 110 71Z', fill: colors.coral }));
        svg.append(svgElement('path', { d: 'M111 134 C111 165 142 172 129 196 C111 220 83 196 97 178 C100 165 107 155 111 134Z', fill: colors.gold }));
      } else if (s.specimen === 'robot') {
        svg.append(svgElement('rect', { x: 73, y: 91, width: 77, height: 56, rx: 13, fill: colors.blue, 'fill-opacity': .22, stroke: colors.blue, 'stroke-width': 2 }));
        svg.append(svgElement('rect', { x: 64, y: 152, width: 94, height: 55, rx: 10, fill: colors.blue, 'fill-opacity': .18, stroke: colors.blue, 'stroke-width': 2 }));
        [93, 130].forEach(x => svg.append(svgElement('circle', { cx: x, cy: 115, r: 7, fill: colors.gold })));
        [82, 140].forEach(x => svg.append(svgElement('circle', { cx: x, cy: 216, r: 12, fill: colors.ink })));
        line(svg, 111, 90, 111, 73); svg.append(svgElement('circle', { cx: 111, cy: 69, r: 5, fill: colors.coral }));
      } else {
        svg.append(svgElement('path', { d: 'M45 188 L62 127 L104 107 L152 123 L172 185 L128 213 L71 207Z', fill: colors.blue, 'fill-opacity': .25, stroke: colors.blue, 'stroke-width': 2 }));
        svg.append(svgElement('path', { d: 'M62 127 L101 155 L152 123 M101 155 L128 213 M45 188 L101 155 L172 185', fill: 'none', stroke: colors.paper, 'stroke-width': 2 }));
      }
      [['Size', d.size], ['Energy', d.energy], ['Cells', s.inside ? d.cells ? 'Yes' : 'No' : 'Look inside']].forEach(([name, value], i) => {
        const y = 94 + i * 58;
        label(svg, 294, y, name, { 'font-size': 15, fill: colors.blue });
        label(svg, 294, y + 23, value, { 'font-size': 18 });
      });
      label(svg, 210, 291, s.inside ? d.alive ? 'This example is living' : 'This example is not living' : 'One clue is not enough', { 'font-size': 23 });
      label(svg, 210, 327, 'A resting seed can still be alive', { 'font-size': 18 });
    } else if (id === 'bio.2.classification') {
      label(svg, 210, 27, 'Related by ancestry, not just appearance', { 'font-size': 20 });
      const positions = { salmon: [303, 61], frog: [303, 102], mouse: [303, 143], bat: [303, 184], lizard: [303, 225], pigeon: [303, 266],
        vertebrates: [42, 145], tetrapods: [91, 188], amniotes: [141, 210], mammals: [214, 163.5], reptiles: [214, 245.5] };
      Object.entries(d.parents).forEach(([child, parent]) => {
        const a = positions[parent], b = positions[child], first = d.firstPath.includes(child), second = d.secondPath.includes(child);
        svg.append(svgElement('path', { d: 'M' + a.join(' ') + ' V' + b[1] + ' H' + b[0], fill: 'none', stroke: first ? colors.teal : second ? colors.blue : colors.ink,
          'stroke-width': first || second ? 3 : 1, opacity: first || second ? 1 : .3 }));
      });
      Object.entries(positions).forEach(([name, [x, y]]) => {
        const selected = name === s.first || name === s.second;
        svg.append(svgElement('circle', { cx: x, cy: y, r: name === d.common ? 6 : 3.5, fill: name === d.common ? colors.gold : selected ? colors.teal : colors.ink }));
        if (x === 303) {
          label(svg, 355, y + 5, name[0].toUpperCase() + name.slice(1), { 'font-size': 16 });
          if (s.flight && ['bat', 'pigeon'].includes(name)) label(svg, 355, y + 20, 'flies', { 'font-size': 11, fill: colors.blue });
        }
      });
      label(svg, 210, 311, d.same ? 'Same animal selected twice' : 'Shared branch: ' + d.label, { 'font-size': d.label.length > 16 ? 18 : 21 });
      label(svg, 210, 337, 'Branch lengths are not a clock', { 'font-size': 17 });
    } else if (id === 'bio.2.ecosystems') {
      label(svg, 210, 27, 'Trace food → eater through the web', { 'font-size': 22 });
      const positions = { grass: [65, 168], rabbits: [201, 91], mice: [201, 239], foxes: [348, 91], owls: [348, 239] };
      d.edges.forEach(([from, to]) => {
        const a = positions[from], b = positions[to], dx = b[0] - a[0], dy = b[1] - a[1], trim = Math.min(42 / Math.abs(dx), dy === 0 ? 1 : 24 / Math.abs(dy));
        const active = ![from, to].includes(s.removed), highlighted = d.routes.some(route => route.some((node, i) => node === from && route[i + 1] === to));
        const group = svgElement('g', { opacity: active ? 1 : .5, 'stroke-dasharray': active ? 'none' : '4 4' });
        biologyArrow(group, a[0] + dx * trim, a[1] + dy * trim, b[0] - dx * trim, b[1] - dy * trim, !active ? colors.coral : highlighted ? colors.gold : colors.blue); svg.append(group);
      });
      Object.entries(positions).forEach(([name, [x, y]]) => {
        svg.append(svgElement('rect', { x: x - 40, y: y - 22, width: 80, height: 44, rx: 10, fill: colors.paper,
          stroke: name === s.removed ? colors.coral : name === s.target ? colors.gold : colors.teal, 'stroke-width': 2, 'stroke-dasharray': name === s.removed ? '4 4' : 'none' }));
        label(svg, x, y + 5, name[0].toUpperCase() + name.slice(1), { 'font-size': 16 });
        if (name === s.removed) line(svg, x - 33, y + 13, x + 33, y - 13, { stroke: colors.coral, 'stroke-width': 2 });
      });
      label(svg, 210, 300, d.routes.length + ' route' + (d.routes.length === 1 ? '' : 's') + ' from grass to ' + s.target, { 'font-size': 22 });
      label(svg, 210, 332, 'Routes are not population predictions', { 'font-size': 18 });
    } else {
      label(svg, 210, 27, 'Small cells, visible gas bubbles', { 'font-size': 23 });
      const top = 233 - d.gas * 6;
      svg.append(svgElement('path', { d: 'M42 74 L42 276 Q42 282 49 282 H181 Q188 282 188 275 V74', fill: 'none', stroke: colors.blue, 'stroke-width': 2 }));
      svg.append(svgElement('path', { d: 'M45 279 V' + top + ' Q114 ' + (top - 13) + ' 185 ' + top + ' V279Z', fill: colors.gold, 'fill-opacity': .26, stroke: colors.gold }));
      for (let i = 0; i < d.gas; i++) svg.append(svgElement('circle', { cx: 62 + i % 4 * 34, cy: top + 14 + Math.floor(i / 4) * 28, r: 5 + i % 3, fill: colors.paper, stroke: colors.blue }));
      label(svg, 115, 63, 'Dough (schematic)', { 'font-size': 15 });
      const fill = s.yeast ? colors.teal : colors.blue;
      svg.append(svgElement('ellipse', { cx: 289, cy: 106, rx: 31, ry: 39, fill, 'fill-opacity': s.yeast ? .16 : .03, stroke: fill, 'stroke-dasharray': s.yeast ? 'none' : '4 4' }));
      svg.append(svgElement('ellipse', { cx: 320, cy: 75, rx: 15, ry: 20, fill, 'fill-opacity': .13, stroke: fill }));
      svg.append(svgElement('circle', { cx: 280, cy: 114, r: 8, fill: colors.plum, opacity: s.yeast ? 1 : .2 }));
      label(svg, 290, 163, s.yeast ? 'Yeast cell (enlarged)' : 'No active yeast', { 'font-size': 16 });
      label(svg, 294, 204, d.gas + ' CO₂ packets', { 'font-size': 22 });
      label(svg, 294, 239, d.ethanol + ' ethanol packets', { 'font-size': 19 });
      label(svg, 210, 310, 'Glucose used: ' + d.consumed + ' · left: ' + d.left, { 'font-size': 22 });
      label(svg, 210, 337, 'Bubbles can make the dough expand', { 'font-size': 18 });
    }
  }

  function botanyLeaf(svg, x, y, side, size, color) {
    const group = svgElement('g', { transform: 'translate(' + x + ' ' + y + ') scale(' + side * size + ' ' + size + ')' });
    group.append(svgElement('path', { d: 'M0 0 C12 -28 44 -43 70 -35 C59 -7 26 15 0 0Z', fill: color, 'fill-opacity': .68, stroke: color, 'stroke-width': 2 }));
    group.append(svgElement('path', { d: 'M0 0 Q34 -12 70 -35 M20 -8 L21 -23 M36 -16 L41 -31 M36 -16 L53 -12', fill: 'none', stroke: colors.paper, 'stroke-width': 1.3 }));
    svg.append(group);
  }

  function botanyPlant(svg, stage, pale, selected, adult) {
    const foliage = pale ? colors.gold : colors.teal;
    svg.append(svgElement('rect', { x: 45, y: 224, width: 330, height: 67, fill: colors.coral, 'fill-opacity': .08 }));
    line(svg, 45, 224, 375, 224, { stroke: colors.coral, 'stroke-width': 1.5 });
    for (let i = 0; i < 12; i++) svg.append(svgElement('circle', { cx: 62 + i * 26, cy: 245 + i % 3 * 14, r: 1.5, fill: colors.coral, opacity: .3 }));
    if (stage >= 2) {
      svg.append(svgElement('path', { d: 'M210 224 C211 244 205 270 212 284 M208 248 C191 251 184 262 178 270 M209 256 C231 263 237 274 245 282 M207 266 L193 281',
        fill: 'none', stroke: selected === 'roots' ? colors.gold : colors.blue, 'stroke-width': selected === 'roots' ? 4 : 2.5, 'stroke-linecap': 'round' }));
      for (let i = 0; i < 5; i++) line(svg, 206, 248 + i * 6, 201 - i % 2 * 4, 252 + i * 6, { stroke: colors.blue, 'stroke-width': .8 });
    }
    if (stage >= 3) {
      svg.append(svgElement('path', { d: stage === 3 ? 'M210 224 C210 189 237 151 219 153 C207 156 211 170 218 172' : 'M210 224 C209 179 212 151 209 ' + (pale ? 85 : 113),
        fill: 'none', stroke: selected === 'stem' ? colors.gold : foliage, 'stroke-width': 7, 'stroke-linecap': 'round' }));
      if (stage === 4) {
        botanyLeaf(svg, 210, pale ? 114 : 155, -1, pale ? .55 : .95, selected === 'leaves' ? colors.gold : foliage);
        botanyLeaf(svg, 210, pale ? 114 : 155, 1, pale ? .55 : .95, selected === 'leaves' ? colors.gold : foliage);
      }
    }
    if (!adult) {
      const y = stage >= 3 ? stage === 3 ? 173 : pale ? 133 : 179 : 233;
      svg.append(svgElement('ellipse', { cx: 200, cy: y, rx: stage === 0 ? 10 : 13, ry: stage === 0 ? 16 : 20, transform: 'rotate(-23 200 ' + y + ')', fill: colors.coral, 'fill-opacity': .7, stroke: colors.coral }));
      svg.append(svgElement('ellipse', { cx: 220, cy: y, rx: stage === 0 ? 10 : 13, ry: stage === 0 ? 16 : 20, transform: 'rotate(23 220 ' + y + ')', fill: colors.gold, 'fill-opacity': .55, stroke: colors.coral }));
    } else {
      svg.append(svgElement('path', { d: 'M210 164 Q247 151 276 105', fill: 'none', stroke: selected === 'stem' ? colors.gold : foliage, 'stroke-width': 4 }));
      for (let i = 0; i < 5; i++) svg.append(svgElement('ellipse', { cx: 278, cy: 81, rx: 10, ry: 18, transform: 'rotate(' + i * 72 + ' 278 98)',
        fill: selected === 'flower' ? colors.gold : colors.plum, 'fill-opacity': .7, stroke: colors.paper }));
      svg.append(svgElement('circle', { cx: 278, cy: 98, r: 8, fill: colors.gold, stroke: colors.ink }));
    }
  }

  function biologyArrow(svg, x1, y1, x2, y2, color = colors.blue) {
    line(svg, x1, y1, x2, y2, { stroke: color, 'stroke-width': 2 });
    const length = Math.hypot(x2 - x1, y2 - y1), ux = (x2 - x1) / length, uy = (y2 - y1) / length;
    for (const side of [-1, 1]) line(svg, x2, y2, x2 - ux * 7 - uy * side * 4, y2 - uy * 7 + ux * side * 4, { stroke: color, 'stroke-width': 2 });
  }

  function drawBotany(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'bio.0.plants') {
      label(svg, 210, 27, d.name, { 'font-size': 23 });
      botanyPlant(svg, d.stage, d.pale, '', false);
      label(svg, 88, 213, 'Soil', { 'font-size': 15 });
      label(svg, 210, 320, d.pale ? 'A pale shoot uses stored food' : d.stage < 2 ? 'Growth begins inside the seed' : 'Root first, then shoot and leaves', { 'font-size': 19 });
      for (let i = 0; i <= 4; i++) svg.append(svgElement('circle', { cx: 170 + i * 20, cy: 338, r: 3, fill: i <= d.stage ? colors.teal : colors.paper, stroke: colors.teal }));
    } else if (id === 'bio.1.plants-parts') {
      label(svg, 210, 27, s.part[0].toUpperCase() + s.part.slice(1) + ': one part of a living system', { 'font-size': 20 });
      botanyPlant(svg, 4, false, s.part, true);
      label(svg, 89, 261, 'Roots', { 'font-size': 16 }); label(svg, 110, 105, 'Leaves', { 'font-size': 16 });
      label(svg, 314, 196, 'Stem', { 'font-size': 16 }); label(svg, 337, 68, 'Flower', { 'font-size': 16 });
      if (s.flow) {
        biologyArrow(svg, 143, 277, 196, 256); biologyArrow(svg, 216, 243, 216, 180); biologyArrow(svg, 216, 178, 242, 153);
      }
      label(svg, 210, 320, s.flow ? 'Water: soil → roots → stem → leaves' : 'Select a part to highlight its job', { 'font-size': 19 });
    } else if (id === 'bio.2.photosynthesis') {
      label(svg, 210, 26, 'Materials in → sugars and oxygen out', { 'font-size': 21 });
      botanyLeaf(svg, 181, 180, 1, 1, colors.teal);
      if (s.light) {
        svg.append(svgElement('circle', { cx: 210, cy: 65, r: 13, fill: colors.gold, 'fill-opacity': .65, stroke: colors.gold }));
        biologyArrow(svg, 210, 84, 210, 126, colors.gold);
      } else {
        svg.append(svgElement('circle', { cx: 210, cy: 65, r: 13, fill: 'none', stroke: colors.ink, 'stroke-dasharray': '3 3' }));
      }
      [[78, 108, s.carbon + ' CO₂', colors.blue], [78, 222, s.water + ' H₂O', colors.blue],
        [339, 108, d.oxygen + ' O₂', colors.teal], [339, 222, d.sugar + ' sugar', colors.teal]].forEach(([x, y, text, color]) => {
        svg.append(svgElement('rect', { x: x - 52, y: y - 27, width: 104, height: 46, rx: 9, fill: color, 'fill-opacity': .08, stroke: color }));
        label(svg, x, y + 3, text, { 'font-size': 20 });
      });
      biologyArrow(svg, 132, 112, 174, 144); biologyArrow(svg, 132, 215, 174, 183);
      biologyArrow(svg, 248, 144, 283, 113, colors.teal); biologyArrow(svg, 248, 179, 283, 215, colors.teal);
      label(svg, 210, 276, 'Unused: ' + d.carbonLeft + ' CO₂ · ' + d.waterLeft + ' H₂O', { 'font-size': 20 });
      label(svg, 210, 308, 'Atoms conserved: C ' + d.atoms.C + ' · H ' + d.atoms.H + ' · O ' + d.atoms.O, { 'font-size': 18 });
      label(svg, 210, 334, 'Light supplies energy, not atoms', { 'font-size': 18 });
    } else {
      label(svg, 210, 27, 'Food → eater: energy moves forward', { 'font-size': 21 });
      const names = ['Grass', 'Rabbits', 'Foxes'];
      d.levels.forEach((energy, i) => {
        const y = 88 + i * 77;
        label(svg, 249, y - 13, names[i] + ': ' + numberText(energy) + ' units', { 'font-size': 18 });
        svg.append(svgElement('rect', { x: 125, y, width: 260, height: 22, fill: colors.teal, 'fill-opacity': .05, stroke: colors.ink, 'stroke-width': .5 }));
        svg.append(svgElement('rect', { x: 125, y, width: 260 * energy / 1000, height: 22, fill: colors.teal }));
        if (i < 2) biologyArrow(svg, 76, y + 22, 76, y + 47, colors.gold);
      });
      for (let i = 0; i < 5; i++) svg.append(svgElement('path', { d: 'M' + (58 + i * 8) + ' 107 Q' + (43 + i * 13) + ' 83 ' + (51 + i * 11) + ' 68 Q' + (58 + i * 8) + ' 87 ' + (62 + i * 8) + ' 107Z', fill: colors.teal }));
      svg.append(svgElement('path', { d: 'M49 183 C41 163 59 148 77 158 L76 134 Q83 124 87 155 Q98 148 100 160 L108 169 L101 175 L92 175 L92 184Z', fill: colors.plum, 'fill-opacity': .65, stroke: colors.plum }));
      svg.append(svgElement('circle', { cx: 45, cy: 175, r: 6, fill: colors.paper, stroke: colors.plum }));
      svg.append(svgElement('circle', { cx: 95, cy: 162, r: 1.5, fill: colors.ink }));
      svg.append(svgElement('path', { d: 'M49 255 Q24 244 31 227 Q39 237 57 239 Q77 232 88 242 L88 228 L98 238 L108 233 L108 247 L118 251 L106 257 L91 256 L86 263 L81 253 L62 256 L56 264Z', fill: colors.coral, 'fill-opacity': .75, stroke: colors.coral }));
      svg.append(svgElement('circle', { cx: 105, cy: 245, r: 1.5, fill: colors.ink }));
      label(svg, 210, 300, 'Only ' + s.percent + '% reaches each next level', { 'font-size': 21 });
      label(svg, 210, 333, 'Heat, waste and uneaten food take other paths', { 'font-size': 16 });
    }
  }

  function drawFinalMath(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'math.5.diffgeo') {
      label(svg, 210, 26, 'A triangle with two right angles', { 'font-size': 22 });
      const project = (longitude, latitude) => [210 + 94 * Math.cos(latitude) * Math.sin(longitude),
        151 + 94 * (.5 * Math.cos(latitude) * Math.cos(longitude) - Math.sqrt(3) / 2 * Math.sin(latitude))];
      const half = d.excess / 2, points = [];
      for (let i = 0; i <= 30; i++) points.push(project(-half, Math.PI / 2 * (1 - i / 30)));
      const equator = [];
      for (let i = 0; i <= 30; i++) { const p = project(-half + 2 * half * i / 30, 0); points.push(p); equator.push(p); }
      for (let i = 0; i <= 30; i++) points.push(project(half, Math.PI / 2 * i / 30));
      svg.append(svgElement('circle', { cx: 210, cy: 151, r: 94, fill: colors.blue, 'fill-opacity': .06, stroke: colors.blue }));
      svg.append(svgElement('ellipse', { cx: 210, cy: 151, rx: 94, ry: 47, fill: 'none', stroke: colors.blue, 'stroke-dasharray': '3 4', opacity: .4 }));
      svg.append(svgElement('polygon', { points: points.map(p => p.join(',')).join(' '), fill: colors.teal, 'fill-opacity': .22, stroke: colors.teal, 'stroke-width': 2 }));
      svg.append(svgElement('polyline', { points: equator.map(p => p.join(',')).join(' '), fill: 'none', stroke: colors.gold, 'stroke-width': 3 }));
      label(svg, 210, 49, 'α = ' + s.angle + '°', { 'font-size': 16 });
      label(svg, 210, 271, '90° + 90° + ' + s.angle + '° = ' + d.angleSum + '°', { 'font-size': 21 });
      label(svg, 210, 301, 'K = 1/' + numberText(s.radius ** 2) + '   A = ' + numberText(d.area), { 'font-size': 20 });
      label(svg, 210, 332, 'KA = ' + numberText(d.excess) + ' radians of excess', { 'font-size': 19 });
    } else if (id === 'math.5.complex-analysis') {
      const x = value => 210 + 34 * value, y = value => 162 - 34 * value;
      label(svg, 210, 26, 'f(z) = ' + s.a + '/z + ' + s.b + '/(z−2)', { 'font-size': 22 });
      line(svg, 91, 162, 329, 162, { opacity: .3 }); line(svg, 210, 43, 210, 281, { opacity: .3 });
      svg.append(svgElement('circle', { cx: 210, cy: 162, r: 34 * s.radius, fill: colors.blue, 'fill-opacity': .04, stroke: colors.blue, 'stroke-width': 2 }));
      const t = Math.PI * .65, tip = [x(s.radius * Math.cos(t)), y(s.radius * Math.sin(t))];
      const tangent = [-Math.sin(t) * d.direction, -Math.cos(t) * d.direction];
      for (const side of [-1, 1]) line(svg, ...tip, tip[0] - tangent[0] * 10 - tangent[1] * 5 * side,
        tip[1] - tangent[1] * 10 + tangent[0] * 5 * side, { stroke: colors.blue, 'stroke-width': 2.5 });
      [[0, s.a], [2, s.b]].forEach(([position, residue]) => {
        svg.append(svgElement('circle', { cx: x(position), cy: 162, r: 5, fill: residue ? colors.coral : colors.paper, stroke: colors.ink }));
        label(svg, x(position), 186, String(position), { 'font-size': 14 });
      });
      label(svg, 210, 302, d.onPath ? 'Pole on path: integral undefined' : '∮ f(z) dz = 2πi × ' + d.multiplier, { 'font-size': 21 });
      label(svg, 210, 333, 'r = ' + s.radius + ' · ' + (s.clockwise ? 'clockwise' : 'counterclockwise'), { 'font-size': 18 });
    } else {
      label(svg, 210, 26, 'Is element j in subset f(i)?', { 'font-size': 23 });
      const cell = (column, row, bit, diagonal, result) => {
        const x = 107 + 34 * column, y = 62 + 27 * row;
        svg.append(svgElement('rect', { x, y, width: 29, height: 23, rx: 3,
          fill: result ? colors.teal : diagonal ? colors.gold : colors.paper, stroke: colors.ink, 'stroke-width': .5 }));
        label(svg, x + 14.5, y + 16, String(bit), { 'font-size': 14, fill: result ? colors.paper : colors.ink });
      };
      for (let j = 0; j < 6; j++) label(svg, 121.5 + 34 * j, 52, String(j + 1), { 'font-size': 14 });
      d.rows.forEach((row, i) => { label(svg, 75, 78 + 27 * i, 'f(' + (i + 1) + ')', { 'font-size': 15 }); row.forEach((bit, j) => cell(j, i, bit, i === j, false)); });
      line(svg, 64, 236, 319, 236, { stroke: colors.teal });
      label(svg, 75, 267, 'D', { 'font-size': 18 });
      d.diagonal.forEach((bit, j) => cell(j, 7, bit, false, true));
      label(svg, 210, 304, 'D = {' + d.members.join(', ') + '}', { 'font-size': 20 });
      label(svg, 210, 334, 'D(i) = 1 − f(i)(i): every row differs', { 'font-size': 18 });
    }
  }

  function drawStageFour(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'math.4.diffeq') {
      const px = t => 66 + 145 * t, py = y => 166 - y * 25;
      label(svg, 210, 28, 'y′ = −' + s.rate + 'y · y(0) = ' + s.initial, { 'font-size': 23 });
      line(svg, px(0), py(0), px(2), py(0)); line(svg, px(0), py(-4), px(0), py(4));
      [-4, 0, 4].forEach(y => label(svg, 44, py(y) + 4, String(y), { 'font-size': 12 }));
      [0, 1, 2].forEach(t => label(svg, px(t), 285, String(t), { 'font-size': 12 }));
      for (let i = 0; i < 100; i++) { const t = i / 50; line(svg, px(t), py(s.initial * Math.exp(-s.rate * t)), px(t + .02), py(s.initial * Math.exp(-s.rate * (t + .02))), { stroke: colors.blue, 'stroke-width': 2.5 }); }
      d.values.forEach((v, i) => {
        if (i) line(svg, px((i - 1) * d.h), py(d.values[i - 1]), px(i * d.h), py(v), { stroke: colors.gold, 'stroke-width': 2 });
        svg.append(svgElement('circle', { cx: px(i * d.h), cy: py(v), r: 3, fill: colors.gold }));
      });
      label(svg, 210, 311, 'Euler ' + numberText(d.approximate) + ' · exact ' + numberText(d.exact), { 'font-size': 20 });
      label(svg, 210, 339, 'Step h = ' + numberText(d.h), { 'font-size': 17 });
    } else if (id === 'math.4.discrete') {
      const points = [[115, 83], [305, 83], [305, 235], [115, 235]];
      label(svg, 210, 28, d.kind === 'none' ? 'No Euler trail' : d.kind === 'empty' ? 'Empty graph' : 'Euler ' + d.kind, { 'font-size': 24 });
      const traced = new Set();
      if (d.possible) for (let i = 0; i < d.traced; i++) traced.add([d.walk[i], d.walk[i + 1]].sort().join(''));
      d.edges.forEach(([a, b]) => line(svg, ...points[a], ...points[b], { stroke: traced.has([a, b].sort().join('')) ? colors.gold : colors.blue, 'stroke-width': 3 }));
      points.forEach(([x, y], i) => {
        svg.append(svgElement('circle', { cx: x, cy: y, r: 17, fill: d.degrees[i] % 2 ? colors.coral : colors.teal }));
        label(svg, x, y + 6, 'ABCD'[i], { fill: colors.paper, 'font-size': 18 });
        label(svg, x, y + (i < 2 ? -27 : 37), 'degree ' + d.degrees[i], { 'font-size': 15 });
      });
      label(svg, 210, 312, 'Degree sum ' + d.degrees.reduce((a, b) => a + b, 0) + ' = 2 × ' + d.edges.length, { 'font-size': 20 });
      label(svg, 210, 339, d.possible && d.walk.length ? d.walk.slice(0, d.traced + 1).map(i => 'ABCD'[i]).join(' → ') : d.connected ? d.odd.length + ' odd-degree vertices' : 'Disconnected non-isolated vertices', { 'font-size': 16 });
    } else if (id === 'math.4.numtheory') {
      label(svg, 210, 28, 'Euclid: remainder becomes divisor', { 'font-size': 21 });
      d.divisions.forEach((row, i) => {
        const y = 65 + i * 25;
        svg.append(svgElement('rect', { x: 40, y: y - 17, width: 340, height: 23, rx: 4, fill: i === d.divisions.length - 1 ? colors.gold : colors.teal, 'fill-opacity': .15 }));
        label(svg, 210, y, row.dividend + ' = ' + row.q + ' × ' + row.divisor + ' + ' + row.remainder, { 'font-size': 17 });
      });
      label(svg, 210, 290, 'gcd = ' + d.gcd, { 'font-size': 24 });
      label(svg, 210, 327, '(' + d.x + ')×' + s.a + ' + (' + d.y + ')×' + s.b + ' = ' + d.gcd, { 'font-size': 20 });
    } else if (id === 'math.4.analysis') {
      const px = h => 210 + 145 * h, py = error => 168 - error * 15;
      label(svg, 210, 28, d.works ? 'This δ works for the chosen ε' : 'This δ is too large', { 'font-size': 22 });
      svg.append(svgElement('rect', { x: 65, y: py(s.epsilon), width: 290, height: 30 * s.epsilon, fill: colors.teal, 'fill-opacity': .2 }));
      svg.append(svgElement('rect', { x: px(-s.delta), y: 63, width: 290 * s.delta, height: 210, fill: colors.gold, 'fill-opacity': .15 }));
      line(svg, 65, py(0), 355, py(0)); line(svg, 210, 63, 210, 273, { opacity: .3 });
      for (let i = 0; i < 100; i++) { const h = -1 + i / 50, next = h + .02; line(svg, px(h), py(2 * s.a * h + h * h), px(next), py(2 * s.a * next + next * next), { stroke: colors.blue, 'stroke-width': 2 }); }
      [-1, 0, 1].forEach(h => label(svg, px(h), 291, String(h), { 'font-size': 12 }));
      label(svg, 210, 317, 'δ ' + s.delta + ' · ε ' + s.epsilon + ' · bound ' + numberText(d.bound), { 'font-size': 20 });
      label(svg, 210, 341, 'Horizontal: h = x−a · vertical: x²−a²', { 'font-size': 14 });
    } else {
      const px = k => 68 + k * 27, py = p => 265 - p * 190;
      label(svg, 210, 28, 'Binomial: n=' + s.n + ', p=' + s.percent / 100, { 'font-size': 24 });
      line(svg, 49, py(0), 355, py(0)); line(svg, 49, py(0), 49, py(1));
      [0, .5, 1].forEach(p => label(svg, 31, py(p) + 4, String(p), { 'font-size': 12 }));
      d.probabilities.forEach((p, k) => svg.append(svgElement('rect', { x: px(k) - 10, y: py(p), width: 20, height: 190 * p, fill: k <= s.cutoff ? colors.gold : colors.blue })));
      for (let k = 0; k <= 10; k++) label(svg, px(k), 285, String(k), { 'font-size': 12 });
      label(svg, 210, 312, 'P(X ≤ ' + s.cutoff + ') ≈ ' + numberText(d.cumulative * 100) + '%', { 'font-size': 22 });
      label(svg, 210, 339, 'Mean ' + numberText(d.mean) + ' · variance ' + numberText(d.variance), { 'font-size': 18 });
    }
  }

  function drawCalculusGeometry(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'math.3.euclid') {
      const unit = 230 / (s.a + s.b), p = (x, y) => (95 + x * unit) + ',' + (60 + y * unit), L = s.a + s.b;
      label(svg, 210, 28, s.rearranged ? 'Uncovered: a² + b²' : 'Uncovered: c²', { 'font-size': 24 });
      svg.append(svgElement('rect', { x: 95, y: 60, width: 230, height: 230, fill: colors.gold, 'fill-opacity': .2, stroke: colors.ink }));
      const triangles = s.rearranged ? [
        [[s.a, 0], [L, 0], [s.a, s.a]], [[L, 0], [L, s.a], [s.a, s.a]],
        [[0, s.a], [s.a, s.a], [0, L]], [[s.a, s.a], [s.a, L], [0, L]],
      ] : [[[0, 0], [s.a, 0], [0, s.b]], [[L, 0], [L, s.a], [s.a, 0]],
        [[L, L], [s.b, L], [L, s.a]], [[0, L], [0, s.b], [s.b, L]]];
      triangles.forEach(points => svg.append(svgElement('polygon', { points: points.map(v => p(...v)).join(' '), fill: colors.teal, 'fill-opacity': .7, stroke: colors.paper, 'stroke-width': 1.5 })));
      if (s.rearranged) {
        label(svg, 95 + s.a * unit / 2, 66 + s.a * unit / 2, 'a²', { 'font-size': 18 });
        label(svg, 95 + (s.a + s.b / 2) * unit, 66 + (s.a + s.b / 2) * unit, 'b²', { 'font-size': 18 });
      } else label(svg, 210, 181, 'c²', { 'font-size': 26 });
      label(svg, 210, 331, s.a ** 2 + ' + ' + s.b ** 2 + ' = ' + d.remaining, { 'font-size': 25 });
    } else if (id === 'math.4.complex') {
      const px = x => 210 + 15 * x, py = y => 162 - 15 * y;
      label(svg, 210, 28, 'Rotate ' + 90 * s.turns + '° · scale ×' + s.scale, { 'font-size': 24 });
      for (let n = -6; n <= 6; n += 2) {
        line(svg, px(n), py(-7), px(n), py(7), { opacity: .1 }); line(svg, px(-7), py(n), px(7), py(n), { opacity: .1 });
        label(svg, px(n), 288, String(n), { 'font-size': 11 });
        if (n) label(svg, 92, py(n) + 4, String(n), { 'font-size': 11 });
      }
      line(svg, px(-7), py(0), px(7), py(0)); line(svg, px(0), py(-7), px(0), py(7));
      [[s.real, s.imaginary, colors.blue], [d.real, d.imaginary, colors.coral]].forEach(([x, y, color]) => {
        line(svg, px(0), py(0), px(x), py(y), { stroke: color, 'stroke-width': 3 });
        svg.append(svgElement('circle', { cx: px(x), cy: py(y), r: 4, fill: color }));
      });
      label(svg, 345, 167, 'Re', { 'font-size': 14 }); label(svg, 210, 49, 'Im', { 'font-size': 13 });
      label(svg, 210, 331, '(' + s.real + ', ' + s.imaginary + ') → (' + d.real + ', ' + d.imaginary + ')', { 'font-size': 23 });
    } else if (id === 'math.4.diff-calc') {
      const px = x => 210 + 50 * x, py = y => 263 - 21 * (y + 1), f = x => s.mode === 'square' ? x * x : Math.abs(x);
      label(svg, 210, 28, d.derivative === null ? 'A corner has no tangent slope' : 'Secant → tangent', { 'font-size': 22 });
      line(svg, px(-3), py(0), px(3), py(0)); line(svg, px(0), py(-1), px(0), py(9), { opacity: .3 });
      for (let i = 0; i < 120; i++) { const x = -3 + i / 20; line(svg, px(x), py(f(x)), px(x + .05), py(f(x + .05)), { stroke: colors.blue, 'stroke-width': 2 }); }
      const slopeLine = (slope, color, dash) => {
        let lo = -3, hi = 3;
        if (slope) { const edges = [s.x + (-1 - d.y) / slope, s.x + (9 - d.y) / slope].sort((a, b) => a - b); lo = Math.max(lo, edges[0]); hi = Math.min(hi, edges[1]); }
        line(svg, px(lo), py(d.y + slope * (lo - s.x)), px(hi), py(d.y + slope * (hi - s.x)), { stroke: color, 'stroke-width': 2, 'stroke-dasharray': dash });
      };
      slopeLine(d.secant, colors.gold, 'none'); if (d.derivative !== null) slopeLine(d.derivative, colors.coral, '6 4');
      [[s.x, d.y], [d.otherX, d.otherY]].forEach(([x, y]) => svg.append(svgElement('circle', { cx: px(x), cy: py(y), r: 4, fill: colors.gold })));
      [-3, 0, 3].forEach(x => label(svg, px(x), 282, String(x), { 'font-size': 12 }));
      [0, 4, 8].forEach(y => label(svg, 43, py(y) + 4, String(y), { 'font-size': 12 }));
      label(svg, 210, 308, 'h ' + d.h + ' · secant ' + numberText(d.secant), { 'font-size': 20 });
      label(svg, 210, 336, 'Derivative: ' + (d.derivative === null ? 'does not exist' : d.derivative), { 'font-size': 18 });
    } else {
      const px = x => 64 + 48 * x, py = y => 270 - (y + 3) * 23;
      label(svg, 210, 28, s.count + ' ' + s.method + ' rectangles', { 'font-size': 23 });
      d.rectangles.forEach(r => svg.append(svgElement('rect', { x: px(r.start), y: Math.min(py(0), py(r.height)), width: r.width * 48,
        height: Math.abs(r.height) * 23, fill: r.height >= 0 ? colors.teal : colors.coral, 'fill-opacity': .35, stroke: colors.paper, 'stroke-width': .7 })));
      line(svg, px(0), py(-s.shift), px(6), py(6 - s.shift), { stroke: colors.blue, 'stroke-width': 2.5 });
      line(svg, px(0), py(0), px(6), py(0)); line(svg, px(0), py(-3), px(0), py(6));
      [0, 2, 4, 6].forEach(x => label(svg, px(x), 286, String(x), { 'font-size': 12 }));
      [-3, 0, 3, 6].forEach(y => label(svg, 45, py(y) + 4, String(y), { 'font-size': 12 }));
      label(svg, 210, 310, 'Sum ' + numberText(d.sum) + ' · integral ' + numberText(d.exact), { 'font-size': 22 });
      label(svg, 210, 339, 'Error ' + numberText(d.error), { 'font-size': 18 });
    }
  }

  function drawEvidence(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'math.3.probability') {
      label(svg, 210, 28, 'Sum ' + (s.cumulative ? '≤ ' : '= ') + s.target, { 'font-size': 24 });
      label(svg, 210, 53, 'Second die →', { 'font-size': 15 });
      for (let n = 1; n <= 6; n++) {
        label(svg, 97 + (n - 1) * 44, 76, String(n), { 'font-size': 15 });
        label(svg, 57, 103 + (n - 1) * 33, String(n), { 'font-size': 15 });
      }
      d.outcomes.forEach(p => {
        const x = 78 + (p.second - 1) * 44, y = 83 + (p.first - 1) * 33;
        svg.append(svgElement('rect', { x, y, width: 38, height: 27, rx: 4, fill: p.selected ? colors.teal : colors.paper, stroke: colors.ink, 'stroke-width': .6 }));
        label(svg, x + 19, y + 19, String(p.sum), { 'font-size': 15, fill: p.selected ? colors.paper : colors.ink });
      });
      label(svg, 210, 301, 'Rows: first die · cells: sums', { 'font-size': 17 });
      label(svg, 210, 334, d.count + ' favourable / 36 outcomes', { 'font-size': 22 });
    } else if (id === 'math.3.statistics') {
      const px = v => 72 + (v + 10) * 6;
      label(svg, 210, 27, s.sample ? 'Sample SD: divide by n − 1' : 'Population SD: divide by n', { 'font-size': 22 });
      line(svg, px(d.mean), 63, px(d.mean), 228, { stroke: colors.coral, 'stroke-width': 2 });
      d.values.forEach((v, i) => {
        const y = 77 + i * 32;
        label(svg, 39, y + 5, 'ABCDE'[i], { 'font-size': 15 });
        line(svg, px(d.mean), y, px(v), y, { stroke: colors.gold, 'stroke-width': 3 });
        svg.append(svgElement('circle', { cx: px(v), cy: y, r: 5, fill: colors.blue }));
        label(svg, 382, y + 5, String(v), { 'font-size': 15 });
      });
      line(svg, px(-10), 236, px(35), 236);
      [-10, 0, 10, 20, 30].forEach(v => label(svg, px(v), 256, String(v), { 'font-size': 12 }));
      label(svg, 210, 298, 'Mean ' + numberText(d.mean) + ' · SD ' + numberText(d.sd), { 'font-size': 23 });
      label(svg, 210, 331, 'Squared deviations sum: ' + numberText(d.squaredSum), { 'font-size': 18 });
    } else if (id === 'math.3.precalc') {
      const px = offset => 210 + offset * 140, py = y => 247 - y * 23;
      label(svg, 210, 28, d.limit === null ? 'One-sided limits disagree' : 'Both sides approach ' + d.limit, { 'font-size': 23 });
      line(svg, 54, py(0), 370, py(0)); line(svg, 210, 54, 210, 256, { opacity: .3 });
      [0, 2, 4, 6, 8].forEach(y => label(svg, 38, py(y) + 4, String(y), { 'font-size': 12 }));
      if (s.mode === 'hole') line(svg, px(-1), py(2 * s.a - 1), px(1), py(2 * s.a + 1), { stroke: colors.blue, 'stroke-width': 3 });
      else {
        line(svg, px(-1), py(s.a), px(0), py(s.a), { stroke: colors.blue, 'stroke-width': 3 });
        line(svg, px(0), py(s.a + 2), px(1), py(s.a + 2), { stroke: colors.blue, 'stroke-width': 3 });
      }
      [...new Set([d.leftLimit, d.rightLimit])].forEach(y => svg.append(svgElement('circle', { cx: px(0), cy: py(y), r: 6, fill: colors.paper, stroke: colors.blue, 'stroke-width': 2 })));
      [[-d.h, d.left], [d.h, d.right]].forEach(([x, y]) => svg.append(svgElement('circle', { cx: px(x), cy: py(y), r: 4, fill: colors.gold })));
      svg.append(svgElement('circle', { cx: px(0), cy: py(s.point), r: 4, fill: colors.coral }));
      label(svg, 210, 276, 'x = a = ' + s.a + ' · h = ' + d.h, { 'font-size': 20 });
      label(svg, 210, 311, 'Left ' + d.left + ' · right ' + d.right, { 'font-size': 19 });
      label(svg, 210, 339, 'Chosen f(a) = ' + s.point, { 'font-size': 17 });
    } else {
      const bound = 20 / s.zoom, px = x => 210 + 53 * x, py = y => 175 - 100 * y / bound;
      const value = x => d.a * (x - s.r1) * (x - s.r2) * (x - s.r3);
      label(svg, 210, 27, 'Cubic: three factors', { 'font-size': 24 });
      line(svg, px(-3), py(0), px(3), py(0)); line(svg, px(0), py(-bound), px(0), py(bound), { opacity: .3 });
      for (let i = 0; i < 240; i++) {
        const x1 = -3 + i / 40, x2 = -3 + (i + 1) / 40, y1 = value(x1), y2 = value(x2);
        let lo = 0, hi = 1;
        if (y1 === y2) { if (Math.abs(y1) > bound) continue; }
        else { const bounds = [(-bound - y1) / (y2 - y1), (bound - y1) / (y2 - y1)].sort((a, b) => a - b); lo = Math.max(0, bounds[0]); hi = Math.min(1, bounds[1]); }
        if (lo <= hi) line(svg, px(x1 + (x2 - x1) * lo), py(y1 + (y2 - y1) * lo), px(x1 + (x2 - x1) * hi), py(y1 + (y2 - y1) * hi), { stroke: colors.blue, 'stroke-width': 2.5 });
      }
      [-3, -2, -1, 0, 1, 2, 3].forEach(x => label(svg, px(x), 294, String(x), { 'font-size': 13 }));
      [-bound, 0, bound].forEach(y => label(svg, 29, py(y) + 4, numberText(y), { 'font-size': 12 }));
      d.distinct.forEach(r => svg.append(svgElement('circle', { cx: px(r.root), cy: py(0), r: 5, fill: colors.gold })));
      label(svg, 210, 329, 'Coefficients: ' + [d.a, d.b, d.c, d.constant].join(', '), { 'font-size': 22 });
    }
  }

  function drawGrowthTrig(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'math.3.trig') {
      const cx = 210, cy = 168, r = 100, x = cx + r * d.cosine, y = cy - r * d.sine;
      label(svg, 210, 28, s.angle + '° around a unit circle', { 'font-size': 23 });
      svg.append(svgElement('circle', { cx, cy, r, fill: 'none', stroke: colors.ink, 'stroke-width': 1.5 }));
      line(svg, 90, cy, 330, cy, { opacity: .4 }); line(svg, cx, 48, cx, 282, { opacity: .4 });
      line(svg, cx, cy, x, y, { stroke: colors.blue, 'stroke-width': 3 });
      line(svg, cx, cy, x, cy, { stroke: colors.gold, 'stroke-width': 4 });
      line(svg, x, cy, x, y, { stroke: colors.coral, 'stroke-width': 4 });
      svg.append(svgElement('circle', { cx: x, cy: y, r: 5, fill: colors.blue }));
      label(svg, 343, 173, 'x'); label(svg, 210, 59, 'y', { 'font-size': 14 });
      label(svg, 80, 173, '−1', { 'font-size': 13 }); label(svg, 317, 185, '1', { 'font-size': 13 });
      label(svg, 210, 309, 'cos θ = ' + numberText(d.cosine) + ' · sin θ = ' + numberText(d.sine), { 'font-size': 21 });
      label(svg, 210, 338, 'tan θ: ' + (d.tangent === null ? 'undefined' : numberText(d.tangent)), { 'font-size': 18 });
    } else if (id === 'math.3.expo-logs') {
      label(svg, 210, 29, 'Base ' + s.base + ': two inverse maps', { 'font-size': 24 });
      const row = (y, left, right, operation, color) => {
        [75, 345].forEach(x => svg.append(svgElement('rect', { x: x - 53, y: y - 28, width: 106, height: 56, rx: 8, fill: colors.paper, stroke: color, 'stroke-width': 2 })));
        line(svg, 134, y, 282, y, { stroke: color, 'stroke-width': 2 });
        line(svg, 271, y - 5, 282, y, { stroke: color }); line(svg, 271, y + 5, 282, y, { stroke: color });
        label(svg, 75, y + 8, left, { 'font-size': 23 }); label(svg, 345, y + 8, right, { 'font-size': 23 });
        label(svg, 210, y - 15, operation, { 'font-size': 18 });
      };
      row(102, String(s.exponent), d.exact, s.base + ' to this power', colors.blue);
      row(207, d.exact, String(s.exponent), 'log base ' + s.base, colors.teal);
      label(svg, 210, 276, 'x → bˣ → logᵦ(bˣ) = x', { 'font-size': 23 });
      label(svg, 210, 323, s.exponent < 0 ? 'Negative exponent → positive reciprocal' : s.exponent === 0 ? 'Every allowed base to power 0 gives 1' : 'Multiply the base ' + s.exponent + ' times', { 'font-size': 17 });
    } else {
      const px = i => 63 + i * 59, py = v => 260 - v * 150 / d.maximum;
      label(svg, 210, 28, s.mode === 'arithmetic' ? 'Same difference: +' + s.step : 'Same ratio: ×' + s.step, { 'font-size': 24 });
      line(svg, 40, 260, 380, 260); line(svg, 40, 90, 40, 260);
      label(svg, 24, 264, '0', { 'font-size': 12 });
      d.values.forEach((value, i) => {
        label(svg, px(i), 65, String(value), { 'font-size': 16 });
        if (i) line(svg, px(i - 1), py(d.values[i - 1]), px(i), py(value), { stroke: colors.teal, 'stroke-width': 2 });
        line(svg, px(i), 260, px(i), py(value), { stroke: colors.blue, opacity: .25 });
        svg.append(svgElement('circle', { cx: px(i), cy: py(value), r: 5, fill: colors.blue }));
        label(svg, px(i), 286, 'n=' + (i + 1), { 'font-size': 14 });
      });
      label(svg, 210, 331, 'Sum of ' + s.count + ' terms = ' + d.sum, { 'font-size': 23 });
    }
  }

  function drawIntersections(svg, current, id) {
    const s = current.state, d = current.data, system = id === 'math.3.systems';
    const xMax = system ? 7 : 5, yMin = system ? -10 : -5, yMax = 10;
    const px = x => 210 + x * 170 / xMax, py = y => 286 - (y - yMin) * 230 / (yMax - yMin);
    const segment = (x1, y1, x2, y2, attrs) => {
      // Clip each mathematical segment to the visible y-range before projection.
      let lo = 0, hi = 1;
      if (y2 === y1) { if (y1 < yMin || y1 > yMax) return; }
      else {
        const bounds = [(yMin - y1) / (y2 - y1), (yMax - y1) / (y2 - y1)].sort((a, b) => a - b);
        lo = Math.max(lo, bounds[0]); hi = Math.min(hi, bounds[1]);
        if (lo > hi) return;
      }
      line(svg, px(x1 + (x2 - x1) * lo), py(y1 + (y2 - y1) * lo),
        px(x1 + (x2 - x1) * hi), py(y1 + (y2 - y1) * hi), attrs);
    };
    for (let y = yMin; y <= yMax; y += 5) {
      line(svg, 40, py(y), 380, py(y), { stroke: colors.ink, opacity: .15 });
      label(svg, 22, py(y) + 4, String(y), { 'font-size': 12 });
    }
    [-xMax, 0, xMax].forEach(x => label(svg, px(x), 303, String(x), { 'font-size': 12 }));
    line(svg, 40, py(0), 380, py(0)); line(svg, px(0), 56, px(0), 286);
    label(svg, 395, py(0) + 4, 'x', { 'font-size': 14 });
    const point = (x, y, color) => svg.append(svgElement('circle', { cx: px(x), cy: py(y), r: 5, fill: color }));
    if (system) {
      segment(-xMax, -xMax * s.m1 + s.b1, xMax, xMax * s.m1 + s.b1, { stroke: colors.blue, 'stroke-width': 3 });
      segment(-xMax, -xMax * s.m2 + s.b2, xMax, xMax * s.m2 + s.b2, { stroke: colors.coral, 'stroke-width': 3, 'stroke-dasharray': '7 5' });
      if (d.kind === 'one') point(d.x, d.y, colors.gold);
      label(svg, 210, 28, d.kind === 'one' ? 'One shared point' : d.kind === 'none' ? 'Parallel: no solution' : 'Same line: infinitely many', { 'font-size': 22 });
      label(svg, 210, 333, d.kind === 'one' ? '(' + numberText(d.x) + ', ' + numberText(d.y) + ')' :
        d.kind === 'none' ? 'Equal slopes, different intercepts' : 'Equal slopes and equal intercepts', { 'font-size': 18 });
    } else {
      const value = x => d.a * (x - s.h) ** 2 + s.k;
      for (let i = 0; i < 200; i++) {
        const x1 = -xMax + i * 2 * xMax / 200, x2 = -xMax + (i + 1) * 2 * xMax / 200;
        segment(x1, value(x1), x2, value(x2), { stroke: colors.blue, 'stroke-width': 2.5 });
      }
      point(s.h, s.k, colors.coral);
      d.roots.forEach(x => point(x, 0, colors.gold));
      label(svg, 210, 28, d.roots.length === 1 ? 'One repeated real root' : d.roots.length + ' real roots', { 'font-size': 23 });
      label(svg, 210, 333, 'Vertex (' + s.h + ', ' + s.k + ') · ' + (d.a > 0 ? 'minimum' : 'maximum'), { 'font-size': 20 });
    }
  }

  function drawLinear(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'math.3.linear') {
      label(svg, 210, 34, 'Equivalent equations', { 'font-size': 24 });
      [[d.left, 102], [d.right, 318]].forEach(([text, x]) => {
        svg.append(svgElement('rect', { x: x - 88, y: 90, width: 176, height: 84, rx: 10,
          fill: colors.paper, stroke: colors.teal, 'stroke-width': 2 }));
        label(svg, x, 140, text, { 'font-size': 24 });
      });
      label(svg, 210, 140, '=', { 'font-size': 28 });
      // A level balance makes the equality invariant visible at every step.
      line(svg, 40, 181, 380, 181, { stroke: colors.teal, 'stroke-width': 3 });
      line(svg, 210, 181, 210, 197, { stroke: colors.teal, 'stroke-width': 3 });
      line(svg, 190, 197, 230, 197, { stroke: colors.teal, 'stroke-width': 3 });
      label(svg, 210, 218, ['Start: ax + b = c', 'Subtract (' + s.b + ') from both sides',
        'Divide both sides by ' + s.a][s.step], { 'font-size': 20 });
      label(svg, 210, 273, 'Solution: x = ' + d.difference + '/' + s.a, { 'font-size': 24 });
      label(svg, 210, 318, 'Same solution at every step', { 'font-size': 18 });
    } else {
      const px = x => 100 + x * 36, py = y => 170 - y * 17;
      for (let y = -7; y <= 7; y++) line(svg, px(-2), py(y), px(6), py(y), { stroke: colors.ink, opacity: .12 });
      for (let x = -2; x <= 6; x++) line(svg, px(x), py(-7), px(x), py(7), { stroke: colors.ink, opacity: .12 });
      [-6, -3, 0, 3, 6].forEach(y => label(svg, 16, py(y) + 4, String(y), { 'font-size': 12 }));
      [-2, 0, 2, 4, 6].forEach(x => label(svg, px(x), 304, String(x), { 'font-size': 12 }));
      line(svg, px(-2), py(0), px(6), py(0)); line(svg, px(0), py(-7), px(0), py(7));
      // Clip the infinite line analytically to the displayed coordinate window.
      let lo = -2, hi = 6;
      if (d.slope) {
        const edges = [(-7 - s.intercept) / d.slope, (7 - s.intercept) / d.slope].sort((a, b) => a - b);
        lo = Math.max(lo, edges[0]); hi = Math.min(hi, edges[1]);
      }
      line(svg, px(lo), py(d.slope * lo + s.intercept), px(hi), py(d.slope * hi + s.intercept), { stroke: colors.blue, 'stroke-width': 3 });
      line(svg, px(0), py(d.y1), px(d.x2), py(d.y1), { stroke: colors.gold, 'stroke-width': 3 });
      line(svg, px(d.x2), py(d.y1), px(d.x2), py(d.y2), { stroke: colors.coral, 'stroke-width': 3 });
      [[0, d.y1], [d.x2, d.y2]].forEach(([x, y]) => svg.append(svgElement('circle', { cx: px(x), cy: py(y), r: 5, fill: colors.teal })));
      label(svg, 210, 27, 'Slope = ' + s.rise + '/' + s.run, { 'font-size': 24 });
      label(svg, 210, 323, 'Run ' + s.run + ' · rise ' + s.rise + ' · intercept ' + s.intercept, { 'font-size': 19 });
      label(svg, 340, 176, 'x'); label(svg, 100, 42, 'y');
    }
  }

  function drawStageTwo(svg, current, id) {
    const s = current.state, d = current.data;
    if (id === 'math.2.primes') {
      label(svg, 210, 29, s.number + ': ' + d.classification, { 'font-size': 21 });
      for (let n = 1; n <= 60; n++) {
        const x = 43 + (n - 1) % 10 * 34, y = 51 + Math.floor((n - 1) / 10) * 29, factor = d.factors.includes(n);
        svg.append(svgElement('rect', { x, y, width: 28, height: 25, rx: 3, fill: factor ? colors.teal : colors.paper,
          stroke: n === s.divisor ? colors.gold : colors.ink, 'stroke-width': n === s.divisor ? 3 : .5 }));
        label(svg, x + 14, y + 18, String(n), { 'font-size': 14, fill: factor ? colors.paper : colors.ink });
      }
      label(svg, 210, 258, 'Factors: ' + d.factors.slice(0, 6).join(', '), { 'font-size': 18 });
      if (d.factors.length > 6) label(svg, 210, 282, d.factors.slice(6).join(', '), { 'font-size': 18 });
      label(svg, 210, 329, s.number + ' ÷ ' + s.divisor + ' = ' + d.quotient + ' r ' + d.remainder, { 'font-size': 23 });
    } else if (id === 'math.2.ratio') {
      label(svg, 210, 29, 'A : B = ' + s.a + ' : ' + s.b, { 'font-size': 25 });
      const batch = (x, y) => {
        for (let i = 0; i < s.a + s.b; i++) svg.append(svgElement('rect', { x: x + i * 60 / (s.a + s.b), y,
          width: 60 / (s.a + s.b), height: 40, fill: i < s.a ? colors.blue : colors.teal, stroke: colors.paper, 'stroke-width': 1 }));
      };
      label(svg, 210, 73, 'One batch'); batch(20, 91);
      label(svg, 210, 171, s.scale + ' batches: repeat both parts');
      for (let i = 0; i < s.scale; i++) batch(20 + i * 63, 190);
      label(svg, 210, 281, d.a + ' scoops A + ' + d.b + ' scoops B');
      label(svg, 210, 329, s.a + ':' + s.b + ' = ' + d.a + ':' + d.b, { 'font-size': 25 });
    } else if (id === 'math.2.exponents') {
      label(svg, 210, 32, s.base + '^' + s.exponent + ' = ' + d.result, { 'font-size': 28 });
      d.powers.forEach((power, i) => {
        const x = 38 + i * 68;
        if (i) line(svg, x - 43, 155, x - 27, 155, { stroke: colors.teal });
        label(svg, x, 114, 'step ' + i, { 'font-size': 15 });
        svg.append(svgElement('rect', { x: x - 26, y: 130, width: 52, height: 50, rx: 8, fill: colors.paper, stroke: colors.teal, 'stroke-width': 2 }));
        label(svg, x, 162, String(power), { 'font-size': 17 });
      });
      label(svg, 210, 238, 'Each step multiplies by ' + s.base);
      label(svg, 210, 306, d.product, { 'font-size': 22 });
    } else if (id === 'math.2.data') {
      const y = value => 230 - value * 8;
      [0, 10, 20].forEach(value => {
        line(svg, 45, y(value), 385, y(value), { opacity: .2 });
        label(svg, 32, y(value) + 5, String(value), { 'font-size': 15, 'text-anchor': 'end' });
      });
      d.values.forEach((value, i) => {
        const x = 66 + i * 65;
        svg.append(svgElement('rect', { x: x - 18, y: y(value), width: 36, height: value * 8, fill: colors.teal, opacity: .65 }));
        // Keep numeric labels clear of mean/median lines at every data value.
        label(svg, x, 55, String(value), { 'font-size': 17 });
        label(svg, x, 254, 'ABCDE'[i], { 'font-size': 18 });
      });
      line(svg, 45, y(d.mean), 385, y(d.mean), { stroke: colors.blue, 'stroke-width': 3 });
      line(svg, 45, y(d.median), 385, y(d.median), { stroke: colors.coral, 'stroke-width': 3, 'stroke-dasharray': '7 5' });
      label(svg, 210, 29, 'Five observations: fixed 0–20 scale', { 'font-size': 20 });
      label(svg, 210, 290, 'Mean = ' + numberText(d.mean) + '   Median = ' + d.median);
      label(svg, 210, 331, 'Sorted: ' + d.sorted.join(', '), { 'font-size': 20 });
    } else {
      label(svg, 210, 33, 'y = ax + b', { 'font-size': 28 });
      [String(s.x), '× (' + s.a + ')', '+ (' + s.b + ')', String(d.result)].forEach((text, i) => {
        const x = 51 + i * 106;
        if (i) line(svg, x - 70, 141, x - 39, 141, { stroke: colors.ink });
        svg.append(svgElement('rect', { x: x - 37, y: 109, width: 74, height: 64, rx: 10, fill: colors.paper,
          stroke: i === 3 ? colors.teal : colors.blue, 'stroke-width': 2 }));
        label(svg, x, 149, text, { 'font-size': 20 });
        label(svg, x, 204, ['input x', 'multiply', 'add', 'output y'][i], { 'font-size': 16 });
      });
      label(svg, 210, 268, '(' + s.a + ') × (' + s.x + ') = ' + d.product);
      label(svg, 210, 323, d.product + ' + (' + s.b + ') = ' + d.result, { 'font-size': 25 });
    }
  }

  function drawLinguistics(svg, current) {
    const verbAttachment = current.state.attachment === 'verb';
    const nodes = {
      sentence: [174, 29, 'S'], subject: [35, 94, 'NP'],
      vp: [251, 94, 'VP'], verb: [105, 231, 'V'], person: [216, 231, 'NP'],
      pp: [342, 231, 'PP'], middle: verbAttachment ? [166, 162, 'VP'] : [278, 162, 'NP'],
    };
    const edges = [['sentence', 'subject'], ['sentence', 'vp'], ['vp', 'middle'],
      ...(verbAttachment ? [['middle', 'verb'], ['middle', 'person'], ['vp', 'pp']]
        : [['vp', 'verb'], ['middle', 'person'], ['middle', 'pp']])];
    edges.forEach(([from, to]) => {
      const a = nodes[from], b = nodes[to], highlighted = to === 'pp';
      line(svg, a[0], a[1] + 8, b[0], b[1] - 22, {
        stroke: highlighted ? colors.plum : colors.ink, 'stroke-width': highlighted ? 5 : 2, opacity: highlighted ? 1 : .65,
      });
    });
    Object.entries(nodes).forEach(([id, [x, y, text]]) => {
      const highlighted = id === 'pp' || id === (verbAttachment ? 'vp' : 'middle');
      if (highlighted) svg.append(svgElement('rect', { x: x - 25, y: y - 24, width: 50, height: 33,
        rx: 7, fill: colors.plum, opacity: .14 }));
      label(svg, x, y, text, { 'font-weight': highlighted ? 700 : 500 });
    });
    line(svg, 35, 104, 35, 279, { opacity: .65 });
    line(svg, 105, 241, 105, 279, { opacity: .65 });
    label(svg, 35, 310, 'I');
    label(svg, 105, 310, 'saw');
    [[216, 43, ['the', 'person']], [342, 59, ['with the', 'telescope']]].forEach(([x, halfWidth, words]) => {
      svg.append(svgElement('polygon', { points: x + ',243 ' + (x - halfWidth) + ',282 ' + (x + halfWidth) + ',282',
        fill: x === 342 ? colors.plum : colors.blue, 'fill-opacity': .07,
        stroke: x === 342 ? colors.plum : colors.ink, 'stroke-width': 1.5 }));
      label(svg, x, 309, words, { 'font-size': 20 });
    });
  }

  function drawLogic(svg, current, uid) {
    const markerId = uid + '-arrow';
    const defs = svgElement('defs');
    const marker = svgElement('marker', { id: markerId, viewBox: '0 0 10 10', refX: 9,
      refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' });
    marker.append(svgElement('path', { d: 'M 0 0 L 10 5 L 0 10 z', fill: colors.blue }));
    defs.append(marker); svg.append(defs);
    const positions = [[82, 182], [320, 78], [320, 283]];
    const paths = {
      w0: 'M 48 140 C -10 51 164 51 116 139',
      w1: 'M 132 159 L 267 101',
      w2: 'M 132 203 L 267 260',
    };
    current.data.edges.forEach(edge => svg.append(svgElement('path', { d: paths[edge.to], fill: 'none',
      stroke: colors.blue, 'stroke-width': 3, 'marker-end': 'url(#' + markerId + ')' })));
    current.data.worlds.forEach((world, index) => {
      const [x, y] = positions[index], color = world.truth ? colors.teal : colors.coral;
      if (world.current) svg.append(svgElement('circle', { cx: x, cy: y, r: 59,
        fill: 'none', stroke: colors.ink, 'stroke-width': 2 }));
      svg.append(svgElement('circle', { cx: x, cy: y, r: 52, fill: colors.paper,
        stroke: color, 'stroke-width': world.accessible ? 4 : 2,
        'stroke-dasharray': world.accessible ? 'none' : '4 4' }));
      label(svg, x, y - 8, world.id, { 'font-weight': 700, 'font-size': 24 });
      label(svg, x, y + 20, 'P ' + truthText(world.truth), { 'font-size': 19 });
    });
    label(svg, 82, 267, 'current', { 'font-size': 20 });
    label(svg, 208, 360, current.data.successors.length
      ? current.data.successors.length + ' accessible ' + (current.data.successors.length === 1 ? 'world' : 'worlds')
      : 'No outgoing arrows', { 'font-size': 20 });
  }

  function render(item, hooks = {}) {
    if (!record(item) || !record(item.props) || Object.keys(item.props).length !== 1 ||
        !own(item.props, 'scenario') || typeof item.props.scenario !== 'string' || !own(specs, item.props.scenario)) return null;
    const id = item.props.scenario, spec = specs[id], uid = 'concept-' + ++serial;
    const title = typeof item.title === 'string' && item.title ? item.title : spec.title;
    const instructionText = typeof item.instructions === 'string' && item.instructions ? item.instructions : spec.instructions;
    let current = build(id);
    const root = element('section', { class: 'card lesson-model concept-model', 'data-renderer': 'concept-lab',
      'data-scenario': id, 'aria-labelledby': uid + '-title', 'aria-describedby': uid + '-instructions' });
    const heading = element('div', { class: 'model-heading-row' });
    heading.append(element('h3', { id: uid + '-title' }, title));
    const instructions = element('p', { id: uid + '-instructions', class: 'model-instructions' }, instructionText);
    const canvas = element('div', { class: 'model-canvas concept-canvas' });
    const svg = svgElement('svg', { viewBox: id === 'mind.5.logic-advanced' ? '0 0 420 382' : '0 0 420 350',
      class: 'concept-svg', width: '100%', role: 'img', 'aria-labelledby': uid + '-figure-title',
      'aria-describedby': uid + '-figure-desc', focusable: 'false' });
    const controls = element('div', { class: 'model-controls concept-controls' });
    const readout = element('p', { class: 'model-readout', id: uid + '-readout' });
    const note = element('p', { class: 'spatial-note concept-note', id: uid + '-note' });
    const status = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    const legend = element('ul', { class: 'spatial-legend', 'aria-label': 'Model key' });
    const detail = element('div', { class: 'concept-detail' });
    const sourceRow = element('p', { class: 'spatial-note concept-sources' });
    const parameterControls = new Map(), groups = new Map();
    // Keep this real button mounted during refresh so keyboard focus survives.
    const preview = id === 'cs.3.web' ? element('div', { class: 'concept-web-preview' }) : null;
    const previewButton = preview ? element('button', { type: 'button', 'data-action': 'web-preview' }, 'Advance preview counter') : null;
    const previewValue = preview ? element('p', { 'data-web-counter': 'true' }) : null;
    if (preview) {
      previewButton.style.minHeight = '44px'; previewButton.style.padding = '12px 20px';
      previewButton.style.color = colors.ink; previewButton.style.border = '2px solid ' + colors.blue;
      previewButton.style.borderRadius = '8px'; previewButton.style.fontSize = '18px';
      previewButton.addEventListener('click', () => {
        if (current.state.enabled) current.state.count = (current.state.count + 1) % 10;
        refresh(true);
      });
      preview.append(previewButton, previewValue);
    }

    function refresh(announce) {
      current = build(id, current.state);
      parameterControls.forEach(({ input, output, control }) => {
        const value = current.state[control.key];
        if (control.type === 'toggle') {
          input.setAttribute('aria-pressed', String(value));
          input.textContent = control.label + ': ' + (id === 'cs.1.binary' ? Number(value) :
            control.key.startsWith('edge') ? (value ? 'on' : 'off') : (id.startsWith('chem.') || id.startsWith('lang.')) ? (value ? 'yes' : 'no') : truthText(value));
          input.classList.toggle('is-selected', value);
        } else {
          input.value = value;
          if (output) {
            output.textContent = value + (control.unit || '');
            input.setAttribute('aria-valuetext', output.textContent);
          }
        }
      });
      svg.replaceChildren(svgElement('title', { id: uid + '-figure-title' }, title),
        svgElement('desc', { id: uid + '-figure-desc' }, current.readout));
      if (id === 'arts.1.beat') drawBeatSubdivision(svg, current);
      else if (id === 'lang.2.etymology') drawWordHistory(svg, current);
      else if (id === 'lang.2.poetry') drawMetricalFeet(svg, current);
      else if (id === 'lang.2.novels') drawNovelKnowledge(svg, current);
      else if (id === 'lang.2.research') drawSourceOrigins(svg, current);
      else if (id === 'lang.2.speaking') drawAudienceExplanation(svg, current);
      else if (id === 'lang.2.grammar') drawClauseConstituents(svg, current);
      else if (id === 'lang.2.paragraphs') drawParagraphLinks(svg, current);
      else if (id === 'lang.0.phonics') drawSoundBlending(svg, current);
      else if (id === 'lang.1.handwriting') drawHandwritingStrokes(svg, current);
      else if (id === 'lang.0.speaking') drawConversation(svg, current);
      else if (id === 'lang.1.childrens-lit') drawReadingEvidence(svg, current);
      else if (id === 'lang.1.writing-stories') drawStoryPlanning(svg, current);
      else if (id === 'lang.1.dictionary') drawDictionaryOrder(svg, current);
      else if (id === 'lang.1.vocabulary') drawWordPrecision(svg, current);
      else if (id === 'lang.1.spelling') drawSpellingMap(svg, current);
      else if (id === 'lang.1.sentences') drawSentenceBuilder(svg, current);
      else if (id === 'lang.0.rhymes') drawRhymeMatch(svg, current);
      else if (id === 'lang.0.stories') drawStoryClues(svg, current);
      else if (id === 'earth.5.frontier') drawWavePolarization(svg, current);
      else if (id === 'earth.5.earth-systems') drawIceAlbedo(svg, current);
      else if (id === 'earth.5.cosmology') drawCosmicExpansion(svg, current);
      else if (id === 'earth.5.astrobiology') drawBiosignatureInference(svg, current);
      else if (id === 'earth.4.planetary') drawAtmosphericRetention(svg, current);
      else if (id === 'earth.4.climatology') drawCarbonTrajectory(svg, current);
      else if (id === 'earth.4.oceanatmos') drawGeostrophicBalance(svg, current);
      else if (id === 'earth.4.geophysics') drawSeismicTimes(svg, current);
      else if (id === 'earth.4.astrophysics') drawRedshiftSpectrum(svg, current);
      else if (id === 'earth.3.astronomy') drawStellarHR(svg, current);
      else if (id === 'earth.3.ecology-earth') drawSeasonalWater(svg, current);
      else if (id === 'earth.3.climate-sci') drawGreenhouseBalance(svg, current);
      else if (id === 'earth.3.space-exploration') drawRocketMassRatio(svg, current);
      else if (id === 'earth.2.geology') drawPlateMarkers(svg, current);
      else if (id === 'earth.2.oceans') drawTidalAlignment(svg, current);
      else if (id === 'earth.2.atmosphere') drawClimateReference(svg, current);
      else if (id === 'earth.2.environment') drawWasteStock(svg, current);
      else if (id === 'earth.2.planets') drawPlanetSizes(svg, current);
      else if (id === 'earth.2.stars') drawStellarFlux(svg, current);
      else if (id === 'earth.0.weather') drawWeatherComparison(svg, current);
      else if (id === 'earth.1.solar-system') drawSolarDistances(svg, current);
      else if (id === 'earth.0.land-water') drawLandWater(svg, current);
      else if (id === 'earth.1.water-cycle') drawWaterStores(svg, current);
      else if (id === 'earth.1.rocks') drawRockRoute(svg, current);
      else if (id === 'cs.4.security') drawPadReuse(svg, current);
      else if (id === 'cs.4.systems') drawPointerAccess(svg, current);
      else if (id === 'cs.5.deep-learning') drawAttentionMix(svg, current);
      else if (id === 'cs.5.distributed') drawQuorumOverlap(svg, current);
      else if (id === 'cs.5.pl-theory') drawTypedReduction(svg, current);
      else if (id === 'cs.5.frontier') drawBoundedCheck(svg, current);
      else if (id === 'cs.4.algorithms-adv') drawShortestPath(svg, current);
      else if (id === 'cs.4.ml') drawLearningErrors(svg, current);
      else if (id === 'cs.4.theory') drawSuffixMachine(svg, current);
      else if (id === 'cs.3.web') drawWebLayers(svg, current);
      else if (id === 'cs.2.internet') drawWebVisit(svg, current);
      else if (id === 'cs.4.os') drawCpuSchedule(svg, current);
      else if (id === 'cs.4.databases-adv') drawAtomicTransfer(svg, current);
      else if (id === 'cs.3.versioncontrol') drawThreeWayMerge(svg, current);
      else if (id === 'cs.3.oop') drawObjectState(svg, current);
      else if (id === 'cs.3.hardware') drawFullAdder(svg, current);
      else if (id === 'cs.2.bigo-intro') drawSearchChecks(svg, current);
      else if (id === 'cs.3.algorithms') drawMergeSort(svg, current);
      else if (id === 'cs.1.blocks') drawBlockBranch(svg, current);
      else if (id === 'cs.2.programming') drawProgramTrace(svg, current);
      else if (id === 'cs.1.parts') drawComputerParts(svg, current);
      else if (id === 'cs.3.databases') drawQueryResult(svg, current);
      else if (id === 'cs.2.data-types') drawTypedAddition(svg, current);
      else if (id === 'cs.2.debugging') drawBoundaryDebugging(svg, current);
      else if (id === 'cs.2.functions') drawFunctionCalls(svg, current);
      else if (['cs.0.sorting', 'cs.0.patterns'].includes(id)) drawEarlyComputing(svg, current, id);
      else if (id === 'chem.3.bonding') drawBondingCarriers(svg, current);
      else if (id === 'chem.4.inorganic') drawCoordinationLedger(svg, current);
      else if (id === 'chem.3.organic-intro') drawAlkaneConnections(svg, current);
      else if (['chem.2.reactions-intro', 'chem.3.reactions'].includes(id)) drawReactionAccounting(svg, current, id);
      else if (id === 'chem.2.periodic') drawPeriodicPattern(svg, current);
      else if (id === 'chem.2.acids') drawAcidityComparison(svg, current);
      else if (['chem.0.materials', 'chem.1.materials-props', 'chem.5.materials'].includes(id)) drawMaterials(svg, current, id);
      else if (id === 'chem.1.changes') drawPhysicalChemicalChange(svg, current);
      else if (id === 'chem.4.electrochem') drawConcentrationCell(svg, current);
      else if (id === 'chem.5.biochem') drawEnzymeInhibition(svg, current);
      else if (id === 'chem.5.frontier') drawGreenChemistry(svg, current);
      else if (['chem.4.analytical', 'chem.5.compchem'].includes(id)) drawChemicalInference(svg, current, id);
      else if (id === 'chem.2.mixtures') drawMixtureSeparation(svg, current);
      else if (id === 'chem.3.atomic-structure') drawAtomicInventory(svg, current);
      else if (['chem.3.gases', 'chem.3.energy', 'chem.4.physical'].includes(id)) drawChemicalConditions(svg, current, id);
      else if (id === 'chem.3.stoichiometry') drawAtomLedger(svg, current);
      else if (['chem.0.mixing', 'chem.0.water-states', 'chem.1.matter'].includes(id)) drawIntroChemistry(svg, current, id);
      else if (['bio.1.health', 'bio.3.microbiology', 'bio.5.immunology', 'bio.5.frontier'].includes(id)) drawBiologyEvidence(svg, current, id);
      else if (['bio.4.neuro', 'bio.4.physiology', 'bio.4.ethology'].includes(id)) drawNeuroPhysiologyBehaviour(svg, current, id);
      else if (['bio.4.genomics', 'bio.5.comp-bio', 'bio.5.systems-bio'].includes(id)) drawMolecularComputation(svg, current, id);
      else if (['bio.3.ecology', 'bio.3.botany', 'bio.4.biochem'].includes(id)) drawPlantPopulationEnzyme(svg, current, id);
      else if (['bio.3.evolution', 'bio.4.evo-bio'].includes(id)) drawEvolution(svg, current, id);
      else if (['bio.1.human-body', 'bio.2.digestion', 'bio.2.reproduction'].includes(id)) drawBodyReproduction(svg, current, id);
      else if (['bio.0.animals', 'bio.1.habitats'].includes(id)) drawAnimalHabitats(svg, current, id);
      else if (['bio.0.body', 'bio.0.seasons'].includes(id)) drawSensesSeasons(svg, current, id);
      else if (['bio.0.living', 'bio.2.classification', 'bio.2.ecosystems', 'bio.2.microbes'].includes(id)) drawLifeSystems(svg, current, id);
      else if (['bio.0.plants', 'bio.1.plants-parts', 'bio.2.photosynthesis', 'bio.1.food-chains'].includes(id)) drawBotany(svg, current, id);
      else if (['math.5.diffgeo', 'math.5.complex-analysis', 'math.5.logic'].includes(id)) drawFinalMath(svg, current, id);
      else if (['math.5.frontier', 'math.5.abstract', 'math.5.measure', 'math.5.functional', 'math.5.numerical'].includes(id)) drawAdvanced(svg, current, id);
      else if (['math.4.diffeq', 'math.4.discrete', 'math.4.numtheory', 'math.4.analysis', 'math.4.prob-theory'].includes(id)) drawStageFour(svg, current, id);
      else if (['math.3.euclid', 'math.4.complex', 'math.4.diff-calc', 'math.4.int-calc'].includes(id)) drawCalculusGeometry(svg, current, id);
      else if (['math.3.probability', 'math.3.statistics', 'math.3.precalc', 'math.3.polynomials'].includes(id)) drawEvidence(svg, current, id);
      else if (['math.3.trig', 'math.3.expo-logs', 'math.3.sequences'].includes(id)) drawGrowthTrig(svg, current, id);
      else if (['math.3.systems', 'math.3.quadratics'].includes(id)) drawIntersections(svg, current, id);
      else if (['math.3.linear', 'math.3.slope'].includes(id)) drawLinear(svg, current, id);
      else if (['math.2.primes', 'math.2.ratio', 'math.2.exponents', 'math.2.data', 'math.2.prealgebra'].includes(id)) drawStageTwo(svg, current, id);
      else if (id === 'math.2.decimals' || id === 'math.2.order-ops') drawDecimalOrder(svg, current, id);
      else if (id === 'math.2.percent' || id === 'math.2.coordinates') drawPercentCoordinates(svg, current, id);
      else if (['math.1.measurement', 'math.1.time', 'math.1.fractions-intro'].includes(id)) drawMeasureTimeFraction(svg, current, id);
      else if (id === 'math.1.multiplication' || id === 'math.1.division') drawGroups(svg, current, id);
      else if (id.startsWith('math.1.')) drawPlaceAndSubtract(svg, current, id);
      else if (id.startsWith('math.0.')) drawEarlyMath(svg, current, id);
      else if (id === 'cs.1.binary') drawBinary(svg, current);
      else if (id === 'hist.3.economics-intro') drawEconomics(svg, current);
      else if (id === 'lang.4.linguistics') drawLinguistics(svg, current);
      else drawLogic(svg, current, uid);
      readout.textContent = current.readout;
      if (preview) {
        previewButton.style.backgroundColor = current.data.background;
        previewValue.textContent = 'Preview counter: ' + current.data.count;
      }
      note.textContent = current.note;
      legend.replaceChildren(...current.legend.map(entry => {
        const li = element('li');
        const swatch = element('span', { class: 'spatial-swatch', 'aria-hidden': 'true' });
        swatch.style.backgroundColor = entry.color;
        li.append(swatch, document.createTextNode(entry.label)); return li;
      }));
      detail.replaceChildren();
      if (id === 'lang.4.linguistics') {
        detail.append(element('p', { class: 'concept-sentence' }, '“' + current.data.sentence + '”'),
          element('p', { class: 'concept-parse-label' }, 'Bracketed structure'),
          element('p', { class: 'concept-parse', 'aria-label': 'Bracketed constituent parse' }, current.data.parse));
      } else if (id === 'mind.5.logic-advanced') {
        const outcomes = element('div', { class: 'concept-outcomes', 'aria-label': 'Truth at w0' });
        [['P', current.data.localP, 'here'], ['□P', current.data.boxP, 'all accessible'],
          ['◇P', current.data.diamondP, 'some accessible']].forEach(([formula, truth, meaning]) => {
          const cell = element('p', { class: 'concept-outcome' });
          cell.append(element('strong', {}, formula + ' ' + truthText(truth)), element('span', {}, meaning));
          outcomes.append(cell);
        });
        detail.append(outcomes);
      }
      sourceRow.replaceChildren(document.createTextNode('Learn more: '), ...current.sources.map(source =>
        element('a', { href: source.url, target: '_blank', rel: 'noopener noreferrer' }, source.label)));
      sourceRow.hidden = current.sources.length === 0;
      if (announce) status.textContent = current.readout;
    }

    spec.controls.forEach(control => {
      let container = controls;
      if (control.group) {
        if (!groups.has(control.group)) {
          const fieldset = element('fieldset', { class: 'concept-control-group' });
          fieldset.append(element('legend', {}, control.group));
          controls.append(fieldset); groups.set(control.group, fieldset);
        }
        container = groups.get(control.group);
      }
      let input, output;
      if (control.type === 'toggle') {
        input = element('button', { type: 'button', class: 'btn small model-option concept-toggle',
          'data-parameter': control.key, 'aria-pressed': 'false' });
        input.addEventListener('click', () => {
          current.state[control.key] = !current.state[control.key]; refresh(true);
        });
        container.append(input);
      } else {
        const labelEl = element('label', { class: 'spatial-parameter concept-parameter', for: uid + '-' + control.key });
        const labelText = element('span', {}, control.label);
        if (control.options) {
          input = element('select', { id: uid + '-' + control.key, 'data-parameter': control.key });
          control.options.forEach(option => input.append(element('option', { value: option.value }, option.label)));
        } else {
          output = element('output', { for: uid + '-' + control.key });
          labelText.append(output);
          input = element('input', { id: uid + '-' + control.key, type: 'range',
            min: control.min, max: control.max, step: control.step, 'data-parameter': control.key });
        }
        input.addEventListener(control.options ? 'change' : 'input', () => {
          current.state[control.key] = control.options ? input.value : Number(input.value); refresh(true);
        });
        labelEl.append(labelText, input); container.append(labelEl);
      }
      parameterControls.set(control.key, { input, output, control });
    });
    const buttons = element('div', { class: 'model-button-row' });
    const reset = element('button', { type: 'button', class: 'btn ghost small', 'data-action': 'reset-model' }, 'Reset model');
    reset.addEventListener('click', () => { current = build(id); refresh(true); });
    buttons.append(reset);
    if (hooks && typeof hooks.speakButton === 'function') {
      heading.prepend(hooks.speakButton(() => [title, instructionText, current.readout,
        current.data.parse || '', current.note].join(' '), 'Read this activity aloud'));
    }
    canvas.append(svg);
    root.append(heading, instructions, canvas);
    if (preview) root.append(preview);
    root.append(controls, buttons, legend, detail, readout, note, sourceRow, status);
    refresh(false);
    return root;
  }

  window.PrimerConceptModels = Object.freeze({ render, build, supported,
    controls(id) { return typeof id === 'string' && own(specs, id) ? specs[id].controls : emptyControls; },
  });
}());
