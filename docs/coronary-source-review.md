# Coronary source acquisition and access review

This source review preserves the complete coronary CTA goal. No restricted CT upload or differently licensed mirror is treated as commercial permission, and no new source is assigned clinical representation credit.

## ASOCA

The [official challenge](https://asoca.grand-challenge.org/) describes lumen annotations and routes current access to [UK Data Service](https://reshare.ukdataservice.ac.uk/855916/). The depositor requires permission for the data. The [source publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC10006074/) permits research/commercial purposes while requesting evidence of project ethics approval or waiver for access. No application, message or ethics claim has been submitted. An unsent access/reuse clarification draft is in `coronary-source-review/asoca-access-request-draft.md`.

## ImageCAS and ImageCAS-X

Pinned [ImageCAS-X annotation record](https://doi.org/10.5281/zenodo.21887809) lists CC BY 4.0. The publisher archive contains 800 annotation sets, corresponding centreline/surface files, split lists and a descriptor workbook. The [author repository](https://github.com/kitbransby/ImageCAS-X) defines fourteen coronary branch labels plus background. These are lumen/branch annotations; they do not directly provide plaque, wall layers, grafts, stents or physiological evidence. The associated 2026 preprint is under review.

The author repository obtains the underlying CT images separately from the original ImageCAS uploader. Current official Kaggle API metadata marks `xiaoweixumedicalai/imagecas` as CC BY-NC 4.0. Other uploader mirrors show different licence labels; those do not establish permission from the original CT rights holder. The annotation grant is recorded separately and does not clear reuse of the original CT images. Annotation derivation/reuse scope still requires review before any commercial promotion; this is a scope hold, not a claim that the declared annotation licence is invalid.

Source metadata and author documentation were acquired. Verified HTTP ranges and a stable archive ETag provided the ZIP directory, five metadata members and four annotation members for case 134. Every acquired member matches its uncompressed byte length and ZIP CRC, with independent SHA-256 records. The complete archive was not downloaded, so the publisher's full-archive MD5 is not claimed verified. No underlying CT image was acquired.

The first available archived case with published `L` dominance and `no` disease descriptors was selected. Numeric image-quality code `2` is retained without inferring its rank. These are unconfirmed source descriptors; `no` coronary disease does not establish a globally healthy patient. The original case label volume and all published centreline/surface files remain unchanged and offline under `.research/coronary-sources/imagecas-x-case-134`.

The mask has 512 × 512 × 206 voxels, declared mm units, 0.318359375 × 0.318359375 × 0.5 sampling, LAS storage axes and agreeing declared qform/sform. Present labels are LAD, LCx, D1, OM1, RCA, left PDA and left posterolateral branch. There are no LM-labelled voxels. That missing label is not evidence of anatomical LM absence and cannot fulfil the left-main requirements. Other missing branch labels are likewise not fabricated.

The two centreline VTK files are legacy binary float arrays; the surface VTK is legacy ASCII double data. Their declared formats were respected after inspection. The point bounds suggest a coordinate-convention difference from the NIfTI RAS bounds, and source surface bounds also differ from the voxel-centre extent. No fitted transform, axis flip, smoothing, registration or clinical accuracy claim was applied. Coordinate convention, source surface processing, label associations and acquired-image fidelity remain unverified.

## Other candidates

A cardiac CT Figshare share link appeared in search, but the live page was unavailable; creator, access and complete rights evidence remain unverified. A CC BY 4.0 Mendeley cardiac segmentation record was located, but its native volume/file inventory was not established. Neither is claimed acquired or suitable for coronary lumen evidence. These remain leads rather than replacements for the required CCTA source.

## Preserved evidence

`docs/coronary-source-review/` contains the pinned annotation metadata, selective member acquisition hashes, case descriptors, native label/VTK inspection and `rights-and-access-review.json`. The full archive directory and original source metadata remain offline. No source image/model was integrated into the reader, no clinical approval was granted, and every coronary requirement remains pending.

## Supplied geometry versus native annotation

The author repository was inspected at commit `dbc7343187adf45ca9306dc3460eebc70f92b204` (2026-09-01). Its mesh-generation code documents native physical LPS millimetres, foreground binarisation, marching cubes and windowed-sinc smoothing. The centreline sampling code also documents LPS. The archived surface contains the documented `voxel_coords_resampled` field. This supports using the standard LPS-to-NIfTI-RAS basis conversion for analysis; it does not attest the exact archive-generation commit or smoothing parameters.

All 20,242 archived surface points were also checked against that stored index field using the current published 0.5 mm resampling configuration and original label-header origin/direction. Maximum consistency error is about 3.33e-6 mm, without fitting a transform. The original CT header is unavailable, and the exact archival configuration is not asserted. `source-code-review.json` and `imagecas-x-case-134-coordinate-field-audit.json` preserve the pinned code/configuration evidence and scope limits.

The supplied 40,472-triangle surface has no boundary or nonmanifold edges in the incidence check, but does not reproduce the native foreground selection exactly. Across 7,921,368 voxel-centre comparisons, it adds 648 interior voxels and omits 1,435 source voxels. Foreground Dice is approximately 0.936546. Omitted voxels by source label are LAD 419, LCx 259, D1 208, OM1 286, RCA 139, left PDA 92 and left posterolateral branch 32. All original labelled foreground is within the compared bounds. These numbers measure surface/annotation consistency, not independent anatomical accuracy or clinical stenosis correctness. The supplied surface and source voxels remain unchanged.

A separate unsmoothed baseline was derived directly from all positive native source labels, with no component removal or invented LM connection. It retains all three source annotation components and has 40,472 triangles. Across 8,018,336 voxel-centre comparisons, all 16,807 original foreground voxels are retained with zero extra interiors or omissions. No original CT data or quantitative clinical measurement is inferred. Closure follows annotation endpoints rather than independently validated physical vessel endings; branch identity remains in the unchanged multi-label volume.

The baseline stays offline in `.research/coronary-sources/imagecas-x-case-134-baseline`. Records are `imagecas-x-case-134-surface-label-audit.json`, `imagecas-x-case-134-baseline.json` and `imagecas-x-case-134-baseline-voxel-audit.json`. Reproduction uses `tools/anatomy_sources/audit_imagecas_source_geometry.py` and `build_imagecas_voxel_baseline.py`. Three analytical VTK-reader tests passed, explicitly distinguishing ASCII double points from binary big-endian float arrays and rejecting unsupported polygon tessellation.

The voxel-consistent baseline is not a clinical approval or replacement for missing branches, calibrated CTA images, walls/plaque, physiology, appropriate data rights or specialist anatomical review. No source was promoted into the reader and no coronary obligation was marked complete.
