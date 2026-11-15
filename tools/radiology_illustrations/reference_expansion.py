"""Original anatomy/reporting diagrams for the Radiology Assistant coverage gaps.

These geometric schematics explain relationships; they are not patient images.
Each scene has its own anatomy and accessible teaching description.
"""
from .core import INK, INK_SOFT, BLUE, BLUE_LIGHT, TEAL, CORAL, CORAL_LIGHT, GOLD, PAPER_LIGHT


def _label(p, xy, text):
    p.text(xy, text, size=25, bold=True, fill=INK)


def _layout(p, item, subtitle):
    p.draw.rounded_rectangle((120, 210, 825, 830), 24, fill=PAPER_LIGHT, outline=BLUE, width=2)
    p.text((145, 225), 'ANATOMY SCHEMATIC', size=22, bold=True, fill=INK_SOFT)
    p.wrapped_text((145, 750, 800, 825), subtitle, size=23, fill=INK_SOFT, line_gap=5)
    for i, entry in enumerate(item['items']):
        y = 225 + i * 205
        p.text((880, y), entry['label'], size=29, bold=True, fill=INK)
        p.wrapped_text((880, y + 38, 1450, y + 165), entry['detail'], size=26, fill=INK_SOFT, line_gap=6)


def _esophagus(p, item):
    _layout(p, item, 'Separate the swallowing event from the structural narrowing.')
    p.draw.line([(350, 330), (420, 390), (435, 680)], fill=BLUE, width=35)
    p.draw.line([(455, 390), (530, 480), (590, 680)], fill=TEAL, width=24)
    p.arrow((350, 310), (402, 366), fill=CORAL, width=9)
    p.draw.ellipse((407, 550, 463, 610), fill=CORAL_LIGHT, outline=CORAL, width=4)
    _label(p, (165, 390), 'bolus')
    _label(p, (535, 500), 'airway')
    _label(p, (180, 655), 'esophagus')
    p.arrow((275, 590), (405, 580), fill=CORAL, width=4)
    _label(p, (150, 540), 'narrowing')


def _anal(p, item):
    _layout(p, item, 'Map the primary, sphincters and regional nodal territories.')
    p.draw.rounded_rectangle((340, 355, 590, 680), 90, fill=BLUE_LIGHT, outline=BLUE, width=5)
    p.draw.rounded_rectangle((385, 335, 545, 690), 65, fill=PAPER_LIGHT, outline=TEAL, width=8)
    p.draw.ellipse((495, 520, 580, 610), fill=CORAL_LIGHT, outline=CORAL, width=5)
    for x in (210, 680):
        p.draw.ellipse((x, 590, x+36, 625), fill=CORAL_LIGHT, outline=CORAL, width=3)
    _label(p, (330, 290), 'rectum → canal')
    _label(p, (165, 685), 'inguinal nodes')
    p.arrow((650, 485), (570, 548), fill=CORAL, width=4)
    _label(p, (615, 425), 'tumour')


def _gi(p, item):
    _layout(p, item, 'Locate the lesion or object, then inspect the nearby bowel wall.')
    points = [(210,390),(650,390),(690,445),(240,465),(200,520),(650,540),(670,595),(260,635)]
    p.draw.line(points, fill=BLUE, width=54, joint='curve')
    p.draw.line(points, fill=BLUE_LIGHT, width=39, joint='curve')
    p.draw.ellipse((505, 367, 572, 423), fill=CORAL_LIGHT, outline=CORAL, width=4)
    p.draw.line((385, 500, 440, 555), fill=CORAL, width=9)
    _label(p, (190, 300), 'bowel lumen')
    p.arrow((640, 310), (555, 367), fill=CORAL, width=4)
    _label(p, (585, 270), 'mass')
    _label(p, (245, 675), 'sharp object / wall relationship')


def _pelvic(p, item):
    _layout(p, item, 'Compare rest with strain and evacuation using the same landmarks.')
    p.draw.line((190, 610, 750, 610), fill=INK_SOFT, width=4)
    for x, colour in [(270,BLUE),(455,TEAL),(630,CORAL)]:
        p.draw.ellipse((x-55,395,x+55,490), outline=colour, width=6)
        p.draw.ellipse((x-55,570,x+55,665), outline=colour, width=6)
        p.arrow((x,505),(x,560),fill=colour,width=6)
    _label(p,(190,320),'anterior')
    _label(p,(405,320),'middle')
    _label(p,(590,320),'posterior')
    _label(p,(205,695),'shared reference line')


def _breast(p,item):
    _layout(p,item,'Shell integrity and a breast tissue abnormality are separate questions.')
    p.draw.arc((180,310,730,690),180,360,fill=BLUE,width=7)
    p.draw.ellipse((250,370,620,655),fill=BLUE_LIGHT,outline=BLUE,width=5)
    p.draw.ellipse((290,405,580,620),outline=TEAL,width=5)
    p.draw.line([(355,580),(410,435),(440,560),(490,470),(520,580)],fill=CORAL,width=5)
    _label(p,(270,270),'implant shell')
    _label(p,(220,690),'folds require sequence correlation')


