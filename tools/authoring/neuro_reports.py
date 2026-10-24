"""Author original, selectable neuroradiology and head/neck reporting rows.

Run from repository root. References describe the imaging domains; these
reporting statements are original and have not undergone clinical approval.
"""
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSIGNMENT = [{'guide_id': 'rad.4.head-trauma', 'investigation_id': 'template:head-trauma-report', 'title': 'Head Injury: Selecting, Timing and Reading the Trauma CT', 'modality': None}, {'guide_id': 'rad.5.craniosynostosis', 'investigation_id': 'ra.craniosynostosis', 'title': 'Craniosynostosis imaging', 'modality': 'Multimodality'}, {'guide_id': 'rad.5.neonatal-spine', 'investigation_id': 'ra.ultrasound-neonatal-spine', 'title': 'Ultrasound neonatal spine', 'modality': 'Ultrasound'}, {'guide_id': 'rad.5.paeds-masses-neuro', 'investigation_id': 'ra.ultrasound-neonatal-brain', 'title': 'Ultrasound neonatal brain', 'modality': 'Ultrasound'}, {'guide_id': 'rad.4.spine-imaging', 'investigation_id': 'ra.mri-lumbar-disc', 'title': 'MRI lumbar disc disease', 'modality': 'MRI'}, {'guide_id': 'rad.4.spine-imaging', 'investigation_id': 'ra.mri-myelopathy', 'title': 'MRI myelopathy', 'modality': 'MRI'}, {'guide_id': 'rad.4.stroke', 'investigation_id': 'ra.acute-stroke', 'title': 'CT and MRI acute stroke', 'modality': 'Multimodality'}, {'guide_id': 'rad.5.brain-anatomy', 'investigation_id': 'ra.brain-anatomy', 'title': 'Brain anatomy and vascular territories', 'modality': 'Reference'}, {'guide_id': 'rad.5.brain-tumour', 'investigation_id': 'ra.mri-brain-tumours', 'title': 'MRI brain tumours', 'modality': 'MRI'}, {'guide_id': 'rad.5.cns-infection', 'investigation_id': 'ra.mri-cns-enhancement', 'title': 'MRI CNS enhancement patterns', 'modality': 'MRI'}, {'guide_id': 'rad.5.dementia', 'investigation_id': 'ra.mri-dementia', 'title': 'MRI dementia', 'modality': 'MRI'}, {'guide_id': 'rad.5.epilepsy-mri', 'investigation_id': 'ra.mri-epilepsy', 'title': 'MRI epilepsy', 'modality': 'MRI'}, {'guide_id': 'rad.5.intracranial-haemorrhage', 'investigation_id': 'ra.ct-traumatic-haemorrhage', 'title': 'CT traumatic intracranial haemorrhage', 'modality': 'CT'}, {'guide_id': 'rad.5.intracranial-haemorrhage', 'investigation_id': 'ra.intracranial-haemorrhage', 'title': 'Non-traumatic intracranial haemorrhage imaging', 'modality': 'Multimodality'}, {'guide_id': 'rad.5.ms-white-matter', 'investigation_id': 'ra.mri-ms', 'title': 'MRI multiple sclerosis', 'modality': 'MRI'}, {'guide_id': 'rad.5.peripheral-vascular', 'investigation_id': 'ra.carotid-obstruction', 'title': 'Carotid obstruction imaging', 'modality': 'Multimodality'}, {'guide_id': 'rad.5.sella', 'investigation_id': 'ra.mri-sella', 'title': 'MRI sella and parasellar region', 'modality': 'MRI'}, {'guide_id': 'rad.5.venous-csf', 'investigation_id': 'ra.venous-sinus-thrombosis', 'title': 'CT and MR venography — sinus thrombosis', 'modality': 'Multimodality'}, {'guide_id': 'rad.5.venous-csf', 'investigation_id': 'ra.intracranial-hypotension', 'title': 'MRI spontaneous intracranial hypotension', 'modality': 'MRI'}, {'guide_id': 'rad.5.deep-neck-spaces', 'investigation_id': 'ra.mri-neck-spaces', 'title': 'MRI infra- and suprahyoid neck', 'modality': 'MRI'}, {'guide_id': 'rad.5.deep-neck-spaces', 'investigation_id': 'ra.head-neck-malignancy', 'title': 'Head and neck tumour imaging', 'modality': 'Multimodality'}, {'guide_id': 'rad.5.esophagus-swallowing', 'investigation_id': 'ra.swallowing', 'title': 'Fluoroscopic swallowing examination', 'modality': 'Radiography'}, {'guide_id': 'rad.5.neck-nodes', 'investigation_id': 'ra.cervical-lymph-nodes', 'title': 'Cervical lymph node map', 'modality': 'Reference'}, {'guide_id': 'rad.5.orbit', 'investigation_id': 'ra.ct-mri-eye', 'title': 'CT and MRI eye', 'modality': 'Multimodality'}, {'guide_id': 'rad.5.paeds-masses-neuro', 'investigation_id': 'ra.paediatric-neck-masses', 'title': 'Paediatric neck mass imaging', 'modality': 'Multimodality'}, {'guide_id': 'rad.5.sinuses', 'investigation_id': 'ra.mri-sinuses', 'title': 'MRI paranasal sinuses', 'modality': 'MRI'}, {'guide_id': 'rad.5.temporal-bone', 'investigation_id': 'ra.ct-temporal-bone', 'title': 'CT temporal bone', 'modality': 'CT'}, {'guide_id': 'rad.5.thyroid-tirads', 'investigation_id': 'ra.ultrasound-thyroid', 'title': 'Ultrasound thyroid — TI-RADS', 'modality': 'Ultrasound'}, {'guide_id': 'rad.5.tinnitus', 'investigation_id': 'ra.tinnitus', 'title': 'Tinnitus imaging', 'modality': 'Multimodality'}, {'guide_id': 'rad.5.trigeminal', 'investigation_id': 'ra.mri-trigeminal', 'title': 'MRI trigeminal neuralgia', 'modality': 'MRI'}]
FORMS = json.loads((ROOT / 'data/radiology/descriptor-reporting.json').read_text())['forms']
OUT = {'version': '2026-10-23', 'sources': [], 'investigations': {}, 'coverage': []}
SOURCE_LOOKUP = {}
for assignment in ASSIGNMENT:
    for source in FORMS[assignment['guide_id']]['sources']:
        if source['url'] not in SOURCE_LOOKUP:
            sid = 'neuro-ref-' + str(len(SOURCE_LOOKUP) + 1)
            SOURCE_LOOKUP[source['url']] = sid
            OUT['sources'].append({'id': sid, 'title': source['title'], 'url': source['url']})

def source(part):
    return next(value for url, value in SOURCE_LOOKUP.items() if part in url)

def slug(s):
    return re.sub('[^a-z0-9]+', '-', s.lower()).strip('-')

def f(identifier, label, text, *, parents=(), exclusive=None, invalidates=()):
    value = {'id': identifier, 'label': label, 'text': text}
    if parents: value['requires_any'] = list(parents)
    if exclusive: value['exclusive_group'] = exclusive
    if invalidates: value['invalidates_normal'] = list(invalidates)
    return value

def row(identifier, label, group, normal, findings, *, refs=None, skip=False, repeat=False, repeat_label='Lesion'):
    value = {'id': identifier, 'label': label, 'group': group, 'normal': normal,
             'source_ids': refs or CURRENT_REFS, 'findings': findings}
    if skip: value['exclude_from_bulk_normal'] = True
    if repeat: value.update(repeatable=True, repeat_label=repeat_label)
    return value

def report(identifier, refs):
    global CURRENT_REFS
    assignment = next(x for x in ASSIGNMENT if x['investigation_id'] == identifier)
    CURRENT_REFS = [source(x) for x in refs]
    value = {key: assignment[key] for key in ['guide_id', 'title', 'modality']}
    value['sections'] = []
    OUT['investigations'][identifier] = value
    return value['sections']

def size(parent='lesion', noun='The lesion'):
    return f('dimensions', 'Three dimensions', noun + ' measures __ × __ × __ mm.', parents=[parent])

def protocol(rows, modalities, extra=None):
    rows.append(row('examination', 'Examination performed', 'Technique', None, [
        f('method', 'Modality', 'The examination was performed using ' + ('[' + ' / '.join(modalities) + ']' if len(modalities)>1 else modalities[0]) + '.', exclusive='method'),
        f('quality', 'Technical limitation', 'Assessment is limited by [motion / metal artefact / incomplete coverage / low signal / limited acoustic window].'),
    ] + (extra or []), skip=True))

def mass_effect(rows):
    rows.extend([
        row('midline', 'Midline / herniation', 'Mass effect and CSF spaces', 'The cerebral midline is maintained without herniation.', [
            f('shift', 'Midline shift', 'There is __ mm [rightward / leftward] midline shift.'),
            f('herniation', 'Herniation', 'There is [subfalcine / right uncal / left uncal / downward transtentorial / upward transtentorial / tonsillar] herniation.')]),
        row('ventricles', 'Ventricular system', 'Mass effect and CSF spaces', 'The ventricles are not dilated.', [
            f('dilatation', 'Ventricular dilatation', 'There is [mild / moderate / marked] [lateral and third ventricular / four-ventricular / right lateral ventricular / left lateral ventricular] dilatation.'),
            f('transependymal', 'Transependymal fluid', 'There is periventricular interstitial fluid consistent with transependymal CSF passage.', parents=['dilatation']),
            f('collapse', 'Ventricular compression', 'The [right lateral ventricle / left lateral ventricle / third ventricle / fourth ventricle] is compressed.')]),
        row('cisterns', 'Basal cisterns', 'Mass effect and CSF spaces', 'The basal cisterns remain patent.', [
            f('effacement', 'Cisternal effacement', 'The [suprasellar / ambient / prepontine / quadrigeminal] cistern is [partially / completely] effaced.')])
    ])

def trauma_rows(rows):
    for side in ['right', 'left']:
        for compartment, normal, findings in [
            ('subdural', f'No {side} convexity subdural collection is identified.', [
                f('collection', 'Subdural collection', f'There is a {side} [frontoparietal / frontotemporoparietal / temporal / occipital / posterior fossa] subdural collection with [hyperdense / hypodense / mixed-density] contents.'),
                f('thickness', 'Maximum thickness', f'The {side} subdural collection measures __ mm in maximal perpendicular thickness.', parents=['collection']),
                f('layers', 'Internal layering', f'The {side} subdural collection contains [fluid-fluid levels / hyperdense acute blood products / membranes].', parents=['collection'])]),
            ('epidural', f'No {side} epidural haematoma is identified.', [
                f('collection', 'Epidural haematoma', f'There is a {side} [frontal / temporal / parietal / occipital / posterior fossa] epidural haematoma.'),
                f('thickness', 'Maximum thickness', f'The {side} epidural haematoma measures __ mm thick.', parents=['collection']),
                f('swirl', 'Internal low attenuation', f'The {side} epidural haematoma contains low-attenuation areas.', parents=['collection'])]),
            ('subarachnoid', f'No {side} convexity subarachnoid haemorrhage is identified.', [
                f('blood', 'Subarachnoid blood', f'There is {side} [frontal sulcal / parietal sulcal / temporal sulcal / occipital sulcal / sylvian fissure] subarachnoid haemorrhage.')]),
        ]:
            rows.append(row(side+'-'+compartment, side.title()+' '+compartment, 'Extra-axial haemorrhage', normal, findings))
        for lobe in ['frontal', 'temporal', 'parietal', 'occipital']:
            name = side+' '+lobe+' lobe'
            rows.append(row(slug(name), name.title(), 'Cerebral parenchyma', f'No acute haemorrhagic contusion is seen in the {name}.', [
                f('contusion', 'Haemorrhagic contusion', f'There are [single / multiple] haemorrhagic contusions in the {name}.'),
                f('oedema', 'Oedema', f'There is [focal / confluent] low attenuation with swelling in the {name}.'),
                f('dimensions', 'Dominant contusion size', f'The largest {name} contusion measures __ × __ × __ mm.', parents=['contusion'])]))
    for identifier,label in [('falx','Falx'),('tentorium','Tentorium'),('basal-subarachnoid','Basal subarachnoid spaces')]:
        rows.append(row(identifier,label,'Extra-axial haemorrhage',f'No acute haemorrhage is seen along the {label.lower()}.',[
            f('blood','Haemorrhage',f'Acute blood is present along the {label.lower()} [centrally / on the right / on the left / bilaterally].')]))
    rows.append(row('intraventricular-blood','Intraventricular blood','Haemorrhage', 'No intraventricular haemorrhage is identified.',[
        f('blood','Intraventricular haemorrhage','Blood is present in the [right lateral ventricle / left lateral ventricle / both lateral ventricles / third ventricle / fourth ventricle].')]))
    for name in ['corpus callosum','brainstem','cerebellum']:
        rows.append(row(slug(name),name.title(),'Deep and posterior fossa structures',f'No acute focal CT abnormality is identified in the {name}.',[
            f('haemorrhage','Haemorrhage',f'There is [punctate / focal / confluent] haemorrhage in the {name}.'),
            f('low-attenuation','Low attenuation',f'There is focal low attenuation in the {name}.')]))
    rows.append(row('shear-pattern','Shear injury pattern','Cerebral parenchyma',None,[
        f('shear','Haemorrhagic shear pattern','Punctate haemorrhages at the [corticomedullary junction / corpus callosum / dorsolateral brainstem] raise concern for traumatic axonal injury. A normal CT does not exclude non-haemorrhagic axonal injury.')],skip=True))
    for name in ['frontal bone','right temporal bone','left temporal bone','right parietal bone','left parietal bone','occipital bone','anterior skull base','central skull base','posterior skull base']:
        rows.append(row(slug(name),name.title(),'Calvarium and skull base',f'No acute fracture is identified in the {name} on the acquired bone images.',[
            f('fracture','Fracture',f'There is a [linear non-displaced / depressed / comminuted / diastatic] fracture of the {name}.'),
            f('depression','Depression',f'The {name} fracture is depressed __ mm.',parents=['fracture']),
            f('extension','Skull-base canal involvement',f'The {name} fracture extends to the [carotid canal / jugular foramen / optic canal / otic capsule / facial nerve canal / cribriform plate].',parents=['fracture'])]))
    rows.append(row('scalp','Scalp','Extracranial structures','No focal scalp haematoma is identified.',[
        f('haematoma','Scalp haematoma','There is [right / left / midline] [frontal / parietal / temporal / occipital] scalp haematoma.'),
        f('wound','Laceration / foreign body','There is a [right / left / midline] scalp laceration [without radiopaque foreign body / containing radiopaque foreign material].')]))
    rows.append(row('intracranial-air','Intracranial air','Complications','No pneumocephalus is identified.',[
        f('air','Pneumocephalus','There is [small-volume / extensive] [extra-axial / intraventricular / intraparenchymal] intracranial air.')]))
    mass_effect(rows)

for identifier in ['template:head-trauma-report','ra.ct-traumatic-haemorrhage']:
    rows = report(identifier,['traumatic-intracranial-haemorrhage'])
    protocol(rows,['non-contrast head CT'])
    trauma_rows(rows)

# Neonatal and paediatric cranial and spinal anatomy.
rows = report('ra.craniosynostosis',['craniosynosthosis'])
protocol(rows,['cranial suture ultrasound','low-dose skull CT with three-dimensional reconstruction'])
for name in ['sagittal','right coronal','left coronal','right lambdoid','left lambdoid','right squamosal','left squamosal']:
    rows.append(row(slug(name)+'-suture',name.title()+' suture','Cranial sutures',f'The {name} suture is patent in the imaged region.',[
        f('fusion','Suture fusion',f'There is [partial / complete] fusion of the {name} suture.'),
        f('segment','Fusion extent',f'The fused {name} suture involves the [anterior / middle / posterior / superior / inferior] portion.',parents=['fusion']),
        f('ridge','Sutural ridging',f'There is bony ridging along the {name} suture.')]))
rows.extend([
    row('metopic','Metopic suture','Cranial sutures',None,[f('status','Metopic status','The metopic suture is [patent / fused without trigonocephalic deformity / fused with trigonocephalic deformity].',exclusive='status'),f('ridge','Metopic ridge','There is a midline metopic ridge [without hypotelorism / with hypotelorism].')],skip=True),
    row('shape','Cranial shape','Skull configuration',None,[f('shape','Shape pattern','The skull has [scaphocephaly / anterior plagiocephaly / posterior plagiocephaly / brachycephaly / trigonocephaly / turricephaly / cloverleaf configuration / positional parallelogram configuration].',exclusive='shape'),f('asymmetry','Asymmetry','There is [right / left] frontal flattening with [ipsilateral / contralateral] occipital flattening.')],skip=True),
    row('orbits','Orbits and anterior skull base','Associated deformity',None,[f('orbit','Orbital configuration','There is [right orbital elevation / left orbital elevation / bilateral shallow orbits / hypotelorism / hypertelorism].'),f('base','Skull-base asymmetry','The anterior skull base is asymmetric with [right / left] orbital roof elevation.')],skip=True),
    row('intracranial','Intracranial assessment on cross-sectional imaging','Associated findings',None,[f('hydrocephalus','Hydrocephalus','Cross-sectional imaging shows [no ventricular dilatation / hydrocephalus].'),f('tonsils','Tonsillar position','On the acquired cross-sectional images the cerebellar tonsils lie [above the foramen magnum / at the foramen magnum / below the foramen magnum].')],skip=True)
])

