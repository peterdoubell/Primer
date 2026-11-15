"""Focused comparison plates; original schematics, never simulated patient scans."""
from pathlib import Path
import math
from PIL import Image
from .core import RadiologyPlate, BLUE, TEAL, CORAL, INK, INK_SOFT, PAPER_LIGHT, GOLD, illustration_entry

SPECS = {
 'rad.5.intracranial-haemorrhage': dict(id='rad.5.haemorrhage-compartments',stage=5,title='Blood: locate the compartment',mode='compare',
  takeaway='Locate blood relative to skull, brain surface and parenchyma before naming the haemorrhage pattern.',
  items=[dict(label='Extra-axial blood',detail='Epidural blood lies between skull and dura; subdural blood lies between dura and arachnoid. Lens and crescent are useful typical shapes, not infallible diagnoses.'),dict(label='Subarachnoid blood',detail='Blood follows CSF spaces in sulci and cisterns; this simplified example highlights cortical sulci.'),dict(label='Intraparenchymal blood',detail='Blood lies within brain tissue. The diagrams show location only, without mass effect, age-related attenuation or cause.')]),
 'rad.4.hrct': dict(id='rad.5.lung-opacity-comparison',stage=5,title='Lung opacity: what stays visible?',mode='compare',
  takeaway='Ground-glass opacity preserves underlying vessel margins; consolidation obscures them, while air-filled bronchi may remain visible.',
  items=[dict(label='Reference lung',detail='The same schematic vessels and branching air-filled bronchus provide a reference in all three panels.'),dict(label='Ground-glass opacity',detail='Increased lung attenuation leaves vessel and bronchial margins visible. This describes an appearance, not a cause.'),dict(label='Consolidation',detail='Denser air-space opacity obscures vessel margins. A patent air-filled bronchus may remain visible as an air bronchogram; it is not obligatory.')]),
 'rad.4.liver': dict(id='rad.5.liver-phase-comparison',stage=5,title='Liver enhancement: compare the phases',mode='compare',
  takeaway='Track the same lesion across phases and compare it with liver and blood pool; one bright phase does not establish a diagnosis.',
  items=[dict(label='No enhancement',detail='A simple-cyst pattern stays unenhanced as the surrounding liver enhances; simple-fluid morphology and attenuation must also agree.'),dict(label='Peripheral nodular fill-in',detail='A typical haemangioma begins with discontinuous peripheral nodules matching blood pool, with progressive centripetal fill-in. Not every haemangioma fills completely.'),dict(label='Arterial enhancement then relative washout',detail='The lesion is brighter than liver arterially and darker than liver later. This pattern alone does not diagnose HCC; population, lesion features and contrast agent matter.')]),
}

def panel(p, box, title, color=BLUE):
 p.card(box,fill=PAPER_LIGHT,outline=color,width=3,radius=20)
 p.text(((box[0]+box[2])/2,box[1]+38),title,size=26,bold=True,fill=INK,anchor='mm')

def note(p,box,text): p.wrapped_text(box,text,size=25,fill=INK_SOFT,line_gap=8)
def ellipse(p,box,fill,outline=BLUE,width=3): p.draw.ellipse(box,fill=fill,outline=outline,width=width)

def haemorrhage(p):
 labels=['EPIDURAL','SUBDURAL','SUBARACHNOID','INTRAPARENCHYMAL']
 details=['Between skull and dura. Typically lens-shaped.','Between dura and arachnoid. Typically crescent-shaped.','Along CSF spaces. Here: cortical sulci.','Within brain tissue. Here: a deep focal collection.']
 for i,(label,detail) in enumerate(zip(labels,details)):
  x=100+i*355; cx=x+165;cy=435
  panel(p,(x,205,x+330,785),label)
  ellipse(p,(cx-125,cy-165,cx+125,cy+165),'#dbd6c7',INK)
  ellipse(p,(cx-111,cy-151,cx+111,cy+151),'#e7eeeb',BLUE)
  p.draw.line((cx,cy-139,cx,cy+139),fill='#a4b5b1',width=3)
  for side in [-1,1]:
   p.draw.arc((cx+side*45-23,cy-28,cx+side*45+23,cy+28),40,320,fill='#a4b5b1',width=3)
  if i in [0,1]:
   reach=1.04 if i==0 else 1.42
   angles=[-reach+2*reach*j/60 for j in range(61)]
   outer=[(cx+109*math.cos(a),cy+149*math.sin(a)) for a in angles]
   # Both arcs meet at the ends. The broader subdural footprint hugs the convexity.
   thickness=75 if i==0 else 22
   inner=[(xx-thickness*math.sin(math.pi*j/60),yy) for j,(xx,yy) in enumerate(outer)]
   p.draw.polygon(outer+list(reversed(inner)),fill=CORAL)
  elif i==2:
   for side in [-1,1]:
    for dy in [-85,-25,45]:
     pts=[(cx+side*98,cy+dy),(cx+side*76,cy+dy+9),(cx+side*85,cy+dy+28),(cx+side*59,cy+dy+36)]
     p.draw.line(pts,fill=CORAL,width=12,joint='curve')
  else: ellipse(p,(cx+14,cy-45,cx+74,cy+34),CORAL,CORAL)
  note(p,(x+20,630,x+310,765),detail)
 note(p,(110,817,1490,905),'Schematic axial locations, anterior at top. Coral marks blood, not measured CT density. Shape supports localisation; inspect the full scan, mass effect and clinical context.')

