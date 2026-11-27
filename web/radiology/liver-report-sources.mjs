/* Teaching views attached to the anatomical rows of the three CT liver reports. */
const exams = new Set(['ct.liver-mass', 'ct.liver-lirads', 'ct.liver-lirads-calculated']);
const anatomy = '/app/anatomy/';
const segments = {
  'segment-i': [1, 44], 'segment-ii': [2, 52], 'segment-iii': [3, 49],
  'segment-iva': [4, 52], 'segment-ivb': [4, 52], 'segment-v': [5, 48],
  'segment-vi': [6, 48], 'segment-vii': [7, 49], 'segment-viii': [8, 50]
};
const torsoLabels = {
  'liver-background': ['liver', 'liver', 'Liver'],
  'spleen': ['gallbladder-pancreas-and-spleen', 'spleen', 'Spleen'],
  'ivc': ['heart-and-great-vessels', 'inferior_vena_cava', 'Inferior vena cava'],
  'gallbladder-lumen': ['gallbladder-pancreas-and-spleen', 'gallbladder', 'Gallbladder'],
  'gallbladder-wall': ['gallbladder-pancreas-and-spleen', 'gallbladder', 'Gallbladder'],
  'pericholecystic': ['gallbladder-pancreas-and-spleen', 'gallbladder', 'Gallbladder']
};
const vesselSystems = {
  'main-portal-vein': 'portal', 'right-portal-vein': 'portal', 'left-portal-vein': 'portal',
  'right-hepatic-vein': 'hepatic', 'middle-hepatic-vein': 'hepatic', 'left-hepatic-vein': 'hepatic'
};
const ducts = {
  'common-bile-duct': ['common-bile', 'Common bile duct below the cystic duct'],
  'right-intrahepatic-ducts': ['right-tree', 'Right hepatic duct and labelled tributaries'],
  'left-intrahepatic-ducts': ['left-tree', 'Left hepatic duct and labelled tributaries']
};
function study(file, query, anchor, label) {
  return {label, href:anatomy + file + '?' + new URLSearchParams(query) + (anchor ? '#' + anchor : '')};
}
export function sourcesFor(exam, key) {
  if (!exams.has(exam)) return null;
  if (Object.hasOwn(segments, key)) {
    const [region, slice] = segments[key], params = {from:exam, region, slice};
    const segment = key === 'segment-iva' ? '4a' : key === 'segment-ivb' ? '4b' : String(region);
    const ct = {exam, segment, plane:'ij', focus:'label'};
    return {
      note: region === 4 ? 'MedSeg labels IVa and IVb individually on CT. The separate MRI labels segment IV as one region.'
        : 'Compare the annotated region in two different people. The CT has 5 mm section spacing.',
      links: [
        study('medseg-liver-001/index.html', {...ct, display:'raw'}, 'ct', 'Unmarked CT'),
        study('medseg-liver-001/index.html', {...ct, display:'map'}, 'map', 'CT segment map'),
        study('medseg-liver-001/index.html', {...ct, display:'outline'}, 'surface', 'CT-derived 3D region'),
        study('liver-regions-mri/index.html', {...params, representation:'schematic'}, 'image-region', 'MRI segment map'),
        study('liver-regions-mri/index.html', {...params, representation:'model'}, 'surface', 'MRI-derived 3D region')
      ]
    };
  }
  if (Object.hasOwn(torsoLabels, key)) {
    const [row, label, name] = torsoLabels[key], params = {exam:'ct.chest-abdomen-pelvis', row, label, from:exam};
    return {
      note: label === 'gallbladder' ? 'The s0028 mask outlines the organ. Lumen contents, wall and surrounding tissue require inspection on CT.'
        : 'The CT and surface show the same labelled structure in case s0028.',
      links: [
        study('ct-torso-s0028/index.html', {...params, representation:'clinical_image'}, 'ct-section', name + ' on unmarked CT'),
        study('ct-torso-s0028/index.html', {...params, representation:'model'}, 'source-surface', name + ' in 3D')
      ]
    };
  }
  if (Object.hasOwn(vesselSystems, key)) {
    const system = vesselSystems[key], name = system === 'portal' ? 'Portal venous tree' : 'Hepatic venous tree';
    return {note:'HVA-CT case 318 labels the venous system as a whole. Individual branches share that label.',
      links:[study('hva-ct-318/index.html', {from:exam, system}, 'image-region', name + ' on CT'),
             study('hva-ct-318/index.html', {from:exam, system}, 'surface', name + ' in 3D')]};
  }
  if (Object.hasOwn(ducts, key)) {
    const [group, name] = ducts[key];
    return {note:'This BodyParts3D anatomical atlas shows the selected source geometry.',
      links:[study('bp3d-biliary-4.3/index.html', {from:exam, group}, 'surface', name + ' in 3D')]};
  }
  if (key === 'hepatic-observation') {
    return {note:'These separately acquired cases illustrate lesion location and extent. Neither supplies a complete multiphase CT assessment.',
      links:[{label:'Annotated lesion on portal venous CT and in 3D', href:anatomy+'msd-liver-lesion/index.html'},
             {label:'Tumour crossing segments VI and VII on MRI', href:anatomy+'phlf-center2-24/index.html'}]};
  }
  return null;
}

export function showSources(container, exam, section) {
  const entry = sourcesFor(exam, section);
  if (!entry) return;
  const note = document.createElement('span');
  note.textContent = entry.note;
  container.append(note);
  for (const source of entry.links) {
    const link = document.createElement('a');
    link.textContent = source.label;
    link.href = source.href;
    link.target = '_blank';
    link.rel = 'noopener';
    container.append(' · ', link);
  }
  container.hidden = false;
}
