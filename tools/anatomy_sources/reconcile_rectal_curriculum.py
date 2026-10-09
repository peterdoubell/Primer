#!/usr/bin/env python3
"""Reconcile rectal teaching with reviewed primary sources; preserve assessment structure."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NODE = 'rad.5.rectal-mr'
PRIMARY = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC13212678/'
RESTAGING = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC13212783/'
ANATOMY = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC9849549/'
FISTULA = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC13512459/'


def write_entry(path, entry):
    text = path.read_text()
    start = text.index('{', text.index('"' + NODE + '"'))
    _, end = json.JSONDecoder().raw_decode(text, start)
    path.write_text(text[:start] + json.dumps(entry, indent=2, ensure_ascii=False).replace('\n', '\n  ') + text[end:])


def reconcile(node):
    node['goal'] = ('Report rectal MRI anatomy, primary staging and post-treatment findings with source quality and confidence; '
                    'map each demonstrated perianal tract and extension, and distinguish imaging assessment from pathology and treatment decisions.')
    ref = node['reference']
    old_source = next((s for s in [ref['source'], *ref.get('also', [])]
                       if s['url'].startswith('https://radiologyassistant.nl/')), None)
    if old_source is None:
        raise ValueError('Retain the original Radiology Assistant reading citation')
    ref['source'] = {'title': 'ESGAR 2026 Part I: primary rectal MRI staging', 'url': PRIMARY,
                     'publisher': 'ESGAR Rectal Imaging Guideline Group / European Radiology'}
    ref['also'] = [
        {'title': 'ESGAR 2026 Part II: restaging and response evaluation', 'url': RESTAGING,
         'publisher': 'ESGAR Rectal Imaging Guideline Group / European Radiology'},
        {'title': 'Original MRI anatomy of the rectum', 'url': ANATOMY, 'publisher': 'Insights into Imaging'},
        {'title': 'Original perianal fistula imaging maps', 'url': FISTULA, 'publisher': 'Diagnostics'},
        old_source,
    ]
    ref['approach'] = [
        {'step': 'Confirm purpose and image quality', 'detail': 'Distinguish primary staging from restaging. Check actual coverage and tumour-aligned high-resolution T2 planes, slice thickness and in-plane sampling. For response assessment, read matched DWI/ADC with T2 and the supplied clinical/endoscopic findings.'},
        {'step': 'Locate the tumour and each landmark', 'detail': 'Report the lower and upper tumour borders relative to sigmoid take-off, anorectal junction, anal verge and peritoneal reflection. Measure height with the stated landmark and lumen-centre convention. ESGAR source sections use conflicting inequalities at exactly 5 cm: retain the measured value and the institution’s explicit definition.'},
        {'step': 'Trace the wall and actual invasive front', 'detail': 'Assess the resolved muscularis propria and deepest tumour front in appropriate planes; MRI may not distinguish T1 from T2. Measure maximal perpendicular extramural depth, separating definite tumour from uncertain desmoplastic change.'},
        {'step': 'Separate fascia from peritoneum and surgical margin', 'detail': 'Identify the closest qualifying primary tumour, EMVI or irregular node/deposit to the MRF, recording distance and confidence. Baseline MRF involvement is at 1 mm or less; a smooth-margin node alone at that distance does not make it involved. Peritoneal invasion is a separate T4a finding. The eventual surgical CRM depends on the actual operation and pathology.'},
        {'step': 'Follow vessels and each nodule', 'detail': 'Describe suspected EMVI from source tumour signal within an extramural vessel and its contour. Inventory mesorectal and lateral nodules by side, compartment, size and morphology, and give patient-level nodal confidence. Irregularity and vein continuity may suggest deposits but cannot establish histological N1c.'},
        {'step': 'Describe each low pelvic interface', 'detail': 'Report internal sphincter, intersphincteric space, external sphincter, puborectalis, levator and adjacent-organ involvement separately, with craniocaudal extent. Internal sphincter or intersphincteric involvement alone does not determine the rectal cT category; demonstrated skeletal-muscle invasion has different staging implications. MRI alone does not establish a feasible operation.'},
        {'step': 'Review the complete treated bed', 'detail': 'Include fibrotic remnants in tumour-bed extent. Combine actual T2 and DWI/ADC patterns with DRE/endoscopy and dated treatment context. State response class and uncertainty; mrTRG, fibrosis or absent restriction alone does not prove complete response. A reappearing fat pad and persistent MRF stranding require different interpretations.'},
        {'step': 'Map the fistula from the supplied planes', 'detail': 'Name every demonstrated internal/external opening, primary tract, branch, blind sinus, collection and deep extension. Record a clock-face convention and relation to each sphincter, puborectalis and levator. Source drawings and annotations are not native masks; a lithotomy clock convention does not verify acquisition position.'},
    ]
    ref['measure'] = [
        {'what': 'Extramural depth', 'how': 'Maximum perpendicular distance from the outer muscularis propria to the definite tumour front; record the source plane and unresolved stranding.', 'cutoff': 'Report the measured millimetres and adopted T3 subdivision; 11 mm is in the commonly used T3c band. Do not hide uncertainty or an exact boundary convention.'},
        {'what': 'Baseline tumour to MRF', 'how': 'Shortest distance from qualifying primary tumour, EMVI or irregular node/deposit; identify the component and level. Preserve smooth-node morphology separately.', 'cutoff': 'MRF+ at 1 mm or less for qualifying components. A smooth-margin node alone within 1 mm is MRF−. No separate baseline 1–2 mm threatened category is recommended by ESGAR 2026.'},
        {'what': 'Tumour height and length', 'how': 'Record actual endpoints, sigmoid take-off, anorectal junction and any additional anal-verge measurement; include the treated fibrotic bed at restaging.', 'cutoff': 'State the exact value, landmark and local definition. Do not resolve the source’s conflicting 5 cm equality convention by silently assigning a category.'},
        {'what': 'Baseline mesorectal nodes', 'how': 'Measure short axis and assess border, shape, internal signal and mucinous features. Combine individual suspicion with tumour risk and node burden.', 'cutoff': 'Size/morphology criteria express suspicion, not tissue proof; report cN0, possibly cN+ or cN+ with confidence. Baseline criteria do not automatically apply after treatment.'},
        {'what': 'Baseline lateral nodes', 'how': 'Keep obturator and internal iliac sides/compartments distinct; document short axis and morphology.', 'cutoff': 'ESGAR 2026 uses 7 mm or more for both compartments; morphology may support suspicion in 5–7 mm nodes, with limited evidence. No recommended lateral-node size threshold exists for restaging.'},
        {'what': 'Fistula and collection extent', 'how': 'Trace each actual tract and opening in native planes, and measure each collection in three dimensions with source calibration.', 'cutoff': 'Parks and St James categories describe demonstrated anatomy. Grade alone does not choose fistulotomy, drainage or a sphincter-sparing operation.'},
    ]
    ref['classify']['name'] = 'MRI anatomical extent and reporting implications'
    ref['classify']['columns'] = ['Category', 'Source observations', 'Meaning', 'Reporting implication']
    ref['classify']['rows'] = [
        ['T1–T2 range', 'No convincing extramural tumour in adequate supplied views', 'MRI may not separate T1 from T2', 'State quality, uncertainty and any relevant endoscopic/ultrasound or tissue evidence'],
        ['T3', 'Definite tumour beyond muscularis propria', 'Report maximal measured extramural depth', 'Describe adopted subdivision plus separate MRF, EMVI, nodes and other risk features'],
        ['T3 MRF+', 'Qualifying tumour component reaches within 1 mm of MRF', 'MRF involvement alone does not mean T4', 'Name the component, distance, level and confidence; distinguish the eventual surgical CRM'],
        ['T4a', 'Convincing invasion of actual peritoneal covering/reflection', 'Peritoneal invasion is distinct from MRF', 'Describe the invaded peritoneal interface; mere contact is insufficient'],
        ['T4b', 'Demonstrated adjacent-organ or specified skeletal-muscle invasion', 'External sphincter, puborectalis or levator involvement matters', 'Map each interface and extent; keep MRI inference and pathological stage separate'],
        ['After treatment', 'Actual T2 fibrosis/residual signal and matched diffusion findings', 'MRI contributes to response assessment', 'Combine with clinical/endoscopic context; detailed ycT may be unreliable in near-complete responders'],
    ]
    ref['classify']['note'] = ('Internal sphincter and intersphincteric involvement are reported separately and do not alone alter rectal cT. '
                              'MRI categories and anatomical risk features support multidisciplinary decisions; they do not automatically prescribe therapy or prove tissue clearance.')
    ref['modifiers'] = [
        {'code': 'EMVI', 'meaning': 'Report the source appearance and confidence; grades 3–4 are positive under the stated MRI grading scheme. Keep vascular invasion distinct from a separate nodule.'},
        {'code': 'MRF', 'meaning': 'Apply the baseline component/morphology rule separately from treated fibrosis. Persistent post-treatment stranding can be equivocal; a reappearing fat pad supports clearance.'},
        {'code': 'cN confidence', 'meaning': 'Combine suspicious nodes and deposits at patient level: cN0, possibly cN+ or cN+. Regional/nonregional classification depends on actual compartment and anal/dentate context.'},
        {'code': 'ycN', 'meaning': 'A 5 mm mesorectal short-axis threshold may inform restaging with limitations and response context. No recommended lateral-node restaging threshold is supplied by ESGAR 2026.'},
        {'code': 'Clinical / imaging / treated / pathological', 'meaning': 'Name the staging framework and actual evidence. Use post-treatment qualifiers for restaging; pathological stage and complete pathological response require tissue evidence.'},
    ]
    ref['template'] = ('TECHNIQUE AND CONTEXT\nPurpose, treatment/date and comparison [ ]. Actual T2 planes, coverage, sampling and quality [ ]. DWI/ADC acquisition or derivation and limitations [ ]. Contrast or not obtained [ ].\n\n'
        'SOURCE FINDINGS\nTumour/treated-bed endpoints, length and relation to sigmoid take-off, ARJ, verge and peritoneal reflection [ ]. Exact height/landmark/local convention [ ].\n'
        'Resolved wall and maximal definite extramural depth [ ]; uncertain or unassessed extent [ ]. MRI T assessment/framework/confidence [ ].\n'
        'MRF: nearest qualifying component, morphology, distance and level [ ]; baseline or treated interpretation [ ]. Peritoneum and each adjacent-organ interface [ ].\n'
        'Internal sphincter, intersphincteric space, external sphincter, puborectalis and levator, including each actual invaded or unresolved layer [ ].\n'
        'EMVI appearance, vessel and confidence [ ]. Each mesorectal/lateral nodule: side, compartment, size, morphology and deposit suspicion [ ]. Patient-level nodal confidence and regional context [ ].\n'
        'Restaging: complete fibrotic bed, residual signal and matched T2/DWI/ADC, response class/confidence and actual DRE/endoscopy/tissue correlation [ ].\n'
        'Fistula: view/clock convention, each demonstrated opening, primary route, sphincter crossing, branch, blind sinus, collection and deep extension [ ]. Prior operation/seton and clinical context [ ].\n\n'
        'IMPRESSION\nSource-supported anatomical assessment and confidence [ ]; uncovered tissue and limitations [ ]; separate supplied pathology [ ]. Multidisciplinary questions [ ]. No automatic histological diagnosis, pathological complete response or treatment decision from MRI alone.')
    ref['pitfalls'] = [
        'Conflating MRF involvement with pathological CRM or T4. Peritoneum, fascia and actual surgical margin are different interfaces.',
        'Treating any nearby node as MRF involvement, or reintroducing a baseline 1–2 mm threatened category. Preserve the qualifying component and smooth versus irregular morphology.',
        'Applying primary lateral-node criteria to restaging, using 9 mm for baseline obturator nodes, or omitting possibly cN+ confidence and regional context.',
        'Using a numerical ADC threshold to stage the primary tumour or prove nodal histology; DWI has specific adjunct and response roles.',
        'Treating fibrosis, mrTRG or absent diffusion restriction as proof of complete response, or forcing a fixed treatment or surveillance programme from selected MRI views.',
        'Inferring viable or acellular mucin from T2 signal, or treating a negative superficial biopsy as proof of clearance.',
        'Inferring an operation from sphincter involvement or fistula grade alone; actual extent, sepsis, continence, prior procedures and patient context require surgical assessment.',
        'Borrowing a drawing’s dentate line, clock convention or coloured tract fill as native MRI resolution, acquisition position, segmentation or registered 3D anatomy.',
    ]
    q = node['quiz']
    q[0]['explain'] = ('A blurred muscle border in an oblique segment can reflect partial volume rather than true invasion. Re-plan adequate small-field T2 images perpendicular to the tumour axis, using sagittal planning and an anal-canal-aligned coronal plane when relevant. ESGAR recommends slices no thicker than 3 mm and in-plane sampling below 1 × 1 mm. Sampling does not itself prove fine anatomical resolution. Routine contrast is not a substitute for correct T2 geometry, and absent extramural tumour on selected views does not independently separate T1 from T2.')
    q[1]['prompt'] = q[1]['prompt'].replace('How should the margin be reported, and what does it drive?', 'How should the baseline fascia finding be reported?')
    q[1]['answer'] = 'MRF involved by the primary at 0.9 mm; report the finding for multidisciplinary planning'
    q[1]['choices'][0] = q[1]['answer']
    q[1]['explain'] = ('The qualifying primary tumour is 0.9 mm from the MRF, so the baseline MRF assessment is involved under the 1 mm-or-less criterion. State the primary component, exact distance, level and quality. MRF involvement alone is not T4 and is not the pathological CRM, which depends on surgery and tissue assessment. ESGAR 2026 does not recommend a separate 1–2 mm threatened MRF category. This risk feature informs multidisciplinary planning but does not independently select a particular neoadjuvant regimen or operation.')
    q[2]['answer'] = 'Suspected EMVI, an adverse imaging risk feature to report separately for multidisciplinary planning'
    q[2]['choices'][0] = q[2]['answer']
    q[2]['explain'] = ('Concordant tumour-signal material within an expanded irregular extramural vein supports MRI EMVI. Describe the vessel, source observations, grade if used and confidence. EMVI is an adverse risk feature, but it does not by itself convert T3 to T4 or prescribe systemic therapy. A qualifying EMVI component within 1 mm of the MRF contributes to baseline MRF involvement. A separate irregular nodule may be suspicious for a deposit; MRI morphology does not establish histological distinction or N1c.')
    q[3]['prompt'] = q[3]['prompt'].replace('Applying the 2016 ESGAR consensus criteria, how should these be reported?', 'Using baseline mesorectal size/morphology criteria, how should individual-node suspicion be reported?')
    q[3]['answer'] = 'The 6 mm and 10 mm nodes are suspicious; round shape alone does not make the 4 mm node suspicious'
    q[3]['choices'][0] = q[3]['answer']
    q[3]['explain'] = ('The 6 mm node has two suspicious morphological features; the 10 mm node meets the baseline size criterion. The 4 mm node has only round shape, so it does not satisfy the stated small-node morphology rule. These criteria estimate suspicion, not proven malignant histology or pathological clearance of a small node. ESGAR 2026 retains individual mesorectal criteria within a patient-level assessment that also considers tumour risk and node burden, reported as cN0, possibly cN+ or cN+ with confidence. Lateral compartments and restaging require their own interpretation.')
    q[4]['prompt'] = q[4]['prompt'].replace('tumour signal reaches and thickens', 'convincing nodular tumour extension invades')
    q[4]['explain'] = ('The prompt supplies convincing invasion of the actual peritoneal interface, supporting an MRI T4a assessment. Mere contact or an equivocal thickened reflection is not sufficient. Peritoneum and MRF are separate boundaries; MRF involvement alone remains T3 MRF+. T4b requires demonstrated invasion of specified adjacent organs or structures. Preserved fat planes in the supplied views are useful observations but do not prove complete pathological clearance. Describe source evidence and confidence for multidisciplinary risk assessment rather than deriving a treatment regimen from the category alone.')
    q[5]['answer'] = 'Residual tumour is strongly suspected; report the discordant response findings for multidisciplinary reassessment'
    q[5]['choices'][0] = q[5]['answer']
    q[5]['explain'] = ('The focal intermediate T2 signal with corresponding restricted diffusion and a persistent ulcer raises strong concern for residual disease. It is not adequately described as uncomplicated fibrosis or T2 shine-through. Report the matched source findings, quality, treated-bed extent and response confidence, then reconcile the actual DRE/endoscopy and any tissue information. MRI alone cannot prove pathological response or prescribe resection. Near-complete response can evolve with time; suitability for organ preservation and reassessment timing depend on the complete clinical setting and an appropriate multidisciplinary programme.')
    q[6]['prompt'] = q[6]['prompt'].replace('predicted circumferential resection margin', 'shortest qualifying baseline tumour-component distance to the MRF')
    q[6]['explain'] = ('The qualifying EMVI component is nearest at 0.8 mm, so report 0.8 mm and identify the vein, level and confidence. The primary is farther away. Qualifying primary tumour, EMVI or an irregular node/deposit within 1 mm supports baseline MRF involvement; a smooth-margin node alone at that distance does not. This is an MRI MRF distance, not the measured pathological CRM. The post-treatment interpretation is different, and ESGAR 2026 does not recommend a separate baseline 1–2 mm threatened category.')
    q[7]['explain'] = ('Report the maximum definite perpendicular extramural tumour depth, 11 mm, rather than an average. That value lies within the commonly used T3c band. Keep the numerical depth and the adopted subdivision convention visible, especially at exact boundaries. Thin low-signal stranding may be desmoplasia; distinguish it from definite nodular tumour and state unresolved findings. Depth, MRF, EMVI and nodal confidence contribute different information. None alone establishes tissue stage or automatically selects neoadjuvant treatment.')
    q[8]['explain'] = ('Crossing the external sphincter is transsphincteric. The accompanying ischioanal collection and secondary tract make the supplied example St James grade 4. Grade 5 describes supralevator/translevator disease. The MRI grade is an anatomical communication tool, not an independent operation-selection rule. Report the actual opening, clock convention, each branch/collection and sphincter/levator relation. Source imaging does not independently prove an organism, complete tract lumen or drainability; surgical planning also requires sepsis, continence, prior treatment and patient context.')
    q[9]['answer'] = ('Report mucin within the treated bed and say MRI cannot distinguish acellular mucin from mucin containing viable tumour cells. Review baseline mucin status, matched source sequences and quality, and correlate endoscopy, digital examination and any appropriate tissue information. Neither imaging alone nor a negative superficial biopsy proves complete response.')
    q[9]['explain'] = ('T2-bright treated mucin can contain acellular material or viable cells, which MRI cannot reliably distinguish. Mucinous degeneration of a previously non-mucinous tumour is not automatically non-response. Response rules for mucinous and solid tumours are not interchangeable without qualification. Describe the actual treated-bed pattern and uncertainty, and combine the obtained clinical/endoscopic evidence. A negative superficial biopsy may miss residual disease and cannot by itself settle complete response.')
    q[10]['answer'] = ('Report demonstrated internal sphincter involvement with the intersphincteric plane and external sphincter apparently intact in the supplied views. Describe the actual craniocaudal extent and confidence; puborectalis, levator and other unprovided interfaces remain unassessed. This supports discussion of sphincter-preserving resection but does not prove that resection is feasible or choose the operation.')
    q[10]['explain'] = ('The surgeon needs the actual invaded and unresolved layers, not a binary operation instruction. Internal sphincter and intersphincteric involvement are reported separately and do not alone set the rectal cT category. Demonstrated external sphincter, puborectalis or levator invasion has different staging implications. The prompt does not establish levator clearance, a complete margin, functional outcome or eligibility for intersphincteric resection. Operative feasibility also depends on the complete anatomy, disease, treatment and patient context.')
    q[11]['answer'] = ('The supplied route is suprasphincteric because it rises above the puborectalis before descending to the ischioanal fossa. Laying the entire tract open would risk major sphincter/puborectalis injury and loss of continence. Map the actual openings and each deep extension for surgical assessment; a seton or sphincter-sparing approach may be considered in the full clinical context, rather than selected from MRI category alone.')
    q[11]['explain'] = ('Parks categories describe the tract’s demonstrated relation to the sphincters and puborectalis. In this supplied complete route, the ascent above puborectalis followed by descent supports suprasphincteric classification. Extrasphincteric disease follows a different route from above the levator outside the sphincter complex. Report any uncertain continuation, opening, collection and prior procedure. A drawing or partial tract cannot prove the complete category; MRI does not itself prescribe drainage, a seton or definitive repair.')
    q[12]['prompt'] = 'Order these illustrative T2 appearances from fibrosis-dominant to tumour-signal-dominant in the traditional mrTRG scheme. This does not ask you to prove complete response or select organ preservation.'
    q[12]['explain'] = ('The traditional mrTRG ordering runs from fibrosis only, through increasingly visible residual tumour signal, to predominantly unchanged or larger tumour signal. The supplied answer preserves that illustrative order. ESGAR 2026 notes that mrTRG can summarize good versus poor response but cannot accurately identify complete responders. Use actual T2 plus matched DWI/ADC, full treated-bed extent, clinical/endoscopic evidence and treatment timing. Fibrosis-only appearance does not prove pathological complete response; do not force a fixed eight-week schedule or treatment choice from this ordering exercise.')
    node['lesson_media'] = [m for m in node['lesson_media'] if m.get('kind') != 'source-gallery'] + [{
        'id': 'rectal-original-source-gallery', 'kind': 'source-gallery', 'title': 'Original rectal and fistula source figures',
        'instructions': 'Open the original MRI, histology, specimen and diagram references with their complete source captions. These are separate published cases and illustrations; they are not your patient, registered 3D anatomy or proof of every reported boundary.',
        'investigation_ids': ['ra.mri-rectal-cancer', 'ra.mri-perianal-fistula'],
    }]
    return node


def build():
    path = ROOT / 'data/curriculum/11-radiology.json'
    text = path.read_text()
    at = text.index('"id": "' + NODE + '"')
    start = text.rfind('{', 0, at)
    node, end = json.JSONDecoder().raw_decode(text, start)
    node = reconcile(node)
    text = text[:start] + json.dumps(node, indent=2, ensure_ascii=False).replace('\n', '\n    ') + text[end:]
    path.write_text(text)
    path = ROOT / 'data/radiology/module-guides.json'
    guides = json.loads(path.read_text())
    guide = guides[NODE]
    guide['overview'] = node['goal'] + ' Original lesson source figures retain separate published patients and evidence roles; they do not provide a complete native examination or registered 3D anatomy.'
    guide['learning_points'] = [step['detail'] for step in node['reference']['approach']]
    write_entry(path, guide)
    path = ROOT / 'data/radiology/reporting-body.json'
    guides = json.loads(path.read_text())
    guide = guides[NODE]
    guide['reviewed_at'] = '2026-10-09'
    guide['protocol'] = [
        'Select primary staging, post-treatment assessment or fistula mapping and record actual treatment, comparison and clinical context.',
        'Check tumour-aligned high-resolution T2 planes, slices no thicker than 3 mm and in-plane sampling below 1 × 1 mm, with coverage of relevant pelvic compartments. Source sampling does not establish fine tissue resolution.',
        'For response assessment, evaluate actual matched T2 and DWI/ADC with image quality and obtained clinical/endoscopic evidence. A numerical ADC threshold does not establish primary stage or histology.',
    ]
    details = [
        'Record every actual tumour/treated-bed endpoint and relation to sigmoid take-off, ARJ, verge and peritoneal reflection; retain exact height, landmark and local category convention.',
        'Map definite wall/extramural, fascia, peritoneal, vascular, sphincter and adjacent-organ findings with confidence. Baseline MRF rules depend on the qualifying component and node morphology; the eventual surgical CRM is separate.',
        'Describe each mesorectal and lateral nodule by actual station/side, size and morphology, with patient-level confidence. Primary lateral-node criteria are not lateral restaging criteria or pathological proof.',
        'Compare the complete treated bed and nodes using matched source T2/DWI/ADC and actual clinical/endoscopic context. Fibrosis, mrTRG and absent restriction alone do not prove complete response.',
        'Locate every demonstrated opening and route, and map each branch, blind sinus, collection and deep extension with a stated view/clock convention. Preserve unresolved extent; grade alone does not prescribe repair.',
    ]
    for step, detail in zip(guide['checklist'], details):
        step['detail'] = detail
    guide['measurements'][0] = {'name': 'Cancer distances', 'method': 'Measure lower/upper borders with stated ARJ/verge/lumen convention, maximal definite extramural depth and nearest qualifying baseline component to MRF.', 'pitfall': 'A smooth-margin node alone within 1 mm does not make baseline MRF involved. MRF distance is not pathological CRM. Record exact values and the source’s unresolved 5 cm category boundary convention.'}
    guide['measurements'][1]['pitfall'] = 'State the clock/view convention; it does not prove MRI acquisition position. A drawn tract fill is not a native mask or complete lumen boundary.'
    guide['pitfalls'] = node['reference']['pitfalls']
    guide['template_sections'][0]['body'] = 'Purpose and actual treatment/comparison [ ]. Tumour/bed endpoints and length [ ]. Exact lower-border height, ARJ/verge landmark and adopted convention [ ]. Sigmoid take-off and peritoneal reflection [ ].'
    guide['template_sections'][1]['body'] = 'MRI T assessment/framework/confidence [ ]. Maximal definite extramural depth and uncertainty [ ]. Baseline MRF qualifying component/morphology/distance/level [ ]. Separate peritoneal, vascular and each actual sphincter/adjacent-organ interface [ ]; unassessed extent [ ].'
    guide['template_sections'][2]['body'] = 'Each actual nodule: side/station/short axis/morphology and deposit suspicion [ ]. Regional context [ ]. Patient-level cN0/possibly cN+/cN+ and confidence [ ]. No histological N1c inference from MRI alone.'
    guide['template_sections'][3]['body'] = 'Actual treatment/date and comparison [ ]. Complete fibrotic bed and source residual signal [ ]. Matched T2/DWI/ADC findings/quality [ ]. Response class/confidence, mesorectal/lateral nodal change and MRF/EMVI interpretation [ ]. Actual DRE/endoscopy/tissue correlation [ ]; unresolved findings [ ].'
    guide['sources'] = [s for s in guide['sources'] if s['url'] not in {PRIMARY, RESTAGING, ANATOMY, FISTULA}] + [{'title': s['title'], 'url': s['url']} for s in [node['reference']['source'], *node['reference']['also']] if s['url'] in {PRIMARY, RESTAGING, ANATOMY, FISTULA}]
    write_entry(path, guide)
    path = ROOT / 'data/radiology/reporting-models.json'
    models = json.loads(path.read_text())
    model = models[NODE]
    model['reporting_aim'] = ('Partial schematic orientation only. Wall layers, fascia/peritoneum, sphincter components, ducts, nerves, vessels, nodes and tumour/fistula geometry are not complete or registered. Original lesson figures retain separate source cases and evidence roles.')
    model['instructions'] = 'Drag to rotate and inspect schematic orientation. ' + model['reporting_aim']
    write_entry(path, model)
    print('Reconciled rectal lesson/reference and all 13 quiz items; original source gallery attached; full anatomy remains unapproved')


if __name__ == '__main__':
    build()
