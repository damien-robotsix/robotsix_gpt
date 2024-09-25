#!/bin/bash

echo "Running AI assistant to generate commit message..."
PROMPT="Commit the current changes in the repo. The commit message should follow the conventional commit format and be descriptive of the changes made."

python3 tools/run_assistant.py "$PROMPT" --no-interactive
