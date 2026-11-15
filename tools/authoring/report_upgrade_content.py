"""Hand-written content for report_upgrade_20261115.py.

Protocol sources, in order of preference:
  Radiology Assistant  radiologyassistant.nl - CT contrast phases and timing ("CT contrast injection and
                       protocols"), and the protocol notes in its topic articles (rectal cancer, PI-RADS,
                       VI-RADS, LI-RADS, renal masses, acute aortic syndrome, CT in trauma, dementia,
                       epilepsy, multiple sclerosis, sella, elbow MRI, peripheral MRA, pulmonary emboli).
  Radiopaedia          radiopaedia.org protocol articles, for sequences the Radiology Assistant does not list.
CT phase timings are those of the Radiology Assistant: late arterial 35 s, portal venous 70 s,
nephrographic 100 s after injection.
"""
BLANK = ['[ ].']

# ------------------------------------------------------------------ CT techniques
CT_AP = 'Portal venous phase (70 s) after IV contrast, diaphragm to symphysis; coronal and sagittal reformats.'
CT_CAP = 'Portal venous phase (70 s) after IV contrast, lung apices to symphysis; coronal and sagittal reformats.'
CT_CHEST = 'Venous phase after IV contrast, thoracic inlet to adrenals; soft tissue and thin lung reconstructions.'
CT_CHEST_PLAIN = 'Unenhanced volumetric thin-section (1 mm) in full inspiration; lung and soft tissue reconstructions.'
CT_NECK = 'Venous phase after IV contrast, skull base to aortic arch; multiplanar soft tissue and bone reformats.'
CT_HEAD = 'Unenhanced, skull base to vertex; brain and bone reconstructions.'
CT_HEAD_TRAUMA = 'Unenhanced, skull base to vertex; brain, subdural and bone windows with multiplanar reformats.'
CT_BONE = 'Unenhanced; thin bone-kernel axial with sagittal, coronal and 3D reformats.'
CT_SPINE = 'Unenhanced; thin bone-kernel axial with sagittal and coronal reformats.'
CT_LIVER = 'Late arterial (35 s), portal venous (70 s) and delayed phases after IV contrast.'
CT_PAEDIATRIC = 'Single portal venous phase after weight-based IV contrast, low-dose paediatric settings.'

# ------------------------------------------------------------------ MRI protocols
MR_LIVER = ('T2 with and without fat-sat, in and opposed phase T1, DWI with ADC; dynamic T1 fat-sat before gadolinium '
            'and in late arterial, portal venous and delayed phases.')
MR_KIDNEY = 'Axial and coronal T2, in and opposed phase T1, DWI with ADC; dynamic T1 fat-sat before and after gadolinium with subtraction.'
MR_NECK = 'Axial and coronal T1 and T2 fat-sat, DWI with ADC; axial and coronal T1 fat-sat after gadolinium; skull base to thoracic inlet.'
MR_SPINE = 'Sagittal T1, T2 and STIR; axial T2 through the abnormal levels.'
MR_SPINE_POSTOP = 'Sagittal T1, T2 and STIR; axial T2; metal artefact reduction.'
MR_PAED_ABDOMEN = 'Coronal and axial T2 with and without fat-sat, axial T1, DWI with ADC; T1 fat-sat before and after gadolinium.'
MR_LIMB = 'Axial T1 and T2 fat-sat; coronal and sagittal STIR; skin marker at the site of symptoms.'
MR_KNEE = 'Coronal T1 and STIR, sagittal 3D fat-suppressed PD, axial fat-suppressed PD and sagittal T2.'
MR_SHOULDER = 'Axial PD fat-sat; oblique coronal T1, PD fat-sat and T2; oblique sagittal T1 and T2 fat-sat.'
MR_BRAIN = 'Sagittal T1, axial T2 and FLAIR, DWI with ADC, SWI.'
GAD = 'T1 fat-sat after gadolinium.'

