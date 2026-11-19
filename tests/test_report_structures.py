"""Every structure a study is routinely reported on has a heading (tools/authoring/report_structures_20261117.py)."""
import json
import re
import sys
from pathlib import Path

from primer import report_templates as rt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'authoring'))
import radproof_export  # noqa: E402
import report_structures_20261117 as structures  # noqa: E402

PRISM = json.loads((ROOT / 'data/radiology/prism-titles.json').read_text())


def _performed():
    excluded = set(PRISM['not_performed_studies'])
    return {identifier: item for identifier, item in rt.library().items() if identifier not in excluded}


def _headings(identifier):
    return [section['heading'] for section in rt.library()[identifier]['sections']]


def _groups(identifier):
    return {group: [section['heading'] for section in members]
            for group, members in rt._blocks(rt.library()[identifier]['sections']) if group}


def test_the_templates_are_what_the_authoring_content_writes():
    blocks, specs = structures.parse(structures.CONTENT)
    assert len(specs) >= 170
    library = rt.library()
    for identifier, ops in specs.items():
        current = library[identifier]['sections']
        assert structures.build(identifier, current, structures.expand(ops, blocks)) == current, identifier


def test_no_heading_hides_structures_behind_a_collective_word():
    collective = {'Tendons', 'Ligaments', 'Nerves', 'Valves', 'Vascular', 'Access', 'Pelvic organs', 'Alternative findings'}
    hidden = re.compile(r'^(?:Other|Remaining)\b.*\b(?:organs|chest|abdomen)\b')
    for identifier, item in _performed().items():
        for section in item['sections']:
            heading = section['heading']
            assert heading not in collective and not hidden.search(heading), (identifier, heading)


def test_wrist_mri_lists_its_ligaments_under_intrinsic_and_extrinsic_subheadings():
    groups = _groups('msk.mri-wrist')
    assert groups['Intrinsic ligaments'] == ['Scapholunate ligament', 'Lunotriquetral ligament']
    assert groups['Extrinsic ligaments'] == [
        'Radioscaphocapitate ligament', 'Long and short radiolunate ligaments', 'Ulnolunate and ulnotriquetral ligaments',
        'Dorsal radiocarpal ligament', 'Dorsal intercarpal ligament']
    assert groups['Triangular fibrocartilage complex'] == [
        'Articular disc', 'Foveal and styloid attachments', 'Dorsal and volar radioulnar ligaments']
    assert [heading.split(' ')[0] for heading in groups['Extensor tendons']] == ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth']
    assert list(groups) == ['Bones and alignment', 'Joints', 'Intrinsic ligaments', 'Extrinsic ligaments',
                            'Triangular fibrocartilage complex', 'Extensor tendons', 'Flexor tendons', 'Nerves']
    headings = _headings('msk.mri-wrist')
    for structure in ('Scaphoid', 'Lunate', 'Distal radioulnar joint', 'Median nerve and carpal tunnel',
                      'Ulnar nerve and Guyon canal', 'Soft tissues'):
        assert structure in headings


