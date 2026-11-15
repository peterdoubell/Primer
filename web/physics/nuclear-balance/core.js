'use strict';
(()=>{
const particle = (label, nucleons, charge) => ({label,nucleons,charge});
const cases = [
  {id:'alpha',title:'Alpha emission',input:[particle('U-238 nucleus',238,92)],
   output:[particle('Th-234 nucleus',234,90),particle('He-4 nucleus (alpha)',4,2)],
   note:'The daughter has two fewer protons and two fewer neutrons. The emitted alpha particle carries both.',
   source:'https://nucleus.iaea.org/sites/nuclear-instrumentation/Shared%20Documents/Basic%20Nuclear%20Physics/Basic%20Nuclear%20Physics%20Lecture.pdf'},
  {id:'beta',title:'Carbon-14 beta-minus decay',input:[particle('C-14 nucleus',14,6)],
   output:[particle('N-14 nucleus',14,7),particle('Electron',0,-1),particle('Electron antineutrino',0,0)],
   note:'One neutron becomes a proton. Nuclear charge rises by one; the emitted electron balances total charge. Zero nucleons does not imply zero rest mass.',
   source:'https://www2.lbl.gov/abc/Basic.html'},
  {id:'fusion',title:'Deuterium–tritium fusion',input:[particle('H-2 nucleus',2,1),particle('H-3 nucleus',3,1)],
   output:[particle('He-4 nucleus',4,2),particle('Neutron',1,0)],
   note:'The two initial nuclei contain five nucleons and two proton charges in total. The helium nucleus and neutron retain those totals.',
   source:'https://www.energy.gov/science/doe-explainsfusion-reactions'},
  {id:'fission',title:'One neutron-induced fission channel',input:[particle('U-235 nucleus',235,92),particle('Incident neutron',1,0)],
   output:[particle('Ba-141 nucleus',141,56),particle('Kr-92 nucleus',92,36),particle('Neutron 1',1,0),particle('Neutron 2',1,0),particle('Neutron 3',1,0)],
   note:'This is one illustrated product channel. The incoming neutron is included in the total. Actual fission has many product channels; no yield or chain-reaction model is supplied.',
   source:'https://openstax.org/books/chemistry/pages/21-4-transmutation-and-nuclear-energy'},
  {id:'gamma',title:'Gamma transition bookkeeping',input:[particle('Excited nucleus X*',40,20)],
   output:[particle('Lower-energy nucleus X',40,20),particle('Gamma photon',0,0)],
   note:'This generic transition illustrates the counting rule. A photon removes excitation energy while the nucleus keeps its nucleon count and charge. No particular excitation level or transition energy is specified.',
   source:'https://www2.lbl.gov/abc/Basic.html'},
];
function totals(rows) {
  return rows.reduce((sum,row)=>({
    nucleons:sum.nucleons+row.nucleons,
    charge:sum.charge+row.charge,
  }),{nucleons:0,charge:0});
}
function ledger(id) {
  const example=cases.find(row=>row.id===id);
  if(!example)throw RangeError('Unknown reaction');
  return {example,before:totals(example.input),after:totals(example.output)};
}
function checkMissingNucleus(id,nucleons,charge) {
  if(!Number.isInteger(nucleons)||!Number.isInteger(charge)||charge<0||nucleons<charge)return false;
  const {example,before}=ledger(id);
  const proposed=totals([{nucleons,charge},...example.output.slice(1)]);
  return proposed.nucleons===before.nucleons&&proposed.charge===before.charge;
}
const api={cases,totals,ledger,checkMissingNucleus};
if(typeof module!=='undefined')module.exports=api;
globalThis.PrimerNuclearBalance=api;

})();
