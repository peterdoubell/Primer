(function(){'use strict';
const TC=7.2,BC0=80,MU0=4*Math.PI*1e-7;
function build({temperature=5,appliedMilliTesla=30}={}){
 if(!Number.isFinite(temperature)||temperature<0||temperature>10||!Number.isFinite(appliedMilliTesla)||appliedMilliTesla<0||appliedMilliTesla>100)throw Error('Outside teaching-model range');
 const transition=appliedMilliTesla<=BC0?TC*Math.sqrt(1-appliedMilliTesla/BC0):null;
 const bc=temperature<TC?BC0*(TC-temperature)*(TC+temperature)/(TC*TC):0;
 const boundary=transition!==null&&temperature===transition;
 const superconducting=transition!==null&&temperature<transition;
 const order=superconducting?Math.sqrt(1-temperature/TC):0;
 const branches=[];
 if(transition!==null&&transition>0){const upper=[];for(let i=0;i<=120;i++){// Sample by order to resolve the square-root endpoint at zero field.
 const q0=1,q1=Math.sqrt(Math.max(0,1-transition/TC)),q=q0+(q1-q0)*i/120;upper.push([TC*(1-q*q),q]);}
 upper[0]=[0,1];upper[upper.length-1]=[transition,Math.sqrt(Math.max(0,1-transition/TC))];branches.push({kind:'superconducting-limit',points:upper,endOpen:appliedMilliTesla>0});}
 branches.push({kind:'normal',points:[[Math.max(0,transition||0),0],[10,0]],startOpen:transition!==null&&appliedMilliTesla>0});
 const fieldDifference=transition!==null?BC0*(temperature-transition)*(temperature+transition)/(TC*TC):appliedMilliTesla-bc;
 const gibbsDifference=temperature<TC?(boundary?0:fieldDifference*(appliedMilliTesla+bc)*1e-6/(2*MU0)):null;
 return{gibbsDifferenceJPerM3:gibbsDifference,freeEnergyMeaning:'Ideal bulk Gibbs difference G_s-G_n at fixed external field; superconducting branch is not supplied above Tc.',geometryAssumption:'Negligible demagnetization, e.g. a long cylinder in longitudinal field; no finite-sample intermediate state.',mu0Approximation:'4 pi × 10^-7 H/m',temperature,appliedMilliTesla,criticalMilliTesla:bc,transitionTemperatureK:transition,orderParameterIndex:boundary&&appliedMilliTesla>0?null:order,boundary,superconducting,branches,coordinateUnits:['K','dimensionless phenomenological index'],fieldConvention:'mu0 H_a, millitesla',boundaryMeaning:'At nonzero-field coexistence, a unique homogeneous order index is not assigned. No intermediate-state geometry is solved.'};
}
window.CondensedCore={build,TC,BC0,MU0};
})();