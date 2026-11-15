#!/usr/bin/env python3
"""Package original regional sinonasal label interfaces as a limited source reference."""
import argparse
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from PIL import Image
from tools.anatomy_sources.render_nasalseg_surface_alignment import read_surface, COLORS
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT/'docs/nasalseg-native-source-review'
ATLAS = 'nasalseg-p001'
FAMILY = 'sinonasal-source'
OUT = ROOT/'web/anatomy'/ATLAS
SOURCE = 'https://zenodo.org/records/13893419'
GRANT = 'https://creativecommons.org/licenses/by/4.0/'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def package(root):
    report = json.loads((PROOF/'source-label-surface-review.json').read_text())
    grid = json.loads((PROOF/'original-case-grid-review.json').read_text())
    metadata_path = root/'zenodo-13893419.json'; metadata = json.loads(metadata_path.read_text())
    if sha(metadata_path.read_bytes()) != grid['source_record_sha256'] or metadata['metadata']['license']['id'] != 'cc-by-4.0':
        raise ValueError('Verified original source grant changed')
    authors = ', '.join(c['name'] for c in metadata['metadata']['creators'])
    attribution = authors+'. NasalSeg Dataset for Nasal Cavity and Paranasal Sinuses Segmentation from CT Images. DOI 10.5281/zenodo.13893419. CC BY 4.0.'
    OUT.mkdir(parents=True,exist_ok=True)
    parts, checks = {}, []
    for row in report['models']:
        vertices, faces = read_surface(root/'P001-source-surfaces'/row['file'], row)
        stored = vertices.astype('<f4'); error = float(np.max(np.abs(stored.astype(float)-vertices)))
        if error > 4e-5: raise ValueError('Unexpected source position transport loss')
        triangles = vertices[faces]; normals = np.zeros_like(vertices)
        cross = np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        for corner in range(3): np.add.at(normals,faces[:,corner],cross)
        lengths = np.linalg.norm(normals,axis=1); zero = lengths == 0; normals[~zero] /= lengths[~zero,None]
        fraw = faces.astype('<u4').tobytes(); praw = vertices.astype('<f8').tobytes()
        identifier = ATLAS+'-label'+str(row['source_label'])
        # Preserve double precision source geometry for independent transport readback.
        (PROOF/(identifier+'-positions.f64.gz')).write_bytes(gzip.compress(praw,mtime=0))
        (PROOF/(identifier+'-triangles.u32.gz')).write_bytes(gzip.compress(fraw,mtime=0))
        decoded = struct.pack('<4sII',b'BP3D',len(stored),faces.size)+stored.tobytes()+normals.astype('<f4').tobytes()+fraw
        encoded = gzip.compress(decoded,mtime=0); filename = identifier+'.bin.gz'; (OUT/filename).write_bytes(encoded)
        readback = gzip.decompress((OUT/filename).read_bytes())
        if readback[12+len(stored)*24:] != fraw or not np.array_equal(np.frombuffer(readback,'<f4',len(stored)*3,12).reshape(-1,3),stored):
            raise ValueError('Transport geometry readback differs')
        parts[identifier] = {'id':identifier,'name':row['source_name'].replace('_',' ')+' · source label interface',
            'file':'/app/anatomy/'+ATLAS+'/'+filename,'sha256':sha(encoded),'decoded_sha256':sha(decoded),
            'vertices':len(stored),'triangles':len(faces),'bounds':[stored.min(0).tolist(),stored.max(0).tolist()],
            'source_label':row['source_label'],'source_positions_sha256':sha(praw),'source_triangles_sha256':sha(fraw),
            'source_OBJ_sha256':row['sha256'],'source_components':row['surface_components'],'source_boundary_edges':row['boundary_edges'],
            'clinical_fidelity':'unverified','color':COLORS[row['source_label']],'layer':'source_labels','regions':[FAMILY]}
        checks.append({'id':identifier,'faces_unchanged':True,'maximum_position_conversion_error_declared_mm':error,
                       'zero_display_normals':int(zero.sum()),'sha256':sha(encoded)})
    low = np.min([p['bounds'][0] for p in parts.values()],axis=0); high = np.max([p['bounds'][1] for p in parts.values()],axis=0)
    notes = ['One regional source CT case (P001); patient age and native DICOM orientation are not independently verified. These are five original region-label interfaces, not a complete sinonasal atlas or the anatomy of the patient being reported.',
        'The source grid is 153×205×52 with declared 0.586×0.586×1.5 mm sampling. This does not establish operative thin-bone effective resolution, raw DICOM/HU lineage or full head coverage.',
        'Both original left nasal-cavity components and 98 open nasal-pharynx edges at the acquired boundary are retained. Viewer rotation or uncropped framing cannot restore anatomy outside the scan.',
        'Frontal/ethmoid/sphenoid cells, full drainage routes, bone/mucosal thickness, optic/carotid/nerve/vessel boundaries and lesion or extrasinus extension are not independently represented.',
        'No extra smoothing, padding, repair, capping, decimation or component removal. Sixteen Lewiner ambiguity-resolution vertices remain; source labels are not independent anatomical validation.',
        'Source LPS coordinates are preserved with float32 transport and display normals. Matching CT planes are from this case; other published figures and models are separate patients without registration.',
        'No MRI tissue characterization, calibrated measurements, physiological drainage or unique diagnosis is supplied. '+attribution+' Adaptation: original label-interface extraction, float32/gzip transport, display normals and source CT/contour display. Clinical/anatomical review pending.']
    manifest = {'dataset':'NasalSeg P001 · regional CT label interfaces','source_url':SOURCE,'license':'CC BY 4.0','license_url':GRANT,
        'coordinate_system':{'basis':'LPS','units':'original NRRD-declared millimetres','unit_meters':.001,
                             'display_basis':'native-lps-to-x-left-y-superior-z-anterior','registration':'Original declared NRRD affine; no fitted registration or independently verified raw DICOM'},
        'parts':parts,'regions':{FAMILY:{'title':'Regional sinonasal source labels · partial','side':'bilateral',
            'parts':[{'id':identifier,'layer':'source_labels'} for identifier in parts],
            'layers':[['source_labels','Original region interfaces']],
            'source_up_range':[float(low[2]-1),float(high[2]+1)],'focus_bounds':[low.tolist(),high.tolist()],
            'uncropped_label':'Acquired source extent · scan-truncated'}},
        'viewer_notes':notes,'clinical_approval':False,'anatomical_approval':False,'complete_sinonasal_geometry_verified':False,
        'runtime_promoted':True,'status':'Partial source reference; anatomical validation pending',
        'source_manifest_sha256':sha((PROOF/'source-label-surface-review.json').read_bytes()),
        'total_triangles':sum(p['triangles'] for p in parts.values())}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); manifest_sha = sha((OUT/'manifest.json').read_bytes())
    (OUT/'ATTRIBUTION.md').write_text('# Regional source reference\n\n'+notes[-1]+'\n\n'+'\n\n'.join(notes[:-1])+'\n')
    # Preserve exact reviewed metadata as licence/attribution evidence, separate from article licence.
    (PROOF/'zenodo-13893419.json').write_bytes(metadata_path.read_bytes())
    image_path = ROOT/'web/reference-media'/ATLAS/'source-CT-label-context.png'; image_path.parent.mkdir(parents=True,exist_ok=True)
    display = root/'P001-source-planes.png'; display_proof = json.loads((PROOF/'source-plane-display-review.json').read_text())
    if sha(display.read_bytes()) != display_proof['sha256']: raise ValueError('Reviewed same-case CT display changed')
    image_path.write_bytes(display.read_bytes())
    with Image.open(image_path) as image: width,height = image.size
    source_image = {'src':'/app/reference-media/'+ATLAS+'/'+image_path.name,'sha256':sha(image_path.read_bytes()),'width':width,'height':height,
        'title':'Matching original CT planes and source labels','alt':'Original P001 CT index planes with the five original label contours.',
        'caption':'Three selected planes from the same regional CT, with original mask contours. Declared physical sample aspect retained; display window is in source units, HU calibration unverified. These planes do not establish full operative anatomy or validate all labels.',
        'attribution':attribution+' Adaptation: source-unit window display and original contour overlays.','source_url':SOURCE,'license_url':GRANT}
    entry = {'id':ATLAS+'-source-labels','label':'Regional CT source label interfaces · partial','atlas':ATLAS,'family':FAMILY,
        'manifest_url':'/app/anatomy/'+ATLAS+'/manifest.json','manifest_sha256':manifest_sha,'initial_layer':'source_labels','initial_cropped':False,
        'population_note':' '.join(notes[:4]),'source_image':source_image}
    path = ROOT/'data/radiology/source-anatomy-references.json'; data = json.loads(path.read_text())
    data['ra.mri-sinuses'] = [e for e in data.get('ra.mri-sinuses',[]) if e['id'] != entry['id']]+[entry]; path.write_text(json.dumps(data,indent=2)+'\n')
    (PROOF/'reader-package-review.json').write_text(json.dumps({'parts':checks,'manifest_sha256':manifest_sha,'source_labels_changed':False,
        'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')
    rights = {'name':'CC BY 4.0','url':GRANT,'commercial_use':True,'redistribution':True,'review_status':'verified',
        'evidence_path':'docs/nasalseg-native-source-review/zenodo-13893419.json','evidence_sha256':sha(metadata_path.read_bytes()),
        'attribution':notes[-1],'reviewed_at':'2026-10-07'}
    assets = [{'id':p['id'],'kind':'model','name':p['name'],'local_path':'web/'+p['file'].removeprefix('/app/'),'sha256':p['sha256'],
        'investigation_ids':['ra.mri-sinuses'],'structure_ids':[],'requirement_coverage':{},'source':{'url':SOURCE,'license':rights},
        'anatomical_review':{'status':'pending','reason':'Five regional label interfaces do not establish full bone/drainage/neurovascular/lesion anatomy.'}} for p in parts.values()]
    assets.append({'id':ATLAS+'-CT-source-display','kind':'clinical_image','name':source_image['title'],'local_path':str(image_path.relative_to(ROOT)),
        'sha256':source_image['sha256'],'modality':'CT','investigation_ids':['ra.mri-sinuses'],'structure_ids':[],'requirement_coverage':{},
        'source':{'url':SOURCE,'license':rights},'pixel_provenance':{'source_voxels_changed':False,'adaptation':'Source-unit window and original mask contours'},
        'anatomical_review':{'status':'pending','reason':'Three source planes do not establish full anatomy or clinical approval.'}})
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=ATLAS+'-')
    print('Five original label interfaces packaged with same-case CT display; complete anatomy/clinical approval remain false')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--source-root',type=Path,required=True)
    package(parser.parse_args().source_root)
