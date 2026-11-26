"""Build the CT chest, abdomen and pelvis teaching inventory from both published report formats."""
import argparse
from collections import Counter
import hashlib
import gzip
import json
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
EXAM = 'ct.chest-abdomen-pelvis'
AUTHOR = 'data/radiology/anatomic-additions-20261119.json'
FAST = 'data/radiology/report-templates/additions-20261119.json'
COMPILED = 'data/radiology/descriptor-reporting.json'
OUTPUT = 'data/radiology/descriptor-requirements/chest-abdomen-pelvis.json'
ATLAS = 'web/anatomy/ct-torso-s0028'
GUIDE = ATLAS + '/report-guide.json'
VERIFIED = 'docs/ct-torso-s0028/source-comparison.json'
KINDS = ('clinical_image', 'schematic', 'model')
ANCHORS = {'clinical_image': 'ct-section', 'schematic': 'ct-section', 'model': 'source-surface'}

# The named report compartments determine the anatomy. The publisher's remaining
# labels stay available in the source viewer without creating report obligations.
def anatomy():
    targets = []

    def add(key, name, role, side='not_applicable', source=None):
        targets.append(dict(id='cap.' + key, name=name, laterality=side, tissue_class=role,
                            source_section_id=section, source_label=source))

    def pair(key, name, role, source_stem=None):
        for side in ('right', 'left'):
            add(key + '.' + side, side.capitalize() + ' ' + name, role, side,
                source_stem + '_' + side if source_stem else None)

    section = 'lungs-and-airways'
    for side, lobes in [('right', ('upper', 'middle', 'lower')), ('left', ('upper', 'lower'))]:
        for lobe in lobes:
            source = f'lung_{lobe}_lobe_{side}'
            add(source, f'{side.capitalize()} {lobe} lobe', 'lung_lobe', side, source)
    add('lingula', 'Lingula', 'lung_subdivision', 'left')
    add('trachea', 'Trachea', 'central_airway', source='trachea')
    pair('main_bronchus', 'main bronchus', 'central_airway')

    section = 'pleura-and-pericardium'
    pair('pleura', 'pleura', 'serosal_membrane')
    pair('pleural_space', 'pleural space', 'potential_space')
    add('pericardium', 'Pericardium', 'membrane')
    add('pericardial_space', 'Pericardial space', 'potential_space')

    section = 'thoracic-lymph-nodes'
    add('mediastinal_nodal_region', 'Mediastinal nodal regions', 'nodal_region')
    for location in ('hilar', 'axillary', 'supraclavicular'):
        pair(location + '_nodal_region', location + ' nodal region', 'nodal_region')

    section = 'heart-and-great-vessels'
    add('heart', 'Heart', 'organ', source='heart')
    add('aorta', 'Aorta', 'artery', source='aorta')
    add('pulmonary_trunk', 'Pulmonary trunk', 'artery')
    pair('pulmonary_artery', 'pulmonary artery', 'artery')
    add('coronary_tree', 'Epicardial coronary arteries', 'arterial_tree')
    for source, name in [('superior_vena_cava', 'Superior vena cava'), ('inferior_vena_cava', 'Inferior vena cava')]:
        add(source, name, 'vein', source=source)

    section = 'liver'
    add('liver', 'Liver', 'organ', source='liver')
    pair('hepatic_lobe', 'hepatic lobe', 'liver_region')
    # The quick-report localisation uses a segment number. Segment I is the caudate.
    for n, roman in enumerate(('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'), start=1):
        add('liver_segment_' + str(n), 'Segment ' + roman + (' (caudate lobe)' if n == 1 else ''), 'functional_liver_region')

    section = 'gallbladder-pancreas-and-spleen'
    for name in ('gallbladder', 'pancreas', 'spleen'):
        add(name, name.capitalize(), 'organ', source=name)
    add('pancreatic_duct', 'Main pancreatic duct', 'duct')
    add('intrahepatic_ducts', 'Intrahepatic bile ducts', 'duct_system')
    add('common_hepatic_duct', 'Common hepatic duct', 'duct')
    add('common_bile_duct', 'Common bile duct', 'duct')
    section = 'adrenal-glands'
    pair('adrenal', 'adrenal gland', 'gland', 'adrenal_gland')
    section = 'kidneys-and-bladder'
    pair('kidney', 'kidney', 'organ', 'kidney')
    pair('collecting_system', 'renal collecting system', 'pelvicalyceal_system')
    add('urinary_bladder', 'Urinary bladder', 'organ', source='urinary_bladder')
    add('bladder_wall', 'Urinary bladder wall', 'organ_wall')
    section = 'bowel-and-peritoneum'
    for key, name, source in [('stomach', 'Stomach', 'stomach'), ('small_bowel', 'Small bowel', 'small_bowel'),
                              ('colon', 'Colon', 'colon'), ('rectum', 'Rectum', None)]:
        add(key, name, 'digestive_organ', source=source)
    add('peritoneal_surface', 'Peritoneal surfaces', 'serosal_membrane')
    add('peritoneal_cavity', 'Peritoneal cavity', 'potential_space')
    add('omentum', 'Omentum', 'peritoneal_fold')
    section = 'reproductive-organs'
    add('uterus', 'Uterus', 'organ')
    pair('adnexa', 'adnexa', 'adnexal_region')
    add('prostate', 'Prostate', 'gland', source='prostate')
    section = 'abdominal-and-pelvic-lymph-nodes'
    add('retroperitoneal_nodal_region', 'Retroperitoneal nodal regions', 'nodal_region')
    add('mesenteric_nodal_region', 'Mesenteric nodal regions', 'nodal_region')
    pair('pelvic_nodal_region', 'pelvic nodal regions', 'nodal_region')
    pair('inguinal_nodal_region', 'inguinal nodal region', 'nodal_region')
    section = 'bones'
    for prefix, count in [('T', 12), ('L', 5)]:
        for index in range(1, count + 1):
            level = prefix + str(index)
            add('vertebra_' + level.lower(), level + ' vertebra', 'vertebra', source='vertebrae_' + level)
    for number in range(1, 13):
        for side in ('right', 'left'):
            add(f'rib_{number}.{side}', f'{side.capitalize()} rib {number}', 'rib', side, f'rib_{side}_{number}')
    add('sacrum', 'Sacrum', 'bone', source='sacrum')
    add('sternum', 'Sternum', 'bone', source='sternum')
    pair('hip_bone', 'hip bone', 'bone', 'hip')
    pair('proximal_femur', 'proximal femur', 'bone_region')
    pair('proximal_humerus', 'proximal humerus', 'bone_region')
    return targets


