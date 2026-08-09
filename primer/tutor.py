"""'Ask the Book' — the Primer's voice.

In Diamond Age the Primer spoke through ractors; here it speaks through an
LLM when an ANTHROPIC_API_KEY is available, and through a rule-based Socratic
engine when offline. Either way the tutor grounds itself in the article being
read and matches its register to the reader's stage.
"""

import json
import os
import random
import re
import urllib.request
from typing import Dict, List

from .learner import STAGE_NAMES

R = random.Random()

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("PRIMER_TUTOR_MODEL", "claude-sonnet-5")

REGISTERS = [
    "The reader is 3-5 years old. Use very short sentences, warm playful tone, "
    "concrete words, and one idea at a time. Ask one tiny question at the end.",
    "The reader is 6-9 years old. Be warm and vivid. Short paragraphs. "
    "Explain with familiar comparisons. End with one curious question.",
    "The reader is 10-13. Be friendly and clear, introduce proper terminology "
    "gently, use analogies, and end with a question that makes them reason.",
    "The reader is 14-17. Be respectful and precise. Introduce real technical "
    "vocabulary. Socratic: prefer guiding questions over answers.",
    "The reader is at undergraduate level. Be rigorous, cite the relevant "
    "concepts by name, and push them to derive results themselves.",
    "The reader is at graduate level. Be a colleague: point at primary "
    "literature, open problems, and counterexamples. Never condescend.",
]

SYSTEM_TEMPLATE = (
    "You are the voice of the Primer, an interactive book of all knowledge, "
    "inspired by the Young Lady's Illustrated Primer. You are a patient, "
    "Socratic tutor. {register}\n\n"
    "Rules: keep replies under 150 words; never just hand over an answer the "
    "reader could reach in one or two steps — guide them; if the reader is "
    "stuck twice, give the answer plainly and kindly; encourage effort, not "
    "talent. The reader is currently reading the article '{title}'. "
    "Relevant excerpt:\n\n{excerpt}"
)


def have_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def ask_llm(messages: List[Dict], title: str, excerpt: str, stage: int) -> Dict:
    system = SYSTEM_TEMPLATE.format(
        register=REGISTERS[min(max(stage, 0), 5)], title=title or "(none)",
        excerpt=(excerpt or "(none)")[:2500],
    )
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 500,
        "system": system,
        "messages": [{"role": m["role"], "content": m["content"]} for m in messages[-12:]],
    }).encode("utf-8")
    req = urllib.request.Request(
        ANTHROPIC_URL, data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = "".join(b.get("text", "") for b in data.get("content", []))
    # `remote`: this reply — and with it the reader's messages and the article
    # excerpt — went to api.anthropic.com. Machine-readable so the UI can
    # disclose it rather than the book quietly speaking through a third party.
    return {"reply": text, "engine": "claude", "remote": True}


# ---------------- rule-based fallback ----------------

def _sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text or ""))
    return [p for p in parts if 30 <= len(p) <= 240]

OPENERS = [
    "Good question. Let's think it through together.",
    "I like where your head is at.",
    "Let's puzzle this out.",
    "That's exactly the kind of thing this book is for.",
]

MOVES = [
    "Read this again slowly: “{sent}” — what do you think the most important word in that sentence is?",
    "Here's a clue from the book: “{sent}” How does that connect to your question?",
    "Before I say more — what do YOU think the answer might be? Take a guess; wrong guesses teach us the most.",
    "The book says: “{sent}” Can you say that back in your own words?",
    "Try this: if you had to explain '{title}' to a younger friend in one sentence, what would you say?",
]

STUCK_MOVES = [
    "You're working hard at this, so let me help directly: {sent}",
    "Here it is plainly: {sent} Does that part make sense now?",
]


def ask_rules(messages: List[Dict], title: str, excerpt: str, stage: int) -> Dict:
    sents = _sentences(excerpt)
    user_turns = [m for m in messages if m["role"] == "user"]
    stuck = len(user_turns) >= 3
    sent = R.choice(sents) if sents else "every big idea is made of small ideas."
    if stuck and sents:
        reply = R.choice(STUCK_MOVES).format(sent=sents[0], title=title)
    else:
        move = R.choice(MOVES).format(sent=sent, title=title or "this topic")
        reply = "{} {}".format(R.choice(OPENERS), move)
    if stage <= 1:
        reply = reply.replace("puzzle this out", "figure it out like detectives")
    # `remote: False`: nothing left this machine — the rule engine answers
    # from the local excerpt alone.
    return {"reply": reply, "engine": "book", "remote": False}


def ask(messages: List[Dict], title: str = "", excerpt: str = "", stage: int = 2) -> Dict:
    if have_api_key():
        try:
            return ask_llm(messages, title, excerpt, stage)
        except Exception:
            pass
    return ask_rules(messages, title, excerpt, stage)
