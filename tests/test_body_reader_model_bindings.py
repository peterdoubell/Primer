import collections
import hashlib
import json
import re

import pytest

from tools import lesson_activities_compatibility as history
from tools.anatomy_sources import bind_body_reader_models as tool
from tools.anatomy_sources import bind_reader_models as brain
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage

PATH = 'data/radiology/radiology-asset-evidence.json'


def records():
    review = json.loads(tool.REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(tool.EVIDENCE.read_text())['assets']}
    leaves, names, _ = tool.requirement_leaves()
    return review, assets, leaves, names


def test_every_record_quotes_its_meshs_own_label_and_passes_the_checker():
    from tools.anatomy_sources.structure_display_names import display_structure_name

    review, assets, leaves, names = records()
    rows = review['accepted']
    assert len(rows) == 212 and len({row['asset_id'] for row in rows}) == 123 and len({row['structure_id'] for row in rows}) == 138
    assert 'not a radiologist review' in review['reviewer'] and '2026-11-19' in review['decision']
    for row in rows:
        asset = assets[row['asset_id']]
        requirement = next(iter(leaves[row['structure_id']].values()))
        assert asset['kind'] == 'model' and asset['name'] == row['quote']
        assert display_structure_name(row['name'], requirement['laterality']) == names[row['structure_id']]
        raw = (tool.ROOT / asset['local_path']).read_bytes()
        assert asset['local_path'] == 'web/anatomy/' + row['mesh'] and hashlib.sha256(raw).hexdigest() == asset['sha256']
        coverage = asset['requirement_coverage'][row['structure_id']]
        assert coverage == {'extent': 'partial', 'basis': tool.basis(row, review)} and '“%s”' % row['quote'] in coverage['basis']
        assert set(row['investigations']) <= set(asset['investigation_ids']) and asset['anatomical_review']['status'] == 'pending'
        license = asset['source']['license']
        assert license['review_status'] == 'verified' and license['commercial_use'] and license['redistribution'] and license['attribution']
        assert hashlib.sha256((tool.ROOT / license['evidence_path']).read_bytes()).hexdigest() == license['evidence_sha256']
        assert (tool.ROOT / asset['visual_review']['evidence_path']).is_file() and asset['visual_review']['sha256'] == asset['sha256']
        # A reader review checked the mesh against its source, or no review did and the record says so.
        review_of_mesh = asset['visual_review']
        assert review_of_mesh['status'] == ('pending' if row['atlas'] in ('bodyparts3d', 'colonvessels') else 'source_checked')
        assert ('reason' in review_of_mesh) == (review_of_mesh['status'] == 'pending')
        for investigation in row['investigations']:
            requirement = leaves[row['structure_id']][investigation]
            assert inspect_binding(asset, requirement) == []
            assert inspect_requirement_coverage(asset, requirement) == ['requirement_coverage_partial']


def test_each_label_names_the_requirement_and_the_leaf_is_the_recorded_kind():
    review, _, _, names = records()
    rows = review['accepted']
    assert collections.Counter(row['evidence'] for row in rows) == {'own_word': 84, 'another_name': 68, 'kind_of': 60}
    assert collections.Counter(row['leaf_basis'] for row in rows) == {'body_part': 92, 'group_member': 57, 'named_part': 52, 'structure': 11}
    pairs = {'another_name': review['another_name_pairs'], 'kind_of': review['kind_of_pairs']}
    for row in rows:
        assert tool.evidence_fits(row, names[row['structure_id']], pairs)
    assert len(pairs['another_name']) == 40 and len(pairs['kind_of']) == 23
    for kind in pairs:
        assert {'%s>%s' % (pair['label_word'], pair['requirement_word']) for pair in pairs[kind]} == set(review[kind + '_reasons'])
        # Every listed pair is used by a binding.
        assert all(any(row.get(kind) == pair for row in rows) for pair in pairs[kind])
    row = next(row for row in rows if row['evidence'] == 'own_word')
    assert not tool.evidence_fits(dict(row, term='duodenum'), names[row['structure_id']], pairs)
    row = next(row for row in rows if row['evidence'] == 'another_name')
    assert not tool.evidence_fits(row, names[row['structure_id']], {'another_name': [], 'kind_of': []})
    # A listed name must match whole words: hepatovenous segment II does not name segment III, nor source segment 2 segment 23.
    row = next(row for row in rows if row['quote'] == 'hepatovenous segment ii')
    assert not tool.evidence_fits(dict(row, quote='hepatovenous segment iii'), names[row['structure_id']], pairs)
    assert tool.label_word_in('Source segment 2', 'source segment 2') and not tool.label_word_in('Source segment 23', 'source segment 2')
    recorded = {row['mesh'] for row in rows}
    # Wholes are not bound to their parts: segment IV (IVa and IVb are required), the venous systems, the union of every vessel,
    # the wall of both ventricles, and the HyperPIC venous wall.
    for key in ('bodyparts3d/FJ2820.bin', 'liver-regions-mri/region-4.mesh.gz', 'hva-ct-318/318-portal.mesh.gz', 'hva-ct-318/318-hepatic.mesh.gz',
                'colonvessels-pat012/arteries-layer-0-value-1.mesh.gz', 'colonvessels-pat012/veins-layer-0-value-1.mesh.gz', 'bodyparts3d/FJ2428.bin',
                'bp3d-cardiac-4.3/transport/FJ2428.bin.gz', 'hyperpic-venous/hpT2/boundary-1.mesh.gz'):
        assert key not in recorded and 'whole' in review['not_recorded'][key]
    # A part is not bound to its whole: one head of a papillary muscle.
    assert 'part is not bound' in review['not_recorded']['bp3d-cardiac-4.3/transport/FJ2418.bin.gz']


