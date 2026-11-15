"""Independent pulmonary integration replay; local fixtures, no external mutation."""
from pathlib import Path
import collections
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
BASE = 'bca576f8d03c5a6ed3c49ea7c7370bde7fb7327e'
CASE = 'ra.ct-pulmonary-nodules'
NODE = 'rad.4.pulmonary-nodule'
PREFIX = '/app/anatomy/lidc-idri-0525/'


def sha(body):
    return hashlib.sha256(body).hexdigest()


def canon(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def load(path):
    return json.loads((ROOT / path).read_bytes())


def historical(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)


def raw_leaves(text):
    """Retain literal leaf encodings, including escaped strings and number spelling."""
    decoder = json.JSONDecoder()
    leaves = {}
    def walk(at, path):
        while text[at].isspace():
            at += 1
        if text[at] == '{':
            at += 1
            while True:
                while text[at].isspace() or text[at] == ',':
                    at += 1
                if text[at] == '}':
                    return at + 1
                name, at = decoder.raw_decode(text, at)
                while text[at].isspace():
                    at += 1
                assert text[at] == ':'
                at = walk(at + 1, path + (name,))
        elif text[at] == '[':
            at += 1
            index = 0
            while True:
                while text[at].isspace() or text[at] == ',':
                    at += 1
                if text[at] == ']':
                    return at + 1
                at = walk(at, path + (index,))
                index += 1
        else:
            _, stop = decoder.raw_decode(text, at)
            leaves[path] = text[at:stop]
            return stop
    walk(0, ())
    return leaves


def main():
    for key in list(os.environ):
        if key.startswith(('TURSO', 'PRIMER_ACCESS_', 'VERCEL', 'BLOB_')):
            os.environ.pop(key)
    logging.disable(logging.CRITICAL)
    result = {'schema_version': 1, 'base_commit': BASE,
              'scope': 'independent raw-token, effective-contract, source and full-app ASGI replay',
              'cloud_verified': False, 'external_mutations': False,
              'clinical_approval': False, 'fine_anatomical_approval': False,
              'structure_coverage_granted': False, 'whole_goal_complete': False,
              'findings': []}
    amendment_path = 'docs/pulmonary-nodule-independent-review-20261011/clinical-amendment-proposal.json'
    assert sha((ROOT / amendment_path).read_bytes()) == 'f172a46b75c14554b830c480e65ea7991a5e63457b71bc054ce8be65eb5075a1'
    amendment = load(amendment_path)
    curr = load('data/curriculum/11-radiology.json')
    node_index = next(i for i, node in enumerate(curr['nodes']) if node['id'] == NODE)
    quiz = curr['nodes'][node_index]['quiz']
    assert quiz == amendment['independent_amended_questions'] and len(quiz) == 13
    old_curr = json.loads(historical('data/curriculum/11-radiology.json'))
    old_node = old_curr['nodes'][node_index]
    assert old_node['quiz'] == amendment['original_questions']
    assert {k: v for k, v in curr['nodes'][node_index].items() if k != 'quiz'} == {k: v for k, v in old_node.items() if k != 'quiz'}
    from primer.quiz import score_quiz
    scores = [score_quiz([q], [str(q['answer'])])['score'] for q in quiz]
    assert scores == [1.0] * 13
    assert round(6 * 2 ** (1 / 3), 1) == 7.6
    assert round((7 + 3.8) / 2) == 5
    result['quiz'] = {'count': 13, 'exact_immutable_amendment': True,
                      'reference_scores': scores, 'sha256': canon(quiz)}

    # Every original leaf outside the six specifically scoped target values
    # retains its literal JSON token, rather than only an equivalent value.
    bounds = {
        'data/curriculum/11-radiology.json': ('nodes', node_index, 'quiz'),
        'data/radiology/reporting-body.json': (NODE,),
        'data/radiology/reporting-models.json': (NODE,),
        'data/radiology/reporting-steps/chest.json': ('investigations', CASE),
        'data/radiology/investigation-overrides-non-msk.json': (CASE,),
    }
    token_rows = []
    for path, allowed in bounds.items():
        before = raw_leaves(historical(path).decode())
        after = raw_leaves((ROOT / path).read_text())
        before = {k: v for k, v in before.items() if k[:len(allowed)] != allowed}
        after = {k: v for k, v in after.items() if k[:len(allowed)] != allowed}
        assert before == after, path
        baseline = ROOT / 'docs/pulmonary-nodule-integration-review-20261011/baseline' / path
        assert baseline.read_bytes() == historical(path), path
        token_rows.append({'path': path, 'unrelated_literal_tokens': len(before)})
    path = 'data/radiology/non-msk-structure-requirements.json'
    old_inventory = json.loads(historical(path))
    inventory = load(path)
    assert inventory['investigations'][:-1] == old_inventory['investigations']
    assert inventory['investigations'][-1]['investigation_id'] == CASE
    before = raw_leaves(historical(path).decode())
    after = raw_leaves((ROOT / path).read_text())
    added_index = len(old_inventory['investigations'])
    old_ids = old_inventory['scope']['catalog_investigation_ids']
    assert inventory['scope']['catalog_investigation_ids'] == old_ids + [CASE]
    assert before == {k: v for k, v in after.items()
                      if not (len(k) > 1 and k[:2] == ('investigations', added_index))
                      and k != ('scope', 'catalog_investigation_ids', len(old_ids))}
    token_rows.append({'path': path, 'unrelated_literal_tokens': len(before),
                       'bounded_scope_id_append': CASE})
    result['raw_token_preservation'] = token_rows

    entry = inventory['investigations'][-1]
    structures = entry['structures']
    assert len(structures) == len({s['id'] for s in structures}) == 79
    parts = [p['id'] for s in structures for p in s['required_parts']]
    assert len(parts) == len(set(parts)) == 625
    for s in structures:
        assert s['coverage_status'] == 'required_not_verified'
        assert s['required_representations'] == ['image', 'schematic', 'model']
        assert s['image_bindings'] == s['schematic_bindings'] == s['model_bindings'] == []
        assert s['clinical_approval'] is s['fine_anatomical_approval'] is False
        assert s['condition']
    assert entry['representation_obligations_floor'] == 1875
    assert entry['verified_representation_obligations'] == 0
    assert entry['unresolved_instantiated_denominator']
    assert entry['clinical_approval'] is entry['fine_anatomical_approval'] is entry['structure_coverage_granted'] is False
    result['inventory'] = {'groups': 79, 'parts': 625, 'unverified_obligations': 1875,
                           'actual_instantiated_denominator_unresolved': True}

    with tempfile.TemporaryDirectory(prefix='pulmonary-independent-integration-') as tmp:
        os.environ.update(PRIMER_DB=str(Path(tmp) / 'reader.db'),
                          PRIMER_BACKUP_DIR=str(Path(tmp) / 'backups'),
                          PRIMER_ACCESS_USERNAME='independent-pulmonary',
                          PRIMER_ACCESS_PASSWORD='synthetic-local-fixture')
        from primer.curriculum import Curriculum
        from primer import radiology_catalog as catalog
        curriculum = Curriculum()
        baseline = load('docs/pulmonary-nodule-integration-review-20261011/baseline-effective-contracts.json')
        assert baseline['source_commit'] == BASE and len(baseline['investigations']) == 136
        preserved = []
        current_ref = None
        for row in baseline['investigations']:
            ref = catalog.detail(curriculum, catalog.resolve(row['id']))['radiology_reference']
            contract = {k: ref.get(k) for k in ['reporting', 'report_templates', 'walkthrough', 'reading']}
            if row['id'] == CASE:
                current_ref = ref
                actual_contract_hash = canon(contract)
                if actual_contract_hash != entry['source_contract_sha256']:
                    result['findings'].append({'id': 'stale-effective-contract-pin',
                                               'actual': actual_contract_hash,
                                               'inventory': entry['source_contract_sha256']})
            else:
                assert contract == row['contract'] and canon(contract) == row['sha256'], row['id']
                preserved.append(row['id'])
        assert len(preserved) == 135
        ref = current_ref
        assert ref['source_native_only'] is True
        assert ref['key_images'] == ref['source_anatomy_references'] == []
        assert [i['id'] for i in ref['source_native_inspectors']] == ['lidc-idri-0525-native']
        walk = ref['walkthrough']
        assert walk['preset_mode'] == 'assessment-prompts' and len(walk['steps']) == 5
        assert walk['start']['images'] == [] and walk['start']['module_illustrations'] is False
        assert all(s['parts'] == s['images'] == [] and s['landmark'] == 'native-source' for s in walk['steps'])
        assert ref['reporting']['protocol'][0] == amendment['protocol_amendment']['after']
        headings = [s['heading'] for s in ref['reporting']['template_sections']]
        assert headings == ['PATHWAY', 'NODULE INVENTORY', 'SIZE AND MORPHOLOGY', 'INTERVAL CHANGE', 'ASSESSMENT']
        assert all('[' in s['body'] for s in ref['reporting']['template_sections'])
        assert all(all('[' in v for v in s['normal'].values()) for s in walk['steps'])
        module = curriculum.nodes[NODE]
        props = [m['props'] for m in module['lesson_media'] if m.get('kind') == 'model' and m.get('renderer') == 'radiology-anatomy']
        assert len(props) == 1 and props[0]['source_native_only'] is True
        assert props[0]['native_inspectors'] == ref['source_native_inspectors']
        assert module['radiology_reference']['key_images'] == []
        result['effective_contracts'] = {'preserved_count': len(preserved), 'preserved_ids': preserved,
                                       'pulmonary_sha256': actual_contract_hash,
                                       'inventory_pin_current': actual_contract_hash == entry['source_contract_sha256'],
                                       'five_blank_assessment_steps': True, 'exact_shared_lesson_source': True}

        from primer import pulmonary_source_delivery as delivery
        from primer import pulmonary_native_inspectors as native
        source = delivery.delivery()
        assert source['project_id'] == 'prj_AkCCMkedaGlozDzJqTtteq29MAit'
        assert source['team_id'] == 'team_uugEwCrCXYWxwsADiEYhKfwD'
        assert source['store_id'] == 'store_JA2lsNp9UCA4bivw'
        files = source['files']
        assert len(files) == 480 and sum(v['bytes'] for v in files.values()) == 370135064
        counts = collections.Counter()
        for src, row in files.items():
            body = (ROOT / 'web' / src.removeprefix('/app/')).read_bytes()
            assert len(body) == row['bytes'] and sha(body) == row['sha256']
            expected = 'https://ja2lsnp9uca4bivw.public.blob.vercel-storage.com/anatomy/lidc-idri-0525/' + row['sha256'] + '/' + src.removeprefix(PREFIX)
            assert row['url'] == expected
            assert row['clinical_approval'] is row['fine_anatomical_approval'] is row['structure_coverage_granted'] is False
            counts[row['role']] += 1
        assert counts['unchanged-original-CT-DICOM'] == 429
        # Exact Git object replay of all483 files also covers authored viewer and manifest.
        tree = subprocess.check_output(['git', 'ls-tree', '-r', BASE, '--', 'web/anatomy/lidc-idri-0525'], cwd=ROOT).decode()
        tree_rows = [line.split('\t', 1) for line in tree.splitlines()]
        assert len(tree_rows) == 483
        for identity, path in tree_rows:
            body = (ROOT / path).read_bytes()
            assert hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest() == identity.split()[2], path
        preserved_source_paths = ['data/radiology/native-source-delivery.json', 'data/radiology/native-source-inspectors.json',
                                  'data/radiology/acute-stroke-source-delivery.json', 'data/radiology/soop-native-inspector.json',
                                  'primer/stroke_source_delivery.py', 'primer/stroke_native_inspectors.py']
        for path in preserved_source_paths:
            assert (ROOT / path).read_bytes() == historical(path), path
        result['source_files'] = {'payload_count': 480, 'bytes': 370135064,
                                  'all483_unchanged_git_objects': True, 'role_counts': dict(counts),
                                  'old_source_registries_and_modules_unchanged': preserved_source_paths}

        config = load('vercel.json')
        routes = config['routes']
        assert len(routes[:480]) == 480
        for src, row in files.items():
            public = '/source-media/' + src.removeprefix('/app/')
            matches = [r for r in routes[:480] if re.fullmatch(r['src'], public)]
            assert len(matches) == 1 and matches[0]['dest'] == row['url'] and matches[0]['status'] == 307
        old_config = json.loads(historical('vercel.json'))
        assert routes[480] == {'src': '/source-media/anatomy/lidc-idri-0525/(.*)', 'dest': '/api/index.py'}
        assert routes[481:] == old_config['routes']
        assert config['builds'][1:] == old_config['builds'][1:]
        ignore = (ROOT / '.vercelignore').read_text().splitlines()
        patterns = [p for p in ignore if p.startswith('web/anatomy/lidc-idri-0525/')]
        for src in files:
            assert any(Path('web/' + src.removeprefix('/app/')).match(p) for p in patterns)
        for name in ['reference.js', 'reference.html', 'manifest.json']:
            assert not any(Path('web/anatomy/lidc-idri-0525/' + name).match(p) for p in patterns)
        result['upload_configuration'] = {'exact_redirects': 480, 'other_routes_unchanged': True,
                                          'payloads_excluded_authored_three_retained': True}

        # Independent cold request matrix uses the actual app and synthetic access,
        # and patches only negative fixtures, never successful response bodies.
        from fastapi.testclient import TestClient
        import primer.server as server
        auth = ('independent-pulmonary', 'synthetic-local-fixture')
        asgi_counts = collections.Counter()
        selected = list(files)
        with TestClient(server.app, follow_redirects=False, raise_server_exceptions=False) as client:
            with patch.object(native, 'references', side_effect=AssertionError('source lookup before authorization')):
                for suffix in ['reference.html', 'reference.js', 'manifest.json', 'original-ct/00000001.dcm', 'unknown.gz']:
                    for verb in ['GET', 'HEAD']:
                        response = client.request(verb, PREFIX + suffix)
                        assert response.status_code == 401 and response.headers['cache-control'] == 'no-store'
                        asgi_counts['auth_before_lookup'] += 1
            for src in selected:
                row = files[src]
                response = client.get(src, auth=auth)
                assert response.status_code == 200 and len(response.content) == row['bytes'] and sha(response.content) == row['sha256'], src
                head = client.head(src, auth=auth)
                assert head.status_code == 200 and head.content == b'' and int(head.headers['content-length']) == row['bytes'], src
                assert response.headers['cache-control'] == head.headers['cache-control'] == 'private, no-store'
                assert response.headers['content-type'].split(';')[0] == row['content_type']
                asgi_counts['exact_local_get'] += 1
                asgi_counts['exact_local_head'] += 1
            malformed = ['original-ct/00000430.dcm', 'original-ct/00000000.dcm', 'original-ct/1.dcm',
                         'original-ct/00000001.dcm/x', 'original-ct/x/00000001.dcm',
                         '%6friginal-ct/00000001.dcm', 'original-ct%2F00000001.dcm',
                         'original-ct/%2e%2e/reference.html', '%252e%252e%252freference.html',
                         'original-ct%5C00000001.dcm', 'reference.html%00', 'nested/reference.js',
                         '%72eference.html', 'reference.html/', 'LICENSE/extra']
            for hosted in [False, True]:
                if hosted:
                    os.environ['VERCEL'] = '1'
                for name in malformed:
                    for verb in ['GET', 'HEAD']:
                        assert client.request(verb, PREFIX + name).status_code == 401
                        response = client.request(verb, PREFIX + name, auth=auth)
                        assert response.status_code == 404, (name, response.status_code)
                        asgi_counts['raw_path_rejections'] += 1
                for suffix in ['reference.html', 'reference.js', 'manifest.json']:
                    for query in ['', '?v=untrusted&next=https://unreviewed.example']:
                        for verb in ['GET', 'HEAD']:
                            response = client.request(verb, PREFIX + suffix + query, auth=auth)
                            assert response.status_code == 200 and response.headers['cache-control'] == 'private, no-store'
                            expected = server.CSP
                            if suffix == 'reference.html':
                                expected = expected.replace("connect-src 'self';", "connect-src 'self' " + delivery.BLOB_PREFIX + ";")
                                expected = expected.replace("frame-ancestors 'none';", "frame-ancestors 'self';")
                            assert response.headers['content-security-policy'] == expected
                            if verb == 'GET':
                                assert sha(response.content) == native.AUTHORED_SHA256[suffix]
                            asgi_counts['authored_private_csp'] += 1
                assert client.get('/app/index.html', auth=auth).headers['content-security-policy'] == server.CSP
            for src in selected:
                for verb in ['GET', 'HEAD']:
                    response = client.request(verb, src + '?url=https://unreviewed.example&sha=0',
                                              headers={'Host': 'unreviewed.example'}, auth=auth)
                    assert response.status_code == 307 and response.headers['location'] == files[src]['url']
                    assert response.headers['cache-control'] == 'private, no-store'
                    asgi_counts['fixed_hosted_redirect_fixture'] += 1
            # Cache already populated: a newly present bad file still fails selected route.
            thin = Path(tmp) / 'thin'
            target = thin / 'web/anatomy/lidc-idri-0525/LICENSE'
            target.parent.mkdir(parents=True)
            target.write_bytes(b'corrupt local source cannot fall back to hosted fixture')
            with patch.object(delivery, 'ROOT', thin):
                for verb in ['GET', 'HEAD']:
                    response = client.request(verb, PREFIX + 'LICENSE', auth=auth)
                    assert response.status_code == 500 and 'location' not in response.headers
                    asgi_counts['cached_present_corrupt_rejected'] += 1
                target.unlink()
                for verb in ['GET', 'HEAD']:
                    response = client.request(verb, PREFIX + 'LICENSE', auth=auth)
                    assert response.status_code == 307 and response.headers['location'] == files[PREFIX + 'LICENSE']['url']
                    asgi_counts['vercel_only_absent_fixture'] += 1
                os.environ.pop('VERCEL')
                for verb in ['GET', 'HEAD']:
                    response = client.request(verb, PREFIX + 'LICENSE', auth=auth)
                    assert response.status_code == 500 and 'location' not in response.headers
                    asgi_counts['local_absent_rejected'] += 1
            result['asgi'] = dict(asgi_counts)
    paths = list(bounds) + ['data/radiology/non-msk-structure-requirements.json',
        'primer/pulmonary_source_delivery.py', 'primer/pulmonary_native_inspectors.py',
        'primer/server.py', 'primer/source_native_inspectors.py', 'primer/module_media.py',
        'primer/radiology.py', 'primer/radiology_catalog.py', 'web/app.js', 'web/lesson-models.js',
        'data/radiology/pulmonary-source-delivery.json', 'data/radiology/pulmonary-native-inspector.json',
        'vercel.json', '.vercelignore']
    result['checked_file_sha256'] = {p: sha((ROOT / p).read_bytes()) for p in dict.fromkeys(paths)}
    result['all_checks_passed'] = not result['findings']
    name = 'independent-replay.json' if result['all_checks_passed'] else 'independent-replay-findings.json'
    (OUT / name).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['raw_token_preservation', 'effective_contracts', 'checked_file_sha256']}, indent=2))
    assert result['all_checks_passed'], result['findings']


if __name__ == '__main__':
    main()
