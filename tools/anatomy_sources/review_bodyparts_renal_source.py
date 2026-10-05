#!/usr/bin/env python3
"""Review every original renal object and preserve source-specific fine-structure gaps."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def selection_holds(root, output):
    from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import Rows
    queries = ['renal cortex','renal medulla','renal pelvis','renal calyx','renal calyces','renal pyramid','renal capsule','capsule of kidney']
    found = {q: [] for q in queries}; metadata = {}
    for name in ['obj2FMA-4.3.html','obj2FMA-partof-4.3.html']:
        raw = (root / name).read_bytes(); parser = Rows(); parser.feed(raw.decode())
        metadata[name] = {'sha256':hashlib.sha256(raw).hexdigest(),'parsed_rows':len(parser.rows)}
        for row in parser.rows[1:]:
            if len(row) < 8:
                continue
            labels = ' '.join(row[4:6]).lower()
            for query in queries:
                if query in labels:
                    found[query].append({'element_id':row[1],'source_fma':row[3],'source_label':row[4],'source_synonyms':row[5],'metadata_file':name})
    (output / 'source-selection-holds.json').write_text(json.dumps({'selected_source_version':'4.3','metadata':metadata,
        'separately_named_target_queries':found,'missing_fine_regions_supplied_by_parent_labels':False,
        'tumour_case_supplies_normal_or_trauma_anatomy':False,'clinical_approval':False,'runtime_promoted':False,
        'limitations':['These label/synonym searches concern the selected two source maps only, not every dataset or all tissue potentially present in a mesh.',
                       'Whole kidney, vascular and ureter labels cannot independently supply separately resolved cortex, medulla, calyces, pelvis, capsule, lumen/wall or injury examples.',
                       'Renal tumour annotations and source phases are not substituted for normal or traumatic renal anatomy.']},indent=2)+'\n')


def review(root, output):
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import review as geometry
    from tools.anatomy_sources.review_bodyparts_source_boundaries import review as boundaries
    from tools.anatomy_sources.audit_bodyparts_bowel_contacts import audit as self_contacts
    from tools.anatomy_sources.audit_bodyparts_renal_interfaces import audit as interfaces
    from tools.anatomy_sources.render_bodyparts_bowel_review import render
    from tools.anatomy_sources.review_bodyparts_renal_coincident_faces import review as coincident
    from tools.anatomy_sources.review_bodyparts_bowel_proximity import review as proximity
    from tools.anatomy_sources.review_bodyparts_mesenteric_correspondence import review as correspondence
    from tools.anatomy_sources.review_bodyparts_renal_pairs import review as pairs
    from tools.anatomy_sources.render_bodyparts_renal_interfaces import render as contact_views
    from tools.anatomy_sources.render_bodyparts_renal_coincident_faces import render as coincident_views
    output.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(root/'upstream-acquisition.json',output/'acquisition.json')
    geometry(root,output,expected_object_count=31)
    boundaries(root,output)
    selection_holds(root,output)
    self_contacts(root,output,expected_object_count=31)
    coincident(root,output)
    interfaces(root,output)
    proximity(root,output)
    correspondence(root,output)
    pairs(output)
    render(root,output)
    contact_views(root,output)
    coincident_views(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); review(args.source_root,args.output)
