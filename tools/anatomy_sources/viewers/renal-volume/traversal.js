'use strict';
// Independent CPU reference for voxel-cell traversal, including path lengths.
function traverseCells(origin,direction,dims,extent){
  let near=-Infinity,far=Infinity;
  for(let a=0;a<3;a++){
    if(direction[a]===0){if(Math.abs(origin[a])>extent[a]/2)return [];continue;}
    const p=(-extent[a]/2-origin[a])/direction[a],q=(extent[a]/2-origin[a])/direction[a];
    near=Math.max(near,Math.min(p,q));far=Math.min(far,Math.max(p,q));
  }
  let t=Math.max(near,0);if(!(far>t))return [];
  const size=extent.map((v,a)=>v/dims[a]);
  const cell=origin.map((v,a)=>Math.max(0,Math.min(dims[a]-1,Math.floor((v+direction[a]*t+extent[a]/2)/size[a]))));
  const step=direction.map(Math.sign);
  const next=cell.map((v,a)=>step[a]===0?Infinity:(-extent[a]/2+(v+(step[a]>0?1:0))*size[a]-origin[a])/direction[a]);
  const delta=size.map((v,a)=>step[a]===0?Infinity:Math.abs(v/direction[a]));const rows=[];
  for(let count=0;count<dims.reduce((a,b)=>a+b,0)+3;count++){
    if(cell.some((v,a)=>v<0||v>=dims[a])||t>=far)break;
    const stop=Math.min(far,...next);
    if(stop>t)rows.push({index:cell.slice(),entry:t,exit:stop});
    if(stop>=far)break;
    for(let a=0;a<3;a++)if(next[a]===stop){cell[a]+=step[a];next[a]+=delta[a];}
    t=stop;
  }
  return rows;
}
if(typeof module!=='undefined')module.exports={traverseCells};
