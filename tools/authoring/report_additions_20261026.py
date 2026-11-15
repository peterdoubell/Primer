"""Author independent examination-specific selectable reports; preserve shipped forms."""
import copy
import gzip
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=json.loads(gzip.decompress((ROOT/'data/radiology/descriptor-reporting-v1.json.gz').read_bytes()))
SOURCES=[
 {'id':'acr-xr','title':'ACR–SPR–SSR practice parameter: radiography of the extremities','url':'https://gravitas.acr.org/PPTS/GetDocumentView?docId=12'},
 {'id':'essr','title':'ESSR: regional MSK imaging, arthritis, soft-tissue tumour and ultrasound guidance','url':'https://www.essr.org/workinggroups/'},
 {'id':'sij','title':'ASAS–SPARTAN consensus: diagnostic sacroiliac joint MRI','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC11671998/'},
 {'id':'knee-post','title':'Radiology Assistant: meniscal pathology including the postoperative meniscus','url':'https://radiologyassistant.nl/musculoskeletal/knee/meniscal-pathology'},
 {'id':'venous','title':'ACR vascular ultrasound examination requirements','url':'https://accreditationsupport.acr.org/support/solutions/articles/11000084118-exam-requirements-vascular-ultrasound'},
 {'id':'scrotum','title':'ACR–AIUM–SPR–SRU practice parameter: scrotal ultrasound','url':'https://gravitas.acr.org/PPTS/GetDocumentView?docId=99'},
 {'id':'acr-parameters','title':'ACR practice parameters and technical standards','url':'https://www.acr.org/clinical-resources/clinical-tools-and-reference/practice-parameters-and-technical-standards'},
 {'id':'lung-rads','title':'ACR Lung-RADS v2022','url':'https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/Lung-RADS'},
 {'id':'c-rads','title':'ACR C-RADS v2023','url':'https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/C-RADS'},
 {'id':'ni-rads','title':'ACR NI-RADS white paper: surveillance of the treated head and neck','url':'https://pubmed.ncbi.nlm.nih.gov/29983244/'},
 {'id':'recist','title':'RECIST Working Group: RECIST 1.1 guideline','url':'https://recist.eortc.org/recist/wp-content/uploads/sites/14/2025/12/RECISTGuidelines.pdf'},
 {'id':'orads','title':'ACR O-RADS US v2022 assessment and lexicon','url':'https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/O-RADS'},
 {'id':'lirads','title':'ACR CT/MRI LI-RADS v2018 diagnostic algorithm','url':'https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/LI-RADS'},
]
OUT={'version':'2026-10-26','sources':SOURCES,'investigations':{},'coverage':[]}
OLD={}
for path in sorted({*(ROOT/'data/radiology').glob('msk-anatomic-*.json'),*(ROOT/'data/radiology').glob('anatomic-*.json')}):
 if path.name=='anatomic-additions-20261026.json':continue
 for key,value in json.loads(path.read_text())['investigations'].items():OLD[key]=value

def slug(t):return re.sub('[^a-z0-9]+','-',t.lower()).strip('-')
def f(id,label,text,parents=None,ex=None,report=True,bad=None):
 d={'id':id,'label':label,'text':text}
 if parents:d['requires_any']=parents
 if ex:d['exclusive_group']=ex
 if not report:d['report']=False
 if bad:d['invalidates_normal']=bad
 return d

def row(id,label,group,normal,findings,refs=('essr',),repeat=False,exclude=False):
 d={'id':id,'label':label,'group':group,'normal':normal,'findings':findings,'source_ids':list(refs)}
 if repeat:d.update(repeatable=True,repeat_label='Lesion')
 if exclude:d['exclude_from_bulk_normal']=True
 return d

def choice(id,label,text,values,group='Technique',refs=('acr-parameters',),report=True):
 return row(id,label,group,None,[f('assessment',label,text+' ['+' / '.join(values)+'].',report=report)],refs,exclude=True)

def exam(id,title,modality,guide,base,rows):
 assert id not in OLD and id not in OUT['investigations'],id
 assert guide in BASE['forms'] and base in OLD,(guide,base)
 assert len({r['id'] for r in rows})==len(rows),id
 OUT['investigations'][id]={'guide_id':guide,'title':title,'modality':modality,'base_investigation_id':base,'sections':rows}
 OUT['coverage'].append({'investigation_id':id,'expected_anatomy_ids':[r['id'] for r in rows]})

def cloned(id):
 rows=copy.deepcopy(OLD[id]['sections'])
 # Carry the exact independent author's source lineage into the addition file.
 known={s['id'] for s in SOURCES}
 for path in sorted({*(ROOT/'data/radiology').glob('msk-anatomic-*.json'),*(ROOT/'data/radiology').glob('anatomic-*.json')}):
  if path.name=='anatomic-additions-20261026.json':continue
  data=json.loads(path.read_text())
  if id not in data['investigations']:continue
  remap={}
  for source in data['sources']:
   new=path.stem+':'+source['id'];remap[source['id']]=new
   if new not in known:SOURCES.append(dict(source,id=new));known.add(new)
  for r in rows:r['source_ids']=[remap[k] for k in r['source_ids']]
  break
 return rows

def side_control():return choice('side','Examined side','Examined side is',['right','left','bilateral'],refs=('acr-xr','essr'))
def xr_tech():return [side_control(),choice('views','Acquired projections','Acquired projections are',['AP and lateral','AP and oblique','AP lateral and oblique','PA lateral and oblique','AP lateral and skyline','AP lateral and mortise','AP pelvis and lateral hip','single AP view','single lateral view','dedicated additional projections'],refs=('acr-xr',)),choice('weight-bearing','Weight bearing','The acquired examination is',['weight-bearing','non-weight-bearing','stress views','weight-bearing and non-weight-bearing views'],refs=('acr-xr',))]

def bone(name,group='Bones'):
 return row(slug(name),name,group,name+': no acute fracture or focal destructive osseous lesion.',[
 f('fracture','Fracture',name+': a [transverse / oblique / spiral / comminuted / avulsion / impacted / intra-articular / stress-type] fracture is identified.'),
 f('site','Fracture location',name+': the fracture involves the [proximal portion / middle portion / distal portion / articular surface].',['fracture']),
 f('displacement','Displacement',name+': the fracture is [undisplaced / minimally displaced / displaced / overriding / distracted].',['fracture']),
 f('offset','Measured displacement',name+': fragment displacement __ mm.',['fracture']),
 f('angulation','Angulation',name+': [no angulation / apex anterior angulation / apex posterior angulation / apex medial angulation / apex lateral angulation].',['fracture']),
 f('angle','Measured angulation',name+': fracture angulation __ °.',['fracture']),
 f('surface','Articular involvement',name+': articular [step-off / depression / gap] measures __ mm.',['fracture']),
 f('healing','Healing',name+': [early callus / bridging callus / persistent fracture line / corticated ununited fragment / malunion].'),
 f('lesion','Focal bone lesion',name+': a [lucent / sclerotic / mixed lucent-sclerotic] lesion is identified.'),
 f('periosteum','Periosteal reaction',name+': [solid / lamellated / interrupted / spiculated] periosteal reaction.'),
 f('density','Bone density',name+': [generalised osteopenia / focal osteopenia / diffuse sclerosis].')],('acr-xr',))

def joint(name):
 return row(slug(name),name,'Joints',name+': alignment and joint space are preserved.',[
 f('alignment','Malalignment',name+': [subluxation / dislocation / varus malalignment / valgus malalignment].'),
 f('narrowing','Joint-space narrowing',name+': [mild / moderate / severe] [uniform / non-uniform] joint-space narrowing.'),
 f('degeneration','Degenerative change',name+': [small / moderate / large] marginal osteophytes.'),
 f('subchondral','Subchondral change',name+': [sclerosis / cysts / sclerosis and cysts / articular collapse].'),
 f('erosion','Erosion',name+': [marginal / central / extensive] articular erosions.'),
 f('calcification','Chondrocalcinosis',name+': chondrocalcinosis is present.'),
 f('effusion','Effusion',name+': a radiographically visible [small / moderate / large] joint effusion.')],('acr-xr',))

def xr_soft():
 return row('soft-tissues','Regional soft tissues','Soft tissues','No focal radiographic soft-tissue abnormality.',[
 f('swelling','Swelling','[Focal / diffuse] soft-tissue swelling.'),f('gas','Gas','[Subcutaneous / deep soft-tissue / intra-articular] gas is present.'),
 f('foreign-body','Radiopaque foreign body','A radiopaque foreign body measures __ mm.'),f('calcification','Calcification','[Tendon-related / periarticular / vascular / diffuse soft-tissue] calcification.')],('acr-xr',),repeat=True)

def hardware():
 return row('hardware','Fixation / arthroplasty components','Postoperative findings',None,[
 f('present','Hardware present','[Plate and screws / intramedullary nail / screws / anchors / joint prosthesis / spinal instrumentation] are present.'),
 f('integrity','Integrity','Hardware is [intact / fractured / disassembled / bent].',['present']),
 f('position','Position','Hardware position is [satisfactory / migrated / protruding beyond cortex / intra-articular / changed from reviewed prior].',['present']),
 f('lucency','Interface','The bone-hardware interface shows [no visible lucency / focal lucency / progressive lucency / circumferential lucency].',['present']),
 f('width','Lucency width','Interface lucency measures __ mm.',['lucency']),
 f('union','Osseous union','The operated site shows [bridging union / partial bridging / no bridging visible / malunion / nonunion morphology].',['present'])],('acr-xr',),exclude=True)

# Separate radiographs have actual regional bones and joints, never MR-only negatives.
XR=[
 ('shoulder','Shoulder','rad.5.shoulder','ra.mri-shoulder',['Proximal humerus','Scapula','Clavicle'],['Glenohumeral joint','Acromioclavicular joint']),
 ('clavicle','Clavicle','rad.5.shoulder','ra.mri-shoulder',['Medial clavicle','Clavicular shaft','Lateral clavicle'],['Sternoclavicular joint','Acromioclavicular joint']),
 ('ac-joints','Acromioclavicular joints','rad.5.shoulder','ra.mri-shoulder',['Right distal clavicle','Left distal clavicle','Right acromion','Left acromion'],['Right acromioclavicular joint','Left acromioclavicular joint']),
 ('humerus','Humerus','rad.5.shoulder','ra.mri-shoulder',['Proximal humerus','Humeral shaft','Distal humerus'],['Visible shoulder joint','Visible elbow joint']),
 ('elbow','Elbow','rad.5.elbow-mri','ra.mri-elbow',['Distal humerus','Radial head and neck','Olecranon','Coronoid process','Proximal ulna'],['Radiocapitellar joint','Ulnohumeral joint','Proximal radioulnar joint']),
 ('forearm','Forearm','rad.5.elbow-mri','ra.mri-elbow',['Radial shaft','Ulnar shaft','Radial head','Distal radius','Distal ulna'],['Visible elbow joint','Distal radioulnar joint','Visible wrist joint']),
 ('wrist','Wrist','rad.5.wrist-hand','ra.wrist-fractures',['Distal radius','Distal ulna','Scaphoid','Lunate','Triquetrum','Pisiform','Trapezium','Trapezoid','Capitate','Hamate'],['Radiocarpal joint','Midcarpal joint','Scapholunate interval','Lunotriquetral interval','Distal radioulnar joint']),
 ('hand','Hand','rad.5.wrist-hand','ra.wrist-fractures',['First metacarpal','Second metacarpal','Third metacarpal','Fourth metacarpal','Fifth metacarpal','Thumb phalanges','Index phalanges','Middle finger phalanges','Ring finger phalanges','Little finger phalanges'],['First CMC joint','MCP joints','PIP joints','DIP joints']),
 ('finger','Finger / thumb','rad.5.wrist-hand','ra.wrist-fractures',['Included metacarpal','Proximal phalanx','Middle phalanx where present','Distal phalanx'],['MCP joint','PIP or thumb IP joint','DIP joint where present']),
 ('pelvis','Pelvis','rad.5.hip','ra.hip-arthroplasty',['Right ilium','Left ilium','Right acetabulum','Left acetabulum','Right superior pubic ramus','Left superior pubic ramus','Right inferior pubic ramus','Left inferior pubic ramus','Sacrum'],['Right hip joint','Left hip joint','Right sacroiliac joint','Left sacroiliac joint','Pubic symphysis']),
 ('hip','Hip','rad.5.hip','ra.hip-arthroplasty',['Femoral head','Femoral neck','Greater trochanter','Lesser trochanter','Proximal femoral shaft','Acetabulum'],['Hip joint','Visible pubic symphysis']),
 ('femur','Femur','rad.5.hip','ra.hip-arthroplasty',['Femoral head and neck','Proximal femoral shaft','Mid femoral shaft','Distal femur'],['Visible hip joint','Visible knee joint']),
 ('knee','Knee','rad.5.knee','ra.mri-knee',['Distal femur','Proximal tibia','Proximal fibula','Patella'],['Medial tibiofemoral compartment','Lateral tibiofemoral compartment','Patellofemoral compartment','Proximal tibiofibular joint']),
 ('tibia-fibula','Tibia and fibula','rad.5.ankle-foot','ra.ankle-fractures',['Proximal tibia','Tibial shaft','Distal tibia','Proximal fibula','Fibular shaft','Distal fibula'],['Visible knee joint','Visible ankle joint']),
 ('ankle','Ankle','rad.5.ankle-foot','ra.ankle-fractures',['Distal tibia','Medial malleolus','Posterior malleolus','Distal fibula','Talus'],['Ankle mortise','Distal tibiofibular syndesmosis','Visible subtalar joint']),
 ('foot','Foot','rad.5.ankle-foot','ra.foot-ankle-cases',['Calcaneus','Talus','Navicular','Cuboid','Medial cuneiform','Intermediate cuneiform','Lateral cuneiform','First metatarsal','Second metatarsal','Third metatarsal','Fourth metatarsal','Fifth metatarsal','Included phalanges'],['Subtalar joint','Talonavicular joint','Calcaneocuboid joint','First tarsometatarsal joint','Lisfranc alignment','Lesser tarsometatarsal joints','MTP joints','Interphalangeal joints']),
 ('toe','Toe / hallux','rad.5.ankle-foot','ra.foot-ankle-cases',['Included metatarsal','Proximal phalanx','Middle phalanx where present','Distal phalanx','Sesamoids where included'],['MTP joint','PIP or hallux IP joint','DIP joint where present']),
 ('calcaneus','Calcaneus','rad.5.ankle-foot','ra.foot-ankle-cases',['Calcaneal body','Posterior tuberosity','Sustentaculum tali','Anterior process'],['Posterior subtalar joint','Calcaneocuboid joint']),
 ('sacroiliac','Sacroiliac joints','rad.4.arthritis','ra.arthritis',['Right sacral margin','Left sacral margin','Right iliac margin','Left iliac margin'],['Right sacroiliac joint','Left sacroiliac joint']),
 ('sacrum-coccyx','Sacrum and coccyx','rad.4.spine-imaging','ra.thoracolumbar-injury',['Sacral body','Right sacral ala','Left sacral ala','Coccyx'],['Sacrococcygeal alignment','Visible right sacroiliac joint','Visible left sacroiliac joint']),
 ('ribs','Ribs','rad.3.chest-xray','ra.chest-radiography',['Included right ribs','Included left ribs'],[]),
]
for key,title,guide,base,bones,joints in XR:
 rows=xr_tech()+[bone(n) for n in bones]+[joint(n) for n in joints]+[xr_soft(),hardware()]
 if key=='finger':rows.insert(1,choice('digit','Examined digit','Examined digit is',['thumb','index finger','middle finger','ring finger','little finger'],refs=('acr-xr',)))
 if key=='toe':rows.insert(1,choice('digit','Examined digit','Examined digit is',['hallux','second toe','third toe','fourth toe','fifth toe'],refs=('acr-xr',)))
 if key=='ribs':rows += [row('pleura','Included pleura','Thorax','No visible pneumothorax or pleural effusion.',[f('pneumothorax','Pneumothorax','A [right / left] pneumothorax is identified.'),f('effusion','Pleural fluid','A [right / left / bilateral] pleural effusion is identified.')],('acr-xr',))]
 exam('xr.'+key,title+' radiographs','Radiography',guide,base,rows)

