"""Independent mathematics and emitted semantic relations, separate from the old atlas review."""
import hashlib
import itertools
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from primer.curriculum import Curriculum
from tools.number_theory_runtime_compatibility import math_product_bytes, math_test_bytes

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/number-theory-semantic-diagram-independent-review-20261012.json"
OLD_REVIEW_SHA = "3ab506f3a410552a309a40fa6d3b942bbd6f2c80ec30605887d12e2f7cd08cfa"
OLD_TEST_SHA = "9d81aca03e072c46f74851908489e6d33d33a5b70c6cb41e2b1e9f132f369cec"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js required")

BRIDGE = r"""
const fs=require('node:fs');global.window={};
const lab=require('./web/math-number-theory-lab.js');
const api=require('./web/number-theory-diagrams.js');
let spatial;
function ready(){if(spatial)return;require('./web/spatial-models.js');
 require('./web/spatial-number-theory-relations.js');require('./web/spatial-module-objects.js');
 const props={scenario:'module.math.4.numtheory',family:'number-theory-exact-traces',
  mode:'model',context:'Independent semantic audit',lesson:'Number Theory'};
 if(!window.PrimerModuleObjects.ensure({props}))throw Error('Missing semantic binding');
 spatial=window.PrimerSpatial;}
const requests=JSON.parse(fs.readFileSync(0,'utf8'));
const result=requests.map(r=>{
 if(r.kind==='meta')return {initial:lab.initial,controls:lab.controls,stations:lab.stations,PAGE_SIZE:api.PAGE_SIZE};
 if(r.kind==='historicalManifest'){
  const ctx={module:{exports:{}}};require('node:vm').runInNewContext(fs.readFileSync(
   './docs/number-theory-reader-review-20261012/historical-scoped-source/math-number-theory-lab.js','utf8'),ctx);
  return {initial:ctx.module.exports.initial,controls:ctx.module.exports.controls.map(({key,min,max})=>({key,min,max}))};
 }
 if(r.kind==='graph')return api.graph(r.state);
 if(r.kind==='stats'){const g=api.graph(r.state);return {nodes:g.nodes.length,edges:g.edges.length,
  pages:api.windowGraph(g,0).pageCount};}
 if(r.kind==='core')return lab.build(r.state).data;
 if(r.kind==='cycleBoundary'){
  const b=lab.build(r.state);return {direct:lab.cycle(r.state.base,r.state.powerModulus),
   cycle:b.data.cycle,proof:b.proof,readout:b.readout};
 }
 if(r.kind==='normalize')return api.normalize(r.state);
 if(r.kind==='pages'){
  const full=api.graph(r.state),count=api.windowGraph(full,0).pageCount;
  const indices=r.selected?[...new Set([0,Math.floor(count/2),count-1])]:Array.from({length:count},(_,i)=>i);
  return {full,windows:indices.map(i=>{const v=api.windowGraph(full,i),needed=[...new Set([-1,
   ...Array.from({length:v.groupEnd-v.groupStart},(_,j)=>v.groupStart+j),...v.nodes.map(n=>n.group)])],
   extents=Object.fromEntries(needed.filter(k=>v.extents[k]).map(k=>[k,v.extents[k]]));return {page:v.page,pageCount:v.pageCount,
   groupStart:v.groupStart,groupEnd:v.groupEnd,totalNodes:v.totalNodes,totalEdges:v.totalEdges,
   nodes:v.nodes,edges:v.edges,extents,positions:v.nodes.map(n=>[n.id,v.position(n)])};})};
 }
 if(r.kind==='geometry'||r.kind==='geometryStats'){
  ready();const b=spatial.build('module.math.4.numtheory',r.state),v=b.numberTheoryRelations.window;
  if(r.kind==='geometryStats')return {nodes:v.nodes.length,edges:v.edges.length,
   loops:v.edges.filter(e=>e.from===e.to).length};
  return {state:b.state,view:v,primitives:b.primitives,readout:b.readout,note:b.note};
 }
 throw Error('Unknown request');
});process.stdout.write(JSON.stringify(result));
"""


def node(requests):
    p = subprocess.run(["node", "-e", BRIDGE], cwd=ROOT, input=json.dumps(requests),
                       capture_output=True, text=True, timeout=180, check=False)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def prime(n):
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))


def int_value(nodes, key):
    return int(nodes[key]["values"]["value"])


