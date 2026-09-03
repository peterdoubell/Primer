"""Lesson-specific deterministic chemistry plates."""

from __future__ import annotations

from typing import Mapping

from . import core as _core
from .core import BLUE, CORAL, GOLD, GREEN, PLUM, TEAL, science_spec


def S(node_id, title, stage, layout, content, alt, caption):
    return science_spec(node_id, title, stage, "chemistry", layout, content, alt, caption)


def _phase_lobe(plate, box, sign, *, fill, outline):
    """Draw one explicitly signed orbital phase lobe."""
    plate.draw.ellipse(box, fill=_core.hex_rgba(fill, 205), outline=outline, width=5)
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    plate.text((cx, cy), sign, size=30, bold=True, fill=outline, anchor="mm")


def _draw_worked_mo(plate, content: Mapping[str, object]) -> None:
    """Worked H2 molecular-orbital energy construction with visible phase."""
    plate.draw.rounded_rectangle(
        (120, 220, 1480, 790), radius=25,
        fill=_core.hex_rgba(_core.PAPER_LIGHT, 235), outline=PLUM, width=4,
    )

    # Energy ordering and column headings.
    plate.arrow((165, 745), (165, 265), fill=_core.INK, width=5, head=18)
    plate.text((150, 255), "E", size=24, bold=True, anchor="mm")
    plate.label((320, 260), "H 1s_A", size=18, fill=BLUE)
    plate.label((800, 260), "H₂ MO LEVELS", size=18, fill=PLUM)
    plate.label((1280, 260), "H 1s_B", size=18, fill=BLUE)

    # Standard correlation lines: two equal-energy AOs combine into one MO
    # below and one MO above their energy.
    for start, end in (
        ((400, 500), (650, 320)), ((400, 500), (650, 625)),
        ((1200, 500), (950, 320)), ((1200, 500), (950, 625)),
    ):
        plate.draw.line((*start, *end), fill=_core.GRID, width=4)
    plate.draw.line((240, 500, 400, 500), fill=BLUE, width=7)
    plate.draw.line((1200, 500, 1360, 500), fill=BLUE, width=7)
    plate.draw.line((650, 320, 950, 320), fill=CORAL, width=8)
    plate.draw.line((650, 625, 950, 625), fill=GREEN, width=8)
    plate.arrow((385, 495), (385, 462), fill=PLUM, width=4, head=11)
    plate.arrow((1215, 495), (1215, 462), fill=PLUM, width=4, head=11)

    # The two 1s basis functions use the same displayed phase convention.
    _phase_lobe(plate, (275, 455, 365, 545), "+", fill=_core.BLUE_LIGHT, outline=BLUE)
    _phase_lobe(plate, (1235, 455, 1325, 545), "+", fill=_core.BLUE_LIGHT, outline=BLUE)
    plate.text((320, 565), "same AO energy", size=17, fill=_core.INK_SOFT, anchor="mm")
    plate.text((1280, 565), "same AO energy", size=17, fill=_core.INK_SOFT, anchor="mm")

    # Out-of-phase subtraction: two separated lobes and an explicit node.
    plate.text((800, 295), "σ*(1s) = 1s_A − 1s_B  ·  HIGHER", size=21,
               bold=True, fill=CORAL, anchor="mm")
    _phase_lobe(plate, (690, 350, 790, 425), "+", fill=_core.CORAL_LIGHT, outline=CORAL)
    _phase_lobe(plate, (810, 350, 910, 425), "−", fill=_core.BLUE_LIGHT, outline=BLUE)
    plate.draw.line((800, 342, 800, 432), fill=_core.INK, width=4)
    plate.text((800, 449), "opposite phase → internuclear node", size=18,
               bold=True, fill=_core.INK_SOFT, anchor="mm")

    # In-phase addition: continuous density spans both nuclei.  The two plus
    # signs expose the common phase; black dots identify the nuclei.
    plate.text((800, 575), "σ(1s) = 1s_A + 1s_B  ·  LOWER", size=21,
               bold=True, fill=GREEN, anchor="mm")
    plate.arrow((775, 620), (775, 590), fill=PLUM, width=4, head=11)
    plate.arrow((825, 590), (825, 620), fill=PLUM, width=4, head=11)
    plate.draw.rounded_rectangle(
        (675, 650, 925, 725), radius=38,
        fill=_core.hex_rgba(_core.GREEN_LIGHT, 215), outline=GREEN, width=5,
    )
    plate.text((745, 687), "+", size=27, bold=True, fill=GREEN, anchor="mm")
    plate.text((855, 687), "+", size=27, bold=True, fill=GREEN, anchor="mm")
    for nx in (775, 825):
        plate.draw.ellipse((nx - 7, 680, nx + 7, 694), fill=_core.INK)
    plate.text((800, 755), "same-phase density between nuclei  ·  H₂ bond order = 1", size=19,
               bold=True, fill=_core.INK, anchor="mm")
    _core._footer(plate, str(content["footer"]))


