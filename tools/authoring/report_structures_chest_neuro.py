"""Chest, heart, vessels, brain, head and neck, spine and whole-body studies: the headings report_structures_20261117.py writes."""

CONTENT = r'''
# ---------------------------------------------------------------- CT chest: one list for every study of the region

## @CHEST_LUNGS
Lungs | Clear. No pulmonary nodule, mass or consolidation. | [Nodule / Mass / Consolidation / Ground-glass opacity] in the [ ], [ ] mm. | [Emphysema / Fibrosis / Bronchiectasis / Atelectasis] [ ].
Airways | Patent trachea and central bronchi. | [Bronchial wall thickening / Mucus plugging / Endobronchial lesion / Tracheal narrowing] [ ].
Pleura | No pleural effusion, thickening or pneumothorax. | [Small / Moderate / Large] [right / left / bilateral] pleural effusion. | [Pleural thickening / Pleural plaques / Pneumothorax] [ ].

## @CHEST_MEDIASTINUM
@MEDIASTINUM_HILA
@CHEST_NODES
@HEART
@GREAT_VESSELS
@OESOPHAGUS_THYROID

## @MEDIASTINUM_HILA
Mediastinum and hila | No mediastinal or hilar mass. | [Prevascular / Visceral / Paravertebral] mediastinal mass, [ ] mm.

## @CHEST_NODES
Lymph nodes | No mediastinal, hilar or axillary lymphadenopathy. | Enlarged [ ] lymph node, [ ] mm short axis.

## @HEART
Heart and pericardium | Normal heart size. No pericardial effusion. | [Cardiomegaly / Pericardial effusion / Coronary artery calcification / Valve calcification] [ ].

## @GREAT_VESSELS
Aorta and pulmonary arteries | Normal calibre thoracic aorta and pulmonary arteries. | [Aortic aneurysm / Aortic atherosclerosis / Enlarged pulmonary trunk] [ ] mm.

## @OESOPHAGUS_THYROID
Oesophagus and thyroid | Normal. | [Hiatus hernia / Oesophageal wall thickening / Thyroid nodule / Goitre] [ ].

## @CHEST_REST
Chest wall | Normal chest wall and axillae. | [Chest wall mass / Breast lesion / Gynaecomastia / Subcutaneous emphysema] [ ].
Upper abdomen | Normal visualised liver, spleen, adrenal glands and kidneys. | [Adrenal nodule / Liver lesion / Gallstones / Renal lesion] [ ].
Bones | No destructive bone lesion. | [Fracture / Lytic lesion / Sclerotic lesion / Degenerative change] [ ].

## ra.ct-mediastinum
@CHEST_LUNGS
= Mediastinum -> Mediastinum and hila | No mediastinal or hilar mass.
= Lymph nodes | No mediastinal, hilar or axillary lymphadenopathy.
@CHEST_MEDIASTINUM except Mediastinum and hila; Lymph nodes
@CHEST_REST

## ra.hrct-lung
= Interstitium
Nodules and airspaces | No nodule, consolidation or emphysema. | [Nodule / Consolidation / Emphysema / Cysts] in the [ ] [ ].
= Airways
Pleura | No pleural thickening, plaques or effusion. | [Pleural plaques / Pleural thickening / Pleural effusion] [ ].
@MEDIASTINUM_HILA
! Mediastinum and lymph nodes
Lymph nodes | No mediastinal or hilar lymphadenopathy. | [Mediastinal / Hilar] lymphadenopathy, [ ] mm short axis.
@HEART
= Pulmonary arteries and heart -> Aorta and pulmonary arteries | Normal calibre thoracic aorta and pulmonary arteries.
! Oesophagus
Oesophagus and thyroid | Normal. | [Oesophageal dilatation / Hiatus hernia] [ ]. | [Thyroid nodule / Goitre] [ ].
@CHEST_REST

## ra.ct-lung-cancer
= Primary tumour
Other lung nodules | No separate tumour nodule. | Separate tumour nodule in the [same / different ipsilateral / contralateral] lobe, [ ] mm.
= Background lungs
Airways | Patent trachea and central bronchi. | [Endobronchial tumour / Bronchial occlusion / Tracheal invasion] [ ].
Pleura | No pleural effusion or nodularity. | [Pleural effusion / Pleural nodularity] on the [right / left].
= Lymph nodes
! Heart and great vessels
@HEART
Aorta and pulmonary arteries | Normal calibre thoracic aorta and pulmonary arteries. No pulmonary embolism. | [Aortic aneurysm / Pulmonary embolism / Vascular invasion] [ ].
Oesophagus and thyroid | Normal. | [Oesophageal invasion / Hiatus hernia / Thyroid nodule] [ ].
Chest wall | No chest wall invasion. Normal axillae. | Chest wall invasion at the [ ]. | Axillary or supraclavicular lymph node [ ] mm.
Adrenal glands and liver | No adrenal or liver metastasis. | [Adrenal / Liver] metastasis [ ].
Bones | No bone metastasis. | [Lytic / Sclerotic] bone metastasis in the [ ].
= Stage

## ra.ct-pulmonary-nodules
= Nodules
! Lungs and airways
Lungs | No consolidation, emphysema or interstitial abnormality. | [Consolidation / Emphysema / Interstitial abnormality / Atelectasis] [ ].
Airways | Patent trachea and central bronchi. | [Bronchial wall thickening / Mucus plugging / Endobronchial lesion] [ ].
! Mediastinum and pleura
Pleura | No pleural effusion or thickening. | [Pleural effusion / Pleural thickening / Pleural plaques] [ ].
@CHEST_MEDIASTINUM
! Upper abdomen and bones
@CHEST_REST

## chest.ct-lung-screening
= Nodules
= Lungs
Airways | Patent trachea and central bronchi. | [Bronchial wall thickening / Mucus plugging / Endobronchial lesion] [ ].
Pleura | No pleural effusion or thickening. | [Pleural effusion / Pleural thickening / Pleural plaques] [ ].
! Mediastinum and lymph nodes
@MEDIASTINUM_HILA
@CHEST_NODES
= Coronary arteries
! Heart and aorta
@HEART
@GREAT_VESSELS
@OESOPHAGUS_THYROID
@CHEST_REST
= Lung-RADS

## oncology.lesion-growth
= Index nodule
= Other nodules
! Lungs and pleura
! Mediastinum and lymph nodes
! Heart and great vessels
Lungs | No consolidation, emphysema or interstitial abnormality. | [Consolidation / Emphysema / Interstitial abnormality / Atelectasis] [ ].
@CHEST_LUNGS except Lungs
@CHEST_MEDIASTINUM
@CHEST_REST

## ra.ct-airways
= Trachea and main bronchi
= Lobar and segmental bronchi
= Lungs
Pleura | No pleural effusion or thickening. | [Pleural effusion / Pleural thickening / Pneumothorax] [ ].
@CHEST_MEDIASTINUM
! Upper abdomen and bones
@CHEST_REST

## ra.ct-covid
= Lungs
Airways | Patent trachea and central bronchi. | [Bronchial wall thickening / Mucus plugging / Traction bronchiectasis] [ ].
@CHEST_LUNGS except Lungs; Airways
! Mediastinum and lymph nodes
! Heart and great vessels
@CHEST_MEDIASTINUM
@CHEST_REST
= CO-RADS

## ra.thymus
= Thymus
= Local extent
@CHEST_LUNGS except Pleura
! Pleura and lymph nodes
Pleura | No pleural nodule or effusion. | [Pleural drop metastasis / Pleural effusion / Pleural thickening] [ ].
@CHEST_NODES
! Heart and great vessels
@HEART
@GREAT_VESSELS
@OESOPHAGUS_THYROID
@CHEST_REST

## mri.thymus
= Thymus
= Local extent
Lungs | Clear. | [Lung nodule / Consolidation / Atelectasis] [ ].
! Pleura and lymph nodes
Pleura | No pleural nodule or effusion. | [Pleural drop metastasis / Pleural effusion / Pleural thickening] [ ].
Lymph nodes | No mediastinal or hilar lymphadenopathy. | Enlarged [ ] lymph node, [ ] mm short axis.
! Heart and great vessels
Heart and pericardium | Normal heart size. No pericardial effusion. | [Pericardial effusion / Pericardial invasion] [ ].
Aorta and pulmonary arteries | Normal calibre aorta and pulmonary arteries. No vascular encasement. | [Vascular encasement / SVC compression] [ ].
! Chest wall and bones
Chest wall | Normal chest wall and axillae. | [Chest wall invasion / Axillary lymphadenopathy] [ ].
Bones | Normal marrow signal. | [Bone lesion / Marrow infiltration] [ ].

## ra.pulmonary-hypertension
= Pulmonary arteries
= Heart and pericardium
Thoracic aorta | Normal calibre thoracic aorta. | [Aortic aneurysm / Aortic dissection / Atherosclerosis] [ ].
= Lungs
Airways | Patent trachea and central bronchi. | [Bronchial wall thickening / Mucus plugging / Bronchiectasis] [ ].
Pleura | No pleural effusion. | [Small / Moderate / Large] [right / left / bilateral] pleural effusion.
! Mediastinum and lymph nodes
@MEDIASTINUM_HILA
@CHEST_NODES
@OESOPHAGUS_THYROID
@CHEST_REST

## ra.paediatric-chest-ct
= Lungs
= Airways
Pleura | No pleural effusion or pneumothorax. | [Pleural effusion / Empyema / Pneumothorax] on the [right / left].
Thymus and mediastinum | Normal thymus for age. No mediastinal mass. | [Mediastinal mass / Thymic enlargement / Pneumomediastinum] [ ].
Lymph nodes | No hilar or mediastinal lymphadenopathy. | [Hilar / Mediastinal] lymphadenopathy, [ ] mm short axis.
! Heart and great vessels
Heart and pericardium | Normal heart size. No pericardial effusion. | [Cardiomegaly / Pericardial effusion / Congenital heart disease] [ ].
Aorta and pulmonary arteries | Normal aortic arch and pulmonary arteries. | [Vascular ring / Aberrant subclavian artery / Pulmonary artery sling / Right-sided aortic arch] [ ].
@OESOPHAGUS_THYROID
@CHEST_REST

## ra.paediatric-mediastinum
= Mediastinal mass
= Airway and vessels
= Lungs, pleura and pericardium
= Spinal canal
Lymph nodes | No hilar or mediastinal lymphadenopathy. | [Hilar / Mediastinal / Supraclavicular] lymphadenopathy, [ ] mm short axis.
! Upper abdomen and bones
@CHEST_REST

## mri.paediatric-mediastinum
= Mediastinal mass
= Airway and vessels
= Lungs, pleura and pericardium
= Spinal canal
Lymph nodes | No hilar or mediastinal lymphadenopathy. | [Hilar / Mediastinal / Supraclavicular] lymphadenopathy, [ ] mm short axis.
! Remaining chest
Heart and great vessels | Normal. | [Cardiomegaly / Pericardial effusion / Vascular anomaly] [ ].
Chest wall and bones | Normal chest wall and marrow signal. | [Chest wall invasion / Rib lesion / Vertebral lesion] [ ].
Upper abdomen | Normal visualised liver, spleen, adrenal glands and kidneys. | [Adrenal mass / Liver lesion / Renal lesion] [ ].

## ra.ct-cardiovascular-pearls
= Heart and pericardium
= Coronary arteries and valves
= Aorta and pulmonary arteries
@CHEST_LUNGS
! Mediastinum and lymph nodes
@MEDIASTINUM_HILA
@CHEST_NODES
@OESOPHAGUS_THYROID
@CHEST_REST

## ct.oesophagus
= Oesophagus
= Leak
= Lungs
@CHEST_LUNGS except Lungs
! Mediastinum and pleura
Mediastinum and hila | No mediastinal collection or fat stranding. | [Mediastinal collection / Mediastinal fat stranding] [ ], [ ] mm.
@CHEST_NODES
! Heart and great vessels
@HEART
@GREAT_VESSELS
! Chest wall and bones
@CHEST_REST except Upper abdomen; Bones
Stomach and upper abdomen | Normal visualised stomach, liver, spleen and adrenal glands. | [Hiatus hernia / Gastric wall thickening / Liver lesion / Subphrenic collection] [ ].
@CHEST_REST except Chest wall; Upper abdomen

# ---------------------------------------------------------------- heart

## cardiology.echocardiography
= Left ventricle
= Diastolic function
= Right ventricle
! Atria
Left atrium | Normal left atrial size. | Left atrial dilatation; LA volume index [ ] mL/m².
Right atrium | Normal right atrial size. | Right atrial dilatation; RA area [ ] cm².
Atrial and ventricular septa | Intact. | [Patent foramen ovale / Atrial septal defect / Ventricular septal defect / Atrial septal aneurysm] [ ].
! Valves
> Valves
Aortic valve | Trileaflet aortic valve without stenosis or regurgitation. | [Mild / Moderate / Severe] aortic [stenosis / regurgitation]. | Aortic valve peak velocity [ ] m/s, mean gradient [ ] mmHg, area [ ] cm². | [Bicuspid / Calcified / Bioprosthetic / Mechanical] aortic valve [ ].
Mitral valve | Normal mitral leaflets without stenosis or regurgitation. | [Mild / Moderate / Severe] mitral [stenosis / regurgitation]. | [Prolapse / Flail leaflet / Annular calcification / Bioprosthetic valve / Mechanical valve] [ ].
Tricuspid valve | Normal tricuspid valve without significant regurgitation. | [Mild / Moderate / Severe] tricuspid regurgitation; peak velocity [ ] m/s.
Pulmonary valve | Normal pulmonary valve without significant regurgitation. | [Mild / Moderate / Severe] pulmonary [stenosis / regurgitation].
>
! Pericardium and aorta
Aortic root and ascending aorta | Normal calibre aortic root and ascending aorta. | Aortic root [ ] mm; ascending aorta [ ] mm.
Pericardium | No pericardial effusion. | [Small / Moderate / Large] pericardial effusion [with / without] tamponade physiology.
= Inferior vena cava
Pulmonary artery pressure | Normal estimated pulmonary artery systolic pressure. | Estimated RVSP [ ] mmHg; tricuspid regurgitation velocity [ ] m/s.

## ra.ct-coronary
= Calcium score
= Coronary anatomy
! Left main and LAD
> Coronary arteries
Left main | No plaque or stenosis. | [Calcified / Partially calcified / Non-calcified] plaque in the left main with [minimal / mild / moderate / severe / occlusive] stenosis.
Left anterior descending and diagonals | No plaque or stenosis. | [Calcified / Partially calcified / Non-calcified] plaque in the [ ] with [minimal / mild / moderate / severe / occlusive] stenosis.
= Circumflex -> Circumflex and obtuse marginals
= Right coronary artery -> Right coronary artery and its branches
>
= High-risk plaque
! Heart and extracardiac findings
Cardiac chambers and valves | Normal cardiac chambers. No valve calcification. | [Chamber dilatation / Left ventricular hypertrophy / Valve calcification / Thrombus] [ ].
Pericardium | No pericardial effusion or thickening. | [Pericardial effusion / Pericardial thickening / Pericardial calcification] [ ].
Aorta and pulmonary arteries | Normal calibre visualised aorta and pulmonary arteries. | [Aortic aneurysm / Enlarged pulmonary trunk / Pulmonary embolism] [ ].
Lungs, pleura and upper abdomen | Clear visualised lungs. No pleural effusion. Normal visualised upper abdomen. | [Lung nodule / Pleural effusion / Hiatus hernia / Upper abdominal finding] [ ].
= CAD-RADS

## ct.calcium-score
! Calcium score
> Coronary calcium
Left main | No calcification. | Left main Agatston score [ ].
Left anterior descending | No calcification. | Left anterior descending Agatston score [ ].
Circumflex | No calcification. | Circumflex Agatston score [ ].
Right coronary artery | No calcification. | Right coronary artery Agatston score [ ].
>
Total calcium score | Agatston score 0. | Agatston score [ ] ([ ] percentile, MESA).
Aorta and valves | No aortic or valve calcification. | [Aortic valve / Mitral annular / Thoracic aortic] calcification [ ].
= Heart and pericardium
= Visible lungs and mediastinum

## ra.ct-tavi
= Aortic valve
= Annulus and LVOT
= Aortic root and coronary heights
! Access
> Access
Thoracic and abdominal aorta | No aneurysm, dissection or significant atheroma of the aorta. | [Aneurysm / Dissection / Shaggy atheroma / Porcelain aorta] of the [ ].
Right iliofemoral arteries | Suitable for transfemoral access. | Minimal luminal diameter [ ] mm on the right. | [Calcification / Tortuosity / Stenosis] of the right [common iliac / external iliac / common femoral] artery.
Left iliofemoral arteries | Suitable for transfemoral access. | Minimal luminal diameter [ ] mm on the left. | [Calcification / Tortuosity / Stenosis] of the left [common iliac / external iliac / common femoral] artery.
Subclavian arteries | Patent. | Minimal luminal diameter: right [ ] mm, left [ ] mm.
>
Cardiac chambers | No left atrial appendage or ventricular thrombus. | [Left atrial appendage thrombus / Left ventricular thrombus / Basal septal bulge] [ ].
= Lungs, pleura and upper abdomen

## ra.thoracic-aorta-measurement
! Aortic root and ascending aorta
! Arch and descending aorta
> Aortic diameters
Annulus and sinuses of Valsalva | Normal calibre aortic annulus and sinuses of Valsalva. | Annulus [ ] mm; sinuses of Valsalva [ ] mm.
Sinotubular junction | Normal calibre sinotubular junction. | Sinotubular junction [ ] mm.
Ascending aorta | Normal calibre ascending aorta. | Mid ascending aorta [ ] mm.
Aortic arch | Normal calibre aortic arch. | Proximal arch [ ] mm; distal arch [ ] mm. | Coarctation at the [ ].
Descending aorta | Normal calibre descending thoracic aorta. | Proximal descending aorta [ ] mm; at the diaphragm [ ] mm.
>
Arch branches | Normal three-vessel arch branching. Patent branch origins. | [Common origin of the brachiocephalic and left common carotid arteries / Aberrant right subclavian artery / Branch stenosis] [ ].
= Aortic wall
= Aortic valve
Heart and pericardium | Normal heart size. No pericardial effusion. | [Cardiomegaly / Pericardial effusion / Coronary artery calcification] [ ].
= Lungs, pleura and upper abdomen

## ra.ct-acute-aortic-syndrome
= Aortic wall
= Aortic calibre
! Branch vessels
> Branch vessels
Coronary arteries and aortic valve | No involvement of the coronary arteries or aortic valve. | Dissection flap involves the [right / left] coronary ostium. | Aortic valve [involvement / regurgitation].
Arch branches | Normal perfusion of the brachiocephalic, left common carotid and left subclavian arteries. | [Brachiocephalic / Left common carotid / Left subclavian] artery arises from the [true / false] lumen [with / without] malperfusion.
Coeliac axis and mesenteric arteries | Normal perfusion of the coeliac axis and mesenteric arteries. | [Coeliac axis / SMA / IMA] arises from the [true / false] lumen [with / without] malperfusion.
Renal arteries | Normal perfusion of both renal arteries. | [Right / Left] renal artery arises from the [true / false] lumen [with / without] malperfusion.
Iliac arteries | Normal perfusion of both iliac arteries. | Dissection extends into the [right / left] [common / external] iliac artery.
>
= Complications
! Chest, abdomen and bones
Lungs and pleura | Clear lungs. No pleural effusion. | [Pleural effusion / Consolidation / Lung nodule] [ ].
@ABDOMEN_BRIEF except Lung bases and bones
Bones | No destructive bone lesion. | [Fracture / Bone lesion] [ ].

## ra.aortic-aneurysm-rupture
= Abdominal aorta
= Rupture
! Branch and iliac arteries
Renal and visceral arteries | Patent coeliac axis, mesenteric and renal arteries. | [Accessory renal artery / Branch stenosis / Branch occlusion] [ ].
Right iliac arteries | Normal calibre right common, internal and external iliac arteries. | Right common iliac aneurysm [ ] mm. | [Stenosis / Occlusion / Tortuosity] of the right [common / external] iliac artery.
Left iliac arteries | Normal calibre left common, internal and external iliac arteries. | Left common iliac aneurysm [ ] mm. | [Stenosis / Occlusion / Tortuosity] of the left [common / external] iliac artery.
! Abdomen, pelvis and bones
@ABDOMEN_BRIEF

# ---------------------------------------------------------------- arteries and veins

## ra.carotid-obstruction
! Right carotid
! Left carotid
! Vertebral arteries
> Right carotid
Right common carotid artery | No plaque or stenosis. | [Echogenic / Hypoechoic / Calcified / Ulcerated] plaque in the right common carotid artery. | Intima-media thickness [ ] mm.
Right internal carotid artery | No plaque or stenosis. | ICA PSV [ ] cm/s, EDV [ ] cm/s, ICA/CCA ratio [ ]; [less than 50 / 50 to 69 / 70 to 99] percent stenosis. | [Echogenic / Hypoechoic / Calcified / Ulcerated] plaque at the right carotid bulb. | [Occlusion / Near occlusion / Dissection] of the right internal carotid artery.
Right external carotid artery | No plaque or stenosis. | Stenosis of the right external carotid artery.
> Left carotid
Left common carotid artery | No plaque or stenosis. | [Echogenic / Hypoechoic / Calcified / Ulcerated] plaque in the left common carotid artery. | Intima-media thickness [ ] mm.
Left internal carotid artery | No plaque or stenosis. | ICA PSV [ ] cm/s, EDV [ ] cm/s, ICA/CCA ratio [ ]; [less than 50 / 50 to 69 / 70 to 99] percent stenosis. | [Echogenic / Hypoechoic / Calcified / Ulcerated] plaque at the left carotid bulb. | [Occlusion / Near occlusion / Dissection] of the left internal carotid artery.
Left external carotid artery | No plaque or stenosis. | Stenosis of the left external carotid artery.
> Vertebral and subclavian arteries
Right vertebral artery | Antegrade flow in the right vertebral artery. | [Retrograde / Absent / Biphasic] flow in the right vertebral artery.
Left vertebral artery | Antegrade flow in the left vertebral artery. | [Retrograde / Absent / Biphasic] flow in the left vertebral artery.
Subclavian arteries | Normal triphasic subclavian waveforms. | [Right / Left] subclavian [stenosis / steal].
>
= Thyroid and neck soft tissues

## ct.angiogram-carotids mri.angiogram-carotids
! Right carotid
! Left carotid
! Vertebral arteries
Aortic arch and branch origins | Normal arch with patent branch origins. | [Common origin of the brachiocephalic and left common carotid arteries / Aberrant right subclavian artery / Origin stenosis] [ ].
> Right carotid
Right common carotid artery | No plaque or stenosis. | [Calcified / Soft / Mixed] plaque in the right common carotid artery [ ].
Right internal carotid artery | No plaque or stenosis. | [Calcified / Soft / Mixed] plaque at the right carotid bulb with [ ] percent stenosis (NASCET). | [Occlusion / Near occlusion / Dissection / Web] of the right internal carotid artery.
Right external carotid artery | No plaque or stenosis. | Stenosis of the right external carotid artery.
> Left carotid
Left common carotid artery | No plaque or stenosis. | [Calcified / Soft / Mixed] plaque in the left common carotid artery [ ].
Left internal carotid artery | No plaque or stenosis. | [Calcified / Soft / Mixed] plaque at the left carotid bulb with [ ] percent stenosis (NASCET). | [Occlusion / Near occlusion / Dissection / Web] of the left internal carotid artery.
Left external carotid artery | No plaque or stenosis. | Stenosis of the left external carotid artery.
> Vertebral and subclavian arteries
Right vertebral artery | Patent. | [Stenosis / Occlusion / Dissection / Hypoplasia] of the right vertebral artery at [ ].
Left vertebral artery | Patent. | [Stenosis / Occlusion / Dissection / Hypoplasia] of the left vertebral artery at [ ].
Subclavian arteries | Patent. | [Right / Left] subclavian artery [stenosis / occlusion].
>
Intracranial arteries | Patent. | [Stenosis / Occlusion / Aneurysm] of the [ ].
= Brain, neck and lung apices

## ct.angiogram-brain mri.angiogram-brain
= Internal carotid arteries
! Cerebral arteries
Anterior cerebral arteries | Patent anterior cerebral and anterior communicating arteries. | [Stenosis / Occlusion / Hypoplasia] of the [right / left] [A1 / A2] segment.
Middle cerebral arteries | Patent M1 and M2 segments of the middle cerebral arteries. | [Stenosis / Occlusion] of the [right / left] [M1 / M2] segment.
Posterior cerebral arteries | Patent posterior cerebral and posterior communicating arteries. | [Stenosis / Occlusion / Fetal origin] of the [right / left] posterior cerebral artery.
= Vertebrobasilar arteries
= Aneurysm
= Vascular malformation
Brain | Normal. | [Infarct / Haemorrhage / Mass] [ ].

## ct.angiogram-lower-limbs
! Aorta and iliac arteries
! Femoropopliteal arteries
! Crural arteries
Aorta | Normal calibre abdominal aorta. | [Aneurysm / Stenosis / Occlusion] of the [infrarenal / suprarenal] aorta [ ].
Renal and mesenteric arteries | Patent. | [Coeliac / Superior mesenteric / Inferior mesenteric / Renal] artery [stenosis / occlusion].
> Right leg
Right iliac arteries | Patent right common, internal and external iliac arteries. | [Stenosis / Occlusion / Aneurysm] of the right [common / internal / external] iliac artery, [ ] percent, over [ ] cm.
Right femoral arteries | Patent right common femoral, profunda and superficial femoral arteries. | [Stenosis / Occlusion] of the right [common femoral / profunda / superficial femoral] artery, [ ] percent, over [ ] cm.
Right popliteal artery | Patent. | [Stenosis / Occlusion / Aneurysm] of the right popliteal artery [ ].
Right crural arteries | Three-vessel run-off to the right ankle. | Right [anterior tibial / posterior tibial / peroneal] artery [stenosis / occlusion] [ ].
> Left leg
Left iliac arteries | Patent left common, internal and external iliac arteries. | [Stenosis / Occlusion / Aneurysm] of the left [common / internal / external] iliac artery, [ ] percent, over [ ] cm.
Left femoral arteries | Patent left common femoral, profunda and superficial femoral arteries. | [Stenosis / Occlusion] of the left [common femoral / profunda / superficial femoral] artery, [ ] percent, over [ ] cm.
Left popliteal artery | Patent. | [Stenosis / Occlusion / Aneurysm] of the left popliteal artery [ ].
Left crural arteries | Three-vessel run-off to the left ankle. | Left [anterior tibial / posterior tibial / peroneal] artery [stenosis / occlusion] [ ].
>
= Collaterals and grafts
@ABDOMEN_BRIEF

## ra.mra-peripheral-vessels
! Aorta and iliac arteries
! Femoropopliteal arteries
! Crural arteries
Aorta | Normal calibre abdominal aorta. | [Aneurysm / Stenosis / Occlusion] of the [infrarenal / suprarenal] aorta [ ].
> Right leg
Right iliac arteries | Patent right common, internal and external iliac arteries. | [Stenosis / Occlusion / Aneurysm] of the right [common / internal / external] iliac artery, [ ] percent, over [ ] cm.
Right femoral arteries | Patent right common femoral, profunda and superficial femoral arteries. | [Stenosis / Occlusion] of the right [common femoral / profunda / superficial femoral] artery, [ ] percent, over [ ] cm.
Right popliteal artery | Patent. | [Stenosis / Occlusion / Aneurysm] of the right popliteal artery [ ].
Right crural arteries | Three-vessel run-off to the right foot. | Right [anterior tibial / posterior tibial / peroneal] artery [stenosis / occlusion] [ ].
> Left leg
Left iliac arteries | Patent left common, internal and external iliac arteries. | [Stenosis / Occlusion / Aneurysm] of the left [common / internal / external] iliac artery, [ ] percent, over [ ] cm.
Left femoral arteries | Patent left common femoral, profunda and superficial femoral arteries. | [Stenosis / Occlusion] of the left [common femoral / profunda / superficial femoral] artery, [ ] percent, over [ ] cm.
Left popliteal artery | Patent. | [Stenosis / Occlusion / Aneurysm] of the left popliteal artery [ ].
Left crural arteries | Three-vessel run-off to the left foot. | Left [anterior tibial / posterior tibial / peroneal] artery [stenosis / occlusion] [ ].
>
= Aneurysm and entrapment

## ct.angiogram-upper-limb
Aortic arch and branch origins | Normal arch with patent branch origins. | [Aberrant right subclavian artery / Origin stenosis / Arch atheroma] [ ].
= Subclavian and axillary arteries
= Brachial artery
= Forearm arteries -> Radial and ulnar arteries
Palmar arches and digital arteries | Patent. | [Incomplete palmar arch / Digital artery occlusion] [ ].
Lung apex, soft tissues and bones | Clear lung apex. No soft tissue or bone abnormality. | [Cervical rib / Haematoma / Fracture / Soft tissue mass] [ ].

## us.venous-duplex-lower-limb
! Femoral and popliteal veins
> Deep veins
Common femoral vein | Fully compressible common femoral vein with spontaneous, phasic flow. | [Occlusive / Non-occlusive] [acute / chronic] thrombus in the common femoral vein, extending [ ].
Femoral and deep femoral veins | Fully compressible femoral and deep femoral veins. | [Occlusive / Non-occlusive] [acute / chronic] thrombus in the [femoral / deep femoral] vein, extending [ ].
Popliteal vein | Fully compressible popliteal vein. | [Occlusive / Non-occlusive] [acute / chronic] thrombus in the popliteal vein, extending [ ].
= Calf veins -> Posterior tibial and peroneal veins
Gastrocnemius and soleal veins | Compressible gastrocnemius and soleal veins. | Thrombus in the [gastrocnemius / soleal] veins.
> Superficial veins
Great saphenous vein | Patent, compressible great saphenous vein and saphenofemoral junction. | Thrombus in the great saphenous vein, [ ] cm from the saphenofemoral junction.
Small saphenous vein | Patent, compressible small saphenous vein. | Thrombus in the small saphenous vein, [ ] cm from the saphenopopliteal junction.
>
= Iliac veins
= Popliteal fossa and soft tissues

## us.lower-limb-veins-bilateral
! Deep veins
! Calf veins
> Right leg
Right femoral and popliteal veins | Fully compressible right common femoral, femoral and popliteal veins. | [Occlusive / Non-occlusive] thrombus in the right [common femoral / femoral / popliteal] vein.
Right calf veins | Compressible right posterior tibial, peroneal and muscular veins. | Thrombus in the right [posterior tibial / peroneal / gastrocnemius / soleal] veins.
Right saphenous veins | Patent right great and small saphenous veins. | Superficial thrombophlebitis of the right [great / small] saphenous vein.
> Left leg
Left femoral and popliteal veins | Fully compressible left common femoral, femoral and popliteal veins. | [Occlusive / Non-occlusive] thrombus in the left [common femoral / femoral / popliteal] vein.
Left calf veins | Compressible left posterior tibial, peroneal and muscular veins. | Thrombus in the left [posterior tibial / peroneal / gastrocnemius / soleal] veins.
Left saphenous veins | Patent left great and small saphenous veins. | Superficial thrombophlebitis of the left [great / small] saphenous vein.
>
= Flow
= Superficial veins and popliteal fossae -> Popliteal fossae and soft tissues | No Baker's cyst or soft tissue collection.

## us.venous-duplex-upper-limb
! Central veins
! Axillary and brachial veins
! Superficial veins
> Central veins
Internal jugular vein | Patent, compressible internal jugular vein. | Thrombus in the internal jugular vein [ ].
Subclavian vein | Patent subclavian vein with normal respiratory variation and cardiac pulsatility. | Thrombus in the [subclavian / brachiocephalic] vein [ ]. | Loss of pulsatility, suggesting central venous obstruction.
> Deep veins
Axillary vein | Fully compressible axillary vein. | [Occlusive / Non-occlusive] thrombus in the axillary vein.
Brachial veins | Fully compressible brachial veins. | [Occlusive / Non-occlusive] thrombus in the brachial veins.
Radial and ulnar veins | Compressible radial and ulnar veins. | Thrombus in the [radial / ulnar] veins.
> Superficial veins
Cephalic vein | Patent. | Thrombus in the cephalic vein [ ].
Basilic vein | Patent. | Thrombus in the basilic vein [ ].
>
= Lines and other findings

## us.transcranial-doppler
= Windows
! Anterior circulation
! Posterior circulation
> Anterior circulation
Middle cerebral arteries | Normal, symmetrical middle cerebral artery velocities and pulsatility indices. | [Raised / Reduced] mean velocity in the [right / left] middle cerebral artery at [ ] cm/s; PI [ ]. | Lindegaard ratio [ ].
Anterior cerebral arteries | Normal, symmetrical anterior cerebral artery velocities. | [Raised / Reduced / Reversed] flow in the [right / left] anterior cerebral artery at [ ] cm/s.
Terminal internal carotid arteries | Normal velocities in the carotid siphons and terminal internal carotid arteries. | [Raised / Reduced] mean velocity in the [right / left] terminal internal carotid artery at [ ] cm/s.
> Posterior circulation
Posterior cerebral arteries | Normal, symmetrical posterior cerebral artery velocities. | [Raised / Reduced] mean velocity in the [right / left] posterior cerebral artery at [ ] cm/s.
Vertebral arteries | Normal vertebral artery velocities with antegrade flow. | [Raised / Reduced / Reversed] flow in the [right / left] vertebral artery.
Basilar artery | Normal basilar artery velocity. | [Raised / Reduced] basilar velocity [ ] cm/s.

# ---------------------------------------------------------------- brain

# What every MRI of the brain shows besides its question.
## @BRAIN_REST
Ventricles and extra-axial spaces | Normal ventricles and sulci for age. No extra-axial collection. | [Hydrocephalus / Atrophy / Subdural collection / Midline shift] [ ].
Intracranial vessels | Normal intracranial flow voids. | [Absent flow void / Aneurysm / Vascular malformation] [ ].
Orbits | Normal. | [Optic nerve / Globe / Extraocular muscle] abnormality [ ].
Paranasal sinuses and mastoids | Clear. | [Sinus mucosal thickening / Mastoid effusion] [ ].
Skull and scalp | Normal. | [Calvarial lesion / Scalp lesion] [ ].

## neuro.mri-brain-routine
! Brain parenchyma
> Brain parenchyma
Cerebral hemispheres | Normal grey and white matter signal. No mass or infarct. | [T2 hyperintense / Enhancing / Diffusion restricting] lesion [ ] mm in the [ ]. | White matter hyperintensities, Fazekas grade [1 / 2 / 3].
Basal ganglia and thalami | Normal. | [Lacune / Haemorrhage / Signal abnormality / Calcification] in the [ ].
Brainstem and cerebellum | Normal. | [Infarct / Mass / Atrophy / Signal abnormality] in the [ ].
>
= Diffusion and susceptibility
! Ventricles and extra-axial spaces
! Ventricles
Ventricles and basal cisterns | Normal ventricular size for age. Patent basal cisterns. No midline shift. | [Hydrocephalus / Ventriculomegaly / Ventricular asymmetry] [ ]. | Midline shift [ ] mm to the [right / left].
Sulci and extra-axial spaces | Normal sulci for age. No extra-axial collection. | [Atrophy / Subdural collection / Arachnoid cyst / Sulcal effacement] [ ].
! Midline structures
Pituitary and sella | Normal. | [Pituitary lesion / Empty sella / Stalk deviation] [ ].
Corpus callosum and pineal region | Normal. | [Callosal lesion / Callosal thinning / Pineal cyst] [ ].
Craniocervical junction | Normal. No cerebellar tonsillar ectopia. | Cerebellar tonsillar descent [ ] mm.
= Vessels -> Intracranial vessels
! Orbits, sinuses and mastoids
Orbits | Normal. | [Optic nerve / Globe / Extraocular muscle] abnormality [ ].
Paranasal sinuses and mastoids | Clear. | [Sinus mucosal thickening / Mastoid effusion] [ ].
Skull and scalp | Normal. | [Calvarial lesion / Scalp lesion] [ ].

## neuro.ct-brain-routine
= Cerebral hemispheres
Basal ganglia and thalami | Normal. | [Lacune / Haemorrhage / Calcification] in the [ ].
! Posterior fossa
Brainstem and cerebellum | Normal. | [Infarct / Haemorrhage / Mass] in the [brainstem / cerebellum].
= Ventricles and basal cisterns
= Extra-axial spaces -> Sulci and extra-axial spaces | Normal sulci for age. No extra-axial collection.
Sella and craniocervical junction | Normal. | [Sellar enlargement / Tonsillar descent] [ ].
Intracranial vessels | No hyperdense artery or venous sinus. | Hyperdense [right / left] [middle cerebral artery / basilar artery / venous sinus].
Orbits | Normal. | [Globe / Optic nerve / Orbital wall] abnormality [ ].
= Paranasal sinuses and mastoids
= Skull and scalp

## ra.acute-stroke
= Brain parenchyma
= Haemorrhage
= Cervical and intracranial arteries
= Collaterals and perfusion
= Mass effect and background brain
Ventricles and extra-axial spaces | Normal ventricles. No extra-axial collection. | [Hydrocephalus / Subdural collection / Effaced sulci] [ ].
Aortic arch and lung apices | Normal arch branch origins. Clear lung apices. | [Arch atheroma / Origin stenosis / Apical lung lesion] [ ].
! Skull, sinuses and orbits
Orbits | Normal. | [Globe / Optic nerve / Orbital wall] abnormality [ ].
Paranasal sinuses and mastoids | Clear. | [Sinus opacification / Mastoid effusion] [ ].
Skull and scalp | Normal. | [Calvarial lesion / Scalp haematoma] [ ].

## mri.brain-stroke
= Brain parenchyma
= Haemorrhage
= Arteries -> Intracranial arteries
= Collaterals and perfusion
= Mass effect and background brain
@BRAIN_REST except Intracranial vessels

## ra.ct-traumatic-haemorrhage
= Extra-axial blood
= Parenchymal injury
= Ventricles -> Ventricles and basal cisterns | Normal ventricular size. Patent basal cisterns. No intraventricular haemorrhage.
= Mass effect
= Skull vault and base
Facial bones and orbits | No facial or orbital fracture on the included images. | [Orbital / Nasal / Zygomatic / Maxillary] fracture [ ]. | [Globe injury / Retrobulbar haematoma] [ ].
Paranasal sinuses and mastoids | Clear. | [Haemosinus / Mastoid effusion / Pneumocephalus] [ ].
Scalp | No scalp haematoma or laceration. | Scalp [haematoma / laceration] over the [ ].
Craniocervical junction | Normal craniocervical alignment. | [Occipital condyle fracture / Atlanto-occipital dissociation / C1 fracture / C2 fracture] [ ].

## ra.intracranial-haemorrhage
= Haemorrhage
= Underlying cause
Intracranial arteries | Patent intracranial arteries without stenosis or vasospasm. | [Aneurysm / Stenosis / Vasospasm / Spot sign] of the [ ].
Venous sinuses | Patent visualised dural venous sinuses. | Thrombus in the [ ] sinus.
= Mass effect
= Background brain
Ventricles and extra-axial spaces | Normal ventricles. No extra-axial collection. | [Hydrocephalus / Intraventricular extension / Subdural collection] [ ].
! Skull, sinuses and orbits
Orbits | Normal. | [Globe / Optic nerve / Orbital wall] abnormality [ ].
Paranasal sinuses and mastoids | Clear. | [Sinus opacification / Mastoid effusion] [ ].
Skull and scalp | No skull fracture. | [Skull fracture / Calvarial lesion / Scalp haematoma] [ ].

## mri.brain-haemorrhage
= Haemorrhage
= Underlying cause
Intracranial arteries | Patent intracranial arteries without stenosis or aneurysm. | [Aneurysm / Stenosis / Vasospasm] of the [ ].
Venous sinuses | Normal dural venous sinus flow voids. | Thrombus in the [ ] sinus.
= Mass effect
= Background brain
@BRAIN_REST except Intracranial vessels

## ra.mri-brain-tumours
= Lesion
= Extent
= Oedema and mass effect
= Response
! Ventricles, vessels and skull base
Remaining brain parenchyma | No other parenchymal signal abnormality. | [White matter hyperintensities / Old infarct / Treatment-related change] [ ].
@BRAIN_REST

## ra.mri-cns-enhancement
= Meninges
= Parenchyma
= Cranial nerves and ependyma
= Extra-axial spaces
! Ventricles, vessels and skull base
Ventricles | Normal ventricular size. | [Hydrocephalus / Ventriculitis / Ventricular debris] [ ].
@BRAIN_REST except Ventricles and extra-axial spaces

## ra.mri-epilepsy
= Hippocampi
Amygdalae and parahippocampal gyri | Normal. | [Amygdala enlargement / Signal abnormality / Atrophy] on the [right / left].
= Cortex
= Focal lesions
White matter and deep grey matter | Normal. | [Heterotopia / Gliosis / White matter signal abnormality] in the [ ].
! Cerebellum and brainstem
Brainstem and cerebellum | Normal. | [Brainstem lesion / Cerebellar atrophy] [ ].
! Ventricles, vessels and skull base
@BRAIN_REST

## ra.mri-ms
= Brain lesions
= Spinal cord and optic nerves
= Activity
= Dissemination
Brain volume | Normal brain volume for age. | [Generalised atrophy / Callosal thinning / Black holes] [ ].
! Ventricles, vessels and skull base
@BRAIN_REST

## ra.mri-dementia
= Global atrophy
= Medial temporal lobes
= Frontal and temporal lobes
Parietal lobes | No disproportionate parietal or precuneus atrophy. | Posterior atrophy (Koedam) grade [1 / 2 / 3].
Basal ganglia and thalami | Normal. | [Lacunes / Iron deposition / Caudate atrophy] [ ].
Brainstem and cerebellum | Normal midbrain, pons and cerebellum. | [Midbrain atrophy / Pontine atrophy / Cerebellar atrophy] [ ].
= Small vessel disease
= Microhaemorrhages
Ventricles and extra-axial spaces | Ventricles in proportion to the sulci. No extra-axial collection. | Evans index [ ]; callosal angle [ ] degrees. | [Disproportionate ventriculomegaly / Subdural collection] [ ].
= Other causes
@BRAIN_REST except Ventricles and extra-axial spaces

## @VENOUS_SINUSES
> Dural venous sinuses
Superior sagittal sinus | Patent. | [Occlusive / Non-occlusive] thrombus in the superior sagittal sinus [ ].
Transverse and sigmoid sinuses | Patent. | Thrombus in the [right / left] [transverse / sigmoid] sinus [ ]. | [Hypoplastic transverse sinus / Arachnoid granulation] mimicking thrombus [ ].
Straight sinus and vein of Galen | Patent. | Thrombus in the [straight sinus / vein of Galen].
Internal jugular veins | Patent. | Thrombus extending into the [right / left] internal jugular vein.
> Cerebral veins
Internal cerebral and basal veins | Patent. | Thrombus in the internal cerebral veins.
Cortical veins | Patent. | Thrombus in the [vein of Trolard / vein of Labbé / cortical veins] on the [right / left].

## ra.venous-sinus-thrombosis mri.venogram
! Dural sinuses
! Deep and cortical veins
@VENOUS_SINUSES
= Parenchyma -> Brain parenchyma
Ventricles and extra-axial spaces | Normal ventricles. No extra-axial collection. | [Hydrocephalus / Subdural collection / Effaced sulci] [ ].
! Skull base, sinuses and mastoids
Paranasal sinuses and mastoids | Clear. | [Mastoiditis / Sinusitis] [ ].
Skull and scalp | No skull base lesion. | [Skull base lesion / Calvarial lesion] [ ].

## ra.mri-sella
= Pituitary gland
Posterior pituitary | Normal posterior pituitary bright spot. | [Absent / Ectopic] posterior pituitary bright spot.
= Stalk and hypothalamus
= Optic chiasm
= Cavernous sinuses
= Sella and skull base
Brain | Normal. | [White matter hyperintensities / Mass / Hydrocephalus] [ ].

## ra.mri-trigeminal
= Root entry zone and cisternal segment
= Brainstem
= Meckel cave and cavernous sinus
= Peripheral branches
Cerebellopontine angles | No cerebellopontine angle mass. | [Vestibular schwannoma / Meningioma / Epidermoid] in the [right / left] cerebellopontine angle.
Brain and skull base | No demyelination or skull base lesion. | [Demyelinating lesion / Skull base lesion / Perineural tumour spread] [ ].

## ra.craniosynostosis
! Sutures
> Sutures
Sagittal suture | Patent. | Fusion of the sagittal suture [ ].
Coronal sutures | Patent. | Fusion of the [right / left / both] coronal sutures.
Metopic suture | Normal metopic suture for age. | Premature fusion of the metopic suture with a ridge.
Lambdoid sutures | Patent. | Fusion of the [right / left / both] lambdoid sutures.
Squamosal sutures and fontanelles | Normal. | [Squamosal suture fusion / Early fontanelle closure / Wormian bones] [ ].
>
= Skull shape
= Orbits and skull base
= Brain

# ---------------------------------------------------------------- orbits, ears, sinuses, face

## mri.orbits ra.ct-mri-eye
= Globes
= Preseptal tissues -> Eyelids and preseptal tissues
= Orbital compartments -> Orbital fat and lacrimal glands | No orbital mass, collection or inflammation. Normal lacrimal glands.
! Extraocular muscles and optic nerves
Extraocular muscles | Normal. | Enlargement of the [inferior / medial / superior / lateral] rectus, [sparing / involving] the tendon.
Optic nerves and sheaths | Normal. | [Optic neuritis / Optic nerve sheath meningioma / Optic glioma / Sheath distension] on the [right / left].
! Apex, walls and sinuses
Orbital apex and cavernous sinuses | Normal. | [Apical crowding / Apex mass / Cavernous sinus involvement] [ ].
Orbital walls | Intact. | [Orbital floor / Medial wall] fracture [ ], [with / without] muscle entrapment.
Paranasal sinuses | Clear. | [Sinusitis / Mucocele / Sinus mass] [ ].
Brain and optic chiasm | Normal. | [Chiasmal lesion / Demyelinating lesions / Intracranial extension] [ ].

## ra.ct-temporal-bone
= External auditory canals
= Middle ear and ossicles
= Mastoids and tegmen
= Inner ear
= Facial nerve canal and IAC
Carotid canals and jugular bulbs | Normal. | [High-riding jugular bulb / Dehiscent jugular bulb / Aberrant internal carotid artery / Sigmoid plate dehiscence] on the [right / left].
= Fracture
Brain and skull base | Normal. | [Cerebellopontine angle mass / Petrous apex lesion / Intracranial complication] [ ].

## ct.angiogram-head-neck-tinnitus
= IAC and CPA
= Inner and middle ear
! Vascular
> Arteries
Carotid arteries | Normal course and calibre of the internal carotid arteries. | [Aberrant internal carotid artery / Dissection / Stenosis / Fibromuscular dysplasia] on the [right / left].
Vertebral and intracranial arteries | Normal. | [Stenosis / Aneurysm / Dissection] of the [ ].
Arteriovenous shunt | No dural arteriovenous fistula or malformation. | Dural arteriovenous fistula at the [ ], supplied by the [ ].
> Veins
Transverse and sigmoid sinuses | No sinus stenosis, diverticulum or sigmoid plate dehiscence. | [Sigmoid sinus diverticulum / Sigmoid plate dehiscence / Transverse sinus stenosis] on the [right / left].
Jugular bulbs | Normal. | [High-riding / Dehiscent] [right / left] jugular bulb.
Emissary veins | No enlarged emissary vein. | Enlarged [mastoid / condylar] emissary vein on the [right / left].
>
Temporal bones | No glomus tumour or other middle ear or jugular foramen mass. | [Glomus tympanicum / Glomus jugulare / Cholesteatoma] on the [right / left]. | [Superior canal dehiscence / Otosclerosis] [ ].
= Brain

## ra.tinnitus
= IAC and CPA
= Inner and middle ear
! Vascular
Vestibulocochlear and facial nerves | Normal. No neurovascular loop contact. | [Vascular loop / Nerve enhancement / Nerve hypoplasia] on the [right / left].
Carotid arteries and jugular bulbs | Normal flow voids. No aberrant artery or high jugular bulb. | [Aberrant internal carotid artery / High-riding jugular bulb / Carotid dissection] on the [right / left].
Dural venous sinuses | Patent, without stenosis. | [Transverse sinus stenosis / Sigmoid sinus diverticulum / Dural arteriovenous fistula] on the [right / left].
Jugular foramen and skull base | No glomus tumour or skull base mass. | [Glomus jugulare / Glomus tympanicum / Petrous apex lesion] on the [right / left].
= Brain

## @SINUS_LIST
> Sinuses
Frontal sinuses and recesses | Clear. | [Mucosal thickening / Opacification / Fluid level] of the [right / left / both] frontal sinuses.
Ethmoid air cells | Clear. | [Mucosal thickening / Opacification] of the [anterior / posterior] ethmoid air cells, [right / left / bilateral].
Maxillary sinuses | Clear. | [Mucosal thickening / Opacification / Fluid level / Retention cyst] of the [right / left / both] maxillary sinuses.
Sphenoid sinuses | Clear. | [Mucosal thickening / Opacification / Fluid level] of the [right / left / both] sphenoid sinuses.

## ct.sinuses
! Sinuses
@SINUS_LIST
= Drainage pathways | | + Lund-Mackay score [ ].
= Nasal cavity -> Nasal cavity, septum and turbinates | Normal.
Anatomical variants | No surgically relevant variant. | [Concha bullosa / Haller cell / Onodi cell / Dehiscent lamina papyracea] on the [right / left]. | Keros type [1 / 2 / 3] olfactory fossa. | Dehiscent [optic nerve / carotid] canal in the sphenoid sinus.
= Focal lesion and bone
= Orbit and skull base -> Orbits and skull base
Nasopharynx | Normal. | [Adenoidal hypertrophy / Nasopharyngeal mass / Tornwaldt cyst] [ ].

## ra.mri-sinuses
! Sinuses
@SINUS_LIST
= Drainage pathways
= Nasal cavity -> Nasal cavity, septum and turbinates | Normal.
= Focal lesion and bone
= Orbit and skull base -> Orbits and skull base
Pterygopalatine fossae and nerves | No perineural spread. | Perineural spread along the [ ] on the [right / left].
Nasopharynx and neck | Normal nasopharynx. No retropharyngeal or cervical lymphadenopathy. | [Nasopharyngeal mass / Retropharyngeal node / Cervical lymphadenopathy] [ ].
Brain | Normal. No dural enhancement. | [Dural enhancement / Frontal lobe involvement / Abscess] [ ].

## ct.facial-bones
Frontal bone and frontal sinuses | Intact. | Frontal sinus fracture involving the [anterior / posterior] table.
= Orbits | Intact orbital walls and floors. Normal globes.
! Nasal bones and mandible
Nasal bones and septum | Intact. | [Nasal bone / Septal / Naso-orbito-ethmoid] fracture [ ]. | Septal haematoma.
= Zygoma and maxilla
Pterygoid plates | Intact. | Pterygoid plate fracture, Le Fort [1 / 2 / 3] pattern.
Mandible and temporomandibular joints | Intact mandible. Normally located condyles. | Mandibular [symphysis / parasymphysis / body / angle / ramus / condyle] fracture [ ]. | Temporomandibular joint dislocation.
Teeth and alveolar processes | Intact. | [Dental / Alveolar] fracture [ ].
= Sinuses -> Paranasal sinuses | Clear.
= Soft tissues
Brain and cervical spine | Normal visualised brain and upper cervical spine. | [Intracranial haemorrhage / Pneumocephalus / Cervical spine fracture] [ ].

## ct.tmj
= Condyles
Glenoid fossae and articular eminences | Normal. | [Erosion / Sclerosis / Flattening] of the [right / left] [glenoid fossa / articular eminence].
= Joint position -> Joint position and translation | Normally seated condyles with normal translation on mouth opening.
= Fracture
Mandible, mastoids and external auditory canals | Normal. | [Mandibular lesion / Mastoid opacification / External auditory canal abnormality] [ ].

# ---------------------------------------------------------------- neck

## @NECK_LIST
> Pharynx and larynx
Nasopharynx | Normal. | Mass [ ] mm of the [right / left] [fossa of Rosenmüller / posterior wall].
Oral cavity and oropharynx | Normal. | Mass [ ] mm of the [tongue / floor of mouth / tonsil / tongue base / soft palate].
Hypopharynx and larynx | Normal. Symmetrical vocal cords. | Mass [ ] mm of the [piriform sinus / supraglottis / glottis / subglottis].
> Deep spaces
Parapharyngeal and masticator spaces | Normal. | Mass [ ] mm centred in the [right / left] [parapharyngeal / masticator] space.
Carotid spaces | Normal. Patent carotid arteries and internal jugular veins. | [Mass / Thrombus / Encasement] in the [right / left] carotid space.
Retropharyngeal and perivertebral spaces | Normal. | [Collection / Mass / Oedema] in the [retropharyngeal / perivertebral] space.
> Salivary and thyroid glands
Parotid glands | Normal. | [Mass / Sialadenitis / Calculus / Duct dilatation] of the [right / left] parotid gland.
Submandibular glands | Normal. | [Mass / Sialadenitis / Calculus / Duct dilatation] of the [right / left] submandibular gland.
Thyroid gland | Normal. | [Nodule / Goitre / Thyroiditis] [ ].

## ra.mri-neck-spaces
! Suprahyoid neck
! Infrahyoid neck
! Airway and glands
@NECK_LIST
= Lymph nodes
= Brain, spine and lung apices -> Skull base, cervical spine and lung apices | Normal visualised skull base, brain, cervical spine and lung apices.

## ct.neck-nodes
= Right neck
= Left neck
Pharynx and larynx | Normal. No mucosal mass. | Mass [ ] mm of the [nasopharynx / oropharynx / oral cavity / hypopharynx / larynx].
= Thyroid and salivary glands -> Salivary and thyroid glands
Vessels | Patent carotid arteries and internal jugular veins. | [Thrombus / Encasement / Stenosis] of the [right / left] [carotid artery / internal jugular vein].
Lung apices and bones | Clear lung apices. No destructive bone lesion. | [Apical nodule / Bone lesion] [ ].

## ra.head-neck-malignancy mri.neck-tumour
= Primary tumour
= Local extent
= Perineural spread
= Vessels and airway -> Airway and vessels
= Lymph nodes
Salivary and thyroid glands | Normal. | [Parotid / Submandibular / Thyroid] [mass / invasion] [ ].
Skull base, brain and orbits | No skull base, intracranial or orbital involvement. | [Skull base invasion / Intracranial extension / Orbital invasion] [ ].
Lung apices and bones | Clear lung apices. No bone lesion. | [Apical nodule / Bone lesion] [ ].
= Stage

## ra.ultrasound-thyroid
! Thyroid gland
> Thyroid gland
Right lobe | Normal right lobe size and echotexture. | Right lobe [ ] x [ ] x [ ] mm. | [Heterogeneous / Hypoechoic / Hypervascular] right lobe parenchyma.
Left lobe | Normal left lobe size and echotexture. | Left lobe [ ] x [ ] x [ ] mm. | [Heterogeneous / Hypoechoic / Hypervascular] left lobe parenchyma.
Isthmus | Normal isthmus thickness. | Isthmus [ ] mm.
>
= Nodules
= Lymph nodes
= Parathyroid and salivary glands

# ---------------------------------------------------------------- spine

## ra.mri-lumbar-disc
! Alignment and vertebrae
! Discs
! Canal and lateral recesses
! Foramina
! Conus and other findings
Alignment | Normal lumbar alignment and lordosis. | [Anterolisthesis / Retrolisthesis] of [ ] on [ ], grade [1 / 2 / 3 / 4]. | [Scoliosis / Loss of lordosis] [ ]. | Transitional lumbosacral vertebra [ ].
Vertebrae | Normal vertebral heights and marrow signal. | Modic type [1 / 2 / 3] endplate change at [ ]. | [Compression fracture / Haemangioma / Marrow lesion / Pars defect] at [ ].
Conus and cauda equina | Normal conus position and signal. Normal cauda equina. | Conus terminates at [ ]. | [Clumped nerve roots / Tethered cord / Intradural lesion] [ ].
! L1-L2
! L2-L3
! L3-L4
! L4-L5
> Lumbar discs
T12-L1 ;; L1-2 ;; L2-3 ;; L3-4 ;; L4-5 ;; L5-S1 | No disc herniation, canal stenosis or foraminal stenosis. | Disc [bulge / protrusion / extrusion / sequestration], [central / right paracentral / left paracentral / foraminal / extraforaminal]. | [Mild / Moderate / Severe] central canal stenosis; lateral recess narrowing [contacting / compressing] the [right / left] traversing root. | [Mild / Moderate / Severe] [right / left / bilateral] foraminal stenosis; exiting root [contacted / compressed]. | Annular fissure.
>
Facet joints and ligamentum flavum | Normal. | [Facet arthropathy / Facet effusion / Synovial cyst / Ligamentum flavum hypertrophy] at [ ].
Sacrum and sacroiliac joints | Normal. | [Sacral insufficiency fracture / Sacroiliitis / Tarlov cyst] [ ].
Paraspinal soft tissues | Normal. | [Paraspinal mass / Muscle atrophy / Collection] [ ].
Retroperitoneum | Normal visualised kidneys and aorta. | [Renal cyst / Hydronephrosis / Aortic aneurysm] [ ].

## neuro.mri-spine-cervical
# Peter's own template (photo, 2026-11-19) supplies the protocol and the wording of the normal lines:
# vertebral body alignment, marrow and disc signal, CSF signal, cord calibre and signal, and the posterior
# fossa and lung apices, which the study also shows.
! Craniocervical junction
! C2-C3
! C3-C4
! C4-C5
! C5-C6
! C6-C7
Alignment | Normal vertebral body alignment. | [Loss of lordosis / Kyphosis / Listhesis] at [ ].
Vertebrae | Normal vertebral heights. Normal marrow and intervertebral disc signal. | [Marrow lesion / Endplate change / Compression fracture / Disc desiccation] at [ ].
Posterior fossa and craniocervical junction | Normal visualised posterior fossa structures. No cerebellar tonsillar ectopia. | Cerebellar tonsillar descent [ ] mm. | [Basilar invagination / Atlantoaxial subluxation / Pannus] [ ]. | [Cerebellar lesion / Brainstem lesion] [ ].
= Spinal cord | Normal cord calibre and signal. Normal CSF signal. | + [Syrinx / Arachnoid cyst / Intradural lesion] at [ ].
> Cervical discs
C2-3 ;; C3-4 ;; C4-5 ;; C5-6 ;; C6-7 ;; C7-T1 | No disc herniation, canal stenosis or foraminal stenosis. | Disc [bulge / protrusion / extrusion] or disc-osteophyte complex, [central / right paracentral / left paracentral]. | [Mild / Moderate / Severe] central canal stenosis, [with / without] cord contact. | [Mild / Moderate / Severe] [right / left / bilateral] foraminal stenosis from uncovertebral and facet hypertrophy.
>
Facet and uncovertebral joints | Normal. | [Facet arthropathy / Uncovertebral hypertrophy] at [ ].
Paraspinal soft tissues | Normal. | [Prevertebral swelling / Paraspinal mass / Lymphadenopathy] [ ].
Vertebral arteries and thyroid | Normal vertebral artery flow voids. Normal visualised thyroid. | [Absent vertebral artery flow void / Thyroid nodule] [ ].
Lung apices | Clear. | [Apical nodule / Apical mass / Pleural thickening] [ ].

## neuro.mri-spine-thoracic
! Alignment and vertebrae
Alignment | Normal thoracic alignment and kyphosis. | [Kyphosis / Scoliosis / Listhesis] at [ ].
Vertebrae | Normal vertebral heights and marrow signal. | [Compression fracture / Marrow lesion / Schmorl nodes] at [ ].
= Spinal cord
Conus | Normal conus position and signal. | Conus terminates at [ ].
= Discs and canal
= Foramina and facets
= Paraspinal soft tissues
Posterior mediastinum and lungs | Normal visualised aorta, lungs and pleura. | [Pleural effusion / Aortic aneurysm / Lung lesion] [ ].

## msk.mri-sacroiliac
= Active inflammation
= Structural change
= ASAS definition
= Spine and other findings -> Lower lumbar spine
! Hips and pelvis
Pelvis and hips | Normal visualised pelvic marrow and hip joints. No enthesitis. | [Insufficiency fracture / Osteitis pubis / Enthesitis / Hip effusion] [ ].

# ---------------------------------------------------------------- whole-body and multi-region studies

## ct.trauma-panscan
# Peter's own panscan template (photo, 2026-11-20) gives the regions, what each reports and the wording of the normal
# lines; negatives are in the library's singular ("No fracture"). The house adds Diaphragm, Abdominal vessels, Lines and
# devices, "No mediastinal haematoma." and "Normal thoracolumbar alignment."
! Brain
! Skull and facial bones
! Cervical alignment
! Cervical vertebrae
! Prevertebral soft tissues
! Lungs and pleura
! Mediastinum and aorta
! Chest wall
! Liver and spleen
! Kidneys and adrenal glands
! Pancreas, bowel and mesentery
! Bladder
! Peritoneum and retroperitoneum
! Thoracic spine
! Lumbar spine
! Pelvis and hips
> Brain
Brain parenchyma | Normal grey-white differentiation. Normal midline and posterior fossa structures. | [Contusion / Diffuse axonal injury / Infarct / Oedema] in the [ ].
Haemorrhage | No intra-axial or extra-axial space-occupying lesion or haemorrhage. | [Extradural / Subdural / Subarachnoid / Intraparenchymal / Intraventricular] haemorrhage [ ], [ ] mm.
Ventricles and basal cisterns | Patent surface sulci, basal cisterns and fourth ventricle. Central midline. No hydrocephalus. | Midline shift [ ] mm to the [right / left]. | [Effaced basal cisterns / Herniation / Hydrocephalus] [ ].
Orbits | Normal orbital contents. | [Globe injury / Retrobulbar haematoma / Orbital emphysema] [ ].
Paranasal sinuses and mastoids | Clear. | [Haemosinus / Mastoid effusion / Pneumocephalus] [ ].
Skull and facial bones | No craniofacial fracture. | [Skull vault / Skull base / Facial] fracture [ ].
> Cervical spine
Craniocervical junction | Intact. | [Occipital condyle fracture / Atlanto-occipital dissociation / Atlantoaxial subluxation] [ ].
Cervical alignment | Normal vertebral alignment. | [Anterolisthesis / Facet subluxation / Facet dislocation] at [ ].
Cervical vertebrae | No fracture or dislocation. | Fracture of [ ].
Prevertebral soft tissues | No prevertebral soft tissue swelling. | Prevertebral swelling [ ] mm at [ ].
> Chest
Airways | Major airways patent and undisplaced. | [Tracheobronchial injury / Airway displacement / Endobronchial blood] [ ].
Mediastinum and aorta | No major vascular injury. No mediastinal haematoma. | [Aortic injury / Mediastinal haematoma / Pneumomediastinum] [ ].
= Heart and pericardium
Pleura | No pneumothorax or haemothorax. | [Small / Moderate / Large] [right / left / bilateral] [pneumothorax / haemothorax].
Lungs | No pulmonary contusion. | [Contusion / Laceration / Aspiration / Atelectasis] in the [ ]. | Bibasal dependent lung changes.
= Diaphragm
> Abdomen and pelvis
Liver | No focal liver lesion or contour irregularity. | Liver injury, AAST grade [I / II / III / IV / V], segment [ ].
Gallbladder and bile ducts | No intrahepatic or extrahepatic biliary dilatation. Normal gallbladder. | [Gallbladder injury / Pericholecystic haematoma / Gallstones] [ ].
Pancreas and spleen | Normal. | Splenic injury, AAST grade [I / II / III / IV / V]. | [Pancreatic contusion / Pancreatic laceration] [ ].
Adrenal glands, kidneys and bladder | Normal. | [Right / Left] renal injury, AAST grade [I / II / III / IV / V]. | [Right / Left] adrenal haematoma. | [Intraperitoneal / Extraperitoneal] bladder rupture.
Stomach and bowel | No gastric or bowel wall thickening. | [Bowel wall discontinuity / Bowel wall thickening / Mesenteric haematoma / Extraluminal gas] [ ].
Peritoneum and retroperitoneum | No haemoperitoneum or pneumoperitoneum. | [Small / Moderate / Large] haemoperitoneum [ ]. | [Pneumoperitoneum / Retroperitoneal haematoma] [ ].
= Abdominal vessels
> Skeletal
Sternum and ribs | No sternal or rib fracture. | Fractures of the [right / left] ribs [ ]; flail segment [present / absent]. | Sternal fracture [ ].
Shoulder girdles | Shoulder joints intact. | [Clavicular / Scapular / Proximal humeral] fracture on the [right / left]. | [Glenohumeral / Acromioclavicular] dislocation on the [right / left].
Thoracic and lumbar spine | Normal thoracolumbar alignment. No thoracolumbar compression fracture. | Fracture of [ ], [compression / burst / Chance / translation / transverse process].
Pelvis and hips | No pelvic or hip fracture. | [Pelvic ring / Acetabular / Sacral / Proximal femoral] fracture [ ]. | [Sacroiliac / Symphyseal] diastasis [ ] mm.
>
= Lines and devices

## ct.oncology-staging
! Neck
! Chest
! Abdomen and pelvis
> Neck
Pharynx, larynx and salivary glands | Normal. No neck mass. | Mass [ ] mm of the [ ].
Thyroid | Normal. | Thyroid nodule [ ] mm.
Cervical lymph nodes | No cervical lymphadenopathy. | Level [ ] lymph node [ ] mm short axis.
> Chest
Lungs and airways | No pulmonary nodule, mass or consolidation. | Pulmonary nodule [ ] mm in the [ ]. | [Mass / Consolidation / Lymphangitis] in the [ ].
Pleura and pericardium | No pleural or pericardial effusion. | [Pleural effusion / Pleural nodularity / Pericardial effusion] [ ].
Thoracic lymph nodes | No mediastinal, hilar or axillary lymphadenopathy. | [Mediastinal / Hilar / Axillary] lymph node [ ] mm at station [ ].
Heart and great vessels | Normal. | [Pulmonary embolism / Tumour thrombus / Pericardial involvement] [ ].
> Abdomen and pelvis
Liver | No focal liver lesion. | Liver lesion [ ] mm in segment [ ].
Gallbladder, pancreas and spleen | Normal. | [Pancreatic / Splenic / Gallbladder] lesion [ ].
Adrenal glands | Normal. | [Right / Left] adrenal nodule [ ] mm.
Kidneys and bladder | Normal. | [Renal / Bladder] lesion [ ]. | Hydronephrosis on the [right / left].
Bowel and peritoneum | Normal bowel. No ascites or peritoneal nodularity. | [Bowel mass / Peritoneal nodularity / Omental disease / Ascites] [ ].
Reproductive organs | Normal. | [Adnexal mass / Uterine mass / Prostate abnormality] [ ].
Abdominal and pelvic lymph nodes | No abdominal or pelvic lymphadenopathy. | [Retroperitoneal / Mesenteric / Pelvic / Inguinal] lymph node [ ] mm.
>
= Bones
= Target lesions

## ra.ct-peritoneal-carcinomatosis
= Peritoneal disease
= Omentum
= Small bowel and mesentery
= Critical sites
= Primary and other spread
Lungs and pleura | No pulmonary nodule or pleural effusion. | [Pulmonary nodule / Pleural effusion / Pleural nodularity] [ ].
Thoracic lymph nodes | No thoracic or cardiophrenic lymphadenopathy. | [Cardiophrenic / Mediastinal / Hilar] lymph node [ ] mm.
@ABDOMEN_BRIEF except Bowel and peritoneum; Lung bases and bones
Bones | No destructive bone lesion. | [Lytic lesion / Sclerotic lesion] in the [ ].

## mri.whole-body
! Bone marrow
> Bone marrow
Skull ;; Spine and sacrum ;; Ribs, sternum, clavicles and scapulae ;; Pelvis ;; Upper limbs ;; Lower limbs | No focal or diffuse marrow lesion. | [Focal / Diffuse] marrow infiltration [ ] (MY-RADS / MET-RADS-P).
>
= Spine -> Spinal canal
! Lymph nodes and organs
Lymph nodes | No lymphadenopathy. | [Cervical / Axillary / Mediastinal / Retroperitoneal / Pelvic / Inguinal] lymphadenopathy [ ] mm.
Chest | Clear lungs. No pleural effusion. | [Lung lesion / Pleural effusion] [ ].
Abdomen and pelvis | Normal liver, spleen, kidneys and pelvic organs. | [Liver / Splenic / Renal / Pelvic] lesion [ ].
Soft tissues | No soft tissue mass. | [Paramedullary / Extramedullary] soft tissue mass at [ ].

# ---------------------------------------------------------------- paediatric abdomen

## mri.paediatric-abdomen-cystic ra.paediatric-cystic-abdominal-masses
= Lesion
= Wall and contents
= Effects
! Other organs
Liver, spleen and pancreas | Normal. | [Liver / Splenic / Pancreatic] lesion [ ].
Kidneys and bladder | Normal. No hydronephrosis. | [Hydronephrosis / Renal lesion / Duplex kidney / Bladder abnormality] [ ].
Bowel | Normal. | [Bowel obstruction / Wall thickening / Malrotation] [ ].
Reproductive organs | Normal. | [Ovarian cyst / Ovarian torsion / Hydrocolpos] [ ].
Free fluid | None. | [Small / Moderate / Large] free fluid.

## ra.paediatric-solid-abdominal-masses
= Mass
= Vessels
= Local extent
= Lymph nodes and metastases
Liver, spleen and pancreas | Normal. | [Liver / Splenic / Pancreatic] lesion [ ].
Kidneys and adrenal glands | Normal. | [Renal / Adrenal] lesion on the [right / left].
Bowel and bladder | Normal. | [Bowel obstruction / Bladder displacement / Hydronephrosis] [ ].

## ct.paediatric-abdomen-solid mri.paediatric-abdomen-solid
= Mass
= Vessels
= Local extent
= Lymph nodes and metastases
Liver, spleen and pancreas | Normal. | [Liver / Splenic / Pancreatic] lesion [ ].
Kidneys and adrenal glands | Normal. | [Renal / Adrenal] lesion on the [right / left].
Bowel and bladder | Normal. | [Bowel obstruction / Bladder displacement / Hydronephrosis] [ ].
Lung bases and bones | Clear lung bases. No bone lesion. | [Pulmonary nodule / Pleural effusion / Bone lesion] [ ].

## ra.paediatric-renal-tumours mri.paediatric-renal-tumour
= Renal mass
= Contralateral kidney
= Veins
= Local extent and rupture
= Lymph nodes and metastases
Liver, spleen and pancreas | Normal. | [Liver / Splenic / Pancreatic] lesion [ ].
Adrenal glands | Normal. | [Right / Left] adrenal [displacement / invasion / mass].
Bowel and bladder | Normal. | [Bowel displacement / Bowel obstruction / Bladder abnormality] [ ].
Lung bases and bones | Clear lung bases. No bone lesion. | [Pulmonary nodule / Pleural effusion / Bone lesion] [ ].
'''
