#!/bin/bash

# Find and delete all .bak files
find . -type f -name "*.bak" -exec rm -f {} +

echo "All .bak files have been removed."
