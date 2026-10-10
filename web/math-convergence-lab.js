/* Original convergence artwork and exact integer/rational tail certificates. */
(function () {
  'use strict';
  const NS='http://www.w3.org/2000/svg',MAX_N=160;
  const families=Object.freeze([
    ['reciprocal','Sequence: 1/n → 0'],['below','Sequence: 1 − 1/n → 1'],
    ['above','Sequence: 1 + 1/n → 1'],['geometric','Sequence: 2⁻ⁿ → 0'],
    ['alternating-decay','Sequence: (−1)ⁿ/n → 0'],['oscillating','Sequence: (−1)ⁿ; subsequences'],
    ['rational-root','Rational decimal approximations to √2'],
    ['uniform-ramp','Functions: x/n on [0,1]'],['powers','Functions: xⁿ on [0,1]'],
  ].map(([value,label])=>Object.freeze({value,label})));
  const initial=Object.freeze({family:'reciprocal',index:20,epsilon:10,sample:50});
  const controls=Object.freeze([
    {key:'index',label:'First tail index N',min:1,max:120,step:1,unit:''},
    {key:'epsilon',label:'Tolerance ε (hundredths)',min:1,max:200,step:1,unit:'/100'},
    {key:'sample',label:'Inspect input x (hundredths)',min:0,max:100,step:1,unit:'/100'},
  ].map(Object.freeze));
  const decimals=new Map();let serial=0;
  const fmt=n=>Number(n.toPrecision(7)).toString();
  function normalize(raw={}) {
    const state={family:families.some(f=>f.value===raw.family)?raw.family:initial.family};
    for(const c of controls)state[c.key]=Number.isFinite(Number(raw[c.key]))
      ?Math.max(c.min,Math.min(c.max,Math.round(Number(raw[c.key])))):initial[c.key];
    return state;
  }
  function isqrt(value) {
    if(value<0n)throw Error('Nonnegative integer required');if(value<2n)return value;
    let x=1n<<BigInt(Math.ceil(value.toString(2).length/2));
    for(;;){const next=(x+value/x)/2n;if(next>=x)return x;x=next;}
  }
  function decimalRoot(n) {
    if(!Number.isInteger(n)||n<1||n>MAX_N)throw Error('Decimal index outside displayed range');
    if(decimals.has(n))return decimals.get(n);
    const denominator=10n**BigInt(n),numerator=isqrt(2n*denominator*denominator);
    const residual=2n*denominator*denominator-numerator*numerator;
    const value=Number(numerator)/Number(denominator);
    // Rationalization avoids subtracting two rounded values near √2.
    const error=Number(residual)/Number(denominator)/Number(denominator)/(Math.SQRT2+value);
    const digits=numerator.toString().padStart(n+1,'0');
    const result={numerator,denominator,residual,value,error,decimal:digits.slice(0,-n)+'.'+digits.slice(-n)};
    decimals.set(n,result);return result;
  }
  const functionFamily=f=>f==='powers'||f==='uniform-ramp';
  function sequencePoint(f,n) {
    if(!Number.isInteger(n)||n<1||n>MAX_N)throw Error('Positive displayed sequence index required');
    if(f==='rational-root'){const q=decimalRoot(n);return {n,value:q.value,error:q.error,limit:Math.SQRT2};}
    const reciprocal=1/n,sign=n%2?-1:1;
    const value=f==='below'?1-reciprocal:f==='above'?1+reciprocal:f==='geometric'?2**(-n)
      :f==='oscillating'?sign:f==='alternating-decay'?sign*reciprocal:reciprocal;
    return {n,value,error:f==='geometric'?2**(-n):f==='oscillating'?1:reciprocal,
      limit:f==='below'||f==='above'?1:0};
  }
  function sequenceTail(f,N,e) {
    if(f==='oscillating')return e>100;
    if(f==='geometric')return (1n<<BigInt(N))*BigInt(e)>100n;
    if(f==='rational-root'){
      const q=decimalRoot(N),num=100n*q.numerator+BigInt(e)*q.denominator,den=100n*q.denominator;
      return num*num>2n*den*den;
    }
    return N*e>100;
  }
  function functionPoint(f,n,x) {
    const value=f==='powers'?x**n:x/n,limit=f==='powers'&&x===1?1:0;
    return {x,value,limit,error:Math.abs(value-limit)};
  }
  function functionTail(f,N,e) {
    // In x^n, sup error=1 is not attained: every point's error is strictly <1.
    return f==='powers'?e>=100:N*e>100;
  }
  function functionGrid(n) {
    const xs=new Set(Array.from({length:201},(_,i)=>i/200));
    for(let i=1;i<=120;i++){const x=1-Math.min(6,n)*i/(120*n);if(x>=0&&x<1)xs.add(x);}
    // Resolve the thin boundary layer while keeping the exact endpoint separate.
    for(const q of [.00001,.0001,.001,.01,.03,.1,.3,1])if(q<n)xs.add(1-q/n);
    return [...xs].sort((a,b)=>a-b);
  }
  function build(raw) {
    const state=normalize(raw),N=state.index,e=state.epsilon,epsilon=e/100;
    const functions=functionFamily(state.family);
    if(functions){
      const sample=functionPoint(state.family,N,state.sample/100),works=functionTail(state.family,N,e);
      const points=functionGrid(N).map(x=>functionPoint(state.family,N,x));
      const witness=state.family==='powers'&&e<100?((epsilon+1)/2)**(1/N):null;
      const proof=state.family==='powers'
        ? 'For every fixed x < 1, xⁿ → 0; at x = 1 every term is 1. For every n, supₓ |fₙ−f| = 1, not attained. '+
          (e>=100?'All actual errors are strictly below this chosen ε, including at ε = 1. This single tolerance does not imply uniform convergence.':'For any n ≥ N, xₙ = ((ε+1)/2)^(1/n) < 1 gives error (ε+1)/2 > ε.')+
          ' Taking ε = 0.5 disproves uniform convergence for every N; the pointwise limit is discontinuous.'
        : 'For every n ≥ N and x ∈ [0,1], |x/n−0| ≤ 1/n ≤ 1/N. The maximum 1/N is attained at x = 1, so the strict ε condition holds exactly when N × ε > 1. Choosing N = floor(1/ε)+1 proves uniform convergence.';
      return {state,functions,epsilon,works,sample,points,witness,sup:state.family==='powers'?1:1/N,proof,
        readout:`At N = ${N}, x = ${fmt(sample.x)}: f_N(x) = ${fmt(sample.value)}, f(x) = ${fmt(sample.limit)}, absolute error = ${fmt(sample.error)}. ε = ${fmt(epsilon)}. The complete infinite-tail tolerance condition is ${works?'satisfied':'not satisfied'} for this chosen ε.`};
    }
    const points=Array.from({length:MAX_N},(_,i)=>sequencePoint(state.family,i+1)),at=points[N-1];
    const works=sequenceTail(state.family,N,e);let required=null;
    if(state.family!=='oscillating')for(let n=1;n<=120;n++)if(sequenceTail(state.family,n,e)){required=n;break;}
    let proof=state.family==='oscillating'
      ? 'Every tail contains even terms +1 and odd terms −1. Each subsequence is constant and converges, but their different limits prove the whole sequence cannot converge to any L. For the candidate L = 0, all tail errors equal 1; the chosen band contains every term only when ε > 1. Passing one wide band does not prove convergence.'
      : state.family==='geometric'
      ? 'For every n ≥ N, |2⁻ⁿ−0| ≤ 2⁻ᴺ, with the maximum attained at N. The strict band condition is 2ᴺ × ε > 1. Integer cross-products certify the chosen tolerance without a rounded boundary comparison.'
      : state.family==='rational-root'
      ? 'Let d = 10ᴺ and k = floor(√2 d), certified by k² < 2d² < (k+1)². Every term is rational and increases or stays unchanged below √2. For all m,n ≥ N, |a_m−a_n| < √2−k/d < 10⁻ᴺ; this is a Cauchy tail. Its only real limit is irrational √2, so it has no limit in ℚ. The exact integer test (100k+e d)² > 2(100d)² certifies ε = e/100. A rounded point coinciding with √2 does not make the rational term equal to it.'
      : 'For every n ≥ N, |a_n−L| = 1/n ≤ 1/N. The maximum error is attained at N. Strict containment requires N × ε > 1, including the equality boundary. N = floor(1/ε)+1 is sufficient for every positive ε. '+
        (state.family==='below'?'The set {1−1/n} has supremum 1 and no maximum.':state.family==='above'?'The values approach 1 from above without reaching it.':state.family==='alternating-decay'?'Alternation does not prevent convergence when the error envelope tends to zero.':'');
    return {state,functions:false,epsilon,works,required,points,at,proof,
      exactDecimal:state.family==='rational-root'?decimalRoot(N).decimal:null,
      readout:`At the first included tail index N = ${N}: a_N = ${fmt(at.value)}, L = ${state.family==='rational-root'?'√2':fmt(at.limit)}, error = ${fmt(at.error)}, ε = ${fmt(epsilon)}. The full tail n ≥ N ${works?'lies strictly inside':'does not lie strictly inside'} this ε band. ${required===null?'':`Smallest valid N for this chosen tolerance: ${required}. `}`};
  }
  function element(tag,attrs={},...children){const e=document.createElement(tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,String(v)));children.forEach(c=>{if(c!=null)e.append(c.nodeType?c:document.createTextNode(String(c)));});return e;}
  function svgNode(tag,attrs={},value){const e=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,String(v)));if(value!=null)e.textContent=String(value);return e;}
  function render(item,hooks){
    if(item?.props?.scenario!=='math.4.analysis.convergence')return null;
    const uid='convergence-'+ ++serial,root=element('section',{class:'card lesson-model math-convergence-lab','data-renderer':'math-convergence-lab','aria-labelledby':uid+'-title'});
    let model=build(initial),enlarged=false;
    const readout=element('p',{class:'convergence-readout'}),proof=element('p',{class:'convergence-proof'}),live=element('p',{role:'status','aria-live':'polite','aria-atomic':'true'});
    const choose=element('select',{'aria-label':'Convergence example','data-convergence-family':''});families.forEach(f=>choose.append(element('option',{value:f.value},f.label)));
    choose.addEventListener('change',()=>{model=build({...model.state,family:choose.value});refresh(true);});
    const widgets=new Map(),inputs=element('div',{class:'model-controls concept-controls'});
    for(const c of controls){const id=uid+'-'+c.key,input=element('input',{id,type:'range',min:c.min,max:c.max,step:c.step,'data-convergence-control':c.key}),output=element('output',{for:id});
      input.addEventListener('input',()=>{model=build({...model.state,[c.key]:Number(input.value)});refresh(false);});input.addEventListener('change',()=>{live.textContent=model.readout;});
      inputs.append(element('label',{class:'model-range-control',for:id},c.label,output,input));widgets.set(c.key,{input,output,c});}
    const panels=element('div',{class:'convergence-panels'}),views=[];
    for(let i=0;i<2;i++){const svg=svgNode('svg',{viewBox:'0 0 440 350',role:'img',focusable:'false','aria-labelledby':uid+'-plot-title-'+i,'aria-describedby':uid+'-plot-desc-'+i});panels.append(element('div',{class:'convergence-viewport',tabindex:0,role:'region','aria-label':i?'Error and tolerance; enlarge and scroll':'Values and their limit; enlarge and scroll'},svg));views.push(svg);}
    const exact=element('details',{class:'convergence-exact'},element('summary',{},'Exact rational decimal at N')),decimal=element('p',{class:'convergence-decimal'});exact.append(decimal);
    const reset=element('button',{type:'button',class:'btn ghost small','data-convergence-action':'reset'},'Reset');reset.addEventListener('click',()=>{model=build(initial);refresh(true);});
    const enlarge=element('button',{type:'button',class:'btn ghost small','aria-pressed':'false','data-convergence-action':'enlarge'},'Enlarge plots');enlarge.addEventListener('click',()=>{enlarged=!enlarged;root.classList.toggle('is-enlarged',enlarged);enlarge.setAttribute('aria-pressed',String(enlarged));enlarge.textContent=enlarged?'Fit plots':'Enlarge plots';});
    root.append(element('div',{class:'model-heading-row'},element('h3',{id:uid+'-title'},item.title||'What an entire tail must do'),enlarge),
      element('p',{class:'model-instructions'},item.instructions||'Choose a sequence or function family. Test a complete tail, not just the visible points.'),choose,inputs,reset,panels,proof,readout,exact,
      element('p',{class:'spatial-note'},'The convention here includes n = N: every n ≥ N must satisfy the strict inequality. ε is e/100 with integer e. Blue marks data or the selected finite function; coral marks the limit or its boundary. Sequence points are discrete, not connected trajectories. The sequence display shows only n = 1…160; integer/rational inequalities, not that finite sample, certify or disprove its infinite tail. Its second plot is log₁₀ absolute error with the actual logarithmic ε boundary. Positive tiny errors are retained in scientific notation. Rational decimals are exact; plotted values and the √2 readout are rounded, and the error is evaluated through a rationalized residual to avoid false zero from subtraction. For functions, open endpoint markers are excluded limit values/suprema and filled markers are actual endpoint values. Adaptive samples resolve the boundary layer, but the continuum/infinite-index conclusions come from the stated proof. These examples do not prove every convergence theorem, interchange of limits, derivative, integral or infinite series.'),
      element('p',{class:'spatial-note'},element('a',{href:'https://ocw.mit.edu/courses/18-100b-real-analysis-spring-2025/pages/lecture-notes/',target:'_blank',rel:'noopener noreferrer'},'Sequence, Cauchy and uniform convergence · MIT lecture notes'),' · Original code and artwork; no course figure reproduced.'),live);
    if(hooks?.speakButton)root.append(hooks.speakButton(()=>model.readout+' '+model.proof));
    function line(svg,a,b,colour,attrs={}){svg.append(svgNode('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:colour,'stroke-width':1.5,...attrs}));}
    function text(svg,x,y,value,attrs={}){svg.append(svgNode('text',{x,y,fill:'#263b46','font-size':12,...attrs},value));}
    function dot(svg,x,y,colour,open=false,attrs={}){svg.append(svgNode('circle',{cx:x,cy:y,r:3.2,fill:open?'#f5efdf':colour,stroke:colour,'stroke-width':1.5,...attrs}));}
    function plot(i,title,x0,x1,y0,y1,xlabel,ylabel){const svg=views[i];svg.replaceChildren(svgNode('title',{id:uid+'-plot-title-'+i},title),svgNode('desc',{id:uid+'-plot-desc-'+i},model.readout),svgNode('rect',{x:0,y:0,width:440,height:350,rx:10,fill:'#f5efdf'}));
      const X=x=>72+338*(x-x0)/(x1-x0),Y=y=>275-211*(y-y0)/(y1-y0);text(svg,20,25,title,{'font-size':15,'font-weight':600});text(svg,20,47,ylabel);
      for(let n=0;n<=4;n++){const x=model.functions?x0+(x1-x0)*n/4:Math.round(x0+(x1-x0)*n/4),y=y0+(y1-y0)*n/4;line(svg,[X(x),64],[X(x),275],'#d5cfbf');line(svg,[72,Y(y)],[410,Y(y)],'#d5cfbf');text(svg,X(x),297,fmt(x),{'text-anchor':'middle'});text(svg,64,Y(y)+4,fmt(y),{'text-anchor':'end'});}
      text(svg,241,329,xlabel,{'text-anchor':'middle'});return {svg,X,Y};}
    function curve(p,points,colour,attrs={}){p.svg.append(svgNode('path',{d:points.map((v,i)=>(i?'L':'M')+p.X(v[0])+' '+p.Y(v[1])).join(' '),fill:'none',stroke:colour,'stroke-width':2,...attrs}));}
    function refresh(announce){const m=model,s=m.state;choose.value=s.family;root.setAttribute('data-convergence-state',JSON.stringify(s));
      for(const {input,output,c} of widgets.values()){input.value=s[c.key];input.disabled=c.key==='sample'&&!m.functions;output.textContent=c.key==='epsilon'?'ε = '+fmt(m.epsilon):c.key==='sample'?(m.functions?'x = '+fmt(s.sample/100):'Not used for sequences'):String(s.index);input.setAttribute('aria-valuetext',output.textContent);}
      proof.textContent=m.proof;readout.textContent=m.readout;exact.hidden=!m.exactDecimal;decimal.textContent=m.exactDecimal||'';
      if(!m.functions){const p=plot(0,'Discrete values and limit',1,MAX_N,-2.1,3.6,'Index n (integers)','a_n');
        p.svg.append(svgNode('rect',{x:p.X(s.index),y:64,width:410-p.X(s.index),height:211,fill:'#e7d4a9','fill-opacity':.3,'data-convergence-tail':'true'}));
        const L=m.at.limit;line(p.svg,[72,p.Y(L)],[410,p.Y(L)],'#b96652');
        for(const sign of [-1,1])line(p.svg,[72,p.Y(L+sign*m.epsilon)],[410,p.Y(L+sign*m.epsilon)],'#317e78',{'stroke-dasharray':'5 4'});
        line(p.svg,[p.X(s.index),64],[p.X(s.index),275],'#926f27',{'stroke-dasharray':'4 3'});
        for(const q of m.points)dot(p.svg,p.X(q.n),p.Y(q.value),q.n>=s.index?'#3e7085':'#87999c',false,{'data-convergence-term':q.n,'data-value':q.value,r:q.n===s.index?3.5:.8});
        const min=Math.floor(Math.min(...m.points.map(q=>Math.log10(q.error)))-1),e=plot(1,'Positive error on a logarithmic axis',1,MAX_N,min,.5,'Index n (integers)','log₁₀ |a_n − L|');
        line(e.svg,[72,e.Y(Math.log10(m.epsilon))],[410,e.Y(Math.log10(m.epsilon))],'#317e78',{'stroke-dasharray':'5 4','data-convergence-epsilon':m.epsilon});
        for(const q of m.points)dot(e.svg,e.X(q.n),e.Y(Math.log10(q.error)),'#3e7085',false,{'data-convergence-error':q.n,'data-error':q.error,r:q.n===s.index?3.5:.8});
      }else{const p=plot(0,'Finite function and pointwise limit',0,1,-.1,1.1,'Input x','f_N(x), f(x)');curve(p,m.points.map(q=>[q.x,q.value]),'#3e7085');
        line(p.svg,[p.X(0),p.Y(0)],[p.X(1),p.Y(0)],'#b96652');dot(p.svg,p.X(1),p.Y(0),'#b96652',s.family==='powers');
        if(s.family==='powers')dot(p.svg,p.X(1),p.Y(1),'#b96652');
        dot(p.svg,p.X(m.sample.x),p.Y(m.sample.value),'#926f27',false,{'data-convergence-sample':'value'});
        const e=plot(1,'Absolute error and strict tolerance',0,1,-.1,2.1,'Input x','|f_N(x) − f(x)|');
        curve(e,m.points.filter(q=>s.family!=='powers'||q.x<1).map(q=>[q.x,q.error]),'#3e7085');
        dot(e.svg,e.X(1),e.Y(s.family==='powers'?1:1/s.index),'#3e7085',s.family==='powers',{'data-convergence-supremum':m.sup,'data-attained':s.family!=='powers'});
        if(s.family==='powers')dot(e.svg,e.X(1),e.Y(0),'#3e7085');
        line(e.svg,[72,e.Y(m.epsilon)],[410,e.Y(m.epsilon)],'#317e78',{'stroke-dasharray':'5 4','data-convergence-epsilon':m.epsilon});
        dot(e.svg,e.X(m.sample.x),e.Y(m.sample.error),'#926f27',false,{'data-convergence-sample':'error'});
        if(m.witness!==null)dot(e.svg,e.X(m.witness),e.Y((m.epsilon+1)/2),'#b96652',false,{'data-convergence-witness':m.witness});
      }
      if(announce)live.textContent=m.readout;
    }
    refresh(false);return root;
  }
  const api=Object.freeze({families,initial,controls,MAX_N,normalize,isqrt,decimalRoot,sequencePoint,sequenceTail,functionPoint,functionTail,functionGrid,build,render});
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else globalThis.PrimerMathConvergenceLab=api;
})();
