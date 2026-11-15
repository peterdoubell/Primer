# Chemistry illustration review

All 29 current 800px plates were inspected against curriculum descriptions.
This is a lesson-resolution content/layout pass, not certification of every
high-resolution browser view or interactive-model state.

## Corrected native plates

- Mixing: all 24 sand grains now stay inside their beaker.
- Materials properties: the hot attachment is correctly a pan handle rather
  than a fridge handle; its grip is labelled cooler, not categorically cool.
- Mixtures: the solvent-collected label wraps inside the distillation panel.
- Periodic table: the chlorine reactivity label clears the shell configuration.
- Stoichiometry: initial, consumed, produced and remaining amounts use moles
  consistently, including the conserved element-amount ledger.
- Gas laws: the two isotherm legends have separate rows.
- Physical chemistry: catalyst routes are named and the equilibrium explanation
  no longer crosses the sidebar divider or oversimplifies K as a plain ratio.
- Analytical chemistry: the signal-axis label no longer sits behind peak A.
- Advanced biochemistry: the x-axis title clears tick labels; the footer explains
  the displayed Michaelis–Menten half-maximum/saturation relationship.
- Materials chemistry: one radius-56 sphere is compared with eight separated
  radius-28 spheres, preserving total volume and doubling total surface area.
- Computational chemistry: minimum labels and the convergence caption are clear;
  the spectrum comparison is explicitly illustrative, not measured data.
- Frontiers: upstream accounting text stays within the system boundary, and
  product metrics are clear of the product-flow arrow.

Eight lessons' descriptions were aligned with their actual pictured examples:
materials, changes, material properties, mixtures, atomic structure, energy,
computational chemistry and frontiers. Accurate existing diagrams were preserved,
including the authored element specimens, atom-conserving reactions, pH activity
ratios, SN2 inversion, octahedral splitting, H2 molecular orbitals and galvanic flow.

## Verification and limits

The focused chemistry regressions inspect actual rendered grain coordinates,
pan-handle labels, nanoparticle radii and separation, font bounds for legend rows,
and stoichiometry unit labels. The broader science glyph test checks all 85
generated natural-science plates using the actual selected fonts. Asset integrity
and deterministic rendering are separate from these conceptual checks.

Twenty-one focused chemistry/biology/review tests pass. The natural-science
checker verifies all 93 lessons and 186 responsive rasters, with deterministic
regeneration for its 85 generated plates; the global inventory remains 432
illustrated lessons and 864 responsive WebPs.

Per-lesson observations and current media fingerprints are recorded in
`illustration-reviews.json`. Remaining subjects, final browser/model verification
and deployment are not claimed complete by this report.