def verify_graph(g):
    """Check arithmetic/logic carried by the graph, not its descriptive captions."""
    s, mode = g["state"], g["mode"]
    nodes = {n["id"]: n for n in g["nodes"]}
    assert len(nodes) == len(g["nodes"])
    assert len({e["id"] for e in g["edges"]}) == len(g["edges"])
    assert all(e["from"] in nodes and e["to"] in nodes for e in g["edges"])
    assert all(-1 <= n["group"] < len(g["groups"]) for n in g["nodes"])
    assert all(-1 <= e["group"] < len(g["groups"]) for e in g["edges"])
    tracks={};extents={}
    for i,n in enumerate(g["nodes"]):
        assert n["displayId"]=="N"+str(i+1)
        h=n["cardHeight"];offset=n["layoutOffset"]
        assert math.isfinite(h) and math.isfinite(offset) and offset>=n["row"]*90-1e-9
        assert h==14 if n["kind"]=="unit_dot" else h>=64
        tracks.setdefault((n["group"],n["col"]),[]).append((offset-h/2,offset+h/2))
        extents.setdefault(str(n["group"]),[]).extend((offset-h/2,offset+h/2))
    for boxes in tracks.values():
        ordered=sorted(boxes)
        assert all(a[1]+16<=b[0]+1e-9 for a,b in zip(ordered,ordered[1:]))
    for group,values in extents.items():
        assert g["extents"][group]=={"min":min(values),"max":max(values)}
    for n in g["nodes"]:
        if n["kind"] in ("integer", "unit_dot"):
            assert isinstance(n["values"]["value"], str)
            assert re.fullmatch(r"-?\d+", n["values"]["value"])
    edges = g["edges"]
    relation = lambda name: [e for e in edges if e["relation"] == name]
    if mode == "division":
        a, n = int(s["a"]), int(s["modulus"])
        q, r = divmod(a, n)
        assert [int_value(nodes, k) for k in ("a", "q", "m", "r", "qm")] == [a, q, n, r, q*n]
        assert q*n <= a < (q+1)*n
        counted = relation("counted_group")
        if 0 <= q <= 8 and n <= 12:
            assert len(counted) == q
            for j, e in enumerate(counted):
                assert e["values"] == {"count": str(n), "index": j, "totalGroups": str(q)}
                members = [x for x in relation("member") if x["to"] == e["from"]]
                assert len(members) == n
                assert all(int_value(nodes, x["from"]) == 1 for x in members)
            assert len(relation("remainder_member")) == r
            assert sum(int_value(nodes, e["from"]) for e in relation("remainder_member")) == r
        else:
            assert not counted and not relation("member")
    elif mode == "product":
        a, b, n = int(s["a"]), int(s["b"]), int(s["modulus"])
        assert [int_value(nodes, k) for k in ("a", "b", "ra", "rb", "P", "RP", "result")] == [a,b,a%n,b%n,a*b,(a%n)*(b%n),a*b%n]
        assert len(relation("reduce_mod")) == 4
        for e in relation("reduce_mod"):
            v = e["values"]
            assert int(v["input"]) % int(v["modulus"]) == int(v["output"])
            assert int_value(nodes, e["from"]) == int(v["input"])
            assert int_value(nodes, e["to"]) == int(v["output"])
    elif mode in ("gcd", "inverse"):
        a = int(s["gcdA"] if mode == "gcd" else s["inverseA"])
        b = int(s["gcdB"] if mode == "gcd" else s["inverseModulus"])
        gcd = math.gcd(a, b)
        w = nodes["euclidw"]["values"]
        assert a*int(w["x"])+b*int(w["y"]) == gcd == int_value(nodes, "euclidg")
        previous = (abs(a), abs(b))
        for e in relation("remainder"):
            v = e["values"]
            A, B, q, r = (int(v[k]) for k in ("dividend", "divisor", "quotient", "remainder"))
            assert (A, B) == previous and (q, r) == divmod(A, B)
            assert int_value(nodes, e["to"]) == r
            assert a*int(v["nextX"])+b*int(v["nextY"]) == r
            previous = B, r
        assert previous == (gcd, 0)
        assert len(relation("back_substitution")) == len(relation("remainder"))
        for e in relation("back_substitution"):
            v = nodes[e["from"]]["values"]
            assert int(v["a"])*int(v["x"])+int(v["b"])*int(v["y"]) == int_value(nodes, e["to"])
        if mode == "inverse":
            exists = gcd == 1
            assert nodes["condition"]["values"] == {"exists": exists, "gcd": str(gcd)}
            assert ("inverse" in nodes) == exists
            if exists:
                assert int_value(nodes, "inverse") == pow(a, -1, b)
                assert relation("inverse_verification")[0]["values"]["result"] == "1"
            else:
                assert "obstruction" in nodes and gcd > 1
    elif mode == "powers":
        a, e, n = int(s["base"]), int(s["exponent"]), int(s["powerModulus"])
        assert int_value(nodes, "powerResult") == pow(a, e, n)
        assert len(relation("conditional_accumulator")) == e.bit_length()
        for i, edge in enumerate(relation("conditional_accumulator")):
            v = edge["values"]
            before, after, f, remaining = (int(v[k]) for k in ("before", "after", "factor", "remaining"))
            assert remaining == e >> i and v["odd"] == bool((e >> i) & 1)
            assert f == pow(a, 1 << i, n)
            assert after == before*(f if v["odd"] else 1) % n
            assert before*pow(f, remaining, n) % n == pow(a, e, n)
            incoming = [x for x in edges if x["to"] == edge["from"]]
            assert len(incoming) == (2 if v["odd"] else 1)
        assert len(relation("even_bit_bypass")) == e.bit_length()-e.bit_count()
        for edge in relation("square_reduce"):
            v = edge["values"]
            assert int(v["factor"])**2 % n == int(v["result"]) == int_value(nodes, edge["to"])
        for edge in relation("residue_recurrence") + relation("cycle_closure"):
            v = edge["values"]
            assert int(v["input"])*a % n == int(v["output"])
            assert int_value(nodes, edge["from"]) == int(v["input"])
            assert int_value(nodes, edge["to"]) == int(v["output"])
        for edge in relation("cycle_closure"):
            v = edge["values"]
            values = [int_value(nodes, "cycle"+str(k)) for k in range(v["prefix"]+v["period"])]
            assert len(set(values)) == len(values)
            assert values[-1]*a % n == values[v["prefix"]]
            assert v["prefix"] == values.index(values[-1]*a % n)
        for edge in relation("unclosed_continuation"):
            assert int_value(nodes, edge["from"])*a % n == int_value(nodes, edge["to"])
            assert edge["values"]["complete"] is False
            seen=[int(v["values"]["value"]) for key,v in nodes.items() if re.fullmatch(r"cycle\d+",key)]
            assert int_value(nodes,edge["to"]) not in seen,"A displayed repeated residue must close the existing cycle"
        if e == 0:
            assert len(relation("zero_exponent")) == 1 and not relation("conditional_accumulator")
    elif mode == "primes":
        for prefix in ("factor", "newFactor"):
            roots = [e for e in relation("factor_product") if e["to"] == prefix+"n"]
            target = int_value(nodes, prefix+"n")
            assert math.prod(int_value(nodes, e["from"]) for e in roots) == target
            for edge in roots:
                v = edge["values"]
                assert prime(int(v["prime"]))
                assert int(v["prime"])**v["exponent"] == int_value(nodes, edge["from"])
                leaves = [e for e in relation("repeated_prime_factor") if e["to"] == edge["from"]]
                assert len(leaves) == v["exponent"]
                assert all(int_value(nodes, e["from"]) == int(v["prime"]) for e in leaves)
        P, N = int_value(nodes, "primeProduct"), int_value(nodes, "euclidN")
        listed = [int(e["values"]["prime"]) for e in relation("prime_product")]
        assert P == math.prod(listed) and N == P+1
        assert all(N % p == 1 for p in listed)
        assert all(int(e["values"]["prime"]) not in listed for e in relation("unlisted_prime_divisor"))
    elif mode == "lemma":
        a, b, d = int(s["factorA"]), int(s["factorB"]), int(s["divisor"])
        assert int_value(nodes, "ab") == a*b
        flags = (a*b % d == 0, a % d == 0, b % d == 0)
        v = nodes["lemmaConclusion"]["values"]
        assert (v["dividesProduct"],v["dividesA"],v["dividesB"]) == flags
        assert v["counterexample"] == (flags[0] and not flags[1] and not flags[2])
        assert nodes["primeHypothesis"]["values"]["prime"] == prime(d)
        for edge in relation("divisibility_test"):
            v = edge["values"]
            assert int_value(nodes, edge["from"]) % d == int(v["remainder"]) == int_value(nodes, edge["to"])
            assert v["divides"] == (int(v["remainder"]) == 0)
        if "lemmaBezout" in nodes:
            v = nodes["lemmaBezout"]["values"]
            # The graph also exposes the stronger coprime-divisor version for
            # composite d. Primality is sufficient here, not necessary.
            assert math.gcd(a,d)==1 and a % d and a*int(v["x"])+d*int(v["y"]) == 1
            assert a*b*int(v["x"])+d*b*int(v["y"]) == b
            proof = relation("prime_divisor_inference")[0]["values"]
            assert proof["antecedent"] == flags[0]
            assert proof["conclusion"] == (flags[2] if flags[0] else None)
    elif mode == "totient":
        n = int(s["totientN"])
        survivors = list(range(n))
        assert int_value(nodes, "classes") == n
        for edge in relation("exclude_multiples"):
            v = edge["values"]
            p = int(v["prime"])
            assert prime(p) and list(map(int, v["before"])) == survivors
            removed = [a for a in survivors if a % p == 0]
            assert list(map(int, v["removed"])) == removed
            survivors = [a for a in survivors if a % p]
            out = nodes[edge["to"]]["values"]
            assert list(map(int, out["removed"])) == removed
            assert list(map(int, out["remaining"])) == survivors
        expected = [a for a in range(n) if math.gcd(a,n) == 1]
        assert survivors == expected and int_value(nodes, "phi") == len(expected)
        for e in relation("survivor_count"):
            v=e["values"];removed=nodes[e["from"]]["values"]["removed"]
            remaining=nodes[e["from"]]["values"]["remaining"]
            assert (v["before"],v["removed"],v["after"])==(len(removed)+len(remaining),len(removed),len(remaining))
            assert int_value(nodes,e["to"])==len(remaining)
        membership = [n for n in g["nodes"] if n["kind"] == "membership"]
        assert len(membership) == n
        for member in membership:
            v = member["values"];a = int(v["a"])
            assert int(v["gcd"]) == math.gcd(a,n) and v["unit"] == (a in expected)
    elif mode == "theorem":
        a, n = int(s["theoremA"]), int(s["theoremN"])
        units = [u for u in range(1,n) if math.gcd(u,n) == 1]
        images = [a*u % n for u in units]
        permutation = math.gcd(a,n) == 1
        maps = relation("unit_multiplication")
        assert len(maps) == len(units)
        assert [int(e["values"]["u"]) for e in maps] == units
        assert [int(e["values"]["image"]) for e in maps] == images
        for u,e in zip(units,maps):
            v=e["values"]
            assert (int(v["u"]),int(v["a"]),int(v["n"]),int(v["image"]))==(u,a,n,a*u%n)
            assert v["imageIsUnit"]==(math.gcd(a*u,n)==1)
        assert nodes["coprime"]["values"]["permutation"] == permutation
        if permutation:
            assert sorted(images) == units
        P = math.prod(units) % n
        Q = math.prod(images) % n
        assert int_value(nodes,"unitProduct") == P and int_value(nodes,"imageProduct") == Q
        assert math.gcd(P,n) == 1 and int(nodes["cancel"]["values"]["inverse"]) == pow(P,-1,n)
        assert int_value(nodes,"euler") == pow(a,len(units),n)
        assert int_value(nodes,"fermat") == pow(a,n-1,n)
        assert nodes["fermatHypothesis"]["values"]["prime"] == prime(n)
        assert all(e["values"]["permutation"] == permutation for e in maps)
        assert relation("product_equality")[0]["values"]["permutation"] == permutation
        assert relation("euler_cancellation")[0]["values"]["coprime"] == permutation
    elif mode == "rsa":
        p,q,e,M = (int(s[k]) for k in ("rsaP","rsaQ","rsaE","rsaMessage"))
        n,phi = p*q,(p-1)*(q-1)
        valid = prime(p) and prime(q) and p!=q and math.gcd(e,phi)==1 and M<n
        rfc_bounds = prime(p) and prime(q) and p!=q and p%2==q%2==1 and 3<=e<n
        assert nodes["rsaValidity"]["values"]["valid"] == valid
        assert nodes["rfcBounds"]["values"]["rfcPublicBounds"] == rfc_bounds
        assert ("rsaD" in nodes) == valid
        if valid:
            d = pow(e,-1,phi)
            assert [int_value(nodes,k) for k in ("rsaN","rsaE","rsaPhi","rsaD","rsaMessage","rsaCipher","rsaRecovered")] == [n,e,phi,d,M,pow(M,e,n),M]
            witness=relation("rsa_private_inverse")[0]["values"]["bezout"]
            assert e*int(witness["x"])+phi*int(witness["y"]) == 1
            tree=relation("factor_product")
            assert math.prod(int_value(nodes,x["from"]) for x in tree)==n
            assert sorted(int(x["values"]["prime"]) for x in tree)==sorted((p,q))
            for i,P in enumerate((p,q)):
                v=nodes["rsaPrimeBranch"+str(i)]["values"]
                assert int(v["prime"]) == P and v["zero"] == (M%P==0)
                assert int(v["ed"]) == e*d and int(v["edModPrimeMinusOne"]) == e*d%(P-1) == 1%(P-1)
                assert int_value(nodes,"rsaPrimeMessage"+str(i)) == int_value(nodes,"rsaPrimeClear"+str(i)) == M%P
            assert len(relation("rsa_crt_reconstruction")) == 2
        else:
            assert "candidatePhi" in nodes and not relation("rsa_encrypt") and not relation("rsa_decrypt")
            assert int_value(nodes,"candidatePhi") == phi
    else:
        raise AssertionError(mode)


