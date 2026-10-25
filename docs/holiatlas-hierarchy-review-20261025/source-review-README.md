# Brain hierarchy review, 25 October 2026

The 63 source-scale entries are suitable for an accurately named hierarchy browser. They add **34 distinct aggregate masks** beyond the 332 existing fine masks. Twenty-seven structure entries repeat single fine masks; the tissue vessels/connective class repeats another fine mask, and tissue Brainstem repeats structure Brainstem. Their geometry is useful for coherent parent selection and removal of internal child boundaries, not evidence of 63 previously missing anatomical structures.

The supplied coarse maps equal the protocol-mapped fine volume at all **56,873,096 voxels**, with **zero differences**, in the existing independent hierarchy proof. This review additionally verifies each parent voxel count against its present child counts. Coarse source headers do not declare spatial units: the millimetre basis is the exact correspondence and identical numerical sform to the millimetre-declared fine grid.

## Integration files

- `source-scale-display-crosswalk.json`: all 63 entries; original and proposed names; exact child codes and counts; absent protocol children; subset/superset exclusions; duplicate geometry identities.
- `proposed-source-compositions.json`: 16 explicitly defined unions that improve anatomical navigation without inventing boundaries.
- `existing-brain-requirement-crosswalk.json`: all 210 existing brain parts, preserving required image, schematic and model representations. Coarse-context links are not clinical completion claims.
- `pr167-reporting-inventory-audit.json`: every one of the 62 current brain report rows, explicit inventory links, 28 enumeration gaps, and the broader 60 exact-investigation-ID gaps.
- `build-review.py`: reproduces those four files from the inspected source/worktree and validates their internal correspondence. It writes only this research directory.

The source/worktree hashes and reviewed commit are in each JSON output. This review changes no product files, reports or requirement inventory.

## Display decisions that matter

These decisions follow the supplied source workbook's membership columns, rather than lexical name matching:

| Source code | Recommended display | Extent decision |
|---|---|---|
| Structure 8–15 | Side + lobe + **cortical grey matter** | Source cerebral WM is separate and has no lobar division. |
| Structure 16–17 | **Limbic cortical group** | Includes cingulate, entorhinal and parahippocampal cortex; excludes the hippocampal and amygdala masks. |
| Structure 18–19 | **Insula and opercula — cortical source group** | Both insular regions plus central, frontal and parietal opercula. Pure-insula selection must use the two insula-labelled children. |
| Structure 20–21 | **Hippocampal source complex** | Seven labelled components; there is no head/body/tail partition. |
| Structure 22–23 | **Amygdala — present source regions** | Seven of eight source classes have voxels; both medial nuclei are absent from the delivered template. |
| Structure 24–25 | **Thalamic source complex** | Thirteen source classes. The protocol includes intermediate space and mammillothalamic tract. |
| Structure 44–45 | **Cerebellar grey matter — source side partition** | Twelve lobule classes per side; WM is separate and no independent vermis/hemisphere boundary exists. |
| Structure 46–47 | **Cerebral white matter — undivided source mask** | Not individual capsules, callosal segments, tracts, centrum semiovale or corona radiata. |
| Structure 48 / tissue 7 | **Brainstem remainder — source grouping** | Keep its four source children and separate pBrain masks visible. Do not present the parent as complete brainstem. |
| Structure 52–53 / tissue 8 | **WM lesion — tiny source residual** | Only 11 right and 17 left voxels; useful for source transparency, not a clinical lesion illustration. |
| Structure 54 / tissue 9 | **Filled intracranial gaps — source vessels/connective class** | Not named artery, vein, sinus, dura or cranial-nerve geometry. |
| Tissue 4 | **Deep structures — source Deep GM grouping** | Retain source taxonomy, but do not promise histologically pure GM. |
| Organ 1 | **Intracranial contents — source ICV mask** | Includes all foreground classes, including CSF and the residual class; not parenchyma alone. |

The JSON contains labels and extent definitions for every other entry, including separate ventricular main/inferior compartments and unchanged single-mask parents.

## Useful additional compositions

All 16 proposed compositions are exact unions of named existing fine labels, one on each side for each row below. Generate only exposed union faces, retaining the exact source grid and all connected components. The image overlay must use the same code set.

| Composition | Right fine codes | Left fine codes | Concrete gain |
|---|---|---|---|
| Insular cortex | 224, 230 | 225, 231 | Separates labelled insula from the opercular source parent. |
| Opercular cortical group | 226, 228, 232 | 227, 229, 233 | Makes the excluded opercular anatomy inspectable beside insula. |
| Precentral cortical regions | 150, 160 | 151, 161 | Includes the separately labelled medial segment. |
| Postcentral cortical regions | 172, 176 | 173, 177 | Includes the separately labelled medial segment. |
| Superior frontal cortical regions | 152, 164 | 153, 165 | Includes the main and medial source labels. |
| Inferior frontal cortical parts | 154, 156, 168 | 155, 157, 169 | Combines the source opercular, orbital and triangular parts. |
| Cingulate cortical regions | 214, 218, 220 | 215, 219, 221 | Excludes entorhinal/parahippocampal cortex from the larger limbic group. |
| Lateral ventricular source compartments | 4, 6 | 5, 7 | Combines source main and inferior compartments without inventing horn boundaries. |

