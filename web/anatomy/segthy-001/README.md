# Native SegThy reader

This reader consumes the separately acquired `001_P1_1_left` and
`001_P1_1_right` ultrasound packages. It never combines their arrays or uses
the centered affines to establish registration. I/J/K name source array axes;
they do not assert patient orientation.

`viewer.js` pins the tested `manifest.json` SHA-256. Update that receipt when
changing authored metadata or generated source assets. Brick and mesh delivery
verifies the compressed length and SHA-256, the decompressed SHA-256, and the
expected decoded length. Brick reads share three fetch slots and retain at most
12 MiB of decoded data in the active sweep's LRU cache. A failed verification
hides the affected raster or surface until an explicit successful retry.

Each raster is a native section: the horizontal source index increases rightward,
and the vertical source index increases upward. Display options change only the
rendered pixels. Click readouts always use the original uint8 intensity and label.
The scale bar uses native grid pitch. Section area is selected-code pixel count
multiplied by the two in-plane pitches. Segmented volume is the supplied native
mask voxel count multiplied by all three pitches, divided by 1000 for mL. These
are measurements of the manual segmentation in this sweep.

The WebGL adapter reuses the shader, typed-buffer implementation, derivative
lighting and orbit transform from `bp3d-dural-4.3/surface-viewer.js`. It loads
only the selected source mask mesh; the plane locator uses the same native index
and spacing convention. Orbit controls have pointer, keyboard and range-input
alternatives.

## Validation receipt (2026-11-22)

Tested package manifest:
`d054557d2c5e6230c49659c23812a4f91d2d044ffc43d4f4b31aca88b0f5e440`.
Independent nibabel reads of the four original NIfTI files verified source shapes,
uint8 range, all six voxel counts and interior focuses. All 18 label-focus sections
across I–J, I–K and J–K matched full native image and label SHA-256 values.
At 1200 px and 390 px viewport widths, all 180 complete canvas comparisons matched
independently computed grayscale, selected/all outlines and selected/all fills;
144 voxel-coordinate/intensity/label click readouts passed. All six full source
meshes loaded. Section keyboard, orbit keyboard and pointer controls, rapid sweep/
plane/label changes, scaled native width, source scale bars, provenance and page
width were checked. Injected 503 responses verified raster and mesh failure/retry;
incorrect compressed length/hash and decoded hash were rejected. Synthetic cropped
edge-brick, concurrent-cache, cancellation and malformed-inventory tests passed.

To reproduce the source comparison, run
`python tools/anatomy_sources/verify_segthy_ultrasound.py SOURCE_DIR web/anatomy/segthy-001`
from the repository root. The four NIfTI inputs and their hashes are identified in
`manifest.json`. [Attribution and packaging details](ATTRIBUTION.md).

After editing this reader, run
`python tools/anatomy_sources/package_segthy_ultrasound.py --delivery-only web/anatomy/segthy-001`
to update the file hashes used by its delivery inventory.
