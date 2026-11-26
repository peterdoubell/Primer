"""Emit a deterministic lossless runtime copy of the authored structured forms."""
import gzip
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/radiology/structured-reporting.json'
PACKED = SOURCE.with_suffix('.json.gz')


def encode(raw):
    output = io.BytesIO()
    with gzip.GzipFile(filename='', fileobj=output, mode='wb', compresslevel=9, mtime=0) as stream:
        stream.write(raw)
    return output.getvalue()


if __name__ == '__main__':
    raw = SOURCE.read_bytes()
    packed = encode(raw)
    assert gzip.decompress(packed) == raw
    PACKED.write_bytes(packed)
    print(f'{len(raw)} authored bytes -> {len(packed)} lossless runtime bytes')
