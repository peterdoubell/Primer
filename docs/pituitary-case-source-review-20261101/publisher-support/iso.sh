#!/bin/bash

# Source directory where files are located
source_directory=""

# Loop through each file in the source directory
for input_image in "$source_directory"*_T1_biascorr.nii.gz; do
    # Extract the ID from the file name
    id=$(basename "$input_image" _T1_biascorr.nii.gz)

    # Output image name
    output_image="${source_directory}${id}_T1_iso.nii.gz"

    # Run the flirt command
    flirt -in "$input_image" -ref "$input_image" -applyisoxfm 0.5 -out "$output_image"
    echo "${id} complete"
done
