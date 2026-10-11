# Complex and quantum spatial audit — 11 October 2026

The bounded independent numerical audit passes **73 complex scenes across C1–C6 and 80 quantum scenes across all five modes**. The focused Python file passes **7 tests**, including a second set of SciPy quadrature and NumPy boundary-matching references. These findings concern numerical data, emitted primitives, units, normalized controls, state retention, and semantic ledgers. Browser reader QA is owned separately by `complex_analysis_lab`; this report does not certify that work or completion of the larger request.

## Reproduction

From the release checkout:

```sh
node tools/check_complex_quantum_spatial.js
/Users/peter/Documents/ChatGPT/Primer/.research/runtime-grade-py312-20261008/bin/python -m pytest tests/test_complex_quantum_spatial.py -q
```

The Node command reports 73 complex states and 80 quantum states. The Python command reports `7 passed`. System Python and the root `.venv` each previously reported `4 passed, 3 skipped` because NumPy/SciPy are absent there. The observation packet is a fixed, bounded `--fixtures` mode of the same checked-in CommonJS entry point. No expression evaluator, VM, filesystem-source execution, arbitrary executable selector, or environment-provided numerical oracle is used.

## Numerical and geometric crosswalk

| Station or mode | Independent reference | Emitted geometry and units checked | Status |
| --- | --- | --- | --- |
| C1 directional derivatives | Direct named complex arithmetic; analytic logarithm and phase of exp(−1/z⁴); finite quotients and pointwise/CR classification | Actual surface facets; input/probe/output transforms; h and approach angle; cyclic phase color; true-zero versus underflow/overflow semantics | Passed bounded fixtures |
| C2 contours and residues | Genuine poles and residue coefficients, signed winding; removed rational zero-residue terms; annulus hypotheses | Circle orientation, separate output loop, correct contour probe, pole markers; rectangle/domain and finite/crop omission | Passed bounded fixtures |
| C3 Taylor radius | Independently generated coefficients, finite polynomial, actual error and valid open-disk remainder bounds; nearest singularity | Convergence circle, probe and partial sum in one uniform output scale; assessed-radius endpoints and unknown boundary semantics | Passed bounded fixtures |
| C4 Liouville and roots | Exact compact-disk maxima; fixed global M/R hypothesis; six dependent proof steps | Comparison disk and uncropped probe; explicit x=R/6 and y=0.1M/R theorem strip | Passed bounded fixtures |
| C5 mean and maximum modulus | Analytic complex mean, independent numerical mean of modulus, exact boundary maximum and theorem hypotheses | Closed input/output loops, uniformly scaled center/mean values; pole, exact zero-circle omission and failed-hypothesis handling | Passed bounded fixtures |
| C6 Jordan arc | Independent real/arc quadratures, oriented residue integral, factor supremum and conditional bound; g=1 and k=0 counterexamples | Upper/lower closing-arc orientation, forward real segment, midpoint probe, phase and logarithmic exponential gain | Passed bounded fixtures |
| Well | Exact SI electron energy; independent complex time-evolving coefficients; analytic Born CDF and independently inverted seeded detections; SciPy probability quadrature | (x,Re ψ,Im ψ) in nm and nm⁻¹/²; hard walls, nm⁻¹ density, selected interval, count/N bin polygons, uniform eV strip, probe; Hamiltonian/time-evolution samples | Passed bounded fixtures |
| Spin | Pauli projector probabilities for all six pure axial states and unpolarized input; original-input and survivor denominators | (rₓ,r_z,−rᵧ), unit calibration circles, axis endpoints; schematic branch connections and width=1+5p; zero survivors and count conservation | Passed bounded fixtures |
| Gaussian | Complex Gaussian integral and direct independent Fourier quadrature; Python SciPy Fourier integration; erfc tails | Position and momentum complex phases, density per x/per k, k=p/ℏ; x gain 0.1 and amplitude/density gain 5; crop coordinates and unrenormalized tails | Passed bounded fixtures |
| Barrier | Four complex interface equations solved independently by Gaussian elimination and NumPy; analytic transmission and conserved current | Three-region complex amplitude; 0.25 potential/energy gain; reflected/transmitted fraction heights, current and unchanged outgoing energy | Passed bounded fixtures |
| Photon | Exact SI hc/λ, joule conversion and distinct 1240 eV·nm assessment convention | λ gain 0.01, energy in eV, selected marker, one-wavelength phase reference with fixed display amplitude | Passed bounded fixtures |

## Complete control crosswalk

Every authored state field is retained when switching stations/modes; fully populated inactive states are checked rather than relying on default-valued fixtures. The following groups identify each field's dependency. `station` and `mode` select the active model while retaining the full ledger of the preparation.

