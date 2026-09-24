"""Source-linked radiology teaching and reporting references.

Article metadata is a dated reading map, not a licensed local reproduction of
Radiology Assistant. Original reporting worksheets remain usable offline.
"""

import copy
import json
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit


DATA = Path(__file__).resolve().parents[1] / "data" / "radiology"
IMAGE_CATALOGS = ("key-images-flagship.json", "key-images-foundations-body.json",
                  "key-images-neuro-msk.json")
REMOTE_IMAGE_PATHS = {
    "radiologyassistant.nl": ("/assets/", "/img/"),
    "upload.wikimedia.org": ("/wikipedia/commons/",),
}
REPORTING_CATALOGS = ("reporting-body.json", "reporting-neuro-msk.json")


def validate_reporting_guide(guide):
    """Professional reference copy is data, never an executable rule engine."""
    if not isinstance(guide, dict):
        raise ValueError("Reporting guide must be an object")
    date.fromisoformat(guide.get("reviewed_at", ""))
    for key in ("protocol", "pitfalls", "impression_prompts", "escalation"):
        values = guide.get(key)
        if not isinstance(values, list) or (key != "escalation" and not values):
            raise ValueError("Reporting guide needs " + key)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("Reporting guide contains an empty " + key)
    for key, fields in (("checklist", ("label", "detail")),
                        ("measurements", ("name", "method", "pitfall")),
                        ("template_sections", ("heading", "body"))):
        rows = guide.get(key)
        if not isinstance(rows, list) or (key != "measurements" and not rows):
            raise ValueError("Reporting guide needs " + key)
        for row in rows:
            if not isinstance(row, dict) or any(not isinstance(row.get(field), str)
                    or not row[field].strip() for field in fields):
                raise ValueError("Invalid reporting guide " + key)
    headings = [row["heading"].casefold() for row in guide["template_sections"]]
    if len(headings) != len(set(headings)):
        raise ValueError("Reporting finding headings must be unique")
    classification = guide.get("classification")
    if classification is not None:
        if not isinstance(classification, dict) or any(
                not isinstance(classification.get(key), str) or not classification[key].strip()
                for key in ("name", "version", "applicability", "summary")):
            raise ValueError("Reporting classification needs its version and scope")
    if not isinstance(guide.get("sources"), list) or not guide["sources"]:
        raise ValueError("Reporting guide needs sources")
    for source in guide["sources"]:
        _source(source)


def _reporting_catalog(nodes):
    references = {}
    for name in REPORTING_CATALOGS:
        entries = _read(name)
        if set(entries) & set(references):
            raise ValueError("Duplicate reporting guide assignment")
        references.update(entries)
    models = _read("reporting-models.json")
    tables = _read("classification-tables.json")
    identifiers = {node["id"] for node in nodes}
    if set(references) != identifiers or set(models) != identifiers:
        raise ValueError("Every radiology module needs a reporting guide and 3D companion")
    if not set(tables).issubset(identifiers):
        raise ValueError("Classification table references an unknown module")
    for identifier, table in tables.items():
        if not table.get("title") or not table.get("scope") or not table.get("rows"):
            raise ValueError("Classification table needs a title, scope and criteria")
        for row in table["rows"]:
            if any(not isinstance(row.get(key), str) or not row[key].strip()
                   for key in ("category", "criteria", "report_note")):
                raise ValueError("Classification table contains an incomplete row")
        for source in table["sources"]:
            _source(source)
        references[identifier]["criteria_table"] = table
    for identifier in identifiers:
        validate_reporting_guide(references[identifier])
        model = models[identifier]
        if model.get("scenario") != "radiology-reference:" + identifier or any(
                not isinstance(model.get(key), str) or not model[key].strip()
                for key in ("id", "title", "instructions", "family")):
            raise ValueError("Invalid reporting 3D companion")
    return references, models


