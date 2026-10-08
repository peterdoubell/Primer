"""Actual container bytes determine motion metadata; unsupported cases fail closed."""
import json
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

from primer.source_motion_contract import parse_motion_contract, parse_mp4_contract, parse_webm_contract

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "web/reference-media/radiology-motion"
ORIGINAL = MEDIA / "swallowing-pmc9188511-mri-montage-original.mp4"
TRANSPORT = MEDIA / "swallowing-pmc9188511-mri-montage-lossless.webm"


def box(kind, payload):
    return struct.pack(">I4s", len(payload) + 8, kind) + payload


def full(kind, payload, version=0, flags=0):
    return box(kind, bytes([version]) + flags.to_bytes(3, "big") + payload)


def table(kind, rows, fmt, version=0):
    return full(kind, struct.pack(">I", len(rows)) + b"".join(struct.pack(fmt, *row) for row in rows), version)


def fixture_mp4(ctts=None, ctts_version=1, extra_track=False, edit=None, version=0):
    ftyp = box(b"ftyp", b"isom\x00\x00\x00\x00")
    mdat = box(b"mdat", b"abcd")
    matrix = struct.pack(">9i", 65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824)
    track_header = bytearray(84 if version == 0 else 96)
    matrix_offset = 40 if version == 0 else 52
    track_header[0] = version
    track_header[1:4] = (3).to_bytes(3, "big")
    track_header[matrix_offset:matrix_offset + 36] = matrix
    struct.pack_into(">II", track_header, matrix_offset + 36, 40 << 16, 30 << 16)
    scale_offset = 12 if version == 0 else 20
    media_header = bytearray(24 if version == 0 else 36)
    media_header[0] = version
    struct.pack_into(">I", media_header, scale_offset, 1000)
    struct.pack_into(">I" if version == 0 else ">Q", media_header, scale_offset + 4, 4000)
    sample = bytearray(78)
    struct.pack_into(">H", sample, 6, 1)
    struct.pack_into(">HH", sample, 24, 40, 30)
    samples = [
        full(b"stsd", struct.pack(">I", 1) + box(b"mp4v", bytes(sample))),
        table(b"stts", [(4, 1000)], ">II"),
        full(b"stsz", struct.pack(">II4I", 0, 4, 1, 1, 1, 1)),
        table(b"stsc", [(1, 4, 1)], ">III"),
        table(b"stco", [(len(ftyp) + 8,)], ">I"),
    ]
    if ctts is not None:
        samples.append(table(b"ctts", [(1, offset) for offset in ctts], ">Ii" if ctts_version else ">II", ctts_version))
    reference = full(b"dref", struct.pack(">I", 1) + full(b"url ", b"", flags=1))
    minf = box(b"minf", box(b"dinf", reference) + box(b"stbl", b"".join(samples)))
    media = box(b"mdia", box(b"mdhd", bytes(media_header)) + full(b"hdlr", b"\x00" * 4 + b"vide" + b"\x00" * 12) + minf)
    edts = b"" if edit is None else box(b"edts", table(b"elst", [edit], ">Iihh"))
    trak = box(b"trak", box(b"tkhd", bytes(track_header)) + edts + media)
    movie_header = bytearray(24)
    struct.pack_into(">II", movie_header, 12, 1000, 4000)
    return ftyp + mdat + box(b"moov", box(b"mvhd", bytes(movie_header)) + trak + (trak if extra_track else b""))


