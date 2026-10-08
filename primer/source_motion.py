"""Byte-bound teaching movies; no anatomical or physiological coverage approval."""
import hashlib,json,math
from pathlib import Path
from .source_motion_contract import parse_motion_contract

def validate_motion_references(registry,known,web):
    if not isinstance(registry,dict):raise ValueError('Source motion must map investigations')
    web=Path(web).resolve();seen=set()
    for investigation,rows in registry.items():
        if investigation not in known or not isinstance(rows,list) or not rows:raise ValueError('Source motion needs a known investigation')
        for row in rows:
            if not isinstance(row,dict) or row.get('id') in seen:raise ValueError('Duplicate or invalid motion reference')
            seen.add(row.get('id'))
            for key in ['id','title','caption','attribution','source_url','license_url','limits']:
                if not isinstance(row.get(key),str) or not row[key].strip():raise ValueError('Source motion requires '+key)
            if row.get('reference_only') is not True or row.get('clinical_approval') is not False or row.get('anatomical_approval') is not False or row.get('structure_ids') or row.get('requirement_coverage'):raise ValueError('Teaching motion cannot grant clinical or anatomical coverage')
            if row.get('modality') not in {'MRI','Radiography','Ultrasound'}:raise ValueError('Source motion needs actual modality')
            for key in ['width','height','frames']:
                if type(row.get(key)) is not int or row[key]<1:raise ValueError('Source motion has invalid dimensions/count')
            contracts={}
            for field,digest in [('src','sha256'),('original_src','original_sha256')]:
                src=row.get(field);prefix='/app/reference-media/radiology-motion/'
                if not isinstance(src,str) or not src.startswith(prefix) or '%' in src or '\\' in src or '/' in src.removeprefix(prefix) or not src.endswith(('.webm','.mp4')):raise ValueError('Motion file must stay in its registered directory')
                path=(web/src.removeprefix('/app/')).resolve()
                if not path.is_relative_to(web) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row.get(digest):raise ValueError('Motion file missing or changed')
                contracts[field]=parse_motion_contract(path)
            source=row.get('source_pts_seconds');transport=row.get('transport_pts_seconds')
            for times in [source,transport]:
                if not isinstance(times,list) or len(times)!=row['frames'] or any(type(t) not in {int,float} or not math.isfinite(t) or t<0 for t in times) or any(a>=b for a,b in zip(times,times[1:])):raise ValueError('Motion timestamps/count/order differ')
            for field,times in [('original_src',source),('src',transport)]:
                contract=contracts[field]
                if any(contract[k]!=row[k] for k in ['width','height','frames']) or contract['pts_seconds']!=times:raise ValueError('Motion dimensions/count/timestamps differ from source container bytes')
            tolerance=row.get('max_transport_timestamp_error_seconds')
            if row.get('decoded_RGB_frames_unchanged') is not True or type(tolerance) not in {int,float} or not math.isfinite(tolerance) or tolerance<0 or tolerance>0.001 or max(abs(a-b) for a,b in zip(source,transport))>tolerance:raise ValueError('Motion transport does not preserve reviewed frames/timing')
            if row.get('motion_context',{}).get('current_patient_registered') is not False:raise ValueError('Motion reference must remain a separate source case')
    return registry
