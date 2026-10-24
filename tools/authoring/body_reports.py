"""Original selectable abdominal/pelvic report wording; run from repository root."""
import copy, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.build_descriptor_reporting import compile_statement
ASSIGN=[{'guide_id': 'rad.3.acute-abdomen',
  'investigation_id': 'ra.acute-abdomen',
  'title': 'Acute abdomen imaging',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.3.acute-abdomen',
  'investigation_id': 'ra.transvaginal-nongynaecology',
  'title': 'Transvaginal ultrasound — non-gynaecological conditions',
  'modality': 'Ultrasound'},
 {'guide_id': 'rad.3.acute-abdomen',
  'investigation_id': 'ra.ultrasound-acute-abdomen',
  'title': 'Ultrasound acute abdomen',
  'modality': 'Ultrasound'},
 {'guide_id': 'rad.4.kidney',
  'investigation_id': 'ra.renal-cysts-bosniak',
  'title': 'CT and MRI renal cysts — Bosniak',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.4.kidney',
  'investigation_id': 'ra.solid-renal-masses',
  'title': 'CT and MRI solid renal masses',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.4.liver',
  'investigation_id': 'ra.liver-masses',
  'title': 'CT and MRI liver masses',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.4.liver',
  'investigation_id': 'ra.liver-lirads',
  'title': 'CT and MRI liver — LI-RADS',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.abdominal-trauma',
  'investigation_id': 'ra.ct-abdominal-trauma',
  'title': 'CT abdominal trauma',
  'modality': 'CT'},
 {'guide_id': 'rad.5.adrenal',
  'investigation_id': 'ra.adrenal-lesions',
  'title': 'CT and MRI adrenal lesions',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.anal-cancer',
  'investigation_id': 'ra.mri-anal-cancer',
  'title': 'MRI anal cancer staging',
  'modality': 'MRI'},
 {'guide_id': 'rad.5.aorta',
  'investigation_id': 'ra.aortic-aneurysm-rupture',
  'title': 'CT aortic aneurysm rupture',
  'modality': 'CT'},
 {'guide_id': 'rad.5.appendicitis',
  'investigation_id': 'ra.appendicitis',
  'title': 'Ultrasound and CT appendix',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.biliary',
  'investigation_id': 'ra.ultrasound-bile-duct-stones',
  'title': 'Ultrasound common bile duct stones',
  'modality': 'Ultrasound'},
 {'guide_id': 'rad.5.biliary',
  'investigation_id': 'ra.ultrasound-gallbladder',
  'title': 'Ultrasound gallbladder',
  'modality': 'Ultrasound'},
 {'guide_id': 'rad.5.biliary',
  'investigation_id': 'ra.biliary-duct-pathology',
  'title': 'Biliary duct imaging',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.bladder-virads',
  'investigation_id': 'ra.mri-bladder',
  'title': 'MRI bladder — VI-RADS',
  'modality': 'MRI'},
 {'guide_id': 'rad.5.bowel-ischaemia',
  'investigation_id': 'ra.ct-bowel-ischaemia',
  'title': 'CT bowel ischaemia',
  'modality': 'CT'},
 {'guide_id': 'rad.5.bowel-ischaemia',
  'investigation_id': 'ra.ct-bowel-wall',
  'title': 'CT bowel wall thickening',
  'modality': 'CT'},
 {'guide_id': 'rad.5.bowel-obstruction',
  'investigation_id': 'ra.ct-bowel-obstruction',
  'title': 'CT small bowel obstruction',
  'modality': 'CT'},
 {'guide_id': 'rad.5.gi-tumours-foreign-bodies',
  'investigation_id': 'ra.ct-small-bowel-tumours',
  'title': 'CT small bowel tumours',
  'modality': 'CT'},
 {'guide_id': 'rad.5.gi-tumours-foreign-bodies',
  'investigation_id': 'ra.gi-foreign-bodies',
  'title': 'GI tract foreign bodies',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.gi-ultrasound',
  'investigation_id': 'ra.ultrasound-gi-tract',
  'title': 'Ultrasound GI tract',
  'modality': 'Ultrasound'},
 {'guide_id': 'rad.5.ibd', 'investigation_id': 'ra.mri-crohn', 'title': "MRI Crohn's disease", 'modality': 'MRI'},
 {'guide_id': 'rad.5.ibd',
  'investigation_id': 'ra.ultrasound-ibd',
  'title': 'Ultrasound inflammatory bowel disease',
  'modality': 'Ultrasound'},
 {'guide_id': 'rad.5.ovarian-orads',
  'investigation_id': 'ra.ovarian-cysts',
  'title': 'Ultrasound and MRI ovarian cysts',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.pancreas-acute',
  'investigation_id': 'ra.ct-pancreatitis',
  'title': 'CT acute pancreatitis',
  'modality': 'CT'},
 {'guide_id': 'rad.5.pancreas-tumour',
  'investigation_id': 'ra.ct-pancreatic-cancer',
  'title': 'CT pancreatic cancer staging',
  'modality': 'CT'},
 {'guide_id': 'rad.5.pancreas-tumour',
  'investigation_id': 'ra.pancreatic-cysts',
  'title': 'CT and MRI pancreatic cysts',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.pelvic-floor',
  'investigation_id': 'ra.dynamic-rectal-examination',
  'title': 'Fluoroscopic defecography',
  'modality': 'Radiography'},
 {'guide_id': 'rad.5.peritoneum',
  'investigation_id': 'ra.abdominal-wall-hernias',
  'title': 'CT abdominal wall hernias',
  'modality': 'CT'},
 {'guide_id': 'rad.5.peritoneum',
  'investigation_id': 'ra.ct-peritoneum',
  'title': 'CT peritoneum and mesentery',
  'modality': 'CT'},
 {'guide_id': 'rad.5.peritoneum',
  'investigation_id': 'ra.ct-peritoneal-carcinomatosis',
  'title': 'CT peritoneal carcinomatosis',
  'modality': 'CT'},
 {'guide_id': 'rad.5.pleura',
  'investigation_id': 'ra.thoracic-ultrasound',
  'title': 'Thoracic ultrasound in acute abdomen',
  'modality': 'Ultrasound'},
 {'guide_id': 'rad.5.prostate-mri',
  'investigation_id': 'ra.mri-prostate',
  'title': 'MRI prostate — PI-RADS v2.1',
  'modality': 'MRI'},
 {'guide_id': 'rad.5.rectal-mr',
  'investigation_id': 'ra.mri-rectal-cancer',
  'title': 'MRI rectal cancer staging and restaging',
  'modality': 'MRI'},
 {'guide_id': 'rad.5.rectal-mr',
  'investigation_id': 'ra.mri-perianal-fistula',
  'title': 'MRI perianal fistulas',
  'modality': 'MRI'},
 {'guide_id': 'rad.5.uterine-mr',
  'investigation_id': 'ra.ultrasound-acute-gynaecology',
  'title': 'Ultrasound acute gynaecology',
  'modality': 'Ultrasound'},
 {'guide_id': 'rad.5.uterine-mr',
  'investigation_id': 'ra.mri-endometriosis',
  'title': 'MRI endometriosis',
  'modality': 'MRI'},
 {'guide_id': 'rad.5.uterine-mr',
  'investigation_id': 'ra.mri-cervical-cancer',
  'title': 'MRI cervical cancer staging',
  'modality': 'MRI'},
 {'guide_id': 'rad.5.uterine-mr',
  'investigation_id': 'ra.mri-endometrial-cancer',
  'title': 'MRI endometrial cancer staging',
  'modality': 'MRI'},
 {'guide_id': 'rad.5.uterine-mr',
  'investigation_id': 'ra.mullerian-anomalies',
  'title': 'Müllerian duct anomaly imaging',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.paeds-abdomen',
  'investigation_id': 'ra.neonatal-acute-abdomen',
  'title': 'Neonatal acute abdomen imaging',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.paeds-abdomen',
  'investigation_id': 'ra.necrotising-enterocolitis',
  'title': 'Necrotising enterocolitis imaging',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.paeds-masses-neuro',
  'investigation_id': 'ra.paediatric-cystic-abdominal-masses',
  'title': 'Paediatric cystic abdominal mass imaging',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.paeds-masses-neuro',
  'investigation_id': 'ra.paediatric-solid-abdominal-masses',
  'title': 'Paediatric solid abdominal mass imaging',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.paeds-masses-neuro',
  'investigation_id': 'ra.paediatric-renal-tumours',
  'title': 'Paediatric renal tumour imaging',
  'modality': 'Multimodality'},
 {'guide_id': 'rad.5.scrotum',
  'investigation_id': 'ra.ultrasound-paediatric-scrotum',
  'title': 'Ultrasound acute scrotum in children',
  'modality': 'Ultrasound'}]
OUT={'version':'2026-10-23','sources':[],'investigations':{},'coverage':[]}
SOURCE={}
def slug(s): return re.sub('[^a-z0-9]+','-',s.lower()).strip('-')
def source(s):
 k=slug(s['title'])
 if k not in SOURCE: SOURCE[k]={'id':k,'title':s['title'],'url':s['url']}
 return k
