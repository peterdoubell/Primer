#!/usr/bin/env python3
"""Acquire original upstream pancreatic anatomy elements from a version-stamped manifest."""
import argparse
from html.parser import HTMLParser
import hashlib
import http.cookiejar
import io
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import zipfile

TARGETS={'FMA63103':'Pancreatic duct tree','FMA63120':'Parenchyma of pancreas','FMA14329':'Source portal vein compound',
         'FMA14331':'Splenic vein','FMA14332':'Superior mesenteric vein','FMA14668':'Common hepatic duct',
         'FMA14812':'Celiac trunk','FMA76536':'Trunk of common hepatic artery','FMA76548':'Trunk of hepatic artery proper',
         'FMA76574':'Trunk of gastroduodenal artery','FMA14749':'Source superior mesenteric artery compound'}


class Rows(HTMLParser):
    def __init__(self):super().__init__();self.rows=[];self.row=[];self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        if tag in ('td','th'):self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:self.row.append(''.join(self.cell).strip());self.cell=None
        if tag=='tr' and self.row:self.rows.append(self.row)


def select(manifest,html):
    if '# Data Version\t4.3' not in manifest or '# Objects set\t4.3' not in manifest:
        raise ValueError('Source manifest version is not 4.3')
    groups={key:set() for key in TARGETS}
    for line in manifest.splitlines():
        fields=line.split('\t')
        if len(fields)==3 and fields[0] in groups:
            ids=fields[2].split('+')
            if any(not re.fullmatch(r'FJ[0-9]+',v) for v in ids):raise ValueError('Unsupported source element ID')
            groups[fields[0]].update(ids)
    if any(not ids for ids in groups.values()):raise ValueError('Requested anatomy is absent from version manifest')
    parser=Rows();parser.feed(html)
    if parser.rows[0][:7]!=['#','FJID','BPID','FMA ID','FMA Name','FMA Synonym','obj file']:
        raise ValueError('Source mapping columns differ')
    selected=sorted(set().union(*groups.values()));mapping={}
    for row in parser.rows[1:]:
        if len(row)>=8 and row[1] in selected:
            if row[1] in mapping or not re.fullmatch(r'BP[0-9]+',row[2]):raise ValueError('Ambiguous source representation mapping')
            mapping[row[1]]={'id':row[1],'representation_id':row[2],'source_fma':row[3],'source_label':row[4],'source_obj_name':row[6],'source_obj_group':row[7]}
    if set(mapping)!=set(selected):raise ValueError('Missing source representation')
    return {key:sorted(value) for key,value in groups.items()},mapping


def alternative_representations(html, selected):
    parser=Rows();parser.feed(html)
    if parser.rows[0][:7]!=['#','FJID','BPID','FMA ID','FMA Name','FMA Synonym','obj file']:
        raise ValueError('Source mapping columns differ')
    result={fid:[] for fid in selected}
    for row in parser.rows[1:]:
        if len(row)>=8 and row[1] in result and re.fullmatch(r'BP[0-9]+',row[2]):
            result[row[1]].append({'id':row[1],'representation_id':row[2],'source_fma':row[3],
                                  'source_label':row[4],'source_obj_name':row[6],'source_obj_group':row[7]})
    return result


def acquire(root):
    groups,mapping=select((root/'FMA2Obj-4.3.txt').read_text(),(root/'obj2FMA-4.3.html').read_text())
    partof_mapping=alternative_representations((root/'obj2FMA-partof-4.3.html').read_text(),mapping)
    jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    headers={'User-Agent':'Mozilla/5.0','Referer':'https://lifesciencedb.jp/bp3d/?lng=en'}
    with opener.open(urllib.request.Request(headers['Referer'],headers=headers),timeout=40) as r:r.read()
    selected=sorted(mapping);params={'ids':json.dumps(selected),'rep_id':json.dumps([mapping[k]['representation_id'] for k in selected]),
                                   'filename':'pancreatic-source-4.3','type':'art_file','all_downloads':'1','version':'4.3'}
    path=root/'upstream-selected-4.3.zip'
    if not path.exists():
        request=urllib.request.Request('https://lifesciencedb.jp/bp3d/download.cgi',data=urllib.parse.urlencode(params).encode(),headers=headers)
        with opener.open(request,timeout=120) as response:
            payload=response.read(100_000_001)
            if len(payload)>100_000_000:raise ValueError('Selected archive exceeded bound')
            path.write_bytes(payload)
    objects=root/'objects';objects.mkdir(exist_ok=True);records=[];unselected=[];seen=set()
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:raise ValueError('Original archive CRC failed')
        for entry in archive.infolist():
            match=re.match(r'(FJ[0-9]+)_(BP[0-9]+)_(FMA[0-9]+)_',Path(entry.filename).name)
            if not match or match[1] not in mapping:unselected.append(entry.filename);continue
            fid,bp,fma=match.groups()
            candidates=[r for r in [mapping[fid]]+partof_mapping[fid] if r['representation_id']==bp and r['source_fma']==fma]
            if fid in seen or not candidates:
                raise ValueError('Returned source element identity differs from both original trees')
            seen.add(fid);raw=archive.read(entry)
            if entry.file_size>100_000_000:raise ValueError('Source element size exceeded bound')
            header={}
            for line in raw.decode().splitlines():
                if not line.startswith('#'):break
                if ':' in line:
                    key,value=line.lstrip('#').split(':',1);header[key.strip()]=value.strip()
            if header.get('Compatibility version')!='4.3' or header.get('File ID')!=fid or header.get('Representation ID')!=bp or header.get('Concept ID')!=fma:
                raise ValueError('Original OBJ header identity differs')
            (objects/(fid+'.obj')).write_bytes(raw)
            records.append({**candidates[0], 'requested_is_a_representation_id':mapping[fid]['representation_id'],
                            'returned_representation_matches_is_a':bp==mapping[fid]['representation_id'],
                            'returned_representation_matches_partof':any(bp==r['representation_id'] and fma==r['source_fma'] for r in partof_mapping[fid]),
                            'original_obj_header':header,'member':entry.filename,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                            'crc32':format(entry.CRC,'08x'),'vertices':sum(s.startswith(b'v ') for s in raw.splitlines()),
                            'faces':sum(s.startswith(b'f ') for s in raw.splitlines())})
    if seen!=set(mapping):raise ValueError('Archive omits selected versioned elements')
    result={'upstream_url':'https://lifesciencedb.jp/bp3d/','version_manifest':'4.3','source_groups':groups,'target_labels':TARGETS,
            'objects':records,'unselected_archive_members_retained_in_original_zip':unselected,
            'archive_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'archive_crc_verified':True,
            'source_metadata_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['FMA2Obj-4.3.txt','obj2FMA-4.3.html','obj2FMA-partof-4.3.html','upstream-license.html']},
            'upstream_default_license':'CC BY-SA 2.1 Japan','license_url':'https://creativecommons.org/licenses/by-sa/2.1/jp/',
            'license_evidence_url':'https://lifesciencedb.jp/bp3d/info_en/license/index.html',
            'archive_40_cc_by_40_grant_reused_for_upstream_meshes':False,'publisher_checksums_available':False,
            'polygon_reduction_rate_independently_verified':False,'original_source_acquisition_resolution_verified':False,'source_geometry_altered':False,'acquisition_resolution_or_anatomical_accuracy_verified':False,'clinical_approval':False,'runtime_promoted':False}
    (root/'upstream-acquisition.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Verified',len(records),'requested original elements;',sum(r['faces'] for r in records),'source faces;',len(unselected),'unselected ZIP members retained',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);acquire(p.parse_args().source_root)
