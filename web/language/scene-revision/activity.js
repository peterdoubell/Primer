const passages = [
  {
    title:'Opening',
    prompt:'Deadline',
    versions:[
      { label:'Earlier draft', text:'Ananda was very late for the ferry and felt worried.', effect:'The reader is told Ananda is late but sees no evidence of the deadline.' },
      { label:'Use a visible signal', text:'The clock above the ferry gate read 18:59. Beside it, the board blinked LAST FERRY · 19:00.', effect:'The clock and departure board give the reader two times to compare.', passes:true },
      { label:'Add atmosphere', text:'Mist had settled over the water, turning the ferry lights into soft yellow circles.', effect:'The mist makes the setting visible. The departure time remains open.' },
    ],
  },
  {
    title:'Dialogue',
    prompt:'Consequence',
    versions:[
      { label:'Earlier draft', text:'“You’d better hurry,” the gatekeeper said.', effect:'The advice signals urgency but leaves the consequence unstated.' },
      { label:'State what pressing the gate does', text:'“If you press that gate, the alarm locks it for five minutes,” the gatekeeper said. “Use the side ramp.”', effect:'The reader can anticipate a five-minute delay and knows there is another route.', passes:true },
      { label:'Explain the gatekeeper’s mood', text:'“I’ve been on my feet since six,” the gatekeeper said. “This shift has felt endless.”', effect:'The exchange suggests the gatekeeper’s fatigue. It gives Ananda no information about the gate.' },
    ],
  },
  {
    title:'Decision',
    prompt:'Choice',
    versions:[
      { label:'Earlier draft', text:'Ananda made a decision and hurried towards the ferry.', effect:'Ananda acts, but the draft never specifies which way or why.' },
      { label:'Act on the warning', text:'Ananda pulled her hand away from the gate and ran down the side ramp.', effect:'The action uses the alternative route and avoids the delay described in the revised dialogue.', passes:true, needsWarning:true },
      { label:'Press the gate', text:'Ananda shoved the gate open and reached the deck in a few seconds.', effect:'The action makes the choice explicit. If the warning is in the scene, this outcome contradicts it.' },
    ],
  },
];
const get=id=>document.getElementById(id);
const picks=[];

function element(tag,text) {
  const node=document.createElement(tag);
  node.textContent=text;
  return node;
}

function versions() {
  return passages.map((passage,index)=>passage.versions[picks[index].selectedIndex]);
}

function hasEvidence(choices,index) {
  const selected=choices[index];
  return Boolean(selected.passes && (!selected.needsWarning || choices[1].passes));
}

function render() {
  const choices=versions();
  get('scene').replaceChildren(...choices.map(row=>element('p',row.text)));
  get('map').replaceChildren(...passages.map((row,index)=>
    element('li',row.prompt+' · '+(hasEvidence(choices,index)?'supported':'needs revision'))));
  get('effects').replaceChildren(...choices.map((choice,index)=>{
    const row=document.createElement('tr');
    const heading=element('th',passages[index].title);
    heading.scope='row';
    const effect=choice.needsWarning && !choices[1].passes ?
      'The draft names the side ramp for the first time in the ending. Add the warning so the choice has a cause.' : choice.effect;
    row.append(heading,element('td',effect));
    return row;
  }));
  get('result').textContent='';
}

for(const [index,passage] of passages.entries()){
  const field=document.createElement('div');
  const label=element('label',passage.title);
  const select=document.createElement('select');
  select.id='revision-'+index;
  label.htmlFor=select.id;
  select.replaceChildren(...passage.versions.map(version=>new Option(version.label)));
  select.addEventListener('change',render);
  field.append(label,select);
  get('controls').append(field);
  picks.push(select);
}
get('original').replaceChildren(...passages.map(passage=>element('p',passage.versions[0].text)));
get('review').addEventListener('click',()=>{
  const choices=versions();
  const score=choices.filter((_,index)=>hasEvidence(choices,index)).length;
  get('result').textContent=score===3 ?
    'All three parts of the brief are met. Read the revised scene aloud to check the rhythm.' :
    score+' of 3 parts of the brief are met. Use the passage table to see what still needs a change.';
});
get('reset').addEventListener('click',()=>{
  for(const select of picks) select.selectedIndex=0;
  render();
  picks[0].focus();
});
render();