rows = report('ra.ultrasound-neonatal-spine',['ultrasound-of-the-neonatal-spine','neonatal-spine'])
protocol(rows,['lumbosacral spinal ultrasound'])
rows.extend([
    row('numbering','Vertebral numbering','Technique',None,[f('count','Numbering basis','Vertebral levels were assigned by [counting from the last rib-bearing vertebra / counting upward from the sacrum / correlation with radiographs].'),f('uncertain','Numbering uncertain','Vertebral numbering remains uncertain because of [transitional anatomy / limited field of view / segmentation anomaly].')],skip=True),
    row('conus','Conus medullaris','Cord and roots',None,[f('tip','Conus level','The conus tip is at [T12–L1 / L1 / L1–L2 / L2 / L2–L3 / L3 / L3–L4 / L4 / below L4].'),f('shape','Conus shape','The conus is [normally tapered / blunt / bulbous / dorsally displaced].')],skip=True),
    row('filum','Filum terminale','Cord and roots','The visualised filum is slender without a focal echogenic mass.',[f('thick','Thickened filum','The filum is thickened and [normally echogenic / diffusely echogenic].'),f('diameter','Filum diameter','The filum measures __ mm in diameter.'),f('lipoma','Filum lipoma','There is a focal echogenic filum lesion compatible with fat.')]),
    row('cord','Distal spinal cord','Cord and roots','The visualised distal spinal cord has uniform echotexture without a focal mass.',[f('cavity','Central canal cavity','There is a [slit-like / fusiform / irregular] central canal cavity extending over the [lower thoracic / thoracolumbar / conus] region.'),f('diameter','Cavity diameter','The central canal cavity measures __ mm in maximum diameter.',parents=['cavity']),f('mass','Cord lesion','There is an [echogenic / hypoechoic / mixed-echogenicity] lesion involving the distal cord.'),f('split','Split cord','Two hemicords are seen separated by an [echogenic spur / soft-tissue septum / indeterminate septum].')]),
    row('roots','Cauda equina motion','Cord and roots','The cauda equina roots show free motion on the observed cine assessment.',[f('motion','Reduced root motion','Cauda equina root motion is [reduced / absent] on cine assessment.'),f('clump','Root position','The cauda equina roots are [dorsally adherent / clumped / displaced by a mass].')],skip=True),
    row('thecal-sac','Thecal sac','Spinal canal','No focal intraspinal collection is seen within the visualised thecal sac.',[f('cyst','Filar cyst','There is a thin-walled filar cyst.'),f('collection','Collection','There is a [simple / complex] intraspinal fluid collection.'),f('end','Sac termination','The distal thecal sac ends at [S1 / S2 / S3 / S4].')]),
    row('posterior-elements','Posterior elements','Dysraphism','The visualised posterior elements show no focal defect.',[f('defect','Posterior defect','There is a posterior element defect at [lumbar / lumbosacral / sacral] level.'),f('sac','Dysraphic sac','A skin-covered dysraphic sac contains [CSF only / neural tissue / echogenic fatty tissue].')]),
    row('skin-tract','Cutaneous tract','Dysraphism','No tract extending from the examined skin marker into the spinal canal is demonstrated.',[f('tract','Tract','A tract extends from the [sacral dimple / skin opening / subcutaneous mass] to the [coccyx / posterior elements / spinal canal].'),f('fluid','Tract-associated collection','The cutaneous tract has an associated [subcutaneous / intraspinal] collection.',parents=['tract'])],skip=True),
    row('soft-tissue','Paraspinal soft tissues','Dysraphism','No focal mass is present in the examined paraspinal soft tissues.',[f('lipoma','Fatty mass','There is an echogenic paraspinal mass with [no demonstrated canal communication / communication with the spinal canal].'),f('vascular','Vascular lesion','There is a [low-flow / hypervascular] subcutaneous lesion on Doppler assessment.')])
])

rows = report('ra.ultrasound-neonatal-brain',['neonatal-brain-us'])
protocol(rows,['transfontanelle cranial ultrasound'],[f('windows','Additional windows','Additional views were acquired through the [posterior fontanelle / right mastoid fontanelle / left mastoid fontanelle / bilateral mastoid fontanelles].')])
for side in ['right','left']:
    group=side.title()+' hemisphere'
    rows.extend([
        row(side+'-germinal-matrix',side.title()+' caudothalamic groove',group,f'No germinal matrix haemorrhage is seen in the {side} caudothalamic groove.',[f('gmh','Germinal matrix haemorrhage',f'There is {side} [focal / extensive] caudothalamic groove haemorrhage.'),f('cyst','Subependymal cyst',f'There is a {side} [single / cluster of] subependymal cyst.')]),
        row(side+'-lateral-ventricle',side.title()+' lateral ventricle',group,f'The {side} lateral ventricle is not dilated and contains no visible blood.',[f('ivh','Intraventricular haemorrhage',f'There is {side} intraventricular [layering blood / echogenic clot].'),f('dilatation','Dilatation',f'The {side} lateral ventricle is [mildly / moderately / markedly] dilated.'),f('levene','Ventricular index',f'The {side} ventricular index at the foramen of Monro is __ mm.'),f('ahw','Anterior horn width',f'The {side} anterior horn width is __ mm.'),f('tod','Thalamo-occipital distance',f'The {side} thalamo-occipital distance is __ mm.'),f('lining','Ventricular lining',f'The {side} ventricular ependyma is [echogenic / irregular] with [no debris / intraventricular debris].')]),
        row(side+'-periventricular-white-matter',side.title()+' periventricular white matter',group,f'The {side} periventricular white matter has no focal echogenic or cystic abnormality.',[f('echogenic','Periventricular echogenicity',f'There is {side} [peritrigonal / frontal / diffuse] periventricular hyperechogenicity that is [homogeneous / patchy].'),f('cysts','Cystic injury',f'There are {side} [focal / extensive] periventricular cysts.'),f('venous-infarct','Periventricular haemorrhagic infarction',f'There is a {side} fan-shaped periventricular haemorrhagic lesion in the [frontal / parietal / temporal] region.')]),
        row(side+'-basal-ganglia',side.title()+' deep grey matter',group,f'The {side} basal ganglia and thalamus have no focal sonographic abnormality.',[f('echogenic','Deep grey echogenicity',f'There is increased echogenicity in the {side} [basal ganglia / thalamus / basal ganglia and thalamus].'),f('vessels','Lenticulostriate vasculopathy',f'Branching echogenic lenticulostriate vessels are visible on the {side}.')]),
        row(side+'-cortex',side.title()+' cortex and subcortical tissue',group,f'The visualised {side} cerebral cortex shows no focal swelling or destructive lesion.',[f('injury','Focal injury',f'There is {side} [frontal / parietal / temporal / occipital] [increased echogenicity / loss of normal differentiation / cystic encephalomalacia].'),f('sulci','Sulcation',f'The {side} cerebral sulcation is [reduced for gestational age / focally abnormal].')])
    ])
rows.extend([
    row('midline','Corpus callosum / septum','Midline','The visualised corpus callosum is present and the midline is maintained.',[f('callosum','Callosal anomaly','The corpus callosum appears [partially absent / completely absent / hypoplastic].'),f('cavum','Cavum variant','A [cavum septi pellucidi / cavum vergae / cavum veli interpositi] is present.'),f('shift','Midline shift','There is [rightward / leftward] midline shift of __ mm.')]),
    row('third-fourth','Third and fourth ventricles','CSF spaces','The third and visualised fourth ventricles are not dilated.',[f('dilatation','Dilatation','The [third / fourth / third and fourth] ventricle is dilated.')]),
    row('cerebellum','Cerebellum and vermis','Posterior fossa','No focal abnormality is seen in the cerebellum on the acquired posterior fossa views.',[f('haemorrhage','Cerebellar haemorrhage','There is [right / left / bilateral / vermian] cerebellar haemorrhage.'),f('malformation','Posterior fossa anomaly','There is [vermian hypoplasia / an enlarged retrocerebellar CSF space / a posterior fossa cyst].')],skip=True),
    row('extra-axial','Extra-axial spaces','CSF spaces','No extra-axial collection is visible in the examined regions.',[f('space','Enlarged spaces','The frontal extra-axial CSF spaces are enlarged [with traversing cortical vessels / without clearly demonstrated traversing vessels].'),f('collection','Collection','There is a [right / left / bilateral] [simple / complex] extra-axial collection.')]),
    row('doppler','Intracranial Doppler','Doppler',None,[f('flow','Sagittal sinus flow','Colour Doppler shows [preserved / reduced / absent] flow in the superior sagittal sinus.'),f('arterial','Arterial waveform','The sampled anterior cerebral artery waveform has [preserved forward diastolic flow / reduced diastolic flow / reversed diastolic flow].')],skip=True)
])
rows = report('ra.mri-lumbar-disc',['lumbar-disc-nomenclature-2-0','lumbar-disc-herniation'])
protocol(rows,['non-contrast lumbar MRI','lumbar MRI with intravenous contrast'])
rows.extend([
    row('numbering','Vertebral numbering','Overview',None,[f('convention','Numbering convention','The lowest fully formed disc is designated [L5–S1 / L6–S1] based on [whole-spine localiser counting / the available regional images].'),f('transition','Transitional vertebra','There is [sacralisation of L5 / lumbarisation of S1].')],skip=True),
    row('alignment','Lumbar alignment','Overview','Lumbar sagittal alignment is maintained.',[f('listhesis','Listhesis','There is [anterolisthesis / retrolisthesis] at [L1–L2 / L2–L3 / L3–L4 / L4–L5 / L5–S1] measuring __ mm.'),f('curve','Coronal curve','There is a [right-convex / left-convex] lumbar curvature.')]),
    row('conus','Conus medullaris','Neural structures','The visualised conus has normal calibre and signal.',[f('level','Conus level','The conus terminates at [T12 / T12–L1 / L1 / L1–L2 / L2 / L2–L3 / L3 / below L3].'),f('signal','Conus signal','There is [focal / diffuse] T2 hyperintensity in the conus.'),f('mass','Conus mass','There is an expansile conus lesion.')]),
    row('cauda','Cauda equina','Neural structures','The cauda equina roots are normally distributed.',[f('clumping','Root clumping','The cauda equina roots are [centrally clumped / peripherally adherent / distorted by a focal mass].'),f('enhancement','Root enhancement after contrast','On post-contrast imaging there is [smooth / nodular] cauda equina enhancement.')]),
])
for level in ['L1','L2','L3','L4','L5','S1']:
    rows.append(row(level.lower()+'-body',level+' vertebral body','Vertebral bodies',f'The {level} vertebral body has preserved height without focal marrow-replacing lesion.',[
        f('collapse','Compression deformity',f'The {level} vertebral body has [anterior wedge / central / diffuse] height loss with [marrow oedema / no marrow oedema].'),
        f('lesion','Marrow lesion',f'There is a [focal low-T1 / focal fat-containing / diffuse low-T1] marrow abnormality in {level}.'),
        f('pars','Pars defect',f'There is a [right / left / bilateral] pars defect at {level}.')]))
for upper, lower, exitroot, traversing in [('L1','L2','L1','L2'),('L2','L3','L2','L3'),('L3','L4','L3','L4'),('L4','L5','L4','L5'),('L5','S1','L5','S1')]:
    level=upper+'–'+lower; ident=(upper+'-'+lower).lower()
    rows.append(row(ident+'-disc',level+' disc',level,f'The {level} disc has preserved height and signal without a focal herniation.',[
        f('degeneration','Disc degeneration',f'The {level} disc is desiccated with [preserved height / mild height loss / moderate height loss / severe height loss].'),
        f('bulge','Disc bulge',f'There is [circumferential / asymmetric right-sided / asymmetric left-sided] bulging of the {level} disc.'),
        f('herniation','Disc herniation',f'There is a [central / right subarticular / left subarticular / right foraminal / left foraminal / right extraforaminal / left extraforaminal] {level} disc [protrusion / extrusion / sequestration].'),
        f('migration','Migration',f'The {level} extruded or sequestered fragment extends [cranially / caudally] by __ mm.',parents=['herniation']),
        f('fissure','Annular fissure',f'There is a [posterior central / right posterolateral / left posterolateral] annular fissure at {level}.'),
        f('endplates','Endplate signal',f'The opposing {level} endplates have [oedematous / fatty / sclerotic] degenerative marrow change.')]))
    rows.append(row(ident+'-canal',level+' central canal',level,f'There is no central canal stenosis at {level}.',[
        f('stenosis','Canal stenosis',f'There is [mild / moderate / severe] central canal stenosis at {level} with [preserved CSF around the roots / root crowding / complete CSF effacement].'),
        f('cause','Contributors',f'{level} canal narrowing is contributed to by [ligamentum flavum thickening / epidural lipomatosis / congenitally short pedicles / facet-associated synovial cyst].',parents=['stenosis'])]))
    for side in ['right','left']:
        rows.extend([
            row(ident+'-'+side+'-recess',side.title()+' lateral recess / '+traversing+' root',level,f'The {side} {level} lateral recess and traversing {traversing} root are unimpeded.',[
                f('stenosis','Recess narrowing',f'The {side} {level} lateral recess is [mildly / moderately / severely] narrowed.'),
                f('root','Traversing root effect',f'The {side} {traversing} traversing root is [contacted without displacement / displaced / compressed] at {level}.')]),
            row(ident+'-'+side+'-foramen',side.title()+' foramen / '+exitroot+' root',level,f'The {side} {level} neural foramen is patent without exiting {exitroot} root compression.',[
                f('stenosis','Foraminal narrowing',f'There is [mild / moderate / severe] {side} {level} foraminal narrowing.'),
                f('root','Exiting root effect',f'The exiting {side} {exitroot} root is [contacted / displaced / compressed] in the [foraminal / extraforaminal] region.')]),
            row(ident+'-'+side+'-facet',side.title()+' facet joint',level,f'The {side} {level} facet joint shows no significant arthropathy.',[
                f('arthropathy','Facet arthropathy',f'There is [mild / moderate / severe] {side} {level} facet arthropathy.'),
                f('effusion','Facet effusion',f'The {side} {level} facet joint contains an effusion.'),
                f('cyst','Facet cyst',f'A {side} {level} facet-associated cyst extends [medially into the canal / into the foramen / posteriorly outside the canal].')])
        ])
rows.append(row('paraspinal','Paraspinal tissues','Additional findings','No focal collection is seen in the visualised paraspinal tissues.',[
    f('atrophy','Paraspinal muscle atrophy','There is [mild / moderate / severe] fatty atrophy of the paraspinal muscles.'),f('collection','Collection','There is a [right / left / midline] [paraspinal / psoas / posterior subcutaneous] collection.')]))

rows = report('ra.mri-myelopathy',['myelopathy'])
protocol(rows,['cervical MRI','thoracic MRI','cervical and thoracic MRI','whole-spine MRI'])
for level in ['C1','C2','C3','C4','C5','C6','C7','T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12']:
    rows.append(row(level.lower()+'-cord',level+' cord level','Cord by vertebral level',f'The spinal cord at {level} has normal calibre and T2 signal on the acquired images.',[
        f('signal','Cord signal',f'At {level} there is [central / dorsal / ventral / right lateral / left lateral / diffuse transverse] cord T2 hyperintensity.'),
        f('size','Cord calibre',f'At {level} the cord is [expanded / atrophic / flattened].'),
        f('compression','Extrinsic compression',f'At {level} the cord is compressed [ventrally / dorsally / from the right / from the left / circumferentially].'),
        f('cavity','Syrinx',f'There is a syrinx at {level} measuring __ mm in maximum diameter.')],skip=True))
rows.append(row('cord-lesion','Cord lesion characterisation','Focal lesions',None,[
    f('lesion','Lesion location','A cord lesion extends from [cervicomedullary junction / C1 / C2 / C3 / C4 / C5 / C6 / C7 / T1 / T2 / T3 / T4 / T5 / T6 / T7 / T8 / T9 / T10 / T11 / T12] to [C1 / C2 / C3 / C4 / C5 / C6 / C7 / T1 / T2 / T3 / T4 / T5 / T6 / T7 / T8 / T9 / T10 / T11 / T12 / conus].'),
    f('axial','Axial distribution','The lesion involves [less than half / more than half / the entire] cord cross-section and is centred [dorsally / ventrally / centrally / right laterally / left laterally].',parents=['lesion']),
    f('enhancement','Enhancement after contrast','On post-contrast imaging the cord lesion shows [no enhancement / focal nodular enhancement / patchy enhancement / ring enhancement / thin transverse enhancement].',parents=['lesion']),
    f('diffusion','Diffusion','On acquired diffusion images the lesion has [restricted diffusion with low ADC / no diffusion restriction / indeterminate diffusion because of artefact].',parents=['lesion']),
    f('blood','Blood products','The lesion contains susceptibility signal compatible with blood products.',parents=['lesion']),
    size()
],repeat=True))
for region,levels in [('Cervical',['C2–C3','C3–C4','C4–C5','C5–C6','C6–C7','C7–T1']),('Thoracic',['T1–T2','T2–T3','T3–T4','T4–T5','T5–T6','T6–T7','T7–T8','T8–T9','T9–T10','T10–T11','T11–T12','T12–L1'])]:
    for level in levels:
        rows.append(row(slug(level)+'-canal',level+' canal',region+' canal',f'No compressive canal lesion is present at {level} on the acquired images.',[
            f('stenosis','Canal narrowing',f'At {level} there is [mild / moderate / severe] canal stenosis from [disc material / disc-osteophyte complex / ligamentous thickening / epidural lesion].'),
            f('cord','Cord relationship',f'At {level} the compressive lesion [effaces the ventral CSF only / contacts the cord / indents the cord / markedly flattens the cord].',parents=['stenosis'])],skip=True))
