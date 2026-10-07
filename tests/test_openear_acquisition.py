"""Acquisition must preserve resumed bytes and reject unverifiable archive identities."""
import hashlib
import io
import json
import zipfile
import pytest
from tools.anatomy_sources.acquire_openear_case import acquire


def archive():
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:z.writestr('ZETA/original.txt',b'original source member')
    return stream.getvalue()


def setup(root,raw,checksum=None):
    root.mkdir()
    (root/'zenodo-1473724.json').write_text(json.dumps({'id':1473724,'metadata':{'license':{'id':'cc-by-4.0'}},'files':[{'key':'ZETA.zip','size':len(raw),'checksum':'md5:'+(checksum or hashlib.md5(raw).hexdigest()),'links':{'self':'https://zenodo.org/original-test'}}]}))


class Response(io.BytesIO):
    def __init__(self,raw,status=200,headers=None):super().__init__(raw);self.status=status;self.headers=headers or {}


def test_exact_resumed_range_survives_checksum_and_member_CRC(tmp_path,monkeypatch):
    raw=archive();root=tmp_path/'cache';setup(root,raw);offset=20;(root/'ZETA.zip.part').write_bytes(raw[:offset])
    def fetch(request,timeout):
        assert request.get_header('Range')=='bytes=20-'
        return Response(raw[offset:],206,{'Content-Range':f'bytes {offset}-{len(raw)-1}/{len(raw)}'})
    monkeypatch.setattr('urllib.request.urlopen',fetch);acquire(root,tmp_path/'proof','ZETA')
    assert (root/'ZETA.zip').read_bytes()==raw and not (root/'ZETA.zip.part').exists()
    proof=json.loads((tmp_path/'proof/ZETA-original-acquisition.json').read_text())
    assert proof['archive']['publisher_MD5_verified'] and proof['members'][0]['ZIP_CRC_verified']
    assert not proof['clinical_approval'] and not proof['runtime_promoted']


def test_ignored_resumed_range_keeps_partial_untouched(tmp_path,monkeypatch):
    raw=archive();root=tmp_path/'cache';setup(root,raw);partial=root/'ZETA.zip.part';partial.write_bytes(raw[:20])
    monkeypatch.setattr('urllib.request.urlopen',lambda request,timeout:Response(raw,200))
    with pytest.raises(ValueError,match='range'):acquire(root,tmp_path/'proof','ZETA')
    assert partial.read_bytes()==raw[:20] and not (root/'ZETA.zip').exists()


def test_publisher_checksum_failure_never_promotes_partial(tmp_path,monkeypatch):
    raw=archive();root=tmp_path/'cache';setup(root,raw,'0'*32)
    monkeypatch.setattr('urllib.request.urlopen',lambda request,timeout:Response(raw))
    with pytest.raises(ValueError,match='MD5'):acquire(root,tmp_path/'proof','ZETA')
    assert not (root/'ZETA.zip').exists() and not (tmp_path/'proof/ZETA-original-acquisition.json').exists()
