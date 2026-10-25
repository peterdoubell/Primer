from pathlib import Path
import json,zipfile,gzip,hashlib,io,datetime
import numpy as np
import nibabel as nib
out=Path(__file__).resolve().parent
rows=next(iter(json.loads((out/'holiatlas-protocol-rows.json').read_text()).values()));protocol={}
for row in rows:
 cells={c['cell'][0]:c['value'] for c in row}
 try:code=int(cells['B'])
 except (KeyError,ValueError):continue
 assert code not in protocol
 protocol[code]={'name':cells['A'],'side':cells.get('I'),'structure':cells.get('C'),'notes':cells.get('K','')}
with zipfile.ZipFile(out/'atlas_v1.0.zip') as archive:
 raw=gzip.decompress(archive.read('substructure_atlas.nii.gz'))
 header=nib.Nifti1Header.from_fileobj(io.BytesIO(raw[:352]));shape=tuple(int(v) for v in header.get_data_shape());offset=int(header['vox_offset']);labels=np.frombuffer(raw,offset=offset,dtype=header.get_data_dtype()).reshape(shape,order='F')
 assert len(raw)==offset+labels.size*labels.dtype.itemsize
 assert np.isfinite(labels).all() and np.array_equal(labels,np.rint(labels))
 small=labels.astype('<u2');assert np.array_equal(small.astype(labels.dtype),labels)
 codes,counts=np.unique(small,return_counts=True);actual={int(k):int(v) for k,v in zip(codes,counts)}
 assert not set(actual)-set(protocol)
 affine=header.get_sform();assert np.array_equal(affine,header.get_qform())
 paired={}
 for name in ['T1w_average.nii.gz','T2w_average.nii.gz','WMn_average.nii.gz']:
  with archive.open(name) as f,gzip.GzipFile(fileobj=f) as g:h=nib.Nifti1Header.from_fileobj(io.BytesIO(g.read(352)))
  assert h.get_data_shape()==shape and np.array_equal(h.get_sform(),affine) and np.array_equal(h.get_qform(),affine)
  paired[name]={'shape':list(shape),'sformAndQformExactlyEqualToLabels':True,'units':h.get_xyzt_units()}
 classes=[{'code':code,**p,'voxels':actual.get(code,0)} for code,p in protocol.items()]
 targets=[]
 for p in classes:
  if any(term in p['name'].lower() for term in ['central sulcus','sylvian','calcarine fissure']):
   loc=np.nonzero(small==p['code']);minimum=[int(x.min()) for x in loc];maximum=[int(x.max()) for x in loc]
   center=np.array([x.mean() for x in loc]);world=affine@np.r_[center,1]
   targets.append({**p,'voxelBoundsInclusive':[minimum,maximum],'centroidSourceCoordinates':world[:3].tolist()})
 proof={'status':'RESEARCH_ONLY; no runtime binding, clinical approval or cross-atlas registration','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archiveRecord':'https://zenodo.org/records/15690524','labelGrid':list(shape),'spacing':list(map(float,header.get_zooms())),'units':header.get_xyzt_units(),'sform':affine.tolist(),'sourceLabelDatatype':str(labels.dtype),'nativeLabelBytes':len(raw),'nativeLabelSHA256':hashlib.sha256(raw).hexdigest(),'allLabelsFiniteExactIntegers':True,'allLabelsLosslesslyUint16Representable':True,'protocolCodes':len(protocol),'presentCodes':len(actual),'missingProtocolCodes':sorted(set(protocol)-set(actual)),'unknownDataCodes':[],'pairedHeaderChecks':paired,'classes':classes,'targetStructures':targets,'limitations':['0.5 mm supplied grid is not proof of acquired resolution or independent boundary accuracy.','Population-average atlas, not an individual patient and not registered to the existing SPL viewer.','No named cistern or capsule entries were found in the protocol; these gaps remain.','No smoothing, class merging or new meshes were performed.']}
 (out/'holiatlas-label-review.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k not in ['classes','targetStructures']}));print('Target structures:',len(targets))
