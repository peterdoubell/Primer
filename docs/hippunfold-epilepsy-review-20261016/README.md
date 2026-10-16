# Hippocampal source reference and epilepsy guidance

The epilepsy and dementia lessons and reporting views gain an interactive T2 MRI and categorical surface reference for published HippUnfold HCP-YA case 101006. The same reference is available in the reporting images, models and step-by-step views. Existing reporting guides and examples remain available.

This addition advances hippocampal source inspection. It does not complete either module or grant clinical approval. The wider radiology, mathematics and physics objective remains open.

## Source and permissible interpretation

- [DeKraker and Khan, HippUnfold HCP-YA Training Data v1.0.0](https://zenodo.org/records/7007362), DOI 10.5281/zenodo.7007362, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- [Published HippUnfold methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC9831605/) and the publication-linked software v1.2.0, commit `aad27a64e6d1649f7313b72c1cedb7245f88bfe6`, inform interpretation. Dataset and software version numbers are distinct.
- The source provides bias-corrected, affine-atlas-registered, resampled coronal-oblique crops. Approximately 0.3 mm is the upsampled grid spacing, not the acquisition resolution. This viewer preserves the supplied filenames, arrays and affines with no additional mirror or anatomical fitting.
- The source methods describe left mirroring. The exact exported archive stage remains unresolved. “L” and “R” therefore identify the supplied source files, not independently validated patient laterality. The viewer does not offer native volumetry, asymmetry scoring, MTA scoring or diagnosis.
- Source classes are supervised research labels. Hippocampal grey matter and SRLM are accompanied by combined entorhinal/parahippocampal boundary context, pial boundary, HATA, posterior boundary context, cyst and DG granule/end-point classes. They do not supply separate CA1–CA4/subiculum fields, whole amygdala, whole dentate gyrus/hilus, whole meninges, complete fornices or mammillary bodies.

## Preserved source and geometry

The four original NIfTI files are retained in `originals/`. The source label ZIP's published MD5 was verified. Two T2 NIfTI members were extracted through exact HTTP byte ranges and verified against their ZIP CRCs. The full 3.31 GB T2 archive was not downloaded or whole-archive hashed. Acquisition evidence records this distinction.

All 8,388,608 T2 values and 8,388,608 categorical values across the two sides recover the original Float64 values bit for bit from Float32 T2 and Uint8 label transport. Array order is `i + nx * (j + ny * k)`. Every mesh uses the matching supplied image affine. No image resampling, smoothing, source component deletion or surface fitting occurs in the viewer.

The 16 displayed surfaces contain all 236,196 exposed voxel faces as 472,392 triangles. These are exact boundaries of categorical voxel cells, with outward normals. They are visibly stepped boundaries of the source segmentation, not smooth biological tissue boundaries or trilinear isosurfaces. Source checkerboard contacts remain present; they are not silently repaired into manifold anatomy. The independent face-transition and ray reconstruction checks, including 201,326,592 voxel comparisons, are retained in `mesh-independent/`.

An earlier marching-cubes prototype had inward winding and duplicate opposite triangles; it is excluded from the product. Its diagnostic proof is retained to explain the method decision. No smoothing or reconstruction is substituted to conceal those errors.

## Clinical text correction

Five fields now describe the transmantle sign as supporting FCD type II, most often IIb, without treating MRI as balloon-cell histology or a surgical-outcome guarantee. Legacy technique summaries now specify isotropic 3D T1 and 3D FLAIR with high-resolution coronal T2 perpendicular to the hippocampal long axes. The exact field changes and primary ILAE sources are in `clinical-corrections.json` and `clinical-corrections.md`.

The existing FCD figure remains correctly captioned and bound. It does not supply separate examples of tumour, cavernoma or scar.

## Verification and remaining scope

Source receipts and fingerprints are indexed by `source-evidence.json`. Independent coordinate and method findings remain separate from actual product browser and authenticated-reader checks. The final product viewer passed 132 full-pixel states, 38 camera-fit states and all 16 GPU mesh checks in each of two delivery modes: raw gzip and HTTP-decoded gzip. GPU source-coordinate error was at most 2.414e-6 mm. Transport checks accepted 43 valid representations and rejected 187 invalid cases. Metadata HTTP/network/JSON/schema failure and retry, source corruption and mesh corruption were also tested. These records bind to the final viewer bytes in `product-viewer/`.

`reader-proof.json` records 16 authenticated reader cases across two modules, four surfaces and two widths, covering 320 interaction states. It verifies the exact current startup bundle, every actual delivered payload, all 16 GPU buffer identities per case, retained reporting guidance, expected access/path rejection, iframe policy, and absence of page errors, CSP violations and horizontal overflow. It uses an isolated synthetic local database; it does not claim an authenticated production learner flow. The 14 source tests independently recover all original Float64 samples and check all exposed labelled-cell faces.

Run source and delivery checks with `python -m pytest tests/test_hippunfold_reference.py -q` and `node tools/check_hippunfold_transport.cjs`. The browser check accepts `HIPP_VIEWER_URL`, `HIPP_PROOF_OUTPUT` and `HIPP_MRI_ORACLE`; use the committed `coordinate-independent/mri-original-oracle.json` as its independent pixel oracle. The authenticated reader checker reads the private fixture produced by `tools/start_optics_reader.py` from standard input and writes its JSON proof to standard output; that launcher creates a loopback server with isolated synthetic data and empty Turso configuration. Private fixture credentials are not part of the published evidence.

`requirements-independent/epilepsy-requirements-map.json` is the pre-integration research snapshot pinned to base commit `8c8d841`; its “current” flags describe that captured state. It maps the reporting groups, source-class limits and quiz prompts. The transmantle and legacy-technique findings are resolved by this change, and the source-descriptor finding is superseded by the new registered reference. The current inventory is `docs/radiology-fidelity-scope.json`, with the exact four-row update recorded in `current-scope-refresh.json`. Missing or incomplete evidence includes hippocampal pathology and FLAIR, full limbic anatomy, cortex and migration disorders, tumour/vascular/scar examples, skull-base encephaloceles, dual pathology, whole-brain exclusion and electroclinical integration. Source fidelity alone cannot prove clinical completeness, normality or diagnostic accuracy. These requirements remain open.

Historical compatibility records reverse only exact documented changes to frozen review comparisons. They do not rebaseline old evidence or extend approval to this source.
