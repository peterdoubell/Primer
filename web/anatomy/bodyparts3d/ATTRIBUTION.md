# BodyParts3D anatomical meshes

BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International.

- Dataset: BodyParts3D version 4.0, official 99% polygon-reduced IS-A OBJ archive.
- Source: <https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html>
- Archive: <https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip>
- Official license statement, updated 25 February 2025: <https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/README_e.html>
- License: Creative Commons Attribution 4.0 International, <https://creativecommons.org/licenses/by/4.0/>.
- Original publication: Mitsuhashi N, Fujieda K, Tamura T, Kawamoto S, Takagi T, Okubo K. *BodyParts3D: 3D structure database for anatomical concepts*. Nucleic Acids Research. DOI: <https://doi.org/10.1093/nar/gkn613>.

## Adaptations

The Primer selects source anatomical elements and combines only components of the same source anatomical concept. Their registered coordinates are preserved. Indexed binary geometry replaces OBJ text; area-weighted vertex normals are calculated for display. Viewing colours, camera framing and regional cropping are presentation choices. No generative geometry, invented anatomical structures, mesh deformation, or additional polygon reduction is applied.

The source is an adult male reference anatomy. These are surface models with the detail available in the published source meshes; they are not complete clinical segmentations or patient-specific models. The 3D viewer identifies omitted fine structures. The source prostate is an external surface without PI-RADS zones; the MSK source selection does not contain articular cartilage, labra, menisci, or all ligaments.

`manifest.json` records each anatomical concept, original FMA / FJ identifiers, source and derived file hashes, geometry counts, bounds, regional membership and license. `tools/build_detailed_anatomy.py` reproduces these assets from the official archive using range requests.
