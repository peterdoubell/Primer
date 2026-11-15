'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process');
const root=path.resolve(__dirname,'..'),work=path.join(root,'.research','plane-shapes-preservation'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
fs.mkdirSync(work,{recursive:true});
if(process.argv[2]==='capture'){
 const mode=process.argv[3];
 // Reuse the checker's fixed dependency inventory. Only repository-authored
 // modules are executed; the historical module is an exact Git blob copy.
 const setup=fs.readFileSync(path.join(root,'tools/check_module_models.js'),'utf8').split('const spatial = context.window.PrimerSpatial')[0].replace("const root = path.resolve(__dirname, '..');",'const root = '+JSON.stringify(root)+';').replace(/require\('([.][.]\/web\/[^']+)'\)/g,(_,name)=>'require('+JSON.stringify(path.resolve(root,'tools',name))+')');
 const runner=setup.replace('require('+JSON.stringify(path.join(root,'web/spatial-module-objects.js'))+');','require('+JSON.stringify(mode==='before'?path.join(work,'before-shapes-module.js'):path.join(root,'web/spatial-module-objects.js'))+');')+`
const bindingData=JSON.parse(fs.readFileSync(path.join(root,'data/module-models.json')));const rows=[];let lessons=0;
for(const b of bindingData.models){
 if(b.node_id==='math.0.shapes')continue;
 const scenario='module.'+b.node_id;const node=JSON.parse(fs.readFileSync(path.join(root,'data/curriculum',fs.readdirSync(path.join(root,'data/curriculum')).find(f=>JSON.parse(fs.readFileSync(path.join(root,'data/curriculum',f))).nodes.some(n=>n.id===b.node_id))))).nodes.find(n=>n.id===b.node_id);
 const item={title:b.title,instructions:b.instructions,props:{scenario,family:b.family,context:b.context,mode:b.mode,lesson:node.title}};
 assert(context.window.PrimerModuleObjects.ensure(item));
 const controls=context.window.PrimerSpatial.controls(scenario),states=[{}];
 for(const c of controls){for(const v of c.options?c.options.map(x=>x.value):[c.min,c.max])states.push({[c.key]:v});}
 for(const state of states){const scene=context.window.PrimerSpatial.build(scenario,state);rows.push([scenario,state,require('crypto').createHash('sha256').update(JSON.stringify(scene)).digest('hex')]);}
 lessons++;
}process.stdout.write(JSON.stringify({lessons,rows}));`;
 fs.writeFileSync(path.join(work,'shape-preservation-runner.cjs'),runner);require(path.join(work,'shape-preservation-runner.cjs'));
}else{
 fs.writeFileSync(path.join(work,'before-shapes-module.js'),cp.execFileSync('git',['show','6d8ee107da8c29fd62de5a5d93fd18b533a543c3:web/spatial-module-objects.js'],{cwd:root}));
 const capture=mode=>cp.execFileSync(process.execPath,[__filename,'capture',mode],{cwd:root,maxBuffer:20*1024*1024});
 const before=capture('before'),current=capture('current');require('assert/strict').deepEqual(JSON.parse(current),JSON.parse(before));const data=JSON.parse(current);
 const proof={baselineCommit:'6d8ee107da8c29fd62de5a5d93fd18b533a543c3',scope:'All 461 unchanged module bindings; default and each control choice or endpoint independently. New shape model is verified separately.',unchangedLessons:data.lessons,identicalSceneStates:data.rows.length,allPassed:true,recordSHA256:sha(current),baselineModuleSHA256:sha(fs.readFileSync(path.join(work,'before-shapes-module.js'))),currentModuleSHA256:sha(fs.readFileSync(path.join(root,'web/spatial-module-objects.js'))),currentBindingsSHA256:sha(fs.readFileSync(path.join(root,'data/module-models.json'))),extendsHistoricalScientificApproval:false};
 fs.writeFileSync(path.join(root,'docs/plane-shapes-review-20261023/preservation-proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
}
