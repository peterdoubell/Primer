import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const dir = path.resolve('web/anatomy/lynos-pat9');
const fixtureFile = path.resolve('docs/lynos-pat9-source-review/map-native-plane-evidence.json');
const source = JSON.parse(await readFile(path.join(dir, 'source.json')));
const fixture = JSON.parse(await readFile(fixtureFile));
const { nativeSectionReader } = await import(pathToFileURL(path.join(dir, 'native-sections.mjs')));
const { paintMaskMap, maskNamesAt, overlapColour } = await import(pathToFileURL(path.join(dir, 'mask-map.mjs')));
const readPacked = async name => {
  const content = await readFile(path.join(dir, name));
  return content.buffer.slice(content.byteOffset, content.byteOffset + content.byteLength);
};
const reader = nativeSectionReader(source, readPacked);
const byLabel = new Map(source.nodalLabels.map(row => [row.label, row]));
const anatomyByRole = new Map(source.nearbyAnnotations.map(row => [row.transportRole, row]));
const hash = buffer => createHash('sha256').update(buffer).digest('hex');

let sampleCount = 0;
for (const entry of fixture.sectionFixtures) {
  const read = role => reader.section(role, entry.orientation, entry.fixedDisplayLASIndex);
  const ct = await read('ct');
  const nodes = await read('nodes');
  assert.equal(nodes.width, entry.width);
  assert.equal(nodes.height, entry.height);
  assert.deepEqual(ct.spacingMm, entry.horizontalAndVerticalSpacingMm);
  assert.deepEqual(ct.directions, entry.displayDirectionsTopBottomLeftRight);
  assert.equal(hash(new Uint8Array(ct.pixels.buffer)), entry.originalCTPlaneInt16LeSha256);
  const landmarks = await Promise.all(source.nearbyAnnotations.map(async annotation =>
    ({ annotation, section: await read(annotation.transportRole) })));
  const section = { nodes, landmarks };
  const raster = new Uint8ClampedArray(entry.width * entry.height * 4);
  const result = paintMaskMap(raster, { width:entry.width, height:entry.height, x0:0, y0:0 },
    nodes, landmarks, byLabel);
  const overlaps = Object.values(entry.overlapPatternCounts).reduce((a,b) => a+b,0);
  assert.equal(result.overlaps, overlaps);
  const allMaskCounts = entry.positiveNodalVoxels +
    Object.values(entry.anatomicalMaskVoxels).reduce((a,b) => a+b,0);
  assert.equal(result.occupied, allMaskCounts-overlaps);
  const nodeIds = [...result.counts.keys()].filter(row => row.label).map(row => row.label).sort((a,b)=>a-b);
  assert.deepEqual(nodeIds,entry.uniqueNodalIDs);
  for (const [original, count] of result.counts) {
    const expected = original.label ? entry.nodalIDVoxelCounts[original.label]
      : entry.anatomicalMaskVoxels[original.transportRole];
    assert.equal(count,expected);
  }
  for (const role of Object.keys(fixture.membershipBitsByRole)) {
    const data = role==='nodes' ? nodes : landmarks.find(row=>row.annotation.transportRole===role).section;
    assert.equal(hash(new Uint8Array(data.pixels.buffer)),entry.roleMaskPlaneDecodedSHA256[role]);
  }
  for (const sample of entry.pixelMembershipSamples) {
    const [x,y] = sample.canvasXY;
    const index = x + entry.width*y;
    assert.equal(ct.pixels[index],sample.originalStoredCTValue);
    const expectedNames = [];
    const nodalId = sample.sourceRoleMemberships.nodes;
    if (nodalId) expectedNames.push(byLabel.get(nodalId).name);
    for (const item of source.nearbyAnnotations) {
      if (sample.sourceRoleMemberships[item.transportRole]) expectedNames.push(item.name);
    }
    assert.deepEqual(maskNamesAt(section,x,y,byLabel),expectedNames);
    let expectedColor = [22,30,38];
    if (sample.members.length>1) expectedColor = overlapColour;
    else if (nodalId) expectedColor = byLabel.get(nodalId).color;
    else if (sample.members.length===1) expectedColor = anatomyByRole.get(sample.members[0]).color;
    assert.deepEqual([...raster.slice(index*4,index*4+4)],[...expectedColor,255]);
    sampleCount++;
  }
}
console.log(JSON.stringify({nativePlanes:fixture.sectionFixtures.length, sampledMembershipPixels:sampleCount,
  overlapTypes:fixture.allOriginalOverlapPatterns.length, checkedEveryRolePlaneHash:true,
  exactMaskCountsAndAreas:true, exactSourceValuesAndSpacing:true}));