# Each report retains its regional references; findings are newly authored.
SOURCE={'practical-approach-to-acute-abdomen': {'id': 'practical-approach-to-acute-abdomen',
                                         'title': 'Practical approach to Acute Abdomen',
                                         'url': 'https://radiologyassistant.nl/abdomen/acute-abdomen/practical-approach-to-acute-abdomen'},
 'transvaginal-ultrasound-for-non-gynaecological-conditions': {'id': 'transvaginal-ultrasound-for-non-gynaecological-conditions',
                                                               'title': 'Transvaginal Ultrasound for '
                                                                        'Non-Gynaecological Conditions',
                                                               'url': 'https://radiologyassistant.nl/abdomen/ultrasound/transvaginal-ultrasound-for-non-gynaecological-conditions'},
 'ultrasound-in-acute-abdomen': {'id': 'ultrasound-in-acute-abdomen',
                                 'title': 'Ultrasound in Acute Abdomen',
                                 'url': 'https://radiologyassistant.nl/abdomen/ultrasound/role-of-ultrasound-in-acute-abdomen'},
 'bosniak-classification-2019': {'id': 'bosniak-classification-2019',
                                 'title': 'Bosniak Classification 2019',
                                 'url': 'https://radiologyassistant.nl/abdomen/kidney/bozniak-2019'},
 'solid-renal-masses': {'id': 'solid-renal-masses',
                        'title': 'Solid Renal Masses',
                        'url': 'https://radiologyassistant.nl/abdomen/kidney/solid-masses'},
 'characterisation-of-liver-masses': {'id': 'characterisation-of-liver-masses',
                                      'title': 'Characterisation of liver masses',
                                      'url': 'https://radiologyassistant.nl/abdomen/liver/characterisation-of-liver-masses'},
 'common-liver-tumors': {'id': 'common-liver-tumors',
                         'title': 'Common Liver Tumors',
                         'url': 'https://radiologyassistant.nl/abdomen/liver/common-liver-tumors'},
 'incidentalomas-in-the-liver': {'id': 'incidentalomas-in-the-liver',
                                 'title': 'Incidentalomas in the liver',
                                 'url': 'https://radiologyassistant.nl/abdomen/liver/incidentalomas'},
 'liver-segmental-anatomy': {'id': 'liver-segmental-anatomy',
                             'title': 'Liver - Segmental Anatomy',
                             'url': 'https://radiologyassistant.nl/abdomen/liver/segmental-anatomy'},
 'li-rads': {'id': 'li-rads', 'title': 'LI-RADS', 'url': 'https://radiologyassistant.nl/abdomen/liver/li-rads'},
 'acr-li-rads': {'id': 'acr-li-rads',
                 'title': 'ACR LI-RADS',
                 'url': 'https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/LI-RADS'},
 'ct-in-abdominal-trauma': {'id': 'ct-in-abdominal-trauma',
                            'title': 'CT in Abdominal Trauma',
                            'url': 'https://radiologyassistant.nl/abdomen/acute-abdomen/ct-in-trauma'},
 'characterization-of-adrenal-lesions-update': {'id': 'characterization-of-adrenal-lesions-update',
                                                'title': 'Characterization of Adrenal lesions - Update',
                                                'url': 'https://radiologyassistant.nl/abdomen/adrenals/lesion-characterization-1'},
 'ese-ensat-adrenal-incidentaloma-guideline-2023': {'id': 'ese-ensat-adrenal-incidentaloma-guideline-2023',
                                                    'title': 'ESE/ENSAT adrenal incidentaloma guideline (2023)',
                                                    'url': 'https://doi.org/10.1093/ejendo/lvad066'},
 'anal-cancer-staging': {'id': 'anal-cancer-staging',
                         'title': 'Anal cancer staging',
                         'url': 'https://radiologyassistant.nl/abdomen/anal-cancer-2/anal'},
 'acr-appropriateness-criteria-staging-and-follow-up-of-anal-cancer': {'id': 'acr-appropriateness-criteria-staging-and-follow-up-of-anal-cancer',
                                                                       'title': 'ACR Appropriateness Criteria: Staging '
                                                                                'and Follow-up of Anal Cancer',
                                                                       'url': 'https://acsearch.acr.org/docs/3195148/Narrative'},
 'aortic-aneurysm-rupture': {'id': 'aortic-aneurysm-rupture',
                             'title': 'Aortic Aneurysm Rupture',
                             'url': 'https://radiologyassistant.nl/abdomen/aorta/aneurysm-rupture'},
 'appendicitis-and-mimics': {'id': 'appendicitis-and-mimics',
                             'title': 'Appendicitis and Mimics',
                             'url': 'https://radiologyassistant.nl/abdomen/acute-abdomen/appendicitis-and-mimics'},
 'appendicitis-us-findings': {'id': 'appendicitis-us-findings',
                              'title': 'Appendicitis - US findings',
                              'url': 'https://radiologyassistant.nl/abdomen/acute-abdomen/appendicitis-us-findings'},
 'appendicitis-pitfalls-in-us-and-ct-diagnosis': {'id': 'appendicitis-pitfalls-in-us-and-ct-diagnosis',
                                                  'title': 'Appendicitis - Pitfalls in US and CT diagnosis',
                                                  'url': 'https://radiologyassistant.nl/abdomen/acute-abdomen/appendicitis-pitfalls-in-us-and-ct-diagnosis'},
 'common-bile-duct-stones-ultrasound': {'id': 'common-bile-duct-stones-ultrasound',
                                        'title': 'Common Bile Duct Stones - Ultrasound',
                                        'url': 'https://radiologyassistant.nl/abdomen/biliary-system/lk-jg-2'},
 'gallbladder-obstruction': {'id': 'gallbladder-obstruction',
                             'title': 'Gallbladder obstruction',
                             'url': 'https://radiologyassistant.nl/abdomen/biliary-system/lk-jg'},
 'biliary-duct-pathology': {'id': 'biliary-duct-pathology',
                            'title': 'Biliary duct pathology',
                            'url': 'https://radiologyassistant.nl/abdomen/biliary-system/biliary-duct-pathology'},
 'gallbladder-wall-thickening': {'id': 'gallbladder-wall-thickening',
                                 'title': 'Gallbladder wall thickening',
                                 'url': 'https://radiologyassistant.nl/abdomen/biliary-system/gallbladder-wall-thickening'},
 'bladder-cancer-vi-rads': {'id': 'bladder-cancer-vi-rads',
                            'title': 'Bladder Cancer - VI-RADS',
                            'url': 'https://radiologyassistant.nl/abdomen/bladder/bladder-cancer-vi-rads'},
 'vi-rads-development-consensus': {'id': 'vi-rads-development-consensus',
                                   'title': 'VI-RADS development consensus',
                                   'url': 'https://pubmed.ncbi.nlm.nih.gov/29755006/'},
 'bowel-ischemia-video-lectures': {'id': 'bowel-ischemia-video-lectures',
                                   'title': 'Bowel Ischemia - Video Lectures',
                                   'url': 'https://radiologyassistant.nl/abdomen/bowel/bowel-ischemia'},
 'ct-pattern-of-bowel-wall-thickening': {'id': 'ct-pattern-of-bowel-wall-thickening',
                                         'title': 'CT-pattern of Bowel wall thickening',
                                         'url': 'https://radiologyassistant.nl/abdomen/bowel/bowel-wall-thickening-ct-pattern'},
 'closed-loop-in-small-bowel-obstruction': {'id': 'closed-loop-in-small-bowel-obstruction',
                                            'title': 'Closed Loop in Small bowel obstruction',
                                            'url': 'https://radiologyassistant.nl/abdomen/bowel/closed-loop-in-small-bowel-obstruction'},
 'closed-loop-obstruction-with-video': {'id': 'closed-loop-obstruction-with-video',
                                        'title': 'Closed Loop Obstruction with video',
                                        'url': 'https://radiologyassistant.nl/abdomen/bowel/closed-loop-obstruction-with-video'},
 'small-bowel-tumors': {'id': 'small-bowel-tumors',
                        'title': 'Small Bowel Tumors',
                        'url': 'https://radiologyassistant.nl/abdomen/bowel/small-bowel-tumors'},
 'sharp-foreign-bodies-in-gi-tract': {'id': 'sharp-foreign-bodies-in-gi-tract',
                                      'title': 'Sharp foreign bodies in GI tract',
                                      'url': 'https://radiologyassistant.nl/abdomen/bowel/sharp-foreign-bodies-in-gi-tract'},
 'us-of-the-gi-tract-technique': {'id': 'us-of-the-gi-tract-technique',
                                  'title': 'US of the GI tract - Technique',
                                  'url': 'https://radiologyassistant.nl/abdomen/ultrasound/lk-jg-1-1-1'},
 'us-of-the-gi-tract-normal-anatomy': {'id': 'us-of-the-gi-tract-normal-anatomy',
                                       'title': 'US of the GI tract - Normal Anatomy',
                                       'url': 'https://radiologyassistant.nl/abdomen/ultrasound/lk-jg-1-1'},
 'crohn-s-disease-role-of-mri': {'id': 'crohn-s-disease-role-of-mri',
                                 'title': "Crohn's disease - role of MRI",
                                 'url': 'https://radiologyassistant.nl/abdomen/bowel/crohn-s-disease'},
 'crohn-s-disease-role-of-ultrasound': {'id': 'crohn-s-disease-role-of-ultrasound',
                                        'title': "Crohn's disease - role of Ultrasound",
                                        'url': 'https://radiologyassistant.nl/abdomen/bowel/ultrasound-in-crohns-disease'},
 'us-of-mimics-of-inflammatory-bowel-disease': {'id': 'us-of-mimics-of-inflammatory-bowel-disease',
                                                'title': 'US of Mimics of Inflammatory Bowel Disease',
                                                'url': 'https://radiologyassistant.nl/abdomen/bowel/us-of-mimics-of-inflammatory-bowel-disease'},
 'ovarian-cystic-lesions': {'id': 'ovarian-cystic-lesions',
                            'title': 'Ovarian cystic lesions',
                            'url': 'https://radiologyassistant.nl/abdomen/unsorted/common-ovarian-cystic-lesions'},
 'roadmap-to-evaluate-ovarian-cysts': {'id': 'roadmap-to-evaluate-ovarian-cysts',
                                       'title': 'Roadmap to evaluate ovarian cysts',
                                       'url': 'https://radiologyassistant.nl/abdomen/unsorted/roadmap-to-evaluate-ovarian-cysts'},
 'acr-o-rads-us-v2022': {'id': 'acr-o-rads-us-v2022',
                         'title': 'ACR O-RADS US v2022',
                         'url': 'https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/O-RADS/Ultrasound'},
 'acr-o-rads-mri': {'id': 'acr-o-rads-mri',
                    'title': 'ACR O-RADS MRI',
                    'url': 'https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/O-RADS/MRI'},
 'acute-pancreatitis': {'id': 'acute-pancreatitis',
                        'title': 'Acute Pancreatitis',
                        'url': 'https://radiologyassistant.nl/abdomen/pancreas/acute-pancreatitis'},
 'pancreatic-cancer-ct-staging-2-0': {'id': 'pancreatic-cancer-ct-staging-2-0',
                                      'title': 'Pancreatic Cancer - CT staging 2.0',
                                      'url': 'https://radiologyassistant.nl/abdomen/pancreas/pancreas-carcinoma-1'},
 'pancreatic-cystic-lesions': {'id': 'pancreatic-cystic-lesions',
                               'title': 'Pancreatic cystic Lesions',
                               'url': 'https://radiologyassistant.nl/abdomen/pancreas/pancreas-cystic-lesions'},
 'dynamic-rectal-examination': {'id': 'dynamic-rectal-examination',
                                'title': 'Dynamic Rectal examination',
                                'url': 'https://radiologyassistant.nl/abdomen/rectum/dynamic-rectal-examination'},
 'esur-esgar-recommendations-for-mri-of-pelvic-floor-dysfunction': {'id': 'esur-esgar-recommendations-for-mri-of-pelvic-floor-dysfunction',
                                                                    'title': 'ESUR/ESGAR recommendations for MRI of '
                                                                             'pelvic floor dysfunction',
                                                                    'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC5374191/'},
 'esr-essentials-pelvic-floor-imaging-esur-practice-recommendations-2026': {'id': 'esr-essentials-pelvic-floor-imaging-esur-practice-recommendations-2026',
                                                                            'title': 'ESR Essentials: Pelvic floor '
                                                                                     'imaging, ESUR practice '
                                                                                     'recommendations (2026)',
                                                                            'url': 'https://doi.org/10.1007/s00330-026-12706-1'},
 'abdominal-wall-hernias': {'id': 'abdominal-wall-hernias',
                            'title': 'Abdominal wall hernias',
                            'url': 'https://radiologyassistant.nl/abdomen/abdomen-1/abdominal-wall-hernias'},
 'anatomy-of-peritoneum-and-mesentery': {'id': 'anatomy-of-peritoneum-and-mesentery',
                                         'title': 'Anatomy of Peritoneum and Mesentery',
                                         'url': 'https://radiologyassistant.nl/abdomen/peritoneum/anatomy-of-peritoneum-and-mesentery'},
 'peritoneal-carcinomatosis': {'id': 'peritoneal-carcinomatosis',
                               'title': 'Peritoneal Carcinomatosis',
                               'url': 'https://radiologyassistant.nl/abdomen/peritoneum/peritoneal-carcinomatosis'},
 'peritoneal-pathology': {'id': 'peritoneal-pathology',
                          'title': 'Peritoneal Pathology',
                          'url': 'https://radiologyassistant.nl/abdomen/peritoneum/peritoneal-pathology'},
 'thoracic-ultrasound-in-acute-abdomen': {'id': 'thoracic-ultrasound-in-acute-abdomen',
                                          'title': 'Thoracic Ultrasound in Acute Abdomen',
                                          'url': 'https://radiologyassistant.nl/abdomen/chest-radiology-for-abdominal-radiologists/chest-radiology-for-abdominal-radiologists'},
 'british-thoracic-society-pleural-disease-guideline-2023': {'id': 'british-thoracic-society-pleural-disease-guideline-2023',
                                                             'title': 'British Thoracic Society — Pleural disease '
                                                                      'guideline (2023)',
                                                             'url': 'https://pubmed.ncbi.nlm.nih.gov/37433578/'},
 'prostate-cancer-pi-rads-v2-1': {'id': 'prostate-cancer-pi-rads-v2-1',
                                  'title': 'Prostate Cancer - PI-RADS v2.1',
                                  'url': 'https://radiologyassistant.nl/abdomen/prostate/prostate-cancer-pi-rads-v2-1'},
 'prostate-anatomy': {'id': 'prostate-anatomy',
                      'title': 'Prostate Anatomy',
                      'url': 'https://radiologyassistant.nl/abdomen/prostate/prostate-cancer-pi-rads-v2-1-1'},
 'acr-pi-rads-v2-1': {'id': 'acr-pi-rads-v2-1',
                      'title': 'ACR PI-RADS v2.1',
                      'url': 'https://edge.sitecorecloud.io/americancoldf5f-acrorgf92a-productioncb02-3650/media/ACR/Files/RADS/PI-RADS/PIRADS-2019.pdf'},
 'acr-pi-rads-resources-and-current-reference-documents': {'id': 'acr-pi-rads-resources-and-current-reference-documents',
                                                           'title': 'ACR — PI-RADS resources and current reference '
                                                                    'documents',
                                                           'url': 'https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/PI-RADS'},
 'acr-pi-rads-v2-1-report-template': {'id': 'acr-pi-rads-v2-1-report-template',
                                      'title': 'ACR — PI-RADS v2.1 report template',
                                      'url': 'https://edge.sitecorecloud.io/americancoldf5f-acrorgf92a-productioncb02-3650/media/ACR/Files/RADS/PI-RADS/PIRADS-Report-Template.pdf'},
 'rectal-cancer-mr-staging-and-restaging-update-2026': {'id': 'rectal-cancer-mr-staging-and-restaging-update-2026',
                                                        'title': 'Rectal Cancer  MR staging and restaging- update 2026',
                                                        'url': 'https://radiologyassistant.nl/abdomen/rectum/rectal-cancer-mr-staging-1-1'},
 'perianal-fistulas': {'id': 'perianal-fistulas',
                       'title': 'Perianal Fistulas',
                       'url': 'https://radiologyassistant.nl/abdomen/rectum/perianal-fistulas'},
 'acute-abdomen-in-gynaecology-ultrasound': {'id': 'acute-abdomen-in-gynaecology-ultrasound',
                                             'title': 'Acute Abdomen in Gynaecology - Ultrasound',
                                             'url': 'https://radiologyassistant.nl/abdomen/unsorted/us-of-acute-gynaecology'},
 'endometriosis-mri-detection': {'id': 'endometriosis-mri-detection',
                                 'title': 'Endometriosis - MRI detection',
                                 'url': 'https://radiologyassistant.nl/abdomen/unsorted/endometriosis-mri-detection'},
 'cervical-cancer-mr-staging': {'id': 'cervical-cancer-mr-staging',
                                'title': 'Cervical Cancer - MR staging',
                                'url': 'https://radiologyassistant.nl/abdomen/unsorted/mr-in-cervical-cancer-1'},
 'endometrial-cancer-mr-staging': {'id': 'endometrial-cancer-mr-staging',
                                   'title': 'Endometrial Cancer - MR staging',
                                   'url': 'https://radiologyassistant.nl/abdomen/unsorted/mr-in-endometrial-cancer'},
 'm-llerian-duct-anomalies': {'id': 'm-llerian-duct-anomalies',
                              'title': 'Müllerian duct anomalies',
                              'url': 'https://radiologyassistant.nl/abdomen/unsorted/mullerian-duct-anomalies'},
 'acute-abdomen-in-neonates': {'id': 'acute-abdomen-in-neonates',
                               'title': 'Acute Abdomen in Neonates',
                               'url': 'https://radiologyassistant.nl/pediatrics/abdominal-masses/acute-abdomen-in-neonates'},
 'necrotizing-enterocolitis': {'id': 'necrotizing-enterocolitis',
                               'title': 'Necrotizing Enterocolitis',
                               'url': 'https://radiologyassistant.nl/pediatrics/abdominal-masses/necrotizing-enterocolitis'},
 'cystic-abdominal-masses-in-children': {'id': 'cystic-abdominal-masses-in-children',
                                         'title': 'Cystic Abdominal Masses in Children',
                                         'url': 'https://radiologyassistant.nl/pediatrics/abdominal-masses/cystic-abdominal-masses-in-children'},
 'solid-abdominal-masses-in-children': {'id': 'solid-abdominal-masses-in-children',
                                        'title': 'Solid Abdominal Masses in Children',
                                        'url': 'https://radiologyassistant.nl/pediatrics/abdominal-masses/malignant-abdominal-tumors-in-children'},
 'renal-tumors-in-children': {'id': 'renal-tumors-in-children',
                              'title': 'Renal Tumors in Children',
                              'url': 'https://radiologyassistant.nl/pediatrics/abdominal-masses/renal-tumors-in-children'},
 'acute-scrotum-in-children': {'id': 'acute-scrotum-in-children',
                               'title': 'Acute Scrotum in Children',
                               'url': 'https://radiologyassistant.nl/pediatrics/abdominal-masses/acute-scrotum-in-children'},
 'bosniak-classification-of-cystic-renal-masses-version-2019-proposal-and-needs-assessment': {'id': 'bosniak-classification-of-cystic-renal-masses-version-2019-proposal-and-needs-assessment',
                                                                                              'title': 'Bosniak '
                                                                                                       'Classification '
                                                                                                       'of Cystic '
                                                                                                       'Renal Masses, '
                                                                                                       'Version 2019: '
                                                                                                       'proposal and '
                                                                                                       'needs '
                                                                                                       'assessment',
                                                                                              'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC6677285/'},
 'esgar-updated-rectal-mri-consensus-2026-part-i-primary-staging': {'id': 'esgar-updated-rectal-mri-consensus-2026-part-i-primary-staging',
                                                                    'title': 'ESGAR updated rectal MRI consensus 2026, '
                                                                             'Part I: primary staging',
                                                                    'url': 'https://doi.org/10.1007/s00330-025-12274-w'},
 'aium-practice-parameter-for-scrotal-ultrasound-2025': {'id': 'aium-practice-parameter-for-scrotal-ultrasound-2025',
                                                         'title': 'AIUM Practice Parameter for Scrotal Ultrasound 2025',
                                                         'url': 'https://www.aium.org/docs/default-source/official-statements-or-practice-parameters/scrotal_2025.pdf'},
 'acr-o-rads-resources-and-assessment-categories': {'id': 'acr-o-rads-resources-and-assessment-categories',
                                                    'title': 'ACR O-RADS resources and assessment categories',
                                                    'url': 'https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/O-RADS'}}
REFS={'ra.acute-abdomen': ['practical-approach-to-acute-abdomen',
                      'transvaginal-ultrasound-for-non-gynaecological-conditions',
                      'ultrasound-in-acute-abdomen'],
 'ra.transvaginal-nongynaecology': ['practical-approach-to-acute-abdomen',
                                    'transvaginal-ultrasound-for-non-gynaecological-conditions',
                                    'ultrasound-in-acute-abdomen'],
 'ra.ultrasound-acute-abdomen': ['practical-approach-to-acute-abdomen',
                                 'transvaginal-ultrasound-for-non-gynaecological-conditions',
                                 'ultrasound-in-acute-abdomen'],
 'ra.renal-cysts-bosniak': ['bosniak-classification-2019', 'solid-renal-masses'],
 'ra.solid-renal-masses': ['bosniak-classification-2019', 'solid-renal-masses'],
 'ra.liver-masses': ['characterisation-of-liver-masses',
                     'common-liver-tumors',
                     'incidentalomas-in-the-liver',
                     'liver-segmental-anatomy',
                     'li-rads',
                     'acr-li-rads'],
 'ra.liver-lirads': ['characterisation-of-liver-masses',
                     'common-liver-tumors',
                     'incidentalomas-in-the-liver',
                     'liver-segmental-anatomy',
                     'li-rads',
                     'acr-li-rads'],
 'ra.ct-abdominal-trauma': ['ct-in-abdominal-trauma'],
 'ra.adrenal-lesions': ['characterization-of-adrenal-lesions-update', 'ese-ensat-adrenal-incidentaloma-guideline-2023'],
 'ra.mri-anal-cancer': ['anal-cancer-staging', 'acr-appropriateness-criteria-staging-and-follow-up-of-anal-cancer'],
 'ra.aortic-aneurysm-rupture': ['aortic-aneurysm-rupture'],
 'ra.appendicitis': ['appendicitis-and-mimics',
                     'appendicitis-us-findings',
                     'appendicitis-pitfalls-in-us-and-ct-diagnosis'],
 'ra.ultrasound-bile-duct-stones': ['common-bile-duct-stones-ultrasound',
                                    'gallbladder-obstruction',
                                    'biliary-duct-pathology',
                                    'gallbladder-wall-thickening'],
 'ra.ultrasound-gallbladder': ['common-bile-duct-stones-ultrasound',
                               'gallbladder-obstruction',
                               'biliary-duct-pathology',
                               'gallbladder-wall-thickening'],
 'ra.biliary-duct-pathology': ['common-bile-duct-stones-ultrasound',
                               'gallbladder-obstruction',
                               'biliary-duct-pathology',
                               'gallbladder-wall-thickening'],
 'ra.mri-bladder': ['bladder-cancer-vi-rads', 'vi-rads-development-consensus'],
 'ra.ct-bowel-ischaemia': ['bowel-ischemia-video-lectures', 'ct-pattern-of-bowel-wall-thickening'],
 'ra.ct-bowel-wall': ['bowel-ischemia-video-lectures', 'ct-pattern-of-bowel-wall-thickening'],
 'ra.ct-bowel-obstruction': ['closed-loop-in-small-bowel-obstruction', 'closed-loop-obstruction-with-video'],
 'ra.ct-small-bowel-tumours': ['small-bowel-tumors', 'sharp-foreign-bodies-in-gi-tract'],
 'ra.gi-foreign-bodies': ['small-bowel-tumors', 'sharp-foreign-bodies-in-gi-tract'],
 'ra.ultrasound-gi-tract': ['us-of-the-gi-tract-technique', 'us-of-the-gi-tract-normal-anatomy'],
 'ra.mri-crohn': ['crohn-s-disease-role-of-mri',
                  'crohn-s-disease-role-of-ultrasound',
                  'us-of-mimics-of-inflammatory-bowel-disease'],
 'ra.ultrasound-ibd': ['crohn-s-disease-role-of-mri',
                       'crohn-s-disease-role-of-ultrasound',
                       'us-of-mimics-of-inflammatory-bowel-disease'],
 'ra.ovarian-cysts': ['ovarian-cystic-lesions',
                      'roadmap-to-evaluate-ovarian-cysts',
                      'acr-o-rads-us-v2022',
                      'acr-o-rads-mri'],
 'ra.ct-pancreatitis': ['acute-pancreatitis'],
 'ra.ct-pancreatic-cancer': ['pancreatic-cancer-ct-staging-2-0', 'pancreatic-cystic-lesions'],
 'ra.pancreatic-cysts': ['pancreatic-cancer-ct-staging-2-0', 'pancreatic-cystic-lesions'],
 'ra.dynamic-rectal-examination': ['dynamic-rectal-examination',
                                   'esur-esgar-recommendations-for-mri-of-pelvic-floor-dysfunction',
                                   'esr-essentials-pelvic-floor-imaging-esur-practice-recommendations-2026'],
 'ra.abdominal-wall-hernias': ['abdominal-wall-hernias',
                               'anatomy-of-peritoneum-and-mesentery',
                               'peritoneal-carcinomatosis',
                               'peritoneal-pathology'],
 'ra.ct-peritoneum': ['abdominal-wall-hernias',
                      'anatomy-of-peritoneum-and-mesentery',
                      'peritoneal-carcinomatosis',
                      'peritoneal-pathology'],
 'ra.ct-peritoneal-carcinomatosis': ['abdominal-wall-hernias',
                                     'anatomy-of-peritoneum-and-mesentery',
                                     'peritoneal-carcinomatosis',
                                     'peritoneal-pathology'],
 'ra.thoracic-ultrasound': ['thoracic-ultrasound-in-acute-abdomen',
                            'british-thoracic-society-pleural-disease-guideline-2023'],
 'ra.mri-prostate': ['prostate-cancer-pi-rads-v2-1',
                     'prostate-anatomy',
                     'acr-pi-rads-v2-1',
                     'acr-pi-rads-resources-and-current-reference-documents',
                     'acr-pi-rads-v2-1-report-template'],
 'ra.mri-rectal-cancer': ['rectal-cancer-mr-staging-and-restaging-update-2026', 'perianal-fistulas'],
 'ra.mri-perianal-fistula': ['rectal-cancer-mr-staging-and-restaging-update-2026', 'perianal-fistulas'],
 'ra.ultrasound-acute-gynaecology': ['acute-abdomen-in-gynaecology-ultrasound',
                                     'endometriosis-mri-detection',
                                     'cervical-cancer-mr-staging',
                                     'endometrial-cancer-mr-staging',
                                     'm-llerian-duct-anomalies'],
 'ra.mri-endometriosis': ['acute-abdomen-in-gynaecology-ultrasound',
                          'endometriosis-mri-detection',
                          'cervical-cancer-mr-staging',
                          'endometrial-cancer-mr-staging',
                          'm-llerian-duct-anomalies'],
 'ra.mri-cervical-cancer': ['acute-abdomen-in-gynaecology-ultrasound',
                            'endometriosis-mri-detection',
                            'cervical-cancer-mr-staging',
                            'endometrial-cancer-mr-staging',
                            'm-llerian-duct-anomalies'],
 'ra.mri-endometrial-cancer': ['acute-abdomen-in-gynaecology-ultrasound',
                               'endometriosis-mri-detection',
                               'cervical-cancer-mr-staging',
                               'endometrial-cancer-mr-staging',
                               'm-llerian-duct-anomalies'],
 'ra.mullerian-anomalies': ['acute-abdomen-in-gynaecology-ultrasound',
                            'endometriosis-mri-detection',
                            'cervical-cancer-mr-staging',
                            'endometrial-cancer-mr-staging',
                            'm-llerian-duct-anomalies'],
 'ra.neonatal-acute-abdomen': ['acute-abdomen-in-neonates', 'necrotizing-enterocolitis'],
 'ra.necrotising-enterocolitis': ['acute-abdomen-in-neonates', 'necrotizing-enterocolitis'],
 'ra.paediatric-cystic-abdominal-masses': ['cystic-abdominal-masses-in-children',
                                           'solid-abdominal-masses-in-children',
                                           'renal-tumors-in-children'],
 'ra.paediatric-solid-abdominal-masses': ['cystic-abdominal-masses-in-children',
                                          'solid-abdominal-masses-in-children',
                                          'renal-tumors-in-children'],
 'ra.paediatric-renal-tumours': ['cystic-abdominal-masses-in-children',
                                 'solid-abdominal-masses-in-children',
                                 'renal-tumors-in-children'],
 'ra.ultrasound-paediatric-scrotum': ['acute-scrotum-in-children']}
