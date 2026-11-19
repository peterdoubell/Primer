"""One house style across every report template (tools/authoring/report_style_20261113.py)."""
import collections
import json
import re
from pathlib import Path

from primer import report_templates as rt

ROOT = Path(__file__).resolve().parents[1]
PRISM = json.loads((ROOT / 'data/radiology/prism-titles.json').read_text())
MODALITY = {
    'CT': r'\bCT\b|\bHRCT\b',
    'MRI': r'\bMRI?\b|\bMRA\b|\bMRCP\b|\bMR\b|STIR|FLAIR|gadolinium',
    'US': r'ultrasound|sonograph|duplex|Doppler|transducer|echocardiogra',
    'XR': r'(?<!correlated with )radiograph',
}


def modalities(text):
    return {m for m, p in MODALITY.items() if re.search(p, text, re.I)}


def test_titles_are_unique_and_name_one_modality():
    library = rt.library()
    counts = collections.Counter(item['title'] for item in library.values())
    assert [t for t, n in counts.items() if n > 1] == []
    for identifier, item in library.items():
        assert len(modalities(item['title'])) <= 1, (identifier, item['title'])


def test_technique_describes_the_examination_s_own_modality():
    for identifier, item in rt.library().items():
        title = modalities(item['title'])
        if 'technique' not in item or not title:
            continue
        for text in [item['technique']['normal'], *item['technique'].get('options', [])]:
            assert not (modalities(text) - title), (identifier, text)


def test_every_performed_study_has_prism_titles_owned_once():
    library = rt.library()
    excluded = set(PRISM['not_performed_studies'])
    assert excluded <= set(library)
    seen = set()
    for identifier in library:
        if identifier in excluded:
            continue
        titles = PRISM['titles'].get(identifier)
        assert titles, identifier
        for title in titles:
            assert title.lower() not in seen and ',' not in title, title
            seen.add(title.lower())


def test_normal_lines_are_terse_full_sentences():
    for identifier, item in rt.library().items():
        for section in item['sections']:
            normal = section['normal']
            assert normal[0].isupper() and normal.endswith('.'), (identifier, normal)
            assert not re.search(r'on the acquired images|\b(?:is|are) (?:identified|seen)\b', normal), (identifier, normal)


# ---- 2026-11-15 upgrade: density, search order and rapid reporting (tools/authoring/report_upgrade_20261115.py)

def _mri_or_ct(title):
    return bool(re.search(r'\bCT\b|\bHRCT\b|\bMRI?\b|\bMRCP\b', title))


def test_every_mri_and_ct_has_its_own_acquisition_and_nothing_else_does():
    for identifier, item in rt.library().items():
        heading = rt.acquisition_heading(identifier, item)
        report = rt.quick_report(identifier)
        if identifier in rt.NOT_ACQUIRED or not _mri_or_ct(item['title']):
            assert heading is None, identifier
            assert not {'Technique', 'Protocol'} & set(report['headings']), identifier
            continue
        assert heading == ('Technique' if re.search(r'\bCT\b|\bHRCT\b', item['title']) else 'Protocol'), identifier
        protocol = item['technique']['normal']
        # States what was acquired: planes and weightings, or phases, not just the study name again.
        assert re.search(r'T1|T2|STIR|FLAIR|DWI|PD|cine|angiogram|phase|Unenhanced|unenhanced|contrast|CT|PET', protocol), (identifier, protocol)
        assert len(protocol) <= 165, (identifier, len(protocol))
        assert 'prescribed' not in protocol and 'the named' not in protocol and 'requested' not in protocol, (identifier, protocol)
        if re.search(r'with contrast', item['title']) and heading == 'Protocol':
            assert 'gadolinium' in ' '.join([protocol, *item['technique'].get('options', [])]), (identifier, protocol)


