# Linear algebra: exact maps, spaces and repeated action

The new companion for `math.4.linalg` connects the authored lesson's ten quizzes and matrix practice to actual calculations and geometry. It supplements the existing five-map planar activity and its illustration. Shared lesson integration, the narrowly reviewed quiz8 wording change, historical compatibility are recorded separately under `integration/`; authenticated-reader evidence is under `reader/`.

`coverage.json` maps all seven audited concept groups, every quiz index and both matrix-practice forms to implemented activities and evidence. This is a bounded implementation of the authored material; linked external articles were not exhaustively reviewed, and neither module nor whole-Primer completeness is certified.

| Activity | Concrete learning represented |
|---|---|
| Columns, area and composition | Editable rational A/B matrices; actual column combinations and transformed square; determinant5 example; both AB and BA with their different action order. |
| Two equations | The exact k-dependent system, both inconsistent singular cases, a separately labelled consistent singular comparison, free-coordinate solutions and distant near-singular intersections. |
| Three constraint planes | Actual affine-plane polygons with unique point, common line, common plane, pairwise crossings without a common point, and parallel inconsistency. Exact ranks and residuals drive the geometry. |
| 3D span and volume | A(t) with determinant3t, repeated nonzero columns, rank-one and zero maps; true source/world cube corners, column bases, image plane/line/point and face-on/edge-on camera controls. |
| Four-coordinate maps | 4×4 and rectangular3×4/2×4 maps, explicit kernel families, all four input coordinates, all actual output coordinates and full-coordinate norms. Bars show coordinate values, not fictitious4D space. |
| Spectrum | Exact representative spectra3/5,2/3/5 and1/2/4; scalar/vector distinction; identity versus defective shear; trace/product and multiplicity; an explicitly separate exact quarter-turn complex contrast. |
| Repeated action | Every indexed point of Aⁿv, eigenvalue4 at n3, nonnormal transient growth, exceptional fast/slow/zero starts, late decay and rotation/reflection. No hidden normalization. |

## Exact calculation and drawing boundaries

The numeric API accepts matrices with one to four rows and columns. Inputs are integers, decimal/scientific strings or fractions, with absolute value at most10⁶ and reduced denominator at most10¹². BigInt rational arithmetic determines matrix products, powers, row reduction, rank, column/kernel/left-kernel bases, determinants, consistency and particular solutions. Rank decisions use exact zero, not a tolerance. A4×4 augmented system retains its fifth right-hand-side column internally. Derived fractions are not forced back into the input bounds.

The column-space basis uses original pivot columns. Kernel bases use canonical free coordinates equal to one. Thus a sign/scaling difference from another valid basis is not a different null space. The3D column family preserves rank three at nonzero rational neighbours of zero even when an orthographic projection looks flat. Constraint-plane vertices satisfy their equations exactly; numerical angles order the convex polygon for drawing. The sampled polygon is a finite portion of an infinite plane. An affine plane that excludes the origin is not presented as a linear subspace.

Camera trigonometry, SVG projection, rounded decimal tick labels and square-root norms are numerical approximations. Every plotted primitive records its world coordinates and projection domain alongside the real SVG attributes. A leading `≈` explicitly marks an abbreviated coordinate. Full exact input/output, solution and squared-norm ledgers remain accessible; nominally exact tables never substitute abbreviated values. The4×4 determinant is described as4D volume scaling, not as the area scaling of every plane.

The general rational API does not solve arbitrary spectra. The spectral activity uses listed exact real families plus the quarter-turn `[[0,−1],[1,0]]`, whose eigenvalues are±i. Its complex eigenvectors are displayed algebraically and are not drawn as real eigenlines. Identity and defective shear demonstrate why repeated eigenvalues alone do not decide diagonalizability. The reflection-squared identity example prevents the invalid converse that A and Aⁿ must have identical eigendirection sets.

For `[[1/2,10],[0,9/10]]` and initial `(0,1)`, exact repeated multiplication gives `(25((9/10)ⁿ−(1/2)ⁿ),(9/10)ⁿ)`. The displayed norm initially grows, peaking at n3 for this example, before decaying. A fast-only start stays in the fast eigendirection. The text separately states the eigenbasis argument for convergence; a finite plotted trace is not the proof.

Every orbit point remains at its true coordinates. Only the selected final point is visibly labelled to prevent collisions. Exact repeats may share a compact index label, such as `n=0–4`; equality is determined from canonical rational vectors. Nearby but distinct tail/growth points are never grouped as mathematically equal. Every point has its exact iteration/coordinate tooltip and accessible label, and the complete exact table retains every iteration.

## Renderer contract and access

`api-contract.json` records the full contract. The entry point is `PrimerLinearAlgebraLab.render(item,hooks,frame)`, with exact props `{scenario:'math.4.linalg'}` and a returned `frame.root`. Standalone mounting is also supported. Other scenarios and extra props return null.

The root is `[data-linalg-lab]`; `root.linalg.getState()`, `getModels()` and `reset()` expose copies of the current state/results. Seven station values are `maps`, `systems`, `planes`, `space`, `kernel`, `spectrum`, `orbits`. Controls, presets, panels and SVGs use stable `data-linalg-*` attributes. Native text controls accept rational input; native range controls drive cameras/iteration count. Free-coordinate and camera controls are disabled when they do not apply. Invalid states remove stale plots, expose an error and allow recovery.

Default plots fit the viewport with declared responsive projection domains. Enlargement creates a keyboard-scrollable900px view without horizontal document overflow. Exact tables wrap long fractions. Marked spoken paragraphs include current state, including all four kernel input coordinates and every actual output coordinate; read-aloud integration is checked in the actual reader.

## Verification

- `tools/check_linear_algebra_core.cjs` compares against independent minor determinants/rank, exact dot products, residuals and authored rational benchmarks. It checks rectangular dimensions,4×4 augmented systems, singular families, all prescribed spectra, powers, true plane polygons and rejected domains. `core-proof.json` pins the actual source.
- `tools/check_linear_algebra_browser.cjs` mounts the actual renderer with production styles at390/1440px. It reads actual SVG/world coordinates, verifies projection/calibration and equation residuals, exercises presets/kinds/enabled controls, tests invalid recovery, enlargement/keyboard scrolling, speech state, exact fractions and coincident/dense orbit labels. `browser/proof.json` records the final bounded run and screenshots.
- `independent-review/` contains separately authored Fraction/minor/RREF/power and actual-render evidence. It is distinct from the implementation's checks.
- `integration/` contains exact shared-change compatibility. `reader/` contains actual authenticated-reader evidence, including preservation of the older activity and source contexts.

The reviewer findings about4D determinant terminology, spoken four-coordinate state, overlapping orbit labels and misleading “exact” wording on abbreviated values are resolved in the implementation. Test counts describe the checked cases; they are not a completeness denominator.

Original examples, code and SVG artwork were written for this workbench. Primary mathematical references are [MIT's four subspaces](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/pages/ax-b-and-the-four-subspaces/the-four-fundamental-subspaces/), [basis and dimension](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/pages/ax-b-and-the-four-subspaces/independence-basis-and-dimension/), [determinants and volume](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/pages/least-squares-determinants-and-eigenvalues/cramers-rule-inverse-matrix-and-volume/), and [diagonalization/powers](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/d05795355f5cbe35356a4a1b39658336_MIT18_06SCF11_Ses2.9sum.pdf). No course prose or figures were copied. The limitations in `primary-sources.json` remain explicit.
