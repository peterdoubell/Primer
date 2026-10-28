/* Exact, bounded school-algebra models. Rational arithmetic never silently clamps. */
(function(host){
  'use strict';
  const IDS=['math.3.linear','math.3.slope','math.3.quadratics','math.3.polynomials'];
  const LIMIT=BigInt(Number.MAX_SAFE_INTEGER),INPUT_LIMIT=1000;
  const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
  const object=o=>o!==null&&typeof o==='object'&&!Array.isArray(o);
  function guard(n){if(n>LIMIT||n< -LIMIT)throw new RangeError('These values require exact fractions beyond this workbench’s supported range. Use smaller numbers or simpler fractions.');return n;}
  function gcd(a,b){a=a<0n?-a:a;b=b<0n?-b:b;while(b)[a,b]=[b,a%b];return a;}
  function rat(n,d=1n){guard(n);guard(d);if(d===0n)throw new RangeError('Division by zero is undefined.');if(d<0n){n=-n;d=-d;}const g=gcd(n,d);return Object.freeze({n:Number(n/g),d:Number(d/g)});}
  const Z=rat(0n),ONE=rat(1n),TWO=rat(2n),FOUR=rat(4n);
  function rational(v){
    if(object(v)){if(Object.keys(v).sort().join(',')!=='d,n'||!Number.isSafeInteger(v.n)||!Number.isSafeInteger(v.d))throw new TypeError('A rational needs safe integer n and d.');return rat(BigInt(v.n),BigInt(v.d));}
    if(!['number','string'].includes(typeof v)||typeof v==='number'&&!Number.isFinite(v))throw new TypeError('Enter a finite integer, decimal or fraction.');
    const s=String(v).trim();if(!/^[+-]?\d+(?:\.\d{1,6}|\/[+-]?\d+)?$/.test(s)||s.length>32)throw new TypeError('Enter an integer, a decimal with at most six places, or an integer fraction.');
    if(s.includes('/')){const[a,b]=s.split('/');return rat(BigInt(a),BigInt(b));}
    if(s.includes('.')){const neg=s[0]==='-',t=s.replace(/^[+-]/,''),[a,b]=t.split('.');return rat(BigInt(a+b)*(neg?-1n:1n),10n**BigInt(b.length));}
    return rat(BigInt(s));
  }
  const add=(a,b)=>rat(guard(guard(BigInt(a.n)*BigInt(b.d))+guard(BigInt(b.n)*BigInt(a.d))),guard(BigInt(a.d)*BigInt(b.d)));
  const neg=a=>rat(-BigInt(a.n),BigInt(a.d));
  const sub=(a,b)=>add(a,neg(b));
  const mul=(a,b)=>rat(guard(BigInt(a.n)*BigInt(b.n)),guard(BigInt(a.d)*BigInt(b.d)));
  const div=(a,b)=>{if(!b.n)throw new RangeError('Division by zero is undefined.');return rat(guard(BigInt(a.n)*BigInt(b.d)),guard(BigInt(a.d)*BigInt(b.n)));};
  const eq=(a,b)=>a.n===b.n&&a.d===b.d;
  const number=r=>typeof r==='number'?(Number.isFinite(r)?r:(()=>{throw new TypeError('Finite coordinate required.');})()):rational(r).n/rational(r).d;
  const text=r=>{const a=rational(r);return String(a.n)+(a.d===1?'':'/'+a.d);};
  function input(v,label){const r=rational(v);if(Math.abs(r.n/r.d)>INPUT_LIMIT||r.d>1000)throw new RangeError(label+' must have magnitude at most 1000 and reduced denominator at most 1000.');return r;}
  const frozen=o=>{if(o&&typeof o==='object'&&!Object.isFrozen(o)){Object.values(o).forEach(frozen);Object.freeze(o);}return o;};
  const clone=o=>JSON.parse(JSON.stringify(o));
  const initial={
    'math.3.linear':{a:'2',b:'6',c:'1',d:'10',leftScale:'1',rightScale:'1',testX:'0',step:0},
    'math.3.slope':{mode:'points',m:'2',atX:'0',x1:'1',y1:'3',x2:'3',y2:'-1',A:'2',B:'1',C:'5',relation:'none',throughX:'0',throughY:'0'},
    'math.3.quadratics':{a:'1',b:'-5',c:'6'},
    'math.3.polynomials':{mode:'factors',left:['-6','1','1'],right:['-2','1'],roots:['1','2','3'],leading:'1'}
  };
  function defaults(id){if(!has(initial,id))throw new RangeError('Unknown algebra lesson.');return clone(initial[id]);}
  function accept(id,raw){if(!object(raw))throw new TypeError('Supply an algebra state object.');const s=defaults(id);for(const k of Object.keys(raw))if(!has(s,k))throw new RangeError('Unknown algebra setting: '+k);Object.assign(s,raw);
    for(const k of Object.keys(s)){
      if(['mode','relation'].includes(k))continue;
      if(k==='step'){if(!Number.isInteger(s[k])||s[k]<0||s[k]>3)throw new RangeError('Solution step must be an integer from 0 to 3.');continue;}
      if(['left','right','roots'].includes(k)){if(!Array.isArray(s[k])||s[k].length<1||s[k].length>(k==='roots'?4:5))throw new RangeError(k==='roots'?'Supply one to four roots.':'Each polynomial input needs one to five coefficients (degree at most 4).');s[k]=s[k].map((v,i)=>text(input(v,k+' coefficient '+i)));}
      else s[k]=text(input(s[k],k));
    }
    if(id==='math.3.slope'&&(!['points','general','point-slope'].includes(s.mode)||!['none','parallel','perpendicular'].includes(s.relation)))throw new RangeError('Unknown line mode or relationship.');
    if(id==='math.3.polynomials'&&!['factors','factor-quadratic','add','multiply','divide'].includes(s.mode))throw new RangeError('Unknown polynomial operation.');return s;
  }
  function trim(a){const p=a.slice();while(p.length>1&&!p.at(-1).n)p.pop();return p;}
  const zeroPoly=p=>p.length===1&&!p[0].n;
  function polynomial(raw){if(!Array.isArray(raw)||raw.length<1||raw.length>9)throw new RangeError('A polynomial needs 1–9 ascending coefficients.');return trim(raw.map(rational));}
  function polyAdd(a,b){return trim(Array.from({length:Math.max(a.length,b.length)},(_,i)=>add(a[i]||Z,b[i]||Z)));}
  function polyMultiply(a,b){if(a.length+b.length-2>8)throw new RangeError('Result degree cannot exceed 8.');const p=Array.from({length:a.length+b.length-1},()=>Z);a.forEach((x,i)=>b.forEach((y,j)=>{p[i+j]=add(p[i+j],mul(x,y));}));return trim(p);}
  function polyDivide(a,b){a=trim(a);b=trim(b);if(zeroPoly(b))throw new RangeError('The zero polynomial cannot be a divisor.');let r=a.slice();const q=Array.from({length:Math.max(1,a.length-b.length+1)},()=>Z),steps=[];
    while(!zeroPoly(r)&&r.length>=b.length){const power=r.length-b.length,c=div(r.at(-1),b.at(-1)),take=Array.from({length:power},()=>Z).concat(b.map(v=>mul(v,c)));q[power]=add(q[power],c);r=polyAdd(r,take.map(neg));steps.push({power,coefficient:c,subtract:take,remainder:r.slice()});}
    const quotient=trim(q),rebuilt=polyAdd(polyMultiply(b,quotient),r);if(rebuilt.length!==a.length||rebuilt.some((v,i)=>!eq(v,a[i])))throw Error('Polynomial division identity failed.');return {quotient,remainder:r,steps,identity:true};
  }
  function evaluate(coefficients,x){if(typeof x!=='number'||!Number.isFinite(x)||Math.abs(x)>1e6)throw new RangeError('Graph x must be finite and within±1,000,000.');const p=polynomial(coefficients);let y=0;for(let i=p.length-1;i>=0;i--){y=y*x+number(p[i]);if(!Number.isFinite(y))throw new RangeError('Graph value is not finite.');}return y;}
  function evaluateExact(coefficients,x){const p=polynomial(coefficients),t=rational(x);let y=Z;for(let i=p.length-1;i>=0;i--)y=add(mul(y,t),p[i]);return y;}
  function polyText(p,variable='x'){p=trim(p);const terms=[];for(let i=p.length-1;i>=0;i--){const r=p[i];if(!r.n)continue;const magnitude=text(rat(BigInt(Math.abs(r.n)),BigInt(r.d))),power=i===0?'':i===1?variable:variable+'^'+i,coefficient=i&&magnitude==='1'?'':magnitude+(i?'·':'');terms.push((terms.length?(r.n<0?' − ':' + '):(r.n<0?'−':''))+coefficient+power);}return terms.join('')||'0';}
  const point=(id,label,x,y,exact=true)=>({id,label,x,y,exact});
  const curve=(id,label,coefficients,role='primary')=>({id,label,coefficients:trim(coefficients),role});
  const line=(id,label,A,B,C,role='primary')=>({id,label,A,B,C,role});
  const graph=()=>({curves:[],lines:[],points:[],segments:[]});
  const aff=(a,b)=>polyText([b,a]);
  const equation=(a,b,c,d)=>aff(a,b)+' = '+aff(c,d);
  function linear(s){const a=rational(s.a),b=rational(s.b),c=rational(s.c),d=rational(s.d),ls=rational(s.leftScale),rs=rational(s.rightScale),LA=mul(ls,a),LB=mul(ls,b),RA=mul(rs,c),RB=mul(rs,d),A=sub(LA,RA),B=sub(RB,LB),solution=A.n?div(B,A):null,kind=A.n?'unique':B.n?'none':'infinite';
    const original='('+text(ls)+')('+aff(a,b)+') = ('+text(rs)+')('+aff(c,d)+')';
    const steps=[original+' is the original equation.',equation(LA,LB,RA,RB)+' after distributing each scale across its complete bracket.',equation(A,Z,Z,B)+' after subtracting the right x term and the left constant from both sides.',kind==='unique'?'Divide both sides by '+text(A)+': x = '+text(solution)+'.':kind==='infinite'?'The equation reduces to 0 = 0: every real x satisfies it.':'The equation reduces to 0 = '+text(B)+': no x satisfies it.'];
    const stages=[[LA,LB,RA,RB],[LA,LB,RA,RB],[A,Z,Z,B],kind==='unique'?[ONE,Z,Z,solution]:[Z,Z,Z,B]],v=stages[s.step],g=graph();g.curves=[curve('left','Left expression',[v[1],v[0]]),curve('right','Right expression',[v[3],v[2]],'secondary')];
    if(solution)g.points.push(point('solution','Equal outputs at x='+text(solution),solution,add(mul(v[0],solution),v[1])));
    const trialX=rational(s.testX),trial={x:trialX,left:add(mul(LA,trialX),LB),right:add(mul(RA,trialX),RB)};trial.equal=eq(trial.left,trial.right);
    const selectedTrial={x:trialX,left:add(mul(v[0],trialX),v[1]),right:add(mul(v[2],trialX),v[3])};
    g.points.push(point('trial-left','Proposed x: left output',trialX,selectedTrial.left),point('trial-right','Proposed x: right output',trialX,selectedTrial.right));
    const parameterRule=A.n?{coefficient:div(rs,A),constant:neg(div(LB,A)),parameter:'d',condition:'A ≠0'}:null;
    const ledger=[{label:'Equation',text:original},{label:'Expanded equation',text:equation(LA,LB,RA,RB)},{label:'Collected equation',text:equation(A,Z,Z,B)},{label:'Solutions',text:kind==='unique'?'x = '+text(solution):kind==='none'?'No solution':'Every real number'}];
    ledger.push({label:'Check the original equation at x='+text(trialX),text:'Left = '+text(trial.left)+'; right = '+text(trial.right)+'. '+(trial.equal?'Both sides agree, so this value is a solution.':'The two sides differ, so this value is not a solution.')});
    if(parameterRule)ledger.push({label:'General right-constant parameter',text:'With a, b, c and both scales fixed, x = '+polyText([parameterRule.constant,parameterRule.coefficient],'d')+'. This follows from A·x = rightScale·d − leftScale·b, for A ≠ 0.'});
    return {title:'Equivalent linear equations',summary:steps[s.step],steps,ledger,result:{kind,solution,leftA:LA,leftB:LB,rightA:RA,rightB:RB,A,B,parameterRule,trial,selectedTrial,selectedStage:{leftA:v[0],leftB:v[1],rightA:v[2],rightB:v[3]},verification:solution?{left:add(mul(LA,solution),LB),right:add(mul(RA,solution),RB)}:null},graph:g};
  }
  function lines(s){const r=k=>rational(s[k]);let A,B,C,p1,p2;if(s.mode==='points'){p1=[r('x1'),r('y1')];p2=[r('x2'),r('y2')];if(eq(p1[0],p2[0])&&eq(p1[1],p2[1]))throw new RangeError('Two distinct points are required to determine a unique line.');A=sub(p2[1],p1[1]);B=sub(p1[0],p2[0]);C=add(mul(A,p1[0]),mul(B,p1[1]));}else if(s.mode==='point-slope'){const m=r('m');p1=[r('x1'),r('y1')];p2=[add(p1[0],ONE),add(p1[1],m)];A=m;B=neg(ONE);C=sub(mul(m,p1[0]),p1[1]);}else{A=r('A');B=r('B');C=r('C');if(!A.n&&!B.n){const kind=C.n?'empty':'entire-plane',g=graph(),atX=r('atX'),summary=C.n?'The equation 0 = '+text(C)+' is false: no point satisfies it.':'The equation 0 = 0 holds at every point of the plane.';g.lines.push(line('base','Degenerate equation',A,B,C));return {title:'A general equation can fail to define a line',summary,steps:[summary,'There is no unique line, so slope and parallel/perpendicular relationships are undefined.'],ledger:[{label:'Equation',text:'0·x +0·y = '+text(C)},{label:'Solution set',text:C.n?'No points':'The entire plane'},{label:'Slope and line relationships',text:'Undefined: the equation does not define a unique line'},{label:'At x='+text(atX),text:C.n?'No y satisfies the equation':'Every y satisfies the equation'}],result:{A,B,C,kind,slope:null,rise:null,run:null,p1:null,p2:null,xIntercept:null,yIntercept:null,xInterceptKind:C.n?'none':'all',yInterceptKind:C.n?'none':'all',relationship:{kind:'undefined'},related:null,evaluation:{x:atX,kind:C.n?'none':'all',y:null}},graph:g};}p1=B.n?[Z,div(C,B)]:[div(C,A),Z];p2=B.n?[ONE,div(sub(C,A),B)]:[div(C,A),ONE];}
    const slope=B.n?neg(div(A,B)):null,kind=B.n?(A.n?'oblique':'horizontal'):'vertical',rise=sub(p2[1],p1[1]),run=sub(p2[0],p1[0]),g=graph();g.lines.push(line('base','Original line',A,B,C));g.points.push(point('p1','P₁',...p1),point('p2','P₂',...p2));g.segments.push({id:'run',label:'run = '+text(run),from:p1,to:[p2[0],p1[1]]},{id:'rise',label:'rise = '+text(rise),from:[p2[0],p1[1]],to:p2});
    let relationship={kind:'none'},other=null;
    if(s.relation!=='none'){const p=[r('throughX'),r('throughY')],a=s.relation==='parallel'?A:B,b=s.relation==='parallel'?B:neg(A),c=add(mul(a,p[0]),mul(b,p[1]));other={A:a,B:b,C:c};const coincident=s.relation==='parallel'&&eq(C,c);relationship={kind:coincident?'coincident':s.relation,through:p};g.lines.push(line('related',coincident?'Coincident line':s.relation+' line',a,b,c,'secondary'));g.points.push(point('through','Through point',...p));if(s.relation==='perpendicular'){const determinant=sub(mul(A,b),mul(a,B));const x=div(sub(mul(C,b),mul(c,B)),determinant),y=div(sub(mul(A,c),mul(a,C)),determinant);relationship.intersection={x,y};g.points.push(point('intersection','Perpendicular intersection',x,y));}}
    const xKind=A.n?'one':C.n?'none':'all',yKind=B.n?'one':C.n?'none':'all',xi=A.n?div(C,A):null,yi=B.n?div(C,B):null;
    const lineText=(a,b,c)=>text(a)+'·x + ('+text(b)+')·y = '+text(c),summary=kind==='vertical'?'Vertical line x = '+text(div(C,A))+': slope is undefined.':(kind==='horizontal'?'Horizontal line. ':'')+'Slope = '+text(slope)+'.';
    if(xKind==='one')g.points.push(point('x-intercept','x-intercept',xi,Z));if(yKind==='one')g.points.push(point('y-intercept','y-intercept',Z,yi));
    const atX=r('atX'),evaluation=B.n?{x:atX,kind:'one',y:div(sub(C,mul(A,atX)),B)}:{x:atX,kind:eq(mul(A,atX),C)?'all':'none',y:null};
    if(evaluation.kind==='one')g.points.push(point('evaluation','At x='+text(atX),atX,evaluation.y));
    const ledger=[{label:'Line equation',text:lineText(A,B,C)},{label:'Evaluate at x='+text(atX),text:evaluation.kind==='one'?'y = '+text(evaluation.y):evaluation.kind==='all'?'Every y lies on this vertical line at that x':'No point on this vertical line has that x'},{label:'Slope',text:slope===null?'Undefined (vertical line)':text(slope)},{label:'Rise and run',text:'rise = '+text(rise)+', run = '+text(run)},{label:'x-axis intersection',text:xKind==='one'?'('+text(xi)+',0)':xKind==='all'?'Every point on the x-axis':'No x-axis intersection'},{label:'y-axis intersection',text:yKind==='one'?'(0,'+text(yi)+')':yKind==='all'?'Every point on the y-axis':'No y-axis intersection'}];
    if(other)ledger.push({label:'Related line',text:lineText(other.A,other.B,other.C)+'; '+relationship.kind+'.'});
    return {title:'Lines, direction and relationships',summary,steps:['A line satisfies A·x + B·y = C at every plotted point.','For distinct points, run = x₂ − x₁ and rise = y₂ − y₁. Divide rise by run only when run is nonzero.','Parallel lines have proportional normals; perpendicular lines have normal vectors with zero dot product.'],ledger,result:{A,B,C,kind,slope,rise,run,p1,p2,xIntercept:xi,yIntercept:yi,xInterceptKind:xKind,yInterceptKind:yKind,relationship,related:other,evaluation},graph:g};
  }
  function sqrtInteger(n){if(n<0n)return null;let x=BigInt(Math.floor(Math.sqrt(Number(n))));while((x+1n)*(x+1n)<=n)x++;while(x*x>n)x--;return x*x===n?x:null;}
  function sqrtRational(r){if(r.n<0)return null;const a=sqrtInteger(BigInt(r.n)),b=sqrtInteger(BigInt(r.d));return a===null||b===null?null:rat(a,b);}
  function quadratics(s){const a=rational(s.a),b=rational(s.b),c=rational(s.c),coefficients=trim([c,b,a]),g=graph();g.curves.push(curve('polynomial','f(x)',coefficients));g.points.push(point('intercept','y-intercept',Z,c));let result,steps,summary,ledger;
    if(!a.n){const kind=b.n?'linear':c.n?'nonzero-constant':'zero-polynomial',root=b.n?neg(div(c,b)):null;result={kind,degree:b.n?1:c.n?0:null,coefficients,discriminant:null,rootSum:null,rootProduct:null,vertex:null,completedSquare:null,roots:root?[{value:root,exact:true,multiplicity:1,expression:text(root)}]:[],realRootCount:root?1:c.n?0:'all'};if(root)g.points.push(point('root','Root '+text(root),root,Z));summary=b.n?'The quadratic coefficient is zero: this is a linear equation with root '+text(root)+'.':c.n?'A nonzero constant has no roots.':'The zero polynomial vanishes for every real x.';steps=[summary];ledger=[{label:'Polynomial',text:polyText(coefficients)},{label:'Classification',text:summary}];}
    else{const D=sub(mul(b,b),mul(FOUR,mul(a,c))),h=neg(div(b,mul(TWO,a))),k=sub(c,div(mul(b,b),mul(FOUR,a))),roots=[],radical=sqrtRational(D);let kind,rootText;
      if(D.n<0){kind='no-real-roots';rootText='No real roots: discriminant '+text(D)+' <0.';}
      else if(!D.n){kind='repeated-real-root';roots.push({value:h,exact:true,multiplicity:2,expression:text(h)});rootText='Repeated real root x = '+text(h)+'.';}
      else if(radical){kind='two-real-roots';for(const sign of [-1,1]){const v=div(add(neg(b),sign<0?neg(radical):radical),mul(TWO,a));roots.push({value:v,exact:true,multiplicity:1,expression:text(v)});}roots.sort((x,y)=>number(x.value)-number(y.value));rootText='Real roots: '+roots.map(r=>r.expression).join(' and ')+'.';}
      else{kind='two-real-roots';const av=number(a),bv=number(b),cv=number(c),sd=Math.sqrt(number(D)),q=-.5*(bv+(bv>=0?sd:-sd)),values=[q/av,cv/q].sort((x,y)=>x-y),den=mul(TWO,a),expressions=['('+text(neg(b))+' − √('+text(D)+')) / ('+text(den)+')','('+text(neg(b))+' + √('+text(D)+')) / ('+text(den)+')'];if(a.n<0)expressions.reverse();values.forEach((v,i)=>roots.push({value:v,exact:false,multiplicity:1,expression:expressions[i],approximation:v}));rootText='Exact real roots: '+roots.map(r=>r.expression).join(' and ')+'. Decimal graph coordinates are approximations.';}
      const completedSquare={a,h,k};result={kind,degree:2,coefficients,discriminant:D,rootSum:neg(div(b,a)),rootProduct:div(c,a),vertex:{x:h,y:k},completedSquare,extremum:a.n>0?'minimum':'maximum',roots,realRootCount:roots.length};summary=rootText;g.points.push(point('vertex','Vertex ('+text(h)+','+text(k)+')',h,k));roots.forEach((r,i)=>g.points.push(point('root'+i,'Root '+r.expression,r.value,Z,r.exact)));g.lines.push(line('symmetry','Axis x='+text(h),ONE,Z,h,'construction'));
      const square=text(a)+'·(x − ('+text(h)+'))² + ('+text(k)+')';steps=['Start with '+polyText(coefficients)+' =0.','Complete the square: '+square+' =0.','The discriminant is b² −4ac = '+text(D)+'.',rootText];ledger=[{label:'Standard form',text:polyText(coefficients)},{label:'Completed square',text:square},{label:'Vertex',text:'('+text(h)+', '+text(k)+'); '+result.extremum},{label:'Discriminant',text:text(D)},{label:'Real roots',text:rootText},{label:'Sum of both algebraic roots',text:'−b/a = '+text(result.rootSum)+'. Count roots with multiplicity; when the discriminant is negative, these are the two non-real roots.'},{label:'Product of both algebraic roots',text:'c/a = '+text(result.rootProduct)+'. Count roots with multiplicity. These identities do not assert that the roots are real.'}];
    }return {title:'Quadratic forms and roots',summary,steps,ledger,result,graph:g};
  }
  function ends(p){p=trim(p);if(zeroPoly(p))return {degree:null,left:'zero',right:'zero',leading:Z};const degree=p.length-1,sign=p.at(-1).n>0?'up':'down';return {degree,left:degree===0?'constant':degree%2?(sign==='up'?'down':'up'):sign,right:degree===0?'constant':sign,leading:p.at(-1)};}
  function polynomials(s){const left=polynomial(s.left),right=polynomial(s.right),leading=rational(s.leading),g=graph(),result={mode:s.mode,inputLeft:left,inputRight:right,roots:null,factorization:null,remainderTheorem:null,terms:[]};let coefficients,summary,steps=[];
    if(s.mode==='factors'){if(!leading.n)throw new RangeError('Factored mode requires a nonzero leading coefficient.');const roots=s.roots.map(rational);coefficients=[leading];for(const r of roots)coefficients=polyMultiply(coefficients,[neg(r),ONE]);const unique=[];for(const r of roots){const old=unique.find(v=>eq(v.value,r));if(old)old.multiplicity++;else unique.push({value:r,multiplicity:1,exact:true,expression:text(r)});}unique.sort((a,b)=>number(a.value)-number(b.value));result.roots=unique;result.factorization={leading,roots};summary='Expand '+text(leading)+roots.map(r=>'·(x − ('+text(r)+'))').join('')+' = '+polyText(coefficients)+'.';steps=[summary,...unique.map(r=>'Root '+text(r.value)+' has multiplicity '+r.multiplicity+': '+(r.multiplicity%2?'crosses':'touches and turns at')+' the axis.')];unique.forEach((r,i)=>g.points.push(point('root'+i,'Root '+text(r.value)+' (multiplicity '+r.multiplicity+')',r.value,Z)));}
    else if(s.mode==='factor-quadratic'){
      if(left.length>3)throw new RangeError('Coefficient-driven factoring is implemented only through degree 2.');
      const q=quadratics({a:text(left[2]||Z),b:text(left[1]||Z),c:text(left[0])});coefficients=left;result.roots=q.result.roots;result.factoring=q.result;
      const possible=q.result.realRootCount!==0&&q.result.realRootCount!=='all',factorText=possible?text(left.at(-1))+q.result.roots.map(r=>'·(x − ('+r.expression+'))'+(r.multiplicity>1?'^'+r.multiplicity:'')).join(''):q.result.realRootCount==='all'?'Zero polynomial: no unique finite list of linear factors.':q.result.degree===0?'A nonzero constant has no linear factors.':'No real linear factorization: the discriminant is negative.';
      result.factorization={kind:'derived-from-coefficients',realLinearFactors:possible,expression:factorText};summary=possible?polyText(left)+' = '+factorText+'.':factorText;steps=[...q.steps,summary];g.points.push(...q.graph.points.filter(p=>p.id!=='intercept'));g.lines.push(...q.graph.lines);
    }
    else if(s.mode==='add'){coefficients=polyAdd(left,right);summary='('+polyText(left)+') + ('+polyText(right)+') = '+polyText(coefficients)+'.';steps=['Align coefficients with equal powers of x.',summary];}
    else if(s.mode==='multiply'){coefficients=polyMultiply(left,right);left.forEach((a,i)=>right.forEach((b,j)=>{if(a.n&&b.n)result.terms.push({leftPower:i,rightPower:j,power:i+j,coefficient:mul(a,b)});}));summary='('+polyText(left)+')·('+polyText(right)+') = '+polyText(coefficients)+'.';steps=['Multiply every term of the first polynomial by every term of the second.', 'Collect products with the same total power.',summary];}
    else{const division=polyDivide(left,right);Object.assign(result,division);coefficients=division.quotient;summary='('+polyText(left)+') = ('+polyText(right)+')·('+polyText(division.quotient)+') + ('+polyText(division.remainder)+').';steps=division.steps.map((r,i)=>'Step '+(i+1)+': add '+polyText(Array.from({length:r.power},()=>Z).concat([r.coefficient]))+' to the quotient; the remaining polynomial is '+polyText(r.remainder)+'.');if(!steps.length)steps.push(zeroPoly(left)?'The dividend is zero: quotient and remainder are both zero.':'The dividend degree is smaller than the divisor degree: quotient 0, remainder equal to the dividend.');steps.push(summary);g.curves.push(curve('dividend','Dividend',left,'secondary'),curve('divisor','Divisor',right,'construction'));
      if(right.length===2){const root=neg(div(right[0],right[1])),value=evaluateExact(left,root),divisorValue=evaluateExact(right,root),remainder=division.remainder[0];if(division.remainder.length!==1||divisorValue.n||!eq(value,remainder))throw Error('The linear-divisor remainder theorem identity failed.');result.remainderTheorem={root,polynomialValue:value,divisorValue,remainder,equality:true};g.points.push(point('remainder-dividend','P(r) equals the remainder',root,value),point('remainder-divisor','The divisor vanishes at r',root,Z));g.segments.push({id:'remainder-value',label:'Remainder '+text(remainder),from:[root,Z],to:[root,value]});steps.push('The linear divisor vanishes at r = '+text(root)+'. Substituting into P = divisor·quotient + remainder gives P('+text(root)+') = '+text(value)+', the constant remainder.');}
    }
    const behavior=ends(coefficients);Object.assign(result,{coefficients,degree:behavior.degree,leadingCoefficient:behavior.leading,endBehavior:behavior});g.curves.unshift(curve('polynomial',s.mode==='divide'?'Quotient':'Result polynomial',coefficients));g.points.push(point('intercept','Result y-intercept',Z,coefficients[0]));
    const ledger=[{label:s.mode==='divide'?'Quotient':'Result polynomial',text:polyText(coefficients)},{label:'Degree',text:behavior.degree===null?'The zero polynomial has no defined degree':String(behavior.degree)},{label:'End behaviour',text:behavior.degree===null?'Zero at every x':behavior.degree===0?'A constant value at every x':'Left end '+behavior.left+'; right end '+behavior.right}];
    if(s.mode==='factors')ledger.push({label:'Provided factorization',text:text(leading)+result.factorization.roots.map(r=>'·(x − ('+text(r)+'))').join('')},{label:'All roots for this factored input',text:result.roots.map(r=>text(r.value)+' (multiplicity '+r.multiplicity+')').join('; ')});
    else if(s.mode==='factor-quadratic')ledger.push({label:'Derived factorization',text:result.factorization.expression},{label:'Factoring scope',text:'This coefficient-driven factorization covers degree 0, 1 and 2 only. Irrational factors retain exact radical expressions; graph coordinates may be approximate.'});
    else if(s.mode!=='divide')ledger.push({label:'Root scope',text:'General roots are not inferred by this polynomial-operation model.'});
    if(s.mode==='divide'){const rd=zeroPoly(result.remainder)?null:result.remainder.length-1,dd=right.length-1;result.remainderDegree=rd;result.divisorDegree=dd;if(result.remainderTheorem){const t=result.remainderTheorem;ledger.push({label:'Zero of the linear divisor',text:'r = −d₀/d₁ = '+text(t.root)+'; the divisor evaluates to 0.'},{label:'Remainder theorem',text:'P('+text(t.root)+') = '+text(t.polynomialValue)+' = R. The product of divisor and quotient is zero at this r.'});}ledger.push({label:'Remainder',text:polyText(result.remainder)},{label:'Exact division identity',text:summary},{label:'Remainder degree condition',text:rd===null?'The remainder is zero.':'degree(R) = '+rd+' < degree(divisor) = '+dd});}
    return {title:'Polynomial operations and structure',summary,steps,ledger,result,graph:g};
  }
  function model(id,raw={}){const state=accept(id,raw),build=id==='math.3.linear'?linear:id==='math.3.slope'?lines:id==='math.3.quadratics'?quadratics:polynomials;return frozen({lessonId:id,kind:id.split('.').at(-1),state,...build(state),exact:true});}
  const catalog={};
  function P(id,label,state,quizIndexes=[],plate=false,context=''){return {id,label,state,quizIndexes,plate,context};}
  catalog['math.3.linear']=[
    P('plate','The displayed balance equation',{a:2,b:6,c:1,d:10},[1],true),
    P('subtract-seven','Undo addition and multiplication',{a:3,b:-7,c:0,d:11},[0]),
    P('bracket','Distribute a complete bracket',{leftScale:2,a:1,b:3,c:1,d:10},[1]),
    P('taxi','Taxi: $3 plus $2 per mile',{a:2,b:3,c:0,d:17},[2],false,'x is miles; the $3 fixed charge and $2-per-mile rate are different quantities.'),
    P('thirds','Fractional coefficient',{a:'1/3',b:4,c:0,d:10},[3]),
    P('phone','Phone plan: fixed fee',{a:1,b:20,c:0,d:35},[4],false,'The call charge is 200×$0.10=$20. x is the fixed monthly fee.'),
    P('both-sides','Check both sides at a proposed x',{a:5,b:2,c:3,d:14,testX:6},[5]),
    P('five-brackets','Distribute, then collect terms',{leftScale:5,a:1,b:-2,c:3,d:6},[6]),
    P('no-solution','Equal x coefficients, unequal constants',{a:4,b:9,c:4,d:2},[7]),
    P('temperature','Celsius C and Fahrenheit F: x=F, d=C',{leftScale:'5/9',a:1,b:-32,c:0,d:20},[8],false,'The general parameter rule gives F=(9/5)C+32 for every C because the nonzero coefficient is 5/9; the chosen C=20 also gives a numerical example.'),
    P('whole-side','Divide the whole side',{a:3,b:5,c:0,d:20},[9]),
    P('identity','An identity: every real number',{leftScale:2,a:1,b:3,c:2,d:6},[]),
    P('negative','Negative coefficient and rational solution',{a:-3,b:2,c:1,d:7},[])
  ];
  catalog['math.3.slope']=[
    P('plate','The displayed descending line',{mode:'points',x1:1,y1:3,x2:3,y2:-1},[1],true),
    P('two-points','Slope from two points',{mode:'points',x1:1,y1:2,x2:4,y2:11},[0]),
    P('point-slope','Point and slope',{mode:'point-slope',m:4,x1:2,y1:3,atX:5},[2]),
    P('horizontal','Horizontal line',{mode:'points',x1:2,y1:7,x2:6,y2:7},[3]),
    P('perpendicular','Perpendicular through (0,1)',{mode:'general',A:-3,B:1,C:-4,relation:'perpendicular',throughX:0,throughY:1},[4]),
    P('general','General form2x+3y=12',{mode:'general',A:2,B:3,C:12},[5]),
    P('intercept','Find the y-intercept',{mode:'points',x1:-2,y1:1,x2:2,y2:9},[6]),
    P('slope-intercept','y=3x−4',{mode:'general',A:-3,B:1,C:-4},[7]),
    P('parallel','Parallel through (0,−7)',{mode:'general',A:-5,B:1,C:1,relation:'parallel',throughX:0,throughY:-7},[8]),
    P('tank','Tank volume V=200−8t',{mode:'general',A:8,B:1,C:200},[9],false,'Read x=t in minutes and y=V in litres. The rate is −8 L/min. The physical draining model applies only for 0≤t≤25, when the volume is nonnegative; the mathematical line extends beyond that interval.'),
    P('vertical','A vertical line',{mode:'points',x1:2,y1:-2,x2:2,y2:3},[]),
    P('axis-perpendicular','Vertical and horizontal perpendicular lines',{mode:'general',A:1,B:0,C:2,relation:'perpendicular',throughX:0,throughY:3},[]),
    P('entire-plane','Degenerate equation: every point',{mode:'general',A:0,B:0,C:0},[]),
    P('empty-equation','Degenerate equation: no points',{mode:'general',A:0,B:0,C:1},[]),
    P('coincident','A parallel through-point gives the same line',{mode:'general',A:-2,B:1,C:1,relation:'parallel',throughX:1,throughY:3},[])
  ];
  catalog['math.3.quadratics']=[
    P('plate','The displayed quadratic x²−5x+6',{a:1,b:-5,c:6},[0],true),
    P('root-sum','Root sum and product',{a:1,b:-7,c:10},[1]),
    P('no-real','Negative discriminant',{a:1,b:2,c:5},[2]),
    P('vertex-three','Vertex at x=3',{a:1,b:-6,c:5},[3]),
    P('repeated-plus','Repeated root: k=6',{a:1,b:6,c:9},[4]),
    P('repeated-minus','Repeated root: k=−6',{a:1,b:-6,c:9},[4]),
    P('projectile','Ball height h(t)=−5t²+30t',{a:-5,b:30,c:0},[5],false,'x=t in seconds and y=h in metres. The flight interval is 0≤t≤6. The root t = 0 is launch; t = 6 is return to the ground. The vertex is the highest point.'),
    P('minimum-four','Completed square with positive minimum',{a:1,b:-8,c:20},[6]),
    P('signed-factors','Roots−5 and2',{a:1,b:3,c:-10},[7]),
    P('complete-square','Complete the square',{a:1,b:6,c:1},[8]),
    P('rectangle','Rectangle width and area',{a:1,b:3,c:-40},[9],false,'x is width in metres and x+3 is length. The area equation is x(x+3)=40. Only the positive root is a physical width.'),
    P('irrational','Irrational real roots',{a:1,b:0,c:-2},[]),
    P('linear-degenerate','Zero quadratic coefficient',{a:0,b:2,c:-6},[]),
    P('zero-polynomial','Zero polynomial',{a:0,b:0,c:0},[]),
    P('nonzero-constant','Nonzero constant',{a:0,b:0,c:3},[])
  ];
  catalog['math.3.polynomials']=[
    P('plate','The displayed cubic with roots1,2,3',{mode:'factors',roots:[1,2,3],leading:1},[4],true),
    P('binomial-product','Expand(x+3)(x−2)',{mode:'multiply',left:[3,1],right:[-2,1]},[0]),
    P('degree-five','Degree-five product',{mode:'multiply',left:[1,0,0,1],right:[0,-1,1]},[1]),
    P('difference-squares','Factor x²−9 from its coefficients',{mode:'factor-quadratic',left:[-9,0,1]},[2]),
    P('remainder','Divide x³−2x+5 by x−2',{mode:'divide',left:[5,-2,0,1],right:[-2,1]},[3]),
    P('quartic-ends','Positive quartic end behaviour',{mode:'factors',roots:[-2,-1,1,2],leading:1},[5]),
    P('collect-powers','Collect the x² terms',{mode:'multiply',left:[4,1],right:[2,-3,1]},[6]),
    P('factor-seven','Factor x²+7x+12 from its coefficients',{mode:'factor-quadratic',left:[12,7,1]},[7]),
    P('root-five','A factor x−5',{mode:'factors',roots:[5,-1],leading:1},[8]),
    P('negative-cubic','Negative cubic end behaviour',{mode:'factors',roots:[-1,0,1],leading:-1},[9]),
    P('multiplicity','Touching and crossing roots',{mode:'factors',roots:[-1,-1,2,2],leading:1},[]),
    P('add','Add coefficients of equal powers',{mode:'add',left:[1,2,3],right:[4,-2,1]},[]),
    P('zero-dividend','Zero dividend',{mode:'divide',left:[0],right:[1,1]},[]),
    P('constant-divisor','A nonzero constant divisor',{mode:'divide',left:[1,2,3],right:[2]},[])
  ];
  function presets(id){defaults(id);return frozen(catalog[id].map(p=>({...clone(p),state:accept(id,p.state)})));}
  const api=Object.freeze({lessonIds:Object.freeze(IDS),bounds:Object.freeze({inputMagnitude:1000,inputDenominator:1000,inputPolynomialDegree:4,resultPolynomialDegree:8,factoredDegree:4,intermediateInteger:Number.MAX_SAFE_INTEGER,graphX:1e6}),model,defaults,presets,rational,number,text,polynomialText:(p,v)=>polyText(polynomial(p),v),evaluate,evaluateExact,derivative:p=>{const a=polynomial(p);return a.length===1?[Z]:a.slice(1).map((v,i)=>mul(v,rat(BigInt(i+1))));},add:(a,b)=>add(rational(a),rational(b)),subtract:(a,b)=>sub(rational(a),rational(b)),multiply:(a,b)=>mul(rational(a),rational(b)),divide:(a,b)=>div(rational(a),rational(b)),polynomialAdd:(a,b)=>polyAdd(polynomial(a),polynomial(b)),polynomialMultiply:(a,b)=>polyMultiply(polynomial(a),polynomial(b)),polynomialDivide:(a,b)=>polyDivide(polynomial(a),polynomial(b))});
  if(host)host.PrimerAlgebraFunctionsCore=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window==='undefined'?null:window);