def test_joint_studies_name_each_ligament_tendon_and_compartment():
    required = {
        'ra.mri-knee': ['Medial meniscus', 'Lateral meniscus', 'Anterior cruciate ligament', 'Posterior cruciate ligament',
                        'Medial collateral ligament', 'Lateral collateral ligament', 'Posterolateral corner',
                        'Quadriceps tendon', 'Patellar tendon', 'Medial compartment', 'Lateral compartment',
                        'Patellofemoral compartment', 'Popliteal fossa'],
        'ra.mri-shoulder': ['Supraspinatus tendon', 'Infraspinatus tendon', 'Subscapularis tendon', 'Teres minor tendon',
                            'Long head of biceps tendon', 'Superior labrum and biceps anchor', 'Anterior labrum',
                            'Posterior labrum', 'Glenohumeral joint', 'Acromioclavicular joint'],
        'ra.mri-elbow': ['Common extensor tendon', 'Common flexor tendon', 'Triceps tendon', 'Ulnar collateral ligament',
                         'Radial collateral ligament', 'Lateral ulnar collateral ligament', 'Annular ligament',
                         'Ulnar nerve', 'Median nerve'],
        'ra.mri-ankle': ['Anterior talofibular ligament', 'Calcaneofibular ligament', 'Posterior talofibular ligament',
                         'Deltoid ligament', 'Spring ligament', 'Tibialis posterior tendon', 'Peroneus longus tendon',
                         'Peroneus brevis tendon', 'Achilles tendon', 'Plantar fascia', 'Sinus tarsi', 'Talus'],
        'msk.mri-hip': ['Labrum', 'Articular cartilage', 'Ligamentum teres', 'Gluteus medius and minimus tendons',
                        'Iliopsoas tendon and bursa', 'Hamstring origin', 'Femoral head and neck'],
        'msk.ultrasound-wrist': ['First compartment (APL and EPB)', 'Sixth compartment (ECU)',
                                 'Median nerve and carpal tunnel', 'Dorsal scapholunate ligament'],
        'ra.ultrasound-shoulder': ['Long head of biceps tendon', 'Subscapularis tendon', 'Supraspinatus tendon',
                                   'Infraspinatus tendon', 'Teres minor tendon', 'Acromioclavicular joint'],
    }
    for identifier, structures_ in required.items():
        headings = _headings(identifier)
        for structure in structures_:
            assert structure in headings, (identifier, structure)


def test_every_study_of_a_region_lists_the_whole_region():
    regions = [
        (r'^CT abdomen and pelvis\b', ['liver', 'gallbladder', 'pancrea', 'spleen', 'adrenal', 'kidney', 'bladder',
                                       'bowel', 'periton', 'lung bases', 'bones']),
        (r'^(?:HRCT|Low-dose CT|CT) chest(?!, abdomen)', ['lung|nodule|interstitium', 'pleura', 'mediastin|lymph nodes',
                                                         'heart|pericardium', 'upper abdomen|adrenal', 'bones']),
        (r'^MRI brain(?! and spine)', ['ventricles', 'orbits', 'sinuses', 'skull']),
        (r'^MRI (?:lumbar|cervical) spine$', ['alignment', 'vertebrae', 'l4-l5|c5-6', 'paraspinal']),
        (r'^Ultrasound abdomen(?: and pelvis, (?:fe)?male)?$', ['liver', 'gallbladder', 'bile ducts', 'pancreas', 'spleen',
                                                               'right kidney', 'left kidney', 'aorta']),
    ]
    matched = 0
    for identifier, item in _performed().items():
        headings = ' | '.join(section['heading'] for section in item['sections']).lower()
        for title, words in regions:
            if re.search(title, item['title']) and 'RECIST' not in item['title']:
                matched += 1
                for word in words:
                    assert re.search(word, headings), (identifier, word, headings)
    assert matched >= 30


def test_spine_mri_reports_every_disc_level():
    assert _groups('ra.mri-lumbar-disc')['Lumbar discs'] == ['T12-L1', 'L1-L2', 'L2-L3', 'L3-L4', 'L4-L5', 'L5-S1']
    # Cervical levels are written as the department writes them (C2-3), lumbar as before (L4-L5).
    assert _groups('neuro.mri-spine-cervical')['Cervical discs'] == ['C2-3', 'C3-4', 'C4-5', 'C5-6', 'C6-7', 'C7-T1']


def test_bilateral_and_multi_region_studies_group_their_headings():
    assert list(_groups('ct.trauma-panscan')) == ['Head', 'Cervical spine', 'Chest', 'Abdomen and pelvis',
                                                  'Thoracolumbar spine and pelvis']
    assert list(_groups('ct.oncology-staging')) == ['Neck', 'Chest', 'Abdomen and pelvis']
    assert list(_groups('ct.angiogram-lower-limbs')) == ['Right leg', 'Left leg']
    assert _groups('ra.carotid-obstruction')['Right carotid'] == [
        'Right common carotid artery', 'Right internal carotid artery', 'Right external carotid artery']
    assert _groups('cardiology.echocardiography')['Valves'] == ['Aortic valve', 'Mitral valve', 'Tricuspid valve', 'Pulmonary valve']


