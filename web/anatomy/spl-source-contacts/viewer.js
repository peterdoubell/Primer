import {installMesh} from './mesh.js';
import {sha} from './transport.js';
const expected='c5ca712f4ee1a0b92f97e2ca50c8260f2dc09ad6669556835cfeef4703b31c2e';
let reader,loading=false;
async function initialize(){
 if(loading)return;
 loading=true;document.getElementById('retry').disabled=true;
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);
 try{
  const response=await fetch('manifest.json',{credentials:'same-origin',signal:controller.signal});
  if(!response.ok)throw Error('Source metadata unavailable');
  const raw=new Uint8Array(await response.arrayBuffer());
  if(await sha(raw)!==expected)throw Error('Source metadata identity differs');
  const manifest=JSON.parse(new TextDecoder().decode(raw));
  if(manifest.schemaVersion!==1||manifest.contactFaces!==274109||manifest.clinicalApproval!==false||manifest.anatomicalBoundaryValidated!==false)throw Error('Source scope differs');
  reader=installMesh(manifest);window.SourceContactReview=reader;
 }catch(error){document.getElementById('mesh-status').textContent='Source review unavailable: '+error.message+'. Use Retry.';}
 finally{clearTimeout(timer);loading=false;document.getElementById('retry').disabled=false;}
}
document.getElementById('retry').onclick=()=>reader?reader.loadMesh():initialize();
initialize();
