"""Generate the twenty language activities that share one layout: reference table, optional drawing, sorting game.

Run: python tools/build_language_sorting_activities.py. It rewrites web/language/<slug>/ and adds registry entries.
"""
import json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / 'web/language'

def A(slug, node, back, title, lede, headers, items, cat_label, prompt, result, quiz=None, visual=None, game_title='Test yourself', visual_caption=''):
    return dict(slug=slug, node=node, back=back, title=title, lede=lede, headers=headers, items=items, cat_label=cat_label,
                prompt=prompt, result=result, quiz=quiz, visual=visual, game_title=game_title, visual_caption=visual_caption)

def I(name, cat, *cols, **extra):
    return dict(name=name, cat=cat, cols=list(cols), **extra)

ACTS = [
A('letter-sounds', 'lang.0.phonics', 'Letter Sounds', 'Letters and their sounds',
  'Each letter stands for a sound. Look at the letters, then choose the letter that starts each word.',
  ['Letter', 'Sound it often makes', 'Starts the word'],
  [I('s', 's', 'sss, like a snake', 'sun'), I('m', 'm', 'mmm', 'moon'), I('t', 't', 't, a quick tap', 'top'), I('p', 'p', 'p, a puff of air', 'pig'),
   I('b', 'b', 'b', 'bat'), I('f', 'f', 'fff', 'fish'), I('d', 'd', 'd', 'dog'), I('n', 'n', 'nnn', 'net'), I('h', 'h', 'h, a breath', 'hat'),
   I('l', 'l', 'lll', 'leg'), I('r', 'r', 'rrr', 'red'), I('c', 'c', 'k, as in cat', 'cup')],
  'Letter', 'Which letter starts the word “{name}”?',
  'Say the word slowly and listen to the first sound. Then find the letter that makes that sound.',
  quiz=[('sock','s'),('map','m'),('ten','t'),('pan','p'),('bed','b'),('fan','f'),('dig','d'),('nut','n'),('hen','h'),('log','l'),('rug','r'),('cat','c'),('sit','s'),('mud','m'),('tap','t'),('pot','p')]),
A('question-words', 'lang.0.speaking', 'Talking and Listening', 'Question words',
  'Good talkers ask questions and listen to the answers. Each question word asks for a different kind of answer.',
  ['Question word', 'It asks about', 'Example question'],
  [I('Who', 'Who', 'a person', 'Who is at the door?'), I('What', 'What', 'a thing or an action', 'What are you making?'), I('Where', 'Where', 'a place', 'Where is my hat?'),
   I('When', 'When', 'a time', 'When is lunch?'), I('Why', 'Why', 'a reason', 'Why is the sky dark?'), I('How', 'How', 'the way something is done', 'How do you tie a bow?')],
  'Question word', 'The answer is “{name}”. Which question word was asked?',
  'Listen to the answer. A person answers Who, a place answers Where, a time answers When, and a reason answers Why.',
  quiz=[('My grandma','Who'),('At the park','Where'),('After dinner','When'),('Because it is raining','Why'),('A red kite','What'),('By mixing blue and yellow','How'),
        ('The bus driver','Who'),('Under the bed','Where'),('On Saturday','When'),('Because I was tired','Why'),('A sandwich','What'),('By pedalling fast','How')]),
A('story-parts', 'lang.0.stories', 'Story Time', 'Beginning, middle and end',
  'Every story has a beginning, a middle and an end. The table shows what each part does. Then sort the sentences.',
  ['Part', 'What it tells you', 'Listen for'],
  [I('Beginning', 'Beginning', 'who the story is about and where they are', 'Once upon a time; One morning'),
   I('Middle', 'Middle', 'what happens, and the problem', 'But then; Suddenly'),
   I('End', 'End', 'how the problem is solved', 'At last; In the end')],
  'Part', 'Which part of the story is this? “{name}”',
  'Ask three questions after any story: who was it about, where were they, and what happened?',
  quiz=[('Once upon a time a little fox lived by a river.','Beginning'),('But then the river began to rise.','Middle'),('At last the fox was safe and warm at home.','End'),
        ('One morning Mina found a tiny door in the garden wall.','Beginning'),('Suddenly the door creaked open and a mouse ran out.','Middle'),('In the end Mina and the mouse were friends.','End'),
        ('There was once a baker who loved to sing.','Beginning'),('Then one day all the bread went missing.','Middle'),('So the baker sang, and everyone shared the bread happily ever after.','End')]),
A('childrens-classics', 'lang.1.childrens-lit', "Great Children's Books", "Classic children's books",
  'These books have been read to children for generations. The drawing places each one on a time line.',
  ['Book', 'Author', 'First published', 'What it is about'],
  [I("Alice's Adventures in Wonderland", 'Lewis Carroll', 'Lewis Carroll', '1865', 'A girl follows a rabbit into a world of nonsense.', year=1865),
   I('The Tale of Peter Rabbit', 'Beatrix Potter', 'Beatrix Potter', '1902', "A rabbit sneaks into Mr McGregor's garden.", year=1902),
   I('The Wind in the Willows', 'Kenneth Grahame', 'Kenneth Grahame', '1908', 'Mole, Rat, Badger and the reckless Mr Toad.', year=1908),
   I('Winnie-the-Pooh', 'A. A. Milne', 'A. A. Milne', '1926', 'A bear and his friends in the Hundred Acre Wood.', year=1926),
   I("Charlotte's Web", 'E. B. White', 'E. B. White', '1952', 'A spider saves a pig by writing in her web.', year=1952),
   I('The Cat in the Hat', 'Dr. Seuss', 'Dr. Seuss', '1957', 'A cat in a striped hat turns a rainy day upside down.', year=1957),
   I('Where the Wild Things Are', 'Maurice Sendak', 'Maurice Sendak', '1963', 'Max sails to an island of wild things.', year=1963),
   I('The Very Hungry Caterpillar', 'Eric Carle', 'Eric Carle', '1969', 'A caterpillar eats through the week and becomes a butterfly.', year=1969)],
  'Author', 'Who wrote “{name}”?',
  'When you finish a book, tell someone who it was about, what happened, and which part you liked best.', visual='timeline', visual_caption='Time line of first publication'),
A('letter-shapes', 'lang.1.handwriting', 'Handwriting', 'Tall, small and tail letters',
  'Letters sit on a line. Small letters fit between the base line and the middle line. Tall letters reach up. Tail letters hang below.',
  ['Letter', 'Family', 'Where it sits'],
  [I(ch, 'Tall', 'Tall', 'reaches up to the top line') for ch in 'bdfhklt'] +
  [I(ch, 'Small', 'Small', 'fits between the base line and the middle line') for ch in 'aceimnorsuvwxz'] +
  [I(ch, 'Tail', 'Tail', 'hangs below the base line') for ch in 'gjpqy'],
  'Family', 'Which family does the letter “{name}” belong to?',
  'Keep small letters the same height, make tall letters clearly taller, and let tails drop below the line.', visual='lines', visual_caption='The writing lines'),
A('read-for-meaning', 'lang.1.reading', 'Learning to Read', 'Read a sentence and understand it',
  'Reading is more than saying the words. After each sentence, ask who it is about, what they did and where.',
  ['Sentence', 'Who', 'Did what', 'Where'],
  [I('The cat sat on the mat.', 'Who', 'the cat', 'sat', 'on the mat'), I('Ben ran to the shop.', 'Who', 'Ben', 'ran', 'to the shop'),
   I('A frog hid under a leaf.', 'Who', 'a frog', 'hid', 'under a leaf'), I('Mum reads in the garden.', 'Who', 'Mum', 'reads', 'in the garden'),
   I('The dog swam in the pond.', 'Who', 'the dog', 'swam', 'in the pond')],
  'Answer', '{name}',
  'Read the sentence, then answer from the sentence itself. If you are not sure, read it again.',
  quiz=[('“The cat sat on the mat.” Who sat?', 'the cat', ['the cat', 'sat', 'on the mat']), ('“Ben ran to the shop.” Who ran?', 'Ben', ['Ben', 'ran', 'to the shop']), ('“A frog hid under a leaf.” Who hid?', 'a frog', ['a frog', 'hid', 'under a leaf']), ('“Mum reads in the garden.” Who reads?', 'Mum', ['Mum', 'reads', 'in the garden']), ('“The dog swam in the pond.” Who swam?', 'the dog', ['the dog', 'swam', 'in the pond']), ('“The cat sat on the mat.” Where did the cat sit?', 'on the mat', ['the cat', 'sat', 'on the mat']), ('“Ben ran to the shop.” Where did Ben run?', 'to the shop', ['Ben', 'ran', 'to the shop']), ('“A frog hid under a leaf.” Where did the frog hide?', 'under a leaf', ['a frog', 'hid', 'under a leaf']), ('“Mum reads in the garden.” Where does Mum read?', 'in the garden', ['Mum', 'reads', 'in the garden']), ('“The dog swam in the pond.” Where did the dog swim?', 'in the pond', ['the dog', 'swam', 'in the pond']), ('“The cat sat on the mat.” What did the cat do?', 'sat', ['the cat', 'sat', 'on the mat']), ('“Ben ran to the shop.” What did Ben do?', 'ran', ['Ben', 'ran', 'to the shop']), ('“A frog hid under a leaf.” What did the frog do?', 'hid', ['a frog', 'hid', 'under a leaf']), ('“Mum reads in the garden.” What does Mum do?', 'reads', ['Mum', 'reads', 'in the garden']), ('“The dog swam in the pond.” What did the dog do?', 'swam', ['the dog', 'swam', 'in the pond'])],
  ),
A('word-hoard', 'lang.1.vocabulary', 'Word Collecting', 'Words, partners and opposites',
  'Collect a word with its meaning, a word that means nearly the same, and its opposite.',
  ['Word', 'Meaning', 'Nearly the same', 'Opposite'],
  [I('enormous', 'tiny', 'very big', 'huge', 'tiny'), I('ancient', 'modern', 'very old', 'old', 'modern'), I('brave', 'fearful', 'ready to face danger', 'bold', 'fearful'),
   I('swift', 'slow', 'moving fast', 'quick', 'slow'), I('gloomy', 'cheerful', 'dark or sad', 'dismal', 'cheerful'), I('fragile', 'sturdy', 'easily broken', 'delicate', 'sturdy'),
   I('generous', 'selfish', 'glad to give', 'giving', 'selfish'), I('silent', 'noisy', 'making no sound', 'quiet', 'noisy'), I('expand', 'shrink', 'to grow larger', 'grow', 'shrink'),
   I('scarce', 'plentiful', 'hard to find', 'rare', 'plentiful')],
  'Opposite', 'Which word is the opposite of “{name}”?',
  'A new word sticks when you use it. Say it in a sentence of your own today.'),
A('story-mountain', 'lang.1.writing-stories', 'Writing Your Own Stories', 'The story mountain',
  'A story climbs to a problem and comes down to an ending. The drawing shows the five steps in order.',
  ['Step', 'What to write', 'Example'],
  [I('Opening', 'Opening', 'who and where', 'Tia lived beside a lighthouse.', stage=0), I('Build-up', 'Build-up', 'something starts to happen', 'One night the lamp flickered.', stage=1),
   I('Problem', 'Problem', 'the biggest trouble', 'The lamp went out as a ship drew near.', stage=2), I('Resolution', 'Resolution', 'how the trouble is solved', 'Tia waved a lantern from the rocks.', stage=3),
   I('Ending', 'Ending', 'how things are afterwards', 'The sailors named the lantern Tia’s Star.', stage=4)],
  'Step', 'Which step of the story is this? “{name}”',
  'Plan the five steps in a few words each before you write. The problem is the top of the mountain.',
  quiz=[('Sam and his dog Pip lived on a windy hill.','Opening'),('One day Pip began to dig by the old oak.','Build-up'),('The hole fell in and Pip was stuck.','Problem'),('Sam lowered a rope and pulled Pip out.','Resolution'),('After that, Pip only dug in the sandpit.','Ending'),
        ('Long ago a girl called Noor kept bees.','Opening'),('That spring the bees grew restless.','Build-up'),('A storm knocked over every hive.','Problem'),('Noor built the hives again, stronger than before.','Resolution'),('The honey that year was the sweetest of all.','Ending')],
  visual='arc', visual_caption='The story mountain'),
A('myth-traditions', 'lang.2.mythology', 'Myths and Legends', 'Gods, tricksters and where their stories come from',
  'Peoples all over the world told stories to explain the sky, the sea and human nature. The drawing places each tradition by longitude and latitude.',
  ['Figure', 'Tradition', 'Known for'],
  [I('Zeus', 'Greek', 'Greek', 'king of the gods; sky and thunder', lon=22, lat=39), I('Athena', 'Greek', 'Greek', 'wisdom and craft'), I('Poseidon', 'Greek', 'Greek', 'the sea and earthquakes'),
   I('Odin', 'Norse', 'Norse', 'chief of the gods; wisdom and poetry', lon=15, lat=62), I('Thor', 'Norse', 'Norse', 'thunder; wields the hammer Mjölnir'), I('Loki', 'Norse', 'Norse', 'trickery and shape-changing'),
   I('Ra', 'Egyptian', 'Egyptian', 'the sun', lon=31, lat=27), I('Isis', 'Egyptian', 'Egyptian', 'magic and protection'), I('Anubis', 'Egyptian', 'Egyptian', 'embalming and the dead'),
   I('Anansi', 'Akan (West African)', 'Akan (West African)', 'the spider trickster who owns all stories', lon=-1, lat=8),
   I('Quetzalcoatl', 'Aztec', 'Aztec', 'the feathered serpent; wind and learning', lon=-99, lat=19),
   I('Amaterasu', 'Japanese', 'Japanese', 'the sun goddess', lon=138, lat=36)],
  'Tradition', 'Which tradition tells of {name}?',
  'Myths from far-apart places often share shapes: a sun deity, a thunder god, a trickster. Compare two and note what differs.', visual='map', visual_caption='Where each tradition comes from'),
A('novel-elements', 'lang.2.novels', 'Reading Novels', 'Character, setting, plot, theme and point of view',
  'A novel is built from a few elements. The drawing shows the usual shape of a plot.',
  ['Element', 'Question it answers', 'Look for'],
  [I('Character', 'Character', 'Who is the story about?', 'what people want, say and do', stage=0), I('Setting', 'Setting', 'Where and when does it happen?', 'place, time, weather, mood', stage=1),
   I('Plot', 'Plot', 'What happens, and why?', 'events linked by cause and effect', stage=2), I('Theme', 'Theme', 'What is the story really about?', 'an idea that keeps returning', stage=3),
   I('Point of view', 'Point of view', 'Who is telling the story?', '“I” or “she”; what the teller can know', stage=4)],
  'Element', 'Which element does this note describe? “{name}”',
  'While you read a long story, keep a short note for each element. Update it every few chapters.',
  quiz=[('The story takes place on a frozen island in winter.','Setting'),('Mara is stubborn but kind, and she hates being told what to do.','Character'),('Because the bridge collapses, the twins must cross the marsh.','Plot'),
        ('Again and again the book returns to the cost of telling the truth.','Theme'),('The narrator says “I” and never knows what the others are thinking.','Point of view'),('Most of the chapters happen in one crowded kitchen in 1920.','Setting'),
        ('The old sailor wants, above all, to see his daughter again.','Character'),('The theft in chapter two leads to the chase in chapter three.','Plot'),('Friendship across differences is the idea under every chapter.','Theme'),('The teller can see into every character’s mind.','Point of view')],
  visual='plot', visual_caption='The usual shape of a plot'),
A('source-types', 'lang.2.research', 'Finding Things Out', 'Primary, secondary and tertiary sources',
  'To find something out, know what kind of source you are holding and check it before you trust it.',
  ['Source', 'Kind', 'Why'],
  [I('a diary', 'Primary', 'Primary', 'written by someone who was there'), I('a letter', 'Primary', 'Primary', 'written at the time by a person involved'), I('a photograph', 'Primary', 'Primary', 'made at the event itself'),
   I('an interview with a witness', 'Primary', 'Primary', 'first-hand account'), I('a biography', 'Secondary', 'Secondary', 'written later, using primary sources'), I('a history book', 'Secondary', 'Secondary', 'explains and interprets the evidence'),
   I('a documentary film', 'Secondary', 'Secondary', 'tells the story from gathered evidence'), I('an encyclopedia', 'Tertiary', 'Tertiary', 'sums up what secondary sources say'), I('a dictionary', 'Tertiary', 'Tertiary', 'a reference list drawn from other works'),
   I('an almanac', 'Tertiary', 'Tertiary', 'collected facts and figures')],
  'Kind', 'What kind of source is {name}?',
  'Checking a source, in order: 1. Who made it? 2. When? 3. What evidence does it give? 4. Does a second, independent source agree?'),
A('argument-parts', 'lang.3.essays', 'The Essay', 'The parts of an argument',
  'An essay argues. Each sentence does a job: it claims, gives evidence, reasons, raises an objection, or answers it.',
  ['Part', 'Its job', 'Signal words'],
  [I('Claim', 'Claim', 'states what you want the reader to accept', 'should; is; must'), I('Evidence', 'Evidence', 'gives facts, examples or quotations', 'for example; a study found'),
   I('Reasoning', 'Reasoning', 'explains why the evidence supports the claim', 'this shows; because; therefore'), I('Counterargument', 'Counterargument', 'states the strongest objection fairly', 'some argue; it may be objected'),
   I('Rebuttal', 'Rebuttal', 'answers the objection', 'however; yet; even so')],
  'Part', 'Which part of an argument is this? “{name}”',
  'A fair essay states the best objection to itself and answers it. That is what makes an argument honest.',
  quiz=[('Schools should start later in the morning.','Claim'),('In one district, attendance rose after the start time moved to nine.','Evidence'),('This shows that a later start removes a barrier to coming to school.','Reasoning'),
        ('Some argue that a later start only moves bedtimes later.','Counterargument'),('However, students in the district slept longer, not later.','Rebuttal'),('Cities must plant more street trees.','Claim'),
        ('For example, shaded streets were several degrees cooler in the survey.','Evidence'),('Because cooler streets need less air conditioning, trees save energy.','Reasoning'),('It may be objected that trees are costly to maintain.','Counterargument'),('Yet the saving in energy outweighs the cost of care.','Rebuttal')]),
A('literary-devices', 'lang.3.literature', 'Literature', 'Literary devices in famous lines',
  'Close reading starts with noticing how a line works. Each device below does something different to meaning.',
  ['Device', 'What it does', 'Example'],
  [I('Simile', 'Simile', 'compares using “like” or “as”', '“O my Luve is like a red, red rose” — Robert Burns'),
   I('Metaphor', 'Metaphor', 'says one thing is another', '“All the world’s a stage” — William Shakespeare'),
   I('Personification', 'Personification', 'gives human action to something not human', '“Because I could not stop for Death – He kindly stopped for me” — Emily Dickinson'),
   I('Alliteration', 'Alliteration', 'repeats a starting sound', '“The fair breeze blew, the white foam flew” — Samuel Taylor Coleridge'),
   I('Hyperbole', 'Hyperbole', 'exaggerates for effect', '“I’ve told you a million times.”'),
   I('Irony', 'Irony', 'says the opposite of what is meant, or shows the opposite of what is expected', 'A fire station burns down.')],
  'Device', 'Which device is at work? “{name}”',
  'Naming the device is the start. Then ask what it makes you see or feel that plain words would not.',
  quiz=[('Her smile was as bright as the morning.','Simile'),('Time is a thief.','Metaphor'),('The wind whispered through the pines.','Personification'),('Peter Piper picked a peck of pickled peppers.','Alliteration'),
        ('This bag weighs a ton.','Hyperbole'),('“What lovely weather,” she said, as the hail broke the window.','Irony'),('He ran like the wind.','Simile'),('The classroom was a zoo.','Metaphor'),
        ('The old house groaned and sighed.','Personification'),('Silver ships sailed slowly south.','Alliteration'),('I am so hungry I could eat a horse.','Hyperbole'),('The lifeguard had to be rescued from the paddling pool.','Irony')]),
A('shakespeare-plays', 'lang.3.shakespeare', 'Shakespeare', 'Comedies, histories and tragedies',
  'The First Folio of 1623 sorted Shakespeare’s plays into comedies, histories and tragedies. Dates are approximate; scholars date the plays from records and style.',
  ['Play', 'Kind', 'Written about', 'In one line'],
  [I('Richard III', 'History', 'History', '1592', 'A ruthless duke schemes his way to the crown.', year=1592),
   I('Romeo and Juliet', 'Tragedy', 'Tragedy', '1595', 'Two young lovers from feuding families.', year=1595),
   I("A Midsummer Night's Dream", 'Comedy', 'Comedy', '1595', 'Lovers and fairies in a wood near Athens.', year=1595),
   I('Much Ado About Nothing', 'Comedy', 'Comedy', '1598', 'Beatrice and Benedick are tricked into love.', year=1598),
   I('Henry V', 'History', 'History', '1599', 'A young king leads his army at Agincourt.', year=1599),
   I('Julius Caesar', 'Tragedy', 'Tragedy', '1599', 'Brutus joins the plot against Caesar.', year=1599),
   I('Hamlet', 'Tragedy', 'Tragedy', '1600', 'A prince is told to avenge his father.', year=1600),
   I('Twelfth Night', 'Comedy', 'Comedy', '1601', 'Shipwrecked Viola disguises herself as a man.', year=1601),
   I('Othello', 'Tragedy', 'Tragedy', '1604', 'Iago poisons a general’s trust in his wife.', year=1604),
   I('King Lear', 'Tragedy', 'Tragedy', '1605', 'An old king divides his kingdom.', year=1605),
   I('Macbeth', 'Tragedy', 'Tragedy', '1606', 'A prophecy drives a Scottish lord to murder.', year=1606)],
  'Kind', 'Which kind of play is “{name}”?',
  'A comedy ends in marriage or reunion, a tragedy in the death of its hero, and a history follows an English king.', visual='timeline', visual_caption='Time line of when each play was written (approximate)'),
A('world-classics', 'lang.3.world-lit', 'World Literature', 'Great works and where they come from',
  'Every literate culture has its classics. The drawing places each work by longitude and latitude.',
  ['Work', 'Region', 'Date', 'Author or source'],
  [I('Epic of Gilgamesh', 'Mesopotamia', 'Mesopotamia', 'about 2100–1200 BCE', 'Sumerian and Akkadian tablets', lon=44, lat=33),
   I('Mahabharata', 'India', 'India', 'about 400 BCE–400 CE', 'attributed to Vyasa', lon=78, lat=24),
   I('Shahnameh', 'Persia', 'Persia', 'about 1010', 'Ferdowsi', lon=53, lat=32, below=True),
   I('The Tale of Genji', 'Japan', 'Japan', 'about 1010', 'Murasaki Shikibu', lon=136, lat=35),
   I('Journey to the West', 'China', 'China', '16th century', 'attributed to Wu Cheng’en', lon=110, lat=34, below=True),
   I('Popol Vuh', 'Maya (Guatemala)', 'Maya (Guatemala)', 'written down in the 16th century', 'K’iche’ Maya tradition', lon=-91, lat=15),
   I('Don Quixote', 'Spain', 'Spain', '1605 and 1615', 'Miguel de Cervantes', lon=-4, lat=40),
   I('Things Fall Apart', 'Nigeria', 'Nigeria', '1958', 'Chinua Achebe', lon=8, lat=8),
   I('One Hundred Years of Solitude', 'Colombia', 'Colombia', '1967', 'Gabriel García Márquez', lon=-74, lat=5)],
  'Region', 'Where does “{name}” come from?',
  'Read one work from a tradition that is new to you, and note one thing it assumes that your own tradition does not.', visual='map', visual_caption='Where each work comes from'),
A('ancient-canon', 'lang.4.classics', 'The Ancient Canon', 'The Greek and Roman canon in time',
  'Greek epic and drama, then Latin epic. Later Western literature keeps answering these works. Early dates are approximate.',
  ['Work', 'Author', 'Language', 'Date'],
  [I('Iliad', 'Homer', 'Homer', 'Greek', 'about 8th century BCE', year=-750), I('Odyssey', 'Homer', 'Homer', 'Greek', 'about 8th century BCE', year=-725),
   I('Theogony', 'Hesiod', 'Hesiod', 'Greek', 'about 700 BCE', year=-700), I('Oresteia', 'Aeschylus', 'Aeschylus', 'Greek', '458 BCE', year=-458),
   I('Medea', 'Euripides', 'Euripides', 'Greek', '431 BCE', year=-431), I('Oedipus the King', 'Sophocles', 'Sophocles', 'Greek', 'about 429 BCE', year=-429),
   I('Aeneid', 'Virgil', 'Virgil', 'Latin', '29–19 BCE', year=-19), I('Metamorphoses', 'Ovid', 'Ovid', 'Latin', 'about 8 CE', year=8)],
  'Author', 'Who composed the “{name}”?',
  'Virgil wrote the Aeneid in answer to Homer: its first half echoes the Odyssey and its second half the Iliad.', visual='timeline', visual_caption='Time line (years BCE are negative)'),
A('poetic-forms', 'lang.4.comp-lit', 'Comparative Literature', 'Poetic forms across traditions',
  'Comparing traditions starts with form. Each form below grew in one tradition and has since travelled.',
  ['Form', 'Tradition of origin', 'Shape'],
  [I('Sonnet', 'Italian', 'Italian', '14 lines; a turn of thought part-way through'), I('Haiku', 'Japanese', 'Japanese', '17 sound units in a 5–7–5 pattern; a seasonal word'),
   I('Tanka', 'Japanese', 'Japanese', '31 sound units in a 5–7–5–7–7 pattern'), I('Ghazal', 'Arabic and Persian', 'Arabic and Persian', 'self-contained couplets sharing a rhyme and refrain'),
   I('Villanelle', 'French', 'French', '19 lines; two refrains that return in turn'), I('Terza rima', 'Italian', 'Italian', 'three-line stanzas chained by rhyme: aba bcb cdc'),
   I('Alliterative verse', 'Old English and Germanic', 'Old English and Germanic', 'two half-lines bound by repeated starting sounds'), I('Rubai', 'Arabic and Persian', 'Arabic and Persian', 'a four-line stanza, usually rhymed aaba')],
  'Tradition', 'In which tradition did the {name} arise?',
  'When a form crosses languages it changes. The English sonnet rhymes differently from the Italian, and English haiku count syllables where Japanese counts shorter sound units.'),
A('theory-schools', 'lang.4.lit-theory', 'Literary Theory', 'Schools of literary theory',
  'Each school asks a different question of the same text. Knowing the question tells you what a reading will notice and what it will miss.',
  ['School', 'Its central question', 'Associated with'],
  [I('Formalism', 'Formalism', 'How does the form of the text itself make its meaning?', 'Viktor Shklovsky; the New Critics'),
   I('Structuralism', 'Structuralism', 'What system of signs and oppositions lies under the text?', 'Ferdinand de Saussure; Claude Lévi-Strauss'),
   I('Deconstruction', 'Deconstruction', 'Where does the text undo the oppositions it depends on?', 'Jacques Derrida'),
   I('Marxist criticism', 'Marxist criticism', 'How do class and economic power shape the text?', 'Karl Marx; Terry Eagleton'),
   I('Feminist criticism', 'Feminist criticism', 'How does the text represent and construct gender?', 'Simone de Beauvoir; Elaine Showalter'),
   I('Psychoanalytic criticism', 'Psychoanalytic criticism', 'What unconscious desires and fears does the text express?', 'Sigmund Freud; Jacques Lacan'),
   I('Reader-response', 'Reader-response', 'What does the reader do to make the meaning?', 'Wolfgang Iser; Stanley Fish'),
   I('Postcolonial criticism', 'Postcolonial criticism', 'How does the text carry or resist the legacy of empire?', 'Edward Said')],
  'School', 'Which school would ask this first? “{name}”',
  'No single school is the right one. Try two on the same passage and compare what each brings out.',
  quiz=[('How do the rhyme and the line breaks enact the poem’s tension?','Formalism'),('Which binary oppositions organise this myth: raw and cooked, nature and culture?','Structuralism'),
        ('Where does the novel’s contrast of speech and writing collapse?','Deconstruction'),('Who owns the mill, and whose labour does the story leave out?','Marxist criticism'),
        ('Why can the heroine act only through marriage?','Feminist criticism'),('What does the narrator’s recurring dream repress?','Psychoanalytic criticism'),
        ('What gaps does the text leave for the reader to fill?','Reader-response'),('How is the colonised island described through the settler’s eyes?','Postcolonial criticism'),
        ('How does the unreliable ordering of scenes create irony?','Formalism'),('Whose voice is missing from this account of the empire’s frontier?','Postcolonial criticism')]),
A('garden-paths', 'lang.5.psycholing', 'Psycholinguistics', 'Garden-path sentences',
  'Readers build structure word by word. A garden-path sentence leads the parser to a first analysis that a later word forces it to abandon. That reanalysis is measurable as longer reading time.',
  ['Sentence', 'First analysis', 'What it really is'],
  [I('The old man the boats.', 'man', '“old man” read as adjective and noun', '“the old” is the subject; “man” is the verb'),
   I('The horse raced past the barn fell.', 'fell', '“raced” read as the main verb', '“raced past the barn” is a reduced relative clause; “fell” is the main verb'),
   I('The complex houses married and single soldiers.', 'houses', '“complex houses” read as adjective and noun', '“the complex” is the subject; “houses” is the verb'),
   I('Fat people eat accumulates.', 'accumulates', '“fat people” read as adjective and noun', '“fat (that) people eat” is the subject; “accumulates” is the verb'),
   I('The cotton clothing is made of grows in Mississippi.', 'grows', '“cotton clothing” read as one noun phrase', '“the cotton (that) clothing is made of” is the subject'),
   I('While the man hunted the deer ran into the woods.', 'ran', '“the deer” read as the object of “hunted”', '“the deer” is the subject of “ran”')],
  'Word', 'At which word must the reader rethink “{name}”?',
  'The parser commits early instead of waiting. Minimal attachment and late closure are two proposed principles for which analysis it tries first.',
  quiz=[('The old man the boats.', 'man', ['old', 'man', 'the', 'boats']), ('The horse raced past the barn fell.', 'fell', ['horse', 'raced', 'barn', 'fell']), ('The complex houses married and single soldiers.', 'houses', ['complex', 'houses', 'married', 'soldiers']), ('Fat people eat accumulates.', 'accumulates', ['Fat', 'people', 'eat', 'accumulates']), ('The cotton clothing is made of grows in Mississippi.', 'grows', ['cotton', 'clothing', 'made', 'grows']), ('While the man hunted the deer ran into the woods.', 'ran', ['hunted', 'deer', 'ran', 'woods'])]),
A('registers', 'lang.5.socioling', 'Sociolinguistics', 'Register: the same message in five styles',
  'Speakers shift style with the situation. Martin Joos described five registers of English, from fixed ritual wording to private talk.',
  ['Register', 'Where it is used', 'Marks'],
  [I('Frozen', 'Frozen', 'ritual, law, oaths', 'fixed wording that does not change'), I('Formal', 'Formal', 'lectures, official letters', 'full sentences; no interruption; careful word choice'),
   I('Consultative', 'Consultative', 'doctor and patient; teacher and student', 'two-way, polite, background information supplied'),
   I('Casual', 'Casual', 'friends', 'slang, contractions, shared background assumed'), I('Intimate', 'Intimate', 'family and partners', 'private words, few words, tone carries the meaning')],
  'Register', 'Which register is this? “{name}”',
  'No register is better than another. Skill lies in choosing the one the situation calls for, and noticing who is expected to shift.',
  quiz=[('I do solemnly swear to tell the truth, the whole truth, and nothing but the truth.','Frozen'),('The committee regrets to inform you that your application was unsuccessful.','Formal'),
        ('How long have you had the cough? Does it get worse at night?','Consultative'),('You coming tonight or what?','Casual'),('Usual, love?','Intimate'),
        ('We the people, in order to form a more perfect union …','Frozen'),('This paper examines three causes of the decline.','Formal'),('Could you show me which step you found difficult?','Consultative'),
        ('Nah, that film was rubbish.','Casual'),('Mm. You too.','Intimate')]),
]

