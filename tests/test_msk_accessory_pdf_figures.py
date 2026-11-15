"""PDF preservation, licensing and extent checks for accessory-muscle sources."""
import copy
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image
from primer.radiology_catalog import _structure_atlases
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage, requirements_for

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/msk-accessory-pdf-source-review'


def test_all_pdf_renders_match_the_reviewed_source_records():
    records = json.loads((REVIEW / 'rendered-figure-records.json').read_text())
    acquired = {Path(r['path']).name: r for r in json.loads((REVIEW / 'acquisition.json').read_text())}
    images = {i['id']: i for i in _structure_atlases()['ra.mri-ankle']}
    assets = {a['id']: a for a in json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']}
    assert len(records) == 5
    for record in records:
        image, asset = images[record['asset_id']], assets[record['asset_id']]
        path = ROOT / record['runtime_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'] == image['sha256'] == asset['sha256']
        assert Image.open(path).size == (image['width'], image['height']) == (record['width'], record['height'])
        assert record['pdf_sha256'] == acquired[record['pdf']]['sha256']
        metadata = json.loads((REVIEW / record['pdf'].replace('.pdf', '.json')).read_text())
        assert parse_qs(urlparse(metadata['pdf_url']).query)['md5'][0] == acquired[record['pdf']]['md5']
        assert metadata['license_code'] == 'CC BY' and not metadata['is_manuscript'] and not metadata['is_retracted']
        assert 'NLM/PMC' in image['attribution'] and 'snapshot' in image['attribution']
        assert not asset['pixel_provenance']['source_stream_preserved']  # PNG is a PDF rendering, not raw JPEG bytes.
        assert asset['anatomical_review']['status'] == 'pending'


def test_fdal_cross_section_does_not_become_course_or_soleus_geometry():
    assets = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']
    asset = next(a for a in assets if a['id'] == 'open-ankle-fdal-batista-fig2')
    req = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    ankle = next(i for i in req['investigations'] if i['investigation_id'] == 'ra.mri-ankle')
    leaves = {r['id']: r for r in requirements_for(ankle)}
    target = 'ankle.flexor_digitorum_accessorius_longus_muscle.muscle_belly'
    assert asset['structure_ids'] == [target]
    assert not inspect_binding(asset, leaves[target])
    assert inspect_requirement_coverage(asset, leaves[target]) == ['requirement_coverage_partial']
    assert asset['source_context']['laterality'] == 'left'
    assert asset['source_context']['population']['age_years'] == 34
    assert asset['source_context']['sequence'] == 'not_reported'
    assert 'source_context_anatomical_variant_mismatch' in inspect_binding(asset, leaves['ankle.accessory_soleus_muscle.muscle_belly'])
    normal = copy.deepcopy(leaves[target])
    normal['context_requirements'].append({'depicted_state':'normal_anatomy'})
    assert 'source_context_depicted_state_mismatch' in inspect_binding(asset, normal)
    publisher = json.loads((REVIEW / 'fdal-crossref.json').read_text())['message']
    assert publisher['DOI'] == '10.1155/2015/823107'
    assert publisher['license'][0]['URL'] == 'http://creativecommons.org/licenses/by/3.0/'
    assert asset['source']['license']['name'] == 'CC BY 3.0'
