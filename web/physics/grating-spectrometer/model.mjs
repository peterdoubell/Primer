// Scalar Fraunhofer array factor for N identical narrow illuminated grooves.
// Wavelengths use NIST's air convention; all calculations below use SI units.
export const lines = Object.freeze([
  Object.freeze({id:'D2',name:'Na I D₂',airNm:588.9950}),
  Object.freeze({id:'D1',name:'Na I D₁',airNm:589.5924})
]);
export const sensorWidthM = 1.2e-3;
export function settings(input={}) {
  const s={density:600,grooves:600,order:1,focalMm:300,pixelUm:5,...input};
  for (const [key,lo,hi] of [['density',100,1200],['grooves',40,3000],['focalMm',100,1000],['pixelUm',1,50]])
    if(!Number.isFinite(s[key])||s[key]<lo||s[key]>hi)throw Error('Out-of-range '+key);
  if(!Number.isInteger(s.grooves)||![1,2].includes(s.order)||![1,5,10,25,50].includes(s.pixelUm)) throw Error('Invalid grating or detector');
  return s;
}
export function arrayIntensity(theta,wavelengthM,pitchM,N) {
  // Reduce phase in cycles before using sinc, retaining the N-groove maximum.
  const q=pitchM*Math.sin(theta)/wavelengthM;
  const r=q-Math.round(q);
  if(Math.abs(r)<1e-14)return 1;
  const amplitude=Math.sin(Math.PI*N*r)/(N*Math.sin(Math.PI*r));
  return amplitude*amplitude;
}
export function configuration(input={}) {
  const s=settings(input),pitchM=1e-3/s.density,focalM=s.focalMm*1e-3,pixelM=s.pixelUm*1e-6;
  const references=lines.map(line=>{const wavelengthM=line.airNm*1e-9,u=s.order*wavelengthM/pitchM;return {...line,wavelengthM,theta:Math.abs(u)<1?Math.asin(u):null};});
  const valid=references.every(r=>r.theta!==null),center=valid?(references[0].theta+references[1].theta)/2:null;
  for(const line of references)line.xM=valid?focalM*Math.tan(line.theta-center):null;
  const meanNm=(lines[0].airNm+lines[1].airNm)/2,deltaNm=lines[1].airNm-lines[0].airNm,required=meanNm/deltaNm;
  return {...s,pitchM,focalM,pixelM,references,valid,center,ruledWidthM:s.grooves*pitchM,resolvingPower:s.order*s.grooves,requiredResolvingPower:required,rayleigh:s.order*s.grooves>=required,deltaNm,meanNm,
    angularSeparation:valid?references[1].theta-references[0].theta:null,
    separationM:valid?references[1].xM-references[0].xM:null};
}
export function responseAt(xM,c) {
  if(!c.valid)return null;
  const theta=c.center+Math.atan(xM/c.focalM);
  const components=c.references.map(l=>arrayIntensity(theta,l.wavelengthM,c.pitchM,c.grooves));
  return {theta,components,total:(components[0]+components[1])/2};
}
export function pixelResponse(x0,x1,c) {
  // Resolve the fastest possible fringe by >=24 midpoint samples per period.
  // cos(theta)<=1 makes f*lambda/(N*d) a conservative lower fringe pitch here.
  const minimumPitch=c.focalM*c.references[0].wavelengthM/(c.grooves*c.pitchM);
  const n=Math.max(8,Math.ceil((x1-x0)*24/minimumPitch));
  const sums=[0,0];
  for(let i=0;i<n;i++) {const r=responseAt(x0+(i+.5)*(x1-x0)/n,c);sums[0]+=r.components[0];sums[1]+=r.components[1];}
  const components=sums.map(v=>v/n);return {components,total:(components[0]+components[1])/2,samples:n};
}
export function detector(input={}) {
  const c=configuration(input);if(!c.valid)return {...c,pixels:[],curve:[]};
  // Choose exact equal-width bins covering the physical 1.2 mm sensor.
  const count=Math.round(sensorWidthM/c.pixelM),pixelM=sensorWidthM/count;
  const pixels=Array.from({length:count},(_,i)=>{const left=-sensorWidthM/2+i*pixelM,right=left+pixelM;return{index:i,left,right,xM:(left+right)/2,...pixelResponse(left,right,c)};});
  const minimumPitch=c.focalM*c.references[0].wavelengthM/(c.grooves*c.pitchM);
  const samples=Math.max(2400,Math.ceil(sensorWidthM*24/minimumPitch));
  const curve=Array.from({length:samples+1},(_,i)=>{const xM=-sensorWidthM/2+sensorWidthM*i/samples;return{xM,...responseAt(xM,c)};});
  return {...c,pixelM,pixels,curve};
}
export function readPixel(c,index) {
  const pixel=c.pixels[index];if(!pixel)throw Error('Detector pixel is out of range');
  const theta=c.center+Math.atan(pixel.xM/c.focalM);
  return {...pixel,theta,inferredAirNm:c.pitchM*Math.sin(theta)/c.order*1e9};
}
