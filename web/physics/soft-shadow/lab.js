import { blockerRadius, lampView, screenDistance, screenHalfWidth, shadowEdges } from './geometry.mjs';

const $ = id => document.getElementById(id);
const lamp = $('lamp');
const blocker = $('blocker');
const probe = $('probe');
const colors = { ink:'#f0eee5', muted:'#adc0d2', gold:'#ffce79', blue:'#7dc7e9', line:'#3a5268', dark:'#102032' };
const percent = fraction => (100 * fraction).toFixed(1) + '%';
const cm = value => value.toFixed(0) + ' cm';

function text(ctx, label, x, y, align='left', color=colors.ink, size=25) {
  const fontScale = Math.max(1, Math.min(1.6, 500 / ctx.canvas.clientWidth));
  ctx.font = size * fontScale + 'px system-ui, sans-serif';
  ctx.textAlign = align;
  ctx.fillStyle = color;
  ctx.fillText(label,x,y);
}

function segment(ctx,points,color,width=3,dash=[]) {
  ctx.strokeStyle=color;
  ctx.lineWidth=width;
  ctx.setLineDash(dash);
  ctx.beginPath();
  ctx.moveTo(...points[0]);
  points.slice(1).forEach(point=>ctx.lineTo(...point));
  ctx.stroke();
  ctx.setLineDash([]);
}

function disk(ctx,x,y,radius,fill) {
  ctx.fillStyle=fill;
  ctx.beginPath();
  ctx.arc(x,y,radius,0,2*Math.PI);
  ctx.fill();
}

function board(id) {
  const canvas=$(id);
  const ctx=canvas.getContext('2d');
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.lineCap='round';
  return ctx;
}

function sideView(sourceRadius,distance,point) {
  const ctx=board('side');
  const x=value=>85 + 8.3 * value;
  const y=value=>295 - 4.4 * value;
  const hit=y(point);
  const count=sourceRadius===0 ? 1 : 9;
  const rays=Array.from({length:count},(_,index)=>sourceRadius===0 ? 0 : sourceRadius*(2*index/(count-1)-1));
  for (const source of rays) {
    const crossing=source+(point-source)*distance/screenDistance;
    const start=[x(0),y(source)];
    if (Math.abs(crossing)<=blockerRadius) {
      segment(ctx,[start,[x(distance),y(crossing)]],colors.line,2,[7,7]);
    } else {
      segment(ctx,[start,[x(screenDistance),hit]],colors.gold,2.5);
    }
  }
  segment(ctx,[[x(0),y(-sourceRadius)],[x(0),y(sourceRadius)]],colors.gold,13);
  if (!sourceRadius) disk(ctx,x(0),y(0),8,colors.gold);
  segment(ctx,[[x(distance),y(-blockerRadius)],[x(distance),y(blockerRadius)]],colors.blue,14);
  segment(ctx,[[x(screenDistance),y(-screenHalfWidth)],[x(screenDistance),y(screenHalfWidth)]],'#f1e2bd',11);
  disk(ctx,x(screenDistance),hit,9,colors.gold);
  disk(ctx,x(screenDistance),hit,4,colors.dark);
  text(ctx,'Lamp',x(0),45,'center');
  text(ctx,'Blocker',x(distance),45,'center');
  text(ctx,'Screen',x(screenDistance),45,'center');
  const base=553;
  segment(ctx,[[x(0),base],[x(screenDistance),base]],colors.line,2);
  for(const tick of [0,distance,screenDistance]) {
    segment(ctx,[[x(tick),base-7],[x(tick),base+7]],colors.line,2);
    text(ctx,cm(tick),x(tick),base+28,'center',colors.muted,21);
  }
  text(ctx,'Side view',34,508,'left',colors.muted,21);
}

let previousScreen;
function screenView(sourceRadius,distance,point) {
  const ctx=board('screen');
  const center=[380,294];
  const radius=245;
  const scale=radius/screenHalfWidth;
  const state=[sourceRadius,distance].join(',');
  if (previousScreen?.state===state) {
    ctx.putImageData(previousScreen.image,0,0);
  } else {
    const image=ctx.createImageData(760,590);
    for (let row=0;row<590;row++) {
      for (let col=0;col<760;col++) {
        const fromCenter=Math.hypot(col-center[0],row-center[1]);
        if (fromCenter>radius) continue;
        const visible=lampView(sourceRadius,distance,fromCenter/scale).visible;
        const base=[13,29,44], bright=[255,226,159];
        const offset=4*(row*760+col);
        for (let channel=0;channel<3;channel++) image.data[offset+channel]=base[channel]+visible*(bright[channel]-base[channel]);
        image.data[offset+3]=255;
      }
    }
    ctx.putImageData(image,0,0);
    const edges=shadowEdges(sourceRadius,distance);
    for(const [edge,color] of [[edges.outer,colors.blue],[edges.inner,colors.muted]]) {
      if (edge>0 && edge<=screenHalfWidth) {
        ctx.strokeStyle=color;
        ctx.lineWidth=1.7;
        ctx.setLineDash([6,7]);
        ctx.beginPath();
        ctx.arc(...center,edge*scale,0,2*Math.PI);
        ctx.stroke();
      }
    }
    segment(ctx,[[center[0]-radius,center[1]],[center[0]+radius,center[1]]],colors.line,1,[3,8]);
    previousScreen={state,image:ctx.getImageData(0,0,760,590)};
  }
  disk(ctx,center[0]+point*scale,center[1],11,colors.gold);
  disk(ctx,center[0]+point*scale,center[1],5,colors.dark);
  text(ctx,'Fully lit',28,566,'left',colors.gold,22);
  text(ctx,'Partly blocked',380,566,'center',colors.blue,22);
  text(ctx,'Fully blocked',732,566,'right',colors.muted,22);
}

