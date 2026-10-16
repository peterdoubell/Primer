# Independent linear algebra review

This review covers the declared `math.4.linalg` workbench: matrix actions and composition, linear systems, affine planes, span/rank/volume, four-coordinate kernels, declared spectra, and repeated powers. It preserves the distinction between exact rational algebra and approximate drawing coordinates/norms. Authenticated lesson mounting and preservation of the original five-map activity are checked by the separate reader proof.

The numerical checker uses Python `Fraction`, exact permutation minors, independent largest-pivot elimination, sequential multiplication, shoelace/triple-product geometry, and independently constructed cube/plane intersections. It does not use the product API to calculate expected values. The source supports small rational matrices and specified spectral fixtures; this review does not claim a general numerical or complex eigensolver.

The browser checker derives expected geometry from ordinary-control state through the Python oracle. It compares actual SVG vertices, projection matrices and axes with that oracle, verifies complete exact coordinate/orbit tables and invalid-state clearing, and checks numeric SVG labels and document overflow. Its exported `captureSnapshot` and `verifySnapshots` helpers are also available to the authenticated reader check.

The exact nonnormal counterexample is `A = [[1/2,10],[0,9/10]]`, `v0 = (0,1)`. The full sequence follows `vn = (25((9/10)^n-(1/2)^n),(9/10)^n)`. In particular, `v2 = (14,81/100)` has norm about 14.0234; `v3 = (151/10,729/1000)` has norm about 15.1176. The finite trace peaks at n=3. The test does not confuse the second and third iterates.

Independent review found two teaching defects, both corrected before the final source pin: a 4D determinant described as an ordinary area factor, and abbreviated coordinates described as exact. Regression checks now require dimension-specific volume wording and full exact coordinate ledgers. Independent numeric-label containment additionally caught the near-singular phone tick expanding to a long decimal; the final formatter preserves scientific notation. Root's orbit-label and non-decay slow-mode wording findings are also included in the final renderer checks. No remaining actionable defect was found within the declared scope.

## Reproduction

From the repository root, with Python 3 and Node available:

```sh
python3 tools/check_linear_algebra_independent.py
node tools/check_linear_algebra_core.cjs
```

The independent Python command runs all numerical requests against the fixed repository module. Add `--write-proof` to refresh its three named numerical receipts. The `purePrefixSHA256` hashes the source before `function render(`; `sourceSHA256` pins the complete module and is the authoritative version identity.

For browser verification, install/use Playwright through the normal environment and run:

```sh
node tools/check_linear_algebra_independent.cjs --browser
```

Add `--write-proof` to refresh the named renderer receipts/screenshots. The verifier uses `python3` by default. On the local scientific runtime, set `PRIMER_INDEPENDENT_PYTHON=/Users/peter/Documents/ChatGPT/Primer/.research/runtime-grade-py312-20261008/bin/python`; no arbitrary executable/file-path arguments are accepted.

`renderer-review.json` holds the source identity, each checked state and verification outcome. Complete raw snapshots are stored losslessly as `renderer-snapshots.json.gz`, with compressed and decoded SHA-256/length recorded in that receipt. Decode with Python `gzip.decompress`, verify both identities, then parse the JSON array. These are archival observations, not executable runtime resources.

The default commands print results and do not overwrite proof files. `final-review.json` pins the source, checker files and final evidence. Browser observations are bounded acceptance evidence, not a claim to have sampled every rational input.
