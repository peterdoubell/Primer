'use strict';
// Units: kpc, km/s, solar masses. G follows the explicit SI conversion below.
const KPC=3.0856775814913673e19,MSUN=1.988409870698051e30,GSI=6.67430e-11,G=GSI*MSUN/KPC/1e6;
function nfwFactor(x){if(x<1e-3){let sum=0;for(let n=2;n<=12;n++)sum+=(n%2? -1:1)*(n-1)/n*x**n;return sum;}return Math.log1p(x)-x/(1+x);}
function model(R,{diskMass=6e10,diskA=3,diskB=.3,haloScaleMass=8e11,haloRadius=20}={}){
 for(const v of [R,diskMass,diskA,diskB,haloScaleMass,haloRadius])if(!Number.isFinite(v))throw Error('Non-finite physical input');
 if(R<0||diskMass<0||diskA<0||diskB<=0||haloScaleMass<0||haloRadius<=0)throw Error('Invalid physical input');
 const x=R/haloRadius,haloEnclosedMass=haloScaleMass*nfwFactor(x),diskSpeed2=G*diskMass*R*R/(R*R+(diskA+diskB)**2)**1.5,haloSpeed2=R===0?0:G*haloEnclosedMass/R;
 return{radiusKpc:R,diskSpeedKms:Math.sqrt(diskSpeed2),haloSpeedKms:Math.sqrt(haloSpeed2),totalSpeedKms:Math.sqrt(diskSpeed2+haloSpeed2),haloEnclosedMassSolar:haloEnclosedMass};
}
function comparison(){
 let seed=0x57a83d19;
 function uniform(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return((seed>>>0)+.5)/4294967296;}
 const radii=[2,4,6,8,10,12,15,18,22,26,32,40],truth={diskMass:6e10,diskA:3,diskB:.3,haloScaleMass:8e11,haloRadius:20};
 return radii.map(r=>{const z=Math.sqrt(-2*Math.log(uniform()))*Math.cos(2*Math.PI*uniform()),expected=model(r,truth).totalSpeedKms;return{radiusKpc:r,speedKms:expected+8*z,sigmaKms:8,expectedKms:expected,standardizedNoise:z};});
}
module.exports={model,comparison,nfwFactor,G,KPC,MSUN,GSI};
