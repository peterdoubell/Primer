"""Contracts for the radiology reading foundation and reporting workbench.

The source inventory is a dated, attributed index, not a local copy of the
publisher's lessons. These checks protect coverage, clinical boundary prompts,
and the separation between a single lesson's references and shared API lists.
"""

from __future__ import annotations

import copy
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from primer import radiology  # noqa: E402
from primer.curriculum import REFERENCE_HOSTS, Curriculum, _validate_reference  # noqa: E402


def _read(name):
    return json.loads((ROOT / "data" / "radiology" / name).read_text())


@pytest.fixture(scope="module")
def curriculum():
    from primer.curriculum import Curriculum

    return Curriculum()


@pytest.fixture(scope="module")
def radiology_nodes(curriculum):
    return [node for node in curriculum.nodes.values()
            if node["domain"] == "radiology" and node["id"].startswith("rad.")]


def _keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _keys(child)


def _assert_https(url):
    parsed = urlsplit(url)
    assert parsed.scheme == "https" and parsed.hostname
    assert not parsed.username and not parsed.password
    assert not any(character.isspace() for character in url)
    assert parsed.port is None or 0 < parsed.port <= 65535


def test_source_inventory_accounts_for_the_reviewed_navigation():
    catalog = _read("source-catalog.json")
    date.fromisoformat(catalog["reviewed_at"])
    articles = catalog["articles"]
    # The September 2026 capture has 188 distinct medical articles and 196
    # navigation URLs; the 25 September recheck added "Thoracic Aorta - How to
    # Measure". Future additions may grow that foundation; silently shrinking
    # both the inventory and its metadata must not pass this guard.
    assert len(articles) >= 189
    assert catalog["unique_articles"] == len(articles)
    assert len({article["id"] for article in articles}) == len(articles)
    canonical_urls = {article["url"] for article in articles}
    assert len(canonical_urls) == len(articles)
    navigation_urls = []
    for article in articles:
        assert article["title"].strip() and article["section"].strip()
        assert article["topic"].strip() and article["module_id"].strip()
        for entry in [article, *article.get("aliases", [])]:
            _assert_https(entry["url"])
            assert urlsplit(entry["url"]).hostname == "radiologyassistant.nl"
            navigation_urls.append(entry["url"])
        assert isinstance(article["headings"], list)
        assert all(isinstance(heading, str) and heading.strip()
                   for heading in article["headings"])
        if not article["headings"]:
            assert article.get("content_type") == "video"
            assert article.get("outline_note")
    assert len(navigation_urls) == len(set(navigation_urls))
    assert len(navigation_urls) == catalog["navigation_article_urls"]
    assert len(navigation_urls) >= 197
    assert {"Abdomen", "Breast", "Cardiovascular", "Chest", "Head/Neck",
            "Musculoskeletal", "Neuroradiology", "Pediatrics", "More"} <= {
                article["section"] for article in articles}
    for excluded in catalog["excluded_navigation_links"]:
        _assert_https(excluded["url"])
        assert excluded["reason"].strip()
        assert excluded["url"] not in navigation_urls


def test_every_source_is_mapped_once_to_a_real_module(radiology_nodes):
    catalog = _read("source-catalog.json")
    by_id = {node["id"]: node for node in radiology_nodes}
    mapped = [source for node in radiology_nodes
              for source in node["radiology_reference"]["reading"]]
    assert {source["module_id"] for source in catalog["articles"]} <= set(by_id)
    assert {source["url"] for source in mapped} == {
        source["url"] for source in catalog["articles"]}
    assert len(mapped) == len(catalog["articles"])
    for node in radiology_nodes:
        reference = node["radiology_reference"]
        assert all(source["module_id"] == node["id"]
                   for source in reference["reading"])
        assert reference["supplementary"] == (not reference["reading"])


