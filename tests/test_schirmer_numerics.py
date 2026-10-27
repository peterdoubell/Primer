"""Independent original-sample, boundary and publication-legend checks."""
from pathlib import Path
import hashlib,json,subprocess,sys
import pytest
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/schirmer-vascular-review-20261026'
@pytest.mark.parametrize('tool',['check_schirmer_planes.py','check_schirmer_meshes.py','check_schirmer_semantics.py'])
def test_original_source_oracles(tool):
 r=subprocess.run([sys.executable,str(ROOT/'tools'/tool)],cwd=ROOT,text=True,capture_output=True,timeout=120);assert r.returncode==0,r.stdout+r.stderr;p=json.loads(r.stdout);assert p['allPassed']and p['clinicalApproval']is False
 if tool=='check_schirmer_planes.py':assert p['planes']==2328 and p['packs']==21 and p['sourceSamplesCompared']==86652384
 elif tool=='check_schirmer_meshes.py':assert len(p['rows'])==11 and p['triangles']==754024 and all(r['allSourceFacesExact']and r['outwardWinding']and r['closedOrientedEdges']and r['volumeExact']for r in p['rows'])
 else:
  assert p['totalInteriorSamples']==p['interiorMatches']==69328 and p['interiorBackground']==p['interiorWrongNamedClass']==0 and p['runtimeLabelsMatchVerifiedNames']
  assert len(p['negativeControls'])==48 and all(r['mismatches']>0 for r in p['negativeControls'])
  assert p['label19']=={'sourceIJK':[142,73,25],'sourceWorld':[-52,-53,-47],'voxels':1,'semanticName':None,'preserved':True}
def test_current_reader_and_recovery_evidence_are_bound_to_the_shipped_source():
 p=json.loads((DOC/'reader/viewer-proof.json').read_bytes());assert p['allPassed']and p['errors']==[]and not p['productionVerified']
 for f,digest in p['sourceSHA256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==digest,f
 assert len(p['viewControls'])==2 and all(v['enlargePreservesNativePixels']and v['scaleBarRemains20SourcePixels']and v['keyboardScroll']and v['cameraAndScalePreserveMesh']for v in p['viewControls'])
 assert len(p['cases'])==286 and len(p['gpu'])==22 and len(p['components'])==30
 assert {(c['viewport'],c['mode'],c['overlay'] if c['mode']=='mri'else c['context'])for c in p['cases']}=={(w,m,b)for w in [390,1440]for m in ['mri','schematic']for b in [False,True]}
 assert {(m['width'],m['nodeId'])for m in p['lessonMounts']}=={(w,n)for w in [390,1440]for n in ['rad.5.brain-anatomy','rad.4.stroke']}
 assert all(m['openedAndClosed']and m['singletonMeaningPreserved']for m in p['lessonMounts'])
 assert all(g['renderedNonbackgroundPixels']>100 and g['glError']==0 for g in p['gpu'])
 assert all(abs(plane['scaleBarSourcePixels']-20)<1e-6 and plane['scaleBarFullyVisible'] for c in p['cases']for plane in c['planes'])
 recovery=json.loads((DOC/'reader/recovery-proof.json').read_bytes());assert recovery['allPassed']and len(recovery['cases'])==6
 for f,digest in recovery['sourceSHA256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==digest,f
 r=subprocess.run([sys.executable,str(ROOT/'tools/check_schirmer_pixels.py')],cwd=ROOT,text=True,capture_output=True,timeout=120);assert r.returncode==0,r.stdout+r.stderr;pixels=json.loads(r.stdout);assert pixels['allPassed']and pixels['cases']==286 and pixels['planes']==858 and pixels['renderedPixelsCompared']==32168136 and pixels['singleton19PlaneChecks']==78
