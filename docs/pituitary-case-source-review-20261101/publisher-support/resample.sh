#!/bin/bash

# Check if input arguments are provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 <input_image> <output_image> <is_mask>"
    echo "  - is_mask: Set to 'true' if the input image is a mask, otherwise set to 'false'"
    exit 1
fi

# Input and output image paths
input_image=$1
output_image=$2
is_mask=$3

# Resampling using FLIRT
flirt -in "$input_image" -ref "$input_image" -applyisoxfm 0.5 -out "$output_image"

if [ "$is_mask" = "true" ]; then
    # Additional processing for masks
    fslmaths "$output_image" -thr 0.9 -bin "$output_image"
fi

echo "Resampling complete."
