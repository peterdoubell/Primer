'use strict';
const get=id=>document.getElementById(id);
const controls=['time','wavelength','fraction','yaw','pitch'];
function draw(){
  const cycles=get('time').valueAsNumber,wavelength=get('wavelength').valueAsNumber;
  const fraction=get('fraction').valueAsNumber,amplitude=wavelength*fraction/100;
  const time=cycles*wavelength,yaw=get('yaw').valueAsNumber*Math.PI/180,pitch=get('pitch').valueAsNumber*Math.PI/180;
  for(const id of controls)document.querySelector('output[for="'+id+'"]').value=get(id).value+(id==='fraction'?'%':id==='yaw'||id==='pitch'?'°':'');
  const canvas=get('wave'),ctx=canvas.getContext('2d');
  ctx.fillStyle='#14232c';ctx.fillRect(0,0,canvas.width,canvas.height);
  function project(x,y,z){
    const horizontal=Math.cos(yaw)*(x-1)-Math.sin(yaw)*z;
    const depth=Math.sin(yaw)*(x-1)+Math.cos(yaw)*z;
    return {x:420+300*horizontal,y:230-300*(Math.cos(pitch)*y-Math.sin(pitch)*depth),depth:Math.sin(pitch)*y+Math.cos(pitch)*depth};
  }
  const parcels=[];
  for(let ix=0;ix<=50;ix++)for(let iy=-2;iy<=2;iy++)for(let iz=-2;iz<=2;iz++){
    const sample=sampleParcel(ix/25,time,amplitude,wavelength);
    parcels.push({...project(sample.x,iy*.1,iz*.1),sample,tracked:ix===25&&iy===0&&iz===0});
  }
  parcels.sort((a,b)=>a.depth-b.depth);
  function paint(parcel){
    const strength=Math.abs(parcel.sample.pressure)/(2*Math.PI*.01);
    const target=parcel.sample.pressure>=0?[245,95,83]:[75,165,245];
    const rgb=target.map(channel=>Math.round(225+(channel-225)*strength));
    ctx.fillStyle=parcel.tracked?'#ffcd47':'rgb('+rgb.join(',')+')';
    ctx.beginPath();ctx.arc(parcel.x,parcel.y,parcel.tracked?5:2.5,0,2*Math.PI);ctx.fill();
  }
  for(const parcel of parcels)if(!parcel.tracked)paint(parcel);
  const tracked=parcels.find(parcel=>parcel.tracked);paint(tracked);
  const current=sampleParcel(1,time,amplitude,wavelength);
  const inset=get('motion'),motion=inset.getContext('2d');
  motion.clearRect(0,0,inset.width,inset.height);
  // The same 100× scale is used for every wavelength and amplitude.
  const marker=420+current.displacement*100*160;
  motion.strokeStyle='#657b80';motion.lineWidth=2;motion.beginPath();motion.moveTo(50,90);motion.lineTo(790,90);motion.moveTo(420,55);motion.lineTo(420,125);motion.stroke();
  motion.fillStyle='#ad7100';motion.beginPath();motion.arc(marker,90,9,0,2*Math.PI);motion.fill();
  motion.fillStyle='#203c43';motion.font='22px system-ui';motion.textAlign='center';motion.fillText('Rest position',420,160);
  get('reading').textContent='Gold parcel displacement: '+current.displacement.toFixed(5)+' length units. Period: '+wavelength+' time units. Peak displacement: '+amplitude.toFixed(5)+' length units.';
  canvas.dataset.parcels=String(parcels.length);
  inset.dataset.displacement=String(current.displacement);
  inset.dataset.marker=String(marker);
}
for(const id of controls)get(id).addEventListener('input',draw);
get('reset').onclick=()=>{for(const [id,value] of Object.entries({time:0,wavelength:1,fraction:1,yaw:25,pitch:20}))get(id).value=value;draw();};
draw();
