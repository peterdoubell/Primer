# Source-derived Open Knee(s) knee schematics

Three teaching views use the same native `oks003` geometry available in the
MRI-knee workspace's **Open Knee(s) · left specimen** 3D option. These are
projections of acquired MRI-derived surfaces, not original publication figures
or diagnostic MR images. The dataset remains one 25-year-old female cadaveric
left knee; anatomical and clinical approval is pending.

| View | Source objects | Anatomical display frame |
| --- | --- | --- |
| Posterior patella and cartilage | PTB and PTC | Camera on −Y; screen right +X (medial), screen up +Z (superior) |
| Superior medial/lateral menisci | MNS-M, MNS-L, TBB and FBB | Camera on +Z; screen right +X (medial), screen up +Y (anterior) |
| Superior medial/lateral tibial cartilage | TBC-M, TBC-L, TBB and FBB | Same superior anatomical frame |

Other joint structures are explicitly omitted to expose the illustrated
surfaces. Omission in a teaching view does not mean absence in the specimen.
The meniscal view does not portray the cartilage layer between menisci and
bone. Source objects retain their relative positions and native RAS millimetre
coordinates. No fitting, mirroring, smoothing, new segmentation or geometry
repair is applied. Display colours, lighting, labels and orthographic projection
are adaptations, and the images are labelled accordingly.

## Source and rights

The source is the [Open Knee(s) oks003 repository](https://simtk.org/svn/openknee/oks/oks003/),
specifically its AGS assembly and [geometry](https://simtk.org/svn/openknee/oks/oks003/Geometry/).
The original [repository licence](https://simtk.org/svn/openknee/license.txt)
is preserved as `web/anatomy/openknee-oks003/SOURCE-LICENSE.txt` and explicitly
covers the source models. This is **CC BY-SA 3.0 Unported**, independent of the
separate MRI archive's licence. The same terms apply to these rendered
adaptations. The [official deed](https://creativecommons.org/licenses/by-sa/3.0/)
allows commercial use and adaptations with attribution and ShareAlike.

Credit: Open Knee(s) Development Team; Chokhandre S, Schwartz A, Klonowski E,
Landis B, Erdemir A. *Open Knee(s): A Free and Open Source Library of
Specimen-Specific Models and Related Digital Assets for Finite Element Analysis
of the Knee Joint* (2022/2023), doi:10.1007/s10439-022-03074-0. Source repository
revision 3413, oks003 AGS assembly. Rendering, colours, labels and viewing
selection added for Primer; native geometry unchanged. No endorsement implied.

## Reproducibility and limits

`tools/anatomy_sources/render_openknee_schematics.py` records the source
manifest, exact part fingerprints and triangle counts, projection frame,
per-pixel depth handling, physical scale and label anchors. The rendered image
and evidence hashes bind each display record to that reviewable source. The
catalogue rejects changed source parts, missing evidence and silent relicensing;
those checks establish provenance, not clinical validity.

General source MRI has a 0.5-mm isotropic grid; the cartilage acquisition has
approximately 0.35 × 0.35 × 0.7-mm sampling. The authors processed and smoothed
the meshes before release. A large rendered image or a large facet count does
not add anatomical resolution. Scale bars describe the source coordinate
scale, not validated patient measurements.

The [paired source review](msk-openknee-source-review/README.md) supports direct
source correspondence for the patella, patellar cartilage and both menisci.
Its mask/mesh agreement is not independent tissue-boundary validation. Whole
object labels do not divide meniscal roots, horns, body, free edge or attachment
surfaces, and the views do not establish cartilage thickness or the full
subchondral interface. Exact tibial-cartilage mask-version ancestry remains
[unresolved](msk-openknee-tibial-review/README.md); the tibial view adds no
fine-structure binding. All original reporting requirements remain in scope.

## Integrated technical evidence

The three 3200 × 2280 PNGs are served from `web/reference-media/msk-open/`,
along with `knee-openknee-rendering-evidence.json` (SHA-256
`8caf0b988fbf7fc5becd376454a1d22c699e75fd1716c01ea6d814ba953de783`).
The catalogue labels them as source-derived schematics and links directly to
the matching left-knee 3D source. It does not assign publication figure numbers
to these new projections.

An [independent anchor audit](msk-openknee-schematic-review/independent-anchor-review.json)
reconstructs all ten label points from native triangle coordinates and
barycentric weights, then ray-tests them against every displayed source object.
It confirms frontmost ownership and correct native orientation. Two tibia
labels were moved from thin posterior rims to clearly exposed anterior bone;
no source geometry or soft-tissue labels changed.

The audit supports three **local, unverified** candidates in both the model and
its matching schematic: PTC for the patellar-cartilage articular face, MNS-M for
the medial meniscal superior face, and MNS-L for the lateral meniscal superior
face. Source mask hashes and sampled MRI review planes are recorded with each
candidate. Those sampled planes are not necessarily the label-anchor planes.
These are six representation candidates sharing three source objects, not six
independent validations. Bone context and both tibial-cartilage objects remain
unbound; every anatomical review remains pending.

With NumPy, Pillow and Matplotlib available, reproduce staging and the
independent check with:

```sh
python3 tools/anatomy_sources/render_openknee_schematics.py
python3 tools/anatomy_sources/check_openknee_schematic_anchors.py
python3 -m pytest -q tests/test_openknee_schematics.py
```

The source STLs must be available at the script's documented `--source` path.
Four analytical renderer tests cover depth crossings and order independence,
left/RAS orientation, uniform millimetre scale and visible barycentric anchors.
Repeated renders produce identical PNG and evidence bytes with the recorded
runtime/font versions. Separate catalogue tests reject source swaps,
relicensing, false MRI/figure identity and stale rendering evidence.
