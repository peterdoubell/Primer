# Abstract algebra fidelity review — 11 October 2026

The authored math.5.abstract lesson now has an eight-station exact algebra lab. This review concerns this lesson and its standalone runtime. It does not establish that all mathematics modules, the deployed reader, or any clinical modules are complete.

The runtime is web/math-algebra-lab.js, with scoped styles in web/math-algebra-lab.css. The renderer is math-algebra-lab; its only accepted prop is scenario: "math.5.abstract.groups-rings-fields". The parent integration owns curriculum, registration, shared state, and coordinated spatial rendering. The exported browser API is PrimerMathAlgebraLab; CommonJS exposes the same frozen API.

## Assessment coverage and mathematical model

| Station | Structures and calculations | Authored assessment |
| --- | --- | --- |
| A1 | All nine operation entries and all 27 associativity triples on three elements; every two-sided identity and inverse candidate; editable base-three operation code. Maximum and modular subtraction are counterexamples. Separate quantified proofs cover positive integers, integers, and rationals under addition. | Q1 |
| A2 | Exact cyclic groups C₂ through C₂₀ and the Klein group; complete element orders, generated subgroups, every subgroup for these families, inverses, and complete coset partitions. | Q2, Q5, Q6 |
| A3 | Every one of the 24 permutations of four letters, actual composition and powers, disjoint cycles, all six elements of order four. Composition σ∘τ means τ acts first. | Q8 |
| A4 | Full modular multiplication tables, units, nonzero zero divisors, multiplication kernels and images, every ideal of the selected modular ring, and the prime-field criterion. The ring axioms descend from the integer laws. | Q3, Q9 |
| A5 | Exact integer map f(n)=kn, kernel/image/inverse-on-image distinction, integer coordinates, negative and zero multipliers, infinite element orders, and the proof that every subgroup of ℤ is dℤ. Equal targets are one node; k=0 visibly collapses the samples. | Q7 |
| A6 | Both Sylow divisibility/congruence constraints, seven universal proof steps, explicit commutator and intersection arguments, prime-order generators, all 15 CRT pairs, inverse CRT map and product-preserving arrows. | Q4 |
| A7 | Complete S₃ or C₁₂ operation, left/right cosets, every conjugate, every representative product, normal quotient tables and projection kernels. A nonnormal order-two subgroup of S₃ exposes actual conflicting representative products. | Extends the group/homomorphism goal |
| A8 | Prime fields F₂, F₃, F₅, F₇; exact scalar embedding a↦aI₂ into the noncommutative ring M₂(Fₚ); every image/kernel and generated ideal; complete general ideal proof. Nonunital zero maps and the unital map into the zero ring expose the two necessary hypotheses. | Q10 |

The old sentence asserting that any product of normal subgroups of coprime order is cyclic was mathematically false. Coprime orders give trivial intersection, and normality gives commutation, but the factors need not be cyclic. The order-fifteen proof explicitly uses their prime orders. For comparison, C₂×C₂ and C₃ are normal factors of coprime orders in a group of order twelve whose elements all have order dividing six.

Finite tables and lists are exhaustive for their labelled finite sets. Pictures of ℤ and ℚ are disclosed finite samples; they do not substitute for universal algebraic proofs. Zero is excluded from the stated zero-divisor convention. Graph positions and colors express mappings, membership and cosets; they do not create an algebraic metric. A5's second panel contains actual integer coordinates, uses stated axes/ranges, and draws only integer points, without interpolating segments.

## Shared core and spatial integration contract

The exported initial, controls, normalize, build, snapshot, and render methods are accompanied by station functions and exact operation helpers. Normalization returns every key, including controls for inactive stations. It clamps integral values to their declared bounds and rejects invalid numeric types/options. The build method returns state, station, active, panels, rows, proof and readout. Its primitives come directly from the station calculation:

- Table panels have kind "table", title, table, names and selected. Entries are exact element indices. Selected, when present, is a row/column pair.
- Graph panels have kind "graph", title, nodes, edges and note. Nodes have exact keys, labels and disclosed layout coordinates x/y, with optional group, selected or excluded values. Edges name existing node keys with from/to/label. In A5, repeated equal target integers share one target node.
- Integer-coordinate panels have kind "points", title, points, xRange, yRange, xLabel, yLabel and note. Points have actual x/y/label values.

The core preserves all finite tables, permutations, cosets, candidate constraints and failures. A7's failure records contain every actual a/b/product/coset for the conflicting representative pair. A6 includes every proof step and a highlighted step; A8 includes the five kernel/ideal proof steps. The accessible HTML ledger supplies every displayed operation-table row in addition to quantities and hypotheses.

