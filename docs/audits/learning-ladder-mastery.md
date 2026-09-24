# Independent Mastery, Placement & Pacing audit

Frozen tree: cc238d81dc375694718746d479b86c062d1f8f95, extracted at /tmp/primer-audit-mastery-cc238d81. No live learner database opened, copied or changed. All server imports used explicit /tmp PRIMER_DB. Audit is independent and read-only against the extraction.

Score: **7.5/10** on this frozen tree. The central placement policy is substantially stronger; the remaining gap is credible evidence and honest measurement, not a reproduced catastrophic promotion/demotion.

Three biggest reasons not higher:

1. Two claimed earned-progression regressions fail in the shipped tests. `tests/test_end_to_end_progression.py:497` ages first_pass_at only, while the three-pass implementation now uses last_pass_at. Running just the two relevant tests gave **2 failed in 20.53s**: line 517 has earned=0, and line 542 has before=1/after=1 with placed math=0. This is a broken test fixture, not proof the product cannot ascend. But the assurance that genuinely earned progression and recovery were exercised is not currently reproducible. Replace SQL manipulation with an advancing clock, account for burn windows, and show real submitted papers confer mastery and promotion.

2. The pace label claims completed-article speed from longest visits. With the real store and HTTP, twenty assigned articles each receiving two five-minute visits (forty logged opens, 200 minutes) yield measured=true, minutes=100, per_article=5, factor=.833. `primer/learner.py:2221` intentionally keeps the maximum per title; `web/app.js:4435` turns that into "You read ... minutes an article." Continued reading and rereading are indistinguishable. The correction now scales only assigned reading, which contains harm, but the measurement should say longest observed visits and disclose continuation underestimation.

3. Validation remains policy/fixture evidence rather than a demonstrated complete learner trajectory. The 23,328-state test checks the chosen function's inequalities, not server placement histories or ascension/gate changes. Existing ascension tests bypass locks. The real HTTP cases and real curriculum are valuable, but they do not establish external calibration of six-minute articles, stage-node time estimates, or long-term recovery across a whole ladder. These are limits to claims, not requests for another massive unit suite.

Reproduced/checked:
- Source confirms one downward rung cap, direct upward movement to target, own-result non-demotion, general median floor 2 when any general result is at least 4, and specialist exclusion.
- Real-store age-five spacing probe at days 0, 2, 4 records passes 1, 2, 3; mastery only on the third pass. No synthetic mastery dictionary.
- Adversarial specialist self-open via HTTP gives 21 assumed prerequisites. For selected biology/physics/math, all real domain estimates remain 0, proven count is 0, and calling ascension returns None. The unused proven variable in ascension is **not itself a reproduced defect**.
- Clock source has independent paper/tab/picture/tutor holds, with longest-duration idempotence. Browser execution of these nested states is outside this audit's independent evidence; do not substitute source inspection for that check.
- Focused progression/pacing run includes real HTTP high-math/four-weak-fields and exhaustive transition test; final result to be appended when complete.

Claims not reproduced: the two earned-stage tests above fail before demonstrating their intended invariant. No claim of exhaustive HTTP histories or externally validated mastery/reading calibration is supported. The historical assertion that a tiny preschool pass can undo weak-field placement was investigated in current code and not independently reproduced.

For 8: repair and rerun the genuine-time earned-promotion/recovery cases; make reading-visit language match observed data; retain the current bounded reading-only pacing adjustment; confirm map/node/quiz graduate gates agree, and complete the independent browser hold checks. An 8 would mean robust implementation with candid measurement limits, not proof that its educational time model has been validated on humans.

Independent recovery probe: without changing frozen files, replaced `_prove` in the test module at runtime with real wall-clock advances of eight days between HTTP sittings (and disabled unrelated wiki summary fetching). Both failing tests then PASS. Earned-first-placement scenario ends stage 1 with history=0; recovery ends stage 2 with math=0. Each has eight currently proven nodes after the long trajectory (earlier evidence decays). This supports a fixture regression, not an ascension-product defect, and materially strengthens the conditional path to 8.

Final focused run: **32 passed, 2 failed in 318.33 seconds**. Included both policy/HTTP tests from test_loop_ladder_contract, all test_end_to_end_progression cases, and test_measured_pacing. Only failures are the two spacing-fixture failures documented above. Thus the 23,328 transitions, high-maths/four-low-fields HTTP sequence, graduate map/node/quiz agreement, reading persistence, pacing bounds and existing placement recovery cases passed. The combined run emitted backup warnings/errors against temporary test databases during clock-shifting fixtures; the isolated two-test run reproduced both same assertion failures without those errors. No live backup was touched; backup behavior was not independently diagnosed in this mastery audit.

## Candidate recheck — tree 9031ee70447222574a2a86634a1a24adeb26edbc

Read-only extraction /tmp/primer-candidate-9031ee70. The new `_prove_nodes` moves the shared server/store wall clock across three days instead of editing a single SQL timestamp. The two formerly failing earned-promotion/recovery cases now pass independently. Pricing copy now says "longest reading visits", says visits do not establish completion, and explicitly warns that returning to finish can make the estimate too short. This resolves the reported overclaim without pretending to infer missing completion data.

Revised independent score: **8.0/10**, based on the bounded implementation, corrected tests and honest measurement scope. This is not an externally calibrated educational effectiveness score. Reasons not higher: (1) no external validation of the time model; (2) observation cannot distinguish completed reading, continuation and rereading; (3) earned progression tests still isolate mastery policy by bypassing node locks, so they do not demonstrate the whole no-shortcuts curriculum journey. These are substantive limits, now exposed rather than concealed. Nested browser hold execution remains the root agent's separate verification and is not claimed as an independently executed part of this audit.

Candidate focused recheck completed: **4 passed in 56.03 seconds** — earned-first-placement protection, demoted-reader mastery recovery, graduate map/node/quiz agreement, and all 23,328 stage-policy transitions. No extraction files modified. Awaiting final-commit identity check only.

Lifecycle follow-up (working candidate, final pin pending): independently inspected `_maintenance_loop` and `_lifespan`. The outer stop check prevents repetition if shutdown arrives inside the backup, each lifespan has a distinct Event, and finally sets it on exceptional exit. Direct regression test passes (1 passed, 1.42 seconds). A separate overlapping-lifespan probe confirms closing one lifespan stops only its worker; exceptional exit stops the second. The two-second join is intentionally bounded: a slow in-flight backup can outlive lifespan exit, but it will stop at the next outer-loop check; this is not a guarantee that every backup completes before process termination. No change to mastery score.

## Final immutable pin

Final implementation commit **b3e1533**, exact tree **a97009117654ddff83725e14bf330a9eced22944**, inspected at `/tmp/primer-final-code-a9700911`.

Bounded comparison against the independently rechecked 9031ee70 candidate confirms no further placement/ascension changes. Curriculum and story implementation and web/app.js are unchanged; pacing changes only correct a comment to say that the rate scales article reading. Server adds the independently verified lifecycle stop fix and widens question selection when initial prompts duplicate. Learner burns review exposure on failed recall only, consistent with the existing quiz exposure policy. No new mastery or pacing discrepancy found. Fixture/comment corrections do not weaken the observed earned-promotion/recovery evidence.

**Final independent score: 8.0/10, pinned to the tree and commit above.** Previous limitations remain: the time model is not externally calibrated, longest reading visits cannot establish completion, and isolated progression regressions are not a complete human curriculum trial. Full-suite result of 1,629 passed / 3 skipped is reported by the root agent, not rerun by this auditor. No additional tests were necessary for this final bounded comparison.
