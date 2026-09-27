PAGE 1
1. ABOUT THE DATASET 
-------------------- 
Title:  Three subject-specific human tibiofemoral joint finite element models: complete three-
dimensional imaging (CT & MR), experimental validation and modelling dataset. 
Creators:  Robert Cooper, Gavin Day, Nagitha Wijayathunga, Jiacheng Yao, Marlène Mengoni, Ruth 
Wilcox, Alison Jones 
Organisation:  Institute of Medical and Biological Engineering, University of Leeds, Leeds, UK. 
Rights-holder:  University of Leeds 
Publication Year:  2023 
 
Description:  
This dataset includes the experimental data, three-dimensional imaging, computational models and 
study data from work validating three subject-specific human tibiofemoral joint finite element 
models. This work forms part of a wider project developing in vitro and in silico pre-clinical testing 
methods for tissue preserving treatments of the knee joint.  
The aim of the related study was to provide validation of contact mechanics outputs for specimen-
specific tibiofemoral joint models and specifically investigate the need for subject-specific shape 
representation for the cartilage and meniscus tissues.   
The dataset provides a complete set of imaging, experimental and computational data for replication 
of the study.  To maximum the potential for re-use the dataset includes imaging and experimental 
data, which was collected alongside the immediate study data, but not used in that work. 
Magnetic resonance imaging of the knee joints in their intact state is included, using eight different 
imaging sequences.   Micro computed tomography imaging of the distal femur and proximal tibia 
after dissection and testing are also provided for all three knee joints.   The experimental data 
includes pressure sensor measurements taken from the tibial cartilage surface at multiple knee joint 
flexion angles and photographs taken during dissection, potting and loading of the joints. The 
computational models are provided for all cases performed for the validation and sensitivity testing 
study, along with the associated results. 
 
Cite as:  
Cooper RJ, Day GA, Wijayathunga VN, Yao J, Mengoni M, Wilcox RK, Jones AC (2023) ‘Three subject-
specific human tibiofemoral joint finite element models: complete three-dimensional imaging (CT & 
MR), experimental validation and modelling dataset.’ University of Leeds. [Dataset] 
https://doi.org/10.5518/981 
 
 
 

PAGE 2
 
Related publications:  
Robert J. Cooper, Gavin A. Day, Vithanage N. Wijayathunga, Jiacheng Yao, Marlène Mengoni, Ruth K. 
Wilcox, Alison C. Jones. ‘Human tibiofemoral joint finite element model validation study: effect of 
cartilage thickness variation and assessment of precision’ (In preparation). 
Robert J. Cooper, Aiqin Liu, Gavin A. Day, Vithanage N. Wijayathunga, Louise M. Jennings, Ruth K. 
Wilcox, Alison C. Jones. ‘Development of robust finite element models of porcine tibiofemoral joints 
loaded under varied flexion angles and tibial freedoms’ Journal of the Mechanical Behavior of 
Biomedical Materials, 2020, 109:103797. 
Ethical approval:  
Ethical approval was obtained via East Midlands - Leicester South Research Ethics Committee 
(18/EM/0224)) for the use of fresh-frozen human cadaveric knees in this work. 
 
Contact: Alison C. Jones, a.c.jones@leeds.ac.uk 
 
Collection: 
This dataset belongs to the wider collection entitled “The Institute of Medical and Biological 
Engineering Knee Dataset”, https://doi.org/10.5518/826 
 
 
2. TERMS OF USE 
--------------- 
Copyright 2023 University of Leeds. This dataset is licensed under a Creative Commons Attribution 
4.0 International Licence: https://creativecommons.org/licenses/by/4.0/. 
 
 
3. PROJECT AND FUNDING INFORMATION 
---------------------------------- 
Title:  Optimising knee therapies through improved population stratification and precision of the 
intervention 
Dates:  1st October 2016 to 30th September 2022 
Funding organisation:  Engineering and Physical Sciences Research Council  
Grant no.:  EP/P001076/1 
 

PAGE 3
4. CONTENTS 
----------- 
Finite element models and images 
The compressed files with “FE model INP” in the title contain the .INP files of all variations of the 
knee models tested in this study.  These files can be read into the ABAQUS finite element software 
and by standard text editing software.  Each files contain the finite element meshes, material 
settings, boundary conditions, progressive loading/constraint steps, and contact conditions. 
 
