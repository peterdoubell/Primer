#!/usr/bin/env python3
"""Preserve current original CT and same-case esophageal/mediastinal/gastric annotations using exact ZIP ranges."""
import argparse,csv,hashlib,io,json,sys,urllib.request,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.acquire_hipas_case import RemoteArchive as OriginalRemoteArchive
SOURCE=Path("/Users/peter/Documents/ChatGPT/Primer/.research/esophagus-native-v3")
class RemoteArchive(OriginalRemoteArchive):
    def read(self,size=-1):
        start=self.position;raw=super().read(size)
        if raw:
            cache=SOURCE/"original-archive-ranges";cache.mkdir(exist_ok=True)
            (cache/(str(start)+"-"+str(start+len(raw)-1)+".bin")).write_bytes(raw)
            print("Original range retained",start,len(raw),flush=True)
        return raw
NAMES=['esophagus', 'trachea', 'aorta', 'heart', 'stomach', 'lung_upper_lobe_left', 'lung_lower_lobe_left', 'lung_upper_lobe_right', 'lung_middle_lobe_right', 'lung_lower_lobe_right', 'pulmonary_vein', 'atrial_appendage_left', 'superior_vena_cava', 'inferior_vena_cava', 'spinal_cord', 'vertebrae_T1', 'vertebrae_T2', 'vertebrae_T3', 'vertebrae_T4', 'vertebrae_T5', 'vertebrae_T6', 'vertebrae_T7', 'vertebrae_T8', 'vertebrae_T9', 'vertebrae_T10', 'vertebrae_T11', 'vertebrae_T12']
def sha(raw):return hashlib.sha256(raw).hexdigest()
def acquire(root,case):
    meta_raw=(root/'zenodo-22688904.json').read_bytes();meta=json.loads(meta_raw)
    if meta['id']!=22688904 or meta['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Actual original data grant differs')
    entry=meta['files'][0];remote=RemoteArchive(entry['links']['self'],entry['size']);out=root/case;out.mkdir(exist_ok=True);records=[]
    with zipfile.ZipFile(remote) as z:
        ct_names=[n for n in z.namelist() if n.endswith('/'+case+'/ct.nii.gz')]
        if len(ct_names)!=1:raise ValueError('Original source case is absent or ambiguous')
        prefix=ct_names[0].removesuffix('ct.nii.gz');names=[ct_names[0]]+[prefix+'segmentations/'+n+'.nii.gz' for n in NAMES]
        meta_name=next(n for n in z.namelist() if n.endswith('/meta.csv') or n=='meta.csv');raw=z.read(meta_name);reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';');case_rows=[r for r in reader if case in r.values()];(out/'source-meta-row.json').write_text(json.dumps(case_rows,indent=2)+'\n')
        for name in names:
            info=z.getinfo(name);path=out/Path(name).name
            if path.exists():
                raw=path.read_bytes()
                import zlib
                if len(raw)!=info.file_size or zlib.crc32(raw)!=info.CRC:raise ValueError('Cached original member differs')
            else:
                raw=z.read(name);path.write_bytes(raw)
            records.append({'member':name,'file':path.name,'bytes':len(raw),'original_member_CRC32':f'{info.CRC:08x}','original_member_CRC_verified':True,'sha256':sha(raw)})
            (out/'acquisition-progress.json').write_text(json.dumps({'records':records,'etag':remote.etag,'full_archive_MD5_verified':False},indent=2)+'\n');print('Original member verified',path.name,len(raw),flush=True)
    fresh=json.loads(urllib.request.urlopen('https://zenodo.org/api/records/22688904',timeout=45).read());current=fresh['files'][0]
    if (current['checksum'],current['size'])!=(entry['checksum'],entry['size']):raise ValueError('Source archive identity changed')
    proof={'case':case,'actual_dataset_record':22688904,'source_doi':'10.5281/zenodo.22688904','actual_dataset_license':meta['metadata']['license'],'metadata_sha256':sha(meta_raw),'original_archive':entry,'archive_entity_tag':remote.etag,'archive_entity_tag_available':remote.etag is not None,'source_object_immutability_independently_verified':False,'publisher_archive_size_and_checksum_unchanged_before_after':True,'ranges':remote.ranges,'records':records,'source_metadata_rows':case_rows,'source_metadata_study_type_is_dedicated_neck_CT':False,'full_archive_MD5_verified':False,'source_samples_relabelled_resampled_or_repaired':False,'native_DICOM_or_independent_physical_calibration_verified':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (out/'acquisition.json').write_text(json.dumps(proof,indent=2)+'\n');print('Complete original CT and 27 same-case context annotation members preserved; full archive checksum not claimed',flush=True)
if __name__=='__main__':acquire(SOURCE,'s0358')
