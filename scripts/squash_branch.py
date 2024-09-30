#!/usr/bin/env python3
import subprocess
import json

def run_assistant(command):
    result = subprocess.run(command, shell=True, capture_output=True)
    return result.stdout.decode('utf-8')

def list_commits(base_branch, current_branch):
    result = subprocess.run(['git', 'log', f'origin/{base_branch}..{current_branch}'], capture_output=True)
    return result.stdout.decode('utf-8')

def generate_commit_message(base_branch, current_branch):
    commits = list_commits(base_branch, current_branch)
    command = f"python3 tools/user_utility/run_assistant.py 'Branch {current_branch} with commits: {commits}' --no-interactive --assistant 'commit_squash'"
    run_assistant(command)

def squash_commits(base_branch):
    # Perform non-interactive squash of commits
    subprocess.run(['git', 'fetch', 'origin'])
    subprocess.run(['git', 'reset', '--soft', f'origin/{base_branch}'])
    
    # Path to the JSON file containing assistant output
    json_file = "/tmp/assistant_output.txt"
    
    # Extract commit subject and body from the JSON file
    with open(json_file, 'r') as file:
        data = json.load(file)
        subject = data['subject']
        body = data['body']
    
    # Commit using the extracted subject and body
    subprocess.run(['git', 'commit', '-m', subject, '-m', body])

def main():
    current_branch = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True).stdout.strip()
    base_branch = 'main'
    generate_commit_message(base_branch, current_branch)
    squash_commits(base_branch)

if __name__ == '__main__':
    main()
