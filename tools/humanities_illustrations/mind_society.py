"""Lesson-specific explanatory plates for Mind, Society & Philosophy."""

from __future__ import annotations

import math
from typing import Dict, Sequence, Tuple

from .core import (
    BLUE,
    BLUE_LIGHT,
    CORAL,
    CORAL_LIGHT,
    GOLD,
    GOLD_LIGHT,
    GREEN,
    GREEN_LIGHT,
    GRID,
    INK,
    INK_SOFT,
    PAPER_LIGHT,
    PLUM,
    PLUM_LIGHT,
    TEAL,
    TEAL_LIGHT,
    Plate,
    Spec,
    box_text,
    draw_branch,
    draw_comparison,
    draw_cycle,
    draw_evidence,
    draw_flow,
    draw_matrix,
    draw_network,
    draw_timeline,
    footer,
    panel,
    pill,
    spec,
)


DOMAIN = "mind-society"


def flow(node_id: str, title: str, stage: int, plate_id: str, alt: str,
         caption: str, steps: Sequence[Tuple[str, str]], conclusion: str) -> Spec:
    return spec(node_id, title, stage, DOMAIN, plate_id, alt, caption,
                lambda plate: draw_flow(plate, steps, conclusion))


def compare(node_id: str, title: str, stage: int, plate_id: str, alt: str,
            caption: str, columns: Sequence[Tuple[str, str, str]], conclusion: str,
            relation: str = "COMPARE THE SAME QUESTION") -> Spec:
    return spec(node_id, title, stage, DOMAIN, plate_id, alt, caption,
                lambda plate: draw_comparison(
                    plate, columns, conclusion, relation=relation))


def _draw_feelings(plate: Plate) -> None:
    draw_comparison(
        plate,
        [
            ("SAM AT A NEW SCHOOL", "Fast heartbeat + thought ‘I might get lost’ → names NERVOUS.",
             "Response: ask a teacher for the room number"),
            ("LEE AT A NEW SCHOOL", "Wide eyes + thought ‘I get to explore’ → names EXCITED.",
             "Response: invite Sam to find the room together"),
        ],
        "The same situation can prompt different feelings; clues help us ask, not assume.",
        relation="SAME SITUATION → DIFFERENT BODY CLUES, THOUGHTS AND FEELINGS",
    )


def _draw_fairness(plate: Plate) -> None:
    panel(plate, (120, 240, 535, 770), fill=BLUE_LIGHT, outline=BLUE)
    pill(plate, (327, 278), "EQUAL", color=BLUE, size=18)
    box_text(plate, (155, 325, 500, 420), "Different heights; each receives 1 box", size=26,
             minimum=18, bold=True, fill=BLUE)
    plate.draw.line((170, 535, 490, 535), fill=INK_SOFT, width=8)
    for index, body_height in enumerate((150, 105, 60)):
        x = 215 + index * 112
        box_top = 615
        head_y = box_top - body_height
        plate.dot((x, head_y), 24, fill=GOLD_LIGHT, outline=GOLD, width=4)
        plate.draw.line((x, head_y + 25, x, box_top), fill=GOLD, width=6)
        plate.draw.rectangle((x - 35, box_top, x + 35, 660), fill=TEAL_LIGHT, outline=TEAL, width=4)
    box_text(plate, (150, 660, 505, 738), "Same share; useful when needs are relevantly alike.",
             size=20, minimum=15)
    panel(plate, (585, 240, 1015, 770), fill=TEAL_LIGHT, outline=TEAL)
    pill(plate, (800, 278), "EQUITABLE", color=TEAL, size=18)
    box_text(plate, (620, 325, 980, 420), "Vary support to address the barrier", size=26,
             minimum=18, bold=True, fill=TEAL)
    plate.draw.line((635, 535, 965, 535), fill=INK_SOFT, width=8)
    body_heights = (150, 105, 60)
    box_heights = (0, 45, 90)
    for index, (body_height, box_height) in enumerate(zip(body_heights, box_heights)):
        x = 690 + index * 112
        box_top = 660 - box_height
        head_y = box_top - body_height
        plate.dot((x, head_y), 24, fill=GOLD_LIGHT, outline=GOLD, width=4)
        plate.draw.line((x, head_y + 25, x, box_top), fill=GOLD, width=6)
        if box_height:
            plate.draw.rectangle((x - 38, box_top, x + 38, 660),
                                 fill=BLUE_LIGHT, outline=BLUE, width=4)
    box_text(plate, (615, 680, 985, 738), "Different support can create comparable access.",
             size=20, minimum=15)
    panel(plate, (1065, 240, 1480, 770), fill=GOLD_LIGHT, outline=GOLD)
    pill(plate, (1272, 278), "TAKE TURNS", color=GOLD, size=18)
    box_text(plate, (1100, 325, 1445, 420), "1 shared bicycle, 3 timed turns", size=26,
             minimum=18, bold=True, fill=GOLD)
    plate.arrow((1140, 540), (1400, 540), fill=CORAL, width=7, head=20)
    for index in range(3):
        x = 1160 + index * 105
        plate.dot((x, 540), 30, fill=(BLUE_LIGHT, TEAL_LIGHT, PLUM_LIGHT)[index],
                  outline=(BLUE, TEAL, PLUM)[index], width=4)
        plate.text((x, 540), str(index + 1), size=22, bold=True, anchor="mm")
    box_text(plate, (1095, 650, 1450, 738), "Sequence shares a resource that cannot be used at once.",
             size=20, minimum=15)
    footer(plate, "Fairness asks which differences matter; kindness notices the person affected.")


