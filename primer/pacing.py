"""The pacing engine: turns the curriculum into a personal roadmap.

Given the reader's age, weekly hours, and breadth of ambition, walks the
curriculum graph stage by stage and lays milestones onto a calendar. Focused
readers push their chosen domains to the graduate stage; polymaths carry more
domains further, and the plan stretches accordingly.

The five-to-ten year figure is what this computes, not what it assumes. It
holds at fifteen to thirty hours a week — the hours a real education costs.
"""

import time
from typing import Dict, List

from .learner import STAGE_NAMES, STAGE_SPAN

WEEKS_PER_YEAR = 50
EFFICIENCY = 0.85  # not every scheduled minute lands

# A node only drops out of the plan when the gates would actually treat it as
# open. The `mastery` argument must be the learner's decay-aware gate view
# (`gate_map()`), which emits exactly 1.0 for a node whose mastery is standing
# (earned or assumed, and not faded) and caps everything else below the 0.8
# gate. The old `>= 0.8` threshold also accepted `mastery_map()` — the raw EMA,
# which never decays and never distinguishes assumed from proven — so a node
# the gates had re-locked (faded, or placement credit since revoked) still
# shortened the roadmap. Plan and gates must count from the same ledger.
GATE_OPEN = 0.999

# Learning a node is not the end of paying for it: the SRS keeps billing.
# Each mastered node mints a handful of cards whose SM-2 intervals grow
# roughly geometrically, so the *lifetime* review cost per node converges —
# a saturating series, not a linear one: weekly review load grows with the
# mastered-node count early on, then flattens as old cards space out to
# months. We fold that in as a flat per-node maintenance estimate (~a dozen
# reviews at ~1 minute each over the plan's horizon). Without it, multi-year
# estimates priced only first-exposure instructional minutes and understated
# the true cost of *keeping* several thousand nodes known.
SRS_REVIEW_MIN_PER_NODE = 12.0

# ...but "a dozen reviews" is an average reader's dozen, and the two things
# that move it are both measured, not guessed. The flat figure assumed the
# baseline deck shape below; a reader whose nodes mint twice as many cards
# pays twice as many reviews, and a reader who lapses often pays for the
# ladder being knocked back down. Both come straight off the deck
# (learner.deck_stats()), so the estimate can be this reader's instead of the
# average one's.
#
# Baseline: a mastered node mints about three cards, and a healthy deck fails
# roughly one review in eight. Feeding those exact numbers in reproduces
# SRS_REVIEW_MIN_PER_NODE, which is the point — the per-reader term is a
# correction to the flat estimate, not a replacement for it, so an unmeasured
# or empty deck keeps the old number rather than jumping.
SRS_BASELINE_CARDS_PER_NODE = 3.0
SRS_BASELINE_LAPSE_RATE = 0.125
# Each lapse costs roughly a relearn plus the re-climb of the first steps —
# call it two extra reviews' worth per lapsed review, over the plan horizon.
SRS_LAPSE_WEIGHT = 2.0
# A floor and a ceiling, because this multiplies a whole curriculum. A reader
# with a tiny, pristine deck should not have maintenance priced near zero (the
# nodes they have not learned yet will mint cards too), and a reader in a bad
# patch should not have their roadmap tripled by one rough fortnight.
SRS_MIN_PER_NODE_FLOOR = 6.0
SRS_MIN_PER_NODE_CEIL = 36.0


def srs_minutes_per_node(deck: "Dict | None") -> float:
    """Per-node lifetime SRS maintenance in minutes, for this reader's deck.

    `deck` is learner.deck_stats(). Missing, empty, or ungraded decks fall
    back to the flat SRS_REVIEW_MIN_PER_NODE — "we have not measured this
    reader yet" must read as the average, never as zero.
    """
    if not deck:
        return SRS_REVIEW_MIN_PER_NODE
    per_node = float(deck.get("cards_per_node") or 0)
    graded = float(deck.get("reviews_graded") or 0)
    if per_node <= 0 and graded <= 0:
        return SRS_REVIEW_MIN_PER_NODE
    card_factor = (per_node / SRS_BASELINE_CARDS_PER_NODE) if per_node > 0 else 1.0
    lapse_rate = float(deck.get("lapse_rate") or 0) if graded > 0 else SRS_BASELINE_LAPSE_RATE
    lapse_factor = ((1 + SRS_LAPSE_WEIGHT * lapse_rate)
                    / (1 + SRS_LAPSE_WEIGHT * SRS_BASELINE_LAPSE_RATE))
    est = SRS_REVIEW_MIN_PER_NODE * card_factor * lapse_factor
    return max(SRS_MIN_PER_NODE_FLOOR, min(SRS_MIN_PER_NODE_CEIL, est))

