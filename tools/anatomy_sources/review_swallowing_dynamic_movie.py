#!/usr/bin/env python3
"""Inspect the original PMC9188511 movie without changing its encoded payload.

PNG decodes and contact sheets are review aids, not raw quantitative MR samples.
All decode files go to an explicitly supplied research directory. The small
provenance report and four review contact sheets go to the review directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from PIL import Image, ImageChops, ImageDraw, ImageStat

MOVIE = "10334_2021_973_MOESM2_ESM.mp4"
SOURCE_SHA256 = "c02a17b4ff007b6dafb73463e762e4f1e8cbd684ef8ce985a38b03c1f070fa27"
XML_SHA256 = "07df7d693144feb701c75d59810d5674f7b428854724f8ffdd2cf244d4c7ac00"


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def text(element: ET.Element | None) -> str:
    return " ".join(" ".join(element.itertext()).split()) if element is not None else ""


def validate_report(report: dict) -> None:
    """Reject timing/identity/coverage inflation independently of decoding."""
    assert report["source"]["sha256"] == SOURCE_SHA256
    assert report["source"]["publisher_media_MD5"] == "fa90605121a6318faa2c31892c1756f1"
    assert report["source"]["publisher_media_MD5_verified"]
    stream = report["encoded_stream"]
    assert (stream["width"], stream["height"], stream["frames"]) == (1233, 1084, 64)
    assert stream["time_base"] == "1/12346"
    assert stream["r_frame_rate"] == stream["avg_frame_rate"] == "6173/500"
    records = report["frames"]
    assert len(records) == 64
    for i, record in enumerate(records):
        assert record["ordinal"] == i + 1 and record["presentation_timestamp_ticks"] == i * 1000
        assert record["presentation_timestamp_fraction_seconds"] == str(Fraction(i * 1000, 12346))
        for key in ("PNG_sha256", "decoded_RGB_sha256"):
            assert len(record[key]) == 64 and set(record[key]) <= set("0123456789abcdef")
    assert len({r["decoded_RGB_sha256"] for r in records}) == 64
    assert report["source_numbering"]["main_figure_ids"] == ["Fig1", "Fig2", "Fig3", "Fig4"]
    assert report["source_numbering"]["supplement_caption_refers_to_Figure_6"]
    assert report["source_numbering"]["main_text_Online_Resource_2_refers_to_Figure_4"]
    assert report["source_numbering"]["numbering_discrepancy_retained"]
    limits = report["limits"]
    for key in ("independent_12_fps_sampling_verified", "MRI_movie_is_VFSS",
                "raw_MRI_arrays_or_patient_affine_available", "individual_age_or_sex_verified",
                "exact_physiological_phase_boundaries_verified", "normal_function_certified",
                "aspiration_absence_established", "native_3D_model_approved",
                "anatomical_leaf_coverage_approved"):
        assert limits[key] is False, key
    assert report["source_cohort"]["volunteers"] == 5
    for key in ("individual_movie_subject_ID", "individual_movie_age_years", "individual_movie_sex"):
        assert report["source_cohort"][key] is None, key
    assert report["source_acquisition"]["volunteer_slices"] == 7
    assert report["source_acquisition"]["pitch_mm_AP_FH_RL"] == [2, 2, 6]
    assert report["source_acquisition"]["sliding_window_reconstruction_doubles_nominal_rate"]
    assert report["source_acquisition"]["flat_field_filter"]
    assert report["source_acquisition"]["temporal_regularisation"]
    assert report["source_acquisition"]["phantom_21_slices_is_volunteer_movie"] is False


def review(source: Path, output: Path, decodes: Path, ffmpeg: str, ffprobe: str) -> dict:
    movie, xml = source / MOVIE, source / "PMC9188511.1.xml"
    metadata = json.loads((source / "PMC9188511.1.json").read_text())
    movie_sha, xml_sha = digest(movie), digest(xml)
    assert movie_sha == SOURCE_SHA256 and xml_sha == XML_SHA256
    source_url = next(u for u in metadata["media_urls"] if urlsplit(u).path.endswith("/" + MOVIE))
    publisher_md5 = parse_qs(urlsplit(source_url).query)["md5"][0]
    assert digest(movie, "md5") == publisher_md5
    root = ET.fromstring(xml.read_bytes())
    authors = [text(a.find("name/given-names")) + " " + text(a.find("name/surname"))
               for a in root.findall(".//contrib[@contrib-type='author']")]
    license_links = [text(e) for e in root.findall(".//license/*") if e.tag.endswith("license_ref")]
    assert "https://creativecommons.org/licenses/by/4.0/" in license_links
    assert metadata["license_code"] == "CC BY" and not metadata["is_retracted"]
    probe = json.loads(subprocess.check_output([
        ffprobe, "-v", "error", "-show_streams", "-show_format", "-show_frames",
        "-show_entries", "frame=best_effort_timestamp,best_effort_timestamp_time,key_frame,pict_type,width,height",
        "-of", "json", str(movie)], text=True))
    video = probe["streams"]
    assert len(video) == 1 and video[0]["codec_type"] == "video"
    stream = video[0]
    assert stream["codec_name"] == "mpeg4" and stream["pix_fmt"] == "yuv420p"
    pts = probe["frames"]
    assert len(pts) == 64 and int(stream["duration_ts"]) == 64000
    decodes.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(movie),
                    "-fps_mode", "passthrough", "-frames:v", "64", str(decodes / "frame-%03d.png")], check=True)
    records, images, previous = [], [], None
    for ordinal, timing in enumerate(pts, 1):
        path = decodes / f"frame-{ordinal:03d}.png"
        with Image.open(path) as decoded:
            assert decoded.size == (1233, 1084) and decoded.mode == "RGB"
            rgb = decoded.copy()
        delta = None if previous is None else sum(ImageStat.Stat(ImageChops.difference(rgb, previous)).mean) / 3
        records.append({"ordinal": ordinal,
                        "presentation_timestamp_ticks": int(timing["best_effort_timestamp"]),
                        "presentation_timestamp_fraction_seconds": str(Fraction(int(timing["best_effort_timestamp"]), 12346)),
                        "presentation_timestamp_seconds_rounded": timing["best_effort_timestamp_time"],
                        "key_frame": bool(timing["key_frame"]), "pict_type": timing["pict_type"],
                        "PNG_sha256": digest(path), "decoded_RGB_sha256": hashlib.sha256(rgb.tobytes()).hexdigest(),
                        "adjacent_full_frame_mean_absolute_RGB_display_difference": delta})
        images.append(rgb)
        previous = rgb
    sheets = []
    for group in range(4):
        sheet = Image.new("RGB", (1600, 1520), "#eeeeee")
        draw = ImageDraw.Draw(sheet)
        for local, rgb in enumerate(images[group * 16:(group + 1) * 16]):
            ordinal = group * 16 + local + 1
            thumbnail = rgb.copy()
            thumbnail.thumbnail((400, 350), Image.Resampling.NEAREST)
            x, y = (local % 4) * 400, (local // 4) * 380
            sheet.paste(thumbnail, (x, y + 24))
            draw.text((x + 5, y + 5), f"Frame {ordinal:02d} / {records[ordinal - 1]['presentation_timestamp_seconds_rounded']} s", fill="black")
        name = f"all-frames-{group + 1}.png"
        sheet.save(output / name)
        sheets.append({"file": name, "sha256": digest(output / name), "ordinals": [group * 16 + 1, (group + 1) * 16],
                       "review_preview_only": True, "resampling": "nearest-neighbour thumbnail; original full frame retained"})
    report = {
        "schema_version": 1, "pmcid": "PMC9188511", "doi": metadata["doi"],
        "source": {"file": MOVIE, "bytes": movie.stat().st_size, "sha256": movie_sha,
                   "publisher_media_URL": source_url, "publisher_media_MD5": publisher_md5,
                   "publisher_media_MD5_verified": True, "source_XML_sha256": xml_sha,
                   "authors": authors, "license": "CC BY 4.0", "license_URL": license_links[0],
                   "article_URL": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9188511/"},
        "encoded_stream": {"codec": stream["codec_name"], "pixel_format": stream["pix_fmt"],
                           "width": stream["width"], "height": stream["height"], "frames": len(pts),
                           "r_frame_rate": stream["r_frame_rate"], "avg_frame_rate": stream["avg_frame_rate"],
                           "time_base": stream["time_base"], "duration_ticks": int(stream["duration_ts"]),
                           "duration_fraction_seconds": str(Fraction(int(stream["duration_ts"]), 12346)),
                           "duration_seconds_rounded": stream["duration"], "audio_stream_present": False},
        "source_numbering": {"main_figure_ids": [f.attrib["id"] for f in root.findall(".//fig")],
                             "main_text_Online_Resource_2_refers_to_Figure_4": "Fig4" in ET.tostring(root.find(".//*[@id='Par26']"), encoding="unicode"),
                             "supplement_caption_refers_to_Figure_6": "figure 6" in text(root.find(".//*[@id='MOESM2']")),
                             "numbering_discrepancy_retained": True},
        "source_cohort": {"volunteers": 5, "healthy_adults_author_report": True,
                          "female_count": 1, "age_range_years": [26, 29], "mean_age_years": 28,
                          "individual_movie_subject_ID": None, "individual_movie_age_years": None,
                          "individual_movie_sex": None},
        "source_acquisition": {"field_strength_T": 3, "pitch_mm_AP_FH_RL": [2, 2, 6],
                               "volunteer_slices": 7, "phantom_21_slices_is_volunteer_movie": False,
                               "base_nominal_reconstruction_rate_fps": 6.2,
                               "sliding_window_reconstruction_doubles_nominal_rate": True,
                               "half_frame_shift_combination": True, "flat_field_filter": True,
                               "temporal_regularisation": True, "oral_agent": "20 mL pineapple juice",
                               "position": "supine", "coil": "custom 12-channel flexible surface coil"},
        "decoded_display": {"tool": subprocess.check_output([ffmpeg, "-version"], text=True).splitlines()[0],
                            "RGB_decodes_are_raw_MRI_intensities": False,
                            "additional_crop_resize_enhancement_in_frame_decodes": False,
                            "encoded_colour_space_metadata_present": "color_space" in stream,
                            "contact_sheets_are_review_thumbnails": True},
        "limits": {"independent_12_fps_sampling_verified": False, "MRI_movie_is_VFSS": False,
                   "raw_MRI_arrays_or_patient_affine_available": False, "individual_age_or_sex_verified": False,
                   "exact_physiological_phase_boundaries_verified": False, "normal_function_certified": False,
                   "aspiration_absence_established": False, "native_3D_model_approved": False,
                   "anatomical_leaf_coverage_approved": False},
        "frames": records, "contact_sheets": sheets,
    }
    validate_report(report)
    (output / "original-movie-review.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("decodes", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    result = review(args.source, args.output, args.decodes, args.ffmpeg, args.ffprobe)
    print(f"Verified {len(result['frames'])} original movie display frames; physiology/native anatomy remains unapproved.")
