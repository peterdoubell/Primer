/* Original listening comparisons. Local Web Audio, no recordings, no autoplay. */
(function () {
 'use strict';
 const event = (notes, beats=1) => ({notes,beats});
 const examples = {
  1: {prompt:'Listen to the two four-note phrases. Which one rises throughout?',a:[60,62,64,65].map(n=>event([n])),b:[65,64,62,60].map(n=>event([n])),answer:'A rises (C–D–E–F); B falls (F–E–D–C). Echo each phrase, then keep the pulse while reversing its contour.'},
  2: {prompt:'Compare the last four notes of A natural and harmonic minor. Which version has the stronger semitone pull into A?',a:[64,65,67,69].map(n=>event([n])),b:[64,65,68,69].map(n=>event([n])),answer:'B uses G-sharp–A; A uses G–A. The raised seventh changes the final interval from a tone to a semitone.'},
  3: {prompt:'Each example contains six equal short sounds. Which groups them as two main beats rather than three?',a:[72,60,72,60,72,60].map(n=>event([n],.5)),b:[72,60,60,72,60,60].map(n=>event([n],.5)),answer:'B groups 3+3, suggesting 6/8. A groups 2+2+2, suggesting 3/4. The higher tones mark the intended accents; all six subdivisions have equal length.'},
  4: {prompt:'Both examples finish on C major. Compare the approach: which begins on the dominant?',a:[event([55,59,62],2),event([48,60,64],2)],b:[event([53,57,60],2),event([48,60,64],2)],answer:'A is V–I (G major to C major), a perfect cadence. B is IV–I (F major to C major), a plagal cadence. Sing the bass movement before naming it.'},
  5: {prompt:'Each example uses C-major chord tones. Which has the chord third as its lowest note?',a:[event([48,55,64],3)],b:[event([52,55,60],3)],answer:'B has E in the bass and is first inversion. A has C in the bass and is root position. The identity of the uppermost note is not the test.'},
  6: {prompt:'Which dominant-seventh example resolves to the tonic, rather than to the submediant?',a:[event([43,59,65],2),event([48,60,64],2)],b:[event([43,59,65],2),event([45,60,64],2)],answer:'A resolves G7–C, V7–I. B resolves G7–A minor, V7–vi, an interrupted effect. In both, listen to B rising to C and F falling to E.'},
  7: {prompt:'Listen for a prepared note held over the dominant before resolving down. Which example delays that resolution?',a:[event([53,60,65],1),event([55,60,62],1),event([55,59,62],1)],b:[event([53,60,65],1),event([55,59,62],2)],answer:'A delays C–B over the G bass, giving the effect of a 4–3 suspension; B moves directly to the third. The C is held across the bass change; compare this with the engraved tie.'},
  8: {prompt:'Compare two short textures. Which lets the lower treble line move while the upper note continues?',a:[event([48,60,64],.5),event([48,62,64],.5),event([48,60,67],1),event([48,60,64],2)],b:[event([48,60,64],1),event([50,62,65],1),event([48,60,64],2)],answer:'A gives the lower treble line separate rhythmic movement; B moves the voices together. Neither four-beat sketch is a complete contrapuntal composition: use it to focus your listening before working on a full score.'},
 };
 function sequence(ex,key) {
  let beat=0; const segments=[], active=new Map();
  ex[key].forEach(e=>{
   const next=new Map();
   e.notes.forEach(midi=>{
    const old=(key==='a' && (ex===examples[7] || ex===examples[8])) ? active.get(midi) : null;
    if(old) { old.beats+=e.beats; next.set(midi,old); }
    else { const segment={midi,start:beat,beats:e.beats,gain:.12/e.notes.length};segments.push(segment);next.set(midi,segment); }
   }); active.clear(); next.forEach((v,k)=>active.set(k,v)); beat+=e.beats;
  }); return {segments,beats:beat};
 }
 const frequency = midi => 440*Math.pow(2,(midi-69)/12);
 function render(item) {
  const ex=examples[item.props.grade]; if(!ex)return null;
  const root=document.createElement('section');root.className='card lesson-model music-listening';root.dataset.renderer='music-listening-lab';
  const add=(tag,text,cls)=>{const el=document.createElement(tag);if(text)el.textContent=text;if(cls)el.className=cls;root.append(el);return el;};
  add('h3',item.title);add('p',ex.prompt);
  const row=add('div',null,'music-audio-controls');
  let context=null, voices=[], timer=null, generation=0;
  const status=add('p','Ready. Choose A or B; sound starts only when you press Play.','muted');status.setAttribute('role','status');
  const answer=add('p',ex.answer,'music-audio-answer');answer.hidden=true;
  const stop=()=>{generation++;voices.forEach(o=>{try{o.stop();}catch(e){/* already ended */}});voices=[];clearTimeout(timer);status.textContent='Stopped.';};
  const play=async key=>{
   stop();const token=generation;
   const Audio=window.AudioContext||window.webkitAudioContext;
   if(!Audio){status.textContent='Audio is unavailable here. Use Show explanation and the notation plate.';return;}
   try {
    if(!context)context=new Audio();await context.resume();if(token!==generation||!root.isConnected)return;
    const start=context.currentTime+.05, score=sequence(ex,key);
    score.segments.forEach(segment=>{
      const when=start+segment.start*60/90, duration=segment.beats*60/90;
      const oscillator=context.createOscillator(),gain=context.createGain();
      oscillator.type='sine';oscillator.frequency.value=frequency(segment.midi);
      gain.gain.setValueAtTime(0,when);gain.gain.linearRampToValueAtTime(segment.gain,when+.015);
      gain.gain.setValueAtTime(segment.gain,when+Math.max(.02,duration-.06));gain.gain.linearRampToValueAtTime(0,when+duration-.01);
      oscillator.connect(gain);gain.connect(context.destination);oscillator.start(when);oscillator.stop(when+duration);voices.push(oscillator);
    });
    const when=start+score.beats*60/90;
    status.textContent='Playing '+key.toUpperCase()+'.';
    timer=setTimeout(()=>{status.textContent='Finished '+key.toUpperCase()+'.';voices=[];},(when-context.currentTime)*1000+50);
   }catch(e){status.textContent='Sound could not start. Try again, or use the written explanation.';}
  };
  [['Play A',()=>play('a')],['Play B',()=>play('b')],['Stop',stop],['Show explanation',()=>{answer.hidden=!answer.hidden;reveal.textContent=answer.hidden?'Show explanation':'Hide explanation';reveal.setAttribute('aria-expanded',String(!answer.hidden));}]].forEach(([label,action])=>{
   const b=document.createElement('button');b.className='btn';b.type='button';b.textContent=label;b.addEventListener('click',action);row.append(b);
  });
  const reveal=row.lastElementChild;reveal.setAttribute('aria-expanded','false');
  add('p','Original synthesised examples at a fixed pulse. They train comparison, not instrumental tone or performance grading. Sing within a comfortable range; listening and written explanations are both available.','muted');
  const observer=new MutationObserver(()=>{if(!root.isConnected){stop();if(context)context.close();observer.disconnect();}});
  // Observe only after the synchronous renderer has attached the card.
  queueMicrotask(()=>{if(root.isConnected)observer.observe(document.body,{childList:true,subtree:true});});
  return root;
 }
 window.PrimerMusic=Object.freeze({render,frequency,sequence,examples});
}());
