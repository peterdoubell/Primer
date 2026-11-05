'use strict';
// Shared study navigation; assessment and mastery remain server-owned.
function renderModuleMission(n, targets) {
  const root = el('section', { class: 'module-mission card', 'aria-label': 'Module mission' });
  const status = el('p', { class: 'muted', role: 'status', 'aria-live': 'polite' });
  const progress = el('progress', { max: targets.length, value: 0, 'aria-label': 'Study steps visited' });
  const trail = el('div', { class: 'module-mission-trail' });
  const visited = new Set();
  const buttons = [];
  const profile = S.state && S.state.profile || {};
  root.append(el('div', { class: 'module-mission-heading' },
    el('div', {}, el('span', { class: 'module-mission-kicker' }, 'YOUR MODULE MISSION'),
      el('h3', {}, 'One idea. A few small steps.')),
    el('span', { class: 'module-mission-reward' },
      (profile.xp || 0) + ' growth · ' + (profile.streak || 0) + ' day streak')),
    el('p', { class: 'muted' }, 'Learn, experiment, then test what sticks. Go at your own pace.'),
    progress, trail, status);
  targets.forEach(({ title, hint, target }, index) => {
    const button = btn({ class: 'module-mission-stop', onclick: () => {
      visited.add(index);
      progress.value = visited.size;
      buttons.forEach((item, i) => {
        item.classList.toggle('visited', visited.has(i));
        if (i === index) item.setAttribute('aria-current', 'step');
        else item.removeAttribute('aria-current');
      });
      status.textContent = visited.size + ' of ' + targets.length + ' study steps visited. '
        + (visited.size === targets.length ? 'Ready to put it into practice? Take the challenge below.' : hint);
      target.setAttribute('tabindex', '-1');
      target.scrollIntoView({ block: 'start', behavior: 'instant' });
      target.focus({ preventScroll: true });
    } }, el('span', { class: 'module-mission-number', 'aria-hidden': 'true' }, index + 1),
      el('span', {}, el('b', {}, title), el('small', {}, hint)));
    buttons.push(button);
    trail.append(button);
  });
  status.textContent = 'Choose a step to begin. Study steps do not award mastery; quiz results do.';
  return root;
}

const moduleOriginalTeachingLesson = renderTeachingLesson;
renderTeachingLesson = function(n) {
  const root = moduleOriginalTeachingLesson(n);
  if (!root) return root;
  const steps = Array.from(root.querySelectorAll('.teaching-step'));
  if (steps.length > 1) {
    let current = 0, showAll = false;
    const label = el('span', { class: 'teaching-step-count', role: 'status', 'aria-live': 'polite' });
    const update = (focus = false) => {
      steps.forEach((step, i) => { step.hidden = !showAll && i !== current; });
      previous.disabled = current === 0 || showAll;
      next.disabled = current === steps.length - 1 || showAll;
      label.textContent = showAll ? 'All learning steps' : 'Step ' + (current + 1) + ' of ' + steps.length;
      toggle.textContent = showAll ? 'One step at a time' : 'Show full lesson';
      if (focus) {
        const heading = steps[current].querySelector('h4');
        heading.setAttribute('tabindex', '-1'); heading.focus({ preventScroll: true });
      }
    };
    const previous = btn({ class: 'btn ghost small', onclick: () => { current--; update(true); } }, 'Back');
    const next = btn({ class: 'btn gold small', onclick: () => { current++; update(true); } }, 'Continue');
    const toggle = btn({ class: 'btn ghost small', onclick: () => { showAll = !showAll; update(); } });
    root.append(el('div', { class: 'teaching-step-controls' }, previous, label, next, toggle));
    update();
  }
  if (n.learning_enrichment) {
    const extra = n.learning_enrichment;
    const section = el('section', { class: 'teaching-enrichment', 'aria-labelledby': 'enrichment-heading' },
      el('h4', { id: 'enrichment-heading' }, extra.title),
      el('p', { class: 'muted' }, extra.gap_addressed),
      el('p', {}, extra.explanation));
    [['worked_example', 'Work through an example'], ['activity', 'Apply the idea'],
      ['reflection', 'Check your reasoning']].forEach(([key, title]) => section.append(
        el('h5', {}, title), el('p', {}, extra[key])));
    section.append(el('p', { class: 'muted' }, extra.authorship),
      el('p', {}, 'Source reading: ', ...extra.sources.flatMap((source, index) =>
        [index ? ' · ' : '', radiologySourceLink(source.title, source.url)])));
    root.append(section);
  }
  return root;
};
const moduleOriginalRenderNode = renderNode;
renderNode = async function(page, nodeId) {
  await moduleOriginalRenderNode(page, nodeId);
  // A failed or retired route has no lesson actions to guide.
  const quiz = Array.from(page.querySelectorAll('button')).find(button => button.textContent.includes('Take the quiz'));
  if (!quiz || !page.isConnected) return;
  const teaching = page.querySelector('.teaching-lesson');
  const media = page.querySelector('.lesson-media');
  const reading = page.querySelector('.lesson-card')?.parentElement;
  const actions = quiz.parentElement;
  const locked = page.querySelector('.req-chip')?.parentElement;
  const targets = [
    { title: 'Learn', hint: 'Discover the idea', target: teaching },
    { title: 'Explore', hint: 'Investigate the visuals', target: media },
    { title: 'Read', hint: 'Make connections', target: reading },
    { title: 'Challenge', hint: quiz.disabled ? 'See what unlocks this lesson' : 'Show what you know', target: quiz.disabled ? locked : actions },
  ].filter(item => item.target);
  if (targets.length) page.insertBefore(renderModuleMission({}, targets), page.children[2] || null);
};
