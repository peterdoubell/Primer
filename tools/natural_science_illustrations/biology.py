"""Lesson-specific deterministic biology plates."""

from __future__ import annotations

from typing import Mapping

from . import core as _core
from .core import BLUE, CORAL, GOLD, GREEN, PLUM, TEAL, science_spec


def S(node_id, title, stage, layout, content, alt, caption):
    return science_spec(node_id, title, stage, "biology", layout, content, alt, caption)


_BASE_GRAPH_RENDERER = getattr(
    _core, "_biology_base_graph_renderer", _core.RENDERERS["graph"]
)
_core._biology_base_graph_renderer = _BASE_GRAPH_RENDERER


def _draw_biology_graph(plate, content: Mapping[str, object]) -> None:
    _BASE_GRAPH_RENDERER(plate, content)
    if content.get("mode") != "neuro-ticks":
        return

    # Add true, data-aligned voltage ticks inside the otherwise generic graph.
    x0, y0, _x1, y1 = 155, 250, 1025, 750
    y_min, y_max = content.get("y_range", (-90, 50))
    for value, label, dy in ((-55, "threshold −55 mV", -18),
                             (-70, "rest −70 mV", 24)):
        y = y1 - (value - y_min) / (y_max - y_min) * (y1 - y0)
        plate.draw.line((x0 - 11, y, x0 + 13, y), fill=_core.INK, width=4)
        plate.text((x0 - 18, y), str(value), size=17, bold=True,
                   fill=_core.INK, anchor="rm")
        plate.text((x0 + 25, y + dy), label, size=16, bold=True,
                   fill=_core.INK_SOFT, anchor="la")


_core.RENDERERS["graph"] = _draw_biology_graph


