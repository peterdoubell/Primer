"""Independent source-array checks of the JavaScript native coordinate implementation."""
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.spl_limbic_source import SOURCE, RESEARCH, PROPOSAL, CODES, parse_nrrd, parse_vtk, sha, require


def main():
    manifest = json.loads((PROPOSAL/'manifest.json').read_text())
    label = parse_nrrd(SOURCE/'slicer/volumes/labels/hncma-atlas.nrrd')
    selected = np.argwhere(np.isin(label['array'], CODES))
    # Explicit source permutation/origin equations, independent of the JavaScript affine inverse.
    ras = 128.-selected[:, [2,0,1]].astype(float)
    image_voxel = np.floor((np.array([107.625,119.625,77.625])-ras[:,[1,2,0]])/.75+.5).astype(int)
    image_voxel = np.unique(image_voxel,axis=0)
    image_ras = np.column_stack([77.625-.75*image_voxel[:,2],107.625-.75*image_voxel[:,0],119.625-.75*image_voxel[:,1]])
    probe_label_voxel = np.floor(128.-image_ras[:,[1,2,0]]+.5).astype(int)
    probe_labels = label['array'][tuple(probe_label_voxel.T)]
    expected_planes, plans, expected_probes = [], [], {}
    sources = {'T1':parse_nrrd(SOURCE/'slicer/volumes/imaging/A1_grayT1.nrrd'),
               'T2':parse_nrrd(SOURCE/'slicer/volumes/imaging/A1_grayT2.nrrd')}
    for name, source in sources.items():
        a=source['array']
        probe_values = a[tuple(image_voxel.T)]
        probe_rows=np.column_stack([image_ras,probe_values,probe_labels]).astype('<f8')
        expected_probes[name]={'count':len(probe_rows),'row_layout':'R,A,S,source MRI float value,source label code as Float64LE','sha256':sha(probe_rows.tobytes())}
        for plane, fixed_axis in [('axial',1),('coronal',0),('sagittal',2)]:
            slices=sorted(set([0,1,a.shape[fixed_axis]//2,a.shape[fixed_axis]-2,a.shape[fixed_axis]-1]+[int(np.median(image_voxel[:,fixed_axis]))]))
            for slice in slices:
                # These are source-native views, expressed directly as NumPy index permutations.
                if plane=='axial':
                    pixels=a[:,slice,:]; yy,xx=np.indices(pixels.shape); ii,jj,kk=yy,np.full_like(yy,slice),xx
                elif plane=='coronal':
                    pixels=a[slice,:,:]; yy,xx=np.indices(pixels.shape); ii,jj,kk=np.full_like(yy,slice),yy,xx
                else:
                    pixels=a[:,:,slice].T; yy,xx=np.indices(pixels.shape); ii,jj,kk=xx,yy,np.full_like(yy,slice)
                li=np.floor(128.-(107.625-.75*ii)+.5).astype(int)
                lj=np.floor(128.-(119.625-.75*jj)+.5).astype(int)
                lk=np.floor(128.-(77.625-.75*kk)+.5).astype(int)
                require(((li>=0)&(li<256)&(lj>=0)&(lj<256)&(lk>=0)&(lk<256)).all(),'Native plane leaves label field')
                overlay=label['array'][li,lj,lk]
                key=f'{name}:{plane}:{slice}'
                plans.append({'name':name,'plane':plane,'slice':slice,'key':key})
                expected_planes.append({'key':key,'width':pixels.shape[1],'height':pixels.shape[0],
                                        'sourcePixelSHA256':sha(pixels.astype('<f4').tobytes(order='C')),
                                        'sourceLabelOverlaySHA256':sha(overlay.astype('<i2').tobytes(order='C'))})
    vertices=[]
    for code in CODES:
        mesh=parse_vtk(next((SOURCE/'slicer/models').glob(f'Model_{code}_*.vtk')))
        vertices.extend(mesh['positions'].astype(float).tolist())
    input_path=RESEARCH/'coordinate-fixtures.json'
    input_path.write_text(json.dumps({'planes':plans,'probeVoxels':image_voxel.tolist(),'meshVertices':vertices}))
    script=RESEARCH/'check-coordinate-core.cjs'
    script.write_text(r'''const fs=require('fs'), zlib=require('zlib'), crypto=require('crypto'), path=require('path');
const root=process.cwd(), base=path.join(root,'.research/limbic-next-20261016'), proposal=path.join(base,'transport-proposal');
const api=require(path.join(root,'web/anatomy/spl-nac-limbic/coordinates.js'));
const m=JSON.parse(fs.readFileSync(path.join(proposal,'manifest.json'))), fixture=JSON.parse(fs.readFileSync(path.join(base,'coordinate-fixtures.json')));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function body(row,Type){const b=zlib.gunzipSync(fs.readFileSync(path.join(proposal,row.file))); return new Type(b.buffer,b.byteOffset,b.byteLength/Type.BYTES_PER_ELEMENT);}
const labels=body(m.labelVolume,Int16Array), labelInverse=api.inverse(m.labelVolume.voxelToRAS), images=Object.fromEntries(['T1','T2'].map(k=>[k,body(m.volumes[k],Float32Array)]));
const planes=fixture.planes.map(plan=>{const row=m.volumes[plan.name], spec=api.planeSpec(row,plan.plane,plan.slice), image=images[plan.name];
const pixels=Buffer.alloc(spec.width*spec.height*4), overlay=Buffer.alloc(spec.width*spec.height*2); let offset=0;
for(let y=0;y<spec.height;y++) for(let x=0;x<spec.width;x++) {const p=api.pixelVoxel(spec,x,y), world=api.transform(row.voxelToRAS,p), lp=api.nearestVoxel(labelInverse,world,m.labelVolume.shape); if(!lp)throw Error('No source label field'); pixels.writeFloatLE(image[api.offset(row.shape,p)],offset*4);overlay.writeInt16LE(labels[api.offset(m.labelVolume.shape,lp)],offset*2);offset++;}
return {key:plan.key,width:spec.width,height:spec.height,sourcePixelSHA256:sha(pixels),sourceLabelOverlaySHA256:sha(overlay)};});
const probes={}; for(const name of ['T1','T2']){const row=m.volumes[name], b=Buffer.alloc(fixture.probeVoxels.length*5*8);let at=0;
for(const p of fixture.probeVoxels){const result=api.probe(row,images[name],m.labelVolume,labels,p);for(const value of [...result.ras,result.value,result.label]){b.writeDoubleLE(value,at);at+=8;}}
probes[name]={count:fixture.probeVoxels.length,row_layout:'R,A,S,source MRI float value,source label code as Float64LE',sha256:sha(b)};}
const inverseChecks=[]; for(const row of [...Object.values(m.volumes),m.labelVolume]){const inverse=api.inverse(row.voxelToRAS);let max=0;for(const p of fixture.meshVertices){const q=api.transform(row.voxelToRAS,api.transform(inverse,p));max=Math.max(max,...q.map((v,i)=>Math.abs(v-p[i])));} inverseChecks.push({volume:row.name,allOriginalVertices:fixture.meshVertices.length,maxRASRoundTripError:max});
for(let axis=0;axis<3;axis++){for(const [position,expected] of [[-.5,true],[-.500000001,false],[row.shape[axis]-.500000001,true],[row.shape[axis]-.5,false]]){const p=[0,0,0];p[axis]=position;const actual=api.nearestVoxel(inverse,api.transform(row.voxelToRAS,p),row.shape)!==null;if(actual!==expected)throw Error('Half voxel bound differs');}}}
console.log(JSON.stringify({planes,probes,inverseChecks,boundaryCases:36}));
''')
    actual=json.loads(subprocess.check_output(['node',str(script)],cwd=ROOT,text=True))
    require(actual['planes']==expected_planes,'JavaScript native plane source pixels or source label overlays differ')
    require(actual['probes']==expected_probes,'JavaScript native source probe value/label/position differs')
    require(max(x['maxRASRoundTripError'] for x in actual['inverseChecks'])<1e-12,'Original vertex round trip exceeded tolerance')
    result={'coordinate_core_file':'web/anatomy/spl-nac-limbic/coordinates.js','coordinate_core_sha256':sha((ROOT/'web/anatomy/spl-nac-limbic/coordinates.js').read_bytes()),
            'manifest_sha256':sha((PROPOSAL/'manifest.json').read_bytes()),'independent_reference':'Original NRRD Float32/Int16 arrays and direct source origin/permutation equations in Python/NumPy, compared to actual Node coordinate API and actual transport bytes.',
            'complete_planes':expected_planes,'all_selected_label_derived_MRI_probes':expected_probes,
            'inverseChecks':actual['inverseChecks'],'half_voxel_boundary_cases':actual['boundaryCases'],
            'total_compared_plane_pixels':sum(x['width']*x['height'] for x in expected_planes),
            'status':'passed','clinical_approval':False}
    (RESEARCH/'coordinate-core-proof.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'passed','planes':len(expected_planes),'pixels':result['total_compared_plane_pixels'],'source_probes_per_MRI':len(image_voxel),'vertices':len(vertices)}))

if __name__=='__main__': main()