def test_a_subheading_is_set_out_in_every_layout():
    report = rt.quick_report('msk.mri-wrist')
    assert report['headings'][:5] == ['Protocol', 'Findings', 'Bones and alignment', 'Distal radius and ulna', 'Scaphoid']
    assert '\n\nIntrinsic ligaments:\nScapholunate ligament: []\nLunotriquetral ligament: []\n\nExtrinsic ligaments:\n' in report['dictation']['text']
    assert '\n\nIntrinsic ligaments:\nScapholunate ligament:\n• Intact.\nLunotriquetral ligament:\n• Intact.\n\n' in report['normal']
    assert 'Scapholunate ligament:\n• Intact.\n• [Partial / Complete] tear of the [volar / membranous / dorsal] component' in report['template']
    dictation = {template['id']: template['text'] for template in radproof_export.export(dictation=True)}
    # RadProof sets out a part of a report in bold; the headings under it keep their blanks.
    # Bold and underline only for section headings: a subheading stands apart, plain.
    assert '\n\nIntrinsic ligaments:\nScapholunate ligament: []\nLunotriquetral ligament: []\n\nExtrinsic ligaments:\n' in dictation['msk.mri-wrist']
    # Every template opens with clinical history and comparison, then the study title: no heading is all capitals.
    assert dictation['msk.mri-wrist'].startswith(
        '**__Clinical history:__**\n[]\n\n**__Comparison:__**\n[]\n\n**__MRI {side} wrist:__**\n**__Protocol:__**\n')
    library = rt.library()
    for identifier, text in dictation.items():
        lines = text.split('\n')
        title = re.fullmatch(r'\*\*__(.+):__\*\*', lines[6]).group(1)
        assert lines[:6] == radproof_export.HISTORY, identifier
        # Only a title that is acronyms throughout (CT KUB, FDG PET/CT) is in capitals.
        assert title != title.upper() or library[identifier]['title'] == library[identifier]['title'].upper(), title
    assert '**__Findings:__**\nBones and alignment:\nDistal radius and ulna: []\n' in dictation['msk.mri-wrist']
    assert '\n\nLumbar discs:\nT12-L1: []\nL1-L2: []\nL2-L3: []\nL3-L4: []\nL4-L5: []\nL5-S1: []\n\n' in dictation['ra.mri-lumbar-disc']
    for text in dictation.values():
        assert '[ ]' not in text
        # Bold and underline only for section headings, each a whole line; everything else is plain.
        headings = [line for line in text.split('\n') if '**' in line or '__' in line]  # not T2*
        assert all(re.fullmatch(r'\*\*__[^_*]+:__\*\*', line) for line in headings), headings
        assert {'**__Clinical history:__**', '**__Comparison:__**'} <= set(headings)
        assert ({'**__Impression:__**', '**__Recommendation:__**'} <= set(headings)) != ('**__Conclusion:__**' in headings)


def test_the_normal_report_says_a_group_once_when_all_of_it_is_normal():
    normal = {template['id']: template['text'] for template in radproof_export.export()}
    wrist = normal['msk.mri-wrist']
    assert ('Intact intrinsic ligaments.\nIntact extrinsic ligaments.\nIntact triangular fibrocartilage complex.\n'
            'Normal extensor tendons.\nNormal flexor tendons.\n') in wrist
    assert 'No scaphoid fracture, nonunion or avascular necrosis.' in wrist
    assert 'Lumbar discs: no disc herniation, canal stenosis or foraminal stenosis.' in normal['ra.mri-lumbar-disc']
    assert 'Coronary arteries: no plaque or stenosis.' in normal['ra.ct-coronary']
    assert 'Intact menisci.\nIntact cruciate ligaments.\n' in normal['ra.mri-knee']
    # A group that is not uniform keeps a line for each heading, and a proper noun keeps its capital.
    assert 'Intact peroneus longus tendon.\nIntact peroneus brevis tendon.\nIntact peroneal retinaculum.' in normal['ra.mri-ankle']
    assert 'Intact Achilles tendon.' in normal['ra.mri-ankle'] and 'Normal Hoffa fat pad.' in normal['ra.mri-knee']
    # A whole-body study prints each region above its own lines.
    lines = normal['ct.trauma-panscan'].split('\n')
    assert lines[lines.index('Cervical spine') + 1] == 'Normal cervical alignment, including the craniocervical junction.'
    assert [line for line in lines if line in {'Head', 'Cervical spine', 'Chest', 'Abdomen and pelvis'}] == [
        'Head', 'Cervical spine', 'Chest', 'Abdomen and pelvis']


