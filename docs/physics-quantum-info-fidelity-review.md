# Quantum information lesson fidelity review — 2026-10-11

Scope: the actual `phys.5.quantum-info` lesson goal and all ten assessment rows. This adds an ideal mathematical laboratory; it does not certify quantum hardware, establish practical algorithm performance, or complete the wider physics/radiology programme. The original four-setting CHSH activity remains a separate authored resource.

## Assessment and mathematical coverage

| Station | Assessed requirement | Calculated and visible evidence |
|---|---|---|
| Q1 qubit | Prerequisite qubit meaning | Normalized complex α,β with arbitrary relative/global phase; explicit I,H,X,Y,Z,Rx,Ry,Rz matrices; output density, Z probabilities, complete Bloch coordinates and exact axis-rotation trajectory. The 2D xz projection explicitly omits y. |
| Q2 register | Quiz 3, 4, 7 | Tensor product preparation or selected basis state through n=12, all 2ⁿ amplitudes and Born probabilities; 10→1024 and 12→4096; H⊗3 gives eight 1/8 outcomes. Same-register repeat measurement is distinguished from a freshly prepared register. Zero-probability selected branches are rejected rather than normalized. All entries are inspectable through 64-row basis pages. |
| Q3 Bell | Quiz 1, 9 | All four Bell vectors; independent xz-plane projective axes; exact joint outcomes and signed correlation; Alice local I/H/X/Z or nonselective axis measurement; Bob partial traces before/after and selected conditional density. Unconditional Bob remains I/2 while conditional probabilities depend on the supplied classical record. |
| Q4 cloning | Quiz 2 | Actual CNOT(|ψ〉|0〉)=α|00〉+β|11〉 versus desired |ψ〉⊗|ψ〉 amplitudes, both marginal densities and fidelities. Known computational basis states are physically copied even when a global phase changes vector coordinates. The general inner-product/linearity obstruction is stated. |
| Q5 teleportation | Quiz 5 | Full eight-amplitude Q,A,B register at initial resource, CNOT Q→A, H on Q, selected measurement branch and corrected checkpoint. Every q,a branch has probability 1/4. Bob receives two bits and applies Xᵃ first, then Zᑫ; the corrected input amplitudes and phases are preserved. Bob before the record is I/2. The consumed Bell pair and changed original Q are explicit. |
| Q6 Grover | Quiz 6, 8 | Phase oracle and arithmetic-mean diffusion calculated for each basis entry when N≤64; a visible before/oracle/diffusion checkpoint table. Exact marked/unmarked aggregate rotation for any integer domain 4≤N≤10⁸, no huge arrays. Integer first peaks compare floor/ceil; million→785 and 10⁸→7853. Rough √N counts 1000/10000 remain distinct. Overshoot lowers success. |
| Q7 noise | Quiz 10 | Two explicitly defined completely positive trace-preserving models on the product input: whole-register replacement and independent local Z flips. Full output probabilities through n=12; density entries materialized through n=4, exact analytic product/mixture representation beyond. Fidelity, marginal density, off-diagonal coherence and independent no-error event probability are separate quantities. |

A pure n-qubit vector uses 2ⁿ amplitudes; a general mixed state uses a density matrix. Z flip noise can suppress coherence while preserving Z output probabilities. A uniform ideal output can also hide global depolarization in that measurement. A scalar hardware error percentage does not specify either channel. Under one independent error trial per step, p=.005 over 200 steps gives `.995**200 ≈ .36696` no-error probability; it is not a universal coherence lifetime.

Grover assumes one marked item, an ideal coherent phase oracle, uniform domain preparation and the appropriate reflection. A non-power-of-two domain requires subspace preparation rather than unqualified H⊗n. Query counts omit oracle construction/loading/gate costs and an additional candidate-verification query. The geometric trace depicts only the last iteration; fractional positions are a visualization guide, not extra oracle calls. No unconditional exponential claim for Shor is made.

## Runtime and shared geometry contract

Renderer `physics-quantum-info-lab`, scenario `phys.5.quantum-info.qubits-circuits-resources`, state bus key `phys.5.quantum-info`.

