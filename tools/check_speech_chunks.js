#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const { splitForSpeech: split, SPEAK_CHUNK: limit } = require('../web/speech-chunks.js');
const excerpt='At t = 0.75 s: x = −1.25 m; E = 1.67783 m/s²; p = 0.01; tail = 2.331e−40. Source DOI 10.1007/s11604-023-01400-7. Read https://example.org/a.b/c?value=0.05. Temperature is 293.15 K. Does p reach 0.99? It need not. ';
const texts=[excerpt.repeat(25),('Pressure 123.456 kPa, velocity −0.00025 m/s and value 0.5. ').repeat(45),
 'First sentence... Next sentence! A quote ends here.") Last value is 0.75.',
 ('Long list with no full stop: 0.125 1.25 −3.5 6.023e23 ').repeat(55),null,''];
let cases=0;
for(const text of texts){
 const clean=String(text??'').replace(/\s+/g,' ').trim(), parts=Array.from(split(text));
 assert.equal(parts.join(' '),clean,'Chunking may only replace existing whitespace, never split numeric tokens.');
 assert.ok(parts.every(p=>p.length<=limit && p.length>0));cases++;
}
for(const number of ['0.75','1.67783','293.15','2.331e−40','123.456','−0.00025']){
 const parts=Array.from(split((excerpt+number+' ').repeat(20)));
 assert.ok(parts.some(p=>p.includes(number)));assert.equal(parts.join(' ').match(new RegExp(number.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),'g')).length,
  (excerpt+number+' ').repeat(20).match(new RegExp(number.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),'g')).length);cases++;
}
console.log(`Verified ${cases} actual speech splitter cases; decimal, scientific, signed, DOI/URL and long-caption tokens preserved with bounded chunks.`);