def function_body(source, name):
    start = source.index('function %s(' % name)
    return source[start:source.index('\nfunction ', start + 1)]


def linked_segments(text):
    """The ColonVessels segments a block of the app links, as 'phase layer:value'."""
    return {'%s %s' % found for found in re.findall(r'colonvessels-pat012/(arterial|venous)/index.html\?segment=(\d+:\d+)', text)}


def test_each_reader_is_shown_in_the_investigations_the_review_records():
    from primer.curriculum import Curriculum
    from primer.radiology_catalog import catalogue, detail
    review = json.loads(tool.REVIEW.read_text())
    readers = review['readers']
    curriculum = Curriculum()
    from tools.pulmonary_lobe_runtime_compatibility import before_pulmonary_lobe_reference_fields
    # Recover this review's original scope; the added nodule-reader entry has its own source-role proof.
    references = {
        item['id']: before_pulmonary_lobe_reference_fields(
            item['id'], detail(curriculum, item)['radiology_reference'])
        for item in catalogue()['investigations']
    }
    # Readers opened from the catalog's source inspectors or source anatomy references.
    for name, reader in readers.items():
        if 'inspector' in reader:
            shown = {identifier for identifier, ref in references.items()
                     if reader['inspector'] in {item.get('id') for item in ref.get('source_native_inspectors') or []}}
            assert shown == set(reader['investigations']), name
        if 'reference' in reader:
            shown = {identifier for identifier, ref in references.items()
                     if reader['reference'] in {item.get('id') for item in ref.get('source_anatomy_references') or []}}
            assert shown == set(reader['investigations']), name
    # The BodyParts3D regions: the spatial-model family names the region when no source anatomy reference replaces it.
    spec = readers['bodyparts3d']
    aliases = re.search(r'const ALIASES = \{(.*?)\};', (tool.ROOT / 'web/radiology-detailed-anatomy.js').read_text(), re.S).group(1)
    assert {key: value for key, value in re.findall(r'(\w+): "(\w+)"', aliases) if key in spec['aliases']} == spec['aliases']
    shown = collections.defaultdict(set)
    for identifier, ref in references.items():
        own = ref.get('source_anatomy_references') or []
        family = (ref.get('spatial_model') or {}).get('family')
        region = spec['aliases'].get(family, family)
        if region in spec['regions'] and not own:
            shown[region].add(identifier)
        for item in own:
            if item.get('atlas') == 'bodyparts3d':
                shown[spec['aliases'].get(item.get('family'), item.get('family'))].add(identifier)
    for region, investigations in spec['regions'].items():
        assert shown[region] == set(investigations), region
    # Readers that the app links from investigation pages.
    app = (tool.ROOT / 'web/app.js').read_text()
    for name, function in (('bp3d-biliary-4.3', 'renderBiliaryAtlasStudy'), ('bp3d-dural-4.3', 'renderDuralVenousAtlas'),
                           ('hyperpic-venous', 'renderDuralVenousAtlas'), ('liver-regions-mri', 'renderLiverRegionStudy')):
        body = function_body(app, function)
        assert '/app/anatomy/%s/' % name in body and all("'%s'" % investigation in body for investigation in readers[name]['investigations'])
    liver = function_body(app, 'renderLiverRegionStudy')
    assert "'ra.liver-masses', 'ra.liver-lirads'" in liver and 'liverReportingStudies.tumour' in liver and 'liverReportingStudies.veins' in liver
    assert "slug: 'phlf-center2-24'" in app and "slug: 'hva-ct-318'" in app
    segments = readers['colonvessels-pat012']['segments']
    for investigation in ('ra.liver-masses', 'ra.liver-lirads'):
        assert linked_segments(liver) == set(segments[investigation])
    vessels = function_body(app, 'renderAbdominalVesselStudies')
    for group, investigation in (('renal', 'ra.solid-renal-masses'), ('pancreatic', 'ra.ct-pancreatic-cancer')):
        block = vessels[vessels.index('"%s": [' % group):]
        block = block[:block.index(']')]
        assert linked_segments(block) == set(segments[investigation])
        assert "'%s'" % investigation in vessels
    assert "['ra.ct-abdominal-trauma', 'ra.ct-bowel-ischaemia'].includes(nodeId)" in vessels
    assert segments['ra.ct-abdominal-trauma'] == segments['ra.ct-bowel-ischaemia'] == 'all'
    assert re.search(r"modules: \['ra.mri-cervical-cancer'\],\s*title: '[^']*',\s*href: '/app/anatomy/kcl-cervix/055t/index.html'", app)