def test_every_module_has_a_complete_original_report_and_image_plan(radiology_nodes):
    template_ids, image_ids = [], []
    for node in radiology_nodes:
        reference = node["radiology_reference"]
        radiology.validate_reference(reference)
        assert len(reference["learning_points"]) >= 2, node["id"]
        assert reference["report_templates"], node["id"]
        assert reference["key_images"], node["id"]
        assert node["reference_count"] == len(reference["reading"])
        assert node["template_count"] == len(reference["report_templates"])
        for template in reference["report_templates"]:
            template_ids.append(template["id"])
            assert template["description"].strip()
            assert len(template["sections"]) >= 4
            headings = [section["heading"].casefold()
                        for section in template["sections"]]
            assert len(headings) == len(set(headings))
            assert any("impression" in heading for heading in headings)
            assert any("quality" in heading for heading in headings)
            assert any("key images" in heading for heading in headings)
            assert "[" in "\n".join(section["body"]
                                      for section in template["sections"])
            if reference["reading"]:
                assert template["sources"], node["id"]
            for source in template.get("sources", []):
                _assert_https(source["url"])
        for image in reference["key_images"]:
            image_ids.append(image["id"])
            assert image["src"], image["id"]
            radiology.validate_image_source(image["src"])
            assert image["image_type"] in ("clinical", "diagram", "table")
            assert image["caption"].strip() and image["alt"].strip()
            assert image["attribution"].strip()
            if image.get("source_url"):
                if image["source_url"].startswith("/app/illustrations/"):
                    radiology.validate_image_source(image["source_url"])
                else:
                    _assert_https(image["source_url"])
        # Learning content can teach the same concept as an assessment, but
        # the private question records and their answer-key fields stay out.
        assert not {"quiz", "answer", "explain", "keywords", "correct"} & set(_keys(reference))
    assert len(template_ids) == len(set(template_ids))
    assert len(image_ids) == len(set(image_ids))


def test_source_titles_topics_and_outlines_remain_searchable(radiology_nodes):
    for node in radiology_nodes:
        topics = node["reference_topics"]
        assert isinstance(topics, list) and len(topics) == len(set(topics))
        assert all(isinstance(topic, str) and topic.strip() for topic in topics)
        for source in node["radiology_reference"]["reading"]:
            assert source["title"] in topics
            assert source["topic"] in topics
            assert set(source["headings"]) <= set(topics)
    # These source terms are not all module titles; the Atlas must retain the
    # index words that let a reader find a topic within a broader module.
    indexed = " ".join(term for node in radiology_nodes
                       for term in node["reference_topics"]).casefold()
    for term in ("cad-rads", "pi-rads", "appendicitis", "tinnitus"):
        assert term in indexed


def _valid_reference():
    return {
        "overview": "An original reference worksheet.",
        "reviewed_at": "2026-09-23",
        "reading": [{"title": "Source", "url": "https://radiologyassistant.nl/",
                     "headings": ["Anatomy"]}],
        "learning_points": ["Correlate the relevant sequences."],
        "report_templates": [{"id": "example", "title": "Example report",
                              "sections": [{"heading": "FINDINGS", "body": "[ ]"}],
                              "sources": [{"title": "Guidance", "url": "https://www.acr.org/"}]}],
        "key_images": [{"id": "image-1", "label": "Anatomy",
                        "description": "Placeholder for the anatomical view.",
                        "source_url": "https://radiologyassistant.nl/"}],
    }


INVALID_SOURCE_URLS = (
    "", "javascript:alert(1)", "data:text/html,example", "http://example.org/",
    "//example.org/article", "https:///missing-host", "https://user:secret@example.org/",
    "https://bad host.example/", "https://example.org:not-a-port/",
)


@pytest.mark.parametrize("location,url", [
    (location, url)
    for location in ("reading", "template", "image")
    for url in INVALID_SOURCE_URLS
    if url or location != "image"
])
def test_invalid_external_urls_are_rejected_before_rendering(url, location):
    reference = _valid_reference()
    if location == "reading":
        reference["reading"][0]["url"] = url
    elif location == "template":
        reference["report_templates"][0]["sources"][0]["url"] = url
    else:
        reference["key_images"][0]["source_url"] = url
    with pytest.raises(ValueError):
        radiology.validate_reference(reference)


def test_original_image_placeholders_can_omit_an_external_source():
    reference = _valid_reference()
    reference["key_images"][0].pop("source_url")
    radiology.validate_reference(reference)


@pytest.mark.parametrize("field,value", [
    ("overview", ""), ("reviewed_at", None), ("reading", {}),
    ("learning_points", [""]), ("report_templates", None), ("key_images", "images"),
])
def test_malformed_reference_fields_fail_at_load_time(field, value):
    reference = _valid_reference()
    reference[field] = value
    with pytest.raises(ValueError):
        radiology.validate_reference(reference)


