"""Make the preserved partial MRI contour envelopes available to the reader."""
from pathlib import Path
import gzip,hashlib,json,shutil,struct
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'output/msk-lumbosacral-sub03/surface-candidates';DEST=ROOT/'web/anatomy/liu-lumbosacral-sub03'


def main():
    original=json.loads((SOURCE/'manifest.json').read_text());assert set(original['parts'])=={'cord','dura'} and original['license']=='CC BY 4.0' and original['clinical_approval'] is False
    audit=json.loads((ROOT/'docs/msk-lumbosacral-nerve-source-review/open-envelope-loft-audit.json').read_text());assert len(audit['parts'])==2
    parts={};DEST.mkdir(parents=True,exist_ok=True)
    for key,part in original['parts'].items():
        path=(SOURCE/part['file']).resolve();assert path.parent==SOURCE.resolve();raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==part['sha256'];decoded=gzip.decompress(raw);magic,n,k=struct.unpack('<4sII',decoded[:12]);assert magic==b'BP3D' and len(decoded)==12+n*24+k*4 and n==part['vertices'] and k==part['triangles']*3
        source_audit=next(r for r in audit['parts'] if r['category']==key);assert source_audit['boundary_matches_only_first_last_rings'] and source_audit['all_sampled_ring_positions_preserved']
        shutil.copyfile(path,DEST/path.name);parts[key]={**part,'file':'/app/anatomy/liu-lumbosacral-sub03/'+path.name,'layer':key,'regions':['lumbosacral-neural']}
    region=original['regions']['spine'];manifest={**original,'parts':parts,'regions':{'lumbosacral-neural':{**region,'title':'MRI-derived cord and dural contours · partial'}},'case_id':'sub-03','runtime_promoted':True,'status':'Partial source reference; anatomical validation pending','derivation':'Original LPS source controls, interpreted with stated fresh Slicer 5.4 cardinal defaults and joined between adjacent planes. No end caps, smoothing or cross-subject fitting.','source_reconstruction_sha256':audit['source_reconstruction_sha256'],'viewer_notes':[
        'Partial contour envelopes from one lumbosacral MRI case. The original finite source endpoints remain open.',
        'Between-plane surfaces are derived from source contours under documented interpolation assumptions. Anatomical boundary accuracy remains under review.',
        'The dural contour envelope has no measured wall thickness. No rootlets, nerve tubes, gray/white matter compartments or complete CSF volume are supplied.',
        'Use the source MRI and the reporting checklist to assess structures beyond this reference. This model does not depict trauma, compression or instability.',
        'Liu, Zhang, Zhou, Xu, Chu and Jia (2024), Figshare collection 10.6084/m9.figshare.c.7372564. Original data CC BY 4.0. Adaptations: stated-default curve reconstruction, open contour loft and display normals.'
    ]}
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(DEST/'ATTRIBUTION.md').write_text('# MRI contour-envelope reference\n\nJionghui Liu, Wenqi Zhang, Yuxing Zhou, Linhao Xu, Yinghua Chu and Fumin Jia (2024). Dataset: https://doi.org/10.6084/m9.figshare.c.7372564. Original MRI: https://doi.org/10.6084/m9.figshare.26403595.v1. Original annotations: https://doi.org/10.6084/m9.figshare.26403442.v1. CC BY 4.0: https://creativecommons.org/licenses/by/4.0/.\n\nAdapted from source sub-03 contours under documented fresh Slicer 5.4 defaults. Adjacent-plane triangulated envelopes retain the interpreted source points, open endpoints and shared LPS coordinates. Display normals generated for lighting. Anatomical boundary accuracy and full reporting coverage remain unverified. The study article licence is distinct; no article figure or generated nerve tube was adapted.\n')
    config=ROOT/'data/radiology/source-anatomy-references.json';entries=json.loads(config.read_text()) if config.exists() else {}
    entries['ra.thoracolumbar-fractures']=[{'id':'liu-sub03-neural','label':'MRI-derived cord and dural contours · partial','atlas':'liu-lumbosacral-sub03','family':'lumbosacral-neural','manifest_url':'/app/anatomy/liu-lumbosacral-sub03/manifest.json','manifest_sha256':hashlib.sha256((DEST/'manifest.json').read_bytes()).hexdigest(),'initial_layer':'cord','initial_cropped':False,'population_note':'Partial cord and dural contour envelopes from MRI source case sub-03. Their endpoints and interpolation assumptions limit anatomical coverage. Assess conus, cauda equina, roots and compression interfaces separately using the acquired images.'}]
    image_source=ROOT/'docs/msk-lumbosacral-nerve-source-review/cord-dura-default-curve-review.png'
    image_dest=ROOT/'web/reference-media/liu-lumbosacral-sub03/cord-dura-source-review.png';image_dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(image_source,image_dest);image_data=image_dest.read_bytes();width,height=struct.unpack('>II',image_data[16:24])
    entries['ra.thoracolumbar-fractures'][0]['source_image']={'id':'liu-sub03-cord-dura-mri-review','src':'/app/reference-media/liu-lumbosacral-sub03/'+image_dest.name,'sha256':hashlib.sha256(image_data).hexdigest(),'width':width,'height':height,'title':'Source MRI and contour comparison','alt':'Native CISS MRI source case sub-03 at slices 14, 40 and 79, beside original contour controls and fresh-default curve reconstructions.','caption':'The source MRI shows the lowest supplied cord contour, an intermediate slice and the final image plane. Original controls and reconstructed curves make the source limits inspectable. Anatomical boundary validation remains pending.','attribution':'Liu, Zhang, Zhou, Xu, Chu and Jia (2024), Figshare collection 10.6084/m9.figshare.c.7372564. CC BY 4.0. Native-image crop/window and contour overlays added for review.','source_url':'https://doi.org/10.6084/m9.figshare.c.7372564','license_url':'https://creativecommons.org/licenses/by/4.0/'}
    config.write_text(json.dumps(entries,indent=2)+'\n');print('Added two preserved partial source surfaces to the local reader assets.')


if __name__=='__main__':main()
