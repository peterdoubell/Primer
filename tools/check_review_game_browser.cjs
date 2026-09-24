#!/usr/bin/env node
'use strict';

// Mutating end-to-end QA: run ONLY against an explicitly supplied disposable
// loopback server. Seed an adult profile with chosen pronouns, exactly eight due cards with unique
// fronts, and at least one future card before running. Playwright may be
// supplied through NODE_PATH. No profile or placement is changed by this test.
// node tools/check_review_game_browser.cjs http://127.0.0.1:PORT /tmp/evidence
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const base = process.argv[2];
const out = process.argv[3];
assert.ok(base && out, 'Provide a disposable QA server URL and evidence directory');
const url = new URL(base);
assert.ok(['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname), 'QA must use a disposable loopback server');
const origin = url.origin;
fs.mkdirSync(out, { recursive: true });
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const deferred = () => {
  let resolve;
  const promise = new Promise(r => { resolve = r; });
  return { promise, resolve };
};

(async () => {
  const browser = await chromium.launch({ headless: true });
  const evidence = { checks: [], posts: [], sources: {}, errors: [], presentationOverrides: [] };
  const sourceReads = [];
  let page, mode = null;
  const note = name => { evidence.checks.push(name); console.log('PASS ' + name); };
  const assertNoOverflow = async label => {
    const widths = await page.evaluate(() => ({ viewport: innerWidth,
      document: document.documentElement.scrollWidth,
      game: document.querySelector('.memory-game').scrollWidth,
      gameWidth: document.querySelector('.memory-game').clientWidth }));
    assert.ok(widths.document <= widths.viewport + 1, label + ': page overflow ' + JSON.stringify(widths));
    assert.ok(widths.game <= widths.gameWidth + 1, label + ': game overflow ' + JSON.stringify(widths));
  };
  const capture = async name => {
    await assertNoOverflow(name);
    assert.doesNotMatch(await page.locator('.memory-game').innerText(), /(^|\n)(null|undefined)(\n|$)/,
      name + ': optional UI nodes must not appear as literal text');
    await page.evaluate(() => {
      window.scrollTo(0, 0);
      document.querySelector('#page').scrollTop = 0;
    });
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await page.screenshot({ path: path.join(out, name + '.png'), fullPage: true });
  };
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.on('pageerror', error => evidence.errors.push(error.message));
    page.on('response', response => {
      const file = new URL(response.url()).pathname.replace(/^\/app\//, '');
      if (['app.js', 'review-game.js', 'review-game.css'].includes(file)) {
        sourceReads.push(response.body().then(body => { evidence.sources[file] = digest(body); }));
      }
    });
    // Record requests without persisting typed recall, which must stay local.
    const sentBodies = [];
    page.on('request', request => { if (request.method() === 'POST') sentBodies.push(request.postData() || ''); });
    await page.route('**/api/review/game', async route => {
      const payload = route.request().postDataJSON();
      assert.deepEqual(Object.keys(payload).sort(), ['card_id', 'expected_due', 'expected_reviews', 'quality', 'seconds']);
      assert.ok(Number.isFinite(payload.seconds) && payload.seconds >= 0);
      const current = mode;
      mode = null;
      const record = { payload, scenario: current ? current.kind : 'normal' };
      evidence.posts.push(record);
      if (current && current.kind === 'fail-before-forward') {
        record.forwarded = false;
        await route.abort('failed');
        return;
      }
      const response = await route.fetch();
      record.forwarded = true;
      record.status = response.status();
      record.response = await response.json();
      if (current && current.kind === 'lose-reply-after-save') {
        await route.abort('failed');
        return;
      }
      if (current && current.kind === 'hold-reply') {
        current.ready.resolve(record);
        await current.release.promise;
      }
      await route.fulfill({ response });
    });
    const deck = async () => {
      const response = await context.request.get(origin + '/api/review/due?limit=50');
      assert.ok(response.ok(), 'Real due API succeeds');
      return response.json();
    };
    const state = await (await context.request.get(origin + '/api/state')).json();
    assert.ok(state.profile && state.profile.stage >= 2, 'Seed an adult/sapling-or-higher QA profile');
    assert.ok(state.profile.pronouns_set, 'Seed chosen QA profile pronouns to avoid the unrelated onboarding modal');
    const initial = await deck();
    assert.equal(initial.cards.length, 8, 'Seed exactly eight due QA cards');
    assert.ok(initial.stats.total > 8, 'Seed at least one future card');
    assert.ok(initial.cards.every(card => card.due <= Date.now() / 1000), 'Due API never queues future cards');
    assert.equal(new Set(initial.cards.map(card => card.front)).size, 8, 'QA fronts must be unique');
    evidence.initialDeck = initial;
    const byFront = new Map(initial.cards.map(card => [card.front, card]));
    const currentCard = async () => {
      const front = await page.locator('.mg-question').innerText();
      const card = byFront.get(front);
      assert.ok(card, 'Game uses a real seeded due card');
      return card;
    };
    const reveal = async () => {
      const card = await currentCard();
      assert.equal(await page.locator('.mg-answer-text').count(), 0, 'Answer is absent before reveal');
      await page.locator('.mg-reveal').click();
      assert.equal(await page.locator('.mg-answer-text').innerText(), card.back);
      return card;
    };
    const waitForFeedback = async card => {
      await page.locator('.mg-next').waitFor();
      assert.equal((await currentCard()).id, card.id, 'Saving never advances the card automatically');
      const record = evidence.posts.at(-1);
      assert.equal(record.response.id, card.id);
      const expectedText = await page.evaluate(timestamp => {
        const date = new Date(timestamp * 1000), now = new Date();
        const day = date.toDateString() === now.toDateString() ? 'today' : 'on ' + date.toLocaleDateString(undefined,
          { month: 'short', day: 'numeric', ...(date.getFullYear() !== now.getFullYear() ? { year: 'numeric' } : {}) });
        return 'This memory returns ' + day + ' at ' + date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }) + '.';
      }, record.response.next_due);
      assert.equal(await page.locator('.mg-return-date').innerText(), expectedText, 'Feedback uses exact server schedule');
      return record;
    };
    const visit = async view => {
      const target = origin + '/#/' + view;
      // A same-document hash change (including same-URL goto) retains the
      // in-memory profile. Reload it when a scenario needs a fresh app boot.
      const navigation = await page.goto(target);
      if (!navigation) await page.reload();
    };
    const openRound = async () => {
      await visit('review-game');
      await page.locator('.mg-start').click();
      await page.locator('.mg-question').waitFor();
    };

    await page.goto(origin + '/#/review');
    const entry = page.getByRole('button', { name: /memory garden|play.*garden/i });
    await entry.first().click();
    await page.locator('.mg-start').waitFor();
    assert.equal(new URL(page.url()).hash, '#/review-game');
    await page.locator('.mg-classic').click();
    await page.waitForURL('**/#/review');
    await entry.first().click();
    await page.locator('.mg-start').waitFor();
    assert.equal(await page.locator('.mg-round-choice[aria-pressed="true"]').count(), 1);
    await page.locator('.mg-round-choice').nth(1).click();
    await page.waitForFunction(() => document.querySelectorAll('.mg-round-choice')[1]?.getAttribute('aria-pressed') === 'true');
    await page.locator('.mg-round-choice').first().click();
    await page.waitForFunction(() => document.querySelectorAll('.mg-round-choice')[0]?.getAttribute('aria-pressed') === 'true');
    assert.match(await page.locator('.mg-start').innerText(), /5-card/);
    await capture('memory-garden-desktop-lobby');
    await page.setViewportSize({ width: 390, height: 844 });
    await capture('memory-garden-mobile-lobby');
    await page.setViewportSize({ width: 1440, height: 1000 });
    note('Review entry, dedicated route, and 5/10-card round selection');

    // Reproduce a fast reader focusing the input before the scheduled heading
    // focus runs. The newer input focus must win, or typing Space can reveal
    // and a number can accidentally submit a review.
    await page.locator('.mg-start').evaluate(button => {
      button.click();
      document.querySelector('.mg-recall-input').focus();
    });
    const privateRecall = 'I am thinking through the answer in my own words.';
    await page.locator('.mg-recall-input').fill(privateRecall);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    assert.ok(await page.locator('.mg-recall-input').evaluate(input => document.activeElement === input),
      'Deferred heading focus must respect newer input focus');
    await page.keyboard.press('Space');
    await page.keyboard.press('1');
    assert.equal(await page.locator('.mg-answer-text').count(), 0, 'Typing shortcuts never reveal or grade');
    assert.equal(evidence.posts.length, 0);
    await page.locator('.mg-recall-input').fill(privateRecall);
    const first = await currentCard();
    await page.locator('.mg-question').focus();
    await page.keyboard.press('Space');
    await page.locator('.mg-grade').first().waitFor();
    assert.equal(await page.locator('.mg-answer-text').innerText(), first.back);
    assert.ok(await page.locator('.mg-recall-input').evaluate(input => input.readOnly));
    mode = { kind: 'fail-before-forward' };
    await page.locator('.mg-grade[data-quality="4"]').click();
    await page.locator('.mg-save-error').waitFor();
    assert.equal((await currentCard()).id, first.id);
    assert.equal(await page.locator('.mg-next').count(), 0);
    assert.ok(await page.locator('.mg-grade[data-quality="4"]').isEnabled());
    assert.equal(evidence.posts[0].forwarded, false);
    note('Hidden answer, private typed recall, keyboard reveal, retryable failed save');

    const held = { kind: 'hold-reply', ready: deferred(), release: deferred() };
    mode = held;
    const grade = page.locator('.mg-grade[data-quality="4"]');
    await grade.scrollIntoViewIfNeeded();
    const gradeBox = await grade.boundingBox();
    await page.mouse.click(gradeBox.x + gradeBox.width / 2, gradeBox.y + gradeBox.height / 2, { clickCount: 2 });
    await held.ready.promise;
    assert.equal(evidence.posts.length, 2, 'A double click emits only one retry request');
    assert.ok(await page.locator('.mg-grade').evaluateAll(buttons => buttons.every(button => button.disabled)));
    assert.match(await page.locator('.mg-save-status').innerText(), /Saving/);
    assert.equal(await page.locator('.mg-next').count(), 0, 'Cannot advance while save is pending');
    held.release.resolve();
    const mainResponses = [(await waitForFeedback(first)).response];
    assert.equal(mainResponses[0].accepted, true);
    const animation = await page.locator('.mg-plot-grown .mg-plant').first().evaluate(el => getComputedStyle(el).animationDuration);
    assert.ok(animation.split(',').every(part => parseFloat(part) <= 0.001), 'Reduced motion suppresses garden animation');
    await capture('memory-garden-desktop-feedback');
    await page.setViewportSize({ width: 390, height: 844 });
    await capture('memory-garden-mobile-feedback');
    await page.setViewportSize({ width: 1440, height: 1000 });
    assert.equal((await currentCard()).id, first.id, 'The card stays until explicitly advanced');
    note('One save on double click, disabled pending controls, accurate schedule, no automatic advance, reduced motion');

    for (const quality of [2, 3, 4, 5]) {
      await page.locator('.mg-next').click();
      const card = await reveal();
      await page.locator('.mg-answer h4').focus();
      await page.keyboard.press(String([2, 3, 4, 5].indexOf(quality) + 1));
      const record = await waitForFeedback(card);
      assert.equal(record.response.accepted, true);
      assert.equal(record.payload.expected_due, card.due);
      assert.equal(record.payload.expected_reviews, card.reviews || 0);
      if (quality === 2) {
        assert.equal(record.response.xp_gained, 0);
        assert.match(await page.locator('.mg-save-status').innerText(), /No XP earned/);
      }
      mainResponses.push(record.response);
    }
    await page.locator('.mg-next').click();
    await page.locator('.mg-summary').waitFor();
    const summary = await page.locator('.mg-summary strong').allTextContents();
    assert.deepEqual(summary, ['5', '4', String(mainResponses.reduce((total, response) => total + response.xp_gained, 0))]);
    await page.locator('.mg-continue').waitFor();
    await capture('memory-garden-desktop-summary');
    await page.setViewportSize({ width: 390, height: 844 });
    await capture('memory-garden-mobile-summary');
    await page.setViewportSize({ width: 1440, height: 1000 });
    assert.equal((await deck()).cards.length, 3, 'Saved cards wait for their actual next due date');
    assert.ok(sentBodies.every(body => !body.includes(privateRecall)), 'Typed recall is never sent to an API');
    await page.locator('.mg-continue').click();
    assert.match(await page.locator('.mg-start').innerText(), /3-card/);
    note('Five-card round, all four ratings, exact summary, future-card exclusion, fresh continuation');

    await page.locator('.mg-start').click();
    const lostCard = await reveal();
    mode = { kind: 'lose-reply-after-save' };
    await page.locator('.mg-grade[data-quality="4"]').click();
    await page.locator('.mg-save-error').waitFor();
    const lostResponse = evidence.posts.at(-1).response;
    assert.equal(lostResponse.accepted, true, 'Server committed before reply was lost');
    assert.ok(await page.locator('.mg-grade[data-quality="4"]').isEnabled());
    await page.locator('.mg-grade[data-quality="4"]').click();
    const replay = await waitForFeedback(lostCard);
    assert.equal(replay.response.accepted, false);
    assert.equal(replay.response.stale, true);
    assert.equal(replay.response.xp_gained, 0);
    assert.equal(replay.response.next_due, lostResponse.next_due);
    assert.match(await page.locator('.mg-save-status').innerText(), /already visited/);
    assert.match(await page.locator('.mg-earned').innerText(), /^0 XP/);
    assert.equal((await deck()).cards.length, 2);
    note('Lost committed response retries safely without duplicate credit or a new schedule');

    await openRound();
    await reveal();
    const exitHold = { kind: 'hold-reply', ready: deferred(), release: deferred() };
    mode = exitHold;
    await page.locator('.mg-grade[data-quality="4"]').click();
    await exitHold.ready.promise;
    await page.locator('.mg-leave').click();
    await page.waitForURL('**/#/today');
    await page.locator('.memory-game').waitFor({ state: 'detached' });
    await page.waitForFunction(() => document.querySelector('#page .pagehead h2') && document.activeElement?.id === 'page');
    const afterExit = await page.evaluate(() => ({ hash: location.hash, focus: document.activeElement?.id }));
    exitHold.release.resolve();
    await page.waitForTimeout(200);
    assert.equal(await page.locator('.memory-game').count(), 0);
    assert.equal(new URL(page.url()).hash, afterExit.hash);
    assert.equal(await page.evaluate(() => document.activeElement?.id), afterExit.focus, 'Late save never steals focus');
    assert.equal((await deck()).cards.length, 1);
    note('Leaving during an in-flight save prevents late UI and focus intrusion');

    // The profile response alone is varied to exercise preschool presentation.
    // The due cards, rating write and schedule still use the real server.
    evidence.presentationOverrides.push('GET /api/state: profile.stage=0, profile.age=3; no persisted profile edits');
    await page.route('**/api/state', async route => {
      const response = await route.fetch();
      const body = await response.json();
      body.profile.stage = 0; body.profile.age = 3;
      await route.fulfill({ response, json: body });
    });
    await page.addInitScript(() => {
      window.__qaSpoken = [];
      speechSynthesis.speak = utterance => { window.__qaSpoken.push(utterance.text); };
      speechSynthesis.cancel = () => {};
    });
    await openRound();
    assert.equal(await page.locator('.memory-game-young').count(), 1);
    assert.equal(await page.locator('.mg-recall-input').count(), 0);
    const youngCard = await currentCard();
    await page.getByRole('button', { name: 'Read the question aloud', exact: true }).click();
    assert.ok((await page.evaluate(() => window.__qaSpoken)).includes(youngCard.front));
    await reveal();
    await page.getByRole('button', { name: 'Read the answer aloud', exact: true }).click();
    assert.ok((await page.evaluate(() => window.__qaSpoken)).includes(youngCard.back));
    assert.equal(await page.locator('.mg-grade').count(), 2);
    assert.deepEqual(await page.locator('.mg-grade strong').allTextContents(), ['Not yet', 'I remembered']);
    await page.setViewportSize({ width: 390, height: 844 });
    await capture('memory-garden-young-mobile');
    await page.locator('.mg-grade[data-quality="2"]').click();
    const young = await waitForFeedback(youngCard);
    assert.equal(young.response.accepted, true);
    assert.equal(young.response.xp_gained, 0);
    assert.match(await page.locator('.mg-save-status').innerText(), /Not yet/);
    await page.locator('.mg-next').click();
    await page.locator('.mg-summary').waitFor();
    assert.deepEqual(await page.locator('.mg-summary strong').allTextContents(), ['1', '0', '0']);
    note('Preschool presentation: spoken prompt and answer, two self-ratings, grade 2 earns no XP');

    const finalDeck = await deck();
    assert.equal(finalDeck.cards.length, 0);
    assert.equal(finalDeck.stats.total, initial.stats.total);
    assert.ok(finalDeck.stats.next_due > Date.now() / 1000);
    evidence.finalDeck = finalDeck;
    await visit('review-game');
    await page.locator('.mg-empty').waitFor();
    assert.match(await page.locator('.mg-empty').innerText(), /Let your memories rest/);
    assert.equal(await page.locator('.mg-start').count(), 0);
    await capture('memory-garden-rest-mobile');
    note('Real empty due deck explains rest and next visit without re-queuing future cards');

    evidence.presentationOverrides.push('GET /api/review/due: no cards and total=0, solely for never-had-cards empty-state presentation');
    await page.route('**/api/review/due?*', async route => {
      const response = await route.fetch();
      const body = await response.json();
      body.cards = []; body.stats = { ...body.stats, total: 0, due: 0, next_due: null };
      await route.fulfill({ response, json: body });
    });
    await page.reload();
    await page.locator('.mg-empty').waitFor();
    assert.match(await page.locator('.mg-empty').innerText(), /garden begins with a lesson/);
    assert.equal(await page.locator('.mg-start').count(), 0);
    await capture('memory-garden-new-reader-mobile');
    note('New reader gets an actionable empty state');

    await Promise.all(sourceReads);
    for (const file of ['app.js', 'review-game.js', 'review-game.css']) {
      assert.equal(evidence.sources[file], digest(fs.readFileSync(path.resolve(__dirname, '../web', file))),
        'Browser verified current source: ' + file);
    }
    assert.deepEqual(evidence.errors, [], 'No uncaught browser JavaScript errors');
    assert.equal(evidence.posts.filter(post => post.response?.accepted === true).length, 8);
    assert.equal(evidence.posts.filter(post => post.forwarded).length, 9, 'Eight accepted writes plus one harmless stale retry');
    note('Current served source, eight accepted reviews, one stale retry, no JavaScript errors');
    fs.rmSync(path.join(out, 'failure.png'), { force: true });
    console.log('PASS ' + evidence.checks.length + ' review game scenarios; evidence in ' + out);
  } catch (error) {
    evidence.failure = error.stack;
    if (page) await page.screenshot({ path: path.join(out, 'failure.png'), fullPage: true }).catch(() => {});
    throw error;
  } finally {
    fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(evidence, null, 2));
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