def lung(p):
 for i,label in enumerate(['REFERENCE LUNG','GROUND-GLASS OPACITY','CONSOLIDATION']):
  x=100+i*480; panel(p,(x,205,x+440,790),label)
  box=(x+30,300,x+410,585)
  p.draw.rounded_rectangle(box,radius=24,fill=['#506671','#849595','#c9d2cc'][i])
  # Identical vessel tree. Dense consolidation removes its visible contrast.
  if i<2:
   for branch in [[(x+72,550),(x+193,430),(x+230,330)],[(x+193,430),(x+344,372)],[(x+145,475),(x+80,377)],[(x+264,406),(x+325,480)]]:
    p.draw.line(branch,fill='#f0eee3',width=12,joint='curve')
  for branch in [[(x+345,540),(x+267,470),(x+249,341)],[(x+267,470),(x+363,425)]]:
   p.draw.line(branch,fill='#354c59',width=19,joint='curve')
  texts=['Vessel margins and air-filled bronchus are clear.','Vessel margins remain visible through increased opacity.','Vessel margins are obscured. A dark air bronchogram remains.']
  note(p,(x+25,625,x+415,750),texts[i])
 note(p,(110,825,1490,915),'Matched schematic regions, not patient CT images. An air bronchogram is optional in consolidation. Neither ground-glass opacity nor consolidation names the underlying disease.')

def liver(p):
 phases=['ARTERIAL','PORTAL VENOUS','DELAYED']
 for j,phase in enumerate(phases): p.text((710+295*j,225),phase,size=25,bold=True,anchor='mm')
 rows=['NO ENHANCEMENT','NODULAR FILL-IN','RELATIVE WASHOUT']
 for i,label in enumerate(rows):
  y=350+i*190
  p.text((115,y-23),label,size=25,bold=True,fill=INK)
  desc=['Simple-cyst pattern','Typical haemangioma pattern','Interpret in the eligible context'][i]
  note(p,(115,y+17,500,y+90),desc)
  for j in range(3):
   cx=710+295*j; bg=['#bbc5bd','#94aaa5','#a4b5ac'][j]; blood=['#edf5dc','#d4e8ce','#d1dfc6'][j]
   ellipse(p,(cx-115,y-76,cx+115,y+76),bg,BLUE)
   ellipse(p,(cx-85,y-18,cx-51,y+16),blood,TEAL,2)
   lesion=['#657c84','#687b84','#edf5dc'][i] if j==0 else (['#657c84','#687b84','#657c84'][i])
   ellipse(p,(cx-31,y-47,cx+63,y+47),lesion,INK,2)
   if i==1:
    if j==2: ellipse(p,(cx-28,y-44,cx+60,y+44),blood,blood,1)
    else:
     for t in [-2.35,-.8,.8,2.35]:
      r=35 if j==0 else 25; rr=12 if j==0 else 24
      px=cx+16+r*math.cos(t);py=y+r*math.sin(t)
      ellipse(p,(px-rr,py-rr,px+rr,py+rr),blood,blood,1)
   if i==0 and j==0:
    p.text((cx-69,y+97),'blood pool',size=20,anchor='mm',fill=INK_SOFT)
    p.text((cx+25,y+97),'lesion',size=20,anchor='mm',fill=INK_SOFT)
 p.wrapped_text((110,820,1490,895),'Schematic extracellular-contrast patterns, not calibrated HU. Small circle = blood pool. Washout alone does not diagnose HCC; hepatobiliary-phase darkness is not washout.',size=24,fill=INK_SOFT,line_gap=7)

RENDERERS={'rad.5.intracranial-haemorrhage':haemorrhage,'rad.4.hrct':lung,'rad.4.liver':liver}

def render_all(root: Path):
 outputs=[]
 for node,item in SPECS.items():
  p=RadiologyPlate(item['id'],item['title'],5);RENDERERS[node](p)
  directory=root/'forest'/'radiology';directory.mkdir(parents=True,exist_ok=True)
  for width in [1600,800]:
   dest=directory/(item['id'].replace('.','-')+'-'+str(width)+'.webp')
   im=p.image if width==1600 else p.image.resize((800,500),Image.Resampling.LANCZOS)
   im.save(dest,'WEBP',quality=86 if width==1600 else 84,method=6);outputs.append(dest)
 return outputs

def entries(): return {node:illustration_entry(item) for node,item in SPECS.items()}
