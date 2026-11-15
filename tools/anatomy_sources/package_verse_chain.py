"""Preserve the complete VerSe source surfaces in browser-readable mesh files."""
from pathlib import Path
import base64,gzip,hashlib,json,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/msk-verse521/browser-parts'


def build():
    audit=json.loads((ROOT/'docs/msk-verse-source-review/chain-surface-audit.json').read_text())
    OUT.mkdir(parents=True,exist_ok=True);parts={};rows=[]
    for row in audit['levels']:
        source=ROOT/row['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256']
        mesh=np.load(source);original=mesh['vertices_world_mm'];vertices=np.ascontiguousarray(original,dtype='<f4');faces=np.ascontiguousarray(mesh['faces'],dtype='<u4')
        assert np.array_equal(vertices.astype(np.float64),original)
        assert np.isfinite(vertices).all() and faces.max()<len(vertices)
        normals=np.zeros_like(original);tri=original[faces];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        for corner in range(3):np.add.at(normals,faces[:,corner],cross)
        length=np.linalg.norm(normals,axis=1);assert np.all(length>0)
        normals=np.asarray(normals/length[:,None],dtype='<f4')
        raw=struct.pack('<4sII',b'BP3D',len(vertices),faces.size)+vertices.tobytes()+normals.tobytes()+faces.tobytes()
        name='verse521-'+row['level'].lower()+'.bin.gz';path=OUT/name;path.write_bytes(gzip.compress(raw,mtime=0))
        restored=gzip.decompress(path.read_bytes());magic,n,k=struct.unpack('<4sII',restored[:12]);assert magic==b'BP3D' and len(restored)==12+n*24+k*4
        assert np.array_equal(np.frombuffer(restored,dtype='<f4',count=n*3,offset=12).reshape(-1,3).astype(np.float64),original)
        assert np.array_equal(np.frombuffer(restored,dtype='<u4',offset=12+n*24).reshape(-1,3),mesh['faces'])
        ident='verse521-'+row['level'].lower();parts[ident]={'id':ident,'name':row['level']+' · source label '+str(row['label']),'file':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'decoded_sha256':hashlib.sha256(raw).hexdigest(),'vertices':n,'triangles':k//3,'bounds':row['world_bounds_mm'],'source_label':row['label'],'source_surface_sha256':row['sha256'],'clinical_fidelity':'unverified'}
        rows.append({'level':row['level'],'source_surface_sha256':row['sha256'],'compressed_sha256':parts[ident]['sha256'],'decoded_sha256':parts[ident]['decoded_sha256'],'position_conversion_error_mm':0,'all_positions_identical':True,'all_faces_identical':True,'unit_normal_max_error':float(np.max(np.abs(np.linalg.norm(normals.astype(float),axis=1)-1))),'triangles':k//3})
    lows=np.array([p['bounds'][0] for p in parts.values()]);highs=np.array([p['bounds'][1] for p in parts.values()]);lo=lows.min(0);hi=highs.max(0)
    manifest={'dataset':'VerSe sub-verse521 · T1–L5 source surfaces','source_url':'https://github.com/anjany/verse','source_dataset_doi':'https://doi.org/10.17605/OSF.IO/T98FZ','source_files':audit['source_files'],'license':'CC BY-SA 4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/','coordinate_system':{'basis':'RAS','units':'millimetres','unit_meters':0.001,'display_basis':'native-ras-to-x-left-y-superior-z-anterior','registration':'Original shared CT affine; no cross-atlas registration'},'parts':parts,'regions':{'spine':{'title':'T1–L5 · source CT case','side':'midline','parts':[{'id':k,'layer':'bone'} for k in parts],'layers':[['bone','Source vertebrae']],'source_up_range':[float(lo[2]-1),float(hi[2]+1)],'focus_bounds':[lo.tolist(),hi.tolist()]}},'total_triangles':sum(r['triangles'] for r in rows),'clinical_approval':False,'runtime_promoted':False,'limitations':['Whole-vertebra labels only: no separately verified reportable substructures.','Source segmentation boundary accuracy, pathology and normality remain unverified.','T7 diagonal connectivity, T12 enclosed-background boundary and Lewiner helper approximations are retained.','No discs, ligaments, cartilage, nerves or other soft-tissue geometry is supplied.'],'adaptation':'Lossless positions and topology repacked as BP3D; area-weighted unit normals generated for lighting only; gzip transport.'}
    manifest['viewer_notes'] = manifest['limitations'] + [manifest['adaptation'], 'Attribution: Sekuboyina et al. (2021); Liebl and Schinz et al. (2021); Löffler et al. (2020). Full citations in ATTRIBUTION.md.']
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    attribution=(ROOT/'output/msk-verse521/t1-l5/ATTRIBUTION.md').read_text()+'\nBrowser packaging: original world positions and faces preserved exactly; area-weighted unit normals generated for lighting. No source components removed.\n'
    (OUT/'ATTRIBUTION.md').write_text(attribution)
    viewer_source=(ROOT/'web/radiology-detailed-anatomy.js').read_text()
    assert viewer_source.count('  const ATLASES = {')==1 and viewer_source.count('  const RANGES = {')==1
    viewer=viewer_source.replace('  const ATLASES = {','  const ATLASES = {\n    verse521: "./",').replace('  const RANGES = {','  const RANGES = {\n    spine: [-500, -36],')
    (OUT/'anatomy-viewer.js').write_text(viewer)
    (OUT/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VerSe T1–L5 source model</title><style>body{margin:0;padding:24px;background:#101820;color:#e9eef1;font:16px system-ui}main{max-width:1100px;margin:auto}a{color:#8bd9f2}p{line-height:1.5}</style><main><h1>VerSe T1–L5 source model</h1><p>Seventeen whole-vertebra source labels in their shared CT coordinates. Anatomical boundary accuracy remains under review. Bone substructures and soft tissues are not separately represented.</p><p><a href="../review/index.html">Inspect matching CT and original labels</a> · <a href="ATTRIBUTION.md">Source attribution and adaptation</a> · <a href="manifest.json">Geometry provenance</a></p><div id="model"></div></main><script src="anatomy-viewer.js"></script><script>document.getElementById('model').append(PrimerDetailedAnatomy.render({family:'spine',atlas:'verse521',initialCropped:false,populationNote:'CT case sub-verse521. No normality, population representativeness or injury-simulation claim.'}));</script></html>''')
    assets={'manifest':manifest,'meshes':{p['file']:base64.b64encode((OUT/p['file']).read_bytes()).decode() for p in parts.values()}}
    embedded=viewer.replace('const r = await fetch(url);', 'const r = new Response(JSON.stringify(JSON.parse(document.getElementById("source-assets").textContent).manifest));')
    fetch_mesh='const response = await fetch(part.file);'
    assert embedded.count(fetch_mesh)==1
    embedded=embedded.replace(fetch_mesh, 'const encoded = JSON.parse(document.getElementById("source-assets").textContent).meshes[part.file]; const bytes = Uint8Array.from(atob(encoded), c => c.charCodeAt(0)); const response = new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip")));')
    embedded=embedded.replace('JSON.parse(document.getElementById("source-assets").textContent)', 'reviewAssets')
    embedded=embedded.replace('  "use strict";', '  "use strict";\n  const reviewAssets = JSON.parse(document.getElementById("source-assets").textContent);',1)
    assert 'fetch(' not in embedded
    page=(OUT/'index.html').read_text().replace('<script src="anatomy-viewer.js"></script>', '<script id="source-assets" type="application/json">'+json.dumps(assets,separators=(',',':')).replace('<','\\u003c')+'</script><script>'+embedded.replace('</script','<\\/script')+'</script>')
    # Manifest and attribution remain separately downloadable in the package;
    # all geometry required for rendering is embedded in this standalone page.
    (OUT/'standalone.html').write_text(page)
    report={'renderer_source_sha256':hashlib.sha256(viewer_source.encode()).hexdigest(),'review_renderer_sha256':hashlib.sha256(viewer.encode()).hexdigest(),'standalone_file':'output/msk-verse521/browser-parts/standalone.html','standalone_sha256':hashlib.sha256(page.encode()).hexdigest(),'standalone_renderer_sha256':hashlib.sha256(embedded.encode()).hexdigest(),'renderer_changes':'Offline atlas/spine registry entries; standalone variant reads embedded manifest and decompresses embedded mesh bytes. Production viewer unchanged.','parts':rows,'total_triangles':manifest['total_triangles'],'position_and_topology_preservation':'Exact roundtrip equality for every saved vertex and triangle','clinical_approval':False,'runtime_promoted':False}
    (ROOT/'docs/msk-verse-source-review/browser-mesh-package.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Packaged',len(rows),'vertebrae;',report['total_triangles'],'triangles; all source vertices and faces preserved exactly.')


if __name__=='__main__':build()