for region,levels in [('cervical',['C2','C3','C4','C5','C6','C7']),('thoracic',['T'+str(n) for n in range(1,13)]),('lumbar',['L'+str(n) for n in range(1,6)])]:
 rows=[choice('views','Acquired projections','Acquired projections are',['AP and lateral','AP lateral and obliques','AP lateral and open-mouth odontoid','lateral flexion and extension','AP and lateral erect']),choice('alignment','Overall alignment','Overall alignment shows',['preserved alignment','straightening','scoliosis','kyphosis','listhesis'])]
 for level in levels:
  rows+=[bone(level+' vertebra','Vertebrae')]
 for a,b in zip(levels,levels[1:]):
  rows += [joint(a+'–'+b+' disc space')]
 rows += [row('posterior-elements','Visible posterior elements','Posterior elements','No visible posterior-element fracture or focal destructive lesion.',[f('facet','Facet arthropathy','[Mild / moderate / severe] visible facet arthropathy.'),f('pars','Pars defect','A [right / left / bilateral] pars defect is visible.'),f('fracture','Fracture','A visible posterior-element fracture is present.')],('acr-xr',)),xr_soft(),hardware()]
 if region=='cervical':rows += [joint('Atlantoaxial alignment'),bone('Odontoid process','Craniovertebral junction'),row('prevertebral','Prevertebral soft tissues','Soft tissues','No prevertebral soft-tissue widening.',[f('widening','Widening','Prevertebral soft tissues are widened at [upper cervical / lower cervical] levels.')],('acr-xr',))]
 exam('xr.spine-'+region,region.capitalize()+' spine radiographs','Radiography','rad.4.spine-imaging','ra.thoracolumbar-injury',rows)
exam('xr.scoliosis','Standing whole-spine scoliosis radiographs','Radiography','rad.4.spine-imaging','ra.thoracolumbar-injury',[
 choice('position','Acquisition','Acquisition is',['standing PA and lateral','standing AP and lateral','supine AP','side-bending views']),
 row('curve','Spinal curve','Curves','No measurable coronal spinal curve.',[f('curve','Curve','A [right-convex / left-convex] [thoracic / thoracolumbar / lumbar] curve is present.'),f('cobb','Cobb measurement','Cobb angle __ ° between [T1 / T2 / T3 / T4 / T5 / T6 / T7 / T8 / T9 / T10 / T11 / T12 / L1 / L2 / L3 / L4 / L5] and [T1 / T2 / T3 / T4 / T5 / T6 / T7 / T8 / T9 / T10 / T11 / T12 / L1 / L2 / L3 / L4 / L5].',['curve']),f('rotation','Rotation','[Mild / moderate / marked] apical vertebral rotation.',['curve'])],('acr-xr',),repeat=True),
 choice('balance-coronal','Coronal balance','Coronal balance is',['neutral','rightward imbalance','leftward imbalance'],'Balance'),choice('balance-sagittal','Sagittal balance','Sagittal balance is',['neutral','positive sagittal imbalance','negative sagittal imbalance'],'Balance'),bone('Included vertebrae'),hardware()])
exam('xr.lower-limb-alignment','Standing lower-limb alignment and leg-length radiographs','Radiography','rad.5.knee','ra.mri-knee',[
 choice('position','Acquisition','Acquisition is',['standing bilateral hip-knee-ankle AP','supine scanogram','standing unilateral long-leg AP']),
 *[row(side+'-measurements',side.capitalize()+' limb','Measurements',None,[f('length','Bone lengths',side.capitalize()+' femur __ mm; tibia __ mm; total limb length __ mm.'),f('axis','Mechanical axis',side.capitalize()+' hip-knee-ankle angle __ ° with [varus / valgus / neutral] alignment.'),f('deviation','Axis deviation',side.capitalize()+' mechanical axis passes __ mm [medial / lateral] to knee centre.')],('acr-xr',),exclude=True) for side in ['right','left']],
 choice('difference','Leg-length comparison','Leg-length comparison shows',['equal measured lengths','right limb longer','left limb longer'],'Measurements'),hardware()])
exam('xr.abdomen','Abdominal radiographs','Radiography','rad.3.acute-abdomen','ra.acute-abdomen',[
 choice('projections','Acquisition','Acquired abdominal projection is',['AP supine','AP erect','supine and erect','left lateral decubitus']),
 row('bowel','Bowel gas pattern','Bowel','No dilated gas-filled bowel loops.',[f('small','Small bowel dilatation','[Central / diffuse] small bowel dilatation.'),f('large','Colonic dilatation','[Focal / diffuse] colonic dilatation.'),f('calibre','Calibre','Maximum dilated bowel calibre __ mm.',['small','large']),f('levels','Fluid levels','[Multiple / few] air-fluid levels on the acquired horizontal-beam view.'),f('stool','Faecal loading','[Mild / moderate / marked] colonic faecal loading.')],('acr-parameters',)),
 row('free-air','Extraluminal gas','Extraluminal gas',None,[f('negative','No visible free gas','No free intraperitoneal gas is visible on the acquired upright or decubitus view.'),f('positive','Free gas','Free intraperitoneal gas is visible.'),f('limited','Limited assessment','Free intraperitoneal gas cannot be reliably excluded on this supine examination.')],('acr-parameters',),exclude=True),
 row('calcifications','Calcifications and foreign bodies','Other findings','No suspicious radiopaque foreign body or pathological calcification.',[f('calcification','Calcification','[Renal-tract / biliary-region / pancreatic-region / vascular / pelvic] calcification.'),f('foreign','Foreign body','A radiopaque foreign body is present in the [upper / mid / lower] abdomen.')],('acr-parameters',),repeat=True),hardware()])

# Postoperative joints retain the complete original anatomy, then add separate operated structures.
def repaired_tendon(name):
 return row('repair-'+slug(name),name+' repair','Tendon repair',None,[f('status','Repair appearance',name+' repair shows [continuous tendon / thinning with continuity / articular-sided defect / bursal-sided defect / full-thickness recurrent defect / indeterminate continuity due to artefact].'),f('size','Defect size',name+' repair defect measures __ × __ mm.',['status']),f('retraction','Retraction',name+' tendon retraction __ mm.',['status']),f('footprint','Footprint',name+' footprint is [covered / partly uncovered / fully uncovered].'),f('anchor','Anchor complication',name+' anchor shows [migration / surrounding cyst / extrusion / susceptibility artefact limiting assessment].')],('essr',),exclude=True)
rows=cloned('ra.mri-shoulder')+[repaired_tendon(n) for n in ['Supraspinatus','Infraspinatus','Subscapularis','Teres minor']]
rows += [choice('biceps-operation','Biceps operation','Observed biceps operative configuration is',['tenodesis with intact fixation','tenodesis with fixation failure','tenotomy configuration','indeterminate operative configuration'],'Biceps operation',('essr',)),row('labral-repair','Labral repair','Labral repair',None,[f('repair','Repair','The [superior / anterosuperior / anteroinferior / posterior] labral repair is [intact in appearance / suspicious for recurrent detachment / obscured by artefact].'),f('anchor','Anchor complication','A labral anchor shows [migration / intra-articular protrusion / surrounding cystic change].')],('essr',),repeat=True,exclude=True)]
exam('msk.mri-shoulder-postoperative','MRI shoulder — postoperative repair','MRI','rad.5.shoulder','ra.mri-shoulder',rows)
rows=cloned('ra.mri-knee')
for ligament in ['ACL','PCL']:
 rows += [row('graft-'+ligament.lower(),ligament+' graft','Ligament reconstruction',None,[f('continuity','Graft continuity',ligament+' graft shows [preserved continuity / partial fibre disruption / complete disruption / indeterminate continuity].'),f('signal','Graft signal',ligament+' graft signal is [expected for documented postoperative interval / increased without definite disruption / markedly heterogeneous / limited by artefact].'),f('impingement','Impingement',ligament+' graft [does not impinge / impinges on the intercondylar roof / impinges on the notch wall].'),f('tunnel','Tunnel complication',ligament+' reconstruction shows [femoral tunnel widening / tibial tunnel widening / tunnel cyst / tunnel malposition / fixation displacement].'),f('tunnel-size','Tunnel size',ligament+' tunnel diameter __ mm.',['tunnel'])],('essr',),exclude=True)]
for name in ['Medial meniscus','Lateral meniscus']:
 rows += [row('repair-'+slug(name),name+' surgery','Meniscal surgery',None,[f('operation','Operative morphology',name+' shows [partial meniscectomy / subtotal meniscectomy / repair / root repair / transplant].'),f('finding','Residual / repaired meniscus',name+' shows [no convincing recurrent tear / new fluid-signal cleft reaching an articular surface / displaced fragment / root discontinuity / indeterminate postoperative signal].',['operation']),f('extrusion','Extrusion',name+' extrusion __ mm.',['operation'])],('knee-post',),exclude=True)]
rows += [row('arthrofibrosis','Arthrofibrosis / cyclops','Postoperative complications','No focal anterior arthrofibrotic nodule.',[f('nodule','Cyclops-type nodule','An anterior intercondylar fibrous nodule measures __ × __ mm.'),f('scar','Diffuse fibrosis','Diffuse postoperative fibrosis involves the [Hoffa fat pad / anterior interval / suprapatellar recess / posterior capsule].')],('essr',)),row('cartilage-repair','Cartilage repair site','Cartilage repair',None,[f('site','Site','A cartilage repair site involves the [medial femoral condyle / lateral femoral condyle / trochlea / patella / tibial plateau].'),f('fill','Fill','The repair site shows [complete fill / partial fill / hypertrophic fill / delamination / exposed subchondral bone].',['site']),f('integration','Integration','Repair margins are [integrated / partly separated / delaminated].',['site']),f('bone','Subchondral bone','The repair bed shows [no oedema / marrow oedema / cysts / collapse].',['site'])],('essr',),repeat=True,exclude=True)]
exam('msk.mri-knee-postoperative','MRI knee — postoperative reconstruction and meniscal repair','MRI','rad.5.knee','ra.mri-knee',rows)

# MRI SI joints separates both articular sides and active / structural findings.
rows=[choice('coverage','Acquired protocol','The acquired SI-joint protocol includes',['semicoronal T1 and fluid-sensitive with semiaxial fluid-sensitive imaging','semicoronal T1 and fluid-sensitive imaging only','incomplete diagnostic coverage'],refs=('sij',))]
for side in ['right','left']:
 for surface in ['iliac','sacral']:
  for division in ['superior','middle','inferior']:
   name=side.capitalize()+' '+division+' '+surface+' articular margin'
   rows += [row(slug(name),name,side.capitalize()+' SI joint',name+': no subchondral oedema, erosion or focal fat metaplasia.',[f('oedema','Oedema',name+': [focal / multifocal / confluent] subchondral marrow oedema.'),f('erosion','Erosion',name+': [single / multiple / extensive] erosions.'),f('fat','Fat metaplasia',name+': subchondral fat metaplasia.'),f('backfill','Backfill',name+': fat-containing erosion backfill.'),f('sclerosis','Sclerosis',name+': subchondral sclerosis.'),f('ankylosis','Ankylosis',name+': [partial / complete] ankylosis.'),f('depth','Oedema depth',name+': oedema depth __ mm.',['oedema'])],('sij',))]
 for structure in ['joint space','capsule','posterior ligamentous compartment']:
  rows += [row(slug(side+' '+structure),side.capitalize()+' '+structure,side.capitalize()+' SI joint',side.capitalize()+' '+structure+': no focal abnormality.',[f('fluid','Fluid / inflammation',side.capitalize()+' '+structure+': [fluid distension / capsular oedema / periarticular soft-tissue oedema / ligamentous oedema].'),f('degeneration','Degeneration',side.capitalize()+' '+structure+': [anterior osteophytes / focal cartilage loss / vacuum phenomenon on available CT / subchondral cysts].')],('sij',))]
