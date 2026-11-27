"""Original nine-code CT source, exact native transport and normal app delivery."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from primer.server import app
from tools.anatomy_sources.verify_medseg_liver_001 import verify
from tools.medseg_liver_compatibility import before_medseg_liver_bytes

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / 'web/anatomy/medseg-liver-001'
DOC = ROOT / 'docs/medseg-liver-001'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def test_every_native_sample_and_all_nine_source_surfaces_match_the_originals():
    actual = verify()
    saved = json.loads((DOC/'source-comparison.json').read_bytes())
    assert actual == saved
    assert actual['transport']['cellsCompared'] == 12320768
    assert actual['transport']['bricks'] == 512
    assert [r['segment'] for r in actual['labels']] == ['1','2','3','4a','4b','5','6','7','8']
    assert [r['sourceName'] for r in actual['labels']][3:5] == ['Segment 4A','Segment 4B']
    assert sum(r['mesh']['triangles'] for r in actual['labels']) == 341310
    assert all(r['focusVerified'] and r['mesh']['closedTwoFaceEdges'] for r in actual['labels'])


def test_delivery_inventory_preserves_original_niftis_and_publisher_palette():
    files = json.loads((DIR/'delivery.json').read_bytes())['files']
    assert set(files) == {p.name for p in DIR.iterdir() if p.is_file() and p.name != 'delivery.json'}
    for name, row in files.items():
        raw = (DIR/name).read_bytes()
        assert (len(raw), sha(raw)) == (row['bytes'],row['sha256'])
    manifest = json.loads((DIR/'manifest.json').read_bytes())
    assert sha((DIR/'manifest.json').read_bytes()) in (DIR/'viewer.js').read_text()
    assert manifest['originalCTDtype'] == manifest['originalLabelDtype'] == 'float32'
    assert manifest['encoding'] == 'int16-le+two-labels'
    assert manifest['shape'] == [512,512,47] and manifest['spacingMm'][2] == 5
    assert manifest['units'][0] == 'mm' and manifest['qformCode'] == manifest['sformCode'] == 1
    assert manifest['labels'][3]['color'] == [193,39,45]
    assert manifest['labels'][4]['color'] == [0,173,190]
    for row in manifest['originals']:
        assert sha((DIR/row['file']).read_bytes()) == row['sha256']


def test_named_owner_rights_retain_upstream_image_license_instead_of_claiming_cc0_ct():
    owner = json.loads((DOC/'publisher-metadata.json').read_bytes())
    assert owner['doi'] == '10.6084/m9.figshare.13643252.v2'
    assert owner['license']['name'] == 'CC0'
    assert {a['full_name'] for a in owner['authors']} == {'MedSeg','Håvard Bjørke Jenssen','Tomas Sakinis'}
    assert 'Segmentations done by MedSeg' in owner['description']
    assert 'Decathlon' in owner['description']
    manifest = json.loads((DIR/'manifest.json').read_bytes())
    assert manifest['imageLicense']['name'] == 'CC BY-SA 4.0'
    assert manifest['annotationLicense']['name'] == 'CC0 1.0'
    html = (DIR/'index.html').read_text()
    assert 'CT is not relicensed as CC0' in html
    assert all('id="'+anchor+'"' in html for anchor in ['ct','map','surface'])
    assert '5 mm' in html and 's0028' in html and 'acquisition phase' in html


def test_source_files_are_delivered_through_owned_app_paths_and_hosted_static_gzip(monkeypatch):
    auth=('medseg-fixture','fixture-only')
    monkeypatch.setenv('PRIMER_ACCESS_USERNAME',auth[0]);monkeypatch.setenv('PRIMER_ACCESS_PASSWORD',auth[1])
    prefix='/app/anatomy/medseg-liver-001/'
    with TestClient(app) as client:
        assert client.get(prefix+'index.html').status_code == 401
        response=client.get(prefix+'index.html',auth=auth)
        assert response.status_code == 200
        assert "frame-ancestors 'self';" in response.headers['content-security-policy']
        for file in ['original-ct.nii.gz','original-labels.nii.gz','segment-4a.mesh.gz','brick-0-0-0.gz']:
            response=client.get(prefix+file,auth=auth)
            assert response.status_code == 200
            assert sha(response.content) == sha((DIR/file).read_bytes())
        assert client.get(prefix+'unlisted.gz',auth=auth).status_code == 404
        monkeypatch.setenv('VERCEL','1')
        for file in ['original-ct.nii.gz','segment-4a.mesh.gz','brick-0-0-0.gz']:
            response=client.head(prefix+file,auth=auth,follow_redirects=False)
            assert response.status_code == 307
            assert response.headers['location'] == '/source-media/anatomy/medseg-liver-001/'+file
    config=json.loads((ROOT/'vercel.json').read_bytes())
    pattern='web/anatomy/medseg-liver-001/*.gz'
    assert pattern in config['builds'][0]['config']['excludeFiles']
    assert {'src':pattern,'use':'@vercel/static'} in config['builds']


def test_new_delivery_inverse_preserves_prior_torso_and_form_history():
    proof=json.loads((DOC/'runtime-inverse.json').read_bytes())
    for path,row in proof.items():
        current=(ROOT/path).read_bytes()
        assert sha(current) == row['after']
        prior=before_medseg_liver_bytes(path,current)
        assert sha(prior) == row['before']
        assert before_medseg_liver_bytes(path,prior) == prior
        assert before_medseg_liver_bytes(path,current+b'foreign') == current+b'foreign'
    from tools import ct_torso_compatibility as torso
    old=json.loads(torso.PROOF.read_bytes())
    for path in ['primer/server.py','vercel.json']:
        restored=torso.before_torso_bytes(path,(ROOT/path).read_bytes())
        assert sha(restored) == old[path]['before']
