"""Split the published diaphragm figure into its lettered panels and bind each to a side.

The peer-reviewed caption of Figure 29 in Safai Zadeh et al. (Diagnostics 2023;13:767,
CC BY 4.0) states the side of every panel: "Visualization of the right-sided (A) and
left-sided diaphragm (B) with the lateral intercostal view and of the right-sided
diaphragm with the subcostal view (C)." The whole figure has no single side, so it
cannot satisfy a sided requirement. Each lettered panel can.

Panels are lossless crops of the stored figure along its white gutters. A binding
here is a source-reviewed, partial depiction. It is not a clinical approval.
"""
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'data/radiology/radiology-asset-evidence.json'
SOURCE_ID = 'open-thoracic-us-pmc9956010-fig29'
RECEIPT = ROOT / 'docs/thoracic-ultrasound-side-panels-20261116/inverse.json'
XML = ROOT / 'docs/thoracic-ultrasound-source-review-20261013/evidence/PMC9956010.xml.gz'
CAPTION = ('Visualization of the right-sided (A) and left-sided diaphragm (B) with the lateral intercostal view '
           'and of the right-sided diaphragm with the subcostal view (C).')
LIST_END = b'\n  ],\n  "reference_rights_assets": ['
PANELS = (
    ('a', (2, 3, 228, 212), 'right', 'Right hemidiaphragm, lateral intercostal view'),
    ('b', (232, 3, 485, 212), 'left', 'Left hemidiaphragm, lateral intercostal view'),
    ('c', (488, 3, 736, 212), 'right', 'Right hemidiaphragm, subcostal view'),
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def records():
    article = re.sub(r'<[^>]+>', '', gzip.decompress(XML.read_bytes()).decode())
    if CAPTION not in ' '.join(article.split()):
        raise ValueError('The stored article no longer carries the reviewed caption')
    parent = next(item for item in json.loads(EVIDENCE.read_text())['assets'] if item['id'] == SOURCE_ID)
    figure = ROOT / parent['local_path']
    if sha(figure.read_bytes()) != parent['sha256']:
        raise ValueError('The stored figure changed')
    image = Image.open(figure).convert('RGB')
    out = []
    for letter, box, side, name in PANELS:
        path = figure.with_name('thoracic-us-diagnostics-13-00767-g029-panel-%s.png' % letter)
        panel = image.crop(box)
        if not path.is_file():
            panel.save(path, optimize=True)
        if Image.open(path).convert('RGB').tobytes() != panel.tobytes():
            raise ValueError('Stored panel differs from the crop: ' + path.name)
        digest = sha(path.read_bytes())
        requirement = 'thoracic_ultrasound.%s_diaphragm' % side
        source = json.loads(json.dumps(parent['source']))
        source['panel'] = letter.upper()
        source['caption'] = CAPTION
        source['license']['attribution'] += ' Adaptation: panel %s cropped from the figure; no resampling.' % letter.upper()
        out.append({
            'id': '%s-panel-%s' % (SOURCE_ID, letter), 'kind': 'clinical_image', 'name': name,
            'local_path': str(path.relative_to(ROOT)), 'sha256': digest, 'modality': 'Ultrasound',
            'investigation_ids': ['ra.thoracic-ultrasound'], 'structure_ids': [requirement],
            'requirement_coverage': {requirement: {
                'extent': 'partial',
                'basis': ('One published still of part of the hemidiaphragm through one acoustic window. The side is '
                          'stated for this panel in the peer-reviewed caption. The full extent is not demonstrated.')}},
            'source_context': {**parent['source_context'], 'laterality': side, 'depicted_state': 'normal_anatomy_as_captioned'},
            'source': source,
            'pixel_provenance': {'source_pixels_changed': False, 'derived_from_asset': SOURCE_ID,
                                 'derived_from_sha256': parent['sha256'],
                                 'adaptation': 'Lossless crop of one lettered panel at pixel box %s' % (list(box),),
                                 'decoded_pixel_sha256': sha(panel.tobytes()),
                                 'highest_resolution_acquired_master_verified': False},
            'fidelity': 'source_reviewed_not_clinically_approved',
            'anatomical_review': {'status': 'pending',
                                  'reason': 'One modest-resolution still per panel; no radiologist has reviewed the binding.'},
            'visual_review': {'status': 'source_checked', 'reviewer': 'Claude stored figure, panel and caption comparison',
                              'reviewed_at': '2026-11-16', 'sha256': digest,
                              'evidence_path': 'docs/thoracic-ultrasound-side-panels-20261116/README.md'},
        })
    return out


def block(items):
    text = ''.join(',\n' + '\n'.join('    ' + line for line in json.dumps(item, indent=2, ensure_ascii=False).splitlines())
                   for item in items)
    return text.encode()


def insert():
    raw = EVIDENCE.read_bytes()
    if raw.count(LIST_END) != 1 or b'"' + SOURCE_ID.encode() + b'-panel-a"' in raw:
        raise ValueError('Evidence file is not in the expected pre-panel state')
    added = block(records())
    start = raw.index(LIST_END)
    after = raw[:start] + added + raw[start:]
    json.loads(after)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps({
        'path': 'data/radiology/radiology-asset-evidence.json', 'before_sha256': sha(raw), 'after_sha256': sha(after),
        'removed_range': [start, start + len(added)], 'removed_sha256': sha(added),
        'clinical_approval': False, 'extends_historical_approval': False}, indent=2) + '\n')
    EVIDENCE.write_bytes(after)


def before_side_panels(raw):
    """Exact earlier bytes of the evidence file; any other state is returned unchanged."""
    receipt = json.loads(RECEIPT.read_text())
    if sha(raw) != receipt['after_sha256']:
        return raw
    start, end = receipt['removed_range']
    if sha(raw[start:end]) != receipt['removed_sha256']:
        raise ValueError('Side-panel evidence span changed')
    restored = raw[:start] + raw[end:]
    if sha(restored) != receipt['before_sha256']:
        raise ValueError('Side-panel inverse changed unrelated bytes')
    return restored


if __name__ == '__main__':
    insert()
    print('added', [item['id'] for item in records()])