# Each note describes the evidence needed for the actual reporting row.
NOTES = {
    'technique': 'Check body coverage, contrast administration, timing, reconstructions and any limitations against the acquisition. The template supplies example protocol wording.',
    'lungs-and-airways': 'Localise a pulmonary finding by lobe and record its measured size where applicable. Inspect the airway lumen and walls on the patient series.',
    'pleura-and-pericardium': 'Distinguish pleural and pericardial fluid. Record side, extent and surface abnormalities where visible.',
    'thoracic-lymph-nodes': 'Localise each relevant node to its actual region or station and record its short-axis dimension on the measured image.',
    'heart-and-great-vessels': 'Assess the visible heart, vessels and contrast opacification. A gross organ outline cannot establish luminal patency or exclude embolus.',
    'liver': 'Localise focal findings by lobe or segment. Use the acquired phases to describe attenuation and enhancement and the actual images for lesion size.',
    'gallbladder-pancreas-and-spleen': 'Assess organ parenchyma, ducts and gallbladder contents on the available phases. Body masks do not trace the duct lumina.',
    'adrenal-glands': 'Record the side of a finding and measure the lesion on the patient images.',
    'kidneys-and-bladder': 'Identify the affected side, inspect the collecting systems and assess the bladder wall with its degree of distension.',
    'bowel-and-peritoneum': 'Name the involved bowel segment and distinguish bowel wall, calibre, peritoneal surface, omental and fluid findings.',
    'reproductive-organs': 'Assess the organs actually present and visible. The source records a female participant but supplies no uterus or adnexal mask.',
    'abdominal-and-pelvic-lymph-nodes': 'Localise individual nodes, distinguish their nodal regions, and record actual short-axis measurements when indicated.',
    'bones': 'Inspect all acquired osseous structures in bone windows. Record the site, character and any associated fracture. Count levels against the patient’s anatomy and document variant or partial coverage.',
    'target-lesions': 'Identify the same lesions over time. Use the short axis for nodal targets and longest diameter for non-nodal targets. Assess target, non-target and new disease against the applicable baseline and nadir.',
}

