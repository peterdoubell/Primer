"""Lesson-specific deterministic Earth-and-space science plates."""

from __future__ import annotations

from .core import BLUE, CORAL, GOLD, GREEN, PLUM, TEAL, science_spec


def S(node_id, title, stage, layout, content, alt, caption):
    return science_spec(node_id, title, stage, "earth-space", layout, content, alt, caption)


_LIST = [
    S("earth.0.weather", "Weather", 0, "cycle", {
        "center":"MOVING AIR + WATER", "center_icon":"cloud", "items":[
            {"heading":"SUN WARMS", "icon":"sun", "detail":"Land and water warm unevenly", "arrow":"evaporate"},
            {"heading":"AIR RISES", "icon":"water", "detail":"Warm moist air expands and cools", "arrow":"condense"},
            {"heading":"CLOUD FORMS", "icon":"cloud", "detail":"Droplets grow around tiny particles", "arrow":"precipitate"},
            {"heading":"RAIN / SNOW", "icon":"rain", "detail":"Drops or crystals become heavy", "arrow":"return"},
        ],
        "footer":"Wind is air moving from pressure differences; daily weather changes as heat, water vapour, and air masses move.",
    }, "A weather cycle links uneven solar heating to evaporation, rising and cooling air, cloud condensation, and rain or snow returning water.",
       "Weather is not produced by clouds alone: moving energy, water, and air pressure create the changing conditions we observe."),

    S("earth.0.land-water", "Land and Water", 0, "network", {
        "nodes":[
            {"id":"rain","label":"RAIN / SNOW", "icon":"cloud","pos":(.04,.14),"color":BLUE},
            {"id":"mount","label":"MOUNTAIN watershed", "icon":"mountain","pos":(.27,.18),"color":GOLD},
            {"id":"stream","label":"STREAMS join downhill", "icon":"water","pos":(.48,.48),"color":TEAL},
            {"id":"river","label":"RIVER erodes + carries sediment", "icon":"water","pos":(.70,.66),"color":BLUE},
            {"id":"ocean","label":"DELTA / OCEAN receives", "icon":"ocean","pos":(.94,.76),"color":PLUM},
            {"id":"ground","label":"GROUNDWATER seeps", "icon":"water","pos":(.30,.82),"color":GREEN},
        ],
        "edges":[("rain","mount","falls"),("mount","stream","gravity"),("stream","river","joins"),
                 ("river","ocean","deposits"),("rain","ground","infiltrates"),("ground","river","baseflow")],
        "footer":"A watershed is the land area draining to one outlet. Flowing water erodes high ground, transports sediment, and deposits it where flow slows.",
    }, "A watershed diagram routes rain and snow from a mountain through streams, groundwater, river, delta, and ocean while tracking erosion and deposition.",
       "Gravity connects landforms and water: drainage pathways both follow the landscape and gradually reshape it."),

    S("earth.1.solar-system", "The Solar System", 1, "scale", {
        "low_label":"NEARER THE SUN", "high_label":"FARTHER FROM THE SUN", "points":[
            {"heading":"MERCURY", "value":"rocky", "position":.02, "icon":"planet", "color":CORAL},
            {"heading":"VENUS", "value":"rocky", "position":.15, "icon":"planet", "color":GOLD},
            {"heading":"EARTH", "value":"rocky", "position":.28, "icon":"earth", "color":BLUE},
            {"heading":"MARS", "value":"rocky", "position":.41, "icon":"planet", "color":CORAL},
            {"heading":"JUPITER", "value":"gas giant", "position":.56, "icon":"planet", "color":GOLD},
            {"heading":"SATURN", "value":"gas giant", "position":.69, "icon":"ringed-planet", "color":TEAL},
            {"heading":"URANUS", "value":"ice giant", "position":.82, "icon":"planet", "color":BLUE},
            {"heading":"NEPTUNE", "value":"ice giant", "position":.96, "icon":"planet", "color":PLUM},
        ],
        "footer":"Order is shown, but sizes and gaps are not to scale. Gravity keeps planets in orbit; moons orbit planets, and small bodies also orbit the Sun.",
    }, "An ordered Solar System line names Mercury through Neptune and distinguishes four rocky planets, two gas giants, and two ice giants.",
       "The sequence is reliable while the compressed drawing is not distance or size scale—a crucial distinction when reading Solar System diagrams."),

    S("earth.1.rocks", "Rocks and Soil", 1, "cycle", {
        "center":"ROCK MATERIAL", "center_icon":"rock", "items":[
            {"heading":"IGNEOUS", "icon":"volcano", "detail":"Magma or lava cools", "arrow":"weathering"},
            {"heading":"SEDIMENT", "icon":"particles", "detail":"Fragments move and settle", "arrow":"compact + cement"},
            {"heading":"SEDIMENTARY", "icon":"layers", "detail":"Layered grains or precipitates", "arrow":"heat + pressure"},
            {"heading":"METAMORPHIC", "icon":"rock", "detail":"Solid rock recrystallises", "arrow":"melt"},
            {"heading":"MAGMA", "icon":"flame", "detail":"Molten rock", "arrow":"cool"},
        ],
        "footer":"Soil forms from weathered mineral particles mixed with water, air, and organic matter; it is more than crushed rock.",
    }, "A rock cycle connects igneous rock, transported sediment, sedimentary rock, metamorphic rock, magma, and cooling back to igneous material.",
       "Any rock can enter multiple pathways when conditions change; the cycle is a network over long time, not one compulsory sequence."),

    S("earth.1.water-cycle", "The Water Cycle", 1, "cycle", {
        "center":"WATER CHANGES PLACE + STATE", "center_icon":"water", "items":[
            {"heading":"EVAPORATE", "icon":"sun", "detail":"Solar energy lifts water vapour", "arrow":"cool"},
            {"heading":"CONDENSE", "icon":"cloud", "detail":"Droplets form in cooler air", "arrow":"grow"},
            {"heading":"PRECIPITATE", "icon":"rain", "detail":"Rain or snow falls", "arrow":"collect"},
            {"heading":"RUNOFF", "icon":"water", "detail":"Water flows to rivers and ocean", "arrow":"store"},
            {"heading":"INFILTRATE", "icon":"earth", "detail":"Some enters soil and groundwater", "arrow":"return"},
        ],
        "footer":"The Sun supplies most cycle energy; gravity returns condensed water downward. Plants add vapour through transpiration.",
    }, "A five-part water cycle follows solar evaporation through condensation, precipitation, runoff, infiltration, and return to surface reservoirs.",
       "Water is conserved while changing state and reservoir; energy and gravity drive the transfers at very different rates."),

    S("earth.2.geology", "The Changing Earth", 2, "cards", {
        "items":[
            {"heading":"DIVERGENT", "icon":"volcano", "stat":"plates separate", "detail":"Mantle rises; new oceanic crust forms at ridges. Shallow quakes occur."},
            {"heading":"CONVERGENT", "icon":"mountain", "stat":"plates approach", "detail":"Subduction makes trenches and volcanic arcs; collision thickens mountains."},
            {"heading":"TRANSFORM", "icon":"earth", "stat":"plates slide past", "detail":"Locked faults store elastic strain, then slip in earthquakes."},
        ],
        "footer":"Plate motion concentrates earthquakes, volcanism, and mountain building at boundaries, but the outcomes depend on crust type and geometry.",
    }, "Divergent, convergent, and transform boundary panels connect relative plate motion to ridges, subduction, mountains, volcanoes, and earthquakes.",
       "Tectonic hazards are surface expressions of moving lithospheric plates and accumulated stress, not random events scattered evenly over Earth."),

    S("earth.2.atmosphere", "Weather and Climate", 2, "layers", {
        "layers":[
            {"heading":"THERMOSPHERE", "detail":"Very thin air; absorbs high-energy solar radiation; many low orbits", "color":PLUM},
            {"heading":"MESOSPHERE", "detail":"Temperature falls upward; many meteors ablate", "color":BLUE},
            {"heading":"STRATOSPHERE", "detail":"Ozone absorbs ultraviolet; temperature rises upward", "color":TEAL},
            {"heading":"TROPOSPHERE", "detail":"Most air and water vapour; convection and nearly all weather", "color":GREEN},
            {"heading":"SURFACE", "detail":"Uneven heating drives pressure, wind, and climate zones", "color":GOLD},
        ],
        "footer":"Weather is short-term atmospheric state; climate is the distribution of weather over decades, shaped by latitude, circulation, surface, and composition.",
    }, "A vertical atmosphere profile places weather in the troposphere, ozone heating in the stratosphere, meteors in the mesosphere, and thin thermospheric air above.",
       "Atmospheric layers differ in temperature trend and composition; climate describes long-term statistics of the variable weather below."),

    S("earth.2.planets", "Worlds of the Solar System", 2, "cards", {
        "items":[
            {"heading":"TERRESTRIAL", "icon":"planet", "stat":"Mercury–Mars", "detail":"Small, dense, rocky surfaces; atmospheres range from nearly absent to massive."},
            {"heading":"GIANT PLANETS", "icon":"planet", "stat":"Jupiter–Neptune", "detail":"Deep H/He or ice-rich envelopes, rings, many moons, no solid outer surface."},
            {"heading":"SMALL BODIES", "icon":"rock", "stat":"asteroids + comets", "detail":"Leftover rock and ice preserve clues to formation; comet tails point away from Sun."},
        ],
        "footer":"Distance influenced available building materials, but mass, impacts, internal heat, atmosphere, and time made each world distinct.",
    }, "Three planetary families compare rocky terrestrial worlds, gas and ice giants, and smaller asteroids and comets by composition and structure.",
       "Planet categories reveal formation patterns without erasing diversity: nearby size or distance alone does not determine a world's history."),

    S("earth.2.stars", "Stars and Galaxies", 2, "scale", {
        "low_label":"LOCAL", "high_label":"LARGER STRUCTURE", "points":[
            {"heading":"EARTH", "value":"planet", "position":.04, "icon":"earth", "color":BLUE},
            {"heading":"SUN", "value":"one star", "position":.28, "icon":"star", "color":GOLD},
            {"heading":"SOLAR NEIGHBOURHOOD", "value":"nearby stars", "position":.52, "icon":"star", "color":TEAL},
            {"heading":"MILKY WAY", "value":"~100–400 billion stars", "position":.76, "icon":"galaxy", "color":PLUM},
            {"heading":"LOCAL GROUP", "value":"many galaxies", "position":.96, "icon":"network", "color":CORAL},
        ],
        "note":"The positions are nested scale levels, not equal physical distance intervals.",
        "footer":"A star shines because fusion in its hot core releases energy; a galaxy is a gravity-bound system of stars, gas, dust, and dark matter.",
    }, "A nested cosmic scale places Earth by the Sun, nearby stars, the Milky Way with hundreds of billions of stars, and the galaxy-rich Local Group.",
       "Stars and galaxies occupy different hierarchy levels: the Sun is one star inside a galaxy, not a separate kind of object from other stars."),

    S("earth.2.oceans", "Oceans and Rivers", 2, "network", {
        "nodes":[
            {"id":"sun","label":"SUN heats surface unevenly", "icon":"sun","pos":(.04,.08),"color":GOLD},
            {"id":"wind","label":"WINDS drive surface currents", "icon":"cloud","pos":(.27,.08),"color":TEAL},
            {"id":"surface","label":"SURFACE CURRENT moves heat", "icon":"ocean","pos":(.55,.08),"color":BLUE},
            {"id":"dense","label":"COLD / SALTY water sinks", "icon":"water","pos":(.84,.38),"color":PLUM},
            {"id":"deep","label":"DEEP CURRENT returns", "icon":"ocean","pos":(.58,.82),"color":BLUE},
            {"id":"moon","label":"MOON gravitational forcing", "icon":"planet","pos":(.03,.72),"color":CORAL},
            {"id":"tides","label":"TIDES periodic sea-level motion", "icon":"water","pos":(.29,.72),"color":GREEN},
        ],
        "edges":[("sun","wind","pressure"),("wind","surface","stress"),("surface","dense","cool / salt"),
                 ("dense","deep","sink"),("deep","surface","upwell"),("moon","tides","gravity")],
        "footer":"Surface currents, density circulation, and tides have different causes. Rivers deliver freshwater and sediment while gravity connects continents to ocean basins.",
    }, "An ocean network separates wind-driven surface currents and density-driven sinking and return flow from a distinct Moon-to-tides gravitational branch.",
       "Ocean motion combines multiple mechanisms; identifying the driver prevents tides, waves, currents, and river flow from being treated as one process."),

    S("earth.2.environment", "Caring for Earth", 2, "matrix", {
        "columns":["PRESSURE", "ACTION AT SOURCE", "MEASURABLE RESPONSE"],
        "rows":[
            ["Climate", "Fossil-carbon emissions", "Efficiency + low-carbon energy", "Falling net greenhouse-gas emissions"],
            ["Water", "Nutrients, toxins, plastic", "Prevent discharge + treat waste", "Lower concentration and biological harm"],
            ["Habitats", "Conversion and fragmentation", "Protect + reconnect + restore", "Native populations and functions recover"],
        ],
        "footer":"Conservation is a testable cause-and-effect process: reduce a pressure, monitor the system, and adapt when the response differs from prediction.",
    }, "An environmental action matrix links climate emissions, water pollution, and habitat loss to source-level interventions and measurable ecological responses.",
       "Effective care targets causes and tracks outcomes; visible clean-up alone may leave the upstream pressure unchanged."),

    S("earth.3.earth-science", "Earth Science", 3, "layers", {
        "mode":"concentric", "layers":[
            {"heading":"CRUST", "detail":"Thin silicate shell; oceanic and continental rocks are continually reworked", "color":GREEN},
            {"heading":"MANTLE", "detail":"Solid rock flows slowly; heat-driven convection participates in plate motion", "color":GOLD},
            {"heading":"OUTER CORE", "detail":"Liquid iron alloy; convection helps generate the magnetic field", "color":CORAL},
            {"heading":"INNER CORE", "detail":"Solid iron-rich centre despite high temperature because pressure is immense", "color":PLUM},
        ],
        "footer":"Seismic waves reveal the hidden layers; internal heat drives tectonics while sunlight and gravity drive surface weathering and sediment transport over deep time.",
    }, "A concentric Earth cross-section labels crust, slowly flowing solid mantle, liquid outer core, and pressure-solidified inner core with evidence-linked properties.",
       "Earth's rock cycle couples internal heat and plate tectonics to surface water, atmosphere, gravity, and immense geological time."),

    S("earth.3.astronomy", "Astronomy", 3, "branch", {
        "root":"STAR-FORMING CLOUD", "root_icon":"cloud", "branches":[
            {"heading":"LOW-MASS PATH", "icon":"star", "edge":"collapse + fusion", "detail":"Main sequence → red giant → planetary nebula → white dwarf."},
            {"heading":"HIGH-MASS PATH", "icon":"star", "edge":"faster fuel use", "detail":"Massive star → supergiant → core-collapse supernova → neutron star or black hole."},
            {"heading":"DISTANCE EVIDENCE", "icon":"telescope", "edge":"observe light", "detail":"Parallax calibrates nearby distances; standard candles and redshift extend the ladder."},
        ],
        "footer":"Initial mass is the main control on stellar lifetime and fate. Looking farther away also looks farther back because light travels at finite speed.",
    }, "A stellar-evolution branch contrasts low-mass stars ending as white dwarfs with high-mass stars reaching supernovae and compact remnants.",
       "Astronomy infers life cycles by comparing many stars and uses overlapping distance methods to establish the scale of the cosmos."),

    S("earth.3.climate-sci", "Climate Science", 3, "network", {
        "nodes":[
            {"id":"sun","label":"SUNLIGHT shortwave in", "icon":"sun","pos":(.04,.20),"color":GOLD},
            {"id":"surface","label":"SURFACE absorbs + emits infrared", "icon":"earth","pos":(.38,.72),"color":GREEN},
            {"id":"atm","label":"GREENHOUSE GASES absorb + emit IR", "icon":"cloud","pos":(.64,.32),"color":CORAL},
            {"id":"space","label":"SPACE outgoing energy", "icon":"star","pos":(.94,.12),"color":PLUM},
            {"id":"carbon","label":"EXTRA CO₂ raises opacity", "icon":"molecule","pos":(.12,.76),"color":BLUE},
            {"id":"feedback","label":"WATER / ICE feedbacks", "icon":"cycle","pos":(.85,.78),"color":TEAL},
        ],
        "edges":[("sun","surface","incoming"),("surface","atm","infrared"),("atm","space",""),
                 ("atm","surface",""),("carbon","atm","forcing"),("surface","feedback","warming"),("feedback","surface","amplify")],
        "footer":"Added greenhouse gas first reduces outgoing infrared at some wavelengths; the surface–troposphere system warms until outgoing energy again balances incoming sunlight.",
    }, "An energy network traces sunlight to Earth's surface, infrared through greenhouse gases to space, and carbon dioxide plus water and ice feedbacks.",
       "The greenhouse effect is radiative energy balance, not a solid lid; climate change follows a forcing, response, and feedback chain measured in multiple records."),

    S("earth.3.ecology-earth", "Biomes and Ecology", 3, "matrix", {
        "columns":["TEMPERATURE", "WATER", "DOMINANT CONSTRAINT"],
        "rows":[
            ["Tropical rainforest", "Warm year-round", "High rainfall", "Light competition; rapid nutrient cycling"],
            ["Savanna / grassland", "Warm or seasonal", "Seasonal / moderate", "Fire, grazing, drought timing"],
            ["Desert", "Often hot; can be cold", "Very low", "Water scarcity and heat balance"],
            ["Tundra", "Cold; short growing season", "Low; often frozen", "Permafrost and temperature"],
        ],
        "footer":"Biomes are broad climate–vegetation patterns, not sharp boxes. Organisms also alter soils, fire regimes, carbon storage, and atmospheric chemistry.",
    }, "A biome matrix compares rainforest, grassland, desert, and tundra by temperature, water availability, and the ecological constraint shaping life.",
       "Climate filters which strategies persist, while organisms feed back on the physical Earth through nutrient cycling, fire, soils, and carbon storage."),

    S("earth.3.space-exploration", "Space Exploration", 3, "cards", {
        "arrows":True, "items":[
            {"heading":"LAUNCH", "icon":"rocket", "detail":"Thrust greater than weight accelerates upward; propellant mass dominates.", "arrow":"gain speed"},
            {"heading":"ORBIT", "icon":"satellite", "detail":"Sideways speed makes the craft continually fall around Earth.", "arrow":"change orbit"},
            {"heading":"TRANSFER", "icon":"planet", "detail":"Timed engine burns reshape the orbit; coasting follows gravity.", "arrow":"operate"},
            {"heading":"MISSION", "icon":"earth", "detail":"Satellites, probes, or crews trade mass, power, time, risk, and data."},
        ],
        "footer":"Rockets work by expelling momentum, including in vacuum. Reaching space is easier than reaching orbit because orbital speed carries most energy demand.",
    }, "A mission sequence distinguishes launch thrust, sideways orbital free-fall, timed transfer burns, and the resource trade-offs of spacecraft operation.",
       "Spaceflight is controlled momentum and energy accounting: engines change velocity, while gravity governs the long coasting arcs between burns."),

    S("earth.4.geophysics", "Geophysics & Geochemistry", 4, "graph", {
        "x_label":"Time after earthquake", "y_label":"Ground motion", "x_range":(0,10), "y_range":(-5,5),
        "curves":[
            {"label":"P arrival", "color":BLUE, "points":[(0,0),(1,0),(2,.2),(2.4,2),(2.8,-1.5),(3.2,.8),(4,0)]},
            {"label":"S arrival", "color":CORAL, "points":[(4,0),(4.6,.3),(5,3.8),(5.5,-3.2),(6.1,2.5),(6.8,-1),(8,0)]},
        ],
        "icon":"earth", "callout_heading":"INTERIOR EVIDENCE", "callout":"P waves cross solids and liquids; S waves require shear rigidity and vanish through the liquid outer core. Travel times map boundaries.",
        "footer":"Seismology constrains structure; gravity and magnetism constrain mass and flow; rock and isotope chemistry constrain composition and age.",
    }, "A seismogram separates earlier compressional P-wave motion from later shear S-wave motion and links S-wave absence to Earth's liquid outer core.",
       "Geophysics infers inaccessible interiors by combining wave travel, gravity, magnetism, and chemical constraints rather than relying on a single measurement."),

    S("earth.4.astrophysics", "Astrophysics", 4, "graph", {
        "x_label":"Surface temperature: hotter ←     → cooler", "y_label":"Luminosity (log scale)", "x_range":(0,10), "y_range":(0,10),
        "curves":[
            {"label":"main sequence", "color":GOLD, "points":[(1,9),(2,8),(4,6.5),(6,4.5),(8,2),(9,1)]},
            {"label":"giants", "color":CORAL, "points":[(6,8),(7.5,8.6),(9,8)]},
            {"label":"white dwarfs", "color":BLUE, "points":[(1,2.5),(2.5,2),(4,1.5)]},
        ],
        "icon":"star", "callout_heading":"READ THE H–R PLANE", "callout":"Temperature sets horizontal position; luminosity and temperature imply radius. Spectra reveal composition, motion, and surface conditions.",
        "footer":"Fusion balances gravity during the main sequence. Mass sets core pressure, fusion rate, luminosity, lifetime, and eventual stellar remnant.",
    }, "A Hertzsprung–Russell-style plot places the main sequence diagonally, luminous cool giants above, and hot faint white dwarfs below.",
       "The H–R diagram turns light measurements into a physical map where location constrains stellar radius, evolutionary state, and mass-dependent lifetime."),

    S("earth.4.planetary", "Planetary Science", 4, "cards", {
        "arrows":True, "items":[
            {"heading":"DISK", "icon":"galaxy", "detail":"Dust and ice condense at temperature-dependent distances around a young star.", "arrow":"collide"},
            {"heading":"ACCRETION", "icon":"rock", "detail":"Sticking and gravity build planetesimals; impacts add and remove material.", "arrow":"heat"},
            {"heading":"DIFFERENTIATION", "icon":"planet", "detail":"Melting lets dense metal sink and lighter silicate rise.", "arrow":"evolve"},
            {"heading":"ACTIVE WORLD", "icon":"earth", "detail":"Cooling, volcanism, impacts, escape, and chemistry reshape surface and atmosphere."},
        ],
        "footer":"Comparative planetology treats each world as an experiment: mass, orbit, composition, atmosphere, and time produce different outcomes.",
    }, "A planet-formation sequence moves from a temperature-structured disk through accretion and impact heating to differentiation and long-term geological evolution.",
       "Worlds inherit starting materials from disks, then diverge through mass-dependent heat retention, atmospheric escape, impacts, and internal activity."),

    S("earth.4.climatology", "Climatology", 4, "graph", {
        "x_label":"Cumulative CO₂ emissions", "y_label":"ΔT", "x_range":(0,10), "y_range":(0,10),
        "curves":[
            {"label":"central", "color":CORAL,
             "points":[(0,0),(2,1.8),(4,3.5),(6,5.2),(8,6.9),(10,8.5)],
             "label_dx":-115, "label_dy":4},
            {"label":"upper bound", "color":BLUE,
             "points":[(0,0),(2,2.4),(4,4.4),(6,6.5),(8,8.4),(10,9.6)],
             "label_dx":-125, "label_dy":-20},
            {"label":"lower bound", "color":GREEN,
             "points":[(0,0),(2,1.2),(4,2.6),(6,3.9),(8,5.3),(10,6.6)],
             "label_dx":-125, "label_dy":22},
        ],
        "icon":"model", "callout_heading":"CARBON BUDGET", "callout":"Warming is approximately proportional to cumulative CO₂ over policy-relevant ranges. A temperature limit therefore implies a finite remaining budget.",
        "footer":"Attribution compares observed spatial, vertical, spectral, and temporal fingerprints with modelled natural and human forcings—not temperature alone.",
    }, "A central near-linear warming-versus-cumulative-carbon curve lies between explicit lower and upper response bounds, explaining why a chosen temperature limit implies an uncertain finite carbon budget.",
       "Climate models combine physical conservation laws with observations; ensembles quantify scenario and parameter uncertainty rather than eliminating it."),

    S("earth.4.oceanatmos", "Ocean & Atmospheric Science", 4, "network", {
        "nodes":[
            {"id":"heat","label":"UNEQUAL HEATING", "icon":"sun","pos":(.04,.22),"color":GOLD},
            {"id":"pressure","label":"PRESSURE GRADIENT FORCE", "icon":"cloud","pos":(.31,.20),"color":CORAL},
            {"id":"rotation","label":"CORIOLIS deflects motion", "icon":"earth","pos":(.53,.72),"color":PLUM},
            {"id":"wind","label":"WIND stress on ocean", "icon":"cloud","pos":(.65,.18),"color":TEAL},
            {"id":"ekman","label":"DEPTH-INTEGRATED EKMAN transport", "icon":"ocean","pos":(.91,.35),"color":BLUE},
            {"id":"upwell","label":"UPWELLING nutrients + cold water", "icon":"water","pos":(.82,.82),"color":GREEN},
        ],
        "edges":[("heat","pressure","creates"),("pressure","wind","accelerates"),("rotation","wind","deflects"),
                 ("wind","ekman","stress"),("rotation","ekman","NH right / SH left"),("ekman","upwell","coastal divergence")],
        "footer":"Ideal open-ocean Ekman transport is depth-integrated and 90° right of wind in the Northern Hemisphere, left in the Southern; coasts, equator, stratification, and turbulence modify it.",
    }, "A rotating-fluid network links unequal heating to pressure gradients and winds, then labels ideal depth-integrated Ekman transport as right of the wind in the Northern Hemisphere and left in the Southern Hemisphere before coastal upwelling.",
       "Ekman transport is an idealised, hemispherically signed result of wind stress, rotation, and friction; boundaries and stratification shape the observed air–sea circulation."),

    S("earth.5.cosmology", "Cosmology", 5, "scale", {
        "low_label":"EARLIER / HOTTER / DENSER", "high_label":"LATER / COOLER / STRUCTURED", "points":[
            {"heading":"HOT BIG BANG", "value":"expanding early state", "position":.02, "icon":"energy", "color":CORAL},
            {"heading":"NUCLEOSYNTHESIS", "value":"first minutes", "position":.23, "icon":"atom", "color":GOLD},
            {"heading":"CMB RELEASE", "value":"≈380,000 years", "position":.44, "icon":"light", "color":TEAL},
            {"heading":"GALAXIES", "value":"gravity grows structure", "position":.68, "icon":"galaxy", "color":PLUM},
            {"heading":"ACCELERATION", "value":"late expansion speeds up", "position":.88, "icon":"network", "color":BLUE},
            {"heading":"NOW", "value":"13.8 billion years", "position":.98, "icon":"earth", "color":GREEN},
        ],
        "note":"ORDERED BUT NOT TO TIME SCALE: the first minutes and 13.8 billion years are compressed onto one axis.",
        "footer":"Expansion stretches wavelength (cosmological redshift). CMB, light-element abundances, and large-scale structure jointly constrain the model.",
    }, "An explicitly not-to-time-scale cosmic timeline orders the hot early universe, first-minutes nucleosynthesis, cosmic microwave background release, galaxy growth, late accelerated expansion, and the present at 13.8 billion years.",
       "The compressed positions show sequence only: Big Bang cosmology describes expansion from a hot dense state, not an explosion from one location into pre-existing empty space."),

    S("earth.5.astrobiology", "Astrobiology", 5, "branch", {
        "root":"CANDIDATE WORLD", "root_icon":"planet", "branches":[
            {"heading":"HABITABILITY", "icon":"water", "edge":"conditions", "detail":"Energy, solvent, elements, and sustained environment make life possible—not certain."},
            {"heading":"BIOSIGNATURE", "icon":"molecule", "edge":"observation", "detail":"Atmospheric or surface pattern difficult to maintain abiotically in context."},
            {"heading":"CONFIRMATION", "icon":"telescope", "edge":"competing tests", "detail":"Multiple independent signals, false-positive models, repeat observations, contamination control."},
        ],
        "footer":"A habitable-zone orbit concerns possible surface liquid water under atmospheric assumptions; it is neither a detection of water nor evidence of life.",
    }, "An astrobiology evidence tree separates potentially habitable conditions from a contextual biosignature and the multiple tests required for confirmation.",
       "Life detection is an inference problem: credible claims must outperform abiotic explanations and survive instrument, stellar, geological, and contamination checks."),

    S("earth.5.earth-systems", "Earth System Science", 5, "matrix", {
        "columns":["STOCK / STATE", "FLUX OR FORCING", "COUPLED EFFECT"],
        "rows":[
            ["Atmosphere ↔ ocean", "Air and seawater heat + carbon", "Heat and CO₂ exchange", "Temperature and carbon co-evolve"],
            ["Land ↔ biosphere", "Rock, soil, water + biomass", "Water, nutrients, O₂ and CO₂", "Life alters soils and geochemistry"],
            ["Cryosphere ↔ radiation", "Ice + stored water", "Sunlight reflected to space", "Less ice → lower albedo → more absorption"],
            ["Human system", "Fuels, land + infrastructure", "Greenhouse gases + land-use change", "Forcing propagates through connected reservoirs"],
        ],
        "footer":"Stocks record amounts; fluxes record transfer rates. Albedo is a radiative feedback, not a transported stock: ice loss reduces reflection and amplifies warming.",
    }, "A four-row Earth-system matrix separates atmosphere–ocean and land–biosphere exchanges, the cryosphere's sunlight reflection to space, and human greenhouse and land-use forcing.",
       "The stock–flux–effect columns distinguish material exchange from radiative feedback: less ice lowers albedo, increases absorbed sunlight, and amplifies warming."),

    S("earth.5.frontier", "Cosmic Frontiers", 5, "matrix", {
        "columns":["DIRECT OBSERVATION", "SUPPORTED INFERENCE", "OPEN QUESTION"],
        "rows":[
            ["Gravitational waves", "Interferometer strain with matched timing / waveform", "Compact binaries radiate spacetime waves", "New sources, strong gravity, primordial background"],
            ["Dark matter", "Rotation, lensing, CMB, structure", "Additional gravitating component", "Particle identity or revised sector physics"],
            ["Dark energy", "Distance–redshift + structure expansion history", "Late cosmic expansion accelerates", "Vacuum energy, field, or gravity change"],
        ],
        "footer":"A frontier claim should preserve the chain from calibrated signal to model comparison; unexplained does not mean unconstrained.",
    }, "A cosmic-frontier matrix separates direct observations, supported physical inferences, and still-open mechanisms for gravitational waves, dark matter, and dark energy.",
       "Modern cosmology has strong evidence for several phenomena while their deeper causes remain unknown; those are different levels of uncertainty."),
]


SPECS = {item["id"]: item for item in _LIST}

if len(SPECS) != len(_LIST):
    raise ValueError("Duplicate Earth-and-space illustration identifier")
