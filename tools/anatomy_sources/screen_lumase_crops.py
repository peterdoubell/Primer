"""Screen the first ten paired L3 masks for source boundary contact, without edits."""
from pathlib import Path
import json,hashlib
import numpy as np
import nibabel as nib
from acquire_lumase_case import read_member
ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/msk-vertebral-substructure-source-review';OUT=ROOT/'.research/anatomy-sources/lumase/crop-screen'
def main():
 archive=json.loads((DOC/'lumase-archive-inventory.json').read_text());by_name={r['name']:r for r in archive['entries']}
 names=sorted(n for n in by_name if n.startswith('L1-L5FineSegMix-663case/') and n.endswith('_L3_seg.nii.gz') and n.replace('_seg.nii.gz','.nii.gz') in by_name)[:10]
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for name in names:
  path=OUT/Path(name).name;entry=by_name[name]
  if path.exists():
   import zlib
   raw=path.read_bytes();assert len(raw)==entry['size'] and zlib.crc32(raw)==entry['crc32']
  else:raw=read_member(archive,entry);path.write_bytes(raw)
  image=nib.load(path);mask=np.asanyarray(image.dataobj);assert np.isfinite(mask).all() and np.equal(mask,np.floor(mask)).all()
  foreground=mask>0;coords=np.argwhere(foreground);contact=np.any((coords==0)|(coords==np.array(mask.shape)-1),axis=1)
  values,counts=np.unique(mask,return_counts=True)
  row={'member':name,'local_path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'crc32':entry['crc32'],'shape':list(mask.shape),'spacing_mm':[float(v) for v in image.header.get_zooms()],'label_voxels':{str(int(v)):int(c) for v,c in zip(values,counts)},'all_seven_labels_present':set(values)==set(range(8)),'boundary_contact_voxels':int(contact.sum()),'foreground_bounds_inclusive':[coords.min(0).tolist(),coords.max(0).tolist()]}
  row['fully_inside_array']=not row['boundary_contact_voxels'];rows.append(row);print(Path(name).name,row['boundary_contact_voxels'],'edge-contact voxels',flush=True)
  report={'selection_rule':'First ten lexicographically ordered paired L3 annotations; all inspected results retained.','rows':rows,'label_semantics_verified':False,'source_masks_modified':False,'clinical_approval':False,'runtime_promoted':False,'qualification':'Absence of boundary contact is a crop-screen criterion, not proof of complete or accurate anatomical labels.'};(DOC/'lumase-crop-screen.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
