# MRI-derived knee component reconciliation — 26 September 2026

The knee viewer now permits separate selection and isolation of the medial and
lateral menisci and medial and lateral tibial plateau cartilage. These are the
four **complete disconnected components already present** in the two combined
Universiti Malaya source objects. No new anatomy, surface cutting, smoothing,
subdivision, interpolation or fitting was performed.

The original 28 objects remain intact in the manifest and on disk. Nested
`components` records replace their two combined entries for display, producing
30 selectable structures with the same total **1,307,872 retained triangles**.
The extra gzip files occupy 305,168 bytes. Initial loading still requests only
the four bones. Combined parents are never rendered over their component views.

## Exact component identity and source preservation

The [primary source dataset](https://researchdata.um.edu.my/dataset.xhtml?persistentId=doi:10.22452/RD/5T6TZ7)
provides MRI-derived geometry in a common native LPS millimetre frame, with CC0
terms. It calls the original objects `Meniscus_Knee` and `Cartilage_Tibia`.
It does **not** provide separate medial/lateral segmentation names for these
objects. Primer's names are positional interpretations, explicitly recorded as
such, not presented as new labels supplied by the authors.

| Component interpretation | Retained source facets | Native X bounds, mm |
| --- | ---: | --- |
| Lateral meniscus | 2,000 | −89.681 to −64.260 |
| Medial meniscus | 3,196 | −49.711 to −16.188 |
| Lateral tibial plateau cartilage | 2,772 | −88.624 to −60.874 |
| Medial tibial plateau cartilage | 3,576 | −48.776 to −20.911 |

For this right-sided source, larger LPS X is medial. The two component bounds
are disjoint in X; the native fibula provides the lateral landmark. The
[superior projection](msk-knee-component-review.png) was inspected in that
unchanged frame: each meniscus occupies the matching tibial compartment, the
medial/lateral cartilage components correspond to those compartments, and the
fibula lies on the lateral side. This is an identity and source-correspondence
check, not independent validation of segmentation boundaries or tissue health.

The extraction uses exact shared positional edges while retaining normal seams.
Every child records its parent render-face indices and the corresponding
original STL face indices. Child position and normal float32 bytes are copied
exactly. Tests independently compare every selected triangle corner and normal
against the parent and prove that the children form a disjoint exhaustive
partition. All previously retained nonzero facets remain present. The earlier
48 exactly empty facet omissions are unchanged.

Reproduce with `tools/anatomy_sources/split_malaya_knee_components.py`; the
normal MRI packager calls the same extraction during a knee build. The
source-frame visual QA tool is `tools/anatomy_sources/render_knee_components.py`.
The original binary files and the ankle's shared knee resources are unchanged.

## What this does not establish

Separating connected components adds individual selection, not anatomical
detail. Meniscal horns, roots, free-edge regions and capsular attachments are
not independently segmented. Cartilage is an enclosed source surface, without
independent articular/deep-interface or sublayer labels. MRI sampling,
author-applied smoothing and the source omissions continue to limit fidelity.
No requirement, high-fidelity approval or clinical-review status was waived.

The evidence ledger links these four models to their whole parent structures
for review. It deliberately does not credit all leaf requirements from those
parent names. Each detailed reporting requirement still needs its own evidence.

## Reconciled existing clinical figures

The original pixels of Bolog and Andreisek's figures 10 and 16 were inspected
again, together with their [primary article captions](https://link.springer.com/article/10.1007/s13244-016-0472-y).
Figure 10 retains the original arrows for the normal anterior medial root,
anterior lateral root and intermeniscal ligament. Only the two anterior-root
requirements receive explicit candidate bindings here; no posterior root or
full meniscal extent is inferred. Figure 16 retains the two original arrows
for the posterosuperior and anteroinferior popliteomeniscal fascicles and is a
candidate for that named fascicle requirement. Both remain unapproved for
clinical-grade completeness. These published examples come from separate
examinations and are not registered validation images of the Malaya subject.

The fidelity audit also checks each clinical-image binding against the target's
explicit modality scope. Ultrasound, radiography, MRI and arthrography are kept
distinct; an approval cannot silently turn a source from another modality into
direct image evidence for the target. Named acquisition-qualified alternatives
are handled explicitly, and missing or unknown modality scope stays unverified.
Source reading and passing these mechanical checks still do not approve anatomy.
