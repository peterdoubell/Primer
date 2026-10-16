# Epilepsy pathology figures

Six complete publisher-served figures now supplement the epilepsy reporting reference and lesson. The existing key images, clinical guide, report templates, diagrams and registered HippUnfold viewer are preserved. The Images tab and lesson source gallery show the complete source captions; four walkthrough steps link the appropriate new examples.

| Source | Teaching role | Essential boundary |
|---|---|---|
| Abud et al., Clinics 2015, Figure 1 | Selected coronal T2/FLAIR hippocampal sclerosis example | Publisher-assigned right hippocampal head; no complete head-to-tail series or calibrated volume. |
| Sone, Frontiers 2021, Figure 4 | Hippocampal architecture comparison | Separate HS and normal comparison images, each enlarged below. Panel layout does not assign patient laterality. |
| Sone, Figure 3 | FCD visibility on FLAIR | Row C changes the display range of row B. IIb is the article’s postoperative pathology result, not MRI-derived histology. |
| Abud et al., Figure 6 | Ganglioglioma morphology and enhancement | T2 and post-contrast T1, not a T1 pre/post pair; the source names the diagnosis without documenting histology here. |
| Abud et al., Figure 7 | Cavernous-malformation morphology and susceptibility | GRE is not SWI. The marked lesions differ across the two panels. |
| Sone, Figure 2 | Encephalocele on T1/CISS | Selected sequence groups; no measured bone defect, CT confirmation, patient side or complete herniation extent. |

The three JPG and three WebP originals total 3,400,899 bytes. They retain the exact encoded bytes, decoded samples, dimensions, original annotations, panel layout and available colour-profile metadata. Publisher raster dimensions do not establish native acquisition resolution, the largest possible original or submitted TIFF identity. Nothing is cropped, enhanced or segmented.

Sources: [Abud et al.](https://www.scielo.br/j/clin/a/JFNmN3SqynTg3vTv7ndPpGs/?lang=en) and [Sone](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2021.699176/full). Article/publisher records support CC BY 4.0, and independent inspection found no separate third-party exception for these six figures. Complete author attribution, supplied copyright, DOI, figure citation, direct image URL, license link and unchanged-byte notice accompany each figure. Source snapshots and independent reviews are retained in `source/` and `integration-independent/`.

## Verification

- `tests/test_epilepsy_pathology_figures.py`: source and archival-storage checks cover original encoded/decoded identities, source captions and rights, exhaustive panel joins, repeated/display-variant roles, original guide/binding preservation, empty structure-coverage claims and static delivery metadata.
- Together with the existing HippUnfold tests, **20 tests passed**. An additional **37 relevant radiology scope, static-raster, module-media and neuroradiology tests passed**.
- `reader-check.cjs` and `reader-proof.json` verify **36 cases**: six figures across Images, walkthrough and lesson gallery at 390 and 1440 pixels. Exact delivered image bodies, original dimensions, complete source-caption access, unfiltered display and full-size label inspection passed without page errors, CSP violations or horizontal page overflow. The existing HippUnfold inline viewer still loaded. This uses an isolated authenticated loopback fixture with synthetic data, not production learner writes.
- Current scope refresh affects only `ra.mri-epilepsy` and `rad.5.epilepsy-mri`. All 136 investigations and 106 curriculum nodes remain inventoried; 40 investigations remain unexpanded. See `current-scope-refresh.json` for exact before/after hashes and bounded provenance.

The existing modal entrance animation and object-fit letterboxing are respected by the reader verifier: it waits for the animation to finish before checking native-size rendering, and accepts an undistorted contained image inside a larger display box. No UI change was needed.

The historical evidence suite initially rejected the new image arrays and companion because the prior HippUnfold inverse requires exact recorded bytes/contracts. The log and failure inventory were handed to the release owner for a new bounded inverse. Historical proofs and broad compatibility code were not changed by this implementation.

## Archival publisher storage

The SciELO publisher snapshot is evidence, not application HTML. Its original 172,478 bytes are stored losslessly as `source/scielo-publisher.html.gz` with gzip mtime zero. `source/archive-storage.json` records the compressed and decoded byte counts and SHA-256 identities. Historical source reviews keep the original logical name `scielo-publisher.html` and its original decoded hash; the provenance tests resolve that name through the exact storage mapping before checking rights and captions. The third-party document's JavaScript and URLs have not been rewritten or executed.

To reproduce the decoded identity without restoring an active HTML file:

```sh
python -c "import gzip, hashlib; from pathlib import Path; raw=gzip.decompress(Path('docs/epilepsy-pathology-figure-review-20261016/source/scielo-publisher.html.gz').read_bytes()); print(len(raw), hashlib.sha256(raw).hexdigest())"
```

Expected output is `172478 9ece3e6704431495bb43c39f4c4ef40d602c50d26bafb4a45a2068ff6c4842f6`. This is a storage-only change: product assets, runtime data, source captions, original rights records and historical proof hashes remain unchanged.

## Reproduce

Run the tests from the repository root with its test Python environment. For the reader check, start `tools/start_optics_reader.py --fixture /path/to/private-fixture.json` using its isolated loopback launcher, then run:

```sh
NODE_PATH=/path/to/playwright/node_modules node docs/epilepsy-pathology-figure-review-20261016/reader-check.cjs < /path/to/private-fixture.json > /path/to/new-reader-proof.json
```

The script rejects non-loopback fixtures. Credentials and learner data remain outside this evidence directory. `intended-changes.json` records the plan before product edits; `preservation-baseline.json` captures the original guide and existing media; `metadata-refinements.json` records the two corrections from independent review. The exact rights/provenance proof is `original-source-review.json`.

## Remaining work

Every new evidence row has empty `structure_ids` and `requirement_coverage`, with anatomical review pending. The six examples do not provide complete bilateral hippocampal extent, fornices/mammillary bodies, all cortex/migration anatomy, DNET-specific evidence, injury/gliosis or reversible peri-ictal examples, complete skull-base geometry, a whole-brain exclusion of dual pathology, native lesion meshes or clinical certification readiness. The full module goal remains open.

The reusable `reader-check.cjs` consumes its private loopback fixture on standard input and writes the current JSON proof to standard output. Redirect that output to a new local result when rerunning it; the retained review proofs are never overwritten by the checker.
