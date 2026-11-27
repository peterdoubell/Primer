import test from 'node:test';
import assert from 'node:assert/strict';
import {arrayIntensity,configuration,detector,pixelResponse,readPixel,settings,lines,sensorWidthM} from '../web/physics/grating-spectrometer/model.mjs';
import fs from 'node:fs';
const near=(a,b,t=1e-10)=>assert.ok(Math.abs(a-b)<t,`${a} differs from ${b}`);
function phasors(theta,lambda,d,N){let re=0,im=0;for(let j=0;j<N;j++){const angle=2*Math.PI*j*d*Math.sin(theta)/lambda;re+=Math.cos(angle);im+=Math.sin(angle);}return(re*re+im*im)/(N*N);}
test('array factor agrees with independently summed complex groove amplitudes',()=>{
 for(const N of [2,40,600,1600,3000])for(const q of [0,.128,1,1+.37/N,1+1/N,1+1.73/N,2-.5/N]){
  const d=1e-6,lambda=4e-7,theta=Math.asin(q*lambda/d);near(arrayIntensity(theta,lambda,d,N),phasors(theta,lambda,d,N),2e-10);
 }
});
test('principal maxima, adjacent minima, symmetry and the two-groove limit',()=>{
 const d=1/600e3,lambda=588.995e-9,N=600;
 for(const m of [0,1,2]){const theta=Math.asin(m*lambda/d);near(arrayIntensity(theta,lambda,d,N),1);near(arrayIntensity(Math.asin((m+1/N)*lambda/d),lambda,d,N),0);near(arrayIntensity(theta,lambda,d,N),arrayIntensity(-theta,lambda,d,N));}
 for(const theta of [-.6,-.1,0,.15,.6])near(arrayIntensity(theta,lambda,d,2),Math.cos(Math.PI*d*Math.sin(theta)/lambda)**2);
});
test('source wavelengths and SI geometry have independently calculated dimensions',()=>{
 const c=configuration();near(c.pitchM,1/600000);near(c.ruledWidthM,.001);near(c.requiredResolvingPower,986.4306996987053,1e-8);near(c.references[0].theta,20.695232157403673*Math.PI/180);near(c.references[1].theta,20.717187442688136*Math.PI/180);near(c.separationM,.00011495760633522796);assert.equal(c.rayleigh,false);
 assert.deepEqual(lines.map(l=>l.airNm),[588.9950,589.5924]);
 const wider=configuration({grooves:1600});near(wider.angularSeparation,c.angularSeparation);assert.equal(wider.rayleigh,true);assert.equal(wider.resolvingPower,1600);
 const dense=configuration({density:900});assert.ok(dense.angularSeparation>c.angularSeparation);assert.equal(dense.resolvingPower,c.resolvingPower);
 const firstZeroWidth=a=>Math.asin((a.order+1/a.grooves)*a.references[0].wavelengthM/a.pitchM)-a.references[0].theta;assert.ok(firstZeroWidth(dense)>firstZeroWidth(c));assert.ok(firstZeroWidth(wider)<firstZeroWidth(c));
 const longer=configuration({focalMm:600});near(longer.separationM,2*c.separationM);near(longer.angularSeparation,c.angularSeparation);assert.equal(longer.resolvingPower,c.resolvingPower);
 assert.equal(configuration({order:2}).resolvingPower,1200);
});
test('pixel integrals agree with independent quadrature of raw phasor sums',()=>{
 const fixture=JSON.parse(fs.readFileSync(new URL('./fixtures/grating-spectrometer-reference.json',import.meta.url)));
 for(const e of fixture.pixels){const c=configuration(e.settings),a=pixelResponse(e.left,e.right,c);near(a.components[0],e.components[0],1.5e-4);near(a.components[1],e.components[1],1.5e-4);near(a.total,e.total,1.5e-4);assert.ok(a.samples>=8);}
});
test('detector bins have no gaps; pixel readings invert the angular calibration',()=>{
 for(const pixelUm of [1,5,10,25,50]){const c=detector({pixelUm});assert.equal(c.pixels.length,1200/pixelUm);near(c.pixels[0].left,-sensorWidthM/2);near(c.pixels.at(-1).right,sensorWidthM/2);for(let i=0;i<c.pixels.length;i++){const p=c.pixels[i];if(i)near(p.left,c.pixels[i-1].right);assert.ok(p.total>=0&&p.total<=1+1e-12);const r=readPixel(c,i);near(c.order*r.inferredAirNm*1e-9,c.pitchM*Math.sin(r.theta));}}
});
test('forbidden orders stay empty and invalid input is rejected',()=>{
 const c=detector({density:1200,order:2});assert.equal(c.valid,false);assert.deepEqual(c.pixels,[]);assert.deepEqual(c.curve,[]);assert.equal(c.references[0].theta,null);assert.equal(c.center,null);assert.equal(c.separationM,null);
 for(const s of [{grooves:1},{grooves:40.1},{density:NaN},{order:0},{focalMm:0},{pixelUm:7}])assert.throws(()=>settings(s));
 assert.throws(()=>readPixel(detector(),-1));
});
