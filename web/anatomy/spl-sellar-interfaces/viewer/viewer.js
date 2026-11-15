import {installMesh} from './mesh.js';
import {sha} from './transport.js';
const expected='fb077721b7947000cf5126928ae0d561627bda3a1da62d6a4b2ca55b9b3e8562';
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
  if(manifest.schemaVersion!==1||manifest.contactFaces!==652||manifest.clinicalApproval!==false||manifest.anatomicalBoundaryValidated!==false)throw Error('Source scope differs');
  reader=installMesh(manifest);window.SourceContactReview=reader;window.SellarContactManifest=manifest;document.getElementById('pair').value='3011:3012';document.getElementById('pair').dispatchEvent(new Event('change'));
 }catch(error){document.getElementById('mesh-status').textContent='Source review unavailable: '+error.message+'. Use Retry.';}
 finally{clearTimeout(timer);loading=false;document.getElementById('retry').disabled=false;}
}
document.getElementById('retry').onclick=()=>reader?reader.loadMesh():initialize();
initialize();

document.getElementById('pair').addEventListener('change',async()=>{const m=window.SellarContactManifest,g=m.groups.find(g=>g.firstCode+':'+g.secondCode===document.getElementById('pair').value),host=document.getElementById('schematics');host.replaceChildren();for(const file of g?.schematicFiles||[]){const img=new Image();img.src=file;img.alt='Exact source categorical section and contact';img.style.width='100%';host.append(img);}});
