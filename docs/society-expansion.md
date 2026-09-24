# Society-domain curriculum expansion

This contribution adds four independently navigable fields, each with two authored modules at every stage: ages 3–5, ages 6–9, ages 10–12, ages 13–17, undergraduate, and master's. The 48 modules are broad disciplinary pathways rather than a claim to exhaust every specialty or satisfy a particular qualification framework.

| Field | Early foundations | Undergraduate study | Master's work |
| --- | --- | --- | --- |
| Business & Economics | Needs, limited resources, work, exchange | Microeconomic models, strategic behaviour, causal evaluation | Econometric identification and a research-based organizational strategy capstone |
| Law, Civics & Public Life | Shared rules, community, rights, fair participation | Comparative institutions, policy evaluation | Sociolegal research methods and institutional reform analysis |
| Education & Learning Sciences | Curiosity, practice, recall, teaching a friend | Assessment validity and educational research | Evidence synthesis and iterative learning-design research |
| Communication & Media | Messages, fiction, source and purpose | Communication theory, content and audience methods | Causal media-effects research and platform-governance capstone |

Each module includes an original teaching overview, a worked example, a practical or research activity, a reflection prompt, three learning outcomes, two article entry points, explicit prerequisite links, a subject-specific concept-diagram specification and a model-family/context suggestion. Stage 0–1 modules include short read-aloud-friendly child text and six authored choice questions. Every older module has ten authored choice questions plus one scenario-based produced response with three hand-selected scoring keywords present in the model answer. There are 448 authored questions across these fields.

Young learners use familiar fictional situations with adult support. Older learners progressively distinguish observation from inference, models from evidence, causal effects from associations, and aggregate results from distributional effects. Master's activities require proposals, critiques, syntheses, protocols or defended capstone recommendations, with explicit uncertainty and rival explanations.

Law and economics are conceptual education. Examples use fictional institutions, token markets and invented datasets; they do not state jurisdiction-specific rights, legal procedures or personal financial recommendations. Media exercises avoid collecting or publishing real children's private information. Education modules do not assign fixed learning-style categories.

## Primary references consulted

The lessons and assessments are original authored material. The following primary institutional sources were consulted for concepts, scope and checks; they are not copied lesson text.

- [World Bank: Impact Evaluation in Practice, second edition](https://www.worldbank.org/en/programs/sief-trust-fund/publication/impact-evaluation-in-practice): comparison designs and counterfactual reasoning.
- [World Bank: When your difference-in-differences has too many differences](https://blogs.worldbank.org/en/impactevaluations/when-your-difference-differences-has-too-many-differences): parallel trends concerns counterfactual changes, and composition/covariate issues complicate identification.
- [World Bank: Revisiting the Difference-in-Differences Parallel Trends Assumption, Part I](https://blogs.worldbank.org/en/impactevaluations/revisiting-difference-differences-parallel-trends-assumption-part-i-pre-trend): a statistically insignificant pre-trend test does not prove the required counterfactual assumption.
- [OHCHR: Universal Declaration of Human Rights](https://europe.ohchr.org/universal-declaration-human-rights): the broad dignity, equality and human-rights framing, without treating the declaration as a uniform domestic procedure.
- [IES What Works Clearinghouse: Organizing Instruction and Study to Improve Student Learning](https://ies.ed.gov/ncee/wwc/PracticeGuide/1): spaced practice, worked examples, retrieval, explanatory questioning and monitoring learning.
- [UNESCO: Media and Information Literacy Curriculum for Teachers](https://www.unesco.org/en/articles/media-and-information-literacy-curriculum-teachers): sources, audiences, purposes and media-literacy teaching scope.
- [UNESCO: Media and Information Literacy for Global Communication and Learning](https://www.unesco.org/en/media-information-literacy/global-communication-learning): contemporary scope including digital citizenship, misinformation, platforms and adaptation to context.

## Validation

`python3 tools/check_banks.py` reports CLEAN for all four new banks after a distractor-quality pass. Depth, authored produced responses, unique prompts/options, key membership, absence of forbidden graduate definitional stems, absolute-language balance and length-cue thresholds pass. This automated check does not certify teaching quality or prove that every item requires application.

A separate structural check verifies stage counts, prerequisites, model families, lesson fields, learning outcomes, visual specifications and short-answer keyword coverage without instantiating `Curriculum()`. Root integration owns photographic media, illustration rendering and model registration. Subsequent content refinements reload the JSON before writing so root-added media entries are preserved.