`PrimerPhysicsQuantumInfoLab` / CommonJS exports `initial`, `normalize`, `controls`, `choices`, `presets`, `controlActive`, `build`, `snapshot`, `render`, all seven named station snapshots and pure complex/matrix/register helpers. `build` returns `{state, station, current, panels, ledger, equation, readout, note, geometry}`. Controls preserve valid active/inactive state on station changes. Register measurement and marked indices normalize to their domain; effective basis-page offsets are calculated without discarding the requested page.

`geometry.blochVectors` contains true x,y,z expectation coordinates, including the zero vector for a maximally mixed local state. `geometry.trajectories[].points` contains complete unit-sphere rotations or the last Grover iteration in its normalized two-dimensional amplitude plane. `geometry.amplitudes` contains all complex basis entries for pure states. Mixed Bell/noise states carry `densityDiagonal:true` and probabilities, never invented pure amplitudes. Bell geometry reflects the current local operation rather than the original resource alone. `geometry.circuit` contains gate/wire/measurement relationships with `step` and `qubit` as declared layout coordinates, plus `target`/`classicalFrom` relationships. Core `current` retains all four teleportation branches, full density/checkpoint data and actual small-domain oracle/diffusion arrays. Camera/layout operations must not alter those physical quantities.

Basis charts place a dot at every calculated discrete coordinate; connecting lines are only guides. Amplitude and density-diagonal tables identify their conventions. Equal-scale unit-circle projections use equal x/y gains. Calibrated curve paths carry source coordinates, scales and units for verification.

## Verification

`node tools/check_physics_quantum_info_lab.js` passes: 2062 analytic fixtures, 133 mounted control/preset states, 432 calibrated SVG curves, 30 exact numeric draft/blur/Enter/Escape controls. The checker tests gate unitarity, trajectory endpoints, tensor normalization/dimensions, all Bell-state local/no-signaling choices, four phase-preserving teleportation branches, physical cloning fidelity, direct oracle/diffusion evolution, Grover peak/overshoot, explicit noise density/fidelity, finite bounds and complete current speech.

`tests/test_physics_quantum_info_lab.py`: seven tests pass in the scientific Python 3.12 environment. Independent oracles use direct three-qubit matrices, corrected branch Kraus operators applied to a reference-entangled Bell input, closed Bell correlation formulas, explicit tensor Born distributions, direct iterative oracle/diffusion arrays, and NumPy Hermitian eigenvalues for density positivity/trace. The tests explicitly avoid using vector difference as physical global-phase equality.

Fresh headless standalone Chromium contexts at 1440×1000 and 390×844 each passed seven stations, 60 exact numeric states, 60 range states, 30 draft and 30 keyboard exercises, 17 assessed presets and 243 complete speech/ledger checks. Reset/enlarge and no horizontal document overflow, SVG-text clipping or JavaScript errors pass. Fourteen full-card screenshots were inspected. Tables intentionally scroll within labeled keyboard-focusable regions on mobile. Evidence is retained in ignored `.research/quantum-info-lab-qa-20261011/proof.json` with source hashes and capture hashes. All owned browser contexts and the local HTTP server close in `finally`. This is standalone evidence; the parent task performs authenticated lesson/shared-3D integration and release checks separately.

Earlier passed standalone receipts are preserved under `proof-before-visible-checkpoints.json` and `proof-before-final-equation-labels.json`; they are not reused as final-source proof.

## Primary references checked

- [IBM Quantum: quantum states and operators](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/introduction)
- [IBM Quantum: circuits, measurements and no-cloning scope](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/quantum-circuits/introduction)
- [IBM Quantum: teleportation, bit ordering and analysis](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/quantum-teleportation)
- [IBM Quantum: phase queries, Grover operation and query model](https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/grover-algorithm/grover-algorithm-description)
- [IBM Quantum: channel linearity and complete positivity](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/quantum-channels/quantum-channel-basics)

The runtime equations, numeric calculations and diagrams are original implementations, not downloaded figures. Hardware noise remains explicitly hypothetical. No clinical, commercial, patient-registration or full-programme approval follows from this lab.
