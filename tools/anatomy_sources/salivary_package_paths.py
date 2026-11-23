"""Confine salivary authoring I/O to the documented package in this checkout."""
from os.path import relpath
from pathlib import Path, PurePath


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "web/anatomy/zanatomy-salivary"
MESH_STEMS = (
    "parotid-gland", "submandibular-gland", "sublingual-gland", "parotid-duct",
    "submandibular-duct", "mylohyoid-muscle", "superficial-part-of-masseter", "deep-part-of-masseter",
)
MESH_FILES = tuple(side + "-" + stem + ".mesh.gz" for side in ("left", "right") for stem in MESH_STEMS) + (
    "mandible.mesh.gz", "hyoid-bone.mesh.gz",
)
PACKAGE_MEMBERS = MESH_FILES + (
    "index.html", "view.css", "controls.js", "planes.mjs", "LICENSE.txt", "surfaces.json", "source.json", "delivery.json",
)


def package_directory(requested):
    """Validate the CLI spelling, then return the trusted checkout path itself."""
    if PACKAGE_ROOT.resolve() != PACKAGE_ROOT:
        raise ValueError("Salivary package directory must not contain symbolic links")
    # Compare names without doing filesystem lookups on a user-supplied path.
    # The caller always receives the directory anchored to this checkout.
    if PurePath(requested) not in (PACKAGE_ROOT, PurePath(relpath(PACKAGE_ROOT))):
        raise ValueError("Use this checkout's web/anatomy/zanatomy-salivary directory; use an isolated checkout for scratch work")
    return PACKAGE_ROOT


def package_member(name):
    """Select a known filename, never construct an I/O path from manifest text."""
    if PACKAGE_ROOT.resolve() != PACKAGE_ROOT:
        raise ValueError("Salivary package directory must not contain symbolic links")
    for allowed in PACKAGE_MEMBERS:
        if name == allowed:
            path = PACKAGE_ROOT / allowed
            if path.is_symlink() or path.resolve() != path:
                raise ValueError("Salivary package members must not be symbolic links")
            return path
    raise ValueError("Unrecognised salivary package member")
