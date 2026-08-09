"""Measures the actual defect rate of quiz.cloze_from_text's auto-generated
items, independent of the generator's own internal guards — a checker that
reused cloze_from_text's own rejection logic to grade cloze_from_text would
prove nothing. Every check here is a fresh, independent read of the item.

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
