# Radiation pulse-counting bench

Lesson: `phys.3.nuclear` (Atoms and Nuclei). Entry:
`/app/physics/radiation-counter/index.html`.

The existing lesson's Radioactive Ensemble Lab follows surviving nuclei. This
activity adds an instrument between interactions and the reported count: explicit
recovery intervals, lost events, a live-time clock, and repeated finite gates.
Changing recovery time reprocesses the same seeded interaction stream. Repeating
the gate comparison uses a new batch seed so successive batches are fresh.

## Physical model and source

The primary source is Pommé, Keightley and Fitzgerald, *Uncertainty of nuclear
counting*, Metrologia **52** (2015), S3–S17,
[doi:10.1088/0026-1394/52/3/S3](https://doi.org/10.1088/0026-1394/52/3/S3).
The [NIST publication record](https://www.nist.gov/publications/uncertainty-nuclear-counting)
provides the open paper. Its non-extendable throughput equation and renewal
interval treatment inform the model. The equations, instrument schematic and
implementation here were authored for Primer; no source figures were copied.

The interaction stream is homogeneous Poisson. Each recorded interaction starts
a fixed, non-extendable dead interval; a lost interaction does not restart that
interval. All gates start live, use `[0, T)`, and hold their settings constant.
The nth recorded-event time is a gamma waiting time plus `(n−1)τ`. The gamma CDF
therefore gives the exact finite-gate count tails. Numerical truncation at tail
probability `1e-13` supplies the displayed count distribution and its moments.
The initial live wait is included explicitly, rather than approximating the
finite-gate mean by the stationary rate times the gate length.

For λ = 5000 interactions/s, τ = 200 µs and T = 100 ms, the stationary output rate
is 2500/s. The finite-gate expected count is 250.125, standard deviation
7.9132668138, and variance/mean about 0.250354. Removing recovery yields Poisson
counts with variance equal to their mean. An entire gate shorter than τ has
only zero or one recorded interaction, giving a Bernoulli limit.

This is an idealised counting chain, with simulated events. Input rate describes
interactions at the chain and already includes detection efficiency/geometry;
it does not infer source activity, dose, radiation energy or a specific GM tube's
response. Gas avalanches, pulse-height response, pileup and extendable dead time
are outside the model. These assumptions are visible in the activity.

## Verification

`node --test tests/radiation-counter.test.mjs` checks lost-pulse recovery,
acceptance at the recovery boundary, clipping at the gate boundary, seeded-stream
identity, all zero-input paths, Poisson and Bernoulli limits, saturation and
independent repeated-gate statistics. The committed reference fixture was
computed independently with SciPy 1.15.3: 14 settings and 66 gamma-tail probes,
including 40000 expected incoming interactions and short-gate boundaries.

`pytest -q tests/test_radiation_counter.py tests/test_lesson_activities.py tests/test_learning_games.py`
passed all 25 tests. The reader-links inventory remained unchanged; the coverage
report changed only the nuclear lesson's existing-activities column.

The actual authenticated application server passed normal lesson → activity →
lesson navigation at 1200 px and 390 px, with the existing inline lab retained.
Browser checks covered same-stream recovery removal, a fresh repeated batch,
zero rate, high-rate 2-second gates, keyboard controls, a selected interaction
inside a 1-ms window at the end of a 2-second gate, and worker cancellation.
There were no page errors, CSP violations or horizontal overflow. All five
activity responses matched the authored bytes, including JavaScript MIME for
`.mjs` and the module worker under the real server CSP. The runner used its own
temporary local database and synthetic account, with no application asset
substitutions or remote writes.

Reproducible reader/source scripts, JSON receipt and screenshots from this local
verification are retained in `/tmp/primer-radiation-counter-qa/`. Scientific tests
and independent reference values are committed with the activity.
