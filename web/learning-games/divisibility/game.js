/* Original Primer practice model: exact decimal arithmetic and limited clues.

   The guided challenges that used to live here are now two learning sequences
   on the shared player ("Last-Digit Detective" and "Longer Endings", authored
   in data/learning-games/number-theory.lg and marked on the server).  What
   remains is the part a sequence cannot be: an open bench where the reader
   tests any whole number they like, of any length, with exact arithmetic. */
(function (scope) {
  'use strict';
  function digits(value) {
    if (typeof value !== 'string' || !/^\d{1,80}$/.test(value)) throw new Error('Use 1–80 decimal digits, without spaces or signs.');
    return value;
  }
  // d divides 10^k exactly, so the last k digits fix the remainder.
  const suffixWidths = {2:1, 4:2, 5:1, 8:3, 10:1, 16:4, 125:3};
  function english(template, values = {}) {
    return template.replace(/\{(\w+)\}/g, (_, name) => String(values[name]));
  }

  function evaluate(challenge, format = english) {
    const d = challenge.divisor;
    if (!Number.isInteger(d) || !Object.hasOwn(suffixWidths, d)) {
      throw new Error('Choose 2, 4, 5, 8, 10, 16 or 125.');
    }
    const width = suffixWidths[d];
    const divisor = BigInt(d);
    const base = 10n ** BigInt(width);

    if (challenge.kind === 'suffix_width') {
      const previousBase = base / 10n;
      return {
        answer: String(width),
        explanation: format('{base} is divisible by {divisor}. Checking an ending of length {width} is enough. Compare {base} with {other}. They agree in their last {shortWidth} digits, but only the first is divisible by {divisor}.',
          {base, divisor: d, width, other: base + previousBase, shortWidth: width - 1}),
      };
    }

    const hidden = challenge.kind === 'hidden';
    const text = digits(hidden ? challenge.suffix : challenge.number);
    const value = BigInt(text);
    if (challenge.kind === 'repair_count') {
      const fixes = [];
      for (let index = 0; index < text.length; index++) {
        for (const digit of '0123456789') {
          if (digit === text[index]) continue;
          const candidate = text.slice(0, index) + digit + text.slice(index + 1);
          if (BigInt(candidate) % divisor === 0n) {
            fixes.push(format('position {position} → {candidate}', {position: text.length - index, candidate}));
            break;
          }
        }
      }
      return {
        answer: String(fixes.length),
        explanation: (fixes.length
          ? format('Working edits, counted from the right: {edits}.', {edits: fixes.join(', ')})
          : format('No single replacement produces a multiple.'))
          + ' ' + format('Changing a digit before the ending of length {width} adds or subtracts a multiple of {base} and preserves the remainder.', {width, base}),
      };
    }

    if (hidden) {
      if (!Number.isInteger(challenge.prefix_digits) || challenge.prefix_digits < 1 || challenge.prefix_digits > 20) {
        throw new Error('Invalid hidden prefix.');
      }
      const shift = 10n ** BigInt(text.length);
      if (shift % divisor !== 0n) {
        const start = 10n ** BigInt(challenge.prefix_digits - 1);
        const end = 10n * start;
        let multiple, nonmultiple;
        // After d prefix increments the residue repeats. Check at most one cycle.
        for (let prefix = start; prefix < end && prefix < start + divisor; prefix++) {
          const candidate = prefix * shift + value;
          if (candidate % divisor === 0n) multiple = candidate;
          else nonmultiple = candidate;
        }
        if (multiple !== undefined && nonmultiple !== undefined) {
          return { answer: 'unknown', explanation: format('{multiple} and {nonmultiple} share this ending. Only the first is divisible by {divisor}.', {multiple, nonmultiple, divisor: d}) };
        }
        return { answer: multiple !== undefined ? 'yes' : 'no',
          explanation: format('Every possible prefix gives the same divisibility result for this ending.') };
      }
    }

    const tail = value % base;
    const remainder = tail % divisor;
    return { answer: remainder === 0n ? 'yes' : 'no', explanation:
      (hidden ? format('The hidden prefix contributes a multiple of {shift}.', {shift: 10n ** BigInt(text.length)})
        : value + ' = ' + base + ' × ' + value / base + ' + ' + tail + '.')
      + ' ' + (width === 1
        ? format('{base} is divisible by {divisor}, so the final digit determines divisibility.', {base, divisor: d})
        : format('{base} is divisible by {divisor}, so the final {width} digits determine divisibility.', {base, divisor: d, width}))
      + ' ' + format('Dividing {tail} by {divisor} leaves a remainder of {remainder}.', {tail, divisor: d, remainder}) };
  }

  // The open bench: any number, any allowed divisor, worked exactly.
  function mount(root, model) {
    const doc = root.ownerDocument;
    function make(tag, text, cls) { const e = doc.createElement(tag); if (text != null) e.textContent = text; if (cls) e.className = cls; return e; }
    root.className = 'card divisibility-game'; root.setAttribute('aria-label', model.title);
    root.append(make('h3', model.title), make('p', model.invitation, 'muted'));
    const label = make('label', 'Whole number '), input = make('input'); input.type = 'text'; input.inputMode = 'numeric'; input.maxLength = 80; input.value = '54280'; label.append(input);
    const divLabel = make('label', ' Divide by '), select = make('select');
    for (const d of model.game_model.allowed_divisors) { const opt = make('option', String(d)); opt.value = String(d); select.append(opt); } divLabel.append(select);
    const output = make('p'); output.setAttribute('role', 'status'); output.setAttribute('aria-live', 'polite');
    const tryIt = make('button', 'Test my number', 'btn'); tryIt.type = 'button';
    const run = () => {
      try {
        const result = evaluate({kind:'exact', number:input.value.trim(), divisor:Number(select.value)});
        output.textContent = (result.answer === 'yes' ? 'Divides evenly.' : 'Does not divide evenly.') + ' ' + result.explanation;
      } catch (error) { output.textContent = error.message; }
    };
    tryIt.addEventListener('click', run);
    input.addEventListener('keydown', event => { if (event.key === 'Enter') run(); });
    root.append(label, divLabel, tryIt, output, make('p', model.knowledge.suffix_rule, 'muted'));
    return root;
  }
  scope.PrimerDivisibility = Object.freeze({ evaluate, mount });
})(typeof window !== 'undefined' ? window : globalThis);