rows += [row('mimics','Alternative causes','Additional findings','No focal sacral insufficiency fracture or destructive pelvic lesion.',[f('fracture','Insufficiency fracture','A [right / left / bilateral] sacral insufficiency fracture is identified.'),f('oci','Osteitis condensans ilii pattern','[Right / left / bilateral] triangular iliac-sided sclerosis without erosions.'),f('infection','Infection pattern','[Right / left] joint fluid, erosive change and adjacent soft-tissue inflammation raise concern for infection.'),f('mechanical','Mechanical pattern','Anterior mechanically distributed SI-joint change is present.')],('sij',))]
exam('msk.mri-sacroiliac','MRI sacroiliac joints — inflammatory and structural assessment','MRI','rad.4.arthritis','ra.arthritis',rows)

# Soft-tissue masses: no mass is a valid explicit observation; each mass is independent.
def soft_mass(modality):
 fs=[f('site','Anatomical location','The lesion is in the [right / left / midline] [neck / shoulder / arm / elbow / forearm / wrist / hand / chest wall / abdominal wall / pelvis / hip / thigh / knee / leg / ankle / foot].'),f('compartment','Compartment','The lesion is [dermal / subcutaneous / fascial / intramuscular / intermuscular / tendon-related / nerve-related / intra-articular].',['site']),f('size','Three dimensions','The lesion measures __ × __ × __ mm.',['site']),f('margin','Margins','The lesion has [well-defined / partly defined / infiltrative] margins.',['site']),f('composition','Composition','The lesion is [simple fluid / complex fluid / predominantly fatty / predominantly solid / mixed solid and cystic / vascular].',['site']),f('neurovascular','Neurovascular relation','The lesion [is separate from / displaces / abuts / encases] the adjacent [nerve / artery / vein / neurovascular bundle].',['site']),f('bone','Bone relationship','The lesion [is separate from bone / abuts cortex / causes cortical remodelling / destroys cortex / extends into marrow].',['site']),f('necrosis','Necrosis / haemorrhage','The lesion contains [necrotic areas / haemorrhagic areas / both necrosis and haemorrhage].',['site']),f('oedema','Surrounding change','There is [no surrounding oedema / mild surrounding oedema / extensive surrounding oedema].',['site'])]
 if modality=='Ultrasound':fs += [f('echo','Echogenicity','The lesion is [anechoic / hypoechoic / isoechoic / hyperechoic / heterogeneous].',['site']),f('doppler','Doppler','The lesion has [no detected internal flow / peripheral flow / internal flow / marked internal flow].',['site']),f('dynamic','Dynamic assessment','The lesion is [compressible / noncompressible / mobile relative to fascia / tethered to fascia].',['site'])]
 else:fs += [f('t1','T1 signal','The lesion is [low T1 signal / intermediate T1 signal / high T1 signal].',['site']),f('t2','Fluid-sensitive signal','The lesion is [low / intermediate / high / mixed] signal on fluid-sensitive sequences.',['site']),f('enhancement','Acquired contrast assessment','On the acquired postcontrast images the lesion shows [no enhancement / thin peripheral enhancement / homogeneous solid enhancement / heterogeneous solid enhancement / nodular enhancement].',['site']),f('diffusion','Acquired diffusion assessment','The solid component shows [restricted diffusion / no definite restriction / indeterminate diffusion].',['site'])]
 return [side_control(),row('mass','Soft-tissue mass','Mass characterization','No focal soft-tissue mass is identified in the examined region.',fs,('essr',),repeat=True),choice('comparison','Reviewed comparison','Compared with the reviewed prior examination the mass is',['unchanged','larger','smaller','new'],'Comparison',('essr',))]
for mod,key in [('MRI','mri'),('Ultrasound','ultrasound')]:exam('msk.'+key+'-soft-tissue-mass',mod+' soft-tissue mass','MRI' if mod=='MRI' else 'Ultrasound','rad.5.bone-tumours','ra.bone-tumours',soft_mass(mod))

# Ultrasound regional protocols enumerate individual tendons, ligaments and nerves.
US={
 'elbow':('rad.5.elbow-mri','ra.mri-elbow',['Common extensor tendon','Common flexor tendon','Distal biceps tendon','Triceps tendon'],['Ulnar collateral ligament anterior bundle','Lateral collateral ligament complex','Annular ligament'],['Ulnar nerve at cubital tunnel','Median nerve','Radial nerve and posterior interosseous branch'],['Anterior recess','Posterior recess','Olecranon bursa']),
 'wrist':('rad.5.wrist-hand','ra.wrist-fractures',['First extensor compartment','Second extensor compartment','Third extensor compartment','Fourth extensor compartment','Fifth extensor compartment','Sixth extensor compartment','Flexor carpi radialis','Flexor carpi ulnaris','Finger flexor tendons'],['Visible scapholunate ligament','Visible ulnar wrist ligaments'],['Median nerve at carpal tunnel','Ulnar nerve at Guyon canal'],['Radiocarpal recess','Midcarpal recess','Distal radioulnar recess']),
 'hand':('rad.5.wrist-hand','ra.wrist-fractures',['Thumb flexor','Index flexors','Middle finger flexors','Ring finger flexors','Little finger flexors','Thumb extensors','Index extensor','Middle finger extensor','Ring finger extensor','Little finger extensor'],['Thumb MCP ulnar collateral ligament','Thumb MCP radial collateral ligament','Digital collateral ligaments','Digital pulleys'],['Digital nerves'],['MCP recesses','PIP recesses','DIP recesses']),
 'hip':('rad.5.hip','ra.hip-arthroplasty',['Gluteus medius tendon','Gluteus minimus tendon','Iliopsoas tendon','Proximal rectus femoris tendon','Proximal adductor tendon','Proximal hamstring tendons'],['Visible anterior capsule'],['Lateral femoral cutaneous nerve','Visible femoral nerve','Visible sciatic nerve'],['Anterior hip recess','Trochanteric bursae','Iliopsoas bursa']),
 'knee':('rad.5.knee','ra.mri-knee',['Quadriceps tendon','Patellar tendon','Distal biceps femoris tendon','Semimembranosus tendon','Pes anserine tendons','Popliteus tendon'],['Medial collateral ligament','Lateral collateral ligament','Medial patellar retinaculum','Lateral patellar retinaculum'],['Common peroneal nerve','Visible tibial nerve'],['Suprapatellar recess','Medial recess','Lateral recess','Prepatellar bursa','Pes anserine bursa','Popliteal fossa']),
 'ankle':('rad.5.ankle-foot','ra.ankle-fractures',['Tibialis anterior tendon','Extensor hallucis longus tendon','Extensor digitorum longus tendon','Tibialis posterior tendon','Flexor digitorum longus tendon','Flexor hallucis longus tendon','Peroneus longus tendon','Peroneus brevis tendon','Achilles tendon'],['Anterior talofibular ligament','Calcaneofibular ligament','Visible posterior talofibular ligament','Deltoid ligament','Anterior inferior tibiofibular ligament','Spring ligament'],['Tibial nerve at tarsal tunnel','Superficial peroneal nerve','Sural nerve'],['Anterior ankle recess','Retrocalcaneal bursa','Superficial Achilles bursa','Sinus tarsi']),
 'foot':('rad.5.ankle-foot','ra.foot-ankle-cases',['Plantar fascia','Hallux flexor tendon','Lesser toe flexor tendons','Hallux extensor tendon','Lesser toe extensor tendons'],['Lisfranc ligament visible component','First MTP plantar plate','Second MTP plantar plate','Third MTP plantar plate','Fourth MTP plantar plate','Fifth MTP plantar plate'],['First intermetatarsal space','Second intermetatarsal space','Third intermetatarsal space','Fourth intermetatarsal space'],['First MTP recess','Lesser MTP recesses','Intermetatarsal bursae'])}
def us_tendon(name):return row(slug(name),name,'Tendons',name+': preserved fibrillar architecture and continuity.',[f('tendinosis','Tendinosis',name+': [mild / moderate / severe] tendinosis.'),f('partial','Partial tear',name+': [low-grade / high-grade] partial-thickness tear.'),f('complete','Complete tear',name+': complete rupture with a gap __ mm.'),f('size','Tear dimensions',name+': tear measures __ × __ mm.',['partial','complete']),f('sheath','Sheath / paratenon',name+': [sheath fluid / synovial thickening / hyperaemia / paratenon thickening].'),f('calcium','Calcific focus',name+': calcific focus __ mm.'),f('dynamic','Dynamic finding',name+': [subluxation / dislocation / snapping / reduced excursion] on observed dynamic assessment.')],('essr',))
def us_ligament(name):return row(slug(name),name,'Ligaments and stabilisers',name+': visible fibres are continuous.',[f('sprain','Sprain',name+': [thickened hypoechoic fibres / partial fibre disruption / complete fibre discontinuity].'),f('laxity','Dynamic laxity',name+': abnormal laxity is demonstrated on the performed stress manoeuvre.'),f('avulsion','Avulsion',name+': an avulsion fragment is identified.')],('essr',))
def nerve(name):return row(slug(name),name,'Nerves',name+': preserved calibre and fascicular pattern in the assessed segment.',[f('enlarged','Enlargement',name+': [focal / diffuse] enlargement.'),f('csa','Cross-sectional area',name+': cross-sectional area __ mm².',['enlarged']),f('echotexture','Fascicles',name+': [hypoechoic swollen fascicles / loss of fascicular pattern / focal neuroma / discontinuity].'),f('compression','Compression',name+': [flattening / external compression / dynamic subluxation] is demonstrated.'),f('site','Level',name+': the abnormality is at the [proximal assessed segment / middle assessed segment / distal assessed segment].')],('essr',))
for region,(guide,base,tendons,ligaments,nerves,recesses) in US.items():
 rows=[side_control()]+[us_tendon(n) for n in tendons]+[us_ligament(n) for n in ligaments]+[nerve(n) for n in nerves]
 rows += [row(slug(n),n,'Recesses and bursae',n+': no distension or synovial thickening.',[f('fluid','Fluid',n+': [small / moderate / large] fluid distension.'),f('synovium','Synovium',n+': [mild / moderate / marked] synovial hypertrophy.'),f('flow','Doppler activity',n+': [absent / mild / moderate / marked] Doppler activity.',['synovium'])],('essr',)) for n in recesses]
 rows += [soft_mass('Ultrasound')[1]]
 exam('msk.ultrasound-'+region,'Ultrasound '+region+' — regional tendons, ligaments and nerves','Ultrasound',guide,base,rows)

# Plexus/nerve reports use individual roots, trunks, divisions and terminal branches.
for kind,guide,base,names in [
 ('brachial','rad.5.shoulder','ra.mri-shoulder',['C5 root','C6 root','C7 root','C8 root','T1 root','Upper trunk','Middle trunk','Lower trunk','Anterior divisions','Posterior divisions','Lateral cord','Medial cord','Posterior cord','Musculocutaneous nerve','Axillary nerve','Radial nerve','Median nerve','Ulnar nerve','Long thoracic nerve','Suprascapular nerve']),
 ('lumbosacral','rad.4.spine-imaging','ra.mri-myelopathy',['L1 root','L2 root','L3 root','L4 root','L5 root','S1 root','S2 root','S3 root','Lumbar plexus','Lumbosacral trunk','Sacral plexus','Femoral nerve','Obturator nerve','Sciatic nerve','Superior gluteal nerve','Inferior gluteal nerve','Pudendal nerve'])]:
 rows=[]
 for side_name in ['right','left']:
  for name in names:
   full=side_name.capitalize()+' '+name
   rows += [row(slug(full),full,side_name.capitalize()+' plexus',full+': preserved calibre, continuity and signal.',[f('signal','Signal',full+': [mild / moderate / marked] T2 hyperintensity.'),f('calibre','Calibre',full+': [focal enlargement / diffuse enlargement / thinning].'),f('continuity','Continuity',full+': [preserved fascicular continuity / partial disruption / complete discontinuity / avulsed root].'),f('mass','Mass / compression',full+': [nerve-centred mass / extrinsic compression / surrounding fibrosis].'),f('enhancement','Acquired contrast assessment',full+': enhancement is present on the acquired postcontrast images.')],('essr',))]
 rows += [row('denervation','Muscle denervation','Muscles','No denervation pattern in the assessed muscle groups.',[f('muscle','Denervation','[Acute oedema / fatty atrophy / mixed oedema and fatty atrophy] involves the [right / left / bilateral] [proximal / distal / proximal and distal] assessed muscle groups.'),f('pattern','Distribution','The distribution is [root-predominant / plexus-predominant / terminal-nerve-predominant / indeterminate].',['muscle'])],('essr',))]
 exam('msk.mri-'+kind+'-plexus','MR neurography — '+kind+' plexus','MRI',guide,base,rows)
for region,names in [('upper-limb',['Median nerve at forearm','Median nerve at carpal tunnel','Ulnar nerve at elbow','Ulnar nerve at Guyon canal','Radial nerve','Posterior interosseous nerve','Superficial radial nerve']),('lower-limb',['Sciatic nerve','Common peroneal nerve at fibular neck','Deep peroneal nerve','Superficial peroneal nerve','Tibial nerve','Sural nerve','Saphenous nerve','Lateral femoral cutaneous nerve'])]:
 exam('msk.ultrasound-nerves-'+region,'Ultrasound peripheral nerves — '+region.replace('-',' '),'Ultrasound','rad.5.marrow-muscle','ra.mri-muscle-disease',[side_control()]+[nerve(n) for n in names])