def validate_image_source(url):
    """Keep image loading confined to the curated publishers and local plates."""
    if not isinstance(url, str) or not url:
        raise ValueError("Radiology image needs a source")
    local_prefix = "/app/illustrations/"
    if url.startswith(local_prefix):
        relative = url[len(local_prefix):]
        if any(part in (".", "..", "") for part in relative.split("/")) or "%" in relative:
            raise ValueError("Invalid local radiology image")
        root = DATA.parents[1] / "web" / "illustrations"
        path = (root / relative).resolve()
        if root.resolve() not in path.parents or path.suffix != ".webp" or not path.is_file():
            raise ValueError("Unknown local radiology image")
        return
    _source({"title": "Image", "url": url})
    parsed = urlsplit(url)
    prefixes = REMOTE_IMAGE_PATHS.get(parsed.hostname, ())
    path = unquote(parsed.path)
    if (not any(path.startswith(prefix) for prefix in prefixes)
            or ".." in path.split("/") or "\\" in path
            or parsed.fragment
            or Path(path).suffix.lower() not in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
        raise ValueError("Radiology image must use an approved publisher asset path")


def _read(name):
    with (DATA / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def _source(source):
    if not isinstance(source, dict) or not source.get("title"):
        raise ValueError("Radiology source needs a title")
    url = source.get("url", "")
    if not isinstance(url, str) or any(char.isspace() or ord(char) < 32 for char in url):
        raise ValueError("Radiology sources must use public HTTPS URLs")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise ValueError("Radiology sources must use public HTTPS URLs") from error
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or port not in (None, 443)):
        raise ValueError("Radiology sources must use public HTTPS URLs")


def validate_reference(reference):
    """Reject broken authored references at startup, before they reach the UI."""
    for key in ("overview", "reviewed_at"):
        if not isinstance(reference.get(key), str) or not reference[key].strip():
            raise ValueError("Radiology reference needs " + key)
    for key in ("reading", "learning_points", "report_templates", "key_images"):
        if not isinstance(reference.get(key), list):
            raise ValueError("Radiology reference needs a list: " + key)
    for point in reference["learning_points"]:
        if not isinstance(point, str) or not point.strip():
            raise ValueError("Empty radiology learning point")
    for source in reference["reading"]:
        _source(source)
        if not isinstance(source.get("headings", []), list):
            raise ValueError("Radiology source headings must be a list")
    identifiers = set()
    for template in reference["report_templates"]:
        if not template.get("id") or template["id"] in identifiers:
            raise ValueError("Radiology template IDs must be unique")
        identifiers.add(template["id"])
        if not template.get("title") or not template.get("sections"):
            raise ValueError("Radiology template needs a title and sections")
        for section in template["sections"]:
            if any(not isinstance(section.get(key), str) or not section[key].strip()
                   for key in ("heading", "body")):
                raise ValueError("Radiology template section needs heading and body")
        for source in template.get("sources", []):
            _source(source)
    image_ids = set()
    for image in reference["key_images"]:
        if not image.get("id") or image["id"] in image_ids:
            raise ValueError("Radiology key image IDs must be unique")
        image_ids.add(image["id"])
        if not image.get("label") or not image.get("description"):
            raise ValueError("Radiology image placeholder needs label and description")
        if image.get("source_url"):
            if image["source_url"].startswith("/app/illustrations/"):
                validate_image_source(image["source_url"])
            else:
                _source({"title": image["label"], "url": image["source_url"]})
        if image.get("src"):
            validate_image_source(image["src"])
            if image.get("image_type") not in ("clinical", "diagram", "table"):
                raise ValueError("Radiology image needs its teaching type")
            for key in ("alt", "caption", "attribution", "source_url"):
                if not isinstance(image.get(key), str) or not image[key].strip():
                    raise ValueError("Radiology image needs " + key)
            if image.get("license_url"):
                _source({"title": "License", "url": image["license_url"]})
            for key in ("width", "height"):
                if key in image and (isinstance(image[key], bool)
                                     or not isinstance(image[key], int) or image[key] <= 0):
                    raise ValueError("Radiology image dimensions must be positive integers")


def attach_references(nodes):
    """Attach large detail payloads and small search metadata to radiology nodes."""
    # Introductory imaging literacy follows its own age-appropriate pathway.
    # Only the clinical reference modules belong in the reporting workbench.
    nodes = [node for node in nodes if not node["id"].startswith("img.")]
    catalog = _read("source-catalog.json")
    guides = _read("module-guides.json")
    guides.update(_read("flagship-templates.json"))
    image_catalog = {}
    for filename in IMAGE_CATALOGS:
        entries = _read(filename)
        if set(entries) & set(image_catalog):
            raise ValueError("Duplicate key image assignment across catalogs")
        image_catalog.update(entries)
    slot_ids = {image["id"] for guide in guides.values() for image in guide["key_images"]}
    if set(image_catalog) != slot_ids:
        raise ValueError("Radiology key image catalog must cover every report slot exactly once")
    known = {node["id"] for node in nodes}
    reporting, models = _reporting_catalog(nodes)
    readings = {identifier: [] for identifier in known}
    supplementary = {identifier: [] for identifier in known}
    for source in _read("supplemental-sources.json"):
        _source(source)
        if source["module_id"] not in known:
            raise ValueError("Supplemental source maps to an unknown module")
        supplementary[source["module_id"]].append(copy.deepcopy(source))
    urls = set()
    for article in catalog["articles"]:
        _source(article)
        if article["url"] in urls:
            raise ValueError("Duplicate Radiology Assistant source: " + article["url"])
        urls.add(article["url"])
        if article["module_id"] not in known:
            raise ValueError("Radiology source maps to an unknown module: " + article["module_id"])
        readings[article["module_id"]].append(copy.deepcopy(article))
    for node in nodes:
        if node["id"] not in guides:
            raise ValueError("Missing radiology guide: " + node["id"])
        reference = copy.deepcopy(guides[node["id"]])
        reference["reviewed_at"] = catalog["reviewed_at"]
        reference["reading"] = readings[node["id"]]
        reference["supplementary"] = not reference["reading"]
        reference["additional_sources"] = supplementary[node["id"]]
        reference["reporting"] = copy.deepcopy(reporting[node["id"]])
        reference["spatial_model"] = copy.deepcopy(models[node["id"]])
        brief = reference["reporting"]
        reference["overview"] = node["goal"]
        if node["id"] not in {"rad.5.coronary-ct", "rad.5.prostate-mri"}:
            for template in reference["report_templates"]:
                sections = template["sections"]
                sections[4:-2] = copy.deepcopy(brief["template_sections"])
                sections[-2]["body"] = "\n".join(
                    "{}. [{}]".format(index, prompt)
                    for index, prompt in enumerate(brief["impression_prompts"], 1))
                sections[2]["body"] = "\n".join(brief["protocol"]) + "\n\n" + sections[2]["body"]
                template["description"] = "Exam-specific reporting fields. Complete observations and remove unused alternatives."
                template["notes"] = list(dict.fromkeys(template.get("notes", []) + brief["pitfalls"]))
        for template in reference["report_templates"]:
            if not template.get("sources"):
                template["sources"] = [
                    {"title": source["title"], "url": source["url"]}
                    for source in reference["reading"]
                ] + [{"title": source["title"], "url": source["url"]}
                     for source in supplementary[node["id"]]]
            present = {source["url"] for source in template["sources"]}
            for source in brief["sources"]:
                if source["url"] not in present:
                    template["sources"].append(copy.deepcopy(source))
                    present.add(source["url"])
        for placeholder in reference["key_images"]:
            # Keep the blank report prompt alongside the independent teaching
            # example. Loading a figure never fills in a patient's findings.
            asset = image_catalog[placeholder["id"]]
            if not asset.get("src"):
                raise ValueError("Every radiology key image needs a displayable source")
            if {"id", "label", "description"} & set(asset):
                raise ValueError("Image assets must not overwrite report slot identity")
            placeholder.update(copy.deepcopy(asset))
            if reference["reading"] and not placeholder.get("source_url"):
                placeholder["source_url"] = reference["reading"][0]["url"]
        validate_reference(reference)
        node["radiology_reference"] = reference
        node["reference_count"] = len(reference["reading"])
        node["template_count"] = len(reference["report_templates"])
        node["reference_topics"] = list(dict.fromkeys(
            value for article in reference["reading"]
            for value in [article["title"], article.get("topic", ""), *article.get("headings", [])]
            if value
        ))
        node["reference_topics"] = list(dict.fromkeys(node["reference_topics"] +
            [item["label"] for item in brief["checklist"]] +
            ([brief["classification"]["name"]] if brief["classification"] else [])))
