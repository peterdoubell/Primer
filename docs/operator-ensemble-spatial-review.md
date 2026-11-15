# Independent operator and ensemble spatial review

The new authored families replace generic study contexts on the actual
`math.5.functional` and `phys.4.statmech` lesson routes with quantitative graphs.
Their coordinate meanings and scope are explicit; they are not physical
particle chambers or an isometric embedding of infinite sequence space.

## Independent coordinate and ledger oracles

`tools/check_operator_ensemble_spatial.js` loads the fixed shipped modules
through CommonJS. Expected operator values come from a separate reduced
BigInt-rational implementation and explicit matrix multiplication, without
calling the numerical activity to obtain expected values. A sufficiently
large input window retains every nonzero requested/output/residual term; it
does not approximate the spectrum by that window.

For each visible j, the operator point must be
`(j/N, accepted x_j, (Tx)_j)`. Its two-step stem passes through
`(j/N,0,0)` and `(j/N,x_j,0)` to that point. Coefficients retain their actual
dimensionless values and signs; the dot's fixed radius is a display aid.
Full norms sum all squared rational coefficients, while the visible and hidden
parts split exactly at N. Matrix inputs are projected; finite-rank inputs
retain their tail and hence the tail of `Tx-lambda x`.

The checker passes 1080 operator states spanning both operators, all three
realizations, N=1/2/4/32, first/boundary/tail positions, signed/two-coordinate
and zero inputs, and all three spectral probes. It checks each actual sphere,
stem and metadata value against the independent matrix action. Exact ledgers,
zero-input/eigenvector distinctions, full reciprocal spectra including zero,
hidden nearest points, and the analytic all-N truncation-error values are
checked. For the 2-by-2 shift at lambda=2/5, the inverse matrix is
`[[-5/2,0],[-25/4,-5/2]]`; its singular norm is
`sqrt((825+sqrt(640625))/32)`, exceeding reciprocal spectral distance 5/2.
The shipped metadata correctly leaves this nonnormal inverse norm unevaluated.

The canonical e_N fixture intentionally has identical visible coefficient
geometry when its domain or spectral probe changes. Its hidden output and
residual ledger nevertheless changes. The generic family checker now preserves
that invariance. To test visible dependence of the next coefficient, it uses
an explicitly interior `position:first` fixture rather than inventing a point
outside the displayed crop. Its boundary fixture also verifies the hidden
coefficient norm. No product runtime change was required.

Ensemble expected counts come from independent Pascal rows. For independent
sites with two distinct labeled states, `Omega_j=C(N,j)` and
`ln P(j)=ln Omega_j-j*x-N*ln(1+exp(-x))`, where `x=DeltaE/(k_B*T)`.
At a positive gap the energies are distinct. At x=0 the two states remain
distinct but share the same energy; they are not two nondegenerate energy
levels. Both populations are then 1/2, and all 2^N labeled microstates are
equiprobable. The plotted point must be `(j/N, ln Omega_j/N, -ln P(j)/N)`. Thus multiplicity
plus surprisal equals `ln 2` for fair coins, and `(j/N)*x+ln Z_1` for canonical
sites. The full Gibbs entropy equals count-distribution entropy plus expected
conditional multiplicity entropy; the selected `ln Omega_j` is not the
entropy of the entire ensemble. The
[MIT equilibrium-statistical-mechanics notes](https://www.mit.edu/~jgt/Content-Web/Teaching/8333/Chapter-3.pdf)
provide the canonical weighting and two-level partition-function framework.

The checker passes 252 ensemble states: both modes; N=1/2/3/4/8/16/32;
x=0/0.25/1/2/10/20; and endpoint/middle selections. Every macrostate sphere,
stem, exact integer count and log-probability coordinate is checked. The
macrostate probabilities normalize; the entropy decomposition holds. Positive
finite probabilities retain finite positive surprisals at the extreme gap.
Changing a canonical gap assigns no energy to fair coins and leaves their
graph unchanged. Highlights and dot sizes indicate selection rather than
probability or entropy volume. Neither ensemble weights nor these pictures
supply recurrence times or molecular dynamics.

## Application controls and delivery

The dedicated pytest file passes three tests, including strict actual authored
bindings and rejection of the old generic particle family. The generic family
checker also passes after the semantic-control correction; its build count is
not a completeness claim.

Actual lesson browser checks at 1440 and 390 CSS pixels exercise all choice
options and native Home/End extrema for the range inputs. Per viewport the
operator graph receives 15 recorded states, six range endpoints and three
speech captures; the ensemble graph receives seven recorded states, four
endpoints and four final speech captures. These include domain-only/hidden-residual
changes, N=32 with x=20, and fair coins with the canonical gap left large.
Keyboard rotation/Home, camera buttons, reset view and exact reset model
were checked. Speech reconstructs the current graph's title, instructions,
readout and scope note with no omitted chunks. These actual captures use
global reader stage 2 on the same advanced lesson routes
`math.5.functional` and `phys.4.statmech`. The host hides model speech buttons
for global stage greater than 2; this is an existing host policy, not an
activity-specific speech failure or a claim that stage-5 speakers are present.

SVG labels remain within their viewboxes and the document does not overflow.
Viewport captures were inspected with each graph fully below the sticky
application header. Auto-fit may make narrow features small at extreme gaps;
it does not alter their world coordinates or analytic readout. Both current
API bindings and the served JavaScript/speech dependency hashes match the
reviewed files. There were no browser errors. All checks used an isolated
database, local server and owned browser; the server/browser were closed and
the disposable database/backups removed after proof capture.

No unresolved quantitative or interaction defect was found in these two
bounded graph families. The runtime ensemble scope sentence now explicitly
distinguishes positive-gap energies from the two labeled states sharing one
energy at x=0. The final desktop/mobile speech refresh covers a positive gap,
the canonical tail, zero gap and fair coins. Every refreshed capture
reconstructs the current text exactly; the longest utterance is 1179 characters.
The served spatial helper matches workspace SHA-256
`30fcee036134cc105511835424e7e96d177f5da50e717fe997ab8a79f68567d1`.
Quantities, controls and plotted geometry did not change with this wording
correction. The
operator theorem arguments and wider ensemble/free-expansion/block domains
belong to their associated activities. Production delivery, other functional
analysis/statistical mechanics requirements and the full curriculum goal
remain outside this completed graph review.
