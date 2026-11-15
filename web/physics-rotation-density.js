(function(){
'use strict';
function diskDensity(R,z,{diskMass:M,diskA:a,diskB:b}){
 if(![R,z,M,a,b].every(Number.isFinite)||R<0||M<0||a<0||b<=0)throw Error('Invalid density input');
 if(M===0)return 0;const q=Math.hypot(z,b),d=R*R+(a+q)**2;
 return M*b*b/(4*Math.PI)*(a*R*R+(a+3*q)*(a+q)**2)/(q**3*d**2.5);
}
function densitySurface(parameters,fraction=.1,nTheta=32,nPhi=64){
 if(!(fraction>0&&fraction<1)||!Number.isInteger(nTheta)||!Number.isInteger(nPhi)||nTheta<4||nPhi<8)throw Error('Invalid density surface sampling');
 const peak=diskDensity(0,0,parameters);if(peak===0)return {positions:[],triangles:[],density:0,empty:true};const target=peak*fraction,positions=[],triangles=[];
 function radius(theta){const s=Math.sin(theta),c=Math.cos(theta);let low=0,high=parameters.diskA+parameters.diskB;for(let k=0;diskDensity(high*s,high*c,parameters)>target;k++){if(k>60)throw Error('Density contour could not be bracketed');high*=2;}for(let k=0;k<70;k++){const mid=(low+high)/2;if(diskDensity(mid*s,mid*c,parameters)>target)low=mid;else high=mid;}return(low+high)/2;}
 const aspect=radius(0)/radius(Math.PI/2);
 positions.push([0,0,radius(0)]);
 for(let j=1;j<nTheta;j++){const t=Math.PI*j/nTheta,theta=Math.atan2(Math.sin(t),aspect*Math.cos(t)),r=radius(theta);for(let i=0;i<nPhi;i++){const phi=2*Math.PI*i/nPhi;positions.push([r*Math.sin(theta)*Math.cos(phi),r*Math.sin(theta)*Math.sin(phi),r*Math.cos(theta)]);}}
 const south=positions.length;positions.push([0,0,-radius(Math.PI)]);
 for(let i=0;i<nPhi;i++){const k=(i+1)%nPhi;triangles.push([0,1+i,1+k]);for(let j=0;j<nTheta-2;j++){const a=1+j*nPhi+i,b=1+j*nPhi+k,c=a+nPhi,d=b+nPhi;triangles.push([a,c,b],[b,c,d]);}const a=1+(nTheta-2)*nPhi+i,b=1+(nTheta-2)*nPhi+k;triangles.push([a,south,b]);}
 return {positions,triangles,density:target,densityUnits:'solar masses/kpc^3',positionUnits:'kpc',fractionOfCentralDensity:fraction,empty:false,meaning:'Sampled constant-density surface; not a material boundary or total extent'};
}
window.RotationDensity={diskDensity,densitySurface};

})();