# Postoperative spine: region-specific levels and bilateral foramina; CT never asserts MR-only cord signal.
for region,levels in [('cervical',['C2–C3','C3–C4','C4–C5','C5–C6','C6–C7','C7–T1']),('thoracic',['T'+str(n)+'–T'+str(n+1) for n in range(1,12)]),('lumbar',['T12–L1','L1–L2','L2–L3','L3–L4','L4–L5','L5–S1'])]:
 rows=[choice('operation','Observed operative changes','Observed operative changes include',['decompression','discectomy','fusion','decompression and fusion','disc replacement'],'Operated levels',('essr',)),hardware()]
 for level in levels:
  for structure in ['disc / operative bed','central canal','right lateral recess','left lateral recess','right neural foramen','left neural foramen','right facet','left facet']:
   name=level+' '+structure
   rows += [row(slug(name),name,'Level '+level,name+': no focal compressive abnormality.',[f('stenosis','Stenosis',name+': [mild / moderate / severe] narrowing.'),f('material','Disc / scar',name+': [disc protrusion / disc extrusion / postoperative scar / indeterminate scar versus disc without contrast].'),f('root','Neural effect',name+': [contact without displacement / displacement / compression] of the adjacent neural structure.'),f('enhancement','Acquired contrast finding',name+': [homogeneous scar-like / peripheral disc-like / abnormal nodular] enhancement on acquired postcontrast images.')],('essr',))]
 rows += [row('collection','Postoperative collection','Complications','No focal postoperative collection.',[f('present','Collection','A [epidural / paraspinal / subcutaneous / operative-bed] collection is present.'),f('size','Dimensions','The collection measures __ × __ × __ mm.',['present']),f('effect','Effect','The collection causes [no neural compression / thecal sac compression / neural foraminal compression].',['present']),f('contrast','Acquired enhancement','The collection shows [no enhancement / thin rim enhancement / thick irregular rim enhancement] on acquired postcontrast images.',['present'])],('essr',),repeat=True),row('neural','Cord / conus / cauda equina','Neural structures','No focal abnormality of the imaged cord, conus or cauda equina.',[f('signal','Cord signal','[Focal / multilevel] cord T2 hyperintensity.'),f('clumping','Root clumping','Cauda equina roots show [central clumping / peripheral adherence / mass-like conglomeration].'),f('enhancement','Acquired enhancement','Abnormal neural enhancement on acquired postcontrast images.')],('essr',))]
 exam('msk.mri-spine-'+region+'-postoperative','MRI '+region+' spine — postoperative','MRI','rad.4.spine-imaging','ra.mri-myelopathy',rows)
rows=[choice('region','Acquired region','The postoperative CT covers the',['cervical spine','thoracic spine','lumbar spine','thoracolumbar spine'],refs=('essr',)),hardware(),row('fusion','Fusion assessment','Fusion',None,[f('bridging','Fusion morphology','The assessed fusion level shows [continuous bridging bone / partial bridging bone / no bridging bone / indeterminate bridging because of artefact].'),f('level','Assessed level','The assessed fusion level is [C2–C3 / C3–C4 / C4–C5 / C5–C6 / C6–C7 / C7–T1 / thoracic / T12–L1 / L1–L2 / L2–L3 / L3–L4 / L4–L5 / L5–S1].',['bridging']),f('subsidence','Subsidence','[No visible cage subsidence / endplate subsidence / cage migration] at the assessed level.',['bridging'])],('essr',),repeat=True,exclude=True),row('canal','Osseous canal and foramina','Neural corridors','No high-grade osseous canal or foraminal narrowing within the imaged operated region.',[f('narrowing','Narrowing','[Mild / moderate / severe] [central canal / right foraminal / left foraminal] osseous narrowing.'),f('cause','Cause','Narrowing is related to [osteophyte / heterotopic bone / displaced hardware / fracture fragment].',['narrowing'])],('essr',),repeat=True),row('soft-tissue','Paraspinal soft tissues','Complications','No focal paraspinal collection or destructive endplate change.',[f('collection','Collection','A paraspinal collection measures __ × __ × __ mm.'),f('endplate','Endplate change','[Focal / progressive] endplate destruction adjacent to the operated level.')],('essr',),repeat=True)]
exam('msk.ct-spine-postoperative','CT spine — fusion and hardware assessment','CT','rad.4.spine-imaging','ra.thoracolumbar-injury',rows)

# Common adult ultrasound and urinary CT.
def renal_rows(mod):
 rows=[]
 for side_name in ['right','left']:
  for part in ['renal parenchyma','collecting system','proximal ureter','distal ureter']:
   name=side_name.capitalize()+' '+part
   normal=name+(': no focal lesion or cortical thinning.' if part=='renal parenchyma' else ': no dilatation or visible calculus.')
   fs=[f('stone','Calculus',name+': a calculus is identified.'),f('stone-size','Calculus dimensions',name+': calculus measures __ × __ mm.',['stone']),f('dilatation','Dilatation',name+': [mild / moderate / severe] dilatation.'),f('mass','Mass',name+': a [solid / cystic / complex cystic] lesion measures __ × __ mm.'),f('scarring','Scarring',name+': [focal / multifocal / diffuse] cortical scarring.')]
   if mod=='CT':fs += [f('density','Calculus attenuation',name+': calculus mean attenuation __ HU.',['stone'])]
   rows += [row(slug(name),name,side_name.capitalize()+' urinary tract',normal,fs,('acr-parameters',),repeat=True)]
 rows += [row('bladder','Urinary bladder','Bladder','No focal bladder wall lesion or visible intraluminal calculus in the adequately distended bladder.',[f('limited','Underfilled','Bladder assessment is limited by underdistension.'),f('wall','Wall','[Diffuse / focal] bladder wall thickening.'),f('mass','Mass','A bladder mural lesion measures __ × __ mm.'),f('stone','Calculus','A bladder calculus measures __ mm.'),f('diverticulum','Diverticulum','A [right / left / posterior / anterior] bladder diverticulum is identified.')],('acr-parameters',),repeat=True)]
 return rows
rows=renal_rows('Ultrasound')
rows += [row('volumes','Bladder volumes','Bladder measurements',None,[f('prevoid','Prevoid volume','Measured prevoid bladder volume __ mL.'),f('postvoid','Postvoid residual','Measured postvoid residual bladder volume __ mL.')],('acr-parameters',),exclude=True)]
exam('us.renal-bladder','Ultrasound renal tract and bladder','Ultrasound','rad.4.kidney','ra.solid-renal-masses',rows)
exam('ct.kub','CT KUB — urinary calculi and obstruction','CT','rad.4.kidney','ra.solid-renal-masses',renal_rows('CT')+[row('secondary','Secondary signs','Obstruction','No perinephric or periureteric inflammatory change.',[f('stranding','Stranding','[Right / left / bilateral] [perinephric / periureteric] stranding.'),f('urinoma','Perirenal fluid','A [right / left] perirenal fluid collection is present.')],('acr-parameters',))])
rows=renal_rows('CT')
for side_name in ['right','left']:
 for part in ['upper calyces','interpolar calyces','lower calyces','renal pelvis','proximal ureter','middle ureter','distal ureter']:
  name=side_name.capitalize()+' '+part
  rows += [row('urothelial-'+slug(name),name+' urothelium','Excretory-phase assessment',None,[f('quality','Opacification',name+' is [fully opacified / partly opacified / unopacified / not covered].'),f('negative','No focal abnormality',name+': no filling defect or focal mural thickening on the diagnostic excretory images.'),f('defect','Filling defect',name+': [smooth / irregular] filling defect __ mm.'),f('thickening','Mural thickening',name+': [smooth / irregular / enhancing] mural thickening.'),f('stricture','Narrowing',name+': focal narrowing spanning __ mm.')],('acr-parameters',),exclude=True)]
exam('ct.urography','CT urography — renal and urothelial assessment','CT','rad.4.kidney','ra.solid-renal-masses',rows)
rows=[]
for name in ['Liver right lobe','Liver left lobe','Main portal vein','Gallbladder','Common bile duct','Pancreatic head','Pancreatic body','Pancreatic tail','Spleen','Abdominal aorta','Inferior vena cava']:
 rows += [row(slug(name),name,'Upper abdomen',name+': no focal abnormality within the visualised portion.',[f('not-seen','Limited visibility',name+': [partly visualised / obscured / not assessed].'),f('mass','Focal lesion',name+': a [solid / simple cystic / complex cystic / echogenic] lesion measures __ × __ mm.'),f('size','Measured dimension',name+': measured dimension __ mm.'),f('diffuse','Diffuse change',name+': [increased echogenicity / heterogeneous echotexture / coarse echotexture / irregular contour].'),f('flow','Acquired Doppler finding',name+': Doppler demonstrates [preserved directional flow / reversed flow / absent detected flow / turbulent flow].')],('acr-parameters',),repeat=True)]
rows += renal_rows('Ultrasound')+[row('free-fluid','Free fluid','Additional findings','No ascites in the examined recesses.',[f('fluid','Fluid','[Small / moderate / large] volume free fluid is identified.')],('acr-parameters',))]
exam('us.abdomen','Ultrasound abdomen — complete adult examination','Ultrasound','rad.3.acute-abdomen','ra.ultrasound-acute-abdomen',rows)
rows=[]
for side_name in ['right','left']:
 for part in ['testis','testicular perfusion','epididymal head','epididymal body','epididymal tail','spermatic cord','tunica vaginalis','inguinal canal']:
  name=side_name.capitalize()+' '+part
  normal=name+(': preserved intratesticular Doppler flow.' if part=='testicular perfusion' else ': no focal abnormality.')
  rows += [row(slug(name),name,side_name.capitalize()+' hemiscrotum',normal,[f('size','Dimensions',name+': measured dimensions __ × __ × __ mm.'),f('mass','Focal lesion',name+': a [solid / simple cystic / complex cystic / mixed] lesion measures __ × __ mm.'),f('echo','Echotexture',name+': [hypoechoic / hyperechoic / heterogeneous] appearance.'),f('flow','Doppler finding',name+': [increased flow / reduced flow / absent detected flow / indeterminate flow].'),f('torsion','Cord configuration',name+': a twisted cord configuration is identified.'),f('fluid','Fluid',name+': [simple / complex / septated] fluid.'),f('calcification','Calcification',name+': [punctate / coarse] calcification.')],('scrotum',),repeat=True)]
 rows += [row(side_name+'-varicocele',side_name.capitalize()+' pampiniform plexus',side_name.capitalize()+' hemiscrotum','No '+side_name+' varicocele on the performed assessment.',[f('veins','Venous diameter','Maximum '+side_name+' pampiniform venous diameter __ mm.'),f('reflux','Reflux','On performed Valsalva assessment there is [no reflux / brief reflux / sustained reflux].'),f('position','Position','Assessment performed [supine / erect / supine and erect].')],('scrotum',))]
exam('us.scrotum-adult','Ultrasound adult scrotum and testes','Ultrasound','rad.5.scrotum','ra.ultrasound-paediatric-scrotum',rows)

# Venous duplex: each named deep vein is independently assessed, including duplicated veins.
VENOUS={'lower-limb':['Common femoral vein','Saphenofemoral junction','Deep femoral vein proximal segment','Femoral vein proximal segment','Femoral vein middle segment','Femoral vein distal segment','Popliteal vein','Posterior tibial veins','Peroneal veins','Gastrocnemius veins','Soleal veins'],'upper-limb':['Internal jugular vein','Brachiocephalic vein visible segment','Subclavian vein','Axillary vein','Paired brachial veins','Radial veins','Ulnar veins','Cephalic vein','Basilic vein']}
for region,names in VENOUS.items():
 rows=[side_control()]
 for side_name in ['right','left']:
  for n in names:
   full=side_name.capitalize()+' '+n
   fs=[f('thrombus','Thrombus',full+': [acute-appearing / chronic post-thrombotic / indeterminate-age] [occlusive / nonocclusive] thrombus.'),f('compress','Compression',full+': [fully compressible / partly compressible / noncompressible / inaccessible to compression].'),f('flow','Flow',full+': [spontaneous phasic flow / continuous flow / reduced flow / no detected flow].'),f('limited','Assessment limitation',full+': [not visualised / partly visualised / obscured by dressing / obscured by oedema].'),f('duplication','Duplication',full+': duplicated venous segments are present.'),f('extension','Extent',full+': thrombus extends to the [proximal assessed limit / middle assessed segment / distal assessed limit].',['thrombus'])]
   compressible=not any(k in n for k in ['Subclavian','Brachiocephalic'])
   normal=full+(': compressible without visible thrombus.' if compressible else ': no visible thrombus with preserved Doppler flow in the assessed segment; compression is not feasible.')
   rows += [row(slug(full),full,side_name.capitalize()+' deep veins',normal,fs,('venous',))]
 rows += [row('superficial-thrombus','Superficial venous thrombosis','Superficial veins','No superficial thrombus in the examined symptomatic superficial veins.',[f('site','Site','Superficial thrombus involves the [right / left] [great saphenous vein / small saphenous vein / superficial tributary / cephalic vein / basilic vein].'),f('distance','Distance to deep junction','Thrombus is __ mm from the assessed deep venous junction.',['site']),f('length','Length','Thrombosed superficial segment length __ mm.',['site'])],('venous',),repeat=True),row('alternative','Alternative regional findings','Additional findings','No focal abnormality identified in the examined symptomatic soft tissues.',[f('finding','Finding','A [popliteal cyst / haematoma / soft-tissue oedema / lymph node / fluid collection] is identified in the symptomatic region.')],('venous',),repeat=True)]
 exam('us.venous-duplex-'+region,'Venous duplex — '+region.replace('-',' ')+' DVT','Ultrasound','rad.5.peripheral-vascular','ra.mra-peripheral-vessels',rows)
rows=[side_control(),choice('position','Performed assessment','Reflux assessment was performed',['standing','reverse Trendelenburg','supine'],'Technique',('venous',))]
for side_name in ['right','left']:
 for name in ['Common femoral vein','Femoral vein','Popliteal vein','Saphenofemoral junction','Great saphenous vein thigh','Great saphenous vein calf','Anterior accessory saphenous vein','Saphenopopliteal junction','Small saphenous vein','Calf perforators']:
  full=side_name.capitalize()+' '+name
  rows += [row(slug(full),full,side_name.capitalize()+' reflux map',full+': no reflux demonstrated on the performed manoeuvre.',[f('reflux','Reflux',full+': reflux demonstrated on [Valsalva / distal augmentation / release after distal compression].'),f('duration','Reflux duration',full+': reflux duration __ ms.',['reflux']),f('diameter','Diameter',full+': diameter __ mm.'),f('patency','Patency',full+': [patent / chronic post-thrombotic change / occluded].')],('venous',))]
exam('us.venous-insufficiency','Venous duplex — lower-limb reflux mapping','Ultrasound','rad.5.peripheral-vascular','ra.mra-peripheral-vessels',rows)

