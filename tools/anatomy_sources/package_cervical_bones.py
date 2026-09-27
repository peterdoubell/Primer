"""Package only checked C1/C2 exports as an offline reference, not approval."""
import hashlib,json,shutil,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path('/tmp/primer-msk-sources/atlantoaxial-staged')
OUT=ROOT/'output/msk-cervical-bones'


def build(output=OUT):
    audit=json.loads((ROOT/'docs/msk-atlantoaxial-source-review/export-audit.json').read_text())
    topology=json.loads((ROOT/'docs/msk-atlantoaxial-source-review/topology.json').read_text())
    world=json.loads((SOURCE/'world-inventory.json').read_text())
    inventory=json.loads((ROOT/'docs/msk-atlantoaxial-source-review/inventory.json').read_text())['sources'][0]['matched_objects']
    parent=json.loads((ROOT/'web/anatomy/msk-atlas/manifest.json').read_text())
    if world['unit_meters']!=0.01 or world['axes']!=audit['axes']:raise ValueError('Unexpected source coordinate system')
    selected=[]
    for name,color in [('Atlas (C1)','#5f9ec5'),('Axis (C2)','#d9a164')]:
        record=next(x for x in audit['parts'] if x['name']==name)
        check=next(x for x in topology['parts'] if x['name']==name)
        source=next(x for x in world['meshes'] if x['name']==name)
        original=next(x for x in inventory if x['name']==name)
        if (source['world_transform_columns']!=original['world_transform_columns']
                or source['source_geometry_id']!=record['source_geometry_id']
                or source['source_model_id']!=record['source_model_id']
                or source['bounds']!=record['bounds']):
            raise ValueError('Changed source identity or transform')
        if check['sha256']!=record['sha256'] or any(check[k] for k in ['boundary_edges','nonmanifold_edges','inconsistent_two_face_edges','degenerate_triangles']):
            raise ValueError('Source topology requires review: '+name)
        data=Path(record['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('Changed source export')
        magic,n,k=struct.unpack('<4sII',data[:12])
        if magic!=b'BP3D' or len(data)!=12+n*24+k*4 or k//3!=record['triangles']:raise ValueError('Invalid binary')
        positions=list(struct.iter_unpack('<fff',data[12:12+n*12]))
        identifier='za-bones-'+str(record['source_model_id'])
        part={k:source[k] for k in ['name','source_model_id','source_geometry_id','world_transform_columns','ancestors']}
        part.update(id=identifier,file=identifier+'.bin',sha256=record['sha256'],vertices=n,triangles=k//3,
                    bounds=[[min(p[a] for p in positions) for a in range(3)],[max(p[a] for p in positions) for a in range(3)]],
                    source_sha256=audit['source_sha256'],source_file='z-anatomy-SkeletalSystem100.fbx',layer='bone',color=color,
                    fidelity_review='pending',license='CC BY-SA 4.0')
        selected.append((part,data))
    output.mkdir(parents=True,exist_ok=True)
    for part,data in selected:(output/part['file']).write_bytes(data)
    parts={p['id']:p for p,_ in selected}
    bounds=[[min(p['bounds'][0][a] for p in parts.values()) for a in range(3)],[max(p['bounds'][1][a] for p in parts.values()) for a in range(3)]]
    manifest={'dataset':'Z-Anatomy C1/C2 bone reference','status':'offline; anatomical fidelity unverified','source_url':parent['source_url'],
              'license':'CC BY-SA 4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/',
              'coordinate_system':parent['coordinate_system'],'parts':parts,
              'bounds':bounds,'excluded':['Occipital source mesh: open/non-manifold edges','No ligament, cartilage, neural or vascular structures included'],
              'limitations':'Preserved source bone surfaces only. No instability, validated joint surfaces, ligament attachments or clinical accuracy inferred.',
              'clinical_approval':False}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    shutil.copyfile(ROOT/'web/anatomy/msk-atlas/SOURCE-LICENSE.txt',output/'SOURCE-LICENSE.txt')
    (output/'ATTRIBUTION.md').write_text('# C1/C2 source-bone reference\n\nBodyParts3D, The Database Center for Life Science (source lineage); Z-Anatomy contributors. CC BY-SA 4.0.\n\nSource: '+parent['source_url']+'\n\nOriginal source-coordinate meshes exported to BP3D using the project ufbx exporter. No alignment, smoothing or hole repair. Normals follow the existing exporter behavior. This offline package is not clinically approved and omits stabilising soft tissues.\n')
    return manifest


if __name__=='__main__':
    result=build();print('Packaged',len(result['parts']),'bones;',sum(p['triangles'] for p in result['parts'].values()),'triangles; offline only.')
