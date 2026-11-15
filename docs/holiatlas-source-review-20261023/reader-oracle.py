from pathlib import Path
import json,gzip,zipfile,io,hashlib,struct
import numpy as np,nibabel as nib
ROOT=Path(__file__).resolve().parent;P=ROOT/'reader-package';labels=json.loads((P/'labels.json').read_text());config=json.loads((P/'config.json').read_text());meta={r['code']:r for r in labels['sourceClasses']};cases=[{'code':80,'component':0},{'code':80,'component':len(meta[80]['components26'])-1},{'code':61,'component':0},{'code':102,'component':0},{'code':342,'component':0},{'code':next(r['code'] for r in meta.values() if r['name']=='Right Thalamus Anterior Ventral Nucleus'),'component':0}];sha=lambda b:hashlib.sha256(b).hexdigest();expected={}
with zipfile.ZipFile(ROOT/'atlas_v1.0.zip') as z:
 raw=gzip.decompress(z.read('substructure_atlas.nii.gz'));h=nib.Nifti1Header.from_fileobj(io.BytesIO(raw[:352]));mask=np.frombuffer(raw,offset=int(h['vox_offset']),dtype=h.get_data_dtype()).reshape(h.get_data_shape(),order='F')
 for contrast,name in [('T1','T1w_average.nii.gz'),('T2','T2w_average.nii.gz'),('WMn','WMn_average.nii.gz')]:
  rawMRI=gzip.decompress(z.read(name));h=nib.Nifti1Header.from_fileobj(io.BytesIO(rawMRI[:352]));image=np.frombuffer(rawMRI,offset=int(h['vox_offset']),dtype=h.get_data_dtype()).reshape(h.get_data_shape(),order='F');low,high=config['windows'][contrast]
  for case in cases:
   code,component=case['code'],case['component'];ijk=meta[code]['components26'][component]['focusSourceIJK']
   for axis in range(3):
    selection=[slice(None)]*3;selection[axis]=ijk[axis];source=image[tuple(selection)].astype(np.float64).T[::-1];selected=(mask[tuple(selection)]==code).T[::-1];gray=np.floor(255*np.clip((source-low)/(high-low),0,1)+.5).astype(np.uint8);pixels=np.empty((*gray.shape,4),np.uint8);pixels[:,:,:3]=gray[:,:,None];pixels[:,:,3]=255;pixels[selected,0]=np.floor(gray[selected]*.45+.5);pixels[selected,1]=pixels[selected,2]=np.floor(gray[selected]*.45+140.25+.5);key=f'{code}:{component}:{contrast}:{axis}';expected[key]={'sha256':sha(pixels.tobytes()),'shape':list(pixels.shape),'selectedPixels':int(selected.sum())};assert expected[key]['selectedPixels']>0
meshes={}
for code,row in meta.items():
 if not row['voxels']:continue
 raw=gzip.decompress((ROOT/'boundaries'/row['mesh']['file']).read_bytes());_,V,T,_=struct.unpack_from('<4sIII',raw);meshes[str(code)]={'positionSHA256':sha(raw[16:16+12*V]),'indexSHA256':sha(raw[16+12*V:]),'vertices':V,'triangles':T}
proof={'scope':'Independent numpy source-volume pixel oracle; native bit and global-face proofs are separate','cases':cases,'pixels':expected,'meshes':meshes};(ROOT/'reader-oracle.json').write_text(json.dumps(proof,indent=2)+'\n');print({'pixelCases':len(expected),'meshCases':len(meshes)})
