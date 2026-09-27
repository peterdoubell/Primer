This readme file was generated on [2026-04-13] by [JEEVARAAJ N VIVEKANANDAN]

GENERAL INFORMATION

Title of Dataset: A Three-Dimensional Lower Extremity Musculoskeletal Geometry Model of An Asian Male 

Author/Principal Investigator Information
Name: DR. JULIANA BINTI USMAN
ORCID: https://orcid.org/0000-0001-8983-0892
Institution: Centre for Applied Biomechanics, Department of Biomedical Engineering, Faculty of Engineering, Universiti Malaya.
Address: 50603 Kuala Lumpur, Malaysia.
Email: juliana_78@um.edu.my

Author/Associate or Co-investigator Information
Name: JEEVARAAJ A/L N.VIVEKANANDAN
ORCID: https://orcid.org/0009-0000-9249-8392
Institution: Department of Biomedical Engineering, Faculty of Engineering, Universiti Malaya.
Address: 50603 Kuala Lumpur, Malaysia.
Email: jeevaraaj@rocketmail.com


- Date of data collection: 2025-10-10 to 2026-03-30
- Geographic location of data collection: Malaysia
- Information about funding sources that supported the collection of the data: Ministry of Higher Education, Malaysia, Research Grant DP KPT (FRGS/1/2019/TK03/UM/02/9), Universiti Malaya Centre of Research Grant (CORG 012-2024).

SHARING/ACCESS INFORMATION

- Licenses/restrictions placed on the data: -
- Links to publications that cite or use the data: -
- Links to other publicly accessible locations of the data: -
- Links/relationships to ancillary data sets: -
- Recommended citation for this dataset: -

DATA & FILE OVERVIEW

File List: 1. Magnetic resonance imaging (MRI) scans: The MRI scans are shared in DICOM format. It consists of scans of the lower extremity in multiple types of sequences and in 3 different segments. It consists of compiled segments in all the sequences. The DICOM folders are separated by the type of sequence used and the folders are named by the sequences naming. The naming is based on Siemens Prisma Magnetom 3T.
2. Segmentation mask: The segmentation masks created are compatible with 3D slicer software in nrrd file format. Segmentation masks of the final model with labels were added to allow other researchers to inspect and adjust the model.
3. Final 3D model: The final model can be directly utilized for analysis without requiring additional processing. Each structure was visually inspected to ensure there were no surface protrusions, openings and overlaps.

- Relationship between files, if important: 3D slicer software was used to segment the MRI scans, where the segmentation mask was created. The final models are the output from the software as individual 3D models. 

METHODOLOGICAL INFORMATION

Description of methods used for collection/generation of data:
Initially, MRI scans were taken from an average sized healthy Asian male. These 7 sequences were taken using Siemens Prisma Magnetom 3T. The sequences were taken in 3 different segments due to limited field of view of MRI. The segments were then combined together.
1.	RT T1 VIBE SAG DIXON_IN
2.	RT T1 VIBE SAG DIXON_F
3.	RT T2 SPC SAG L - LIMB
4.	RT T2 FS SPC SAG L - LIMB
5.	RT T1 VIBE SAG DIXON FS L - LIMB
6.	T1 VIBE SAG DIXON_OPP L - LIMB
7.	T1 SAG VIBE DIXON_W L – LIMB

Methods for processing the data:
In 3D slicer software, the MRI scans were uploaded in DICOM format. ‘Grow from seeds’ is a semi-automated function in 3D slicer to segment the images into a 3D model. The area of interest and background were shaded with a paintbrush using different colours in multiple slices. The function then utilizes region-growing algorithm to expand the painted labels to fill the anatomical structures. Each of the slices were cycled through to refine the region of interest. A list of smoothing processes were done on the model by first opening function was done to remove small, isolated protrusions to smooth the surface. Then, closing function was used to fill small gaps within the segment. Median function was also used to reduce overall noise and unwanted protrusions while preserving the overall shape of the object. After all the structures were segmented and smoothed, joint smoothing function was used to ensure each parts fit together with their neighboring parts without overlapping to each other. Finally, the individual models of each parts were generated in STL files.

Instrument- or software-specific information needed to interpret the data:
Any software that support DICOM format file can open the MRI scans. The folders are separated by the type of sequences used. User can select the type and open the whole folder as a DICOM. For the final model, software that support STL files such as ANSYS and Solidworks can be used. 3D slicer software is required to run the segmentation mask file which is in nrrd format. 

- Standards and calibration information, if appropriate: -
- Environmental/experimental conditions: -
- Describe any quality-assurance procedures performed on the data: The creation of the segmentations for the 3D model was done with reference to segmentations maps created by Andreassen, Hume [1], anatomical reference from Hansen [2] and anatomical imaging application of MRIMaster [3]. All the geometries were inspected and validated by a radiologist and radiographer from Universiti Malaya Medical Centre (UMMC). Nevertheless, we acknowledge that certain inaccuracies may still be present. In some regions, the boundaries between anatomical structures on the MRI images were challenging to distinguish. Such geometries were not included in the dataset, particularly minor tendon, minor ligaments and intrinsic foot muscles which were hard to identify.
[1] Andreassen, T.E., et al., Three Dimensional Lower Extremity Musculoskeletal Geometry of the Visible Human Female and Male. Scientific Data, 2023. 10(1): p. 34.
[2] Hansen, J.T., Netter's Clinical Anatomy-E-Book: Netter's Clinical Anatomy-E-Book. 2021: Elsevier Health Sciences.
[3] Rejosh George, et al. MRI Images and Techniques. 2026  [cited 2026 20.02]; Available from: https://mrimaster.com/.
- People involved with sample collection, processing, analysis and/or submission: Jeevaraaj N Vivekanandan, Dr. Hazwan Amzar Bin Khairul Annuar, Mohd Azwan Bin Abdullah and Dr. Juliana Binti Usman.

DATA-SPECIFIC INFORMATION FOR: DICOM

- Number of variables: 7
- Number of cases/rows: 174 - 176 files in each folder
- Variable List: Folder separated by the type of sequences used:
1.	RT T1 VIBE SAG DIXON_IN
2.	RT T1 VIBE SAG DIXON_F
3.	RT T2 SPC SAG L - LIMB
4.	RT T2 FS SPC SAG L - LIMB
5.	RT T1 VIBE SAG DIXON FS L - LIMB
6.	T1 VIBE SAG DIXON_OPP L - LIMB
7.	T1 SAG VIBE DIXON_W L – LIMB
- Missing data codes: Right (RT)
Contrast weight: T1/T2
Sequence type: Sampling Perfection with Application optimized Contrasts using different flip-angle Evolutions (SPACE/SPC) and Volumetric Interpolated Breath-hold Examination (VIBE) 
Technique: DIXON
Reconstruction technique type: In phase (IN)/ Opposed phase (OPP)/ Water Only (W)/ Fat only (F).
- Specialized formats or other abbreviations used: DICOM

DATA-SPECIFIC INFORMATION FOR: Final model segmentation

- Number of variables: 1
- Number of cases/rows: 30 items.
- Variable List: Main variable to be used is Final model in the format of nrrd (can be opened using 3D slicer software).
- Specialized formats or other abbreviations used: nrrd

DATA-SPECIFIC INFORMATION FOR: Final model STL parts

- Number of variables: 1
- Number of cases/rows: 67 individual parts
- Variable List: There are total of 13 bones, 4 cartilages, 5 ligaments, 42 muscles structures, 1 meniscus and 2 tendons from hip to foot. 
- Specialized formats or other abbreviations used: STL
