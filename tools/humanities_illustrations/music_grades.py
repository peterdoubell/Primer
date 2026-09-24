"""Original worked notation plates for the pre-undergraduate music pathway."""
import json
from functools import partial
from pathlib import Path
from .core import spec, panel, footer, BLUE, TEAL, PLUM, CORAL, GOLD, INK, INK_SOFT, PAPER_LIGHT
from .music_notation import staff, note, glyph, music_font, GLYPHS


def text(p,x,y,value,size=25,color=INK): p.text((x,y),value,size=size,anchor='mm',fill=color,bold=True)
def stave(p,x,y,width=570,clef='treble',gap=28):return staff(p,x,y,width,gap,clef)
def pitch_y(top,step,gap=28):return top+4*gap-step*gap/2

def heading(p,title,subtitle):
 text(p,800,226,title,29)
 text(p,800,266,subtitle,23,INK_SOFT)
def explain(p,value):p.wrapped_text((150,710,1450,794),value,size=25,fill=INK,line_gap=7)

def grade1(p):
 heading(p,'G MAJOR: ONE SHARP, EIGHT SCALE NOTES','G  A  B  C  D  E  F-sharp  G')
 stave(p,145,390,1300)
 glyph(p,'sharp',280,390,28)
 for i,step in enumerate(range(2,10)):
  x=405+i*130;y=pitch_y(390,step)
  # Upper stems turn down at or above the middle line.
  note(p,x,y,28,stem='down' if step>=4 else True,color=TEAL if i==6 else BLUE)
  text(p,x+16,610,str(i+1),23)
 explain(p,'The signature sharpens every F unless cancelled. Count letters before accidentals: G major uses G, A, B, C, D, E and F-sharp, then returns to G.')
 footer(p,'Scale degrees describe function: 1–3–5 gives the tonic triad G–B–D.')

def grade2(p):
 heading(p,'A MINOR: COMPARE THE SEVENTH DEGREE','Natural minor uses G; harmonic minor uses G-sharp.')
 for x,label,sharp in [(140,'NATURAL MINOR',False),(850,'HARMONIC MINOR',True)]:
  text(p,x+265,330,label)
  stave(p,x,390,575)
  # E4 F4 G4 A4: the sixth and seventh retain their letter names.
  for i,step in enumerate([0,1,2,3]):
   xx=x+150+i*110;y=pitch_y(390,step)
   if sharp and i==2:glyph(p,'sharp',xx-42,y,28)
   note(p,xx,y,28,color=TEAL if i==2 else BLUE)
  text(p,x+280,542,'E   F   '+('G-sharp' if sharp else 'G')+'   A',24)
 ends=[]
 for xx in [425,535,645]:ends.append(note(p,xx,642,16,color=TEAL))
 p.draw.line((ends[0],586,ends[-1],586),fill=TEAL,width=7)
 text(p,553,570,'3',23,TEAL)
 ends2=[note(p,xx,642,16,color=BLUE) for xx in [1040,1170]]
 p.draw.line((ends2[0],586,ends2[-1],586),fill=BLUE,width=7)
 text(p,800,620,'=',32)
 text(p,800,683,'Three triplet quavers = the duration of two ordinary quavers',23)
 explain(p,'The key signature remains empty in A minor. A raised seventh needs an accidental: it creates the semitone G-sharp–A and changes the dominant from E minor to E major.')
 footer(p,'A minor and C major share a signature, but cadences and melodic emphasis establish different tonics.')

