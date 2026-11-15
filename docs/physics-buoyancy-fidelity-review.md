# Floating and sinking: hydrostatic model review

The previous `phys.0.float-sink` interaction compared dimensionless force ratios
at full immersion. It supplied no displaced-water geometry, floating depth or
newton calibration. Its companion 3D particle chamber explicitly did not model
buoyancy. Both are replaced with physical representations of one rigid sealed
square-base prism. The existing illustration remains a separately labelled
schematic example of a clay hull; no unreviewed raster is substituted.

The section activity predicts partial floating equilibrium when the object is
less dense than the liquid. Equal densities admit any fully immersed depth,
with no selected restoring depth. A denser object has no free floating
equilibrium; its illustrated fully immersed position is explicitly a test
snapshot, not a stable position or a simulated fall. Held-depth mode supplies
the signed external force needed to keep any displayed position fixed.

Mass, volume, height, liquid density, gravity and held depth are independently
controlled. The elementary volume control and three fixed-mass examples are
available immediately; additional parameters are under an expandable section.
The 3D view has separate held-depth controls and is explicitly independent of
the equilibrium-prediction view. Its binding and generator now use the
`buoyant-prism` family instead of the unrelated particle chamber.

## Equations, geometry and physical limits

For prism height H, square-base area A=V/H and bottom depth d measured downward
from a fixed liquid surface:

    h_sub = clamp(d, 0, H)
    V_displaced = A h_sub
    p_bottom = ρ g max(d, 0)
    p_top = ρ g max(d − H, 0)
    B = A(p_bottom − p_top) = ρ g V_displaced
    W = m g
    F_holding = W − B                 (positive upward)

Lengths are converted from cm to m, volumes from cm³ to m³ and masses from g to
kg before SI pressure/force evaluation. Pressures are gauge values relative to
the common surface air pressure. Opposing lateral pressures cancel. Free
floating requires d/H=ρ_object/ρ_liquid, and mathematically balanced predictions
display zero imbalance rather than a binary floating-point arithmetic residue.
The pressure-based and displaced-mass calculations are independently compared.

The section uses the same fixed scale in both length directions: 8 SVG units/cm.
Its shown width also specifies the out-of-plane width, so the displayed prism
preserves volume. Submerged colouring is a fraction of the sealed object, not
water entering it. All section force arrows share 30 SVG units/N, with a fixed
±5 N axis containing the complete control range. They never saturate.

The 3D geometry uses one coordinate unit per 10 cm, with true square-base and
height dimensions. Exposed and submerged faces partition a single closed
prism without overlapping volumes or added internal cap faces. The plane/grid
marks a window of the free liquid surface, with 5 cm grid spacing. It does not
claim a tank wall or bottom. Force arrows use 0.15 coordinate units/N; they are
separated sideways for legibility and do not claim distinct attachment points
or torques. Camera projection and zoom do not change physical geometry.

Both activities assume a large, uniform-density liquid reservoir, fixed vertical
orientation, rigid sealed geometry and symmetric mass distribution. Air
buoyancy, surface tension, flooding, compressibility, rotation, waves, drag and
transient fluid motion are omitted. The static imbalance predicts force
direction if released, not acceleration or a complete motion trajectory.

The governing result is [Archimedes’ principle and hydrostatic pressure,
OpenStax University Physics §14.4](https://openstax.org/books/university-physics-volume-1/pages/14-4-archimedes-principle-and-buoyancy).
Code, diagrams, numerical cases and verification are original. No textbook
figure or noncommercial media asset is copied into Primer.

## Verification evidence

The direct-module checker compares 7,776 hydrostatic states against independent
SI calculations and horizontal-face pressure integration. It covers dry,
partial and full immersion, free prediction versus held depth, density/height/
gravity extremes and neutral-depth nonuniqueness. Seventeen mounted states
check actual rectangle coordinates, displaced volume, fixed force-arrow
lengths, all controls, presets, reset and enlargement. Fifty-four 3D states
check oriented closed-surface volume, physical bounds, submerged volume and
every segmented force-arrow shaft against its stated newton scale.

The existing module-model checker verifies 462 exact lesson bindings, 42 object
families, 90 controls and 3,204 deterministic builds. All other 461 bindings
remain unchanged, and the generator reproduces the complete current manifest.
The retained physics checker still verifies the other 35 concept scenarios,
66 controls and 22,137 equation/geometry assertions.

The actual local lesson route passed at 1440 and 390 CSS pixels. Each viewport
checked 19 section/control states and 12 3D control extrema, reset, keyboard
rotation, enlarged internal scrolling, complete SVG text bounds and absence
of page overflow. API bindings and four served script/style hashes matched
the reviewed source. The actual read-aloud button preserved the complete
visible numeric readout. Browser errors were empty. These are local checks;
authenticated production interaction is a separate verification boundary.

This corrects concrete physical representations in one lesson. It does not
approve every physics lesson, the 59 mathematics lessons or the complete
radiology scope. The full thread goal remains active and unproven.
