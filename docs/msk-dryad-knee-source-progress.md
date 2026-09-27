# Dryad knee source acquisition and fidelity review

Reviewed 26 September 2026. **Acquired research candidate; no clinical replacement
approved.** This supersedes the earlier metadata-only acquisition status.

## Verified acquisition

The [public Dryad record](https://datadryad.org/dataset/doi:10.5061/dryad.zkh1893gw)
identifies CC0-1.0 and a left-knee source. Current metadata is version 6 (API
version 273935). Each acquired file matches the published size and SHA-256:

| File | Bytes | SHA-256 |
|---|---:|---|
| README.md | 44,551 | `47d697b44376677487a587f0f7efde6b5396b47d33b3338045d639fa73effd08` |
| STLs.zip | 141,495,698 | `873f56215c90634e249ce122cf6f558ce85615d80a708c0c1b45b7b6d7379362` |
| Imaging_Data.zip | 637,706,876 | `aa3fa1453cf20491494ef69dd02ed6bc92eb01e272159a5f3e4cdf6b2a5f9831` |

Earlier web/API attempts returned 403/401. The normal public browser controls
subsequently worked: the README was saved and the archive links issued ordinary
repository download redirects. The exact issued destinations were downloaded;
no cookies, authentication, hidden endpoint guesses, modified signatures or
challenge bypass were used. Originals remain in
`/tmp/primer-msk-sources/dryad-knee/`; durable acquisition records and the source
README are in [the review folder](msk-dryad-knee-source-review/README.md).

A bounded range preview inspected MRI entries while the full download was live.
The final audit re-extracted from the **complete SHA-verified archive** and
checked every selected member's original CRC and byte count. ZIP method 9 is
Deflate64, so extraction used the installed native Info-ZIP decoder rather than
unsupported Python `zipfile` decompression. No downloaded code was executed.

## Actual geometry

The 12 raw MRI-derived ASCII STLs match the README's inventory of major bones,
three cartilage objects, medial/lateral menisci and ACL/PCL/MCL/LCL. All extracted
files match their archive members byte for byte. There are **631,032 nonzero
facets**, with no boundary/nonmanifold edges, duplicate facets or inconsistent
paired-edge winding. Global self-intersections were not assessed.

All filenames disclose smoothing and all headers name MeshLab. Roots, ligament
bundles, attachment footprints and fine capsular structures are not independently
labelled. Lateral tibial cartilage remains visibly coarse. The tibia/fibula
object visibly includes both bones but is one connected surface; this does not
establish independent bone boundaries or physiological joint continuity.

The [geometry review](msk-dryad-knee-source-review/geometry-review.md) and
[exact measurements](msk-dryad-knee-source-review/geometry-audit.json) preserve
native-coordinate renderings and separate-source comparisons. The
[linked publication](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2025.1554836/full)
evaluates CT/surface-scan biomechanical models with ligament connectors; that
validation does not certify these separate MRI STL boundaries.

## MRI export and pairing limitations

The scan and all 12 masks specify a `1024 × 1830 × 130` unsigned-byte grid,
approximately **0.5127 × 0.5127 × 2 mm**. This has finer in-plane sampling but
coarser slice spacing than the current Malaya export, not a uniform improvement.

`S192803_MRI_Scan.raw` has the correct 243,609,600 bytes and original CRC, but
only **15,475 nonzero voxels (0.00635%)**. Their index bounds are Z 62–83,
Y 964–999, X 521–594. Native slices and whole-grid projections show a small
local grayscale region on an otherwise black grid. This describes limited
exported content; it does not establish why the export is sparse or identify
the region by appearance. Index-space images also have anisotropic sampling.

All masks share the exact declared grid. Nonzero scan content overlaps all
5,826 lateral tibial-cartilage mask voxels and parts of the tibia/fibula,
femoral-cartilage and lateral-meniscus masks. It has no nonzero overlap with
the ACL, PCL, MCL, LCL, femur, patella, medial tibial-cartilage or medial-meniscus
masks. These are index-space comparisons, not proof of registration or anatomy.
The export cannot support a complete knee image/mesh comparison.

The usual `Offset + M × (Spacing × index)` calculation does not align ACL mask
bounds with the STL. `Mᵀ × (Offset + Spacing × index)` comes closer numerically,
but is not a documented source transformation. No transform was adopted or fitted.

The [full imaging audit](msk-dryad-knee-source-review/imaging-audit.json) records
all 13 original headers, hashes, CRCs, voxel histograms, extents, mask overlaps
and explicit frame calculations. An independent reader re-extracted the scan,
ACL and patella from the complete archive and reproduced their raw hashes,
CRCs, counts, zero overlaps and both frame calculations. The
[MRI content review](msk-dryad-knee-source-review/mri-export-content-review.png)
is an offline source-quality artifact, not a clinical image in Primer.

## Decision and reproducibility

Retain this source offline. A complete MRI export, documented coordinate
convention, and anatomical review of boundaries and missing components are
needed before promotion. CC0 permits reuse; it does not certify fidelity.
A [technical inquiry](msk-dryad-knee-data-inquiry.md) is prepared but unsent.

Reusable tools are `tools/anatomy_sources/audit_dryad_knee_geometry.py` and
`tools/anatomy_sources/audit_dryad_knee_imaging.py`; see their `--help` options.
They require NumPy/Matplotlib (plus SciPy for geometry) and native Deflate64-capable
`unzip` for imaging. The imaging tool verifies the full archive before extraction:

```sh
python tools/anatomy_sources/audit_dryad_knee_imaging.py \
  --archive /tmp/primer-msk-sources/dryad-knee/Imaging_Data.zip \
  --output /tmp/primer-msk-sources/dryad-knee/imaging-audit \
  --geometry-audit /tmp/primer-msk-sources/dryad-knee/geometry-audit/geometry-audit.json
```

Original pixels, masks and surfaces remain unchanged. No runtime asset,
requirement, evidence approval or commercial-readiness claim was promoted.
