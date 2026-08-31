"""Deterministic mathematics plates for the missing Grove and Forest lessons.

Every diagram is constructed from exact, bounded geometry.  Colour supports
the hierarchy, while labels, line styles, symbols, borders and arrows carry the
same distinctions for readers who do not perceive colour.
"""

from __future__ import annotations

import math
import random
from typing import Callable, List, Sequence, Tuple

from .core import (
    BLUE,
    BLUE_LIGHT,
    CORAL,
    CORAL_LIGHT,
    EDGE,
    GOLD,
    GOLD_LIGHT,
    GREEN,
    GREEN_LIGHT,
    GRID,
    INK,
    INK_SOFT,
    PAPER,
    PAPER_LIGHT,
    PLUM,
    PLUM_LIGHT,
    TEAL,
    TEAL_LIGHT,
    Plate,
    Spec,
    font,
    hex_rgba,
    mix,
    validate_specs,
)


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]


def _curve_points(
    point: Callable[[float, float], Point],
    function: Callable[[float], float],
    start: float,
    end: float,
    *,
    steps: int = 180,
) -> List[Point]:
    return [
        point(x, function(x))
        for x in (start + (end - start) * index / steps for index in range(steps + 1))
    ]


def _open_dot(plate: Plate, center: Point, radius: int = 13, *, outline: str = INK) -> None:
    x, y = center
    plate.draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill=PAPER_LIGHT, outline=outline, width=5,
    )


def _cross(plate: Plate, center: Point, radius: int = 14, *, fill: str = INK, width: int = 6) -> None:
    x, y = center
    plate.draw.line((x - radius, y - radius, x + radius, y + radius), fill=fill, width=width)
    plate.draw.line((x - radius, y + radius, x + radius, y - radius), fill=fill, width=width)


def _cell(
    plate: Plate,
    box: Box,
    value: str,
    *,
    fill: str = PAPER_LIGHT,
    outline: str = EDGE,
    text_fill: str = INK,
    size: int = 25,
    width: int = 3,
) -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(box, radius=9, fill=fill, outline=outline, width=width)
    plate.text(((x0 + x1) / 2, (y0 + y1) / 2), value, size=size, bold=True,
               fill=text_fill, anchor="mm")


def _draw_linalg(plate: Plate) -> None:
    """Compare three maps by following the same marked unit square."""

    source = (395, 208, 1205, 444)
    plate.card(source, fill=mix(PAPER_LIGHT, BLUE_LIGHT, 0.13), outline=BLUE)
    plate.text((800, 236), "SAME MARKED INPUT", size=24, bold=True,
               fill=BLUE, anchor="mm")

    # The four named vertices let the viewer see exactly which distinct
    # points survive—or merge—under each transformation below.
    origin = (505, 407)
    unit = 116
    o = origin
    a = (origin[0] + unit, origin[1])
    b = (origin[0], origin[1] - unit)
    c = (origin[0] + unit, origin[1] - unit)
    plate.draw.line((445, origin[1], 682, origin[1]), fill=GRID, width=3)
    plate.draw.line((origin[0], 430, origin[0], 263), fill=GRID, width=3)
    plate.draw.polygon((o, a, c, b), fill=hex_rgba(BLUE_LIGHT, 115),
                       outline=INK, width=5)
    plate.arrow(o, a, fill=BLUE, width=8, head=20)
    plate.arrow(o, b, fill=TEAL, width=8, head=20)
    for point, label, offset in (
        (o, "O", (-18, 15)), (a, "A", (14, 15)),
        (b, "B", (-18, -15)), (c, "C", (14, -15)),
    ):
        plate.dot(point, 7, fill=GOLD_LIGHT, outline=INK, width=3)
        plate.text((point[0] + offset[0], point[1] + offset[1]), label,
                   size=18, bold=True, anchor="mm")
    plate.text((555, 424), "e1", size=19, bold=True, fill=BLUE, anchor="mm")
    plate.text((485, 344), "e2", size=19, bold=True, fill=TEAL, anchor="mm")

    plate.text((760, 290), "O=(0,0)    A=(1,0)", size=23, bold=True,
               math_face=True, fill=INK)
    plate.text((760, 334), "B=(0,1)    C=(1,1)", size=23, bold=True,
               math_face=True, fill=INK)
    plate.text((760, 378), "basis:  e1=OA,  e2=OB", size=22, bold=True,
               math_face=True, fill=INK)
    plate.label((1012, 414), "input area = 1", size=20, fill=BLUE)

    cards = (
        (116, 525, 542, 880),
        (588, 525, 1014, 880),
        (1060, 525, 1484, 880),
    )
    centers = tuple((box[0] + box[2]) / 2 for box in cards)
    for start_x, center, label, color in (
        (555, centers[0], "I", BLUE),
        (800, centers[1], "S", GOLD),
        (1045, centers[2], "P", CORAL),
    ):
        plate.arrow((start_x, 444), (center, 515), fill=color, width=7, head=20)
        plate.label((center, 500), label, size=19, fill=color)

    for box, color in zip(cards, (BLUE, GOLD, CORAL)):
        plate.card(box, fill=mix(PAPER_LIGHT, color, 0.08), outline=color)

    headers = (
        ("IDENTITY", "I(x,y) = (x,y)", BLUE),
        ("SHEAR", "S(x,y) = (x+y,y)", GOLD),
        ("PROJECTION", "P(x,y) = (x,0)", CORAL),
    )
    for center, (heading, formula, color) in zip(centers, headers):
        plate.text((center, 553), heading, size=23, bold=True,
                   fill=color, anchor="mm")
        plate.text((center, 588), formula, size=21, bold=True,
                   math_face=True, fill=INK, anchor="mm")

    def panel_point(box: Box, x_value: float, y_value: float) -> Point:
        return box[0] + 80 + 116 * x_value, 785 - 116 * y_value

    def reference_square(box: Box) -> Tuple[Point, Point, Point, Point]:
        points = tuple(panel_point(box, x_value, y_value) for x_value, y_value in (
            (0, 0), (1, 0), (0, 1), (1, 1),
        ))
        ref_o, ref_a, ref_b, ref_c = points
        for start, end in ((ref_o, ref_a), (ref_a, ref_c),
                           (ref_c, ref_b), (ref_b, ref_o)):
            plate.dashed_line(start, end, fill=INK_SOFT, width=3, dash=8, gap=7)
        return ref_o, ref_a, ref_b, ref_c

    for box in cards:
        graph_left, graph_right = box[0] + 44, box[2] - 24
        graph_top, graph_bottom = 622, 804
        panel_origin = panel_point(box, 0, 0)
        for grid_x in range(3):
            x_pixel = panel_point(box, grid_x, 0)[0]
            plate.draw.line((x_pixel, graph_top, x_pixel, graph_bottom),
                            fill=hex_rgba(GRID, 145), width=2)
        for grid_y in range(2):
            y_pixel = panel_point(box, 0, grid_y)[1]
            plate.draw.line((graph_left, y_pixel, graph_right, y_pixel),
                            fill=hex_rgba(GRID, 145), width=2)
        plate.arrow((graph_left, panel_origin[1]), (graph_right, panel_origin[1]),
                    fill=INK, width=4, head=15)
        plate.arrow((panel_origin[0], graph_bottom), (panel_origin[0], graph_top),
                    fill=INK, width=4, head=15)

    # Identity: every vertex and both basis vectors stay put.
    i_o, i_a, i_b, i_c = reference_square(cards[0])
    plate.draw.polygon((i_o, i_a, i_c, i_b), fill=hex_rgba(BLUE_LIGHT, 155),
                       outline=BLUE, width=6)
    plate.arrow(i_o, i_a, fill=BLUE, width=7, head=18)
    plate.arrow(i_o, i_b, fill=TEAL, width=7, head=18)
    for point, label, offset in (
        (i_o, "O", (-12, 15)), (i_a, "A", (12, 15)),
        (i_b, "B", (-12, -14)), (i_c, "C", (12, -14)),
    ):
        plate.dot(point, 6, fill=GOLD_LIGHT, outline=INK, width=2)
        plate.text((point[0] + offset[0], point[1] + offset[1]), label,
                   size=16, bold=True, anchor="mm")

    # Shear: e1 is fixed while e2 tilts; the square becomes a same-area
    # parallelogram.  Keeping the source square dashed makes the displacement
    # visible without suggesting a change of input.
    s_o, s_a, _, _ = reference_square(cards[1])
    s_b = panel_point(cards[1], 1, 1)
    s_c = panel_point(cards[1], 2, 1)
    plate.draw.polygon((s_o, s_a, s_c, s_b), fill=hex_rgba(GOLD_LIGHT, 160),
                       outline=GOLD, width=6)
    plate.arrow(s_o, s_a, fill=BLUE, width=7, head=18)
    plate.arrow(s_o, s_b, fill=TEAL, width=7, head=18)
    for point, label, offset in (
        (s_o, "O", (-12, 15)), (s_a, "A", (12, 15)),
        (s_b, "B", (-12, -14)), (s_c, "C", (12, -14)),
    ):
        plate.dot(point, 6, fill=GOLD_LIGHT, outline=INK, width=2)
        plate.text((point[0] + offset[0], point[1] + offset[1]), label,
                   size=16, bold=True, anchor="mm")

    # Projection: the top vertices fall onto the bottom vertices.  The two
    # merging pairs witness non-injectivity, so an inverse cannot recover y.
    p_o, p_a, p_b, p_c = reference_square(cards[2])
    plate.arrow(p_b, p_o, fill=CORAL, width=6, head=18)
    plate.arrow(p_c, p_a, fill=CORAL, width=6, head=18)
    plate.draw.line((*p_o, *p_a), fill=INK, width=14)
    plate.draw.line((*p_o, *p_a), fill=CORAL_LIGHT, width=6)
    for point, label, offset in (
        (p_o, "O = B", (2, 21)), (p_a, "A = C", (2, 21)),
    ):
        plate.dot(point, 8, fill=CORAL_LIGHT, outline=INK, width=3)
        plate.text((point[0] + offset[0], point[1] + offset[1]), label,
                   size=16, bold=True, fill=CORAL, anchor="mm")
    plate.label((cards[2][0] + 183, 686), "P e2 = 0", size=17, fill=CORAL)

    plate.text((centers[0], 830), "det I = 1   •   area stays 1",
               size=20, bold=True, math_face=True, fill=BLUE, anchor="mm")
    plate.text((centers[1], 830), "det S = 1   •   area stays 1",
               size=20, bold=True, math_face=True, fill=GOLD, anchor="mm")
    plate.text((centers[2], 830), "det P = 0   •   area collapses to 0",
               size=19, bold=True, math_face=True, fill=CORAL, anchor="mm")
    plate.text((centers[2], 860), "not invertible: distinct points merge",
               size=17, bold=True, fill=INK, anchor="mm")