_LIST = [
    S("bio.0.living", "Living and Not Living", 0, "cards", {
        "items": [
            {"heading": "PLANT", "icon": "plant", "detail": "Uses energy, grows, responds, and makes new plants."},
            {"heading": "ANIMAL", "icon": "animal", "detail": "Takes in food, grows, senses its surroundings, and reproduces."},
            {"heading": "ROCK", "icon": "rock", "detail": "May move or get bigger when pieces collect, but has no cells or metabolism."},
        ],
        "footer": "One clue is not enough: living systems use energy, maintain themselves, respond, grow, and belong to reproducing lineages.",
    }, "A plant and animal satisfy several linked signs of life, while a rock lacks cells, metabolism, response, and reproduction.",
       "Living things are identified by a coordinated set of processes—not simply by motion, size, or any single visible clue."),

    S("bio.0.animals", "Animals", 0, "cards", {
        "items": [
            {"heading": "FISH · POND", "icon": "fish", "detail": "Gills take dissolved oxygen from water; fins push and steer."},
            {"heading": "BIRD · WOODS", "icon": "bird", "detail": "Wings move through air; feet and beaks fit perching and feeding."},
            {"heading": "CAMEL · DESERT", "icon": "animal", "detail": "Long legs and water-saving kidneys help in heat and drought."},
        ],
        "footer": "A habitat supplies food, water, shelter, and space; body structures and behaviour help an animal use those resources.",
    }, "Fish, bird, and camel examples connect gills, wings, and water-saving traits to the different resources and challenges of their habitats.",
       "Animals do not merely live in named places—their structures and behaviours solve particular problems posed by those environments."),

    S("bio.0.plants", "Plants Grow", 0, "cycle", {
        "center": "ONE LIFE, MANY STAGES", "center_icon": "plant",
        "items": [
            {"heading": "SEED", "icon": "seed", "detail": "Embryo plus stored food", "arrow": "water"},
            {"heading": "ROOT FIRST", "icon": "plant", "detail": "Anchors; absorbs water", "arrow": "shoot"},
            {"heading": "LEAVES", "icon": "leaf", "detail": "Light powers sugar making", "arrow": "growth"},
            {"heading": "FLOWER", "icon": "plant", "detail": "Seeds form after pollination", "arrow": "dispersal"},
        ],
        "footer": "Germination uses stored food first; once leaves open, light, carbon dioxide, water, and minerals support continued growth.",
    }, "A four-stage plant life cycle shows a seed germinating root-first, producing leaves, flowering, and making seeds that restart the cycle.",
       "The diagram separates germination from later photosynthetic growth and shows why seed formation closes, rather than ends, the life cycle."),

    S("bio.0.body", "My Body", 0, "matrix", {
        "columns": ["SENSE ORGAN", "DETECTS", "MESSAGE GOES TO"],
        "rows": [
            ["Sight", "Eyes", "Light", "Brain"],
            ["Hearing", "Ears", "Sound vibrations", "Brain"],
            ["Smell", "Nose", "Airborne chemicals", "Brain"],
            ["Taste", "Tongue", "Dissolved chemicals", "Brain"],
            ["Touch", "Skin", "Pressure, heat, cold, pain", "Brain / spinal cord"],
        ],
        "footer": "Sense organs convert different kinds of stimuli into nerve signals; the nervous system combines those signals to guide action.",
    }, "A five-row table maps sight, hearing, smell, taste, and touch to their organs, detected stimuli, and nervous-system destination.",
       "The five senses are different input channels: each is specialised for a stimulus, yet all communicate through the nervous system."),

    S("bio.0.seasons", "The Seasons", 0, "cycle", {
        "center": "LIGHT + TEMPERATURE", "center_icon": "sun",
        "items": [
            {"heading": "SPRING", "icon": "seed", "detail": "Buds open; many young are born"},
            {"heading": "SUMMER", "icon": "sun", "detail": "Long light supports growth"},
            {"heading": "AUTUMN", "icon": "leaf", "detail": "Leaves fall; animals store or migrate"},
            {"heading": "WINTER", "icon": "snow", "detail": "Dormancy saves energy"},
        ],
        "footer": "Seasonal responses follow recurring changes in daylight, temperature, water, and food—not a one-way ageing of nature.",
    }, "A spring-to-winter cycle links changing daylight and temperature to budding, growth, leaf fall, migration, and dormancy in living things.",
       "Living things use seasonal cues to time costly activities so growth and reproduction occur when resources are more favourable."),

    S("bio.1.habitats", "Habitats", 1, "cards", {
        "items": [
            {"heading": "DESERT", "icon": "plant", "stat": "scarce water", "detail": "Cactus stores water; spines reduce leaf area and browsing."},
            {"heading": "OCEAN", "icon": "fish", "stat": "water + salt", "detail": "Streamlined bodies cut drag; gills exchange gases with water."},
            {"heading": "POLAR", "icon": "animal", "stat": "cold", "detail": "Insulation slows heat loss; broad feet spread weight on snow."},
        ],
        "footer": "An adaptation helps in a particular environment and can carry costs elsewhere; no organism is 'best' in every habitat.",
    }, "Desert, ocean, and polar cards pair environmental challenges with cactus, fish, and mammal adaptations that address those challenges.",
       "Habitats act as filters: inherited traits that improve survival and reproduction under local conditions tend to persist."),

    S("bio.1.food-chains", "Food Chains", 1, "network", {
        "nodes": [
            {"id": "sun", "label": "SUNLIGHT", "icon": "sun", "pos": (.05,.25), "color": GOLD},
            {"id": "grass", "label": "GRASS producer", "icon": "plant", "pos": (.32,.25), "color": GREEN},
            {"id": "rabbit", "label": "RABBIT consumer", "icon": "animal", "pos": (.59,.25), "color": TEAL},
            {"id": "fox", "label": "FOX predator", "icon": "animal", "pos": (.86,.25), "color": CORAL},
            {"id": "decomp", "label": "DECOMPOSERS recycle matter", "icon": "fungus", "pos": (.50,.82), "color": PLUM},
        ],
        "edges": [("sun","grass","energy"),("grass","rabbit","food"),("rabbit","fox","food"),
                  ("grass","decomp","dead matter"),("rabbit","decomp","waste"),("fox","decomp","dead matter")],
        "footer": "Arrows point from the energy source to the eater. Energy eventually leaves as heat; decomposers return matter to the environment.",
    }, "A labelled network sends energy from sunlight to grass, rabbit, and fox, while dead matter and waste flow to decomposers.",
       "Food-chain arrows track transferred energy, whereas decomposers reveal the different fate of matter: nutrients are recycled but energy is not."),

    S("bio.1.plants-parts", "Parts of a Plant", 1, "network", {
        "nodes": [
            {"id":"soil","label":"SOIL water + minerals","icon":"water","pos":(.04,.72),"color":BLUE},
            {"id":"root","label":"ROOT absorbs + anchors","icon":"plant","pos":(.25,.72),"color":GOLD},
            {"id":"stem","label":"STEM xylem + phloem","icon":"plant","pos":(.48,.50),"color":TEAL},
            {"id":"leaf","label":"LEAF makes sugar","icon":"leaf","pos":(.73,.20),"color":GREEN},
            {"id":"flower","label":"FLOWER makes seeds","icon":"plant","pos":(.92,.48),"color":CORAL},
            {"id":"sink","label":"GROWING PARTS use sugar","icon":"seed","pos":(.72,.82),"color":PLUM},
        ],
        "edges": [("soil","root","",BLUE),("root","stem","xylem ↑",BLUE),("stem","leaf","water ↑",BLUE),
                  ("leaf","stem","phloem",GREEN),("stem","sink","sugar",GREEN),("stem","flower","sugar",GREEN)],
        "footer": "Xylem mainly carries water and minerals upward; phloem distributes sugars from sources such as leaves to growing or storing sinks.",
    }, "A plant transport network traces water from soil through roots and xylem to leaves, then sugar through phloem to flowers and growing tissues.",
       "Plant parts cooperate: roots acquire materials, leaves build sugars, vascular tissues transport them, and flowers support reproduction."),

    S("bio.1.human-body", "Inside the Body", 1, "network", {
        "nodes": [
            {"id":"air","label":"AIR oxygen in","icon":"cloud","pos":(.05,.18),"color":BLUE},
            {"id":"lungs","label":"LUNGS exchange gases","icon":"lungs","pos":(.28,.18),"color":TEAL},
            {"id":"heart","label":"HEART pumps blood","icon":"heart","pos":(.53,.42),"color":CORAL},
            {"id":"muscle","label":"MUSCLES use O₂ + fuel","icon":"body","pos":(.82,.23),"color":PLUM},
            {"id":"bones","label":"BONES support + lever","icon":"bone","pos":(.82,.72),"color":GOLD},
            {"id":"return","label":"CO₂ returns","icon":"cloud","pos":(.28,.78),"color":BLUE},
        ],
        "edges": [("air","lungs","inhale"),("lungs","heart","O₂"),("heart","muscle","blood"),
                  ("muscle","return","CO₂"),("return","lungs","exhale"),("bones","muscle","move together",GOLD,"both")],
        "footer": "Movement depends on cooperation: lungs exchange gases, the heart circulates blood, and muscles pull on bones across joints.",
    }, "A body-system route carries oxygen from air through lungs and heart to muscle, returns carbon dioxide, and links muscles with bones for movement.",
       "Organs form coordinated systems; none of the lungs, heart, muscles, or skeleton can supply movement by working alone."),

    S("bio.1.health", "Staying Healthy", 1, "matrix", {
        "columns": ["WHAT IT SUPPLIES", "WHAT IT HELPS"],
        "rows": [
            ["Varied food + water", "Energy, building materials, micronutrients", "Growth and repair"],
            ["Sleep", "Time for neural and body regulation", "Attention, memory, recovery"],
            ["Active play", "Load on heart, lungs, muscle, bone", "Fitness and strength"],
            ["Hand / tooth hygiene", "Removes microbes, plaque, and food", "Lowers infection and decay risk"],
        ],
        "footer": "Healthy habits shift risks and support normal function; they are not guarantees and do not replace medical care when someone is ill.",
    }, "A table links varied food, sleep, activity, and hygiene to the resources or challenges they provide and the body functions they support.",
       "The habits work through different mechanisms, so a single 'healthy' action cannot substitute for nutrition, sleep, movement, and hygiene together."),

    S("bio.2.classification", "Classifying Life", 2, "network", {
        "nodes": [
            {"id":"luca", "label":"LUCA shared ancestor", "icon":"dna", "pos":(.04,.46), "color":PLUM},
            {"id":"bacteria", "label":"BACTERIA distinct lineage", "icon":"bacteria", "pos":(.30,.10), "color":TEAL},
            {"id":"archstem", "label":"ARCHAEAL STEM closer to eukaryotes", "icon":"microbe", "pos":(.30,.82), "color":GOLD},
            {"id":"archaea", "label":"OTHER ARCHAEA diverse cells", "icon":"microbe", "pos":(.67,.78), "color":BLUE},
            {"id":"euk", "label":"EUKARYOTES nuclei + organelles", "icon":"cell", "pos":(.92,.12), "color":GREEN},
        ],
        "edges": [
            ("luca", "bacteria", "diverge"),
            ("luca", "archstem", "diverge"),
            ("archstem", "archaea", "diversify"),
            ("archstem", "euk", "host lineage"),
            ("bacteria", "euk", "mitochondrial ancestor", CORAL),
        ],
        "footer": "This simplified phylogeny follows molecular evidence: eukaryotes arose from an archaeal host lineage, while mitochondria came from a bacterial endosymbiont.",
    }, "A simplified phylogeny branches Bacteria from the shared ancestor and places Eukaryotes within an archaeal host lineage, with a second bacterial contribution to mitochondria.",
       "Classification is nested ancestry, not a ladder: branching marks lineage divergence, while the mitochondrial edge records an endosymbiotic merger."),

    S("bio.2.photosynthesis", "Photosynthesis", 2, "flow", {
        "input_heading":"LEAF INPUTS", "inputs":[
            {"label":"Light energy", "icon":"sun"}, {"label":"6 CO₂ through stomata", "icon":"cloud"},
            {"label":"6 H₂O through xylem", "icon":"water"}],
        "process":"CHLOROPLAST", "icon":"leaf", "mechanism":"Chlorophyll captures light; reactions store energy in chemical bonds.",
        "output_heading":"PRODUCTS", "outputs":[
            {"label":"C₆H₁₂O₆ sugar", "icon":"molecule"}, {"label":"6 O₂ released", "icon":"cloud"}],
        "in_arrow":"capture", "out_arrow":"build",
        "footer":"6 CO₂ + 6 H₂O + light → C₆H₁₂O₆ + 6 O₂. Atoms are rearranged; the energy stored in sugar came from light.",
    }, "A leaf flow diagram brings light, six carbon dioxide, and six water molecules into a chloroplast and outputs glucose and six oxygen molecules.",
       "Photosynthesis conserves atoms while changing energy form: carbon dioxide supplies carbon, water supplies electrons, and light drives sugar formation."),

    S("bio.2.digestion", "Body Systems", 2, "flow", {
        "input_heading":"ENTERS THE BODY", "inputs":[
            {"label":"Food to digestive tract", "icon":"food"},
            {"label":"O₂ inhaled into lungs", "icon":"lungs"},
        ],
        "process":"COUPLED BODY SYSTEMS", "icon":"system",
        "mechanism":"Gut absorbs nutrients; blood delivers nutrients and O₂ to cells, then carries each waste to the organ that removes it.",
        "output_heading":"DIFFERENT EXIT ROUTES", "outputs":[
            {"label":"CO₂ exhaled by lungs", "icon":"lungs"},
            {"label":"Urea + excess water via kidneys", "icon":"water"},
            {"label":"Unabsorbed residue via colon", "icon":"system"},
        ],
        "in_arrow":"absorb + exchange", "out_arrow":"sort by route",
        "footer":"Carbon dioxide returns in blood to the lungs; kidneys remove dissolved metabolic wastes; the colon expels material that was never absorbed.",
    }, "A body-systems flow combines absorbed nutrients and inhaled oxygen, then separates carbon dioxide to the lungs, dissolved wastes to the kidneys, and unabsorbed residue to the colon.",
       "Circulation links specialised organs, but different wastes leave by different routes: exhalation, urine formation, and elimination are not one generic process."),

    S("bio.2.reproduction", "Reproduction and Growth", 2, "network", {
        "nodes":[
            {"id":"reproduction", "label":"REPRODUCTION starts offspring", "icon":"cell", "pos":(.03,.45), "color":PLUM},
            {"id":"asexual", "label":"ASEXUAL one parent; close copy", "icon":"cell", "pos":(.29,.13), "color":TEAL},
            {"id":"sexual", "label":"SEXUAL meiosis + fertilisation", "icon":"chromosome", "pos":(.29,.78), "color":CORAL},
            {"id":"offspring", "label":"NEW ORGANISM begins", "icon":"seed", "pos":(.61,.45), "color":GOLD},
            {"id":"growth", "label":"GROWTH mitosis + differentiation", "icon":"body", "pos":(.91,.45), "color":GREEN},
        ],
        "edges":[
            ("reproduction", "asexual", "one-parent route"),
            ("reproduction", "sexual", "gamete route"),
            ("asexual", "offspring", "offspring"),
            ("sexual", "offspring", "zygote"),
            ("offspring", "growth", "then develops"),
        ],
        "footer":"Asexual and sexual reproduction are alternative routes to a new organism; growth follows as mitosis adds cells and differentiation gives them distinct jobs.",
    }, "A reproduction network splits into asexual and sexual routes, reconverges at a new organism, and only then proceeds to growth by mitosis and differentiation.",
       "Reproduction establishes a new individual; growth develops that individual, so growth is a later shared process rather than a third reproductive route."),

    S("bio.2.ecosystems", "Ecosystems", 2, "flow", {
        "input_heading":"ENTERS", "inputs":[{"label":"Sunlight energy", "icon":"sun"},{"label":"CO₂, water, minerals", "icon":"water"}],
        "process":"FOOD WEB", "icon":"network", "mechanism":"Producers build biomass; consumers and decomposers transfer its matter and energy.",
        "output_heading":"FATES", "outputs":[{"label":"Heat leaves at every level", "icon":"energy"},{"label":"Nutrients return to soil / air", "icon":"cycle"}],
        "in_arrow":"capture", "out_arrow":"transfer",
        "footer":"Energy flows one way and becomes dispersed heat; matter cycles among organisms, air, water, and soil. Biodiversity adds alternate pathways.",
    }, "An ecosystem budget separates incoming sunlight from cycling carbon, water, and minerals, then shows heat leaving and nutrients returning after food-web transfers.",
       "Ecosystem balance is dynamic: energy needs continual input while matter is repeatedly reused through producers, consumers, and decomposers."),

    S("bio.2.microbes", "Tiny Life", 2, "scale", {
        "low_label":" ", "high_label":" ", "points":[
            {"heading":"0.1 µm", "value":"typical virus", "position":.00, "icon":"virus", "color":CORAL},
            {"heading":"1 µm", "value":"typical bacterium", "position":.33, "icon":"bacteria", "color":TEAL},
            {"heading":"10 µm", "value":"typical yeast", "position":.67, "icon":"fungus", "color":PLUM},
            {"heading":"10 µm", "value":"animal range starts", "position":.67, "icon":"cell", "color":GREEN},
            {"heading":"100 µm", "value":"animal range endpoint", "position":1.00, "icon":"cell", "color":BLUE},
        ],
        "note":"TRUE LOG₁₀ SCALE: each equal horizontal gap is ×10; yeast and smaller animal cells overlap near 10 µm.",
        "footer":"Sizes vary widely. Bacteria and fungi are cells; viruses are acellular and reproduce only by using a host cell's machinery.",
    }, "A true base-ten size axis places a typical virus at 0.1 micrometre, bacterium at 1, and yeast at 10, where the 10-to-100-micrometre animal-cell range begins and overlaps.",
       "Equal spacing means a tenfold size ratio, while the shared 10-micrometre position makes the yeast–animal-cell overlap explicit rather than implying separate size classes."),

    S("bio.3.genetics", "Genetics", 3, "flow", {
        "input_heading":"INHERITED INPUT", "inputs":[{"label":"Allele from egg", "icon":"chromosome"},{"label":"Allele from sperm", "icon":"chromosome"}],
        "process":"GENOTYPE", "icon":"dna", "mechanism":"Alleles are DNA variants at a gene; meiosis separates them into gametes.",
        "output_heading":"OBSERVED OUTCOME", "outputs":[{"label":"Protein activity", "icon":"molecule"},{"label":"Phenotype shaped by genes + environment", "icon":"body"}],
        "in_arrow":"fertilisation", "out_arrow":"expression",
        "footer":"DNA sequence can affect phenotype through gene expression, but dominance is not 'strength' and most traits involve many genes plus environment.",
    }, "A genetics flow joins one allele from each parent into a genotype, then connects gene expression to proteins and an environmentally influenced phenotype.",
       "Inheritance transmits DNA variants; development and environment mediate how those variants become observable traits."),

    S("bio.3.evolution", "Evolution", 3, "cards", {
        "arrows":True, "items":[
            {"heading":"1 · VARIATION", "icon":"dna", "detail":"Mutation and recombination create inherited differences.", "arrow":"environment"},
            {"heading":"2 · FILTER", "icon":"animal", "detail":"Some variants leave more surviving offspring in these conditions.", "arrow":"inherit"},
            {"heading":"3 · GENERATIONS", "icon":"cycle", "detail":"Successful variants become more common in the population.", "arrow":"diverge"},
            {"heading":"4 · LINEAGES", "icon":"branch", "detail":"Isolation plus accumulated change can produce new species."},
        ],
        "footer":"Individuals do not evolve because they need to. Population allele frequencies change across generations; selection has no foresight.",
    }, "Four linked stages show inherited variation, differential reproductive success, allele-frequency change over generations, and possible lineage divergence.",
       "Natural selection is a population-level consequence of heritable differences in reproductive success, not purposeful improvement within an individual."),

    S("bio.3.cell-bio", "Cell Biology", 3, "network", {
        "nodes":[
            {"id":"mem","label":"MEMBRANE selects exchange","icon":"cell","pos":(.05,.52),"color":TEAL},
            {"id":"nuc","label":"NUCLEUS stores DNA","icon":"dna","pos":(.32,.18),"color":PLUM},
            {"id":"rib","label":"RIBOSOME builds protein","icon":"molecule","pos":(.60,.18),"color":CORAL},
            {"id":"mito","label":"MITOCHONDRION makes ATP","icon":"energy","pos":(.60,.78),"color":GOLD},
            {"id":"work","label":"CELL WORK + GROWTH","icon":"system","pos":(.88,.50),"color":GREEN},
        ],
        "edges":[("mem","nuc","signals"),("nuc","rib","mRNA"),("mem","mito","fuel + O₂"),
                 ("rib","work","proteins"),("mito","work","ATP")],
        "footer":"Before mitosis, DNA is replicated once; chromosome copies then separate so each daughter cell receives a genome.",
    }, "A cell network links selective membrane exchange and nuclear DNA to ribosome-made proteins, mitochondrial ATP, and coordinated cell work.",
       "Organelles divide labour but remain coupled by flows of information, matter, and energy; mitosis preserves the genome during cell division."),

    S("bio.3.ecology", "Ecology", 3, "network", {
        "nodes":[
            {"id":"atmosphere", "label":"ATMOSPHERE CO₂ pool", "icon":"cloud", "pos":(.43,.03), "color":BLUE},
            {"id":"producers", "label":"PRODUCERS fix carbon", "icon":"plant", "pos":(.04,.45), "color":GREEN},
            {"id":"consumers", "label":"CONSUMERS eat biomass", "icon":"animal", "pos":(.39,.82), "color":CORAL},
            {"id":"decomposers", "label":"DECOMPOSERS use remains", "icon":"fungus", "pos":(.82,.76), "color":PLUM},
            {"id":"respiration", "label":"CELLULAR RESPIRATION releases CO₂", "icon":"energy", "pos":(.91,.16), "color":GOLD},
        ],
        "edges":[
            ("atmosphere", "producers", "photosynthesis", GREEN),
            ("producers", "consumers", "feeding", CORAL),
            ("producers", "decomposers", "dead tissue", PLUM),
            ("consumers", "decomposers", "waste + remains", PLUM),
            ("producers", "respiration", "plants respire", GOLD),
            ("consumers", "respiration", "animals respire", GOLD),
            ("decomposers", "respiration", "microbes respire", GOLD),
            ("respiration", "atmosphere", "CO₂ return", BLUE),
        ],
        "footer":"Producers, consumers, and decomposers all respire carbon to CO₂; photosynthesis provides the opposing atmospheric-to-biomass flux.",
    }, "A carbon network sends atmospheric carbon dioxide into producers by photosynthesis and returns it through plant, animal, and decomposer respiration, with feeding and remains linking the living pools.",
       "Carbon follows several simultaneous fluxes rather than one loop: every living group respires, while only carbon-fixing producers drive the major atmospheric input shown."),

    S("bio.3.microbiology", "Microbiology & Disease", 3, "cards", {
        "arrows":True, "items":[
            {"heading":"EXPOSURE", "icon":"virus", "detail":"A pathogen crosses a body barrier and begins replicating.", "arrow":"minutes"},
            {"heading":"INNATE", "icon":"shield", "detail":"Barriers, inflammation, and phagocytes respond broadly.", "arrow":"days"},
            {"heading":"ADAPTIVE", "icon":"antibody", "detail":"Rare matching B and T cells expand into specific effectors.", "arrow":"afterward"},
            {"heading":"MEMORY", "icon":"cell", "detail":"Long-lived cells respond faster on later exposure."},
        ],
        "footer":"Vaccines present safe antigen information so adaptive memory can form without the full risks of the disease.",
    }, "A time-ordered infection diagram moves from pathogen exposure through innate defence and specific adaptive expansion to long-lived immune memory.",
       "Innate immunity acts quickly and broadly; adaptive immunity takes time to select and multiply matching cells, then preserves a faster memory response."),

    S("bio.3.botany", "Botany", 3, "flow", {
        "input_heading":"ROOT / LEAF INPUTS", "inputs":[{"label":"Soil water + ions", "icon":"water"},{"label":"CO₂ + sunlight", "icon":"sun"}],
        "process":"VASCULAR PLANT", "icon":"plant", "mechanism":"Transpiration helps pull xylem water upward; photosynthesis makes transportable sugars.",
        "output_heading":"SOURCE → SINK", "outputs":[{"label":"O₂ + water vapour via stomata", "icon":"cloud"},{"label":"Phloem sugar to roots, fruits, shoots", "icon":"seed"}],
        "in_arrow":"acquire", "out_arrow":"distribute",
        "footer":"Opening stomata gains CO₂ but loses water. Guard cells regulate this trade-off; xylem and phloem solve different transport problems.",
    }, "A vascular plant diagram joins root water uptake and leaf carbon dioxide capture to xylem transpiration and phloem sugar delivery to sinks.",
       "Plant function emerges from a constrained exchange: stomata must admit carbon dioxide while limiting water loss, and vascular tissues connect distant organs."),

    S("bio.4.biochem", "Biochemistry", 4, "graph", {
        "x_label":"Reaction progress", "y_label":"Free energy G", "x_range":(0,10), "y_range":(0,10),
        "curves":[
            {"label":"uncatalysed", "color":CORAL, "points":[(0,7),(2,7.2),(4,9.2),(6,6),(8,3.2),(10,3)]},
            {"label":"enzyme", "color":GREEN, "points":[(0,7),(2,7.1),(4,7.8),(6,5),(8,3.1),(10,3)]},
        ],
        "icon":"enzyme", "callout_heading":"WHAT CHANGES?", "callout":"The enzyme lowers activation energy by stabilising a transition pathway. Reactant and product free energies stay the same.",
        "footer":"Catalysts speed forward and reverse reactions; they do not change ΔG or the equilibrium position, and they are regenerated after turnover.",
    }, "Two reaction-coordinate curves share identical reactant and product energies, but the enzyme-catalysed pathway has a lower activation-energy peak.",
       "Enzymes alter kinetics by providing another pathway; they do not supply reaction energy or make an unfavourable equilibrium favourable."),

    S("bio.4.genomics", "Genomics", 4, "cards", {
        "arrows":True, "items":[
            {"heading":"1 · SEQUENCE", "icon":"sequence", "detail":"Read many overlapping DNA fragments with quality scores.", "arrow":"align"},
            {"heading":"2 · COMPARE", "icon":"computer", "detail":"Map reads or assemble them; call variants against evidence.", "arrow":"interpret"},
            {"heading":"3 · EDIT", "icon":"dna", "detail":"Guide RNA can direct Cas nuclease to a matching target.", "arrow":"verify"},
            {"heading":"4 · VALIDATE", "icon":"shield", "detail":"Measure intended, off-target, and phenotypic effects."},
        ],
        "footer":"A genome is not self-interpreting: sequencing error, reference bias, cell mosaicism, and biological context all affect conclusions.",
    }, "A genomics workflow moves from overlapping sequence reads through alignment and variant calling to targeted CRISPR editing and outcome validation.",
       "Genome reading and editing are evidence pipelines; confidence comes from controls, replication, and checking both intended and unintended changes."),

    S("bio.4.neuro", "Neuroscience", 4, "graph", {
        "mode":"neuro-ticks", "x_label":"Time (ms)", "y_label":"V", "x_range":(0,10), "y_range":(-90,50),
        "curves":[
            {"label":"REST / THRESHOLD", "color":BLUE,
             "points":[(0,-70),(2,-70),(3,-55)], "label_at":2, "label_dx":-105, "label_dy":-28},
            {"label":"Na⁺ IN", "color":GOLD,
             "points":[(3,-55),(3.7,35)], "label_at":1, "label_dx":105, "label_dy":-18},
            {"label":"K⁺ OUT", "color":CORAL,
             "points":[(3.7,35),(4.5,-10),(5.2,-82)], "label_at":1, "label_dx":145, "label_dy":-8},
            {"label":"RECOVERY", "color":GREEN,
             "points":[(5.2,-82),(7,-70),(10,-70)], "label_at":1, "label_dx":115, "label_dy":-24},
        ],
        "icon":"neuron", "callout_heading":"THRESHOLD + PHASES", "callout":"Crossing about −55 mV triggers positive feedback opening Na⁺ channels. Na⁺ influx depolarises; channel inactivation and K⁺ efflux repolarise, briefly undershooting rest.",
        "footer":"Action potentials are all-or-none; at the terminal, Ca²⁺ entry triggers transmitter release. Stimulus strength is encoded mainly by spike timing and frequency.",
    }, "A membrane-potential graph labels resting potential near minus 70 millivolts, threshold near minus 55, sodium-driven depolarisation, potassium-driven repolarisation, and the undershoot back to rest.",
       "The phase labels connect voltage changes to channel events and separate threshold crossing from the later calcium-triggered chemical signal at the synapse."),

    S("bio.4.evo-bio", "Evolutionary Biology", 4, "network", {
        "nodes":[
            {"id":"var","label":"MUTATION + RECOMBINATION", "icon":"dna","pos":(.05,.22),"color":PLUM},
            {"id":"pool","label":"POPULATION GENE POOL", "icon":"network","pos":(.34,.22),"color":BLUE},
            {"id":"sel","label":"SELECTION non-random", "icon":"animal","pos":(.67,.14),"color":GREEN},
            {"id":"drift","label":"DRIFT sampling chance", "icon":"particles","pos":(.67,.74),"color":GOLD},
            {"id":"freq","label":"ALLELE FREQUENCIES CHANGE", "icon":"graph","pos":(.92,.44),"color":CORAL},
            {"id":"tree","label":"PHYLOGENY inferred from shared traits", "icon":"branch","pos":(.34,.80),"color":TEAL},
        ],
        "edges":[("var","pool","variation"),("pool","sel","fitness differences"),("pool","drift","finite samples"),
                 ("sel","freq","directional"),("drift","freq","stochastic"),("pool","tree","divergence")],
        "footer":"Selection and drift can both change allele frequencies. Phylogenies use inherited similarities to reconstruct branching, not direct ancestor ladders.",
    }, "A population-genetics network separates non-random selection from random genetic drift and connects inherited divergence to phylogenetic inference.",
       "Evolutionary biology explains frequency change with multiple mechanisms and tests lineage relationships using shared derived evidence."),

    S("bio.4.physiology", "Systems Physiology", 4, "cycle", {
        "center":"BODY TEMPERATURE ≈ SET POINT", "center_icon":"body", "items":[
            {"heading":"DISTURBANCE", "icon":"sun", "detail":"Temperature rises", "arrow":"detect"},
            {"heading":"SENSOR", "icon":"brain", "detail":"Thermoreceptors signal", "arrow":"compare"},
            {"heading":"CONTROL", "icon":"system", "detail":"Hypothalamus integrates", "arrow":"command"},
            {"heading":"EFFECTOR", "icon":"water", "detail":"Sweating + skin blood flow", "arrow":"reduce error"},
        ],
        "footer":"Negative feedback opposes a disturbance; it regulates around a range and does not require every value to remain perfectly constant.",
    }, "A negative-feedback loop shows rising body temperature detected by sensors, compared by the hypothalamus, and reduced by sweating and skin blood flow.",
       "Homeostasis is active regulation: effectors change heat transfer in the direction that reduces deviation from the controlled range."),

    S("bio.4.ethology", "Animal Behaviour", 4, "matrix", {
        "columns":["SOURCE", "FITNESS LOGIC", "HOW TO TEST"],
        "rows":[
            ["Reflex / fixed action", "Inherited circuitry + cue", "Fast reliable response", "Alter cue; compare naïve animals"],
            ["Learning", "Experience changes response", "Flexibility in variable settings", "Controlled training + retention"],
            ["Cooperation", "Direct, reciprocal, or kin benefit", "Benefit must exceed relevant cost", "Measure costs, benefits, relatedness"],
        ],
        "footer":"For kin-directed helping, Hamilton's rule rB > C predicts when indirect fitness benefit can outweigh the actor's cost.",
    }, "A behaviour table contrasts inherited responses, learned responses, and cooperation by source, fitness trade-off, and experimental test.",
       "Ethology asks both proximate questions about mechanisms and ultimate questions about evolutionary consequences; either alone is incomplete."),

    S("bio.5.systems-bio", "Systems & Synthetic Biology", 5, "network", {
        "nodes":[
            {"id":"signal","label":"INPUT SIGNAL", "icon":"light","pos":(.05,.48),"color":GOLD},
            {"id":"sensor","label":"SENSOR GENE", "icon":"dna","pos":(.30,.25),"color":PLUM},
            {"id":"reg","label":"REGULATOR PROTEIN", "icon":"molecule","pos":(.55,.25),"color":CORAL},
            {"id":"output","label":"OUTPUT GENE", "icon":"dna","pos":(.82,.25),"color":GREEN},
            {"id":"product","label":"MEASURED PRODUCT", "icon":"beaker","pos":(.82,.78),"color":TEAL},
            {"id":"feedback","label":"FEEDBACK CONTROL", "icon":"cycle","pos":(.42,.78),"color":BLUE},
        ],
        "edges":[("signal","sensor","activates"),("sensor","reg","expression"),("reg","output","activates"),
                 ("output","product","expression"),("product","feedback","measure"),("feedback","sensor","represses")],
        "footer":"Synthetic circuits reuse biological parts, but behaviour emerges from network topology, rates, noise, burden, and the host-cell context.",
    }, "A synthetic gene circuit converts an input signal through sensor, regulator, and output genes, then feeds measured product back to repress the sensor.",
       "Systems biology explains phenotype from interactions and dynamics; synthetic biology tests that understanding by constructing controlled circuits."),

    S("bio.5.immunology", "Immunology", 5, "network", {
        "nodes":[
            {"id":"antigen", "label":"ANTIGEN presented", "icon":"virus", "pos":(.03,.45), "color":CORAL},
            {"id":"match", "label":"RARE MATCHING B / T CELL", "icon":"cell", "pos":(.30,.45), "color":TEAL},
            {"id":"expand", "label":"CLONAL EXPANSION", "icon":"network", "pos":(.57,.45), "color":PLUM},
            {"id":"effector", "label":"EFFECTOR CELLS act now", "icon":"antibody", "pos":(.90,.16), "color":GOLD},
            {"id":"memory", "label":"MEMORY CELLS persist", "icon":"shield", "pos":(.90,.77), "color":GREEN},
        ],
        "edges":[
            ("antigen", "match", "select"),
            ("match", "expand", "proliferate"),
            ("expand", "effector", "differentiate"),
            ("expand", "memory", "differentiate"),
        ],
        "footer":"After expansion, activated clones branch into short-lived effector and longer-lived memory populations; memory is not an effector's next stage.",
    }, "An adaptive-immunity network runs from antigen presentation to selection and expansion of a matching clone, then branches into immediate effector cells and persistent memory cells.",
       "Specificity exists before exposure; antigen expands a matching clone, whose descendants take parallel effector and memory fates under help, tolerance, and regulation."),

    S("bio.5.comp-bio", "Computational Biology", 5, "matrix", {
        "columns":["REPRESENTATION", "ALGORITHM", "BIOLOGICAL CLAIM"],
        "rows":[
            ["Sequence", "A C G T strings + quality", "Alignment / dynamic programming", "Homology or variant hypothesis"],
            ["Structure", "3-D coordinates / contacts", "Energy search or learned model", "Fold and binding hypothesis"],
            ["Evolution", "Character matrix / sequences", "Likelihood or Bayesian tree", "Branching history + uncertainty"],
        ],
        "footer":"A computational score is not biological truth: benchmark data, null models, uncertainty, and independent experiments determine what the output supports.",
    }, "A three-row computational biology pipeline maps sequences, structures, and evolutionary data to algorithms and explicitly limited biological hypotheses.",
       "Bioinformatics converts representations into ranked explanations; validation and uncertainty are part of the inference, not optional afterthoughts."),

    S("bio.5.frontier", "Frontiers of Biology", 5, "matrix", {
        "columns":["WHAT IS ESTABLISHED", "OPEN MECHANISM", "DISCRIMINATING EVIDENCE"],
        "rows":[
            ["Origin of life", "Some molecular systems self-assemble; templated polymers can copy with errors", "Path from geochemistry to evolvable cells", "Prebiotic pathway under plausible conditions"],
            ["Ageing", "Damage, regulation, and selection all contribute", "Which causes dominate by tissue and age", "Interventions that extend healthy function"],
            ["Life elsewhere", "Life alters chemistry on Earth", "How often life begins and persists", "Multiple contextual biosignatures, not one gas"],
        ],
        "footer":"Frontier science separates observation from explanation and asks which feasible measurement would make competing hypotheses diverge.",
    }, "A frontier-evidence matrix separates established observations, open mechanisms, and discriminating tests for origins of life, ageing, and extraterrestrial life.",
       "Unsolved biology advances when broad questions become competing, risky predictions that new data can distinguish."),
]


SPECS = {item["id"]: item for item in _LIST}

if len(SPECS) != len(_LIST):
    raise ValueError("Duplicate biology illustration identifier")
