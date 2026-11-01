#!/bin/bash

directory=""

# Variables
subject=""

# Input and output image paths
T1=".nii.gz"
T2=".nii.gz"
tumour="tumour.nii.gz"
carotids="carotids.nii.gz"

resample.sh "$directory/$subject/$T1" "$directory/$subject/${subject}_T1.nii.gz" 'false'
# resample.sh "$directory/$subject/$tumour" "$directory/$subject/${subject}_tumour.nii.gz" 'true'
# resample.sh "$directory/$subject/$carotids" "$directory/$subject/${subject}_carotids.nii.gz" 'true'


# Check if T2 file exists before running the second resample script
if [ -f "$directory/$subject/$T2" ]; then
    resample.sh "$directory/$subject/$T2" "$directory/$subject/${subject}_T2.nii.gz" 'false'
else 
    echo "No T2"
fi