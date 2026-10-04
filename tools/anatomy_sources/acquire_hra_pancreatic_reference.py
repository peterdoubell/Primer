#!/usr/bin/env python3
"""Acquire versioned HRA pancreatic raw distributions with distinct model rights."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def distributions(metadata, sex, version='v1.3'):
    base='https://lod.humanatlas.io/ref-organ/pancreas-'+sex+'/'+version
    nodes={r['@id']:r for r in metadata['@graph']}
    raw=nodes[base+'#raw-data']
    if 'https://creativecommons.org/licenses/by/4.0/' not in raw.get('dct:license',''):
        raise ValueError('Raw model grant is not the selected CC BY 4.0 grant')
    result=[]
    for reference in raw['dcat:distribution']:
        row=nodes[reference['@id']];url=row['dcat:downloadURL']['@value']
        prefix='https://cdn.humanatlas.io/digital-objects/ref-organ/pancreas-'+sex+'/'+version+'/assets/'
        if not url.startswith(prefix) or url[len(prefix):] not in ['crosswalk.csv','3d-vh-'+sex[0]+'-pancreas.glb']:
            raise ValueError('Unrelated raw model distribution')
        result.append((url,url[len(prefix):]))
    if len(result)!=2 or len({name for _,name in result})!=2:
        raise ValueError('Need one original GLB and its crosswalk')
    return raw,result


def acquire(output):
    receipts=[]
    for sex in ['female','male']:
        folder=output/('pancreas-'+sex+'-v1.3');folder.mkdir(parents=True,exist_ok=True)
        url='https://cdn.humanatlas.io/digital-objects/ref-organ/pancreas-'+sex+'/v1.3/metadata.jsonld'
        path=folder/'metadata.jsonld'
        if not path.exists():path.write_bytes(urllib.request.urlopen(url,timeout=40).read())
        metadata=json.loads(path.read_text());raw,files=distributions(metadata,sex)
        sources=[]
        for link,name in [(url,'metadata.jsonld')]+files:
            path=folder/name
            if not path.exists():path.write_bytes(urllib.request.urlopen(link,timeout=40).read())
            sources.append({'name':name,'url':link,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                            'sha256_is_local_fingerprint_not_publisher_checksum':True})
        receipts.append({'sex':sex,'version':'v1.3','source_doi':raw['ccf:doi']['@id'],'raw_model_license':raw['dct:license'],
                         'source_citation':raw['schema1:citation'],'source_description':raw['rdfs:comment'],
                         'source_reviewed_by':raw['schema1:reviewedBy'],'sources':sources,'clinical_approval':False,'runtime_promoted':False})
        print(sex,[(r['name'],r['bytes']) for r in sources],flush=True)
    (output/'acquisition.json').write_text(json.dumps(receipts,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    acquire(p.parse_args().output)
