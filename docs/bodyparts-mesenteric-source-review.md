# Original mesenteric vascular source review

The local candidate packet contains 38 original BodyParts3D objects selected through 33 version-4.3 groups, covering celiac/SMA/IMA trunks, colic and ileocolic branches, pancreaticoduodenal arteries/veins, mesenteric and colic veins, splenic vein and pre-hepatic portal vein. Compound and trunk groups overlap; they do not create additional independent vessels or fine-structure coverage. [Acquisition evidence](bodyparts-mesenteric-source-review/acquisition.json) retains original headers, returned representations, object hashes and archive CRC results. The original archive and OBJ files remain in ignored research storage.

The [complete version manifest](bodyparts-mesenteric-source-review/complete-version-manifest.txt) is bound to the original metadata SHA-256 and makes the absent requested FMA14820 branch independently checkable. [Selection holds](bodyparts-mesenteric-source-review/source-selection-holds.json) retain all 34 requested labels: the ascending branch of the inferior ileocolic branch remains absent from this manifest, despite a legacy mapping row. It is not removed from the clinical requirement or replaced with another branch. Selected source metadata snapshots are preserved without alteration.

Seven returns differ from the requested is-a representation, but match the provider's original part-of mapping and returned OBJ headers. The source identities remain explicit:

| Object | Requested representation | Returned representation |
| --- | --- | --- |
| FJ3553 posterior cecal artery | BP20929 | BP23977 |
| FJ3406 anterior cecal artery | BP21036 | BP22077 |
| FJ3442 IMA trunk | BP22910 | BP23699 |
| FJ3410 appendicular artery | BP21026 | BP22112 |
| FJ3590 right colic artery | BP20288 | BP21884 |
| FJ2034 ileal ileocolic branch | BP20778 | BP23788 |
| FJ2025 marginal colic artery | BP20855 | BP22106 |

[Geometry evidence](bodyparts-mesenteric-source-review/original-obj-geometry-review.json) preserves all 26,700 triangles, original coordinates/normals/indices and 43 exact-position connected components. No triangle has zero area and no nonmanifold edge is found under that analysis. Source surfaces are not fitted to their header bounds: the maximum observed/header difference is 0.1102 mm in FJ2034; FJ2025 differs by 0.0639 mm. These discrepancies remain evidence, not grounds for changing coordinates.

FJ3553 has twelve open boundary edges. [Complete boundary evidence](bodyparts-mesenteric-source-review/complete-source-boundary-review.json) retains every original face, endpoint record and position: one twelve-edge graph cycle with degree two at each vertex. That numerical loop is not independently classified as an anatomical cut end or defect, and no cap is added. FJ2025 has five components and FJ3588 superior rectal artery has two; no connection, smoothing or tissue repair is invented. Closed surfaces elsewhere do not independently establish a vessel lumen, wall layers or physiological patency.

[Complete per-object contact evidence](bodyparts-mesenteric-source-review/complete-self-contact-summary.json) retains all 38 losslessly compressed results. Every source triangle was numerically testable; 231,629 conservative candidate pairs were accounted for, with zero unexpected self-contacts. Objects were tested separately. Cross-object connections, contacts and repeated vein representations remain unverified; these results are not approval of a continuous vascular tree.

Fourteen [source view sheets](bodyparts-mesenteric-source-review/source-figure-review.json) display every unique original object's triangles at two azimuths, preserving the coordinate scale/aspect within each panel. Panel scales differ. Red/blue colours and lighting are review categories only, not acquisition evidence, flow, oxygenation or patency. Layout review prompted more spacing and shorter axis labels so narrow source vessels do not overlap neighbouring titles or attribution. Original source geometry is unchanged.

The provider's [current license page](https://lifesciencedb.jp/bp3d/info_en/license/index.html) states CC BY-SA 2.1 Japan for this upstream source. The separate archive-4.0 CC BY 4.0 grant is not reused. Derived review views retain the same share-alike attribution; rights do not approve clinical accuracy or native acquisition fidelity.

Validation: 17 scientific source/parser/geometry checks passed, followed by 28 combined source, boundary, ischaemia-scope and all-radiology scope checks after final rendering. Complete evidence hashes, every source triangle and the missing branch are checked. Original sources remain unmodified. Nothing is promoted to runtime and no anatomical coverage is granted. Jejunal/ileal arcades, vasa recta, source-specific peripheral branches, actual collateral/variant pathways, whole wall/lumen interfaces, calibrated acquisition and positive pathological representations remain required. The all-radiology goal remains active with 19,617 known obligations, 94 unexpanded investigations and 106 unreconciled curriculum surfaces; full denominator and readiness remain unproven.