def test_independent_integer_relationships_for_all_ten_stations():
    cases = [{"mode":"division","a":str(a),"modulus":str(n)} for a in range(-20,21) for n in range(2,10)]
    cases += [{"mode":"product","a":str(a),"b":str(b),"modulus":str(n)} for a,b,n in itertools.product(range(-4,5),range(-4,5),range(2,10))]
    cases += [{"mode":"gcd","gcdA":str(a),"gcdB":str(b)} for a,b in itertools.product(range(-12,13),repeat=2)]
    cases += [{"mode":"inverse","inverseA":str(a),"inverseModulus":str(n)} for a in range(-12,13) for n in range(2,20)]
    cases += [{"mode":"powers","base":str(a),"exponent":str(e),"powerModulus":str(n)} for a,e,n in itertools.product(range(-3,4),range(9),range(2,10))]
    cases += [{"mode":"primes","factorN":str(n)} for n in range(2,201)]
    cases += [{"mode":"lemma","divisor":str(d),"factorA":str(a),"factorB":str(b)} for d,a,b in itertools.product(range(2,14),range(-4,5),range(-4,5))]
    cases += [{"mode":"totient","totientN":str(n)} for n in range(2,61)]
    cases += [{"mode":"theorem","theoremA":str(a),"theoremN":str(n)} for a in range(-8,9) for n in range(2,61)]
    cases += [{"mode":"rsa","rsaP":str(p),"rsaQ":str(q),"rsaE":str(e),"rsaMessage":str(M)} for p,q,e in [(5,11,3),(11,17,7),(2,3,5),(3,5,3)] for M in range(p*q)]
    for start in range(0,len(cases),250):
        for g in node([{"kind":"graph","state":s} for s in cases[start:start+250]]):
            verify_graph(g)
    assert len(cases) == 5051


def boundary_cases():
    meta=node([{"kind":"meta"}])[0]
    return meta,[{"mode":c["modes"][0],c["key"]:v} for c in meta["controls"] for v in (c["min"],c["max"])]


