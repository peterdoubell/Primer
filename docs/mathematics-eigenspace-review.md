# Linear algebra representation review

The linear algebra goal names vector spaces and eigenvalues. The existing plane
transformation and determinant activity did not represent eigenspaces. Its new
companion uses the same five fixed matrices, retaining the original grid and
area activity. Both grid panels now share a labelled coordinate scale chosen
to contain every transformed grid corner; stretch and shear previously clipped
the outer transformed grid.

| Matrix | Eigenvalues, with multiplicity | Eigenspaces | Rank / nullity |
|---|---|---|---|
| Identity | 1, 1 | Whole plane, dimension 2 | 2 / 0 |
| x stretch | 2, 1 | x and y axes | 2 / 0 |
| x shear | 1, 1 | x axis only; no eigenbasis | 2 / 0 |
| Reflection across x | 1, −1 | x and y axes | 2 / 0 |
| Projection onto x | 1, 0 | x and y axes | 1 / 1 |

An independent unit probe links the vector and image to scalar projection qv
and perpendicular residual r. The readout states that q is an eigenvalue only
when the residual is exactly zero for a nonzero probe. Negative eigenvalues
reverse the vector; zero eigenvalues map an eigenvector to zero. The identity's
two-dimensional eigenspace is distinguished from the shear's defective repeated
root. Column-space and kernel bases, their dimensions and rank-nullity appear
beside the plot. Both plots use dimensionless coordinates.

The artwork and code are original. Definitions are consistent with
[MIT's eigenvalue/eigenvector teaching](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/pages/least-squares-determinants-and-eigenvalues/eigenvalues-and-eigenvectors/).
No course artwork or video is redistributed.

The independent checker verifies 185 states against characteristic-polynomial,
eigenpair, kernel, rank-nullity and orthogonal-decomposition identities, then
checks another 185 actual mounted vector endpoints after control events. It
explicitly checks negative and zero eigenvalues, the defective shear, equilibrium
image, enlargement and reset. This is a five-matrix activity, not a general
floating-point eigensolver, higher-dimensional basis construction, or proof of
complete visual coverage of every linear algebra topic.

Independent actual-app browser review checked all five matrices at 0°, 45°, 90°
and 180°: 20 probe states and 400 original/transformed grid lines agreed with
independent coordinate and signed-area calculations. Desktop and 390px views,
internal enlargement, reset, zero images, negative eigenvalues and defective
shear passed. The full light plot background keeps signed ticks and axis titles
legible. Captured activity speech text includes the current values, separate
probe explanation and circle key; audio pronunciation was not assessed. Local
proof is retained in `.research/math-eigenspace-browser-review`.
