// Compare every labelled structure's original focal section on each source axis with
// the section reader used by the app. No source pixels are replaced in this check.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gunzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { nativeReader, FetchPool, sourceAssetName } from '../../web/anatomy/segthy-001/native-volume.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const directory = path.join(root, 'web/anatomy/ct-torso-s0028');
const manifest = JSON.parse(await fs.readFile(path.join(directory, 'manifest.json'), 'utf8'));
const proof = JSON.parse(await fs.readFile(path.join(root, 'docs/ct-torso-s0028/source-comparison.json'), 'utf8'));
const files = new Map();
for (let i=0;i<299;i+=64) for(let j=0;j<299;j+=64) for(let k=0;k<394;k+=64) {
  const file=`brick-${i}-${j}-${k}.gz`;files.set(file,path.join(directory,file));
}
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
async function read(brick) {
  const filename=files.get(sourceAssetName('ct-torso-s0028',brick.file));
  if(!filename)throw Error('Unknown archive brick.');
  const packed=await fs.readFile(filename);
  assert.equal(digest(packed),brick.sha256);
  const decoded=gunzipSync(packed);
  assert.equal(digest(decoded),brick.decodedSHA256);
  return decoded.buffer.slice(decoded.byteOffset,decoded.byteOffset+decoded.byteLength);
}
const reader=nativeReader(manifest,new FetchPool(3),read,150*1024*1024);
let total=0;
for(const item of proof.probes){
  const label=manifest.labels.find(row=>row.sourceLabel===item.class);
  for(const section of item.sections){
    const key=['jk','ik','ij'][section.axis],plane=await reader.section(key,item.position);
    const mask=Uint8Array.from(plane.labels,(code,at)=>Number(code===label.code || plane.overlap[at]===label.code));
    assert.equal(digest(mask),section.maskSha256,item.class+' '+key+' complete mask');
    assert.equal(digest(new Uint8Array(plane.image.buffer)),section.imageSha256,item.class+' '+key+' complete CT');
    total++;
  }
}
console.log(total+' original CT planes and complete membership masks match. Peak parallel fetches: '+reader.stats().maximumConcurrentFetches);
