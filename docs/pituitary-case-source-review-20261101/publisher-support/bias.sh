#!/bin/bash

# Define the path to the base directory
base_directory=""

# Read the text file containing the list of directories
while IFS= read -r directory; do
    full_directory="${base_directory}${directory}"
    echo "Processing directory: $full_directory"
    
    cd "$full_directory" || { echo "Failed to change directory to $full_directory"; exit 1; }
    
    # Run the fsl_anat command, substituting the {directory} placeholder with the actual directory
    fsl_anat -i "T1_raw.nii.gz" --noreorient --nocrop --noreg --nononlinreg --noseg --nosubcortseg

    # You can add additional commands here if needed

    # Rename files containing 'mpr', 'stealth', or 'STEALTH' in their filenames to 'T1_raw.nii.gz'
    for file in *; do
        if [[ "$file" =~ mpr|stealth|STEALTH ]]; then
            echo "Renaming file: $file to T1_raw.nii.gz"
            mv "$file" "T1_raw.nii.gz" || { echo "Failed to rename file"; exit 1; }
        fi
    done

    
    # Rename the file containing 'mpr' in its name to 'T1_raw.nii.gz'
    mpr_file=$(find . -maxdepth 1 -type f -name "*mpr*")
    if [ -n "$mpr_file" ]; then
        echo "Renaming file: $mpr_file to T1_raw.nii.gz"
        mv "$mpr_file" "T1_raw.nii.gz" || { echo "Failed to rename file"; exit 1; }
    else
        echo "No file with 'mpr' in its name found in directory: $full_directory"
    fi

    # Remove files ending with '.nii'
    find . -type f -name "*.nii" -delete

    # After processing, you may want to return to the base directory
    cd "$base_directory" || { echo "Failed to change directory back to $base_directory"; exit 1; }


done < "list.txt"