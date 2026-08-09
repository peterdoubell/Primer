"""The curriculum graph: the Primer's spine from preschool to graduate level.

Domain files live in data/curriculum/*.json. Each node maps a concept to
Wikipedia articles, a practice generator, and optional authored quiz items.

Progression rules:
- Stage-0 nodes are always unlocked.
- A node is unlocked when its explicit prereqs are mastered AND its stage
  gate is open: 60% of the previous stage's nodes in the same domain mastered.
- Mastery of a node is recorded by the learner store (>= 0.8 level).

Beyond the authored graph lies the Vast Domain: every Wikipedia article is
reachable from node articles by links and search — reading them logs progress
and feeds the spaced-repetition deck, so the curriculum is a spine, not a cage.
"""

import json
import os
from typing import Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURRICULUM_DIR = os.path.join(ROOT, "data", "curriculum")

# Total minutes to *master* a node — spread over many sessions of reading,
# practice, quizzing and spaced review across weeks — not a single sitting.
# Higher stages cost much more, reflecting real depth: stage 0 ≈ 1.8h up to a
# graduate concept ≈ 16–17h. These feed the pacing engine, which then scopes
# the honest 5–10-year promise to the reader's hours and breadth.
# Hours a stage's node is expected to take, in minutes: [3, 6, 11, 18, 28, 45].
#
# These were previously [110, 180, 300, 480, 720, 1000] minutes, which priced the
# whole journey — preschool to graduate across ten fields — at 2,738 hours. That
# was not an estimate; it was the 5-to-10-year promise divided by a comfortable
# weekly figure and read backwards. Quantum field theory came out at 16.7 hours
# against a real two-semester sequence of roughly 350.
#
# The honest anchor is instructional time: K-12 runs about 13,000 hours, an
# undergraduate degree about 4,500, graduate coursework and reading thousands
# more. One-to-one adaptive tutoring is genuinely faster than a classroom — no
# waiting for the group, no re-teaching for the median, nothing repeated that
# the reader has already shown they know — so the Primer prices its curriculum
# at roughly a third of the classroom equivalent: 6,496 hours.
#
# That is a real number with a real consequence, which the roadmap now states
# plainly: the promise holds at 15-30 hours a week, and not at six.
DEFAULT_MINUTES = [180, 360, 660, 1080, 1680, 2700]
# Fraction of the previous stage (same domain) that must be mastered before the
# next opens. Deliberately stricter at the top: entering undergraduate work with
# 40% of secondary school unlearned is how people end up lost, so stages 4–5
# demand a much fuller foundation.
STAGE_GATE = 0.6
STAGE_GATE_BY_STAGE = {0: 0.0, 1: 0.75, 2: 0.75, 3: 0.78, 4: 0.85, 5: 0.85}


def _content_chars(node: Dict) -> int:
    """Rough proxy for how much there is to teach in a node: characters of
    authored quiz prompt/explanation/answer text, plus any kid_text lesson."""
    total = len(node.get("kid_text") or "")
    for q in node.get("quiz") or []:
        total += len(q.get("prompt", "")) + len(q.get("explain", "")) + len(q.get("answer", ""))
    return total