BREADTH_PLANS = {
    # domains carried to graduate stage : others carried to secondary stage
    "focused": {"deep_target": 5, "wide_target": 3, "label": "Focused — a few fields, all the way"},
    "balanced": {"deep_target": 5, "wide_target": 4, "label": "Balanced — deep spine, wide shoulders"},
    "polymath": {"deep_target": 5, "wide_target": 5, "label": "Polymath — everything, everywhere"},
}


def roadmap(profile: Dict, graph: Dict, mastery: Dict[str, float],
            proven: "set | None" = None, deck: "Dict | None" = None) -> Dict:
    """graph: {domains: [{id,name}], nodes: [node]} — see curriculum.py.

    `mastery` must be the learner's decay-aware gate view (gate_map()), not
    the raw EMA mastery_map() — see GATE_OPEN above.

    `proven`, when given, is the learner's proven_set(): nodes mastered by
    spaced performance rather than placement credit. gate_map() emits an
    identical 1.0 for both, so from `mastery` alone this function cannot
    tell a node the reader demonstrated from one the placement interview
    merely assumed — and a headline that counts them identically overstates
    what has been shown. Passing the set splits the headline (see
    `nodes_proven` / `nodes_assumed` below) without changing anything the
    plan schedules; omitting it keeps the old shape working and leaves the
    split fields None, meaning "caller didn't say", never "zero".

    `deck`, when given, is the learner's deck_stats(): the maintenance term
    folded into every remaining node is then priced from this reader's own
    card count per node and observed lapse rate rather than from the flat
    average (see srs_minutes_per_node). Optional for the same reason `proven`
    is — omitting it keeps the old numbers exactly, and the figure used is
    reported as `srs_minutes_per_node` so the estimate can be audited instead
    of taken on faith.

    `profile["settings"]["domain_stage"]`, when present, prices the 25%
    review discount below per node against *that node's own domain's*
    placed level rather than one scalar shared by every field the reader
    chose — a domain never set here still falls back to `profile["stage"]`,
    so a reader who has never touched the sliders sees exactly the old
    numbers.
    """
    breadth = profile.get("breadth", "balanced")
    plan = BREADTH_PLANS.get(breadth, BREADTH_PLANS["balanced"])
    deep_domains = set(profile.get("domains") or [])
    hours = max(float(profile.get("hours_per_week") or 6), 1.0)
    minutes_per_year = hours * 60 * WEEKS_PER_YEAR * EFFICIENCY
    srs_per_node = srs_minutes_per_node(deck)
    domain_stage = (profile.get("settings") or {}).get("domain_stage") or {}
    current_stage = int(profile.get("stage") or 0)

    # Remaining minutes for every node not yet mastered, bucketed by stage.
    # `minutes` stays the raw, undiscounted total (the "stages" field below
    # reports real hours left, not a paced estimate); `weighted_minutes` is
    # the same total with each node's own review discount already applied,
    # since that discount is no longer uniform within a bucket once it can
    # vary by domain.
    stage_buckets: List[Dict] = [
        {"stage": s, "minutes": 0.0, "weighted_minutes": 0.0, "nodes": 0, "domains": set()}
        for s in range(6)
    ]
    for node in graph["nodes"]:
        target = plan["deep_target"] if (not deep_domains or node["domain"] in deep_domains) \
            else plan["wide_target"]
        if node["stage"] > target:
            continue
        # Only a gate-open node (exactly 1.0 from gate_map) leaves the plan —
        # a faded or merely-high-EMA node is still work to be scheduled.
        if mastery.get(node["id"], 0) >= GATE_OPEN:
            continue
        b = stage_buckets[node["stage"]]
        # Instructional minutes plus the node's lifetime SRS maintenance —
        # see SRS_REVIEW_MIN_PER_NODE. Folding it in here keeps the years,
        # the timeline, and the per-stage hours all telling the same story.
        node_minutes = node.get("minutes", 40) + srs_per_node
        # Skipped for pacing (it's review, priced at 25%) once this domain's
        # own placed level has passed the node's stage.
        reader_stage_here = domain_stage.get(node["domain"], current_stage)
        weight = 0.25 if node["stage"] < reader_stage_here else 1.0
        b["minutes"] += node_minutes
        b["weighted_minutes"] += node_minutes * weight
        b["nodes"] += 1
        b["domains"].add(node["domain"])

    total_minutes = sum(b["weighted_minutes"] for b in stage_buckets)
    years_total = total_minutes / minutes_per_year if minutes_per_year else 99

    # Build the year-by-year timeline.
    timeline = []
    year_start = time.time()
    minutes_left_in_year = minutes_per_year
    year_index = 1
    year_contents: List[str] = []
    for b in stage_buckets:
        need = b["weighted_minutes"]
        if need <= 0:
            continue
        while need > 0:
            take = min(need, minutes_left_in_year)
            frac_done = 1 - (need - take) / b["weighted_minutes"] if b["weighted_minutes"] else 1
            need -= take
            minutes_left_in_year -= take
            label = "{} ({})".format(STAGE_NAMES[b["stage"]], STAGE_SPAN[b["stage"]])
            entry = label if frac_done >= 0.999 else "{} — reach {:.0%}".format(label, frac_done)
            if not year_contents or not year_contents[-1].startswith(label):
                year_contents.append(entry)
            else:
                year_contents[-1] = entry
            if minutes_left_in_year <= 0:
                timeline.append({"year": year_index, "milestones": year_contents})
                year_index += 1
                year_contents = []
                minutes_left_in_year = minutes_per_year
            if year_index > 15:
                break
        if year_index > 15:
            break
    if year_contents:
        timeline.append({"year": year_index, "milestones": year_contents})

    # Same ledger as the scheduling loop above: gate-open only, so a faded or
    # revoked node is never headlined as mastered while the gates re-lock it.
    mastered = sum(1 for v in mastery.values() if v >= GATE_OPEN)
    # Split the headline where the caller lets us. A gate-open node is either
    # proven (spaced performance) or assumed (placement credit not yet
    # tested); collapsing the two into one number let the roadmap claim
    # placement guesses as accomplishments. `nodes_mastered` keeps its old
    # meaning — everything the gates treat as standing — so no consumer
    # breaks; the new fields carry the honest decomposition.
    if proven is not None:
        proven_open = sum(1 for n, v in mastery.items()
                          if v >= GATE_OPEN and n in proven)
        nodes_proven: "int | None" = proven_open
        nodes_assumed: "int | None" = mastered - proven_open
    else:
        nodes_proven = nodes_assumed = None
    return {
        "breadth": breadth,
        "breadth_label": plan["label"],
        "hours_per_week": hours,
        "estimated_years": round(max(years_total, 0.1), 1),
        # An observation about the plan, not a constraint on it. The constants
        # this falls out of are anchored to instructional time; if the answer is
        # twenty-five years at six hours a week, the book says twenty-five years.
        "within_promise": 5 <= years_total <= 10,
        "hours_for_ten_years": round(total_minutes / (10 * WEEKS_PER_YEAR * 60 * EFFICIENCY), 1),
        "hours_for_five_years": round(total_minutes / (5 * WEEKS_PER_YEAR * 60 * EFFICIENCY), 1),
        "total_hours": round(total_minutes / 60),
        "note": _pace_note(years_total, hours, total_minutes),
        "timeline": timeline[:12],
        "stages": [
            {
                "stage": b["stage"],
                "name": STAGE_NAMES[b["stage"]],
                "span": STAGE_SPAN[b["stage"]],
                "nodes_remaining": b["nodes"],
                "hours_remaining": round(b["minutes"] / 60, 1),
            }
            for b in stage_buckets if b["nodes"]
        ],
        "srs_minutes_per_node": round(srs_per_node, 1),
        "nodes_mastered": mastered,
        "nodes_proven": nodes_proven,
        "nodes_assumed": nodes_assumed,
        "nodes_total": len(graph["nodes"]),
    }