def grade3(p):
 heading(p,'SIX QUAVERS: TWO DIFFERENT METRES','Equal written duration does not imply the same grouping.')
 for x,label,groups in [(145,'3/4: THREE CROTCHET BEATS',[2,2,2]),(850,'6/8: TWO DOTTED-CROTCHET BEATS',[3,3])]:
  text(p,x+260,338,label,23)
  positions=[]
  for i in range(6):
   xx=x+60+i*78;positions.append(note(p,xx,525,26,color=BLUE))
  index=0
  for group in groups:
   p.draw.line((positions[index],434,positions[index+group-1],434),fill=BLUE,width=9)
   center=(positions[index]+positions[index+group-1])/2
   text(p,center,614,'beat '+str(index//group+1),22,TEAL);index+=group
 explain(p,'In 3/4, count 1-and 2-and 3-and. In 6/8, count 1-la-li 2-la-li. Beam groups show the pulse; they are not merely decorative joins between stems.')
 footer(p,'Try clapping the same six notes with the two different accent patterns before reading a new phrase.')

def grade4(p):
 heading(p,'MIDDLE C: SAME PITCH, THREE CLEFS','Clef changes move the written position, not the sounding note.')
 for x,clef,label,step in [(140,'treble','TREBLE',-2),(615,'alto','ALTO',4),(1090,'bass','BASS',10)]:
  text(p,x+165,330,label)
  stave(p,x,450,365,clef,26)
  y=pitch_y(450,step,26);xx=x+190
  if step in [-2,10]:p.draw.line((xx-12,y,xx+44,y),fill=INK,width=3)
  note(p,xx,y,26,stem='down' if step>=4 else True,color=TEAL)
  text(p,x+190,650,'C4',26,TEAL)
 explain(p,'The alto clef points to middle C on the third line. Rewriting at the same pitch is different from transposing an octave: check both the note name and its register.')
 footer(p,'Treble anchors G4; bass anchors F3; the C clef anchors C4.')

def grade5(p):
 heading(p,'READ THE CLEF, THEN NAME THE BASS','Four clefs locate the same C4; inversion follows the chord’s lowest note.')
 for x,clef,label,step in [(140,'treble','TREBLE',-2),(480,'bass','BASS',10),(820,'alto','ALTO',4),(1160,'tenor','TENOR',6)]:
  text(p,x+135,310,label,22)
  stave(p,x,370,285,clef,20)
  xx=x+165;y=pitch_y(370,step,20)
  if step in [-2,10]:p.draw.line((xx-10,y,xx+38,y),fill=INK,width=2)
  note(p,xx,y,20,stem='down' if step>=4 else True,color=PLUM)
 for x,label,steps,bass in [(145,'ROOT POSITION',[0,2,4],'C'),(615,'FIRST INVERSION',[2,4,7],'E'),(1085,'SECOND INVERSION',[4,7,9],'G')]:
  text(p,x+165,527,label,22)
  stave(p,x,592,375,'bass',20)
  for step in steps:
   y=pitch_y(592,step+3,20);xx=x+192
   if step+3>=10:
    for ledger in range(10,step+4,2):p.draw.line((xx-10,pitch_y(592,ledger,20),xx+44,pitch_y(592,ledger,20)),fill=INK,width=2)
   note(p,xx,y,20,kind='whole',stem=False,color=TEAL)
  text(p,x+184,708,'Bass: '+bass,23)
 p.wrapped_text((150,748,1450,796),'C, E and G remain the chord tones. The bass determines inversion; clef and upper spacing are separate questions.',size=25,fill=INK,line_gap=7)
 footer(p,'Tenor clef places C4 on the fourth line. Alto clef places it on the third.')


def grade6(p):
 heading(p,'V7 RESOLVES TO I: TRACK THE TENDENCY TONES','Original C-major voice-leading sketch; inner fifth omitted in V7.')
 for x,label,pitches in [(300,'G7: G–B–F',[(1,'B4'),(4,'F4')]),(1010,'C MAJOR: C–C–E',[(0,'C5'),(5,'E4')])]:
  text(p,x+120,325,label,24)
  stave(p,x-115,400,465)
  for position,name in pitches:
   # Treble top F5; each diatonic step is half a staff space.
   y=400+position*14+42
   note(p,x+120,y,28,kind='whole',stem=False,color=TEAL)
   text(p,x+290,y,name,22)
 p.arrow((675,456),(860,442),fill=TEAL,width=5,head=16)
 p.arrow((675,498),(860,512),fill=CORAL,width=5,head=16)
 text(p,785,390,'B rises to C',24,TEAL);text(p,785,590,'F falls to E',24,CORAL)
 explain(p,'The leading note B tends to rise to C; the chordal seventh F tends to fall to E. Read these notes against a bass moving G–C, then check spacing and the other voices in a full realisation.')
 footer(p,'Figured bass names intervals above the bass. It does not replace melodic voice-leading.')

def grade7(p):
 heading(p,'A 4–3 SUSPENSION: PREPARE, HOLD, RESOLVE','C is consonant over F, held over G, then resolves to B.')
 stave(p,180,388,1250,'treble',22)
 stave(p,180,545,1250,'bass',22)
 xs=[390,830,1250]
 for x,title,upper,bass in zip(xs,['PREPARATION','SUSPENSION','RESOLUTION'],['C5','C5','B4'],['F3','G3','G3']):
  text(p,x+15,325,title,23)
  uy=388+(1.5 if upper=='C5' else 2)*22
  note(p,x,uy,22,kind='half',stem='down',color=TEAL)
  by=545+(1 if bass=='F3' else .5)*22
  note(p,x,by,22,kind='half',stem='down',color=BLUE)
  text(p,x+15,680,upper+' / '+bass,22)
 p.draw.arc((404,416,844,456),0,180,fill=TEAL,width=4)
 explain(p,'Check the harmony on both sides of the tie. Preparation and stepwise resolution make the dissonance accountable; a tied note is not automatically a suspension.')
 footer(p,'The 4 and 3 describe intervals above G; they are not chord numbers.')

def grade8(p):
 heading(p,'THREE PARTS: TWO TREBLE LINES AND CONTINUO','Original phrase skeleton in C; separate the voices before analysing the whole.')
 for row,(clef,label,steps) in enumerate([('treble','TREBLE 1',[7,8,9,7]),('treble','TREBLE 2',[5,6,7,5]),('bass','CONTINUO',[3,4,3,3])]):
  top=330+row*120;stave(p,390,top,980,clef,20)
  for yy in [top+20,top+60]:p.draw.text((510,yy),'\ue084',font=music_font(20),fill=INK,anchor='ls')
  text(p,235,top+40,label,24)
  for i,step in enumerate(steps):
   xx=615+i*205;y=pitch_y(top,step,20)
   note(p,xx,y,20,stem='down' if step>=4 else True,color=[BLUE,TEAL,PLUM][row])
  p.draw.line((1370,top,1370,top+80),fill=INK,width=4)
  if row==2:
   for i in range(4):text(p,628+i*205,682,'5/3',18,PLUM)
 explain(p,'Read one melodic line at a time, then the bass and harmonic rhythm. A complete trio-sonata continuation needs independent rhythm, controlled dissonance, imitation and cadential direction beyond this consonant skeleton.')
 footer(p,'“Trio” refers to the three principal parts; continuo realisation may involve more than one performer.')

DRAWERS=[grade1,grade2,grade3,grade4,grade5,grade6,grade7,grade8]
DESCRIPTIONS=[
('An engraved G-major scale carries an F-sharp key signature and numbered degrees.','Each letter occurs once; the signature supplies F-sharp, and degrees 1–3–5 form the tonic triad.'),
('Two engraved E–F–G–A fragments compare G with G-sharp in A harmonic minor; a beamed triplet equals the duration of two ordinary quavers.','Harmonic minor changes the seventh degree with an accidental; the relative-major key signature stays the same.'),
('Six engraved quavers are beamed in three pairs for 3/4 and two groups of three for 6/8.','Equal total note values can organise different pulses: three simple beats versus two compound beats.'),
('Proper treble, alto and bass clefs locate middle C on matching staves with ledger lines where needed.','A change of clef changes the notation position; a change of octave changes the sounding register.'),
('Treble, bass, alto and tenor clefs locate C4; C-major chord tones then appear over C, E and G in three engraved bass-clef inversions.','The bass identifies root position, first inversion or second inversion; upper spacing is a separate choice.'),
('Two engraved treble staves show B4 rising to C5 and F4 falling to E4 in a dominant-seventh resolution.','Hear the leading note and chordal seventh resolve in context, then check a complete four-part setting.'),
('Paired engraved staves show C5 over F3, a tied C5 over G3, and its downward resolution to B4 over G3.','A suspension needs preparation, dissonance and resolution, not merely a note tied across a bar line.'),
('Two engraved treble parts and a bass-clef continuo part present a short original consonant phrase skeleton.','A complete continuation develops independent melodic lines within a harmonic and stylistic plan.')]
SPECS={}
for node in json.loads((Path(__file__).resolve().parents[2]/'data/curriculum/09-arts.json').read_text())['nodes']:
 if node.get('music_grade'):
  g=node['music_grade'];alt,caption=DESCRIPTIONS[g-1]
  SPECS[node['id']]=spec(node['id'],node['title'],node['stage'],'arts',node['id'].replace('.','-')+'-engraved',alt,caption,DRAWERS[g-1])

SHORT_TITLES = ['Pitch and Major Keys', 'Minor Keys and Triplets', 'Compound Metre', 'Clefs and Harmony', 'Fluent Score Reading', 'Four-Part Harmony', 'Chromatic Harmony', 'Counterpoint and Style']
for i, item in enumerate(SPECS.values()):
 item['display_title'] = 'Music Grade ' + str(i + 1) + ': ' + SHORT_TITLES[i]
