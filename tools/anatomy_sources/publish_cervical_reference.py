"""Publish checked C1/C2 source bytes as a limited reference, not certification."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'output/msk-cervical-bones'
DEST=ROOT/'web/anatomy/msk-cervical'

def build():
    original=json.loads((SOURCE/'manifest.json').read_text())
    if {p['name'] for p in original['parts'].values()}!={'Atlas (C1)','Axis (C2)'}:raise ValueError('Unexpected cervical selection')
    parts={}
    for identifier,p in original['parts'].items():
        source=(SOURCE/p['file']).resolve()
        if not source.is_relative_to(SOURCE.resolve()):raise ValueError('Source path leaves package')
        data=source.read_bytes()
        if hashlib.sha256(data).hexdigest()!=p['sha256']:raise ValueError('Changed bone geometry')
        parts[identifier]={**p,'file':'/app/anatomy/msk-cervical/'+source.name,'regions':['cervical']}
    DEST.mkdir(parents=True,exist_ok=True)
    for p in parts.values():shutil.copyfile(SOURCE/Path(p['file']).name,DEST/Path(p['file']).name)
    lo,hi=original['bounds']
    result={**original,'status':'Limited source-bone reference; clinical fidelity unverified','parts':parts,
      'regions':{'cervical':{'title':'C1/C2 bones · limited reference','side':'midline','parts':[{'id':k,'layer':'bone'} for k in parts],'layers':[['bone','Bones']],'source_up_range':[lo[1]-.5,hi[1]+.5],'focus_bounds':[lo,hi]}},
      'viewer_notes':['Atlas and axis source-bone surfaces only, in their original shared coordinates. No fitting, smoothing or mesh repair.',
      'The occipital bone is excluded because of unresolved source topology defects. Ligaments, cartilage, pannus, erosions and neural structures are not supplied by this reference. It cannot establish clinical stability.',
      'Closed topology and preserved geometry do not prove anatomical fidelity. Fine articular and attachment anatomy remains unverified.',
      'BodyParts3D, The Database Center for Life Science (source lineage); Z-Anatomy contributors. Adapted source meshes: CC BY-SA 4.0.']}
    (DEST/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    for file in ['ATTRIBUTION.md','SOURCE-LICENSE.txt']:shutil.copyfile(SOURCE/file,DEST/file)
    attribution=DEST/'ATTRIBUTION.md'
    attribution.write_text(attribution.read_text().replace('This offline package','This limited source reference'))
    print('Published two limited source-bone references; no clinical approval.')
if __name__=='__main__':build()
