# Original thoracic anatomy source review

Twelve original BodyParts3D 4.3 objects provide 649,480 retained faces: the diaphragm, three intercostal muscle layers and their producer-marked M variants, and five mitral/tricuspid valve leaflets. This is a source review package for `ra.thoracic-ultrasound`, not complete reporting anatomy or clinical approval.

Run from the repository root:

```sh
python -m http.server 8771 --bind 127.0.0.1 --directory docs/thoracic-native-anatomy-review-20261013
```

Open `http://127.0.0.1:8771/`. Choose individual objects, intercostal layers, valve leaflets or the full retained source assembly. Groups use the original common source coordinates; no geometry is fitted or bridged. Source XY/XZ/YZ controls describe projection axes rather than claiming verified patient orientation. Colours distinguish source layers and are not photographs of tissue.

Original OBJ files, original source mappings and the upstream license are retained in gzip form. Every source vertex, authored normal and triangle order is preserved, subject only to measured Float32 transport error. The largest positional conversion error is approximately 0.0000586 source mm; that number is numerical precision, not acquisition resolution or anatomical accuracy. No decimation, capping, smoothing, welding or deletion is performed.

The diaphragm contains four exact-position nonmanifold edges, each approximately 0.002–0.003 source mm long, in a localized original mesh patch. Their original face indices and coordinates are recorded in `evidence/topology-events.json`. They remain unchanged. Matching identical vertex positions for diagnostics closes the source index seams but does not change any delivered geometry. Neither these diagnostics nor a closed surface establishes a valid anatomical assembly.

Producer M forms are preserved separately and do not establish independently acquired left/right anatomy. No patient registration, ultrasound-to-model registration, functional valve/diaphragm motion, clinical measurement or anatomical completeness is inferred.

The actual reporting requirement remains broader: pleural and pericardial tissue/space interfaces, lung/consolidation/bronchial context, ribs and superficial tissue, chambers, IVC and other acquired findings still need complete source correspondence. These 12 objects do not satisfy those missing structures. They remain outside the deployed module until integration and verification are complete.

Reproduce the package from the retained acquisition folder:

```sh
python tools/anatomy_sources/package_thoracic_original_sources.py \
  --source-root .research/thoracic-ultrasound-20261013/bp3d-native-source \
  --output docs/thoracic-native-anatomy-review-20261013
```

BodyParts3D, Copyright 2008 Database Center for Life Science (DBCLS). The upstream 4.3 source and geometric transport adaptation use [CC BY-SA 2.1 Japan](https://creativecommons.org/licenses/by-sa/2.1/jp/). The separate archive 4.0 CC BY 4.0 grant is not applied. Source: [BodyParts3D](https://lifesciencedb.jp/bp3d/).

Verification: `python -m pytest tests/test_thoracic_original_geometry.py -q` compares every source coordinate, authored normal and face against the transported arrays and re-derives all four source topology events. With Playwright and Chromium available, `node tools/check_thoracic_source_geometry.cjs` verifies actual GPU uploads and draw calls for each object and assembly at desktop/mobile widths; start the local server above first.
