'use strict';
const Model = {
  START: '<s>', END: '</s>',
  // Lower-cased word tokens for each sentence, wrapped in start and end markers.
  sentences: text => text.toLowerCase().split(/[.!?]+/).map(s => s.match(/[a-z’']+/g) || []).filter(s => s.length)
    .map(s => [Model.START, ...s, Model.END]),
  count(text) {
    const unigrams = {}, bigrams = {};
    for (const sentence of Model.sentences(text)) {
      sentence.forEach((token, i) => {
        unigrams[token] = (unigrams[token] || 0) + 1;
        if (i + 1 < sentence.length) { const pair = bigrams[token] = bigrams[token] || {}; pair[sentence[i + 1]] = (pair[sentence[i + 1]] || 0) + 1; }
      });
    }
    return {unigrams, bigrams};
  },
  stats(text) {
    const words = Model.sentences(text).flatMap(s => s.slice(1, -1));
    return {tokens: words.length, types: new Set(words).size};
  },
  // Every token that can follow something: the words plus the end marker.
  vocabulary: counts => Object.keys(counts.unigrams).filter(token => token !== Model.START).sort(),
  probability(counts, previous, next, smooth = false) {
    const pair = (counts.bigrams[previous] || {})[next] || 0, total = Object.values(counts.bigrams[previous] || {}).reduce((a, b) => a + b, 0);
    if (smooth) return (pair + 1) / (total + Model.vocabulary(counts).length);
    return total ? pair / total : 0;
  },
  // Followers of a word, most likely first; ties in alphabetical order.
  next(counts, previous, smooth = false) {
    const seen = counts.bigrams[previous] || {}, words = smooth ? Model.vocabulary(counts) : Object.keys(seen);
    return words.map(word => ({word, count: seen[word] || 0, p: Model.probability(counts, previous, word, smooth)}))
      .sort((a, b) => b.p - a.p || a.word.localeCompare(b.word));
  },
  // Greedy generation: always take the most likely next token; stop at the end marker or a repeat.
  generate(counts, limit = 12) {
    const out = [], used = new Set(); let token = Model.START;
    while (out.length < limit) {
      const best = Model.next(counts, token)[0];
      if (!best || best.word === Model.END || used.has(token + ' ' + best.word)) break;
      used.add(token + ' ' + best.word); out.push(best.word); token = best.word;
    }
    return out.join(' ');
  },
};
function start() {
  const pick = Kit.get('word');
  function draw() {
    const text = Kit.get('corpus').value, counts = Model.count(text), smooth = Kit.get('smooth').value === '1', stats = Model.stats(text);
    const options = [Model.START, ...Model.vocabulary(counts).filter(token => token !== Model.END)], keep = options.includes(pick.value) ? pick.value : options[0];
    pick.replaceChildren(...options.map(token => new Option(token === Model.START ? 'start of sentence' : token, token)));
    pick.value = keep;
    const followers = Model.next(counts, keep, smooth);
    Kit.rows(Kit.get('rows'), followers.map(row => [row.word === Model.END ? 'end of sentence' : row.word, String(row.count), Kit.fmt(row.p, 3)]));
    Kit.get('stats').textContent = stats.tokens + ' word tokens, ' + stats.types + ' different word types.';
    const seen = followers.filter(row => row.count).length;
    Kit.get('result').textContent = (followers.length ? 'After “' + (keep === Model.START ? 'start of sentence' : keep) + '” the model has seen ' + seen + ' different continuations. ' : '')
      + (smooth ? 'Smoothing gives every unseen pair a small probability, so no sentence is judged impossible. ' : 'Without smoothing, any pair the corpus lacks gets probability 0. ')
      + 'Greedy generation from this corpus: “' + Model.generate(counts) + '”.';
  }
  Kit.bind(['corpus', 'word', 'smooth'], draw);
}
if (typeof module === 'object') module.exports = Model; else start();
