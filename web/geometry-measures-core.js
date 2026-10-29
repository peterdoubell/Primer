/* Native unit-square and unit-cube constructions for area, perimeter and volume. */
(function(host){
'use strict';
function integer(n,name,min=1,max=12){if(!Number.isInteger(n)||n<min||n>max)throw Error(name+' is outside the supported integer range');return n;}
function polygonMetrics(points){let twiceArea=0,perimeter=0;for(let i=0;i<points.length;i++){const a=points[i],b=points[(i+1)%points.length];twiceArea+=a[0]*b[1]-b[0]*a[1];perimeter+=Math.hypot(b[0]-a[0],b[1]-a[1]);}return {twiceArea:Math.abs(twiceArea),perimeter};}
function planar(state){const width=integer(state.width,'Width'),height=integer(state.height,'Height');let polygon,cells=[];
if(state.kind==='rectangle'){polygon=[[0,0],[width,0],[width,height],[0,height]];}
else if(state.kind==='triangle'){const apex=integer(state.apex,'Apex',0,width);polygon=[[0,0],[width,0],[apex,height]];}
else if(state.kind==='cutout'){const cutWidth=integer(state.cutWidth,'Cut width',1,width-1),cutHeight=integer(state.cutHeight,'Cut height',1,height-1);polygon=[[0,0],[width,0],[width,height-cutHeight],[width-cutWidth,height-cutHeight],[width-cutWidth,height],[0,height]];}
else throw Error('Unknown plane shape');
if(state.kind!=='triangle')for(let y=0;y<height;y++)for(let x=0;x<width;x++)if(state.kind!=='cutout'||x<width-state.cutWidth||y<height-state.cutHeight)cells.push([x,y]);
const metrics=polygonMetrics(polygon);return {...state,width,height,polygon,cells,...metrics,area:metrics.twiceArea/2,lengthUnit:'cm',areaUnit:'cm²',heightFoot:state.kind==='triangle'?[state.apex,0]:null};}
function cuboid(state){const width=integer(state.width,'Width'),height=integer(state.height,'Height'),depth=integer(state.depth,'Depth');const cubes=[],faces=[];
for(let x=0;x<width;x++)for(let y=0;y<height;y++)for(let z=0;z<depth;z++){const cell=[x,y,z];cubes.push(cell);for(let axis=0;axis<3;axis++)for(const sign of [-1,1])if(cell[axis]===(sign<0?0:[width,height,depth][axis]-1))faces.push({cell,axis,sign});}
return {kind:'cuboid',width,height,depth,cubes,faces,volume:cubes.length,surfaceArea:faces.length,layerArea:width*depth,layers:height,lengthUnit:'cm',volumeUnit:'cm³',areaUnit:'cm²'};}
function equalPerimeter(width,height,otherWidth){integer(width,'Width');integer(height,'Height');integer(otherWidth,'Comparison width',Math.max(1,width+height-12),Math.min(12,width+height-1));const first=planar({kind:'rectangle',width,height}),second=planar({kind:'rectangle',width:otherWidth,height:width+height-otherWidth});return {kind:'compare',first,second,sharedPerimeter:first.perimeter,areaDifference:second.area-first.area};}
function withUnit(model,unit){if(!['cm','m'].includes(unit))throw Error('Unsupported unit');return {...model,...(model.first?{first:withUnit(model.first,unit),second:withUnit(model.second,unit)}:{}),lengthUnit:unit,areaUnit:unit+'²',volumeUnit:unit+'³',capacityLitres:model.kind==='cuboid'?model.volume*(unit==='m'?1000:.001):null};}
function scaledRectangle(width,height,factor){integer(factor,'Scale factor',1,3);const first=planar({kind:'rectangle',width,height}),polygon=first.polygon.map(p=>p.map(n=>n*factor)),cells=[];for(let y=0;y<height*factor;y++)for(let x=0;x<width*factor;x++)cells.push([x,y]);const metrics=polygonMetrics(polygon),second={kind:'rectangle',width:width*factor,height:height*factor,polygon,cells,...metrics,area:metrics.twiceArea/2};return {kind:'scale',first,second,factor,lengthRatio:factor,areaRatio:second.area/first.area};}
const defaults={kind:'rectangle',width:6,height:5,depth:3,apex:3,cutWidth:2,cutHeight:3,compareWidth:3,factor:2,unit:'cm'};
function accept(raw={}){
 if(!raw||typeof raw!=='object'||Array.isArray(raw))throw TypeError('Supply a measurement state');
 for(const key of Object.keys(raw))if(!Object.hasOwn(defaults,key))throw RangeError('Unknown measurement setting: '+key);
 const s={...defaults,...raw};
 if(!['rectangle','triangle','cutout','cuboid','compare','scale'].includes(s.kind))throw RangeError('Unknown measurement construction');
 if(!['cm','m'].includes(s.unit))throw RangeError('Choose centimetres or metres');
 for(const name of ['width','height','depth'])integer(s[name],name);
 integer(s.factor,'Scale factor',1,3);integer(s.apex,'Apex',0,12);integer(s.cutWidth,'Cut width');integer(s.cutHeight,'Cut height');integer(s.compareWidth,'Comparison width');
 return s;
}
function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
function model(raw={}){const state=accept(raw),s=state;const shape=s.kind==='cuboid'?cuboid(s):s.kind==='compare'?equalPerimeter(s.width,s.height,s.compareWidth):s.kind==='scale'?scaledRectangle(s.width,s.height,s.factor):planar(s);return freeze({...withUnit(shape,s.unit),state});}
const api={planar,cuboid,polygonMetrics,equalPerimeter,withUnit,scaledRectangle,accept,model,defaults:()=>({...defaults})};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
if(host)host.PrimerGeometryMeasuresCore=api;
})(typeof window==='undefined'?null:window);

