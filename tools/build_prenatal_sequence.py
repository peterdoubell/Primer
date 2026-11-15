#!/usr/bin/env python3
"""Build WebP stills and a captioned GIF from an approved prenatal POV manifest.

This is an asset encoder, not an image generator. The input is a JSON object with
``frames`` containing ``developmentalDay``, an absolute ``source`` PNG path,
``label``, ``ageLabel``, and ``caption`` for every stage. Artwork is uniformly
resized and never cropped. Captions use developmental day and pregnancy age only.

Requires Pillow with WebP support and ffmpeg (for temporally stable ordered GIF
dithering). Run only after the selected-frame manifest has been approved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Iterator

from PIL import GifImagePlugin, Image, ImageDraw, ImageFont, ImageOps, features


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DAYS = list(range(5, 22)) + [
    24, 28, 31, 35, 38, 42, 45, 49, 52, 56, 59, 63, 66, 70, 73, 77, 80, 83,
]
GIF_SIZE = (800, 800)
ART_SIZE = (740, 740)
STILL_SIZE = (1024, 1024)
TWEEN_COUNT = 3
TWEEN_MS = 70
HOLD_MS = 1000
END_HOLD_MS = 2000
BACKGROUND = (184, 156, 148)
FOOTER = (226, 210, 203)
INK = (69, 48, 46)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def pixel_hash(image: Image.Image) -> str:
    return hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()


def read_manifest(path: Path) -> tuple[dict, list[dict]]:
    document = json.loads(path.read_text())
    frames = document.get('frames')
    if not isinstance(frames, list):
        raise ValueError('Manifest must contain a frames array.')
    days = [frame.get('developmentalDay') for frame in frames]
    if days != EXPECTED_DAYS:
        raise ValueError(f'Expected exactly these 35 stages, in order: {EXPECTED_DAYS}')
    for frame in frames:
        for key in ('source', 'label', 'ageLabel', 'caption'):
            if not isinstance(frame.get(key), str) or not frame[key].strip():
                raise ValueError(f'Day {frame["developmentalDay"]}: missing {key}.')
        source = Path(frame['source'])
        if not source.is_absolute() or not source.is_file():
            raise ValueError(f'Source must be an existing absolute path: {source}')
        with Image.open(source) as image:
            if image.format != 'PNG':
                raise ValueError(f'Expected a selected source PNG: {source}')
            image.verify()
    return document, frames


def font(size: int, override: Path | None) -> ImageFont.FreeTypeFont:
    candidates = [override] if override else [
        Path('/System/Library/Fonts/HelveticaNeue.ttc'),
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        Path('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'),
    ]
    for path in candidates:
        if path and path.is_file():
            return ImageFont.truetype(str(path), size)
    raise RuntimeError('No suitable caption font found; provide --font.')


def fit(image: Image.Image, size: tuple[int, int], background=BACKGROUND) -> Image.Image:
    canvas = Image.new('RGB', size, background)
    resized = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
    canvas.paste(resized, ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2))
    return canvas


def compose(image: Image.Image, stage: dict, title_font, age_font) -> Image.Image:
    canvas = Image.new('RGB', GIF_SIZE, BACKGROUND)
    canvas.paste(fit(image, ART_SIZE), ((GIF_SIZE[0] - ART_SIZE[0]) // 2, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, ART_SIZE[1], 799, 799), fill=FOOTER)
    title = f'Day {stage["developmentalDay"]}'
    age = f'Pregnancy age · {stage["ageLabel"]}'
    if draw.textlength(age, font=age_font) > 740:
        raise ValueError(f'Pregnancy-age caption is too long on {title}: {age}')
    draw.text((400, 745), title, font=title_font, fill=INK, anchor='mt')
    draw.text((400, 775), age, font=age_font, fill=INK, anchor='mt')
    return canvas


def animation_frames(keyframes: list[Image.Image]) -> Iterator[Image.Image]:
    for index, keyframe in enumerate(keyframes):
        yield keyframe
        if index + 1 < len(keyframes):
            for tween in range(1, TWEEN_COUNT + 1):
                yield Image.blend(keyframe, keyframes[index + 1], tween / (TWEEN_COUNT + 1))


def animation_entries(stages: list[dict]) -> list[dict]:
    entries = []
    for index, stage in enumerate(stages):
        entries.append({
            'type': 'keyframe', 'developmentalDay': stage['developmentalDay'],
            'durationMs': END_HOLD_MS if index in (0, len(stages) - 1) else HOLD_MS,
        })
        if index + 1 < len(stages):
            for tween in range(1, TWEEN_COUNT + 1):
                entries.append({
                    'type': 'crossfade', 'fromDay': stage['developmentalDay'],
                    'toDay': stages[index + 1]['developmentalDay'],
                    'fraction': tween / (TWEEN_COUNT + 1), 'durationMs': TWEEN_MS,
                })
    for index, entry in enumerate(entries):
        entry['frameIndex'] = index
    return entries


def shared_palette(keyframes: list[Image.Image]) -> Image.Image:
    count = len(keyframes) + (len(keyframes) - 1) * TWEEN_COUNT
    samples = Image.new('RGB', (128 * 14, 128 * ((count + 13) // 14)), FOOTER)
    for index, frame in enumerate(animation_frames(keyframes)):
        samples.paste(frame.resize((128, 128), Image.Resampling.LANCZOS),
                      (index % 14 * 128, index // 14 * 128))
    palette = samples.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    swatch = Image.new('P', (16, 16))
    swatch.putpalette(palette.getpalette())
    swatch.putdata(list(range(256)))
    return swatch


def ordered_quantize(keyframes: list[Image.Image], palette: Image.Image,
                     temp: Path, ffmpeg: str, count: int) -> list[Image.Image]:
    palette_path = temp / 'palette.png'
    palette.save(palette_path)
    encoded = temp / 'ordered-colour-frames.gif'
    command = [
        ffmpeg, '-hide_banner', '-loglevel', 'error', '-y',
        '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '800x800',
        '-framerate', '100', '-i', 'pipe:0', '-i', str(palette_path),
        '-lavfi', 'paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle',
        '-fps_mode', 'passthrough', '-loop', '0', str(encoded),
    ]
    with (temp / 'ffmpeg.log').open('wb') as stderr:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=stderr)
        try:
            assert process.stdin is not None
            for frame in animation_frames(keyframes):
                process.stdin.write(frame.tobytes())
            process.stdin.close()
            exit_code = process.wait()
        except BaseException:
            if process.stdin:
                process.stdin.close()
            process.kill()
            process.wait()
            raise
    if exit_code:
        raise RuntimeError(f'ffmpeg failed: {(temp / "ffmpeg.log").read_text()}')
    quantized = []
    # Keep ffmpeg's exact palette indices. Re-quantizing decoded RGB with Pillow
    # can slightly change colours because its palette lookup is approximate.
    previous_strategy = GifImagePlugin.LOADING_STRATEGY
    GifImagePlugin.LOADING_STRATEGY = GifImagePlugin.LoadingStrategy.RGB_AFTER_DIFFERENT_PALETTE_ONLY
    try:
        with Image.open(encoded) as gif:
            if gif.n_frames != count:
                raise RuntimeError(f'Quantizer returned {gif.n_frames} frames; expected {count}.')
            common_palette = gif.getpalette()
            for index in range(count):
                gif.seek(index)
                if gif.mode != 'P' or gif.getpalette() != common_palette:
                    raise RuntimeError(f'Quantizer changed the shared palette at frame {index}.')
                indexed = gif.copy()
                indexed.info.clear()
                quantized.append(indexed)
    finally:
        GifImagePlugin.LOADING_STRATEGY = previous_strategy
    return quantized


def verify_gif(path: Path, quantized: list[Image.Image], entries: list[dict]) -> dict:
    with Image.open(path) as gif:
        assert gif.size == GIF_SIZE
        assert gif.n_frames == 137 == len(entries) == len(quantized)
        assert gif.info.get('loop') == 0
        for index, (expected, entry) in enumerate(zip(quantized, entries)):
            gif.seek(index)
            assert gif.info['duration'] == entry['durationMs']
            digest = pixel_hash(gif)
            assert digest == pixel_hash(expected), f'Decoded frame {index} changed or reordered.'
            entry['decodedPixelSha256'] = digest
    key_entries = [entry for entry in entries if entry['type'] == 'keyframe']
    assert [entry['developmentalDay'] for entry in key_entries] == EXPECTED_DAYS
    assert entries[0]['developmentalDay'] == 5 and entries[-1]['developmentalDay'] == 83
    assert all(entry['frameIndex'] == index * 4 for index, entry in enumerate(key_entries))
    return {
        'frameCount': len(entries), 'keyframeCount': len(key_entries),
        'tweenCount': len(entries) - len(key_entries), 'dimensions': list(GIF_SIZE),
        'loop': 0, 'durationMs': sum(entry['durationMs'] for entry in entries),
        'decodedFramesMatchExpected': True, 'allStagesInManifestOrder': True,
        'firstDay': 5, 'lastDay': 83,
    }


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f'.{destination.name}.', dir=destination.parent,
                                     delete=False) as stream:
        pending = Path(stream.name)
        try:
            with source.open('rb') as original:
                shutil.copyfileobj(original, stream)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            pending.unlink(missing_ok=True)
            raise
    pending.replace(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=PROJECT_ROOT / 'output/imagegen/embryo-pov-series/selected-frames.json')
    parser.add_argument('--web-dir', type=Path, default=PROJECT_ROOT / 'web/reference-media/prenatal-development')
    parser.add_argument('--gif-copy', type=Path, default=PROJECT_ROOT / 'output/imagegen/embryo-first-trimester-pov.gif')
    parser.add_argument('--metadata', type=Path, default=PROJECT_ROOT / 'output/imagegen/embryo-first-trimester-pov.metadata.json')
    parser.add_argument('--font', type=Path)
    parser.add_argument('--ffmpeg', default=shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg')
    parser.add_argument('--validate-only', action='store_true', help='Validate selected sources without creating output.')
    args = parser.parse_args()
    _, stages = read_manifest(args.manifest)
    if args.validate_only:
        print(f'Valid: {len(stages)} ordered PNG sources; Day 5 through Day 83.')
        return
    if not features.check('webp'):
        raise RuntimeError('This Pillow installation does not support WebP.')
    if not shutil.which(args.ffmpeg):
        raise RuntimeError(f'ffmpeg is unavailable: {args.ffmpeg}')
    title_font, age_font = font(22, args.font), font(17, args.font)
    args.gif_copy.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='prenatal-encode-', dir=args.gif_copy.parent) as name:
        temp = Path(name)
        keyframes, source_logs = [], []
        for stage in stages:
            source = Path(stage['source'])
            with Image.open(source) as loaded:
                image = ImageOps.exif_transpose(loaded).convert('RGB')
            webp = temp / f'day-{stage["developmentalDay"]:03d}.webp'
            fit(image, STILL_SIZE).save(webp, format='WEBP', quality=94, method=6)
            with Image.open(webp) as still:
                assert still.size == STILL_SIZE and still.format == 'WEBP'
                still.load()
            keyframes.append(compose(image, stage, title_font, age_font))
            source_logs.append({
                'developmentalDay': stage['developmentalDay'], 'source': str(source),
                'sourceSha256': sha256_file(source), 'sourceDimensions': list(image.size),
                'label': stage['label'], 'ageLabel': stage['ageLabel'],
                'webp': str(args.web_dir / webp.name), 'webpSha256': sha256_file(webp),
                'webpBytes': webp.stat().st_size,
            })
        # Publish the independently verified stills before the longer GIF pass,
        # so gallery verification can run while the animation is encoding.
        for log in source_logs:
            atomic_copy(temp / Path(log['webp']).name, Path(log['webp']))
        print(f'WEBPS_READY: {len(source_logs)} verified 1024x1024 stills in {args.web_dir}', flush=True)
        entries = animation_entries(stages)
        palette = shared_palette(keyframes)
        quantized = ordered_quantize(keyframes, palette, temp, args.ffmpeg, len(entries))
        gif = temp / 'prenatal-development.gif'
        quantized[0].save(gif, save_all=True, append_images=quantized[1:], loop=0,
                          duration=[entry['durationMs'] for entry in entries], disposal=1,
                          optimize=True, palette=quantized[0].getpalette())
        verification = verify_gif(gif, quantized, entries)
        report = {
            'manifest': str(args.manifest.resolve()), 'manifestSha256': sha256_file(args.manifest),
            'gif': str(args.web_dir / gif.name), 'gifCopy': str(args.gif_copy),
            'gifBytes': gif.stat().st_size, 'gifSha256': sha256_file(gif),
            'verification': verification,
            'contentNote': 'Illustrative development; generated stages are not observations or predictions of an individual pregnancy.',
            'encoding': {
                'artTreatment': 'Full source artwork fitted uniformly, never cropped; crossfades only.',
                'webp': '1024x1024; quality 94; method 6',
                'gif': '800x800; 740x740 artwork with 60px bottom caption strip; no personal dates',
                'palette': 'One shared 256-colour median-cut palette; ordered Bayer dither scale 4',
                'compression': 'Lossless inter-frame transparency and rectangle optimization',
                'transitions': '3 crossfade frames per gap at 25%, 50%, 75%; 70ms each',
                'keyframes': '1000ms holds; first and last 2000ms; infinite loop',
            },
            'sources': source_logs, 'frames': entries,
        }
        report_path = temp / 'metadata.json'
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        # Publish the animation only after every decoded GIF frame is verified.
        atomic_copy(gif, args.web_dir / gif.name)
        atomic_copy(gif, args.gif_copy)
        atomic_copy(report_path, args.metadata)
        assert sha256_file(args.gif_copy) == sha256_file(args.web_dir / gif.name)
        print(json.dumps({
            'gif': report['gif'], 'copy': report['gifCopy'], 'metadata': str(args.metadata),
            'bytes': report['gifBytes'], **verification,
        }, indent=2))


if __name__ == '__main__':
    main()
