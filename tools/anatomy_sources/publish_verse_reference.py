"""Expose preserved VerSe surfaces and native CT planes with explicit limits."""
from pathlib import Path
import gzip,hashlib,json,shutil,struct
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'output/msk-verse521/browser-parts'
DEST=ROOT/'web/anatomy/verse521'
def digest(data):return hashlib.sha256(data).hexdigest()
def main():
    original=json.loads((SOURCE/'manifest.json').read_text())
    audit=json.loads((ROOT/'docs/msk-verse-source-review/browser-mesh-package.json').read_text())
    assert original['clinical_approval'] is False and original['total_triangles']==798442
    assert len(original['parts'])==17 and all(p['all_positions_identical'] and p['all_faces_identical'] for p in audit['parts'])
    DEST.mkdir(parents=True,exist_ok=True)
    parts={}
    for key,part in original['parts'].items():
        path=(SOURCE/part['file']).resolve();assert path.parent==SOURCE.resolve()
        raw=path.read_bytes();assert digest(raw)==part['sha256'];decoded=gzip.decompress(raw)
        magic,n,k=struct.unpack('<4sII',decoded[:12]);assert magic==b'BP3D' and n==part['vertices'] and k==part['triangles']*3 and len(decoded)==12+n*24+k*4
        shutil.copyfile(path,DEST/path.name)
        parts[key]={**part,'file':'/app/anatomy/verse521/'+path.name,'layer':'bone','regions':['thoracolumbar-source']}
    acquisition_path=ROOT/'docs/msk-verse-source-review/sub-verse521_dir-ax_ct.json'
    acquisition=json.loads(acquisition_path.read_text())
    geometry=json.loads((ROOT/'docs/msk-verse-source-review/case-geometry.json').read_text())
    thickness=float(acquisition['SliceThickness']);assert thickness==geometry['source_acquisition_slice_thickness_mm']
    spacing=json.loads((ROOT/'docs/msk-verse-source-review/full-volume-review-viewer.json').read_text())['voxel_spacing_mm'];assert spacing[2]==geometry['stored_slice_spacing_mm']
    resolution_note=f'Stored CT sample spacing: {spacing[0]:.2f} × {spacing[1]:.2f} × {spacing[2]:.1f} mm. Source acquisition slice thickness: {thickness:g} mm. Sample spacing does not establish effective anatomical resolution; fine endplates, cortices and facets remain unverified.'
    manifest={**original,'parts':parts,'regions':{'thoracolumbar-source':original['regions']['spine']},'runtime_promoted':True,'status':'CT source reference; anatomical boundary review pending','source_acquisition':{'slice_thickness_mm':thickness,'stored_slice_spacing_mm':geometry['stored_slice_spacing_mm'],'metadata_sha256':digest(acquisition_path.read_bytes())},'viewer_notes':[resolution_note]+original['viewer_notes']}
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    attribution=(SOURCE/'ATTRIBUTION.md').read_text().replace('This is an offline review set, not clinically approved anatomy.','This is a source reference available in the reader; anatomical approval remains pending.')
    (DEST/'ATTRIBUTION.md').write_text(attribution)
    volume=ROOT/'output/msk-verse521/review/index.html'
    report=json.loads((ROOT/'docs/msk-verse-source-review/full-volume-review-viewer.json').read_text())
    raw=volume.read_bytes()
    # The saved viewer is tied to the acquired CT/mask through its audit record.
    sha=report.get('viewer_sha256') or report.get('sha256')
    if sha is None:
        sha=report['html_sha256']
    assert digest(raw)==sha
    html=raw.decode();start=html.rfind('<script>');end=html.index('</script>',start)
    script=html[start+len('<script>'):end]
    needle="$('level').append(option)});"
    assert script.count(needle)==1
    script=script.replace(needle,needle+"\nconst requestedLevel=new URLSearchParams(location.search).get('level');const initialLevel=data.levels.findIndex(item=>item.level===requestedLevel);if(initialLevel>=0)$('level').value=String(initialLevel);\n")
    (DEST/'ct-reference.js').write_text(script)
    html=html[:start]+'<script src="/app/anatomy/verse521/ct-reference.js"></script>'+html[end+len('</script>'):]
    anchor='<div class="controls">';assert html.count(anchor)==1
    html=html.replace(anchor,'<p class="source-resolution">'+resolution_note+'</p>\n'+anchor)
    raw=html.encode();(DEST/'ct-reference.html').write_bytes(raw)
    entry={'id':'verse521-bones','label':'CT-derived vertebrae · T1–L5','atlas':'verse521','family':'thoracolumbar-source','manifest_url':'/app/anatomy/verse521/manifest.json','manifest_sha256':digest((DEST/'manifest.json').read_bytes()),'initial_layer':'bone','initial_cropped':False,'population_note':'Whole-vertebra source labels from one CT case, T1–L5. Normality, pathology and separately reportable substructures remain unverified. This CT case is independent of the MRI cord/dura reference; their coordinates must not be combined.','source_volume':{'id':'verse521-native-ct-planes','src':'/app/anatomy/verse521/ct-reference.html','sha256':digest(raw),'source_viewer_sha256':sha,'level_by_part':{key:key.removeprefix('verse521-').upper() for key in parts},'script_sha256':digest(script.encode()),'title':'Inspect matching source CT planes · T1–L5','caption':resolution_note+' Native CT crops spanning each supplied vertebral label and its margin. Select level, plane and slice; adjust the CT window and original-label overlay. These crops do not establish whole-examination or soft-tissue completeness.','attribution':'Sekuboyina et al. (2021), Liebl and Schinz et al. (2021), Löffler et al. (2020). VerSe data, CC BY-SA 4.0. Adaptation: native CT crops, window display and original-label overlays; no source voxels resampled or edited.','source_url':'https://doi.org/10.17605/OSF.IO/T98FZ','license_url':'https://creativecommons.org/licenses/by-sa/4.0/'}}
    path=ROOT/'data/radiology/source-anatomy-references.json';config=json.loads(path.read_text())
    config['ra.thoracolumbar-fractures']=[entry]+[e for e in config['ra.thoracolumbar-fractures'] if e['id']!=entry['id']]
    path.write_text(json.dumps(config,indent=2)+'\n')
    print('Preserved 17 meshes and matching native CT plane viewer; anatomical approval pending.')
if __name__=='__main__':main()
