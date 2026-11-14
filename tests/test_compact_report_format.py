"""Compact formatting preserves explicit selections and versioned report text."""
import gzip
import json
from pathlib import Path

from primer.descriptor_reporting import render_descriptors

ROOT = Path(__file__).resolve().parents[1] / 'data/radiology'
PREVIOUS = '2c97a03290803ef7ce536452c0a1852351514aec9d1deae6c24dda900c154185'
KNEE = 'ra.mri-knee'


def knee_form(path):
    with gzip.open(path, 'rt') as source:
        catalog = json.load(source)
    return next(form for form in catalog['forms'].values()
                if any(exam['id'] == KNEE for exam in form['investigations']))


def test_knee_compacts_only_complete_normal_groups_and_preserves_previous_output():
    current = knee_form(ROOT / 'descriptor-reporting.json.gz')
    old = knee_form(ROOT / 'descriptor-history' / (PREVIOUS + '.json.gz'))
    prefix = 'anatomy-medial-meniscus-'
    state = {'investigation_id': KNEE, 'selections': {
        prefix + segment: {'normal': True}
        for segment in ('anterior-horn', 'body', 'posterior-horn')
    }}
    compact = render_descriptors(current, state)
    assert compact['valid']
    assert compact['sections'][0]['text'] == (
        '• No tear of the medial meniscal anterior horn, body or posterior horn.'
    )
    original = render_descriptors(old, state)
    assert original['valid'] and original['text'].startswith('MEDIAL COMPARTMENT\n')
    assert len(original['sections'][0]['text'].splitlines()) == 3
    assert len(compact['sections'][0]['text'].split()) < len(original['sections'][0]['text'].split())

    row = prefix + 'body'
    finding = KNEE + ':medial-meniscus-body:bucket-handle'
    state['selections'][row] = {'findings': {finding: {}}}
    mixed = render_descriptors(current, state)
    assert mixed['valid'] and 'Bucket-handle tear involving the medial meniscus body.' in mixed['text']
    assert 'intercondylar notch' not in mixed['text']
    assert 'No tear of the medial meniscal anterior horn, body or posterior horn' not in mixed['text']
    assert 'The medial meniscus posterior horn has no tear.' in mixed['text']

    state['selections'][row]['findings'][KNEE + ':medial-meniscus-body:fragment'] = {'slot-1': 'inferior gutter'}
    located = render_descriptors(current, state)
    assert located['valid'] and 'inferior gutter' in located['text']
