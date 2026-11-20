import collections
import hashlib
import json

import pytest

from tools import lesson_activities_compatibility as history
from tools.anatomy_sources import bind_models
from tools.anatomy_sources import bind_reader_models as tool
from tools.anatomy_sources.bind_body_reader_models import before_body_reader_model_records
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage

PATH = 'data/radiology/radiology-asset-evidence.json'


def records():
    review = json.loads(tool.REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(tool.EVIDENCE.read_text())['assets']}
    leaves, names, structures = tool.requirement_leaves()
    return review, assets, leaves, names


def test_every_record_quotes_its_meshs_own_label_and_passes_the_checker():
    review, assets, leaves, names = records()
    rows = review['accepted']
    assert len(rows) == 192 and len({row['asset_id'] for row in rows}) == 186 and len({row['structure_id'] for row in rows}) == 103
    assert 'not a radiologist review' in review['reviewer'] and '2026-11-19' in review['decision']
    for row in rows:
        asset = assets[row['asset_id']]
        assert asset['kind'] == 'model' and asset['name'] == row['quote'] and row['name'] == names[row['structure_id']]
        raw = (tool.ROOT / asset['local_path']).read_bytes()
        assert asset['local_path'] == 'web/anatomy/' + row['mesh'] and hashlib.sha256(raw).hexdigest() == asset['sha256']
        if 'faces_path' in asset['geometry']:
            assert hashlib.sha256((tool.ROOT / asset['geometry']['faces_path']).read_bytes()).hexdigest() == asset['geometry']['faces_sha256']
        coverage = asset['requirement_coverage'][row['structure_id']]
        assert coverage == {'extent': 'partial', 'basis': tool.basis(row, review)} and '“%s”' % row['quote'] in coverage['basis']
        assert set(row['investigations']) <= set(asset['investigation_ids']) and asset['anatomical_review']['status'] == 'pending'
        license = asset['source']['license']
        assert license['review_status'] == 'verified' and license['commercial_use'] and license['redistribution'] and license['attribution']
        assert hashlib.sha256((tool.ROOT / license['evidence_path']).read_bytes()).hexdigest() == license['evidence_sha256']
        assert (tool.ROOT / asset['visual_review']['evidence_path']).is_file() and asset['visual_review']['sha256'] == asset['sha256']
        for investigation in row['investigations']:
            requirement = leaves[row['structure_id']][investigation]
            assert inspect_binding(asset, requirement) == []
            assert inspect_requirement_coverage(asset, requirement) == ['requirement_coverage_partial']


def test_each_label_names_the_requirement_and_the_leaf_is_the_recorded_kind():
    review, _, leaves, names = records()
    rows = review['accepted']
    assert collections.Counter(row['evidence'] for row in rows) == {'own_word': 101, 'another_name': 53, 'kind_of': 38}
    assert collections.Counter(row['leaf_basis'] for row in rows) == {'named_part': 113, 'group_member': 63, 'body_part': 12, 'structure': 4}
    pairs = {'another_name': review['another_name_pairs'], 'kind_of': review['kind_of_pairs']}
    for row in rows:
        assert tool.evidence_fits(row, names[row['structure_id']], pairs)
    for kind in pairs:
        assert {'%s>%s' % (pair['label_word'], pair['requirement_word']) for pair in pairs[kind]} == set(review[kind + '_reasons'])
    row = next(row for row in rows if row['evidence'] == 'own_word')
    assert not tool.evidence_fits(dict(row, term='caudate'), names[row['structure_id']], pairs)
    row = next(row for row in rows if row['evidence'] == 'another_name')
    assert not tool.evidence_fits(row, names[row['structure_id']], {'another_name': [], 'kind_of': []})
    bound = {row['structure_id'] for row in rows}
    # Wholes are not bound to their parts: the caudate, the lateral ventricle, the corpus callosum, the pons and the hippocampus.
    for leaf in ('brain.right_caudate.head', 'brain.left_lateral_ventricle.frontal_horn', 'brain.corpus_callosum.genu',
                 'brain.brainstem.pons_basis', 'epilepsy.left.hippocampus.head', 'sella.right.optic_nerve.whole_obtained_course'):
        assert leaf not in bound
    # Parts are not bound to their wholes: no gyral part, amygdala nucleus or cerebellar lobule mesh is recorded.
    recorded = {row['mesh'] for row in rows}
    meshes = tool.inventory(review)
    for key, mesh in meshes.items():
        if any(text in mesh['label'] for text in ('part of', 'Amygdala Lateral', 'Cerebellum Lobule', 'Medial Segment')):
            assert key not in recorded and review['not_recorded'][key]
    # Vascular-territory masks are not bound: the stroke requirements ask for tissue extent without a generic territory mask.
    assert not any(row['atlas'] == 'schirmer' for row in rows)


