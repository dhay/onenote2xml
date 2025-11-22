#!/bin/bash

# Script to convert OneNote .one files to ENEX format
# Preserves directory structure from backup to output directory

set -e  # Exit on error

# Function to detect platform and find default backup directory
detect_backup_dir() {
    local platform=$(uname -s)

    case "$platform" in
        Darwin)
            # macOS
            local base_dir="$HOME/Library/Containers/com.microsoft.onenote.mac/Data/Library/Application Support/Microsoft User Data/OneNote"

            # Find the most recent version directory
            if [ -d "$base_dir" ]; then
                # Look for version directories (e.g., 16.0, 15.0) and get the most recent
                local version_dir=$(find "$base_dir" -maxdepth 1 -type d -name "[0-9]*" | sort -V | tail -1)

                if [ -n "$version_dir" ] && [ -d "$version_dir/Backup" ]; then
                    echo "$version_dir/Backup"
                    return 0
                fi
            fi
            ;;
        MINGW*|MSYS*|CYGWIN*)
            # Windows (Git Bash, MSYS2, Cygwin)
            local base_dir="$LOCALAPPDATA/Microsoft/OneNote"

            if [ -d "$base_dir" ]; then
                # Look for version directories and get the most recent
                local version_dir=$(find "$base_dir" -maxdepth 1 -type d -name "[0-9]*" 2>/dev/null | sort -V | tail -1)

                if [ -n "$version_dir" ] && [ -d "$version_dir/Backup" ]; then
                    echo "$version_dir/Backup"
                    return 0
                fi
            fi
            ;;
    esac

    # No default found
    return 1
}

# Function to display usage
usage() {
    local default_backup=$(detect_backup_dir 2>/dev/null || echo "None detected")

    cat << EOF
Usage: $0 [-b BACKUP_DIR] -o OUTPUT_DIR

Convert all .one files in BACKUP_DIR to .enex files in OUTPUT_DIR,
preserving the directory structure.

Options:
    -b BACKUP_DIR    Path to OneNote backup directory containing .one files
                     (Optional: auto-detected if not specified)
                     Default: $default_backup
    -o OUTPUT_DIR    Path to output directory for .enex files (Required)
    -h               Display this help message

Platform-specific default backup directories:
    macOS:   ~/Library/Containers/com.microsoft.onenote.mac/Data/Library/
             Application Support/Microsoft User Data/OneNote/<version>/Backup
    Windows: %LOCALAPPDATA%\\Microsoft\\OneNote\\<version>\\Backup

Example:
    $0 -o ~/Documents/Evernote-Export
    $0 -b ~/Documents/OneNote-Backup -o ~/Documents/Evernote-Export

EOF
    exit 1
}

# Parse command line arguments
BACKUP_DIR=""
OUTPUT_DIR=""

while getopts "b:o:h" opt; do
    case $opt in
        b)
            BACKUP_DIR="$OPTARG"
            ;;
        o)
            OUTPUT_DIR="$OPTARG"
            ;;
        h)
            usage
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            usage
            ;;
    esac
done

# Auto-detect backup directory if not specified
if [ -z "$BACKUP_DIR" ]; then
    echo "No backup directory specified, attempting to auto-detect..."
    BACKUP_DIR=$(detect_backup_dir)
    if [ $? -ne 0 ] || [ -z "$BACKUP_DIR" ]; then
        echo "Error: Could not auto-detect OneNote backup directory." >&2
        echo "Please specify the backup directory with -b option." >&2
        echo "" >&2
        usage
    fi
    echo "Auto-detected backup directory: $BACKUP_DIR"
fi

# Validate output directory is specified
if [ -z "$OUTPUT_DIR" ]; then
    echo "Error: Output directory (-o) is required." >&2
    usage
fi

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory does not exist: $BACKUP_DIR" >&2
    exit 1
fi

# Create output directory if it doesn't exist
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

# Get absolute paths
BACKUP_DIR=$(cd "$BACKUP_DIR" && pwd)
OUTPUT_DIR=$(cd "$OUTPUT_DIR" && pwd)

echo "Backup directory: $BACKUP_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Find all .one files and process them
file_count=0
success_count=0
error_count=0

# Use find to locate all .one files, excluding OneNoteRecycleBin directories
while IFS= read -r -d '' one_file; do
    ((file_count++))

    # Get the relative path from backup directory
    rel_path="${one_file#$BACKUP_DIR/}"

    # Get the directory part of the relative path
    rel_dir=$(dirname "$rel_path")

    # Get the filename without extension
    filename=$(basename "$one_file" .one)

    # Create the output directory structure
    output_subdir="$OUTPUT_DIR/$rel_dir"
    mkdir -p "$output_subdir"

    # Set the output file path
    output_file="$output_subdir/$filename.enex"

    echo "[$file_count] Converting: $rel_path"
    echo "    -> $output_file"

    # Run the conversion
    if python3 1note2enex.py "$one_file" --output "$output_file" 2>&1; then
        ((success_count++))
        echo "    ✓ Success"
    else
        ((error_count++))
        echo "    ✗ Failed"
    fi
    echo ""

done < <(find "$BACKUP_DIR" -type f -name "*.one" ! -path "*/OneNote_RecycleBin/*" -print0)

# Print summary
echo "========================================="
echo "Conversion Summary"
echo "========================================="
echo "Total files found:    $file_count"
echo "Successfully converted: $success_count"
echo "Failed:                $error_count"
echo "========================================="

if [ $error_count -gt 0 ]; then
    exit 1
fi

exit 0
