# Calibrated galaxy rotation and disk density

The frontier lesson replaces arbitrary curve-amplitude controls and a generic detector companion with one calibrated rotation/density activity. All authored goals, prose and assessments remain unchanged. This activity addresses circular-speed inference; it does not complete the lesson’s quantum-gravity topic or the whole Primer fidelity goal.

The physical model combines a Miyamoto–Nagai disk with a spherical NFW halo. Radius is in kpc, speed in km/s, and mass uses the IAU nominal solar conversion. Halo scale mass is not total or virial mass; an untruncated NFW halo has divergent total mass. The plotted interval is finite. Synthetic observations are a fixed seeded Gaussian-noise realization with assumed sigma 8 km/s. Their bars are one standard deviation, not fitted-parameter confidence intervals. The mismatch is a weighted squared residual, with no p-value or uniqueness claim.

The 3D disk surface follows 10% of the current central density. It is an iso-density contour, not a material boundary or total extent. Coordinates retain the same scale on each axis. Mesh checks sample triangle centroids and edge midpoints; the stated tolerance is not a rigorous continuous bound. Equal a+b with fixed masses/halo produces an exact within-model midplane-curve degeneracy while the 3D density changes.

`runtime-core-proof.json` checks the shipped core against independent halo-density integration and potential gradients. `reader/` captures the actual authenticated synthetic app, including plot coordinates, uncertainty bars, GPU buffers and camera scale. `prototype/` preserves the earlier standalone experiments and their recipes; those are not claims about the final application bytes. The current reader proof pins its runtime sources separately.

Run `tools/check_rotation_core.py --output <temporary-json>` for the current core, and `tools/check_rotation_geometry.py`, `tools/check_rotation_comparison.py`, and `tools/check_rotation_app_gpu.cjs` for independent checks of captured actual-reader output. The browser runner `tools/check_rotation_app.py` uses temporary synthetic data and performs no production learner writes.

Primary model documentation: https://docs.galpy.org/en/v1.12.0/tutorials/potentials/introduction.html and https://docs.galpy.org/en/v1.5.0/reference/potentialnfw.html . Unit definitions: the IAU 2015 Resolution B3 and CODATA gravitational constant references are retained in `prototype/units-review.json`.
