#!/usr/bin/env python3
"""Build an offline unsmoothed lumen-label baseline; not clinical anatomy approval."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import nibabel as nib
from tools.anatomy_sources.massp_probability_mesh import mesh_mask


def build(root,output):
    output.mkdir(parents=True,exist_ok=True)
    acquisition=json.loads((root.parent/'imagecas-x-case-134-acquisition.json').read_text())
    source_name='134.coronary.nii.gz';entry=next(e for e in acquisition['files'] if Path(e['name']).name==source_name)
    path=root/source_name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Source annotation changed')
    image=nib.load(path);labels=np.asarray(image.dataobj);q,qcode=image.get_qform(coded=True);s,scode=image.get_sform(coded=True)
    if not qcode or not scode or not np.allclose(q,s,rtol=0,atol=1e-5):raise ValueError('Ambiguous label affine')
    vertices,faces,stats=mesh_mask(labels>0,image.affine)
    mesh_path=output/'134-unsmoothed-lumen.npz';np.savez_compressed(mesh_path,vertices=vertices,faces=faces)
    name='ImageCAS-X case 134 foreground lumen labels'
    record={'source_doi':'10.5281/zenodo.21887809','publisher_selection_file':source_name,'selection':'All original positive source labels; branch identities remain in the untouched label volume',
            'records':[{'label_id':1,'code':'lumen','side':'source','name':name,'mesh_file':mesh_path.name,'mesh_sha256':hashlib.sha256(mesh_path.read_bytes()).hexdigest(),'output_mesh_created':True,**stats}],
            'source_label_sha256':entry['sha256'],'source_label_values_changed':False,'smoothing_or_decimation':False,
            'clinical_approval':False,'runtime_promoted':False,'original_ct_images_acquired':False,
            'limits':'Source-label isosurface, not measured continuous vessel wall. Labels lack LM in this case and do not prove whole-tree completeness. Closure follows annotation endpoints, not validated physical vessel endings; no lumen measurements, original CT accuracy or commercial CT permission is granted.'}
    (output/'surface-review.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Triangles:',len(faces),'source components:',stats['source_components_6_connected'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();build(args.source,args.output)
