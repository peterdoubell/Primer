"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const sandbox = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../web/radiology-detailed-anatomy.js"), "utf8"), sandbox);
const label = sandbox.window.PrimerDetailedAnatomy.viewOrientation;

test("RAS and LPS references preserve anatomical directions without reflecting the model", () => {
  const project = sandbox.window.PrimerDetailedAnatomy.displayPoint;
  const plain = value => JSON.parse(JSON.stringify(value));
  assert.deepEqual(plain(project([10, 20, 30], false, true)), [-10, 30, 20]);
  // The same world location encoded in LPS yields the same display position.
  assert.deepEqual(plain(project([-10, -20, 30])), [-10, 30, 20]);
  assert.deepEqual(plain(project([-10, 30, 20], true)), [-10, 30, 20]);
  const x=project([1,0,0],false,true), y=project([0,1,0],false,true), z=project([0,0,1],false,true);
  const determinant=x[0]*(y[1]*z[2]-y[2]*z[1])-x[1]*(y[0]*z[2]-y[2]*z[0])+x[2]*(y[0]*z[1]-y[1]*z[0]);
  assert.equal(determinant,1,"Display conversion is a rotation, not a reflection");
});

test("lateral and medial presets follow the source side", () => {
  const presets=sandbox.window.PrimerDetailedAnatomy.anatomicalPresets;
  for (const side of ["left","right"]) {
    const lateral=presets(side).find(p=>p[0]==="Lateral");
    const medial=presets(side).find(p=>p[0]==="Medial");
    assert.equal(label({yaw:lateral[1],pitch:lateral[2]}),side === "left" ? "Left lateral" : "Right lateral");
    assert.equal(medial[1],-lateral[1]);
  }
});

test("anatomical view labels describe the current camera, not the last button", () => {
  assert.equal(label({ yaw: 0, pitch: 0 }), "Anterior");
  assert.equal(label({ yaw: Math.PI, pitch: 0 }), "Posterior");
  assert.equal(label({ yaw: Math.PI / 2, pitch: 0 }), "Right lateral");
  assert.equal(label({ yaw: -Math.PI / 2, pitch: 0 }), "Left lateral");
  assert.equal(label({ yaw: 0, pitch: Math.PI / 2 }), "Superior");
  assert.equal(label({ yaw: 0, pitch: -Math.PI / 2 }), "Inferior");
  assert.equal(label({ yaw: 4 * Math.PI, pitch: 0 }), "Anterior");
  assert.match(label({ yaw: 0.3, pitch: 0 }), /^Rotated view/);
  assert.match(label({ yaw: 0, pitch: 1.25 }), /^Rotated view/);
  assert.match(label({ yaw: Math.PI, pitch: 0.1 }), /^Rotated view/);
});

test("whole-foot preset frames every native pedal bone without changing source geometry", () => {
  const data = JSON.parse(fs.readFileSync(path.join(__dirname, "../web/anatomy/msk-atlas/manifest.json"), "utf8"));
  const before = JSON.stringify(data), region = data.regions.ankle;
  const preset = sandbox.window.PrimerDetailedAnatomy.sourceView({ family:"foot", atlas:"z-anatomy", view:"whole-foot" }, data, region);
  const bones = region.parts.map(entry=>({...data.parts[entry.id],...entry}))
    .filter(part=>part.layer === "bone" && !["Tibia.r","Fibula.r"].includes(part.name));
  assert.equal(bones.length,27);
  assert.deepEqual(JSON.parse(JSON.stringify(preset.boneIds)).sort(),bones.map(part=>part.id).sort());
  for (const part of bones) for (let axis=0;axis<3;axis++) {
    assert.ok(preset.focusBounds[0][axis] < part.bounds[0][axis],part.name+": complete lower bound");
    assert.ok(preset.focusBounds[1][axis] > part.bounds[1][axis],part.name+": complete upper bound");
  }
  assert.equal(preset.range[0],Math.min(...bones.map(part=>part.bounds[0][1]))-.5);
  assert.equal(preset.range[1],Math.max(...bones.map(part=>part.bounds[1][1]))+.5);
  assert.ok(preset.range[1] < region.source_up_range[1],"Do not frame long lower-leg shafts");
  assert.equal(preset.focusBounds[1][2],Math.max(...bones.map(part=>part.bounds[1][2]))+.5,"Include distal toes in anterior extent");
  assert.equal(label(preset.camera),"Superior");
  assert.equal(JSON.stringify(data),before,"Preset does not alter any part, region or coordinate");
  assert.equal(sandbox.window.PrimerDetailedAnatomy.sourceView({ family:"ankle", atlas:"z-anatomy" },data,region),null,"Ankle default remains unchanged");
});