def test_frames_follow_the_sources_own_anatomy():
    review, _, _, _ = records()
    meshes = tool.inventory(review)
    cache = {}
    offset = lambda key: tool.measure(key, meshes, review, cache)['centroid_mm']  # noqa: E731
    # BodyParts3D: the liver's right lobe lies right of the midline, and the ventricular wall and the circumflex artery left of it.
    for code in ('FJ2821', 'FJ2822', 'FJ2823', 'FJ2824', 'FJ2817'):
        assert offset('bodyparts3d/%s.bin' % code) > 40
    assert offset('bodyparts3d/FJ2428.bin') < -25 and offset('bodyparts3d/FMA3895.bin') < -50
    # The BodyParts3D 4.3 readers use the same coordinates as the 4.0 atlas.
    for old, new in (('bodyparts3d/FJ2817.bin', 'bp3d-biliary-4.3/FJ2817.mesh.gz'), ('bodyparts3d/FJ2438.bin', 'bp3d-cardiac-4.3/transport/FJ2438.bin.gz')):
        assert tool.positions(old, meshes[old])[0] == tool.positions(new, meshes[new])[0]
    # ColonVessels: the splenic vessels lie on the body's left and the portal vein on its right.
    assert offset('colonvessels-pat012/veins-layer-3-value-2.mesh.gz') < -40 and offset('colonvessels-pat012/arteries-layer-2-value-3.mesh.gz') < -50
    assert offset('colonvessels-pat012/veins-layer-2-value-7.mesh.gz') > 40
    # HRA female bladder: every region has exactly the coordinates of the same region in the HRA united female body.
    for name, node in (('ureteral_orifice_r', 'n0712-p0-vh_f_ureteral_orifice_r'), ('trigone_of_urinary_bladder', 'n0710-p0-vh_f_trigone_of_urinary_bladder')):
        key = 'hra-bladder-female-v1.1/hra-bladder-female-v1.1-vh_f_%s.bin.gz' % name
        united = 'hra-female-pelvis-v1.10/hra-female-pelvis-v1.10-%s.bin.gz' % node
        assert tool.positions(key, meshes[key])[0] == tool.positions(united, {'format': 'bp3d'})[0]


