"""Musical progression, engraving and practice boundaries."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest
from primer.curriculum import Curriculum, _validate_music_study

ROOT = Path(__file__).resolve().parents[1]


def test_all_eight_music_grades_precede_undergraduate_composition():
    c = Curriculum()
    grades = sorted((n for n in c.nodes.values() if n.get('music_grade')), key=lambda n:n['music_grade'])
    assert [n['music_grade'] for n in grades] == list(range(1, 9))
    assert all(n['stage'] < 4 and n['strand'] == 'music' for n in grades)
    assert grades[-1]['id'] in c.nodes['arts.4.composition']['prereqs']
    for n in grades:
        assert len(n['quiz']) >= 10
        assert len(n['music_study']['units']) >= 3
        assert all(n['music_study'][key] for key in ('aural','practical','sight_reading','composition','checkpoint'))
        assert [p['grade'] for p in n['music_path']] == list(range(1,9))
        assert all(p['id'] in c.nodes for p in n['music_path'])
    # The original introduction remains a distinct lesson: previous mastery is not Grade 1 credit.
    assert 'music_grade' not in c.nodes['arts.2.music-reading']


def test_music_chain_opens_without_visual_art_and_cannot_skip_previous_grade():
    c = Curriculum()
    mastered = {'math.1.fractions-intro':1, 'math.2.ratio':1}
    order = ['arts.0.singing','arts.0.dance','arts.1.instruments','arts.1.beat','arts.2.music-reading',
             'arts.2.music-grade-1','arts.2.music-grade-2','arts.2.music-grade-3','arts.3.music-theory',
             'arts.3.music-grade-4','arts.3.music-grade-5','arts.3.music-grade-6','arts.3.music-grade-7','arts.3.music-grade-8']
    for identifier in order:
        node = c.nodes[identifier]
        assert c.unlocked(node,mastered), (identifier,c.unlock_requirements(node,mastered))
        mastered[identifier] = 1
    assert 'arts.0.colors' not in mastered
    del mastered['arts.3.music-grade-7']
    assert not c.unlocked(c.nodes['arts.3.music-grade-8'],mastered)
    assert any('Grade 7' in reason for reason in c.unlock_requirements(c.nodes['arts.3.music-grade-8'],mastered))


def test_visual_art_credit_does_not_unlock_an_advanced_music_grade():
    c=Curriculum()
    visual={n['id']:1 for n in c.nodes.values() if n['domain']=='arts' and n.get('strand')!='music'}
    assert not c.unlocked(c.nodes['arts.3.music-grade-8'],visual)


@pytest.mark.parametrize('change',[
    lambda n:n.update(music_grade=True),
    lambda n:n.update(stage=4),
    lambda n:n['music_study'].update(aural=''),
    lambda n:n['music_study'].update(units=[]),
    lambda n:n['music_study'].update(source={'title':'Bad','url':'javascript:alert(1)'}),
])
def test_incomplete_or_misplaced_music_study_is_rejected(change):
    n=copy.deepcopy(Curriculum().nodes['arts.2.music-grade-1'])
    change(n)
    with pytest.raises(ValueError):_validate_music_study(n)


def test_music_study_and_grade_map_stay_out_of_atlas_payload():
    atlas=Curriculum().annotated_graph({})
    for n in atlas['nodes']:
        assert 'music_study' not in n and 'music_path' not in n


def test_engraved_clefs_use_the_correct_reference_lines(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'tools'))
    from humanities_illustrations import music_notation as m
    glyphs=[]
    class Draw:
        def line(self,*args,**kwargs):pass
    class Plate:
        draw=Draw()
    monkeypatch.setattr(m,'glyph',lambda p,name,x,y,gap: glyphs.append((name,y)))
    for clef in ['treble','bass','alto','tenor']:m.staff(Plate(),0,100,500,20,clef)
    assert glyphs == [('treble',160),('bass',120),('alto',140),('alto',120)]
    assert m.music_font(20).getmask(m.GLYPHS['treble']).getbbox()


def test_music_plates_titles_fit_the_inner_frame(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'tools'))
    from humanities_illustrations.music_grades import SPECS
    from humanities_illustrations.core import font
    for item in SPECS.values():
        assert font(50,bold=True).getlength(item['display_title']) <= 1408


def test_listening_sequence_keeps_the_suspension_held():
    script = """
    const assert=require('node:assert/strict'); global.window={};
    require('./web/music-listening.js'); const m=window.PrimerMusic;
    assert.equal(m.frequency(69),440);
    assert.equal(Object.keys(m.examples).length,8);
    for (const example of Object.values(m.examples)) for (const key of ['a','b']) {
      const s=m.sequence(example,key);
      assert.ok(s.beats>0 && s.beats<=8);
      for(const n of s.segments) assert.ok(n.start>=0 && n.beats>0 && n.gain<=.12 && Number.isFinite(m.frequency(n.midi)));
    }
    const suspended=m.sequence(m.examples[7],'a').segments.filter(n=>n.midi===60);
    assert.equal(suspended.length,1); assert.equal(suspended[0].beats,2);
    assert.equal(m.sequence(m.examples[8],'a').segments.find(n=>n.midi===64).beats,1);
    """
    result=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
