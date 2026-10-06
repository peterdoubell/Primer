#!/usr/bin/env python3
"""Read authored view/opacity controls without executing PDF or 3D scripts."""
import argparse
import hashlib
import json
from pathlib import Path


def pdf_bool(value):
    decoded=getattr(value,'value',value)
    if not isinstance(decoded,bool):raise ValueError('Invalid source PDF boolean')
    return decoded


def view_record(view):
    d=view.get_object();overrides=[]
    for entry in d.get('/NA',[]):
        node=entry.get_object()
        overrides.append({'node_name':str(node['/N']) if '/N' in node else None,
                          'opacity':float(node['/O']) if '/O' in node else None,
                          'visible':pdf_bool(node['/V']) if '/V' in node else None,
                          'matrix_values_in_source_order':[float(v) for v in node['/M']] if '/M' in node else None})
    return {'external_name':str(d.get('/XN','')),'internal_name':str(d.get('/IN','')),
            'reset_nodes_before_overrides':pdf_bool(d.get('/NR',False)),
            'camera_to_world_values':[float(v) for v in d['/C2W']],
            'camera_orbit_distance':float(d['/CO']),'matrix_source':str(d.get('/MS')),
            'background_colour':[float(v) for v in d['/BG'].get_object()['/C']],
            'lighting_scheme':str(d['/LS'].get_object()['/Subtype']),
            'render_mode':str(d['/RM'].get_object()['/Subtype']),
            'projection':{str(k):float(v) if isinstance(v,(float,int)) else str(v) for k,v in d['/P'].get_object().items()},
            'node_overrides':overrides,'original_renderer_pixel_equivalence_verified':False}


def review(pdf,source,output):
    from pypdf import PdfReader
    inv=json.loads((source/'original-model-inventory.json').read_text());raw=pdf.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=inv['original_pdf_sha256']:raise ValueError('Original model PDF differs')
    reader=PdfReader(pdf);ann=[a.get_object() for p in reader.pages for a in p.get('/Annots',[]) if a.get_object().get('/Subtype')=='/3D']
    if len(ann)!=1 or hashlib.sha256(ann[0]['/3DD'].get_data()).hexdigest()!=inv['u3d_sha256']:raise ValueError('Embedded scene differs')
    default=view_record(ann[0]['/3DV']);views=[view_record(v) for v in ann[0]['/3DD']['/VA'].get_object()]
    names={n['name'] for n in inv['model_nodes']}
    if any(v['node_name'] not in names for record in [default]+views for v in record['node_overrides'] if v['node_name'] is not None):raise ValueError('Unresolved named view override')
    output.mkdir(parents=True,exist_ok=True)
    (output/'source-pdf-view-review.json').write_text(json.dumps({'source_pdf_sha256':hashlib.sha256(raw).hexdigest(),
        'original_u3d_sha256':inv['u3d_sha256'],'default_view':default,'views':views,
        'pdf_or_3d_scripts_executed':False,'unnamed_override_scope_independently_verified':False,
        'view_transform_application_independently_verified':False,'authored_colour_is_biological_signal':False,
        'patient_axes_or_registration_verified':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')
    print('Retained default view and',len(views),'authored view records without script execution.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pdf',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.pdf,a.source,a.output)
