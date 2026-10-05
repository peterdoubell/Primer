'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {contourDisplayPoints,sourcePointDisplayError}=require('./anatomy_sources/viewers/renal-volume/source-lines.js');
const root=path.resolve(__dirname,'..'),meta=JSON.parse(fs.readFileSync(path.join(root,'docs/cptac-renal-source-review/volume-reference/export-provenance.json')));
const source=JSON.parse(fs.readFileSync(path.join(root,'docs/cptac-renal-source-review/volume-reference/original-source-polylines.json')));
const size=meta.texture_shape_xyz.map((n,a)=>n*meta.source_spacing_xyz_mm[a]),scale=Math.max(...size),centre=meta.origin_lps_mm.map((v,a)=>v+(meta.texture_shape_xyz[a]-1)*meta.source_spacing_xyz_mm[a]/2);
let points=0,maximum=0;
for(const c of source.contours){const mapped=contourDisplayPoints(c.source_decimal_lps_xyz_mm,meta);assert.equal(mapped.length,c.points*3);for(let i=0;i<mapped.length;i++){assert(Math.abs(mapped[i]*scale+centre[i%3]-Number(c.source_decimal_lps_xyz_mm[i]))<1e-10);}assert.equal(Number(c.source_decimal_lps_xyz_mm[2]),meta.frames[c.native_acquisition1_plane_index].source_position_lps_mm[2]);points+=c.points;maximum=Math.max(maximum,sourcePointDisplayError(c.source_decimal_lps_xyz_mm,meta));}
assert.equal(source.contours.length,75);assert.equal(points,5341);assert(maximum<.000004);
console.log('Verified all 75 source polylines / 5,341 points, reversible LPS display mapping and float32 error bound',maximum);