def test_sides_agree_with_where_the_decoded_meshes_lie():
    review, assets, leaves, _ = records()
    meshes = tool.inventory(review)
    cache = {}
    counts = collections.Counter()
    for row in review['accepted']:
        found = tool.mesh_side(row['mesh'], meshes, review, cache)
        asset = assets[row['asset_id']]
        geometry, context = asset['geometry'], asset['source_context']
        assert row['mesh_side'] == found['located'] and found['located'] != 'contradicts_label'
        if 'share_right' in found:
            reader = review['readers'][tool.reader_of(row['mesh'], review)]
            assert reader['frame'] == geometry['source_frame']
            assert geometry['source_frame_axes_basis'] == review['frames'][reader['frame']]['axes_basis']
            assert geometry['share_of_vertices_right_of_source_midline'] == found['share_right']
            assert geometry['centroid_mm_right_of_source_midline'] == found['centroid_mm']
        if row['side_basis'] in ('right', 'left'):
            assert context['laterality'] == row['side_basis'] == meshes[row['mesh']]['side']
            assert (found['share_right'] > 0.5) == (row['side_basis'] == 'right')
        elif row['side_basis'] in ('organ_right', 'organ_left'):
            side = row['side_basis'][len('organ_'):]
            assert found['partner_kind'] == 'organ_half' and meshes[row['mesh']]['side'] == side
            assert (found['centroid_mm'] > found['partner_centroid_mm']) == (side == 'right')
            sided = any(leaves[other['structure_id']][investigation]['laterality'] in ('left', 'right')
                        for other in review['accepted'] if other['mesh'] == row['mesh'] for investigation in other['investigations'])
            assert context.get('laterality') == (side if sided else None)
        else:
            assert 'laterality' not in context
        counts[row['side_basis']] += 1
    assert counts == {'unsided': 99, 'organ_left': 45, 'organ_right': 37, 'right': 20, 'left': 9, 'both': 2}
    # The right coronary trunk lies mostly left of the body midline, so its label's side names the heart's right, checked against the left trunk.
    rca = tool.mesh_side('bodyparts3d/FJ2723.bin', meshes, review, cache)
    assert rca['share_right'] < 0.5 and rca['located'] == 'right' and rca['partner_kind'] == 'organ_half'
    # Swapped labels are caught, for a body side and for an organ half.
    for key, label in (('bodyparts3d/FJ3147.bin', 'left kidney'), ('bodyparts3d/FJ2416.bin', 'left hepatic vein')):
        swapped = dict(meshes, **{key: dict(meshes[key], side='left', label=label)})
        partner = review['partners'][key]['partner']
        swapped[partner] = dict(meshes[partner], side='right')
        assert tool.mesh_side(key, swapped, review, {})['located'] == 'contradicts_label'


def test_every_other_mesh_of_the_readers_is_listed_with_its_reason():
    review, assets, _, _ = records()
    meshes = tool.inventory(review)
    assert len(meshes) == 263 and len(review['readers']) == 17
    recorded = {row['mesh'] for row in review['accepted']}
    assert recorded | set(review['not_recorded']) == set(meshes) and not recorded & set(review['not_recorded'])
    recorded_paths = {asset['local_path'] for asset in assets.values()}
    for key, reason in review['not_recorded'].items():
        assert reason and 'web/anatomy/' + key not in recorded_paths
    for key, mesh in meshes.items():
        reason = review['not_recorded'].get(key, '')
        if mesh['reader'] == 'hyperpic-venous' and key not in recorded:
            assert 'cut plane' in reason or 'wall of the whole' in reason
        if mesh['reader'] == 'kcl-cervix':
            assert 'pregnancy' in reason
        if mesh['reader'] == 'totalseg-v1-s0028-cardiac':
            assert 'context' in reason
        if mesh['reader'] == 'lynos-pat9' and mesh['label'].startswith('Annotated node'):
            assert 'lymph node' in reason
        if 'fundus of urinary bladder' == mesh['label']:
            assert 'dome' in reason and 'base' in reason
    assert set(review['readers_not_in_scope']) >= {'kidney-adrenal-s0028', 'cptac-renal-contours', 'venat', 'illinois-uterus'}


