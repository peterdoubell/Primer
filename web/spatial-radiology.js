/* Radiology geometry companions. Original schematic geometry, not patient scans.
 * Measurement source: ACC/AHA 2022 aortic guideline, doi:10.1161/CIR.0000000000001106.
 * Alignment source: AO Surgery Reference, Assessment of reduction quality.
 */
(function () {
  'use strict';
  const circle = fn => Array.from({ length: 65 }, (_, i) => fn(i * Math.PI / 32));
  const legend = (label, color) => ({ label, color });
  window.PrimerSpatial.register({
    'rad.3.ct-image': {
      initial: { plane: 'axial', position: 0 },
      controls: [
        { key: 'plane', label: 'Section plane', options: [
          { value: 'axial', label: 'Axial' }, { value: 'coronal', label: 'Coronal' }, { value: 'sagittal', label: 'Sagittal' }] },
        { key: 'position', label: 'Section position', min: -1, max: 1, step: .1, unit: '' },
      ],
      build(s, g) {
        const c = g.colors, axis = { sagittal: 0, axial: 1, coronal: 2 }[s.plane];
        const radius = .65, p = s.position;
        g.box([0,0,0], [2,2,2], c.blue, { opacity: .06 });
        g.mesh((u,v) => { const a=u*Math.PI, b=v*2*Math.PI; return [radius*Math.sin(a)*Math.cos(b),radius*Math.cos(a),radius*Math.sin(a)*Math.sin(b)]; }, 16, 24, c.teal, { opacity: .22 });
        const point = (a,b) => { const xyz = [0,0,0]; xyz[axis]=p; xyz[(axis+1)%3]=a; xyz[(axis+2)%3]=b; return xyz; };
        g.polygon([point(-1,-1),point(1,-1),point(1,1),point(-1,1)], c.gold, { opacity: .22 });
        const r = Math.sqrt(Math.max(0, radius*radius-p*p));
        if (r > 0) g.line(circle(t => point(r*Math.cos(t),r*Math.sin(t))), c.coral, { width: 4 });
        g.label([0,1.25,0], 'Superior'); g.label([1.25,0,0], 'Patient left'); g.label([0,0,1.25], 'Anterior');
        return { readout: `${s.plane[0].toUpperCase()+s.plane.slice(1)} section at ${p.toFixed(1)}. Sphere intersection diameter: ${(2*r).toFixed(2)} schematic units. ${r ? 'Moving away from the centre makes the section smaller.' : 'This plane misses the sphere.'}`,
          legend: [legend('Reference volume',c.blue),legend('Spherical target',c.teal),legend('Section plane',c.gold),legend('Intersection',c.coral)],
          note: 'An ideal sphere inside a reference volume, not anatomy or a CT reconstruction. The intersection is calculated exactly. Rotate the volume to connect a flat section with its 3D position; this perspective view is not the conventional radiological display orientation.' };
      },
    },
    'rad.5.tavi-ct': {
      initial: { tilt: 0 },
      controls: [{ key: 'tilt', label: 'Plane tilt from perpendicular', min: 0, max: 60, step: 5, unit: '°' }],
      build(s,g) {
        const c=g.colors, a=s.tilt*Math.PI/180, r=.55;
        g.mesh((u,v) => [r*Math.cos(u*2*Math.PI),-1.2+2.4*v,r*Math.sin(u*2*Math.PI)],32,8,c.blue,{opacity:.15});
        g.line([[0,-1.4,0],[0,1.4,0]],c.ink,{width:2});
        const point=(x,z)=>[x,x*Math.tan(a),z];
        g.polygon([point(-.7,-.7),point(.7,-.7),point(.7,.7),point(-.7,.7)],c.gold,{opacity:.18});
        g.line(circle(t=>point(r*Math.cos(t),r*Math.sin(t))),c.coral,{width:3});
        g.line([point(-r,0),point(r,0)],c.coral,{width:4});
        g.line([[0,0,-r],[0,0,r]],c.teal,{width:4});
        g.label([0,1.55,0],'Vessel centreline');
        return { readout: `Tilt ${s.tilt}°. True lumen diameter: 10.0 mm. Oblique long axis: ${(10/Math.cos(a)).toFixed(1)} mm (${(100*(1/Math.cos(a)-1)).toFixed(0)}% larger). Short axis stays 10.0 mm.`,
          legend:[legend('Ideal circular lumen',c.blue),legend('Measurement plane',c.gold),legend('Oblique long axis',c.coral),legend('True diameter',c.teal)],
          note:'A straight circular access-vessel lumen illustrates obliquity alone: long axis = diameter / cos(tilt). Set tilt to zero to obtain an orthogonal section. Real access vessels may be irregular, calcified and tortuous; this is not an aortic-annulus model or a device-sizing calculator.' };
      },
    },
    'rad.3.fracture-description': {
      initial: { translation: .4, angle: 20, direction: 'lateral' },
      controls:[
        { key:'translation',label:'Distal translation / shaft width',min:0,max:1,step:.1,unit:'' },
        { key:'angle',label:'Distal angulation',min:0,max:40,step:5,unit:'°' },
        { key:'direction',label:'Displacement direction',options:[{value:'lateral',label:'Lateral'},{value:'anterior',label:'Anterior'}] },
      ],
      build(s,g) {
        const c=g.colors, a=s.angle*Math.PI/180, width=.4, shift=s.translation*width;
        const transform=(x,y,z)=>{const p=[x*Math.cos(a)+y*Math.sin(a)+shift,-.08+x*Math.sin(a)-y*Math.cos(a),z];return s.direction==='anterior'?[p[2],p[1],p[0]]:p;};
        g.box([0,.68,0],[width,1.2,width],c.blue);
        const corners=[[-.2,0,-.2],[.2,0,-.2],[.2,1.2,-.2],[-.2,1.2,-.2],[-.2,0,.2],[.2,0,.2],[.2,1.2,.2],[-.2,1.2,.2]].map(p=>transform(...p));
        [[0,1,2,3],[4,7,6,5],[0,4,5,1],[3,2,6,7],[0,3,7,4],[1,5,6,2]].forEach(face=>g.polygon(face.map(i=>corners[i]),c.coral));
        g.line([[0,1.4,0],[0,-1.4,0]],c.ink,{width:1});
        g.label([-.6,1,0],'Proximal'); g.label(transform(.5,1,0),'Distal');
        return { readout:`Distal fragment: ${(s.translation*100).toFixed(0)}% shaft-width translation ${s.direction}ly; ${s.angle}° angulation toward the ${s.direction} side. Rotate a quarter turn to see how a single projection can hide displacement.`,
          legend:[legend('Proximal reference',c.blue),legend('Distal fragment',c.coral),legend('Original shaft axis',c.ink)],
          note:'Square rods isolate translation and angulation; they are not realistic bone anatomy. The small gap separates fragments visually. Translation is measured at the distal fracture-face centre. No shortening, axial rotation, healing prediction or treatment threshold is modelled.' };
      },
    },
  });
}());
