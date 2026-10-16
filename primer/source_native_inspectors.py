"""Pinned source-native atlas inspectors; source fidelity is not clinical approval."""
import hashlib
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/radiology'
PREFIX = '/app/anatomy/brain-fine-massp2/'


@lru_cache(maxsize=1)
def delivery():
    data = json.loads((DATA / 'native-source-delivery.json').read_text())
    if data.get('schema_version') != 1 or data.get('project_id') != 'prj_AkCCMkedaGlozDzJqTtteq29MAit':
        raise ValueError('Native source delivery belongs to another project')
    store_id = data.get('store_id', '')
    if (not re.fullmatch(r'store_[A-Za-z0-9]{16}', store_id)
            or data.get('blob_hostname') != store_id.removeprefix('store_').lower() + '.public.blob.vercel-storage.com'):
        raise ValueError('Native source store identity or hostname changed')
    files = data['files']
    if len(files) != 14:
        raise ValueError('Incomplete native brain payload inventory')
    for src, row in files.items():
        if (not src.startswith(PREFIX) or not re.fullmatch(r'[a-z0-9.-]+\.gz', src.removeprefix(PREFIX))
                or not re.fullmatch(r'[0-9a-f]{64}', row.get('sha256', ''))
                or type(row.get('bytes')) is not int or row['bytes'] <= 0):
            raise ValueError('Invalid native source file identity')
        url = urlsplit(row['url'])
        if (url.scheme != 'https' or url.hostname != data['blob_hostname'] or url.netloc != url.hostname
                or not url.hostname.endswith('.public.blob.vercel-storage.com')
                or url.query or url.fragment or not url.path.startswith('/anatomy/brain-fine-massp2/' + row['sha256'] + '/')):
            raise ValueError('Native source delivery leaves its pinned content-addressed store')
    return data


@lru_cache(maxsize=1)
def references():
    data = json.loads((DATA / 'native-source-inspectors.json').read_text())
    if set(data['bindings']) != {'ra.brain-anatomy'} or len(data['inspectors']) != 1:
        raise ValueError('Unexpected native source inspector scope')
    published = delivery()['files']
    for item in data['inspectors'].values():
        if (item.get('src') != PREFIX + 'reference.html' or item.get('manifest_url') != PREFIX + 'manifest.json'
                or item.get('bound_source_ids') != ['massp2-subcortical-reference']
                or item.get('clinical_approval') is not False or item.get('fine_anatomical_approval') is not False):
            raise ValueError('Native source inspector has an unreviewed path or approval')
        for field, src in [('sha256', item['src']), ('script_sha256', PREFIX + 'reference.js'), ('manifest_sha256', item['manifest_url'])]:
            if hashlib.sha256((ROOT / 'web' / src.removeprefix('/app/')).read_bytes()).hexdigest() != item[field]:
                raise ValueError('Native source inspector file changed')
        manifest = json.loads((ROOT / 'web/anatomy/brain-fine-massp2/manifest.json').read_text())
        arrays = [manifest['labels'], *manifest['contrasts'].values(), *manifest['probabilities'].values()]
        if len(arrays) != 14 or {row['file'] for row in arrays} != set(published):
            raise ValueError('Native source contrast, probability or label is missing')
        for row in arrays:
            route = published[row['file']]
            if (route['sha256'], route['bytes']) != (row['sha256'], row['bytes']):
                raise ValueError('Native source delivery differs from the reviewed manifest')
            local = ROOT / 'web' / row['file'].removeprefix('/app/')
            if local.is_file():
                raw = local.read_bytes()
                if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                    raise ValueError('Native source compressed bytes changed')
            elif not os.environ.get('VERCEL'):
                raise ValueError('Native source payload absent locally')
        if sum(row['bytes'] for row in arrays) != 17434638:
            raise ValueError('Native source packet is incomplete')
        for field in ['title', 'caption', 'attribution', 'source_url', 'license', 'license_url']:
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError('Native source inspector lacks explicit provenance')
    result = {key: [data['inspectors'][identifier] for identifier in identifiers] for key, identifiers in data['bindings'].items()}
    from .stroke_native_inspectors import references as stroke_references
    result.update(stroke_references())
    from .pulmonary_native_inspectors import references as pulmonary_references
    result.update(pulmonary_references())
    from .thoracic_native_inspectors import references as thoracic_references
    result.update(thoracic_references())
    from .thoracic_lung_native import references as lung_references
    for identifier, entries in lung_references().items():
        result[identifier] = [*result.get(identifier, []), *entries]
    from .thoracic_basal_context import references as basal_references
    for identifier, entries in basal_references().items():
        result[identifier] = [*result.get(identifier, []), *entries]
    from .cardiac_native_inspector import references as cardiac_references
    for identifier, entries in cardiac_references().items():
        result[identifier] = [*result.get(identifier, []), *entries]
    from .cardiac_wall_context import references as wall_references
    for identifier, entries in wall_references().items():
        result[identifier] = [*result.get(identifier, []), *entries]
    from .hippunfold_reference import references as hippocampal_references
    for identifier, entries in hippocampal_references().items():
        result[identifier] = [*result.get(identifier, []), *entries]
    from .spl_limbic_reference import references as spl_limbic_references
    for identifier, entries in spl_limbic_references().items():
        result[identifier] = [*result.get(identifier, []), *entries]
    return result