def test_lumens_populations_and_the_source_reviews_limits():
    review, assets, leaves, _ = records()
    rows = review['accepted']
    for row in rows:
        if any(word in tool.words(row['name'].split(': ', 1)[-1]) for word in tool.LUMEN_WORDS):
            assert row['atlas'] in review['lumen_sources']
        # No bound requirement asks for an example of pathology.
        for investigation in row['investigations']:
            assert all(target.get('purpose') != 'pathology_example' for target in tool.context_targets(leaves[row['structure_id']][investigation]))
    bound = {investigation for row in rows for investigation in row['investigations']}
    # Adult sources are not bound in paediatric or neonatal anatomy, nor the pregnancy cervix atlases in cervical cancer staging.
    assert set(review['population_limits']) == {'ra.paediatric-renal-tumours', 'ra.ultrasound-neonatal-brain'}
    assert not bound & (set(review['population_limits']) | {'ra.mri-cervical-cancer'})
    # Sources excluded as a whole have no record: the cardiac CT labels stay context, as their source review says.
    assert set(review['unbound_sources']) == {'kcl-cervix', 'hyperpic', 'totalsegmentator', 'hva-ct'}
    assert not {row['atlas'] for row in rows} & set(review['unbound_sources'])
    # Each record states only what its source states about the people it shows.
    assert assets['phlf-center2-24-regions-6']['source_context']['depicted_state'] == 'source_patient_case_with_liver_tumour'
    assert 'population' not in assets['lynos-pat9-azygos']['source_context']
    assert assets['hra-bladder-female-v1.1-vh_f_trigone_of_urinary_bladder']['source_context']['population'] == {'life_stage': 'adult', 'sex': 'female'}
    assert assets['hra-bladder-male-v1.1-vh_m_trigone_of_urinary_bladder']['source']['url'].endswith('urinary-bladder-male/v1.1')
    cohort = review['sources']['colonvessels']['cohort_evidence']
    excerpt = (tool.ROOT / cohort['path']).read_bytes()
    assert hashlib.sha256(excerpt).hexdigest() == cohort['sha256']
    lines = ' '.join(json.loads(excerpt)['lines'].values())
    assert '50 adult patients' in lines and 'Age range: 32–89 years' in lines and 'semi-automatically extracted' in lines
    assert assets['colonvessels-pat012-veins-layer-2-value-7']['source_context']['population'] == {'life_stage': 'adult'}
    # The male HRA bladder is symmetrical, so its sides rest on the release's convention, and its records say so.
    assert review['frames']['hra-male']['axes_basis'] == 'convention' and review['frames']['hra-female']['axes_basis'] == 'anatomy'
    for ident, leaf in (('hra-bladder-male-v1.1-vh_m_ureteral_orifice_r', 'bladder.uvj.right.ureteral_orifice'),
                        ('hra-bladder-male-v1.1-vh_m_ureteral_orifice_l', 'bladder.uvj.left.ureteral_orifice')):
        assert 'convention' in assets[ident]['requirement_coverage'][leaf]['basis']
    assert 'convention' not in assets['hra-bladder-female-v1.1-vh_f_ureteral_orifice_r']['requirement_coverage']['bladder.uvj.right.ureteral_orifice']['basis']


def bounds(key, meshes):
    xs, ys, zs = zip(*tool.positions(key, meshes[key])[0])
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def test_source_objects_whose_labels_disagree_with_their_geometry_are_corrected_or_not_bound():
    review, _, _, _ = records()
    meshes = tool.inventory(review)
    recorded = {row['mesh'] for row in review['accepted']}
    manifest = json.loads((tool.ANATOMY / 'bodyparts3d/manifest.json').read_text())['parts']
    excerpt = json.loads((tool.DOCS / 'evidence/bodyparts3d-4.0-isa-element-parts-excerpt.json').read_text())
    official = collections.defaultdict(list)
    for line in excerpt['lines'].values():
        concept, name, element = line.split('\t')
        official[name].append(element)
    # The official 4.0 table assigns these objects.
    assert official == {'trunk of portal vein': ['FJ3102', 'FJ3122'], 'hepatovenous segment v': ['FJ2821'], 'hepatovenous segment vi': ['FJ2822'],
                        'hepatovenous segment vii': ['FJ2409'], 'hepatovenous segment viii': ['FJ2823', 'FJ2824']}
    # BodyParts3D 4.3 names the same objects differently.
    table = (tool.ROOT / 'docs/cardiac-wall-context-review-20261016/obj2FMA-4.3.html').read_text(encoding='utf-8', errors='replace')

    def later_name(element):
        return re.search(r'<td class="art_id">%s</td>\s*<td class="rep_id">[^<]*</td>\s*<td class="cdi_name">[^<]*</td>\s*'
                         r'<td class="cdi_name_e">([^<]*)</td>' % element, table).group(1)
    assert later_name('FJ2409') == 'Hepatovenous segment VI' and later_name('FJ2822') == 'Hepatovenous segment VI'
    assert later_name('FJ2823') == 'Hepatovenous segment VII' and later_name('FJ2824') == 'Hepatovenous segment VIII'
    assert later_name('FJ3102') == 'Trunk of left portal vein' and later_name('FJ3122') == 'Trunk of right portal vein'
    # The atlas follows the later table for the two segments, records what the official table says, and shows each portal trunk by its own name.
    assert not {'FJ2409', 'FMA15746', 'FMA14329'} & set(manifest)
    for code, name, was in (('FJ2823', 'hepatovenous segment vii', ['FJ2409']), ('FJ2824', 'hepatovenous segment viii', ['FJ2823', 'FJ2824'])):
        assert manifest[code]['name'] == name and manifest[code]['source_ids'] == [code]
        assert manifest[code]['source_correction']['official_table_source_ids'] == was == official[name]
    assert manifest['FJ3102']['name'] == 'trunk of left portal vein' and manifest['FJ3122']['name'] == 'trunk of right portal vein'
    assert 'source_correction' not in manifest['FJ3102'] and 'source_correction' not in manifest['FJ3122']
    # No segment mesh now has another segment's bounds: the object the official table calls segment VII had segment VI's.
    codes = ('FJ2816', 'FJ2818', 'FJ2819', 'FJ2820', 'FJ2821', 'FJ2822', 'FJ2823', 'FJ2824')
    boxes = {code: bounds('bodyparts3d/%s.bin' % code, meshes) for code in codes}
    for first in codes:
        for second_code in codes:
            if first < second_code:
                assert max(abs(a - b) for a, b in zip(boxes[first], boxes[second_code])) > 15, (first, second_code)
    # The four corrected meshes are bound; the main portal vein is not, because the requirements split it into lumen and wall.
    assert {'bodyparts3d/%s.bin' % code for code in ('FJ2823', 'FJ2824', 'FJ3102', 'FJ3122')} <= recorded
    assert 'bodyparts3d/FJ3082.bin' not in recorded and 'lumen' in review['not_recorded']['bodyparts3d/FJ3082.bin']
    # The object labelled common hepatic duct runs far below the cystic duct, and stays unbound.
    duct, cystic = bounds('bp3d-biliary-4.3/FJ3079.mesh.gz', meshes), bounds('bp3d-biliary-4.3/FJ3080.mesh.gz', meshes)
    assert duct[5] - duct[4] > 80 and cystic[4] - duct[4] > 55
    key = 'bp3d-biliary-4.3/FJ3079.mesh.gz'
    assert key not in recorded and 'common bile duct' in review['not_recorded'][key]
    assert len(review['source_findings']) == 7 and all(review['source_findings'])
    assert 'corrected' in review['source_findings'][0] and 'FJ2823' in review['source_findings'][0]
    # Repeated source objects keep their own records; the cystic duct pair fills the same place.
    assert max(abs(a - b) for a, b in zip(cystic, bounds('bp3d-biliary-4.3/FJ4526.mesh.gz', meshes))) < 0.5
    assert {'bp3d-biliary-4.3/FJ3080.mesh.gz', 'bp3d-biliary-4.3/FJ4526.mesh.gz'} <= recorded


