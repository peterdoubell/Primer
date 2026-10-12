"""Bounded independent viewport delta; the scientific review remains historical."""
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from tools.number_theory_runtime_compatibility import math_product_bytes, math_test_bytes

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("semantic_oracle", ROOT /
    "docs/number-theory-viewport-delta-independent-review-20261012/test_number_theory_diagrams.before.py")
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)

# Reuse the already reviewed minimal DOM, replacing fixed scroll heights with the
# actual emitted SVG height. This exercises callbacks, not a source-text pattern.
DOM = oracle.DOM.split("const frames=states.map")[0].replace(
    "this.scrollHeight=2000;this.scrollWidth=1050;",
    "Object.defineProperty(this,'scrollHeight',{get:()=>{const sv=this.querySelector('[data-nt-semantic-svg]');"
    "return sv&&sv.attributes.viewBox?Number(sv.attributes.viewBox.split(' ')[3]):2000;}});this.scrollWidth=1050;"
)

AUDIT = r"""
window.PrimerLessonStateBus={join:realBus.join,publish:realBus.publish};
Element.prototype.focus=function(){document.activeElement=this;};
const results=[];
for(const width of [390,1000]){
 const r=api.render(item),vp=r.querySelector('.nt-semantic-viewport');vp.clientWidth=width;
 r.setModelState({mode:'powers',base:'3',exponent:'100',powerModulus:'256',diagramPage:17},false,true);flush();
 const peer=api.renderSpatial({props,title:'Viewport peer'},{state:r.getDiagramState()});
 realBus.publish(lab.key,new Element('section'),r.getDiagramState());flush();
 const graphKey=()=>{const v=r.getDiagramData();return JSON.stringify({page:v.page,nodes:v.nodes,edges:v.edges});};
 const offset=()=>[vp.scrollLeft,vp.scrollTop];
 function frame(){const v=r.getDiagramData();return {page:v.page,state:r.getDiagramState(),offset:offset(),
  width:vp.clientWidth,height:vp.clientHeight,scrollHeight:vp.scrollHeight,nodes:v.nodes.map(n=>{
   const g=r.querySelectorAll('[data-nt-semantic-node]').find(g=>g.attributes['data-nt-semantic-node']===n.id),
    a=g.children[0].attributes,box=g.children[0].tagName==='circle'?
    [Number(a.cx)-Number(a.r),Number(a.cy)-Number(a.r),Number(a.cx)+Number(a.r),Number(a.cy)+Number(a.r)]:
    [Number(a.x),Number(a.y),Number(a.x)+Number(a.width),Number(a.y)+Number(a.height)];
   return {id:n.id,context:n.context,group:n.group,col:n.col,box};}),groupStart:v.groupStart,groupEnd:v.groupEnd};}
 function attempt(name,action){vp.scrollTo({top:vp.scrollHeight,left:vp.scrollWidth});
  r.querySelector('[data-nt-control="base"]').focus();
  const before=frame(),key=graphKey(),focus=document.activeElement;action();flush();
  results.push({width,name,before,after:frame(),sameGraph:key===graphKey(),focusPreserved:document.activeElement===focus});}
 attempt('identical_direct_replay',()=>r.setModelState(r.getDiagramState(),false,true));
 attempt('null_update',()=>r.setModelState(null,false,true));
 attempt('unknown_update',()=>r.setModelState({alien:'changed'},false,true));
 attempt('inactive_control_update',()=>r.setModelState({a:'19'},false,true));
 attempt('invalid_native_edit',()=>{const i=r.querySelector('[data-nt-control="base"]');i.value='invalid';i.fire('keydown',{key:'Enter'});});
 attempt('identical_page_commit',()=>{const i=r.querySelector('[data-nt-diagram-page]');i.value=String(r.getDiagramData().page);i.fire('keydown',{key:'Enter'});});
 attempt('identical_peer_update',()=>realBus.publish(lab.key,new Element('section'),r.getDiagramState()));
 attempt('spatial_peer_replay',()=>{const i=peer.querySelector('[data-parameter="diagramPage"]');i.value=String(r.getDiagramData().page);i.fire('keydown',{key:'Enter'});});
 attempt('observer_redraw',()=>r.setAttribute('data-nt-state',r.getAttribute('data-nt-state')));
 attempt('native_page_change',()=>r.querySelector('[data-nt-diagram-next="-1"]').fire('click'));
 attempt('native_math_change',()=>{const i=r.querySelector('[data-nt-control="base"]');i.value='2';i.fire('keydown',{key:'Enter'});});
 attempt('spatial_peer_math_change',()=>{const i=peer.querySelector('[data-parameter="base"]');i.value='4';i.fire('keydown',{key:'Enter'});});
 attempt('spatial_peer_page_change',()=>{const i=peer.querySelector('[data-parameter="diagramPage"]');i.value='0';i.fire('keydown',{key:'Enter'});});
 attempt('peer_graph_shrink',()=>realBus.publish(lab.key,new Element('section'),{mode:'powers',base:'1',exponent:'0',powerModulus:'7',diagramPage:10000}));
 attempt('mode_change',()=>r.setModelState({mode:'division',a:'17',modulus:'5'},false,true));
 r.setModelState({mode:'powers',base:'3',exponent:'100',powerModulus:'256',diagramPage:17},false,true);flush();
 const beforeHome=graphKey(),beforeNavigationState=JSON.stringify(r.getDiagramState());vp.focus();
 vp.fire('keydown',{key:'End'});const end=frame();
 vp.fire('keydown',{key:'Home'});const home=frame();
 results.push({width,name:'home_end',end,home,graphUnchanged:graphKey()===beforeHome,
  stateUnchanged:JSON.stringify(r.getDiagramState())===beforeNavigationState,focusPreserved:document.activeElement===vp});
}
process.stdout.write(JSON.stringify(results));
"""


