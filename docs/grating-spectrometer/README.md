# Sodium reference-line grating spectrometer

The existing Waves and Optics lesson contains single- and two-slit teaching models, a lens bench and a polariser activity. Its registry had no finite multi-groove spectrometer or reference-line resolution comparison. This additive activity links from `phys.3.optics-waves` and `phys.4.experiment`, retaining all existing entries and the normal reader entry/return route. It does not change the curriculum, server, renderer APIs or historical inverse chains.

## Reference data

`source-receipt.json` pins the unmodified public NIST response bytes, losslessly gzip-compressed alongside this note, with both transport and decoded hashes. The persistent-line table supplies the two Na I wavelengths, the strong-line table labels the visible range as air wavelengths, and the reference page identifies R56 as P. Risberg, *Ark. Fys.* 10, 583 (1956). Exact Å-to-nm conversion gives 588.9950 and 589.5924 nm. Their separation is 0.5974 nm. The handbook explicitly points to newer, higher-accuracy sodium work; this activity retains the source digits rather than claiming modern metrological accuracy or inventing uncertainties.

The wavelength facts are separate from modelled optical profiles. No captured spectrum, measured detector trace, noise data or lamp intensity ratio is supplied. Equal component weights are a stated demonstration condition, not a claim about the source's measured line powers. Blue/coral identify mathematical component curves; both physical lines are yellow.

## Physics and dimensions

The interference factor is the squared magnitude of the coherent sum from N identical, uniformly illuminated, very narrow equally spaced grooves. Its closed form uses a phase remainder for numerical stability and the correct unit limit at a principal maximum. The two different wavelengths are mutually incoherent, so their normalized intensities, rather than amplitudes, are averaged.

Normal-incidence directions use `sin(theta) = m lambda / d`, with air wavelengths and SI pitch. Values at grazing incidence or beyond are excluded from the forward telescope view. An ideal infinity-focused telescope samples angular diffraction; the model does not put a bare screen in a falsely assumed far field. The detector coordinate is the explicitly stated ideal rectilinear map `x = f tan(theta - theta0)`, centred on the mean principal direction. Pixel calibration inverts that map exactly. Hardware drawings are schematic and enlarged; the computed ray angles and detector axes have their declared units.

The pixel width is a real model dimension. Its response is an average across that interval, not a sample at its centre. Midpoint integration uses at least 24 subdivisions per conservative minimum fringe pitch `f lambda/(N d)`; this also sets the optical curve sampling. Absolute optical flux, finite groove-width efficiency, source line width, aberrations, entrance slit width and noise are omitted.

More grooves narrow each peak without moving its principal direction. More groove density **at fixed N** increases both angular separation and angular width; the ruled width decreases and the grating resolving power `|m|N` stays fixed. Increasing focal length magnifies the detector image and can improve sampling without changing that grating criterion. Larger pixels can hide structure even when the ideal narrow-separation, equal-line Rayleigh estimate is met. The plot keeps one fixed vertical normalization and a finite 1.2 mm field; off-sensor centres are explicitly reported.

At the default settings (600 grooves/mm, N=600, m=1, f=300 mm), the principal angles are 20.6952321574° and 20.7171874427°, separated by 0.383192 mrad. The detector separation is 0.1149576063 mm. The ideal required resolving power is about 986.43; N=600 in first order falls below it, while N=1600 or N=600 in accessible second order exceed it.

## Verification

- `node --test tests/grating-spectrometer.test.mjs` checks the closed form against direct complex-wave sums, first zeros and maxima, the two-groove limit, dimensions, density versus aperture changes, calibration inversion, contiguous detector bins and invalid/grazing orders.
- `tests/fixtures/grating-spectrometer-reference.json` supplies 13 independently integrated pixel responses, including a deliberately demanding wide-pixel/narrow-peak case. The production calculation differs from direct N-groove phasors plus SciPy adaptive quadrature by at most 3.46e-5 in normalized component response, below the test's 1.5e-4 absolute tolerance. This numerical tolerance is not a measurement uncertainty.
- To reproduce the independent fixture (authoring-only NumPy and SciPy environment): `python tools/physics_sources/verify_grating_spectrometer.py`. Use `--write` to regenerate the committed reference fixture. The default checks it.
- `python -m pytest -q tests/test_grating_spectrometer.py tests/test_lesson_activities.py tests/test_learning_games.py` validates the model, original source receipts, existing activities and normal learning-sequence inventory.
- `python tools/learning_games_inventory.py --check` and `python tools/learning_games_report.py --check` verify the shared inventories. Registry links do not require adding an obsolete hard-coded reader link.

Local browser verification uses an isolated synthetic reader database and the real app at both 390 and 1280 pixels: both lesson links/returns, controlled comparisons, finite detector readings, physical pixel clicking and keyboard selection, forbidden-order clearing and recovery, and horizontal overflow. No external source requests or server writes are needed by the lab at runtime.
