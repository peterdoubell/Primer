# Independent epilepsy requirement/evidence map

> Follow-up correction: the image-3 binding is defensible because FCD is itself a focal lesion. It does not illustrate the step’s specific tumour, cavernoma or scar examples. Retain the binding and accurate caption; see [the minimal correction proposal](epilepsy-minimal-corrections-proposal.md). This supersedes the initial audit’s stronger image-binding wording.

Draft for specialist review. No clinical approval or module-completion claim. The current effective reporting contract was regenerated through `Curriculum` and the radiology catalogue and exactly matches the saved scope snapshot: `3256b93cbef7e6a7d6acda0ffa2238c9d21b16616ea9d1bcef3fb9b6489eb6ce`.

The report requires bilateral hippocampal morphology, internal architecture, signal and adjacent limbic structures; it also requires cortical/migration review, focal lesions, the skull base, dual pathology and electroclinical context. A successful hippocampal tissue viewer advances one part of this scope.

## Reporting groups

| Requirement | 7007362 evidence boundary |
| --- | --- |
| Hippocampal extent, shape and orientation | Source-derived hippocampal tissue geometry within each provided crop; full clinical orientation/extent, true bilateral native relationship and morphology remain unproven. |
| Hippocampal internal architecture | Can display GM, SRLM and DG-labelled source regions. CA1–CA4/subiculum are not supplied classes; full internal-architecture normality is not established. |
| Adjacent mesial temporal anatomy | HATA and MTLC give limited local boundary context. Pial and IndGris are unfolding labels; none establishes the complete adjacent structures. |
| Fornices and mammillary bodies | No fornix or mammillary-body classes; cropped images do not establish complete pathway coverage. |
| Sclerosis, signal and asymmetry assessment | Source-grid counts/morphology are measurable after geometry review. No FLAIR, native transforms/head-size normalization, age-reference interpretation or diagnosis for this subject is established. |
| Whole-brain cortical development and dysplasia | MTLC is only a cropped boundary class; there is no whole cortical ribbon, dysplasia mask or transmantle class. |
| Migration and gyral malformations | The eight tissue classes do not identify heterotopia or polymicrogyria. |
| Focal lesions and acquired substrates | Cyst is an unfolding tissue class, not evidence of tumour, vascular malformation, gliosis or injury. |
| Temporal skull base and encephalocele | A hippocampal training crop and Pial class do not establish skull-base coverage or an encephalocele. |
| Whole-brain search and dual pathology | Two hippocampal boxes cannot establish a negative whole-brain search or dual pathology. |
| Peri-ictal change and acute alternatives | No timeline, clinical diagnosis, FLAIR, ADC or longitudinal pathology is supplied for subject 101006. |

Each JSON group retains its exact checklist indices, report sections and walkthrough steps, required subparts, and distinct acceptance conditions for images, schematics and models. The groups are not a score or a multiplied count of laterality, source classes and representation types.

## What the eight classes mean

| Value / class | Permitted limited credit | Do not infer |
| --- | --- | --- |
| 1 / GM | Cropped labelled hippocampal ribbon | Not a CA1–CA4/subiculum parcellation or complete clinical hippocampal-volume convention. |
| 2 / SRLM | Labelled internal-band spatial relation | Not proof that every lamina is independently resolved, that architecture is normal, or that signal is pathological. |
| 3 / MTLC | Local cortex boundary context | Not separate complete entorhinal/parahippocampal segmentations or a whole-brain cortical-dysplasia survey. |
| 4 / Pial | A boundary label used in the unfolding framework | Not a complete meningeal model, skull-base surface, or CSF-pathway assessment. |
| 5 / HATA | Anterior transition boundary context | Not the complete amygdala or independent nuclei. |
| 6 / IndGris | Posterior unfolding boundary context | Not fimbria, fornix or mammillary bodies. |
| 7 / Cyst | Source-labelled cyst spaces | Not a tumour, a lesion diagnosis, clinical benignity, or all cystic epilepsy substrates. |
| 8 / DG | Granule-cell-layer/end-point label in the method | Not the complete dentate gyrus, hilus/CA4, or histologic pathology. |

