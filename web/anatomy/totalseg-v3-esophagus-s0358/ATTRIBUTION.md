# Partial source reference

Original CT case s0358: source metadata age 90,female,study type ct pelvis,trauma/abdomen. These are source-labelled inspection candidates, not a normal esophageal atlas or current patient.

All 27 complete original selected source label interfaces and 686,252 triangles are retained. Original source-grid CT and masks can be inspected separately in every plane. No smoothing,padding,capping,decimation,component deletion,relabeling or fitted transformation is applied. Display colours and normals are illustrative.

One declared 255×255×523 grid with 1.5 mm pitch and original RAS sform. Raw DICOM/HU calibration, native patient orientation,contrast phase and fine-tissue accuracy remain unverified. Left/right are original source label names; patient laterality is not independently verified.

The esophageal label is an organ envelope, without separate lumen,wall layers,mucosa,glands,plexuses or hiatal attachments. Whole heart does not separately identify left atrium; atrial appendage is not the entire atrium. Published clinical figures are different cases with no registration to this CT.

Left upper lung mask contains 261 six-connected components and 137 surface interfaces. Heart has 2 foreground components and 47 surface interfaces,including 45 opposite-winding to the largest; surface count alone does not identify organ fragments. Pulmonary veins retain 4 disconnected components. These source assignments require further anatomical review.

Spinal cord retains 40 open source boundary edges at the scan extent. T6,T8,T11 and lower lung additional components remain. Closed source label endpoints do not establish physical organ ends. Source stair steps and Lewiner ambiguity-field residuals are not independently measured anatomical accuracy.

Inspection reference only: no every-structure reporting coverage,clinical approval,current lesion diagnosis,physiological timing,pressure or flow evidence is granted. Original members pass CRC/SHA with stable publisher archive identity before/after; full 37.4 GB archive MD5 and object immutability remain unverified. Jakob Wasserthal. TotalSegmentator dataset v3.0.0, case s0358. DOI 10.5281/zenodo.22688904. CC BY 4.0. Adaptation: original 0.5 label-interface extraction, float32 transport and display normals.
