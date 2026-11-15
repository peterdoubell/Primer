# Quantifier scope study

The Linguistics lesson already contains a PP-attachment tree model. This activity addresses its separate quantifier-scope assessment: “Every child climbed a tree.” Learners edit a relation through a keyboard-accessible table and inspect the identical edges on a labelled map. Both scope orders show witnesses and counterexamples. A scene-building challenge tests each-only, both, neither, and the impossible shared-only combination.

The first reading allows the witness tree to vary; it does not require different trees. The second requires a common witness, not exactly one tree. The displayed domains contain exactly three children and three trees, and unchecked cells are false. The included implication argument applies outside the finite example. Natural-language context and relative reading preferences are not modelled.

Primary teaching reference: [forall x: Calgary, chapter 25.3](https://forallx.openlogicproject.org/html/Ch25.html), quantifier order and the quantifier-shift fallacy. The activity uses original wording and graphics.

`node tools/check_quantifier_scope.cjs` checks all 512 relations against an independent set-based oracle: 343 satisfy the per-child reading, 169 satisfy the common-tree reading, 174 satisfy only the first, and 169 satisfy neither. Every witness list is verified. Shared-only is impossible in all states; the explanatory argument establishes the implication generally.

`NODE_PATH=PATH_TO_PLAYWRIGHT node tools/check_quantifier_scope_browser.cjs` exhausts the same 512 scenes through actual checkbox changes, comparing SVG edges, checked states and displayed truth values with a separately computed oracle. It also checks challenges, feedback clearing, keyboard Space input and 320/390/1440px layouts. Authenticated local reader verification checks the lesson link and return path.