def f(k,label,text,parents=None,ex=None,bad=None):
 d={'id':k,'label':label,'text':text}
 if parents:d['requires_any']=parents
 if ex:d['exclusive_group']=ex
 if bad:d['invalidates_normal']=bad
 return d
def s(k,label,group,normal,findings,exclude=False,repeat=False):
 d={'id':k,'label':label,'group':group,'normal':normal,'findings':findings}
 if exclude:d['exclude_from_bulk_normal']=True
 if repeat:d.update(repeatable=True,repeat_label='Lesion')
 return d
def measure(label,parents,unit='mm'):
 return f('measure','Exact dimensions',f'{label} measures __ {unit} × __ {unit} × __ {unit}.',parents)
def vessel(k,label,group='Vessels',tumour=False):
 fs=[f('thrombus','Thrombus',f'The {label.lower()} contains [non-occlusive / occlusive] [bland thrombus / suspected tumour thrombus / indeterminate thrombus].',ex='lumen'),f('narrow','Stenosis',f'The {label.lower()} has [mild / moderate / severe] focal narrowing.',ex='lumen'),f('collateral','Collaterals',f'Collateral vessels are present around the {label.lower()}.')]
 if tumour:fs += [f('contact','Tumour contact',f'Tumour contact with the {label.lower()} spans [less than 180 degrees / exactly 180 degrees / more than 180 degrees] of its circumference, with [smooth / irregular] vessel contour.'),f('contact-length','Contact length',f'Tumour contact along the {label.lower()} measures __ mm.',['contact'])]
 return s(k,label,group,f'The {label.lower()} is patent without focal narrowing.',fs,True)
def nodes(stations,group='Lymph nodes'):
 return [s(slug('nodes-'+n),n,group,f'No morphologically suspicious {n.lower()} lymph node is identified.',[f('suspicious','Suspicious morphology',f'A {n.lower()} lymph node is [rounded / irregular / heterogeneous / necrotic / clustered with adjacent nodes].'),f('size','Short axis',f'The {n.lower()} lymph node short axis measures __ mm.',['suspicious'])],repeat=True) for n in stations]
def collection(k='collection',group='Complications',places='right upper quadrant / left upper quadrant / right lower quadrant / left lower quadrant / pelvis / retroperitoneum'):
 return s(k,'Fluid collection',group,None,[f('collection','Collection',f'A [simple fluid / complex fluid / gas-containing / haemorrhagic] collection is present in the [{places}].'),measure('The collection',['collection']),f('wall','Wall', 'The collection wall is [thin / thick / irregular / not discernible].',['collection']),f('enhance','After contrast','On the acquired post-contrast images the collection has [rim enhancement / no rim enhancement / indeterminate enhancement].',['collection'])],True,True)
def organ(k,label,kind,group='Solid organs',us=False):
 word='visualised ' if us else ''
 fs={'liver':[f('fat','Steatosis',f'The {word}liver has [diffuse / geographic] steatosis.'),f('contour','Cirrhotic morphology',f'The {word}liver has a nodular surface with [caudate enlargement / left lateral segment enlargement / right lobe volume loss].'),f('mass','Focal lesion',f'A [cystic / solid / indeterminate] focal lesion is present in hepatic segment [I / II / III / IVa / IVb / V / VI / VII / VIII].'),measure('The hepatic lesion',['mass'])],
 'spleen':[f('enlarged','Splenomegaly','The spleen is enlarged.'),f('length','Length','Splenic craniocaudal length measures __ mm.',['enlarged']),f('lesion','Focal lesion','A [cystic / solid / wedge-shaped] splenic lesion is present.'),measure('The splenic lesion',['lesion'])],
 'pancreas':[f('oedema','Inflammatory change','The pancreatic [head / uncinate process / neck / body / tail / entire gland] is enlarged with surrounding inflammatory change.'),f('atrophy','Atrophy','There is [focal / diffuse] pancreatic atrophy.'),f('mass','Mass','A [solid / cystic / mixed solid-cystic] lesion is present in the pancreatic [head / uncinate process / neck / body / tail].'),measure('The pancreatic lesion',['mass'])],
 'kidney':[f('scar','Scarring',f'The {label.lower()} has [focal cortical scarring / diffuse cortical thinning].'),f('stone','Calculus',f'The {label.lower()} contains a calculus in the [upper calyx / interpolar calyx / lower calyx / pelvis].'),f('stone-size','Calculus size',f'The {label.lower()} calculus measures __ mm.',['stone']),f('mass','Focal lesion',f'The {label.lower()} contains a [simple cyst / complex cyst / solid lesion / wedge-shaped parenchymal abnormality].'),measure(f'The {label.lower()} lesion',['mass'])],
 'adrenal':[f('nodular','Nodule',f'The {label.lower()} contains a [homogeneous / heterogeneous / fat-containing / calcified] nodule.'),measure(f'The {label.lower()} nodule',['nodular']),f('thick','Thickening',f'The {label.lower()} shows [smooth / nodular] thickening.')]}[kind]
 normals={'liver':f'No focal abnormality is identified in the {word}liver.','spleen':f'The {word}spleen is not enlarged and has no focal abnormality.','pancreas':f'No focal abnormality or inflammatory change is identified in the {word}pancreas.','kidney':f'The {word}{label.lower()} has preserved parenchymal thickness without a focal lesion.','adrenal':f'The {word}{label.lower()} is not enlarged and contains no nodule.'}
 return s(k,label,group,normals[kind],fs,us)
def urinary(us=False):
 rows=[organ('right-kidney','Right kidney','kidney',us=us),organ('left-kidney','Left kidney','kidney',us=us)]
 for side in ['Right','Left']:
  rows += [s(slug(side+'-collecting-system'),side+' collecting system','Urinary tract',f'The {side.lower()} collecting system is not dilated.',[f('dilatation','Dilatation',f'There is [mild / moderate / severe] {side.lower()} pelvicalyceal dilatation.'),f('pelvis-size','Pelvic diameter',f'The {side.lower()} renal pelvis measures __ mm anteroposteriorly.',['dilatation'])]),s(slug(side+'-ureter'),side+' ureter','Urinary tract',f'The visualised {side.lower()} ureter is not dilated.',[f('dilated','Hydroureter',f'The {side.lower()} ureter is dilated to the [proximal ureter / mid ureter / distal ureter / ureterovesical junction].'),f('stone','Calculus',f'A calculus is present in the {side.lower()} [proximal ureter / mid ureter / distal ureter / ureterovesical junction].'),f('size','Calculus size',f'The {side.lower()} ureteric calculus measures __ mm.',['stone'])],True)]
 rows += [s('bladder','Bladder','Urinary tract','The adequately distended bladder has no focal wall abnormality.',[f('wall','Wall thickening','Bladder wall thickening is [diffuse / focal at the dome / focal at the trigone / focal at the right lateral wall / focal at the left lateral wall / focal at the posterior wall].'),f('stone','Calculus','An intravesical calculus is present.'),f('gas','Gas','Gas is present [within the bladder lumen / within the bladder wall].'),f('limited','Underdistended','The bladder is underdistended, limiting wall assessment.')],True)]
 return rows
def biliary(us=False):
 return [s('gallbladder-lumen','Gallbladder lumen','Hepatobiliary','The gallbladder contains no calculus or sludge.',[f('stones','Calculi','The gallbladder contains [a single mobile calculus / multiple mobile calculi / an impacted neck calculus / an impacted infundibular calculus].'),f('size','Largest calculus','The largest gallbladder calculus measures __ mm.',['stones']),f('sludge','Sludge','[Mobile layering / Non-mobile tumefactive] sludge is present in the gallbladder.'),f('distended','Distension','The gallbladder is distended.'),f('absent','Post-cholecystectomy','The gallbladder is surgically absent.',ex='absence')]),s('gallbladder-wall','Gallbladder wall','Hepatobiliary','The gallbladder wall is not thickened.',[f('thick','Thickening','Gallbladder wall thickening is [diffuse smooth / focal smooth / focal irregular / striated oedematous].'),f('measure','Thickness','The gallbladder wall measures __ mm.',['thick']),f('hyper','Doppler hyperaemia','Doppler assessment shows gallbladder wall hyperaemia.'),f('defect','Wall defect','A focal gallbladder wall defect is present.'),f('gas','Mural gas','Gas is present within the gallbladder wall.')]),s('pericholecystic','Pericholecystic tissues','Hepatobiliary','No pericholecystic fluid or inflammatory change is identified.',[f('fluid','Fluid','Pericholecystic fluid is present.'),f('fat','Inflammation','Pericholecystic inflammatory change is present.')]),s('common-bile-duct','Common bile duct','Bile ducts','The common bile duct is not dilated.',[f('dilated','Dilatation','The common bile duct is dilated [throughout / proximal to a distal obstruction].'),f('diameter','Diameter','The common bile duct measures __ mm.',['dilated']),f('stone','Choledocholithiasis','A [single / multiple] [proximal / mid-duct / distal] common bile duct [calculus is / calculi are] identified.'),f('stone-size','Stone size','The largest common bile duct calculus measures __ mm.',['stone']),f('sludge','Debris','Intraluminal biliary sludge or debris is present.'),f('cutoff','Abrupt cutoff','There is abrupt common bile duct narrowing at the [porta hepatis / pancreatic head / ampulla].')]),s('right-intrahepatic-ducts','Right intrahepatic ducts','Bile ducts','The right intrahepatic ducts are not dilated.',[f('dilated','Dilatation','The right intrahepatic ducts show [central / peripheral / central and peripheral] dilatation.'),f('strictures','Strictures','The right intrahepatic ducts show [a focal stricture / multifocal strictures with intervening dilatation].')]),s('left-intrahepatic-ducts','Left intrahepatic ducts','Bile ducts','The left intrahepatic ducts are not dilated.',[f('dilated','Dilatation','The left intrahepatic ducts show [central / peripheral / central and peripheral] dilatation.'),f('strictures','Strictures','The left intrahepatic ducts show [a focal stricture / multifocal strictures with intervening dilatation].')])]
def appendix(us=False):
 return [s('appendix','Appendix','Appendix','The appendix is visualised, normal in calibre and has no surrounding inflammatory change.',[f('dilated','Dilated appendix','The appendix is dilated [diffusely / at the tip / proximally].'),f('diameter','Outer diameter','The appendix outer diameter measures __ mm.',['dilated']),f('wall','Wall thickening','The appendiceal wall is thickened [uniformly / irregularly].'),f('appendicolith','Appendicolith','An appendicolith is present at the [base / body / tip].'),f('defect','Wall defect','A focal appendiceal wall defect is identified.'),f('not-seen','Not visualised','The appendix is not visualised; appendicitis cannot be excluded on this examination.',ex='visibility')]),s('periappendiceal-fat','Periappendiceal fat','Appendix','No periappendiceal inflammatory change is identified.',[f('fat','Inflammation','Periappendiceal inflammatory change is present.'),f('phlegmon','Phlegmon','An ill-defined periappendiceal inflammatory mass is present.')]),s('periappendiceal-fluid','Periappendiceal fluid and gas','Appendix','No periappendiceal collection or extraluminal gas is identified.',[f('fluid','Collection','A [simple / complex / gas-containing] periappendiceal collection is present.'),measure('The periappendiceal collection',['fluid']),f('gas','Extraluminal gas','Extraluminal gas is present adjacent to the appendix.')])]+([s('appendix-compression','Appendiceal compression and Doppler','Ultrasound manoeuvres',None,[f('compression','Compression','On graded compression the appendix is [compressible / non-compressible / not assessable].'),f('doppler','Vascularity','Doppler assessment of the appendiceal wall shows [increased flow / preserved flow / absent detectable flow / technically limited flow assessment].')],True)] if us else [])
BOWEL=['Stomach','Duodenum','Jejunum','Proximal ileum','Terminal ileum','Caecum','Ascending colon','Transverse colon','Descending colon','Sigmoid colon','Rectum']
def bowel(names=BOWEL,us=False,mri=False,ibd=False):
 rows=[]
 for n in names:
  fs=[f('thick','Wall thickening',f'The {n.lower()} shows [symmetric circumferential / asymmetric eccentric / stratified oedematous] wall thickening.'),f('wall-size','Wall thickness',f'The {n.lower()} wall measures __ mm.',['thick']),f('length','Involved length',f'The involved {n.lower()} segment measures __ cm.',['thick']),f('dilated','Dilatation',f'The {n.lower()} is dilated.'),f('calibre','Luminal calibre',f'The {n.lower()} lumen measures __ mm.',['dilated']),f('narrow','Narrowing',f'The {n.lower()} has [a short focal / a long segment] fixed narrowing with [no upstream dilatation / upstream dilatation].'),f('fat','Adjacent inflammation',f'There is inflammatory change adjacent to the {n.lower()}.'),f('pneumatosis','Pneumatosis',f'Intramural gas is present in the {n.lower()}.')]
  if us:fs += [f('layers','Stratification',f'The {n.lower()} wall layers are [preserved / partially lost / completely lost].',['thick']),f('doppler','Doppler',f'On Doppler assessment the {n.lower()} wall has [increased flow / reduced detectable flow / no detectable flow].',['thick']),f('motility','Motility',f'During real-time assessment the {n.lower()} has [increased peristalsis / reduced peristalsis / absent observed peristalsis].')]
  else:fs += [f('enhance','After contrast',f'On acquired post-contrast images the {n.lower()} wall shows [hyperenhancement / reduced enhancement / absent enhancement / layered enhancement].',['thick','narrow','dilated'])]
  if mri:fs += [f('oedema','T2 oedema',f'T2 hyperintense mural oedema is present in the {n.lower()}.',['thick']),f('dwi','Diffusion',f'The {n.lower()} wall shows restricted diffusion.',['thick'])]
  if ibd:fs += [f('ulcers','Ulceration',f'[Superficial / Deep] ulceration is present in the {n.lower()}.'),f('comb','Comb sign',f'Engorged vasa recta are present adjacent to the {n.lower()}.'),f('fat-prolif','Fibrofatty proliferation',f'Mesenteric fibrofatty proliferation is present adjacent to the {n.lower()}.')]
  rows.append(s(slug(n),n,'Bowel segments',f'The visualised {n.lower()} is not dilated and has no mural thickening.',fs,us))
 return rows
