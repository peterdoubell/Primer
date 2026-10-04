"""Tree-specific representation identities and upstream rights must remain explicit."""
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import select,alternative_representations

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/bodyparts-pancreatic-upstream-review'


def html(table):
    return '<table>'+''.join('<tr>'+''.join('<td>'+v+'</td>' for v in row)+'</tr>' for row in [table['headers']]+table['selected_element_rows'])+'</table>'


def test_selected_source_version_and_distinct_tree_aliases_are_reconciled():
    manifest=(REVIEW/'selected-version-manifest.txt').read_text()
    tables=json.loads((REVIEW/'selected-original-mapping-rows.json').read_text())
    groups,isa=select(manifest,html(tables['obj2FMA-4.3.html']))
    partof=alternative_representations(html(tables['obj2FMA-partof-4.3.html']),isa)
    receipt=json.loads((REVIEW/'acquisition.json').read_text())
    assert groups==receipt['source_groups'] and len(isa)==25
    assert len(receipt['objects'])==25 and sum(r['faces'] for r in receipt['objects'])==26488
    assert sum(not r['returned_representation_matches_is_a'] for r in receipt['objects'])==10
    for r in receipt['objects']:
        candidates=[isa[r['id']]]+partof[r['id']]
        assert any(c['representation_id']==r['representation_id'] and c['source_fma']==r['source_fma'] for c in candidates)
        header=r['original_obj_header']
        assert header['Compatibility version']=='4.3' and header['File ID']==r['id']
        assert header['Representation ID']==r['representation_id'] and header['Concept ID']==r['source_fma']
    duct=next(r for r in receipt['objects'] if r['id']=='FJ1896')
    assert duct['source_label']=='Pancreatic duct tree' and duct['representation_id']=='BP23800'
    assert duct['requested_is_a_representation_id']=='BP20579' and duct['returned_representation_matches_partof'] is True
    assert receipt['archive_crc_verified'] is True
    assert receipt['upstream_default_license']=='CC BY-SA 2.1 Japan'
    assert receipt['archive_40_cc_by_40_grant_reused_for_upstream_meshes'] is False
    assert receipt['polygon_reduction_rate_independently_verified'] is False
    assert receipt['clinical_approval'] is False and receipt['runtime_promoted'] is False


def test_wrong_version_and_missing_report_target_cannot_substitute_for_selected_source():
    manifest=(REVIEW/'selected-version-manifest.txt').read_text()
    table=json.loads((REVIEW/'selected-original-mapping-rows.json').read_text())['obj2FMA-4.3.html']
    with pytest.raises(ValueError,match='version'):
        select(manifest.replace('# Data Version\t4.3','# Data Version\t4.0'),html(table))
    missing='\n'.join(line for line in manifest.splitlines() if not line.startswith('FMA63103\t'))
    with pytest.raises(ValueError,match='absent'):
        select(missing,html(table))
    table['selected_element_rows'].append(table['selected_element_rows'][0])
    with pytest.raises(ValueError,match='Ambiguous'):
        select(manifest,html(table))
