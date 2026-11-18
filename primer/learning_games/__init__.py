"""Interactive learning sequences for every curriculum module.

A *sequence* is a short guided run through one idea: introduce it, show it on
a worked example, ask the reader to predict, check what they said, explain the
outcome, and finish by applying the idea somewhere new.  The reader acts at
every checked step — predicting, ordering, matching, classifying, filling a
missing value, making a constrained edit, deciding from the fewest clues,
comparing two structures, steering a parameter, or assembling an answer.

    authoring   the plain-text model format, its parser and validator
    evaluators  marking and targeted feedback, plus subject-supplied methods
    derived     sequences built from a module's reviewed reporting reference
    catalog     what each module has; the public projection of a step
    progress    reader checkpoints, the growth ledger entry, review cards
    api         the routes (``/api/learning-games/...``)

Sequences are study.  They never write mastery; the server-scored quiz and its
spaced passes remain the only proof the book accepts.
"""
from .api import router

__all__ = ["router"]
