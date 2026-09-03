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
             "Predictability • hearing • appeal • equal protection"),
            ("RULE BY POWER", "A ruler uses legal forms selectively while remaining above meaningful constraint.",
             "Arbitrary exceptions • weak review • unequal treatment"),
        ],
        "A legal system approaches justice when power itself is answerable to public rules.",
        relation="THE SAME COURTROOM — TWO DIFFERENT RELATIONSHIPS TO POWER",
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
    plate.text((446, 531), "river basin", size=22, bold=True, fill=BLUE, anchor="mm")
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
    footer(plate, "Archaeological meaning comes from provenience, association and method—not treasure alone.")


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
    footer(plate, "Strategy, causal identification and observed choice answer different economic questions.")


_ITEMS = [
    compare(
        "hist.0.community", "People Who Help", 0, "community-needs-helpers-plate",
        "Three linked examples pair a community need with a trained helper and the result: illness with a health worker and care, a fire with firefighters and safety, and a question with a librarian and reliable information.",
        "Community roles connect a need, relevant training and a public benefit; one person may help in several ways and helpers also rely on one another.",
        [
            ("ILLNESS", "Health worker assesses and treats.", "Need → relevant skill → care"),
            ("FIRE", "Firefighters contain danger and rescue.", "Need → coordinated response → safety"),
            ("QUESTION", "Librarian helps locate and evaluate sources.", "Need → information skill → knowledge"),
        ],
        "Helpers match knowledge and cooperation to a community need.",
        relation="NEED → TRAINED HELPER → COMMUNITY OUTCOME",
    ),
    compare(
        "hist.0.longago", "Long, Long Ago", 0, "before-modern-tools-plate",
        "Three panels compare sending a message and moving a load long ago with today: a carried letter versus a phone call, and a handcart or animal-powered cart versus a motor vehicle, followed by a panel naming evidence sources.",
        "People long ago solved familiar needs with different tools. Historians learn about those tools from objects, pictures, buildings and stories rather than by guessing.",
        [
            ("SEND A MESSAGE", "Then: messenger and letter. Now: phone or network.", "Same need; different speed, reach and infrastructure"),
            ("MOVE A LOAD", "Then: people, animals and carts. Now: engines and vehicles.", "Same task; different energy source and capacity"),
            ("HOW WE KNOW", "Artifacts, images, buildings and accounts survive unevenly.", "Evidence supports an inference; gaps remain"),
        ],
        "Changing tools alter how a task is done, while evidence lets us reconstruct the change.",
    ),
    flow(
        "hist.1.ancient", "Ancient Peoples", 1, "river-city-chain-plate",
        "A four-step chain shows seasonal rivers and managed water supporting crops, harvest surpluses supporting specialized work, growing settlements needing coordination, and administrators using records and writing, with Egypt and Mesopotamia named as different river societies.",
        "Ancient Egypt and Mesopotamia developed differently, but in both regions rivers, farming, specialization and administration interacted in the growth of cities.",
        [
            ("RIVERS + WATER", "Nile and Tigris–Euphrates communities adapted to different floods and landscapes."),
            ("FOOD SURPLUS", "Stored harvests could support some people doing work beyond farming."),
            ("SPECIALIZATION", "Craft, trade, building, ritual and defense linked larger settlements."),
            ("RECORDS", "Accounting and writing helped institutions track goods, labor and decisions."),
        ],
        "A city is not caused by one invention: environment, labor, exchange and institutions interact.",
    ),
    compare(
        "hist.1.maps", "Maps and Places", 1, "map-reading-tools-plate",
        "Three panels explain a map's north arrow, symbol legend and scale: an upward route gives direction, a blue line and star are decoded by a legend, and one map centimeter corresponds to two real kilometers.",
        "Direction, a legend and scale turn marks on a page into spatial claims. A map selects information for a purpose and cannot show everything.",
        [
            ("DIRECTION", "A north arrow or compass rose orients the page; up is north only when declared.", "Route: school → north → park"),
            ("LEGEND", "Symbols stand for features: blue line = river; ★ = capital.", "Read the key before interpreting marks"),
            ("SCALE", "1 cm on this example map represents 2 km on the ground.", "3 cm route → 6 km actual distance"),
        ],
        "Read orientation, legend and scale together before drawing a conclusion from a map.",
        relation="THREE TOOLS TURN MAP MARKS INTO MEANING",
    ),
    timeline(
        "hist.1.inventions", "Great Inventions", 1, "inventions-needs-effects-plate",
        "A timeline links controlled fire in deep prehistory, wheel-and-axle transport around the fourth millennium BCE, and early writing around 3400 to 3200 BCE to the needs they addressed and the later practices they enabled.",
        "Controlled fire, wheel-and-axle systems and writing emerged through long collective histories; each changed what communities could cook, move or record.",
        [
            ("deep prehistory", "Controlled fire", "Heat, light, protection and cooking; evidence predates written history."),
            ("c. 4th millennium BCE", "Wheel + axle", "Rotating parts reduced friction for pottery and transport in some regions."),
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
                ("EAST ASIA", [("late Zhou", "competing states and philosophies"), ("Qin unification", "unified China in 221 BCE; short-lived dynasty")]),
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
        "A reciprocal network links Silk Road routes, Indian Ocean sea lanes, Atlantic crossings and local ports to a central exchange system; labels name movement of goods and ideas as well as disease, conquest and coerced labor.",
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
        "A layered map shows a river basin and mountain range crossing a political border, a capital inside one country, and definitions of place, region, country and system at the side.",
        "Countries and capitals are political geography; rivers, mountains and climates are physical geography. Their boundaries often cross and influence one another.",
        _draw_geography,
    ),
    flow(
        "hist.2.civics-intro", "Rules and Fairness", 2, "fair-rule-review-plate",
        "A four-step playground example moves from a shared problem of three children and one swing to hearing needs, agreeing on timed turns with equal access, and reviewing whether the rule works, linking rights to responsibilities.",
        "A fair rule starts from a shared problem, protects relevant rights, assigns responsibilities and can be reviewed when its effects are unequal or unexpected.",
        [
            ("SHARED PROBLEM", "Three children want one swing at the same time."),
            ("HEAR NEEDS", "Each person gets a voice; safety and access matter."),
            ("MAKE A RULE", "Take timed turns: right to access ↔ responsibility to yield."),
            ("REVIEW EFFECTS", "Did everyone get a real chance? Adjust for relevant needs."),
        ],
        "Fairness is not blind sameness: a rule should address the reason people differ.",
    ),
    timeline(
        "hist.3.early-modern", "Renaissance to Revolution", 3,
        "ideas-authority-revolution-plate",
        "A dated sequence links Renaissance humanism and print, the Reformation after 1517, seventeenth-century scientific inquiry, Enlightenment debate and the American, Haitian and French Revolutions, with cautious labels such as circulated and influenced rather than a single-cause arrow.",
        "Print, religious conflict, new inquiry and arguments about authority circulated across institutions and empires; they influenced revolutions without mechanically causing them.",
        [
            ("c. 1400s", "Renaissance + print", "Humanist study and movable-type print widened some intellectual networks."),
            ("from 1517", "Reformation", "Religious authority fractured amid political and social conflict."),
            ("1600s", "Scientific inquiry", "Observation, mathematics and institutions reshaped claims about nature."),
            ("1700s", "Enlightenment debate", "Writers contested sovereignty, rights and toleration."),
            ("1776–1804", "Atlantic revolutions", "American, French and Haitian upheavals made different claims and exclusions."),
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
        "A timeline shows World War I from 1914 to 1918, crisis and fascism in the interwar years, World War II from 1939 to 1945, and places decolonization from the 1940s to 1970s beside the overlapping Cold War from about 1947 to 1991.",
        "World war, imperial crisis, decolonization and superpower rivalry overlapped. Newly independent states had their own projects and were not merely pieces on a Cold War board.",
        [
            ("1914–1918", "World War I", "Mass mobilization and imperial war destabilized states and borders."),
            ("1918–1939", "Interwar crisis", "Uneven recovery, depression, fascism and anticolonial organizing."),
            ("1939–1945", "World War II", "Global war and genocide transformed power and legitimacy."),
            ("1940s–1970s", "Decolonization", "Independence movements dismantled formal empires through varied struggles."),
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
        "Democracy is an ongoing feedback system, not only a vote on election day.",
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
        "A reciprocal network places an economy at the center and links households, firms, government and macroeconomic aggregates, distinguishing individual choices from output, inflation and unemployment and noting that GDP is not total wellbeing.",
        "Microeconomics studies choices and markets; macroeconomics studies aggregates and policy. Individual decisions build aggregates, while aggregate conditions feed back into individual options.",
        lambda plate: draw_network(
            plate,
            ("ECONOMY", "Flows of work, goods, income, credit, taxes and public services."),
            [
                ("HOUSEHOLDS — MICRO", "labor, consumption, saving and constraints"),
                ("FIRMS — MICRO", "production, hiring, investment and pricing"),
                ("GOVERNMENT — MACRO", "tax, spending, regulation and redistribution"),
                ("AGGREGATES — MACRO", "output, inflation, unemployment and external balance"),
            ],
            "GDP tracks priced production, not the complete distribution, sustainability or quality of life.",
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
        "A reciprocal network links a port disruption at the center to trade and supply chains, security alliances, climate and energy, and international institutions, showing how a local shock propagates unevenly across borders.",
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
        "Two courtroom columns contrast rule of law, with published rules, hearing, equal protection and appeal, against rule by power, with arbitrary exceptions, weak review and unequal treatment.",
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
            ("TEST INSTITUTIONS", "Ask whether offices are fairly open and inequalities benefit the least advantaged."),
        ],
        "A thought experiment clarifies a principle; rival theories still contest liberty, equality and desert.",
    ),
    spec(
        "hist.5.anthropology", "Anthropology & Archaeology", 5, DOMAIN,
        "archaeological-context-inference-plate",
        "A stratigraphic trench places later material above charcoal and pottery and earlier stone tools and bone, beside a four-step method of recording context, dating, comparing evidence and making a bounded inference.",
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
                ("ATLANTIC", [("1000–1500", "regional seas before sustained ocean crossing"), ("1500–1800", "colonization, slave trade and Columbian exchange"), ("1800–present", "emancipation, migration and unequal trade")]),
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
