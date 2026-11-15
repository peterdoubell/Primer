const get = id => document.getElementById(id);
const radius = 5;
const ink = '#163746';
const teal = '#126f74';
const brick = '#9b4630';
const pi = Math.PI;

function lineFrom(point, angle) {
  const direction = [Math.cos(angle), Math.sin(angle)];
  const dot = point[0] * direction[0] + point[1] * direction[1];
  const radical = Math.sqrt(dot ** 2 + radius ** 2 - point[0] ** 2 - point[1] ** 2);
  const front = -dot + radical;
  const back = dot + radical;
  return {
    front, back, direction,
    end: point.map((coordinate, axis) => coordinate + front * direction[axis]),
    start: point.map((coordinate, axis) => coordinate - back * direction[axis]),
  };
}

function drawCanvas(id) {
  const canvas = get(id);
  const width = Math.round(canvas.getBoundingClientRect().width);
  if (width > 0 && width !== canvas.width) canvas.width = width;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = '15px system-ui';
  return {canvas, ctx, width:canvas.width};
}

function path(ctx, vertices, colour, width = 1, shade) {
  ctx.beginPath();
  vertices.forEach(([x,y],index) => index ? ctx.lineTo(x,y) : ctx.moveTo(x,y));
  if (shade) {
    ctx.closePath();
    ctx.fillStyle = shade;
    ctx.fill();
  }
  ctx.strokeStyle = colour;
  ctx.lineWidth = width;
  ctx.stroke();
}

function label(ctx,text,[x,y],colour=ink) {
  ctx.fillStyle = colour;
  ctx.fillText(text,x,y);
}

function drawCircle(p, ab, cd, proof) {
  const { canvas, ctx, width } = drawCanvas('circle');
  const size = Math.min((width - 66) / 2, 172);
  const project = ([x,y]) => [width / 2 + x * size / radius, 198 - y * size / radius];
  const origin = project([0,0]);
  const [a,b,c,d,pixel] = [ab.end, ab.start, cd.end, cd.start, p].map(project);
  ctx.beginPath();
  ctx.arc(...origin, size, 0, 2 * pi);
  ctx.strokeStyle = ink;
  ctx.lineWidth = 2;
  ctx.stroke();
  if (proof >= 2) {
    path(ctx, [a,pixel,d], teal, 1.5, '#146f7324');
    path(ctx, [c,pixel,b], brick, 1.5, '#ad5f3f24');
  }
  path(ctx, [a,b], teal, 2);
  path(ctx, [c,d], brick, 2);
  if (proof >= 1) {
    const aAngle = Math.atan2(a[1]-pixel[1],a[0]-pixel[0]);
    const dAngle = Math.atan2(d[1]-pixel[1],d[0]-pixel[0]);
    const separation = (dAngle - aAngle + 4*pi) % (2*pi);
    // Draw the smaller arc in each of the two vertically opposite angles.
    const start = separation <= pi ? aAngle : dAngle;
    const end = start + Math.min(separation, 2*pi-separation);
    const arcSize = Math.min(18, .35 * Math.min(ab.front, ab.back, cd.front, cd.back) * size / radius);
    for (const turn of [0,pi]) {
      ctx.beginPath();
      ctx.arc(...pixel,arcSize,start+turn,end+turn);
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#5d4586';
      ctx.stroke();
    }
  }
  for (const [name,point] of [['A',a],['B',b],['C',c],['D',d]]) {
    const dx=point[0]-origin[0],dy=point[1]-origin[1];
    const shiftX = dx > 0 ? 9 : -18;
    label(ctx,name,[point[0]+shiftX,point[1] + (dy>0?18:-9)]);
  }
  ctx.fillStyle = ink;
  ctx.fillRect(origin[0]-1.5,origin[1]-1.5,3,3);
  ctx.fillRect(pixel[0]-2,pixel[1]-2,4,4);
  label(ctx,p[0]===0 ? 'O = P' : 'O',[origin[0]-12,origin[1]+20]);
  if (p[0]!==0) label(ctx,'P',[pixel[0]+5,pixel[1]-10]);
  canvas.setAttribute('aria-label','Circle of radius 5 with chords AB and CD intersecting at P, '+p[0].toFixed(1)+' units from O');
}

function drawAreas(chords) {
  const { canvas, ctx, width } = drawCanvas('areas');
  const scale = Math.min((width - 38) / 20, 20);
  chords.forEach((chord,index)=>{
    const x = 10 + index * (10 * scale + 18), y=200;
    const w=chord.front*scale, h=chord.back*scale;
    ctx.fillStyle=index===0?'#a8dede':'#f0cbbd';
    ctx.fillRect(x,y-h,w,h);
    ctx.strokeStyle=index===0?teal:brick;
    ctx.strokeRect(x,y-h,w,h);
    label(ctx,index===0?'AP × PB':'CP × PD',[x,y+24]);
  });
  canvas.setAttribute('aria-label','Rectangles with equal areas, each '+(chords[0].front*chords[0].back).toFixed(3)+' square units');
}

function render() {
  const distance=get('offset').valueAsNumber;
  const first=get('angle-a').valueAsNumber;
  const second=get('angle-c').valueAsNumber;
  const proof=Number(get('proof').value);
  const p=[distance,0];
  const ab=lineFrom(p,first*pi/180);
  const cd=lineFrom(p,second*pi/180);
  for(const [id,value] of [['offset',distance.toFixed(1)+' units'],['angle-a',first+'°'],['angle-c',second+'°']]){
    get(id+'-value').textContent=value;
    get(id).setAttribute('aria-valuetext',value);
  }
  drawCircle(p,ab,cd,proof);
  drawAreas([ab,cd]);
  get('values').replaceChildren(...[ab,cd].map((chord,index)=>{
    const tr=document.createElement('tr');
    const title=document.createElement('th');
    title.scope='row';
    title.textContent=index===0?'AB':'CD';
    const lengths=document.createElement('td');
    lengths.textContent=chord.front.toFixed(3)+' and '+chord.back.toFixed(3);
    const product=document.createElement('td');
    product.textContent=(chord.front*chord.back).toFixed(3);
    tr.append(title,lengths,product);
    return tr;
  }));
  get('reason').textContent=[
    'Both products remain equal as you turn the chords. Moving P changes their common value.',
    'Angles APD and CPB are vertically opposite, so they are equal.',
    'Angles DAP and BCP subtend the same chord BD. Together with the equal angles at P, this gives △APD ∼ △CPB.',
    'Corresponding lengths give AP/CP = PD/PB. Cross-multiplying yields AP × PB = CP × PD. A diameter through P has segment lengths 5 − OP and 5 + OP. Their product is 25 − OP².',
  ][proof];
}

for(const id of ['offset','angle-a','angle-c'])get(id).addEventListener('input',render);
get('proof').addEventListener('change',render);
const resize=new ResizeObserver(render);
for(const id of ['circle','areas'])resize.observe(get(id));
render();
