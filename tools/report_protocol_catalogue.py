"""Acquisition options for the remainder of the MRI and CT catalogue.

Options describe individual acquired series or a named series set. They are
not default scanner prescriptions. Source links are ordered by preference.
"""

RA = 'https://radiologyassistant.nl/'
RP = 'https://radiopaedia.org/articles/'
CT = RA + 'more/ct-protocols/ct-contrast-injection-and-protocols'
BODY = RP + 'mri-sequences-overview'
BRAIN = RP + 'brain-screen-protocol-mri-1'
SPINE = RP + 'cervical-spine-protocol-mri'
CTA = RP + 'ct-angiography-of-the-cerebral-arteries-protocol'
RENAL = RA + 'abdomen/kidney/solid-masses'

# Explicit examination IDs avoid accidentally applying a protocol to a new study.
PROTOCOLS = [
    ('msk.mri-sacroiliac', 'SI joint series', (
        'Oblique coronal T1-weighted images through both SI joints.',
        'Oblique coronal and oblique axial fluid-sensitive images through both SI joints.',
    ), (RP + 'sacroiliac-joint-protocol-mri',)),
    ('mri.renal-cyst mri.renal-mass mri.kidneys', 'Renal MRI series', (
        'Renal T2-weighted and precontrast T1-weighted imaging.',
        'Dynamic renal postcontrast T1-weighted imaging.',
        'Subtraction images from matched precontrast and postcontrast acquisitions.',
        'Renal DWI and ADC maps.',
    ), (RENAL, BODY)),
    ('ra.mri-lumbar-disc', 'Lumbar disc and canal series', (
        'Sagittal lumbar T1- and T2-weighted images.',
        'Axial T2-weighted images through the assessed disc levels.',
        'Sagittal lumbar STIR or equivalent fat-suppressed fluid-sensitive images.',
    ), (RP + 'lumbar-spine-protocol-mri',)),
    ('neuro.mri-spine-cervical neuro.mri-spine-thoracic', 'Spine and cord series', (
        'Sagittal T1- and T2-weighted images through the named spinal region.',
        'Axial T2-weighted images through the assessed levels.',
        'Sagittal fat-suppressed fluid-sensitive images.',
    ), (SPINE,)),
    ('msk.mri-spine-cervical-postoperative msk.mri-spine-thoracic-postoperative msk.mri-spine-lumbar-postoperative',
     'Postoperative spine series', (
        'Sagittal T1- and T2-weighted images and axial T2-weighted images through operated levels.',
        'Fluid-sensitive images with metal artefact reduction.',
        'Precontrast and postcontrast T1-weighted imaging through the operative bed.',
    ), (SPINE,)),
    ('mri.thoracolumbar-trauma mri.cervical-spine-trauma', 'Spine trauma series', (
        'Sagittal T1, T2 and STIR or equivalent fluid-sensitive imaging through the injured region.',
        'Axial T2-weighted images at the levels of suspected injury.',
    ), (SPINE,)),
    ('msk.mri-lumbosacral-plexus msk.mri-brachial-plexus', 'Plexus neurography series', (
        'T1-weighted anatomical coverage of the named plexus and adjacent muscles.',
        'Multiplanar fat-suppressed fluid-sensitive imaging along the plexus.',
        'Volumetric fat-suppressed neurography with multiplanar reformats.',
        'Postcontrast fat-suppressed T1-weighted images through the plexus.',
    ), (RP + 'magnetic-resonance-neurography',)),
    ('mri.adrenals', 'Adrenal characterization series', (
        'In-phase and opposed-phase T1-weighted imaging through both adrenal glands.',
        'Adrenal T2-weighted images.',
        'Dynamic postcontrast T1-weighted images through the adrenal glands.',
    ), (RA + 'abdomen/unsorted/characterization-of-adrenal-lesions', BODY)),
    ('ra.mri-bladder', 'Bladder VI-RADS series', (
        'High-resolution multiplanar T2-weighted imaging through the bladder.',
        'Bladder DWI and ADC maps.', 'Dynamic postcontrast T1-weighted imaging of the bladder.',
    ), (RA + 'abdomen/bladder/bladder-cancer-vi-rads',)),
    ('msk.mri-soft-tissue-mass', 'Mass and local staging series', (
        'T1-weighted and fluid-sensitive images covering the entire mass and its anatomical compartment.',
        'High-resolution axial images through the mass and adjacent neurovascular structures.',
        'Precontrast and postcontrast fat-suppressed T1-weighted imaging through the mass.',
    ), (RP + 'soft-tissue-mass',)),
    ('mri.whole-body', 'Whole-body survey series', (
        'Whole-body T1-weighted anatomical survey.',
        'Whole-body STIR or equivalent fat-suppressed fluid-sensitive survey.',
        'Whole-body diffusion-weighted imaging with ADC maps.',
    ), (RP + 'whole-body-mri',)),
    ('neuro.mri-brain-routine mri.brain-anatomy', 'Brain survey series', (
        'Brain T1, T2 and FLAIR imaging.', 'Brain DWI and ADC maps.',
        'Susceptibility-weighted or T2*-weighted imaging.',
    ), (BRAIN,)),
    ('ra.mri-brain-tumours ra.mri-cns-enhancement', 'Brain lesion and enhancement series', (
        'Brain T2 and FLAIR imaging.', 'DWI and ADC maps.',
        'Matched precontrast and postcontrast volumetric T1-weighted imaging.',
        'Susceptibility-weighted imaging.', 'Perfusion imaging through the lesion.',
    ), (RA + 'neuroradiology/brain-tumor/systematic-approach', BRAIN)),
    ('ra.mri-breast', 'Breast lesion series', (
        'Bilateral T2-weighted imaging.',
        'Bilateral precontrast and dynamic postcontrast fat-suppressed T1-weighted imaging with subtraction.',
        'Breast DWI and ADC maps.',
    ), (RA + 'breast/bi-rads/bi-rads-for-mammography-and-ultrasound-2013', RP + 'breast-protocol-mri')),
    ('ra.mri-cardiomyopathy', 'Ventricular function and tissue series', (
        'ECG-synchronised cine images in long-axis views and a contiguous ventricular short-axis stack.',
        'Native myocardial T1 mapping.', 'Myocardial T2 mapping.',
        'Late gadolinium enhancement imaging in matching ventricular planes.',
        'Stress and rest myocardial perfusion imaging.',
    ), (RP + 'cardiac-mri-protocol',)),
    ('ra.mri-neck-spaces neck.mri-post-treatment mri.neck-tumour', 'Neck and nodal staging series', (
        'Multiplanar T1 and fat-suppressed T2-weighted imaging through the neck and nodal stations.',
        'Neck DWI and ADC maps.', 'Postcontrast fat-suppressed T1-weighted images through the neck.',
    ), (RA + 'head-neck/suprahyoid-neck/suprahyoid-neck-mr-pathology', BODY)),
    ('ra.mri-dementia', 'Atrophy and vascular burden series', (
        'Volumetric T1-weighted brain imaging with coronal reformats through the medial temporal lobes.',
        'Brain FLAIR imaging.', 'Susceptibility-weighted or T2*-weighted imaging.', 'DWI and ADC maps.',
    ), (RA + 'neuroradiology/dementia/role-of-mri', BRAIN)),
    ('mri.both-hips msk.mri-hip', 'Hip joint and marrow series', (
        'Coronal pelvis T1-weighted and fluid-sensitive survey.',
        'Small-field multiplanar imaging of the symptomatic hip.',
        'Oblique axial images along the femoral neck.',
        'Fat-suppressed T1-weighted imaging following intra-articular contrast.',
    ), (RP + 'hip-protocol-mri',)),
    ('ra.mri-crohn', 'MR enterography series', (
        'Small-bowel distension with oral enteric contrast.',
        'Axial and coronal T2-weighted bowel imaging including fat-suppressed images.',
        'Precontrast and postcontrast T1-weighted bowel imaging.',
        'Bowel DWI and ADC maps.', 'Cine imaging of bowel motility.',
    ), (RA + 'abdomen/bowel/crohn-s-disease', BODY)),
    ('mri.angiogram-brain', 'Intracranial arterial series', (
        'Intracranial 3D time-of-flight MR angiography.',
        'Source images and maximum-intensity projections of the intracranial arteries.',
        'Contrast-enhanced intracranial MR angiography.',
    ), (RP + 'time-of-flight-mr-angiography',)),
    ('mri.angiogram-carotids', 'Cervical arterial series', (
        'MR angiography covering the cervical carotid and vertebral arteries.',
        'Contrast-enhanced arterial acquisition from the aortic arch through the cervical vessels.',
        'Fat-suppressed T1-weighted vessel-wall images through the neck.',
    ), (RP + 'magnetic-resonance-angiography',)),
    ('ra.mra-peripheral-vessels', 'Peripheral arterial series', (
        'Contrast-enhanced arterial MR angiography of the requested vascular territory.',
        'Multistation arterial runoff acquisition.', 'Time-resolved distal arterial imaging.',
    ), (RA + 'cardiovascular/peripheral-mra/contrast-enhanced-mra-of-peripheral-vessels',)),
    ('ra.mri-diabetic-foot', 'Ulcer and marrow series', (
        'Small-field T1-weighted and fat-suppressed fluid-sensitive images covering the ulcer and adjacent bones.',
        'Postcontrast fat-suppressed T1-weighted imaging through the ulcer and deep tissues.',
    ), (RA + 'musculoskeletal/diabetic-foot/mri-examination', BODY)),
    ('ra.mri-muscle-injury ra.mri-muscle-disease ra.mri-hamstring mri.forearm mri.lower-leg',
     'Muscle compartment series', (
        'Axial T1-weighted and fat-suppressed fluid-sensitive images through the involved muscle compartments.',
        'Long-axis fluid-sensitive images through the symptomatic muscle and myotendinous junction.',
        'T1-weighted Dixon water and fat reconstructions.',
    ), (BODY,)),
    ('mri.bony-pelvis', 'Pelvic marrow series', (
        'Coronal T1-weighted and STIR or equivalent fluid-sensitive images covering the bony pelvis.',
        'Axial fluid-sensitive images through the symptomatic region.',
    ), (BODY,)),
    ('mri.thymus mri.paediatric-mediastinum', 'Mediastinal characterization series', (
        'Multiplanar T1- and T2-weighted imaging through the mediastinum.',
        'In-phase and opposed-phase T1-weighted images through the thymic bed.',
        'Postcontrast fat-suppressed T1-weighted imaging of the mediastinal lesion.',
    ), (RA + 'chest/thymic-masses/thymic-masses', BODY)),
    ('template:msk-mri-report', 'Regional musculoskeletal acquisition', (
        'T1-weighted images through the named structure.',
        'Orthogonal fluid-sensitive images through the named structure.',
        'Targeted small-field acquisition through the area of concern.',
    ), (BODY,)),
    ('mri.orbits', 'Orbital series', (
        'Small-field axial and coronal orbital T1-weighted images.',
        'Fat-suppressed T2 or STIR images along the optic nerves and through the chiasm.',
        'Axial and coronal postcontrast fat-suppressed T1-weighted images.',
    ), (RP + 'orbits-protocol-mri',)),
    ('mri.adnexal-mass mri.female-pelvis', 'Pelvic characterization series', (
        'Multiplanar pelvic T2-weighted imaging.',
        'T1-weighted imaging with and without fat suppression.',
        'Pelvic DWI and ADC maps.', 'Dynamic postcontrast pelvic T1-weighted imaging.',
    ), (RA + 'abdomen/ovarium/roadmap-to-evaluate-ovarian-cysts', BODY)),
    ('mri.paediatric-abdomen-cystic mri.paediatric-abdomen-solid mri.paediatric-renal-tumour',
     'Paediatric abdominal mass series', (
        'Multiplanar T2-weighted imaging covering the abdominal mass and its organ of origin.',
        'Precontrast T1-weighted imaging and DWI with ADC maps.',
        'Postcontrast T1-weighted imaging through the mass and adjacent vessels.',
    ), (BODY,)),
    ('ra.mri-perianal-fistula', 'Perianal tract series', (
        'Oblique axial and coronal T2-weighted images aligned to the anal canal.',
        'Fat-suppressed fluid-sensitive imaging including ischioanal and supralevator coverage.',
        'Postcontrast fat-suppressed T1-weighted imaging through the fistula tract.',
    ), (RA + 'abdomen/rectum/perianal-fistulas', BODY)),
    ('ra.mri-sella', 'Sellar series', (
        'Thin-section coronal and sagittal sellar T1-weighted images.',
        'Coronal T2-weighted imaging through the sella.',
        'Dynamic contrast-enhanced coronal pituitary imaging.',
        'Thin-section postcontrast sellar T1-weighted images.',
    ), (RP + 'pituitary-protocol-mri',)),
    ('ra.mri-sinuses', 'Sinonasal soft-tissue series', (
        'Multiplanar T1 and fat-suppressed T2-weighted imaging of the paranasal sinuses and skull base.',
        'Postcontrast fat-suppressed T1-weighted imaging through the sinonasal region.',
        'DWI and ADC maps through the lesion.',
    ), (BODY,)),
    ('ra.mri-trigeminal', 'Trigeminal nerve series', (
        'Thin-section 3D heavily T2-weighted images through the cisternal trigeminal nerves.',
        'Intracranial time-of-flight angiography through the root entry zones.',
        'Postcontrast T1-weighted imaging through Meckel caves and skull base.',
    ), (RP + 'trigeminal-neuralgia',)),
    ('ra.mri-endometriosis', 'Endometriosis mapping series', (
        'Multiplanar high-resolution pelvic T2-weighted imaging.',
        'Pelvic T1-weighted images with and without fat suppression.',
    ), (RA + 'abdomen/unsorted/endometriosis-mri-detection', BODY)),
    ('ra.mri-cervical-cancer', 'Cervical staging series', (
        'Small-field T2-weighted images aligned to the cervical canal.',
        'DWI and ADC maps matched to the tumour planes.',
        'Large-field pelvic survey including nodal stations.',
        'Postcontrast T1-weighted imaging through the cervix.',
    ), (RA + 'abdomen/unsorted/mr-in-cervical-cancer-1', BODY)),
    ('ra.mri-endometrial-cancer', 'Endometrial staging series', (
        'Sagittal and oblique axial T2-weighted images aligned to the uterine cavity.',
        'Uterine DWI and ADC maps.', 'Dynamic postcontrast T1-weighted imaging through the uterus.',
    ), (RA + 'abdomen/unsorted/mr-in-endometrial-cancer', BODY)),
    ('ra.intracranial-hypotension', 'Intracranial hypotension series', (
        'Sagittal brain T1 and axial FLAIR imaging.',
        'Postcontrast volumetric T1-weighted brain imaging.',
        'Heavily T2-weighted spinal survey for extradural fluid.',
    ), (RA + 'neuroradiology/white-matter-disease-1/spontaneous-intracranial-hypotension', BRAIN)),
    ('mri.venogram', 'Intracranial venous series', (
        'Intracranial time-of-flight or phase-contrast MR venography.',
        'Contrast-enhanced intracranial MR venography.',
        'Source images and venographic maximum-intensity projections.',
    ), (RP + 'mr-venography',)),
    ('ct.oesophagus', 'Oesophageal acquisition', (
        'Chest CT following oral water-soluble contrast.',
        'Postcontrast chest acquisition following IV iodinated contrast.',
        'Additional delayed images through the suspected leak.',
    ), (CT, RP + 'oesophageal-perforation')),
    ('ct.colonography', 'Colonography acquisition', (
        'Colonic distension with gas and supine low-dose acquisition.',
        'Prone or decubitus acquisition.',
        'Oral faecal tagging.', 'Postcontrast staging acquisition after IV iodinated contrast.',
    ), (RP + 'ct-colonography-protocol',)),
    ('ra.ct-small-bowel-tumours', 'Small-bowel lesion phases', (
        'Neutral oral enteric contrast for bowel distension.',
        'Enteric or late arterial phase after IV iodinated contrast.',
        'Portal venous phase through the abdomen and pelvis.',
    ), (RA + 'abdomen/bowel/small-bowel-tumors', RP + 'ct-enterography-protocol')),
    ('ra.ct-bowel-wall ra.ct-bowel-obstruction ct.appendix ra.abdominal-wall-hernias',
     'Acute abdominal acquisition', (
        'Portal venous phase abdomen and pelvis after IV iodinated contrast.',
        'Unenhanced abdomen and pelvis acquisition.',
        'Oral enteric contrast administered.',
    ), (CT,)),
    ('ra.ct-peritoneum ra.ct-peritoneal-carcinomatosis ct.pelvis ct.paediatric-abdomen-solid',
     'Abdominal or pelvic lesion coverage', (
        'Portal venous phase after IV iodinated contrast through the prescribed abdominal or pelvic coverage.',
        'Delayed postcontrast images through the region of concern.',
    ), (CT,)),
    ('ra.ct-lung-cancer ct.oncology-staging ra.ct-mediastinum ra.paediatric-chest-ct ra.ct-cardiovascular-pearls',
     'Chest and staging coverage', (
        'Postcontrast chest acquisition after IV iodinated contrast.',
        'Portal venous phase through the included abdomen and pelvis.',
        'Thin-section lung and soft-tissue reconstructions.',
    ), (CT,)),
    ('neck.ct-post-treatment ct.neck-nodes', 'Contrast neck acquisition', (
        'Postcontrast soft-tissue neck acquisition including cervical nodal stations.',
        'Multiplanar neck reformats.',
    ), (CT,)),
    ('ct.angiogram-brain', 'Intracranial CTA coverage', (
        'Arterial-phase CTA of the intracranial circulation after IV iodinated contrast.',
        'Thin source images and maximum-intensity projections.',
    ), (CT, CTA)),
    ('ct.angiogram-carotids ct.angiogram-head-neck-tinnitus', 'Head and neck vascular coverage', (
        'Arterial-phase CTA of the cervical and intracranial arteries after IV iodinated contrast.',
        'Arch-to-vertex coverage.', 'Additional venous-phase acquisition.',
    ), (CT, CTA)),
    ('ct.angiogram-lower-limbs ct.angiogram-upper-limb', 'Limb arterial coverage', (
        'Arterial-phase CTA after IV iodinated contrast through the named limb and its arterial inflow.',
        'Bolus tracking.', 'Additional delayed distal runoff acquisition.',
    ), (CT,)),
    ('ra.vascular-anomalies ra.thoracic-aorta-measurement', 'Thoracic vascular acquisition', (
        'Arterial phase after IV iodinated contrast.',
        'ECG-synchronised thoracic aortic acquisition.',
        'Delayed venous phase through the vascular anomaly.',
        'Double-oblique multiplanar aortic reformats.',
    ), (CT, RA + 'cardiovascular/thoracic-aorta/vascular-anomalies-of-aorta-pulmonary-and-systemic-vessels')),
    ('ct.guided-biopsy', 'Biopsy acquisition', (
        'Limited CT localization for needle planning.',
        'Serial CT images confirming needle position.',
        'Limited post-procedure CT assessment.',
    ), (RP + 'ct-guided-biopsy',)),
]

