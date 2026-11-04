from pathlib import Path
from fractions import Fraction
from collections import Counter
from functools import lru_cache
import json,math,hashlib
from nltk import CFG
from nltk.parse import EarleyChartParser
D=Path(__file__).resolve().parent
G=CFG.fromstring("""S -> NP VP
NP -> Det N | NP PP | 'we'
VP -> V NP | VP PP
PP -> P NP
Det -> 'a' | 'the'
N -> 'fox' | 'bird' | 'tree' | 'telescope'
V -> 'saw' | 'heard'
P -> 'with' | 'near'
""")
parsers={str(x):EarleyChartParser(CFG(x,G.productions()))for x in {p.lhs()for p in G.productions()}}
lexicon={w for p in G.productions()for w in p.rhs()if isinstance(w,str)}
@lru_cache(None)
def count(words,label):
 if not words or any(w not in lexicon for w in words):return 0
 return sum(1 for _ in parsers[label].parse(words))
def bracket(n):return '('+n['label']+' '+(n['word']if 'word'in n else' '.join(bracket(x)for x in n['children']))+')'
parser_cases=json.loads((D/'parser-browser-cases.json').read_bytes());tree_nodes=tree_edges=chart_cells=0;worst=0
for c in parser_cases:
 words=c['text'].split();n=len(words);assert c['count']==count(tuple(words),'S')
 for i,row in enumerate(c['chartRows']):
  assert row[0]==str(i)+' · '+words[i]
  for j,text in enumerate(row[1:],1):
   if j<=i:assert text=='—';continue
   expected={label:count(tuple(words[i:j]),label)for label in parsers};expected={k:v for k,v in expected.items()if v}
   actual={}if text=='∅'else{k:int(v)for pair in text.split(', ')for k,v in [pair.split(': ')]}
   assert actual==expected;(i,j);chart_cells+=1
 if not c['count']:assert c['nodes']==[]and c['edges']==[];continue
 expected_trees={t.pformat(margin=10000)for t in parsers['S'].parse(words)};assert bracket(c['tree'])in expected_trees
 positions=[];edges=[]
 def walk(node,depth):
  index=len(positions);x=60+45*(node['i']+node['j']);y=40+75*depth;positions.append((node['label'],x,y,node['i'],node['j']))
  for child in node.get('children',[]):
   child_index=walk(child,depth+1);edges.append((index,child_index))
  if 'word'in node:
   target=len(positions);positions.append((node['word'],x,y+75,node['i'],node['j']));edges.append((index,target))
  return index
 walk(c['tree'],0);assert len(c['nodes'])==len(positions)==3*n-1
 for node,(label,x,y,i,j)in zip(c['nodes'],positions):
  assert node['text']==label and node['source']['i']==i and node['source']['j']==j
  error=max(abs(node['x']-x),abs(node['y']-y));worst=max(worst,error);assert error<1e-8;tree_nodes+=1
 assert len(c['edges'])==len(edges)
 for e,(a,b)in zip(c['edges'],edges):
  assert e['ids']==str(a)+':'+str(b);expected=[positions[a][1],positions[a][2]+10,positions[b][1],positions[b][2]-10];error=max(abs(x-y)for x,y in zip(e['coords'],expected));worst=max(worst,error);assert error<1e-8;tree_edges+=1
vocab=['the','fox','bird','cat','dog','rests','</s>','<unk>'];sources={'varied':['fox','bird','cat','dog','fox','bird'],'foxHeavy':['fox','fox','fox','fox','fox','bird']};bars=links=probability_cells=0
for c in json.loads((D/'probability-browser-cases.json').read_bytes()):
 sentences=[['the',n,'rests']for n in sources[c['corpusId']]];pairs=Counter((a,b)for s in sentences for a,b in zip(['<s>']+s,s+['</s>']));h=c['history'];total=sum(v for (before,after),v in pairs.items()if before==h);alpha=Fraction(c['alphaHalves'],2);denominator=total+alpha*len(vocab)
 assert c['trainingRows']==[[str(i+1),' '.join(s)]for i,s in enumerate(sentences)]
 assert len(c['tableRows'])==8
 for i,(word,row)in enumerate(zip(vocab,c['tableRows'])):
  observed=pairs[h,word];prob=None if not denominator else Fraction(observed+alpha,denominator);assert row[0]==word and row[1]==str(observed);probability_cells+=1
  if prob is None:assert row[2]=='undefined';continue
  left,right=row[2].split(' ≈ ');assert left==f'{prob.numerator}/{prob.denominator}'and abs(float(right)-float(prob))<=.000050001
  entry=next(x for x in c['barRects']if x['word']==word);expected=[85,50+40*i,200*float(prob),22];error=max(abs(x-y)for x,y in zip(entry['coords'],expected));worst=max(worst,error);assert error<1e-8;bars+=1
  matches=[x for x in c['mapLines']if x['word']==word]
  if prob==0:assert not matches;continue
  assert len(matches)==1 and word in c['mapTexts']and left in c['mapTexts'];line=matches[0];angle=-math.pi/2+i*math.pi/4;dx=120*math.cos(angle);dy=210*math.sin(angle);length=math.hypot(dx,dy);expected=[160,260,160+dx-dx*25/length,260+dy-dy*25/length];error=max(abs(x-y)for x,y in zip(line['coords'],expected));worst=max(worst,error);assert error<1e-8
  assert line['dash']==('none'if observed else'5 4');links+=1
metric_bars=0
for c in json.loads((D/'evaluation-browser-cases.json').read_bytes()):
 tp,fp,fn,tn=[c[k]for k in ['tp','fp','fn','tn']];assert c['matrixRows']==[['Actual positive',f'{tp} (TP)',f'{fn} (FN)'],['Actual negative',f'{fp} (FP)',f'{tn} (TN)']]
 for i,(name,n,d)in enumerate([('Accuracy',tp+tn,tp+fp+fn+tn),('Recall',tp,tp+fn)]):
  matches=[b for b in c['rects']if b['name']==name]
  if not d:assert not matches;continue
  f=Fraction(n,d);assert len(matches)==1 and matches[0]['fraction']==f'{f.numerator}/{f.denominator}';expected=[95,55+70*i,200*float(f),28];error=max(abs(x-y)for x,y in zip(matches[0]['coords'],expected));worst=max(worst,error);assert error<1e-8;metric_bars+=1
proof={'allPassed':True,'parserCases':len(parser_cases),'renderedChartCells':chart_cells,'renderedTreeNodes':tree_nodes,'renderedTreeEdges':tree_edges,'renderedProbabilityCells':probability_cells,'renderedProbabilityBars':bars,'renderedTransitionEdges':links,'renderedMetricBars':metric_bars,'maximumCoordinateError':worst,'independentParser':'NLTK EarleyChartParser','probabilitiesCheckedWith':'fractions.Fraction','applicationIntegrated':False,'wholeGoalComplete':False}
(D/'rendered-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
