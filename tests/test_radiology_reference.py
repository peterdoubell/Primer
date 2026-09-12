"""The reporting frameworks on the specialist modules.

Radiology is a reference work, not a ladder. Its modules are opened by a
working radiologist mid-dictation, and what they open them FOR is the
`reference` block: the order to look in, what to measure, the table to land
in, the words to say, and the traps.

That block is authored medical content, so these tests guard two things the
rest of the curriculum does not need. The first is provenance — a threshold a
reader might act on has to be checkable against the page it came from, so
every block cites one, on a host we trust. The second is that the block is not
scaffolding: a heading with nothing under it reads as authority and says
nothing.
"""

import json
import os
import sys
import tempfile

import pytest

# Before anything imports primer.server: that module attaches to the live
# reader's record at import unless PRIMER_DB points elsewhere.
os.environ.setdefault("PRIMER_DB",
                      os.path.join(tempfile.gettempdir(), "primer-reference-test.db"))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer.curriculum import (  # noqa: E402
    REFERENCE_HOSTS, Curriculum, _validate_reference,
)

RADIOLOGY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "curriculum", "11-radiology.json")


@pytest.fixture(scope="module")
def radiology_nodes():
    with open(RADIOLOGY, encoding="utf-8") as fh:
        return json.load(fh)["nodes"]


@pytest.fixture(scope="module")
def referenced(radiology_nodes):
    return [n for n in radiology_nodes if n.get("reference")]


def test_the_specialist_field_carries_reporting_frameworks(referenced, radiology_nodes):
    """The point of the field. If this collapses, the reference tool is gone
    and nobody noticed, because nothing else in the suite reads the block."""
    assert len(referenced) >= 40, \
        "only %d of %d radiology modules carry a framework" % (
            len(referenced), len(radiology_nodes))


def test_every_framework_cites_a_source_we_trust(referenced):
    """A number a radiologist may act on has to be checkable. The host list is
    the whitelist; the citation is what makes the threshold auditable rather
    than merely asserted."""
    for node in referenced:
        source = node["reference"]["source"]
        assert source["url"].startswith("https://"), node["id"]
        host = source["url"][len("https://"):].split("/")[0].lower()
        host = host[4:] if host.startswith("www.") else host
        assert host in REFERENCE_HOSTS, "%s cites %s" % (node["id"], host)
        assert source["title"].strip() and source["publisher"].strip(), node["id"]


def test_no_framework_is_an_empty_shell(referenced):
    """A source and nothing else is a citation, not a framework."""
    for node in referenced:
        ref = node["reference"]
        body = set(ref) - {"source"}
        assert body, "%s cites a source and says nothing" % node["id"]


def test_every_grading_table_fills_its_columns(referenced):
    """A ragged row renders as a table with a hole in it, and the hole is the
    cell the reader most needs — usually the management column."""
    for node in referenced:
        classify = node["reference"].get("classify")
        if not classify:
            continue
        width = len(classify["columns"])
        assert width >= 2, node["id"]
        for row in classify["rows"]:
            assert len(row) == width, "%s: %r" % (node["id"], row[:2])
            assert all(str(c).strip() for c in row), "%s has a blank cell" % node["id"]


def test_the_framework_reaches_the_reader(referenced):
    """`_public_node` is subtractive — it strips `quiz` and, off the detail
    route, `lesson_media`. This asserts nothing has started stripping the one
    field the specialist reader came for."""
    import primer.server as srv

    picked = referenced[0]["id"]
    node = srv.curr.node(picked)
    public = srv._public_node(node, include_detail=True)
    assert "reference" in public, "the framework is being stripped before the client"
    assert public["reference"]["source"]["url"].startswith("https://")


def test_templates_are_dictation_ready(referenced):
    """A template is for lifting into a report. One that is a paragraph of
    prose, or that has no blanks to fill, is a description of a report rather
    than the start of one."""
    for node in referenced:
        template = node["reference"].get("template")
        if not template:
            continue
        assert "\n" in template, "%s template is a single line" % node["id"]
        assert "[" in template, "%s template has nothing to fill in" % node["id"]


