"""Bounded container contracts for the reviewed, single-video teaching movies.

These readers derive dimensions, sample count and presentation timestamps from
actual container bytes. They do not decode pixels, approve anatomical labels or
measure physiological events. Unsupported tracks, edits, lacing and encryption
fail closed rather than being interpreted approximately.
"""
import math
import struct
from pathlib import Path

MAX_BYTES = 256 * 1024 * 1024
MAX_FRAMES = 1_000_000
MAX_ELEMENTS = 1_000_000


def _bytes(source):
    if isinstance(source, (bytes, bytearray, memoryview)):
        if len(source) > MAX_BYTES:
            raise ValueError("Motion container exceeds byte bound")
        data = bytes(source)
    else:
        path = Path(source)
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("Motion container exceeds byte bound")
        data = path.read_bytes()
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Motion container is empty or exceeds byte bound")
    return data


def _one(elements, key, required=True):
    matches = [element for element in elements if element[0] == key]
    if len(matches) != 1:
        if not matches and not required:
            return None
        raise ValueError("Missing or repeated container element " + repr(key))
    return matches[0]


def _boxes(data, start, end):
    """Return type/payload-start/end triples; never search byte strings as boxes."""
    result = []
    while start < end:
        if end - start < 8 or len(result) >= MAX_ELEMENTS:
            raise ValueError("Truncated or excessive ISO-BMFF boxes")
        size, kind = struct.unpack_from(">I4s", data, start)
        header = 8
        if size == 1:
            if end - start < 16:
                raise ValueError("Truncated ISO-BMFF extended size")
            size = struct.unpack_from(">Q", data, start + 8)[0]
            header = 16
        elif size == 0:
            size = end - start
        if size < header or size > end - start:
            raise ValueError("Invalid ISO-BMFF box size")
        result.append((kind, start + header, start + size))
        start += size
    return result


def _full(data, box, versions=(0,)):
    payload = data[box[1]:box[2]]
    if len(payload) < 4 or payload[0] not in versions:
        raise ValueError("Unsupported or truncated full box " + repr(box[0]))
    return payload, payload[0], int.from_bytes(payload[1:4], "big")


def _media_header(data, box):
    payload, version, _ = _full(data, box, (0, 1))
    offset = 12 if version == 0 else 20
    width = 4 if version == 0 else 8
    if len(payload) < offset + 4 + width:
        raise ValueError("Truncated movie/media header")
    scale = struct.unpack_from(">I", payload, offset)[0]
    duration = int.from_bytes(payload[offset + 4:offset + 4 + width], "big")
    if not scale or not duration or duration == (1 << (8 * width)) - 1:
        raise ValueError("Invalid movie/media timescale or duration")
    return scale, duration


def _table(data, box, record_size, versions=(0,)):
    payload, version, flags = _full(data, box, versions)
    if flags or len(payload) < 8:
        raise ValueError("Invalid table flags/header")
    count = struct.unpack_from(">I", payload, 4)[0]
    if count < 1 or count > MAX_FRAMES or len(payload) != 8 + count * record_size:
        raise ValueError("Invalid table count or byte size")
    return payload, count, version


