(function(root){
  'use strict';
  const children=['Ari','Bo','Cleo'],trees=['Oak','Pine','Elm'];
  function evaluate(mask){
    if(!Number.isInteger(mask)||mask<0||mask>511)throw new RangeError('Expected a nine-bit relation');
    const rows=children.map((_,c)=>trees.map((_,t)=>Boolean(mask&(1<<(3*c+t)))));
    const witnesses=rows.map(row=>row.flatMap((yes,t)=>yes?[t]:[]));
    const shared=trees.flatMap((_,t)=>rows.every(row=>row[t])?[t]:[]);
    return {rows,witnesses,shared,each:witnesses.every(row=>row.length>0),one:shared.length>0,missing:children.flatMap((_,c)=>witnesses[c].length?[]:[c])};
  }
  const api={children,trees,evaluate};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.ScopeStudy=api;
})(typeof globalThis!=='undefined'?globalThis:this);
