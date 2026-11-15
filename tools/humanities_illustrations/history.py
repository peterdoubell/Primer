"""Lesson-specific explanatory plates for History & Civics."""

from __future__ import annotations

from typing import Dict, Sequence, Tuple

from .core import (
    BLUE,
    BLUE_LIGHT,
    CORAL,
    GOLD,
    GOLD_LIGHT,
    GREEN,
    INK,
    INK_SOFT,
    PAPER_LIGHT,
    PLUM,
    TEAL,
    TEAL_LIGHT,
    Plate,
    Spec,
    box_text,
    draw_branch,
    draw_comparison,
    draw_evidence,
    draw_flow,
    draw_matrix,
    draw_network,
    draw_timeline,
    draw_tracks,
    footer,
    panel,
    pill,
    spec,
)


DOMAIN = "history"


def _draw_fair_turns(plate: Plate) -> None:
    pill(plate, (800, 225), "THREE CHILDREN AGREE TO TRY TWO-MINUTE TURNS", color=TEAL, size=24)
    # One shared resource, pictured separately from the proposed allocation.
    panel(plate, (120, 285, 610, 780), outline=BLUE)
    plate.draw.line((190, 600, 275, 370, 455, 370, 540, 600), fill=BLUE, width=12, joint="curve")
    for x in (325, 405):
        plate.draw.line((x, 375, x, 555), fill=INK_SOFT, width=5)
    plate.draw.rounded_rectangle((305, 550, 425, 575), radius=7, fill=GOLD)
    plate.text((365, 655), "ONE SHARED SWING", size=25, bold=True, anchor="mm")
    box_text(plate, (150, 690, 580, 760), "Hear everyone's needs before agreeing on the rule.", size=24)
    panel(plate, (660, 285, 1480, 780), outline=TEAL)
    pill(plate, (1070, 330), "PROPOSED SCHEDULE — NOT A TEST RESULT", color=TEAL, size=21)
    left, step = 735, 220
    for i, (name, tone) in enumerate((("ARI", BLUE), ("BO", TEAL), ("CAM", PLUM))):
        x = left+i*step
        plate.draw.rectangle((x, 420, x+step, 540), fill=tone)
        plate.text((x+step/2, 480), name, size=27, bold=True, fill=PAPER_LIGHT, anchor="mm")
        plate.text((x, 575), str(i*2), size=24, anchor="mm")
    plate.text((left+3*step, 575), "6", size=24, anchor="mm")
    plate.text((1070, 625), "MINUTES FROM START", size=23, bold=True, anchor="mm")
    box_text(plate, (700, 674, 1440, 756), "Equal time is one proposal. Check safety, access and whether each child gets a usable turn.", size=24)
    footer(plate, "Try the agreed rule, hear feedback, then revise. Equal time alone does not prove fairness.")


def _draw_ancient_resources(plate: Plate) -> None:
    pill(plate, (800, 220), "INTERACTING NEEDS — NOT FOUR INEVITABLE STEPS", color=TEAL, size=24)
    for cx, label, tone in ((430, "WATER + CROPS", BLUE), (1170, "STORAGE + RECORDS", PLUM)):
        panel(plate, (cx-300, 270, cx+300, 785), outline=tone)
        pill(plate, (cx, 310), label, color=tone, size=25)
    plate.draw.line((220, 365, 270, 430, 245, 510, 280, 595, 245, 640), fill=BLUE, width=30, joint="curve")
    plate.draw.line((260, 490, 390, 490), fill=BLUE, width=12)
    for x in (420, 500, 580):
        plate.draw.line((x, 590, x, 420), fill=GREEN, width=5)
        for y in (445, 480, 515):
            plate.draw.ellipse((x-25, y-20, x, y+5), fill=GOLD)
            plate.draw.ellipse((x, y-20, x+25, y+5), fill=GOLD)
    box_text(plate, (165, 665, 695, 756), "Water management could support crops; floods also brought risks.", size=25)
    plate.draw.rounded_rectangle((955, 400, 1115, 620), radius=48, fill=GOLD_LIGHT, outline=GOLD, width=5)
    plate.draw.ellipse((955, 382, 1115, 432), fill=GOLD, outline=INK_SOFT, width=3)
    plate.draw.rounded_rectangle((1210, 400, 1390, 615), radius=17, fill=GOLD_LIGHT, outline=PLUM, width=5)
    for y in (450, 500, 550):
        for x in (1245, 1295, 1345):
            plate.draw.line((x, y, x+15, y-15), fill=PLUM, width=5)
    plate.text((1035, 650), "grain store", size=21, anchor="mm")
    plate.text((1300, 650), "record", size=21, anchor="mm")
    box_text(plate, (905, 687, 1435, 763), "Stored goods needed coordination; records helped track them.", size=25)
    plate.arrow((740, 500), (860, 500), fill=TEAL, width=5, head=16)
    plate.arrow((860, 565), (740, 565), fill=TEAL, width=5, head=16)
    footer(plate, "Schematic examples, not an excavated site. Egypt and Mesopotamia had different histories.")


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


def timeline(node_id: str, title: str, stage: int, plate_id: str, alt: str,
             caption: str, events: Sequence[Tuple[str, str, str]], conclusion: str,
             qualifier: str = "TIME RUNS LEFT → RIGHT") -> Spec:
    return spec(node_id, title, stage, DOMAIN, plate_id, alt, caption,
                lambda plate: draw_timeline(
                    plate, events, conclusion, qualifier=qualifier))


def _draw_supply_demand(plate: Plate) -> None:
    """A worked market-clearing graph with directional quantity responses."""

    panel(plate, (120, 230, 980, 780), fill=PAPER_LIGHT, outline=BLUE)
    origin = (250, 690)
    plate.arrow(origin, (880, 690), fill=INK, width=6, head=20)
    plate.arrow(origin, (250, 300), fill=INK, width=6, head=20)
    box_text(plate, (660, 705, 920, 752), "QUANTITY", size=21, bold=True, fill=INK_SOFT)
    box_text(plate, (128, 258, 230, 345), "PRICE", size=21, bold=True, fill=INK_SOFT)
    plate.draw.line((330, 620, 830, 340), fill=TEAL, width=10)
    plate.draw.line((330, 340, 830, 620), fill=CORAL, width=10)
    plate.text((790, 316), "supply", size=25, bold=True, fill=TEAL)
    plate.text((780, 650), "demand", size=25, bold=True, fill=CORAL)
    equilibrium = (580, 480)
    plate.dot(equilibrium, 16, fill=GOLD_LIGHT, outline=GOLD, width=6)
    plate.dashed_line((250, equilibrium[1]), equilibrium, fill=GOLD, width=4)
    plate.dashed_line((equilibrium[0], equilibrium[1]), (equilibrium[0], 690),
                      fill=GOLD, width=4)
    pill(plate, (580, 440), "MARKET-CLEARING POINT", color=GOLD, size=17)
    panel(plate, (1030, 250, 1478, 480), fill=BLUE_LIGHT, outline=TEAL)
    box_text(plate, (1054, 270, 1454, 338), "IF PRICE IS HIGHER", size=25,
             bold=True, fill=TEAL)
    box_text(plate, (1058, 350, 1450, 454),
             "Quantity supplied exceeds quantity demanded: a surplus pushes sellers to adjust.",
             size=21, minimum=15)
    panel(plate, (1030, 520, 1478, 750), fill=GOLD_LIGHT, outline=CORAL)
    box_text(plate, (1054, 540, 1454, 608), "IF PRICE IS LOWER", size=25,
             bold=True, fill=CORAL)
    box_text(plate, (1058, 620, 1450, 724),
             "Quantity demanded exceeds quantity supplied: a shortage pressures the price or allocation.",
             size=21, minimum=15)
    footer(plate, "The crossing is a model, not a guarantee: institutions and shifting curves matter.")


