# Five whole-number lessons: calibrated units, places and groups

Place Value, Addition, Subtraction, Multiplication and Division now have lesson-specific whole-number workbenches and calibrated 3D companions. The original five illustrations, five teaching activities, all 35 quiz items, prerequisite lists and child-facing text remain. The new examples cover every original assessment calculation. New teaching sections explain the models and their bounds.

## Exact calculations and different meanings

The arithmetic core accepts bounded nonnegative whole-number inputs and uses exact integer arithmetic within JavaScript's safe integer range. The place reader covers 0–9999, including zero placeholders. The repeatable exchange ledger covers totals through 200; exchanges are closed within those bounds and preserve total value. Addition and subtraction operands cover 0–999. Multiplication covers all factors 0–12, and division covers totals 0–144 with divisors 0–12. Malformed inputs and cross-lesson modes are rejected.

Addition shows equal-place sums, incoming carries, result digits and outgoing carries. Subtraction distinguishes taking away from comparing amounts. The borrowing ledger computes the nonnegative gap using larger minus smaller; the signed A − B equation is stated separately. A request larger than the available amount has an explicit shortfall, rather than negative physical counters. Multiplication shows every counter in the array and its repeated-addition interpretation. Sharing fixes the number of groups; grouping fixes the group size. Whole-object quotients and remainders remain distinct from the exact fraction for continuously divisible quantities. Division by zero has an explicit undefined state with no stale diagram.

The SVG charts use labelled linear axes or individually counted unit tiles. A stack segment's width encodes its contribution in unit values, not its piece count. Before/after rows share one scale. Digit and operation ledgers give exact values. Large diagrams scroll vertically or horizontally; arrays fit a compact phone layout and can be enlarged. Invalid drafts preserve accepted calculations and speech, and Escape restores the accepted input. Swapping amounts and applying/reversing an exchange update through the same core validation.

## Calibrated 3D quantities

One unit cube has dimensions 0.2 × 0.2 × 0.2 in world coordinates. Ten rods use 2 × 0.2 × 0.2; hundred slabs use 2 × 0.2 × 2; thousand cubes use 2 × 2 × 2. Their volumes have the exact ratio 1:10:100:1000. The place-value companion can exchange one higher-place piece for ten smaller pieces. Addition switches between combined equal-place pieces and the usual digits without changing total volume.

Subtraction uses equal unit counters through 100, with separate retained/removed groups or comparison groups. Outlined shortfall counters add no material. Multiplication includes all 12×12 units and a turned array. Division shows all equal groups and every remainder counter, including 144 groups of one. Requested empty sharing groups may have empty outlines. Gray reference units and group enclosures are inspection guides and are excluded from material totals. The companions have independent controls, stated in their instructions and notes.

All solid faces retain outward winding, closed edges, nonoverlap and calibrated volume. The largest tested scene has 2,604 primitives, below the existing 3,000-primitive limit. Camera changes alter projection rather than quantities. The shared callout search now starts from a visible search origin when an anchor is off-screen, preventing zoomed labels from collapsing onto one edge. A cropped-view notice appears exactly when non-label geometry extends beyond the canvas, including sphere radius when applicable; it tells the learner to zoom out to inspect all geometry.

## Evidence

Independent integer/Fraction checks cover 56,774 states and 615,446 assertions: all four-place values, all allowed exchange representations, all lesson-range additions and subtractions through 100, larger carry/borrow samples, every times-table product through twelve, and all supported dividend/divisor pairs in both meanings. They include 290 undefined cases and twelve malformed or cross-lesson rejections.

The actual shipped spatial families and exact lesson bindings are measured across 1,382 geometry states: 273,570 outward face checks, 45,595 piece-volume checks and 1,919,837 nonoverlap checks. These oracles print results without rewriting frozen evidence during tests.

The authenticated reader uses isolated synthetic data and an eight-year-old profile. Across 390- and 1440-pixel viewports it verifies all five lessons, 116 activity states, 192 speech checks, 462 camera poses, exchanges in both directions, factor/addend swaps, invalid-draft recovery, original image loading, keyboard scrolling and enlargement. Independent checks compare actual SVG quantities and projected source vertices; callouts stay inside the canvas without overlap, and crop notices match computed geometry. Screenshots include ordinary and zoomed stress states.

The eight shared runtime edits have an exact literal/hash inverse for frozen historical evidence. This restores only the recorded prior byte view; it does not transfer earlier approvals to new behavior. The whole-curriculum model checker retains all 462 bindings and now covers 71 families. CI retains all checks and tests; its job budget is 45 minutes because an observed 15m31s checkout plus a 20m30s full suite exceeds the former 30-minute budget.

This review covers these five implementations. The full radiology, mathematics and physics objective remains incomplete, including the remaining reporting-structure and module fidelity work.
