// Execute the actual clock functions with a deterministic browser clock.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source=fs.readFileSync('web/app.js','utf8');
const code=source.slice(source.indexOf('let readingClock = null;'),source.indexOf('function prepareReaderContext'));
let now=1000; const sent=[]; const events={};
const ctx={Date:{now:()=>now}, fetch:(_url,options)=>{sent.push(JSON.parse(options.body));return Promise.resolve();},
 document:{visibilityState:'visible',addEventListener:(e,f)=>events[e]=f},
 window:{addEventListener:(e,f)=>events[e]=f},S:{view:'reader',title:'Plant'}};
vm.createContext(ctx); vm.runInContext(code,ctx);
const run=(s)=>vm.runInContext(s,ctx);
run("startReadingClock('Plant')"); now+=30000;
run("pauseReadingClock('tutor')"); assert.equal(sent.at(-1).seconds,30);
now+=10000; run("pauseReadingClock('picture')");
now+=10000; run("resumeReadingClock('tutor')");
now+=10000; run("pauseReadingClock('paper')");
now+=10000; run("resumeReadingClock('picture')");
ctx.document.visibilityState='hidden';events.visibilitychange();
now+=10000;ctx.document.visibilityState='visible';events.visibilitychange();
assert.equal(run('Object.keys(readingClock.holds).join()'),'paper');
run("resumeReadingClock('paper')");now+=30000;run('stopReadingClock()');
assert.equal(sent.at(-1).seconds,60);
assert.match(source,/focusin.*pauseReadingClock\('tutor'\)/);
assert.match(source,/pointerenter.*pauseReadingClock\('tutor-pointer'\)/);
assert.match(source,/onClose: \(\) => resumeReadingClock\('picture'\)/);
console.log('Reading clock: overlapping tutor, picture, paper and visibility holds preserve 60 seconds of actual reading.');
