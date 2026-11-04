from pathlib import Path
import argparse
parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path);args=parser.parse_args()
from fractions import Fraction
from collections import Counter
import itertools,json,random,subprocess,hashlib
R=Path(__file__).resolve().parents[1];D=R/'docs/language-computation-review-20261104'
rng=random.Random(4704)
texts=['we saw a fox','we saw a fox with a telescope','we saw a fox near a tree with a telescope','fox a saw we','we saw a wolf','']
for a,b,p in itertools.product(['fox','bird','tree'],['fox','bird','tree'],['with','near']):texts.append(f'we saw a {a} {p} a {b}')
for a,b,c in itertools.product(['with','near'],repeat=3):texts.append(f'we saw a fox {a} a bird {b} a tree {c} a telescope')
for _ in range(40):texts.append(' '.join(rng.choices(['we','saw','heard','a','the','fox','bird','near','with','tree'],k=rng.randint(1,10))))
texts=list(dict.fromkeys(texts))
corpora={'varied':[['the',n,'rests']for n in ['fox','bird','cat','dog','fox','bird']],'foxHeavy':[['the',n,'rests']for n in ['fox','fox','fox','fox','fox','bird']]}
vocabulary=['the','fox','bird','cat','dog','rests','</s>','<unk>'];histories=['<s>','the','fox','bird','cat','dog','rests','<unk>']
requests=[{'corpusId':c,'history':h,'alphaHalves':a}for c,h,a in itertools.product(corpora,histories,[0,1,2])]
matrices=[dict(zip(['tp','fp','fn','tn'],v))for v in itertools.product([0,1,5,30,100],repeat=4)]
matrices.extend([{'tp':30,'fp':10,'fn':20,'tn':40},{'tp':0,'fp':0,'fn':5,'tn':95}])
matrices.extend(dict(zip(['tp','fp','fn','tn'],[rng.randint(0,100)for _ in range(4)]))for _ in range(64))
bridge="""const fs=require('fs'),C=require('./web/language-computation-core.js'),q=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify({parses:q.texts.map(text=>{const m=C.parse(text);return{...m,trees:Array.from({length:m.count},(_,i)=>C.tree(m,i))}}),lm:q.requests.map(x=>C.languageModel(x.corpusId,x.history,x.alphaHalves)),evaluation:q.matrices.map(C.evaluation)}));"""
r=json.loads(subprocess.check_output(['node','-e',bridge],input=json.dumps({'texts':texts,'requests':requests,'matrices':matrices}),text=True))
oracle=json.loads((D/'independent-parser-oracles.json').read_bytes());expected_by_text={x['text']:x for x in oracle['sentences']};assert len(expected_by_text)==71
def bracket(n):
 if 'word'in n:return '('+n['label']+' '+n['word']+')'
 return '('+n['label']+' '+' '.join(bracket(c)for c in n['children'])+')'
root_trees=chart_states=trace_contributions=0
for text,m in zip(texts,r['parses']):
 expected=set(expected_by_text[text]['trees'])
 actual=[bracket(t)for t in m['trees']];assert len(actual)==len(set(actual))==m['count']and set(actual)==expected,(text,m['count'],len(expected))
 root_trees+=len(actual)
 expected_cells={(x['i'],x['j']):x['entries']for x in expected_by_text[text]['cells']}
 assert [(x['length'],x['i'],x['j'])for x in m['events']]==[(length,i,i+length)for length in range(1,m['n']+1)for i in range(m['n']-length+1)]
 for event in m['events']:
  i,j=event['i'],event['j']
  if(i,j)not in expected_cells:continue
  assert event['entries']==expected_cells[i,j];chart_states+=8
  for c in event['contributions']:
   if 'word'in c:assert c['ways']==1 and c['word']==m['words'][i]
   else:
    k=c['split'];left=expected_cells[i,k].get(c['left'],0);right=expected_cells[k,j].get(c['right'],0);assert c['leftCount']==left and c['rightCount']==right and c['ways']==left*right
   trace_contributions+=1
