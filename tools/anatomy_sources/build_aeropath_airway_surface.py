#!/usr/bin/env python3
"""Reconstruct all original airway-labelled voxels without repair or smoothing."""
import argparse
import hashlib
import json
from pathlib import Path
import nibabel as nib
import numpy as np
from tools.anatomy_sources.massp_probability_mesh import mesh_mask,MeshTopologyError


def build(root,output):
    output.mkdir(parents=True,exist_ok=True);acquisition=json.loads((root/'acquisition.json').read_text())
    name='1_CT_HR_label_airways.nii.gz';entry=next(e for e in acquisition['files'] if e['name']==name);path=root/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Source annotation changed')
    image=nib.load(path);values=np.asarray(image.dataobj)
    if set(np.unique(values))!={0,1}:raise ValueError('Unexpected airway labels')
    q,qcode=image.get_qform(coded=True);s,scode=image.get_sform(coded=True)
    if not qcode or not scode or not np.allclose(q,s,rtol=0,atol=1e-5):raise ValueError('Source affine ambiguity')
    details={}
    try:
        vertices,faces,stats=mesh_mask(values>0,image.affine)
    except MeshTopologyError as error:
        stats=error.diagnostics;details={'output_mesh_created':False,'status':'held_topology_failure'}
    else:
        mesh_path=output/'case-1-airways.npz';np.savez_compressed(mesh_path,vertices=vertices,faces=faces)
        details={'output_mesh_created':True,'status':'offline_source_surface_requires_validation','mesh_file':mesh_path.name,'mesh_sha256':hashlib.sha256(mesh_path.read_bytes()).hexdigest()}
    record={'source_dataset_doi':acquisition['source_dataset_doi'],'source_annotation_file':name,'source_annotation_sha256':entry['sha256'],
            'source_affine':image.affine.tolist(),'native_axis_codes':list(nib.aff2axcodes(image.affine)),
            'source_values_changed':False,'smoothing_or_decimation':False,**details,**stats,'clinical_approval':False,'runtime_promoted':False,
            'limits':'Binary source annotation only. Surface closure follows annotation endpoints, not demonstrated physical airway endings. No wall/cartilage, named branches, lobes, segments or acquisition phase inferred. Source cohort has pathology; no healthy designation or whole-anatomy completeness claimed.'}
    (output/'surface-review.json').write_text(json.dumps(record,indent=2)+'\n');print(details['status'],stats['triangles'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();build(args.source,args.output)