def test_recorded_bodyparts3d_labels_agree_with_the_later_object_table():
    review, _, _, _ = records()
    meshes = tool.inventory(review)
    manifest = json.loads((tool.ANATOMY / 'bodyparts3d/manifest.json').read_text())['parts']
    table = (tool.ROOT / 'docs/cardiac-wall-context-review-20261016/obj2FMA-4.3.html').read_text(encoding='utf-8', errors='replace')
    later = collections.defaultdict(set)
    for element, name in re.findall(r'<td class="art_id">([^<]*)</td>\s*<td class="rep_id">[^<]*</td>\s*<td class="cdi_name">[^<]*</td>\s*'
                                    r'<td class="cdi_name_e">([^<]*)</td>', table):
        later[element].add(name.lower())
    # The reader names the superior bulb of the internal jugular vein by its common name.
    reader_names = {'right jugular bulb': 'superior bulb of right internal jugular vein'}
    checked = 0
    for key in sorted({row['mesh'] for row in review['accepted']}):
        mesh = meshes[key]
        if mesh['atlas'] not in ('bodyparts3d', 'bodyparts3d-4.3'):
            continue
        elements = manifest[mesh['code']]['source_ids'] if mesh['atlas'] == 'bodyparts3d' else [mesh['code']]
        label = mesh['label'].lower()
        for element in elements:
            assert later[element] == {reader_names.get(label, label)}, (key, element)
            checked += 1
    # 75 recorded meshes; the circumflex artery has six source objects and the cerebellum two.
    assert checked == 81
    # The object the official 4.0 table calls segment VII is a second segment VI; the atlas no longer delivers it.
    assert later['FJ2409'] == {'hepatovenous segment vi'} and 'FJ2409' not in manifest