def peritoneal():
 return [s('free-fluid','Peritoneal fluid','Peritoneum','No free intraperitoneal fluid is identified.',[f('fluid','Free fluid','There is [trace / small volume / moderate volume / large volume] [simple fluid / complex fluid / haemoperitoneum] in the [pelvis / right upper quadrant / left upper quadrant / paracolic gutters / abdomen and pelvis].')]),s('free-gas','Extraluminal gas','Peritoneum','No pneumoperitoneum is identified.',[f('gas','Free gas','[Localised / Diffuse] free intraperitoneal gas is present.'),f('retro','Retroperitoneal gas','Retroperitoneal extraluminal gas is present.')])]
def abdomen(us=False):
 return [organ('liver','Liver','liver',us=us),*biliary(us),organ('pancreas','Pancreas','pancreas',us=us),organ('spleen','Spleen','spleen',us=us),*urinary(us),*peritoneal()]
def save(k,rows):
 a=next(x for x in ASSIGN if x['investigation_id']==k)
 for row in rows: row['source_ids']=REFS[k]
 OUT['investigations'][k]={'guide_id':a['guide_id'],'title':a['title'],'modality':a['modality'],'sections':rows}

save('ra.acute-abdomen',abdomen()+bowel()+appendix()+nodes(['Mesenteric','Retroperitoneal'])+[collection()])
save('ra.ultrasound-acute-abdomen',abdomen(True)+bowel(['Terminal ileum','Caecum','Sigmoid colon'],True)+appendix(True)+[collection()])
save('ra.transvaginal-nongynaecology',bowel(['Terminal ileum','Appendix','Sigmoid colon','Rectum'],True)+urinary(True)[2:]+peritoneal()+[collection(places='right adnexal region / left adnexal region / pouch of Douglas / rectovaginal space')])
save('ra.appendicitis',appendix(True)+bowel(['Terminal ileum','Caecum','Sigmoid colon'],True)+urinary(True)+peritoneal()+[collection()])
for k in ['ra.ultrasound-bile-duct-stones','ra.ultrasound-gallbladder','ra.biliary-duct-pathology']:
 rows=[organ('liver','Liver','liver',us=k!='ra.biliary-duct-pathology'),*biliary(True),organ('pancreas','Pancreas','pancreas',us=True)]
 rows += [s('common-hepatic-duct','Common hepatic duct and confluence','Bile ducts','The common hepatic duct and hilar confluence show no focal narrowing.',[f('stricture','Stricture','A [smooth / irregular / shouldered] stricture involves the [common hepatic duct / hilar confluence / right hepatic duct / left hepatic duct].'),f('length','Stricture length','The biliary stricture spans __ mm.',['stricture']),f('mass','Periductal mass','A mass surrounds the [common hepatic duct / hilar confluence / right hepatic duct / left hepatic duct].'),measure('The periductal mass',['mass'])]),s('cystic-duct','Cystic duct','Bile ducts',None,[f('stone','Cystic duct stone','A cystic duct calculus is present with [no common hepatic duct compression / extrinsic common hepatic duct compression].')],True)]
 if k!='ra.biliary-duct-pathology':rows += [s('murphy','Sonographic Murphy sign','Ultrasound manoeuvre',None,[f('sign','Murphy sign','The sonographic Murphy sign is [positive / negative / indeterminate / not assessable after analgesia].')],True)]
 else:rows += [vessel('portal-vein','Portal vein'),s('mrcp','MRCP assessment','MRCP only',None,[f('mrcp','Duct morphology','On the acquired MRCP sequences the biliary tree shows [multifocal beading / dominant hilar narrowing / distal intraductal filling defects / postoperative biliary anastomotic narrowing].')],True)]
 save(k,rows)

# Focal renal lesions: repeatable lesion blocks, separate vessels and collecting systems.
for k,cyst in [('ra.renal-cysts-bosniak',True),('ra.solid-renal-masses',False)]:
 fs=[f('lesion','Lesion location','A renal lesion is located in the [right / left] [upper pole / interpolar region / lower pole], [anteriorly / posteriorly / medially / laterally / centrally].'),measure('The renal lesion',['lesion']),f('growth','Growth pattern','The renal lesion is [predominantly exophytic / partly exophytic / entirely endophytic].',['lesion']),f('sinus','Renal sinus relationship','The renal lesion [is separate from / abuts / extends into] the renal sinus.',['lesion']),f('collecting','Collecting system relationship','The renal lesion [does not involve / abuts / distorts / invades] the collecting system.',['lesion']),f('fat','Macroscopic fat','Macroscopic fat is [present / absent / indeterminate] in the renal lesion.',['lesion']),f('haemorrhage','Haemorrhage','Haemorrhagic contents are present in the renal lesion.',['lesion']),f('ct','CT attenuation','On the acquired unenhanced CT images the lesion measures __ HU.',['lesion']),f('enhance','Enhancement','On acquired pre- and post-contrast images the renal lesion shows [no measurable enhancement / homogeneous enhancement / heterogeneous enhancement / indeterminate enhancement].',['lesion']),f('diffusion','MRI diffusion','On the acquired diffusion sequences the renal lesion shows [restricted diffusion / no restricted diffusion / indeterminate diffusion].',['lesion'])]
 if cyst:fs += [f('wall','Cyst wall','The renal cyst wall is [smooth and thin / smoothly minimally thickened / thickened / irregular].',['lesion']),f('wall-mm','Wall thickness','Maximum renal cyst wall thickness measures __ mm.',['wall']),f('septa','Septa','The renal cyst contains [no septa / one to three septa / four or more septa].',['lesion']),f('septa-character','Septal morphology','Renal cyst septa are [thin smooth / minimally thickened smooth / thick / irregular], with [no demonstrated enhancement / enhancement / indeterminate enhancement].',['septa']),f('nodule','Mural nodule','A renal cyst mural nodule is [enhancing / non-enhancing / indeterminate for enhancement].',['lesion']),f('nodule-size','Nodule size','The renal cyst mural nodule measures __ mm.',['nodule']),f('calc','Calcification','Renal cyst calcification is [punctate / coarse / curvilinear].',['lesion']),f('bosniak','Assigned Bosniak category','The clinician-assigned Bosniak v2019 category is [I / II / IIF / III / IV / not classifiable on this examination].',['lesion'])]
 else:fs += [f('necrosis','Necrosis','The renal mass contains [no visible necrosis / focal necrosis / extensive necrosis].',['lesion']),f('pseudocapsule','Pseudocapsule','The renal mass has [a visible pseudocapsule / no discernible pseudocapsule].',['lesion']),f('gerota','Fascial extension','The renal mass [remains within / extends beyond] Gerota fascia.',['lesion']),f('nephrometry','Hilar proximity','The nearest distance from renal mass to collecting system or sinus measures __ mm.',['lesion'])]
 rows=urinary()+[s('renal-lesion','Renal lesion','Focal lesions',None,fs,True,True),vessel('right-renal-vein','Right renal vein'),vessel('left-renal-vein','Left renal vein'),vessel('ivc','Inferior vena cava'),organ('right-adrenal','Right adrenal','adrenal'),organ('left-adrenal','Left adrenal','adrenal'),*nodes(['Right hilar','Left hilar','Paracaval','Para-aortic']),*peritoneal()]
 for row in rows:
  if row['id']=='renal-lesion':
   next(x for x in row['findings'] if x['id']=='lesion')['invalidates_normal']=['right-kidney','left-kidney']
 save(k,rows)

for k in ['ra.liver-masses','ra.liver-lirads']:
 fs=[f('lesion','Observation','A focal hepatic observation is present in segment [I / II / III / IVa / IVb / V / VI / VII / VIII].'),measure('The hepatic observation',['lesion']),f('composition','Composition','The hepatic observation is [solid / cystic / mixed solid-cystic / predominantly fatty].',['lesion']),f('margin','Margin','The hepatic observation has [well-defined / ill-defined / lobulated / infiltrative] margins.',['lesion']),f('ap','Arterial phase','On acquired arterial-phase images the observation shows [non-rim hyperenhancement / rim hyperenhancement / peripheral discontinuous nodular enhancement / no arterial hyperenhancement / non-diagnostic arterial assessment].',['lesion']),f('pv','Portal venous phase','On acquired portal venous-phase images the observation shows [non-peripheral washout / peripheral washout / persistent enhancement / centripetal filling / no washout / indeterminate washout].',['lesion']),f('delayed','Delayed phase','On acquired delayed-phase images the observation has [an enhancing capsule / progressive central enhancement / persistent enhancement / no enhancing capsule / indeterminate capsule].',['lesion']),f('t2','T2 signal','On acquired T2-weighted images the observation is [markedly hyperintense / mildly hyperintense / isointense / hypointense / heterogeneous].',['lesion']),f('dwi','Diffusion','On acquired diffusion images the observation has [restricted diffusion / no restricted diffusion / indeterminate diffusion].',['lesion']),f('chemical-shift','Chemical shift','On acquired opposed-phase images the observation shows [signal loss / no signal loss].',['lesion']),f('hb','Hepatobiliary phase','On the acquired hepatobiliary phase the observation is [hypointense / isointense / hyperintense / heterogeneous].',['lesion']),f('growth','Interval change','Compared with the available prior examination the observation is [new / enlarged / unchanged / smaller / no longer visible].',['lesion'])]
 if k=='ra.liver-lirads':fs += [f('lirads','Assigned LI-RADS','For an eligible untreated observation, the clinician-assigned CT/MRI LI-RADS v2018 category is [LR-1 / LR-2 / LR-3 / LR-4 / LR-5 / LR-M / LR-TIV / LR-NC].',['lesion']),f('eligibility','Eligibility','LI-RADS diagnostic categorisation is [applicable in this at-risk adult / not applicable because the patient is not in the defined at-risk population / not applicable because this observation is treated].',['lesion'])]
 rows=[organ('liver-background','Background liver','liver'),s('hepatic-observation','Hepatic observation','Focal observations',None,fs,True,True)]
 for seg in ['I','II','III','IVa','IVb','V','VI','VII','VIII']:
  rows.append(s('segment-'+seg.lower(),'Segment '+seg,'Segmental distribution',None,[f('burden','Distribution',f'Segment {seg} contains [a solitary observation / multiple observations / confluent infiltrative tumour].')],True))
 rows += [vessel('main-portal-vein','Main portal vein'),vessel('right-portal-vein','Right portal vein'),vessel('left-portal-vein','Left portal vein'),vessel('right-hepatic-vein','Right hepatic vein'),vessel('middle-hepatic-vein','Middle hepatic vein'),vessel('left-hepatic-vein','Left hepatic vein'),vessel('ivc','Inferior vena cava'),*biliary(),organ('spleen','Spleen','spleen'),*nodes(['Porta hepatis','Portacaval','Coeliac','Para-aortic']),*peritoneal()]
 # Background normal only concerns diffuse morphology, avoiding a contradiction with observations.
 rows[0]['normal']='The liver has smooth contour without imaging features of diffuse chronic liver disease.'
 rows[0]['findings']=[x for x in rows[0]['findings'] if x['id'] in ['fat','contour']]
 save(k,rows)
# Trauma: injuries assigned separately to organs, vascular structures and compartments.
rows=[]
for n in ['Liver','Spleen','Right kidney','Left kidney','Pancreas','Right adrenal','Left adrenal']:
 fs=[f('laceration','Laceration',f'The {n.lower()} has [a single laceration / multiple lacerations / a deep parenchymal disruption].'),f('depth','Laceration depth',f'The deepest {n.lower()} laceration measures __ mm.',['laceration']),f('haematoma','Haematoma',f'A [subcapsular / intraparenchymal / periorgan] haematoma involves the {n.lower()}.'),measure(f'The {n.lower()} haematoma',['haematoma']),f('devascularisation','Perfusion defect',f'On the acquired contrast-enhanced images the {n.lower()} has [a focal perfusion defect / segmental devascularisation / global devascularisation].'),f('bleeding','Active vascular injury',f'There is [active contrast extravasation / a pseudoaneurysm / an arteriovenous fistula] at the {n.lower()}.')]
 if 'kidney' in n:fs += [f('urine','Excretory phase','On the acquired excretory phase there is [no urinary contrast leak / a contained urinary contrast leak / extensive urinary contrast extravasation] adjacent to the '+n.lower()+'.')]
 if n=='Pancreas':fs += [f('duct','Main duct','The main pancreatic duct is [intact where visualised / interrupted at the injury / not adequately assessed].',['laceration'])]
 rows.append(s(slug(n),n,'Solid organ injury',f'No traumatic injury is identified in the {n.lower()}.',fs))
for n in ['Duodenum','Jejunum','Ileum','Colon']:
 rows.append(s(slug(n),n,'Bowel injury',f'No traumatic mural abnormality is identified in the {n.lower()}.',[f('wall','Mural injury',f'The {n.lower()} has [focal mural thickening / an intramural haematoma / focal wall discontinuity].'),f('gas','Adjacent gas',f'Extraluminal gas is present adjacent to the {n.lower()}.'),f('contrast','Enteric contrast leak',f'On the acquired enteric contrast images there is extraluminal contrast adjacent to the {n.lower()}.')]))
rows += [s('mesentery','Mesentery','Bowel injury','No mesenteric haematoma or focal stranding is identified.',[f('haematoma','Haematoma','A mesenteric haematoma is present in the [small bowel mesentery / transverse mesocolon / sigmoid mesocolon].'),measure('The mesenteric haematoma',['haematoma']),f('bleed','Vascular injury','The mesentery shows [active contrast extravasation / vessel beading / abrupt vessel cutoff].')]),*peritoneal(),collection(),vessel('aorta','Abdominal aorta'),vessel('ivc','Inferior vena cava')]
for n in ['Right hemidiaphragm','Left hemidiaphragm','Urinary bladder','Anterior abdominal wall']:
 rows.append(s(slug(n),n,'Additional injury',f'No traumatic disruption of the {n.lower()} is identified.',[f('disruption','Disruption',f'Traumatic disruption of the {n.lower()} is [suspected / demonstrated].'),f('haematoma','Haematoma',f'A haematoma is present at the {n.lower()}.')]))
save('ra.ct-abdominal-trauma',rows)

rows=[]
for side in ['Right','Left']:
 fs=[f('lesion','Adrenal lesion',f'The {side.lower()} adrenal contains a [homogeneous / heterogeneous / predominantly cystic / fat-containing] lesion.'),measure(f'The {side.lower()} adrenal lesion',['lesion']),f('unenhanced','Unenhanced attenuation',f'On the acquired unenhanced CT images the {side.lower()} adrenal lesion measures __ HU.',['lesion']),f('enhanced','Enhanced attenuation',f'On the acquired enhanced CT images the {side.lower()} adrenal lesion measures __ HU.',['lesion']),f('delayed','Delayed attenuation',f'On the acquired delayed CT images the {side.lower()} adrenal lesion measures __ HU.',['lesion']),f('chemical','Chemical shift',f'On the acquired chemical-shift MRI images the {side.lower()} adrenal lesion shows [homogeneous signal loss / heterogeneous signal loss / no signal loss / indeterminate signal loss] on opposed-phase imaging.',['lesion']),f('blood','Haemorrhage',f'The {side.lower()} adrenal lesion contains haemorrhagic products.',['lesion']),f('calcification','Calcification',f'The {side.lower()} adrenal lesion contains [punctate / coarse / peripheral] calcification.',['lesion']),f('invasion','Local invasion',f'The {side.lower()} adrenal lesion [abuts without definite invasion / invades] the [kidney / liver / pancreas / diaphragm / inferior vena cava].',['lesion']),f('interval','Interval change',f'Compared with the available prior examination the {side.lower()} adrenal lesion is [new / larger / unchanged / smaller].',['lesion'])]
 rows += [s(slug(side+'-adrenal'),side+' adrenal','Adrenal glands',f'The {side.lower()} adrenal gland has no focal lesion.',fs,repeat=True)]
rows += [vessel('ivc','Inferior vena cava'),vessel('left-renal-vein','Left renal vein'),*nodes(['Retrocrural','Para-aortic','Paracaval']),organ('liver','Liver','liver')]
save('ra.adrenal-lesions',rows)

rows=[]
for n in ['Suprarenal aorta','Juxtarenal aorta','Infrarenal aorta','Right common iliac artery','Left common iliac artery','Right internal iliac artery','Left internal iliac artery','Right external iliac artery','Left external iliac artery']:
 fs=[f('aneurysm','Aneurysm',f'The {n.lower()} has a [fusiform / saccular] aneurysm.'),f('diameter','Outer-wall diameter',f'The {n.lower()} maximal outer-wall diameter perpendicular to its centreline measures __ mm.',['aneurysm']),f('thrombus','Mural thrombus',f'The {n.lower()} contains [eccentric / circumferential] mural thrombus.'),f('rupture','Rupture signs',f'The {n.lower()} shows [active extravasation / focal wall disruption / an adjacent sentinel haematoma / a draped contour / a hyperattenuating crescent].'),f('stranding','Perivascular stranding',f'Perivascular stranding surrounds the {n.lower()}.')]
 rows.append(s(slug(n),n,'Aorta and iliac arteries',f'The {n.lower()} is not aneurysmal.',fs))
