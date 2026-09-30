"""Build a standalone, lossless-data CT/label review viewer for all T1-L5 levels."""
from pathlib import Path
import base64, gzip, hashlib, json
import nibabel as nib
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
CASE=Path('/tmp/primer-msk-sources/verse/verse521')
OUT=ROOT/'output/msk-verse521/review'


def main():
    audit=json.loads((ROOT/'docs/msk-verse-source-review/chain-surface-audit.json').read_text())
    for name,digest in audit['source_files'].items():
        assert hashlib.sha256((CASE/name).read_bytes()).hexdigest()==digest
    ct=nib.load(CASE/'sub-verse521_dir-ax_ct.nii.gz');seg=nib.load(CASE/'sub-verse521_dir-ax_seg-vert_msk.nii.gz')
    assert ct.shape==seg.shape and np.array_equal(ct.affine,seg.affine)
    values=np.asanyarray(ct.dataobj);labels=np.asanyarray(seg.dataobj)
    assert np.isfinite(values).all()
    rows=[];evidence=[]
    def payload(raw):return base64.b64encode(gzip.compress(raw,mtime=0)).decode()
    for level in audit['levels']:
        start=np.maximum(0,np.asarray(level['crop_start'])-2);stop=np.minimum(values.shape,np.asarray(level['crop_stop'])+2)
        crop=tuple(slice(a,b) for a,b in zip(start,stop))
        scaled=values[crop];array=np.ascontiguousarray(scaled,dtype='<f4');binary=np.ascontiguousarray(labels[crop]==level['label'],dtype='u1')
        assert np.array_equal(array,scaled) and int(binary.sum())==level['source_voxels']
        raw=array.tobytes();mask=binary.tobytes();assert np.array_equal(np.frombuffer(gzip.decompress(base64.b64decode(payload(raw))),dtype='<f4').reshape(array.shape),scaled)
        center=(np.asarray(array.shape)//2).tolist();sample={}
        for axis in range(3):
            # Independent slice extraction provides reference centre values for browser QA.
            plane=np.take(array,center[axis],axis=axis);remaining=[a for a in range(3) if a!=axis]
            sample[str(axis)]=float(plane[center[remaining[0]],center[remaining[1]]])
        meta={'level':level['level'],'label':level['label'],'shape':list(array.shape),'start':start.tolist(),'stop':stop.tolist(),'foreground_voxels':int(binary.sum()),'ct_sha256':hashlib.sha256(raw).hexdigest(),'label_sha256':hashlib.sha256(mask).hexdigest(),'center_voxel':(start+center).tolist(),'center_values_by_axis':sample}
        evidence.append(meta);rows.append(dict(meta,ct=payload(raw),mask=payload(mask)))
    dataset={'case':'sub-verse521','axes':list(nib.aff2axcodes(ct.affine)),'spacing':list(map(float,ct.header.get_zooms())),'affine':ct.affine.tolist(),'levels':rows}
    template=(ROOT/'tools/anatomy_sources/verse-review-template.html').read_text()
    html=template.replace('__DATASET__',json.dumps(dataset,separators=(',',':')).replace('<','\\u003c'))
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/'index.html';path.write_text(html)
    result={'source_files':audit['source_files'],'affine':ct.affine.tolist(),'voxel_spacing_mm':list(map(float,ct.header.get_zooms())),'axis_codes':list(nib.aff2axcodes(ct.affine)),'viewer_file':str(path.relative_to(ROOT)),'viewer_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'viewer_bytes':path.stat().st_size,'levels':evidence,'storage':'gzip-compressed little-endian float32 scaled CT values and uint8 target-label arrays; C order, exact source equality checked','voxel_resampling':False,'geometry_modified':False,'clinical_approval':False,'runtime_promoted':False}
    (ROOT/'docs/msk-verse-source-review/full-volume-review-viewer.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Built',len(rows),'levels;',path.stat().st_size,'bytes; exact source-array equality verified.')


if __name__=='__main__':main()