# Routine brain examinations retain anatomy and explicit modality limits.
for key,mod,title in [('mri','MRI','MRI brain — routine examination'),('ct','CT','CT brain — routine examination')]:
 rows=[]
 for side_name in ['right','left']:
  for structure in ['frontal lobe','parietal lobe','temporal lobe','occipital lobe','insula','basal ganglia','thalamus','cerebellar hemisphere']:
   name=side_name.capitalize()+' '+structure
   fs=[f('haemorrhage','Haemorrhage',name+': haemorrhage is identified.'),f('lesion','Focal lesion',name+': a focal [intra-axial / extra-axial] lesion is identified.'),f('oedema','Oedema',name+': [vasogenic / cytotoxic-pattern / indeterminate] oedema.'),f('chronic','Chronic injury',name+': [encephalomalacia / gliosis / old infarct] is identified.')]
   if mod=='MRI':fs += [f('diffusion','Diffusion',name+': restricted diffusion is present.'),f('signal','Signal',name+': [T2-FLAIR hyperintensity / susceptibility focus / T1 hyperintensity] is present.'),f('enhancement','Acquired enhancement',name+': [parenchymal / leptomeningeal / pachymeningeal] enhancement on acquired postcontrast images.')]
   else:fs += [f('attenuation','Attenuation',name+': [hypoattenuation / hyperattenuation / calcification] is identified.')]
   rows += [row(slug(name),name,'Brain parenchyma',name+': no focal abnormality on the acquired '+mod+' images.',fs,('acr-parameters',))]
 for name in ['Midbrain','Pons','Medulla','Ventricles','Basal cisterns','Extra-axial spaces','Calvarium','Included paranasal sinuses','Included mastoid air cells']:
  rows += [row(slug(name),name,'Additional structures',name+': no focal abnormality.',[f('finding','Abnormality',name+': [focal lesion / enlargement / compression / abnormal fluid / abnormal density or signal] is identified.')],('acr-parameters',))]
 rows += [row('mass-effect','Mass effect','Mass effect','No midline shift or herniation.',[f('shift','Midline shift','[Rightward / leftward] midline shift __ mm.'),f('herniation','Herniation','[Subfalcine / uncal / downward transtentorial / tonsillar] herniation is present.')],('acr-parameters',))]
 exam('neuro.'+key+'-brain-routine',title,mod,'rad.5.brain-anatomy','ra.brain-anatomy',rows)

# Dedicated lung screening, CT colonography and post-treatment neck surveillance.
rows=cloned('ra.ct-pulmonary-nodules')
rows += [choice('screen-context','Screening examination','This is a',['baseline screening LDCT','annual screening LDCT','short-interval screening follow-up'],'Screening',('lung-rads',)),choice('lung-rads-category','Reviewed Lung-RADS category','Clinician-reviewed Lung-RADS v2022 category is',['0','1','2','3','4A','4B','4X'],'Assessment',('lung-rads',)),choice('lung-rads-s','S modifier','Clinician-reviewed S modifier is',['present for significant non-lung-cancer finding','absent'],'Assessment',('lung-rads',))]
exam('chest.ct-lung-screening','Low-dose CT lung screening — Lung-RADS v2022','CT','rad.4.pulmonary-nodule','ra.ct-pulmonary-nodules',rows)
rows=[choice('prep','Bowel preparation','Preparation is',['adequate','partly limited by stool','partly limited by fluid','nondiagnostic'],'Technique',('c-rads',)),choice('distension','Distension','Colonic distension is',['adequate in both positions','adequate in one position','segmentally limited','nondiagnostic'],'Technique',('c-rads',))]
for name in ['Caecum','Ascending colon','Hepatic flexure','Transverse colon','Splenic flexure','Descending colon','Sigmoid colon','Rectum']:
 rows += [row(slug(name),name,'Colonic segments',name+': no polypoid lesion or suspicious mural mass on the diagnostic views.',[f('limited','Limited segment',name+': [poor distension / retained stool / retained fluid / motion] limits assessment.'),f('polyp','Polyp',name+': a [sessile / pedunculated / flat] polyp is identified.'),f('size','Polyp dimensions',name+': polyp measures __ × __ mm.',['polyp']),f('position','Polyp confirmation',name+': lesion is seen on [both acquired positions / one acquired position only].',['polyp']),f('mass','Mass / stricture',name+': [suspicious mural mass / indeterminate stricture / likely diverticular stricture].'),f('diverticula','Diverticulosis',name+': [mild / moderate / extensive] diverticulosis.')],('c-rads',),repeat=True)]
rows += [choice('c-rads-colonic','Colonic category','Clinician-reviewed C-RADS v2023 colonic category is',['C0','C1','C2a','C2b','C3','C4'],'Assessment',('c-rads',)),choice('c-rads-extra','Extracolonic category','Clinician-reviewed extracolonic category is',['E0','E1/E2','E3','E4'],'Assessment',('c-rads',)),row('extra','Extracolonic finding','Extracolonic findings','No clinically significant extracolonic finding within the limits of this examination.',[f('finding','Finding','A focal abnormality involves the [liver / gallbladder / pancreas / spleen / kidney / adrenal gland / aorta / pelvis / lung base / bone].'),f('size','Dimensions','The finding measures __ × __ mm.',['finding'])],('c-rads',),repeat=True)]
exam('ct.colonography','CT colonography — C-RADS v2023','CT','rad.5.gi-tumours-foreign-bodies','ra.ct-small-bowel-tumours',rows)
for modality in ['CT','MRI']:
 rows=[choice('treatment','Treatment context','Documented prior treatment is',['surgery','radiotherapy','chemoradiotherapy','surgery and radiotherapy','surgery and chemoradiotherapy'],'Treatment context',('ni-rads',)),choice('site','Treated primary site','The treated primary site is',['oral cavity','oropharynx','nasopharynx','hypopharynx','larynx','sinonasal cavity','salivary gland','unknown primary'],'Treatment context',('ni-rads',))]
 for name in ['Primary tumour bed','Reconstruction / flap','Mucosal surface','Deep treatment bed','Skull base','Perineural pathways','Carotid spaces','Airway']:
  rows += [row(slug(name),name,'Primary site and treatment bed',name+': expected post-treatment appearance without focal suspicious abnormality.',[f('change','Treatment change',name+': [diffuse oedema / non-mass-like fibrosis / flap-related change / surgical defect].'),f('suspicious','Suspicious finding',name+': [focal mucosal abnormality / focal nodular enhancement / discrete recurrent-appearing mass / new progressive asymmetry].'),f('size','Dimensions',name+': focal abnormality measures __ × __ mm.',['suspicious']),f('comparison','Reviewed comparison',name+': the finding is [new / increased / unchanged / decreased / resolved] on reviewed comparison.')],('ni-rads',))]
 for side_name in ['right','left']:
  for level in ['IA','IB','IIA','IIB','III','IV','VA','VB','VI','VII']:
   name=side_name.capitalize()+' level '+level
   rows += [row(slug(name),name,'Cervical nodes',name+': no suspicious node.',[f('node','Suspicious node',name+': [enlarged / necrotic / progressively enhancing / morphologically suspicious] node.'),f('size','Short axis',name+': node short axis __ mm.',['node']),f('change','Reviewed interval change',name+': [new / increased / unchanged / decreased / resolved] nodal abnormality.')],('ni-rads',),repeat=True)]
 rows += [choice('primary-category','Primary-site NI-RADS','Clinician-reviewed primary-site NI-RADS category is',['0','1','2a','2b','3','4'],'Assessment',('ni-rads',)),choice('nodal-category','Nodal NI-RADS','Clinician-reviewed nodal NI-RADS category is',['0','1','2','3','4'],'Assessment',('ni-rads',))]
 exam('neck.'+modality.lower()+'-post-treatment','Post-treatment head and neck '+modality+' — NI-RADS',modality,'rad.5.deep-neck-spaces','ra.head-neck-malignancy',rows)

# Refine region-specific anatomy rather than repeating grouped prompts.
hand=OUT['investigations']['xr.hand']
hand['sections']=xr_tech()+[bone(d+' '+p+' phalanx') for d in ['Index','Middle finger','Ring finger','Little finger'] for p in ['proximal','middle','distal']]+[bone('Thumb '+p+' phalanx') for p in ['proximal','distal']]+[bone(n+' metacarpal') for n in ['First','Second','Third','Fourth','Fifth']]+[joint(n+' CMC joint') for n in ['First','Second','Third','Fourth','Fifth']]+[joint(d+' MCP joint') for d in ['Thumb','Index','Middle finger','Ring finger','Little finger']]+[joint(d+' '+j+' joint') for d in ['Index','Middle finger','Ring finger','Little finger'] for j in ['PIP','DIP']]+[joint('Thumb IP joint'),xr_soft(),hardware()]
foot=OUT['investigations']['xr.foot']
old=foot['sections'];foot['sections']=[r for r in old if r['id'] not in ['included-phalanges','mtp-joints','interphalangeal-joints']]
foot['sections'] += [bone(d+' '+p+' phalanx') for d in ['Second toe','Third toe','Fourth toe','Fifth toe'] for p in ['proximal','middle','distal']]+[bone('Hallux '+p+' phalanx') for p in ['proximal','distal']]+[joint(d+' MTP joint') for d in ['First','Second','Third','Fourth','Fifth']]+[joint(d+' '+j+' joint') for d in ['Second toe','Third toe','Fourth toe','Fifth toe'] for j in ['PIP','DIP']]+[joint('Hallux IP joint')]
for identifier in ['msk.ultrasound-wrist','msk.ultrasound-hand']:
 inv=OUT['investigations'][identifier]
 if identifier.endswith('wrist'):
  remove=['First extensor compartment','Second extensor compartment','Third extensor compartment','Fourth extensor compartment','Fifth extensor compartment','Sixth extensor compartment','Finger flexor tendons']
  extra=['Abductor pollicis longus','Extensor pollicis brevis','Extensor carpi radialis longus','Extensor carpi radialis brevis','Extensor pollicis longus','Extensor digitorum','Extensor indicis proprius','Extensor digiti minimi','Extensor carpi ulnaris','Flexor pollicis longus']+[d+' flexor '+t for d in ['Index','Middle finger','Ring finger','Little finger'] for t in ['digitorum superficialis','digitorum profundus']]
  inv['sections']=[r for r in inv['sections'] if r['label'] not in remove]+[us_tendon(n) for n in extra]
 else:
  remove=['Digital collateral ligaments','Digital pulleys','Digital nerves']
  inv['sections']=[r for r in inv['sections'] if r['label'] not in remove]
  inv['sections'] += [us_ligament(d+' '+j+' '+s+' collateral ligament') for d in ['Index','Middle finger','Ring finger','Little finger'] for j in ['MCP','PIP','DIP'] for s in ['radial','ulnar']]
  inv['sections'] += [us_ligament(d+' '+p+' pulley') for d in ['Index','Middle finger','Ring finger','Little finger'] for p in ['A1','A2','A3','A4','A5']]+[us_ligament('Thumb '+p+' pulley') for p in ['A1','A2']]
  inv['sections'] += [nerve(d+' '+s+' digital nerve') for d in ['Thumb','Index','Middle finger','Ring finger','Little finger'] for s in ['radial','ulnar']]
# New postoperative descriptors cannot coexist with conflicting native normals.
for identifier,inv in OUT['investigations'].items():
 rowids={r['id'] for r in inv['sections']}
 for r in inv['sections']:
  for finding in r['findings']:
   if identifier=='msk.mri-shoulder-postoperative' and r['id'].startswith('repair-'):
    target=r['id'][7:]+'-tendon'
    if target in rowids:finding['invalidates_normal']=[target]
   if identifier=='msk.mri-knee-postoperative':
    targets=[]
    if r['id']=='graft-acl':targets=['acl']
    if r['id']=='graft-pcl':targets=['pcl']
    if r['id'] in ['repair-medial-meniscus','repair-lateral-meniscus']:
     prefix='medial-meniscus' if 'medial' in r['id'] else 'lateral-meniscus';targets=[k for k in rowids if k.startswith(prefix)]
    if r['id']=='cartilage-repair':targets=[k for k in rowids if 'cartilage' in k and k!='cartilage-repair']
    if targets:finding['invalidates_normal']=sorted(targets)
   if r['group']=='Tendons' and finding['id'] in ['partial','complete']:finding['exclusive_group']='tear-extent'
# Arthroplasty radiographs address each component and periprosthetic bone separately.
for joint_name,guide,base,components in [('knee','rad.5.knee','ra.mri-knee',['Femoral component','Tibial tray and stem','Patellar component']),('shoulder','rad.5.shoulder','ra.mri-shoulder',['Humeral component','Glenoid component / baseplate','Glenosphere or humeral head'])]:
 rows=xr_tech()
 for name in components:
  rows += [row(slug(name),name,'Arthroplasty components',name+': no visible breakage, migration or surrounding lucency.',[f('position','Position',name+': [migration / subsidence / tilt / malposition].'),f('integrity','Integrity',name+': [fracture / dissociation / wear-related change].'),f('interface','Interface',name+': [focal / progressive / circumferential] interface lucency.'),f('width','Lucency width',name+': interface lucency __ mm.',['interface']),f('cement','Cement mantle',name+': [intact / fractured / deficient] visible cement mantle.')],('acr-xr',))]
 rows += [joint('Prosthetic articulation'),bone('Periprosthetic bone'),row('ossification','Heterotopic ossification','Additional findings','No significant heterotopic ossification.',[f('present','Ossification','[Mild / moderate / extensive] heterotopic ossification.')],('acr-xr',)),xr_soft()]
 exam('xr.'+joint_name+'-arthroplasty',joint_name.capitalize()+' arthroplasty radiographs','Radiography',guide,base,rows)