@pytest.mark.parametrize("collection", ["report_templates", "key_images"])
def test_duplicate_workbench_identifiers_are_rejected(collection):
    reference = _valid_reference()
    reference[collection].append(copy.deepcopy(reference[collection][0]))
    with pytest.raises(ValueError):
        radiology.validate_reference(reference)


@pytest.mark.parametrize("field", ["heading", "body"])
def test_empty_report_sections_are_rejected(field):
    reference = _valid_reference()
    reference["report_templates"][0]["sections"][0][field] = "  "
    with pytest.raises(ValueError):
        radiology.validate_reference(reference)


@pytest.mark.parametrize("defect", ["unknown-module", "duplicate-source", "missing-guide"])
def test_broken_source_mapping_cannot_silently_reduce_coverage(monkeypatch, defect):
    data = {name: _read(name) for name in (
        "source-catalog.json", "module-guides.json", "flagship-templates.json")}
    nodes = [node for node in json.loads((ROOT / "data/curriculum/11-radiology.json").read_text())["nodes"]
             if node["id"].startswith("rad.")]
    if defect == "unknown-module":
        data["source-catalog.json"]["articles"][0]["module_id"] = "rad.nonexistent"
    elif defect == "duplicate-source":
        data["source-catalog.json"]["articles"].append(
            copy.deepcopy(data["source-catalog.json"]["articles"][0]))
    else:
        identifier = next(node["id"] for node in nodes
                          if node["id"] not in data["flagship-templates.json"])
        data["module-guides.json"].pop(identifier)
    real_read = radiology._read
    monkeypatch.setattr(radiology, "_read", lambda name: (
        copy.deepcopy(data[name]) if name in data else real_read(name)))
    with pytest.raises(ValueError):
        radiology.attach_references(nodes)