def test_bound_liver_segments_lie_where_their_numbers_say():
    review, _, _, _ = records()
    meshes = tool.inventory(review)
    recorded = {row['mesh'] for row in review['accepted']}

    def centre(key):
        assert key in recorded
        points = tool.positions(key, meshes[key])[0]
        return [sum(point[axis] for point in points) / len(points) for axis in range(3)]
    # Liver-region MRI: the mesh coordinates follow the source axes R, A, S.
    assert json.loads((tool.ANATOMY / 'liver-regions-mri/volume.json').read_text())['sourceAxes'] == ['R', 'A', 'S']
    region = {number: centre('liver-regions-mri/region-%d.mesh.gz' % number) for number in (1, 2, 3, 5, 6, 7, 8)}
    assert all(region[right][0] > region[left][0] + 50 for right in (5, 6, 7, 8) for left in (2, 3))   # right lobe, left lateral section
    assert region[2][2] > region[3][2] and region[8][2] > region[5][2] and region[7][2] > region[6][2]  # superior above inferior
    assert region[5][1] > region[6][1] and region[8][1] > region[7][1]                                   # anterior before posterior
    assert region[2][0] < region[1][0] < region[5][0]                                                     # the caudate lies between
    # PHLF: region 7 lies above region 6.
    assert centre('phlf-center2-24/regions-7.mesh.gz')[2] > centre('phlf-center2-24/regions-6.mesh.gz')[2] + 30
    # BodyParts3D (-X right, -Y anterior, +Z up): II above III on the left; on the right, V in front of VI, VIII in front of VII,
    # VII above VI and VIII above V.
    part = {name: centre('bodyparts3d/%s.bin' % code) for name, code in (
        ('ii', 'FJ2818'), ('iii', 'FJ2819'), ('v', 'FJ2821'), ('vi', 'FJ2822'), ('vii', 'FJ2823'), ('viii', 'FJ2824'))}
    assert part['ii'][2] > part['iii'][2] and part['ii'][0] > 0 and part['iii'][0] > 0
    assert all(part[name][0] < -40 for name in ('v', 'vi', 'vii', 'viii'))
    assert part['v'][1] < part['vi'][1] - 30 and part['viii'][1] < part['vii'][1] - 30
    assert part['vii'][2] > part['vi'][2] + 30 and part['viii'][2] > part['v'][2] + 30


def test_each_bound_bile_duct_tributary_lies_inside_the_segment_it_is_bound_to():
    review, _, _, _ = records()
    meshes = tool.inventory(review)

    def box(found):
        return [(min(point[axis] for point in found), max(point[axis] for point in found)) for axis in range(3)]
    # The 4.3 biliary objects share the 4.0 atlas's coordinates.
    segment = {name: box(tool.positions('bodyparts3d/%s.bin' % code, meshes['bodyparts3d/%s.bin' % code])[0])
               for name, code in (('II', 'FJ2818'), ('III', 'FJ2819'), ('IV', 'FJ2820'), ('V', 'FJ2821'), ('VI', 'FJ2822'),
                                  ('VII', 'FJ2823'), ('VIII', 'FJ2824'))}
    checked = 0
    for row in review['accepted']:
        found = re.fullmatch(r'biliary\.segment_(?:left|right)_[a-z]+_([IV]+)\..*', row['structure_id'])
        if not found:
            continue
        cloud = tool.positions(row['mesh'], meshes[row['mesh']])[0]
        centre = [sum(point[axis] for point in cloud) / len(cloud) for axis in range(3)]
        assert all(low <= value <= high for value, (low, high) in zip(centre, segment[found.group(1)])), row['mesh']
        checked += 1
    assert checked == 12


def test_body_reader_model_records_have_an_exact_inverse_and_only_add_records():
    receipt = json.loads(tool.RECEIPT.read_text())
    raw = tool.EVIDENCE.read_bytes()
    assert second.sha(raw) == receipt['after_sha256'] and receipt['path'] == PATH
    before = tool.before_body_reader_model_records(raw)
    assert second.sha(before) == receipt['before_sha256']
    assert tool.before_body_reader_model_records(before) == before
    assert tool.before_body_reader_model_records(raw + b'\n') == raw + b'\n'
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    # The ledger before this pass is the ledger right after the brain readers' pass.
    assert second.sha(before) == json.loads(brain.RECEIPT.read_text())['after_sha256']
    old_view, new_view = json.loads(before), json.loads(raw)
    assert {k: v for k, v in old_view.items() if k != 'assets'} == {k: v for k, v in new_view.items() if k != 'assets'}
    added = new_view['assets'][len(old_view['assets']):]
    assert new_view['assets'][:len(old_view['assets'])] == old_view['assets'] and len(added) == 123
    assert [item['id'] for item in added] == sorted({row['asset_id'] for row in json.loads(tool.REVIEW.read_text())['accepted']})
    # The history chain peels this pass first.
    assert history.before_activity_registry_bytes(PATH, raw) == history.before_activity_registry_bytes(PATH, before)


