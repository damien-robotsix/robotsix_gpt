#!/bin/bash

echo "Running AI assistant to generate commit message..."
PROMPT="Commit the current changes in the repo. Gather details on the changes if needed. You can ignore assistant_config.json. The commit message should follow the conventional commit format."

python3 tools/run_assistant.py "$PROMPT" --no-interactive