rows += [s('proximal-neck','Proximal aneurysm neck','Repair anatomy',None,[f('neck','Neck','The infrarenal aneurysm neck is [straight / angulated / conical / reverse conical].'),f('length','Length','The infrarenal aneurysm neck length measures __ mm.',['neck']),f('diameter','Diameter','The proximal aneurysm neck diameter measures __ mm.',['neck']),f('angulation','Angulation','Proximal aneurysm neck angulation measures __ degrees.',['neck'])],True),collection('retroperitoneal-haematoma',places='right retroperitoneum / left retroperitoneum / bilateral retroperitoneum'),*peritoneal()]
for n in ['Coeliac artery','Superior mesenteric artery','Right renal artery','Left renal artery']:rows.append(vessel(slug(n),n))
save('ra.aortic-aneurysm-rupture',rows)

for k in ['ra.ct-bowel-ischaemia','ra.ct-bowel-wall','ra.ct-bowel-obstruction','ra.ct-small-bowel-tumours','ra.gi-foreign-bodies','ra.ultrasound-gi-tract','ra.mri-crohn','ra.ultrasound-ibd']:
 us=k in ['ra.ultrasound-gi-tract','ra.ultrasound-ibd'];mri=k=='ra.mri-crohn';ibd=k in ['ra.mri-crohn','ra.ultrasound-ibd']
 rows=bowel(us=us,mri=mri,ibd=ibd)+peritoneal()+[collection()]+nodes(['Mesenteric','Retroperitoneal'])
 if k in ['ra.ct-bowel-ischaemia','ra.ct-bowel-wall','ra.ct-bowel-obstruction']:
  rows += [vessel(slug(n),n) for n in ['Coeliac artery','Superior mesenteric artery','Inferior mesenteric artery','Superior mesenteric vein','Portal vein']]
  rows += [s('portomesenteric-gas','Portomesenteric venous gas','Complications','No portomesenteric venous gas is identified.',[f('gas','Venous gas','Gas is present in the [mesenteric veins / main portal vein / intrahepatic portal branches / mesenteric and portal veins].')])]
 if k=='ra.ct-bowel-obstruction':
  rows += [s('transition','Transition point','Obstruction',None,[f('transition','Transition','A transition point is present in the [jejunum / proximal ileum / distal ileum / terminal ileum], in the [right upper quadrant / left upper quadrant / right lower quadrant / left lower quadrant / pelvis].'),f('cause','Cause','The obstruction is associated with [an adhesion pattern without a visible mass / an external hernia / an internal hernia / an intraluminal foreign body / a tumour / an inflammatory stricture / intussusception / gallstone ileus].',['transition']),f('closed','Closed loop','[Two adjacent transition points / A C-shaped closed loop / A U-shaped closed loop / A mesenteric whirl] is present.',['transition']),f('faeces','Small bowel faeces','A small bowel faeces sign is present immediately proximal to the transition.',['transition'])],repeat=True)]
 if k=='ra.ct-small-bowel-tumours':
  rows += [s('bowel-tumour','Small bowel lesion','Tumour',None,[f('lesion','Location and growth','A [annular constricting / polypoid intraluminal / exophytic / infiltrative] lesion arises from the [duodenum / jejunum / proximal ileum / distal ileum].'),measure('The small bowel lesion',['lesion']),f('enhance','Enhancement','On acquired post-contrast images the lesion is [hyperenhancing / hypoenhancing / heterogeneously enhancing].',['lesion']),f('necrotic','Necrosis','The lesion contains [central necrosis / cavitation communicating with the lumen / coarse calcification].',['lesion']),f('spread','Mesenteric reaction','Adjacent mesentery shows [desmoplastic retraction / a spiculated mass / vascular encasement].',['lesion'])],repeat=True)]
 if k=='ra.gi-foreign-bodies':
  rows += [s('foreign-body','Foreign body','Foreign bodies',None,[f('body','Foreign body','A [linear sharp / blunt rounded / button battery / magnet / multiple clustered magnets / indeterminate] foreign body is located in the [oesophagus / stomach / duodenum / jejunum / ileum / caecum / colon / rectum].'),measure('The foreign body',['body']),f('penetration','Wall relationship','The foreign body is [entirely intraluminal / embedded in the wall / penetrating through the wall / entirely extraluminal].',['body']),f('migration','Migration','The penetrating foreign body extends into the [mesentery / liver / pancreas / retroperitoneum / abdominal wall].',['penetration']),f('change','Interval movement','Compared with the available prior images the foreign body [has progressed distally / remains at the same location / is no longer visible].',['body'])],repeat=True)]
 if ibd:
  rows += [s('penetrating-tract','Fistula or sinus','Penetrating disease',None,[f('tract','Tract','A tract arises from the [jejunum / ileum / terminal ileum / colon / rectum] and is [blind-ending / enteroenteric / enterocolic / enterovesical / enterocutaneous].'),f('activity','Activity','The tract contains [fluid / gas / fibrotic tissue].',['tract']),measure('The associated inflammatory mass',['tract'])],repeat=True),s('anastomosis','Surgical anastomosis','Postoperative bowel',None,[f('anastomosis','Anastomosis','The [ileocolic / small bowel / colorectal] anastomosis shows [no mural abnormality / inflammatory thickening / fixed narrowing / suspected dehiscence].')],True)]
 save(k,rows)

# Pancreatic inflammatory and neoplastic reports.
def pancreas_parts(inflammation=False):
 rows=[]
 for n in ['Head','Uncinate process','Neck','Body','Tail']:
  fs=[f('enlarged','Enlargement',f'The pancreatic {n.lower()} is [focally enlarged / diffusely enlarged].'),f('atrophy','Atrophy',f'There is parenchymal atrophy in the pancreatic {n.lower()}.'),f('duct','Duct calibre',f'The main pancreatic duct in the {n.lower()} measures __ mm.')]
  if inflammation:fs += [f('oedema','Oedema',f'Inflammatory oedema involves the pancreatic {n.lower()}.'),f('necrosis','Non-enhancement',f'On acquired post-contrast images the pancreatic {n.lower()} shows [focal non-enhancement / extensive non-enhancement].')]
  rows.append(s('pancreas-'+slug(n),'Pancreatic '+n.lower(),'Pancreas',f'The pancreatic {n.lower()} has no focal contour abnormality or inflammatory change.',fs))
 return rows
for k in ['ra.ct-pancreatitis','ra.ct-pancreatic-cancer','ra.pancreatic-cysts']:
 rows=pancreas_parts(k=='ra.ct-pancreatitis')+biliary()+[vessel(slug(n),n,tumour=k=='ra.ct-pancreatic-cancer') for n in ['Coeliac artery','Common hepatic artery','Superior mesenteric artery','Portal vein','Superior mesenteric vein','Splenic vein','Splenic artery']]+nodes(['Peripancreatic','Porta hepatis','Coeliac','Para-aortic'])+peritoneal()
 if k=='ra.ct-pancreatitis':
  rows += [s('pancreatic-collection','Pancreatic collection','Collections',None,[f('collection','Collection','A collection is present in the [lesser sac / anterior pararenal space / peripancreatic tissues / mesenteric root / pelvis], containing [fluid only / fluid and non-liquid debris / predominantly non-liquid debris].'),measure('The pancreatic collection',['collection']),f('capsule','Encapsulation','The collection is [unencapsulated / partially encapsulated / fully encapsulated].',['collection']),f('gas','Gas','Gas is present within the collection.',['collection']),f('duct','Duct relationship','The main pancreatic duct [communicates with the collection / terminates at the collection / cannot be evaluated at the collection].',['collection']),f('term','Clinical classification','With clinical timing confirmed, the clinician-assigned revised Atlanta collection type is [acute peripancreatic fluid collection / acute necrotic collection / pseudocyst / walled-off necrosis / indeterminate].',['collection'])],repeat=True),s('whole-gland-necrosis','Necrosis extent','Pancreas',None,[f('extent','Extent','The estimated pancreatic parenchymal non-enhancement involves [none / less than 30 percent / 30–50 percent / more than 50 percent] of the gland on acquired contrast-enhanced images.')],True)]
 else:
  fs=[f('lesion','Lesion','A pancreatic lesion is present in the [head / uncinate process / neck / body / tail].'),measure('The pancreatic lesion',['lesion']),f('duct','Main duct','The lesion [does not communicate with / communicates with / obstructs / has an indeterminate relationship to] the main pancreatic duct.',['lesion']),f('upstream','Upstream parenchyma','Upstream pancreatic parenchyma shows [no atrophy / mild atrophy / marked atrophy].',['lesion']),f('invasion','Adjacent structures','The lesion [abuts without definite invasion / invades] the [duodenum / stomach / transverse colon / left adrenal / left kidney].',['lesion'])]
  if k=='ra.pancreatic-cysts':fs += [f('morph','Cyst morphology','The pancreatic cyst is [unilocular / macrocystic multilocular / microcystic / mixed microcystic and macrocystic].',['lesion']),f('wall','Wall','The cyst wall is [thin smooth / thick smooth / irregular].',['lesion']),f('nodule','Mural nodule','A [non-enhancing / enhancing / indeterminate] mural nodule is present on the acquired contrast-enhanced examination.',['lesion']),f('nodule-size','Nodule size','The pancreatic cyst mural nodule measures __ mm.',['nodule']),f('septa','Septa','Pancreatic cyst septa are [absent / thin / thick / irregular].',['lesion']),f('calc','Calcification','Calcification is [central stellate / peripheral / coarse internal] within the pancreatic lesion.',['lesion'])]
  else:fs += [f('enhance','Enhancement','The pancreatic lesion is [hypoenhancing / isoenhancing / hyperenhancing / heterogeneously enhancing] on acquired pancreatic-phase imaging.',['lesion']),f('duct-cutoff','Duct cutoff','There is abrupt [pancreatic duct / common bile duct / pancreatic and common bile duct] cutoff at the lesion.',['lesion'])]
  rows += [s('pancreatic-lesion','Pancreatic lesion','Lesions',None,fs,True,True),organ('liver','Liver','liver')]
 save(k,rows)
def extension(k,label,group='Local extension'):
 return s(k,label,group,f'No tumour invasion of the {label.lower()} is identified.',[f('contact','Contact',f'Tumour [abuts with a preserved interface / abuts with an indeterminate interface / directly invades] the {label.lower()}.'),f('depth','Invasion depth',f'Tumour extends __ mm into the {label.lower()}.',['contact'])])
def pelvic_nodes(inguinal=False):
 names=['Right obturator','Left obturator','Right internal iliac','Left internal iliac','Right external iliac','Left external iliac','Right common iliac','Left common iliac','Presacral','Mesorectal']
 if inguinal:names += ['Right inguinal','Left inguinal']
 return nodes(names)
# Prostate: zone- and sequence-specific inputs, with separate capsule, NVBs and seminal vesicles.
fs=[f('lesion','Lesion location','A prostate lesion lies in the [right / left] [apex / mid gland / base], in the [anterior / posteromedial / posterolateral] sector.'),f('zone','Zone of origin','The lesion originates in the [peripheral zone / transition zone / central zone / anterior fibromuscular stroma].',['lesion']),measure('The prostate lesion',['lesion']),f('t2-morphology','T2 morphology','The lesion is [a circumscribed encapsulated nodule / a mostly encapsulated nodule / a heterogeneous ill-defined area / a lenticular non-circumscribed focus / a homogeneous markedly hypointense focus] on T2-weighted images.',['lesion']),f('diffusion','Diffusion morphology','The lesion has [focal marked ADC hypointensity with marked high-b-value hyperintensity / focal mild ADC hypointensity with mild high-b-value hyperintensity / linear diffusion abnormality / no focal diffusion abnormality].',['lesion']),f('t2-adequate','T2 adequate','T2-weighted imaging is adequate for assessment of this lesion.',['lesion'],ex='t2-quality'),f('t2-inadequate','T2 inadequate','T2-weighted imaging is inadequate for assessment of this lesion.',['lesion'],ex='t2-quality'),f('dwi-adequate','DWI adequate','DWI and ADC imaging are adequate for assessment of this lesion.',['lesion'],ex='dwi-quality'),f('dwi-inadequate','DWI inadequate','DWI and ADC imaging are inadequate for assessment of this lesion.',['lesion'],ex='dwi-quality'),f('t2-score','Assigned T2 score','The clinician-assigned PI-RADS v2.1 T2 sequence score is [1 / 2 / 3 / 4 / 5].',['t2-adequate']),f('dwi-score','Assigned DWI score','The clinician-assigned PI-RADS v2.1 DWI sequence score is [1 / 2 / 3 / 4 / 5].',['dwi-adequate']),f('dce','Dynamic contrast','The PI-RADS v2.1 DCE assessment is [positive / negative / not available].',['lesion']),f('treatment','Applicability','This lesion is in a [treatment-naive prostate / previously treated prostate].',['lesion']),f('capsule-contact','Capsular contact','The prostate lesion has capsular contact spanning __ mm.',['lesion']),f('capsule-breach','Capsular breach','The lesion shows [capsular bulging without definite breach / definite extraprostatic extension / indeterminate extraprostatic extension].',['lesion'],bad=['prostatic-capsule']),f('index','Index lesion','This is the index lesion based on the reviewed MRI findings.',['lesion'])]
rows=[s('prostate-background','Prostate background','Gland','There is no diffuse prostatic signal abnormality.',[f('bph','BPH','The transition zone contains [mild / moderate / marked] benign prostatic hyperplastic nodules.'),f('prostatitis','Inflammatory pattern','The peripheral zone has [linear / wedge-shaped / diffuse] low T2 signal without a discrete mass.'),f('haemorrhage','Haemorrhage','Haemorrhagic signal is present in the [right peripheral zone / left peripheral zone / bilateral peripheral zones / transition zone].')]),s('prostate-dimensions','Prostate dimensions','Gland',None,[f('dimensions','Dimensions','The prostate measures __ mm transverse × __ mm anteroposterior × __ mm craniocaudal.')]),s('prostate-lesion','Prostate lesion','Focal lesions',None,fs,True,True),extension('prostatic-capsule','Prostatic capsule'),extension('right-neurovascular-bundle','Right neurovascular bundle'),extension('left-neurovascular-bundle','Left neurovascular bundle'),extension('right-seminal-vesicle','Right seminal vesicle'),extension('left-seminal-vesicle','Left seminal vesicle'),extension('bladder-neck','Bladder neck'),extension('external-urethral-sphincter','External urethral sphincter'),extension('rectum','Rectal wall'),*pelvic_nodes(),s('pelvic-bones','Pelvic bones','Additional findings','No suspicious focal marrow lesion is identified within the imaged pelvic bones.',[f('lesion','Marrow lesion','A suspicious marrow lesion is present in the [sacrum / right ilium / left ilium / right ischium / left ischium / right pubis / left pubis / proximal femur].'),measure('The marrow lesion',['lesion'])],repeat=True)]
save('ra.mri-prostate',rows)

# Bladder: sequence components and each wall region; score assigned, not invented from morphology.
fs=[f('lesion','Lesion location','A bladder lesion is present at the [dome / anterior wall / posterior wall / right lateral wall / left lateral wall / trigone / bladder neck].'),measure('The bladder lesion',['lesion']),f('morph','Morphology','The bladder lesion is [papillary on a thin stalk / papillary on a broad stalk / sessile / infiltrative flat wall thickening].',['lesion']),f('muscle','T2 muscle layer','The detrusor low-signal line beneath the lesion is [preserved / focally indistinct / focally interrupted / extensively interrupted].',['lesion']),f('dwi','Diffusion extent','Restricted diffusion [is confined to the luminal lesion / reaches but does not clearly cross the muscle / crosses the muscle / extends into perivesical fat / cannot be assessed].',['lesion']),f('dce','Dynamic enhancement extent','On acquired dynamic contrast images early enhancement [is confined to the inner layer / reaches but does not clearly cross the muscle / crosses the muscle / extends into perivesical fat / cannot be assessed].',['lesion']),f('virads','Assigned VI-RADS','The clinician-assigned VI-RADS 2018 category for this untreated lesion is [1 / 2 / 3 / 4 / 5 / not applicable].',['lesion']),f('orifice','Ureteric orifice','The lesion [spares / involves / obscures] the [right ureteric orifice / left ureteric orifice / both ureteric orifices].',['lesion']),f('perivesical','Perivesical extension','The lesion has macroscopic perivesical extension.',['lesion'],bad=['perivesical-fat'])]
rows=[s('bladder-distension','Bladder distension','Acquisition',None,[f('distension','Distension','Bladder distension is [adequate / insufficient / excessive].'),f('timing','Treatment context','The bladder examination is [before TURBT or intravesical treatment / after TURBT / after intravesical treatment / in an indeterminate treatment context].')],True),s('bladder-lesion','Bladder lesion','Focal lesions',None,fs,True,True),extension('perivesical-fat','Perivesical fat'),extension('prostate-stroma','Prostatic stroma'),extension('uterus','Uterus'),extension('vagina','Vagina'),extension('pelvic-sidewall','Pelvic sidewall'),*urinary(),*pelvic_nodes()]
save('ra.mri-bladder',rows)

