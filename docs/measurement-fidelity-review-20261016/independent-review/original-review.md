# Independent scientific review: measurement workbench

The reviewed pure API passes the independent calculations below after two concrete numerical defects were found and corrected by the implementation agent. This review did not modify product code, tests, docs, Git or deployments. It does not claim renderer or whole-physics-module verification.

## Defect found and resolved

`weightedLineFit` originally restored a large absolute x mean before forming small centered deviations. For valid inputs

- x = [999999, 999999 + 2⁻³³, 999999 + 2⁻³²]
- y = [1, 2, 4]
- σ = [1, 1, 2]

it returned χ² = 0.466666666666667 and a leverage of 1.244444…, rather than the translation-invariant χ² = 1/9 and fitted values [8/9, 20/9, 32/9]. A leverage above one contradicted the weighted projection calculation. The same data translated to x near zero returned the correct result.

The implementation now retains mean offsets and centered coordinates before restoring absolute origins, including for y residuals. The independent exact-rational oracle verifies the translated and untranslated cases, large-y/small-variation case, coefficients, covariance, predictions, residuals and hat-matrix leverage/rank. The original read-only reproducer is `probe.cjs`; current results are in `api-results.json` and `exact-fit-receipts.json`.

## Independent calculations

| Area | Check method and result |
|---|---|
| Standard propagation | Complex-step derivatives and direct covariance quadratic forms agree, including positive/negative covariance, exact common-effect cancellation and zero-output relative-uncertainty handling. Sum/difference are linear; ratio and inverse-square are clearly first-order. |
| Exact input bounds | Rational endpoint extrema derived from monotonicity agree for negative and zero-crossing sum/difference domains and positive ratio/inverse-square domains. Zero-crossing denominator bounds and inputs outside the declared physical domain reject. These are rectangular set bounds, not standard uncertainties or probability intervals. |
| Resolution | Three-point Gauss–Legendre quadrature independently integrates the declared uniform ±Δ/2 rounding model. Δ/√12 is conditional on that distribution, not inferred from resolution alone. |
| Repeats | Averaging response vectors distinguish independent repeat effects from common effects. Shared calibration/rounding does not shrink; independent rounding does. The already-in-scatter mode adds no duplicate rounding term. |
| Bias correction | Correcting the recognized synthetic offset changes the signed expectation/error, not the variance components. An uncorrected offset is not relabelled as standard uncertainty. |
| Weighted line fitting | Exact rational design normal equations and matrix inversion agree for heteroscedastic and uniform known σ, negative/positive x, large origins and fixed reference models. Covariance, χ², degrees of freedom, predictions, residuals and leverage are checked independently. |
| No residual rescaling | Multiplying an orthogonal residual pattern by 64 leaves parameter covariance unchanged while χ² increases by 4096. Multiplying every supplied σ by four multiplies covariance by 16 and divides χ² by 16. |
| Synthetic examples | All 12 observations remain. A common offset is absorbed by a free intercept with unchanged residual χ². The fixed pattern is explicitly synthetic, not evidence of random independent sampling. |

`check.py` uses a fresh Node VM evaluation of one exact source snapshot through `run_api.cjs`. The scientific oracle uses Python `Fraction` algebra, NumPy linear operations, complex-step derivatives and quadrature. It does not import or reuse the implementation’s sensitivity or covariance routines. The API prefix before the default renderer state is hashed separately so later renderer-only work cannot be mistaken for a change in the checked scientific functions.

## Assumptions and limits checked in the authored explanation

The API treats x as exact and the supplied y uncertainties as known and independent. A χ²-distribution interpretation additionally needs Gaussian errors and the correct mean model. Fitted residuals are correlated. Reference-line coefficients have zero uncertainty by assumption, rather than because a fit established them. Standard uncertainties are not guaranteed bounds; nonlinear first-order propagation does not bound a denominator or guarantee adequate linearization. The pendulum relation is an ideal small-amplitude model. The interval API covers only its declared monotone physical domains, not unrestricted signed division or arbitrary powers.

These meanings agree with [NIST TN1297 Appendix A](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-law-propagation-uncertainty), [section 4 on distribution assumptions](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-4-type-b-evaluation-standard-uncertainty), and [section 5.2 on systematic corrections](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-5-combined-standard-uncertainty). The fit criterion is consistent with [NIST’s weighted-least-squares description](https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd432.htm). Exact known-σ parameter covariance was independently derived as (XᵀWX)⁻¹; no unknown residual scale was estimated.

The second pure-API boundary issue is resolved in the frozen source. Inputs x=[0, 10^-155, 2×10^-155] and x=[0, 10^-160, 2×10^-160], y=[1,2,3], σ=1 now raise an explicit RangeError asking for x rescaling; they do not return infinite covariance. The large-origin fit correction remains valid. No remaining substantive defect was identified within the independently checked APIs and declared domains. Browser/renderer fidelity and final integrated-reader behavior remain separate checks.

## Final pinned disposition

All independent checks passed against frozen `web/measurement-lab.js` SHA-256 `8a1d68588bb9689146a5673c1d2f7f7b4fad10213f53c10f47c4d1c35bd537af`, verified unchanged before and after the run. `review.json` records both resolved defects, exact rejection messages, calculation methods and remaining verification scope. No renderer or full-module-completeness claim is made.