def _draw_diff_calc(plate: Plate) -> None:
    plot_box = (142, 238, 1040, 824)
    plate.card((116, 212, 1068, 852), fill=mix(PAPER_LIGHT, CORAL_LIGHT, 0.16))
    point = plate.axes(plot_box, x_range=(-2.1, 2.3), y_range=(-0.5, 4.8), grid_step=1)
    plate.polyline(_curve_points(point, lambda x: x * x, -2.1, 2.18), fill=BLUE, width=10)
    plate.text((168, 258), "f(x) = x²", size=30, bold=True, math_face=True, fill=BLUE)

    fixed = (1.0, 1.0)
    p_pixel = point(*fixed)
    plate.dot(p_pixel, 15, fill=PAPER_LIGHT, outline=INK, width=6)
    plate.text((p_pixel[0] - 12, p_pixel[1] + 34), "P", size=25, bold=True, anchor="ra")
    secants = ((1.0, CORAL, 18, 14), (0.55, PLUM, 13, 10), (0.22, TEAL, 8, 8))
    for h, color, dash, gap in secants:
        slope = 2 + h
        # Intersect the secant with the plot's y-bounds so it cannot escape the panel.
        x_left = max(-2.1, 1 + (-0.5 - 1) / slope)
        x_right = min(2.3, 1 + (4.8 - 1) / slope)
        y_left = 1 + slope * (x_left - 1)
        y_right = 1 + slope * (x_right - 1)
        plate.dashed_line(point(x_left, y_left), point(x_right, y_right),
                          fill=color, width=5, dash=dash, gap=gap)
        q = (1 + h, (1 + h) ** 2)
        plate.dot(point(*q), 11, fill=PAPER_LIGHT, outline=color, width=5)
        plate.text((point(*q)[0] + 12, point(*q)[1] - 18), "h={:.2g}".format(h),
                   size=20, bold=True, fill=color)

    tangent_start = point(0.25, -0.5)
    tangent_end = point(2.3, 3.6)
    plate.draw.line((*tangent_start, *tangent_end), fill=INK, width=13)
    plate.draw.line((*tangent_start, *tangent_end), fill=GOLD_LIGHT, width=4)
    plate.label((782, 754), "limit slope = 2", size=23, fill=INK)

    side = (1100, 212, 1478, 852)
    plate.card(side, fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.18), outline=GOLD)
    plate.text((1289, 253), "CORNER CHECK", size=25, bold=True, fill=GOLD, anchor="mm")
    corner = plate.axes((1140, 302, 1440, 610), x_range=(-1.3, 1.3), y_range=(-0.2, 1.5),
                        grid_step=1, labels=False)
    plate.polyline(_curve_points(corner, abs, -1.28, 1.28), fill=CORAL, width=10)
    plate.dot(corner(0, 0), 13, fill=CORAL, outline=INK, width=4)
    plate.arrow(corner(-0.95, 0.95), corner(-0.3, 0.3), fill=BLUE, width=7, head=19)
    plate.arrow(corner(0.3, 0.3), corner(0.95, 0.95), fill=TEAL, width=7, head=19)
    plate.text((1180, 641), "left slope  −1", size=23, bold=True, fill=BLUE)
    plate.text((1180, 681), "right slope +1", size=23, bold=True, fill=TEAL)
    plate.draw.line((1146, 724, 1434, 724), fill=EDGE, width=3)
    plate.wrapped_text((1144, 733, 1436, 832), "Minimum, but no derivative at the corner",
                       size=24, bold=True, fill=INK)


def _draw_int_calc(plate: Plate) -> None:
    left = (126, 214, 1065, 854)
    plate.card(left, fill=mix(PAPER_LIGHT, CORAL_LIGHT, 0.12))
    top_box = (170, 248, 1015, 500)
    top = plate.axes(top_box, x_range=(-1.4, 2.4), y_range=(-1.5, 2.5), grid_step=1)
    zero_y = top(0, 0)[1]
    negative = [top(-1, 0)] + _curve_points(top, lambda x: x, -1, 0, steps=40) + [top(0, 0)]
    positive = [top(0, 0)] + _curve_points(top, lambda x: x, 0, 2, steps=60) + [top(2, 0)]
    plate.draw.polygon(negative, fill=hex_rgba(CORAL_LIGHT, 180), outline=CORAL)
    plate.draw.polygon(positive, fill=hex_rgba(TEAL_LIGHT, 180), outline=TEAL)
    for x in [value / 10 for value in range(-9, 0, 2)]:
        plate.draw.line((*top(x, 0), *top(x, x)), fill=hex_rgba(CORAL, 125), width=4)
    for x in [value / 10 for value in range(2, 20, 2)]:
        plate.draw.line((*top(x, 0), *top(x, x)), fill=hex_rgba(TEAL, 125), width=4)
    plate.polyline(_curve_points(top, lambda x: x, -1.35, 2.35), fill=INK, width=8)
    plate.text((190, 266), "f(t) = t", size=27, bold=True, math_face=True)
    plate.text((266, zero_y + 54), "− signed", size=22, bold=True, fill=CORAL)
    plate.text((755, zero_y - 52), "+ signed", size=22, bold=True, fill=TEAL)

    bottom_box = (170, 567, 1015, 818)
    bottom = plate.axes(bottom_box, x_range=(-1.4, 2.4), y_range=(-0.7, 2.6), grid_step=1)
    accumulation = lambda x: 0.5 * x * x - 0.5
    plate.polyline(_curve_points(bottom, accumulation, -1, 2.35), fill=BLUE, width=9)
    x_mark = 2.0
    marker_x = top(x_mark, 0)[0]
    plate.dashed_line((marker_x, top_box[1]), (marker_x, bottom_box[3]), fill=GOLD,
                      width=5, dash=13, gap=9)
    tangent = lambda x: accumulation(x_mark) + x_mark * (x - x_mark)
    plate.draw.line((*bottom(1.35, tangent(1.35)), *bottom(2.32, tangent(2.32))),
                    fill=INK, width=9)
    plate.dot(bottom(x_mark, accumulation(x_mark)), 13, fill=GOLD_LIGHT, outline=INK, width=4)
    plate.text((190, 588), "F(x) = ∫₋₁ˣ f(t) dt", size=27, bold=True, math_face=True, fill=BLUE)
    plate.label((827, 772), "slope F′(2) = f(2) = 2", size=21, fill=INK)

    plate.card((1100, 214, 1478, 854), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.18), outline=GOLD)
    plate.text((1289, 268), "ACCUMULATION", size=25, bold=True, fill=GOLD, anchor="mm")
    plate.text((1142, 352), "F(x) = ∫ f(t) dt,  a to x", size=31, bold=True,
               math_face=True)
    plate.double_arrow((1180, 437), (1398, 437), fill=GOLD, width=7)
    plate.text((1289, 486), "Fundamental Theorem", size=24, bold=True, anchor="mm")
    plate.text((1165, 548), "F′(x) = f(x)", size=35, bold=True, math_face=True, fill=BLUE)
    plate.draw.line((1140, 621, 1438, 621), fill=EDGE, width=3)
    _cell(plate, (1147, 659, 1267, 721), "+", fill=TEAL_LIGHT, outline=TEAL, size=32)
    plate.text((1290, 690), "adds", size=25, bold=True, fill=TEAL, anchor="lm")
    _cell(plate, (1147, 746, 1267, 808), "−", fill=CORAL_LIGHT, outline=CORAL, size=32)
    plate.text((1290, 777), "subtracts", size=25, bold=True, fill=CORAL, anchor="lm")


def _draw_multivar(plate: Plate) -> None:
    plate.card((116, 212, 952, 852), fill=mix(PAPER_LIGHT, CORAL_LIGHT, 0.12))
    contour_box = (160, 260, 906, 806)
    point = plate.axes(contour_box, x_range=(-2.5, 2.5), y_range=(-2.5, 2.5), grid_step=1)

    def draw_level(level: float, color: str, dashed: bool = False) -> None:
        branches: List[List[Point]] = []
        if level > 0:
            for sign in (-1, 1):
                branch = []
                for index in range(121):
                    y = -2.4 + 4.8 * index / 120
                    x = sign * math.sqrt(y * y + level)
                    if abs(x) <= 2.5:
                        branch.append(point(x, y))
                branches.append(branch)
        else:
            for sign in (-1, 1):
                branch = []
                for index in range(121):
                    x = -2.4 + 4.8 * index / 120
                    y_sq = x * x - level
                    y = sign * math.sqrt(y_sq)
                    if abs(y) <= 2.5:
                        branch.append(point(x, y))
                branches.append(branch)
        for branch in branches:
            if dashed and len(branch) > 1:
                for first, second in zip(branch[::4], branch[2::4]):
                    plate.draw.line((*first, *second), fill=color, width=4)
            else:
                plate.polyline(branch, fill=color, width=4)

    draw_level(0.75, BLUE)
    draw_level(2.0, BLUE, dashed=True)
    draw_level(-0.75, PLUM)
    draw_level(-2.0, PLUM, dashed=True)
    plate.text((180, 276), "contours of f(x,y)=x²−y²", size=27, bold=True,
               math_face=True, fill=INK)
    p = (1.5, 0.5)
    p_px = point(*p)
    plate.dot(p_px, 15, fill=GOLD_LIGHT, outline=INK, width=5)
    plate.text((p_px[0] + 15, p_px[1] + 30), "P=(1.5,0.5)", size=21, bold=True)
    # Gradient at P is (3,-1); the displayed arrow is scaled but keeps direction.
    gradient_end = point(p[0] + 0.75, p[1] - 0.25)
    plate.arrow(p_px, gradient_end, fill=CORAL, width=10, head=25)
    gradient_text = "∇f=(3,−1)"
    gradient_face = font(22, math_face=True)
    gradient_label = (gradient_end[0] - 40, gradient_end[1] + 75)
    left, top, right, bottom = plate.draw.textbbox(
        gradient_label, gradient_text, font=gradient_face, anchor="mm",
    )
    plate.draw.rounded_rectangle(
        (left - 16, top - 9, right + 16, bottom + 9),
        radius=14, fill=CORAL,
    )
    plate.draw.text(
        gradient_label, gradient_text, font=gradient_face,
        fill=PAPER_LIGHT, anchor="mm",
    )
    # A distinct dashed unit direction u=(3/5,4/5).
    direction_end = point(p[0] + 0.6, p[1] + 0.8)
    plate.dashed_line(p_px, direction_end, fill=TEAL, width=7, dash=14, gap=8)
    plate.arrow(point(p[0] + 0.42, p[1] + 0.56), direction_end,
                fill=TEAL, width=7, head=20)
    plate.text((direction_end[0] - 4, direction_end[1] + 24), "unit direction u",
               size=21, bold=True, fill=TEAL, anchor="ra")

    plate.card((990, 212, 1478, 852), fill=mix(PAPER_LIGHT, BLUE_LIGHT, 0.2), outline=BLUE)
    plate.text((1234, 251), "TWO COORDINATE SLICES", size=23, bold=True,
               fill=BLUE, anchor="mm")
    x_slice = plate.axes((1035, 292, 1435, 500), x_range=(-2, 2), y_range=(-1, 4),
                         grid_step=1, labels=False)
    plate.polyline(_curve_points(x_slice, lambda x: x * x - 0.25, -2, 2),
                   fill=BLUE, width=8)
    plate.text((1050, 310), "hold y=0.5", size=22, bold=True, fill=BLUE)
    plate.label((1235, 531), "at P: ∂f/∂x = 3", size=18, fill=BLUE)
    y_slice = plate.axes((1035, 570, 1435, 778), x_range=(-2, 2), y_range=(-2, 3),
                         grid_step=1, labels=False)
    plate.polyline(_curve_points(y_slice, lambda y: 2.25 - y * y, -2, 2),
                   fill=PLUM, width=8)
    plate.text((1050, 588), "hold x=1.5", size=22, bold=True, fill=PLUM)
    plate.label((1235, 724), "at P: ∂f/∂y = −1", size=18, fill=PLUM)
    plate.label((1234, 820), "directional slope = grad f dot u", size=20, fill=INK)