probabilities=0
for req,m in zip(requests,r['lm']):
 c=corpora[req['corpusId']];pairs=Counter((a,b)for s in c for a,b in zip(['<s>']+s,s+['</s>']));context=sum(v for (h,w),v in pairs.items()if h==req['history']);a=Fraction(req['alphaHalves'],2);denom=context+a*len(vocabulary)
 expected=[]
 for word,p in zip(vocabulary,m['predictions']):
  count=pairs[req['history'],word];assert p['word']==word and p['count']==count
  f=None if denom==0 else Fraction(count+a,denom);expected.append(f);got=p['probability']
  assert(got is None)==(f is None)
  if f is not None:assert got['n']==f.numerator and got['d']==f.denominator and abs(got['value']-float(f))<1e-15
  probabilities+=1
 assert m['rowDefined']==(denom!=0)
 if denom:assert sum(expected)==1;assert set(m['mostLikely'])=={w for w,p in zip(vocabulary,expected)if p==max(expected)}
 else:assert m['mostLikely']==[]
 types=Counter(w for s in c for w in s);ratio=Fraction(len(types),sum(types.values()));assert m['lexicalTokens']==18 and m['types']==len(types)and Fraction(m['typeTokenRatio']['n'],m['typeTokenRatio']['d'])==ratio
for x,m in zip(matrices,r['evaluation']):
 tp,fp,fn,tn=[x[k]for k in ['tp','fp','fn','tn']];total=tp+fp+fn+tn
 pairs={'precision':(tp,tp+fp),'recall':(tp,tp+fn),'accuracy':(tp+tn,total),'f1':(2*tp,2*tp+fp+fn),'majorityAccuracy':(max(tp+fn,fp+tn),total)}
 for key,(n,d)in pairs.items():
  got=m[key];assert(got is None)==(d==0)
  if d:assert Fraction(got['n'],got['d'])==Fraction(n,d)
 assert m['majorityClass']==(None if not total else'tie'if tp+fn==fp+tn else'positive'if tp+fn>fp+tn else'negative')
bounds_script="""const assert=require('node:assert/strict'),C=require('./web/language-computation-core.js'),m=C.parse('we saw a fox');const cases=[()=>C.parse(null),()=>C.parse('A'),()=>C.parse('we <img>'),()=>C.parse('a'.repeat(301)),()=>C.parse(Array(15).fill('we').join(' ')),()=>C.languageModel('__proto__'),()=>C.languageModel('varied','constructor'),()=>C.languageModel('varied','the',NaN),()=>C.languageModel('varied','the',.5),()=>C.evaluation({tp:-1}),()=>C.evaluation({tp:101}),()=>C.evaluation({fp:.5}),()=>C.evaluation({fn:NaN}),()=>C.evaluation({tn:Infinity}),()=>C.evaluation({tp:'1'}),()=>C.tree(m,-1),()=>C.tree(m,1),()=>C.visibleChart(m,-1),()=>C.visibleChart(m,m.events.length+1),()=>C.feedback('constructor',m,0)];for(const f of cases)assert.throws(f);assert.equal(C.parse('').count,0);assert.equal(C.fraction(0,0),null);console.log(cases.length);"""
invalid_count=int(subprocess.check_output(['node','-e',bounds_script],text=True,cwd=R))
proof={'allPassed':True,'invalidInputsRejected':invalid_count,'independentParserOracle':oracle['generator'],'nltkVersionUsedForOracle':oracle['version'],'sentenceCases':len(texts),'completeTreesCompared':root_trees,'independentChartSymbolStates':chart_states,'traceContributions':trace_contributions,'probabilityRows':len(requests),'exactProbabilityEntries':probabilities,'confusionMatrices':len(matrices),'sourceSHA256':hashlib.sha256((R/'web/language-computation-core.js').read_bytes()).hexdigest(),'scope':'Shipped runtime with independent parser oracles and exact fraction arithmetic','productionDeployed':False,'wholeGoalComplete':False}
(args.output or D/'runtime-core-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
