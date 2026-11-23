"""Package two paired intensity/label volumes from SegThy's manual training tier.

Run with the directory of 001_P1_1_{left,right}_{image,mask}.nii.gz and an
output directory. Inputs are from the MedOtter/SegThy mirror at the revision
below. NIfTI payload pins also permit an independently obtained gzip encoding.
"""
import argparse
import gzip
import hashlib
import io
import itertools
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from skimage.measure import marching_cubes


REVISION = "318d0e04578419d2976a093f9873f14b782f253d"
MIRROR = f"https://huggingface.co/datasets/MedOtter/SegThy/tree/{REVISION}"
PINS = {
    "left": (
        "a121ae56daad64b91183190faa08dc53fa71a27608e41919034076fc4538b293",
        "a77aa43696526e6167445ddbc72a99d300390c99f312740e4a673b1072e6cf87",
    ),
    "right": (
        "168328e09b717340382e9e6f7b36e2eb9103c249c63b271f8be11311f11f07f0",
        "3ab8a9eb4d554c072a5983ed51cfbb5996ff88631b69e8bf21ebeeb4aa67f3fa",
    ),
}
LABELS = {1: ("thyroid lobe", [255, 192, 72]), 2: ("carotid artery", [239, 108, 109]),
          3: ("jugular vein", [87, 201, 245]), 4: ("carotid artery", [239, 108, 109]),
          5: ("jugular vein", [87, 201, 245])}
BRICK = 96


def sha(data):
    return hashlib.sha256(data).hexdigest()


def store(directory, name, raw):
    packed = io.BytesIO()
    with gzip.GzipFile(fileobj=packed, mode="wb", compresslevel=6, mtime=0) as stream:
        stream.write(raw)
    blob = packed.getvalue()
    (directory / name).write_bytes(blob)
    return {"file": name, "bytes": len(blob), "sha256": sha(blob), "decodedSHA256": sha(raw)}


def package_case(inputs, output, side):
    identifier = "001_P1_1_" + side
    images = []
    sources = {}
    for role, payload_sha in zip(("image", "mask"), PINS[side]):
        path = inputs / f"{identifier}_{role}.nii.gz"
        packed = path.read_bytes()
        if sha(gzip.decompress(packed)) != payload_sha:
            raise ValueError(f"Unexpected NIfTI payload for {identifier} {role}")
        images.append(nib.load(path))
        sources[role] = {"payloadSHA256": payload_sha, "mirrorPath": f"us/train/{role}s/{identifier}.nii.gz"}
    image, mask = images
    if image.shape != mask.shape or not np.array_equal(image.affine, mask.affine):
        raise ValueError("Image and mask grids differ")
    data, labels = (np.asanyarray(item.dataobj) for item in images)
    codes = [1, 2, 3] if side == "left" else [1, 4, 5]
    if (any(a.dtype != np.uint8 for a in (data, labels)) or sorted(np.unique(labels)) != [0, *codes]
            or image.header.get_xyzt_units()[0] != "mm"):
        raise ValueError("Unexpected source type, units or label alphabet")
    shape = image.shape
    spacing = np.array(image.header.get_zooms(), dtype=float)
    case = {"id": identifier, "side": side.title(), "shape": list(shape), "spacingMm": spacing.tolist(),
            "affine": image.affine.tolist(), "sources": sources, "brickSize": BRICK, "bricks": [], "labels": []}
    for origin in itertools.product(*(range(0, n, BRICK) for n in shape)):
        slices = tuple(slice(start, start + BRICK) for start in origin)
        gray, label = data[slices], labels[slices]
        pairs = np.stack((gray.T, label.T), axis=-1)
        name = "{}-{}-{}-{}.gz".format(side, *origin)
        case["bricks"].append({**store(output, name, pairs.tobytes()), "start": origin, "size": gray.shape})
    for code in codes:
        cells = np.argwhere(labels == code)
        centre = cells.mean(axis=0)
        focus = cells[np.argmin(np.sum((cells - centre) ** 2, axis=1))]
        low = np.maximum(cells.min(axis=0) - 1, 0)
        high = np.minimum(cells.max(axis=0) + 2, shape)
        mask_roi = labels[tuple(slice(a, b) for a, b in zip(low, high))] == code
        vertices, triangles, _, _ = marching_cubes(mask_roi.astype(np.uint8), level=.5, gradient_direction="ascent",
                                                     allow_degenerate=False)
        vertices = ((vertices + low) * spacing).astype("<f4")
        triangles = triangles.astype("<u4")
        mesh = store(output, f"{side}-{code}-mesh.gz", vertices.tobytes() + triangles.tobytes())
        mesh.update(vertices=len(vertices), triangles=len(triangles))
        name, color = LABELS[code]
        case["labels"].append({"code": code, "name": side.title() + " " + name, "color": color,
                               "voxelCount": len(cells), "focus": focus.tolist(), "mesh": mesh})
    return case


def write_delivery(output):
    manifest = json.loads((output / "manifest.json").read_bytes())
    names = {"manifest.json", "index.html", "viewer.js", "viewer.css", "mesh-view.mjs",
             "native-volume.mjs", "source-selection.mjs", "ATTRIBUTION.md", "README.md"}
    for case in manifest["cases"]:
        names.update(row["file"] for row in case["bricks"])
        names.update(label["mesh"]["file"] for label in case["labels"])
    files = {}
    for name in sorted(names):
        raw = (output / name).read_bytes()
        files[name] = {"bytes": len(raw), "sha256": sha(raw)}
    (output / "delivery.json").write_text(json.dumps({"files": files}, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?")
    parser.add_argument("output", type=Path)
    parser.add_argument("--delivery-only", action="store_true", help="refresh file hashes after a reader edit")
    args = parser.parse_args()
    if args.delivery_only:
        write_delivery(args.output)
        return
    if args.input is None:
        parser.error("supply the source NIfTI directory or use --delivery-only")
    args.output.mkdir(parents=True, exist_ok=True)
    result = {
        "source": "https://www.cs.cit.tum.de/en/camp/publications/segthy-dataset/",
        "article": "https://doi.org/10.1371/journal.pone.0268550",
        "mirror": MIRROR,
        "license": "CC BY, version unspecified by publisher",
        "acquisition": "Freehand tracked ultrasound, volunteer 001, physician P1, acquisition 1 per side.",
        "registration": "Separate native sweep grids. The source files contain no inter-sweep registration.",
        "labelKey": "The US Readme documents manual thyroid and vessel annotations and assigns thyroid code 1. The pinned distribution identifies carotid codes 2/4 and jugular codes 3/5, consistent with the study's MRI class key. Sweep filenames identify side.",
        "surfaces": "0.5 interfaces of the manual labels, in positive native-index millimetres. No smoothing, decimation, padding beyond the scan, or component removal.",
        "cases": [package_case(args.input, args.output, side) for side in PINS],
    }
    (args.output / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    if (args.output / "index.html").exists():
        write_delivery(args.output)


if __name__ == "__main__":
    main()
