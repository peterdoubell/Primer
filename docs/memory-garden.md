# Memory Garden

Open **Review → Play Memory Garden**, or use `#/review-game`. The classic
review deck remains available.

Choose a round of up to five or ten due cards. Recall an answer before revealing
it, then compare and rate your own recall. Older learners can write an optional
answer locally; younger learners have read-aloud controls and two larger rating
buttons. The game does not automatically mark free-text answers correct.

Each saved review updates the existing spaced-repetition schedule. Successful
recall grows a flower; a missed answer waters a sprout for another visit.
Feedback shows the exact next scheduled date and time, and the round summary
shows saved reviews, flowers and the XP actually returned by the server.
Finishing a round offers a stopping point. Continuing fetches cards that are
currently due, so recently missed cards wait for their scheduled return.

Empty gardens explain how to create a deck through learning. A deck with no
due cards shows when the next memory returns. Leaving a round retains every
saved review; unfinished cards remain available. The decorative garden and
round totals belong to the current round, while the card schedule, mastery and
earned XP persist in the existing reader record.

## Implementation

- `web/review-game.js` and `web/review-game.css` implement the game within the
  existing book interface, with local SVG plant drawings and theme tokens.
- `/api/review/due` supplies interleaved due cards and the existing review goal.
  Queue requests are bounded to 1–50 cards.
- `/api/review/game` accepts `card_id`, `quality`, optional `seconds`, and the
  displayed card's `expected_due` and `expected_reviews` revision fields.
- The store first checks the revision, then performs a conditional SQL update
  scoped to that reader and revision before recording mastery effects or review
  events. A stale submission returns `accepted: false`, zero XP and the actual
  schedule. This protects failures as well as successes when a response is lost
  or another tab reviews the same card.
- The original review API keeps its existing early-review behavior. The game
  uses the same scheduling algorithm, age-specific intervals, XP limits and
  rules for repeatedly missed cards; it adds no independent mastery system.
- `next_due` exposes the exact scheduled Unix timestamp. `next_days` remains
  available for existing clients.

The UI prevents overlapping submissions, keeps failed saves retryable, checks
the response body as well as its HTTP status, and ignores late responses after
navigation. Typed recall text is never submitted. Keyboard controls, readable
status announcements, large touch targets and reduced-motion behavior are
provided throughout.

## Verification

`tests/test_review_game.py` covers guarded success/failure retries, forced
concurrent stale reads on separate SQLite connections, exact schedules,
age-specific intervals, XP limits, difficult-card parking, cross-reader and
expired-session isolation, and request validation. Existing review and mastery
regressions remain in place.

`tools/check_review_game_browser.cjs` exercises the actual game and API on an
explicitly disposable local reader, including a lost committed response and a
retry, double clicks, navigation during saving, keyboard/mobile interactions,
younger-reader presentation, and an exhausted due deck. Its starting fixture is
an adult reader with pronouns configured, eight due cards and one future card.
Screenshots and results are saved under `artifacts/memory-game/`.

Verified on 2026-09-24: 639 Python regressions passed with one existing skip,
including all 33 game API/store tests. The final browser run passed ten
scenarios with zero JavaScript errors. Its database contained exactly eight
reviews and eight events for the eight tested cards; the future card was
unchanged despite a failed request and a retry after a lost committed response.
Young-reader presentation was exercised with a profile-response override;
young-reader scheduling intervals were tested against the real store.