def test_the_tool_refuses_a_row_that_breaks_a_rule(tmp_path, monkeypatch):
    review = json.loads(tool.REVIEW.read_text())
    leaves, names, _ = tool.requirement_leaves()
    ledger, document = tmp_path / 'evidence.json', tmp_path / 'review.json'
    ledger.write_bytes(tool.before_body_reader_model_records(tool.EVIDENCE.read_bytes()))
    monkeypatch.setattr(tool, 'EVIDENCE', ledger)
    monkeypatch.setattr(tool, 'REVIEW', document)
    document.write_text(json.dumps(review))
    made = tool.plan()
    assert len(made) == 123 and sum(len(item['structure_ids']) for item in made) == 212
    rows = review['accepted']
    kidney = next(i for i, row in enumerate(rows) if row['structure_id'] == 'renal_mass.right_kidney.whole_extent')
    segment = next(i for i, row in enumerate(rows) if row['quote'] == 'hepatovenous segment iii' and row['structure_id'].startswith('liver_mass.'))
    renal, cervix = 'bodyparts3d/FJ2038.bin', 'kcl-cervix/055t/label-1.mesh.gz'
    finding = min(leaf for leaf, found in leaves.items() if 'ra.solid-renal-masses' in found
                  and [target.get('purpose') for target in tool.context_targets(found['ra.solid-renal-masses'])] == ['pathology_example'])
    cases = {
        'not in an investigation whose reader shows': (kidney, dict(rows[kidney], investigations=['ra.adrenal-lesions'])),
        'not the mesh’s source label': (kidney, dict(rows[kidney], quote='right kidney and ureter')),
        'does not name the requirement': (kidney, dict(rows[kidney], term='adrenal')),
        # The right kidney's mesh cannot bind the left kidney.
        'Side of the label, the mesh and the requirement disagree': (kidney, dict(
            rows[kidney], structure_id='renal_mass.left_kidney.whole_extent', name='Left kidney and localisation anatomy: Complete acquired renal extent')),
        'not the kind of leaf recorded': (kidney, dict(rows[kidney], leaf_basis='named_part')),
        # A BodyParts3D vessel surface is not a lumen.
        'opacified lumen': (kidney, dict(rows[kidney], mesh=renal, asset_id=tool.asset_id(renal), quote='right renal artery', term='renal artery',
                                        structure_id='renal_mass.right_renal_arterial_supply.main_lumina', leaf_basis='named_part',
                                        name='Right renal arterial supply: Main renal artery lumina')),
        # The listed name of hepatovenous segment II is a substring of “hepatovenous segment iii”, but not the same words.
        'Label does not name the requirement': (segment, dict(
            rows[segment], structure_id='liver_mass.segment_ii.parenchymal_territory',
            name='Source-defined Couinaud II left lateral superior: Actual parenchymal territory',
            another_name={'label_word': 'hepatovenous segment ii', 'requirement_word': 'couinaud ii'})),
        # An anatomy atlas is not an example of pathology.
        'example of pathology is not bound': (kidney, dict(rows[kidney], structure_id=finding, name=names[finding])),
        # An adult atlas is not bound to paediatric anatomy.
        'paediatric anatomy needs a paediatric source': (kidney, dict(
            rows[kidney], structure_id='paediatric_renal_tumours.right_kidney', name='Right kidney', leaf_basis='structure',
            investigations=['ra.paediatric-renal-tumours'])),
        # A pregnancy atlas is not bound in cervical cancer staging.
        'Source is not bound: pregnancy population atlases': (kidney, dict(
            rows[kidney], mesh=cervix, asset_id=tool.asset_id(cervix), atlas='kcl-cervix', quote='Endocervical canal', term='cervical canal',
            structure_id='cervical_cancer.central.cervical_canal.actual_covered_identity_and_extent', investigations=['ra.mri-cervical-cancer'])),
    }
    for problem, (index, broken) in cases.items():
        document.write_text(json.dumps(dict(review, accepted=rows[:index] + [broken] + rows[index + 1:])))
        with pytest.raises(ValueError, match=problem):
            tool.plan()
    # A pair that no binding uses may not stay in the list.
    unused = {'label_word': 'hepatovenous segment iv', 'requirement_word': 'couinaud iv'}
    document.write_text(json.dumps(dict(review, another_name_pairs=review['another_name_pairs'] + [unused],
                                        another_name_reasons=dict(review['another_name_reasons'], **{'hepatovenous segment iv>couinaud iv': 'unused'}))))
    with pytest.raises(ValueError, match='pair is used by no binding'):
        tool.plan()
