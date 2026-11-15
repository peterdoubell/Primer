(function(host){
  'use strict';
  const core=host?host.PrimerBaseTenCore:require('./base-ten-core.js');
  const dimensions=[[.2,.2,.2],[2,.2,.2],[2,.2,2],[2,2,2]],places=['Ones','Tens','Hundreds','Thousands'];
  const range=(key,label,min,max,step=1)=>({key,label,min,max,step});
  const choice=(key,label,options)=>({key,label,options:options.map(([value,label])=>({value,label}))});
  function outline(g,center,size,meta={}){
    const p=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]].map(v=>v.map((x,i)=>center[i]+x*size[i]/2));
    for(const[a,b]of[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]])g.line([p[a],p[b]],'#83949a',{...meta});
  }
  function normalized(initial,controls,raw){
    const state={};for(const c of controls){const v=raw[c.key];if(c.options)state[c.key]=c.options.some(o=>o.value===v)?v:initial[c.key];else{const n=(typeof v==='number'||typeof v==='string'&&v.trim())?Number(v):NaN;state[c.key]=Math.round(Math.max(c.min,Math.min(c.max,Number.isFinite(n)?n:initial[c.key])));}}
    return state;
  }
  function placeGeometry(counts,g){
    const boxes=[],colors=[g.colors.coral,g.colors.gold,g.colors.teal,g.colors.blue];
    outline(g,[8,0,-3],dimensions[0],{base_ten_reference:true});g.label([8,.7,-3],'Fixed one-unit cube');
    for(let p=0;p<4;p++){
      const n=counts[p];for(let i=0;i<n;i++){
        const center=p===3?[-5+(i%3)*2.3,1,Math.floor(i/3)*2.3]:p===2?[3,.1+i*.3,0]:p===1?[6,.1+i*.3,0]:[8+(i%5)*.3,.1,Math.floor(i/5)*.3];
        g.box(center,dimensions[p],colors[p],{base_ten_place:p,base_ten_piece:i,base_ten_units:10**p});boxes.push({place:p,piece:i,center,dimensions:dimensions[p],units:10**p});
      }
      if(n){const at=p===3?[-3,3.8,2]:p===2?[3,n*.3+.6,0]:p===1?[6,n*.3+.6,0]:[8,.8,1];g.label(at,n+' '+places[p].toLowerCase());}
    }
    return {boxes,counts,total:counts.reduce((n,c,p)=>n+c*10**p,0),worldVolumePerUnit:.008};
  }
  function placeResult(s,g,lesson){
    const value=s.value,counts=core.digits(value).map(p=>p.digit),original=[...counts];let possible=true,from=null;
    if(s.representation!=='bundled'){
      from={unbundleTen:1,unbundleHundred:2,unbundleThousand:3}[s.representation];possible=counts[from]>0;
      if(possible){counts[from]--;counts[from-1]+=10;}
    }
    const geometry=placeGeometry(counts,g);
    return{readout:'The number is '+value+'. '+counts.map((n,p)=>n+' × '+10**p).reverse().join(' + ')+' = '+value+'. '+(from===null?'These are its usual base-ten digits.':possible?'One '+places[from].toLowerCase().replace(/s$/,'')+' has been exchanged for ten '+places[from-1].toLowerCase()+'. Total value is unchanged.':'There is no '+places[from].toLowerCase().replace(/s$/,'')+' to exchange in the bundled representation.'),note:'Every solid has a calibrated volume in one fixed unit system: a unit cube is 0.2 × 0.2 × 0.2, a ten rod is 2 × 0.2 × 0.2, a hundred slab is 2 × 0.2 × 2, and a thousand cube is 2 × 2 × 2. Their volumes are in the exact ratio 1 : 10 : 100 : 1000. Gray edges mark the reference unit. Separated columns and inspection gaps change position, not value. The controls are independent of the other lesson activities.',legend:places.map((label,i)=>({label,color:[g.colors.coral,g.colors.gold,g.colors.teal,g.colors.blue][i]})),baseTenGeometry:{...geometry,lesson,kind:'place',value,originalCounts:original,exchangePossible:possible}};
  }
  function additionResult(s,g,lesson){
    const a=core.digits(s.a),b=core.digits(s.b),counts=s.phase==='unregrouped'?a.map((p,i)=>p.digit+b[i].digit):core.digits(s.a+s.b).map(p=>p.digit),geometry=placeGeometry(counts,g);
    return{readout:s.a+' + '+s.b+' = '+(s.a+s.b)+'. '+(s.phase==='unregrouped'?'Equal-place pieces from both addends are combined before exchanges.':'Ten-to-one exchanges have produced the usual digits of the sum.')+' '+counts.map((n,p)=>n+' × '+10**p).reverse().join(' + ')+'.',note:'Each colored denomination keeps its fixed physical volume. Exchanging ten unit cubes for one ten rod, or ten ten rods for one hundred slab, preserves total volume and number value. This shows one representation at a time; switching phase does not add a second copy of the total. Columns are separated for inspection. The same unit scale is used for both phases and for every input.',legend:places.map((label,i)=>({label,color:[g.colors.coral,g.colors.gold,g.colors.teal,g.colors.blue][i]})),baseTenGeometry:{...geometry,lesson,kind:'addition',a:s.a,b:s.b,phase:s.phase}};
  }
  const cube=(g,center,color,meta)=>g.box(center,dimensions[0],color,meta);
  function arrayPoint(i,columns,origin=[0,0,0]){return[origin[0]+(i%columns)*.3,origin[1],origin[2]+Math.floor(i/columns)*.3];}
  function counterResult(s,g,lesson){
    const boxes=[],ghosts=[];outline(g,[-1,.1,-1],dimensions[0],{base_ten_reference:true});
    function material(center,role,group,index,color){cube(g,center,color,{base_ten_role:role,base_ten_group:group,base_ten_index:index,base_ten_units:1});boxes.push({center,dimensions:dimensions[0],role,group,index,units:1});}
    let readout,note;
    if(lesson==='math.1.multiplication'){
      const rows=s.turned?s.b:s.a,columns=s.turned?s.a:s.b;
      for(let r=0;r<rows;r++)for(let c=0;c<columns;c++)material([c*.3,.1,r*.3],'array',r,c,r%2?g.colors.coral:g.colors.blue);
      readout=rows+' rows × '+columns+' counters per row = '+(rows*columns)+'. '+(s.turned?'The array has been turned: the two factors exchange roles.':'Every row has the same number of counters.');
      note='Each solid cube represents one counter and has the same fixed volume, 0.008 world-volume units. Row colors identify equal groups. Turning the array exchanges row and column counts without adding or removing material. Zero rows or zero counters per row produce no solid cubes. Gray edges show one reference counter.';
    }else if(lesson==='math.1.subtraction'){
      if(s.meaning==='difference'){
        for(let i=0;i<s.a;i++)material(arrayPoint(i,10,[0,.1,0]),'first',0,i,g.colors.blue);
        for(let i=0;i<s.b;i++)material(arrayPoint(i,10,[4,.1,0]),'second',1,i,g.colors.coral);
        readout='First amount '+s.a+'; second amount '+s.b+'. Their nonnegative gap is '+Math.abs(s.a-s.b)+'. Signed subtraction: '+s.a+' − '+s.b+' = '+(s.a-s.b)+'.';
        note='These are two separate comparison groups. Equal-sized cubes represent equal units; the scene contains both quantities for comparison and does not present their combined count as the subtraction result. Matching equal units leaves the stated gap. The signed equation also indicates which quantity is larger.';
      }else{
        const retained=Math.max(s.a-s.b,0),removed=Math.min(s.a,s.b),shortfall=Math.max(s.b-s.a,0);
        for(let i=0;i<retained;i++)material(arrayPoint(i,10,[0,.1,0]),'retained',0,i,g.colors.blue);
        for(let i=0;i<removed;i++)material(arrayPoint(i,10,[4,.1,0]),'removed',1,i,g.colors.coral);
        for(let i=0;i<shortfall;i++){const center=arrayPoint(i,10,[8,.1,0]);outline(g,center,dimensions[0],{base_ten_shortfall:i});ghosts.push({center,dimensions:dimensions[0],units:1});}
        readout='Start with '+s.a+'. Remove '+removed+' available counters. '+retained+' stay.'+(shortfall?' '+shortfall+' more counters would be needed to remove the requested '+s.b+'. The signed answer is '+(s.a-s.b)+'.':' '+s.a+' − '+s.b+' = '+retained+'.');
        note='Blue solids remain; coral solids have been moved into the removed group. Their combined number is the starting quantity, so removal does not invent or duplicate counters. Gray empty outlines in the shortfall group represent missing counters and contribute no material volume. Negative signed differences describe a shortfall, not negative physical cubes. Every material counter has the same fixed size.';
      }
    }else{
      const m=core.build(lesson,{mode:s.meaning,total:s.total,divisor:s.divisor});
      if(m.status==='undefined')return{readout:m.reason,note:'Zero groups or zero group size do not define a division result. The gray reference unit remains a scale marker, not a counter included in the dividend.',legend:[{label:'Gray outline: reference unit',color:'#83949a'}],baseTenGeometry:{lesson,kind:'division',status:'undefined',boxes:[],ghosts:[],total:0,worldVolumePerUnit:.008}};
      const cols=Math.max(1,Math.min(12,m.groupSize)),depth=Math.max(1,Math.ceil(m.groupSize/cols)),groupColumns=Math.max(1,Math.min(12,Math.ceil(Math.sqrt(m.groupCount)))),groupWidth=cols*.3+.5,groupDepth=depth*.3+.5;
      for(let group=0;group<m.groupCount;group++){
        const origin=[(group%groupColumns)*groupWidth,.1,Math.floor(group/groupColumns)*groupDepth];
        for(let i=0;i<m.groupSize;i++)material(arrayPoint(i,cols,origin),'equal-group',group,i,group%2?g.colors.coral:g.colors.blue);
        outline(g,[origin[0]+(cols-1)*.15,.1,origin[2]+(depth-1)*.15],[cols*.3,.25,depth*.3],{base_ten_group_outline:group});
      }
      const rz=Math.ceil(m.groupCount/groupColumns)*groupDepth+.5;
      for(let i=0;i<m.remainder;i++)material(arrayPoint(i,12,[0,.1,rz]),'remainder',-1,i,g.colors.gold);
      readout=s.total+' ÷ '+s.divisor+' = '+m.quotient+' remainder '+m.remainder+'. '+(s.meaning==='share'?m.groupCount+' equal groups receive '+m.groupSize+' each.':m.groupCount+' complete groups each contain '+m.groupSize+'.')+' Check: '+s.divisor+' × '+m.quotient+' + '+m.remainder+' = '+s.total+'.';
      note='Every solid is one whole counter at the same fixed size. Colors and gray enclosures identify complete equal groups; gold counters are the remainder outside those groups. No counters are discarded or silently split. Empty enclosures may show a requested empty sharing group, but they contain no material. Sharing fixes the number of groups; grouping fixes the number in each group.';
    }
    return{readout,note,legend:[{label:'First amount / retained / alternating groups',color:g.colors.blue},{label:'Second amount / removed / alternating groups',color:g.colors.coral},{label:'Division remainder',color:g.colors.gold},{label:'Gray outlines: groups, reference or stated shortfall',color:'#83949a'}],baseTenGeometry:{lesson,kind:lesson.split('.').at(-1),boxes,ghosts,total:boxes.length,worldVolumePerUnit:.008}};
  }
  const specifications={
    'math.1.place-value':{title:'Calibrated base-ten place values',initial:{value:47,representation:'bundled'},controls:[range('value','Whole number',0,9999),choice('representation','Representation',[['bundled','Usual digits'],['unbundleTen','Exchange one ten for ten ones'],['unbundleHundred','Exchange one hundred for ten tens'],['unbundleThousand','Exchange one thousand for ten hundreds']])]},
    'math.1.addition':{title:'Addition with fixed-volume regrouping',initial:{a:8,b:5,phase:'unregrouped'},controls:[range('a','First addend',0,999),range('b','Second addend',0,999),choice('phase','Exchange phase',[['unregrouped','Combine equal places'],['regrouped','Exchange to usual digits']])]},
    'math.1.subtraction':{title:'Take away and compare equal units',initial:{a:9,b:4,meaning:'takeAway'},controls:[range('a','First amount',0,100),range('b','Second amount',0,100),choice('meaning','Meaning',[['takeAway','Take away'],['difference','Compare quantities']])]},
    'math.1.multiplication':{title:'Equal arrays through twelve by twelve',initial:{a:4,b:3,turned:'no'},controls:[range('a','Rows before turning',0,12),range('b','Counters per row before turning',0,12),choice('turned','Array orientation',[['no','Original'],['yes','Turned']])]},
    'math.1.division':{title:'Equal sharing, grouping and remainders',initial:{total:12,divisor:3,meaning:'share'},controls:[range('total','Total whole counters',0,144),range('divisor','Number of groups / group size',0,12),choice('meaning','Meaning',[['share','Share into this many groups'],['group','Make groups of this size']])]},
  };
  const families={};for(const[lesson,spec]of Object.entries(specifications))families[lesson]={...spec,normalize:raw=>normalized(spec.initial,spec.controls,raw),build(s,g){if(lesson==='math.1.place-value')return placeResult(s,g,lesson);if(lesson==='math.1.addition')return additionResult(s,g,lesson);return counterResult({...s,turned:s.turned==='yes'},g,lesson);},camera:{yaw:-28,pitch:21}};
  if(host)host.PrimerBaseTenSpatialFamilies=families;if(typeof module!=='undefined'&&module.exports)module.exports=families;
})(typeof window==='undefined'?null:window);
