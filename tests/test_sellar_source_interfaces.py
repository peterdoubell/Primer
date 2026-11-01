"""Independent source geometry and deliberately bounded sellar source meaning."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1]
D=R/'docs/sellar-source-interfaces-review-20261101'
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def test_every_contact_and_schematic_is_checked_against_original_source_cells(tmp_path):
    output=tmp_path/'proof.json'
    result=subprocess.run([sys.executable,str(R/'tools/anatomy_sources/check_sellar_source_interfaces.py'),'--output',str(output)],cwd=R,capture_output=True,text=True,timeout=120)
    assert result.returncode==0,result.stdout+result.stderr
    proof=json.loads(output.read_bytes())
    assert proof['allPassed']and proof['sourceClasses']==21 and proof['allCandidatePairs']==210
    assert proof['contactPairs']==36 and proof['sourceFaces']==652 and proof['triangles']==1304
    assert proof['SVGsections']==108 and proof['sourceCellsIndependentlyReconstructedFromSVG']==55237
    assert proof['sourceFaceSectionSegmentsChecked']==378
    assert proof['allSourceFacesMatchedIndependentSixNeighbourOracle']and proof['allModelQuadsAreasWindingAndNativeCornersVerified']
    assert proof['allSVGSourceCellsAndContactSectionsVerifiedViaOriginalAffine']and not proof['anatomicalInterfaceVerified']


def test_native_mri_canvas_proof_reconstructs_original_samples(tmp_path):
    output=tmp_path/'pixels.json'
    result=subprocess.run([sys.executable,str(R/'tools/check_sellar_interfaces_mri_pixels.py'),'--output',str(output)],cwd=R,capture_output=True,text=True,timeout=120)
    assert result.returncode==0,result.stdout+result.stderr
    proof=json.loads(output.read_bytes())
    assert proof['allPassed']and proof['states']==288 and proof['actualCanvasPixelsCompared']==125927424
    assert proof['crosshairLocationsChecked']==1728 and not proof['sourceSamplesResampled']and not proof['anatomicalVisibilityVerified']
    browser=json.loads((D/'browser-proof.json').read_bytes())
    assert browser['allPassed']and browser['errors']==[]and browser['controlledLoopbackFixture']
    assert not browser['authenticatedAppVerified']and not browser['productionVerified']and not browser['clinicalApproval']
    assert len(browser['schematics'])==72 and len(browser['cameras'])==216
    assert {row['width']for row in browser['GPU']}=={390,1440}
    assert all(row['cullingDisabled']for row in browser['GPU'])
    for name,digest in browser['sourceSHA256'].items():assert sha((D/'viewer'/name).read_bytes())==digest
    camera=json.loads((D/'camera-proof.json').read_bytes())
    assert camera['allPassed']and camera['actualGPUUniformCameraStates']==216
    assert camera['maxAbsoluteClipCoordinate']<1 and camera['maxGPUCameraBasisRigidError']<2e-7


def test_all_sellar_requirements_and_opposite_side_contacts_remain_explicit():
    requirement=next(r for r in json.loads((R/'data/radiology/non-msk-structure-requirements.json').read_bytes())['investigations']if r['investigation_id']=='ra.mri-sella')
    mapping=json.loads((D/'requirement-source-granularity.json').read_bytes())
    assert mapping['requirementRecordSHA256']==sha(json.dumps(requirement,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
    expected={part['id']for s in requirement['structures']for part in s['required_parts']}
    actual={part['requirementId']for s in mapping['structures']for part in s['requiredParts']}
    assert actual==expected and len(actual)==840 and len(mapping['structures'])==131
    assert mapping['representationObligations']==2520 and mapping['partsWithSourceContactCandidates']==12
    assert not mapping['clinicalApproval']and not mapping['completeReportingCoverage']and not mapping['wholeGoalComplete']
    for structure in mapping['structures']:
        assert not structure['completeStructureApproved']
        for p in structure['requiredParts']:
            assert all(p[key]is False for key in ['completeRequiredPartApproved','imageAnatomicalApproval','schematicAnatomicalApproval','modelAnatomicalApproval'])
    manifest=json.loads((D/'manifest.json').read_bytes());opposite=[row for row in manifest['models']if row['oppositeSideNamedSourceContact']]
    assert {tuple(row['sourceCodes'])for row in opposite}=={(78,216),(383,388),(384,389),(3002,3003)}
    assert sum(row['sourceFaces']for row in opposite)==23
    index=json.loads((D/'evidence-index.json').read_bytes())
    for name,digest in index['evidenceSHA256'].items():assert sha((D/name).read_bytes())==digest,name
    for name,digest in index['sourceSHA256'].items():assert sha((R/name).read_bytes())==digest,name
