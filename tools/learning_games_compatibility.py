"""Recover the exact backend from before the learning-sequence router (2026-11-18).

The learning-sequence system adds two lines to ``primer/server.py`` that mount
``primer.learning_games.router``. Older compatibility checks restore historical
bytes of that file, so this link removes exactly those two lines, and only from
the exact current bytes recorded in ``docs/learning-games/runtime-inverse.json``.
Any other change to the file leaves it untouched here, so it still fails the
checks further down the chain.
"""
from pathlib import Path

from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / "docs/learning-games/runtime-inverse.json"
PIN = "abe3343bff1d0e4a1306d07b239838f6c9c59b416d7ff1fbb76fbe6eced92a4e"


def before_learning_games_bytes(path, raw):
    if str(path) != "primer/server.py":
        return raw
    return _restore(path, raw, PROOF, PIN)
