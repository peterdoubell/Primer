# Final thermodynamics delivery review — 2026-10-10

Result: passed the bounded final release revalidation. No material delivery, selector, readout, speech, or mobile-layout defect was found in the checked states. No runtime code or shared source/dependency ledger was changed by this review.

The authenticated local app was tested at `http://127.0.0.1:8900/?final_cycle_review=1#node/phys.3.thermo`, in an independently owned browser session, at 1440 × 980 and 390 × 980. The API binds the 2D `physics-cycle-lab` to `phys.3.thermo.cycle-entropy` and the 3D `spatial-3d` model to `module.phys.3.thermo` / `carnot-state-path`.

## Requested native states and physical results

At each viewport, the real mode and leg select controls were used to request engine and refrigerator leg `3` (the fourth leg), followed by 50% path position. Expectations came from the requested values and independent ideal-gas/Carnot calculations, rather than from the potentially normalized select value. Both the mounted 2D state and actual 3D readout retained the requested fourth leg after the final generic typed-option handler change.

- Engine fourth leg: D → A, reversible adiabatic compression; Q = 0, W_by ≈ −154.978 J, ΔU ≈ +154.978 J, T ≈ 424.264 K. Visible volume and pressure also matched the independent oracle.
- Refrigerator fourth leg: B → A, hot isothermal compression; Q = W_by = −200 J and ΔU = 0 at 50%, T = 600 K. Visible volume and pressure matched the independent oracle.
- First-law mode: explicitly requested Q = −150 J and W_by = −400 J gave ΔU = 250 J. The separate signed energy plot was shown; leg selector, cycle table and reservoir plot were disabled/hidden. Its visible annotation states that no pressure–volume path is asserted.

The checked mobile and desktop states had no whole-page horizontal overflow, no clipped or overlapping 3D labels, and no browser errors. Screenshots were inspected for the actual mobile engine scene, mobile first-law signed ledger, and desktop refrigerator scene. Ten actual model speech-button invocations were intercepted without producing audio; every chunk sequence reconstructed the full expected numeric readout exactly, and every chunk was at most 1200 characters (maximum observed: 1130).

The actual `math.5.numerical` route was also checked at 390 px. Requesting native sign `−1` retained that value and produced the expected negative conditioning case: δ = −10⁻¹⁶ and Δx₂ = −10⁻¹⁵. The mounted readout matched the independently requested negative model, and its visible geometry label read `Δx₂ = -1e-15`.

## Final bytes and relation to the earlier broad proof

Each of these seven assets was fetched from the authenticated browser with caching bypassed. All served SHA-256 values equaled the current local file bytes.

| Asset | SHA-256 |
| --- | --- |
| `physics-cycle-lab.js` | `79fe10e9adce60e014c712c81eebee5ec5dc5705bb174e44e193bb774a1ed81c` |
| `physics-cycle-lab.css` | `850b75480f71df16b34e18cd748592197effe675fcae26daf2b63912c462eab8` |
| `lesson-models.js` | `b2489a4aad2f7215afe49387a68887f566559c66ec1d07e4b92b573365c55528` |
| `spatial-models.js` | `b3d2e6dbb578e527da86fe221386456449cfcebd704cbdc06ab4c256cf0c63b6` |
| `spatial-module-objects.js` | `eb8d0c56cf50fc00c03a4fbd5e228af4ee9e6f21a739d9e322016a3d548c4095` |
| `app.js` | `f5a09f4e423084cd848b7be78054cc16c89a18e83cde5966cbbb1c0054d70980` |
| `styles.css` | `53a6b03e8e7c1aaae2b6310768f15c4b308855a74c06163f1fe7221561b082c0` |

The earlier `.research/cycle-route-proof-20261010-vJzbTF/proof.json` covered 172 2D and 102 3D states across these two viewports. Cycle JS/CSS, lesson models, app JS and common CSS are byte-identical to that proof. The two spatial assets have changed. This review explicitly revalidates the Carnot family’s requested fourth-leg selection, physical signs, scalar readouts and speech against their final served bytes after the shared renderer fix. It supplements the earlier broader proof; it does not claim that all 102 earlier 3D states were rerun after the final changes.

## Evidence and scope

Final machine-readable proof and eleven screenshots are preserved in the owner workspace’s ignored `.research/physics-cycle-final-review-20261010-z115hwm2/` directory. The reproducing browser driver is `.research/physics-cycle-final-delivery-qa-20261010.py`. The independently owned browser was closed; the root QA server was left running.

This is local release delivery evidence for the named routes and requested states. Production deployment and wider anatomical/clinical approval are outside this review.