rows.extend([
    row('conus','Conus','Additional neural structures','The visualised conus has normal signal and calibre.',[f('signal','Conus abnormality','The conus has [T2 hyperintensity / swelling / atrophy].')],skip=True),
    row('perimedullary-vessels','Perimedullary vessels','Vascular clues','No conspicuous dilated perimedullary vessels are seen in the acquired field.',[f('veins','Prominent vessels','Serpiginous perimedullary vessels are present along the [dorsal / ventral / both dorsal and ventral] cord surface.')],skip=True),
    row('epidural','Epidural space','Extradural tissues','No epidural mass or collection is seen in the acquired spinal field.',[f('lesion','Epidural lesion','There is an epidural [mass / collection / haematoma] in the [cervical / thoracic / thoracolumbar] region.'),f('enhancement','Post-contrast pattern','The epidural lesion shows [solid / peripheral / heterogeneous] enhancement on the acquired post-contrast images.',parents=['lesion'])],skip=True),
    row('marrow','Vertebral marrow','Extradural tissues','No focal marrow-replacing lesion is seen in the acquired spinal field.',[f('lesion','Marrow lesion','There are [single / multiple / diffuse] marrow abnormalities in the [cervical / thoracic / lumbar] vertebrae.')],skip=True)
])

# Cerebral regional rows are independently addressable; specialised exams append
# disease-specific descriptors instead of repeating an undifferentiated checklist.
def brain_regions(rows, mode='mri', group='Brain parenchyma', skip=False):
    for side in ['right','left']:
        for region in ['frontal lobe','parietal lobe','temporal lobe','occipital lobe','insula','basal ganglia','thalamus','cerebellar hemisphere']:
            name=side+' '+region
            if mode=='mri':
                normal=f'No focal signal abnormality is identified in the {name} on the acquired sequences.'
                fs=[f('t2','T2 / FLAIR abnormality',f'The {name} contains [cortical / subcortical / confluent / focal] T2 hyperintensity.'),f('diffusion','Restricted diffusion',f'There is restricted diffusion with low ADC in the {name}.'),f('blood','Blood products',f'There are [punctate / focal / confluent] susceptibility foci in the {name} compatible with blood products.'),f('loss','Volume loss',f'There is [mild / moderate / severe] focal volume loss in the {name}.')]
            else:
                normal=f'No acute focal parenchymal abnormality is identified in the {name} on the acquired images.'
                fs=[f('ischaemia','Ischaemic change',f'The {name} shows [loss of grey-white differentiation / focal swelling / established tissue loss].'),f('blood','Haemorrhage',f'There is [punctate / focal / confluent] haemorrhage in the {name}.')]
            rows.append(row(slug(name),name.title(),group,normal,fs,skip=skip))
    for name in ['midbrain','pons','medulla','cerebellar vermis','corpus callosum']:
        rows.append(row(slug(name),name.title(),group,f'No focal abnormality is identified in the {name} on the acquired images.',[
            f('lesion','Focal abnormality',f'There is a focal lesion involving the {name}.'),f('signal','Signal / density pattern',f'The {name} lesion has ' + ('[T2 hyperintensity / restricted diffusion / haemorrhagic contents].' if mode=='mri' else '[T2 hyperintensity on MRI / restricted diffusion on MRI / haemorrhagic contents / low attenuation on CT].'),parents=['lesion'])],skip=skip))

rows = report('ra.acute-stroke',['imaging-in-acute-stroke','vascular-territories'])
protocol(rows,['non-contrast CT','CT with CT angiography','CT with CT angiography and perfusion','MRI','MRI with MR angiography'])
brain_regions(rows,'mixed')
rows.append(row('infarct','Infarct territory','Infarct characterisation',None,[
    f('lesion','Territory','There is an infarct in the [right / left / bilateral] [ACA / MCA / PCA / anterior choroidal / PICA / AICA / superior cerebellar / perforator / cortical borderzone / internal borderzone] territory.'),
    f('extent','Extent','The infarct involves [a focal portion / multiple portions / most] of the named territory.',parents=['lesion']),
    f('age','Imaging stage','The infarct has imaging features of [acute / subacute / chronic] injury.',parents=['lesion']),
    f('dwi','DWI / ADC','On MRI there is [DWI hyperintensity with reduced ADC / DWI hyperintensity without reduced ADC / no DWI hyperintensity] in the infarct.',parents=['lesion']),
    f('flair','FLAIR','The diffusion-positive lesion is [not visible / subtly visible / clearly hyperintense] on FLAIR.',parents=['lesion']),
    f('haemorrhage','Haemorrhagic transformation','The infarct contains [scattered petechiae / confluent petechiae / a focal haematoma without substantial mass effect / a haematoma with substantial mass effect].',parents=['lesion']),size()
],repeat=True,repeat_label='Infarct'))
for side in ['right','left']:
    for vessel in ['cervical internal carotid artery','intracranial internal carotid artery','M1 middle cerebral artery','M2 middle cerebral branches','A1 anterior cerebral artery','A2 anterior cerebral artery','P1 posterior cerebral artery','P2 posterior cerebral artery','intracranial vertebral artery']:
        rows.append(row(slug(side+'-'+vessel),side.title()+' '+vessel,'Angiography',f'The {side} {vessel} is patent without a focal high-grade stenosis on the acquired angiogram.',[
            f('occlusion','Occlusion',f'The {side} {vessel} is occluded [proximally / distally].',exclusive='lumen'),f('stenosis','Stenosis',f'There is [mild / moderate / severe] stenosis of the {side} {vessel}.',exclusive='lumen'),f('reconstitution','Distal reconstitution',f'The {side} {vessel} has [preserved distal reconstitution / reduced distal reconstitution / no distal reconstitution].',parents=['occlusion'])],skip=True))
rows.extend([
    row('basilar','Basilar artery','Angiography','The basilar artery is patent without a focal high-grade stenosis on the acquired angiogram.',[f('occlusion','Occlusion','The basilar artery is occluded in the [proximal / middle / distal] segment.',exclusive='lumen'),f('stenosis','Stenosis','There is [mild / moderate / severe] basilar artery stenosis.',exclusive='lumen')],skip=True),
    row('perfusion','Perfusion assessment','Perfusion',None,[f('quality','Perfusion quality','The acquired perfusion study is [diagnostic / limited by motion / limited by bolus timing / limited by incomplete coverage].'),f('territory','Perfusion deficit','There is a [right / left / bilateral] [ACA / MCA / PCA / posterior fossa] perfusion abnormality.'),f('core','Software core estimate','The software-estimated ischaemic core volume is __ mL.',parents=['territory']),f('delay','Software hypoperfusion estimate','The software-estimated hypoperfused tissue volume is __ mL.',parents=['territory'])],skip=True)
])
mass_effect(rows)
rows = report('ra.tinnitus',['pulsatile-and-non-pulsatile-tinnitus','3094199'])
protocol(rows,['MRI internal auditory canals','MRI with MR angiography and venography','CT angiography and venography','high-resolution temporal bone CT'])
rows.append(row('symptoms','Symptom classification','Clinical selection',None,[f('side','Symptom side','Tinnitus is reported on the [right / left / both sides].'),f('type','Symptom character','Tinnitus is reported as [pulse-synchronous / non-pulsatile].')],skip=True))
for side in ['right','left']:
    for name,normal,findings in [
        ('cerebellopontine angle',f'No focal mass is seen in the {side} cerebellopontine angle on acquired MRI.',[f('mass','CPA lesion',f'There is a {side} cerebellopontine-angle [solid / cystic / fat-containing] lesion.'),f('enhance','Enhancement',f'The {side} CPA lesion shows [homogeneous / heterogeneous / no] enhancement on acquired post-contrast MRI.',parents=['mass'])]),
        ('internal auditory canal',f'No focal mass is seen in the {side} internal auditory canal on acquired MRI.',[f('lesion','IAC lesion',f'There is a [fundal / mid-canal / porus-centred] lesion in the {side} internal auditory canal.'),f('size','IAC lesion size',f'The {side} IAC lesion measures __ × __ × __ mm.',parents=['lesion'])]),
        ('cochlear nerve',f'The {side} cochlear nerve is identified without focal enlargement on dedicated MRI.',[f('nerve','Cochlear nerve finding',f'The {side} cochlear nerve is [not identified / hypoplastic / enlarged].')]),
        ('vestibular nerves',f'The {side} vestibular nerves show no focal enlargement on dedicated MRI.',[f('nerve','Vestibular nerve finding',f'The {side} [superior / inferior / both] vestibular nerve is enlarged.')]),
        ('facial nerve',f'No focal lesion is seen along the imaged {side} facial nerve.',[f('lesion','Facial nerve lesion',f'There is a focal lesion along the {side} [cisternal / intracanalicular / labyrinthine / geniculate / tympanic / mastoid] facial nerve segment.')]),
        ('cochlea and vestibule',f'The {side} cochlea and vestibule retain normal fluid signal on acquired high-resolution MRI.',[f('signal','Labyrinthine signal',f'The {side} [cochlea / vestibule / semicircular canals] show [T1 hyperintensity / loss of normal T2 fluid signal / enhancement on post-contrast MRI].')]),
        ('middle ear',f'No focal mass is identified in the {side} middle ear on the acquired study.',[f('mass','Middle ear mass',f'There is a mass at the {side} [cochlear promontory / hypotympanum / epitympanum].'),f('enhance','Vascular enhancement',f'The {side} middle-ear mass enhances avidly on acquired contrast imaging.',parents=['mass'])]),
        ('jugular bulb',f'The {side} jugular bulb has no diverticulum or bony dehiscence on acquired CT.',[f('variant','Jugular bulb variant',f'The {side} jugular bulb is [high-riding / dehiscent into the middle ear / diverticular].')]),
        ('sigmoid sinus wall',f'The {side} sigmoid sinus wall is intact on acquired CT.',[f('wall','Sigmoid wall finding',f'The {side} sigmoid sinus wall shows [dehiscence / a diverticulum / erosion].')]),
        ('petrous carotid canal',f'The {side} petrous carotid canal has intact bone on acquired CT.',[f('variant','Carotid canal variant',f'The {side} carotid has [an aberrant middle-ear course / focal bony dehiscence / aneurysmal expansion].')]),
        ('superior semicircular canal',f'The {side} superior semicircular canal has intact bony covering on dedicated reformatted CT.',[f('defect','Superior canal covering',f'The {side} superior semicircular canal shows [definite dehiscence / markedly thin bone without definite dehiscence].')]),
        ('transverse sigmoid junction',f'The {side} transverse-sigmoid junction is patent without a focal high-grade stenosis on acquired venography.',[f('stenosis','Venous stenosis',f'There is [mild / moderate / severe] focal stenosis at the {side} transverse-sigmoid junction.'),f('thrombus','Venous thrombosis',f'There is thrombosis at the {side} transverse-sigmoid junction.')])
    ]:
        rows.append(row(slug(side+'-'+name),side.title()+' '+name,'Side-specific auditory and vascular pathways',normal,findings,skip=True))
rows.extend([
    row('shunting','Arteriovenous shunt clues','Vascular assessment',None,[f('vessels','Abnormal vessels','The acquired angiographic images show [enlarged meningeal vessels / prominent transosseous vessels / a vascular nidus / arterialised-appearing draining veins / no definite shunt-related abnormality].'),f('timing','Early venous filling','On acquired time-resolved angiography there is [no demonstrated early venous filling / early venous filling suspicious for an arteriovenous shunt].'),f('limit','Shunt assessment limit','The examination is not a catheter angiogram and a small dural arteriovenous fistula is not excluded by these images.')],skip=True),
    row('pressure-clues','Intracranial pressure imaging signs','Associated findings',None,[f('sella','Sellar appearance','There is [no empty sella / a partially empty sella / a completely empty sella].'),f('optic','Optic nerve sheath','There is [no visible / bilateral] optic nerve sheath distension.'),f('globe','Posterior globe contour','There is [no visible / bilateral] posterior globe flattening.')],skip=True)
])

rows = report('ra.mri-trigeminal',['trigeminal-neuralgia-and-neuropathy','69509'])
protocol(rows,['dedicated trigeminal MRI without contrast','dedicated trigeminal MRI before and after contrast'],[f('sequence','High-resolution acquisition','The study includes [high-resolution three-dimensional heavily T2-weighted imaging / conventional sequences without dedicated high-resolution nerve imaging].')])
for side in ['right','left']:
    group=side.title()+' trigeminal pathway'
    rows.extend([
        row(side+'-nucleus',side.title()+' trigeminal nuclei / fascicles',group,f'No focal signal abnormality is identified along the {side} pontine trigeminal nuclei and fascicles.',[f('signal','Pontine lesion',f'There is [T2 hyperintensity / restricted diffusion / a haemorrhagic lesion / an expansile lesion] along the {side} intrapontine trigeminal pathway.')]),
        row(side+'-root-entry',side.title()+' root entry zone',group,f'The {side} trigeminal root entry zone has no deforming vascular contact.',[f('contact','Vascular contact',f'There is contact between the {side} trigeminal root entry zone and [the superior cerebellar artery / the anterior inferior cerebellar artery / an ectatic basilar artery / a vein / an indeterminate vessel].'),f('effect','Nerve effect',f'The contacting vessel causes [no visible deformation / displacement / indentation / focal thinning] of the {side} nerve.',parents=['contact']),f('surface','Contact surface',f'Contact is on the [superior / inferior / medial / lateral] surface of the {side} nerve.',parents=['contact'])]),
        row(side+'-cisternal',side.title()+' cisternal segment',group,f'The {side} cisternal trigeminal nerve has normal calibre.',[f('mass','Cisternal lesion',f'There is a [focal nerve enlargement / cisternal mass adjacent to the nerve / diffusion-restricting cisternal lesion] along the {side} trigeminal nerve.'),f('atrophy','Nerve atrophy',f'The {side} cisternal trigeminal nerve is atrophic.'),f('enhance','Nerve enhancement',f'The {side} cisternal nerve shows [smooth / nodular] enhancement on acquired post-contrast images.')]),
        row(side+'-meckel',side.title()+' Meckel cave / ganglion',group,f'The {side} Meckel cave has preserved CSF signal without a mass.',[f('mass','Meckel cave lesion',f'The {side} Meckel cave contains [a solid lesion / a cystic lesion / infiltrative tissue] with [preserved / expanded] bony contours.'),f('enhance','Ganglion enhancement',f'The {side} trigeminal ganglion shows asymmetric [smooth / nodular] enhancement on acquired post-contrast images.')]),
        row(side+'-cavernous',side.title()+' cavernous sinus / V1–V2',group,f'No focal mass is identified in the {side} cavernous sinus.',[f('lesion','Cavernous lesion',f'The {side} cavernous sinus is involved by [a focal mass / infiltrative tissue / an aneurysmal vascular lesion].'),f('v1','V1 pathway',f'There is abnormal tissue along the {side} V1 pathway through the superior orbital fissure.'),f('v2','V2 pathway',f'There is abnormal tissue along the {side} V2 pathway through the foramen rotundum.')]),
        row(side+'-v2',side.title()+' V2 / pterygopalatine fossa',group,f'The fat around the imaged {side} V2 pathway and pterygopalatine fossa is preserved.',[f('spread','V2 perineural spread',f'There is [nerve enlargement / loss of perineural fat / abnormal post-contrast enhancement] along the {side} [foramen rotundum / pterygopalatine fossa / infraorbital canal].')]),
        row(side+'-v3',side.title()+' V3 / foramen ovale',group,f'The imaged {side} V3 pathway has no focal enlargement or mass.',[f('spread','V3 perineural spread',f'There is [nerve enlargement / foraminal expansion / abnormal post-contrast enhancement] along the {side} V3 pathway.'),f('distal','Distal branch',f'The {side} abnormality extends along the [inferior alveolar nerve / lingual nerve / auriculotemporal nerve].',parents=['spread'])]),
        row(side+'-masseter',side.title()+' masseter',group,f'The {side} masseter has preserved bulk and signal.',[f('denervation','Denervation',f'The {side} masseter shows [oedema with preserved bulk / fatty atrophy].')]),
        row(side+'-temporalis',side.title()+' temporalis',group,f'The {side} temporalis has preserved bulk and signal.',[f('denervation','Denervation',f'The {side} temporalis shows [oedema with preserved bulk / fatty atrophy].')]),
        row(side+'-medial-pterygoid',side.title()+' medial pterygoid',group,f'The {side} medial pterygoid has preserved bulk and signal.',[f('denervation','Denervation',f'The {side} medial pterygoid shows [oedema with preserved bulk / fatty atrophy].')]),
        row(side+'-lateral-pterygoid',side.title()+' lateral pterygoid',group,f'The {side} lateral pterygoid has preserved bulk and signal.',[f('denervation','Denervation',f'The {side} lateral pterygoid shows [oedema with preserved bulk / fatty atrophy].')])
    ])
