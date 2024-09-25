#!/bin/bash

git add .

echo "Running AI assistant to generate commit message..."
PROMPT="Use 'git status' to check the current state of the repository. Then, use 'git diff' to review changes made. Provide a detailed commit following the conventional commit format. Then, commit the changes."

python3 tools/run_assistant.py "$PROMPT" --no-interactive
