"""Reproduce grouped SPL reporting metadata and optionally its exact cell meshes.

Source arrays remain in spl-nac-limbic. No resampling or source cleanup occurs.
"""
from pathlib import Path
import gzip
import hashlib
import json
import re
import sys
import numpy as np
from scipy.ndimage import label as connected

ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/'docs/spl-reporting-source-review-20261016'
ASSETS=ROOT/'web/anatomy/spl-nac-reporting'
SHARED=ROOT/'web/anatomy/spl-nac-limbic'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def read(name):return json.loads(gzip.decompress((DOCS/name).read_bytes()))
def save(name,value):
    (ASSETS/name).write_text(json.dumps(value,indent=2)+'\n')
def build(rebuild=False):
    base_raw=(SHARED/'manifest.json').read_bytes()
    assert sha(base_raw)=='204f87b6d88a9570eb34664497a1462a5d8bba1afa0c2f7abe1cdf11082de2e6'
    base=json.loads(base_raw);source=base['labelVolume'];encoded=(SHARED/source['file']).read_bytes();raw=gzip.decompress(encoded)
    assert sha(encoded)==source['gzipSHA256'] and sha(raw)==source['decodedSHA256']
    array=np.frombuffer(raw,dtype=source['dtype']).reshape(source['shape'],order='F');affine=np.asarray(source['voxelToRAS'])
    inventory=read('source-inventory.json.gz');catalog={row['code']:row for row in inventory['records']}
    package=read('boundary-package.json.gz');assert package['sourceCommit']==base['sourceCommit']
    labels={row['code']:dict(row) for row in package['labels']};meshes={row['code']:dict(row) for row in package['labelMeshes']}
    assert len(labels)==len(meshes)==207
    for row in base['labels']:
        if row['code'] not in labels:
            c=catalog[row['code']]
            labels[row['code']]={'code':row['code'],'name':row['name'],'sourceName':row['sourceName'],'color':row['color'],
                'metadataLabel':c['metadata'].get('label') if c['metadata'] else None,'sourceDeclaredNameDisagreement':c['source_declared_name_disagreement'],
                'sourceVoxelCount':c['voxel_count'],'focusSourceIJK':c['focus_label_ijk'],'focusRAS':c['focus_RAS_mm']}
            mesh=dict(next(m for m in base['labelMeshes'] if m['code']==row['code']));mesh['sharedSource']='spl-nac-limbic';meshes[row['code']]=mesh
    hierarchy={row['code']:row for row in read('independent-requirements.json.gz')['cerebellar_model_hierarchy']}
    for code,row in labels.items():
        c=catalog[code];cells=np.argwhere(array==code);assert len(cells)==row['sourceVoxelCount']==c['voxel_count']
        low=cells.min(0);high=cells.max(0)+1;slices=tuple(slice(int(a),int(b)) for a,b in zip(low,high))
        component,n=connected(array[slices]==code,np.ones((3,3,3),dtype='u1'))
        records=[]
        for number in range(1,n+1):
            points=np.argwhere(component==number)+low;centroid=points.mean(0);focus=points[np.argmin(((points-centroid)**2).sum(1))]
            world=(affine@np.r_[focus,1])[:3];assert array[tuple(focus)]==code
            world_points=np.einsum('nj,ij->ni',points,affine[:3,:3])+affine[:3,3]
            assert np.isfinite(world_points).all()
            records.append({'sourceVoxelCount':len(points),'focusSourceIJK':focus.tolist(),'focusRAS':world.tolist(),
                            'voxelCenterBoundsRAS':[world_points.min(0).tolist(),world_points.max(0).tolist()]})
        records.sort(key=lambda item:(-item['sourceVoxelCount'],item['focusSourceIJK']))
        assert [item['sourceVoxelCount'] for item in records]==c['components_26']['sizes_descending']
        row['components26']=records;row['componentSizes26']=[item['sourceVoxelCount'] for item in records]
        row['components6']=c['components_6']['sizes_descending'];row['sourceSliceRanges']=c['required_native_inspection']['whole_label_slice_ranges']
        row['sourceHierarchy']=hierarchy.get(code,{}).get('directly_evidenced_zone_names',[])
        row['hierarchyExtrapolated']=False
        row['interpretation']='Original categorical source class. Exact cells and components do not independently validate biological borders or continuity.'
        for volume in base['volumes'].values():
            native=np.rint((np.linalg.inv(np.asarray(volume['voxelToRAS']))@np.r_[row['focusRAS'],1])[:3]).astype(int)
            assert np.all(native>=0) and np.all(native<volume['shape'])
            ras=(np.asarray(volume['voxelToRAS'])@np.r_[native,1])[:3];back=np.rint((np.linalg.inv(affine)@np.r_[ras,1])[:3]).astype(int)
            assert array[tuple(back)]==code
    groups=read('requirements.json.gz')['groups']
    titles={'orientation-and-source-grids':'Orientation and source grids','basal-ganglia':'Deep grey relationships','thalamic-parts':'Thalamic source parts','capsules-and-white-matter':'White matter and capsule gaps','callosal-septal-commissural':'Callosal, septal and commissural anatomy','brainstem':'Brainstem levels','cerebellum':'Cerebellar parcels and nuclei','ventricular-system':'Ventricular relationships','cortex-and-lobes':'Cortical localisation','sulcal-landmarks':'Sulcal source gaps','cisterns-and-extra-axial':'Cistern and extra-axial gaps','vascular-localisation':'Vascular localisation gaps'}
    descriptions={
      'orientation-and-source-grids':'Move through all three native planes. Read the edge labels, physical RAS coordinate and native sample indices; the MRI and label grids have separate affines.',
      'basal-ganglia':'Compare caudate11 with putamen12, then the external and internal pallidal source parts13/25. Use paired surfaces and selected overlays to connect the named objects with the native slices. Claustrum and subthalamic labels are adjacent context, not interchangeable basal-ganglia names.',
      'thalamic-parts':'Inspect each named thalamic source part on the MRI, and compare it with caudate11 or third ventricle24. The supplied set includes lamina and geniculate bodies; it is not a demonstrated whole-thalamus partition.',
      'capsules-and-white-matter':'Compare hemisphere white matter2/41 with adjacent deep-grey labels using the comparison selector. This broad source class cannot identify the separate internal-capsule limbs.',
      'callosal-septal-commissural':'Compare corpus callosum3004, septum96 and anterior commissure142 with third ventricle24. Inspect the retained small source components individually, including the remote anterior-commissure component.',
      'brainstem':'Compare the source midbrain region40, residual pons35 and medulla61 in sagittal and axial views. Select fourth ventricle15 or aqueduct19 as comparison context; preserve the source partial/residual qualifications.',
      'cerebellum':'Compare the named cerebellar source parcels and nuclei with fourth ventricle15. The displayed zone names come only from recorded source hierarchy paths; combined I/II and FaGE classes remain combined.',
      'ventricular-system':'Trace the separate lateral ventricles4/43, temporal horns5/44, third ventricle24, aqueduct19 and fourth ventricle15 through native slices. Compare selected cavities with caudate11 or hippocampus17; source connectivity does not establish physiological patency.',
      'cortex-and-lobes':'Locate the named source parcel in axial, coronal and sagittal views, then compare a neighbouring parcel. These parcels are not complete whole-lobe or sulcal-boundary masks.',
      'sulcal-landmarks':'The source lists model-only sulcal curves, but those original geometry bytes have not been acquired and reviewed for this viewer. The MRI remains available; no curve is fabricated from label cells.',
      'cisterns-and-extra-axial':'Inspect native MRI context. Distinct cistern and extra-axial-space classes are absent here, so this group supplies no invented surfaces.',
      'vascular-localisation':'Inspect the native source images with their modality limits. This atlas reference supplies no validated arterial or venous lumen or vascular-territory boundaries.'}
    for group in groups:
        group['title']=titles[group['id']];group['activity']=re.sub(r'\b(caudate|putamen|parts|matter|callosum|septum|commissure|region|pons|medulla|ventricle|aqueduct|ventricles|horns|hippocampus)(\d+(?:/\d+)*)',r'\1 (\2)',descriptions[group['id']])
        group['codes']=group['available_distinct_current_label_codes'];assert all(code in labels for code in group['codes'])
        group['completeReportingRequirementApproved']=False
    groups.append({'id':'limbic-context','title':'Limbic source context','codes':[r['code'] for r in base['labels']],
        'reporting_requirement':'Hippocampal, amygdalar, fornical, cingulate and hypothalamic source context',
        'activity':'Compare a hippocampal source label with the temporal horn and inspect the fornical source components. These labels do not supply separate hippocampal CA fields or establish biological tract continuity.',
        'missing_or_unresolved_structures':['Separate CA fields and subiculum are absent from these categorical source classes.'],
        'semantic_limits':['Publisher processed surfaces remain available separately in the twelve-structure source viewer.'],
        'completeReportingRequirementApproved':False})
    if rebuild:
        from tools.anatomy_sources import spl_limbic_label_boundary as boundary
        boundary.RESEARCH=DOCS
        def write(name,decoded):
            packed=gzip.compress(decoded,compresslevel=9,mtime=0);(ASSETS/name).write_bytes(packed)
            return {'file':name,'byteLength':len(decoded),'gzipBytes':len(packed),'gzipSHA256':sha(packed),'decodedSHA256':sha(decoded)}
        rebuilt=boundary.prepare_label_boundaries(array,affine,package['labels'],source['source'],write)
        for mesh in rebuilt:
            assert mesh['gzipSHA256']==meshes[mesh['code']]['gzipSHA256']
    for mesh in meshes.values():
        directory=SHARED if mesh.get('sharedSource') else ASSETS
        for row in [mesh,mesh['faceProvenance']]:
            packed=(directory/row['file']).read_bytes();decoded=gzip.decompress(packed)
            assert sha(packed)==row['gzipSHA256'] and sha(decoded)==row['decodedSHA256'] and len(decoded)==row['byteLength']
    result={'schemaVersion':1,'source':base['source'],'sourceCommit':base['sourceCommit'],'sourceCoordinateSystem':'RAS','sourceCoordinateUnits':'mm',
        'sharedSourceManifestSHA256':sha(base_raw),'volumes':{k:{**v,'sharedSource':'spl-nac-limbic'} for k,v in base['volumes'].items()},
        'labelVolume':{**source,'sharedSource':'spl-nac-limbic'},'labels':sorted(labels.values(),key=lambda r:r['code']),
        'labelMeshes':sorted(meshes.values(),key=lambda r:r['code']),'groups':groups,'defaultGroup':'basal-ganglia',
        'generatedBoundaryPayloadCount':207,'sharedBoundaryPayloadCount':len(labels)-207,'additionalSourceClassCount':len(labels)-len(base['labels']),'previouslyAvailableSourceClassCount':len(base['labels']),'sourceLicense':base['license'],
        'clinicalApproval':False,'completeReportingAnatomyApproved':False,'normalPopulationAtlas':False,'currentPatientRegistration':False,'newFittedTransforms':False,
        'missingClassesAreNotFabricated':True,'allComponentsRetained':True}
    save('manifest.json',result)
    print(json.dumps({'classes':len(labels),'groups':len(groups),'newMeshes':207,'sharedMeshes':len(labels)-207,'manifestSHA256':sha((ASSETS/'manifest.json').read_bytes())}))
if __name__=='__main__':build('--rebuild-meshes' in sys.argv)