1–RTKN0668 FE model INP files.zip The models of Knee 1 (or archive code RTKN0668). 
 
1-LTKN8941 FE model INP files.zip The models of Knee 2 (or archive code LTKN8941). 
 
1-LTKN1468 FE model INP files.zip 
 
The models of Knee 3 (or archive code LTKN1468). 
 
1-FE tibial contact pressure images.zip 
This compressed file contains PNG image files showing 
the contact pressure maps from the finite element 
models of both medial and lateral tibial condyles.  
 
File name codes used to identify the different cases are given below. These naming conventions 
are used for both the .INP model files and the .PNG image files. 
 
Knee specimens The three knees are identified by their codes: 
RTKN0668, LTKN8941, LTKN1468 
 
Cartilage representation The cartilage representation is indicated by “seg” for 
cases in which the cartilage has a non-uniform 
thickness directly segmented from imaging, and “uni” 
for cases in which the cartilage has a uniform thickness. 
 
Meniscus inclusion The inclusion or exclusion of the two menisci is 
indicated by “intact” (where the menisci are included) 
and “nomen” (where they are excluded). 
 
Tibial constraint The different tibial constraint cases are indicated by 
“fix” (where the tibia is constrained in all degrees of 
freedom) or “progFree” (where the experimental tibial 
freedom is replicated by progressive release of each 
degree of freedom). 
 
Load matching experimental Two of the files have two versions, where one version 
has an extension of either “_f200” or “_f80”.  These are 
the cases where the experimental load did not reach 
the intended 500 N. For those modelling cases two 
versions of provided.  A version loaded to 500 N (with 
no additional file extension) and a version loaded to 
the lower load value achieved experimentally (either 
80 N or 200 N).  
 
 

PAGE 4
 
Study data 
2-Study results sheets.zip This compressed file contains the .CSV files of 
model settings, model output measures and 
comparisons with experimental data. 
 
 
Files within the compressed file are as follows. 
 
Full_Model_Output_Data.csv Case descriptions, model settings and 
measures from all Finite Element modelling 
cases in the study.  
 
ExpFE_Contact_Area_nomen_fix.csv Comparison of the contact area on the medial 
and lateral tibial condyles, for experimental 
and computational cases with no menisci and a 
fully fixed tibia. 
 
ExpFE_Contact_Area_nomen_partFree.csv Comparison of the contact area on the medial 
and lateral tibial condyles, for experimental 
and computational cases with no menisci and a 
partially free tibia. 
 
ExpFE_ML_Force_Balance_nomen_fix.csv Comparison of the percentage of force being 
carried by the medial versus the lateral tibial 
condyles, for experimental and computational 
cases with no menisci and a fully fixed tibia. 
 
ExpFE_ML_Force_Balance_nomen_partFree.csv Comparison of the percentage of force being 
carried by the medial versus the lateral tibial 
condyles, for experimental and computational 
cases with no menisci and a partially free tibia. 
 
FE_Tibial_Movement_nomen_partFree.csv The movement of the tibia in the 
computational cases with no menisci and a 
partially free tibia.  
 
FE_Meniscus_Contact_Area.csv Results from the intact tibiofemoral joint finite 
element models, showing the amount of 
contact area on the tibial cartilage from 
contact with the meniscus and from contact 
with the femoral cartilage. 
 
FE_Meniscus_Load_Carried.csv Results from the intact tibiofemoral joint finite 
element models, showing the amount of load 
applied to the tibial cartilage from contact with 
the meniscus and from contact with the 
femoral cartilage. 
 
 

PAGE 5
 
Experimental pressure data     
The compressed files in this section contain data from pressure sensors within the tibiofemoral 
joint in the experimental specimens.  This data has been recorded for three cadaveric knees 
tested in two states (with and without meniscus) and at two flexion angles (10 degrees and 20 
degrees). 
 
3-RTKN0668_pressure_sensor_data.zip   
 
The data recorded for Knee 1 (or archive code 
RTKN0668). 
 
3-LTKN8941_pressure_sensor_data.zip   
 
The data recorded for Knee 2 (or archive code 
LTKN8941). 
 
3-LTKN1468_pressure_sensor_data.zip 
 