def _draw_diffeq(plate: Plate) -> None:
    plate.card((116, 212, 1478, 852), fill=mix(PAPER_LIGHT, CORAL_LIGHT, 0.11))
    plot_box = (165, 260, 1435, 780)
    point = plate.axes(plot_box, x_range=(0, 8), y_range=(0, 700), grid_step=100,
                       labels=False)
    for time in range(1, 8):
        px = point(time, 0)[0]
        plate.draw.line((px, plot_box[1], px, plot_box[3]),
                        fill=hex_rgba(GRID, 150), width=2)
    for time in (0, 4, 8):
        plate.text((point(time, 0)[0], plot_box[3] + 8), str(time), size=18,
                   bold=True, fill=INK_SOFT, anchor="ma")
    for population in (0, 500, 700):
        plate.text((plot_box[0] - 12, point(0, population)[1]), str(population),
                   size=18, bold=True, fill=INK_SOFT, anchor="rm")
    plate.text((177, 274), "P′ = 0.4P(1−P/500)", size=30, bold=True,
               math_face=True, fill=INK)
    plate.text((1430, 800), "time", size=24, bold=True, anchor="ra")
    plate.text((177, 306), "population P", size=23, bold=True)

    capacity = 500.0
    rate = 0.4
    for time in [0.45 + 0.68 * index for index in range(11)]:
        for population in [70 + 68 * index for index in range(9)]:
            slope = rate * population * (1 - population / capacity)
            # Preserve rise/run while bounding steep field segments as a unit.
            dx = 0.22
            dy = 2 * dx * slope
            if abs(dy) > 65:
                scale = 65 / abs(dy)
                dx *= scale
                dy *= scale
            first = point(time - dx, population - dy / 2)
            second = point(time + dx, population + dy / 2)
            plate.draw.line((*first, *second), fill=hex_rgba(INK_SOFT, 155), width=4)

    k_y = point(0, capacity)[1]
    plate.dashed_line((plot_box[0], k_y), (plot_box[2], k_y), fill=GOLD,
                      width=7, dash=24, gap=14)
    plate.label((1310, k_y - 30), "equilibrium K=500", size=21, fill=GOLD, text_fill=INK)

    def logistic(initial: float, time: float) -> float:
        factor = capacity / initial - 1
        return capacity / (1 + factor * math.exp(-rate * time))

    starts = ((120.0, BLUE, "below K: rises", 62),
              (350.0, TEAL, "below K: rises", 26),
              (650.0, CORAL, "above K: falls", -95))
    for initial, color, label, label_offset in starts:
        points = [point(time, logistic(initial, time)) for time in
                  (8 * index / 180 for index in range(181))]
        plate.polyline(points, fill=color, width=10)
        end = points[-1]
        plate.dot(points[0], 11, fill=PAPER_LIGHT, outline=color, width=5)
        plate.text((end[0] - 6, end[1] + label_offset), label,
                   size=20, bold=True, fill=color, anchor="ra")

    plate.text((800, 826),
               "Each short segment gives the local slope; one initial value selects one curve.",
               size=22, bold=True, fill=INK_SOFT, anchor="mm")


