const examples=[
  {
    label:'The cyclist and the binoculars',
    subject:'Mira',verb:'saw',action:'Seeing the cyclist',object:'the cyclist',phrase:'with binoculars',
    meanings:['Mira used binoculars to see the cyclist.','Mira saw a cyclist who had binoculars.'],
    clues:['Mira was watching the road through her binoculars.','The cyclist had binoculars hanging from a strap. Mira noticed the binoculars with her unaided eyes.'],
  },
  {
    label:'The assistant and the umbrella',
    subject:'Dev',verb:'photographed',action:'Taking the photograph',object:'the assistant',phrase:'with the umbrella',
    meanings:['Dev used the umbrella while taking the photograph.','Dev photographed the assistant who had the umbrella.'],
    clues:['Dev shielded the camera from rain with the umbrella while the assistant stood under the porch.','The assistant held the umbrella above his head while Dev took the photograph.'],
  },
  {
    label:'The bag and the bench',
    subject:'Sam',verb:'opened',action:'Opening the bag',object:'the bag',phrase:'on the bench',
    meanings:['Sam opened the bag while on the bench.','Sam opened the bag that was on the bench.'],
    clues:['Sam sat on the bench and opened a bag she was holding.','Two bags were nearby. Sam reached for the one on the bench and opened it while standing on the pavement.'],
  },
];
const get=id=>document.getElementById(id);
const picker=get('example');
const context=get('context');
const feedback=get('feedback');

function element(tag,text){
 const node=document.createElement(tag);
 node.textContent=text;
 return node;
}

function tree(row,toNoun){
 const root=document.createElement('ul');
 root.className='tree';
 root.setAttribute('aria-label',toNoun?'Noun attachment tree':'Action attachment tree');
 const sentence=element('li','Sentence');
 const level=document.createElement('ul');
 const subject=element('li','Subject');
 const subjectLevel=document.createElement('ul');
 subjectLevel.append(element('li',row.subject));
 subject.append(subjectLevel);
 const action=element('li','Verb phrase');
 const content=document.createElement('ul');
 const noun=element('li','Object noun phrase');
 const nounLevel=document.createElement('ul');
 nounLevel.append(element('li',row.object));
 const phrase=document.createElement('li');
 const marker=element('span','Prepositional phrase · '+row.phrase);
 marker.className='attachment';
 phrase.append(marker);
 if(toNoun) nounLevel.append(phrase);
 noun.append(nounLevel);
 content.append(element('li',row.verb),noun);
 if(!toNoun)content.append(phrase);
 action.append(content);
 level.append(subject,action);
 sentence.append(level);
 root.append(sentence);
 return root;
}

function showClue(){
 const row=examples[picker.selectedIndex];
 get('clue').textContent=row.clues[context.selectedIndex];
 feedback.textContent='';
}

function render(){
 const row=examples[picker.selectedIndex];
 get('sentence').textContent=[row.subject,row.verb,row.object,row.phrase].join(' ')+'.';
 get('action-tree').replaceChildren(tree(row,false));
 get('noun-tree').replaceChildren(tree(row,true));
 for(const [index,id] of ['action-meaning','noun-meaning'].entries())get(id).textContent=row.meanings[index];
 get('comparison').replaceChildren(...row.meanings.map((meaning,index)=>{
  const tr=document.createElement('tr');
  const head=element('th',index===0?'Action attachment':'Noun phrase attachment');
  head.scope='row';
  tr.append(head,element('td',index===0?row.action:row.object),element('td',meaning));
  return tr;
 }));
 context.selectedIndex=0;
 showClue();
}

function answer(pick){
 const row=examples[picker.selectedIndex];
 const correct=context.selectedIndex;
 feedback.textContent=(pick===correct?'That reading fits. ':'Compare the other reading. ')+row.meanings[correct];
}

picker.replaceChildren(...examples.map(row=>new Option(row.label)));
picker.addEventListener('change',render);
context.addEventListener('change',showClue);
get('answer-action').addEventListener('click',()=>answer(0));
get('answer-noun').addEventListener('click',()=>answer(1));
render();
