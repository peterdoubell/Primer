"""Regression boundaries for the natural-science visual-quality pass."""

from __future__ import annotations

import math
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def _natural_science_modules():
    sys.path.insert(0, str(TOOLS))
    try:
        from natural_science_illustrations import biology, chemistry, core, earth_space
    finally:
        sys.path.pop(0)
    return biology, chemistry, earth_space, core


def test_every_generated_biology_plate_has_a_lesson_specific_renderer():
    """Biology may not fall back to the interchangeable generic icon layouts."""
    biology, _chemistry, _earth_space, core = _natural_science_modules()

    assert len(biology.SPECS) == 32
    assert set(biology.SPECS) == set(biology.BIOLOGY_RENDERERS)
    assert set(biology.SPECS).issubset(core.NODE_RENDERERS)
    assert len({id(renderer) for renderer in biology.BIOLOGY_RENDERERS.values()}) == 32


def test_every_generated_natural_science_plate_is_lesson_specific():
    """All generator-owned science lessons must meet the mathematics visual bar."""
    biology, chemistry, earth_space, core = _natural_science_modules()
    cohorts = (
        (biology.SPECS, biology.BIOLOGY_RENDERERS, 32),
        (chemistry.SPECS, chemistry.CHEMISTRY_RENDERERS, 28),
        (earth_space.SPECS, earth_space.EARTH_SPACE_RENDERERS, 25),
    )
    expected_ids = set()
    renderers = []
    for specs, cohort_renderers, expected_count in cohorts:
        assert len(specs) == expected_count
        assert set(specs) == set(cohort_renderers)
        expected_ids.update(specs)
        renderers.extend(cohort_renderers.values())

    assert set(core.NODE_RENDERERS) == expected_ids
    assert len(expected_ids) == 85
    assert len({id(renderer) for renderer in renderers}) == 85


def test_scientific_symbols_keep_the_sans_serif_plate_voice():
    """One subscript must not turn a complete prose label into serif maths."""
    _biology, _chemistry, _earth_space, core = _natural_science_modules()

    face = core._science_font("O₂ returns · Na⁺ enters", 30, bold=True)
    assert "stix" not in os.path.basename(face.path).lower()


def test_corrected_early_biology_captions_fit_their_reserved_boxes(monkeypatch):
    """Measure actual font ink, not just the nominal caption rectangle."""
    biology, _chemistry, _earth_space, core = _natural_science_modules()
    from natural_science_illustrations import biology_early_detail as detail

    original = detail._wrapped_center
    checked = []

    def measured(plate, box, value, **kwargs):
        draw_text = plate.draw.text

        def capture(xy, text, **options):
            bounds = plate.draw.textbbox(
                xy, text, font=options['font'], anchor=options.get('anchor'),
                stroke_width=options.get('stroke_width', 0))
            assert bounds[0] >= box[0] and bounds[1] >= box[1], (value, box, bounds)
            assert bounds[2] <= box[2] and bounds[3] <= box[3], (value, box, bounds)
            checked.append(text)
            return draw_text(xy, text, **options)

        plate.draw.text = capture
        try:
            return original(plate, box, value, **kwargs)
        finally:
            plate.draw.text = draw_text

    monkeypatch.setattr(detail, '_wrapped_center', measured)
    for node_id in ('bio.0.body', 'bio.0.seasons', 'bio.1.human-body',
                    'bio.1.habitats', 'bio.1.health', 'bio.2.digestion'):
        spec = biology.SPECS[node_id]
        plate = core.SciencePlate(node_id, spec['title'], spec['stage'], 'biology')
        biology.BIOLOGY_RENDERERS[node_id](plate, spec['content'])
    assert len(checked) >= 20


def test_introductory_plant_roots_do_not_enter_caption_band(monkeypatch):
    biology, _chemistry, _earth_space, core = _natural_science_modules()
    from natural_science_illustrations import biology_early_detail as detail

    roots = []
    captions = []
    original_roots, original_body = detail._roots, detail._body_text

    def root(plate, origin, **kwargs):
        roots.append(origin[1] + kwargs.get('depth', 115))
        return original_roots(plate, origin, **kwargs)

    def body(plate, box, value, **kwargs):
        captions.append(box[1])
        return original_body(plate, box, value, **kwargs)

    monkeypatch.setattr(detail, '_roots', root)
    monkeypatch.setattr(detail, '_body_text', body)
    for node_id in ('bio.0.living', 'bio.0.plants'):
        roots.clear()
        captions.clear()
        spec = biology.SPECS[node_id]
        plate = core.SciencePlate(node_id, spec['title'], spec['stage'], 'biology')
        biology.BIOLOGY_RENDERERS[node_id](plate, spec['content'])
        assert roots and captions
        assert max(roots) + 10 <= min(captions)