def _draw_money(plate: Plate) -> None:
    panel(plate, (120, 240, 1480, 770), fill=PAPER_LIGHT, outline=GOLD)
    pill(plate, (800, 280), "$10 EARNED — GIVE EVERY DOLLAR A JOB", color=GOLD, size=19)
    categories = [
        ("NEEDS", 5, BLUE, BLUE_LIGHT, "food or transport"),
        ("SAVE", 3, TEAL, TEAL_LIGHT, "future goal / emergency"),
        ("GIVE", 1, PLUM, PLUM_LIGHT, "chosen support"),
        ("WANTS", 1, CORAL, CORAL_LIGHT, "something optional"),
    ]
    x = 170
    unit = 110
    for heading, count, color, light, detail in categories:
        width = count * unit
        panel(plate, (x, 370, x + width - 10, 590), fill=light, outline=color, radius=12)
        box_text(plate, (x + 8, 386, x + width - 18, 450), f"{heading}  ${count}",
                 size=25, minimum=16, bold=True, fill=color)
        for index in range(count):
            plate.dot((x + 52 + index * unit, 515), 31, fill=PAPER_LIGHT, outline=color, width=5)
            plate.text((x + 52 + index * unit, 515), "$1", size=20, bold=True, fill=color, anchor="mm")
        box_text(plate, (x + 6, 606, x + width - 16, 684), detail,
                 size=19, minimum=14, bold=True, fill=color)
        x += width
    box_text(plate, (300, 700, 1300, 755), "$5 + $3 + $1 + $1 = $10 — the plan balances", size=28,
             minimum=20, bold=True, fill=INK)
    footer(plate, "A budget makes tradeoffs visible; categories and amounts should match a real person's situation.")


def _draw_study_curves(plate: Plate) -> None:
    panel(plate, (120, 235, 1480, 780), fill=PAPER_LIGHT, outline=BLUE)
    origin = (235, 690)
    plate.arrow(origin, (1410, 690), fill=INK, width=6, head=20)
    plate.arrow(origin, (235, 300), fill=INK, width=6, head=20)
    plate.text((1320, 724), "days", size=22, bold=True, fill=INK_SOFT)
    plate.text((150, 292), "recall", size=22, bold=True, fill=INK_SOFT)
    # Cramming curve: high once, steep fall.
    cram = []
    spaced = []
    for index in range(101):
        x = 260 + index * 10.7
        cram_y = 650 - 300 * math.exp(-index / 15)
        # Sawtooth-like boosts at four retrieval sessions, increasingly durable.
        strength = 0.0
        for session, durability in ((0, 18), (22, 25), (48, 34), (78, 48)):
            if index >= session:
                strength = max(strength, math.exp(-(index - session) / durability))
        spaced_y = 650 - 300 * strength
        cram.append((x, cram_y))
        spaced.append((x, spaced_y))
    plate.polyline(cram, fill=CORAL, width=8)
    plate.polyline(spaced, fill=TEAL, width=8)
    for session in (0, 22, 48, 78):
        x = 260 + session * 10.7
        plate.draw.line((x, 650, x, 335), fill=TEAL + "88", width=3)
        pill(plate, (x, 660), "RECALL", color=TEAL, size=12)
    plate.text((520, 560), "one cram session", size=22, bold=True, fill=CORAL)
    plate.text((980, 405), "spaced retrieval", size=22, bold=True, fill=TEAL)
    footer(plate, "Retrieving after some forgetting strengthens later access more than rereading everything at once.")


def _draw_epistemology(plate: Plate) -> None:
    panel(plate, (120, 235, 900, 780), fill=PAPER_LIGHT, outline=PLUM)
    pill(plate, (510, 272), "TRADITIONAL TARGET", color=PLUM, size=18)
    plate.draw.ellipse((220, 330, 610, 700), fill=BLUE_LIGHT + "99", outline=BLUE, width=6)
    plate.draw.ellipse((420, 330, 810, 700), fill=TEAL_LIGHT + "99", outline=TEAL, width=6)
    plate.draw.ellipse((320, 465, 710, 790), fill=GOLD_LIGHT + "88", outline=GOLD, width=6)
    plate.text((300, 410), "BELIEF", size=24, bold=True, fill=BLUE, anchor="mm")
    plate.text((725, 410), "TRUTH", size=24, bold=True, fill=TEAL, anchor="mm")
    plate.text((515, 725), "JUSTIFICATION", size=22, bold=True, fill=GOLD, anchor="mm")
    plate.text((515, 555), "knowledge?", size=29, bold=True, fill=PLUM, anchor="mm")
    panel(plate, (950, 255, 1480, 760), fill=CORAL_LIGHT, outline=CORAL)
    pill(plate, (1215, 292), "GETTIER PRESSURE TEST", color=CORAL, size=17)
    box_text(plate, (985, 330, 1445, 440), "A justified belief is true partly because of luck.",
             size=25, minimum=18, bold=True, fill=CORAL)
    plate.arrow((1060, 500), (1370, 500), fill=CORAL, width=7, head=22)
    box_text(plate, (980, 525, 1450, 680),
             "Belief ✓   Truth ✓   Justification ✓\nYet the link between reason and truth seems defective.",
             size=23, minimum=17, bold=True)
    footer(plate, "Justified true belief is illuminating, but Gettier cases challenge whether it is sufficient.")