def _draw_rule_of_law(plate: Plate) -> None:
    draw_comparison(
        plate,
        [
            ("RULE OF LAW", "Published rules bind officials and citizens; decisions need reasons and review.",
             "Human rights • independent review • equal protection"),
            ("RULE BY POWER", "A ruler uses legal forms selectively while remaining above meaningful constraint.",
             "Arbitrary exceptions • weak review • unequal treatment"),
        ],
        "Accountable power, independent courts and human rights—not merely a government using laws.",
        relation="TWO DIFFERENT RELATIONSHIPS BETWEEN LAW AND POWER",
    )


def _draw_geography(plate: Plate) -> None:
    """Nested spatial scales plus physical features that cross borders."""

    panel(plate, (120, 244, 920, 770), fill=BLUE_LIGHT, outline=BLUE)
    pill(plate, (520, 280), "ONE MAP — SEVERAL LAYERS", color=BLUE, size=19)
    plate.draw.polygon(((240, 370), (430, 310), (610, 355), (790, 305),
                        (850, 610), (650, 700), (420, 640), (220, 710)),
                       fill="#dce6c5", outline=GREEN)
    plate.draw.line((330, 640, 390, 560, 460, 500, 535, 455, 630, 380),
                    fill=BLUE, width=13)
    plate.text((370, 490), "river", size=22, bold=True, fill=BLUE, anchor="mm")
    plate.draw.line((550, 650, 610, 570, 670, 645, 730, 555, 800, 630),
                    fill=CORAL, width=8)
    plate.text((690, 692), "mountain range", size=21, bold=True, fill=CORAL, anchor="mm")
    plate.draw.line((510, 330, 510, 692), fill=PLUM, width=5)
    plate.text((492, 350), "border", size=19, bold=True, fill=PLUM, anchor="ra")
    plate.dot((700, 440), 18, fill=GOLD_LIGHT, outline=GOLD, width=5)
    plate.text((730, 440), "capital", size=21, bold=True, fill=GOLD, anchor="lm")
    panel(plate, (975, 244, 1480, 770), fill=PAPER_LIGHT, outline=TEAL)
    for index, (head, detail) in enumerate([
        ("PLACE", "A location: coordinates or a named site."),
        ("REGION", "An area grouped by shared physical or human features."),
        ("COUNTRY", "A political territory; borders may change over time."),
        ("SYSTEM", "Rivers, climates and trade routes often cross borders."),
    ]):
        y = 274 + index * 116
        pill(plate, (1080, y + 30), head, color=(TEAL, GREEN, PLUM, BLUE)[index], size=17)
        box_text(plate, (1180, y, 1455, y + 76), detail, size=18, minimum=14, align="left")
    footer(plate, "Geography asks how physical places and human boundaries interact across scale.")


def _draw_anthropology(plate: Plate) -> None:
    """Show why archaeological context matters more than an isolated object."""

    panel(plate, (120, 240, 720, 780), fill=GOLD_LIGHT, outline=GOLD)
    pill(plate, (420, 276), "STRATIGRAPHIC CONTEXT", color=GOLD, size=18)
    layers = [
        (330, 430, "later layer", CORAL),
        (430, 535, "charcoal + pottery", PLUM),
        (535, 650, "stone tool + bone", TEAL),
        (650, 742, "earlier layer", BLUE),
    ]
    for top, bottom, label, color in layers:
        plate.draw.rectangle((170, top, 670, bottom), fill=color + "55", outline=color, width=3)
        plate.text((200, (top + bottom) / 2), label, size=22, bold=True, fill=color, anchor="lm")
    plate.arrow((685, 715), (685, 345), fill=INK_SOFT, width=5, head=18)
    plate.text((676, 330), "generally later ↑", size=18, bold=True, fill=INK_SOFT, anchor="ra")
    draw_box = (790, 270, 1478, 748)
    panel(plate, draw_box, fill=PAPER_LIGHT, outline=TEAL)
    for index, (head, detail) in enumerate([
        ("1  RECORD", "Position, association and disturbance before removing finds."),
        ("2  DATE", "Use stratigraphy, typology and absolute methods where suitable."),
        ("3  COMPARE", "Bones, artifacts, environment and living communities provide different evidence."),
        ("4  INFER", "Offer a bounded explanation and state uncertainty; an object alone cannot tell a whole culture."),
    ]):
        y0 = 296 + index * 108
        box_text(plate, (820, y0, 1035, y0 + 88), head, size=21, minimum=15,
                 bold=True, fill=(BLUE, TEAL, PLUM, CORAL)[index])
        box_text(plate, (1050, y0, 1445, y0 + 88), detail, size=18, minimum=13, align="left")
    footer(plate, "Invented, undisturbed layers: position gives relative order; object type alone does not establish age.")


