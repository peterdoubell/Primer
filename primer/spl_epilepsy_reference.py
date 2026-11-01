"""Focused source context without new anatomical data or approval transfer."""
from functools import lru_cache
from pathlib import Path
import copy
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'spl-epilepsy-context'
IDENTIFIER = 'spl-epilepsy-temporal-ventricular-source-context'
PREFIX = '/app/anatomy/' + ATLAS + '/'
REGISTRY = ROOT / 'data/radiology/spl-epilepsy-context-reference.json'
REGISTRY_SHA256 = '0ccdf7ab5027ce7570f51f0f6e525cc8d734508f8eec24ef596e559bcece5327'
AUTHORED = frozenset({'index.html', 'manifest.json'})
CONTEXT_CODES = [4, 43, 5, 44, 2, 41, 1001, 2001, 1009, 2009, 1015, 2015, 1030, 2030, 1033, 2033, 1034, 2034]
sha = lambda raw: hashlib.sha256(raw).hexdigest()

def regular(path):
    if not path.is_file() or any(p.is_symlink() for p in [path, *path.parents] if p == ROOT or ROOT in p.parents):
        raise ValueError('Epilepsy context source must be a regular file')

@lru_cache(maxsize=1)
def registry():
    regular(REGISTRY); raw = REGISTRY.read_bytes()
    if sha(raw) != REGISTRY_SHA256:
        raise ValueError('Epilepsy source context registry changed')
    data = json.loads(raw)
    if (data['schema_version'] != 1 or data['bindings'] != ['ra.mri-epilepsy'] or
            set(data['files']) != AUTHORED or data['source_payloads_changed'] is not False or
            data['clinicalApproval'] is not False or data['wholeGoalComplete'] is not False or
            data['context_group']['codes'] != CONTEXT_CODES or data['context_group']['completeReportingRequirementApproved'] is not False):
        raise ValueError('Epilepsy source context scope changed')
    return data

@lru_cache(maxsize=1)
def manifest_bytes():
    row = registry()['runtime_manifest']
    if row['path'] != 'data/radiology/spl-epilepsy-context-manifest.json.gz':
        raise ValueError('Epilepsy context manifest address differs')
    path = ROOT / row['path']; regular(path); packed = path.read_bytes()
    if len(packed) != row['bytes'] or sha(packed) != row['sha256']:
        raise ValueError('Epilepsy context manifest transport differs')
    raw = gzip.decompress(packed)
    if len(raw) != row['decodedBytes'] or sha(raw) != row['decodedSHA256']:
        raise ValueError('Epilepsy context manifest identity differs')
    return raw

def validate_file(asset):
    if asset not in AUTHORED:
        raise ValueError('Unknown epilepsy context resource')
    row = registry()['files'][asset]
    if asset == 'manifest.json':
        raw = manifest_bytes()
        if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
            raise ValueError('Epilepsy context manifest descriptor differs')
        return ROOT / 'web/anatomy' / ATLAS / asset
    path = ROOT / 'web/anatomy' / ATLAS / asset; regular(path); raw = path.read_bytes()
    if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
        raise ValueError('Epilepsy context resource changed')
    return path

@lru_cache(maxsize=1)
def references():
    from . import spl_reporting_reference as source
    source.references()
    data = registry()
    for asset in AUTHORED:
        validate_file(asset)
    original = source.manifest_bytes()
    if sha(original) != data['source_manifest_sha256']:
        raise ValueError('Epilepsy context parent identity differs')
    expected = copy.deepcopy(json.loads(original))
    expected['groups'][0] = data['context_group']
    expected['defaultGroup'] = data['context_group']['id']
    expected['defaultComparisonCode'] = 43
    actual = json.loads(manifest_bytes())
    if actual != expected:
        raise ValueError('Epilepsy context changed original source data or unrelated groups')
    labels = {row['code']: row for row in actual['labels']}
    if any(code not in labels for code in CONTEXT_CODES):
        raise ValueError('Epilepsy context names absent source labels')
    item = data['inspector']; grain = item['source_grain']
    if (item['id'] != IDENTIFIER or item['src'] != PREFIX + 'index.html' or
            item['manifest_url'] != PREFIX + 'manifest.json' or item['bound_source_ids'] != [IDENTIFIER] or
            item['sha256'] != data['files']['index.html']['sha256'] or
            item['manifest_sha256'] != data['files']['manifest.json']['sha256'] or
            grain['initial_context_codes'] != CONTEXT_CODES or grain['initial_context_label_classes'] != 18 or
            grain['all_available_source_label_classes'] != 217 or
            any(grain[key] is not False for key in ['ventricular_wall_layers_separately_labelled', 'hippocampal_subdivisions_separately_labelled', 'epilepsy_pathology_validated']) or
            any(item.get(flag) is not False for flag in source.FLAGS)):
        raise ValueError('Epilepsy context identity or approval meaning changed')
    return {'ra.mri-epilepsy': [item]}