function lampViewDiagram(sourceRadius,view) {
  const ctx=board('view');
  const x=380,y=285;
  const scale=sourceRadius>0 ? 196 / Math.max(sourceRadius,14) : 14;
  const apparentRadius=view.apparentRadius*scale;
  if(sourceRadius) {
    disk(ctx,x,y,sourceRadius*scale,colors.gold);
    ctx.save();
    ctx.beginPath();
    ctx.arc(x,y,sourceRadius*scale,0,2*Math.PI);
    ctx.clip();
    disk(ctx,x+view.apparentX*scale,y,apparentRadius,colors.dark);
    ctx.restore();
    ctx.strokeStyle=colors.blue;
    ctx.lineWidth=2.5;
    ctx.setLineDash([7,7]);
    ctx.beginPath();
    ctx.arc(x+view.apparentX*scale,y,apparentRadius,0,2*Math.PI);
    ctx.stroke();
    ctx.setLineDash([]);
  } else {
    disk(ctx,x,y,8,view.visible ? colors.gold : colors.dark);
    ctx.strokeStyle=colors.gold;
    ctx.lineWidth=2;
    ctx.beginPath();
    ctx.arc(x,y,8,0,2*Math.PI);
    ctx.stroke();
    if(!view.visible) {
      segment(ctx,[[x-16,y-16],[x+16,y+16]],colors.blue,4);
      segment(ctx,[[x-16,y+16],[x+16,y-16]],colors.blue,4);
    }
  }
  text(ctx,sourceRadius ? 'Round lamp' : 'Point lamp',x,45,'center');
  text(ctx,percent(view.visible)+' of the lamp is visible',x,553,'center',colors.ink,27);
}

function render() {
  const sourceRadius=Number(lamp.value)/2;
  const distance=Number(blocker.value);
  const point=Number(probe.value);
  const view=lampView(sourceRadius,distance,point);
  const edges=shadowEdges(sourceRadius,distance);
  $('lamp-value').textContent=sourceRadius ? cm(2*sourceRadius) : 'Point';
  $('blocker-value').textContent=cm(distance);
  $('probe-value').textContent=cm(point);
  const statement={dark:'The lamp is fully hidden. This spot is dark.',partial:'Part of the lamp peeks around the blocker. This spot is partly lit.',lit:'The whole lamp is visible. This spot is fully lit.'}[view.kind];
  $('result').textContent=statement;
  $('screen-description').textContent=edges.inner>0
    ? 'The middle stays dark. '+(sourceRadius ? 'A band around it fades into the light.' : 'The edge is sharp.')
    : 'Some of the lamp is visible even at the middle. The centre has no fully dark patch.';
  $('view-description').textContent=sourceRadius
    ? 'Gold shows the lamp you can see. The dashed blue circle marks the blocker projected onto the lamp.'
    : 'A point lamp is either visible or hidden at each spot on the screen.';
  $('side').setAttribute('aria-label','Straight light paths from the lamp to a point '+cm(point)+' from the screen centre. '+statement);
  $('screen').setAttribute('aria-label','Screen with a fully dark radius of '+edges.inner.toFixed(1)+' cm and partly blocked light out to '+edges.outer.toFixed(1)+' cm. '+statement);
  $('view').setAttribute('aria-label','View of the lamp from the chosen screen point. '+percent(view.visible)+' of the lamp area is visible.');
  sideView(sourceRadius,distance,point);
  screenView(sourceRadius,distance,point);
  lampViewDiagram(sourceRadius,view);
}

for(const control of [lamp,blocker,probe]) control.addEventListener('input',render);
$('tiny').addEventListener('click',()=>{lamp.value=0;render();});
$('wide').addEventListener('click',()=>{lamp.value=28;render();});
render();

window.addEventListener('resize', () => { previousScreen = undefined; render(); });
