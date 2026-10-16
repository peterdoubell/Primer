# Optics fidelity review — 16 October 2026

The optics lesson's existing interference activity only combined two coherent contributions at one detector. Four companion activities now model signed thin-lens image formation, finite-aperture single-slit diffraction, refraction/total internal reflection, and coherent single-film reflectance. The existing interference controls, curriculum JSON, quiz questions, and source illustration are preserved.

The runtime attachment is limited to `phys.3.optics-waves`. Other physics scenarios retain their original behavior. The models live in the existing concept bundle, which loads before the lesson-model renderer. The existing read-aloud function includes their current readouts. Each plot can be enlarged and scrolled with keyboard or touch.

## Physics and units

- **Lens:** ideal paraxial thin lens, distances in centimetres. A fixed 0.5 cm object, whole-centimetre focal magnitudes 5–50 and object distances 5–100 keep each model ray slope at most 0.1. Positive image distance means real; negative means virtual. At exact focus the outgoing rays are parallel and no finite image is invented. Solid arrows show propagating rays; dashed back-extensions locate virtual images. The lens line is a schematic symbol, not a calibrated aperture. Vertical detail defaults to an explicitly labelled 10× scale; an equal-distance-scale view is available. Finite-aperture clipping, aberrations and exact thick-lens surfaces are not solved.
- **Slit:** uniformly illuminated, coherent monochromatic scalar Fraunhofer model. Width is in micrometres, wavelength in nanometres, and screen distance in metres. The plot is angular intensity normalized to each aperture's own on-axis value. It does not assert equal absolute transmitted power or detector-plane irradiance. Minima use `a sin θ = mλ`; screen positions use `y = L tan θ`. If a first forward minimum does not exist, the model says so. The permitted aperture/wavelength/distance ranges have Fresnel number at most approximately 0.066. Minima outside the selected angular window are not drawn.
- **Interface:** Snell's law for homogeneous, isotropic, nonabsorbing media, with angles measured from the normal. `n = c/v` uses the exact SI vacuum light speed. The diagram shows directions; ray lengths and widths do not encode optical power. Above the critical angle the propagating transmitted ray is absent. The evanescent field is explicitly omitted. The critical numerical comparison uses eight machine epsilons on the dimensionless sine ratio.
- **Film:** one lossless, plane-parallel film at normal incidence, with wavelength-independent indices. The spectral reflectance includes all coherent internal reflections. Signed boundary field-reflection coefficients retain phase inversions. A zero reflection has no phase label. At zero thickness the layer vanishes; the readout identifies only the direct air/substrate interface and suppresses phase labels for the absent layer. The explicit vertical scale can be 0–100%, 0–25%, 0–10% or 0–5%; values above the selected range are clipped and disclosed. This is spectral reflectance, not a prediction of perceived colour, illumination, dispersion or actual oil composition.

All calculations use binary floating-point arithmetic. Displayed numbers use six significant digits. The lens core's wider numerical domain is used for algebraic stress tests; only its UI parameter domain is asserted to keep ray slopes at most 0.1. All pure model APIs reject unsupported domains, nonfinite values, strings, null and non-object argument containers.

## Evidence and reproduction

`node tools/check_optics_core.cjs` checks 14,400 lens states and 105 slit states against the lens relation, independent ray intersections, focus limits, quiz examples, slit minima, intensity bounds/symmetry and narrowing/widening behavior.

`node tools/check_optics_interfaces.cjs` checks 4,500 interface states and 18,180 film states. The film reflectance is independently compared with an 80-term coherent internal-reflection series; zero-thickness and index-matched quarter-wave limits are included. Refraction checks include critical-angle neighbors and Cartesian unit ray directions.

`node tools/check_optics_contract.cjs` rejects 153 invalid inputs and checks all 8,832 supported lens UI states, including the slope limit and finite image values outside exact focus.

With Playwright available through `NODE_PATH`, run:

```
node tools/check_optics_browser.cjs
node tools/check_optics_rendered.cjs
```

The first mounts the actual physics renderer with current styles and authored lesson metadata. It exercises ten lens preset/viewport combinations, equal-axis switching, enlargement of all four plots, invalid-input recovery, preserved interference controls and no horizontal document overflow. Two mounted optics instances have unique IDs; another physics scenario does not receive the optics companions. Screenshots are from this integrated renderer. The second checks ten actual refraction SVG geometries and 270 curve cases across both viewport sizes and all film scales. At 19 dense interior evaluations per segment, maximum observed interpolation errors are 0.020272 SVG units for diffraction and 0.020723 for film. This is numerical evidence, not a formal global error bound. No page errors were observed.

For authenticated delivery, start an isolated server and run the reader verifier:

```
python tools/start_optics_reader.py --fixture .research/optics-fixture.json
node tools/check_optics_reader.cjs .research/optics-fixture.json
```

Stop the server after verification. The fixture uses random synthetic credentials, a fresh temporary database/content/backup directory, explicit empty Turso configuration and loopback binding. `reader-proof.json` records 32 states at 390px and 1440px, checks exact served startup-bundle bytes, preserves the existing interference behavior, and verifies the complete authored physics curriculum file is unchanged. The node API continues to omit quiz answers. This is local synthetic-account evidence; no authenticated production learner-flow claim is made.

## Historical boundaries and remaining work

`runtime-inverse.json` records the exact three-line optics attachment in the shared lesson renderer. `tools/optics_runtime_compatibility.py` accepts only the recorded before/after hashes and exact literal reversal. The older dipole, calibrated-wave and other historical reviews retain their original evidence. No existing clinical or historical approval is extended.

This review establishes these four scoped optics additions under their declared assumptions. It does not certify the optics module, validate the existing raster illustration, prove all spatial two-source interference behavior, or establish whole-curriculum/clinical completeness. Full regression, CI and production delivery evidence are recorded separately as release work completes.

## Primary sources

- [OpenStax: thin lenses](https://openstax.org/books/university-physics-volume-3/pages/2-4-thin-lenses)
- [OpenStax: single-slit intensity](https://openstax.org/books/university-physics-volume-3/pages/4-2-intensity-in-single-slit-diffraction)
- [OpenStax: total internal reflection](https://openstax.org/books/university-physics-volume-3/pages/1-4-total-internal-reflection)
- [OpenStax: thin-film interference](https://openstax.org/books/university-physics-volume-3/pages/3-4-interference-in-thin-films)
- [MIT 2.627: normal-incidence coherent single-film reflectance, slide 34](https://ocw.mit.edu/courses/2-627-fundamentals-of-photovoltaics-fall-2013/044e9c8d1cda6823e4b7c54309effd99_MIT2_627F13_lec03.pdf)