HTML = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s · Primer</title>
<link rel="stylesheet" href="/app/activities/kit.css">
<script defer src="/app/activities/kit.js"></script>
<script defer src="lab.js"></script>
</head>
<body><main>
<a href="/app/#/node/%(node)s">Return to %(back)s</a>
<h1>%(title)s</h1>
<p class="lede">%(lede)s</p>
<label for="show">Show</label><select id="show"></select>
%(figure)s<table><caption>%(caption)s</caption><thead><tr>%(heads)s</tr></thead><tbody id="rows"></tbody></table>
<h2>%(game_title)s</h2>
<p id="prompt"></p>
<div id="choices" class="choices"></div>
<p id="feedback" role="status"></p>
<p id="result" role="status"></p>
</main></body></html>
'''

JS = r'''%(strict)s
const Model = {
  ITEMS: %(items)s,
  CATEGORIES: %(cats)s,
  QUIZ: %(quiz)s,
  PROMPT: %(prompt)s,
  category: name => (Model.ITEMS.find(item => item.name === name) || {}).cat,
  inCategory: cat => Model.ITEMS.filter(item => item.cat === cat).map(item => item.name),
  // Round n asks about one quiz entry and offers up to four categories, the right one among them.
  round(n) {
    const quiz = Model.QUIZ, cats = Model.CATEGORIES, entry = quiz[(n * %(step)d) %% quiz.length];
    const size = Math.min(4, cats.length), at = cats.indexOf(entry[1]), first = (at - (n * 7 + (n >> 1)) %% size + cats.length) %% cats.length;
    // An entry may carry its own options, for questions whose choices come from the sentence itself.
    const options = entry[2] || Array.from({length: size}, (_, i) => cats[(first + i) %% cats.length]);
    return {text: entry[0], prompt: Model.PROMPT.replace('{name}', entry[0]), options, answer: entry[1]};
  },
  check: (n, choice) => Model.round(n).answer === choice,
};
function start() {
  const show = Kit.get('show'); let n = 0, score = 0;
  show.add(new Option('Everything', ''));
  if (%(filter)s) Model.CATEGORIES.forEach(cat => show.add(new Option(cat, cat)));
  function ask() {
    const round = Model.round(n);
    Kit.get('prompt').textContent = round.prompt;
    Kit.get('choices').replaceChildren(...round.options.map(option => {
      const button = document.createElement('button'); button.textContent = option;
      button.addEventListener('click', () => {
        const right = option === round.answer; if (right) score++;
        Kit.get('feedback').textContent = (right ? 'Yes. ' : 'Not quite. ') + 'The answer is ' + round.answer + '. Score ' + score + ' of ' + (n + 1) + '.';
        n++; ask();
      });
      return button;
    }));
  }
  function draw() {
    const shown = Model.ITEMS.filter(item => !show.value || item.cat === show.value);
    Kit.rows(Kit.get('rows'), shown.map(item => [item.name, ...item.cols]));
%(draw)s
    Kit.get('result').textContent = %(result)s;
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();
'''

DRAW = {
 None: '',
 'timeline': r'''    const years = Model.ITEMS.map(item => item.year), lo = Math.min(...years), hi = Math.max(...years), pad = Math.max(2, (hi - lo) * 0.08), count = Model.ITEMS.length;
    const p = Kit.plot(Kit.get('graph'), {x: [lo - pad, hi + pad], y: [-0.6, count + 1], grid: false});
    p.line(lo - pad, 0, hi + pad, 0, '#172533', 1.5);
    for (const year of Kit.ticks(lo - pad, hi + pad)) { p.line(year, 0, year, count + 0.6, '#d8dfe4', 1); p.text(String(year), year, 0, '#172533', -14, 20); }
    p.text('Year', hi + pad, 0, '#172533', -34, 40);
    Model.ITEMS.forEach((item, i) => {
      const on = shown.includes(item), y = count - i, left = item.year > (lo + hi) / 2;
      p.point(item.year, y, on ? '#963d18' : '#9aa6ae', 6, !on);
      p.text(item.name, item.year, y, on ? '#172533' : '#7a8790', left ? -10 - p.ctx.measureText(item.name).width : 10, 5);
    });''',
 'map': r'''    const p = Kit.plot(Kit.get('graph'), {x: [-130, 170], y: [-20, 75], xlabel: 'Longitude (°E)', ylabel: 'Latitude (°N)', grid: true});
    Model.ITEMS.filter(item => item.lon !== undefined).forEach(item => {
      const on = shown.includes(item), below = item.below === true;
      p.point(item.lon, item.lat, on ? '#963d18' : '#9aa6ae', 7, !on);
      p.text(item.cat, item.lon, item.lat, on ? '#172533' : '#7a8790', below ? -12 : 10, below ? 22 : -8);
    });''',
 'arc': r'''    const heights = [1, 2.2, 4, 2.2, 1];
    const p = Kit.plot(Kit.get('graph'), {x: [-0.6, 4.9], y: [0, 5], grid: false});
    for (let i = 0; i < 4; i++) p.line(i, heights[i], i + 1, heights[i + 1], '#215783', 3);
    Model.ITEMS.forEach(item => { const on = shown.includes(item); p.point(item.stage, heights[item.stage], on ? '#963d18' : '#9aa6ae', 7, !on); p.text((item.stage + 1) + '. ' + item.name, item.stage, heights[item.stage], '#172533', -30, -14); });''',
 'plot': r'''    const stages = ['Opening', 'Rising action', 'Climax', 'Falling action', 'Resolution'], heights = [1, 2.4, 4, 2.4, 1.3];
    const p = Kit.plot(Kit.get('graph'), {x: [-0.6, 4.9], y: [0, 5], grid: false});
    for (let i = 0; i < 4; i++) p.line(i, heights[i], i + 1, heights[i + 1], '#215783', 3);
    stages.forEach((stage, i) => { p.point(i, heights[i], '#963d18', 6); p.text(stage, i, heights[i], '#172533', -34, -14); });''',
 'lines': r'''    const p = Kit.plot(Kit.get('graph'), {x: [0, 10], y: [-1.6, 2.6], grid: false});
    p.line(0, 2, 10, 2, '#9aa6ae', 1.5, [6, 6]); p.line(0, 1, 10, 1, '#9aa6ae', 1.5, [6, 6]); p.line(0, 0, 10, 0, '#172533', 2.5); p.line(0, -1, 10, -1, '#9aa6ae', 1.5, [6, 6]);
    p.text('top line', 8.2, 2, '#4a5560', 0, -6); p.text('middle line', 8.2, 1, '#4a5560', 0, -6); p.text('base line', 8.2, 0, '#172533', 0, -6); p.text('tail line', 8.2, -1, '#4a5560', 0, -6);
    const boxes = {Tall: [0, 2], Small: [0, 1], Tail: [-1, 1]}, sample = {Tall: 'h', Small: 'a', Tail: 'g'};
    Object.keys(boxes).forEach((family, i) => { const [from, to] = boxes[family], x = 1 + i * 2.4, on = !show.value || show.value === family, colour = on ? '#215783' : '#c3ccd2';
      p.line(x, from, x, to, colour, 14); p.text(family + ' (' + sample[family] + ')', x, 2, on ? '#172533' : '#7a8790', -22, -22); });''',
}

def coprime_step(n):
    return next(s for s in (7, 5, 3, 11, 13, 1) if math.gcd(s, n) == 1)

def build():
    out = []
    for a in ACTS:
        cats = []
        for it in a['items']:
            if it['cat'] not in cats: cats.append(it['cat'])
        quiz = a['quiz'] or [(it['name'], it['cat']) for it in a['items']]
        for c in [q[1] for q in quiz]:
            if c not in cats: cats.append(c)
        table_cats = {it['cat'] for it in a['items']}
        filt = len(table_cats) > 1 and len(table_cats) < len(a['items']) or a['visual'] in ('arc', 'lines')
        d = ROOT / a['slug']; d.mkdir(parents=True, exist_ok=True)
        fig = ''
        if a['visual']:
            fig = '<figure>\n<canvas id="graph" width="760" height="%d" role="img" aria-label="%s. The table below gives the same information."></canvas>\n<figcaption>%s</figcaption>\n</figure>\n' % (
                {'timeline': 440, 'map': 420, 'arc': 380, 'plot': 380, 'lines': 320}[a['visual']], a['visual_caption'], a['visual_caption'] + ('. Points are placed by longitude and latitude; no coastlines are drawn.' if a['visual'] == 'map' else '.'))
        (d / 'index.html').write_text(HTML % dict(title=a['title'], node=a['node'], back=a['back'], lede=a['lede'], figure=fig, caption=a['headers'][0] + ' table',
            heads=''.join('<th scope="col">%s</th>' % h for h in a['headers']), game_title=a['game_title']))
        (d / 'lab.js').write_text(JS % dict(strict="'use strict';", items=json.dumps(a['items'], ensure_ascii=False), cats=json.dumps(cats, ensure_ascii=False),
            quiz=json.dumps(quiz, ensure_ascii=False), prompt=json.dumps(a['prompt'], ensure_ascii=False), step=coprime_step(len(quiz)),
            filter='true' if filt else 'false', draw=DRAW[a['visual']], result=json.dumps(a['result'], ensure_ascii=False)))
        for it in a['items']:
            assert len(it['cols']) == len(a['headers']) - 1, (a['slug'], it['name'])
        out.append((a['node'], a['slug'], a['title']))
    return out

if __name__ == '__main__':
    made = build()
    reg_path = ROOT.parent / 'activities/registry.json'; reg = json.loads(reg_path.read_text())
    for node, slug, title in made:
        entry = {'href': '/app/language/%s/index.html' % slug, 'label': title}
        links = reg.setdefault(node, [])
        if entry not in links: links.append(entry)
    reg_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + '\n')
    print(len(made), 'activities')
