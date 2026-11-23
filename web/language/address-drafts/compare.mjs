// Match tokens in order, allowing the reader to choose whether punctuation and case count.
export function tokens(text, punctuation, matchCase) {
  const words = /[\p{L}\p{M}\p{N}]+(?:[’'][\p{L}\p{M}\p{N}]+)*/gu;
  const all = /[\p{L}\p{M}\p{N}]+(?:[’'][\p{L}\p{M}\p{N}]+)*|[^\s]/gu;
  return Array.from(text.matchAll(punctuation ? all : words), (hit) => ({
    start: hit.index,
    end: hit.index + hit[0].length,
    text: hit[0],
    key: matchCase ? hit[0] : hit[0].toLowerCase()
  }));
}

export function align(a, b) {
  const width = b.length + 1;
  const scores = new Uint16Array((a.length + 1) * width);
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      const at = i * width + j;
      scores[at] =
        a[i].key === b[j].key
          ? 1 + scores[at + width + 1]
          : Math.max(scores[at + width], scores[at + 1]);
    }
  }
  const pairs = [];
  let i = 0,
    j = 0;
  while (i < a.length && j < b.length) {
    const at = i * width + j;
    if (a[i].key === b[j].key) {
      pairs.push([i++, j++]);
    } else if (scores[at + width] >= scores[at + 1]) {
      i++;
    } else j++;
  }
  return pairs;
}

export function containsWords(text, phrase) {
  const words = tokens(text, false, false).map((t) => t.key);
  const query = tokens(phrase, false, false).map((t) => t.key);
  return query.length > 0 && words.some((_, i) => query.every((key, j) => words[i + j] === key));
}

export const prompts = [
  { passage: 2, phrase: 'met here' },
  { passage: 3, phrase: 'who died here' },
  { passage: 3, phrase: 'gave their lives' },
  { passage: 4, phrase: 'fitting and proper' },
  { passage: 4, phrase: 'in all propriety' },
  { passage: 5, phrase: 'we can not dedicate' },
  { passage: 6, phrase: 'have hallowed it' },
  { passage: 6, phrase: 'have consecrated it' },
  { passage: 8, phrase: 'unfinished work' },
  { passage: 11, phrase: 'by the people' }
];