def _draw_economic_theory(plate: Plate) -> None:
    """Three worked advanced-economics tools, not three prose summaries."""

    # Game theory: a numeric Prisoner's Dilemma payoff matrix.
    panel(plate, (120, 238, 550, 782), fill=BLUE_LIGHT, outline=BLUE)
    pill(plate, (335, 276), "GAME THEORY", color=BLUE, size=18)
    box_text(plate, (145, 306, 525, 346), "PAYOFFS = (A, B)", size=20,
             minimum=15, bold=True, fill=BLUE)
    box_text(plate, (242, 348, 512, 384), "PLAYER B", size=18,
             minimum=14, bold=True, fill=INK_SOFT)
    # Keep row headings in their own lane so the 800 px derivative remains
    # readable instead of letting the first payoff cell cover the text.
    matrix_x, matrix_y = 270, 390
    cell_w, cell_h = 120, 112
    for col, heading in enumerate(("COOPERATE", "DEFECT")):
        box_text(plate, (matrix_x + col * cell_w, matrix_y,
                         matrix_x + (col + 1) * cell_w, matrix_y + 48),
                 heading, size=16, minimum=12, bold=True, fill=BLUE)
    payoffs = (("3, 3", "0, 5"), ("5, 0", "1, 1"))
    for row, heading in enumerate(("A: COOPERATE", "A: DEFECT")):
        top = matrix_y + 52 + row * cell_h
        box_text(plate, (137, top, matrix_x - 14, top + cell_h), heading,
                 size=16, minimum=12, bold=True, fill=TEAL)
        for col in range(2):
            left = matrix_x + col * cell_w
            is_equilibrium = row == 1 and col == 1
            panel(plate, (left, top, left + cell_w - 6, top + cell_h - 6),
                  fill=GOLD_LIGHT if is_equilibrium else PAPER_LIGHT,
                  outline=GOLD if is_equilibrium else BLUE, radius=8, width=3)
            box_text(plate, (left + 5, top + 5, left + cell_w - 11,
                             top + cell_h - 11), payoffs[row][col], size=27,
                     minimum=18, bold=True, fill=GOLD if is_equilibrium else INK)
    box_text(plate, (145, 682, 525, 752),
             "Neither player gains by switching alone at defect / defect: Nash equilibrium (1, 1).",
             size=18, minimum=13, bold=True, fill=BLUE)

    # Econometrics: a causal graph exposing the back-door path.
    panel(plate, (575, 238, 1015, 782), fill=TEAL_LIGHT, outline=TEAL)
    pill(plate, (795, 276), "ECONOMETRICS", color=TEAL, size=18)
    plate.dot((795, 382), 50, fill=GOLD_LIGHT, outline=GOLD, width=5)
    plate.text((795, 382), "C", size=29, bold=True, anchor="mm")
    box_text(plate, (690, 302, 900, 332), "C = COMMON CAUSE", size=17,
             minimum=13, bold=True, fill=GOLD)
    plate.dot((680, 555), 52, fill=BLUE_LIGHT, outline=BLUE, width=5)
    plate.text((680, 555), "T", size=29, bold=True, anchor="mm")
    plate.dot((910, 555), 52, fill=CORAL + "22", outline=CORAL, width=5)
    plate.text((910, 555), "Y", size=29, bold=True, anchor="mm")
    plate.arrow((765, 421), (710, 507), fill=BLUE, width=6, head=18)
    plate.arrow((825, 421), (880, 507), fill=CORAL, width=6, head=18)
    plate.dashed_line((737, 555), (850, 555), fill=PLUM, width=6)
    box_text(plate, (744, 510, 844, 548), "effect?", size=16,
             minimum=12, bold=True, fill=PLUM)
    box_text(plate, (604, 620, 986, 752),
             "C → T and C → Y create a back-door association. Design plus explicit assumptions are needed to identify T → Y.",
             size=20, minimum=14, bold=True, fill=TEAL)

    # Behavioral economics: matched expected values in gain and loss domains.
    panel(plate, (1040, 238, 1480, 782), fill=CORAL + "18", outline=CORAL)
    pill(plate, (1260, 276), "BEHAVIORAL", color=CORAL, size=18)
    for top, heading, sure, gamble, equation, color, light in (
        (326, "GAIN DOMAIN", "sure gain $50", "50% gain $100; 50% $0",
         "EV: +$50 = +$50", TEAL, BLUE_LIGHT),
        (540, "LOSS DOMAIN", "sure lose $50", "50% lose $100; 50% $0",
         "EV: -$50 = -$50", CORAL, GOLD_LIGHT),
    ):
        panel(plate, (1066, top, 1454, top + 194), fill=light,
              outline=color, radius=12)
        box_text(plate, (1082, top + 8, 1438, top + 45), heading, size=19,
                 minimum=14, bold=True, fill=color)
        box_text(plate, (1082, top + 48, 1438, top + 96),
                 f"A  {sure}", size=20, minimum=14, bold=True)
        box_text(plate, (1082, top + 96, 1438, top + 144),
                 f"B  {gamble}", size=19, minimum=13, bold=True)
        box_text(plate, (1082, top + 145, 1438, top + 185), equation,
                 size=18, minimum=13, bold=True, fill=color)
    footer(plate, "Three toy examples: strategic payoffs, causal assumptions and hypothetical choices—not measured behavior.")


def _draw_community_tools(plate: Plate) -> None:
    for i, (heading, action, result, color, pale) in enumerate([
        ("HEALTH WORKER", "Listen and check", "Work out what care is needed", BLUE, BLUE_LIGHT),
        ("FIREFIGHTERS", "Protect and coordinate", "A trained team responds to danger", TEAL, TEAL_LIGHT),
        ("LIBRARIAN", "Find and check sources", "Help answer a question", GOLD, GOLD_LIGHT),
    ]):
        x = 120 + 465 * i
        panel(plate, (x, 240, x + 430, 780), fill=pale, outline=color)
        pill(plate, (x + 215, 285), heading, color=color, size=18)
        if i == 0:
            # A stethoscope's listening ends join a tube and chestpiece.
            plate.draw.arc((x + 95, 330, x + 245, 495), 0, 180, fill=INK_SOFT, width=12)
            for dx in (95, 245):
                plate.draw.line((x + dx, 412, x + dx, 362), fill=INK_SOFT, width=9)
                plate.dot((x + dx, 358), 10, fill=INK)
            plate.polyline([(x + 170, 495), (x + 170, 535), (x + 295, 535),
                            (x + 295, 465)], fill=BLUE, width=13)
            plate.dot((x + 295, 455), 27, fill=PAPER_LIGHT, outline=INK_SOFT, width=7)
            plate.dot((x + 295, 455), 15, fill=BLUE_LIGHT)
        elif i == 1:
            # Helmet and radio emphasize trained protection and teamwork,
            # not a universal fire-extinguishing technique for children.
            plate.draw.pieslice((x + 60, 355, x + 265, 530), 180, 360,
                                fill=GOLD_LIGHT, outline=GOLD, width=5)
            plate.draw.rounded_rectangle((x + 50, 435, x + 275, 461), radius=8,
                                         fill=GOLD_LIGHT, outline=GOLD, width=4)
            plate.draw.rounded_rectangle((x + 292, 398, x + 365, 555), radius=10,
                                         fill=INK_SOFT, outline=INK, width=4)
            plate.draw.line((x + 350, 397, x + 350, 340), fill=INK, width=8)
            plate.draw.rectangle((x + 306, 416, x + 351, 451), fill=TEAL_LIGHT)
            for y in (480, 492, 504):
                plate.draw.line((x + 309, y, x + 349, y), fill=PAPER_LIGHT, width=3)
        else:
            # An open book is being inspected, not treated as automatically true.
            plate.draw.polygon([(x + 65, 380), (x + 210, 405), (x + 355, 380),
                                (x + 355, 555), (x + 210, 575), (x + 65, 555)],
                               fill=PAPER_LIGHT, outline=GOLD)
            plate.draw.line((x + 210, 405, x + 210, 575), fill=GOLD, width=4)
            for y in (440, 465, 490, 515):
                plate.draw.line((x + 90, y, x + 180, y + 10), fill=INK_SOFT, width=3)
            plate.dot((x + 285, 450), 47, fill=GOLD_LIGHT, outline=INK_SOFT, width=7)
            plate.draw.line((x + 320, 484, x + 367, 531), fill=INK_SOFT, width=14)
            plate.text((x + 285, 450), "?", size=43, bold=True, anchor="mm")
        box_text(plate, (x + 20, 598, x + 410, 650), action, size=27, minimum=23, bold=True, fill=color)
        box_text(plate, (x + 25, 672, x + 405, 750), result, size=25, minimum=22)
    footer(plate, "Tools support a helper's knowledge. Helpers also listen and work together.")