def _draw_discrete(plate: Plate) -> None:
    plate.card((116, 212, 865, 852), fill=mix(PAPER_LIGHT, CORAL_LIGHT, 0.12))
    center = (490, 520)
    radius = 245
    vertices = [
        (center[0] + radius * math.cos(-math.pi / 2 + 2 * math.pi * index / 5),
         center[1] + radius * math.sin(-math.pi / 2 + 2 * math.pi * index / 5))
        for index in range(5)
    ]
    labels = "ABCDE"
    for first in range(5):
        for second in range(first + 1, 5):
            plate.draw.line((*vertices[first], *vertices[second]),
                            fill=hex_rgba(BLUE, 190), width=7)
    # The center note prevents edge crossings from being read as extra vertices.
    plate.draw.ellipse((425, 455, 555, 585), fill=PAPER_LIGHT, outline=EDGE, width=3)
    plate.text((490, 503), "crossing", size=19, bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((490, 541), "≠ vertex", size=24, bold=True, fill=CORAL, anchor="mm")
    for label, vertex in zip(labels, vertices):
        plate.dot(vertex, 36, fill=GOLD_LIGHT, outline=INK, width=6)
        plate.text(vertex, label, size=28, bold=True, anchor="mm")
        offset_x = 52 if vertex[0] >= center[0] else -52
        plate.text((vertex[0] + offset_x, vertex[1]), "deg 4", size=18, bold=True,
                   fill=BLUE, anchor="lm" if offset_x > 0 else "rm")
    plate.label((490, 802), "K5: 5 vertices, 10 edges", size=23, fill=INK)

    plate.card((900, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.18), outline=GOLD)
    plate.text((1189, 252), "UNORDERED PAIRS", size=25, bold=True, fill=GOLD, anchor="mm")
    pairs = [labels[i] + labels[j] for i in range(5) for j in range(i + 1, 5)]
    for index, pair in enumerate(pairs):
        column = index % 2
        row = index // 2
        x0 = 950 + column * 242
        y0 = 292 + row * 74
        _cell(plate, (x0, y0, x0 + 190, y0 + 56), pair,
              fill=PAPER_LIGHT, outline=BLUE, size=24)
    plate.text((1189, 702), "C(5,2) = 10", size=34, bold=True, math_face=True, anchor="mm")
    plate.draw.line((960, 746, 1418, 746), fill=EDGE, width=3)
    plate.text((1189, 790), "Σ degrees = 5×4 = 20 = 2|E|", size=27, bold=True,
               math_face=True, anchor="mm")
    plate.text((1189, 828), "Every edge is counted at both ends.", size=21,
               fill=INK_SOFT, anchor="mm")


def _draw_numtheory(plate: Plate) -> None:
    plate.card((116, 212, 855, 852), fill=mix(PAPER_LIGHT, CORAL_LIGHT, 0.12))
    center = (485, 525)
    radius = 250
    positions = {}
    for residue in range(7):
        angle = -math.pi / 2 + 2 * math.pi * residue / 7
        positions[residue] = (center[0] + radius * math.cos(angle),
                              center[1] + radius * math.sin(angle))
    plate.draw.ellipse((center[0] - radius, center[1] - radius,
                        center[0] + radius, center[1] + radius),
                       outline=hex_rgba(EDGE, 190), width=8)
    orbit = [1, 2, 4, 1]
    colors = [BLUE, TEAL, CORAL]
    for step, (first, second) in enumerate(zip(orbit, orbit[1:])):
        start, end = positions[first], positions[second]
        vector_x, vector_y = end[0] - start[0], end[1] - start[1]
        length = math.hypot(vector_x, vector_y)
        inset = 46
        adjusted_start = (start[0] + vector_x / length * inset,
                          start[1] + vector_y / length * inset)
        adjusted_end = (end[0] - vector_x / length * inset,
                        end[1] - vector_y / length * inset)
        plate.arrow(adjusted_start, adjusted_end, fill=colors[step], width=10, head=26)
        mid = ((adjusted_start[0] + adjusted_end[0]) / 2,
               (adjusted_start[1] + adjusted_end[1]) / 2)
        plate.label((mid[0], mid[1] - 20), "2^{}".format(step + 1), size=18,
                    fill=colors[step])
    for residue, position in positions.items():
        active = residue in {1, 2, 4}
        plate.dot(position, 35, fill=GOLD_LIGHT if active else PAPER_LIGHT,
                  outline=INK if active else EDGE, width=6 if active else 4)
        plate.text(position, str(residue), size=28, bold=True, anchor="mm")
    plate.text((382, 478), "powers of 2", size=29, bold=True, fill=INK, anchor="mm")
    plate.text((382, 518), "modulo 7", size=25, bold=True, fill=INK_SOFT, anchor="mm")
    plate.label((485, 816), "cycle: 1, 2, 4, then 1  (period 3)", size=22, fill=INK)

    plate.card((892, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.18), outline=GOLD)
    plate.text((1185, 252), "POWER TABLE", size=25, bold=True, fill=GOLD, anchor="mm")
    headers = ["n", "0", "1", "2", "3", "4", "5", "6"]
    values = ["2ⁿ mod 7", "1", "2", "4", "1", "2", "4", "1"]
    column_widths = [112] + [52] * 7
    for row, entries in enumerate((headers, values)):
        x0 = 925
        for column, (value, column_width) in enumerate(zip(entries, column_widths)):
            y0 = 303 + row * 70
            _cell(plate, (x0, y0, x0 + column_width, y0 + 56), value,
                  fill=GOLD_LIGHT if row == 0 else PAPER_LIGHT,
                  outline=INK if column == 0 else EDGE,
                  size=16 if column == 0 else 22)
            x0 += column_width + 5
    plate.draw.line((932, 475, 1438, 475), fill=EDGE, width=3)
    plate.text((1185, 528), "100 = 3×33 + 1", size=29, bold=True,
               math_face=True, anchor="mm")
    plate.text((1185, 578), "so 2¹⁰⁰ mod 7 = 2", size=31, bold=True,
               math_face=True, fill=BLUE, anchor="mm")
    plate.draw.line((932, 630, 1438, 630), fill=EDGE, width=3)
    plate.text((1185, 682), "17 = 2×7 + 3", size=27, bold=True,
               math_face=True, anchor="mm")
    plate.text((1185, 728), "17 ≡ 3  (mod 7)", size=31, bold=True,
               math_face=True, fill=TEAL, anchor="mm")
    plate.wrapped_text((950, 770, 1420, 835), "A residue is a class, not a place the number physically travels.",
                       size=20, fill=INK_SOFT)


def _draw_analysis(plate: Plate) -> None:
    plate.card((116, 212, 1060, 852), fill=mix(PAPER_LIGHT, CORAL_LIGHT, 0.1))
    plot_box = (160, 258, 1015, 806)
    point = plate.axes(plot_box, x_range=(0.8, 3.2), y_range=(2.0, 10.0),
                       grid_step=1, labels=False)
    plate.text((plot_box[2], plot_box[3] + 8), "x", size=22, bold=True,
               math_face=True, anchor="ra")
    plate.text((plot_box[0] - 10, plot_box[1] + 2), "y", size=22, bold=True,
               math_face=True, anchor="ra")
    epsilon = 0.6
    delta = 0.2
    x0, limit = 2.0, 6.0
    x_left, x_right = point(x0 - delta, 0)[0], point(x0 + delta, 0)[0]
    y_top, y_bottom = point(0, limit + epsilon)[1], point(0, limit - epsilon)[1]
    plate.draw.rectangle((plot_box[0], y_top, plot_box[2], y_bottom),
                         fill=hex_rgba(BLUE_LIGHT, 86))
    plate.draw.rectangle((x_left, plot_box[1], x_right, plot_box[3]),
                         fill=hex_rgba(GOLD_LIGHT, 95))
    for x in range(int(x_left), int(x_right) + 1, 18):
        plate.draw.line((x, plot_box[1], x, plot_box[3]), fill=hex_rgba(GOLD, 75), width=3)
    for y in range(int(y_top), int(y_bottom) + 1, 18):
        plate.draw.line((plot_box[0], y, plot_box[2], y), fill=hex_rgba(BLUE, 72), width=3)
    for x in (x_left, x_right):
        plate.dashed_line((x, plot_box[1]), (x, plot_box[3]), fill=GOLD,
                          width=6, dash=16, gap=10)
    for y in (y_top, y_bottom):
        plate.dashed_line((plot_box[0], y), (plot_box[2], y), fill=BLUE,
                          width=6, dash=16, gap=10)
    plate.polyline(_curve_points(point, lambda x: 3 * x, 0.8, 3.2), fill=CORAL, width=10)
    _open_dot(plate, point(x0, limit), 14, outline=INK)
    plate.text((185, 278), "f(x)=3x,  x→2,  L=6", size=28, bold=True,
               math_face=True, fill=INK)
    plate.label((310, y_top - 26), "|f(x)−6| < ε", size=20, fill=BLUE)
    plate.label(((x_left + x_right) / 2, 767), "0 < |x−2| < δ", size=20,
                fill=GOLD, text_fill=INK)
    plate.label((806, y_top - 48), "every nearby x lands inside",
                size=18, fill=CORAL)

    plate.card((1094, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.18), outline=GOLD)
    plate.text((1286, 253), "QUANTIFIER ORDER", size=24, bold=True, fill=GOLD, anchor="mm")
    plate.text((1138, 326), "FOR EVERY", size=20, bold=True, fill=INK_SOFT)
    plate.text((1138, 372), "ε > 0", size=39, bold=True, math_face=True, fill=BLUE)
    plate.arrow((1160, 431), (1395, 431), fill=GOLD, width=8, head=25)
    plate.text((1138, 489), "CHOOSE", size=20, bold=True, fill=INK_SOFT)
    plate.text((1138, 535), "δ = ε / 3", size=39, bold=True, math_face=True, fill=GOLD)
    plate.draw.line((1138, 601, 1436, 601), fill=EDGE, width=3)
    plate.text((1286, 648), "ε = 0.6", size=29, bold=True, math_face=True,
               fill=BLUE, anchor="mm")
    plate.text((1286, 700), "δ = 0.2", size=29, bold=True, math_face=True,
               fill=GOLD, anchor="mm")
    plate.wrapped_text((1136, 738, 1438, 826),
                       "The bands show an all-points condition; sampled dots alone do not prove it.",
                       size=19, bold=True, fill=INK)


def _bernoulli_sequence(length: int = 1000) -> List[int]:
    rng = random.Random(41719)
    return [1 if rng.random() < 0.5 else 0 for _ in range(length)]


def _draw_prob_theory(plate: Plate) -> None:
    plate.card((116, 212, 1478, 852), fill=mix(PAPER_LIGHT, CORAL_LIGHT, 0.1))
    sequence = _bernoulli_sequence()
    checkpoints = (10, 100, 1000)
    counts = [sum(sequence[:count]) for count in checkpoints]

    for index, (trials, heads) in enumerate(zip(checkpoints, counts)):
        x0 = 150 + index * 445
        x1 = x0 + 392
        plate.card((x0, 244, x1, 442), fill=PAPER_LIGHT,
                   outline=(BLUE, TEAL, CORAL)[index])
        plate.text((x0 + 25, 272), "n = {:,}".format(trials), size=25, bold=True,
                   fill=(BLUE, TEAL, CORAL)[index])
        plate.text(((x0 + x1) / 2, 334), "{}/{} heads".format(heads, trials),
                   size=30, bold=True, anchor="mm")
        proportion = heads / trials
        plate.text(((x0 + x1) / 2, 382), "proportion {:.3f}".format(proportion),
                   size=25, bold=True, math_face=True, anchor="mm")
        plate.text(((x0 + x1) / 2, 420), "count gap {:+d}".format(heads - trials // 2),
                   size=20, fill=INK_SOFT, anchor="mm")

    plate.text((800, 472), "horizontal axis: trial count n (log scale)",
               size=20, bold=True, fill=INK_SOFT, anchor="mm")
    chart = (165, 500, 1436, 808)
    plate.draw.rounded_rectangle(chart, radius=18, fill=hex_rgba(PAPER_LIGHT, 210),
                                 outline=EDGE, width=3)
    x0, y0, x1, y1 = chart
    lower, upper = 0.35, 0.72
    for proportion in (0.4, 0.5, 0.6, 0.7):
        y = y1 - (proportion - lower) / (upper - lower) * (y1 - y0)
        if proportion == 0.5:
            plate.dashed_line((x0 + 30, y), (x1 - 25, y), fill=INK,
                              width=6, dash=20, gap=12)
        else:
            plate.draw.line((x0 + 30, y, x1 - 25, y), fill=hex_rgba(GRID, 170), width=3)
        plate.text((x0 + 20, y), "{:.1f}".format(proportion), size=18, anchor="rm")

    plot_points = []
    running = 0
    sample_indices = list(range(10, 1001, 5))
    for trial, outcome in enumerate(sequence, 1):
        running += outcome
        if trial in sample_indices:
            px = x0 + 36 + (math.log10(trial) - 1) / 2 * (x1 - x0 - 72)
            proportion = running / trial
            py = y1 - (proportion - lower) / (upper - lower) * (y1 - y0)
            plot_points.append((px, py))
    plate.polyline(plot_points, fill=BLUE, width=7)
    for trials, heads, color in zip(checkpoints, counts, (BLUE, TEAL, CORAL)):
        px = x0 + 36 + (math.log10(trials) - 1) / 2 * (x1 - x0 - 72)
        py = y1 - (heads / trials - lower) / (upper - lower) * (y1 - y0)
        plate.dot((px, py), 11, fill=PAPER_LIGHT, outline=color, width=5)
        plate.text((px, y1 - 13), str(trials), size=18, bold=True, fill=color, anchor="ms")
    plate.label((1246, 536), "reference p = 0.5", size=19, fill=INK)
    plate.text((800, 831),
               "authored, reproducible trial sequence • proportions settle; raw counts still fluctuate",
               size=21, bold=True, fill=INK_SOFT, anchor="mm")


def _operation_table(
    plate: Plate,
    origin: Point,
    symbols: Sequence[str],
    values: Sequence[Sequence[str]],
    *,
    accent: str,
    heading: str,
    operator: str,
) -> None:
    x0, y0 = origin
    cell = 66
    plate.text((x0 + cell * 2.5, y0 - 48), heading, size=26, bold=True,
               fill=accent, anchor="mm")
    _cell(plate, (x0, y0, x0 + cell, y0 + cell), operator, fill=accent,
          outline=INK, text_fill=PAPER_LIGHT, size=25)
    for index, symbol in enumerate(symbols):
        _cell(plate, (x0 + (index + 1) * cell, y0,
                      x0 + (index + 2) * cell, y0 + cell), symbol,
              fill=GOLD_LIGHT, outline=INK, size=24)
        _cell(plate, (x0, y0 + (index + 1) * cell,
                      x0 + cell, y0 + (index + 2) * cell), symbol,
              fill=GOLD_LIGHT, outline=INK, size=24)
    for row, row_values in enumerate(values):
        for column, value in enumerate(row_values):
            fill = mix(PAPER_LIGHT, accent, 0.12)
            border = INK if row == column else EDGE
            _cell(plate, (x0 + (column + 1) * cell, y0 + (row + 1) * cell,
                          x0 + (column + 2) * cell, y0 + (row + 2) * cell),
                  value, fill=fill, outline=border, size=23,
                  width=5 if row == column else 3)


def _draw_abstract(plate: Plate) -> None:
    plate.card((116, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.12))
    c4_symbols = ("0", "1", "2", "3")
    c4_values = tuple(tuple(str((row + col) % 4) for col in range(4)) for row in range(4))
    v4_symbols = ("e", "a", "b", "c")
    v4_values = (
        ("e", "a", "b", "c"),
        ("a", "e", "c", "b"),
        ("b", "c", "e", "a"),
        ("c", "b", "a", "e"),
    )
    _operation_table(plate, (168, 304), c4_symbols, c4_values,
                     accent=BLUE, heading="CYCLIC GROUP C4", operator="+")
    _operation_table(plate, (910, 304), v4_symbols, v4_values,
                     accent=PLUM, heading="KLEIN FOUR-GROUP V4", operator="*")
    plate.label((402, 702), "add 1:  0, 1, 2, 3, then 0", size=21, fill=BLUE)
    plate.label((1144, 702), "a*a=e,  b*b=e,  c*c=e", size=21, fill=PLUM)
    plate.draw.line((170, 758, 1424, 758), fill=EDGE, width=3)
    plate.text((800, 805), "same number of elements  ≠  same group structure",
               size=30, bold=True, fill=INK, anchor="mm")
    plate.text((800, 839), "Diagonal borders mark each element combined with itself.",
               size=20, fill=INK_SOFT, anchor="mm")


def _draw_measure(plate: Plate) -> None:
    plate.card((116, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.12))
    line_left, line_right = 185, 1185
    base_y = 756
    plate.draw.line((line_left, base_y, line_right, base_y), fill=INK, width=7)
    plate.text((line_left, base_y + 32), "0", size=23, bold=True, anchor="mm")
    plate.text((line_right, base_y + 32), "1", size=23, bold=True, anchor="mm")
    rationals = (0.5, 1 / 3, 2 / 3, 0.25, 0.75, 0.2)
    epsilon = 0.5
    colors = (BLUE, TEAL, CORAL, PLUM, GREEN, GOLD)
    for index, (rational, color) in enumerate(zip(rationals, colors), 1):
        y = 278 + (index - 1) * 70
        length = epsilon / (2 ** index)
        center = line_left + rational * (line_right - line_left)
        half = length * (line_right - line_left) / 2
        plate.draw.line((center - half, y, center + half, y), fill=color, width=12)
        _open_dot(plate, (center - half, y), 8, outline=color)
        _open_dot(plate, (center + half, y), 8, outline=color)
        plate.dashed_line((center, y + 8), (center, base_y - 10), fill=color,
                          width=3, dash=8, gap=9)
        plate.dot((center, base_y), 9, fill=PAPER_LIGHT, outline=color, width=4)
        plate.text((130, y), "q{}".format(index), size=21, bold=True,
                   fill=color, anchor="rm")
        plate.text((1218, y), "length ε/2{}".format("^" + str(index)),
                   size=21, bold=True, fill=color, anchor="lm")
    plate.label((515, 235), "finite prefix of an infinite enumeration", size=21, fill=INK)
    plate.card((1235, 658, 1445, 824), fill=PAPER_LIGHT, outline=GOLD)
    plate.text((1340, 684), "LENGTH BUDGET", size=18, bold=True, fill=GOLD, anchor="mm")
    plate.text((1340, 721), "first 6", size=19, bold=True, anchor="mm")
    plate.text((1340, 762), "63ε / 64", size=27, bold=True, math_face=True, anchor="mm")
    plate.text((1340, 800), "< ε", size=28, bold=True, math_face=True,
               fill=TEAL, anchor="mm")
    plate.text((800, 833), "dense can still have measure zero • the drawing is not the whole countable cover",
               size=21, bold=True, fill=INK_SOFT, anchor="mm")


def _draw_grid_patch(
    plate: Plate,
    box: Box,
    transform: Callable[[float, float], Point],
    *,
    accent: str,
) -> None:
    x0, y0, x1, y1 = box
    for index in range(7):
        u = index / 6
        points = [transform(u, step / 80) for step in range(81)]
        plate.polyline(points, fill=hex_rgba(GRID, 210), width=3)
    for index in range(5):
        v = index / 4
        points = [transform(step / 80, v) for step in range(81)]
        plate.polyline(points, fill=hex_rgba(GRID, 210), width=3)
    loop = [
        transform(0.5 + 0.24 * math.cos(angle), 0.5 + 0.29 * math.sin(angle))
        for angle in (2 * math.pi * step / 120 for step in range(121))
    ]
    plate.polyline(loop, fill=accent, width=10)
    for fraction in (0.0, 0.25, 0.5, 0.75):
        angle = 2 * math.pi * fraction
        point = transform(0.5 + 0.24 * math.cos(angle), 0.5 + 0.29 * math.sin(angle))
        plate.dot(point, 7, fill=PAPER_LIGHT, outline=INK, width=3)


def _draw_topology(plate: Plate) -> None:
    plate.card((116, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.12))
    left_box = (158, 270, 635, 585)
    right_box = (700, 270, 1177, 585)
    plate.text((396, 242), "BEFORE", size=24, bold=True, fill=BLUE, anchor="mm")
    plate.text((938, 242), "AFTER A STRETCH", size=24, bold=True, fill=TEAL, anchor="mm")

    def flat(u: float, v: float) -> Point:
        return (left_box[0] + u * (left_box[2] - left_box[0]),
                left_box[1] + v * (left_box[3] - left_box[1]))

    def warped(u: float, v: float) -> Point:
        width = right_box[2] - right_box[0]
        height = right_box[3] - right_box[1]
        return (right_box[0] + u * width + 34 * math.sin(math.pi * v) * (u - 0.5),
                right_box[1] + v * height + 32 * math.sin(math.pi * u) * math.sin(math.pi * v))

    _draw_grid_patch(plate, left_box, flat, accent=BLUE)
    _draw_grid_patch(plate, right_box, warped, accent=TEAL)
    plate.double_arrow((636, 428), (696, 428), fill=GOLD, width=7)
    plate.label((1320, 331), "NO CUT", size=20, fill=INK)
    plate.draw.line((1240, 385, 1400, 385), fill=CORAL, width=11)
    plate.draw.line((1310, 357, 1330, 413), fill=PAPER_LIGHT, width=20)
    _cross(plate, (1320, 385), 32, fill=CORAL, width=8)
    plate.text((1320, 450), "tearing changes", size=20, bold=True, fill=CORAL, anchor="mm")
    plate.text((1320, 480), "the topology", size=20, bold=True, fill=CORAL, anchor="mm")

    plate.draw.line((160, 625, 1434, 625), fill=EDGE, width=3)
    centers = (360, 800, 1240)
    # Boundary-surface icons: sphere, torus, and schematic double torus.
    plate.draw.ellipse((centers[0] - 105, 665, centers[0] + 105, 803),
                       fill=BLUE_LIGHT, outline=INK, width=6)
    plate.draw.arc((centers[0] - 80, 694, centers[0] + 80, 774), 0, 360,
                   fill=hex_rgba(BLUE, 150), width=4)
    plate.draw.ellipse((centers[1] - 125, 665, centers[1] + 125, 803),
                       fill=TEAL_LIGHT, outline=INK, width=6)
    plate.draw.ellipse((centers[1] - 52, 697, centers[1] + 52, 771),
                       fill=PAPER_LIGHT, outline=INK, width=6)
    for offset in (-72, 72):
        plate.draw.ellipse((centers[2] + offset - 92, 670, centers[2] + offset + 92, 798),
                           fill=GOLD_LIGHT, outline=INK, width=6)
        plate.draw.ellipse((centers[2] + offset - 37, 702, centers[2] + offset + 37, 766),
                           fill=PAPER_LIGHT, outline=INK, width=5)
    plate.draw.rectangle((centers[2] - 72, 704, centers[2] + 72, 766),
                         fill=GOLD_LIGHT, outline=INK, width=5)
    for center, genus in zip(centers, (0, 1, 2)):
        plate.text((center, 828), "boundary surface • genus {}".format(genus),
                   size=20, bold=True, anchor="mm")


def _draw_diffgeo(plate: Plate) -> None:
    plate.card((116, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.12))
    plate.text((392, 244), "INTRINSICALLY FLAT", size=24, bold=True, fill=BLUE, anchor="mm")
    # Flat sheet.
    sheet = (160, 286, 625, 512)
    plate.draw.rounded_rectangle(sheet, radius=14, fill=BLUE_LIGHT, outline=INK, width=6)
    for index in range(1, 6):
        x = sheet[0] + (sheet[2] - sheet[0]) * index / 6
        plate.draw.line((x, sheet[1], x, sheet[3]), fill=hex_rgba(INK_SOFT, 130), width=3)
    for index in range(1, 4):
        y = sheet[1] + (sheet[3] - sheet[1]) * index / 4
        plate.draw.line((sheet[0], y, sheet[2], y), fill=hex_rgba(INK_SOFT, 130), width=3)
    plate.label((392, 547), "sheet: K = 0", size=21, fill=BLUE)

    # Cylinder: same six-by-four grid, rolled without stretching.
    cx, top_y, bottom_y = 845, 286, 512
    rx, ry = 170, 44
    plate.draw.rectangle((cx - rx, top_y, cx + rx, bottom_y), fill=TEAL_LIGHT)
    plate.draw.ellipse((cx - rx, top_y - ry, cx + rx, top_y + ry),
                       fill=TEAL_LIGHT, outline=INK, width=6)
    plate.draw.ellipse((cx - rx, bottom_y - ry, cx + rx, bottom_y + ry),
                       fill=TEAL_LIGHT, outline=INK, width=6)
    plate.draw.line((cx - rx, top_y, cx - rx, bottom_y), fill=INK, width=6)
    plate.draw.line((cx + rx, top_y, cx + rx, bottom_y), fill=INK, width=6)
    for index in range(1, 6):
        x = cx - rx + 2 * rx * index / 6
        plate.draw.line((x, top_y, x, bottom_y), fill=hex_rgba(INK_SOFT, 130), width=3)
    for index in range(1, 4):
        y = top_y + (bottom_y - top_y) * index / 4
        plate.draw.arc((cx - rx, y - ry, cx + rx, y + ry), 0, 360,
                       fill=hex_rgba(INK_SOFT, 130), width=3)
    plate.label((845, 547), "cylinder: K = 0", size=21, fill=TEAL)
    plate.double_arrow((590, 398), (670, 398), fill=GOLD, width=8)
    plate.text((630, 365), "roll", size=19, bold=True, fill=GOLD, anchor="mm")

    # Positive and negative curvature cues.
    sphere_center = (1217, 397)
    sphere_r = 164
    plate.draw.ellipse((sphere_center[0] - sphere_r, sphere_center[1] - sphere_r,
                        sphere_center[0] + sphere_r, sphere_center[1] + sphere_r),
                       fill=GOLD_LIGHT, outline=INK, width=7)
    plate.draw.ellipse((sphere_center[0] - sphere_r, sphere_center[1] - 48,
                        sphere_center[0] + sphere_r, sphere_center[1] + 48),
                       outline=hex_rgba(INK_SOFT, 150), width=4)
    north = (sphere_center[0], sphere_center[1] - sphere_r + 16)
    west = (sphere_center[0] - sphere_r + 22, sphere_center[1])
    south_front = (sphere_center[0], sphere_center[1] + 44)
    plate.draw.arc((sphere_center[0] - sphere_r, sphere_center[1] - sphere_r,
                    sphere_center[0] + sphere_r, sphere_center[1] + sphere_r),
                   180, 270, fill=CORAL, width=11)
    plate.draw.line((*north, *south_front), fill=CORAL, width=11)
    plate.draw.arc((sphere_center[0] - sphere_r, sphere_center[1] - 48,
                    sphere_center[0] + sphere_r, sphere_center[1] + 48),
                   90, 180, fill=CORAL, width=11)
    for vertex in (north, west, south_front):
        plate.dot(vertex, 10, fill=PAPER_LIGHT, outline=CORAL, width=4)
        plate.text((vertex[0] + 15, vertex[1] - 9), "90°", size=17,
                   bold=True, fill=CORAL)
    plate.label((1217, 594), "sphere: K > 0", size=21, fill=CORAL)
    plate.text((1217, 627), "90°+90°+90° > 180°", size=20, bold=True,
               math_face=True, anchor="mm")

    plate.draw.line((160, 657, 1437, 657), fill=EDGE, width=3)
    # Saddle grid: a precise schematic of opposite principal bending.
    saddle_center = (390, 735)
    for offset in (-80, -40, 0, 40, 80):
        points = []
        for step in range(101):
            x = -145 + 290 * step / 100
            y = offset * 0.3 + (x * x / 400) * (1 if offset >= 0 else -1)
            points.append((saddle_center[0] + x, saddle_center[1] + y))
        plate.polyline(points, fill=PLUM if offset else INK, width=4)
    for offset in (-120, -60, 0, 60, 120):
        points = []
        for step in range(101):
            y = -90 + 180 * step / 100
            x = offset * 0.45 + (y * y / 250) * (1 if offset >= 0 else -1)
            points.append((saddle_center[0] + x, saddle_center[1] + y))
        plate.polyline(points, fill=hex_rgba(PLUM, 170), width=3)
    plate.label((390, 825), "saddle: K < 0", size=19, fill=PLUM)
    plate.wrapped_text((620, 691, 1405, 829),
                       "Visible bending is extrinsic. Gaussian curvature is read from distances, geodesics and angle behavior within the surface.",
                       size=27, bold=True, fill=INK)


def _sequence_row(
    plate: Plate,
    origin: Point,
    values: Sequence[str],
    *,
    accent: str,
    label: str,
) -> None:
    x0, y0 = origin
    plate.text((x0 - 36, y0 + 34), label, size=29, bold=True, math_face=True,
               fill=accent, anchor="rm")
    for index, value in enumerate(values):
        left = x0 + index * 94
        _cell(plate, (left, y0, left + 78, y0 + 68), value,
              fill=mix(PAPER_LIGHT, accent, 0.12), outline=accent, size=25)
    plate.text((x0 + len(values) * 94 - 2, y0 + 34), "…", size=35, bold=True,
               fill=INK, anchor="lm")


def _draw_functional(plate: Plate) -> None:
    plate.card((116, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.12))
    plate.text((800, 242), "A WINDOW INTO AN INFINITE ℓ² SEQUENCE", size=25,
               bold=True, fill=GOLD, anchor="mm")
    _sequence_row(plate, (255, 292), ("3", "4", "0", "0", "0", "0"),
                  accent=BLUE, label="x =")
    plate.arrow((690, 392), (910, 392), fill=GOLD, width=10, head=28)
    plate.text((800, 365), "unilateral shift S", size=22, bold=True,
               fill=GOLD, anchor="mm")
    _sequence_row(plate, (255, 430), ("0", "3", "4", "0", "0", "0"),
                  accent=TEAL, label="Sx =")
    plate.label((445, 548), "||x||^2 = 3^2 + 4^2 = 25", size=21, fill=BLUE)
    plate.label((1080, 548), "||Sx||^2 = 0^2 + 3^2 + 4^2 = 25", size=21, fill=TEAL)

    plate.draw.line((160, 605, 1436, 605), fill=EDGE, width=3)
    plate.text((330, 672), "target y =", size=24, bold=True, fill=CORAL,
               anchor="rm")
    _sequence_row(plate, (355, 638), ("1", "0", "0", "0"),
                  accent=CORAL, label="")
    plate.arrow((860, 674), (1030, 674), fill=CORAL, width=9, head=27)
    plate.card((1055, 628, 1418, 750), fill=CORAL_LIGHT, outline=CORAL)
    plate.text((1236, 663), "NO PREIMAGE", size=26, bold=True, fill=CORAL, anchor="mm")
    plate.text((1236, 708), "every Sx starts with 0", size=21, bold=True,
               fill=INK, anchor="mm")
    plate.text((800, 806), "S preserves norm (isometry) but is not onto — an infinite-dimensional signal.",
               size=25, bold=True, fill=INK, anchor="mm")
    plate.text((800, 839), "Ellipses are essential: the space is not the six boxes shown.",
               size=20, fill=INK_SOFT, anchor="mm")


def _draw_complex_analysis(plate: Plate) -> None:
    plate.card((116, 212, 930, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.1))
    plane_box = (170, 258, 875, 807)
    point = plate.axes(plane_box, x_range=(-1.5, 3.5), y_range=(-2.2, 2.2), grid_step=1)
    plate.text((190, 278), "f(z)=1 / [z(z−2)]", size=29, bold=True,
               math_face=True, fill=INK)
    pole_zero = point(0, 0)
    pole_two = point(2, 0)
    _cross(plate, pole_zero, 18, fill=CORAL, width=8)
    _cross(plate, pole_two, 18, fill=PLUM, width=8)
    plate.text((pole_zero[0] - 18, pole_zero[1] + 40), "pole 0 • Res −1/2",
               size=20, bold=True, fill=CORAL, anchor="ra")
    plate.text((pole_two[0] + 18, pole_two[1] + 40), "pole 2 • Res +1/2",
               size=20, bold=True, fill=PLUM, anchor="la")

    # Solid C1 encloses only zero; dashed C2 encloses both poles.
    c1_center = point(0, 0)
    c1_rx = abs(point(0.88, 0)[0] - c1_center[0])
    c1_ry = abs(point(0, 1.2)[1] - c1_center[1])
    c1_box = (c1_center[0] - c1_rx, c1_center[1] - c1_ry,
              c1_center[0] + c1_rx, c1_center[1] + c1_ry)
    plate.draw.ellipse(c1_box, outline=BLUE, width=10)
    plate.arrow((c1_center[0] + 45, c1_center[1] - c1_ry),
                (c1_center[0] - 20, c1_center[1] - c1_ry),
                fill=BLUE, width=9, head=25)
    plate.label((c1_center[0] - c1_rx + 12, c1_center[1] - c1_ry - 25),
                "C1 solid • CCW", size=18, fill=BLUE)

    c2_center = point(1, 0)
    c2_rx = abs(point(2.55, 0)[0] - c2_center[0])
    c2_ry = abs(point(0, 1.75)[1] - point(0, 0)[1])
    c2_box = (c2_center[0] - c2_rx, c2_center[1] - c2_ry,
              c2_center[0] + c2_rx, c2_center[1] + c2_ry)
    for start in range(0, 360, 22):
        plate.draw.arc(c2_box, start, min(start + 12, 360), fill=GOLD, width=7)
    plate.arrow((c2_center[0] + 50, c2_center[1] - c2_ry),
                (c2_center[0] - 20, c2_center[1] - c2_ry),
                fill=GOLD, width=7, head=22)
    plate.label((c2_center[0] + c2_rx - 40, c2_center[1] + c2_ry - 5),
                "C2 dashed • both poles", size=18, fill=GOLD, text_fill=INK)

    plate.card((965, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.18), outline=GOLD)
    plate.text((1221, 253), "RESIDUE ACCOUNT", size=24, bold=True,
               fill=GOLD, anchor="mm")
    plate.text((1010, 324), "∮C f(z) dz", size=34, bold=True,
               math_face=True, fill=INK)
    plate.text((1010, 375), "= 2πi × sum enclosed residues", size=25, bold=True,
               math_face=True, fill=INK)
    plate.draw.line((1010, 425, 1435, 425), fill=EDGE, width=3)
    plate.text((1025, 475), "C1 encloses 0 only", size=23, bold=True, fill=BLUE)
    plate.text((1025, 523), "integral = 2πi(−1/2) = −πi", size=26,
               bold=True, math_face=True)
    plate.draw.line((1010, 570, 1435, 570), fill=EDGE, width=3)
    plate.text((1025, 620), "C2 encloses both", size=23, bold=True, fill=GOLD)
    plate.text((1025, 668), "residue sum = −1/2 + 1/2 = 0", size=24,
               bold=True, math_face=True)
    plate.text((1025, 716), "integral = 0", size=28, bold=True, fill=TEAL)
    plate.card((1015, 760, 1428, 821), fill=CORAL_LIGHT, outline=CORAL)
    plate.text((1221, 790), "No pole may lie on the path.", size=22,
               bold=True, fill=CORAL, anchor="mm")


def _draw_logic(plate: Plate) -> None:
    plate.card((116, 212, 1082, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.1))
    rows = (
        "00101101", "11001010", "01011100", "11100010",
        "00010111", "10110001", "01101011", "10011100",
    )
    x0, y0 = 225, 276
    cell_w, cell_h = 83, 55
    for column in range(8):
        plate.text((x0 + column * cell_w + cell_w / 2, y0 - 26), str(column + 1),
                   size=18, bold=True, fill=INK_SOFT, anchor="mm")
    anti_bits = []
    for row_index, bits in enumerate(rows):
        y = y0 + row_index * cell_h
        plate.text((x0 - 20, y + cell_h / 2), "s{}".format(row_index + 1),
                   size=20, bold=True, math_face=True, fill=INK, anchor="rm")
        for column, bit in enumerate(bits):
            diagonal = column == row_index
            _cell(plate, (x0 + column * cell_w, y,
                          x0 + column * cell_w + cell_w - 8, y + cell_h - 7),
                  bit,
                  fill=GOLD_LIGHT if diagonal else PAPER_LIGHT,
                  outline=CORAL if diagonal else EDGE,
                  size=23, width=6 if diagonal else 2)
            if diagonal:
                anti_bits.append("1" if bit == "0" else "0")
                _cross(plate, (x0 + column * cell_w + (cell_w - 8) / 2,
                               y + (cell_h - 7) / 2), 15, fill=CORAL, width=4)
    plate.text((945, 478), "…", size=42, bold=True, anchor="mm")
    plate.draw.line((170, 732, 1026, 732), fill=EDGE, width=3)
    plate.text((x0 - 20, 785), "d", size=23, bold=True, math_face=True,
               fill=BLUE, anchor="rm")
    for column, bit in enumerate(anti_bits):
        _cell(plate, (x0 + column * cell_w, 758,
                      x0 + column * cell_w + cell_w - 8, 812),
              bit, fill=BLUE_LIGHT, outline=BLUE, size=24, width=5)
    plate.text((945, 785), "…", size=42, bold=True, fill=BLUE, anchor="mm")
    plate.label((607, 837), "flip each diagonal bit", size=21, fill=BLUE)

    plate.card((1115, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.18), outline=GOLD)
    plate.text((1296, 254), "DIAGONAL RULE", size=23, bold=True, fill=GOLD, anchor="mm")
    plate.text((1155, 330), "d[n] = 1 - s[n,n]", size=31, bold=True,
               math_face=True, fill=INK)
    plate.arrow((1180, 392), (1400, 392), fill=GOLD, width=8, head=24)
    plate.wrapped_text((1150, 424, 1440, 552),
                       "At position n, the new sequence differs from listed row n.",
                       size=25, bold=True, fill=INK)
    plate.draw.line((1150, 590, 1440, 590), fill=EDGE, width=3)
    plate.text((1296, 635), "FINITE WINDOW", size=23, bold=True,
               fill=CORAL, anchor="mm")
    plate.wrapped_text((1150, 667, 1440, 812),
                       "The table illustrates an infinite construction. Eight rows alone do not prove uncountability.",
                       size=23, bold=True, fill=CORAL)


def _draw_numerical(plate: Plate) -> None:
    plate.card((116, 212, 820, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.1))
    plate.card((855, 212, 1478, 852), fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.16), outline=GOLD)
    plate.text((468, 246), "NEWTON: TANGENT STEP", size=24, bold=True,
               fill=BLUE, anchor="mm")
    newton_box = (160, 282, 775, 620)
    newton = plate.axes(newton_box, x_range=(0, 2.2), y_range=(-2, 2.8), grid_step=1)
    plate.polyline(_curve_points(newton, lambda x: x * x - 2, 0, 2.18), fill=INK, width=9)
    tangent = lambda x: 2 * x - 3
    plate.draw.line((*newton(0.45, tangent(0.45)), *newton(2.1, tangent(2.1))),
                    fill=BLUE, width=9)
    x_zero_y = newton(0, 0)[1]
    plate.dot(newton(1, -1), 13, fill=PAPER_LIGHT, outline=BLUE, width=5)
    plate.dot(newton(1.5, 0), 13, fill=BLUE_LIGHT, outline=INK, width=5)
    plate.dashed_line((newton(1, 0)[0], x_zero_y), newton(1, -1), fill=BLUE,
                      width=4, dash=10, gap=8)
    plate.text((newton(1, 0)[0], x_zero_y + 31), "x0=1", size=20, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((newton(1.5, 0)[0], x_zero_y + 31), "x1=1.5", size=20, bold=True,
               fill=BLUE, anchor="mm")
    plate.label((468, 655), "x(n+1) = x(n) - f(x(n))/f'(x(n))", size=19, fill=BLUE)
    newton_values = ("1.0000", "1.5000", "1.4167", "1.4142")
    for index, value in enumerate(newton_values):
        x = 165 + index * 154
        _cell(plate, (x, 718, x + 132, 774), value, fill=PAPER_LIGHT,
              outline=BLUE, size=20)
        if index < len(newton_values) - 1:
            plate.arrow((x + 134, 746), (x + 150, 746), fill=BLUE, width=5, head=13)
    plate.text((468, 816), "fast near a simple root • not guaranteed globally", size=20,
               bold=True, fill=INK_SOFT, anchor="mm")

    plate.text((1166, 246), "BISECTION: VALID BRACKET", size=24, bold=True,
               fill=GOLD, anchor="mm")
    bisect_box = (900, 282, 1435, 548)
    bisect = plate.axes(bisect_box, x_range=(0.75, 2.1), y_range=(-1.5, 2.5), grid_step=1,
                        labels=False)
    plate.polyline(_curve_points(bisect, lambda x: x * x - 2, 0.75, 2.08), fill=INK, width=9)
    for x, label, style in ((1.0, "a", BLUE), (2.0, "b", CORAL), (1.5, "m1", GOLD)):
        px = bisect(x, 0)[0]
        plate.dashed_line((px, bisect_box[1]), (px, bisect_box[3]), fill=style,
                          width=5, dash=13, gap=9)
        plate.text((px, bisect(0, 0)[1] + 28), label, size=19, bold=True,
                   fill=style, anchor="mm")
    intervals = (("[1, 2]", 1.0), ("[1, 1.5]", 0.5), ("[1.25, 1.5]", 0.25))
    for index, (label, width_value) in enumerate(intervals):
        y = 610 + index * 66
        x_start = 925 + index * 48
        x_end = x_start + width_value * 380
        plate.draw.line((x_start, y, x_end, y), fill=(BLUE, TEAL, GOLD)[index], width=12)
        plate.draw.line((x_start, y - 16, x_start, y + 16), fill=INK, width=5)
        plate.draw.line((x_end, y - 16, x_end, y + 16), fill=INK, width=5)
        plate.text((1375, y), label, size=22, bold=True, math_face=True,
                   fill=(BLUE, TEAL, GOLD)[index], anchor="rm")
    plate.text((1166, 814), "continuous f + opposite endpoint signs", size=21,
               bold=True, fill=INK_SOFT, anchor="mm")


def _draw_frontier(plate: Plate) -> None:
    """Separate finite evidence, arbitrary-case proof, and falsification."""

    # Euler's prime-producing polynomial makes the boundary between a long
    # finite check and a universal statement concrete: it is prime for every
    # integer 0 <= n <= 39, then fails at the very next integer.
    plate.card((116, 212, 1478, 474),
               fill=mix(PAPER_LIGHT, GOLD_LIGHT, 0.14), outline=GOLD)
    plate.text((797, 243), "FINITE COMPUTATION: EVIDENCE, NOT UNIVERSAL PROOF",
               size=23, bold=True, fill=GOLD, anchor="mm")
    plate.text((797, 280), "Conjecture:  f(n) = n² + n + 41  is prime for every integer n ≥ 0",
               size=27, bold=True, math_face=True, fill=INK, anchor="mm")

    checked_cases = (("n=0", "41"), ("n=1", "43"), ("n=2", "47"),
                     ("n=3", "53"), ("...", "..."), ("n=39", "1601"))
    cell_w = 126
    cell_gap = 12
    start_x = 145
    for index, (case, value) in enumerate(checked_cases):
        x0 = start_x + index * (cell_w + cell_gap)
        box = (x0, 316, x0 + cell_w, 389)
        plate.draw.rounded_rectangle(
            box, radius=12, fill=BLUE_LIGHT, outline=INK, width=4,
        )
        if case != "...":
            plate.text((x0 + 12, 327), case, size=18, bold=True, fill=INK)
            plate.text((x0 + cell_w / 2, 367), value, size=22, bold=True,
                       math_face=True, fill=BLUE, anchor="mm")
            # The tick is geometry, not a color-dependent or font-dependent glyph.
            plate.draw.line((x0 + 94, 337, x0 + 103, 346), fill=INK, width=5)
            plate.draw.line((x0 + 103, 346, x0 + 118, 326), fill=INK, width=5)
        else:
            plate.text((x0 + cell_w / 2, 352), "...", size=28, bold=True,
                       fill=INK, anchor="mm")

    checked_right = start_x + len(checked_cases) * (cell_w + cell_gap) - cell_gap
    plate.draw.line((start_x, 410, checked_right, 410), fill=INK, width=4)
    plate.draw.line((start_x, 399, start_x, 421), fill=INK, width=4)
    plate.draw.line((checked_right, 399, checked_right, 421), fill=INK, width=4)
    plate.text(((start_x + checked_right) / 2, 440),
               "all 40 integer cases from 0 through 39 checked",
               size=20, bold=True, fill=BLUE, anchor="mm")

    bound_x = 1000
    plate.dashed_line((bound_x, 310), (bound_x, 445), fill=INK,
                      width=5, dash=11, gap=8)
    plate.text((bound_x, 306), "BOUND 39", size=17, bold=True,
               fill=INK, anchor="mm")
    for index, case in enumerate(("n=40", "n=41")):
        x0 = 1035 + index * 150
        plate.draw.rounded_rectangle(
            (x0, 316, x0 + 126, 389), radius=12,
            fill=PAPER_LIGHT, outline=INK_SOFT, width=3,
        )
        plate.text((x0 + 63, 338), case, size=18, bold=True,
                   fill=INK_SOFT, anchor="mm")
        plate.text((x0 + 63, 369), "not checked", size=17,
                   fill=INK_SOFT, anchor="mm")
    plate.arrow((1348, 353), (1440, 353), fill=INK_SOFT, width=5, head=18)
    plate.text((1394, 389), "continues", size=17, bold=True,
               fill=INK_SOFT, anchor="mm")

    # A proof chain must cover an arbitrary input.  This induction proof is
    # fully specified, so the arrows communicate logical dependence rather
    # than decorative motion.
    plate.card((116, 500, 948, 852),
               fill=mix(PAPER_LIGHT, BLUE_LIGHT, 0.14), outline=BLUE)
    plate.text((532, 532), "ARBITRARY-CASE PROOF",
               size=23, bold=True, fill=BLUE, anchor="mm")
    plate.text((532, 565), "Claim:  1 + 3 + ... + (2n − 1) = n²  for every n ≥ 1",
               size=23, bold=True, math_face=True, fill=INK, anchor="mm")

    plate.card((145, 601, 328, 736), fill=PAPER_LIGHT, outline=INK)
    plate.text((236, 626), "BASE", size=18, bold=True, fill=BLUE, anchor="mm")
    plate.text((236, 672), "P(1)", size=25, bold=True,
               math_face=True, fill=INK, anchor="mm")
    plate.text((236, 707), "1 = 1²", size=22, bold=True,
               math_face=True, fill=INK, anchor="mm")

    plate.arrow((342, 668), (390, 668), fill=INK, width=6, head=18)
    plate.card((405, 588, 711, 750), fill=GOLD_LIGHT, outline=INK)
    plate.text((558, 613), "ARBITRARY k", size=18, bold=True,
               fill=GOLD, anchor="mm")
    plate.text((558, 643), "assume P(k)", size=19, bold=True,
               math_face=True, fill=INK, anchor="mm")
    plate.text((558, 672), "1 + ... + (2k − 1) = k²", size=18, bold=True,
               math_face=True, fill=INK, anchor="mm")
    plate.text((558, 701), "add the next odd number  2k + 1", size=17, bold=True,
               math_face=True, fill=INK, anchor="mm")
    plate.text((558, 730), "k² + (2k + 1) = (k + 1)²", size=19, bold=True,
               math_face=True, fill=INK, anchor="mm")

    plate.arrow((725, 668), (773, 668), fill=INK, width=6, head=18)
    plate.card((788, 601, 919, 736), fill=TEAL_LIGHT, outline=INK)
    plate.text((853, 626), "STEP", size=18, bold=True, fill=TEAL, anchor="mm")
    plate.text((853, 674), "P(k+1)", size=23, bold=True,
               math_face=True, fill=INK, anchor="mm")
    plate.text((853, 712), "follows", size=19, bold=True,
               fill=INK, anchor="mm")
    plate.draw.line((145, 780, 919, 780), fill=EDGE, width=3)
    plate.text((532, 818), "base + arbitrary step  ⇒  the claim holds for every n ≥ 1",
               size=21, bold=True, math_face=True, fill=BLUE, anchor="mm")

    # A single witnessed failure has the opposite logical asymmetry: unlike
    # evidence, it can settle a universal claim immediately.
    plate.card((974, 500, 1478, 852),
               fill=mix(PAPER_LIGHT, CORAL_LIGHT, 0.19), outline=CORAL)
    plate.text((1226, 532), "ONE COUNTEREXAMPLE",
               size=23, bold=True, fill=CORAL, anchor="mm")
    plate.text((1226, 572), "Return to the prime conjecture",
               size=20, bold=True, fill=INK, anchor="mm")
    plate.card((1020, 605, 1432, 725), fill=PAPER_LIGHT, outline=INK)
    plate.text((1226, 636), "n = 40",
               size=23, bold=True, math_face=True, fill=INK, anchor="mm")
    plate.text((1226, 674), "f(40) = 40² + 40 + 41",
               size=22, bold=True, math_face=True, fill=INK, anchor="mm")
    plate.text((1226, 707), "= 1681 = 41 × 41",
               size=23, bold=True, math_face=True, fill=CORAL, anchor="mm")
    _cross(plate, (1055, 775), 25, fill=INK, width=8)
    plate.text((1104, 760), "COMPOSITE",
               size=24, bold=True, fill=CORAL)
    plate.text((1104, 796), "so the universal claim is false",
               size=20, bold=True, fill=INK)
    plate.text((1226, 831), "One failure refutes 'every n'.",
               size=18, bold=True, fill=INK_SOFT, anchor="mm")


SPECS: dict[str, Spec] = {
    "math.4.linalg": {
        "id": "math.4.linalg",
        "title": "Linear Algebra",
        "stage": 4,
        "plate_id": "determinant-area-collapse-plate",
        "alt": "The same marked unit square remains a square under identity, shears into an equal-area parallelogram, and projects to a line as distinct vertices merge.",
        "caption": "Determinant tracks signed area scaling: identity and shear have determinant one, while projection has determinant zero, collapses area, and cannot be inverted.",
        "draw": _draw_linalg,
    },
    "math.4.diff-calc": {
        "id": "math.4.diff-calc",
        "title": "Differential Calculus",
        "stage": 4,
        "plate_id": "secant-tangent-plate",
        "alt": "A parabola shows secant lines through nearby points approaching a tangent, beside a corner with different one-sided slopes.",
        "caption": "A derivative is the limit of secant slopes when that limit exists. A minimum at a corner need not have derivative zero.",
        "draw": _draw_diff_calc,
    },
    "math.4.int-calc": {
        "id": "math.4.int-calc",
        "title": "Integral Calculus",
        "stage": 4,
        "plate_id": "signed-accumulation-plate",
        "alt": "A sign-changing curve has positive and negative shaded regions aligned with its accumulation function below.",
        "caption": "The definite integral accumulates signed change. The Fundamental Theorem links the accumulation function's slope to the original function.",
        "draw": _draw_int_calc,
    },
    "math.4.multivar": {
        "id": "math.4.multivar",
        "title": "Multivariable Calculus",
        "stage": 4,
        "plate_id": "surface-gradient-plate",
        "alt": "A saddle's contour map marks a point, its two coordinate slices, the gradient and a chosen direction.",
        "caption": "Partial derivatives are coordinate-slice slopes. The gradient packages them, and its dot product with a unit vector gives directional change.",
        "draw": _draw_multivar,
    },
    "math.4.diffeq": {
        "id": "math.4.diffeq",
        "title": "Differential Equations",
        "stage": 4,
        "plate_id": "logistic-direction-field-plate",
        "alt": "A logistic slope field shows solutions rising toward, staying on, or falling toward a carrying-capacity line.",
        "caption": "A differential equation assigns a local slope. An initial condition selects one solution, and equilibria organize its long-run behavior.",
        "draw": _draw_diffeq,
    },
    "math.4.discrete": {
        "id": "math.4.discrete",
        "title": "Discrete Mathematics",
        "stage": 4,
        "plate_id": "complete-graph-pairs-plate",
        "alt": "Five labeled vertices are joined by all ten possible edges, with a tally matching edges to unordered pairs.",
        "caption": "In a simple complete graph, each edge is one unordered pair. Summing degrees counts every edge twice.",
        "draw": _draw_discrete,
    },
    "math.4.numtheory": {
        "id": "math.4.numtheory",
        "title": "Number Theory",
        "stage": 4,
        "plate_id": "modular-power-cycle-plate",
        "alt": "A seven-position residue clock traces powers of two through the repeating cycle one, two, four, one.",
        "caption": "Congruence keeps only the remainder class. Repeated powers enter cycles, which make huge exponents manageable.",
        "draw": _draw_numtheory,
    },
    "math.4.analysis": {
        "id": "math.4.analysis",
        "title": "Real Analysis",
        "stage": 4,
        "plate_id": "epsilon-delta-band-plate",
        "alt": "Epsilon and delta bands around a line show every nearby input mapping into a required output band.",
        "caption": "The limit definition controls every punctured-neighborhood input, not just sampled points. Delta may depend on epsilon.",
        "draw": _draw_analysis,
    },
    "math.4.prob-theory": {
        "id": "math.4.prob-theory",
        "title": "Probability Theory",
        "stage": 4,
        "plate_id": "law-large-numbers-plate",
        "alt": "Three checkpoints compare a coin's running heads proportion with one half while the raw count difference still fluctuates.",
        "caption": "The law of large numbers concerns long-run proportions under stated assumptions. It does not force short runs to balance or counts to stay close.",
        "draw": _draw_prob_theory,
    },
    "math.5.abstract": {
        "id": "math.5.abstract",
        "title": "Abstract Algebra",
        "stage": 5,
        "plate_id": "finite-group-structure-plate",
        "alt": "Two four-element operation tables reveal different element orders in the cyclic and Klein four-groups.",
        "caption": "Groups can have the same number of elements yet different structure. Element orders distinguish the cyclic group C4 from the Klein four-group.",
        "draw": _draw_abstract,
    },
    "math.5.measure": {
        "id": "math.5.measure",
        "title": "Measure Theory",
        "stage": 5,
        "plate_id": "shrinking-cover-plate",
        "alt": "Shrinking open intervals cover an enumerated finite prefix of rational points while their total length stays below a chosen budget.",
        "caption": "A countable set can be dense yet have measure zero because covers can have arbitrarily small total length. The drawing shows only a finite prefix.",
        "draw": _draw_measure,
    },
    "math.5.topology": {
        "id": "math.5.topology",
        "title": "Topology",
        "stage": 5,
        "plate_id": "topological-invariants-plate",
        "alt": "A marked loop survives stretching of a gridded surface, while sphere, torus and double torus show increasing genus.",
        "caption": "Homeomorphisms preserve topological structure, not lengths or angles. Genus is one invariant, not a complete test in every setting.",
        "draw": _draw_topology,
    },
    "math.5.diffgeo": {
        "id": "math.5.diffgeo",
        "title": "Differential Geometry",
        "stage": 5,
        "plate_id": "intrinsic-curvature-plate",
        "alt": "A flat sheet and cylinder share zero Gaussian curvature, while sphere and saddle diagrams show positive and negative intrinsic curvature.",
        "caption": "Gaussian curvature is intrinsic: rolling without stretching preserves it, while internal distances and geodesic-angle behavior reveal curvature.",
        "draw": _draw_diffgeo,
    },
    "math.5.functional": {
        "id": "math.5.functional",
        "title": "Functional Analysis",
        "stage": 5,
        "plate_id": "unilateral-shift-plate",
        "alt": "An infinite sequence shifts one place right, preserving its norm but leaving some target sequences unreachable.",
        "caption": "The unilateral shift on square-summable sequences is an isometry but not onto, behavior impossible for a same-dimension finite linear map.",
        "draw": _draw_functional,
    },
    "math.5.complex-analysis": {
        "id": "math.5.complex-analysis",
        "title": "Complex Analysis",
        "stage": 5,
        "plate_id": "residue-contour-plate",
        "alt": "A solid directed contour encloses one pole while a dashed directed contour encloses both, linking enclosed residues to the contour integral.",
        "caption": "For a meromorphic function with no pole on the path, the contour integral is determined by enclosed residues and winding.",
        "draw": _draw_complex_analysis,
    },
    "math.5.logic": {
        "id": "math.5.logic",
        "title": "Logic and Set Theory",
        "stage": 5,
        "plate_id": "cantor-diagonal-plate",
        "alt": "A binary table highlights its diagonal and constructs a new sequence that differs from every listed row.",
        "caption": "Cantor's infinite diagonal construction defeats any proposed enumeration. This finite window illustrates the rule, not the proof by itself.",
        "draw": _draw_logic,
    },
    "math.5.numerical": {
        "id": "math.5.numerical",
        "title": "Numerical Analysis",
        "stage": 5,
        "plate_id": "root-methods-plate",
        "alt": "Newton's tangent step and bisection's shrinking bracket approach the square root of two on the same curve.",
        "caption": "Newton can converge rapidly near a simple root. Bisection is slower but preserves a valid continuous sign-changing bracket.",
        "draw": _draw_numerical,
    },
    "math.5.frontier": {
        "id": "math.5.frontier",
        "title": "The Frontier",
        "stage": 5,
        "plate_id": "evidence-proof-counterexample-plate",
        "alt": "A prime-valued conjecture is checked through n equals 39 and continues past a dashed bound, beside an arbitrary-case induction chain and the counterexample n equals 40.",
        "caption": "Finite computation can make a conjecture credible but cannot cover unbounded cases. A proof handles an arbitrary case; one counterexample refutes a universal statement.",
        "draw": _draw_frontier,
    },
}


_EXPECTED_IDS = {
    "math.4.linalg", "math.4.diff-calc", "math.4.int-calc", "math.4.multivar", "math.4.diffeq",
    "math.4.discrete", "math.4.numtheory", "math.4.analysis", "math.4.prob-theory",
    "math.5.abstract", "math.5.measure", "math.5.topology", "math.5.diffgeo",
    "math.5.functional", "math.5.complex-analysis", "math.5.logic", "math.5.numerical",
    "math.5.frontier",
}

validate_specs(SPECS, _EXPECTED_IDS)