# Tailor urinary descriptors to the structure and acquisition modality.
for iid in ['us.renal-bladder','ct.kub','ct.urography','us.abdomen']:
 for r in OUT['investigations'][iid]['sections']:
  if not any(r['id'].endswith(slug(part)) for part in ['renal parenchyma','collecting system','proximal ureter','distal ureter']):continue
  if 'renal-parenchyma' in r['id']:
   r['findings']=[x for x in r['findings'] if x['id'] not in ['stone','stone-size','density','dilatation']]
   r['findings'] += [f('length','Renal length',r['label']+': renal length __ mm.'),f('thickness','Cortical thickness',r['label']+': cortical thickness __ mm.')]
  else:
   r['findings']=[x for x in r['findings'] if x['id'] not in ['scarring','mass']]
   r['findings'] += [f('material','Luminal material',r['label']+': [echogenic material / clot-like material / focal mural lesion] is present.'),f('visibility','Visibility',r['label']+': [fully assessed / partly visualised / not visualised].')]
# Routine cervical/thoracic MRI uses complete level-specific native rows, without operated-site claims.
for region in ['cervical','thoracic']:
 inv=copy.deepcopy(OUT['investigations']['msk.mri-spine-'+region+'-postoperative'])
 rows=[r for r in inv['sections'] if r['id'] not in ['operation','hardware','collection']]
 for r in rows:
  r['label']=r['label'].replace('disc / operative bed','disc')
  for x in r['findings']:
   x['text']=x['text'].replace('disc / operative bed','disc').replace(' / postoperative scar / indeterminate scar versus disc without contrast',' / disc-osteophyte complex').replace('homogeneous scar-like / peripheral disc-like / abnormal nodular','peripheral / nodular / diffuse')
  if r['label'].endswith('facet'):
   r['normal']=r['label']+': no significant facet arthropathy or effusion.'
   r['findings']=[f('arthropathy','Arthropathy',r['label']+': [mild / moderate / severe] arthropathy.'),f('fluid','Effusion',r['label']+': an effusion is present.'),f('cyst','Synovial cyst',r['label']+': a synovial cyst measures __ mm.')]
 exam('neuro.mri-spine-'+region,'MRI '+region+' spine — degenerative assessment','MRI','rad.4.spine-imaging','ra.mri-myelopathy',rows)
# Keep the declared anatomy contract reproducible after refinements.
OUT['coverage']=[{'investigation_id':iid,'expected_anatomy_ids':[r['id'] for r in inv['sections']]} for iid,inv in OUT['investigations'].items()]

# Operated meniscal, cartilage and labral segments stay independently selectable.
shoulder=OUT['investigations']['msk.mri-shoulder-postoperative']
shoulder['sections']=[r for r in shoulder['sections'] if r['id']!='labral-repair']
for r in shoulder['sections']:
 if r['id']=='biceps-operation':
  for finding in r['findings']:finding['invalidates_normal']=['biceps-anchor','biceps-intraarticular','biceps-groove','biceps-position','biceps-pulley']
for key in ['superior','anterosuperior','anterior','anteroinferior','inferior','posteroinferior','posterior','posterosuperior']:
 target=key+'-labrum';name=key.capitalize()+' labral repair'
 shoulder['sections'] += [row('repair-'+target,name,'Labral repair',None,[f('assessment','Repair assessment',name+' is [intact in appearance / suspicious for recurrent detachment / limited by artefact].',bad=[target]),f('anchor','Anchor finding',name+': [no anchor complication / anchor migration / intra-articular protrusion / surrounding cystic change].',bad=[target])],('essr',),exclude=True)]
knee=OUT['investigations']['msk.mri-knee-postoperative']
knee['sections']=[r for r in knee['sections'] if r['id'] not in ['repair-medial-meniscus','repair-lateral-meniscus','cartilage-repair']]
for side_name in ['medial','lateral']:
 for segment in ['anterior-horn','body','posterior-horn','anterior-root','posterior-root']:
  target=side_name+'-meniscus-'+segment;name=side_name.capitalize()+' meniscus '+segment.replace('-',' ')+' surgery'
  knee['sections'] += [row('repair-'+target,name,'Meniscal surgery',None,[f('operation','Operative morphology',name+': [partial resection / repair / root fixation / transplant segment].',bad=[target]),f('assessment','Repair / residual assessment',name+': [no convincing recurrent tear / fluid-signal cleft reaching the articular surface / displaced residual fragment / discontinuity / indeterminate postoperative signal].',bad=[target])],('knee-post',),exclude=True)]
for target,name in [(r['id'],r['label']) for r in OLD['ra.mri-knee']['sections'] if 'cartilage' in r['id']]:
 knee['sections'] += [row('repair-'+target,name+' repair site','Cartilage repair',None,[f('fill','Defect fill',name+' repair shows [complete fill / partial fill / hypertrophic fill / delamination / exposed subchondral bone].',bad=[target]),f('integration','Integration',name+' repair margins are [integrated / partly separated / delaminated].',bad=[target]),f('bone','Repair bed',name+' repair bed shows [no oedema / marrow oedema / cysts / collapse].',bad=[target])],('essr',),exclude=True)]

# Calculation-bound examinations retain explicit applicability and never assign a
# category to an untouched or explicitly normal lesion block.
BIND={}
def bind(iid,section,calculator,label,trigger,inputs):
 BIND.setdefault(iid,{})[section]=[{'calculator_id':calculator,'label':label,'trigger_any':trigger,'inputs':inputs}]
 OUT['investigations'][iid]['calculator_ids']=[calculator]
def src(finding,slot=None,mapping=None,section=None,value=None):
 d={'finding_id':finding}
 if slot:d['slot_id']=slot
 if mapping is not None:d['map']=mapping
 if section:d['section_id']=section
 if slot is None:d['value']=value
 return d
def inp(*sources):return {'sources':list(sources)}
def enum_input(finding,values,section=None):return inp(src(finding,'slot-1',values,section))
def yn(id,label,text,parents=None,report=True):return f(id,label,text+' [present / absent].',parents,report=report)
Y={'present':True,'absent':False}
# O-RADS US v2022: each lesion has its own classification path.
iid='us.adnexal-orads'
rows=[choice('applicability','O-RADS applicability','Applicability is',['adnexal lesion appropriate for O-RADS assessment','not appropriate for O-RADS assessment'],'Assessment context',('orads',),False),choice('quality','Technical evaluation','Technical assessment is',['adequate for risk stratification','inadequate for risk stratification'],'Assessment context',('orads',),False),choice('menopause','Menopausal status','Reviewed menopausal status is',['premenopausal','early postmenopausal under five years','late postmenopausal five years or longer'],'Assessment context',('orads',)),choice('extraovarian','Suspicious extraovarian findings','Assessment of ascites and peritoneal nodules shows',['no suspicious extraovarian findings','findings explained by a reviewed alternative cause','suspicious unexplained ascites or peritoneal nodules'],'Extraovarian assessment',('orads',))]
for side_name in ['right','left']:
 rows += [row(side_name+'-ovary',side_name.capitalize()+' ovary','Ovaries',side_name.capitalize()+' ovary: no focal lesion identified.',[f('size','Ovarian dimensions',side_name.capitalize()+' ovary measures __ × __ × __ mm.'),f('unseen','Not visualised',side_name.capitalize()+' ovary is not visualised.'),f('absent','Surgically absent',side_name.capitalize()+' ovary is surgically absent.')],('orads',))]
patterns=[('simple','Simple cyst','simple_cyst'),('unilocular','Unilocular non-simple cyst','unilocular_nonsimple'),('bilocular','Bilocular cyst without solid tissue','bilocular_no_solid'),('multilocular','Multilocular cyst without solid tissue','multilocular_no_solid'),('unilocular-solid','Unilocular cyst with solid component','unilocular_with_solid'),('multilocular-solid','Bi- or multilocular cyst with solid component','bi_multilocular_with_solid'),('solid','Solid lesion','solid')]
classic=[('physiologic','Physiologic finding','physiologic'),('hemorrhagic','Typical haemorrhagic cyst','hemorrhagic'),('dermoid','Typical dermoid','dermoid'),('endometrioma','Typical endometrioma','endometrioma'),('paraovarian','Typical paraovarian cyst','paraovarian'),('inclusion','Typical peritoneal inclusion cyst','peritoneal_inclusion'),('hydrosalpinx','Typical hydrosalpinx','hydrosalpinx')]
fs=[f('lesion','Lesion location','An adnexal lesion is identified in the [right ovary / left ovary / right adnexa / left adnexa / midline adnexa].'),f('size','Maximum diameter','Maximum lesion diameter __ mm.',['lesion'])]
fs += [f(k,label,'The lesion is a '+label.lower()+'.',['lesion'],ex='morphology') for k,label,_ in patterns]
fs += [f(k,label,'The lesion has the reviewed typical appearance of a '+label.lower()+'.',['lesion'],ex='morphology') for k,label,_ in classic]
fs += [f('contour','Wall / outer contour','The assessed inner wall or solid-lesion outer contour is [smooth / irregular].',[k for k,_,_ in patterns]),f('color','Colour score','Reviewed intralesional colour score is [1 / 2 / 3 / 4].',['multilocular','multilocular-solid','solid']),f('shadow','Broad shadowing','[Broad acoustic shadowing is present / Broad acoustic shadowing is absent].',['solid']),f('papillary','Papillary projections','Number of papillary projections __.',['unilocular-solid']),f('classic-confirmed','Typical criteria confirmed','All applicable classic-lesion criteria have been explicitly reviewed and confirmed.',[k for k,_,_ in classic],report=False)]
fs.insert(-2,f('physiologic-review','Small simple-cyst assessment','Small simple-cyst assessment confirms a [physiologic follicle / nonphysiologic cyst].',['simple'],report=False))
next(x for x in fs if x['id']=='papillary')['slot_overrides']={'slot-1':{'label':'Papillary projections','minimum':0,'maximum':50,'type':'integer'}}
rows += [row('adnexal-lesion','Adnexal lesion','Lesions','No ovarian or adnexal lesion is identified in the assessed regions.',fs,('orads',),repeat=True)]
exam(iid,'Ultrasound adnexal lesions — calculated O-RADS US v2022','Ultrasound','rad.5.ovarian-orads','ra.ovarian-cysts',rows)
path_sources=[src(k,value='none') for k,_,_ in patterns]+[src(k,value=value) for k,_,value in classic]
inputs={'applicable_adnexal_lesion':enum_input('assessment',{'adnexal lesion appropriate for O-RADS assessment':True,'not appropriate for O-RADS assessment':False},'applicability'),'technically_adequate':enum_input('assessment',{'adequate for risk stratification':True,'inadequate for risk stratification':False},'quality'),'suspicious_ascites_or_peritoneal_nodules':enum_input('assessment',{'no suspicious extraovarian findings':False,'findings explained by a reviewed alternative cause':False,'suspicious unexplained ascites or peritoneal nodules':True},'extraovarian'),'classic_pattern':inp(*path_sources),'classic_criteria_confirmed':inp(src('classic-confirmed',value=True)),'menopausal_status':enum_input('assessment',{'premenopausal':'premenopausal','early postmenopausal under five years':'early_postmenopausal','late postmenopausal five years or longer':'late_postmenopausal'},'menopause'),'size_mm':inp(src('size','slot-1')),'morphology':inp(*[src(k,value=value) for k,_,value in patterns]),'contour':enum_input('contour',{'smooth':'smooth','irregular':'irregular'}),'color_score':enum_input('color',{str(n):n for n in range(1,5)}),'broad_shadowing':enum_input('shadow',{'Broad acoustic shadowing is present':True,'Broad acoustic shadowing is absent':False}),'papillary_projections':inp(src('papillary','slot-1')),'physiologic_finding_confirmed':enum_input('physiologic-review',{'physiologic follicle':True,'nonphysiologic cyst':False})}
# A simple cyst itself supplies its defining smooth contour, without an extra click.
inputs['contour']['sources'].append(src('simple',value='smooth'))
bind(iid,'adnexal-lesion','orads_us_2022','O-RADS US v2022',['lesion'],inputs)
# LI-RADS CT/MRI diagnostic categories; use the complete current liver anatomy.
iid='liver.lirads-calculated';rows=cloned('ra.liver-lirads')
fs=[f('lesion','Observation','A focal hepatic observation is identified in segment [I / II / III / IVa / IVb / V / VI / VII / VIII].'),f('eligibility','Reviewed eligibility','Reviewed observation applicability is [eligible untreated adult at risk / outside the diagnostic algorithm population / previously treated observation / pathologically proven observation].',['lesion'],report=False),f('quality','Technical adequacy','Categorisation on the acquired multiphasic images is [technically adequate / technically inadequate].',['lesion'],report=False),f('table','Major-feature table','Use the reviewed major-feature diagnostic pathway.',['lesion'],ex='pathway',report=False),f('benign','Definitely benign','The observation has definitely benign features.',['lesion'],ex='pathway'),f('probably-benign','Probably benign','The observation has probably benign features.',['lesion'],ex='pathway'),f('lr-m','Non-HCC-specific malignancy pattern','The observation has reviewed malignant features not specific for HCC.',['lesion'],ex='pathway'),f('tiv','Tumour in vein','Definite enhancing tumour in vein is present.',['lesion'],ex='pathway'),f('size','Observation size','Maximum observation diameter __ mm.',['lesion']),yn('aphe','Nonrim APHE','Nonrim arterial-phase hyperenhancement is',['table']),yn('washout','Nonperipheral washout','Nonperipheral washout is',['table']),yn('capsule','Enhancing capsule','An enhancing capsule is',['table']),yn('growth','Threshold growth','Reviewed LI-RADS v2018 threshold growth is',['table']),f('ancillary','Ancillary adjustment','Reviewed ancillary-feature adjustment is [none / upgrade by one category without establishing LR-5 / downgrade by one category].',['table'],report=False)]
for n,r in enumerate(rows):
 if r['id']=='hepatic-observation':rows[n]=row('hepatic-observation','Hepatic observation','Focal observations','No focal hepatic observation is identified on the acquired images.',fs,('lirads',),repeat=True)