COMPARISONS = {
    'liver': ('Eight liver segments on a separate source MRI', 'liver-regions-mri/index.html'),
    'gallbladder-pancreas-and-spleen': ('Biliary ducts in the BodyParts3D anatomical atlas', 'bp3d-biliary-4.3/index.html'),
    'thoracic-lymph-nodes': ('Mediastinal nodal annotations on chest CT 0571', 'lnq-case-0571/index.html'),
    'abdominal-and-pelvic-lymph-nodes': ('Pelvic nodes on the baseline CT of case 023', 'recist-pelvic-023/index.html'),
    'target-lesions': ('Published target measurements across three scans in case 023', 'recist-pelvic-023/comparison.html'),
}

GUIDANCE = [
    {'id': 'acr-thoracic-ct', 'url': 'https://gravitas.acr.org/PPTS/GetDocumentView?docId=13',
     'title': 'ACR practice parameter for thoracic CT', 'scope': 'Thoracic acquisition and documentation.'},
    {'id': 'acr-abdomen-pelvis-ct', 'url': 'https://gravitas.acr.org/PPTS/GetDocumentView?docId=168',
     'title': 'ACR practice parameter for abdominal and pelvic CT', 'scope': 'Abdominopelvic acquisition and documentation.'},
    {'id': 'recist-1.1', 'url': 'https://recist.eortc.org/recist-1-1/',
     'title': 'RECIST Working Group, version 1.1', 'scope': 'Target selection, measurement and longitudinal response in applicable solid-tumour studies.'},
]

def read(root, path):
    return json.loads((root / path).read_bytes())


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def field_kind(section, key):
    if section == 'technique':
        return 'examination_scope'
    if key == 'normal':
        return 'current_exam_assessment'
    if key == 'size':
        return 'measurement'
    return {'sum': 'aggregate_measurement', 'response': 'longitudinal_classification',
            'measurable': 'measurability_assessment', 'nature': 'characterisation'}.get(key, 'current_finding')


def build(root=ROOT):
    authored = read(root, AUTHOR)['investigations'][EXAM]
    fast = read(root, FAST)['templates'][EXAM]
    form, = [item for group in read(root, COMPILED)['forms'].values()
             for item in group['investigations'] if item['id'] == EXAM]
    sections = [row['id'] for row in authored['sections']]
    if (sections != list(NOTES) or sections != [row['anatomy_id'] for row in form['sections']]
            or [row['label'] for row in authored['sections'][1:]] != [row['heading'] for row in fast['sections']]):
        raise ValueError('Report anatomy rows changed between authored, compiled and quick reports')
    targets = anatomy()
    evidence = []
    rows = []
    for original, compiled in zip(authored['sections'], form['sections']):
        key = original['id']
        if [(f['id'], f['text']) for f in original['findings']] != [
                (f['id'].rsplit(':', 1)[1], f['text']) for f in compiled['findings']]:
            raise ValueError('Report fields changed in ' + key)
        report_fields = list(compiled['findings'])
        if original.get('normal') != (compiled['normal'] or {}).get('text'):
            raise ValueError('Normal assessment changed in ' + key)
        if compiled['normal']:
            report_fields.insert(0, compiled['normal'])
        for field in report_fields:
            fid = field['id'].rsplit(':', 1)[1]
            kind = field_kind(key, fid)
            record = dict(id=field['id'], source_section_id=key, name=field['label'], requirement_type=kind,
                          statement=field['text'], source_sha256=digest(field), required_representations=[],
                          requires_any=field.get('requires_any', []), slots=[
                              {k: s[k] for k in ('kind', 'source_token')} for s in field['slots']])
            if kind == 'measurement':
                record['unit'] = 'mm'
                record['axis'] = 'short_axis' if key.endswith('lymph-nodes') else 'not_specified_in_field'
            elif kind == 'aggregate_measurement':
                record.update(unit='mm', evidence=['individual_target_identity_and_size', 'applicable_measurement_axis'])
            elif kind == 'longitudinal_classification':
                record['evidence'] = ['comparable_exams', 'baseline_and_nadir', 'individual_targets',
                                      'non_target_disease', 'new_lesions', 'appropriate_response_criteria']
            evidence.append(record)
        quick = fast['technique'] if key == 'technique' else next(row for row in fast['sections'] if row['heading'] == original['label'])
        rows.append(dict(id=key, label=original['label'], section_sha256=digest(original), quick_report=quick,
                         source_field_ids=[f['id'] for f in report_fields],
                         anatomical_requirement_ids=[t['id'] for t in targets if t['source_section_id'] == key]))
    by_section = {row['id']: row for row in rows}
    for target in targets:
        target.update(requirement_type='anatomical_landmark', required_representations=list(KINDS),
                      report_provenance={'path': AUTHOR, 'section_sha256': by_section[target['source_section_id']]['section_sha256']})
    return dict(schema_version=1, schema='primer.typed-descriptor-requirements/1', investigation_id=EXAM,
                title=authored['title'], guide_id=authored['guide_id'], clinical_validation_status='unreviewed',
                clinical_approval=False, representation_completion_claim=False, sources=GUIDANCE,
                conventions={'scope': 'Named anatomy in the two CAP report formats, including field-of-view and patient-dependent regions. Variant levels, nodal stations and actual lesions require individual localisation.',
                             'segments': 'The quick report requests a liver segment. The eight functional regions include segment I as the caudate. Segment IV subdivisions require individual assessment.',
                             'sides': 'Paired anatomy is individually identified. Reproductive anatomy depends on the organs present.',
                             'evidence': 'Clinical findings, acquisition, measurements and response require the patient examination. Teaching sources provide partial anatomical examples.'},
                source_report={'author_path': AUTHOR, 'author_investigation_sha256': digest(authored), 'compiled_path': COMPILED,
                               'compiled_investigation_sha256': digest(form), 'fast_report_path': FAST,
                               'fast_report_sha256': digest(fast), 'source_section_ids': sections},
                sections=rows, anatomical_requirements=targets, evidence_requirements=evidence,
                counts={'anatomical_requirements': len(targets), 'representation_obligations': len(targets) * len(KINDS),
                        'typed_evidence_records': len(evidence),
                        'evidence_records_by_type': dict(sorted(Counter(r['requirement_type'] for r in evidence).items()))})


