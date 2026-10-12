"""Preserve primary LIDC source intake without making clinical approval claims."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / '.research/pulmonary-intake-20261011'
SOURCES = {
    'lidc-collection.html': 'https://www.cancerimagingarchive.net/collection/lidc-idri/',
    'dicom-seg-collection.html': 'https://www.cancerimagingarchive.net/analysis-result/dicom-lidc-idri-nodules/',
    'tcia-usage-policy.html': 'https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/',
    'cc-by-3-legal.html': 'https://creativecommons.org/licenses/by/3.0/legalcode.en',
    'lidc-xml.zip': 'https://www.cancerimagingarchive.net/wp-content/uploads/LIDC-XML-only.zip',
    'lidc-metadata.csv': 'https://www.cancerimagingarchive.net/wp-content/uploads/LIDC-IDRI_MetaData.csv',
    'lidc-xml-documentation.doc': 'https://www.cancerimagingarchive.net/wp-content/uploads/LIDC_XML_Documentation_1_Jan_2009.doc',
    'lidc-reader-instructions.doc': 'https://www.cancerimagingarchive.net/wp-content/uploads/LIDC_Reader_Instructions_pub.doc',
    'lidc-schema.zip': 'https://www.cancerimagingarchive.net/wp-content/uploads/LIDC-IDRI-voi-array.zip',
    'series-inventory.json': 'https://services.cancerimagingarchive.net/nbia-api/services/v1/getSeries?Collection=LIDC-IDRI&Modality=CT',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def get(name_url):
    name, url = name_url
    path = PRIVATE / name
    if not path.exists():
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                raw = response.read()
            path.write_bytes(raw)
        except Exception as e:
            return dict(name=name, url=url, failure=str(e))
    raw = path.read_bytes()
    return dict(name=name, url=url, bytes=len(raw), sha256=sha(raw))


def local_tag(element):
    return element.tag.rsplit('}', 1)[-1]


def text(node, tag):
    return next((n.text for n in node.iter() if local_tag(n) == tag), None)


def analyze_xml():
    records = []
    with zipfile.ZipFile(PRIVATE / 'lidc-xml.zip') as z:
        for name in z.namelist():
            if not name.lower().endswith('.xml'):
                continue
            raw = z.read(name)
            root = ET.fromstring(raw)
            sessions = [x for x in root.iter() if local_tag(x) == 'readingSession']
            nodules = []
            for session_i, session in enumerate(sessions):
                for nodule in session:
                    if local_tag(nodule) != 'unblindedReadNodule':
                        continue
                    characteristics = next((x for x in nodule if local_tag(x) == 'characteristics'), None)
                    nodules.append(dict(reader_index=session_i, id=text(nodule, 'noduleID'),
                                        roi_count=sum(local_tag(x) == 'roi' for x in nodule),
                                        characteristics={local_tag(x): x.text for x in characteristics} if characteristics is not None else {}))
            records.append(dict(xml_name=name, bytes=len(raw), sha256=sha(raw),
                                series_uid=text(root, 'SeriesInstanceUid'),
                                study_uid=text(root, 'StudyInstanceUID'),
                                sessions=len(sessions), nodules=nodules))
    (PRIVATE / 'xml-inventory.json').write_text(json.dumps(records, indent=2) + '\n')
    return records


def main():
    PRIVATE.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        records = list(executor.map(get, SOURCES.items()))
    (PRIVATE / 'intake-receipt.json').write_text(json.dumps(records, indent=2) + '\n')
    xml = analyze_xml()
    series = json.loads((PRIVATE / 'series-inventory.json').read_text())
    by_uid = {s['SeriesInstanceUID']: s for s in series}
    candidates = []
    for x in xml:
        s = by_uid.get(x['series_uid'])
        if not s:
            continue
        texture = {n['characteristics'].get('texture') for n in x['nodules']}
        calc = {n['characteristics'].get('calcification') for n in x['nodules']}
        if {'1', '3', '5'} <= texture or ('1' in texture and s['ImageCount'] > 200):
            candidates.append(dict(patient=s['PatientID'], images=s['ImageCount'], bytes=s['FileSize'],
                                   uid=x['series_uid'], texture=sorted(v for v in texture if v),
                                   calcification=sorted(v for v in calc if v), xml=x['xml_name']))
    # Source identifiers and annotation content stay in the private intake
    # inventories. Terminal diagnostics report only aggregate counts.
    print(json.dumps(dict(xml_files=len(xml), ct_series=len(series), candidate_count=len(candidates)), indent=2))


if __name__ == '__main__':
    main()