PROTOCOLS = {
    # Abdomen and pelvis CT
    'ra.acute-abdomen': (CT_AP, ['Unenhanced, no IV contrast.']),
    'ct.appendix': CT_AP,
    'ra.ct-peritoneum': CT_AP,
    'ra.ct-bowel-wall': 'Portal venous phase (70 s) after IV contrast with neutral oral contrast; coronal and sagittal reformats.',
    'ra.ct-bowel-obstruction': ('Portal venous phase (70 s) after IV contrast, no positive oral contrast; coronal and sagittal reformats.',
                                ['Late arterial phase (35 s) for bowel wall enhancement.']),
    'ra.abdominal-wall-hernias': (CT_AP, ['Valsalva acquisition.']),
    'ra.ct-abdominal-trauma': ('Arterial and portal venous phases after IV contrast, diaphragm to symphysis.',
                               ['Excretory phase at 7 to 10 minutes for the urinary tract.']),
    'ra.ct-bowel-ischaemia': 'Unenhanced, arterial and portal venous (70 s) phases, diaphragm to symphysis; no positive oral contrast.',
    'ra.ct-small-bowel-tumours': 'Neutral oral contrast; enteric phase and portal venous phase (70 s) after IV contrast; coronal reformats.',
    'ct.colonography': 'Bowel preparation with faecal tagging; CO2 distension; unenhanced low-dose supine and prone acquisitions; 2D and 3D review.',
    'ra.ct-pancreatitis': 'Late arterial (35 s) phase through the pancreas and portal venous (70 s) phase through the abdomen and pelvis.',
    'ra.ct-pancreatic-cancer': ('Late arterial (35 s) phase through the pancreas and portal venous (70 s) phase through the abdomen and pelvis; '
                                'thin reformats along the vessels.'),
    'ra.ct-peritoneal-carcinomatosis': CT_CAP,
    'ct.liver-mass': 'Unenhanced, late arterial (35 s), portal venous (70 s) and delayed phases through the liver.',
    'ct.liver-lirads': CT_LIVER,
    'ct.liver-lirads-calculated': CT_LIVER,
    'ct.abdomen-multiphase': 'Unenhanced, late arterial (35 s), portal venous (70 s) and delayed phases, diaphragm to symphysis.',
    'ct.pelvis': 'Portal venous phase (70 s) after IV contrast, iliac crests to symphysis; coronal and sagittal reformats.',
    'ct.oncology-staging': 'Portal venous phase (70 s) after IV contrast, skull base to symphysis; lung, soft tissue and bone reconstructions.',
    'ra.recist': 'Portal venous phase (70 s) after IV contrast, lung apices to symphysis; sections of 5 mm or less.',
    'oncology.recist-follow-up': 'Portal venous phase (70 s) after IV contrast, lung apices to symphysis; matched to the baseline protocol.',
    'ct.paediatric-abdomen-solid': CT_PAEDIATRIC,
    'ra.paediatric-renal-tumours': CT_PAEDIATRIC,
    'ct.trauma-panscan': ('Unenhanced head and cervical spine; arterial phase chest and portal venous phase abdomen and pelvis '
                          'after IV contrast; spine reformats.'),
    'ct.guided-biopsy': 'Planning CT, intermittent CT guidance during needle placement and post-procedure CT.',
    # Urinary tract and adrenals
    'ct.kub': 'Unenhanced low-dose, kidneys to bladder base; coronal reformats.',
    'ct.urography': 'Unenhanced, then split-bolus combined nephrographic and excretory phase, kidneys to bladder base.',
    'ra.renal-cysts-bosniak': 'Unenhanced and nephrographic (100 s) phases through the kidneys.',
    'ra.solid-renal-masses': 'Unenhanced, corticomedullary (35 s) and nephrographic (100 s) phases through the kidneys.',
    'ra.adrenal-lesions': 'Unenhanced, portal venous (70 s) and 15-minute delayed phases through the adrenals for washout.',
    # Chest CT
    'ra.hrct-lung': ('Unenhanced volumetric thin-section (1 mm) supine in full inspiration, high-spatial-frequency reconstruction; expiratory series.',
                     ['Prone series for dependent opacity.']),
    'ra.ct-pulmonary-nodules': 'Unenhanced volumetric thin-section (1 mm); lung and soft tissue reconstructions with MIP.',
    'chest.ct-lung-screening': 'Unenhanced low-dose volumetric thin-section (1 mm) in full inspiration; lung reconstructions with MIP.',
    'oncology.lesion-growth': 'Unenhanced volumetric thin-section (1 mm), reconstruction matched to the prior study for volumetry.',
    'ra.ct-airways': 'Unenhanced volumetric thin-section in inspiration and dynamic expiration; multiplanar and minimum-intensity reformats.',
    'ra.ct-covid': CT_CHEST_PLAIN,
    'ra.ct-lung-cancer': 'Portal venous phase (70 s) after IV contrast, supraclavicular fossae to adrenals; thin lung reconstructions.',
    'ra.ct-mediastinum': CT_CHEST,
    'ra.thymus': CT_CHEST,
    'ra.ct-cardiovascular-pearls': CT_CHEST,
    'ra.paediatric-chest-ct': 'Low-dose single phase after weight-based IV contrast; multiplanar soft tissue and lung reformats.',
    'ra.paediatric-mediastinum': 'Low-dose single phase after weight-based IV contrast; multiplanar soft tissue and lung reformats.',
    'ra.pulmonary-hypertension': ('Pulmonary arterial phase with bolus tracking in the pulmonary trunk, caudocranial in shallow inspiration; '
                                  'MIP reformats.'),
    'ct.oesophagus': 'Oral water-soluble contrast immediately before scanning; portal venous phase after IV contrast, thoracic inlet to upper abdomen.',
    # Heart and vessels
    'ra.ct-coronary': 'Unenhanced calcium score, then ECG-gated arterial phase after IV contrast with sublingual nitrate and heart rate control.',
    'ct.calcium-score': 'Prospectively ECG-triggered unenhanced acquisition, 3 mm reconstructions, Agatston scoring.',
    'ct.cardiac-mass': 'ECG-gated arterial phase after IV contrast with a delayed phase to separate thrombus from slow flow.',
    'ra.ct-tavi': ('ECG-gated arterial phase of the aortic root and heart, then arterial phase of the aorta to the femoral heads; '
                   'systolic annulus reconstructions.'),
    'ra.thoracic-aorta-measurement': 'ECG-gated arterial phase after IV contrast; double-oblique reformats perpendicular to the centreline.',
    'ra.ct-acute-aortic-syndrome': ('Unenhanced chest, then arterial phase with bolus tracking from the thoracic inlet to the femoral heads, '
                                    'ECG-gated through the chest.', ['Venous phase.']),
    'ra.aortic-aneurysm-rupture': ('Unenhanced and arterial phase with bolus tracking, diaphragm to femoral heads.',
                                   ['Delayed phase for endoleak.']),
    'ra.vascular-anomalies': 'Arterial phase after IV contrast, thoracic inlet to diaphragm; multiplanar and 3D reformats.',
    'ct.angiogram-carotids': 'Arterial phase with bolus tracking, aortic arch to vertex; MIP and curved planar reformats.',
    'ct.angiogram-head-neck-tinnitus': 'Arterial phase with bolus tracking, aortic arch to vertex, with venous phase and temporal bone reconstructions.',
    'ct.angiogram-brain': 'Arterial phase with bolus tracking, skull base to vertex; thin source images, MIP and 3D reformats.',
    'ct.angiogram-lower-limbs': 'Arterial phase with bolus tracking, diaphragm to toes; MIP and curved planar reformats.',
    'ct.angiogram-upper-limb': 'Arterial phase with bolus tracking, aortic arch to fingertips, contralateral injection; MIP and curved planar reformats.',
    # Head and neck CT
    'neuro.ct-brain-routine': (CT_HEAD, ['Repeat after IV contrast.']),
    'ra.brain-anatomy': CT_HEAD,
    'ra.ct-traumatic-haemorrhage': CT_HEAD_TRAUMA,
    'template:head-trauma-report': CT_HEAD_TRAUMA,
    'ra.acute-stroke': 'Unenhanced head; CT angiogram from the aortic arch to the vertex; CT perfusion.',
    'ra.intracranial-haemorrhage': ('Unenhanced head, then CT angiogram of the intracranial arteries.', ['CT venogram.']),
    'ra.venous-sinus-thrombosis': 'Unenhanced head, then CT venogram in the venous phase, skull base to vertex; MIP reformats.',
    'ra.craniosynostosis': 'Unenhanced low-dose; bone-kernel reconstruction with 3D surface rendering of the vault and sutures.',
    'ra.ct-mri-eye': ('Thin axial sections through the orbits after IV contrast; coronal and sagittal soft tissue and bone reformats.',
                      ['Unenhanced, for trauma or foreign body.']),
    'ra.ct-temporal-bone': 'Unenhanced high-resolution (0.6 mm or less) bone-kernel acquisition; axial and coronal reformats of each side.',
    'ct.sinuses': 'Unenhanced low-dose; thin bone-kernel axial with coronal and sagittal reformats.',
    'ct.facial-bones': CT_BONE,
    'ct.tmj': 'Unenhanced, closed and open mouth; oblique sagittal and coronal bone reformats.',
    'ct.neck-nodes': CT_NECK,
    'ra.head-neck-malignancy': CT_NECK,
    'neck.ct-post-treatment': CT_NECK,
    # Spine and musculoskeletal CT
    'ra.cervical-spine-injury': 'Unenhanced, skull base to T1; thin bone-kernel axial with sagittal and coronal reformats.',
    'ra.thoracolumbar-fractures': CT_SPINE,
    'ra.thoracolumbar-injury': CT_SPINE,
    'msk.ct-spine-postoperative': 'Unenhanced with metal artefact reduction; bone and soft tissue reformats in three planes.',
    'ct.ankle-foot': CT_BONE, 'ct.elbow': CT_BONE, 'ct.femur': CT_BONE, 'ct.knee': CT_BONE, 'ct.shoulder': CT_BONE,
    'ct.hip': 'Unenhanced; thin bone-kernel axial with sagittal, coronal, oblique axial and 3D reformats.',
    'ct.pelvis-hips': 'Unenhanced; thin bone-kernel axial with sagittal, coronal and 3D reformats of the pelvis and both hips.',
    'ct.wrist-hand': 'Unenhanced; thin bone-kernel axial with sagittal, coronal and long-axis scaphoid reformats.',
    # Nuclear medicine with CT
    'template:pet-ct-report': 'FDG after a 6-hour fast; low-dose CT for attenuation correction and localisation, skull base to mid-thigh.',
    'template:theranostics-report': 'PSMA or SSTR ligand PET with low-dose CT for attenuation correction and localisation, vertex to mid-thigh.',

    # Abdomen and pelvis MRI
    'ra.biliary-duct-pathology': ('Axial and coronal T2, thick-slab 2D and 3D heavily T2-weighted MRCP, in and opposed phase T1.',
                                  ['Dynamic T1 fat-sat after gadolinium.']),
    'ra.liver-masses': (MR_LIVER, ['Hepatobiliary phase at 20 minutes with gadoxetate.']),
    'ra.liver-lirads': (MR_LIVER, ['Hepatobiliary phase at 20 minutes with gadoxetate.']),
    'liver.lirads-calculated': MR_LIVER,
    'ra.pancreatic-cysts': 'T2 with and without fat-sat, 2D and 3D MRCP, DWI with ADC; dynamic T1 fat-sat before and after gadolinium.',
    'ra.mri-crohn': ('Oral contrast distension and antiperistaltic agent; coronal and axial T2 with and without fat-sat, cine, DWI; '
                     'coronal T1 fat-sat before and after gadolinium.'),
    'ra.mri-perianal-fistula': ('Sagittal T2; oblique axial and coronal T2 with and without fat-sat aligned to the anal canal.',
                                [GAD]),
    'ra.mri-rectal-cancer': ('Sagittal T2, large-field axial T2, high-resolution (3 mm) oblique axial and coronal T2 perpendicular '
                             'and parallel to the tumour, DWI with ADC.'),
    'ra.mri-anal-cancer': ('Sagittal T2; high-resolution oblique axial and coronal T2 aligned to the anal canal; '
                           'large-field axial T2 including the inguinal nodes; DWI with ADC.'),
    'mri.renal-cyst': MR_KIDNEY, 'mri.renal-mass': MR_KIDNEY, 'mri.kidneys': MR_KIDNEY,
    'mri.adrenals': ('Axial in and opposed phase T1, axial and coronal T2, DWI with ADC.', ['Dynamic T1 fat-sat after gadolinium.']),
    'ra.mri-bladder': 'Distended bladder; T2 in three planes, DWI with ADC, dynamic T1 after gadolinium.',
    'ra.mri-prostate': ('T2 in three planes, high b-value DWI with ADC, dynamic contrast-enhanced T1; large-field T1 for nodes and bone.',
                        ['Biparametric, without dynamic contrast.']),
    'mri.female-pelvis': ('Sagittal, axial and coronal T2; axial T1 with and without fat-sat; DWI with ADC.', [GAD]),
    'mri.adnexal-mass': ('Sagittal, axial and coronal T2; axial T1 with and without fat-sat; DWI with ADC; '
                         'dynamic T1 fat-sat after gadolinium with time-intensity curves.'),
    'ra.mri-endometriosis': ('Sagittal, axial and oblique axial T2; axial T1 with and without fat-sat; antiperistaltic agent.',
                             ['Vaginal and rectal gel.', GAD]),
    'ra.mri-cervical-cancer': ('Sagittal T2; high-resolution oblique axial T2 perpendicular to the cervical canal; DWI with ADC; '
                               'large-field axial T2 to the renal hila.'),
    'ra.mri-endometrial-cancer': ('Sagittal T2; oblique axial T2 perpendicular to the endometrial cavity; DWI with ADC; '
                                  'dynamic T1 fat-sat after gadolinium; large-field axial T2 to the renal hila.'),
    'ra.mullerian-anomalies': 'Sagittal T2; oblique coronal T2 along the long axis of the uterus; axial T1 fat-sat; coronal T2 including the kidneys.',
    'mri.paediatric-abdomen-cystic': ('Coronal and axial T2 with and without fat-sat, axial T1, DWI with ADC.', [GAD]),
    'mri.paediatric-abdomen-solid': MR_PAED_ABDOMEN,
    'mri.paediatric-renal-tumour': MR_PAED_ABDOMEN,
    # Chest, heart and vessels MRI
    'mri.thymus': 'Axial T1, T2 fat-sat, in and opposed phase T1 for the chemical shift ratio, DWI with ADC; T1 fat-sat after gadolinium.',
    'mri.paediatric-mediastinum': 'ECG and respiratory gated; axial and coronal T2 fat-sat, axial T1, DWI with ADC; T1 fat-sat after gadolinium.',
    'ra.cardiac-masses': 'Cine SSFP, T1 and T2 with and without fat-sat, first-pass perfusion, early and late gadolinium enhancement.',
    'ra.mri-cardiomyopathy': ('Cine SSFP in long-axis views and a short-axis stack, native T1 and T2 mapping, late gadolinium enhancement, '
                              'post-contrast T1 mapping.'),
    'ra.mra-peripheral-vessels': 'Contrast-enhanced three-station MR angiogram, aorta to feet, with subtraction and MIP; time-resolved calf station.',
    'mri.angiogram-carotids': ('Contrast-enhanced MR angiogram from the aortic arch to the circle of Willis; time-of-flight through the bifurcations.',
                               ['Axial T1 fat-sat for dissection.']),
    'mri.angiogram-brain': '3D time-of-flight MR angiogram of the circle of Willis; source images and MIP.',
    'mri.venogram': ('T1, T2, FLAIR, DWI and SWI; contrast-enhanced MR venogram with MIP.', ['Phase-contrast venogram without gadolinium.']),
    'ra.mri-breast': 'Axial T2, DWI with ADC; dynamic T1 fat-sat before and after gadolinium with subtraction and kinetic curves.',
    'ra.breast-cancer-staging': ('Axial T2, DWI with ADC; dynamic T1 fat-sat before and after gadolinium with subtraction and kinetic curves; '
                                 'both axillae included.'),
    'ra.breast-implants': 'Axial T2; axial and sagittal silicone-only and silicone-suppressed sequences.',
    # Brain, head and neck MRI
    'neuro.mri-brain-routine': (MR_BRAIN, ['3D T1 after gadolinium.']),
    'mri.brain-anatomy': MR_BRAIN,
    'mri.brain-stroke': 'DWI with ADC, FLAIR, T2, SWI and time-of-flight MR angiogram.',
    'mri.brain-haemorrhage': ('T1, T2, FLAIR, DWI with ADC, SWI and time-of-flight MR angiogram.', ['T1 after gadolinium.']),
    'ra.mri-brain-tumours': 'T2, FLAIR, DWI with ADC, SWI, 3D T1 before and after gadolinium, perfusion.',
    'ra.mri-cns-enhancement': 'T2, FLAIR, DWI with ADC, SWI, 3D T1 before and after gadolinium.',
    'ra.mri-dementia': 'Sagittal 3D T1 with coronal reformats perpendicular to the hippocampus, axial FLAIR and T2, DWI, SWI.',
    'ra.mri-epilepsy': '3D T1, 3D FLAIR, coronal T2 and FLAIR perpendicular to the hippocampus, axial T2, DWI, SWI.',
    'ra.mri-ms': ('Sagittal 3D FLAIR, axial T2, DWI, SWI, 3D T1 after gadolinium.', ['Cord: sagittal T2 and STIR, axial T2.']),
    'ra.intracranial-hypotension': ('Brain: sagittal T1, axial FLAIR, 3D T1 after gadolinium. Whole spine: sagittal T2 and '
                                    'heavily T2-weighted 3D fat-sat for epidural fluid.'),
    'ra.mri-sella': 'Thin coronal and sagittal T1, coronal T2, dynamic coronal T1 and delayed T1 after gadolinium.',
    'ra.mri-trigeminal': ('Thin 3D heavily T2-weighted and 3D time-of-flight through the root entry zones; '
                          'T1 fat-sat after gadolinium to the skull base; whole-brain FLAIR.'),
    'ra.tinnitus': 'Thin 3D heavily T2-weighted through the internal auditory meati; axial T1 before and after gadolinium; whole-brain FLAIR.',
    'mri.orbits': 'Thin axial and coronal T1, coronal STIR, DWI; axial and coronal T1 fat-sat after gadolinium; whole-brain FLAIR.',
    'ra.mri-sinuses': 'Axial and coronal T1 and T2 fat-sat, DWI with ADC; T1 fat-sat after gadolinium in two planes.',
    'ra.mri-neck-spaces': MR_NECK, 'mri.neck-tumour': MR_NECK, 'neck.mri-post-treatment': MR_NECK,
    # Spine and plexus MRI
    'ra.mri-lumbar-disc': 'Sagittal T1, T2 and STIR; axial T2 from L3 to S1 and through any other abnormal level.',
    'neuro.mri-spine-cervical': 'Sagittal T1, T2 and STIR; axial T2 and gradient echo from C2 to T1.',
    'neuro.mri-spine-thoracic': 'Sagittal T1, T2 and STIR with a counting localiser; axial T2 through the abnormal levels.',
    'ra.mri-myelopathy': ('Sagittal T1, T2 and STIR; axial T2 through the abnormal levels.', ['T1 after gadolinium.']),
    'mri.thoracolumbar-trauma': 'Sagittal T1, T2 and STIR, T1 to sacrum; axial T2 through the injured levels.',
    'mri.cervical-spine-trauma': 'Sagittal T1, T2 and STIR; axial T2 and gradient echo through the injured levels.',
    'msk.mri-spine-cervical-postoperative': (MR_SPINE_POSTOP, ['T1 after gadolinium.']),
    'msk.mri-spine-thoracic-postoperative': (MR_SPINE_POSTOP, ['T1 after gadolinium.']),
    'msk.mri-spine-lumbar-postoperative': 'Sagittal T1, T2 and STIR; axial T2; sagittal and axial T1 before and after gadolinium; metal artefact reduction.',
    'msk.mri-lumbosacral-plexus': 'Coronal T1 and 3D STIR of the plexus; axial T1 and T2 fat-sat from L2 to the ischial tuberosities; DWI neurography.',
    'msk.mri-brachial-plexus': 'Coronal T1 and 3D STIR; sagittal T2 fat-sat from the roots to the axilla; axial T1 and T2 fat-sat; DWI neurography.',
    # Musculoskeletal MRI
    'ra.mri-knee': MR_KNEE,
    'msk.mri-knee-postoperative': MR_KNEE[:-1] + '; metal artefact reduction.',
    'ra.mri-shoulder': (MR_SHOULDER, ['MR arthrogram: T1 fat-sat in three planes with ABER.']),
    'msk.mri-shoulder-postoperative': MR_SHOULDER[:-1] + '; metal artefact reduction.',
    'ra.mri-elbow': 'T1 and T2 fat-sat in axial, coronal and sagittal planes.',
    'msk.mri-wrist': 'Coronal T1, PD fat-sat and 3D gradient echo; axial T1 and PD fat-sat; sagittal PD fat-sat.',
    'msk.mri-hand': 'Coronal T1 and STIR; axial T1 and PD fat-sat; sagittal PD fat-sat of the symptomatic ray.',
    'msk.mri-hip': ('Coronal T1 and STIR of the pelvis; coronal and sagittal PD fat-sat and oblique axial PD along the femoral neck.',
                    ['MR arthrogram: T1 fat-sat in three planes.']),
    'mri.both-hips': 'Coronal T1 and STIR of the pelvis; axial T2 fat-sat; sagittal PD of each femoral head.',
    'mri.bony-pelvis': ('Coronal T1 and STIR; axial T1 and T2 fat-sat; sagittal T2 fat-sat through the sacrum.', [GAD]),
    'msk.mri-sacroiliac': 'Oblique coronal T1 and STIR and oblique axial T2 fat-sat through both sacroiliac joints.',
    'ra.mri-ankle': 'Axial T1 and PD fat-sat; coronal PD fat-sat; sagittal T1 and STIR.',
    'msk.mri-foot': 'Short-axis T1 and T2 fat-sat; long-axis T1 and STIR; sagittal STIR.',
    'ra.mri-diabetic-foot': 'T1 and STIR in the short and long axis; sagittal T1 and STIR; T1 fat-sat before and after gadolinium.',
    'ra.mri-hamstring': ('Coronal T1 and STIR of the pelvis and thighs; axial T1 and T2 fat-sat from the ischial tuberosities; '
                         'sagittal T2 fat-sat of the injured side.'),
    'mri.forearm': (MR_LIMB, [GAD]),
    'mri.lower-leg': (MR_LIMB, [GAD]),
    'ra.mri-muscle-injury': 'Axial T1 and T2 fat-sat and long-axis STIR, both sides for comparison; skin marker at the site of symptoms.',
    'ra.mri-muscle-disease': 'Axial T1 and STIR of the pelvis, thighs and calves; coronal T1 and STIR.',
    'ra.stress-fractures': 'T1 and STIR in two planes through the symptomatic bone.',
    'ra.bone-tumours': ('T1 and STIR along the whole bone for skip lesions; axial T1 and T2 fat-sat; '
                        'T1 fat-sat before and after gadolinium; correlated with radiographs.'),
    'ra.cartilage-tumours': 'Long-axis T1 and STIR; axial T1 and T2 fat-sat; T1 fat-sat after gadolinium; correlated with radiographs.',
    'msk.mri-soft-tissue-mass': 'Skin marker; axial T1 and T2 fat-sat, long-axis T1 and STIR, DWI with ADC; T1 fat-sat before and after gadolinium.',
    'template:msk-mri-report': ('T1 and fluid-sensitive fat-sat sequences in at least two planes.', [GAD]),
    'mri.whole-body': 'Coronal T1 and STIR, vertex to toes; axial DWI with ADC; sagittal T1 and STIR of the whole spine.',
}