def _tinnitus(p,item):
    _layout(p,item,'Trace both arterial and venous pathways next to the temporal bone.')
    p.draw.ellipse((315,370,545,590),outline=INK_SOFT,width=7)
    p.draw.arc((355,405,505,550),20,335,fill=INK_SOFT,width=7)
    p.draw.line([(260,665),(275,480),(290,325)],fill=CORAL,width=15)
    p.draw.line([(610,325),(600,485),(575,650)],fill=BLUE,width=18)
    p.draw.ellipse((560,505,630,570),outline=BLUE,width=6)
    _label(p,(155,280),'arterial')
    _label(p,(570,280),'venous')
    _label(p,(270,695),'temporal bone relationships')


def _trigeminal(p,item):
    _layout(p,item,'Contact becomes more informative when the nerve changes shape.')
    p.draw.rounded_rectangle((175,350,345,660),55,fill=BLUE_LIGHT,outline=BLUE,width=5)
    p.draw.line([(335,490),(455,475),(545,490),(685,490)],fill=GOLD,width=16)
    p.draw.line([(430,345),(485,430),(490,520),(555,650)],fill=CORAL,width=11)
    p.draw.ellipse((465,452,517,516),outline=INK,width=3)
    _label(p,(160,285),'brainstem')
    _label(p,(565,535),'nerve')
    _label(p,(535,350),'vessel')
    _label(p,(190,695),'root → cistern → Meckel cave')


def _sella(p,item):
    _layout(p,item,'Measure the lesion and identify the optic and cavernous relationships.')
    p.draw.arc((290,400,650,690),0,180,fill=INK_SOFT,width=8)
    p.draw.ellipse((350,475,580,645),fill=BLUE_LIGHT,outline=BLUE,width=5)
    p.draw.line((465,365,465,475),fill=TEAL,width=12)
    p.draw.line((300,350,630,350),fill=CORAL,width=14)
    for x in (255,650):
        p.draw.ellipse((x,495,x+48,570),fill=CORAL_LIGHT,outline=CORAL,width=4)
    _label(p,(305,285),'optic chiasm')
    _label(p,(500,400),'stalk')
    _label(p,(405,550),'pituitary')
    _label(p,(180,715),'cavernous carotids on either side')


def _elbow(p,item):
    _layout(p,item,'Localise the tendon, ligament, osteochondral or nerve abnormality.')
    p.draw.rounded_rectangle((370,310,530,510),25,fill=BLUE_LIGHT,outline=BLUE,width=5)
    p.draw.ellipse((345,440,555,580),fill=BLUE_LIGHT,outline=BLUE,width=5)
    p.draw.rounded_rectangle((390,580,510,720),20,fill=BLUE_LIGHT,outline=BLUE,width=5)
    p.draw.rounded_rectangle((570,545,650,720),20,fill=BLUE_LIGHT,outline=BLUE,width=5)
    p.draw.line([(335,415),(315,555),(370,650)],fill=TEAL,width=10)
    p.draw.line([(575,440),(640,505),(680,650)],fill=CORAL,width=10)
    _label(p,(165,420),'ligament')
    _label(p,(645,380),'nerve')
    _label(p,(350,275),'joint surface')


def _neonatal(p,item):
    _layout(p,item,'Show the counting landmarks before labelling the conus level.')
    for i in range(5):
        y=320+i*74
        p.draw.rounded_rectangle((245,y,365,y+54),8,fill=BLUE_LIGHT,outline=BLUE,width=4)
        _label(p,(170,y+8),str(i+1))
    p.draw.polygon([(450,310),(510,310),(510,490),(480,560),(450,490)],fill=CORAL_LIGHT,outline=CORAL)
    p.draw.line((480,555,480,710),fill=TEAL,width=6)
    p.arrow((650,540),(510,550),fill=CORAL,width=4)
    _label(p,(625,480),'conus')
    _label(p,(525,665),'filum')
    _label(p,(150,275),'counted landmarks')


def _bowel_us(p,item):
    _layout(p,item,'Resolve wall layers and measure perpendicular to a distended segment.')
    for radius,colour in [(170,BLUE),(140,PAPER_LIGHT),(112,TEAL),(90,PAPER_LIGHT),(65,BLUE_LIGHT)]:
        p.draw.ellipse((450-radius,515-radius,450+radius,515+radius),fill=colour)
    p.draw.line((515,510,620,510),fill=CORAL,width=5)
    p.draw.line((515,490,515,530),fill=CORAL,width=4)
    p.draw.line((620,490,620,530),fill=CORAL,width=4)
    _label(p,(355,480),'lumen')
    _label(p,(590,430),'wall')
    _label(p,(200,705),'distension + layers + Doppler')


