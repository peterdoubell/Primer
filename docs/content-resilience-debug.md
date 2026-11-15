# Content resilience debug — 24 September 2026

## Fixes

- Local lesson APIs use cache-only article summaries. Opening a lesson no
  longer waits for up to six remote Wikipedia summaries and their fallbacks.
  Missing/corrupt optional metadata leaves the local lesson and media intact.
- Temporary upstream 5xx failures join the existing network/429/503 backoff.
- Image proxy responses need a nonempty body and an explicit image MIME type;
  invalid cached entries can recover instead of remaining broken photos.
- Per the user's clarification, the familiar “DON’T PANIC” banner remains for
  genuine failures. The objective is fixing those failures, not hiding them.
  Error cards retain factual explanations and retries without unfounded
  saved-data promises or guesses about the cause.
- Responsive images try their other authored source before showing a failure.
  The former image-shaped placeholder is replaced by a compact textual retry
  control, preserving captions and descriptions. Successful retries restore the
  actual image. Decorative failures leave no broken-image box.
- The enlarged viewer can fall back to the already-loaded image when its larger
  source fails. Article retry rebuilds the route instead of adding a second reader.
- Corrected the ultrasound key diagram's source to the existing 1600-pixel asset,
  matching its dimensions and providing genuinely readable enlarged detail.

No clinical image was invented or substituted for a missing case. External
providers can still fail later; the recovery state is honest and actionable,
not a claim that the entire internet will always be available.

## Verification

- 933 distinct local images exist and decode; all 444 lessons have illustrations.
- All 432 distinct external radiology image URLs returned image responses in
  the live audit. This is point-in-time availability, not a permanent guarantee.
- All 136 reporting-reference pages passed real browser checks, with 500 images
  decoded/displayed and all 34 model families responding to interaction. No
  page exceptions, placeholders or failed image requests were observed.
- All 444 local lesson APIs returned successfully. The final browser run's
  maximum observed API latency was 47 ms; this is a local measurement, not an SLA.
- 101 lesson browser routes passed. Injected failures verified image retry,
  alternate-resolution recovery, enlarged-view fallback, page retry, and reader
  retry without duplicate readers. No JavaScript exceptions occurred.
- The gallery displayed 1,581 entries without error cards/placeholders. The live
  Genetics article returned HTTP 200, and reader retry displayed it successfully.
- Full suite: 32,071 passed, two skipped. A subsequent one-line reader-retry fix
  was covered by the final injected-failure browser run and 470 passing focused
  tests (one skipped).
- JavaScript syntax and Git whitespace checks passed.

Reproduce the browser regression check against an isolated, onboarded local
QA server with `node tools/check_content_resilience.cjs URL`
and Playwright available on the Node module path. The test is restricted to
loopback addresses and does not create a learner profile.

Changes are in the existing working tree; prior unrelated/unmerged changes were
preserved. The refreshed preview is local only; no merge or deployment was made.

Browser QA now prints a generated `EVIDENCE_DIRECTORY` for each run; see [browser-qa.md](browser-qa.md).