| Family | Controls | Geometry/data dependency | Status |
| --- | --- | --- | --- |
| Complex C1 | directionalFn, pointRe, pointIm, angle, logStep | Named surface, probe, derivative classification, directional step and quotient | Passed |
| Complex C2 | contourFn, residueA, residueB, circleRe, circleIm, radius, winding | Genuine poles/residues, oriented contour, annulus domain and complex output | Passed |
| Complex C3 | taylorFn, terms, pointRe, pointIm | Coefficients, polynomial, probe, convergence boundary and remainder bounds | Passed |
| Complex assessed inference | inferenceRadius | Geometry legitimately stays invariant; selected admissible radius changes semantic ledger/readout; 2 and 3 remain allowed endpoints | Passed, separate ledger check |
| Complex C4 | growthFn, growthRadius, globalM | Entire comparison, disk maximum, actual disk and hypothetical M/R strip | Passed |
| Complex proof reveal | proofStep | Geometry legitimately stays invariant; full ordered proof and reveal-count ledger update | Passed, separate ledger check |
| Complex C5 | meanFn, circleRe, circleIm, radius | Named function, complex mean/modulus maximum, zero-circle omission and disk hypotheses | Passed |
| Complex C6 | arcFn, k, halfPlane, arcRadius, poleA | Signed arc, exponential gain, poles, finite integrals and Jordan certificate | Passed |
| Complex local display | domainExtent, heightCrop, heightMode | Exact bounded crop controls, projection ordinate and mesh omission; physics state remains shared | Passed invalid/default, bound and exact-fraction checks |
| Quantum well preparation | wellState, n, lengthNm, mix, phaseDeg, globalPhaseDeg, timeFs | Exact energy, complex coefficients and amplitude; common phase preserves density while changing ψ | Passed, full phase-ledger check |
| Quantum observed energy | projection | Only outcomes with positive prepared Born probability are retained; impossible alternatives restore unmeasured preparation; supported observed eigenstates repeat certainly | Passed independent alternative-outcome negatives |
| Quantum interval/probe | regionStart, regionEnd, probe | nm interval endpoints, exact regional probability and complex probe | Passed, reversed endpoint normalization checked |
| Quantum spin | prep, axis, middle, middleSign | Pauli expectations, selected branch probabilities and conditional denominator | Passed all preparation/axis choices and all middle/sign choices |
| Quantum Gaussian | sigmaNm, centerNm, kCenter, chirp, cropSigma | Fourier-linked phases/spreads, position-density invariance under chirp, cropped tails and SI momentum ledger | Passed |
| Quantum barrier | energyEV, heightEV, widthNm | Independently matched scattering problem, zero-width transparency, potential/energy gain and flux | Passed, E<V₀ normalization checked |
| Quantum photon | wavelengthNm | Vacuum SI energy and phase-reference wavelength | Passed including exact fractional wavelength |
| Quantum finite preparation batches | detections, seed, batch | Independent deterministic detections and count geometry; exact amplitudes remain invariant | Passed with independent inverse-CDF bin fixture |

The exact assessed-width checks set E₁=1.5 eV and E₁=2 eV using independently calculated electron well widths. They verify the widths are not snapped to the visible slider step, and reproduce E₄=24 eV and E₃=18 eV. Full quantum preparation retains an exact width `0.4123456789`, a nonzero batch, and an eigenenergy projection across all five modes.

Calibration negatives deliberately displace the photon marker, alter a spin branch width, and change a complex facet coordinate; the independent validators reject each mutation. Additional edges include path poles, removed rational poles, clockwise double winding, pathology underflow/overflow, Taylor boundary/outside probes, nonholomorphic mean contrasts, zero survivors, Gaussian tail crops, zero-width/narrow/thick barriers and normalized E≥V₀ inputs.

## Findings and bounded verification

The root implementation owner corrected the following issues while this audit was running; the corresponding bounded checks now pass:

1. C5 output samples excluded the repeated endpoint, leaving the output loop open. The emitted line now closes the loop.
2. Optional display controls accepted `null`, booleans, arrays and whitespace as numbers. Invalid values now restore the documented defaults.
3. The C2/C6 scene probe did not use the active contour/arc probe. The emitted probe now follows that location.
4. Annulus surfaces showed samples outside the selected domain. Whole rectangles are now omitted unless their radial range lies strictly inside the annulus; its boundaries are explicitly drawn.
5. Log-only underflow samples could be represented by output zero markers. Those unrepresentable finite outputs are now suppressed while their uncropped logarithmic ledger remains available.
6. A logarithmic facet could cross an interior true zero despite finite uncropped corners. Exact zero-circle/isolated-zero/rational numerator tests and a conservative polynomial nonzero certificate now omit those cells. The independently reproduced C5 peak cell `(15,16)` is omitted in logarithmic mode and remains continuous in magnitude mode. An off-grid rational zero and all four independently calibrated Laurent numerator roots are also omitted. C6 reciprocal integrands are explicitly exempt because they have no zeros in their regular domains.
7. Unsupported observed eigenenergies could fabricate a collapsed state with zero prepared probability. Independent negatives now verify eigenstate n=1 cannot yield n=6, mix=0 cannot yield n=2, and mix=1 cannot yield n=1. Each invalid request restores `projection=none` and leaves the complete unmeasured data and geometry intact. Supported mixture outcomes and same-n observations, including n=3/n=4, preserve ideal repeat certainty.

Finite facets approximate the named functions between mesh samples. The Laurent certificate may omit rectangles that are actually nonzero because it issues only a sufficient certificate: a conservative omission does not assert a root exists. This bounded audit verifies emitted vertices and the stated zero/pole/domain certificates; it does not prove holomorphy, a global theorem, or exact continuous surface coverage between samples.

No full test suite, Git mutation, deployment, or duplicate browser QA was performed by this audit owner. Source hashes and machine-readable statuses are recorded in the companion JSON report.
