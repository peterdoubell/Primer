"""Record pinned source evidence and bounded coordinate/transport verification."""
import gzip
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.anatomy_sources.spl_limbic_source import RESEARCH,SOURCE,PROPOSAL,REVIEW,COMMIT,sha,require,deterministic_gzip


def main():
    manifest_raw=(PROPOSAL/'manifest.json').read_bytes(); manifest=json.loads(manifest_raw)
    manifest_sha=sha(manifest_raw)
    REVIEW.mkdir(exist_ok=True,parents=True)
    proofs={}
    for filename in ['transport-proof.json','spatial-audit.json','label-boundary-proof.json','coordinate-core-proof.json']:
        raw=(RESEARCH/filename).read_bytes(); data=json.loads(raw)
        pin=data.get('manifest_sha256',data.get('transport_manifest_sha256'))
        require(pin in (None,manifest_sha),'A proof describes a different transport manifest')
        (REVIEW/filename).write_bytes(raw); proofs[filename]={'file':filename,'sha256':sha(raw)}
    for filename in ['LICENSE.txt','ATTRIBUTION.txt','SOURCE-README.md','SOURCE-LICENSE.md']:
        shutil.copyfile(PROPOSAL/filename,REVIEW/filename)
    (REVIEW/'transport-manifest.json').write_bytes(manifest_raw)
    archives=[]
    def archive(path,name,url=None):
        raw=path.read_bytes(); packed=deterministic_gzip(raw); destination=REVIEW/'source-evidence'/name
        destination.parent.mkdir(exist_ok=True,parents=True); destination.write_bytes(packed)
        require(gzip.decompress(destination.read_bytes())==raw,'Evidence archive changed original response bytes')
        archives.append({'file':str(destination.relative_to(REVIEW)),'url':url,'storage':'lossless gzip; raw response is not executable project HTML/source',
                         'stored_bytes':len(packed),'stored_sha256':sha(packed),'decoded_bytes':len(raw),'decoded_sha256':sha(raw)})
    acquisition=json.loads((RESEARCH/'coordinate-evidence/acquisition.json').read_text())
    for row in acquisition:
        path=RESEARCH/'coordinate-evidence'/row['path']
        require(sha(path.read_bytes())==row['sha256'],'Coordinate authority response changed')
        archive(path,row['path']+'.gz',row['url'])
    for row in json.loads((RESEARCH/'external-metadata/primary-pages-acquisition.json').read_text()):
        if row['path'] not in ['spl-publisher.html','slicer-license.html']:continue
        path=RESEARCH/'external-metadata'/row['path']
        require(sha(path.read_bytes())==row['sha256'],'Publisher response changed')
        archive(path,row['path']+'.gz',row['url'])
    for relative in ['LICENSE.md','README.md','slicer/brain-atlas.mrml','slicer/colortables/hncma-atlas-lut.ctbl','labelinfo/brain-atlas-labels-with-metadata.tsv','labelinfo/hncma-atlas-lut.tsv']:
        archive(SOURCE/relative,relative.replace('/','--')+'.gz','https://raw.githubusercontent.com/mhalle/spl-brain-atlas/'+COMMIT+'/'+relative)
    for name,url in [('spl-commit.json','https://api.github.com/repos/mhalle/spl-brain-atlas/commits/'+COMMIT),('spl-tree.json','https://api.github.com/repos/mhalle/spl-brain-atlas/git/trees/'+COMMIT+'?recursive=1')]:
        archive(RESEARCH/'external-metadata'/name,name+'.gz',url)
    (REVIEW/'archive-storage.json').write_text(json.dumps({'schema_version':1,'files':archives},indent=2)+'\n')
    boundary=json.loads((RESEARCH/'label-boundary-proof.json').read_text())
    spatial=json.loads((RESEARCH/'spatial-audit.json').read_text())
    coordinates=json.loads((RESEARCH/'coordinate-core-proof.json').read_text())
    files=[{'file':str(p.relative_to(PROPOSAL)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(PROPOSAL.rglob('*')) if p.is_file()]
    payloads=[*manifest['volumes'].values(),manifest['labelVolume']]
    for row in manifest['meshes']:
        payloads.extend([row,row['originalNormals'],row['originalStrips'],row['originalVTK']])
    for row in manifest['labelMeshes']:payloads.extend([row,row['faceProvenance']])
    for row in payloads:
        raw=(PROPOSAL/row['file']).read_bytes(); decoded=gzip.decompress(raw)
        require(sha(raw)==row['gzipSHA256'] and sha(decoded)==row['decodedSHA256'] and len(decoded)==row['byteLength'],'Published transport payload differs')
    commit=json.loads((RESEARCH/'external-metadata/spl-commit.json').read_text())
    review={'schema_version':1,'source_repository':'https://github.com/mhalle/spl-brain-atlas','source_commit':COMMIT,
            'source_commit_tree':commit['commit']['tree']['sha'],'source_publisher':'https://www.openanatomy.org/atlas-pages/atlas-spl-nac-brain.html',
            'source_case':'One normal volunteer, publisher-described healthy 42-year-old male. Automatic parcellation with manual segmentation of many structures; a processed anatomical teaching atlas, not a population or pathology dataset.',
            'source_identity_verification':'Original selected file byte length and Git blob SHA1 verified against the pinned Git tree; source SHA256 retained. Raw native NRRD files reconstruct exactly from retained headers and untouched gzip bodies.',
            'legacy_coordinate_convention':{'model_space':'RAS millimetres','scene_version':'Slicer4.4.0','evidence':'Main MRML model nodes have no parent transform. Slicer v4.4.0 vtkMRMLModelStorageNode .vtk branch reads original vtkPolyData without LPS sign conversion. Official historical Slicer coordinate guidance and contemporaneous 2017 developer guidance specify model RAS coordinates.',
                                            'modern_default_warning':'Later Slicer versions can treat unmarked VTK as LPS. Applying that default to this 2017 Slicer4.4 scene would introduce an incorrect sign flip.',
                                            'NRRD_space':'LPS','LPS_to_RAS':[[-1,0,0,0],[0,-1,0,0],[0,0,1,0],[0,0,0,1]],'registration_fit':False},
            'native_grids':{name:{key:row[key] for key in ['shape','dtype','storageOrder','voxelToLPS','voxelToRAS','source','decodedSHA256','finiteSampleCount']} for name,row in {**manifest['volumes'],'labels':manifest['labelVolume']}.items()},
            'half_voxel_warning':manifest['halfVoxelWarning'],'selected_labels':manifest['labels'],
            'lossless_transport':{'manifest_sha256':manifest_sha,'native_sample_count':55115776,'original_mesh_count':12,'original_strip_derived_triangles':sum(x['triangleCount'] for x in manifest['meshes']),
                                  'exact_label_mesh_count':12,'exact_label_voxel_count':sum(x['sourceVoxelCount'] for x in manifest['labelMeshes']),
                                  'exact_label_exposed_faces':sum(x['exposedFaceCount'] for x in manifest['labelMeshes']),
                                  'exact_label_triangles':sum(x['triangleCount'] for x in manifest['labelMeshes']),
                                  'HVX1_header_bytes':16,'all_original_samples_and_original_vertices_normals_strips_preserved':True,
                                  'no_source_grid_resampling_coordinate_fit_smoothing_or_cleanup':True,'payload_hash_checks':len(payloads),'files':files},
            'surface_distinction':{'default':'labelMeshes: exact categorical voxel-cell boundaries, preserving source staircase, all small components, cavities and nonmanifold contacts. Their exactness is to categorical source cells, not independent biological truth.',
                                   'comparison':'meshes: original producer-processed models, with original positions/normals/strips unchanged. They are not exact label boundaries.',
                                   'measured_limit':manifest['originalSurfaceWarning'],'left_fornix_outlier':'The 12.2374 mm label-face-center distance is an isolated one-voxel source component; the main 739-voxel component maximum is 3.4536 mm. No component is removed.'},
            'license':{'name':manifest['license'],'publisher_explicitly_applies_to_atlas_data':True,'terms_file':'LICENSE.txt','attribution_file':'ATTRIBUTION.txt',
                       'proprietary_incorporation_permitted_by_part_B_2':True,'conditions':'Retain full Part B terms and required Brigham preface with copies/sublicenses/user documentation; retain applicable source attribution/copyright/third-party notices; clearly mark modified forms; no institutional endorsement. Part B research-purpose and clinical-use language is retained unchanged. Part C applies.',
                       'not_CC_BY_or_CC_BY_SA':True,'no_unrelated_third_party_rights_granted':True},
            'verification':{'proofs':proofs,'coordinate_native_planes':len(coordinates['complete_planes']),'coordinate_pixel_and_label_pairs':coordinates['total_compared_plane_pixels'],
                            'source_probes_per_MRI':coordinates['all_selected_label_derived_MRI_probes']['T1']['count'],'source_original_vertices':coordinates['inverseChecks'][0]['allOriginalVertices'],
                            'source_label_exact_face_oracle_all_12_passed':True,'source_surface_distances_audited':True},
            'unsupported_claims':['No separately labelled subiculum or CA fields are created from the broad hippocampus/parahippocampal labels.','No replacement for disease examples, histology, patient-specific registration, diagnostic validation, whole-module clinical approval or complete reporting anatomy.','No claim that automatic/manual source segmentation or producer surface geometry is anatomically error-free.'],
            'clinical_approval':False,'whole_module_complete':False,'whole_primer_goal_complete':False}
    (REVIEW/'source-review.json').write_text(json.dumps(review,indent=2)+'\n')
    lines=['# SPL-PNL/NAC native coordinate source review','',
           'This package preserves the original native T1/T2 MRI, the full categorical label volume and 12 original publisher surfaces. It also provides separate exact voxel-cell boundary surfaces for the 12 selected label classes. The exact boundaries are the default; original surfaces remain comparisons. No clinical or whole-module approval is asserted.','',
           'The source is the [SPL/NAC atlas](https://www.openanatomy.org/atlas-pages/atlas-spl-nac-brain.html), pinned to [commit '+COMMIT+'](https://github.com/mhalle/spl-brain-atlas/tree/'+COMMIT+'). It is one normal volunteer and combines automatic parcellation with manual segmentation. Original Git blobs, lengths and SHA256 values are recorded.','',
           '## Coordinate convention','',
           'Original model vertices are **legacy Slicer RAS millimetres**. The main MRML scene is Slicer4.4.0 and contains no selected model or volume parent transform. The contemporaneous VTK reader passes original polydata through unchanged. Modern Slicer unmarked-VTK defaults must not be applied retrospectively. The NRRD volumes explicitly declare LPS; multiplying their declared affines by diag(-1,-1,1,1) yields matrices exactly matching the main MRML scene. There is no fitted alignment.','',
           'Native T1 and T2 contain 288 × 320 × 208 Float32 samples at 0.75 mm. Labels contain 256³ Int16 samples at 1 mm. All 55,115,776 source samples remain bit-exact. Axis 0 is fastest; storage offset is i + nx × (j + ny × k). Each grid has its own affine. The unused 1 mm MRI resample starts at (-127.5,-127.5,127.5) LPS while labels start at (-128,-128,128), a half-voxel offset; equal array dimensions would not justify index alignment.','',
           '## Surfaces and measured limits','',
           'The derived surfaces expose every original categorical cell face whose neighbor has a different code, including every cavity and tiny component. RAS cell corners are exact half-integers. Each face becomes two outward triangles; independent full-grid face-set checks and signed enclosed volume equal to every source voxel count pass for all classes. Corner/edge contacts that are nonmanifold in the categorical source remain present. These boundaries are exact to the source segmentation, not an independent anatomical validation.','',
           'Original VTK surfaces are separately retained without deleting, welding, smoothing, repairing or rounding vertices, normals, strips or implied triangles. They differ from the labels, especially the fornix. Distances below are sampled in both directions: every original vertex to the nearest exposed label-cell quad, and every exposed label-cell face center to the nearest original triangle. They are **not continuous Hausdorff bounds**.','',
           '| Code | Source label | Voxels | Exact faces | Original vertex → label boundary max (mm) | Label face center → original surface max (mm) |','|---|---|---:|---:|---:|---:|']
    for lab,sp,bo in zip(manifest['labels'],spatial['rows'],boundary['rows']):
        lines.append(f"| {lab['code']} | {lab['name']} | {lab['voxelCount']} | {bo['face_count']} | {sp['all_original_vertices_to_categorical_cell_boundary']['max_mm']:.4f} | {sp['all_exposed_face_centers_to_original_triangle_surface']['max_mm']:.4f} |")
    lines.extend(['','The left fornix 12.2374 mm outlier is an isolated one-voxel label component; the 739-voxel main component reaches 3.4536 mm. It is preserved. The original left/right fornix vertices reach 5.4833/7.1654 mm from their categorical boundaries. These discrepancies are disclosed instead of altering either source to force agreement.','',
                  '## Transport and independent checks','',
                  'The 16-byte HVX1 header is magic, vertex count, triangle count, reserved0. Float32LE RAS positions and Uint32LE triangles follow. Original normal and length-prefixed strip arrays have separate lossless sidecars, and exact original VTK files are retained as gzip archives. Native MRI/label gzip bodies are unchanged; retained NRRD headers reconstruct the exact original files. The package adds 37,892 categorical boundary triangles alongside all 29,130 original strip-derived triangles.','',
                  'Independent Python/NumPy source-array checks agree with the JavaScript coordinate core on 34 complete native planes (2,439,168 source pixels and label overlays), 18,514 source-label-derived MRI probes per contrast, all 16,369 original mesh vertices through coordinate round trips, and 36 half-voxel field-boundary cases. This verifies coordinate/data behavior, not clinical correctness or browser visual quality.','',
                  '## License and remaining limits','',
                  'The publisher expressly applies the **3D Slicer Agreement v1.0, Part B** to this atlas. Full terms, the required Brigham notice, original source notices and marked-conversion details accompany both data and this review. Part B permits proprietary incorporation subject to its terms; it retains research-use and clinical-application restrictions/disclaimers, third-party obligations and no-endorsement conditions. This is not a Creative Commons license.','',
                  'The broad hippocampus and parahippocampal labels do not establish separately labelled subiculum or CA fields. No disease, histology, population variation, patient registration, whole-module clinical approval or complete reporting coverage follows from this package.','',
                  'Publisher HTML and historical source-code evidence are archived losslessly as gzip, with raw and stored hashes in archive-storage.json. The proof files and complete manifest are listed in source-review.json.','',
                  'Manifest SHA256: `'+manifest_sha+'`.',''])
    (REVIEW/'README.md').write_text('\n'.join(lines))
    inventory=[{'file':str(p.relative_to(REVIEW)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(REVIEW.rglob('*')) if p.is_file() and p.name!='artifact-index.json']
    (REVIEW/'artifact-index.json').write_text(json.dumps({'schema_version':1,'files':inventory},indent=2)+'\n')
    print(json.dumps({'review':str(REVIEW),'manifest_sha256':manifest_sha,'payloads_verified':len(payloads),'transport_files':len(files),'transport_bytes':sum(x['bytes'] for x in files),'review_files':len(inventory),'source_review_sha256':sha((REVIEW/'source-review.json').read_bytes())}))

if __name__=='__main__':main()