def _draw_message_history(plate: Plate) -> None:
    for i, (heading, color, pale) in enumerate([
        ("BRITAIN, 1840", BLUE, BLUE_LIGHT),
        ("A PRESENT-DAY OPTION", TEAL, TEAL_LIGHT),
        ("HOW DO WE KNOW?", GOLD, GOLD_LIGHT),
    ]):
        x = 120 + i * 465
        panel(plate, (x, 240, x + 430, 780), fill=pale, outline=color)
        pill(plate, (x + 215, 285), heading, color=color, size=18)
        if i == 0:
            plate.draw.rectangle((x + 55, 360, x + 375, 535), fill=PAPER_LIGHT, outline=BLUE, width=4)
            plate.draw.rectangle((x + 304, 379, x + 354, 436), fill=INK)
            plate.text((x + 329, 408), "1d", size=22, fill=PAPER_LIGHT, anchor="mm")
            plate.text((x + 195, 465), "Meet at two.", size=26, anchor="mm")
            box_text(plate, (x + 25, 568, x + 405, 647), "A stamped letter travels through the post.", size=26, minimum=23, bold=True)
            box_text(plate, (x + 25, 673, x + 405, 750), "The Penny Black prepaid postage.", size=24, minimum=21)
        elif i == 1:
            plate.draw.rounded_rectangle((x + 128, 333, x + 302, 554), radius=18,
                                         fill=INK, outline=INK_SOFT, width=4)
            plate.draw.rounded_rectangle((x + 141, 354, x + 289, 523), radius=7, fill=PAPER_LIGHT)
            plate.draw.rounded_rectangle((x + 153, 394, x + 278, 456), radius=12, fill=TEAL_LIGHT)
            box_text(plate, (x + 155, 397, x + 276, 452), "Meet at 2.", size=25, minimum=22, pad=4)
            plate.dot((x + 215, 540), 6, fill=PAPER_LIGHT)
            box_text(plate, (x + 25, 568, x + 405, 647), "A phone message travels through a network.", size=26, minimum=23, bold=True)
            box_text(plate, (x + 25, 673, x + 405, 750), "It needs power and a connection.", size=24, minimum=21)
        else:
            plate.draw.rectangle((x + 75, 353, x + 355, 540), fill=PAPER_LIGHT, outline=GOLD, width=4)
            plate.draw.rectangle((x + 102, 380, x + 171, 458), fill=INK)
            plate.text((x + 136, 420), "1d", size=25, fill=PAPER_LIGHT, anchor="mm")
            for y in (397, 422, 447):
                plate.draw.line((x + 197, y, x + 321, y), fill=INK_SOFT, width=4)
            plate.text((x + 215, 503), "1840", size=27, bold=True, anchor="mm")
            box_text(plate, (x + 25, 568, x + 405, 647), "Surviving stamps and letters are evidence.", size=26, minimum=23, bold=True)
            box_text(plate, (x + 25, 673, x + 405, 750), "Museum records give dates and context.", size=24, minimum=21)
    footer(plate, "One example, not one story for everyone. People still send paper letters.")


MAP_SCALE_PIXELS = 100
MAP_SCALE_KM = 2
MAP_ROUTE = ((310, 650), (310, 350))