def ebml(key, payload):
    key_bytes = key.to_bytes((key.bit_length() + 7) // 8, "big")
    width = next(width for width in range(1, 9) if len(payload) < (1 << (7 * width)) - 1)
    size = ((1 << (7 * width)) | len(payload)).to_bytes(width, "big")
    return key_bytes + size + payload


def uint(key, value):
    return ebml(key, value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big"))


def fixture_webm(flags=0x80, duplicate_track=False, duplicate_pts=False,
                 group=False, offset_cluster=False, unknown_size=False,
                 track_extra=b"", visual_extra=b""):
    header = ebml(0x1A45DFA3, ebml(0x4282, b"webm"))
    info = ebml(0x1549A966, uint(0x2AD7B1, 1_000_000))
    visual = ebml(0xE0, uint(0xB0, 40) + uint(0xBA, 30) + visual_extra)
    track = ebml(0xAE, uint(0xD7, 1) + uint(0x83, 1) + ebml(0x86, b"V_VP9") + visual + track_extra)
    tracks = ebml(0x1654AE6B, track + (track if duplicate_track else b""))
    def block(time):
        payload = b"\x81" + struct.pack(">hB", time, flags) + b"frame"
        return ebml(0xA0, ebml(0xA1, payload)) if group else ebml(0xA3, payload)
    cluster = ebml(0x1F43B675, uint(0xE7, 0) + block(0) + block(0 if duplicate_pts else 81) + (b"" if offset_cluster else block(162)))
    if offset_cluster:
        cluster += ebml(0x1F43B675, uint(0xE7, 200) + block(-38))
    payload = info + tracks + cluster
    return header + (b"\x18\x53\x80\x67\xff" + payload if unknown_size else ebml(0x18538067, payload))


@pytest.mark.parametrize("path,key", [(ORIGINAL, "source_pts_seconds"), (TRANSPORT, "transport_pts_seconds")])
def test_actual_movie_contract_matches_all_reviewed_dimensions_frames_and_times(path, key):
    reference = json.loads((ROOT / "data/radiology/source-motion-references.json").read_text())["ra.swallowing"][0]
    contract = parse_motion_contract(path)
    assert {name: contract[name] for name in ("width", "height", "frames")} == {"width": 1233, "height": 1084, "frames": 64}
    assert contract["pts_seconds"] == reference[key]


@pytest.mark.parametrize("version", [0, 1])
def test_mp4_full_box_versions_and_unit_rate_no_offset_edit(version):
    assert parse_mp4_contract(fixture_mp4(version=version, edit=(4000, 0, 1, 0))) == {
        "width": 40, "height": 30, "frames": 4, "pts_seconds": [0.0, 1.0, 2.0, 3.0]}


def test_signed_composition_offsets_reorder_presentation_not_decode_times():
    contract = parse_mp4_contract(fixture_mp4(ctts=[1000, -1000, 1000, -1000]))
    assert contract["pts_seconds"] == [0.0, 1.0, 2.0, 3.0]
    assert parse_mp4_contract(fixture_mp4(ctts=[0, 0, 0, 0], ctts_version=0))["frames"] == 4


@pytest.mark.parametrize("offsets", [[-1000, 0, 0, 0], [0, -1000, 0, 0], [0, 0, 0, 1000], [0, 0]])
def test_unpresentable_or_ambiguous_composition_times_fail(offsets):
    with pytest.raises(ValueError):
        parse_mp4_contract(fixture_mp4(ctts=offsets))


@pytest.mark.parametrize("edit", [(3000, 0, 1, 0), (4000, 1000, 1, 0), (4000, -1, 1, 0), (4000, 0, 2, 0)])
def test_trim_offset_empty_or_non_unit_edit_is_not_guessed(edit):
    with pytest.raises(ValueError, match="edits"):
        parse_mp4_contract(fixture_mp4(edit=edit))


def test_second_mp4_track_is_rejected():
    with pytest.raises(ValueError, match="repeated"):
        parse_mp4_contract(fixture_mp4(extra_track=True))


@pytest.mark.parametrize("mutation", ["top_size", "stts_count", "stts_delta", "sample_size", "chunk_offset", "width"])
def test_changed_mp4_tables_or_media_extents_cannot_supply_fake_contract(mutation):
    data = bytearray(fixture_mp4())
    if mutation == "top_size":
        struct.pack_into(">I", data, 0, len(data) + 1)
    elif mutation == "stts_count":
        struct.pack_into(">I", data, data.index(b"stts") + 12, 5)
    elif mutation == "stts_delta":
        struct.pack_into(">I", data, data.index(b"stts") + 16, 2000)
    elif mutation == "sample_size":
        struct.pack_into(">I", data, data.index(b"stsz") + 16, 500)
    elif mutation == "chunk_offset":
        struct.pack_into(">I", data, data.index(b"stco") + 12, len(data))
    elif mutation == "width":
        struct.pack_into(">I", data, data.index(b"tkhd") + 4 + 76, 41 << 16)
    with pytest.raises(ValueError):
        parse_mp4_contract(data)


@pytest.mark.parametrize("path", [ORIGINAL, TRANSPORT])
@pytest.mark.parametrize("cut", [1, 7, 25])
def test_truncation_of_actual_container_is_rejected(path, cut):
    with pytest.raises(ValueError):
        parse_motion_contract(path.read_bytes()[:-cut])


@pytest.mark.parametrize("group,offset_cluster", [(False, False), (True, False), (False, True), (True, True)])
def test_simple_blocks_groups_and_signed_cluster_relative_times(group, offset_cluster):
    assert parse_webm_contract(fixture_webm(group=group, offset_cluster=offset_cluster)) == {
        "width": 40, "height": 30, "frames": 3, "pts_seconds": [0.0, 0.081, 0.162]}


@pytest.mark.parametrize("kwargs", [
    {"flags": 0x82}, {"flags": 0x84}, {"flags": 0x86}, {"flags": 0x88},
    {"duplicate_track": True}, {"duplicate_pts": True}, {"unknown_size": True},
    {"track_extra": uint(0x56AA, 1)}, {"track_extra": ebml(0x23314F, struct.pack(">d", 2.0))},
    {"visual_extra": uint(0x54B0, 80)}, {"visual_extra": uint(0x54AA, 1)},
])
def test_ambiguous_laced_delayed_scaled_or_cropped_webm_is_rejected(kwargs):
    with pytest.raises(ValueError):
        parse_webm_contract(fixture_webm(**kwargs))


def test_webm_invalid_declared_size_is_not_read_outside_parent():
    data = bytearray(fixture_webm())
    index = data.index(b"\xb0")
    data[index + 1] = 0xFE  # Claim 126 bytes inside a much smaller video element.
    with pytest.raises(ValueError, match="size"):
        parse_webm_contract(data)


@pytest.mark.parametrize("path", [ORIGINAL, TRANSPORT])
def test_independent_ffprobe_matches_actual_container_contract_when_available(path):
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        pytest.skip("Independent ffprobe is unavailable; production parser has no subprocess dependency")
    output = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_frames", "-show_streams",
        "-show_entries", "stream=width,height:frame=pts_time", "-of", "json", str(path)], check=True, capture_output=True, text=True, timeout=20)
    probe = json.loads(output.stdout)
    contract = parse_motion_contract(path)
    assert len(probe["streams"]) == 1
    assert (contract["width"], contract["height"]) == (probe["streams"][0]["width"], probe["streams"][0]["height"])
    assert contract["frames"] == len(probe["frames"])
    assert contract["pts_seconds"] == pytest.approx([float(frame["pts_time"]) for frame in probe["frames"]], abs=0.00000051)


@pytest.mark.parametrize("data", [b"", b"not a movie", b"\x1a\x45\xdf\xa3\x00", b"\x00\x00\x00\x01ftyp"])
def test_empty_unknown_and_truncated_signatures_fail_closed(data):
    with pytest.raises(ValueError):
        parse_motion_contract(data)