def test_every_original_domain_endpoint_large_integer_and_rsa_scope_distinction():
    meta,cases=boundary_cases()
    assert len(meta["controls"])==22 and len(cases)==44 and meta["PAGE_SIZE"]==4
    historical=node([{"kind":"historicalManifest"}])[0]
    assert meta["initial"]==historical["initial"]
    assert [{k:c[k] for k in ("key","min","max")} for c in meta["controls"]]==historical["controls"]
    cases += [dict(mode="division",a="-17",modulus="5"),dict(mode="division",a="9007199254740993",modulus="97"),
              dict(mode="powers",base="2",exponent="340",powerModulus="341"),dict(mode="powers",base="0",exponent="0"),
              dict(mode="theorem",theoremA="2",theoremN="341"),dict(mode="theorem",theoremA="2",theoremN="561"),
              dict(mode="rsa",rsaP="2",rsaQ="2",rsaE="2",rsaMessage="0"),
              dict(mode="rsa",rsaP="9",rsaQ="17"),dict(mode="rsa",rsaP="11",rsaQ="11"),
              dict(mode="rsa",rsaE="187"),dict(mode="rsa",rsaE="8"),dict(mode="rsa",rsaMessage="187")]
    for g in node([{"kind":"graph","state":s} for s in cases]):
        verify_graph(g)
    invalid=node([{"kind":"core","state":s} for s in cases[-6:]])
    assert invalid[0]["phi"] is None and len(invalid[0]["issues"])==1
    assert invalid[1]["phi"] is None and invalid[2]["phi"] is None
    assert invalid[3]["valid"] and not invalid[3]["rfcPublicBounds"]
    assert not invalid[4]["valid"] and invalid[4]["rfcPublicBounds"]
    assert not invalid[5]["valid"] and invalid[5]["phi"]=="160"
    cap_states=[dict(mode="powers",base="3",powerModulus=str(n),exponent="100") for n in (256,512)]
    cap=node([{"kind":"graph","state":s} for s in cap_states])
    helper=node([{"kind":"cycleBoundary","state":s} for s in cap_states])
    for n,b in zip((256,512),helper):
        c=b["cycle"]
        assert c==b["direct"]
        assert c["values"]==[str(pow(3,k,n)) for k in range(64)]
        assert len(set(c["values"]))==64
        assert c["complete"]==(n==256)
        assert (c["prefix"],c["period"])==((0,64) if n==256 else (None,None))
        next_residue=int(c["values"][-1])*3 % n
        assert next_residue==(1 if n==256 else 257)
        assert (str(next_residue) in c["values"])==(n==256)
        assert ("cycle length 64" in " ".join(b["proof"]))==(n==256)
        assert ("no period has been established" in " ".join(b["proof"]))==(n==512)
    for g in cap:verify_graph(g)
    closure=[e for e in cap[0]["edges"] if e["relation"]=="cycle_closure"]
    assert len(closure)==1 and closure[0]["values"]["prefix"]==0 and closure[0]["values"]["period"]==64
    assert (closure[0]["from"],closure[0]["to"])==("cycle63","cycle0")
    assert closure[0]["values"]["prefix"]==helper[0]["cycle"]["prefix"]
    assert closure[0]["values"]["period"]==helper[0]["cycle"]["period"]
    assert not [e for e in cap[0]["edges"] if e["relation"]=="unclosed_continuation"]
    assert not [n for n in cap[0]["nodes"] if n["id"]=="cycleContinuation"]
    assert not [e for e in cap[1]["edges"] if e["relation"]=="cycle_closure"]
    continuation=[e for e in cap[1]["edges"] if e["relation"]=="unclosed_continuation"]
    assert len(continuation)==1 and continuation[0]["values"]["output"]=="257"
    assert continuation[0]["values"]["complete"] is False


def positions(view):
    """Reconstruct categorical placement from group order and source row/column indices."""
    outside=sorted({n["group"] for n in view["nodes"] if n["context"]})
    order=[-1,*range(view["groupStart"],view["groupEnd"]),*outside]
    cursor=30;origins={}
    for group in order:
        extent=view["extents"].get(str(group),{"min":0,"max":0})
        origins[group]=cursor-extent["min"]
        cursor+=extent["max"]-extent["min"]+80
    return {n["id"]:[n["col"]*230+120,origins[n["group"]]+n["layoutOffset"]] for n in view["nodes"]}


def test_complete_pagination_preserves_every_node_edge_witness_and_context_endpoint():
    meta,endpoints=boundary_cases()
    cases=[{"mode":mode} for mode,_ in meta["stations"]]+endpoints
    cases += [dict(mode="powers",base="3",powerModulus=str(n),exponent="100") for n in (256,512)]
    for s in cases:
        packet=node([{"kind":"pages","state":s}])[0]
        full=packet["full"];windows=packet["windows"]
        originals={n["id"]:n for n in full["nodes"]}
        original_indices={key:i for i,key in enumerate(originals)}
        original_edges={e["id"]:e for e in full["edges"]}
        node_union=set();edge_union=set()
        assert len(windows)==max(1,math.ceil(len(full["groups"])/4))
        for i,v in enumerate(windows):
            assert v["page"]==i and v["pageCount"]==len(windows)
            assert (v["groupStart"],v["groupEnd"])==(4*i,min(len(full["groups"]),4*i+4))
            assert (v["totalNodes"],v["totalEdges"])==(len(originals),len(original_edges))
            ids={n["id"] for n in v["nodes"]}
            for n in v["nodes"]:
                clean={k:value for k,value in n.items() if k!="context"}
                assert clean==originals[n["id"]]
                assert n["displayId"]=="N"+str(original_indices[n["id"]]+1)
                assert n["context"]==(n["group"]!=-1 and not v["groupStart"]<=n["group"]<v["groupEnd"])
            expected_edges=[e for e in full["edges"] if e["group"]==-1 or v["groupStart"]<=e["group"]<v["groupEnd"]]
            assert v["edges"]==expected_edges
            assert all(e["from"] in ids and e["to"] in ids for e in v["edges"])
            expected=positions(v)
            for key,p in v["positions"]:
                assert p==pytest.approx(expected[key],abs=1e-12)
            node_union.update(ids);edge_union.update(e["id"] for e in v["edges"])
        assert node_union==set(originals) and edge_union==set(original_edges)
    normalized=node([{"kind":"normalize","state":{"mode":"product","diagramPage":10000}},
                     {"kind":"normalize","state":None}])
    assert normalized[0]["diagramPage"]==0 and normalized[1]["diagramPage"]==0


