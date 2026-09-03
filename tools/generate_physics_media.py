#!/usr/bin/env python3
"""Render, integrate, and verify complete explanatory media for physics.

The 36 new plates are deterministic scientific diagrams.  Their paired model
entries all bind to the lesson-specific ``physics-concept-lab`` scenario whose
identifier is the curriculum node identifier.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from physics_illustrations.core import (
    HEIGHT,
    STAGE_DIRS,
    WIDTH,
    Spec,
    asset_paths,
    illustration_entry,
    render_spec,
    validate_specs,
)


ROOT = Path(__file__).resolve().parents[1]
CURRICULUM_PATH = ROOT / "data" / "curriculum" / "03-physics.json"
OUTPUT_ROOT = ROOT / "web" / "illustrations"
PREEXISTING_COMPLETE_IDS = {
    "phys.0.light-shadow",
    "phys.1.light",
    "phys.4.fluids",
}


MODEL_META: Dict[str, Tuple[str, str]] = {
    "phys.0.push-pull": ("Force Balance Lab", "Change the rightward push, compare it with the fixed 4 N leftward push, and watch the net force change."),
    "phys.0.hot-cold": ("Thermal Contact Lab", "Advance contact time and follow the two temperatures toward thermal equilibrium."),
    "phys.0.float-sink": ("Float or Sink Lab", "Reshape a fixed mass by changing displaced volume, then compare weight and buoyancy."),
    "phys.1.motion": ("Motion and Friction Lab", "Change surface friction after the same launch, then compare the position curve."),
    "phys.1.machines": ("Simple Machine Lab", "Change the machine geometry to trade force for distance or direction."),
    "phys.1.magnets": ("Magnetic Field Lab", "Rotate the second magnet to inspect how pole orientation changes the interaction."),
    "phys.1.sound": ("Sound Wave Lab", "Change frequency and amplitude independently to connect pitch and loudness to the wave."),
    "phys.1.energy": ("Energy Transfer Lab", "Move through the transfer and track every unit among gravitational, kinetic, and thermal stores."),
    "phys.2.forces": ("Net Force Lab", "Change applied force and friction to connect the net force to acceleration."),
    "phys.2.gravity": ("Mass and Weight Lab", "Change mass and gravitational field strength to see weight respond through W = mg."),
    "phys.2.electricity": ("Circuit Relationship Lab", "Open the circuit or change voltage and resistance to see current respond."),
    "phys.2.heat": ("Heat Transfer Lab", "Select a transfer mechanism and vary the temperature gap without treating unlike rates as one ranking."),
    "phys.2.waves": ("Wave Relationship Lab", "Change frequency and amplitude while the model preserves the wave-speed constraint."),
    "phys.2.matter": ("Particle State Lab", "Change temperature and inspect particle arrangements and coexistence at the phase boundaries."),
    "phys.2.units": ("Measurement Lab", "Change instrument resolution and repeat count to inspect precision and uncertainty."),
    "phys.3.mechanics": ("Force and Motion Lab", "Change force and mass to test Newton's second law and its limiting cases."),
    "phys.3.energy-work": ("Collision Ledger Lab", "Change collision elasticity and compare momentum conservation with kinetic-energy accounting."),
    "phys.3.em": ("Induction Coil Lab", "Move, stop, or reverse the magnet to test how changing flux induces voltage."),
    "phys.3.optics-waves": ("Interference Bench", "Change path difference and wave amplitude to move between constructive and destructive interference."),
    "phys.3.thermo": ("Heat Engine Budget", "Change reservoir temperatures and compare the engine with the Carnot efficiency bound."),
    "phys.3.nuclear": ("Radioactive Ensemble Lab", "Track the expected ensemble fraction while distinguishing it from unpredictable individual decay times."),
    "phys.3.relativity-intro": ("Light Clock Lab", "Change relative speed to connect invariant light speed with time dilation."),
    "phys.3.modern": ("Photoelectric Bench", "Change frequency and photon arrival rate independently to test threshold energy and emission count."),
    "phys.4.classical": ("Hamiltonian Motion Lab", "Change the trial path and inspect action alongside the phase-space trajectory."),
    "phys.4.em-maxwell": ("Electromagnetic Wave Lab", "Change frequency while wavelength adjusts to preserve electromagnetic wave speed."),
    "phys.4.quantum": ("Quantum Sampling Lab", "Choose a state and draw a reproducible seeded mock sample from its predicted probability distribution."),
    "phys.4.statmech": ("Microstate Counter", "Choose the number of heads and compare macrostate multiplicity with entropy."),
    "phys.4.relativity": ("Relativistic Frame Lab", "Change frame speed and proper time to compare coordinate time and simultaneity."),
    "phys.4.solid-state": ("Band and Carrier Lab", "Change band gap, temperature, and doping to inspect the carrier population."),
    "phys.4.particles": ("Decay Conservation Lab", "Choose a candidate decay channel and audit its conserved quantum numbers."),
    "phys.4.experiment": ("Measurement Error Lab", "Change scatter, calibration offset, and outliers to inspect residuals and uncertainty."),
    "phys.5.qft": ("Field Mode Lab", "Change one free bosonic mode's occupation number and frequency, then inspect its quantized energy ladder."),
    "phys.5.gr-cosmo": ("Expanding Universe Lab", "Change the observation epoch's scale factor to connect expansion with redshift."),
    "phys.5.condensed": ("Meissner Transition Lab", "Vary temperature and applied field around a lead-like type-I phase boundary, then inspect whether the Meissner state persists."),
    "phys.5.quantum-info": ("Quantum Correlation Lab", "Change detector-angle difference and pair count to compare local randomness with joint correlations."),
    "phys.5.frontier": ("Evidence Comparison Lab", "Change model assumptions and compare their rotation-curve predictions with evidence."),
}


def load_curriculum() -> Dict[str, object]:
    with CURRICULUM_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def all_specs() -> Dict[str, Spec]:
    from physics_illustrations.advanced import SPECS as advanced
    from physics_illustrations.early import SPECS as early
    from physics_illustrations.middle import SPECS as middle

    specs: Dict[str, Spec] = {}
    for cohort in (early, middle, advanced):
        overlap = set(specs).intersection(cohort)
        if overlap:
            raise ValueError("Duplicate physics cohort specs: {}".format(sorted(overlap)))
        specs.update(cohort)
    return specs


def validate_inventory(curriculum: Dict[str, object], specs: Dict[str, Spec]) -> None:
    nodes = curriculum["nodes"]
    physics_ids = {node["id"] for node in nodes}
    expected = physics_ids - PREEXISTING_COMPLETE_IDS
    validate_specs(specs, expected)
    if set(MODEL_META) != expected:
        raise ValueError("Physics model metadata does not match the missing cohort")
    for node in nodes:
        node_id = node["id"]
        if node_id in specs:
            item = specs[node_id]
            if item["title"] != node["title"] or item["stage"] != node["stage"]:
                raise ValueError("Spec metadata drift for {}".format(node_id))


def model_entry(node_id: str) -> Dict[str, object]:
    title, instructions = MODEL_META[node_id]
    return {
        "id": node_id.replace(".", "-") + "-concept-lab",
        "kind": "model",
        "renderer": "physics-concept-lab",
        "title": title,
        "instructions": instructions,
        "props": {"scenario": node_id},
    }


def render_assets(specs: Dict[str, Spec], overwrite: bool) -> List[Path]:
    if not overwrite:
        collisions = [path for item in specs.values() for path in asset_paths(OUTPUT_ROOT, item)
                      if path.exists()]
        if collisions:
            raise FileExistsError(
                "Refusing to overwrite {} existing outputs; first paths: {}".format(
                    len(collisions), collisions[:5]))
    outputs: List[Path] = []
    for item in specs.values():
        outputs.extend(render_spec(OUTPUT_ROOT, item, overwrite=overwrite))
    return outputs


def sync_curriculum(curriculum: Dict[str, object], specs: Dict[str, Spec]) -> Tuple[int, int]:
    illustrations_added = 0
    models_added = 0
    for node in curriculum["nodes"]:
        node_id = node["id"]
        if node_id not in specs:
            continue
        media = node.setdefault("lesson_media", [])
        illustrations = [item for item in media if item.get("kind") == "illustration"]
        models = [item for item in media if item.get("kind") == "model"]
        expected_illustration = illustration_entry(specs[node_id])
        expected_model = model_entry(node_id)
        if illustrations and illustrations != [expected_illustration]:
            raise ValueError("Refusing to replace authored illustration for {}".format(node_id))
        if models and models != [expected_model]:
            raise ValueError("Refusing to replace authored model for {}".format(node_id))
        if not illustrations:
            media.insert(0, expected_illustration)
            illustrations_added += 1
        if not models:
            media.append(expected_model)
            models_added += 1
    if illustrations_added or models_added:
        with CURRICULUM_PATH.open("w", encoding="utf-8") as handle:
            json.dump(curriculum, handle, indent=1, ensure_ascii=False)
            handle.write("\n")
    return illustrations_added, models_added


def verify(curriculum: Dict[str, object], specs: Dict[str, Spec]) -> None:
    nodes = curriculum["nodes"]
    if len(nodes) != 39:
        raise ValueError("Expected 39 physics lessons, found {}".format(len(nodes)))
    seen_urls = set()
    seen_media_ids = set()
    for node in nodes:
        node_id = node["id"]
        media = node.get("lesson_media", [])
        if [item.get("kind") for item in media] != ["illustration", "model"]:
            raise ValueError("{} does not have exactly illustration then model".format(node_id))
        illustration, model = media
        if illustration["id"] in seen_media_ids or model["id"] in seen_media_ids:
            raise ValueError("Duplicate physics media id at {}".format(node_id))
        seen_media_ids.update((illustration["id"], model["id"]))
        if (illustration["width"], illustration["height"]) != (WIDTH, HEIGHT):
            raise ValueError("Bad declared dimensions for {}".format(node_id))
        if illustration["alt"] == illustration["caption"]:
            raise ValueError("Alt and caption must differ for {}".format(node_id))
        if min(len(illustration[key].split()) for key in ("alt", "caption")) < 8:
            raise ValueError("Alt and caption must explain the relationship for {}".format(node_id))
        candidates = illustration["srcset"].split(",")
        candidate_urls = set()
        for candidate in candidates:
            url, descriptor = candidate.strip().split()
            if url in seen_urls:
                raise ValueError("Raster URL reused by {}".format(node_id))
            seen_urls.add(url)
            candidate_urls.add(url)
            path = ROOT / "web" / url.removeprefix("/app/")
            if not path.is_file():
                raise FileNotFoundError(path)
            with Image.open(path) as opened:
                width, height = opened.size
                if opened.format != "WEBP" or width != int(descriptor[:-1]):
                    raise ValueError("Bad raster format or width for {}".format(path))
                if width * HEIGHT != height * WIDTH:
                    raise ValueError("Bad raster aspect ratio for {}".format(path))
            if path.stat().st_size >= 300_000:
                raise ValueError("Oversize physics illustration {}".format(path))
        if len(candidate_urls) != 2 or illustration["src"] not in candidate_urls:
            raise ValueError("{} needs two responsive sources and a valid fallback".format(node_id))
        if node_id in specs and model != model_entry(node_id):
            raise ValueError("Model metadata drift for {}".format(node_id))
    if len(seen_urls) != 78:
        raise ValueError("Expected 78 unique physics rasters, found {}".format(len(seen_urls)))


def write_contact_sheet(curriculum: Dict[str, object], destination: Path) -> None:
    thumb_w, thumb_h = 320, 200
    columns = 5
    label_h = 38
    rows = (len(curriculum["nodes"]) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "#efe7d2")
    draw = ImageDraw.Draw(sheet)
    font_path = ("/System/Library/Fonts/Supplemental/Arial.ttf"
                 if os.path.isfile("/System/Library/Fonts/Supplemental/Arial.ttf")
                 else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    face = ImageFont.truetype(font_path, 18)
    for index, node in enumerate(curriculum["nodes"]):
        illustration = node["lesson_media"][0]
        source = ROOT / "web" / illustration["src"].removeprefix("/app/")
        with Image.open(source) as opened:
            thumb = ImageOps.fit(opened.convert("RGB"), (thumb_w, thumb_h),
                                 method=Image.Resampling.LANCZOS)
        x = index % columns * thumb_w
        y = index // columns * (thumb_h + label_h)
        sheet.paste(thumb, (x, y))
        draw.text((x + 8, y + thumb_h + 8), node["id"], font=face, fill="#24303a")
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--sync-curriculum", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--contact-sheet", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    curriculum = load_curriculum()
    specs = all_specs()
    validate_inventory(curriculum, specs)
    if args.render:
        outputs = render_assets(specs, args.overwrite)
        print("Rendered {} physics illustration files".format(len(outputs)))
    if args.sync_curriculum:
        additions = sync_curriculum(curriculum, specs)
        print("Added {} illustrations and {} models".format(*additions))
        curriculum = load_curriculum()
    if args.check:
        verify(curriculum, specs)
        print("Verified 39 physics media pairs and 78 responsive rasters")
    if args.contact_sheet:
        write_contact_sheet(curriculum, args.contact_sheet)
        print("Wrote {}".format(args.contact_sheet))
    if not any((args.render, args.sync_curriculum, args.check, args.contact_sheet)):
        print("{} new specs cover {} total physics lessons".format(
            len(specs), len(curriculum["nodes"])))


if __name__ == "__main__":
    main()
