# Physics illustration review

Current scope: all 39 lesson images inspected at 800px against their
curriculum descriptions. Per-lesson observations and responsive asset fingerprints are in
`illustration-reviews.json`.

## Corrections

Nine native plates received concrete changes:

- Floating/sinking: a submerged clay ball and broad hollow hull now explain
  excluded water; the caption discloses a schematic, non-volume-scale section.
- Simple machines: the load rests on the ramp and the effort label fits.
- Magnets: paired attraction arrows and genuinely closed field loops replace
  one-way attraction and disconnected arcs. External and internal directions
  are explicitly opposite, N-to-S outside and S-to-N within the bar.
- Forces: the crate's 4 N and 9 N arrows use the same scale and labels clear it.
  A filled helmet/jumpsuit replaces the stick marker at terminal speed.
- Gravity: inward-force and tangent-velocity labels no longer obscure the orbit.
- Electricity: removed a rail-to-rail short across the parallel loads and moved
  labels off wires. Both bulb branches now interrupt their respective paths.
- Waves: the lower amplitude caption clears its border.
- Matter: all three phases preserve 20 identically styled particles, with close
  condensed spacing versus a gas distributed through the vessel.
- Measurement: the ruler now has 0, 5 and 10 labels, supporting its stated reading.

The two authored light images and the remaining six native plates were preserved.
They provide concrete shadow, dispersion, force, thermal-equilibrium, motion,
sound, energy-accounting and heat-transfer explanations.

## Verification and limits

The later-stage pass corrected thirteen additional native plates. The collision
panel now works through a fully inelastic example: 8 kg m/s before and after,
with kinetic energy decreasing from 16 J to 32/3 J. Its velocity arrows share a
scale. The Carnot formula and axes are separated. Free-particle and oscillator
examples are distinguished; the oscillator axes cross at zero and its flow
direction satisfies Hamilton's equations. The light-cone time axis passes
through its vertex.

Other corrections add a quantum zero line and synthetic-data disclosure,
fair-coin assumptions and group labels, unobscured semiconductor holes,
scatter/bias labels, bounded beta-decay claims, clear cosmology/Meissner/state
labels and separated rotation-curve annotations. Cosmological separations and
wavelength both double in the illustrated end-to-end comparison. All final
changed rasters were inspected at 800px; this is not an enlarged-browser audit.

Five regression tests check closed field paths, ramp contact, hollow-hull/ball
placement, wire-only battery connectivity and phase particle count/spacing.
The circuit test walks the actual rendered wire centre-lines: the supply terminals
must not connect without crossing a load. This would fail for the removed shunt.

Four further regressions check collision velocity scaling, oscillator flow,
light-cone origin and matching expansion/wavelength factors. Twenty focused
physics/cohort/review tests pass. The physics asset checker passes
for all 39 lesson pairs and 78 responsive rasters. These checks do not certify
all enlarged browser views or model states.

Overall review coverage is now 197/432 current records. Remaining subject review,
model-appropriateness assessment, final runtime verification and deployment are
still unfinished.
