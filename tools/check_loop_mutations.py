"""Run six deliberate regressions against a disposable source copy.

No content directory or learner database is read or copied. Run with the same
Python environment used by pytest. Each mutant must produce a test failure.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

source = pathlib.Path(__file__).resolve().parents[1]
root = pathlib.Path(tempfile.mkdtemp(prefix="primer-mutants-"))
for directory in ("primer", "tests", "data", "web", "tools"):
    shutil.copytree(source / directory, root / directory,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
python = sys.executable
logs = root / "results"
logs.mkdir()
print("Mutation logs:", logs, flush=True)
failures = []
cases = [('advanced_floor',
  'primer/server.py',
  'return max(target, 2 if max(measured) >= 4 else 0)',
  'return target',
  'tests/test_loop_ladder_contract.py::test_stage_policy_exhaustive_reachable_sittings'),
 ('spacing',
  'primer/learner.py',
  'if need < 3 or last_pass is None or now - last_pass >= prove_gap:',
  'if True:',
  'tests/test_loop_ladder_contract.py::test_three_young_passes_are_each_spaced_and_the_page_says_three'),
 ('reading_scope',
  'primer/pacing.py',
  'baseline + reading_minutes * (rate["factor"] - 1) + srs_per_node',
  'baseline * rate["factor"] + srs_per_node',
  'tests/test_measured_pacing.py::test_the_maintenance_half_is_not_scaled_twice'),
 ('review_exposure',
  'primer/server.py',
  'burned.get(learner.review_fingerprint(q.get("prompt", "")))',
  'None',
  'tests/test_loop_ladder_contract.py::test_explained_and_abbreviated_review_keys_cannot_be_fresh_evidence'),
 ('practice_completion',
  'primer/server.py',
  'learner.log_event("practice",',
  'learner.log_event("practice_disabled",',
  'tests/test_loop_ladder_contract.py::test_unmarked_practice_counts_once_in_today_without_mastery')]
cases.append(('successful_retrieval', 'primer/learner.py',
              'if quality < 3 and row["node_id"]:', 'if row["node_id"]:',
              'tests/test_loop_ladder_contract.py::test_successful_review_does_not_burn_an_already_known_key'))
for name,file,old,new,test in cases:
 p=root/file;original=p.read_text();assert old in original,name;p.write_text(original.replace(old,new))
 try:
  env=dict(os.environ,PRIMER_DB=str(root / ('mutant-'+name+'.db')),PYTHONDONTWRITEBYTECODE='1')
  r=subprocess.run([python,'-m','pytest',test,'-q'],cwd=root,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (logs / (name + '.log')).write_text(r.stdout)
  killed = r.returncode == 1 and 'FAILED ' in r.stdout
  print(name, 'KILLED' if killed else 'UNEXPECTED', r.returncode, flush=True)
  if not killed: failures.append(name)
 finally:p.write_text(original)

if failures:
    raise SystemExit("Mutants survived or failed to run: " + ", ".join(failures))
