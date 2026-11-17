"""Build per-structure source locators for the radiology reporting inventories.

A locator says where a named reportable structure is shown or labelled in a
named external source. It is a reading aid, never an asset binding: it does not
count towards structure coverage and makes no fidelity claim.

Sources, as directed by the project owner on 2026-11-16:
  * musculoskeletal: the Stanford MSK MRI Atlas at xrayhead.com (Bao Do MD);
  * everything else: Radiology Assistant articles already cited by the
    requirement itself.

Nothing is copied from either site. For the atlas only the label name and the
plane and slice numbers on which it appears are recorded. For Radiology
Assistant only the section anchor, section heading and the address of the
publisher's own figure are recorded.

Usage: python tools/anatomy_sources/build_structure_source_locators.py
Downloaded pages are kept in a fixed folder under the system temporary directory,
so a rebuild does not refetch them.
"""
import hashlib
import html
import json
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'web/radiology/structure-atlas'
ATLAS = 'https://xrayhead.com/theatlas.php?id='
ATLAS_REGIONS = ('ankle', 'elbow', 'hip', 'knee', 'lower_leg', 'shoulder', 'thigh', 'wrist')
RETRIEVED = '2026-11-16'

# Atlas regions that show the anatomy of each musculoskeletal investigation.
REGIONS = {
    'ra.mri-ankle': ['ankle', 'lower_leg'], 'ra.ankle-fractures': ['ankle'],
    'ra.foot-ankle-cases': ['ankle'], 'ra.mri-diabetic-foot': ['ankle'],
    'ra.mri-elbow': ['elbow'], 'ra.paediatric-elbow-fractures': ['elbow'],
    'ra.hip-fai': ['hip'], 'ra.paediatric-hip': ['hip'], 'ra.mri-knee': ['knee'],
    'ra.mri-hamstring': ['thigh', 'hip', 'knee'], 'ra.mri-shoulder': ['shoulder'],
    'ra.ultrasound-shoulder': ['shoulder'], 'ra.wrist-instability': ['wrist'],
    'ra.wrist-fractures': ['wrist'],
    'ra.stress-fractures': ['hip', 'knee', 'lower_leg', 'ankle'],
}

# Reviewed by hand against the atlas label lists. 'same' is another name for the
# same structure; 'part' means the atlas labels only named parts of it.
ALIASES = {
    'ankle': {
        'distal tibia': ('part', ['tibia', 'medial malleolus']),
        'talus': ('part', ['body of talus', 'head of talus', 'neck of talus',
                           'lateral process of talus', 'posterior process of talus']),
        'anterior inferior tibiofibular ligament': ('same', ['anterior tibiofibular ligament']),
        'posterior inferior tibiofibular ligament': ('same', ['posterior tibiofibular ligament']),
        'deltoid ligament': ('part', ['deep deltoid ligament of ankle']),
        'spring ligament complex': ('part', ['spring ligament superomedial bundle']),
        'plantar fascia': ('part', ['medial bundle of plantar fascia']),
        'posterior tibial tendon': ('same', ['tendon of tibialis posterior']),
        'fibularis longus tendon': ('same', ['tendon of peroneus longus']),
        'fibularis brevis tendon': ('same', ['tendon of peroneus brevis']),
        'extensor digitorum longus tendon': ('same', ['extensor digitorum longus tendon of foot']),
        'sinus tarsi fat': ('same', ['sinus tarsi']),
        'subtalar joint': ('part', ['posterior subtalar joint', 'middle subtalar joint',
                                    'anterior subtalar joint']),
        'metatarsal 1': ('same', ['first metatarsal']),
        'metatarsal 5': ('part', ['base of 5th metatarsal']),
    },
    'elbow': {
        'distal biceps tendon': ('same', ['distal tendon of biceps brachii']),
        'lacertus fibrosus': ('same', ['lacertus fibrosis']),
        'ulnar collateral ligament': ('same', ['medial collateral ligament of elbow joint']),
        'radial collateral ligament': ('same', ['radial collateral ligament of elbow']),
        'annular ligament': ('same', ['annular ligament of radius']),
        'biceps muscle': ('same', ['biceps brachii muscle']),
        'anconeus muscle': ('same', ['anconeus']),
        'extensor digitorum muscle': ('same', ['extensor digitorum']),
        'proximal ulna': ('part', ['olecranon', 'coronoid process of ulna']),
        'proximal radius': ('part', ['radial head', 'radial tuberosity']),
        'distal humerus': ('part', ['capitellum', 'trochlea', 'medial epicondyle of humerus',
                                    'lateral epicondyle of humerus']),
    },
    'hip': {
        'iliopsoas muscle': ('same', ['iliopsoas']),
        'proximal hamstring tendons': ('same', ['hamstring tendon']),
        'proximal femur': ('part', ['greater trochanter of femur', 'lesser trochanter of femur',
                                    'calcar femoralis']),
    },
    'knee': {
        'medial collateral ligament': ('same', ['medial collateral ligament of knee']),
        'meniscofemoral ligaments': ('part', ['ligament of wrisberg']),
        'gracilis tendon': ('same', ['gracilis tendon of distal thigh']),
        'medial gastrocnemius muscle': ('same', ['medial head of gastrocnemius muscle']),
        'lateral gastrocnemius muscle': ('same', ['lateral head of gastrocnemius muscle']),
        'common fibular nerve': ('same', ['common peroneal nerve']),
        'popliteal artery': ('part', ['popliteal vessels']),
        'popliteal vein': ('part', ['popliteal vessels']),
        'distal femur': ('part', ['medial condyle of femur', 'lateral condyle of femur']),
        'proximal tibia': ('part', ['medial tibial plateau', 'lateral tibial plateau',
                                    'tibial tuberosity', 'gerdy tubercle']),
        'proximal fibula': ('part', ['head of fibula', 'styloid process of fibular head']),
        'biceps femoris long-head muscle': ('same', ['long head of biceps femoris muscle']),
        'biceps femoris short-head muscle': ('same', ['short head of biceps femoris muscle']),
    },
    'thigh': {
        'biceps femoris long-head muscle': ('same', ['biceps femoris (long head)']),
        'biceps femoris short-head muscle': ('same', ['biceps femoris (short head)']),
        'semimembranosus muscle': ('same', ['semimembranosus']),
    },
    'shoulder': {
        'long head biceps tendon': ('same', ['tendon of long head of biceps brachii']),
        'inferior glenohumeral ligament complex': (
            'part', ['anterior band of inferior glenohumeral ligament',
                     'axillary pouch of inferior glenohumeral ligament']),
        'distal clavicle': ('part', ['clavicle']),
        'coracoclavicular ligament': ('part', ['conoid ligament', 'trapezoid ligament']),
        'posterior glenoid labrum': ('same', ['posterior labrum']),
        'scapula': ('part', ['acromion', 'coracoid process', 'glenoid']),
        'proximal humerus': ('part', ['greater tuberosity of humerus', 'lesser tuberosity of humerus']),
    },
    'wrist': {
        'scapholunate interosseous ligament': ('same', ['scapholunate ligament']),
        'lunotriquetral interosseous ligament': ('same', ['lunotriquetral ligament']),
        'distal radius': ('part', ['radial styloid', 'lunate fossa of radius', 'sigmoid notch of radius']),
    },
    'lower_leg': {},
}


