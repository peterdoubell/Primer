"""Embed the two reviewed open-envelope candidates in a standalone review page."""
from pathlib import Path
import base64,hashlib,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/msk-lumbosacral-sub03/surface-candidates';DOC=ROOT/'docs/msk-lumbosacral-nerve-source-review'


def main():
    manifest=json.loads((OUT/'manifest.json').read_text());assert set(manifest['parts'])=={'cord','dura'} and not manifest['runtime_promoted'];meshes={}
    for part in manifest['parts'].values():
        path=(OUT/part['file']).resolve();assert path.parent==OUT.resolve();raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==part['sha256'];meshes[part['file']]=base64.b64encode(raw).decode()
    original=(ROOT/'web/radiology-detailed-anatomy.js').read_text();renderer=original.replace('  const ATLASES = {','  const ATLASES = {\n    "source-review": "./",').replace('  const RANGES = {','  const RANGES = {\n    spine: [-1000,0],')
    renderer=renderer.replace('const r = await fetch(url);','const r = new Response(JSON.stringify(reviewAssets.manifest));').replace('const response = await fetch(part.file);','const encoded = reviewAssets.meshes[part.file]; const bytes = Uint8Array.from(atob(encoded), c => c.charCodeAt(0)); const response = new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip")));')
    renderer=renderer.replace('  "use strict";','  "use strict";\n  const reviewAssets = JSON.parse(document.getElementById("source-assets").textContent);',1)
    renderer=renderer.replace('["Lateral", lateralYaw, 0], ["Medial", -lateralYaw, 0]','[side === "midline" ? "Right lateral" : "Lateral", lateralYaw, 0], [side === "midline" ? "Left lateral" : "Medial", -lateralYaw, 0]')
    assert 'fetch(' not in renderer
    assets=json.dumps({'manifest':manifest,'meshes':meshes},separators=(',',':')).replace('<','\\u003c')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Source MRI cord and dura · open-envelope review</title><style>body{margin:0;padding:24px;background:#101820;color:#e9eef1;font:16px system-ui}main{max-width:1100px;margin:auto}p{line-height:1.5}a{color:#9adcf4}</style><main><h1>Source MRI cord and dura · open-envelope review</h1><p>Sub-03 source contours interpreted with explicit fresh Slicer 5.4 defaults, joined only between adjacent MRI planes. Both ends remain open at the supplied contours. These are partial contour envelopes, not verified complete tissue volumes.</p><p>Choose an envelope or select a structure and isolate it. The dural envelope does not encode a measured wall thickness. No nerve tubes, rootlets or missing tip have been added.</p><div id="model"></div><p>Original data: Jionghui Liu, Wenqi Zhang, Yuxing Zhou, Linhao Xu, Yinghua Chu and Fumin Jia (2024), <a href="https://doi.org/10.6084/m9.figshare.c.7372564">Figshare collection</a>, <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Adaptations: stated-default curve reconstruction, uncapped triangulated joins and display normals. Source anatomical accuracy remains under review.</p></main>'''
    page+='<script id="source-assets" type="application/json">'+assets+'</script><script>'+renderer.replace('</script','<\\/script')+'</script><script>document.getElementById("model").append(PrimerDetailedAnatomy.render({family:"spine",atlas:"source-review",initialLayer:"cord",initialCropped:false,populationNote:"MRI source case sub-03. No normality, complete neural anatomy or compression-simulation claim."}));</script></html>'
    (OUT/'standalone.html').write_text(page)
    report={'file':str((OUT/'standalone.html').relative_to(ROOT)),'sha256':hashlib.sha256(page.encode()).hexdigest(),'production_renderer_sha256':hashlib.sha256(original.encode()).hexdigest(),'review_renderer_sha256':hashlib.sha256(renderer.encode()).hexdigest(),'changes':'Offline atlas/spine registration, embedded-data loader, explicit right/left camera labels for midline anatomy. Production viewer unchanged.','parts':{k:{'sha256':v['sha256'],'triangles':v['triangles']} for k,v in manifest['parts'].items()},'clinical_approval':False,'runtime_promoted':False}
    (DOC/'open-envelope-viewer.json').write_text(json.dumps(report,indent=2)+'\n');print('Embedded source envelopes;',len(page),'characters.')


if __name__=='__main__':main()
