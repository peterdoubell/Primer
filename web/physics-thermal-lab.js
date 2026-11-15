/* Original calibrated heat-transfer artwork. SI balances determine all plotted data. */
(function () {
  'use strict';
  const NS='http://www.w3.org/2000/svg',SIGMA=5.670374419e-8,CP=4180;
  const initial=Object.freeze({mode:'conduction',left:80,right:20,area:100,length:5,conductivity:1,
    flow:10,coefficient:100,emissivity:80,capacityA:1000,capacityB:1000,conductance:5,time:0});
  const controls=Object.freeze([
    ['left','Temperature A / wall / surface',-20,120,1,'°C',['contact','conduction','stream','radiation']],
    ['right','Temperature B / inlet / surroundings',-20,120,1,'°C',['contact','conduction','stream','radiation']],
    ['area','Cross-section / exposed surface area',10,200,10,'cm²',['conduction','radiation']],
    ['length','Slab thickness / heated path length',.5,20,.5,'cm',['conduction','stream']],
    ['conductivity','Thermal conductivity k',.02,200,.02,'W/(m·K)',['conduction']],
    ['flow','Water mass flow',1,50,1,'g/s',['stream']],
    ['coefficient','Wall convection coefficient h',10,500,10,'W/(m²·K)',['stream']],
    ['emissivity','Thermal emissivity / absorptivity',0,100,1,'/100',['radiation']],
    ['capacityA','Heat capacity A',100,5000,100,'J/K',['contact']],
    ['capacityB','Heat capacity B',100,5000,100,'J/K',['contact']],
    ['conductance','Contact conductance G',0,20,.5,'W/K',['contact']],
    ['time','Time in contact',0,600,1,'s',['contact']],
  ].map(([key,label,min,max,step,unit,modes])=>Object.freeze({key,label,min,max,step,unit,modes})));
  const modes=Object.freeze([['conduction','Conduction through a stationary slab'],['stream','Convection: water through a heated channel'],['radiation','Radiation across a vacuum']]);
  const fmt=n=>Number(n.toPrecision(6)).toString();let serial=0;
  function normalize(raw={}) {
    const s={mode:['contact',...modes.map(m=>m[0])].includes(raw.mode)?raw.mode:initial.mode};
    for(const c of controls)s[c.key]=Number.isFinite(Number(raw[c.key]))?Math.max(c.min,Math.min(c.max,Number(raw[c.key]))):initial[c.key];
    if(s.mode==='stream')for(const key of ['left','right'])s[key]=Math.max(5,Math.min(95,s[key]));
    return s;
  }
  function contactAt(s,t) {
    const a=s.capacityA,b=s.capacityB,delta=s.left-s.right,rate=s.conductance*(1/a+1/b);
    const fraction=-Math.expm1(-rate*t),energy=delta===0||fraction===0?0:a*b/(a+b)*delta*fraction;
    return {a:s.left-energy/a,b:s.right+energy/b,energy,power:s.conductance===0||delta===0?0:s.conductance*delta*Math.exp(-rate*t)};
  }
  function streamAt(s,x) {
    // Steady plug-flow energy balance m_dot cp dT/dx = h P (T_wall-T).
    const exponent=s.coefficient*.04*x/(s.flow*.001*CP);
    return s.right+(s.left-s.right)*(-Math.expm1(-exponent));
  }
  function build(raw) {
    const s=normalize(raw),area=s.area*1e-4,length=s.length*.01,delta=s.left-s.right;
    let m={state:s,area,length,delta};
    if(s.mode==='contact') {
      const at=contactAt(s,s.time),equilibrium=(s.capacityA*s.left+s.capacityB*s.right)/(s.capacityA+s.capacityB);
      const tau=s.conductance===0?Infinity:1/(s.conductance*(1/s.capacityA+1/s.capacityB));
      m={...m,...at,equilibrium,tau,points:Array.from({length:121},(_,i)=>({x:i*5,...contactAt(s,i*5)})),
        equation:'C_A dT_A/dt = −G(T_A−T_B); C_B dT_B/dt = G(T_A−T_B).',
        note:'Two hypothetical bodies are internally uniform, insulated from their surroundings, and have constant heat capacities and contact conductance. Their temperature gap decays exponentially. Temperature is not stored heat; the signed transferred energy comes from each capacity times its temperature change. No melting, evaporation, heat loss to a room or living tissue is modelled. G = 0 disconnects the bodies; then the weighted equilibrium temperature is a possible energy-balance value, not a temperature they will reach.',
        readout:`At ${fmt(s.time)} s: A = ${fmt(at.a)} °C, B = ${fmt(at.b)} °C. Energy from A to B = ${fmt(at.energy)} J; instantaneous rate = ${fmt(at.power)} W. ΔU_A = ${fmt(-at.energy)} J; ΔU_B = ${fmt(at.energy)} J; total change = 0 J. `+
          (s.conductance===0?'Contact is disconnected; both temperatures stay fixed.':`Equilibrium temperature = ${fmt(equilibrium)} °C; gap time constant = ${fmt(tau)} s. `)+
          (delta===0?'The bodies start at equal temperature, so net transfer is zero.':delta>0?'A warms B.':'B warms A; the signed A-to-B transfer is negative.')};
    } else if(s.mode==='conduction') {
      const power=s.conductivity*area*delta/length,gradient=-delta/length,flux=power/area;
      m={...m,power,gradient,flux,points:Array.from({length:81},(_,i)=>({x:length*i/80,t:s.left-delta*i/80})),
        equation:'Q̇ = −k A dT/dx = k A (T_A−T_B)/L.',
        note:'This is a steady, one-dimensional homogeneous slab with constant k, fixed boundary temperatures, no internal heat source, no contact resistance and insulated lateral faces. The matter stays in place. The linear temperature profile and constant signed flux follow Fourier’s law. Conductivity is a hypothetical adjustable parameter, not a measured material or skin-contact model. Area and thickness are real geometric inputs; no transient heating or phase change is solved.',
        readout:`Slab area = ${fmt(area)} m²; thickness = ${fmt(length)} m; k = ${fmt(s.conductivity)} W/(m·K). Temperature gradient = ${fmt(gradient)} K/m. Heat flux in +x = ${fmt(flux)} W/m²; rate A → B = ${fmt(power)} W. Matter is stationary. `+(delta===0?'Equal boundaries give zero net transfer.':delta>0?'Net energy moves from A to B.':'Net energy moves from B to A.')};
    } else if(s.mode==='stream') {
      const outlet=streamAt(s,length),power=s.flow*.001*CP*(outlet-s.right),ntu=s.coefficient*.04*length/(s.flow*.001*CP);
      m={...m,outlet,power,ntu,points:Array.from({length:81},(_,i)=>({x:length*i/80,t:streamAt(s,length*i/80)})),
        equation:'ṁ c_p dT/dx = h P (T_wall−T); Q̇ = ṁ c_p (T_out−T_in).',
        note:'A pump maintains steady one-way plug flow of liquid water through a hypothetical channel with wetted perimeter P = 0.04 m. Water has fixed c_p = 4180 J/(kg·K), and the wall has fixed temperature and uniform h. Axial conduction, viscous heating, pressure work and evaporation are omitted. The power ledger uses inlet enthalpy as its reference: output means the fluid’s enthalpy rise, not absolute outgoing enthalpy. Wall and inlet controls stay between 5 and 95 °C so this ambient-pressure water example remains liquid. This forced-convection model demonstrates energy carried by moving matter; it does not simulate buoyancy, rising air, turbulence or a natural-convection circulation. Greater flow can lower the outlet temperature change while increasing the total transfer rate.',
        readout:`Water flows inlet → outlet at ${fmt(s.flow*.001)} kg/s. T_in = ${fmt(s.right)} °C; wall = ${fmt(s.left)} °C; T_out = ${fmt(outlet)} °C. Heated length = ${fmt(length)} m; h = ${fmt(s.coefficient)} W/(m²·K); NTU = ${fmt(ntu)}. Wall-to-fluid rate = ${fmt(power)} W, exactly matching ṁ c_p ΔT. `+(delta===0?'Equal wall and inlet temperatures give no net heating.':delta>0?'The moving water gains energy from the wall.':'The moving water loses energy to the colder wall; flow still runs inlet → outlet.')};
    } else {
      const emissivity=s.emissivity/100,absoluteA=s.left+273.15,absoluteB=s.right+273.15;
      const emitted=emissivity*SIGMA*area*absoluteA**4,absorbed=emissivity*SIGMA*area*absoluteB**4;
      // Factored fourth-power difference retains equal-temperature zero exactly.
      const power=emissivity===0||delta===0?0:emissivity*SIGMA*area*delta*(absoluteA+absoluteB)*(absoluteA**2+absoluteB**2);
      m={...m,emissivity,absoluteA,absoluteB,emitted,absorbed,power,
        equation:'Q̇_out = ε σ A (T_surface⁴−T_surroundings⁴), with T in kelvin.',
        note:'A diffuse grey surface faces a large isothermal black enclosure with view factor 1 across a vacuum. Thermal absorptivity equals emissivity, which is held constant. The bars show emitted and absorbed thermal radiation, not total reflected radiation. Net outward power is their difference. The vacuum eliminates matter-mediated transfer in this ideal gap, while electromagnetic radiation persists. ε = 0 is an ideal perfectly reflecting surface with zero emission and absorption; ε = 1 is black. Solar colour/shortwave absorption, spectra, finite view factors and conductive supports of a real flask are outside this model.',
        readout:`Surface = ${fmt(absoluteA)} K; surroundings = ${fmt(absoluteB)} K; ε = ${fmt(emissivity)}; area = ${fmt(area)} m². Emitted = ${fmt(emitted)} W; absorbed = ${fmt(absorbed)} W; net outward = ${fmt(power)} W. `+(emissivity===0?'An ideal reflector exchanges no net thermal energy.':delta===0?'Emission and absorption remain equal; net exchange is zero.':delta>0?'The surface loses net energy.':'The surface gains net energy from warmer surroundings.')};
    }
    return m;
  }
  function el(tag,attrs={},...children){const e=document.createElement(tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));for(const c of children)if(c!=null)e.append(c.nodeType?c:document.createTextNode(String(c)));return e;}
  function sn(tag,attrs={},value){const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));if(value!=null)e.textContent=String(value);return e;}
  function render(item,hooks) {
    const scenario=item?.props?.scenario,contact=scenario==='phys.0.hot-cold.energy-balance';
    if(!contact&&scenario!=='phys.2.heat.transport')return null;
    const uid='thermal-'+ ++serial,root=el('section',{class:'card lesson-model physics-thermal-lab','data-renderer':'physics-thermal-lab','aria-labelledby':uid+'-title'});
    const start={...initial,mode:contact?'contact':'conduction'};let model=build(start);
    const readout=el('p',{class:'thermal-readout'}),equation=el('p',{class:'thermal-equation'}),note=el('p',{class:'spatial-note'}),live=el('p',{class:'thermal-live',role:'status','aria-live':'polite','aria-atomic':'true'});
    const select=el('select',{'aria-label':'Heat transfer model','data-thermal-mode':''});for(const [value,label] of modes)select.append(el('option',{value},label));
    select.hidden=contact;select.addEventListener('change',()=>{model=build({...model.state,mode:select.value});refresh(true);});
    const widgets=new Map(),inputs=el('div',{class:'model-controls concept-controls'});
    for(const c of controls){const id=uid+'-'+c.key,input=el('input',{id,type:'range',min:c.min,max:c.max,step:c.step,'data-thermal-control':c.key}),output=el('output',{for:id}),label=el('label',{for:id,class:'model-range-control'},c.label,output,input);
      input.addEventListener('input',()=>{model=build({...model.state,[c.key]:Number(input.value)});refresh(false);});input.addEventListener('change',()=>{live.textContent=model.readout;});inputs.append(label);widgets.set(c.key,{input,output,label,c});}
    const presets=el('div',{class:'model-button-row'});
    for(const [name,patch,label] of [['reverse',{left:20,right:80},'Reverse temperatures'],['equal',{left:50,right:50},'Equal temperatures'],...(contact?[['unequal',{capacityA:1000,capacityB:4000,left:80,right:20,time:100},'Large cool body']]:[['insulator',{mode:'conduction',conductivity:.04},'Poor conductor'],['reflector',{mode:'radiation',emissivity:5},'Low emissivity']])]){
      const b=el('button',{type:'button',class:'btn ghost small','data-thermal-preset':name},label);b.addEventListener('click',()=>{model=build({...model.state,...patch});refresh(true);});presets.append(b);}
    const reset=el('button',{type:'button',class:'btn ghost small','data-thermal-action':'reset'},'Reset');reset.addEventListener('click',()=>{model=build(start);refresh(true);});presets.append(reset);
    const enlarge=el('button',{type:'button',class:'btn ghost small','data-thermal-action':'enlarge','aria-pressed':'false'},'Enlarge plots');enlarge.addEventListener('click',()=>{const on=enlarge.getAttribute('aria-pressed')!=='true';enlarge.setAttribute('aria-pressed',String(on));root.classList.toggle('is-enlarged',on);enlarge.textContent=on?'Fit plots':'Enlarge plots';});
    const panels=el('div',{class:'thermal-panels'}),views=[];
    for(let i=0;i<2;i++){const svg=sn('svg',{viewBox:'0 0 440 350',role:'img','aria-labelledby':uid+'-svg-title-'+i,'aria-describedby':uid+'-svg-desc-'+i});views.push(svg);panels.append(el('div',{class:'thermal-viewport',tabindex:0,role:'region','aria-label':i?'Energy accounting; enlarge and scroll':'Temperatures and transport; enlarge and scroll'},svg));}
    root.append(el('div',{class:'model-heading-row'},el('h3',{id:uid+'-title'},item.title||'Track temperatures and energy'),enlarge),el('p',{class:'model-instructions'},item.instructions),select,presets,inputs,panels,equation,readout,note,
      el('p',{class:'spatial-note'},el('a',{href:'https://openstax.org/books/university-physics-volume-2/pages/1-6-mechanisms-of-heat-transfer',target:'_blank',rel:'noopener noreferrer'},'Heat-transfer laws · OpenStax'),' · σ = 5.670374419 × 10⁻⁸ W/(m²·K⁴), ',el('a',{href:'https://physics.nist.gov/cgi-bin/cuu/Value?sigma',target:'_blank',rel:'noopener noreferrer'},'NIST CODATA'),'. Original artwork; no source figures copied.'),live);
    if(hooks?.speakButton)root.append(hooks.speakButton(()=>model.readout+' '+model.equation));
    function text(svg,x,y,value,attrs={}){svg.append(sn('text',{x,y,fill:'#263b46','font-size':12,...attrs},value));}
    function line(svg,a,b,color,attrs={}){svg.append(sn('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:color,'stroke-width':2,...attrs}));}
    function setup(i,title){const svg=views[i];svg.replaceChildren(sn('title',{id:uid+'-svg-title-'+i},title),sn('desc',{id:uid+'-svg-desc-'+i},model.readout),sn('rect',{x:0,y:0,width:440,height:350,fill:'#f5efdf',rx:10}));text(svg,18,25,title,{'font-size':15,'font-weight':600});return svg;}
    function plot(svg,xmax){const X=x=>72+338*x/xmax,Y=t=>275-211*(t+20)/140;
      for(let i=0;i<=4;i++){const x=xmax*i/4,t=-20+35*i;line(svg,[X(x),64],[X(x),275],'#d5cfbf');line(svg,[72,Y(t)],[410,Y(t)],'#d5cfbf');text(svg,X(x),297,fmt(x),{'text-anchor':'middle'});text(svg,64,Y(t)+4,fmt(t),{'text-anchor':'end'});}
      text(svg,18,47,'Temperature (°C)');text(svg,241,329,model.state.mode==='contact'?'Time (s)':'Distance along path (cm)',{'text-anchor':'middle'});return {X,Y};}
    function curve(svg,points,X,Y,key,color){svg.append(sn('path',{d:points.map((p,i)=>(i?'L':'M')+X(p.x)+' '+Y(p[key])).join(' '),fill:'none',stroke:color,'stroke-width':2,'data-thermal-series':key}));}
    function bars(svg,rows,unit){const max=Math.max(1,...rows.map(r=>Math.abs(r[1])))*1.1,X=q=>230+170*q/max;
      text(svg,18,47,'Signed energy balance ('+unit+')');for(const q of [-max,0,max]){line(svg,[X(q),75],[X(q),280],'#d5cfbf');text(svg,X(q),310,fmt(q),{'text-anchor':'middle'});}
      rows.forEach(([name,value,color],i)=>{const y=105+i*58;const b=sn('rect',{x:Math.min(X(0),X(value)),y,width:Math.abs(X(value)-X(0)),height:19,fill:color,'data-thermal-balance':name,'data-value':value,'data-scale':max});svg.append(b);text(svg,18,y-7,name+': '+fmt(value)+' '+unit);});text(svg,230,335,'Axis rescales; compare labelled values',{'text-anchor':'middle'});}
    function refresh(announce){const m=model,s=m.state;root.setAttribute('data-thermal-state',JSON.stringify(s));select.value=s.mode;
      for(const {input,output,label,c} of widgets.values()){const active=c.modes.includes(s.mode);label.hidden=!active;input.disabled=!active;const waterTemperature=s.mode==='stream'&&['left','right'].includes(c.key);input.min=waterTemperature?5:c.min;input.max=waterTemperature?95:c.max;input.value=s[c.key];output.textContent=fmt(s[c.key])+' '+c.unit;input.setAttribute('aria-valuetext',output.textContent);}
      const leftLabel=widgets.get('left').label.firstChild,rightLabel=widgets.get('right').label.firstChild;
      if(leftLabel)leftLabel.textContent=s.mode==='contact'?'Initial temperature A':s.mode==='stream'?'Wall temperature':s.mode==='radiation'?'Surface temperature':'Boundary temperature A';
      if(rightLabel)rightLabel.textContent=s.mode==='contact'?'Initial temperature B':s.mode==='stream'?'Inlet temperature':s.mode==='radiation'?'Surroundings temperature':'Boundary temperature B';
      const a=setup(0,s.mode==='contact'?'Two temperatures over time':s.mode==='radiation'?'Radiation across a vacuum':'Temperature along the material path'),b=setup(1,s.mode==='contact'?'Transferred energy':'Power accounting');
      if(s.mode==='contact'){const {X,Y}=plot(a,600);curve(a,m.points,X,Y,'a','#b96652');curve(a,m.points,X,Y,'b','#3e7085');line(a,[72,Y(m.equilibrium)],[410,Y(m.equilibrium)],'#b98a2f',{'stroke-dasharray':'4 4'});
        for(const [key,color] of [['a','#b96652'],['b','#3e7085']])a.append(sn('circle',{cx:X(s.time),cy:Y(m[key]),r:4,fill:color,'data-thermal-inspect':key}));
        text(a,86,58,'A (red), B (blue), energy-balance T (gold)',{'font-size':10});bars(b,[['ΔU_A',-m.energy,'#b96652'],['ΔU_B',m.energy,'#3e7085'],['Total change',0,'#317e78']],'J');
      }else if(s.mode!=='radiation'){const {X,Y}=plot(a,20),points=m.points.map(p=>({...p,x:p.x*100}));curve(a,points,X,Y,'t','#3e7085');
        if(s.mode==='stream'){line(a,[72,Y(s.left)],[X(s.length),Y(s.left)],'#b96652',{'stroke-dasharray':'4 4'});text(a,90,58,'Fixed wall (red), moving water (blue)',{'font-size':10});}
        else text(a,90,58,'Stationary matter; linear steady profile',{'font-size':10});
        bars(b,[['Input to path',m.power,'#b96652'],['Output from path',-m.power,'#3e7085'],['Stored power',0,'#317e78']],'W');
        if(s.mode==='stream'){text(b,18,286,'ṁ c_p ΔT = wall-to-water power');}
      }else{a.append(sn('rect',{x:30,y:80,width:100,height:155,fill:'#b96652',rx:8}),sn('rect',{x:310,y:80,width:100,height:155,fill:'#3e7085',rx:8}));
        text(a,80,110,'Surface',{'text-anchor':'middle'});text(a,80,140,fmt(m.absoluteA)+' K',{'text-anchor':'middle'});text(a,360,110,'Enclosure',{'text-anchor':'middle'});text(a,360,140,fmt(m.absoluteB)+' K',{'text-anchor':'middle'});
        text(a,220,70,'Vacuum: no moving matter',{'text-anchor':'middle'});
        if(m.emitted>0){line(a,[140,175],[300,175],'#b96652');line(a,[300,175],[288,167],'#b96652');line(a,[300,175],[288,183],'#b96652');}
        if(m.absorbed>0){line(a,[300,220],[140,220],'#3e7085');line(a,[140,220],[152,212],'#3e7085');line(a,[140,220],[152,228],'#3e7085');}
        text(a,220,163,'Emitted thermal energy',{'text-anchor':'middle'});text(a,220,248,'Absorbed thermal energy',{'text-anchor':'middle'});text(a,220,285,'Arrows indicate direction, not magnitude',{'text-anchor':'middle'});text(a,220,315,'Net outward = emitted − absorbed',{'text-anchor':'middle'});
        bars(b,[['Emitted outward',m.emitted,'#b96652'],['Absorbed inward',-m.absorbed,'#3e7085'],['Net outward',m.power,'#317e78']],'W');}
      equation.textContent=m.equation;readout.textContent=m.readout;note.textContent=m.note;if(announce)live.textContent=m.readout;
    }
    refresh(false);return root;
  }
  const api=Object.freeze({initial,controls,modes,normalize,contactAt,streamAt,build,render,SIGMA,CP});
  if(typeof window!=='undefined')window.PrimerPhysicsThermalLab=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
})();
