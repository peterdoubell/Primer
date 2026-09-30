"""Embed separate observer surfaces with a common MRI-coordinate viewing frame."""
from pathlib import Path
import base64,hashlib,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/msk-rootlet-sub-amu02';DOC=ROOT/'docs/msk-rootlet-source-review'


def main():
    agreement=json.loads((DOC/'annotation-surface-comparison.json').read_text())
    assert all(r['consensus_matches_at_least_two_votes'] for r in agreement['same_class_rater_support']), 'Consensus display statement requires re-review'
    manifests=json.loads((OUT/'manifests.json').read_text());meshes={}
    original_annotations=list(manifests)
    cells=json.loads((DOC/'voxel-cell-boundary-comparison.json').read_text())
    for row in cells['parts']:
        key=row['annotation']+'_cells'
        if key not in manifests:
            manifest=json.loads(json.dumps(manifests[row['annotation']]))
            manifest['parts']={}
            manifest['regions']['cervical']['parts']=[]
            manifest['viewer_notes'][0]='Boundary faces of occupied source voxel cells; no detail is inferred inside a voxel.'
            manifest['viewer_notes'][1]='Edge and corner contacts in the annotations can form non-manifold surfaces; these contacts remain in this reference.'
            manifests[key]=manifest
        original=next(part for part in manifests[row['annotation']]['parts'].values() if part['source_label']==row['label'])
        part=dict(original,id=original['id']+'-cells',file='cell-boundaries/'+Path(row['file']).name,sha256=row['sha256'],vertices=row['topology']['unique_exact_positions'],triangles=row['topology']['triangles'],bounds=row['bounds_ras_mm'])
        bounds=part['bounds'];low=[-bounds[1][0],bounds[0][2],bounds[0][1]];high=[-bounds[0][0],bounds[1][2],bounds[1][1]]
        frame=manifests[key]['review_display_bounds']
        assert all(a<=b for a,b in zip(frame[0],low)) and all(a<=b for a,b in zip(high,frame[1]))
        manifests[key]['parts'][part['id']]=part
        manifests[key]['regions']['cervical']['parts'].append({'id':part['id'],'layer':'rootlets'})
    for key,m in manifests.items():
        observer=key.removesuffix('_cells')
        display='STAPLE consensus' if observer=='staple' else 'Rater '+observer[-1]
        display+=' · voxel reference' if key.endswith('_cells') else ' · interpolated surface'
        m['dataset']='Spine Generic sub-amu02 · '+display
        m['regions']['cervical']['title']=display+' · annotated dorsal rootlet regions'
        for p in m['parts'].values():
            raw=(OUT/p['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256'];meshes[p['file']]=base64.b64encode(raw).decode()
    source=(ROOT/'web/radiology-detailed-anatomy.js').read_text();renderer=source.replace('  const ATLASES = {','  const ATLASES = {\n'+''.join('    '+json.dumps(k)+': '+json.dumps(k+'/')+',\n' for k in manifests))
    renderer=renderer.replace('  "use strict";','  "use strict";\n  const reviewAssets = JSON.parse(document.getElementById("source-assets").textContent);',1)
    renderer=renderer.replace('const r = await fetch(url);','const r = new Response(JSON.stringify(reviewAssets.manifests[url.split("/")[0]]));').replace('const response = await fetch(part.file);','const bytes = Uint8Array.from(atob(reviewAssets.meshes[part.file]), c => c.charCodeAt(0)); const response = new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip")));')
    old='const view = sourceView({ ...options, atlas }, data, region);';assert renderer.count(old)==1
    renderer=renderer.replace(old,'const view = { id: "shared-frame", title: region.title, range: region.source_up_range, focusBounds: data.review_display_bounds, fixedFrame: true, camera: { yaw: Math.PI, pitch: 0 }, initialLayer: "rootlets", boneIds: [], note: "Shared MRI coordinates and common full-set framing; no geometric registration or fitting applied." };')
    assert renderer.count('const fixedBounds = state.cropped')==1
    renderer=renderer.replace('const fixedBounds = state.cropped','const fixedBounds = sourcePreset?.fixedFrame && !state.isolated ? sourcePreset.focusBounds : state.cropped')
    renderer=renderer.replace('["Lateral", lateralYaw, 0], ["Medial", -lateralYaw, 0]','[side === "midline" ? "Right lateral" : "Lateral", lateralYaw, 0], [side === "midline" ? "Left lateral" : "Medial", -lateralYaw, 0]')
    assert 'fetch(' not in renderer
    assets=json.dumps({'manifests':manifests,'meshes':meshes},separators=(',',':')).replace('<','\\u003c')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Manual rootlet annotations · source comparison</title><style>body{margin:0;padding:24px;background:#101820;color:#e9eef1;font:16px system-ui}main{max-width:1100px;margin:auto}p{line-height:1.5}select{font:inherit;padding:9px;margin:0 8px}a{color:#8fdef5}</style><main><h1>Manual dorsal-rootlet annotations · source comparison</h1><p>Spine Generic sub-amu02. Compare four manual annotations and their STAPLE consensus in the same MRI coordinates and full-set frame. These are surfaces of labelled voxels, not proof of complete nerve anatomy.</p><label>Annotation <select id="observer"><option value="staple">STAPLE consensus</option><option value="rater1">Rater 1</option><option value="rater2">Rater 2</option><option value="rater3">Rater 3</option><option value="rater4">Rater 4</option></select></label><label>Boundary view <select id="boundary"><option value="iso">Interpolated label surface</option><option value="cells">Voxel reference</option></select></label><p id="boundary-note"></p><p id="annotation-note" role="status"></p><div id="host"></div><p>Source: <a href="https://doi.org/10.5281/zenodo.4299140">Spine Generic</a>; rootlet annotations described by <a href="https://doi.org/10.1162/imag_a_00218">Valošek et al. (2024)</a>. Attribution and <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> terms retained; repository metadata also says CC0. Adaptation: label-isosurface and voxel-boundary extraction and review rendering; no smoothing or invented annotation.</p></main>'''
    page+='<script id="source-assets" type="application/json">'+assets+'</script><script>'+renderer.replace('</script','<\\/script')+'</script><script>const observer=document.getElementById("observer"),boundary=document.getElementById("boundary"); function show(){document.getElementById("boundary-note").textContent=boundary.value==="cells"?"The voxel reference preserves occupied-label volume. Cell contacts can form singular boundaries; subvoxel anatomy is unresolved.":"These interpolated surfaces enclose 8–23% less volume than occupied label cells in this case. The difference is representation sensitivity, not a measured anatomical error.";document.getElementById("annotation-note").textContent=observer.value==="rater3"?"No T1 label voxels were supplied by this rater. This does not mean the anatomy is absent.":observer.value==="staple"?"Consensus derived from the raters; it is not an independent manual annotation. In this case it matches voxels selected by at least two of four raters.":"Original manual annotation. Differences from other raters are retained.";document.getElementById("host").replaceChildren(PrimerDetailedAnatomy.render({family:"cervical",atlas:observer.value+(boundary.value==="cells"?"_cells":""),initialLayer:"rootlets",initialCropped:false,populationNote:"Dorsal C2–T1 source label groups only. Individual rootlets, sides and ventral anatomy are not separately inferred."}));}observer.addEventListener("change",show);boundary.addEventListener("change",show);show();</script></html>'
    (OUT/'comparison.html').write_text(page);(OUT/'review-renderer.js').write_text(renderer)
    report={'file':str((OUT/'comparison.html').relative_to(ROOT)),'sha256':hashlib.sha256(page.encode()).hexdigest(),'production_renderer_sha256':hashlib.sha256(source.encode()).hexdigest(),'review_renderer_sha256':hashlib.sha256(renderer.encode()).hexdigest(),'annotations':original_annotations,'representations':['interpolated_surface','voxel_cell_reference'],'source_surfaces':len(meshes),'common_display_bounds':next(iter(manifests.values()))['review_display_bounds'],'changes':'Offline observer registry, embedded sources, common non-isolated viewing bounds, explicit lateral labels for midline anatomy. Production renderer unchanged.','clinical_approval':False,'runtime_promoted':False};(DOC/'comparison-viewer.json').write_text(json.dumps(report,indent=2)+'\n');print('Embedded',len(meshes),'source surfaces;',len(page),'characters.')


if __name__=='__main__':main()
