# Partial processed tongue source reference

One source BeLong case, sub-007_segID-001; source demographic age 33.12 years and sex female. The publication describes the released cohort as non-neurodegenerative healthy controls; the individual spreadsheet has no diagnosis field. This does not independently establish normal anatomy, swallowing function or the current patient.

These are distributed processed source data: study-template registration, mouth ROI masking/cropping, and publisher 1 mm Gaussian smoothing of labels. They are not an unmodified native acquisition. The original distributed MRI and label samples, own sforms and registration affine are preserved separately.

Source grid 64×320×320 with declared 0.8 mm isotropic sample pitch. MRI stored int16 samples have original slope 0.05391012504696846 and intercept 1766.5269775390625; these are source-scaled signal values, not calibrated physical tissue measurements. The mask has its own slightly different sform; no replacement affine or fitted registration is applied. Camera labels use source coordinates.

All four distributed labels and all 67,508 triangles are retained. Inferior longitudinal remains two separate source components; transverse and vertical are a single combined publisher label, not individually resolved muscles. No extra smoothing, capping, padding, decimation, repair, mirroring, component removal or relabelling.

Hyoglossus, styloglossus, palatoglossus, muscle fibres, neural and vascular supply, fine mucosal interfaces, palate, hyoid, laryngeal folds/cartilage, pharyngeal wall and cricopharyngeal interfaces are not independently represented. Closed masks do not prove an anatomical capsule or a separately resolved tissue boundary.

Matching MRI planes belong to this processed case and use its source index grid. There is no registration to published swallowing movies, other source patients or current reports. Static anatomy supplies no bolus transit, airway protection, aspiration exclusion, muscle activity or physiological swallowing simulation. Display colours are labels, not photographic tissue colours.

Dataset rights are verified from the OSF node-linked CC0 grant, separately from the article CC-BY-NC-ND 4.0 licence. Independent anatomical and clinical review remain pending. Ribeiro, F. L. and Shaw, T. B. An annotated MRI dataset for the study of the human tongue musculature. OSF WT9FC, DOI 10.17605/OSF.IO/WT9FC. Dataset CC0 1.0 Universal; the separately restricted article supplies no reused graphics or captions. Adaptation: unchanged distributed label interfaces, float32 transport, display normals and declared MRI window.
