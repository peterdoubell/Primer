"""Regression checks for observed chemistry illustration defects."""

import sys
import math
from pathlib import Path


def modules():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
    try:
        from natural_science_illustrations import chemistry, chemistry_early_detail, core
    finally:
        sys.path.pop(0)
    return chemistry, chemistry_early_detail, core


def test_sand_grains_stay_inside_the_beaker(monkeypatch):
    _chemistry, detail, core = modules()
    plate = core.SciencePlate('chem.0.mixing', 'Mixing', 0, 'chemistry')
    original_beaker, original_polygon = detail._beaker, plate.draw.polygon
    liquid = []
    grains = []

    def beaker(*args, **kwargs):
        bounds = original_beaker(*args, **kwargs)
        liquid[:] = bounds
        return bounds

    def polygon(points, *args, **kwargs):
        grains.append(points)
        return original_polygon(points, *args, **kwargs)

    monkeypatch.setattr(detail, '_beaker', beaker)
    monkeypatch.setattr(plate.draw, 'polygon', polygon)
    detail._mixing_beaker(plate, 800, core.GOLD, 'sand')
    assert len(grains) == 24
    assert all(liquid[0] <= x <= liquid[2] and liquid[1] <= y <= liquid[3]
               for grain in grains for x, y in grain)


def test_hot_attachment_is_a_pan_handle_not_a_fridge(monkeypatch):
    chemistry, detail, core = modules()
    spec = chemistry.SPECS['chem.1.materials-props']
    plate = core.SciencePlate('chem.1.materials-props', spec['title'], 1, 'chemistry')
    original = detail._label
    labels = []

    def label(plate, center, value, *args, **kwargs):
        labels.append(value)
        return original(plate, center, value, *args, **kwargs)

    monkeypatch.setattr(detail, '_label', label)
    detail.draw_material_properties(plate, spec['content'])
    assert {'PAN HANDLE', 'HOT', 'COOLER'} <= set(labels)
    assert 'FRIDGE HANDLE' not in labels
    assert 'insulating pan handle' in spec['alt']


def test_nanoparticle_comparison_preserves_volume_and_doubles_surface(monkeypatch):
    chemistry, _detail, core = modules()
    from natural_science_illustrations import chemistry_advanced_detail as detail
    spec = chemistry.SPECS['chem.5.materials']
    plate = core.SciencePlate('chem.5.materials', spec['title'], 5, 'chemistry')
    original = plate.dot
    spheres = []

    def dot(center, radius, **kwargs):
        if radius in (56, 28):
            spheres.append((center, radius))
        return original(center, radius, **kwargs)

    monkeypatch.setattr(plate, 'dot', dot)
    detail.draw_materials(plate, spec['content'])
    large = [item for item in spheres if item[1] == 56]
    small = [item for item in spheres if item[1] == 28]
    assert len(large) == 1 and len(small) == 8
    assert large[0][1] ** 3 == sum(radius ** 3 for _, radius in small)
    assert 2 * large[0][1] ** 2 == sum(radius ** 2 for _, radius in small)
    assert all(math.dist(a, b) > ra + rb
               for i, (a, ra) in enumerate(spheres)
               for b, rb in spheres[i + 1:])


def test_gas_legend_rows_are_separate(monkeypatch):
    chemistry, _detail, core = modules()
    from natural_science_illustrations import chemistry_advanced_detail as detail
    spec = chemistry.SPECS['chem.3.gases']
    plate = core.SciencePlate('chem.3.gases', spec['title'], 3, 'chemistry')
    original = plate.text
    bounds = []

    def text(xy, value, **kwargs):
        if value.startswith(('300 K', '450 K')):
            face = core._science_font(value, kwargs['size'], bold=kwargs.get('bold', False))
            bounds.append(plate.draw.textbbox(xy, value, font=face, anchor=kwargs['anchor']))
        return original(xy, value, **kwargs)

    monkeypatch.setattr(plate, 'text', text)
    detail.draw_gases(plate, spec['content'])
    assert len(bounds) == 2
    assert bounds[0][3] + 5 <= bounds[1][1]


def test_stoichiometry_ledger_keeps_mole_units(monkeypatch):
    chemistry, _detail, core = modules()
    from natural_science_illustrations import chemistry_advanced_detail as detail
    spec = chemistry.SPECS['chem.3.stoichiometry']
    plate = core.SciencePlate('chem.3.stoichiometry', spec['title'], 3, 'chemistry')
    original = plate.text
    labels = []

    def text(xy, value, **kwargs):
        labels.append(value)
        return original(xy, value, **kwargs)

    monkeypatch.setattr(plate, 'text', text)
    detail.draw_stoichiometry(plate, spec['content'])
    assert '10 mol H · 4 mol O' in labels
    assert 'total: 10 mol H · 4 mol O' in labels
    assert {'consume 4 mol H₂', 'consume 2 mol O₂', 'form 4 mol H₂O'} <= set(labels)
