# Applied STEM curriculum expansion

This addition supplies four broad learning pathways, each with two modules at every existing stage: ages 3–5, 6–9, 10–12, 13–17, undergraduate study, and master's-level inquiry. The 48 modules introduce engineering, health/public health, environment/agriculture, and architecture/design. They are foundation pathways into these fields, not comprehensive degree programs or coverage of every professional specialty.

## Authored content

Each module has a distinct teaching overview, worked example, activity, reflection, three learning outcomes, at least two article references, and a prerequisite list. Stages 0–1 include adult-supported `kid_text` and six read-aloud choice items. Stages 2–5 contain ten authored choice items and a separate scenario-based short response with at least three selected marking concepts. The total is 448 assessment items: 416 choices and 32 produced responses. Distractors in older stages were individually revised around plausible related concepts and checked for answer-length and absolute-language cues.

Master's modules require explicit research or critique: constrained optimization and validation; equitable program evaluation and reproducible public-health research; transition scenarios and adaptive environmental management; and performance-based design research and participatory studios. Activities distinguish hypotheses, observations, assumptions, uncertainty, and value judgments. None of these pathways awards a qualification or substitutes for supervised professional training.

## Field scope and boundaries

- `engineering` (`eng.*`): structures and tools progress through mechanisms, feedback, stress, energy, control, reliability, robust optimization, and research validation. Structural and device examples are educational models, not construction or safety certifications.
- `health` (`health.*`): communication and shared wellbeing progress through evidence literacy, population data, epidemiology, social determinants, causal inference, appraisal, evaluation, and research ethics. New content contains no diagnosis, medication, clinical treatment, or personalized medical guidance. Health numbers describe fictional populations. This expansion does not revise the separate pre-existing radiology curriculum.
- `environment` (`env.*`): observation and growing progress through soils, food systems, water and nutrient budgets, agroecology, field methods, sustainability transitions, and research. Management discussions are context-sensitive; examples are not site-specific farming or land-management recommendations.
- `design` (`design.*`): spaces and shelters progress through plans, user needs, scale, inclusion, climate, wayfinding, performance modeling, evaluation, and graduate research studios. Accessibility and building-performance principles are not a claim of compliance with any jurisdiction's construction standards.

## Visual and model handoff

Each module includes a `visual_spec` with three or four authored conceptual panels, a `flow` or `compare` mode, and a takeaway. Flow arrows are used for an actual sequence or transfer, not merely to connect unrelated outcomes. Numerical diagrams use clearly hypothetical values already taught in the corresponding lesson. Each module supplies a supported `model_family` and a lesson-specific `model_context` that states the representation's limits. These are input specifications for the main integration work; media assets and shared manifests are owned by the parent task.

Photographs, diagrams, and models should be identified by type. A photorealistic rendering is not measurement evidence. Generic 3D geometry is a conceptual aid rather than a validated physical simulation, medical model, or professional design tool.

## Primary-source checks

The author consulted these primary sources for conceptual definitions and framing. The lessons and fictional exercises are independently authored, not quotations or reproductions of these sources.

- WHO, [Health literacy](https://www.who.int/vietnam/news/fact-sheets/detail/health-literacy): understandable, trustworthy information and people's ability to access and use it.
- WHO, [Social determinants of health](https://www.who.int/health-topics/social-determinants-of-health): social and environmental conditions, inequities, and upstream influences.
- CDC, [Analyzing and Interpreting Data](https://www.cdc.gov/field-epi-manual/php/chapters/analyze-interpret-data.html): population measures, study comparisons, and ratios.
- FAO, [The State of Knowledge of Soil Biodiversity](https://www.fao.org/interactive/soil-biodiversity/en/): soil organisms and ecosystem functions.
- FAO, [Biodiversity and Ecosystem Services](https://www.fao.org/agriculture/crops/thematic-sitemap/theme/biodiversity/en/): ecological relationships relevant to agriculture.

## Validation

`tools/check_banks.py` reports all four new banks CLEAN, including depth, produced-response coverage, duplicate detection, length cues, naming-stem checks, and absolute-language balance. This automated audit does not certify educational completeness. A separate structural check verifies stage coverage, prerequisite existence, acyclicity, article and outcome counts, lesson fields, unique prompts, model families, visual panels, and short-answer scoring against the authored keys. The parent task owns whole-application and integrated-media tests.
