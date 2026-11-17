"""Generate the physics activities for the modules that had none.

They use the page shell of tools/build_math_number_activities.py: controls, a drawing, a table and a result line.
The model of each is a small pure object, tested in tests/activity-models.test.cjs.

Run: python tools/build_physics_activities.py. It rewrites web/physics/<slug>/ and adds registry entries.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_math_number_activities as base  # noqa: E402

base.ACTS.clear()
slider, select = base.slider, base.select
SQUARE = 700


def add(*args, **kwargs):
    base.add(*args, subject='physics', **kwargs)


add('heat-flows', 'phys.0.hot-cold', 'Hot and Cold', 'Heat moves from warm to cool',
    'Put a warm thing against a cool thing. Heat flows from the warmer one to the cooler one until they are the same.',
    [('a', slider('a', 'First thing (°C)', 0, 100, 80)), ('b', slider('b', 'Second thing (°C)', 0, 100, 20)), ('t', slider('t', 'Minutes waited', 0, 30, 5))], ['Question', 'Answer'],
    '''  RATE: 0.15,
  // Two equal objects in contact: each approaches the average.
  temps(a, b, minutes) { const mid = (a + b) / 2, k = Math.exp(-Model.RATE * minutes); return [mid + (a - mid) * k, mid + (b - mid) * k]; },
  final: (a, b) => (a + b) / 2,
  direction: (a, b) => a > b ? 'first to second' : a < b ? 'second to first' : 'none',''',
    '''  const [x, y] = Model.temps(v.a, v.b, v.t), p = Kit.plot(canvas, {x: [0, 4], y: [0, 110], grid: false}), warm = n => n >= Model.final(v.a, v.b) ? '#b3261e' : '#215783';
  p.line(1.2, 0, 1.2, x, warm(v.a), 90); p.line(2.8, 0, 2.8, y, warm(v.b), 90); p.text(Kit.fmt(x, 3) + ' °C', 1.2, x, '#172533', -24, -10); p.text(Kit.fmt(y, 3) + ' °C', 2.8, y, '#172533', -24, -10); p.line(0.3, 0, 3.7, 0, '#172533', 2);
  if (v.a !== v.b) { const up = v.a > v.b; p.arrow(up ? 1.7 : 2.3, 55, up ? 2.3 : 1.7, 55, '#172533', 3); p.text('heat', 1.85, 55, '#172533', 0, -12); }
  return {sum: Kit.fmt(x, 3) + ' °C and ' + Kit.fmt(y, 3) + ' °C',
    rows: [['Which way does heat flow?', Model.direction(v.a, v.b)], ['First thing now', Kit.fmt(x, 3) + ' °C'], ['Second thing now', Kit.fmt(y, 3) + ' °C'], ['Where they will end up', Kit.fmt(Model.final(v.a, v.b), 3) + ' °C']],
    result: v.a === v.b ? 'They are already the same temperature, so no heat flows.' : 'Heat always flows from warm to cool, never the other way by itself. The warm thing cools and the cool thing warms until they match. (Two things of the same size and material are assumed.)'};''', height=300,
    aria='Two bars showing the temperatures of the two things, with an arrow for the heat flow.')

add('shadow-length', 'phys.0.light-shadow', 'Light and Shadow', 'Where shadows come from',
    'Light travels in straight lines. A shadow is the place the light cannot reach. Move the lamp and watch the shadow.',
    [('lamp', slider('lamp', 'Lamp height', 2, 10, 5, 0.5)), ('object', slider('object', 'Object height', 0.5, 3, 1.5, 0.5)), ('distance', slider('distance', 'Object’s distance from the lamp', 1, 8, 3, 0.5))], ['Question', 'Answer'],
    '''  // Similar triangles: shadow / object = (distance + shadow) / lamp. No finite shadow unless the lamp is higher than the object.
  shadow: (lamp, object, distance) => lamp > object ? object * distance / (lamp - object) : Infinity,''',
    '''  const s = Model.shadow(v.lamp, v.object, v.distance), p = Kit.plot(canvas, {x: [-1, 17], y: [-1, 11], grid: false}), end = Number.isFinite(s) ? v.distance + s : 17;
  p.line(-1, 0, 17, 0, '#172533', 2); p.line(0, 0, 0, v.lamp, '#9aa6ae', 3); p.point(0, v.lamp, '#d99a00', 11); p.line(v.distance, 0, v.distance, v.object, '#215783', 10);
  if (Number.isFinite(s)) { p.line(0, v.lamp, end, 0, '#d99a00', 1.5, [6, 5]); p.line(v.distance, 0, Math.min(end, 17), 0, '#172533', 9); }
  return {sum: Number.isFinite(s) ? 'Shadow length ' + Kit.fmt(s, 3) : 'The shadow never ends',
    rows: [['Shadow length', Number.isFinite(s) ? Kit.fmt(s, 3) : 'endless'], ['Lamp higher than the object?', v.lamp > v.object ? 'yes' : 'no'], ['Shadow compared with the object', Number.isFinite(s) ? Kit.fmt(s / v.object, 3) + ' times as long' : '—']],
    result: Number.isFinite(s) ? 'The ray that just clears the top of the object marks the end of the shadow. A lower lamp or an object further away makes a longer shadow, like the sun late in the day.' : 'The lamp is not higher than the object, so the ray over the top never comes down to the ground.'};''', height=360,
    aria='A lamp, an object and the shadow it casts along the ground.')

add('balanced-forces', 'phys.0.push-pull', 'Pushes and Pulls', 'Pushes, pulls and what happens next',
    'A push or a pull is a force. When the forces on a thing balance, its motion does not change.',
    [('right', slider('right', 'Push to the right', 0, 10, 6)), ('left', slider('left', 'Push to the left', 0, 10, 2))], ['Question', 'Answer'],
    '''  // Net force, positive to the right.
  net: (right, left) => right - left,
  outcome(right, left) { const n = right - left; return n > 0 ? 'speeds up to the right' : n < 0 ? 'speeds up to the left' : 'no change in motion'; },''',
    '''  const n = Model.net(v.right, v.left), p = Kit.plot(canvas, {x: [-14, 14], y: [-2, 3], grid: false});
  p.line(-14, -1, 14, -1, '#172533', 2); p.line(-1.5, 0, 1.5, 0, '#8a6d3b', 90);
  if (v.right) p.arrow(-1.6 - v.right, 0.4, -1.6, 0.4, '#215783', 5); if (v.left) p.arrow(1.6 + v.left, 0.4, 1.6, 0.4, '#963d18', 5);
  if (n) p.arrow(0, 2.3, n, 2.3, '#3c7a4b', 5); p.text(n ? 'overall force' : 'forces balance', n ? n / 2 : 0, 2.3, '#172533', -40, -12);
  return {sum: 'Overall force: ' + Math.abs(n) + (n ? (n > 0 ? ' to the right' : ' to the left') : ''),
    rows: [['Push to the right', String(v.right)], ['Push to the left', String(v.left)], ['Overall force', n ? Math.abs(n) + (n > 0 ? ' to the right' : ' to the left') : '0 (balanced)'], ['What the box does', Model.outcome(v.right, v.left)]],
    result: n ? 'The pushes do not balance, so the box speeds up in the direction of the bigger push.' : 'The pushes balance. A still box stays still, and a moving box keeps moving the same way. It takes an unbalanced force to start or stop motion.'};''', height=260,
    aria='A box with a push from each side and an arrow for the overall force.')

add('falling-energy', 'phys.1.energy', 'Energy Everywhere', 'Energy changes form as a ball falls',
    'A ball held up high has stored energy. As it falls, stored energy becomes energy of motion. The total stays the same.',
    [('mass', slider('mass', 'Mass (kg)', 0.5, 5, 1, 0.5)), ('height', slider('height', 'Starting height (m)', 1, 20, 10)), ('fallen', slider('fallen', 'Part of the drop completed (%)', 0, 100, 40, 5))], ['Energy', 'Joules'],
    '''  G: 9.8,
  // Air resistance is ignored.
  energy(mass, height, percent) {
    const y = height * (1 - percent / 100), stored = mass * Model.G * y, total = mass * Model.G * height, moving = total - stored;
    return {y, stored, moving, total, speed: Math.sqrt(2 * moving / mass)};
  },''',
    '''  const e = Model.energy(v.mass, v.height, v.fallen), p = Kit.plot(canvas, {x: [0, 6], y: [0, e.total * 1.2], grid: false});
  [['stored (height)', e.stored, '#215783'], ['motion', e.moving, '#963d18'], ['total', e.total, '#3c7a4b']].forEach(([name, value, colour], i) => { p.line(1.2 + i * 1.6, 0, 1.2 + i * 1.6, value, colour, 70); p.text(name, 1.2 + i * 1.6, e.total * 1.08, '#172533', -40, 0); });
  p.line(0.4, 0, 5.4, 0, '#172533', 2);
  return {sum: 'Height ' + Kit.fmt(e.y, 3) + ' m, speed ' + Kit.fmt(e.speed, 3) + ' m/s',
    rows: [['Stored energy (gravitational)', Kit.fmt(e.stored)], ['Energy of motion (kinetic)', Kit.fmt(e.moving)], ['Total', Kit.fmt(e.total)], ['Speed (m/s)', Kit.fmt(e.speed, 3)]],
    result: 'Energy is not used up: every joule lost from the stored energy appears as energy of motion. When the ball lands, that energy becomes sound and a little heat. Air resistance is ignored here.'};''', height=320,
    aria='Bars for stored energy, energy of motion and their total.')

add('compass-field', 'phys.1.magnets', 'Magnets', 'A compass around a bar magnet',
    'A magnet has a north pole and a south pole. A compass needle shows which way the magnet would push another north pole.',
    [('x', slider('x', 'Compass position across', -4, 4, 2, 0.5)), ('y', slider('y', 'Compass position up', -4, 4, 1.5, 0.5)), ('facing', select('facing', 'Bring a second magnet with this pole first', [('N', 'north pole'), ('S', 'south pole')]))], ['Question', 'Answer'],
    '''  // Field direction of a small bar magnet at the origin with its north pole toward +x (a dipole). Returns a unit vector, or null at the centre.
  field(x, y) { const r2 = x * x + y * y; if (!r2) return null; const bx = (3 * x * x - r2), by = 3 * x * y, size = Math.hypot(bx, by); return [bx / size + 0, by / size + 0]; },
  angle(x, y) { const f = Model.field(x, y); return f ? Math.atan2(f[1], f[0]) * 180 / Math.PI : null; },
  // Like poles repel, unlike poles attract.
  force: (pole, other) => pole === other ? 'repel' : 'attract',''',
    '''  const p = Kit.plot(canvas, {x: [-5, 5], y: [-5, 5], grid: false}), f = Model.field(v.x, v.y), near = v.x >= 0 ? 'N' : 'S';
  for (let x = -4.5; x <= 4.5; x += 1) for (let y = -4.5; y <= 4.5; y += 1) { const g = Model.field(x, y); if (g && Math.hypot(x, y) > 1.2) p.arrow(x - g[0] * 0.3, y - g[1] * 0.3, x + g[0] * 0.3, y + g[1] * 0.3, '#b9c3ca', 1.5); }
  p.line(-0.9, 0, 0, 0, '#215783', 26); p.line(0, 0, 0.9, 0, '#b3261e', 26); p.text('S', -0.6, 0, '#fff', -4, 6); p.text('N', 0.5, 0, '#fff', -4, 6);
  if (f) { p.arrow(v.x - f[0] * 0.6, v.y - f[1] * 0.6, v.x + f[0] * 0.6, v.y + f[1] * 0.6, '#b3261e', 4); p.point(v.x, v.y, '#172533', 4); }
  return {sum: f ? 'Needle points ' + Kit.fmt(Model.angle(v.x, v.y), 3).replace('-', '−') + '° from the magnet’s axis' : 'Move the compass off the magnet',
    rows: [['Needle direction', f ? Kit.fmt(Model.angle(v.x, v.y), 3).replace('-', '−') + '°' : '—'], ['Nearer pole of the magnet', near === 'N' ? 'north' : 'south'], ['Second magnet, ' + (v.facing === 'N' ? 'north' : 'south') + ' pole first, at that end', 'they ' + Model.force(v.facing, near)]],
    result: 'Field lines leave the north pole and curve round to the south pole; the needle lines up along them. Like poles repel and unlike poles attract. Earth acts as a magnet too, which is why a compass finds north.'};''', height=SQUARE,
    aria='A bar magnet, small arrows showing its field, and a compass needle at the chosen place.')

add('distance-speed-time', 'phys.1.motion', 'How Things Move', 'Speed, time and distance',
    'Speed says how far something goes each second. Set a speed and a time and read the distance.',
    [('speed', slider('speed', 'Speed (metres each second)', 0, 15, 5, 0.5)), ('time', slider('time', 'Time (seconds)', 0, 20, 8)), ('friction', slider('friction', 'Slowing each second (m/s)', 0, 3, 0, 0.5))], ['Question', 'Answer'],
    '''  distance: (speed, time) => speed * time,
  // With a steady slowing, the thing stops after speed ÷ slowing seconds.
  stopTime: (speed, slowing) => slowing ? speed / slowing : Infinity,
  travelled(speed, time, slowing) { const t = Math.min(time, Model.stopTime(speed, slowing)); return speed * t - slowing * t * t / 2; },
  speedAt: (speed, time, slowing) => Math.max(0, speed - slowing * time),''',
    '''  const d = Model.travelled(v.speed, v.time, v.friction), stop = Model.stopTime(v.speed, v.friction), p = Kit.plot(canvas, {x: [0, 20], y: [0, 310], xlabel: 'time (s)', ylabel: 'distance (m)'});
  p.curve(t => Model.travelled(v.speed, t, v.friction), '#215783'); p.point(v.time, d, '#963d18', 6); if (v.friction) p.curve(t => Model.distance(v.speed, t), '#9aa6ae', 0, 20, 1.5);
  return {sum: Kit.fmt(d) + ' m in ' + v.time + ' s',
    rows: [['Distance travelled', Kit.fmt(d) + ' m'], ['Speed now', Kit.fmt(Model.speedAt(v.speed, v.time, v.friction)) + ' m/s'], ['Distance with no slowing', Kit.fmt(Model.distance(v.speed, v.time)) + ' m'], ['Time until it stops', Number.isFinite(stop) ? Kit.fmt(stop) + ' s' : 'it never stops']],
    result: v.friction ? 'Friction is a force against the motion. It slows the thing by ' + v.friction + ' m/s every second, so the graph bends over and goes flat when it stops.' : 'With nothing slowing it, the thing keeps the same speed and the graph is a straight line: distance = speed × time. Things stop because forces such as friction act on them.'};''', height=420,
    aria='Graph of distance against time.')

add('series-parallel', 'phys.2.electricity', 'Electricity', 'Two bulbs: in series or in parallel',
    'Current flows round a complete circuit. Connect two bulbs one after the other, or side by side, and compare.',
    [('kind', select('kind', 'Connection', [('series', 'Series (one after the other)'), ('parallel', 'Parallel (side by side)')])), ('volts', slider('volts', 'Battery (volts)', 1.5, 12, 6, 1.5)), ('r1', slider('r1', 'Bulb 1 resistance (ohms)', 1, 20, 6)), ('r2', slider('r2', 'Bulb 2 resistance (ohms)', 1, 20, 12))], ['Quantity', 'Bulb 1', 'Bulb 2', 'Whole circuit'],
    '''  circuit(kind, volts, r1, r2) {
    if (kind === 'series') { const total = r1 + r2, current = volts / total; return {total, current, bulbs: [{volts: current * r1, current, power: current * current * r1}, {volts: current * r2, current, power: current * current * r2}], power: volts * current}; }
    const total = r1 * r2 / (r1 + r2), bulbs = [r1, r2].map(r => ({volts, current: volts / r, power: volts * volts / r}));
    return {total, current: volts / total, bulbs, power: volts * volts / total};
  },''',
    '''  const c = Model.circuit(v.kind, v.volts, v.r1, v.r2), top = Math.max(c.bulbs[0].power, c.bulbs[1].power), p = Kit.plot(canvas, {x: [0, 4], y: [0, top * 1.3], grid: false});
  c.bulbs.forEach((b, i) => { p.line(1.2 + i * 1.6, 0, 1.2 + i * 1.6, b.power, '#d99a00', 80); p.text('bulb ' + (i + 1) + ': ' + Kit.fmt(b.power, 3) + ' W', 1.2 + i * 1.6, b.power, '#172533', -44, -10); }); p.line(0.3, 0, 3.7, 0, '#172533', 2);
  const f = n => Kit.fmt(n, 3);
  return {sum: 'Battery current ' + f(c.current) + ' A',
    rows: [['Voltage (V)', f(c.bulbs[0].volts), f(c.bulbs[1].volts), f(v.volts)], ['Current (A)', f(c.bulbs[0].current), f(c.bulbs[1].current), f(c.current)], ['Resistance (Ω)', String(v.r1), String(v.r2), f(c.total)], ['Power (W)', f(c.bulbs[0].power), f(c.bulbs[1].power), f(c.power)]],
    result: v.kind === 'series' ? 'In series the same current passes through both bulbs and they share the battery voltage. The bulb with more resistance takes the larger share and is brighter. Remove one and both go out.' : 'In parallel each bulb gets the full battery voltage and its own current. The bulb with less resistance draws more current and is brighter. Remove one and the other stays lit.'};''', height=320,
    aria='Bars showing the power of each bulb, which sets its brightness.', caption='Circuit values')

add('heating-curve', 'phys.2.matter', 'States of Matter', 'Heating ice until it is steam',
    'Add heat to one kilogram of ice at −20 °C. The temperature rises, except while the ice melts and while the water boils.',
    [('heat', slider('heat', 'Heat added (kilojoules)', 0, 3200, 500, 10))], ['Stage', 'Heat needed (kJ)', 'Temperature'],
    '''  // One kilogram of water substance, starting as ice at −20 °C. Specific heats in kJ/(kg·K), latent heats in kJ/kg.
  ICE: 2.1, WATER: 4.18, STEAM: 2.0, FUSION: 334, VAPORISATION: 2260, START: -20,
  stages() { const a = Model.ICE * 20, b = a + Model.FUSION, c = b + Model.WATER * 100, d = c + Model.VAPORISATION; return [a, b, c, d]; },
  state(heat) {
    const [a, b, c, d] = Model.stages();
    if (heat < a) return {temperature: Model.START + heat / Model.ICE, phase: 'solid (ice)'};
    if (heat < b) return {temperature: 0, phase: 'melting: ice and water together', melted: (heat - a) / Model.FUSION};
    if (heat < c) return {temperature: (heat - b) / Model.WATER, phase: 'liquid (water)'};
    if (heat < d) return {temperature: 100, phase: 'boiling: water and steam together', boiled: (heat - c) / Model.VAPORISATION};
    return {temperature: 100 + (heat - d) / Model.STEAM, phase: 'gas (steam)'};
  },''',
    '''  const s = Model.state(v.heat), [a, b, c, d] = Model.stages(), p = Kit.plot(canvas, {x: [0, 3200], y: [-30, 180], xlabel: 'heat added (kJ)', ylabel: 'temperature (°C)'});
  p.curve(q => Model.state(q).temperature, '#215783'); p.point(v.heat, s.temperature, '#963d18', 7);
  const f = n => Kit.fmt(n, 4);
  return {sum: Kit.fmt(s.temperature, 3).replace('-', '−') + ' °C — ' + s.phase,
    rows: [['Warm the ice from −20 °C to 0 °C', f(a), 'rises'], ['Melt the ice', f(Model.FUSION), 'stays at 0 °C'], ['Warm the water from 0 °C to 100 °C', f(c - b), 'rises'], ['Boil the water', f(Model.VAPORISATION), 'stays at 100 °C'], ['Warm the steam', '2 for each degree', 'rises']],
    result: (s.melted !== undefined ? Kit.fmt(100 * s.melted, 3) + '% of the ice has melted. ' : s.boiled !== undefined ? Kit.fmt(100 * s.boiled, 3) + '% of the water has boiled. ' : '') + 'On the flat parts the heat is not raising the temperature: it is pulling the particles apart to change the state. Boiling takes nearly seven times as much heat as melting. Normal atmospheric pressure is assumed.'};''', height=440,
    aria='Graph of temperature against heat added, with flat parts at melting and boiling.', caption='Stages for one kilogram')

add('measurement-uncertainty', 'phys.2.units', 'Measuring the World', 'A measurement and its uncertainty',
    'No measurement is exact. An honest result gives the value, the unit and how far off it might be.',
    [('reading', slider('reading', 'Reading (millimetres)', 1, 200, 47)), ('step', select('step', 'Smallest division of the ruler', [('1', '1 mm'), ('0.5', '0.5 mm'), ('5', '5 mm'), ('10', '1 cm')]))], ['Form', 'Value'],
    '''  // Half the smallest division is the usual reading uncertainty of a scale.
  uncertainty: step => step / 2,
  relative: (reading, step) => 100 * Model.uncertainty(step) / reading,
  PREFIXES: [['kilometres', 1e-6], ['metres', 1e-3], ['centimetres', 0.1], ['millimetres', 1], ['micrometres', 1000]],
  convert: (mm, factor) => mm * factor,
  // Round to a number of significant figures.
  significant(value, figures) { if (!value) return 0; const power = figures - 1 - Math.floor(Math.log10(Math.abs(value))); return Math.round(value * 10 ** power) / 10 ** power; },
  scientific(value) { const e = Math.floor(Math.log10(Math.abs(value))); return (Math.round(value / 10 ** e * 1000) / 1000) + ' × 10^' + e; },''',
    '''  const step = Number(v.step), u = Model.uncertainty(step), lo = Math.floor(v.reading / step) * step - 5 * step, hi = lo + 11 * step, p = Kit.plot(canvas, {x: [lo - step, hi + step], y: [-1.2, 1.6], grid: false});
  axis(p, lo, hi, step); p.line(v.reading - u, 0.6, v.reading + u, 0.6, '#e3b89c', 16); p.line(v.reading, 0.15, v.reading, 1.1, '#963d18', 3); p.text('mm (close-up of the ruler)', hi, 0, '#172533', -170, 44);
  return {sum: v.reading + ' mm ± ' + u + ' mm',
    rows: [['Result', v.reading + ' ± ' + u + ' mm'], ['Range it could lie in', (v.reading - u) + ' mm to ' + (v.reading + u) + ' mm'], ['Uncertainty as a percentage', Kit.fmt(Model.relative(v.reading, step), 3) + '%'],
      ...Model.PREFIXES.map(([name, factor]) => ['In ' + name, Model.scientific(Model.convert(v.reading, factor)) + ' ' + name]), ['To 1 significant figure', Model.significant(v.reading, 1) + ' mm']],
    result: 'The uncertainty is taken as half the smallest division. The same ± ' + u + ' mm matters much more for a short length than a long one: here it is ' + Kit.fmt(Model.relative(v.reading, step), 3) + '% of the reading. Changing the unit changes the number but not the length.'};''',
    aria='A ruler with a band showing the range the true length could lie in.')

add('faraday-induction', 'phys.3.em', 'Electricity and Magnetism', 'Faraday’s law: a changing field makes a voltage',
    'A coil in a changing magnetic field has a voltage induced in it. Only the change matters: a steady field induces nothing.',
    [('turns', slider('turns', 'Turns of wire', 1, 200, 50)), ('area', slider('area', 'Area of the coil (cm²)', 1, 100, 20)), ('b1', slider('b1', 'Field at the start (tesla)', -1, 1, 0, 0.1)), ('b2', slider('b2', 'Field at the end (tesla)', -1, 1, 0.5, 0.1)), ('dt', slider('dt', 'Time taken (seconds)', 0.01, 2, 0.5, 0.01))], ['Quantity', 'Value'],
    '''  // Flux through one turn in webers, with the area given in cm².
  flux: (field, areaCm2) => field * areaCm2 * 1e-4,
  // Average emf in volts. The minus sign is Lenz’s law: the induced current opposes the change.
  emf: (turns, areaCm2, b1, b2, dt) => -turns * (Model.flux(b2, areaCm2) - Model.flux(b1, areaCm2)) / dt,''',
    '''  const e = Model.emf(v.turns, v.area, v.b1, v.b2, v.dt), p = Kit.plot(canvas, {x: [-0.5, 3], y: [-1.2, 1.2], xlabel: 'time (s)', ylabel: 'field (T)'}), m = n => Kit.fmt(n, 3).replace('-', '−');
  p.line(-0.5, v.b1, 0, v.b1, '#215783', 3); p.line(0, v.b1, v.dt, v.b2, '#963d18', 3); p.line(v.dt, v.b2, 3, v.b2, '#215783', 3);
  return {sum: 'Induced voltage ' + m(e) + ' V while the field changes',
    rows: [['Flux through one turn at the start', m(Model.flux(v.b1, v.area) * 1000) + ' mWb'], ['Flux through one turn at the end', m(Model.flux(v.b2, v.area) * 1000) + ' mWb'], ['Rate of change of field', m((v.b2 - v.b1) / v.dt) + ' T/s'], ['Induced voltage (average)', m(e) + ' V'], ['Before and after the change', '0 V']],
    result: v.b1 === v.b2 ? 'The field does not change, so no voltage is induced however strong it is.' : 'The voltage is the number of turns times the rate of change of flux. Making the change faster, the coil larger or the turns more numerous all raise it. The minus sign is Lenz’s law: the induced current makes a field that opposes the change. This is how generators and transformers work.'};''', height=400,
    aria='Graph of the magnetic field against time; the sloping part is where voltage is induced.')

add('collision-lab', 'phys.3.energy-work', 'Work, Energy and Momentum', 'Collisions: momentum is always conserved',
    'Two carts collide on a straight track. Momentum is conserved in every collision; kinetic energy only in a perfectly bouncy one.',
    [('m1', slider('m1', 'Mass 1 (kg)', 1, 10, 2)), ('v1', slider('v1', 'Velocity 1 (m/s)', -10, 10, 6)), ('m2', slider('m2', 'Mass 2 (kg)', 1, 10, 4)), ('v2', slider('v2', 'Velocity 2 (m/s)', -10, 10, -1)), ('e', slider('e', 'Bounciness (0 = stick, 1 = elastic)', 0, 1, 1, 0.1))], ['Quantity', 'Before', 'After'],
    '''  // Coefficient of restitution e: relative speed after = e × relative speed before.
  collide(m1, v1, m2, v2, e) {
    const p = m1 * v1 + m2 * v2, total = m1 + m2;
    return [(p + m2 * e * (v2 - v1)) / total, (p + m1 * e * (v1 - v2)) / total];
  },
  momentum: (m1, v1, m2, v2) => m1 * v1 + m2 * v2,
  kinetic: (m1, v1, m2, v2) => m1 * v1 * v1 / 2 + m2 * v2 * v2 / 2,
  // They only collide if cart 1 (on the left) is catching up with cart 2.
  approaching: (v1, v2) => v1 > v2,''',
    '''  const hit = Model.approaching(v.v1, v.v2), [a, b] = hit ? Model.collide(v.m1, v.v1, v.m2, v.v2, v.e) : [v.v1, v.v2], p = Kit.plot(canvas, {x: [-14, 14], y: [0, 4], grid: false}), m = n => Kit.fmt(n, 3).replace('-', '−');
  const row = (y, u1, u2, label) => { p.line(-14, y - 0.35, 14, y - 0.35, '#9aa6ae', 1); p.point(-3, y, '#215783', 6 + v.m1 * 1.6); p.point(3, y, '#963d18', 6 + v.m2 * 1.6); if (u1) p.arrow(-3, y + 0.6, -3 + u1, y + 0.6, '#215783'); if (u2) p.arrow(3, y + 0.6, 3 + u2, y + 0.6, '#963d18'); p.text(label, -14, y + 0.6, '#172533', 4, 0); };
  row(2.7, v.v1, v.v2, 'before'); row(0.8, a, b, 'after');
  const k0 = Model.kinetic(v.m1, v.v1, v.m2, v.v2), k1 = Model.kinetic(v.m1, a, v.m2, b);
  return {sum: hit ? 'After: ' + m(a) + ' m/s and ' + m(b) + ' m/s' : 'The carts do not collide',
    rows: [['Velocity of cart 1 (m/s)', m(v.v1), m(a)], ['Velocity of cart 2 (m/s)', m(v.v2), m(b)], ['Total momentum (kg·m/s)', m(Model.momentum(v.m1, v.v1, v.m2, v.v2)), m(Model.momentum(v.m1, a, v.m2, b))], ['Total kinetic energy (J)', m(k0), m(k1)], ['Kinetic energy lost (J)', '—', m(Math.max(0, k0 - k1))]],
    result: !hit ? 'Cart 1 is not catching up with cart 2, so nothing changes.' : v.e === 1 ? 'An elastic collision: both momentum and kinetic energy are the same before and after.' : 'Momentum is unchanged, but ' + m(k0 - k1) + ' J of kinetic energy has become heat, sound and deformation.' + (v.e === 0 ? ' The carts stick together and move as one.' : '')};''', height=340,
    aria='The two carts with their velocity arrows before and after the collision.', caption='Before and after')

add('carnot-engine', 'phys.3.thermo', 'Thermodynamics', 'The best any heat engine can do',
    'A heat engine takes heat from a hot place, turns some into work and dumps the rest somewhere cooler. The temperatures alone set the ceiling on its efficiency.',
    [('hot', slider('hot', 'Hot temperature (K)', 300, 1500, 800, 10)), ('cold', slider('cold', 'Cold temperature (K)', 100, 600, 300, 10)), ('heat', slider('heat', 'Heat taken in (J)', 100, 2000, 1000, 100)), ('real', slider('real', 'This engine’s efficiency (%)', 0, 100, 35))], ['Quantity', 'Ideal (Carnot)', 'This engine'],
    '''  // Carnot limit; meaningful only when hot > cold.
  limit: (hot, cold) => hot > cold ? 1 - cold / hot : 0,
  flows(heat, efficiency) { const work = heat * efficiency; return {work, waste: heat - work}; },
  // Total entropy change of the two reservoirs for one cycle (J/K). It cannot be negative.
  entropy: (hot, cold, heat, efficiency) => -heat / hot + heat * (1 - efficiency) / cold,
  possible: (hot, cold, efficiency) => efficiency <= Model.limit(hot, cold) + 1e-12,''',
    '''  const limit = Model.limit(v.hot, v.cold), eff = v.real / 100, ideal = Model.flows(v.heat, limit), mine = Model.flows(v.heat, eff), ok = Model.possible(v.hot, v.cold, eff), p = Kit.plot(canvas, {x: [0, 7], y: [0, 2200], grid: false, ylabel: 'joules'}), f = n => Kit.fmt(n, 4).replace('-', '−');
  [['heat in', v.heat, '#b3261e'], ['ideal work', ideal.work, '#3c7a4b'], ['ideal waste', ideal.waste, '#215783'], ['this work', mine.work, ok ? '#3c7a4b' : '#9aa6ae'], ['this waste', mine.waste, ok ? '#215783' : '#9aa6ae']].forEach(([name, value, colour], i) => { p.line(1 + i * 1.25, 0, 1 + i * 1.25, value, colour, 60); p.text(name, 1 + i * 1.25, value, '#172533', -30, -10); });
  p.line(0.4, 0, 6.6, 0, '#172533', 2);
  const dS = Model.entropy(v.hot, v.cold, v.heat, eff);
  return {sum: 'Carnot limit ' + f(100 * limit) + '%',
    rows: [['Efficiency', f(100 * limit) + '%', v.real + '%'], ['Work out (J)', f(ideal.work), f(mine.work)], ['Waste heat (J)', f(ideal.waste), f(mine.waste)], ['Entropy change of the surroundings (J/K)', '0', f(dS)]],
    result: v.hot <= v.cold ? 'With no temperature difference no engine can produce work.' : ok ? 'This engine is allowed: its entropy change is ' + (Math.abs(dS) < 1e-9 ? 'zero, the ideal reversible case.' : 'positive, as the second law requires.') + ' Waste heat is unavoidable; only a colder sink or a hotter source raises the limit.' : 'This engine is impossible. It would beat the Carnot limit and lower the total entropy by ' + f(-dS) + ' J/K, which the second law forbids.'};''', height=380,
    aria='Bars for heat taken in, work and waste heat, for the ideal engine and this engine.', caption='One cycle')

add('em-spectrum', 'phys.4.em-maxwell', 'Electrodynamics', 'One wave, every wavelength',
    'Maxwell’s equations give waves of electric and magnetic field that travel at one speed in a vacuum. Frequency alone separates radio from light from X-rays.',
    [('power', slider('power', 'Frequency: 10 to the power', 4, 20, 14.7, 0.1))], ['Quantity', 'Value'],
    '''  C: 299792458, H: 6.62607015e-34, EV: 1.602176634e-19,
  wavelength: frequency => Model.C / frequency,
  photon: frequency => Model.H * frequency / Model.EV,
  period: frequency => 1 / frequency,
  // Conventional band edges by wavelength in metres; the boundaries are not sharp.
  BANDS: [[1e-11, 'gamma rays'], [1e-8, 'X-rays'], [3.8e-7, 'ultraviolet'], [7.5e-7, 'visible light'], [1e-3, 'infrared'], [1, 'microwaves'], [Infinity, 'radio waves']],
  band(frequency) { const w = Model.wavelength(frequency); return Model.BANDS.find(([edge]) => w < edge)[1]; },
  scientific(value) { const e = Math.floor(Math.log10(value)); return (Math.round(value / 10 ** e * 100) / 100) + ' × 10^' + e; },''',
    '''  const f = 10 ** v.power, w = Model.wavelength(f), p = Kit.plot(canvas, {x: [0, 3], y: [-1.6, 1.6], grid: false});
  p.line(0, 0, 3, 0, '#172533', 1.5); p.curve(x => Math.sin(2 * Math.PI * x), '#b3261e', 0, 3); p.curve(x => 0.45 * Math.sin(2 * Math.PI * x), '#215783', 0, 3, 2);
  p.arrow(0, -1.3, 1, -1.3, '#172533', 2); p.text('one wavelength = ' + Model.scientific(w) + ' m', 0, -1.3, '#172533', 4, -8); p.text('electric field', 0.25, 1, '#b3261e', 8, -12); p.text('magnetic field (at right angles)', 1.25, 0.45, '#215783', 8, -10);
  return {sum: Model.band(f) + ': wavelength ' + Model.scientific(w) + ' m',
    rows: [['Frequency', Model.scientific(f) + ' Hz'], ['Wavelength', Model.scientific(w) + ' m'], ['Period', Model.scientific(Model.period(f)) + ' s'], ['Energy of one photon', Model.scientific(Model.photon(f)) + ' eV'], ['Band', Model.band(f)], ['Speed in a vacuum', '299 792 458 m/s (exact)']],
    result: 'Every electromagnetic wave travels at the same speed in a vacuum, so wavelength × frequency is always c. The electric and magnetic fields oscillate in step, at right angles to each other and to the direction of travel. Band boundaries are conventions, not sharp physical edges.'};''', height=360,
    aria='One electromagnetic wave: the electric and magnetic fields oscillating in step.')

add('pipe-flow', 'phys.4.fluids', 'Fluid Mechanics', 'Flow through a narrowing pipe',
    'Water cannot pile up, so it speeds up where the pipe narrows. Where it moves faster its pressure is lower.',
    [('a1', slider('a1', 'Wide section area (cm²)', 5, 50, 20)), ('a2', slider('a2', 'Narrow section area (cm²)', 1, 50, 5)), ('v1', slider('v1', 'Speed in the wide section (m/s)', 0.5, 5, 2, 0.5))], ['Quantity', 'Wide section', 'Narrow section'],
    '''  DENSITY: 1000,
  // Continuity for an incompressible fluid: A1 v1 = A2 v2.
  speed: (a1, a2, v1) => v1 * a1 / a2,
  // Volume per second in litres per second, with area in cm² and speed in m/s.
  flow: (areaCm2, speed) => areaCm2 * 1e-4 * speed * 1000,
  // Bernoulli for a level pipe with no friction: pressure drop in pascals from section 1 to section 2.
  drop: (a1, a2, v1) => Model.DENSITY * (Model.speed(a1, a2, v1) ** 2 - v1 ** 2) / 2,''',
    '''  const v2 = Model.speed(v.a1, v.a2, v.v1), drop = Model.drop(v.a1, v.a2, v.v1), p = Kit.plot(canvas, {x: [0, 10], y: [-4, 4], grid: false}), h1 = Math.sqrt(v.a1) / 2.2, h2 = Math.sqrt(v.a2) / 2.2, f = n => Kit.fmt(n, 3).replace('-', '−');
  for (const s of [1, -1]) { p.line(0, s * h1, 3.5, s * h1, '#172533', 3); p.line(3.5, s * h1, 5.5, s * h2, '#172533', 3); p.line(5.5, s * h2, 10, s * h2, '#172533', 3); }
  p.arrow(0.6, 0, 0.6 + Math.min(v.v1 * 0.5, 2.6), 0, '#215783', 4); p.arrow(6, 0, 6 + Math.min(v2 * 0.5, 3.8), 0, '#963d18', 4);
  return {sum: 'Speed in the narrow section ' + f(v2) + ' m/s',
    rows: [['Area (cm²)', String(v.a1), String(v.a2)], ['Speed (m/s)', f(v.v1), f(v2)], ['Flow (litres per second)', f(Model.flow(v.a1, v.v1)), f(Model.flow(v.a2, v2))], ['Pressure compared with the wide section (kPa)', '0', f(-drop / 1000)]],
    result: v.a2 === v.a1 ? 'The pipe does not change width, so the speed and pressure stay the same.' : v.a2 < v.a1 ? 'The same volume passes every second, so a smaller area needs a higher speed. The water gains kinetic energy, and its pressure falls to pay for it (Bernoulli). Friction and height changes are ignored.' : 'The pipe widens, so the water slows down and its pressure rises.'};''', height=340,
    aria='A pipe that changes width, with arrows showing the speed in each section.', caption='The two sections')

add('quark-charges', 'phys.4.particles', 'Particle Physics', 'Building particles from quarks',
    'Protons, neutrons and mesons are made of quarks. Add up the quark charges and you get the charge of the particle.',
    [('hadron', select('hadron', 'Particle', [('proton', 'Proton'), ('neutron', 'Neutron'), ('piplus', 'Pion π⁺'), ('piminus', 'Pion π⁻'), ('kplus', 'Kaon K⁺'), ('lambda', 'Lambda Λ'), ('omega', 'Omega Ω⁻'), ('deltapp', 'Delta Δ⁺⁺')]))], ['Particle', 'Family', 'Charge (e)', 'Spin'],
    '''  // Electric charge in thirds of the elementary charge, so the sums are exact.
  QUARKS: {u: 2, d: -1, s: -1, c: 2, b: -1, t: 2},
  HADRONS: {proton: ['u', 'u', 'd'], neutron: ['u', 'd', 'd'], piplus: ['u', 'anti-d'], piminus: ['d', 'anti-u'], kplus: ['u', 'anti-s'], lambda: ['u', 'd', 's'], omega: ['s', 's', 's'], deltapp: ['u', 'u', 'u']},
  thirds: quark => quark.startsWith('anti-') ? -Model.QUARKS[quark.slice(5)] : Model.QUARKS[quark],
  // Charge in units of e.
  charge: name => Model.HADRONS[name].reduce((sum, quark) => sum + Model.thirds(quark), 0) / 3,
  kind: name => Model.HADRONS[name].length === 3 ? 'baryon (three quarks)' : 'meson (a quark and an antiquark)',
  // Baryon number: +1/3 for each quark, −1/3 for each antiquark.
  baryonNumber: name => Model.HADRONS[name].reduce((sum, quark) => sum + (quark.startsWith('anti-') ? -1 : 1), 0) / 3,
  PARTICLES: [['up quark', 'quark', '+2/3', '1/2'], ['down quark', 'quark', '−1/3', '1/2'], ['charm quark', 'quark', '+2/3', '1/2'], ['strange quark', 'quark', '−1/3', '1/2'], ['top quark', 'quark', '+2/3', '1/2'], ['bottom quark', 'quark', '−1/3', '1/2'],
    ['electron', 'lepton', '−1', '1/2'], ['muon', 'lepton', '−1', '1/2'], ['tau', 'lepton', '−1', '1/2'], ['electron neutrino', 'lepton', '0', '1/2'], ['muon neutrino', 'lepton', '0', '1/2'], ['tau neutrino', 'lepton', '0', '1/2'],
    ['photon', 'force carrier', '0', '1'], ['gluon', 'force carrier', '0', '1'], ['W boson', 'force carrier', '±1', '1'], ['Z boson', 'force carrier', '0', '1'], ['Higgs boson', 'scalar', '0', '0']],''',
    '''  const quarks = Model.HADRONS[v.hadron], q = Model.charge(v.hadron), p = Kit.plot(canvas, {x: [0, 4.6], y: [-1.2, 1.2], grid: false}), third = n => n === 2 ? '+2/3' : n === -2 ? '−2/3' : n === 1 ? '+1/3' : '−1/3';
  p.line(0.3, 0, 4.3, 0, '#172533', 1.5);
  quarks.forEach((quark, i) => { const t = Model.thirds(quark); p.line(1 + i * 1.1, 0, 1 + i * 1.1, t / 3, t > 0 ? '#b3261e' : '#215783', 60); p.text(quark + ' ' + third(t), 1 + i * 1.1, t / 3, '#172533', -26, t > 0 ? -10 : 22); });
  return {sum: quarks.join(' + ') + '  →  charge ' + (q > 0 ? '+' : q < 0 ? '−' : '') + Math.abs(q),
    rows: Model.PARTICLES,
    result: 'This particle is a ' + Model.kind(v.hadron) + ' with baryon number ' + Model.baryonNumber(v.hadron) + '. Quark charges come in thirds, yet every particle seen on its own has a whole-number charge, because quarks are never found alone. The table lists the 17 kinds of particle in the Standard Model.'};''', height=300,
    aria='Bars for the charge of each quark in the chosen particle.', caption='The Standard Model particles')

add('particle-in-a-box', 'phys.4.quantum', 'Quantum Mechanics', 'An electron in a box',
    'Confine an electron between two walls. Only certain standing waves fit, so only certain energies are allowed.',
    [('n', slider('n', 'Level n', 1, 6, 2)), ('width', slider('width', 'Width of the box (nanometres)', 0.2, 2, 1, 0.1))], ['Level', 'Energy (eV)', 'Nodes inside'],
    '''  H: 6.62607015e-34, MASS: 9.1093837015e-31, EV: 1.602176634e-19,
  // Energy in electronvolts for a box of the given width in nanometres.
  energy: (n, widthNm) => n * n * Model.H ** 2 / (8 * Model.MASS * (widthNm * 1e-9) ** 2) / Model.EV,
  // Normalised wavefunction on 0 ≤ x ≤ 1 (width taken as 1).
  psi: (n, x) => Math.SQRT2 * Math.sin(n * Math.PI * x),
  density: (n, x) => Model.psi(n, x) ** 2,
  // Probability of finding the electron between fractions a and b of the width.
  probability: (n, a, b) => (b - a) - (Math.sin(2 * n * Math.PI * b) - Math.sin(2 * n * Math.PI * a)) / (2 * n * Math.PI),
  nodes: n => n - 1,
  // Wavelength in nanometres of the photon emitted in a jump between two levels.
  photon: (from, to, widthNm) => 1239.841984 / (Model.energy(from, widthNm) - Model.energy(to, widthNm)),''',
    '''  const p = Kit.plot(canvas, {x: [0, 1], y: [-1.6, 2.2], xlabel: 'position ÷ width'});
  p.curve(x => Model.density(v.n, x), '#963d18'); p.curve(x => Model.psi(v.n, x), '#215783', 0, 1, 2);
  p.text('probability density', 0.02, 2.05, '#963d18', 0, 0); p.text('wavefunction', 0.02, -1.45, '#215783', 0, 0);
  return {sum: 'E' + v.n + ' = ' + Kit.fmt(Model.energy(v.n, v.width)) + ' eV',
    rows: [1, 2, 3, 4, 5, 6].map(n => [(n === v.n ? '→ ' : '') + n, Kit.fmt(Model.energy(n, v.width)), String(Model.nodes(n))]),
    result: 'The energy grows as n² and shrinks as the box widens: squeezing the electron costs energy. The chance of finding it in the middle third is ' + Kit.fmt(100 * Model.probability(v.n, 1 / 3, 2 / 3), 3) + '%. ' + (v.n > 1 ? 'Dropping to the level below would emit a photon of wavelength ' + Kit.fmt(Model.photon(v.n, v.n - 1, v.width), 4) + ' nm.' : 'Even the lowest level has energy above zero: the electron can never be at rest.')};''', height=440,
    aria='The wavefunction and the probability density across the box.', caption='Allowed levels')

add('lorentz-transform', 'phys.4.relativity', 'Relativity', 'One event seen from a moving frame',
    'Mark an event in space and time. An observer moving past assigns it a different place and time, but both agree on the spacetime interval.',
    [('v', slider('v', 'Speed of the moving frame (fraction of c)', -0.9, 0.9, 0.6, 0.05)), ('x', slider('x', 'Position x (light-seconds)', -4, 4, 2, 0.25)), ('t', slider('t', 'Time t (seconds)', -4, 4, 3, 0.25)), ('w', slider('w', 'Speed of an object in the moving frame (fraction of c)', -0.9, 0.9, 0.5, 0.05))], ['Quantity', 'Rest frame', 'Moving frame'],
    '''  gamma: v => 1 / Math.sqrt(1 - v * v),
  // Units with c = 1: x in light-seconds, t in seconds.
  transform(v, x, t) { const g = Model.gamma(v); return [g * (x - v * t), g * (t - v * x)]; },
  // Invariant interval squared; positive is time-like, negative space-like.
  interval: (x, t) => t * t - x * x,
  kind(x, t) { const s = Model.interval(x, t); return Math.abs(s) < 1e-12 ? 'light-like' : s > 0 ? 'time-like' : 'space-like'; },
  // Velocity of an object moving at w in a frame that itself moves at v.
  addVelocities: (v, w) => (v + w) / (1 + v * w),''',
    '''  const [x2, t2] = Model.transform(v.v, v.x, v.t), p = Kit.plot(canvas, {x: [-5, 5], y: [-5, 5], xlabel: 'x', ylabel: 't'}), m = n => Kit.fmt(n, 4).replace('-', '−'), kind = Model.kind(v.x, v.t);
  p.line(-5, -5, 5, 5, '#d99a00', 1.5, [6, 5]); p.line(-5, 5, 5, -5, '#d99a00', 1.5, [6, 5]);
  p.line(-5 * v.v, -5, 5 * v.v, 5, '#3c7a4b', 2); p.line(-5, -5 * v.v, 5, 5 * v.v, '#3c7a4b', 2); p.text('t′ axis', 4 * v.v, 4, '#3c7a4b'); p.text('x′ axis', 4, 4 * v.v, '#3c7a4b');
  p.point(v.x, v.t, '#963d18', 7); p.text('event', v.x, v.t);
  return {sum: 'Moving frame: x′ = ' + m(x2) + ', t′ = ' + m(t2),
    rows: [['Position (light-seconds)', m(v.x), m(x2)], ['Time (seconds)', m(v.t), m(t2)], ['Interval t² − x²', m(Model.interval(v.x, v.t)), m(Model.interval(x2, t2))], ['Lorentz factor γ', '1', m(Model.gamma(v.v))], ['Object moving at ' + m(v.w) + ' c in the moving frame', m(Model.addVelocities(v.v, v.w)) + ' c', m(v.w) + ' c']],
    result: 'The two observers disagree about where and when, but not about the interval, which is ' + kind + '. ' + (kind === 'space-like' ? 'For a space-like interval even the order in time of this event and the origin can differ between observers.' : kind === 'time-like' ? 'For a time-like interval every observer agrees which came first.' : 'A light ray connects the event to the origin for every observer.') + ' Speeds do not simply add: the combined speed never reaches c. The yellow lines are light rays.'};''', height=SQUARE,
    aria='A spacetime diagram with light rays, the axes of the moving frame and the event.', caption='The same event in two frames')

add('band-gap', 'phys.4.solid-state', 'Solid State Physics', 'Band gaps and why semiconductors conduct',
    'In a crystal, electrons need the band-gap energy to break free and conduct. Heat or light can supply it.',
    [('material', select('material', 'Material', [('si', 'Silicon'), ('ge', 'Germanium'), ('gaas', 'Gallium arsenide'), ('diamond', 'Diamond')])), ('temperature', slider('temperature', 'Temperature (K)', 200, 600, 300, 10))], ['Material', 'Band gap (eV)', 'Longest wavelength absorbed (nm)'],
    '''  // Band gaps near room temperature, in electronvolts.
  GAPS: {si: 1.12, ge: 0.67, gaas: 1.42, diamond: 5.47},
  NAMES: {si: 'Silicon', ge: 'Germanium', gaas: 'Gallium arsenide', diamond: 'Diamond'},
  K: 8.617333262e-5,
  // Boltzmann factor that governs the intrinsic carrier density: exp(−Eg / 2kT).
  factor: (gap, temperature) => Math.exp(-gap / (2 * Model.K * temperature)),
  // How many times the factor grows between two temperatures.
  growth: (gap, t1, t2) => Model.factor(gap, t2) / Model.factor(gap, t1),
  // Photons with a longer wavelength than this cannot lift an electron across the gap (nm).
  cutoff: gap => 1239.841984 / gap,
  light(gap) { const w = Model.cutoff(gap); return w < 380 ? 'ultraviolet' : w < 750 ? 'visible' : 'infrared'; },
  thermal: temperature => Model.K * temperature,''',
    '''  const gap = Model.GAPS[v.material], p = Kit.plot(canvas, {x: [200, 600], y: [-70, 0], xlabel: 'temperature (K)', ylabel: 'log₁₀ of the Boltzmann factor'});
  const colours = {si: '#215783', ge: '#3c7a4b', gaas: '#963d18', diamond: '#6b3fa0'};
  Object.keys(Model.GAPS).forEach((name, i) => { const at = 250 + i * 85; p.curve(T => Math.log10(Model.factor(Model.GAPS[name], T)), colours[name], 200, 600, name === v.material ? 4 : 1.5); p.text(Model.NAMES[name], at, Math.log10(Model.factor(Model.GAPS[name], at)), colours[name], 4, 18); });
  p.point(v.temperature, Math.log10(Model.factor(gap, v.temperature)), '#172533', 6);
  return {sum: Model.NAMES[v.material] + ': factor 10^' + Kit.fmt(Math.log10(Model.factor(gap, v.temperature)), 3).replace('-', '−') + ' at ' + v.temperature + ' K',
    rows: Object.keys(Model.GAPS).map(name => [(name === v.material ? '→ ' : '') + Model.NAMES[name], String(Model.GAPS[name]), Kit.fmt(Model.cutoff(Model.GAPS[name]), 4) + ' (' + Model.light(Model.GAPS[name]) + ')']),
    result: 'Thermal energy kT at ' + v.temperature + ' K is only ' + Kit.fmt(Model.thermal(v.temperature), 3) + ' eV, far below the gap, so very few electrons are free. But the number rises steeply: warming ' + Model.NAMES[v.material].toLowerCase() + ' from 300 K to 400 K multiplies the factor by about ' + Kit.fmt(Model.growth(gap, 300, 400), 3) + '. Diamond’s wide gap makes it an insulator. Doping, not heat, is what makes chips work.'};''', height=460,
    aria='Curves of the Boltzmann factor against temperature for four materials.', caption='Materials')

add('counting-microstates', 'phys.4.statmech', 'Statistical Mechanics', 'Entropy is counting',
    'Toss N coins. Each exact sequence is a microstate; the number of heads is the macrostate. The macrostates with the most microstates are overwhelmingly likely.',
    [('n', slider('n', 'Coins N', 2, 40, 10)), ('k', slider('k', 'Heads', 0, 40, 5))], ['Quantity', 'Value'],
    '''  // Number of microstates with k heads among n coins.
  multiplicity(n, k) { if (k < 0 || k > n) return 0; let c = 1; for (let i = 1; i <= Math.min(k, n - k); i++) c = c * (n - i + 1) / i; return Math.round(c); },
  total: n => 2 ** n,
  probability: (n, k) => Model.multiplicity(n, k) / Model.total(n),
  // Entropy in units of Boltzmann’s constant: S/k = ln Ω.
  entropy: (n, k) => Math.log(Model.multiplicity(n, k)),
  // Chance of landing within the given fraction of N either side of half heads.
  near(n, fraction) { let sum = 0; for (let k = 0; k <= n; k++) if (Math.abs(k - n / 2) <= fraction * n) sum += Model.probability(n, k); return sum; },''',
    '''  const k = Math.min(v.k, v.n), top = Model.multiplicity(v.n, Math.floor(v.n / 2)), p = Kit.plot(canvas, {x: [-1, v.n + 1], y: [0, top * 1.12], xlabel: 'heads', ylabel: 'microstates'});
  for (let i = 0; i <= v.n; i++) p.line(i, 0, i, Model.multiplicity(v.n, i), i === k ? '#963d18' : '#215783', 10);
  return {sum: 'Ω = ' + Model.multiplicity(v.n, k) + (Model.multiplicity(v.n, k) === 1 ? ' microstate' : ' microstates') + ' for ' + k + ' heads',
    rows: [['Microstates for this macrostate, Ω', String(Model.multiplicity(v.n, k))], ['All microstates, 2 to the power N', String(Model.total(v.n))], ['Probability of this macrostate', Kit.fmt(Model.probability(v.n, k), 3)], ['Entropy S ÷ k = ln Ω', Kit.fmt(Model.entropy(v.n, k), 4)], ['Chance of being within 10% of N of an even split', Kit.fmt(100 * Model.near(v.n, 0.1), 3) + '%']],
    result: 'Every single sequence is equally likely, but an even split can happen in far more ways than all heads. As N grows the peak sharpens: with the numbers of atoms in real matter, anything but the most probable macrostate is never seen. That is why entropy increases.'};''', height=440,
    aria='Bar chart of the number of microstates for each number of heads.')

add('black-hole-time', 'phys.5.gr-cosmo', 'General Relativity and Cosmology', 'Time near a black hole',
    'Mass curves spacetime. Close to a compact mass, clocks run slow compared with clocks far away, and at the Schwarzschild radius light can no longer escape.',
    [('mass', slider('mass', 'Mass: 10 to this power, in solar masses', 0, 10, 1, 0.1)), ('ratio', slider('ratio', 'Your distance, in Schwarzschild radii', 1.05, 20, 3, 0.05))], ['Quantity', 'Value'],
    '''  // Schwarzschild radius of one solar mass in kilometres: 2GM/c².
  RS_SUN: 2.953,
  radius: solarMasses => Model.RS_SUN * solarMasses,
  // Rate of a clock hovering at r, compared with a clock far away (non-rotating mass).
  rate: ratio => Math.sqrt(1 - 1 / ratio),
  // Seconds lost per day by the hovering clock.
  lostPerDay: ratio => 86400 * (1 - Model.rate(ratio)),
  // Escape speed as a fraction of c.
  escape: ratio => Math.sqrt(1 / ratio),
  // Factor by which light climbing out to infinity is stretched in wavelength.
  redshift: ratio => 1 / Model.rate(ratio),
  scientific(value) { const e = Math.floor(Math.log10(value)); return e > 5 ? (Math.round(value / 10 ** e * 100) / 100) + ' × 10^' + e : String(Math.round(value * 100) / 100); },''',
    '''  const M = 10 ** v.mass, rs = Model.radius(M), p = Kit.plot(canvas, {x: [0, 20], y: [0, 1.1], xlabel: 'distance ÷ Schwarzschild radius', ylabel: 'clock rate'});
  p.line(1, 0, 1, 1.1, '#172533', 2, [5, 5]); p.curve(r => Model.rate(r), '#215783', 1.0001, 20); p.point(v.ratio, Model.rate(v.ratio), '#963d18', 7); p.text('horizon', 1, 1, '#172533', 6, 0);
  return {sum: 'Your clock runs at ' + Kit.fmt(100 * Model.rate(v.ratio), 4) + '% of the far-away rate',
    rows: [['Mass', Model.scientific(M) + ' solar masses'], ['Schwarzschild radius', Model.scientific(rs) + ' km'], ['Your distance from the centre', Model.scientific(rs * v.ratio) + ' km'], ['Clock rate compared with far away', Kit.fmt(Model.rate(v.ratio), 4)], ['Seconds lost each day', Kit.fmt(Model.lostPerDay(v.ratio), 4)], ['Escape speed', Kit.fmt(Model.escape(v.ratio), 3) + ' c'], ['Light sent outward is stretched by', Kit.fmt(Model.redshift(v.ratio), 4) + ' times']],
    result: 'The Schwarzschild radius grows in step with the mass: about 3 km for each solar mass. The clock rate depends only on how many Schwarzschild radii away you hover. At the horizon the rate reaches zero and the escape speed reaches c. These figures are for a non-rotating mass and an observer held in place, not one in orbit or falling in.'};''', height=420,
    aria='Curve of clock rate against distance from the black hole, with the horizon marked.')

add('force-range', 'phys.5.qft', 'Quantum Field Theory', 'Why some forces reach further than others',
    'In quantum field theory a force is carried by a field whose particle has a mass. The heavier the carrier, the shorter the reach.',
    [('carrier', select('carrier', 'Force carrier', [('pion', 'Pion (nuclear force between protons and neutrons)'), ('w', 'W boson (weak force)'), ('z', 'Z boson (weak force)'), ('photon', 'Photon (electromagnetism)')])), ('r', slider('r', 'Distance (femtometres)', 0.1, 5, 1.4, 0.1))], ['Carrier', 'Mass (MeV)', 'Range (fm)'],
    '''  // ħc in MeV·fm.
  HBARC: 197.3269804,
  // Rest energies in MeV.
  MASSES: {pion: 139.57, w: 80377, z: 91187.6, photon: 0},
  NAMES: {pion: 'Pion', w: 'W boson', z: 'Z boson', photon: 'Photon'},
  // Range ħ/(mc) in femtometres; unlimited for a massless carrier.
  range: name => Model.MASSES[name] ? Model.HBARC / Model.MASSES[name] : Infinity,
  // Yukawa potential relative to a Coulomb-like 1/r potential at the same distance.
  suppression: (name, r) => Model.MASSES[name] ? Math.exp(-r / Model.range(name)) : 1,
  // Shape of the potential, e^(−r/range)/r, in arbitrary units.
  potential: (name, r) => Model.suppression(name, r) / r,''',
    '''  const range = Model.range(v.carrier), p = Kit.plot(canvas, {x: [0, 5], y: [0, 6], xlabel: 'distance (fm)', ylabel: 'strength of the potential (arbitrary units)'}), f = n => Number.isFinite(n) ? Kit.fmt(n, 3) : 'unlimited';
  p.curve(r => 1 / r, '#9aa6ae', 0.1, 5, 1.5); p.curve(r => Model.potential(v.carrier, r), '#215783', 0.1, 5); p.point(v.r, Model.potential(v.carrier, v.r), '#963d18', 6); p.text('1/r (massless carrier)', 2.6, 0.5, '#7a8790', 0, -10);
  return {sum: Model.NAMES[v.carrier] + ': range ' + (Number.isFinite(range) ? Kit.fmt(range, 3) + ' fm' : 'unlimited'),
    rows: Object.keys(Model.MASSES).map(name => [(name === v.carrier ? '→ ' : '') + Model.NAMES[name], String(Model.MASSES[name]), f(Model.range(name))]),
    result: Number.isFinite(range) ? 'At ' + v.r + ' fm the potential is cut to ' + Kit.fmt(100 * Model.suppression(v.carrier, v.r), 3) + '% of what a massless carrier would give. The range is ħ ÷ (mass × c): about the size of a nucleus for the pion, and a thousand times smaller than a proton for the W and Z, which is why the weak force seems weak.' : 'The photon has no mass, so electromagnetism has unlimited range and its potential falls only as 1/r. (The gluon is also massless, but the strong force is short-ranged for a different reason: confinement.)'};''', height=440,
    aria='The potential against distance for the chosen carrier, compared with a massless carrier.', caption='Carriers')

add('qubit-gates', 'phys.5.quantum-info', 'Quantum Information', 'One qubit: states, gates and measurement',
    'A qubit can be in a blend of 0 and 1. Gates turn the state; measuring gives 0 or 1 with probabilities set by the amplitudes.',
    [('theta', slider('theta', 'Polar angle θ (degrees)', 0, 180, 60, 5)), ('phi', slider('phi', 'Phase φ (degrees)', 0, 345, 0, 15)), ('gate', select('gate', 'Gate applied', [('H', 'Hadamard H'), ('X', 'X (bit flip)'), ('Z', 'Z (phase flip)'), ('none', 'none')]))], ['Quantity', 'Before the gate', 'After the gate'],
    '''  // State cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩ as [[re, im], [re, im]].
  state(thetaDeg, phiDeg) { const t = thetaDeg * Math.PI / 360, f = phiDeg * Math.PI / 180; return [[Math.cos(t), 0], [Math.sin(t) * Math.cos(f), Math.sin(t) * Math.sin(f)]]; },
  apply(gate, [a, b]) {
    const s = Math.SQRT1_2;
    if (gate === 'X') return [b, a];
    if (gate === 'Z') return [a, [-b[0], -b[1]]];
    if (gate === 'H') return [[s * (a[0] + b[0]), s * (a[1] + b[1])], [s * (a[0] - b[0]), s * (a[1] - b[1])]];
    return [a, b];
  },
  // Probabilities of measuring 0 and 1.
  probabilities: ([a, b]) => [a[0] ** 2 + a[1] ** 2, b[0] ** 2 + b[1] ** 2],
  // Bloch vector (x, y, z).
  bloch([a, b]) { return [2 * (a[0] * b[0] + a[1] * b[1]), 2 * (a[0] * b[1] - a[1] * b[0]), a[0] ** 2 + a[1] ** 2 - b[0] ** 2 - b[1] ** 2]; },''',
    '''  const before = Model.state(v.theta, v.phi), after = Model.apply(v.gate, before), P0 = Model.probabilities(before), P1 = Model.probabilities(after), B0 = Model.bloch(before), B1 = Model.bloch(after), p = Kit.plot(canvas, {x: [-1.5, 1.5], y: [-1.5, 1.5], grid: false}), f = n => Kit.fmt(Math.abs(n) < 1e-12 ? 0 : n, 3).replace('-', '−');
  for (let i = 0; i < 120; i++) p.line(Math.cos(i * Math.PI / 60), Math.sin(i * Math.PI / 60), Math.cos((i + 1) * Math.PI / 60), Math.sin((i + 1) * Math.PI / 60), '#9aa6ae', 1.5);
  p.line(-1, 0, 1, 0, '#d8dfe4', 1); p.line(0, -1, 0, 1, '#d8dfe4', 1); p.text('|0⟩', 0, 1, '#172533', -10, -10); p.text('|1⟩', 0, -1, '#172533', -10, 22); p.text('x', 1, 0, '#172533', 8, 4);
  p.arrow(0, 0, B0[0], B0[2], '#215783'); p.arrow(0, 0, B1[0], B1[2], '#963d18'); p.text('before', B0[0], B0[2], '#215783'); p.text('after', B1[0], B1[2], '#963d18', 8, 14);
  return {sum: 'P(0) = ' + f(P1[0]) + ', P(1) = ' + f(P1[1]) + ' after the gate',
    rows: [['Chance of measuring 0', f(P0[0]), f(P1[0])], ['Chance of measuring 1', f(P0[1]), f(P1[1])], ['Bloch vector x', f(B0[0]), f(B1[0])], ['Bloch vector y', f(B0[1]), f(B1[1])], ['Bloch vector z', f(B0[2]), f(B1[2])]],
    result: 'The arrow shows the state on the Bloch sphere, seen from the side (x across, z up; y points into the page). X swaps the poles, Z reverses x and y, and H exchanges the z and x directions. The phase φ changes nothing if you measure straight away, but it changes what H does: that is interference.'};''', height=SQUARE,
    aria='A side view of the Bloch sphere with the state before and after the gate.', caption='Before and after')

if __name__ == '__main__':
    print(base.build(), 'activities')
