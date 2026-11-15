#!/usr/bin/env python3
"""Compare all original pancreatic region boundary edges without fusion or repairs."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(root,output):
    from tools.anatomy_sources.inspect_hra_renal_glb import read_glb,accessor
    from tools.anatomy_sources.audit_hra_renal_interfaces import compare_boundaries
    for sex in ['female','male']:
        key='pancreas-'+sex+'-v1.3';report_path=output/(key+'-original-primitives.json');report=json.loads(report_path.read_text())
        path=root/key/('3d-vh-'+sex[0]+'-pancreas.glb');raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=report['source_glb_sha256']:raise ValueError('Original source GLB changed')
        doc,binary=read_glb(raw);parts=[]
        for r in report['records']:
            node=doc['nodes'][r['node_index']];p=doc['meshes'][node['mesh']]['primitives'][r['primitive_index']]
            vertices=accessor(doc,binary,p['attributes']['POSITION']);indices=accessor(doc,binary,p['indices']).reshape(-1)
            if hashlib.sha256(vertices.tobytes()).hexdigest()!=r['position_accessor_sha256'] or hashlib.sha256(indices.tobytes()).hexdigest()!=r['indices_accessor_sha256']:
                raise ValueError('Original accessor differs from inventory')
            parts.append({'id':r['node_name'],'vertices':vertices,'faces':indices.reshape(-1,3)})
        result=compare_boundaries(parts)
        result.update(source_glb_sha256=report['source_glb_sha256'],source_inventory_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
                      sex=sex,source_version='v1.3',runtime_promoted=False,
                      limits=['All source region boundaries compared by exact Float32 coordinates; no tolerance, snapping, fitting, welding or fusion changes the source.',
                              'Corresponding region cut edges do not prove histological boundaries, full organ solidity, patient registration or clinically approved topology.',
                              'Unmatched, multiple-owner, nonmanifold and degenerate source elements remain held for review rather than pruned or capped.'])
        (output/(key+'-boundary-review.json')).write_text(json.dumps(result,indent=2)+'\n')
        print('Original anatomy boundary review complete.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.source_root,a.output)
