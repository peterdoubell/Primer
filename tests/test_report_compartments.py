"""Presentation changes must retain every authored observation and constraint."""
import copy
import gzip
import json
from pathlib import Path
from tools.report_compartments import apply_compartments
from tools.build_descriptor_reporting import digest

ROOT = Path(__file__).resolve().parents[1]
OLD = '9ab4c575a5d1915788d21f278bafed5873308c36cfb3ee74c49cba8a24c1d8d2'


def catalog():
    return json.loads(gzip.decompress((ROOT/'data/radiology/descriptor-reporting.json.gz').read_bytes()))


def test_every_structure_has_one_compartment_and_all_clinical_content_is_preserved():
    previous = json.loads(gzip.decompress((ROOT/f'data/radiology/descriptor-history/{OLD}.json.gz').read_bytes()))
    current = catalog()
    count = 0
    for guide, form in current['forms'].items():
        old_exams = {e['id']: e for e in previous['forms'][guide]['investigations']}
        for exam in form['investigations']:
            old = {s['id']: s for s in old_exams[exam['id']]['sections']}
            rows = {s['id']: s for s in exam['sections']}
            assert rows.keys() == old.keys()
            membership = [key for c in exam['compartments'] for key in c['section_ids']]
            assert len(membership) == len(set(membership)) == len(rows)
            assert set(membership) == set(rows)
            for key, section in rows.items():
                assert section['compartment']
                assert {k:v for k,v in section.items() if k not in ('compartment','report_section_id','report_section_label')} == {k:v for k,v in old[key].items() if k not in ('report_section_id','report_section_label')}
            count += 1
    assert count == 225


def test_knee_compartments_join_related_tissues_and_keep_patella_out_of_medial_compartment():
    exam = next(e for f in catalog()['forms'].values() for e in f['investigations'] if e['id']=='ra.mri-knee')
    rows = {s['anatomy_id']:s['compartment'] for s in exam['sections']}
    assert {rows[k] for k in ('medial-meniscus-body','medial-femoral-cartilage','mcl-superficial','medial-femoral-bone','pes-bursa')} == {'Medial compartment'}
    assert rows['patellar-medial-cartilage'] == rows['mpfl'] == rows['quadriceps'] == 'Patellofemoral compartment'
    assert rows['lcl'] == rows['lateral-meniscus-body'] == rows['lateral-tibial-cartilage']
    assert rows['acl'] == rows['pcl'] == 'Intercondylar compartment'
    assert rows['baker-cyst'] == 'Posterior compartment'


def test_compartment_compilation_is_idempotent_and_does_not_change_ids():
    forms = copy.deepcopy(catalog()['forms'])
    before = copy.deepcopy(forms)
    apply_compartments(forms,digest)
    assert forms == before
