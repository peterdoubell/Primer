(function () {
'use strict';
const scenario='math.3.systems.general-form';
const keys=['a1','b1','c1','a2','b2','c2'];
const initial={a1:1,b1:1,c1:10,a2:1,b2:-1,c2:4};
const presets=[
 ['q1','1 · Sum and difference',[1,1,10,1,-1,4],'The shared point is (7, 3).'],
 ['q2','2 · Subtract equations',[2,1,11,1,1,7],'Subtract equation 2 from equation 1: x = 4.'],
 ['q3','3 · Parallel lines',[-2,1,1,-2,1,3],'Same slope, different intercepts: no solution.'],
 ['q4','4 · Substitute x = y + 2',[3,2,16,1,-1,2],'Substitution gives 5y = 10; y = 2.'],
 ['q5','5 · Adult and child tickets',[3,2,37,1,4,29],'x is adult price; y is child price. Prices are nonnegative. The unique pair is ($9, $5).'],
 ['q6','6 · An identity after elimination',[1,1,10,2,2,20],'Both proper equations describe the same line. The eliminated row is 0 = 0.'],
 ['q7','7 · Two elimination steps',[4,3,18,2,-1,4],'The shared point is (3, 2).'],
 ['q8','8 · Cows and chickens',[1,1,20,4,2,56],'x counts cows; y counts chickens. Counts must be nonnegative integers. The unique pair is (8, 12).'],
 ['q9','9 · A single crossing',[1,1,10,1,-1,4],'A point solves the system only when it lies on both lines.'],
 ['q10','10 · Start with y = 12 − 3x',[3,1,12,5,-2,9],'Equation 1 has y coefficient 1; isolating y avoids an opening division. The shared point is (3, 3).'],
 ['vertical','Vertical and horizontal constraints',[1,0,3,0,1,2],'Vertical lines are valid constraints: x = 3 and y = 2.'],
 ['empty','A contradictory zero row',[0,0,1,1,0,3],'0 = 1 is impossible. This is an empty constraint, not a line.'],
 ['free','One identity, one line',[0,0,0,2,-3,6],'The identity imposes no restriction; the other equation supplies one line.'],
 ['plane','Two identities',[0,0,0,0,0,0],'Every point in the x/y plane solves both identities.']
];
const gcd=(a,b)=>{a=a<0n?-a:a;b=b<0n?-b:b;while(b){[a,b]=[b,a%b];}return a;};
function fraction(n,d=1n){for(const v of [n,d])if(typeof v==='number'&&!Number.isSafeInteger(v))throw new RangeError('Exact fractions require safe integer Numbers or BigInts');n=BigInt(n);d=BigInt(d);if(!d)throw new RangeError('Zero denominator');if(d<0n){n=-n;d=-d;}const g=gcd(n,d);return {n:n/g,d:d/g};}
const add=(a,b)=>fraction(a.n*b.d+b.n*a.d,a.d*b.d);
const multiply=(a,b)=>fraction(a.n*b.n,a.d*b.d);
const negate=a=>fraction(-a.n,a.d);
const text=a=>a.d===1n?String(a.n):a.n+'/'+a.d;
const real=a=>Number(a.n)/Number(a.d);
const integer=v=>typeof v==='string'?Number(v.trim().replace('−','-')):v;
function valid(v){const token=typeof v==='string'?v.trim().replace('−','-'):v;return (typeof v==='number'?Number.isSafeInteger(v):typeof token==='string'&&/^[+-]?\d{1,3}$/.test(token))&&integer(v)>=-100&&integer(v)<=100;}
function normalize(raw={}){if(!raw||typeof raw!=='object'||Array.isArray(raw))raw={};return Object.fromEntries(keys.map(k=>[k,valid(raw[k])?integer(raw[k]):initial[k]]));}
const equation=(a,b,c)=>{let lhs=a?(a===1?'x':a===-1?'−x':a+'x'):'';if(b){const term=Math.abs(b)===1?'y':Math.abs(b)+'y';lhs+=lhs?(b<0?' − ':' + ')+term:(b<0?'−':'')+term;}return (lhs||'0')+' = '+c;};
function eliminate(rows){
 const matrix=rows.map(row=>row.map(v=>fraction(v))),snap=()=>matrix.map(row=>row.map(text));
 const steps=[{operation:'Original augmented matrix',matrix:snap()}];let pivotRow=0;
 for(let col=0;col<2&&pivotRow<2;col++){
  const found=matrix.findIndex((row,i)=>i>=pivotRow&&row[col].n!==0n);if(found<0)continue;
  if(found!==pivotRow){[matrix[found],matrix[pivotRow]]=[matrix[pivotRow],matrix[found]];steps.push({operation:'Swap rows '+(found+1)+' and '+(pivotRow+1),matrix:snap()});}
  const pivot=matrix[pivotRow][col];matrix[pivotRow]=matrix[pivotRow].map(v=>multiply(v,fraction(pivot.d,pivot.n)));
  steps.push({operation:'Divide row '+(pivotRow+1)+' by '+text(pivot),matrix:snap()});
  for(let r=0;r<2;r++)if(r!==pivotRow&&matrix[r][col].n){const factor=matrix[r][col];matrix[r]=matrix[r].map((v,j)=>add(v,negate(multiply(factor,matrix[pivotRow][j]))));steps.push({operation:'Row '+(r+1)+' ← row '+(r+1)+' − ('+text(factor)+') × row '+(pivotRow+1),matrix:snap()});}
  pivotRow++;
 }
 return {steps,matrix:snap(),rank:pivotRow};
}
function clip(a,b,c,radius){
 if(!a&&!b)return [];
 const points=[],push=(x,y)=>{if(Math.abs(x)<=radius+1e-8&&Math.abs(y)<=radius+1e-8&&!points.some(p=>Math.hypot(p[0]-x,p[1]-y)<1e-8))points.push([Math.max(-radius,Math.min(radius,x)),Math.max(-radius,Math.min(radius,y))]);};
 if(b)for(const x of [-radius,radius])push(x,(c-a*x)/b);
 if(a)for(const y of [-radius,radius])push((c-b*y)/a,y);
 return points.slice(0,2);
}
function substitute(rows){
 const candidates=rows.flatMap((row,r)=>row.slice(0,2).flatMap((v,c)=>v?[{r,c,value:v}]:[]));
 if(!candidates.length)return {steps:['Neither equation has a nonzero variable coefficient, so no variable can be isolated. Check the constant rows directly.'],pivot:null};
 candidates.sort((a,b)=>(Math.abs(a.value)===1?0:1)-(Math.abs(b.value)===1?0:1)||Math.abs(a.value)-Math.abs(b.value)||a.r-b.r||a.c-b.c);
 const {r,c}=candidates[0],other=1-r,free=1-c,p=rows[r],q=rows[other];
 const constant=fraction(p[2],p[c]),slope=fraction(-p[free],p[c]);
 const coefficient=add(fraction(q[free]),multiply(fraction(q[c]),slope)),rhs=add(fraction(q[2]),negate(multiply(fraction(q[c]),constant)));
 const variable=c?'y':'x',freeVariable=free?'y':'x';
 const steps=['Isolate '+variable+' in equation '+(r+1)+': '+variable+' = '+text(constant)+' + ('+text(slope)+')'+freeVariable,
  'Substitute that expression into equation '+(other+1)+': ('+text(coefficient)+')'+freeVariable+' = '+text(rhs)];
 if(coefficient.n){const answer=multiply(rhs,fraction(coefficient.d,coefficient.n)),back=add(constant,multiply(slope,answer));steps.push('Divide by '+text(coefficient)+': '+freeVariable+' = '+text(answer)+'. Substitute back: '+variable+' = '+text(back)+'.');}
 else steps.push(rhs.n?'The remaining statement 0 = '+text(rhs)+' is impossible.':'The remaining statement 0 = 0 is an identity; '+freeVariable+' is free.');
 return {steps,pivot:{row:r,column:c},constant:text(constant),slope:text(slope),freeVariable,coefficient:text(coefficient),rhs:text(rhs)};
}
function build(raw={}){
 const state=normalize(raw),{a1,b1,c1,a2,b2,c2}=state;
 const D=a1*b2-a2*b1,Nx=c1*b2-c2*b1,Ny=a1*c2-a2*c1;
 const impossible=(!a1&&!b1&&c1!==0)||(!a2&&!b2&&c2!==0)||(!D&&(Nx!==0||Ny!==0));
 const rank=(!a1&&!b1&&!a2&&!b2)?0:D?2:1;
 const kind=impossible?'none':D?'one':rank?'line':'plane';
 const pair=kind==='one'?[fraction(Nx,D),fraction(Ny,D)]:null;
 const solution=pair?.map(text)||null;
 const row=([a1,b1,c1].some((v,i)=>i<2&&v!==0))?[a1,b1,c1]:[a2,b2,c2];
 const parameter=kind==='line'?(row[0]?{x:text(fraction(row[2],row[0]))+' − ('+text(fraction(row[1],row[0]))+')t',y:'t'}:{x:'t',y:text(fraction(row[2],row[1]))}):null;
 const reduction=eliminate([[a1,b1,c1],[a2,b2,c2]]),substitution=substitute([[a1,b1,c1],[a2,b2,c2]]);
 const residuals=pair?[[a1,b1,c1],[a2,b2,c2]].map(([a,b,c])=>text(add(add(multiply(fraction(a),pair[0]),multiply(fraction(b),pair[1])),fraction(-c)))):null;
 const radius=Math.max(5,Math.ceil(1.2*Math.max(...(pair?pair.map(v=>Math.abs(real(v))):[0]),...[[a1,b1,c1],[a2,b2,c2]].flatMap(([a,b,c])=>[a?Math.abs(c/a):0,b?Math.abs(c/b):0]))));
 const zMax=Math.max(1,(Math.abs(a1)+Math.abs(b1))*radius+Math.abs(c1),(Math.abs(a2)+Math.abs(b2))*radius+Math.abs(c2));
 const lines=[[a1,b1,c1],[a2,b2,c2]].map(([a,b,c])=>({equation:equation(a,b,c),kind:a||b?'line':c?'empty':'plane',points:clip(a,b,c,radius)}));
 const readout=kind==='one'?'One solution: x = '+solution[0]+', y = '+solution[1]+'.':kind==='none'?'No solution: the augmented constraints are inconsistent.':kind==='line'?'Infinitely many solutions on a line: x = '+parameter.x+', y = '+parameter.y+'; t is any real number.':'Infinitely many solutions: every real pair (x, y).';
 return {state,kind,rank,determinant:D,numerators:[Nx,Ny],solution,parameter,residuals,reduction,substitution,radius,zMax,lines,readout,
  point:pair?pair.map(real):null,
  surfaces:[[a1,b1,c1],[a2,b2,c2]].map(([a,b,c])=>[[-radius,-radius],[radius,-radius],[radius,radius],[-radius,radius]].map(([x,y])=>[x,y,a*x+b*y-c])),
  note:'The solver uses exact rational arithmetic for integer coefficients from −100 to 100. Plots use floating-point screen projection. A finite graph window cannot establish consistency; the exact row reduction does. In 3D, height is the equation residual a×x + b×y − c, not a third unknown. The x/y and residual axes have separately labelled scales. Only points shared by both residual surfaces and the zero plane solve the system. Multiplying an equation changes its residual surface while preserving its zero set; distinct surfaces may therefore encode the same solution line.'};
}
function render(item,hooks){
 if(item?.renderer!=='math-systems-lab'||item.props?.scenario!==scenario)return null;
 const el=(tag,attrs={},...children)=>{const n=document.createElement(tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);for(const c of children.flat(Infinity))if(c!=null)n.append(typeof c==='object'?c:document.createTextNode(String(c)));return n;};
 const svg=(tag,attrs={},...children)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);for(const c of children)n.append(typeof c==='object'?c:document.createTextNode(String(c)));return n;};
 const root=el('section',{class:'card lesson-model math-systems-lab','data-renderer':'math-systems-lab'}),controls=el('div',{class:'systems-controls'}),inputs=new Map(),choose=el('select',{'aria-label':'Systems example','data-systems-example':''}),live=el('p',{role:'status','aria-live':'polite'});let model=build(initial),yaw=35,pitch=30,context=presets[0][3];
 choose.append(el('option',{value:'custom'},'Custom coefficients'));for(const[id,label]of presets)choose.append(el('option',{value:id},label));choose.value='q1';
 for(const key of keys){const input=el('input',{type:'text',inputmode:'numeric','aria-label':key,'data-systems-coefficient':key}),label=key[0]==='c'?'right side':key[0]+' coefficient';controls.append(el('label',{},'Equation '+key[1]+' · '+label+' (integer −100…100)',input));inputs.set(key,input);const commit=()=>{if(!valid(input.value)){input.setAttribute('aria-invalid','true');live.textContent='Enter an integer between −100 and 100. The accepted equations are retained.';return;}input.removeAttribute('aria-invalid');choose.value='custom';context='Custom coefficients: solve over the real numbers.';model=build({...model.state,[key]:integer(input.value)});refresh();};input.addEventListener('change',commit);input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();commit();}if(e.key==='Escape'){input.value=String(model.state[key]);input.removeAttribute('aria-invalid');}});}
 const readout=el('p',{class:'systems-readout'}),meaning=el('p'),plot=svg('svg',{viewBox:'0 0 600 450',role:'img','aria-label':'Exact equation zero sets in the x/y plane','data-systems-plot':'2d'}),space=svg('svg',{viewBox:'0 0 600 450',role:'img',tabindex:0,'aria-label':'Equation residual surfaces; arrow keys rotate, Home resets camera','data-systems-plot':'3d'}),steps=el('div',{class:'systems-steps'}),substitutionSteps=el('ol',{class:'systems-substitution'}),scales=el('p',{class:'spatial-note'}),camera=el('div',{class:'systems-camera'});
 for(const[key,label,min,max]of [['yaw','Turn',-180,180],['pitch','Tilt',15,75]]){const input=el('input',{type:'range',min,max,step:1,value:key==='yaw'?yaw:pitch,'data-systems-camera':key,'aria-label':label});input.addEventListener('input',()=>{if(key==='yaw')yaw=Number(input.value);else pitch=Number(input.value);draw3D();});camera.append(el('label',{},label,input));}
 const resetCamera=()=>{yaw=35;pitch=30;root.querySelector('[data-systems-camera="yaw"]').value=String(yaw);root.querySelector('[data-systems-camera="pitch"]').value=String(pitch);draw3D();};
 const reset=el('button',{type:'button',class:'btn ghost small'},'Reset camera');reset.addEventListener('click',resetCamera);camera.append(reset);
 space.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home'].includes(e.key))return;e.preventDefault();if(e.key==='Home'){resetCamera();return;}if(e.key==='ArrowLeft')yaw-=10;if(e.key==='ArrowRight')yaw+=10;if(e.key==='ArrowUp')pitch+=5;if(e.key==='ArrowDown')pitch-=5;yaw=((yaw+180)%360+360)%360-180;pitch=Math.max(15,Math.min(75,pitch));root.querySelector('[data-systems-camera="yaw"]').value=String(yaw);root.querySelector('[data-systems-camera="pitch"]').value=String(pitch);draw3D();});
 choose.addEventListener('change',()=>{const p=presets.find(p=>p[0]===choose.value);if(!p)return;model=build(Object.fromEntries(keys.map((k,i)=>[k,p[2][i]])));context=p[3];refresh();});
 function figure(title,picture,name){const viewport=el('div',{class:'systems-viewport',tabindex:0,role:'region','aria-label':title+'; enlarge and scroll for detail'},picture),toggle=el('button',{type:'button',class:'btn ghost small','aria-pressed':'false','data-systems-enlarge':name},'Enlarge '+name+' plot');toggle.addEventListener('click',()=>{const on=toggle.getAttribute('aria-pressed')!=='true';toggle.setAttribute('aria-pressed',String(on));toggle.textContent=(on?'Fit ':'Enlarge ')+name+' plot';picture.style.width=on?'600px':'';picture.style.minWidth=on?'600px':'';picture.style.maxWidth=on?'none':'';viewport.scrollLeft=0;viewport.scrollTop=0;});return el('figure',{},el('figcaption',{},title),toggle,viewport);}
 root.append(el('h3',{},item.title||'Systems: exact equations and geometric constraints'),el('p',{},'Choose any of the ten quiz examples, or edit general-form coefficients. Compare exact elimination with the zero sets and residual surfaces.'),choose,controls,meaning,readout,el('div',{class:'systems-figures'},figure('Where both equation residuals are zero',plot,'equation'),el('div',{},figure('3D residual surfaces and their zero contours',space,'residual'),camera,scales)),el('h4',{},'Substitution without rounding'),substitutionSteps,el('h4',{},'Exact row reduction'),el('p',{},'Each row lists the x coefficient, the y coefficient, then the right side after the vertical separator.'),steps,el('p',{class:'spatial-note'},model.note),live);
 const speech=()=>model.readout+' '+context+' '+model.substitution.steps.join('. ')+'. '+model.lines.map(l=>l.equation).join('. ')+'. '+model.reduction.steps.map(s=>s.operation+': '+s.matrix.map(r=>r.join(', ')).join('; ')).join('. ')+'. '+model.note;root.getModelSpeech=speech;if(hooks?.speakButton)root.append(hooks.speakButton(speech));
 const colors=['#245f91','#b35640'];
 function draw2D(){plot.replaceChildren();const R=model.radius,to=([x,y])=>[260+180*x/R,220-180*y/R];for(const v of [-R,-R/2,0,R/2,R]){const[x]=to([v,0]),[,y]=to([0,v]);plot.append(svg('line',{x1:x,y1:40,x2:x,y2:400,stroke:v===0?'#526057':'#c9bfae','stroke-width':v===0?2:1}),svg('line',{x1:80,y1:y,x2:440,y2:y,stroke:v===0?'#526057':'#c9bfae','stroke-width':v===0?2:1}),svg('text',{x,y:425,'text-anchor':'middle','font-size':19},v),svg('text',{x:70,y:y+6,'text-anchor':'end','font-size':18},v));}plot.append(svg('text',{x:463,y:228,'font-size':22},'x'),svg('text',{x:268,y:25,'font-size':22},'y'));
 model.lines.forEach((l,i)=>{if(l.kind==='plane')plot.append(svg('rect',{x:80,y:40,width:360,height:360,fill:colors[i],opacity:.08}));if(l.points.length===2){const a=to(l.points[0]),b=to(l.points[1]);plot.append(svg('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:colors[i],'stroke-width':4,'stroke-dasharray':i?'9 5':'none','data-systems-zero-line':i}));}plot.append(svg('text',{x:462,y:60+i*35,fill:colors[i],'font-size':20},'Equation '+(i+1)));});if(model.point){const p=to(model.point);plot.append(svg('circle',{cx:p[0],cy:p[1],r:7,fill:'#9f741b','data-systems-solution':'true'}));}}
 function draw3D(){space.replaceChildren();const yr=yaw*Math.PI/180,pr=pitch*Math.PI/180,project=([x,y,z])=>{x/=model.radius;y/=model.radius;z/=model.zMax;const u=x*Math.cos(yr)-y*Math.sin(yr),v=x*Math.sin(yr)+y*Math.cos(yr);return [300+90*u,235-90*(v*Math.cos(pr)+z*Math.sin(pr)),v*Math.sin(pr)-z*Math.cos(pr)];};const polygons=[{points:[[-model.radius,-model.radius,0],[model.radius,-model.radius,0],[model.radius,model.radius,0],[-model.radius,model.radius,0]],color:'#819080',id:'zero'},...model.surfaces.map((points,i)=>({points,color:colors[i],id:String(i)}))];polygons.sort((a,b)=>a.points.reduce((v,p)=>v+project(p)[2],0)-b.points.reduce((v,p)=>v+project(p)[2],0));for(const p of polygons)space.append(svg('polygon',{points:p.points.map(v=>project(v).slice(0,2).join(',')).join(' '),fill:p.color,opacity:p.id==='zero'?.13:.24,stroke:p.color,'data-systems-surface':p.id}));
 for(const[point,label,color,index]of [[[model.radius,0,0],'x','#566c91',0],[[0,model.radius,0],'y','#4e7954',1],[[0,0,model.zMax],'residual','#80578c',2]]){const a=project([0,0,0]),b=project(point);space.append(svg('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:color,'stroke-width':3,'data-systems-axis':label}),svg('circle',{cx:b[0],cy:b[1],r:4,fill:color}),svg('text',{x:25+index*180,y:62,fill:color,'font-size':20},label+' axis'));}
 model.lines.forEach((l,i)=>{if(l.points.length===2){const a=project([...l.points[0],0]),b=project([...l.points[1],0]);space.append(svg('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:colors[i],'stroke-width':4,'stroke-dasharray':i?'9 5':'none','data-systems-zero-contour':i}));}});if(model.point){const p=project([...model.point,0]);space.append(svg('circle',{cx:p[0],cy:p[1],r:7,fill:'#9f741b','data-systems-3d-solution':'true'}));}space.append(svg('text',{x:25,y:30,'font-size':20},'Blue: residual 1 · coral: residual 2'),svg('text',{x:25,y:420,'font-size':20},'Grey: zero plane · gold: shared solution'));scales.textContent='x/y ranges: −'+model.radius+'…'+model.radius+'. Residual height: −'+model.zMax+'…'+model.zMax+'. Turn '+yaw+'°, tilt '+pitch+'°. Rotation changes the view; the equations and exact solution stay fixed.';space.setAttribute('data-camera-state',JSON.stringify({yaw,pitch}));}
 function refresh(){root.setAttribute('data-systems-state',JSON.stringify(model.state));for(const[k,input]of inputs){input.value=String(model.state[k]);input.removeAttribute('aria-invalid');}meaning.textContent=context;readout.textContent=model.lines.map(l=>l.equation).join(' ; ')+'. '+model.readout+(model.residuals?' Exact residual checks: '+model.residuals.join(', ')+'.':'');substitutionSteps.replaceChildren(...model.substitution.steps.map(v=>el('li',{},v)));steps.replaceChildren(...model.reduction.steps.map(s=>el('section',{},el('p',{},s.operation),el('pre',{},s.matrix.map(row=>'[ '+row.slice(0,2).join('  ')+' │ '+row[2]+' ]').join('\n')))));draw2D();draw3D();live.textContent=model.readout;}
 root.getSystemsModel=()=>build(model.state);refresh();return root;
}
const api=Object.freeze({scenario,keys,initial,presets,valid,normalize,fraction,eliminate,substitute,clip,build,render});if(typeof window!=='undefined')window.PrimerMathSystemsLab=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
}());
