"""Report acquisition choices. A choice records an acquisition the reader confirms."""
try:
    from tools.report_protocol_catalogue import ADDITIONAL_PROTOCOLS
except ModuleNotFoundError:
    from report_protocol_catalogue import ADDITIONAL_PROTOCOLS

CT = 'https://radiologyassistant.nl/more/ct-protocols/ct-contrast-injection-and-protocols'
MRI = 'https://radiopaedia.org/articles/mri-sequences-overview'
PE = 'https://radiopaedia.org/articles/ct-pulmonary-angiogram-protocol'
LI = 'https://radiologyassistant.nl/abdomen/liver/li-rads'

KNEE = (
    ('Knee MRI sequence set', (
        'Coronal T1 and STIR, sagittal 3D fat-suppressed PD, axial fat-suppressed PD and sagittal T2.',
        'Multiplanar T1-weighted and fluid-sensitive imaging in axial, coronal and sagittal planes.',
    )),
    ('https://radiologyassistant.nl/musculoskeletal/knee/meniscal-pathology', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11399221/', 'https://radiopaedia.org/articles/mri-of-the-knee-an-approach'),
)

# Profiles describe the series or phase to document. Actual scanner settings,
# dose, timing and additional acquisitions are supplied from the performed study.
PROFILES = [
    (('ra.mri-knee', 'msk.mri-knee-postoperative'), KNEE),
    (('ra.mri-shoulder', 'msk.mri-shoulder-postoperative'), (
        ('Shoulder sequence set', ('Axial, oblique coronal and oblique sagittal imaging with T1-weighted and fluid-sensitive sequences.',)),
        ('https://radiologyassistant.nl/musculoskeletal/shoulder/mri-anatomy', 'https://radiopaedia.org/articles/shoulder-protocol-mri'),
    )),
    (('ra.mri-ankle',), (
        ('Ankle sequence set', ('Multiplanar ankle imaging with T1-weighted and fat-suppressed fluid-sensitive sequences.',)),
        ('https://radiologyassistant.nl/musculoskeletal/ankle/mri-examination', MRI),
    )),
    (('ra.mri-prostate',), (
        ('Prostate sequence set', ('High-resolution T2-weighted imaging, high b-value DWI and ADC maps.', 'Dynamic postcontrast T1-weighted imaging.')),
        ('https://radiologyassistant.nl/abdomen/prostate/prostate-cancer-pi-rads-v2-1', 'https://radiopaedia.org/articles/prostate-mri-protocol'),
    )),
    (('ra.mri-rectal-cancer',), (
        ('Rectal sequence set', ('High-resolution multiplanar T2-weighted imaging including images perpendicular to the tumour axis, with DWI and ADC maps.',)),
        ('https://radiologyassistant.nl/abdomen/rectum/rectal-cancer-mr-staging-1-1', 'https://radiopaedia.org/articles/rectal-cancer-protocol-mri'),
    )),
    (('ra.mri-anal-cancer',), (
        ('Anal canal sequence set', ('High-resolution T2-weighted imaging in planes aligned with the anal canal.', 'DWI and ADC maps.')),
        ('https://radiologyassistant.nl/abdomen/anal-cancer-2/anal', MRI),
    )),
    (('ra.mri-epilepsy',), (
        ('Epilepsy sequence set', ('Volumetric T1-weighted and FLAIR imaging with high-resolution coronal T2-weighted images perpendicular to the hippocampal long axis.',)),
        ('https://radiologyassistant.nl/neuroradiology/epilepsy/role-of-mri', MRI),
    )),
    (('ra.mri-ms', 'ra.mri-myelopathy'), (
        ('Demyelination sequence set', ('Brain T2-weighted and FLAIR imaging.', 'Sagittal cord fluid-sensitive imaging with targeted axial T2-weighted images.')),
        ('https://radiologyassistant.nl/neuroradiology/multiple-sclerosis/diagnosis-and-differential-diagnosis-3-1', MRI),
    )),
    (('mri.brain-stroke', 'mri.brain-haemorrhage'), (
        ('Stroke or haemorrhage series', ('DWI and ADC maps.', 'FLAIR imaging.', 'Susceptibility-weighted or T2*-weighted imaging.', 'Intracranial MR angiography.')),
        ('https://radiologyassistant.nl/neuroradiology/brain-ischemia/imaging-in-acute-stroke', 'https://radiopaedia.org/articles/brain-screen-protocol-mri-1'),
    )),
    (('ct.liver-mass', 'ct.liver-lirads', 'ct.liver-lirads-calculated', 'ct.abdomen-multiphase'), (
        ('Liver or abdominal phases', ('Unenhanced series.', 'Late arterial phase.', 'Portal venous phase.', 'Delayed phase.')),
        (LI, CT),
    )),
    (('ra.ct-pancreatic-cancer', 'ra.ct-pancreatitis'), (
        ('Pancreatic and staging phases', ('Pancreatic parenchymal phase.', 'Portal venous phase.')), (CT,),
    )),
    (('ct.urography',), (
        ('Urinary tract phases', ('Unenhanced series.', 'Nephrographic phase.', 'Excretory phase.', 'Combined nephrographic and excretory phase after split-bolus injection.')),
        ('https://radiologyassistant.nl/abdomen/kidney/solid-masses', CT),
    )),
    (('ra.pulmonary-hypertension',), (
        ('Pulmonary angiography acquisition', ('Pulmonary arterial phase after IV iodinated contrast.', 'Bolus tracking in the pulmonary trunk.', 'Test bolus timing.')),
        (CT, PE),
    )),
    (('ra.ct-acute-aortic-syndrome', 'ra.aortic-aneurysm-rupture'), (
        ('Aortic acquisition', ('Unenhanced series.', 'Aortic arterial phase after IV iodinated contrast.', 'ECG-gated thoracic acquisition.', 'Delayed phase.')),
        ('https://radiologyassistant.nl/cardiovascular/thoracic-aorta/acute-aortic-syndrome', CT),
    )),
    (('ra.ct-abdominal-trauma', 'ct.trauma-panscan'), (
        ('Trauma phases', ('Arterial phase.', 'Portal venous phase.', 'Delayed excretory phase.')),
        ('https://radiologyassistant.nl/abdomen/acute-abdomen/ct-in-trauma', CT),
    )),
    (('ra.ct-bowel-ischaemia',), (
        ('Mesenteric phases', ('Unenhanced series.', 'Mesenteric arterial phase.', 'Portal venous phase.')), (CT,),
    )),
    (('ra.ct-tavi', 'ra.ct-coronary', 'ct.cardiac-mass'), (
        ('Cardiac acquisition', ('ECG-synchronised cardiac acquisition.', 'Arterial phase after IV iodinated contrast.', 'Delayed acquisition.', 'Arterial access-route coverage.')),
        ('https://radiologyassistant.nl/cardiovascular/thoracic-aorta/TAVI-TAVR', CT),
    )),
]

BY_ID = {identifier: profile for identifiers, profile in PROFILES for identifier in identifiers}
def report_protocol(exam):
    modality = exam.get('modality')
    if modality not in ('MRI', 'CT'):
        return None
    identifier = exam['id']
    if identifier in BY_ID:
        (label, options), sources = BY_ID[identifier]
        if identifier == 'msk.mri-knee-postoperative':
            options += ('Metal artefact reduction sequences.',)
        return {'label': label, 'options': options, 'sources': sources, 'study_specific': True}
    if identifier in ADDITIONAL_PROTOCOLS:
        return ADDITIONAL_PROTOCOLS[identifier]
    raise ValueError(f'Missing study-specific {modality} acquisition choices for {identifier}')
