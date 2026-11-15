"""Partial native source reader preserves geometry and cannot claim complete clinical anatomy."""
import gzip,hashlib,json,math,struct
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'web/anatomy/hvsmr2-pat7';SOURCE=ROOT/'docs/hvsmr2-pat7-native-source-review'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_every_original_source_surface_is_preserved_in_reader_transport():
    manifest=json.loads((OUT/'manifest.json').read_text());review=json.loads((SOURCE/'native-source-review.json').read_text());export=json.loads((SOURCE/'reader-package-review.json').read_text());rows={r['id']:r for r in export['parts']}
    assert len(manifest['parts'])==len(review['classes'])==8 and manifest['total_triangles']==567000
    for c in review['classes']:
        id='hvsmr2-pat7-label'+str(c['label']);p=manifest['parts'][id];raw=(ROOT/'web'/p['file'].removeprefix('/app/')).read_bytes();decoded=gzip.decompress(raw);magic,n,k=struct.unpack('<4sII',decoded[:12])
        assert magic==b'BP3D' and n==c['vertices'] and k==c['triangles']*3 and len(decoded)==12+n*24+k*4
        assert sha(raw)==p['sha256']==rows[id]['sha256'] and sha(decoded)==p['decoded_sha256']
        original_pos=gzip.decompress((SOURCE/f'label{c["label"]}-positions.f64.gz').read_bytes());original_faces=gzip.decompress((SOURCE/f'label{c["label"]}-triangles.u32.gz').read_bytes())
        assert decoded[12+n*24:]==original_faces and p['source_triangles_sha256']==sha(original_faces)
        source=struct.iter_unpack('<d',original_pos);stored=struct.iter_unpack('<f',decoded[12:12+n*12]);error=max(abs(a[0]-b[0]) for a,b in zip(source,stored))
        assert error==rows[id]['maximum_position_conversion_error_source_mm'] and error<=1e-5
        assert rows[id]['faces_unchanged'] and rows[id]['zero_display_normals']==0
        for normal in struct.iter_unpack('<fff',decoded[12+n*12:12+n*24]):assert all(math.isfinite(x) for x in normal) and abs(sum(x*x for x in normal)-1)<2e-6
        assert p['clinical_fidelity']=='unverified'
    assert manifest['coordinate_system']['display_basis']=='native-ras-to-x-left-y-superior-z-anterior'
    assert not manifest['clinical_approval'] and not manifest['anatomical_approval'] and not manifest['complete_venous_geometry_verified']
def test_actual_reader_reference_uses_matching_mri_with_scope_notes():
    ref=detail(Curriculum(),resolve('ra.vascular-anomalies'))['radiology_reference'];entries=ref['source_anatomy_references'];entry=next(e for e in entries if e['atlas']=='hvsmr2-pat7')
    assert entry['family']=='cardiac-venous-source' and entry['initial_layer']=='blood_pool' and entry['initial_cropped'] is False
    assert entry['manifest_sha256']==sha((OUT/'manifest.json').read_bytes())
    assert 'not a normal whole-heart atlas' in entry['population_note'] and 'coronary sinus' in entry['population_note']
    image=entry['source_image'];assert sha((ROOT/'web'/image['src'].removeprefix('/app/')).read_bytes())==image['sha256']
    assert image['license_url']=='https://creativecommons.org/licenses/by/4.0/' and 'three planes do not establish' in image['caption'].lower()
    manifest=json.loads((OUT/'manifest.json').read_text());assert any('No shunt ratio' in n for n in manifest['viewer_notes'])
    assert 'generic aorta model does not contain the actual anomaly' in ref['walkthrough']['spatial_model']['reporting_aim']
def test_new_source_assets_have_rights_but_no_verified_leaf_bindings():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];selected=[a for a in assets if a['id'].startswith('hvsmr2-pat7-')]
    assert len(selected)==9 and sum(a['kind']=='model' for a in selected)==8
    for a in selected:
        assert not a['structure_ids'] and not a['requirement_coverage'] and a['anatomical_review']['status']=='pending'
        license=a['source']['license'];assert license['review_status']=='verified' and license['commercial_use'] and license['redistribution']
        assert sha((ROOT/license['evidence_path']).read_bytes())==license['evidence_sha256']

def test_client_accepts_the_registered_source_family():
    import shutil,subprocess
    import pytest
    node=shutil.which('node')
    if not node:pytest.skip('Node runtime unavailable for client contract check')
    script="const vm=require('vm'),fs=require('fs');const c={window:{}};vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),c);if(!c.window.PrimerDetailedAnatomy.supported('cardiac-venous-source'))process.exit(1);"
    subprocess.run([node,'-e',script,str(ROOT/'web/radiology-detailed-anatomy.js')],check=True,capture_output=True)