def _draw_causation(plate: Plate) -> None:
    panel(plate, (120, 240, 720, 770), fill=BLUE_LIGHT, outline=BLUE)
    pill(plate, (420, 278), "COMMON-CAUSE MODEL", color=BLUE, size=18)
    plate.dot((300, 500), 62, fill=GOLD_LIGHT, outline=GOLD, width=6)
    plate.text((300, 500), "C", size=32, bold=True, anchor="mm")
    plate.dot((540, 405), 58, fill=TEAL_LIGHT, outline=TEAL, width=6)
    plate.text((540, 405), "A", size=32, bold=True, anchor="mm")
    plate.dot((540, 610), 58, fill=CORAL_LIGHT, outline=CORAL, width=6)
    plate.text((540, 610), "B", size=32, bold=True, anchor="mm")
    plate.arrow((365, 480), (470, 430), fill=TEAL, width=7, head=20)
    plate.arrow((365, 520), (470, 585), fill=CORAL, width=7, head=20)
    box_text(plate, (165, 650, 675, 738),
             "C can make A and B covary even when this model contains no A → B arrow.",
             size=22, minimum=16, bold=True, fill=BLUE)
    panel(plate, (780, 240, 1480, 770), fill=PAPER_LIGHT, outline=PLUM)
    pill(plate, (1130, 278), "ONE INTERVENTIONIST TEST", color=PLUM, size=18)
    plate.dot((945, 485), 58, fill=TEAL_LIGHT, outline=TEAL, width=6)
    plate.text((945, 485), "do(A)", size=27, bold=True, anchor="mm")
    plate.dot((1295, 485), 58, fill=CORAL_LIGHT, outline=CORAL, width=6)
    plate.text((1295, 485), "B?", size=30, bold=True, anchor="mm")
    plate.dashed_line((1010, 485), (1225, 485), fill=PLUM, width=7)
    box_text(plate, (1030, 415, 1210, 465), "causal effect?", size=17,
             minimum=13, bold=True, fill=PLUM)
    box_text(plate, (825, 575, 1435, 728),
             "If a well-defined intervention on A leaves B unchanged—with the model and relevant background conditions held fixed—that counts against A causing B in this setting.",
             size=22, minimum=15, bold=True, fill=PLUM)
    footer(plate, "Interventionism is one framework for causation; metaphysics also asks what grounds causal facts.")


def _draw_philsci(plate: Plate) -> None:
    """A test pipeline that visibly branches on agreement versus anomaly."""

    box_text(plate, (170, 194, 1430, 236),
             "THE SAME TEST CAN SUPPORT A THEORY OR EXPOSE AN ANOMALY",
             size=22, bold=True, fill=INK_SOFT)
    stages = [
        ((120, 278, 380, 474), "THEORY",
         "State the claim's scope and separate it from background assumptions.", BLUE, BLUE_LIGHT),
        ((430, 278, 690, 474), "RISKY PREDICTION",
         "Name an outcome that would discriminate this account from rivals.", TEAL, TEAL_LIGHT),
        ((740, 278, 1000, 474), "TEST + DATA",
         "Calibrate measures, use controls and quantify uncertainty.", PLUM, PLUM_LIGHT),
    ]
    for index, (box, heading, detail, color, light) in enumerate(stages):
        panel(plate, box, fill=light, outline=color, radius=16)
        box_text(plate, (box[0] + 12, box[1] + 12, box[2] - 12, box[1] + 72),
                 heading, size=23, minimum=16, bold=True, fill=color)
        box_text(plate, (box[0] + 16, box[1] + 76, box[2] - 16, box[3] - 12),
                 detail, size=18, minimum=13)
        if index < len(stages) - 1:
            plate.arrow((box[2] + 7, 376), (stages[index + 1][0][0] - 7, 376),
                        fill=color, width=6, head=18)

    # Comparison is a genuine branch rather than a prose step in a line.
    diamond = ((1115, 294), (1210, 376), (1115, 458), (1020, 376))
    plate.draw.polygon(diamond, fill=GOLD_LIGHT, outline=GOLD, width=6)
    box_text(plate, (1042, 326, 1188, 426), "PREDICTION\nVS DATA", size=19,
             minimum=14, bold=True, fill=GOLD)
    plate.arrow((1007, 376), (1022, 376), fill=GOLD, width=6, head=15)

    support_box = (1250, 252, 1480, 440)
    anomaly_box = (1250, 492, 1480, 680)
    panel(plate, support_box, fill=GREEN_LIGHT, outline=GREEN, radius=16)
    box_text(plate, (1262, 266, 1468, 328), "FIT WITHIN UNCERTAINTY", size=20,
             minimum=14, bold=True, fill=GREEN)
    box_text(plate, (1266, 338, 1464, 424),
             "Provisional corroboration; not proof or final confirmation.",
             size=17, minimum=12, bold=True)
    panel(plate, anomaly_box, fill=CORAL_LIGHT, outline=CORAL, radius=16)
    box_text(plate, (1262, 506, 1468, 564), "ANOMALY / MISFIT", size=20,
             minimum=14, bold=True, fill=CORAL)
    box_text(plate, (1266, 574, 1464, 664),
             "Check theory, auxiliaries, measurement, analysis and rival accounts.",
             size=17, minimum=12, bold=True)
    plate.arrow((1214, 350), (1242, 338), fill=GREEN, width=6, head=16)
    plate.arrow((1162, 438), (1242, 548), fill=CORAL, width=6, head=16)

    revision_box = (710, 590, 1165, 772)
    panel(plate, revision_box, fill=GOLD_LIGHT, outline=GOLD, radius=16)
    box_text(plate, (730, 606, 1145, 660), "REVISE + RETEST", size=23,
             minimum=16, bold=True, fill=GOLD)
    box_text(plate, (735, 666, 1140, 752),
             "Any change must generate a new discriminating prediction rather than merely shield the claim.",
             size=18, minimum=13, bold=True)
    plate.arrow((1242, 642), (1173, 686), fill=CORAL, width=6, head=18)
    plate.arrow((710, 684), (585, 484), fill=GOLD, width=6, head=18)
    pill(plate, (620, 578), "NEW TEST", color=GOLD, size=14)
    footer(plate, "Evidence constrains theories through branching comparisons, revision and renewed prediction.")