# Rectal and anal staging deliberately describe anatomy rather than automatically assigning TNM.
for k in ['ra.mri-rectal-cancer','ra.mri-anal-cancer']:
 rectal=k=='ra.mri-rectal-cancer'
 fs=[f('tumour','Visible tumour',('The rectal tumour is [polypoid / sessile / partly annular / circumferential / diffusely infiltrative].' if rectal else 'The tumour is centred in the [anal canal / anal margin / anorectal junction].')),measure('The tumour',['tumour']),f('circumference','Circumferential location','The tumour occupies the [anterior / right anterolateral / right lateral / right posterolateral / posterior / left posterolateral / left lateral / left anterolateral / entire] circumference.',['tumour']),f('clock','Clock-face extent','The tumour spans from __ o’clock to __ o’clock.',['tumour']),f('lower-border','Height from anal verge','The tumour lower border lies __ mm above the anal verge.',['tumour']),f('junction','Anorectal junction relationship','The lower tumour border is [above / at / below] the anorectal junction.',['tumour']),f('mucin','Mucin','The tumour contains [no visible mucinous component / a focal mucinous component / a predominant mucinous component].',['tumour']),f('dwi','Diffusion','The tumour shows [restricted diffusion / equivocal restriction / no restricted diffusion].',['tumour'])]
 if rectal:fs += [f('takeoff','Sigmoid take-off','The tumour is [entirely below / straddling / entirely above] the sigmoid take-off.',['tumour']),f('reflection','Anterior peritoneal reflection','The tumour is [below / straddling / above] the anterior peritoneal reflection.',['tumour']),f('wall','Mural depth','The tumour [is confined to the bowel wall / extends beyond muscularis propria / invades the peritoneal surface / directly invades an adjacent structure].',['tumour']),f('extramural-depth','Extramural depth','Tumour extends __ mm beyond the muscularis propria.',['wall'])]
 rows=[s('primary-tumour','Primary tumour','Primary tumour',None,fs,True,True)]
 if rectal:rows += [s('mesorectal-fascia','Mesorectal fascia','Local extent','The mesorectal fascia is not threatened by visible tumour-bearing tissue.',[f('distance','Nearest distance','The closest [primary tumour / extramural venous invasion / tumour deposit / irregular node with suspected extranodal extension] lies __ mm from the mesorectal fascia.'),f('location','Nearest margin location','The closest mesorectal fascial margin is [anterior / right anterolateral / right lateral / right posterolateral / posterior / left posterolateral / left lateral / left anterolateral].',['distance'])]),s('emvi','Extramural venous invasion','Local extent','No extramural venous tumour invasion is identified.',[f('emvi','EMVI','Extramural venous invasion is [equivocal / present], in the [mesorectum / superior rectal vascular pedicle].')]),s('tumour-deposit','Mesorectal tumour deposit','Local extent',None,[f('deposit','Deposit','A mesorectal tumour deposit lies [anterior / right lateral / posterior / left lateral] to the rectum.'),measure('The mesorectal deposit',['deposit']),f('mrf','Margin distance','The tumour deposit lies __ mm from the mesorectal fascia.',['deposit'])],repeat=True)]
 rows += [extension(slug(n),n) for n in ['Internal anal sphincter','Intersphincteric plane','External anal sphincter','Right puborectalis','Left puborectalis','Right levator ani','Left levator ani','Right ischioanal fossa','Left ischioanal fossa','Vaginal wall','Prostate','Seminal vesicles','Bladder','Pelvic sidewall','Sacrum']]+pelvic_nodes(True)+[s('restaging','Post-treatment assessment','Restaging only',None,[f('context','Restaging','This is a post-treatment examination with prior images available.'),f('bed','Tumour bed','The tumour bed shows [predominantly low T2 fibrosis / mixed fibrosis and intermediate T2 signal / persistent intermediate T2 tumour signal / predominantly mucinous signal].',['context']),f('residual','Residual diffusion','The treated bed shows [no focal restricted diffusion / equivocal focal restricted diffusion / definite focal restricted diffusion].',['context']),f('change','Interval response','Compared with the available prior examination the tumour burden has [decreased / remained similar / increased].',['context'])],True)]
 save(k,rows)

rows=[]
fs=[f('tract','Primary tract','A perianal fistula has a [intersphincteric / transsphincteric / suprasphincteric / extrasphincteric / superficial subcutaneous] course.'),f('internal','Internal opening','The internal opening is at __ o’clock, [below / at / above] the dentate line.',['tract']),f('height','Opening height','The internal opening lies __ mm above the anal verge.',['tract']),f('external','External opening','The external opening lies in the [right anterior perianal skin / right posterior perianal skin / left anterior perianal skin / left posterior perianal skin / right gluteal skin / left gluteal skin].',['tract']),f('activity','Activity','The tract contains [T2-bright fluid / predominantly low T2 fibrosis / mixed fluid and fibrosis].',['tract']),f('enhance','After contrast','On acquired contrast-enhanced images the tract shows [avid enhancement / mild enhancement / no enhancement].',['tract']),f('sphincter-level','Sphincter crossing','The tract crosses the [lower third / middle third / upper third] of the external sphincter.',['tract']),f('branch','Secondary extension','A secondary tract extends into the [intersphincteric plane / right ischioanal fossa / left ischioanal fossa / supralevator space / horseshoe posterior compartment / horseshoe anterior compartment].',['tract'])]
rows += [s('fistula','Fistula','Tracts',None,fs,True,True)]
for n in ['Internal anal sphincter','External anal sphincter','Intersphincteric space','Right ischioanal fossa','Left ischioanal fossa','Supralevator compartment','Levator plate']:
 rows += [s(slug(n),n,'Sphincters and spaces',f'No fistulous extension or collection is identified in the {n.lower()}.',[f('tract','Fistulous extension',f'A fistulous tract extends through the {n.lower()}.'),f('abscess','Abscess',f'An abscess involves the {n.lower()}.'),measure(f'The {n.lower()} abscess',['abscess']),f('scar','Scar',f'Low T2 scar tissue is present in the {n.lower()}.')])]
rows += [s('proctitis','Rectal wall','Associated disease','No rectal mural thickening is identified.',[f('thick','Proctitis','The rectum has [circumferential / eccentric] mural thickening with [mural oedema / restricted diffusion / perirectal inflammation].')])]
save('ra.mri-perianal-fistula',rows)

# Female pelvic imaging.
def uterus():
 return [s('uterine-position','Uterine position','Uterus',None,[f('position','Position','The uterus is [anteverted / retroverted / axial] and [anteflexed / retroflexed / unflexed].'),f('dimensions','Dimensions','The uterus measures __ mm length × __ mm anteroposterior × __ mm transverse.')]),s('myometrium','Myometrium','Uterus','The myometrium has no focal lesion.',[f('fibroid','Leiomyoma','A [submucosal / intramural / subserosal / pedunculated subserosal / cervical] leiomyoma is present in the [anterior wall / posterior wall / fundus / right lateral wall / left lateral wall / cervix].'),measure('The leiomyoma',['fibroid']),f('degeneration','Degeneration','The leiomyoma has [cystic / haemorrhagic / hyaline / calcific] degeneration.',['fibroid']),f('adenomyosis','Adenomyosis pattern','The myometrium has [focal / diffuse] features of adenomyosis.')],repeat=True),s('endometrium','Endometrium','Uterus',None,[f('thin','Endometrial appearance','The endometrium is [uniform / heterogeneous / poorly delineated].'),f('thickness','Thickness','Double-layer endometrial thickness measures __ mm.'),f('fluid','Cavity fluid','The endometrial cavity contains [simple fluid / echogenic debris / blood products].'),f('polyp','Polypoid lesion','An endometrial polypoid lesion is present.'),measure('The endometrial lesion',['polyp'])]),s('cervix','Cervix','Uterus','No focal cervical mass is identified.',[f('cyst','Nabothian cysts','[Simple nabothian cysts / A cluster of cervical cysts] is present.'),f('mass','Mass','A [solid / mixed solid-cystic] cervical lesion is present.'),measure('The cervical lesion',['mass'])])]
def ovaries(us=False):
 rows=[]
 for side in ['Right','Left']:
  fs=[f('enlarge','Enlargement',f'The {side.lower()} ovary is enlarged with [preserved follicles / peripheral follicles / heterogeneous stroma].'),measure(f'The {side.lower()} ovary',['enlarge']),f('not-seen','Not visualised',f'The {side.lower()} ovary is not visualised.',ex='visibility'),f('absent','Surgically absent',f'The {side.lower()} ovary is surgically absent.',ex='visibility')]
  if us:fs += [f('arterial','Arterial Doppler',f'Arterial flow within the {side.lower()} ovary is [demonstrated / not detected / technically indeterminate].'),f('venous','Venous Doppler',f'Venous flow within the {side.lower()} ovary is [demonstrated / not detected / technically indeterminate].'),f('pedicle','Vascular pedicle',f'The {side.lower()} ovarian vascular pedicle has a twisted whirlpool appearance.')]
  rows += [s(slug(side+'-ovary'),side+' ovary','Adnexa',f'The visualised {side.lower()} ovary is not enlarged and has no adnexal mass.',fs,True)]
 return rows
def adnexal_lesion():
 return s('adnexal-lesion','Adnexal lesion','Adnexal lesions',None,[f('lesion','Location','An adnexal lesion is [right ovarian / left ovarian / right paraovarian / left paraovarian / right tubal / left tubal / midline of uncertain origin].'),measure('The adnexal lesion',['lesion']),f('cyst','Cystic morphology','The lesion is [unilocular / bilocular / multilocular / predominantly solid / mixed solid-cystic].',['lesion']),f('wall','Wall and septa','The lesion has [a smooth thin wall / a smooth thick wall / an irregular wall / smooth septa / irregular septa].',['lesion']),f('contents','Contents','The lesion contains [simple fluid / reticular haemorrhagic echoes / homogeneous low-level echoes / fat / proteinaceous fluid / mixed contents].',['lesion']),f('papillae','Papillary projections','There are [no papillary projections / one to three papillary projections / four or more papillary projections].',['lesion']),f('solid','Solid component','A solid component is present with [smooth / irregular] contour.',['lesion']),dict(measure('The solid adnexal component',['solid']),id='solid-measure'),f('doppler','US Doppler','On acquired Doppler images intralesional vascularity is [absent / minimal / moderate / very strong].',['lesion']),f('t1','MRI T1 signal','On acquired MRI the lesion is [T1 hypointense / T1 hyperintense without fat suppression / T1 hyperintense with fat suppression].',['lesion']),f('t2','MRI T2 signal','On acquired MRI the lesion is [T2 bright / T2 dark / T2 shading / heterogeneous on T2].',['lesion']),f('enhance','MRI enhancement','On acquired contrast-enhanced MRI the solid tissue shows [low-risk enhancement relative to myometrium / intermediate-risk enhancement relative to myometrium / high-risk enhancement relative to myometrium / indeterminate enhancement].',['solid']),f('orads-us','Assigned O-RADS US','The clinician-assigned O-RADS US v2022 category is [0 / 1 / 2 / 3 / 4 / 5 / not applicable].',['lesion']),f('orads-mri','Assigned O-RADS MRI','The clinician-assigned O-RADS MRI category under the ACR 2022 system is [0 / 1 / 2 / 3 / 4 / 5 / not applicable].',['lesion'])],True,True)
rows=uterus()+ovaries(True)+[adnexal_lesion()]+peritoneal()
for side in ['Right','Left']:rows += [s(slug(side+'-tube'),side+' fallopian tube','Adnexa',None,[f('dilated','Tubal dilatation',f'The {side.lower()} tube is dilated with [simple fluid / echogenic debris / blood products].'),f('wall','Wall thickening',f'The {side.lower()} tubal wall is thickened.'),f('complex','Tubo-ovarian complex',f'There is a complex {side.lower()} tubo-ovarian inflammatory mass.'),measure(f'The {side.lower()} tubo-ovarian mass',['complex'])],True)]
save('ra.ovarian-cysts',copy.deepcopy(rows))
acute=copy.deepcopy(rows)+[s('pregnancy-location','Pregnancy-related findings','Acute gynaecology',None,[f('intrauterine','Intrauterine sac','An intrauterine gestational sac is [present / absent / indeterminate].'),f('extrauterine','Extrauterine sac','An extrauterine gestational sac is present in the [right adnexa / left adnexa / cervix / Caesarean scar / interstitial region].'),f('yolk','Yolk sac','The extrauterine sac contains [a yolk sac / an embryo / a yolk sac and embryo].',['extrauterine']),f('cardiac','Cardiac activity','Embryonic cardiac activity in the extrauterine sac is [demonstrated / not demonstrated].',['yolk'])],True)]
save('ra.ultrasound-acute-gynaecology',acute)

rows=uterus()+ovaries()+[s('endometrioma','Ovarian endometrioma','Adnexa',None,[f('lesion','Endometrioma pattern','A [right / left] ovarian cyst has T1 hyperintensity persisting with fat suppression and [T2 shading / T2 dark spots / both T2 shading and dark spots].'),measure('The endometrioma',['lesion']),f('nodule','Mural nodule','A mural nodule in the endometrioma is [non-enhancing / enhancing / not assessable without contrast].',['lesion'])],True,True)]
for n,g in [('Bladder dome','Anterior compartment'),('Vesicouterine pouch','Anterior compartment'),('Right distal ureter','Lateral compartments'),('Left distal ureter','Lateral compartments'),('Right uterosacral ligament','Posterior compartment'),('Left uterosacral ligament','Posterior compartment'),('Torus uterinus','Posterior compartment'),('Rectovaginal septum','Posterior compartment'),('Posterior vaginal fornix','Posterior compartment'),('Pouch of Douglas','Posterior compartment'),('Anterior rectal wall','Bowel'),('Rectosigmoid','Bowel'),('Sigmoid colon','Bowel'),('Caecum','Bowel'),('Appendix','Bowel'),('Anterior abdominal wall scar','Extrapelvic sites')]:
 rows.append(s(slug(n),n,g,f'No deep endometriotic nodule is identified at the {n.lower()}.',[f('plaque','Fibrotic plaque',f'The {n.lower()} contains [a T2-dark fibrotic plaque / a nodular infiltrative lesion / haemorrhagic foci].'),measure(f'The {n.lower()} lesion',['plaque']),f('tether','Tethering',f'There is tethering and distortion at the {n.lower()}.'),f('lumen','Luminal compromise',f'Endometriotic involvement at the {n.lower()} causes [no luminal narrowing / luminal narrowing / upstream dilatation].',['plaque'])]))
rows += [s('pelvic-adhesions','Pelvic adhesions','Adhesions',None,[f('ovaries','Ovarian tethering','The ovaries are [medially tethered / apposed behind the uterus / tethered to the uterine surface].'),f('culdesac','Pouch of Douglas','The pouch of Douglas is [partly obliterated / completely obliterated].')],True)]
save('ra.mri-endometriosis',rows)

for k in ['ra.mri-cervical-cancer','ra.mri-endometrial-cancer']:
 cervical=k=='ra.mri-cervical-cancer'
 fs=[f('tumour','Tumour','A [polypoid / infiltrative / diffuse] tumour is centred in the '+('cervix.' if cervical else '[endometrial cavity / fundal endometrium / lower uterine segment].')),measure('The uterine tumour',['tumour']),f('dwi','Diffusion','The tumour shows [restricted diffusion / equivocal diffusion restriction / no restricted diffusion].',['tumour'])]
 if cervical:fs += [f('stromal','Cervical stroma','The low T2 cervical stromal rim is [preserved / partly disrupted / completely disrupted].',['tumour']),f('cranial','Cranial extent','The tumour extends to the [endocervical canal only / internal os / lower uterine segment / uterine corpus].',['tumour']),f('os-distance','Distance from internal os','The superior tumour margin lies __ mm below the internal os.',['tumour'])]
 else:fs += [f('invasion','Myometrial invasion','Myometrial invasion is [not identified / less than half of the myometrial thickness / at least half of the myometrial thickness / indeterminate].',['tumour']),f('depth','Invasion depth','Myometrial tumour invasion measures __ mm within a myometrium measuring __ mm in thickness.',['invasion']),f('serosa','Serosal surface','The tumour [does not reach / abuts / breaches] the uterine serosa.',['tumour']),f('cervical','Cervical involvement','The tumour [does not involve the cervix / extends into endocervical glands without definite stromal invasion / invades cervical stroma / has indeterminate cervical stromal involvement].',['tumour'])]
 rows=[s('uterine-tumour','Primary tumour','Primary tumour',None,fs,True,True)]
 for n in ['Right parametrium','Left parametrium','Upper vagina','Lower vagina','Bladder wall','Rectal wall','Right pelvic sidewall','Left pelvic sidewall','Right ovary','Left ovary']:
  rows.append(extension(slug(n),n))
 rows += urinary()[2:6]+pelvic_nodes()+peritoneal()+[s('treatment-bed','Treatment bed','Restaging only',None,[f('restaging','Post-treatment','The post-treatment bed shows [low T2 fibrosis without focal restriction / mixed fibrosis and focal restricted diffusion / residual intermediate T2 tumour signal with restriction].'),f('change','Interval change','Compared with the available prior MRI the tumour burden is [reduced / unchanged / increased].',['restaging'])],True)]
 save(k,rows)

