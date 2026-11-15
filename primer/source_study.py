"""Independent native studies; a volume reference does not require a mesh atlas."""
import hashlib
import json
import os
import re
from pathlib import Path

REGISTRATIONS = {
    'tcga-dk-aa6p': {
        'patient_id': 'TCGA-DK-AA6P',
        'study_instance_uid': '1.3.6.1.4.1.14519.5.2.1.9203.4016.142258435654094518230804693190',
        'modality': 'MRI', 'source_series': 22, 'source_frames': 1359,
        'source_pixel_samples': 107937792,
    },
}


def validate_study_references(registry, known, web):
    if not isinstance(registry, dict):
        raise ValueError('Source studies must map investigations')
    web = Path(web).resolve()
    inventory = None
    seen = set()
    for investigation, rows in registry.items():
        if investigation not in known or not isinstance(rows, list) or not rows:
            raise ValueError('Source study needs a known investigation')
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError('Invalid source study')
            for key in ('id', 'title', 'caption', 'limits', 'attribution', 'source_url', 'license_url'):
                if not isinstance(row.get(key), str) or not row[key].strip():
                    raise ValueError('Source study requires ' + key)
            if row['id'] in seen or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', row['id']):
                raise ValueError('Duplicate or unsafe source study identity')
            seen.add(row['id'])
            registration = REGISTRATIONS.get(row['id'])
            if not registration or any(row.get(k) != registration[k] for k in
                    ('modality', 'source_series', 'source_frames', 'source_pixel_samples')):
                raise ValueError('Source study differs from its independently reviewed registration')
            if (row.get('reference_only') is not True or row.get('clinical_approval') is not False
                    or row.get('anatomical_approval') is not False or row.get('structure_ids')
                    or row.get('requirement_coverage')):
                raise ValueError('Source study does not establish reporting anatomy coverage')
            if (row.get('modality') not in {'MRI', 'CT'} or row.get('license') != 'CC BY 3.0'
                    or row['license_url'] != 'https://creativecommons.org/licenses/by/3.0/'
                    or not row['source_url'].startswith('https://')):
                raise ValueError('Source study requires reviewed modality and commercial source licence')
            prefix = '/app/studies/' + row['id'] + '/'
            if row.get('src') != prefix + 'mri-reference.html':
                raise ValueError('Source study needs its canonical native viewer')
            context = row.get('source_context', {})
            if any(context.get(k) != registration[k] for k in ('patient_id', 'study_instance_uid')):
                raise ValueError('Source study case identity changed')
            if (not context.get('patient_id') or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)+', context.get('study_instance_uid', ''))
                    or context.get('current_patient_registered') is not False):
                raise ValueError('Source study must retain its separate case identity')
            for key in ('source_series', 'source_frames', 'source_pixel_samples'):
                if type(row.get(key)) is not int or row[key] <= 0:
                    raise ValueError('Invalid source study counts')
            files = row.get('files')
            if (not isinstance(files, dict) or set(files) != {'mri-reference.html', 'mri-reference.js'}
                    | {s.get('file') for s in row.get('series_transport', [])}):
                raise ValueError('Source study file inventory differs from complete series transport')
            series = row.get('series_transport', [])
            if (len(series) != row['source_series'] or len({s['file'] for s in series}) != len(series)
                    or sum(s.get('frames', 0) for s in series) != row['source_frames']
                    or sum(s.get('decoded_bytes', 0) for s in series) != row['source_pixel_samples'] * 2):
                raise ValueError('Source study series/frame/scalar accounting differs')
            for s in series:
                if (not re.fullmatch(r'series-[0-9]{4}\.bin\.gz', s['file'])
                        or type(s.get('frames')) is not int or s['frames'] <= 0
                        or type(s.get('decoded_bytes')) is not int or s['decoded_bytes'] <= 0
                        or s['decoded_bytes'] % 2 or not re.fullmatch(r'[0-9a-f]{64}', s.get('decoded_int16_le_sha256', ''))
                        or files[s['file']].get('sha256') != s.get('compressed_sha256')):
                    raise ValueError('Invalid source series transport identity')
            for filename, identity in files.items():
                if filename not in {'mri-reference.html', 'mri-reference.js'} and not re.fullmatch(r'series-[0-9]{4}\.bin\.gz', filename):
                    raise ValueError('Unsafe source study filename')
                if (not isinstance(identity, dict) or type(identity.get('bytes')) is not int or identity['bytes'] <= 0
                        or not re.fullmatch(r'[0-9a-f]{64}', identity.get('sha256', ''))):
                    raise ValueError('Invalid source study file identity')
                src = prefix + filename
                path = (web / src.removeprefix('/app/')).resolve()
                if not path.is_relative_to(web):
                    raise ValueError('Source study leaves its workspace')
                if path.is_file():
                    raw = path.read_bytes()
                    if len(raw) != identity['bytes'] or hashlib.sha256(raw).hexdigest() != identity['sha256']:
                        raise ValueError('Source study file changed')
                else:
                    if not os.environ.get('VERCEL'):
                        raise ValueError('Source study file missing')
                    if inventory is None:
                        inventory = json.loads((web.parent / 'data/radiology/radiology-static-source-studies.json').read_text())
                    if inventory.get('schema_version') != 1 or inventory.get('files', {}).get(src) != identity:
                        raise ValueError('Hosted source study differs from verified release inventory')
    return registry
