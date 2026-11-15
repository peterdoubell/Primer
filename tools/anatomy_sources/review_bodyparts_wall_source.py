#!/usr/bin/env python3
"""Preserve available original wall pieces and explicit mirror/fine-layer source gaps."""
import argparse,hashlib,json,shutil
from pathlib import Path


def preserve_selection(root,output):
    from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import Rows
    from tools.anatomy_sources.acquire_bodyparts_wall_upstream import TARGETS
    receipt=json.loads((root/'upstream-acquisition.json').read_text())
    ids={r['id'] for r in receipt['objects']}
    manifest=(root/'FMA2Obj-4.3.txt').read_text()
    selected=[line for line in manifest.splitlines() if line.startswith('#') or line.split('\t')[0] in TARGETS]
    (output/'selected-version-manifest.txt').write_text('\n'.join(selected)+'\n')
    tables={}
    for name in ['obj2FMA-4.3.html','obj2FMA-partof-4.3.html']:
        raw=(root/name).read_bytes();parser=Rows();parser.feed(raw.decode())
        tables[name]={'source_sha256':hashlib.sha256(raw).hexdigest(),'headers':parser.rows[0],
                      'selected_element_rows':[r for r in parser.rows[1:] if len(r)>1 and r[1] in ids]}
    (output/'selected-original-mapping-rows.json').write_text(json.dumps(tables,indent=2)+'\n')


def compare_original_M(root,output):
    import numpy as np
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    receipt=json.loads((output/'acquisition.json').read_text());by_id={r['id']:r for r in receipt['objects']}
    a=(root/'objects/FJ1452.obj').read_bytes();b=(root/'objects/FJ1452M.obj').read_bytes()
    if hashlib.sha256(a).hexdigest()!=by_id['FJ1452']['sha256'] or hashlib.sha256(b).hexdigest()!=by_id['FJ1452M']['sha256']:raise ValueError('Original source geometry differs')
    av,an,af,anf=read_obj(a.decode());bv,bn,bf,bnf=read_obj(b.decode());reflected=av*np.array([-1,1,1])
    exact_set={tuple(v) for v in reflected}=={tuple(v) for v in bv}
    from scipy.spatial import cKDTree
    ab=cKDTree(bv).query(reflected)[0];ba=cKDTree(reflected).query(bv)[0]
    mirror={'source_ids':['FJ1452','FJ1452M'],'source_M_id_retained':True,'original_position_records_exactly_equal':bool(np.array_equal(av,bv)),
            'source_X_reflected_position_sets_exactly_equal':exact_set,'original_vertex_counts':[len(av),len(bv)],'source_triangle_counts':[len(af),len(bf)],
            'maximum_reflected_nearest_vertex_distance_mm':float(max(ab.max(),ba.max())),
            'mean_reflected_nearest_vertex_distances_mm':[float(ab.mean()),float(ba.mean())],
            'nearest_vertex_distance_is_continuous_surface_distance':False,'face_indices_exactly_equal':bool(np.array_equal(af,bf)),
            'normal_indices_exactly_equal':bool(np.array_equal(anf,bnf)),'source_geometry_changed':False,
            'reflection_is_analysis_only_not_source_export_transform':True,'independent_left_right_patient_geometry_verified':False,
            'source_patient_axis_registration_verified':False,'clinical_approval':False,'runtime_promoted':False}
    (output/'original-M-source-comparison.json').write_text(json.dumps(mirror,indent=2)+'\n')


def review(root,output):
    import numpy as np
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import review as geometry,read_obj
    from tools.anatomy_sources.review_bodyparts_source_boundaries import review as boundaries
    from tools.anatomy_sources.audit_bodyparts_bowel_contacts import audit as self_contacts
    from tools.anatomy_sources.render_bodyparts_bowel_review import render
    from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import Rows
    output.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/'upstream-acquisition.json',output/'acquisition.json')
    preserve_selection(root,output)
    geometry(root,output,expected_object_count=5);boundaries(root,output);self_contacts(root,output,expected_object_count=5);render(root,output,single_panel_bottom=.27,sparse_short_axes=True)
    compare_original_M(root,output)
    queries=['rectus abdominis','rectus of abdomen','internal oblique of abdomen','internal abdominal oblique','transversus abdominis','transverse abdominal','rectus sheath','sheath of rectus','fascia transversalis','linea semilunaris']
    found={q:[] for q in queries};metadata={}
    for name in ['obj2FMA-4.3.html','obj2FMA-partof-4.3.html']:
        raw=(root/name).read_bytes();p=Rows();p.feed(raw.decode());metadata[name]={'sha256':hashlib.sha256(raw).hexdigest(),'parsed_rows':len(p.rows)}
        for r in p.rows[1:]:
            if len(r)<8:continue
            for q in queries:
                if q in ' '.join(r[4:6]).lower():found[q].append({'id':r[1],'source_fma':r[3],'source_label':r[4],'source_synonyms':r[5]})
    (output/'source-selection-holds.json').write_text(json.dumps({'source_version':'4.3','metadata':metadata,'named_layer_or_landmark_queries':found,
        'missing_layers_derived_from_outer_muscle':False,'mirrored_source_is_independent_patient_side':False,
        'clinical_approval':False,'runtime_promoted':False,'limits':['Searches are limited to the selected two source label/synonym maps; no claim about all datasets or tissue present inside a parent mesh.',
        'Outer muscle, linea alba and ligament labels cannot supply complete rectus/sheath/oblique/transversus, fascia, mesh or pathological hernia anatomy.',
        'The original M-marked source must be retained separately; no local mirroring, fitting, symmetric patient assumption or clinical source-axis approval is introduced.']},indent=2)+'\n')

    from tools.anatomy_sources.review_bodyparts_wall_proximity import review as proximity
    from tools.anatomy_sources.audit_bodyparts_wall_interfaces import audit as interfaces
    from tools.anatomy_sources.review_bodyparts_wall_pairs import review as pairs
    from tools.anatomy_sources.render_bodyparts_wall_self_contacts import render as self_locations
    from tools.anatomy_sources.render_bodyparts_wall_interfaces import render as pair_locations
    proximity(root,output);interfaces(root,output);pairs(output)
    self_locations(root,output);pair_locations(root,output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.source_root,a.output)
