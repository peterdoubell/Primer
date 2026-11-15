#!/usr/bin/env python3
"""Bind carotid source figures and references without unobserved normal findings or borrowed patient anatomy."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
INV='ra.carotid-obstruction'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def integrate():
    folder=ROOT/'docs/carotid-obstruction-source-review';folder.mkdir(exist_ok=True)
    pool_path=ROOT/'data/radiology/investigation-source-images.json';pool=json.loads(pool_path.read_text())
    archive=folder/'held-legacy-and-unavailable-source-mappings.json'
    if not archive.exists():
        save(archive,{'legacy_images':pool.get(INV,[]),
          'reason':'Legacy remote thumbnails have no independently established commercial redistribution grant; complete licensed local figures replace them.',
          'unavailable_unmapped_originals':['FJ4809','FJ7563','FJ7563M','FJ7588','FJ7588M'],
          'unavailable_reason':'Original download service returned no objects for these unmapped metadata entries; no proxy, mirrored substitute or imagined geometry is published.',
          'excluded_wrong_candidate':{'id':'FJ7564','actual_producer_filename':'right digastricus posterior belly.obj','published_as_carotid':False},
          'held_left_ICA_mapping':'FJ3483 has the previously documented internal/common-carotid label and source-extent conflict; not substituted into the right reference.'})
    pool.pop(INV,None);save(pool_path,pool)
    path=ROOT/'data/radiology/reporting-steps/neuroradiology.json';data=json.loads(path.read_text());entry=data['investigations'][INV] if 'investigations' in data else data[INV]
    ids={row['figure_number']:row['id'] for row in json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV]
         if row['source_url']=='https://pmc.ncbi.nlm.nih.gov/articles/PMC6377693/'}
    near2020='open-carotid-obstruction-pmc7160198-fig2';near2026='open-carotid-obstruction-pmc12866240-fig1'
    entry['start']={'images':[near2026,ids[12]],'module_illustrations':False}
    entry['preset_mode']='assessment-prompts'
    entry['walkthrough_reviewed_at']='2026-10-10'
    entry['model']={'family':'neck','reporting_aim':'Use source references only for their retained acquired or curated extent. The schematic neck is orientation, not complete bilateral carotid lumen/wall, plaque, dissection or intracranial collateral anatomy. No reference is registered to the current patient.'}
    steps=entry['steps']
    prompts=[
      'Source adequacy and coverage [__]. Each observed side, vessel segment, plaque/wall finding and unresolved source boundary [__]. Unassessed origin, branch or vessel extent [__].',
      'Lumen and reference evaluability [__]. Observed minimum lumen, actual named reference site/diameter and method [__]. Distal ICA calibre, comparison ICA/ECA and possible full or subtler distal collapse [__]. Reasons grading is withheld or unresolved [__].',
      'Actual acquisition and temporal adequacy [__]. Observed stump, non-opacified extent, distal contrast/reconstitution and uncertainty [__]. Unacquired delayed phase or distal vessel coverage [__].',
      'Wall/vasculopathy source adequacy [__]. Observed flap, mural signal, channel, aneurysm or bead-like morphology [__]. Unresolved wall layers, channels and unassessed source extent [__].',
      'Acquired intracranial/contralateral coverage and comparison adequacy [__]. Observed runoff, collaterals, variant anatomy and source-supported interval change [__]. Unassessed vessels, perfusion and timing limitations [__].'
    ]
    for step,prompt in zip(steps,prompts):
        step['normal']={section:prompt for section in step['sections']}
    steps[0]['images']=[ids[12],ids[14]]
    steps[0]['look']='Trace actual covered arch origins, common carotid course, bifurcation, ICA and ECA on each side using the acquired source images and suitable reformats. Describe the supplied plaque/wall and surrounding tissue interfaces; a generic tube or selected publication view does not establish every branch or wall layer.'
    steps[0]['anatomy_note']='The curated right trunk reference and native CT label reference are separate source contexts, not a reconstructed bilateral current-patient carotid tree. Neither independently resolves lumen versus intima/media/adventitia or pathological plaque components.'
    steps[1]['images']=[near2020,near2026]
    steps[1]['detail']='Assess the supplied minimum lumen and distal ICA, first excluding an unsuitable or collapsed reference. Distal reduction may be threadlike or subtler and normal-appearing; retain full-collapse versus without-full-collapse distinctions.'
    steps[1]['findings']=['[Side/site] source-supported conventional stenosis of [__]% by [method], with actual reference site and quality [__].',
       'Near-occlusion concern: severe proximal narrowing with source-supported distal ICA reduction [with full collapse / without full collapse / unresolved]. No routine percentage grade is assigned to a collapsed reference.']
    steps[1]['look']='For suitable conventional NASCET assessment, record the actual narrowest lumen and disease-free distal ICA reference, method and plane. Review both distal ICAs, ipsilateral ECA and supplied intracranial variants/obstructions. Do not use bulb calibre, a collapsed vessel, an unvalidated model surface or an inadequate source as an interchangeable reference.'
    steps[1]['tip']='Near-occlusion can occur without a threadlike full collapse. Small ICA calibre alone is insufficient: assess severe proximal disease, expected calibre, comparison vessels, variants and distal disease together. Do not calculate a routine NASCET percentage from a reduced/collapsed distal reference.'
    steps[2]['images']=[near2026]
    steps[2]['look']='Use the actual complete covered lumen, source quality, contrast acquisition and any supplied delayed imaging to assess non-opacification, true occlusion, near-occlusion/slow filling and pseudo-occlusion from distal intracranial disease. Single-phase absence of contrast or a static MRA display cannot independently establish complete occlusion.'
    steps[2]['tip']='Separate source-observed non-opacification from confirmed occlusion. Record what was acquired, any unresolved timing/flow limitation and the actual distal examination; do not invent delayed-phase confirmation.'
    steps[3]['images']=[ids[n] for n in [11,12,13,14,15,16]]
    steps[3]['look']='Inspect actual acquired wall and lumen data for dissection, flap/true-false channels, mural haematoma, pseudoaneurysm and supplied non-atherosclerotic morphology. Fat-suppressed T1 and angiographic findings require their actual acquisition context. Source diagrams illustrate concepts, not independently resolved patient wall thickness or exact dissection planes.'
    steps[3]['tip']='Typical location or a bead-like outline is not independent proof of tissue identity, cause or vessel patency. Describe acquired morphology and limits. Static vocal-fold medialisation in a source trauma case does not independently establish functional paralysis or a unique nerve injury.'
    steps[4]['images']=[near2026,ids[16]]
    steps[4]['look']='Trace each actually covered intracranial vessel, contralateral carotid and available collateral route. Retain anatomical variants, distal tandem obstruction, unacquired territories and comparison-method/timing limits. A visible artery or flat MRA rendering does not prove functional collateral flow, cerebral perfusion or a registered interval change.'
    save(path,data)
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());guide=data[INV]['reporting']
    guide['reviewed_at']='2026-10-10'
    guide['protocol']=['State the actual CTA, MRA, Doppler or angiographic acquisition, phase/timing, source quality and coverage. Review each covered arch origin, common carotid, bifurcation, ICA/ECA, distal calibre and intracranial extent; retain unassessed sites.']
    guide['measurements'][0]['method']='When the source supports conventional NASCET assessment, specify the actual minimum lumen diameter, disease-free distal ICA reference site/diameter, acquisition and measurement plane. Keep diameter, area and ultrasound velocity criteria distinct; no grading is obtained from reference atlas meshes.'
    guide['measurements'][0]['pitfall']='Withhold a routine percentage when near-occlusion/distal collapse, unsuitable reference, unresolved lumen or inadequate acquisition invalidates the denominator. Distal reduction need not be threadlike; asymmetry alone is not a diagnosis.'
    guide['pitfalls']=['Near-occlusion with or without full collapse is not ordinary percentage stenosis; evaluate proximal severity and expected distal calibre with comparison vessels, variants and distal disease.',
       'Non-opacification, slow filling, distal intracranial pseudo-occlusion and MRA flow artefact require actual adequate source/timing assessment; a still image cannot substitute for missing phases or flow evidence.',
       'Imaging morphology, microscopic wall/tissue identity, haemodynamic significance and clinical function remain separate. Only actual source-supported observations enter the report.']
    guide['sources'] += [s for s in [
       {'title':'Johansson et al. 2020: CTA near-occlusion detection','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC7160198/'},
       {'title':'Johansson, Barud and Strömberg 2026: near-occlusion diagnostic review','url':'https://doi.org/10.1093/esj/23969873251355158'},
       {'title':'Pathology of the carotid space: arterial source examples','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6377693/'}]
       if s['url'] not in {r['url'] for r in guide['sources']}]
    save(path,data)
    path=ROOT/'data/radiology/source-anatomy-references.json';refs=json.loads(path.read_text())
    atlas=ROOT/'web/anatomy/bp3d-carotid-4.3/manifest.json';m=json.loads(atlas.read_text())
    curved={'id':'bp3d-carotid-4.3-original-right-trunks','label':'Original right carotid source trunks · curated, incomplete reporting scope',
      'atlas':'bp3d-carotid-4.3','family':'carotid-right-source','manifest_url':'/app/anatomy/bp3d-carotid-4.3/manifest.json',
      'manifest_sha256':sha(atlas),'initial_layer':'source-surfaces','initial_cropped':False,'population_note':'Curated adult-male right common, external and internal carotid source trunks. Independent of the native CT, published cases and current patient. Full original objects are retained, but left-side anatomy, branch completeness, junction continuity and separated lumen/wall or lesion tissues remain unapproved. Do not grade patient stenosis or infer patency from this reference. Source coordinates and calibration limits, full construction details and CC BY-SA2.1 Japan attribution are stated below.'}
    native=copy.deepcopy(next(r for r in refs['ra.ultrasound-thyroid'] if r['atlas']=='totalseg-v3-s0358'))
    native['id']='totalseg-v3-s0358-carotid-source-context';native['label']='Native CT common-carotid and adjacent labels · partial, not CTA grading'
    native['population_note']='Independent CT case s0358, source metadata female and age90; all eight original labels remain, including partial common-carotid interfaces and adjacent structures. This is not a dedicated carotid CTA or a matched current-patient/publication/curated-male examination. No complete ICA/ECA/bifurcation, separated wall/lumen or stenosis grade is supplied. The source grid is1.5mm; raw DICOM calibration, arterial phase, effective wall resolution and independent orientation remain unverified. Full source details are below.'
    refs[INV]=[curved,native];save(path,refs)
    print('Carotid reporting prompts and separate source contexts integrated; no unobserved normality or anatomical approval.')

if __name__=='__main__':integrate()
