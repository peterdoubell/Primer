"""SPL source identity, exact categorical boundaries and authenticated delivery.

Source integrity is deliberately separate from anatomical or clinical approval.
"""
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct

import numpy as np
import pytest

from primer import spl_limbic_reference as spl
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'web/anatomy'/spl.ATLAS
REVIEW=ROOT/'docs/spl-limbic-source-review-20261016'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture(scope='module')
def manifest():
    return json.loads((ASSETS/'manifest.json').read_text())


def decoded(row):
    packed=(ASSETS/row['file']).read_bytes()
    assert sha(packed)==row['gzipSHA256']
    raw=gzip.decompress(packed)
    assert sha(raw)==row['decodedSHA256'] and len(raw)==row['byteLength']
    return raw


def mesh(row):
    raw=decoded(row)
    assert struct.unpack_from('<4sIII',raw)==(b'HVX1',row['vertexCount'],row['triangleCount'],0)
    split=16+row['vertexCount']*12
    assert sha(raw[16:split])==row['positionByteSHA256'] and sha(raw[split:])==row['indexByteSHA256']
    vertices=np.frombuffer(raw[16:split],'<f4').reshape(-1,3)
    triangles=np.frombuffer(raw[split:],'<u4').reshape(-1,3)
    assert len(triangles)==row['triangleCount'] and triangles.max()<len(vertices)
    return vertices,triangles


def test_inventory_is_exact_regular_and_source_reviewed():
    registry=spl.registry()
    assert len(registry['files'])==88
    assert set(registry['files'])=={str(p.relative_to(ASSETS)) for p in ASSETS.rglob('*') if p.is_file()}
    for name,row in registry['files'].items():
        path=spl.validate_file(name)
        assert path.is_file() and not path.is_symlink()
        assert sha(path.read_bytes())==row['sha256'] and path.stat().st_size==row['bytes']
    raw=(REVIEW/'source-review.json').read_bytes()
    assert sha(raw)==registry['source_review_sha256']
    review=json.loads(raw)
    assert review['clinical_approval'] is review['whole_module_complete'] is review['whole_primer_goal_complete'] is False
    for row in review['lossless_transport']['files']:
        assert registry['files'][row['file']]=={'bytes':row['bytes'],'sha256':row['sha256']}


def test_native_grids_reconstruct_every_original_NRRD_bit_and_declared_affine(manifest):
    count=0
    for name,row in {**manifest['volumes'],'labels':manifest['labelVolume']}.items():
        header=(ASSETS/row['sourceHeaderFile']).read_bytes()
        original=header+(ASSETS/row['file']).read_bytes()
        assert len(original)==row['source']['bytes'] and sha(original)==row['source']['sha256']
        assert hashlib.sha1(('blob '+str(len(original))+'\0').encode()+original).hexdigest()==row['source']['gitBlobSHA1']
        fields=dict(line.split(':',1) for line in header.decode().splitlines()[1:] if line and not line.startswith('#'))
        fields={k.strip():v.strip() for k,v in fields.items()}
        assert fields['endian']=='little' and fields['space']=='left-posterior-superior' and fields['encoding']=='gzip'
        assert fields['type']==('short' if name=='labels' else 'float')
        assert fields['sizes']==' '.join(map(str,row['shape']))
        vectors=[list(map(float,m.split(','))) for m in re.findall(r'\(([^)]+)\)',fields['space directions'])]
        lps=np.eye(4);lps[:3,:3]=np.asarray(vectors).T;lps[:3,3]=list(map(float,fields['space origin'].strip('()').split(',')))
        np.testing.assert_array_equal(lps,row['voxelToLPS'])
        np.testing.assert_array_equal(np.diag([-1,-1,1,1])@lps,row['voxelToRAS'])
        a=np.frombuffer(decoded(row),row['dtype'])
        assert a.size==np.prod(row['shape']) and np.isfinite(a).all()
        count+=a.size
    assert count==55115776
    assert manifest['volumes']['T1']['voxelToRAS']==manifest['volumes']['T2']['voxelToRAS']!=manifest['labelVolume']['voxelToRAS']


