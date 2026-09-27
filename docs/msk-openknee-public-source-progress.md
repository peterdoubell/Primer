# Open Knee(s): public source acquisition and bounded geometry review

Reviewed 2026-09-26. **A complete author-selected 16-object `oks003` source assembly was acquired through public repository links.** It is now available as an optional anatomical teaching source in the knee reporting viewer. No clinical approval has occurred. All MSK fine-component requirements remain in place.

## New access finding

The earlier audit's Generation-1 SimTK release-download confirmation still requires an account; that route was not retried. Two independently public routes are now verified:

- The official [MRI/data DOI](https://doi.org/10.18735/4e78-1311) resolves to a public [MRI and joint-mechanics archive](http://archive.simtk.org/oks/MRI_JointMech/) with ordinary directory links.
- The official [models DOI](https://doi.org/10.18735/b0zv-n395) resolves to the project Data Share page. That page's **Browse source code** link opens the [public source repository](https://simtk.org/svn/openknee/) at revision **3413**. Its linked [oks003 directory](https://simtk.org/svn/openknee/oks/oks003/) exposes source geometry, segmentations and assembly definitions without login.

Only public page links and the visible Data Share form were followed. No private endpoint, account, restricted-download workaround or author contact was used. The old `simbios.stanford.edu` hostname had a certificate mismatch and was abandoned; certificate verification was not disabled.

## Exact assembly and terms

The selected [Model/Connectivity.xml](https://simtk.org/svn/openknee/oks/oks003/Model/Connectivity.xml) names 16 AGS surface files. Every file was present in the [Geometry directory](https://simtk.org/svn/openknee/oks/oks003/Geometry/) and was downloaded unchanged. This is the exact source-selected assembly, not a mixture of guessed latest revisions. The alternative `Geometry/Connectivity.xml` references an absent `oks003_MRC_MNS-M_EMK_04_LVTIT.stl`; that incomplete alternative was not substituted into this assembly.

The [repository license](https://simtk.org/svn/openknee/license.txt) is **CC BY-SA 3.0 Unported**, explicitly allowing commercial reuse with attribution and ShareAlike conditions for adaptations. The [separate MRI archive license](http://archive.simtk.org/oks/MRI_JointMech/license.txt) is **CC BY 4.0**. Preserve these separate notices; do not relabel the SVN geometry using the MRI archive's terms. Exact license text, specimen metadata and assembly XML are retained beside the staged meshes. Attribution identifies the Open Knee(s) Development Team and the [Chokhandre et al. project paper](https://doi.org/10.1007/s10439-022-03074-0).

Staging directory: `/tmp/primer-msk-sources/openknee-public-pass/oks003-native/`.

- `acquisition.json`: all 16 source URLs, exact byte hashes, bytes, HTTP modification/ETag records and selected assembly hash.
- `geometry-audit.json`: original bounds, facets, topology/components, source-normal checks and per-file hashes.
- `license.txt`, `source-metadata.xml`, `author-assembly.xml`: unchanged official sidecars.
- `selected-masks-acquisition.json`: exact source hashes and complete relevant NIfTI header fields for the two acquired masks.
- Parent staging folder includes reproducible `audit_native_geometry.py`, `render_native_review.py` and `acquire_selected_masks.py` scripts, plus saved public directory listings.

## Specimen context

The [source metadata](https://simtk.org/svn/openknee/oks/oks003/metadata.xml) and archive README identify a **left knee from a 25-year-old female donor**, height 1.73 m, mass 68 kg, BMI 22.8. The [2021 data descriptor, Table 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC7890148/) reports radiologist-assessed grade 0 cartilage damage, osteophytes, marrow abnormality, effusion, synovitis and extrusion, normal meniscal morphology, and no ligament/other soft-tissue damage for `oks003`. This is the authors' source assessment, not our clinical certification or population-wide normality claim. The table was available in indexed primary-source text; direct PMC access presented a browser challenge and was not retried.

## Geometry actually acquired

The 16 binary STLs occupy **15,352,544 bytes** and contain **307,024 nonzero facets**. All have finite positions/normals, one component by exact shared edges, no boundary or nonmanifold edges, no repeated geometric faces, and consistent winding. No source normal opposes its facet winding. Source geometry was not smoothed, welded, repaired, fitted, split or decimated by this audit. Edge topology does not establish tissue-boundary accuracy; global self-intersections were not tested.

| Source ID | Whole source object | Facets |
|---|---|---:|
| FMB | Femur | 40,338 |
| TBB | Tibia | 41,796 |
| FBB | Fibula | 7,584 |
| PTB | Patella | 17,280 |
| FMC | Femoral cartilage | 40,824 |
| TBC-L | Lateral tibial cartilage | 25,578 |
| TBC-M | Medial tibial cartilage | 20,580 |
| PTC | Patellar cartilage | 21,756 |
| MNS-M | Medial meniscus | 11,664 |
| MNS-L | Lateral meniscus | 12,448 |
| ACL | Anterior cruciate ligament | 13,500 |
| PCL | Posterior cruciate ligament | 4,698 |
| MCL | Medial collateral ligament | 19,440 |
| LCL | Lateral collateral ligament | 4,638 |
| PTL | Patellar ligament/tendon | 12,600 |
| QAT | Quadriceps tendon | 12,300 |

Five review sheets show cartilage, menisci, ligaments and extensor structures in native XY/XZ/YZ projections, plus isolated soft tissues. Visual inspection finds substantive, nonuniform tissue volumes and separately identified patellar/tibial cartilage, rather than material patches or line connectors. Meniscal surfaces have crescent profiles with regional thickness variation. The tibial cartilage is less visibly faceted than the Dryad candidate's lateral cartilage; this comparison is about the rendered surface, not demonstrated anatomical accuracy. Quadriceps geometry has a proximal truncation and remains a covered tendon segment, not an entire extensor muscle complex.

## Sampling and paired-source handoff

The [MRI archive README](http://archive.simtk.org/oks/MRI_JointMech/readme.txt) maps `oks003` with no protocol deviations to:

- General MRI: [source NIfTI](http://archive.simtk.org/oks/MRI_JointMech/mri/mri-oks003/1.3.12.2.1107.5.2.19.45406.2014120210113013368841431.0.0.0.nii), nominal **0.5 mm isotropic**. Root acquired 97,075,552 bytes, SHA-256 `e0566dd0a81db02e3d6fcfc29ce0d78afe4337c2fb5b0375ea9e0a04595cf5cb`, with its content/frame audited against both source labels and meshes.
- Cartilage MRI: [source NIfTI](http://archive.simtk.org/oks/MRI_JointMech/mri/mri-oks003/1.3.12.2.1107.5.2.19.45406.2014120210325342222042395.0.0.0.nii), nominal **0.35 × 0.35 × 0.7 mm**, 102,760,800 bytes, SHA-256 `9266f03edaff042932cdae09f7c308a80e4106e3790f32c4004c52d6edc67812`. These local SHA values identify the acquired bytes; no independently published MRI checksum was supplied.
- Connective-tissue acquisitions: three orthogonal proton-density sequences at nominal **0.35 × 0.35 × 2.8 mm**; not downloaded here.

Two exact matching masks were acquired from the publicly linked [segmentation directory](https://simtk.org/svn/openknee/oks/oks003/segmentation/):

| Mask | Bytes | Grid / spacing | SHA-256 |
|---|---:|---|---|
| `oks003_ACL_AGS.nii` | 243,352 | 54 × 75 × 30; 0.5 mm isotropic | `15a000d09af5ac1fb8fd3879439651f1979d83f68e2276399c88cb4a8ce8983d` |
| `oks003_MNS-M_AGS_02.nii` | 308,800 | 119 × 27 × 48; 0.3515625 × 0.3515625 × 0.699997 mm | `d257b0e71f6bf54864b42c65d7d473075b8fbe1121da9dc1d50d9d7dd8c947ee` |

Both are cropped int16 label volumes with millimetre units, `qform_code=1`, `sform_code=0`, and quaternion `(-0.5, 0.5, -0.5)`. Their declared offsets place them near the mesh bounds without fitted registration. The meniscal mask uses the cartilage acquisition grid, so general MRI alone must not be called its original segmentation reference. Native meshes place patella anterior (+Y), fibula laterally (−X for the left knee), and proximal anatomy superior (+Z), consistent with RAS. The subsequent 14-object paired audit uses these declared affines directly; bounding-box containment alone was not treated as registration evidence.

## Limits and next decision

The [project paper](https://link.springer.com/article/10.1007/s10439-022-03074-0) distinguishes segmentation-derived raw surfaces from smoothed/resampled surfaces and numerical model attachments. The selected processed meshes are not untouched voxel boundaries. It also states that some fine stabilizers are not modelled, and that separating MCL layers or cruciate bundles would require further work.

No acquired object separately labels meniscal roots, meniscocapsular/meniscotibial attachments, ACL/PCL bundles or MCL layers. Anatomically suggestive endpoints and the assembly's tie/contact definitions must not be promoted to independently delineated fibre volumes. Quantitative mesh density is not clinical fidelity. The subsequent source audit supports an optional teaching reference with explicit limits. It does not verify every fine reporting component. The completed integration is described below; independent clinical review remains pending.

## Processing specification and extended mask mapping

The official [Cleveland Clinic Model Development Specifications](https://simtk.org/docman/view.php/1061/11481/CC-OKS-MD-specifications.pdf), updated 15 August 2018, was acquired unchanged (907,422 bytes; SHA-256 `0ec1bfa5838ae5a8e80b6024377cea009e98b3d0111aeb1519b5a21c120b0de3`). Pages 13–16 were inspected as rendered pages and text. The specification preserves the image coordinate system through geometry generation and specifies millimetre STL export. `LVTIT` denotes Laplacian smoothing, VCG reconstruction, Taubin smoothing, Iso Parameterization/remeshing, and Taubin smoothing. The tissue-specific table is a starting guide; it permits visual/quantitative checking and repairs. It is not an exact processing log for each downloaded mesh. Local copy: `/tmp/primer-msk-sources/openknee-public-pass/CC-OKS-MD-specifications.pdf`.

Fourteen assembly objects have a direct tissue/segmentor/revision filename match in the published mask listing: **FMB, TBB, FBB, PTB, FMC, PTC, MNS-M, MNS-L, ACL, PCL, MCL, LCL, PTL and QAT**. The extended acquisition records their exact bytes, hashes, header fields and choice basis in `assembly-mask-bindings.json`; `mask-mapping.json` contains only those successful mappings. Some masks are full 102,760,800-byte volumes rather than cropped labels. Corresponding names do not prove tissue-boundary agreement; the root task's separate paired-source audit evaluates that.

**TBC-L and TBC-M remain unmapped.** Their selected mesh names end in `AGS_LVTTIT_02.stl` and `AGS_LVTIT_02.stl`, respectively. The directory exposes only `oks003_TBC-L_AGS.nii` and `oks003_TBC-M_AGS.nii`; it supplies no version-labelled AGS masks or per-file provenance explaining that trailing processing revision. Those base masks are not silently substituted. The two held mappings and reasons are recorded separately in `assembly-mask-bindings.json`.

All 14 selected masks completed and were rehashed, totaling **1,022,977,088 bytes**. The simple `mask-mapping.json` has SHA-256 `495c3d937c9782ebad089c82935e1132605f69cfc37cf3d60dedb7b9b2b878fb`. Original files and masks remain outside the application.

## Optional viewer packaging and integration

`python3 tools/build_openknee_atlas.py` creates `/tmp/primer-msk-sources/openknee-public-pass/viewer-staged/` for review and explicitly refuses a destination inside `web/`. The reviewed package was subsequently copied into `web/anatomy/openknee-oks003/`. The provider `openknee-oks003` is selectable in the MRI-knee reporting workspace, alongside the existing separate source anatomies; its addition does not replace the previous default.

The staged package contains **16 parts, 307,024 facets and 7,705,870 gzip transport bytes**. The BP3D buffers contain separate float32 position/normal arrays and sequential triangle indices. An independent uint32 bit comparison verified every original triangle corner, facet normal and triangle order after decompressing the transport. Native RAS millimetre coordinates remain unchanged; no geometry fitting, mirroring, smoothing, deletion or invented component is applied. Layers are 4 bones, 4 cartilage volumes, 2 menisci, 4 ligaments and 2 tendons. PTL displays as patellar tendon while retaining the source patellar-ligament terminology.

The manifest preserves CC BY-SA 3.0 attribution and the exact source license/assembly/metadata sidecars, left-sided specimen context and source-processing limits. `clinical_image_pair.available` and independent clinical approval remain false. No MRI or mask payload is included in this viewer staging directory. The initial registration field is explicitly incomplete; the separate paired-source audit can supply bounded correspondence evidence without converting it into a clinical-accuracy claim.

The final staged rebuild used `--paired-audit /tmp/primer-msk-sources/openknee-public-pass/paired-mri-audit/full-pair/paired-source-audit.json`. The builder verifies the 14 mesh and mask identities, both known MRI acquisition hashes, six unique image/plane comparisons per structure, and the declared absence of fitted transforms or geometry edits. It preserves that exact technical JSON as `registration-evidence.json` (SHA-256 `5bd53e668563dbbd23b8a511caba9c0c6d1f0029658221d5e08b5caf0ea89fa0`). The 84 sampled section Dice values range from 0.7792 to 0.9983; this records source mask/mesh agreement, not independent tissue-boundary accuracy. TBC-L and TBC-M remain unresolved. Clinical image-pair availability and clinical alignment approval remain false.

Six negative checks rejected altered MRI/mesh/mask hashes, a fitted-transform claim, a missing section and a missing structure. `ATTRIBUTION.md` and `converted_geometry_license` explicitly apply the same **CC BY-SA 3.0 Unported** terms to all converted mesh files and derived geometry, independently of the MRI archive license. No source meshes or transport bytes changed when this technical evidence was attached.

Secondary public routes were checked only as leads: the [Leeds meniscus sensitivity release](https://archive.researchdata.leeds.ac.uk/1168/) exposes CC BY 4.0 computational derivatives and links an independent [three-specimen imaging/model release](https://archive.researchdata.leeds.ac.uk/1082/). Those files were not downloaded after the complete `oks003` assembly became available. The [Zenodo graph-analysis release](https://zenodo.org/records/21855195) explicitly excludes original MRI and geometry, so it is not a replacement anatomy source.

## Completed correspondence and verification

The subsequent [tibial-cartilage variant review](msk-openknee-tibial-review/README.md)
acquired both unversioned candidate masks and the raw/earlier processed surfaces.
It found approximately 8.7% and 11.7% smaller enclosed volumes in the selected
surfaces relative to those masks. This quantifies source representation changes,
not anatomical error; exact revision ancestry remains unresolved. A plane/mesh
edge-case correction restored valid raw-surface intersections, while all existing
84 section results reproduced byte for byte. No runtime surfaces were replaced.

The 14 mapped structures were inspected on 84 native planes across the general
and cartilage sequences. Original MRI samples and source mesh coordinates are
unchanged; only the author labels are nearest-neighbor sampled at the image
voxel centers for comparison. `tools/anatomy_sources/audit_openknee_pair.py`
reproduces this check. [Durable review sheets and numerical evidence](msk-openknee-source-review/README.md)
include the two MRI acquisition records, exact source-mask mappings and all
14 rendered comparisons. LCL has the lowest section overlap and remains a
source-resolution/smoothing limitation; overlap is not biological accuracy.

The public viewer preserves native RAS coordinates in its buffers and applies
a documented display rotation to positions and normals. It uses left-sided
lateral/medial camera presets. Sixteen separate evidence records are inventoried
without automatically binding whole-object names to fine structure requirements.
The two uncertain tibial-cartilage mask mappings remain explicit. No original
MRI, label volume, or diagnostic image pair is published by this integration.

Static geometry bounds, transport decoding and HTTP gzip delivery passed, as
did five coordinate/camera tests and the combined 368-test MSK/API regression
run. [Browser verification](msk-hip-knee-browser-audit-2026-09-26.md) passed all
16 isolated objects, five layers, source switching/disposal, left-side presets
and mobile controls, with no raw-volume requests or WebGL errors. These checks
support source integrity and rendering, not clinical certification.
