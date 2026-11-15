"""Locate retained VerSe source components against the unchanged mask and CT."""
from pathlib import Path
import hashlib
import json
import numpy as np
import nibabel as nib
from scipy import ndimage, sparse
from scipy.sparse.csgraph import connected_components
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
CASE = Path('/tmp/primer-msk-sources/verse/verse521')
OUT = ROOT / 'docs/msk-verse-source-review'


def main():
    audit = json.loads((OUT/'chain-surface-audit.json').read_text())
    for filename, digest in audit['source_files'].items():
        assert hashlib.sha256((CASE/filename).read_bytes()).hexdigest() == digest
    ct = nib.load(CASE/'sub-verse521_dir-ax_ct.nii.gz')
    seg = nib.load(CASE/'sub-verse521_dir-ax_seg-vert_msk.nii.gz')
    assert ct.shape == seg.shape and np.array_equal(ct.affine, seg.affine)
    mask = np.asanyarray(seg.dataobj)
    values = np.asanyarray(ct.dataobj)
    entry = next(x for x in audit['levels'] if x['level'] == 'T12')
    path = ROOT/entry['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
    mesh = np.load(path)
    faces, voxel, world = mesh['faces'], mesh['vertices_voxel'], mesh['vertices_world_mm']
    edges = np.concatenate([faces[:,[0,1]], faces[:,[1,2]], faces[:,[2,0]]])
    graph = sparse.coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(voxel),len(voxel)))
    count, labels = connected_components(graph,directed=False)
    components = []
    for component in range(count):
        included = labels[faces[:,0]] == component
        assert np.all(labels[faces[included]] == component)
        ids = np.unique(faces[included])
        xyz = world[faces[included]] - world[ids].mean(0)
        volume = float(np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6)
        components.append({'triangles':int(included.sum()),'vertices':len(ids),
                           'voxel_bounds':[voxel[ids].min(0).tolist(),voxel[ids].max(0).tolist()],
                           'signed_volume_mm3':volume,'vertex_ids':ids.tolist()})
    small = min(components,key=lambda x:x['triangles'])
    assert small['triangles'] == 8 and small['vertices'] == 6
    center = voxel[small['vertex_ids']].mean(0)
    assert np.allclose(center,np.rint(center),rtol=0,atol=1e-7)
    center = np.rint(center).astype(int)
    lo = np.asarray(entry['crop_start']);hi = np.asarray(entry['crop_stop'])
    field = mask[tuple(slice(a,b) for a,b in zip(lo,hi))] == entry['label']
    holes = ndimage.binary_fill_holes(field) & ~field
    hole_labels, _ = ndimage.label(holes,ndimage.generate_binary_structure(3,1))
    hole_id = int(hole_labels[tuple(center-lo)])
    assert hole_id > 0
    cavity_voxels = np.argwhere(hole_labels == hole_id)+lo
    assert len(cavity_voxels) == 1 and np.array_equal(cavity_voxels[0],center)
    assert mask[tuple(center)] == 0 and small['signed_volume_mm3'] < 0
    neighbors = []
    for axis in range(3):
        for delta in [-1,1]:
            point=center.copy();point[axis]+=delta
            neighbors.append({'voxel':point.tolist(),'label':int(mask[tuple(point)])})
    assert all(n['label']==entry['label'] for n in neighbors)
    report={'source_files':audit['source_files'],'surface_sha256':entry['sha256'],
            't12_components':components,'cavity_voxel':center.tolist(),
            'cavity_world_ras_mm':nib.affines.apply_affine(ct.affine,center).tolist(),
            'source_label':int(mask[tuple(center)]),'six_neighbors':neighbors,
            'enclosed_background_component_voxels':len(cavity_voxels),
            'interpretation':'The eight-triangle component is an inward-facing boundary around one enclosed background voxel in the original T12 label; it is not a disconnected foreground island.',
            'clinical_interpretation':'Undetermined. This mask property does not establish a real anatomical cavity, pathology or segmentation error.',
            'source_or_surface_modified':False,'clinical_approval':False,'runtime_promoted':False}
    points=[('T12 enclosed background voxel',center,19),('T7 diagonal foreground connection',np.array([208,144,341]),14)]
    assert mask[tuple(points[1][1])] == 14
    t7 = points[1][1]
    touching=[]
    for offset in np.ndindex(3,3,3):
        delta=np.asarray(offset)-1
        if np.any(delta) and mask[tuple(t7+delta)] == 14:
            touching.append({'offset':delta.tolist(),'nonzero_axes':int(np.count_nonzero(delta))})
    assert touching and not any(n['nonzero_axes']==1 for n in touching)
    report['t7_source_voxel']=t7.tolist()
    report['t7_touching_label_neighbors']=touching
    report['t7_has_face_neighbor']=False
    fig, axes = plt.subplots(2,3,figsize=(12,8))
    records=[];codes=nib.aff2axcodes(ct.affine);opposite={'L':'R','R':'L','A':'P','P':'A','S':'I','I':'S'}
    for row,(title,point,label) in enumerate(points):
        for col,axis in enumerate([2,0,1]):
            slices=[slice(int(p)-10,int(p)+11) for p in point];slices[axis]=int(point[axis])
            image=values[tuple(slices)].T;binary=(mask[tuple(slices)]==label).T
            remaining=[a for a in range(3) if a!=axis];spacing=ct.header.get_zooms();ax=axes[row,col]
            ax.imshow(image,cmap='gray',vmin=-200,vmax=1000,origin='lower',interpolation='nearest',aspect=spacing[remaining[1]]/spacing[remaining[0]])
            ax.contour(np.arange(binary.shape[1]),np.arange(binary.shape[0]),binary,levels=[.5],colors=['cyan'],linewidths=.8)
            ax.plot([10],[10],marker='+',color='#ffcc55',markersize=12)
            for x,y,text in [(.03,.5,opposite[codes[remaining[0]]]),(.97,.5,codes[remaining[0]]),(.5,.97,codes[remaining[1]]),(.5,.03,opposite[codes[remaining[1]]])]:
                ax.text(x,y,text,transform=ax.transAxes,color='#ffcc55',ha='center',va='center')
            ax.set_title(title+'\n'+['Axial','Sagittal','Coronal'][col]);ax.set_axis_off()
            records.append({'level':title[:3].strip(),'axis':axis,'index':int(point[axis]),'center_voxel':point.tolist()})
    fig.suptitle('VerSe sub-verse521 · retained source-mask features',fontsize=15)
    fig.text(.5,.02,'Cyan: original label boundary; gold cross: audited voxel centre. Native planes, nearest-neighbour display.\nNo voxel or surface edits. Display range −200 to 1000 scaled CT values; no clinical conclusion.',ha='center')
    fig.tight_layout(rect=(0,.07,1,.94));fig.savefig(OUT/'retained-components-ct-review.png',dpi=170);plt.close(fig)
    report['review_planes']=records
    (OUT/'retained-component-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['interpretation']);print('Source voxel:',center.tolist(),'signed cavity surface volume:',small['signed_volume_mm3'])


if __name__ == '__main__':
    main()
