# Complete provided-grid plane package and source-case preview

This packet prepares case 1 for bounded source-plane access. It preserves all supplied samples in two processed MRI volumes and two separate binary source annotations. The 82 cached pack files contain 4,980 independently compressed source-index planes, totalling 1,223,389,436 bytes. No full MRI volume is required by the preview client: the largest decoded plane is 806,384 bytes, and the decoded cache is bounded to 16 MiB.

Each of the three source-axis families reconstructs every original volume exactly. The independent checker derives native storage offsets for every supplied voxel and compares the reconstructed byte stream with the literal original NIfTI data segment after its original header offset. It verifies 827,349,984 scalar reconstructions across the three axis families, all member hashes/ranges/gzip streams and every original sform/qform matrix. This is supplied-data integrity, not independent biological validation.

The tiny non-zero MRI affine terms are retained. The viewer displays original i/j/k planes with dominant source-coded RAS directions; it does not round the affine to axis alignment or reslice images. For the explicitly used sforms, corner bounds prove nearest original annotation lookup equals corresponding source indices over the whole grid. The annotation qform displacement of 22.5 mm remains disclosed and unchanged. The source MRI was already registered/resampled by its authors; it must not be described as newly acquired 0.5 mm detail or acquisition-native imaging.

The controlled phone/desktop preview passes 40 cases covering both contrasts, source ROI/full-plane display, central/edge source indices, checksum-verified byte ranges and source sample/coordinate probes. Independent original-NIfTI reconstruction matches 21,280,840 actual plain/marked canvas pixels. Both processed source-mask models are byte-checked in GPU buffers at both widths; six camera states retain all source vertices within the frame. These are source-mask boundaries: closed endpoint faces indicate label extent, not vessel occlusion, separate vessel walls or isolated tumour tissue.

Large original MRI and pack payloads remain in the ignored `.research/pituitary-case-source-20261101` cache. This Git packet retains compressed metadata, verification proofs, recipes, the two source-mask model packages, the preview code and twelve original portable verification planes. Their combined compressed size is about 3.25 MB. The portable tests recheck these planes and captured initial renders; they do not claim a fresh full-volume reconstruction on a machine without the cached originals/payloads.

Rebuild or independently check all cached provided planes:

```
python tools/anatomy_sources/package_pituitary_provided_planes.py
python tools/anatomy_sources/check_pituitary_provided_planes.py
```

The tools accept explicit source/output locations. Historical preview and model-generation recipes are under `recipes/`; run from the repository root against the original ignored staging directory. No publisher shell script is executed. No source MRI/header is rewritten, and no fitting, smoothing, repair or extra component deletion is applied by Primer.

The original dataset remains CC BY 4.0 with the source attribution and limits in the parent evidence packet. This preview is not application-integrated, hosted, clinically approved or complete sellar coverage. The complete radiology/math/physics goal remains active.