def _draw_worked_map(plate: Plate) -> None:
    panel(plate, (120, 240, 915, 780), fill=PAPER_LIGHT, outline=BLUE)
    pill(plate, (510, 277), "ONE INVENTED MAP", color=BLUE, size=20)
    # A straight route spans exactly three copies of the graphical scale bar.
    plate.polyline([(610, 310), (565, 395), (610, 480), (575, 570), (620, 680)],
                   fill=BLUE, width=17)
    plate.draw.line((*MAP_ROUTE[0], *MAP_ROUTE[1]), fill=CORAL, width=8)
    for y in range(350, 651, MAP_SCALE_PIXELS):
        plate.draw.line((290, y, 330, y), fill=CORAL, width=4)
    plate.draw.rectangle((294, 634, 326, 666), fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.dot((310, 350), 18, fill=TEAL_LIGHT, outline=TEAL, width=4)
    plate.text((365, 350), "Park", size=27, fill=TEAL, anchor="lm")
    plate.text((365, 650), "School", size=27, fill=GOLD, anchor="lm")
    plate.text((422, 485), "3 scale lengths", size=25, anchor="mm")
    plate.text((422, 520), "= 6 km", size=30, bold=True, anchor="mm", fill=CORAL)
    plate.arrow((790, 442), (790, 340), fill=INK, width=6, head=18)
    plate.text((790, 320), "N", size=27, bold=True, anchor="mm")
    plate.text((730, 495), "North is up", size=24, anchor="mm")
    plate.text((730, 527), "on this map.", size=24, anchor="mm")
    plate.draw.rectangle((260, 710, 260 + MAP_SCALE_PIXELS, 723), fill=INK)
    for x, value in ((260, "0"), (360, "2 km")):
        plate.draw.line((x, 703, x, 730), fill=INK, width=3)
        plate.text((x, 754), value, size=22, anchor="mm")
    plate.text((580, 724), "Use this bar, not screen centimetres.", size=23, anchor="mm")
    panel(plate, (960, 240, 1480, 780), fill=TEAL_LIGHT, outline=TEAL)
    pill(plate, (1220, 280), "READ THE KEY", color=TEAL, size=20)
    for y, name, color in ((370, "School", GOLD), (460, "Park", TEAL),
                            (550, "River", BLUE), (640, "Walking route", CORAL)):
        if name == "School":
            plate.draw.rectangle((1014, y - 16, 1046, y + 16), fill=GOLD_LIGHT, outline=color, width=4)
        elif name == "Park":
            plate.dot((1030, y), 18, fill=TEAL_LIGHT, outline=color, width=4)
        else:
            plate.draw.line((1005, y, 1055, y), fill=color, width=9)
        plate.text((1100, y), name, size=29, anchor="lm", fill=INK)
    box_text(plate, (990, 695, 1450, 754), "Symbols are defined for this map.", size=24, minimum=22)
    footer(plate, "The school-to-park route goes north. A map selects details; this is not a real place.")


_ITEMS = [
    spec(
        "hist.0.community", "People Who Help", 0, DOMAIN, "community-needs-helpers-plate",
        "A stethoscope, a protective helmet with a radio, and a book under a magnifying glass connect three helpers to their work: health workers listen and check, firefighters protect and coordinate, and librarians find and check sources.",
        "Community roles connect a need, relevant training and a public benefit; one person may help in several ways and helpers also rely on one another.",
        _draw_community_tools,
    ),
    spec(
        "hist.0.longago", "Long, Long Ago", 0, DOMAIN, "before-modern-tools-plate",
        "A schematic British stamped letter from 1840 and a present-day phone carry the same invented meeting message. A museum-record panel connects surviving stamps and letters to evidence about the past.",
        "The Penny Black introduced prepaid adhesive postage in Britain in 1840. This bounded example compares a physical postal route with an electronic network, not a universal replacement of old tools. Drawings are schematic, the message is invented, and paper letters remain in use.",
        _draw_message_history,
    ),
    spec(
        "hist.1.ancient", "Ancient Peoples", 1, DOMAIN, "river-city-chain-plate",
        "A schematic water channel reaches cereal plants; beside it a grain store and a marked tablet represent storage and record keeping. Opposing arrows link the two panels as interacting needs, not inevitable stages. The drawings do not reconstruct an excavated site or transcribe real writing.",
        "Ancient Egypt and Mesopotamia developed differently, but in both regions rivers, farming, specialization and administration interacted in the growth of cities.",
        _draw_ancient_resources,
    ),
    spec(
        "hist.1.maps", "Maps and Places", 1, DOMAIN, "map-reading-tools-plate",
        "An invented map shows a school south of a park, a river to their east, a north arrow and a symbol key. The straight school-to-park route spans three copies of the two-kilometre scale bar, giving six kilometres.",
        "Read direction, symbols and scale together. The graphical scale stays proportional when the picture resizes; physical screen centimetres do not. This invented map selects a few features and is not a navigation guide to a real place.",
        _draw_worked_map,
    ),
    timeline(
        "hist.1.inventions", "Great Inventions", 1, "inventions-needs-effects-plate",
        "A timeline links controlled fire in deep prehistory, wheel-and-axle transport around the fourth millennium BCE, and early writing around 3400 to 3200 BCE to the needs they addressed and the later practices they enabled.",
        "Controlled fire, wheel-and-axle systems and writing emerged through long collective histories; each changed what communities could cook, move or record.",
        [
            ("deep prehistory", "Controlled fire", "Heat, light, protection and cooking; evidence predates written history."),
            ("c. 4th millennium BCE", "Wheeled transport", "Wheels rolled loads rather than dragging them; rotating pottery tools had a different use."),
            ("c. 3400–3200 BCE", "Early writing", "Marks recorded goods and language; systems developed in more than one region."),
        ],
        "Inventions solve needs, depend on earlier knowledge and often evolve across many makers.",
        qualifier="APPROXIMATE DATES — DEVELOPMENT WAS GRADUAL AND REGIONAL",
    ),
    spec(
        "hist.2.civilizations", "Ancient Civilizations", 2, DOMAIN,
        "ancient-contemporaries-plate",
        "Four parallel rows place the Mediterranean, South Asia, East Asia and the Americas around 300 BCE, showing Hellenistic kingdoms and Rome, the Maurya Empire, the late Zhou and emerging Qin state, and varied Maya and Zapotec centers as contemporaries rather than rungs on one ladder.",
        "Ancient societies in several regions were contemporary. Comparing their political forms, exchange networks and evidence avoids treating world history as one civilization replacing another.",
        lambda plate: draw_tracks(
            plate,
            [
                ("MEDITERRANEAN", [("Hellenistic kingdoms", "Greek-speaking successor states"), ("Roman Republic", "expanding alliances and conquest")]),
                ("SOUTH ASIA", [("Maurya Empire", "large state; Ashoka later ruled c. 268–232 BCE"), ("regional networks", "trade, cities and diverse traditions")]),
                ("EAST ASIA", [("late Zhou", "competing states and philosophies"), ("Qin state", "one competing state; unification came later, in 221 BCE")]),
                ("AMERICAS", [("Maya centers", "developing cities in Mesoamerica"), ("Zapotec Monte Albán", "urban and regional power")]),
            ],
            "Contemporaneity makes comparison possible without ranking societies on a single scale.",
            direction="A CROSS-SECTION AROUND 300 BCE — DATES AND BOUNDARIES ARE APPROXIMATE",
        ),
    ),
    spec(
        "hist.2.middle-ages", "The Middle Ages", 2, DOMAIN,
        "medieval-connected-worlds-plate",
        "Five peer geographic tracks around 1000 CE show the Byzantine eastern Mediterranean, Islamic polities across Southwest Asia and North Africa, West African states, Song China in East Asia, and varied European polities as concurrent histories rather than one European age.",
        "The label Middle Ages fits European periodization best. Around 1000 CE, many connected regions had distinct states, faiths, cities and knowledge traditions.",
        lambda plate: draw_tracks(
            plate,
            [
                ("E. MEDITERRANEAN", [("Byzantine Empire", "Constantinople was an imperial and trading center"), ("regional networks", "Orthodox religious, artistic and diplomatic ties")]),
                ("SW ASIA + N. AFRICA", [("Islamic polities", "Abbasid, Fatimid and other powers"), ("knowledge networks", "translation, mathematics, medicine and trade")]),
                ("WEST AFRICA", [("regional states", "gold, salt and political authority"), ("trans-Saharan links", "merchants connected towns and courts")]),
                ("EAST ASIA", [("Song China", "large cities and expanding commerce"), ("knowledge + craft", "printing, scholarship and technologies")]),
                ("EUROPE", [("varied polities", "kingdoms, lordships and city powers"), ("social networks", "towns, monasteries, courts and trade")]),
            ],
            "Different calendars of change overlap; no region was waiting for another to become modern.",
            direction="AROUND 1000 CE — CONNECTED REGIONS, DIFFERENT PERIODIZATIONS",
        ),
    ),
    spec(
        "hist.2.exploration", "Exploration and Trade", 2, DOMAIN,
        "exchange-routes-consequences-plate",
        "A conceptual network links Silk Road routes, Indian Ocean sea lanes, Atlantic crossings after 1492 and local communities to connected exchange. Labels name goods and ideas alongside disease, conquest and coerced labor. Arrows show relationships, not geographic routes or equal benefits.",
        "Trade and exploration connected existing networks rather than empty spaces. Contact moved goods and knowledge, but also disease, violence, enslavement and imperial control.",
        lambda plate: draw_network(
            plate,
            ("CONNECTED EXCHANGE", "People, ports and overland hubs relay movement; few travelers cross an entire network."),
            [
                ("SILK ROAD ROUTES", "caravan stages moved textiles, horses, beliefs and techniques"),
                ("INDIAN OCEAN", "monsoon knowledge linked East Africa, Asia and the Middle East"),
                ("ATLANTIC AFTER 1492", "plants and animals moved with epidemic disease, conquest, enslavement and coerced labor"),
                ("LOCAL COMMUNITIES", "negotiated, resisted, adapted and bore unequal costs"),
            ],
            "Connection creates exchange and power asymmetries; map both benefits and harms.",
            edge_word="ROUTES MOVE MORE THAN GOODS",
        ),
    ),
    spec(
        "hist.2.geography", "World Geography", 2, DOMAIN,
        "geographic-scale-layers-plate",
        "An invented map shows a river crossing a political border, a mountain range east of it and a capital on one side. Adjacent definitions distinguish place, region, country and system. The river line is not a drainage-basin boundary, and the map does not depict real countries.",
        "Countries and capitals are political geography; rivers, mountains and climates are physical geography. Their boundaries often cross and influence one another.",
        _draw_geography,
    ),
    spec(
        "hist.2.civics-intro", "Rules and Fairness", 2, DOMAIN, "fair-rule-review-plate",
        "A shared swing stands beside an invented six-minute schedule: Ari from zero to two, Bo from two to four and Cam from four to six minutes. Equal-width blocks represent equal time, but labels require checking safety, access and usable turns before judging fairness.",
        "A fair rule starts from a shared problem, protects relevant rights, assigns responsibilities and can be reviewed when its effects are unequal or unexpected.",
        _draw_fair_turns,
    ),
    timeline(
        "hist.3.early-modern", "Renaissance to Revolution", 3,
        "ideas-authority-revolution-plate",
        "A dated sequence links Renaissance humanism and print, the Reformation after 1517, seventeenth-century scientific inquiry, Enlightenment debate and the American, Haitian and French Revolutions, with cautious labels such as circulated and influenced rather than a single-cause arrow.",
        "Print, religious conflict, new inquiry and arguments about authority circulated across institutions and empires; they influenced revolutions without mechanically causing them.",
        [
            ("c. 1400s", "European humanism", "Humanist study and expanding print widened networks in Europe; printing had earlier Asian histories."),
            ("from 1517", "Reformation", "Religious authority fractured amid political and social conflict."),
            ("1600s", "Scientific inquiry", "Observation, mathematics and institutions reshaped claims about nature."),
            ("1700s", "Enlightenment debate", "Writers contested sovereignty, rights and toleration."),
            ("1770s–1804", "Atlantic revolutions", "American, French and Haitian upheavals made different claims and exclusions."),
        ],
        "Ideas matter through people, institutions and material conflicts—not as an automatic domino chain.",
        qualifier="OVERLAPPING DEVELOPMENTS — ARROWS SHOW INFLUENCE, NOT INEVITABILITY",
    ),
    spec(
        "hist.3.industrial", "The Industrial Revolution", 3, DOMAIN,
        "industrialization-branching-effects-plate",
        "A source card combines fossil energy, machines, capital and labor organization, then branches to greater output and cheaper goods, urbanization and wage work, pollution and extraction, and labor conflict followed by uneven reform.",
        "Industrialization raised productive capacity while redistributing work, wealth, health and environmental costs. Its effects differed across class, gender, place and empire.",
        lambda plate: draw_branch(
            plate,
            ("INDUSTRIAL SYSTEM", "Fossil energy + machinery + investment + reorganized labor and transport"),
            [
                ("MORE OUTPUT", "Factories and mechanization increased the quantity and lowered the cost of many goods."),
                ("URBANIZATION", "Workers moved toward industrial towns; time discipline and wage labor expanded."),
                ("EXTERNAL COSTS", "Coal smoke, dangerous work and resource extraction imposed harms not in the sale price."),
                ("CONFLICT + REFORM", "Workers organized; regulation and public health improved some conditions unevenly."),
            ],
            "Productivity gains and social costs belong in the same causal account.",
            relation="RESHAPED",
        ),
    ),
    timeline(
        "hist.3.modern-world", "The Modern World", 3, "modern-world-branches-plate",
        "A selected timeline shows World War I in 1914–1918, interwar crisis, World War II in 1939–1945, a major decolonization wave in the 1940s–1970s and the overlapping Cold War around 1947–1991. Decolonization explicitly began earlier and continued later.",
        "World war, imperial crisis, decolonization and superpower rivalry overlapped. Newly independent states had their own projects and were not merely pieces on a Cold War board.",
        [
            ("1914–1918", "World War I", "Mass mobilization and imperial war destabilized states and borders."),
            ("1918–1939", "Interwar crisis", "Uneven recovery, depression, fascism and anticolonial organizing."),
            ("1939–1945", "World War II", "Global war and genocide transformed power and legitimacy."),
            ("1940s–1970s", "Decolonization wave", "A major wave of independence; struggles began earlier and continued later."),
            ("c. 1947–1991", "Cold War", "US–Soviet rivalry intersected with local and postcolonial conflicts."),
        ],
        "Period labels overlap; follow whose agency and which geography each label centers.",
        qualifier="OVERLAPPING GLOBAL PROCESSES — NOT ONE SIMPLE SEQUENCE",
    ),
    flow(
        "hist.3.civics", "Government & Citizenship", 3, "law-making-feedback-plate",
        "A five-step example of constitutional lawmaking runs from citizen demands and elections through a drafted bill, committee debate and amendment, legislative vote and executive action, then court review and public feedback, with a note that systems vary.",
        "In one common constitutional pattern, citizens, legislatures, executives and courts constrain and influence lawmaking; exact powers differ by country and constitution.",
        [
            ("PUBLIC INPUT", "Petitions, organizing, parties and elections put problems on an agenda."),
            ("DRAFT BILL", "Representatives translate a proposal into legal text."),
            ("DEBATE + AMEND", "Committees hear evidence; legislators bargain and revise."),
            ("VOTE + EXECUTIVE", "Legislature passes or rejects; executive may sign or veto."),
            ("REVIEW + FEEDBACK", "Courts may test legality; citizens observe effects and seek change."),
        ],
        "One constitutional pattern, not a universal sequence: powers and procedures differ by country.",
    ),
    spec(
        "hist.3.economics-intro", "How Economies Work", 3, DOMAIN,
        "supply-demand-worked-market-plate",
        "A price-versus-quantity graph has an upward supply curve, a downward demand curve and a marked crossing; side cards explain the surplus above and shortage below that market-clearing price.",
        "Supply and demand describe planned quantities at possible prices. Their crossing is a useful model, while real outcomes also depend on institutions, bargaining and curve shifts.",
        _draw_supply_demand,
    ),
    timeline(
        "hist.3.world-religions", "World Religions", 3, "religious-histories-overlap-plate",
        "An approximate origins timeline marks diverse Hindu traditions before the first millennium BCE, Israelite and Jewish traditions in the first millennium BCE, Buddhism around the fifth century BCE, Christianity in the first century CE, Islam in the seventh century CE and Sikh tradition from the fifteenth century, ending with all as living changing traditions.",
        "Religious traditions have layered origins, internal diversity and histories of exchange. A date can orient a learner but cannot summarize beliefs or define a living community.",
        [
            ("before 1st millennium BCE", "Hindu traditions", "diverse South Asian roots; no single founding event"),
            ("1st millennium BCE", "Jewish traditions", "Israelite origins and later rabbinic development"),
            ("c. 5th c. BCE", "Buddhism", "teachings associated with Siddhartha Gautama; many schools"),
            ("1st c. CE", "Christianity", "emerged in Jewish Roman contexts; many later traditions"),
            ("7th c. CE", "Islam", "Qur'anic revelation and early Muslim community; diverse traditions"),
            ("15th c. CE", "Sikh tradition", "began with Guru Nanak and the Sikh Gurus in Punjab"),
        ],
        "Origins are reference points; every tradition continues to change across places and communities.",
        qualifier="APPROXIMATE ORIGINS — ALL SHOWN AS LIVING, INTERNALLY DIVERSE TRADITIONS",
    ),
    spec(
        "hist.4.historiography", "Historiography", 4, DOMAIN,
        "sources-method-interpretation-plate",
        "A diary, newspaper and payroll register converge on a method card labeled provenance, context, corroboration and silences, which leads to a qualified interpretation; the conclusion notes that new evidence can revise it.",
        "Historians do not simply collect facts. They ask who produced each source, for whom, under what conditions, what agrees, and whose experience is missing.",
        lambda plate: draw_evidence(
            plate,
            [
                ("DIARY", "close perspective; selective memory and private purpose"),
                ("NEWSPAPER", "public account; editorial choices and political context"),
                ("PAYROLL", "systematic names and wages; excludes unpaid work"),
            ],
            ("SOURCE CRITICISM", "Check provenance, context, corroboration and silences."),
            ("QUALIFIED ACCOUNT", "Best explanation for the available evidence—not the past itself."),
            "New evidence can revise an interpretation without making every interpretation equally plausible.",
        ),
    ),
    spec(
        "hist.4.political-sci", "Political Science", 4, DOMAIN,
        "politics-levels-network-plate",
        "A reciprocal network puts a public policy at the center and connects institutions, ideology, citizens and groups, and international constraints, showing that the same policy is shaped at several analytical levels.",
        "Political science connects institutions, interests, ideas and international relations. No single level explains a policy outcome by itself.",
        lambda plate: draw_network(
            plate,
            ("PUBLIC POLICY", "Example: an energy transition changes rules, costs and benefits."),
            [
                ("INSTITUTIONS", "constitutions, elections, courts and administrative capacity"),
                ("IDEOLOGIES", "competing accounts of liberty, equality, order and authority"),
                ("CITIZENS + GROUPS", "preferences, identities, movements, firms and organized interests"),
                ("INTERNATIONAL SYSTEM", "alliances, trade, law and power constrain choices"),
            ],
            "Explain an outcome by tracing interactions across levels, then compare rival explanations.",
            edge_word="POWER AND FEEDBACK CROSS LEVELS",
        ),
    ),
    spec(
        "hist.4.economics", "Economics", 4, DOMAIN,
        "micro-macro-feedback-plate",
        "A conceptual network links households, firms, policy at both micro and macro scales, and economy-wide aggregates. The footer distinguishes GDP, which includes some nonmarket production, from total wellbeing and sustainability. Arrows represent relationships, not measured flow sizes.",
        "Microeconomics studies choices and markets; macroeconomics studies aggregates and policy. Individual decisions build aggregates, while aggregate conditions feed back into individual options.",
        lambda plate: draw_network(
            plate,
            ("ECONOMY", "Flows of work, goods, income, credit, taxes and public services."),
            [
                ("HOUSEHOLDS — MICRO", "labor, consumption, saving and constraints"),
                ("FIRMS — MICRO", "production, hiring, investment and pricing"),
                ("POLICY — BOTH SCALES", "market rules and incentives; aggregate tax and spending effects"),
                ("AGGREGATES — MACRO", "output, inflation, unemployment and external balance"),
            ],
            "GDP measures production, including some nonmarket output—not total wellbeing or sustainability.",
            edge_word="INDIVIDUAL CHOICES ↔ AGGREGATE CONDITIONS",
        ),
    ),
    spec(
        "hist.4.social-history", "Social & Cultural History", 4, DOMAIN,
        "history-from-below-evidence-plate",
        "Oral histories, pay records, domestic objects and official files converge through comparison and attention to power and silence, yielding an account of ordinary work, family and collective action rather than a history based only on leaders.",
        "Social and cultural history reconstruct ordinary lives by combining evidence made for different purposes, including sources that institutions preserved unevenly.",
        lambda plate: draw_evidence(
            plate,
            [
                ("ORAL HISTORY", "remembered experience; interviewer and later context matter"),
                ("PAY + CENSUS RECORDS", "patterns of work and residence; official categories constrain"),
                ("OBJECTS + SPACES", "domestic labor, consumption and embodied practice"),
                ("OFFICIAL FILES", "state and employer viewpoints; authority leaves a large archive"),
            ],
            ("READ ACROSS", "Compare scale and viewpoint; ask who is absent and why."),
            ("CHANGE FROM BELOW", "A bounded history of everyday life, culture and collective action."),
            "Adding sources changes not just detail but whose actions count as historical explanation.",
        ),
    ),
    spec(
        "hist.4.geopolitics", "The Contemporary World", 4, DOMAIN,
        "global-interdependence-network-plate",
        "A conceptual network links a hypothetical port disruption to supply chains, security, energy and climate, and international institutions. Arrows suggest possible feedback relationships, not measured magnitudes or a forecast about a named event.",
        "Contemporary geopolitics joins territorial power to interdependence. Trade, security, climate and institutions transmit shocks, but states and communities experience them unequally.",
        lambda plate: draw_network(
            plate,
            ("PORT DISRUPTION", "A local delay changes shipping time, costs and access to key inputs."),
            [
                ("SUPPLY CHAINS", "firms reroute; shortages and prices move across borders"),
                ("SECURITY", "states protect routes, bargain and interpret strategic risk"),
                ("ENERGY + CLIMATE", "fuel choices alter dependence and shared external costs"),
                ("INSTITUTIONS", "treaties and organizations coordinate, constrain and sometimes fail"),
            ],
            "Globalization spreads opportunity and vulnerability through networks structured by unequal power.",
            edge_word="A SHOCK PROPAGATES — RESPONSES FEED BACK",
        ),
    ),
    spec(
        "hist.4.law", "Law and Justice", 4, DOMAIN,
        "rule-of-law-contrast-plate",
        "Two comparison columns contrast rule of law, including public rules, human rights, independent review and equal protection, with rule by power, including arbitrary exceptions, weak review and unequal treatment. This is a conceptual comparison, not a depiction of a courtroom or jurisdiction-specific procedure.",
        "Law can restrain power or become its instrument. Public rules, procedural fairness, independent review and effective remedies are central rule-of-law safeguards.",
        _draw_rule_of_law,
    ),
    spec(
        "hist.5.economic-theory", "Advanced Economics", 5, DOMAIN,
        "economic-theory-toolkit-plate",
        "Three worked panels show a Prisoner's Dilemma payoff matrix with defect–defect as the Nash equilibrium, a causal graph where common cause C confounds treatment T and outcome Y, and matched sure-versus-gamble choices with expected value plus or minus fifty dollars in separate gain and loss domains.",
        "Advanced economics asks how strategic interaction, causal evidence and psychologically realistic behavior alter predictions. Each tool answers a different kind of question.",
        _draw_economic_theory,
    ),
    flow(
        "hist.5.political-theory", "Political Philosophy", 5,
        "veil-of-ignorance-institutions-plate",
        "A four-step Rawlsian thought experiment removes knowledge of one's future social position, asks participants to choose equal basic liberties and rules for inequality, builds institutions from those principles, and checks the position of the least advantaged.",
        "The veil of ignorance is a test of impartial justification: choose principles without knowing which social position you will occupy, then examine their institutional effects.",
        [
            ("ORIGINAL POSITION", "People reason together under fair bargaining conditions."),
            ("VEIL OF IGNORANCE", "No one knows their class, race, sex, abilities or conception of the good."),
            ("CHOOSE PRINCIPLES", "Rawls argues for equal basic liberties and tightly constrained inequality."),
            ("TEST INSTITUTIONS", "Fair opportunity; inequalities must give the greatest benefit to the least advantaged."),
        ],
        "A thought experiment clarifies a principle; rival theories still contest liberty, equality and desert.",
    ),
    spec(
        "hist.5.anthropology", "Anthropology & Archaeology", 5, DOMAIN,
        "archaeological-context-inference-plate",
        "An invented undisturbed stratigraphic section labels four layers, including charcoal and pottery above stone tools and bone in this example only. An upward arrow indicates generally later deposits. Adjacent steps cover context, dating, comparison and bounded inference; object type alone does not determine age.",
        "Archaeology builds claims from provenience, association, dating and comparison. Anthropology adds biological, linguistic, social and community knowledge while respecting uncertainty and descendant communities.",
        _draw_anthropology,
    ),
    spec(
        "hist.5.world-systems", "World & Global History", 5, DOMAIN,
        "comparative-history-tracks-plate",
        "Three parallel tracks compare Indian Ocean exchange, Atlantic-centered empires and industrial-global networks across 1000–1500, 1500–1800 and 1800–present, with movement, coercion and ecological effects named in each phase.",
        "Global history compares connections and divergence across a shared time axis. Systems shift as power, labor regimes, technologies and environments change.",
        lambda plate: draw_tracks(
            plate,
            [
                ("INDIAN OCEAN", [("1000–1500", "monsoon ports; merchant diasporas"), ("1500–1800", "armed European entry into older networks"), ("1800–present", "steam, empire and container shipping")]),
                ("ATLANTIC", [("1000–1500", "regional seafaring; sustained transatlantic expansion from 1492"), ("1500–1800", "colonization, slave trade and Columbian exchange"), ("1800–present", "emancipation, migration and unequal trade")]),
                ("ENERGY + INDUSTRY", [("1000–1500", "biomass-based production"), ("1500–1800", "commercial expansion and proto-industry"), ("1800–present", "fossil energy, factories and planetary effects")]),
            ],
            "Comparison explains changing relationships; it does not rank civilizations on a universal ladder.",
            direction="SHARED PERIODS, DIFFERENT REGIONAL TRAJECTORIES AND CONNECTIONS",
        ),
    ),
    spec(
        "hist.5.frontier", "Debates and Frontiers", 5, DOMAIN,
        "historical-causal-debate-plate",
        "Competing hypotheses about whether a railway caused town growth are tested against maps, census records and route plans, then passed through comparison, chronology and counterfactual reasoning to a qualified claim that can be revised.",
        "A frontier debate becomes productive when rival explanations imply different evidence. Quantification can sharpen comparison, but measurement choices and archival silences remain historical problems.",
        lambda plate: draw_evidence(
            plate,
            [
                ("HYPOTHESIS A", "rail access lowered transport costs and attracted activity"),
                ("HYPOTHESIS B", "the route followed towns already growing for other reasons"),
                ("EVIDENCE", "dated maps, censuses, prices, petitions and planned-but-unbuilt routes"),
            ],
            ("IDENTIFICATION", "Establish timing; compare plausible controls and counterfactuals; test sensitivity."),
            ("BOUNDED CAUSAL CLAIM", "Estimate what the railway changed, for whom, where and with what uncertainty."),
            "Cliometrics adds tests to source criticism; it does not turn a contested past into certainty.",
        ),
    ),
]


SPECS: Dict[str, Spec] = {item["id"]: item for item in _ITEMS}