def _draw_behavioral_choice(plate: Plate) -> None:
    panel(plate, (120, 240, 720, 770), fill=TEAL_LIGHT, outline=TEAL)
    pill(plate, (420, 278), "GAIN FRAME", color=TEAL, size=18)
    box_text(plate, (170, 330, 670, 420), "A  Sure gain of $50", size=29, bold=True, fill=TEAL)
    box_text(plate, (170, 435, 670, 545), "B  50% gain $100\n    50% gain $0", size=27,
             minimum=20, bold=True, fill=BLUE)
    box_text(plate, (180, 580, 660, 700), "Expected value:\nA = $50     B = 0.5×$100 = $50",
             size=25, minimum=18, bold=True, fill=INK)
    panel(plate, (780, 240, 1480, 770), fill=CORAL_LIGHT, outline=CORAL)
    pill(plate, (1130, 278), "WHAT THE MODEL TESTS", color=CORAL, size=18)
    for index, (head, detail) in enumerate([
        ("DESCRIPTION", "Which outcomes and probabilities are represented?"),
        ("NORMATIVE RULE", "Expected value treats the two options alike here."),
        ("OBSERVED CHOICE", "Certainty, framing and reference points may shift preference."),
        ("UPDATE", "Repeated evidence can motivate a richer model of utility."),
    ]):
        y0 = 330 + index * 94
        box_text(plate, (820, y0, 1050, y0 + 72), head, size=21, minimum=15,
                 bold=True, fill=(BLUE, TEAL, PLUM, CORAL)[index])
        box_text(plate, (1070, y0, 1440, y0 + 72), detail, size=18, minimum=13, align="left")
    footer(plate, "Equal expected values need not feel equal; behavioral science measures the systematic difference.")


def _draw_advanced_logic(plate: Plate) -> None:
    panel(plate, (120, 235, 790, 780), fill=BLUE_LIGHT, outline=BLUE)
    pill(plate, (455, 272), "MODAL LOGIC", color=BLUE, size=18)
    worlds = [(270, 470, "w₀", ""), (500, 365, "w₁", "P"), (650, 560, "w₂", "¬P")]
    for x, y, label, truth in worlds:
        plate.dot((x, y), 55, fill=PAPER_LIGHT, outline=BLUE, width=6)
        plate.text((x, y - (14 if truth else 0)), label, size=25, bold=True, anchor="mm")
        if truth:
            plate.text((x, y + 25), truth, size=21, bold=True, fill=BLUE, anchor="mm")
    plate.arrow((330, 450), (438, 390), fill=BLUE, width=6, head=18)
    plate.arrow((330, 490), (588, 545), fill=BLUE, width=6, head=18)
    box_text(plate, (165, 625, 745, 740),
             "Here ◇P is true (w₁), while □P is false (not w₂).\nNecessity checks all accessible worlds; possibility needs one.",
             size=22, minimum=16, bold=True, fill=BLUE)
    panel(plate, (850, 235, 1480, 780), fill=CORAL_LIGHT, outline=CORAL)
    pill(plate, (1165, 272), "PARACONSISTENT LOGIC", color=CORAL, size=18)
    plate.dot((985, 390), 50, fill=GOLD_LIGHT, outline=GOLD, width=6)
    plate.text((985, 390), "P", size=28, bold=True, anchor="mm")
    plate.dot((1345, 390), 50, fill=PLUM_LIGHT, outline=PLUM, width=6)
    plate.text((1345, 390), "¬P", size=27, bold=True, anchor="mm")
    panel(plate, (1065, 470, 1265, 550), fill=PAPER_LIGHT, outline=CORAL, radius=12)
    box_text(plate, (1075, 480, 1255, 540), "THEORY CONTAINS\nP AND ¬P",
             size=19, minimum=15, bold=True, fill=CORAL)
    plate.arrow((1015, 438), (1095, 468), fill=GOLD, width=5, head=15)
    plate.arrow((1315, 438), (1235, 468), fill=PLUM, width=5, head=15)
    plate.dot((1360, 635), 46, fill=BLUE_LIGHT, outline=BLUE, width=6)
    plate.text((1360, 635), "Q", size=27, bold=True, anchor="mm")
    plate.dashed_line((1268, 550), (1320, 610), fill=CORAL, width=6)
    plate.draw.line((1278, 568, 1310, 600), fill=CORAL, width=8)
    plate.draw.line((1310, 568, 1278, 600), fill=CORAL, width=8)
    box_text(plate, (900, 680, 1430, 750),
             "The contradiction does not entail every unrelated Q.",
             size=21, minimum=16, bold=True, fill=CORAL)
    footer(plate, "Different logics alter consequence or possibility deliberately; each needs explicit semantics.")


def _draw_language_context(plate: Plate) -> None:
    sentence = "I am here now."
    for index, (speaker, place, time, color, light) in enumerate([
        ("Amina", "Cape Town", "09:00", BLUE, BLUE_LIGHT),
        ("Bo", "Nairobi", "10:00", TEAL, TEAL_LIGHT),
    ]):
        x0 = 120 + index * 700
        panel(plate, (x0, 250, x0 + 650, 735), fill=light, outline=color)
        pill(plate, (x0 + 325, 290), f"CONTEXT {index + 1}", color=color, size=18)
        box_text(plate, (x0 + 70, 340, x0 + 580, 430), f'“{sentence}”',
                 size=34, minimum=24, bold=True, fill=color)
        mapping = [("I", speaker), ("here", place), ("now", time)]
        for row, (word, referent) in enumerate(mapping):
            y = 490 + row * 68
            box_text(plate, (x0 + 70, y, x0 + 240, y + 52), word, size=23,
                     bold=True, fill=color)
            plate.arrow((x0 + 245, y + 26), (x0 + 340, y + 26), fill=color, width=5, head=15)
            box_text(plate, (x0 + 350, y, x0 + 580, y + 52), referent, size=23,
                     minimum=17, bold=True, fill=INK)
    footer(plate, "The words stay fixed while speaker, place and time determine their reference and truth conditions.")