def parse_mp4_contract(source):
    data = _bytes(source)
    top = _boxes(data, 0, len(data))
    _one(top, b"ftyp")
    if any(box[0] in {b"moof", b"mfra"} for box in top):
        raise ValueError("Fragmented movies are unsupported")
    mdat = [(box[1], box[2]) for box in top if box[0] == b"mdat"]
    if not mdat:
        raise ValueError("Movie has no media payload")
    moov = _one(top, b"moov")
    movie = _boxes(data, moov[1], moov[2])
    if any(box[0] == b"mvex" for box in movie):
        raise ValueError("Fragmented movie declarations are unsupported")
    movie_scale, _ = _media_header(data, _one(movie, b"mvhd"))
    # Reject even a second audio/hint track rather than guessing timeline scope.
    trak = _one(movie, b"trak")
    track = _boxes(data, trak[1], trak[2])
    tkhd = _one(track, b"tkhd")
    payload, version, flags = _full(data, tkhd, (0, 1))
    matrix_offset = 40 if version == 0 else 52
    if not flags & 1 or len(payload) != matrix_offset + 44:
        raise ValueError("Disabled or invalid visual track header")
    if struct.unpack_from(">9i", payload, matrix_offset) != (65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824):
        raise ValueError("Rotated or transformed visual tracks are unsupported")
    fixed_width, fixed_height = struct.unpack_from(">II", payload, matrix_offset + 36)
    if fixed_width & 65535 or fixed_height & 65535:
        raise ValueError("Fractional track display dimensions are unsupported")
    dimensions = fixed_width >> 16, fixed_height >> 16
    if min(dimensions) < 1:
        raise ValueError("Invalid visual track dimensions")
    mdia = _one(track, b"mdia")
    media = _boxes(data, mdia[1], mdia[2])
    scale, duration = _media_header(data, _one(media, b"mdhd"))
    hdlr, _, _ = _full(data, _one(media, b"hdlr"))
    if len(hdlr) < 12 or hdlr[8:12] != b"vide":
        raise ValueError("Movie must contain a single visual track")
    minf = _one(media, b"minf")
    media_info = _boxes(data, minf[1], minf[2])
    dinf = _one(media_info, b"dinf")
    dref = _one(_boxes(data, dinf[1], dinf[2]), b"dref")
    refs, _, ref_flags = _full(data, dref)
    if ref_flags or len(refs) < 8 or struct.unpack_from(">I", refs, 4)[0] != 1:
        raise ValueError("Ambiguous media data references")
    reference = _one(_boxes(data, dref[1] + 8, dref[2]), b"url ")
    url_payload, _, url_flags = _full(data, reference)
    if url_flags != 1 or len(url_payload) != 4:
        raise ValueError("External media data references are unsupported")
    stbl = _one(media_info, b"stbl")
    samples = _boxes(data, stbl[1], stbl[2])
    stsd = _one(samples, b"stsd")
    description, _, description_flags = _full(data, stsd)
    if description_flags or len(description) < 8 or struct.unpack_from(">I", description, 4)[0] != 1:
        raise ValueError("Ambiguous visual sample descriptions")
    entries = _boxes(data, stsd[1] + 8, stsd[2])
    if len(entries) != 1 or entries[0][0] not in {b"mp4v", b"avc1", b"avc3", b"hvc1", b"hev1", b"vp09", b"av01"}:
        raise ValueError("Unsupported visual sample description")
    sample = data[entries[0][1]:entries[0][2]]
    if len(sample) < 78 or struct.unpack_from(">H", sample, 6)[0] != 1:
        raise ValueError("Truncated or external visual sample description")
    if struct.unpack_from(">HH", sample, 24) != dimensions:
        raise ValueError("Encoded and displayed visual dimensions differ")
    stsz, _, stsz_flags = _full(data, _one(samples, b"stsz"))
    if stsz_flags or len(stsz) < 12:
        raise ValueError("Invalid sample size header")
    fixed_size, count = struct.unpack_from(">II", stsz, 4)
    if count < 1 or count > MAX_FRAMES or len(stsz) != 12 + (0 if fixed_size else count * 4):
        raise ValueError("Invalid sample size/count table")
    sizes = [fixed_size] * count if fixed_size else list(struct.unpack_from(">" + str(count) + "I", stsz, 12))
    if min(sizes) < 1:
        raise ValueError("Empty media samples are unsupported")
    stts, records, _ = _table(data, _one(samples, b"stts"), 8)
    decode_times, tick = [], 0
    for offset in range(8, 8 + records * 8, 8):
        run, delta = struct.unpack_from(">II", stts, offset)
        if not run or not delta or len(decode_times) + run > count:
            raise ValueError("Invalid decoding-time run/count")
        decode_times.extend(tick + index * delta for index in range(run))
        tick += run * delta
    if len(decode_times) != count or tick != duration:
        raise ValueError("Sample timing/count differs from media duration")
    composition = _one(samples, b"ctts", required=False)
    offsets = [0] * count
    if composition is not None:
        ctts, records, composition_version = _table(data, composition, 8, (0, 1))
        offsets = []
        for offset in range(8, 8 + records * 8, 8):
            run = struct.unpack_from(">I", ctts, offset)[0]
            value = struct.unpack_from(">i" if composition_version else ">I", ctts, offset + 4)[0]
            if not run or len(offsets) + run > count:
                raise ValueError("Invalid composition-time run/count")
            offsets.extend([value] * run)
        if len(offsets) != count:
            raise ValueError("Composition-time sample count differs")
    pts = sorted(a + b for a, b in zip(decode_times, offsets))
    if pts[0] < 0 or pts[-1] >= duration or any(a >= b for a, b in zip(pts, pts[1:])):
        raise ValueError("Negative or ambiguous presentation timestamps")
    edits = _one(track, b"edts", required=False)
    if edits is not None:
        edit_box = _one(_boxes(data, edits[1], edits[2]), b"elst")
        _, edit_version, _ = _full(data, edit_box, (0, 1))
        elst, records, _ = _table(data, edit_box, 12 if edit_version == 0 else 20, (0, 1))
        if records != 1:
            raise ValueError("Complex movie edit lists are unsupported")
        edit_duration = int.from_bytes(elst[8:12 if edit_version == 0 else 16], "big")
        media_start_offset = 12 if edit_version == 0 else 16
        media_start_width = 4 if edit_version == 0 else 8
        media_start = int.from_bytes(elst[media_start_offset:media_start_offset + media_start_width], "big", signed=True)
        rate = struct.unpack_from(">hh", elst, media_start_offset + media_start_width)
        if media_start != 0 or rate != (1, 0) or abs(edit_duration * scale - duration * movie_scale) > scale:
            raise ValueError("Offset, trimmed or non-unit-rate movie edits are unsupported")
    chunk_table = [box for box in samples if box[0] in {b"stco", b"co64"}]
    if len(chunk_table) != 1:
        raise ValueError("Missing or ambiguous chunk-offset table")
    chunk_width = 4 if chunk_table[0][0] == b"stco" else 8
    chunks, chunk_count, _ = _table(data, chunk_table[0], chunk_width)
    positions = [int.from_bytes(chunks[offset:offset + chunk_width], "big") for offset in range(8, len(chunks), chunk_width)]
    stsc, runs, _ = _table(data, _one(samples, b"stsc"), 12)
    maps = [struct.unpack_from(">III", stsc, offset) for offset in range(8, len(stsc), 12)]
    if maps[0][0] != 1 or any(a[0] >= b[0] for a, b in zip(maps, maps[1:])) or any(first > chunk_count or per_chunk < 1 or desc != 1 for first, per_chunk, desc in maps):
        raise ValueError("Invalid chunk-to-sample mapping")
    consumed, run_index, ranges = 0, 0, []
    for index, position in enumerate(positions, 1):
        if run_index + 1 < runs and index == maps[run_index + 1][0]:
            run_index += 1
        run_count = maps[run_index][1]
        if consumed + run_count > count:
            raise ValueError("Chunk mapping exceeds sample count")
        end = position + sum(sizes[consumed:consumed + run_count])
        if not any(begin <= position < end <= stop for begin, stop in mdat):
            raise ValueError("Media samples leave actual mdat payload")
        ranges.append((position, end))
        consumed += run_count
    if consumed != count or any(a[1] > b[0] for a, b in zip(sorted(ranges), sorted(ranges)[1:])):
        raise ValueError("Missing or overlapping media chunks")
    sync = _one(samples, b"stss", required=False)
    if sync is not None:
        table, _, _ = _table(data, sync, 4)
        indices = list(struct.unpack_from(">" + str((len(table) - 8) // 4) + "I", table, 8))
        if indices[0] < 1 or indices[-1] > count or any(a >= b for a, b in zip(indices, indices[1:])):
            raise ValueError("Invalid sync sample indices")
    return {"width": dimensions[0], "height": dimensions[1], "frames": count, "pts_seconds": [time / scale for time in pts]}


def _vint(data, position, end, identifier=False):
    if position >= end or data[position] == 0:
        raise ValueError("Truncated or invalid EBML variable integer")
    width = 1
    while not data[position] & (1 << (8 - width)):
        width += 1
    if width > (4 if identifier else 8) or position + width > end:
        raise ValueError("Invalid EBML integer width")
    value = int.from_bytes(data[position:position + width], "big")
    if not identifier:
        value &= (1 << (7 * width)) - 1
        if value == (1 << (7 * width)) - 1:
            raise ValueError("Unknown EBML sizes/track numbers are unsupported")
    return value, width


def _elements(data, start, end):
    result = []
    while start < end:
        if len(result) >= MAX_ELEMENTS:
            raise ValueError("Excessive EBML element count")
        key, key_width = _vint(data, start, end, True)
        size, size_width = _vint(data, start + key_width, end)
        payload = start + key_width + size_width
        if size > end - payload:
            raise ValueError("EBML element exceeds parent/container size")
        result.append((key, payload, payload + size))
        start = payload + size
    return result


def _uint(data, element):
    if not 1 <= element[2] - element[1] <= 8:
        raise ValueError("Invalid EBML unsigned integer size")
    return int.from_bytes(data[element[1]:element[2]], "big")


def _optional_uint(data, elements, key, default):
    element = _one(elements, key, False)
    return default if element is None else _uint(data, element)


def parse_webm_contract(source):
    data = _bytes(source)
    top = _elements(data, 0, len(data))
    header = _one(top, 0x1A45DFA3)
    declaration = _elements(data, header[1], header[2])
    doc_type = _one(declaration, 0x4282)
    if data[doc_type[1]:doc_type[2]] != b"webm":
        raise ValueError("Movie is not declared WebM")
    if _optional_uint(data, declaration, 0x42F2, 4) > 4 or _optional_uint(data, declaration, 0x42F3, 8) > 8:
        raise ValueError("Unsupported EBML identifier/size bounds")
    segment = _one(top, 0x18538067)
    elements = _elements(data, segment[1], segment[2])
    info = _one(elements, 0x1549A966)
    time_scale = _optional_uint(data, _elements(data, info[1], info[2]), 0x2AD7B1, 1_000_000)
    if time_scale < 1:
        raise ValueError("Invalid WebM timestamp scale")
    tracks = _one(elements, 0x1654AE6B)
    track_entries = _elements(data, tracks[1], tracks[2])
    entry = _one(track_entries, 0xAE)
    track = _elements(data, entry[1], entry[2])
    track_number = _uint(data, _one(track, 0xD7))
    if track_number < 1 or _uint(data, _one(track, 0x83)) != 1 or _optional_uint(data, track, 0xB9, 1) != 1:
        raise ValueError("WebM must contain one enabled video track")
    codec = _one(track, 0x86)
    if data[codec[1]:codec[2]] not in {b"V_VP8", b"V_VP9", b"V_AV1"}:
        raise ValueError("Unsupported WebM video codec")
    if _one(track, 0x6D80, False) is not None or _optional_uint(data, track, 0x56AA, 0) != 0 or _optional_uint(data, track, 0x537F, 0) != 0:
        raise ValueError("Encrypted, delayed or offset video tracks are unsupported")
    scale_element = _one(track, 0x23314F, False)
    if scale_element is not None:
        raw = data[scale_element[1]:scale_element[2]]
        if len(raw) not in (4, 8) or struct.unpack(">f" if len(raw) == 4 else ">d", raw)[0] != 1:
            raise ValueError("Non-unit WebM track timestamp scale is unsupported")
    video = _one(track, 0xE0)
    visual = _elements(data, video[1], video[2])
    width, height = _uint(data, _one(visual, 0xB0)), _uint(data, _one(visual, 0xBA))
    if not 1 <= width <= 65535 or not 1 <= height <= 65535:
        raise ValueError("Invalid WebM video dimensions")
    if any(_optional_uint(data, visual, key, 0) != 0 for key in (0x54AA, 0x54BB, 0x54CC, 0x54DD, 0x54B2)) or _optional_uint(data, visual, 0x54B0, width) != width or _optional_uint(data, visual, 0x54BA, height) != height:
        raise ValueError("Cropped or scaled WebM video is unsupported")
    pts = []
    clusters = [element for element in elements if element[0] == 0x1F43B675]
    if not clusters:
        raise ValueError("WebM has no source frame clusters")
    for cluster in clusters:
        contents = _elements(data, cluster[1], cluster[2])
        cluster_time = _uint(data, _one(contents, 0xE7))
        if any(element[0] == 0xAF for element in contents):
            raise ValueError("Encrypted WebM blocks are unsupported")
        for element in contents:
            if element[0] == 0xA0:
                element = _one(_elements(data, element[1], element[2]), 0xA1)
            elif element[0] != 0xA3:
                continue
            number, number_width = _vint(data, element[1], element[2])
            payload = element[1] + number_width
            if number != track_number or element[2] - payload < 4:
                raise ValueError("Unknown track or truncated/empty WebM block")
            relative, flags = struct.unpack_from(">hB", data, payload)
            if flags & 0x0E:
                raise ValueError("Laced or invisible WebM blocks are unsupported")
            timestamp = (cluster_time + relative) * time_scale
            if timestamp < 0 or len(pts) >= MAX_FRAMES:
                raise ValueError("Negative timestamp or excessive WebM frame count")
            pts.append(timestamp)
    pts.sort()
    if not pts or any(a >= b for a, b in zip(pts, pts[1:])):
        raise ValueError("Empty or ambiguous WebM presentation timestamps")
    seconds = [time / 1_000_000_000 for time in pts]
    if any(not math.isfinite(time) for time in seconds):
        raise ValueError("Non-finite WebM presentation timestamps")
    return {"width": width, "height": height, "frames": len(pts), "pts_seconds": seconds}


def parse_motion_contract(source):
    """Dispatch using the actual container signature, not its filename suffix."""
    data = _bytes(source)
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return parse_webm_contract(data)
    if len(data) >= 8 and data[4:8] == b"ftyp":
        return parse_mp4_contract(data)
    raise ValueError("Unsupported motion container signature")
