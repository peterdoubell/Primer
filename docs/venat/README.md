# Venous Neuroanatomy Atlas

The [VENAT atlas](https://doi.org/10.6084/m9.figshare.7205960.v4) by Janine Huck and colleagues combines repeated 7 T MRI measurements in 20 participants. The Figshare record licenses the released maps under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The [paper](https://doi.org/10.1007/s00429-019-01919-4) describes the registration workflow and the differences between the partial-volume and detection-density maps.

The viewer shows the population atlas in MNI152 space. Primer calculated maximum projections directly from the released 0.5 mm atlas grid and extracted three partial-volume isosurfaces at levels 0.10, 0.15 and 0.25 using linear edge interpolation. Two zero-area faces that collapsed during Float32 conversion were removed from the 0.25 mesh. All other faces were retained. The acquisition records and source review pin the inputs, projections and decoded meshes. All mesh vertices reproduced the chosen threshold to within 0.000002 partial-volume units.

Individual vein names, clinical variants and thrombus require separate annotations or patient imaging. Independent anatomical review remains open.
