"""Re-decode every original and browser cine frame against the retained SHA-256 proof.

Requires ffmpeg. Verifies decoded YUV sample identity, not RGB colorimetry,
acquisition timing, anatomical correspondence or a clinical interpretation.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def decoded_hashes(path):
    result = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:v:0',
         '-fps_mode', 'passthrough', '-f', 'framehash', '-hash', 'sha256', '-'],
        check=True, capture_output=True, text=True, timeout=60,
    )
    return [line.split(',')[-1].strip() for line in result.stdout.splitlines()
            if line and not line.startswith('#')]


def main():
    data = ROOT / 'data/radiology'
    proof = json.loads((data / 'thoracic-ultrasound-motion-proof.json').read_text())
    rows = json.loads((data / 'source-motion-references.json').read_text())['ra.thoracic-ultrasound']
    count = 0
    for row in rows:
        entry = proof['clips'][row['id']]
        actual = []
        for path_key, hash_key, frame_key in [
            ('original_src', 'original_sha256', 'original_decoded_YUV_frame_sha256'),
            ('src', 'sha256', 'transport_decoded_YUV_frame_sha256'),
        ]:
            path = ROOT / 'web' / row[path_key].removeprefix('/app/')
            if hashlib.sha256(path.read_bytes()).hexdigest() != row[hash_key]:
                raise ValueError('Container changed: ' + path.name)
            hashes = decoded_hashes(path)
            if hashes != entry[frame_key] or len(hashes) != row['frames']:
                raise ValueError('Decoded frame proof differs: ' + path.name)
            actual.append(hashes)
        if actual[0] != actual[1]:
            raise ValueError('Source and transport decoded samples differ: ' + row['id'])
        count += row['frames']
    print(f'{len(rows)} clips; {count} original/transport decoded YUV frame pairs verified')


if __name__ == '__main__':
    main()
