/* Equations and their graphs share one accepted state with the 3D chart. */
(function(host){
  'use strict';
  const IDS=['math.3.linear','math.3.slope','math.3.quadratics','math.3.polynomials'];
  const colors=['#316a83','#bb6248','#876888','#4f8050','#b08625'];
  let serial=0;
  const numberText=n=>Number.isInteger(n)?String(n):Math.abs(n)>1e4||Math.abs(n)>0&&Math.abs(n)<.001?Number(n.toPrecision(4)).toExponential():Number(n.toPrecision(6)).toString();
  function render(item,hooks={}){
    const lesson=item?.props?.scenario,c=host?.PrimerAlgebraFunctionsCore,geometry=host?.PrimerAlgebraFunctionsSpatial;
    if(item?.renderer!=='algebra-functions-lab'||!IDS.includes(lesson)||Object.keys(item.props).length!==1||!c||!geometry)return null;
    const E=(tag,attrs={},...children)=>{const n=document.createElement(tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,String(v));for(const child of children.flat())if(child!==undefined&&child!==null)n.append(child.nodeType?child:document.createTextNode(String(child)));return n;};
    const S=(tag,attrs={},text)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;};
    const uid='algebra-functions-'+ ++serial,bus=host.PrimerLessonStateBus,examples=c.presets(lesson);
    let model=c.model(lesson,c.defaults(lesson)),view=geometry.viewState(model,{}),scene=geometry.sceneForState(model,view),selectedExample=null,enlarged=false,controlSignature='',viewSignature='';
    const root=E('section',{class:'card lesson-model algebra-functions-lab','data-algebra-lesson':lesson,'aria-labelledby':uid+'-title'});
    const title=E('h3',{id:uid+'-title'},item.title||model.title),presets=E('select',{'data-algebra-presets':'','aria-label':'Worked example'},E('option',{value:''},'Choose a worked example'),examples.map(p=>E('option',{value:p.id},p.label)));
    const reset=E('button',{type:'button','data-algebra-reset':''},'Reset'),enlarge=E('button',{type:'button','data-algebra-enlarge':'','aria-pressed':'false'},'Enlarge graph');
    const controls=E('div',{class:'algebra-controls'}),viewControls=E('div',{class:'algebra-controls algebra-view-controls'}),error=E('p',{role:'alert','data-algebra-error':''}),context=E('p',{class:'algebra-context','data-algebra-context':''});
    const result=E('div',{'data-algebra-result':''}),plotHost=E('section',{class:'algebra-plot-panel'}),live=E('p',{class:'algebra-live',role:'status','aria-live':'polite','aria-atomic':'true'});
    root.append(title,E('p',{},item.instructions||'Enter the quantities, follow the exact calculations, and compare the same state in the coordinate graph and 3D chart.'),E('div',{class:'algebra-actions'},E('label',{},'Worked example',presets),reset,enlarge),context,controls,error,result,viewControls,plotHost,live);
    function scalar(key,label){return{key,label};}
    function select(key,label,options){return{key,label,options};}
    function fields(){
      if(lesson==='math.3.linear')return[
        scalar('a','Left x coefficient a'),scalar('b','Left constant b'),scalar('leftScale','Left outside factor'),scalar('c','Right x coefficient c'),scalar('d','Right constant d'),scalar('rightScale','Right outside factor'),scalar('testX','Check a proposed x'),
        select('step','Equivalent equation to display',[[0,'Original equation'],[1,'Expand brackets'],[2,'Collect x terms and constants'],[3,'Solve or classify']])];
      if(lesson==='math.3.slope'){
        const list=[select('mode','Given information',[['points','Two distinct points'],['point-slope','Slope and a point'],['general','General equation Ax + By = C']])];
        if(model.state.mode==='general')list.push(scalar('A','A: x coefficient'),scalar('B','B: y coefficient'),scalar('C','C: right-hand constant'));
        else{list.push(scalar('x1','First point: x'),scalar('y1','First point: y'));if(model.state.mode==='points')list.push(scalar('x2','Second point: x'),scalar('y2','Second point: y'));else list.push(scalar('m','Given slope m'));}
        list.push(scalar('atX','Evaluate the relation at x'),select('relation','Construct a related line',[['none','No related line'],['parallel','Parallel through a point'],['perpendicular','Perpendicular through a point']]));
        if(model.state.relation!=='none')list.push(scalar('throughX','Related line through: x'),scalar('throughY','Related line through: y'));return list;
      }
      if(lesson==='math.3.quadratics')return[scalar('a','a: coefficient of x²'),scalar('b','b: coefficient of x'),scalar('c','c: constant')];
      const list=[select('mode','Polynomial operation',[['factors','Expand from given roots'],['factor-quadratic','Factor a quadratic from coefficients'],['add','Add polynomials'],['multiply','Multiply polynomials'],['divide','Divide with a remainder']])];
      if(model.state.mode==='factors')return [...list,scalar('leading','Leading coefficient'),{key:'roots',label:'Given roots, separated by commas',array:true}];
      for(const group of model.state.mode==='factor-quadratic'?['left']:['left','right'])for(let power=0;power<=4;power++)list.push({key:group+'.'+power,label:(group==='left'?'P':'Q')+' coefficient of '+(power===0?'1':power===1?'x':'x^'+power),coefficient:true});return list;
    }
    function valueAt(key){const [name,index]=key.split('.');return index===undefined?model.state[name]:(model.state[name][Number(index)]??'0');}
    function rebuildControls(){
      const descriptor=fields(),signature=JSON.stringify(descriptor),active=controls.contains(document.activeElement)?document.activeElement:null;
      const activeKey=active?.dataset.algebraField,selection=active?.tagName==='INPUT'?[active.selectionStart,active.selectionEnd]:null;
      if(signature===controlSignature){for(const input of controls.querySelectorAll('[data-algebra-field]')){const value=valueAt(input.dataset.algebraField);input.value=Array.isArray(value)?value.join(', '):String(value);input.removeAttribute('aria-invalid');}if(selection&&active)active.setSelectionRange(Math.min(selection[0],active.value.length),Math.min(selection[1],active.value.length));return;}
      controlSignature=signature;controls.replaceChildren();
      const hint=lesson==='math.3.linear'?'Equation: left factor × (ax + b) = right factor × (cx + d).':lesson==='math.3.quadratics'?'Function: y = ax² + bx + c. Setting a to zero changes its degree and is classified explicitly.':lesson==='math.3.polynomials'?'Coefficients describe P(x) and Q(x) in ascending powers. A zero highest coefficient lowers the degree. Roots mode starts from supplied roots; quadratic factoring starts from the coefficients.':'Points and coefficients define a relation in an x–y coordinate plane.';
      controls.append(E('p',{class:'algebra-controls-hint'},hint+' Enter integers, fractions such as -2/3, or decimals. Input magnitude is limited to 1000 and the reduced denominator to 1000.'));
      for(const field of descriptor){
        const id=uid+'-'+field.key.replace('.','-'),input=field.options?E('select',{id,'data-algebra-field':field.key},field.options.map(([v,label])=>E('option',{value:v},label))):E('input',{id,type:'text',inputmode:'text','data-algebra-field':field.key,autocomplete:'off',spellcheck:'false'});
        const value=valueAt(field.key);input.value=field.array?value.join(', '):String(value);
        input.addEventListener('change',()=>commitDraft(input));
        input.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();commitDraft(input);}else if(event.key==='Escape'){event.preventDefault();rebuildControls();controls.querySelector('[data-algebra-field="'+field.key+'"]')?.focus();error.textContent='';}});
        controls.append(E('label',{for:id,class:field.coefficient?'algebra-coefficient':''},field.label,input));
      }
      if(activeKey)controls.querySelector('[data-algebra-field="'+activeKey+'"]')?.focus();
    }
    function commitDraft(changed){
      const next=JSON.parse(JSON.stringify(model.state));
      try{
        for(const input of controls.querySelectorAll('[data-algebra-field]')){
          const [key,index]=input.dataset.algebraField.split('.');
          if(index!==undefined){while(next[key].length<=Number(index))next[key].push('0');next[key][Number(index)]=input.value;}
          else if(key==='roots'){next.roots=input.value.split(',').map(s=>s.trim());if(next.roots.some(s=>!s))throw Error('Each given root needs a value.');}
          else next[key]=key==='step'?Number(input.value):input.value;
        }
        accept(next,true,false,null);
      }catch(e){changed.setAttribute('aria-invalid','true');error.textContent=e.message+' Calculations, speech and both graphs still use the last accepted inputs. Press Escape to restore them.';}
    }
    function accept(raw,announce=true,fromShared=false,example=null){
      const next=c.model(lesson,geometry.algebraState(raw)),nextView=geometry.viewState(next,raw),nextScene=geometry.sceneForState(next,nextView);
      model=next;view=nextView;scene=nextScene;selectedExample=example;presets.value=example?.id||'';error.textContent='';rebuildControls();refresh(announce);
      const shared={...model.state,...view};if(!fromShared)bus?.publish(lesson,root,shared);return shared;
    }
    function drawGraph(){
      plotHost.replaceChildren();const b=scene.bounds,extent=Math.max(b.xmax-b.xmin,b.ymax-b.ymin),gain=620/extent;
      const xPad=(620-(b.xmax-b.xmin)*gain)/2,yPad=(620-(b.ymax-b.ymin)*gain)/2,X=x=>95+xPad+(x-b.xmin)*gain,Y=y=>55+yPad+(b.ymax-y)*gain;
      const centres={x:(b.xmin+b.xmax)/2,y:(b.ymin+b.ymax)/2};
      const offsets={x:view.chartFocus!=='overview'||Math.abs(centres.x)/(b.xmax-b.xmin)>1e4,y:view.chartFocus!=='overview'||Math.abs(centres.y)/(b.ymax-b.ymin)>1e4};
      const tickExtent=view.chartFocus==='overview'?extent/2:view.chartRadius;
      const tickPower=tickExtent<1||tickExtent>=1000?Math.floor(Math.log10(tickExtent)):0,tickFactor=10**tickPower;
      const tick=(value,axis)=>Number(((value-(offsets[axis]?centres[axis]:0))/tickFactor).toPrecision(3)).toString();
      const axisName=axis=>(offsets[axis]?'Δ':'')+axis+(tickPower?' (×10^'+tickPower+')':'');
      const svg=S('svg',{viewBox:'0 0 770 755',role:'img','aria-label':model.title+' coordinate graph. Both axes use the same scale.','data-algebra-graph':'','data-scale':gain,'data-bounds':JSON.stringify(b),'data-tick-factor':tickFactor,'data-offset-x':offsets.x?centres.x:0,'data-offset-y':offsets.y?centres.y:0});
      svg.append(S('title',{},model.title+' · equal coordinate scales'),S('rect',{x:95,y:55,width:620,height:620,fill:'#fcfaf4',stroke:'#a6b3ae'}));
      for(let j=0;j<=4;j++){
        const x=b.xmin+(b.xmax-b.xmin)*j/4,y=b.ymin+(b.ymax-b.ymin)*j/4;
        svg.append(S('line',{x1:X(x),x2:X(x),y1:Y(b.ymin),y2:Y(b.ymax),stroke:'#d7ddd6'}),S('line',{x1:X(b.xmin),x2:X(b.xmax),y1:Y(y),y2:Y(y),stroke:'#d7ddd6'}));
        svg.append(S('text',{x:X(x),y:Y(b.ymin)+25,'text-anchor':'middle','data-algebra-tick':'x','data-coordinate':x},tick(x,'x')),S('text',{x:X(b.xmin)-10,y:Y(y)+5,'text-anchor':'end','data-algebra-tick':'y','data-coordinate':y},tick(y,'y')));
      }
      for(const axis of scene.axes)svg.append(S('line',{x1:X(axis.from[0]),y1:Y(axis.from[1]),x2:X(axis.to[0]),y2:Y(axis.to[1]),stroke:'#253c45','stroke-width':1.8,'data-algebra-axis':axis.axis}));
      scene.lines.forEach((line,i)=>{if(line.status==='all-plane')svg.append(S('rect',{x:X(b.xmin),y:Y(b.ymax),width:(b.xmax-b.xmin)*gain,height:(b.ymax-b.ymin)*gain,fill:colors[(scene.curves.length+i)%colors.length],opacity:.13,'data-algebra-all-plane':line.id}));});
      scene.curves.forEach((curve,i)=>curve.paths.forEach((path,p)=>svg.append(S('path',{d:path.map(([x,y],j)=>(j?'L':'M')+X(x)+' '+Y(y)).join(' '),fill:'none',stroke:colors[i%colors.length],'stroke-width':2.5,'stroke-linecap':'round','data-algebra-curve':curve.id,'data-path-index':p,'data-source-points':JSON.stringify(path)}))));
      scene.lines.forEach((line,i)=>{if(!line.segment)return;const[a,z]=line.segment;svg.append(S('line',{x1:X(a[0]),y1:Y(a[1]),x2:X(z[0]),y2:Y(z[1]),stroke:colors[(scene.curves.length+i)%colors.length],'stroke-width':2.5,'stroke-linecap':'round','data-algebra-line':line.id,'data-source-points':JSON.stringify(line.segment)}));});
      for(const segment of scene.segments)if(segment.visible)svg.append(S('line',{x1:X(segment.from[0]),y1:Y(segment.from[1]),x2:X(segment.to[0]),y2:Y(segment.to[1]),stroke:'#247e79','stroke-width':2,'stroke-linecap':'round','stroke-dasharray':'6 4','data-algebra-construction':segment.id,'data-source-points':JSON.stringify([segment.from,segment.to])}));
      for(const group of scene.markerGroups){const point={...group,id:group.pointIds.join('|'),label:group.pointIds.map(id=>scene.points.find(p=>p.id===id).label).join('; ')};const circle=S('circle',{cx:X(point.x),cy:Y(point.y),r:5,fill:point.exact?'#b08625':'#bb6248',stroke:'#fff','stroke-width':1,'data-algebra-point':point.id,'data-source-x':point.x,'data-source-y':point.y,'data-exact':point.exact});circle.append(S('title',{},point.label+' ('+numberText(point.x)+', '+numberText(point.y)+')'+(point.exact?'':' approximately')));svg.append(circle);}
      svg.append(S('text',{x:405,y:735,'text-anchor':'middle'},'Horizontal: '+axisName('x')+' · Vertical: '+axisName('y')));
      const legend=E('ul',{class:'algebra-legend'});[...scene.curves,...scene.lines].forEach((item,i)=>{const swatch=E('span',{'aria-hidden':'true',class:'algebra-swatch'});swatch.style.backgroundColor=colors[i%colors.length];legend.append(E('li',{},swatch,item.label+(item.status==='empty'?' — no satisfying points':item.status==='all-plane'?' — every point satisfies':'')));});
      const pointRows=scene.points.map(point=>E('tr',{},E('th',{scope:'row'},point.label),E('td',{},point.xText),E('td',{},point.yText),E('td',{},(point.exact?'Exact mathematical point':'Approximate location')+(point.visible?'':' · outside the window'))));
      const points=E('div',{class:'algebra-table-scroll',tabindex:'0',role:'region','aria-label':'Scrollable exact special-point table'},E('table',{class:'algebra-point-table'},E('caption',{},'Special points in mathematical coordinates; irrational locations are approximate'),E('thead',{},E('tr',{},['Point','x','y','Interpretation'].map(t=>E('th',{scope:'col'},t)))),E('tbody',{},pointRows)));
      plotHost.append(E('h4',{},'Coordinate graph'),E('div',{class:'algebra-viewport',tabindex:'0',role:'region','aria-label':'Scrollable coordinate graph'},svg),legend,E('p',{class:'algebra-graph-note'},'This finite window clips lines and curves that continue beyond it. Both coordinate directions use equal units; an oblique 3D view can change apparent angles. The curve is drawn with straight segments, with maximum vertical approximation bound '+numberText(scene.maxChordError)+' y units. Gold points are exact; terracotta points approximate irrational roots. Use the exact ledger and point table for calculations. Both views share the chosen window. Changing the algebra resets the overview. Enlarge the graph for detail; swipe or use arrow keys inside enlarged graphs and wide tables.'));
      if(offsets.x||offsets.y||tickPower)plotHost.append(E('p',{class:'algebra-axis-origin','data-algebra-axis-origin':''},['x','y'].filter(axis=>offsets[axis]).map(axis=>axis+' = '+String(centres[axis])+' + Δ'+axis+'.').join(' ')+(tickPower?' Multiply both axes’ tick numbers by 10^'+tickPower+' to obtain coordinate units.':'')+' Tick numbers are rounded to three significant digits; exact mathematical point coordinates remain in the table.'));
      if(scene.curves.some(curve=>curve.boundaryUncertain))plotHost.append(E('p',{class:'algebra-boundary-notice',role:'status'},'A curve may touch the window boundary below the available coordinate precision. Its absence here does not prove that it lies entirely outside. Change the focused window to inspect that boundary.'));
      if(pointRows.length)plotHost.append(points);
    }
    function refresh(announce){
      root.dataset.algebraState=JSON.stringify(model.state);root.dataset.algebraView=JSON.stringify(view);context.textContent=selectedExample?.context||'This is a mathematical coordinate model. Application units and physical restrictions are stated in the worked examples.';
      const rows=model.ledger.map(row=>E('tr',{},E('th',{scope:'row'},row.label),E('td',{},row.text)));
      result.replaceChildren(E('h4',{},model.title),E('p',{'data-algebra-summary':''},model.summary),E('ol',{class:'algebra-steps'},model.steps.map(step=>E('li',{},step))),E('div',{class:'algebra-table-scroll',tabindex:'0',role:'region','aria-label':'Scrollable exact calculation ledger'},E('table',{},E('caption',{},'Exact calculation ledger'),E('thead',{},E('tr',{},E('th',{scope:'col'},'Quantity or statement'),E('th',{scope:'col'},'Value'))),E('tbody',{},rows))));
      drawGraph();refreshViewControls();if(announce)live.textContent=model.summary+' '+(view.chartFocus==='overview'?'Overview window.':'Focused window with coordinate half-width '+view.chartRadius+'.');
    }
    function refreshViewControls(){
      const active=viewControls.contains(document.activeElement)?document.activeElement?.dataset.algebraViewControl:null;
      const signature=JSON.stringify(scene.points.map(p=>[p.id,p.marker,p.label]));
      if(signature===viewSignature){const f=viewControls.querySelector('[data-algebra-view-control=focus]'),r=viewControls.querySelector('[data-algebra-view-control=radius]');f.value=view.chartFocus;r.value=String(view.chartRadius);r.disabled=view.chartFocus==='overview';f.removeAttribute('aria-invalid');r.removeAttribute('aria-invalid');return;}
      viewSignature=signature;
      const focus=E('select',{'data-algebra-view-control':'focus'},E('option',{value:'overview'},'Overview: all special points'),scene.points.map(p=>E('option',{value:p.id},p.marker+' · '+p.label)));
      const radius=E('input',{type:'text',inputmode:'text','data-algebra-view-control':'radius','aria-label':'Focused window coordinate half-width'});
      focus.value=view.chartFocus;radius.value=String(view.chartRadius);radius.disabled=view.chartFocus==='overview';
      function apply(input){try{accept({...model.state,chartFocus:focus.value,chartRadius:radius.value},true,false,selectedExample);}catch(e){input.setAttribute('aria-invalid','true');error.textContent=e.message+' The accepted algebra and window are unchanged.';}}
      focus.onchange=()=>apply(focus);radius.onchange=()=>apply(radius);radius.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();apply(radius);}else if(event.key==='Escape'){event.preventDefault();refreshViewControls();viewControls.querySelector('[data-algebra-view-control=radius]').focus();error.textContent='';}};
      viewControls.replaceChildren(E('label',{},'Inspect the graph window',focus),E('label',{},'Half-width in x and y units',radius),E('p',{class:'algebra-controls-hint'},'Focus a named point, then enter a positive decimal or scientific-notation radius from 1e−12 to 1e12. Both directions keep equal units. This changes the view, not the equation; points outside the chosen window remain listed.'));
      if(active)viewControls.querySelector('[data-algebra-view-control="'+active+'"]')?.focus();
    }
    presets.onchange=()=>{const example=examples.find(p=>p.id===presets.value);if(example)accept(example.state,true,false,example);};
    reset.onclick=()=>accept(c.defaults(lesson));enlarge.onclick=()=>{enlarged=!enlarged;root.classList.toggle('algebra-enlarged',enlarged);enlarge.textContent=enlarged?'Standard graph size':'Enlarge graph';enlarge.setAttribute('aria-pressed',String(enlarged));};
    root.getModelSpeech=()=>model.title+'. '+context.textContent+' '+model.summary+' '+model.steps.join(' ')+' '+model.ledger.map(row=>row.label+': '+row.text+'.').join(' ');
    root.setModelState=(raw,announce=false,fromShared=false)=>accept(raw,announce,fromShared,null);
    root.algebraFunctions={getModel:()=>model,getScene:()=>scene,getView:()=>({...view}),getState:()=>JSON.parse(JSON.stringify({...model.state,...view}))};
    if(hooks.speakButton)title.prepend(hooks.speakButton(root.getModelSpeech,'Read this activity aloud'));
    bus?.join(lesson,root,values=>root.setModelState(values,false,true));rebuildControls();refresh(false);return root;
  }
  const api=Object.freeze({render});if(host)host.PrimerAlgebraFunctionsLab=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window==='undefined'?null:window);
