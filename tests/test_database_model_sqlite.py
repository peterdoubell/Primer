"""Compare shipped query and atomicity models with independent SQLite execution."""
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
ROWS = [
    (1, "Owl", "A", 10), (2, "Fox", "B", 40), (3, "Ant", "A", 70),
    (4, "Bee", "B", 90), (5, "Elk", "B", 70), (6, "Yak", "A", 20),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_query_model_matches_sqlite_for_every_control_setting():
    script = """
const fs = require('node:fs'), vm = require('node:vm');
const context = {window: {}};
vm.runInNewContext(fs.readFileSync('web/concept-models.js', 'utf8'), context);
const results = [];
for (let minimum = 0; minimum <= 100; minimum += 10)
  for (const group of ['all', 'A', 'B'])
    for (const descending of [false, true]) {
      const state = {minimum, group, descending};
      results.push({state, data: context.window.PrimerConceptModels.build('cs.3.databases', state).data});
    }
process.stdout.write(JSON.stringify(results));
"""
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True,
        timeout=15, check=True,
    )
    cases = json.loads(completed.stdout)
    assert len(cases) == 66
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("CREATE TABLE records (id INTEGER PRIMARY KEY, name TEXT, grp TEXT, score INTEGER)")
        connection.executemany("INSERT INTO records VALUES (?, ?, ?, ?)", ROWS)
        source = [dict(row) for row in connection.execute(
            'SELECT id, name, grp AS "group", score FROM records ORDER BY id'
        )]
        for case in cases:
            state = case["state"]
            order = "DESC" if state["descending"] else "ASC"
            query = ('SELECT id, name, grp AS "group", score FROM records '
                     'WHERE score >= ? AND (? = \'all\' OR grp = ?) '
                     'ORDER BY score ' + order + ', id ASC')
            expected = [dict(row) for row in connection.execute(
                query, (state["minimum"], state["group"], state["group"])
            )]
            assert case["data"]["result"] == expected, state
            assert case["data"]["rows"] == source, state
        assert connection.execute("SELECT count(*) FROM records").fetchone()[0] == 6
    finally:
        connection.close()


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_atomicity_model_matches_sqlite_commit_and_rollback():
    script = """
const fs = require('node:fs'), vm = require('node:vm');
const context = {window: {}};
vm.runInNewContext(fs.readFileSync('web/concept-models.js', 'utf8'), context);
const cases = [];
for (let amount = 0; amount <= 8; amount++)
  for (const failure of [false, true]) for (const atomic of [false, true]) {
    const state = {amount, failure, atomic};
    cases.push({state, data: context.window.PrimerConceptModels.build('cs.4.databases-adv', state).data});
  }
process.stdout.write(JSON.stringify(cases));
"""
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True,
        timeout=15, check=True,
    )
    cases = json.loads(completed.stdout)
    assert len(cases) == 36
    connection = sqlite3.connect(":memory:", isolation_level=None)
    try:
        connection.execute("CREATE TABLE counters (id TEXT PRIMARY KEY, quantity INTEGER NOT NULL)")
        for case in cases:
            state, data = case["state"], case["data"]
            connection.execute("DELETE FROM counters")
            connection.executemany("INSERT INTO counters VALUES (?, ?)", [("A", 8), ("B", 2)])
            if state["atomic"]:
                connection.execute("BEGIN")
            connection.execute("UPDATE counters SET quantity = quantity - ? WHERE id = 'A'", (state["amount"],))
            if state["failure"]:
                if state["atomic"]:
                    connection.execute("ROLLBACK")
            else:
                connection.execute("UPDATE counters SET quantity = quantity + ? WHERE id = 'B'", (state["amount"],))
                if state["atomic"]:
                    connection.execute("COMMIT")
            actual = dict(connection.execute("SELECT id, quantity FROM counters"))
            assert (data["finalA"], data["finalB"]) == (actual["A"], actual["B"]), state
            assert data["total"] == sum(actual.values()), state
            assert not connection.in_transaction
    finally:
        connection.close()