_ITEMS = [
    spec(
        "mind.0.feelings", "Feelings", 0, DOMAIN, "situation-feeling-response-plate",
        "Two children enter the same new school: Sam notices a fast heartbeat and worries about getting lost, while Lee feels wide-eyed excitement; each names a feeling and chooses a different helpful response.",
        "Feelings involve situations, body clues and interpretations. The same event can feel different to different people, so empathy begins by noticing and asking.",
        _draw_feelings,
    ),
    spec(
        "mind.0.fair", "Fair and Kind", 0, DOMAIN, "equal-equitable-turns-plate",
        "Three worked panels distinguish equal sharing of one box each, equitable support using boxes of different heights to overcome a barrier, and timed turns on one shared bicycle.",
        "Fair can mean equal shares, relevant support or turns depending on the problem. Kindness attends to how the arrangement affects actual people.",
        _draw_fairness,
    ),
    spec(
        "mind.0.choices", "Making Choices", 0, DOMAIN, "choice-now-later-reasons-plate",
        "A two-by-two decision table compares taking an umbrella or leaving it behind under two uncertain outcomes, rain or dry weather, and lists the consequence of each choice-outcome pair.",
        "A reason connects what matters and what we know to a choice. Uncertainty means a good decision can still have an unlucky result.",
        lambda plate: draw_matrix(
            plate,
            ["TAKE UMBRELLA", "LEAVE IT"],
            ["IF IT RAINS", "IF IT STAYS DRY"],
            [
                ["stay dry; carry the umbrella", "carried extra weight"],
                ["get wet", "travel light"],
            ],
            "Use the forecast and what matters to choose; judge the decision by reasons, not hindsight alone.",
            corner="CHOICE × OUTCOME",
        ),
    ),
    flow(
        "mind.1.thinking", "Good Thinking", 1, "claim-reason-evidence-question-plate",
        "A four-step argument begins with the claim that a plant grew taller because it was near a window, adds a measured example, asks whether water or plant type also differed, and proposes a fair comparison to test the reason.",
        "Good thinking makes a claim, gives a relevant reason, checks evidence and asks what else could explain the result.",
        [
            ("CLAIM", "‘The window made this plant grow taller.’"),
            ("REASON + EVIDENCE", "It received more light; its height changed from 8 cm to 14 cm."),
            ("ASK WHAT ELSE", "Did water, soil, temperature or starting plant differ too?"),
            ("FAIR CHECK", "Use similar plants; vary position while holding other care alike."),
        ],
        "A reason is strongest when evidence distinguishes it from a plausible alternative.",
    ),
    flow(
        "mind.1.friendship", "Getting Along", 1, "conflict-listen-repair-plate",
        "A five-step playground conflict process moves from pausing, hearing each person's account, paraphrasing the other view, naming both needs and proposing a testable agreement about sharing a game.",
        "Resolving conflict does not require pretending everyone saw the event alike. Listening, restating and naming needs create room for a workable repair.",
        [
            ("PAUSE", "Stop the action and make the situation physically safe."),
            ("EACH TELLS", "One speaks while the other listens without interruption."),
            ("PARAPHRASE", "‘You wanted a turn and thought I ignored you—is that right?’"),
            ("NAME NEEDS", "Belonging, fairness, space, safety or keeping an agreement."),
            ("TRY + REVIEW", "Agree on timed turns; check afterward whether both could join."),
        ],
        "A repair is specific, mutual and revisable—not simply an order to stop feeling upset.",
    ),
    spec(
        "mind.1.money-sense", "Money Sense", 1, DOMAIN, "ten-dollar-budget-plate",
        "Ten one-dollar coins are grouped into a balanced example budget: five dollars for needs, three to save, one to give and one for wants, with the arithmetic five plus three plus one plus one equals ten.",
        "A budget assigns limited money among present needs, future goals, giving and optional wants. Real categories and amounts depend on a person's circumstances.",
        _draw_money,
    ),
    flow(
        "mind.1.rules", "Right and Wrong", 1, "rule-reason-review-plate",
        "A four-step ethics check starts with cutting a lunch line, asks what happens if everyone does it, checks harm, consent and fairness, and revises the action to waiting or asking for an agreed exception.",
        "Rules help coordinate people when their actions affect one another. A reasoned rule considers general use, harm, consent, fairness and justified exceptions.",
        [
            ("ACTION", "‘I cut to the front because I am in a hurry.’"),
            ("GENERALIZE", "If everyone cut when hurried, the line could no longer coordinate turns."),
            ("CHECK PEOPLE", "Others lose time and did not agree; ask whether a relevant need changes the case."),
            ("REVISE", "Wait, or request an explicit exception with a reason others can assess."),
        ],
        "A moral reason should be shareable with the people who bear the consequence.",
    ),
    flow(
        "mind.2.psychology-intro", "How the Mind Works", 2,
        "attention-memory-learning-plate",
        "A five-step arrow path runs from sights and sounds through selective attention, limited working memory, active encoding and practice, and retrieval from long-term memory.",
        "Learning is not a camera recording. Attention selects, working memory transforms a small amount, and retrieval practice makes long-term access more durable.",
        [
            ("SENSORY INPUT", "Many sights, sounds and body signals arrive at once."),
            ("ATTENTION", "Goals and salience select some information; unattended detail may vanish."),
            ("WORKING MEMORY", "Hold and combine a limited set; overload impairs processing."),
            ("ENCODE + PRACTICE", "Connect meaning, examples and prior knowledge."),
            ("RETRIEVE", "Recall without looking; successful effort strengthens later access."),
        ],
        "Memory improves through meaningful processing and retrieval, not exposure alone.",
    ),
    spec(
        "mind.2.society", "Living Together", 2, DOMAIN,
        "people-groups-institutions-feedback-plate",
        "A reciprocal network links a school-day norm at the center to individuals, peer groups, cultural meanings and formal institutions, with two-way arrows showing people learn and also change social patterns.",
        "Society is neither only individuals nor an entity above them. People act through groups, meanings and institutions, reproducing or changing norms through feedback.",
        lambda plate: draw_network(
            plate,
            ("ONE SCHOOL NORM", "Example: how people take turns speaking in class."),
            [
                ("INDIVIDUALS", "interpret expectations, choose actions and experience consequences"),
                ("PEER GROUPS", "reward, model, challenge or exclude particular behavior"),
                ("CULTURAL MEANINGS", "define respect, authority and participation differently"),
                ("INSTITUTIONS", "rules, schedules, roles and resources make some actions easier"),
            ],
            "Social patterns constrain action, yet repeated action and collective organizing can alter them.",
            edge_word="LEARNED NORMS ↔ HUMAN AGENCY",
        ),
    ),
    compare(
        "mind.2.big-questions", "Big Questions", 2, "fairness-three-lenses-plate",
        "Three columns apply consequence, rule and character or care lenses to the same question of whether to reveal a friend's harmful secret, naming what each lens notices and what evidence remains needed.",
        "Philosophical questions become clearer when rival answers give reasons and face the same case. Different lenses can expose consequences, duties and relationships without automatically settling the answer.",
        [
            ("CONSEQUENCES", "Who may be helped or harmed now and later? How likely is each outcome?", "Need evidence about risk, alternatives and affected people"),
            ("RULES / RIGHTS", "What promise, duty, consent or right applies? Can an exception be justified?", "Need a rule others could reasonably accept"),
            ("CHARACTER / CARE", "What would honesty, courage and care require in this relationship?", "Need attention to dependence, trust and power"),
        ],
        "A good answer states a principle, applies it consistently and confronts the hardest counterexample.",
        relation="ONE DIFFICULT CASE — THREE REASON-GIVING LENSES",
    ),
    spec(
        "mind.2.study-skills", "Learning How to Learn", 2, DOMAIN,
        "spacing-retrieval-curves-plate",
        "Two recall-strength curves compare a single cram session that fades steeply with four spaced retrieval sessions that repeatedly boost recall and decay more slowly across days.",
        "Spacing allows some forgetting before retrieval, making practice effortful and durable. The exact curve varies, but repeated recall generally outperforms one massed review.",
        _draw_study_curves,
    ),
    flow(
        "mind.3.critical", "Critical Thinking", 3, "prediction-evidence-update-plate",
        "A five-step reasoning chain starts with a claim that a supplement improves sleep, turns it into a measurable prediction, compares a randomized group with a control, checks attrition and expectancy bias, and updates the claim with an effect size and uncertainty.",
        "Critical thinking asks what evidence a claim predicts, what alternative processes could mimic it, and how much the result should change confidence.",
        [
            ("CLAIM", "‘This supplement improves sleep.’ Define the people, dose and outcome."),
            ("PREDICTION", "Compared with control, average validated sleep quality should improve."),
            ("OBSERVE", "Randomize where ethical; measure before and after; keep procedures comparable."),
            ("BIAS CHECK", "Inspect expectancy, missing data, selective outcomes and subgroup fishing."),
            ("UPDATE", "Report effect size, interval, limitations and what result would change the conclusion."),
        ],
        "Evidence changes confidence by degree; one favorable result is neither proof nor nothing.",
    ),
    spec(
        "mind.3.psychology", "Psychology", 3, DOMAIN,
        "behavior-levels-development-plate",
        "A reciprocal network places one child's classroom behavior at the center and connects neural and bodily state, cognition and emotion, family and peer context, and development over time, warning against a single-cause label.",
        "Psychological explanation spans biological, cognitive, social and developmental levels. Causes interact, and the same behavior can arise through different pathways.",
        lambda plate: draw_network(
            plate,
            ("OBSERVED BEHAVIOR", "A child stops participating during a difficult group task."),
            [
                ("BODY + BRAIN", "sleep, stress response, sensory needs and neurodevelopment"),
                ("COGNITION + EMOTION", "working memory load, expectation, anxiety and motivation"),
                ("SOCIAL CONTEXT", "peer climate, teaching design, language and family conditions"),
                ("DEVELOPMENT", "skills and self-regulation change with experience and age"),
            ],
            "Assess patterns across situations and time before treating a behavior as a fixed trait.",
            edge_word="INTERACTING LEVELS — MANY POSSIBLE PATHS",
        ),
    ),
    compare(
        "mind.3.ethics", "Ethics", 3, "moral-theories-one-case-plate",
        "Three columns evaluate whether to break a promise to prevent serious harm: consequentialism compares outcomes, deontology tests duties and universalizable rules, and virtue or care ethics examines character, relationships and vulnerability.",
        "Moral theories organize reasons differently. Applying each to the same hard case reveals both its insight and the questions it leaves unresolved.",
        [
            ("CONSEQUENTIALISM", "Compare likely wellbeing and harm for everyone affected, including indirect effects.", "Challenge: prediction, distribution and what counts as a consequence"),
            ("DEONTOLOGY", "Ask which duties and rights bind: promise, honesty, aid, and respect for persons.", "Challenge: conflict among duties and the wording of the rule"),
            ("VIRTUE / CARE", "Ask what practical wisdom, trust, courage and attention to dependence require.", "Challenge: translating character and relationship into action"),
        ],
        "A theory earns its force by explaining the case and surviving a difficult counterexample.",
        relation="ONE CASE: BREAK A PROMISE TO PREVENT SERIOUS HARM?",
    ),
    spec(
        "mind.3.philosophy-intro", "History of Philosophy", 3, DOMAIN,
        "philosophy-arguments-transmission-plate",
        "A timeline links Socratic questioning in fifth-century BCE Athens, Plato and Aristotle, Hellenistic schools, medieval philosophy in Arabic, Hebrew and Latin traditions, and early modern debates on knowledge and politics, emphasizing transmission and dispute.",
        "Philosophical history is a network of arguments, translations and institutions. A Socrates-to-moderns route is one path through a much larger global history.",
        lambda plate: draw_timeline(
            plate,
            [
                ("5th c. BCE", "Socratic questioning", "dialogue tests definitions and the examined life; texts come through others"),
                ("4th c. BCE", "Plato + Aristotle", "systematic disputes about knowledge, ethics, politics and nature"),
                ("3rd c. BCE onward", "Hellenistic schools", "Stoic, Epicurean and skeptical practices cross long periods"),
                ("c. 800–1400 CE", "Translation + commentary", "Arabic, Hebrew and Latin thinkers transform inherited arguments"),
                ("1600s–1700s", "Early modern debates", "reason, experience, science, freedom and state authority contested"),
            ],
            "Ideas persist by being translated, criticized and repurposed—not merely handed down intact.",
            qualifier="ONE CONNECTED ROUTE — NOT THE WHOLE GLOBAL HISTORY OF PHILOSOPHY",
        ),
    ),
    flow(
        "mind.3.social-science", "Social Sciences", 3,
        "social-research-triangulation-plate",
        "A five-step social research process moves from a question about why park use differs by neighborhood through operational definitions and sampling, surveys plus observation and interviews, pattern comparison, and limits and alternative explanations.",
        "Social science turns broad concepts into observable measures, samples people and settings, combines methods and states what its design cannot establish.",
        [
            ("QUESTION", "Why is park use lower in one neighborhood? Specify place, period and population."),
            ("OPERATIONALIZE", "Measure visits, access, safety perception, shade, programs and travel time."),
            ("SAMPLE + METHODS", "Combine counts, surveys and interviews; note who is missed by each."),
            ("COMPARE PATTERNS", "Test whether access and use covary; look for contradictory cases."),
            ("LIMIT CLAIM", "Association is not automatically cause; explain selection and uncertainty."),
        ],
        "Triangulation is powerful because methods have different blind spots, not because agreement guarantees truth.",
    ),
    spec(
        "mind.4.epistemology", "Epistemology", 4, DOMAIN,
        "belief-truth-justification-gettier-plate",
        "Three overlapping circles for belief, truth and justification meet at a region marked knowledge with a question mark; a Gettier pressure-test card shows all three checks satisfied through luck while the reason-to-truth link remains defective.",
        "The traditional analysis of knowledge as justified true belief is a useful starting point. Gettier cases show why the quality of the connection between justification and truth also matters.",
        _draw_epistemology,
    ),
    spec(
        "mind.4.metaphysics", "Metaphysics", 4, DOMAIN,
        "causal-common-cause-intervention-plate",
        "A common-cause model shows C pointing separately to A and B with no A-to-B arrow; a second panel presents, as one interventionist test, the qualified question of whether a well-defined do-A changes B under the stated model and background conditions.",
        "A common cause can make two events covary without either causing the other. Interventionism is one influential framework for probing causal dependence, not a complete or uncontested definition of metaphysical causation.",
        _draw_causation,
    ),
    spec(
        "mind.4.cognitive-sci", "Cognitive Science", 4, DOMAIN,
        "cognitive-levels-navigation-plate",
        "A reciprocal network puts successful navigation at the center and connects computational goal, algorithmic representation, neural implementation and evidence from psychology, neuroscience, linguistics, philosophy and artificial intelligence.",
        "Cognitive science explains one capacity at multiple levels. A task description, information-processing strategy and physical implementation constrain one another without being interchangeable.",
        lambda plate: draw_network(
            plate,
            ("NAVIGATE HOME", "The same successful behavior can be explained at several compatible levels."),
            [
                ("COMPUTATIONAL", "goal: choose an efficient route under uncertainty"),
                ("ALGORITHMIC", "represent landmarks or a map; update position and compare options"),
                ("IMPLEMENTATION", "neural systems, perception and motor control realize processing"),
                ("DISCIPLINES", "behavioral tests, brain measures, formal models and AI simulations"),
            ],
            "A model gains force when predictions connect levels and survive evidence from several methods.",
            edge_word="TASK ↔ REPRESENTATION ↔ MECHANISM",
        ),
    ),
    flow(
        "mind.4.ethics-adv", "Moral Philosophy", 4, "meta-normative-applied-plate",
        "A four-level arrow chain separates a metaethical question about what wrong means from a normative principle, an applied case about allocating scarce medicine and the resulting transparent institutional procedure.",
        "Metaethics, normative ethics and applied ethics ask different questions. Keeping the levels distinct prevents a claim about moral language from silently deciding a policy case.",
        [
            ("METAETHICS", "What does ‘wrong’ mean? Are moral claims truth-apt, objective or constructed?"),
            ("NORMATIVE ETHICS", "Which principles—welfare, duty, virtue, care or justice—guide action?"),
            ("APPLIED CASE", "How should scarce medicine be allocated among people with competing claims?"),
            ("INSTITUTIONAL RULE", "Translate reasons into transparent criteria, appeal and bias monitoring."),
        ],
        "A defensible policy links levels openly and remains revisable in light of effects and objections.",
    ),
    spec(
        "mind.4.philsci", "Philosophy of Science", 4,
        DOMAIN,
        "theory-risky-prediction-revision-plate",
        "A theory leads to a risky prediction and calibrated test, then a prediction-versus-data diamond visibly branches to provisional corroboration when results fit within uncertainty or to an anomaly when they do not; anomaly checks and revision loop back to a new discriminating test.",
        "Scientific theories gain content by risking observations. A failed prediction may implicate the theory, measurement or auxiliary assumptions, so revision must generate further tests rather than merely protect the claim.",
        _draw_philsci,
    ),
    spec(
        "mind.4.economics-behav", "Decision & Behavioral Science", 4, DOMAIN,
        "equal-expected-value-framing-plate",
        "A worked gain-frame choice compares a sure fifty dollars with a fifty-percent chance of one hundred dollars and a fifty-percent chance of zero; both equal fifty dollars in expected value, while a second panel lists how certainty and framing may shift observed choice.",
        "Expected value supplies a normative benchmark in this simplified case. Behavioral evidence tests how actual choices respond to certainty, framing, reference points and loss aversion.",
        _draw_behavioral_choice,
    ),
    spec(
        "mind.5.logic-advanced", "Advanced Logic", 5, DOMAIN,
        "modal-paraconsistent-logics-plate",
        "A possible-world graph has P in accessible world w-one and not-P in w-two, so diamond-P is true while box-P is false; beside it, P and not-P enter one theory but a blocked arrow shows they do not entail unrelated Q.",
        "Modal logic formalizes necessity and possibility through accessibility. Paraconsistent logics alter consequence so contradictions need not make every sentence derivable.",
        _draw_advanced_logic,
    ),
    spec(
        "mind.5.phil-mind", "Philosophy of Mind & AI", 5, DOMAIN,
        "mind-ai-levels-explanatory-gap-plate",
        "A reciprocal network places an AI system reporting pain at the center and connects observable behavior, functional organization, physical implementation and subjective experience, with the last marked as not settled by performance alone.",
        "Behavioral competence, functional organization, physical mechanism and subjective experience are distinct targets. Evidence about one constrains but may not settle claims about the others.",
        lambda plate: draw_network(
            plate,
            ("AI SAYS ‘I FEEL PAIN’", "A report is observable evidence whose interpretation depends on a theory of mind."),
            [
                ("BEHAVIOR", "Does the system discriminate, learn, avoid and explain consistently?"),
                ("FUNCTION", "What causal roles integrate memory, attention, goals and self-models?"),
                ("IMPLEMENTATION", "Which computational and physical processes realize those roles?"),
                ("EXPERIENCE", "Is there something it is like for the system? Performance alone may not decide."),
            ],
            "Do not slide from convincing language behavior directly to either consciousness or its absence.",
            edge_word="RELATED QUESTIONS — NO AUTOMATIC INFERENCE",
        ),
    ),
    spec(
        "mind.5.phil-language", "Philosophy of Language", 5, DOMAIN,
        "indexical-context-reference-plate",
        "Two context panels contain the identical sentence I am here now; arrows map I, here and now to Amina, Cape Town and 09:00 in one context and to Bo, Nairobi and 10:00 in the other.",
        "Indexicals show why sentence type alone does not fix reference or truth conditions. Speaker, place and time supply context-sensitive values.",
        _draw_language_context,
    ),
    spec(
        "mind.5.political-phil", "Political & Social Philosophy", 5, DOMAIN,
        "housing-justice-power-lenses-plate",
        "A reciprocal network places an affordable-housing policy at the center and connects distribution of benefits and burdens, recognition and status, democratic procedure, and power over land and agenda-setting.",
        "Political philosophy evaluates not only who receives resources, but also status, decision procedures and the power that shapes available choices.",
        lambda plate: draw_network(
            plate,
            ("HOUSING POLICY", "Where should affordable homes be built, funded and governed?"),
            [
                ("DISTRIBUTION", "Who receives housing, pays costs and bears displacement risk?"),
                ("RECOGNITION", "Whose needs and identities are respected rather than stigmatized?"),
                ("PROCEDURE", "Who participates, what reasons are public, and can decisions be appealed?"),
                ("POWER", "Who owns land, sets the agenda and can exit or veto the process?"),
            ],
            "A just outcome can be undermined by domination; a fair procedure can still preserve unjust structure.",
            edge_word="JUSTICE HAS MATERIAL, SOCIAL AND POLITICAL DIMENSIONS",
        ),
    ),
    spec(
        "mind.5.frontier", "Enduring Questions", 5, DOMAIN,
        "open-questions-evidence-map-plate",
        "Four evidence streams—neural and behavioral data, linguistic practice, moral disagreement and machine behavior—converge on a method of argument, models and counterexamples, then lead to qualified constraints rather than a box labeled solved.",
        "Enduring philosophical problems persist because evidence underdetermines key concepts or values, not because inquiry makes no progress. Arguments can rule out answers and sharpen what remains.",
        lambda plate: draw_evidence(
            plate,
            [
                ("CONSCIOUSNESS", "neural, behavioral and first-person evidence constrain theories of experience"),
                ("MEANING", "use, reference, inference and context pull in related but distinct directions"),
                ("NORMATIVITY", "moral reasons must answer disagreement, power and motivation"),
                ("AI MORAL STATUS", "capacity evidence and uncertainty meet potentially asymmetric harms"),
            ],
            ("PHILOSOPHICAL METHOD", "Clarify concepts; formalize where useful; test implications and counterexamples."),
            ("PROGRESS WITHOUT CLOSURE", "Discard incoherent views, map tradeoffs and state live uncertainty."),
            "An unanswered question can still have better and worse arguments, evidence and decision rules.",
        ),
    ),
]


SPECS: Dict[str, Spec] = {item["id"]: item for item in _ITEMS}
