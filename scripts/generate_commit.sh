#!/bin/bash

# Stage all changes for commit
git add .

# Notify user of AI assistant involvement
echo "Running AI assistant to generate commit message..."

# Run AI Assistant to generate a commit message
python3 tools/user_utility/run_assistant.py "commit" --no-interactive --assistant "commit"

# Path to the JSON file containing assistant's output
JSON_FILE="/tmp/assistant_output.txt"

# Extract commit subject and body from the JSON file
subject=$(jq -r '.subject' "$JSON_FILE")
body=$(jq -r '.body' "$JSON_FILE")

# Commit using the extracted subject and body
git commit -m "$subject" -m "$body"

# This script automates the process of staging changes, generating a commit message with AI, and then making the commit.