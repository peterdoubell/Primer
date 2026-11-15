# Physics model fidelity followup

Source review of the 39 physics lesson bindings identified further differences
between equations, rendered coordinates and the physical quantities claimed.
Five additional concept labs are corrected here. The four earlier corrections
remain intact. This is continuing fidelity work, not approval of all 39 lessons.

| Lesson | Change grounded in the physical example | Quantitative verification |
| --- | --- | --- |
| `phys.1.motion` | The selected time is now independent of friction. Its marker uses that exact time rather than a different sampled curve index. The constant-friction trajectory stops without reversing, and the readout accounts for kinetic energy plus thermal gain. Axes state seconds and metres. | Every plotted coordinate is checked against the piecewise constant-acceleration solution. At each selected time, K+F_friction x=16 J for the 2 kg, 4 m/s launch. Zero friction and post-stop states are included. |
| `phys.3.relativity-intro` | A 1 μs proper-time clock event is now drawn on a calibrated 0–4 μs coordinate-time scale. Previously only the slope changed, with no plotted clock tick. | The event obeys t=γτ and x/c=βt, including β=0 and β=0.95. The Minkowski interval recovers τ². |
| `phys.4.relativity` | The moving-frame simultaneity slice now passes through the selected event. Every point satisfies t′=γ(t−βx/c)=τ. Previously the slice stayed at one arbitrary intercept while the proper-time control moved the event. Physical clipping preserves the line equation. | Positive, zero and negative β, proper times 1/4/10 μs, both slice endpoints, event coordinates, line slope and inverse transformation are checked independently. |
| `phys.3.thermo` | Input heat, rejected heat and work arrows use the same shaft-width scale. Their displayed widths represent the reversible limit, with real-engine inequalities retained. Previously arrow lengths used unrelated scales. | All selected reservoir pairs satisfy Q_h=W+Q_c, Q_c/Q_h=T_c/T_h and zero total reversible reservoir entropy change. The measured SVG shaft widths obey those relations. |
| `phys.3.nuclear` | A fractional ensemble expectation is separated from one integer mock survival history. Exponential lifetimes persist while time moves; changing the realization selects another reproducible history. Previously fractional expected survivors were rounded to whole visible dots. | The theoretical curve and selected marker follow 2⁻ᵗ. Each mock history is monotone, starts with N₀ nuclei, loses exactly one nucleus per step, and contains the selected integer count. Expected count and binomial standard deviation agree with the readout and support-clipped error bar. |

