#!/usr/bin/env python3
"""Preserve every coincident renal source face pair and its complete component without pruning."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def review(root, output):
    import numpy as np
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    inventory = json.loads((output/'original-obj-geometry-review.json').read_text())
    summary = json.loads((output/'complete-self-contact-summary.json').read_text()); findings = []
    for row in summary['records']:
        packed = (output/row['file']).read_bytes(); payload = gzip.decompress(packed)
        if hashlib.sha256(packed).hexdigest() != row['compressed_sha256'] or hashlib.sha256(payload).hexdigest() != row['uncompressed_sha256']:
            raise ValueError('Complete self-contact evidence differs')
        contacts = json.loads(payload)['triangle_contact_audit']['unexpected_contacts']
        selected = [c for c in contacts if c['shared_vertex_count'] == 3]
        if not selected:
            continue
        source = next(r for r in inventory['records'] if r['id'] == row['element_id'])
        raw = (root/'objects'/(source['id']+'.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != source['source_sha256']:
            raise ValueError('Original source changed')
        v,n,f,nf = read_obj(raw.decode()); unique,inverse = np.unique(v,axis=0,return_inverse=True); mapped = inverse[f]
        for contact in selected:
            first,second = contact['face_indices']; a,b = mapped[first],mapped[second]
            if set(a) != set(b):
                raise ValueError('Reported exact-position face coincidence differs')
            members = set(a)
            while True:
                selected_faces = np.flatnonzero(np.any(np.isin(mapped,list(members)),axis=1))
                expanded = set(mapped[selected_faces].ravel())
                if expanded == members:
                    break
                members = expanded
            findings.append({'element_id':source['id'],'source_label':source['source_label'],'source_obj_sha256':source['source_sha256'],
                'face_indices':[first,second],'complete_component_face_indices':selected_faces.tolist(),
                'exact_position_vertex_ids':[int(i) for i in sorted(members)],'original_vertex_indices':f[[first,second]].tolist(),
                'original_positions_mm':v[f[[first,second]]].tolist(),'original_normal_indices':nf[[first,second]].tolist(),
                'original_normals':n[nf[[first,second]]].tolist(),'coincident_component_is_only_the_two_original_faces':set(selected_faces)=={first,second},
                'source_geometry_changed':False,'anatomical_tissue_or_native_defect_classified':False})
    (output/'coincident-source-face-review.json').write_text(json.dumps({'findings':findings,
        'source_geometry_review_sha256':hashlib.sha256((output/'original-obj-geometry-review.json').read_bytes()).hexdigest(),
        'source_faces_removed_repaired_or_merged':False,'clinical_approval':False,'runtime_promoted':False,
        'limits':['An exact-position closed component or coincident face pair does not independently establish tissue volume, wall/lumen identity, branch patency or biological correctness.',
                  'All source indices, positions and normals remain intact. No component is deleted as an assumed artefact or renamed into a missing fine structure.']},indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); review(args.source_root,args.output)
