"""Current atlas extension preserves old entries and exact native-label evidence."""
import copy,gzip,hashlib,json
from pathlib import Path
from primer.holiatlas_reference import references,registry,metadata_bytes
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/holiatlas-schematic-review-20261026'
def test_append_only_regions_and_original_metadata_are_preserved():
 before=(D/'before-hierarchy.json').read_bytes();current=json.loads(metadata_bytes('hierarchy.json'));old=json.loads(before)
 assert current['presentClasses']==81 and current['totalTriangles']==22598628
 rows=current['levels']['composition']['sourceClasses'];assert len(rows)==18 and rows[:16]==old['levels']['composition']['sourceClasses']
 assert [(r['code'],r['fineSourceCodes']) for r in rows[16:]]==[(17,[170,178]),(18,[171,179])]
 restored=copy.deepcopy(current);restored['levels']['composition']['sourceClasses']=rows[:16];restored['levels']['composition']['totalTriangles']-=284304;restored['presentClasses']-=2;restored['totalTriangles']-=284304
 assert (json.dumps(restored,indent=2)+'\n').encode()==before
 assert gzip.decompress((D/'before-hierarchy.json.gz').read_bytes())==before
 assert all(r['exclusionsAndLimits'] for r in rows[16:])
def test_runtime_registry_and_authenticated_native_pixel_evidence():
 assert references();r=registry();assert len(r['files'])==851 and r['hierarchy_components26']==743
 proof=json.loads((D/'reader/viewer-browser-proof.json').read_bytes());native=json.loads((D/'reader/viewer-native-proof.json').read_bytes())
 assert proof['allPassed'] and proof['authenticatedReader'] and proof['errors']==[]
 for path,digest in proof['sourceSHA256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
 assert native['allPassed'] and native['planes']==48 and native['nativePixelsCompared']==7124160
 assert native['mriCases']==48 and native['mriPlanes']==144 and native['mriNativePixelsCompared']==21372480
 assert native['browserProofSHA256']==hashlib.sha256((D/'reader/viewer-browser-proof.json').read_bytes()).hexdigest()
 assert not native['clinicalApproval'] and not native['productionVerified']


def test_current_reporting_context_names_exact_unions_without_completion_claims():
 context=json.loads((D/'current-reporting-context.json').read_bytes())
 assert context['hierarchySHA256']==hashlib.sha256(metadata_bytes('hierarchy.json')).hexdigest()
 assert [(r['source_selection']['code'],r['source_selection']['fine_codes']) for r in context['rows']]==[(17,[170,178]),(18,[171,179])]
 assert all(not r['clinical_requirement_complete'] and len(r['available_representations'])==3 and r['limits'] for r in context['rows'])
