"""One standard for every report template: self-contained lines, uniform conclusions and spelling.

Rules applied here to data/radiology/report-templates/*.json (tests/test_report_style.py enforces them):

Conclusion
  A study without a stated indication concludes "Normal <study title>." ("Normal MRI lumbar spine.",
  "Normal ultrasound knee.", "Normal ankle radiographs."), as the practice's own normals do.
  A study with an indication, protocol or classification concludes with what it excludes
  ("No appendicitis."), with the category in brackets where there is one ("(BI-RADS 1)").
  A conclusion never names an organ as normal in place of the study ("Normal pituitary gland.").

Findings
  Every normal sentence names its subject, so it reads on its own when the report is flat
  ("Normal liver size and echotexture.", not "Normal size and echotexture." under Liver).
  Adjective first ("Central trachea.", "Intact leads.").
  Nothing is said twice in one report.

Headings
  One name for one thing: Bones, Fracture, Vertebrae, LI-RADS category.

Spelling
  Baker's cyst, radiopaque, run-off, bone abnormality (not bony), fat-sat, DWI with ADC.
  Procedures record "Informed consent obtained."

Usage: python3 tools/authoring/report_uniformity_20261117.py   (idempotent)
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / 'data' / 'radiology' / 'report-templates'

# Applied to every string in every template file.
SPELLING = [
    ('Baker cyst', "Baker's cyst"),
    ('radio-opaque', 'radiopaque'),
    ('runoff', 'run-off'),
    ('bony abnormality', 'bone abnormality'),
    ('fat-suppressed', 'fat-sat'),
    ('"Informed consent. ', '"Informed consent obtained. '),
]

# identifier -> [(old text, new text)] inside that template's block.
TEXT = {
    'us.abdomen': [('"Normal size and echotexture.', '"Normal liver size and echotexture.')],
    'ra.ultrasound-gallbladder': [('"Normal wall thickness.', '"Normal gallbladder wall thickness.')],
    'ra.ultrasound-ibd': [('"Normal wall thickness and stratification.', '"Normal terminal ileal wall thickness and stratification.')],
    'fl.contrast-enema': [('Normal calibre and mucosa.', 'Normal colonic calibre and mucosa.')],
    'us.venous-duplex-lower-limb': [('"Fully compressible with normal spontaneous, phasic flow.',
                                     '"Fully compressible common femoral, femoral and popliteal veins with normal spontaneous, phasic flow.')],
    'ct.urography': [('"Normal opacification.', '"Normal opacification of the collecting systems and ureters.')],
    'us.scrotum-adult': [('"Normal size and echotexture.', '"Normal testicular size and echotexture.')],
    'ra.mri-sella': [('"Normal size, signal and enhancement.', '"Normal pituitary size, signal and enhancement.')],
    'ra.ultrasound-thyroid': [('"Normal size and echotexture.', '"Normal thyroid size and echotexture.')],
    'mri.cervical-spine-trauma': [('"Normal, including the craniocervical', '"Normal alignment, including the craniocervical')],
    'ra.cervical-spine-injury': [('"Normal, including the craniocervical', '"Normal alignment, including the craniocervical')],
    'msk.ultrasound-nerves-upper-limb': [('"Normal calibre and echotexture at the carpal tunnel and forearm.',
                                          '"Normal median nerve calibre and echotexture at the carpal tunnel and forearm.')],
    'ra.ultrasound-shoulder': [('"Normal tendon in the bicipital groove.', '"Normal long head of biceps tendon in the bicipital groove.')],
    'ra.cardiovascular-devices': [('Leads intact.', 'Intact leads.')],
    'ra.chest-radiography': [('"Trachea central.', '"Central trachea.')],
    'mri.female-pelvis': [('Junctional zone not thickened.', 'Normal junctional zone.')],
    'ra.mri-dementia': [('Hippocampal volumes normal for age.', 'Normal hippocampal volumes for age.')],
    'ra.ultrasound-ddh': [('Graf type I: alpha angle 60 degrees or more with good bony coverage. Stable.',
                           'Stable Graf type I hip, with an alpha angle of 60 degrees or more and good bony coverage.')],
    'mri.thymus': [('Clear visualised lungs. Normal heart and great vessels. No pleural effusion.',
                    'Clear visualised lungs. Normal heart and great vessels.')],
    'mri.paediatric-mediastinum': [('Clear visualised lungs. Normal heart and great vessels. No pleural effusion.',
                                    'Normal heart and great vessels.')],
    'fl.retrograde-pyelogram': [('Non-dilated pelvicalyceal system. No filling defect.',
                                 'Non-dilated pelvicalyceal system without filling defect.')],
    'xr.sacrum-coccyx': [('Normal coccygeal alignment. No fracture.', 'Normal coccygeal alignment. No coccygeal fracture.')],
    'ra.foot-ankle-cases': [('"No fracture. Normal Lisfranc alignment.', '"No midfoot or forefoot fracture. Normal Lisfranc alignment.')],
    'ra.mri-neck-spaces': [('"Normal parapharyngeal, masticator,', '"Normal suprahyoid parapharyngeal, masticator,'),
                           ('"Normal visceral, carotid,', '"Normal infrahyoid visceral, carotid,')],
    'ra.mri-crohn': [('Oral contrast distension and antiperistaltic agent;', 'Oral contrast and antiperistaltic agent;')],
    'ra.acute-abdomen': [('No aggressive bone lesion.', 'No destructive bone lesion.')],
    'ct.pelvis': [('No suspicious bone lesion.', 'No destructive bone lesion.')],
    'fl.lumbar-puncture': [('"title": "Lumbar puncture, fluoroscopy-guided"', '"title": "Fluoroscopy-guided lumbar puncture"')],
    'ct.appendix': [('      "sections": [\n        {"heading": "Periappendiceal region"',
                     '      "sections": [\n'
                     '        {"heading": "Appendix", "normal": "Normal appendix, under 6 mm in diameter.",\n'
                     '         "options": ["Dilated appendix, [ ] mm diameter, [with / without] appendicolith.",\n'
                     '                     "Appendix not visualised."]},\n'
                     '        {"heading": "Periappendiceal region"'),
                    ('         "options": ["[Mesenteric adenitis / Terminal ileitis / Ovarian cyst / Ureteric calculus] [ ]."]}\n      ],',
                     '         "options": ["[Mesenteric adenitis / Terminal ileitis / Ovarian cyst / Ureteric calculus] [ ]."]},\n'
                     '        {"heading": "Other organs, lung bases and bones", "normal": "Normal liver, spleen, pancreas, adrenals, kidneys and pelvic organs. Clear lung bases. No destructive bone lesion.",\n'
                     '         "options": ["[ ]."]}\n      ],')],
}

# identifier -> (old heading, new heading).
HEADINGS = {
    'mri.cervical-spine-trauma': ('Fractures', 'Fracture'),
    'ra.cervical-spine-injury': ('Fractures', 'Fracture'),
    'ra.child-abuse-imaging': ('Fractures', 'Fracture'),
    'xr.stress-injury': ('Bone', 'Bones'),
    'ct.femur': ('Bone', 'Bones'),
    'xr.sinuses': ('Bone', 'Bones'),
    'ra.mri-muscle-injury': ('Bone', 'Bones'),
    'ra.stress-fractures': ('Bone', 'Bones'),
    'mri.thoracolumbar-trauma': ('Vertebral bodies', 'Vertebrae'),
    'ra.thoracolumbar-fractures': ('Vertebral bodies', 'Vertebrae'),
    'ra.thoracolumbar-injury': ('Vertebral bodies', 'Vertebrae'),
    'ra.ultrasound-neonatal-brain': ('Germinal matrix and ventricles', 'Haemorrhage'),
    'liver.lirads-calculated': ('Category', 'LI-RADS category'),
    'ct.liver-lirads-calculated': ('Category', 'LI-RADS category'),
}

# CT cannot assess mucosal pattern or peristalsis: this study looks for a leak.
SECTIONS = {
    'ct.oesophagus': '''      "sections": [
        {"heading": "Oesophagus", "normal": "Normal calibre oesophagus. No wall thickening or mass.",
         "options": ["[Circumferential / Eccentric] wall thickening at [ ] cm, over [ ] mm.",
                     "[Dilatation / Hiatus hernia / Diverticulum] [ ]."]},
        {"heading": "Leak", "normal": "No contrast leak or extraluminal gas.",
         "options": ["Contrast leak at [ ] [ ].",
                     "[Pneumomediastinum / Extraluminal gas] [ ]."]},
        {"heading": "Mediastinum and pleura", "normal": "No mediastinal collection. No pleural effusion.",
         "options": ["[Mediastinal collection / Mediastinal fat stranding] [ ], [ ] mm.",
                     "[Right / Left / Bilateral] pleural effusion [ ]."]},
        {"heading": "Lungs", "normal": "Clear.",
         "options": ["[Consolidation / Aspiration change / Collapse] in the [ ]."]}
      ],''',
}

IMPRESSION = {
    # Radiographs of one region: the practice's "Normal <region> radiographs."
    'xr.ankle': 'Normal ankle radiographs.',
    'ra.foot-ankle-cases': 'Normal foot and ankle radiographs.',
    'xr.tibia-fibula': 'Normal tibia and fibula radiographs.',
    'xr.foot': 'Normal foot radiographs.',
    'xr.toe': 'Normal toe radiographs.',
    'xr.calcaneus': 'Normal calcaneus radiographs.',
    'xr.pelvis': 'Normal pelvis radiograph.',
    'xr.hip': 'Normal hip radiographs.',
    'xr.femur': 'Normal femur radiographs.',
    'xr.clavicle': 'Normal clavicle radiographs.',
    'xr.humerus': 'Normal humerus radiographs.',
    'xr.forearm': 'Normal forearm radiographs.',
    'xr.wrist': 'Normal wrist radiographs.',
    'xr.finger': 'Normal finger radiographs.',
    'xr.sacrum-coccyx': 'Normal sacrum and coccyx radiographs.',
    'xr.facial-bones': 'Normal facial bones radiographs.',
    'xr.mandible': 'Normal mandible radiographs.',
    'xr.sternum': 'Normal sternum radiographs.',
    'xr.scapula': 'Normal scapula radiographs.',
    'xr.sesamoid': 'Normal sesamoid radiographs.',
    'xr.sternoclavicular': 'Normal sternoclavicular joint radiographs.',
    'xr.tmj': 'Normal temporomandibular joint radiographs.',
    'xr.sacroiliac': 'Normal sacroiliac joint radiographs.',
    'xr.ac-joints': 'Normal acromioclavicular joint radiographs.',
    'xr.sinuses': 'Normal paranasal sinus radiograph.',
    'xr.cephalogram': 'Normal lateral cephalometric radiograph.',
    'xr.standing-feet': 'Normal weight-bearing foot radiographs.',
    'xr.standing-knees': 'Normal weight-bearing knee radiographs.',
    'ra.paediatric-hip': 'Normal pelvis and hip radiographs.',
    # Studies without an indication: "Normal <study>."
    'ra.acute-abdomen': 'Normal CT abdomen and pelvis.',
    'ct.abdomen-multiphase': 'Normal CT abdomen and pelvis.',
    'ra.ct-mediastinum': 'Normal CT chest.',
    'ra.transvaginal-nongynaecology': 'Normal transvaginal ultrasound pelvis.',
    'ra.ultrasound-bile-duct-stones': 'Normal ultrasound liver and biliary tree.',
    'ra.ultrasound-gallbladder': 'Normal ultrasound gallbladder.',
    'ra.ultrasound-gi-tract': 'Normal ultrasound bowel.',
    'ra.biliary-duct-pathology': 'Normal MRCP.',
    'ra.esophagus': 'Normal barium swallow.',
    'ra.dynamic-rectal-examination': 'Normal fluoroscopic defecography.',
    'fl.cystogram': 'Normal cystogram.',
    'mri.thymus': 'Normal MRI thymus.',
    'mri.adrenals': 'Normal MRI adrenals.',
    'mri.orbits': 'Normal MRI orbits.',
    'ra.ct-mri-eye': 'Normal CT orbits.',
    'ct.sinuses': 'Normal CT paranasal sinuses.',
    'ra.mri-sinuses': 'Normal MRI paranasal sinuses.',
    'ct.angiogram-brain': 'Normal CT angiogram brain.',
    'ct.angiogram-upper-limb': 'Normal CT angiogram upper limb.',
    'mri.angiogram-brain': 'Normal MR angiogram brain.',
    'ct.tmj': 'Normal CT temporomandibular joints.',
    'mri.both-hips': 'Normal MRI both hips.',
    'cardiology.percutaneous-angiography': 'Normal coronary angiogram.',
    'ra.thoracic-aorta-measurement': 'Normal CT angiogram thoracic aorta.',
    'template:nuclear-general-report': 'Normal nuclear medicine study.',
    'us.renal-bladder': 'Normal ultrasound kidneys and bladder.',
    'us.scrotum-adult': 'Normal ultrasound scrotum.',
    'ra.ultrasound-acute-gynaecology': 'Normal ultrasound pelvis.',
    'msk.ultrasound-ankle': 'Normal ultrasound ankle.',
    'msk.ultrasound-foot': 'Normal ultrasound foot.',
    'msk.ultrasound-hip': 'Normal ultrasound hip.',
    'msk.ultrasound-knee': 'Normal ultrasound knee.',
    'ra.ultrasound-shoulder': 'Normal ultrasound shoulder.',
    'msk.ultrasound-elbow': 'Normal ultrasound elbow.',
    'msk.ultrasound-wrist': 'Normal ultrasound wrist.',
    'msk.ultrasound-hand': 'Normal ultrasound hand.',
    'ra.mri-sella': 'Normal MRI pituitary.',
    'ra.ct-temporal-bone': 'Normal CT temporal bones.',
    'ra.ultrasound-thyroid': 'Normal ultrasound thyroid.',
    'ra.mri-lumbar-disc': 'Normal MRI lumbar spine.',
    'neuro.mri-spine-cervical': 'Normal MRI cervical spine.',
    'neuro.mri-spine-thoracic': 'Normal MRI thoracic spine.',
    # Studies with an indication: what they exclude, with the category where there is one.
    'ra.appendicitis': 'No appendicitis.',
    'ct.appendix': 'No appendicitis.',
    'ct.oesophagus': 'No oesophageal perforation or leak.',
    'ra.mri-cardiomyopathy': 'No MRI evidence of cardiomyopathy.',
    'ra.mri-muscle-disease': 'No MRI evidence of myopathy.',
    'ra.ultrasound-paediatric-scrotum': 'No testicular torsion.',
    'us.male-breast': 'No suspicious breast abnormality (BI-RADS 1).',
    'ra.male-breast': 'No suspicious breast abnormality (BI-RADS 1).',
}


def block(text, identifier):
    start = text.index(f'    "{identifier}": {{\n')
    following = re.compile(r'^    "[^"\n]+": \{$', re.M).search(text, start + 1)
    return start, following.start() if following else len(text)


def apply():
    changed = 0
    owners = {}
    for path in sorted(LIBRARY.glob('*.json')):
        for identifier in json.loads(path.read_text(encoding='utf-8'))['templates']:
            owners[identifier] = path
    texts = {path: path.read_text(encoding='utf-8') for path in set(owners.values())}

    def edit(identifier, transform):
        path = owners[identifier]
        text = texts[path]
        start, end = block(text, identifier)
        texts[path] = text[:start] + transform(text[start:end]) + text[end:]

    def swap(old, new):
        def transform(body):
            if old in body:
                return body.replace(old, new)
            if new not in body:
                raise SystemExit(f'cannot place {old!r}')
            return body
        return transform

    for path, text in texts.items():
        for old, new in SPELLING:
            text = text.replace(old, new)
        # DWI names its ADC map in every MRI protocol.
        text = re.sub(r'("technique": \{"normal": "[^"]*?)\bDWI(?! with ADC| neurography)', r'\1DWI with ADC', text)
        texts[path] = text
    for identifier, pairs in TEXT.items():
        for old, new in pairs:
            edit(identifier, swap(old, new))
    for identifier, (old, new) in HEADINGS.items():
        edit(identifier, swap(f'{{"heading": "{old}",', f'{{"heading": "{new}",'))
    for identifier, sections in SECTIONS.items():
        edit(identifier, lambda body: re.sub(r'      "sections": \[\n.*?\n      \],', lambda _: sections, body, flags=re.S))
    for identifier, impression in IMPRESSION.items():
        edit(identifier, lambda body: re.sub(r'"impression": (?:"[^"]*"|\[[^\]]*\])',
                                             lambda _: '"impression": ' + json.dumps(impression, ensure_ascii=False), body))
    for path, text in texts.items():
        json.loads(text)
        if text != path.read_text(encoding='utf-8'):
            path.write_text(text, encoding='utf-8')
            changed += 1
    return changed


if __name__ == '__main__':
    print(apply(), 'files changed')
