"""Recover the exact reader before the scoped source-study navigation."""
import hashlib
import json
from pathlib import Path
from tools.colonvessels_compatibility import _restore
from tools.liver_regions_compatibility import before_liver_regions_bytes
from tools.colonvessels_compatibility import before_colonvessels_bytes, before_vessel_navigation_bytes

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

DELIVERY_ROUTE = b"""@app.api_route("/app/anatomy/cptac-endometrial/{asset}", methods=["GET", "HEAD"], include_in_schema=False)
async def endometrial_source_delivery(asset: str, request: Request):
    directory = os.path.join(WEB_DIR, "anatomy", "cptac-endometrial")
    with open(os.path.join(directory, "source.json"), encoding="utf-8") as source:
        manifest = json.load(source)
    chunks = {chunk["file"] for sequence in manifest["sequences"].values() for chunk in sequence["chunks"]}
    if asset not in chunks | {"index.html", "viewer.js", "viewer.css", "source.json"}:
        return JSONResponse({"detail": "Unknown endometrial source asset"}, status_code=404)
    if asset in chunks and os.environ.get("VERCEL"):
        return RedirectResponse("/source-media/anatomy/cptac-endometrial/" + asset, status_code=307)
    return await app.state.source_static.get_response("anatomy/cptac-endometrial/" + asset, request.scope)


"""
DELIVERY_PINS = {'primer/server.py': {'before': '7d68a1a1f7f3da93cd3c70b317ab6bbf6cfc69464af472abd0f8a9fb2286a4e0',
                      'after': '0ae1df51fc541314e59222412536d8fd6abe4772c05546904c4198383a508049'},
 'vercel.json': {'before': '5ba129f70855e223d20c25292d54f82d8d43c4934539fbec92d9783260ac50e6',
                 'after': '79828720cf5a1eb11b9a7905ffd1a1c9dc31c8756cd8aad33c1af8cd4f0bf33d'}}

def before_endometrial_delivery_bytes(path, raw):
    record = DELIVERY_PINS.get(str(path))
    if record is None or hashlib.sha256(raw).hexdigest() != record["after"]:
        return raw
    if str(path) == "primer/server.py":
        restored = raw.replace(DELIVERY_ROUTE, b"", 1)
        restored = restored.replace(b'@app.api_route("/app/reference-media/radiology-open/{asset:path}",', b'@app.api_route("/app/reference-media/radiology-open/{asset}",', 1)
        restored = restored.replace(b'        target = "/source-media/reference-media/radiology-open/" + quote(asset, safe="/")', b'        target = "/source-media/reference-media/radiology-open/" + quote(asset, safe="")', 1)
    else:
        config = json.loads(raw)
        pattern = "web/anatomy/cptac-endometrial/*.gz"
        config["builds"].remove({"src": pattern, "use": "@vercel/static"})
        excludes = config["builds"][0]["config"]["excludeFiles"]
        config["builds"][0]["config"]["excludeFiles"] = excludes.replace("," + pattern + "}", "}")
        restored = (json.dumps(config, indent=2) + "\n").encode()
    if hashlib.sha256(restored).hexdigest() != record["before"]:
        raise ValueError("Endometrial source delivery changed unrelated bytes")
    return restored

