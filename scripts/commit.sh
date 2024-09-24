#!/bin/bash

# Step 1: Perform preparatory tasks
echo "Performing preparatory tasks..."
git add .
git status

# Step 2: Generate commit message using the AI assistant with the diff as context
echo "Running AI assistant to generate commit message..."
PROMPT="Commit the current changes in the repo. Here is the current git status: $GIT_STATUS. Gather extra details on the changes if needed. You can ignore assistant_config.json."

python3 tools/run_assistant.py "$PROMPT" --no-interactive

