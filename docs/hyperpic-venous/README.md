# HyperPIC venous simulation boundaries

Pierre Mollo, Guillaume Dollé, Olivier Balédent and Stéphanie Salmon released the MRI-derived hpT2 and hpT6 computational meshes. The Zenodo record lists CC BY 4.0. The bundled source code carries its own CeCILL terms. Primer uses the deposited mesh data and its boundary definitions. [Source archive](https://doi.org/10.5281/zenodo.11032278) · [Article](https://doi.org/10.1051/mmnp/2025002)

The archive's mesh README specifies millimetres and five labels. Label 1 is the wall. Labels 2 and 3 are the right and left transverse sinus boundaries. Labels 4 and 5 are the straight and superior sagittal sinus boundaries. The browser uses the source X, Y and Z coordinates and retains 70,842 original boundary triangles at Float32 precision. The audit records the archive hashes, original face counts and independent triangle-area sums.

The table measures the labelled simulation boundary faces. Their dimensions describe the cut planes of the two computational domains. The vessel wall is a single source label. Full vessel calibre, patient pathology, matching native venography and named measurements beyond the released labels remain separate requirements.
