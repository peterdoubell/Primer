# Language computation studio

`lang.5.comp-ling` gains working illustrations, tables, algorithms, maps and four
practice activities. The original illustration, ten assessment questions,
authored learning goal, article references and separate physical-computer
context remain in place. The activity does not submit quiz answers or change
mastery. All 40 language modules and the existing review-game scope remain in
`docs/language-artifact-scope-20261104.json`; this studio does not complete that
larger request or the radiology, mathematics and physics objective.

## What is calculated

The parser uses an explicitly authored context-free grammar in Chomsky normal
form: terminal rules and binary nonterminal rules only. The chart visits
half-open token spans by increasing length and adds products of child parse
counts. Packed alternatives support an indexed tree viewer without choosing a
meaning or an intended attachment. The example with two prepositional phrases
has five trees under this grammar. The parser accepts at most 14 lowercase,
whitespace-separated word tokens; an unknown word or uncovered sequence yields
zero complete trees. These outcomes are grammar coverage, not a general test of
English grammaticality, agreement, case or truth.

The two corpora are authored samples of six three-word sentences each. No
community or real-world language-use statistics are represented. Both have 18
lexical tokens; start/end markers are excluded from the type–token ratio. Each
sentence separately contributes a start marker and an end marker to the bigram
counts. The vocabulary is fixed across samples, including a reserved unknown
category and the end marker; the start marker is not a prediction target.
Conditional probabilities use `(count + k)/(context count + kV)`, with `k` equal
to zero, one half or one. An unseen unsmoothed history has no estimated row,
which is displayed as undefined. All tied maximum-probability answers are
accepted by the practice activity. Add-k here illustrates sparsity and is not
presented as a production modelling recommendation.

A separate binary-classifier activity uses constructed confusion matrices.
Precision, recall, accuracy, F1 and the majority-class baseline come directly
from the displayed counts. Zero denominators remain undefined. F1 uses the
count formula `2TP/(2TP+FP+FN)`, which can be zero even when precision has no
predicted-positive denominator. The all-negative preset has accuracy 95/100,
recall 0/5 and undefined precision. These classifier counts are not purported
outputs or evaluation results of the bigram model.

The task-identification game distinguishes sense selection, morphology, a
specified tokenization convention, coreference and grammatical class. Examples
and answers are authored annotations; no general-purpose disambiguation system
is claimed. The coreference example deliberately retains contextual ambiguity.

## Drawings and accessibility

Parse-tree nodes and edges derive from the selected packed-forest tree.
Probability-bar lengths and transition labels derive from exact fractions.
The transition map's positions are layout choices, not semantic distances;
solid and dashed edges distinguish observed transitions and smoothing-only
support. Classifier bars share a declared zero-to-one scale. Undefined values
do not become zero bars. The probability and evaluation plots fit narrow
screens; wider parse charts and trees have scroll regions and explicit pan
controls. Every diagram has adjacent textual/table evidence. Controls use
native labels and buttons; each mount owns its state and disposes its observer.

## Verification and source methods

The shipped core is loaded through its CommonJS exports. Runtime checks require
no NLTK dependency. Independent parser oracles were generated with NLTK 3.10.4's
Earley parser, using the explicit authored grammar, and stored with their
generator metadata. This uses a different parsing strategy from the shipped
bottom-up chart. The canonical generator is `tools/generate_language_computation_earley_oracles.py`
(run with NLTK 3.10.4). Earlier experiments and browser evidence are preserved
under `prototype`; they are not current-reader proof.

Twenty invalid or resource-exceeding inputs are also rejected.
Bulk case arrays keep one complete observation per line; no observations or fields
were removed during format normalization.
Current checks include 71 sentences, 156 complete trees, 6,728 independent
chart-symbol states, 384 exact probability entries and 691 confusion matrices.
The authenticated synthetic app proof covers 20 parser/tree views, 96
probability states, ten matrix states, ten ambiguity cases, 228 practice-feedback
checks, four independent mounts and two route reopens. Independent readback
checks 722 rendered chart cells, 392 tree nodes, 376 tree edges, 768 probability
cells, 704 bars, 544 transition edges and 16 metric bars. No production learner
writes or production authenticated-reader verification is claimed.

Method references: Jurafsky and Martin, *Speech and Language Processing*,
August 19, 2026 drafts of [Chapter 19](https://web.stanford.edu/~jurafsky/slp3/19.pdf)
for CNF chart parsing and [Chapter 3](https://web.stanford.edu/~jurafsky/slp3/3.pdf)
for conditional n-gram counts and smoothing; [NLTK's Earley parser documentation](https://www.nltk.org/api/nltk.parse.earleychart.html)
for the independent parser; and [Google's classification metrics documentation](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall)
for metric definitions. Implementation, sentences, corpus counts, practice
examples and figures here are original; no textbook figures or training corpus
were copied. Historical source checks use a pinned, exact byte projection that
restores only the reviewed changes and grants no approval to the new activity.