The data recorded for Knee 3 (or archive code 
LTKN1468). 
 
 
Photographs from lab dissection, potting and testing  
The compressed files in this section contain photographs taken during the experimental work.  
These include the dissection steps, potting and testing.  These photographs give a sense of the 
quality of the tissue of each sample.  
 
 
4-RTKN0668_lab_photographs.zip  The images taken of Knee 1 (or archive code 
RTKN0668). 
 
4-LTKN8941_lab_photographs.zip  The images taken of Knee 2 (or archive code 
LTKN8941). 
 
4-LTKN1468_lab_photographs.zip  The images taken of Knee 3 (or archive code 
LTKN1468). 
 
 
  

PAGE 6
Micro-Computed Tomography images of tibiofemoral joint with surrounding tissue dissected 
 
5-Knee_CT_preview_slices.zip 
The three-dimensional CT images in this section are 
large and will take some time to download.  Preview 
images for each CT image are available in this 
compressed file. 
    
   The following details apply for the block of compressed CT images stacks immediately below. 
 
   Image: high-resolution peripheral quantitative computed tomography 
   Machine: XtremeCT, Scanco Medical AG, Switzerland 
   Resolution: isotropic voxel size of 82 µm 
   Format: DICOM image stack 
   Storage size: Each image stack ~3-5 Gb. 
 
5-RTKN0668_mCT_intact.zip          Knee 1, full knee with patella 
 
5-RTKN0668_mCT_dissected.zip       Knee 1, tibiofemoral joint, ligaments removed 
 
5-RTKN0668_mCT_nomen.zip           Knee 1, tibiofemoral joint, no meniscus  
 
5-LTKN8941_mCT_dissected.zip       Knee 2, tibiofemoral joint, ligaments removed 
 
5-LTKN8941_mCT_nomen.zip           Knee 2, tibiofemoral joint, no meniscus 
 
5-LTKN8941_mCT_nomen_femur.zip Knee 2, just the femur, condyles cut off 
 
5-LTKN1468_mCT_dissected.zip Knee 3, tibiofemoral joint, ligaments removed 
 
5-LTKN1468_mCT_nomen_femur.zip     Knee 3, just the femur 
 
5-LTKN1468_mCT_nomen_tibia.zip     Knee 3, just the tibia 
 
 
  

PAGE 7
Magnetic Resonance Images of pre-dissection whole knee 
 
6-Knee_MR_preview_slices.zip 
The three-dimensional MR images in 
this section are large and may take 
some time to download.  Preview 
images for each MR image are 
available in this compressed file. 
 
For all MR images of all knees: 
Format: DICOM image stack 
Storage size: Each image stack 15-30 Mb 
 
Machine used for all MR images of RTKN0668 (Knee1):  
3 Tesla MRI scanner (Siemens Magnetom Prisma, Erlangen, Germany)  
using a 15 channel transmit/receive knee coil (Siemens, Erlangen, Germany) 
    
Machine used for all MR images of LTKN8941 (Knee 2) & LTKN1468 (Knee 3): 
3 Tesla MRI scanner (Siemens Magnetom Vida, Erlangen, Germany)  
using an 18 channel transmit/receive knee coil (Siemens, Erlangen, Germany) 
    
The various MR sequences taken of the three cadaveric knees are described below.   
Some were taken for all three knees and others for only one or two of them. 
 
 
 
The following details apply for the block of compressed MR images listed immediately below. 
Image sequence: MRI - 3D Double Echo Steady State (DESS)  
    Resolution: 0.36 x 0.36 x 0.7 mm3, 144 slices 
    Objective in this work: Cartilage imaging & assessment 
    
6-RTKN0668_MR_DESS.zip        Knee 1 
6-LTKN8941_MR_DESS.zip        Knee 2 
6-LTKN1468_MR_DESS.zip         Knee 3 
 
 
 
The following details apply for the block of compressed MR images listed immediately below. 
Image sequence: MRI - 2D Proton density weighted, Turbo spin echo, No fat saturation  
    [similar to sequences in the Osteoarthritis Initiative database, with higher resolution] 
    Slice direction: Sagittal 
    Resolution: 0.3 mm in plane, 1.6mm slice thickness, 62 slices, No slice gap  
    Objective in this work: Anatomical details  
    
