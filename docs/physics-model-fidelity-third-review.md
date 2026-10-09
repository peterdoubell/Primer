# Physics model fidelity: third review

The 27 physics lessons outside the twelve previously corrected examples were
reviewed against their actual curriculum goals and authored model calculations.
Five more examples are corrected here. Correct examples do not establish that
their full lessons, all 39 physics lessons, mathematics or radiology meet the
requested final standard.

| Corrected example | Physical change | Independent evidence |
| --- | --- | --- |
| `phys.4.quantum` | Infinite-well density is normalized in nm⁻¹. Every seeded detection is retained; histogram area is exactly one without clipping counts or removing gaps from the normalization account. A new well-length control moves the wall on a fixed 0–2 nm axis and changes the actual electron energy as n²/L². | Actual bar areas/counts, wall coordinates, complete theoretical curve, normalization integral and electron energies agree across every n=1…5 and selected sample/length extremes. |
| `phys.4.solid-state` | Arbitrary donor-dot indices are replaced by signed ionized donor/acceptor densities, electrons, holes and a calibrated Fermi level. Charge neutrality and mass action hold together. | n and p reconstructed from the actual rendered band/EF coordinates satisfy n−p=N_D−N_A and np=n_i². Intrinsic, n-type and p-type cases and temperature/gap extremes are covered. The tested range remains dilute. |
| `phys.5.quantum-info` | Four setting pairs now form a signed CHSH statistic. A visibility control mixes singlet correlations with isotropic white noise. Mock pair data include both joint correlations and actual local counts. | Four independent detector-angle dot products agree with the plotted theory. The maximal theoretical value is 2√2. Mock S is assembled from four integer-count correlations, with the correct signed-S variance and support-clipped error bars. |
| `phys.5.qft` | Every one-mode energy level now includes the half-quantum vacuum offset, on a common E/ℏ scale. A separate zero line prevents n=0 from being visually assigned zero energy. | All rendered levels satisfy E_n/ℏ=(n+1/2)ω, with the correct adjacent spacing and selected occupation. Angular frequency is in rad/s and E/ℏ in s⁻¹. |
| `phys.2.electricity` | The current gauge now spans the full allowed 0–12 A range. Its earlier saturation at 3 A concealed changes in larger currents. Load power is also reported. | Gauge width agrees with V/R for open/closed circuits and voltage/resistance extremes; P=VI agrees with the readout. |