rows.append(row('trigeminal-lesion','Trigeminal pathway target lesion','Lesion detail',None,[f('lesion','Target segment','There is a lesion along the [right / left] [brainstem / cisternal / Meckel cave / cavernous / V1 / V2 / V3] segment of the trigeminal pathway.'),size(),f('signal','Signal characteristics','The lesion is [T2 hyperintense / T2 hypointense / mixed T2 signal] and [restricts diffusion / does not restrict diffusion].',parents=['lesion']),f('enhance','Contrast pattern','The lesion shows [homogeneous / heterogeneous / peripheral / no] enhancement on acquired post-contrast images.',parents=['lesion'])],repeat=True))
rows = report('ra.swallowing',['swallowing-disorders-update','69471'])
protocol(rows,['videofluoroscopic swallowing study','barium pharyngogram'],[f('projection','Views','The examination included [lateral views / lateral and frontal views].'),f('consistency','Tested consistency','Swallows were assessed with [thin liquid / mildly thick liquid / moderately thick liquid / puree / solid bolus].')])
for identifier,label,normal,findings in [
    ('lip-seal','Lip seal','Lip seal is maintained during the observed swallows.',[f('escape','Anterior escape','There is [mild / marked] anterior bolus escape.')]),
    ('tongue-control','Oral bolus control','The tongue maintains and transfers the observed bolus.',[f('control','Bolus control','There is [impaired bolus formation / repetitive tongue pumping / premature posterior bolus escape / oral residue].')]),
    ('palate','Velopharyngeal closure','No nasopharyngeal reflux occurs during the observed swallows.',[f('reflux','Nasal reflux','Contrast refluxes into the nasopharynx during swallowing.')]),
    ('trigger','Pharyngeal swallow initiation','Pharyngeal swallowing begins without visible prolonged delay during the observed swallows.',[f('delay','Delayed initiation','Pharyngeal initiation is delayed with the bolus reaching the [valleculae / piriform sinuses] before the swallow.')]),
    ('tongue-base','Tongue-base retraction','Tongue-base retraction is adequate during the observed swallows.',[f('retraction','Reduced retraction','Tongue-base retraction is reduced [mildly / markedly].')]),
    ('hyolaryngeal','Hyoid and laryngeal elevation','Hyolaryngeal elevation and anterior excursion are preserved during the observed swallows.',[f('excursion','Reduced excursion','There is reduced [hyoid anterior excursion / laryngeal elevation / combined hyolaryngeal excursion].')]),
    ('epiglottis','Epiglottic inversion','Epiglottic inversion is complete during the observed swallows.',[f('inversion','Impaired inversion','Epiglottic inversion is [partial / absent].')]),
    ('pharyngeal-contraction','Pharyngeal contraction','Pharyngeal contraction is symmetric on the acquired frontal views.',[f('asymmetry','Asymmetric contraction','Pharyngeal contraction is reduced on the [right / left / both sides].')]),
    ('valleculae','Vallecular residue','No substantial vallecular residue remains after the observed swallows.',[f('residue','Vallecular residue','There is [mild / moderate / marked] vallecular residue after [thin liquid / thick liquid / puree / solid] swallowing.'),f('clear','Clearance','Vallecular residue [clears with a repeat swallow / persists despite repeat swallowing].',parents=['residue'])]),
    ('piriform','Piriform sinus residue','No substantial piriform sinus residue remains after the observed swallows.',[f('residue','Piriform residue','There is [right / left / bilateral] [mild / moderate / marked] piriform sinus residue.'),f('clear','Clearance','Piriform sinus residue [clears with a repeat swallow / persists despite repeat swallowing].',parents=['residue'])]),
    ('ues','Upper oesophageal sphincter','The upper oesophageal sphincter opens during the observed swallows without significant hold-up.',[f('opening','Impaired opening','Upper oesophageal sphincter opening is [reduced / brief / absent].'),f('bar','Cricopharyngeal bar','There is a cricopharyngeal bar causing [no significant / mild / marked] bolus hold-up.')]),
    ('cervical-oesophagus','Cervical oesophagus','No fixed narrowing is seen in the visualised cervical oesophagus.',[f('web','Web','There is a cervical oesophageal web.'),f('diverticulum','Diverticulum','There is a [posterior pharyngoesophageal / left anterolateral / right anterolateral] diverticulum.'),f('size','Diverticulum dimensions','The diverticulum measures __ × __ mm.',parents=['diverticulum']),f('extrinsic','Extrinsic impression','The cervical oesophagus is indented by [anterior vertebral osteophytes / an extrinsic soft-tissue impression].')]),
]:
    rows.append(row(identifier,label,'Observed swallowing mechanics',normal,findings,skip=True))
rows.append(row('swallow-trial','Bolus trial / airway protection','Trial-specific findings',None,[
    f('trial','Bolus consistency','A trial was performed with [thin liquid / mildly thick liquid / moderately thick liquid / puree / solid] in [upright neutral position / chin-tuck position / right head-turn position / left head-turn position].'),
    f('airway','Airway entry','During this trial there is [no airway entry / supraglottic penetration / penetration reaching the vocal folds / aspiration below the vocal folds].',parents=['trial']),
    f('timing','Timing of airway entry','Airway entry occurs [before / during / after] the swallow.',parents=['airway']),
    f('response','Protective response','Observed airway material is [completely expelled / partially expelled / not expelled despite a cough / not associated with a cough].',parents=['airway']),
    f('clearance','Bolus clearance','There is [complete / incomplete] pharyngeal clearance for this trial.',parents=['trial'])
],repeat=True,repeat_label='Trial'))

rows = report('ra.ct-mri-eye',['orbita/pathology'])
protocol(rows,['non-contrast orbital CT','contrast-enhanced orbital CT','orbital MRI without contrast','orbital MRI before and after contrast'])
for side in ['right','left']:
    group=side.title()+' orbit'
    rows.extend([
        row(side+'-globe',side.title()+' globe',group,f'The {side} globe has preserved contour and volume.',[f('rupture','Globe injury','The {side} globe has [contour disruption / reduced volume / intraocular gas / an intraocular foreign body].'),f('size','Globe configuration',f'The {side} globe is [enlarged / small / elongated with posterior staphyloma / phthisical].')]),
        row(side+'-lens',side.title()+' lens',group,f'The {side} lens lies in its expected position.',[f('lens','Lens position',f'The {side} lens is [anteriorly dislocated / posteriorly dislocated / subluxed / surgically absent with lens implant].')]),
        row(side+'-vitreous',side.title()+' vitreous / retina',group,f'No focal lesion or detachment is identified in the {side} ocular cavity on the acquired images.',[f('blood','Vitreous blood',f'There are blood products in the {side} vitreous cavity.'),f('detach','Detachment',f'There is a {side} [retinal / choroidal] detachment.'),f('mass','Intraocular mass',f'There is a {side} [posterior / anterior] intraocular mass with [no visible calcification / calcification on acquired CT].')]),
        row(side+'-sclera',side.title()+' sclera / uvea',group,f'The {side} scleral contour is not abnormally thickened.',[f('thick','Wall thickening',f'The {side} globe wall has [focal / diffuse] thickening.'),f('enhance','Wall enhancement',f'The {side} globe wall shows abnormal enhancement on acquired post-contrast images.')]),
        row(side+'-optic-nerve',side.title()+' optic nerve',group,f'The {side} optic nerve is not enlarged on the acquired images.',[f('enlarge','Optic nerve enlargement',f'The {side} optic nerve is [fusiformly / nodularly] enlarged.'),f('signal','Optic nerve signal on MRI',f'The {side} optic nerve has T2 hyperintensity on the acquired MRI.'),f('enhance','Optic nerve enhancement',f'On post-contrast imaging there is [intraneural / perineural / both intraneural and perineural] enhancement of the {side} optic nerve.'),f('atrophy','Optic nerve atrophy',f'The {side} optic nerve is atrophic.')]),
        row(side+'-nerve-sheath',side.title()+' optic nerve sheath',group,f'The {side} optic nerve sheath is not visibly distended.',[f('distend','Sheath distension',f'The {side} optic nerve sheath is distended.'),f('lesion','Sheath lesion',f'There is a [circumferential / eccentric] lesion along the {side} optic nerve sheath.')]),
        row(side+'-intraconal',side.title()+' intraconal fat',group,f'The {side} intraconal fat contains no focal lesion or oedema.',[f('stranding','Intraconal oedema',f'There is [mild / marked] oedema in the {side} intraconal fat.'),f('mass','Intraconal lesion',f'There is a [well-circumscribed / infiltrative] {side} intraconal lesion.')]),
        row(side+'-extraconal',side.title()+' extraconal space',group,f'The {side} extraconal space contains no focal lesion.',[f('lesion','Extraconal lesion',f'There is a [superior / inferior / medial / lateral] {side} extraconal [mass / collection / haematoma].'),f('abscess','Collection diffusion','The extraconal collection shows restricted diffusion on acquired MRI.',parents=['lesion'])]),
        row(side+'-lacrimal',side.title()+' lacrimal gland',group,f'The {side} lacrimal gland is not enlarged.',[f('enlarge','Lacrimal enlargement',f'The {side} lacrimal gland is [diffusely enlarged / focally nodular].'),f('lesion','Lacrimal lesion',f'The {side} lacrimal gland contains a [well-defined / infiltrative] lesion.')]),
        row(side+'-apex',side.title()+' orbital apex',group,f'No focal lesion is identified at the {side} orbital apex.',[f('crowding','Apical crowding',f'There is crowding at the {side} orbital apex.'),f('extension','Apical extension',f'A lesion extends through the {side} [optic canal / superior orbital fissure / inferior orbital fissure].')]),
        row(side+'-preseptal',side.title()+' preseptal tissues',group,f'The {side} preseptal tissues are not swollen.',[f('oedema','Preseptal swelling',f'There is [mild / marked] {side} preseptal swelling.'),f('collection','Preseptal collection',f'There is a {side} preseptal collection.')]),
        row(side+'-sov',side.title()+' superior ophthalmic vein',group,f'The {side} superior ophthalmic vein is not enlarged.',[f('enlarge','Vein enlargement',f'The {side} superior ophthalmic vein is enlarged.'),f('thrombus','Venous filling defect',f'On acquired contrast imaging there is a filling defect in the {side} superior ophthalmic vein.')]),
        row(side+'-wall',side.title()+' orbital walls','CT bone assessment',f'No fracture or focal destruction is identified in the {side} orbital walls on the acquired CT.',[f('fracture','Wall fracture',f'There is a {side} [floor / medial wall / roof / lateral wall] fracture.'),f('herniation','Soft-tissue herniation',f'The {side} fracture has herniation of [fat / fat and extraocular muscle] through the defect.',parents=['fracture']),f('erosion','Bone change',f'There is [erosion / remodelling / hyperostosis] of the {side} orbital wall.')],skip=True)
    ])
    for muscle in ['superior rectus','inferior rectus','medial rectus','lateral rectus','superior oblique','inferior oblique']:
        rows.append(row(slug(side+'-'+muscle),side.title()+' '+muscle,'Extraocular muscles',f'The {side} {muscle} is not enlarged.',[f('enlargement','Muscle enlargement',f'The {side} {muscle} is enlarged with [tendon sparing / tendon involvement].'),f('signal','MRI signal',f'The {side} {muscle} has T2 hyperintensity on the acquired MRI.'),f('displace','Displacement',f'The {side} {muscle} is [displaced / compressed / entrapped at a fracture defect].')]))
rows.append(row('orbital-lesion','Orbital target lesion','Lesion detail',None,[f('lesion','Lesion location','The target lesion lies in the [right / left] [ocular / intraconal / extraconal / lacrimal / orbital apex] compartment.'),size(),f('enhance','Post-contrast enhancement','The lesion shows [no / homogeneous / heterogeneous / peripheral] enhancement on acquired post-contrast images.',parents=['lesion']),f('diffusion','MRI diffusion','The lesion shows [restricted diffusion / facilitated diffusion / indeterminate diffusion] on acquired MRI.',parents=['lesion'])],repeat=True))

rows = report('ra.mri-sinuses',['paranasal-sinuses/mri-examination'])
protocol(rows,['sinonasal MRI without contrast','sinonasal MRI before and after intravenous contrast'])
for side in ['right','left']:
    for sinus in ['frontal','anterior ethmoid','posterior ethmoid','maxillary','sphenoid']:
        rows.append(row(slug(side+'-'+sinus),side.title()+' '+sinus+' sinus','Paranasal sinuses',f'The {side} {sinus} sinus has no significant mucosal disease or focal lesion.',[
            f('mucosal','Mucosal thickening',f'There is [mild / moderate / marked] mucosal thickening in the {side} {sinus} sinus.'),
            f('fluid','Retained contents',f'The {side} {sinus} sinus contains [simple fluid / proteinaceous T1-bright contents / T2-dark contents / an air-fluid level].'),
            f('mass','Focal mass',f'There is a [solid / polypoid / expansile cystic] lesion in the {side} {sinus} sinus.'),
            f('enhance','Enhancement pattern',f'On post-contrast imaging the {side} {sinus} abnormality has [peripheral mucosal enhancement only / solid enhancement / convoluted cerebriform enhancement / non-enhancing devitalised mucosa].',parents=['mucosal','fluid','mass'])]))
    for site in ['nasal cavity','middle meatus','frontal recess','sphenoethmoidal recess','pterygopalatine fossa','retroantral fat','orbital apex','cavernous sinus']:
        rows.append(row(slug(side+'-'+site),side.title()+' '+site,'Drainage pathways and extension',f'No focal soft-tissue abnormality is identified in the {side} {site} on the acquired images.',[
            f('tissue','Abnormal tissue',f'There is [oedema / infiltrative tissue / a focal mass / obstructing polypoid tissue] in the {side} {site}.'),
            f('enhance','Post-contrast pattern',f'The {side} {site} abnormality shows [solid / peripheral / absent] enhancement on post-contrast imaging.',parents=['tissue'])]))
rows.extend([
    row('septum','Nasal septum','Nasal cavity','No focal nasal septal mass is identified.',[f('deviation','Septal deviation','The septum deviates [rightward / leftward].'),f('mass','Septal lesion','There is a [solid / cystic / destructive] nasal septal lesion.')]),
    row('cribriform','Cribriform plate / anterior skull base','Skull-base interface','No intracranial soft-tissue extension is identified at the anterior skull base.',[f('extension','Skull-base extension','Abnormal tissue extends across the [right / left / midline] anterior skull base.'),f('encephalocele','Encephalocele','There is a [right / left / midline] [meningocele / meningoencephalocele] through the anterior skull base.')]),
    row('intracranial','Intracranial complications','Complications','No focal intracranial collection is seen in the imaged field.',[f('empyema','Empyema','There is an adjacent [epidural / subdural] collection with restricted diffusion.'),f('abscess','Cerebral abscess','There is a [frontal / temporal] parenchymal lesion with a diffusion-restricting centre.'),f('meninges','Meningeal enhancement','Abnormal adjacent [dural / leptomeningeal] enhancement is present on acquired post-contrast images.')]),
    row('sinonasal-lesion','Sinonasal lesion','Target lesion',None,[f('lesion','Lesion origin','The lesion is centred in the [right / left / midline] [nasal cavity / maxillary sinus / ethmoid region / frontal sinus / sphenoid sinus].'),size(),f('diffusion','Diffusion','The lesion shows [restricted / facilitated / heterogeneous] diffusion.',parents=['lesion']),f('perineural','Perineural extension','There is extension along the [infraorbital canal / vidian canal / foramen rotundum / foramen ovale].',parents=['lesion']),f('CT','Correlated CT bone finding','Correlated CT demonstrates [remodelling / erosion / hyperostosis / a focal skull-base defect].',parents=['lesion'])],repeat=True)
])

rows = report('ra.ct-temporal-bone',['temporal-bone/anatomy-2-0','temporal-bone/pathology'])
protocol(rows,['high-resolution temporal bone CT'])
for side in ['right','left']:
    for name,normal,features in [
        ('external auditory canal','is patent without focal bony erosion','soft-tissue occlusion / focal inferior wall erosion / exostoses / congenital atresia'),
        ('tympanic membrane','is not thickened or retracted','thickening / retraction / perforation / a ventilation tube'),
        ('Prussak space','is aerated','soft tissue without erosion / soft tissue with scutal erosion'),
        ('scutum','is intact','blunting / focal erosion'),
        ('epitympanum','is aerated','soft-tissue opacification / an expansile lesion'),
        ('mesotympanum','is aerated','soft-tissue opacification / a hypotympanic-contiguous mass'),
        ('hypotympanum','is aerated','fluid / a soft-tissue mass'),
        ('malleus','is intact','head erosion / handle erosion / congenital malformation / dislocation'),
        ('incus','is intact','body erosion / long-process erosion / lenticular-process erosion / dislocation'),
        ('stapes','has intact visible crura and footplate','crural erosion / footplate thickening / malformation / nonvisualisation'),
        ('incudomalleolar joint','is aligned','diastasis / dislocation / fusion'),
        ('incudostapedial joint','is aligned','diastasis / dislocation / erosion'),
        ('aditus ad antrum','is patent','soft-tissue opacification / widening with erosion'),
        ('mastoid air cells','are aerated with preserved septa','partial opacification / complete opacification / coalescent septal destruction / sclerosis with poor pneumatization'),
        ('tegmen tympani','is intact','focal thinning / dehiscence / fracture'),
        ('tegmen mastoideum','is intact','focal thinning / dehiscence / fracture'),
        ('cochlea','has preserved bony morphology','incomplete partition / hypoplasia / labyrinthine ossification / pericochlear lucency'),
        ('vestibule','has preserved bony morphology','enlargement / dysplasia / labyrinthine ossification'),
        ('superior semicircular canal','has intact bony covering','dehiscence / marked thinning / dysplasia / ossification'),
        ('posterior semicircular canal','has intact bony covering','dehiscence / dysplasia / ossification'),
        ('lateral semicircular canal','has intact bony covering','fistula or erosion / dysplasia / ossification'),
        ('vestibular aqueduct','is not enlarged','enlargement / nonvisualisation'),
        ('internal auditory canal','has preserved bony margins and calibre','widening / narrowing / erosion'),
        ('labyrinthine facial canal','has intact visible margins','widening / erosion / fracture'),
        ('geniculate ganglion fossa','has preserved bony margins','enlargement / erosion / a honeycomb bony lesion'),
        ('tympanic facial canal','has intact visible bony covering','dehiscence / erosion / aberrant course'),
        ('mastoid facial canal','has preserved bony margins','widening / erosion / fracture'),
        ('oval window','is patent','obliteration / surrounding lucency / footplate thickening'),
        ('round window niche','is patent','soft-tissue obstruction / bony obliteration'),
        ('carotid canal','has intact bony covering','dehiscence / aberrant course into the middle ear / fracture'),
        ('jugular bulb plate','is intact','dehiscence / a high-riding bulb / a diverticulum'),
        ('sigmoid sinus plate','is intact','dehiscence / erosion / a diverticulum'),
        ('petrous apex','has no expansile or destructive lesion','trapped fluid without expansion / an expansile lesion / destructive change / fatty marrow asymmetry')
    ]:
        rows.append(row(slug(side+'-'+name),side.title()+' '+name,side.title()+' temporal bone',f'The {side} {name} {normal}.',[
            f('abnormality','Specific finding',f'The {side} {name} shows [{features}].')]))
    rows.append(row(side+'-otosclerosis',side.title()+' otic capsule / fissula ante fenestram','Otic capsule',f'No focal lucency is seen at the {side} fissula ante fenestram or pericochlear capsule.',[f('fenestral','Fenestral lucency',f'There is focal lucency at the {side} fissula ante fenestram.'),f('retrofenestral','Retrofenestral lucency',f'There is [focal / circumferential] pericochlear lucency on the {side}.')]))