def _pace_note(years: float, hours: float, total_minutes: float) -> str:
    """What the plan actually costs, in the reader's own terms.

    This used to reassure at six hours a week. It shouldn't have: an education
    is a serious number of hours, and a plan that hides that is not a plan.
    """
    for_ten = total_minutes / (10 * WEEKS_PER_YEAR * 60 * EFFICIENCY)
    for_five = total_minutes / (5 * WEEKS_PER_YEAR * 60 * EFFICIENCY)
    if years < 5:
        return ("About {:.1f} years at {:.0f} hours a week — quicker than the "
                "book's five-year mark, so there is room to carry more fields "
                "further, or to go deeper into the frontier reading. The whole "
                "plan as it stands is {:,} hours."
                ).format(years, hours, round(total_minutes / 60))
    if years <= 10:
        return ("About {:.1f} years at {:.0f} hours a week, inside the Primer's "
                "five-to-ten year promise. That is {:,} hours of real work."
                ).format(years, hours, round(total_minutes / 60))
    return ("At {:.0f} hours a week this comes to about {:.1f} years — the whole "
            "plan is {:,} hours. Ten years needs {:.0f} hours a week, five needs "
            "{:.0f}. Fewer fields, or fields carried less far, brings both down."
            ).format(hours, years, round(total_minutes / 60), for_ten, for_five)