# Dedicated regional planning and reconstructions are kept distinct from
# vascular or IV-contrast choices.
JOINTS = {
    'ra.mri-elbow': ('elbow', 'axial, coronal and sagittal', RP + 'mri-of-the-elbow-an-approach'),
    'msk.mri-foot': ('foot', 'long- and short-axis', BODY),
    'msk.mri-wrist': ('wrist', 'axial, coronal and sagittal', RP + 'wrist-protocol-mri'),
    'msk.mri-hand': ('hand or symptomatic digits', 'orthogonal small-field', BODY),
}
for identifier, (region, planes, source) in JOINTS.items():
    PROTOCOLS.append((identifier, f'{region.capitalize()} MRI acquisition', (
        f'T1-weighted images through the {region}.',
        f'{planes.capitalize()} fluid-sensitive images through the {region}.',
    ), (source,)))

NONCONTRAST = {
    'ct.kub': ('urinary tract from kidneys to bladder', 'Thin axial and coronal urinary tract reconstructions.'),
    'ct.calcium-score': ('coronary arteries with ECG synchronisation', 'Coronary calcium scoring reconstruction.'),
    'ra.hrct-lung': ('lungs at full inspiration', 'Thin-section high-spatial-frequency reconstructions.', 'Expiratory series.', 'Prone inspiratory series.'),
    'chest.ct-lung-screening': ('lungs with a low-dose screening acquisition', 'Thin-section lung reconstructions.'),
    'ra.ct-traumatic-haemorrhage': ('head from skull base to vertex', 'Brain and bone reconstructions.'),
    'neuro.ct-brain-routine': ('head from skull base to vertex', 'Brain and bone reconstructions.'),
    'ct.sinuses': ('paranasal sinuses', 'Thin-section coronal and sagittal bone reformats.'),
    'ra.ct-temporal-bone': ('temporal bones', 'Small-field high-resolution bone reconstructions.'),
    'ct.facial-bones': ('facial bones', 'Multiplanar bone and soft-tissue reformats.'),
    'ct.tmj': ('temporomandibular joints', 'Closed-mouth acquisition.', 'Open-mouth acquisition.'),
    'ra.ct-pulmonary-nodules': ('lungs', 'Thin-section lung reconstructions for nodule comparison.'),
    'ra.ct-covid': ('lungs', 'Thin-section lung and soft-tissue reconstructions.'),
    'ra.ct-airways': ('tracheobronchial tree', 'Thin-section multiplanar airway reconstructions.', 'Expiratory airway series.'),
    'msk.ct-spine-postoperative': ('operated spinal levels', 'Multiplanar bone and soft-tissue reconstructions.', 'Metal artefact reduction reconstructions.'),
}
for identifier, region in {
    'ct.knee': 'knee', 'ct.ankle-foot': 'ankle and foot', 'ct.hip': 'hip', 'ct.femur': 'femur',
    'ct.elbow': 'elbow', 'ct.shoulder': 'shoulder', 'ct.wrist-hand': 'wrist and hand', 'ct.pelvis-hips': 'pelvis and hips',
}.items():
    NONCONTRAST[identifier] = (region, 'Thin-section bone reconstruction with orthogonal reformats.')

for identifier, (region, *reconstructions) in NONCONTRAST.items():
    PROTOCOLS.append((identifier, 'Acquisition and reconstruction',
                      (f'Unenhanced CT of the {region}.', *reconstructions), (CT,)))

ADDITIONAL_PROTOCOLS = {}
for identifiers, label, options, sources in PROTOCOLS:
    for identifier in identifiers.split():
        if identifier in ADDITIONAL_PROTOCOLS:
            raise ValueError(f'Duplicate protocol for {identifier}')
        ADDITIONAL_PROTOCOLS[identifier] = {
            'label': label, 'options': options, 'sources': sources, 'study_specific': True,
        }
