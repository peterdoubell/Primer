"""The curriculum graph: the Primer's spine from preschool to graduate level.

Domain files live in data/curriculum/*.json. Each node maps a concept to
Wikipedia articles, a practice generator, and optional authored quiz items.

Assessment design — why most nodes have `practice: null`. The authored quiz
banks are the assessment spine: every node carries human-written items, and
mastery is earned against those. Procedural generators (practice.py) exist
only where a concept is a *mechanical skill* with a parameterisable item
space — arithmetic, counting, unit conversion, algebraic manipulation and
their kin — which is why the ~41 nodes that have one skew heavily toward the
mechanical strands of math, language and CS. Conceptual nodes
("Gödel's incompleteness theorems") do not decompose into templates
a generator could mint honestly; a generated item there would test pattern-
matching on the template, not the concept. So generators *supplement* the
spine with unlimited drill where drill is the right instrument, and their
absence on a node is a design statement, not missing coverage.

Two more deliberate asymmetries in the data files, recorded here because JSON
cannot carry comments:

- `kid_text` exists only for stage 0-1 nodes. It is the read-aloud lesson
  voice for pre-readers and early readers (ages 3-9). From stage 2 up the
  reader works from the linked articles themselves — learning to read the
  real literature is part of the curriculum, so a simplified shadow text
  would work against the goal, not toward it.
- Domain node counts are uneven by design (math 59, arts 25). Node count
  tracks how much *gated, sequential* structure a field has, not how big or
  worthy the field is: mathematics is a long dependency chain where each rung
  must be held before the next, while arts and earth science branch shallow
  and wide, so fewer spine nodes carry the same breadth — the taglines
  promise the field, and the Vast Domain (below) supplies its breadth beyond
  the spine.

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
ILLUSTRATION_ROOT = os.path.join(ROOT, "web", "illustrations")


def _webp_dimensions(path: str):
    """Read dimensions from the small WebP header without an image dependency."""
    with open(path, "rb") as image:
        header = image.read(30)
    if len(header) < 25 or header[:4] != b"RIFF" or header[8:12] != b"WEBP":
        raise ValueError("lesson illustration is not a WebP: {}".format(path))
    chunk = header[12:16]
    if chunk == b"VP8X" and len(header) >= 30:
        width = 1 + int.from_bytes(header[24:27], "little")
        height = 1 + int.from_bytes(header[27:30], "little")
    elif chunk == b"VP8 " and len(header) >= 30 and header[23:26] == b"\x9d\x01\x2a":
        width = int.from_bytes(header[26:28], "little") & 0x3FFF
        height = int.from_bytes(header[28:30], "little") & 0x3FFF
    elif chunk == b"VP8L" and header[20] == 0x2F:
        packed = int.from_bytes(header[21:25], "little")
        width = 1 + (packed & 0x3FFF)
        height = 1 + ((packed >> 14) & 0x3FFF)
    else:
        raise ValueError("lesson illustration has an unsupported WebP header: {}".format(path))
    if width <= 0 or height <= 0:
        raise ValueError("lesson illustration has invalid dimensions: {}".format(path))
    return width, height


def _discover_lesson_illustrations():
    """Build URL metadata from the trusted static tree, never authored input."""
    images = {}
    for directory, _, filenames in os.walk(ILLUSTRATION_ROOT):
        for filename in filenames:
            if not filename.endswith(".webp"):
                continue
            disk_path = os.path.join(directory, filename)
            relative = os.path.relpath(disk_path, ILLUSTRATION_ROOT).replace(os.sep, "/")
            images["/app/illustrations/" + relative] = _webp_dimensions(disk_path)
    return images


LESSON_ILLUSTRATION_DIMENSIONS = _discover_lesson_illustrations()
LESSON_ILLUSTRATION_URLS = frozenset(LESSON_ILLUSTRATION_DIMENSIONS)

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
LESSON_MODEL_RENDERERS = frozenset({
    "counter", "shape-explorer", "shadow-lab", "sequence-runner",
    "make-ten", "light-paths", "algorithm-tracer", "life-cycle",
    "fraction-equivalence-lab", "atom-element-builder", "cell-microscope",
    "counterexample-lab", "function-composition-lab", "circulation-route-lab",
    "truth-table-lab", "stack-queue-lab", "matrix-transform-lab",
    "venturi-flow-lab", "gene-expression-stepper", "tcp-packet-tracer",
    "heat-equation-lab", "complexity-certificate-lab",
    "morphogen-gradient-lab", "ct-window-lab",
    "alphabet-explorer", "inclusive-family-timeline",
    "day-night-rotation-lab", "classroom-paint-mixer",
    "reading-path-lab", "timeline-order-lab", "seasons-tilt-lab",
    "art-elements-composer", "integer-number-line-lab", "physics-concept-lab",
})

# These scenarios intentionally exclude the three physics lessons with bespoke
# renderers.  A scenario is bound to the matching node id below, so authored
# curriculum data cannot silently reuse a scientific model in the wrong lesson.
PHYSICS_MODEL_SCENARIOS = frozenset({
    "phys.0.push-pull", "phys.0.hot-cold", "phys.0.float-sink",
    "phys.1.motion", "phys.1.machines", "phys.1.magnets", "phys.1.sound",
    "phys.1.energy", "phys.2.forces", "phys.2.gravity", "phys.2.electricity",
    "phys.2.heat", "phys.2.waves", "phys.2.matter", "phys.2.units",
    "phys.3.mechanics", "phys.3.energy-work", "phys.3.em",
    "phys.3.optics-waves", "phys.3.thermo", "phys.3.nuclear",
    "phys.3.relativity-intro", "phys.3.modern", "phys.4.classical",
    "phys.4.em-maxwell", "phys.4.quantum", "phys.4.statmech",
    "phys.4.relativity", "phys.4.solid-state", "phys.4.particles",
    "phys.4.experiment", "phys.5.qft", "phys.5.gr-cosmo",
    "phys.5.condensed", "phys.5.quantum-info", "phys.5.frontier",
})


def _validate_lesson_media(node: Dict) -> None:
    """Fail closed when authored lesson media does not match its small schema.

    Media is executable UI at the last inch of the pipeline. Keeping the
    curriculum format deliberately narrow prevents a future data edit from
    smuggling HTML, remote URLs, or an unbounded renderer into that UI.
    """
    media = node.get("lesson_media", [])
    if not isinstance(media, list):
        raise ValueError("{} lesson_media must be a list".format(node.get("id")))
    seen = set()
    illustration_keys = {"id", "kind", "src", "srcset", "alt", "caption", "width", "height"}
    model_keys = {"id", "kind", "renderer", "title", "instructions", "props"}
    static_prefix = "/app/illustrations/"

    def text(entry: Dict, key: str) -> str:
        value = entry.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("{} lesson media {} needs {}".format(node.get("id"), entry.get("id"), key))
        return value

    def local_image(path: str):
        if not path.startswith(static_prefix) or not path.endswith(".webp"):
            raise ValueError("{} lesson image must be a local WebP".format(node.get("id")))
        # The requested value is compared with a manifest produced solely from
        # the trusted illustration directory above. It never participates in
        # a filesystem expression, so traversal and arbitrary-file probes are
        # impossible even if this validator is reused with untrusted data.
        if path not in LESSON_ILLUSTRATION_URLS:
            raise ValueError("{} lesson image is not in the illustration manifest: {}".format(
                node.get("id"), path))
        return LESSON_ILLUSTRATION_DIMENSIONS[path]

    for entry in media:
        if not isinstance(entry, dict):
            raise ValueError("{} lesson media entries must be objects".format(node.get("id")))
        media_id = text(entry, "id")
        if media_id in seen:
            raise ValueError("{} repeats lesson media id {}".format(node.get("id"), media_id))
        seen.add(media_id)
        kind = entry.get("kind")
        if kind == "illustration":
            if set(entry) != illustration_keys:
                raise ValueError("{} illustration {} has unexpected fields".format(node.get("id"), media_id))
            source = text(entry, "src")
            local_image(source)
            if any(isinstance(entry.get(key), bool) or not isinstance(entry.get(key), int)
                   or entry[key] <= 0 for key in ("width", "height")):
                raise ValueError("{} illustration {} needs positive integer dimensions".format(node.get("id"), media_id))
            widths = set()
            sources = set()
            for candidate in text(entry, "srcset").split(","):
                parts = candidate.strip().split()
                if len(parts) != 2 or not parts[1].endswith("w") or not parts[1][:-1].isdigit():
                    raise ValueError("{} illustration {} has an invalid srcset".format(node.get("id"), media_id))
                width = int(parts[1][:-1])
                if width <= 0 or width in widths:
                    raise ValueError("{} illustration {} has an invalid srcset".format(node.get("id"), media_id))
                widths.add(width)
                sources.add(parts[0])
                actual_width, actual_height = local_image(parts[0])
                if actual_width != width or actual_width * entry["height"] != actual_height * entry["width"]:
                    raise ValueError("{} illustration {} has an invalid srcset".format(node.get("id"), media_id))
            if source not in sources:
                raise ValueError("{} illustration {} src is missing from srcset".format(node.get("id"), media_id))
            text(entry, "alt")
            text(entry, "caption")
        elif kind == "model":
            if set(entry) != model_keys:
                raise ValueError("{} model {} has unexpected fields".format(node.get("id"), media_id))
            renderer = text(entry, "renderer")
            if renderer not in LESSON_MODEL_RENDERERS:
                raise ValueError("{} model {} has unknown renderer {}".format(node.get("id"), media_id, renderer))
            text(entry, "title")
            text(entry, "instructions")
            props = entry.get("props")
            if not isinstance(props, dict):
                raise ValueError("{} model {} props must be an object".format(node.get("id"), media_id))
            if renderer == "counter":
                if set(props) != {"total"} or isinstance(props.get("total"), bool) \
                        or not isinstance(props.get("total"), int) or not 1 <= props["total"] <= 20:
                    raise ValueError("{} counter model needs total 1..20".format(node.get("id")))
            elif renderer == "shape-explorer" and props:
                raise ValueError("{} shape explorer takes no props".format(node.get("id")))
            elif renderer == "shadow-lab":
                start = props.get("start_position")
                if set(props) != {"start_position"} or isinstance(start, bool) \
                        or not isinstance(start, int) or not 0 <= start <= 100:
                    raise ValueError("{} shadow lab needs start_position 0..100".format(node.get("id")))
            elif renderer == "sequence-runner":
                if props != {"scenario": "pack-bag"}:
                    raise ValueError("{} sequence runner has an unknown scenario".format(node.get("id")))
            elif renderer == "make-ten":
                if set(props) != {"first", "second"} or any(
                        isinstance(props.get(key), bool) or not isinstance(props.get(key), int)
                        or not 1 <= props[key] <= 9 for key in ("first", "second")) \
                        or not 11 <= props["first"] + props["second"] <= 18:
                    raise ValueError("{} make-ten model needs two addends 1..9 with a sum 11..18".format(
                        node.get("id")))
            elif renderer in {"light-paths", "life-cycle"} and props:
                raise ValueError("{} {} model takes no props".format(node.get("id"), renderer))
            elif renderer == "algorithm-tracer":
                if props != {"scenario": "jam-sandwich"}:
                    raise ValueError("{} algorithm tracer has an unknown scenario".format(node.get("id")))
            elif renderer == "fraction-equivalence-lab":
                keys = {"numerator", "denominator", "max_factor"}
                if set(props) != keys or any(
                        isinstance(props.get(key), bool) or not isinstance(props.get(key), int)
                        for key in keys) or not 2 <= props["denominator"] <= 8 \
                        or not 1 <= props["numerator"] < props["denominator"] \
                        or not 2 <= props["max_factor"] <= 4 \
                        or props["denominator"] * props["max_factor"] > 24:
                    raise ValueError("{} fraction equivalence lab needs a bounded proper fraction".format(
                        node.get("id")))
            elif renderer == "atom-element-builder":
                keys = {"protons", "neutrons", "electrons"}
                if set(props) != keys or any(
                        isinstance(props.get(key), bool) or not isinstance(props.get(key), int)
                        for key in keys) or not 1 <= props["protons"] <= 10 \
                        or not 0 <= props["neutrons"] <= 12 \
                        or not 0 <= props["electrons"] <= 10 \
                        or abs(props["protons"] - props["electrons"]) > 2:
                    raise ValueError("{} atom builder needs bounded particle counts".format(node.get("id")))
            elif renderer == "cell-microscope":
                magnification = props.get("start_magnification")
                if set(props) != {"start_specimen", "start_magnification"} \
                        or props.get("start_specimen") not in {"onion", "leaf", "cheek"} \
                        or isinstance(magnification, bool) or not isinstance(magnification, int) \
                        or magnification not in {40, 100, 400}:
                    raise ValueError("{} cell microscope has unknown starting settings".format(node.get("id")))
            elif renderer == "counterexample-lab":
                if props != {"scenario": "squares-and-rectangles"}:
                    raise ValueError("{} counterexample lab has an unknown scenario".format(node.get("id")))
            elif renderer == "integer-number-line-lab":
                expected = {
                    "min": -12, "max": 12,
                    "start_value": -2, "start_delta": -7,
                }
                integer_keys = {"min", "max", "start_value", "start_delta"}
                if props != expected or set(props) != integer_keys \
                        or any(type(props.get(key)) is not int for key in integer_keys) \
                        or not props["min"] < props["max"] \
                        or not props["min"] <= props["start_value"] <= props["max"] \
                        or not props["min"] <= props["start_value"] + props["start_delta"] <= props["max"]:
                    raise ValueError("{} integer number line lab has unknown settings".format(
                        node.get("id")))
            elif renderer == "function-composition-lab":
                keys = {
                    "f_slope", "f_intercept", "g_slope", "g_intercept",
                    "x_min", "x_max", "start_x",
                }
                if set(props) != keys or any(
                        isinstance(props.get(key), bool) or not isinstance(props.get(key), int)
                        for key in keys) or any(
                        props[key] == 0 or not -3 <= props[key] <= 3
                        for key in ("f_slope", "g_slope")) or any(
                        not -5 <= props[key] <= 5
                        for key in ("f_intercept", "g_intercept")) \
                        or not -8 <= props["x_min"] < props["x_max"] <= 8 \
                        or not props["x_min"] <= props["start_x"] <= props["x_max"]:
                    raise ValueError("{} function composition lab needs bounded integer rules".format(
                        node.get("id")))
            elif renderer == "circulation-route-lab":
                start_step = props.get("start_step")
                if set(props) != {"route", "start_step", "show_oxygenation"} \
                        or props.get("route") != "cardiopulmonary" \
                        or isinstance(start_step, bool) or not isinstance(start_step, int) \
                        or not 0 <= start_step <= 8 \
                        or not isinstance(props.get("show_oxygenation"), bool):
                    raise ValueError("{} circulation route lab has unknown starting settings".format(
                        node.get("id")))
            elif renderer == "truth-table-lab":
                if set(props) != {"start_operator", "start_p", "start_q"} \
                        or props.get("start_operator") not in {"and", "or", "implies"} \
                        or not isinstance(props.get("start_p"), bool) \
                        or not isinstance(props.get("start_q"), bool):
                    raise ValueError("{} truth table lab has unknown starting settings".format(
                        node.get("id")))
            elif renderer == "stack-queue-lab":
                capacity = props.get("capacity")
                initial_count = props.get("initial_count")
                if set(props) != {"start_mode", "capacity", "initial_count"} \
                        or props.get("start_mode") not in {"stack", "queue"} \
                        or isinstance(capacity, bool) or not isinstance(capacity, int) \
                        or not 3 <= capacity <= 8 \
                        or isinstance(initial_count, bool) or not isinstance(initial_count, int) \
                        or not 0 <= initial_count <= capacity:
                    raise ValueError("{} stack and queue lab has unknown starting settings".format(
                        node.get("id")))
            elif renderer == "matrix-transform-lab":
                if set(props) != {"start_transform"} or props.get("start_transform") not in {
                        "identity", "x-stretch", "x-shear", "y-reflection", "x-projection"}:
                    raise ValueError("{} matrix transform lab has an unknown starting transform".format(
                        node.get("id")))
            elif renderer == "venturi-flow-lab":
                if set(props) != {"scenario", "start_throat"} \
                        or props.get("scenario") != "horizontal-water-venturi" \
                        or props.get("start_throat") not in {"full-area", "half-area", "quarter-area"}:
                    raise ValueError("{} Venturi flow lab has unknown starting settings".format(
                        node.get("id")))
            elif renderer == "gene-expression-stepper":
                if set(props) != {"scenario", "start_gene_state"} \
                        or props.get("scenario") != "eukaryotic-met-glu-phe" \
                        or props.get("start_gene_state") not in {"off", "on"}:
                    raise ValueError("{} gene expression stepper has unknown starting settings".format(
                        node.get("id")))
            elif renderer == "tcp-packet-tracer":
                if props != {"scenario": "tcp-four-segment-loss-two"}:
                    raise ValueError("{} TCP packet tracer has an unknown scenario".format(
                        node.get("id")))
            elif renderer == "heat-equation-lab":
                expected = {
                    "cells": 9, "hot_cell": 4, "diffusion_percent": 20,
                    "max_steps": 10,
                }
                if props != expected or any(
                        type(props.get(key)) is not int for key in expected):
                    raise ValueError("{} heat equation lab has unknown settings".format(
                        node.get("id")))
            elif renderer == "complexity-certificate-lab":
                expected = {
                    "scenario": "sat-certificate", "start_n": 4, "max_n": 20,
                }
                if props != expected or any(
                        type(props.get(key)) is not int for key in ("start_n", "max_n")):
                    raise ValueError("{} complexity certificate lab has unknown settings".format(
                        node.get("id")))
            elif renderer == "morphogen-gradient-lab":
                expected = {
                    "cells": 11, "source": 100, "decay_percent": 20,
                    "low_threshold": 30, "high_threshold": 65,
                }
                if props != expected or any(
                        type(props.get(key)) is not int for key in expected):
                    raise ValueError("{} morphogen gradient lab has unknown settings".format(
                        node.get("id")))
            elif renderer == "ct-window-lab":
                expected = {
                    "phantom": "synthetic-hu-reference", "level": 40, "width": 400,
                }
                if props != expected or any(
                        type(props.get(key)) is not int for key in ("level", "width")):
                    raise ValueError("{} CT window lab has unknown settings".format(
                        node.get("id")))
            elif renderer == "alphabet-explorer":
                start_letter = props.get("start_letter")
                if set(props) != {"alphabet", "start_letter", "example_set"} \
                        or props.get("alphabet") != "english-basic-latin" \
                        or props.get("example_set") != "common-words-v1" \
                        or not isinstance(start_letter, str) or len(start_letter) != 1 \
                        or not "A" <= start_letter <= "Z":
                    raise ValueError("{} alphabet explorer has unknown settings".format(
                        node.get("id")))
            elif renderer == "inclusive-family-timeline":
                if props != {
                        "scenario": "fictional-family-three-times", "start_time": "today"}:
                    raise ValueError("{} inclusive family timeline has unknown settings".format(
                        node.get("id")))
            elif renderer == "day-night-rotation-lab":
                start_hour = props.get("start_hour")
                step_hours = props.get("step_hours")
                if set(props) != {"scenario", "start_hour", "step_hours"} \
                        or props.get("scenario") != "earth-rotation-equinox-equator" \
                        or type(start_hour) is not int or start_hour not in {0, 6, 12, 18} \
                        or type(step_hours) is not int or step_hours != 6:
                    raise ValueError("{} day and night rotation lab has unknown settings".format(
                        node.get("id")))
            elif renderer == "classroom-paint-mixer":
                colors = {"red", "yellow", "blue", "white"}
                first = props.get("start_first")
                second = props.get("start_second")
                if set(props) != {"scenario", "start_first", "start_second"} \
                        or props.get("scenario") != "equal-parts-classroom-ryb" \
                        or not isinstance(first, str) or first not in colors \
                        or not isinstance(second, str) or second not in colors:
                    raise ValueError("{} classroom paint mixer has unknown settings".format(
                        node.get("id")))
            elif renderer == "reading-path-lab":
                start_phase = props.get("start_phase")
                if set(props) != {"scenario", "start_phase"} \
                        or props.get("scenario") != "simple-english-cat-sat" \
                        or not isinstance(start_phase, str) \
                        or start_phase not in {"sounds", "blend", "sentence", "meaning"}:
                    raise ValueError("{} reading path lab has unknown settings".format(
                        node.get("id")))
            elif renderer == "timeline-order-lab":
                start_order = props.get("start_order")
                event_ids = {"roof-restored", "opened", "reading-room"}
                if set(props) != {"scenario", "start_order"} \
                        or props.get("scenario") != "fictional-library-three-dates" \
                        or not isinstance(start_order, list) or len(start_order) != 3 \
                        or any(not isinstance(event_id, str) for event_id in start_order) \
                        or set(start_order) != event_ids:
                    raise ValueError("{} timeline order lab has unknown settings".format(
                        node.get("id")))
            elif renderer == "seasons-tilt-lab":
                start_position = props.get("start_position")
                start_hemisphere = props.get("start_hemisphere")
                if set(props) != {"scenario", "start_position", "start_hemisphere"} \
                        or props.get("scenario") != "earth-tilt-four-positions" \
                        or not isinstance(start_position, str) \
                        or start_position not in {
                            "march-equinox", "june-solstice",
                            "september-equinox", "december-solstice",
                        } \
                        or not isinstance(start_hemisphere, str) \
                        or start_hemisphere not in {"north", "south"}:
                    raise ValueError("{} seasons tilt lab has unknown settings".format(
                        node.get("id")))
            elif renderer == "art-elements-composer":
                start_elements = props.get("start_elements")
                allowed_elements = {"line", "shape", "color", "texture", "pattern"}
                if set(props) != {"scenario", "start_elements"} \
                        or props.get("scenario") != "garden-five-elements" \
                        or not isinstance(start_elements, list) or not start_elements \
                        or any(not isinstance(element, str) or element not in allowed_elements
                               for element in start_elements) \
                        or len(start_elements) != len(set(start_elements)):
                    raise ValueError("{} art elements composer has unknown settings".format(
                        node.get("id")))
            elif renderer == "physics-concept-lab":
                scenario = props.get("scenario")
                if set(props) != {"scenario"} or not isinstance(scenario, str) \
                        or scenario not in PHYSICS_MODEL_SCENARIOS \
                        or scenario != node.get("id"):
                    raise ValueError("{} physics concept lab has an unknown or cross-lesson scenario".format(
                        node.get("id")))
        else:
            raise ValueError("{} lesson media {} has unknown kind".format(node.get("id"), media_id))


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
        self._domain_by_article: Dict[str, str] = {}
        raw_nodes: List[Dict] = []
        for name in sorted(os.listdir(CURRICULUM_DIR)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(CURRICULUM_DIR, name), "r") as f:
                data = json.load(f)
            domain_id = data["id"]
            self.domains.append({
                "id": domain_id, "name": data["name"],
                "icon": data.get("icon", "✦"), "color": data.get("color", "#4a6fa5"),
                "tagline": data.get("tagline", ""),
                "node_count": len(data["nodes"]),
                # The stage a domain starts at. The ten general fields start at
                # 0 and run the whole book, which is what makes them fields a
                # reader travels rather than subjects they are handed. A
                # specialist domain declares a later entry and begins where the
                # general spine ends — radiology is postgraduate by nature, and
                # preschool radiology is not a thing anyone should invent to
                # satisfy a structural rule. The stage gate already allows this:
                # stage_gate_open returns True when the previous stage is empty,
                # so entry is governed by the cross-domain prereqs the nodes
                # declare, not by a ladder that does not exist.
                "entry_stage": int(data.get("entry_stage", 0)),
            })
            for node in data["nodes"]:
                node = dict(node)
                node["domain"] = domain_id
                node.setdefault("prereqs", [])
                node.setdefault("articles", [])
                node.setdefault("practice", None)
                node.setdefault("quiz", [])
                # A specialist field is a reference work, not a ladder: its
                # modules are peers, so the only order they have is the one a
                # section heading gives them. The ten general fields need none
                # — their stages ARE their filing — and leave this empty.
                node.setdefault("section", "")
                node.setdefault("kid_text", "")
                node.setdefault("lesson_media", [])
                _validate_lesson_media(node)
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
            # First node to claim an article, in book order, decides which
            # domain that article's reading level is judged by. An article
            # can be linked from more than one node — occasionally across
            # domains — and ties have to resolve somehow rather than
            # silently taking whichever loaded last.
            for title in node.get("articles") or []:
                self._domain_by_article.setdefault(title, node["domain"])

        # Titles are unique within a domain but not across the graph —
        # math.3.functions and cs.2.functions are both just "Functions".
        # unlock_requirements() names prereqs by title, so it needs to know
        # which titles are ambiguous in order to qualify them with a domain.
        self._title_counts: Dict[str, int] = {}
        for node in raw_nodes:
            t = node.get("title", "")
            self._title_counts[t] = self._title_counts.get(t, 0) + 1
        self._domain_names = {d["id"]: d["name"] for d in self.domains}

    # ---------- queries ----------

    def graph(self) -> Dict:
        return {"domains": self.domains, "nodes": list(self.nodes.values())}

    def node(self, node_id: str) -> Optional[Dict]:
        return self.nodes.get(node_id)

    def domain_for_article(self, title: str) -> Optional[str]:
        """Which domain's reading level should judge this article, if any
        curriculum node actually links it — see load()'s index."""
        return self._domain_by_article.get(title)

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
                if pn is None:
                    reqs.append("Master “{}”".format(p))
                    continue
                # A bare title is only a legible quest marker if it points at
                # exactly one tile the reader can find. Two cases break that:
                # the prereq lives in another domain (the reader is looking at
                # a math tile; "Functions" won't be found under math), and a
                # title that appears on more than one node anywhere in the
                # graph ("Functions" is both math.3 and cs.2 — the reader can
                # land on the wrong one and wonder why mastering it changed
                # nothing). Both get the domain name spelled out.
                title = pn["title"]
                if (pn["domain"] != node["domain"]
                        or self._title_counts.get(title, 0) > 1):
                    title = "{} ({})".format(
                        title, self._domain_names.get(pn["domain"], pn["domain"]))
                reqs.append("Master “{}”".format(title))
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
            n.pop("lesson_media", None)  # detail-only; plates and model copy are much larger
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