def _skull(p,item):
    _layout(p,item,'Inspect individual sutures as well as the overall skull shape.')
    p.draw.ellipse((265,310,650,675),fill=BLUE_LIGHT,outline=BLUE,width=6)
    p.draw.line((455,320,455,660),fill=PAPER_LIGHT,width=12)
    p.draw.line([(300,430),(455,410),(610,430)],fill=PAPER_LIGHT,width=12)
    p.draw.line((455,485,455,615),fill=CORAL,width=14)
    for y in range(492,615,25):
        p.draw.line((435,y,475,y+15),fill=CORAL,width=4)
    _label(p,(185,270),'superior view')
    p.arrow((700,550),(485,550),fill=CORAL,width=4)
    _label(p,(635,470),'fusion')
    _label(p,(165,700),'patent gaps shown schematically')


DATA = [
('esophagus-swallowing','Esophagus & Swallowing','head-neck',_esophagus, [('Function','Record bolus consistency, airway entry, clearance and the phase of swallowing.'),('Structure','Describe the site, length and contour of a stricture or mucosal lesion.'),('Complication','Look for aspiration, obstruction and leak using the appropriate examination.')]),
('anal-cancer','Anal Cancer: Local Extent','abdomen',_anal,[('Primary','Locate the tumour and measure its extent in orthogonal planes.'),('Sphincters','Map the sphincter complex and any adjacent organ invasion.'),('Regional nodes','Include pelvic and inguinal territories; use the anal cancer nodal map.')]),
('gi-tumours-foreign-bodies','Bowel Lesions & Foreign Bodies','abdomen',_gi,[('Localise','Identify the bowel segment and the intraluminal or mural position.'),('Characterise','Separate an object from a mass; describe wall and mesenteric relationships.'),('Complications','Assess obstruction, local inflammation, abscess and perforation.')]),
('pelvic-floor','Dynamic Pelvic Floor','abdomen',_pelvic,[('Rest','Establish the reference line and identify each compartment.'),('Strain','Compare descent against the same landmarks and document effort.'),('Evacuation','Inspect emptying, rectocele and intussusception on dynamic images.')]),
('breast-implants-male','Breast Implants & Male Breast','breast',_breast,[('Implant','Assess shell integrity with the appropriate sequence or modality.'),('Tissue','Evaluate a focal breast lesion separately from implant integrity.'),('Capsule','Describe peri-implant fluid, capsular masses and regional nodes.')]),
('tinnitus','Tinnitus: Vascular Relationships','head-neck',_tinnitus,[('Phenotype','Pulsatile and non-pulsatile symptoms lead to different imaging questions.'),('Vessels','Assess arterial and venous structures near the temporal bone.'),('Beyond vessels','Review the middle ear, skull base and internal auditory canals.')]),
('trigeminal','The Trigeminal Nerve','head-neck',_trigeminal,[('Trace the nerve','Follow the cisternal course to Meckel cave and the skull-base foramina.'),('Contact + shape','Describe the vessel and any displacement or atrophy of the nerve.'),('Alternatives','Look for mass, enhancement, demyelination and perineural disease.')]),
('sella','Sella & Parasellar Relationships','brain',_sella,[('Gland + lesion','Measure the gland and lesion; inspect signal and enhancement.'),('Optic structures','Describe the stalk, chiasm and suprasellar extension.'),('Lateral extension','Assess the cavernous sinuses, carotids and adjacent skull base.')]),
('elbow-mri','Elbow: Structures That Matter','bone',_elbow,[('Tendons','Name the tendon, injury location, continuity and retraction.'),('Stability','Inspect the individual collateral ligament components.'),('Joint + nerve','Review cartilage, loose bodies and the course of relevant nerves.')]),
('neonatal-spine','Neonatal Spine: Conus & Filum','bone',_neonatal,[('Number first','Explain how vertebral levels were counted and state any uncertainty.'),('Cord + filum','Document the conus position, cord motion and filum appearance.'),('Skin to canal','Trace any dermal tract and assess associated dysraphism.')]),
('gi-ultrasound','Bowel Ultrasound: Wall Layers','abdomen',_bowel_us,[('Find the segment','Use landmarks, graded compression and multiple imaging planes.'),('Measure the wall','Record distension and measure perpendicular to the bowel wall.'),('Add function','Assess peristalsis, compressibility, vascularity and the mesentery.')]),
('craniosynostosis','Cranial Sutures & Skull Shape','bone',_skull,[('Shape','Describe the cranial shape and the clinical question.'),('Sutures','Identify each patent or fused suture using age-appropriate imaging.'),('Associated anatomy','Assess the cranial base, orbits and intracranial structures as visible.')]),
]

RENDERERS = {'rad.5.'+key: renderer for key,title,motif,renderer,items in DATA}
RECORDS = [{'id':'rad.5.'+key,'title':title,'stage':5,'mode':'map','motif':motif,
            'takeaway':items[2][1] if len(items[2][1].split()) >= 8 else 'On imaging, ' + items[2][1][0].lower() + items[2][1][1:],
            'items':[{'label':label,'detail':detail} for label,detail in items]} for key,title,motif,renderer,items in DATA]
