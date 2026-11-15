"""Original source annotation frames are retained; no silent coordinate repair."""
from pathlib import Path
import gzip,hashlib,json
import nibabel as nib
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'docs/pituitary-case-source-review-20261101'
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def test_primary_source_rights_acquisition_and_original_annotation_conflict():
    metadata=json.loads((D/'figshare-27894084-v1.json').read_bytes())
    assert metadata['doi']=='10.6084/m9.figshare.27894084.v1'
    assert metadata['license']['url']=='https://creativecommons.org/licenses/by/4.0/'
    acquisition=json.loads((D/'case-1-acquisition.json').read_bytes());review=json.loads((D/'case-1-source-review.json').read_bytes())
    assert acquisition['sourceFileId']==50793273 and acquisition['sourceArchiveBytes']==47245902155
    assert not acquisition['fullArchiveDownloaded']and not acquisition['sourceFilesChanged']
    assert not acquisition['sourceImagesAreAcquisitionNative']and len(acquisition['files'])==4
    assert len(review['panels'])==12 and not review['coordinateConflictResolvedByPrimer']
    assert review['sourceSformAndQformAlternativesRetained']and not review['sourceRegistrationFitted']
    assert not review['tumourAndNormalGlandSeparatelyLabelled']and not review['carotidWallAndIndividualBranchesSeparatelyLabelled']
    assert not review['clinicalApproval']and review['sourceMaskOverlapCells']==0
    case=json.loads((D/'case-1-source-metadata.json').read_bytes());cells={r['column']:r for r in case['sourceReportedCells']}
    assert case['duplicateWorkbookHeadingsRetained']and cells['C']['heading']==cells['F']['heading']=='Voxel (mm)'
    assert cells['C']['sourceValue']=='0.488 x 0.488 x 1.5'and cells['F']['sourceValue']=='/'
    assert case['sourceVolumeValuesAgree']and case['sourceMaskVolumeMm3']==case['sourceWorkbookMaskVolumeMm3']==802
    for name,voxels in [('1_carotids_f.nii.gz',13196),('1_tumor_f.nii.gz',6416)]:
        path=D/'original-annotations'/name;record=next(r for r in acquisition['files']if r['sourceFile']==name)
        assert sha(path.read_bytes())==record['sha256']
        image=nib.load(path);data=np.asanyarray(image.dataobj)
        assert image.shape==(499,404,342)and image.header.get_zooms()==(.5,.5,.5)
        assert np.array_equal(np.unique(data),[0,1])and np.count_nonzero(data)==voxels
        assert np.max(abs(image.get_qform()-image.get_sform()))==22.5
        assert int(image.header['qform_code'])==int(image.header['sform_code'])==1
    index=json.loads((D/'evidence-index.json').read_bytes())
    for name,digest in index['evidenceSHA256'].items():assert sha((D/name).read_bytes())==digest,name
    for name,digest in index['sourceSHA256'].items():assert sha((R/name).read_bytes())==digest,name
