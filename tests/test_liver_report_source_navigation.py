"""The three protocol-specific liver reports retain each source's boundaries and modality."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import parse_qs, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMS = ['ct.liver-mass', 'ct.liver-lirads', 'ct.liver-lirads-calculated']


@pytest.fixture(scope='module')
def published():
    forms = json.loads((ROOT/'data/radiology/descriptor-reporting.json').read_bytes())['forms']
    rows = {i['id']: [s['anatomy_id'] for s in i['sections']] for f in forms.values() for i in f['investigations'] if i['id'] in EXAMS}
    # Run the same module called by the normal report renderer.
    script = """
import fs from 'node:fs';
import {sourcesFor} from './web/radiology/liver-report-sources.mjs';
const forms = JSON.parse(fs.readFileSync(0));
console.log(JSON.stringify(Object.fromEntries(Object.entries(forms).map(([exam, rows]) =>
  [exam,Object.fromEntries(rows.map(id => [id,sourcesFor(exam,id)]))]))));
"""
    return json.loads(subprocess.run(['node','--input-type=module','--eval',script], cwd=ROOT, input=json.dumps(rows),
                                     capture_output=True, text=True, check=True).stdout)


def test_only_the_reviewed_report_rows_open_sources(published):
    assert set(published) == set(EXAMS)
    for exam, rows in published.items():
        assert len(rows) == 31
        assert {key for key,value in rows.items() if value is None} == {
            'nodes-porta-hepatis','nodes-portacaval','nodes-coeliac','nodes-para-aortic','free-fluid','free-gas'}
        for key, item in rows.items():
            if not item: continue
            assert item['links'] and item['note']
            for link in item['links']:
                url = urlsplit(link['href'])
                assert url.path.startswith('/app/anatomy/') and not url.netloc and not url.scheme
                assert (ROOT/'web'/url.path.removeprefix('/app/')).is_file()
                if url.query:
                    key = 'exam' if '/medseg-liver-001/' in url.path else 'from'
                    assert parse_qs(url.query)[key] == [exam]


def test_mri_segment_iv_is_retained_as_a_whole_region(published):
    areas = {'i': (1,44), 'ii': (2,52), 'iii': (3,49), 'iva': (4,52), 'ivb': (4,52),
             'v': (5,48), 'vi': (6,48), 'vii': (7,49), 'viii': (8,50)}
    for num, (region,section) in areas.items():
        item = published[EXAMS[0]]['segment-'+num]
        mr = [urlsplit(link['href']) for link in item['links'] if '/liver-regions-mri/' in link['href']]
        assert len(mr) == 2
        for url in mr:
            params = parse_qs(url.query)
            assert url.path == '/app/anatomy/liver-regions-mri/index.html'
            assert params['slice'] == [str(section)] and params['region'] == [str(region)]
        if num in ('iva','ivb'):
            assert 'labels segment IV as one region' in item['note']


def test_vessel_system_focus_reproduces_source_segmentation_and_bile_duct_part():
    directory = ROOT/'web/anatomy/hva-ct-318'
    metadata = json.loads((directory/'volume.json').read_bytes())
    counts = {1:[], 2:[]}
    cells = metadata['shape'][0] * metadata['shape'][1]
    for chunk in metadata['chunks']:
        source = chunk['labels']
        raw = gzip.decompress((directory/source['file']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == source['sha256']
        for offset in range(0,len(raw),cells):
            for code in counts:
                counts[code].append(raw[offset:offset+cells].count(code))
    assert [(x.index(max(x)),sum(x)) for x in counts.values()] == [(98,94370),(121,155702)]
    atlas = ROOT/'web/anatomy/bp3d-biliary-4.3'
    surfaces = json.loads((atlas/'surfaces.json').read_bytes())
    page = (atlas/'index.html').read_text()
    assert page.count('class="layer"') == len(surfaces)
    shared = [row for row in surfaces if row['label'] == 'FJ3079']
    assert {row['sourcePart']['structure'] for row in shared} == {'common bile duct','common hepatic duct'}
    assert "['common-bile', ['FJ3079-common-bile']]" in (atlas/'surface-viewer.js').read_text()


def test_three_ct_liver_reports_open_the_native_segment_in_all_three_views(published):
    segments = {'i':'1','ii':'2','iii':'3','iva':'4a','ivb':'4b','v':'5','vi':'6','vii':'7','viii':'8'}
    for exam, rows in published.items():
        for number, segment in segments.items():
            links = [urlsplit(link['href']) for link in rows['segment-' + number]['links']
                     if '/medseg-liver-001/' in link['href']]
            assert len(links) == 3 and {url.fragment for url in links} == {'ct','map','surface'}
            for url in links:
                display = {'ct':'raw','map':'map','surface':'outline'}[url.fragment]
                assert parse_qs(url.query) == {'exam':[exam], 'segment':[segment], 'plane':['ij'],
                                               'display':[display], 'focus':['label']}
