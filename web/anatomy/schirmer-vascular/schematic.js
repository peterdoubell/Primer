(function(host){'use strict';
const colors=Object.freeze({background:[250,248,241,255],context:[218,224,220,255],selection:[20,108,108,255]});
function raster(labels,width,height,codes,{outline=false,context=true}={}){
 if(!(labels instanceof Uint16Array)||!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||labels.length!==width*height||typeof outline!=='boolean'||typeof context!=='boolean')throw new TypeError('Invalid native label plane');
 if(!Array.isArray(codes)||!codes.length||new Set(codes).size!==codes.length||codes.some(c=>!Number.isInteger(c)||c<1||c>65535))throw new TypeError('Select distinct nonzero source codes');
 const membership=new Uint8Array(65536);for(const code of codes)membership[code]=1;const selected=i=>membership[labels[i]]===1,out=new Uint8ClampedArray(labels.length*4);
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){const i=x+width*y,isSelected=selected(i),boundary=isSelected&&(x===0||y===0||x===width-1||y===height-1||!selected(i-1)||!selected(i+1)||!selected(i-width)||!selected(i+width));const color=isSelected&&(!outline||boundary)?colors.selection:context&&labels[i]!==0?colors.context:colors.background;out.set(color,4*(x+width*(height-1-y)));}return out;
}
function orientation(axis){if(!Number.isInteger(axis)||axis<0||axis>2)throw new RangeError('Source axis must be0,1or2');return [{left:'P',right:'A',top:'S',bottom:'I'},{left:'R',right:'L',top:'S',bottom:'I'},{left:'R',right:'L',top:'A',bottom:'P'}][axis];}
function scaleBar(spacingMM,lengthMM=20){if(!Number.isFinite(spacingMM)||spacingMM<=0||!Number.isFinite(lengthMM)||lengthMM<=0)throw new RangeError('Positive finite scale required');return {lengthMM,pixels:lengthMM/spacingMM};}
const api=Object.freeze({raster,orientation,scaleBar,colors});if(typeof module!=='undefined'&&module.exports)module.exports=api;if(host)host.PrimerAtlasSchematic=api;
})(typeof window!=='undefined'?window:null);
