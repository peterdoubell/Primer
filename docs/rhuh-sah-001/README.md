# RHUH subarachnoid haemorrhage

The [RHUH release](https://zenodo.org/records/8228847) by Santiago Cepeda and Sergio García-García supplies preprocessed non-contrast CT and expert haemorrhage masks under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Case 001 has matching RAS image and label arrays of 193 × 229 × 193 with 1 mm voxel spacing. The authors skull-stripped, resampled and normalized the scan before release. The viewer preserves the released normalized values as Float32 and stores the binary mask as unsigned bytes.

The mask contains 60,797 labelled voxels and spans 89 axial planes. Its 81,496 model triangles follow the exact exposed voxel faces. The mesh encloses 60,797 cubic millimetres on the source grid. The source supplies a single binary label. No site of rupture or subtype is assigned to individual components. Independent specialist review is pending.
