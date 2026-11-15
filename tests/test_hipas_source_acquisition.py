"""Range provenance must reject wrong bytes and record missing server entity tags honestly."""
import io
import pytest
from tools.anatomy_sources.acquire_hipas_case import RemoteArchive
class Response(io.BytesIO):
    status=206
    def __init__(self,raw,range_header,etag=None):
        super().__init__(raw);self.headers={'Content-Range':range_header}
        if etag is not None:self.headers['ETag']=etag
@pytest.mark.parametrize('raw,content_range',[(b'ab','bytes 0-2/10'),(b'abc','bytes 1-3/10'),(b'abc','bytes 0-2/11')])
def test_range_rejects_truncated_shifted_or_changed_archive(monkeypatch,raw,content_range):
    monkeypatch.setattr('urllib.request.urlopen',lambda *args,**kw:Response(raw,content_range))
    with pytest.raises(ValueError):RemoteArchive('https://example.test/file',10).read(3)
def test_missing_etag_retains_exact_range_provenance(monkeypatch):
    monkeypatch.setattr('urllib.request.urlopen',lambda *args,**kw:Response(b'abc','bytes 0-2/10'))
    source=RemoteArchive('https://example.test/file',10)
    assert source.read(3)==b'abc' and source.etag is None
    assert source.ranges[0]['start']==0 and source.ranges[0]['end']==2 and len(source.ranges[0]['sha256'])==64
def test_supplied_entity_tag_cannot_change_between_ranges(monkeypatch):
    replies=iter([Response(b'abc','bytes 0-2/10','original'),Response(b'def','bytes 3-5/10','changed')])
    monkeypatch.setattr('urllib.request.urlopen',lambda *args,**kw:next(replies));source=RemoteArchive('https://example.test/file',10);source.read(3)
    with pytest.raises(ValueError):source.read(3)
@pytest.mark.parametrize('offset,whence',[(-1,0),(11,0),(1,2)])
def test_seek_cannot_escape_original_archive(offset,whence):
    with pytest.raises(ValueError):RemoteArchive('https://example.test/file',10).seek(offset,whence)
