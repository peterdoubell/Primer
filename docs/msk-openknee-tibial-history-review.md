# Open Knee(s) oks003 tibial-cartilage ancestry review

Reviewed 2026-09-26. **The exact ancestry of the two selected `_02` surfaces remains unresolved.** This pass found new author documentation explaining how to identify the selected assembly, but no record establishing which mask and processing operations produced these particular revisions. It does not repeat the [existing numerical comparison](msk-openknee-tibial-review/README.md), replace source geometry, or approve anatomical fidelity.

## Access boundary

The installed environment has no `svn` executable. Apache's [documented read protocol](https://svn.apache.org/repos/asf/subversion/trunk/notes/http-and-webdav/webdav-protocol) identifies `PROPFIND` as a read method for version metadata. One depth-zero request to the published lateral `_02` STL asked for its version and history-discovery properties. The server returned **HTTP 403**. That route was stopped: no `REPORT` retry, alternate protocol/hostname, guessed revision URL, authentication bypass or author contact followed.

The new documents below were independently published files linked from already acquired public repository directory listings. They were read through ordinary successful GET requests, not through an alternate attempt to retrieve denied history.

## New source evidence

The [author simulation notes](https://simtk.org/svn/openknee/oks/oks_simulation_notes.odt) explicitly explain that segmentation and geometry folders retain multiple attempts and direct users to the Model connectivity file to identify the surfaces used for assembly. The `oks003` entry reports a successful simulation with ties, contacts and prestrain, but supplies no tibial-cartilage `_02` processing history. Its later troubleshooting entries document specific changes for other specimens; those must not be borrowed as explanations for `oks003`.

The [author review procedure](https://simtk.org/svn/openknee/doc/OKS_Review_Procedure.odt) includes segmentation/geometry selection tables for other specimens. At `oks003`, instead of a completed chart, it asks:

> Oks003- should we use the knee hub segmentations? Or use only the existing segmentations on the open knee site?

The document's internal last-edit metadata is 4 January 2019. This is evidence of an unresolved question in that particular document, **not** proof that later model work remained unresolved. It cannot establish the selected meshes' input masks. The published [segmentor-folder README](https://simtk.org/svn/openknee/oks/Segmentors/Readme.txt) identifies four other segmentors and provides no AGS `_02` processing record, so that branch was not crawled further.

## What the already acquired version headers show

| Source files | ETag revision marker | Available Last-Modified |
|---|---:|---|
| Unversioned lateral/medial AGS masks | 2099 | 16 May 2019, 18:43:09 GMT |
| Raw, earlier-processed and selected `_02` AGS surfaces | 2100 | Selected `_02` files: 16 May 2019, 18:51:07 GMT |

These are recorded transport/version headers, not recovered SVN log messages. The nearby revisions and timestamps support a related publication batch, but do not establish an order among raw, earlier and `_02` surfaces uploaded in the same revision. Neither timestamps nor the numerical overlaps prove direct ancestry.

The selected [Model/Connectivity.xml](https://simtk.org/svn/openknee/oks/oks003/Model/Connectivity.xml) unambiguously names `oks003_TBC-L_AGS_LVTTIT_02.stl` and `oks003_TBC-M_AGS_LVTIT_02.stl`. Their original SHA-256 values remain:

- Lateral: `298f2bf3c8225a3125ed2fee2226d837b578deb3f1385c49eaf9319ac58e864e`.
- Medial: `cb45845df56e1d0c22db6eaf780282b904fdbcb65e1e2e5fe57e0235f1800b4d`.

The existing processing specification explains smoothing, reconstruction, remeshing and possible repair in general. It is not a per-file log. The new author notes strengthen the decision to retain the explicit selected assembly, but do not justify silently assigning the two unversioned masks to it.

## Remaining decision and preserved evidence

Retain both current meshes and their unresolved mask-version mappings. The missing evidence is specific: an accessible history entry or author processing record linking each exact `_02` file to its input segmentation and explaining the subsequent operations. It remains unknown whether the additional differences arose from remeshing, smoothing, repair, manual surface edits or regeneration from another segmentation. No operation should be inferred merely to explain a smaller enclosed volume.

New originals, extracted text, request/error record and machine-readable conclusions were staged in `/tmp/primer-msk-sources/openknee-public-pass/tibial-history-review/`. On 27 September, the small original author documents, text extractions, stopped-request record and provenance JSON were durably preserved in [msk-source-followup-review/openknee](msk-source-followup-review/README.md). Their acquired-document hashes were rechecked against the original provenance record; no history request or numerical comparison was repeated.

| New document | Bytes | SHA-256 |
|---|---:|---|
| `oks_simulation_notes.odt` | 31,756 | `24ed97b0f0674329bb9ad229202cb2b54c1b952d4dc3e100961e2a8e562ba13f` |
| `OKS_Review_Procedure.odt` | 20,536 | `5b8c2f2538f17d22eff814ccf2361819e6644d6bb474619c8d4fe016deb49197` |
| `segmentor-readme.txt` | 110 | `dca07942739ae9243df49cbbb5bf1ad30718fab642f23c825479d11347b0588a` |

`provenance-review.json` (SHA-256 `78f68ffb171bf8e375dd146b1fc8fa8ea1e0a18d23774b82bf7e4182a556ed0f`) fingerprints every acquired document and the inspected runtime manifest, records the exact 403 request, and separates supported findings from residual uncertainty. Original masks/meshes and runtime geometry, catalog and evidence ledger were unchanged. No clinical approval or new comparison result was generated.
