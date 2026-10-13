# Thoracic ultrasound source candidate

This review library adds 16 intact published figure groups and six browser-playable clinical cine clips for all five reporting steps of `ra.thoracic-ultrasound`. It is not a completed module, clinical approval, or evidence of complete anatomical coverage.

Serve this directory over localhost and open `index.html`. Still images and provenance are checked in. The six large WebM derivatives are intentionally excluded from Git; prepare them from the retained acquisition folder before reviewing cine:

```sh
python tools/prepare_thoracic_ultrasound_review.py --source .research/thoracic-ultrasound-20261013
python -m http.server 8767 --bind 127.0.0.1 --directory docs/thoracic-ultrasound-source-review-20261013
```

The preparation tool fails on missing or mismatched media and never silently downloads a replacement. `manifest.json` identifies every source, author, license, checksum, case limitation and unresolved gap. Original published panel groups remain unchanged. Source JPEG resolution limits are retained; enlargement adds no detail. Clinical measurements belong to the source cases.

`evidence/motion-verification.json` records all 1,630 decoded YUV frame hashes and original/derived presentation times. VP9 derivatives preserve every decoded plane; WebM timestamp quantization is below 0.5 ms. This does not prove original acquisition frame timing or RGB display colorimetry. The frame slider requests an exported timestamp: browser seeking is explicitly approximate.

Source attribution appears with every selected item. PMC5401877 states CC BY without a version in its deposited license paragraph; the manifest preserves that distinction. Third-party permission assets from PMC11460009 and noncommercial media from PMC9356263 are excluded. Full cine/privacy review and specialist review remain pending. No clinical diagnosis, current-patient measurement, segmentation, or cross-case 3D registration is inferred from these examples.

Next integration work must map reviewed structures to original pixels, preserve the existing assessment state and acquisition limitations, provide missing dynamic bronchogram and complex pleural-fluid examples, and supply faithful schematics/3D with their own provenance. The five-step inventory in `requirements.json` distinguishes anatomical parts from artifacts and conditional observations.

Original JATS evidence is stored as deterministic gzip; the manifest JATS checksum refers to decompressed original bytes. This preserves publisher whitespace unchanged.
