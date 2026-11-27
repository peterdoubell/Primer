# Single-case chest, abdomen and pelvis CT

The reader uses the original TotalSegmentator v3.0.0 CT from case s0028 and every one of its 117 binary segmentation files. It is reachable from the chest–abdomen–pelvis and trauma panscan reports and the corresponding teaching modules. Each report-area link names the applicable source classes. Separate compartments such as pleura, nodal stations and tumour targets retain explicit gaps. [Wasserthal and colleagues, version 3.0.0](https://zenodo.org/records/22688904)

The dataset describes s0028 as a 59-year-old female neck–chest–abdomen–pelvis examination. The stored grid is 299 × 299 × 394, at 1.5 mm spacing. 109 masks contain voxels, 8 are empty and 20 touch the acquired grid boundary. The publisher’s no-pathology category is metadata for this case. It does not establish an exhaustive normal reference or the findings in the current patient.

The archive record and its published MD5 identify the 37,415,622,057-byte source ZIP. Only the exact range containing the 117 original segmentation members was retrieved. Their local ZIP headers, lengths, CRC32s and SHA-256s were checked. The CT already present in the lung reader was matched to the same archive member. The complete 37 GB archive was not downloaded or independently hashed. The acquisition receipt retains the source-byte evidence.

For viewing, each checked 64-cell brick stores a little-endian signed 16-bit original CT sample and up to two mask membership indices per voxel, with I varying fastest. Those indices are transport keys. Each user-visible choice retains the original published class name. At 5,676 positions two source masks include the same voxel. Both memberships are retained in the map, area table and pixel readout. Empty masks are selectable and have no derived surface.

The 3D surfaces follow the 0.5 interfaces of the individual binary masks in native-grid millimetres. Every component is retained. Masks touching the edge use only samples inside the scan; no extra boundary caps are added. The independent source comparison checked 35,223,994 CT values, all 117 complete mask arrays, 1,184,902 vertices and 2,368,866 triangles. It verified every transition edge and the incident geometry of the 244 ambiguous-cell centre vertices. This establishes representation of the source arrays. Independent clinical validation is open.

Run these commands with NumPy, NiBabel and scikit-image available to reproduce the source package or independently compare it against the source inputs.

```sh
python tools/anatomy_sources/acquire_s0028_torso.py
python tools/anatomy_sources/package_s0028_torso.py
python tools/anatomy_sources/verify_s0028_torso.py
```

The original CT, masks and derived surfaces are credited to Jakob Wasserthal and colleagues, University Hospital Basel, under CC BY 4.0. Adaptations include lossless brick encoding, display colours, multiplanar display and mesh extraction. [Licence](https://creativecommons.org/licenses/by/4.0/)