def references(inventory, root=ROOT):
    native = read(root, ATLAS + '/manifest.json')
    labels = {row['sourceLabel']: row for row in native['labels']}
    probes = {row['class']: row for row in read(root, VERIFIED)['probes']}
    areas = {row['id']: row for row in read(root, ATLAS + '/report-areas.json')[EXAM]}
    links = []
    for target in inventory['anatomical_requirements']:
        name = target['source_label']
        if name is None:
            continue
        area = target['source_section_id']
        label = labels[name]
        if name not in areas[area]['sourceLabels']:
            raise ValueError(f'{name} is outside {area}')
        if not label['voxelCount']:
            continue
        sample = probes[name]
        if (sample['position'] != label['focus'] or label['code'] not in sample['members'] or not label.get('mesh') or
                {s['axis'] for s in sample['sections']} != {0, 1, 2}):
            raise ValueError('No original CT, mask and surface probe for ' + name)
        for kind in KINDS:
            query = urlencode({'exam': EXAM, 'row': area, 'label': name, 'representation': kind})
            links.append(dict(investigation_id=EXAM, requirement_id=target['id'], representation=kind,
                              status='partial', source_id='ct-torso-s0028', source_label=name, side=target['laterality'],
                              anatomy_role=target['tissue_class'], focus=label['focus'], reaches_grid_edge=label['touchesGridEdge'],
                              ct_sample_sha256=native['ctSampleSHA256'], mask_sha256=label['sourceSHA256'],
                              surface_sha256=label['mesh']['sha256'] if kind == 'model' else None,
                              complete_extent=False, current_patient_registration=False, clinical_approval=False,
                              href='/app/anatomy/ct-torso-s0028/index.html?' + query + '#' + ANCHORS[kind]))
    return links + liver_segment_links(inventory, root)


