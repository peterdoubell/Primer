#!/usr/bin/env python3
"""Audit original microscopy frames and recorded reconstruction positions without guessing collision handling."""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image
from tools.anatomy_sources.decode_openear_ZETA_volumes import verified_memmap

def sha(raw):return hashlib.sha256(raw).hexdigest()
def nearest_source_slots(positions,pitch,depth):
    positions=np.asarray(positions,float)
    if positions.ndim!=1 or not np.isfinite(positions).all() or pitch<=0 or depth<1 or np.any(np.diff(positions)<0):raise ValueError('Invalid original reconstruction positions')
    slots=np.rint(positions/pitch).astype(int)
    if (slots<0).any() or (slots>=depth).any():raise ValueError('Original photo position outside declared reconstruction')
    return slots

def review(root,proof_dir):
    acquired=json.loads((proof_dir/'ZETA-original-acquisition.json').read_text());records={r['member']:r for r in acquired['members']};rows=[];out=root/'ZETA-photo-reference';out.mkdir(exist_ok=True)
    with zipfile.ZipFile(root/'ZETA.zip') as z:
        p='04_Reconstruction_Microslicing/Materials_for_Reconstruction/Layer_Positions_ZETA.csv';t='04_Reconstruction_Microslicing/Transformations_Zeta.CSV';positions_raw=z.read(p);matrices_raw=z.read(t)
        if sha(positions_raw)!=records[p]['sha256'] or sha(matrices_raw)!=records[t]['sha256']:raise ValueError('Original reconstruction tables changed')
        positions=np.array([float(l) for l in positions_raw.decode().splitlines()]);matrices=np.array([[float(x) for x in l.split(';')] for l in matrices_raw.decode().splitlines()]).reshape(-1,3,3)
        names=sorted(n for n in records if n.startswith('03_Microslicing_Raw/') and n.endswith('.tif'))
        if len(names)!=len(positions) or len(names)!=len(matrices) or not np.isfinite(matrices).all() or not np.isfinite(positions).all() or np.any(np.diff(positions)<0):raise ValueError('Original photo/table cardinality or interpretation differs')
        chosen=int(np.argmin(abs(positions-32)))
        for i,name in enumerate(names):
            raw=z.read(name)
            if sha(raw)!=records[name]['sha256']:raise ValueError('Original photo bytes changed')
            frames=[]
            with Image.open(io.BytesIO(raw)) as image:
                for f in range(image.n_frames):
                    image.seek(f);frames.append({'original_frame_index':f,'width':image.width,'height':image.height,'mode':image.mode})
                if i==chosen:
                    image.seek(0);image.load();pixels=image.tobytes();master=out/f'{i:03d}-original-frame0.png';image.save(master)
                    with Image.open(master) as restored:
                        restored.load()
                        if restored.tobytes()!=pixels or restored.size!=image.size:raise ValueError('Original decoded photo sample preservation differs')
                    selected={'member':name,'source_position':float(positions[i]),'original_frame_index':0,'original_pixels_sha256':sha(pixels),'lossless_original_frame_file':master.name,'lossless_original_frame_sha256':sha(master.read_bytes()),'original_transform_matrix':matrices[i].tolist(),'original_pixels_changed':False}
            rows.append({'member':name,'source_member_sha256':sha(raw),'ZIP_CRC_reverified':True,'original_source_position':float(positions[i]),'original_transform_matrix':matrices[i].tolist(),'original_TIFF_frames':frames})
    volume_path=proof_dir/'ZETA-original-volume-readback.json';volume_proof=json.loads(volume_path.read_text());colour=next(v for v in volume_proof['volumes'] if 'Microslicing' in v['member']);pitch=float(colour['equivalent_RAS_affine'][2][2]);depth=colour['source_sizes_fastest_first'][3]
    slots=nearest_source_slots(positions,pitch,depth);counts=Counter(slots.tolist());collisions=[{'native_reconstructed_index':i,'source_photo_indices':np.where(slots==i)[0].tolist()} for i,n in sorted(counts.items()) if n>1]
    layer=int(np.rint(selected['source_position']/pitch));data=verified_memmap(out.parent/'ZETA-volume-review/Microslicing_Zeta.nrrd.raw',colour);plane=Image.fromarray(np.asarray(data[layer]));plane_path=out/f'ZETA-reconstructed-layer{layer}.png';plane.save(plane_path)
    selected.update(nearest_reconstructed_original_layer=layer,actual_reconstructed_plane_position=layer*pitch,source_raw_vs_reconstructed_plane_position_difference=float(layer*pitch-selected['source_position']),reconstructed_plane_file=plane_path.name,reconstructed_plane_sha256=sha(plane_path.read_bytes()))
    result={'case':'ZETA','source_position_table_sha256':sha(positions_raw),'source_transform_table_sha256':sha(matrices_raw),'all_original_photo_files_CRC_and_SHA_reverified':True,
        'original_photographs':rows,'source_photograph_count':len(rows),'source_reconstructed_native_layers':depth,'distinct_nearest_recorded_photo_slots':len(counts),
        'slots_without_nearest_original_photo':sorted(set(range(depth))-set(counts)),'colliding_nearest_photo_slots':collisions,
        'nearest_slot_calculation_is_not_proof_of_exact_author_reconstruction_algorithm_or_collision_resolution':True,'selected_raw_and_reconstructed_planes':selected,
        'original_transform_units_canvas_padding_and_raw_to_registered_sample_identity_independently_verified':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (proof_dir/'ZETA-original-photo-reconstruction-review.json').write_text(json.dumps(result,indent=2)+'\n');print(len(rows),'original TIFFs checked;',len(counts),'distinct native slots;',len(collisions),'unresolved collisions');print(selected)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();review(a.source_root,a.proof_dir)