rows=[s('uterine-contour','External uterine contour','Uterine anatomy',None,[f('contour','Fundal contour','The external fundal contour is [convex / flat / shallowly indented / deeply cleft].'),f('depth','External indentation','The external fundal indentation measures __ mm.',['contour'])]),s('endometrial-cavities','Endometrial cavities','Uterine anatomy',None,[f('cavities','Cavity configuration','There is [a single normal-shaped endometrial cavity / a single laterally curved cavity / a partial intracavitary septum / a complete intracavitary septum / two separate endometrial cavities / no visible functional cavity].'),f('septum','Septum composition','The intracavitary septum is [predominantly fibrous / predominantly muscular / mixed fibromuscular].',['cavities']),f('depth','Internal indentation','Internal fundal indentation measures __ mm.',['cavities']),f('angle','Internal angle','The internal fundal indentation angle measures __ degrees.',['cavities'])]),s('uterine-horns','Uterine horns','Uterine anatomy',None,[f('horns','Horns','Uterine horns are [single right-sided / single left-sided / paired communicating / paired non-communicating / not identified].'),f('rudimentary','Rudimentary horn','A [right / left] rudimentary horn contains [functional endometrium / no visible functional endometrium].'),f('retained','Retained contents','There is [haematometra / hydrometra] in the [right horn / left horn / main cavity].')]),s('cervical-anatomy','Cervical anatomy','Cervix and vagina',None,[f('cervices','Cervices','There is [one cervix / a duplicated cervix / cervical aplasia].')]),s('vaginal-anatomy','Vaginal anatomy','Cervix and vagina',None,[f('vagina','Vaginal morphology','The vagina has [normal continuity / a longitudinal non-obstructing septum / a longitudinal obstructing septum / a transverse septum / upper vaginal aplasia / complete vaginal aplasia].'),f('obstruction','Retained contents','The [right hemivagina / left hemivagina / entire vagina] contains [blood products / simple fluid].')]),*urinary(),*ovaries()]
save('ra.mullerian-anomalies',rows)
# Dynamic fluoroscopy keeps acquisition/evacuation findings explicitly selected.
rows=[s('performance','Examination performance','Technique',None,[f('phases','Acquired phases','The study includes [rest and strain / rest squeeze strain and evacuation / strain and attempted evacuation].'),f('limited','Limitations','Assessment is limited by [incomplete rectal filling / inability to evacuate / insufficient strain / non-physiological positioning].')],True)]
for phase in ['Rest','Squeeze','Strain','Evacuation']:
 rows += [s(slug('anorectal-angle-'+phase),phase+' anorectal angle','Anorectal mechanics',None,[f('angle','Angle',f'The anorectal angle during {phase.lower()} measures __ degrees.'),f('opening','Anal canal',f'During {phase.lower()} the anal canal is [closed / partially open / widely open].')],True)]
rows += [s('pelvic-descent','Pelvic floor descent','Anorectal mechanics',None,[f('descent','Descent','During maximal evacuation the anorectal junction descends [within the expected range / excessively / inadequately].'),f('distance','Descent distance','The anorectal junction descends __ mm relative to its resting position.',['descent'])],True),s('puborectalis','Puborectalis relaxation','Anorectal mechanics',None,[f('relaxation','Relaxation','During attempted evacuation the puborectalis impression [relaxes / persists / paradoxically increases].')],True),s('evacuation','Rectal evacuation','Evacuation',None,[f('emptying','Emptying','Rectal emptying is [complete / near complete / incomplete / absent].'),f('retention','Retained contrast','Residual contrast is [minimal / moderate / substantial].',['emptying'])],True),s('rectocele','Rectocele','Posterior compartment',None,[f('rectocele','Rectocele','A [small / moderate / large] [anterior / posterior] rectocele develops during evacuation.'),f('depth','Depth','The rectocele projects __ mm beyond the expected rectal contour.',['rectocele']),f('retention','Retention','The rectocele [empties completely / retains contrast] after evacuation.',['rectocele'])],True),s('intussusception','Rectal intussusception','Posterior compartment',None,[f('intussusception','Intussusception','Rectal intussusception [remains intrarectal / descends into the anal canal / extends outside the anal verge].'),f('wall','Wall layers','The intussusception appears [mucosal / full-thickness / indeterminate].',['intussusception'])],True),s('enterocele','Enterocele or sigmoidocele','Middle compartment',None,[f('hernia','Herniation','During evacuation [small bowel / sigmoid colon / peritoneal fat] descends between the rectum and vagina.'),f('compression','Outlet effect','The descending contents [do not compress / compress] the rectal outlet.',['hernia'])],True),s('vaginal-vault','Vaginal vault','Middle compartment if opacified',None,[f('descent','Vault descent','On the acquired opacified vaginal views the vaginal vault shows [no prolapse / caudal prolapse].')],True),s('bladder-base','Bladder base','Anterior compartment if opacified',None,[f('cystocele','Cystocele','On the acquired opacified bladder views the bladder base shows [no prolapse / caudal prolapse].')],True)]
save('ra.dynamic-rectal-examination',rows)

rows=[]
for n in ['Epigastric linea alba','Umbilicus','Infraumbilical linea alba','Right linea semilunaris','Left linea semilunaris','Right inguinal canal','Left inguinal canal','Right femoral canal','Left femoral canal','Right lumbar triangle','Left lumbar triangle','Parastomal region','Previous incisional site']:
 rows.append(s(slug(n),n,'Fascial defects',f'No hernia is identified at the {n.lower()}.',[f('hernia','Hernia',f'A hernia at the {n.lower()} contains [fat only / small bowel / colon / stomach / urinary bladder / mixed viscera].'),f('neck','Defect dimensions',f'The {n.lower()} fascial defect measures __ mm transverse × __ mm craniocaudal.',['hernia']),measure(f'The {n.lower()} hernia sac',['hernia']),f('obstructed','Bowel obstruction',f'The herniated bowel at the {n.lower()} shows [no obstruction / obstruction at the neck / a closed loop].',['hernia']),f('compromise','Compromise',f'The hernia at the {n.lower()} has [sac fluid / inflammatory stranding / bowel mural thickening / reduced mural enhancement on acquired contrast images / pneumatosis].',['hernia'])],exclude=n in ['Parastomal region','Previous incisional site'],repeat=True))
for side in ['Right','Left']:
 for m in ['rectus abdominis','external oblique','internal oblique','transversus abdominis']:
  rows.append(s(slug(side+'-'+m),side+' '+m,'Abdominal wall muscles',f'The {side.lower()} {m} has preserved bulk.',[f('atrophy','Atrophy',f'The {side.lower()} {m} has [mild / moderate / severe] atrophy.'),f('fat','Fatty change',f'There is [mild / moderate / severe] fatty replacement of the {side.lower()} {m}.'),f('width','Width',f'The {side.lower()} {m} width at the dominant defect measures __ mm.')]))
rows += [s('diastasis','Rectus diastasis','Abdominal wall geometry','No rectus diastasis is identified.',[f('diastasis','Diastasis','Rectus diastasis is present [above the umbilicus / at the umbilicus / below the umbilicus / throughout the midline].'),f('gap','Inter-rectus distance','The maximal inter-rectus distance measures __ mm.',['diastasis'])]),s('loss-domain','Hernia volumetry','Abdominal wall geometry',None,[f('sac','Hernia sac volume','The measured hernia sac volume is __ mL.'),f('cavity','Abdominal cavity volume','The measured abdominal cavity volume is __ mL.')]),s('mesh','Previous mesh repair','Postoperative repair',None,[f('mesh','Mesh','The visible mesh is [well positioned / folded / detached / recurrently herniated at its margin].'),f('collection','Mesh collection','A [simple / complex / gas-containing] collection abuts the mesh.'),measure('The mesh-adjacent collection',['collection']),f('fistula','Fistula','There is a suspected communication between bowel and [mesh / skin / an adjacent collection].')],True)]
save('ra.abdominal-wall-hernias',rows)

peritoneal_sites=['Right subphrenic space','Left subphrenic space','Liver capsule','Splenic capsule','Falciform ligament','Porta hepatis','Lesser sac','Gastrohepatic ligament','Greater omentum','Right paracolic gutter','Left paracolic gutter','Small bowel mesentery','Mesenteric root','Transverse mesocolon','Sigmoid mesocolon','Pelvic cul-de-sac','Small bowel serosa','Colonic serosa','Anterior parietal peritoneum']
for k in ['ra.ct-peritoneum','ra.ct-peritoneal-carcinomatosis']:
 rows=[]
 for n in peritoneal_sites:
  rows.append(s(slug(n),n,'Peritoneal distribution',f'No nodularity or mass is identified at the {n.lower()}.',[f('nodules','Nodules',f'The {n.lower()} contains [a discrete nodule / multiple nodules / confluent soft tissue / sheet-like thickening].'),measure(f'The dominant deposit at the {n.lower()}',['nodules']),f('stranding','Stranding',f'There is [mild / marked] stranding at the {n.lower()}.'),f('fluid','Loculated fluid',f'Loculated fluid is present at the {n.lower()}.'),f('calcification','Calcification',f'Calcified deposits are present at the {n.lower()}.')]))
 rows += peritoneal()+bowel(['Jejunum','Ileum','Colon'])+nodes(['Porta hepatis','Coeliac','Para-aortic','Pelvic'])+[collection()]
 if k=='ra.ct-peritoneal-carcinomatosis':
  rows += [s('surgical-sites','Surgically relevant extent','Operability descriptors',None,[f('mesenteric-root','Mesenteric root','Tumour at the mesenteric root [does not encase / encases] the mesenteric vessels.'),f('bowel','Small bowel burden','Small bowel serosal involvement is [limited focal / multifocal / diffuse confluent].'),f('porta','Hilar involvement','Porta hepatis disease [spares / narrows / encases] the portal triad.'),f('obstruction','Obstruction','Peritoneal disease causes [no bowel obstruction / a single-level obstruction / multilevel bowel obstruction].')],True)]
 save(k,rows)

rows=[]
for side in ['Right','Left']:
 rows += [s(slug(side+'-pleural-fluid'),side+' pleural fluid','Pleural spaces',f'No {side.lower()} pleural effusion is identified in the examined windows.',[f('effusion','Effusion',f'The {side.lower()} pleural space contains [a small / a moderate / a large] [anechoic / echogenic / septated] effusion.'),f('depth','Depth',f'Maximal {side.lower()} pleural fluid depth in the examined position measures __ mm.',['effusion'])]),s(slug(side+'-pleura'),side+' pleura','Pleural surfaces',f'The examined {side.lower()} pleural surface is smooth.',[f('thickening','Thickening',f'The {side.lower()} pleura shows [smooth thickening / irregular thickening / nodular thickening].'),f('sliding','Lung sliding',f'At the examined {side.lower()} anterior chest windows lung sliding is [present / absent / indeterminate].'),f('lung-point','Lung point',f'A lung point is identified in the {side.lower()} [anterior / lateral] chest.')]),s(slug(side+'-lung-base'),side+' lung base','Subpleural lung',f'No focal subpleural consolidation is identified at the examined {side.lower()} lung base.',[f('consolidation','Consolidation',f'The {side.lower()} lung base has subpleural consolidation with [dynamic air bronchograms / static air bronchograms / fluid bronchograms].'),f('b-lines','B-lines',f'The examined {side.lower()} lung windows show [focal / diffuse] B-lines.'),f('atelectasis','Atelectasis',f'Compressive atelectasis is present at the {side.lower()} lung base.')]),s(slug(side+'-diaphragm'),side+' diaphragm','Diaphragm',None,[f('motion','Motion',f'During the assessed respiratory manoeuvre the {side.lower()} hemidiaphragm has [normal caudal excursion / reduced excursion / absent excursion / paradoxical cranial motion].'),f('measure','Excursion',f'The {side.lower()} diaphragmatic excursion measures __ mm.',['motion'])],True)]
save('ra.thoracic-ultrasound',rows)

# Neonatal studies distinguish radiographic observations from optional US/contrast observations.
for k in ['ra.neonatal-acute-abdomen','ra.necrotising-enterocolitis']:
 rows=[]
 for n in ['Stomach','Proximal small bowel','Distal small bowel','Colon','Rectum']:
  rows.append(s(slug(n),n,'Radiographic gas pattern',None,[f('gas','Gas pattern',f'On the acquired radiograph the {n.lower()} is [normally aerated / dilated / poorly aerated / gasless].'),f('pneumatosis','Pneumatosis',f'Pneumatosis is visible in the {n.lower()}.'),f('persistent','Persistent loop',f'A persistently dilated {n.lower()} loop remains in the same position on the available serial radiographs.')],True))
 rows += [s('free-air','Free intraperitoneal air','Radiographic complications',None,[f('air','Free air','On the acquired radiographs there is [no visible free intraperitoneal air / subdiaphragmatic free air / a football sign / a falciform ligament sign / free air on the horizontal-beam view].')],True),s('portal-gas','Portal venous gas','Gas complications',None,[f('gas','Portal gas','Portal venous gas is [visible on radiographs / visible on acquired ultrasound / not seen on the acquired examination].')],True),s('abdominal-fluid','Abdominal fluid','Ultrasound findings',None,[f('fluid','Fluid','On the acquired ultrasound there is [no free fluid / simple free fluid / complex free fluid / a focal collection].'),measure('The focal abdominal collection',['fluid'])],True),s('us-bowel','Bowel wall ultrasound','Ultrasound findings',None,[f('wall','Mural assessment','On acquired ultrasound the bowel wall is [normal thickness with preserved layers / thickened with preserved layers / thickened with lost layers / abnormally thin].'),f('wall-size','Wall thickness','The affected bowel wall measures __ mm.',['wall']),f('perfusion','Doppler perfusion','On the acquired Doppler assessment the affected bowel wall has [preserved flow / increased flow / reduced flow / no detectable flow / technically indeterminate flow].',['wall']),f('motility','Motility','During acquired real-time ultrasound the affected loops have [preserved peristalsis / reduced peristalsis / absent observed peristalsis].',['wall'])],True),s('sma-smv','Mesenteric vessel relationship','Ultrasound rotation assessment',None,[f('orientation','Orientation','On acquired ultrasound the superior mesenteric vein is [right of the artery / left of the artery / anterior to the artery / not adequately seen].'),f('whirlpool','Whirlpool','A mesenteric whirlpool is [demonstrated / not demonstrated / not adequately assessed] on the acquired ultrasound.')],True)]
 if k=='ra.neonatal-acute-abdomen':
  rows += [s('upper-gi','Duodenal course','Acquired upper GI contrast study',None,[f('junction','DJ junction','On the acquired upper GI study the duodenojejunal junction is [normally positioned / low and right-sided / indeterminate].'),f('corkscrew','Duodenal obstruction','The contrast-filled duodenum shows [a corkscrew configuration / an abrupt cutoff / a web-like narrowing / no obstructing abnormality].')],True),s('contrast-enema','Colonic contrast assessment','Acquired contrast enema',None,[f('colon','Calibre','The acquired contrast enema shows [normal colonic calibre / microcolon / left colon narrowing / an abrupt colonic transition].'),f('rectosigmoid','Rectosigmoid ratio','The rectum is [wider than / similar in calibre to / narrower than] the sigmoid colon.'),f('plug','Filling defects','There are [meconium plugs / small pellets / no intraluminal filling defects] on the acquired enema.')],True)]
 save(k,rows)

for k in ['ra.paediatric-cystic-abdominal-masses','ra.paediatric-solid-abdominal-masses','ra.paediatric-renal-tumours']:
 cyst=k=='ra.paediatric-cystic-abdominal-masses';renal=k=='ra.paediatric-renal-tumours'
 fs=[f('mass','Mass origin','The mass arises from the [right kidney / left kidney / right adrenal / left adrenal / liver / spleen / pancreas / mesentery / retroperitoneum / right ovary / left ovary / presacral space / indeterminate organ].'),measure('The abdominal mass',['mass']),f('boundary','Margins','The mass has [smooth well-defined / lobulated / infiltrative] margins.',['mass']),f('cross-midline','Midline relationship','The mass [does not cross / crosses] the midline.',['mass']),f('calc','Calcification','The mass contains [no visible calcification / punctate calcification / coarse calcification / peripheral calcification].',['mass']),f('blood','Haemorrhage','The mass contains [no visible haemorrhage / haemorrhagic components].',['mass']),f('fat','Fat','Macroscopic fat is [present / absent / indeterminate] within the mass.',['mass'])]
 if cyst:fs += [f('locules','Locules','The cystic mass is [unilocular / multilocular].',['mass']),f('contents','Contents','The cyst contains [simple fluid / proteinaceous fluid / haemorrhagic debris / mixed fluid and solid components].',['mass']),f('wall','Wall','The cyst wall is [thin smooth / thick smooth / irregular / layered with a bowel-wall signature].',['mass']),f('septa','Septa','Internal septa are [absent / thin / thick / irregular].',['mass']),f('solid','Solid nodule','A mural solid nodule is present.',['mass']),f('solid-size','Nodule size','The mural solid nodule measures __ mm.',['solid']),f('duct','Duct connection','The cyst [communicates with / displaces without communication / has an indeterminate relationship to] the [common bile duct / pancreatic duct / collecting system / urinary bladder / bowel lumen].',['mass'])]
 else:fs += [f('tissue','Internal architecture','The mass is [homogeneous solid / heterogeneous solid / predominantly solid with necrosis / mixed solid and cystic].',['mass']),f('enhance','After contrast','On acquired contrast-enhanced images the mass has [homogeneous enhancement / heterogeneous enhancement / minimal enhancement / non-enhancing necrotic components].',['mass']),f('claw','Claw sign','An organ claw sign indicates origin from the [right kidney / left kidney / liver / spleen / pancreas].',['mass']),f('rupture','Rupture signs','There is [capsular disruption / peritumoral fluid / peritumoral haemorrhage] adjacent to the mass.',['mass']),f('extension','Local invasion','The mass [abuts without definite invasion / invades] the [liver / kidney / pancreas / diaphragm / psoas / bowel / abdominal wall].',['mass'])]
 if renal:fs += [f('rest','Additional renal foci','The remaining renal parenchyma has [no additional focus / peripheral plaque-like foci / multiple rounded foci / diffuse nephrogenic-rest-like abnormality].',['mass']),f('sinus','Renal sinus','The renal mass [spares / extends into / has indeterminate involvement of] the renal sinus.',['mass']),f('pelvis','Collecting system','The mass [compresses / protrudes into / invades / does not involve] the collecting system.',['mass'])]
 rows=[s('paediatric-mass','Abdominal mass','Lesions',None,fs,True,True),*urinary(True),organ('liver','Liver','liver',us=True),organ('spleen','Spleen','spleen',us=True),organ('pancreas','Pancreas','pancreas',us=True),organ('right-adrenal','Right adrenal','adrenal',us=True),organ('left-adrenal','Left adrenal','adrenal',us=True)]
 rows += [vessel(slug(n),n,tumour=True) for n in ['Aorta','Coeliac artery','Superior mesenteric artery','Portal vein','Right renal vein','Left renal vein','Inferior vena cava']]+nodes(['Right renal hilar','Left renal hilar','Para-aortic','Paracaval','Mesenteric'])+peritoneal()
 if not cyst:rows += [s('spinal-extension','Neural foramina and spinal canal','Paraspinal extent','No extension into the imaged neural foramina or spinal canal is identified.',[f('foramina','Foraminal extension','The mass extends through the [right / left / bilateral] [lower thoracic / lumbar / sacral] neural foramina.'),f('canal','Canal extension','The mass extends into the [epidural space without cord compression / epidural space with cord compression / epidural space with cauda equina compression].',['foramina'])],True),s('liver-sectors','Liver sector involvement','Hepatic tumour mapping',None,[f('left-lateral','Left lateral sector','The left lateral hepatic sector is [spared / involved / indeterminate].'),f('left-medial','Left medial sector','The left medial hepatic sector is [spared / involved / indeterminate].'),f('right-anterior','Right anterior sector','The right anterior hepatic sector is [spared / involved / indeterminate].'),f('right-posterior','Right posterior sector','The right posterior hepatic sector is [spared / involved / indeterminate].'),f('caudate','Caudate lobe','The caudate lobe is [spared / involved / indeterminate].')],True)]
 save(k,rows)