The [dataset](https://zenodo.org/records/7007362) is an upsampled training derivative. The [method](https://elifesciences.org/articles/77945) distinguishes the eight tissue classes from later inferred subfield parcellation. Neither the storage grid nor a closed mesh proves native anatomy, diagnostic normality, lesion visibility or completeness. The original [HCP acquisition methods](https://www.freesurfer.net/pub/articles/2013/2013_-_Glasser_et_al._-_NeuroImage.pdf) report 0.7-mm structural acquisitions; stored 0.3-mm voxels do not add acquired detail.

Native-volume claims remain unavailable without the case transforms and a defined boundary convention. Grid volume is `count × |det(index-to-mm affine)|`; affine mapping from original to processed physical coordinates changes volume by its determinant. Even corrected volume needs segmentation QA and a suitable clinical reference interpretation. Do not infer sclerosis or meaningful asymmetry from these cropped counts.

## Actionable current-contract issues

- **no-inventory**: scope.json has structure_inventory null and required_not_yet_expanded for this investigation.
- **image-slots-not-complete**: Current descriptors contain three remote image slots; no source_native_inspectors and no structure_atlas. Skull-base/dual-pathology and electroclinical steps have no images. Presence of remote examples does not prove rights, image visibility or every required structure.
- **third-image-label-mismatch**: Focal-lesion walkthrough uses epilepsy-mri-image-3, whose current caption describes focal cortical dysplasia across T1/T2/FLAIR, not a tumour/cavernoma/gliosis example.
- **fcd-tip-certainty**: Current tip says transmantle signal indicates FCD IIb. The ILAE 2022 consensus uses probabilistic imaging prediction; wording should avoid equating an imaging sign with confirmed histologic subtype.
- **legacy-technique**: Module legacy reference.template offers 3-D / coronal oblique FLAIR while current reporting protocol specifically requires isotropic 3D FLAIR. Reconcile learner-visible versions without weakening HARNESS.
- **normal-language**: Walkthrough normal phrases are report templates, not evidence this HCP training subject or any atlas mesh has normal diagnostic anatomy.

The [ILAE FCD update](https://pmc.ncbi.nlm.nih.gov/articles/PMC9545778/) treats transmantle signal as a subtype predictor. A learner-facing phrase such as “supports an FCD type II pattern, often IIb; MRI does not establish histologic subtype” would preserve that distinction. The retained FCD image can support morphology/signal comparison; separate tumour, cavernoma and scar examples still need their own sources.

## Clinical source boundaries

The [HARNESS consensus](https://www.ilae.org/guidelines/guidelines-and-reports/recommendations-for-the-use-of-structural-magnetic-resonance-imaging-in-the-care-of-patients-with-epilepsy) underpins acquisition, mesial temporal architecture and whole-brain review. Current [infant recommendations](https://pubmed.ncbi.nlm.nih.gov/41894169/) do not establish an optimal individual sequence protocol; an adult HCP viewer must not be presented as infant validation. The primary [encephalocele detection study](https://pubmed.ncbi.nlm.nih.gov/29903924/) and [coexisting-lesion study](https://pmc.ncbi.nlm.nih.gov/articles/PMC9977755/) support dedicated skull-base review and maintaining a search for other lesions. [Peri-ictal imaging evidence](https://pubmed.ncbi.nlm.nih.gov/11415912/) requires temporal and diffusion context that a static anatomy model cannot provide.

## Next actions

1. Complete independent left/right image-label coordinate review before any clinical runtime binding of 7007362.
2. If integrated, label the source as an upsampled, atlas-registered, mirrored HCP training tissue demonstrator; expose exact class limitations and preserve original image comparison.
3. Acquire exact native transforms or change any proposed native-volume/asymmetry claim to processed-grid research measurements.
4. Expand the actual epilepsy structure inventory from these draft reporting groups with specialist-reviewed boundaries and image visibility.
5. Supply source-backed fornix/mammillary, amygdala and whole-brain/skull-base anatomy; do not award coverage from transition/boundary labels.
6. Resolve focal-lesion image binding and add source-licensed diagnostic examples for the currently uncovered report tasks, including dual pathology and peri-ictal evolution.
7. Review FCD language and reconcile all current lesson/report versions, then validate the full report-to-image-to-model learner flow.

`epilepsy-requirements-map.json` is the machine-readable deliverable. `current-epilepsy-contract.json` and `scope-epilepsy-module.json` preserve the exact inspected contract/module. `source-acquisition.json` records successful primary XML snapshots and failed retrievals honestly; the official 2019 ILAE PDF was readable through the web tool, while a direct request returned 403. This is requirements evidence, not a production inventory mutation or clinical review approval.

All twelve current quiz prompts are mapped to requirement IDs in `assessment_trace`; that trace covers the temporal-horn, DNET-pattern, periventricular heterotopia, polymicrogyria and cavernoma questions as well as protocol and re-review tasks. It does not count quiz coverage as image evidence.
