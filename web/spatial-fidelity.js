/* Calibrated topology and spacetime views of the same authored lesson state. */
(function () {
  'use strict';
  const TAU = 2 * Math.PI;
  const fmt = n => Number.isFinite(n) ? Number(n.toPrecision(6)).toString() : String(n);
  const line = (g, points, color, kind, extra = {}) => {
    if (points.length >= 2) g.line(points, color, {width: 2.2, fidelity_kind: kind, ...extra});
  };
  const axes = (g, origin, ends, names) => ends.forEach((end, i) => {
    line(g, [origin, end], g.colors.ink, 'axis', {width: 1}); g.label(end, names[i]);
  });
  const legend = g => [{label: 'Exact source data / selected object', color:g.colors.blue},
    {label:'Comparison / reference',color:g.colors.teal}, {label:'Excluded endpoint / witness',color:g.colors.coral}];
  function parameters(controls,state) {
    return controls.filter(c=>(!c.stations||c.stations.includes(state.station))&&(!c.modes||c.modes.includes(state.mode))&&
      !(state.mode==='gravity'&&(c.key==='heightM'&&state.gravitySystem!=='tower'||['orbitAltitudeKm','clockCorrection'].includes(c.key)&&state.gravitySystem!=='gps')))
      .map(c=>c.label+' '+(c.options?(c.options.find(o=>(o.value??o[0])===state[c.key])?.label??c.options.find(o=>o[0]===state[c.key])?.[1]??state[c.key]):fmt(state[c.key]))+(c.unit?' '+c.unit:''))
      .join('. ');
  }
  const topology = {
    title:'Open sets and actual topological surfaces', requires:'PrimerMathTopologyLab', linkedStateKey:'math.5.topology',
    initialFactory:() => ({...window.PrimerMathTopologyLab.initial}),
    normalize:raw => window.PrimerMathTopologyLab.normalize(raw),
    controlsFactory:() => window.PrimerMathTopologyLab.controls.map(c => ({...c,
      numericInput:!c.options,preserveExact:!c.options,visibleWhen:c.stations?{station:c.stations}:undefined})),
    build(s,g) {
      const lab=window.PrimerMathTopologyLab,m=lab.build(s),d=m.active,primitives=[];
      const record=(kind,data)=>primitives.push({kind,...data});
      if(s.station==='T1') {
        const positions=Array.from({length:8},(_,mask)=>[mask&1?1:-1,mask&2?1:-1,mask&4?1:-1]);
        for(let mask=0;mask<8;mask++) {
          const point=positions[mask],included=d.opens.includes(mask);
          g.sphere(point,.09,included?g.colors.blue:g.colors.coral,{fidelity_kind:'subset',mask,included});
          g.label([point[0],point[1]+.2,point[2]],lab.setName(mask)); record('subset',{mask,point,included});
          for(let bit=0;bit<3;bit++)if(!(mask&(1<<bit)))line(g,[point,positions[mask|(1<<bit)]],g.colors.teal,'subset_inclusion',{width:1});
        }
        g.label([0,-1.6,0],'Subset lattice; no metric');
      } else if(s.station==='T2') {
        const left=Array.from({length:3},(_,i)=>[-2,1.2-1.2*i,0]),right=Array.from({length:3},(_,i)=>[2,1.2-1.2*i,0]);
        for(let i=0;i<3;i++) {
          g.sphere(left[i],.12,g.colors.blue);g.sphere(right[i],.12,g.colors.teal);
          g.label([left[i][0]-.4,left[i][1],0],'X: '+['a','b','c'][i]);g.label([right[i][0]+.4,right[i][1],0],'Y: '+['a','b','c'][i]);
          line(g,[left[i],right[d.mapping[i]]],g.colors.gold,'map',{source:i,target:d.mapping[i]});
          record('map',{source:i,target:d.mapping[i],points:[left[i],right[d.mapping[i]]]});
        }
        g.label([0,-2,0],'Exact preimages in ledger');
      } else if(s.station==='T3') {
        axes(g,[0,0,0],[[5,0,0],[0,2,0],[0,0,2]],['x; gain 5','Selected index n: y=.03(n−2)','Closed-cover layout z=1+.03j']);
        d.selected.forEach((u,i)=>{const points=[[5*u.start,.03*i,0],[5*u.end,.03*i,0]];line(g,points,g.colors.blue,'open_cover_interval');record('open_cover_interval',{interval:u,points});});
        line(g,[[0,-.3,0],[5*d.omittedBoundary,-.3,0]],g.colors.coral,'uncovered_interval');
        g.sphere([5*d.witness,-.3,0],.07,g.colors.coral,{fidelity_kind:'uncovered_witness'});
        d.closedCover.forEach((u,i)=>{const points=[[5*u.start,0,1+.03*i],[5*u.end,0,1+.03*i]];line(g,points,g.colors.teal,'closed_interval_cover');});
        record('uncovered_witness',{value:d.witness,point:[5*d.witness,-.3,0]});
        g.label([2.5,-.8,0],'Open ends; finite witness');
      } else if(s.station==='T4') {
        const span=Math.max(d.witness,...d.excludedUnion.map(Math.abs),1),gain=4/span;
        axes(g,[0,0,0],[[4,0,0],[0,1,0],[0,0,1]],['Finite window of the infinite real line','U = R minus finite A','V = R minus finite B']);
        for(const [set,z,color] of [[d.excludedA,0,g.colors.blue],[d.excludedB,1,g.colors.teal]]) {
          line(g,[[0,0,z],[4,0,z]],color,'cofinite_window');
          for(const value of set)g.sphere([gain*value,0,z],.07,g.colors.coral,{fidelity_kind:'excluded_point',value});
        }
        const point=[gain*d.witness,.15,.5];g.sphere(point,.1,g.colors.gold);record('intersection_witness',{value:d.witness,point,gain});
        g.label([2,-.65,.5],'Witness in both opens');
      } else if(s.station==='T5') {
        const graph=d.graph.map(p=>[4*p[0],p[1],0]),vertical=d.vertical.map(p=>[4*p[0],p[1],0]);
        line(g,graph,g.colors.blue,'finite_sine_graph');line(g,vertical,g.colors.teal,'limiting_segment');
        for(const p of d.sequence)g.sphere([4*p.x,p.y,0],.035,g.colors.gold,{fidelity_kind:'closure_sequence',n:p.n});
        g.sphere([4*d.selected.x,d.selected.y,0],.07,g.colors.coral);
        record('finite_sine_graph',{points:graph,xMin:d.xMin});record('limiting_segment',{points:vertical});
        axes(g,[0,0,0],[[4,0,0],[0,1,0],[0,0,.5]],['x; gain 4','sin(1/x); gain 1','Layout plane']);
        g.label([2,-1.5,0],'Unresolved infinite tail');
      } else if(s.station==='T6') {
        const vertices=d.vertices.map(p=>[p[0],p[2],-p[1]]);
        d.faces.forEach((face,i)=>g.polygon(face.map(j=>vertices[j]),g.colors.blue,{stroke:false,opacity:.84,fidelity_kind:'surface_triangle',face:i}));
        const offset=Math.max(...vertices.map(p=>p[0]))+3;
        const curve=d.figureEight.map(p=>[p[0]+offset,p[2],-p[1]]);
        line(g,curve,g.colors.teal,'separate_figure_eight');g.sphere([offset,0,0],.08,g.colors.coral);
        g.label([0,1,0],'Closed surface: g='+d.genus+'; V−E+F='+d.counts.chi);
        g.label([offset,.8,0],'Marked crossing, separate');
        record('surface',{vertices,faces:d.faces,counts:d.counts,determinant:d.jacobianDeterminant});
        record('figure_eight',{points:curve,offset});
      } else {
        const circle=d.circle.map(p=>[p[0],p[1],0]);line(g,circle,g.colors.blue,'circle');
        const interval=[[3,-1,0],[3,1,0]];line(g,interval,g.colors.teal,'source_interval');
        g.sphere([3,-1,0],.06,g.colors.teal,{fidelity_kind:'included_endpoint'});
        if(d.domain==='halfopen')line(g,Array.from({length:33},(_,i)=>[3+.08*Math.cos(TAU*i/32),1+.08*Math.sin(TAU*i/32),0]),g.colors.coral,'excluded_endpoint');
        else g.sphere([3,1,0],.06,g.colors.teal,{fidelity_kind:'included_endpoint'});
        record('source_domain',{domain:d.domain,startIncluded:true,endIncluded:d.domain!=='halfopen',endpointEquivalence:d.domain==='quotient'});
        const map=t=>[3,-1+t/Math.PI,0];
        const selectedSource=map(d.angle),selectedImage=[d.selected[0],d.selected[1],0];
        g.sphere(selectedSource,.07,g.colors.gold);g.sphere(selectedImage,.07,g.colors.gold);
        line(g,[selectedSource,selectedImage],g.colors.gold,'selected_circle_map');
        record('selected_circle_map',{angle:d.angle,source:selectedSource,target:selectedImage});
        for(const [key,p] of [['upper',d.upper],['lower',d.lower]]) {
          const source=map(d.preimages[key]),target=[p[0],p[1],0];line(g,[source,target],g.colors.gold,'circle_map',{key});
          g.sphere(target,.06,g.colors.coral);record('circle_map',{key,source,target,preimage:d.preimages[key]});
        }
        g.label([3,1.5,0],d.domain==='quotient'?'Endpoints identified in quotient':'Source t: 0 to 2π');
        g.label([0,-1.6,0],'Continuous circle seam');
      }
      return {state:m.state,readout:m.readout+' '+parameters(lab.controls,m.state),note:'These diagrams show the exact authored sets, maps and sampled coordinates. Cube/graph placement of an abstract set is a layout, not a metric or physical geometry of that space. The genus scene uses the actual closed oriented triangulation and exact affine deformation, with the figure-eight on a separate reference sheet. Open covers and the sine limit need the full quantified proof in the ledger; a finite display is not that proof. All seven station states are shared with the activity; camera changes only the view.',legend:legend(g),topology:{state:m.state,active:d,primitives}};
    }
  };
  const relativity = {
    title:'Calibrated events and relativistic worldlines',requires:'PrimerPhysicsRelativityLab',linkedStateKey:'phys.4.relativity',
    initialFactory:()=>({...window.PrimerPhysicsRelativityLab.initial}),normalize:raw=>window.PrimerPhysicsRelativityLab.normalize(raw),
    controlsFactory:()=>[
      {key:'mode',label:'Relativity station',options:window.PrimerPhysicsRelativityLab.stations.map(([value,label])=>({value,label}))},
      ...window.PrimerPhysicsRelativityLab.choices.map(c=>({...c,options:c.options.map(([value,label])=>({value,label})),visibleWhen:{mode:c.modes,...(c.key==='clockCorrection'?{gravitySystem:['gps']}:{})}})),
      ...window.PrimerPhysicsRelativityLab.controls.map(c=>({...c,numericInput:true,preserveExact:true,visibleWhen:{mode:c.modes,...(c.key==='heightM'?{gravitySystem:['tower']}:c.key==='orbitAltitudeKm'?{gravitySystem:['gps']}:{})}}))],
    build(s,g) {
      const lab=window.PrimerPhysicsRelativityLab,m=lab.build(s),panels=[];
      const palette=[g.colors.blue,g.colors.teal,g.colors.coral,g.colors.gold,g.colors.plum];
      m.panels.forEach((panel,index)=>{
        const curves=panel.curves||[],markers=panel.markers||[],all=curves.flatMap(c=>c.points).concat(markers);
        const maxX=Math.max(1e-12,...all.map(p=>Math.abs(p.x))),maxY=Math.max(1e-12,...all.map(p=>Math.abs(p.y)));
        const xScale=panel.equalScale?Math.max(maxX,maxY):maxX,yScale=panel.equalScale?xScale:maxY,z=-4*index;
        const project=p=>[2*p.x/xScale,2*p.y/yScale,z];
        curves.forEach((c,j)=>line(g,c.points.map(project),palette[j%palette.length],'calibrated_curve',{key:c.key,panel:index}));
        markers.forEach(p=>g.sphere(project(p),.045,g.colors.gold,{fidelity_kind:'calibrated_marker',key:p.key,panel:index}));
        const first=curves[0],unit=(text)=>/\(([^)]+)\)/.exec(text||'')?.[1]||text||'value';
        const gain=n=>Number(n.toPrecision(3)).toString();
        axes(g,[0,0,z],[[2.4,0,z],[0,2.4,z]],
          ['X / '+unit(first?.xUnit)+' ×'+gain(2/xScale),'Y / '+unit(first?.yUnit)+' ×'+gain(2/yScale)]);
        g.label([0,-2.7,z],'Chart '+(index+1));panels.push({index,z,xScale,yScale,equalScale:Boolean(panel.equalScale),curves,markers});
      });
      let circular=null;
      if(s.mode==='sagnac') {
        const d=m.current,z=-4*m.panels.length,ctScale=Math.max(...Object.values(d.worldlines).flatMap(ps=>ps.map(p=>p.ctM)),1e-12);
        const project=p=>[2*p.xM/d.R,2*p.ctM/ctScale,z-2*p.yM/d.R];
        for(const [j,[key,ps]] of Object.entries(d.worldlines).entries())line(g,ps.map(project),palette[j],'circular_worldline',{key});
        axes(g,[0,0,z],[[2,0,z],[0,2,z],[0,0,z-2]],['x/R; gain 2','ct (m); gain '+fmt(2/ctScale),'y/R; gain −2']);
        g.label([0,-.8,z],'Spatial x,y; temporal ct');
        circular={ctScale,R:d.R,worldlines:d.worldlines};
      }
      const calibration=panels.map(p=>{
        const c=p.curves[0];return 'Chart '+(p.index+1)+': '+m.panels[p.index].title+'. Source X: '+c?.xUnit+', gain '+(2/p.xScale).toPrecision(16)+'. Source Y: '+c?.yUnit+', gain '+(2/p.yScale).toPrecision(16)+'.';
      }).join(' ');
      return {state:m.state,readout:m.readout+' '+parameters([...lab.controls,...lab.choices],m.state)+' '+calibration,note:m.note+' The 3D scene embeds calibrated mathematical charts on separate planes; their depth offsets are not physical distances. Listed gains and units recover the original values. Spacetime panels preserve equal x/ct scaling before camera projection. Camera rotation is a Euclidean view change, not a Lorentz transformation. The circular Sagnac view has two spatial directions plus a separately scaled temporal ordinate. All eight station states are shared with the activity.',legend:legend(g),relativity:{state:m.state,current:m.current,panels,circular}};
    }
  };
  const api=Object.freeze({topology,relativity});
  if(typeof window!=='undefined')window.PrimerFidelitySpatialFamilies=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
}());