def test_ct_and_mri_of_the_same_organ_keep_their_own_vocabulary():
    for identifier, item in _performed().items():
        text = json.dumps(item['sections'], ensure_ascii=False)
        if re.search(r'\bCT\b|\bHRCT\b', item['title']):
            assert not re.search(r'marrow signal|opposed phase|T2 hyperintens|flow void', text), identifier
        if re.search(r'\bMRI\b|\bMRCP\b', item['title']):
            assert not re.search(r'\[ \] HU\b|hyperdense', text), identifier


def test_studies_of_one_kind_read_alike():
    # Every adult chest radiograph has the same headings, after any heading of its own question.
    chest = ['Lungs', 'Pleura', 'Heart and mediastinum', 'Hila', 'Diaphragm', 'Bones and soft tissues']
    for identifier in ('ra.chest-radiography', 'xr.chest-immigration', 'ra.tuberculosis', 'ra.cardiovascular-devices'):
        headings = _headings(identifier)
        start = headings.index('Lungs')
        assert headings[start:start + 6] == chest, identifier
    # A limb radiograph reports its bones before alignment and joints, and its soft tissues last.
    for identifier, item in _performed().items():
        if re.fullmatch(r'Right [a-z ]+ radiographs / Left [a-z ]+ radiographs', item['title']):
            headings = _headings(identifier)
            assert headings[-1].lower().endswith('soft tissues'), identifier
            if 'stress' not in identifier:
                assert not re.search(r'joint|alignment|mortise', headings[0], re.I), identifier
    # Every chest CT names the mediastinum, nodes, heart and great vessels as the general study does.
    old = {'Heart and great vessels', 'Mediastinum and lymph nodes', 'Lungs and pleura', 'Chest wall and bones',
           'Heart and aorta', 'Pulmonary arteries and heart', 'Mediastinum'}
    for identifier, item in _performed().items():
        if re.match(r'(?:HRCT|Low-dose CT|CT) chest(?!, abdomen)', item['title']):
            assert not old & set(_headings(identifier)), identifier
    # Spine injury: alignment and vertebrae first, the classification last.
    for identifier in ('ra.cervical-spine-injury', 'mri.cervical-spine-trauma', 'ra.thoracolumbar-injury',
                       'ra.thoracolumbar-fractures', 'mri.thoracolumbar-trauma'):
        headings = _headings(identifier)
        assert headings[:2] == ['Alignment', 'Vertebrae'] and headings[-1] == 'Classification', identifier
    # Every procedure records consent and time-out, and ends with its complications.
    for identifier, item in _performed().items():
        sections = {section['heading']: section for section in item['sections']}
        if 'Procedure' in sections:
            assert sections['Procedure']['normal'].startswith('Informed consent obtained. Time-out completed.'), identifier
            assert _headings(identifier)[-1] == 'Complications', identifier
    # CT and MRI of the brain name its parts alike.
    for identifier in ('neuro.ct-brain-routine', 'neuro.mri-brain-routine'):
        assert {'Brainstem and cerebellum', 'Ventricles and basal cisterns', 'Sulci and extra-axial spaces', 'Orbits',
                'Paranasal sinuses and mastoids', 'Skull and scalp'} <= set(_headings(identifier)), identifier


