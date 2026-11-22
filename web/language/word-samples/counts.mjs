export const localWindow = 25;

export function tokenize(text, keepCase = false) {
  const words = [];
  const pattern = /\p{L}[\p{L}\p{M}]*(?:[’']\p{L}[\p{L}\p{M}]*)*/gu;
  for (const hit of text.matchAll(pattern)) {
    let form = hit[0].normalize('NFC').replaceAll('’', "'");
    if (!keepCase) form = form.toLocaleLowerCase('en-GB');
    words.push({ text: hit[0], form, start: hit.index, end: hit.index + hit[0].length });
  }
  return words;
}

export function traceWords(words) {
  const counts = new Map();
  const recent = new Map();
  const trace = [];
  let totalWindowTypes = 0;
  for (const [i, word] of words.entries()) {
    const prior = counts.get(word.form);
    const count = (prior?.count || 0) + 1;
    const first = prior?.first ?? i;
    counts.set(word.form, { count, first });
    recent.set(word.form, (recent.get(word.form) || 0) + 1);
    if (i >= localWindow) {
      const expired = words[i - localWindow].form;
      const remaining = recent.get(expired) - 1;
      if (remaining) recent.set(expired, remaining);
      else recent.delete(expired);
    }
    const windows = Math.max(0, i + 2 - localWindow);
    if (windows) totalWindowTypes += recent.size;
    trace.push({
      types: counts.size,
      ratio: counts.size / (i + 1),
      meanLocalRatio: windows ? totalWindowTypes / (localWindow * windows) : null,
      first, count,
    });
  }
  return trace;
}

export function frequentForms(words, length) {
  const counts = new Map();
  for (const word of words.slice(0, length)) {
    counts.set(word.form, (counts.get(word.form) || 0) + 1);
  }
  // Maps retain first-observed order, which breaks equal-frequency ties.
  return [...counts].sort((a, b) => b[1] - a[1]);
}