def test_emitted_semantic_3d_nodes_edges_self_loops_and_direction_heads():
    meta,endpoints=boundary_cases()
    cases=[{"mode":mode} for mode,_ in meta["stations"]]+endpoints
    cases += [dict(mode="powers",base="1",exponent="0",powerModulus="7"),
              dict(mode="powers",base="0",exponent="8",powerModulus="7")]
    cases += [dict(mode="powers",base="3",powerModulus=str(n),exponent="100") for n in (256,512)]
    requests=[]
    for s in cases:
        packet=node([{"kind":"pages","state":s,"selected":True}])[0]
        requests.extend({"kind":"geometry","state":{**s,"diagramPage":v["page"]}} for v in packet["windows"])
    depths={"integer":0,"operation":.5,"hypothesis":-.8,"proof":-1.2,"witness":.8,
            "set":1.2,"membership":1.5,"scope":-1.6,"inequality":-.4}
    loops=nodes_count=edges_count=0
    for start in range(0,len(requests),25):
        for result in node(requests[start:start+25]):
            v=result["view"];xy=positions(v)
            assert result["state"]["diagramPage"]==v["page"]
            expected={n["id"]:[xy[n["id"]][0]/110,-xy[n["id"]][1]/150,depths.get(n["kind"],0)] for n in v["nodes"]}
            primitives=result["primitives"]
            spheres=[p for p in primitives if p.get("nt_relation_kind")=="node"]
            labels=[p for p in primitives if p["kind"]=="label"]
            wires=[p for p in primitives if p.get("nt_relation_kind")=="edge"]
            heads=[p for p in primitives if p.get("nt_relation_kind")=="arrow"]
            assert len(spheres)==len(v["nodes"]) and len(wires)==len(heads)==len(v["edges"])
            assert len(labels)==len(v["nodes"])
            assert all(math.isfinite(x) for p in primitives for q in p["points"] for x in q)
            for p,n in zip(spheres,v["nodes"]):
                assert p["id"]==n["id"] and p["label"]==n["label"] and p["values"]==n["values"]
                assert p["points"][0]==pytest.approx(expected[n["id"]],abs=1e-12)
            for p,n in zip(labels,v["nodes"]):
                assert p["text"]==n["displayId"] and re.fullmatch(r"N\d+",p["text"])
                assert p["points"][0]==pytest.approx([expected[n["id"]][0],expected[n["id"]][1]+.24,expected[n["id"]][2]],abs=1e-12)
                assert n["displayId"]+" = "+n["label"] in result["readout"]
            for p,h,e in zip(wires,heads,v["edges"]):
                assert (p["id"],p["from"],p["to"],p["relation"],p["values"])==(e["id"],e["from"],e["to"],e["relation"],e["values"])
                if e["from"]!=e["to"]:
                    assert p["points"][0]==pytest.approx(expected[e["from"]],abs=1e-12)
                    assert p["points"][-1]==pytest.approx(expected[e["to"]],abs=1e-12)
                else:
                    loops+=1
                    assert len(p["points"])>20
                    center=expected[e["from"]]
                    assert min(math.dist(q,center) for q in p["points"])<.08
                assert h["id"]==e["id"] and h["points"][1]==pytest.approx(p["points"][-1],abs=1e-12)
                direction=[b-a for a,b in zip(p["points"][-2],p["points"][-1])]
                for flank in (h["points"][0],h["points"][2]):
                    assert sum((f-tip)*d for f,tip,d in zip(flank,h["points"][1],direction))<0
            nodes_count+=len(spheres);edges_count+=len(wires)
    assert loops>=2 and nodes_count>1000 and edges_count>1000


def test_original_questions_and_preserved_historical_arithmetic_review_bytes():
    lesson=Curriculum().node("math.4.numtheory")
    assert len(lesson["quiz"])==10
    assert hashlib.sha256((ROOT/"docs/number-theory-scientific-independent-review-20261012.json").read_bytes()).hexdigest()==OLD_REVIEW_SHA
    assert hashlib.sha256((ROOT/"docs/number-theory-reader-review-20261012/historical-scoped-source/test_math_number_theory_lab.py").read_bytes()).hexdigest()==OLD_TEST_SHA
    modes=["division","gcd","product","powers","inverse","rsa","powers","lemma","totient","theorem"]
    states=[{"mode":m} for m in modes]
    states[2]["a"]="7";states[6].update(base="7",exponent="2023",powerModulus="10")
    graphs=node([{"kind":"graph","state":s} for s in states])
    for g in graphs:verify_graph(g)
    nodes=[{n["id"]:n for n in g["nodes"]} for g in graphs]
    assert [int_value(nodes[i],key) for i,key in [(0,"r"),(1,"euclidg"),(2,"result"),(3,"powerResult"),(4,"inverse"),(6,"powerResult"),(8,"phi"),(9,"fermat")]]==[2,12,1,2,5,3,8,1]
    assert int_value(nodes[5],"rsaD")==23 and nodes[7]["lemmaConclusion"]["values"]["counterexample"]


