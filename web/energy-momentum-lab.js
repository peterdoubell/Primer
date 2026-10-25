/* Original SI mechanics diagrams. Idealized models and assumptions are explicit.
   The numerical model has no DOM dependency; plotted data preserve physical units. */
(function (host) {
  'use strict';
  const NS='http://www.w3.org/2000/svg';
  const scenario='phys.3.energy-work';
  const modes=Object.freeze([['collision','Collisions and reference frames'],['impulse','Force, contact time and impulse'],['work','Work, gravity and friction'],['power','Power and energy transfer']]);
  const controls=Object.freeze([
    ['massA','Mass A',.1,20,.1,2,'kg',['collision']],['massB','Mass B',.1,20,.1,1,'kg',['collision']],
    ['velocityA','Initial velocity A',-6,6,.1,4,'m/s',['collision']],['velocityB','Initial velocity B',-6,6,.1,0,'m/s',['collision']],
    ['restitution','Coefficient of restitution',0,1,.05,0,'',['collision']],['frame','Reference-frame velocity',-6,6,.1,0,'m/s',['collision']],
    ['collisionTime','Elapsed time',0,4,.01,1,'s',['collision']],
    ['impactMass','Object mass',.01,20,.01,.06,'kg',['impulse']],['incoming','Initial velocity',-12,12,.1,-4,'m/s',['impulse']],
    ['outgoing','Final velocity',-12,12,.1,0,'m/s',['impulse']],['duration','Force-pulse duration',.005,2,.005,.1,'s',['impulse']],
    ['fraction','Fraction of pulse elapsed',0,1,.01,.5,'',['impulse']],
    ['mass','Sliding mass',.1,1500,.1,2,'kg',['work']],['initialVelocity','Initial slope velocity',-20,20,.1,4,'m/s',['work']],
    ['force','Applied force along +q',-2500,2500,1,0,'N',['work']],['angle','Slope angle',-90,90,1,20,'°',['work']],
    ['gravity','Gravitational acceleration',0,20,.1,9.81,'m/s²',['work']],['friction','Friction coefficient (static = kinetic)',0,1,.01,.2,'',['work']],
    ['workTime','Elapsed time',0,10,.01,2,'s',['work']],
    ['watts','Constant input power',0,2000,1,60,'W',['power']],['seconds','Transfer time',0,600,1,300,'s',['power']],
    ['efficiency','Useful energy fraction',0,100,1,20,'%',['power']]
  ].map(([key,label,min,max,step,value,unit,active])=>Object.freeze({key,label,min,max,step,value,unit,active})));
  const initial=Object.freeze(Object.fromEntries([['mode','collision'],...controls.map(c=>[c.key,c.value])]));
  function normalize(raw={}) {
    if(!raw||typeof raw!=='object'||Array.isArray(raw))throw new TypeError('Supply a state object.');
    const s={...initial,...raw};
    for(const k of Object.keys(s))if(!Object.hasOwn(initial,k))throw new RangeError('Unknown state field: '+k);
    if(!modes.some(m=>m[0]===s.mode))throw new RangeError('Unknown mechanics station.');
    for(const c of controls)if(typeof s[c.key]!=='number'||!Number.isFinite(s[c.key])||s[c.key]<c.min||s[c.key]>c.max)throw new RangeError(c.label+' must be finite and between '+c.min+' and '+c.max+' '+c.unit+'.');
    return s;
  }
  const momentum=(m,v)=>m*v,kinetic=(m,v)=>.5*m*v*v;
  function collision(raw={}) {
    const s=normalize(raw),M=s.massA+s.massB,closing=s.velocityA-s.velocityB,willCollide=closing>0;
    const reduced=s.massA*s.massB/M,impulse=willCollide?reduced*(1+s.restitution)*closing:0;
    const vA=s.velocityA-impulse/s.massA,vB=s.velocityB+impulse/s.massB;
    const eventTime=willCollide?2/closing:null;
    const comVelocity=(s.massA*s.velocityA+s.massB*s.velocityB)/M;
    const lost=willCollide?.5*reduced*(1-s.restitution*s.restitution)*closing*closing:0;
    const at=t=>{
      const after=willCollide&&t>=eventTime,dt=after?t-eventTime:0;
      const xA=-1.3+s.velocityA*t+(after?(vA-s.velocityA)*dt:0)-s.frame*t;
      const xB=1.3+s.velocityB*t+(after?(vB-s.velocityB)*dt:0)-s.frame*t;
      const a=(after?vA:s.velocityA)-s.frame,b=(after?vB:s.velocityB)-s.frame;
      return {t,after,xA,xB,vA:a,vB:b,pA:momentum(s.massA,a),pB:momentum(s.massB,b),kA:kinetic(s.massA,a),kB:kinetic(s.massB,b),internal:after?lost:0,
        center:(s.massA*xA+s.massB*xB)/M};
    };
    const points=Array.from({length:81},(_,i)=>at(i/20));
    if(eventTime!==null&&eventTime<=4)points.push(at(eventTime));points.sort((a,b)=>a.t-b.t);
    const before={pA:s.massA*(s.velocityA-s.frame),pB:s.massB*(s.velocityB-s.frame),kA:kinetic(s.massA,s.velocityA-s.frame),kB:kinetic(s.massB,s.velocityB-s.frame)};
    const after={pA:s.massA*(vA-s.frame),pB:s.massB*(vB-s.frame),kA:kinetic(s.massA,vA-s.frame),kB:kinetic(s.massB,vB-s.frame)};
    return {state:s,willCollide,eventTime,impulse,lost,reduced,comVelocity,vA,vB,points,current:at(s.collisionTime),before,after,at,
      equation:'m_A u_A + m_B u_B = m_A v_A + m_B v_B; v_B−v_A = e(u_A−u_B). ΔK = −½μ(1−e²)(u_A−u_B)².',
      note:'Two nonrotating carts on an infinite, frictionless, horizontal track. Their schematic 0.60 m bodies start at −1.30 m and +1.30 m, leaving a 2.00 m gap. No external horizontal impulse acts. A collision is instantaneous: contact forces and deformation are not resolved here. e = 0 keeps the carts together; 0 < e < 1 transfers kinetic energy to unmodelled internal energy; e = 1 is elastic. The observer moves at constant velocity: x′ = x−v_frame t and v′ = v−v_frame. Total momentum and kinetic energy depend on frame; the collision’s kinetic-energy loss does not. When A is not catching B, no collision is applied.'};
  }
  function impulse(raw={}) {
    const s=normalize(raw),J=s.impactMass*(s.outgoing-s.incoming),t=s.fraction*s.duration;
    const at=t=>{
      const z=t/s.duration,cumulative=z<=.5?2*z*z:1-2*(1-z)*(1-z),force=J/s.duration*(z<=.5?4*z:4*(1-z));
      const velocity=s.incoming+J*cumulative/s.impactMass;
      return {t,force,impulse:J*cumulative,velocity,kinetic:kinetic(s.impactMass,velocity)};
    };
    return {state:s,J,average:J/s.duration,peak:2*J/s.duration,current:at(t),at,points:Array.from({length:81},(_,i)=>at(s.duration*i/80)),deltaK:kinetic(s.impactMass,s.outgoing)-kinetic(s.impactMass,s.incoming),
      equation:'J = ∫F dt = m(v_f−v_i); F_average = J/Δt; a triangular pulse has F_peak = 2J/Δt.',
      note:'A prescribed triangular NET force pulse acts in one dimension on a constant mass. Its area is fixed by the requested velocity change. It is a comparison model, not a measured impact waveform, contact deformation, force limit or damage prediction. Increasing duration reduces average and peak force only when the mass and velocity change are held fixed. Equal and opposite impulses act on the interacting partner if external impulses are negligible. Velocity can pass through zero and reverse; the signed work equals the kinetic-energy change, not impulse times speed.'};
  }
  function work(raw={}) {
    const s=normalize(raw),r=s.angle*Math.PI/180,N=Math.abs(s.angle)===90?0:s.mass*s.gravity*Math.cos(r),weight=s.mass*s.gravity*Math.sin(r),drive=s.force-weight,limit=s.friction*N;
    const initialSign=Math.sign(s.initialVelocity),canStart=Math.abs(drive)>limit;
    const firstAcceleration=initialSign?(drive-limit*initialSign)/s.mass:canStart?(drive-limit*Math.sign(drive))/s.mass:0;
    const stop=s.initialVelocity*firstAcceleration<0?-s.initialVelocity/firstAcceleration:null;
    const restart=canStart?(drive-limit*Math.sign(drive))/s.mass:0;
    const at=t=>{
      let q,v,length,a,frictionForce,status;
      if(stop!==null&&t>=stop){
        const qs=s.initialVelocity*stop+.5*firstAcceleration*stop*stop,dt=t-stop;
        a=restart;v=a*dt;const dq=.5*a*dt*dt;q=qs+dq;length=Math.abs(qs)+Math.abs(dq);
        frictionForce=a===0?-drive:-limit*Math.sign(drive);status=a===0?'At rest: static friction balances the drive':'Direction reversed after stopping';
      }else{
        a=firstAcceleration;v=s.initialVelocity+a*t;q=s.initialVelocity*t+.5*a*t*t;length=Math.abs(q);
        frictionForce=initialSign?-limit*initialSign:canStart?-limit*Math.sign(drive):-drive;
        status=s.initialVelocity===0&&a===0?'At rest: static friction balances the drive':'Sliding';
      }
      const appliedWork=s.force*q,gravityWork=-weight*q,frictionWork=-limit*length,K=kinetic(s.mass,v),U=weight*q,Q=limit*length,K0=kinetic(s.mass,s.initialVelocity);
      return {t,q,v,a,length,frictionForce,status,x:q*Math.cos(r),height:q*Math.sin(r),appliedWork,gravityWork,frictionWork,K,U,Q,K0,netWork:appliedWork+gravityWork+frictionWork,
        balance:K+U+Q-K0-appliedWork,pApplied:s.force*v,pGravity:-weight*v,pFriction:frictionForce*v};
    };
    const points=Array.from({length:101},(_,i)=>at(i/10));if(stop!==null&&stop<=10)points.push(at(stop));points.sort((a,b)=>a.t-b.t);
    return {state:s,N,weight,drive,limit,stop,firstAcceleration,restart,points,current:at(s.workTime),at,
      equation:'W_net = ΔK; W_applied = Fq; ΔU_g = mgq sinθ; Q = μN × distance travelled; K + U_g + Q = K₀ + W_applied.',
      note:'A point mass slides on an infinitely long straight slope with a constant force parallel to it. +q runs to the right and along the slope, or vertically upward at +90°; negative velocity runs the other way. Gravity is uniform; the normal force is mg cosθ and does no work. Static and kinetic friction deliberately share one coefficient here. At zero speed, static friction can hold the mass if |F−mg sinθ| ≤ μN; otherwise motion restarts in the direction of the remaining force. All stopping and reversal times are solved as exact constant-acceleration pieces, not by allowing friction to propel a stopped body. Q is the total internal-energy increase of the mass–slope system; its split between the surfaces is unspecified. Potential energy is zero at the initial position and can be negative. No rotation, air drag, finite track ends or changing friction are modelled.'};
  }
  function power(raw={}) {
    const s=normalize(raw),eta=s.efficiency/100,at=t=>({t,input:s.watts*t,useful:eta*s.watts*t,other:(1-eta)*s.watts*t});
    return {state:s,eta,current:at(s.seconds),points:Array.from({length:61},(_,i)=>at(i*10)),at,
      equation:'E_in = P_in t; E_useful = ηE_in; E_other = (1−η)E_in. 1 W = 1 J/s.',
      note:'A device receives constant input power for the selected time and transfers energy into two declared channels, with no net energy stored inside the device. The adjustable useful fraction is hypothetical; it is not a measured lamp, motor, human or thermal-engine efficiency. Other output is transferred energy, not destroyed energy. Start-up transients, time-varying loads and thermodynamic limits of specific devices are outside this accounting model. Zero input power or zero time transfers zero energy.'};
  }
  function build(raw={}){const s=normalize(raw);return {collision,impulse,work,power}[s.mode](s);}
  const presets=Object.freeze([
    ['stick','2 kg hits 1 kg and sticks',{mode:'collision',massA:2,massB:1,velocityA:4,velocityB:0,restitution:0,frame:0,collisionTime:1}],
    ['exchange','Equal masses exchange velocities',{mode:'collision',massA:2,massB:2,velocityA:4,velocityB:0,restitution:1,frame:0,collisionTime:1}],
    ['headon','Head-on collision',{mode:'collision',massA:2,massB:1,velocityA:3,velocityB:-3,restitution:.6,frame:0,collisionTime:1}],
    ['away','Moving apart: no collision',{mode:'collision',velocityA:-2,velocityB:2,frame:0,collisionTime:1}],
    ['short','Short stopping pulse',{mode:'impulse',impactMass:.06,incoming:-4,outgoing:0,duration:.01,fraction:.5}],
    ['long','Long stopping pulse',{mode:'impulse',impactMass:.06,incoming:-4,outgoing:0,duration:.2,fraction:.5}],
    ['bounce','Rebound doubles the velocity change',{mode:'impulse',impactMass:.06,incoming:-4,outgoing:4,duration:.1,fraction:1}],
    ['static','50 N push: no displacement',{mode:'work',mass:20,initialVelocity:0,force:50,angle:0,gravity:10,friction:.5,workTime:5}],
    ['fall','Frictionless descent',{mode:'work',mass:2,initialVelocity:0,force:0,angle:30,gravity:10,friction:0,workTime:2}],
    ['reverse','Climb, stop and slide back',{mode:'work',mass:2,initialVelocity:4,force:0,angle:30,gravity:10,friction:.1,workTime:2}],
    ['brake','Slide to a permanent stop',{mode:'work',mass:2,initialVelocity:4,force:0,angle:0,gravity:10,friction:.2,workTime:3}],
    ['crane','250 kg lifted 8 m at steady speed',{mode:'work',mass:250,initialVelocity:1,force:2500,angle:90,gravity:10,friction:0,workTime:8}],
    ['car','1500 kg at 20 m/s',{mode:'work',mass:1500,initialVelocity:20,force:0,angle:0,gravity:9.81,friction:0,workTime:0}],
    ['lamp','60 W for 5 minutes',{mode:'power',watts:60,seconds:300,efficiency:20}]
  ]);
  const fmt=n=>{if(!Number.isFinite(n))return 'not reached';return n===0?'0':String(Number(n.toPrecision(6)));};
  const COLORS={a:'#246d91',b:'#a74737',c:'#647a26',gold:'#966c08',ink:'#243640',grid:'#d1d6d4'};
  let serial=0;
  function render(item={},hooks={}){
    if(item.props?.scenario!==scenario||Object.keys(item.props).length!==1||item.renderer&&item.renderer!=='physics-concept-lab')return null;
    const doc=host.document;if(!doc)throw new Error('A document is required to render the workbench.');
    const el=(tag,attrs={},...children)=>{const n=doc.createElement(tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,String(v));for(const v of children)if(v!=null)n.append(v.nodeType?v:doc.createTextNode(String(v)));return n;};
    const svgEl=(tag,attrs={},value)=>{const n=doc.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(value!==undefined)n.textContent=String(value);return n;};
    const uid='energy-momentum-'+ ++serial,root=el('section',{class:'card lesson-model energy-momentum-lab','data-energy-momentum-lab':'true','aria-labelledby':uid+'-heading'});
    let model=build(),enlarged=false;
    const heading=el('h3',{id:uid+'-heading'},'Work, energy and momentum workbench');
    const intro=el('p',{},'Follow a physical trajectory, then inspect the quantities that must balance. Change real masses, velocities, forces and time; every graph carries its units.');
    const mode=el('select',{id:uid+'-mode','data-energy-control':'mode'});for(const[value,label]of modes)mode.append(el('option',{value},label));
    const reset=el('button',{type:'button',class:'btn ghost small','data-energy-action':'reset'},'Reset workbench');
    const zoom=el('button',{type:'button',class:'btn ghost small','data-energy-action':'enlarge','aria-pressed':'false'},'Enlarge diagrams');
    const com=el('button',{type:'button',class:'btn ghost small','data-energy-action':'com'},'Use centre-of-mass frame');
    const buttons=el('div',{class:'energy-buttons'},el('label',{for:uid+'-mode'},'Station ',mode),reset,zoom,com);
    const presetHost=el('div',{class:'energy-buttons'}),presetButtons=[];
    for(const[key,label,patch]of presets){const b=el('button',{type:'button',class:'btn ghost small','data-energy-preset':key},label);b.addEventListener('click',()=>commit({...model.state,...patch}));presetHost.append(b);presetButtons.push([b,patch.mode]);}
    const form=el('div',{class:'energy-controls'}),widgets=new Map(),error=el('p',{class:'energy-error',role:'alert','data-energy-error':''});
    for(const c of controls){const input=el('input',{type:'number',id:uid+'-'+c.key,min:c.min,max:c.max,step:'any','data-energy-control':c.key}),label=el('label',{for:input.id},c.label+' ('+(c.unit||'dimensionless')+')',input),range=el('input',{type:'range',min:c.min,max:c.max,step:c.step,'aria-label':c.label,'data-energy-range':c.key});
      label.append(range);form.append(label);widgets.set(c.key,{input,range,label,c});
      input.addEventListener('change',()=>{const raw=input.value.trim(),value=Number(raw);if(raw===''){input.setAttribute('aria-invalid','true');error.textContent='Enter a number for '+c.label+'. The applied state is unchanged.';return;}try{commit({...model.state,[c.key]:value});}catch(e){input.setAttribute('aria-invalid','true');error.textContent=e.message+' The applied state is unchanged.';}});
      input.addEventListener('keydown',e=>{if(e.key==='Enter'){input.dispatchEvent(new Event('change'));e.preventDefault();}if(e.key==='Escape'){input.value=model.state[c.key];input.removeAttribute('aria-invalid');error.textContent='';}});
      range.addEventListener('input',()=>commit({...model.state,[c.key]:Number(range.value)},false));range.addEventListener('change',()=>{live.textContent=speech();});
    }
    const panels=el('div',{class:'energy-panels'}),views=[];
    for(let i=0;i<4;i++){const svg=svgEl('svg',{viewBox:'0 0 520 340',role:'img','aria-labelledby':uid+'-title-'+i,'aria-describedby':uid+'-desc-'+i}),wrap=el('div',{class:'energy-viewport',tabindex:0,role:'region','aria-label':'Mechanics diagram '+(i+1)+'; enlarge and scroll'},svg);views.push({svg,wrap});panels.append(wrap);}
    const equation=el('p',{class:'energy-equation'}),readout=el('p',{'data-energy-readout':''}),note=el('p',{class:'spatial-note','data-energy-note':''}),table=el('table',{class:'energy-ledger','data-energy-ledger':''}),live=el('p',{class:'energy-live',role:'status','aria-live':'polite','aria-atomic':'true'});
    root.append(heading,intro,buttons,presetHost,form,error,panels,equation,readout,table,note,el('p',{class:'spatial-note'},'Physical laws: ',el('a',{href:'https://openstax.org/books/university-physics-volume-1/pages/9-2-impulse-and-collisions',target:'_blank',rel:'noopener noreferrer'},'impulse'),' · ',el('a',{href:'https://openstax.org/books/university-physics-volume-1/pages/9-4-types-of-collisions',target:'_blank',rel:'noopener noreferrer'},'collisions'),' · ',el('a',{href:'https://openstax.org/books/university-physics-volume-1/pages/7-3-work-energy-theorem',target:'_blank',rel:'noopener noreferrer'},'work–energy'),' (OpenStax). Original diagrams; no source figures copied.'),live);
    function speech(){return readout.textContent+' '+equation.textContent+' '+table.textContent+' '+note.textContent;}
    root.getModelSpeech=speech;if(hooks.speakButton)heading.prepend(hooks.speakButton(speech,'Read this activity aloud'));
    mode.addEventListener('change',()=>commit({...model.state,mode:mode.value}));reset.addEventListener('click',()=>{enlarged=false;commit(initial);});zoom.addEventListener('click',()=>{enlarged=!enlarged;size();});
    com.addEventListener('click',()=>{const m=collision(model.state);commit({...model.state,frame:m.comVelocity});});
    function size(){root.classList.toggle('is-enlarged',enlarged);zoom.setAttribute('aria-pressed',String(enlarged));zoom.textContent=enlarged?'Fit diagrams':'Enlarge diagrams';if(!enlarged)for(const v of views)v.wrap.scrollLeft=0;}
    function text(svg,x,y,value,attrs={}){svg.append(svgEl('text',{x,y,fill:COLORS.ink,'font-size':12,...attrs},value));}
    function line(svg,x1,y1,x2,y2,color=COLORS.grid,attrs={}){svg.append(svgEl('line',{x1,y1,x2,y2,stroke:color,'stroke-width':1,...attrs}));}
    function setup(i,title,description){const{svg,wrap}=views[i];wrap.hidden=false;svg.replaceChildren(svgEl('title',{id:uid+'-title-'+i},title),svgEl('desc',{id:uid+'-desc-'+i},description),svgEl('rect',{x:0,y:0,width:520,height:340,rx:10,fill:'#fffdf6'}));text(svg,18,27,title,{'font-size':16,'font-weight':600});return svg;}
    function bounds(values,includeZero=true){const v=includeZero?[0,...values]:values;let lo=Math.min(...v),hi=Math.max(...v),pad=(hi-lo)*.08;if(pad===0)pad=Math.max(1,Math.abs(lo)*.1);return [lo-pad,hi+pad];}
    const axisFmt=n=>n===0?'0':Math.abs(n)>=10000||Math.abs(n)<.001?n.toExponential(2):String(Number(n.toPrecision(4)));
    function axes(svg,{xmin=0,xmax,ymin,ymax,xlabel,ylabel,yTicks=true}){
      const X=x=>78+408*(x-xmin)/(xmax-xmin),Y=y=>274-204*(y-ymin)/(ymax-ymin);
      svg.setAttribute('data-energy-axes',JSON.stringify({xmin,xmax,ymin,ymax,x0:78,x1:486,y0:274,y1:70}));
      for(let i=0;i<=4;i++){const x=xmin+(xmax-xmin)*i/4,y=ymin+(ymax-ymin)*i/4;line(svg,X(x),70,X(x),274);if(yTicks)line(svg,78,Y(y),486,Y(y));text(svg,X(x),296,axisFmt(x),{'text-anchor':'middle','font-size':10});if(yTicks)text(svg,70,Y(y)+4,axisFmt(y),{'text-anchor':'end','font-size':10});}
      text(svg,18,52,ylabel,{'font-size':11});text(svg,282,326,xlabel,{'text-anchor':'middle','font-size':12});return {X,Y};
    }
    function curve(svg,points,ax,xkey,ykey,key,color){svg.append(svgEl('polyline',{points:points.map(p=>ax.X(p[xkey])+','+ax.Y(p[ykey])).join(' '),fill:'none',stroke:color,'stroke-width':2,'data-energy-series':key,'data-energy-values':JSON.stringify(points.map(p=>[p[xkey],p[ykey]]))}));}
    function point(svg,ax,x,y,key,color){svg.append(svgEl('circle',{cx:ax.X(x),cy:ax.Y(y),r:4,fill:color,'data-energy-point':key,'data-x':x,'data-y':y}));}
    function ledger(rows){table.replaceChildren(el('caption',{},'Numerical ledger (SI units)'),el('thead',{},el('tr',{},el('th',{scope:'col'},'Quantity'),el('th',{scope:'col'},'Value'),el('th',{scope:'col'},'Unit'))));const body=el('tbody',{});for(const[key,label,value,unit]of rows)body.append(el('tr',{'data-energy-row':key,'data-value':value},el('th',{scope:'row'},label),el('td',{},fmt(value)),el('td',{},unit)));table.append(body);}
    function signedBars(svg,rows,unit){const max=Math.max(1,...rows.map(r=>Math.abs(r[1])))*1.15,ax=axes(svg,{xmin:-max,xmax:max,ymin:0,ymax:1,xlabel:unit,ylabel:'Signed quantities; common scale',yTicks:false});for(let i=0;i<rows.length;i++){const[label,value,color,key]=rows[i],y=90+i*51;svg.append(svgEl('rect',{x:Math.min(ax.X(0),ax.X(value)),y,width:Math.abs(ax.X(value)-ax.X(0)),height:16,fill:color,'data-energy-bar':key,'data-value':value,'data-scale':max}));text(svg,84,y-6,label+': '+fmt(value)+' '+unit,{'font-size':11});}}
    function refresh(announce){const m=model,s=m.state;root.setAttribute('data-energy-state',JSON.stringify(s));mode.value=s.mode;com.hidden=s.mode!=='collision';for(const[b,active]of presetButtons)b.hidden=active!==s.mode;
      for(const{input,range,label,c}of widgets.values()){const active=c.active.includes(s.mode);label.hidden=!active;input.disabled=range.disabled=!active;input.value=s[c.key];range.value=s[c.key];range.setAttribute('aria-valuetext',fmt(s[c.key])+' '+c.unit);input.removeAttribute('aria-invalid');}
      views.forEach(v=>{v.wrap.hidden=true;v.svg.removeAttribute('data-energy-axes');});error.textContent='';equation.textContent=m.equation;note.textContent=m.note;
      if(s.mode==='collision'){
        const c=m.current,b=m.before,a=m.after,svg=setup(0,'Cart positions at '+fmt(s.collisionTime)+' s','Blue cart A and red cart B have calibrated 0.60 m widths on the same horizontal metre axis. Their body heights are schematic, not masses.');
        const midpoint=(c.xA+c.xB)/2,span=Math.max(4,(c.xB-c.xA+.6)*1.2),ax=axes(svg,{xmin:midpoint-span/2,xmax:midpoint+span/2,ymin:0,ymax:1,xlabel:'Position (m); axis follows carts in selected frame',ylabel:'A '+fmt(s.massA)+' kg (blue); B '+fmt(s.massB)+' kg (red); cross = COM',yTicks:false});
        line(svg,78,200,486,200,COLORS.ink,{'stroke-width':2});
        for(const[key,x,mass,color]of [['A',c.xA,s.massA,COLORS.a],['B',c.xB,s.massB,COLORS.b]]){svg.append(svgEl('rect',{x:ax.X(x-.3),y:155,width:ax.X(x+.3)-ax.X(x-.3),height:40,fill:color,'data-energy-cart':key,'data-position':x,'data-length':.6}));text(svg,ax.X(x),140,key,{'text-anchor':'middle','font-size':11});}
        line(svg,ax.X(c.center)-5,218,ax.X(c.center)+5,218,COLORS.gold,{'stroke-width':2});line(svg,ax.X(c.center),213,ax.X(c.center),223,COLORS.gold,{'stroke-width':2});
        const p=setup(1,'Trajectories over 4 seconds','The slope of position versus time is velocity. A kink marks instantaneous collision. Axis bounds include every shown position.');const ay=bounds(m.points.flatMap(p=>[p.xA,p.xB,p.center])),ap=axes(p,{xmax:4,ymin:ay[0],ymax:ay[1],xlabel:'Elapsed time (s)',ylabel:'Position (m); A blue, B red, COM green'});
        for(const[key,color]of [['xA',COLORS.a],['xB',COLORS.b],['center',COLORS.c]])curve(p,m.points,ap,'t',key,key,color);point(p,ap,s.collisionTime,c.xA,'A',COLORS.a);point(p,ap,s.collisionTime,c.xB,'B',COLORS.b);
        const pm=setup(2,'Momentum before and after','Signed momentum in the selected reference frame. The total is conserved.');signedBars(pm,[['A before',b.pA,COLORS.a,'pA-before'],['B before',b.pB,COLORS.b,'pB-before'],['A after',a.pA,COLORS.a,'pA-after'],['B after',a.pB,COLORS.b,'pB-after']],'kg·m/s');
        const ke=setup(3,'Energy before and after','Kinetic energy can become internal energy. The same total is retained including that transfer.');signedBars(ke,[['Initial kinetic',b.kA+b.kB,COLORS.a,'kinetic-before'],['Final kinetic',a.kA+a.kB,COLORS.b,'kinetic-after'],['Internal energy gained',m.lost,COLORS.gold,'internal']],'J');
        readout.textContent=(m.willCollide?'Contact at '+fmt(m.eventTime)+' s. '+(c.after?'The selected time is after contact. ':'The selected time is before contact. ')+(m.eventTime>4?'Contact is beyond the plotted time window. ':''):'A is not catching B; no collision occurs. ')+ 'Current velocities in this frame: A '+fmt(c.vA)+' m/s; B '+fmt(c.vB)+' m/s. '+(s.restitution===0&&m.willCollide?'After contact the carts move together. ':'')+'Cart heights are schematic; masses are the labelled values.';
        ledger([['p-before','Total momentum before',b.pA+b.pB,'kg·m/s'],['p-after','Total momentum after',a.pA+a.pB,'kg·m/s'],['vA-final','A final velocity in frame',m.vA-s.frame,'m/s'],['vB-final','B final velocity in frame',m.vB-s.frame,'m/s'],['J-A','Impulse on A',-m.impulse,'N·s'],['J-B','Impulse on B',m.impulse,'N·s'],['K-before','Kinetic energy before',b.kA+b.kB,'J'],['K-after','Kinetic energy after',a.kA+a.kB,'J'],['internal','Internal energy gained',m.lost,'J']]);
      }else if(s.mode==='impulse'){
        const c=m.current,a=setup(0,'Prescribed net-force pulse','The signed area beneath the triangular curve is impulse. Longer duration reduces peak force for the same velocity change.');const yr=bounds(m.points.map(p=>p.force)),ax=axes(a,{xmax:s.duration,ymin:yr[0],ymax:yr[1],xlabel:'Time since pulse starts (s)',ylabel:'Net force (N)'});curve(a,m.points,ax,'t','force','force',COLORS.a);point(a,ax,c.t,c.force,'force',COLORS.b);
        const b=setup(1,'Accumulated impulse','Impulse is the time integral of net force, not force itself.');const br=bounds(m.points.map(p=>p.impulse)),bx=axes(b,{xmax:s.duration,ymin:br[0],ymax:br[1],xlabel:'Time since pulse starts (s)',ylabel:'Impulse (N·s)'});curve(b,m.points,bx,'t','impulse','impulse',COLORS.c);point(b,bx,c.t,c.impulse,'impulse',COLORS.b);
        const v=setup(2,'Velocity response','Velocity follows the integrated force divided by mass, including any stop and rebound.');const vr=bounds(m.points.map(p=>p.velocity)),vx=axes(v,{xmax:s.duration,ymin:vr[0],ymax:vr[1],xlabel:'Time since pulse starts (s)',ylabel:'Velocity (m/s)'});curve(v,m.points,vx,'t','velocity','velocity',COLORS.a);point(v,vx,c.t,c.velocity,'velocity',COLORS.b);
        readout.textContent='At '+fmt(c.t)+' s: force '+fmt(c.force)+' N, accumulated impulse '+fmt(c.impulse)+' N·s, velocity '+fmt(c.velocity)+' m/s. Total impulse '+fmt(m.J)+' N·s; average force '+fmt(m.average)+' N; signed peak '+fmt(m.peak)+' N. ';
        ledger([['J','Total impulse',m.J,'N·s'],['F-mean','Average net force',m.average,'N'],['F-peak','Signed peak force',m.peak,'N'],['p-change','Momentum change',s.impactMass*(s.outgoing-s.incoming),'kg·m/s'],['delta-K','Total work / kinetic-energy change',m.deltaK,'J'],['current-K','Current kinetic energy',c.kinetic,'J']]);
      }else if(s.mode==='work'){
        const c=m.current,a=setup(0,'A mass on the calibrated slope','Horizontal and vertical axes use the same metres-per-pixel scale. The blue dot marks the mass; its radius is a display marker, not a physical size. The gold cross is the initial position.');
        const xs=m.points.map(p=>p.x),hs=m.points.map(p=>p.height),xmin=Math.min(0,...xs),xmax=Math.max(0,...xs),hmin=Math.min(0,...hs),hmax=Math.max(0,...hs),xc=(xmin+xmax)/2,hc=(hmin+hmax)/2,span=Math.max(1,xmax-xmin,2*(hmax-hmin))*1.18;
        const ax=axes(a,{xmin:xc-span/2,xmax:xc+span/2,ymin:hc-span/4,ymax:hc+span/4,xlabel:'Horizontal coordinate (m); equal scale',ylabel:'Height relative to start (m)'});
        curve(a,m.points,ax,'x','height','slope-path',COLORS.ink);point(a,ax,c.x,c.height,'mass-position',COLORS.a);line(a,ax.X(0)-5,ax.Y(0),ax.X(0)+5,ax.Y(0),COLORS.gold,{'stroke-width':2});line(a,ax.X(0),ax.Y(0)-5,ax.X(0),ax.Y(0)+5,COLORS.gold,{'stroke-width':2});
        text(a,90,64,'Slope angle '+fmt(s.angle)+'°; marker is schematic',{'font-size':10});
        const b=setup(1,'Kinetic, potential and internal energy','Potential energy is referenced to initial height and may be negative. Internal energy grows with distance travelled, including after reversal.');const br=bounds(m.points.flatMap(p=>[p.K,p.U,p.Q,p.K0+p.appliedWork])),bx=axes(b,{xmax:10,ymin:br[0],ymax:br[1],xlabel:'Elapsed time (s)',ylabel:'Energy (J): K blue, U red, Q green'});for(const[key,color]of [['K',COLORS.a],['U',COLORS.b],['Q',COLORS.c]])curve(b,m.points,bx,'t',key,key,color);
        const d=setup(2,'Work on the mass','The sum of signed work from applied force, gravity and friction equals the change in kinetic energy.');signedBars(d,[['Applied work',c.appliedWork,COLORS.a,'applied'],['Gravity work',c.gravityWork,COLORS.b,'gravity'],['Friction work',c.frictionWork,COLORS.gold,'friction'],['Net work = ΔK',c.netWork,COLORS.c,'net']],'J');
        const v=setup(3,'Displacement, stops and reversal','The slope of this curve is velocity. After reversal displacement can decrease while total distance and frictional energy increase.');const vr=bounds(m.points.map(p=>p.q)),vx=axes(v,{xmax:10,ymin:vr[0],ymax:vr[1],xlabel:'Elapsed time (s)',ylabel:'Signed distance along slope q (m)'});curve(v,m.points,vx,'t','q','q',COLORS.a);point(v,vx,c.t,c.q,'q',COLORS.b);
        readout.textContent=c.status+'. At '+fmt(c.t)+' s: q = '+fmt(c.q)+' m, height change = '+fmt(c.height)+' m, total travel = '+fmt(c.length)+' m; velocity = '+fmt(c.v)+' m/s. '+(m.stop!==null?'First zero velocity at '+fmt(m.stop)+' s. ':'')+'Normal force = '+fmt(m.N)+' N; current friction = '+fmt(c.frictionForce)+' N.';
        ledger([['K0','Initial kinetic energy',c.K0,'J'],['K','Current kinetic energy',c.K,'J'],['U','Gravitational potential change',c.U,'J'],['Q','Internal-energy increase',c.Q,'J'],['W','Applied work',c.appliedWork,'J'],['net','Net work',c.netWork,'J'],['delta-K','Kinetic-energy change',c.K-c.K0,'J'],['balance','K + U + Q − K₀ − W (rounding residual)',c.balance,'J'],['power','Applied instantaneous power',c.pApplied,'W'],['distance','Distance travelled',c.length,'m'],['velocity','Current slope velocity',c.v,'m/s'],['friction-force','Current signed friction force',c.frictionForce,'N']]);
      }else{
        const c=m.current,a=setup(0,'Energy transferred at constant power','Slope is power. Input energy equals the sum of useful and other transferred energy at every time.');const yr=bounds(m.points.map(p=>p.input)),ax=axes(a,{xmax:600,ymin:yr[0],ymax:yr[1],xlabel:'Elapsed time (s)',ylabel:'Energy (J): input blue, useful green, other red'});for(const[key,color]of [['input',COLORS.a],['useful',COLORS.c],['other',COLORS.b]])curve(a,m.points,ax,'t',key,key,color);point(a,ax,c.t,c.input,'input',COLORS.a);
        const b=setup(1,'Energy account at selected time','Other output is transferred energy, not missing or destroyed energy.');signedBars(b,[['Input',c.input,COLORS.a,'input'],['Useful output',c.useful,COLORS.c,'useful'],['Other output',c.other,COLORS.b,'other']],'J');
        readout.textContent=fmt(s.watts)+' W for '+fmt(s.seconds)+' s ('+fmt(s.seconds/60)+' min) transfers '+fmt(c.input)+' J. The chosen useful fraction '+fmt(s.efficiency)+'% gives '+fmt(c.useful)+' J useful and '+fmt(c.other)+' J other output.';
        ledger([['input','Input energy',c.input,'J'],['useful','Useful output',c.useful,'J'],['other','Other output',c.other,'J'],['useful-power','Useful output power',m.eta*s.watts,'W'],['other-power','Other output power',(1-m.eta)*s.watts,'W']]);
      }
      size();if(announce)live.textContent=speech();
    }
    function commit(raw,announce=true){const next=build(raw);model=next;refresh(announce);}
    refresh(false);return root;
  }
  const api=Object.freeze({scenario,modes,controls,initial,presets,normalize,collision,impulse,work,power,build,render});
  if(host)host.PrimerEnergyMomentumLab=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
