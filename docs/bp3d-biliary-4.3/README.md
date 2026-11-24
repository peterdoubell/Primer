# Biliary source atlas

The biliary lesson, biliary duct reporting and gallbladder ultrasound reference link to 20 original BodyParts3D 4.3 objects in 14 source groups. Original hashes and CRCs matched the existing source review. Every face index and Float32 vertex was preserved. Repeated objects remain independently selectable in source coordinates.

The viewer credits DBCLS and applies CC BY-SA 2.1 Japan to the adapted atlas assets. It covers the gallbladder, common hepatic duct, cystic duct, right and left hepatic ducts and selected tributaries. Luminal continuity, wall layers, clinical variants and independent anatomy review remain open. Source contact findings are recorded in the original review.

The version-stamped 4.3 `concept-objfiles-list` maps FMA14668 to FJ3079 in both `is_a` and `part_of` and has no FMA14667 entry. The latter is the common bile duct concept in the [IFAA terminology](https://ifaa.unifr.ch/Public/TNAEntryPage/auto/part/EN/TAH2739%20P3%20EN.htm). [Clarkson and Whipple’s comparative study](https://pubmed.ncbi.nlm.nih.gov/30815072/) flagged the BodyParts3D common hepatic duct segmentation. Until 2026-11-24 the viewer kept the source label for the whole object and assigned no part of FJ3079 a new duct identity.

Since 2026-11-24 the viewer shows FJ3079 in two parts, divided where the source cystic duct meets it: the part above is labelled common hepatic duct and the part below common bile duct. Every source triangle is in one part, unchanged. The measurements, the method and its limits are in `docs/bp3d-biliary-duct-partition-20261124`. No radiologist has reviewed the division.
