#!/bin/bash

echo "Running AI assistant to generate commit message..."
PROMPT="Commit the current changes in the repo. The commit message should be detailled and follow the conventional commit format."

python3 tools/run_assistant.py "$PROMPT" --no-interactive
