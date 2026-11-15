#!/usr/bin/env python3
"""Preserve complete original arterial source objects and quarantine conflicting ontology identities."""
import argparse,gzip,hashlib,json,re,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import select,alternative_representations,Rows

def sha(raw):return hashlib.sha256(raw).hexdigest()
def review(root,output):
    targets=json.loads((root/'selected-targets.json').read_text());groups,mapping=select((root/'FMA2Obj-4.3.txt').read_text(),(root/'obj2FMA-4.3.html').read_text(),targets,True);alternatives=alternative_representations((root/'obj2FMA-partof-4.3.html').read_text(),mapping);output.mkdir(parents=True,exist_ok=True);(output/'original-objects').mkdir(exist_ok=True);records=[];held=[];seen=set();archive=root/'upstream-selected-4.3.zip'
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise ValueError('Original archive CRC differs')
        for member in z.infolist():
            match=re.match(r'(FJ[0-9]+M?)_(BP[0-9]+)_(FMA[0-9]+)_',Path(member.filename).name)
            if not match or match[1] not in mapping:raise ValueError('Original archive includes unreviewed element')
            fid,bp,fma=match.groups()
            if fid in seen:raise ValueError('Duplicated original element')
            seen.add(fid);raw=z.read(member);header={}
            for line in raw.decode().splitlines():
                if not line.startswith('#'):break
                if ':' in line:
                    key,value=line.lstrip('#').split(':',1);header[key.strip()]=value.strip()
            if header.get('Compatibility version')!='4.3' or header.get('File ID')!=fid or header.get('Representation ID')!=bp or header.get('Concept ID')!=fma:raise ValueError('Original header/member identity differs')
            candidates=[r for r in [mapping[fid]]+alternatives[fid] if r['representation_id']==bp and r['source_fma']==fma];path=output/'original-objects'/f'{fid}.obj.gz'
            with gzip.GzipFile(filename=str(path),mode='wb',mtime=0) as stream:stream.write(raw)
            record={'id':fid,'original_member':member.filename,'file':str(path.relative_to(output)),'sha256':sha(raw),'compressed_file_sha256':sha(path.read_bytes()),'bytes':len(raw),'zip_crc_verified':True,'original_obj_header':header,'requested_is_a_mapping':mapping[fid],'original_partof_mappings':alternatives[fid],'matches_requested_mapping':bool(candidates),'source_positions_faces_or_normals_changed':False,'independent_patient_laterality_or_anatomical_validation':False,'source_M_suffix':fid.endswith('M'),'clinical_approval':False,'runtime_promoted':False}
            records.append(record)
            if not candidates:held.append({'id':fid,'returned_FMA':fma,'returned_representation_id':bp,'requested_mapping':mapping[fid],'reason':'Returned identity matches neither the original is-a nor part-of maps. Preserve, do not relabel, bind or repair.'})
    if set(mapping)!=seen:raise ValueError('Original archive omits requested element')
    receipt={'source_url':'https://lifesciencedb.jp/bp3d/','source_version':'4.3','license':'CC BY-SA 2.1 Japan','license_url':'https://creativecommons.org/licenses/by-sa/2.1/jp/','license_evidence_url':'https://lifesciencedb.jp/bp3d/info_en/license/index.html','archive_sha256':sha(archive.read_bytes()),'archive_crc_verified':True,'source_metadata_sha256':{n:sha((root/n).read_bytes()) for n in ['FMA2Obj-4.3.txt','obj2FMA-4.3.html','obj2FMA-partof-4.3.html','upstream-license.html']},'source_groups':groups,'requested_source_labels':targets,'objects':records,'identity_holds':held,'complete_source_objects_retained':True,'source_geometry_changed':False,'native_MRI_or_patient_registration_verified':False,'full_reportable_tree_wall_or_disease_coverage_verified':False,'clinical_approval':False,'runtime_promoted':False}
    filename_conflicts=[]
    for record in records:
        label=record['requested_is_a_mapping']['source_label'].lower();name=record['requested_is_a_mapping']['source_obj_name'].lower();side='left' if 'left ' in label else 'right' if 'right ' in label else None;opposite='right' if side=='left' else 'left' if side=='right' else None
        if side and opposite in name and side not in name:filename_conflicts.append({'id':record['id'],'source_label':record['requested_is_a_mapping']['source_label'],'source_obj_name':record['requested_is_a_mapping']['source_obj_name'],'reason':'Catalogue anatomical label and original filename use opposite side terms; filename mismatch is retained, not proof of independent laterality.'})
    receipt['original_filename_laterality_conflicts']=filename_conflicts
    (output/'source-identity-review.json').write_text(json.dumps(receipt,indent=2)+'\n')
    # Preserve selected original mapping rows, rather than only our translated labels.
    tables={}
    for name in ['obj2FMA-4.3.html','obj2FMA-partof-4.3.html']:
        p=Rows();p.feed((root/name).read_text());tables[name]={'sha256':sha((root/name).read_bytes()),'headers':p.rows[0],'original_rows':[r for r in p.rows[1:] if len(r)>1 and r[1] in seen]}
    (output/'original-mapping-rows.json').write_text(json.dumps(tables,indent=2)+'\n');(output/'original-license.html').write_bytes((root/'upstream-license.html').read_bytes());print(len(records),'original objects retained;',len(held),'identity conflicts held.',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();review(a.source_root,a.output)
