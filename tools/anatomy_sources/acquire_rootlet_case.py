"""Acquire a bounded public rootlet case using published annex keys and hashes."""
from pathlib import Path
import base64,hashlib,json,re,urllib.request
ROOT=Path(__file__).resolve().parents[2]/'.research/anatomy-sources/rootlets';SUBJECT='sub-amu02';REF='r20250314';BASE='https://object-arbutus.alliancecan.ca/4f21233170e74c7d8653d790029d4ce2:def-jcohen-data-multi-subject'


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    commit='a0738046538232df8e09eba8d98899eada9c11d5'
    tree_path=ROOT/'repository-tree.json'
    if not tree_path.exists():
        tree=json.load(urllib.request.urlopen('https://api.github.com/repos/spine-generic/data-multi-subject/git/trees/'+commit+'?recursive=1'))
        assert not tree.get('truncated');tree_path.write_text(json.dumps(tree,indent=2)+'\n')
    tree=json.loads(tree_path.read_text());assert not tree.get('truncated');selected=[]
    for f in tree['tree']:
        p=f['path']
        if p.startswith('derivatives/labels/'+SUBJECT+'/anat/') and '_T2w_' in p:selected.append(f)
        elif p in [f'{SUBJECT}/anat/{SUBJECT}_T2w.nii.gz',f'{SUBJECT}/anat/{SUBJECT}_T2w.json']:selected.append(f)
    records=[];out=ROOT/SUBJECT;out.mkdir(exist_ok=True)
    for entry in selected:
        name=entry['path'];cached=ROOT/'repository-metadata'/name
        if cached.exists():raw=cached.read_bytes()
        else:
            blob=json.load(urllib.request.urlopen(entry['url']));raw=base64.b64decode(blob['content']);cached.parent.mkdir(parents=True,exist_ok=True);cached.write_bytes(raw)
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==entry['sha']
        if name.endswith('.json'):
            (out/Path(name).name).write_bytes(raw);records.append({'repository_path':name,'git_blob_sha':entry['sha'],'file':str(out/Path(name).name),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'kind':'sidecar'});continue
        pointer=raw.decode().strip();match=re.fullmatch(r'/annex/objects/(SHA256E-s(\d+)--([0-9a-f]{64})\.nii\.gz)',pointer);assert match,pointer
        size=int(match[2]);assert size<20_000_000;destination=out/Path(name).name;url=BASE+'/'+match[1]
        if destination.exists():payload=destination.read_bytes()
        else:
            with urllib.request.urlopen(url,timeout=60) as response:payload=response.read(size+1)
            assert len(payload)==size and hashlib.sha256(payload).hexdigest()==match[3];destination.write_bytes(payload)
        assert len(payload)==size and hashlib.sha256(payload).hexdigest()==match[3]
        records.append({'repository_path':name,'git_blob_sha':entry['sha'],'file':str(destination),'sha256':match[3],'bytes':size,'kind':'nifti','public_url':url});print(destination.name,size,'SHA-256 verified',flush=True)
    (ROOT/'acquisition.json').write_text(json.dumps({'repository':'https://github.com/spine-generic/data-multi-subject','release':REF,'commit':commit,'files':records,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':main()
