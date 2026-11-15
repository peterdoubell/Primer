(function(host){
  'use strict';
  const lessons={
    'math.1.place-value':['place','exchange'],
    'math.1.addition':['add'],
    'math.1.subtraction':['takeAway','difference'],
    'math.1.multiplication':['multiply'],
    'math.1.division':['share','group'],
  };
  const initial={mode:'place',value:'47',hundreds:'0',tens:'4',ones:'7',a:'8',b:'5',total:'12',divisor:'3',from:'tens',direction:'unbundle'};
  function integer(raw,lo,hi,label){
    if(!['string','number'].includes(typeof raw)||!/^\d{1,6}$/.test(String(raw)))throw new RangeError(label+' must be a whole number.');
    const n=Number(raw);if(n<lo||n>hi)throw new RangeError(label+' must be between '+lo+' and '+hi+'.');return n;
  }
  function defaults(lesson,mode){
    if(!Object.hasOwn(lessons,lesson))throw new RangeError('Unknown base-ten lesson.');
    mode=mode===undefined?lessons[lesson][0]:mode;if(!lessons[lesson].includes(mode))throw new RangeError('This investigation belongs to another lesson.');
    return {...initial,mode,...(mode==='takeAway'||mode==='difference'?{a:'9',b:'4'}:mode==='multiply'?{a:'4',b:'3'}:{})};
  }
  const digits=n=>[0,1,2,3].map(power=>({power,unit:10**power,digit:Math.floor(n/10**power)%10,contribution:(Math.floor(n/10**power)%10)*10**power}));
  function build(lesson,raw={}){
    if(!raw||typeof raw!=='object'||Array.isArray(raw))throw new TypeError('Supply a base-ten state object.');
    for(const key of Object.keys(raw))if(!Object.hasOwn(initial,key)||!['string','number'].includes(typeof raw[key]))throw new RangeError('Unknown or invalid base-ten setting: '+key);
    const state={...defaults(lesson,raw.mode),...raw},m={lesson,state,status:'defined',steps:[]},mode=state.mode;
    const take=(key,lo,hi,label)=>integer(state[key],lo,hi,label);
    if(mode==='place'){
      const value=take('value',0,9999,'Number');Object.assign(m,{value,places:digits(value),expanded:digits(value).filter(d=>d.digit).map(d=>d.contribution),note:'Position determines a digit’s value. Zero holds an empty place. This activity covers whole numbers from 0 to 9999.'});
    }else if(mode==='exchange'){
      const before={hundreds:take('hundreds',0,2,'Hundreds'),tens:take('tens',0,20,'Tens'),ones:take('ones',0,200,'Ones')},units={hundreds:100,tens:10,ones:1},from=state.from,direction=state.direction;
      if(!['hundreds','tens'].includes(from)||!['unbundle','bundle'].includes(direction))throw new RangeError('Choose hundreds or tens and an exchange direction.');
      if(before.hundreds*100+before.tens*10+before.ones>200)throw new RangeError('Exchange up to 200 unit values at a time.');
      const lower=from==='hundreds'?'tens':'ones',after={...before},possible=direction==='unbundle'?before[from]>=1:before[lower]>=10;
      if(possible){if(direction==='unbundle'){after[from]--;after[lower]+=10;}else{after[lower]-=10;after[from]++;}}
      const value=Object.keys(units).reduce((n,k)=>n+before[k]*units[k],0);Object.assign(m,{before,after,value,possible,from,lower,direction,note:possible?'The exchange changes the number of pieces, but preserves their total value. Each higher-place piece equals ten lower-place pieces.':'There are not enough pieces for that exchange. The represented value is unchanged.'});
    }else if(mode==='add'){
      const a=take('a',0,999,'First addend'),b=take('b',0,999,'Second addend'),columns=[];let carry=0;
      for(let power=0;power<3;power++){const A=Math.floor(a/10**power)%10,B=Math.floor(b/10**power)%10,sum=A+B+carry,next=Math.floor(sum/10);columns.push({power,unit:10**power,aDigit:A,bDigit:B,carryIn:carry,rawSum:sum,resultDigit:sum%10,carryOut:next});carry=next;}
      if(carry)columns.push({power:3,unit:1000,aDigit:0,bDigit:0,carryIn:carry,rawSum:carry,resultDigit:carry,carryOut:0});
      Object.assign(m,{a,b,result:a+b,places:digits(a+b),columns,note:'Add equal places. Exchanging ten ones for one ten, or ten tens for one hundred, preserves the total. Swapping addends preserves their sum.'});
    }else if(mode==='takeAway'||mode==='difference'){
      const a=take('a',0,999,'First amount'),b=take('b',0,999,'Second amount'),columns=[];let borrow=0;const high=Math.max(a,b),low=Math.min(a,b);
      for(let power=0;power<3;power++){const A=Math.floor(high/10**power)%10,B=Math.floor(low/10**power)%10;let result=A-borrow-B;const next=result<0?1:0;if(next)result+=10;columns.push({power,unit:10**power,highDigit:A,lowDigit:B,borrowIn:borrow,borrowOut:next,resultDigit:result});borrow=next;}
      if(borrow)throw Error('Magnitude subtraction has an unresolved borrow.');
      Object.assign(m,{a,b,result:a-b,magnitude:high-low,high,low,columns,places:digits(high-low),canTakeAway:b<=a,retained:Math.max(a-b,0),removed:Math.min(a,b),shortfall:Math.max(b-a,0),note:mode==='takeAway'?(b<=a?'Removed amount plus retained amount equals the starting amount. Regrouping lends ten smaller units from one larger unit.':'There are not enough objects to remove that many. The shortfall is shown separately; the signed subtraction is negative. Negative numbers are developed in the later lesson.'):'Compare the two quantities by matching equal units. Their nonnegative gap is the magnitude of the difference; the equation A − B also keeps its sign.'});
    }else if(mode==='multiply'){
      const a=take('a',0,12,'Rows'),b=take('b',0,12,'Counters per row');Object.assign(m,{a,b,result:a*b,rows:a,columns:b,swappedRows:b,swappedColumns:a,repeatedAddends:Array(a).fill(b),note:'Every row has the same number of counters. Turning the array exchanges rows and columns while preserving the product. Zero rows or zero counters per row give zero counters.'});
    }else{
      const total=take('total',0,144,'Total counters'),divisor=take('divisor',0,12,mode==='share'?'Number of groups':'Counters in each group');
      if(!divisor){Object.assign(m,{status:'undefined',total,divisor,reason:total?'A positive total cannot be divided into zero groups or groups of zero.':'Zero divided by zero does not determine a unique quotient.'});return m;}
      const quotient=Math.floor(total/divisor),remainder=total%divisor;let x=total,y=divisor;while(y)[x,y]=[y,x%y];const numerator=total/x,denominator=divisor/x;Object.assign(m,{total,divisor,quotient,remainder,exactQuotient:{numerator,denominator,text:String(numerator)+(denominator===1?'':'/'+denominator)},groupCount:mode==='share'?divisor:quotient,groupSize:mode==='share'?quotient:divisor,check:divisor*quotient+remainder,note:mode==='share'?'Sharing asks how many counters each of the stated groups receives. Whole counters leave a remainder; none are discarded or silently split. Multiplication checks the equal shares plus the remainder.':'Grouping asks how many complete groups of the stated size can be made. Whole counters leave a remainder, smaller than the group size. Multiplication checks complete groups plus the remainder.'});
    }
    return m;
  }
  const api=Object.freeze({lessons,defaults,build,digits});if(host)host.PrimerBaseTenCore=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window==='undefined'?null:window);