# ------------------------------------------------------------------ named review areas
UPPER_ABDOMEN = ('Upper abdomen and bones', 'Normal visualised upper abdomen. No destructive bone lesion.',
                 ['[Adrenal nodule / Liver lesion / Bone lesion / Fracture] [ ].'])
LUNGS_ABDOMEN = ('Lungs, pleura and upper abdomen', 'Clear lungs. No pleural effusion. Normal visualised upper abdomen.',
                 ['[Lung nodule / Pleural effusion / Upper abdominal finding] [ ].'])
OTHER_ORGANS = 'Other organs, lung bases and bones'
BASES = ' Clear lung bases. No destructive bone lesion.'
ABDOMEN_ALL = (OTHER_ORGANS, 'Normal liver, spleen, pancreas, adrenals, kidneys and pelvic organs.' + BASES, BLANK)
ABDOMEN_NOT_KIDNEYS = (OTHER_ORGANS, 'Normal liver, spleen, pancreas, adrenals, bowel and pelvic organs.' + BASES, BLANK)
LIVER_REST = ('Other upper abdominal organs', 'Normal gallbladder, pancreas, adrenals and kidneys. No lymphadenopathy.', BLANK)
BRAIN_REST = ('Ventricles, vessels and skull base', 'Normal ventricles and flow voids. Normal orbits, sinuses and mastoids.', BLANK)
PELVIS_REST = ('Other pelvic organs and bones', 'Normal bladder and reproductive organs. No bone lesion.', BLANK)
STROKE = ('Mass effect and background brain', 'No mass effect or midline shift. No old infarct or small vessel disease.',
          ['[Hyperdense vessel / Midline shift / Old infarct / Small vessel disease] [ ].'])
