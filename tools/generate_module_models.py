#!/usr/bin/env python3
"""Write exact lesson bindings for rotatable physical study objects.

A context binding deliberately describes an artifact or setting, not a simulated
abstract concept. Existing lesson-specific 3D scenes take precedence at runtime.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES = {}
for source in sorted((ROOT / 'data/curriculum').glob('*.json')):
    domain = json.loads(source.read_text())
    NODES.update((node['id'], node) for node in domain['nodes']
                 if not node['id'].startswith('rad.'))

BINDINGS = {}
def bind(domain, family, mode, context, suffixes):
    for suffix in suffixes.split():
        node_id = domain + '.' + suffix
        if node_id not in NODES:
            raise ValueError('Unknown lesson: ' + node_id)
        if node_id in BINDINGS:
            raise ValueError('Duplicate binding: ' + node_id)
        BINDINGS[node_id] = dict(family=family, mode=mode, context=context)

# Mathematics: concrete quantities, measurements and explicitly chosen examples.
bind('math','unit-blocks','model','Count the same equal units in different arrangements and compare the total with complete groups and leftovers.', '0.counting 0.compare 0.patterns 0.numbers20 1.addition 1.subtraction 1.place-value 1.multiplication 1.division 2.primes 2.order-ops 2.exponents 3.sequences')
bind('math','lattice','model','Inspect edges, equal distances and repeated positions in three perpendicular directions.', '0.shapes 1.measurement 2.geometry')
bind('math','clock','model','Relate equal angular divisions to the positions of an analog clock’s two hands.', '1.time')
bind('math','fraction-disk','model','Compare equal parts with the fixed whole; relate the selected fraction to its decimal and percentage.', '1.fractions-intro 2.fractions 2.decimals 2.percent 2.ratio')
bind('math','balance','context','Use a physical equality comparison to discuss which changes preserve or break a balance; signed numbers and algebraic symbols need the lesson’s separate definitions.', '2.negatives 2.prealgebra 3.linear 3.systems')
bind('math','surface','model','Inspect an explicit coordinate example from several directions and distinguish an input coordinate from a plotted output height.', '2.coordinates 3.slope 3.quadratics 3.functions 3.polynomials 3.trig 3.precalc 4.diff-calc 4.int-calc 4.multivar 4.diffeq 4.analysis 5.diffgeo 5.numerical 5.pde')
bind('math','urn','model','Use an inspectable finite population to connect counts, proportions and equally likely selection; broader distributions require additional assumptions.', '2.data 3.probability 3.statistics 4.prob-theory')
bind('math','lattice','context','This regular spatial construction provides a concrete example for discussing structure and relations; it does not establish the lesson’s general theorem or abstract definition.', '3.euclid 3.expo-logs 3.vectors 4.linalg 4.discrete 4.numtheory 5.abstract 5.topology')
bind('math','surface','context','Use the chosen real-valued surface as one geometric example when discussing the lesson’s more general mathematical objects; it is not a complete model of those objects.', '4.complex 5.measure 5.functional 5.complex-analysis')
bind('math','book','context','Inspect a text-bearing object as a setting for definitions, arguments and open problems; mathematical validity comes from the statements and proofs, not the object’s shape.', '5.logic 5.frontier')

# Language: material texts, reproduction and physical communication settings.
bind('lang','book','context','Inspect facing pages and their order as a physical setting for reading and writing. The displayed lines are placeholders; linguistic meaning comes from the lesson’s actual words.', '0.alphabet 0.stories 1.reading 1.spelling 1.vocabulary 1.sentences 1.handwriting 1.childrens-lit 1.writing-stories 1.dictionary 2.grammar 2.paragraphs 2.poetry 2.mythology 2.novels 2.research 3.literature 3.world-lit 3.essays 4.lit-theory 4.creative 4.classics 4.comp-lit 5.narratology')
bind('lang','stage','context','Inspect a speaker–listener arrangement to discuss voice, audience, turn-taking and interpretation; the model describes physical orientation, not speech sounds or comprehension.', '0.phonics 0.rhymes 0.speaking 2.speaking 3.shakespeare 3.rhetoric 3.linguistics-intro 3.second-language 4.linguistics 5.socioling')
bind('lang','press','context','Inspect how a reproducible text can be carried by physical type, paper and pressure; compare that material evidence with claims about a word’s history or a text’s transmission.', '2.etymology 3.media 4.history-english 5.philology')
bind('lang','experiment','context','Use the two physical stations to discuss controls and observations in language research; no language-processing results or participant responses are generated.', '5.psycholing')
bind('lang','computer','context','Inspect the physical computing substrate on which language software may run; the hardware arrangement does not represent grammar, meaning, a corpus or a language model.', '5.comp-ling')

# Physics: geometry and ideal examples, with research apparatus for abstract topics.
bind('phys','lever','model','Inspect a load, effort and pivot, and compare force with moment arm in the stated ideal static example.', '0.push-pull 1.machines 2.forces 3.energy-work')
bind('phys','camera','model','Trace straight sightlines through a pinhole and inspect the inverted image on the screen.', '0.light-shadow 1.light 3.optics-waves')
bind('phys','particles','context','Compare inspectable arrangements of enlarged particles; this static object does not calculate temperature, pressure, buoyancy or a thermodynamic process.', '0.hot-cold 0.float-sink 2.heat 2.matter 3.thermo 4.statmech')
bind('phys','pendulum','model','Relate string length and angular position to the bob’s geometry and height above its lowest point.', '1.motion 1.energy 2.gravity 3.mechanics 4.classical')
bind('phys','circuit','model','Trace the complete path in a simple ideal DC circuit and compare resistance, voltage and current; magnetic effects need a separate field description.', '2.electricity')
bind('phys','wave','context','Inspect a transverse rope example and distinguish its spatial wavelength from displacement. Sound in air and electromagnetic fields are different physical wave systems.', '1.sound 2.waves 4.em-maxwell')
bind('phys','laboratory','context','Inspect separate containers and relative measurement marks as a physical context for units, experiments and fluid observations; no flow or measurement uncertainty is calculated.', '2.units 4.fluids 4.experiment')
bind('phys','lattice','context','Inspect a repeated three-dimensional arrangement as a concrete structural example. Quantum states, elementary particles and material properties require models beyond these visible sites.', '4.solid-state 5.condensed')
bind('phys','clock','context','Inspect how a physical clock displays readings before discussing comparisons between observers; the clock geometry itself does not simulate time dilation.', '3.relativity-intro 4.relativity')
bind('phys','magnet','model','Inspect magnetic-field directions on two perpendicular planes and reverse the poles to reverse the field.', '1.magnets 3.em')
bind('phys','detector','context','Inspect concentric sensing regions around a particle-interaction point as a physical context for testing theories against measurements; no collision event or field dynamics is simulated.', '3.nuclear 4.particles 5.qft 5.frontier')
bind('phys','interference','context','Inspect coherent-light interference as a concrete experimental setting for discussing waves, measurement and quantum phenomena; the model itself computes only an ideal classical intensity pattern.', '3.modern 4.quantum 5.quantum-info')
bind('phys','telescope','context','Inspect astronomical observing equipment as a bridge from theory to measurements; its shape does not model spacetime curvature or cosmic expansion.', '5.gr-cosmo')

# Biology: visible structures are schematic and should not imply universal anatomy.
bind('bio','habitat','context','Inspect organisms within a land-and-water setting and identify the kinds of evidence needed to discuss life, behavior and environmental relationships.', '0.living 0.animals 0.seasons 1.habitats 1.food-chains 2.classification 2.ecosystems 3.evolution 3.ecology 4.evo-bio 4.ethology')
bind('bio','plant','model','Trace the spatial connection between root zone, stem and leaves while keeping plant structure distinct from the processes the lesson explains.', '0.plants 1.plants-parts 2.photosynthesis 3.botany')
bind('bio','cell','context','Inspect a simplified eukaryotic cell as one level of biological organization; the example does not model a whole body, an organ system, a disease or every kind of microbe.', '0.body 1.lifecycles 1.human-body 1.health 2.cells 2.digestion 2.reproduction 2.microbes 3.cell-bio 3.human-anatomy 3.microbiology 4.physiology 5.developmental 5.immunology')
bind('bio','dna','model','Trace paired strands and their helical arrangement while distinguishing physical DNA structure from gene function and inheritance.', '3.genetics 4.molecular 4.genomics')
bind('bio','molecule','context','Compare explicitly identified small molecules as building blocks in a biological setting; these examples do not represent an enzyme, metabolic pathway or protein structure.', '4.biochem')
bind('bio','neuron','model','Trace dendrites, cell body and axon in a generic neuron, and follow the explanatory marker toward the terminals.', '4.neuro')
bind('bio','laboratory','context','Inspect separate samples and a measurement setting to discuss biological evidence, comparisons and the limits of a model; no biological outcomes are calculated.', '5.systems-bio 5.frontier')
bind('bio','computer','context','Inspect a computing substrate used for biological data analysis; this physical board does not model a genome, organism or statistical inference.', '5.comp-bio')

# Chemistry: known small molecules and generic materials/apparatus, never fake reactions.
bind('chem','particles','context','Inspect arrangements of enlarged particles as a structural comparison; no temperature, phase change, pressure or interaction law is simulated.', '0.materials 0.water-states 1.matter 1.changes 1.materials-props 3.gases')
bind('chem','laboratory','context','Inspect distinct samples, vessel walls and liquid levels as a setting for chemical observations and measurements; colors do not identify substances or reactions.', '0.mixing 2.mixtures 2.reactions-intro 2.acids 3.stoichiometry 3.reactions 3.energy 4.physical 4.analytical 5.frontier')
bind('chem','molecule','model','Compare the stated bent, linear and tetrahedral molecular shapes; atoms and bonds are display conventions rather than electron clouds.', '2.molecules 3.bonding 3.organic-intro 4.organic')
bind('chem','lattice','context','Inspect repeated sites in a simple cubic arrangement as a material-structure example; the lattice is not an atomic orbital, periodic table, or universal crystal structure.', '2.atoms 2.periodic 3.atomic-structure 4.inorganic 5.materials')
bind('chem','molecule','context','Use small-molecule geometry to locate a structural question before discussing electronic or biochemical explanations; these examples do not calculate quantum states or model macromolecules.', '4.quantum-chem 5.biochem 5.compchem')
bind('chem','circuit','context','Inspect the complete external electrical path as a context for electrochemistry; the simple circuit does not depict ions, electrodes, redox reactions or an electrochemical cell.', '4.electrochem')

# Computer science: tangible stacks, connections and the physical substrate.
bind('cs','stack','model','Inspect an ordered stack of numbered cards, add or remove the top card, and keep insertion order distinct from the cards’ spatial display.', '0.instructions 0.sorting 0.patterns 1.algorithms 1.blocks 2.programming 2.data-types 2.functions 2.debugging 3.data-structures 3.algorithms')
bind('cs','unit-blocks','context','Use countable physical tokens as a setting for discussing discrete quantities; color and row position do not automatically encode binary digits.', '1.binary')
bind('cs','computer','context','Inspect processor, memory and their physical support as one implementation setting for the lesson’s software abstractions; dimensions and component count do not encode program semantics or speed.', '1.parts 2.bigo-intro 3.oop 3.hardware 4.algorithms-adv 4.theory 4.os 4.ml 4.systems 5.complexity 5.deep-learning 5.pl-theory 5.quantum 5.frontier')
bind('cs','network','context','Inspect client devices and explicit links, then separate this physical topology from the lesson’s protocols, logical services and security claims.', '2.internet 3.web 3.versioncontrol 4.networks 4.security 5.distributed')
bind('cs','stack','context','Use an inspectable ordered collection to discuss how information is represented and retrieved; this LIFO example does not model a relational database, query plan or transaction.', '3.databases 4.databases-adv')

# History: invented contexts and evidence-bearing artifacts avoid false reconstructions.
bind('hist','book','context','Inspect a material source as an object with ordered surfaces and a binding; the history of people and events must be established from evidence beyond this invented book.', '0.family 1.timelines 3.world-religions 4.historiography 4.social-history 4.law 5.political-theory 5.frontier')
bind('hist','village','context','Inspect private buildings, paths and a common place as an invented social setting; no architectural form is being assigned to a particular culture, period or political system.', '0.community 2.middle-ages 2.civics-intro 3.civics 4.political-sci')
bind('hist','excavation','context','Inspect the position of example artifacts within layered deposits; distinguish physical context from claims about dates, identity and historical meaning.', '0.longago 1.ancient 2.civilizations 5.anthropology')
bind('hist','globe','model','Locate a position on a spherical coordinate grid while keeping that grid separate from historical borders, routes and identities.', '1.maps 2.geography 4.geopolitics')
bind('hist','press','context','Inspect the physical alignment of type, paper and pressure as one setting for discussing the production and circulation of information.', '1.inventions 3.early-modern 3.industrial')
bind('hist','ship','context','Inspect cargo space and sailing equipment as one material context for movement and exchange; historical routes, labor, coercion and economic effects are not inferred from the vessel.', '2.exploration 3.modern-world 5.world-systems')
bind('hist','meeting','context','Inspect a shared decision setting as a context for economic choices and institutions; the arrangement supplies no prices, preferences, equilibria or evidence about real behavior.', '3.economics-intro 4.economics 5.economic-theory')

# Earth and space: geometry, invented landforms and real classes of instruments.
bind('earth','orbit','model','Inspect an orbit’s plane and position around a central body while keeping the circular example distinct from real planetary data.', '0.sky 1.seasons 1.solar-system 2.planets 3.space-exploration 4.planetary')
bind('earth','landscape','model','Inspect how a horizontal water surface intersects an invented landform; compare relief, elevation and the exposed land–water boundary.', '0.land-water 1.water-cycle 2.geology 2.oceans 3.earth-science')
bind('earth','landscape','context','Use a land–water boundary as one physical setting for the lesson’s environmental systems; moving the water plane does not forecast weather, climate or environmental change.', '0.weather 2.atmosphere 2.environment 3.climate-sci 4.climatology 4.oceanatmos 5.earth-systems')
bind('earth','excavation','context','Inspect layers and exposed sections as a setting for reasoning from geological evidence; the invented deposits do not represent Earth’s interior or establish absolute ages.', '1.rocks 4.geophysics')
bind('earth','telescope','context','Inspect observing equipment and its aperture as a physical connection to astronomical evidence; the instrument does not simulate stars, galaxies or cosmic evolution.', '2.stars 3.astronomy 4.astrophysics 5.cosmology 5.frontier')
bind('earth','habitat','context','Inspect land, water and organisms as a physical setting for questions about living environments; the invented scene does not imply life has been found beyond Earth.', '3.ecology-earth 5.astrobiology')

# Arts: spatial inspection of material practice, performance and instruments.
bind('arts','studio','context','Inspect the picture surface, its physical support and the surrounding viewpoint as a setting for making and interpreting visual art; the painted marks are only an example.', '0.colors 0.drawing 1.elements 1.crafts 2.art-history-intro 2.color-theory 3.art-history 4.aesthetics 4.art-theory 5.theory-advanced 5.creative-practice 5.frontier')
bind('arts','stage','context','Inspect a performer’s orientation to shared performance space and an audience; no sound, choreography or emotional response is simulated.', '0.singing 0.dance 2.theatre 4.world-arts')
bind('arts','instrument','context','Inspect strings, bridge and resonating body as a material setting for music; the geometric controls do not produce sound, notation or a composition.', '1.instruments 1.beat 2.music-reading 3.music-theory 3.music-history 4.composition')
bind('arts','instrument','context','Inspect strings, bridge and resonating body as the physical setting for performed music. Study the lesson’s engraved score and listening lab for its actual pitches, rhythm and harmony; this spatial object does not generate those musical relationships.', '2.music-grade-1 2.music-grade-2 2.music-grade-3 3.music-grade-4 3.music-grade-5 3.music-grade-6 3.music-grade-7 3.music-grade-8')
bind('arts','camera','model','Trace projection through a pinhole to distinguish object size, image size, inversion and viewpoint.', '2.photography 3.film-studies')
bind('arts','architecture','model','Inspect columns, equal bays and a supported roof as one spatial study of proportion, rhythm and enclosure.', '3.design')

# Mind and society: contexts are deliberately not visual diagnoses or moral metrics.
bind('mind','meeting','context','Inspect a shared discussion setting and access to common material. Feelings, values, relationships and social roles are not encoded by the figures’ positions or colors.', '0.feelings 0.fair 0.choices 1.friendship 1.money-sense 1.rules 2.society 3.ethics 4.ethics-adv 4.economics-behav 5.political-phil')
bind('mind','experiment','context','Inspect two equally arranged stations to discuss observations, controls and fair comparisons; no participant data, psychological outcomes or causal conclusions are supplied.', '1.thinking 2.psychology-intro 2.study-skills 3.critical 3.psychology 3.social-science 4.epistemology 4.philsci')
bind('mind','book','context','Inspect a physical carrier of arguments, definitions and alternative interpretations. Logical validity and philosophical claims depend on content, not on the object’s dimensions.', '2.logic-intro 2.big-questions 3.logic 3.philosophy-intro 4.metaphysics 5.logic-advanced 5.phil-language 5.frontier')
bind('mind','neuron','context','Inspect a generic neuron as one biological level relevant to mind research; it does not explain consciousness, diagnose mental states or reduce the lesson’s philosophical question to anatomy.', '4.cognitive-sci 5.phil-mind')

FAMILY_TITLES = {
 'magnet':'Bar magnet and field directions','detector':'Layered particle detector','interference':'Two-slit optical bench',
 'unit-blocks':'Counting blocks','balance':'Equal-arm balance','surface':'Coordinate surface',
 'urn':'Probability urn','book':'Bound book','press':'Printing press','stage':'Speaking and performance space',
 'lever':'Lever and fulcrum','pendulum':'Pendulum','wave':'Transverse wave on a rope','camera':'Pinhole camera',
 'circuit':'Simple electric circuit','particles':'Particle chamber','plant':'Plant and root system',
 'habitat':'Habitat cross-section','cell':'Cell cutaway','dna':'DNA double helix','neuron':'Neuron structure',
 'molecule':'Molecular shapes','lattice':'Crystal lattice','laboratory':'Laboratory vessels',
 'computer':'Computer architecture','network':'Connected computers','village':'Settlement and shared space',
 'excavation':'Archaeological excavation','ship':'Sailing vessel','globe':'Latitude and longitude globe',
 'landscape':'Landform and water level','orbit':'Circular orbit geometry','telescope':'Reflector telescope',
 'instrument':'Plucked string instrument','architecture':'Post-and-lintel pavilion','meeting':'Shared discussion table',
 'experiment':'Two-condition experiment station','fraction-disk':'Partitioned disk','clock':'Clock face and hands',
 'stack':'Stack of data cards','studio':'Artist’s easel',
}
for node_id, node in NODES.items():
    if node.get('lesson'):
        family = node['model_family']
        if family not in FAMILY_TITLES or not node.get('model_context'):
            raise ValueError('Expansion lesson needs a known model and an authored context: ' + node_id)
        BINDINGS[node_id] = dict(family=family, mode='context', context=node['model_context'])
if set(NODES) != set(BINDINGS):
    raise ValueError('Unbound lessons: ' + ', '.join(sorted(set(NODES)-set(BINDINGS))))
models=[]
for node_id, node in NODES.items():
    binding=BINDINGS[node_id]
    family=binding['family']
    models.append({
        'node_id':node_id,
        'family':family,
        'title':FAMILY_TITLES[family] + ' · 3D study',
        'instructions':'Drag or use the camera buttons to inspect the object from different sides. Change the labeled controls, then compare the geometry with the explanation below.',
        'context':node['title'] + ': ' + binding['context'],
        'mode':binding['mode'],
    })
output=ROOT/'data/module-models.json'
output.write_text(json.dumps({'version':1,'models':models},ensure_ascii=False,indent=2)+'\n')
print(f'{len(models)} exact lesson bindings; {len(set(m["family"] for m in models))} object families → {output}')
