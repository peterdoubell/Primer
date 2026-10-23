# Shapes All Around: sides and corners

The supplementary model for `math.0.shapes` previously showed a simple-cubic crystal lattice. The lesson goal is to identify circles, triangles and squares and count their sides. The new binding shows those flat shapes, plus a non-square rectangle for comparison. The existing lesson illustration and shape-wheel activity remain available.

Each polygon boundary uses its actual vertices and closed edge sequence. Rotation and uniform scaling preserve lengths, right angles and intrinsic area. Polygon corner markers are drawing aids. The circle has no mathematical straight sides or corners; its display uses 360 chords. The maximum radial drawing error is `r(1 − cos(π/360))`, less than 0.000058 model units throughout the size control. No source imagery or clinical anatomy is represented by this mathematical construction.

The default camera cancels the shape-plane tilt, so a square initially looks square and a circle round. The camera can then be rotated independently. Reset view returns to the face-on view. The scene explains the effect of viewing a flat circle at an angle.

## Verification

- `node tools/check_plane_shapes.cjs`: 1,100 states. Independently checks boundary closure, plane equation, side and corner counts, side lengths, perpendicular adjacent edges, shoelace areas, circle radii and chord midpoint error.
- `node tools/check_module_models.js`: 462 bindings, 64 families and 16,881 deterministic builds passed. Existing geometry assertions remain in place.
- `tools/check_plane_shapes_browser.cjs`: actual shared SVG renderer and shipped lesson binding, 48 states at each of 390 and 1440 pixels. Checks visible controls, view-box containment, page overflow, reset, keyboard camera and browser errors. Screenshots are saved for all four shapes at both widths; square phone view visually inspected. `browser-proof.json` pins the rendered runtime sources.
- Generator rerun changes only the intended lesson binding. It also now retains the previously authored exact-arithmetic number-theory companion, which the old generator would have replaced with a generic lattice.

The standalone browser harness does not establish production delivery. A separate authenticated-reader check (`tools/check_plane_shapes_reader.py`) passed at 390 and 1440 pixels using isolated synthetic storage: all four shapes, preserved original shape wheel, anonymous access rejection, reset, no page overflow, no CSP violations or page errors, and actual startup bundle identity. `reader-proof.json` records that evidence. Full regression and release checks are recorded separately. This is one improvement within the wider incomplete radiology, mathematics and physics objective.
