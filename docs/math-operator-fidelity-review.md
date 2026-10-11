# Operators, spectra and truncation: fidelity review

The actual `math.5.functional` lesson asks about the norm-preserving,
non-surjective unilateral shift, the reciprocal diagonal spectrum including
its non-eigenvalue limit zero, the noncompact Hilbert unit ball and Parseval
norms. The dedicated activity adds exact sparse rational calculations to these
examples alongside the existing function-projection activity. It does not
replace the lesson's other completeness, duality, Riesz or Hahn-Banach content.

## Mathematical authority

The ambient space is complex square-summable sequences; the controls select
real rational finite-support vectors. The activity distinguishes three objects:
the infinite operator, its N-dimensional matrix accepting P_N x, and the
finite-rank operator P_N T P_N acting on all of the infinite space. Their
different domains are part of the calculation. Requested, accepted, excluded,
visible and hidden terms remain separate in the exact squared-norm ledger.

For S, shifting coefficients preserves the full norm, its kernel is zero, and
its range misses e_1. The compression loses e_N, whereas the infinite operator
sends it to e_(N+1). The infinite finite-rank extension also kills every tail
input. The truncation error norm is exactly one for every N, witnessed by e_N.
The infinite shift has the closed unit disk as its spectrum and no eigenvalues;
these statements are analytical facts rather than deductions from a crop.
Outside the disk, the Neumann inverse series converges. Inside it, the adjoint
has a nonzero geometric-sequence eigenvector, so S-lambda I cannot be onto.
On the boundary, finite geometric-sequence unit probes have residual norm
sqrt(2/N), tending to zero. A zero input never qualifies as an eigenvector.

For D e_j = e_j/j, the full spectrum is {1, 1/2, 1/3, ...} plus zero. D is
injective, but D e_j tends to zero in norm while every e_j has norm one, so no
bounded inverse at zero exists. The square-summable target y_j=1/j would need
the nonsquare-summable preimage with every coordinate one. Finite-rank
approximation has exact operator-norm error 1/(N+1), supplying the compactness
argument. Shrinking distances for one displayed pair alone would not prove it.
[MIT Lecture 19](https://ocw.mit.edu/courses/18-102-introduction-to-functional-analysis-spring-2021/39ac233d5d7cbfffcdce8086143688f6_MIT18_102s21_lec19.pdf)
provides the finite-rank/compactness framework, and
[MIT Lecture 20](https://ocw.mit.edu/courses/18-102-introduction-to-functional-analysis-spring-2021/9eaaf363541d01d53c330ee7931fc715_MIT18_102s21_lec20.pdf)
provides the bounded-operator spectral framework.

The diagonal is normal, so its resolvent norm equals reciprocal distance to
its full spectrum. At lambda=2/5 with N=2, the infinite operator's nearest
point is the hidden 1/3: distance 1/15 and inverse norm 15. The compressed
diagonal's nearest point is 1/2: distance 1/10 and inverse norm 10. A finite
compressed shift may be nonnormal; the activity correctly declines to invent
its inverse norm from spectral distance.

## Verification completed at the actual lesson route

The implementation's existing Node matrix-action and Python Fraction/NumPy
checks had passed before this review continued. They were preserved. The
remaining application checks used a new isolated QA database and local server,
with an owned Chromium 151 browser context. No real learner record was used.

At both 1440 and 390 CSS pixels, 14 selected operator states and all 12 numeric
control extrema were exercised through native selects, typing and blur. Draft
clearing leaves the model unchanged; committing a blank restores that
control's default. A native ArrowUp increment was also checked. The boundary,
resolvent, tiny-nonzero and zero presets, matrix-projected tail input,
finite-rank hidden residual, and eigenvalue 1/65536 beyond the plotted spectral
prefix were checked against explicit expected ledgers. In particular,
D e_65536 retains residual squared norm 1/4294967296 at lambda zero, and has
zero residual for the exact nonzero eigenvalue 1/65536.

Enlargement produces a 660-pixel SVG with horizontal scrolling inside its
viewport; it does not widen the mobile document. Reset restores the complete
authored state and fitted plots. SVG text bounds, responsive controls, table
scrolling and absence of document overflow were checked; captured screenshots
were inspected. The served activity, stylesheet, application, speech helper
and spatial dependencies match reviewed workspace hashes. Browser errors were
empty. The isolated browser and server were closed after review; the disposable
QA database and its backups were removed, with proof and screenshots retained.

Five actual speech captures per viewport reconstruct the full expected title,
instructions, current readout, mathematical proof, orthonormal witness and
scope note exactly after whitespace normalization. The longest utterance is
1179 characters, within the shared 1200-character bound. This verifies current
text delivery and queue chunking, not acoustic pronunciation. The host offers
model speech buttons only at global reader stage 2 or lower; these captures
used global reader stage 2 on the same advanced `math.5.functional` lesson
route. The host hides the model speech button whenever global stage exceeds
2; this review does not claim a stage-5 speech button or change that policy.

Ignored route evidence and screenshots are in
`.research/operator-ensemble-qa-independent-20261011/` in the parent workspace.
These are local application checks, not authenticated-production verification
or completion of the full mathematics/physics/radiology objective.
