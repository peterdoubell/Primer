import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INV='ra.ultrasound-thyroid';PREFIX='open-thyroid-pmc8864691-fig'
def test_every_reviewed_source_figure_is_integrated_without_native_or_anatomy_claims():
    rows=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV]
    rows=[x for x in rows if x['id'].startswith(PREFIX)];assert len(rows)==21
    displays=json.loads((ROOT/'docs/thyroid-pictorial-source-review/PDF-display-review.json').read_text())['figures']
    ledger=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    from primer.radiology_catalog import _validate_source_panel_roles
    for row,display in zip(rows,displays):
        assert row['figure_number']==display['figure_number']
        assert hashlib.sha256((ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes()).hexdigest()==row['sha256']==display['display_sha256']
        assert (row['width'],row['height'])==tuple(display['dimensions'])
        assert row['license']=='CC BY 4.0' and row['source_caption_full']
        assert not row['source_context']['different_figures_assumed_same_patient']
        _validate_source_panel_roles(row)
        asset=next(a for a in ledger if a['id']==row['id'])
        assert asset['pixel_provenance']['source_pixels_changed'] and 'colour/display rendering' in asset['pixel_provenance']['change_reason']
        assert asset['anatomical_review']['status']=='pending' and not asset['structure_ids'] and not asset['requirement_coverage']
    assert rows[10]['panel_identifier_scheme']=='grid_unlettered'
    assert not rows[10]['source_context']['source_panels_independently_registered']
    assert 'hidden physical material' in rows[16]['limits']
def test_published_examples_are_linked_by_feature_without_normal_or_management_defaults():
    node=json.loads((ROOT/'data/radiology/reporting-steps/head-neck.json').read_text())['investigations'][INV]
    assert node['start']['images']==[] and not node['start']['module_illustrations']
    assert all(s['normal']=={} for s in node['steps'])
    assert [x for x in node['steps'][2]['images'] if x.startswith(PREFIX)]==[PREFIX+str(n) for n in range(1,22)]
    assert node['steps'][3]['images']==[PREFIX+'12',PREFIX+'20']
    assert not node['steps'][4]['images']