def test_the_normal_line_does_not_repeat_its_heading():
    def stems(text):
        return {w.lower().rstrip('s') for w in re.findall(r"[A-Za-z']+", text)} - {'and', 'the', 'of', 'or', 'both', 'visualised', 'a', 'an'}
    for identifier, item in rt.library().items():
        for section in item['sections']:
            first = section['normal'].split('. ')[0].rstrip('.')
            lead, _, tail = first.partition(' ')
            assert not (lead in {'Normal', 'Intact', 'Patent', 'Clear', 'No', 'Preserved'} and tail
                        and stems(tail) == stems(section['heading'])), (identifier, section['heading'], section['normal'])


def test_no_generic_other_findings_section():
    for identifier, item in rt.library().items():
        for section in item['sections']:
            assert section['heading'].lower() not in {'other findings', 'other'}, identifier
            assert 'No other significant finding' not in section['normal'], (identifier, section['heading'])


def test_finding_lines_start_with_the_finding_and_stay_scannable():
    for identifier, item in rt.library().items():
        for section in item['sections']:
            for option in section.get('options', []):
                where = (identifier, section['heading'], option)
                # A line may be only blanks; otherwise it names the finding before any blank.
                assert not option.startswith('[ ]') or not re.sub(r'[\[\] .:]', '', option), where
                assert len(option) <= 145, where
                picks = [pick[1:-1].split(' / ') for pick in re.findall(r'\[[^\]]* / [^\]]*\]', option)]
                assert len(picks) <= 3, where
                # Six choices at most, except coded scales such as BI-RADS or AO Spine.
                assert all(len(choices) <= 6 or all(len(choice) <= 4 for choice in choices) for choices in picks), where


def test_radproof_export_keeps_every_normal_line_self_contained():
    import sys
    sys.path.insert(0, str(ROOT / 'tools' / 'authoring'))
    import radproof_export
    library = rt.library()
    for template in radproof_export.export():
        lines = template['text'].split('\n')
        heading = rt.acquisition_heading(template['id'], library[template['id']])
        assert ('__Protocol:__' in lines) == (heading == 'Protocol'), template['id']
        assert ('__Technique:__' in lines) == (heading == 'Technique'), template['id']
        if template['id'] not in radproof_export.MULTI_REGION:
            assert not radproof_export.BARE & set(lines), template['id']


# ---- 2026-11-16: radiographs as Prism titles and reports them (tools/authoring/radiograph_titles_20261116.py)

def test_radiograph_prism_titles_name_the_region_not_the_modality():
    import sys
    sys.path.insert(0, str(ROOT / 'tools' / 'authoring'))
    import radproof_export
    library = rt.library()
    for identifier, titles in PRISM['titles'].items():
        if radproof_export.is_radiograph(identifier, library[identifier]):
            for title in titles:
                assert not re.search(r'x-?ray|radiograph|\bxr\b', title, re.I), (identifier, title)


def test_radiographs_have_findings_under_the_title_and_count_their_views():
    import sys
    sys.path.insert(0, str(ROOT / 'tools' / 'authoring'))
    import radproof_export
    exported = {t['id']: t['text'].split('\n') for t in radproof_export.export()}
    knee = exported['xr.knee']
    # Clinical history and comparison open every template; the study title follows in Prism's capitals.
    assert knee[:7] == ['__Clinical history:__', '[]', '', '__Comparison:__', '[]', '', '**__{SIDE} KNEE RADIOGRAPH{S}:__**']
    assert knee[7] == 'No fracture.'
    assert '__Findings:__' not in knee and knee[-1] == 'Normal knee radiograph{s}.'
    assert '**__CHEST RADIOGRAPH{S}:__**' in exported['ra.chest-radiography']
    assert '__Findings:__' in exported['ct.trauma-panscan']


def test_3d_uterus_is_reported_in_the_pelvic_ultrasound():
    assert 'us.uterus-3d' in PRISM['not_performed_studies'] and 'us.uterus-3d' not in PRISM['titles']
    assert '3D ultrasound uterus' in PRISM['titles']['ra.ultrasound-acute-gynaecology']