DOM = r"""
const fs=require('node:fs');const states=JSON.parse(fs.readFileSync(0,'utf8'));
const observers=[],pending=new Set();
function childChanged(root){for(const o of observers)if(o.root===root&&o.options.childList)pending.add(o.fn);}
function flush(){let limit=20;while(pending.size){if(!--limit)throw Error('Observer loop');
 const callbacks=[...pending];pending.clear();callbacks.forEach(f=>f());}}
class Text{constructor(v){this.nodeType=3;this.textContent=String(v);}}
class Element{
 constructor(tag){this.nodeType=1;this.tagName=tag;this.attributes={};this.children=[];this.events={};
  this.style={};this.dataset={};this.isConnected=true;this._value='';this.scrollTop=0;this.scrollLeft=0;
  this.clientHeight=400;this.clientWidth=390;this._scrollHeight=2000;this.scrollWidth=1050;
  this.classList={toggle:(name,on)=>{const s=new Set((this.attributes.class||'').split(/\s+/).filter(Boolean));
    on=on===undefined?!s.has(name):on;on?s.add(name):s.delete(name);this.attributes.class=[...s].join(' ');}};}
 get scrollHeight(){if((this.attributes.class||'').includes('nt-semantic-viewport')){const svg=this.querySelector('svg');return Number(svg?.getAttribute('viewBox')?.split(' ')[3])||this._scrollHeight;}return this._scrollHeight;}
 set scrollHeight(v){this._scrollHeight=v;}
 setAttribute(k,v){this.attributes[k]=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=String(v);for(const o of observers)
  if(o.root===this&&o.options.attributeFilter?.includes(k))pending.add(o.fn);}
 getAttribute(k){return this.attributes[k]??null;}
 removeAttribute(k){delete this.attributes[k];}
 get value(){return this._value;}set value(v){this._value=String(v);}
 get type(){return this.attributes.type;}set type(v){this.attributes.type=String(v);}
 append(...items){for(const item of items){this.children.push(item);item.parentNode=this;}childChanged(this);}
 prepend(...items){this.children.unshift(...items);items.forEach(i=>i.parentNode=this);}
 before(item){const a=this.parentNode.children,index=a.indexOf(this);a.splice(index,0,item);item.parentNode=this.parentNode;childChanged(this.parentNode);}
 replaceChildren(...items){this.children=[];this.append(...items);}
 get textContent(){return this.children.map(c=>c.textContent).join('');}
 set textContent(v){this.children=[new Text(v)];}
 addEventListener(k,f){(this.events[k]??=[]).push(f);}
 fire(k,extra={}){for(const f of this.events[k]||[])f({target:this,preventDefault(){},...extra});flush();}
 all(){return [this,...this.children.filter(c=>c.nodeType===1).flatMap(c=>c.all())];}
 matches(s){if(s[0]==='.')return (this.attributes.class||'').split(/\s+/).includes(s.slice(1));
  if(s[0]==='['){const m=s.match(/^\[([^=\]]+)(?:="([^"]*)")?\]$/);return m&&
   (m[2]===undefined?Object.hasOwn(this.attributes,m[1]):this.attributes[m[1]]===m[2]);}
  return this.tagName===s;}
 querySelector(s){return this.all().find(e=>e.matches(s))||null;}
 querySelectorAll(s){return this.all().filter(e=>e.matches(s));}
 getBBox(){const width=this.textContent.length*8,height=14;
  return {x:Number(this.attributes.x)-width/2,y:Number(this.attributes.y)-height,width,height};}
 scrollBy(v){this.scrollTo({top:this.scrollTop+(v.top||0),left:this.scrollLeft+(v.left||0)});}
 scrollTo(v){if(v.top!==undefined)this.scrollTop=Math.max(0,Math.min(this.scrollHeight-this.clientHeight,v.top));
  if(v.left!==undefined)this.scrollLeft=Math.max(0,Math.min(this.scrollWidth-this.clientWidth,v.left));}
}
global.document={createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t),createTextNode:v=>new Text(v)};
global.MutationObserver=class{constructor(fn){this.fn=fn;}observe(root,options){this.disconnect();this.entry={fn:this.fn,root,options};observers.push(this.entry);}
 disconnect(){const i=observers.indexOf(this.entry);if(i>=0)observers.splice(i,1);pending.delete(this.fn);this.entry=null;}};
global.window={};const realBus=require('./web/lesson-state.js');
window.PrimerLessonStateBus={join(){},publish(){}};
const lab=require('./web/math-number-theory-lab.js'),api=require('./web/number-theory-diagrams.js');
require('./web/spatial-models.js');require('./web/spatial-number-theory-relations.js');require('./web/spatial-module-objects.js');
const item={renderer:'math-number-theory-lab',props:{scenario:lab.scenario}};
const props={scenario:'module.math.4.numtheory',family:'number-theory-exact-traces',mode:'model',context:'DOM semantic audit',lesson:'Number Theory'};
if(!window.PrimerModuleObjects.ensure({props}))throw Error('Missing semantic family');
function capture(r){const v=r.getDiagramData(),svg=r.querySelector('[data-nt-semantic-svg]');
 return {state:r.getDiagramState(),view:{page:v.page,pageCount:v.pageCount,groupStart:v.groupStart,groupEnd:v.groupEnd,
  nodes:v.nodes,edges:v.edges,extents:v.extents},positions:v.nodes.map(n=>[n.id,v.position(n)]),
  svgNodes:svg.querySelectorAll('[data-nt-semantic-node]').map(n=>({id:n.attributes['data-nt-semantic-node'],
   shape:n.children[0].tagName,attrs:n.children[0].attributes,title:n.querySelector('title').textContent,
   lines:n.querySelectorAll('tspan').map(t=>t.textContent)})),
  paths:svg.querySelectorAll('[data-nt-semantic-edge]').map(e=>({id:e.attributes['data-nt-semantic-edge'],d:e.attributes.d,title:e.querySelector('title').textContent})),
  arrows:svg.querySelectorAll('[data-nt-semantic-arrow]').map(e=>({id:e.attributes['data-nt-semantic-arrow'],d:e.attributes.d})),
  witness:JSON.parse(r.querySelector('.nt-diagram-witness').textContent),
  relations:r.querySelectorAll('[data-nt-relation]').map(e=>({id:e.attributes['data-nt-relation'],text:e.textContent})),
  pageInput:r.querySelector('[data-nt-diagram-page]').value,max:r.querySelector('[data-nt-diagram-page]').max,
  viewBox:svg.getAttribute('viewBox'),
  status:r.querySelector('.nt-diagram-status').textContent,speech:r.getModelSpeech()};}
const frames=states.map(s=>{const r=api.render(item);r.setModelState(s,false,true);flush();return capture(r);});
const endpoints=[];for(const c of lab.controls)for(const value of [c.min,c.max]){
 const r=api.render(item);r.setModelState({mode:c.modes[0]},false,true);flush();
 const input=r.querySelector('[data-nt-control="'+c.key+'"]');input.value=value;input.fire('keydown',{key:'Enter'});
 endpoints.push({state:r.getDiagramState(),aria:input.getAttribute('aria-invalid')});}
let publications=0,other=0;window.PrimerLessonStateBus={join:realBus.join,publish(...args){publications++;realBus.publish(...args);}};
const left=api.render(item,{speakButton:(fn,label)=>{const b=new Element('button');b.setAttribute('data-audit-speech','');b.speech=fn;return b;}}),right=api.renderSpatial({props,title:'Semantic graph'});
const otherRoot=new Element('section');realBus.join('phys.5.qft',otherRoot,()=>other++);
function spatialState(r){return Object.fromEntries(r.querySelectorAll('[data-parameter]').map(e=>
 [e.attributes['data-parameter'],e.attributes['data-parameter']==='diagramPage'?Number(e.value):e.value]));}
left.setModelState({mode:'powers',base:'2',exponent:'100',powerModulus:'7'},true);flush();
const from2D={left:left.getDiagramState(),right:spatialState(right),publications};
const p=left.querySelector('[data-nt-diagram-page]');p.value='10000';p.fire('change');
const clamped={left:left.getDiagramState(),right:spatialState(right),viewPage:left.getDiagramData().page,input:p.value};
const p3=right.querySelector('[data-parameter="diagramPage"]');p3.value='0';p3.fire('keydown',{key:'Enter'});
const from3D={left:left.getDiagramState(),right:spatialState(right)};
const base=right.querySelector('[data-parameter="base"]');base.value='9007199254740993';base.fire('keydown',{key:'Enter'});
const large={left:left.getDiagramState(),right:spatialState(right),type:base.type};
const spoken=left.querySelectorAll('[data-audit-speech]').map(b=>b.speech()),spokenView=left.getDiagramData();
left.setModelState(null);flush();const nullRetained=left.getDiagramState();
const viewport=left.querySelector('.nt-semantic-viewport'),beforeScroll=left.getDiagramState();
viewport.fire('keydown',{key:'End'});const scrollEnd=[viewport.scrollLeft,viewport.scrollTop];
viewport.fire('keydown',{key:'Home'});const scrollHome=[viewport.scrollLeft,viewport.scrollTop];
const afterScroll=left.getDiagramState(),scrollView=capture(left).view,scrollMetrics=[viewport.clientWidth,viewport.clientHeight];
left.querySelector('[data-nt-action="reset"]').fire('click');const reset={left:left.getDiagramState(),right:spatialState(right)};

// Actual SVG projection at three rigid camera states, including a self-loop.
const cameraState={mode:'powers',base:'1',exponent:'0',powerModulus:'7',diagramPage:0};
const cameraRoot=api.renderSpatial({props,title:'Camera audit'},{state:cameraState});
const original=window.PrimerSpatial.build(props.scenario,cameraState);
function projected(){const svg=cameraRoot.querySelector('svg');return {camera:cameraRoot.dataset.view,
 circles:svg.querySelectorAll('circle').filter(c=>c.attributes.fill!=='#fff').map(c=>c.attributes),
 polylines:svg.querySelectorAll('polyline').map(c=>c.attributes.points),
 labels:svg.querySelectorAll('.spatial-label').map(e=>({id:e.textContent,x:Number(e.attributes.x),y:Number(e.attributes.y),bbox:e.getBBox()})),
 key:cameraRoot.querySelectorAll('[data-nt-key-id]').map(tr=>({id:tr.attributes['data-nt-key-id'],cells:tr.children.map(c=>c.textContent)}))};}
const camera=[projected()];cameraRoot.querySelector('svg').fire('keydown',{key:'ArrowRight'});camera.push(projected());
cameraRoot.querySelectorAll('button').find(b=>b.textContent==='Zoom in').fire('click');camera.push(projected());
const cameraAfter=spatialState(cameraRoot);
const cameraView=api.windowGraph(api.graph(cameraAfter),cameraAfter.diagramPage);
window.PrimerSpatial.register({'audit.foreign':{initial:{x:2},controls:[{key:'x',label:'Foreign Number',min:0,max:20,step:1,numericInput:true}],
 build(s,g){g.sphere([s.x,0,0],.1,g.colors.blue);return {readout:typeof s.x+':'+s.x,note:'Foreign audit',legend:[]};}}});
const foreign=api.renderSpatial({props:{scenario:'audit.foreign'},title:'Foreign audit'});
const foreignIsolation=foreign?{key:!!foreign.querySelector('.nt-spatial-key-scroll'),type:foreign.querySelector('[data-parameter="x"]').type,
 readout:foreign.querySelector('.spatial-readout').textContent}:null;
process.stdout.write(JSON.stringify({frames,endpoints,from2D,clamped,from3D,large,nullRetained,
 beforeScroll,afterScroll,scrollEnd,scrollHome,scrollView,scrollMetrics,reset,other,camera,original:original.primitives,cameraAfter,
 spoken,spokenNodes:spokenView.nodes,spokenEdges:spokenView.edges,cameraNodes:cameraView.nodes,foreignIsolation}));
"""


