# Independent CVH5 importer evaluation

The unchanged original U3D contains 47 RHAdobeMeshResource objects. Independent verification of their coordinates, topology, normals and UIC1 initialization remains outstanding.

The Aspose Java FOSS repository at the pinned commit advertises Universal3D loading in `FileFormat`, but its actual load dispatcher has no U3D branch and throws `No importer available for format: u3d`. A support flag is not evidence that this extension can be decoded.

The separate vendor SDK 26.9.0 was evaluated using a task-local ARM64 JDK. The known OBJ cube loaded as one mesh, eight points and twelve triangles. The original pelvic U3D raised `TrialException`, retained only five children of the source model group, and returned zero meshes, points and polygons. This demonstrates that the available evaluation cannot verify the original geometry. It does not distinguish unsupported RHAdobe decoding from evaluation-related truncation and does not prove any source defect.

The original source hash, SDK acquisition hashes, control input, probe code and exact output logs are retained. No licence limits were bypassed, no SDK or runtime was added to Primer, and no candidate arrays were fitted to make a comparison pass. An unrestricted independent original decoder or adequate native encoder/renderer evidence is still needed. This review grants no clinical approval or model coverage and does not change the existing holds.