def fetch(url, cache):
    path = cache / (hashlib.sha256(url.encode()).hexdigest()[:24] + '.html')
    if not path.is_file():
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                path.write_bytes(response.read())
        except Exception as error:  # A missing article leaves the structure without a locator.
            print('skipped', url, error, file=sys.stderr)
            path.write_bytes(b'')
    return path.read_text(encoding='utf-8', errors='replace')


def atlas_labels(page):
    body = re.search(r'function putlabels\(\)(.*?)function showlabels', page, re.S)
    labels = {}
    if not body:
        return labels
    for plane, block in re.findall(r'if \(plane == "(\w+)"\)\s*\{(.*?)(?=if \(plane ==|\Z)', body.group(1), re.S):
        for image, name in re.findall(r'currentimage==(\d+)\)\{showlabels\("([^"]+)"', block):
            labels.setdefault(name.strip().lower(), {}).setdefault(plane, set()).add(int(image))
    return {name: {plane: sorted(images) for plane, images in sorted(planes.items())}
            for name, planes in sorted(labels.items())}


def plain(name):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', name.lower())).strip()


def atlas_locator(name, regions, labels):
    key = plain(name)
    for region in regions:
        index = {plain(label): label for label in labels[region]}
        if key in index:
            return {'region': region, 'match': 'same_name', 'labels': [index[key]]}
    for region in regions:
        alias = ALIASES[region].get(name.lower())
        if alias:
            return {'region': region, 'match': {'same': 'reviewed_synonym', 'part': 'named_parts_only'}[alias[0]],
                    'labels': alias[1]}
    return None


BLOCK = re.compile(r'<section class="bblok.*?</section>', re.S)
TAG = re.compile(r'<[^>]+>')


def article_blocks(page):
    """Each illustrated section, filed under the nearest heading that has an anchor."""
    blocks, anchor, title = [], None, ''
    for match in re.finditer(r'<h[23] id="([^"]+)"[^>]*>(.*?)</h[23]>|<section class="bblok.*?</section>', page, re.S):
        if match.group(1):
            anchor, title = match.group(1), html.unescape(TAG.sub('', match.group(2))).strip()
        block = match.group(0)
        if not block.startswith('<section'):
            continue
        heading = re.search(r'<h3 id="([^"]+)"[^>]*>(.*?)</h3>', block, re.S)
        if heading:
            anchor, title = heading.group(1), html.unescape(TAG.sub('', heading.group(2))).strip()
        if not anchor:
            continue
        images = re.findall(r'<img src="(/assets/[^"]+)"', block)
        blocks.append({'anchor': anchor, 'heading': title, 'images': images[:1],
                       'text': ' ' + plain(html.unescape(TAG.sub(' ', block))) + ' '})
    return blocks