rows=[]
for side in ['Right','Left']:
 rows += [s(slug(side+'-testis'),side+' testis','Testes',f'The {side.lower()} testis has homogeneous echotexture and preserved contour.',[f('lie','Lie',f'The {side.lower()} testis has [a horizontal lie / a high-riding position / an inguinal position].'),f('size','Dimensions',f'The {side.lower()} testis measures __ mm × __ mm × __ mm.'),f('echo','Echotexture',f'The {side.lower()} testis is [diffusely hypoechoic / heterogeneous / focally hypoechoic].'),f('rupture','Contour disruption',f'The {side.lower()} testis has contour disruption with extrusion of parenchyma.'),f('lesion','Focal lesion',f'A [solid / cystic / avascular haemorrhagic] focal lesion is present in the {side.lower()} testis.'),measure(f'The {side.lower()} testicular lesion',['lesion'])]),s(slug(side+'-testicular-flow'),side+' testicular Doppler','Vascular assessment',None,[f('arterial','Arterial flow',f'Compared with the contralateral side, {side.lower()} intratesticular arterial flow is [symmetric / reduced / absent / increased / not technically assessable].'),f('venous','Venous flow',f'{side} intratesticular venous flow is [demonstrated / not detected / not technically assessable].'),f('waveform','Arterial waveform',f'The {side.lower()} intratesticular arterial waveform shows [preserved diastolic flow / absent diastolic flow / reversed diastolic flow].')],True),s(slug(side+'-cord'),side+' spermatic cord','Spermatic cords',f'No twisting of the visualised {side.lower()} spermatic cord is identified.',[f('whirlpool','Whirlpool',f'The {side.lower()} spermatic cord shows a whirlpool configuration.'),f('thick','Thickening',f'The {side.lower()} spermatic cord is thickened and [hyperaemic / not hyperaemic].')],True)]
 for part in ['head','body','tail']:
  rows += [s(slug(side+'-epididymis-'+part),side+' epididymal '+part,'Epididymides',f'The {side.lower()} epididymal {part} is not enlarged.',[f('enlarge','Enlargement',f'The {side.lower()} epididymal {part} is enlarged and [hypoechoic / heterogeneous].'),f('flow','Doppler flow',f'The {side.lower()} epididymal {part} shows [increased / reduced / absent detectable] Doppler flow.',['enlarge']),f('cyst','Cyst',f'A cyst is present in the {side.lower()} epididymal {part}.')])]
 rows += [s(slug(side+'-appendage'),side+' testicular appendage','Appendages',None,[f('appendage','Abnormal appendage',f'An enlarged avascular appendage is visible adjacent to the {side.lower()} superior testicular pole.'),measure(f'The {side.lower()} appendage',['appendage'])],True),s(slug(side+'-tunica'),side+' tunica vaginalis','Extratesticular tissues',f'No pathological fluid collection surrounds the {side.lower()} testis.',[f('fluid','Fluid',f'The {side.lower()} tunica vaginalis contains [simple fluid / septated fluid / echogenic blood products / complex inflammatory fluid].'),f('gas','Gas',f'Gas is present in the {side.lower()} scrotal collection.')]),s(slug(side+'-inguinal'),side+' inguinal canal','Extratesticular tissues',f'No hernia is identified in the examined {side.lower()} inguinal canal.',[f('hernia','Hernia',f'The {side.lower()} inguinal canal contains a hernia of [fat / bowel].'),f('motility','Herniated bowel',f'The herniated bowel shows [preserved peristalsis / reduced peristalsis / no observed peristalsis].',['hernia'])],True)]
rows += [s('scrotal-wall','Scrotal wall','Extratesticular tissues','The scrotal wall is not thickened.',[f('oedema','Oedema','Scrotal wall oedema is [right-sided / left-sided / bilateral].'),f('hyperaemia','Hyperaemia','The thickened scrotal wall shows [increased / absent detectable] Doppler flow.',['oedema']),f('gas','Soft tissue gas','Gas is present in the scrotal wall.')])]
save('ra.ultrasound-paediatric-scrotum',rows)

# Add primary consensus references independently of the regional teaching links.
for key, title, url in [
 ('ra.renal-cysts-bosniak','Bosniak Classification of Cystic Renal Masses, Version 2019: proposal and needs assessment','https://pmc.ncbi.nlm.nih.gov/articles/PMC6677285/'),
 ('ra.mri-rectal-cancer','ESGAR updated rectal MRI consensus 2026, Part I: primary staging','https://doi.org/10.1007/s00330-025-12274-w'),
 ('ra.ultrasound-paediatric-scrotum','AIUM Practice Parameter for Scrotal Ultrasound 2025','https://www.aium.org/docs/default-source/official-statements-or-practice-parameters/scrotal_2025.pdf'),
 ('ra.ovarian-cysts','ACR O-RADS resources and assessment categories','https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/O-RADS')]:
 sid=source({'title':title,'url':url})
 for row in OUT['investigations'][key]['sections']:row['source_ids']=list(dict.fromkeys([*row['source_ids'],sid]))

# Acute gynaecological ultrasound does not expose MRI-only characterization choices.
for row in OUT['investigations']['ra.ultrasound-acute-gynaecology']['sections']:
 if row['id']=='adnexal-lesion':
  row['findings']=[x for x in row['findings'] if x['id'] not in {'t1','t2','enhance','orads-mri','orads-us'}]
# A covered ureter does not imply evaluation of the whole upstream renal tract.
# Final content safeguards and validation follow below.
# Peer review: separate invasion from abutment, and scope pelvic/paediatric observations.
for inv in OUT['investigations'].values():
 for row in inv['sections']:
  depth=next((x for x in row['findings'] if x['id']=='depth' and x.get('requires_any')==['contact']),None)
  if depth:
   contact=next(x for x in row['findings'] if x['id']=='contact')
   contact['text']=contact['text'].replace('[abuts with a preserved interface / abuts with an indeterminate interface / directly invades]','[abuts with a preserved interface / abuts with an indeterminate interface]')
   contact['exclusive_group']='tumour-relationship'
   row['findings'].insert(1,f('invades','Definite invasion',f"Tumour directly invades the {row['label'].lower()}.",ex='tumour-relationship'))
   depth['requires_any']=['invades']
for row in OUT['investigations']['ra.mri-prostate']['sections']:
 if row['id']=='prostate-dimensions':
  row['findings'].append(f('psa','Reviewed PSA','The supplied and reviewed serum PSA is __ ng/mL.'))
fistula=OUT['investigations']['ra.mri-perianal-fistula']
for row in fistula['sections']:
 if row['id']=='fistula':
  parent=next(x for x in row['findings'] if x['id']=='tract')
  parent['text']='A perianal fistula has a [intersphincteric / suprasphincteric / extrasphincteric / superficial subcutaneous] course.'
  parent['exclusive_group']='primary-course'
  row['findings'].insert(1,f('transsphincteric','Transsphincteric tract','A perianal fistula has a transsphincteric course.',ex='primary-course'))
  for finding in row['findings']:
   if finding.get('requires_any')==['tract']:finding['requires_any']=['tract','transsphincteric']
   if finding['id']=='sphincter-level':finding['requires_any']=['transsphincteric']
   if finding['id'] in ['tract','transsphincteric','branch','sphincter-level']:
    finding['invalidates_normal']=['internal-anal-sphincter','external-anal-sphincter','intersphincteric-space','right-ischioanal-fossa','left-ischioanal-fossa','supralevator-compartment','levator-plate']
for key in ['ra.mri-bladder','ra.mri-cervical-cancer','ra.mri-endometrial-cancer']:
 inv=OUT['investigations'][key]
 inv['sections']=[row for row in inv['sections'] if row['id']!='free-gas']
 for row in inv['sections']:
  if row['id'] in ['right-kidney','left-kidney','right-collecting-system','left-collecting-system']:
   row['exclude_from_bulk_normal']=True
  if row['id']=='free-fluid':
   row['normal']='No free pelvic fluid is identified.'
   for finding in row['findings']:finding['text']=finding['text'].replace('[pelvis / right upper quadrant / left upper quadrant / paracolic gutters / abdomen and pelvis]','pelvis')
for row in OUT['investigations']['ra.mri-endometriosis']['sections']:
 if row['id'] in ['caecum','appendix','anterior-abdominal-wall-scar']:row['exclude_from_bulk_normal']=True
 for finding in row['findings']:finding['text']=finding['text'].replace('echogenic debris','proteinaceous debris')
for key in ['ra.neonatal-acute-abdomen','ra.necrotising-enterocolitis']:
 for row in OUT['investigations'][key]['sections']:
  if row['id'] in ['stomach','rectum']:row['findings']=[x for x in row['findings'] if x['id']!='persistent']

# Peer review: avoid occult-stone exclusion and incompatible category/depth choices.
for inv in OUT['investigations'].values():
 if inv['modality']!='Ultrasound':
  for row in inv['sections']:
   if row['id']=='gallbladder-lumen':row['normal']='No visible intraluminal gallbladder abnormality is identified on the acquired images.'
for row in OUT['investigations']['ra.mri-rectal-cancer']['sections']:
 if row['id']=='primary-tumour':
  old=next(x for x in row['findings'] if x['id']=='wall')
  old.update(id='wall-confined',label='Confined to bowel wall',text='The tumour is confined to the bowel wall.',exclusive_group='mural-depth')
  row['findings'] += [f('extramural','Extramural extension','The tumour extends beyond the muscularis propria.',['tumour'],ex='mural-depth'),f('peritoneal-invasion','Peritoneal invasion','The tumour invades the peritoneal surface.',['tumour'],ex='mural-depth'),f('adjacent-invasion','Adjacent structure invasion','The tumour directly invades an adjacent structure.',['tumour'],ex='mural-depth')]
  next(x for x in row['findings'] if x['id']=='extramural-depth')['requires_any']=['extramural']
for row in OUT['investigations']['ra.liver-lirads']['sections']:
 if row['id']=='hepatic-observation':
  row['findings']=[x for x in row['findings'] if x['id']!='eligibility']
  row['findings'] += [f('eligible','Eligible untreated observation','This untreated observation is in an adult meeting LI-RADS at-risk criteria.',['lesion'],ex='lirads-applicability'),f('not-at-risk','Not in at-risk population','LI-RADS diagnostic categorisation is not applicable because the patient does not meet the defined at-risk criteria.',['lesion'],ex='lirads-applicability'),f('treated','Previously treated observation','The observation has undergone treatment; untreated-observation LI-RADS categorisation is not applicable.',['lesion'],ex='lirads-applicability')]
  next(x for x in row['findings'] if x['id']=='lirads')['requires_any']=['eligible']

# Multimodality and conditional findings do not silently attest to an unperformed sequence.
for key, inv in OUT['investigations'].items():
 by={row['id']:row for row in inv['sections']}
 for row in inv['sections']:
  if inv['modality']=='CT':
   row['findings']=[x for x in row['findings'] if not re.search(r'Doppler|sonographic|On graded compression|real-time assessment',x['text'])]
  # Never include non-observed genital organs automatically in a normal batch.
  if row['id'] in {'uterus','vagina','vaginal-wall','prostate','seminal-vesicles','prostate-stroma','right-ovary','left-ovary','right-adrenal','left-adrenal'} and inv['guide_id'] in {'rad.5.anal-cancer','rad.5.rectal-mr','rad.5.bladder-virads','rad.5.uterine-mr'}:
   row['exclude_from_bulk_normal']=True
  for item in row['findings']:
   # Enumerate scores rather than suggesting a classifier from morphology alone.
   result=compile_statement(item['text'],kind='finding',label=item['label'],source={})
   bad=[slot for slot in result['slots'] if slot['kind']=='context']
   if bad:raise ValueError((key,row['id'],item['id'],bad))
   overrides=item.setdefault('slot_overrides',{})
   for slot in result['slots']:
    if slot['kind']=='number':
     unit=slot.get('unit','')
     limit={'minimum':-1024 if unit=='HU' else 0}
     if unit in ['degrees','°']:limit['maximum']=360
     if unit in ['o’clock',"o'clock"]:limit={'minimum':1,'maximum':12,'step':1}
     overrides.setdefault(slot['id'],limit)
   if not overrides:item.pop('slot_overrides',None)
  if row['normal']:
   parsed=compile_statement(row['normal'],kind='normal',label='Normal',source={})
   assert not parsed['slots'],(key,row['id'],'normal has slots')
 # An observation in a separate repeatable block invalidates broad organ-normal assertions.
 links={'renal-lesion':['right-kidney','left-kidney'],'pancreatic-lesion':['pancreas-head','pancreas-uncinate-process','pancreas-neck','pancreas-body','pancreas-tail'],'bladder-lesion':['bladder'],'adnexal-lesion':['right-ovary','left-ovary'],'endometrioma':['right-ovary','left-ovary'],'paediatric-mass':['right-kidney','left-kidney','liver','spleen','pancreas','right-adrenal','left-adrenal']}
 for block,targets in links.items():
  if block in by:
   parent=next(x for x in by[block]['findings'] if x['id'] in ['lesion','mass'])
   parent['invalidates_normal']=list(dict.fromkeys(parent.get('invalidates_normal',[])+[t for t in targets if t in by]))
 # Post-cholecystectomy conflicts with all gallbladder normal/positive morphology.
 if 'gallbladder-lumen' in by:
  absent=next(x for x in by['gallbladder-lumen']['findings'] if x['id']=='absent')
  absent['invalidates_normal']=[x for x in ['gallbladder-wall','pericholecystic'] if x in by]
 # Endometriotic lumen descriptors belong only to actual luminal organs.
 if key=='ra.mri-endometriosis':
  for row in inv['sections']:
   if row['id'] not in ['bladder-dome','right-distal-ureter','left-distal-ureter','anterior-rectal-wall','rectosigmoid','sigmoid-colon','caecum','appendix']:
    row['findings']=[x for x in row['findings'] if x['id']!='lumen']
 # Generic transvaginal exploration does not evaluate upper renal anatomy.
 if key=='ra.transvaginal-nongynaecology':
  inv['sections']=[x for x in inv['sections'] if 'collecting-system' not in x['id']]
  for row in inv['sections']:
   if row['id'] in ['right-ureter','left-ureter']:
    for item in row['findings']:
     item['text']=item['text'].replace('[proximal ureter / mid ureter / distal ureter / ureterovesical junction]','[distal ureter / ureterovesical junction]')
 # MRI-only endometrioma data must not be hidden behind US-only choices; they remain separately named.
 ids=[x['id'] for x in inv['sections']]
 assert len(ids)==len(set(ids)),(key,'duplicate anatomy')
 for row in inv['sections']:
  fids=[x['id'] for x in row['findings']]
  assert len(fids)==len(set(fids)),(key,row['id'],'duplicate finding',fids)
  for item in row['findings']:
   assert set(item.get('requires_any',[]))<=set(fids),(key,row['id'],item['id'],'dependency')
   assert set(item.get('invalidates_normal',[]))<=set(ids),(key,row['id'],item['id'],'normal link')
   assert item['id'] not in item.get('requires_any',[])
 OUT['coverage'].append({'investigation_id':key,'expected_anatomy_ids':ids})
assert set(OUT['investigations'])=={a['investigation_id'] for a in ASSIGN}
OUT['sources']=list(SOURCE.values())
(ROOT/'data/radiology/anatomic-body.json').write_text(json.dumps(OUT,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'investigations':len(OUT['investigations']),'rows':sum(len(x['sections']) for x in OUT['investigations'].values()),'findings':sum(len(s['findings']) for x in OUT['investigations'].values() for s in x['sections']),'repeatable':sum(bool(s.get('repeatable')) for x in OUT['investigations'].values() for s in x['sections'])}))
