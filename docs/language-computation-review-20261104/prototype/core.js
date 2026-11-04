/* Original teaching implementation. Small authored examples; not a general English model. */
(function (root) {
  'use strict';
  const grammar = Object.freeze({
    start: 'S',
    binary: Object.freeze([
      ['S', 'NP', 'VP'], ['NP', 'Det', 'N'], ['NP', 'NP', 'PP'],
      ['VP', 'V', 'NP'], ['VP', 'VP', 'PP'], ['PP', 'P', 'NP'],
    ].map(Object.freeze)),
    lexical: Object.freeze({
      NP: Object.freeze(['we']), Det: Object.freeze(['a', 'the']),
      N: Object.freeze(['fox', 'bird', 'tree', 'telescope']),
      V: Object.freeze(['saw', 'heard']), P: Object.freeze(['with', 'near']),
    }),
  });
  const sentences = Object.freeze([
    {id:'simple', text:'we saw a fox'},
    {id:'attachment', text:'we saw a fox with a telescope'},
    {id:'two-attachments', text:'we saw a fox near a tree with a telescope'},
    {id:'word-order', text:'fox a saw we'},
    {id:'unknown', text:'we saw a wolf'},
  ].map(Object.freeze));
  function tokens(text) {
    if (typeof text !== 'string' || text.length > 300 || !/^[a-z\s]*$/.test(text)) throw Error('Use lowercase words and spaces from this toy grammar');
    const words = text.trim() ? text.trim().split(/\s+/) : [];
    if (words.length > 14) throw Error('At most fourteen tokens are supported');
    return words;
  }
  const symbols = Object.freeze([...new Set(grammar.binary.flat().concat(Object.keys(grammar.lexical)))]);
  function parse(text) {
    const words = tokens(text), n = words.length;
    const chart = Array.from({length:n+1}, () => Array.from({length:n+1}, () => Object.create(null)));
    const events = [];
    // Each event completes one half-open span [i,j). All smaller spans already exist.
    for (let length=1; length<=n; length++) for (let i=0; i+length<=n; i++) {
      const j=i+length, cell=chart[i][j], contributions=[];
      if (length===1) {
        for (const [label, forms] of Object.entries(grammar.lexical)) if (forms.includes(words[i])) {
          cell[label]={count:1, alternatives:[{word:words[i]}]};
          contributions.push({label,word:words[i],ways:1});
        }
      } else {
        for (let k=i+1; k<j; k++) for (const [label,left,right] of grammar.binary) {
          const a=chart[i][k][left], b=chart[k][j][right];
          if (!a || !b) continue;
          const ways=a.count*b.count;
          if (!Number.isSafeInteger(ways)) throw Error('Parse count exceeds exact integer range');
          if (!cell[label]) cell[label]={count:0, alternatives:[]};
          cell[label].count+=ways;
          if (!Number.isSafeInteger(cell[label].count)) throw Error('Parse count exceeds exact integer range');
          cell[label].alternatives.push({split:k,left,right,ways});
          contributions.push({label,split:k,left,right,leftCount:a.count,rightCount:b.count,ways});
        }
      }
      events.push({index:events.length,i,j,length,entries:Object.fromEntries(Object.entries(cell).map(([k,v])=>[k,v.count])),contributions});
    }
    return {words,n,chart,events,count:chart[0][n]?.[grammar.start]?.count||0,
      unknownWords:[...new Set(words.filter(w=>!Object.values(grammar.lexical).some(forms=>forms.includes(w))))]};
  }
  function tree(model, rank=0) {
    if (!Number.isSafeInteger(rank)||rank<0||rank>=model.count) throw Error('Choose an existing parse rank');
    function build(label,i,j,r) {
      const entry=model.chart[i][j][label];
      for (const a of entry.alternatives) {
        const ways=a.word?1:a.ways;
        if (r>=ways) {r-=ways;continue;}
        if (a.word) return {label,i,j,word:a.word};
        const rightCount=model.chart[a.split][j][a.right].count;
        return {label,i,j,split:a.split,children:[build(a.left,i,a.split,Math.floor(r/rightCount)),build(a.right,a.split,j,r%rightCount)]};
      }
      throw Error('Missing packed-forest alternative');
    }
    return build(grammar.start,0,model.n,rank);
  }
  function visibleChart(model, completed) {
    if (!Number.isInteger(completed)||completed<0||completed>model.events.length) throw Error('Invalid algorithm position');
    return model.events.slice(0,completed).map(event=>({i:event.i,j:event.j,entries:{...event.entries}}));
  }
  function treeLayout(node) {
    const positions=[],edges=[];let maxDepth=0;
    function visit(n,depth) {
      const id=positions.length, point={id,label:n.label,word:n.word||null,i:n.i,j:n.j,depth,x:60+((n.i+n.j)/2)*90,y:40+depth*75};
      positions.push(point);maxDepth=Math.max(maxDepth,depth);
      for(const child of n.children||[]) {const childId=visit(child,depth+1);edges.push({from:id,to:childId});}
      if(n.word) {
        const wordId=positions.length;positions.push({id:wordId,label:n.word,word:n.word,i:n.i,j:n.j,depth:depth+1,x:point.x,y:point.y+75,terminal:true});
        edges.push({from:id,to:wordId});maxDepth=Math.max(maxDepth,depth+1);
      }
      return id;
    }
    visit(node,0);
    return {positions,edges,width:120+node.j*90,height:90+maxDepth*75};
  }
  const corpora = Object.freeze({
    varied:Object.freeze(['fox','bird','cat','dog','fox','bird'].map(noun=>Object.freeze(['the',noun,'rests']))),
    foxHeavy:Object.freeze(['fox','fox','fox','fox','fox','bird'].map(noun=>Object.freeze(['the',noun,'rests']))),
  });
  const vocabulary = Object.freeze(['the','fox','bird','cat','dog','rests','</s>','<unk>']);
  const histories = Object.freeze(['<s>','the','fox','bird','cat','dog','rests','<unk>']);
  function fraction(n,d) {
    if (!Number.isSafeInteger(n)||!Number.isSafeInteger(d)||n<0||d<0) throw Error('Nonnegative exact counts required');
    if(d===0)return null;
    let a=n,b=d;while(b){const t=a%b;a=b;b=t;}
    return {n:n/a,d:d/a,value:n/d,text:(n/a)+'/'+(d/a)};
  }
  function languageModel(corpusId='varied',history='the',alphaHalves=0) {
    if(!Object.hasOwn(corpora,corpusId)||!histories.includes(history)||![0,1,2].includes(alphaHalves))throw Error('Unknown corpus, history or smoothing');
    const sentences=corpora[corpusId],counts=Object.create(null),typeCounts=Object.create(null);let lexicalTokens=0;
    for(const sentence of sentences){
      for(const word of sentence){typeCounts[word]=(typeCounts[word]||0)+1;lexicalTokens++;}
      const sequence=['<s>',...sentence,'</s>'];
      for(let i=1;i<sequence.length;i++) {const h=sequence[i-1],w=sequence[i];if(!counts[h])counts[h]=Object.create(null);counts[h][w]=(counts[h][w]||0)+1;}
    }
    const row=counts[history]||{},total=Object.values(row).reduce((a,b)=>a+b,0),denominator=2*total+alphaHalves*vocabulary.length;
    const predictions=vocabulary.map(word=>({word,count:row[word]||0,probability:fraction(2*(row[word]||0)+alphaHalves,denominator)}));
    const maximum=denominator===0?null:Math.max(...predictions.map(p=>p.probability.value));
    return {corpusId,history,alphaHalves,sentences:sentences.map(s=>s.slice()),counts,typeCounts,lexicalTokens,types:Object.keys(typeCounts).length,
      typeTokenRatio:fraction(Object.keys(typeCounts).length,lexicalTokens),contextCount:total,denominator,predictions,
      mostLikely:maximum===null?[]:predictions.filter(p=>p.probability.value===maximum).map(p=>p.word),
      rowDefined:denominator!==0,vocabulary:vocabulary.slice(),boundaryMarkersCountedInTTR:false};
  }
  function evaluation({tp=30,fp=10,fn=20,tn=40}={}) {
    const counts={tp,fp,fn,tn};
    if(!Object.values(counts).every(x=>Number.isInteger(x)&&x>=0&&x<=100))throw Error('Counts must be integers from zero to 100');
    const total=tp+fp+fn+tn,positives=tp+fn,negatives=fp+tn;
    return {...counts,total,positives,negatives,predictedPositives:tp+fp,
      precision:fraction(tp,tp+fp),recall:fraction(tp,tp+fn),accuracy:fraction(tp+tn,total),f1:fraction(2*tp,2*tp+fp+fn),
      majorityAccuracy:fraction(Math.max(positives,negatives),total),majorityClass:total===0?null:positives===negatives?'tie':positives>negatives?'positive':'negative'};
  }
  const ambiguity = Object.freeze([
    {id:'sense',prompt:'A search for a river bank returns pages about mortgages. Which task failed?',answer:'sense',why:'The same written form has different meanings; the surrounding request selects the river sense.'},
    {id:'form',prompt:'A search for “ran” misses records containing “run”. Which task is implicated?',answer:'morphology',why:'These are related word forms. Matching their lemma or morphological relation differs from choosing a sense.'},
    {id:'token',prompt:'An exercise defines “New York” as one token, but its tokenizer returns two separate tokens. Which processing choice needs review?',answer:'tokenization',why:'Token boundaries depend on the declared convention. Here the output breaks that convention; this is not a claim that every system should treat a place name as one token.'},
    {id:'reference',prompt:'“Mira thanked Jo because she helped.” The system cannot decide who “she” refers to. Which task remains unresolved?',answer:'coreference',why:'The expression must be linked to a referent in context. This sentence alone may not settle which person helped.'},
    {id:'pos',prompt:'Compare “The birds fly” with “A fly landed”. The word “fly” has different grammatical roles. Which task distinguishes the roles?',answer:'pos',why:'A part-of-speech analysis uses the context to distinguish a verb from a noun; it does not by itself identify a referent.'},
  ].map(Object.freeze));
  const tasks=Object.freeze([['sense','Word-sense disambiguation'],['morphology','Morphological analysis'],['tokenization','Tokenization / annotation units'],['coreference','Coreference resolution'],['pos','Part-of-speech analysis']].map(Object.freeze));
  function feedback(kind,model,answer) {
    if(kind==='parses')return {correct:String(model.count)===String(answer),why:'This explicit grammar licenses '+model.count+' complete parse(s). It does not decide intended meaning.'};
    if(kind==='next')return {correct:model.mostLikely.includes(answer),why:model.rowDefined?'Maximum-probability token(s): '+model.mostLikely.join(', ')+'. Tied maxima are all accepted.':'No unsmoothed conditional distribution can be estimated for an unseen history.'};
    if(kind==='task')return {correct:model.answer===answer,why:model.why};
    if(kind==='evaluation')return {correct:answer==='recall',why:'Recall uses actual positives: TP / (TP + FN). Here that is '+model.tp+'/'+model.positives+(model.recall?' = '+model.recall.text+'.':', which is undefined because there are no actual positives.')+' Accuracy uses all '+model.total+' examples.'+(model.precision?'':' Precision is undefined because there are no predicted positives.')};
    throw Error('Unknown practice task');
  }
  const api=Object.freeze({grammar,symbols,sentences,tokens,parse,tree,visibleChart,treeLayout,corpora,vocabulary,histories,fraction,languageModel,evaluation,ambiguity,tasks,feedback});
  if(typeof module==='object'&&module.exports)module.exports=api;else root.PrimerLanguageComputation=api;
})(globalThis);
