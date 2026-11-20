"""Radiographs, spine injury, neck surveillance, femur CT and procedures: the headings report_structures_20261117.py writes.

Added 2026-11-19 so that studies of one kind read alike: every adult chest radiograph has the same seven
headings, a limb radiograph goes bones, alignment, joints, soft tissues, the spine injury studies share their
headings with classification last, and every procedure records consent and time-out under Procedure.
"""

CONTENT = r'''
# ---------------------------------------------------------------- chest radiographs: one list for every adult study

## @CXR_LUNGS
Lungs | Clear. | [Consolidation / Collapse / Nodule / Mass / Interstitial opacity] in the [ ]. | [Pulmonary oedema / Hyperinflation / Cavitation] [ ].

## @CXR_PLEURA
Pleura | No pleural effusion or pneumothorax. | [Small / Moderate / Large] [right / left / bilateral] pleural effusion. | [Right / Left] pneumothorax, [ ] cm at the level of the hilum.

## @CXR_HEART
Heart and mediastinum | Normal heart size and mediastinal contours. Central trachea. | [Cardiomegaly / Widened mediastinum / Tracheal deviation / Pneumomediastinum] [ ].

## @CXR_HILA
Hila | Normal. | [Hilar enlargement / Hilar lymphadenopathy / Hilar mass] on the [right / left / both sides] [ ].

## @CXR_DIAPHRAGM
Diaphragm | Normal. No free subdiaphragmatic gas. | [Right / Left / Bilateral] free subdiaphragmatic gas. | [Raised hemidiaphragm / Eventration / Hiatus hernia] [ ].

## @CXR_BONES
Bones and soft tissues | No acute bone abnormality. Normal soft tissues. | [Rib fracture / Vertebral fracture / Lytic lesion / Sclerotic lesion] [ ]. | [Subcutaneous emphysema / Soft tissue mass / Breast prosthesis] [ ].

## @CXR_LINES
Lines and devices | None. | [Endotracheal tube / Central venous catheter / Nasogastric tube / Pacemaker lead] tip [ ].

## @CXR
@CXR_LUNGS
@CXR_PLEURA
@CXR_HEART
@CXR_HILA
@CXR_DIAPHRAGM
@CXR_BONES
@CXR_LINES

## ra.chest-radiography
! Airways and cardiomediastinum
! Pleura and diaphragm
! Devices and bones
= Lungs
@CXR except Lungs

## xr.chest-immigration
= Lungs
= Pleura
@CXR_HEART
= Hila and mediastinum -> Hila | No hilar or mediastinal lymphadenopathy.
@CXR_DIAPHRAGM
! Heart and bones
@CXR_BONES
@CXR_LINES

## ra.tuberculosis
= Lungs
= Pleura
Heart and mediastinum | Normal heart size and mediastinal contours. Central trachea. | [Cardiomegaly / Pericardial effusion / Widened mediastinum] [ ].
= Hila and mediastinum -> Hila | No hilar or mediastinal lymphadenopathy.
@CXR_DIAPHRAGM
! Heart and bones
Bones and soft tissues | No acute bone abnormality. Normal soft tissues. | [Vertebral destruction / Rib lesion / Lytic lesion] [ ]. | [Paravertebral abscess / Soft tissue mass] [ ].
@CXR_LINES

## ra.cardiovascular-devices
= Cardiac device
= Valves and occluders
! Heart and lungs
@CXR except Lines and devices
= Lines and tubes

# ---------------------------------------------------------------- abdominal radiographs

## xr.abdomen
= Bowel gas pattern
= Free gas
= Calcification
= Soft tissues and bones -> Bones and soft tissues | No bone abnormality. Normal soft tissue outlines.
= Lines and devices

## xr.acute-abdomen-series
= Bowel gas pattern
= Free gas
= Calcification
= Chest
= Bones and soft tissues

# ---------------------------------------------------------------- spine radiographs

## xr.spine-cervical
= Alignment
= Odontoid and C1
= Vertebrae
= Discs and joints -> Discs and facet joints
= Prevertebral soft tissues

## xr.spine-thoracic
= Alignment
= Vertebrae
= Discs and joints -> Discs and facet joints
= Paraspinal lines

## xr.spine-lumbar
= Alignment
= Vertebrae
= Discs and facets -> Discs and facet joints
= Sacroiliac joints
Soft tissues | No abnormal soft tissue calcification. | [Aortic calcification / Aortic aneurysm / Renal calculus / Gallstone] [ ].

# ---------------------------------------------------------------- limb and girdle radiographs: bones, alignment, joints, soft tissues

## xr.knee
= Bones
= Alignment and patella
= Joint
= Soft tissues

## xr.shoulder
= Bones
= Glenohumeral joint
= Acromioclavicular joint
= Subacromial space and soft tissues

## xr.hip
= Proximal femur
= Pelvis
= Hip joint
= Soft tissues

## xr.scapula
= Scapula
= Bones -> Clavicle, humerus and ribs | No fracture or focal bone lesion.
= Glenohumeral joint
Soft tissues | Normal. | [Soft tissue swelling / Subcutaneous emphysema] [ ].

## xr.clavicle
= Clavicle
= Joints
= Lung apex and ribs
Soft tissues | Normal. | [Soft tissue swelling / Skin tenting / Subcutaneous emphysema] [ ].

## xr.ac-joints
= Bones
= Acromioclavicular joints
= Soft tissues

## xr.sternoclavicular
= Bones
= Alignment
Soft tissues | Normal. | [Soft tissue swelling / Retrosternal haematoma] [ ].

## xr.ankle-stress
= Mortise
= Talar tilt
= Anterior drawer
= Bones
Soft tissues | Normal. | Soft tissue swelling over the [lateral / medial] malleolus [ ].

## xr.sesamoid
= Sesamoids
= First metatarsophalangeal joint
Soft tissues | Normal. | [Soft tissue swelling / Foreign body] [ ].

# ---------------------------------------------------------------- spine injury: one list, classification last

## ra.cervical-spine-injury mri.cervical-spine-trauma
= Alignment
= Fracture -> Vertebrae | No fracture.
= Ligaments and discs
= Canal and cord
= Soft tissues and vessels
= Classification

## ra.thoracolumbar-injury
= Levels and alignment -> Alignment | Normal vertebral numbering and alignment.
= Vertebrae
= Posterior structures -> Posterior elements and ligaments | Intact posterior elements.
= Canal -> Canal and cord | No canal compromise.
= Associated findings -> Paraspinal and other injuries
Classification | No fracture to classify. | AO Spine [A0 / A1 / A2 / A3 / A4 / B1 / B2 / B3 / C] at [ ]; TLICS [ ].

## ra.thoracolumbar-fractures
= Alignment
= Vertebrae
= Posterior elements and ligaments
= Canal and cord | No canal compromise.
= Paraspinal and other injuries
= Classification

## mri.thoracolumbar-trauma
= Alignment
= Vertebrae
= Posterior elements and ligaments
= Canal and cord
= Paraspinal and other injuries
= Classification

# ---------------------------------------------------------------- neck after treatment: the rest of the neck as well

## neck.ct-post-treatment
= Primary site
= Neck -> Lymph nodes | No new or enlarging lymph node.
Pharynx and larynx | Normal. No mucosal mass. | Mass [ ] mm of the [nasopharynx / oropharynx / oral cavity / hypopharynx / larynx].
Salivary and thyroid glands | Normal. | [Salivary gland atrophy / Sialadenitis / Thyroid nodule] [ ].
Vessels | Patent carotid arteries and internal jugular veins. | [Carotid stenosis / Internal jugular vein thrombosis / Carotid blowout] [ ].
! Treatment effects and lung apices
Treatment effects | No osteoradionecrosis or soft tissue necrosis. | [Osteoradionecrosis / Soft tissue necrosis / Fistula / Laryngeal oedema] [ ].
Lung apices and bones | Clear lung apices. No destructive bone lesion. | [Lung nodule / Bone lesion] [ ].

## neck.mri-post-treatment
= Primary site
= Neck -> Lymph nodes | No new or enlarging lymph node.
Pharynx and larynx | Normal. No mucosal mass. | Mass [ ] mm of the [nasopharynx / oropharynx / oral cavity / hypopharynx / larynx].
Salivary and thyroid glands | Normal. | [Salivary gland atrophy / Sialadenitis / Thyroid nodule] [ ].
Vessels | Patent carotid arteries and internal jugular veins. | [Carotid stenosis / Internal jugular vein thrombosis] [ ].
= Treatment effects and skull base

# ---------------------------------------------------------------- neck ultrasound: the glands named as in every other neck study

## ra.cervical-lymph-nodes
= Right neck
= Left neck
= Thyroid and salivary glands -> Salivary and thyroid glands

## ra.paediatric-neck-masses
= Lesion
= Vascularity
= Lymph nodes
= Thyroid and salivary glands -> Salivary and thyroid glands

# ---------------------------------------------------------------- CT femur: each part by name, like the other CT joints

## ct.femur
! Fracture
! Bones
! Joints and soft tissues
> Bones
Femoral head and neck | No femoral head or neck fracture. | [Subcapital / Transcervical / Basicervical / Intertrochanteric] fracture [ ]. | [Lytic / Sclerotic] lesion [ ].
Femoral shaft | No femoral shaft fracture or focal bone lesion. | [Transverse / Oblique / Spiral / Comminuted / Atypical] fracture of the [proximal / mid / distal] femoral shaft [ ]. | [Lytic / Sclerotic] lesion [ ]; periosteal reaction [ ].
Distal femur | No distal femoral fracture. | [Supracondylar / Intercondylar / Condylar] fracture [ ].
> Joints
Hip joint | Congruent hip joint. | [Dislocation / Effusion / Joint space narrowing] [ ].
Knee joint | Congruent knee joint. No effusion. | [Effusion / Lipohaemarthrosis / Joint space narrowing] [ ].
>
Soft tissues | Normal. | [Haematoma / Mass / Gas / Foreign body] [ ].

# ---------------------------------------------------------------- procedures: target, procedure (consent and time-out), what it yields, complications

## ct.guided-biopsy
Target | Target lesion identified with a safe access route. | Lesion [ ] mm in the [ ]; route via [ ].
= Procedure
= Specimens
= Complications

## template:biopsy-safety-report
= Target
= Procedure | Informed consent obtained. Time-out completed. Needle tip confirmed in the target.
= Specimens
= Complications

## ra.ultrasound-joint-injection
= Target
= Injection -> Procedure | Informed consent obtained. Time-out completed. Needle tip confirmed within the joint; injectate distributed freely.
= Outcome -> Complications | No immediate complication. Aftercare advice given.

# ---------------------------------------------------------------- bone densitometry: one line for each site measured

## dxa.bone-densitometry
# Peter's own densitometry template (photo, 2026-11-20) names the sites and gives each one line to fill: BMD, T-score
# and a bracket. densitometry_dictation_20261120.py writes that line into the dictation layout.
! Lumbar spine
! Hips
! Interval change
Spine | Spine T-score at or above -1.0. | BMD = [ ], T-score = [ ] ([ ]). | Excluded vertebrae: [ ].
Left hip | Left hip T-score at or above -1.0. | BMD = [ ], T-score = [ ] ([ ]).
Left neck of femur | Left neck of femur T-score at or above -1.0. | BMD = [ ], T-score = [ ] ([ ]).
Right hip | Right hip T-score at or above -1.0. | BMD = [ ], T-score = [ ] ([ ]).
Right neck of femur | Right neck of femur T-score at or above -1.0. | BMD = [ ], T-score = [ ] ([ ]).
Forearm | Forearm T-score at or above -1.0. | [Right / Left] forearm: BMD = [ ], T-score = [ ] ([ ]).
'''
