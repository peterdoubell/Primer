/* Original schematic reporting anatomy. No patient data or diagnostic measurements. */
(function () {
  'use strict';
  const MODULES = {"rad.3.contrast":{"id":"radiology-model-rad.3.contrast","title":"Contrast Agents and Their Risks · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate the enhancement target to the imaged volume; record the agent, phase and any limitation.","scenario":"radiology-reference:rad.3.contrast","family":"acquisition","focus":["target"],"reporting_aim":"Relate the enhancement target to the imaged volume; record the agent, phase and any limitation."},"rad.2.radiation-safety":{"id":"radiology-model-rad.2.radiation-safety","title":"Radiation Safety · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Connect beam extent with the acquired field; record relevant dose indices from the scanner, never this schematic.","scenario":"radiology-reference:rad.2.radiation-safety","family":"acquisition","focus":["beam"],"reporting_aim":"Connect beam extent with the acquired field; record relevant dose indices from the scanner, never this schematic."},"rad.3.ct-image":{"id":"radiology-model-rad.3.ct-image","title":"Reading the CT Image · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Move the section through the target and correlate axial, coronal and sagittal locations.","scenario":"radiology-reference:rad.3.ct-image","family":"acquisition","focus":["plane"],"reporting_aim":"Move the section through the target and correlate axial, coronal and sagittal locations."},"rad.3.mri-sequences":{"id":"radiology-model-rad.3.mri-sequences","title":"Telling MRI Sequences Apart · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Localise the same finding across orthogonal planes before comparing T1, T2, diffusion and enhancement.","scenario":"radiology-reference:rad.3.mri-sequences","family":"acquisition","focus":["target"],"reporting_aim":"Localise the same finding across orthogonal planes before comparing T1, T2, diffusion and enhancement."},"rad.2.modalities":{"id":"radiology-model-rad.2.modalities","title":"What Each Modality Detects · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate projection imaging to a cross-sectional target; modality signal and attenuation are not simulated.","scenario":"radiology-reference:rad.2.modalities","family":"acquisition","focus":["detector"],"reporting_aim":"Relate projection imaging to a cross-sectional target; modality signal and attenuation are not simulated."},"rad.5.ultrasound-physics":{"id":"radiology-model-rad.5.ultrasound-physics","title":"Ultrasound Physics, Doppler and Artefacts · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Inspect the beam-target relationship; an insonation pathway is shown, without Doppler velocity calculation.","scenario":"radiology-reference:rad.5.ultrasound-physics","family":"acquisition","focus":["beam"],"reporting_aim":"Inspect the beam-target relationship; an insonation pathway is shown, without Doppler velocity calculation."},"rad.5.biopsy-safety":{"id":"radiology-model-rad.5.biopsy-safety","title":"Image-guided Biopsy and Drainage · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate to inspect target, proposed needle path and intervening structures; plan a real trajectory on patient imaging.","scenario":"radiology-reference:rad.5.biopsy-safety","family":"access","focus":["needle"],"reporting_aim":"Rotate to inspect target, proposed needle path and intervening structures; plan a real trajectory on patient imaging."},"rad.4.oncology-response":{"id":"radiology-model-rad.4.oncology-response","title":"Measuring Tumour Response · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Use orthogonal views to localise a target lesion and its organ relationship; measure response on matched clinical images.","scenario":"radiology-reference:rad.4.oncology-response","family":"access","focus":["target"],"reporting_aim":"Use orthogonal views to localise a target lesion and its organ relationship; measure response on matched clinical images."},"rad.4.structured-reporting":{"id":"radiology-model-rad.4.structured-reporting","title":"Structured Reporting · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Use plane, side and anatomical landmark consistently when transferring a finding into a structured report.","scenario":"radiology-reference:rad.4.structured-reporting","family":"acquisition","focus":["plane"],"reporting_aim":"Use plane, side and anatomical landmark consistently when transferring a finding into a structured report."},"rad.5.ir-basics":{"id":"radiology-model-rad.5.ir-basics","title":"Interventional Radiology · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace vessel, target and access route; distinguish anatomical location from a clinically safe procedural route.","scenario":"radiology-reference:rad.5.ir-basics","family":"access","focus":["vessel"],"reporting_aim":"Trace vessel, target and access route; distinguish anatomical location from a clinically safe procedural route."},"rad.5.airways":{"id":"radiology-model-rad.5.airways","title":"Airway Disease · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace trachea, main bronchi and lobar destinations; report the level and distribution of airway abnormality.","scenario":"radiology-reference:rad.5.airways","family":"thorax","focus":["airway"],"reporting_aim":"Trace trachea, main bronchi and lobar destinations; report the level and distribution of airway abnormality."},"rad.4.hrct":{"id":"radiology-model-rad.4.hrct","title":"HRCT of the Lung · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Compare upper/lower and central/peripheral distribution; lobes are stylised and secondary lobules are not resolved.","scenario":"radiology-reference:rad.4.hrct","family":"thorax","focus":["lobes"],"reporting_aim":"Compare upper/lower and central/peripheral distribution; lobes are stylised and secondary lobules are not resolved."},"rad.5.mediastinum":{"id":"radiology-model-rad.5.mediastinum","title":"Mediastinal Masses and the Nodal Map · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate around the central compartment and relate a finding to the trachea, hila and heart.","scenario":"radiology-reference:rad.5.mediastinum","family":"thorax","focus":["mediastinum"],"reporting_aim":"Rotate around the central compartment and relate a finding to the trachea, hila and heart."},"rad.5.pleura":{"id":"radiology-model-rad.5.pleura","title":"Pleura · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Follow the outer pleural envelope and diaphragmatic bases when describing pleural extent.","scenario":"radiology-reference:rad.5.pleura","family":"thorax","focus":["pleura"],"reporting_aim":"Follow the outer pleural envelope and diaphragmatic bases when describing pleural extent."},"rad.5.chest-infection":{"id":"radiology-model-rad.5.chest-infection","title":"Pneumonia, Tuberculosis and CO-RADS · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Localise lobar and multilobar distribution and distinguish pleural from parenchymal involvement.","scenario":"radiology-reference:rad.5.chest-infection","family":"thorax","focus":["lobes"],"reporting_aim":"Localise lobar and multilobar distribution and distinguish pleural from parenchymal involvement."},"rad.5.pe-pulm-htn":{"id":"radiology-model-rad.5.pe-pulm-htn","title":"Pulmonary Embolism and Pulmonary Hypertension · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace central and lobar pulmonary arterial branches; distal branches and emboli are not modelled.","scenario":"radiology-reference:rad.5.pe-pulm-htn","family":"thorax","focus":["pulmonary"],"reporting_aim":"Trace central and lobar pulmonary arterial branches; distal branches and emboli are not modelled."},"rad.4.lung-cancer":{"id":"radiology-model-rad.4.lung-cancer","title":"Staging Lung Cancer on Imaging · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Connect tumour lobe, pleura and mediastinal relationships; use clinical images for nodal stations and staging.","scenario":"radiology-reference:rad.4.lung-cancer","family":"thorax","focus":["mediastinum"],"reporting_aim":"Connect tumour lobe, pleura and mediastinal relationships; use clinical images for nodal stations and staging."},"rad.3.chest-xray":{"id":"radiology-model-rad.3.chest-xray","title":"The Chest Radiograph · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate to understand overlapping lung, heart and diaphragm silhouettes in a projection image.","scenario":"radiology-reference:rad.3.chest-xray","family":"thorax","focus":["heart"],"reporting_aim":"Rotate to understand overlapping lung, heart and diaphragm silhouettes in a projection image."},"rad.4.pulmonary-nodule":{"id":"radiology-model-rad.4.pulmonary-nodule","title":"The Incidental Pulmonary Nodule · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Localise the lobe and relationship to a fissure or pleura; nodule size and follow-up are not inferred here.","scenario":"radiology-reference:rad.4.pulmonary-nodule","family":"thorax","focus":["lobes"],"reporting_aim":"Localise the lobe and relationship to a fissure or pleura; nodule size and follow-up are not inferred here."},"rad.5.aorta":{"id":"radiology-model-rad.5.aorta","title":"Acute Aortic Syndrome · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace root, arch, descending aorta and branch vessels before describing longitudinal disease extent.","scenario":"radiology-reference:rad.5.aorta","family":"aorta","focus":["arch"],"reporting_aim":"Trace root, arch, descending aorta and branch vessels before describing longitudinal disease extent."},"rad.5.cardiac-mri":{"id":"radiology-model-rad.5.cardiac-mri","title":"Cardiac MRI · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Identify ventricular long-axis and short-axis relationships; wall motion, scar and perfusion are not simulated.","scenario":"radiology-reference:rad.5.cardiac-mri","family":"heart","focus":["ventricles"],"reporting_aim":"Identify ventricular long-axis and short-axis relationships; wall motion, scar and perfusion are not simulated."},"rad.5.cardiac-masses-devices":{"id":"radiology-model-rad.5.cardiac-masses-devices","title":"Cardiac Masses, Thrombus and Devices · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate an intracardiac finding to chamber, septum and outflow tract; attachment and mobility require clinical images.","scenario":"radiology-reference:rad.5.cardiac-masses-devices","family":"heart","focus":["atria"],"reporting_aim":"Relate an intracardiac finding to chamber, septum and outflow tract; attachment and mobility require clinical images."},"rad.5.congenital-ct":{"id":"radiology-model-rad.5.congenital-ct","title":"Congenital Heart CT · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace systemic and pulmonary outflow against the chamber arrangement; this example depicts usual connections.","scenario":"radiology-reference:rad.5.congenital-ct","family":"heart","focus":["outflow"],"reporting_aim":"Trace systemic and pulmonary outflow against the chamber arrangement; this example depicts usual connections."},"rad.5.coronary-ct":{"id":"radiology-model-rad.5.coronary-ct","title":"Coronary CT Angiography · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate from the origins through LAD, LCx and RCA courses; this example uses right coronary dominance.","scenario":"radiology-reference:rad.5.coronary-ct","family":"coronary","focus":["lad"],"reporting_aim":"Rotate from the origins through LAD, LCx and RCA courses; this example uses right coronary dominance."},"rad.5.peripheral-vascular":{"id":"radiology-model-rad.5.peripheral-vascular","title":"Peripheral, Carotid and Mesenteric Vascular Imaging · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace aortic branches and iliac inflow; peripheral runoff and carotid bifurcations require the dedicated examination.","scenario":"radiology-reference:rad.5.peripheral-vascular","family":"aorta","focus":["branches"],"reporting_aim":"Trace aortic branches and iliac inflow; peripheral runoff and carotid bifurcations require the dedicated examination."},"rad.5.tavi-ct":{"id":"radiology-model-rad.5.tavi-ct","title":"TAVI Planning CT · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate root and ascending aorta to the arch and access vessels; valve sizing must use patient-specific double-oblique measurements.","scenario":"radiology-reference:rad.5.tavi-ct","family":"aorta","focus":["root"],"reporting_aim":"Relate root and ascending aorta to the arch and access vessels; valve sizing must use patient-specific double-oblique measurements."},"rad.4.stroke":{"id":"radiology-model-rad.4.stroke","title":"Acute Stroke Imaging · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate medial, lateral and posterior cerebral territories to the section; vascular borders vary and are approximate.","scenario":"radiology-reference:rad.4.stroke","family":"brain","focus":["territories"],"reporting_aim":"Relate medial, lateral and posterior cerebral territories to the section; vascular borders vary and are approximate."},"rad.5.brain-tumour":{"id":"radiology-model-rad.5.brain-tumour","title":"Approach to an Intracranial Mass · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate lesion location to hemispheres, deep nuclei and ventricular spaces; there is no tumour or grading simulation.","scenario":"radiology-reference:rad.5.brain-tumour","family":"brain","focus":["ventricles"],"reporting_aim":"Relate lesion location to hemispheres, deep nuclei and ventricular spaces; there is no tumour or grading simulation."},"rad.5.brain-anatomy":{"id":"radiology-model-rad.5.brain-anatomy","title":"Brain Anatomy and Vascular Territories · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate to distinguish medial ACA, lateral MCA and posterior PCA cortical distributions.","scenario":"radiology-reference:rad.5.brain-anatomy","family":"brain","focus":["territories"],"reporting_aim":"Rotate to distinguish medial ACA, lateral MCA and posterior PCA cortical distributions."},"rad.5.cns-infection":{"id":"radiology-model-rad.5.cns-infection","title":"CNS Infection and Enhancement Patterns · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate the surface, parenchyma and ventricles before describing the compartment of enhancement.","scenario":"radiology-reference:rad.5.cns-infection","family":"brain","focus":["meninges"],"reporting_aim":"Relate the surface, parenchyma and ventricles before describing the compartment of enhancement."},"rad.5.venous-csf":{"id":"radiology-model-rad.5.venous-csf","title":"Cerebral Venous Thrombosis and CSF Disorders · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Follow ventricular connections and the superior sagittal sinus; hydrocephalus and venous patency are not simulated.","scenario":"radiology-reference:rad.5.venous-csf","family":"brain","focus":["ventricles"],"reporting_aim":"Follow ventricular connections and the superior sagittal sinus; hydrocephalus and venous patency are not simulated."},"rad.5.dementia":{"id":"radiology-model-rad.5.dementia","title":"Dementia and Neurodegeneration on MRI · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Compare the medial temporal structures and cortical distribution; this schematic is not an atrophy scoring image.","scenario":"radiology-reference:rad.5.dementia","family":"brain","focus":["hippocampi"],"reporting_aim":"Compare the medial temporal structures and cortical distribution; this schematic is not an atrophy scoring image."},"rad.5.epilepsy-mri":{"id":"radiology-model-rad.5.epilepsy-mri","title":"Epilepsy · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate to the medial temporal long axes and relate a coronal plane to the hippocampi.","scenario":"radiology-reference:rad.5.epilepsy-mri","family":"brain","focus":["hippocampi"],"reporting_aim":"Rotate to the medial temporal long axes and relate a coronal plane to the hippocampi."},"rad.4.head-trauma":{"id":"radiology-model-rad.4.head-trauma","title":"Head Injury · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Inspect skull-adjacent, surface and deep compartments before describing traumatic findings.","scenario":"radiology-reference:rad.4.head-trauma","family":"brain","focus":["meninges"],"reporting_aim":"Inspect skull-adjacent, surface and deep compartments before describing traumatic findings."},"rad.5.intracranial-haemorrhage":{"id":"radiology-model-rad.5.intracranial-haemorrhage","title":"Intracranial Haemorrhage · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Distinguish lobar, deep and ventricular compartments when localising haemorrhage.","scenario":"radiology-reference:rad.5.intracranial-haemorrhage","family":"brain","focus":["deep"],"reporting_aim":"Distinguish lobar, deep and ventricular compartments when localising haemorrhage."},"rad.5.ms-white-matter":{"id":"radiology-model-rad.5.ms-white-matter","title":"Multiple Sclerosis and the White Matter Differential · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate periventricular, juxtacortical and infratentorial locations; lesions and diagnostic criteria are not generated.","scenario":"radiology-reference:rad.5.ms-white-matter","family":"brain","focus":["ventricles"],"reporting_aim":"Relate periventricular, juxtacortical and infratentorial locations; lesions and diagnostic criteria are not generated."},"rad.4.spine-imaging":{"id":"radiology-model-rad.4.spine-imaging","title":"Spine MRI · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate vertebral body, disc, canal and foramina across orthogonal planes.","scenario":"radiology-reference:rad.4.spine-imaging","family":"spine","focus":["canal"],"reporting_aim":"Relate vertebral body, disc, canal and foramina across orthogonal planes."},"rad.5.sella":{"id":"radiology-model-rad.5.sella","title":"Sella and Parasellar MRI · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate to see the superior chiasm, lateral carotids and pituitary stalk around the sellar contents.","scenario":"radiology-reference:rad.5.sella","family":"sella","focus":["chiasm"],"reporting_aim":"Rotate to see the superior chiasm, lateral carotids and pituitary stalk around the sellar contents."},"rad.5.neck-nodes":{"id":"radiology-model-rad.5.neck-nodes","title":"Cervical Node Levels and the Malignant Node · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace jugular-chain landmarks alongside carotid spaces; nodal levels require actual hyoid, cricoid and vessel boundaries.","scenario":"radiology-reference:rad.5.neck-nodes","family":"neck","focus":["nodes"],"reporting_aim":"Trace jugular-chain landmarks alongside carotid spaces; nodal levels require actual hyoid, cricoid and vessel boundaries."},"rad.5.deep-neck-spaces":{"id":"radiology-model-rad.5.deep-neck-spaces","title":"Deep Neck Spaces · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Inspect the relationship of pharyngeal, parapharyngeal, retropharyngeal and carotid spaces.","scenario":"radiology-reference:rad.5.deep-neck-spaces","family":"neck","focus":["spaces"],"reporting_aim":"Inspect the relationship of pharyngeal, parapharyngeal, retropharyngeal and carotid spaces."},"rad.5.orbit":{"id":"radiology-model-rad.5.orbit","title":"Orbit · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace globe, optic nerve and orbital apex while rotating around the extraocular muscle cone.","scenario":"radiology-reference:rad.5.orbit","family":"orbit","focus":["optic"],"reporting_aim":"Trace globe, optic nerve and orbital apex while rotating around the extraocular muscle cone."},"rad.5.sinuses":{"id":"radiology-model-rad.5.sinuses","title":"Paranasal Sinuses · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate frontal, ethmoid, maxillary and sphenoid cavities to the orbits and skull base.","scenario":"radiology-reference:rad.5.sinuses","family":"sinuses","focus":["ethmoid"],"reporting_aim":"Relate frontal, ethmoid, maxillary and sphenoid cavities to the orbits and skull base."},"rad.5.temporal-bone":{"id":"radiology-model-rad.5.temporal-bone","title":"Temporal Bone · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Follow external canal, ossicular chain, cochlea and vestibular apparatus in an enlarged left-ear schematic.","scenario":"radiology-reference:rad.5.temporal-bone","family":"temporal","focus":["labyrinth"],"reporting_aim":"Follow external canal, ossicular chain, cochlea and vestibular apparatus in an enlarged left-ear schematic."},"rad.5.thyroid-tirads":{"id":"radiology-model-rad.5.thyroid-tirads","title":"Thyroid Nodules · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Localise thyroid lobes and isthmus against the trachea and lateral vessels; nodule features are assessed on ultrasound.","scenario":"radiology-reference:rad.5.thyroid-tirads","family":"neck","focus":["thyroid"],"reporting_aim":"Localise thyroid lobes and isthmus against the trachea and lateral vessels; nodule features are assessed on ultrasound."},"rad.5.esophagus-swallowing":{"id":"radiology-model-rad.5.esophagus-swallowing","title":"Esophagus and Swallowing · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate to distinguish posterior oesophagus from anterior airway; swallowing motion and aspiration are not simulated.","scenario":"radiology-reference:rad.5.esophagus-swallowing","family":"swallow","focus":["esophagus"],"reporting_aim":"Rotate to distinguish posterior oesophagus from anterior airway; swallowing motion and aspiration are not simulated."},"rad.5.tinnitus":{"id":"radiology-model-rad.5.tinnitus","title":"Imaging Pulsatile and Non-pulsatile Tinnitus · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Compare the inner ear with adjacent sigmoid sinus and jugular bulb; vascular variants require actual imaging.","scenario":"radiology-reference:rad.5.tinnitus","family":"temporal","focus":["venous"],"reporting_aim":"Compare the inner ear with adjacent sigmoid sinus and jugular bulb; vascular variants require actual imaging."},"rad.5.trigeminal":{"id":"radiology-model-rad.5.trigeminal","title":"Trigeminal Neuralgia and Neuropathy · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace cisternal trigeminal nerve from pons toward Meckel cave and the three divisions; contacts are not diagnoses.","scenario":"radiology-reference:rad.5.trigeminal","family":"trigeminal","focus":["nerve"],"reporting_aim":"Trace cisternal trigeminal nerve from pons toward Meckel cave and the three divisions; contacts are not diagnoses."},"rad.5.pancreas-acute":{"id":"radiology-model-rad.5.pancreas-acute","title":"Acute Pancreatitis · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Locate head, body, tail and adjacent duodenum when describing inflammatory extent and collections.","scenario":"radiology-reference:rad.5.pancreas-acute","family":"pancreatobiliary","focus":["pancreas"],"reporting_aim":"Locate head, body, tail and adjacent duodenum when describing inflammatory extent and collections."},"rad.5.appendicitis":{"id":"radiology-model-rad.5.appendicitis","title":"Appendicitis and its Mimics · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Locate caecum, terminal ileum and appendix; appendix position varies substantially in real patients.","scenario":"radiology-reference:rad.5.appendicitis","family":"bowel","focus":["appendix"],"reporting_aim":"Locate caecum, terminal ileum and appendix; appendix position varies substantially in real patients."},"rad.5.biliary":{"id":"radiology-model-rad.5.biliary","title":"Biliary Obstruction, Stones and the Thickened Gallbladder · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace intrahepatic confluence, common bile duct, cystic duct and pancreatic duct to the duodenum.","scenario":"radiology-reference:rad.5.biliary","family":"pancreatobiliary","focus":["ducts"],"reporting_aim":"Trace intrahepatic confluence, common bile duct, cystic duct and pancreatic duct to the duodenum."},"rad.5.bowel-ischaemia":{"id":"radiology-model-rad.5.bowel-ischaemia","title":"Bowel Ischaemia and Wall Thickening Patterns · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate small bowel loops to mesenteric inflow; viability and enhancement cannot be determined from this schematic.","scenario":"radiology-reference:rad.5.bowel-ischaemia","family":"bowel","focus":["mesentery"],"reporting_aim":"Relate small bowel loops to mesenteric inflow; viability and enhancement cannot be determined from this schematic."},"rad.5.bowel-obstruction":{"id":"radiology-model-rad.5.bowel-obstruction","title":"Bowel Obstruction, Closed Loop and Volvulus · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Follow bowel continuity and mesenteric relationships; no transition point or closed-loop diagnosis is encoded.","scenario":"radiology-reference:rad.5.bowel-obstruction","family":"bowel","focus":["smallbowel"],"reporting_aim":"Follow bowel continuity and mesenteric relationships; no transition point or closed-loop diagnosis is encoded."},"rad.5.abdominal-trauma":{"id":"radiology-model-rad.5.abdominal-trauma","title":"CT in Abdominal Trauma and AAST Grading · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Orient liver, spleen, kidneys and central vessels before describing injury compartment and extent.","scenario":"radiology-reference:rad.5.abdominal-trauma","family":"abdomen","focus":["solid"],"reporting_aim":"Orient liver, spleen, kidneys and central vessels before describing injury compartment and extent."},"rad.5.ibd":{"id":"radiology-model-rad.5.ibd","title":"Crohn Disease · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace terminal ileum to caecum and compare small bowel with colon for segment-by-segment reporting.","scenario":"radiology-reference:rad.5.ibd","family":"bowel","focus":["ileum"],"reporting_aim":"Trace terminal ileum to caecum and compare small bowel with colon for segment-by-segment reporting."},"rad.5.pancreas-tumour":{"id":"radiology-model-rad.5.pancreas-tumour","title":"Pancreatic Cancer Staging and Cystic Lesions · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate around pancreatic head and body to inspect nearby portal-mesenteric and arterial relationships.","scenario":"radiology-reference:rad.5.pancreas-tumour","family":"pancreatobiliary","focus":["vessels"],"reporting_aim":"Rotate around pancreatic head and body to inspect nearby portal-mesenteric and arterial relationships."},"rad.5.peritoneum":{"id":"radiology-model-rad.5.peritoneum","title":"Peritoneum, Mesentery and the Abdominal Wall · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate solid organs, mesentery and pelvic recesses when localising fluid or peritoneal disease.","scenario":"radiology-reference:rad.5.peritoneum","family":"abdomen","focus":["spaces"],"reporting_aim":"Relate solid organs, mesentery and pelvic recesses when localising fluid or peritoneal disease."},"rad.5.rectal-mr":{"id":"radiology-model-rad.5.rectal-mr","title":"Rectal Cancer · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Inspect rectal wall, mesorectal envelope and sphincter complex; real margin distances require high-resolution oblique MRI.","scenario":"radiology-reference:rad.5.rectal-mr","family":"rectal","focus":["mesorectum"],"reporting_aim":"Inspect rectal wall, mesorectal envelope and sphincter complex; real margin distances require high-resolution oblique MRI."},"rad.3.acute-abdomen":{"id":"radiology-model-rad.3.acute-abdomen","title":"The Acute Abdomen · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Use regional organ relationships to organise the acute-abdomen search pattern.","scenario":"radiology-reference:rad.3.acute-abdomen","family":"abdomen","focus":["bowel"],"reporting_aim":"Use regional organ relationships to organise the acute-abdomen search pattern."},"rad.4.liver":{"id":"radiology-model-rad.4.liver","title":"The Liver Lesion · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate around the portal-plane and hepatic-vein landmarks to relate Couinaud segments; boundaries are schematic.","scenario":"radiology-reference:rad.4.liver","family":"liver","focus":["segments"],"reporting_aim":"Rotate around the portal-plane and hepatic-vein landmarks to relate Couinaud segments; boundaries are schematic."},"rad.4.kidney":{"id":"radiology-model-rad.4.kidney","title":"The Renal Mass · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate cortex, central sinus and collecting system before describing lesion location and exophytic/endophytic extent.","scenario":"radiology-reference:rad.4.kidney","family":"renal","focus":["kidneys"],"reporting_aim":"Relate cortex, central sinus and collecting system before describing lesion location and exophytic/endophytic extent."},"rad.5.anal-cancer":{"id":"radiology-model-rad.5.anal-cancer","title":"Anal Cancer · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Localise anal canal, internal/external sphincter region and levator plane for anatomical description.","scenario":"radiology-reference:rad.5.anal-cancer","family":"rectal","focus":["sphincter"],"reporting_aim":"Localise anal canal, internal/external sphincter region and levator plane for anatomical description."},"rad.5.gi-tumours-foreign-bodies":{"id":"radiology-model-rad.5.gi-tumours-foreign-bodies","title":"Small Bowel Tumours and GI Foreign Bodies · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace stomach-to-bowel location and adjacent mesentery before describing a mass or foreign body.","scenario":"radiology-reference:rad.5.gi-tumours-foreign-bodies","family":"bowel","focus":["smallbowel"],"reporting_aim":"Trace stomach-to-bowel location and adjacent mesentery before describing a mass or foreign body."},"rad.5.pelvic-floor":{"id":"radiology-model-rad.5.pelvic-floor","title":"Dynamic Pelvic Floor Imaging · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate to a lateral view of the levator plane and pelvic organs; evacuation and descent are not simulated.","scenario":"radiology-reference:rad.5.pelvic-floor","family":"rectal","focus":["levator"],"reporting_aim":"Rotate to a lateral view of the levator plane and pelvic organs; evacuation and descent are not simulated."},"rad.5.gi-ultrasound":{"id":"radiology-model-rad.5.gi-ultrasound","title":"Bowel Ultrasound · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Follow normal bowel continuity and terminal ileum/caecum landmarks; compression and mural layers are not simulated.","scenario":"radiology-reference:rad.5.gi-ultrasound","family":"bowel","focus":["ileum"],"reporting_aim":"Follow normal bowel continuity and terminal ileum/caecum landmarks; compression and mural layers are not simulated."},"rad.5.scrotum":{"id":"radiology-model-rad.5.scrotum","title":"Acute Scrotum and Testicular Masses · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Compare testes, posterior epididymides and superior spermatic cords; torsion and perfusion are not inferred here.","scenario":"radiology-reference:rad.5.scrotum","family":"scrotum","focus":["testes"],"reporting_aim":"Compare testes, posterior epididymides and superior spermatic cords; torsion and perfusion are not inferred here."},"rad.5.adrenal":{"id":"radiology-model-rad.5.adrenal","title":"Adrenal Lesion Characterisation · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Localise the suprarenal glands relative to kidneys and midline great vessels.","scenario":"radiology-reference:rad.5.adrenal","family":"renal","focus":["adrenals"],"reporting_aim":"Localise the suprarenal glands relative to kidneys and midline great vessels."},"rad.5.bladder-virads":{"id":"radiology-model-rad.5.bladder-virads","title":"Bladder Cancer and VI-RADS · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate mucosal surface, muscular wall and perivesical tissue; invasion assessment needs multiplanar T2, diffusion and enhancement.","scenario":"radiology-reference:rad.5.bladder-virads","family":"bladder","focus":["wall"],"reporting_aim":"Relate mucosal surface, muscular wall and perivesical tissue; invasion assessment needs multiplanar T2, diffusion and enhancement."},"rad.5.ovarian-orads":{"id":"radiology-model-rad.5.ovarian-orads","title":"Ovarian Lesions · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Locate adnexa against uterus, bladder and rectum; mass morphology and risk category require actual imaging.","scenario":"radiology-reference:rad.5.ovarian-orads","family":"female","focus":["ovaries"],"reporting_aim":"Locate adnexa against uterus, bladder and rectum; mass morphology and risk category require actual imaging."},"rad.5.prostate-mri":{"id":"radiology-model-rad.5.prostate-mri","title":"Prostate MRI · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Separate peripheral and transition zones and trace apex-to-base location, urethra and seminal vesicles.","scenario":"radiology-reference:rad.5.prostate-mri","family":"prostate","focus":["peripheral"],"reporting_aim":"Separate peripheral and transition zones and trace apex-to-base location, urethra and seminal vesicles."},"rad.5.uterine-mr":{"id":"radiology-model-rad.5.uterine-mr","title":"Uterus and Cervix · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate endometrial cavity, myometrium, cervix and adnexa across orthogonal views.","scenario":"radiology-reference:rad.5.uterine-mr","family":"female","focus":["uterus"],"reporting_aim":"Relate endometrial cavity, myometrium, cervix and adnexa across orthogonal views."},"rad.5.breast-calcifications":{"id":"radiology-model-rad.5.breast-calcifications","title":"Breast Calcifications · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate ductal/radial distribution to the nipple and breast quadrant; calcification morphology is not depicted.","scenario":"radiology-reference:rad.5.breast-calcifications","family":"breast","focus":["ducts"],"reporting_aim":"Relate ductal/radial distribution to the nipple and breast quadrant; calcification morphology is not depicted."},"rad.5.breast-mri":{"id":"radiology-model-rad.5.breast-mri","title":"Breast MRI, Ultrasound and Staging · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate to compare breast quadrant, depth, nipple and chest-wall relationships for lesion localisation.","scenario":"radiology-reference:rad.5.breast-mri","family":"breast","focus":["quadrants"],"reporting_aim":"Rotate to compare breast quadrant, depth, nipple and chest-wall relationships for lesion localisation."},"rad.4.breast":{"id":"radiology-model-rad.4.breast","title":"Reading the Mammogram · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate projection localisation to a three-dimensional breast and its chest-wall boundary.","scenario":"radiology-reference:rad.4.breast","family":"breast","focus":["quadrants"],"reporting_aim":"Relate projection localisation to a three-dimensional breast and its chest-wall boundary."},"rad.5.breast-implants-male":{"id":"radiology-model-rad.5.breast-implants-male","title":"Breast Implants and the Male Breast · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Identify retroareolar tissues and pectoral relationship; this schematic does not simulate an implant or rupture.","scenario":"radiology-reference:rad.5.breast-implants-male","family":"breast","focus":["chestwall"],"reporting_aim":"Identify retroareolar tissues and pectoral relationship; this schematic does not simulate an implant or rupture."},"rad.5.ankle-foot":{"id":"radiology-model-rad.5.ankle-foot","title":"Ankle Fractures and the Painful Foot · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate tibia, fibula and talus to the mortise, hindfoot and major tendon paths.","scenario":"radiology-reference:rad.5.ankle-foot","family":"ankle","focus":["mortise"],"reporting_aim":"Relate tibia, fibula and talus to the mortise, hindfoot and major tendon paths."},"rad.5.marrow-muscle":{"id":"radiology-model-rad.5.marrow-muscle","title":"Bone Marrow, Stress Injury, Muscle and the Diabetic Foot · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Inspect marrow, cortex and muscle compartments; oedema and infection are signal findings on actual MRI.","scenario":"radiology-reference:rad.5.marrow-muscle","family":"longbone","focus":["muscle"],"reporting_aim":"Inspect marrow, cortex and muscle compartments; oedema and infection are signal findings on actual MRI."},"rad.5.bone-tumours":{"id":"radiology-model-rad.5.bone-tumours","title":"Bone Tumours · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Localise a bone lesion by epiphysis, metaphysis, diaphysis and cortex; matrix and biological behaviour are not simulated.","scenario":"radiology-reference:rad.5.bone-tumours","family":"longbone","focus":["marrow"],"reporting_aim":"Localise a bone lesion by epiphysis, metaphysis, diaphysis and cortex; matrix and biological behaviour are not simulated."},"rad.3.fracture-description":{"id":"radiology-model-rad.3.fracture-description","title":"Describing a Fracture · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate around the long-bone axis to understand orthogonal localisation; no fracture displacement is implied in this companion.","scenario":"radiology-reference:rad.3.fracture-description","family":"longbone","focus":["cortex"],"reporting_aim":"Rotate around the long-bone axis to understand orthogonal localisation; no fracture displacement is implied in this companion."},"rad.5.hip":{"id":"radiology-model-rad.5.hip","title":"Hip · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Inspect femoral head-neck, acetabulum and labrum from multiple viewpoints before describing a hip finding.","scenario":"radiology-reference:rad.5.hip","family":"hip","focus":["joint"],"reporting_aim":"Inspect femoral head-neck, acetabulum and labrum from multiple viewpoints before describing a hip finding."},"rad.5.knee":{"id":"radiology-model-rad.5.knee","title":"Knee · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Inspect menisci, cruciates and extensor mechanism with femorotibial anatomy visible behind them.","scenario":"radiology-reference:rad.5.knee","family":"knee","focus":["menisci"],"reporting_aim":"Inspect menisci, cruciates and extensor mechanism with femorotibial anatomy visible behind them."},"rad.5.msk-mri":{"id":"radiology-model-rad.5.msk-mri","title":"Musculoskeletal MRI · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Correlate longitudinal and cross-sectional views of marrow, cortex and adjacent soft tissue.","scenario":"radiology-reference:rad.5.msk-mri","family":"longbone","focus":["muscle"],"reporting_aim":"Correlate longitudinal and cross-sectional views of marrow, cortex and adjacent soft tissue."},"rad.5.shoulder":{"id":"radiology-model-rad.5.shoulder","title":"Shoulder · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate rotator cuff course to humeral head, glenoid and acromial arch.","scenario":"radiology-reference:rad.5.shoulder","family":"shoulder","focus":["cuff"],"reporting_aim":"Relate rotator cuff course to humeral head, glenoid and acromial arch."},"rad.4.arthritis":{"id":"radiology-model-rad.4.arthritis","title":"The Radiographic Pattern of Arthritis · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Compare carpal, MCP and interphalangeal distribution; erosions and joint-space loss require radiographs.","scenario":"radiology-reference:rad.4.arthritis","family":"hand","focus":["joints"],"reporting_aim":"Compare carpal, MCP and interphalangeal distribution; erosions and joint-space loss require radiographs."},"rad.5.wrist-hand":{"id":"radiology-model-rad.5.wrist-hand","title":"Wrist and Hand · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate scaphoid, lunate and capitate to the distal radius and adjacent carpal row.","scenario":"radiology-reference:rad.5.wrist-hand","family":"hand","focus":["carpus"],"reporting_aim":"Relate scaphoid, lunate and capitate to the distal radius and adjacent carpal row."},"rad.5.elbow-mri":{"id":"radiology-model-rad.5.elbow-mri","title":"Elbow MRI · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Inspect medial ulnar nerve, anterior distal biceps and lateral radiocapitellar relationships.","scenario":"radiology-reference:rad.5.elbow-mri","family":"elbow","focus":["nerves"],"reporting_aim":"Inspect medial ulnar nerve, anterior distal biceps and lateral radiocapitellar relationships."},"rad.5.paeds-hip-elbow":{"id":"radiology-model-rad.5.paeds-hip-elbow","title":"Developmental Dysplasia of the Hip and the Child's Elbow · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Identify cartilaginous femoral-head coverage and acetabular relationships; paediatric elbow ossification requires its dedicated images.","scenario":"radiology-reference:rad.5.paeds-hip-elbow","family":"hip","focus":["growth"],"reporting_aim":"Identify cartilaginous femoral-head coverage and acetabular relationships; paediatric elbow ossification requires its dedicated images."},"rad.4.paediatric":{"id":"radiology-model-rad.4.paediatric","title":"Imaging the Child · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Distinguish growth plate and epiphysis from shaft; skeletal maturity is intentionally not assigned an age.","scenario":"radiology-reference:rad.4.paediatric","family":"longbone","focus":["physis"],"reporting_aim":"Distinguish growth plate and epiphysis from shaft; skeletal maturity is intentionally not assigned an age."},"rad.5.child-abuse":{"id":"radiology-model-rad.5.child-abuse","title":"Non-accidental Injury · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Review metaphyseal and cortical landmarks systematically; normal schematic anatomy neither establishes nor excludes injury.","scenario":"radiology-reference:rad.5.child-abuse","family":"longbone","focus":["metaphysis"],"reporting_aim":"Review metaphyseal and cortical landmarks systematically; normal schematic anatomy neither establishes nor excludes injury."},"rad.5.paeds-masses-neuro":{"id":"radiology-model-rad.5.paeds-masses-neuro","title":"Paediatric Masses and Neonatal Neurosonography · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Use ventricular and midline landmarks for neonatal neurosonographic orientation; masses and age-specific dimensions are not simulated.","scenario":"radiology-reference:rad.5.paeds-masses-neuro","family":"brain","focus":["ventricles"],"reporting_aim":"Use ventricular and midline landmarks for neonatal neurosonographic orientation; masses and age-specific dimensions are not simulated."},"rad.5.paeds-chest":{"id":"radiology-model-rad.5.paeds-chest","title":"The Neonatal and Paediatric Chest · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Locate thymic, airway and mediastinal relationships in a stylised chest; proportions are not age-calibrated.","scenario":"radiology-reference:rad.5.paeds-chest","family":"thorax","focus":["thymus"],"reporting_aim":"Locate thymic, airway and mediastinal relationships in a stylised chest; proportions are not age-calibrated."},"rad.5.paeds-abdomen":{"id":"radiology-model-rad.5.paeds-abdomen","title":"The Paediatric Acute Abdomen · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace ileocaecal and duodenal relationships; rotation anomalies and obstruction require age-appropriate clinical imaging.","scenario":"radiology-reference:rad.5.paeds-abdomen","family":"bowel","focus":["ileum"],"reporting_aim":"Trace ileocaecal and duodenal relationships; rotation anomalies and obstruction require age-appropriate clinical imaging."},"rad.5.neonatal-spine":{"id":"radiology-model-rad.5.neonatal-spine","title":"Neonatal Spine Ultrasound · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Trace cord within canal and toward the tapering conus; this short segment is unnumbered and cannot establish conus level.","scenario":"radiology-reference:rad.5.neonatal-spine","family":"spine","focus":["cord"],"reporting_aim":"Trace cord within canal and toward the tapering conus; this short segment is unnumbered and cannot establish conus level."},"rad.5.craniosynostosis":{"id":"radiology-model-rad.5.craniosynostosis","title":"Craniosynostosis and Skull Shape · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Rotate to inspect sagittal, coronal, lambdoid and metopic sutural positions without implying fusion.","scenario":"radiology-reference:rad.5.craniosynostosis","family":"skull","focus":["sutures"],"reporting_aim":"Rotate to inspect sagittal, coronal, lambdoid and metopic sutural positions without implying fusion."},"rad.5.nuclear-general":{"id":"radiology-model-rad.5.nuclear-general","title":"Bone Scan, V/Q, Thyroid and Sentinel Node · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Map organs and skeleton to functional-imaging locations; colour identifies anatomy and does not represent tracer uptake.","scenario":"radiology-reference:rad.5.nuclear-general","family":"nuclear","focus":["skeleton"],"reporting_aim":"Map organs and skeleton to functional-imaging locations; colour identifies anatomy and does not represent tracer uptake."},"rad.5.pet-ct":{"id":"radiology-model-rad.5.pet-ct","title":"FDG PET/CT in Oncology · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Correlate a functional-imaging focus with organ position; physiologic and pathologic uptake are not simulated.","scenario":"radiology-reference:rad.5.pet-ct","family":"nuclear","focus":["organs"],"reporting_aim":"Correlate a functional-imaging focus with organ position; physiologic and pathologic uptake are not simulated."},"rad.5.theranostics":{"id":"radiology-model-rad.5.theranostics","title":"PSMA, DOTATATE and Theranostics · 3D landmarks","instructions":"Drag to rotate; choose a reporting landmark and move the section plane. Relate target assessment to whole-body organ distribution; tracer avidity, eligibility and dosimetry are not calculated.","scenario":"radiology-reference:rad.5.theranostics","family":"nuclear","focus":["urinary"],"reporting_aim":"Relate target assessment to whole-body organ distribution; tracer avidity, eligibility and dosimetry are not calculated."}};
  const TAU = Math.PI * 2;
  const circle = (center, rx, rz, y = center[1]) => Array.from({ length: 49 }, (_, i) => [center[0] + rx * Math.cos(i * TAU / 48), y, center[2] + rz * Math.sin(i * TAU / 48)]);
  const families = Object.create(null);
  const family = (id, landmarks, build, note) => { families[id] = { landmarks, build, note }; };
  // X increases toward the patient's left, Y superiorly, Z anteriorly.
  // Anatomy is deliberately simplified and does not encode diagnostic thresholds.
  function painter(g, s, spec) {
    const palette = ['teal', 'blue', 'plum', 'gold', 'green', 'blue', 'teal', 'plum'];
    const keys = Object.keys(spec.landmarks), anchors = new Map(), annotated = new Set();
    function style(key, position, opacity = .55) {
      if (!anchors.has(key)) anchors.set(key, position);
      const selected = s.focus === key;
      const color = selected ? g.colors.coral : g.colors[palette[Math.max(0, keys.indexOf(key)) % palette.length]];
      return { color, opacity: selected ? Math.max(.58, opacity) : s.context === 'outline' ? .10 : opacity };
    }
    return {
      ell(key, p, r, opacity = .35, range = [0, TAU]) {
        const st = style(key, p, opacity);
        g.mesh((u, v) => { const a = u * Math.PI, b = range[0] + v * (range[1] - range[0]);
          return [p[0] + r[0] * Math.sin(a) * Math.cos(b), p[1] + r[1] * Math.cos(a), p[2] + r[2] * Math.sin(a) * Math.sin(b)];
        }, 8, 12, st.color, { opacity: st.opacity, stroke: false });
      },
      line(key, points, width = 6, opacity = .9) {
        const st = style(key, points[Math.floor(points.length / 2)], opacity);
        g.line(points, st.color, { width: s.focus === key ? width + 1.5 : width, opacity: st.opacity });
      },
      box(key, p, size, opacity = .4) {
        const st = style(key, p, opacity); g.box(p, size, st.color, { opacity: st.opacity, stroke: false });
      },
      poly(key, points, opacity = .35) {
        const p = [0,1,2].map(axis => points.reduce((sum, q) => sum + q[axis], 0) / points.length);
        const st = style(key, p, opacity); g.polygon(points, st.color, { opacity: st.opacity, stroke: false });
      },
      ring(key, p, rx, rz, width = 5) { this.line(key, circle(p, rx, rz), width); },
      annotation(key, p, text) {
        if (s.labels !== 'hide' && (s.focus === key || s.labels === 'all')) { g.label(p, text); annotated.add(key); }
      },
      labels() {
        if (s.labels === 'hide') return;
        anchors.forEach((p, key) => {
          if (!annotated.has(key) && (s.labels === 'all' || s.focus === key)) g.label(p, spec.landmarks[key] || key);
        });
      },
    };
  }
  family('acquisition', { target: 'Imaged target', plane: 'Section location', beam: 'Beam path', detector: 'Detector plane' }, (s,h) => {
    h.ell('target', [0,0,0], [.55,.8,.48]);
    h.line('beam', [[-1.05,.8,.9],[0,0,0],[.9,-.6,-.7]], 4);
    h.poly('beam', [[-1.05,.8,.9],[.8,-.95,-.7],[.8,.75,-.7]], .12);
    h.box('detector', [.9,-.15,-.75], [.05,1.65,1.2]);
    h.line('detector', Array.from({length:49}, (_,i) => [1.05*Math.cos(i*TAU/48),1.05*Math.sin(i*TAU/48),0]), 4);
    const axis={axial:1,coronal:2,sagittal:0}[s.plane];
    h.line('plane',[[-.8,-.8],[.8,-.8],[.8,.8],[-.8,.8],[-.8,-.8]].map(([a,b])=>{
      const p=[0,0,0];p[axis]=s.position;p[(axis+1)%3]=a;p[(axis+2)%3]=b;return p;
    }),3);
  }, 'An acquisition geometry demonstration, not a CT or MR scanner simulation. Section planes are spatial guides; the drawing does not generate diagnostic image pixels.');
  family('access', { target: 'Target', vessel: 'Vessel', needle: 'Proposed path', boundary: 'Tissue boundary' }, (s,h) => {
    h.ell('target', [.25,-.15,0], [.34,.34,.3]);
    h.line('vessel', [[-.4,-1,-.3],[-.35,-.3,-.25],[-.6,.7,-.2],[-.5,1.1,-.25]], 13);
    h.line('needle', [[1,.95,.8],[.65,.48,.42],[.25,-.15,0]], 4);
    h.box('boundary', [0,0,-.6],[1.7,2,.08],.12);
    [-.8,-.25,.3,.85].forEach(y => h.line('boundary',[[-.85,y,.45],[-.5,y+.15,.7],[.1,y+.17,.75]],8,.32));
  }, 'Target, vessel and needle path are abstract procedural landmarks. A visually clear path here does not establish safety, sterility, coagulation suitability or a patient-specific access route.');
  function thorax(s,h) {
    h.ell('lobes',[-.58,.4,0],[.4,.7,.43]); h.ell('lobes',[-.62,-.43,-.13],[.44,.55,.4]);
    h.ell('lobes',[-.56,-.25,.35],[.37,.26,.24]);
    h.ell('lobes',[.58,.38,.06],[.4,.7,.4]); h.ell('lobes',[.64,-.45,-.16],[.4,.5,.38]);
    [['RUL',[-.58,.72,0]],['RML',[-.62,-.22,.42]],['RLL',[-.72,-.62,-.21]],['LUL',[.59,.73,.08]],['LLL',[.71,-.61,-.2]]]
      .forEach(([text,p])=>h.annotation('lobes',p,text));
    [-1,1].forEach(side => {
      h.ell('pleura',[side*.6,-.05,0],[.49,1.03,.52],.08);
      h.line('airway',[[0,.42,.05],[side*.31,.05,.03],[side*.59,.45,-.05]],6);
      h.line('airway',[[side*.31,.05,.03],[side*.49,-.3,-.05],[side*.62,-.67,-.16]],6);
      h.line('pulmonary',[[.12,.07,.3],[side*.32,.13,.24],[side*.62,.43,.2]],6);
      h.line('pulmonary',[[side*.32,.13,.24],[side*.55,-.54,.17]],6);
      h.line('lobes',[[side*.97,-.04,.2],[side*.67,-.2,.35],[side*.3,-.46,.1]],2,.9);
    });
    h.line('airway',[[0,1.15,.05],[0,.42,.05]],8);
    h.ell('heart',[.18,-.37,.2],[.39,.48,.36],.24);
    h.box('mediastinum',[0,.22,-.2],[.35,1.6,.43],.12);
    h.ell('thymus',[0,.62,.45],[.28,.25,.12],.25);
  }
  family('thorax', { lobes:'Lobar landmarks',airway:'Trachea / bronchi',pulmonary:'Pulmonary arteries',pleura:'Pleural envelope',heart:'Cardiac silhouette',mediastinum:'Mediastinum',thymus:'Thymic region' }, thorax,
    'Five lobar volumes, central airways and pulmonary arteries are simplified. Fissures, segmental bronchovascular anatomy, lymph-node stations and age-specific proportions must be checked on the clinical examination.');
  function heart(s,h) {
    h.ell('atria',[-.48,.4,-.05],[.28,.33,.31]); h.ell('atria',[.28,.44,-.27],[.3,.28,.28]);
    h.ell('ventricles',[.39,-.28,.02],[.4,.65,.36]); h.ell('ventricles',[-.21,-.15,.32],[.38,.49,.25]);
    h.annotation('atria',[-.48,.4,-.05],'RA'); h.annotation('atria',[.28,.44,-.27],'LA');
    h.annotation('ventricles',[.39,-.45,.02],'LV'); h.annotation('ventricles',[-.21,-.15,.32],'RV');
    h.line('outflow',[[.07,.04,0],[.04,.72,0],[.17,1,.02],[.43,1,-.2],[.6,.7,-.32]],12);
    h.line('outflow',[[-.19,.02,.4],[-.2,.72,.48],[.12,.82,.44],[.52,.7,.36]],11);
    h.line('septum',[[.04,.26,.07],[.12,-.67,.13]],5);
  }
  family('heart',{ventricles:'Ventricles',atria:'Atria',outflow:'Great-vessel outflow',septum:'Ventricular septum'},heart,
    'Usual chamber connections are shown in a schematic orientation. Valves, conduction tissue, myocardial segments, shunts, function and scar are not resolved.');
  family('coronary',{lad:'LAD / diagonals',lcx:'LCx / obtuse marginal',rca:'RCA / PDA',origins:'Aortic root / LM',myocardium:'Myocardial reference'},(s,h)=>{
    h.ell('myocardium',[.13,-.12,0],[.63,.85,.49],.17);
    h.line('origins',[[0,.4,.13],[0,.99,.08]],15);
    h.line('origins',[[.05,.6,.16],[.26,.46,.38]],7);
    h.line('lad',[[.26,.46,.38],[.2,.17,.5],[.32,-.32,.48],[.35,-.8,.14]],7);
    h.line('lad',[[.22,.12,.49],[.55,-.02,.4],[.66,-.25,.22]],4);
    h.line('lcx',[[.26,.46,.38],[.55,.4,.2],[.7,.21,-.13],[.58,.09,-.42],[.2,.04,-.48]],7);
    h.line('lcx',[[.69,.24,-.12],[.66,-.35,-.25],[.44,-.65,-.32]],4);
    h.line('rca',[[-.04,.62,.22],[-.37,.4,.43],[-.54,.13,.36],[-.49,-.3,.08],[-.24,-.52,-.36],[.05,-.4,-.5],[.26,-.72,-.19]],7);
  },'Stylised epicardial coronary courses with right dominance: the PDA arises from the RCA. Vessel calibre, stenosis, plaque, anomalous courses and CAD-RADS are not calculated. Rotate to see the posterior LCx and PDA.');
  family('aorta',{root:'Aortic root',arch:'Arch / descending',branches:'Branch vessels',iliacs:'Iliac access'},(s,h)=>{
    h.line('root',[[-.25,.14,.35],[-.25,.65,.35]],18);
    h.line('arch',[[-.25,.65,.35],[-.2,.98,.29],[.02,1.11,.06],[.32,1.03,-.2],[.4,.74,-.35],[.36,.1,-.35],[.3,-.7,-.31]],15);
    h.line('branches',[[-.12,.96,.24],[-.42,1.25,.15],[-.69,1.35,.1]],7);
    h.line('branches',[[.07,1.08,.03],[.05,1.38,-.03]],6); h.line('branches',[[.27,1.05,-.14],[.55,1.25,-.16]],6);
    h.line('branches',[[.32,-.02,-.33],[.29,-.13,.15]],6);
    [-1,1].forEach(side=>{h.line('branches',[[.31,-.25,-.32],[side*.66,-.3,-.3]],6); h.line('iliacs',[[.3,-.7,-.31],[side*.48,-.94,-.18],[side*.58,-1.19,.02]],9);});
  },'Aortic and branch trajectories are simplified; branch variants, lumen shape, wall layers and access-vessel tortuosity are not reproduced. No dimensions or device-sizing decisions derive from this geometry.');
  family('brain',{territories:'Cortical territories',ventricles:'Ventricular system',deep:'Deep nuclei',hippocampi:'Hippocampi',meninges:'Brain surface',sinus:'Sagittal sinus'},(s,h)=>{
    [-1,1].forEach(side=>{
      h.ell('meninges',[side*.39,.15,0],[.55,.84,.87],.1);
      h.ell('territories',[side*.24,.73,.16],[.17,.23,.59],.33);
      h.ell('territories',[side*.72,.23,.07],[.21,.42,.52],.34);
      h.ell('territories',[side*.35,.15,-.71],[.28,.31,.19],.34);
      if(side===1){h.annotation('territories',[.24,.83,.17],'ACA');h.annotation('territories',[.85,.21,.08],'MCA');h.annotation('territories',[.35,.1,-.85],'PCA');}
      h.ell('deep',[side*.28,.05,.07],[.18,.22,.26],.4);
      h.line('ventricles',[[side*.18,.35,.36],[side*.24,.49,.12],[side*.26,.37,-.25],[side*.27,.06,-.39],[side*.3,-.19,-.14]],8);
      h.line('hippocampi',[[side*.5,-.35,.22],[side*.45,-.3,-.1],[side*.42,-.22,-.46]],9);
    });
    h.line('ventricles',[[0,.13,.03],[0,-.26,-.18],[0,-.59,-.36]],7);
    h.line('sinus',Array.from({length:25},(_,i)=>{const a=i*Math.PI/24;return[0,.12+.9*Math.sin(a),.9*Math.cos(a)];}),5);
    h.ell('meninges',[0,-.7,-.48],[.45,.3,.38],.2);
  },'Territories show only broad medial (ACA), lateral (MCA) and posterior (PCA) cortical locations; borders vary. Surface, deep nuclei, ventricles and hippocampi are idealised. No lesion, perfusion map or atrophy score is generated.');
  family('spine',{bodies:'Vertebral bodies',discs:'Intervertebral discs',canal:'Spinal canal',cord:'Cord / conus',foramina:'Foraminal exits'},(s,h)=>{
    [-.84,-.42,0,.42,.84].forEach(y=>{
      h.box('bodies',[0,y,.27],[.57,.3,.5]); h.ell('canal',[0,y,-.2],[.3,.15,.24],.12);
      h.line('bodies',[[-.27,y,.05],[-.36,y,-.27],[0,y,-.56],[.36,y,-.27],[.27,y,.05]],8,.55);
      [-1,1].forEach(side=>h.line('foramina',[[0,y-.15,-.21],[side*.46,y-.2,-.1]],4));
    });
    [-.63,-.21,.21,.63].forEach(y=>h.ell('discs',[0,y,.27],[.32,.06,.29],.65));
    h.line('cord',[[0,1.05,-.18],[0,.34,-.18],[0,-.4,-.18],[0,-.65,-.19]],10);
    h.poly('cord',[[-.065,-.6,-.18],[.065,-.6,-.18],[0,-.94,-.18]],.8);
    h.line('cord',[[0,-.88,-.18],[0,-1.13,-.18]],3);
  },'An unnumbered short spinal segment illustrates body/disc, canal and foraminal relationships. The conus location is illustrative and cannot establish a vertebral level, cord termination, stenosis or instability.');
  family('sella',{gland:'Pituitary gland',chiasm:'Optic chiasm',carotids:'Cavernous carotids',stalk:'Pituitary stalk',sphenoid:'Sphenoid sinus'},(s,h)=>{
    h.ell('gland',[0,-.15,0],[.42,.27,.33],.6);
    h.line('stalk',[[0,.03,0],[0,.65,-.12]],7);
    h.line('chiasm',[[-.66,.55,.45],[0,.47,.2],[.56,.5,-.2]],8); h.line('chiasm',[[.66,.55,.45],[0,.47,.2],[-.56,.5,-.2]],8);
    [-1,1].forEach(side=>h.line('carotids',[[side*.6,-.7,-.35],[side*.56,-.25,-.28],[side*.61,.11,.15],[side*.57,.39,.1]],11));
    h.ell('sphenoid',[0,-.68,.1],[.53,.27,.52],.18);
  },'The sellar region is enlarged to show relationships. The chiasm is superior, cavernous carotids lateral and sphenoid sinus inferior; variants and cavernous-sinus compartments require patient imaging.');
  family('neck',{spaces:'Deep neck spaces',pharynx:'Pharyngeal lumen',carotids:'Carotid spaces',nodes:'Jugular-chain region',thyroid:'Thyroid / isthmus'},(s,h)=>{
    h.line('pharynx',[[0,1,.28],[0,.33,.28],[0,-.25,.25],[0,-1,.29]],19,.38);
    h.box('spaces',[0,.45,-.22],[.63,1.1,.17],.24);
    [-1,1].forEach(side=>{
      h.ell('spaces',[side*.36,.53,.05],[.17,.5,.25],.35);
      h.line('carotids',[[side*.55,-1,0],[side*.52,.15,0],[side*.57,1.05,-.08]],10);
      [.8,.35,-.12,-.55].forEach(y=>h.ell('nodes',[side*.77,y,.05],[.1,.15,.11],.5));
      h.ell('thyroid',[side*.25,-.56,.39],[.2,.35,.18],.6);
    });
    h.box('thyroid',[0,-.63,.45],[.25,.13,.12],.6);
  },'A schematic combines supra- and infrahyoid landmarks. It illustrates relationships rather than exact fascial boundaries or a complete cervical nodal-level map.');
  family('orbit',{globe:'Globes',optic:'Optic nerves / apex',muscles:'Extraocular muscles',walls:'Orbital walls'},(s,h)=>{
    [-1,1].forEach(side=>{
      h.ell('globe',[side*.58,.1,.55],[.31,.31,.31],.65);
      h.line('optic',[[side*.58,.1,.3],[side*.42,.08,-.25],[side*.24,.03,-.65]],8);
      [-1,1].forEach(d=>{
        h.line('muscles',[[side*.55,d*.25,.51],[side*.5,d*.19,.02],[side*.24,.02,-.57]],5);
        h.line('muscles',[[side*.58+d*.28,.1,.52],[side*.5+d*.2,.1,.05],[side*.24,.02,-.57]],5);
      });
      h.line('walls',[[side*.98,-.4,.75],[side*.94,.52,.7],[side*.2,.39,-.76],[side*.2,-.28,-.77],[side*.98,-.4,.75]],3,.5);
    });
  },'Orbital geometry is enlarged and simplified. Extraocular muscle origins, orbital apex and optic nerve course are schematic; blowout defects, entrapment and optic neuropathy cannot be inferred.');
  family('sinuses',{frontal:'Frontal sinuses',ethmoid:'Ethmoid region',maxillary:'Maxillary sinuses',sphenoid:'Sphenoid sinuses',orbits:'Orbital reference'},(s,h)=>{
    [-1,1].forEach(side=>{
      h.ell('frontal',[side*.31,.88,.2],[.26,.3,.27],.5);
      h.ell('maxillary',[side*.62,-.47,.25],[.38,.48,.4],.45);
      h.ell('sphenoid',[side*.21,.08,-.6],[.23,.29,.3],.55);
      for(let i=0;i<3;i++)h.ell('ethmoid',[side*.2,.15,.42-i*.24],[.11,.26,.12],.6);
      h.ell('orbits',[side*.66,.28,.21],[.33,.35,.48],.08);
    });
  },'Paranasal cavities are grouped spatially, without air-cell variants or an ostiomeatal-complex model. Review drainage pathways, orbit and skull-base margins on the examination.');
  family('temporal',{canal:'External / middle ear',ossicles:'Ossicular chain',labyrinth:'Cochlea / vestibule',venous:'Sigmoid / jugular bulb',iac:'Internal acoustic canal'},(s,h)=>{
    h.line('canal',[[1.1,0,.1],[.7,0,.1],[.35,0,.08]],14,.5);
    [[.29,.08,.07],[.1,.16,.08],[-.08,.09,.04]].forEach(p=>h.ell('ossicles',p,[.085,.13,.08],.8));
    h.line('labyrinth',Array.from({length:65},(_,i)=>{let t=i/64*TAU*2.4,r=.035+.2*i/64;return[-.42+r*Math.cos(t),-.13+r*Math.sin(t),.2-i*.003];}),5);
    h.line('labyrinth',Array.from({length:49},(_,i)=>[-.42+.26*Math.cos(i*TAU/48),.44+.29*Math.sin(i*TAU/48),-.23]),5);
    h.line('labyrinth',Array.from({length:49},(_,i)=>[-.49,.39+.26*Math.sin(i*TAU/48),-.22+.27*Math.cos(i*TAU/48)]),5);
    h.line('venous',[[.22,.95,-.55],[.4,.4,-.55],[.39,-.19,-.42],[.26,-.55,-.35],[.31,-.99,-.38]],12);
    h.line('iac',[[-.42,.2,-.16],[-.95,.24,-.2]],9);
  },'An enlarged left-ear orientation model separates external, middle and inner ear from posterior venous landmarks. Small structures and distances are exaggerated; bony canals, dehiscence and vascular variants need thin-section imaging.');
  family('swallow',{esophagus:'Oesophagus',airway:'Larynx / trachea',epiglottis:'Epiglottic region',pharynx:'Pharynx'},(s,h)=>{
    h.line('pharynx',[[0,1.12,0],[0,.65,-.1],[0,.2,-.12]],19,.5);
    h.line('esophagus',[[0,.18,-.18],[0,-.45,-.25],[0,-1.15,-.26]],14);
    h.line('airway',[[0,.25,.3],[0,-.28,.4],[0,-1.13,.42]],18);
    h.ell('epiglottis',[0,.5,.27],[.19,.25,.06],.7);
    h.line('pharynx',[[-.38,.63,.1],[0,.56,.35],[.38,.63,.1]],6);
  },'Static midline relationships only: posterior oesophagus and anterior airway. Bolus transit, airway protection, motility, aspiration and normal timing are not simulated.');
  family('trigeminal',{pons:'Pons',nerve:'Cisternal CN V',cave:'Meckel cave',divisions:'V1 / V2 / V3'},(s,h)=>{
    h.ell('pons',[0,0,-.57],[.48,.5,.35],.3);
    [-1,1].forEach(side=>{
      h.line('nerve',[[side*.3,.05,-.33],[side*.65,.03,.01]],8);
      h.ell('cave',[side*.68,.05,.16],[.17,.16,.2],.55);
      [[.88,.5,.73],[1,.08,.79],[.92,-.57,.53]].forEach(end=>h.line('divisions',[[side*.72,.04,.28],[side*end[0],end[1],end[2]]],5));
    });
  },'CN V is represented from the pons through Meckel cave to three separated divisions. No vessel contact, compression, nerve calibre, enhancement or foraminal pathology is modelled.');
  family('liver',{segments:'Couinaud segments',portal:'Portal branches',hepatic:'Hepatic veins / IVC',gallbladder:'Gallbladder landmark'},(s,h)=>{
    const lobes = [
      ['I',[.03,.12,-.57],[.19,.35,.21]], ['II',[.75,.41,-.13],[.31,.36,.31]],
      ['III',[.75,-.38,.24],[.3,.35,.35]], ['IVa',[.22,.42,.32],[.25,.36,.34]],
      ['IVb',[.2,-.36,.35],[.26,.34,.31]], ['V',[-.4,-.38,.31],[.36,.35,.36]],
      ['VI',[-.61,-.35,-.39],[.33,.35,.32]], ['VII',[-.63,.43,-.35],[.34,.35,.35]],
      ['VIII',[-.37,.43,.3],[.36,.37,.37]]];
    lobes.forEach(([label,p,r])=>{
      h.ell('segments',p,r,.25);
      // Numerals remain attached to their segment when the user rotates.
      h.annotation('segments',p,label);
    });
    h.line('portal',[[.02,-.77,-.24],[.02,-.09,-.18],[-.57,-.07,-.04]],8);
    h.line('portal',[[.02,-.09,-.18],[.43,.11,.02],[.8,.12,.14]],8);
    h.line('hepatic',[[.02,-.77,-.73],[.02,.89,-.73]],12);
    [[-.77,.1,-.28],[-.14,.11,.38],[.72,.33,.03]].forEach(p=>h.line('hepatic',[p,[0,.8,-.65]],6));
    h.ell('gallbladder',[-.06,-.62,.64],[.13,.27,.13],.6);
  },'Couinaud locations are schematic: II/III left lateral, IV left medial, V/VIII right anterior, VI/VII right posterior and I caudate posterior. Portal and venous landmarks are guides; actual boundaries and volumes vary.');
  family('pancreatobiliary',{pancreas:'Pancreas',ducts:'Bile / pancreatic ducts',vessels:'Portal / mesenteric',duodenum:'Duodenal loop',gallbladder:'Gallbladder'},(s,h)=>{
    h.ell('pancreas',[-.59,-.13,.17],[.31,.4,.25],.55);
    h.ell('pancreas',[-.1,.04,.1],[.43,.21,.21],.55); h.ell('pancreas',[.57,.18,.02],[.46,.16,.16],.55);
    h.line('ducts',[[.94,.18,.08],[.34,.15,.14],[-.3,.03,.25],[-.55,-.27,.31],[-.82,-.26,.29]],5);
    h.line('ducts',[[-.42,.96,.16],[-.48,.52,.17],[-.49,.05,.2],[-.62,-.26,.31],[-.82,-.26,.29]],6);
    h.line('ducts',[[-.48,.69,.17],[-.07,.9,.08]],5);
    h.ell('gallbladder',[-.84,.55,.4],[.17,.35,.18],.5); h.line('ducts',[[-.83,.68,.38],[-.48,.53,.17]],4);
    h.line('duodenum',[[-.39,.44,.23],[-.93,.35,.23],[-1.04,-.2,.26],[-.79,-.58,.09],[-.27,-.48,-.03],[.1,-.25,-.02]],11);
    h.line('vessels',[[0,-.98,-.15],[0,.02,-.2],[-.1,.72,-.18]],11);
    h.line('vessels',[[.96,.18,-.22],[.37,.13,-.2],[0,.02,-.2]],6);
    h.line('vessels',[[.21,-.98,-.31],[.21,-.1,-.31],[.13,.38,-.42]],6);
  },'The pancreatic head lies in the duodenal loop on the patient’s right; body and tail extend left. Ducts and adjacent vessels are separated for visibility. No duct diameter, vessel contact angle or resectability is calculated.');
  function bowel(s,h) {
    h.line('colon',[[-.79,-.48,.18],[-.87,.08,.03],[-.8,.75,-.05],[-.26,.66,.17],[.3,.67,.16],[.82,.78,-.08],[.9,.2,.02],[.77,-.4,.07],[.36,-.62,.26],[.22,-.93,-.18],[0,-1.15,-.22]],15);
    h.ell('caecum',[-.77,-.56,.15],[.22,.25,.22],.6);
    h.line('appendix',[[-.87,-.65,.17],[-1,-.8,.11],[-.96,-1.02,.04]],6);
    const loops=Array.from({length:100},(_,i)=>{const t=i/99*TAU*2.6;return[.5*Math.sin(t),.38-.92*i/99,.28+.25*Math.cos(t)];});
    h.line('smallbowel',loops,9,.78);
    h.line('ileum',[[.16,-.6,.32],[-.15,-.65,.38],[-.48,-.54,.24],[-.72,-.48,.15]],11);
    h.line('mesentery',[[.07,.9,-.28],[.1,.4,-.15],[.11,-.28,.1]],7);
    [-.43,-.1,.31,.52].forEach(x=>h.line('mesentery',[[.1,.4,-.15],[x,-.22,.25]],3));
  }
  family('bowel',{colon:'Colon / rectum',caecum:'Caecum',appendix:'Appendix',smallbowel:'Small bowel loops',ileum:'Terminal ileum',mesentery:'Mesenteric root'},bowel,
    'The bowel layout shows broad continuity and mesenteric relationships only; loops, appendix position and mesenteric orientation vary. Wall layers, vascular patency, distension and a transition point are not simulated.');
  family('abdomen',{solid:'Solid organs',bowel:'Bowel compartment',vessels:'Great vessels',spaces:'Peritoneal spaces'},(s,h)=>{
    h.ell('solid',[-.51,.62,.14],[.59,.37,.49],.4); h.ell('solid',[.86,.55,-.08],[.19,.35,.29],.5);
    [-1,1].forEach(side=>h.ell('solid',[side*.56,.07,-.4],[.2,.35,.17],.5));
    h.line('vessels',[[.08,1,-.52],[.1,-.77,-.52]],10);
    h.ell('bowel',[0,-.37,.21],[.73,.59,.38],.16);
    h.poly('spaces',[[-1,.28,.1],[-.84,-.74,.17],[-.15,-1.05,.08],[.89,-.67,.14],[1,.29,.08]],.08);
    h.line('spaces',[[-.98,.3,.22],[-.91,-.7,.26],[-.08,-1.08,.25],[.89,-.69,.23],[.99,.27,.18]],4,.55);
  },'Organ envelopes and paracolic/pelvic recess relationships are simplified. Peritoneal reflections, retroperitoneal compartments, mesenteric vessels and injury grades require cross-sectional images.');
  family('renal',{kidneys:'Kidneys',sinus:'Renal sinus / hilum',collecting:'Collecting system',adrenals:'Adrenal glands',vessels:'Renal vessels'},(s,h)=>{
    [-1,1].forEach(side=>{
      h.ell('kidneys',[side*.66,.24,-.08],[.31,.58,.3],.3);
      h.ell('sinus',[side*.54,.2,.06],[.13,.28,.15],.55);
      h.line('collecting',[[side*.52,.25,.1],[side*.39,-.03,.12],[side*.35,-.65,.12],[side*.17,-1,.3]],6);
      [-.1,.53].forEach(y=>h.line('collecting',[[side*.52,.25,.1],[side*.7,y,-.05]],4));
      h.line('vessels',[[.04,.26,-.41],[side*.5,.2,-.01]],6);
      h.poly('adrenals',[[side*.65,.78,-.07],[side*.4,1.04,-.07],[side*.39,.82,.12],[side*.74,.82,.1]],.7);
    });
    h.line('vessels',[[.04,-.85,-.41],[.04,1.05,-.41]],10);
    h.ell('collecting',[0,-1.04,.29],[.27,.2,.21],.35);
  },'Paired renal, suprarenal and collecting-system locations are shown. Kidneys are simplified envelopes; renal segmental anatomy, lesion complexity, adrenal chemical shift and enhancement are not represented.');
  family('rectal',{wall:'Rectal wall',mesorectum:'Mesorectal envelope',sphincter:'Anal sphincter region',levator:'Levator plane',bladder:'Anterior bladder'},(s,h)=>{
    h.ell('mesorectum',[0,.37,-.18],[.6,.75,.49],.13);
    h.line('wall',[[0,1.09,-.17],[0,.56,-.22],[0,.05,-.17],[0,-.55,.03]],24,.8);
    h.line('sphincter',[[0,-.48,.02],[0,-1,.16]],30,.32);
    h.line('sphincter',[[0,-.48,.02],[0,-1,.16]],14,.95);
    h.poly('levator',[[-.93,-.17,-.28],[-.45,-.68,.15],[0,-.79,.19],[.45,-.68,.15],[.93,-.17,-.28],[0,-.34,-.71]],.35);
    h.ell('bladder',[0,.09,.72],[.42,.37,.27],.22);
  },'Rectum, mesorectal envelope and pelvic-floor relationships are schematic. The sphincter region is shown as nested contours; tumour stage, mesorectal-fascia distance, fistula grade and organ descent are not calculated.');
  family('prostate',{peripheral:'Peripheral zone',transition:'Transition zone',central:'Central zone',stroma:'Anterior stroma',urethra:'Urethra / apex',vesicles:'Seminal vesicles',rectum:'Posterior rectum'},(s,h)=>{
    // Posterolateral shell: Z <= 0.12; anterior sector is omitted deliberately.
    h.ell('peripheral',[0,-.08,.05],[.7,.7,.52],.5,[Math.PI*.93,TAU+Math.PI*.07]);
    [-1,1].forEach(side=>{
      h.ell('transition',[side*.23,-.04,.22],[.26,.52,.29],.5);
      h.ell('vesicles',[side*.43,.84,-.18],[.29,.32,.19],.6);
      h.line('central',[[side*.28,.63,-.12],[side*.12,.29,-.14],[0,.08,-.01]],7);
    });
    h.ell('central',[0,.39,-.13],[.25,.25,.22],.4);
    h.ell('stroma',[0,-.07,.51],[.51,.53,.065],.55);
    h.line('urethra',[[0,.67,.22],[0,.04,.13],[0,-.76,.11],[0,-1.02,.17]],7);
    h.line('rectum',[[0,.95,-.77],[0,.1,-.81],[0,-.9,-.62]],20,.3);
  },'Peripheral zone is posterolateral, transition zone surrounds the proximal urethra, central zone surrounds the ejaculatory ducts near the base, and fibromuscular stroma is anterior. This is zonal anatomy, not the full PI-RADS sector map or a lesion score.');
  family('bladder',{wall:'Bladder wall',lumen:'Bladder lumen',ureters:'Ureteric entry',perivesical:'Perivesical envelope',outlet:'Bladder outlet'},(s,h)=>{
    h.ell('perivesical',[0,.12,.09],[.8,.87,.69],.07);
    h.ell('wall',[0,.12,.09],[.67,.73,.57],.27);
    h.ell('lumen',[0,.14,.09],[.58,.65,.48],.2);
    [-1,1].forEach(side=>h.line('ureters',[[side*.65,1,-.5],[side*.52,.26,-.38],[side*.26,-.21,-.3]],6));
    h.line('outlet',[[0,-.56,.03],[0,-1.08,.11]],8);
  },'Nested envelopes distinguish lumen, muscular-wall region and perivesical tissue. Wall thickness is deliberately exaggerated. This schematic cannot distinguish VI-RADS categories or demonstrate invasion.');
  family('female',{uterus:'Uterus / myometrium',endometrium:'Endometrial cavity',cervix:'Cervix',ovaries:'Ovaries / tubes',bladder:'Bladder',rectum:'Rectum'},(s,h)=>{
    h.ell('uterus',[0,.39,.13],[.48,.56,.33],.38);
    h.line('endometrium',[[0,-.02,.09],[0,.68,.22]],8);
    h.line('endometrium',[[-.28,.67,.17],[0,.55,.16],[.28,.67,.17]],5);
    h.ell('cervix',[0,-.24,.04],[.24,.28,.21],.6);
    h.line('cervix',[[0,-.35,.03],[0,-.85,.05]],15,.35);
    [-1,1].forEach(side=>{
      h.ell('ovaries',[side*.88,.29,.02],[.2,.29,.17],.6);
      h.line('ovaries',[[side*.35,.68,.16],[side*.66,.73,.1],[side*.99,.58,.08],[side*.94,.33,.05]],5);
    });
    h.ell('bladder',[0,-.42,.66],[.43,.34,.29],.2);
    h.line('rectum',[[0,.67,-.65],[0,-.1,-.65],[0,-.91,-.34]],17,.4);
  },'Uterus, cervix and adnexa are oriented against anterior bladder and posterior rectum. Uterine version, shape and adnexal position vary. Junctional-zone thickness, invasion and adnexal risk scores are not encoded.');
  family('scrotum',{testes:'Testes',epididymis:'Epididymides',cord:'Spermatic cords',envelope:'Scrotal envelope'},(s,h)=>{
    [-1,1].forEach(side=>{
      h.ell('testes',[side*.4,-.35,0],[.29,.53,.27],.6);
      h.ell('envelope',[side*.4,-.35,0],[.38,.66,.35],.08);
      h.line('epididymis',[[side*.46,.12,-.22],[side*.57,-.3,-.24],[side*.48,-.79,-.17]],11);
      h.line('cord',[[side*.46,.13,-.2],[side*.48,.61,-.13],[side*.56,1.05,-.13]],8);
    });
  },'Normal positional relationships only. Epididymides lie posterior to the testes and cords extend superiorly. The model does not simulate torsion, flow, echogenicity, hydrocele or lesion vascularity.');
  family('breast',{quadrants:'Breast quadrants',ducts:'Radial ductal paths',nipple:'Nipple',chestwall:'Pectoral boundary',axilla:'Axillary tail'},(s,h)=>{
    // Left breast, with hemispherical anterior projection from the chest wall.
    h.ell('quadrants',[0,0,-.15],[.88,.86,.85],.22,[0,Math.PI]);
    h.box('chestwall',[0,0,-.24],[1.9,1.85,.12],.25);
    h.ell('nipple',[0,0,.77],[.11,.11,.1],.85);
    [[-.57,.53,.23],[.57,.53,.23],[-.57,-.53,.23],[.57,-.53,.23]].forEach(p=>h.line('ducts',[p,[p[0]*.6,p[1]*.6,.5],[0,0,.73]],5));
    h.line('quadrants',[[-.83,0,.17],[0,0,.72],[.83,0,.17]],2);
    h.line('quadrants',[[0,-.83,.17],[0,0,.72],[0,.83,.17]],2);
    h.ell('axilla',[.89,.83,-.02],[.23,.34,.16],.5);
  },'A single left breast is shown: patient-left is lateral. Radial paths, quadrant planes, nipple and pectoral boundary are schematic. Compression, clock-face scoring, calcification morphology and implant integrity are not modelled.');
  family('knee',{bones:'Femur / tibia / fibula',menisci:'Meniscal contours',cruciates:'ACL / PCL',extensor:'Patella / tendon',collaterals:'Collateral ligaments'},(s,h)=>{
    h.box('bones',[0,.8,-.03],[.55,.78,.46],.38);
    [-1,1].forEach(side=>{
      h.ell('bones',[side*.29,.21,-.03],[.26,.36,.35],.4);
      const start=side===1?-.87*Math.PI:.24*Math.PI, end=side===1?.87*Math.PI:1.76*Math.PI;
      h.line('menisci',Array.from({length:37},(_,i)=>{const t=start+(end-start)*i/36;return[side*.29+.23*Math.cos(t),-.21,-.03+.3*Math.sin(t)];}),7);
    });
    h.box('bones',[0,-.75,-.02],[.67,.9,.53],.35);
    h.line('bones',[[.61,-.3,-.16],[.68,-1.15,-.12]],13,.45);
    h.line('cruciates',[[-.11,-.26,.23],[.2,.28,-.21]],7);
    h.line('cruciates',[[.08,-.26,-.26],[-.17,.24,.16]],7);
    h.ell('extensor',[0,.17,.52],[.23,.29,.1],.6); h.line('extensor',[[0,.83,.52],[0,.4,.53]],8);h.line('extensor',[[0,-.07,.53],[0,-.55,.34]],8);
    [-1,1].forEach(side=>h.line('collaterals',[[side*.55,.35,.02],[side*.52,-.45,.02]],5));
  },'A left knee with simplified medial C-shaped and more nearly circular lateral meniscal contours, plus crossing ACL/PCL courses. Wedge thickness, root attachment detail, tears, laxity, cartilage loss and alignment are not simulated.');
  family('shoulder',{humerus:'Humeral head',glenoid:'Glenoid / labrum',cuff:'Rotator cuff paths',acromion:'Acromial arch',biceps:'Long-head biceps'},(s,h)=>{
    h.ell('humerus',[.4,.02,0],[.42,.43,.4],.4); h.line('humerus',[[.51,-.31,.02],[.65,-1.1,.05]],26,.4);
    h.ell('glenoid',[-.12,.02,0],[.08,.35,.27],.6);
    h.line('glenoid',Array.from({length:49},(_,i)=>[-.09,.37*Math.cos(i*TAU/48),.3*Math.sin(i*TAU/48)]),5);
    h.poly('glenoid',[[-.2,.55,-.25],[-1,-.52,-.42],[-.4,-.73,-.1],[-.12,.05,-.15]],.3);
    h.line('acromion',[[-.91,.57,-.17],[-.34,.64,-.12],[.26,.67,-.03],[.61,.56,.04]],12);
    h.line('cuff',[[-.77,.41,-.13],[-.17,.5,0],[.31,.43,.11],[.64,.23,.1]],8);
    h.line('cuff',[[-.81,-.06,-.41],[-.11,.03,-.43],[.5,.13,-.29]],8);
    h.line('cuff',[[-.74,-.05,.32],[-.1,.1,.43],[.45,.09,.34]],8);
    h.line('biceps',[[-.06,.35,.07],[.34,.36,.29],[.57,.01,.4],[.61,-.9,.28]],6);
  },'A left shoulder: superior supraspinatus, posterior cuff and anterior subscapularis paths are simplified. The labral ring and biceps route are orientation aids; no tear, impingement or instability is simulated.');
  family('hip',{pelvis:'Pelvic ring',joint:'Femoral head / neck',labrum:'Acetabular rim',growth:'Cartilage region',shaft:'Proximal femur'},(s,h)=>{
    [-1,1].forEach(side=>{
      h.poly('pelvis',[[side*.38,.93,-.3],[side*.98,.75,-.17],[side*.91,.17,.13],[side*.36,-.31,.18],[side*.12,-.15,.33],[side*.43,.19,-.31]],.35);
      h.ell('joint',[side*.55,.03,.05],[.28,.28,.28],.6);
      h.line('joint',[[side*.58,-.03,.03],[side*.88,-.3,.01]],19);
      h.line('shaft',[[side*.89,-.23,0],[side*.92,-1.1,.02]],22,.5);
      h.ell('growth',[side*.55,.03,.05],[.33,.33,.33],.12);
      h.line('labrum',Array.from({length:33},(_,i)=>[side*(.52+.11*Math.cos(i*TAU/32)),.36*Math.sin(i*TAU/32),.05+.33*Math.cos(i*TAU/32)]),5);
    });
    h.line('pelvis',[[-.11,-.13,.34],[.11,-.13,.34]],7);
  },'Paired hips with acetabular and head-neck relationships. Cartilage is exaggerated as an outer envelope; skeletal maturity, coverage angles, dysplasia and impingement measurements require real age-appropriate imaging.');
  family('ankle',{mortise:'Ankle mortise',hindfoot:'Talus / calcaneus',midfoot:'Midfoot',tendons:'Achilles / flexors',ligaments:'Lateral ligaments'},(s,h)=>{
    h.box('mortise',[-.07,.71,0],[.46,.95,.43],.4);h.line('mortise',[[.47,1.19,-.09],[.5,.01,-.13]],15,.5);
    h.ell('hindfoot',[.02,-.03,.11],[.36,.27,.39],.6);h.ell('hindfoot',[.06,-.52,-.15],[.34,.31,.62],.4);
    h.ell('midfoot',[0,-.26,.68],[.39,.19,.27],.5);h.line('midfoot',[[-.26,-.33,.88],[-.21,-.4,1.18]],12,.5);
    h.line('tendons',[[.08,1.12,-.51],[.08,.1,-.62],[.09,-.51,-.65]],9);
    h.line('tendons',[[-.38,1.1,-.08],[-.39,.04,-.1],[-.35,-.26,.55]],6);
    h.line('ligaments',[[.5,.02,-.11],[.3,-.16,.44]],5);h.line('ligaments',[[.5,.02,-.11],[.36,-.45,-.16]],5);
  },'Left ankle and hindfoot: lateral fibula, talar dome, posterior Achilles and medial flexor route are schematic. Mortise widening, ligament injury and hindfoot alignment are not measured.');
  family('hand',{carpus:'Carpal relationships',joints:'MCP / IP joints',radius:'Distal radius / ulna',tendons:'Flexor-tendon paths'},(s,h)=>{
    h.box('radius',[.25,-.98,0],[.4,.45,.26],.45);h.box('radius',[-.34,-.99,-.04],[.24,.4,.24],.4);
    [[.32,-.53,.06],[0,-.53,0],[-.3,-.5,-.03],[.4,-.17,0],[.16,-.14,0],[-.09,-.12,0],[-.33,-.1,0]].forEach(p=>h.ell('carpus',p,[.16,.17,.13],.6));
    [-.43,-.15,.15,.43].forEach((x,i)=>{
      const top=.65+(.15-Math.abs(x))*.6;
      h.line('joints',[[x,.13,0],[x,top,0]],12,.5);
      h.ell('joints',[x,top+.06,0],[.1,.1,.1],.7);
      h.line('joints',[[x,top+.18,0],[x,top+.41,0]],9,.5);
      h.line('tendons',[[x*.55,-.78,.17],[x,top+.36,.16]],3);
    });
    h.line('joints',[[.53,-.13,.02],[.85,.14,.08],[1.01,.4,.12]],12,.5);
  },'A left hand in an anatomical palm-forward orientation: radius/thumb are lateral toward patient-left. Carpal shapes and rows are simplified; this is not a carpal alignment measurement or a complete ossification atlas.');
  family('elbow',{bones:'Distal humerus / ulna',radius:'Radius / capitellum',nerves:'Ulnar nerve route',biceps:'Distal biceps',triceps:'Triceps / olecranon'},(s,h)=>{
    h.box('bones',[0,.77,0],[.46,.7,.42],.45);h.ell('bones',[-.16,.24,0],[.26,.27,.3],.5);h.ell('radius',[.28,.23,.05],[.2,.23,.23],.5);
    h.line('bones',[[-.25,.07,-.34],[-.26,-.2,-.32],[-.2,-.45,-.09],[-.17,-1.08,.11]],20,.4);
    h.ell('radius',[.33,-.16,.06],[.23,.12,.23],.6);h.line('radius',[[.33,-.26,.04],[.42,-1.08,.12]],15,.45);
    h.line('nerves',[[-.51,1,-.06],[-.54,.24,-.28],[-.48,-.23,-.2],[-.4,-.97,-.01]],5);
    h.line('biceps',[[.11,1,.42],[.2,.29,.47],[.33,-.4,.23]],8);
    h.line('triceps',[[0,1,-.43],[-.12,.28,-.45],[-.25,.02,-.36]],9);
  },'Left elbow relationships: lateral radial head/capitellum, posterior triceps/olecranon, medial ulnar-nerve route and anterior distal biceps. This is not an ossification sequence or a ligament stress examination.');
  family('longbone',{cortex:'Cortical envelope',marrow:'Medullary compartment',physis:'Growth-plate region',metaphysis:'Metaphyses',muscle:'Muscle envelope'},(s,h)=>{
    h.ell('cortex',[0,0,0],[.29,1.08,.29],.16);
    h.ell('marrow',[0,0,0],[.18,.96,.18],.45);
    [-1,1].forEach(side=>{
      h.ell('metaphysis',[0,side*.75,0],[.36,.27,.34],.38);
      h.ell('cortex',[0,side*1.11,0],[.38,.2,.36],.4);
      h.ring('physis',[0,side*.97,0],.37,.35,7);
    });
    h.ell('muscle',[.4,.02,.02],[.22,.89,.26],.3);h.ell('muscle',[-.41,.02,-.03],[.21,.94,.25],.3);
  },'An idealised long bone with separate marrow, cortex, metaphyseal and growth-plate regions. The growth plate is an orientation aid, not an age-specific normal appearance. No injury, oedema, tumour or maturity assessment is generated.');
  family('skull',{vault:'Calvarial envelope',sutures:'Sagittal / coronal sutures',lambdoid:'Lambdoid suture',metopic:'Metopic suture',fontanelle:'Anterior fontanelle'},(s,h)=>{
    h.ell('vault',[0,0,0],[.91,.86,1.06],.2);
    h.line('sutures',Array.from({length:35},(_,i)=>{const a=.28+i/34*2.3;return[0,.87*Math.sin(a),1.07*Math.cos(a)];}),5);
    h.line('sutures',Array.from({length:35},(_,i)=>{const a=i/34*Math.PI;return[.9*Math.cos(a),.82*Math.sin(a),.28];}),5);
    [-1,1].forEach(side=>h.line('lambdoid',[[0,.58,-.79],[side*.45,.35,-.82],[side*.75,-.02,-.59]],5));
    h.line('metopic',[[0,.73,.57],[0,.48,.88],[0,.08,1.06]],5);
    h.poly('fontanelle',[[0,.86,.05],[-.17,.82,.29],[0,.74,.54],[.17,.82,.29]],.7);
  },'An infant skull-envelope schematic shows sutural positions and the anterior fontanelle. Sutures are drawn as paths, without fusion, ridging, age-specific widths or a predicted skull-shape diagnosis.');
  family('nuclear',{organs:'Visceral organs',skeleton:'Skeletal landmarks',urinary:'Kidneys / bladder',thyroid:'Thyroid region'},(s,h)=>{
    h.ell('organs',[0,1.04,0],[.24,.29,.22],.35);
    h.ell('organs',[.11,.43,.12],[.2,.24,.16],.6);h.ell('organs',[-.28,.08,.08],[.31,.18,.23],.55);
    [-1,1].forEach(side=>{
      h.ell('urinary',[side*.25,-.13,-.14],[.12,.22,.12],.65);
      h.line('urinary',[[side*.23,-.29,-.1],[side*.1,-.58,.09]],4);
      h.line('skeleton',[[side*.2,-.65,0],[side*.27,-1.31,.01]],8);
      h.line('skeleton',[[side*.43,.51,0],[side*.63,-.31,0]],7);
      [.24,.43,.62].forEach(y=>h.line('skeleton',[[0,y,-.18],[side*.36,y-.06,.06],[side*.18,y-.12,.2]],4,.55));
      h.ell('thyroid',[side*.07,.72,.08],[.065,.12,.065],.7);
    });
    h.line('skeleton',[[0,.69,-.18],[0,-.53,-.16]],7);h.ell('urinary',[0,-.63,.11],[.14,.14,.12],.6);
    h.line('skeleton',[[-.27,-.46,0],[-.25,-.66,0],[.25,-.66,0],[.27,-.46,0]],7);
  },'Whole-body localisation only: colour denotes anatomical groups, never tracer concentration. Biodistribution differs by radiopharmaceutical and patient; no uptake intensity, lesion detection, SUV, absorbed dose or therapy eligibility is modelled.');

  const planeNames = { axial: 'Axial', coronal: 'Coronal', sagittal: 'Sagittal' };
  const orientationNote = 'Original schematic 3D anatomy, not patient data. +X is patient left, +Y superior, +Z anterior; this freely rotated perspective is not the conventional radiological display. Colours identify structures, not disease.';
  const registry = {};
  const has = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  function scenario(nodeId, item) {
    const def = has(families, item.family) ? families[item.family] : null;
    if (!def || !Array.isArray(item.focus) || !has(def.landmarks, item.focus[0])) throw new Error('Missing radiology model landmarks: ' + nodeId);
    const focus = item.focus[0];
    return {
      camera: { yaw: -24, pitch: 14, zoom: .96 },
      initial: { focus, plane: 'axial', position: 0, labels: 'focus', context: 'anatomy' },
      controls: [
        { key: 'focus', label: 'Reporting landmark', options: Object.entries(def.landmarks).map(([value,label])=>({value,label})) },
        { key: 'plane', label: 'Section plane', options: Object.entries(planeNames).map(([value,label])=>({value,label})) },
        { key: 'position', label: 'Section offset (schematic)', min: -1.1, max: 1.1, step: .1, unit: '' },
        { key: 'context', label: 'Surrounding anatomy', options: [{value:'anatomy',label:'Show anatomy'},{value:'outline',label:'Fade context'}] },
        { key: 'labels', label: 'Labels', options: [{value:'focus',label:'Selected landmark'},{value:'all',label:'All landmarks'},{value:'hide',label:'Hide labels'}] },
      ],
      build(s,g) {
        const h = painter(g,s,def); def.build(s,h);
        const axis = { sagittal:0, axial:1, coronal:2 }[s.plane];
        const point = (a,b) => {const p=[0,0,0];p[axis]=s.position;p[(axis+1)%3]=a;p[(axis+2)%3]=b;return p;};
        g.polygon([point(-1.15,-1.15),point(1.15,-1.15),point(1.15,1.15),point(-1.15,1.15)],g.colors.gold,{opacity:.10,stroke:g.colors.gold,width:1});
        // Moving a plane is an orientation exercise, not a simulated diagnostic slice.
        h.labels();
        const axisDirection={axial:'inferior ↔ superior',coronal:'posterior ↔ anterior',sagittal:'patient right ↔ patient left'}[s.plane];
        return {
          readout: def.landmarks[s.focus]+'. '+item.reporting_aim+' '+planeNames[s.plane]+' guide at '+s.position.toFixed(1)+' schematic units ('+axisDirection+'). The plane marks location; it does not create a CT/MR image.',
          legend: [{label:'Selected: '+def.landmarks[s.focus],color:g.colors.coral},{label:'Section guide',color:g.colors.gold},{label:s.context==='outline'?'Faded anatomical context':'Anatomical context',color:g.colors.teal}],
          note: orientationNote+' '+def.note,
        };
      },
    };
  }
  Object.entries(MODULES).forEach(([nodeId, item]) => { registry[item.scenario] = scenario(nodeId, item); });
  window.PrimerSpatial.register(registry);
  // An investigation whose backing module shows the wrong anatomy carries its own
  // corrected family (for example a paediatric elbow reference backed by a hip
  // module). Those scenes are registered from the served specification on demand.
  const INVESTIGATION = /^radiology-investigation:ra\.[a-z0-9-]+$/;
  function ensure(spec) {
    if (!spec || typeof spec.scenario !== 'string') return null;
    if (has(registry, spec.scenario)) return spec.scenario;
    if (!INVESTIGATION.test(spec.scenario) || typeof spec.reporting_aim !== 'string') return null;
    if (!has(families, spec.family) || !Array.isArray(spec.focus) || !has(families[spec.family].landmarks, spec.focus[0])) return null;
    registry[spec.scenario] = scenario(spec.scenario, { family: spec.family, focus: spec.focus, reporting_aim: spec.reporting_aim });
    window.PrimerSpatial.register({ [spec.scenario]: registry[spec.scenario] });
    return spec.scenario;
  }
  window.PrimerRadiologyReferenceModels = Object.freeze({
    get supported() { return Object.keys(MODULES); },
    get families() { return Object.keys(families); },
    specification(nodeId) { return Object.prototype.hasOwnProperty.call(MODULES,nodeId) ? JSON.parse(JSON.stringify(MODULES[nodeId])) : null; },
    landmarks(family) { return has(families, family) ? { ...families[family].landmarks } : null; },
    ensure,
    render(spec, hooks = {}) {
      if (!ensure(spec)) return null;
      return window.PrimerSpatial.render({ id:spec.id, title:spec.title, instructions:spec.instructions,
        kind:'model', renderer:'spatial-3d', props:{scenario:spec.scenario} }, hooks);
    },
  });
}());
