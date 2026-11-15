"""Portable checks for the complete provided-plane recipe and captured source view."""
from pathlib import Path
import gzip,hashlib,json
import nibabel as nib
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'docs/pituitary-case-source-review-20261101/provided-plane-reader'
sha=lambda b:hashlib.sha256(b).hexdigest()

def manifest():return json.loads(gzip.decompress((D/'manifest.json.gz').read_bytes()))

def test_all_provided_plane_ranges_and_original_header_forms_are_retained():
    m=manifest();proof=json.loads((D/'independent-proof.json').read_bytes())
    assert proof['allPassed']and proof['volumeCount']==4 and proof['planeMembers']==4980 and proof['packFiles']==82
    assert proof['providedVoxelValuesIndependentlyReconstructed']==827349984
    assert proof['manifestSHA256']==sha(gzip.decompress((D/'manifest.json.gz').read_bytes()))
    assert not proof['sourceHeaderChanged']and not proof['sourceImageResampled']and not proof['coordinateConflictResolved']and not proof['clinicalApproval']
    assert set(m['volumes'])=={'T1CE','T2','tumourGland','carotids'}and sum(r['bytes']for r in m['packs'].values())==1223389436
    ends={};count=0
    for v in m['volumes'].values():
        assert v['shape']==[499,404,342]and not v['acquisitionNative']and not v['sourceSamplesResampledByPrimer']
        for axis in range(3):
            rows=v['planes'][str(axis)];assert len(rows)==v['shape'][axis]
            for index,row in enumerate(rows):
                assert row['sourceIndex']==index and row['sourceFixedAxis']==axis
                assert {axis,row['horizontalNativeAxis'],row['verticalNativeAxis']}=={0,1,2}
                assert row['decodedBytes']==row['width']*row['height']*np.dtype(v['dtype']).itemsize
                assert row['offset']==ends.get(row['pack'],0)
                ends[row['pack']]=row['offset']+row['compressedBytes'];count+=1
    assert count==4980 and set(ends)==set(m['packs'])
    assert all(end==m['packs'][name]['bytes']and end<=16*1024*1024 for name,end in ends.items())
    for key in ['tumourGland','carotids']:
        assert np.max(abs(np.asarray(m['volumes'][key]['originalQform'])-m['volumes'][key]['originalSform']))==22.5
    affine=json.loads((D/'sform-nearest-index-proof.json').read_bytes())
    assert len(affine['rows'])==8 and not affine['qformDiscrepancyResolved']
    for row in affine['rows']:
        assert row['maxCornerComponentDeviationSourceVoxels']<.5 and row['nearestSourceIndexIsIdentityOverWholeGrid']and row['noAffineCoefficientRoundedOrChanged']


def test_portable_original_planes_and_initial_render_match_without_large_volume_downloads():
    samples=json.loads((D/'verification-planes/index.json').read_bytes());m=manifest();decoded={}
    for sample in samples:
        packed=(D/'verification-planes'/sample['file']).read_bytes();row=sample['entry'];assert sha(packed)==row['compressedSHA256']
        raw=gzip.decompress(packed);assert len(raw)==row['decodedBytes']and sha(raw)==row['decodedSHA256']
        a=np.frombuffer(raw,dtype=sample['dtype']).reshape(row['height'],row['width']);decoded[sample['volume'],row['sourceFixedAxis']]=a
        if sample['volume']in ['tumourGland','carotids']:
            original=nib.load(D.parent/'original-annotations'/m['volumes'][sample['volume']]['sourceFile']);assert np.array_equal(a,np.take(np.asanyarray(original.dataobj),row['sourceIndex'],axis=row['sourceFixedAxis']).T)
    cases=json.loads((D/'browser/browser-cases.json').read_bytes());selected=[c for c in cases if c['point']==[246,271,118]];assert len(selected)==8
    for case in selected:
        for canvas in case['canvases']:
            spec=canvas['state']['spec'];state=canvas['state'];axis=canvas['axis'];y,x=np.indices((spec['height'],spec['width']));u=spec['high'][spec['u']]-x;v=spec['high'][spec['v']]-y;signal=decoded[case['contrast'],axis][v,u].astype(float);grey=np.floor(np.clip(255*(signal-(state['center']-state['width']/2))/state['width'],0,255)).astype(np.uint8);rgb=np.repeat(grey[...,None],3,axis=2)
            if canvas['mode']=='marked':
                for key,on,color in [('tumourGland',state['complex'],[255,168,52]),('carotids',state['carotids'],[92,210,244])]:
                    mask=decoded[key,axis][v,u]!=0
                    if on:rgb[mask]=np.floor(.55*rgb[mask]+.45*np.asarray(color)+.5).astype(np.uint8)
            rgba=np.concatenate([rgb,np.full((*grey.shape,1),255,np.uint8)],axis=2)
            assert sha(rgba.tobytes())==canvas['sha256']
    b=json.loads((D/'browser/browser-proof.json').read_bytes());p=json.loads((D/'browser/pixel-proof.json').read_bytes())
    assert b['allPassed']and b['errors']==[]and len(b['initialLoads'])==2
    assert all(r['rangeRequests']==9 for r in b['initialLoads'])
    assert all(r['bytes']<=16*1024*1024 for r in b['cacheStates'])
    assert p['allPassed']and p['actualPlainAndMarkedCanvasPixelsCompared']==21280840 and p['sourceSamplesAndCoordinateProbesChecked']==240
    assert not p['imageResamplingAppliedByPrimer']and not p['coordinateConflictResolved']and not p['clinicalApproval']
    for name,digest in b['sourceSHA256'].items():assert sha((D/'provided-plane-viewer'/name).read_bytes())==digest
    index=json.loads((D/'evidence-index.json').read_bytes())
    for name,digest in index['evidenceSHA256'].items():assert sha((D/name).read_bytes())==digest,name
    for name,digest in index['sourceSHA256'].items():assert sha((R/name).read_bytes())==digest,name



def test_source_fetch_failures_and_context_loss_have_verified_recovery():
    proof=json.loads((D/'browser/lifecycle-proof.json').read_bytes())
    assert proof['allPassed']and proof['controlledFixture']and proof['errors']==[]and not proof['clinicalApproval']
    assert all(proof[k]for k in ['metadataFailureRetryPreservesIndependentModels','invalidRangeRejectedAndRetryRecovers','rapidChangesRetainLatestContrastAndSourcePoint','modelFailureRetryPreservesIndependentMRI','contextLossRestoresOriginalModels'])
