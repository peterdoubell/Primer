'use strict';

const get = id => document.getElementById(id);
const svg = get('chart');
const kpcInMetres = 149597870700 * 648000000 / Math.PI;
const accelerationUnit = 1e16 / kpcInMetres;
const signedSquare = value => value * Math.abs(value);
const format = value => Number(value.toPrecision(4)).toString();
let catalog;

function node(tag, attributes, text) {
  const element = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
  if (text !== undefined) element.textContent = text;
  svg.append(element);
}

function calculate(source, diskWeight, bulgeWeight) {
  const [radius, speed, error, gas, disk, bulge] = source.map(Number);
  const baryon2 = signedSquare(gas) + diskWeight * signedSquare(disk) + bulgeWeight * signedSquare(bulge);
  return {radius, speed, error, baryon2, baryonSpeed: baryon2 >= 0 ? Math.sqrt(baryon2) : null,
    difference: (speed ** 2 - baryon2) / radius * accelerationUnit};
}

function plot(name, rows, showSpeed, selected) {
  const xMax = Math.max(...rows.map(row => row.radius));
  const extremes = showSpeed
    ? rows.flatMap(row => [row.speed - row.error, row.speed + row.error, row.baryonSpeed ?? 0])
    : rows.map(row => row.difference);
  const minimum = Math.min(0, ...extremes), maximum = Math.max(0, ...extremes);
  const step = (maximum - minimum) / 4 || 1;
  const x = radius => 78 + radius / xMax * 526;
  const y = value => 280 - (value - minimum) / (4 * step) * 248;
  const unit = showSpeed ? 'Speed (km/s)' : 'Acceleration difference (10⁻¹⁰ m/s²)';
  svg.replaceChildren();
  node('title', {id:'chart-title'}, name + ' · ' + unit + ' by radius');
  for (let i = 0; i <= 4; i++) {
    const radius = i * xMax / 4, value = minimum + step * i;
    node('line',{x1:x(radius),x2:x(radius),y1:32,y2:280,class:'grid'});
    node('line',{x1:78,x2:604,y1:y(value),y2:y(value),class:'grid'});
    node('text',{x:x(radius),y:302,'text-anchor':'middle'},format(radius));
    node('text',{x:70,y:y(value)+5,'text-anchor':'end'},format(value));
  }
  node('line',{x1:78,x2:604,y1:y(0),y2:y(0),class:'axis'});
  node('text',{x:78,y:20},unit);
  node('text',{x:341,y:328,'text-anchor':'middle'},'Radius (kpc)');

  if (showSpeed) {
    let path = '', previous = false;
    for (const row of rows) {
      if (row.baryonSpeed === null) { previous = false; continue; }
      path += (previous ? 'L' : 'M') + x(row.radius) + ',' + y(row.baryonSpeed) + ' ';
      previous = true;
    }
    node('path',{d:path,class:'model'});
  }
  for (const [i,row] of rows.entries()) {
    const cx = x(row.radius), cy = y(showSpeed ? row.speed : row.difference);
    if (showSpeed) node('line',{x1:cx,x2:cx,y1:y(row.speed-row.error),y2:y(row.speed+row.error),class:'error','data-row':i});
    node('circle',{cx,cy,r:3,class:'point','data-row':i});
    if (i === selected) node('circle',{cx,cy,r:7,class:'selected'});
  }
}

