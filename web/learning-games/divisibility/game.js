/* Original Primer practice model: exact decimal arithmetic and limited clues. */
(function (scope) {
  'use strict';
  function digits(value) {
    if (typeof value !== 'string' || !/^\d{1,80}$/.test(value)) throw new Error('Use 1–80 decimal digits, without spaces or signs.');
    return value;
  }
  function evaluate(challenge) {
    const d = challenge.divisor;
    if (![2, 4, 5, 10].includes(d)) throw new Error('Choose 2, 4, 5 or 10.');
    const hidden = challenge.kind === 'hidden';
    const text = digits(hidden ? challenge.suffix : challenge.number);
    if (hidden && (!Number.isInteger(challenge.prefix_digits) || challenge.prefix_digits < 1 || challenge.prefix_digits > 20)) throw new Error('Invalid hidden prefix.');
    const divisor = BigInt(d), value = BigInt(text);
    if (hidden && (10n ** BigInt(text.length)) % divisor !== 0n) {
      if (value % 2n !== 0n) return { answer: 'no', explanation: 'The visible final digit is odd. Every multiple of 4 is even, so no hidden prefix can make this number divisible by 4.' };
      const first = (10n ** BigInt(challenge.prefix_digits - 1)) * (10n ** BigInt(text.length)) + value;
      const second = first + (10n ** BigInt(text.length));
      return { answer: 'unknown', explanation: 'The same ending can hide different outcomes: ' + first + ' leaves remainder ' + first % divisor + '; ' + second + ' leaves remainder ' + second % divisor + ' when divided by ' + d + '. Reveal another digit to decide.' };
    }
    const width = d === 4 ? 2 : 1;
    const base = d === 4 ? 100n : 10n;
    const tail = hidden ? value % base : BigInt(text.slice(-width));
    const remainder = tail % divisor;
    return { answer: remainder === 0n ? 'yes' : 'no', explanation:
      (hidden ? 'Every hidden prefix contributes a multiple of ' + String(10n ** BigInt(text.length)) + '. '
        : value + ' = ' + base + ' × ' + value / base + ' + ' + tail + '. ')
      + base + ' is divisible by ' + d + ', so the final ' + (width === 1 ? 'digit' : 'two digits')
      + ' decide. ' + tail + ' leaves remainder ' + remainder + ' when divided by ' + d + '.' };
  }
  function mount(root, model) {
    const doc = root.ownerDocument;
    function make(tag, text, cls) { const e = doc.createElement(tag); if (text != null) e.textContent = text; if (cls) e.className = cls; return e; }
    function button(text, action) { const b = make('button', text, 'btn'); b.type = 'button'; b.addEventListener('click', action); return b; }
    root.className = 'card divisibility-game'; root.setAttribute('aria-label', model.title);
    root.append(make('h3', model.title), make('p', 'Use place value to unlock the clues. This is practice; official mastery comes from your module quiz.', 'muted'));
    const progress = make('progress'); progress.max = model.challenges.length; progress.value = 0; progress.setAttribute('aria-label', 'Challenges solved');
    const counter = make('p', '', 'muted'), question = make('section');
    root.append(progress, counter, question);
    let index = 0;
    function draw(focus) {
      question.replaceChildren();
      counter.textContent = index + ' of ' + model.challenges.length + ' challenges solved';
      if (index === model.challenges.length) {
        question.append(make('h4', 'Case solved!'), make('p', model.knowledge.one_digit), make('p', model.knowledge.two_digits), make('p', 'Try a new number below, or take the module quiz when you are ready.'), button('Play again', () => { index = 0; progress.value = 0; draw(true); }));
      } else {
        const c = model.challenges[index], result = evaluate(c);
        const heading = make('h4', c.kind === 'hidden' ? 'Do the visible digits settle the question?' : 'Can it divide evenly?');
        const number = make('p', c.kind === 'hidden' ? 'Hidden digits: ' + '□'.repeat(c.prefix_digits) + c.suffix : c.number, 'divisibility-number');
        const prompt = make('p', 'Divisible by ' + c.divisor + '?');
        const feedback = make('p'); feedback.setAttribute('role', 'status'); feedback.setAttribute('aria-live', 'polite');
        const choices = make('div', null, 'divisibility-choices');
        let selection = null, solved = false;
        ['yes', 'no', ...(c.kind === 'hidden' ? ['unknown'] : [])].forEach(answer => {
          const b = button({yes:'Yes',no:'No',unknown:'Not enough information'}[answer], () => {
            selection = answer;
            for (const sibling of choices.children) sibling.setAttribute('aria-pressed', String(sibling === b));
            check.disabled = false;
          });
          b.setAttribute('aria-pressed', 'false'); choices.append(b);
        });
        const next = button('Continue', () => { index++; draw(true); }); next.hidden = true;
        const check = button('Check answer', () => {
          if (solved || selection === null) return;
          if (selection !== result.answer) { feedback.textContent = 'Try again. ' + result.explanation; return; }
          solved = true; progress.value = index + 1;
          feedback.textContent = 'Correct. ' + result.explanation;
          check.disabled = true; for (const b of choices.children) b.disabled = true;
          next.hidden = false;
        }); check.disabled = true;
        question.append(heading, number, prompt, choices, check, feedback, next);
      }
      const heading = question.querySelector('h4'); heading.tabIndex = -1;
      if (focus) heading.focus();
    }
    draw(false);
    const sandbox = make('details'), summary = make('summary', 'Experiment with your own number'); sandbox.append(summary);
    const label = make('label', 'Whole number '), input = make('input'); input.type = 'text'; input.inputMode = 'numeric'; input.maxLength = 80; input.value = '54280'; label.append(input);
    const divLabel = make('label', ' Divide by '), select = make('select');
    for (const d of model.game_model.allowed_divisors) { const opt = make('option', String(d)); opt.value = String(d); select.append(opt); } divLabel.append(select);
    const output = make('p'); output.setAttribute('role', 'status');
    const tryIt = button('Test my number', () => {
      try { const r = evaluate({kind:'exact', number:input.value, divisor:Number(select.value)}); output.textContent = (r.answer === 'yes' ? 'Divides evenly. ' : 'Does not divide evenly. ') + r.explanation; }
      catch (e) { output.textContent = e.message; }
    });
    sandbox.append(label, divLabel, tryIt, output); root.append(sandbox);
    return root;
  }
  scope.PrimerDivisibility = Object.freeze({ evaluate, mount });
})(typeof window !== 'undefined' ? window : globalThis);
