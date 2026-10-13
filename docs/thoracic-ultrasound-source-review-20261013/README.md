# Thoracic ultrasound source candidate

This review library adds 16 intact published figure groups and six browser-playable clinical cine clips for all five reporting steps of `ra.thoracic-ultrasound`. It is not a completed module, clinical approval, or evidence of complete anatomical coverage.

Serve this directory over localhost and open `index.html`. Still images and provenance are checked in. The six large WebM derivatives are intentionally excluded from Git; prepare them from the retained acquisition folder before reviewing cine:

```sh
python tools/prepare_thoracic_ultrasound_review.py --source .research/thoracic-ultrasound-20261013
python -m http.server 8767 --bind 127.0.0.1 --directory docs/thoracic-ultrasound-source-review-20261013
```

The preparation tool fails on missing or mismatched media and never silently downloads a replacement. `manifest.json` identifies every source, author, license, checksum, case limitation and unresolved gap. Original published panel groups remain unchanged. Source JPEG resolution limits are retained; enlargement adds no detail. Clinical measurements belong to the source cases.

`evidence/motion-verification.json` records all 1,630 decoded YUV frame hashes and original/derived presentation times. VP9 derivatives preserve every decoded plane; WebM timestamp quantization is below 0.5 ms. This does not prove original acquisition frame timing or RGB display colorimetry. The frame slider requests an exported timestamp: browser seeking is explicitly approximate.

Source attribution appears with every selected item. PMC5401877 states CC BY without a version in its deposited license paragraph; its publisher copyright hyperlink was subsequently verified to target CC BY 4.0 (see the retained link evidence). Third-party permission assets from PMC11460009 and noncommercial media from PMC9356263 are excluded. Full cine/privacy review and specialist review remain pending. No clinical diagnosis, current-patient measurement, segmentation, or cross-case 3D registration is inferred from these examples.

Next integration work must map reviewed structures to original pixels, preserve the existing assessment state and acquisition limitations, provide missing dynamic bronchogram and complex pleural-fluid examples, and supply faithful schematics/3D with their own provenance. The five-step inventory in `requirements.json` distinguishes anatomical parts from artifacts and conditional observations.

Original JATS evidence is stored as deterministic gzip; the manifest JATS checksum refers to decompressed original bytes. This preserves publisher whitespace unchanged.

## Module integration

All 16 original figure groups are registered as reference images in `ra.thoracic-ultrasound` and assigned to its five reporting steps. Unreviewed legacy fallback imagery is suppressed for this investigation. Normal-result shortcuts are removed; reporting templates require assessment adequacy and preserve not-assessed choices. Figure 13 keeps its illustrative panel separate from its two Doppler panels. Existing generic 3D orientation is not credited as anatomical coverage. All six cine clips are now delivered as separate source references with links to unchanged original files. Their transport contract explicitly verifies YUV samples and does not claim RGB display equivalence. Sampled temporal/overlay review is retained; full frame-by-frame clinical review remains pending.

Authenticated local reader checks exercised all five steps at 1440 and 390 pixels, loaded all 16 images at each width, and compared all delivered image bodies with their packaged original bytes. No browser exceptions were observed. Full CI, production delivery, structure-specific annotations, and clinical validation remain outstanding.

## Cine delivery verification

The six original containers and lossless VP9 derivatives are included in runtime assets. All 1,630 original and derivative frames were decoded again and compared with SHA-256 hashes of their YUV samples. Original and transport timestamps are parsed from container bytes, independently of the earlier FFprobe export. QuickTime embedded JPEG and MP42 AVI support is bounded to self-contained media, matching dimensions, one video track and a verified sample index. External references and unsupported codecs are rejected.

Three cardiac source exports repeat recorded content; scanner clock resets are disclosed. Four originals omit color range, while their browser transports declare limited range: no display colorimetry equivalence is claimed. Both distinctions are visible with the clips. Playback uses presented-frame timestamps where supported; clock-based fallback is labeled approximate. Authenticated browser checks covered six clips, two widths and both callback modes (24 cases), including playback and first/middle/last seeking.

The exact motion UI inverse preserves the earlier pulmonary UI audit without accepting unrelated app changes. Complete clinical assessment, anatomical correspondence, schematic/3D coverage and production release remain outstanding.
