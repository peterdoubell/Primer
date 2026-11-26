import {detector,readPixel,sensorWidthM} from './model.mjs';
const $=id=>document.getElementById(id),canvas=$('profile'),ctx=canvas.getContext('2d');
const fields={density:'density',grooves:'grooves',order:'order',focalMm:'focal',pixelUm:'pixel'};
const colours=['#83d4ec','#ef9d87','#f3d18b'];
let current,selected=119,plot;
const fixed=(v,d=3)=>v.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
function row(values){const r=document.createElement('tr');for(const value of values){const c=document.createElement('td');c.textContent=value;r.append(c);}return r;}
function setup(){return Object.fromEntries(Object.entries(fields).map(([k,id])=>[k,Number($(id).value)]));}
function bench(){
 const rays=$('rays'),scope=$('telescope');rays.replaceChildren();scope.replaceChildren();
 if(!current.valid){$('angle-label').textContent='No forward image for this order';return;}
 const ns='http://www.w3.org/2000/svg',make=(tag,attrs)=>{const el=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))el.setAttribute(k,v);return el;};
 for(const line of current.references)rays.append(make('path',{d:`M340 230L${340+200*Math.cos(line.theta)} ${230-200*Math.sin(line.theta)}`,fill:'none',stroke:'#f3d18b','stroke-width':'2'}));
 scope.setAttribute('transform',`translate(${340+200*Math.cos(current.center)} ${230-200*Math.sin(current.center)}) rotate(${-current.center*180/Math.PI})`);
 scope.append(make('rect',{x:-45,y:-18,width:95,height:36,rx:9,fill:'url(#metal)'}),make('ellipse',{cx:-45,cy:0,rx:7,ry:18,fill:'#8fd5e1'}),make('rect',{x:50,y:-9,width:25,height:18,rx:3,fill:'#768f99'}));
 $('angle-label').textContent=`Telescope θ₀ = ${fixed(current.center*180/Math.PI,4)}°`;
}
function draw(){
 const w=canvas.clientWidth,h=w<600?320:360,dpr=devicePixelRatio||1;canvas.style.height=h+'px';canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#11232e';ctx.fillRect(0,0,w,h);
 const left=52,right=w-15,top=25,bottom=h-48;plot={left,right,top,bottom,w,h};
 const x=v=>left+(v+sensorWidthM/2)/sensorWidthM*(right-left),y=v=>bottom-v*(bottom-top);
 ctx.font='12px system-ui';ctx.lineWidth=1;ctx.strokeStyle='#344f5d';ctx.fillStyle='#c7d9df';
 for(let i=0;i<=4;i++){const yy=y(i/4);ctx.beginPath();ctx.moveTo(left,yy);ctx.lineTo(right,yy);ctx.stroke();ctx.textAlign='right';ctx.fillText((i/4).toFixed(2),left-8,yy+4);}
 for(let i=0;i<=4;i++){const mm=-.6+i*.3,xx=x(mm/1000);ctx.textAlign='center';ctx.fillText(mm.toFixed(1),xx,bottom+20);}
 ctx.textAlign='left';ctx.fillText('Normalized response',left,15);ctx.textAlign='center';ctx.fillText('Detector position relative to pointing (mm)',(left+right)/2,h-8);
 if(!current.valid){ctx.fillStyle='#f3d18b';ctx.fillText('This order has no forward image.',(left+right)/2,(top+bottom)/2);return;}
 ctx.save();ctx.beginPath();ctx.rect(left,top,right-left,bottom-top);ctx.clip();
 for(const pixel of current.pixels){ctx.fillStyle=pixel.index===selected?'#e4e8b684':'#cfdecd40';const a=x(pixel.left),b=x(pixel.right);ctx.fillRect(a,y(pixel.total),Math.max(.5,b-a),bottom-y(pixel.total));}
 for(let n=0;n<3;n++){ctx.beginPath();for(let i=0;i<current.curve.length;i++){const point=current.curve[i],yy=y(n===2?point.total:point.components[n]);if(!i)ctx.moveTo(x(point.xM),yy);else ctx.lineTo(x(point.xM),yy);}ctx.strokeStyle=colours[n];ctx.lineWidth=n===2?2:1.3;ctx.stroke();}
 for(const line of current.references){ctx.setLineDash([4,5]);ctx.strokeStyle='#c6d7dc66';ctx.beginPath();ctx.moveTo(x(line.xM),top);ctx.lineTo(x(line.xM),bottom);ctx.stroke();}ctx.setLineDash([]);
 const pixel=current.pixels[selected];if(pixel){ctx.strokeStyle='#f8efc6';ctx.lineWidth=1;ctx.strokeRect(x(pixel.left),top,Math.max(1,x(pixel.right)-x(pixel.left)),bottom-top);}
 ctx.restore();
}
function inspect(){
 if(!current.valid){$('readout').textContent='No detector reading is assigned to a forbidden order.';$('pixel-table').replaceChildren();$('table-note').textContent='';return;}
 const p=readPixel(current,selected),wavelength=x=>current.pitchM*Math.sin(current.center+Math.atan(x/current.focalM))/current.order*1e9;
 $('pixel-value').textContent=`${selected+1} / ${current.pixels.length}`;
 $('selected').value=selected;
 $('readout').textContent=`Pixel ${selected+1}: ${fixed(p.left*1000,4)} to ${fixed(p.right*1000,4)} mm. Centre angle ${fixed(p.theta*180/Math.PI,6)}°. Assigned wavelength ${fixed(p.inferredAirNm,5)} nm in air; bin edges ${fixed(wavelength(p.left),5)}–${fixed(wavelength(p.right),5)} nm. Averaged normalized response ${fixed(p.total,5)}. This bin can contain contributions from both reference lines.`;
 const start=Math.max(0,Math.min(current.pixels.length-9,selected-4));
 $('pixel-table').replaceChildren(...current.pixels.slice(start,start+9).map(p=>{const r=readPixel(current,p.index);return row([p.index+1,fixed(p.xM*1000,4),fixed(r.inferredAirNm,5),fixed(p.total,6)]);}));
 $('table-note').textContent=`${Math.min(9,current.pixels.length)} of ${current.pixels.length} model pixels, nearest the selected position.`;
 $('previous').disabled=selected===0;$('next').disabled=selected===current.pixels.length-1;draw();
}
function refresh(){
 const previousX=current?.pixels[selected]?.xM??0;const s=setup();current=detector(s);selected=Math.max(0,Math.min(current.pixels.length-1,Math.floor((previousX+sensorWidthM/2)/current.pixelM)));if(selected<0)selected=0;
 $('density-value').textContent=s.density+' grooves/mm';$('grooves-value').textContent=s.grooves.toLocaleString('en-US');$('focal-value').textContent=s.focalMm+' mm';
 $('pitch').textContent=fixed(current.pitchM*1e6,4)+' µm';$('width').textContent=fixed(current.ruledWidthM*1000,3)+' mm';$('resolving').textContent=current.resolvingPower.toLocaleString('en-US');$('required').textContent=fixed(current.requiredResolvingPower,2);
 $('assessment').textContent=!current.valid?'The selected order cannot give a forward image at both reference wavelengths: at least one is grazing or non-propagating (|mλ/d| ≥ 1). Reduce the density or use first order.':current.rayleigh?'The ideal grating meets the near-equal-line Rayleigh estimate. Inspect the pixel averages too: detector size and omitted real-instrument effects can still limit a measurement.':'The ideal grating falls below the near-equal-line Rayleigh estimate. More illuminated grooves or a higher accessible order are needed; magnification alone does not increase |m|N.';
 $('lines').replaceChildren(...current.references.map(l=>row([l.name,fixed(l.airNm,4)+' nm',l.theta===null?'Grazing or non-propagating':fixed(l.theta*180/Math.PI,6)+'°',l.xM===null?'No image':fixed(l.xM*1000,6)+' mm'])));
 $('separation').textContent=current.valid?`Reference separation Δλ = ${fixed(current.deltaNm,4)} nm. Predicted angular separation ${fixed(current.angularSeparation*1000,6)} mrad; detector separation ${fixed(current.separationM*1000,6)} mm. These centres are predicted from the reference wavelengths, not fitted to the trace.`:'The reference wavelength separation remains '+fixed(current.deltaNm,4)+' nm; this order does not give a detector image.';
 const outside=current.valid&&current.references.some(l=>Math.abs(l.xM)>sensorWidthM/2);
 $('profile-caption').textContent=!current.valid?'No extrapolated profile is shown for a forbidden order.':`${current.pixels.length} pixels × ${s.pixelUm} µm. Optical curves and pixel bars share the same vertical normalization; the plot is not rescaled to its largest value.${outside?' A reference line centre lies outside the finite sensor; change focal length or order.':''}`;
 for(const id of ['selected','previous','next'])$(id).disabled=!current.valid;
 $('selected').max=Math.max(0,current.pixels.length-1);bench();inspect();draw();
}
function select(index){if(!current.valid)return;selected=Math.max(0,Math.min(current.pixels.length-1,index));inspect();}
for(const id of Object.values(fields))$(id).addEventListener($(id).tagName==='SELECT'?'change':'input',()=>{$('comparison').textContent='';refresh();});
$('selected').addEventListener('input',()=>select(+$('selected').value));$('previous').addEventListener('click',()=>select(selected-1));$('next').addEventListener('click',()=>select(selected+1));
canvas.addEventListener('click',e=>{const b=canvas.getBoundingClientRect(),x=(e.clientX-b.left)*plot.w/b.width;select(Math.floor((x-plot.left)/(plot.right-plot.left)*current.pixels.length));});
canvas.addEventListener('keydown',e=>{const moves={ArrowLeft:selected-1,ArrowRight:selected+1,Home:0,End:current.pixels.length-1};if(e.key in moves){e.preventDefault();select(moves[e.key]);}});
function preset(id,state,text){$(id).addEventListener('click',()=>{for(const[k,v]of Object.entries(state))$(fields[k]).value=v;refresh();$('comparison').textContent=text;});}
const base={density:600,grooves:600,order:1,focalMm:300,pixelUm:5};
preset('baseline',base,'Baseline: 600 grooves/mm, N = 600, first order, 300 mm focal length and 5 µm pixels.');
preset('open',{...base,grooves:1600},'Only N changes from baseline. The principal directions stay fixed; the interference peaks narrow and |m|N rises from 600 to 1,600.');
preset('second',{...base,order:2},'Only order changes from baseline. Second order increases both dispersion and ideal resolving power, if it propagates.');
preset('coarse',{...base,grooves:1600,pixelUm:50},'Compare with “Open to 1,600 grooves”: the grating and its optical curves are unchanged, but each pixel now averages a ten-times wider interval.');
new ResizeObserver(()=>{if(current)draw();}).observe(canvas.parentElement);refresh();