The state bus key is math.5.abstract. Joining does not publish. A peer update rebuilds the model without echoing. Every local commit and reset publishes the complete normalized state. There is no persistence, cross-lesson message, formula parser, arbitrary source-file loader, or caller-selected CLI output path.

## Scientific and interaction verification

The tools/check_math_algebra_lab.js checker uses separate labelled-function, tuple enumeration, repeated-action, set-membership, exhaustive subgroup/ideal, matrix arithmetic and DOM checks. It verifies:

- All 19,683 labelled three-element operation tables, including the three group tables, all associativity counterexamples and invalid closure inputs.
- 209 cyclic element/subgroup/coset states; exhaustive subgroups through order twelve; the entire Klein subgroup lattice and contrasting C₄ orders.
- Every 576 ordered S₄ composition, 312 powers, and the independent order histogram 1:1, 2:9, 3:8, 4:6.
- 189 modular ring/kernel states, full selected addition/multiplication entries, exhaustive ideals through modulus ten, units, zero-divisor partners and the distinct assessed kernel/image.
- 481 integer multiplier/target examples, exact plotted points and mapping endpoints, including the unique collapsed target for the zero map. These bounded examples verify calculations; the text separately proves infinite statements.
- All 225 CRT product pairs, six normal/nonnormal quotient states and every representative product, and 51 field/matrix map/ideal states using independent matrix addition and multiplication.
- 94 mounted control/fixture states and 3,597 exact rendered operation-table cells; SVG coordinates/endpoints, current speech, draft/blur/Enter/Escape behavior, sliders, reset/enlarge and complete-state bus propagation.

The tests/test_math_algebra_lab.py suite has four passing checks: strict authored-node binding with malformed/cross-lesson negatives, dependency/control styles, the independent checker and the infinite-map/general-theorem hypotheses. The Python counterexample checks the incorrect broad coprime-factor claim separately from the finite runtime.

Standalone real-browser evidence is in ignored .research/algebra-lab-qa-20261011/proof.json, with the fixed-path harness standalone.cjs and sixteen station screenshots. At both 1440 and 390 pixels it checks eight stations, sixty numeric/select states, seventeen real slider/ArrowRight controls, seventeen fixtures, seventeen numeric draft/keyboard controls, twenty-five live speech captures and exact reset/enlarge. Every SVG text box is checked against its actual viewbox and other labels; all visible numeric/select controls are at least 44 pixels high. Page/model overflow and JavaScript errors are absent. Loaded runtime/style bytes are hashed against current local files.

Failed and superseded proofs are preserved. The initial table-caption/column-label collision was fixed. An initial copied-harness dataset name was corrected. Earlier successful records precede the explicit quotient witness, merged target nodes, or expanded ring/integer proof text and are not represented as final-source proofs. A signed-zero mismatch in the independent target-node comparison was corrected to mathematical numeric equality; the runtime's inverse value zero is canonicalized.

The browser context and local server are closed after the final run. This standalone review does not assert authenticated reader, coordinated 3D, production delivery or whole-subject completion; those are separate parent integration reviews.

## Primary references

[J. S. Milne, Group Theory, version 4.01](https://www.jmilne.org/math/CourseNotes/GT.pdf), chapters 1, 4 and 5, supports the group, coset, quotient, permutation, direct product and Sylow hypotheses. [Romyar Sharifi, UCLA, Abstract Algebra chapter 3](https://math.ucla.edu/~sharifi/notes/algebra-ch03.html), sections 3.1, 3.5 and 3.7, supports ring/field definitions, kernels, ideals and quotient statements. These were read during implementation. The diagrams, code, explanations and independent tests are authored here; no textbook pages or figures are copied.

## Frozen source hashes

- web/math-algebra-lab.js: 2305b53a9d4f55bc10b28fbe62d474e8ef214c2f6e0c4b6e83c0106b616d8460
- web/math-algebra-lab.css: d8b3588478d281dc4fa2420edaf725501d4fb6cd2de8ce92ef0eafbf8f04c2e0
- tools/check_math_algebra_lab.js: cf6fbacf82ff372bbe0ef37edff37ea8444dd499da807c0a0e3e3a76fdfe1981
- tests/test_math_algebra_lab.py: 05d37684f955b778ff83a30cd0668779a6ab141b20a61ad49fc25f85e65976df
- standalone_qa_proof: 9da632efe5aa7f99a0cfdd67df2ce64598e6a7be61bc514c718fa0766727f078