# ---- 2026-11-17: one standard for conclusions, lines and spelling (tools/authoring/report_uniformity_20261117.py)

def _export():
    import sys
    sys.path.insert(0, str(ROOT / 'tools' / 'authoring'))
    import radproof_export
    return radproof_export


def _performed():
    excluded = set(PRISM['not_performed_studies'])
    return {identifier: item for identifier, item in rt.library().items() if identifier not in excluded}


def test_a_normal_conclusion_names_the_study_not_an_organ():
    rx = _export()
    for identifier, item in _performed().items():
        impression = item['impression'] if isinstance(item['impression'], str) else ' '.join(item['impression'])
        title = rx.VIEWS.sub('', rx.study_title(item['title'])).replace('{Side} ', '').replace('{side} ', '')
        if not impression.startswith('Normal ') or ',' in title or identifier == 'dxa.bone-densitometry':
            continue  # a study with an indication concludes with what it excludes or finds
        study = rx.lower_first(re.sub(r' with(?:out)?(?: oral)? contrast$', '', title))
        assert impression.replace('radiographs', 'radiograph') == f'Normal {study}.'.replace('radiographs', 'radiograph'), (identifier, impression)


def test_every_normal_sentence_names_its_subject():
    attributes = set('''normal size echotexture signal calibre thickness stratification enhancement contour wall flow
        compressible fully spontaneous phasic opacification mucosa outline morphology and with including stable'''.split())
    for identifier, item in _performed().items():
        for section in item['sections']:
            for sentence in re.split(r'(?<=\.)\s+(?=[A-Z])', section['normal']):
                words = re.findall(r'[a-z]+', sentence.lower())
                assert sentence in {'Normal.', 'Stable.'} or set(words) - attributes, (identifier, sentence)
                assert not re.match(r'Normal, including', sentence), (identifier, sentence)


def test_one_spelling_for_one_term():
    variants = re.compile(r'Baker cyst|radio-opaque|runoff|bony abnormality|fat-suppressed|Informed consent\.')
    for identifier, item in rt.library().items():
        assert not variants.search(json.dumps(item, ensure_ascii=False)), identifier
        if rt.acquisition_heading(identifier, item) == 'Protocol':
            assert not re.search(r'\bDWI(?! with ADC| neurography)', item['technique']['normal']), identifier


def test_exported_normal_reports_are_flat_self_contained_and_say_nothing_twice():
    rx = _export()
    library = rt.library()
    for template in rx.export():
        lines = template['text'].split('\n')
        if template['id'] in rx.MULTI_REGION:
            continue
        # Clinical history, comparison and the study title come first.
        findings = [line for line in lines[len(rx.HISTORY) + 1:lines.index('**__Conclusion:__**')] if line and not line.startswith('__')]
        if rt.acquisition_heading(template['id'], library[template['id']]):
            findings = findings[1:]  # the protocol line
        assert len(findings) == len(set(findings)), (template['id'], findings)
        for line in findings:
            # No "Spleen: normal." labels and no stage or category restating the conclusion.
            assert not re.search(r': (?:normal|none|clear|intact|patent|preserved|not involved)\.$', line), (template['id'], line)
            assert not re.search(r' to (?:stage|classify|score)\.$|^[A-Z]{1,3}-RADS \d', line), (template['id'], line)
    exported = {template['id']: template['text'] for template in rx.export()}
    assert 'Normal pancreas.\nNormal spleen.\nNormal adrenal glands.' in exported['ra.acute-abdomen']
    assert 'Right carotid: no plaque or stenosis.\nLeft carotid: no plaque or stenosis.' in exported['ra.carotid-obstruction']
    assert exported['ra.ultrasound-breast'].split('\n')[len(rx.HISTORY)] == '**__ULTRASOUND BREAST:__**'  # right, left or both
    assert 'BI-RADS 1' not in exported['ra.mammography'].split('**__Conclusion:__**')[0]
