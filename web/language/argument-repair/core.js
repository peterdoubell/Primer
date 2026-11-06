'use strict';

(function () {
  const facts = {
    hours: { title: 'Current opening hours', text: 'Harbour Library opens Monday to Friday, 09:00–17:00. It currently closes on Saturdays.' },
    proposal: { title: 'The actual proposal', text: 'Open 09:00–12:00 on four Saturdays as a trial. Keep every existing weekday session. The estimated extra cost is £480, within a £600 trial budget.' },
    staffing: { title: 'What the proposal does not supply', text: 'The proposal includes a cost estimate. It has no confirmed roster showing which staff can work the four extra sessions.' },
    alternatives: { title: 'Other options on the agenda', text: 'The agenda also lists one Tuesday evening opening and a reserved-book pickup service. Their costs and likely access benefits have not yet been compared.' },
    comparison: { title: 'A different library’s two monthly totals', text: 'North Library recorded 400 loans in May and 500 in June. Saturday opening and a reading festival both began in June. The record provides no comparison library or longer time series.' },
  };
  const assumption = text => ({ text, evidence: [], kind: 'Assumption to examine' });
  const statement = (text, evidence) => ({ text, evidence, kind: 'Claim about the record' });
  const scenarios = {
    scope: {
      title: 'Did the reply address the proposal?',
      records: ['proposal', 'staffing'],
      diagnosis: 'This is a straw man in this scenario. The reply changes a four-Saturday trial into a plan to remove weekday sessions. Its objection addresses that changed proposal.',
      original: {
        premises: [statement('The proposal replaces all weekday sessions with Saturday opening.', ['proposal']), assumption('Removing weekday sessions could make access harder for current weekday readers.')],
        warrant: 'Reject a plan if it removes access that those readers need.',
        conclusion: 'Reject the four-Saturday trial because it removes all weekday access.',
      },
      repaired: {
        premises: [statement('The trial retains all existing weekday sessions.', ['proposal']), statement('A confirmed roster for the extra sessions is missing.', ['staffing'])],
        warrant: 'Extra sessions require available staff. Roster feasibility matters when deciding whether the trial can run.',
        conclusion: 'Ask for a staffing plan before deciding on the actual four-Saturday trial.',
      },
      choices: [
        { id: 'roster', text: 'Keep the proposal’s actual scope and ask for a confirmed staffing plan.', correct: true, feedback: 'This restores the real proposal and raises a relevant unresolved question. It leaves the final decision open.' },
        { id: 'silence', text: 'Say that everyone opposing the trial dislikes readers.', correct: false, feedback: 'This assigns a motive to critics without evidence. It leaves the changed description of the proposal uncorrected.' },
        { id: 'guarantee', text: 'Keep weekday sessions and claim the £480 estimate guarantees the trial will run.', correct: false, feedback: 'The budget estimate addresses cost. The record still lacks a confirmed roster, so it does not guarantee feasibility.' },
      ],
    },
    options: {
      title: 'Are these really the only options?',
      records: ['hours', 'proposal', 'alternatives'],
      diagnosis: 'This is a false dilemma in this scenario. The argument presents two exhaustive choices even though the agenda lists additional possibilities. Its demand for an immediate choice hides those alternatives.',
      original: {
        premises: [statement('The library currently has no Saturday opening.', ['hours']), statement('The only choices are Saturday opening or doing nothing about access.', ['alternatives'])],
        warrant: 'If these are the only choices, improving access requires approving Saturday opening.',
        conclusion: 'Either approve Saturday opening or give up on improving access.',
      },
      repaired: {
        premises: [statement('Saturday opening, a Tuesday evening session and reserved-book pickup are on the agenda.', ['proposal', 'alternatives']), statement('Their costs and access benefits have not yet been compared.', ['alternatives'])],
        warrant: 'A choice among the available options should consider their costs, likely benefits and feasibility.',
        conclusion: 'Compare the three options before choosing an access improvement.',
      },
      choices: [
        { id: 'cheap', text: 'Choose Tuesday evening because it is certainly the cheapest option.', correct: false, feedback: 'The record gives no comparative costs. Naming another option does not supply the evidence needed to rank it.' },
        { id: 'compare', text: 'Include the listed alternatives and compare their costs, access benefits and feasibility.', correct: true, feedback: 'This restores the options the argument omitted and identifies the information needed to compare them.' },
        { id: 'reverse', text: 'Replace the choice with “either keep current hours or close the library.”', correct: false, feedback: 'This introduces another unsupported two-option choice and again omits the alternatives in the agenda.' },
      ],
    },
    cause: {
      title: 'Does the timing establish the cause?',
      records: ['comparison'],
      diagnosis: 'The two totals show an increase after Saturday opening began. The same record also reports a new reading festival, so it cannot identify the separate contribution of either change.',
      original: {
        premises: [statement('Loans at North Library rose from 400 in May to 500 in June, an increase of 25%.', ['comparison']), statement('Saturday opening began in June.', ['comparison'])],
        warrant: 'A rise that follows a change must have been caused by that change alone.',
        conclusion: 'Saturday opening alone caused all of the 25% increase.',
      },
      repaired: {
        premises: [statement('Loans rose by 25% between these two months.', ['comparison']), statement('Saturday opening and a reading festival both began in June; the record has no comparison library or longer series.', ['comparison'])],
        warrant: 'These observations do not separate the effects of the simultaneous changes or other differences between the months.',
        conclusion: 'Report the increase and gather comparative evidence before attributing it to Saturday opening.',
      },
      choices: [
        { id: 'festival', text: 'Conclude that the reading festival alone caused the entire increase.', correct: false, feedback: 'This substitutes a different cause without separating the effects of either change.' },
        { id: 'none', text: 'Conclude that Saturday opening had no effect because a festival also happened.', correct: false, feedback: 'The festival is another possible influence. Its presence does not establish that Saturday opening had zero effect.' },
        { id: 'limits', text: 'State the observed increase and seek a suitable comparison before assigning the cause.', correct: true, feedback: 'This keeps the measured change while limiting the causal claim to what the evidence can support. A comparison would also need checks for other differences.' },
      ],
    },
  };
  const appeals = {
    ethos: { name: 'Credibility', quote: '“I have managed this library for twelve years, and I take its staffing seriously.”', explanation: 'The speaker presents experience to establish credibility, an appeal to ethos. Check whether that experience is relevant and whether the factual claims have support.' },
    pathos: { name: 'Emotion', quote: '“Imagine waiting all week for the chance to borrow a book with your child.”', explanation: 'The sentence invites an emotional response, an appeal to pathos. That concern can matter while the proposal’s costs, access benefits and feasibility still need examination.' },
    logos: { name: 'Reasoning', quote: '“The £480 estimate is £120 below the £600 trial budget.”', explanation: 'The sentence uses a calculation, an appeal to logos. The arithmetic supports a claim about the stated estimate and budget. It leaves the staffing question unresolved.' },
  };

  function evaluateRepair(scenarioId, choiceId) {
    const scenario = scenarios[scenarioId];
    if (!Object.hasOwn(scenarios, scenarioId)) throw new RangeError('Unknown scenario');
    const choice = scenario.choices.find(item => item.id === choiceId);
    if (!choice) throw new RangeError('Unknown repair choice');
    return { correct: choice.correct, feedback: choice.feedback, map: choice.correct ? scenario.repaired : scenario.original };
  }

  const api = Object.freeze({ facts, scenarios, appeals, evaluateRepair });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof globalThis !== 'undefined') globalThis.PrimerRhetoric = api;
})();
