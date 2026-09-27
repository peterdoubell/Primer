# Open Knee(s) oks003 source review

These are offline source-review artifacts, not clinical approvals. The optional
viewer preserves the 16 author-selected meshes under CC BY-SA 3.0. Raw MRI and
label volumes remain in acquisition staging outside the web application.

- [Acquisition, licences and limits](../msk-openknee-public-source-progress.md)
- [Original MRI archive README](archive-readme.txt)
- [Fourteen-object paired audit](paired-source-audit.json)
- [Native geometry measurements](geometry-audit.json)
- [Exact mask choices and held variants](assembly-mask-bindings.json)
- [Artifact hashes](artifact-sha256.json)

The 14 `*-source-planes.png` sheets show original MRI samples, author label
outlines in cyan and exact mesh-plane intersections in gold. They use declared
NIfTI affines with no fitted registration. Numerical overlap compares the
authors' labels with their processed meshes; it is not independent anatomical
accuracy. MRI displays have windowing for visibility, with no source voxel
modifications. The general and cartilage acquisition licences remain CC BY 4.0;
the source repository's geometry and labels remain CC BY-SA 3.0.