exam(iid,'CT/MRI liver — calculated LI-RADS v2018','Multimodality','rad.5.liver' if 'rad.5.liver' in BASE['forms'] else 'rad.4.liver','ra.liver-lirads',rows)
bind(iid,'hepatic-observation','lirads_ct_mri_2018','LI-RADS CT/MRI v2018',['lesion'],{'eligible_untreated_adult':enum_input('eligibility',{'eligible untreated adult at risk':True,'outside the diagnostic algorithm population':False,'previously treated observation':False,'pathologically proven observation':False}),'technically_adequate':enum_input('quality',{'technically adequate':True,'technically inadequate':False}),'pathway':inp(src('table',value='major_features'),src('benign',value='definitely_benign'),src('probably-benign',value='probably_benign'),src('lr-m',value='lr_m'),src('tiv',value='tumor_in_vein')),'size_mm':inp(src('size','slot-1')),'nonrim_aphe':enum_input('aphe',Y),'nonperipheral_washout':enum_input('washout',Y),'enhancing_capsule':enum_input('capsule',Y),'threshold_growth':enum_input('growth',Y),'ancillary_adjustment':enum_input('ancillary',{'none':'none','upgrade by one category without establishing LR-5':'upgrade_one','downgrade by one category':'downgrade_one'})})
# Explicit reviewed case sums are separate from individual lesion measurements.
iid='oncology.recist-follow-up'
fs=[f('eligibility','RECIST eligibility','Reviewed RECIST applicability is [RECIST 1.1 applicable with valid target selection and measurements / RECIST 1.1 not applicable].',report=False),f('baseline','Reviewed baseline sum','Reviewed baseline target-lesion measurement sum __ mm.'),f('nadir','Reviewed nadir sum','Reviewed lowest prior case-level target measurement sum __ mm.'),f('current','Reviewed current sum','Reviewed current target-lesion measurement sum __ mm.'),f('target-cr','Target complete-response criteria','Target complete-response criteria are [met with disappearance of non-nodal targets and target nodes under 10 mm / not met].'),f('prior-cr','Prior complete response','A prior complete response was [confirmed / not confirmed].'),f('nontarget','Non-target disease','Reviewed non-target status is [no baseline non-target disease / complete response / persistent non-CR non-PD disease / unequivocal progression / not evaluable].'),yn('new','Unequivocal new lesions','Unequivocal new lesions are'),f('sd-duration','SD duration criterion','The protocol minimum duration for stable disease is [met / not met].',report=False)]
rows=[row('response','Reviewed response inputs','Response assessment',None,fs,('recist',),exclude=True),row('target-record','Target lesion record','Target measurements',None,[f('site','Target location','The target lesion is in the [lung / liver / lymph node / kidney / adrenal / soft tissue / bone with measurable soft-tissue component / other measured organ].'),f('axis','Measurement axis','The reviewed measurement axis is [long axis for a non-nodal lesion / short axis for a pathological node].',['site']),f('measurements','Measurements','Baseline __ mm; current __ mm.',['site']),f('organ-count','Reviewed target selection','Maximum five targets in total and two per organ were reviewed and confirmed.',['site'],report=False)],('recist',),repeat=True,exclude=True)]
exam(iid,'RECIST 1.1 — longitudinal time-point response','Reference','rad.4.oncology-response','ra.recist',rows)
bind(iid,'response','recist_1_1','RECIST 1.1 time-point response',['eligibility','baseline','nadir','current','new','nontarget'],{'recist_1_1_applicable':enum_input('eligibility',{'RECIST 1.1 applicable with valid target selection and measurements':True,'RECIST 1.1 not applicable':False}),'baseline_sum_mm':inp(src('baseline','slot-1')),'nadir_sum_mm':inp(src('nadir','slot-1')),'current_sum_mm':inp(src('current','slot-1')),'target_cr_confirmed':enum_input('target-cr',{'met with disappearance of non-nodal targets and target nodes under 10 mm':True,'not met':False}),'prior_cr_confirmed':enum_input('prior-cr',{'confirmed':True,'not confirmed':False}),'non_target_status':enum_input('nontarget',{'no baseline non-target disease':'none','complete response':'cr','persistent non-CR non-PD disease':'non_cr_non_pd','unequivocal progression':'unequivocal_pd','not evaluable':'not_evaluable'}),'unequivocal_new_lesions':enum_input('new',Y),'minimum_sd_duration_met':enum_input('sd-duration',{'met':True,'not met':False})})
iid='oncology.lesion-growth'
fs=[f('lesion','Lesion location','The compared lesion is in the [right lung / left lung / liver / kidney / adrenal / lymph node / soft tissue / other measured organ].'),f('comparable','Measurement comparability','Diameter measurements are [reviewed and comparable / not comparable].',['lesion'],report=False),f('prior','Prior diameter','Prior reviewed diameter __ mm.',['lesion']),f('current','Current diameter','Current reviewed diameter __ mm.',['lesion']),f('prior-volume','Prior measured volume','Prior measured volume __ mm³.',['lesion']),f('current-volume','Current measured volume','Current measured volume __ mm³.',['lesion']),f('vol-comparable','Volumetry comparability','Measured volumes are [reviewed and comparable / not comparable].',['prior-volume','current-volume'],report=False),f('interval','Reviewed interval','Reviewed comparison interval __ days.',['lesion'])]
exam(iid,'Lesion growth — diameter change and measured-volume doubling time','Reference','rad.4.pulmonary-nodule','ra.ct-pulmonary-nodules',[row('growth-lesion','Compared lesion','Longitudinal measurements',None,fs,('lung-rads',),repeat=True,exclude=True)])
bind(iid,'growth-lesion','lesion_growth','Lesion growth measurements',['lesion'],{'comparable_measurements_confirmed':enum_input('comparable',{'reviewed and comparable':True,'not comparable':False}),'prior_diameter_mm':inp(src('prior','slot-1')),'current_diameter_mm':inp(src('current','slot-1')),'prior_volume_mm3':inp(src('prior-volume','slot-1')),'current_volume_mm3':inp(src('current-volume','slot-1')),'interval_days':inp(src('interval','slot-1')),'comparable_volumetry_confirmed':enum_input('vol-comparable',{'reviewed and comparable':True,'not comparable':False})})
# Normal ovarian parenchyma does not exclude a separately characterised focal lesion.
for r in OUT['investigations']['us.adnexal-orads']['sections']:
 if r['id'] in ['right-ovary','left-ovary']:
  r['normal']=r['label']+': no diffuse abnormality in the visualised ovarian parenchyma.'
# Facet, recess and foraminal rows use findings specific to those structures.
for iid,inv in OUT['investigations'].items():
 if not (iid.startswith('msk.mri-spine-') or iid.startswith('neuro.mri-spine-')):continue
 for r in inv['sections']:
  if r['label'].endswith('facet'):
   r['normal']=r['label']+': no significant facet arthropathy or effusion.'
   r['findings']=[f('arthropathy','Arthropathy',r['label']+': [mild / moderate / severe] arthropathy.'),f('fluid','Effusion',r['label']+': an effusion is present.'),f('cyst','Synovial cyst',r['label']+': a synovial cyst measures __ mm.'),f('resection','Resection',r['label']+': postoperative partial resection.') ] if iid.startswith('msk.') else [f('arthropathy','Arthropathy',r['label']+': [mild / moderate / severe] arthropathy.'),f('fluid','Effusion',r['label']+': an effusion is present.'),f('cyst','Synovial cyst',r['label']+': a synovial cyst measures __ mm.')]
  elif any(k in r['label'] for k in ['lateral recess','neural foramen']):
   r['findings']=[x for x in r['findings'] if x['id'] not in ['material','enhancement']]
# Brain supporting structures have their own vocabulary rather than a generic lesion list.
for modality in ['ct','mri']:
 rows=OUT['investigations']['neuro.'+modality+'-brain-routine']['sections']
 definitions={
  'ventricles':('No hydrocephalus or intraventricular haemorrhage.',[f('dilatation','Dilatation','[Mild / moderate / marked] ventricular dilatation.'),f('pattern','Pattern','Ventricular enlargement is [communicating in pattern / obstructive in pattern / proportionate to volume loss / indeterminate].',['dilatation']),f('blood','Intraventricular blood','[Right / left / bilateral] intraventricular haemorrhage is present.')]),
  'basal-cisterns':('Basal cisterns are patent.',[f('effacement','Effacement','[Partial / complete] basal cisternal effacement.'),f('blood','Cisternal haemorrhage','Haemorrhage is present in the [suprasellar / interpeduncular / prepontine / ambient / quadrigeminal] cistern.')]),
  'extra-axial-spaces':('No extra-axial collection.',[f('collection','Collection','A [right / left / bilateral] [subdural / extradural / subarachnoid] abnormality is identified.'),f('thickness','Thickness','Maximum extra-axial collection thickness __ mm.',['collection'])]),
  'calvarium':('No focal calvarial abnormality within examination limits.',[f('lesion','Focal abnormality','A focal [destructive / sclerotic / expansile / postoperative] calvarial abnormality is identified.')]),
  'included-paranasal-sinuses':('Included paranasal sinuses show no significant opacification.',[f('mucosa','Mucosal thickening','[Mild / moderate / marked] mucosal thickening in the [maxillary / ethmoid / frontal / sphenoid] sinuses.'),f('fluid','Fluid','An air-fluid level is present in the [right maxillary / left maxillary / sphenoid / frontal] sinus.')]),
  'included-mastoid-air-cells':('No significant included mastoid opacification.',[f('fluid','Opacification','[Right / left / bilateral] mastoid opacification.')]),
 }
 for r in rows:
  if r['id'] in definitions:r['normal'],r['findings']=definitions[r['id']]
  if modality=='ct':
   for finding in r['findings']:
    if finding['id']=='oedema':finding['text']=r['label']+': [focal / diffuse] parenchymal swelling with reduced attenuation.'

# All additional IDs are stable and included once in the generated manifest.
OUT['coverage']=[{'investigation_id':iid,'expected_anatomy_ids':[r['id'] for r in inv['sections']]} for iid,inv in OUT['investigations'].items()]

# A unilateral duplex acquisition cannot attest to the opposite limb.
for iid in ['us.venous-duplex-lower-limb','us.venous-duplex-upper-limb','us.venous-insufficiency']:
 for r in OUT['investigations'][iid]['sections']:
  if r['id'].startswith(('right-','left-')):
   examined_side='right' if r['id'].startswith('right-') else 'left'
   r['requires_scope']={'section_id':'side','finding_id':'assessment','slot_id':'slot-1','values':[examined_side,'bilateral']}

# Acquisition choices are specific to the examination; no inferred views or load.
XR_VIEWS={
 'shoulder':['AP scapular-Y and axillary','AP and scapular-Y','AP internal and external rotation','AP only','axillary only'],
 'clavicle':['AP and cephalic-tilt','AP only'],
 'ac-joints':['bilateral AP','bilateral Zanca','bilateral stress views'],
 'elbow':['AP and lateral','AP lateral and oblique','dedicated radial-head views'],
 'wrist':['PA lateral and oblique','PA and lateral','dedicated scaphoid views','clenched-fist stress views'],
 'hand':['PA oblique and lateral','PA and oblique','bilateral comparison views'],
 'finger':['PA oblique and lateral','AP and lateral'],
 'pelvis':['AP pelvis','AP inlet and outlet','AP and Judet views'],
 'hip':['AP pelvis and lateral hip','AP and lateral hip','AP and frog-leg lateral hip','cross-table lateral hip'],
 'knee':['AP and lateral','AP lateral and skyline','weight-bearing AP lateral and skyline','weight-bearing AP lateral skyline and tunnel'],
 'ankle':['AP lateral and mortise','AP and lateral','stress mortise views'],
 'foot':['AP oblique and lateral','weight-bearing AP oblique and lateral','bilateral weight-bearing AP'],
 'toe':['AP oblique and lateral','AP and lateral'],
 'calcaneus':['axial and lateral','lateral only'],
 'sacroiliac':['AP and bilateral oblique','AP only'],
 'sacrum-coccyx':['AP and lateral','lateral only'],
 'ribs':['dedicated oblique rib views with chest radiograph','dedicated oblique rib views','single AP rib view'],
}
for iid,inv in OUT['investigations'].items():
 if not iid.startswith('xr.'):continue
 key=iid[3:]
 if key in XR_VIEWS:
  for index,r in enumerate(inv['sections']):
   if r['id']=='views':inv['sections'][index]=choice('views','Acquired projections','Acquired projections are',XR_VIEWS[key],refs=('acr-xr',))
 if key not in ['knee','ankle','foot','hip','pelvis','lower-limb-alignment','knee-arthroplasty']:
  inv['sections']=[r for r in inv['sections'] if r['id']!='weight-bearing']
OUT['coverage']=[{'investigation_id':iid,'expected_anatomy_ids':[r['id'] for r in inv['sections']]} for iid,inv in OUT['investigations'].items()]

# Keep structure-specific wording and modality limits explicit.
for iid,replacements in {
 'xr.elbow':{'Proximal ulna':'Proximal ulnar shaft'},
 'xr.ankle':{'Distal tibia':'Distal tibial metaphysis'},
 'xr.pelvis':{'Right ilium':'Right iliac wing','Left ilium':'Left iliac wing'},
}.items():
 for r in OUT['investigations'][iid]['sections']:
  old=r['label']
  if old not in replacements:continue
  new=replacements[old];r['label']=new;r['id']=slug(new)
  if r.get('normal'):r['normal']=r['normal'].replace(old,new)
  for finding in r['findings']:finding['text']=finding['text'].replace(old,new)
for iid,inv in OUT['investigations'].items():
 if iid.startswith('xr.'):
  for r in inv['sections']:
   if r['group']=='Joints' and r['label'] not in ['Ulnohumeral joint','Ankle mortise']:
    r['findings']=[x for x in r['findings'] if x['id']!='effusion']
for iid in ['xr.knee','xr.knee-arthroplasty']:
 OUT['investigations'][iid]['sections'].append(row('suprapatellar-effusion','Suprapatellar recess','Soft tissues','No visible suprapatellar effusion.',[f('effusion','Effusion','A [small / moderate / large] suprapatellar effusion is visible.')],('acr-xr',)))
