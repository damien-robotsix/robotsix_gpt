#!/bin/bash

# Fetch the current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Base branch to compare against (usually main or master)
BASE_BRANCH="main"

# Function: Lists commits between current branch and base branch
list_commits() {
  # Get the commit log between the current branch and the base branch
  git log origin/$BASE_BRANCH..$CURRENT_BRANCH
}

# Function: Runs the AI assistant to generate a commit message
generate_commit_message() {
  COMMITS=$(list_commits)
  # Call the AI assistant to help with generating a commit message
  python3 tools/run_assistant.py "Branch $CURRENT_BRANCH with commits: $COMMITS" --no-interactive --assistant "commit_squash"
}

# Function: Squashes all commits on the current branch
squash_commits() {
  # Perform non-interactive squash of commits
  git fetch origin
  git reset --soft origin/$BASE_BRANCH

  # Path to the JSON file containing assistant output
  JSON_FILE="/tmp/assistant_output.txt"

  # Extract commit subject and body from the JSON file
  subject=$(jq -r '.subject' "$JSON_FILE")
  body=$(jq -r '.body' "$JSON_FILE")

  # Commit using the extracted subject and body
  git commit -m "$subject" -m "$body"
}

# Main script execution starts here
generate_commit_message
squash_commits