function update() {
  const name = get('galaxy').value, source = catalog[name].rows;
  const diskWeight = get('disk').valueAsNumber, bulgeWeight = get('bulge').valueAsNumber;
  get('disk-value').textContent = diskWeight.toFixed(2);
  get('bulge-value').textContent = bulgeWeight.toFixed(2);
  const rows = source.map(row => calculate(row,diskWeight,bulgeWeight));
  const showSpeed = get('quantity').value === 'speed', index = get('radius').selectedIndex;
  const point = rows[index];
  plot(name,rows,showSpeed,index);
  get('legend').textContent = showSpeed
    ? 'Blue dots and bars show the observed speeds and published velocity errors. Gold connects the calculated baryonic speeds at the sampled radii.'
    : 'Blue dots show the acceleration difference calculated at each published radius. The horizontal axis line marks zero.';
  get('sample').textContent = 'At ' + source[index][0] + ' kpc, observed speed ' + source[index][1] + ' ± ' +
    source[index][2] + ' km/s. ' +
    (point.baryonSpeed === null ? 'The net baryonic force points outward here. ' : 'Baryonic circular speed ' + format(point.baryonSpeed) + ' km/s. ') +
    'Acceleration difference ' + format(point.difference) + ' × 10⁻¹⁰ m/s².';
  const body = get('source-rows');
  body.querySelector('[aria-current]')?.removeAttribute('aria-current');
  body.rows[index].setAttribute('aria-current','true');
}

function selectGalaxy() {
  const name = get('galaxy').value, galaxy = catalog[name], source = galaxy.rows;
  const quality = ['high','medium','low'][galaxy.quality-1];
  const meta = name + ' · ' + source.length + ' radii · distance ' + galaxy.distanceMpc + ' ± ' + galaxy.distanceErrorMpc +
    ' Mpc · inclination ' + galaxy.inclinationDegrees + ' ± ' + galaxy.inclinationErrorDegrees + '° · SPARC Q' + galaxy.quality + ' (' + quality + ').';
  get('metadata').textContent = meta +
    (galaxy.quality === 3 || Number(galaxy.inclinationDegrees) < 30 ? ' SPARC excluded this galaxy from its final science sample.' : '');
  get('table-caption').textContent = name + ' · original values in km/s except radius';
  get('radius').replaceChildren(...source.map((row,i) => new Option((i+1) + ' · ' + row[0] + ' kpc',i)));
  const body = get('source-rows');
  body.replaceChildren();
  for (const values of source) {
    const row = body.insertRow();
    for (const value of values.slice(0,6)) row.insertCell().textContent = value;
  }
  update();
}

async function start() {
  get('retry').hidden = true;
  get('status').textContent = 'Loading 175 galaxy profiles…';
  try {
    const response = await fetch('source.json');
    if (!response.ok) throw Error('Source table unavailable');
    const bytes = await response.arrayBuffer();
    const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))]
      .map(value => value.toString(16).padStart(2,'0')).join('');
    if (hash !== 'd0402343c859bcf393e3b274f82f18cd99d85fb048de99d4ccc03b0f47608371') throw Error('Source checksum differs');
    const data = JSON.parse(new TextDecoder().decode(bytes));
    catalog = data.galaxies;
    const entries = Object.entries(catalog);
    const count = entries.reduce((sum,[,galaxy]) => sum + galaxy.rows.length,0);
    if (entries.length !== 175 || count !== 3391) throw Error('Source table is incomplete');
    const picker = get('galaxy');
    for (const flag of [1,2,3]) {
      const group = document.createElement('optgroup');
      group.label = 'SPARC quality ' + flag;
      for (const [name,galaxy] of entries) if (galaxy.quality === flag) group.append(new Option(name,name));
      picker.append(group);
    }
    picker.value = 'NGC3198';
    selectGalaxy();
    get('explorer').hidden = false;
    get('status').textContent = '175 galaxies · 3,391 published radial samples.';
  } catch {
    get('galaxy').replaceChildren();
    get('status').textContent = 'The source table could not be loaded.';
    get('retry').hidden = false;
  }
}

get('retry').addEventListener('click',start);
get('galaxy').addEventListener('change',selectGalaxy);
for (const id of ['disk','bulge','quantity','radius']) get(id).addEventListener('input',update);
svg.addEventListener('click',event => {
  const row = event.target.dataset.row;
  if (row === undefined) return;
  get('radius').value = row;
  update();
});
start();