for iid,inv in OUT['investigations'].items():
 if iid.startswith('msk.mri-spine-') and iid.endswith('postoperative'):
  for index,r in enumerate(inv['sections']):
   if r['id']=='hardware':
    inv['sections'][index]=row('hardware','Implants and susceptibility artefact','Postoperative findings',None,[f('configuration','Observed configuration','The MR-visible operative configuration is [posterior instrumentation / anterior instrumentation / interbody implant / disc replacement / combined instrumentation].'),f('artefact','Artefact','Implant-related artefact [does not substantially limit assessment / partly obscures the operated level / severely limits assessment].'),f('fluid','Peri-implant fluid','Peri-implant fluid is visible on the acquired sequences.'),f('marrow','Adjacent marrow','Adjacent marrow shows [oedema / fatty change / heterogeneous signal].')],('essr',),exclude=True)
 if iid.startswith('neuro.mri-spine-'):
  for r in inv['sections']:
   if r.get('normal'):r['normal']=r['normal'].replace('disc / operative bed','disc')
   for finding in r['findings']:
    if finding['label']=='Disc / scar':finding['label']='Disc contour'
 if iid in ['msk.mri-brachial-plexus','msk.mri-lumbosacral-plexus']:
  for r in inv['sections']:
   if 'root' not in r['label'].lower():
    for finding in r['findings']:
     if finding['id']=='continuity':finding['text']=finding['text'].replace(' / avulsed root','')
 if iid.startswith('msk.ultrasound-'):
  for r in inv['sections']:
   if r['label'] in ['Achilles tendon','Patellar tendon','Quadriceps tendon','Plantar fascia']:
    for finding in r['findings']:
     if finding['id']=='sheath':
      finding['label']='Surrounding tissues';finding['text']=r['label']+': [surrounding oedema / surrounding hyperaemia / adjacent tissue thickening].'
foot=OUT['investigations']['msk.ultrasound-foot']
for index,r in enumerate(foot['sections']):
 if r['group']=='Nerves' and 'intermetatarsal space' in r['label']:
  foot['sections'][index]=nerve('Common plantar digital nerve at the '+r['label'].lower())
# Scrotal perfusion, cord, tunica and epididymis do not share interchangeable findings.
for r in OUT['investigations']['us.scrotum-adult']['sections']:
 name=r['label'];key=r['id']
 if key.endswith('-testis'):
  r['findings']=[f('size','Testicular dimensions',name+' measures __ × __ × __ mm.'),f('lesion','Focal lesion',name+': a [solid / simple cystic / complex cystic / mixed] lesion measures __ × __ mm.'),f('texture','Echotexture',name+': [homogeneous / heterogeneous / diffusely hypoechoic] echotexture.'),f('calcification','Calcification',name+': [scattered punctate calcifications / diffuse microlithiasis / coarse calcification].')]
 elif key.endswith('-testicular-perfusion'):
  r['findings']=[f('flow','Doppler perfusion',name+': [preserved flow / increased flow / reduced flow / absent detected flow / technically indeterminate flow].'),f('spectral','Spectral assessment',name+': [preserved arterial and venous signals / high-resistance arterial signal / reversed diastolic arterial flow / absent venous signal].')]
 elif '-epididymal-' in key:
  r['findings']=[f('size','Size',name+': [normal size / mild enlargement / marked enlargement].'),f('lesion','Focal lesion',name+': a [simple cyst / complex cyst / solid lesion] measures __ × __ mm.'),f('flow','Doppler activity',name+': [normal / increased / indeterminate] Doppler activity.'),f('texture','Echotexture',name+': [homogeneous / heterogeneous / hypoechoic] echotexture.'),f('calcification','Calcification',name+': focal calcification.')]
 elif key.endswith('-spermatic-cord'):
  r['findings']=[f('twist','Cord configuration',name+': a [twisted / redundant without demonstrated twist] cord configuration.'),f('thickening','Thickening',name+': thickening and increased Doppler activity.'),f('lesion','Focal lesion',name+': a [fat-containing / solid / cystic] lesion measures __ × __ mm.')]
 elif key.endswith('-tunica-vaginalis'):
  r['findings']=[f('hydrocele','Fluid',name+': [small / moderate / large] [simple / complex / septated] fluid.'),f('wall','Tunical change',name+': [thickening / calcification / focal nodule].')]
 elif key.endswith('-inguinal-canal'):
  r['findings']=[f('hernia','Hernia',name+': a [fat-containing / bowel-containing] hernia is demonstrated.'),f('dynamic','Performed dynamic assessment',name+': the hernia is [reducible / partly reducible / non-reducible] on the performed manoeuvre.',['hernia']),f('testis','Testis location',name+': an inguinal testis is identified.'),f('mass','Focal lesion',name+': a focal lesion measures __ × __ mm.')]
for iid in ['ct.kub','ct.urography']:
 for r in OUT['investigations'][iid]['sections']:
  for finding in r['findings']:
   if finding['id']=='material':finding['text']=finding['text'].replace('echogenic material','soft-tissue attenuation material')
# Complete adult abdominal ultrasound: use organ-appropriate observations.
for r in OUT['investigations']['us.abdomen']['sections']:
 name=r['label'];key=r['id']
 if key.startswith('liver-'):
  r['normal']=name+': homogeneous parenchyma without a focal lesion in the visualised portion.'
  r['findings']=[f('texture','Parenchymal texture',name+': [increased echogenicity / coarse heterogeneous texture / nodular contour].'),f('lesion','Focal lesion',name+': a [simple cystic / complex cystic / solid hypoechoic / solid echogenic / heterogeneous] lesion measures __ × __ mm.'),f('visibility','Visibility',name+': [fully assessed / partly visualised / substantially obscured].')]
 elif key=='main-portal-vein':
  r['normal']='No main portal venous dilatation or visible thrombus.'
  r['findings']=[f('diameter','Diameter','Main portal vein diameter __ mm.'),f('flow','Performed Doppler assessment','On performed Doppler assessment portal flow is [hepatopetal / hepatofugal / bidirectional / not detected / technically indeterminate].'),f('thrombus','Thrombus','[Partial / occlusive] main portal venous thrombus is visible.')]
 elif key=='gallbladder':
  r['normal']='No gallbladder calculus, wall thickening or pericholecystic fluid.'
  r['findings']=[f('stones','Calculi','[Single / multiple] gallbladder calculi.'),f('sludge','Sludge','Gallbladder sludge is present.'),f('wall','Wall thickness','Gallbladder wall thickness __ mm.'),f('fluid','Pericholecystic fluid','Pericholecystic fluid is present.'),f('murphy','Performed sonographic Murphy assessment','Performed sonographic Murphy assessment is [positive / negative / indeterminate].'),f('polyp','Polypoid lesion','A gallbladder polypoid lesion measures __ mm.'),f('absent','Cholecystectomy','The gallbladder is surgically absent.')]
 elif key=='common-bile-duct':
  r['normal']='No visible bile-duct dilatation or common-duct calculus.'
  r['findings']=[f('diameter','Duct diameter','Common bile duct diameter __ mm.'),f('stone','Visible calculus','A visible common bile duct calculus measures __ mm.'),f('intrahepatic','Intrahepatic ducts','[Mild / moderate / severe] intrahepatic duct dilatation.'),f('visibility','Distal duct visibility','The distal common duct is [visualised / partly obscured / not visualised].')]
 elif key.startswith('pancreatic-'):
  r['normal']=name+': no focal abnormality in the visualised portion.'
  r['findings']=[f('lesion','Focal lesion',name+': a [solid / cystic / complex] lesion measures __ × __ mm.'),f('texture','Parenchymal texture',name+': [heterogeneous / hypoechoic / echogenic] parenchyma.'),f('calcification','Calcification',name+': calcification is visible.'),f('duct','Visible pancreatic duct',name+': visible pancreatic duct diameter __ mm.'),f('visibility','Visibility',name+': [fully visualised / partly visualised / not visualised].')]
 elif key=='spleen':
  r['normal']='The visualised splenic parenchyma is homogeneous without a focal lesion.'
  r['findings']=[f('length','Length','Maximum splenic length __ mm.'),f('lesion','Focal lesion','A [solid / simple cystic / complex cystic] splenic lesion measures __ × __ mm.'),f('texture','Echotexture','Heterogeneous splenic echotexture.')]
 elif key=='abdominal-aorta':
  r['normal']='The visualised abdominal aorta is not aneurysmally dilated.'
  r['findings']=[f('diameter','Maximum diameter','Maximum assessed aortic AP diameter __ mm.'),f('aneurysm','Aneurysm morphology','A [fusiform / saccular] aortic aneurysm is identified.'),f('thrombus','Mural thrombus','Mural thrombus is present within the assessed aortic segment.'),f('plaque','Atheroma','Aortic atheromatous plaque is visible.'),f('visibility','Visibility','The aorta is [fully assessed / partly visualised / substantially obscured].')]
 elif key=='inferior-vena-cava':
  r['normal']='No IVC dilatation in the visualised segment.'
  r['findings']=[f('calibre','Calibre','The assessed IVC is [dilated / small in calibre].'),f('thrombus','Visible thrombus','Visible IVC thrombus is present.'),f('flow','Performed Doppler assessment','Performed IVC Doppler assessment shows [preserved flow / altered flow / no detected flow / technically indeterminate flow].'),f('visibility','Visibility','The IVC is [visualised / partly visualised / not visualised].')]
OUT['coverage']=[{'investigation_id':iid,'expected_anatomy_ids':[r['id'] for r in inv['sections']]} for iid,inv in OUT['investigations'].items()]

# The imaged neural structures depend on the spinal region.
for iid,inv in OUT['investigations'].items():
 if not (iid.startswith('msk.mri-spine-') or iid.startswith('neuro.mri-spine-')):continue
 for r in inv['sections']:
  if r['id']!='neural':continue
  if 'cervical' in iid:
   r['normal']='No focal abnormality of the imaged cervical spinal cord.'
   r['findings']=[x for x in r['findings'] if x['id']!='clumping']
  elif 'thoracic' in iid:
   r['normal']='No focal abnormality of the imaged thoracic cord or included conus.'
   r['findings']=[x for x in r['findings'] if x['id']!='clumping']
  else:r['normal']='No focal abnormality of the imaged conus or cauda equina.'
# Each reconstruction tunnel has independent observations and measurements.
knee=OUT['investigations']['msk.mri-knee-postoperative']
for r in knee['sections']:
 if r['id'] in ['graft-acl','graft-pcl']:r['findings']=[x for x in r['findings'] if x['id'] not in ['tunnel','tunnel-size']]
for ligament in ['ACL','PCL']:
 for site in ['femoral','tibial']:
  name=ligament+' '+site+' tunnel'
  knee['sections'].append(row('graft-'+ligament.lower()+'-'+site+'-tunnel',name,'Reconstruction tunnels',None,[f('diameter','Diameter',name+': diameter __ mm.'),f('widening','Widening',name+': [no widening / mild widening / marked widening].'),f('cyst','Tunnel cyst',name+': a tunnel-related cyst is present.'),f('position','Reviewed position',name+': position is [expected / malpositioned / not confidently assessed].'),f('fixation','MR-visible fixation',name+': [expected MR appearance / displacement suspected / obscured by artefact].')],('essr',),exclude=True))
OUT['coverage']=[{'investigation_id':iid,'expected_anatomy_ids':[r['id'] for r in inv['sections']]} for iid,inv in OUT['investigations'].items()]

# Routine organ assessments and measurements are not lesion records. Keep focal
# findings repeatable in their own rows so dimensions can accompany a normal organ.
for iid in ['us.abdomen','us.renal-bladder','us.scrotum-adult','ct.kub','ct.urography']:
 inv=OUT['investigations'][iid];refined=[]
 for r in inv['sections']:
  if not r.get('repeatable'):
   if iid=='ct.urography' and r['id'].startswith('urothelial-'):
    negative=next((f for f in r['findings'] if f['id']=='negative'),None)
    if negative:r['normal']=negative['text'];r['findings']=[f for f in r['findings'] if f['id']!='negative']
   refined.append(r);continue
  parent=copy.deepcopy(r);parent.pop('repeatable',None);parent.pop('repeat_label',None)
  focal_ids={f['id'] for f in parent['findings'] if f['id'] in {'mass','lesion','stone','polyp','foreign-body'}}
  changed=True
  while changed:
   previous=set(focal_ids)
   focal_ids.update(f['id'] for f in parent['findings'] if set(f.get('requires_any',[])) & focal_ids)
   changed=focal_ids!=previous
  focal=[f for f in parent['findings'] if f['id'] in focal_ids]
  measurements=[f for f in parent['findings'] if f['id'] not in focal_ids and '__' in f['text'] and not f.get('requires_any')]
  measured_ids={f['id'] for f in measurements}
  parent['findings']=[f for f in parent['findings'] if f['id'] not in focal_ids | measured_ids]
  for finding in parent['findings']:
   if finding['id']=='dilatation':finding['text']=finding['text'].replace('[mild / moderate / severe] dilatation','[no / mild / moderate / severe] dilatation')
  refined.append(parent)
  if measurements:refined.append(row(parent['id']+'-measurements',parent['label']+' measurements',parent['group'],None,measurements,tuple(parent['source_ids']),exclude=True))
  if focal:
   for finding in focal:finding['invalidates_normal']=list(dict.fromkeys(finding.get('invalidates_normal',[])+[parent['id']]))
   child=row(parent['id']+'-focal-findings',parent['label']+' focal findings',parent['group'],None,focal,tuple(parent['source_ids']),repeat=True,exclude=True)
   child['repeat_label']='Calculus' if {'stone'}=={f['id'] for f in focal if not f.get('requires_any')} else 'Finding'
   refined.append(child)
 inv['sections']=refined
OUT['coverage']=[{'investigation_id':iid,'expected_anatomy_ids':[r['id'] for r in inv['sections']]} for iid,inv in OUT['investigations'].items()]

if __name__=='__main__':
 p=ROOT/'data/radiology/anatomic-additions-20261026.json';p.write_text(json.dumps(OUT,ensure_ascii=False,indent=2)+'\n')
 bindings_path=ROOT/'data/radiology/descriptor-calculation-bindings.json'
 bindings=json.loads(bindings_path.read_text());bindings['version']='2026-10-26';bindings['investigations'].update(BIND)
 bindings_path.write_text(json.dumps(bindings,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'new_examinations':len(OUT['investigations']),'structures':sum(len(x['sections']) for x in OUT['investigations'].values()),'radiographs':[k for k in OUT['investigations'] if k.startswith('xr.')]}))
