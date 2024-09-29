#!/bin/bash

# Fetch the current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Function to run the AI assistant to generate a commit message
generate_commit_message() {
  # Run the AI assistant with a prompt to create a conventional commit message
  python3 tools/run_assistant.py "Generate a conventional commit message for squashing the branch $CURRENT_BRANCH" --no-interactive

  # Read the generated message
  COMMIT_MESSAGE=$(cat /tmp/assistant_output.txt)
}

# Squash commits on the current branch
squash_commits() {
  # Perform non-interactive squash of commits
  git fetch origin
  git reset --soft origin/main
  git commit -F /tmp/assistant_output.txt
}

# Create a pull request
create_pull_request() {
  # Push the changes after rebase and squash
  git push origin $CURRENT_BRANCH --force

  # Create a PR using GitHub CLI (assumes gh CLI is installed and authenticated)
  gh pr create --base main --head $CURRENT_BRANCH --title "$COMMIT_MESSAGE" --body ""
}

# Main script execution
generate_commit_message
squash_commits
create_pull_request

echo "Pull request from $CURRENT_BRANCH to main with squashed commit has been created."
