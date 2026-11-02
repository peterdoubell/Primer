'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.resolve(__dirname,'..');
const context=vm.createContext({window:{}});
for(const name of ['core','ledger'])vm.runInContext(fs.readFileSync(path.join(root,'web/physics-particle-'+name+'.js'),'utf8'),context);
module.exports={...context.window.PrimerParticleCore,...context.window.PrimerParticleLedger};
