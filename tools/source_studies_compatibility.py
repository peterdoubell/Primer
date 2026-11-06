"""Recover the exact reader before the scoped source-study navigation."""
import hashlib

MENU = b"""function renderUterineSourceStudies(nodeId) {
  const studies = [
    { modules: ['ra.mri-endometrial-cancer'],
      title: 'Inspect an endometrial tumour on original MRI',
      href: '/app/anatomy/cptac-endometrial/index.html',
      context: 'One tumour case with post-contrast MRI, T2 MRI and original lesion contours. The two acquisitions are navigated independently.' },
    { modules: ['ra.mri-cervical-cancer'],
      title: 'Inspect original cervical cancer MRI contours',
      href: '/app/anatomy/ccth-a01/index.html',
      context: 'One cervical cancer case with 30 acquired T2 sections and the original contour stack.' },
    { modules: ['ra.mri-cervical-cancer'],
      title: 'Compare cervical cancer staging images across modalities',
      href: '/app/reference-studies/cervical-staging-2024/index.html',
      context: 'Selected publication figures for cervical stroma, parametria, vagina, adjacent organs and lymph nodes.' },
    { modules: ['ra.mri-cervical-cancer'],
      title: 'Explore the cervical canal and stroma on pregnancy MRI',
      href: '/app/anatomy/kcl-cervix/055t/index.html',
      context: 'Two pregnancy population atlases with three cervical layers. These references describe pregnancy anatomy.' },
    { modules: [],
      title: 'Study a uterine myoma MRI case with wall and cavity annotations',
      href: '/app/anatomy/umd-141/index.html',
      context: 'One myoma case with the original MRI and sampled wall, cavity, myoma and cyst labels.' },
    { modules: ['ra.mullerian-anomalies'],
      title: 'Compare uterine cavity and external contour on source images',
      href: '/app/reference-studies/mullerian-2025/index.html',
      context: 'Published anomaly examples and a separate 3D pelvic reference.' },
  ];
  const shown = studies.filter(study => nodeId === 'rad.5.uterine-mr' || study.modules.includes(nodeId));
  if (!shown.length) return null;
  return el('section', { class: 'card', 'aria-label': 'Original MRI and anatomy studies' },
    el('h2', {}, 'Original MRI and anatomy studies'),
    el('ul', {}, ...shown.map(study => el('li', {},
      el('a', { href: study.href }, study.title),
      el('p', { class: 'muted' }, study.context)))));
}

"""
CALL = b"""  const sourceStudies = renderUterineSourceStudies(n.id);
  if (sourceStudies) page.append(sourceStudies);
"""
DESK = b"""  if (n.id === 'ra.mri-endometrial-cancer') page.append(el('div', { class: 'model-button-row', style: 'margin:1rem 0' },
    el('a', { class: 'btn ghost', href: '/app/anatomy/cptac-endometrial/index.html' },
      'Inspect an endometrial tumour on original MRI')));
"""
LESSON = b"""  if (n.id === 'rad.5.uterine-mr') page.append(el('div', { class: 'model-button-row', style: 'margin:1rem 0' },
    el('a', { class: 'btn ghost', href: '/app/anatomy/cptac-endometrial/index.html' },
      'Inspect an endometrial tumour on original MRI'),
    el('a', { class: 'btn ghost', href: '/app/reference-studies/mullerian-2025/index.html' },
      'Compare uterine cavity and external contour on source images')));
"""

def before_source_studies_bytes(path, raw):
    if str(path) != "web/app.js" or hashlib.sha256(raw).hexdigest() != "877916899eeaffb7acc23f19517304b3f20b0ed99fb9650b9bcd25a418a13c5a":
        return raw
    restored = raw.replace(MENU, b"", 1)
    restored = restored.replace(CALL, DESK, 1).replace(CALL, LESSON, 1)
    if hashlib.sha256(restored).hexdigest() != "6b81721dd7418583d432c5a225847399425492bd3cea07c374a6314cd95eb30c":
        raise ValueError("Source-study navigation changed unrelated reader bytes")
    return restored
