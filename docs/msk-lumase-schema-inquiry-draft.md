# LumASe source-definition inquiry — unsent draft

To the LumASe dataset authors:

We are assessing the original LumASe version 0.1 data, DOI 10.5281/zenodo.7181338, as a source for anatomical teaching references. Before naming or using the seven regions, we need to verify their original definitions and field of view.

Could you provide:

1. The original numeric label dictionary for values 1–7, ideally with the annotation configuration or source document that defines it.
2. Whether paired regions combine left and right sides, and how boundaries between the vertebral body, pedicles, laminae and articular processes were defined. Are facet surfaces or endplate interfaces distinct annotations, or included only in larger bone regions?
3. The crop protocol and whether a region reaching the NIfTI array edge can represent a truncated structure. Our native audit of the first ten paired L3 masks finds foreground at crop boundaries in every case. In source file `101002964255_L3_seg.nii.gz`, values 4–7 touch at least one boundary.
4. Whether larger original CT fields of view and their matching annotations are available for checking those endpoints, with their applicable reuse terms.
5. Confirmation that the original CT images and supplied masks are covered by the record's CC BY 4.0 terms, separately from later harmonized derivatives.

We have retained source labels and crop edges without changing voxels, filling holes, adding closure caps or assigning anatomical meanings from label order. We can provide exact file hashes and native-plane review images to support the questions.

This draft has not been sent. It does not identify a sender, organisation or recipient address, and makes no claim of clinical validation.
