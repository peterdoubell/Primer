"""What the hosted shell costs to load, and what compression must never touch.

Nothing the book served was compressed: about 2.8 MB of JavaScript and CSS
crossed the wire at full size on every first visit. primer/compression.py
compresses the book's own text in the Vercel entrypoint. These tests pin the
saving, and the three ways the first cut got it wrong: double-encoding the
build-time-gzipped meshes, compressing study volumes delivered deliberately
without an encoding, and putting a Content-Encoding on reviewed source files
whose contract is "the exact original bytes".
"""

import glob
import gzip
import hashlib
import json
import os
import sys
import tempfile

import pytest

# Before anything imports primer.server: it attaches to the live reader's
# record at import unless PRIMER_DB points elsewhere.
_TMP = tempfile.mkdtemp(prefix="primer-load-time-")
os.environ.setdefault("PRIMER_DB", os.path.join(_TMP, "reader.db"))
os.environ.setdefault("PRIMER_CONTENT_DIR", os.path.join(_TMP, "content"))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
WEB = os.path.join(ROOT, "web")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    import primer.server as srv
    from primer.compression import TextCompression
    with TestClient(TextCompression(srv.app)) as c:
        yield c


def _first(pattern):
    found = sorted(glob.glob(os.path.join(WEB, pattern), recursive=True))
    if not found:
        pytest.skip("nothing matching %s in this checkout" % pattern)
    return found[0], "/app/" + os.path.relpath(found[0], WEB).replace(os.sep, "/")


def test_the_hosted_entrypoint_is_the_compressed_book():
    import api.index as entry
    from primer.compression import TextCompression
    assert isinstance(entry.app, TextCompression), "Vercel serves the book uncompressed"


def test_the_reviewed_backend_is_left_byte_for_byte_as_reviewed():
    """Compression lives outside primer/server.py on purpose: a reviewed
    record pins that file's hash as the backend it verified."""
    pin = os.path.join(ROOT, "docs", "acute-stroke-reader-review-20261011",
                       "final-cache-CSP-API-supplement.json")
    if not os.path.exists(pin):
        pytest.skip("no pinned review in this checkout")
    with open(pin) as fh, open(os.path.join(ROOT, "primer", "server.py"), "rb") as src:
        from tools.qft_runtime_compatibility import historical_runtime_bytes
        raw = historical_runtime_bytes("primer/server.py", src.read())
        assert json.load(fh)["server_SHA256"] == hashlib.sha256(raw).hexdigest()


def test_the_largest_script_goes_out_compressed(client):
    r = client.get("/app/concept-models.js", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    assert r.headers.get("content-encoding") == "gzip", "the shell's scripts are sent uncompressed"
    raw = os.path.getsize(os.path.join(WEB, "concept-models.js"))
    # Large files stream, so there is no Content-Length; count what crossed the wire.
    assert r.num_bytes_downloaded < raw * 0.5, \
        "%d bytes sent for a %d-byte file" % (r.num_bytes_downloaded, raw)


def test_the_shell_and_the_curriculum_map_go_out_compressed(client):
    for path in ("/app/", "/api/curriculum"):
        r = client.get(path, headers={"Accept-Encoding": "gzip"})
        assert r.status_code == 200 and r.headers.get("content-encoding") == "gzip", path


def test_a_build_time_gzipped_mesh_is_not_encoded_twice(client):
    disk, url = _first("anatomy/*/*.bin.gz")
    r = client.get(url, headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    with open(disk, "rb") as fh:
        assert r.content == gzip.decompress(fh.read()), "the mesh was re-encoded"


def test_a_study_volume_is_delivered_exactly_as_written(client):
    """The series are .bin.gz sent WITHOUT a Content-Encoding, so the viewer
    can verify the original gzip container itself."""
    disk, url = _first("studies/*/*.bin.gz")
    r = client.get(url, headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200 and "content-encoding" not in r.headers
    with open(disk, "rb") as fh:
        assert r.content == fh.read()


def test_reviewed_source_files_carry_no_encoding(client):
    """Source PDFs and their siblings promise the exact original bytes."""
    from primer.compression import compressible
    for path in ("/app/reference-media/radiology-open/acute-stroke/x.pdf",
                 "/app/anatomy/soop-stroke-sub342/reference.html",
                 "/app/studies/tcga-dk-aa6p/mri-reference.html",
                 "/source-media/anything.js"):
        assert not compressible(path), path
    disk, url = _first("reference-media/**/*.pdf")
    r = client.get(url, headers={"Accept-Encoding": "gzip"})
    if r.status_code == 200:
        assert "content-encoding" not in r.headers


def test_images_are_not_recompressed(client):
    _disk, url = _first("illustrations/**/*.webp")
    r = client.get(url, headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200 and "content-encoding" not in r.headers


@pytest.mark.parametrize("name", ["physics-qft-lab.js", "physics-qft-lab.css", "spatial-qft.js"])
def test_current_qft_asset_transport_keeps_decoded_body_and_security_headers(client, name):
    expected = open(os.path.join(WEB, name), "rb").read()
    identity = client.get("/app/"+name, headers={"Accept-Encoding": "identity"})
    encoded = client.get("/app/"+name, headers={"Accept-Encoding": "gzip"})
    assert identity.status_code == encoded.status_code == 200
    assert identity.content == encoded.content == expected
    assert "content-encoding" not in identity.headers
    assert encoded.headers.get("content-encoding") == "gzip"
    for header in ["content-security-policy", "cache-control", "content-type"]:
        assert encoded.headers.get(header) == identity.headers.get(header)
    assert encoded.num_bytes_downloaded < len(expected)
