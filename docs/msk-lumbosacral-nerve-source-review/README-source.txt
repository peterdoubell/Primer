An open-access lumbosacral spine MRI dataset with enhanced spinal nerve root structure resolution

(abstract) Spinal cord injury (SCI) profoundly affects an individual's ability to move. Fortunately, recent advancements in neuromodulation, particularly the spatio-temporal epidural electrical stimulation (EES) targeting the spinal nerve roots, promoted rapid rehabilitation of SCI patients. Such neuromodulation techniques require precise anatomical modelling of spinal cord. However, the lack of spine imaging datasets, especially high-quality magnetic resonance imaging (MRI) datasets highlighting nerve roots, hinders the translation of EES into medical practice. To address this problem, we introduce an open-access lumbosacral spine MRI dataset acquired in 14 healthy adults, using constructive interference in steady state (CISS) sequence, double echo steady state (DESS) sequence, and T2-weight turbo spin echo (T2-TSE) sequence, with enhanced nerve root resolution. The dataset also includes the corresponding anatomical annotations of nerve roots and the final reconstructed 3D spinal cord models. The quality of our dataset is assessed using image quality metrics implemented in MRI quality control tool (MRIQC). Our dataset provides a valuable platform to promote a wide range of spinal cord neuromodulation research and collaboration among neurorehabilitation engineers

### Contact information:
- Name: Jionghui Liu
- Email: jhliu22@m.fudan.edu.cn

### Of all subjects the following data were acquired:
- Whole spine 3T T2-weighted TSE scan: TR/TE = 4320/104 ms, flip angle = 160$^\circ$, slice thickness = 3.3 mm, voxel size = 0.6 $\times$ 0.6 $\times$ 3.0 mm$^3$
- 3T DESS scan: TR/TE = 11.59/4.24 ms, flip angle = 25$^\circ$, slice thickness = 1.27 mm, voxel size = 0.6 mm isotropic
- 3T high-resolution CISS scan: TR/TE = 9.80/4.46 ms, flip angle = 50$^\circ$, slice thickness = 1.8 mm or 2.0 mm, voxel size = 0.4 $\times$ 0.4 $\times$ 1.8 mm$^3$ or  0.3 $\times$ 0.3 $\times$ 2 mm$^3$
- demographic information

### The "derivatives" folder contains:
- anatomical annotations of the lumbosacral spine on CISS, DESS images
- derivative lumbosacral models
- anatqc, quality assessment of anat dataset, implemented with https://github.com/rordenlab/dcm2niix