"""Music engraving using Bravura's SMuFL glyphs (SIL Open Font License).

SMuFL uses four staff spaces per em. Clef origins identify G4, F3 and C4;
placing the baseline on the named staff line preserves those meanings.
"""
from functools import lru_cache
from pathlib import Path
from PIL import ImageFont
from .core import INK, BLUE, TEAL, PLUM, GOLD, PAPER_LIGHT, panel, box_text, footer, pill

FONT = Path(__file__).resolve().parents[1] / 'fonts/bravura/Bravura.otf'
GLYPHS = {'treble':'\ue050','bass':'\ue062','alto':'\ue05c','black':'\ue0a4','half':'\ue0a3','whole':'\ue0a2','sharp':'\ue262','flat':'\ue260','natural':'\ue261'}
@lru_cache(maxsize=32)
def music_font(gap): return ImageFont.truetype(str(FONT),round(gap*4))
def glyph(p,name,x,y,gap=32,color=INK):
    p.draw.text((x,y),GLYPHS[name],font=music_font(gap),fill=color,anchor='ls')
def staff(p,x,y,width,gap=32,clef='treble'):
    for i in range(5):p.draw.line((x,y+i*gap,x+width,y+i*gap),fill=INK,width=2)
    anchor={'treble':3,'bass':1,'alto':2,'tenor':1}[clef]
    glyph(p,'alto' if clef=='tenor' else clef,x+12,y+anchor*gap,gap)
    return y+4*gap

def note(p,x,y,gap=32,kind='black',stem=True,color=BLUE):
    glyph(p,kind,x,y,gap,color)
    width=music_font(gap).getlength(GLYPHS[kind])
    if stem:
        sx=x+1 if stem=='down' else x+width-1
        sy=y+3.5*gap if stem=='down' else y-3.5*gap
        p.draw.line((sx,y,sx,sy),fill=color,width=3)
    return x+width-1

def reading_plate(p):
    panel(p,(100,205,1500,575),fill=PAPER_LIGHT,outline=BLUE)
    for x,clef,label,reference,anchor in [(145,'treble','TREBLE: G CLEF','G4 — second line from bottom',3),(855,'bass','BASS: F CLEF','F3 — fourth line from bottom',1)]:
        p.text((x+260,245),label,size=25,bold=True,anchor='mm')
        staff(p,x,325,580,30,clef)
        y=325+anchor*30
        note(p,x+205,y,30,stem='down' if clef=='bass' else True,color=TEAL)
        p.text((x+275,505),reference,size=23,bold=True,anchor='mm',fill=TEAL)
        # Middle C: below the treble, above the bass staff.
        cy=475 if clef=='treble' else 295
        p.draw.line((x+420,cy,x+470,cy),fill=INK,width=3)
        note(p,x+426,cy,30,stem='down' if clef=='bass' else True,color=PLUM)
        p.text((x+445,542),'middle C (C4)',size=21,anchor='mm',fill=PLUM)
    panel(p,(100,590,1500,798),fill=PAPER_LIGHT,outline=TEAL)
    p.text((220,632),'4/4',size=36,bold=True,anchor='mm')
    for x,y,kind,color in [(430,690,'black',BLUE),(675,690,'black',TEAL),(790,690,'black',TEAL),(1070,690,'half',PLUM)]:
        end=note(p,x,y,23,kind,color=color)
    a=675+music_font(23).getlength(GLYPHS['black'])-1;b=790+music_font(23).getlength(GLYPHS['black'])-1
    p.draw.line((a,609,b,609),fill=TEAL,width=9)
    for x,text in [(445,'crotchet: 1'),(745,'two quavers: ½ + ½'),(1085,'minim: 2')]:p.text((x,744),text,size=26,bold=True,anchor='mm')
    p.text((800,782),'One complete bar: 1 + ½ + ½ + 2 = 4 crotchet beats',size=24,anchor='mm')
    footer(p,'Clefs anchor pitch; note shape and grouping show duration. G4, F3 and C4 are scientific pitch names.')
