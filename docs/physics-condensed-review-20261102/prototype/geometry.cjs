'use strict';const{cylinderField}=require('./field.cjs');
function geometry(parameters){const f=cylinderField(parameters),radius=1,zLimits=[-2,2],rings=zLimits.map(z=>Array.from({length:65},(_,i)=>[Math.cos(i*2*Math.PI/64),Math.sin(i*2*Math.PI/64),z]));const base={coordinateUnits:'mm',radiusMM:radius,displayedAxialWindowMM:zLimits,rings,physicalEndFaces:false,infiniteCylinder:true,fieldGlyphs:[],currentGlyphs:[],uniqueHomogeneousState:f.unique};if(!f.unique)return{...base,note:f.reason};
 const bScale=10,kScale=1e-5;function glyph(kind,origin,value,scale){return{kind,originMM:origin,value,endpointMM:origin.map((x,i)=>x+scale*value[i]),displayScale:scale,zero:value.every(v=>v===0)};}
 for(const z of [-1,0,1]){base.fieldGlyphs.push(glyph('inside-B',[0,0,z],f.insideTesla,bScale));for(let i=0;i<8;i++){const t=i*2*Math.PI/8;for(const[r,kind,value]of [[.5,'inside-B',f.insideTesla],[1.5,'outside-B',f.outsideTesla]])base.fieldGlyphs.push(glyph(kind,[r*Math.cos(t),r*Math.sin(t),z],value,bScale));}}
 for(let i=0;i<16;i++){const t=i*2*Math.PI/16;base.currentGlyphs.push(glyph('surface-K',[Math.cos(t),Math.sin(t),0],f.surfaceCurrent(t),kScale));}
 return{...base,fieldValueUnits:'T',currentValueUnits:'A/m',fieldDisplayScaleMMperT:bScale,currentDisplayScaleMMperAperM:kScale,note:'Vector-glyph lengths encode field/current values, not particle paths. Cylinder rings mark the displayed cut window, not physical ends.'};
}
module.exports={geometry};