def cervical_nodes(rows, reference=False, ultrasound=False):
    levels=[('Ia','submental'),('Ib','submandibular'),('IIa','upper jugular anterior to the spinal accessory nerve'),('IIb','upper jugular posterior to the spinal accessory nerve'),('III','mid-jugular'),('IV','lower jugular'),('Va','upper posterior triangle'),('Vb','lower posterior triangle'),('VI','central compartment'),('VIIa','retropharyngeal'),('VIIb','retrostyloid'),('VIII','parotid'),('IX','buccofacial'),('Xa','retroauricular'),('Xb','occipital')]
    for side in ['right','left']:
        for level,name in levels:
            # Level Ia is conventionally a midline compartment and is authored once.
            if level=='Ia' and side=='left': continue
            prefix='midline' if level=='Ia' else side
            normal=(f'No morphologically suspicious node is identified in the assessed {prefix} level {level} ({name}) region.' if reference else f'No morphologically suspicious node is identified in the imaged {prefix} level {level} ({name}) region.')
            rows.append(row(slug(prefix+'-node-'+level),prefix.title()+' level '+level+' · '+name,'Cervical nodal stations',normal,[
                f('node','Mapped node',f'A node is mapped to the {prefix} level {level} ({name}) region.'),
                f('dimensions','Node dimensions',f'The {prefix} level {level} node measures __ mm in short axis and __ mm in long axis.',parents=['node']),
                f('morphology','Node morphology',f'The mapped node is [oval with preserved fatty hilum / rounded with absent fatty hilum / cystic / centrally necrotic / calcified / matted].',parents=['node']),
                f('ene','Extranodal extension features','The mapped node has [no visible extranodal spread / an irregular infiltrative margin / adjacent muscle invasion / vascular encasement].',parents=['node']),
                f('side-relation','Adjacent structure','The mapped node is [separate from / abutting / inseparable from] the [carotid artery / internal jugular vein / sternocleidomastoid muscle / salivary gland].',parents=['node'])
            ],repeat=True,repeat_label='Node',skip=reference))

def neck_spaces(rows):
    for side in ['right','left']:
        for space in ['parotid','masticator','parapharyngeal','carotid','sublingual','submandibular','posterior cervical']:
            rows.append(row(side+'-'+space+'-space',side.title()+' '+space+' space','Deep neck spaces',f'No focal mass or collection is identified in the {side} {space} space.',[
                f('mass','Space-centred lesion',f'There is a [well-defined / infiltrative / multiloculated] [solid / cystic / mixed solid and cystic / fat-containing] lesion in the {side} {space} space.'),
                f('oedema','Inflammatory change',f'The {side} {space} space contains [mild / marked] oedematous change.'),
                f('collection','Collection',f'There is a collection in the {side} {space} space.'),
                f('diffusion','Collection diffusion',f'The {side} {space} collection shows [restricted diffusion / no restricted diffusion / indeterminate diffusion] on acquired diffusion images.',parents=['collection']),
                f('enhancement','Post-contrast pattern',f'On post-contrast images the {side} {space} lesion has [homogeneous / heterogeneous / peripheral / no] enhancement.',parents=['mass','collection'])]))
    for space in ['retropharyngeal','danger','prevertebral','visceral']:
        rows.append(row(space+'-space',space.title()+' space','Midline and trans-spatial spread',f'No focal mass or collection is identified in the {space} space.',[
            f('mass','Space-centred lesion',f'There is a [solid / cystic / mixed] lesion in the {space} space.'),
            f('fluid','Fluid',f'There is [thin non-loculated / loculated] fluid in the {space} space.'),
            f('extent','Caudal extent',f'The {space} abnormality extends to [the hyoid level / the cricoid level / the thoracic inlet / the imaged superior mediastinum].',parents=['mass','fluid']),
            f('enhance','Post-contrast enhancement',f'The {space} lesion has [no / solid / peripheral] enhancement on acquired post-contrast images.',parents=['mass','fluid'])]))
    for side in ['right','left']:
        rows.extend([
            row(side+'-parotid-gland',side.title()+' parotid gland','Salivary glands',f'The {side} parotid gland has no focal lesion or duct dilatation.',[f('lesion','Gland lesion',f'There is a [superficial lobe / deep lobe / both superficial and deep lobe] lesion of the {side} parotid gland.'),f('duct','Duct dilatation',f'The {side} parotid duct is dilated [without a demonstrated obstructing lesion / with a visible intraductal filling defect].'),f('inflamed','Inflammatory change',f'The {side} parotid gland is enlarged and oedematous.')]),
            row(side+'-submandibular-gland',side.title()+' submandibular gland','Salivary glands',f'The {side} submandibular gland has no focal lesion or duct dilatation.',[f('lesion','Gland lesion',f'There is a [solid / cystic] lesion in the {side} submandibular gland.'),f('duct','Duct dilatation',f'The {side} submandibular duct is dilated.'),f('inflamed','Inflammatory change',f'The {side} submandibular gland is enlarged and oedematous.')]),
            row(side+'-jugular',side.title()+' internal jugular vein','Vascular structures',f'The imaged {side} internal jugular vein is patent on the acquired vascular or post-contrast images.',[f('thrombus','Jugular thrombus',f'There is [non-occlusive / occlusive] thrombosis of the {side} internal jugular vein.'),f('compression','Venous compression',f'The {side} internal jugular vein is compressed by the adjacent lesion.')],skip=True)
        ])
    rows.append(row('airway','Pharyngeal and laryngeal airway','Airway','The imaged airway is not significantly narrowed.',[f('narrow','Airway narrowing','There is [mild / moderate / severe] narrowing of the [nasopharyngeal / oropharyngeal / hypopharyngeal / supraglottic / glottic / subglottic] airway.'),f('deviation','Airway deviation','The airway is displaced [rightward / leftward / anteriorly].')]))

rows = report('ra.mri-neck-spaces',['MR-anatomy-and-pathology','Suprahyoid-neck-MR-Pathology','cervical-node-map'])
protocol(rows,['neck MRI without contrast','neck MRI before and after intravenous contrast'])
neck_spaces(rows)
cervical_nodes(rows)
rows.append(row('neck-lesion','Neck lesion characterisation','Target lesions',None,[f('lesion','Lesion centre','A lesion is centred in the [right / left / midline] [parotid space / masticator space / parapharyngeal space / carotid space / sublingual space / submandibular space / retropharyngeal space / prevertebral space / visceral space / posterior cervical space].'),size(),f('displacement','Displacement pattern','The lesion displaces the parapharyngeal fat [anteriorly / posteriorly / medially / laterally] and the carotid space [anteriorly / posteriorly / medially / laterally].',parents=['lesion']),f('perineural','Perineural spread','The lesion extends along the [mandibular nerve / maxillary nerve / facial nerve / hypoglossal nerve].',parents=['lesion']),f('skull-base','Skull-base involvement','The lesion involves the [foramen ovale / foramen rotundum / stylomastoid foramen / jugular foramen / hypoglossal canal].',parents=['lesion'])],repeat=True))

rows = report('ra.cervical-lymph-nodes',['cervical-node-map'])
protocol(rows,['CT node mapping','MRI node mapping','ultrasound node mapping','reference localisation only'])
cervical_nodes(rows,reference=True)
rows.append(row('mapping-convention','Nodal map convention','Reference scope',None,[f('convention','Map convention','Node locations use the named cervical map in the linked reference; retropharyngeal and retrostyloid levels are recorded as VIIa and VIIb, respectively.'),f('staging','Staging scope','Anatomical node mapping is recorded without automatically assigning a primary-site-specific N stage.')],skip=True))

rows = report('ra.head-neck-malignancy',['head-neck-tumors','cervical-node-map','MR-anatomy-and-pathology'])
protocol(rows,['contrast-enhanced neck CT','neck MRI before and after contrast','non-contrast neck MRI'])
for name in ['nasopharyngeal roof','right fossa of Rosenmüller','left fossa of Rosenmüller','right palatine tonsil','left palatine tonsil','tongue base','oral tongue','floor of mouth','right retromolar trigone','left retromolar trigone','hard palate','soft palate','posterior pharyngeal wall','right piriform sinus','left piriform sinus','postcricoid region','epiglottis','right aryepiglottic fold','left aryepiglottic fold','right true vocal cord','left true vocal cord','anterior commissure','subglottis']:
    rows.append(row(slug(name),name.title(),'Mucosal primary sites',f'No focal mucosal mass is identified at the {name} on the acquired images.',[
        f('mass','Mucosal lesion',f'There is [focal thickening / an exophytic mass / an infiltrative mass / ulceration] at the {name}.'),
        f('extent','Local depth',f'The {name} lesion [appears confined to the mucosal surface / extends into underlying muscle / infiltrates adjacent fat].',parents=['mass'])]))
for name in ['right paraglottic space','left paraglottic space','pre-epiglottic fat','thyroid cartilage','cricoid cartilage','hyoid bone','mandible','maxilla','prevertebral muscles','skull base']:
    rows.append(row(slug(name),name.title(),'Local tumour extension',f'No visible tumour invasion of the {name} is identified.',[f('invasion','Invasion',f'There is [suspected / definite] invasion of the {name}.'),f('uncertain','Indeterminate interface',f'The interface with the {name} is indeterminate because of [inflammation / motion / dental artefact / limited spatial resolution].')]))
for side in ['right','left']:
    rows.extend([
        row(side+'-carotid',side.title()+' carotid relationship','Resectability landmarks',f'The {side} carotid artery is not encased by tumour.',[f('encasement','Carotid contact',f'Tumour contacts the {side} carotid artery over [less than 90 degrees / 90–180 degrees / 180–270 degrees / more than 270 degrees] with [preserved calibre / luminal narrowing].')]),
        row(side+'-perineural',side.title()+' named neural pathways','Perineural spread',f'No abnormal enlargement or enhancement is seen along the assessed {side} skull-base neural pathways on the acquired post-contrast images.',[f('spread','Perineural spread',f'There is suspected perineural spread along the {side} [V2 / V3 / facial / hypoglossal] pathway.'),f('level','Proximal extent',f'The {side} perineural abnormality reaches the [pterygopalatine fossa / foramen rotundum / foramen ovale / Meckel cave / stylomastoid foramen / facial canal / hypoglossal canal].',parents=['spread'])],skip=True)
    ])
cervical_nodes(rows)
rows.append(row('primary-lesion','Primary lesion measurements','Target lesion',None,[f('lesion','Primary site','The primary lesion is centred in the [nasopharynx / oropharynx / oral cavity / hypopharynx / supraglottic larynx / glottis / subglottis / salivary gland / sinonasal cavity].'),size(),f('midline','Midline extent','The lesion [does not cross / crosses] the midline.',parents=['lesion']),f('response','Interval response','Compared with available prior imaging the primary lesion is [smaller / unchanged / larger / not identified].',parents=['lesion'])],repeat=True,repeat_label='Primary lesion'))

rows = report('ra.paediatric-neck-masses',['neck-masses-in-children','cervical-node-map'])
protocol(rows,['neck ultrasound','contrast-enhanced neck CT','neck MRI without contrast','neck MRI before and after contrast'])
for site in ['submental region','right submandibular region','left submandibular region','right parotid region','left parotid region','right lateral neck','left lateral neck','midline infrahyoid neck','suprasternal region']:
    rows.append(row(slug(site),site.title(),'Neck regions',f'No focal mass is identified in the examined {site}.',[
        f('mass','Mass',f'There is a [solid / cystic / mixed solid and cystic / predominantly fatty] mass in the {site}.'),
        f('vascularity','Vascularity',f'On acquired Doppler imaging the {site} mass shows [no internal / peripheral / internal / high-flow] vascularity.',parents=['mass']),
        f('inflammation','Inflammation',f'The {site} lesion has surrounding inflammatory change.',parents=['mass'])]))
rows.extend([
    row('hyoid-tract','Hyoid / thyroglossal tract','Developmental relations',None,[f('tract','Thyroglossal relation','A cystic lesion lies [above / at / below] the hyoid and [abuts the hyoid / extends around the hyoid / has no demonstrated hyoid relation].'),f('tongue-base','Tongue-base extension','The lesion extends toward the foramen caecum.'),f('thyroid','Orthotopic thyroid','Thyroid tissue is [present in the orthotopic thyroid bed / not identified in the orthotopic thyroid bed].')],skip=True),
    row('sublingual','Sublingual spaces / mylohyoid','Developmental relations','No focal lesion is identified in the examined floor of mouth.',[f('ranula','Ranula pattern','A [right / left] sublingual cystic lesion [remains above / extends below] the mylohyoid with a tail toward the sublingual gland.'),f('dermoid','Fat-containing cyst','A midline floor-of-mouth cyst contains [fat globules / restricted diffusion / neither definite fat nor restricted diffusion on the acquired images].')]),
    row('branchial','Branchial region','Developmental relations',None,[f('branchial','Branchial-pattern lesion','A [right / left] cystic lesion lies [between the submandibular gland and anterior sternocleidomastoid / in the parotid region / in the lower neck adjacent to the thyroid].'),f('sinus','Sinus tract','A tract is seen extending toward the [external auditory canal / tonsillar fossa / piriform sinus / skin surface].')],skip=True),
    row('vascular-malformation','Vascular / lymphatic lesion','Lesion characterisation',None,[f('lymphatic','Lymphatic morphology','There is a [macrocystic / microcystic / mixed] multiloculated lesion crossing [one / several] neck spaces.'),f('fluid-level','Fluid levels','The lymphatic-pattern lesion contains fluid-fluid levels.',parents=['lymphatic']),f('venous','Venous morphology','There are compressible venous channels with [slow Doppler flow / no detected Doppler flow / phleboliths].'),f('high-flow','High-flow pattern','The lesion has high-flow arterial and venous waveforms on acquired Doppler imaging.')],skip=True),
    row('paeds-neck-lesion','Target neck lesion','Lesion measurements',None,[f('lesion','Target site','The target lesion lies in the [right / left / midline] [upper neck / lower neck / floor of mouth / parotid region / retropharyngeal region].'),size(),f('airway','Airway effect','The lesion [does not narrow / mildly narrows / markedly narrows] the adjacent airway.',parents=['lesion']),f('deep','Deep extension','Cross-sectional imaging shows extension into the [parapharyngeal space / masticator space / carotid space / retropharyngeal space / mediastinum].',parents=['lesion'])],repeat=True)
])
cervical_nodes(rows)
rows = report('ra.ultrasound-thyroid',['ti-rads/ti-rads','ACR/Files/RADS/TI-RADS/TI-RADS-Ultrasound-Reporting-Template.pdf','Reporting-and-Data-Systems/TI-RADS'])
protocol(rows,['thyroid and cervical nodal ultrasound'])
for side in ['right','left']:
    rows.append(row(side+'-lobe',side.title()+' thyroid lobe','Thyroid parenchyma',f'The {side} thyroid lobe has homogeneous background echotexture.',[
        f('dimensions','Lobe dimensions',f'The {side} thyroid lobe measures __ × __ × __ mm.'),
        f('echotexture','Background echotexture',f'The {side} lobe is [mildly heterogeneous / markedly heterogeneous / diffusely hypoechoic / diffusely hyperechoic].'),
        f('vascularity','Doppler vascularity',f'The {side} lobe has [normal / increased / reduced] Doppler vascularity.'),
        f('absent','Lobe absent',f'The {side} thyroid lobe is [surgically absent / not visualised].')]))
