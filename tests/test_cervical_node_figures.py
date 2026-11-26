"""Verify the original publications, panel roles, reporting entry and hosted image route."""
import hashlib

from fastapi.testclient import TestClient
from primer import cervical_node_figures as study
from primer.server import app


def test_cervical_and_inguinal_examples_remain_distinct_in_the_published_file():
    figures, bindings = study.catalog()
    normal = figures['regional-node-us-2026-fig4ab']
    detail = normal['source_context']['panel_details']
    assert {p: (r['site'], r['side']) for p, r in detail.items()} == {
        'a': ('cervical', None), 'b': ('inguinal', None)}
    inflammatory = figures['periauricular-node-us-2026-fig14']
    detail = inflammatory['source_context']['panel_details']
    assert [(p, r['site'], r['side'], r['display']) for p, r in detail.items()] == [
        ('a', 'periauricular', 'left', 'grayscale'), ('b', 'periauricular', 'left', 'Doppler'),
        ('c', 'periauricular', 'left', 'Doppler')]
    child = figures['paediatric-cervical-node-us-2025-fig3']
    assert [r['source_category'] for r in child['source_context']['panel_details'].values()] == [
        'reactive', 'suspicious', 'high suspicion']
    assert bindings['ra.paediatric-neck-masses'] == [child['id']]
    for row in figures.values():
        assert row['license_url'] == 'https://creativecommons.org/licenses/by/4.0/'
        original = (study.ROOT / 'web' / row['src'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(original).hexdigest() == row['sha256']
        assert row['clinical_approval'] is False and row['structure_coverage_granted'] is False
        assert row['source_context']['current_patient_registration'] is False


def test_node_figures_reach_each_matching_exam_with_full_size_bytes(monkeypatch):
    monkeypatch.delenv('VERCEL', raising=False)
    figures, bindings = study.catalog()
    with TestClient(app) as client:
        for exam, expected in bindings.items():
            detail = client.get('/api/radiology/modules/' + exam).json()['radiology_reference']
            cards = [r for r in detail['source_native_inspectors'] if r['id'] in figures]
            assert [r['id'] for r in cards] == expected
            for card in cards:
                image, = card['photographic_figures']
                assert image == figures[card['id']]
                assert hashlib.sha256(client.get(image['src']).content).hexdigest() == image['sha256']
                assert card['structure_ids'] == card['requirement_coverage'] == []
                assert card['current_patient_registration'] is False
                assert 'inline_label' not in card
            if exam == 'us.soft-tissue-neck':
                assert {'segthy-001', 'salivary-us-2025', 'zanatomy-salivary'} <= {
                    r['id'] for r in detail['source_native_inspectors']}
        auth = ('node-figure-fixture', 'fixture-only')
        monkeypatch.setenv('PRIMER_ACCESS_USERNAME', auth[0])
        monkeypatch.setenv('PRIMER_ACCESS_PASSWORD', auth[1])
        monkeypatch.setenv('VERCEL', '1')
        for path in study.by_url():
            assert client.head(path).status_code == 401
            response = client.head(path, auth=auth, follow_redirects=False)
            assert response.status_code == 307
            assert response.headers['location'] == path.replace('/app/', '/source-media/', 1)
        assert client.get('/app/reference-media/radiology-open/unlisted-node-image.png', auth=auth).status_code == 404
