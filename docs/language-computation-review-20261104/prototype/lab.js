(function(rootScope) {
  'use strict';
  function render(item,hooks={}) {
    if(item?.props?.scenario!=='lang.5.comp-ling'||!rootScope.PrimerLanguageComputation)return null;
    const C=rootScope.PrimerLanguageComputation,root=document.createElement('section');
    root.className='card language-computation-lab';
    let disposed=false,mounted=false;
    const state={station:'parser',sentence:'attachment',text:C.sentences[1].text,completed:0,rank:0,corpus:'varied',history:'the',alpha:0,caseIndex:0,counts:{tp:30,fp:10,fn:20,tn:40}};
    root.innerHTML=`<h3>Language from rules and data</h3>
      <p>Work through a small authored grammar, two constructed corpora and a separate classifier example. These examples expose calculations and assumptions; they do not model all of English or supply measured language-use statistics.</p>
      <nav aria-label="Language computation activities"><button type="button" data-station="parser">Parse a sentence</button><button type="button" data-station="corpus">Count and predict</button><button type="button" data-station="ambiguity">Name the task</button><button type="button" data-station="evaluation">Audit a classifier</button></nav>
      <section data-panel="parser"><h4>Build a parse chart, then inspect its trees</h4>
        <label>Authored example <select data-role="sentence"></select></label>
        <label>Or use lowercase words from the grammar <input data-role="sentence-text" type="text" maxlength="300"></label><button type="button" data-role="use-sentence">Use sentence</button>
        <p data-role="parse-error" class="feedback" role="status"></p>
        <details><summary>The entire toy grammar and lexicon</summary><div data-role="grammar"></div><p>Rules have either two nonterminal children or one terminal word. No empty or unary nonterminal productions are supported here. A zero parse count means this grammar does not cover the input. A successful parse does not check case, agreement, intended meaning or truth.</p></details>
        <ol><li>Initialize one-word spans from the lexicon.</li><li>Visit spans in order of increasing length.</li><li>Try each internal split and each binary production.</li><li>Multiply the two child counts for each alternative; add alternatives for the same parent.</li><li>Read S in the full span and follow packed alternatives to recover individual trees.</li></ol>
        <div class="actions"><button type="button" data-role="step">Next chart cell</button><button type="button" data-role="finish">Complete chart</button><button type="button" data-role="reset-parse">Reset chart</button></div>
        <p data-role="parse-status" aria-live="polite"></p><p>Scroll the chart and tree horizontally to inspect all columns and words. The tree keeps readable text size.</p><button type="button" data-role="end-chart">Last chart columns</button><div class="scroll" tabindex="0" role="region" aria-label="Parse chart; scroll horizontally"><div data-role="chart"></div></div>
        <div data-role="trace"></div><p data-role="parse-result"></p>
        <div class="actions"><button type="button" data-role="previous-tree">Earlier tree</button><button type="button" data-role="next-tree">Next tree</button><button type="button" data-role="center-tree">Center tree root</button><button type="button" data-role="start-tree">First words</button><button type="button" data-role="end-tree">Last words</button></div>
        <div class="scroll visual" tabindex="0" role="region" aria-label="Parse tree; scroll horizontally"><svg data-role="tree" role="img" aria-label="Actual constituent tree for the selected parse"></svg></div><p data-role="tree-status"></p>
        <fieldset><legend>Practice: predict the number of complete parses</legend><label>Your prediction <input data-role="parse-guess" type="number" min="0" max="1000" step="1"></label><button type="button" data-role="check-parse">Check prediction</button><p data-role="parse-feedback" class="feedback" role="status"></p></fieldset>
      </section>
      <section data-panel="corpus" hidden><h4>What changes when the sample changes?</h4>
        <label>Constructed training sample <select data-role="corpus"><option value="varied">Varied animals</option><option value="foxHeavy">Fox-heavy sample</option></select></label>
        <div data-role="sentences"></div><p data-role="corpus-summary"></p>
        <p>Both samples contain 18 lexical word tokens, so their type–token ratios compare equal-sized samples. They are authored teaching data, not representative corpora of any community. Tokenization here is whitespace splitting of the displayed words. Each sentence separately receives one &lt;s&gt; start marker and one &lt;/s&gt; end marker; these markers are excluded from the type–token ratio.</p>
        <label>Previous token (one-token history) <select data-role="history"></select></label><label>Add-k smoothing <select data-role="alpha"><option value="0">k = 0 (unsmoothed)</option><option value="1">k = 1/2</option><option value="2">k = 1</option></select></label>
        <p>The fixed prediction vocabulary is the union of both samples’ words, plus &lt;/s&gt; and a reserved &lt;unk&gt; category. The start marker is a history, not a predicted token. P(w|h) = [C(h,w)+k] / [C(h)+kV]. Without smoothing, an unseen history has no estimated row. Add-k is a simple demonstration, not a recommendation for a production language model.</p>
        <p data-role="lm-status" aria-live="polite"></p><div data-role="prediction-table"></div>
        <div class="scroll visual" tabindex="0" role="region" aria-label="Probability bars"><svg data-role="bars" viewBox="0 0 320 430" role="img" aria-label="Calculated next-token probabilities from zero to one"></svg></div>
        <div class="scroll visual" tabindex="0" role="region" aria-label="Transition map"><svg data-role="map" viewBox="0 0 320 520" role="img" aria-label="Outgoing next-token probabilities for the selected history"></svg></div>
        <p>The map’s positions are a layout choice, not semantic distances. Solid edges have observed counts; dashed edges have zero observed count and positive smoothing mass. Exact probabilities are in the table. These associations reflect the chosen sample; a likely continuation is not evidence that a statement is true.</p>
        <fieldset><legend>Practice: choose a maximum-probability next token</legend><label>Your choice <select data-role="next-guess"></select></label><button type="button" data-role="check-next">Check choice</button><p data-role="next-feedback" class="feedback" role="status"></p></fieldset>
      </section>
      <section data-panel="ambiguity" hidden><h4>Different ambiguities need different analyses</h4>
        <div data-role="task-table"></div><p data-role="task-prompt"></p><label>Which task is involved? <select data-role="task-guess"></select></label><div class="actions"><button type="button" data-role="check-task">Check task</button><button type="button" data-role="next-task">Next example</button></div><p data-role="task-feedback" class="feedback" role="status"></p>
        <p>These are authored annotations for the displayed cases. Selecting the right task names the problem; it does not run a general-purpose disambiguation system. Some reference ambiguities remain unresolved without additional context.</p>
      </section>
      <section data-panel="evaluation" hidden><h4>Audit a separate text classifier</h4>
        <p>These constructed counts belong to a separate binary classifier example, not to the bigram model above. “Actual” refers to the supplied reference labels; “predicted” refers to the classifier’s labels at one fixed threshold.</p>
        <div class="counts"><label>True positives <input data-role="tp" type="number" min="0" max="100" step="1" value="30"></label><label>False positives <input data-role="fp" type="number" min="0" max="100" step="1" value="10"></label><label>False negatives <input data-role="fn" type="number" min="0" max="100" step="1" value="20"></label><label>True negatives <input data-role="tn" type="number" min="0" max="100" step="1" value="40"></label></div>
        <div class="actions"><button type="button" data-role="default-counts">Original counts</button><button type="button" data-role="negative-counts">All-negative, imbalanced example</button><button type="button" data-role="empty-counts">No examples</button></div>
        <p data-role="evaluation-error" role="status"></p><div data-role="confusion"></div><div data-role="metrics"></div>
        <div class="scroll visual" tabindex="0" role="region" aria-label="Classifier metric chart"><svg data-role="evaluation-bars" viewBox="0 0 320 260" role="img" aria-label="Calculated accuracy and recall, each on a zero-to-one scale"></svg></div>
        <p data-role="evaluation-status" aria-live="polite"></p>
        <ol><li>Read the four confusion-matrix cells and sum their reference-label totals.</li><li>Choose the denominator that answers the question: predicted positives for precision, actual positives for recall, all examples for accuracy.</li><li>Check for a zero denominator before division.</li><li>Compare with a majority-class baseline and examine the kinds of errors. The costs of errors depend on the task.</li></ol>
        <fieldset><legend>Practice: identify the metric for finding actual positives</legend><label>Which metric most directly answers “What fraction of actual positives were found?” <select data-role="metric-guess"><option value="accuracy">Accuracy</option><option value="precision">Precision</option><option value="recall">Recall</option></select></label><button type="button" data-role="check-metric">Check metric</button><p data-role="metric-feedback" class="feedback" role="status"></p></fieldset>
      </section>
      <p class="practice-note">Practice feedback stays in this activity. It does not submit quiz answers or change lesson mastery.</p>`;
    const get=k=>root.querySelector('[data-role="'+k+'"]');
    function element(tag,text,attrs={}) {const e=document.createElement(tag);if(text!==null)e.textContent=text;for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));return e;}
    function options(select,rows) {select.replaceChildren(...rows.map(([v,t])=>element('option',t,{value:v})));}
    function table(host,head,rows,caption) {
      const t=element('table',null);if(caption)t.append(element('caption',caption));
      const thead=element('thead',null),hr=element('tr',null);for(const label of head)hr.append(element('th',label,{scope:'col'}));thead.append(hr);t.append(thead);
      const body=element('tbody',null);for(const row of rows){const tr=element('tr',null);row.forEach((v,i)=>tr.append(element(i===0?'th':'td',String(v),i===0?{scope:'row'}:{})));body.append(tr);}t.append(body);host.replaceChildren(t);return t;
    }
    const NS='http://www.w3.org/2000/svg';
    function svg(svg,tag,attrs,text) {const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=text;svg.append(e);return e;}
    const frac=f=>f?f.text+' ≈ '+f.value.toFixed(4):'undefined';
    options(get('sentence'),[...C.sentences.map(s=>[s.id,s.text]),['custom','Custom input shown below']]);get('sentence').value=state.sentence;get('sentence-text').value=state.text;
    table(get('grammar'),['Parent','Children / terminal words'],[...C.grammar.binary.map(([a,b,c])=>[a,b+' '+c]),...Object.entries(C.grammar.lexical).map(([a,b])=>[a,b.map(w=>'“'+w+'”').join(' | ')])],'All rules used by this chart');
    options(get('history'),C.histories.map(w=>[w,w]));get('history').value=state.history;
    options(get('next-guess'),C.vocabulary.map(w=>[w,w]));options(get('task-guess'),C.tasks);
    table(get('task-table'),['Task','Question it addresses'],[
      ['Word-sense disambiguation','Which meaning of this word fits the context?'],['Morphological analysis','How are word forms and their structure related?'],['Tokenization / annotation units','Which units does this task require us to identify?'],['Coreference resolution','Which expressions refer to the same entity?'],['Part-of-speech analysis','Which grammatical class fits this occurrence?'],
    ],'Task distinctions for the practice cases');
    let parsed=C.parse(state.text),lm=C.languageModel(),metrics=C.evaluation();
    function drawParse() {
      if(disposed)return;
      get('parse-status').textContent=state.completed+' of '+parsed.events.length+' chart cells completed. Spans use half-open token boundaries [i,j).';
      const visible=new Map(C.visibleChart(parsed,state.completed).map(c=>[c.i+':'+c.j,c]));
      const rows=[];for(let i=0;i<parsed.n;i++){const row=[i+' · '+parsed.words[i]];for(let j=1;j<=parsed.n;j++){
        const c=visible.get(i+':'+j);row.push(j<=i?'—':!c?'not computed':Object.keys(c.entries).length?Object.entries(c.entries).map(([k,v])=>k+': '+v).join(', '):'∅');
      }rows.push(row);}
      table(get('chart'),['Start / token',...Array.from({length:parsed.n},(_,i)=>'End '+(i+1))],rows,'Constituent counts in each span');
      get('trace').replaceChildren();const event=parsed.events[state.completed-1];
      if(event){get('trace').append(element('p','Last cell ['+event.i+','+event.j+'): '+parsed.words.slice(event.i,event.j).join(' ')));
        const ul=element('ul',null);for(const a of event.contributions)ul.append(element('li',a.word?a.label+' → '+a.word+' contributes one lexical analysis.':a.label+' → '+a.left+' '+a.right+', split '+a.split+': '+a.leftCount+' × '+a.rightCount+' = '+a.ways+' alternative(s).'));
        if(!event.contributions.length)ul.append(element('li','No rule contributes a constituent to this span.'));get('trace').append(ul);
      }
      const done=state.completed===parsed.events.length;
      get('step').disabled=done;get('finish').disabled=done;get('previous-tree').disabled=!done||!parsed.count||state.rank===0;get('next-tree').disabled=!done||!parsed.count||state.rank+1>=parsed.count;for(const k of ['center-tree','start-tree','end-tree'])get(k).disabled=!done||!parsed.count;
      get('parse-result').textContent=done?'The full-span S count is '+parsed.count+'. '+(parsed.unknownWords.length?'Unknown word(s): '+parsed.unknownWords.join(', ')+'.':''):'Complete the chart to inspect full-sentence trees.';
      const plot=get('tree');plot.replaceChildren();let layout=null,chosen=null;
      if(done&&parsed.count){chosen=C.tree(parsed,state.rank);layout=C.treeLayout(chosen);plot.setAttribute('viewBox','0 0 '+layout.width+' '+layout.height);plot.style.minWidth=layout.width+'px';
        for(const e of layout.edges){const a=layout.positions[e.from],b=layout.positions[e.to];svg(plot,'line',{x1:a.x,y1:a.y+10,x2:b.x,y2:b.y-10,stroke:'#90aecb','stroke-width':2,'data-tree-edge':e.from+':'+e.to});}
        for(const p of layout.positions){const e=svg(plot,'text',{x:p.x,y:p.y,'text-anchor':'middle',fill:p.terminal?'#f8d27b':'#e5f1ff','font-size':p.terminal?16:15,'data-tree-node':p.id},p.label);e.dataset.source=JSON.stringify(p);}
        get('tree-status').textContent='Tree '+(state.rank+1)+' of '+parsed.count+'. Node spans cover exactly the displayed token sequence. The chart retains alternatives; it does not choose the intended attachment.';
      }else {plot.setAttribute('viewBox','0 0 600 120');plot.style.minWidth='480px';svg(plot,'text',{x:30,y:60,fill:'currentColor','font-size':16},done?'No complete tree is licensed by this grammar.':'Tree appears after the full chart is computed.');get('tree-status').textContent='';}
      root.languageReview={...root.languageReview,parser:{text:state.text,completed:state.completed,rank:state.rank,count:parsed.count,events:parsed.events,visible:[...visible.values()],tree:chosen,layout}};if(layout)centerTree();
    }
    function centerTree(){const layout=root.languageReview?.parser?.layout;if(disposed||!layout)return;const plot=get('tree'),v=plot.parentElement;v.scrollLeft=Math.max(0,layout.positions[0].x*plot.getBoundingClientRect().width/layout.width-v.clientWidth/2);}
    get('center-tree').onclick=centerTree;get('start-tree').onclick=()=>{get('tree').parentElement.scrollLeft=0;};get('end-tree').onclick=()=>{const v=get('tree').parentElement;v.scrollLeft=v.scrollWidth-v.clientWidth;};get('end-chart').onclick=()=>{const v=get('chart').parentElement;v.scrollLeft=v.scrollWidth-v.clientWidth;};
    function drawLM() {
      if(disposed)return;lm=C.languageModel(state.corpus,state.history,state.alpha);
      table(get('sentences'),['Sentence','Words'],lm.sentences.map((s,i)=>[i+1,s.join(' ')]),'Every training sentence in the selected sample');
      get('corpus-summary').textContent=lm.lexicalTokens+' lexical tokens; '+lm.types+' distinct word types; type–token ratio '+frac(lm.typeTokenRatio)+'.';
      get('lm-status').textContent='History '+state.history+': C(h) = '+lm.contextCount+', V = '+lm.vocabulary.length+'. '+(lm.rowDefined?'A conditional distribution is defined.':'No unsmoothed row can be estimated for this unseen history.');
      table(get('prediction-table'),['Next token','C(h,w)','P(w|h)'],lm.predictions.map(p=>[p.word,p.count,frac(p.probability)]),'Counts and estimated probabilities');
      const bars=get('bars');bars.replaceChildren();for(const p of [0,.25,.5,.75,1]){const x=85+200*p;svg(bars,'line',{x1:x,x2:x,y1:35,y2:365,stroke:'#496078'});svg(bars,'text',{x,y:390,'text-anchor':'middle',fill:'currentColor','font-size':12},p);}
      const barSource=[];lm.predictions.forEach((p,i)=>{const y=50+i*40;svg(bars,'text',{x:75,y:y+17,fill:'currentColor','font-size':14,'text-anchor':'end'},p.word);
        if(p.probability){const x=85,width=200*p.probability.value;const e=svg(bars,'rect',{x,y,width,height:22,fill:p.count?'#f2c86d':'#7dbce8','data-probability-bar':p.word});e.dataset.source=JSON.stringify(p);barSource.push({word:p.word,x,y,width,height:22,probability:p.probability});}
      });svg(bars,'text',{x:160,y:419,fill:'currentColor','font-size':13,'text-anchor':'middle'},lm.rowDefined?'Next-token probability (0–1)':'No estimated row');
      const map=get('map');map.replaceChildren();const edgeSource=[];
      const targets=lm.predictions.map((p,i)=>{const angle=-Math.PI/2+i*Math.PI/4;return{...p,x:160+120*Math.cos(angle),y:260+210*Math.sin(angle)};});
      for(const p of targets)if(p.probability&&p.probability.n>0){
        const dx=p.x-160,dy=p.y-260,n=Math.hypot(dx,dy),ux=dx/n,uy=dy/n,x2=p.x-ux*25,y2=p.y-uy*25;
        svg(map,'line',{x1:160,y1:260,x2,y2,stroke:p.count?'#f2c86d':'#7dbce8','stroke-width':2,'stroke-dasharray':p.count?'none':'5 4','data-transition':p.word});
        svg(map,'path',{d:`M ${x2-7*ux-3*uy} ${y2-7*uy+3*ux} L ${x2} ${y2} L ${x2-7*ux+3*uy} ${y2-7*uy-3*ux}`,fill:'none',stroke:'#e5f1ff','stroke-width':2});
        const lx=160+dx*.57,ly=260+dy*.57;svg(map,'rect',{x:lx-24,y:ly-13,width:48,height:19,fill:'#132034'});svg(map,'text',{x:lx,y:ly,fill:'#e5f1ff','font-size':12,'text-anchor':'middle'},p.probability.text);edgeSource.push({word:p.word,count:p.count,probability:p.probability,x1:160,y1:260,x2,y2});
      }
      for(const p of targets)svg(map,'text',{x:p.x,y:p.y+5,fill:'currentColor','font-size':14,'text-anchor':'middle'},p.word);
      svg(map,'rect',{x:107,y:242,width:106,height:36,fill:'#203c55',rx:5});svg(map,'text',{x:160,y:265,fill:'#f8d27b','font-size':13,'text-anchor':'middle'},'h: '+state.history);
      root.languageReview={...root.languageReview,lm:{...lm,bars:barSource,edges:edgeSource}};
      get('check-next').disabled=!lm.rowDefined;
    }
    function drawTask(){const a=C.ambiguity[state.caseIndex];get('task-prompt').textContent=(state.caseIndex+1)+' of '+C.ambiguity.length+'. '+a.prompt;root.languageReview={...root.languageReview,task:{id:a.id,index:state.caseIndex}};}
    function drawEvaluation(){
      if(disposed)return;metrics=C.evaluation(state.counts);get('metric-feedback').textContent='';
      table(get('confusion'),['Reference label','Predicted positive','Predicted negative'],[['Actual positive',metrics.tp+' (TP)',metrics.fn+' (FN)'],['Actual negative',metrics.fp+' (FP)',metrics.tn+' (TN)']], 'Confusion matrix: rows are reference labels; columns are predictions');
      table(get('metrics'),['Metric','Definition','Result'],[
        ['Precision','TP / (TP + FP)',frac(metrics.precision)],['Recall','TP / (TP + FN)',frac(metrics.recall)],['Accuracy','(TP + TN) / total',frac(metrics.accuracy)],['F1','2TP / (2TP + FP + FN)',frac(metrics.f1)],['Majority baseline','max(actual positives, actual negatives) / total',frac(metrics.majorityAccuracy)],
      ],'Metrics from the displayed counts');
      const plot=get('evaluation-bars');plot.replaceChildren();for(const t of [0,.25,.5,.75,1]){const x=95+200*t;svg(plot,'line',{x1:x,x2:x,y1:30,y2:180,stroke:'#496078'});svg(plot,'text',{x,y:215,fill:'currentColor','font-size':13,'text-anchor':'middle'},t);}
      const bars=[];for(const [i,[name,f]]of [['Accuracy',metrics.accuracy],['Recall',metrics.recall]].entries()){const y=55+70*i;svg(plot,'text',{x:80,y:y+20,fill:'currentColor','font-size':13,'text-anchor':'end'},name);
        if(f){const width=200*f.value;const e=svg(plot,'rect',{x:95,y,width,height:28,fill:i?'#7dbce8':'#f2c86d','data-metric-bar':name});e.dataset.fraction=f.text;bars.push({name,x:95,y,width,height:28,fraction:f});}else svg(plot,'text',{x:105,y:y+20,fill:'currentColor','font-size':14},'undefined');
      }
      get('evaluation-status').textContent='Total '+metrics.total+'; actual positives '+metrics.positives+'; actual negatives '+metrics.negatives+'. '+(metrics.majorityClass===null?'No examples means there is no majority baseline.':metrics.majorityClass==='tie'?'The reference classes are tied; either constant-class baseline has the same accuracy.':'A constant '+metrics.majorityClass+' prediction is the majority-class baseline.')+' Undefined ratios are not replaced by zero.';
      root.languageReview={...root.languageReview,evaluation:{...metrics,bars}};
    }
    function chooseSentence(text,id){
      try {const next=C.parse(text);parsed=next;state.text=text;state.sentence=id;get('sentence').value=id;state.completed=0;state.rank=0;get('sentence-text').value=text;get('parse-error').textContent='';get('parse-feedback').textContent='';drawParse();}
      catch(e){get('parse-error').textContent='Input not applied. '+e.message;}
    }
    get('sentence').onchange=e=>{const s=C.sentences.find(s=>s.id===e.target.value);if(s)chooseSentence(s.text,s.id);else get('sentence-text').focus();};
    get('use-sentence').onclick=()=>chooseSentence(get('sentence-text').value,'custom');
    get('step').onclick=()=>{state.completed=Math.min(parsed.events.length,state.completed+1);drawParse();};
    get('finish').onclick=()=>{state.completed=parsed.events.length;drawParse();};
    get('reset-parse').onclick=()=>{state.completed=0;state.rank=0;drawParse();get('parse-feedback').textContent='';};
    get('previous-tree').onclick=()=>{state.rank=Math.max(0,state.rank-1);drawParse();};
    get('next-tree').onclick=()=>{state.rank=Math.min(parsed.count-1,state.rank+1);drawParse();};
    get('check-parse').onclick=()=>{const n=get('parse-guess').valueAsNumber;if(!Number.isSafeInteger(n)||n<0){get('parse-feedback').textContent='Enter a nonnegative whole number.';return;}const r=C.feedback('parses',parsed,n);get('parse-feedback').textContent=(r.correct?'Correct. ':'Try again. ')+r.why;};
    for(const [id,key]of [['corpus','corpus'],['history','history'],['alpha','alpha']])get(id).onchange=e=>{state[key]=id==='alpha'?Number(e.target.value):e.target.value;get('next-feedback').textContent='';drawLM();};
    get('check-next').onclick=()=>{const r=C.feedback('next',lm,get('next-guess').value);get('next-feedback').textContent=(r.correct?'Correct. ':'Try again. ')+r.why;};
    get('check-task').onclick=()=>{const r=C.feedback('task',C.ambiguity[state.caseIndex],get('task-guess').value);get('task-feedback').textContent=(r.correct?'Correct. ':'Try again. ')+r.why;};
    get('next-task').onclick=()=>{state.caseIndex=(state.caseIndex+1)%C.ambiguity.length;get('task-feedback').textContent='';drawTask();};
    for(const k of ['tp','fp','fn','tn'])get(k).onchange=e=>{const n=e.target.valueAsNumber;if(!Number.isInteger(n)||n<0||n>100){e.target.value=state.counts[k];get('evaluation-error').textContent='Use whole-number counts from zero to 100.';return;}state.counts[k]=n;get('evaluation-error').textContent='';drawEvaluation();};
    function setCounts(counts){state.counts={...counts};for(const k of Object.keys(counts))get(k).value=counts[k];get('evaluation-error').textContent='';drawEvaluation();}
    get('default-counts').onclick=()=>setCounts({tp:30,fp:10,fn:20,tn:40});get('negative-counts').onclick=()=>setCounts({tp:0,fp:0,fn:5,tn:95});get('empty-counts').onclick=()=>setCounts({tp:0,fp:0,fn:0,tn:0});
    get('check-metric').onclick=()=>{const r=C.feedback('evaluation',metrics,get('metric-guess').value);get('metric-feedback').textContent=(r.correct?'Correct. ':'Try again. ')+r.why;};
    function show(station){state.station=station;for(const s of root.querySelectorAll('[data-panel]'))s.hidden=s.dataset.panel!==station;for(const b of root.querySelectorAll('[data-station]'))b.setAttribute('aria-pressed',String(b.dataset.station===station));root.dataset.station=station;}
    for(const b of root.querySelectorAll('[data-station]'))b.onclick=()=>show(b.dataset.station);
    drawParse();drawLM();drawTask();drawEvaluation();show(state.station);
    root.getModelSpeech=()=>[...root.querySelectorAll('h4,p,caption')].filter(e=>!e.closest('[hidden]')).map(e=>e.textContent).join(' ');
    if(hooks.speakButton)root.querySelector('h3').prepend(hooks.speakButton(root.getModelSpeech,'Read this language activity aloud'));
    root.dispose=()=>{if(disposed)return;disposed=true;life.disconnect();root.dataset.disposed='true';};
    const life=new MutationObserver(()=>{if(root.isConnected)mounted=true;else if(mounted)root.dispose();});life.observe(document,{subtree:true,childList:true});
    return root;
  }
  rootScope.PrimerLanguageComputationLab=Object.freeze({render});
})(globalThis);