# ---- the validator itself, against the shapes that would hurt a reader ----

def _ok(**over):
    ref = {"source": {"title": "T", "url": "https://radiologyassistant.nl/x",
                      "publisher": "The Radiology Assistant"},
           "pitfalls": ["Something real."]}
    ref.update(over)
    return {"id": "rad.5.test", "reference": ref}


def test_a_valid_block_passes():
    _validate_reference(_ok())


def test_a_node_without_a_reference_is_fine():
    _validate_reference({"id": "math.0.counting"})


@pytest.mark.parametrize("url,why", [
    ("http://radiologyassistant.nl/x", "plain http"),
    ("https://example.com/x", "a host nobody vetted"),
    ("https://evil.nl/radiologyassistant.nl", "a lookalike path"),
])
def test_an_untrusted_citation_is_refused(url, why):
    node = _ok()
    node["reference"]["source"]["url"] = url
    with pytest.raises(ValueError):
        _validate_reference(node)


def test_secondary_sources_are_held_to_the_same_standard():
    """A module often spans several articles. The extra citations are
    provenance, so they get the same host check as the first — otherwise
    `also` becomes the hole in the whitelist."""
    _validate_reference(_ok(also=[{"title": "Second", "publisher": "The Radiology Assistant",
                                   "url": "https://radiologyassistant.nl/y"}]))
    with pytest.raises(ValueError):
        _validate_reference(_ok(also=[{"title": "Bad", "publisher": "P",
                                       "url": "https://example.com/y"}]))
    with pytest.raises(ValueError):
        _validate_reference(_ok(also=[]))


def test_the_same_page_is_not_cited_twice():
    with pytest.raises(ValueError):
        _validate_reference(_ok(also=[{"title": "Same", "publisher": "The Radiology Assistant",
                                       "url": "https://radiologyassistant.nl/x"}]))


def test_the_index_digest_carries_the_framework_name(referenced):
    """The Atlas route cannot afford 300 KB of reference blocks, but the index
    has to be searchable by the name the reader thinks in. The digest is what
    makes "LI-RADS" find The Liver Lesion."""
    import primer.server as srv

    node = srv.curr.node("rad.4.liver")
    listed = srv._public_node(node)
    assert "reference" not in listed, "the full block is riding on the Atlas route"
    assert listed["framework"]["name"], "no framework name for the index to match"
    assert "LI-RADS" in listed["framework"]["name"]
    detail = srv._public_node(node, include_detail=True)
    assert "reference" in detail, "the detail route must still carry the block"


def test_a_ragged_grading_table_is_refused():
    with pytest.raises(ValueError):
        _validate_reference(_ok(classify={
            "name": "N", "columns": ["A", "B", "C"],
            "rows": [["1", "2", "3"], ["1", "2"]]}))


def test_a_blank_cell_is_refused():
    with pytest.raises(ValueError):
        _validate_reference(_ok(classify={
            "name": "N", "columns": ["A", "B"], "rows": [["1", "   "]]}))


def test_a_source_with_no_body_is_refused():
    node = {"id": "rad.5.test", "reference": {"source": {
        "title": "T", "url": "https://radiologyassistant.nl/x",
        "publisher": "The Radiology Assistant"}}}
    with pytest.raises(ValueError):
        _validate_reference(node)


def test_an_unknown_key_is_refused():
    with pytest.raises(ValueError):
        _validate_reference(_ok(rubbish=["x"]))


def test_an_empty_block_is_refused():
    with pytest.raises(ValueError):
        _validate_reference(_ok(approach=[]))


def test_the_whole_corpus_loads_with_its_frameworks():
    """The loader validates every block on the way in, so this is the check
    that the authored data and the schema have not drifted apart."""
    curr = Curriculum()
    rad = [n for n in curr.nodes.values() if n["domain"] == "radiology"]
    assert rad, "radiology did not load"
    assert any(n.get("reference") for n in rad)