rows.extend([
    row('isthmus','Isthmus','Thyroid parenchyma','The isthmus has homogeneous background echotexture.',[f('thickness','Isthmus thickness','The isthmus measures __ mm anteroposteriorly.'),f('texture','Isthmus texture','The isthmus is [heterogeneous / diffusely hypoechoic / surgically absent].')]),
    row('thyroid-nodule','Thyroid nodule','Nodules','No thyroid nodules are identified.',[
        f('nodule','Nodule location','The thyroid nodule location is [right upper pole / right mid portion / right lower pole / left upper pole / left mid portion / left lower pole / isthmus centrally / isthmus-right lobe junction / isthmus-left lobe junction].'),
        f('dimensions','Three dimensions','The nodule measures __ × __ × __ mm.',parents=['nodule']),
        f('composition','Composition','The nodule is [cystic or almost completely cystic / spongiform / mixed cystic and solid / solid or almost completely solid].',parents=['nodule'],exclusive='composition'),
        f('echogenicity','Echogenicity','The nodule or its solid component is [anechoic / hyperechoic or isoechoic / hypoechoic / very hypoechoic].',parents=['nodule'],exclusive='echogenicity'),
        f('shape','Shape','On the transverse image the nodule is [wider-than-tall / taller-than-wide].',parents=['nodule'],exclusive='shape'),
        f('margin','Margin','The nodule margin assessment is [smooth / ill-defined / lobulated or irregular / extrathyroidal extension].',parents=['nodule'],exclusive='margin'),
        f('echogenic-foci','Echogenic foci','The nodule contains [no echogenic foci / large comet-tail artefacts only / macrocalcification only / peripheral rim calcification only / punctate echogenic foci only / macrocalcification and peripheral rim calcification / macrocalcification and punctate echogenic foci / peripheral rim calcification and punctate echogenic foci / macrocalcification and peripheral rim calcification and punctate echogenic foci].',parents=['nodule'],exclusive='foci'),
        f('vascularity','Nodule vascularity','The nodule has [no detectable / predominantly peripheral / internal / mixed peripheral and internal] Doppler flow.',parents=['nodule']),
        f('interval','Interval size','Compared with the available prior examination this nodule is [unchanged / larger / smaller / newly visible].',parents=['nodule']),
        f('prior-size','Prior dimensions','The prior nodule dimensions were __ × __ × __ mm.',parents=['interval']),
        f('previous-sampling','Prior sampling','This nodule has [no documented previous sampling / documented prior benign cytology / documented prior indeterminate cytology / documented prior malignant cytology].',parents=['nodule'])
    ],repeat=True,repeat_label='Nodule'),
    row('retrosternal','Inferior thyroid extent','Extent','The visualised thyroid does not extend below the sonographic field.',[f('extension','Inferior extension','Thyroid tissue extends below the thoracic inlet and its inferior margin [is seen / is not fully seen] sonographically.')]),
    row('thyroid-bed','Thyroidectomy bed','Postoperative assessment',None,[f('bed','Bed assessment','The [right / left / bilateral] thyroidectomy bed contains [no focal lesion / a hypoechoic nodule / echogenic residual thyroid tissue / a fluid collection].')],skip=True)
])
for side in ['right','left']:
    for level in ['II','III','IV','V','VI']:
        rows.append(row(slug(side+'-node-'+level),side.title()+' level '+level+' nodes','Regional lymph nodes',f'No morphologically suspicious lymph node is seen in the examined {side} level {level} region.',[
            f('suspicious','Suspicious node',f'A {side} level {level} node has [cystic change / punctate echogenic foci / peripheral vascularity / round shape with absent fatty hilum / abnormal echogenic cortical tissue].'),f('size','Node short axis',f'The {side} level {level} node measures __ mm in short axis.',parents=['suspicious'])]))

rows = report('ra.carotid-obstruction',['differentiating-carotid-pathology'])
protocol(rows,['CT angiography','contrast-enhanced MR angiography','non-contrast MR angiography','carotid duplex ultrasound'])
for side in ['right','left']:
    for segment in ['common carotid artery','carotid bulb','proximal cervical internal carotid artery','distal cervical internal carotid artery','external carotid origin']:
        name=side+' '+segment
        rows.append(row(slug(name),name.title(),side.title()+' carotid system',f'The {name} is patent without a focal stenosis on the acquired study.',[
            f('plaque','Plaque',f'The {name} contains [calcified / non-calcified / mixed] plaque.'),
            f('stenosis','Lumen reduction',f'The {name} has [mild / moderate / severe] luminal narrowing.',exclusive='lumen'),
            f('occlusion','Occlusion',f'The {name} is occluded.',exclusive='lumen'),
            f('ulcer','Plaque surface',f'The {name} plaque surface is [smooth / irregular / ulcerated].',parents=['plaque']),
            f('dissection','Dissection features',f'The {name} shows [an intimal flap / eccentric mural thickening / a tapered flame-shaped stenosis / a dissecting pseudoaneurysm].'),
            f('thrombus','Intraluminal thrombus',f'There is an intraluminal filling defect in the {name} [attached to the wall / surrounded by contrast at its distal tip].')]))
    rows.extend([
        row(side+'-nascet',side.title()+' ICA stenosis assessment',side.title()+' carotid quantification',None,[
            f('category','NASCET category',f'Using a normal distal ICA reference, the {side} cervical ICA stenosis is [less than 50% / 50–69% / 70–99% without distal collapse].',exclusive='stenosis-type'),
            f('near','Near occlusion',f'The {side} cervical ICA shows near occlusion [with full distal collapse / without full distal collapse]. A conventional NASCET percentage is not assigned.',exclusive='stenosis-type'),
            f('occluded','Occluded ICA',f'The {side} cervical ICA is completely occluded.',exclusive='stenosis-type'),
            f('residual','Residual lumen',f'The minimum residual {side} ICA lumen is __ mm and the normal distal reference lumen is __ mm.',parents=['category']),
            f('web','Carotid web',f'There is a shelf-like defect along the posterior {side} carotid bulb suspicious for a carotid web.')],skip=True),
        row(side+'-duplex',side.title()+' duplex measurements',side.title()+' carotid quantification',None,[f('ica-velocity','ICA velocities',f'The sampled {side} ICA peak systolic velocity is __ cm/s and end-diastolic velocity is __ cm/s.'),f('cca-velocity','CCA velocity',f'The sampled {side} CCA peak systolic velocity is __ cm/s.'),f('flow','ICA waveform',f'The {side} ICA waveform shows [normal low-resistance flow / reduced diastolic flow / a high-resistance pattern / no detectable flow].')],skip=True),
        row(side+'-intracranial-ica',side.title()+' intracranial ICA', 'Distal circulation',f'The imaged {side} intracranial ICA is patent.',[f('occlusion','Distal ICA occlusion',f'The {side} intracranial ICA is occluded in the [petrous / cavernous / supraclinoid / terminus] segment.'),f('tandem','Tandem occlusion',f'There is an associated {side} [M1 / proximal M2 / A1] occlusion.')],skip=True),
        row(side+'-vertebral',side.title()+' vertebral artery','Vertebrobasilar circulation',f'The imaged {side} vertebral artery is patent.',[f('stenosis','Vertebral disease',f'The {side} vertebral artery has [origin stenosis / focal dissection / occlusion / hypoplasia].'),f('direction','Duplex flow direction',f'On duplex the {side} vertebral flow is [antegrade / bidirectional / retrograde].')],skip=True)
    ])
rows.append(row('arch','Aortic arch / great-vessel origins','Proximal circulation',None,[f('configuration','Arch configuration','The acquired angiogram shows [standard three-vessel arch branching / a shared brachiocephalic-left common carotid origin / a direct left vertebral origin / an aberrant right subclavian artery].'),f('disease','Origin disease','There is [no focal / mild / moderate / severe] stenosis at the [brachiocephalic / left common carotid / left subclavian] origin.')],skip=True))
rows = report('ra.mri-sella',['sella-turcica-and-parasellar-region','69485'])
protocol(rows,['dedicated pituitary MRI without contrast','dedicated pituitary MRI before and after contrast','dedicated pituitary MRI with dynamic contrast sequences'])
rows.extend([
    row('anterior-gland','Anterior pituitary','Pituitary gland','No focal lesion is identified in the anterior pituitary on the acquired images.',[f('height','Gland height','The pituitary gland measures __ mm craniocaudally.'),f('enlarge','Diffuse enlargement','There is [symmetric / asymmetric] diffuse pituitary enlargement.'),f('empty','Empty sella','There is [partial / complete] CSF filling of the sella with flattening of the gland.'),f('enhance','Gland enhancement','On post-contrast imaging the gland enhances [homogeneously / heterogeneously].')]),
    row('posterior-gland','Posterior pituitary','Pituitary gland','The posterior pituitary T1 bright spot is present in the expected position.',[f('absent','Bright spot absent','The posterior pituitary T1 bright spot is not identified.'),f('ectopic','Ectopic bright spot','The posterior pituitary bright spot is ectopic at the [median eminence / proximal infundibulum].')]),
    row('stalk','Pituitary stalk','Suprasellar structures','The pituitary stalk is midline and not thickened.',[f('deviation','Stalk deviation','The pituitary stalk is deviated [rightward / leftward].'),f('thick','Stalk thickening','The stalk is [smoothly / nodularly] thickened.'),f('diameter','Stalk measurement','The stalk measures __ mm in transverse diameter.')]),
    row('optic-chiasm','Optic chiasm','Suprasellar structures','The optic chiasm is not compressed and has normal signal.',[f('contact','Chiasmal relationship','The lesion [abuts / elevates / compresses] the optic chiasm.'),f('signal','Chiasmal signal','The chiasm has [focal / diffuse] T2 hyperintensity.')]),
    row('hypothalamus','Hypothalamus','Suprasellar structures','No focal hypothalamic lesion is identified.',[f('lesion','Hypothalamic lesion','There is a [solid / cystic / mixed solid-cystic] hypothalamic lesion.')]),
    row('third-ventricle','Third ventricle','Suprasellar structures','The third ventricular floor is not distorted.',[f('extension','Third ventricular involvement','The lesion [elevates the floor of / extends into / obstructs] the third ventricle.')]),
    row('sella-floor','Sellar floor / clivus','Bony and inferior extension','No focal marrow-replacing lesion is identified in the visualised clivus.',[f('floor','Sellar floor','There is [sellar expansion / inferior sellar floor displacement / suspected sellar floor breach].'),f('clivus','Clival involvement','There is [focal / diffuse] clival marrow replacement.'),f('sphenoid','Sphenoid extension','The lesion extends into the sphenoid sinus.')])
])
for side in ['right','left']:
    rows.extend([
        row(side+'-cavernous-sinus',side.title()+' cavernous sinus','Parasellar structures',f'The {side} cavernous sinus is not expanded.',[f('extension','Cavernous sinus extension',f'The sellar lesion extends into the {side} cavernous sinus with [less than half / at least half / complete] encasement of the cavernous carotid.'),f('margin','Carotid tangent relationship',f'The {side} lesion margin lies [medial to the medial carotid tangent / between the medial tangent and intercarotid line / between the intercarotid line and lateral tangent / lateral to the lateral tangent].',parents=['extension']),f('compartment','Superior / inferior extension',f'{side.title()} cavernous extension is predominantly [superior / inferior / both superior and inferior] to the carotid.',parents=['extension'])]),
        row(side+'-carotid',side.title()+' cavernous carotid','Parasellar structures',f'The {side} cavernous carotid flow void is preserved.',[f('vessel','Carotid relationship',f'The {side} cavernous carotid is [displaced / narrowed / encased without narrowing].'),f('vascular-lesion','Vascular lesion concern',f'A flow-related lesion adjacent to the {side} cavernous carotid requires dedicated angiographic correlation.')]),
        row(side+'-optic-nerve',side.title()+' prechiasmatic optic nerve','Suprasellar structures',f'The {side} prechiasmatic optic nerve is not compressed.',[f('compression','Optic nerve compression',f'The {side} prechiasmatic optic nerve is [displaced / compressed] by the lesion.')])
    ])
rows.append(row('sellar-lesion','Sellar / parasellar lesion','Lesion detail','No focal sellar or parasellar lesion is identified on the acquired images.',[
    f('lesion','Lesion centre','A lesion is centred in the [right pituitary / left pituitary / midline pituitary / suprasellar cistern / pituitary stalk / right parasellar compartment / left parasellar compartment].'),size(),
    f('composition','Composition','The lesion is [solid / cystic / mixed solid and cystic / predominantly haemorrhagic].',parents=['lesion']),
    f('signal','Signal','The lesion is [low / intermediate / high] on T1 and [low / intermediate / high] on T2.',parents=['lesion']),
    f('enhancement','Enhancement after contrast','The lesion shows [no enhancement / reduced early enhancement relative to gland / homogeneous enhancement / heterogeneous enhancement / peripheral enhancement] on acquired contrast images.',parents=['lesion']),
    f('cyst-nodule','Intracystic nodule','The cystic lesion contains an intracystic nodule.',parents=['lesion']),
    f('distance','Chiasmal clearance','The lesion lies __ mm below the optic chiasm.',parents=['lesion']),
    f('interval','Interval change','Compared with the available prior study the lesion is [unchanged / larger / smaller / newly visible].',parents=['lesion'])
],repeat=True))

rows = report('ra.venous-sinus-thrombosis',['cerebral-venous-thrombosis'])
protocol(rows,['CT venography','contrast-enhanced MR venography','non-contrast MR venography'])
for vessel in ['superior sagittal sinus','inferior sagittal sinus','straight sinus','vein of Galen','torcular','right transverse sinus','left transverse sinus','right sigmoid sinus','left sigmoid sinus','right jugular bulb','left jugular bulb','right internal cerebral vein','left internal cerebral vein','right basal vein of Rosenthal','left basal vein of Rosenthal']:
    rows.append(row(slug(vessel),vessel.title(),'Dural sinuses and deep veins',f'The {vessel} is patent on the acquired venographic images.',[
        f('thrombus','Thrombus',f'There is [non-occlusive / occlusive] thrombosis of the {vessel}.',exclusive='lumen'),
        f('uncertain','Nonvisualisation',f'The {vessel} is not fully visualised; [flow-related artefact / hypoplasia / incomplete coverage / thrombus] remains a consideration.',exclusive='lumen'),
        f('recanalisation','Partial recanalisation',f'The {vessel} contains [single / multiple] recanalised channels.',parents=['thrombus']),
        f('granulation','Arachnoid granulation',f'A focal rounded defect in the {vessel} has imaging characteristics of an arachnoid granulation.')]))
for side in ['right','left']:
    rows.append(row(side+'-cortical-veins',side.title()+' cortical veins','Superficial veins',f'No thrombosed {side} cortical vein is identified on the acquired images.',[
        f('thrombus','Cortical vein thrombus',f'There is thrombosis of a {side} [frontal cortical / parietal cortical / temporal cortical / vein of Labbé / vein of Trolard] vein.'),
        f('collaterals','Collateral veins',f'The {side} cortical collateral veins are prominent.')]))
rows.append(row('venous-injury','Venous parenchymal injury','Complications',None,[f('lesion','Venous injury','There is [right / left / bilateral] [frontal / parietal / temporal / occipital / thalamic / cerebellar] parenchymal injury in a venous distribution.'),f('blood','Haemorrhagic component','The venous injury is [non-haemorrhagic / petechially haemorrhagic / associated with a haematoma].',parents=['lesion']),f('diffusion','Diffusion','On acquired MRI there is [restricted / facilitated / mixed] diffusion within the affected region.',parents=['lesion']),size()],repeat=True,repeat_label='Injured region'))
mass_effect(rows)

rows = report('ra.intracranial-hypotension',['spontaneous-intracranial-hypotension'])
protocol(rows,['brain MRI without contrast','brain MRI before and after contrast','brain and whole-spine MRI'])
rows.extend([
    row('dura','Pachymeninges','Intracranial signs','No diffuse pachymeningeal enhancement is present on the acquired post-contrast images.',[f('enhancement','Dural enhancement','There is [smooth diffuse / focal / irregular] pachymeningeal thickening and enhancement.')],skip=True),
    row('venous-engorgement','Dural venous sinuses','Intracranial signs','The dural venous sinuses are not visibly engorged.',[f('engorgement','Venous engorgement','The dural venous sinuses are distended with convex margins.')]),
    row('pituitary','Pituitary gland','Intracranial signs','The pituitary gland is not enlarged.',[f('enlargement','Pituitary enlargement','The pituitary gland is enlarged with a convex superior margin.')]),
    row('suprasellar-cistern','Suprasellar cistern','Brain sagging','The suprasellar cistern remains open.',[f('effacement','Suprasellar narrowing','The suprasellar cistern is effaced.'),f('distance','Suprasellar distance','The suprasellar cistern measures __ mm.')]),
    row('prepontine-cistern','Prepontine cistern','Brain sagging','The prepontine cistern remains open.',[f('effacement','Prepontine narrowing','The prepontine cistern is narrowed with ventral pontine flattening.'),f('distance','Prepontine distance','The prepontine cistern measures __ mm.')]),
    row('mammillopontine','Mammillopontine distance','Brain sagging',None,[f('distance','Mammillopontine distance','The mammillopontine distance measures __ mm.')],skip=True),
    row('tonsils','Cerebellar tonsils','Brain sagging','The cerebellar tonsils do not descend below the foramen magnum.',[f('descent','Tonsillar descent','The cerebellar tonsils extend __ mm below the foramen magnum.'),f('shape','Tonsillar morphology','The descended tonsils are [rounded / pointed] with [preserved / crowded] surrounding CSF spaces.',parents=['descent'])]),
    row('midbrain','Midbrain position','Brain sagging','There is no visible downward displacement of the midbrain.',[f('sag','Midbrain sagging','There is caudal displacement of the midbrain with distortion of the diencephalic floor.')])
])
for side in ['right','left']:
    rows.append(row(side+'-subdural',side.title()+' subdural space','Associated collections',f'No {side} subdural collection is present.',[f('collection','Subdural collection',f'There is a {side} [CSF-like / haemorrhagic / mixed-signal] subdural collection.'),f('depth','Collection thickness',f'The {side} collection measures __ mm thick.',parents=['collection'])]))
