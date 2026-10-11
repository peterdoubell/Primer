/* Exact QFT quantities in calibrated charts, with explicit topological diagram layout. */
(function () {
  'use strict';
  const options=xs=>xs.map(([value,label])=>({value,label}));
  const family={
    title:'Fields, momenta and matched observables',requires:'PrimerPhysicsQftLab',linkedStateKey:'phys.5.qft',
    initialFactory:()=>({...window.PrimerPhysicsQftLab.initial}),
    normalize:raw=>window.PrimerPhysicsQftLab.normalize(raw),
    controlsFactory:()=>{const a=window.PrimerPhysicsQftLab;return [{key:'mode',label:'Quantum field theory station',options:options(a.stations)},...[...a.controls,...a.choices].map(c=>({...c,numericInput:!c.options,preserveExact:!c.options,options:c.options?options(c.options):undefined,visibleWhen:{mode:c.modes,...(c.key==='phaseDeg'?{correctionKind:['amplitude']}:{} )}}))];},
    build(state,g){const a=window.PrimerPhysicsQftLab,m=a.build(state),charts=[],extra=[];
      const line=(pts,color,kind,data={})=>{if(pts.length>1)g.line(pts,color,{width:1.5,fidelity_kind:kind,...data});};
      for(let i=0;i<m.panels.length;i++){
        const p=m.panels[i],all=p.curves.flatMap(c=>c.points).concat(p.markers||[]),xmin=Math.min(0,...all.map(v=>v.x)),xmax=Math.max(0,...all.map(v=>v.x)),ymin=Math.min(0,...all.map(v=>v.y)),ymax=Math.max(0,...all.map(v=>v.y));
        const sharedGain=Math.min(5/(xmax-xmin||1),3/(ymax-ymin||1)),xGain=p.equalScale?sharedGain:5/(xmax-xmin||1),yGain=p.equalScale?sharedGain:3/(ymax-ymin||1),origin=[-2.5,0,i*4],map=v=>[origin[0]+(v.x-xmin)*xGain,origin[1]+(v.y-ymin)*yGain,origin[2]];
        line([map({x:xmin,y:ymin}),map({x:xmax,y:ymin})],g.colors.ink,'qft_chart_x_axis',{panel:i});
        line([map({x:xmin,y:ymin}),map({x:xmin,y:ymax})],g.colors.ink,'qft_chart_y_axis',{panel:i});
        g.label([-2.5,-.45,i*4],'Chart '+(i+1));
        const graphs=[];
        p.curves.forEach((c,j)=>{const color=[g.colors.teal,g.colors.blue,g.colors.gold][j%3],pts=c.points.map(map),discrete=c.xUnit.includes('occupation index');if(!discrete)line(pts,color,'qft_curve',{panel:i,key:c.key});else pts.forEach((v,k)=>g.sphere(v,.035,color,{fidelity_kind:'qft_discrete_occupation',panel:i,key:c.key,index:k}));graphs.push({key:c.key,source:c.points,points:pts,discrete});});
        const markers=(p.markers||[]).map(v=>{const point=map(v);g.sphere(point,.065,g.colors.coral,{fidelity_kind:'qft_marker',panel:i,key:v.key});return {...v,point};});
        charts.push({index:i,title:p.title,origin,xmin,xmax,ymin,ymax,xGain,yGain,graphs,markers,xUnit:p.curves[0].xUnit,yUnit:p.curves[0].yUnit});
      }
      if(m.state.mode==='scattering'){
        // Actual COM momentum vectors have components (p_x c, p_y c, p_z c).
        const scale=2/Math.max(1,m.state.momentumMeV),origin=[0,-3,0];
        for(const key of ['p1','p2','p3','p4','qt']){const v=m.current[key].slice(1),point=v.map((x,i)=>origin[i]+x*scale);line([origin,point],key==='qt'?g.colors.coral:g.colors.blue,'qft_momentum_vector',{key});g.sphere(point,.05,g.colors.blue,{fidelity_kind:'qft_momentum_endpoint',key});extra.push({kind:'momentum',key,value:v,origin,point,gain:scale});}
        // The diagram graph carries topology only; its line lengths are not spacetime or travel time.
        const offset=[0,-5,5];for(const e of m.geometry.diagram.edges){const pts=[e.from,e.to].map(v=>v.map((x,i)=>x+offset[i]));line(pts,e.internal?g.colors.gold:g.colors.teal,'qft_diagram_edge',{key:e.label,internal:e.internal});g.label(pts[0],e.label);extra.push({kind:'diagram',...e,points:pts,offset});}
      }else if(m.state.mode==='modes'){
        // Three axes carry momentum, occupation, and excitation energy with declared independent units.
        const d=m.current,pg=2/Math.max(...d.rows.map(v=>Math.abs(v.pc))),ng=2/Math.max(1,m.state.occupation),eg=2/Math.max(1,d.excitationEnergy),origin=[0,-4,0];
        for(const r of d.rows){const point=[origin[0]+r.pc*pg,origin[1]+r.occupation*ng,origin[2]+r.excitation*eg];g.sphere(point,.06,g.colors.teal,{fidelity_kind:'qft_mode_coordinate',j:r.j});extra.push({kind:'mode',source:r,point,origin,pGain:pg,nGain:ng,eGain:eg});}
      }else if(m.state.mode==='casimir'){
        // Coordinates form a field-factor chart over real normalized x/a and z/a inputs.
        const s=m.state,points=[],xGain=2,zGain=2,factorGain=.7,origin=[-1,-4,0];
        for(let xi=0;xi<=16;xi++)for(let zi=0;zi<=24;zi++){const xA=xi/16,zA=zi/24,factor=Math.sin(s.normalMode*Math.PI*zA)*Math.cos(m.current.kparallel*m.current.a*xA),point=[origin[0]+xA*xGain,origin[1]+factor*factorGain,origin[2]+zA*zGain];points.push({xA,zA,factor,point});}
        const at=(xi,zi)=>points[xi*25+zi];
        for(let xi=0;xi<16;xi++)for(let zi=0;zi<24;zi++)g.polygon([at(xi,zi).point,at(xi+1,zi).point,at(xi+1,zi+1).point,at(xi,zi+1).point],g.colors.blue,{fidelity_kind:'qft_standing_factor',cell:[xi,zi],opacity:.35});
        extra.push({kind:'standing-factor',points,origin,xGain,zGain,factorGain,notVectorEM:true});
      }
      const parameters=[...a.controls,...a.choices].filter(c=>a.controlActive(c,m.state)).map(c=>c.label+': '+(c.options?c.options.find(o=>o[0]===m.state[c.key])[1]:m.state[c.key])+(c.unit?' '+c.unit:'')).join('. ');
      const calibration=charts.map(c=>'Chart '+(c.index+1)+': x gain '+c.xGain.toPrecision(16)+' per '+c.xUnit+', y gain '+c.yGain.toPrecision(16)+' per '+c.yUnit+', origin '+c.origin.join(', ')+'.').join(' ');
      const extraCalibration=extra.length?m.state.mode==='scattering'?' Momentum components map to x,y,z with gain '+extra.find(v=>v.kind==='momentum').gain.toPrecision(16)+' per MeV. Diagram edges preserve contribution topology only.':m.state.mode==='modes'?' The extra coordinate graph has x=pc, y=occupation, z=excitation energy with gains '+extra[0].pGain.toPrecision(16)+' per MeV, '+extra[0].nGain.toPrecision(16)+' per quantum, '+extra[0].eGain.toPrecision(16)+' per MeV, and origin '+extra[0].origin.join(', ')+'. Mode points are discrete.':' The extra surface is sin(nπz/a)cos(k∥x), plotted over x/a,z/a at gains 2,2 and field-factor gain 0.7. It is a scalar mode-factor chart.':'';
      return {state:m.state,readout:m.readout+' '+parameters+'. '+calibration+extraCalibration,note:m.note+' Chart depth and origins separate displays. Each chart is a calibrated quantitative plot, not a physical spatial field. The exchange diagram is a categorical contribution graph, never a particle path. A camera move preserves the complete lesson state.',legend:[{label:'Declared exact model',color:g.colors.teal},{label:'Comparison / field factor',color:g.colors.blue},{label:'Selected value / internal contribution',color:g.colors.coral}],qft:{state:m.state,current:m.current,charts,extra}};
    }
  };
  if(typeof window!=='undefined')window.PrimerQftSpatialFamily=family;
  if(typeof module!=='undefined'&&module.exports)module.exports=family;
})();
