# Original pelvic nodal CT references

Primer serves two baseline acquisitions from Rojas-Pizarro and colleagues’ CT collection. The authors published the acquired NIfTI volumes, manual lesion instance masks and RECIST measurement table under CC BY 4.0. The measurement for case 023 is the authors’ recorded measurement. [Source dataset](https://doi.org/10.5281/zenodo.17788162) · [Methods](https://doi.org/10.1038/s41597-026-06597-6) · [Licence](https://creativecommons.org/licenses/by/4.0/)

| Case | Primer reference | Source nodal labels | Native sampling | Retained source indices |
| --- | --- | --- | --- | --- |
| 015 | Bladder Cancer and VI-RADS | Three pelvic nodes | 0.763671875 × 0.763671875 × 2.5 mm | z 25–64 |
| 023 | RECIST | Two iliac nodes, including target A measured at 16 mm on the axial short axis | 0.697265625 × 0.697265625 × 2.5 mm | z 26–57 |

Both retained bands include every original pixel in each axial plane. The CT and mask NIfTI dimensions and both affines match exactly. The viewer decodes the original signed 16-bit samples, applies the stored CT scale of 1 and intercept of −1024, and uses the publisher’s label numbers. Orthogonal views retain the source samples and display their acquired spacing. The masks preserve all label numbers in each band. The outline controls identify only the selected nodal labels.

Each selectable 3D surface follows the outer faces of the labelled voxel cells in the original RAS millimetre coordinates. The two cases contain 24,980 triangles across five nodal labels. Label 1 in case 015 retains both original connected components. The audit records preserve source member sizes, CRCs, SHA-256 digests, crop coordinates and mesh geometry. Case 015 illustrates CT nodal context for a separate MRI reporting lesson. The masks delineate gross nodal contours. Internal nodal detail, specific chains in case 015, and histopathology are outside the source annotations.
