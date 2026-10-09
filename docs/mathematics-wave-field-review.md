# Wave-field fidelity review

The PDE lesson already included an insulated nine-cell heat stencil. Its goal
and quiz also name the wave equation and travelling profiles, which the heat
stencil cannot represent. The new activity preserves that stencil and adds two
exact one-dimensional wave families on a finite interval with fixed-zero ends.

The modal example uses the first two sine eigenfunctions. Both initial
displacement coefficients are independent, and the first-mode initial velocity
is independently controlled. A continuum heat solution shares the initial
profile and Dirichlet boundaries; its modal amplitudes decay while the wave
oscillates. Heat needs one initial profile, whereas the wave also needs velocity.
The separate original heat rod has insulated boundaries and is not the same
boundary-value problem.

The travelling example uses a compact C² bump centred at0.3L with half-width0.08L.
For a2L-periodic bump F, u(x,t)=F(x−ct)−F(−x−ct) enforces both fixed endpoints.
Its initial velocity is−c f′, so the initial pulse travels rightward before
reflecting with sign inversion. No absorbing boundary, wrap-through or smoothing
is substituted for reflection. Original code and artwork use standard results
described in [MIT's wave-propagation notes](https://ocw.mit.edu/courses/2-062j-wave-propagation-spring-2017/pages/lecture-notes/);
no course graphics or media are redistributed.

The field u is dimensionless; x is in metres, time in seconds, speed in m/s and
diffusivity in m²/s. E=½∫(u_t²+c²u_x²)dx has units m/s² and is a mathematical
wave invariant, not calibrated physical energy. Heat H=½∫u²dx has units m and
decays. Their normalized fractions use their own initial values. Zero initial
quantities have undefined ratios; those curves are omitted and explicitly
labelled rather than drawn as zero. Neither physical material properties nor
absolute temperature is inferred.

The spatial profiles sample321 exact points. The space-time colour map samples
50×64 cell centres over one wave period in a clearly stated time window; it is
not a full-history or continuous image. Blue/pale/coral mean positive/zero/negative
field. The current-time line and all axes use the stated physical coordinates.
The amplitude bound contains every permitted profile and sampled cell.

Independent verification checks2592 field/derivative states, spatial and temporal
derivatives, Dirichlet ends, continuous initial data and the PDEs themselves.
Simpson integration of the actual velocity/gradient verifies conserved energy,
including the compact-pulse coefficient1024/385. Eleven separately evolved
finite-difference wave/heat solutions provide a solver-independent comparison,
including reflected pulses. Twenty-one mounted slider states, reset,
zero-initial/velocity-only cases and actual SVG endpoints are checked. An
independent agent derived the pulse integral, inspected90 extreme time windows
and checked all sampled field magnitudes; its zero-ratio concern was corrected.

This activity does not supply general multidimensional fields, arbitrary initial
profiles, forcing, nonlinear wave media, dissipative waves, elliptic problems or
weak/distributional solutions. Those remain outside this concrete example; full
PDE and mathematics visual coverage is not established by these checks.

The actual local lesson route `#/node/math.5.pde` was reviewed with a disposable
QA profile at 1440 and 390 CSS pixels. Eighty-eight native browser states passed:
every slider's keyboard extrema/reset, a velocity-only modal case, zero
equilibrium, a pulse before/after reflection and after one period, pulse control
extrema, and fit/enlarged views. Each state's 321-point profiles, defined
quadratic-ratio traces, physical time marker and 50×64 colour cells were compared
with independent stated formulas; 281,600 actual colour cells were checked.
Zero-initial ratios were absent and explicitly labelled undefined. Body overflow,
transformed SVG text bounds, plot descriptions, slider names/value text and
disabled pulse controls passed. Enlargement no longer shrinks the wide desktop
quantity panel, mobile keyboard scrolling works, and a pointer click with the
button visible below the fixed header activates it.

The lesson API returned the exact authored wave-model binding. Served
`app.js`, `math-wave-lab.js` and `math-wave-lab.css` bytes matched the workspace
SHA-256 values. The actual read-aloud button supplied the complete readout in two
speech-synthesis chunks, preserving decimals such as `0.75` and `1.67783` after
the shared speech-splitting repair. This checked utterance content, not audible
pronunciation or device voice availability. No page exceptions were observed.
Evidence is retained in the ignored research cache as
`math-wave-actual-route-browser-review.json`. These are local route checks;
production behavior and complete PDE coverage remain separate requirements.