def test_each_reader_is_shown_in_the_investigations_the_review_records():
    from primer.curriculum import Curriculum
    from primer.radiology_catalog import detail, resolve
    review = json.loads(tool.REVIEW.read_text())
    curriculum = Curriculum()
    investigations = sorted({investigation for reader in review['readers'].values() for investigation in reader['investigations']})
    for investigation in investigations:
        shown = {item.get('id') for item in detail(curriculum, resolve(investigation))['radiology_reference'].get('source_native_inspectors') or []}
        recorded = {reader['inspector'] for reader in review['readers'].values() if investigation in reader['investigations']}
        assert recorded <= shown, investigation
    # The epilepsy reader shows one group of the reporting classes; the server sends its mesh requests to the reporting reader.
    context = json.loads((tool.ANATOMY / review['readers']['spl-epilepsy-context']['manifest']).read_text())
    group = next(item for item in context['groups'] if item['id'] == context['defaultGroup'])
    assert len(group['codes']) == 18 and review['readers']['spl-epilepsy-context']['served_from'] == 'spl-nac-reporting'
    assert not (tool.ANATOMY / 'spl-epilepsy-context' / 'label-2.mesh.gz').exists()


def test_sides_agree_with_where_the_decoded_meshes_lie():
    review, assets, leaves, names = records()
    meshes = tool.inventory(review)
    cache = {}
    counts = collections.Counter()
    for row in review['accepted']:
        found = tool.mesh_side(row['mesh'], meshes, review, cache)
        geometry = assets[row['asset_id']]['geometry']
        assert geometry['share_of_vertices_right_of_source_midline'] == found['share_right']
        assert geometry['centroid_mm_right_of_source_midline'] == found['centroid_mm']
        assert row['mesh_side'] == found['located'] and found['located'] != 'contradicts_label'
        context = assets[row['asset_id']]['source_context']
        if row['side_basis'] in ('right', 'left'):
            assert context['laterality'] == row['side_basis'] == meshes[row['mesh']]['side']
            # The mirror mesh lies on the other side.
            assert (found['centroid_mm'] > found['mirror_centroid_mm']) == (row['side_basis'] == 'right')
        elif row['side_basis'] == 'bilateral':
            assert context['laterality'] == 'bilateral' and leaves[row['structure_id']][row['investigations'][0]]['laterality'] == 'bilateral'
        else:
            assert 'laterality' not in context
        counts[row['side_basis']] += 1
    assert counts == {'right': 86, 'left': 86, 'unsided': 14, 'both': 4, 'bilateral': 2}
    # A swapped pair of labels is caught: the right-labelled mesh would lie left of its mirror.
    key = next(row['mesh'] for row in review['accepted'] if row['quote'] == 'right putamen')
    swapped = dict(meshes, **{key: dict(meshes[key], side='left', label='left putamen')})
    assert tool.mesh_side(key, swapped, review, {})['located'] == 'contradicts_label'


