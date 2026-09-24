/* Tangible study objects for the whole Primer. Coordinates are genuine 3D;
 * abstraction/context labels deliberately distinguish objects from simulations.
 * Lesson bindings are authored in data/module-models.json. */
(function () {
  'use strict';
  const TAU = 2 * Math.PI;
  const registered = new Map();
  const range = (key, label, min, max, step, unit = '') => ({key, label, min, max, step, unit});
  const choice = (key, label, options) => ({key, label, options: options.map(([value, text]) => ({value, label: text}))});
  const radians = degrees => degrees * Math.PI / 180;
  const add = (a, b) => a.map((v, i) => v + b[i]);
  const multiply = (a, n) => a.map(v => v * n);
  const lerp = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
  const fmt = (x, places = 2) => Number(x.toFixed(places)).toString();
  const rotateZ = (p, angle) => [p[0] * Math.cos(angle) - p[1] * Math.sin(angle), p[0] * Math.sin(angle) + p[1] * Math.cos(angle), p[2]];
  const colors = {wood: '#99704b', paper: '#e7dfc7', metal: '#83949a', soil: '#826552', pale: '#b9c8c4'};

  function cylinder(g, center, radius, height, color, options = {}) {
    const count = 20;
    const ring = (y) => Array.from({length: count}, (_, i) => [center[0] + radius * Math.cos(i * TAU / count), center[1] + y, center[2] + radius * Math.sin(i * TAU / count)]);
    const low = ring(-height / 2), high = ring(height / 2);
    for (let i = 0; i < count; i++) g.polygon([low[i], low[(i + 1) % count], high[(i + 1) % count], high[i]], color, options);
    if (!options.open) g.polygon(high, color, options);
    g.polygon([...low].reverse(), color, options);
  }
  function ellipsoid(g, center, radii, color, options = {}) {
    g.mesh((u, v) => {
      const polar = Math.PI * u, azimuth = TAU * v;
      return [center[0] + radii[0] * Math.sin(polar) * Math.cos(azimuth), center[1] + radii[1] * Math.cos(polar), center[2] + radii[2] * Math.sin(polar) * Math.sin(azimuth)];
    }, 8, 16, color, {stroke: false, ...options});
  }
  function beam(g, a, b, width, color) {
    // A square prism, with its four longitudinal faces in real world space.
    const delta = b.map((v, i) => v - a[i]), length = Math.hypot(...delta);
    const axis = delta.map(v => v / length);
    const helper = Math.abs(axis[1]) < .9 ? [0, 1, 0] : [1, 0, 0];
    const side = [axis[1] * helper[2] - axis[2] * helper[1], axis[2] * helper[0] - axis[0] * helper[2], axis[0] * helper[1] - axis[1] * helper[0]];
    const sideLength = Math.hypot(...side);
    const unit = side.map(v => v / sideLength);
    const normal = [axis[1] * unit[2] - axis[2] * unit[1], axis[2] * unit[0] - axis[0] * unit[2], axis[0] * unit[1] - axis[1] * unit[0]];
    const corners = point => [[-1,-1], [1,-1], [1,1], [-1,1]].map(([s, n]) => point.map((v, i) => v + (s * unit[i] + n * normal[i]) * width / 2));
    const start = corners(a), end = corners(b);
    start.forEach((p, i) => g.polygon([p, start[(i + 1) % 4], end[(i + 1) % 4], end[i]], color));
    g.polygon(start, color); g.polygon(end, color);
  }
  function base(g, size = [3.4, .1, 2.3]) { g.box([0, -1, 0], size, colors.paper); }
  function tree(g, x, z, height = 1) {
    cylinder(g, [x, -.8 + height * .36, z], .055, height * .7, colors.wood);
    ellipsoid(g, [x, -.7 + height, z], [.28, .42, .28], g.colors.green);
  }
  function person(g, x, z, color, height = .75) {
    const feet = -.9;
    g.sphere([x, feet + height * .91, z], height * .12, colors.wood);
    beam(g, [x, feet + height * .7, z], [x, feet + height * .38, z], height * .18, color);
    beam(g, [x, feet + height * .38, z], [x - height * .1, feet, z], height * .075, color);
    beam(g, [x, feet + height * .38, z], [x + height * .1, feet, z], height * .075, color);
    beam(g, [x - height * .21, feet + height * .38, z], [x, feet + height * .65, z], height * .07, color);
    beam(g, [x + height * .21, feet + height * .38, z], [x, feet + height * .65, z], height * .07, color);
  }
  function house(g, x, z, width = .6, height = .5) {
    g.box([x, -.9 + height / 2, z], [width, height, width * .8], colors.paper);
    const bottom = -.9 + height, top = bottom + width * .42;
    const front = z + width * .45, back = z - width * .45;
    g.polygon([[x-width*.6,bottom,front],[x,top,front],[x,top,back],[x-width*.6,bottom,back]], g.colors.coral);
    g.polygon([[x,top,front],[x+width*.6,bottom,front],[x+width*.6,bottom,back],[x,top,back]], colors.wood);
    g.polygon([[x-width*.6,bottom,front],[x,top,front],[x+width*.6,bottom,front]], g.colors.coral);
    g.box([x, -.9 + height * .3, z + width * .405], [width * .18, height * .6, .015], g.colors.blue);
  }
  function result(readout, note, labels, g) {
    return {readout, note, legend: labels.map(([label, color]) => ({label, color: color || g.colors.blue}))};
  }
  const families = Object.create(null);
  function define(id, title, initial, controls, build) { families[id] = {title, initial, controls, build}; }

  define('unit-blocks', 'Counting blocks', {count: 12, group: 4}, [range('count', 'Number of blocks', 1, 30, 1), range('group', 'Blocks in each row', 1, 10, 1)], (s, g) => {
    for (let i = 0; i < s.count; i++) g.box([(i % s.group - (s.group-1)/2)*.4, -.68, (Math.floor(i/s.group) - 1)*.4], [.34,.34,.34], i % 2 ? g.colors.teal : g.colors.blue);
    const rows = Math.floor(s.count / s.group), remainder = s.count % s.group;
    g.label([0,.04,-.8], `${s.count} equal blocks`);
    return result(`${s.count} blocks arranged in rows of ${s.group}: ${rows} complete rows and ${remainder} left over. Rearranging a fixed count changes its grouping, not its total.`, 'Equal-sized physical counters. A row arrangement is one concrete example; it does not prove a general arithmetic identity.', [['Blue and teal: equal units']], g);
  });

  define('balance', 'Equal-arm balance', {left: 3, right: 3}, [range('left', 'Left-hand units', 1, 6, 1), range('right', 'Right-hand units', 1, 6, 1)], (s, g) => {
    base(g); cylinder(g,[0,-.25,0],.1,1.4,colors.metal);
    const angle = radians((s.left - s.right) * 4), end = x => add([0,.45,0], rotateZ([x,0,0],angle));
    beam(g,end(-1.12),end(1.12),.1,colors.wood);
    for (const [x,n,color] of [[-1,s.left,g.colors.blue],[1,s.right,g.colors.coral]]) {
      const anchor=end(x), tray=[anchor[0],anchor[1]-.6,0];
      [-.25,.25].forEach(z => g.line([anchor,[tray[0],tray[1],z]],colors.metal));
      cylinder(g,tray,.32,.06,colors.metal);
      for(let i=0;i<n;i++) g.box([tray[0]+(i%2-.5)*.18,tray[1]+.13+Math.floor(i/2)*.15,0],[.15,.13,.15],color);
    }
    g.label([-1,.95,0],`${s.left} units`,g.colors.blue);g.label([1,.95,0],`${s.right} units`,g.colors.coral);
    return result(`Equal arms compare ${s.left} and ${s.right} equal masses. ${s.left===s.right?'The loads balance.':(s.left>s.right?'The left load is heavier.':'The right load is heavier.')} Difference: ${Math.abs(s.left-s.right)} units.`, 'The beam angle is an exaggerated comparison indicator, not a solved equilibrium angle. For ethical or logical topics, the balance is an object used to discuss comparison; it cannot measure fairness or truth.', [['Blue: left load',g.colors.blue],['Coral: right load',g.colors.coral]],g);
  });

  define('surface', 'Coordinate surface', {shape:'bowl',height:1}, [choice('shape','Example surface',[['bowl','Bowl: z = x² + y²'],['saddle','Saddle: z = x² − y²'],['plane','Plane: z = x + y']]),range('height','Vertical scale',.25,1.5,.25)], (s,g)=>{
    const fn=(x,y)=>s.height*(s.shape==='bowl'?(x*x+y*y):s.shape==='saddle'?(x*x-y*y):(x+y));
    g.mesh((u,v)=>{const x=(u-.5)*2.2,y=(v-.5)*2.2;return [x,fn(x,y),y];},16,16,g.colors.teal,{opacity:.72});
    g.arrow([-1.5,0,0],[1.5,0,0],g.colors.blue);g.arrow([0,0,-1.5],[0,0,1.5],g.colors.coral);g.arrow([0,-1,0],[0,1.5,0],g.colors.ink);
    g.label([1.5,0,0],'x',g.colors.blue);g.label([0,0,1.5],'y',g.colors.coral);g.label([0,1.5,0],'z');
    return result(`${s.shape==='bowl'?'Bowl':s.shape==='saddle'?'Saddle':'Plane'} surface; vertical scale ${s.height}. Rotate to distinguish the two horizontal coordinates from height. Compare cross-sections when one coordinate is held fixed.`, 'A sampled graph of an explicitly chosen two-variable function. Height is a dependent value, not an additional input. The mesh is an example for reasoning about space and functions, not a complete representation of this lesson’s abstract objects.',[['Teal: function values',g.colors.teal],['Axes: x, y and vertical z',g.colors.ink]],g);
  });

  define('urn','Probability urn',{blue:6,spread:1},[range('blue','Blue balls out of ten',0,10,1),range('spread','Open vessel',0,1,.25)],(s,g)=>{
    cylinder(g,[0,-.28,0],.87,1.25,colors.pale,{open:true,opacity:.13});
    for(let i=0;i<10;i++){const a=i*2.4;g.sphere([Math.cos(a)*(.32+s.spread*.3),-.68+Math.floor(i/4)*.28,Math.sin(a)*(.32+s.spread*.3)],.13,i<s.blue?g.colors.blue:g.colors.coral);}
    g.label([0,1,0],`${s.blue} blue · ${10-s.blue} coral`);
    return result(`There are ${s.blue} blue balls among 10 equally selectable balls. P(blue) = ${s.blue}/10 = ${s.blue*10}%. Opening the display changes visibility, not the count or probability.`, 'A finite, equally likely sampling example. Positions are fixed to make the inventory inspectable; this does not simulate mixing, random draws, or every probability distribution.',[['Blue: selected category',g.colors.blue],['Coral: other category',g.colors.coral]],g);
  });

  define('book','Bound book',{opening:110,pages:4},[range('opening','Opening angle',30,160,10,'°'),range('pages','Visible page layers',2,8,1)],(s,g)=>{
    const a=radians((180-s.opening)/2),length=1.13;
    for(const sign of [-1,1]){
      const corner=(x,z,y=0)=>[sign*x*Math.cos(a),x*Math.sin(a)+y,z];
      g.polygon([corner(0,-.8,-.035),corner(length,-.8,-.035),corner(length,.8,-.035),corner(0,.8,-.035)],g.colors.blue);
      for(let i=0;i<s.pages;i++){
        const y=.025+i*.015;
        g.polygon([corner(.025,-.74,y),corner(length-.04,-.74,y),corner(length-.04,.74,y),corner(.025,.74,y)],colors.paper);
        if(i===s.pages-1)for(let line=0;line<7;line++)g.line([corner(.18,-.5+line*.15,y+.005),corner(.91,-.5+line*.15,y+.005)],colors.metal,{width:1.3});
      }
    }
    cylinder(g,[0,-.035,0],.055,.15,g.colors.blue);
    g.label([0,-.18,.9],'Spine');g.label([1.15,.6,-.7],'Page surface');
    return result(`Book opened to ${s.opening}°. ${s.pages} page layers are separated on each side. Turn the object to inspect the spine, facing pages, and the sequence of surfaces that carry writing.`, 'A physical model of a bound book; the marks indicate lines rather than readable text. A book provides a context for language, interpretation, memory and evidence, but its geometry does not model their meaning.',[['Blue: binding',g.colors.blue],['Cream: page layers',colors.paper]],g);
  });

  define('press','Printing press',{separation:.5,rows:4},[range('separation','Platen clearance',.15,.8,.05),range('rows','Rows of type',2,6,1)],(s,g)=>{
    base(g);g.box([0,-.62,0],[1.85,.2,1.3],colors.wood);
    for(const x of [-.9,.9])beam(g,[x,-.7,-.4],[x,1.1,-.4],.16,colors.wood);
    beam(g,[-1,1.03,-.4],[1,1.03,-.4],.18,colors.wood);
    const top=-.36+s.separation;
    g.box([0,top,0],[1.5,.12,1.1],colors.metal);cylinder(g,[0,(top+1.03)/2,-.15],.07,1.03-top,colors.metal);
    g.box([0,-.49,0],[1.4,.025,1.03],colors.paper);
    for(let r=0;r<s.rows;r++)for(let c=0;c<7;c++)g.box([-.54+c*.18,-.43,-.4+r*.14],[.12,.07,.09],g.colors.ink);
    g.label([.98,.42,0],'Platen');g.label([-1,-.3,.55],'Type bed');
    return result(`${s.rows} rows of raised type sit above a sheet; platen clearance is ${fmt(s.separation)} model units. Rotate underneath the platen to inspect how flat type, paper and pressure align.`, 'A simplified platen press. Type blocks are not a transcription, and the model omits inking, screw mechanics and historical variations. Its physical arrangement supports discussion of reproducible texts; it does not reproduce a specific historical press.',[['Brown: support frame',colors.wood],['Dark blocks: raised type',g.colors.ink]],g);
  });

  define('stage','Speaking and performance space',{audience:5,width:2},[range('audience','Audience seats',3,9,1),range('width','Stage width',1.5,3,.25)],(s,g)=>{
    base(g,[4,.1,3.2]);g.box([0,-.82,-.65],[s.width,.25,1],colors.wood);
    person(g,0,-.7,g.colors.coral,1.2);
    for(let i=0;i<s.audience;i++){const x=(i-(s.audience-1)/2)*.32,z=.85;g.box([x,-.55,z],[.25,.08,.28],g.colors.blue);g.box([x,-.4,z+.12],[.25,.3,.06],g.colors.blue);}
    g.arrow([0,-.05,-.55],[0,-.05,.75],g.colors.gold);
    g.label([0,.65,-.65],'Speaker / performer',g.colors.coral);g.label([0,-.2,1.35],'Audience',g.colors.blue);
    return result(`Stage width ${s.width} model units; ${s.audience} audience seats. Inspect the distance, sightline and orientation between a performer and listeners.`, 'A physical communication setting. The arrow indicates the intended audience, not simulated sound, attention or persuasion. Seat count does not predict learning or social response.',[['Coral: performer',g.colors.coral],['Blue: audience seating',g.colors.blue]],g);
  });

  define('lever','Lever and fulcrum',{load:3,arm:1},[range('load','Load force',1,6,1,' N'),range('arm','Effort arm',.5,1.5,.25,' m')],(s,g)=>{
    base(g);g.polygon([[-.3,-.9,-.3],[.3,-.9,-.3],[0,-.28,-.3]],colors.metal);g.polygon([[-.3,-.9,.3],[.3,-.9,.3],[0,-.28,.3]],colors.metal);beam(g,[-1,-.26,0],[s.arm,-.26,0],.11,colors.wood);
    g.box([-1,-.2+s.load*.04,0],[.25,s.load*.08,.3],g.colors.blue);g.arrow([-1,.45+s.load*.08,0],[-1,-.16+s.load*.08,0],g.colors.blue);g.arrow([s.arm,.72,0],[s.arm,-.19,0],g.colors.coral);g.label([0,-.78,.45],'Fulcrum');g.label([-1,.78+s.load*.08,0],`${s.load} N`,g.colors.blue);
    return result(`With a 1 m load arm, the load moment is ${s.load} N·m. To balance it using a ${s.arm} m effort arm, effort = ${s.load}/${s.arm} = ${fmt(s.load/s.arm)} N.`, 'Ideal static lever with a massless rigid beam, vertical forces and no friction. Arrow lengths identify forces and do not encode their magnitude. Changing the effort arm changes required effort; the lesson’s other forces and constraints are outside this example.',[['Blue: load force',g.colors.blue],['Coral: balancing effort',g.colors.coral]],g);
  });

  define('pendulum','Pendulum',{length:1.4,angle:30},[range('length','String length',.8,2,.2,' m'),range('angle','Angle from vertical',-60,60,10,'°')],(s,g)=>{
    const pivot=[0,1.15,0],a=radians(s.angle),bob=[s.length*Math.sin(a),1.15-s.length*Math.cos(a),0];
    beam(g,[-1.4,1.3,0],[1.4,1.3,0],.1,colors.wood);g.line([pivot,bob],g.colors.ink,{width:2.5});g.sphere(bob,.18,g.colors.coral);g.sphere(pivot,.06,colors.metal);
    g.line([pivot,[0,1.15-s.length,0]],colors.metal,{dashed:true});g.line(Array.from({length:33},(_,i)=>{const t=-Math.PI/3+i*Math.PI/48;return[s.length*Math.sin(t),1.15-s.length*Math.cos(t),0];}),g.colors.teal,{opacity:.35});
    g.label(bob,'Bob',g.colors.coral);
    return result(`Length ${s.length} m, displacement ${s.angle}°. The bob is h = L(1 − cos θ) = ${fmt(s.length*(1-Math.cos(a)),3)} m above its lowest point.`, 'A static geometry of a taut, massless string and point-like bob. The angle control sets a position; it is not elapsed time and does not simulate damping or large-angle dynamics.',[['Coral: pendulum bob',g.colors.coral],['Dashed line: vertical reference',colors.metal]],g);
  });

  define('wave','Transverse wave on a rope',{amplitude:.4,cycles:2},[range('amplitude','Amplitude',.1,.7,.1),range('cycles','Cycles along the rope',1,4,1)],(s,g)=>{
    const points=Array.from({length:97},(_,i)=>[-1.6+i/30,s.amplitude*Math.sin(TAU*s.cycles*i/96),0]);
    g.line(points,g.colors.coral,{width:5});g.line([[-1.7,0,0],[1.7,0,0]],colors.metal,{dashed:true});
    for(const x of [-1.6,1.6])cylinder(g,[x,-.4,0],.065,1.2,colors.wood);
    points.filter((_,i)=>i%8===0).forEach(p=>g.sphere(p,.045,g.colors.coral));g.arrow([-.1,-.9,0],[.7,-.9,0],g.colors.blue);g.label([0,.98,0],'Transverse displacement');
    return result(`${s.cycles} full cycles occupy 3.2 length units; wavelength = ${fmt(3.2/s.cycles)}. Amplitude = ${s.amplitude}. Material displacement is perpendicular to the rope’s length.`, 'One frozen sinusoidal rope shape. This is a transverse example; sound in air is longitudinal. No wave speed, propagation in time or energy transport is simulated.',[['Coral: rope displacement',g.colors.coral],['Blue: along-rope direction',g.colors.blue]],g);
  });

  define('camera','Pinhole camera',{distance:2.4,depth:.7},[range('distance','Object distance',1.8,3.6,.3),range('depth','Pinhole-to-screen distance',.4,1,.1)],(s,g)=>{
    const h=.65,pinhole=[0,0,0],top=[-s.distance,h,0],bottom=[-s.distance,0,0],projected=[s.depth,-h*s.depth/s.distance,0];
    g.box([s.depth/2,0,0],[s.depth,1.2,.85],g.colors.blue,{opacity:.1});g.polygon([[s.depth,-.6,-.42],[s.depth,.6,-.42],[s.depth,.6,.42],[s.depth,-.6,.42]],colors.paper,{opacity:.8});
    g.arrow(bottom,top,g.colors.coral);g.arrow([s.depth,0,0],projected,g.colors.coral);g.sphere(pinhole,.035,g.colors.ink);g.line([top,pinhole,projected],g.colors.gold);g.line([bottom,pinhole,[s.depth,0,0]],g.colors.gold);
    g.label(top,'Object',g.colors.coral);g.label([0,.73,0],'Pinhole');g.label([s.depth,-.72,0],'Image screen');
    return result(`Object height ${h}; distance ${s.distance}; camera depth ${s.depth}. Image height = −${h} × ${s.depth}/${s.distance} = ${fmt(-h*s.depth/s.distance,3)}. The image is inverted.`, 'Ideal pinhole geometry, with no lens, diffraction or exposure calculation. Distances share arbitrary units. It explains projection and framing, not color perception or photographic image quality.',[['Coral: object and inverted image',g.colors.coral],['Gold: straight light rays',g.colors.gold]],g);
  });

  define('circuit','Simple electric circuit',{voltage:6,resistance:3,closed:'yes'},[range('voltage','Supply voltage',3,12,3,' V'),range('resistance','Resistance',1,6,1,' Ω'),choice('closed','Switch',[['yes','Closed'],['no','Open']])],(s,g)=>{
    base(g);const y=-.55;
    g.line([[-1,y,-.7],[-1,y,.7],[1,y,.7],[1,y,-.7],[.28,y,-.7]],g.colors.blue,{width:4});g.line([[-1,y,-.7],[-.3,y,-.7]],g.colors.blue,{width:4});
    g.line([[-.3,y,-.7],[.28,s.closed==='yes'?y:y+.38,-.7]],g.colors.coral,{width:4});g.box([-1,y+.13,0],[.28,.3,.45],g.colors.gold);g.box([1,y+.13,0],[.25,.28,.5],g.colors.coral);
    g.label([-1,.07,0],`${s.voltage} V`,g.colors.gold);g.label([1,.07,0],`${s.resistance} Ω`,g.colors.coral);g.label([0,.13,-.7],s.closed==='yes'?'Closed switch':'Open switch');
    return result(s.closed==='yes'?`Closed ideal circuit: I = V/R = ${s.voltage}/${s.resistance} = ${fmt(s.voltage/s.resistance)} A. Power in the resistor = ${fmt(s.voltage*s.voltage/s.resistance)} W.`:'Open switch: this ideal circuit has no complete current path, so current is zero.', 'Ideal DC source, ideal wires and a single ohmic resistor. Components are enlarged to expose their connections. Heating, battery limits, contact resistance and transient effects are omitted; this is not a wiring safety guide.',[['Gold: voltage source',g.colors.gold],['Coral: resistor and switch',g.colors.coral]],g);
  });

  define('particles','Particle chamber',{state:'solid',count:18},[choice('state','Arrangement',[['solid','Ordered solid'],['liquid','Disordered liquid'],['gas','Separated gas']]),range('count','Visible particles',6,24,6)],(s,g)=>{
    g.box([0,0,0],[2.2,1.9,1.8],colors.pale,{opacity:.07});
    for(let i=0;i<s.count;i++){
      const solid=[(i%4-1.5)*.34,(Math.floor(i/4)%3-1)*.34,(Math.floor(i/12)-.5)*.34];
      const liquid=[Math.sin(i*2.4)*.72,-.55+Math.floor(i/8)*.24,Math.cos(i*1.8)*.59];
      const gas=[Math.sin(i*2.4)*.95,Math.cos(i*1.6)*.75,Math.sin(i*3.1+.4)*.7];
      g.sphere(s.state==='solid'?solid:s.state==='liquid'?liquid:gas,.11,s.state==='gas'?g.colors.gold:g.colors.teal);
    }
    return result(`${s.count} visible particles in a ${s.state} arrangement. ${s.state==='solid'?'An ordered pattern preserves neighboring positions.':s.state==='liquid'?'Particles remain close while the illustrated positions lack a repeating lattice.':'Particles are shown more widely separated throughout the chamber.'}`, 'Static schematic, with greatly enlarged particles and intentionally simplified density. It does not calculate phase transitions, molecular motion, temperature or pressure. Not every solid is crystalline.',[['Particles: equal illustrative units',s.state==='gas'?g.colors.gold:g.colors.teal],['Transparent box: viewing chamber',colors.pale]],g);
  });

  define('plant','Plant and root system',{leaves:6,roots:'show'},[range('leaves','Leaf count',2,8,2),choice('roots','Below-ground view',[['show','Expose roots'],['hide','Show soil surface']])],(s,g)=>{
    cylinder(g,[0,-.76,0],.7,.35,colors.soil,{opacity:s.roots==='show'?.12:1});cylinder(g,[0,.02,0],.045,1.35,g.colors.green);
    for(let i=0;i<s.leaves;i++){const a=i*2.4,y=-.35+i*.17,tip=[Math.cos(a)*.58,y+.16,Math.sin(a)*.58];beam(g,[0,y,0],tip,.022,g.colors.green);ellipsoid(g,tip,[.27,.045,.13],i%2?g.colors.green:g.colors.teal);}
    if(s.roots==='show')for(let i=0;i<7;i++){const a=i*TAU/7;g.line([[0,-.61,0],[Math.cos(a)*.23,-.82,Math.sin(a)*.23],[Math.cos(a)*.56,-1.04,Math.sin(a)*.56]],colors.wood,{width:3});}
    g.label([0,.9,0],'Shoot');g.label([.65,-.9,0],'Root zone');
    return result(`${s.leaves} leaves are connected to one stem; roots are ${s.roots==='show'?'exposed below':'concealed by'} the soil surface. Rotate to trace the connection from roots to stem to leaves.`, 'A generic plant, with simplified branching and leaves. Leaf count is an inspection control, not a model of growth rate, photosynthesis, climate or a particular species.',[['Green: stem and leaves',g.colors.green],['Brown: soil and roots',colors.soil]],g);
  });

  define('habitat','Habitat cross-section',{trees:3,water:.3},[range('trees','Trees in the scene',1,5,1),range('water','Water depth',.15,.6,.15)],(s,g)=>{
    g.box([-.55,-.95,0],[1.9,.3,2.1],colors.soil);g.box([1,-1.03+s.water/2,0],[1.1,s.water,2.1],g.colors.blue,{opacity:.6});
    for(let i=0;i<s.trees;i++)tree(g,-1.1+(i%2)*.7,-.7+Math.floor(i/2)*.65,.7+i%2*.15);
    ellipsoid(g,[.15,-.43,.4],[.28,.16,.13],g.colors.coral);g.sphere([.37,-.32,.4],.11,g.colors.coral);for(const x of [-.02,.26])for(const z of [.34,.46])beam(g,[x,-.47,z],[x,-.79,z],.035,colors.wood);
    g.label([-1,.5,-.7],'Plants');g.label([1,.05,0],'Water');
    return result(`${s.trees} trees share a land-and-water setting; water depth is ${fmt(s.water)} model units. Inspect the boundary between water, soil and above-ground life.`, 'A small physical setting, not a quantitative ecosystem. The tree and animal stand for organisms; species, scale, populations, food-web dynamics and environmental effects are not simulated.',[['Green: plants',g.colors.green],['Blue: water',g.colors.blue],['Coral: animal',g.colors.coral]],g);
  });

  define('cell','Cell cutaway',{separation:0,organelles:4},[range('separation','Separate internal structures',0,.8,.2),range('organelles','Visible mitochondria',2,6,1)],(s,g)=>{
    g.mesh((u,v)=>{const p=Math.PI*u,a=(.28+v*.76)*TAU;return[1.25*Math.sin(p)*Math.cos(a),.95*Math.cos(p),Math.sin(p)*Math.sin(a)];},10,18,g.colors.teal,{opacity:.13,stroke:false});
    ellipsoid(g,[-s.separation*.6,0,0],[.4,.37,.38],g.colors.plum);
    for(let i=0;i<s.organelles;i++){const a=i*TAU/s.organelles;const p=[Math.cos(a)*(.7+s.separation),Math.sin(a)*.52,Math.cos(a+.8)*.44];ellipsoid(g,p,[.19,.1,.12],g.colors.gold);g.line([add(p,[-.12,0,0]),add(p,[-.05,.03,.015]),add(p,[.02,-.025,-.01]),add(p,[.12,0,0])],colors.wood,{width:2});}
    g.label([-.3,.6,0],'Nucleus',g.colors.plum);g.label([1.2,.75,.25],'Cell boundary',g.colors.teal);
    return result(`A cutaway exposes one nucleus and ${s.organelles} mitochondria. Separation ${fmt(s.separation)} moves the structures apart for inspection.`, 'A schematic eukaryotic cell. The separation is an exploded view, not a biological process. Organelle counts, shapes, scale and positions are illustrative; membranes and all other cell machinery are omitted.',[['Teal: outer boundary',g.colors.teal],['Plum: nucleus',g.colors.plum],['Gold: mitochondria',g.colors.gold]],g);
  });

  define('dna','DNA double helix',{pairs:10,separation:0},[range('pairs','Visible base pairs',6,14,2),range('separation','Separate the strands',0,.6,.2)],(s,g)=>{
    const strands=[[],[]];
    for(let i=0;i<s.pairs;i++){
      const a=i*TAU/10.5,y=(i-(s.pairs-1)/2)*.2;
      const p=[.55*Math.cos(a)+s.separation,y,-.55*Math.sin(a)],q=[-.55*Math.cos(a)-s.separation,y,.55*Math.sin(a)];
      strands[0].push(p);strands[1].push(q);g.sphere(p,.055,g.colors.blue);g.sphere(q,.055,g.colors.coral);
      const mid=lerp(p,q,.5);beam(g,p,mid,.045,i%2?g.colors.gold:g.colors.green);beam(g,mid,q,.045,i%2?g.colors.plum:g.colors.teal);
    }
    g.line(strands[0],g.colors.blue,{width:4});g.line(strands[1],g.colors.coral,{width:4});
    g.label([.9,1.5,0],'Paired strands');
    return result(`${s.pairs} paired positions; idealized twist about 34.3° per pair (10.5 pairs per turn). Strand separation is ${fmt(s.separation)} model units. Rotate to see paired rungs and two continuous backbones.`, 'A schematic right-handed DNA helix, with simplified equal grooves and arbitrary colors. Separation is an inspection aid, not a replication simulation. This does not display atomic structure, a nucleotide sequence, gene function or DNA scale relative to a cell.',[['Blue / coral: backbones',g.colors.blue],['Colored rungs: paired bases',g.colors.gold]],g);
  });

  define('neuron','Neuron structure',{branches:5,signal:0},[range('branches','Dendrite branches',3,7,1),range('signal','Signal marker position',0,4,1)],(s,g)=>{
    ellipsoid(g,[-.8,0,0],[.35,.32,.3],g.colors.plum);g.sphere([-.8,0,.23],.12,g.colors.gold);
    for(let i=0;i<s.branches;i++){const a=i*TAU/s.branches,p=[-.8+Math.cos(a)*.72,Math.sin(a)*.65,Math.sin(a*2)*.2];beam(g,[-.8,0,0],p,.045,g.colors.plum);beam(g,p,add(p,[Math.cos(a+.4)*.22,Math.sin(a+.4)*.22,.15]),.025,g.colors.plum);}
    beam(g,[-.48,0,0],[1.5,0,0],.06,g.colors.blue);for(let i=0;i<4;i++)ellipsoid(g,[-.12+i*.4,0,0],[.15,.12,.12],colors.pale);
    g.sphere([-.35+s.signal*.45,.14,0],.07,g.colors.coral);beam(g,[1.5,0,0],[1.77,.25,.18],.04,g.colors.blue);beam(g,[1.5,0,0],[1.77,-.25,-.18],.04,g.colors.blue);
    g.label([-.85,.85,0],'Dendrites');g.label([.65,.5,0],'Axon');
    return result(`${s.branches} dendrite branches surround the cell body. Signal marker step ${s.signal} of 4 follows the axon toward its terminals.`, 'A generic neuron with exaggerated myelin segments. Moving the marker illustrates direction only; it does not compute action potentials, synaptic transmission, cognition or individual mental states.',[['Plum: cell body and dendrites',g.colors.plum],['Blue: axon',g.colors.blue],['Coral: explanatory signal marker',g.colors.coral]],g);
  });

  define('molecule','Molecular shapes',{molecule:'water',spacing:1},[choice('molecule','Molecule',[['water','Water · H₂O'],['carbon-dioxide','Carbon dioxide · CO₂'],['methane','Methane · CH₄']]),range('spacing','Display bond length',.8,1.3,.1)],(s,g)=>{
    const water=s.molecule==='water',co=s.molecule==='carbon-dioxide';const origin=[0,0,0];
    g.sphere(origin,.24,water?g.colors.coral:g.colors.ink);
    const a=radians(104.5/2);const points=water?[[-Math.sin(a),Math.cos(a),0],[Math.sin(a),Math.cos(a),0]]:co?[[-1,0,0],[1,0,0]]:[[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]].map(p=>multiply(p,1/Math.sqrt(3)));
    for(const p of points){const end=multiply(p,s.spacing);beam(g,origin,end,.065,colors.metal);g.sphere(end,co?.21:.13,co?g.colors.coral:colors.paper);}
    return result(`${water?'Water: bent, H–O–H angle about 104.5°.':co?'Carbon dioxide: linear, O–C–O angle 180°.':'Methane: tetrahedral, H–C–H angles about 109.5°.'} Display bond length ${s.spacing} changes spacing only.`, 'Ball-and-stick geometry. Atom radii, bond lengths and colors are display conventions; the spacing slider is not bond vibration, pressure or a chemical reaction. Electron density and multiple-bond detail are omitted.',[['Coral: oxygen',g.colors.coral],['Dark: carbon; cream: hydrogen',g.colors.ink]],g);
  });

  define('lattice','Crystal lattice',{cells:2,spacing:.65},[range('cells','Cells along each axis',1,3,1),range('spacing','Lattice spacing',.45,.85,.1)],(s,g)=>{
    const n=s.cells;
    const pos=(x,y,z)=>[(x-n/2)*s.spacing,(y-n/2)*s.spacing,(z-n/2)*s.spacing];
    for(let x=0;x<=n;x++)for(let y=0;y<=n;y++)for(let z=0;z<=n;z++){
      const p=pos(x,y,z);g.sphere(p,.075,g.colors.blue);if(x<n)g.line([p,pos(x+1,y,z)],colors.metal,{width:1});if(y<n)g.line([p,pos(x,y+1,z)],colors.metal,{width:1});if(z<n)g.line([p,pos(x,y,z+1)],colors.metal,{width:1});
    }
    return result(`${n} × ${n} × ${n} simple-cubic cells with ${(n+1)**3} visible corner sites. Spacing ${s.spacing}; block side ${fmt(n*s.spacing)} and volume ${fmt((n*s.spacing)**3,3)} cubic model units.`, 'A finite simple-cubic lattice used to inspect repetition and three spatial directions. Corner sites are shared by neighboring cells in an extended crystal; visible-site count is not atoms per unit cell. It does not represent every material or calculate material properties.',[['Blue: lattice sites',g.colors.blue],['Gray: lattice connections',colors.metal]],g);
  });

  define('laboratory','Laboratory vessels',{fill:.4,tubes:3},[range('fill','Liquid fill fraction',.2,.8,.2),range('tubes','Sample tubes',2,5,1)],(s,g)=>{
    base(g);cylinder(g,[-.8,-.15,0],.5,1.35,colors.pale,{opacity:.15,open:true});cylinder(g,[-.8,-.78+s.fill*.6,0],.47,s.fill*1.2,g.colors.blue,{opacity:.65});
    g.box([.8,-.25,0],[1.15,.06,.55],colors.wood);g.box([.8,-.8,0],[1.15,.06,.55],colors.wood);
    for(let i=0;i<s.tubes;i++){const x=.3+i*.24;cylinder(g,[x,-.2,0],.075,1.2,colors.pale,{opacity:.25,open:true});cylinder(g,[x,-.72+s.fill*.4,0],.06,s.fill*.8,i%2?g.colors.coral:g.colors.teal,{opacity:.75});}
    for(let i=1;i<5;i++)g.line([[-1.32,-.8+i*.23,.06],[-1.14,-.8+i*.23,.06]],g.colors.ink,{width:1.2});
    g.label([-.8,.76,0],'Measured sample');g.label([.8,.68,0],'Comparison samples');
    return result(`Main vessel fill ${Math.round(s.fill*100)}%; ${s.tubes} sample tubes. Rotate to compare vessel walls, liquid levels and separate sample positions.`, 'A schematic bench arrangement; the graduations are relative markers, not calibrated units. Liquid color does not identify a substance or pH. This is a physical context for measurement and comparison, not a chemistry experiment or a procedural instruction.',[['Blue: main sample',g.colors.blue],['Teal and coral: comparison samples',g.colors.teal]],g);
  });

  define('computer','Computer architecture',{separation:.3,memory:4},[range('separation','Exploded-view spacing',0,.9,.3),range('memory','Visible memory packages',2,6,1)],(s,g)=>{
    g.box([0,-.7,0],[2.8,.09,1.8],g.colors.green);g.box([-.55,-.43+s.separation,0],[.68,.15,.68],g.colors.ink);
    for(let i=0;i<6;i++)g.box([-.8+i*.1,-.27+s.separation,0],[.045,.18,.64],colors.metal);
    for(let i=0;i<s.memory;i++)g.box([.5,-.54+s.separation*.4,-.7+i*.25],[.5,.14,.17],g.colors.blue);
    g.box([-1,-.47,-.61],[.43,.32,.3],colors.metal);g.box([-1,-.47,.61],[.43,.32,.3],colors.metal);
    for(let i=0;i<4;i++)g.line([[-.15,-.64,i*.09-.14],[.18,-.64,i*.09-.14],[.18,-.64,-.6+i*.25],[.48,-.64,-.6+i*.25]],g.colors.gold,{width:1.6});
    g.label([-.6,.35+s.separation,0],'Processor + heat sink');g.label([.65,.05,0],'Memory');
    return result(`${s.memory} memory packages surround a processor location. Exploded spacing ${s.separation} lifts components above the board so connections and support surfaces remain visible.`, 'Illustrative physical hardware. Trace placement and memory count are not a functional circuit design. Algorithms, software abstractions and complexity live above this physical implementation; the board does not model their semantics or performance.',[['Green: circuit board',g.colors.green],['Blue: memory packages',g.colors.blue],['Gold: illustrative traces',g.colors.gold]],g);
  });

  define('network','Connected computers',{clients:4,topology:'star'},[range('clients','Client devices',3,6,1),choice('topology','Cable arrangement',[['star','Central switch'],['ring','Closed ring']])],(s,g)=>{
    const points=Array.from({length:s.clients},(_,i)=>[1.1*Math.cos(i*TAU/s.clients),-.6,1.1*Math.sin(i*TAU/s.clients)]);
    for(const p of points){g.box(add(p,[0,.2,0]),[.38,.3,.16],g.colors.blue);g.box(add(p,[0,.04,.1]),[.44,.06,.3],colors.metal);}
    if(s.topology==='star'){g.box([0,-.62,0],[.5,.15,.4],g.colors.coral);for(const p of points)g.line([[0,-.67,0],p],g.colors.gold,{width:2.5});}else points.forEach((p,i)=>g.line([p,points[(i+1)%points.length]],g.colors.gold,{width:2.5}));
    g.label([0,.35,0],s.topology==='star'?'Switch at center':'Ring links');
    return result(`${s.clients} client devices in a ${s.topology} arrangement; ${s.clients} visible cables. ${s.topology==='star'?'Each client has a direct cable to the central switch.':'Each client has two neighbors on the ring.'}`, 'A small physical network arrangement. Cables do not imply a protocol, packet route, security property or reliability guarantee. Spatial separation is for inspection and does not encode latency.',[['Blue: client devices',g.colors.blue],['Gold: links',g.colors.gold],['Coral: central switch, when shown',g.colors.coral]],g);
  });

  define('village','Settlement and shared space',{buildings:4,spacing:.85},[range('buildings','Buildings',3,6,1),range('spacing','Distance from shared center',.65,1.25,.2)],(s,g)=>{
    base(g,[3.7,.1,3.7]);cylinder(g,[0,-.89,0],.42,.035,colors.metal);
    for(let i=0;i<s.buildings;i++){const a=i*TAU/s.buildings;house(g,Math.cos(a)*s.spacing,Math.sin(a)*s.spacing,.55,.45);g.line([[0,-.92,0],[Math.cos(a)*s.spacing,-.92,Math.sin(a)*s.spacing]],colors.wood,{width:3});}
    g.label([0,.5,0],'Shared center');
    return result(`${s.buildings} buildings stand ${s.spacing} model units from a shared center. Inspect how paths connect private spaces to a common meeting place.`, 'An invented settlement used as a physical discussion setting. Building shapes do not identify a culture, period, religion, household structure or political system. Spacing changes geometry only; it does not predict social outcomes.',[['Cream and coral: buildings',colors.paper],['Gray: shared place',colors.metal]],g);
  });

  define('excavation','Archaeological excavation',{layers:4,cutaway:'open'},[range('layers','Depositional layers',2,5,1),choice('cutaway','View',[['open','Open trench'],['closed','Intact surface']])],(s,g)=>{
    const layerColors=[colors.soil,colors.wood,'#b49a77','#807466','#c4ac87'];
    for(let i=0;i<s.layers;i++){const y=-.8+i*.25;g.box([-.65,y,0],[.6,.23,1.7],layerColors[i]);g.box([.65,y,0],[.6,.23,1.7],layerColors[i]);g.box([0,y,-.65],[.7,.23,.4],layerColors[i]);if(s.cutaway==='closed')g.box([0,y,.15],[.7,.23,1.2],layerColors[i]);}
    if(s.cutaway==='open'){cylinder(g,[0,-.46,.03],.18,.28,g.colors.coral,{open:true});g.box([.03,-.06,-.05],[.29,.08,.2],colors.metal);}
    g.label([-.75,.7,0],'Layered deposits');g.label([0,-.95,.95],'Exposed section');
    return result(`${s.layers} horizontal layers in ${s.cutaway==='open'?'an open trench':'an intact block'}. Rotate to inspect the position of artifacts relative to boundaries between deposits.`, 'An invented, undisturbed stratigraphic example. Lower layers are earlier only when the sequence has not been overturned or cut by later activity. Artifact position alone does not establish an absolute date, identity or interpretation.',[['Earth colors: distinct deposits',colors.soil],['Coral / gray: example artifacts',g.colors.coral]],g);
  });

  define('ship','Sailing vessel',{cargo:4,sail:1},[range('cargo','Visible cargo crates',2,8,2),range('sail','Sail spread',.5,1,.25)],(s,g)=>{
    g.mesh((u,v)=>{const x=(u-.5)*3,a=Math.PI*v;return[x,-.55-.32*Math.sin(a)*(1-Math.abs(x/1.65)),.5*Math.cos(a)*(1-(x/1.65)**2)];},16,8,colors.wood);
    g.polygon([[-1.45,-.52,0],[-.85,-.52,-.4],[.85,-.52,-.4],[1.45,-.52,0],[.85,-.52,.4],[-.85,-.52,.4]],colors.paper);
    cylinder(g,[0,.2,0],.04,1.6,colors.wood);beam(g,[-.7*s.sail,.8,0],[.7*s.sail,.8,0],.035,colors.wood);g.mesh((u,v)=>[(u-.5)*1.4*s.sail,.8-v*.9,.18*Math.sin(u*Math.PI)*Math.sin(v*Math.PI)],8,8,colors.paper);
    for(let i=0;i<s.cargo;i++)g.box([-.85+(i%4)*.56,-.43,(Math.floor(i/4)-.5)*.36],[.2,.17,.2],g.colors.gold);
    g.label([0,1.2,0],'Sail');g.label([.75,-.25,.4],'Cargo');
    return result(`${s.cargo} crates and sail spread ${Math.round(s.sail*100)}%. Inspect how hull volume, deck space, mast and sail occupy different parts of a vessel.`, 'A generic historical sailing vessel, not a reconstruction of a specific culture or voyage. Sail spread changes visible area, not calculated propulsion. Trade routes, coercion, economic value and historical causes require other evidence.',[['Cream: sail and deck',colors.paper],['Gold: cargo',g.colors.gold]],g);
  });

  define('globe','Latitude and longitude globe',{latitude:30,longitude:30},[range('latitude','Latitude',-75,75,15,'°'),range('longitude','Longitude',-180,180,30,'°')],(s,g)=>{
    ellipsoid(g,[0,0,0],[1,1,1],g.colors.blue,{opacity:.14});
    const point=(lat,lon,r=1)=>[r*Math.cos(radians(lat))*Math.cos(radians(lon)),r*Math.sin(radians(lat)),r*Math.cos(radians(lat))*Math.sin(radians(lon))];
    for(const lat of [-60,-30,0,30,60])g.line(Array.from({length:49},(_,i)=>point(lat,i*7.5)),lat===0?g.colors.gold:colors.metal,{width:lat===0?2:1,opacity:.7});
    for(let lon=0;lon<360;lon+=30)g.line(Array.from({length:33},(_,i)=>point(-90+i*180/32,lon)),colors.metal,{width:1,opacity:.5});
    const p=point(s.latitude,s.longitude,1.04);g.sphere(p,.075,g.colors.coral);g.arrow([0,-1.25,0],[0,1.35,0],g.colors.ink);g.label([0,1.5,0],'North');g.label(multiply(p,1.2),'Position',g.colors.coral);
    return result(`Selected position: latitude ${s.latitude}°, longitude ${s.longitude}°. Latitude measures north/south angular displacement from the equator; longitude is measured around the polar axis from the chosen zero meridian.`, 'A spherical coordinate globe without coastlines, borders or a map projection. Radius is arbitrary. The zero meridian is the positive x direction in this model; choosing it is a coordinate convention.',[['Gold: equator',g.colors.gold],['Coral: selected position',g.colors.coral],['Gray: coordinate grid',colors.metal]],g);
  });

  define('landscape','Landform and water level',{height:.6,water:.2},[range('height','Terrain relief',.4,1,.2),range('water','Water elevation',-.2,.4,.2)],(s,g)=>{
    const terrain=(x,z)=>-.6+s.height*(.65*Math.exp(-((x+.6)**2+(z+.2)**2)*1.9)+.85*Math.exp(-((x-.5)**2+(z-.5)**2)*2.5));
    g.mesh((u,v)=>{const x=(u-.5)*3,z=(v-.5)*2.6;return[x,terrain(x,z),z];},20,20,colors.soil);
    g.polygon([[-1.5,s.water-.5,-1.3],[1.5,s.water-.5,-1.3],[1.5,s.water-.5,1.3],[-1.5,s.water-.5,1.3]],g.colors.blue,{opacity:.4,stroke:false});
    g.label([-.8,.7,-.1],'Higher ground');g.label([.9,-.5+s.water,1.3],'Level water surface');
    return result(`Terrain relief scale ${s.height}; water elevation ${fmt(s.water-.5)}. Rotate to inspect where a horizontal water surface intersects sloping ground; changing the level changes the submerged region.`, 'An invented static landform in arbitrary units. No erosion, fluid flow, real flood risk, climate response or geographic location is calculated.',[['Brown: land surface',colors.soil],['Blue: horizontal water surface',g.colors.blue]],g);
  });

  define('orbit','Circular orbit geometry',{phase:60,inclination:15},[range('phase','Orbital position',0,330,30,'°'),range('inclination','Orbital inclination',0,60,15,'°')],(s,g)=>{
    const a=radians(s.inclination),point=angle=>[1.35*Math.cos(angle),1.35*Math.sin(angle)*Math.sin(a),1.35*Math.sin(angle)*Math.cos(a)];
    g.sphere([0,0,0],.36,g.colors.gold);g.line(Array.from({length:65},(_,i)=>point(i*TAU/64)),g.colors.blue,{width:2});const p=point(radians(s.phase));g.sphere(p,.16,g.colors.teal);g.line([[0,0,0],p],colors.metal,{dashed:true});
    g.polygon([[-1.6,0,-1.6],[1.6,0,-1.6],[1.6,0,1.6],[-1.6,0,1.6]],colors.pale,{opacity:.1});g.label([0,.62,0],'Central body');
    return result(`Orbital position ${s.phase}°; plane inclination ${s.inclination}°. Radius remains 1.35 model units at every position in this circular example.`, 'Circular geometry with greatly exaggerated body sizes. The controls select position and plane orientation; they do not evolve time, calculate gravity or represent an actual planetary orbit. Seasons require axial tilt and are taught in the dedicated seasons model.',[['Gold: central body',g.colors.gold],['Teal: orbiting body',g.colors.teal],['Blue: circular path',g.colors.blue]],g);
  });

  define('telescope','Reflector telescope',{opening:.5,elevation:30},[range('opening','Tube radius',.3,.6,.1),range('elevation','Pointing elevation',10,60,10,'°')],(s,g)=>{
    base(g);const a=radians(s.elevation),transform=p=>add(rotateZ(p,a),[0,.05,0]);
    const start=transform([-1,0,0]),end=transform([1,0,0]);
    for(let i=0;i<24;i++){const p=i*TAU/24,q=(i+1)*TAU/24;g.polygon([[-1,s.opening*Math.cos(p),s.opening*Math.sin(p)],[1,s.opening*Math.cos(p),s.opening*Math.sin(p)],[1,s.opening*Math.cos(q),s.opening*Math.sin(q)],[-1,s.opening*Math.cos(q),s.opening*Math.sin(q)]].map(transform),g.colors.blue,{opacity:.3});}
    g.polygon(Array.from({length:24},(_,i)=>transform([-1,s.opening*Math.cos(i*TAU/24),s.opening*Math.sin(i*TAU/24)])),colors.metal);
    for(const z of [-.13,.13])g.line([transform([1.3,z,z]),transform([-.95,z,z]),transform([.3,0,0])],g.colors.gold,{width:1.5});
    beam(g,[0,-.85,0],[0,-.15,0],.12,colors.metal);beam(g,[0,-.65,0],[-.7,-.94,.5],.08,colors.metal);beam(g,[0,-.65,0],[.7,-.94,.5],.08,colors.metal);
    g.label(start,'Primary mirror');g.label(end,'Open aperture');
    return result(`Tube diameter ${fmt(s.opening*2)} and pointing elevation ${s.elevation}°. Aperture area is proportional to radius squared: πr² = ${fmt(Math.PI*s.opening*s.opening)} square model units.`, 'Simplified reflector telescope with straight guide rays and a schematic primary mirror. Mirror curvature, secondary optics, aberrations and image quality are not computed. A telescope is a measurement context for astronomy, not a model of the universe.',[['Blue: optical tube',g.colors.blue],['Gray: primary mirror and mount',colors.metal],['Gold: illustrative light paths',g.colors.gold]],g);
  });

  define('instrument','Plucked string instrument',{strings:4,length:1},[range('strings','Strings',3,6,1),range('length','Vibrating length scale',.6,1.2,.2)],(s,g)=>{
    ellipsoid(g,[0,-.4,0],[.62,.15,.7],colors.wood);ellipsoid(g,[0,-.32,-.35],[.43,.1,.35],colors.wood);g.box([0,-.24,-.95],[.23,.08,1.5*s.length],colors.wood);
    cylinder(g,[0,-.25,.08],.2,.018,g.colors.ink);g.box([0,-.17,.42],[.52,.05,.07],colors.metal);
    for(let i=0;i<s.strings;i++){const x=(i-(s.strings-1)/2)*.035;g.line([[x,-.12,.43],[x,-.12,-.6-1.1*s.length]],g.colors.gold,{width:1.2});}
    for(let i=0;i<7;i++){const z=-.4-i*.13*s.length;g.line([[-.115,-.185,z],[.115,-.185,z]],colors.metal,{width:1});}
    g.label([.8,-.1,.3],'Resonating body');g.label([0,.15,-1.5],'Strings');
    return result(`${s.strings} strings; length scale ${s.length}. Inspect the route from bridge across the body and along the neck. For an ideal taut string at fixed tension and mass per length, fundamental frequency varies inversely with vibrating length.`, 'A generic plucked instrument, not a specific musical tradition or exact acoustic simulation. The body and string spacing are schematic, and the activity produces no sound.',[['Brown: body and neck',colors.wood],['Gold: strings',g.colors.gold]],g);
  });

  define('architecture','Post-and-lintel pavilion',{bays:3,height:1.2},[range('bays','Structural bays',2,4,1),range('height','Column height',.8,1.6,.2)],(s,g)=>{
    base(g,[3.8,.1,2]);const spacing=2.8/s.bays;
    for(let i=0;i<=s.bays;i++)for(const z of [-.55,.55]){cylinder(g,[-1.4+i*spacing,-.9+s.height/2,z],.075,s.height,colors.paper);cylinder(g,[-1.4+i*spacing,-.89,z],.13,.09,colors.metal);}
    g.box([0,-.82+s.height,0],[3.1,.17,1.45],g.colors.coral);for(let i=0;i<s.bays;i++)g.line([[-1.4+i*spacing,-.93,0],[-1.4+(i+1)*spacing,-.93,0]],g.colors.blue,{width:3});
    g.label([0,s.height-.45,0],'Roof / lintel');g.label([1.4,-.2,.65],'Column');
    return result(`${s.bays} bays across a 2.8-unit span: each bay is ${fmt(2.8/s.bays)} units wide. Column height ${s.height}; compare rhythm, proportion, enclosure and the route of support to the ground.`, 'An invented post-and-lintel pavilion for spatial and design inspection. It is not a structural engineering calculation, a historical reconstruction or a standard for safe construction.',[['Cream: columns',colors.paper],['Coral: roof / lintel',g.colors.coral],['Blue: equal bay divisions',g.colors.blue]],g);
  });

  define('meeting','Shared discussion table',{seats:4,distance:1},[range('seats','Places at the table',3,8,1),range('distance','Seating radius',.8,1.2,.1)],(s,g)=>{
    base(g,[3.4,.1,3.4]);cylinder(g,[0,-.39,0],.63,.1,colors.wood);cylinder(g,[0,-.65,0],.07,.5,colors.metal);
    for(let i=0;i<s.seats;i++){const a=i*TAU/s.seats;person(g,Math.cos(a)*s.distance,Math.sin(a)*s.distance,i%2?g.colors.blue:g.colors.coral,.68);}
    g.box([0,-.31,0],[.25,.03,.35],colors.paper);g.label([0,.25,0],'Shared task / evidence');
    return result(`${s.seats} places around one table; seating radius ${s.distance}. Rotate to inspect facing positions, shared space, and access to the item in the center.`, 'A physical setting for discussing cooperation, participation and decision-making. Position does not represent social value, emotion, personality or power, and changing seat count does not model human behavior.',[['Brown: shared table',colors.wood],['Blue and coral: participants',g.colors.blue],['Cream: shared material',colors.paper]],g);
  });

  define('experiment','Two-condition experiment station',{distance:1,trial:1},[range('distance','Stimulus distance',.6,1.4,.2),range('trial','Highlighted trial',1,6,1)],(s,g)=>{
    base(g,[3.6,.1,2.4]);for(const [x,color] of [[-.8,g.colors.blue],[.8,g.colors.coral]]){
      g.box([x,-.7,-.4],[.55,.35,.12],color);g.box([x,-.88,.1+s.distance*.35],[.42,.08,.24],colors.metal);g.arrow([x,-.42,-.35],[x,-.42,.1+s.distance*.35],g.colors.gold);
      for(let i=1;i<=6;i++)g.sphere([x-.24+(i-1)*.095,-.84,.9],i===s.trial?.04:.025,i===s.trial?g.colors.gold:colors.metal);
    }
    g.label([-.8,.05,-.4],'Condition A',g.colors.blue);g.label([.8,.05,-.4],'Condition B',g.colors.coral);
    return result(`Trial ${s.trial} highlighted in each condition; equal stimulus distance ${s.distance} on both stations. Compare the physical arrangements and identify what would need to stay constant in a fair comparison.`, 'An invented experiment setup. The two conditions have no assigned treatment or measured outcomes. There are no human data or claims about psychology; the object supports reasoning about controlled comparisons, evidence and replication.',[['Blue / coral: comparison stations',g.colors.blue],['Gold: current trial marker and viewing guides',g.colors.gold]],g);
  });


  define('fraction-disk','Partitioned disk',{parts:'4',selected:1,separation:.1},[choice('parts','Equal parts',[['2','Halves'],['4','Quarters'],['8','Eighths']]),range('selected','Highlighted parts',1,8,1),range('separation','Separate the pieces',0,.3,.1)],(s,g)=>{
    const n=Number(s.parts),selected=Math.min(n,s.selected),radius=1;
    for(let i=0;i<n;i++){
      const a=i*TAU/n,b=(i+1)*TAU/n,mid=(a+b)/2,offset=[Math.cos(mid)*s.separation,0,Math.sin(mid)*s.separation],color=i<selected?g.colors.blue:colors.paper;
      const arc=Array.from({length:13},(_,j)=>add([Math.cos(a+(b-a)*j/12)*radius,.04,Math.sin(a+(b-a)*j/12)*radius],offset));
      const center=add([0,.04,0],offset);g.polygon([center,...arc],color);
      for(let j=0;j<12;j++)g.polygon([arc[j],arc[j+1],add(arc[j+1],[0,-.18,0]),add(arc[j],[0,-.18,0])],color);
      for(const edge of [arc[0],arc[12]])g.polygon([center,edge,add(edge,[0,-.18,0]),add(center,[0,-.18,0])],color);
    }
    return result(`${selected} of ${n} equal parts: ${selected}/${n} = ${fmt(selected/n)} = ${fmt(selected/n*100)}%. Each piece subtends ${360/n}°. Selecting more than ${n} highlights the whole disk.`, 'The pieces have equal angle, radius and thickness, so they have equal area and volume. Separation is an inspection aid and does not change the part-to-whole fraction. This represents one fixed whole.',[['Blue: selected parts',g.colors.blue],['Cream: other equal parts',colors.paper]],g);
  });

  define('clock','Clock face and hands',{hour:3,minute:0},[range('hour','Hour',0,11,1),range('minute','Minutes',0,55,5)],(s,g)=>{
    // The face is in the xy plane; a box frame and disk mesh expose its depth.
    g.mesh((u,v)=>{const a=TAU*u;return[Math.cos(a)*(1-v),Math.sin(a)*(1-v),0];},48,1,colors.paper);
    for(let i=0;i<12;i++){const a=i*TAU/12;g.line([[.87*Math.sin(a),.87*Math.cos(a),.025],[.97*Math.sin(a),.97*Math.cos(a),.025]],g.colors.ink,{width:2});}
    const m=s.minute*TAU/60,h=(s.hour+s.minute/60)*TAU/12;
    g.arrow([0,0,.05],[.78*Math.sin(m),.78*Math.cos(m),.05],g.colors.blue);g.arrow([0,0,.085],[.5*Math.sin(h),.5*Math.cos(h),.085],g.colors.coral);g.sphere([0,0,.08],.055,g.colors.ink);
    g.label([0,1.12,0],'12');g.label([1.1,0,0],'3');g.label([0,-1.12,0],'6');g.label([-1.1,0,0],'9');
    return result(`${s.hour||12}:${String(s.minute).padStart(2,'0')}. Minute-hand angle ${s.minute*6}° clockwise from 12; hour-hand angle ${fmt((s.hour+s.minute/60)*30)}°. The hour hand moves continuously as minutes increase.`, 'An analog twelve-hour display; depth separates the hands for inspection. This does not identify morning versus evening, a date, a time zone, or the duration of an event.',[['Blue: minute hand',g.colors.blue],['Coral: hour hand',g.colors.coral]],g);
  });

  define('stack','Stack of data cards',{cards:4,separation:.1},[range('cards','Cards on the stack',1,8,1),range('separation','Card separation',.02,.18,.04)],(s,g)=>{
    base(g);for(let i=0;i<s.cards;i++){const y=-.78+i*(.1+s.separation);g.box([0,y,0],[1.5,.09,1],i===s.cards-1?g.colors.coral:g.colors.blue);if(i===0||i===s.cards-1)g.label([.95,y,0],String(i+1),i===s.cards-1?g.colors.coral:g.colors.blue);}
    return result(`${s.cards} cards; card ${s.cards} is at the top. Increasing the count pushes a new highest-numbered card; decreasing it removes the top card first. The other cards preserve insertion order.`, 'A tangible LIFO stack example. Card spacing is for inspection. Programming values, stack frames, memory addresses and concurrency are not represented by physical card dimensions.',[['Coral: top card',g.colors.coral],['Blue: earlier cards',g.colors.blue]],g);
  });

  define('studio','Artist’s easel',{tilt:20,width:1.2},[range('tilt','Canvas tilt',0,30,10,'°'),range('width','Canvas width',.8,1.6,.2)],(s,g)=>{
    base(g);for(const x of [-.65,.65])beam(g,[x,-.95,0],[x*.25,1.05,-.2],.07,colors.wood);beam(g,[0,1,-.2],[0,-.95,-.9],.07,colors.wood);beam(g,[-.75,-.5,0],[.75,-.5,0],.08,colors.wood);
    const a=radians(s.tilt),point=(x,y,z)=>[x,y*Math.cos(a),z-y*Math.sin(a)];g.polygon([point(-s.width/2,-.45,.03),point(s.width/2,-.45,.03),point(s.width/2,.9,.03),point(-s.width/2,.9,.03)],colors.paper);
    g.polygon([point(-s.width*.35,-.22,.04),point(s.width*.35,-.22,.04),point(0,.53,.04)],g.colors.blue);g.sphere(point(-s.width*.2,.58,.04),.1,g.colors.gold);
    g.label([0,1.2,0],'Picture surface');
    return result(`Canvas width ${s.width}; tilt ${s.tilt}° from vertical. Rotate to distinguish the flat image from its support, and inspect how picture proportions and viewpoint affect the visible composition.`, 'A generic studio object with simple painted shapes. The colored marks are not a mixing model, an artwork attribution, or a rule for aesthetic judgment. Camera rotation changes your view, not the marks on the canvas.',[['Cream: picture surface',colors.paper],['Brown: easel structure',colors.wood]],g);
  });


  define('magnet','Bar magnet and field directions',{polarity:'normal',distance:1.2},[choice('polarity','Pole orientation',[['normal','North on the right'],['reversed','North on the left']]),range('distance','Field sampling distance',1,1.6,.2)],(s,g)=>{
    const sign=s.polarity==='normal'?1:-1;
    g.box([-.3,0,0],[.6,.32,.36],sign===1?g.colors.blue:g.colors.coral);g.box([.3,0,0],[.6,.32,.36],sign===1?g.colors.coral:g.colors.blue);
    for(const phi of [0,Math.PI/2])for(let i=0;i<16;i++){
      if(phi&&i%8===0)continue;
      const a=i*TAU/16,p=[s.distance*Math.cos(a),s.distance*.75*Math.sin(a)*Math.cos(phi),s.distance*.75*Math.sin(a)*Math.sin(phi)],r=Math.hypot(...p),n=p.map(x=>x/r);
      const field=n.map((v,j)=>sign*(3*v*n[0]-(j===0?1:0))),length=Math.hypot(...field);
      g.arrow(p,p.map((v,j)=>v+field[j]/length*.25),g.colors.teal,{width:1.8});
    }
    g.label([-.3,.42,0],sign===1?'S':'N',sign===1?g.colors.blue:g.colors.coral);g.label([.3,.42,0],sign===1?'N':'S',sign===1?g.colors.coral:g.colors.blue);
    return result(`North pole is on the ${sign===1?'right':'left'}. Field directions are sampled on two perpendicular planes at distance scale ${s.distance}. Reversing polarity reverses every field arrow.`, 'An ideal point-dipole direction field around a schematic bar magnet. All arrows have equal length, so they show direction rather than field strength. The point-dipole approximation is not an exact field close to a finite magnet; sampled arrows are not isolated magnetic poles or particle trajectories.',[['Coral: north pole',g.colors.coral],['Blue: south pole',g.colors.blue],['Teal: magnetic-field direction',g.colors.teal]],g);
  });

  define('detector','Layered particle detector',{cutaway:90,separation:0},[range('cutaway','Cutaway opening',60,180,30,'°'),range('separation','Separate detector layers',0,.3,.1)],(s,g)=>{
    const layerColors=[g.colors.teal,g.colors.gold,g.colors.plum],radii=[];
    for(let i=0;i<3;i++){
      const radius=.4+i*(.3+s.separation);radii.push(radius);
      g.mesh((u,v)=>{const a=radians(s.cutaway)+v*(TAU-radians(s.cutaway));return[radius*Math.cos(a),radius*Math.sin(a),(u-.5)*2.3];},10,24,layerColors[i],{opacity:.3});
    }
    g.line([[0,0,-1.65],[0,0,1.65]],g.colors.ink,{width:3});g.sphere([0,0,0],.065,g.colors.coral);
    const direction=[.8,.6,.4],transverse=Math.hypot(direction[0],direction[1]);g.line([[0,0,0],multiply(direction,radii[2]/transverse*1.12)],g.colors.coral,{width:2});
    for(const radius of radii)g.sphere(multiply(direction,radius/transverse),.035,g.colors.coral);
    g.label([-radii[0],.25,1.22],'Tracking layer',g.colors.teal);g.label([-radii[1],-.4,1.22],'Calorimeter',g.colors.gold);g.label([-radii[2],.55,1.22],'Outer detectors',g.colors.plum);
    return result(`Three concentric detector regions surround a beam axis; cutaway ${s.cutaway}°, extra layer spacing ${s.separation}. Rotate to inspect the path from the interaction point outward through the layers.`, 'A generic collider-detector arrangement inspired by layered tracking, calorimetry and outer particle detection. The red line is a straight inspection guide, not a reconstructed event or a predicted charged-particle trajectory. Materials, magnetic fields, response, endcaps and real detector dimensions are omitted.',[['Teal: tracking region',g.colors.teal],['Gold: calorimeter region',g.colors.gold],['Plum: outer detection region',g.colors.plum]],g);
  });

  define('interference','Two-slit optical bench',{gap:.35,distance:1.4},[range('gap','Slit separation',.25,.55,.1),range('distance','Slit-to-screen distance',1,2.2,.2)],(s,g)=>{
    const wavelength=.05,half=s.gap/2,slot=.025;
    g.box([-1,0,0],[.3,.18,.18],g.colors.coral);
    for(const [low,high] of [[-.8,-half-slot],[-half+slot,half-slot],[half+slot,.8]])g.box([0,(low+high)/2,0],[.055,high-low,.6],colors.metal);
    g.polygon([[s.distance,-.8,-.35],[s.distance,.8,-.35],[s.distance,.8,.35],[s.distance,-.8,.35]],g.colors.ink);
    for(let i=0;i<80;i++){
      const y=-.79+i*.02,delta=Math.hypot(s.distance,y-half)-Math.hypot(s.distance,y+half),intensity=Math.cos(Math.PI*delta/wavelength)**2;
      g.polygon([[s.distance-.007,y-.01,-.34],[s.distance-.007,y+.01,-.34],[s.distance-.007,y+.01,.34],[s.distance-.007,y-.01,.34]],g.colors.gold,{opacity:.05+.95*intensity,stroke:false});
    }
    for(const y of [-half,half])g.line([[-.82,0,0],[0,y,0],[s.distance,0,0]],g.colors.gold,{opacity:.55,width:1.5});
    g.label([-.9,.4,0],'Coherent source');g.label([0,1,0],'Two narrow slits');g.label([s.distance,1,0],'Interference screen');
    return result(`Slit separation d = ${s.gap}; screen distance L = ${s.distance}; wavelength λ = ${wavelength}, all in the same model units. Approximate central fringe spacing λL/d = ${fmt(wavelength*s.distance/s.gap,3)}. Bands use the actual path-length difference from the two slit centers.`, 'Ideal coherent, monochromatic light with equal amplitudes at each point. Display intensity is proportional to cos²(πΔ/λ). Finite-slit diffraction envelopes, spreading losses, alignment error and quantum detection events are omitted. Wavelength and slit widths are enlarged for visibility; this is not a laboratory setup guide.',[['Gray: two-slit barrier',colors.metal],['Gold bands: relative intensity',g.colors.gold],['Coral: source housing',g.colors.coral]],g);
  });

  function ensure(item) {
    const p = item && item.props;
    if (!p || typeof p.scenario !== 'string' || !/^module\.(math|lang|phys|bio|chem|cs|hist|earth|arts|mind|eng|health|env|design|business|civics|education|media|img)\.[0-5]\.[a-z0-9-]+$/.test(p.scenario)) return false;
    if (!Object.prototype.hasOwnProperty.call(families,p.family)) return false;
    if (!['model','context'].includes(p.mode) || typeof p.context !== 'string' || typeof p.lesson !== 'string') return false;
    const binding = JSON.stringify([p.family,p.mode,p.context,p.lesson]);
    if (registered.has(p.scenario)) return registered.get(p.scenario) === binding;
    if (window.PrimerSpatial.supported.includes(p.scenario)) return false;
    const family = families[p.family];
    const context = p.context, mode = p.mode, lesson = p.lesson;
    window.PrimerSpatial.register({[p.scenario]: {
      initial:{...family.initial}, controls:family.controls, camera:{yaw:-28,pitch:21},
      build(state,g) {
        const explanation = family.build(state,g);
        explanation.readout = context + ' ' + explanation.readout;
        if(mode==='context') explanation.note = 'Physical study context for “' + lesson + '”. ' + explanation.note;
        return explanation;
      },
    }});
    registered.set(p.scenario,binding);
    return true;
  }
  window.PrimerModuleObjects = Object.freeze({
    ensure,
    render(item,hooks) {return ensure(item)?window.PrimerSpatial.render(item,hooks):null;},
    get families() { return Object.keys(families); },
    title(id) {return Object.prototype.hasOwnProperty.call(families,id)?families[id].title:null;},
  });
}());
