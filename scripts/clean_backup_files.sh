#!/bin/bash

# Find and delete all backup (.bak) files in the repository
find . -type f -name "*.bak" -exec rm -f {} +

# Notify user of completion of backup deletion
echo "All .bak files have been removed."

# This script helps to clean up any unwanted backup files that could clutter the repository.