def test_one_name_for_one_set_of_structures():
    def parts(heading):  # the words, in any order: "Thyroid and salivary glands" is "Salivary and thyroid glands"
        return tuple(sorted(word for word in re.findall(r'[a-z0-9]+', heading.lower()) if word != 'and'))
    names = {}
    for item in _performed().values():
        for section in item['sections']:
            names.setdefault(parts(section['heading']), set()).add(section['heading'])
    assert [sorted(found) for found in names.values() if len(found) > 1] == []  # not "Bones and soft tissues" and "Soft tissues and bones"


def test_the_soft_tissue_neck_ultrasound_surveys_the_whole_neck():
    """Peter asked for it (2026-11-19): the general neck ultrasound, apart from the lymph node study."""
    assert _headings('us.soft-tissue-neck') == [
        'Area of concern', 'Parotid glands', 'Submandibular glands', 'Thyroid gland', 'Right neck', 'Left neck',
        'Vessels', 'Muscles and soft tissues']
    assert _groups('us.soft-tissue-neck') == {
        'Salivary and thyroid glands': ['Parotid glands', 'Submandibular glands', 'Thyroid gland'],
        'Lymph nodes': ['Right neck', 'Left neck']}
    # The practice's general neck titles choose it; the lymph node study keeps its own.
    assert {'ultrasound soft tissue neck', 'ultrasound neck', 'sonar neck'} <= set(PRISM['titles']['us.soft-tissue-neck'])
    assert PRISM['titles']['ra.cervical-lymph-nodes'] == ['ultrasound neck lymph nodes', 'ultrasound cervical lymph nodes']
    assert PRISM['practice_studies']['Ultrasound neck'] == 'us.soft-tissue-neck'
    dictation = {template['id']: template for template in radproof_export.export(dictation=True)}
    neck = dictation['us.soft-tissue-neck']
    assert neck['name'] == 'Ultrasound soft tissue neck'
    assert '**__Ultrasound soft tissue neck:__**\nArea of concern: []\n\nSalivary and thyroid glands:\n' in neck['text']
    # The click builder has the same structures, every finding enumerated.
    from primer.reporting_bridge import descriptor_forms
    investigation = next(i for form in descriptor_forms()['forms'].values() for i in form['investigations']
                         if i['id'] == 'us.soft-tissue-neck')
    assert investigation['modality'] == 'Ultrasound'
    assert [section['label'] for section in investigation['sections']][1:] == [
        'Area of concern', 'Parotid glands', 'Submandibular glands', 'Thyroid gland', 'Right neck', 'Left neck',
        'Vessels', 'Muscles and soft tissues']


CERVICAL_SPINE = """**__Clinical history:__**
[]

**__Comparison:__**
[]

**__MRI cervical spine:__**
**__Technique:__**
Sagittal T1 and T2 weighted sequences.
Axial T2 and T2* sequences.
Right and left sagittal oblique T2 sequences.

**__Findings:__**
The visualised posterior fossa structures and lung apices are normal.
Normal vertebral body alignment.
Normal marrow and intervertebral disc signal.
Normal CSF signal.
Normal cord calibre and signal.

C2-3: []

C3-4: []

C4-5: []

C5-6: []

C6-7: []

C7-T1: []

**__Conclusion:__**
[]"""


def test_mri_cervical_spine_dictates_as_the_department_writes_it():
    """Peter's own template (photo, 2026-11-19): its sequences, normal sentences, levels and Conclusion."""
    dictation = {template['id']: template for template in radproof_export.export(dictation=True)}
    assert dictation['neuro.mri-spine-cervical']['text'] == CERVICAL_SPINE
    # Primer's own dictation template is the same text without RadProof's markup (and no colon after the name).
    primer = rt.quick_report('neuro.mri-spine-cervical')['dictation']['text']
    plain = re.sub(r'\*\*__(.+?):__\*\*', r'\1:', CERVICAL_SPINE).replace('MRI cervical spine:\n', 'MRI cervical spine\n')
    assert primer == plain
    # The fast template and click builder use the same acquisition.
    assert rt.library()['neuro.mri-spine-cervical']['technique']['normal'] == (
        'Sagittal T1 and T2 weighted sequences. Axial T2 and T2* sequences. Right and left sagittal oblique T2 sequences.')
