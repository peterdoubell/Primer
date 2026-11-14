"""Select a routine acquisition from each reviewed study's choices.

Indices refer to the existing, referenced report protocol choices. An explicit
selection or edited technique supersedes the suggested acquisition.
"""

# Number of routine choices from the start of each profile. Entries with
# alternatives or optional series use explicit indices below.
ROUTINE = {
    1: """
        ra.mri-knee msk.mri-knee-postoperative ra.mri-shoulder msk.mri-shoulder-postoperative
        ra.mri-ankle ra.mri-rectal-cancer ra.mri-epilepsy ct.appendix
        ra.ct-bowel-wall ra.ct-bowel-obstruction ra.abdominal-wall-hernias
        ct.pelvis ct.paediatric-abdomen-solid ra.ct-peritoneum ra.ct-peritoneal-carcinomatosis
        ra.mri-diabetic-foot
    """,
    2: """
        msk.mri-sacroiliac ct.knee ra.hrct-lung ct.kub ra.ct-pulmonary-nodules chest.ct-lung-screening
        msk.ct-spine-postoperative mri.thoracolumbar-trauma mri.cervical-spine-trauma
        ra.ct-abdominal-trauma ct.trauma-panscan mri.adrenals ra.ct-airways
        ra.mri-anal-cancer ct.ankle-foot msk.mri-foot msk.mri-soft-tissue-mass
        neuro.ct-brain-routine ra.ct-covid ra.ct-coronary ct.calcium-score
        neck.ct-post-treatment ra.mri-elbow ct.oesophagus ct.hip ct.pelvis-hips
        ra.ct-traumatic-haemorrhage ct.angiogram-brain mri.angiogram-brain
        ra.mri-muscle-injury ra.mri-muscle-disease ra.mri-hamstring ct.femur mri.bony-pelvis
        mri.forearm mri.lower-leg mri.thymus ct.neck-nodes ct.facial-bones
        mri.paediatric-mediastinum ct.elbow ra.ct-pancreatic-cancer ra.pulmonary-hypertension
        ra.mra-peripheral-vessels ct.angiogram-carotids mri.angiogram-carotids
        ct.angiogram-lower-limbs ct.angiogram-upper-limb ct.shoulder ra.mri-sinuses ct.sinuses
        ra.ct-temporal-bone ct.angiogram-head-neck-tinnitus ra.mri-endometriosis
        ct.wrist-hand msk.mri-wrist msk.mri-hand ra.mri-prostate ra.mri-ms
    """,
    3: """
        ct.guided-biopsy ct.urography mri.renal-cyst mri.renal-mass mri.kidneys
        ct.oncology-staging ra.mri-lumbar-disc msk.mri-lumbosacral-plexus
        neuro.mri-spine-cervical neuro.mri-spine-thoracic mri.brain-stroke
        ra.ct-acute-aortic-syndrome ra.mri-bladder mri.whole-body ra.ct-bowel-ischaemia
        neuro.mri-brain-routine mri.brain-anatomy ra.mri-breast ct.cardiac-mass
        ra.mri-neck-spaces neck.mri-post-treatment mri.neck-tumour ra.ct-small-bowel-tumours
        ct.colonography msk.mri-hip mri.brain-haemorrhage template:msk-mri-report mri.orbits
        mri.paediatric-abdomen-cystic mri.paediatric-abdomen-solid mri.paediatric-renal-tumour
        ra.mri-perianal-fistula msk.mri-brachial-plexus ct.tmj ra.mri-trigeminal
        ra.mri-cervical-cancer ra.mri-endometrial-cancer mri.female-pelvis
        ra.intracranial-hypotension
    """,
    4: """
        ct.liver-mass ct.liver-lirads ct.liver-lirads-calculated ct.abdomen-multiphase
        ra.mri-brain-tumours ra.mri-cardiomyopathy ra.mri-cns-enhancement ra.mri-dementia
        ra.mri-crohn mri.adnexal-mass
    """,
}
ROUTINE_INDICES = {identifier: tuple(range(count))
                   for count, ids in ROUTINE.items() for identifier in ids.split()}
ROUTINE_INDICES.update({
    'ra.mri-myelopathy': (1,),
    'msk.mri-spine-cervical-postoperative': (0, 1),
    'msk.mri-spine-thoracic-postoperative': (0, 1),
    'msk.mri-spine-lumbar-postoperative': (0, 1),
    'ra.aortic-aneurysm-rupture': (0, 1),
    'ra.thoracic-aorta-measurement': (0, 1, 3),
    'ra.vascular-anomalies': (0,),
    'ra.ct-tavi': (0, 1, 3),
    'mri.venogram': (0, 2),
    'ra.mri-sella': (0, 1, 3),
    'ra.ct-pancreatitis': (1,),
    'mri.both-hips': (0,),
    'ra.ct-lung-cancer': (0, 2),
    'ra.ct-cardiovascular-pearls': (0, 2),
    'ra.ct-mediastinum': (0, 2),
    'ra.paediatric-chest-ct': (0, 2),
})


def standard_acquisition(identifier, options):
    if identifier not in ROUTINE_INDICES:
        raise ValueError(f'Missing routine acquisition for {identifier}')
    return ' '.join(options[index] for index in ROUTINE_INDICES[identifier])
