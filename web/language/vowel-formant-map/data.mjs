export const languages = { En: 'English', Sp: 'Spanish' };
const columns = ['l1','speaking','speaker','frag','nwords','vowel','word','length','en','f0','f1','f2','f3'];

export function readTokens(text) {
  const lines = text.trimEnd().split(/\r?\n/);
  if (lines.shift() !== columns.join(',')) throw Error('The vowel table has an unexpected header.');
  return lines.map((line, index) => {
    const values = line.split(',');
    if (values.length !== columns.length) throw Error('The vowel table has an unexpected row.');
    const token = Object.fromEntries(columns.map((name, column) =>
      [name, column < 3 || name === 'vowel' || name === 'word' ? values[column] : Number(values[column])]));
    if (!(token.l1 in languages) || !(token.speaking in languages) ||
        !Number.isFinite(token.f1) || !Number.isFinite(token.f2)) throw Error('A vowel token cannot be plotted.');
    return { row: index + 1, ...token };
  });
}

export function speakerKey(token) {
  return token.l1 + '|' + token.speaker;
}

export function selectTokens(tokens, filters) {
  const word = filters.word.trim().toLowerCase();
  return tokens.filter(token =>
    (!filters.speaking || token.speaking === filters.speaking) &&
    (!filters.l1 || token.l1 === filters.l1) &&
    (!filters.vowel || token.vowel === filters.vowel) &&
    (!filters.speaker || speakerKey(token) === filters.speaker) &&
    (!word || token.word.toLowerCase().includes(word)));
}

export function median(values) {
  if (!values.length) return null;
  const sorted = values.slice().sort((a,b) => a-b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle-1]+sorted[middle])/2;
}

export function summaries(tokens, method) {
  const groups = new Map();
  for (const token of tokens) {
    const id = [token.speaking,token.l1,token.vowel].join('|');
    if (!groups.has(id)) groups.set(id, []);
    groups.get(id).push(token);
  }
  return [...groups].map(([id, rows]) => {
    const speakers = new Map();
    for (const token of rows) {
      const key = speakerKey(token);
      if (!speakers.has(key)) speakers.set(key, []);
      speakers.get(key).push(token);
    }
    const value = formant => method === 'speakers'
      ? median([...speakers.values()].map(records => median(records.map(token => token[formant]))))
      : median(rows.map(token => token[formant]));
    const {l1,speaking,vowel} = rows[0];
    return {id,l1,speaking,vowel,tokens:rows.length,speakers:speakers.size,f1:value('f1'),f2:value('f2')};
  }).sort((a,b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
}

export function comparison(first, second, formant) {
  const difference = first[formant] - second[formant];
  return difference === 0 ? 'tie' : difference > 0 ? 'first' : 'second';
}

export function plotPosition(f1, f2, box) {
  return {
    x:box.left + (3400-f2)/3000*(box.right-box.left),
    y:box.top + f1/2100*(box.bottom-box.top),
  };
}
