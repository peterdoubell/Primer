#!/usr/bin/env python3
"""Screen every original subset thyroid mask for extent; containment is not anatomical approval."""
import argparse,gzip,hashlib,json,io,zipfile
from pathlib import Path
import numpy as np
import nibabel as nib

def sha(raw):return hashlib.sha256(raw).hexdigest()
def screen(source,out):
    meta_raw=(source/'metadata.json').read_bytes();meta=json.loads(meta_raw);entry=meta['files'][0];archive=source/entry['key'];md5=hashlib.md5();digest=hashlib.sha256()
    with archive.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):md5.update(chunk);digest.update(chunk)
    if archive.stat().st_size!=entry['size'] or 'md5:'+md5.hexdigest()!=entry['checksum'] or meta['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Original archive/licence identity differs')
    rows=[]
    with zipfile.ZipFile(archive) as z:
        names=sorted(n for n in z.namelist() if n.endswith('/segmentations/thyroid_gland.nii.gz'))
        if len(names)!=102:raise ValueError('Original thyroid case inventory differs')
        for name in names:
            raw=z.read(name);image=nib.Nifti1Image.from_bytes(gzip.decompress(raw));mask=np.asanyarray(image.dataobj)
            if mask.ndim!=3 or not np.isfinite(image.affine).all() or not set(np.unique(mask)).issubset({0,1}):raise ValueError('Original mask/grid is unsupported')
            locations=np.where(mask!=0);foreground=int(np.count_nonzero(mask));bounds=[[int(x.min()),int(x.max())] for x in locations] if foreground else None
            touches=[axis for axis,x in enumerate(bounds or []) if x[0]==0 or x[1]==mask.shape[axis]-1]
            rows.append({'case':name.split('/')[0],'member':name,'source_member_sha256':sha(raw),'source_member_CRC32':f'{z.getinfo(name).CRC:08x}','shape':list(mask.shape),'source_spacing':[float(v) for v in image.header.get_zooms()],'foreground_voxels':foreground,'source_bounds_xyz_inclusive':bounds,'touches_volume_axes':touches,'empty':not foreground,'source_affine':image.affine.tolist(),'source_components_or_labels_modified':False})
            del mask,image,locations
    proof={'source_doi':'10.5281/zenodo.10047263','original_metadata_sha256':sha(meta_raw),'archive_sha256':digest.hexdigest(),'publisher_full_archive_MD5_verified':True,'actual_dataset_license':meta['metadata']['license'],'cases':rows,'case_count':len(rows),'nonempty_not_boundary_touching_cases':[r['case'] for r in rows if not r['empty'] and not r['touches_volume_axes']],'empty_cases':[r['case'] for r in rows if r['empty']],'boundary_touching_cases':[r['case'] for r in rows if r['touches_volume_axes']],'source_boundary_containment_is_full_anatomical_approval':False,'source_1_5mm_sampling_is_adequate_for_all_reported_tiny_tissues':False,'clinical_approval':False,'runtime_promoted':False}
    out.mkdir(parents=True,exist_ok=True);(out/'subset-thyroid-screen.json').write_text(json.dumps(proof,indent=2)+'\n');print('102 thyroid masks reviewed; empty',len(proof['empty_cases']),'boundary touching',len(proof['boundary_touching_cases']),'s0011',next(r for r in rows if r['case']=='s0011')['touches_volume_axes'])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();screen(a.source_root,a.proof_dir)
