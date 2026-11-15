(function (host) {
  'use strict';
  let serial = 0;
  function render(item, hooks = {}) {
    if (item?.renderer !== 'concept-lab' || item?.props?.scenario !== 'math.2.decimals' || Object.keys(item.props).length !== 1) return null;
    const c = host.PrimerDecimalCore; if (!c) return null;
    let state = c.defaults(), model = c.build(state), enlarged = false;
    const root = document.createElement('section'); root.className = 'card lesson-model decimal-workbench';
    const modes = { place: 'Explore place values', compare: 'Compare decimals', add: 'Add', subtract: 'Subtract', multiply: 'Multiply', divide: 'Divide into groups', round: 'Round to a decimal place', money: 'Totals and change' };
    const placeName = p => ({ 6:'Millions',5:'Hundred thousands',4:'Ten thousands',3:'Thousands',2:'Hundreds',1:'Tens',0:'Ones',[-1]:'Tenths',[-2]:'Hundredths',[-3]:'Thousandths',[-4]:'Ten-thousandths',[-5]:'Hundred-thousandths',[-6]:'Millionths' })[p] || '10^' + p;
    const E = (tag, attrs = {}, ...children) => { const n = document.createElement(tag); for (const [k,v] of Object.entries(attrs)) n.setAttribute(k,String(v)); for (const x of children.flat()) if (x != null) n.append(x.nodeType ? x : document.createTextNode(String(x))); return n; };
    const S = (tag, attrs = {}, text) => { const n = document.createElementNS('http://www.w3.org/2000/svg',tag); for (const [k,v] of Object.entries(attrs)) n.setAttribute(k,String(v)); if (text !== undefined) n.textContent = text; return n; };
    const $ = selector => root.querySelector(selector), R = p => c.q(p.n,p.d), abs = p => c.pack(c.q(BigInt(p.n) < 0n ? -BigInt(p.n) : BigInt(p.n),p.d)), paren = v => String(v).startsWith('-') ? '(' + v + ')' : v;
    const presets = [
      ['add','0.75 + 1.6',{mode:'add',a:'0.75',b:'1.6'}], ['multiply','0.4 × 0.3',{mode:'multiply',a:'0.4',b:'0.3'}],
      ['compare','Compare 0.089 and 0.7',{mode:'compare',a:'0.089',b:'0.7'}], ['pens','Four pens at 1.45',{mode:'money',a:'1.45',quantityA:'4',b:'0',quantityB:'0',tender:'10'}],
      ['subtract','3 − 0.85',{mode:'subtract',a:'3',b:'0.85'}], ['ribbon','1.8 ÷ 0.6',{mode:'divide',a:'1.8',b:'0.6'}],
      ['multiply2','2.5 × 0.4',{mode:'multiply',a:'2.5',b:'0.4'}], ['round','Round 3.478 to hundredths',{mode:'round',a:'3.478',places:'2'}],
      ['change','Pay 10 for 3.40 + 2.75',{mode:'money',a:'3.40',b:'2.75',tender:'10'}], ['trailing','Compare 1.2 and 1.20',{mode:'compare',a:'1.2',b:'1.20'}],
      ['place','Place values in 1.20',{mode:'place',a:'1.20'}], ['carry','Regroup 0.999 + 0.001',{mode:'add',a:'0.999',b:'0.001'}],
      ['negative','Subtract a negative decimal',{mode:'subtract',a:'-0.1',b:'-0.2'}], ['third','An exact nonterminating quotient',{mode:'divide',a:'1',b:'3'}],
      ['zero','Division by zero',{mode:'divide',a:'1',b:'0'}], ['tie','A negative rounding tie',{mode:'round',a:'-1.25',places:'1'}],
      ['owed','When the tender is too small',{mode:'money',a:'3.40',b:'2.75',tender:'5'}],
    ];
    const heading = E('h3',{id:'decimal-title-'+ ++serial},'Decimals: place, operation and value'); root.setAttribute('aria-labelledby',heading.id);
    const operation = E('select',{'data-decimal-mode':''},Object.entries(modes).map(([k,v])=>E('option',{value:k},v)));
    const preset = E('select',{'data-decimal-preset':''},E('option',{value:''},'Choose a worked example'),presets.map(([k,v])=>E('option',{value:k},v)));
    root.append(heading,E('p',{},'Align equal places and keep the unit fixed. Calculations retain exact values; diagram coordinates are display approximations.'),E('div',{class:'decimal-actions'},E('label',{},'Investigation',operation),E('label',{},'Worked example',preset),E('button',{type:'button','data-decimal-reset':''},'Reset'),E('button',{type:'button','data-decimal-zoom':'','aria-pressed':'false'},'Enlarge diagrams')),E('div',{class:'decimal-controls','data-decimal-controls':''}),E('p',{role:'alert','data-decimal-error':''}),E('div',{'data-decimal-result':''}));
    function fields() {
      if (state.mode === 'place') return [['a','Decimal value']];
      if (state.mode === 'round') return [['a','Decimal value'],['places','Decimal places',Array.from({length:7},(_,i)=>[String(i),String(i)])]];
      if (state.mode === 'money') return [['a','First unit price'],['quantityA','First quantity'],['b','Second unit price'],['quantityB','Second quantity'],['tender','Amount tendered']];
      return [['a',state.mode === 'divide'?'Dividend':'First decimal'],['b',state.mode === 'divide'?'Divisor':'Second decimal'],...(state.mode === 'divide'?[['groupStart','Groups skipped before diagram']]:[])];
    }
    function controls() {
      const box = $('[data-decimal-controls]'); box.replaceChildren();
      for (const [key,label,options] of fields()) {
        const input = options ? E('select',{'data-decimal-control':key},options.map(([v,l])=>E('option',{value:v},l))) : E('input',{type:'text',inputmode:['quantityA','quantityB','groupStart'].includes(key)?'numeric':'decimal','data-decimal-control':key});
        input.value = state[key];
        input.addEventListener('change',()=>{
          try { const candidate = {...state}; for (const field of root.querySelectorAll('[data-decimal-control]')) candidate[field.dataset.decimalControl] = field.value; const next = c.build(candidate); state = candidate; model = next; for (const field of root.querySelectorAll('[data-decimal-control]')) field.removeAttribute('aria-invalid'); refresh(); }
          catch (error) { input.setAttribute('aria-invalid','true'); $('[data-decimal-error]').textContent = error.message + ' The result still uses the last accepted inputs.'; }
        });
        input.addEventListener('keydown',event=>{ if(event.key==='Enter'){event.preventDefault();input.dispatchEvent(new Event('change'));} if(event.key==='Escape'){controls();$('[data-decimal-control="'+key+'"]').focus();$('[data-decimal-error]').textContent='';} });
        box.append(E('label',{},label,input));
      }
    }
    function table(title, heads, rows, widths=null) { return E('section',{class:'decimal-ledger'},E('h4',{},title),E('p',{class:'decimal-scroll-help'},'Scroll sideways for all columns, or focus the table and use the arrow keys.'),E('div',{class:'decimal-table',tabindex:0,role:'region','aria-label':title},E('table',{},E('caption',{class:'decimal-caption'},title),widths?E('colgroup',{},widths.map(width=>E('col',{style:'width:'+width+'px'}))):null,E('thead',{},E('tr',{},heads.map(h=>E('th',{scope:'col'},h)))),E('tbody',{},rows.map(row=>E('tr',{},row.map(v=>E('td',{},v)))))))); }
    function panel(title, svg) { return E('section',{class:'decimal-panel'},E('h4',{},title),E('p',{class:'decimal-scroll-help'},'Enlarge for closer inspection. Scroll a wide diagram sideways, or focus it and use the arrow keys.'),E('div',{class:'decimal-viewport',tabindex:0,role:'region','aria-label':title+' diagram; scroll if needed'},svg)); }
    function aligned() {
      const rows = [['A: '+state.a,...model.columns.map(col=>E('span',{class:(col.aExplicit?'':'decimal-padding ') + (state.mode==='compare'&&model.sameSign&&col.power===model.firstDifferentPower?'decimal-different':''),'data-decimal-digit':'A','data-power':col.power},col.aDigit))]];
      if (state.mode === 'compare') rows.push(['B: '+state.b,...model.columns.map(col=>E('span',{class:(col.bExplicit?'':'decimal-padding ') + (model.sameSign&&col.power===model.firstDifferentPower?'decimal-different':''),'data-decimal-digit':'B','data-power':col.power},col.bDigit))]);
      const alignedTable=table('Equal places are aligned; lighter zeros are padding',['Input',...model.columns.map(col=>placeName(col.power)+(col.power===0?' · decimal point follows':''))],rows,[140,...model.columns.map(()=>90)]);alignedTable.querySelector('table').style.tableLayout='fixed';alignedTable.querySelector('table').style.minWidth=(140+model.columns.length*90)+'px';alignedTable.querySelector('table').style.width=(140+model.columns.length*90)+'px';return alignedTable;
    }
    function bars(title, rows) {
      const values = rows.map(row=>R(row[1])), zero=c.q(0), lo=values.reduce((a,b)=>c.compare(a,b)<0?a:b,zero), hi=values.reduce((a,b)=>c.compare(a,b)>0?a:b,zero);
      let span=c.sub(hi,lo);if(!span.n)span=c.q(1);const padding=c.div(span,c.q(20)),min=c.sub(lo,padding),max=c.add(hi,padding),den=c.pack(c.sub(max,min)).value,X=p=>180+c.pack(c.sub(p,min)).value/den*500;
      const height=100+rows.length*67,svg=S('svg',{viewBox:'0 0 720 '+height,role:'img','aria-label':title,'data-decimal-plot':'bars'});svg.dataset.domain=JSON.stringify({min:c.pack(min),max:c.pack(max),x0:180,x1:680});
      for(let i=0;i<=2;i++){const v=c.add(min,c.mul(c.sub(max,min),c.q(i,2)));svg.append(S('line',{x1:X(v),y1:20,x2:X(v),y2:height-55,stroke:'#d2d7ce'}),S('text',{x:X(v),y:height-25,'text-anchor':i===0?'start':i===2?'end':'middle','font-size':13,'data-decimal-axis':c.pack(v).fraction},c.pack(v).exact));}
      rows.forEach(([label,p],i)=>{const y=32+i*67,x0=X(zero),x1=X(R(p));svg.append(S('text',{x:10,y:y+18},label),S('rect',{x:Math.min(x0,x1),y,width:Math.abs(x1-x0),height:24,fill:p.value<0?'#a75c4b':'#267f78','data-decimal-bar':label,'data-exact':p.fraction}),S('text',{x:180,y:y+45},p.exact));});svg.append(S('line',{x1:X(zero),y1:15,x2:X(zero),y2:height-55,stroke:'#354b48','stroke-width':2}));return panel(title,svg);
    }
    function area() {
      const svg=S('svg',{viewBox:'55 40 450 405',class:'decimal-compact',role:'img','aria-label':'Multiplication rectangle on equally scaled nonnegative axes','data-decimal-plot':'area'}),extent=model.axisExtent.value,scale=280/extent;
      svg.append(S('rect',{x:180,y:80,width:280,height:280,fill:'#f8f4e9',stroke:'#83949a'}),S('rect',{x:180,y:360-model.magnitudeB.value*scale,width:model.magnitudeA.value*scale,height:model.magnitudeB.value*scale,fill:'#267f78','fill-opacity':.85,'data-decimal-area':'','data-exact':abs(model.result).fraction}));
      for(let i=0;i<=10;i++){const value=c.pack(c.mul(R(model.axisExtent),c.q(i,10))).exact;svg.append(S('line',{x1:180+i*28,y1:80,x2:180+i*28,y2:360,stroke:'#83949a'}),S('line',{x1:180,y1:80+i*28,x2:460,y2:80+i*28,stroke:'#83949a'}));if(i%5===0)svg.append(S('text',{x:180+i*28,y:385,'text-anchor':'middle'},value),S('text',{x:164,y:365-i*28,'text-anchor':'end'},value));}
      svg.append(S('text',{x:320,y:423,'text-anchor':'middle'},'A magnitude: '+model.magnitudeA.exact),S('text',{x:75,y:220,transform:'rotate(-90 75 220)','text-anchor':'middle'},'B magnitude: '+model.magnitudeB.exact));svg.dataset.extent=JSON.stringify(model.axisExtent);return panel('Nonnegative area; algebraic sign is separate',svg);
    }
    function groups() {
      const w=model.groupWindow;if(w.empty)return E('p',{},model.quotient.n==='0'?'A zero dividend contains zero groups.':'This window begins after the final group. Reduce the number of groups skipped.');
      const svg=S('svg',{viewBox:'0 0 '+Math.max(300,28+w.groups.length*54+24)+' 180',class:w.groups.length<=6?'decimal-compact':'',role:'img','aria-label':'Consecutive divisor-sized group positions','data-decimal-plot':'groups'});
      w.groups.forEach((group,j)=>{const x=28+j*54;svg.append(S('rect',{x,y:45,width:46,height:45,fill:'#f8f4e9',stroke:'#83949a'}),S('rect',{x,y:45,width:46*group.fraction.value,height:45,fill:'#267f78','data-decimal-group':group.index,'data-exact':group.fraction.fraction}),S('text',{x:x+23,y:115,'text-anchor':'middle'},String(j+1)));});
      svg.append(S('text',{x:28,y:150},'Numbers count positions within this displayed window.'));return panel('A window of equal-sized groups',svg);
    }
    function rounding() {
      // Subtract exact rationals before converting: small offsets near a large
      // value must not disappear through floating-point cancellation.
      const point=p=>100+c.pack(c.div(c.sub(R(p),R(model.lower)),R(model.unit))).value*520;
      const svg=S('svg',{viewBox:'80 40 560 205',class:'decimal-compact',role:'img','aria-label':'Neighboring decimal marks, halfway point, input and rounded value','data-decimal-plot':'round'});
      svg.append(S('line',{x1:100,y1:110,x2:620,y2:110,stroke:'#354b48'}));
      for(const [p,label] of [[model.lower,'Lower'],[model.midpoint,'Halfway'],[model.upper,'Upper']])svg.append(S('line',{x1:point(p),y1:100,x2:point(p),y2:120,stroke:'#354b48'}),S('text',{x:point(p),y:label==='Halfway'?195:170,'text-anchor':label==='Lower'?'start':label==='Upper'?'end':'middle'},label));
      svg.append(S('circle',{cx:point(model.a),cy:74,r:6,fill:'#a75c4b','data-decimal-round':'input','data-exact':model.a.fraction}),S('line',{x1:point(model.a),y1:80,x2:point(model.a),y2:110,stroke:'#a75c4b'}),S('circle',{cx:point(model.rounded),cy:142,r:6,fill:'#267f78','data-decimal-round':'rounded','data-exact':model.rounded.fraction}));return panel('Round on one exact interval',svg);
    }
    function refresh() {
      operation.value=state.mode;root.dataset.state=JSON.stringify(state);$('[data-decimal-error]').textContent='';const out=$('[data-decimal-result]');out.replaceChildren();
      if(model.status==='undefined'){out.append(E('p',{role:'status',class:'decimal-undefined'},model.reason));size();return;}
      if(state.mode==='place'){out.append(E('p',{class:'decimal-equation'},state.a+' = '+model.expanded.map(p=>paren(p.exact)).join(' + ')+' = '+model.a.exact),aligned(),table('Digit contributions',['Place','Digit','Unit value','Contribution'],model.columns.map(col=>[placeName(col.power),col.aDigit,col.unit.exact,col.contribution.exact])));}
      else if(state.mode==='compare'){out.append(E('p',{class:'decimal-equation'},state.a+' '+(model.relation<0?' < ':model.relation>0?' > ':' = ')+state.b),aligned(),E('p',{},!model.sameSign?'The signs determine the order.':model.relation===0?'Every aligned place has the same value. A trailing zero does not change the number.':'The first different magnitude place is '+placeName(model.firstDifferentPower).toLowerCase()+'.'+(model.a.value<0?' Both numbers are negative, so reverse the magnitude order.':'')),bars('The same number-line scale',[['A',model.a],['B',model.b]]));}
      else if(['add','subtract'].includes(state.mode)){out.append(E('p',{class:'decimal-equation'},paren(state.a)+(state.mode==='add'?' + ':' − ')+paren(state.b)+' = '+model.result.exact),E('p',{},'Aligned inputs: '+model.alignedA+' and '+model.alignedB+'. The column work uses magnitude '+model.magnitudeOperation+' in order '+model.magnitudeOrder.join(', ')+'; final sign '+(model.sign<0?'negative':model.sign>0?'positive':'zero')+'.'),table('Work from the smallest displayed place',['Place','Top magnitude digit','Bottom magnitude digit','Incoming '+(model.magnitudeOperation==='add'?'carry':'borrow'),'Result digit','Outgoing '+(model.magnitudeOperation==='add'?'carry':'borrow')],model.columns.map(col=>[placeName(col.power),col.aDigit,col.bDigit,col.transferIn,col.result,col.transferOut])),bars('Inputs and result on one common scale',[['A',model.a],['B',model.b],['Result',model.result]]));}
      else if(state.mode==='multiply'){out.append(E('p',{class:'decimal-equation'},paren(state.a)+' × '+paren(state.b)+' = '+model.result.exact),E('p',{},model.integerA+' × '+paren(model.integerB)+' = '+model.integerProduct+' in integer coefficients. Divide by 10^'+model.decimalPlaces+' to restore the decimal places.'),area(),E('p',{},'Area magnitude = '+abs(model.result).exact+' square units. The algebraic product is '+model.result.exact+'. Both axes use the same unit scale, from 0 to '+model.axisExtent.exact+'. Grid spacing is '+c.pack(c.div(R(model.axisExtent),c.q(10))).exact+' original units on each axis.'));}
      else if(state.mode==='divide'){out.append(E('p',{class:'decimal-equation'},paren(state.a)+' ÷ '+paren(state.b)+' = '+paren(model.scaledA)+' ÷ '+paren(model.scaledB)+' = '+model.quotient.exact),E('p',{},'Both operands were multiplied by '+model.scaleFactor+'. Magnitudes contain '+model.fullGroups+' complete groups and '+model.fractionOfLastGroup.exact+' of a further group; remainder amount '+model.remainderAmount.exact+'.'+(model.quotient.decimal===null?' The exact quotient has a nonterminating decimal expansion.':'')),groups(),E('p',{},(model.groupWindow.groups.length?'This window shows absolute group positions '+String(BigInt(model.groupWindow.groups[0].index)+1n)+' through '+String(BigInt(model.groupWindow.groups.at(-1).index)+1n)+'. ':'')+'Group positions before this window: '+model.groupWindow.hiddenBefore+'; after it: '+model.groupWindow.hiddenAfter+'.'),bars('Dividend and divisor on one common scale',[['Dividend',model.a],['Divisor',model.b]]));}
      else if(state.mode==='round'){out.append(E('p',{class:'decimal-equation'},state.a+' rounded to '+model.places+' decimal places is '+model.formatted+'.'),E('p',{},'Lower mark: '+model.lower.exact+'. Upper mark: '+model.upper.exact+'. Halfway: '+model.midpoint.exact+'. The upper marker row shows the input; the lower row shows the selected rounding mark.'+(model.alreadyExact?' The input already lies exactly on a selected-place mark.':model.halfway?' This is an exact tie: round away from zero.':'')),rounding());}
      else{out.append(table('Exact item costs',['Item','Unit price','Quantity','Subtotal'],[['A',model.priceA,state.quantityA,model.costA.exact],['B',model.priceB,state.quantityB,model.costB.exact]]),E('p',{class:'decimal-equation'},'Total: '+model.totalMoney+'. Tendered: '+model.paid+'. '+(model.sufficient?'Change: ':'Still owed: ')+model.changeMoney+'.'),E('p',{},'Tender minus total = '+model.balance.exact+'.'),bars('Costs, tender and signed balance',[['Total',model.total],['Tender',c.pack(c.parse(state.tender).rational)],['Balance',model.balance]]));}
      out.append(E('p',{class:'decimal-note'},model.note));size();
    }
    function size(){root.classList.toggle('decimal-enlarged',enlarged);$('[data-decimal-zoom]').textContent=enlarged?'Fit diagrams':'Enlarge diagrams';$('[data-decimal-zoom]').setAttribute('aria-pressed',String(enlarged));}
    operation.addEventListener('change',()=>{state=c.defaults(operation.value);model=c.build(state);preset.value='';controls();refresh();});
    preset.addEventListener('change',()=>{const p=presets.find(p=>p[0]===preset.value);if(!p)return;state={...c.defaults(p[2].mode),...p[2]};model=c.build(state);controls();refresh();});
    $('[data-decimal-reset]').onclick=()=>{state=c.defaults();model=c.build(state);enlarged=false;preset.value='';controls();refresh();};$('[data-decimal-zoom]').onclick=()=>{enlarged=!enlarged;size();};
    root.getModelSpeech=()=>modes[state.mode]+'. Accepted inputs: '+fields().map(([k,label])=>label+': '+state[k]).join('; ')+'. '+[...$('[data-decimal-result]').querySelectorAll('p,h4,th,td')].map(n=>n.textContent).join(' ');
    if(hooks.speakButton)heading.prepend(hooks.speakButton(root.getModelSpeech,'Read this activity aloud'));
    root.decimal={getState:()=>({...state}),getModel:()=>model};controls();refresh();return root;
  }
  const api=Object.freeze({render});if(host)host.PrimerDecimalLab=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window==='undefined'?null:window);