def source_locators(name, articles):
    key = plain(re.sub(r'^(right|left|bilateral|each imaged|each examined|named|visible)\s+', '', name, flags=re.I))
    if len(key) < 5:
        return []
    found = []
    for url, blocks in articles:
        for block in blocks:
            in_heading = (' ' + key + ' ') in (' ' + plain(block['heading']) + ' ')
            if in_heading or (' ' + key + ' ') in block['text']:
                found.append((0 if in_heading else 1, 0 if block['images'] else 1, len(found),
                              {'url': url + '#' + block['anchor'], 'heading': block['heading'],
                               'named_in': 'heading' if in_heading else 'text',
                               **({'figure': 'https://radiologyassistant.nl' + block['images'][0]} if block['images'] else {})}))
    return [entry[3] for entry in sorted(found, key=lambda entry: entry[:3])[:3]]


def main(cache):
    cache.mkdir(parents=True, exist_ok=True)
    labels = {region: atlas_labels(fetch(ATLAS + region, cache)) for region in ATLAS_REGIONS}
    index, totals = [], {'requirements': 0, 'atlas': 0, 'radiology_assistant': 0, 'either': 0}
    (OUT / 'locators').mkdir(parents=True, exist_ok=True)
    for old in (OUT / 'locators').glob('*.json'):
        old.unlink()
    for name in ('msk', 'non-msk'):
        data = json.loads((ROOT / 'data/radiology' / (name + '-structure-requirements.json')).read_text())
        for investigation in data['investigations']:
            identifier = investigation['investigation_id']
            urls = sorted({url for structure in investigation['structures'] for url in structure.get('source_urls') or []
                           if url.startswith('https://radiologyassistant.nl/')})
            articles = [(url, article_blocks(fetch(url, cache))) for url in urls]
            regions = REGIONS.get(identifier, [])
            rows, counts = [], {'requirements': 0, 'atlas': 0, 'radiology_assistant': 0, 'either': 0}
            for structure in investigation['structures']:
                row = {'id': structure['id'], 'name': structure['name']}
                atlas = atlas_locator(structure['name'], regions, labels) if regions else None
                if atlas:
                    atlas['in_requirement_modality_scope'] = 'MRI' in (structure.get('modality_scope') or [])
                    row['atlas'] = atlas
                sources = source_locators(structure['name'], articles)
                if sources:
                    row['radiology_assistant'] = sources
                counts['requirements'] += 1
                counts['atlas'] += bool(atlas)
                counts['radiology_assistant'] += bool(sources)
                counts['either'] += bool(atlas or sources)
                rows.append(row)
            for key, value in counts.items():
                totals[key] += value
            slug = identifier.replace('ra.', '')
            (OUT / 'locators' / (slug + '.json')).write_text(json.dumps(
                {'investigation_id': identifier, 'atlas_regions': regions, 'articles': urls, 'counts': counts,
                 'structures': rows}, indent=1, sort_keys=True) + '\n')
            index.append({'investigation_id': identifier, 'file': 'locators/' + slug + '.json', **counts})
    (OUT / 'index.json').write_text(json.dumps({
        'schema_version': 1, 'retrieved_at': RETRIEVED,
        'policy': ('A locator says where a named structure is shown or labelled in an external source. '
                   'It is a reading aid matched on the structure name; it is not an asset binding, '
                   'has not been reviewed by a radiologist and does not count towards structure coverage.'),
        'sources': {
            'atlas': {'name': 'Stanford MSK MRI Atlas', 'author': 'Bao Do MD', 'site': 'https://xrayhead.com/',
                      'page': ATLAS, 'modality': 'MRI',
                      'reuse': 'No reuse licence is stated. Nothing is copied or embedded; locators link out.'},
            'radiology_assistant': {'name': 'Radiology Assistant', 'site': 'https://radiologyassistant.nl/',
                                    'reuse': ('The publisher permits reproduction for educational purposes with credit to '
                                              'the original author and the Radiology Assistant. Figures are shown from the '
                                              "publisher's own address with that credit; none is stored here."),
                                    'reuse_url': 'https://radiologyassistant.nl/disclaimer'}},
        'atlas_labels': labels, 'totals': totals, 'investigations': sorted(index, key=lambda row: row['investigation_id']),
    }, indent=1, sort_keys=True) + '\n')
    print(json.dumps(totals))


if __name__ == '__main__':
    main(Path(tempfile.gettempdir()) / 'primer-structure-locator-cache')
