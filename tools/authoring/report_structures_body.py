"""Abdomen, pelvis, urinary tract and breast: the headings report_structures_20261117.py writes."""

CONTENT = r'''
# ---------------------------------------------------------------- CT abdomen and pelvis: one list for every study of the region

## @SOLID_ORGANS
Liver | Normal liver size and contour. No focal liver lesion. | [Steatosis / Cirrhotic morphology / Hepatomegaly] [ ]. | Focal liver lesion [ ] mm in segment [ ] [ ].
Gallbladder and bile ducts | Normal gallbladder. No biliary dilatation. | [Gallstones / Cholecystitis / Gallbladder wall thickening] [ ]. | [Intrahepatic / Extrahepatic] biliary dilatation; common bile duct [ ] mm.
Pancreas | Normal. | [Pancreatitis / Pancreatic mass / Pancreatic duct dilatation / Atrophy] [ ].
Spleen | Normal. | [Splenomegaly / Splenic infarct / Focal splenic lesion] [ ].
Adrenal glands | Normal. | [Right / Left] adrenal nodule [ ] mm, [ ] HU.
Kidneys and ureters | Normal kidneys. No calculus or hydronephrosis. | Calculus [ ] mm, [right / left] [kidney / proximal ureter / mid ureter / distal ureter / VUJ], [with / without] hydronephrosis. | [Pyelonephritis / Renal cyst / Renal mass] [ ].
Bladder | Normal. | [Bladder wall thickening / Bladder mass / Bladder calculus] [ ].
Reproductive organs | Normal. | [Ovarian cyst / Adnexal mass / Uterine fibroid / Enlarged prostate] [ ].

## @BOWEL
Stomach and small bowel | Normal. No bowel obstruction. | Small bowel obstruction with transition point in the [ ]. | [Gastric wall thickening / Enteritis / Small bowel mass] [ ].
Colon and appendix | Normal. | [Appendicitis / Diverticulitis / Colitis / Colonic mass] [ ]. | Large bowel obstruction with transition point in the [ ].

## @ABDOMEN_REST
Peritoneum and mesentery | No free fluid, free gas or collection. | [Free fluid / Pneumoperitoneum / Collection / Mesenteric stranding / Peritoneal nodularity] [ ].
Lymph nodes | No lymphadenopathy. | [Retroperitoneal / Mesenteric / Pelvic / Inguinal] lymphadenopathy, [ ] mm short axis.
Vessels | Normal calibre aorta. Patent mesenteric vessels and portal vein. | Abdominal aortic aneurysm, [ ] mm. | [Mesenteric vessel occlusion / Portal vein thrombosis / Atherosclerosis] [ ].
Abdominal wall | No hernia. | [Inguinal / Femoral / Umbilical / Incisional] hernia containing [ ], [with / without] obstruction.
Lung bases | Clear. | [Basal consolidation / Atelectasis / Pleural effusion / Nodule] [ ].
Bones | No destructive bone lesion. | [Fracture / Lytic lesion / Sclerotic lesion / Degenerative change] [ ].

## @ABDOMEN
@SOLID_ORGANS
@BOWEL
@ABDOMEN_REST

# The abdomen where the study is of something else (an angiogram, a spine): each organ still named.
## @ABDOMEN_BRIEF
Liver, spleen, pancreas and adrenal glands | Normal. | [Liver lesion / Splenomegaly / Pancreatic lesion / Adrenal nodule] [ ].
Kidneys and bladder | Normal. | [Renal cyst / Renal mass / Hydronephrosis / Calculus / Bladder wall thickening] [ ].
Bowel and peritoneum | Normal bowel. No free fluid. | [Bowel wall thickening / Bowel obstruction / Free fluid / Collection] [ ].
Lung bases and bones | Clear lung bases. No destructive bone lesion. | [Basal consolidation / Pleural effusion / Fracture / Bone lesion] [ ].

## ra.acute-abdomen
! Liver, gallbladder and bile ducts
! Pancreas and spleen
! Kidneys, ureters and bladder
! Bowel and appendix
! Peritoneum
! Vessels and lymph nodes
! Pelvic organs
! Abdominal wall
! Lung bases and bones
@ABDOMEN

## ct.abdomen-multiphase
= Liver
= Biliary tree and gallbladder -> Gallbladder and bile ducts | Normal gallbladder. No biliary dilatation.
! Pancreas, spleen and adrenal glands
Pancreas | Normal. | [Hypervascular / Hypovascular / Cystic] pancreatic lesion [ ] mm. | Pancreatic duct [ ] mm.
Spleen | Normal. | [Splenomegaly / Focal splenic lesion] [ ].
Adrenal glands | Normal. | [Right / Left] adrenal nodule [ ] mm; unenhanced [ ] HU; absolute washout [ ] percent.
= Kidneys -> Kidneys and ureters
! Bowel and peritoneum
! Vessels and lymph nodes
! Pelvis
Bladder | Normal. | [Bladder wall thickening / Bladder mass / Bladder calculus] [ ].
Reproductive organs | Normal. | [Ovarian cyst / Adnexal mass / Uterine fibroid / Enlarged prostate] [ ].
@BOWEL
Peritoneum and mesentery | No free fluid, free gas or collection. | [Free fluid / Collection / Mesenteric stranding / Peritoneal nodularity] [ ].
Lymph nodes | No lymphadenopathy. | [Retroperitoneal / Mesenteric / Pelvic / Inguinal] lymphadenopathy, [ ] mm short axis.
Vessels | Patent portal and hepatic veins. Normal calibre aorta. | [Portal vein / Hepatic vein / Mesenteric vein] thrombus [ ]. | [Aortic aneurysm / Arterial stenosis / Variant arterial anatomy] [ ].
Abdominal wall | No hernia. | [Inguinal / Femoral / Umbilical / Incisional] hernia containing [ ].
Lung bases | Clear. | [Basal consolidation / Atelectasis / Pleural effusion / Nodule] [ ].
Bones | No destructive bone lesion. | [Fracture / Lytic lesion / Sclerotic lesion / Degenerative change] [ ].

## ct.appendix
= Appendix
= Periappendiceal region
= Complications
! Alternative findings
! Other organs, lung bases and bones
Caecum and terminal ileum | Normal. | [Caecal wall thickening / Terminal ileitis / Caecal diverticulitis / Caecal mass] [ ].
Mesenteric lymph nodes | No enlarged mesenteric lymph nodes. | Enlarged right iliac fossa mesenteric lymph nodes, up to [ ] mm short axis.
@SOLID_ORGANS
Stomach and small bowel | Normal. No bowel obstruction. | Small bowel obstruction with transition point in the [ ]. | [Gastric wall thickening / Enteritis / Small bowel mass] [ ].
Colon | Normal remaining colon. | [Diverticulitis / Colitis / Colonic mass] [ ].
@ABDOMEN_REST except Lymph nodes

## ra.ct-abdominal-trauma
= Liver
Gallbladder and bile ducts | No gallbladder or bile duct injury. | [Gallbladder wall injury / Pericholecystic haematoma / Biloma] [ ].
= Spleen
Pancreas | No pancreatic injury. | Pancreatic [contusion / laceration] at the [head / neck / body / tail], [with / without] duct involvement.
Adrenal glands | No adrenal haematoma. | [Right / Left] adrenal haematoma.
= Kidneys and urinary tract -> Kidneys and ureters | No renal or ureteric injury.
Bladder | No bladder injury. | [Intraperitoneal / Extraperitoneal] bladder rupture.
! Pancreas, bowel and mesentery
Bowel and mesentery | No bowel or mesenteric injury. | [Bowel wall discontinuity / Bowel wall thickening / Mesenteric haematoma / Extraluminal gas] [ ].
! Haemorrhage and vessels
Peritoneum and retroperitoneum | No haemoperitoneum, retroperitoneal haematoma or free gas. | [Small / Moderate / Large] haemoperitoneum [ ]. | [Retroperitoneal haematoma / Free gas] [ ].
Vessels | No active extravasation. Intact aorta and inferior vena cava. | Active [arterial / venous] extravasation from [ ]. | [Pseudoaneurysm / Aortic injury / IVC injury] [ ].
Diaphragm and abdominal wall | Intact. | [Diaphragmatic rupture / Abdominal wall haematoma / Traumatic hernia / Seat belt sign] [ ].
! Bones and lung bases
Lung bases | No pneumothorax, haemothorax or basal lung contusion. | [Pneumothorax / Haemothorax / Lung contusion] [ ].
Bones | No pelvic, spinal or rib fracture. | [Pelvic / Spinal / Rib] fracture [ ].

## ra.ct-bowel-ischaemia
= Mesenteric arteries
= Mesenteric veins
= Bowel wall
= Mesentery and peritoneum
! Other organs, lung bases and bones
Aorta | Normal calibre aorta without dissection or mural thrombus. | [Aortic dissection / Mural thrombus / Aneurysm / Atherosclerosis] [ ].
@SOLID_ORGANS
@ABDOMEN_REST except Peritoneum and mesentery; Vessels

## ra.ct-bowel-wall
= Bowel wall
= Mesentery and vessels
= Lumen and complications
! Other organs, lung bases and bones
@SOLID_ORGANS
Peritoneum | No free fluid, free gas or collection. | [Free fluid / Pneumoperitoneum / Collection / Peritoneal nodularity] [ ].
@ABDOMEN_REST except Peritoneum and mesentery; Vessels

## ra.ct-bowel-obstruction
Stomach | Normal. | [Gastric distension / Gastric outlet obstruction] [ ].
= Small bowel
= Large bowel
= Closed loop and ischaemia
= Peritoneum
! Other organs, lung bases and bones
@SOLID_ORGANS
@ABDOMEN_REST except Peritoneum and mesentery

## ra.ct-small-bowel-tumours
Stomach and duodenum | Normal. | [Gastric / Duodenal] [wall thickening / mass / polyp] [ ].
= Small bowel
Colon and appendix | Normal. | [Colonic mass / Colitis / Diverticulosis / Appendiceal lesion] [ ].
= Mesentery and lymph nodes
! Liver and peritoneum
! Other organs, lung bases and bones
Liver | No liver metastasis. | Liver lesion [ ] mm in segment [ ], [hypervascular / hypovascular].
@SOLID_ORGANS except Liver
Peritoneum | No ascites or peritoneal disease. | [Ascites / Peritoneal nodularity / Omental disease] [ ].
@ABDOMEN_REST except Peritoneum and mesentery; Lymph nodes

## ct.colonography
= Preparation and distension
! Colon
> Colon
Rectum | No polyp or mass of 6 mm or more in the rectum. | [Polyp / Mass] [ ] mm in the rectum, [sessile / pedunculated / flat].
Sigmoid colon | No polyp or mass of 6 mm or more in the sigmoid colon. | [Polyp / Mass] [ ] mm in the sigmoid colon, [sessile / pedunculated / flat]. | Diverticulosis.
Descending colon | No polyp or mass of 6 mm or more in the descending colon. | [Polyp / Mass] [ ] mm in the descending colon, [sessile / pedunculated / flat].
Transverse colon | No polyp or mass of 6 mm or more in the transverse colon. | [Polyp / Mass] [ ] mm in the transverse colon, [sessile / pedunculated / flat].
Ascending colon | No polyp or mass of 6 mm or more in the ascending colon. | [Polyp / Mass] [ ] mm in the ascending colon, [sessile / pedunculated / flat].
Caecum and ileocaecal valve | No polyp or mass of 6 mm or more in the caecum. | [Polyp / Mass] [ ] mm in the caecum, [sessile / pedunculated / flat]. | Lipomatous ileocaecal valve.
>
= Extracolonic findings
= C-RADS

## ra.ct-pancreatitis
= Pancreas
= Collections
= Vessels
= Ducts and gallbladder
! Other organs, lung bases and bones
@SOLID_ORGANS except Gallbladder and bile ducts; Pancreas
@BOWEL
@ABDOMEN_REST except Vessels

## ra.ct-pancreatic-cancer
= Primary tumour
Pancreatic and bile ducts | No pancreatic or biliary duct dilatation. | Pancreatic duct [ ] mm with upstream atrophy. | Common bile duct [ ] mm; [stent in place / no stent].
= Arterial contact
= Venous contact
Lymph nodes | No regional lymphadenopathy. | [Peripancreatic / Coeliac / Para-aortic / Portocaval] lymph node, [ ] mm short axis.
= Metastases
= Resectability
@SOLID_ORGANS except Pancreas; Gallbladder and bile ducts
@BOWEL
@ABDOMEN_REST except Lymph nodes; Vessels

## ra.ct-peritoneum
= Peritoneum
= Omentum and mesentery
= Bowel
! Other organs, lung bases and bones
@SOLID_ORGANS
@ABDOMEN_REST except Peritoneum and mesentery

## ra.abdominal-wall-hernias
= Hernia
= Complications
= Abdominal wall
! Other organs, lung bases and bones
@SOLID_ORGANS
@BOWEL
@ABDOMEN_REST except Abdominal wall

## ct.pelvis
! Bladder and pelvic organs
Bladder | Normal. | [Bladder wall thickening / Bladder mass / Bladder calculus] [ ].
Reproductive organs | Normal. | [Ovarian cyst / Adnexal mass / Uterine fibroid / Enlarged prostate] [ ].
= Bowel -> Rectum and pelvic bowel
! Lymph nodes and fluid
Peritoneum | No free fluid or collection. | [Free fluid / Collection / Peritoneal nodularity] [ ].
Lymph nodes | No pelvic or inguinal lymphadenopathy. | [Iliac / Obturator / Inguinal / Mesorectal] lymphadenopathy, [ ] mm short axis.
Vessels | Patent iliac vessels. | [Iliac artery aneurysm / Iliac vein thrombosis / Atherosclerosis] [ ].
Pelvic wall and groins | No hernia or soft tissue mass. | [Inguinal / Femoral / Obturator] hernia containing [ ].
= Bones

# ---------------------------------------------------------------- CT urinary tract and adrenals

## ct.kub
! Kidneys
! Ureters
Right kidney and ureter | No right renal or ureteric calculus. No hydronephrosis. | Calculus [ ] mm, [ ] HU, in the right [kidney / proximal ureter / mid ureter / distal ureter / VUJ]. | Right [hydronephrosis / hydroureter / perinephric stranding].
Left kidney and ureter | No left renal or ureteric calculus. No hydronephrosis. | Calculus [ ] mm, [ ] HU, in the left [kidney / proximal ureter / mid ureter / distal ureter / VUJ]. | Left [hydronephrosis / hydroureter / perinephric stranding].
= Bladder
! Other organs, lung bases and bones
@SOLID_ORGANS except Kidneys and ureters; Bladder
@BOWEL
@ABDOMEN_REST

## ct.urography
= Kidneys
= Collecting systems and ureters
= Bladder
! Other organs, lung bases and bones
@SOLID_ORGANS except Kidneys and ureters; Bladder
@BOWEL
@ABDOMEN_REST

## ra.renal-cysts-bosniak
= Renal cysts
= Bosniak category
= Kidneys
! Other organs, lung bases and bones
@SOLID_ORGANS except Kidneys and ureters
@BOWEL
@ABDOMEN_REST

## ra.solid-renal-masses
= Renal mass
= Local extent
Renal vein and inferior vena cava | Patent. | Tumour thrombus in the [renal vein / infrahepatic IVC / intrahepatic IVC / right atrium].
= Kidneys
= Lymph nodes and metastases
@SOLID_ORGANS except Kidneys and ureters
@BOWEL
@ABDOMEN_REST except Lymph nodes

## ra.adrenal-lesions
= Right adrenal
= Left adrenal
! Other organs, lung bases and bones
@SOLID_ORGANS except Adrenal glands
@BOWEL
@ABDOMEN_REST

# ---------------------------------------------------------------- MRI abdomen

## @MRI_UPPER_ABDOMEN
Gallbladder and bile ducts | Normal gallbladder. No biliary dilatation. | [Gallstones / Gallbladder wall thickening / Biliary dilatation / Choledocholithiasis] [ ].
Pancreas | Normal. | [Pancreatic mass / Pancreatic cyst / Duct dilatation / Atrophy] [ ].
Spleen | Normal. | [Splenomegaly / Focal splenic lesion / Splenic siderosis] [ ].
Adrenal glands | Normal. | [Right / Left] adrenal nodule [ ] mm, signal drop on opposed phase [present / absent].
Kidneys | Normal. | [Renal cyst / Renal mass / Hydronephrosis] [ ].
Lymph nodes | No lymphadenopathy. | [Porta hepatis / Retroperitoneal / Mesenteric] lymphadenopathy, [ ] mm short axis.
Bowel and peritoneum | Normal visualised bowel. No ascites. | [Ascites / Bowel wall thickening / Peritoneal nodularity] [ ].
Lung bases and bones | Clear lung bases. Normal marrow signal. | [Pleural effusion / Basal consolidation / Bone lesion] [ ].

## @CT_UPPER_ABDOMEN
Gallbladder and bile ducts | Normal gallbladder. No biliary dilatation. | [Gallstones / Cholecystitis / Gallbladder wall thickening / Biliary dilatation] [ ].
Pancreas | Normal. | [Pancreatitis / Pancreatic mass / Pancreatic duct dilatation / Atrophy] [ ].
Spleen | Normal. | [Splenomegaly / Splenic infarct / Focal splenic lesion] [ ].
Adrenal glands | Normal. | [Right / Left] adrenal nodule [ ] mm, [ ] HU.
Kidneys | Normal. | [Renal cyst / Renal mass / Hydronephrosis / Calculus] [ ].
Lymph nodes | No lymphadenopathy. | [Porta hepatis / Retroperitoneal / Mesenteric] lymphadenopathy, [ ] mm short axis.
Bowel and peritoneum | Normal visualised bowel. No ascites. | [Ascites / Bowel wall thickening / Peritoneal nodularity] [ ].
Lung bases and bones | Clear lung bases. No destructive bone lesion. | [Pleural effusion / Basal consolidation / Bone lesion] [ ].

## ra.liver-masses
= Background liver
= Focal lesions
! Vessels and bile ducts
Hepatic vessels | Patent hepatic and portal veins and hepatic artery. | [Portal vein / Hepatic vein] [thrombus / tumour thrombus / occlusion] [ ]. | Variant hepatic arterial anatomy [ ].
! Spleen, peritoneum and lymph nodes
@MRI_UPPER_ABDOMEN

## ct.liver-mass
= Background liver
= Focal lesions
! Vessels and bile ducts
Hepatic vessels | Patent hepatic and portal veins and hepatic artery. | [Portal vein / Hepatic vein] [thrombus / tumour thrombus / occlusion] [ ]. | Variant hepatic arterial anatomy [ ].
! Spleen, peritoneum and lymph nodes
@CT_UPPER_ABDOMEN

## ra.liver-lirads
= Background liver
= Observations
= Vessels -> Hepatic vessels
= Portal hypertension
! Other upper abdominal organs
@MRI_UPPER_ABDOMEN except Spleen; Bowel and peritoneum
Bowel | Normal. | [Bowel wall thickening / Portal colopathy] [ ].

## ct.liver-lirads
= Background liver
= Observations
= Vessels -> Hepatic vessels
= Portal hypertension
! Other upper abdominal organs
@CT_UPPER_ABDOMEN except Spleen; Bowel and peritoneum
Bowel | Normal. | [Bowel wall thickening / Portal colopathy] [ ].

## liver.lirads-calculated
= Observation
= LI-RADS category
= Vessels -> Hepatic vessels
! Other upper abdominal organs
@MRI_UPPER_ABDOMEN

## ct.liver-lirads-calculated
= Observation
= LI-RADS category
= Vessels -> Hepatic vessels
! Other upper abdominal organs
@CT_UPPER_ABDOMEN

## ra.biliary-duct-pathology
= Intrahepatic ducts
= Extrahepatic ducts
= Gallbladder -> Gallbladder and cystic duct
= Pancreatic duct
Pancreas | Normal. | [Pancreatic mass / Pancreatic cyst / Pancreatitis / Pancreas divisum] [ ].
! Liver and vessels
Liver | Normal. No focal liver lesion. | [Steatosis / Cirrhotic morphology / Focal liver lesion] [ ].
Hepatic vessels | Patent portal vein and hepatic artery. | [Portal vein thrombosis / Variant arterial anatomy] [ ].
@MRI_UPPER_ABDOMEN except Gallbladder and bile ducts; Pancreas

## ra.pancreatic-cysts
= Cysts
= Worrisome features
= Pancreatic duct
= Pancreas
Liver | Normal. No focal liver lesion. | [Steatosis / Cirrhotic morphology / Focal liver lesion] [ ].
Peripancreatic vessels | Patent splenic, superior mesenteric and portal veins. | [Splenic vein / Portal vein / Superior mesenteric vein] [thrombosis / narrowing] [ ].
@MRI_UPPER_ABDOMEN except Pancreas

## mri.adrenals
= Right adrenal
= Left adrenal
! Other upper abdominal organs
Liver | Normal. No focal liver lesion. | [Steatosis / Cirrhotic morphology / Focal liver lesion] [ ].
@MRI_UPPER_ABDOMEN except Adrenal glands

## mri.renal-cyst
= Renal cysts
= Bosniak category
= Kidneys
! Other upper abdominal organs
Liver | Normal. No focal liver lesion. | [Steatosis / Cirrhotic morphology / Focal liver lesion] [ ].
@MRI_UPPER_ABDOMEN except Kidneys

## mri.renal-mass
= Renal mass
= Local extent
Renal vein and inferior vena cava | Patent. | Tumour thrombus in the [renal vein / infrahepatic IVC / intrahepatic IVC / right atrium].
= Kidneys
= Lymph nodes and metastases
Liver | Normal. No focal liver lesion. | [Steatosis / Cirrhotic morphology / Focal liver lesion] [ ].
@MRI_UPPER_ABDOMEN except Kidneys; Lymph nodes

## mri.kidneys
! Kidneys
Right kidney | Normal right renal size and signal. No renal mass or hydronephrosis. | [Cystic / Solid] right renal lesion [ ] mm, [enhancing / non-enhancing], Bosniak [ ].
Left kidney | Normal left renal size and signal. No renal mass or hydronephrosis. | [Cystic / Solid] left renal lesion [ ] mm, [enhancing / non-enhancing], Bosniak [ ].
Collecting systems and ureters | No dilatation or filling defect. | [Hydronephrosis / Hydroureter / Urothelial thickening / Filling defect] on the [right / left].
= Renal veins -> Renal arteries and veins
= Adrenal glands
Liver | Normal. No focal liver lesion. | [Steatosis / Cirrhotic morphology / Focal liver lesion] [ ].
@MRI_UPPER_ABDOMEN except Adrenal glands; Kidneys

## ra.mri-crohn
Stomach and duodenum | Normal. | [Gastric / Duodenal] wall thickening [ ].
Jejunum and proximal ileum | No jejunal or proximal ileal wall thickening. | [Wall thickening / Mural hyperenhancement / Restricted diffusion] of the [jejunum / proximal ileum], length [ ] cm.
= Small bowel -> Terminal ileum | No terminal ileal wall thickening or abnormal enhancement.
= Strictures
= Penetrating disease
= Colon
= Mesentery
= Perianal region
Liver and bile ducts | Normal liver. No biliary dilatation or beading. | [Steatosis / Biliary beading / Gallstones] [ ].
Kidneys and bladder | Normal. | [Renal calculus / Hydronephrosis / Bladder wall thickening] [ ].
Sacroiliac joints and bones | Normal sacroiliac joints. Normal marrow signal. | [Sacroiliitis / Avascular necrosis / Bone lesion] [ ].

## ra.mri-perianal-fistula
= Primary tract
= Extensions
= Abscess
= Activity
= Sphincters
Levator plate and supralevator space | No supralevator extension. | [Supralevator / Translevator] extension on the [right / left].
Rectum and pelvic organs | Normal rectum. No proctitis. Normal visualised pelvic organs. | [Proctitis / Rectal wall thickening / Rectovaginal fistula] [ ].

## ra.mri-rectal-cancer
= Tumour
= Mesorectal fascia and EMVI
Peritoneal reflection | No involvement of the peritoneal reflection. | Tumour [at / above / below] the anterior peritoneal reflection, [with / without] peritoneal involvement.
= Anal sphincter
= Nodes and deposits
! Other pelvic organs and bones
Bladder and reproductive organs | Normal. No invasion. | Invasion of the [bladder / prostate / seminal vesicles / uterus / vagina].
Pelvic sidewall and sacrum | No pelvic sidewall or sacral involvement. | Tumour abuts the [pelvic sidewall / sacrum / sciatic notch] on the [right / left].
Bones | No bone lesion. | Bone lesion in the [ ].

## ra.mri-anal-cancer
= Primary tumour
= Sphincters and adjacent organs
= Lymph nodes
! Other pelvic organs and bones
Rectum and mesorectum | Normal. | Tumour extension into the [lower rectum / mesorectum].
Bladder and reproductive organs | Normal. | [Bladder / Prostate / Vaginal / Uterine] abnormality [ ].
Bones | No bone lesion. | Bone lesion in the [ ].

# ---------------------------------------------------------------- ultrasound abdomen and pelvis

## @US_UPPER_ABDOMEN
Liver | Normal liver size and echotexture. No focal liver lesion. | [Increased echogenicity / Coarse echotexture / Nodular surface] [ ]. | [Cyst / Haemangioma / Solid lesion] [ ] mm in segment [ ]. | Liver span [ ] cm.
Portal and hepatic veins | Patent portal vein with hepatopetal flow. Patent hepatic veins. | Portal vein [ ] mm; flow [hepatopetal / hepatofugal / absent].
Gallbladder | Normal gallbladder without gallstones. | [Gallstones / Sludge / Polyp / Wall thickening] [ ]. | Sonographic Murphy sign [positive / negative].
Bile ducts | No biliary dilatation. | Common bile duct [ ] mm. | [Intrahepatic / Extrahepatic] biliary dilatation [ ].
Pancreas | Normal. | [Pancreatitis / Pancreatic duct dilatation / Pancreatic mass] [ ]. | Pancreas obscured by bowel gas.
Spleen | Normal. | Splenomegaly, [ ] cm. | [Focal lesion / Splenule] [ ].
Right kidney | Normal. No right hydronephrosis, calculus or renal mass. | Right kidney [ ] cm. | [Hydronephrosis / Calculus / Simple cyst / Solid mass] in the right kidney [ ].
Left kidney | Normal. No left hydronephrosis, calculus or renal mass. | Left kidney [ ] cm. | [Hydronephrosis / Calculus / Simple cyst / Solid mass] in the left kidney [ ].
Aorta and inferior vena cava | Normal calibre abdominal aorta and inferior vena cava. | Abdominal aorta [ ] cm.

## us.abdomen
! Liver
! Gallbladder and bile ducts
! Pancreas
! Spleen
! Kidneys
! Aorta and IVC
@US_UPPER_ABDOMEN
= Free fluid and lymph nodes

## us.abdomen-pelvis-female
! Liver and biliary tree
! Pancreas and spleen
! Kidneys
! Aorta
@US_UPPER_ABDOMEN
= Bladder
! Uterus and ovaries
Uterus and endometrium | Normal uterus. Normal endometrial thickness. | Uterus [ ] x [ ] x [ ] cm; endometrium [ ] mm. | [Fibroid / Adenomyosis / Endometrial thickening] [ ].
Right ovary | Normal. | Right ovary [ ] mL. | [Simple cyst / Haemorrhagic cyst / Dermoid / Solid mass] [ ] mm in the right ovary.
Left ovary | Normal. | Left ovary [ ] mL. | [Simple cyst / Haemorrhagic cyst / Dermoid / Solid mass] [ ] mm in the left ovary.
= Free fluid

## us.abdomen-pelvis-male
! Liver and biliary tree
! Pancreas and spleen
! Kidneys
! Aorta
@US_UPPER_ABDOMEN
! Bladder and prostate
Bladder | Normal. | [Wall thickening / Calculus / Mass] [ ]. | Post-void residual [ ] mL.
Prostate | Normal prostate size. | Prostate volume [ ] mL.
= Free fluid

## ra.ultrasound-acute-abdomen
= Symptomatic region
! Bowel and appendix
Appendix | Normal. | Non-compressible appendix, [ ] mm in diameter. | Appendix not visualised; no secondary signs of appendicitis.
Bowel | No bowel wall thickening or dilated loops. | [Bowel wall thickening / Dilated loops / Intussusception] in the [ ].
! Hepatobiliary and pancreas
Liver | Normal. | [Increased echogenicity / Focal lesion / Hepatomegaly] [ ].
Gallbladder and bile ducts | Normal gallbladder. No biliary dilatation. | [Gallstones / Wall thickening / Pericholecystic fluid / Biliary dilatation] [ ].
Pancreas and spleen | Normal. | [Pancreatitis / Splenomegaly] [ ]. | Pancreas obscured by bowel gas.
! Kidneys and bladder
Kidneys | No hydronephrosis or calculus. | [Hydronephrosis / Calculus / Perinephric fluid] in the [right / left] kidney.
Bladder | Normal. | [Wall thickening / Calculus / Debris] [ ].
Uterus and ovaries | Normal. | [Ovarian cyst / Adnexal mass / Enlarged ovary with reduced flow] [ ].
= Pelvis and peritoneum -> Peritoneum
= Aorta

## ra.appendicitis
= Appendix
= Periappendiceal region
= Complications
! Alternative findings
Caecum and terminal ileum | Normal. | [Terminal ileitis / Caecal wall thickening / Intussusception] [ ].
Mesenteric lymph nodes | No enlarged mesenteric lymph nodes. | Enlarged right iliac fossa mesenteric lymph nodes, up to [ ] mm short axis.
Right ovary and uterus | Normal. | [Ovarian cyst / Enlarged ovary with reduced flow / Adnexal mass] [ ].
Right kidney and gallbladder | Normal. | [Hydronephrosis / Renal calculus / Gallstones / Cholecystitis] [ ].
Free fluid | None. | [Small / Moderate / Large] [simple / echogenic] free fluid in the [right iliac fossa / pelvis].

## ra.ultrasound-bile-duct-stones
Liver | Normal. | [Increased echogenicity / Focal lesion / Abscess] [ ].
! Bile ducts
Intrahepatic bile ducts | Normal. | Intrahepatic biliary dilatation, [right / left / bilateral].
Common bile duct | Normal calibre common bile duct. | Common bile duct [ ] mm.
= Duct contents
= Gallbladder
! Liver and pancreas
Pancreas | Normal pancreatic head and duct. | [Pancreatic head mass / Pancreatic duct dilatation / Pancreatitis] [ ]. | Pancreas obscured by bowel gas.

## ra.ultrasound-gi-tract
! Bowel wall
! Lumen and motility
Stomach and duodenum | Normal. | [Gastric wall thickening / Pyloric thickening / Distension] [ ].
Small bowel | Normal small bowel wall thickness and peristalsis. | Wall thickening [ ] mm over [ ] cm of the [jejunum / ileum], [preserved / lost] stratification. | Dilated loops up to [ ] mm.
Terminal ileum and ileocaecal valve | Normal. | Terminal ileal wall thickening [ ] mm over [ ] cm.
Appendix | Normal. | Non-compressible appendix, [ ] mm in diameter.
Colon | Normal colonic wall thickness and haustration. | Wall thickening [ ] mm of the [caecum / ascending / transverse / descending / sigmoid] colon. | [Diverticulosis / Diverticulitis] [ ].
! Surroundings
Mesentery and lymph nodes | No inflamed mesenteric fat or lymphadenopathy. | [Creeping fat / Mesenteric lymphadenopathy] [ ].
Peritoneum | No free fluid or collection. | [Free fluid / Collection] [ ].

## ra.ultrasound-ibd
Jejunum and proximal ileum | Normal wall thickness of the jejunum and proximal ileum. | Wall thickening [ ] mm over [ ] cm of the [jejunum / proximal ileum].
= Terminal ileum
! Colon
> Colon
Caecum and ascending colon | Normal wall thickness of the caecum and ascending colon. | Wall thickening [ ] mm of the [caecum / ascending colon].
Transverse colon | Normal wall thickness of the transverse colon. | Wall thickening [ ] mm of the transverse colon.
Descending colon | Normal wall thickness of the descending colon. | Wall thickening [ ] mm of the descending colon.
Sigmoid colon | Normal wall thickness of the sigmoid colon. | Wall thickening [ ] mm of the sigmoid colon.
>
= Activity
= Complications
Mesenteric lymph nodes and free fluid | No lymphadenopathy or free fluid. | [Mesenteric lymphadenopathy / Free fluid] [ ].

## ra.esophagus
Pharynx | Normal pharyngeal contours. No pouch or web. | [Pharyngeal pouch / Cricopharyngeal bar / Web / Aspiration] [ ].
= Oesophageal lumen
= Mucosa
= Motility
Gastro-oesophageal junction | No hiatus hernia or reflux. | [Sliding / Paraoesophageal] hiatus hernia, [ ] cm. | Gastro-oesophageal reflux to the level of the [ ].
= Leak

## us.abdominal-wall
! Hernia
> Hernia sites
Right inguinal and femoral canals | No right inguinal or femoral hernia at rest or on Valsalva. | Right [direct inguinal / indirect inguinal / femoral] hernia, [ ] mm defect, containing [fat / bowel], [reducible / irreducible].
Left inguinal and femoral canals | No left inguinal or femoral hernia at rest or on Valsalva. | Left [direct inguinal / indirect inguinal / femoral] hernia, [ ] mm defect, containing [fat / bowel], [reducible / irreducible].
Umbilicus and linea alba | No umbilical, epigastric or incisional hernia. | [Umbilical / Epigastric / Incisional / Spigelian] hernia, [ ] mm defect, containing [fat / bowel], [reducible / irreducible].
>
= Abdominal wall
= Mass or collection

# ---------------------------------------------------------------- urinary tract and scrotum ultrasound

## us.renal-bladder
= Right kidney
= Left kidney
Ureters | No ureteric dilatation. Ureteric jets present. | [Right / Left] hydroureter to the level of the [ ]. | Absent [right / left] ureteric jet.
= Bladder
= Prostate and pelvis

## us.renal-doppler
! Kidneys
Right kidney | Normal right renal size. No hydronephrosis. | Right kidney [ ] cm. | [Hydronephrosis / Cortical thinning / Increased echogenicity] of the right kidney.
Left kidney | Normal left renal size. No hydronephrosis. | Left kidney [ ] cm. | [Hydronephrosis / Cortical thinning / Increased echogenicity] of the left kidney.
! Renal arteries
Aorta | Normal calibre abdominal aorta. | Aortic peak systolic velocity [ ] cm/s. | [Aneurysm / Atherosclerosis] [ ].
Right renal artery | Patent, with a normal peak systolic velocity. | Right renal artery peak systolic velocity [ ] cm/s; renal-aortic ratio [ ]. | Stenosis of the [origin / proximal / mid / distal] right renal artery.
Left renal artery | Patent, with a normal peak systolic velocity. | Left renal artery peak systolic velocity [ ] cm/s; renal-aortic ratio [ ]. | Stenosis of the [origin / proximal / mid / distal] left renal artery.
= Intrarenal arteries
= Renal veins

## us.scrotum-adult
! Testes
Right testis | Normal right testicular size and echotexture, without focal lesion. | Right testis [ ] x [ ] x [ ] cm. | [Hypoechoic / Heterogeneous / Cystic] lesion [ ] mm in the right testis, [with / without] internal vascularity. | [Microlithiasis / Atrophy / Tubular ectasia] [ ].
Left testis | Normal left testicular size and echotexture, without focal lesion. | Left testis [ ] x [ ] x [ ] cm. | [Hypoechoic / Heterogeneous / Cystic] lesion [ ] mm in the left testis, [with / without] internal vascularity. | [Microlithiasis / Atrophy / Tubular ectasia] [ ].
= Doppler -> Testicular perfusion
! Epididymis
Right epididymis | Normal. | [Epididymal cyst / Epididymitis / Spermatocele] of the right epididymis [ ].
Left epididymis | Normal. | [Epididymal cyst / Epididymitis / Spermatocele] of the left epididymis [ ].
! Extratesticular
Spermatic cords and pampiniform plexus | No varicocele. | [Right / Left / Bilateral] varicocele, veins up to [ ] mm, [with / without] reflux on Valsalva.
Tunica and scrotal wall | No hydrocele or scrotal wall thickening. | [Hydrocele / Haematocele / Pyocele / Scrotal wall thickening] on the [right / left].
Inguinal canals | No inguinoscrotal hernia. | [Right / Left] inguinoscrotal hernia containing [fat / bowel].

## ra.ultrasound-paediatric-scrotum
! Testes
Right testis | Normal size, echotexture and position of the right testis. | [Enlarged / Heterogeneous / Hypoechoic] right testis [ ]. | Right testis [undescended / retractile] at the [ ].
Left testis | Normal size, echotexture and position of the left testis. | [Enlarged / Heterogeneous / Hypoechoic] left testis [ ]. | Left testis [undescended / retractile] at the [ ].
= Doppler -> Testicular perfusion
! Epididymis and cord
Epididymides and appendages | Normal epididymides. No torted appendage. | [Epididymitis / Torted appendix testis / Epididymal enlargement] on the [right / left].
Spermatic cords | Normal. No whirlpool sign. | Whirlpool sign of the [right / left] spermatic cord.
= Scrotal wall -> Scrotal wall and tunica
Inguinal canals | No hernia. | [Right / Left] inguinal hernia containing [fat / bowel].

# ---------------------------------------------------------------- pelvis: gynaecology, bladder, prostate

## ra.ultrasound-acute-gynaecology
= Uterus | Normal. Normal endometrial thickness.
Cervix | Normal. | [Nabothian cysts / Cervical mass / Cervical polyp] [ ].
= Pregnancy
= Right ovary
= Left ovary
= Adnexa and free fluid
Bladder | Normal. | [Wall thickening / Calculus / Debris] [ ].

## ra.ovarian-cysts
Uterus and endometrium | Normal. | Endometrial thickness [ ] mm. | [Fibroid / Adenomyosis / Endometrial polyp] [ ].
= Right ovary
= Left ovary
= Adnexa and peritoneum
= O-RADS

## us.early-pregnancy
= Gestational sac
Yolk sac | Normal. | Yolk sac [absent / enlarged / calcified], [ ] mm.
= Embryo
! Uterus and adnexa
Uterus and cervix | No subchorionic haematoma. Closed cervix. | Subchorionic haematoma [ ] mm. | [Fibroid / Uterine anomaly / Short cervix] [ ].
Right ovary | Normal. | [Corpus luteum / Simple cyst / Adnexal mass] [ ] mm in the right ovary.
Left ovary | Normal. | [Corpus luteum / Simple cyst / Adnexal mass] [ ] mm in the left ovary.
= Free fluid

## mri.female-pelvis
= Uterus
Endometrium | Normal endometrial thickness and signal. | Endometrial thickness [ ] mm. | [Endometrial polyp / Endometrial thickening / Fluid in the cavity] [ ].
! Cervix and vagina
Cervix | Normal. | [Cervical mass / Nabothian cysts / Cervical stenosis] [ ].
Vagina and vulva | Normal. | [Vaginal cyst / Vaginal mass / Bartholin cyst] [ ].
! Ovaries and adnexa
Right ovary | Normal. | [Cystic / Solid] right adnexal lesion [ ] mm, O-RADS MRI [ ].
Left ovary | Normal. | [Cystic / Solid] left adnexal lesion [ ] mm, O-RADS MRI [ ].
Fallopian tubes | No hydrosalpinx. | [Right / Left / Bilateral] [hydrosalpinx / haematosalpinx / pyosalpinx].
= Endometriosis
! Bladder and bowel
Bladder and urethra | Normal. | [Bladder wall thickening / Urethral diverticulum / Bladder mass] [ ].
Rectum and pelvic bowel | Normal. | [Bowel wall thickening / Diverticulosis / Bowel endometriosis] [ ].
Pelvic floor | Normal levator ani and pelvic floor support. | [Levator ani defect / Cystocele / Rectocele / Uterine descent] [ ].
! Lymph nodes and fluid
Lymph nodes | No pelvic lymphadenopathy. | [Iliac / Obturator / Inguinal] lymphadenopathy, [ ] mm short axis.
Peritoneum | No free fluid or peritoneal deposit. | [Free fluid / Peritoneal deposit] [ ].
Bones | Normal marrow signal. | [Bone lesion / Sacroiliitis / Insufficiency fracture] [ ].

## mri.adnexal-mass
Uterus and endometrium | Normal. | [Fibroid / Adenomyosis / Endometrial thickening] [ ].
= Right ovary
= Left ovary
= Adnexa and peritoneum
= O-RADS
Bladder and bowel | Normal bladder and pelvic bowel. | [Bladder / Bowel] involvement [ ].
Lymph nodes | No pelvic or para-aortic lymphadenopathy. | [Iliac / Obturator / Para-aortic] lymphadenopathy, [ ] mm short axis.
Bones | Normal marrow signal. | Bone lesion in the [ ].

## ra.mri-endometriosis
= Ovaries
! Anterior compartment
> Anterior compartment
Bladder | No bladder wall endometriosis. | Bladder wall nodule [ ] mm at the [dome / posterior wall / trigone], [with / without] detrusor involvement.
Vesicouterine pouch and round ligaments | No disease of the vesicouterine pouch or round ligaments. | [Vesicouterine pouch obliteration / Round ligament thickening] on the [right / left].
! Posterior compartment
> Posterior compartment
Uterosacral ligaments and torus uterinus | No uterosacral ligament or torus thickening or nodule. | [Right / Left / Bilateral] uterosacral ligament nodule, [ ] mm. | Torus uterinus nodule [ ] mm.
Posterior fornix and rectovaginal septum | No endometriosis of the posterior fornix or rectovaginal septum. | Nodule [ ] mm of the [posterior fornix / rectovaginal septum].
Rectosigmoid | No bowel wall endometriosis. | Rectosigmoid nodule [ ] mm long, [ ] cm from the anal verge, involving [ ] percent of the circumference. | Depth of invasion: [serosa / muscularis / submucosa].
Pouch of Douglas | Open pouch of Douglas. | [Partial / Complete] obliteration of the pouch of Douglas.
! Lateral compartments
> Lateral compartments
Parametria and pelvic sidewalls | No parametrial or pelvic sidewall endometriosis. | [Right / Left] parametrial nodule [ ] mm.
Ureters | No ureteric involvement or hydronephrosis. | [Right / Left] ureteric [encasement / stenosis] with [hydroureter / hydronephrosis].
Sacral plexus and sciatic nerves | No endometriosis of the sacral plexus or sciatic nerves. | [Right / Left] [sacral plexus / sciatic nerve] endometriosis.
>
= Uterus
Fallopian tubes | No hydrosalpinx or haematosalpinx. | [Right / Left / Bilateral] [hydrosalpinx / haematosalpinx].
= Other sites

## ra.mri-cervical-cancer
= Tumour
= Stroma and parametria
= Vagina and uterine body
= Pelvic sidewall and urinary tract
Bladder and rectum | No bladder or rectal invasion. | Invasion of the [bladder / rectum] [ ].
Ovaries | Normal. | [Ovarian cyst / Ovarian mass] on the [right / left].
= Lymph nodes
Bones and peritoneum | No bone lesion or peritoneal disease. | [Bone lesion / Peritoneal deposit / Ascites] [ ].
= FIGO stage

## ra.mri-endometrial-cancer
= Tumour
= Myometrial invasion
= Cervix
= Serosa, adnexa and vagina
Bladder and rectum | No bladder or rectal invasion. | Invasion of the [bladder / rectum] [ ].
= Lymph nodes and peritoneum
Bones | No bone lesion. | Bone lesion in the [ ].
= FIGO stage

## ra.mullerian-anomalies
= Fundal contour
= Uterine cavity
= Cervix and vagina
! Kidneys and ovaries
Ovaries | Normal. | [Polycystic morphology / Ovarian cyst / Absent ovary] on the [right / left].
Kidneys | Both kidneys present and normally sited. | [Absent / Ectopic / Duplex] [right / left] kidney.
Endometriosis and haematometra | No haematometra, haematocolpos or endometriosis. | [Haematometra / Haematocolpos / Endometrioma] [ ].

## ra.mri-bladder
= Bladder lesion
= Muscle invasion
= VI-RADS
! Pelvis
Ureters and upper tracts | No hydroureter or upper tract lesion on the included images. | [Right / Left] [hydroureter / hydronephrosis / ureteric lesion].
Prostate, seminal vesicles, uterus and vagina | No invasion of the prostate, seminal vesicles, uterus or vagina. | Invasion of the [prostate / seminal vesicles / uterus / vagina / pelvic sidewall].
Lymph nodes | No pelvic lymphadenopathy. | [Obturator / Internal iliac / External iliac / Common iliac] lymph node, [ ] mm short axis.
Bones | No bone lesion. | Bone lesion in the [ ].

## ra.mri-prostate
= Gland
= Peripheral zone
= Transition zone
! Local extent
Extraprostatic extension | None. | Extraprostatic extension at the [right / left] [base / mid gland / apex].
Neurovascular bundles | No neurovascular bundle involvement. | [Right / Left] neurovascular bundle [abutted / involved].
Seminal vesicles | Normal. | [Right / Left / Bilateral] seminal vesicle invasion.
! Lymph nodes and bones
Lymph nodes | No pelvic lymphadenopathy. | [Obturator / Internal iliac / External iliac / Common iliac] lymph node, [ ] mm short axis.
Bones | No bone metastasis. | Bone lesion in the [ ].
Bladder and rectum | Normal. | [Bladder wall thickening / Bladder base invasion / Rectal wall involvement] [ ].
= PI-RADS

# ---------------------------------------------------------------- breast

## ra.mri-breast
= Background
Foci | No suspicious focus. | Focus in the [right / left] breast at [ ] o'clock.
= Masses
= Non-mass enhancement
Skin, nipples and chest wall | Normal. | [Skin thickening / Nipple retraction / Pectoralis involvement / Chest wall invasion] on the [right / left].
! Axillae and chest wall
Axillary and internal mammary nodes | No suspicious lymph nodes. | Suspicious [axillary / internal mammary] lymph node on the [right / left], [ ] mm.
Visualised chest, liver and bones | Normal. | [Pleural effusion / Liver lesion / Bone lesion] [ ].
= BI-RADS
'''