VENOUS = ('Skull base, sinuses and mastoids', 'Clear mastoids and paranasal sinuses. No skull base lesion.',
          ['[Mastoiditis / Sinusitis / Skull base lesion] [ ].'])
STRESS = ('Alternative cause of pain', 'None.', ['[Tumour / Osteomyelitis / Tendon injury] [ ].'])
GLANDS = ('Thyroid and salivary glands', 'Normal.', BLANK)

REVIEW_AREAS = {
    **{k: UPPER_ABDOMEN for k in ('ra.ct-pulmonary-nodules', 'oncology.lesion-growth', 'ra.ct-airways', 'ra.ct-covid',
                                  'ra.ct-mediastinum', 'ra.thymus', 'ra.pulmonary-hypertension', 'ra.paediatric-chest-ct',
                                  'ra.paediatric-mediastinum', 'ra.ct-cardiovascular-pearls')},
    'ra.hrct-lung': ('Upper abdomen, oesophagus and bones', 'Normal visualised upper abdomen and oesophagus. No destructive bone lesion.',
                     ['[Oesophageal dilatation / Hiatus hernia / Bone lesion] [ ].']),
    'chest.ct-lung-screening': ('Upper abdomen and bones', 'Normal visualised upper abdomen. No destructive bone lesion.',
                                ['Significant other finding (S): [ ].']),
    'ra.ct-lung-cancer': ('Heart and great vessels', 'Normal heart size. No pericardial effusion. Normal aorta and pulmonary arteries.',
                          ['[Pericardial effusion / Coronary calcification / Aortic aneurysm / Pulmonary embolism] [ ].']),
    **{k: ('Remaining chest', 'Clear visualised lungs. Normal heart and great vessels. No pleural effusion.', BLANK)
       for k in ('mri.thymus', 'mri.paediatric-mediastinum')},
    **{k: LUNGS_ABDOMEN for k in ('ct.cardiac-mass', 'ra.cardiac-masses', 'ra.mri-cardiomyopathy', 'ra.ct-tavi',
                                  'ra.thoracic-aorta-measurement', 'ra.vascular-anomalies')},
    'ra.ct-acute-aortic-syndrome': ('Chest, abdomen and bones', 'Clear lungs. Normal solid organs and bowel. No destructive bone lesion.', BLANK),
    'ra.aortic-aneurysm-rupture': ('Abdomen, pelvis and bones', 'Normal solid organs and bowel.' + BASES, BLANK),
    **{k: ABDOMEN_ALL for k in ('ra.ct-bowel-ischaemia', 'ra.ct-bowel-wall', 'ra.ct-bowel-obstruction', 'ra.ct-peritoneum',
                                'ra.abdominal-wall-hernias')},
    'ra.ct-small-bowel-tumours': (OTHER_ORGANS, 'Normal spleen, pancreas, adrenals, kidneys and pelvic organs.' + BASES, BLANK),
    'ra.ct-pancreatitis': (OTHER_ORGANS, 'Normal liver, spleen, adrenals, kidneys and bowel. No ascites.' + BASES,
                           ['[Ascites / Pleural effusion / Bowel involvement] [ ].']),
    'ct.kub': (OTHER_ORGANS, ABDOMEN_NOT_KIDNEYS[1], ['[Appendicitis / Diverticulitis / Adnexal mass / Aortic aneurysm] [ ].']),
    'ct.urography': ABDOMEN_NOT_KIDNEYS,
    'ra.renal-cysts-bosniak': ABDOMEN_NOT_KIDNEYS,
    'ra.adrenal-lesions': (OTHER_ORGANS, 'Normal liver, spleen, pancreas, kidneys and bowel.' + BASES, BLANK),
    'mri.renal-cyst': ('Other upper abdominal organs', 'Normal liver, spleen, pancreas and adrenals. No lymphadenopathy.', BLANK),
    'mri.adrenals': ('Other upper abdominal organs', 'Normal liver, spleen, pancreas and kidneys. No lymphadenopathy.', BLANK),
    **{k: ('Spleen, peritoneum and lymph nodes', 'Normal spleen. No ascites or lymphadenopathy.',
           ['[Splenomegaly / Ascites / Varices / Lymphadenopathy] [ ].']) for k in ('ra.liver-masses', 'ct.liver-mass')},
    **{k: LIVER_REST for k in ('ra.liver-lirads', 'liver.lirads-calculated', 'ct.liver-lirads', 'ct.liver-lirads-calculated')},
    'ra.mri-rectal-cancer': PELVIS_REST, 'ra.mri-anal-cancer': PELVIS_REST,
    'ra.recist': ('Non-measurable and incidental findings', 'None.', BLANK),
    **{k: ('Brain, neck and lung apices', 'Normal included brain, neck soft tissues and lung apices.', BLANK)
       for k in ('ct.angiogram-carotids', 'mri.angiogram-carotids')},
    'ra.carotid-obstruction': ('Thyroid and neck soft tissues', 'Normal.', BLANK),
    'xr.cartilage-lesion': ('Joints and alignment', 'Normal alignment. Preserved joint spaces.', BLANK),
    'ra.cartilage-tumours': ('Joint and neurovascular bundle', 'Not involved.', ['[Joint / Neurovascular] involvement [ ].']),
    'xr.stress-injury': STRESS, 'ra.stress-fractures': STRESS,
    'mri.brain-stroke': STROKE, 'ra.acute-stroke': STROKE,
    'mri.brain-haemorrhage': ('Background brain', 'No small vessel disease, old haemorrhage or microhaemorrhage.',
                              ['[Small vessel disease / Old haemorrhage / Microhaemorrhages / Superficial siderosis] [ ].']),
    'ra.intracranial-haemorrhage': ('Background brain', 'No small vessel disease or old haemorrhage.',
                                    ['[Small vessel disease / Old haemorrhage / Microhaemorrhages / Superficial siderosis] [ ].']),
    'mri.venogram': VENOUS, 'ra.venous-sinus-thrombosis': VENOUS,
    **{k: BRAIN_REST for k in ('ra.mri-brain-tumours', 'ra.mri-cns-enhancement', 'ra.mri-epilepsy', 'ra.mri-ms')},
    'ct.neck-nodes': GLANDS, 'ra.cervical-lymph-nodes': GLANDS,
    'ra.mri-neck-spaces': ('Brain, spine and lung apices', 'Normal included brain, cervical spine and lung apices.', BLANK),
    'neck.ct-post-treatment': ('Treatment effects and lung apices', 'No osteoradionecrosis or soft tissue necrosis. Clear lung apices.',
                               ['[Osteoradionecrosis / Soft tissue necrosis / Lung nodule] [ ].']),
    'neck.mri-post-treatment': ('Treatment effects and skull base', 'No osteoradionecrosis, perineural spread or skull base marrow change.',
                                ['[Osteoradionecrosis / Perineural spread / Skull base marrow change] [ ].']),
    'us.lower-limb-veins-bilateral': ('Superficial veins and popliteal fossae', 'Patent great saphenous veins. No Baker cyst.',
                                      ['[Superficial thrombophlebitis / Baker cyst] [ ].']),
    'us.venous-duplex-lower-limb': ('Popliteal fossa and soft tissues', "No Baker's cyst, haematoma or superficial thrombophlebitis.",
                                    ["[Baker's cyst / Superficial thrombophlebitis / Haematoma / Lymphadenopathy] [ ]."]),
    'cardiology.percutaneous-angiography': ('Anomalies and complications', 'No coronary anomaly, dissection or fistula.',
                                            ['[Chronic total occlusion / Collaterals / Dissection / Thrombus / Stent restenosis] [ ].']),
    'ra.mra-peripheral-vessels': ('Aneurysm and entrapment', 'No aneurysm, popliteal entrapment or cystic adventitial disease.',
                                  ['[Aneurysm / Popliteal entrapment / Cystic adventitial disease] [ ].']),
    'ra.hip-fai': ('Other pain generators', 'None.', ['[Os acetabuli / Herniation pit / Enthesopathy / Sacroiliitis] [ ].']),
    'msk.ultrasound-hip': ('Soft tissues', 'No mass or collection.', BLANK),
    'msk.mri-soft-tissue-mass': ('Satellite lesions and lymph nodes', 'None.', ['[Satellite lesion / Lymphadenopathy] [ ].']),
    'ra.mri-muscle-injury': ('Bone', 'No bone bruise or avulsion fracture.', ['[Bone bruise / Avulsion fracture / Myositis ossificans] [ ].']),
    'ra.mri-muscle-disease': ('Bones and joints', 'Normal marrow signal. No joint effusion.', BLANK),
    'ra.ultrasound-thyroid': ('Parathyroid and salivary glands', 'Normal.', ['[Parathyroid lesion / Salivary gland lesion] [ ].']),
    'ra.ultrasound-ddh': ('Joint and proximal femur', 'No effusion. Normal proximal femur.', ['[Effusion / Proximal femoral anomaly] [ ].']),
    'ra.paediatric-ultrasound-values': ('Bowel, pylorus and free fluid', 'No free fluid, mass or intussusception.',
                                        ['Pyloric muscle thickness [ ] mm, length [ ] mm.', '[Intussusception / Free fluid / Mass] [ ].']),
    'us.abdomen': ('Free fluid and lymph nodes', 'No free fluid or lymphadenopathy.', ['[Free fluid / Pleural effusion / Lymphadenopathy] [ ].']),
    'us.renal-bladder': ('Prostate and pelvis', 'No free fluid.', ['Prostate volume [ ] mL.']),
    'ra.mri-myelopathy': ('Vessels and paraspinal tissues', 'No perimedullary flow voids, epidural lesion or paraspinal mass.',
                          ['[Perimedullary flow voids / Epidural lesion / Paraspinal mass] [ ].']),
    'msk.mri-lumbosacral-plexus': ('Compressive causes', 'No compressive pelvic mass or spinal cause.',
                                   ['[Pelvic mass / Piriformis abnormality / Spinal stenosis] [ ].']),
    'msk.mri-brachial-plexus': ('Compressive causes', 'No cervical rib, apical mass or compressive lesion.',
                                ['[Cervical rib / Pancoast tumour / Fibrous band / Radiation change] [ ].']),
}