for region in ['cervical','thoracic','lumbar']:
    rows.append(row(region+'-epidural',region.title()+' epidural space','Spinal screening',f'No extradural CSF collection is identified in the imaged {region} region.',[f('collection','Extradural CSF','There is a [ventral / dorsal / circumferential] extradural CSF collection in the {region} region.'),f('veins','Epidural veins','The {region} epidural venous plexus is engorged.')],skip=True))
rows.append(row('diverticulum','Spinal diverticulum / possible leak level','Spinal screening',None,[f('lesion','Diverticulum','A nerve-root sleeve diverticulum is present on the [right / left] at [C7–T1 / T1–T2 / T2–T3 / T3–T4 / T4–T5 / T5–T6 / T6–T7 / T7–T8 / T8–T9 / T9–T10 / T10–T11 / T11–T12 / T12–L1 / L1–L2 / L2–L3 / L3–L4 / L4–L5 / L5–S1].'),size(),f('relation','Collection relationship','The diverticulum is [adjacent to / separate from] the identified extradural collection.',parents=['lesion'])],repeat=True,repeat_label='Diverticulum'))
rows.append(row('leak-scope','Leak localisation','Interpretation scope',None,[f('scope','Localisation limit','Routine MRI [shows an extradural CSF collection but does not localise the active dural defect / does not show an extradural collection; this does not exclude a CSF-venous fistula].')],skip=True))
rows = report('ra.mri-cns-enhancement',['enhancement-patterns-in-cns-diseases'])
protocol(rows,['MRI before and after intravenous contrast','non-contrast MRI only'])
for part in ['right cerebral convexity','left cerebral convexity','falx','tentorium','skull base']:
    rows.append(row('dura-'+slug(part),part.title()+' dura','Pachymeninges',f'No abnormal dural thickening or enhancement is seen at the {part} on the acquired post-contrast images.',[
        f('enhance','Dural enhancement',f'The dura at the {part} shows [smooth diffuse / focal nodular / irregular] thickening and enhancement.'),f('thick','Dural thickness',f'The abnormal {part} dura measures __ mm thick.',parents=['enhance'])],skip=True))
for part in ['right cerebral sulci','left cerebral sulci','basal cisterns','cerebellar folia']:
    rows.append(row('lepto-'+slug(part),part.title(),'Leptomeninges',f'No abnormal leptomeningeal enhancement is seen in the {part} on the acquired post-contrast images.',[
        f('enhance','Leptomeningeal enhancement',f'There is [smooth / nodular / mixed smooth and nodular] leptomeningeal enhancement in the {part}.'),f('restriction','Restricted subarachnoid material',f'Material in the {part} shows restricted diffusion.')],skip=True))
for side in ['right','left']:
    rows.extend([
        row(side+'-ependymal',side.title()+' ependyma','Ventricles',f'No abnormal {side} ventricular ependymal enhancement is seen on the acquired post-contrast images.',[f('enhance','Ependymal enhancement',f'There is [smooth / nodular] enhancement along the {side} ventricular ependyma.'),f('debris','Ventricular debris',f'The {side} lateral ventricle contains dependent material with [restricted diffusion / no restricted diffusion / indeterminate diffusion].')],skip=True),
        row(side+'-gyral',side.title()+' cortex','Parenchymal patterns',f'No abnormal {side} cerebral cortical enhancement is seen on the acquired post-contrast images.',[f('enhance','Gyral enhancement',f'There is {side} [frontal / temporal / parietal / occipital / insular] gyral enhancement.'),f('signal','Cortical signal',f'The enhancing {side} cortex has [T2 swelling / restricted diffusion / laminar T1 hyperintensity / associated tissue loss].',parents=['enhance'])],skip=True)
    ])
rows.append(row('enhancing-lesion','Enhancing parenchymal lesion','Focal lesions',None,[
    f('lesion','Lesion location','There is a [right / left / midline] [frontal / temporal / parietal / occipital / basal ganglia / thalamic / brainstem / cerebellar / callosal] enhancing lesion.'),
    f('pattern','Enhancement pattern','Enhancement is [solid homogeneous / solid heterogeneous / thin complete ring / thick irregular ring / open ring / punctate perivascular / radial perivascular].',parents=['lesion']),
    f('diffusion','Diffusion pattern','Restricted diffusion is present in the [centre / rim / solid portion / surrounding tissue] of the lesion.',parents=['lesion']),
    f('no-restriction','No diffusion restriction','The lesion shows no definite restricted diffusion.',parents=['lesion'],exclusive='diffusion'),
    f('oedema','Surrounding oedema','The lesion has [minimal / moderate / extensive] surrounding oedema.',parents=['lesion']),size()
],repeat=True))
mass_effect(rows)

rows = report('ra.mri-dementia',['dementia/update'])
protocol(rows,['non-contrast brain MRI','brain MRI with intravenous contrast'])
for side in ['right','left']:
    for region in ['frontal lobe','temporal pole','lateral temporal lobe','parietal lobe','precuneus','posterior cingulate','occipital lobe']:
        rows.append(row(slug(side+'-'+region),side.title()+' '+region,'Regional cortical volume',f'No disproportionate volume loss is seen in the {side} {region}.',[
            f('atrophy','Regional atrophy',f'There is [mild / moderate / severe] volume loss in the {side} {region}.'),f('scar','Established focal injury',f'There is established [cortical infarction / encephalomalacia] in the {side} {region}.')]))
    rows.append(row(side+'-hippocampus',side.title()+' hippocampus','Medial temporal structures',f'The {side} hippocampus has preserved volume.',[
        f('atrophy','Hippocampal atrophy',f'The {side} hippocampus shows [mild / moderate / severe] volume loss.'),
        f('mta','Visual MTA score',f'The manually assessed {side} medial temporal atrophy score is [0 / 1 / 2 / 3 / 4].'),
        f('signal','Hippocampal signal',f'The {side} hippocampus has [T2 hyperintensity / restricted diffusion / focal swelling].')]))
    for name in ['thalamus','basal ganglia','deep frontal white matter','deep parietal white matter']:
        rows.append(row(slug(side+'-'+name),side.title()+' '+name,'Vascular burden',f'No focal ischaemic injury is seen in the {side} {name}.',[
            f('lacunes','Lacunes',f'There are [single / multiple] established lacunes in the {side} {name}.'),f('acute','Acute ischaemia',f'There is a focus of restricted diffusion with low ADC in the {side} {name}.')]))
rows.extend([
    row('white-matter','White matter hyperintensities','Vascular burden','No significant white matter hyperintensity is present.',[f('burden','White matter burden','There are [punctate / early confluent / confluent] deep white matter hyperintensities.'),f('fazekas','Visual Fazekas score','The manually assessed Fazekas score is [0 / 1 / 2 / 3].'),f('distribution','Distribution','White matter changes are predominantly [periventricular / deep / anterior temporal / external capsular / diffuse].')]),
    row('microbleeds','Microbleeds and superficial siderosis','Haemorrhagic burden','No microbleeds or superficial siderosis are seen on the acquired susceptibility-sensitive sequence.',[f('microbleeds','Microbleeds','Microbleeds have a [strictly lobar / deep / infratentorial / mixed lobar and deep] distribution.'),f('count','Microbleed count','There are [one / two to four / five to ten / more than ten / innumerable] microbleeds.',parents=['microbleeds']),f('siderosis','Cortical superficial siderosis','There is [focal / disseminated] cortical superficial siderosis in the [right / left / bilateral] cerebral hemispheres.')],skip=True),
    row('ventricular-pattern','Ventricular and sulcal pattern','CSF spaces','Ventricular size is proportionate to the cerebral sulcal spaces.',[f('disproportion','Disproportionate ventriculomegaly','The ventricles are enlarged out of proportion to high-convexity sulcal size.'),f('desh','DESH features','There is high-convexity sulcal crowding with enlarged sylvian fissures.'),f('callosal-angle','Callosal angle','The measured callosal angle is __ degrees.'),f('evans','Frontal horn dimensions','The frontal horn width is __ mm and the maximal inner skull diameter on the same axial plane is __ mm.')]),
    row('posterior-fossa','Brainstem and cerebellum','Regional volume','No disproportionate brainstem or cerebellar atrophy is identified.',[f('atrophy','Regional atrophy','There is disproportionate atrophy of the [midbrain / pons / cerebellar hemispheres / cerebellar vermis].')]),
    row('diffusion','Other diffusion pattern','Additional findings','No other restricted diffusion is seen.',[f('ribbon','Cortical ribbon pattern','There is cortical ribbon-like restricted diffusion in the [right / left / bilateral] [frontal / parietal / temporal / occipital] lobes.'),f('striatum','Striatal pattern','There is restricted diffusion in the [right / left / bilateral] caudate and putamen.')]),
    row('comparison','Comparison','Follow-up',None,[f('change','Interval change','Compared with the available prior MRI there is [no appreciable progression / progression of regional atrophy / increased vascular lesion burden].')],skip=True)
])

rows = report('ra.mri-epilepsy',['epilepsy/role-of-mri','ilae.org'])
protocol(rows,['dedicated epilepsy brain MRI','routine brain MRI'],[f('sequences','Protocol components','Acquired epilepsy sequences include [three-dimensional T1 and FLAIR with high-resolution coronal T2 perpendicular to the hippocampi / incomplete dedicated epilepsy sequences].')])
for side in ['right','left']:
    rows.extend([
        row(side+'-hippocampus',side.title()+' hippocampus','Mesial temporal lobes',f'The {side} hippocampus has preserved volume, internal architecture and T2 signal.',[f('atrophy','Volume loss',f'The {side} hippocampus is [mildly / markedly] atrophic.'),f('t2','T2 hyperintensity',f'The {side} hippocampus has [focal / diffuse] T2 hyperintensity.'),f('architecture','Internal architecture',f'The {side} hippocampal internal architecture is indistinct.'),f('swelling','Swelling',f'The {side} hippocampus is swollen [with / without] restricted diffusion.'),f('rotation','Incomplete inversion',f'The {side} hippocampus has incomplete inversion with rounded morphology and a vertically oriented collateral sulcus.')]),
        row(side+'-amygdala',side.title()+' amygdala','Mesial temporal lobes',f'The {side} amygdala is not enlarged and has normal signal.',[f('enlargement','Amygdala enlargement',f'The {side} amygdala is enlarged with [normal / increased] T2 signal.'),f('lesion','Focal lesion',f'There is a focal lesion in the {side} amygdala.')]),
        row(side+'-fornix',side.title()+' fornix / mammillary body','Mesial temporal lobes',f'The {side} fornix and mammillary body have preserved volume.',[f('atrophy','Associated atrophy',f'The {side} [fornix / mammillary body / fornix and mammillary body] is reduced in volume.')])
    ])
    for region in ['frontal','parietal','temporal','occipital','insular']:
        rows.append(row(side+'-'+region+'-cortex',side.title()+' '+region+' cortex','Cortical architecture',f'No focal cortical malformation is identified in the {side} {region} region.',[
            f('dysplasia','Dysplasia features',f'The {side} {region} cortex shows [cortical thickening / grey-white junction blurring / a transmantle T2 band / abnormal sulcation].'),
            f('polymicrogyria','Polymicrogyria',f'There is [focal / extensive] polymicrogyria in the {side} {region} region.'),
            f('scar','Gliotic scar',f'There is {side} {region} [cortical gliosis / ulegyria / encephalomalacia].'),
            f('encephalocele','Encephalocele',f'There is a {side} {region} encephalocele.')]))
    rows.append(row(side+'-heterotopia',side.title()+' neuronal heterotopia','Developmental lesions',f'No grey matter heterotopia is seen in the {side} cerebral hemisphere.',[f('heterotopia','Heterotopia',f'There is {side} [periventricular nodular / subcortical nodular / band] heterotopia.')]))
rows.append(row('epilepsy-lesion','Additional epileptogenic lesion','Focal lesions',None,[
    f('lesion','Lesion','A [right / left / midline] [frontal / temporal / parietal / occipital / hypothalamic] lesion has imaging features of [a cavernous malformation / a cortically based low-grade tumour / a hypothalamic hamartoma / a focal vascular malformation].'),
    size(),f('features','Lesion features','The lesion is [multicystic / solid / haemorrhagic / calcified on correlated CT] with [minimal / moderate / marked] surrounding signal change.',parents=['lesion']),f('enhance','Enhancement after contrast','The lesion shows [no / faint / avid / heterogeneous] enhancement on the acquired post-contrast images.',parents=['lesion'])
],repeat=True))
mass_effect(rows)

rows = report('ra.intracranial-haemorrhage',['non-traumatic-intracranial-hemorrhage'])
protocol(rows,['non-contrast CT','CT with angiography','MRI','MRI with angiography','CT with venography','MRI with venography'])
for side in ['right','left']:
    for region in ['frontal lobe','parietal lobe','temporal lobe','occipital lobe','basal ganglia','thalamus','cerebellar hemisphere']:
        rows.append(row(slug(side+'-'+region),side.title()+' '+region,'Parenchymal haemorrhage',f'No haemorrhage is seen in the {side} {region} on the acquired images.',[
            f('bleed','Haematoma',f'There is a {side} {region} haematoma with [acute / mixed-age / chronic] blood products.'),
            f('size','Haematoma dimensions',f'The {side} {region} haematoma measures __ × __ × __ mm.',parents=['bleed']),
            f('oedema','Perihaematomal oedema',f'There is [mild / moderate / extensive] oedema around the {side} {region} haematoma.',parents=['bleed'])]))
for site in ['pons','midbrain','medulla','corpus callosum','intraventricular compartment','basal cisterns','right cerebral convexity subarachnoid space','left cerebral convexity subarachnoid space','right subdural space','left subdural space']:
    rows.append(row(slug(site),site.title(),'Additional haemorrhage compartments',f'No haemorrhage is identified in the {site}.',[f('blood','Haemorrhage',f'There is [small-volume / moderate / extensive] haemorrhage in the {site}.')]))
rows.extend([
    row('microhaemorrhage','Microbleeds / siderosis','MRI susceptibility',None,[f('micro','Microbleed distribution','On susceptibility-sensitive MRI microbleeds are [strictly lobar / deep / infratentorial / mixed lobar and deep].'),f('siderosis','Superficial siderosis','On susceptibility-sensitive MRI there is [focal / disseminated] cortical superficial siderosis.'),f('cavernoma','Cavernous malformation pattern','A lesion has a reticulated mixed-signal core and a peripheral haemosiderin rim.')],skip=True),
    row('underlying-lesion','Underlying vascular or enhancing lesion','Additional sequences',None,[f('angiogram','Angiographic finding','Acquired angiography demonstrates [no definite culprit vascular lesion / an aneurysm / an arteriovenous malformation / abnormal vessels suspicious for a fistula / an indeterminate vascular abnormality].'),f('venogram','Venographic finding','Acquired venography demonstrates [no thrombosis / dural sinus thrombosis / cortical vein thrombosis / deep venous thrombosis].'),f('enhancement','Enhancement','Acquired post-contrast images show [no discrete underlying enhancing mass / a nodular enhancing component / irregular enhancement requiring follow-up].')],skip=True),
    row('expansion-sign','Contrast extravasation','CT angiography',None,[f('spot','CTA spot sign','Within the haematoma CTA shows [no contrast focus / a focus of contrast pooling suspicious for active extravasation].')],skip=True)
])
mass_effect(rows)

rows = report('ra.mri-ms',['diagnosis-and-differential-diagnosis-3-1','S1474-4422'])
protocol(rows,['brain MRI','brain and cervical cord MRI','brain and whole-cord MRI','spinal cord MRI'],[f('contrast','Contrast acquisition','Post-contrast sequences were [acquired / not acquired].')])
for side in ['right','left']:
    for site in ['frontal periventricular white matter','temporal periventricular white matter','parietal periventricular white matter','occipital periventricular white matter','frontal juxtacortical white matter','temporal juxtacortical white matter','parietal juxtacortical white matter','occipital juxtacortical white matter','cerebellar white matter','middle cerebellar peduncle']:
        rows.append(row(slug(side+'-'+site),side.title()+' '+site,'Brain lesion distribution',f'No focal T2 lesion is seen in the {side} {site}.',[
            f('lesions','T2 lesions',f'There are [single / few / multiple / confluent] T2 lesions in the {side} {site}.'),f('morphology','Lesion morphology',f'The {side} {site} lesions are [ovoid / punctate / linear / poorly marginated].',parents=['lesions']),f('new','Interval change',f'Compared with the available prior study the {side} {site} lesions are [unchanged / increased in number / increased in size / decreased in conspicuity].',parents=['lesions'])]))
for site in ['callososeptal interface','corpus callosum body','corpus callosum splenium','midbrain','pons','medulla']:
    rows.append(row(slug(site),site.title(),'Midline and infratentorial lesions',f'No focal T2 lesion is seen in the {site}.',[f('lesions','T2 lesions',f'There are [single / multiple] T2 lesions in the {site}.'),f('location','Axial location',f'The {site} lesion is [central / peripheral / right-sided / left-sided].',parents=['lesions'])]))
for side in ['right','left']:
    rows.append(row(side+'-optic-nerve',side.title()+' optic nerve','Additional dedicated coverage',f'No focal abnormality is seen in the {side} optic nerve on the dedicated acquired sequences.',[f('signal','Optic nerve signal',f'The {side} optic nerve has [focal / longitudinally extensive] T2 hyperintensity.'),f('enhance','Optic nerve enhancement',f'The {side} optic nerve enhances on acquired post-contrast images.')],skip=True))
