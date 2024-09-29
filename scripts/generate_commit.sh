#!/bin/bash

git add .

echo "Running AI assistant to generate commit message..."

python3 tools/run_assistant.py "commit" --no-interactive --assistant "commit"

# Path to your JSON file
JSON_FILE="/tmp/assistant_output.txt"

# Extract subject and body
subject=$(jq -r '.subject' "$JSON_FILE")
body=$(jq -r '.body' "$JSON_FILE")

# Commit using the extracted subject and body
git commit -m "$subject" -m "$body"
