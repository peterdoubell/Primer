#!/usr/bin/env python3
"""Retain every original CT sample and every overlapping selected binary label."""
import argparse,base64,gzip,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
ROOT=Path(__file__).resolve().parents[2];PROOF=ROOT/'docs/thyroid-native-source-review/s0358';OUT=ROOT/'web/anatomy/totalseg-v3-s0358'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def payload(source,row):
    raw=(source/row['file']).read_bytes()
    if sha(raw)!=row['source_file_sha256']:raise ValueError('Original source member changed')
    decoded=gzip.decompress(raw);n=int(np.prod(row['dimensions']));size=n*row['bits']//8;start=int(row['voxel_offset']);data=decoded[start:start+size]
    if sha(data)!=row['raw_voxel_sha256']:raise ValueError('Independent original voxel digest differs')
    if len(data)!=size or row['endian']!='<' or row['slope']!=1 or row['intercept']!=0:raise ValueError('Unsupported original sample layout')
    return data

def package(source):
    native=json.loads((PROOF/'native-source-review.json').read_text());records=native['original_files'];ctrow=next(r for r in records if r['file']=='ct.nii.gz');ct=payload(source,ctrow)
    if ctrow['datatype_code']!=4 or ctrow['dimensions']!=[255,255,523]:raise ValueError('Unexpected original CT grid')
    combined=np.zeros(int(np.prod(ctrow['dimensions'])),dtype=np.uint8);levels=[];proofs=[];targets={r['file']:r for r in native['targets']}
    for bit,row in enumerate(r for r in records if r['file']!='ct.nii.gz'):
        original=payload(source,row);mask=np.frombuffer(original,dtype=np.uint8)
        if row['dimensions']!=ctrow['dimensions'] or row['sform']!=ctrow['sform'] or not np.isin(mask,[0,1]).all():raise ValueError('Source mask grid/value differs')
        combined|=mask<<bit;stem=row['file'].removesuffix('.nii.gz');target=targets[row['file']]
        levels.append({'level':stem.replace('_',' '),'part_id':'totalseg-v3-s0358-'+stem,'bit':bit,'center_indices':[int((a+b)//2) for a,b in target['native_bounds_xyz_inclusive']],'foreground_voxels':target['foreground_voxels']})
        proofs.append({'file':row['file'],'bit':bit,'source_file_sha256':row['source_file_sha256'],'original_payload_sha256':sha(original),'foreground_voxels':target['foreground_voxels']})
    masks=combined.tobytes()
    for row in proofs:
        recovered=((combined>>row['bit'])&1).astype(np.uint8).tobytes()
        if sha(recovered)!=row['original_payload_sha256']:raise ValueError('Overlap-preserving label readback differs')
    data={'case':'s0358','shape':ctrow['dimensions'],'spacing':[1.5,1.5,1.5],'affine':ctrow['sform'],'axes':native['source_axes'],'storage_order':'x fastest, then y, then z; original NIfTI voxel order','sample_type':'little-endian signed int16; source values, independently calibrated HU unverified','ct_sha256':sha(ct),'mask_sha256':sha(masks),'levels':levels,'ct':base64.b64encode(gzip.compress(ct,mtime=0)).decode(),'mask':base64.b64encode(gzip.compress(masks,mtime=0)).decode()}
    html=OUT/'ct-reference.html';template=ROOT/'tools/anatomy_sources/thyroid_source_CT_template.html';html.write_text(template.read_text().replace('__DATASET_JSON__',json.dumps(data,separators=(',',':'))))
    # Read persisted embedded arrays independently; source payloads and all overlaps must survive.
    stored=json.loads(html.read_text().split('<script id="dataset" type="application/json">',1)[1].split('</script>',1)[0]);readct=gzip.decompress(base64.b64decode(stored['ct']));readmask=gzip.decompress(base64.b64decode(stored['mask']))
    if readct!=ct or readmask!=masks:raise ValueError('Persisted original array bytes changed')
    proof={'case':'s0358','source_native_review_sha256':sha((PROOF/'native-source-review.json').read_bytes()),'shape':ctrow['dimensions'],'CT_sample_count':int(np.prod(ctrow['dimensions'])),'CT_payload_sha256':sha(ct),'CT_source_file_sha256':ctrow['source_file_sha256'],'all_original_CT_sample_bytes_preserved':True,'mask_payload_sha256':sha(masks),'binary_mask_readback':proofs,'all_eight_binary_masks_recover_exactly':True,'overlap_voxels':int(np.count_nonzero((combined&(combined-1))!=0)),'source_voxels_resampled_relabelled_cropped_or_repaired':False,'viewer_sha256':sha(html.read_bytes()),'script_sha256':sha((OUT/'ct-reference.js').read_bytes()),'clinical_approval':False,'independent_physical_calibration':False}
    (PROOF/'CT-reader-array-review.json').write_text(json.dumps(proof,indent=2)+'\n')
    p=ROOT/'data/radiology/source-anatomy-references.json';refs=json.loads(p.read_text());entry=next(r for r in refs['ra.ultrasound-thyroid'] if r['atlas']=='totalseg-v3-s0358');manifest=json.loads((OUT/'manifest.json').read_text());entry['source_volume']={'id':'totalseg-v3-s0358-complete-CT','src':'/app/anatomy/totalseg-v3-s0358/ct-reference.html','sha256':proof['viewer_sha256'],'script_sha256':proof['script_sha256'],'level_by_part':{i:r['name'].split(' · ')[0] for i,r in manifest['parts'].items()},'title':'Inspect matching complete source CT and original labels','caption':'Every native source slice and all eight original masks, with preserved overlaps. One 1.5 mm CT dataset grid; source index/RAS coordinates and source-value windowing, not independently calibrated HU, native DICOM orientation or ultrasound findings. Source annotation bounds and caps do not establish complete physical anatomy.','attribution':manifest['viewer_notes'][-1],'source_url':manifest['source_url'],'license_url':manifest['license_url']};p.write_text(json.dumps(refs,indent=2)+'\n');print('Every',proof['CT_sample_count'],'CT sample and eight masks preserved;',proof['overlap_voxels'],'overlap voxels retained')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
