"""Package exact, independently checked source hierarchy masks for the atlas reader.

Requires the original licensed archive/protocol and the completed boundary review.
No registration, smoothing, anatomical relabeling, or inferred missing regions.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import io
import json
import zipfile

import nibabel as nib
import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_SHA = '6932bc8063568f0037627d5b85199ff6142b4457413f8fef8817871a3ffa1ee5'
PROTOCOL_SHA = '0276cb7b396aa42a688d8f444d8b0efac9c0f68ebd3fafdc97c30df06a5a01e1'
SEMANTICS_SHA = 'f5a36bbfa981197e3fb1e4fb6d53ea8cda4554f3136865983f50a49737087c57'
COMPOSITIONS_SHA = 'f2c0a11483f9a5b77b4c8ae94ae7c39424eb5a4f93a88cb647f0ff6457cc928a'
REVIEW_SHA = {
    'structure': ('a3f8b16c7920a80885121630b02f62493745c6e4ee99a269512ae0f789bf26f2',
                  '95b6c9d7c4a5f4271e14b421bbe6b6d62d18207fba15032ebe83235c1cff7c51'),
    'tissue': ('c487925f4779cb7d7820bfdc5f423158ce017af76061111b2942e3692b7e12c8',
               '68ff2162cf17a13d7a54956ffd6d703b552ae2126c765fa7c740d03d9163a349'),
    'organ': ('40f6057f466df35bd96e8380d5735059934db81e572b785241f62e603dcc8516',
              'b79af050393309fddce46db7850ea9381966ca236937a677bbdb51f7bc0108a5'),
}
LEVELS = {'structure': ('structure_atlas.nii.gz', 'C', 'D'),
          'tissue': ('tissue_atlas.nii.gz', 'E', 'F'),
          'organ': ('icm_atlas.nii.gz', 'G', 'H')}
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def read_pinned_json(path, expected_sha):
    """Return the reviewed bytes once; never reopen an intake path for export."""
    raw = path.read_bytes()
    if sha(raw) != expected_sha:
        raise ValueError('Unreviewed atlas authoring input')
    return raw, json.loads(raw)


def native(archive, member):
    raw = gzip.decompress(archive.read(member))
    header = nib.Nifti1Header.from_fileobj(io.BytesIO(raw[:352]))
    values = np.frombuffer(raw, offset=int(header['vox_offset']),
                           dtype=header.get_data_dtype()).reshape(header.get_data_shape(), order='F')
    assert np.isfinite(values).all() and np.array_equal(values, np.rint(values))
    return raw, header, values


def components(mask, origin):
    """Return every 26-connected component and a real source cell near its middle."""
    connected, count = ndimage.label(mask, np.ones((3, 3, 3), dtype=bool))
    sizes = np.bincount(connected.ravel())
    result = []
    for code, box in enumerate(ndimage.find_objects(connected), 1):
        middle = np.array([(s.start + s.stop - 1) // 2 for s in box])
        order = sorted(range(box[0].start, box[0].stop), key=lambda x: (abs(x-middle[0]), x))
        for i in order:
            candidates = np.argwhere(connected[i, box[1], box[2]] == code)
            if candidates.size:
                candidates += [box[1].start, box[2].start]
                closest = candidates[np.argmin(np.sum((candidates-middle[1:])**2, axis=1))]
                local = np.array([i, *closest])
                break
        assert connected[tuple(local)] == code
        focus = (local + origin).tolist()
        result.append({'id': code, 'voxels': int(sizes[code]), 'focusSourceIJK': focus,
                       'focusSourceWorld': (np.array(focus)*.5 + [-90, -126, -72]).tolist()})
    assert len(result) == count and sum(r['voxels'] for r in result) == int(mask.sum())
    return sorted(result, key=lambda r: (-r['voxels'], r['id']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--semantics', type=Path, required=True)
    parser.add_argument('--compositions', type=Path, required=True)
    args = parser.parse_args()
    archive_path = args.source/'atlas_v1.0.zip'
    archive_bytes = archive_path.read_bytes()
    if sha(archive_bytes) != ARCHIVE_SHA:
        raise ValueError('Unreviewed source atlas archive')
    protocol_path = args.source/'holiatlas-protocol-rows.json'
    _, protocol = read_pinned_json(protocol_path, PROTOCOL_SHA)
    lookup = {key: {} for key in LEVELS}
    for row in next(iter(protocol.values())):
        cells = {c['cell'][0]: c['value'] for c in row}
        try:
            fine_code = int(cells['B'])
        except (KeyError, ValueError):
            continue
        for level, (_, _, column) in LEVELS.items():
            try:
                lookup[level][fine_code] = int(cells[column])
            except (KeyError, ValueError):
                continue
    semantic_raw, semantic_review = read_pinned_json(args.semantics, SEMANTICS_SHA)
    composition_raw, compositions = read_pinned_json(
        args.compositions/'composition-manifest.json', COMPOSITIONS_SHA)
    composition_reviews = {}
    for name in ('source-compositions.json', 'build-compositions.py', 'verify-compositions.py',
                 'boundary-proof.json', 'independent-verification.json'):
        raw = (args.compositions/name).read_bytes()
        if sha(raw) != compositions['proofs'][name]:
            raise ValueError('Unreviewed composition evidence')
        composition_reviews[name] = raw
    destination = ROOT/'web/anatomy/holiatlas'
    review_out = ROOT/'docs/holiatlas-hierarchy-review-20261025'
    review_out.mkdir(parents=True, exist_ok=True)
    semantics = {r['scale']+':'+str(r['code']): r for r in semantic_review['entries']}
    assert len(semantics) == 63 and semantic_review['clinical_completion_claim'] is False
    (review_out/'source-scale-display-crosswalk.json').write_bytes(semantic_raw)
    labels = json.loads((destination/'labels.json').read_bytes())
    fine_names = {r['code']: r['name'] for r in labels['sourceClasses']}
    result = {'schemaVersion': 1, 'sourceRecord': 'https://zenodo.org/records/15690524',
              'sourceArchiveSHA256': ARCHIVE_SHA, 'protocolSHA256': sha(protocol_path.read_bytes()),
              'clinicalApproval': False, 'currentPatientRegistration': False,
              'sourceGridIsAcquisitionResolution': False,
              'millimetreFrameBasis': 'Exact voxel correspondence to the fine-label source grid with declared millimetres; coarse source headers leave spatial units unspecified.',
              'levels': {}}
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        fine_raw, fine_header, original_fine = native(archive, 'substructure_atlas.nii.gz')
        fine_sha = sha(fine_raw)
        fine = original_fine.astype(np.uint16)
        assert np.array_equal(fine, original_fine)
        del original_fine
        assert fine_header.get_xyzt_units()[0] == 'mm'
        present = set(map(int, np.unique(fine)))
        for level, (member, _, _) in LEVELS.items():
            raw, header, coarse = native(archive, member)
            assert coarse.shape == fine.shape and np.array_equal(header.get_sform(), fine_header.get_sform())
            assert not present-set(lookup[level])
            lut = np.full(max(lookup[level])+1, -1, dtype=np.int16)
            for code, target in lookup[level].items():
                lut[code] = target
            assert np.array_equal(lut[fine], coarse)
            proof_dir = args.review/('boundaries-'+level)
            reviewed_bytes = {}
            for name, expected in zip(('boundary-proof.json', 'independent-verification.json'), REVIEW_SHA[level]):
                reviewed_bytes[name], _ = read_pinned_json(proof_dir/name, expected)
            boundary = json.loads(reviewed_bytes['boundary-proof.json'])
            independent = json.loads(reviewed_bytes['independent-verification.json'])
            assert boundary['allPassed'] and independent['allPassed']
            assert boundary['sourceLabelSHA256'] == sha(raw)
            assert len(boundary['rows']) == {'structure': 53, 'tissue': 9, 'organ': 1}[level]
            rows = []
            boxes = ndimage.find_objects(coarse.astype(np.uint16))
            for source in boundary['rows']:
                code = source['code']
                box = boxes[code-1]
                mask = coarse[box] == code
                assert int(mask.sum()) == source['sourceVoxels']
                parts = components(mask, np.array([s.start for s in box]))
                assert [p['voxels'] for p in parts] == source['componentsByConnectivity']['26']
                payloads = {}
                for kind in ('mesh', 'facesPayload'):
                    payload = dict(source[kind])
                    encoded = (proof_dir/payload['file']).read_bytes()
                    assert len(encoded) == payload['gzipBytes'] and sha(encoded) == payload['gzipSHA256']
                    decoded = gzip.decompress(encoded)
                    assert len(decoded) == payload['bytes'] and sha(decoded) == payload['sha256']
                    payload['file'] = 'hierarchy-'+level+'-'+payload['file']
                    (destination/payload['file']).write_bytes(encoded)
                    payloads[kind] = payload
                members = sorted(k for k, v in lookup[level].items() if v == code and k in fine_names)
                meaning = semantics[level+':'+str(code)]
                assert meaning['source_voxels'] == source['sourceVoxels']
                present_members = [k for k in members if k in present]
                assert present_members == meaning['present_fine_codes']
                rows.append({'code': code, 'sourceName': source['sourceName'],
                             'name': meaning['display_name'],
                             'sourceDefinedMeaning': meaning['extent_definition'],
                             'exclusionsAndLimits': meaning['exclusions_and_limits'],
                             'recommendedUse': meaning['recommended_use'],
                             'level': level, 'voxels': source['sourceVoxels'],
                             'components26': parts, 'boundsSourceWorld': source['boundsSourceWorld'],
                             'fineSourceCodes': members, 'fineSourceNames': [fine_names[k] for k in members],
                             'triangles': source['triangles'], **payloads})
            result['levels'][level] = {'sourceMember': member, 'nativeSHA256': sha(raw),
                'nativeDatatype': str(coarse.dtype), 'sourceHeaderUnits': list(header.get_xyzt_units()),
                'sourceAffine': header.get_sform().tolist(), 'shape': list(coarse.shape),
                'sourceClasses': rows, 'fineToSourceCode': lut.tolist(),
                'protocolMappingCheckedVoxels': fine.size, 'protocolMappingDisagreements': 0,
                'totalTriangles': sum(r['triangles'] for r in rows)}
            for name in ('boundary-proof.json', 'independent-verification.json'):
                (review_out/(level+'-'+name)).write_bytes(reviewed_bytes[name])
            print(level, len(rows), 'classes', sum(len(r['components26']) for r in rows), 'components', flush=True)
    assert compositions['sourceArchiveSHA256'] == ARCHIVE_SHA and compositions['sourceLabelSHA256'] == fine_sha
    assert compositions['count'] == 16 and compositions['clinicalApproval'] is False
    for name in ('boundary-proof.json', 'independent-verification.json'):
        assert json.loads(composition_reviews[name])['allPassed']
    rows = []
    for code, item in enumerate(compositions['compositions'], 1):
        payloads = {}
        for kind in ('mesh', 'facesPayload'):
            payload = dict(item[kind]); encoded = (args.compositions/payload['file']).read_bytes()
            assert len(encoded) == payload['gzipBytes'] and sha(encoded) == payload['gzipSHA256']
            decoded = gzip.decompress(encoded)
            assert len(decoded) == payload['bytes'] and sha(decoded) == payload['sha256']
            payload['file'] = 'hierarchy-composition-'+payload['file']
            (destination/payload['file']).write_bytes(encoded); payloads[kind] = payload
        rows.append({'code': code, 'sourceCompositionId': item['id'], 'level': 'composition',
                     'name': item['displayName'], 'sourceName': item['displayName'],
                     'sourceDefinedMeaning': item['extentDefinition'],
                     'exclusionsAndLimits': [item['remainingLimit']],
                     'voxels': item['sourceVoxels'], 'triangles': item['triangles'],
                     'fineSourceCodes': item['sourceMemberCodes'], 'fineSourceNames': item['sourceMemberNames'],
                     'components26': item['components26'], 'boundsSourceWorld': item['boundsSourceWorld'], **payloads})
    result['levels']['composition'] = {'scope': compositions['scope'], 'sourceClasses': rows,
        'sourceMember': 'substructure_atlas.nii.gz', 'nativeSHA256': fine_sha,
        'totalTriangles': sum(r['triangles'] for r in rows), 'mutuallyExclusive': False}
    composition_out = review_out/'compositions'; composition_out.mkdir(exist_ok=True)
    (composition_out/'composition-manifest.json').write_bytes(composition_raw)
    for name, raw in composition_reviews.items():
        (composition_out/name).write_bytes(raw)
    result['presentClasses'] = sum(len(v['sourceClasses']) for v in result['levels'].values())
    result['totalTriangles'] = sum(v['totalTriangles'] for v in result['levels'].values())
    (destination/'hierarchy.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'classes': result['presentClasses'], 'triangles': result['totalTriangles'],
                      'hierarchySHA256': sha((destination/'hierarchy.json').read_bytes())}))


if __name__ == '__main__':
    main()