def test_original_VTK_positions_normals_strips_and_every_triangle_are_lossless(manifest):
    total=0
    for row in manifest['meshes']:
        raw=decoded(row['originalVTK'])
        assert sha(raw)==row['source']['sha256']
        assert hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()==row['source']['gitBlobSHA1']
        match=re.match(rb'# vtk DataFile Version 3\.0\nvtk output\nBINARY\nDATASET POLYDATA\nPOINTS (\d+) float\n',raw)
        n=int(match[1]);start=match.end();positions,triangles=mesh(row)
        assert positions.astype('>f4').tobytes()==raw[start:start+12*n]
        at=start+12*n;strip_header=re.match(rb'\nTRIANGLE_STRIPS (\d+) (\d+)\n',raw[at:]);at+=strip_header.end()
        ns,ni=map(int,strip_header.groups());strips=np.frombuffer(decoded(row['originalStrips']),'<i4')
        assert strips.astype('>i4').tobytes()==raw[at:at+4*ni];at+=4*ni
        normals_header=re.match(rb'\nPOINT_DATA (\d+)\nNORMALS Normals float\n',raw[at:]);at+=normals_header.end()
        normals=np.frombuffer(decoded(row['originalNormals']),'<f4')
        assert normals.astype('>f4').tobytes()==raw[at:at+12*n] and not raw[at+12*n:].strip()
        expected=[];cursor=0
        for _ in range(ns):
            size=int(strips[cursor]);indices=strips[cursor+1:cursor+1+size]
            expected.extend([indices[i:i+3].tolist() if i%2==0 else [int(indices[i+1]),int(indices[i]),int(indices[i+2])] for i in range(size-2)])
            cursor+=size+1
        assert cursor==ni
        np.testing.assert_array_equal(triangles,expected)
        assert row['sourceAffine']==spl.IDENTITY and row['exactCategoricalVoxelBoundaryClaim'] is False
        total+=len(triangles)
    assert total==29130


@pytest.mark.parametrize('code',list(spl.STRUCTURES))
def test_every_label_boundary_is_exact_complete_and_outward(code,manifest):
    labels=np.frombuffer(decoded(manifest['labelVolume']),'<i2').reshape((256,256,256),order='F')
    row=next(row for row in manifest['labelMeshes'] if row['code']==code)
    world,indices=mesh(row);world=world.astype(float)
    assert np.all(world*2==np.rint(world*2))
    wc=world[indices];normal_world=np.cross(wc[:,1]-wc[:,0],wc[:,2]-wc[:,0])
    assert np.all(np.sum(normal_world**2,axis=1)==1)
    # Direct inverse of the declared source permutation and origin, independent of the generator.
    source=128.-world[:,[1,2,0]];corners=source[indices]
    normal_source=-normal_world[:,[1,2,0]]
    owner=np.rint(corners.mean(1)-normal_source*.25).astype(int)
    assert np.all((owner>=0)&(owner<256)) and np.all(labels[tuple(owner.T)]==code)
    neighbor=owner+normal_source.astype(int);inside=np.all((neighbor>=0)&(neighbor<256),axis=1)
    assert np.all(labels[tuple(neighbor[inside].T)]!=code)
    axis=np.argmax(abs(normal_source),axis=1);sign=normal_source[np.arange(len(axis)),axis]
    keys=np.ravel_multi_index(tuple(owner.T),labels.shape)*6+axis*2+(sign>0)
    order=np.argsort(keys,kind='stable');unique,counts=np.unique(keys[order],return_counts=True)
    assert np.all(counts==2)
    pairs=corners[order].reshape(-1,2,3,3)
    common=(pairs[:,0,:,None,:]==pairs[:,1,None,:,:]).all(-1).any(-1)
    assert np.all(common.sum(1)==2)
    shared=pairs[:,0][common].reshape(-1,2,3)
    assert np.all(np.sum((shared[:,0]-shared[:,1])**2,axis=1)==2)
    mask=labels==code;padded=np.pad(mask,1);expected=[]
    for a in range(3):
        for direction in (-1,1):
            slices=[slice(1,257)]*3;slices[a]=slice(1+direction,257+direction)
            expected.append(np.flatnonzero((mask & ~padded[tuple(slices)]).ravel())*6+a*2+(direction>0))
    np.testing.assert_array_equal(unique,np.sort(np.concatenate(expected)))
    volume=np.einsum('ij,ij->i',wc[:,0],np.cross(wc[:,1],wc[:,2])).sum()/6
    assert volume==np.count_nonzero(mask)==row['sourceVoxelCount']
    assert row['allComponentsAndCavitiesRetained'] and row['allCellFacesExact']


def test_three_reports_append_distinct_bounded_source_context():
    curriculum=Curriculum();refs=spl.references()
    assert set(refs)==spl.BINDINGS
    for identifier in refs:
        ref=detail(curriculum,resolve(identifier))['radiology_reference']
        item=next(item for item in ref['source_native_inspectors'] if item['id']==spl.IDENTIFIER)
        assert item==refs[identifier][0]
        assert all(item[flag] is False for flag in spl.APPROVAL_FLAGS)
        assert item['source_grain']['subject_count']==1
        assert item['source_grant']['terms_url']==spl.PREFIX+'LICENSE.txt'
        assert 'subiculum' in item['caption'] and 'fornices' in item['caption']
        assert ref['reporting']['checklist'] and ref['report_templates'] and ref['walkthrough']['steps']
        media=next(m for m in curriculum.node(ref['investigation']['module_id'])['lesson_media'] if m['kind']=='source-native-inspectors' and identifier in m['investigation_ids'])
        assert media
        if identifier in {'ra.mri-epilepsy','ra.mri-dementia'}:
            assert any(item['id']=='hippunfold-hcp101006-registered-reference' for item in ref['source_native_inspectors'])