def test_food_chain_species_labels_do_not_overlap(monkeypatch):
    biology, _chemistry, _earth_space, core = _natural_science_modules()
    spec = biology.SPECS['bio.1.food-chains']
    plate = core.SciencePlate('bio.1.food-chains', spec['title'], spec['stage'], 'biology')
    original = plate.label
    boxes = []

    def label(xy, value, **kwargs):
        if value in ('GRASS / PRODUCER', 'RABBIT / CONSUMER', 'FOX / PREDATOR'):
            face = core._science_font(value, kwargs.get('size', 28), bold=True)
            bounds = plate.draw.textbbox(xy, value, font=face, anchor='mm')
            boxes.append((bounds[0] - 15, bounds[2] + 15))
        return original(xy, value, **kwargs)

    monkeypatch.setattr(plate, 'label', label)
    biology.BIOLOGY_RENDERERS['bio.1.food-chains'](plate, spec['content'])
    assert len(boxes) == 3
    assert all(left[1] + 10 <= right[0] for left, right in zip(boxes, boxes[1:]))


def test_repaired_biology_labels_stay_inside_their_panels(monkeypatch):
    biology, _chemistry, _earth_space, core = _natural_science_modules()
    selected = {
        'bio.2.classification': {'OTHER ARCHAEA': (105, 225, 1495, 785)},
        'bio.3.microbiology': {
            'lymphocyte clone expands': (750, 665, 1150, 715),
            'memory persists': (1185, 655, 1420, 700),
        },
        'bio.3.botany': {'water + ions': (175, 710, 400, 760)},
    }
    for node_id, labels in selected.items():
        spec = biology.SPECS[node_id]
        plate = core.SciencePlate(node_id, spec['title'], spec['stage'], 'biology')
        original = plate.text
        seen = set()

        def text(xy, value, **kwargs):
            if value in labels:
                box = labels[value]
                face = core._science_font(value, kwargs.get('size', 36),
                                          bold=kwargs.get('bold', False))
                bounds = plate.draw.textbbox(xy, value, font=face,
                                             anchor=kwargs.get('anchor', 'la'))
                assert box[0] <= bounds[0] <= bounds[2] <= box[2], (value, bounds)
                assert box[1] <= bounds[1] <= bounds[3] <= box[3], (value, bounds)
                seen.add(value)
            return original(xy, value, **kwargs)

        monkeypatch.setattr(plate, 'text', text)
        biology.BIOLOGY_RENDERERS[node_id](plate, spec['content'])
        assert seen == set(labels)


def test_evolution_plate_counts_are_phenotypes_not_diploid_allele_counts(monkeypatch):
    biology, _chemistry, _earth_space, core = _natural_science_modules()
    from natural_science_illustrations import biology_advanced_detail as detail
    populations = [[], []]
    original = detail._beetle

    def beetle(plate, center, **kwargs):
        if kwargs.get('size') == 64:
            populations[0 if center[0] < 600 else 1].append(kwargs['marked'])
        return original(plate, center, **kwargs)

    monkeypatch.setattr(detail, '_beetle', beetle)
    spec = biology.SPECS['bio.3.evolution']
    plate = core.SciencePlate('bio.3.evolution', spec['title'], spec['stage'], 'biology')
    biology.BIOLOGY_RENDERERS['bio.3.evolution'](plate, spec['content'])
    assert [(sum(pop), len(pop)) for pop in populations] == [(4, 12), (9, 12)]
    assert 'not measured allele frequencies' in spec['caption']


def test_generated_science_labels_do_not_render_missing_glyph_boxes(monkeypatch):
    """Inspect the actual fonts used for every drawn label, not source strings."""
    biology, chemistry, earth, core = _natural_science_modules()
    checked = set()
    missing = set()
    for domain, module in (('biology', biology), ('chemistry', chemistry),
                            ('earth-space', earth)):
        for node_id, spec in module.SPECS.items():
            plate = core.SciencePlate(node_id, spec['title'], spec['stage'], domain)
            original = plate.draw.text

            def text(xy, value, *args, **kwargs):
                face = kwargs.get('font', args[1] if len(args) > 1 else None)
                if face is not None:
                    fallback = bytes(face.getmask('\U0010ffff'))
                    for char in str(value):
                        key = (face.path, face.size, char)
                        if char.isspace() or key in checked:
                            continue
                        checked.add(key)
                        if bytes(face.getmask(char)) == fallback:
                            missing.add((node_id, char, face.path))
                return original(xy, value, *args, **kwargs)

            monkeypatch.setattr(plate.draw, 'text', text)
            core.NODE_RENDERERS[node_id](plate, spec['content'])
    assert len(checked) > 100
    assert not missing, sorted(missing)


def test_domain_contact_sheets_review_authored_and_generated_plates(tmp_path):
    """Every science QA sheet includes authored and generator-owned lessons."""
    for domain, lesson_count in (("biology", 37), ("chemistry", 29),
                                 ("earth-space", 27)):
        destination = tmp_path / (domain + ".webp")
        result = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "generate_natural_science_illustrations.py"),
                "--contact-sheet",
                str(destination),
                "--contact-sheet-domain",
                domain,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert destination.is_file()
        with Image.open(destination) as sheet:
            assert sheet.size == (5 * 320,
                                  math.ceil(lesson_count / 5) * (200 + 38))