def liver_segment_links(inventory, root=ROOT):
    """Select the largest acquired cross-section for each released MRI region."""
    directory = root / 'web/anatomy/liver-regions-mri'
    metadata = read(directory, 'volume.json')
    surfaces = {s['label']: s for s in read(directory, 'surfaces.json')}
    targets = {t['id']: t for t in inventory['anatomical_requirements']}
    expected = {'liver_segment_' + str(n): n for n in range(1, 9)}
    if metadata['labels'] != dict(background=0, **expected):
        raise ValueError('Unexpected source MRI region identities')
    width, height, depth = metadata['shape']
    area = width * height
    section_counts = {n: [] for n in surfaces}
    mask_digest = hashlib.sha256()
    for chunk in metadata['chunks']:
        source = chunk['labels']
        buf = gzip.decompress((directory / source['file']).read_bytes())
        if (len(buf) != chunk['slices'] * area or chunk['firstSlice'] != len(section_counts[1])
                or hashlib.sha256(buf).hexdigest() != source['sha256']):
            raise ValueError('MRI segment array differs from its original layout')
        mask_digest.update(buf)
        for offset in range(0, len(buf), area):
            section = buf[offset:offset + area]
            for n in section_counts:
                section_counts[n].append(section.count(n))
    if mask_digest.hexdigest() != metadata['decodedMaskSHA256'] or len(section_counts[1]) != depth:
        raise ValueError('MRI segment volume differs from published source samples')
    links = []
    for name, n in expected.items():
        r = surfaces[n]
        target = targets['cap.' + name]
        counts = section_counts[n]
        if (target['tissue_class'] != 'functional_liver_region' or target['source_section_id'] != 'liver'
                or sum(counts) != r['sourceVoxels'] or not max(counts)):
            raise ValueError('Source region or voxel count differs from the liver target')
        section = counts.index(max(counts))
        for kind, anchor in [('schematic', 'image-region'), ('model', 'surface')]:
            query = urlencode({'from': EXAM, 'region': n, 'slice': section, 'representation': kind})
            links.append(dict(investigation_id=EXAM, requirement_id=target['id'], representation=kind,
                status='partial', source_id='liver-regions-mri', source_case=metadata['selectedCase'],
                source_modality='MRI', source_label=name, side=target['laterality'], anatomy_role=target['tissue_class'],
                mask_sha256=metadata['decodedMaskSHA256'], surface_decoded_sha256=r['sha256'] if kind == 'model' else None,
                source_voxels=r['sourceVoxels'], slice_index=section, source_section_pixels=counts[section],
                complete_extent=False, clinical_approval=False, current_patient_registration=False,
                href='/app/anatomy/liver-regions-mri/index.html?' + query + '#' + anchor))
    return links


def viewer_guide(inventory, links, root=ROOT):
    labels = {row['sourceLabel']: row for row in read(root, ATLAS + '/manifest.json')['labels']}
    views = {}
    comparisons = {}
    for link in links:
        destination = comparisons if link['source_id'] == 'liver-regions-mri' else views
        destination.setdefault(link['requirement_id'], {})[link['representation']] = link['href']
    guide = {}
    for section in inventory['sections']:
        key = section['id']
        targets = []
        for t in inventory['anatomical_requirements']:
            if t['source_section_id'] != key:
                continue
            obj = labels.get(t['source_label'])
            state = ('unlabelled' if obj is None else 'empty' if not obj['voxelCount']
                     else 'reaches_edge' if obj['touchesGridEdge'] else 'labelled')
            target = dict(name=t['name'], sourceLabel=t['source_label'], state=state, links=views.get(t['id'], {}))
            if t['id'] in comparisons:
                target['separateMRI'] = comparisons[t['id']]
            targets.append(target)
        guide[key] = dict(note=NOTES[key], targets=targets)
        if key == 'technique':
            guide[key]['guidance'] = GUIDANCE[:2]
        elif key == 'target-lesions':
            guide[key]['guidance'] = [GUIDANCE[2]]
        if key in COMPARISONS:
            title, path = COMPARISONS[key]
            if not (root / 'web/anatomy' / path).is_file():
                raise ValueError('Missing comparison ' + path)
            guide[key]['comparison'] = {'title': title, 'href': '/app/anatomy/' + path}
    return guide


def validate(data, root=ROOT):
    if data != build(root):
        raise ValueError('CAP inventory differs from the current report or reviewed anatomical targets')
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    inv = build()
    links = references(inv)
    for name, value in [(OUTPUT, inv), (GUIDE, viewer_guide(inv, links))]:
        file = ROOT / name
        if args.write:
            file.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
        elif read(ROOT, name) != value:
            raise SystemExit('Regenerate ' + name)
    print(inv['counts'], len(links), 'partial source links')