6-RTKN0668_MR_2D_TSE_SAG_IW_0.3pix.zip Knee 1 
6-LTKN8941_MR_2D_TSE_SAG_IW_0.3pix.zip Knee 2 
6-LTKN1468_MR_2D_TSE_SAG_IW_0.3pix.zip       Knee 3 
    
 
 
 
 
 

PAGE 8
 
 
The following details apply for the block of compressed MR images listed immediately below. 
Image sequence: MRI - 2D Proton density weighted, Turbo spin echo, With fat saturation   
    [similar to sequences in the Osteoarthritis Initiative database, with higher resolution] 
    Slice direction: Coronal 
    Resolution: 0.3 mm in plane, 1.6mm slice thickness, 62 slices, No slice gap 
    Objective in this work:  Bone marrow lesions, Cartilage lesions, inflammation, meniscal tears, 
    parameniscal cysts, meniscal extrusion        
 
6-RTKN0668_MR_2D_TSE_COR_FS_IW_0.3pix.zip Knee 1 
6-LTKN8941_MR_2D_TSE_COR_FS_IW_0.3pix.zip       Knee 2 
6-LTKN1468_MR_2D_TSE_COR_FS_IW_0.3pix.zip       Knee 3 
    
 
 
The following details apply for the block of compressed MR images listed immediately below. 
Image sequence: MRI - 2D Proton density weighted, Turbo spin echo, With fat saturation   
   Slice direction: Transverse (axial) 
   Resolution: 0.3 mm in plane, 1.6 mm slice thickness, 62 slices, No slice gap 
   Objective in this work:  Meniscal tears, Bone marrow lesions 
 
6-LTKN1468_MR_2D_TSE_TRA_FS_IW_0.3pix.zip       Knee 3 
 
 
 
The following details apply for the block of compressed MR images listed immediately below. 
Image sequence: MRI - 2D T2-weighted, Turbo spin echo, No fat saturation    
   Slice direction: Sagittal  
   Resolution: 0.3 mm in plane, 1.6 mm slice thickness, 60 slices, no slice gap   
    
6-RTKN0668_MR_2D_T2_noFS_TSE_SAG_IW_0.3pix.zip Knee 1 
6-LTKN8941_MR_2D_T2_noFS_TSE_SAG_IW_0.3pix.zip       Knee 2 
6-LTKN1468_MR_2D_T2_noFS_TSE_SAG_IW_0.3pix.zip       Knee 3 
    
 
 
The following details apply for the block of compressed MR images listed immediately below. 
Image sequence: MRI - 2D T2-weighted, Turbo spin echo, With fat saturation   
    Slice direction: Sagittal  
    Resolution: 0.3 mm in plane, 1.6 mm slice thickness, 60 slices, no slice gap      
    Objective in this work:  Bone marrow lesions, Cartilage lesions, Inflammation, Haem arthrosis,   
    Meniscal root tears, Parameniscal cysts 
        
6-RTKN0668_MR_2D_T2_FS_TSE_SAG_IW_0.3pix.zip        Knee 1 
6-LTKN8941_MR_2D_T2_FS_TSE_SAG_IW_0.3pix.zip       Knee 2 
    
 
 
 
 

PAGE 9
The following details apply for the block of compressed MR images listed immediately below. 
Image sequence: MRI - 3D T1 VIBE, with water excitation     
   Slice direction: Coronal 
   Resolution: 0.4 mm x 0.4 mm x 0.7 mm        
   Objective in this work:  Assessment of the bone as well as other soft tissue structures such as 
   ligaments       
      
6-LTKN1468_MR_T1_vibe_we_cor iso_High res.zip    Knee 3 
    
 
 
The following details apply for the block of compressed MR images stacks immediately below. 
Image sequence: MRI - 2D, Multi echo data image combination (MEDIC)     
   Slice direction: Coronal 
   Resolution: High in-plane res, 0.2 mm x 0.2 mm x 2 mm  
   Objective in this work:  Cartilage & ligament assessment  
     
6-LTKN1468_MR_medic_cor.zip    Knee 3 
 
           
     
 
5. METHODS 
---------- 
Specimen codes  
Codes linking the simple specimen numbers used in the study data sheets and associated paper, to 
those used in the wider knee database.  [Filename: specimen_codes.txt] 
 
Method documentation  
Details of the experimental and computational methods and the details of the comparisons made in 
the results data sheets, are given in this document.  [Filename: method_documentation.pdf] 
 
 
 