_BASE_LAYERS_RENDERER = getattr(
    _core, "_chemistry_base_layers_renderer", _core.RENDERERS["layers"]
)
_core._chemistry_base_layers_renderer = _BASE_LAYERS_RENDERER


def _draw_chemistry_layers(plate, content: Mapping[str, object]) -> None:
    if content.get("mode") == "mo-energy":
        _draw_worked_mo(plate, content)
    else:
        _BASE_LAYERS_RENDERER(plate, content)


_core.RENDERERS["layers"] = _draw_chemistry_layers


_LIST = [
    S("chem.0.materials", "Stuff Around Us", 0, "matrix", {
        "columns":["STATE HERE", "OBSERVABLE PROPERTY", "USE THAT FITS"],
        "rows":[
            ["Wood", "Solid", "Stiff, light, can absorb water", "Furniture kept dry"],
            ["Metal", "Solid", "Strong; conducts heat and electricity", "Pan or wire"],
            ["Water", "Liquid", "Flows; keeps its volume", "Drink or washing"],
            ["Air", "Gas mixture", "Fills space; compresses", "Breathing or inflated tyre"],
        ],
        "footer":"A material is identified by a pattern of properties. The same object can contain several materials chosen for different jobs.",
    }, "A table compares wood, metal, water, and air by state, observable properties, and practical uses that depend on those properties.",
       "Materials are not sorted only by appearance: repeatable properties such as flow, stiffness, conductivity, and compressibility explain suitable uses."),

    S("chem.0.mixing", "Mixing", 0, "branch", {
        "root":"WATER + MATERIAL", "root_icon":"mix", "branches":[
            {"heading":"SALT DISSOLVES", "icon":"beaker", "edge":"tiny particles spread", "detail":"A clear solution forms; salt is still present and can return after evaporation."},
            {"heading":"SAND SUSPENDS", "icon":"particles", "edge":"stir", "detail":"Grains remain separate, settle with time, and can be filtered."},
            {"heading":"OIL SEPARATES", "icon":"water", "edge":"shake", "detail":"Droplets briefly disperse, then join into a layer because the liquids do not mix."},
        ],
        "footer":"Mixing can spread substances without making a new substance. Dissolved does not mean disappeared, and not every mixture is uniform.",
    }, "Water mixed with salt, sand, or oil branches into a solution, a settling suspension, or temporary droplets that reform a separate layer.",
       "Particle interactions determine whether a mixture stays uniform, settles, or separates; simple observations reveal which process occurred."),

    S("chem.0.water-states", "Ice, Water, Steam", 0, "cards", {
        "arrows":True, "items":[
            {"heading":"ICE", "icon":"solid", "detail":"Water molecules vibrate in an ordered solid structure.", "arrow":"melting"},
            {"heading":"LIQUID WATER", "icon":"liquid", "detail":"Molecules stay close but continually change neighbours.", "arrow":"boiling"},
            {"heading":"WATER VAPOUR", "icon":"gas", "detail":"Separate molecules move freely through the gas."},
        ],
        "footer":"Heating changes molecular motion and arrangement, not H₂O into a different chemical. Cooling reverses vapour → liquid → ice.",
    }, "Particle diagrams show the same water molecules ordered in ice, close and mobile in liquid, and widely separated in water vapour.",
       "Melting and boiling are physical state changes: molecular arrangement changes while each molecule remains H₂O."),

    S("chem.1.matter", "Solids, Liquids, Gases", 1, "cards", {
        "items":[
            {"heading":"SOLID", "icon":"solid", "stat":"fixed shape + volume", "detail":"Particles occupy stable neighbours and mainly vibrate."},
            {"heading":"LIQUID", "icon":"liquid", "stat":"flows; fixed volume", "detail":"Particles remain close but rearrange past one another."},
            {"heading":"GAS", "icon":"gas", "stat":"fills container", "detail":"Particles are far apart; collisions create pressure."},
        ],
        "footer":"State depends on temperature and pressure: it describes collective particle behaviour, not a permanent label attached to a substance.",
    }, "Solid, liquid, and gas particle models connect spacing and motion to fixed shape, flow, volume, compression, and pressure.",
       "Macroscopic state properties follow from particle arrangement, motion, and interaction rather than from particles themselves becoming solid or liquid."),

    S("chem.1.changes", "Changing Matter", 1, "matrix", {
        "columns":["WHAT PARTICLES DO", "NEW SUBSTANCE?", "CLUE / REVERSAL"],
        "rows":[
            ["Melting / freezing", "Rearrange with energy change", "No", "Reverse by heating / cooling"],
            ["Dissolving salt", "Ions spread among water molecules", "No", "Recover salt by evaporation"],
            ["Burning wood", "Atoms rearrange into gases and ash", "Yes", "Products cannot simply be cooled back"],
        ],
        "footer":"Reversibility is a useful clue, not a perfect definition. Chemical change is established by identifying substances before and after.",
    }, "A comparison table distinguishes melting, dissolving, and burning through particle rearrangement, formation of new substances, and possible reversal.",
       "Physical changes preserve molecular identity; chemical reactions conserve atoms while reconnecting them into different substances."),

    S("chem.1.materials-props", "Properties of Materials", 1, "matrix", {
        "columns":["NEEDED PROPERTY", "WHY IT WORKS"],
        "rows":[
            ["Window", "Transparent + rigid", "Transmits visible light while holding shape"],
            ["Pan base", "Thermally conductive + high melting point", "Moves heat to food without melting"],
            ["Raincoat", "Flexible + water-resistant", "Bends with the body while blocking liquid water"],
            ["Fridge handle", "Low thermal conductivity", "Slows heat flow to the hand"],
        ],
        "footer":"Engineering starts with constraints: the best material is the one whose measured properties fit the job and its trade-offs.",
    }, "A design table matches windows, pan bases, raincoats, and refrigerator handles to transparency, conductivity, melting point, flexibility, and water resistance.",
       "Choosing a material is causal reasoning from required function to relevant property, not a ranking of materials from universally best to worst."),

    S("chem.2.molecules", "Molecules and Compounds", 2, "matrix", {
        "columns":["SPECIES-CORRECT SKETCH", "WHAT THE FORMULA COUNTS", "STRUCTURE"],
        "rows":[
            ["Element · oxygen", "O=O", "2 oxygen atoms per O₂", "Discrete covalent molecule"],
            ["Molecular compound · water", "H—O—H · bent", "2 H + 1 O per H₂O", "Discrete covalent molecule"],
            ["Ionic compound · sodium chloride", "… Na⁺  Cl⁻  Na⁺  Cl⁻ …", "1:1 simplest ratio in NaCl", "Extended alternating lattice"],
        ],
        "footer":"Lines in O=O and H—O—H mark bonds; spaces between Na⁺ and Cl⁻ mark alternating ions, not separate NaCl molecules.",
    }, "Species-correct structural sketches compare diatomic oxygen O double bond O, water H—O—H explicitly labelled as bent, and a repeating sequence of alternating sodium and chloride ions.",
       "Formulae count atoms in discrete molecules or the simplest ion ratio in a lattice; the particle-level structure determines which interpretation applies."),

    S("chem.2.mixtures", "Mixtures and Solutions", 2, "branch", {
        "root":"MIXTURE", "root_icon":"mix", "branches":[
            {"heading":"LARGE SOLID + LIQUID", "icon":"particles", "edge":"particle size", "detail":"Filter: solid remains as residue; liquid and dissolved material pass."},
            {"heading":"DISSOLVED SOLID", "icon":"beaker", "edge":"volatility", "detail":"Evaporate solvent to recover solid, or distil to collect solvent too."},
            {"heading":"MISCIBLE LIQUIDS", "icon":"water", "edge":"boiling points", "detail":"Fractional distillation enriches the more volatile component first."},
        ],
        "footer":"Separation exploits a physical-property difference—size, solubility, boiling point, magnetism—not an arbitrary recipe.",
    }, "A separation decision tree chooses filtration, evaporation or distillation, and fractional distillation from particle size, solubility, and boiling-point differences.",
       "Mixture components retain properties that can be exploited; the correct separation method follows from which property differs."),

    S("chem.2.reactions-intro", "Chemical Reactions", 2, "matrix", {
        "columns":["BEFORE: REACTANTS", "AFTER: PRODUCTS", "CONSERVATION CHECK"],
        "rows":[
            ["Particle sketch", "H—H  +  H—H  +  O=O", "H—O—H  +  H—O—H", "Same 4 H and 2 O atoms"],
            ["Formula equation", "2 H₂ + O₂", "2 H₂O", "Coefficients count species"],
            ["What changes", "Two H—H + one O=O bonds", "Four O—H bonds", "Atoms persist; bonds rearrange"],
        ],
        "footer":"2 H₂ + O₂ → 2 H₂O: coefficients change how many molecules react; subscripts remain part of each species' identity.",
    }, "A balanced before-and-after particle ledger shows two H—H molecules plus one O=O molecule becoming two H—O—H molecules, with four hydrogen and two oxygen atoms on each side.",
       "The structural sketches make conservation visible: chemical reactions reconnect existing atoms into new species rather than changing element identities."),

    S("chem.2.acids", "Acids and Bases", 2, "scale", {
        "low_label":"MORE ACIDIC · higher [H₃O⁺]", "high_label":"MORE BASIC · higher [OH⁻]", "points":[
            {"heading":"LEMON", "value":"pH ≈ 2", "position":.14, "icon":"acid", "color":CORAL},
            {"heading":"PURE WATER", "value":"pH 7 at 25 °C", "position":.50, "icon":"water", "color":GREEN},
            {"heading":"SOAP", "value":"pH ≈ 10", "position":.72, "icon":"base", "color":BLUE},
            {"heading":"BLEACH", "value":"pH ≈ 12–13", "position":.90, "icon":"base", "color":PLUM},
        ],
        "note":"Each pH unit represents a tenfold change in hydronium activity; the scale is logarithmic.",
        "footer":"Acid–base neutralisation transfers protons; in simple aqueous cases H₃O⁺ + OH⁻ → 2 H₂O. Concentration and strength are different ideas.",
    }, "A logarithmic pH scale locates lemon near 2, pure water at 7 at 25 degrees Celsius, soap near 10, and bleach near 12 to 13.",
       "Moving one pH unit changes hydronium activity tenfold, so equal distances on the scale do not represent equal additive changes."),

    S("chem.2.periodic", "Reading the Periodic Table", 2, "matrix", {
        "columns":["LOCATION", "SHARED PATTERN", "EXAMPLE"],
        "rows":[
            ["Period (row)", "Across the table", "Same number of occupied main electron shells", "Period 3: Na → Ar"],
            ["Group 1", "Far left", "One valence electron; reactive metals", "Li, Na, K"],
            ["Group 17", "Near right", "Seven valence electrons; reactive nonmetals", "F, Cl, Br"],
            ["Group 18", "Far right", "Filled outer shell; low reactivity", "He, Ne, Ar"],
        ],
        "footer":"Atomic number increases one proton at a time. Periodic repetition arises from electron configurations, with transition-metal details beyond simple group rules.",
    }, "A periodic-table reading guide connects rows to occupied shells and groups 1, 17, and 18 to recurring valence-electron patterns and examples.",
       "The table orders elements by proton number so electron configurations—and therefore chemical properties—recur in a structured pattern."),

    S("chem.3.atomic-structure", "Atomic Structure", 3, "layers", {
        "mode":"concentric", "layers":[
            {"heading":"n = 3", "detail":"Higher shell: more available orbitals and generally higher energy", "color":BLUE},
            {"heading":"n = 2", "detail":"Contains 2s and three 2p orbitals; capacities follow quantum states", "color":TEAL},
            {"heading":"n = 1", "detail":"Lowest shell: one 1s orbital holding up to two electrons", "color":GOLD},
            {"heading":"NUCLEUS", "detail":"Protons set atomic number; neutrons distinguish isotopes", "color":CORAL},
        ],
        "footer":"Shell pictures are energy-level maps, not tiny planetary orbits. Electron probability distributions are orbitals with quantised states.",
    }, "Nested atomic energy shells surround a proton-and-neutron nucleus, with annotations for the 1s, second-shell, and higher-shell orbital structure.",
       "Atomic identity comes from proton number, isotope from neutron count, and chemistry largely from electrons occupying quantum states."),

    S("chem.3.bonding", "Chemical Bonding", 3, "cards", {
        "items":[
            {"heading":"IONIC", "icon":"ionic", "stat":"electron transfer", "detail":"Oppositely charged ions attract throughout a lattice; e.g. Na⁺ and Cl⁻."},
            {"heading":"COVALENT", "icon":"bond", "stat":"shared electron pair", "detail":"Nuclei attract shared electron density; bonds can be polar."},
            {"heading":"METALLIC", "icon":"metal", "stat":"delocalised electrons", "detail":"Positive ion cores share mobile electrons, enabling conduction and malleability."},
        ],
        "footer":"Bond categories are models of electron distribution and electrostatic attraction; real bonds can lie between idealised limits.",
    }, "Ionic, covalent, and metallic panels compare electron transfer into lattices, shared electron density, and delocalised mobile electrons.",
       "Bonding is explained by lower-energy electron–nucleus arrangements, not by atoms consciously seeking full shells."),

    S("chem.3.stoichiometry", "Moles and Equations", 3, "matrix", {
        "columns":["START", "USED / MADE IN 2 BATCHES", "FINISH"],
        "rows":[
            ["Hydrogen · H—H", "5 mol H₂", "−4 mol H₂", "1 mol H₂ left"],
            ["Oxygen · O=O", "2 mol O₂", "−2 mol O₂", "0 mol; limiting"],
            ["Water · H—O—H", "0 mol H₂O", "+4 mol H₂O", "4 mol H₂O formed"],
        ],
        "footer":"Each batch is 2 H₂ + O₂ → 2 H₂O. Two O₂ permit two batches, consuming 4 of 5 H₂ and leaving 1 H₂.",
    }, "A species-labelled limiting-reagent ledger starts with five moles H—H and two moles O=O, uses two reaction batches, and ends with four moles H—O—H plus one mole H—H.",
       "The coefficient ratio applies to distinct chemical species: oxygen is exhausted first, so it fixes the maximum water product while hydrogen remains."),

    S("chem.3.reactions", "Types of Reactions", 3, "matrix", {
        "columns":["TRANSFER", "DRIVING OBSERVATION", "NET IONIC EXAMPLE"],
        "rows":[
            ["Acid–base", "Proton H⁺", "pH changes; heat may transfer", "H⁺ + OH⁻ → H₂O"],
            ["Redox", "Electrons / oxidation state", "Voltage, colour, metal change", "Zn + Cu²⁺ → Zn²⁺ + Cu"],
            ["Precipitation", "Ions pair into low-solubility solid", "Solid appears from solutions", "Ag⁺ + Cl⁻ → AgCl(s)"],
        ],
        "footer":"Reaction labels describe different bookkeeping. Spectator ions remain unchanged and are omitted from a net ionic equation.",
    }, "A reaction table contrasts acid–base proton transfer, redox electron transfer, and precipitation into a low-solubility solid with net ionic equations.",
       "Classifying reactions exposes what is conserved and transferred, allowing observations to be connected to particle-level mechanisms."),

    S("chem.3.gases", "Gas Laws", 3, "graph", {
        "x_label":"Volume V", "y_label":"Pressure P", "x_range":(1,10), "y_range":(0,10),
        "curves":[
            {"label":"lower T", "color":BLUE, "points":[(1,7),(2,4),(3,2.7),(5,1.6),(8,1),(10,.8)]},
            {"label":"higher T", "color":CORAL, "points":[(1,9.5),(2,6),(3,4),(5,2.4),(8,1.5),(10,1.2)]},
        ],
        "icon":"gas", "callout_heading":"PARTICLE CAUSE", "callout":"At fixed n, shrinking V raises collision frequency and P. Raising absolute T increases molecular kinetic energy and P.",
        "footer":"PV = nRT for an ideal gas. Boyle's inverse P–V relation assumes fixed n and T; temperatures in gas laws use kelvin.",
    }, "Two inverse pressure–volume curves at lower and higher temperature show pressure rising as gas volume shrinks for a fixed amount of gas.",
       "Gas laws are conditional relationships: changing pressure by compression is not the same experiment as changing it by heating."),

    S("chem.3.energy", "Energy in Reactions", 3, "graph", {
        "x_label":"Reaction progress", "y_label":"Potential energy", "x_range":(0,10), "y_range":(0,10),
        "curves":[
            {"label":"exothermic", "color":CORAL, "points":[(0,6),(2,6.2),(4,9),(6,5),(8,2.8),(10,2.8)]},
            {"label":"endothermic", "color":BLUE, "points":[(0,3),(2,3.1),(4,7),(6,6),(8,7.1),(10,7.1)]},
        ],
        "icon":"energy", "callout_heading":"RATE ≠ ΔH", "callout":"Peak height controls activation barrier and rate; endpoint difference is reaction enthalpy. A catalyst lowers the barrier, not ΔH.",
        "footer":"Exothermic reactions transfer heat to surroundings (ΔH < 0); endothermic reactions absorb it (ΔH > 0) under constant pressure.",
    }, "Reaction-coordinate curves distinguish an exothermic drop and endothermic rise while separating activation-energy peaks from enthalpy changes.",
       "Thermodynamic energy change and kinetic reaction rate answer different questions; a large energy release can still occur slowly."),

    S("chem.3.organic-intro", "Carbon Chemistry", 3, "branch", {
        "root":"CARBON SKELETON", "root_icon":"carbon", "branches":[
            {"heading":"ALKANE C–C", "icon":"molecule", "edge":"single bonds", "detail":"Tetrahedral carbon chains can branch and rotate."},
            {"heading":"ALKENE C=C", "icon":"bond", "edge":"double bond", "detail":"Restricted rotation and electron-rich π bond enable addition reactions."},
            {"heading":"ALCOHOL C–OH", "icon":"water", "edge":"functional group", "detail":"Polar O–H changes solubility and oxidation chemistry."},
        ],
        "footer":"Carbon's four valence bonds build chains, rings, and 3-D frameworks; functional groups create recurring reactivity within those skeletons.",
    }, "A carbon-skeleton branch compares alkane single bonds, alkene double bonds, and alcohol hydroxyl groups with their structural and reactive consequences.",
       "Organic diversity comes from combining carbon connectivity, three-dimensional arrangement, and functional groups—not from carbon alone."),

    S("chem.4.physical", "Physical Chemistry", 4, "graph", {
        "x_label":"Reaction coordinate", "y_label":"Gibbs free energy G", "x_range":(0,10), "y_range":(0,10),
        "curves":[
            {"label":"uncatalysed", "color":CORAL, "points":[(0,7),(2,7.2),(4,9.5),(6,7),(8,3),(10,3)]},
            {"label":"catalysed", "color":GREEN, "points":[(0,7),(2,7.1),(4,7.8),(6,5),(8,3),(10,3)]},
        ],
        "icon":"model", "callout_heading":"TWO QUESTIONS", "callout":"ΔG determines equilibrium tendency; activation free energy ΔG‡ controls rate. The catalyst changes only the pathway barrier.",
        "footer":"A negative ΔG does not guarantee a fast process. Thermodynamics predicts relative stability; kinetics predicts how quickly states interconvert.",
    }, "A free-energy landscape gives catalysed and uncatalysed routes the same negative Gibbs endpoint change but different activation barriers.",
       "Physical chemistry keeps equilibrium driving force separate from rate, then connects both to molecular energy distributions and pathways."),

    S("chem.4.organic", "Organic Chemistry", 4, "network", {
        "nodes":[
            {"id":"nuc", "label":":Nu⁻ LONE PAIR source", "icon":"molecule", "pos":(.03,.16), "color":TEAL},
            {"id":"carbon", "label":"R—Cδ⁺—LGδ⁻ electrophile", "icon":"carbon", "pos":(.39,.16), "color":CORAL},
            {"id":"bondpair", "label":"C—LG BOND PAIR source", "icon":"bond", "pos":(.39,.78), "color":PLUM},
            {"id":"leaving", "label":":LG⁻ receives pair", "icon":"molecule", "pos":(.72,.78), "color":BLUE},
            {"id":"product", "label":"R—C—Nu + LG⁻", "icon":"molecule", "pos":(.91,.16), "color":GREEN},
        ],
        "edges":[
            ("nuc", "carbon", "lone pair → C", TEAL),
            ("bondpair", "leaving", "C—LG pair → LG", PLUM),
            ("carbon", "product", "C—Nu forms as C—LG breaks", GREEN),
        ],
        "footer":"The two mechanism arrows start at electron pairs and end at an atom: :Nu⁻ → C while the C—LG bond pair → LG. They do not trace atom motion.",
    }, "An electron-flow map sends the nucleophile lone pair to electrophilic carbon and the carbon–leaving-group bond pair to the leaving group while the substitution product forms.",
       "Mechanistic arrows have explicit electron sources and destinations, making simultaneous bond formation and bond cleavage distinct from a sequence of moving atoms."),

    S("chem.4.inorganic", "Inorganic Chemistry", 4, "layers", {
        "layers":[
            {"heading":"e_g · 2 ORBITALS · HIGHER", "detail":"d(z²) and d(x²−y²) point along the ligand axes, so their electron density experiences greater repulsion", "color":CORAL},
            {"heading":"Δo · OCTAHEDRAL SPLITTING", "detail":"The energy gap depends on metal identity, oxidation state, ligand strength, and metal–ligand distance", "color":GOLD},
            {"heading":"t₂g · 3 ORBITALS · LOWER", "detail":"d(xy), d(xz), and d(yz) point between ligand axes and are stabilised relative to e_g", "color":GREEN},
            {"heading":"[ML₆]ⁿ⁺ OCTAHEDRON", "detail":"Exactly six ligand donor atoms surround M along +x, −x, +y, −y, +z, and −z", "color":BLUE},
        ],
        "footer":"Six-axis ligand geometry splits five d orbitals into a higher pair and lower trio; occupancy then controls colour, magnetism, and reactivity.",
    }, "An octahedral ligand-field energy stack states that six ligand donors surround a metal along plus and minus x, y, and z, splitting five d orbitals into higher e-g and lower t-two-g sets.",
       "The diagram connects the six-ligand geometry to orbital orientation and energy splitting before linking electron occupancy to colour and magnetic behaviour."),

    S("chem.4.analytical", "Analytical Chemistry", 4, "graph", {
        "x_label":"Retention time", "y_label":"Detector signal", "x_range":(0,10), "y_range":(0,10),
        "curves":[{"label":"sample chromatogram", "color":TEAL,
                   "points":[(0,.4),(1,.5),(2,.5),(2.4,5),(2.8,.6),(4,.5),(5.2,9),(5.8,.7),(7,.5),(8.2,3),(8.7,.5),(10,.5)]}],
        "icon":"beaker", "callout_heading":"IDENTIFY + QUANTIFY", "callout":"Retention time suggests identity against standards; integrated peak area estimates amount through a calibration curve.",
        "footer":"A signal is not a result until blanks, standards, resolution, uncertainty, and matrix effects show what the peaks can support.",
    }, "A three-peak chromatogram links retention time to tentative identity and integrated peak area to concentration through external calibration.",
       "Analytical chemistry separates detection from inference: instruments produce signals, while standards and uncertainty turn signals into defensible measurements."),

    S("chem.4.quantum-chem", "Quantum Chemistry", 4, "layers", {
        "mode":"mo-energy",
        "footer":"Electrons fill molecular orbitals by energy; bond order = (bonding e⁻ − antibonding e⁻) / 2. H₂ has bond order 1; idealised He₂ has 0.",
    }, "A worked hydrogen molecular-orbital energy diagram correlates two equal-energy one-s atomic orbitals with lower sigma one-s and higher sigma-star one-s levels, showing same-sign bonding density, opposite-sign lobes, an internuclear node, and two paired electrons in the bonding level.",
       "The signed lobes make wave interference visible: in-phase addition builds density between nuclei, out-of-phase subtraction creates a node, and hydrogen's two bonding electrons give bond order one."),

    S("chem.4.electrochem", "Electrochemistry", 4, "network", {
        "nodes":[
            {"id":"zn","label":"ANODE Zn → Zn²⁺ + 2e⁻", "icon":"metal","pos":(.06,.30),"color":CORAL},
            {"id":"load","label":"LOAD receives electrical work", "icon":"light","pos":(.47,.10),"color":GOLD},
            {"id":"cu","label":"CATHODE Cu²⁺ + 2e⁻ → Cu", "icon":"metal","pos":(.88,.30),"color":BLUE},
            {"id":"bridge","label":"SALT BRIDGE ion migration", "icon":"beaker","pos":(.47,.78),"color":TEAL},
        ],
        "edges":[("zn","load","e⁻ through wire"),("load","cu","e⁻ through wire"),
                 ("bridge","zn","anions"),("bridge","cu","cations")],
        "footer":"Oxidation occurs at the anode and reduction at the cathode in both cell types; electrode signs depend on galvanic versus electrolytic operation.",
    }, "A zinc–copper galvanic-cell network tracks oxidation at zinc, electron flow through a wire, copper-ion reduction, and salt-bridge charge balance.",
       "The salt bridge completes internal ionic conduction without carrying electrons; separating half-reactions lets spontaneous redox deliver electrical work."),

    S("chem.5.biochem", "Advanced Biochemistry", 5, "graph", {
        "x_label":"Substrate concentration [S]", "y_label":"v", "x_range":(0,10), "y_range":(0,10),
        "curves":[
            {"label":"Vmax", "color":CORAL, "points":[(0,8),(10,8)],
             "label_at":1, "label_dx":-80, "label_dy":-22},
            {"label":"Vmax / 2", "color":BLUE, "points":[(0,4),(2,4)],
             "label_at":1, "label_dx":115, "label_dy":18},
            {"label":"Km", "color":PLUM, "points":[(2,0),(2,4)],
             "label_at":0, "label_dx":40, "label_dy":-20},
            {"label":"v([S])", "color":GREEN,
             "points":[(0,0),(1,2.67),(2,4),(3,4.8),(4,5.33),(6,6),(8,6.4),(10,6.67)],
             "label_at":7, "label_dx":-120, "label_dy":-22},
        ],
        "icon":"enzyme", "callout_heading":"READ Km FROM GUIDES", "callout":"The vertical Km guide meets the curve where the horizontal Vmax/2 guide ends. At high [S], rate approaches the Vmax asymptote without crossing it.",
        "footer":"Protein sequence shapes a dynamic energy landscape; folding, binding, catalysis, and allostery depend on ensembles, not one rigid structure.",
    }, "A saturating Michaelis–Menten rate curve connects half-maximal velocity at Km and the high-substrate plateau to enzyme active-site occupancy.",
       "Enzyme kinetics converts molecular binding and turnover into measurable rates, while deviations reveal inhibition, cooperativity, or mechanism complexity."),

    S("chem.5.materials", "Materials Chemistry", 5, "cards", {
        "items":[
            {"heading":"POLYMER", "icon":"polymer", "stat":"chain architecture", "detail":"Length, branching, crosslinks, and intermolecular forces set toughness and softening."},
            {"heading":"NANOMATERIAL", "icon":"particles", "stat":"high surface / volume", "detail":"A larger fraction of atoms lies at interfaces, changing reactivity and optics."},
            {"heading":"SEMICONDUCTOR", "icon":"energy", "stat":"tunable carriers", "detail":"Band gap, temperature, and dopants control electrons and holes."},
        ],
        "footer":"Structure links processing to properties: synthesis and defects determine microstructure, which determines performance and failure.",
    }, "Polymer-chain architecture, nanoscale surface fraction, and semiconductor band carriers are each connected to resulting material properties.",
       "Materials chemistry designs function across scales, from bonds and defects through microstructure to the behaviour of a finished component."),

    S("chem.5.compchem", "Computational Chemistry", 5, "cards", {
        "arrows":True, "items":[
            {"heading":"1 · MODEL", "icon":"molecule", "detail":"Choose quantum electrons or a fitted force field and define boundaries.", "arrow":"calculate"},
            {"heading":"2 · SAMPLE", "icon":"computer", "detail":"Optimise a structure or integrate many finite time steps.", "arrow":"ensemble"},
            {"heading":"3 · PREDICT", "icon":"graph", "detail":"Estimate energies, spectra, rates, or distributions with uncertainty.", "arrow":"test"},
            {"heading":"4 · VALIDATE", "icon":"beaker", "detail":"Compare against higher-level calculations and independent experiments."},
        ],
        "footer":"Simulation is an experiment on a mathematical model. Time step, sampling, basis, parameters, and finite size bound what it can claim.",
    }, "A computational chemistry workflow moves from an explicit molecular model through numerical sampling to uncertain predictions and experimental validation.",
       "Agreement is meaningful only within a declared model domain; convergence and validation distinguish chemical insight from attractive molecular animation."),

    S("chem.5.frontier", "Frontiers of Chemistry", 5, "matrix", {
        "columns":["DESIGN LEVER", "TARGET METRIC", "FAILURE TEST"],
        "rows":[
            ["Catalyst", "Lower-barrier selective pathway", "Rate + selectivity + lifetime", "Poisoning, rare metals, side products"],
            ["Green process", "Solvent, feedstock, and energy choice", "Atom economy + life-cycle impact", "Burden shifted upstream"],
            ["Molecular machine", "Biased motion through a cycle", "Work per fuel / photon input", "Random motion mistaken for direction"],
        ],
        "footer":"Frontier chemistry optimises whole systems: activity without selectivity, durability, scalable synthesis, and life-cycle accounting is not a solution.",
    }, "A design matrix evaluates catalysts, green processes, and molecular machines through mechanism, performance metric, and a specific failure test.",
       "Chemical innovation becomes credible when molecular performance survives selectivity, durability, scale, resource, and full-system impact constraints."),
]


SPECS = {item["id"]: item for item in _LIST}

if len(SPECS) != len(_LIST):
    raise ValueError("Duplicate chemistry illustration identifier")
