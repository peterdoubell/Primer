"""Independent Python integer oracles and actual DOM/geometry for the authored lesson.

Finite calculations do not mechanically prove infinitude, Euler, Fermat or RSA
security. No server, browser, external key material or network is used here.
"""
import copy
import hashlib
import itertools
import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media
from tools.number_theory_runtime_compatibility import math_product_bytes, math_test_bytes
from tools.number_theory_duration_compatibility import historical_number_theory_duration

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = "math.4.numtheory.exact-integers"
REVIEW = ROOT / "docs/number-theory-scientific-independent-review-20261012.json"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js required")

BRIDGE = r"""
const fs=require('node:fs'), lab=require('./web/math-number-theory-lab.js');
const requests=JSON.parse(fs.readFileSync(0,'utf8'));
let spatial;
function spatialReady(){
  if(spatial)return;
  global.window={PrimerMathNumberTheoryLab:lab};
  require('./web/spatial-models.js');require('./web/spatial-number-theory.js');
  require('./web/spatial-module-objects.js');
  const props={scenario:'module.math.4.numtheory',family:'number-theory-exact-traces',
    mode:'model',context:'Independent integer audit',lesson:'Number Theory'};
  if(!window.PrimerModuleObjects.ensure({props}))throw Error('Missing authored spatial binding');
  spatial=window.PrimerSpatial;
}
const result=requests.map(r=>{
  if(r.kind==='meta')return {initial:lab.initial,controls:lab.controls,stations:lab.stations,
    presets:lab.presets,scenario:lab.scenario,key:lab.key,frozen:Object.isFrozen(lab)};
  if(r.kind==='normalize')return lab.normalize(r.value);
  if(r.kind==='valid')return lab.validInteger(r.value,lab.controls.find(c=>c.key===r.key));
  if(r.kind==='helper')return lab[r.method](...r.args);
  if(r.kind==='throws'){try{lab[r.method](...r.args);return null;}catch(e){return e.name;}}
  if(r.kind==='spatial'){
    spatialReady();const m=spatial.build('module.math.4.numtheory',r.state);
    return {model:lab.build(r.state),state:m.state,primitives:m.primitives,
      panels:m.numberTheory.panels,note:m.note,readout:m.readout};
  }
  if(r.kind==='spatialIsolation'){
    spatialReady();const p={scenario:'module.math.4.numtheory',family:'number-theory-exact-traces',
      mode:'model',context:'Independent integer audit',lesson:'Number Theory'};
    return [window.PrimerModuleObjects.ensure({props:p}),
      window.PrimerModuleObjects.ensure({props:{...p,scenario:'module.math.4.analysis'}}),
      window.PrimerModuleObjects.ensure({props:{...p,family:'lattice'}}),
      window.PrimerModuleObjects.ensure({props:{...p,mode:'context'}}),
      window.PrimerModuleObjects.ensure({props:{...p,lesson:'Other lesson'}}),
      spatial.build('module.math.4.not-authored',{})];
  }
  if(r.kind==='build'){
    const m=lab.build(r.state);
    if(r.pick==='data')return m.data;
    if(r.pick==='rsaSummary')return {valid:m.data.valid,n:m.data.n,phi:m.data.phi,d:m.data.d,
      c:m.data.encrypted?.result,clear:m.data.decrypted?.result,matches:m.data.matches,
      recoveredPhi:m.data.keyRecovery?.phi,recoveredD:m.data.keyRecovery?.d,
      factors:m.data.keyRecovery?.factorization.factors};
    return m;
  }
  throw Error('Unknown independent-audit request');
});
process.stdout.write(JSON.stringify(result,(_,v)=>typeof v==='bigint'?String(v):v));
"""


def node(requests):
    result = subprocess.run(["node", "-e", BRIDGE], cwd=ROOT,
                            input=json.dumps(requests), capture_output=True,
                            text=True, timeout=120, check=False)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def build(state, pick=None):
    return {"kind": "build", "state": state, "pick": pick}


def prime(n):
    """All possible small divisors, independently of runtime's shrinking trial loop."""
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))