for region in ['cervical','thoracic','conus']:
    rows.append(row(region+'-cord',region.title()+' cord','Additional dedicated coverage',f'No focal signal abnormality is seen in the acquired {region} cord images.',[f('lesion','Cord lesion',f'There are [single / multiple] T2 lesions in the {region} cord.'),f('distribution','Cord distribution',f'The {region} cord lesion is [dorsal / lateral / central / diffuse] and extends over [less than two / two to three / more than three] vertebral segments.',parents=['lesion']),f('atrophy','Cord atrophy',f'There is focal {region} cord atrophy.')],skip=True))
rows.append(row('ms-lesion','Target lesion','Lesion detail',None,[f('lesion','Target localisation','A target lesion is located in the [right periventricular / left periventricular / right cortical-juxtacortical / left cortical-juxtacortical / infratentorial / cervical cord / thoracic cord / optic nerve] compartment.'),size(),f('enhance','Enhancement after contrast','The target lesion shows [no / nodular / incomplete-ring / complete-ring] enhancement on acquired post-contrast images.',parents=['lesion']),f('central-vein','Central vein sign','The acquired susceptibility protocol shows [a central vein / no definite central vein / an indeterminate central vein] within this lesion.',parents=['lesion']),f('rim','Paramagnetic rim','The lesion has [a definite / no definite / an indeterminate] paramagnetic rim on the acquired susceptibility protocol.',parents=['lesion']),f('t1','T1 signal','The target lesion is [isointense / persistently hypointense] on T1 imaging.',parents=['lesion'])],repeat=True))
rows.append(row('comparison','Comparison and interpretation scope','Follow-up',None,[f('comparison','Comparison','There are [no new T2 lesions / new T2 lesions / enlarging T2 lesions / new and enlarging T2 lesions] compared with the available prior study.'),f('scope','Diagnostic scope','The reported lesion distribution requires clinical and laboratory correlation; imaging alone has not been used to assign a diagnosis of multiple sclerosis.')],skip=True))

rows = report('ra.brain-anatomy',['brain/anatomy','vascular-territories'])
for side in ['right','left']:
    for name in ['precentral gyrus','postcentral gyrus','superior frontal gyrus','middle frontal gyrus','inferior frontal gyrus','superior parietal lobule','inferior parietal lobule','superior temporal gyrus','middle temporal gyrus','inferior temporal gyrus','insula','cingulate gyrus','precuneus','cuneus','lingual gyrus','hippocampus','amygdala','caudate nucleus','putamen','globus pallidus','thalamus','anterior limb of internal capsule','genu of internal capsule','posterior limb of internal capsule','cerebellar hemisphere']:
        rows.append(row(slug(side+'-'+name),side.title()+' '+name,'Anatomical localisation · '+side,None,[f('localise','Localise finding',f'The imaged abnormality involves the {side} {name}.'),f('relation','Relationship',f'The {side} {name} is [displaced / compressed / expanded / atrophic / directly infiltrated] by the observed process.')],skip=True))
for territory in ['ACA','MCA superior division','MCA inferior division','PCA','anterior choroidal','lenticulostriate','PICA','AICA','superior cerebellar','ACA–MCA borderzone','MCA–PCA borderzone','internal borderzone']:
    rows.append(row(slug(territory),territory+' territory','Vascular localisation',None,[f('localise','Territory relation',f'The distribution is [right / left / bilateral] and follows the {territory} territory.')],skip=True))

rows = report('ra.mri-brain-tumours',['systematic-approach'])
protocol(rows,['MRI without contrast','MRI before and after intravenous contrast'])
brain_regions(rows)
rows.append(row('tumour','Focal intracranial lesion','Lesion characterisation',None,[
    f('lesion','Location','A [right / left / midline] [frontal / parietal / temporal / occipital / insular / basal ganglia / thalamic / callosal / brainstem / cerebellar / sellar / pineal / cerebellopontine angle / intraventricular / skull-base] lesion is present.'),
    f('compartment','Compartment','The lesion is [intra-axial / extra-axial / intraventricular / centred in the meninges / centred in the skull base].',parents=['lesion']),size(),
    f('t1','T1 signal','The lesion is predominantly [hypointense / isointense / hyperintense / mixed signal] on T1 imaging.',parents=['lesion']),
    f('t2','T2 signal','The lesion is predominantly [hypointense / isointense / hyperintense / mixed signal] on T2 imaging.',parents=['lesion']),
    f('composition','Composition','The lesion is [solid / predominantly cystic with a mural nodule / mixed solid and cystic / necrotic / fat-containing].',parents=['lesion']),
    f('enhancement','Post-contrast pattern','On post-contrast imaging the lesion has [no enhancement / homogeneous enhancement / heterogeneous enhancement / smooth peripheral enhancement / irregular peripheral enhancement / open-ring enhancement / nodular enhancement].',parents=['lesion']),
    f('diffusion','Diffusion','The lesion demonstrates [restricted diffusion with low ADC / facilitated diffusion / mixed diffusion characteristics / no definite diffusion abnormality].',parents=['lesion']),
    f('blood','Susceptibility','There are [blood products / mineralisation-like susceptibility foci / prominent intralesional vessels] within the lesion.',parents=['lesion']),
    f('oedema','Perilesional signal','There is [minimal / moderate / extensive] surrounding T2 hyperintensity involving [white matter only / cortex and white matter].',parents=['lesion']),
    f('extension','Local extension','The lesion extends into the [corpus callosum / ependymal surface / leptomeninges / dura / calvarium / adjacent ventricle].',parents=['lesion']),
    f('perfusion','Perfusion','On the acquired perfusion study the lesion has [increased / intermediate / low] relative perfusion.',parents=['lesion']),
    f('spectroscopy','Spectroscopy','The acquired spectrum shows [elevated choline relative to creatine / reduced NAA / a lipid-lactate peak / technically indeterminate metabolites].',parents=['lesion'])
],repeat=True))
rows.extend([
    row('dural-spread','Dural spread','Tumour extension','No abnormal focal dural enhancement is seen on the acquired post-contrast images.',[f('dural','Dural disease','There is [focal / multifocal / diffuse] abnormal dural enhancement.')],skip=True),
    row('leptomeningeal-spread','Leptomeningeal spread','Tumour extension','No abnormal leptomeningeal enhancement is seen on the acquired post-contrast images.',[f('spread','Leptomeningeal disease','There is [linear / nodular] leptomeningeal enhancement in the [supratentorial / infratentorial / supratentorial and infratentorial] compartment.')],skip=True),
    row('treatment','Treatment bed','Follow-up',None,[f('resection','Resection cavity','A [right / left / midline] [frontal / temporal / parietal / occipital / cerebellar] resection cavity is present.'),f('margin','Resection margin','The resection margin shows [no nodular enhancement / thin smooth enhancement / nodular enhancement / restricted diffusion] on the relevant acquired sequences.',parents=['resection']),f('change','Interval lesion change','Compared with the available prior examination the lesion is [smaller / unchanged / larger / newly visible].')],skip=True)
])
mass_effect(rows)

# Complete the level-specific exit pathways in the myelopathy examination.
# These remain coverage-dependent so a cervical acquisition cannot auto-assert
# a normal thoracic foramen.
myelopathy=OUT['investigations']['ra.mri-myelopathy']['sections']
CURRENT_REFS=[source('myelopathy')]
for level,root in [('C2–C3','C3'),('C3–C4','C4'),('C4–C5','C5'),('C5–C6','C6'),('C6–C7','C7'),('C7–T1','C8')]+[(f'T{i}–T{i+1}',f'T{i}') for i in range(1,12)]+[('T12–L1','T12')]:
    for side in ['right','left']:
        myelopathy.append(row(slug(level+'-'+side+'-foramen'),side.title()+' '+level+' foramen / '+root+' root','Foramina by level',f'The {side} {level} foramen is patent without exiting {root} root compression on the acquired images.',[
            f('stenosis','Foraminal stenosis',f'The {side} {level} foramen has [mild / moderate / severe] stenosis.'),
            f('root','Root effect',f'The exiting {side} {root} root is [contacted / displaced / compressed].'),
            f('lesion','Foraminal lesion',f'A [disc-osteophyte complex / soft disc herniation / nerve-sheath lesion / perineural cyst] occupies the {side} {level} foramen.')],skip=True))

# Fontanel assessment remains explicit because normal closure is age-dependent.
CURRENT_REFS=[source('craniosynosthosis')]
for name in ['anterior','posterior']:
    OUT['investigations']['ra.craniosynostosis']['sections'].append(row(name+'-fontanelle',name.title()+' fontanelle','Cranial sutures',None,[f('status','Fontanel status',f'The {name} fontanelle is [open / small / closed] on the acquired examination.')],skip=True))
for identifier in ['ra.mri-neck-spaces','ra.head-neck-malignancy','ra.paediatric-neck-masses']:
    for item in OUT['investigations'][identifier]['sections']:
        if '-node-vii' in item['id']:
            item['exclude_from_bulk_normal']=True

# Migrated fragments require an actual extrusion or sequestration, rather than
# merely any herniation choice (which also included a contained protrusion).
for item in OUT['investigations']['ra.mri-lumbar-disc']['sections']:
    old=next((v for v in item['findings'] if v['id']=='herniation'),None)
    if old:
        index=item['findings'].index(old)
        options=[]
        for identifier,label,noun in [('protrusion','Disc protrusion','protrusion'),('extrusion','Disc extrusion','extrusion'),('sequestration','Sequestered fragment','sequestration')]:
            text=old['text'].replace('[protrusion / extrusion / sequestration]',noun)
            options.append(f(identifier,label,text,exclusive='focal-herniation'))
        item['findings'][index:index+1]=options
        next(v for v in item['findings'] if v['id']=='migration')['requires_any']=['extrusion','sequestration']

# Explicit lesion extension elsewhere in the sella report excludes the global
# negative lesion assertion; measurements and non-focal variants do not.
sellar_positive_findings={
    'stalk':{'thick'},'optic-chiasm':{'contact','signal'},'hypothalamus':{'lesion'},'third-ventricle':{'extension'},
    'sella-floor':{'clivus','sphenoid'},'right-cavernous-sinus':{'extension'},'left-cavernous-sinus':{'extension'},
    'right-carotid':{'vessel','vascular-lesion'},'left-carotid':{'vessel','vascular-lesion'},
    'right-optic-nerve':{'compression'},'left-optic-nerve':{'compression'},
}
for item in OUT['investigations']['ra.mri-sella']['sections']:
    for finding in item['findings']:
        if finding['id'] in sellar_positive_findings.get(item['id'],set()):
            finding['invalidates_normal']=list(dict.fromkeys(finding.get('invalidates_normal',[])+['sellar-lesion']))

# Explicit controls preserve calculator applicability without entering clinical
# assertions into the report text. The source findings remain selectable.
patient_controls = [
    f('adult', 'Adult patient', 'The patient is an adult.', exclusive='patient-group'),
    f('child', 'Paediatric patient', 'The patient is a child.', exclusive='patient-group'),
]
for item in patient_controls:
    item['report'] = False
thyroid = OUT['investigations']['ra.ultrasound-thyroid']
thyroid['sections'].insert(1, row('patient-group','Patient group','Calculation applicability',None,patient_controls,
    refs=[source('Reporting-and-Data-Systems/TI-RADS')],skip=True))

# Prevent dependent statements about aspiration timing when no airway entry was
# selected. Distinct findings keep the condition explicit in the shared engine.
trial = next(r for r in OUT['investigations']['ra.swallowing']['sections'] if r['id']=='swallow-trial')
airway = next(f for f in trial['findings'] if f['id']=='airway')
airway['text'] = 'During this trial there is [supraglottic penetration / penetration reaching the vocal folds / aspiration below the vocal folds].'
airway['exclusive_group'] = 'airway-entry'
trial['findings'].append(f('no-airway-entry','No airway entry','There is no airway entry during this trial.',parents=['trial'],exclusive='airway-entry'))
for r in OUT['investigations']['ra.mri-cns-enhancement']['sections']:
    if r['id']=='enhancing-lesion':
        next(f for f in r['findings'] if f['id']=='diffusion')['exclusive_group']='diffusion'

# Cross-row positive findings must not coexist with a broad regional normal.
# Conservative invalidation intentionally clears all potentially involved rows
# where a location is selected inside a repeated lesion, rather than silently
# assuming a normal in its containing compartment.
for investigation_id, repeated_id, ids in [
    ('ra.mri-myelopathy','cord-lesion',[r['id'] for r in OUT['investigations']['ra.mri-myelopathy']['sections'] if r['group']=='Cord by vertebral level' or r['id']=='conus']),
    ('ra.mri-ms','ms-lesion',[r['id'] for r in OUT['investigations']['ra.mri-ms']['sections'] if r['normal']]),
    ('ra.mri-sella','sellar-lesion',[r['id'] for r in OUT['investigations']['ra.mri-sella']['sections'] if r['id'] in ['anterior-gland','hypothalamus','stalk','right-cavernous-sinus','left-cavernous-sinus']]),
    ('ra.mri-trigeminal','trigeminal-lesion',[r['id'] for r in OUT['investigations']['ra.mri-trigeminal']['sections'] if r['normal'] and any(r['id'].endswith(suffix) for suffix in ['-nucleus','-cisternal','-meckel','-cavernous','-v2','-v3'])]),
    ('ra.mri-brain-tumours','tumour',[r['id'] for r in OUT['investigations']['ra.mri-brain-tumours']['sections'] if r['group']=='Brain parenchyma']),
    ('ra.mri-neck-spaces','neck-lesion',[r['id'] for r in OUT['investigations']['ra.mri-neck-spaces']['sections'] if r['group'] in ['Deep neck spaces','Midline and trans-spatial spread']]),
    ('ra.head-neck-malignancy','primary-lesion',[r['id'] for r in OUT['investigations']['ra.head-neck-malignancy']['sections'] if r['group']=='Mucosal primary sites']),
    ('ra.ct-mri-eye','orbital-lesion',[r['id'] for r in OUT['investigations']['ra.ct-mri-eye']['sections'] if r['id'].endswith(('-vitreous','-intraconal','-extraconal','-lacrimal','-apex'))]),
    ('ra.mri-sinuses','sinonasal-lesion',[r['id'] for r in OUT['investigations']['ra.mri-sinuses']['sections'] if r['group']=='Paranasal sinuses' or r['id'].endswith('nasal-cavity')]),
]:
    target=next(r for r in OUT['investigations'][investigation_id]['sections'] if r['id']==repeated_id)
    next(f for f in target['findings'] if f['id']=='lesion')['invalidates_normal']=ids

# Make source input portable: only the authored output belongs to the runtime;
# the generator is a reproducible content-writing aid.
import sys
sys.path.insert(0,str(ROOT))
from tools.build_descriptor_reporting import compile_statement
for investigation_id, investigation in OUT['investigations'].items():
    row_ids={r['id'] for r in investigation['sections']}
    assert len(row_ids)==len(investigation['sections']), investigation_id
    for position, r in enumerate(investigation['sections']):
        assert r['source_ids'], (investigation_id,r['id'])
        local_ids={v['id'] for v in r['findings']}
        assert len(local_ids)==len(r['findings']), (investigation_id,r['id'])
        for value in r['findings']:
            assert all(p in local_ids and p!=value['id'] for p in value.get('requires_any',[])),(investigation_id,r['id'],value['id'])
            assert all(p in row_ids for p in value.get('invalidates_normal',[])),(investigation_id,r['id'],value['id'])
            compiled=compile_statement(value['text'],kind='finding',label=value['label'],source={'investigation_id':investigation_id,'step_index':position})
            assert not any(s['kind']=='context' for s in compiled['slots']), (investigation_id,r['id'],value['id'],compiled)
            overrides=value.setdefault('slot_overrides',{})
            for slot in compiled['slots']:
                if slot['kind']=='number':
                    overrides[slot['id']]={'minimum':0}
                    if slot.get('unit')=='%': overrides[slot['id']]['maximum']=100
                    if slot.get('unit')=='degrees': overrides[slot['id']]['maximum']=180
            if not overrides:value.pop('slot_overrides')
        if r['normal']:
            compiled=compile_statement(r['normal'],kind='normal',source={'investigation_id':investigation_id,'step_index':position})
            assert not compiled['slots'],(investigation_id,r['id'],compiled)
            lower=r['normal'].lower()
            # These assertions require an actual protocol component or view.
            if any(token in lower for token in ['post-contrast','angiogram','venographic','acquired ct','acquired mri','dedicated mri','reformatted ct','acquired frontal','posterior fossa views','cine assessment']):
                r['exclude_from_bulk_normal']=True
    OUT['coverage'].append({'investigation_id':investigation_id,'expected_anatomy_ids':[r['id'] for r in investigation['sections']]})
used={s for v in OUT['investigations'].values() for r in v['sections'] for s in r['source_ids']}
OUT['sources']=[s for s in OUT['sources'] if s['id'] in used]
assert set(OUT['investigations'])=={a['investigation_id'] for a in ASSIGNMENT}
(ROOT/'data/radiology/anatomic-neuro.json').write_text(json.dumps(OUT,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'investigations':len(OUT['investigations']),'rows':sum(len(i['sections']) for i in OUT['investigations'].values()),'findings':sum(len(r['findings']) for i in OUT['investigations'].values() for r in i['sections']),'repeatable_rows':sum(bool(r.get('repeatable')) for i in OUT['investigations'].values() for r in i['sections']),'sources':len(OUT['sources'])}))
