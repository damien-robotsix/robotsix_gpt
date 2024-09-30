#!/usr/bin/env python3
import subprocess
import json

def run_assistant(command):
    result = subprocess.run(command, shell=True, capture_output=True)
    return result.stdout.decode('utf-8')

def main():
    # Stage all changes for commit
    subprocess.run(['git', 'add', '.'])
    print("Running AI assistant to generate commit message...")
    
    # Run AI Assistant to generate a commit message
    run_assistant("python3 tools/user_utility/run_assistant.py 'commit' --no-interactive --assistant 'commit'")
    
    # Path to the JSON file containing assistant's output
    json_file = "/tmp/assistant_output.txt"
    
    # Extract commit subject and body from the JSON file
    with open(json_file, 'r') as file:
        data = json.load(file)
        subject = data['subject']
        body = data['body']
    
    # Commit using the extracted subject and body
    subprocess.run(['git', 'commit', '-m', subject, '-m', body])

if __name__ == '__main__':
    main()