def visible(node, frame):
    x, y = frame["offset"]
    left, top, right, bottom = node["box"]
    return x <= left and y <= top and right <= x + frame["width"] and bottom <= y + frame["height"]


def current_sources(frame):
    nodes = [n for n in frame["nodes"] if not n["context"] and (
        frame["page"] == 0 or frame["groupStart"] <= n["group"] < frame["groupEnd"])]
    minimum_column = min(n["col"] for n in nodes)
    return [n for n in nodes if n["col"] == minimum_column]


def test_changed_graph_restores_current_view_and_identical_graph_preserves_manual_scroll():
    result = subprocess.run(["node", "-e", DOM + AUDIT], cwd=ROOT, input="[]",
                            text=True, capture_output=True, timeout=60, check=False)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    unchanged = {"identical_direct_replay", "null_update", "unknown_update", "inactive_control_update",
                 "invalid_native_edit", "identical_page_commit", "identical_peer_update", "spatial_peer_replay", "observer_redraw"}
    changed = {"native_page_change", "native_math_change", "spatial_peer_math_change",
               "spatial_peer_page_change", "peer_graph_shrink", "mode_change"}
    assert len(data) == 32
    for case in data:
        assert case["focusPreserved"], case["name"]
        if case["name"] in unchanged:
            assert case["sameGraph"], case["name"]
            assert case["before"]["offset"] == case["after"]["offset"], case["name"]
        elif case["name"] in changed:
            assert not case["sameGraph"], case["name"]
            assert any(visible(n, case["after"]) for n in current_sources(case["after"])), case["name"]
            assert case["after"]["offset"] != case["before"]["offset"], case["name"]
        else:
            assert case["name"] == "home_end" and case["graphUnchanged"] and case["stateUnchanged"]
            last = max(case["end"]["nodes"], key=lambda n: n["box"][3])
            assert visible(last, case["end"]), "End must reveal a real final card"
            assert any(visible(n, case["home"]) for n in current_sources(case["home"])), "Home must reveal the current-page source"


def test_viewport_delta_receipt_preserves_scientific_receipt_and_mathematical_source():
    review = json.loads((ROOT / "docs/number-theory-viewport-delta-independent-review-20261012.json").read_text())
    assert review["result"] == "pass_for_scoped_viewport_delta"
    assert not review["browser_reader_approval"] and not review["whole_goal_complete"]
    historical = ROOT / review["scientific_receipt"]["path"]
    assert hashlib.sha256(historical.read_bytes()).hexdigest() == review["scientific_receipt"]["sha256"]
    for key in ("baseline_diagram_source", "preserved_fixture"):
        assert hashlib.sha256((ROOT / review[key]["path"]).read_bytes()).hexdigest() == review[key]["sha256"]
    for path, digest in review["unchanged_reviewed_source_sha256"].items():
        assert hashlib.sha256(math_product_bytes(path,(ROOT / path).read_bytes())).hexdigest() == digest, path
    source = (ROOT / "web/number-theory-diagrams.js").read_text()
    math = source.split("  function render(item,hooks)")[0]
    spatial = source.split("  function renderSpatial(item,hooks)")[1]
    assert hashlib.sha256(math.encode()).hexdigest() == review["unchanged_semantic_prefix_sha256"]
    assert hashlib.sha256(spatial.encode()).hexdigest() == review["unchanged_spatial_suffix_sha256"]
    assert hashlib.sha256(source.encode()).hexdigest() == review["current_diagram_source_sha256"]
    reconstructed = source
    for replacement in review["source_delta_inverse_replacements"]:
        assert reconstructed.count(replacement["new_literal"]) == 1
        reconstructed = reconstructed.replace(replacement["new_literal"], replacement["old_literal"], 1)
    assert reconstructed.encode() == (ROOT / review["baseline_diagram_source"]["path"]).read_bytes()
    assert hashlib.sha256(math_test_bytes('tests/test_number_theory_diagram_viewport.py',Path(__file__).read_bytes())).hexdigest() == review["viewport_oracle_sha256"]
