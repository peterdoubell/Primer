"""Pin only reviewed SPL source bytes plus the five separately authored viewer files."""
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from primer.spl_limbic_reference import ATLAS, IDENTIFIER, PREFIX, SOURCE_COMMIT, SOURCE_MANIFEST_SHA256, SOURCE_REVIEW_SHA256, APPROVAL_FLAGS, BINDINGS, expected_files


def main():
    base=ROOT/'web/anatomy'/ATLAS
    review_raw=(ROOT/'docs/spl-limbic-source-review-20261016/source-review.json').read_bytes()
    if hashlib.sha256(review_raw).hexdigest()!=SOURCE_REVIEW_SHA256:raise ValueError('Pinned SPL source review changed')
    review=json.loads(review_raw)
    source={row['file']:row for row in review['lossless_transport']['files']}
    if len(source)!=83 or review['lossless_transport']['manifest_sha256']!=SOURCE_MANIFEST_SHA256:
        raise ValueError('SPL source review scope differs')
    files={}
    for p in sorted(base.rglob('*')):
        if p.is_symlink() or (not p.is_file() and not p.is_dir()):raise ValueError('SPL runtime must contain regular files/directories')
        if p.is_file():
            raw=p.read_bytes(); name=str(p.relative_to(base))
            files[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    if set(files)!=expected_files() or len(files)!=88:raise ValueError('SPL runtime file scope differs')
    for name,row in source.items():
        if files[name]!={'sha256':row['sha256'],'bytes':row['bytes']}:raise ValueError('Reviewed SPL source bytes changed: '+name)
    item={'id':IDENTIFIER,'modality':'Native T1/T2 MRI and limbic source-label boundaries',
          'coordinate_context':'source-native-mri-and-separate-label-grid-in-declared-RAS',
          'title':'Limbic anatomy in original MRI and source-label boundaries',
          'src':PREFIX+'index.html','manifest_url':PREFIX+'manifest.json',
          'sha256':files['index.html']['sha256'],'manifest_sha256':SOURCE_MANIFEST_SHA256,
          'caption':'Explore the SPL atlas’s original T1/T2 MRI and twelve left/right labels for the hippocampus, amygdala, fornix, mammillary body, parahippocampal gyrus and mammillothalamic tract. The default surfaces follow every exposed categorical voxel face, retaining small components. Separately selectable original publisher surfaces can differ substantially, especially at the fornices. This single-subject research atlas supplies source anatomy context; it does not supply separate CA fields or subiculum, patient registration, diagnostic validation or complete reporting anatomy.',
          'attribution':'SPL-PNL/NAC Brain Atlas: Michael Halle, Florin Talos, Marianna Jakab, Nikos Makris, Dominic Meier, Laurence Wald, Bruce Fischl, Ron Kikinis and collaborators. Source commit '+SOURCE_COMMIT+'. Original MRI/label sample bytes and original VTK coordinate, normal and strip bits are preserved. Primer’s marked adaptations are lossless transport, display windowing and exact categorical cell boundaries; full source notices and 3D Slicer Agreement terms accompany the viewer.',
          'source_url':'https://www.openanatomy.org/atlas-pages/atlas-spl-nac-brain.html',
          'publication_url':'https://github.com/mhalle/spl-brain-atlas/tree/'+SOURCE_COMMIT,
          'license':'3D Slicer Contribution and Software License Agreement v1.0, Part B and applicable Part C',
          'license_url':'https://www.openanatomy.org/atlas-pages/slicer-license.html',
          'source_grain':{'kind':'single-subject anatomical research atlas','subject_count':1,'MRI':'native 0.75 mm T1/T2','categorical_labels':'separate native 1 mm Int16 source grid','selected_label_classes':12,'original_producer_surfaces':12,'default_surface':'exact categorical voxel-cell boundaries','separately_labelled_CA_fields_or_subiculum':False},
          'source_grant':{'publisher_explicitly_applies_license_to_data':True,'terms_url':PREFIX+'LICENSE.txt','attribution_url':PREFIX+'ATTRIBUTION.txt','marked_derived_version':True,'reuse_terms':'Part B permits proprietary incorporation subject to all license conditions; retain the full terms, required Brigham notice, applicable third-party notices and research-use/clinical-application language. No institutional endorsement is implied.'},
          'bound_source_ids':[IDENTIFIER],**{flag:False for flag in APPROVAL_FLAGS}}
    data={'schema_version':1,'source_repository':'https://github.com/mhalle/spl-brain-atlas','source_commit':SOURCE_COMMIT,
          'source_review_sha256':hashlib.sha256(review_raw).hexdigest(),'bindings':{key:[IDENTIFIER] for key in sorted(BINDINGS)},
          'inspectors':{IDENTIFIER:item},'files':files}
    registry=ROOT/'data/radiology/spl-limbic-reference.json'
    raw=(json.dumps(data,indent=2)+'\n').encode();registry.write_bytes(raw)
    digest=hashlib.sha256(raw).hexdigest(); helper=ROOT/'primer/spl_limbic_reference.py'
    code,n=re.subn(r"REGISTRY_SHA256 = '[^']+'","REGISTRY_SHA256 = '"+digest+"'",helper.read_text())
    if n!=1:raise ValueError('SPL registry pin anchor differs')
    helper.write_text(code)
    print(json.dumps({'registry_sha256':digest,'files':len(files),'bytes':sum(row['bytes'] for row in files.values())}))

if __name__=='__main__':main()