def test_actual_2d_svg_shapes_wires_relation_labels_and_native_shared_page_controls():
    meta,endpoints=boundary_cases()
    states=[]
    for mode,_ in meta["stations"]:
        packet=node([{"kind":"pages","state":{"mode":mode}}])[0]
        states += [{"mode":mode,"diagramPage":v["page"]} for v in packet["windows"]]
    states += [dict(mode="powers",base="1",exponent="0"),dict(mode="powers",base="0",exponent="7"),
               dict(mode="division",a="-17",modulus="5"),dict(mode="division",a="9007199254740993",modulus="97"),
               dict(mode="division",a="96",modulus="12",diagramPage=1)]
    states += [dict(mode="powers",base="3",powerModulus=str(n),exponent="100",diagramPage=10000) for n in (256,512)]
    states += endpoints
    p=subprocess.run(["node","-e",DOM],cwd=ROOT,input=json.dumps(states),capture_output=True,text=True,timeout=180,check=False)
    assert p.returncode==0,p.stderr
    data=json.loads(p.stdout)
    for frame in data["frames"]:
        v=frame["view"];xy=positions(v)
        assert frame["state"]["diagramPage"]==v["page"]==int(frame["pageInput"])
        assert int(frame["max"])==v["pageCount"]-1
        assert len(frame["svgNodes"])==len(v["nodes"]) and len(frame["paths"])==len(v["edges"])
        visible={n["id"]:n for n in frame["svgNodes"]}
        assert len({tuple(p) for _,p in frame["positions"]})==len(v["nodes"]),"Distinct semantic nodes share an anchor"
        _,_,canvas_width,canvas_height=map(float,frame["viewBox"].split())
        boxes=[]
        for n in v["nodes"]:
            rendered=visible[n["id"]];a=rendered["attrs"];x,y=xy[n["id"]]
            if n["kind"]=="unit_dot":
                assert rendered["shape"]=="circle" and [float(a[k]) for k in ("cx","cy","r")]==pytest.approx([x,y,7])
                assert rendered["title"]==n["label"]+" = 1"
                assert n["cardHeight"]==14
            else:
                assert rendered["shape"]=="rect"
                assert [float(a[k]) for k in ("x","width")]==pytest.approx([x-92,184])
                assert float(a["y"])+float(a["height"])/2==pytest.approx(y)
                assert float(a["height"])==n["cardHeight"]
                assert rendered["title"]==n["label"]
                assert re.sub(r"\s+","",''.join(rendered["lines"]))==re.sub(r"\s+","",n["label"])
            box=(float(a["cx"])-7,float(a["cy"])-7,float(a["cx"])+7,float(a["cy"])+7) if rendered["shape"]=="circle" else (
                float(a["x"]),float(a["y"]),float(a["x"])+float(a["width"]),float(a["y"])+float(a["height"]))
            assert 0<=box[0]<box[2]<=canvas_width and 0<=box[1]<box[3]<=canvas_height
            assert all(box[2]<=b[0]+1e-9 or box[0]>=b[2]-1e-9 or box[3]<=b[1]+1e-9 or box[1]>=b[3]-1e-9 for b in boxes),n["id"]+" overlaps a previous mathematical node"
            boxes.append(box)
        for path,e in zip(frame["paths"],v["edges"]):
            assert path["id"]==e["id"] and path["title"]==e["label"]
            nums=list(map(float,re.findall(r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?",path["d"])))
            assert len(nums)==8
            source,target=visible[e["from"]],visible[e["to"]]
            a,b=xy[e["from"]],xy[e["to"]]
            if e["from"]==e["to"]:
                top=float(source["attrs"]["cy"])-7 if source["shape"]=="circle" else float(source["attrs"]["y"])
                assert nums[:2]==pytest.approx([a[0],top]) and nums[-2:]==pytest.approx([a[0],top])
                assert nums[3]<top and nums[5]<top
            else:
                source_radius=7 if source["shape"]=="circle" else 92
                target_radius=7 if target["shape"]=="circle" else 92
                assert nums[:2]==pytest.approx([a[0]+source_radius,a[1]])
                assert nums[-2:]==pytest.approx([b[0]-target_radius,b[1]])
            arrow=next(h for h in frame["arrows"] if h["id"]==e["id"])
            points=list(map(float,re.findall(r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?",arrow["d"])))
            assert len(points)==6 and points[2:4]==pytest.approx(nums[-2:])
            tangent=[nums[-2]-nums[-4],nums[-1]-nums[-3]]
            for flank in (points[:2],points[4:]):
                assert sum((f-t)*d for f,t,d in zip(flank,points[2:4],tangent))<0
        assert frame["witness"]["edges"]==v["edges"]
        assert frame["witness"]["nodes"]==[{k:n[k] for k in ("id","label","kind","values")} for n in v["nodes"]]
        originals={n["id"]:n for n in v["nodes"]}
        assert frame["relations"]==[{"id":e["id"],"text":originals[e["from"]]["label"]+" → "+originals[e["to"]]["label"]+": "+e["label"]} for e in v["edges"]]
        assert all(n["label"] in frame["speech"] for n in v["nodes"])
        assert all(e["label"] in frame["speech"] for e in v["edges"])
    assert len(data["endpoints"])==44
    expected=node([{"kind":"normalize","state":s} for s in endpoints])
    assert [e["state"] for e in data["endpoints"]]==expected
    assert all(e["aria"] is None for e in data["endpoints"])
    assert data["from2D"]["left"]==data["from2D"]["right"] and data["from2D"]["publications"]==1
    assert data["clamped"]["left"]==data["clamped"]["right"]
    assert data["clamped"]["left"]["diagramPage"]==data["clamped"]["viewPage"]==int(data["clamped"]["input"])
    assert data["from3D"]["left"]==data["from3D"]["right"] and data["from3D"]["left"]["diagramPage"]==0
    assert data["large"]["left"]==data["large"]["right"]==data["nullRetained"]
    assert data["large"]["left"]["base"]=="9007199254740993" and data["large"]["type"]=="text"
    assert data["beforeScroll"] == data["afterScroll"]
    # Home/End now reveal real cards rather than the superseded empty SVG corner.
    v = data["scrollView"]
    xy = positions(v)
    cards = [(n, xy[n["id"]], n["cardHeight"]) for n in v["nodes"]]
    last = max(cards, key=lambda row: row[1][1] + row[2] / 2)
    first = min(cards, key=lambda row: (row[1][1] - row[2] / 2, row[1][0]))
    width, height = data["scrollMetrics"]
    for (n, (x, y), h), (left, top) in [(last, data["scrollEnd"]), (first, data["scrollHome"])]:
        half_width = 7 if n["kind"] == "unit_dot" else 92
        assert left <= x - half_width and x + half_width <= left + width
        assert top <= y - h / 2 and y + h / 2 <= top + height
    assert data["reset"]["left"]==data["reset"]["right"]=={**meta["initial"],"diagramPage":0}
    assert data["other"]==0
    assert len(data["spoken"])==2
    for speech in data["spoken"]:
        assert all(n["label"] in speech for n in data["spokenNodes"])
        assert all(e["label"] in speech for e in data["spokenEdges"])
    assert data["foreignIsolation"] in (None,{"key":False,"type":"number","readout":"number:2"})
    verify_projected_camera(data)


def verify_projected_camera(data):
    primitives=[p for p in data["original"] if p["kind"]!="label"]
    bounds=[]
    for p in primitives:
        for q in p["points"]:
            bounds += [[v+sign*p["radius"] for v in q] for sign in (-1,1)] if "radius" in p else [q]
    center=[(min(q[i] for q in bounds)+max(q[i] for q in bounds))/2 for i in range(3)]
    radius=max([.1]+[math.dist(q,center)+p.get("radius",0) for p in primitives for q in p["points"]])
    for frame in data["camera"]:
        assert sorted(t["id"] for t in frame["labels"])==sorted(n["displayId"] for n in data["cameraNodes"])
        assert frame["key"]==[{"id":n["displayId"],"cells":[n["displayId"],n["label"]]} for n in data["cameraNodes"]]
        boxes=[]
        for label in frame["labels"]:
            assert re.fullmatch(r"N\d+",label["id"])
            b=label["bbox"];box=(b["x"],b["x"]+b["width"],b["y"],b["y"]+b["height"])
            assert 0<=box[0]<=box[1]<=600 and 0<=box[2]<=box[3]<=420
            assert all(box[1]<=p[0] or box[0]>=p[1] or box[3]<=p[2] or box[2]>=p[3] for p in boxes)
            boxes.append(box)
        yaw,pitch,zoom=map(float,frame["camera"].split(','))
        yaw,pitch=math.radians(yaw),math.radians(pitch)
        def rotate(q):
            x,y,z=[v-c for v,c in zip(q,center)]
            X=x*math.cos(yaw)+z*math.sin(yaw);Z=-x*math.sin(yaw)+z*math.cos(yaw)
            return X,y*math.cos(pitch)-Z*math.sin(pitch),y*math.sin(pitch)+Z*math.cos(pitch)
        extent=[(rotate(q),p.get("radius",0)) for p in primitives for q in p["points"]]
        fit=min(282/max([.1]+[abs(q[0])+r for q,r in extent]),192/max([.1]+[abs(q[1])+r for q,r in extent]))
        scale=min(175/radius*zoom,fit) if zoom<=1 else 175/radius*zoom
        def project(q):
            x,y,_=rotate(q);return [300+x*scale,210-y*scale]
        expected=[[*project(p["points"][0]),p["radius"]*scale] for p in primitives if p["kind"]=="sphere"]
        actual=[[float(c[k]) for k in ("cx","cy","r")] for c in frame["circles"]]
        assert len(actual)==len(expected)
        for a,b in zip(sorted(actual),sorted(expected)):
            assert a==pytest.approx(b,abs=1e-8)
        segments=[]
        for p in primitives:
            if p["kind"]!="line":continue
            points=p["points"]
            segments += [[project(a),project(b)] for a,b in zip(points,points[1:])] if len(points)>2 else [[project(q) for q in points]]
        rendered=[[[float(v) for v in point.split(',')] for point in line.split()] for line in frame["polylines"]]
        assert len(segments)==len(rendered)
        for a,b in zip(sorted(rendered),sorted(segments)):
            assert a[0]==pytest.approx(b[0],abs=1e-8) and a[1]==pytest.approx(b[1],abs=1e-8)
    assert data["cameraAfter"]["mode"]=="powers" and data["cameraAfter"]["base"]=="1" and data["cameraAfter"]["exponent"]=="0"


def test_semantic_review_pins_current_sources_and_preserves_evidence_scope():
    r=json.loads(REVIEW.read_text())
    assert r["result"]=="pass_for_scoped_number_theory_semantic_relationships"
    assert not r["whole_goal_complete"] and not r["browser_reader_approval"]
    assert not r["mechanical_verification_of_infinite_theorems"]
    delta=json.loads((ROOT/"docs/number-theory-viewport-delta-independent-review-20261012.json").read_text())
    for path,digest in r["reviewed_source_sha256"].items():
        source=math_product_bytes(path,(ROOT/path).read_bytes())
        if path == "web/number-theory-diagrams.js":
            assert hashlib.sha256(source).hexdigest()==delta["current_diagram_source_sha256"]
            restored=source.decode()
            for change in delta["source_delta_inverse_replacements"]:
                assert restored.count(change["new_literal"])==1
                restored=restored.replace(change["new_literal"],change["old_literal"],1)
            assert hashlib.sha256(restored.encode()).hexdigest()==digest
        else:
            assert hashlib.sha256(source).hexdigest()==digest
    assert hashlib.sha256((ROOT/delta["preserved_fixture"]["path"]).read_bytes()).hexdigest()==r["oracle_source"]["sha256"]
    amendment=json.loads((ROOT/"docs/number-theory-semantic-oracle-viewport-amendment-20261012.json").read_text())
    current=math_test_bytes(r["oracle_source"]["path"],(ROOT/r["oracle_source"]["path"]).read_bytes())
    assert hashlib.sha256(current).hexdigest()==amendment["current_sha256"]
    restored=current.decode()
    for change in amendment["inverse_replacements"]:
        assert restored.count(change["new_literal"])==1
        restored=restored.replace(change["new_literal"],change["old_literal"],1)
    assert hashlib.sha256(restored.encode()).hexdigest()==r["oracle_source"]["sha256"]