The physical assumptions follow [OpenStax friction](https://openstax.org/books/university-physics-volume-1/pages/6-2-friction),
the [Lorentz transformation](https://openstax.org/books/university-physics-volume-3/pages/5-5-the-lorentz-transformation),
the [Carnot cycle](https://openstax.org/books/university-physics-volume-2/pages/4-5-the-carnot-cycle),
and [radioactive decay](https://openstax.org/books/university-physics-volume-3/pages/10-3-radioactive-decay).
The nuclear example uses independent exponentially distributed lifetimes with
λ=ln 2 in half-life units. A selected realization is synthetic, not measured data.
Its error bar represents one theoretical standard deviation, not a confidence
interval or guaranteed error bound. Daughter decay is omitted.

The Carnot shafts represent the reversible bound, not a prediction of a real
engine's efficiency. Equal shaft width per joule is explicitly stated; differently
directed arrow lengths and arrowheads are pathway symbols. The stopping-cart
energy account includes thermal stores of the cart and surface. Neither the
trajectory nor these spacetime examples include rotation, acceleration during
turnaround, gravity or unmodelled losses.

`node tools/check_physics_models.js` passes all 36 concept-lab mounts and 65
independently exercised controls. Its 14,862 equation/geometry assertions now cover
nine targeted scenarios in total, including the four previous corrections.
Control readouts retain the decimal precision of their authored step, including
quarter half-lives. Those checks inspect shipped SVG geometry after actual control
events and use physical invariants as independent oracles.

The shipped renderer was also mounted with actual curriculum media records in an
isolated browser preview. All 110 authored/edge/reset/fit/enlarged states passed at
390 and 1440 CSS pixels. Each control was moved with Home/End keys and Reset;
resets restored the exact authored readout. Body overflow and SVG text clipping
checks passed. The five authored desktop views were visually inspected. Evidence
is retained in the ignored research cache as
`physics-fidelity-followup-browser-review.json`, bound to the reviewed physics
section hash. These preview checks do not establish authenticated routes or
production behavior.

The three dedicated-renderer defects were also corrected in this followup,
extending the work to twelve targeted physics examples:

| Dedicated lesson | Corrected representation | Verification |
| --- | --- | --- |
| `phys.0.light-shadow` | Point-source boundary rays touch the actual lamp-facing corners of the square-cornered opaque card. The cast rectangle also has square corners and remains on the screen throughout the control range. The source/card/screen coordinates share a scale. The lamp support no longer crosses and blocks the lower ray. Extended-source penumbrae are explicitly omitted. | All 101 positions satisfy the near-face intersection and similar-triangle magnification law. Cast endpoints match rays, the screen contains the cast, lamp-off hides rays/shadow, and Reset restores the authored state. |
| `phys.1.light` | Incoming, internal and emerging prism rays join at both physical faces and satisfy Snell's law using seven tabulated N-BK7 spectral indices. A new control selects the seven-line white approximation or one monochromatic line. The physical dispersion stays small; colour and line weight are display cues. Mirror rays use equal angles from the actual source centre. Diffuse toy rays leave the illuminated face into the outward half-space. | All eight spectral states use the exact source rows and satisfy Snell at both faces, face intersections, joined endpoints and screen containment. Mirror reflection and illuminated-face scattering are checked from actual SVG endpoints. |
| `phys.4.fluids` | Velocity arrows use one length scale, including equal arrows at equal areas. Circular radii follow the square root of area. Open standpipe heights use h=P_g/(ρg), a common centreline datum and a separate calibrated head panel above the scale breaks. The boundary inlet gauge pressure is 16.5 kPa, water density 1000 kg/m³ and g=9.81 m/s². | All three geometries satisfy Q=Av, circular area/radius ratios, Bernoulli pressure differences and hydrostatic standpipe heights. The downstream head recovers only within the ideal loss-free model. |

The prism uses [SCHOTT's original N-BK7 data sheet](https://media.schott.com/api/public/content/41e799d0bf874807a0bb8e702fbb75b5?v=54856406)
with [Snell's law and dispersion](https://openstax.org/books/physics/pages/16-2-refraction).
The seven wavelengths and indices are factual tabulated values, not a fitted
glass model or a measured power spectrum. Fresnel reflections, absorption,
diffraction and a quantitative diffuse-scattering distribution are omitted.
The shadow law follows [similar triangles](https://openstax.org/books/contemporary-mathematics/pages/10-3-triangles);
the flow/head relations use [Bernoulli's equation](https://openstax.org/books/college-physics/pages/12-2-bernoullis-equation?query=first+law).

`node tools/check_physics_dedicated_models.js` passes 883 independent coordinate
assertions. A focused pytest regression invokes that shipped-renderer checker.
The existing DOM infrastructure is reused through an explicit module export;
standalone execution of the remaining-model checker retains its normal behavior.
Each dedicated renderer now participates in the existing enlarge/scroll control.
An additional 60 browser states passed at 390/1440 CSS pixels, including all prism
selections, all Venturi choices, shadow extrema/lamp-off, resets and fit/enlarged
views. The authored desktop views were visually inspected. Evidence is retained
as `physics-dedicated-browser-review.json` with hashes of all three renderer
sections. These preview states remain distinct from production-route verification.

The remaining concept labs still require full equation, physical-coordinate,
assumption and learner-content coverage review. Their disclosed qualitative
indices or simplified examples do not establish complete coverage of advanced
electrodynamics, solid-state physics, quantum field theory, cosmology or quantum
information. In particular, a single-angle singlet sample is not a Bell-inequality
demonstration. The goal remains broader than the nine examples checked here.
