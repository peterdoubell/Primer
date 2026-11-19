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
  // A stop is promised before its section has loaded; one that turns out to
  // have nothing behind it is withdrawn rather than left pointing at nothing.
  root.dropStop = target => {
    const index = targets.findIndex(item => item.target === target);
    if (index < 0 || !buttons[index].isConnected) return;
    buttons[index].remove(); visited.delete(index);
    progress.max = trail.children.length; progress.value = visited.size;
  };
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
  const play = learningGameSection(page, nodeId);
  const targets = [
    { title: 'Learn', hint: 'Discover the idea', target: teaching },
    { title: 'Play', hint: 'Learn by doing', target: play },
    { title: 'Explore', hint: 'Investigate the visuals', target: media },
    { title: 'Read', hint: 'Make connections', target: reading },
    { title: 'Challenge', hint: quiz.disabled ? 'See what unlocks this lesson' : 'Show what you know', target: quiz.disabled ? locked : actions },
  ].filter(item => item.target);
  if (!targets.length) return;
  const mission = renderModuleMission({}, targets);
  page.insertBefore(mission, page.children[2] || null);
  if (play) { mission.after(play); mountLearningGame(play, page, nodeId, mission); }
};

// Learning sequences: one idea in a few small checked steps. The authored
// models stay on the server, which marks every response; the player and its
// stylesheet are fetched only when a lesson is opened.
let learningGameAssets;
function loadLearningGames(assets) {
  if (!learningGameAssets) {
    const wanted = [...assets.scripts, assets.style];
    const add = url => new Promise((resolve, reject) => {
      const style = url === assets.style;
      const tag = document.createElement(style ? 'link' : 'script');
      if (style) { tag.rel = 'stylesheet'; tag.href = url; } else { tag.src = url; tag.async = false; }
      tag.dataset.learningGame = '';
      tag.onload = resolve;
      tag.onerror = () => { tag.remove(); reject(new Error('Activity file unavailable')); };
      document.head.append(tag);
    });
    // Scripts in order, each waiting for the last: the player needs the drawings.
    learningGameAssets = wanted.reduce((chain, url) => chain.then(() => add(url)), Promise.resolve())
      .catch(error => {
        learningGameAssets = null;
        document.head.querySelectorAll('[data-learning-game]').forEach(tag => tag.remove());
        throw error;
      });
  }
  return learningGameAssets;
}
function learningGameSection(page, nodeId) {
  if (typeof fetch !== 'function' || !nodeId) return null;
  return el('section', { class: 'card lg-play', 'aria-label': 'Learn by doing' });
}
async function mountLearningGame(section, page, nodeId, mission) {
  section.replaceChildren(el('p', { class: 'muted', role: 'status' }, 'Opening the activity…'));
  try {
    const response = await fetch('/api/learning-games/' + encodeURIComponent(nodeId));
    if (response.status === 401 && typeof toSignIn === 'function') return toSignIn();
    if (!response.ok) throw new Error('Activity unavailable');
    const data = await response.json();
    if (!section.isConnected) return;
    if (!data.sequences.length) { if (mission) mission.dropStop(section); section.remove(); return; }
    await loadLearningGames(data.assets);
    if (!section.isConnected) return;
    window.PrimerLearningGames.mount(section, data, { page });
  } catch (error) {
    if (!section.isConnected) return;
    // The lesson never depends on this: say so, and offer the one thing that helps.
    section.replaceChildren(el('h3', {}, 'Learn by doing'),
      el('p', { role: 'alert' }, 'The activity could not load. Your lesson is still available.'),
      btn({ class: 'btn', onclick: () => mountLearningGame(section, page, nodeId, mission) }, 'Try again'));
  }
}

// The open number bench belongs to one lesson; it loads only there.
let divisibilityGameAssets;
function loadDivisibilityGame() {
  if (!divisibilityGameAssets) {
    divisibilityGameAssets = Promise.all([
      new Promise((resolve, reject) => {
        if (window.PrimerDivisibility) return resolve();
        const script = document.createElement('script');
        script.src = '/app/learning-games/divisibility/game.js';
        script.onload = resolve;
        script.onerror = () => { script.remove(); reject(new Error('Game script unavailable')); };
        document.head.append(script);
      }),
      fetch('/app/learning-games/divisibility/model.json').then(response => {
        if (!response.ok) throw new Error('Game model unavailable');
        return response.json();
      }),
    ]).then(([, model]) => model).catch(error => { divisibilityGameAssets = null; throw error; });
  }
  return divisibilityGameAssets;
}
const divisibilityOriginalRenderNode = renderNode;
renderNode = async function(page, nodeId) {
  await divisibilityOriginalRenderNode(page, nodeId);
  if (nodeId !== 'math.2.primes' || !page.isConnected || !page.querySelector('.lesson-card')) return;
  const game = el('section', { class: 'card divisibility-game' });
  game.append(el('p', {}, 'Loading the number bench…'));
  const anchor = page.querySelector('.lg-play') || page.querySelector('.module-mission');
  if (anchor) anchor.after(game); else page.append(game);
  async function mountGame() {
    try {
      const model = await loadDivisibilityGame();
      if (!game.isConnected) return;
      game.replaceChildren(); window.PrimerDivisibility.mount(game, model);
    } catch (error) {
      if (!game.isConnected) return;
      game.replaceChildren(el('p', {}, 'The number bench could not load. Your lesson is still available.'),
        btn({ class: 'btn', onclick: mountGame }, 'Retry'));
    }
  }
  await mountGame();
};