def test_every_other_mesh_of_the_readers_is_listed_with_its_reason():
    review, assets, _, _ = records()
    meshes = tool.inventory(review)
    assert len(meshes) == 753
    recorded = {row['mesh'] for row in review['accepted']}
    assert recorded | set(review['not_recorded']) == set(meshes) and not recorded & set(review['not_recorded'])
    recorded_paths = {asset['local_path'] for asset in assets.values()}
    for key, reason in review['not_recorded'].items():
        assert reason and 'web/anatomy/' + key not in recorded_paths
    for key, mesh in meshes.items():
        if mesh['atlas'] == 'schirmer':
            assert 'territory' in review['not_recorded'][key]
        if mesh['label'] in ('Right Lobe Occipital', 'Left Lobe Occipital'):
            assert 'CSF' in review['not_recorded'][key]


def test_reader_model_records_have_an_exact_inverse_and_only_add_records():
    receipt = json.loads(tool.RECEIPT.read_text())
    raw = before_body_reader_model_records(tool.EVIDENCE.read_bytes())  # The body readers' meshes were recorded afterwards.
    assert second.sha(raw) == receipt['after_sha256'] and receipt['path'] == PATH
    before = tool.before_reader_model_records(raw)
    assert second.sha(before) == receipt['before_sha256']
    assert tool.before_reader_model_records(before) == before
    assert tool.before_reader_model_records(raw + b'\n') == raw + b'\n'
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    # The ledger before this pass is the ledger right after the stored-model pass.
    assert second.sha(before) == json.loads(bind_models.RECEIPT.read_text())['after_sha256']
    old_view, new_view = json.loads(before), json.loads(raw)
    assert {k: v for k, v in old_view.items() if k != 'assets'} == {k: v for k, v in new_view.items() if k != 'assets'}
    added = new_view['assets'][len(old_view['assets']):]
    assert new_view['assets'][:len(old_view['assets'])] == old_view['assets'] and len(added) == 186
    assert [item['id'] for item in added] == sorted(row['asset_id'] for row in {row['asset_id']: row for row in
                                                                              json.loads(tool.REVIEW.read_text())['accepted']}.values())
    # The history chain peels this pass first.
    assert history.before_activity_registry_bytes(PATH, raw) == history.before_activity_registry_bytes(PATH, before)


def test_the_tool_refuses_a_row_that_breaks_a_rule(tmp_path, monkeypatch):
    review = json.loads(tool.REVIEW.read_text())
    ledger, document = tmp_path / 'evidence.json', tmp_path / 'review.json'
    ledger.write_bytes(tool.before_reader_model_records(before_body_reader_model_records(tool.EVIDENCE.read_bytes())))
    monkeypatch.setattr(tool, 'EVIDENCE', ledger)
    monkeypatch.setattr(tool, 'REVIEW', document)
    document.write_text(json.dumps(review))
    made = tool.plan()
    assert len(made) == 186 and sum(len(item['structure_ids']) for item in made) == 192
    index = next(i for i, row in enumerate(review['accepted']) if row['quote'] == 'left precentral gyrus')
    row = review['accepted'][index]
    cases = {
        # The holiAtlas reader is not shown in the epilepsy investigation.
        'not in an investigation whose reader shows': dict(row, investigations=['ra.mri-epilepsy']),
        'not the mesh’s source label': dict(row, quote='left precentral gyrus and sulcus'),
        'does not name the requirement': dict(row, term='postcentral gyrus'),
        # A labelled left mesh cannot bind the right precentral gyrus.
        'Requirement leaf or its name is not recorded': dict(row, structure_id='brain.right_surface.precentral_gyrus'),
        'Side of the label, the mesh and the requirement disagree': dict(row, structure_id='brain.right_surface.precentral_gyrus',
                                                                         name='Right cortex and surface landmarks: Precentral gyrus'),
        'not the kind of leaf recorded': dict(row, leaf_basis='body_part'),
    }
    for problem, broken in cases.items():
        document.write_text(json.dumps(dict(review, accepted=review['accepted'][:index] + [broken] + review['accepted'][index + 1:])))
        with pytest.raises(ValueError, match=problem):
            tool.plan()
