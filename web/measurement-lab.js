/* Original measurement teaching models and SVG artwork. No data collection.
   Definitions: NIST TN 1297, Appendix A; JCGM 100:2008 sections 4–5.
   Standard uncertainties, bounded inputs and synthetic errors remain separate. */
(function (host) {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const C = Object.freeze({ink:'#263b46', blue:'#316e88', teal:'#26756c', coral:'#b14d3c', gold:'#8b641a', grid:'#c8d1d5', paper:'#fffdf7'});
  const copy = value => JSON.parse(JSON.stringify(value));
  const fmt = value => value === 0 ? '0' : String(Number(value.toPrecision(6)));
  const axisFmt = value => value === 0 ? '0' : Math.abs(value)<.001||Math.abs(value)>=10000 ? value.toExponential(2) : String(Number(value.toPrecision(4)));
  const finite = (value, name, low=-1e6, high=1e6) => {
    if (typeof value !== 'number' || !Number.isFinite(value) || value < low || value > high) throw new RangeError(name + ' must be finite and in [' + low + ', ' + high + '].');
    return value;
  };
  function uncertainty(value, name) {
    finite(value,name,0,1e6);
    if (value > 0 && value < 1e-12) throw new RangeError(name + ' must be zero or at least 10⁻¹² in its stated SI unit.');
    return value;
  }
  const operations = Object.freeze({
    sum: Object.freeze({label:'Voltage sum A + B', a:'Voltage A (V)', b:'Voltage B (V)', unit:'V', inputUnits:['V','V'], formula:'y = A + B', nonlinear:false}),
    difference: Object.freeze({label:'Voltage difference A − B', a:'Voltage A (V)', b:'Voltage B (V)', unit:'V', inputUnits:['V','V'], formula:'y = A − B', nonlinear:false}),
    ratio: Object.freeze({label:'Speed L / t', a:'Length L (m)', b:'Time t (s)', unit:'m/s', inputUnits:['m','s'], formula:'v = L / t', nonlinear:true}),
    gravity: Object.freeze({label:'Pendulum estimate 4π²L / T²', a:'Pendulum length L (m)', b:'Period T (s)', unit:'m/s²', inputUnits:['m','s'], formula:'g = 4π²L / T²', nonlinear:true})
  });
  function model(operation, a, b) {
    const spec=operations[operation]; if(!spec)throw new RangeError('Unknown measurement model.');
    finite(a,'A'); finite(b,'B');
    if(spec.nonlinear && (a<0||b<1e-6))throw new RangeError('Length must be nonnegative and time at least 10⁻⁶ s.');
    let value,gradient;
    if(operation==='sum'){value=a+b;gradient=[1,1];}
    if(operation==='difference'){value=a-b;gradient=[1,-1];}
    if(operation==='ratio'){value=a/b;gradient=[1/b,-a/(b*b)];}
    if(operation==='gravity'){value=4*Math.PI*Math.PI*a/(b*b);gradient=[4*Math.PI*Math.PI/(b*b),-8*Math.PI*Math.PI*a/(b*b*b)];}
    return {...spec,operation,a,b,value,gradient};
  }
  function propagate({operation,a,b,ua,ub,rho=0}) {
    const m=model(operation,a,b);uncertainty(ua,'u(A)');uncertainty(ub,'u(B)');finite(rho,'Correlation ρ',-1,1);
    const [ga,gb]=m.gradient, x=ga*ua,y=gb*ub;
    // PSD decomposition retains exact cancellation at ρ=±1 and avoids negative
    // variances from cancellation of three separately rounded terms.
    const variance=(x+rho*y)**2+(1-rho*rho)*y*y;
    const standard=Math.sqrt(variance),covariance=rho*ua*ub;
    return {...m,ua,ub,rho,covariance,variance,standard,
      varianceTerms:[x*x,y*y,2*x*y*rho],relativeStandard:m.value===0?null:standard/Math.abs(m.value),
      denominatorRelativeStandard:m.nonlinear?ub/b:null,
      firstOrderApproximation:m.nonlinear,
      interpretation:m.nonlinear?'Local first-order standard uncertainty; the input moments do not specify a distribution or bound the denominator.':'Exact variance relation for this linear measurement model, with the supplied covariance.'};
  }
  function interval({operation,a,b,da,db}) {
    const m=model(operation,a,b);uncertainty(da,'Bound half-width of A');uncertainty(db,'Bound half-width of B');
    const aBounds=[a-da,a+da],bBounds=[b-db,b+db];
    if(m.nonlinear && (aBounds[0]<0||bBounds[0]<1e-6))throw new RangeError('The whole length interval must be nonnegative and the time interval must stay at or above 10⁻⁶ s.');
    const corners=aBounds.flatMap(A=>bBounds.map(B=>({a:A,b:B,value:model(operation,A,B).value})));
    const low=Math.min(...corners.map(p=>p.value)),high=Math.max(...corners.map(p=>p.value));
    const linearizedHalfWidth=Math.abs(m.gradient[0])*da+Math.abs(m.gradient[1])*db;
    return {...m,da,db,aBounds,bBounds,corners,low,high,linearizedHalfWidth,
      linearizedInterval:[m.value-linearizedHalfWidth,m.value+linearizedHalfWidth],
      interpretation:'Bounds define a rectangular set of allowed input pairs. No probability distribution, standard uncertainty or coverage probability is inferred.'};
  }
  function repeatBudget({n,readingStd,calibrationStd,resolution,resolutionMode='included-in-scatter',target=5,offset=.2,correction=.2}) {
    if(!Number.isSafeInteger(n)||n<1||n>1000000)throw new RangeError('Repeat count must be an integer in [1, 1000000].');
    uncertainty(readingStd,'Single-reading standard deviation');uncertainty(calibrationStd,'Shared calibration standard uncertainty');uncertainty(resolution,'Resolution step');
    for(const [name,v]of Object.entries({target,offset,correction}))finite(v,name);
    if(!['included-in-scatter','independent-uniform','shared-uniform'].includes(resolutionMode))throw new RangeError('Unknown resolution model.');
    const readingVariance=readingStd*readingStd/n;
    const resolutionVariance=resolutionMode==='included-in-scatter'?0:resolution*resolution/12/(resolutionMode==='independent-uniform'?n:1);
    const calibrationVariance=calibrationStd*calibrationStd;
    const variance=readingVariance+resolutionVariance+calibrationVariance;
    const floorVariance=calibrationVariance+(resolutionMode==='shared-uniform'?resolution*resolution/12:0);
    return {n,readingStd,calibrationStd,resolution,resolutionMode,target,offset,correction,
      expectedRaw:target+offset,expectedCorrected:target+offset-correction,residualOffset:offset-correction,
      readingVariance,resolutionVariance,calibrationVariance,variance,standard:Math.sqrt(variance),floor:Math.sqrt(floorVariance),
      interpretation:'Repeat scatter is independent with a supplied single-reading standard deviation. Calibration is shared and independent of the scatter. A recognized offset is corrected separately; uncertainty is not the signed error.'};
  }
  const sum = values => {let total=0,c=0;for(const v of values){const y=v-c,t=total+y;c=(t-total)-y;total=t;}return total;};
  function weightedLineFit(rows,{mode='fit',intercept:knownIntercept=1,slope:knownSlope=.5}={}) {
    if(!Array.isArray(rows)||rows.length<3||rows.length>10000)throw new RangeError('Supply 3–10000 observations.');
    if(!['fit','reference'].includes(mode))throw new RangeError('Unknown fit mode.');
    const points=rows.map((r,i)=>({x:finite(r.x,'x['+i+']'),y:finite(r.y,'y['+i+']'),sigma:finite(r.sigma,'σ['+i+']',1e-9,1e6)}));
    finite(knownIntercept,'Reference intercept');finite(knownSlope,'Reference slope');
    const weights=points.map(r=>1/(r.sigma*r.sigma)),W=sum(weights),x0=points[0].x,y0=points[0].y;
    const dxbar=sum(points.map((r,i)=>weights[i]*(r.x-x0)))/W,dybar=sum(points.map((r,i)=>weights[i]*(r.y-y0)))/W;
    const xbar=x0+dxbar,ybar=y0+dybar;
    // Preserve small relative coordinates: adding the mean offset to a large
    // origin can round it away before the second central moment is formed.
    const centeredX=points.map(r=>(r.x-x0)-dxbar),centeredY=points.map(r=>(r.y-y0)-dybar);
    const Sxx=sum(points.map((r,i)=>weights[i]*centeredX[i]**2));
    const Sxy=sum(points.map((r,i)=>weights[i]*centeredX[i]*centeredY[i]));
    if(mode==='fit' && !(Sxx>0))throw new RangeError('A free line requires distinct x coordinates.');
    if(mode==='fit' && (Sxx<2.2250738585072014e-308||!Number.isFinite(1/Sxx)||!Number.isFinite(xbar*xbar/Sxx)))throw new RangeError('The x spread cannot represent a finite, reliable parameter covariance; rescale the x coordinates.');
    const slope=mode==='fit'?Sxy/Sxx:knownSlope,intercept=mode==='fit'?(y0-slope*x0)+(dybar-slope*dxbar):knownIntercept;
    const varianceSlope=mode==='fit'?1/Sxx:0,varianceIntercept=mode==='fit'?1/W+xbar*xbar/Sxx:0;
    const covariance=mode==='fit'?-xbar/Sxx:0;
    const data=points.map((p,i)=>{
      const fitted=mode==='fit'?y0+(dybar+slope*centeredX[i]):intercept+slope*p.x;
      const residual=mode==='fit'?centeredY[i]-slope*centeredX[i]:p.y-fitted,normalized=residual/p.sigma;
      const meanVariance=mode==='fit'?1/W+centeredX[i]**2/Sxx:0;
      return {...p,fitted,residual,normalized,weight:weights[i],meanStandard:Math.sqrt(meanVariance),leverage:mode==='fit'?weights[i]*meanVariance:0};
    });
    const chiSquare=sum(data.map(r=>r.normalized*r.normalized)),parametersEstimated=mode==='fit'?2:0,degreesOfFreedom=data.length-parametersEstimated;
    return {mode,rows:data,count:data.length,intercept,slope,xbar,ybar,origin:{x:x0,y:y0},meanOffsets:{x:dxbar,y:dybar},Sxx,Sxy,weightSum:W,
      parameterCovariance:[[varianceIntercept,covariance],[covariance,varianceSlope]],
      interceptStandard:Math.sqrt(varianceIntercept),slopeStandard:Math.sqrt(varianceSlope),
      chiSquare,reducedChiSquare:chiSquare/degreesOfFreedom,degreesOfFreedom,parametersEstimated,
      rawMean:sum(points.map(p=>p.y))/points.length,
      interpretation:'x is exact; supplied σ values are known independent y standard uncertainties. Parameter covariance is not multiplied by reduced χ². A chi-square distribution interpretation additionally assumes Gaussian errors and the correct mean model. Fitted residuals themselves are correlated.'};
  }
  function summarizeReadings(values) {
    if(!Array.isArray(values)||values.length<1||values.length>10000)throw new RangeError('Supply 1–10000 readings.');
    values.forEach((v,i)=>finite(v,'Reading '+i));
    const origin=values[0],offset=sum(values.map(v=>v-origin))/values.length,mean=origin+offset;
    const sampleVariance=values.length<2?null:sum(values.map(v=>((v-origin)-offset)**2))/(values.length-1);
    return {count:values.length,mean,sampleVariance,sampleStandardDeviation:sampleVariance===null?null:Math.sqrt(sampleVariance),standardError:sampleVariance===null?null:Math.sqrt(sampleVariance/values.length)};
  }
  const repeatReadings=Object.freeze([4.8,5.0,5.1,4.9,5.2]);
  const residualPattern=Object.freeze([-.7,.25,.9,-.35,.5,-.8,.1,.65,-.45,.3,-.15,.75]);
  function fitExample({scatter=.3,offset=0,acceleration=0,outlier=0,sigma=.3,heterogeneous=false,mode='fit'}={}) {
    finite(scatter,'Synthetic scatter scale',0,2);finite(offset,'Synthetic calibration offset',-3,3);finite(acceleration,'Unmodelled acceleration',-.2,.2);finite(outlier,'Extra shift of point 9',-5,5);finite(sigma,'Supplied y standard uncertainty',.01,3);
    if(typeof heterogeneous!=='boolean')throw new TypeError('heterogeneous must be boolean.');
    const rows=residualPattern.map((r,i)=>({x:i,y:1+.5*i+offset+.5*acceleration*i*i+scatter*r+(i===8?outlier:0),sigma:sigma*(heterogeneous?1+i/11:1)}));
    return {...weightedLineFit(rows,{mode}),sourceState:{scatter,offset,acceleration,outlier,sigma,heterogeneous,mode},reference:{intercept:1,slope:.5},
      syntheticNote:'Twelve fixed irregular teaching residuals, not a random sample or empirical evidence of independence. All points, including point 9, remain in the fit.'};
  }
  const defaults=Object.freeze({
    station:'fit',
    propagation:Object.freeze({operation:'ratio',a:10,b:2,ua:.1,ub:.04,rho:0}),
    bounds:Object.freeze({operation:'ratio',a:10,b:2,da:.1,db:.04}),
    repeats:Object.freeze({n:25,readingStd:.2,calibrationStd:.05,resolution:.1,resolutionMode:'included-in-scatter',target:5,offset:.2,correction:.2}),
    fit:Object.freeze({scatter:.3,offset:0,acceleration:0,outlier:0,sigma:.3,heterogeneous:false,mode:'fit'})
  });
  let serial=0;
  function render(item={},hooks={},frame=null) {
    if(item.props?.scenario && item.props.scenario!=='phys.4.experiment')return null;
    const doc=host.document;if(!doc)throw new Error('Rendering requires a browser document.');
    const el=(tag,attrs={},...children)=>{const e=doc.createElement(tag);for(const[k,v]of Object.entries(attrs)){if(k==='style')Object.assign(e.style,v);else e.setAttribute(k,String(v));}e.append(...children.map(v=>typeof v==='object'?v:doc.createTextNode(String(v))));return e;};
    const svgEl=(tag,attrs={},text)=>{const e=doc.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=String(text);return e;};
    const uid='measurement-'+(++serial),shell=frame||{};
    const root=shell.root||el('section',{class:'card lesson-model measurement-lab','aria-labelledby':uid+'-title'});
    root.setAttribute('data-measurement-lab','true');root.style.minWidth='0';root.style.maxWidth='100%';
    const main=el('div',{style:{display:'block',width:'100%',minWidth:'0',textAlign:'left',boxSizing:'border-box'}});
    const readout=shell.readout||el('p',{}),live=shell.status||el('p',{role:'status','aria-live':'polite','aria-atomic':'true'});
    if(frame){shell.canvas.style.display='block';shell.canvas.style.width='100%';shell.canvas.style.minHeight='0';shell.canvas.style.minWidth='0';shell.canvas.append(main);}
    else{const heading=el('h3',{id:uid+'-title'},item.title||'Measurement workbench');root.append(heading,el('p',{},'Compare measurement models, declared uncertainty assumptions and every original observation.'),main,readout,live);if(hooks?.speakButton)heading.prepend(hooks.speakButton(()=>readout.getAttribute('data-measurement-speech')||readout.textContent,'Read this activity aloud'));}
    const state=copy(defaults),models={};let enlarged=false;
    const station=el('select',{'aria-label':'Measurement station','data-measurement-control':'station',style:{font:'inherit',maxWidth:'100%',padding:'8px'}});
    const names={fit:'Fit, residuals and calibration',propagation:'Standard uncertainty and covariance',bounds:'Bounded inputs and exact intervals',repeats:'Repeatability, resolution and shared uncertainty'};
    for(const[k,v]of Object.entries(names))station.append(el('option',{value:k},v));station.value=state.station;
    const choose=el('label',{for:uid+'-station',style:{display:'block',fontWeight:'600'}},'Measurement station');station.id=uid+'-station';choose.append(station);
    const button=(text,action,attrs={})=>{const b=el('button',{type:'button',class:'btn ghost small',style:{font:'inherit',minHeight:'44px',whiteSpace:'normal',margin:'4px'},...attrs},text);b.addEventListener('click',action);return b;};
    const zoom=button('Enlarge plots',()=>{enlarged=!enlarged;size();},{'aria-pressed':'false','data-measurement-action':'enlarge'});
    const reset=button('Reset workbench',()=>{Object.assign(state,copy(defaults));station.value=state.station;for(const p of Object.values(panels))p.sync();enlarged=false;size();show();refresh(true);},{'data-measurement-action':'reset'});
    main.append(el('div',{style:{display:'flex',flexWrap:'wrap',gap:'10px',alignItems:'end'}},choose,zoom,reset));
    const panels={};
    function panel(key,note) {
      const section=el('section',{'data-measurement-panel':key,style:{minWidth:'0'}}),heading=el('h4',{},names[key]);
      const form=el('div',{style:{display:'flex',flexWrap:'wrap',gap:'12px',alignItems:'end',margin:'12px 0'}});
      const presetHost=el('div',{}),output=el('div',{'data-measurement-output':key}),noteEl=el('p',{},note),widgets=new Map();
      section.append(heading,noteEl,form,presetHost,output);main.append(section);
      const record={section,form,presetHost,output,noteEl,widgets,sync(){for(const[k,w]of widgets){if(w.input.type==='checkbox')w.input.checked=state[key][k];else w.input.value=String(state[key][k]);w.input.removeAttribute('aria-invalid');}}};panels[key]=record;return record;
    }
    function control(key,field,label,{min,max,step='any',options,boolean=false}={}) {
      const p=panels[key],id=uid+'-'+key+'-'+field,caption=el('span',{},label),input=el(options?'select':'input',{id,'data-measurement-control':key+'.'+field,style:{font:'inherit',padding:'7px',maxWidth:'100%',width:options?'auto':'9em',boxSizing:'border-box'}});
      if(options){for(const [v,t]of options)input.append(el('option',{value:v},t));}
      else{input.type=boolean?'checkbox':'number';if(!boolean){if(min!==undefined)input.min=min;if(max!==undefined)input.max=max;input.step=step;}}
      const wrap=el('label',{for:id,style:{display:'flex',flexDirection:'column',gap:'4px',maxWidth:'100%',fontSize:'.95rem'}},caption,input);p.form.append(wrap);p.widgets.set(field,{input,caption});
      input.addEventListener('change',()=>{state[key][field]=options?input.value:boolean?input.checked:input.valueAsNumber;refresh(true,key);});return input;
    }
    function presets(key,rows){for(const [label,patch]of rows)panels[key].presetHost.append(button(label,()=>{state[key]={...state[key],...patch};panels[key].sync();refresh(true,key);},{'data-measurement-preset':label}));}
    panel('propagation','Inputs are estimates with supplied standard uncertainties and correlation. No distribution or coverage probability is inferred. The sum/difference variance is exact for a linear model; ratios and inverse-square models use local first-order propagation.');
    panel('bounds','Enter half-widths of allowed input intervals. Every pair in the input rectangle is permitted. This is set propagation, not a probability model. Exact endpoint ranges are compared with a separately labelled first-order estimate.');
    for(const key of ['propagation','bounds']){
      control(key,'operation','Measurement model',{options:Object.entries(operations).map(([k,v])=>[k,v.label])});
      control(key,'a','Input A',{min:-100,max:100});control(key,'b','Input B',{min:-100,max:100});
      if(key==='propagation'){control(key,'ua','u(A)',{min:0,max:10});control(key,'ub','u(B)',{min:0,max:10});control(key,'rho','Input correlation ρ',{min:-1,max:1,step:.1});}
      else{control(key,'da','Half-width of A',{min:0,max:10});control(key,'db','Half-width of B',{min:0,max:10});}
    }
    presets('propagation',[
      ['Independent voltage sum',{operation:'sum',a:3,b:4,ua:.3,ub:.4,rho:0}],
      ['Speed: 1% and 2%',{...defaults.propagation}],
      ['Shared offset cancels',{operation:'difference',a:1.52,b:1.28,ua:.2,ub:.2,rho:1}],
      ['Period: 1% gives 2%',{operation:'gravity',a:1,b:2,ua:0,ub:.02,rho:0}]
    ]);
    presets('bounds',[
      ['Small speed bounds',{...defaults.bounds}],
      ['Large denominator range',{operation:'ratio',a:10,b:2,da:1,db:1.5}],
      ['Equal voltage bounds',{operation:'difference',a:1.52,b:1.28,da:.2,db:.2}]
    ]);
    panel('repeats','The supplied single-reading standard deviation comes from an independent repeatability assessment. Its contribution falls as 1/√n. Shared calibration uncertainty persists. A known synthetic offset and its applied correction are separate from uncertainty. Resolution adds Δ/√12 only under the explicitly selected rectangular ±Δ/2 model; do not add it again if already represented in the observed scatter.');
    control('repeats','n','Independent repeat count n',{min:1,max:400,step:1});
    control('repeats','readingStd','Single-reading standard deviation (V)',{min:0,max:2});
    control('repeats','calibrationStd','Shared calibration u (V)',{min:0,max:1});
    control('repeats','resolution','Resolution step Δ (V)',{min:0,max:1});
    control('repeats','resolutionMode','Resolution contribution',{options:[['included-in-scatter','Already included in scatter: no extra term'],['shared-uniform','Additional uniform error shared by every repeat'],['independent-uniform','Additional independent uniform phases per repeat']]});
    control('repeats','offset','Known synthetic instrument offset (V)',{min:-1,max:1});control('repeats','correction','Offset correction subtracted (V)',{min:-1,max:1});
    presets('repeats',[
      ['Use five-reading example',{n:5,readingStd:summarizeReadings(repeatReadings).sampleStandardDeviation,resolution:.1,resolutionMode:'included-in-scatter',offset:0,correction:0}],
      ['400 readings, uncorrected bias',{n:400,readingStd:.2,calibrationStd:.01,resolution:.1,resolutionMode:'included-in-scatter',offset:.2,correction:0}],
      ['Correct offset, retain uncertainty',{...defaults.repeats,n:400}],
      ['Identical rounding phase',{n:400,readingStd:0,calibrationStd:0,resolution:.1,resolutionMode:'shared-uniform'}],
      ['Independent rounding phases',{n:400,readingStd:0,calibrationStd:0,resolution:.1,resolutionMode:'independent-uniform'}]
    ]);
    panel('fit','Twelve synthetic position readings at exactly known times. The irregular residual pattern is fixed, not evidence of randomness. Supply independent y standard uncertainties σ; x uncertainty is neglected. A free line estimates two parameters. Parameter covariance uses the supplied σ and is never silently scaled by residual scatter.');
    control('fit','mode','Line model',{options:[['fit','Estimate intercept and speed from all data'],['reference','Test fixed reference: 1 m + (0.5 m/s)t']]});
    control('fit','scatter','Synthetic scatter scale (m)',{min:0,max:2});control('fit','offset','Calibration offset in all readings (m)',{min:-3,max:3});
    control('fit','outlier','Extra shift of point 9 (m)',{min:-5,max:5});control('fit','acceleration','Unmodelled acceleration (m/s²)',{min:-.2,max:.2});
    control('fit','sigma','Supplied y standard uncertainty σ (m)',{min:.01,max:3});control('fit','heterogeneous','Increase supplied σ towards later readings',{boolean:true});
    presets('fit',[
      ['Small reduced χ²',{scatter:.3,offset:0,acceleration:0,outlier:0,sigma:2,heterogeneous:false,mode:'fit'}],
      ['Hidden common offset',{scatter:.3,offset:2,acceleration:0,outlier:0,sigma:.3,heterogeneous:false,mode:'fit'}],
      ['Wrong constant-speed model',{scatter:.1,offset:0,acceleration:.12,outlier:0,sigma:.3,heterogeneous:false,mode:'fit'}],
      ['Keep a large outlier',{scatter:2,offset:3,acceleration:.2,outlier:5,sigma:.1,heterogeneous:true,mode:'fit'}]
    ]);
    function table(caption,heads,rows){const t=el('table',{style:{borderCollapse:'collapse',fontSize:'.95rem',width:'100%'}});t.append(el('caption',{style:{textAlign:'left',fontWeight:'600',margin:'8px 0'}},caption),el('thead',{},el('tr',{},...heads.map(h=>el('th',{scope:'col',style:{textAlign:'left',padding:'6px',borderBottom:'1px solid #87959d'}},h)))),el('tbody',{},...rows.map(row=>el('tr',{},...row.map((v,i)=>el(i?'td':'th',{...(i?{}:{scope:'row'}),style:{textAlign:'left',padding:'6px',borderBottom:'1px solid #acb6bd'}},typeof v==='number'?fmt(v):v))))));return el('div',{role:'region',tabindex:'0','aria-label':caption+'; scroll if needed',style:{maxWidth:'100%',overflowX:'auto'}},t);}
    function plot(target,title,xLabel,yLabel,xValues,yValues,draw,options={}){
      const pad=values=>{const lo=Math.min(...values),hi=Math.max(...values),gap=hi===lo?Math.max(Math.abs(lo)*.1,1):.08*(hi-lo);return [lo-gap,hi+gap];};
      const xd=pad(xValues),yd=pad(yValues),W=680,H=360,left=90,right=655,top=44,bottom=293;
      const X=x=>left+(x-xd[0])/(xd[1]-xd[0])*(right-left),Y=y=>bottom-(y-yd[0])/(yd[1]-yd[0])*(bottom-top);
      const svg=svgEl('svg',{viewBox:'0 0 '+W+' '+H,role:'img','aria-label':title,'data-measurement-plot':title,'data-axis-domain':JSON.stringify({x:xd,y:yd,left,right,top,bottom})});svg.append(svgEl('title',{},title),svgEl('rect',{x:0,y:0,width:W,height:H,fill:C.paper,rx:6}));
      svg.style.width='100%';svg.style.display='block';svg.style.maxWidth='none';svg.style.height='auto';
      const text=(x,y,v,attrs={})=>svg.append(svgEl('text',{x,y,fill:C.ink,'font-size':15,...attrs},v));
      text(14,25,title,{'font-size':18,'font-weight':'600'});
      const xt=options.xTicks||Array.from({length:5},(_,i)=>xd[0]+(xd[1]-xd[0])*i/4),yt=options.yTicks||Array.from({length:5},(_,i)=>yd[0]+(yd[1]-yd[0])*i/4);
      xt.forEach((x,i)=>{svg.append(svgEl('line',{x1:X(x),y1:top,x2:X(x),y2:bottom,stroke:C.grid}));text(X(x),bottom+23,options.xTickLabels?.[i]||axisFmt(x),{'text-anchor':'middle','font-size':13});});
      yt.forEach((y,i)=>{svg.append(svgEl('line',{x1:left,y1:Y(y),x2:right,y2:Y(y),stroke:C.grid}));text(left-9,Y(y)+4,options.yTickLabels?.[i]||axisFmt(y),{'text-anchor':'end','font-size':13});});
      text((left+right)/2,H-10,xLabel,{'text-anchor':'middle'});text(17,190,yLabel,{transform:'rotate(-90 17 190)','text-anchor':'middle'});
      const line=(a,b,color,attrs={})=>svg.append(svgEl('line',{x1:X(a[0]),y1:Y(a[1]),x2:X(b[0]),y2:Y(b[1]),stroke:color,'stroke-width':2,...attrs}));
      const dot=(x,y,color,attrs={})=>svg.append(svgEl('circle',{cx:X(x),cy:Y(y),r:4,fill:color,...attrs}));
      const poly=(points,color,attrs={})=>svg.append(svgEl('polyline',{points:points.map(p=>X(p[0])+','+Y(p[1])).join(' '),fill:'none',stroke:color,'stroke-width':2,...attrs}));
      draw({svg,X,Y,line,dot,poly,text,xd,yd});
      const wrap=el('div',{role:'region',tabindex:'0','aria-label':title+'; enlarge then scroll for detail',style:{overflowX:'auto',maxWidth:'100%',width:'100%',margin:'12px 0',border:'1px solid #9aa9b2',borderRadius:'6px',background:C.paper}},svg);
      target.append(wrap);return svg;
    }
    function standardView(p,m){
      p.output.append(el('p',{},m.formula+': estimate '+fmt(m.value)+' '+m.unit+', combined standard uncertainty u = '+fmt(m.standard)+' '+m.unit+'. '+(m.relativeStandard===null?'Relative uncertainty is undefined for a zero output estimate.':'Relative standard uncertainty = '+fmt(100*m.relativeStandard)+'%.')));
      const values=[...m.varianceTerms,m.variance],labels=['A variance','B variance','Covariance term','Combined variance'];
      plot(p.output,'Signed variance budget','Variance contribution','Variance ('+m.unit+')²',[0,3],[0,...values],({svg,X,Y})=>{values.forEach((v,i)=>svg.append(svgEl('rect',{x:X(i)-22,y:Math.min(Y(0),Y(v)),width:44,height:Math.abs(Y(v)-Y(0)),fill:i===2?C.coral:i===3?C.teal:C.blue,'data-variance-index':i,'data-variance':v})));},{xTicks:[0,1,2,3],xTickLabels:['A','B','Covariance','Total']});
      p.output.append(table('Sensitivity and covariance account',['Quantity','Value'],[['∂y/∂A [('+m.unit+')/('+m.inputUnits[0]+')]',m.gradient[0]],['∂y/∂B [('+m.unit+')/('+m.inputUnits[1]+')]',m.gradient[1]],['Cov(A,B) ('+m.inputUnits.join('·')+')',m.covariance],...labels.map((label,i)=>[label+' ('+m.unit+')²',values[i]])]));
      p.output.append(el('p',{},m.interpretation+' A covariance term may be negative; the total variance is nonnegative. A displayed standard uncertainty is not a guaranteed error bound or a confidence interval. '+(m.operation==='gravity'?'The pendulum relation assumes small oscillations and an ideal simple pendulum. ':'')+(m.nonlinear?'Here u(time)/time = '+fmt(100*m.denominatorRelativeStandard)+'%; this diagnostic is not a guarantee that linearization is adequate. Denominator support and nonlinear effects require additional information.':'')));
    }
    function boundsView(p,m){
      p.output.append(el('p',{},m.formula+': nominal '+fmt(m.value)+' '+m.unit+'. Exact allowed range ['+fmt(m.low)+', '+fmt(m.high)+'] '+m.unit+'. First-order estimate ['+m.linearizedInterval.map(fmt).join(', ')+'] '+m.unit+'.'));
      plot(p.output,'Exact set range and local approximation','Output ('+m.unit+')','Range type',[m.low,m.high,...m.linearizedInterval],[0,1],({line,dot})=>{line([m.linearizedInterval[0],0],[m.linearizedInterval[1],0],C.gold,{'data-bound-line':'linearized','stroke-width':7,'stroke-dasharray':'7 4'});line([m.low,1],[m.high,1],C.teal,{'data-bound-line':'exact','stroke-width':7});line([m.value,-.05],[m.value,1.05],C.coral,{'data-bound-line':'nominal'});dot(m.value,1,C.coral);},{yTicks:[0,1],yTickLabels:['First order','Exact']});
      p.output.append(table('All four input corners',['A ('+m.inputUnits[0]+')','B ('+m.inputUnits[1]+')','Output ('+m.unit+')'],m.corners.map(r=>[r.a,r.b,r.value])),el('p',{},m.interpretation+' These selected measurement functions are monotone in each input on the accepted domain, so their extrema occur at corners. For a nonlinear ratio, the exact interval can be asymmetric; the first-order estimate is not a guaranteed enclosure. The pendulum relation assumes small oscillations and an ideal simple pendulum.'));
    }
    function repeatsView(p,m){
      p.output.append(el('p',{},'At n = '+m.n+', u(mean) = '+fmt(m.standard)+' V; persistent model floor = '+fmt(m.floor)+' V. Known synthetic target '+fmt(m.target)+' V, expected raw reading '+fmt(m.expectedRaw)+' V, expected corrected mean '+fmt(m.expectedCorrected)+' V. Remaining signed offset = '+fmt(m.residualOffset)+' V.'));
      const maxN=Math.max(400,m.n),curve=Array.from({length:400},(_,i)=>{const n=Math.round(1+(maxN-1)*i/399);return repeatBudget({...state.repeats,n});});
      plot(p.output,'Uncertainty of the mean and shared floor','Number of independent repeats n','Standard uncertainty (V)',[1,maxN],[0,...curve.map(r=>r.standard)],({poly,line,dot})=>{poly(curve.map(r=>[r.n,r.standard]),C.blue,{'data-repeat-curve':'combined'});poly(curve.map(r=>[r.n,Math.sqrt(r.readingVariance)]),C.gold,{'data-repeat-curve':'scatter'});line([1,m.floor],[maxN,m.floor],C.coral,{'data-repeat-floor':'true'});dot(m.n,m.standard,C.teal,{'data-repeat-selected':'true'});});
      p.output.append(el('p',{},'Blue: combined standard uncertainty. Gold: repeat-scatter contribution. Coral: shared floor. The curve gives model uncertainty, not the errors of an observed sample path.'),table('Variance budget of the mean',['Component','Variance (V²)'],[['Independent repeat scatter s²/n',m.readingVariance],['Additional resolution contribution',m.resolutionVariance],['Shared calibration u_cal²',m.calibrationVariance],['Total',m.variance]]));
      const resolutionNote=m.resolutionMode==='included-in-scatter'?'Resolution is already represented in the supplied scatter: no second resolution term is added.':m.resolutionMode==='shared-uniform'?'An additional common unknown rounding phase has a rectangular ±Δ/2 model. Its variance Δ²/12 does not shrink with repeats.':'Additional rounding phases are explicitly modelled as independent and uniform within ±Δ/2, and absent from the supplied scatter. Their variance Δ²/(12n) shrinks with n. Repeated identical digital readings do not establish these assumptions.';
      p.output.append(el('p',{},m.interpretation+' '+resolutionNote+' More repeats do not remove an uncorrected common offset. A small standard uncertainty does not establish accuracy when relevant effects are omitted.'));
      const sample=summarizeReadings(repeatReadings);p.output.append(el('details',{},el('summary',{style:{cursor:'pointer',minHeight:'44px'}},'Five-reading example: mean and sample spread'),table('Separate worked example of repeat observations',['Reading','Voltage (V)'],repeatReadings.map((v,i)=>[i+1,v])),el('p',{},'These five illustrative readings have mean '+fmt(sample.mean)+' V, sample standard deviation s = '+fmt(sample.sampleStandardDeviation)+' V, and estimated standard error s/√5 = '+fmt(sample.standardError)+' V if their errors are independent with common variance. They do not establish those assumptions or measure the calibration uncertainty. Their observed spread already reflects the displayed resolution. Use the example preset to transfer s and n=5 into the budget.')));
    }
    function fitView(p,m){
      const stateFit=m.sourceState,pred=x=>m.intercept+m.slope*x;
      p.output.append(el('p',{},(m.mode==='fit'?'Estimated line':'Fixed reference')+': position = '+fmt(m.intercept)+' m + ('+fmt(m.slope)+' m/s) × time. χ² = '+fmt(m.chiSquare)+', degrees of freedom = '+m.count+' − '+m.parametersEstimated+' = '+m.degreesOfFreedom+', reduced χ² = '+fmt(m.reducedChiSquare)+'. All '+m.count+' observations are included.'));
      const allY=m.rows.flatMap(r=>[r.y-r.sigma,r.y+r.sigma,r.fitted,1+.5*r.x]);
      plot(p.output,'Every position reading and its supplied σ','Time t (s)','Position y (m)',m.rows.map(r=>r.x),allY,({line,dot})=>{line([0,1],[11,6.5],C.gold,{'data-fit-line':'reference','stroke-dasharray':'6 4'});line([0,pred(0)],[11,pred(11)],C.teal,{'data-fit-line':'fitted'});m.rows.forEach((r,i)=>{line([r.x,r.y-r.sigma],[r.x,r.y+r.sigma],C.blue,{'data-fit-errorbar':i});dot(r.x,r.y,i===8&&stateFit.outlier?C.coral:C.blue,{'data-fit-point':i});});});
      p.output.append(el('p',{},'Blue points: all synthetic readings; blue bars: supplied ±1 standard uncertainty, not guaranteed intervals. Teal: selected line. Dashed gold: declared reference 1 m + (0.5 m/s)t. Red marks the deliberately shifted point 9. Axes rescale to contain every point and bar.'));
      plot(p.output,'Normalized residuals rᵢ / σᵢ','Time t (s)','Dimensionless residual',m.rows.map(r=>r.x),[0,...m.rows.map(r=>r.normalized)],({line,dot})=>{line([0,0],[11,0],C.grid);m.rows.forEach((r,i)=>{line([r.x,0],[r.x,r.normalized],C.coral);dot(r.x,r.normalized,C.coral,{'data-fit-residual':i});});});
      p.output.append(table('Line parameter uncertainty from supplied σ',['Quantity','Value'],[['Intercept standard uncertainty (m)',m.interceptStandard],['Speed standard uncertainty (m/s)',m.slopeStandard],['Cov(intercept,speed) (m²/s)',m.parameterCovariance[0][1]],['Mean of the 12 raw positions (m)',m.rawMean]]));
      const details=el('details',{},el('summary',{style:{cursor:'pointer',minHeight:'44px'}},'Inspect all observations and residuals'),table('Complete synthetic data',['Point','t (s)','y (m)','σ (m)','Fitted y (m)','Residual (m)','r/σ'],m.rows.map((r,i)=>[i+1,r.x,r.y,r.sigma,r.fitted,r.residual,r.normalized])));p.output.append(details);
      p.output.append(el('p',{},m.interpretation+' A low reduced χ² is not proof of a correct experiment: large supplied uncertainties, dependence or unusually small scatter can also lower it. A high value may reflect underestimated uncertainties, a wrong mean model or an outlier. A free intercept can absorb a common calibration offset while leaving small residuals. In fixed-reference mode no parameters are estimated and their uncertainty is zero by assumption, not by inference. '+m.syntheticNote));
    }
    function units(key){const s=state[key],spec=operations[s.operation];if(!spec)return;const w=panels[key].widgets;w.get('a').caption.textContent=spec.a;w.get('b').caption.textContent=spec.b;w.get('a').input.min=spec.nonlinear?'0':'-100';w.get('b').input.min=spec.nonlinear?'0.000001':'-100';for(const [field,i]of [[key==='bounds'?'da':'ua',0],[key==='bounds'?'db':'ub',1]])w.get(field).caption.textContent=(key==='bounds'?'Allowed half-width ':'Standard uncertainty u(')+(i?'B':'A')+(key==='bounds'?'':')')+' ('+spec.inputUnits[i]+')';}
    function size(){zoom.setAttribute('aria-pressed',String(enlarged));zoom.textContent=enlarged?'Fit plots':'Enlarge plots';for(const svg of root.querySelectorAll('[data-measurement-plot]')){svg.style.width=enlarged?'900px':'100%';svg.style.minWidth=enlarged?'900px':'';}}
    function show(){for(const[k,p]of Object.entries(panels)){p.section.hidden=k!==state.station;for(const node of p.section.querySelectorAll('[data-model-speak]'))node.removeAttribute('data-model-speak');if(k===state.station){p.noteEl.setAttribute('data-model-speak','true');for(const node of Array.from(p.output.querySelectorAll(':scope > p')).slice(1))node.setAttribute('data-model-speak','true');}}readout.textContent=models[state.station]?.summary||names[state.station];readout.setAttribute('data-measurement-speech',models[state.station]?.speech||readout.textContent);}
    function refresh(announce,key){
      const keys=key?[key]:Object.keys(panels);for(const k of keys){const p=panels[k];p.output.replaceChildren();units(k);
        try{for(const {input}of p.widgets.values()){if(input.type==='number' && (!input.validity.valid || !Number.isFinite(input.valueAsNumber)))throw new RangeError('Enter a valid value in each labelled field and keep within its range.');input.removeAttribute('aria-invalid');}
          const m=k==='propagation'?propagate(state[k]):k==='bounds'?interval(state[k]):k==='repeats'?repeatBudget(state[k]):fitExample(state[k]);
          if(k==='propagation')standardView(p,m);if(k==='bounds')boundsView(p,m);if(k==='repeats')repeatsView(p,m);if(k==='fit')fitView(p,m);
          models[k]={value:m,summary:p.output.querySelector(':scope > p').textContent,speech:p.noteEl.textContent+' '+Array.from(p.output.querySelectorAll(':scope > p')).map(node=>node.textContent).join(' ')};p.section.removeAttribute('data-error');
        }catch(error){models[k]={error:error.message,summary:'Invalid input: '+error.message};p.section.setAttribute('data-error',error.message);p.output.append(el('p',{role:'alert'},'Invalid input: '+error.message));for(const {input}of p.widgets.values())if(input.type==='number'&&!input.validity.valid)input.setAttribute('aria-invalid','true');}
      }
      root.setAttribute('data-measurement-state',JSON.stringify(state));size();show();if(announce)live.textContent=models[state.station]?.summary||'';
    }
    station.addEventListener('change',()=>{state.station=station.value;show();live.textContent=names[state.station];});
    const sources=el('p',{},'Measurement definitions: ',el('a',{href:'https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-law-propagation-uncertainty',target:'_blank',rel:'noopener noreferrer'},'NIST: uncertainty propagation'),'.');main.append(sources);
    for(const p of Object.values(panels))p.sync();refresh(false);
    root.measurement={getState:()=>copy(state),getModels:()=>Object.fromEntries(Object.entries(models).map(([k,v])=>[k,v.error?{error:v.error}:copy(v.value)])),reset:()=>reset.click()};
    return root;
  }
  const api=Object.freeze({operations,defaults,model,propagate,interval,repeatBudget,weightedLineFit,fitExample,summarizeReadings,repeatReadings,render});
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(host)host.PrimerMeasurementLab=api;
})(typeof window!=='undefined'?window:globalThis);
