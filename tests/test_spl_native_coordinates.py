"""Independent coordinate fixtures; these do not establish clinical validity."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')


def test_native_plane_orientation_and_distinct_label_grid_use_world_coordinates():
    script = """
const c=require('./web/anatomy/spl-nac-limbic/coordinates.js');
const m={shape:[288,320,208],voxelToRAS:[[0,0,-.75,77.625],[-.75,0,0,107.625],[0,-.75,0,119.625],[0,0,0,1]]};
const l={shape:[256,256,256],voxelToRAS:[[0,0,-1,128],[-1,0,0,128],[0,-1,0,128],[0,0,0,1]]};
const points=[];
for(const p of [[0,0,0],[287,319,207],[143,159,103],[100,100,100],[144,160,104]]) {
 const world=c.transform(m.voxelToRAS,p);
 points.push({p,world,inverse:c.transform(c.inverse(m.voxelToRAS),world),label:c.nearestVoxel(c.inverse(l.voxelToRAS),world,l.shape)});
}
const planes=['axial','coronal','sagittal'].map(plane=>{
 const spec=c.planeSpec(m,plane,100),p=c.pixelVoxel(spec,0,0);
 return {spec,topLeft:c.transform(m.voxelToRAS,p),topRight:c.transform(m.voxelToRAS,c.pixelVoxel(spec,spec.width-1,0)),bottomLeft:c.transform(m.voxelToRAS,c.pixelVoxel(spec,0,spec.height-1))};
});
const identity=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]];
console.log(JSON.stringify({points,planes,outside:[[-.50001,0,0],[255.5,0,0],[0,256,0]].map(p=>c.nearestVoxel(identity,p,[256,256,256])),ties:[[-.5,0,0],[.5,0,0],[254.5,0,0]].map(p=>c.nearestVoxel(identity,p,[256,256,256]))}));
"""
    data = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT, text=True))
    for row in data['points']:
        i, j, k = row['p']
        expected = [77.625 - .75*k, 107.625 - .75*i, 119.625 - .75*j]
        assert row['world'] == expected
        assert row['inverse'] == row['p']
        # Derived directly from the published label header: i=128-y,j=128-z,k=128-x.
        x, y, z = expected
        assert row['label'] == [int(128-y+.5), int(128-z+.5), int(128-x+.5)]
        assert row['label'] != row['p'], 'Different native grids must never share voxel indices'
    for row in data['planes']:
        name = row['spec']['plane']
        top, right, bottom = row['topLeft'], row['topRight'], row['bottomLeft']
        horizontal = 1 if name == 'sagittal' else 0
        vertical = 1 if name == 'axial' else 2
        assert right[horizontal] < top[horizontal]
        assert bottom[vertical] < top[vertical]
        assert row['spec']['spacing'] == [.75, .75]
        assert all(right[axis] == top[axis] for axis in range(3) if axis != horizontal)
        assert all(bottom[axis] == top[axis] for axis in range(3) if axis != vertical)
    assert data['outside'] == [None, None, None]
    assert data['ties'] == [[0, 0, 0], [1, 0, 0], [255, 0, 0]]


def test_native_coordinates_reject_oblique_or_invalid_display_requests_and_keep_int16_labels():
    script = """
const assert=require('node:assert/strict'),c=require('./web/anatomy/spl-nac-limbic/coordinates.js');
const identity=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], row={shape:[2,2,2],voxelToRAS:identity};
const image=new Float32Array([1,2,3,4,5,6,7,8]),labels=new Int16Array([0,17,53,100,200,3007,3005,-1]);
assert.equal(c.probe(row,image,row,labels,[1,0,1]).label,3007);
assert.equal(c.probe(row,image,row,labels,[1,1,1]).label,-1);
const bad=[];
for(const run of [()=>c.inverse([[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,1]]),()=>c.planeSpec(row,'axial',2),()=>c.planeSpec(row,'coronal',.5),()=>c.planeSpec({...row,voxelToRAS:[[1,.1,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]},'axial',1),()=>c.probe(row,image,row,labels,[2,0,0])]) {
 try{run();bad.push(false);}catch(e){bad.push(e instanceof RangeError);}
}
console.log(JSON.stringify({bad,sourceSample: c.probe(row,image,row,labels,[1,0,1])}));
"""
    data = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT, text=True))
    assert data['bad'] == [True] * 5
    assert data['sourceSample'] == {'voxel': [1, 0, 1], 'ras': [1, 0, 1], 'value': 6,
                                    'labelVoxel': [1, 0, 1], 'label': 3007}
