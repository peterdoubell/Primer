# Original laryngeal phonation source reference — partial

The package preserves the author's original Stiff phase-01 threshold-segmented air–tissue interface from [Zenodo 19629778](https://zenodo.org/records/19629778), CC BY 4.0, for use as a limited source reference. It provides no complete swallowing/VFSS anatomy, separate cartilage/tissue layers, pathological interpretation, physiological validation, or proven registration to MRI. All dataset creators and DOI are recorded in the packaged attribution and exact original metadata snapshot.

`original-frame_01.stl` is the exact complete source member, SHA256 `dddf49ed16942555eefcda5f97db3f39942676532bd816f348277895715480d2`. The BP3D package keeps 29,326 triangles, 14,831 bit-exact source coordinates, all four components (29,294/16/8/8 faces), all 328 open boundary edges, and original face order. Every one of the 87,978 reconstructed face corners was compared byte-for-byte against the original STL corner stream after writing and reading the compressed package. Positions have zero transport error. Averaged display normals and neutral colour are presentation adaptations; no geometry was fitted, centered, smoothed, capped, repaired, decimated or deleted.

The original STL header identifies Blender 3.4.1. It supplies no source patient orientation, units, coordinate convention or transform. The manifest retains this uncertainty and uses source-coordinate camera labels. The display's source-X/source-Z/negative-source-Y permutation is a fixed camera convention, not anatomical orientation or MRI registration. No MRI overlay or `source_image`/`source_volume` link is included.

The matching published MR array contains 11,239,424 original float64 reconstructed samples on a 224³ grid. Independent custom and pynrrd readers agree on every sample. Native acquisition resolution is nominal 0.8 mm; the actual exported pitch is 0.3839285671710968, produced by zero-filling (nominal 0.4 mm in the article). The 89.9 MB NRRD remains in the source cache rather than being duplicated here. The copied native/reader/header proofs preserve its SHA256 and geometry. Inherited NIfTI srow key/value strings conflict in x/z directions with the primary NRRD affine even after RAS/LPS conversion. The coordinate audit quantifies this mismatch and eight fixed sign hypotheses. LPS gives stronger airspace correspondence, but an undocumented transform and absent original segmentation mask prevent producer-proven registration. This hypothesis is not displayed as fact in the runtime manifest.

The source is one professionally trained female singer performing sustained phonation, not swallowing. Phase 01 is the authors' maximum glottal-opening phase bin. Ten acoustic phase bins aggregate an oscillatory cycle across a 5 min 20 s scan; these are not consecutive independent live images. The matching audio-to-volume sample clock and separately acquired upright high-speed video are not independently reconciled. The article explicitly notes partial-volume limits, unreliable cartilage differentiation and unresolved membranous-fold/vocal-process transition. Only a threshold-segmented interface is available; detailed reporting tissues remain unapproved.

Acquisition proofs include exact ZIP-member CRC32 and local SHA256, stable publisher size/checksum before/after byte ranges, and independent original-STL acquisition. The whole 5,228,064,118-byte archive was not downloaded or independently MD5-verified; HTTP entity tags were unavailable. These limitations are retained in the reader notes.

`original-STL-review.png` shows all original source faces with neutral shading and source axes; the visual review does not approve clinical fidelity. The authoritative transport proof is `reader-transport-review.json`. `registry-candidate.json` contains a reviewable entry and rights-bound model evidence with empty `structure_ids` and `requirement_coverage`, and pending anatomical review.

Package without changing global registration:

```sh
python tools/anatomy_sources/package_laryngeal_phonation_reference.py \
  --source-root /Users/peter/Documents/ChatGPT/Primer/.research/swallow-fine-larynx-19629778
```

After the atlas/family and hosted static contracts are explicitly accepted by the integration owner, apply the partial source reference to swallowing:

```sh
python tools/anatomy_sources/package_laryngeal_phonation_reference.py \
  --source-root /Users/peter/Documents/ChatGPT/Primer/.research/swallow-fine-larynx-19629778 \
  --apply-registry --investigation ra.swallowing
```

`--investigation ra.mri-neck-spaces` is also supported only for an intentionally scoped phonation-interface reference, with all the same limitations; it does not represent complete neck spaces. Default application is swallowing alone. The packaging-only run used here did not alter global registry/evidence, viewer JavaScript, server code or Git state. The coordinate reproduction script requires the original matched files in its source-cache layout; the large NRRD is intentionally not committed.
