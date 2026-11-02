'use strict';
// Direct imports execute the same dual-environment modules served to the reader.
const core=require('../web/physics-particle-core.js');
const ledger=require('../web/physics-particle-ledger.js');
module.exports={...core,...ledger};
