# Signed point-dipole orientation model

The `phys.1.magnets` concept lab now plots signed axial and sideways force in millinewtons instead of qualitative orientation indices. A second control varies separation from 0.08 to 0.20 m. Both moments have fixed magnitude 1 A m². The first moment points along +z at the origin; the second is held at (0,0,r) and tilted from +z toward +x. These are prescribed snapshots, not simulated free motion or a finite-bar calibration.

With C=μ0/(4π) approximated as 10⁻⁷ N/A², the source field is B=C[3(m₁·n)n−m₁]/R³. Interaction energy is U=−m₂·B, force is −∇U with the second moment held fixed, and torque is m₂×B. The relations follow [UT Austin's magnetic vector potential/dipole notes](https://web2.ph.utexas.edu/~vadim/Classes/2024s-u/vecpot.pdf) and [OpenStax's current-loop torque treatment](https://openstax.org/books/university-physics-volume-2/pages/11-5-force-and-torque-on-a-current-loop).

On the prescribed axis, Fx=3C sinθ/r⁴, Fz=−6C cosθ/r⁴, τy=−2C sinθ/r³ and U=−2C cosθ/r³. Positive Fz points away from the first dipole; negative Fz is attraction. At 90°, axial force vanishes while sideways force and torque remain nonzero. The exactly anti-aligned orientation has zero torque but is unstable. The readout separates force, torque and energy units. A fixed −15 to +15 mN plot scale contains the entire permitted domain; the header legend remains separate from curves and markers.

The existing 3D bar object remains an orientation study. This point-dipole model does not solve its finite geometry, induced magnetization, hysteresis, contact forces, or dynamics. No measured material parameters or finite-bar force predictions are claimed.

The physics checker now makes 57,211 equation/rendered-coordinate assertions across 18 targeted scenarios. The new checks use the full three-dimensional field to compute numerical gradients of energy, rather than copying the runtime force formulas. They compare every plotted sample and marker over 91 angle/separation states, signed readouts, cross-product torque, and the orthogonal-force counterexample. Explicit tolerances include both SVG-coordinate rounding and differentiation error.

Authenticated isolated browser checks passed 34 authored, native keyboard endpoint, joint-corner, orthogonal and reset states at 1440 and 390 pixels. SVG text clipping/overlap and page overflow checks passed. Served renderer bytes match the recorded SHA-256. This is local reader evidence; production delivery remains pending.

The exact inverse retains historical source comparisons. Earlier wave/ramp evidence remains attached to its preserved renderer view, and current equation checks still exercise those cases. No clinical or whole-physics approval is extended.
