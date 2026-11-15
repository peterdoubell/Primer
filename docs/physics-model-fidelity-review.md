# Physics model fidelity review

The physics curriculum has 39 lessons. Thirty-six use the shared physics concept
lab, while light/shadow, light/colour and advanced fluids use dedicated renderers.
The interactive mounts and illustrations are already present. Presence and a
changing picture do not establish that a model faithfully represents its lesson.

This review corrects four concrete physical inconsistencies in the shipped
concept labs. It does not approve all physics modules or the radiology goal.

| Lesson | Concrete correction | Scientific basis |
| --- | --- | --- |
| `phys.3.modern` | Curve, threshold, selected marker and displayed kinetic energy now use one equation and one physical scale. The example work function is 2.15 eV, with frequency in multiples of 10¹⁴ Hz, electron energy in eV and stopping-potential magnitude in V. Changing photon flux preserves the energy. | [OpenStax photoelectric effect](https://openstax.org/books/university-physics-volume-3/pages/6-2-photoelectric-effect); [NIST exact SI constants](https://www.nist.gov/pml/special-publication-330/sp-330-section-2). |
| `phys.3.optics-waves` | Both coherent contributions and their pointwise sum are visible on a fixed calibrated amplitude scale. Half-wavelength path differences cancel; integer wavelengths reinforce. The phase coordinate is explicitly a detector trace, not a two-slit image. | [OpenStax interference of waves](https://openstax.org/books/university-physics-volume-1/pages/16-5-interference-of-waves). |
| `phys.4.classical` | The drawn free-particle path is now the same path used for the action calculation: for m=1 kg and T=1 s, q=t+ε sin(πt), S=0.5+π²ε²/4 J s. Fixed endpoints persist throughout the full deformation range without clipping. A separate calibrated oscillator orbit has q and p intercepts determined by its Hamiltonian. | [Hamilton's principle, University of Texas](https://farside.ph.utexas.edu/teaching/336k/Newtonhtml/node89.html). The explicit path integral is derived from the stated free-particle Lagrangian; the separate oscillator has m=1 kg and k=1 N/m. |
| `phys.2.units` | Independent read-off errors now average with repeats. A separate shared calibration standard uncertainty remains as a floor. The visible curve, marker and readout use u²=(1.2²+resolution²/12)/N+u_cal², with a fixed 0–2 mm scale that contains all permitted states. | [NIST assumed uncertainty distributions](https://www.itl.nist.gov/div898/handbook/mpc/section5/mpc541.htm); [NIST combined standard uncertainty](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-5-combined-standard-uncertainty). |

All physical calculations state their assumptions. The read-off model assumes
independent rounding between repeats, which need not hold for repeated identical
digital readings. Calibration uncertainty is a standard uncertainty, not a known
bias or a guaranteed error bound. The free-particle example has a minimum action;
the general principle only requires stationary action. The example metal and
oscillator parameters are teaching choices, not measured material properties.

`node tools/check_physics_models.js` exercises all 36 concept-lab mounts and 63
controls. It now also checks 6,461 equation/geometry assertions across the four
corrected scenarios: the entire photoelectric curve and marker coordinates;
numerical integration of the actual displayed trial path; oscillator intercepts;
pointwise superposition and destructive cancellation; and the repeat/calibration
uncertainty budget. These assertions inspect the shipped SVG after slider events,
rather than testing a duplicated renderer calculation.

An isolated browser preview mounted the shipped renderer with the actual
curriculum media records. Ninety-six states passed at 390 and 1440 CSS pixels:
each control's Home/End states, resets, authored fit and enlarged views. The audit
checked body overflow, text bounding boxes inside each SVG, and exact readout
restoration. The four authored desktop views and representative mobile views were
visually inspected; interference labels were moved after a detected overlap.
This preview does not establish authenticated route or production deployment
behavior. Browser evidence is retained in the ignored research cache as
`physics-fidelity-browser-review.json` with the reviewed physics-section hash.

Remaining work includes equation and coordinate review of the other concept labs,
the three dedicated renderers, enlarged/browser states for the remaining lessons,
and assessing whether each model covers the actual module content. Examples still
using qualitative or limited representations include bar-magnet orientation,
heat-transfer pathways, donor-carrier indices, one-mode quantum field theory,
scale-factor cosmology and a single-angle entangled-pair sample. The latter does
not demonstrate a Bell inequality violation. A correct toy model of one example
does not establish complete high-fidelity coverage of an advanced module.
