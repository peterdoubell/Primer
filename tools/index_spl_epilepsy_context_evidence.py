"""Bind the focused context experiment and source-grain reconciliation."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'docs/epilepsy-source-context-review-20261101';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 reader=json.loads((D/'reader/proof.json').read_bytes());grain=json.loads((D/'requirement-source-granularity.json').read_bytes())
 assert reader['allPassed']and len(reader['cases'])==4 and not reader['clinicalApproval']and not reader['productionLearnerWrites']
 assert sum(len(c['pixelCases'])for c in reader['cases'])==480
 assert sum(p['pixels']for c in reader['cases']for p in c['pixelCases'])==34979840
 assert len(grain['pairedRequirements'])==12 and len(grain['retainedOtherContractGroups'])==6 and not grain['completeReportingCoverage']
 for proof in [reader,grain]:
  for file,digest in proof['sourceSHA256'].items():assert sha(R/file)==digest,file
 extra=['primer/spl_epilepsy_reference.py','tools/anatomy_sources/spl_epilepsy_context_prepare.py','tools/check_epilepsy_source_granularity.py','tools/spl_epilepsy_runtime_compatibility.py','tools/index_spl_epilepsy_context_evidence.py','tests/test_spl_epilepsy_context.py']
 sources={**reader['sourceSHA256'],**grain['sourceSHA256'],**{name:sha(R/name)for name in extra}}
 result={'scope':'Exact source context and interaction checks, not clinical/anatomical approval','nativeMRIPixelCases':480,'actualCanvasPixelsCompared':34979840,'authenticatedSyntheticMounts':4,'initialSourceLabelClasses':18,'allAvailableSourceLabelClasses':217,'anatomicalSourcePayloadsChanged':False,'combinedSourceClassesRemainCombined':True,'clinicalApproval':False,'completeReportingCoverage':False,'wholeGoalComplete':False,'priorFailedAttempt':'reader/initial-partial-proof.json','sourceSHA256':sources,'proofSHA256':{str(p.relative_to(D)):sha(p)for p in sorted(D.rglob('*.json'))if p.name!='evidence-index.json'}}
 (D/'evidence-index.json').write_text(json.dumps(result,indent=2)+'\n');print({k:result[k]for k in ['nativeMRIPixelCases','actualCanvasPixelsCompared','initialSourceLabelClasses','clinicalApproval']})
if __name__=='__main__':main()