These compositions establish the precise source representation a learner sees; they do not prove independent clinical extent equivalence. For example, superior frontal composition must not silently acquire separate medial-frontal or supplementary-motor labels.

## Source-grounded schematic work with highest immediate value

1. **Cortex, opercula and insula:** three linked views of an exact native plane, labelled source boundary overlay and clipped 3D selection. Include pure-insula child union versus the five-child source parent. This fixes a consequential parent-label ambiguity while giving a usable image/schematic/model comparison.
2. **Medial and lateral cortical landmarks:** source-derived outlines of both precentral components and both postcentral components, with native MRI underneath. Label the medial segments independently. The unsegmented hand knob remains a separate requirement needing its own reviewed delineation.
3. **Deep structures in context:** axial and coronal source-image outlines with thalamic complex, internal/external pallidal parts, caudate and adjacent undivided WM. Keep the capsule uncoloured until a source actually delineates its limbs; do not infer capsule geometry from leftover space between masks.
4. **Ventricular compartments:** show exact main/inferior lateral-ventricular labels and third/fourth ventricles on native planes. A separate reviewed flow schematic can teach connectivity, but the atlas does not prove aqueduct/foraminal/aperture lumen geometry.
5. **Cerebellar lobules and WM:** paired native-plane and surface outlines of source lobules plus WM. A labelled vermis, cerebellar lobe or peduncle schematic needs additional reviewed boundaries; side labels alone cannot establish those subdivisions.

These are proposed source-derived schematic implementations. No schematic is claimed complete by this review.

## Reporting inventory drift

PR 167 kept the total report inventory at **156 investigations**, but expanded explicit anatomical coverage from **32 to 156 investigations** and **1,028 to 4,124 anatomical rows**. The two detailed requirement JSONs were unchanged by that commit. They enumerate **96 investigation IDs**; **60 current reporting IDs** do not occur there verbatim. This is an exact-ID reconciliation result, not proof that those 60 modules have no existing visual material or related requirements.

The current brain anatomy report has **62 selectable anatomical/territory rows**. Of these, **28 are not explicitly enumerated** among its existing 31 requirement parents and 210 required parts:

- **24 bilateral cortical rows:** superior, middle and inferior frontal gyri; superior and inferior parietal lobules; superior, middle and inferior temporal gyri; cingulate gyrus; precuneus; cuneus; lingual gyrus.
- **Two amygdala rows**, one per side.
- **Two MCA division territory rows**, superior and inferior.

The other 34 reporting rows have explicit parts, broader named parents, component requirements, or related bilateral territory requirements. The audit distinguishes these categories. None is interpreted as complete image/schematic/model coverage. The missing 28 entries should be added to the requirements without removing the 210 already demanded parts.

The new cortical and amygdala inventory rows can make immediate use of existing fine labels and the reviewed compositions above. The MCA division territories require a separately reviewed vascular-territory source; cortical lobar masks cannot supply them.

## Additional source needs

The remaining required geometry needs actual delineations: capsule limbs and callosal segments; caudate head/body/tail; hippocampal longitudinal regions; brainstem tectum/tegmentum/basis and peduncles; cerebellar vermis, lobes and nuclei; ventricular horns and connecting channels; named cisterns and meningeal compartments; named arteries, veins and sinuses; and arterial/border-zone territory maps. A useful next source must supply reviewed masks or surfaces for those named extents and its own image-space registration. No candidate dataset is approved merely for having a similar anatomical label.

## Primary evidence and interpretation

The exact [released dataset](https://zenodo.org/records/15690524) and its `HoliBrain_Protocol_v1.0.xlsx` are authoritative for the child-parent membership and counts used here. The file reviewed locally is pinned by hash in the JSON outputs.

The [published paper](https://www.nature.com/articles/s41598-026-40186-2) describes the cohort and construction; its later web sections were inaccessible during this review. The authors’ [primary preprint](https://arxiv.org/html/2501.16879v1) supplies the detailed integration description: pBrain insertion leaves a partial midbrain; the hippocampal protocol adds fimbria and HATA; thalamic intermediate space links nuclei; the vessels/connective label comes from filling foreground holes. Sulcal names refer to assigned external CSF territories. These statements support the scope distinctions above. The preprint and release have different historical licensing statements; this review neither imports preprint figures nor replaces the release’s existing licence record.

Clinical accuracy beyond the inspected source extents, boundary interpretation, and complete three-representation coverage remains to be established. The exact hierarchy and compositions are concrete progress toward that larger work.