@pytest.mark.parametrize('asset',['../index.html','originals%2FModel_17_left_hippocampus.vtk.gz','/index.html','originals/../LICENSE.txt','missing.gz',''])
def test_unknown_and_noncanonical_paths_rejected(asset):
    with pytest.raises(ValueError,match='Unknown'):spl.validate_file(asset)


@pytest.mark.parametrize('asset',['T1.bin.gz','originals/Model_17_left_hippocampus.vtk.gz','index.html'])
def test_corrupt_nonregular_and_symlink_files_never_use_hosted_fallback(asset,tmp_path,monkeypatch):
    spl.registry();monkeypatch.setattr(spl,'ROOT',tmp_path);monkeypatch.setenv('VERCEL','1')
    path=tmp_path/'web/anatomy'/spl.ATLAS/asset;path.parent.mkdir(parents=True);path.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='bytes changed'):spl.validate_file(asset)
    path.unlink();path.mkdir()
    with pytest.raises(ValueError,match='regular'):spl.validate_file(asset)
    path.rmdir();path.symlink_to(ASSETS/asset)
    with pytest.raises(ValueError,match='regular'):spl.validate_file(asset)


def test_missing_registered_sources_use_hosting_only_on_vercel(tmp_path,monkeypatch):
    spl.registry();monkeypatch.setattr(spl,'ROOT',tmp_path);monkeypatch.delenv('VERCEL',raising=False)
    with pytest.raises(ValueError,match='missing'):spl.validate_file('T1.bin.gz')
    monkeypatch.setenv('VERCEL','1');spl.validate_file('T1.bin.gz')
    for asset in spl.AUTHORED:
        with pytest.raises(ValueError,match='missing'):spl.validate_file(asset)


def test_authentication_exact_bytes_encoded_path_rejection_and_private_caching(monkeypatch):
    from fastapi.testclient import TestClient
    import primer.server as server
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV,'source-test')
    monkeypatch.setenv(server.ACCESS_PASSWORD_ENV,'isolated-source-test-password')
    monkeypatch.delenv('VERCEL',raising=False)
    # No lifespan and no learner API operations; this delivery test does not create or change a learner record.
    client=TestClient(server.app)
    try:
        for asset in ['index.html','T1.bin.gz','originals/Model_17_left_hippocampus.vtk.gz']:
            assert client.get(spl.PREFIX+asset,follow_redirects=False).status_code==401
        for asset in ['index.html','manifest.json','label-3003.mesh.gz','originals/Model_17_left_hippocampus.vtk.gz','LICENSE.txt']:
            response=client.get(spl.PREFIX+asset,auth=('source-test','isolated-source-test-password'))
            assert response.status_code==200 and response.content==(ASSETS/asset).read_bytes()
            assert response.headers['cache-control']=='private, no-store'
            if asset=='index.html':assert "frame-ancestors 'self'" in response.headers['content-security-policy']
        for asset in ['originals%2FModel_17_left_hippocampus.vtk.gz','%69ndex.html','not-registered.gz']:
            assert client.get(spl.PREFIX+asset,auth=('source-test','isolated-source-test-password')).status_code==404
        response=client.head(spl.PREFIX+'T1.bin.gz',auth=('source-test','isolated-source-test-password'))
        assert response.status_code==200 and not response.content
        assert int(response.headers['content-length'])==spl.registry()['files']['T1.bin.gz']['bytes']
        monkeypatch.setenv('VERCEL','1')
        response=client.get(spl.PREFIX+'T1.bin.gz',auth=('source-test','isolated-source-test-password'),follow_redirects=False)
        assert response.status_code==307 and response.headers['location']=='/source-media/anatomy/spl-nac-limbic/T1.bin.gz'
    finally:client.close()


def test_registry_refresh_cannot_rebaseline_a_changed_source_review(tmp_path,monkeypatch):
    from tools.anatomy_sources import spl_limbic_registry as builder
    target=tmp_path/'docs/spl-limbic-source-review-20261016/source-review.json'
    target.parent.mkdir(parents=True)
    target.write_bytes((REVIEW/'source-review.json').read_bytes()+b' ')
    monkeypatch.setattr(builder,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='Pinned SPL source review changed'):
        builder.main()
    assert not (tmp_path/'data/radiology/spl-limbic-reference.json').exists()
