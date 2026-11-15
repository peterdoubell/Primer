# Knee Model Data Validation for Specimen 192803 - Experimental Data, Models, Code, and Results

<https://doi.org/10.5061/dryad.zkh1893gw>

This dataset contains experimental data, models, code, and results for the S192803 specimen data. This dataset is one of two model datasets used in the paper Validation of Subject-Specific Knee Models from In Vivo Measurements, which is in review at the Journal of Biomechanical Engineering. The dataset contained herein is derived from the experimental data collected during a previous publication in the Journal of Medical Devices, entitled: "Apparatus for In Vivo Knee Laxity Assessment Using High-Speed Stereo Radiography". Available at: [https://doi.org/10.1115/1.4051834](https://doi.org/10.1115/1.4051834Another)

A similar dataset exists for the other specimen, S193761.

Work was created by Dr. Thor E. Andreassen, Dr. Donald R. Hume, Dr. Landon D. Hamilton, Stormy L. Hegg, Sean E. Higinbotham, and Dr. Kevin B. Shelburne at the Center for Orthopaedic Biomechanics at the University of Denver.

The work was funded by the NIH National Institute of Arthritis and Musculoskeletal and Skin Diseases, National Institute of Biomedical Imaging and Bioengineering, and the National Institute of Child Health and Human Development (Grant U01 AR072989).

If you have any questions, please email the main author, Dr. Thor Andreassen, at

[thor.andreassen@du.edu](mailto:thor.andreassen@du.e)

or at

[andreassen.thor@mayo.edu](mailto:andreassen.thor@mayo.e)

## Sharing/Access information

**Liability Agreement**

The Data is provided “as is” with no express or implied warranty or guarantee. The University of Denver and the Center for Orthopaedic Biomechanics do not accept any liability or provide any guarantee in connection with uses of the Data, including but not limited to, fitness for a particular purpose and noninfringement. The University of Denver and the Center for Orthopaedic Biomechanics are not liable for direct or indirect losses or damage, of any kind, which may arise through the use of this data.

**Sharing/USE**

This Code/Software is free to use for any reason. However, we ask that if you use any part of this work, that you cite the original two works that made it possible:

Andreassen, T. E., Hamilton, L. D., Hume, D., Higinbotham, S. E., Behnam, Y., Clary, C., and Shelburne, K. B. (September 10, 2021). "Apparatus for In Vivo Knee Laxity Assessment Using High-Speed Stereo Radiography." ASME. *J. Med. Devices*. December 2021; 15(4): 041004. <https://doi.org/10.1115/1.4051834>

Andreassen, T. E., Hume, D. R., Hamilton, L. D., Hegg, S.L.,  Higinbotham, S. E., and Shelburne, K. B. "Validation of Subject-Specific Knee Models from In Vivo Measurements." ASME. *J. Biomech, Engineering*.

## Code

The code provided is contained in the "Working Models" and the "Processing Code" Folders. The optimization of the model can be run by running the "Lig_Calibration.m" file in the "Optimization Full" folder. The code will run the Abaqus trials specified by the "JOBNAMES" and "JOBLIST" files. Values for the ligament parameters will be updated in the "Lig-Parameters.inp" file according to the current trial for the optimization. Kinematics will be extracted using the .py files and then the errors of these will be compared against the known laxity kinematics in the "Data_Processed_2.mat" file. The global cost will be calculated according to the weights in the "Weight.xlsx" file. Then the new set of design variables will be calculated and used to update the "Lig-Parameters.inp" file. The optimization will continue until manually stopped o convergence within a tolerance is reached.

To view experimental results of a given trial following optimization, the chosen parameters are update in the "AMP_TEST.inp" file for the knee flexion angle, and the desired loads. These are updated by changing the parameters of the "TF_KIN_STEP2_CYLINDRICAL_FE" and the "TF_LOAD_STEP2_" variables. Then the model can be run using the terminal on the "MAIN_TEST.inp" file. Lastly, results can be extracted using the "GET_ODB_Step_Info.m" script in the "Processing Code" folder and choosing the correct ODB file, and whether the portion you are interested in is the "LAXITY" step or the "FLEXION" step.

## Description of the data and file structure

This dataset represents original data from the work to validate the reproducibility of knee models based on the datasets used to build them. The files contained include Imaging Data, Knee Laxity Data, Optimization Code and Models, Processing Code, and Results. The imaging data provided include imaging and segmentation for the CT and MRI scans. Additional surface scans with color texture are provided as surface obj. The models were created in Abaqus Explicit and are provided as .inp files. All optimization and results are extracted using a combination of MATLAB and Python scripts.

The .mhd files, together with the .raw files, are segmentation files that can be used in segmentation software such as 3D Slicer, Materialize Mimics, or Simpleware ScanIP. The .stl files and the .obj (.obj and .mtl and .png together) are 3D geometries representing the outer meshed as triangulated surfaces. The .stl files only contain the geometry, while the .obj files include the original color of the vertices in the .mtl and the .png files. Stl and obj files can be opened and manipulated in software such as MeshMixer, MeshLab, or HyperWorks Hypermesh.

**Imaging Data - Original Cadaveric Specimen Images used for the creation of 3D geometries via segmentation**

1.  CTS - Computed tomography (CT) and surface texture scans

    1.  CT Scan - CT scans of specimen lower extremity

        1.  Imaging - Full lower extremity CT scans of the specimen
            1.  Full lower extremity CT scan of the specimen as .mhd files
        2.  Segmentation - Segmented pixel maps for the major bones of the legs of the specimen
            1.  Patella (Left and Right) as .mhd files
            2.  Femur (Left and Right) as .mhd files
            3.  Combined Tibia and Fibula (Left and Right) as .mhd files
    2.  Surface Scans - Surface Texture 3D geometries with color for left knee of the specimen

        1.  Capsule_Left
            1.  Capsule of the left knee as .stl and .obj formats
        2.  Femur_Left
            1.  Distal femur of the left knee as .stl and .obj formats
        3.  TibFib_Left
            1.  Combined proximal tibia and fibula with the meniscus intact of the left knee as .stl and .obj formats
            2.  Combined proximal tibia and fibula with the meniscus resected of the left knee as .stl and .obj formats
        4.  Patella_Left
            1.  Patella of the left knee as .stl and .obj formats
2.  MRI - Magnetic resonance imaging (MRI) scans of the lower extremity of the specimen

    1.  Imaging - Full lower extremity MRI scans of the specimen
        1.  Full lower extremity MRI scan of the specimen as .mhd files
    2.  Segmentation - Segmented pixel maps for the major bones, cartilage, ligaments, and menisci of the left knee of the specimen

        1.  Femur (Left) as .mhd files
        2.  Patella (Left) as .mhd files
        3.  Tibia/Fibula (Left) as .mhd files
        4.  Femoral Cartilage (Left) as .mhd files
        5.  Medial Tibial Cartilage (Left) as .mhd files
        6.  Lateral Tibial Cartilage (Left) as .mhd files
        7.  Medial Meniscus (Left) as .mhd files
        8.  Lateral Meniscus (Left) as .mhd files
        9.  ACL (Left) as .mhd files
        10. LCL (Left) as .mhd files
        11. MCL (Left) as .mhd files
        12. PCL (Left) as .mhd files

**STLs - Surface geometries as triangulated surface meshes used for creation of models and original tracked data**

1.  Aligned CT Scan STLs - Geometries of the bones aligned to standard coordinate systems (aligned axis and origin) based on recommendations from Grood and Suntay, 1984, *A joint coordinate system for the clinical description of three-dimensional motions: application to the knee*. These bones are the same as the ones in the other folder Raw CT STLs and were used to determine the original experimental kinematics of the specimen in different dynamic scenarios.

    1.  Femur (Left and Right) as .stl files
    2.  Patella (Left and Right) as .stl files
    3.  Combined Tibia and Fibula (Left and Right) as .stl files
2.  Raw CT Scan STLs  - Geometries of the bones in the original standard coordinate system of the CT Scan (aligned axis and origin). These bones are the same as the ones in the other folder Aligned CT STLs.

    1.  Femur (Left and Right) as .stl files
    2.  Patella (Left and Right) as .stl files
    3.  Combined Tibia and Fibula (Left and Right) as .stl files
3.  Raw MRI Scan STLs  - Geometries of the major bones, cartilage, ligaments, and menisci of the left knee of the specimen in the original standard coordinate system of the MRI Scan (aligned axis and origin).
    1.  Femur (Left) as .stl file
    2.  Patella (Left) as .stl file
    3.  Tibia/Fibula (Left) as .stl file
    4.  Femoral Cartilage (Left) as .stl file
    5.  Medial Tibial Cartilage (Left) as .stl file
    6.  Lateral Tibial Cartilage (Left) as .stl file
    7.  Medial Meniscus (Left) as .stl file
    8.  Lateral Meniscus (Left) as .stl file
    9.  ACL (Left) as .stl file
    10. LCL (Left) as .stl file
    11. MCL (Left) as .stl file
    12. PCL (Left) as .stl file

**Dynamics Data - Experimental measurements of applied loads and resulting motion (kinematics) of the left knee of the specimen. Degrees of freedom represented are the three rotations, namely, flexion/extension [F(+)E], varus/valgus [Vr/Vl(+)], internal/external [IE(+)] and the three translations, namely, medial/lateral [ML(+)], anterior/posterior [A(+)P], and superior/inferior [S(+)I]. The positive directions are given as: flexion, valgus, external, lateral, anterior and superior. All rotations are in degrees and all translations are in mm. When loads are applied to these directions the moments are in N*m and the loads are in N.**

1.  RKS Data - Experimental dynamics of the left knee of the specimen using a Robotic Knee Simulator (RKS)

    1.  Raw - Unprocessed data with no filters or interpolation done
        1.  PFLEX - Passive Flexion of the knee with no external loads applied and only flexion of the knee
            1.  0 - 70 degrees of knee flexion as .xlsx file
            2.  50 - 110 degrees of knee as .xlsx file
        2.  Dwell - Motion of the knee under very small anterior/posterior or internal/external loads
            1.  AP at 0 degrees of knee flexion as .xlsx file
            2.  AP at 15 degrees of knee flexion as .xlsx file
            3.  AP at 30 degrees of knee flexion as .xlsx file
            4.  AP at 45 degrees of knee flexion as .xlsx file
            5.  AP at 60 degrees of knee flexion as .xlsx file
            6.  AP at 75 degrees of knee flexion as .xlsx file
            7.  AP at 90 degrees of knee flexion as .xlsx file
            8.  AP at 105 degrees of knee flexion as .xlsx file
            9.  AP at 120 degrees of knee flexion as .xlsx file
            10. IE at 0 degrees of knee flexion as .xlsx file
            11. IE at 15 degrees of knee flexion as .xlsx file
            12. IE at 30 degrees of knee flexion as .xlsx file
            13. IE at 45 degrees of knee flexion as .xlsx file
            14. IE at 60 degrees of knee flexion as .xlsx file
            15. IE at 75 degrees of knee flexion as .xlsx file
            16. IE at 90 degrees of knee flexion as .xlsx file
            17. IE at 105 degrees of knee flexion as .xlsx file
            18. IE at 120 degrees of knee flexion as .xlsx file
        3.  AP Laxity - Motion of the knee under anterior/posterior loads
            1.  Anterior at 0 degrees of knee flexion as .xlsx file
            2.  Anterior at 15 degrees of knee flexion as .xlsx file
            3.  Anterior at 30 degrees of knee flexion as .xlsx file
            4.  Anterior at 45 degrees of knee flexion as .xlsx file
            5.  Anterior at 60 degrees of knee flexion as .xlsx file
            6.  Anterior at 75 degrees of knee flexion as .xlsx file
            7.  Anterior at 90 degrees of knee flexion as .xlsx file
            8.  Anterior at 105 degrees of knee flexion as .xlsx file
            9.  Anterior at 120 degrees of knee flexion as .xlsx file
            10. Posterior at 0 degrees of knee flexion as .xlsx file
            11. Posterior at 15 degrees of knee flexion as .xlsx file
            12. Posterior at 30 degrees of knee flexion as .xlsx file
            13. Posterior at 45 degrees of knee flexion as .xlsx file
            14. Posterior at 60 degrees of knee flexion as .xlsx file
            15. Posterior at 75 degrees of knee flexion as .xlsx file
            16. Posterior at 90 degrees of knee flexion as .xlsx file
            17. Posterior at 105 degrees of knee flexion as .xlsx file
            18. Posterior at 120 degrees of knee flexion as .xlsx file
        4.  IE Laxity - Motion of the knee under internal/external moments
            1.  Internal at 0 degrees of knee flexion as .xlsx file
            2.  Internal at 15 degrees of knee flexion as .xlsx file
            3.  Internal at 30 degrees of knee flexion as .xlsx file
            4.  Internal at 45 degrees of knee flexion as .xlsx file
            5.  Internal at 60 degrees of knee flexion as .xlsx file
            6.  Internal at 75 degrees of knee flexion as .xlsx file
            7.  Internal at 90 degrees of knee flexion as .xlsx file
            8.  Internal at 105 degrees of knee flexion as .xlsx file
            9.  Internal at 120 degrees of knee flexion as .xlsx file
            10. External at 0 degrees of knee flexion as .xlsx file
            11. External at 15 degrees of knee flexion as .xlsx file
            12. External at 30 degrees of knee flexion as .xlsx file
            13. External at 45 degrees of knee flexion as .xlsx file
            14. External at 60 degrees of knee flexion as .xlsx file
            15. External at 75 degrees of knee flexion as .xlsx file
            16. External at 90 degrees of knee flexion as .xlsx file
            17. External at 105 degrees of knee flexion as .xlsx file
            18. External at 120 degrees of knee flexion as .xlsx file
        5.  VrVl Laxity - Motion of the knee under internal/external moments
            1.  Valgus at 0 degrees of knee flexion as .xlsx file
            2.  Valgus at 15 degrees of knee flexion as .xlsx file
            3.  Valgus at 30 degrees of knee flexion as .xlsx file
            4.  Valgus at 45 degrees of knee flexion as .xlsx file
            5.  Valgus at 60 degrees of knee flexion as .xlsx file
            6.  Valgus at 75 degrees of knee flexion as .xlsx file
            7.  Valgus at 90 degrees of knee flexion as .xlsx file
            8.  Valgus at 105 degrees of knee flexion as .xlsx file
            9.  Valgus at 120 degrees of knee flexion as .xlsx file
            10. Varus at 0 degrees of knee flexion as .xlsx file
            11. Varus at 15 degrees of knee flexion as .xlsx file
            12. Varus at 30 degrees of knee flexion as .xlsx file
            13. Varus at 45 degrees of knee flexion as .xlsx file
            14. Varus at 60 degrees of knee flexion as .xlsx file
            15. Varus at 75 degrees of knee flexion as .xlsx file
            16. Varus at 90 degrees of knee flexion as .xlsx file
            17. Varus at 105 degrees of knee flexion as .xlsx file
            18. Varus at 120 degrees of knee flexion as .xlsx file
    2.  Filtered - Processed data with low-pass Butterworth filter and uniform time spacing interpolation done
        1.  PFLEX - Passive Flexion of the knee with no external loads applied and only flexion of the knee
            1.  0 - 70 degrees of knee flexion as .xlsx file
            2.  50 - 110 degrees of knee as .xlsx file
        2.  Dwell - Motion of the knee under very small anterior/posterior or internal/external loads
            1.  AP at 0 degrees of knee flexion as .xlsx file
            2.  AP at 15 degrees of knee flexion as .xlsx file
            3.  AP at 30 degrees of knee flexion as .xlsx file
            4.  AP at 45 degrees of knee flexion as .xlsx file
            5.  AP at 60 degrees of knee flexion as .xlsx file
            6.  AP at 75 degrees of knee flexion as .xlsx file
            7.  AP at 90 degrees of knee flexion as .xlsx file
            8.  AP at 105 degrees of knee flexion as .xlsx file
            9.  AP at 120 degrees of knee flexion as .xlsx file
            10. IE at 0 degrees of knee flexion as .xlsx file
            11. IE at 15 degrees of knee flexion as .xlsx file
            12. IE at 30 degrees of knee flexion as .xlsx file
            13. IE at 45 degrees of knee flexion as .xlsx file
            14. IE at 60 degrees of knee flexion as .xlsx file
            15. IE at 75 degrees of knee flexion as .xlsx file
            16. IE at 90 degrees of knee flexion as .xlsx file
            17. IE at 105 degrees of knee flexion as .xlsx file
            18. IE at 120 degrees of knee flexion as .xlsx file
        3.  AP Laxity - Motion of the knee under anterior/posterior loads
            1.  Anterior at 0 degrees of knee flexion as .xlsx file
            2.  Anterior at 15 degrees of knee flexion as .xlsx file
            3.  Anterior at 30 degrees of knee flexion as .xlsx file
            4.  Anterior at 45 degrees of knee flexion as .xlsx file
            5.  Anterior at 60 degrees of knee flexion as .xlsx file
            6.  Anterior at 75 degrees of knee flexion as .xlsx file
            7.  Anterior at 90 degrees of knee flexion as .xlsx file
            8.  Anterior at 105 degrees of knee flexion as .xlsx file
            9.  Anterior at 120 degrees of knee flexion as .xlsx file
            10. Posterior at 0 degrees of knee flexion as .xlsx file
            11. Posterior at 15 degrees of knee flexion as .xlsx file
            12. Posterior at 30 degrees of knee flexion as .xlsx file
            13. Posterior at 45 degrees of knee flexion as .xlsx file
            14. Posterior at 60 degrees of knee flexion as .xlsx file
            15. Posterior at 75 degrees of knee flexion as .xlsx file
            16. Posterior at 90 degrees of knee flexion as .xlsx file
            17. Posterior at 105 degrees of knee flexion as .xlsx file
            18. Posterior at 120 degrees of knee flexion as .xlsx file
        4.  IE Laxity - Motion of the knee under internal/external moments
            1.  Internal at 0 degrees of knee flexion as .xlsx file
            2.  Internal at 15 degrees of knee flexion as .xlsx file
            3.  Internal at 30 degrees of knee flexion as .xlsx file
            4.  Internal at 45 degrees of knee flexion as .xlsx file
            5.  Internal at 60 degrees of knee flexion as .xlsx file
            6.  Internal at 75 degrees of knee flexion as .xlsx file
            7.  Internal at 90 degrees of knee flexion as .xlsx file
            8.  Internal at 105 degrees of knee flexion as .xlsx file
            9.  Internal at 120 degrees of knee flexion as .xlsx file
            10. External at 0 degrees of knee flexion as .xlsx file
            11. External at 15 degrees of knee flexion as .xlsx file
            12. External at 30 degrees of knee flexion as .xlsx file
            13. External at 45 degrees of knee flexion as .xlsx file
            14. External at 60 degrees of knee flexion as .xlsx file
            15. External at 75 degrees of knee flexion as .xlsx file
            16. External at 90 degrees of knee flexion as .xlsx file
            17. External at 105 degrees of knee flexion as .xlsx file
            18. External at 120 degrees of knee flexion as .xlsx file
        5.  VrVl Laxity - Motion of the knee under internal/external moments
            1.  Valgus at 0 degrees of knee flexion as .xlsx file
            2.  Valgus at 15 degrees of knee flexion as .xlsx file
            3.  Valgus at 30 degrees of knee flexion as .xlsx file
            4.  Valgus at 45 degrees of knee flexion as .xlsx file
            5.  Valgus at 60 degrees of knee flexion as .xlsx file
            6.  Valgus at 75 degrees of knee flexion as .xlsx file
            7.  Valgus at 90 degrees of knee flexion as .xlsx file
            8.  Valgus at 105 degrees of knee flexion as .xlsx file
            9.  Valgus at 120 degrees of knee flexion as .xlsx file
            10. Varus at 0 degrees of knee flexion as .xlsx file
            11. Varus at 15 degrees of knee flexion as .xlsx file
            12. Varus at 30 degrees of knee flexion as .xlsx file
            13. Varus at 45 degrees of knee flexion as .xlsx file
            14. Varus at 60 degrees of knee flexion as .xlsx file
            15. Varus at 75 degrees of knee flexion as .xlsx file
            16. Varus at 90 degrees of knee flexion as .xlsx file
            17. Varus at 105 degrees of knee flexion as .xlsx file
            18. Varus at 120 degrees of knee flexion as .xlsx file
    3.  Processed Data Targets - Chosen subset of data points (corresponding kinematics and loads) from maximum values of specific .xlsx files. Values include kinematics in Grood and Suntay Clinical and Cylindricial joint coordinate system. Steps are values for kinematics based on the initial position of the knee in the model configuration based on the MRI position of the knee.
        1.  Processed laxity targets as matlab structure array as .mat file
    4.  Input Files - Specific input files containing the chosen loads to apply to the model and the overall model definition for use in Abaqus Explicit model. All files are the corresponding values matching the targets given as rows in the structure array in the Processed Data Target file.
        1.  Amplitude and Main input file for Anterior knee laxity test at 0 degrees of knee flexion as .inp file
        2.  Amplitude and Main input file for Anterior knee laxity test at 30 degrees of knee flexion as .inp file
        3.  Amplitude and Main input file for Anterior knee laxity test at 60 degrees of knee flexion as .inp file
        4.  Amplitude and Main input file for Anterior knee laxity test at 90 degrees of knee flexion as .inp file
        5.  Amplitude and Main input file for Posterior knee laxity test at 0 degrees of knee flexion as .inp file
        6.  Amplitude and Main input file for Posterior knee laxity test at 30 degrees of knee flexion as .inp file
        7.  Amplitude and Main input file for Posterior knee laxity test at 60 degrees of knee flexion as .inp file
        8.  Amplitude and Main input file for Posterior knee laxity test at 90 degrees of knee flexion as .inp file
        9.  Amplitude and Main input file for Internal knee laxity test at 0 degrees of knee flexion as .inp file
        10. Amplitude and Main input file for Internal knee laxity test at 30 degrees of knee flexion as .inp file
        11. Amplitude and Main input file for Internal knee laxity test at 60 degrees of knee flexion as .inp file
        12. Amplitude and Main input file for Internal knee laxity test at 90 degrees of knee flexion as .inp file
        13. Amplitude and Main input file for External knee laxity test at 0 degrees of knee flexion as .inp file
        14. Amplitude and Main input file for External knee laxity test at 30 degrees of knee flexion as .inp file
        15. Amplitude and Main input file for External knee laxity test at 60 degrees of knee flexion as .inp file
        16. Amplitude and Main input file for External knee laxity test at 90 degrees of knee flexion as .inp file
        17. Amplitude and Main input file for Varus knee laxity test at 0 degrees of knee flexion as .inp file
        18. Amplitude and Main input file for Varus knee laxity test at 30 degrees of knee flexion as .inp file
        19. Amplitude and Main input file for Varus knee laxity test at 60 degrees of knee flexion as .inp file
        20. Amplitude and Main input file for Varus knee laxity test at 90 degrees of knee flexion as .inp file
        21. Amplitude and Main input file for Valgus knee laxity test at 0 degrees of knee flexion as .inp file
        22. Amplitude and Main input file for Valgus knee laxity test at 30 degrees of knee flexion as .inp file
        23. Amplitude and Main input file for Valgus knee laxity test at 60 degrees of knee flexion as .inp file
        24. Amplitude and Main input file for Valgus knee laxity test at 90 degrees of knee flexion as .inp file
        25. Amplitude and Main input file for Full extension position of the knee as .inp file
2.  KLA Data - Experimental dynamics of the left knee of the specimen using the Knee Laxity Apparatus (KLA)

    1.  Raw - Unprocessed data with no filters or interpolation done
        1.  AP Laxity - Motion of the knee under anterior/posterior loads
            1.  Anterior at 0 lbs at 0 degrees of knee flexion as .xlsx file
            2.  Anterior at 0 lbs at 30 degrees of knee flexion as .xlsx file
            3.  Anterior at 10 lbs at 30 degrees of knee flexion as .xlsx file
            4.  Anterior at 20 lbs at 30 degrees of knee flexion as .xlsx file
            5.  Anterior at 30 lbs at 30 degrees of knee flexion as .xlsx file
            6.  Anterior at 40 lbs at 30 degrees of knee flexion as .xlsx file
            7.  Posterior at 0 lbs at 30 degrees of knee flexion as .xlsx file
            8.  Posterior at 10 lbs at 30 degrees of knee flexion as .xlsx file
            9.  Posterior at 20 lbs at 30 degrees of knee flexion as .xlsx file
            10. Posterior at 30 lbs at 30 degrees of knee flexion as .xlsx file
            11. Posterior at 40 lbs at 30 degrees of knee flexion as .xlsx file
            12. Anterior at 0 lbs at 90 degrees of knee flexion as .xlsx file
            13. Anterior at 10 lbs at 90 degrees of knee flexion as .xlsx file
            14. Anterior at 20 lbs at 90 degrees of knee flexion as .xlsx file
            15. Anterior at 30 lbs at 90 degrees of knee flexion as .xlsx file
            16. Anterior at 40 lbs at 90 degrees of knee flexion as .xlsx file
            17. Posterior at 0 lbs at 90 degrees of knee flexion as .xlsx file
            18. Posterior at 10 lbs at 90 degrees of knee flexion as .xlsx file
            19. Posterior at 20 lbs at 90 degrees of knee flexion as .xlsx file
            20. Posterior at 30 lbs at 90 degrees of knee flexion as .xlsx file
            21. Posterior at 40 lbs at 90 degrees of knee flexion as .xlsx file
            22. Anterior at varying lbs at 30 degrees of knee flexion as .xslx file
        2.  IE Laxity - Motion of the knee under internal/external loads
            1.  External at 0 lbs at 30 degrees of knee flexion as .xlsx file
            2.  External at 5 lbs at 30 degrees of knee flexion as .xlsx file
            3.  External at 10 lbs at 30 degrees of knee flexion as .xlsx file
            4.  External at 15 lbs at 30 degrees of knee flexion as .xlsx file
            5.  External at 20 lbs at 30 degrees of knee flexion as .xlsx file
            6.  Internal at 0 lbs at 30 degrees of knee flexion as .xlsx file
            7.  Internal at 5 lbs at 30 degrees of knee flexion as .xlsx file
            8.  Internal at 10 lbs at 30 degrees of knee flexion as .xlsx file
            9.  Internal at 15 lbs at 30 degrees of knee flexion as .xlsx file
            10. Internal at 20 lbs at 30 degrees of knee flexion as .xlsx file
            11. External at 5 lbs at 90 degrees of knee flexion as .xlsx file
            12. External at 10 lbs at 90 degrees of knee flexion as .xlsx file
            13. External at 15 lbs at 90 degrees of knee flexion as .xlsx file
            14. External at 20 lbs at 90 degrees of knee flexion as .xlsx file
            15. Internal at 0 lbs at 90 degrees of knee flexion as .xlsx file
            16. Internal at 5 lbs at 90 degrees of knee flexion as .xlsx file
            17. Internal at 10 lbs at 90 degrees of knee flexion as .xlsx file
            18. Internal at 15 lbs at 90 degrees of knee flexion as .xlsx file
            19. Internal at 20 lbs at 90 degrees of knee flexion as .xlsx file
            20. External at varying lbs at 30 degrees of knee flexion as .xlsx
            21. External at varying lbs at 90 degrees of knee flexion as .xlsx
            22. Internal at varying lbs at 30 degrees of knee flexion as .xlsx
            23. Internal at varying lbs at 90 degrees of knee flexion as .xlsx
    2.  Processed Data Targets - Chosen subset of data points (corresponding kinematics and loads) from maximum values of specific .xlsx files. Values include kinematics in Grood and Suntay Clinical and Cylindricial joint coordinate system. Steps are values for kinematics based on the initial position of the knee in the model configuration based on the MRI position of the knee.
        1.  Processed laxity targets as matlab structure array as .mat file
        2.  Original laxity targets as matlab structure array with no offsets to base position as .mat file
    3.  Input Files - Specific input files containing the chosen loads to apply to the model and the overall model definition for use in Abaqus Explicit model. All files are the corresponding values matching the targets given as rows in the structure array in the Processed Data Target file.
        1.  Amplitude and Main input file for Anterior at 0 lbs at 0 degrees of knee flexion as .inp file
        2.  Amplitude and Main input file for Anterior at 0 lbs at 30 degrees of knee flexion as .inp file
        3.  Amplitude and Main input file for Anterior at 10 lbs at 30 degrees of knee flexion as .inp file
        4.  Amplitude and Main input file for Anterior at 20 lbs at 30 degrees of knee flexion as .inp file
        5.  Amplitude and Main input file for Anterior at 30 lbs at 30 degrees of knee flexion as .inp file
        6.  Amplitude and Main input file for Anterior at 40 lbs at 30 degrees of knee flexion as .inp file
        7.  Amplitude and Main input file for Anterior at 0 lbs at 90 degrees of knee flexion as .inp file
        8.  Amplitude and Main input file for Anterior at 10 lbs at 90 degrees of knee flexion as .inp file
        9.  Amplitude and Main input file for Anterior at 20 lbs at 90 degrees of knee flexion as .inp file
        10. Amplitude and Main input file for Anterior at 30 lbs at 90 degrees of knee flexion as .inp file
        11. Amplitude and Main input file for Anterior at 40 lbs at 90 degrees of knee flexion as .inp file
        12. Amplitude and Main input file for External at 0 lbs at 30 degrees of knee flexion as .inp file
        13. Amplitude and Main input file for External at 5 lbs at 30 degrees of knee flexion as .inp file
        14. Amplitude and Main input file for External at 10 lbs at 30 degrees of knee flexion as .inp file
        15. Amplitude and Main input file for External at 15 lbs at 30 degrees of knee flexion as .inp file
        16. Amplitude and Main input file for External at 20 lbs at 30 degrees of knee flexion as .inp file
        17. Amplitude and Main input file for Internal at 0 lbs at 30 degrees of knee flexion as .inp file
        18. Amplitude and Main input file for Internal at 5 lbs at 30 degrees of knee flexion as .inp file
        19. Amplitude and Main input file for Internal at 10 lbs at 30 degrees of knee flexion as .inp file
        20. Amplitude and Main input file for Internal at 15 lbs at 30 degrees of knee flexion as .inp file
        21. Amplitude and Main input file for Internal at 20 lbs at 30 degrees of knee flexion as .inp file
        22. Amplitude and Main input file for External at 0 lbs at 90 degrees of knee flexion as .inp file
        23. Amplitude and Main input file for External at 5 lbs at 90 degrees of knee flexion as .inp file
        24. Amplitude and Main input file for External at 10 lbs at 90 degrees of knee flexion as .inp file
        25. Amplitude and Main input file for External at 15 lbs at 90 degrees of knee flexion as .inp file
        26. Amplitude and Main input file for External at 20 lbs at 90 degrees of knee flexion as .inp file
        27. Amplitude and Main input file for Internal at 0 lbs at 90 degrees of knee flexion as .inp file
        28. Amplitude and Main input file for Internal at 5 lbs at 90 degrees of knee flexion as .inp file
        29. Amplitude and Main input file for Internal at 10 lbs at 90 degrees of knee flexion as .inp file
        30. Amplitude and Main input file for Internal at 15 lbs at 90 degrees of knee flexion as .inp file
        31. Amplitude and Main input file for Internal at 20 lbs at 90 degrees of knee flexion as .inp file

**Working Models - Working models for Abaqus Explicit Analysis as well as code used to optimize ligament parameters. The model files included are unique geometries and material properties for this specimen. However, all model definitionsbasic layout and description of files are described in more detail in the related KneeHub project for the Team DU models.**

1.  CTS-KLA - Abaqus model and optimization code for optimization of ligament parameters of model to match simulated laxity targets with experimental measurements. Geometries are taken from the STLs in the CTS datasets. Experimental data targets are taken from the KLA dataset.
    1.  Abaqus Input Files - Complete Abaqus Explicit model for all simulated laxity targets. Files included are all of the Abaqus input files for the amplitudes and main files in the KLA Input file folder, as well as geometry, material properties, coordinate system definitions, and output request input files. The models can be run by running one of the Abaqus input files with "MAIN" in it through the command terminal using the "abaqus" batch command. Descriptions of the input files included are given in the original manuscript submitted to the Journal of Biomechanical Engineering.
    2.  Optimization - Complete set of code used to perform optimization of a given model set. All files included are matlab .m files and experimental parameters for calibrations are included based on previous .mat files from processed results folder for the KLA data. The main function is the "LigCalibration_Wrapper.m".
    3.  Python - Complete set of code used to extract important values from the simulated Abaqus Explicit models. File are pythons scripts that use Abaqus API to extract important results from odb files.
    4.  Optimization Full - Complete optimization code including all files from the previous 3 folders. This is necessary to perform the optimization. The main function is the "LigCalibration_Wrapper.m". Chosen target files to include in the optimization are given in the JOBLIST and JOBName files. To run the optimization, the LigCalibration_Wrapper.m file is run, and runs the jobs in the JOBLIST and JOBNAME files. Results from the simulations are extracted using the python scripts and then values are compared against the experimental values in the .mat processed data file. Optimization uses Simplex and Particle Swarm to update the ligament reference strains and stiffnesses in the LIG-PARAMETERS input files. Multiple versions of this file are include to show the progression of the optimization from initial values form literature to specimen-specific values obtained from the optimization of simulated to experimental dynamics.
2.  CTS-RKS - Abaqus model and optimization code for optimization of ligament parameters of model to match simulated laxity targets with experimental measurements. Geometries are taken from the STLs in the CTS datasets. Experimental data targets are taken from the RKS dataset.
    1.  Abaqus Input Files - Complete Abaqus Explicit model for all simulated laxity targets. Files included are all of the Abaqus input files for the amplitudes and main files in the RKS Input file folder, as well as geometry, material properties, coordinate system definitions, and output request input files. The models can be run by running one of the Abaqus input files with "MAIN" in it through the command terminal using the "abaqus" batch command. Descriptions of the input files included are given in the original manuscript submitted to the Journal of Biomechanical Engineering.
    2.  Optimization - Complete set of code used to perform optimization of a given model set. All files included are matlab .m files and experimental parameters for calibrations are included based on previous .mat files from processed results folder for the RKS data. The main function is the "LigCalibration_Wrapper.m".
    3.  Python - Complete set of code used to extract important values from the simulated Abaqus Explicit models. File are pythons scripts that use Abaqus API to extract important results from odb files.
    4.  Optimization Full - Complete optimization code including all files from the previous 3 folders. This is necessary to perform the optimization. The main function is the "LigCalibration_Wrapper.m". Chosen target files to include in the optimization are given in the JOBLIST and JOBName files. To run the optimization, the LigCalibration_Wrapper.m file is run, and runs the jobs in the JOBLIST and JOBNAME files. Results from the simulations are extracted using the python scripts and then values are compared against the experimental values in the .mat processed data file. Optimization uses Simplex and Particle Swarm to update the ligament reference strains and stiffnesses in the LIG-PARAMETERS input files. Multiple versions of this file are include to show the progression of the optimization from initial values form literature to specimen-specific values obtained from the optimization of simulated to experimental dynamics.
3.  MRI-KLA - Abaqus model and optimization code for optimization of ligament parameters of model to match simulated laxity targets with experimental measurements. Geometries are taken from the STLs in the MRI datasets. Experimental data targets are taken from the KLA dataset.
    1.  Abaqus Input Files - Complete Abaqus Explicit model for all simulated laxity targets. Files included are all of the Abaqus input files for the amplitudes and main files in the KLA Input file folder, as well as geometry, material properties, coordinate system definitions, and output request input files. The models can be run by running one of the Abaqus input files with "MAIN" in it through the command terminal using the "abaqus" batch command. Descriptions of the input files included are given in the original manuscript submitted to the Journal of Biomechanical Engineering.
    2.  Optimization - Complete set of code used to perform optimization of a given model set. All files included are matlab .m files and experimental parameters for calibrations are included based on previous .mat files from processed results folder for the KLA data. The main function is the "LigCalibration_Wrapper.m".
    3.  Python - Complete set of code used to extract important values from the simulated Abaqus Explicit models. File are pythons scripts that use Abaqus API to extract important results from odb files.
    4.  Optimization Full - Complete optimization code including all files from the previous 3 folders. This is necessary to perform the optimization. The main function is the "LigCalibration_Wrapper.m". Chosen target files to include in the optimization are given in the JOBLIST and JOBName files. To run the optimization, the LigCalibration_Wrapper.m file is run, and runs the jobs in the JOBLIST and JOBNAME files. Results from the simulations are extracted using the python scripts and then values are compared against the experimental values in the .mat processed data file. Optimization uses Simplex and Particle Swarm to update the ligament reference strains and stiffnesses in the LIG-PARAMETERS input files. Multiple versions of this file are include to show the progression of the optimization from initial values form literature to specimen-specific values obtained from the optimization of simulated to experimental dynamics.

\**Processing Code - Code used to process results of Abaqus model simulation .odb files. Files contain python scripts to access odb results and extract important values as .csv and .mat files. MATLAB scripts are used to run python scripts in turn for a given odb file and plot important results for each file. **

1.  CTS-KLA - Complete set of processing code for CTS-KLA models. Python scripts are used to get the outputs for contact, ligament connector forces, and force and displacement kinematics of the bones based on rigid body node motion. The main MATLAB script is called "get_ODB_Step_Info.m". This function is given an ODB and the type of motion (Flexion or Laxity), and the corresponding step of interest and DOF of interest. The function calls the appropriate Python scripts and MATLAB functions to calculate important values for the current simulation. The "Tibia_Cart.mat" file contains the specific medial and lateral tibial cartilage geometries to allow for the center of pressure to be calculated for these models.
2.  CTS-RKS - Complete set of processing code for CTS-KLA models. Python scripts are used to get the outputs for contact, ligament connector forces, and force and displacement kinematics of the bones based on rigid body node motion. The main MATLAB script is called "get_ODB_Step_Info.m". This function is given an ODB and the type of motion (Flexion or Laxity), and the corresponding step of interest and DOF of interest. The function calls the appropriate Python scripts and MATLAB functions to calculate important values for the current simulation. The "Tibia_Cart.mat" file contains the specific medial and lateral tibial cartilage geometries to allow for the center of pressure to be calculated for these models.
3.  MRI-KLA - Complete set of processing code for CTS-KLA models. Python scripts are used to get the outputs for contact, ligament connector forces, and force and displacement kinematics of the bones based on rigid body node motion. The main MATLAB script is called "get_ODB_Step_Info.m". This function is given an ODB and the type of motion (Flexion or Laxity), and the corresponding step of interest and DOF of interest. The function calls the appropriate Python scripts and MATLAB functions to calculate important values for the current simulation. The "Tibia_Cart.mat" file contains the specific medial and lateral tibial cartilage geometries to allow for the center of pressure to be calculated for these models.

**Results - Simulation results for each model from test scenarios used in the manuscript. Results include contact load, Grood and Suntay dynamics, ligament forces as individual fiber loads, and combined bundle loads, and contact area. Results were obtained using the "get_ODB_Step_Info.m" script in the processing code for each individual trial. All files contain units within the headers of the corresponding column. Ligament loads are given by the name of the ligament fiber and the units are in Newtons.**

1.  CTS-KLA - Results for Anterior laxity tests at 133N at 30 degrees, 60 degrees, and 90 degrees for the CTS-KLA knee models. Additional results are included for the simulated passive flexion motion.
    1.  CSV - Results in .csv format
    2.  MAT - Results in .mat format
2.  CTS-RKS -  Results for Anterior laxity tests at 133N at 30 degrees, 60 degrees, and 90 degrees for the CTS-KLA knee models. Additional results are included for the simulated passive flexion motion. Additional laxity tests are included for AP, IE, and VrVl laxity tests at 30 degrees and 90 degrees of knee flexion.
    1.  CSV - Results in .csv format
    2.  MAT - Results in .mat format
3.  MRI-KLA Results for Anterior laxity tests at 133N at 30 degrees, 60 degrees, and 90 degrees for the CTS-KLA knee models. Additional results are included for the simulated passive flexion motion.
    1.  CSV - Results in .csv format
    2.  MAT - Results in .mat format

**Aligned Model - Aligned model in HyperMesh model file including all alignment of MRI and CT geometries to one another from various imaging modalities. Files include resulting ligament fibers, hexahedral mesh geometries for cartilage, and rigid body nodes.**

1.  S192803_FE_CTS_build.hm - All geometries from the CT images and surface scans used to create the CTS models.
2.  S192803_FE_MRI_build.hm - All geometries from the CT images and surface scans used to create the MRI model.