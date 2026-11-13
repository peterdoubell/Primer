"""House style for every report template, and Prism titles for every performed study.

House style (enforced by tests/test_report_style.py):
  Title      Modality and region first ("CT abdomen and pelvis with contrast", "MRI right knee",
             "Ultrasound thyroid"); radiographs end in "radiograph(s)"; fluoroscopy is named by
             the procedure; an indication or protocol follows a comma. One modality; titles unique.
  Technique  Every non-radiograph opens with the standard protocol of its own modality;
             options are variants of that modality only.
  Findings   Short sentence-case anatomical headings. The normal line is terse, present tense,
             UK spelling, full stops.
  Impression One normal summary line.
Run after examination_additions_20261112.py; this pass and its outputs are the source of truth.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'radiology'
TEMPLATES = DATA / 'report-templates'
ADDITIONS = DATA / 'anatomic-additions-20261112.json'
PRISM = DATA / 'prism-titles.json'

# ------------------------------------------------------------------ identities
RENAME = {
    'ct.brain': 'ct.angiogram-brain', 'mri.brain': 'mri.angiogram-brain',
    'ct.lower-limbs': 'ct.angiogram-lower-limbs', 'ct.upper-limb': 'ct.angiogram-upper-limb',
    'us.abdomen-acute': 'us.abdomen-pelvis-female', 'us.us-abdomen-acute': 'us.abdomen-pelvis-male',
    'dxa.dxa': 'dxa.bone-densitometry',
}
DROP = {'mri.neck': 'mri.angiogram-carotids'}  # duplicate of the carotid MRA split
PRACTICE_REMAP = {'CT angiogram of the neck vessels': 'ct.angiogram-carotids',
                  'MR angiogram of the neck vessels': 'mri.angiogram-carotids',
                  'CT sinuses': 'ct.sinuses', 'MRI orbits': 'mri.orbits'}
# Not performed studies (review worksheets) or teaching duplicates of a routine study:
# they stay in Primer but are not report templates for RadProof.
NOT_STUDIES = ['template:modalities-report', 'template:radiation-safety-report', 'template:ct-image-report',
               'template:mri-sequences-report', 'template:structured-reporting-report',
               'template:ultrasound-physics-report', 'ra.ct-contrast-protocols', 'ra.brain-anatomy',
               'mri.brain-anatomy', 'ra.paediatric-ultrasound-values', 'template:head-trauma-report',
               'template:msk-mri-report', 'template:fracture-description-report']
NO_OTHER_FINDINGS = {'template:modalities-report', 'template:radiation-safety-report', 'template:ct-image-report',
                     'template:mri-sequences-report', 'template:structured-reporting-report',
                     'template:ultrasound-physics-report', 'ra.ct-contrast-protocols'}

# ------------------------------------------------------------------ titles
TITLES = {
    'ra.ct-bowel-wall': 'CT abdomen and pelvis with contrast, bowel wall thickening',
    'ra.ct-bowel-obstruction': 'CT abdomen and pelvis with contrast, bowel obstruction',
    'ra.ct-peritoneum': 'CT abdomen and pelvis with contrast, peritoneum and mesentery',
    'ra.ct-peritoneal-carcinomatosis': 'CT chest, abdomen and pelvis with contrast, peritoneal disease',
    'ra.abdominal-wall-hernias': 'CT abdomen and pelvis, abdominal wall hernia',
    'ra.ct-bowel-ischaemia': 'CT angiogram abdomen and pelvis, mesenteric ischaemia',
    'ra.cardiac-masses': 'MRI heart, cardiac mass', 'ra.mri-cardiomyopathy': 'MRI heart, cardiomyopathy',
    'ct.cardiac-mass': 'CT heart, cardiac mass',
    'ra.mri-brain-tumours': 'MRI brain with contrast, tumour', 'ra.mri-cns-enhancement': 'MRI brain with contrast, enhancing lesion',
    'ra.ct-covid': 'CT chest without contrast, COVID-19', 'ra.thymus': 'CT chest with contrast, thymus',
    'ra.ct-mediastinum': 'CT chest with contrast', 'ra.paediatric-mediastinum': 'CT chest with contrast, paediatric mediastinal mass',
    'ra.ct-cardiovascular-pearls': 'CT chest, cardiovascular findings',
    'ra.paediatric-chest-ct': 'CT chest, paediatric', 'ra.tuberculosis': 'Chest radiographs, tuberculosis',
    'ra.renal-cysts-bosniak': 'CT kidneys, renal cyst protocol', 'ra.solid-renal-masses': 'CT kidneys, renal mass protocol',
    'ra.ultrasound-paediatric-scrotum': 'Ultrasound scrotum, paediatric acute scrotum',
    'us.scrotum-adult': 'Ultrasound scrotum',
    'ra.paediatric-cystic-abdominal-masses': 'Ultrasound abdomen, paediatric cystic mass',
    'ra.paediatric-solid-abdominal-masses': 'Ultrasound abdomen, paediatric solid mass',
    'mri.paediatric-abdomen-cystic': 'MRI abdomen, paediatric cystic mass',
    'mri.paediatric-abdomen-solid': 'MRI abdomen, paediatric solid mass',
    'ct.paediatric-abdomen-solid': 'CT abdomen with contrast, paediatric solid mass',
    'ra.paediatric-renal-tumours': 'CT abdomen with contrast, paediatric renal tumour',
    'ra.ct-traumatic-haemorrhage': 'CT brain, head injury', 'ra.intracranial-haemorrhage': 'CT brain and CT angiogram, haemorrhage',
    'ra.venous-sinus-thrombosis': 'CT venogram', 'mri.venogram': 'MR venogram',
    'mri.angiogram-carotids': 'MR angiogram neck vessels', 'ct.angiogram-carotids': 'CT angiogram neck vessels',
    'ra.mri-myelopathy': 'MRI cervical spine, myelopathy / MRI thoracic spine, myelopathy',
    'ra.thoracolumbar-fractures': 'CT thoracic and lumbar spine, fracture classification',
    'ra.thoracolumbar-injury': 'CT thoracic and lumbar spine, trauma',
    'ra.ct-pulmonary-nodules': 'CT chest, pulmonary nodule',
    'ra.liver-masses': 'MRI liver with contrast, focal lesion', 'ct.liver-mass': 'CT liver, multiphase, focal lesion',
    'ra.stress-fractures': 'MRI stress injury', 'ra.bone-tumours': 'MRI bone lesion with contrast',
    'ra.ultrasound-acute-abdomen': 'Ultrasound abdomen, acute pain',
    'ra.paediatric-neck-masses': 'Ultrasound neck, paediatric neck mass',
    'ra.cervical-lymph-nodes': 'Ultrasound neck, lymph nodes',
    'ra.neonatal-acute-abdomen': 'Abdominal radiograph, neonatal acute abdomen',
    'ra.necrotising-enterocolitis': 'Abdominal radiographs, necrotising enterocolitis',
    'ct.angiogram-head-neck-tinnitus': 'CT angiogram head and neck, pulsatile tinnitus',
    'ra.tinnitus': 'MRI internal auditory meati',
    'ct.neck-nodes': 'CT neck with contrast, lymph nodes',
    'ra.head-neck-malignancy': 'CT neck with contrast, cancer staging',
    'ra.ankle-fractures': 'Right ankle radiographs, trauma / Left ankle radiographs, trauma',
    'ra.wrist-fractures': 'Right wrist radiographs, trauma / Left wrist radiographs, trauma',
    'template:head-trauma-report': 'CT brain, head injury review worksheet',
}

# ------------------------------------------------------------------ technique of the right modality
TECHNIQUE = {
    'us.uterus-3d': 'Transvaginal 3D ultrasound of the uterus with a coronal reconstruction through the fundus.',
    'mri.brain-anatomy': 'MRI brain with T1, T2, FLAIR, diffusion and SWI.',
    'mri.paediatric-mediastinum': 'MRI chest with T1, T2, diffusion and post-contrast imaging, weight-based protocol.',
    'ct.angiogram-head-neck-tinnitus': 'CT angiogram from the aortic arch to the vertex with arterial and venous phase review and temporal bone reconstructions.',
    'ct.neck-nodes': 'CT neck from the skull base to the aortic arch with IV contrast.',
    'mri.paediatric-abdomen-cystic': 'MRI abdomen and pelvis with T2, T1, diffusion and post-contrast imaging, weight-based protocol.',
    'ct.paediatric-abdomen-solid': 'CT abdomen and pelvis with IV contrast, weight-based low-dose protocol.',
    'mri.paediatric-abdomen-solid': 'MRI abdomen and pelvis with T2, T1, diffusion and post-contrast imaging, weight-based protocol.',
    'mri.paediatric-renal-tumour': 'MRI abdomen with T2, T1, diffusion and post-contrast imaging, weight-based protocol.',
}

# Protocol lines state what was acquired, as a report does (not instructions).
TECHNIQUE.update({
    'ct.appendix': 'Portal venous phase CT abdomen and pelvis with IV contrast; coronal and sagittal reconstructions.',
    'ct.liver-mass': 'Non-contrast, late arterial, portal venous and delayed phase CT liver.',
    'ct.liver-lirads': 'Late arterial, portal venous and delayed phase CT liver.',
    'ct.liver-lirads-calculated': 'Late arterial, portal venous and delayed phase CT liver (LI-RADS v2018 technique).',
    'ct.oesophagus': 'Portal venous phase CT chest and upper abdomen with IV and oral water-soluble contrast.',
    'ct.cardiac-mass': 'ECG-gated CT heart with arterial and delayed phase IV contrast.',
    'ct.angiogram-carotids': 'CT angiogram from the aortic arch to the vertex with multiplanar and curved reconstructions.',
    'mri.angiogram-carotids': 'Contrast-enhanced MR angiogram from the aortic arch to the circle of Willis with time-of-flight of the bifurcations.',
    'mri.thymus': 'MRI thymus with T1, fat-suppressed T2, chemical-shift and diffusion-weighted imaging, and post-contrast T1.',
    'mri.renal-cyst': 'MRI kidneys with T2, fat-suppressed T1 and dynamic contrast-enhanced imaging with subtraction.',
    'mri.renal-mass': 'MRI kidneys with T2, chemical-shift T1, diffusion and dynamic contrast-enhanced imaging with subtraction.',
    'mri.adrenals': 'MRI adrenals with T2, chemical-shift T1 and diffusion-weighted imaging.',
    'mri.adnexal-mass': 'MRI pelvis with T2, T1 with and without fat suppression, diffusion and dynamic contrast-enhanced imaging.',
    'mri.brain-stroke': 'MRI brain with diffusion, FLAIR, SWI and time-of-flight MR angiography.',
    'mri.brain-haemorrhage': 'MRI brain with T1, T2, FLAIR, diffusion, SWI and time-of-flight MR angiography.',
    'mri.venogram': 'MRI brain with T1, T2, FLAIR, diffusion and SWI, and contrast-enhanced MR venography.',
    'mri.orbits': 'MRI orbits with thin-section T1 and fat-suppressed T2, diffusion and post-contrast fat-suppressed T1.',
    'ct.sinuses': 'Low-dose CT paranasal sinuses without contrast with coronal and sagittal reconstructions.',
    'mri.neck-tumour': 'MRI neck with T1, T2, diffusion and post-contrast fat-suppressed T1 from the skull base to the thoracic inlet.',
    'mri.thoracolumbar-trauma': 'MRI thoracic and lumbar spine with sagittal T1, T2 and STIR and axial T2.',
    'mri.cervical-spine-trauma': 'MRI cervical spine with sagittal T1, T2 and STIR, axial T2 and gradient echo.',
    'fl.barium-meal': 'Double-contrast barium meal with effervescent agent, and single-contrast compression views.',
    'dxa.bone-densitometry': 'DXA of the lumbar spine (L1 to L4) and both hips.',
    'fl.contrast-enema': 'Double-contrast barium enema after bowel preparation.',
    'ct.abdomen-multiphase': 'Non-contrast, late arterial, portal venous and delayed phase CT abdomen and pelvis.',
    'ct.angiogram-brain': 'CT angiogram of the intracranial arteries with MIP and 3D reconstructions.',
    'ct.angiogram-lower-limbs': 'CT angiogram from the renal arteries to the feet with MIP and curved reconstructions.',
    'ct.angiogram-upper-limb': 'CT angiogram from the aortic arch to the hand with MIP and curved reconstructions.',
    'ct.ankle-foot': 'CT ankle and foot without contrast with sagittal, coronal and 3D reconstructions.',
    'ct.calcium-score': 'Prospectively ECG-triggered non-contrast CT heart (Agatston protocol).',
    'ct.elbow': 'CT elbow without contrast with sagittal, coronal and 3D reconstructions.',
    'ct.facial-bones': 'CT facial bones without contrast with coronal, sagittal and 3D reconstructions.',
    'ct.oncology-staging': 'CT from the skull base to the pubic symphysis with IV contrast in the portal venous phase.',
    'ct.tmj': 'CT temporomandibular joints without contrast with oblique sagittal and coronal reconstructions.',
    'ct.trauma-panscan': 'Non-contrast CT brain and cervical spine, then CT chest, abdomen and pelvis with IV contrast in the arterial and portal venous phases.',
    'ct.guided-biopsy': 'CT-guided biopsy under local anaesthetic after informed consent.',
    'fl.lumbar-puncture': 'Fluoroscopy-guided lumbar puncture under local anaesthetic after informed consent.',
    'fl.hip-arthrogram': 'Fluoroscopy-guided hip injection of iodinated contrast and dilute gadolinium after informed consent.',
    'fl.hysterosalpingogram': 'Hysterosalpingogram with water-soluble contrast via a cervical catheter.',
    'fl.mcug': 'Micturating cystourethrogram with water-soluble contrast via a urethral catheter.',
    'mri.angiogram-brain': 'Time-of-flight MR angiogram of the circle of Willis with MIP reconstructions.',
    'mri.female-pelvis': 'MRI pelvis with multiplanar T2, T1 with and without fat suppression and diffusion-weighted imaging.',
    'mri.kidneys': 'MRI kidneys with T2, chemical-shift T1, diffusion and dynamic contrast-enhanced imaging.',
    'mri.whole-body': 'Whole-body MRI with T1, STIR and diffusion-weighted imaging, and sagittal whole-spine T1 and STIR.',
    'fl.urethrogram': 'Retrograde urethrogram with water-soluble contrast in the oblique position.',
    'fl.shoulder-arthrogram': 'Fluoroscopy-guided shoulder injection of iodinated contrast and dilute gadolinium after informed consent.',
    'mg.stereotactic-biopsy': 'Stereotactic vacuum-assisted breast biopsy under local anaesthetic after informed consent.',
    'fl.theatre': 'Intra-operative C-arm fluoroscopy acquired by the operating team.',
    'us.transcranial-doppler': 'Transcranial Doppler through the temporal, transorbital and suboccipital windows.',
    'us.abdomen-pelvis-female': 'Transabdominal ultrasound of the abdomen and pelvis.',
    'us.abdomen-pelvis-male': 'Transabdominal ultrasound of the abdomen and pelvis.',
    'us.abdominal-wall': 'Ultrasound of the abdominal wall and both groins at rest and with Valsalva.',
    'us.lower-limb-veins-bilateral': 'Compression and colour Doppler ultrasound of both legs from the common femoral to the calf veins.',
    'us.early-pregnancy': 'Transabdominal and transvaginal ultrasound.',
    'us.renal-doppler': 'Ultrasound kidneys with colour and spectral Doppler of the renal arteries.',
    'us.paracentesis': 'Ultrasound-guided paracentesis under local anaesthetic after informed consent.',
    'fl.contrast-swallow-leak': 'Water-soluble contrast swallow in the frontal, oblique and lateral projections.',
})

# ------------------------------------------------------------------ curated rewrites of practice-derived templates
S = lambda heading, normal, *options: {'heading': heading, 'normal': normal, 'options': list(options)}  # noqa: E731
BONE = '[Fracture / Dislocation / Lytic lesion / Sclerotic lesion] [ ].'
SOFT = '[Swelling / Gas / Foreign body / Calcification] [ ].'
CURATED = {
    'xr.acute-abdomen-series': ('Abdominal radiograph, supine, and chest radiograph, erect', [
        S('Free gas', 'No free subdiaphragmatic gas.', '[Right / Left / Bilateral] free subdiaphragmatic gas.'),
        S('Bowel gas pattern', 'Normal bowel gas pattern. No dilated small or large bowel.', '[Small bowel / Large bowel] dilatation to [ ] cm, [with / without] air-fluid levels.'),
        S('Calcification', 'No abnormal calcification.', '[Renal / Ureteric / Gallstone / Vascular] calcification [ ].'),
        S('Chest', 'Clear lungs. No pleural effusion. Normal heart size.', '[Consolidation / Pleural effusion / Pneumothorax] [ ].'),
        S('Bones and soft tissues', 'No acute bony abnormality.', BONE)], 'No bowel obstruction or free gas.'),
    'xr.ankle-stress': ('Right ankle stress radiographs / Left ankle stress radiographs', [
        S('Mortise', 'Congruent ankle mortise.', 'Medial clear space [ ] mm.'),
        S('Talar tilt', 'No abnormal talar tilt on inversion stress.', 'Talar tilt [ ] degrees.'),
        S('Anterior drawer', 'No abnormal anterior talar translation.', 'Anterior translation [ ] mm.'),
        S('Bones', 'No fracture.', BONE)], 'No ankle instability on stress views.'),
    'fl.barium-meal': ('Barium meal', [
        S('Oesophagus', 'Free passage of contrast through the oesophagus.', '[Stricture / Mass / Dysmotility] [ ].'),
        S('Gastro-oesophageal junction', 'No hiatus hernia or reflux.', '[Sliding / Rolling] hiatus hernia [ ].', 'Gastro-oesophageal reflux to the [ ].'),
        S('Stomach', 'Normal gastric distension, folds and emptying. No ulcer or mass.', '[Ulcer / Mass / Outlet obstruction] [ ].'),
        S('Duodenum', 'Normal duodenal cap, C-loop and duodenojejunal flexure.', '[Ulcer / Malrotation / Diverticulum] [ ].')], 'Normal barium meal.'),
    'xr.bone-age': ('Bone age radiograph, left hand', [
        S('Bone age', 'Bone age within two standard deviations of chronological age (Greulich and Pyle).', 'Chronological age [ ]. Bone age [ ] (Greulich and Pyle). [Advanced / Delayed] by [ ].'),
        S('Bones', 'No bony abnormality.', '[Dysplasia / Fracture / Focal lesion] [ ].')], 'Bone age appropriate for chronological age.'),
    'dxa.bone-densitometry': ('Bone densitometry (DXA)', [
        S('Lumbar spine', 'Lumbar spine (L1 to L4) T-score above -1.0.', 'L1 to L4 BMD [ ] g/cm2, T-score [ ], Z-score [ ].', 'Excluded vertebrae: [ ].'),
        S('Hips', 'Total hip and femoral neck T-scores above -1.0.', 'Total hip BMD [ ] g/cm2, T-score [ ]. Femoral neck T-score [ ].'),
        S('Interval change', 'No prior study for comparison.', 'Change since [ ]: [ ] percent at the [ ].')], 'Normal bone mineral density (WHO).'),
    'xr.cervical-spine-flexion-extension': ('Cervical spine radiographs, flexion and extension', [
        S('Alignment', 'Normal alignment in neutral, flexion and extension.', '[Anterolisthesis / Retrolisthesis] of [ ] on [ ] by [ ] mm in [flexion / extension].'),
        S('Atlantoaxial joint', 'Normal atlantodental interval in flexion.', 'Atlantodental interval [ ] mm in flexion.'),
        S('Vertebrae and discs', 'Normal vertebral body heights and disc spaces.', '[Disc space narrowing / Fracture] at [ ].'),
        S('Prevertebral soft tissues', 'Normal prevertebral soft tissues.', 'Prevertebral soft tissue thickening [ ].')], 'No cervical instability.'),
    'fl.contrast-enema': ('Barium enema', [
        S('Colon', 'Contrast reaches the caecum with terminal ileal filling. Normal calibre and mucosa.', '[Stricture / Mass / Polyp] in the [ ].'),
        S('Diverticula', 'No diverticular disease.', 'Diverticular disease of the [ ].'),
        S('Rectum', 'Normal rectum.', '[Mass / Stricture / Fistula] [ ].')], 'Normal barium enema.'),
    'ct.abdomen-multiphase': ('CT abdomen and pelvis, multiphase', [
        S('Liver', 'Normal liver. No focal lesion in any phase.', '[ ] mm [arterially enhancing / washout / hypovascular] lesion in segment [ ].'),
        S('Biliary tree and gallbladder', 'No biliary dilatation. Normal gallbladder.', '[Biliary dilatation / Gallstones] [ ].'),
        S('Pancreas, spleen and adrenal glands', 'Normal pancreas, spleen and adrenal glands.', '[Pancreatic / Adrenal / Splenic] lesion [ ].'),
        S('Kidneys', 'Symmetrical renal enhancement. No renal mass or hydronephrosis.', '[ ] mm [enhancing / non-enhancing] renal lesion, [ ] HU.'),
        S('Bowel and peritoneum', 'Normal bowel. No free fluid.', '[Bowel wall thickening / Free fluid / Collection] [ ].'),
        S('Vessels and lymph nodes', 'Patent portal and hepatic veins. No lymphadenopathy.', '[Thrombus / Lymphadenopathy] [ ].'),
        S('Pelvis', 'Normal bladder and pelvic organs.', '[ ].')], 'Normal multiphase CT abdomen and pelvis.'),
    'ct.angiogram-brain': ('CT angiogram brain', [
        S('Internal carotid arteries', 'Patent intracranial internal carotid arteries.', '[Stenosis / Occlusion] of the [right / left] ICA [ ].'),
        S('Cerebral arteries', 'Patent anterior, middle and posterior cerebral arteries.', '[Stenosis / Occlusion] of the [ ] [ ].'),
        S('Vertebrobasilar arteries', 'Patent vertebral and basilar arteries.', '[Stenosis / Occlusion] of the [ ] [ ].'),
        S('Aneurysm', 'No intracranial aneurysm.', '[ ] mm [saccular / fusiform] aneurysm of the [ ], neck [ ] mm.'),
        S('Vascular malformation', 'No arteriovenous malformation.', 'Arteriovenous malformation [ ].')], 'Normal CT angiogram of the brain.'),
    'ct.angiogram-lower-limbs': ('CT angiogram aorta and lower limbs', [
        S('Aorta and iliac arteries', 'Normal calibre abdominal aorta. Patent iliac arteries.', '[Stenosis / Occlusion / Aneurysm] of the [ ] [ ].'),
        S('Femoropopliteal arteries', 'Patent common femoral, profunda, superficial femoral and popliteal arteries.', '[ ] percent stenosis / Occlusion of the [ ] over [ ] cm.'),
        S('Crural arteries', 'Three-vessel runoff to the ankles.', '[Anterior tibial / Posterior tibial / Peroneal] [occlusion / stenosis] [ ].'),
        S('Collaterals and grafts', 'No significant collaterals. No graft or stent.', '[Graft / Stent] [patent / occluded / stenosed] [ ].')], 'No significant peripheral arterial disease.'),
    'ct.angiogram-upper-limb': ('CT angiogram right upper limb / CT angiogram left upper limb', [
        S('Subclavian and axillary arteries', 'Patent subclavian and axillary arteries.', '[Stenosis / Occlusion / Aneurysm] [ ].'),
        S('Brachial artery', 'Patent brachial artery.', '[Stenosis / Occlusion] [ ].'),
        S('Forearm arteries', 'Patent radial and ulnar arteries to the wrist.', '[Stenosis / Occlusion] of the [radial / ulnar] artery [ ].')], 'Normal CT angiogram of the upper limb.'),
    'ct.ankle-foot': ('CT right ankle and foot / CT left ankle and foot', [
        S('Fracture', 'No fracture.', '[Intra-articular / Extra-articular] fracture of the [ ], [ ] mm step.'),
        S('Ankle joint', 'Congruent ankle mortise. Intact talar dome.', '[Osteochondral lesion / Malalignment] [ ].'),
        S('Hindfoot and midfoot', 'Normal subtalar, midfoot and Lisfranc alignment.', '[Subluxation / Lisfranc injury] [ ].'),
        S('Bones', 'No focal bone lesion.', BONE)], 'Normal CT ankle and foot.'),
    'ct.calcium-score': ('CT coronary calcium score', [
        S('Calcium score', 'Agatston score 0.', 'Agatston score [ ] ([ ] percentile, MESA). LM [ ], LAD [ ], LCx [ ], RCA [ ].'),
        S('Heart and pericardium', 'Normal cardiac size. No pericardial effusion.', '[Cardiomegaly / Pericardial effusion / Valve calcification] [ ].'),
        S('Visible lungs and mediastinum', 'No significant finding in the visible lungs.', '[ ] mm pulmonary nodule in the [ ].')], 'No coronary artery calcium (CAC 0).'),
    'ct.elbow': ('CT right elbow / CT left elbow', [
        S('Fracture', 'No fracture.', '[Radial head / Coronoid / Distal humerus / Olecranon] fracture [ ].'),
        S('Joint', 'Congruent radiocapitellar and ulnohumeral joints. No effusion or loose body.', '[Effusion / Loose body / Subluxation] [ ].'),
        S('Bones', 'No focal bone lesion.', BONE)], 'Normal CT elbow.'),
    'ct.facial-bones': ('CT facial bones', [
        S('Orbits', 'Intact orbital walls and floors.', '[Orbital floor / Medial wall] fracture [ ], [with / without] muscle entrapment.'),
        S('Zygoma and maxilla', 'Intact zygomatic arches, zygomaticomaxillary complexes and maxillae.', '[Zygomaticomaxillary complex / Le Fort / Arch] fracture [ ].'),
        S('Nasal bones and mandible', 'Intact nasal bones and mandible. Normal temporomandibular joints.', '[Nasal / Mandibular] fracture [ ].'),
        S('Sinuses', 'Clear paranasal sinuses.', '[Haemosinus / Mucosal thickening] in the [ ].'),
        S('Soft tissues', 'No soft tissue swelling.', SOFT)], 'No facial fracture.'),
    'ct.femur': ('CT right femur / CT left femur', [
        S('Fracture', 'No fracture.', 'Fracture of the [proximal / mid / distal] femur [ ].'),
        S('Bone', 'No focal bone lesion or periosteal reaction.', '[Lytic / Sclerotic] lesion [ ]; periosteal reaction [ ].'),
        S('Joints and soft tissues', 'Normal hip and knee alignment. Normal soft tissues.', '[Effusion / Haematoma / Mass] [ ].')], 'Normal CT femur.'),
    'ct.hip': ('CT right hip / CT left hip', [
        S('Fracture', 'No fracture or dislocation.', '[Femoral neck / Intertrochanteric / Acetabular] fracture [ ].'),
        S('Joint', 'Congruent hip joint with preserved joint space.', '[Joint space narrowing / Loose body] [ ].'),
        S('Femoral head and acetabulum', 'Normal femoral head and acetabulum.', '[Avascular necrosis / Cam morphology / Dysplasia] [ ].')], 'Normal CT hip.'),
    'ct.knee': ('CT right knee / CT left knee', [
        S('Fracture', 'No fracture.', 'Tibial plateau fracture, Schatzker [ ], [ ] mm depression.'),
        S('Joint', 'Congruent tibiofemoral and patellofemoral joints. No lipohaemarthrosis.', '[Lipohaemarthrosis / Effusion / Loose body] [ ].'),
        S('Bones', 'No focal bone lesion.', BONE)], 'Normal CT knee.'),
    'ct.pelvis': ('CT pelvis with contrast', [
        S('Bladder and pelvic organs', 'Normal bladder and pelvic organs.', '[Bladder wall thickening / Pelvic mass] [ ].'),
        S('Bowel', 'Normal pelvic bowel.', '[Bowel wall thickening / Diverticulitis / Collection] [ ].'),
        S('Lymph nodes and fluid', 'No pelvic lymphadenopathy or free fluid.', '[Lymphadenopathy / Free fluid] [ ].'),
        S('Bones', 'No suspicious bone lesion.', BONE)], 'Normal CT pelvis.'),
    'ct.pelvis-hips': ('CT pelvis and hips', [
        S('Pelvic ring and acetabula', 'No fracture of the pelvic ring or acetabula.', '[Pelvic ring / Acetabular] fracture [ ].'),
        S('Hip joints', 'Congruent hip joints with preserved joint spaces. Normal femoral heads.', '[Dislocation / Avascular necrosis / Joint space narrowing] [ ].'),
        S('Sacroiliac joints and symphysis', 'Normal sacroiliac joints and pubic symphysis.', '[Diastasis / Widening] [ ].'),
        S('Soft tissues', 'Normal pelvic soft tissues.', '[Haematoma / Mass] [ ].')], 'Normal CT pelvis and hips.'),
    'ct.shoulder': ('CT right shoulder / CT left shoulder', [
        S('Fracture', 'No fracture or dislocation.', '[Proximal humeral / Glenoid / Scapular] fracture [ ].'),
        S('Glenohumeral joint', 'Concentric glenohumeral joint. Intact glenoid rim.', 'Glenoid bone loss [ ] percent. Hill-Sachs lesion [ ].'),
        S('Acromioclavicular joint', 'Normal acromioclavicular joint.', '[Separation / Arthropathy] [ ].')], 'Normal CT shoulder.'),
    'ct.oncology-staging': ('CT skull base to pubic symphysis with contrast, oncology staging', [
        S('Neck', 'No cervical lymphadenopathy or neck mass.', 'Level [ ] lymph node [ ] mm short axis.', '[Mass / Thyroid nodule] [ ].'),
        S('Chest', 'No pulmonary nodule, mass, pleural effusion or thoracic lymphadenopathy.', '[ ] mm pulmonary nodule in the [ ].', '[Mediastinal / Hilar] lymph node [ ] mm at station [ ].'),
        S('Abdomen and pelvis', 'No focal liver, adrenal or peritoneal lesion. No abdominal or pelvic lymphadenopathy.', '[Liver / Adrenal / Peritoneal] lesion [ ].', '[Retroperitoneal / Pelvic] lymph node [ ] mm.'),
        S('Bones', 'No suspicious bone lesion.', '[Lytic / Sclerotic / Mixed] lesion in the [ ]; [no / with] pathological fracture.'),
        S('Target lesions', 'No measurable disease.', 'Target lesion [ ]: [ ] mm (series [ ], image [ ]).', 'Sum of diameters [ ] mm; [complete response / partial response / stable disease / progressive disease] (RECIST 1.1).')], 'No evidence of metastatic disease.'),
    'ct.tmj': ('CT temporomandibular joints', [
        S('Condyles', 'Normal mandibular condyles. No erosion or osteophyte.', '[Erosion / Osteophyte / Flattening] of the [right / left] condyle.'),
        S('Joint position', 'Normally seated condyles in the glenoid fossae.', '[Anterior / Posterior] condylar position [ ].'),
        S('Fracture', 'No fracture.', '[Condylar / Subcondylar] fracture [ ].')], 'Normal temporomandibular joints.'),
    'ct.trauma-panscan': ('CT trauma, whole body', [
        S('Brain', 'No intracranial haemorrhage, contusion or mass effect. No skull fracture.', '[Extradural / Subdural / Subarachnoid / Intraparenchymal] haemorrhage [ ].', '[Midline shift / Herniation] [ ].'),
        S('Cervical spine', 'Normal alignment. No fracture.', 'Fracture of [ ].', 'Prevertebral swelling [ ].'),
        S('Chest', 'No pneumothorax, haemothorax, pulmonary contusion or mediastinal haematoma. Normal aorta.', '[Pneumothorax / Haemothorax / Contusion] [ ].', '[Aortic injury / Rib fractures] [ ].'),
        S('Abdomen and pelvis', 'No solid organ, bowel or mesenteric injury. No free fluid or free gas.', '[Liver / Spleen / Kidney] injury, AAST grade [ ].', '[Active extravasation / Free gas / Free fluid] [ ].'),
        S('Thoracolumbar spine and pelvis', 'No spinal or pelvic fracture.', '[Spinal / Pelvic] fracture [ ].'),
        S('Lines and devices', 'No lines or tubes.', '[Endotracheal tube / Chest drain / Pelvic binder] position [ ].')], 'No traumatic injury.'),
    'ct.wrist-hand': ('CT right wrist and hand / CT left wrist and hand', [
        S('Fracture', 'No fracture.', '[Scaphoid / Distal radius / Carpal / Metacarpal] fracture [ ].'),
        S('Alignment', 'Normal carpal alignment. Congruent distal radioulnar joint.', '[Carpal / Distal radioulnar / Carpometacarpal] malalignment [ ].'),
        S('Bones', 'No focal bone lesion.', BONE)], 'Normal CT wrist and hand.'),
    'ct.guided-biopsy': ('CT-guided biopsy', [
        S('Procedure', 'Informed consent. Time-out completed. CT-guided biopsy of the target lesion.', '[ ] G [core / FNA] needle, [ ] passes, from the [ ] approach.'),
        S('Specimens', 'Specimens sent for histology.', 'Specimens sent for [histology / cytology / microbiology].'),
        S('Complications', 'No immediate complication.', '[Pneumothorax / Haemorrhage] [ ].')], 'Uncomplicated CT-guided biopsy.'),
    'fl.cystogram': ('Cystogram', [
        S('Bladder', 'Normal bladder filling and outline. No filling defect or diverticulum.', '[Filling defect / Diverticulum / Trabeculation] [ ].'),
        S('Leak', 'No contrast leak.', '[Intraperitoneal / Extraperitoneal] contrast leak [ ].'),
        S('Reflux', 'No vesicoureteric reflux.', 'Vesicoureteric reflux, grade [ ], [right / left].')], 'Normal cystogram. No leak.'),
    'xr.facial-bones': ('Facial bones radiographs', [
        S('Orbits and zygoma', 'Intact orbital margins and zygomatic arches.', '[Orbital floor / Zygomatic arch / Zygomaticomaxillary complex] fracture [ ].'),
        S('Maxillary sinuses', 'Clear maxillary sinuses. No air-fluid level.', '[Air-fluid level / Opacification] in the [right / left] maxillary sinus.'),
        S('Mandible', 'Intact mandible.', 'Mandibular fracture [ ].')], 'No facial fracture.'),
    'fl.lumbar-puncture': ('Lumbar puncture, fluoroscopy-guided', [
        S('Procedure', 'Informed consent. Time-out completed. Fluoroscopy-guided lumbar puncture.', '[ ] G needle at [ ], [ ] attempts. Opening pressure [ ] cm H2O.'),
        S('CSF', 'Clear CSF obtained and sent for analysis.', '[Clear / Blood-stained / Turbid] CSF, [ ] mL.'),
        S('Complications', 'No immediate complication.', '[ ].')], 'Uncomplicated fluoroscopy-guided lumbar puncture.'),
    'fl.hip-arthrogram': ('Right hip arthrogram injection / Left hip arthrogram injection', [
        S('Procedure', 'Informed consent. Time-out completed. Anterior approach to the hip under fluoroscopy.', '[ ] G needle; [ ] mL iodinated contrast and [ ] mL dilute gadolinium.'),
        S('Arthrogram', 'Intra-articular contrast confirmed.', '[Extravasation / Lymphatic filling] [ ].'),
        S('Complications', 'No immediate complication.', '[ ].')], 'Uncomplicated hip arthrogram injection.'),
    'fl.hysterosalpingogram': ('Hysterosalpingogram', [
        S('Uterine cavity', 'Normal uterine cavity. No filling defect.', '[Filling defect / Septum / Synechiae] [ ].'),
        S('Fallopian tubes', 'Both fallopian tubes fill normally.', '[Right / Left] tubal [occlusion / hydrosalpinx] [ ].'),
        S('Peritoneal spill', 'Free peritoneal spill from both tubes.', '[Loculated / Absent] spill on the [right / left].')], 'Patent fallopian tubes. Normal uterine cavity.'),
    'xr.chest-immigration': ('Chest radiograph, immigration', [
        S('Lungs', 'Clear lungs. No consolidation, cavitation, nodule or fibrosis.', '[Consolidation / Cavitation / Nodule / Fibrosis / Calcified granuloma] in the [ ].'),
        S('Hila and mediastinum', 'Normal hila and mediastinum. No lymphadenopathy.', '[Hilar / Mediastinal] lymphadenopathy [ ].'),
        S('Pleura', 'No pleural effusion or thickening.', '[Pleural effusion / Pleural thickening / Calcification] [ ].'),
        S('Heart and bones', 'Normal heart size. No bony abnormality.', BONE)], 'Normal chest radiograph. No radiographic evidence of active or previous tuberculosis.'),
    'xr.cephalogram': ('Lateral cephalometric radiograph', [
        S('Craniofacial skeleton', 'Normal skull, maxilla and mandible.', '[Maxillary / Mandibular] [prognathism / retrognathism] [ ].'),
        S('Airway', 'Patent airway.', 'Airway narrowing at the [ ].'),
        S('Bones', 'No bony abnormality.', BONE)], 'Normal lateral cephalogram.'),
    'xr.lumbar-spine-flexion-extension': ('Lumbar spine radiographs, flexion and extension', [
        S('Alignment', 'Normal alignment in neutral, flexion and extension. No spondylolisthesis.', '[Anterolisthesis / Retrolisthesis] of [ ] on [ ] by [ ] mm, [ ] mm translation.'),
        S('Pars interarticularis', 'No pars defect.', 'Pars defect at [ ].'),
        S('Vertebrae and discs', 'Normal vertebral body heights and disc spaces.', '[Disc space narrowing / Fracture] at [ ].')], 'No lumbar instability.'),
    'xr.mandible': ('Mandible radiographs', [
        S('Mandible', 'Intact mandible.', 'Mandibular fracture at the [symphysis / body / angle / ramus / condyle] [ ].'),
        S('Temporomandibular joints', 'Normally located condyles.', '[Dislocation / Erosion] of the [right / left] condyle.'),
        S('Teeth', 'No periapical lucency.', 'Periapical lucency at [ ].')], 'No mandibular fracture.'),
    'fl.mcug': ('Micturating cystourethrogram', [
        S('Bladder', 'Normal bladder outline. No diverticulum.', '[Trabeculation / Diverticulum] [ ].'),
        S('Vesicoureteric reflux', 'No vesicoureteric reflux on filling or voiding.', 'Vesicoureteric reflux, grade [ ] (international), [right / left].'),
        S('Urethra', 'Normal urethra on voiding. No valve or stricture.', '[Posterior urethral valve / Stricture] [ ].'),
        S('Emptying', 'Complete bladder emptying.', 'Post-void residual [ ].')], 'Normal micturating cystourethrogram.'),
    'mri.angiogram-brain': ('MR angiogram brain', [
        S('Internal carotid arteries', 'Patent intracranial internal carotid arteries.', '[Stenosis / Occlusion] of the [right / left] ICA [ ].'),
        S('Cerebral arteries', 'Patent anterior, middle and posterior cerebral arteries.', '[Stenosis / Occlusion] of the [ ] [ ].'),
        S('Vertebrobasilar arteries', 'Patent vertebral and basilar arteries.', '[Stenosis / Occlusion] of the [ ] [ ].'),
        S('Aneurysm', 'No intracranial aneurysm.', '[ ] mm aneurysm of the [ ].'),
        S('Vascular malformation', 'No arteriovenous malformation.', 'Arteriovenous malformation [ ].')], 'Normal MR angiogram of the brain.'),
    'mri.bony-pelvis': ('MRI bony pelvis', [
        S('Bone marrow', 'Normal marrow signal. No fracture or focal lesion.', '[Fracture / Marrow oedema / Focal lesion] in the [ ].'),
        S('Hip joints', 'Normal hip joints. No effusion. Normal femoral heads.', '[Effusion / Avascular necrosis / Labral tear] [ ].'),
        S('Sacroiliac joints and symphysis', 'Normal sacroiliac joints and pubic symphysis.', '[Sacroiliitis / Osteitis pubis] [ ].'),
        S('Tendons and muscles', 'Intact gluteal tendons and hamstring origins.', '[Tendinopathy / Tear] of the [ ].')], 'Normal MRI bony pelvis.'),
    'mri.both-hips': ('MRI both hips', [
        S('Femoral heads', 'Normal femoral head signal and contour. No avascular necrosis.', 'Avascular necrosis of the [right / left] femoral head, ARCO stage [ ].'),
        S('Bone marrow', 'No marrow oedema or fracture.', '[Marrow oedema / Insufficiency fracture] [ ].'),
        S('Joints', 'Preserved cartilage. No effusion.', '[Effusion / Cartilage loss] in the [right / left] hip.'),
        S('Tendons and bursae', 'Intact gluteus medius and minimus tendons. No trochanteric bursitis.', '[Tendinopathy / Tear / Bursitis] [ ].')], 'Normal MRI of both hips.'),
    'mri.female-pelvis': ('MRI female pelvis', [
        S('Uterus', 'Normal uterine size and zonal anatomy. Junctional zone not thickened.', '[Fibroid / Adenomyosis / Endometrial thickening] [ ].'),
        S('Cervix and vagina', 'Normal cervix and vagina.', '[Cervical mass / Nabothian cysts] [ ].'),
        S('Ovaries and adnexa', 'Normal ovaries. No adnexal mass.', '[ ] mm [cystic / solid] adnexal lesion, O-RADS MRI [ ].'),
        S('Endometriosis', 'No endometriosis.', 'Endometriosis in the [ ] compartment [ ].'),
        S('Bladder and bowel', 'Normal bladder and pelvic bowel.', '[ ].'),
        S('Lymph nodes and fluid', 'No pelvic lymphadenopathy or free fluid.', '[Lymphadenopathy / Free fluid] [ ].')], 'Normal MRI female pelvis.'),
    'mri.forearm': ('MRI right forearm / MRI left forearm', [
        S('Bones', 'Normal radius and ulna marrow signal.', '[Fracture / Marrow oedema / Focal lesion] [ ].'),
        S('Muscles', 'Normal flexor and extensor muscles.', '[Tear / Oedema / Mass] of the [ ].'),
        S('Soft tissues and nerves', 'No soft tissue mass or collection. Normal neurovascular bundles.', '[Mass / Collection / Neuropathy] [ ].')], 'Normal MRI forearm.'),
    'mri.kidneys': ('MRI kidneys', [
        S('Kidneys', 'Normal renal size and signal. No renal mass or hydronephrosis.', '[ ] mm [cystic / solid] renal lesion, [enhancing / non-enhancing], Bosniak [ ].'),
        S('Renal veins', 'Patent renal veins.', 'Renal vein thrombus [ ].'),
        S('Adrenal glands', 'Normal adrenal glands.', '[ ] mm adrenal nodule, signal drop [present / absent].')], 'Normal MRI kidneys.'),
    'mri.lower-leg': ('MRI right lower leg / MRI left lower leg', [
        S('Bones', 'Normal tibia and fibula marrow signal. No stress injury.', '[Stress reaction / Stress fracture / Focal lesion] of the [tibia / fibula], grade [ ].'),
        S('Muscles', 'Normal calf muscles.', '[Tear / Oedema / Mass] of the [ ].'),
        S('Soft tissues and vessels', 'No soft tissue mass or collection. Normal neurovascular bundles.', '[Mass / Collection] [ ].')], 'Normal MRI lower leg.'),
    'mri.whole-body': ('MRI whole body', [
        S('Bone marrow', 'Normal marrow signal throughout. No focal lesion.', '[Focal / Diffuse] marrow infiltration [ ] (MY-RADS / MET-RADS-P).'),
        S('Spine', 'No pathological fracture or spinal canal compromise.', '[Pathological fracture / Epidural disease] at [ ].'),
        S('Lymph nodes and organs', 'No lymphadenopathy. Normal solid organs.', '[Lymphadenopathy / Organ lesion] [ ].')], 'No evidence of marrow or metastatic disease.'),
    'xr.nasal-bones': ('Nasal bones radiograph', [
        S('Nasal bones', 'No nasal bone fracture.', '[Displaced / Undisplaced] nasal bone fracture.'),
        S('Soft tissues', 'Normal nasal soft tissues.', SOFT)], 'No nasal bone fracture.'),
    'xr.orbits': ('Orbit radiographs, foreign body screen', [
        S('Foreign body', 'No radio-opaque foreign body in either orbit.', 'Radio-opaque foreign body in the [right / left] orbit [ ].'),
        S('Orbital margins', 'Intact orbital margins.', 'Orbital fracture [ ].')], 'No radio-opaque orbital foreign body.'),
    'fl.retrograde-pyelogram': ('Right retrograde pyelogram / Left retrograde pyelogram', [
        S('Ureter', 'Normal ureteric calibre and course. No stricture or filling defect.', '[Stricture / Filling defect / Calculus] at the [ ].'),
        S('Pelvicalyceal system', 'Non-dilated pelvicalyceal system. No filling defect.', '[Hydronephrosis / Filling defect] [ ].'),
        S('Extravasation', 'No contrast extravasation.', 'Contrast extravasation [ ].')], 'Normal retrograde pyelogram.'),
    'fl.urethrogram': ('Retrograde urethrogram', [
        S('Anterior urethra', 'Normal calibre anterior urethra.', '[Stricture / Filling defect / Diverticulum] of the [penile / bulbar] urethra, [ ] cm.'),
        S('Posterior urethra', 'Normal posterior urethra. Free passage into the bladder.', '[Stricture / Disruption] [ ].'),
        S('Extravasation', 'No contrast extravasation.', 'Contrast extravasation [ ].')], 'Normal retrograde urethrogram.'),
    'xr.scapula': ('Right scapula radiographs / Left scapula radiographs', [
        S('Scapula', 'No scapular fracture.', 'Fracture of the [body / neck / glenoid / acromion / coracoid] [ ].'),
        S('Glenohumeral joint', 'Congruent glenohumeral joint.', '[Dislocation / Subluxation] [ ].'),
        S('Bones', 'No focal bone lesion.', BONE)], 'Normal scapula.'),
    'xr.sesamoid': ('Right sesamoid radiographs / Left sesamoid radiographs', [
        S('Sesamoids', 'Intact hallux sesamoids in normal position.', '[Fracture / Fragmentation / Sclerosis] of the [medial / lateral] sesamoid.'),
        S('First metatarsophalangeal joint', 'Normal first metatarsophalangeal joint.', '[Osteoarthritis / Hallux valgus] [ ].')], 'Normal sesamoids.'),
    'fl.shoulder-arthrogram': ('Right shoulder arthrogram injection / Left shoulder arthrogram injection', [
        S('Procedure', 'Informed consent. Time-out completed. Fluoroscopy-guided glenohumeral injection.', '[ ] G needle, [anterior / posterior] approach; [ ] mL iodinated contrast and [ ] mL dilute gadolinium.'),
        S('Arthrogram', 'Intra-articular contrast confirmed.', '[Extravasation / Subacromial contrast] [ ].'),
        S('Complications', 'No immediate complication.', '[ ].')], 'Uncomplicated shoulder arthrogram injection.'),
    'xr.sinuses': ('Paranasal sinus radiograph', [
        S('Sinuses', 'Clear paranasal sinuses. No air-fluid level or mucosal thickening.', '[Air-fluid level / Opacification / Mucosal thickening] in the [ ] sinus.'),
        S('Bone', 'No bony erosion.', 'Bony erosion of the [ ].')], 'Clear paranasal sinuses.'),
    'xr.skull': ('Skull radiographs', [
        S('Vault', 'No skull fracture. No lytic or sclerotic lesion.', '[Linear / Depressed] fracture of the [ ] bone.', '[Lytic / Sclerotic] lesion in the [ ].'),
        S('Sella and sutures', 'Normal sella turcica and sutures.', '[Enlarged sella / Sutural diastasis / Premature fusion] [ ].')], 'Normal skull radiographs.'),
    'fl.small-bowel-follow-through': ('Small bowel follow-through', [
        S('Small bowel', 'Normal small bowel calibre and fold pattern.', '[Stricture / Dilatation / Mass / Fistula] at the [ ].'),
        S('Terminal ileum', 'Normal terminal ileum.', '[Narrowing / Ulceration / Separation of loops] of the terminal ileum.'),
        S('Transit', 'Normal small bowel transit.', 'Contrast reaches the colon at [ ] minutes.', 'Delayed transit [ ].')], 'Normal small bowel follow-through.'),
    'xr.soft-tissue-neck': ('Soft tissue neck radiograph, lateral', [
        S('Prevertebral soft tissues', 'Normal prevertebral soft tissue thickness.', 'Prevertebral thickening to [ ] mm at [ ].'),
        S('Airway', 'Patent airway. Normal epiglottis and aryepiglottic folds.', '[Epiglottic swelling / Airway narrowing] [ ].'),
        S('Foreign body and gas', 'No radio-opaque foreign body. No soft tissue gas.', '[Foreign body / Soft tissue gas] at [ ].')], 'Normal soft tissue neck radiograph.'),
    'xr.standing-feet': ('Foot radiographs, both, weight-bearing', [
        S('Alignment', 'Normal longitudinal arches. Normal Lisfranc alignment. No hallux valgus.', '[Pes planus / Pes cavus / Hallux valgus / Lisfranc malalignment] [ ].'),
        S('Joints', 'Preserved joint spaces.', '[Joint space narrowing / Osteophytes / Erosions] at [ ].'),
        S('Bones and soft tissues', 'No fracture or focal bone lesion. Normal soft tissues.', BONE)], 'Normal weight-bearing radiographs of both feet.'),
    'xr.standing-knees': ('Knee radiographs, both, weight-bearing', [
        S('Tibiofemoral joints', 'Preserved tibiofemoral joint spaces on weight-bearing.', '[Medial / Lateral] joint space narrowing in the [right / left] knee, Kellgren-Lawrence grade [ ].'),
        S('Patellofemoral joints', 'Normal patellofemoral joints and patellar position.', '[Patellofemoral osteoarthritis / Patella alta / Patella baja] [ ].'),
        S('Bones and effusion', 'No fracture or focal bone lesion. No effusion.', '[Effusion / Osteophytes / Subchondral sclerosis] [ ].')], 'Normal weight-bearing radiographs of both knees.'),
    'mg.stereotactic-biopsy': ('Right stereotactic breast biopsy / Left stereotactic breast biopsy', [
        S('Procedure', 'Informed consent. Time-out completed. Stereotactic vacuum-assisted biopsy of the target.', '[ ] G vacuum-assisted needle, [ ] cores; specimen radiograph [shows / does not show] the target calcification.'),
        S('Marker clip', 'Marker clip placed; position confirmed on the post-procedure mammogram.', 'Clip [ ] mm from the target in the [ ] direction.'),
        S('Complications', 'No immediate complication.', '[Haematoma / Vasovagal episode] [ ].')], 'Uncomplicated stereotactic breast biopsy.'),
    'mg.stereotactic-localisation': ('Right stereotactic breast localisation / Left stereotactic breast localisation', [
        S('Procedure', 'Informed consent. Time-out completed. Stereotactic localisation of the target.', '[Hookwire / Seed / Reflector] placed via the [ ] approach.'),
        S('Position', 'Post-procedure mammogram confirms the device at the target.', 'Device [ ] mm from the target in the [ ] direction.'),
        S('Complications', 'No immediate complication.', '[ ].')], 'Successful stereotactic breast localisation.'),
    'xr.sternoclavicular': ('Sternoclavicular joint radiographs', [
        S('Alignment', 'Symmetrical, normally aligned sternoclavicular joints.', '[Anterior / Posterior] dislocation of the [right / left] sternoclavicular joint.'),
        S('Bones', 'No fracture, erosion or sclerosis.', '[Fracture / Erosion / Sclerosis] [ ].')], 'Normal sternoclavicular joints.'),
    'xr.sternum': ('Sternum radiographs', [
        S('Sternum', 'No sternal fracture. Normal manubriosternal alignment.', '[Displaced / Undisplaced] sternal fracture at the [ ].'),
        S('Soft tissues', 'No retrosternal soft tissue swelling.', 'Retrosternal haematoma [ ].')], 'No sternal fracture.'),
    'xr.tmj': ('Temporomandibular joint radiographs', [
        S('Closed mouth', 'Normally seated condyles in the glenoid fossae.', '[Anterior / Posterior] condylar position on the [right / left].'),
        S('Open mouth', 'Normal condylar translation to the articular eminence.', '[Reduced / Excessive] translation on the [right / left].'),
        S('Condyles', 'Normal condylar contour. No erosion or osteophyte.', '[Erosion / Osteophyte / Flattening] [ ].')], 'Normal temporomandibular joints.'),
    'fl.theatre': ('Theatre fluoroscopy', [
        S('Images', 'Intra-operative fluoroscopic images acquired by the operating team.', '[ ] images; screening time [ ] s; dose-area product [ ].'),
        S('Findings', 'Satisfactory position of the implant or reduction on the final images.', '[Implant / Reduction] position [ ].')], 'Intra-operative images for the surgical record.'),
    'us.transcranial-doppler': ('Transcranial Doppler', [
        S('Windows', 'Adequate temporal and suboccipital windows.', 'Inadequate [right / left] temporal window.'),
        S('Anterior circulation', 'Normal, symmetrical mean flow velocities and pulsatility indices in the MCA, ACA and PCA.', '[Raised / Reduced] mean velocity in the [ ] at [ ] cm/s; PI [ ].'),
        S('Posterior circulation', 'Normal vertebral and basilar flow.', '[Raised / Reduced] basilar velocity [ ] cm/s.')], 'Normal transcranial Doppler.'),
    'us.abdomen-pelvis-female': ('Ultrasound abdomen and pelvis, female', [
        S('Liver and biliary tree', 'Normal liver size and echotexture. No focal lesion. Normal gallbladder. No biliary dilatation.', '[Steatosis / Focal lesion / Gallstones / Biliary dilatation] [ ].'),
        S('Pancreas and spleen', 'Normal pancreas and spleen.', '[Splenomegaly / Pancreatic lesion] [ ].'),
        S('Kidneys', 'Normal kidneys. No hydronephrosis or calculus.', '[Hydronephrosis / Calculus / Cyst] in the [right / left] kidney [ ].'),
        S('Aorta', 'Normal calibre abdominal aorta.', 'Abdominal aortic aneurysm, [ ] cm.'),
        S('Bladder', 'Normal bladder.', '[Wall thickening / Calculus] [ ].'),
        S('Uterus and ovaries', 'Normal uterus and ovaries. No adnexal mass.', '[Fibroid / Ovarian cyst / Adnexal mass] [ ].'),
        S('Free fluid', 'No free fluid.', '[Small / Moderate / Large] free fluid [ ].')], 'Normal ultrasound abdomen and pelvis.'),
    'us.abdomen-pelvis-male': ('Ultrasound abdomen and pelvis, male', [
        S('Liver and biliary tree', 'Normal liver size and echotexture. No focal lesion. Normal gallbladder. No biliary dilatation.', '[Steatosis / Focal lesion / Gallstones / Biliary dilatation] [ ].'),
        S('Pancreas and spleen', 'Normal pancreas and spleen.', '[Splenomegaly / Pancreatic lesion] [ ].'),
        S('Kidneys', 'Normal kidneys. No hydronephrosis or calculus.', '[Hydronephrosis / Calculus / Cyst] in the [right / left] kidney [ ].'),
        S('Aorta', 'Normal calibre abdominal aorta.', 'Abdominal aortic aneurysm, [ ] cm.'),
        S('Bladder and prostate', 'Normal bladder. Normal prostate size.', 'Prostate volume [ ] mL. [Wall thickening / Post-void residual] [ ].'),
        S('Free fluid', 'No free fluid.', '[Small / Moderate / Large] free fluid [ ].')], 'Normal ultrasound abdomen and pelvis.'),
    'us.abdominal-wall': ('Ultrasound abdominal wall', [
        S('Hernia', 'No hernia at rest or on Valsalva.', '[Inguinal / Femoral / Umbilical / Incisional] hernia, [ ] mm defect, containing [fat / bowel], [reducible / irreducible].'),
        S('Abdominal wall', 'Normal skin, subcutaneous fat and abdominal wall muscles. No rectus diastasis.', '[Rectus diastasis / Haematoma / Lipoma] [ ].'),
        S('Mass or collection', 'No soft tissue mass or collection.', '[Mass / Collection] [ ].')], 'No abdominal wall hernia.'),
    'us.lower-limb-veins-bilateral': ('Venous duplex ultrasound, both lower limbs', [
        S('Deep veins', 'Fully compressible common femoral, femoral and popliteal veins bilaterally, with normal flow.', '[Occlusive / Non-occlusive] thrombus in the [right / left] [ ] vein.'),
        S('Calf veins', 'Compressible calf veins bilaterally.', 'Calf vein thrombus in the [right / left] [ ].'),
        S('Flow', 'Normal respiratory phasicity and augmentation bilaterally.', 'Loss of phasicity in the [right / left] common femoral vein.'),
        S('Other findings', 'Patent great saphenous veins. No Baker cyst.', '[Superficial thrombophlebitis / Baker cyst] [ ].')], 'No deep vein thrombosis in either leg.'),
    'us.early-pregnancy': ('Ultrasound early pregnancy', [
        S('Gestational sac', 'Single intrauterine gestational sac with a yolk sac.', 'Mean sac diameter [ ] mm. [No yolk sac / No embryo].'),
        S('Embryo', 'Single embryo with cardiac activity.', 'Crown-rump length [ ] mm, equivalent to [ ] weeks [ ] days. Cardiac activity [present / absent].'),
        S('Uterus and adnexa', 'No subchorionic haematoma. Normal ovaries. No adnexal mass.', '[Subchorionic haematoma / Adnexal mass] [ ].'),
        S('Free fluid', 'No free fluid.', '[Small / Moderate / Large] free fluid [ ].')], 'Single live intrauterine pregnancy.'),
    'us.renal-doppler': ('Ultrasound renal Doppler', [
        S('Kidneys', 'Normal renal size. No hydronephrosis.', '[Right / Left] kidney [ ] cm. [Hydronephrosis / Scarring] [ ].'),
        S('Renal arteries', 'Patent main renal arteries with normal peak systolic velocities.', 'Peak systolic velocity [ ] cm/s; renal-aortic ratio [ ] on the [right / left].'),
        S('Intrarenal arteries', 'Normal intrarenal waveforms. Resistive indices within normal limits.', 'Tardus parvus waveform on the [right / left]; RI [ ].'),
        S('Renal veins', 'Patent renal veins.', 'Renal vein thrombus [ ].')], 'No renal artery stenosis.'),
    'us.paracentesis': ('Ultrasound-guided paracentesis', [
        S('Procedure', 'Informed consent. Time-out completed. Ultrasound-guided paracentesis at the marked site.', '[ ] G needle in the [right / left] iliac fossa.'),
        S('Fluid', 'Straw-coloured ascites drained and sent for analysis.', '[ ] mL of [straw-coloured / blood-stained / turbid] fluid.'),
        S('Complications', 'No immediate complication.', '[ ].')], 'Uncomplicated ultrasound-guided paracentesis.'),
    'fl.water-soluble-enema': ('Water-soluble contrast enema', [
        S('Rectum and colon', 'Free flow of contrast through the rectum and colon.', '[Stricture / Obstruction] at the [ ].'),
        S('Anastomosis', 'Intact anastomosis. No contrast leak.', 'Contrast leak at the [ ] anastomosis [ ].')], 'No anastomotic leak.'),
    'fl.contrast-swallow-leak': ('Water-soluble contrast swallow', [
        S('Oesophagus', 'Free passage of contrast into the stomach.', '[Stricture / Obstruction] at the [ ].'),
        S('Leak', 'No contrast leak.', 'Contrast leak at the [ ] [ ].'),
        S('Aspiration', 'No aspiration.', '[Penetration / Aspiration] [ ].')], 'No leak or obstruction.'),
}

# ------------------------------------------------------------------ Prism titles for every performed study
PRISM_TITLES = {
    'ra.ultrasound-acute-abdomen': ['ultrasound abdomen acute', 'acute abdomen ultrasound'],
    'ra.transvaginal-nongynaecology': ['transvaginal ultrasound non-gynaecological', 'TV ultrasound pelvis'],
    'ra.appendicitis': ['ultrasound appendix', 'appendix ultrasound', 'ultrasound right iliac fossa'],
    'ra.ultrasound-bile-duct-stones': ['ultrasound liver and biliary tree', 'ultrasound bile ducts', 'ultrasound CBD'],
    'ra.ultrasound-gallbladder': ['ultrasound gallbladder', 'gallbladder ultrasound', 'ultrasound RUQ'],
    'ra.liver-lirads': ['MRI liver HCC surveillance', 'MRI liver cirrhosis'],
    'liver.lirads-calculated': ['MRI liver LI-RADS', 'MRI liver primovist'],
    'ra.ct-abdominal-trauma': ['CT abdomen and pelvis trauma', 'CT abdomen trauma'],
    'ra.ct-bowel-ischaemia': ['CT angiogram abdomen and pelvis', 'CT mesenteric angiogram', 'CTA mesenteric'],
    'ra.ct-bowel-wall': ['CT abdomen and pelvis bowel'],
    'ra.ct-bowel-obstruction': ['CT abdomen and pelvis bowel obstruction', 'CT small bowel obstruction'],
    'ra.ct-small-bowel-tumours': ['CT enterography', 'CT small bowel enterography'],
    'ra.ultrasound-gi-tract': ['ultrasound bowel', 'bowel ultrasound'],
    'ra.ultrasound-ibd': ['intestinal ultrasound', 'ultrasound IBD', 'ultrasound small bowel'],
    'ra.mri-crohn': ['MR enterography', 'MRI small bowel', 'MRE'],
    'ra.mri-anal-cancer': ['MRI anal canal', 'MRI anal cancer'],
    'ra.swallowing': ['videofluoroscopic swallow', 'VFSS', 'modified barium swallow'],
    'ra.dynamic-rectal-examination': ['defecating proctogram', 'defecography', 'evacuation proctogram'],
    'ra.gi-foreign-bodies': ['foreign body x-ray', 'swallowed foreign body x-ray', 'mouth to anus x-ray'],
    'ra.ct-pancreatitis': ['CT pancreas', 'CT pancreatitis'],
    'ra.ct-pancreatic-cancer': ['CT pancreas protocol', 'pancreatic protocol CT'],
    'ra.pancreatic-cysts': ['MRI pancreas and MRCP', 'MRI pancreatic cyst'],
    'ra.ct-peritoneum': ['CT abdomen and pelvis peritoneum'],
    'ra.ct-peritoneal-carcinomatosis': ['CT peritoneal carcinomatosis'],
    'ra.abdominal-wall-hernias': ['CT abdominal wall', 'CT hernia'],
    'ct.appendix': ['CT appendix', 'CT appendicitis'],
    'ct.liver-mass': ['CT liver multiphase', 'CT liver lesion'],
    'ct.liver-lirads': ['CT liver HCC surveillance', 'CT liver cirrhosis'],
    'ct.liver-lirads-calculated': ['CT liver LI-RADS'],
    'ct.oesophagus': ['CT chest with oral contrast', 'CT oesophagus'],
    'us.breast-implants': ['ultrasound breast implants', 'breast implant ultrasound'],
    'ct.cardiac-mass': ['CT heart', 'cardiac CT mass'],
    'ct.angiogram-carotids': ['CT angiogram carotids neck'],
    'mri.angiogram-carotids': ['MR angiogram carotids neck'],
    'mri.thymus': ['MRI thymus', 'MRI mediastinum'],
    'mri.paediatric-mediastinum': ['MRI chest paediatric', 'MRI chest child'],
    'mri.renal-cyst': ['MRI kidneys renal cyst', 'MRI renal cyst'],
    'mri.renal-mass': ['MRI kidneys renal mass', 'MRI renal mass'],
    'mri.adrenals': ['MRI adrenal glands', 'MRI adrenal'],
    'mri.adnexal-mass': ['MRI pelvis adnexal mass', 'MRI adnexa'],
    'us.uterus-3d': ['3D ultrasound uterus', 'ultrasound uterus 3D'],
    'xr.bone-lesion': ['x-ray bone lesion', 'bone lesion x-ray'],
    'xr.cartilage-lesion': ['x-ray cartilage lesion'],
    'xr.stress-injury': ['x-ray stress fracture', 'stress fracture x-ray'],
    'mri.brain-stroke': ['MRI brain stroke protocol', 'MRI brain stroke', 'MRI stroke'],
    'mri.brain-haemorrhage': ['MRI brain haemorrhage'],
    'mri.venogram': ['MR venogram', 'MRV brain', 'MR venography'],
    'mri.orbits': [],
    'ct.angiogram-head-neck-tinnitus': ['CT angiogram pulsatile tinnitus', 'CTA tinnitus'],
    'ct.sinuses': [],
    'mri.neck-tumour': ['MRI neck cancer staging', 'MRI neck tumour'],
    'ct.neck-nodes': ['CT neck lymph nodes'],
    'mri.paediatric-abdomen-cystic': ['MRI abdomen paediatric cystic mass'],
    'ct.paediatric-abdomen-solid': ['CT abdomen paediatric', 'CT abdomen child'],
    'mri.paediatric-abdomen-solid': ['MRI abdomen paediatric', 'MRI abdomen child'],
    'mri.paediatric-renal-tumour': ['MRI abdomen paediatric renal tumour', 'MRI Wilms'],
    'mri.thoracolumbar-trauma': ['MRI thoracolumbar spine trauma', 'MRI spine trauma'],
    'us.male-breast': ['ultrasound male breast', 'ultrasound gynaecomastia'],
    'mri.cervical-spine-trauma': ['MRI cervical spine trauma', 'MRI c-spine trauma'],
    'template:breast-calcifications-report': ['magnification mammogram', 'mammogram magnification views'],
    'ra.mri-breast': ['MRI breasts', 'MRI breast', 'breast MRI', 'MR breast'],
    'ra.breast-implants': ['MRI breast implants', 'breast implant MRI'],
    'ra.male-breast': ['male mammogram', 'mammogram male breast'],
    'ra.breast-cancer-staging': ['MRI breasts staging', 'MRI breast cancer staging'],
    'cardiology.echocardiography': ['echocardiogram', 'transthoracic echocardiogram', 'TTE', 'echo'],
    'cardiology.percutaneous-angiography': ['coronary angiogram', 'cardiac catheterisation', 'angiogram coronary'],
    'ra.ct-tavi': ['CT TAVI', 'TAVI CT', 'CT TAVR', 'TAVI planning CT'],
    'ra.thoracic-aorta-measurement': ['CT angiogram thoracic aorta', 'CTA thoracic aorta'],
    'ra.aortic-aneurysm-rupture': ['CT angiogram abdominal aorta', 'CTA abdominal aorta', 'CT AAA'],
    'ra.cardiac-masses': ['MRI heart mass', 'cardiac MRI mass'],
    'ra.mri-cardiomyopathy': ['cardiac MRI', 'MRI heart', 'CMR', 'cardiac MR'],
    'ra.cardiovascular-devices': ['chest x-ray pacemaker', 'chest x-ray device check'],
    'ra.vascular-anomalies': ['CT angiogram chest', 'CTA chest'],
    'ra.mra-peripheral-vessels': ['MR angiogram lower limbs', 'MRA lower limbs', 'MR runoff'],
    'us.venous-duplex-upper-limb': ['upper limb venous Doppler', 'ultrasound arm DVT', 'arm DVT ultrasound'],
    'us.venous-insufficiency': ['venous insufficiency Doppler', 'varicose veins ultrasound', 'venous reflux study'],
    'ra.ct-lung-cancer': ['CT chest and upper abdomen', 'CT lung cancer staging'],
    'ra.ct-pulmonary-nodules': ['CT chest nodule', 'CT pulmonary nodule'],
    'chest.ct-lung-screening': ['low-dose CT chest', 'lung cancer screening CT', 'LDCT chest'],
    'oncology.lesion-growth': ['CT chest nodule follow-up', 'CT chest follow-up'],
    'ra.ct-airways': ['CT chest airways', 'CT bronchiectasis'],
    'ra.ct-covid': ['CT chest COVID', 'CT chest without contrast COVID'],
    'ra.tuberculosis': ['chest x-ray tuberculosis', 'chest x-ray TB'],
    'ra.thymus': ['CT chest thymus', 'CT thymus'],
    'ra.paediatric-chest-ct': ['CT chest paediatric', 'CT chest child'],
    'ra.neonatal-chest-xray': ['neonatal chest x-ray', 'NICU chest x-ray', 'babygram'],
    'ra.paediatric-mediastinum': ['CT chest paediatric mediastinal mass'],
    'ra.ct-cardiovascular-pearls': ['CT chest cardiovascular'],
    'template:nuclear-general-report': ['nuclear medicine study', 'bone scan', 'thyroid scan', 'VQ scan'],
    'template:pet-ct-report': ['FDG PET/CT', 'PET/CT', 'PET CT', 'FDG PET'],
    'template:theranostics-report': ['PSMA PET/CT', 'SSTR PET/CT', 'DOTATATE PET/CT'],
    'oncology.recist-follow-up': ['CT chest abdomen and pelvis RECIST follow-up', 'CT CAP follow-up'],
    'ra.renal-cysts-bosniak': ['CT kidneys renal cyst', 'CT renal cyst'],
    'ra.solid-renal-masses': ['CT kidneys renal mass', 'CT renal mass'],
    'ct.urography': ['CT urogram', 'CT urography', 'CTU'],
    'ra.adrenal-lesions': ['CT adrenals washout', 'adrenal protocol CT'],
    'ra.mri-bladder': ['MRI bladder', 'bladder MRI', 'MRI bladder VI-RADS'],
    'ra.ultrasound-paediatric-scrotum': ['ultrasound scrotum paediatric', 'ultrasound testes child'],
    'ra.ovarian-cysts': ['ultrasound adnexa', 'ultrasound ovarian cyst'],
    'us.adnexal-orads': ['ultrasound adnexa O-RADS', 'transvaginal ultrasound adnexa'],
    'ra.mri-endometriosis': ['MRI pelvis endometriosis', 'MRI endometriosis'],
    'ra.mri-cervical-cancer': ['MRI pelvis cervical cancer', 'MRI cervix'],
    'ra.mri-endometrial-cancer': ['MRI pelvis endometrial cancer', 'MRI endometrium'],
    'ra.mullerian-anomalies': ['MRI pelvis uterine anomaly', 'MRI uterine anatomy'],
    'ra.arthritis': ['hands x-ray arthritis', 'hands and feet x-ray', 'x-ray hands and feet'],
    'ra.ankle-fractures': ['ankle x-ray trauma', 'ankle fracture x-ray'],
    'ra.foot-ankle-cases': ['foot and ankle x-ray', 'x-ray foot and ankle'],
    'ra.hip-fai': ['hip x-ray impingement', 'hip x-ray FAI', 'Dunn view hip'],
    'msk.mri-knee-postoperative': ['MRI knee postoperative', 'MRI knee post-op'],
    'xr.knee-arthroplasty': ['knee replacement x-ray', 'knee arthroplasty x-ray', 'TKR x-ray'],
    'ra.mri-diabetic-foot': ['MRI foot with contrast', 'MRI diabetic foot', 'MRI foot osteomyelitis'],
    'msk.ultrasound-nerves-lower-limb': ['ultrasound nerves lower limb', 'ultrasound peroneal nerve'],
    'msk.mri-shoulder-postoperative': ['MRI shoulder postoperative', 'MRI shoulder post-op'],
    'xr.shoulder-arthroplasty': ['shoulder replacement x-ray', 'shoulder arthroplasty x-ray'],
    'ra.wrist-instability': ['wrist instability series', 'wrist x-ray instability', 'clenched fist view'],
    'msk.ultrasound-hand': ['ultrasound hand', 'hand ultrasound', 'ultrasound finger'],
    'msk.mri-hand': ['MRI hand', 'MRI finger', 'hand MRI'],
    'msk.ultrasound-nerves-upper-limb': ['ultrasound nerves upper limb', 'ultrasound carpal tunnel', 'ultrasound ulnar nerve'],
    'ra.bone-tumours': ['MRI bone lesion', 'MRI bone tumour'],
    'ra.cartilage-tumours': ['MRI cartilage lesion', 'MRI enchondroma'],
    'msk.mri-soft-tissue-mass': ['MRI soft tissue mass', 'MRI lump'],
    'ra.mri-muscle-injury': ['MRI muscle injury', 'MRI muscle tear'],
    'ra.mri-muscle-disease': ['MRI muscles myositis', 'MRI myopathy'],
    'ra.stress-fractures': ['MRI stress fracture', 'MRI stress injury'],
    'ra.ultrasound-joint-injection': ['ultrasound guided joint injection', 'ultrasound guided injection'],
    'ra.ct-traumatic-haemorrhage': ['CT brain trauma', 'CT head trauma', 'CT head injury'],
    'ra.intracranial-haemorrhage': ['CT brain and CT angiogram', 'CT brain haemorrhage'],
    'ra.mri-brain-tumours': ['MRI brain tumour', 'MRI brain metastases'],
    'ra.mri-cns-enhancement': ['MRI brain enhancing lesion'],
    'ra.mri-dementia': ['MRI brain dementia', 'MRI brain memory', 'MRI brain cognitive'],
    'ra.mri-epilepsy': ['MRI brain epilepsy', 'MRI epilepsy protocol', 'MRI seizure'],
    'ra.mri-ms': ['MRI brain MS', 'MRI brain demyelination', 'MRI multiple sclerosis'],
    'ra.venous-sinus-thrombosis': ['CT venogram', 'CTV brain', 'CT venography'],
    'ra.intracranial-hypotension': ['MRI brain and spine with contrast', 'MRI intracranial hypotension'],
    'ra.mri-trigeminal': ['MRI trigeminal nerves', 'MRI trigeminal neuralgia'],
    'ra.mri-sinuses': ['MRI paranasal sinuses', 'MRI sinuses', 'MR sinuses'],
    'ra.craniosynostosis': ['CT head 3D', 'CT craniosynostosis', 'CT skull 3D'],
    'neck.ct-post-treatment': ['CT neck post-treatment', 'CT neck surveillance'],
    'neck.mri-post-treatment': ['MRI neck post-treatment', 'MRI neck surveillance'],
    'ra.paediatric-elbow-fractures': ['elbow x-ray paediatric', 'elbow x-ray child'],
    'ra.paediatric-hip': ['hip x-ray paediatric', 'pelvis x-ray child', 'frog leg x-ray'],
    'ra.neonatal-acute-abdomen': ['abdominal x-ray neonatal', 'neonatal abdominal x-ray'],
    'ra.necrotising-enterocolitis': ['abdominal x-ray NEC', 'decubitus abdomen x-ray neonatal'],
    'ra.paediatric-neck-masses': ['ultrasound neck paediatric', 'ultrasound neck child'],
    'ra.paediatric-cystic-abdominal-masses': ['ultrasound abdomen paediatric cystic mass'],
    'ra.paediatric-solid-abdominal-masses': ['ultrasound abdomen paediatric', 'ultrasound abdomen child'],
    'ra.paediatric-renal-tumours': ['CT abdomen paediatric renal tumour'],
    'ra.thoracolumbar-fractures': ['CT thoracolumbar spine', 'CT TL spine'],
    'ra.mri-myelopathy': ['MRI spine myelopathy', 'MRI cord compression'],
    'msk.mri-lumbosacral-plexus': ['MR neurography lumbosacral plexus', 'MRI lumbosacral plexus'],
    'msk.mri-brachial-plexus': ['MR neurography brachial plexus', 'MRI brachial plexus'],
    'msk.mri-spine-cervical-postoperative': ['MRI cervical spine postoperative', 'MRI c-spine post-op'],
    'msk.mri-spine-thoracic-postoperative': ['MRI thoracic spine postoperative', 'MRI t-spine post-op'],
    'msk.ct-spine-postoperative': ['CT spine postoperative', 'CT spine post-op', 'CT spine fusion'],
    'ra.ultrasound-neonatal-spine': ['ultrasound spine neonatal', 'neonatal spine ultrasound', 'ultrasound spine infant'],
}

# ------------------------------------------------------------------ formatter (one layout for every file)


def _dump(value):
    return json.dumps(value, ensure_ascii=False)


def format_file(data):
    lines = ['{', '  "schema": ' + _dump(data['schema']) + ',', '  "revision": ' + _dump(data['revision']) + ',',
             '  "templates": {']
    items = list(data['templates'].items())
    for index, (identifier, item) in enumerate(items):
        lines.append('    ' + _dump(identifier) + ': {')
        lines.append('      "title": ' + _dump(item['title']) + ',')
        lines.append('      "radiograph": ' + ('true' if item['radiograph'] else 'false') + ',')
        if 'technique' in item:
            lines.append('      "technique": {"normal": ' + _dump(item['technique']['normal']) + ',')
            lines.append('                    "options": ' + _dump(item['technique'].get('options', [])) + '},')
        lines.append('      "sections": [')
        for s_index, section in enumerate(item['sections']):
            options = section.get('options', [])
            head = '        {"heading": ' + _dump(section['heading']) + ', "normal": ' + _dump(section['normal']) + ','
            lines.append(head)
            if options:
                lines.append('         "options": [' + _dump(options[0]) + ('' if len(options) == 1 else ','))
                for o_index, option in enumerate(options[1:], 1):
                    lines.append('                     ' + _dump(option) + ('' if o_index == len(options) - 1 else ','))
                lines[-1] += ']}'
            else:
                lines.append('         "options": []}')
            if s_index < len(item['sections']) - 1:
                lines[-1] += ','
        lines.append('      ],')
        impression = item['impression']
        tail = '      "impression": ' + _dump(impression)
        if 'recommendation' in item:
            tail += ',\n      "recommendation": ' + _dump(item['recommendation'])
        lines.append(tail)
        lines.append('    }' + (',' if index < len(items) - 1 else ''))
    lines += ['  }', '}']
    return '\n'.join(lines) + '\n'


MODALITY = {
    'CT': r'\bCT\b|\bHRCT\b',
    'MRI': r'\bMRI?\b|\bMRA\b|\bMRCP\b|\bMR\b|STIR|FLAIR|gadolinium',
    'US': r'ultrasound|sonograph|duplex|Doppler|transducer|echocardiogra',
    'XR': r'(?<!correlated with )radiograph',
}


def modalities(text):
    return {m for m, p in MODALITY.items() if re.search(p, text, re.I)}


def run():
    files = {path: json.loads(path.read_text()) for path in sorted(TEMPLATES.glob('*.json'))}
    owner = {}
    for path, data in files.items():
        for identifier in data['templates']:
            owner[identifier] = path
    additions = json.loads(ADDITIONS.read_text())
    prism = json.loads(PRISM.read_text())

    # Identities: renames and the duplicate removal.
    for old, new in RENAME.items():
        path = owner.pop(old)
        templates = files[path]['templates']
        files[path]['templates'] = {(new if k == old else k): v for k, v in templates.items()}
        owner[new] = path
        additions['investigations'][new] = additions['investigations'].pop(old)
        for row in additions['coverage']:
            if row['investigation_id'] == old:
                row['investigation_id'] = new
        if old in prism['titles']:
            prism['titles'][new] = prism['titles'].pop(old)
        prism['practice_studies'] = {k: (new if v == old else v) for k, v in prism['practice_studies'].items()}
    for gone, keep in DROP.items():
        files[owner.pop(gone)]['templates'].pop(gone)
        additions['investigations'].pop(gone)
        additions['coverage'] = [r for r in additions['coverage'] if r['investigation_id'] != gone]
        moved = prism['titles'].pop(gone, [])
        prism['titles'].setdefault(keep, [])
        prism['titles'][keep] = moved + [t for t in prism['titles'][keep] if t not in moved]
        prism['practice_studies'] = {k: (keep if v == gone else v) for k, v in prism['practice_studies'].items()}
    for study, target in PRACTICE_REMAP.items():
        previous = prism['practice_studies'][study]
        prism['practice_studies'][study] = target
        # The practice study's titles follow it to the examination of the right modality.
        names = [n['names'] for n in json.loads((DATA / 'radproof-practice-library.json').read_text())['templates']
                 if n['name'] == study][0]
        moved = [t for t in prism['titles'].get(previous, []) if t in names]
        prism['titles'][previous] = [t for t in prism['titles'].get(previous, []) if t not in moved]
        prism['titles'].setdefault(target, [])
        prism['titles'][target] = moved + [t for t in prism['titles'][target] if t not in moved]

    library = {k: files[owner[k]]['templates'][k] for k in owner}
    for identifier, item in library.items():
        if identifier in CURATED:
            title, sections, impression = CURATED[identifier]
            item['title'] = title
            item['sections'] = sections
            item['impression'] = impression
        if identifier in TITLES:
            item['title'] = TITLES[identifier]
        if identifier in TECHNIQUE:
            item['technique']['normal'] = TECHNIQUE[identifier]
        title_modalities = modalities(item['title'])
        if 'technique' in item and title_modalities:
            item['technique']['options'] = [o for o in item['technique'].get('options', [])
                                            if not (modalities(o) - title_modalities)]
        # One normal impression line.
        if isinstance(item['impression'], list) and len(item['impression']) == 1:
            item['impression'] = item['impression'][0]
        if identifier in additions['investigations']:
            additions['investigations'][identifier]['title'] = item['title'].split(' / ')[0]

    # Prism titles: every performed study has some; none is owned twice.
    for identifier, titles in PRISM_TITLES.items():
        if identifier not in library:
            raise SystemExit('Prism titles for an unknown examination: ' + identifier)
        current = prism['titles'].setdefault(identifier, [])
        current += [t for t in titles if t not in current]
    seen, dropped = {}, []
    shared = {t.lower() for t in prism['shared_left_to_practice']}
    for identifier in list(prism['titles']):
        kept = []
        for title in prism['titles'][identifier]:
            key = title.lower()
            if key in seen or key in shared or ',' in title:
                dropped.append((identifier, title, seen.get(key)))
                continue
            seen[key] = identifier
            kept.append(title)
        prism['titles'][identifier] = kept
    prism['titles'] = {k: v for k, v in prism['titles'].items() if v}
    prism['not_performed_studies'] = NOT_STUDIES
    missing = [k for k in library if k not in NOT_STUDIES and not prism['titles'].get(k)]
    if missing:
        raise SystemExit('Performed studies without Prism titles: ' + ', '.join(missing))

    for path, data in files.items():
        data['revision'] = '2026-11-13'
        path.write_text(format_file(data))
    ADDITIONS.write_text(json.dumps(additions, ensure_ascii=False, indent=1) + '\n')
    PRISM.write_text(json.dumps(prism, ensure_ascii=False, indent=1) + '\n')
    practice_file = ROOT / 'tools' / 'authoring' / 'practice_examinations.json'
    practice_file.write_text(json.dumps(prism['practice_studies'], ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'templates': len(library), 'curated': len(CURATED), 'retitled': len(TITLES),
                      'with_prism_titles': len(prism['titles']), 'titles': sum(len(v) for v in prism['titles'].values()),
                      'dropped_duplicate_titles': dropped}))


if __name__ == '__main__':
    run()
