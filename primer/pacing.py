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

BREADTH_PLANS = {
    # domains carried to graduate stage : others carried to secondary stage
    "focused": {"deep_target": 5, "wide_target": 3, "label": "Focused — a few fields, all the way"},
    "balanced": {"deep_target": 5, "wide_target": 4, "label": "Balanced — deep spine, wide shoulders"},
    "polymath": {"deep_target": 5, "wide_target": 5, "label": "Polymath — everything, everywhere"},
}


def roadmap(profile: Dict, graph: Dict, mastery: Dict[str, float]) -> Dict:
    """graph: {domains: [{id,name}], nodes: [node]} — see curriculum.py."""
    breadth = profile.get("breadth", "balanced")
    plan = BREADTH_PLANS.get(breadth, BREADTH_PLANS["balanced"])
    deep_domains = set(profile.get("domains") or [])
    hours = max(float(profile.get("hours_per_week") or 6), 1.0)
    minutes_per_year = hours * 60 * WEEKS_PER_YEAR * EFFICIENCY

    # Remaining minutes for every node not yet mastered, bucketed by stage.
    stage_buckets: List[Dict] = [
        {"stage": s, "minutes": 0.0, "nodes": 0, "domains": set()} for s in range(6)
    ]
    for node in graph["nodes"]:
        target = plan["deep_target"] if (not deep_domains or node["domain"] in deep_domains) \
            else plan["wide_target"]
        if node["stage"] > target:
            continue
        if mastery.get(node["id"], 0) >= 0.8:
            continue
        b = stage_buckets[node["stage"]]
        b["minutes"] += node.get("minutes", 40)
        b["nodes"] += 1
        b["domains"].add(node["domain"])

    # Skip stages below current placement for pacing (they're review, priced at 25%).
    current_stage = int(profile.get("stage") or 0)
    total_minutes = 0.0
    for b in stage_buckets:
        weight = 0.25 if b["stage"] < current_stage else 1.0
        total_minutes += b["minutes"] * weight

    years_total = total_minutes / minutes_per_year if minutes_per_year else 99

    # Build the year-by-year timeline.
    timeline = []
    year_start = time.time()
    minutes_left_in_year = minutes_per_year
    year_index = 1
    year_contents: List[str] = []
    for b in stage_buckets:
        weight = 0.25 if b["stage"] < current_stage else 1.0
        need = b["minutes"] * weight
        if need <= 0:
            continue
        while need > 0:
            take = min(need, minutes_left_in_year)
            frac_done = 1 - (need - take) / (b["minutes"] * weight) if b["minutes"] else 1
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

    mastered = sum(1 for v in mastery.values() if v >= 0.8)
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
        "nodes_mastered": mastered,
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
