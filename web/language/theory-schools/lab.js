'use strict';
const Model = {
  ITEMS: [{"name": "Formalism", "cat": "Formalism", "cols": ["How does the form of the text itself make its meaning?", "Viktor Shklovsky; the New Critics"]}, {"name": "Structuralism", "cat": "Structuralism", "cols": ["What system of signs and oppositions lies under the text?", "Ferdinand de Saussure; Claude Lévi-Strauss"]}, {"name": "Deconstruction", "cat": "Deconstruction", "cols": ["Where does the text undo the oppositions it depends on?", "Jacques Derrida"]}, {"name": "Marxist criticism", "cat": "Marxist criticism", "cols": ["How do class and economic power shape the text?", "Karl Marx; Terry Eagleton"]}, {"name": "Feminist criticism", "cat": "Feminist criticism", "cols": ["How does the text represent and construct gender?", "Simone de Beauvoir; Elaine Showalter"]}, {"name": "Psychoanalytic criticism", "cat": "Psychoanalytic criticism", "cols": ["What unconscious desires and fears does the text express?", "Sigmund Freud; Jacques Lacan"]}, {"name": "Reader-response", "cat": "Reader-response", "cols": ["What does the reader do to make the meaning?", "Wolfgang Iser; Stanley Fish"]}, {"name": "Postcolonial criticism", "cat": "Postcolonial criticism", "cols": ["How does the text carry or resist the legacy of empire?", "Edward Said"]}],
  CATEGORIES: ["Formalism", "Structuralism", "Deconstruction", "Marxist criticism", "Feminist criticism", "Psychoanalytic criticism", "Reader-response", "Postcolonial criticism"],
  QUIZ: [["How do the rhyme and the line breaks enact the poem’s tension?", "Formalism"], ["Which binary oppositions organise this myth: raw and cooked, nature and culture?", "Structuralism"], ["Where does the novel’s contrast of speech and writing collapse?", "Deconstruction"], ["Who owns the mill, and whose labour does the story leave out?", "Marxist criticism"], ["Why can the heroine act only through marriage?", "Feminist criticism"], ["What does the narrator’s recurring dream repress?", "Psychoanalytic criticism"], ["What gaps does the text leave for the reader to fill?", "Reader-response"], ["How is the colonised island described through the settler’s eyes?", "Postcolonial criticism"], ["How does the unreliable ordering of scenes create irony?", "Formalism"], ["Whose voice is missing from this account of the empire’s frontier?", "Postcolonial criticism"]],
  PROMPT: "Which school would ask this first? “{name}”",
  category: name => (Model.ITEMS.find(item => item.name === name) || {}).cat,
  inCategory: cat => Model.ITEMS.filter(item => item.cat === cat).map(item => item.name),
  // Round n asks about one quiz entry and offers up to four categories, the right one among them.
  round(n) {
    const quiz = Model.QUIZ, cats = Model.CATEGORIES, entry = quiz[(n * 7) % quiz.length];
    const size = Math.min(4, cats.length), at = cats.indexOf(entry[1]), first = (at - (n * 7 + (n >> 1)) % size + cats.length) % cats.length;
    // An entry may carry its own options, for questions whose choices come from the sentence itself.
    const options = entry[2] || Array.from({length: size}, (_, i) => cats[(first + i) % cats.length]);
    return {text: entry[0], prompt: Model.PROMPT.replace('{name}', entry[0]), options, answer: entry[1]};
  },
  check: (n, choice) => Model.round(n).answer === choice,
};
function start() {
  const show = Kit.get('show'); let n = 0, score = 0;
  show.add(new Option('Everything', ''));
  if (false) Model.CATEGORIES.forEach(cat => show.add(new Option(cat, cat)));
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

    Kit.get('result').textContent = "No single school is the right one. Try two on the same passage and compare what each brings out.";
  }
  Kit.bind(['show'], draw); ask();
}
if (typeof module === 'object') module.exports = Model; else start();