def test_api_sends_reports_only_for_opened_lesson_and_never_sends_quiz_keys(
        curriculum, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from primer.learner import LearnerStore
    import primer.server as server

    store = LearnerStore(str(tmp_path / "reference-api.db"))
    store.save_profile("Reference QA", 40, 3, "balanced", 5, ["radiology"])
    monkeypatch.setattr(server, "learner", store)
    monkeypatch.setattr(server, "curr", curriculum)
    monkeypatch.setattr(server.wiki, "get_summary", lambda *args, **kwargs: None)
    node = curriculum.node("rad.5.coronary-ct")
    sentinel = "PRIVATE-QUIZ-ANSWER-REFERENCE-REGRESSION"
    monkeypatch.setitem(node, "quiz", [{"prompt": "Private prompt", "answer": sentinel,
                                       "explain": sentinel, "keywords": [sentinel]}])
    # Ensure Today exercises a radiology node even when the normal adaptive
    # selector would choose a different frontier lesson for a fresh reader.
    monkeypatch.setattr(curriculum, "next_lessons", lambda *args, **kwargs: [node])
    client = TestClient(server.app)
    try:
        detail_response = client.get("/api/curriculum/node/" + node["id"])
        graph_response = client.get("/api/curriculum")
        today_response = client.get("/api/today")
        assert detail_response.status_code == graph_response.status_code == today_response.status_code == 200
        detail = detail_response.json()
        graph = graph_response.json()
        today = today_response.json()
        assert detail["radiology_reference"] == node["radiology_reference"]
        assert detail["question_count"] == 1
        graph_node = next(item for item in graph["nodes"] if item["id"] == node["id"])
        today_node = next(item for item in today["lessons"] if item["id"] == node["id"])
        for lightweight in (graph_node, today_node):
            assert not {"radiology_reference", "report_templates", "key_images", "lesson_media"} & set(_keys(lightweight))
            for field in ("reference_topics", "reference_count", "template_count"):
                assert lightweight[field] == node[field]
        for response in (detail_response, graph_response, today_response):
            assert sentinel not in response.text
        for public in (detail, graph_node, today_node):
            assert not {"quiz", "answer", "explain", "keywords"} & set(_keys(public))
        # Projection of the index must not remove the full data from the
        # in-memory curriculum or a subsequent lesson response.
        assert client.get("/api/curriculum/node/" + node["id"]).json()["radiology_reference"] == detail["radiology_reference"]
    finally:
        client.close()


def _normalise(text):
    return text.replace("\u2013", "-").replace("\u2212", "-").replace("\u2265", ">=").replace("\u2264", "<=")


def _flagship_sections(identifier):
    template = _read("flagship-templates.json")[identifier]["report_templates"][0]
    return {section["heading"]: _normalise(section["body"])
            for section in template["sections"]}


def test_ccta_preserves_cad_rads_boundaries_and_non_diagnostic_rules():
    sections = _flagship_sections("rad.5.coronary-ct")
    classification = sections["CAD-RADS 2.0"]
    for category, boundary in (("1", "1-24%"), ("2", "25-49%"),
                               ("3", "50-69%"), ("4A", "70-99%")):
        assert re.search(r"^" + category + r":.*" + re.escape(boundary), classification, re.M)
    assert re.search(r"4B:.*LM\s*>=50%.*(three|3)[ -]vessel", classification, re.I)
    assert re.search(r"5:.*(occlu|100%)", classification, re.I)
    assert all(boundary in classification for boundary in (">1.5 mm", "<50%", ">=50%"))
    assert re.search(r"category N", classification, re.I)
    assert re.search(r"append N", classification, re.I)
    burden = sections["PLAQUE BURDEN"]
    for category, calcium, sis in (("P1", "1-100", "1-2"),
                                   ("P2", "101-300", "3-4"),
                                   ("P3", "301-999", "5-7"),
                                   ("P4", ">=1000", ">=8")):
        line = next(line for line in burden.splitlines() if line.startswith(category + " "))
        assert "CAC " + calcium in line and "SIS " + sis in line
    assert re.search(r"CAD-RADS 0.*no P", burden, re.I)
    assert re.search(r"zero plaque.*not P1", burden, re.I)
    assert re.search(r"(two|2).*HRP features.*plaque", sections["PLAQUE"], re.I)


def test_ccta_physiology_and_management_need_clinical_context():
    sections = _flagship_sections("rad.5.coronary-ct")
    physiology = sections["CT-FFR / CT PERFUSION"]
    for boundary in ("I+ <=0.75", "I- >0.80", "I\u00b1 0.76-0.80"):
        assert boundary in physiology
    assert "1-2 cm distal" in physiology
    assert re.search(r"lowest distal value.*(not|never).*referral", physiology, re.I)
    management = sections["OPTIONAL MANAGEMENT LINE"]
    assert "ECG" in management and "troponin" in management
    assert re.search(r"(do not|cannot|must not).*diagnos.*exclud.*ACS.*CAD-RADS alone", management, re.I)


def test_prostate_report_covers_zonal_scoring_mapping_and_staging():
    sections = _flagship_sections("rad.5.prostate-mri")
    text = "\n".join(sections.values())
    for concept in ("PSA density", "Volume", "sector", "DWI", "ADC", "DCE",
                    "Extraprostatic", "seminal vesicles", "series/image"):
        assert concept.casefold() in text.casefold()
    scoring = sections["SCORING CHECK"]
    assert re.search(r"PZ:.*DWI 3.*PI-RADS 4.*positive DCE", scoring)
    assert re.search(r"TZ:.*T2 2.*DWI >=4.*PI-RADS 3.*T2 3.*DWI 5.*PI-RADS 4", scoring)
    assert re.search(r"DCE does not upgrade TZ", scoring)
    assert ">=1.5 cm" in scoring


# Specialist framework contracts retained alongside the reading/reporting workbench.
@pytest.fixture(scope="module")
def authored_radiology_nodes():
    return json.loads((ROOT / "data/curriculum/11-radiology.json").read_text())["nodes"]


@pytest.fixture(scope="module")
def referenced(authored_radiology_nodes):
    return [n for n in authored_radiology_nodes if n.get("reference")]


def test_the_specialist_field_carries_reporting_frameworks(referenced, authored_radiology_nodes):
    """The point of the field. If this collapses, the reference tool is gone
    and nobody noticed, because nothing else in the suite reads the block."""
    assert len(referenced) >= 40, \
        "only %d of %d radiology modules carry a framework" % (
            len(referenced), len(authored_radiology_nodes))


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