class Curriculum:
    def __init__(self):
        self.domains: List[Dict] = []
        self.nodes: Dict[str, Dict] = {}
        self._by_domain_stage: Dict[str, Dict[int, List[Dict]]] = {}
        self.load()

    def load(self):
        self.domains, self.nodes, self._by_domain_stage = [], {}, {}
        raw_nodes: List[Dict] = []
        for name in sorted(os.listdir(CURRICULUM_DIR)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(CURRICULUM_DIR, name), "r") as f:
                data = json.load(f)
            domain_id = data["id"]
            self.domains.append({
                "id": domain_id, "name": data["name"],
                "icon": data.get("icon", "📖"), "color": data.get("color", "#8a6d3b"),
                "tagline": data.get("tagline", ""),
                "node_count": len(data["nodes"]),
            })
            for node in data["nodes"]:
                node = dict(node)
                node["domain"] = domain_id
                node.setdefault("prereqs", [])
                node.setdefault("articles", [])
                node.setdefault("practice", None)
                node.setdefault("quiz", [])
                node.setdefault("kid_text", "")
                # Provenance, recorded once, where authored items enter the
                # app. A human wrote these: fixed prompt, fixed answer, the
                # same tomorrow as today. The generators in practice.py stamp
                # the opposite on every item they mint, so downstream code can
                # ask what an item *is* instead of guessing from how its text
                # reads — a guess that suppressed 39 durable authored items
                # ("5 + 3 = ?" is always 8; "How many sides? 🔺" is always 3)
                # because they happened to look like generated instances.
                for _q in node["quiz"]:
                    _q.setdefault("ephemeral", False)
                raw_nodes.append(node)

        # A flat per-stage default charges "Counting to 10" and "Gödel's
        # incompleteness theorems" the same minutes as every other node at
        # their stage. Nodes vary a lot in authored depth even within a
        # stage (quiz text runs 2-9x longer at the graduate end) — scale the
        # stage default by each node's own content density against its
        # stage's average, clamped so density never swings the estimate more
        # than ±50%. This is a real, measurable proxy (more explaining, more
        # worked cases, more to teach) — not an invented per-node number.
        by_stage: Dict[int, List[Dict]] = {}
        for node in raw_nodes:
            by_stage.setdefault(node["stage"], []).append(node)
        for stage, nodes in by_stage.items():
            lens = [_content_chars(n) for n in nodes]
            avg = sum(lens) / len(lens) if lens else 0
            for node, length in zip(nodes, lens):
                if "minutes" in node:
                    continue  # an explicit authored override always wins
                base = DEFAULT_MINUTES[stage]
                ratio = (length / avg) if avg else 1.0
                ratio = max(0.5, min(1.5, ratio))
                node["minutes"] = max(5, round(base * ratio / 5) * 5)

        for node in raw_nodes:
            self.nodes[node["id"]] = node
            self._by_domain_stage.setdefault(node["domain"], {}).setdefault(
                node["stage"], []).append(node)

    # ---------- queries ----------

    def graph(self) -> Dict:
        return {"domains": self.domains, "nodes": list(self.nodes.values())}

    def node(self, node_id: str) -> Optional[Dict]:
        return self.nodes.get(node_id)

    def stage_gate_open(self, domain: str, stage: int, mastery: Dict[str, float]) -> bool:
        if stage == 0:
            return True
        prev = self._by_domain_stage.get(domain, {}).get(stage - 1, [])
        if not prev:
            return True
        done = sum(1 for n in prev if mastery.get(n["id"], 0) >= 0.8)
        return done / len(prev) >= STAGE_GATE_BY_STAGE.get(stage, STAGE_GATE)

    def unlocked(self, node: Dict, mastery: Dict[str, float]) -> bool:
        for p in node["prereqs"]:
            if mastery.get(p, 0) < 0.8:
                return False
        return self.stage_gate_open(node["domain"], node["stage"], mastery)

    def unlock_requirements(self, node: Dict, mastery: Dict[str, float]) -> List[str]:
        """Human-readable list of what still stands between the reader and this
        node — so every locked tile is a legible quest marker, not a blank lock."""
        reqs = []
        for p in node["prereqs"]:
            if mastery.get(p, 0) < 0.8:
                pn = self.nodes.get(p)
                reqs.append("Master “{}”".format(pn["title"] if pn else p))
        stage = node["stage"]
        if stage > 0 and not self.stage_gate_open(node["domain"], stage, mastery):
            prev = self._by_domain_stage.get(node["domain"], {}).get(stage - 1, [])
            done = sum(1 for n in prev if mastery.get(n["id"], 0) >= 0.8)
            gate = STAGE_GATE_BY_STAGE.get(stage, STAGE_GATE)
            import math as _m
            need = max(0, _m.ceil(gate * len(prev)) - done)
            if need > 0:
                from .learner import STAGE_NAMES
                reqs.append("Master {} more {} topic{}".format(
                    need, STAGE_NAMES[stage - 1], "s" if need != 1 else ""))
        return reqs

    def annotated_graph(self, mastery: Dict[str, float]) -> Dict:
        nodes = []
        for node in self.nodes.values():
            n = dict(node)
            level = mastery.get(node["id"], 0)
            n["mastery"] = round(level, 2)
            n["mastered"] = level >= 0.8
            n["unlocked"] = self.unlocked(node, mastery)
            if not n["unlocked"] and not n["mastered"]:
                n["unlock_requirements"] = self.unlock_requirements(node, mastery)
            n.pop("quiz", None)  # keep the graph payload light
            nodes.append(n)
        domains = []
        for d in self.domains:
            stages = []
            for s in range(6):
                ns = self._by_domain_stage.get(d["id"], {}).get(s, [])
                if not ns:
                    continue
                done = sum(1 for n in ns if mastery.get(n["id"], 0) >= 0.8)
                stages.append({"stage": s, "total": len(ns), "mastered": done,
                               "open": self.stage_gate_open(d["id"], s, mastery)})
            dd = dict(d)
            dd["stages"] = stages
            dd["mastered"] = sum(1 for n in self.nodes.values()
                                 if n["domain"] == d["id"] and mastery.get(n["id"], 0) >= 0.8)
            domains.append(dd)
        return {"domains": domains, "nodes": nodes}

    def next_lessons(self, mastery: Dict[str, float], domains: Optional[List[str]] = None,
                     per_domain: int = 2) -> List[Dict]:
        """The frontier: unlocked, unmastered nodes, lowest stage first."""
        picks: List[Dict] = []
        for d in self.domains:
            if domains and d["id"] not in domains:
                continue
            count = 0
            for s in range(6):
                if count >= per_domain:
                    break
                for node in self._by_domain_stage.get(d["id"], {}).get(s, []):
                    if count >= per_domain:
                        break
                    if mastery.get(node["id"], 0) >= 0.8:
                        continue
                    if self.unlocked(node, mastery):
                        n = dict(node)
                        n["mastery"] = round(mastery.get(node["id"], 0), 2)
                        picks.append(n)
                        count += 1
        return picks

    def domain_stage_estimate(self, domain: str, mastery: Dict[str, float]) -> int:
        """Highest stage where the reader has meaningful mastery."""
        est = 0
        for s in range(6):
            ns = self._by_domain_stage.get(domain, {}).get(s, [])
            if not ns:
                continue
            done = sum(1 for n in ns if mastery.get(n["id"], 0) >= 0.8)
            if done / len(ns) >= STAGE_GATE_BY_STAGE.get(s + 1, STAGE_GATE):
                est = min(s + 1, 5)
        return est

    def seed_mastery_for_stage(self, stage: int, domains: Optional[List[str]] = None) -> List[str]:
        """Node ids below `stage` — used to credit placement results."""
        out = []
        for node in self.nodes.values():
            if domains and node["domain"] not in domains:
                continue
            if node["stage"] < stage:
                out.append(node["id"])
        return out