def before_combined_source_release_bytes(path, raw):
    if str(path) == 'web/app.js' and hashlib.sha256(raw).hexdigest() == '05befa3f6b6d865f5dd6743a00825a2e02b821fec5656ef8c601a170d0769cb8':
        raw = raw.replace(b"  if (n.id === 'phys.5.condensed') page.append(el('a', { class: 'btn ghost', href: '/app/physics/ising/index.html' },\n    'Explore spin order and temperature'));\n", b'', 1)
        if hashlib.sha256(raw).hexdigest() != 'f4c23a904f8e527c6a292fb56d8241bece656f19908b1f2d7e7d4d5f6743c6ea':
            raise ValueError('Ising link changed unrelated reader bytes')
    if str(path) == 'web/app.js':
        raw = _restore(path, raw, Path(__file__).resolve().parents[1] / 'docs/hepatic-vessel-navigation/runtime-inverse.json', '41b11d4a5301b0f6120e1ae95b2c2b992e617b499cf52b29a8442b9cbe1744ad')
    if str(path) == 'web/app.js' and hashlib.sha256(raw).hexdigest() == '12a7c5b6d8a8a48728be5ab918574ee89f9bf53671ca57b8b6355ba4cdc9b15e':
        raw = raw.replace(b"  if (n.id === 'lang.4.linguistics') page.append(el('a', { class: 'btn ghost', href: '/app/language/quantifier-scope/index.html' },\n    'Explore every child and a tree: two scope orders'));\n", b'', 1)
        if hashlib.sha256(raw).hexdigest() != '2fa2dbf4e88e2179d7811cea6d1f1852653bd12c3a753135b057cac4986e3656':
            raise ValueError('Quantifier scope link changed unrelated reader bytes')
    return before_liver_regions_bytes(path, raw)


def before_source_studies_bytes(path, raw):
    raw = before_combined_source_release_bytes(path, raw)
    from tools.fast_report_templates_compatibility import before_fast_templates_bytes
    raw = before_fast_templates_bytes(path, raw)
    if str(path) == 'web/app.js' and hashlib.sha256(raw).hexdigest() == '1bcc58db62c46a558d7e1c691e1b9db44b09cd92bea386c2bf1b8b338d6d113b':
        raw = raw.replace(b"  if (n.id === 'phys.3.nuclear') page.append(el('a', { class: 'btn ghost', href: '/app/physics/nuclear-balance/index.html' },\n    'Balance nucleons and charge in nuclear reactions'));\n", b'', 1)
        if hashlib.sha256(raw).hexdigest() != 'd278fa8be990e8bf83ce8dbaa3d1e2fcf2ac0b87d8ffe5b1bd0d38ed5b0288f9':
            raise ValueError('Nuclear study link changed unrelated reader bytes')
    raw = before_vessel_navigation_bytes(path, raw)
    if str(path) == 'web/app.js' and hashlib.sha256(raw).hexdigest() == 'b8bfd780d07072654d06081e7728219619824dfb33ad58289960d9c5e8cf194e':
        raw = raw.replace(b"  if (n.id === 'math.3.probability') page.append(el('a', { class: 'btn ghost', href: '/app/math/marble-draws/index.html' },\n    'Explore replacement and conditional probability'));\n", b'', 1)
        if hashlib.sha256(raw).hexdigest() != '0a1e531b708254ae4700e7cf5fb5eea728f9cc8fc346b407c2a737f4f226499d':
            raise ValueError('Probability study link changed unrelated reader bytes')
    if str(path) == 'web/app.js' and hashlib.sha256(raw).hexdigest() == '0a1e531b708254ae4700e7cf5fb5eea728f9cc8fc346b407c2a737f4f226499d':
        raw = raw.replace(b"  if (n.id === 'lang.3.rhetoric') page.append(el('a', { class: 'btn ghost', href: '/app/language/argument-repair/index.html' },\n    'Inspect evidence and repair an argument'));\n", b'', 1)
        if hashlib.sha256(raw).hexdigest() != 'fe5e3f2d9ae2721ea09f3f25cdee65b058525bfb5a7b2eac16d14866c697058f':
            raise ValueError('Rhetoric study link changed unrelated reader bytes')
    raw = before_colonvessels_bytes(path, raw)
    raw = before_endometrial_delivery_bytes(path, raw)
    if str(path) != "web/app.js" or hashlib.sha256(raw).hexdigest() != "877916899eeaffb7acc23f19517304b3f20b0ed99fb9650b9bcd25a418a13c5a":
        return raw
    restored = raw.replace(MENU, b"", 1)
    restored = restored.replace(CALL, DESK, 1).replace(CALL, LESSON, 1)
    if hashlib.sha256(restored).hexdigest() != "6b81721dd7418583d432c5a225847399425492bd3cea07c374a6314cd95eb30c":
        raise ValueError("Source-study navigation changed unrelated reader bytes")
    return restored
