"""Finite drawings cannot substitute for exact tails, endpoint exceptions or rational completeness."""
import copy
from decimal import Decimal, localcontext
import json
from pathlib import Path
import shutil
import subprocess
import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT=Path(__file__).resolve().parents[1]

def test_analysis_binding_preserves_continuity_and_supplies_true_function_error_companion():
 curr=Curriculum();node=copy.deepcopy(curr.node('math.4.analysis'))
 assert sum(m.get('renderer')=='concept-lab' for m in node['lesson_media'])==1
 model=next(m for m in node['lesson_media'] if m.get('renderer')=='math-convergence-lab')
 assert model['props']=={'scenario':'math.4.analysis.convergence'}
 spatial=next(m for m in node['lesson_media'] if m.get('renderer')=='spatial-3d')
 assert spatial['props']['family']=='analysis-tail-errors' and spatial['props']['mode']=='model'
 _validate_lesson_media(node)
 bad=copy.deepcopy(node);bad['id']='math.4.diffeq'
 with pytest.raises(ValueError,match='convergence|cross-lesson'):_validate_lesson_media(bad)
 model['props']['extra']=True
 with pytest.raises(ValueError,match='convergence'):_validate_lesson_media(node)
 shell=(ROOT/'web/index.html').read_text();assert shell.index('/app/math-convergence-lab.js')<shell.index('/app/lesson-models.js')
 assert '/app/math-convergence-lab.css' in shell

@pytest.mark.skipif(shutil.which('node') is None,reason='Node is required')
def test_infinite_tail_inequalities_endpoint_exceptions_and_actual_geometry():
 result=subprocess.run(['node','tools/check_math_convergence_lab.js'],cwd=ROOT,capture_output=True,text=True,timeout=30)
 assert result.returncode==0,result.stdout+result.stderr
 assert '168000 exact tail decisions' in result.stdout and '18 3D error families' in result.stdout

@pytest.mark.skipif(shutil.which('node') is None,reason='Node is required')
def test_decimal_brackets_and_nonzero_errors_match_independent_high_precision_sqrt():
 script="const a=require('./web/math-convergence-lab.js');console.log(JSON.stringify(Array.from({length:160},(_,i)=>{const q=a.decimalRoot(i+1);return {n:i+1,decimal:q.decimal,error:q.error};})));"
 result=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True,check=True)
 rows=json.loads(result.stdout)
 with localcontext() as context:
  context.prec=210;limit=Decimal(2).sqrt()
  for row in rows:
   value=Decimal(row['decimal']);error=limit-value
   assert Decimal(0)<error<Decimal(10)**(-row['n'])
   assert len(row['decimal'].split('.')[1])==row['n']
   assert abs(Decimal(str(row['error']))/error-1)<Decimal('3e-15')
