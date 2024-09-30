#!/bin/bash

# Fetch the current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Fetch the base branch (usually main or master)
BASE_BRANCH="main"

# Fetch the commits from the branch
list_commits() {
  # Get the commit log between the current branch and the base branch
  git log origin/$BASE_BRANCH..$CURRENT_BRANCH
}

# Function to run the AI assistant to generate a commit message
generate_commit_message() {
  COMMITS=$(list_commits)
  # Call the AI assistant
  python3 tools/run_assistant.py "Branch $CURRENT_BRANCH with commits: $COMMITS" --no-interactive --assistant "commit_squash"
}

# Squash commits on the current branch
squash_commits() {
  # Perform non-interactive squash of commits
  git fetch origin
  git reset --soft origin/$BASE_BRANCH
  # Path to your JSON file
  JSON_FILE="/tmp/assistant_output.txt"

  # Extract subject and body
  subject=$(jq -r '.subject' "$JSON_FILE")
  body=$(jq -r '.body' "$JSON_FILE")

  # Commit using the extracted subject and body
  git commit -m "$subject" -m "$body"
}

# Main script execution
generate_commit_message
squash_commits
