"""Byte-bound teaching movies; no anatomical or physiological coverage approval."""
import hashlib,json,math
from pathlib import Path
from .source_motion_integrity import verified_motion_contract

def _validate_yuv_fidelity(row, data_dir):
    """Bind a sample-domain claim to the retained, independently decoded proof."""
    proof_path = Path(data_dir) / 'thoracic-ultrasound-motion-proof.json'
    raw = proof_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != row.get('frame_fidelity_proof_sha256'):
        raise ValueError('YUV frame proof changed')
    proof = json.loads(raw)
    entry = proof.get('clips', {}).get(row['id'])
    if proof.get('schema_version') != 1 or not isinstance(entry, dict):
        raise ValueError('Missing YUV frame proof')
    if (row.get('decoded_YUV_frames_unchanged') is not True
            or row.get('decoded_RGB_frames_unchanged') is not False
            or entry.get('RGB_colorimetry_verified') is not False):
        raise ValueError('YUV sample proof cannot grant RGB colorimetry')
    for field in ('frames', 'width', 'height', 'original_sha256', 'source_pts_seconds', 'transport_pts_seconds'):
        if entry.get(field) != row.get(field):
            raise ValueError('YUV frame proof source binding differs')
    if entry.get('transport_sha256') != row.get('sha256'):
        raise ValueError('YUV frame proof transport binding differs')
    if (entry.get('source_pixel_format') not in {'yuv420p', 'yuvj420p'}
            or entry.get('transport_pixel_format') != 'yuv420p'):
        raise ValueError('YUV sample layout or range differs')
    source_range, transport_range = entry.get('source_color_range'), entry.get('transport_color_range')
    explicit = (entry.get('range_policy') == 'preserve_explicit_range'
                and source_range in {'pc', 'tv'} and source_range == transport_range)
    unspecified = (entry.get('range_policy') == 'source_unspecified_transport_limited'
                   and source_range == 'unspecified' and transport_range == 'tv'
                   and 'Source color range is unspecified' in row.get('limits', ''))
    if not (explicit or unspecified):
        raise ValueError('YUV color-range policy is missing or contradictory')
    original = entry.get('original_decoded_YUV_frame_sha256')
    transport = entry.get('transport_decoded_YUV_frame_sha256')
    if (not isinstance(original, list) or len(original) != row['frames']
            or original != transport
            or any(not isinstance(h, str) or len(h) != 64
                   or any(c not in '0123456789abcdef' for c in h) for h in original)):
        raise ValueError('YUV decoded frame samples differ')


def validate_motion_references(registry,known,web):
    if not isinstance(registry,dict):raise ValueError('Source motion must map investigations')
    web=Path(web).resolve();seen=set()
    proof_path = web.parent/'data/radiology/thoracic-ultrasound-motion-proof.json'
    known_yuv = json.loads(proof_path.read_text()).get('clips', {}) if proof_path.exists() else {}
    yuv_digests = {entry.get(key) for entry in known_yuv.values()
                   for key in ('original_sha256', 'transport_sha256')}
    for investigation,rows in registry.items():
        if investigation not in known or not isinstance(rows,list) or not rows:raise ValueError('Source motion needs a known investigation')
        for row in rows:
            if not isinstance(row,dict) or row.get('id') in seen:raise ValueError('Duplicate or invalid motion reference')
            seen.add(row.get('id'))
            for key in ['id','title','caption','attribution','source_url','license_url','limits']:
                if not isinstance(row.get(key),str) or not row[key].strip():raise ValueError('Source motion requires '+key)
            if row.get('reference_only') is not True or row.get('clinical_approval') is not False or row.get('anatomical_approval') is not False or row.get('structure_ids') or row.get('requirement_coverage'):raise ValueError('Teaching motion cannot grant clinical or anatomical coverage')
            if row.get('modality') not in {'MRI','CT','Radiography','Ultrasound'}:raise ValueError('Source motion needs actual modality')
            for key in ['width','height','frames']:
                if type(row.get(key)) is not int or row[key]<1:raise ValueError('Source motion has invalid dimensions/count')
            contracts={}
            for field,digest in [('src','sha256'),('original_src','original_sha256')]:
                src=row.get(field);prefix='/app/reference-media/radiology-motion/'
                if not isinstance(src,str) or not src.startswith(prefix) or '%' in src or '\\' in src or '/' in src.removeprefix(prefix) or not src.endswith(('.webm','.mp4','.avi','.mov','.m4v')):raise ValueError('Motion file must stay in its registered directory')
                path=(web/src.removeprefix('/app/')).resolve()
                if not path.is_relative_to(web):raise ValueError('Motion path leaves web directory')
                contracts[field]=verified_motion_contract(path,src,row.get(digest),web.parent/'data/radiology')
            source=row.get('source_pts_seconds');transport=row.get('transport_pts_seconds')
            for times in [source,transport]:
                if not isinstance(times,list) or len(times)!=row['frames'] or any(type(t) not in {int,float} or not math.isfinite(t) or t<0 for t in times) or any(a>=b for a,b in zip(times,times[1:])):raise ValueError('Motion timestamps/count/order differ')
            for field,times in [('original_src',source),('src',transport)]:
                contract=contracts[field]
                if any(contract[k]!=row[k] for k in ['width','height','frames']) or contract['pts_seconds']!=times:raise ValueError('Motion dimensions/count/timestamps differ from source container bytes')
            tolerance=row.get('max_transport_timestamp_error_seconds')
            if (row.get('original_sha256') in yuv_digests or row.get('sha256') in yuv_digests) and row.get('frame_fidelity') != 'decoded_yuv420_samples':
                raise ValueError('Known YUV source cannot be relabelled as RGB fidelity')
            if row.get('frame_fidelity') == 'decoded_yuv420_samples':
                _validate_yuv_fidelity(row, web.parent/'data/radiology')
            elif row.get('frame_fidelity') is not None or row.get('decoded_RGB_frames_unchanged') is not True:
                raise ValueError('Unverified motion frame fidelity')
            if type(tolerance) not in {int,float} or not math.isfinite(tolerance) or tolerance<0 or tolerance>0.001 or max(abs(a-b) for a,b in zip(source,transport))>tolerance:raise ValueError('Motion transport does not preserve reviewed frames/timing')
            if row.get('motion_context',{}).get('current_patient_registered') is not False:raise ValueError('Motion reference must remain a separate source case')
    return registry