test("whole-foot preset refuses a subset or another atlas and derives bounds from actual toes", () => {
  const data = JSON.parse(fs.readFileSync(path.join(__dirname, "../web/anatomy/msk-atlas/manifest.json"), "utf8"));
  const options={family:"foot",atlas:"z-anatomy",view:"whole-foot"}, region=data.regions.ankle;
  assert.throws(()=>sandbox.window.PrimerDetailedAnatomy.sourceView({...options,atlas:"malaya-ankle"},data,region),/registered/);
  const target=region.parts.find(entry=>data.parts[entry.id].name === "Distal phalanx of second finger of foot.r");
  assert.throws(()=>sandbox.window.PrimerDetailedAnatomy.sourceView(options,data,{...region,parts:region.parts.filter(entry=>entry.id!==target.id)}),/every named pedal bone/);
  data.parts[target.id].bounds[1][2]+=10;
  const preset=sandbox.window.PrimerDetailedAnatomy.sourceView(options,data,region);
  assert.equal(preset.focusBounds[1][2],data.parts[target.id].bounds[1][2]+.5,"Distal extent follows the source mesh bounds");
});

test('hamstring view preserves the full four-muscle source envelope', () => {
  const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../web/anatomy/msk-atlas/manifest.json'),'utf8'));
  const sourceView=sandbox.window.PrimerDetailedAnatomy.sourceView;
  const options={view:'hamstrings',atlas:'z-anatomy',family:'knee'};
  const view=sourceView(options,data,data.regions.knee);
  assert.equal(view.partIds.length,9);
  assert.equal(view.divisionIds.length,2);
  assert.equal(view.muscleIds.length,4);
  assert.equal(view.contextIds.length,3);
  assert.equal(view.initialLayer,'muscle');
  assert.equal(view.camera.yaw,Math.PI);
  for(const id of view.framingIds) {
    const part=data.parts[id];
    for(let axis=0;axis<3;axis++) {
      assert.ok(view.focusBounds[0][axis]<part.bounds[0][axis]);
      assert.ok(view.focusBounds[1][axis]>part.bounds[1][axis]);
    }
    assert.ok(view.range[0]<part.bounds[0][1] && view.range[1]>part.bounds[1][1]);
  }
  assert.ok(view.range[1]>data.regions.knee.source_up_range[1]);
  assert.ok(data.parts[view.divisionIds[0]].bounds[0][1]<view.range[0]);
  assert.equal(view.cropLabel,"Thigh reference extent");
  assert.throws(()=>sourceView({...options,atlas:'malaya-mri'},data,data.regions.knee));
  const changed=JSON.parse(JSON.stringify(data)); delete changed.parts[view.partIds[0]];
  assert.throws(()=>sourceView(options,changed,changed.regions.knee));
});

test('hamstring preset rejects changed side, identity, tissue and malformed bounds', () => {
  const original=JSON.parse(fs.readFileSync(path.join(__dirname,'../web/anatomy/msk-atlas/manifest.json'),'utf8'));
  const options={view:'hamstrings',atlas:'z-anatomy',family:'knee'};
  for(const mutate of [
    d=>{d.regions.knee.side='left'}, d=>{d.regions.hip.side='left'},
    d=>{d.parts['za-nerves-809851269'].name='Sciatic nerve.l'},
    d=>{d.parts['za-joints-558314782'].layer='nerve'},
    d=>{d.parts['za-muscles-63886170'].bounds=[]},
    d=>{d.parts['za-muscles-63886170'].bounds=[[0,0],[1,1]]},
    d=>{d.parts['za-muscles-63886170'].bounds=[[1,1,1],[0,0,0]]},
  ]) {
    const data=JSON.parse(JSON.stringify(original)); mutate(data);
    assert.throws(()=>sandbox.window.PrimerDetailedAnatomy.sourceView(options,data,data.regions.knee));
  }
});
