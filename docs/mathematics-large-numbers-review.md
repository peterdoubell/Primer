# Law of large numbers representation review

Date: 2026-10-09. The existing binomial concept model and illustration remain.
The new `math-probability-lab` activity adds persistent sample paths and finite
concentration calculations to `math.4.prob-theory`. It does not complete the
visual goal for all 59 mathematics lessons.

## Probability model and replay path

The analytical model assumes independent, identically distributed trials with
one fixed success probability p. For Bernoulli trials, p is an integer percentage
from 0 to 100. For the fair-die experiment, actual outcomes are faces 1–6 and
the plotted success indicator is 1 for a six, 0 otherwise, with p=1/6. The
Bernoulli probability control is disabled and labelled as unused in die mode.
The die's raw face average is reported separately with its own expectation and
variance; it is not confused with the six proportion.

The sample path uses seeded PCG32 pseudorandom output and rejection mapping to
bounded integers. It is a deterministic illustration of the IID model, not
proof of independence or physical randomness. Selecting a larger or smaller n
preserves the same prefix, up to the supported 8,192 trials. Changing tolerance
does not generate another path. The seed can be entered or advanced, and the
original sequence can be restored. Sample-size presets include 6,000, matching
the lesson's fair-die count/proportion question.

The PCG32 portion is adapted from Melissa O'Neill's reference implementation.
Attribution, modification notice and the Apache-2.0 license are retained in
`web/math-probability-lab.LICENSE.txt`. Original plots and probability teaching
calculations are authored for Primer. No textbook figure is reproduced.

## Exact formulas and numerical evaluation

For success count Sₙ and success proportion Sₙ/n:

    E[Sₙ] = np                  Var(Sₙ) = np(1−p)
    E[Sₙ/n] = p                 Var(Sₙ/n) = p(1−p)/n

Thus count standard deviation grows as √n and proportion standard deviation
shrinks as 1/√n when 0<p<1. Those are distributional properties, not monotonic
claims about a particular count deviation or proportion error. At p=0 or p=1,
the outcomes and count are deterministic and both variances are zero.

The finite-n error event is inclusive:

    |Sₙ/n − p| ≥ ε.

Its probability is calculated by summing the binomial PMF. The PMF is computed
from a central mode using log recurrences and a compensated normalization sum;
no normal approximation is used. Event membership uses integer cross-products
for the exposed rational p and epsilon percentages, avoiding floating-point
misclassification of outcomes exactly on the boundary. Machine-evaluated values
are rounded for display; the algebraic formulas are exact under the stated model.

Positive tail probabilities that underflow in an ordinary binary64 scalar retain
their finite log probability and are displayed in scientific notation. For
n=8,192, p=1/2 and ε=1/2, the event consists of the all-failure and all-success
outcomes, so its exact probability is 2^(1−8192), about 1.8336 × 10^−2466. The
activity displays this positive value rather than calling it impossible. Only
genuinely impossible model events are displayed as zero.

The companion Chebyshev bound is min(1, p(1−p)/(nε²)). For every fixed ε>0
it tends to zero as n increases, establishing the weak-law statement for this
model. A displayed finite path is not offered as a proof of the infinite limit.

## Visual meaning

The three linked plots show the running success proportion, signed count
deviation Sₖ−kp, and model concentration at selected integer sample sizes. The
proportion plot keeps a fixed 0–1 scale and a labelled ±ε error band. The count
plot fits the selected prefix and explicitly states that its changing axis labels
must be read in count units. Its gold ±1-SD curves are not confidence intervals
or guaranteed boundaries for a path.

The concentration plot uses labelled log₂ sample-size and log₁₀ probability
axes. Blue points come from binomial tail sums; gold points are the Chebyshev
bound. Joining lines are visual guides between calculated sizes. The exact
finite-n tail can oscillate because possible success counts are integers. A
zero tail is not placed at a fabricated finite logarithm: the deterministic
endpoint cases use an explanatory panel.

The last twenty included outcomes remain individually inspectable with trial
numbers and success meaning in their accessible labels. All plots use a full
light background so signed ticks and axis labels remain readable in the dark
application theme. Enlargement scrolls inside each plot's own viewport.

## Verification and limits

`tools/check_math_probability_lab.js` verifies the published PCG32 test vector,
56 binomial distributions and 210 concentration states. Small-n PMFs are also
checked by enumerating every binary outcome sequence. It checks moments, total
mass, the bound, rational boundary ties, rare-event log values, persistent
prefixes, both endpoint laws and fair-die outcomes. Fourteen mounted control
states, sample-size presets, seed replay, enlargement and reset exercise the
actual renderer and plotted coordinates. A seed-1 replay includes a sample
proportion that enters and then leaves its tolerance band; one standard deviation
is also exceeded. Those checks prevent misleading path guarantees.

`tests/test_math_probability_lab.py` runs the JavaScript checks and compares
24 PMF cases and 75 finite-n tail sums against independent SciPy calculations,
including n=6,000 and n=8,192, p=0.01, p=1/6, p=0.5 and p=0.99. The license
notice is also verified. All four focused tests passed in the available Python
3.12 verification environment.

Desktop and 390px browser review inspected the actual plots and controls. It
verified that extending 10 to 100 trials keeps the earlier plotted points; the
6,000-die example reports 992 sixes with count SD about 28.87; the 8,192-trial
rare tail remains positive in the readout; p=0 and p=1 produce deterministic
outcomes; and advancing seed 9,999 wraps to 0. The phone page stays 390px wide,
with enlarged 660px plots inside 324px scrolling containers. Source curves and
the numerical values are verified; this is not a validation of all possible
browser states or audio pronunciation. Local review evidence is retained in
the ignored `.research/math-probability-preview` directory.

This covers bounded IID indicators and a fair-die example. It does not model
arbitrary dependence, nonidentical trials, arbitrary random-variable laws,
infinite-variance examples or every probability topic in the lesson. The full
mathematics fidelity goal remains open.

Primary references: [MIT 18.440, Chebyshev and the weak law](https://ocw.mit.edu/courses/18-440-probability-and-random-variables-spring-2014/9adbf88f8a8b456963d6299ea683e954_MIT18_440S14_Lecture30.pdf)
and [PCG's reproducible generator and bounded integer mapping](https://www.pcg-random.org/using-pcg-c-basic.html).

Actual integrated-route review also passed at `#/node/math.4.prob-theory`,
with the original binomial model retained. Browser interactions verified seed
replay, prefix extension, die n=6,000, p=0/p=1 and the positive rare tail. The
activity's native speech callback preserved complete decimal and scientific
tokens after the shared speech-splitting fix; audio pronunciation was not tested.
Desktop/dark and 390px views, internal 660px enlargement and reset passed with
no captured exceptions. Served helper, stylesheet, renderer and app hashes
matched reviewed files. Proof is local in `.research/math-probability-integrated-review`.