# First heading of the limb trauma radiographs: bones, not only fractures.
RENAMES = {k: {'Fracture': 'Bones'} for k in ('xr.ankle', 'ra.ankle-fractures', 'xr.foot', 'xr.toe', 'xr.knee')}

# ------------------------------------------------------------------ line rewrites (applied after the automatic passes)
REWRITES = {
    # Normal lines the automatic pass leaves awkward.
    'Normal. Normal craniocervical and atlantoaxial relationships.': 'Normal, including the craniocervical and atlantoaxial relationships.',
    # A leading blank becomes the finding's label.
    '[ ] Fr drain placed; [ ] mL of [ ] fluid aspirated.': 'Drain [ ] Fr placed; [ ] mL of [ ] fluid aspirated.',
    '[ ] G [core / FNA] needle, [ ] passes, from the [ ] approach.': 'Needle [ ] G [core / FNA], [ ] passes, [ ] approach.',
    '[ ] G needle at [ ], [ ] attempts. Opening pressure [ ] cm H2O.': 'Needle [ ] G at [ ], [ ] attempts. Opening pressure [ ] cm H2O.',
    '[ ] G needle in the [right / left] iliac fossa.': 'Needle [ ] G in the [right / left] iliac fossa.',
    '[ ] G needle, [anterior / posterior] approach; [ ] mL iodinated contrast and [ ] mL dilute gadolinium.':
        'Needle [ ] G, [anterior / posterior] approach; [ ] mL iodinated contrast and [ ] mL dilute gadolinium.',
    '[ ] G needle; [ ] mL iodinated contrast and [ ] mL dilute gadolinium.': 'Needle [ ] G; [ ] mL iodinated contrast and [ ] mL dilute gadolinium.',
    '[ ] G vacuum-assisted needle, [ ] cores; specimen radiograph [shows / does not show] the target calcification.':
        'Vacuum-assisted needle [ ] G, [ ] cores; specimen radiograph [shows / does not show] the target calcification.',
    '[ ] T2 lesions: [periventricular / juxtacortical / infratentorial] [ ].': 'T2 lesions [ ]: [periventricular / juxtacortical / infratentorial] [ ].',
    '[ ] [lobar / deep] microhaemorrhages; superficial siderosis [ ].': 'Microhaemorrhages [ ], [lobar / deep]; superficial siderosis [ ].',
    '[ ] arises from the [true / false] lumen [with / without] malperfusion.': 'Branch [ ] arises from the [true / false] lumen [with / without] malperfusion.',
    '[ ] at the site of maximal tenderness.': 'Finding at the site of maximal tenderness: [ ].',
    '[ ] catheter tip at [ ].': 'Catheter [ ], tip at [ ].',
    '[ ] communicated to [ ] at [ ].': 'Communicated [ ] to [ ] at [ ].',
    '[ ] enhancing lesions [ ].': 'Enhancing lesions [ ] at [ ].',
    '[ ] images; screening time [ ] s; dose-area product [ ].': 'Images [ ]; screening time [ ] s; dose-area product [ ].',
    '[ ] nerve [ ].': 'Nerve [ ]: [ ].',
    '[ ] new or enlarging T2 lesions since [ ].': 'New or enlarging T2 lesions [ ] since [ ].',
    '[ ] passes with a [ ] gauge [core / fine-needle] needle; [ ] cores obtained.': 'Needle [ ] gauge [core / fine-needle], [ ] passes; [ ] cores obtained.',
    '[ ] regurgitation, regurgitant fraction [ ] percent.': 'Regurgitation of the [ ] valve, regurgitant fraction [ ] percent.',
    '[ ] suspicious [mesorectal / lateral pelvic] nodes, largest [ ] mm.': 'Suspicious [mesorectal / lateral pelvic] nodes [ ], largest [ ] mm.',
    '[ ]: [protrusion / extrusion / calcified disc] with [mild / moderate / severe] canal stenosis.':
        'Level [ ]: [protrusion / extrusion / calcified disc] with [mild / moderate / severe] canal stenosis.',
    'Stenosis / Occlusion [ ] percent of the [ ] over [ ] cm.': '[Stenosis / Occlusion] of the [ ], [ ] percent, over [ ] cm.',
    # Over-long lines: shorter wording, or two lines.
    'Radiographs: [geographic with sclerotic margin / geographic without sclerotic margin / moth-eaten / permeative], [osteoid / chondroid / no] matrix, [no / solid / lamellated / spiculated / Codman] periosteal reaction.':
        ['Radiograph margin [geographic sclerotic / geographic non-sclerotic / moth-eaten / permeative]; matrix [osteoid / chondroid / none].',
         'Periosteal reaction [none / solid / lamellated / spiculated / Codman].'],
    '[Cystic / Spongiform / Mixed / Solid], [anechoic / hyperechoic / isoechoic / hypoechoic / very hypoechoic], [wider-than-tall / taller-than-wide], [smooth / lobulated / extrathyroidal extension], [no echogenic foci / macrocalcification / rim calcification / punctate echogenic foci].':
        ['Composition [cystic / spongiform / mixed / solid]; echogenicity [anechoic / hyperechoic / isoechoic / hypoechoic / very hypoechoic].',
         'Shape [wider-than-tall / taller-than-wide]; margin [smooth / lobulated / extrathyroidal extension].',
         'Echogenic foci [none / macrocalcification / rim calcification / punctate].'],
    '[Oval / Round / Irregular] mass [ ] mm with [circumscribed / obscured / microlobulated / indistinct / spiculated] margins in the [right / left] breast at [ ] o\'clock, [ ] cm from the nipple.':
        ['[Oval / Round / Irregular] mass [ ] mm, [circumscribed / obscured / microlobulated / indistinct / spiculated] margin.',
         "Site: [right / left] breast, [ ] o'clock, [ ] cm from the nipple."],
    '[Oval / Round / Irregular] mass [ ] mm with [circumscribed / irregular / spiculated] margins and [homogeneous / heterogeneous / rim] enhancement at [ ] o\'clock in the [right / left] breast.':
        ['[Oval / Round / Irregular] mass [ ] mm, [circumscribed / irregular / spiculated] margin, [homogeneous / heterogeneous / rim] enhancement.',
         "Site: [right / left] breast, [ ] o'clock."],
    '[Oval / Round / Irregular] [anechoic / hypoechoic / isoechoic / complex cystic and solid] mass [ ] x [ ] x [ ] mm at [ ] o\'clock, [ ] cm from the nipple.':
        "[Oval / Round / Irregular] [anechoic / hypoechoic / isoechoic / complex] mass [ ] x [ ] x [ ] mm at [ ] o'clock, [ ] cm from the nipple.",
    '[Parallel / Not parallel] orientation; [circumscribed / indistinct / angular / microlobulated / spiculated] margin; [enhancement / shadowing / no posterior features].':
        ['Orientation [parallel / not parallel]; margin [circumscribed / indistinct / angular / microlobulated / spiculated].',
         'Posterior features [none / enhancement / shadowing].'],
    'Category [A / C / D]: [almost entirely fatty / heterogeneously dense, which may obscure small masses / extremely dense, which lowers sensitivity].':
        'Category [A / C / D]: [almost entirely fatty / heterogeneously dense / extremely dense].',
    '[Amorphous / Coarse heterogeneous / Fine pleomorphic / Fine linear branching] calcifications, [grouped / linear / segmental / regional], [right / left] breast at [ ].':
        ['[Amorphous / Coarse heterogeneous / Fine pleomorphic / Fine linear branching] calcifications in the [right / left] breast at [ ].',
         'Distribution [grouped / linear / segmental / regional] over [ ] mm.'],
    'Typically benign [skin / vascular / popcorn / large rod-like / round / rim / dystrophic / milk of calcium / suture] calcifications.':
        'Typically benign calcifications: [ ].',
    '[L1-2 / L2-3 / L3-4 / L4-5 / L5-S1]: [bulge / protrusion / extrusion / sequestration], [central / right paracentral / left paracentral / foraminal / extraforaminal].':
        '[L1-2 / L2-3 / L3-4 / L4-5 / L5-S1]: [bulge / protrusion / extrusion / sequestration], [central / paracentral / foraminal / extraforaminal] [ ].',
    '[C2-3 / C3-4 / C4-5 / C5-6 / C6-7 / C7-T1]: [disc osteophyte complex / protrusion / extrusion] with [mild / moderate / severe] canal stenosis.':
        '[C2-3 / C3-4 / C4-5 / C5-6 / C6-7 / C7-T1]: [osteophyte complex / protrusion / extrusion], [mild / moderate / severe] canal stenosis.',
    '[Transverse / Oblique / Spiral / Comminuted / Segmental / Avulsion / Impacted] fracture of the [ ], [diaphyseal / metaphyseal / epiphyseal], [intra-articular / extra-articular].':
        ['[Transverse / Oblique / Spiral / Comminuted / Segmental / Avulsion] fracture of the [ ], [diaphyseal / metaphyseal / epiphyseal].',
         '[Intra-articular / Extra-articular]; [impacted / not impacted].'],
    '[Horizontal / Vertical / Radial / Complex / Bucket-handle / Root] tear of the [medial / lateral] meniscus, [posterior horn / body / anterior horn].':
        '[Horizontal / Vertical / Radial / Complex / Bucket-handle / Root] tear, [medial / lateral] meniscus [posterior horn / body / anterior horn].',
    '[Myofascial / Musculotendinous / Intratendinous] injury of the [biceps femoris long head / semitendinosus / semimembranosus], [ ] cm, BAMIC grade [ ].':
        '[Myofascial / Musculotendinous / Intratendinous] injury of the [biceps femoris / semitendinosus / semimembranosus], [ ] cm, BAMIC grade [ ].',
    '[Exophytic / Mesophytic / Endophytic] solid mass [ ] mm in the [upper pole / interpolar region / lower pole] of the [right / left] kidney.':
        '[Exophytic / Mesophytic / Endophytic] solid mass [ ] mm, [upper pole / interpolar region / lower pole], [right / left] kidney.',
    'Mass [ ] x [ ] x [ ] mm arising from the [upper pole / interpolar region / lower pole] of the [right / left] kidney, claw sign [present / absent].':
        'Mass [ ] x [ ] x [ ] mm, [upper pole / interpolar region / lower pole], [right / left] kidney; claw sign [present / absent].',
    '[Intersphincteric / Transsphincteric / Suprasphincteric / Extrasphincteric] fistula, internal opening at [ ] o\'clock, [ ] cm from the anal verge.':
        "[Intersphincteric / Transsphincteric / Suprasphincteric / Extrasphincteric] fistula; internal opening [ ] o'clock, [ ] cm from the verge.",
    '[Unilocular / Multilocular / Microcystic] cyst [ ] mm in the pancreatic [head / body / tail], [communicating / not communicating] with the duct.':
        '[Unilocular / Multilocular / Microcystic] cyst [ ] mm in the pancreatic [head / body / tail]; duct communication [present / absent].',
    'Nodule [ ] mm of the [right uterosacral ligament / left uterosacral ligament / torus uterinus / posterior vaginal fornix / rectosigmoid].':
        'Nodule [ ] mm of the [right uterosacral ligament / left uterosacral ligament / torus / posterior fornix / rectosigmoid].',
    '[Mild / Moderate / Severe] [right / left / bilateral] foraminal stenosis at [ ] with [contact / compression] of the exiting [ ] nerve root.':
        '[Mild / Moderate / Severe] [right / left / bilateral] foraminal stenosis at [ ]; exiting [ ] root [contacted / compressed].',
    '[Enhancing mural nodule / Thickened enhancing wall / Main duct 5 to 9 mm / Main duct 10 mm or more / Growth of 5 mm or more in 2 years] [ ].':
        '[Enhancing mural nodule / Thickened enhancing wall / Main duct 5 to 9 mm / Main duct 10 mm or more / Rapid growth] [ ].',
    '[Glomus tumour / Dural arteriovenous fistula / Sigmoid sinus diverticulum / Aberrant ICA / High jugular bulb / Venous sinus stenosis] [ ].':
        '[Glomus tumour / Dural AV fistula / Sigmoid sinus diverticulum / Aberrant ICA / High jugular bulb / Venous sinus stenosis] [ ].',
    '[Anechoic / Hypoechoic / Hyperechoic / Heterogeneous] lesion [ ] x [ ] x [ ] mm, [subcutaneous / intramuscular / intermuscular], [well-defined / ill-defined].':
        ['[Anechoic / Hypoechoic / Hyperechoic / Heterogeneous] lesion [ ] x [ ] x [ ] mm, [subcutaneous / intramuscular / intermuscular].',
         'Margin [well-defined / ill-defined].'],
    '[Inguinal / Femoral / Umbilical / Incisional / Spigelian / Lumbar / Obturator] hernia, defect [ ] cm.':
        '[Inguinal / Femoral / Umbilical / Incisional / Spigelian / Lumbar] hernia, defect [ ] cm.',
    '[Radial head / Radial neck / Olecranon / Coronoid / Supracondylar / Lateral condyle / Medial epicondyle] fracture [ ].':
        '[Radial head / Radial neck / Olecranon / Coronoid / Supracondylar / Condylar] fracture [ ].',
    'Calculus [ ] mm in the [right / left] [kidney / proximal ureter / mid ureter / distal ureter / VUJ] [with / without] hydronephrosis.':
        'Calculus [ ] mm, [right / left] [kidney / proximal ureter / mid ureter / distal ureter / VUJ], [with / without] hydronephrosis.',
    'Lesion [ ] mm in segment [ ] with [arterial hyperenhancement / washout / peripheral nodular enhancement / hepatobiliary phase hypointensity] [ ].':
        'Lesion [ ] mm in segment [ ]: [arterial hyperenhancement / washout / peripheral nodular enhancement / hepatobiliary hypointensity] [ ].',
    '[Reticulation / Honeycombing / Traction bronchiectasis / Ground-glass opacity], [subpleural basal / upper zone / peribronchovascular / diffuse] distribution.':
        '[Reticulation / Honeycombing / Traction bronchiectasis / Ground-glass opacity], [subpleural basal / upper zone / peribronchovascular / diffuse].',
    'Fracture of the [proximal / middle / distal] phalanx of the [thumb / index / middle / ring / little] finger, [intra-articular / extra-articular] [ ].':
        'Fracture of the [proximal / middle / distal] phalanx, [thumb / index / middle / ring / little] finger, [intra-articular / extra-articular].',
    '[Intra-articular / Extra-articular] distal radius fracture, [dorsal / volar] angulation [ ] degrees, radial height [ ] mm.':
        '[Intra-articular / Extra-articular] distal radius fracture; [dorsal / volar] tilt [ ] degrees, radial height [ ] mm.',
}