def factors(n):
    """Collect prime divisors of the original integer, then count their powers."""
    out = []
    for p in range(2, math.isqrt(n) + 1):
        if n % p == 0 and prime(p):
            exponent = 1
            while n % p ** (exponent + 1) == 0:
                exponent += 1
            out.append({"prime": str(p), "exponent": exponent})
    accounted = math.prod(int(f["prime"]) ** f["exponent"] for f in out)
    if accounted < n:
        out.append({"prime": str(n // accounted), "exponent": 1})
    return out


def assert_euclid(d, a, b):
    g = math.gcd(a, b)
    assert int(d["gcd"]) == g
    assert a * int(d["x"]) + b * int(d["y"]) == g == int(d["identity"])
    assert d["bothZero"] == (a == b == 0)
    previous = (abs(a), abs(b))
    for row in d["rows"]:
        A, B, q, r = (int(row[k]) for k in ("dividend", "divisor", "quotient", "remainder"))
        assert (A, B) == previous
        assert (q, r) == divmod(A, B) and 0 <= r < B
        assert math.gcd(A, B) == math.gcd(B, r) == g
        assert a * int(row["x"]) + b * int(row["y"]) == A
        assert a * int(row["nextX"]) + b * int(row["nextY"]) == r
        previous = (B, r)
    assert previous[1] == 0
    assert previous[0] == g


def assert_power(d, a, e, n):
    assert int(d["result"]) == pow(a, e, n)
    assert d["bitCount"] == len(d["rows"]) == e.bit_length()
    accumulator = 1
    for i, row in enumerate(d["rows"]):
        remaining, f, before, after, squared = (int(row[k]) for k in
            ("remaining", "factor", "before", "after", "squared"))
        assert row["bit"] == i and remaining == e >> i
        assert row["odd"] == bool((e >> i) & 1)
        assert f == pow(a, 1 << i, n) and squared == pow(a, 1 << (i + 1), n)
        assert before == accumulator
        assert after == (before * (f if row["odd"] else 1)) % n
        assert (before * pow(f, remaining, n)) % n == pow(a, e, n)
        accumulator = after
    assert accumulator == int(d["result"])


def assert_model_arithmetic(m):
    """Independently check the active mathematics at every advertised endpoint."""
    d, s, mode = m["data"], m["state"], m["mode"]
    if mode == "division":
        assert (int(d["q"]), int(d["r"])) == divmod(int(s["a"]), int(s["modulus"]))
    elif mode == "product":
        a, b, n = int(s["a"]), int(s["b"]), int(s["modulus"])
        assert int(d["product"]) == a*b and int(d["result"]) == a*b % n
        assert int(d["residueProduct"]) == (a % n)*(b % n)
    elif mode in ("gcd", "inverse"):
        a = int(s["gcdA"] if mode == "gcd" else s["inverseA"])
        b = int(s["gcdB"] if mode == "gcd" else s["inverseModulus"])
        assert_euclid(d, a, b)
        if mode == "inverse":
            assert d["exists"] == (math.gcd(a, b) == 1)
            assert d["inverse"] == (str(pow(a, -1, b)) if d["exists"] else None)
    elif mode == "powers":
        a, e, n = int(s["base"]), int(s["exponent"]), int(s["powerModulus"])
        assert_power(d, a, e, n)
        assert list(map(int, d["cycle"]["values"])) == [pow(a, k, n) for k in range(len(d["cycle"]["values"]))]
    elif mode == "primes":
        assert d["factors"] == factors(int(s["factorN"]))
        assert d["prime"] == prime(int(s["factorN"]))
        witness = d["euclid"]
        N = math.prod(map(int, witness["primes"])) + 1
        assert int(witness["N"]) == N and witness["factorization"]["factors"] == factors(N)
        assert all(N % int(p) == int(r) == 1 for p, r in witness["remainderChecks"])
    elif mode == "lemma":
        divisor, a, b = int(s["divisor"]), int(s["factorA"]), int(s["factorB"])
        assert d["prime"] == prime(divisor)
        assert (d["dividesProduct"], d["dividesA"], d["dividesB"]) == (a*b % divisor == 0, a % divisor == 0, b % divisor == 0)
        assert_euclid(d["bezout"], a, divisor)
    elif mode in ("totient", "theorem"):
        n = int(s["totientN"] if mode == "totient" else s["theoremN"])
        units = [str(k) for k in range(1, n) if math.gcd(k, n) == 1]
        assert int(d["phi"]) == len(units) and d["units"] == units
        if mode == "theorem":
            a = int(s["theoremA"])
            assert d["coprime"] == (math.gcd(a, n) == 1) and d["prime"] == prime(n)
            assert_power(d["euler"], a, len(units), n)
            assert_power(d["fermat"], a, n-1, n)
    elif mode == "rsa":
        p, q, e, M = (int(s[k]) for k in ("rsaP", "rsaQ", "rsaE", "rsaMessage"))
        n, phi = p*q, (p-1)*(q-1)
        valid = prime(p) and prime(q) and p != q and math.gcd(e, phi) == 1 and M < n
        assert d["valid"] == valid and int(d["n"]) == n
        assert int(d["phiCandidate"]) == phi
        assert d["phi"] == (str(phi) if prime(p) and prime(q) and p != q else None)
        if valid:
            private = pow(e, -1, phi)
            assert int(d["d"]) == private
            assert_power(d["encrypted"], M, e, n)
            assert_power(d["decrypted"], int(d["encrypted"]["result"]), private, n)
            assert int(d["decrypted"]["result"]) == M
            assert d["keyRecovery"]["factorization"]["factors"] == factors(n)
            assert_euclid(d["keyRecovery"]["bezout"], e, phi)
    else:
        raise AssertionError(mode)


def test_nonnegative_division_and_product_against_python_integer_arithmetic():
    cases = [(a, n) for a in range(-100, 101) for n in range(2, 41)]
    cases += [(9007199254740993, 97), (-10**60, 10**18), (10**60, 10**18 - 1)]
    actual = node([build({"mode": "division", "a": str(a), "modulus": str(n)}, "data")
                   for a, n in cases])
    for (a, n), d in zip(cases, actual):
        assert (int(d["q"]), int(d["r"])) == divmod(a, n)
        assert int(d["q"]) * n + int(d["r"]) == a and 0 <= int(d["r"]) < n
    products = list(itertools.product(range(-15, 16), range(-15, 16), range(2, 13)))
    products += [(10**60, -10**60, 10**18 - 1), (9007199254740993, 9007199254740993, 97)]
    actual = node([build({"mode": "product", "a": str(a), "b": str(b), "modulus": str(n)}, "data")
                   for a, b, n in products])
    for (a, b, n), d in zip(products, actual):
        assert int(d["product"]) == a * b
        assert (int(d["ra"]), int(d["rb"])) == (a % n, b % n)
        assert int(d["residueProduct"]) == (a % n) * (b % n)
        assert int(d["result"]) == a * b % n


def test_signed_gcd_bezout_and_inverse_with_every_reported_trace():
    pairs = list(itertools.product(range(-30, 31), repeat=2))
    pairs += [(-10**60, 10**60 - 1), (9007199254740993, 9007199254740995)]
    actual = node([{"kind": "helper", "method": "euclid", "args": [str(a), str(b)]} for a, b in pairs])
    for (a, b), d in zip(pairs, actual):
        assert_euclid(d, a, b)
    cases = [(a, n) for a in range(-40, 41) for n in range(2, 41)]
    cases += [(-10**60, 10**18 - 1), (9007199254740993, 97)]
    actual = node([{"kind": "helper", "method": "inverse", "args": [str(a), str(n)]} for a, n in cases])
    for (a, n), d in zip(cases, actual):
        assert_euclid(d, a, n)
        assert d["exists"] == (math.gcd(a, n) == 1)
        if d["exists"]:
            assert int(d["inverse"]) == pow(a, -1, n)
            assert 0 <= int(d["inverse"]) < n and a * int(d["inverse"]) % n == 1
        else:
            assert d["inverse"] is None
        if n <= 40:
            assert [x for x in range(n) if a * x % n == 1] == ([int(d["inverse"])] if d["exists"] else [])


def test_binary_power_invariants_exact_large_exponents_and_complete_small_cycles():
    cases = list(itertools.product(range(-9, 10), range(17), range(2, 20)))
    cases += [(-10**60, 10**60, 10**18 - 1), (9007199254740993, 2**80 + 3, 97),
              (2, 100, 7), (7, 2023, 10), (0, 0, 7)]
    actual = node([{"kind": "helper", "method": "power", "args": list(map(str, (a, e, n)))} for a, e, n in cases])
    for (a, e, n), d in zip(cases, actual):
        assert_power(d, a, e, n)
    cycles = [(a, n) for a in range(-9, 10) for n in range(2, 20)] + [(2, 101), (0, 7)]
    actual = node([{"kind": "helper", "method": "cycle", "args": [str(a), str(n)]} for a, n in cycles])
    for (a, n), d in zip(cycles, actual):
        expected = []
        for k in range(65):
            r = pow(a, k, n)
            if r in expected:
                prefix = expected.index(r)
                break
            expected.append(r)
        if len(expected) <= 64 and k < 64:
            assert d["complete"] and d["prefix"] == prefix
            assert d["period"] == len(expected) - prefix
            assert list(map(int, d["values"])) == expected
        else:
            assert not d["complete"] and d["prefix"] is None and d["period"] is None
            assert list(map(int, d["values"])) == expected[:64]
        if d["complete"] and math.gcd(a, n) == 1:
            assert d["prefix"] == 0


def test_factorization_totient_and_infinitude_witnesses_against_divisor_sets():
    cases = list(range(2, 501)) + [65536, 999983, 999999, 1000000]
    actual = node([{"kind": "helper", "method": "factorize", "args": [str(n)]} for n in cases])
    for n, d in zip(cases, actual):
        assert d["factors"] == factors(n)
        assert d["prime"] == prime(n) and int(d["product"]) == n
        remaining = n
        for i, row in enumerate(d["tests"]):
            divisor = int(row["divisor"])
            assert divisor == (2 if i == 0 else 2 * i + 1)
            assert int(row["before"]) == remaining and divisor * divisor <= remaining
            assert int(row["remainder"]) == remaining % divisor
            assert int(row["after"]) * divisor ** row["exponent"] == remaining
            remaining = int(row["after"])
            assert remaining % divisor != 0
        assert remaining == 1 or prime(remaining)
    cases = list(range(2, 201)) + [10000]
    actual = node([{"kind": "helper", "method": "totient", "args": [str(n)]} for n in cases])
    for n, d in zip(cases, actual):
        units = [a for a in range(1, n) if math.gcd(a, n) == 1]
        assert list(map(int, d["units"])) == units and int(d["phi"]) == len(units)
        assert d["classified"] == [{"residue": str(a), "gcd": str(math.gcd(a, n)), "unit": a in units}
                                     for a in range(1, min(n, 65))]
        assert d["displayComplete"] == (n <= 65)
        count = n
        for row in d["rows"]:
            assert int(row["before"]) == count
            p = int(row["prime"])
            assert count % p == 0 and prime(p)
            count = count // p * (p - 1)
            assert int(row["after"]) == count
        assert count == len(units)
    witnesses = node([build({"mode": "primes", "primeCount": str(k)}) for k in range(1, 7)])
    for k, m in enumerate(witnesses, 1):
        d = m["data"]["euclid"]
        assert list(map(int, d["primes"])) == [2, 3, 5, 7, 11, 13][:k]
        N = math.prod(map(int, d["primes"])) + 1
        assert int(d["N"]) == N and d["factorization"]["factors"] == factors(N)
        assert all(int(r) == N % int(p) == 1 for p, r in d["remainderChecks"])
        assert all(f["prime"] not in d["primes"] for f in d["factorization"]["factors"])
    assert not witnesses[-1]["data"]["euclid"]["factorization"]["prime"]


def test_prime_divisor_hypotheses_euler_fermat_and_pseudoprime_negatives():
    cases = list(itertools.product(range(2, 21), range(-8, 9), range(-8, 9)))
    actual = node([build({"mode": "lemma", "divisor": str(d), "factorA": str(a), "factorB": str(b)}, "data")
                   for d, a, b in cases])
    for (d, a, b), row in zip(cases, actual):
        flags = (a * b % d == 0, a % d == 0, b % d == 0)
        assert row["prime"] == prime(d)
        assert (row["dividesProduct"], row["dividesA"], row["dividesB"]) == flags
        assert row["counterexample"] == (flags[0] and not flags[1] and not flags[2])
        assert [int(row[k]) for k in ("productRemainder", "aRemainder", "bRemainder")] == [a*b % d, a % d, b % d]
        assert_euclid(row["bezout"], a, d)
        if prime(d) or math.gcd(a, d) == 1:
            assert not row["counterexample"]
    cases = list(itertools.product(range(-8, 9), range(2, 41))) + [(2, 341), (2, 561), (2, 20), (13, 13)]
    actual = node([build({"mode": "theorem", "theoremA": str(a), "theoremN": str(n)}) for a, n in cases])
    for (a, n), m in zip(cases, actual):
        d = m["data"]
        phi = sum(math.gcd(k, n) == 1 for k in range(1, n))
        assert int(d["phi"]) == phi and int(d["gcd"]) == math.gcd(a, n)
        assert d["prime"] == prime(n) and d["coprime"] == (math.gcd(a, n) == 1)
        assert_power(d["euler"], a, phi, n)
        assert_power(d["fermat"], a, n - 1, n)
        assert ("Euler applies:" in m["readout"]) == d["coprime"]
        assert ("Fermat also applies:" in m["readout"]) == (prime(n) and d["coprime"])
    assert actual[-4]["data"]["fermat"]["result"] == "1" and not actual[-4]["data"]["prime"]
    assert actual[-3]["data"]["fermat"]["result"] == "1" and not actual[-3]["data"]["prime"]
    assert actual[-2]["data"]["euler"]["result"] == "16" and not actual[-2]["data"]["coprime"]
    assert actual[-1]["data"]["fermat"]["result"] == "0" and not actual[-1]["data"]["coprime"]


def test_complete_toy_rsa_round_trips_and_public_factor_recovery_include_nonunits():
    keys = [(5, 11, 3), (61, 53, 17), (11, 17, 7), (2, 3, 5), (3, 5, 3), (2, 251, 3)]
    cases = [(p, q, e, M) for p, q, e in keys for M in range(p * q)]
    actual = node([build({"mode": "rsa", "rsaP": str(p), "rsaQ": str(q), "rsaE": str(e), "rsaMessage": str(M)}, "rsaSummary")
                   for p, q, e, M in cases])
    nonunits = 0
    for (p, q, e, M), d in zip(cases, actual):
        n, phi = p * q, (p - 1) * (q - 1)
        private = pow(e, -1, phi)
        assert d["valid"] and d["matches"]
        assert (int(d["n"]), int(d["phi"]), int(d["d"])) == (n, phi, private)
        assert int(d["c"]) == pow(M, e, n) and int(d["clear"]) == M
        assert (int(d["recoveredPhi"]), int(d["recoveredD"])) == (phi, private)
        assert d["factors"] == factors(n)
        nonunits += math.gcd(M, n) != 1
    assert nonunits == sum(p*q - (p-1)*(q-1) for p, q, _ in keys) == 418
    invalid = [dict(rsaP="2", rsaQ="2", rsaE="2", rsaMessage="0"),
               dict(rsaP="11", rsaQ="11"), dict(rsaP="9", rsaQ="17"),
               dict(rsaP="11", rsaQ="17", rsaE="8"),
               dict(rsaP="11", rsaQ="17", rsaMessage="187")]
    for m in node([build({"mode": "rsa", **s}) for s in invalid]):
        assert not m["data"]["valid"] and m["data"]["keyRecovery"] is None
        assert "No RSA round trip is claimed." in m["readout"]
        assert "encrypted" not in m["data"]


def endpoint_states():
    meta = node([{"kind": "meta"}])[0]
    return meta, [{"mode": c["modes"][0], c["key"]: value}
                  for c in meta["controls"] for value in (c["min"], c["max"])]


def test_every_declared_endpoint_invalid_input_and_explicit_helper_rejection():
    meta, states = endpoint_states()
    assert meta["frozen"] and len(meta["stations"]) == 10 and len(meta["controls"]) == 22
    models = node([build(s) for s in states])
    for s, m in zip(states, models):
        assert set(m["state"]) == set(meta["initial"])
        assert all(m["state"][k] == v for k, v in s.items())
        assert all(isinstance(v, str) for v in m["state"].values())
        assert m["readout"] and m["proof"] and m["boundary"]
        assert_model_arithmetic(m)
    bad = [None, True, False, [], {}, "", " ", "3.5", "1e3", "0x10", "Infinity", "NaN", 9007199254740992]
    requests = [{"kind": "normalize", "value": v} for v in [None, True, False, [], "bad", 7]]
    expectations = [meta["initial"]] * len(requests)
    for c in meta["controls"]:
        for v in bad + [str(int(c["min"]) - 1), str(int(c["max"]) + 1)]:
            requests.append({"kind": "normalize", "value": {c["key"]: v}})
            expectations.append(meta["initial"])
    assert node(requests) == expectations
    initial_model = node([build({})])[0]
    assert node([build(None), {"kind": "helper", "method": "snapshot", "args": [None]}]) == [initial_model, initial_model]
    assert node([{"kind": "normalize", "value": {"a": " +00017 ", "extra": "ignored"}}])[0] == meta["initial"]
    invalid_helpers = [("mod", ["3", "0"]), ("mod", ["3", "-2"]),
                       ("inverse", ["3", "0"]), ("inverse", ["3", "1"]),
                       ("cycle", ["2", "1"]), ("cycle", ["2", "-1"]),
                       ("power", ["2", "-1", "7"]), ("power", ["2", "4", "1"]),
                       ("factorize", ["1"]), ("factorize", ["1000001"])]
    assert node([{"kind": "throws", "method": method, "args": args} for method, args in invalid_helpers]) == ["RangeError"] * len(invalid_helpers)


def test_exported_exact_helpers_reject_unsafe_number_arguments_before_bigint_conversion():
    methods = [("mod", [3, 7]), ("euclid", [48, 36]), ("inverse", [3, 7]),
               ("power", [2, 100, 7]), ("cycle", [2, 7]),
               ("factorize", [84]), ("totient", [20])]
    requests = []
    for method, args in methods:
        for i in range(len(args)):
            malformed = args.copy()
            malformed[i] = 9007199254740993
            requests.append({"kind": "throws", "method": method, "args": malformed})
    assert len(requests) == 13
    assert node(requests) == ["RangeError"] * len(requests)
    # Safe Number arguments remain supported; exact decimal strings retain the
    # integer that cannot be represented by a safe JavaScript Number.
    d = node([{"kind": "helper", "method": "mod", "args": [17, 5]},
              {"kind": "helper", "method": "mod", "args": ["9007199254740993", 97]},
              {"kind": "helper", "method": "power", "args": [2, 100, 7]}])
    assert d[0] == "2" and d[1] == "33" and d[2]["result"] == "2"


def test_original_ten_questions_and_strict_authored_binding():
    authored = Curriculum().node("math.4.numtheory")
    assert len(authored["quiz"]) == 10
    assert [q["answer"] for q in authored["quiz"]] == ["2", "12", "1", "2", "5",
        "The private key, which is recoverable from the public modulus", "3",
        "Six is composite, so Euclid's lemma does not apply", "8", "One, since 12 is 13 minus one"]
    model = next(m for m in authored["lesson_media"] if m.get("renderer") == "math-number-theory-lab")
    assert model["props"] == {"scenario": SCENARIO}
    _validate_lesson_media(authored)
    for props in ({"scenario": "math.4.numtheory"}, {"scenario": SCENARIO, "extra": True},
                  {"scenario": "math.5.logic.diagonal-models-proof"}, {}):
        changed = copy.deepcopy(authored)
        next(m for m in changed["lesson_media"] if m.get("renderer") == "math-number-theory-lab")["props"] = props
        with pytest.raises(ValueError, match="math-number-theory-lab"):
            _validate_lesson_media(changed)
    with pytest.raises(ValueError, match="math-number-theory-lab"):
        _validate_lesson_media({"id": "math.4.analysis", "lesson_media": [copy.deepcopy(model)]})
    states = [dict(mode="division"), dict(mode="gcd"), dict(mode="product", a="7"),
              dict(mode="powers"), dict(mode="inverse"), dict(mode="rsa"),
              dict(mode="powers", base="7", exponent="2023", powerModulus="10"),
              dict(mode="lemma"), dict(mode="totient"), dict(mode="theorem")]
    d = node([build(s, "data") for s in states])
    assert [d[0]["r"], d[1]["gcd"], d[2]["result"], d[3]["result"], d[4]["inverse"],
            d[6]["result"], d[8]["phi"], d[9]["fermat"]["result"]] == ["2", "12", "1", "2", "5", "3", "8", "1"]
    assert d[5]["keyRecovery"]["d"] == d[5]["d"] == "23" and d[7]["counterexample"]
    shell = (ROOT / "web/index.html").read_text()
    assert shell.index("/app/lesson-state.js") < shell.index("/app/math-number-theory-lab.js") < shell.index("/app/lesson-models.js")
    assert shell.index("/app/spatial-number-theory.js") < shell.index("/app/spatial-module-objects.js")
    assert "/app/math-number-theory-lab.css" in shell
    binding = json.loads((ROOT / "data/module-models.json").read_text())
    entries = binding if isinstance(binding, list) else next(v for v in binding.values() if isinstance(v, list))
    entry = next(e for e in entries if e.get("node_id") == "math.4.numtheory")
    assert entry["family"] == "number-theory-exact-traces" and entry["mode"] == "model"
    assert node([{"kind": "spatialIsolation"}])[0] == [True, False, False, False, False, None]


def test_actual_spatial_cells_coordinates_and_directed_algorithm_transitions():
    meta, endpoints = endpoint_states()
    states = [{"mode": mode} for mode, _ in meta["stations"]] + endpoints
    states += [dict(mode="gcd", gcdA="0", gcdB="0"),
               dict(mode="powers", base="0", exponent="0", powerModulus="7"),
               dict(mode="powers", exponent=str(10**60)),
               dict(mode="theorem", theoremA="2", theoremN="341"),
               dict(mode="rsa", rsaP="2", rsaQ="2", rsaMessage="0")]
    # Consecutive large Fibonacci numbers maximize the Euclid trace at this scale.
    a, b = 1, 1
    while a + b <= 10**60:
        a, b = b, a + b
    states.append(dict(mode="gcd", gcdA=str(a), gcdB=str(b)))
    actual = node([{"kind": "spatial", "state": s} for s in states])
    cells_checked = edges_checked = 0
    for row in actual:
        assert row["state"] == row["model"]["state"]
        source_panels = row["model"]["panels"]
        geometry = row["primitives"]
        assert all(math.isfinite(v) for p in geometry for q in p["points"] for v in q)
        assert len(geometry) <= 3000
        cells = [p for p in geometry if p.get("nt_kind") == "exact_cell"]
        expected_cells = []
        expected_edges = []
        for panel_index, p in enumerate(source_panels):
            visible = p["rows"][:40]
            fields = len(p["columns"])
            row_gain, field_gain = 4 / max(1, len(visible)-1), 4 / max(1, fields-1)
            for i, values in enumerate(visible):
                for j, value in enumerate(values):
                    # Independent stable-category enumeration for each field.
                    categories = list(dict.fromkeys(r[j] for r in visible))
                    slot = categories.index(value)
                    point = [panel_index*8+i*row_gain,
                             slot*2/max(1, len(categories)-1), j*field_gain]
                    expected_cells.append((panel_index, i, j, value, point))
            if "remainder divisions" in p["title"] or "Square-and-multiply" in p["title"]:
                for i in range(1, len(visible)):
                    expected_edges.append((panel_index, i-1, i,
                        [[panel_index*8+(i-1)*row_gain, -.3, 0],
                         [panel_index*8+i*row_gain, -.3, 0]]))
            record = row["panels"][panel_index]
            assert (record["totalRows"], record["visibleRows"], record["omittedRows"]) == (
                len(p["rows"]), len(visible), max(0, len(p["rows"])-40))
            assert f'{len(visible)} of {len(p["rows"])} rows drawn' in row["readout"]
        assert len(cells) == len(expected_cells)
        for primitive, (panel, i, j, value, point) in zip(cells, expected_cells):
            assert primitive["kind"] == "sphere"
            assert (primitive["panel"], primitive["row"], primitive["field"], primitive["value"]) == (panel, i, j, value)
            assert primitive["points"][0] == pytest.approx(point)
        edges = [p for p in geometry if p.get("nt_kind") == "step_transition"]
        arrows = [p for p in geometry if p.get("nt_kind") == "step_arrow"]
        assert len(edges) == len(arrows) == len(expected_edges)
        for edge, arrow, (panel, i, j, points) in zip(edges, arrows, expected_edges):
            assert (edge["panel"], edge["from"], edge["to"]) == (panel, i, j)
            assert (arrow["panel"], arrow["from"], arrow["to"]) == (panel, i, j)
            assert edge["points"][0] == pytest.approx(points[0])
            assert edge["points"][1] == pytest.approx(points[1])
            assert arrow["points"][1] == pytest.approx(points[1])
            assert arrow["points"][0][0] < points[1][0] and arrow["points"][2][0] < points[1][0]
        assert "categorical" in row["note"] and "complete exact tables" in row["note"]
        cells_checked += len(cells)
        edges_checked += len(edges)
    assert (len(actual), cells_checked, edges_checked) == (60, 2419, 230)


DOM_AUDIT = r"""
const fs=require('node:fs'), vm=require('node:vm');
const states=JSON.parse(fs.readFileSync(0,'utf8'));
class Text{constructor(value){this.nodeType=3;this.textContent=String(value);}}
class Element{
  constructor(tag){this.nodeType=1;this.tagName=tag;this.attributes={};this.children=[];
    this.events={};this.style={};this.dataset={};this.isConnected=true;this._value='';
    this.classList={toggle:(name,on)=>{const s=new Set((this.attributes.class||'').split(/\s+/).filter(Boolean));
      const wanted=on===undefined?!s.has(name):on;wanted?s.add(name):s.delete(name);
      this.attributes.class=[...s].join(' ');return wanted;}};}
  setAttribute(k,v){this.attributes[k]=String(v);}
  getAttribute(k){return this.attributes[k]??null;}
  removeAttribute(k){delete this.attributes[k];}
  get type(){return this.attributes.type;}
  set type(v){this.attributes.type=String(v);}
  get value(){return this._value;}
  set value(v){this._value=String(v);}
  append(...items){for(const v of items){this.children.push(v);v.parentNode=this;}}
  prepend(...items){this.children.unshift(...items);for(const v of items)v.parentNode=this;}
  replaceChildren(...items){this.children=[];this.append(...items);}
  get textContent(){return this.children.map(c=>c.textContent).join('');}
  set textContent(v){this.children=[new Text(v)];}
  addEventListener(name,fn){(this.events[name]??=[]).push(fn);}
  fire(name,extra={}){for(const fn of this.events[name]||[])fn({target:this,preventDefault(){},...extra});}
  all(){return [this,...this.children.filter(c=>c.nodeType===1).flatMap(c=>c.all())];}
}
global.document={createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t),
  createTextNode:v=>new Text(v)};
global.window={};
const realBus=require('./web/lesson-state.js');let publications=0,otherDeliveries=0,unknownDeliveries=0;
window.PrimerLessonStateBus={join:realBus.join,publish(...args){publications++;realBus.publish(...args);}};
const lab=require('./web/math-number-theory-lab.js');
const item={renderer:'math-number-theory-lab',props:{scenario:lab.scenario}};
const elements=(r,k,v)=>r.all().filter(e=>e.attributes[k]===v);
function describe(r){
  const tables=r.all().filter(e=>e.tagName==='table').map(t=>({
    title:t.children.find(e=>e.tagName==='caption').textContent,
    columns:t.children.find(e=>e.tagName==='thead').children[0].children.map(e=>e.textContent),
    rows:t.children.find(e=>e.tagName==='tbody').children.map(tr=>tr.children.map(e=>e.textContent))}));
  return {state:JSON.parse(r.getAttribute('data-nt-state')),tables,
    readout:elements(r,'class','nt-readout')[0].textContent,
    ledger:JSON.parse(elements(r,'class','nt-ledger')[0].textContent),speech:r.getModelSpeech(),
    controls:r.all().filter(e=>e.attributes['data-nt-control']).map(e=>({key:e.attributes['data-nt-control'],
      value:e.value,hidden:!!e.parentNode.hidden,disabled:!!e.disabled}))};
}
const mounted=states.map(s=>{const root=lab.render(item);root.setModelState(s,false,true);return describe(root);});
const invalid=[{}, {props:{}},{props:{scenario:'math.4.numtheory'}},
  {props:{scenario:lab.scenario,extra:true}},{...item,renderer:'concept-lab'}].map(x=>lab.render(x)===null);
const linkedBus=window.PrimerLessonStateBus;
window.PrimerLessonStateBus={join(){},publish(){}};
const nativeEndpoints=states.filter(s=>Object.keys(s).length===2).map(s=>{
  const r=lab.render(item),key=Object.keys(s).find(k=>k!=='mode');
  const mode=elements(r,'data-nt-mode','')[0];mode.value=s.mode;mode.fire('change');
  const input=elements(r,'data-nt-control',key)[0];input.value=s[key];input.fire('keydown',{key:'Enter'});
  return {state:describe(r).state,invalid:input.getAttribute('aria-invalid')};
});
window.PrimerLessonStateBus=linkedBus;
const left=lab.render(item),right=lab.render(item),other=new Element('section'),unknown=new Element('section');
realBus.join('phys.5.qft',other,()=>otherDeliveries++);realBus.join('unknown',unknown,()=>unknownDeliveries++);
publications=0;left.setModelState({mode:'product',a:'9007199254740993',modulus:'97'},true);
const linked={left:describe(left).state,right:describe(right).state,publications,otherDeliveries,unknownDeliveries};
const input=elements(left,'data-nt-control','a')[0];
const before=describe(left);input.value='3.5';input.fire('keydown',{key:'Enter'});
const rejected={state:describe(left).state,readout:describe(left).readout,aria:input.getAttribute('aria-invalid'),publications};
input.fire('keydown',{key:'Escape'});const escaped={value:input.value,aria:input.getAttribute('aria-invalid')};
input.value='-17';input.fire('keydown',{key:'Enter'});
const committed={left:describe(left).state,right:describe(right).state,publications};
const mode=elements(left,'data-nt-mode','')[0];mode.value='theorem';mode.fire('change');
elements(left,'data-nt-preset','fermat')[0].fire('click');const preset=describe(left);
elements(left,'data-nt-action','enlarge')[0].fire('click');
const enlarged={pressed:elements(left,'data-nt-action','enlarge')[0].getAttribute('aria-pressed'),class:left.attributes.class};
elements(left,'data-nt-action','reset')[0].fire('click');const reset={left:describe(left).state,right:describe(right).state};
realBus.publish('unknown',null,{mode:'rsa'});
const disconnected=lab.render(item);disconnected.isConnected=false;
left.setModelState({mode:'division',a:'23'});const detached=describe(disconnected).state;

// Execute the actual shared input gate in isolated native-runtime instances.
// The mock scene exposes the value's actual type in its mounted readout; it
// does not use the lesson's parser, so Number/string conversion is observable.
function gate(patch){
  const c={...lab.controls.find(c=>c.key==='a'),numericInput:true,integerValidator:v=>lab.validInteger(v,lab.controls[0]),...patch.control};
  const id=patch.id||'module.math.4.numtheory', ctx={window:{PrimerMathNumberTheoryLab:lab},document:global.document};
  vm.createContext(ctx);vm.runInContext(fs.readFileSync('./web/spatial-models.js','utf8'),ctx);
  ctx.window.PrimerSpatial.register({[id]:{initial:{[c.key]:'17'},controls:[c],
    familyId:patch.family||'number-theory-exact-traces',linkedStateKey:patch.link||'math.4.numtheory',
    normalize:s=>s,build(s,g){g.sphere([0,0,0],.1,g.colors.blue);
      return {readout:typeof s[c.key]+':'+String(s[c.key]),note:'Gate audit',legend:[]};}}});
  const r=ctx.window.PrimerSpatial.render({props:{scenario:id},title:'Gate audit'});
  const i=elements(r,'data-parameter',c.key)[0];i.value='9007199254740993';i.fire('change');
  return {type:i.type,readout:elements(r,'class','model-readout spatial-readout')[0].textContent};
}
const gates=[{}, {id:'module.math.4.analysis'}, {family:'lattice'}, {link:'phys.5.qft'},
  {control:{exactInteger:false}}, {control:{key:'invented'}}, {control:{max:'999999999999999999999999999999999999999999999999999999999999'}}].map(gate);
process.stdout.write(JSON.stringify({mounted,nativeEndpoints,invalid,linked,before:before.state,rejected,escaped,committed,
  preset,enlarged,reset,detached,otherDeliveries,unknownDeliveries,gates}));
"""


def test_actual_table_dom_keyboard_complete_state_bus_and_narrow_integer_input_gate():
    meta, states = endpoint_states()
    states = [{"mode": mode} for mode, _ in meta["stations"]] + states
    result = subprocess.run(["node", "-e", DOM_AUDIT], cwd=ROOT, input=json.dumps(states),
                            capture_output=True, text=True, timeout=90, check=False)
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)
    expected = node([build(s) for s in states])
    for dom, m in zip(actual["mounted"], expected):
        assert dom["state"] == m["state"] and dom["readout"] == m["readout"]
        assert dom["tables"] == m["panels"] and dom["ledger"] == m["data"]
        for c in dom["controls"]:
            spec = next(control for control in meta["controls"] if control["key"] == c["key"])
            assert c["value"] == m["state"][c["key"]]
            assert c["hidden"] == c["disabled"] == (m["mode"] not in spec["modes"])
        assert m["readout"] in dom["speech"] and m["boundary"] in dom["speech"]
        assert all(v in dom["speech"] for p in m["panels"] for r in p["rows"] for v in r)
    assert len(actual["nativeEndpoints"]) == 44
    for committed, m in zip(actual["nativeEndpoints"], expected[10:]):
        assert committed["state"] == m["state"] and committed["invalid"] is None
    assert all(actual["invalid"])
    assert actual["linked"]["left"] == actual["linked"]["right"]
    assert actual["linked"]["publications"] == 1
    assert actual["rejected"]["state"] == actual["before"]
    assert actual["rejected"]["aria"] == "true" and actual["rejected"]["publications"] == 1
    assert actual["escaped"] == {"value": "9007199254740993", "aria": None}
    assert actual["committed"]["left"] == actual["committed"]["right"]
    assert actual["committed"]["left"]["a"] == "-17" and actual["committed"]["publications"] == 2
    assert actual["preset"]["state"]["mode"] == "theorem" and actual["preset"]["state"]["a"] == "-17"
    assert actual["enlarged"]["pressed"] == "true" and "is-enlarged" in actual["enlarged"]["class"]
    assert actual["reset"]["left"] == actual["reset"]["right"] == actual["detached"] == meta["initial"]
    assert actual["otherDeliveries"] == actual["unknownDeliveries"] == 0
    assert actual["gates"][0] == {"type": "text", "readout": "string:9007199254740993"}
    assert actual["gates"][1:] == [{"type": "number", "readout": "number:9007199254740992"}] * 6


def test_review_receipt_pins_the_scoped_source_and_lesson_semantics():
    review = json.loads(REVIEW.read_text())
    assert review["result"] == "pass_for_scoped_number_theory_lesson"
    assert review["whole_goal_complete"] is False and review["browser_reader_approval"] is False
    assert review["mechanical_verification_of_infinite_theorems"] is False
    assert [q["number"] for q in review["quiz_mapping"]] == list(range(1, 11))
    amendment = json.loads((ROOT / "docs/number-theory-semantic-source-amendment-20261012.json").read_text())
    assert set(amendment["files"]) == {"web/math-number-theory-lab.js", "web/lesson-models.js",
                                      "web/index.html", "data/module-models.json",
                                      "tests/test_math_number_theory_lab.py"}
    def checked_source(path, expected):
        source = (ROOT / path).read_bytes()
        source = math_test_bytes(path,math_product_bytes(path,source))
        if path not in amendment["files"]:
            assert hashlib.sha256(source).hexdigest() == expected
            return
        record = amendment["files"][path]
        assert hashlib.sha256(source).hexdigest() == record["current_sha256"]
        restored = source.decode()
        for replacement in record["inverse_replacements"]:
            assert replacement["occurrences"] == 1
            assert restored.count(replacement["new_literal"]) == 1
            restored = restored.replace(replacement["new_literal"], replacement["old_literal"], 1)
        assert hashlib.sha256(restored.encode()).hexdigest() == record["historical_sha256"] == expected
        assert hashlib.sha256((ROOT / record["historical_copy"]).read_bytes()).hexdigest() == expected
    for path, digest in review["reviewed_source_sha256"].items():
        checked_source(path, digest)
    oracle = review["oracle_source"]
    checked_source(oracle["path"], oracle["sha256"])
    lesson = Curriculum().node("math.4.numtheory")
    lesson = historical_number_theory_duration(lesson)
    current_semantic = hashlib.sha256(json.dumps(lesson, sort_keys=True, ensure_ascii=False,
                                               separators=(",", ":")).encode()).hexdigest()
    assert current_semantic == amendment["current_lesson_semantic_sha256"]
    historical = (ROOT / amendment["historical_lesson"]["path"]).read_bytes()
    assert hashlib.sha256(historical).hexdigest() == amendment["historical_lesson"]["file_sha256"]
    historical_semantic = hashlib.sha256(json.dumps(json.loads(historical), sort_keys=True,
                                        ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    assert historical_semantic == review["reviewed_lesson_semantic_sha256"]
    assert amendment["historical_correspondence_only"] is True
    assert amendment["current_behavior_approval"] is False


@pytest.mark.parametrize("mutation", ["physics_text", "math_text", "minutes", "lesson_quiz", "pool_membership"])
def test_duration_counterfactual_rejects_unreviewed_corpus_or_lesson(mutation):
    from tools.number_theory_duration_compatibility import current_corpus, PHYSICS
    corpus = current_corpus()
    lesson = Curriculum().node("math.4.numtheory")
    if mutation in {"physics_text", "math_text", "pool_membership"}:
        path = PHYSICS if mutation == "physics_text" else next(
            name for name, raw in corpus.items() if json.loads(raw)["id"] == "math")
        data = json.loads(corpus[path])
        target = next(n for n in data["nodes"] if n["id"] == (
            "phys.4.fluids" if mutation == "physics_text" else "math.4.numtheory"))
        if mutation == "pool_membership":
            target["stage"] = 3
        else:
            target["quiz"][0]["prompt"] += " unreviewed text"
        corpus[path] = json.dumps(data, ensure_ascii=False).encode()
    elif mutation == "minutes":
        lesson["minutes"] = 1085
    else:
        lesson["quiz"][0]["prompt"] += " unreviewed math"
    with pytest.raises(ValueError, match="Unreviewed"):
        historical_number_theory_duration(lesson, corpus)


def test_duration_counterfactual_restores_only_verified_minutes_without_mutation():
    from tools.number_theory_duration_compatibility import current_corpus, derive, reviewed
    lesson = Curriculum().node("math.4.numtheory")
    original = copy.deepcopy(lesson)
    proof = reviewed()
    calculation = derive(current_corpus())
    assert calculation == proof["derivation"]
    assert calculation["current_estimate"]["rounded_minutes"] == lesson["minutes"] == 1075
    assert calculation["previous_estimate"]["rounded_minutes"] == 1080
    previous = historical_number_theory_duration(lesson)
    assert lesson == original and previous is not lesson
    assert {k:v for k,v in previous.items() if k != "minutes"} == {k:v for k,v in original.items() if k != "minutes"}
    assert previous["minutes"] == 1080
    assert historical_number_theory_duration(previous) == previous


def test_duration_test_source_inverse_is_exact_and_rejects_unreviewed_changes():
    from tools.number_theory_duration_compatibility import before_duration_test_bytes, reviewed
    path = "tests/test_math_number_theory_lab.py"
    raw = (ROOT / path).read_bytes()
    previous = before_duration_test_bytes(path, raw)
    assert hashlib.sha256(previous).hexdigest() == reviewed()["test_source_inverse"]["before_sha256"]
    assert before_duration_test_bytes(path, previous) == previous
    assert before_duration_test_bytes("unrelated.py", b"unrelated bytes") == b"unrelated bytes"
    with pytest.raises(ValueError, match="Unreviewed"):
        before_duration_test_bytes(path, raw + b"\n# unreviewed change\n")