The well uses [OpenStax's normalized infinite-well solution](https://openstax.org/books/university-physics-volume-3/pages/7-4-the-quantum-particle-in-a-box)
and [NIST 2022 electron-mass data](https://physics.nist.gov/cuu/pdf/wallet_2022.pdf).
The semiconductor follows the [MIT semiconductor physics review](https://ocw.mit.edu/courses/6-772-compound-semiconductor-devices-spring-2003/f28cc4ae7325640e457b5e14b2d5fa19_lec4_supplement.pdf).
Its symmetric effective densities of states are deliberately hypothetical:
Nc=Nv=10¹⁹(T/300)^(3/2) cm⁻³. It is not a fitted silicon model. Fully ionized,
nondegenerate carriers, fixed gap and effective masses are assumptions; freeze-out,
mobility, junctions and degenerate statistics are omitted. The gap range is
0.5–4 eV so the displayed approximation stays dilute over the selected temperature
and dopant ranges.

The four-setting example follows the [CHSH bound](https://quantum.cloud.ibm.com/docs/en/tutorials/chsh-inequality)
and singlet correlation E(a,b)=−a·b; visibility multiplies that correlation for a
singlet/white-noise mixture. Finite mock estimates can fluctuate outside bounds on
expectations. They are not experimental Bell evidence. Local theoretical marginals
remain 50/50, while finite local counts need not be equal. Gates, algorithms,
teleportation and experimental loophole closure are not shown. The QFT ladder
uses [Tong's free-field oscillator construction](https://www.damtp.cam.ac.uk/user/tong/qft/two.pdf);
it does not treat interactions, fermions, renormalization or the full field vacuum.
Subtracting a reference vacuum energy changes the energy zero, not the spacing.

The core checker passes 36 mounts, 67 controls and 22,137 equation/geometry
assertions across fourteen targeted concept-lab scenarios. The previous 883
dedicated-renderer assertions still pass. Ten focused physics pytest tests pass.
These checks retain the twelve prior corrections and do not promote smoke-test
presence to physical approval.

The five new examples passed 142 direct-renderer browser states at 390/1440 CSS
pixels: independent Home/End control changes, exact reset restoration and
fit/enlarged views. SVG text clipping and body overflow checks passed; all five
authored desktop views were visually inspected. Evidence is in the ignored
research cache as `physics-third-browser-review.json`, bound to the reviewed
physics-section hash. This does not verify authenticated lesson routes or
production deployments.

The following audit covers all 27 lessons in this review scope. “Missing” refers
to the authored model or unverified physical representation, not a claim that
the associated articles contain no explanation.

| Lesson | What the current model actually supplies | Remaining requirement or fidelity gap |
| --- | --- | --- |
| `phys.0.push-pull` | Steady opposing forces and net direction. | Starting/stopping trajectories and inertia are not modelled. Curriculum wording that motion always needs a push was flagged for correction. |
| `phys.0.hot-cold` | Equal-capacity insulated pair with an exponential temperature gap. | Heat capacity, conductance, energy transfer and the time constant need explicit quantitative verification; temperature-bar heights are not heat contents. |
| `phys.0.float-sink` | Full-immersion density/force-ratio example. | Force labels lack newton calibration; partial submersion, displaced-water geometry and floating equilibrium are missing. |
| `phys.1.machines` | Ideal ramp force/work relation. | Named levers, wheels and pulleys are not represented by the ramp example. |
| `phys.1.magnets` | Qualitative cosine/sine orientation indices. | Actual pole/field/compass geometry and calibrated force/torque assumptions are missing. “Always north” wording was flagged. |
| `phys.1.sound` | Pressure waveform and relative amplitude-squared intensity. | Calibrated time/pressure axes, longitudinal air motion and propagation versus vibration frequency need verification. Ambiguous “speed changes pitch” wording was flagged. |
| `phys.1.energy` | A closing 100-unit store ledger. | It is bookkeeping, not a physically calculated trajectory or measured transfer sequence; actual stores/pathways need a grounded example. |
| `phys.2.forces` | Instantaneous net force for an already-moving crate. | Static friction, speed-dependent drag and terminal-motion behavior in the stated goal are not modelled. |
| `phys.2.gravity` | Weight in a uniform local field. | Named falls, orbits and tides are missing; graph-axis calibration still needs independent verification. |
| `phys.2.electricity` | Corrected ideal single-load current/power example. | Parallel/series networks and static charge/sparks in the goal remain outside this model. |
| `phys.2.heat` | Qualitative conduction/convection/radiation motifs. | Material/geometry-dependent fluxes, convection transport and absolute-temperature radiative exchange are not quantitatively represented. |
| `phys.2.waves` | Fixed-speed wavelength relation and one sinusoidal trace. | Physical spatial/time axes, longitudinal sound and the differing water/light representations remain to be checked. |
| `phys.2.matter` | Water phase labels, particle motifs and coexistence at transition temperatures. | Latent heat, controllable phase fractions, pressure dependence and quantitative density/energy accounting are missing. |
| `phys.3.mechanics` | Constant net-force acceleration of a point mass. | Trajectories, interaction pairs and broader Newton-law applications need physical representations and independent coordinate checks. |
| `phys.3.energy-work` | Equal-mass one-dimensional restitution and relative energy ledger. | Configurable masses/velocities, collision geometry and absolute momentum/energy scales remain missing. |
| `phys.3.em` | Linear fixed-gradient Faraday example. | Flux-gradient units, real coil/flux geometry, Lenz-current direction and broader fields/circuits are insufficiently represented. |
| `phys.4.em-maxwell` | Qualitative orthogonal in-phase vacuum-wave cues and a separate spatial example. | Absolute E/B scaling, Poynting direction, divergence/curl/charge relations and physical spacetime coordinates need verification. |
| `phys.4.quantum` | Corrected normalized infinite-well eigenstates and measurement sampling. | The stated spin/Schrödinger goals and current spin, uncertainty, superposition and tunnelling questions are not fully illustrated. |
| `phys.4.statmech` | Exact four-coin multiplicities and lnΩ. | Atomic ensembles, energy-dependent probabilities and temperature as an entropy derivative are missing. |
| `phys.4.solid-state` | Corrected bulk donor/acceptor equilibrium plus existing unit-cell activity. | Depletion regions, band bending, pn-junction bias, conductivity/mobility and actual-material calibration remain outside this model. |
| `phys.4.particles` | Three symbolic additive-quantum-number checks. | Quarks/leptons/gauge families and actual charge/baryon/lepton values are not illustrated comprehensively; energy/momentum/spin audits are absent. |
| `phys.4.experiment` | Synthetic bias/scatter/outlier residuals. | Plot clipping can conceal raw extremes; calibrated axes, uncertainty propagation, repeated-trial inference and residual independence need work. |
| `phys.5.qft` | Corrected one-bosonic-mode ladder. | Interactions, off-shell diagram interpretation, fermions, loop corrections and renormalization in current questions remain missing. |
| `phys.5.gr-cosmo` | Homogeneous scale-factor/redshift example. | Einstein/Friedmann dynamics, matter/radiation/Λ history, causal horizons and gravitational observables are not represented. |
| `phys.5.condensed` | Simplified lead-like type-I order/critical-field example. | Actual Meissner flux geometry, phase-boundary fidelity, other transitions and emergence remain incomplete. |
| `phys.5.quantum-info` | Corrected four-setting correlations/noise and actual finite local counts. | Qubit gates, no-cloning, teleportation/classical bits, Grover and noisy circuits in the actual curriculum are still missing. |
| `phys.5.frontier` | Synthetic outer-disk rotation-curve fit. | Physical radii/speeds and mass-model assumptions need calibration; the named quantum-gravity/open-problem scope is not represented. |

Every row still needs review of complete lesson coverage and relevant rendered
states. The five corrected examples address concrete errors and some named
questions; they do not finish these lessons or the overall goal.
