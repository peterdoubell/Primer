"""Measures the actual defect rate of quiz.cloze_from_text's auto-generated
items, independent of the generator's own internal guards — a checker that
reused cloze_from_text's own rejection logic to grade cloze_from_text would
prove nothing. Every check here is a fresh, independent read of the item.

Its 0% is therefore NOT the defect rate — it is the share of items broken in
ways a regex can see. The rate that counts is hand-measured: 29 of 40, 72.5%,
in tools/hand-audit-cloze-2026-08.md, drawn by tools/audit_cloze.py from real
cached article text. Read that file before quoting a number from this one.

Run: .venv/bin/python tools/audit_cloze_defects.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer import quiz

# A representative corpus, not the live Wikipedia feed — this keeps the audit
# reproducible and fast, and covers the shapes selfcheck items actually see:
# short paragraphs, dense fact statements, dates, and proper nouns, across
# unrelated subjects so no single topic's phrasing style dominates the count.
CORPUS = [
    ("Photosynthesis", "Photosynthesis is the process by which plants convert light energy into chemical energy. Chlorophyll absorbs sunlight inside the chloroplast. The process produces oxygen as a byproduct. Glucose is stored as an energy source for the plant. Most photosynthesis occurs in the leaves of a plant."),
    ("Roman Empire", "The Roman Empire was founded in 27 BC when Augustus became the first emperor. It grew to control the entire Mediterranean basin at its height. The empire split into western and eastern halves in 285 AD. The western half collapsed in 476 AD. The eastern half, later called the Byzantine Empire, survived for another thousand years."),
    ("Volcanoes", "A volcano forms where magma from within the Earth's crust reaches the surface. Pressure builds beneath the surface until an eruption releases it. Lava, ash, and gases are expelled during an eruption. Mount Vesuvius famously destroyed Pompeii in 79 AD. Volcanic soil is often extremely fertile for agriculture."),
    ("Great Barrier Reef", "The Great Barrier Reef is the world's largest coral reef system, located off the coast of Queensland, Australia. It stretches over 2,300 kilometers and comprises nearly 3,000 individual reefs. Rising ocean temperatures have caused significant coral bleaching events since 1998. The reef supports an extraordinary diversity of marine life. UNESCO designated it a World Heritage Site in 1981."),
    ("The printing press", "Johannes Gutenberg introduced the movable-type printing press to Europe around 1440. Before this, books were copied by hand, a slow and expensive process. The printing press dramatically lowered the cost of producing books. It contributed to rising literacy rates across Europe. The Gutenberg Bible, printed around 1455, was among the first major books produced this way."),
    ("Photosynthesis in algae", "Algae also perform photosynthesis, much like land plants. Many algae live in oceans, lakes, and rivers. Some algae are single-celled, while others form large colonies like kelp forests. Algae produce a significant portion of the planet's oxygen. Excessive nutrient runoff can trigger harmful algal blooms."),
    ("The water cycle", "The water cycle describes the continuous movement of water on, above, and below the surface of the Earth. Evaporation converts liquid water into vapor. Condensation forms clouds as vapor cools. Precipitation returns water to the surface as rain or snow. Groundwater eventually flows back into rivers and oceans, completing the cycle."),
    ("Magnetism", "A magnet produces a magnetic field that exerts force on certain other materials, particularly iron, nickel, and cobalt. Every magnet has a north pole and a south pole. Like poles repel each other, while opposite poles attract. Earth itself behaves like a giant magnet due to its molten iron core. Compasses rely on this natural magnetism to indicate direction."),
    ("The stock market", "A stock market is a marketplace where shares of publicly traded companies are bought and sold. The New York Stock Exchange, founded in 1792, is one of the oldest and largest exchanges in the world. Stock prices fluctuate based on supply, demand, and investor sentiment. A stock index tracks the performance of a group of stocks together. Market crashes can wipe out significant wealth in a short period."),
    ("Bees", "Bees are flying insects closely related to wasps and ants, known for their role in pollination. A single beehive can contain tens of thousands of individual bees. Worker bees collect nectar and pollen from flowers. Honey is produced by bees as a stored food source for the colony during winter. Bee populations have declined sharply in recent decades due to habitat loss and pesticide exposure."),
    ("Quantum computing", "Quantum computing uses quantum bits, or qubits, instead of classical binary bits. A qubit can exist in a superposition of states simultaneously. Quantum entanglement allows qubits to be correlated in ways classical bits cannot. Google claimed quantum supremacy with its Sycamore processor in 2019. Error correction remains one of the biggest obstacles to building practical quantum computers."),
    ("The French Revolution", "The French Revolution began in 1789 amid widespread economic crisis and social inequality. The storming of the Bastille on July 14 became a symbolic turning point. King Louis XVI was executed by guillotine in 1793. The Reign of Terror under Robespierre led to thousands of executions. Napoleon Bonaparte eventually rose to power in the revolution's aftermath."),
    ("Antarctica", "Antarctica is the coldest, driest, and windiest continent on Earth. It holds roughly 90 percent of the world's ice. No permanent human population lives there, only rotating scientific researchers. The continent is governed by the Antarctic Treaty, signed in 1959. Emperor penguins are among the few species able to survive its harshest winters."),
    ("Shakespeare's plays", "William Shakespeare wrote 39 plays during his lifetime, spanning tragedies, comedies, and histories. Hamlet is considered one of his greatest tragedies. The Globe Theatre in London staged many of his works. Shakespeare's plays remain widely performed more than four centuries after his death. His influence on the English language includes hundreds of commonly used phrases."),
    ("Nuclear fission", "Nuclear fission splits a heavy atomic nucleus into two smaller nuclei, releasing energy. Uranium-235 is a commonly used fuel in nuclear reactors. A chain reaction occurs when released neutrons trigger further fission events. Nuclear power plants generate electricity using controlled fission reactions. The 1986 Chernobyl disaster remains the worst nuclear accident in history."),
    ("Coral bleaching", "Coral bleaching occurs when corals expel the symbiotic algae living in their tissues. Rising ocean temperatures are the primary cause of mass bleaching events. Bleached coral is not dead but becomes highly vulnerable to disease. Severe or prolonged bleaching often leads to coral death. Reef ecosystems can take decades to recover from a major bleaching event."),
    ("The internet's origins", "The internet grew out of ARPANET, a project funded by the US Department of Defense in 1969. Email became one of the earliest widely used applications on early networks. Tim Berners-Lee invented the World Wide Web in 1989 while working at CERN. The number of internet users worldwide surpassed one billion around 2005. Broadband access dramatically changed how people consume media online."),
    # Extended when quiz.py gained a word-class filter on distractors: the
    # filter cut per-paragraph yield roughly in half (a distractor must now be
    # substitutable for the key, and a five-sentence paragraph rarely offers
    # three such words), which left the old corpus too thin to measure a rate
    # against. More paragraphs, same shapes — the corpus grew, the bar did not.
    ("Plate tectonics", "The Earth's outer shell is divided into large plates that move slowly over the mantle. Plate boundaries produce earthquakes, mountain ranges, and ocean trenches. The theory of continental drift was proposed by Alfred Wegener in 1912. Seafloor spreading provided the mechanism that Wegener's theory lacked. The Himalayas formed where the Indian plate collided with the Eurasian plate."),
    ("Vaccination", "A vaccine trains the immune system to recognise a pathogen before an infection occurs. Edward Jenner demonstrated the principle with cowpox in 1796. Smallpox was declared eradicated worldwide in 1980. Vaccines contain weakened or inactivated material from the target organism. Widespread immunisation protects people who cannot be vaccinated themselves."),
    ("The Silk Road", "The Silk Road was a network of trade routes connecting China with the Mediterranean world. Merchants carried silk, spices, glass, and precious metals along these routes. The routes also carried religions, technologies, and diseases between distant regions. Chinese silk reached the Roman Empire by the first century. Maritime trade eventually displaced much of the overland traffic."),
    ("Photography", "A camera records an image by focusing light onto a light-sensitive surface. Louis Daguerre announced the daguerreotype process in 1839. Roll film made photography accessible to amateurs at the end of the century. Colour processes became commercially practical in the 1930s. Digital sensors replaced film for most purposes during the 2000s."),
    ("Antibiotics", "An antibiotic kills bacteria or prevents them from multiplying. Alexander Fleming observed the effect of penicillin mould in 1928. Mass production of penicillin began during the Second World War. Antibiotics have no effect on viral infections such as influenza. Overuse of antibiotics drives the spread of resistant bacterial strains."),
    ("The Amazon rainforest", "The Amazon rainforest covers much of the Amazon basin in South America. It contains a large share of the planet's known plant and animal species. The forest exchanges enormous quantities of water with the atmosphere. Deforestation for cattle ranching and soy farming has cleared large areas. The Amazon river discharges more water than any other river on Earth."),
    ("Gravity", "Gravity is the attraction between objects that have mass. Isaac Newton published his law of universal gravitation in 1687. Albert Einstein described gravity as the curvature of spacetime in 1915. The gravitational pull of the Moon produces ocean tides on Earth. Objects in orbit are in continuous free fall around a larger body."),
    ("The Industrial Revolution", "The Industrial Revolution began in Britain during the eighteenth century. Steam power replaced water and muscle as the main source of mechanical energy. Textile manufacture moved from cottages into large factories. Railways reduced the cost of moving goods across long distances. Urban populations grew rapidly as workers moved toward industrial centres."),
    ("Ecosystems", "An ecosystem includes every organism in an area together with its physical surroundings. Producers capture energy and pass it to consumers along a food chain. Decomposers return nutrients from dead material to the soil. Removing a predator can allow prey populations to expand sharply. Ecosystems recover from disturbance at very different speeds."),
    ("The periodic table", "Dmitri Mendeleev published an early periodic table in 1869. Elements are arranged by atomic number across the modern table. Elements in the same column share similar chemical behaviour. Mendeleev left gaps for elements that had not yet been discovered. The noble gases occupy the rightmost column of the table."),
    ("Ancient Egypt", "Ancient Egypt developed along the fertile banks of the Nile. The annual flood deposited silt that supported intensive agriculture. The Great Pyramid at Giza was built for the pharaoh Khufu. Hieroglyphic writing recorded religious texts and administrative accounts. The Rosetta Stone allowed scholars to decipher the script in the nineteenth century."),
    ("Sound", "Sound travels as a pressure wave through a material medium. The frequency of a wave determines the pitch that a listener perceives. Sound moves faster through water than through air. Human hearing covers roughly twenty to twenty thousand hertz. Echoes occur when a wave reflects from a distant surface."),
    ("Cartography", "A map projection flattens a curved surface onto a plane. Every projection distorts area, shape, distance, or direction to some degree. The Mercator projection preserves angles and helped sailors navigate. Modern maps combine satellite imagery with surveyed ground measurements. Scale describes the ratio between map distance and real distance."),
    ("The immune system", "The immune system defends the body against bacteria, viruses, and parasites. White blood cells identify and destroy material the body treats as foreign. Antibodies bind to specific molecules on the surface of a pathogen. Memory cells allow a faster response to a second exposure. An autoimmune disorder occurs when the system attacks healthy tissue."),
    ("Renaissance art", "The Renaissance began in Italian city states during the fourteenth century. Linear perspective allowed painters to represent depth on a flat panel. Wealthy families such as the Medici funded workshops and public commissions. Leonardo da Vinci combined anatomical study with painting. Oil paint allowed slower work and richer colour than earlier tempera."),
    ("Deserts", "A desert is a region that receives very little precipitation each year. The Sahara is the largest hot desert on the planet. Desert temperatures can swing sharply between day and night. Many desert plants store water in thickened stems or leaves. Sand dunes form where wind moves loose grains across open ground."),
    ("Bridges", "A bridge carries a road or railway across an obstacle such as a river. An arch transfers load outward into the supports at each end. A suspension bridge hangs its deck from cables strung between tall towers. The Brooklyn Bridge opened to traffic in 1883. Engineers must allow for expansion as materials warm and cool."),
    ("Migration of birds", "Many bird species travel long distances between breeding and wintering grounds. The Arctic tern makes one of the longest annual journeys of any animal. Birds navigate using the sun, the stars, and the magnetic field of the Earth. Some species gain large fat reserves before departure. Habitat loss along a route can affect populations at both ends of it."),
    ("Money", "Money serves as a medium of exchange, a store of value, and a unit of account. Early societies traded goods directly through barter. Coins of standard weight appeared in Lydia around the seventh century BCE. Paper currency circulated widely in China long before it reached Europe. Central banks now control the supply of currency in most countries."),
    ("Glaciers", "A glacier forms where snow accumulates faster than it melts each year. The weight of accumulated snow compresses the lower layers into dense ice. Glaciers carve valleys with steep walls and flat floors. Moraines are ridges of debris left behind by a retreating glacier. Most mountain glaciers have lost mass steadily in recent decades."),
    ("Theatre", "Greek drama grew out of religious festivals honouring Dionysus. Actors performed in open air amphitheatres carved into hillsides. A chorus commented on the action and addressed the audience directly. Roman theatre borrowed heavily from Greek models. Masks allowed a small cast to represent many characters."),
    ("Earthquakes", "An earthquake releases stored energy when rock along a fault slips suddenly. Seismic waves radiate outward from the point of rupture. The moment magnitude scale describes the energy released by an event. Buildings on soft sediment suffer more damage than those on bedrock. Aftershocks can continue for weeks after a large earthquake."),
    ("Coffee", "Coffee is brewed from the roasted seeds of a tropical shrub. Cultivation spread from Ethiopia into Yemen and then across the Ottoman world. Coffee houses became centres of conversation in seventeenth century Europe. Brazil produces more coffee beans than any other country. Roasting temperature strongly affects the flavour of the finished drink."),
    ("Trains", "A railway carries wheeled vehicles along fixed steel rails. Steam locomotives dominated rail transport through the nineteenth century. Diesel and electric traction replaced steam in most countries after 1950. High speed lines connect many major cities in Japan and Europe. Freight trains move bulk cargo at low cost per tonne."),
    ("Whales", "Whales are marine mammals that breathe air through blowholes. The blue whale is the largest animal known to have existed. Baleen whales strain small organisms from great volumes of seawater. Toothed whales hunt individual prey using echolocation. Commercial whaling reduced several populations to a fraction of their former size."),
    ("Clocks", "A clock measures the passage of time using a regular repeating process. Mechanical clocks with escapements appeared in European towns during the fourteenth century. A pendulum swings with a period that depends mainly on its length. Quartz crystals vibrate at a very stable frequency when supplied with current. Atomic clocks define the modern standard for the second."),
    ("Rivers", "A river carries water from higher ground toward a lake or an ocean. The area drained by a river is called its basin. Meanders form where flowing water erodes one bank and deposits on the other. A delta builds where sediment settles as a river enters still water. Floodplains support fertile soils and dense human settlement."),
    ("Chess", "Chess is played by two opponents on a board of sixty-four squares. The game descends from earlier games played in India and Persia. Modern rules for the queen and bishop settled in Europe around 1500. Wilhelm Steinitz became the first recognised world champion in 1886. Computer programs have defeated the strongest human players since the 1990s."),
    ("Volcanic islands", "Many islands form where volcanic activity builds land above sea level. Hawaii sits above a persistent hot spot in the Pacific plate. Iceland straddles the boundary between two spreading plates. New volcanic rock weathers into fertile soil over time. Isolated islands often develop species found nowhere else."),
    ("Paper", "Paper is made from cellulose fibres pressed into thin sheets. Cai Lun refined the manufacturing process in China around 105 CE. Knowledge of papermaking reached Europe through the Islamic world. Mechanised mills lowered the price of paper during the nineteenth century. Recycled fibre now supplies a large share of packaging material."),
    ("Bacteria", "Bacteria are single-celled organisms without a nucleus. They live in soil, water, and inside larger organisms. Some bacteria fix nitrogen that plants cannot obtain from the air. Many bacterial species reproduce by dividing every twenty minutes under good conditions. Gut bacteria help break down food that human enzymes cannot digest."),
    ("Weather forecasting", "Forecasters predict conditions by solving equations that describe the atmosphere. Observations arrive from ground stations, balloons, aircraft, and satellites. Numerical models divide the atmosphere into a grid of cells. Small errors in the starting conditions grow rapidly over several days. Forecast accuracy has improved steadily with computing power."),
    ("Opera", "Opera combines singing, orchestral music, and staged drama. The form emerged in Florence at the end of the sixteenth century. Italian remained the dominant language of opera for two hundred years. Wagner expanded the orchestra and the scale of the works. Modern productions often relocate a familiar story to a new setting."),
    ("Diamonds", "Diamond is a form of carbon with atoms arranged in a rigid lattice. The structure makes diamond the hardest natural material known. Natural diamonds crystallise deep in the mantle under great pressure. Volcanic pipes carry the crystals toward the surface. Synthetic diamonds are manufactured for industrial cutting and grinding."),
    ("Sleep", "Sleep is a reversible state of reduced responsiveness to the surroundings. The brain cycles between rapid eye movement sleep and deeper stages. Memory consolidation appears to depend on adequate sleep. Chronic shortage of sleep affects attention, mood, and immune response. Light exposure in the evening delays the onset of sleepiness."),
    ("Castles", "A castle served as both a fortress and a residence for a lord. Thick stone walls replaced earlier timber defences during the twelfth century. A moat and a drawbridge controlled access to the main gate. Gunpowder artillery made high walls increasingly vulnerable. Many surviving castles were later rebuilt as country houses."),
    ("Solar power", "A photovoltaic cell converts sunlight directly into electric current. Silicon remains the dominant material in commercial panels. Panel costs have fallen sharply over the past two decades. Output varies with cloud cover, season, and the angle of the panel. Battery storage allows solar electricity to be used after sunset."),
    ("Spiders", "Spiders are arachnids with eight legs and two body segments. Most species produce silk from glands at the rear of the abdomen. Orb weavers rebuild their webs regularly as the silk degrades. Venom subdues prey and begins digestion before feeding. Spiders consume enormous numbers of insects each year."),
    ("Universities", "The earliest European universities were founded in Bologna and Paris. Students originally organised themselves into guilds to negotiate with teachers. The curriculum centred on grammar, rhetoric, logic, and later theology. Printing lowered the cost of textbooks for students. Research became a central mission of universities in the nineteenth century."),
    ("Salt", "Salt preserves food by drawing water out of bacterial cells. Coastal societies produced salt by evaporating seawater in shallow pans. Inland deposits were mined from ancient seabeds buried underground. Trade routes across the Sahara carried salt southward for centuries. Iodised salt reduced the incidence of goitre in many countries."),
    ("Comets", "A comet is a body of ice and dust that orbits the Sun. Heating near the Sun releases gas that forms a glowing coma. Solar wind pushes the tail away from the Sun. Halley's comet returns to the inner Solar System roughly every 76 years. Some comets originate in a distant cloud beyond the planets."),
    ("Dance", "Dance uses ordered movement of the body as expression or ritual. Ballet developed in Italian and French courts before becoming a theatrical form. Notation systems record choreography for later performance. Folk traditions pass steps from one generation to the next without writing. Film and video changed how widely dance styles spread."),
    ("Insurance", "Insurance spreads the cost of a rare loss across many contributors. Marine insurance developed among merchants in Italian trading cities. An actuary estimates the likely cost of future claims. Premiums reflect the risk that an individual policy represents. Reinsurance allows an insurer to transfer part of its exposure."),
    ("Forests", "A forest is a landscape dominated by trees and their associated species. Temperate forests shed leaves in response to seasonal cold. Tropical forests hold the greatest diversity of tree species. Fire clears undergrowth and releases nutrients in some forest types. Managed replanting can restore cover on cleared land."),
    ("Telescopes", "A telescope gathers light to reveal objects too faint for the eye. Refracting designs use a lens while reflecting designs use a mirror. Larger mirrors collect more light and resolve finer detail. The atmosphere blurs images, which is why some telescopes orbit above it. Radio telescopes detect wavelengths far longer than visible light."),
    ("Wool", "Wool is the fleece of sheep and certain other animals. The fibres trap air, which makes wool a good insulator. Medieval England built substantial wealth on the export of raw wool. Spinning twists cleaned fibres into a continuous yarn. Wool absorbs moisture without feeling wet against the skin."),
    ("Lighthouses", "A lighthouse marks a hazard or a harbour entrance with a visible light. The Pharos of Alexandria stood for centuries as the most famous ancient example. Rotating lenses concentrate a beam that sweeps across the horizon. Each station uses a distinct flash pattern so sailors can identify it. Automated equipment has replaced resident keepers at almost every station."),
    ("Rice", "Rice feeds a larger share of the world's population than any other single crop. Cultivation began in the Yangtze valley several thousand years ago. Flooded paddies suppress weeds and supply water through the growing season. Terraced hillsides allow rice farming on steep ground. Milling removes the outer bran layer to produce white rice."),
    ("Submarines", "A submarine controls its depth by adjusting the water held in ballast tanks. Early boats relied on hand cranks and compressed air. Diesel engines charged batteries on the surface for submerged running. Nuclear reactors allowed boats to remain underwater for months. Sonar detects other vessels by listening for sound in the water."),
    ("Cheese", "Cheese is made by coagulating milk and separating the solid curd. Rennet or acid triggers the separation of curd from whey. Ageing develops flavour as enzymes break down fats and proteins. Regional varieties reflect local breeds, pastures, and traditions. Some cheeses depend on particular moulds introduced during ripening."),
    ("Hurricanes", "A hurricane draws energy from warm ocean water near the equator. Bands of thunderstorms spiral inward toward a calm central eye. Wind speed determines the category assigned to a storm. Storm surge often causes more damage than wind alone. Landfall cuts a storm off from the warm water that sustains it."),
    ("Newspapers", "A newspaper gathers and prints reports of recent events for a general audience. Regular printed news sheets appeared in Europe early in the seventeenth century. Steam presses and cheap paper produced mass circulation titles. Advertising revenue supported large reporting staffs for over a century. Online publishing has reshaped both the audience and the economics."),
    ("Antarctic ice", "The Antarctic ice sheet holds most of the fresh water on the planet. Ice flows outward under its own weight toward the coast. Floating ice shelves buttress the glaciers behind them. Cores drilled through the ice record atmospheric conditions across long periods. Warming ocean water thins some shelves from below."),
    ("Ceramics", "Ceramics are made by shaping clay and hardening it with heat. Firing drives out water and fuses particles into a rigid body. Glazes seal the surface and give a vessel its colour. Porcelain requires higher temperatures than earthenware. Fragments of pottery survive burial and help archaeologists date a site."),
    ("Radio", "Radio carries information as modulated electromagnetic waves. Guglielmo Marconi demonstrated transmission across the Atlantic in 1901. Broadcast stations reached mass audiences during the 1920s. Frequency modulation offered better sound quality than earlier methods. Radio remains widely used where other networks are unavailable."),
    ("Elephants", "Elephants are the largest land animals alive today. A trunk serves for breathing, drinking, grasping, and communication. Herds are led by an experienced older female. Elephants remember water sources across very large ranges. Ivory poaching remains a serious threat to remaining populations."),
    ("Dictionaries", "A dictionary records the words of a language with their meanings. Samuel Johnson published an influential English dictionary in 1755. The Oxford English Dictionary traced words through documented historical usage. Lexicographers rely on large collections of real sentences. Digital dictionaries can update entries continuously."),
    ("Concrete", "Concrete hardens through a chemical reaction between cement and water. Roman builders used volcanic ash to produce durable structures. Steel reinforcement gives concrete strength under tension. The Pantheon dome remains the largest unreinforced concrete dome. Cement production accounts for a substantial share of industrial emissions."),
    ("Butterflies", "A butterfly passes through egg, larva, pupa, and adult stages. Caterpillars feed heavily to store energy for the transformation. Wing colour comes from tiny overlapping scales. Monarch butterflies travel thousands of kilometres between seasons. Many species depend on a single host plant for reproduction."),
    ("Canals", "A canal carries boats along an artificial waterway. Locks raise and lower vessels between stretches at different levels. The Erie Canal opened a route between the Great Lakes and the Atlantic. The Suez Canal shortened the voyage between Europe and Asia. Railways later took much of the freight that canals had carried."),
    ("Mushrooms", "A mushroom is the fruiting body of a fungus growing in soil or wood. Threads called hyphae spread through the substrate out of sight. Spores released from the cap disperse on air currents. Many fungi form partnerships with tree roots that benefit both. Several common species are dangerously toxic to eat."),
    ("Kites", "A kite flies when moving air pushes against a tethered surface. Kites were used in China for signalling and for measuring distances. Benjamin Franklin used a kite in an experiment on atmospheric electricity. A tail steadies the flight of a light kite in gusty conditions. Modern traction kites pull boards across water and snow."),
    ("Perfume", "Perfume blends aromatic compounds dissolved in alcohol and water. Distillation of flowers and resins spread through the Islamic world. Grasse in southern France became a centre of the trade. Synthetic molecules widened the palette available to perfumers. Top notes evaporate first, leaving heavier base notes behind."),
    ("Tunnels", "A tunnel carries a route beneath ground, water, or a mountain. Boring machines cut a circular face and line the walls behind them. Ventilation removes exhaust and supplies fresh air to workers. The Channel Tunnel links England and France beneath the sea. Ground water pressure complicates work in soft material."),
    ("Owls", "Owls are birds of prey that hunt mostly at night. Soft feather edges muffle the sound of an owl in flight. Large forward-facing eyes gather light in near darkness. Asymmetric ear openings help an owl locate prey by sound alone. Pellets of undigested bone reveal what an owl has eaten."),
    ("Windmills", "A windmill converts moving air into rotating mechanical motion. Early mills ground grain and pumped water from low land. Dutch builders raised mills that could turn to face a shifting wind. Sails were later replaced by aerofoil blades. Modern turbines generate electricity rather than mechanical power."),
    ("Marble", "Marble forms when limestone recrystallises under heat and pressure. The stone takes a high polish and cuts cleanly in any direction. Quarries at Carrara supplied sculptors throughout the Renaissance. Impurities produce the coloured veins that run through many blocks. Acid rain slowly erodes marble surfaces exposed outdoors."),
]

STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "into", "onto",
    "was", "were", "are", "has", "have", "had", "its", "their", "them",
    "which", "who", "when", "where", "while", "than", "then", "also",
    "most", "some", "such", "other", "these", "those", "over", "under",
}

MIN_STEM_CHARS = 25


def audit_item(item, source_text):
    """Independent checks — deliberately NOT reusing cloze_from_text's own
    guard logic, so this measures the generator, not its opinion of itself."""
    defects = []
    front, back = item.get("prompt", ""), item.get("answer", "")
    choices = item.get("choices", [])

    if len(front) < MIN_STEM_CHARS:
        defects.append("stem too short to give context")
    if back.lower().strip() in STOPWORDS:
        defects.append("key is a function word, not a fact")
    if len(back.strip()) < 2:
        defects.append("key is trivially short")
    if choices:
        lowered = [c.lower().strip() for c in choices]
        if len(set(lowered)) != len(lowered):
            defects.append("duplicate choices")
        if back.lower().strip() not in lowered:
            defects.append("key not among its own choices")
        if len(choices) < 3:
            defects.append("fewer than 3 total choices (including key)")
    blank_free = front.replace("______", "")
    if back.lower().strip() and back.lower().strip() in blank_free.lower():
        defects.append("key still recoverable by copying the stem")
    if not re.search(r"[a-zA-Z]", blank_free):
        defects.append("stem has no readable context at all")
    return defects


def main():
    total_items = 0
    total_defects = 0
    per_item_reports = []
    for topic, text in CORPUS:
        items = quiz.cloze_from_text(text, n=5, topic=topic)
        for item in items:
            total_items += 1
            defects = audit_item(item, text)
            if defects:
                total_defects += 1
                per_item_reports.append((topic, item.get("prompt", "")[:70], defects))

    rate = (total_defects / total_items * 100) if total_items else 0.0
    print("Sampled {} auto-generated cloze items across {} source paragraphs.".format(
        total_items, len(CORPUS)))
    print("Defective: {} ({:.1f}%)".format(total_defects, rate))
    if per_item_reports:
        print("\nDefects found:")
        for topic, stem, defects in per_item_reports:
            print("  [{}] \"{}\" -- {}".format(topic, stem, ", ".join(defects)))
    verdict = "PASS (<5% target)" if rate < 5.0 else "FAIL (>=5% target)"
    print("\n{}".format(verdict))
    return 0 if rate < 5.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
