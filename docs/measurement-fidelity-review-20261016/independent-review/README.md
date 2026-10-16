# Independent numerical regression

The final independent scientific review and its raw API/exact-rational receipts are preserved byte-identically here. They apply to `web/measurement-lab.js` SHA-256 `8a1d68588bb9689146a5673c1d2f7f7b4fad10213f53c10f47c4d1c35bd537af`. The original research-location strings in those receipts document provenance; they are not runtime inputs.

Two defects discovered in independent review are resolved: a large absolute x origin previously corrupted small centered moments, and extremely small x spacing previously returned infinite parameter covariance. The exact-rational fit now remains invariant under translating the coordinate origin, and unrepresentable covariance raises a clear request to rescale x.

## Run the regression checks

From the repository root, with Node.js and the project Python dependencies available:

```sh
node tools/check_measurement_core.cjs
python tools/check_measurement_independent.py
python -m pytest tests/test_measurement_lab.py -q
```

Both numerical checkers print JSON results to stdout. Their normal execution writes no proof files. The pytest wrapper removes proof-writing environment flags, uses bounded subprocess timeouts and verifies that the entire measurement evidence directory remains byte-identical.

`tools/check_measurement_independent.cjs` reads the one fixed repository module and a JSON request array on stdin, then returns JSON on stdout. Only the five reviewed pure methods are callable. It accepts no filesystem path from arguments, environment variables or stdin. The Python checker generates all requests itself and bounds its Node subprocess to 30 seconds; pytest bounds each complete checker to 60 seconds.

To deliberately refresh only the portable independent receipts at their fixed destination:

```sh
python tools/check_measurement_independent.py --write-proof
```

That flag writes `api-results.json`, `exact-fit-receipts.json` and `review.json` only under `independent-review/regression-output/`. It never overwrites the preserved original review, core proof, renderer proof or authenticated-reader proof. The pre-existing core checker has its own explicit `MEASUREMENT_WRITE_PROOF=1` mechanism; the regression tests do not enable it.

## Independent oracles

The promoted checker retains all scientific fixtures and independent methods from the final review:

- Complex-step sensitivities and covariance quadratic forms, including common-effect cancellation and signed cross terms.
- Rational endpoint extrema for negative/zero-crossing voltage domains and positive length/time ratio and inverse-square domains.
- Gauss–Legendre integration of the declared rectangular rounding model, combined with independent/shared averaging responses.
- Exact rational weighted normal equations and covariance inversion, including predictions, residuals, χ², degrees of freedom and leverage.
- Residual-amplitude and supplied-σ rescaling tests that distinguish known-σ covariance from a residual-scaled estimate.
- Both numerical-regression fixtures, invalid domains and retained synthetic-case assumptions.

The independently accepted scientific scope covers these APIs and declared domains. It does not establish renderer behavior, production delivery, arbitrary numerical domains, empirical independence of the synthetic observations or whole-module completeness. Renderer and authenticated-reader verification remain in their separate frozen evidence directories.
