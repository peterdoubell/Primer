"""Independent finite-set audit; it does not mechanically prove metatheorems."""
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/math-logic-independent-review-20261011.json"


def node_json(source):
    result = subprocess.run(
        ["node", "-e", source], cwd=ROOT, capture_output=True,
        text=True, check=True, timeout=45,
    )
    return json.loads(result.stdout)


def encode_row(hasher, value):
    hasher.update((json.dumps(value, separators=(",", ":")) + "\n").encode())


def test_all_four_element_relation_witnesses_against_set_composition():
    """Check complete counterexamples, not just the four property booleans."""
    actual = node_json("""
      const lab=require('./web/math-logic-lab.js'), crypto=require('node:crypto');
      const h=crypto.createHash('sha256');let count=0;
      for(let n=1;n<=4;n++)for(let mask=0;mask<2**(n*n);mask++){
        const a=lab.relation(n,mask), f=a.failures;
        h.update(JSON.stringify([n,mask,a.pairs,f.reflexive,f.symmetric,
          f.antisymmetric,f.transitive])+'\\n');count++;
      }
      console.log(JSON.stringify({count,digest:h.digest('hex')}));
    """)
    expected = hashlib.sha256()
    count = 0
    for n in range(1, 5):
        names = range(n)
        for mask in range(1 << (n * n)):
            pairs = {(x, y) for x, y in itertools.product(names, repeat=2)
                     if mask & (1 << (x * n + y))}
            # These are set difference and relational composition operations,
            # independently expressed from the JavaScript nested predicate loops.
            reflexive = {(x,) for x in names if (x, x) not in pairs}
            symmetric = pairs - {(y, x) for x, y in pairs}
            antisymmetric = {(x, y) for x, y in pairs
                             if x != y and (y, x) in pairs}
            transitive = {(x, y, z) for x, y in pairs for v, z in pairs
                          if y == v and (x, z) not in pairs}
            encode_row(expected, [n, mask, sorted(pairs), sorted(reflexive),
                                  sorted(symmetric), sorted(antisymmetric),
                                  sorted(transitive)])
            count += 1
    assert actual == {"count": count, "digest": expected.hexdigest()}
    assert count == 66066


def test_spatial_relation_cells_and_directed_edges_against_bit_sets():
    actual = node_json("""
      global.window={};window.PrimerMathLogicLab=require('./web/math-logic-lab.js');
      require('./web/spatial-models.js');require('./web/spatial-logic.js');
      require('./web/spatial-module-objects.js');
      const item={props:{scenario:'module.math.5.logic',family:'logic-witness-geometry',
        mode:'model',context:'Audit',lesson:'Logic and Set Theory'}};
      if(!window.PrimerModuleObjects.ensure(item))throw Error('Missing binding');
      console.log(JSON.stringify(Array.from({length:512},(_,mask)=>{
        const a=window.PrimerSpatial.build(item.props.scenario,
          {station:'relations',relationSize:3,relationMask:mask});
        const cells=a.primitives.filter(p=>p.fidelity_kind==='logic_cell');
        const edges=a.primitives.filter(p=>p.fidelity_kind==='logic_edge');
        const arrows=a.primitives.filter(p=>p.fidelity_kind==='logic_arrow');
        return {mask,cells:cells.map(p=>[p.row,p.column,p.value]),
          edges:edges.map(p=>[Number(p.from),Number(p.to),p.label]),
          arrows:arrows.map(p=>[Number(p.from),Number(p.to)]),
          finite:a.primitives.every(p=>p.points.every(q=>q.every(Number.isFinite)))};
      })));
    """)
    for row in actual:
        pairs = [(x, y) for x, y in itertools.product(range(3), repeat=2)
                 if row["mask"] & (1 << (3 * x + y))]
        assert row["cells"] == [[x, y, (x, y) in pairs]
                                for x, y in itertools.product(range(3), repeat=2)]
        assert row["edges"] == [[x, y, f"({x + 1},{y + 1})"] for x, y in pairs]
        assert row["arrows"] == [[x, y] for x, y in pairs]
        assert row["finite"] is True


def test_review_pins_exact_scoped_runtime_and_all_quiz_requirements():
    review = json.loads(REVIEW.read_text())
    assert review["whole_goal_complete"] is False
    assert review["mechanical_verification_of_infinite_theorems"] is False
    assert review["result"] == "pass_for_scoped_logic_lesson"
    assert sorted(q["number"] for q in review["quiz_mapping"]) == list(range(1, 11))
    assert len(review["station_mapping"]) == 8
    for path, expected in review["reviewed_runtime_sha256"].items():
        from tools.qft_runtime_compatibility import historical_runtime_bytes
        assert hashlib.sha256(historical_runtime_bytes(path, (ROOT / path).read_bytes())).hexdigest() == expected
    curriculum = json.loads((ROOT / "data/curriculum/01-mathematics.json").read_text())
    def locate(value):
        if isinstance(value, dict):
            if value.get("id") == "math.5.logic":
                return value
            for child in value.values():
                result = locate(child)
                if result is not None:
                    return result
        elif isinstance(value, list):
            for child in value:
                result = locate(child)
                if result is not None:
                    return result
    lesson = locate(curriculum)
    actual = hashlib.sha256(json.dumps(lesson, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()
    assert actual == review["reviewed_lesson_semantic_sha256"]
