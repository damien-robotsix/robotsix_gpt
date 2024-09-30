#!/usr/bin/env python3
import subprocess
import json
import sys
import ai_assistant.run_assistant

def main():
    # Stage all changes for commit
    subprocess.run(['git', 'add', '.'])
    print("Running AI assistant to generate commit message...")
    
    # Run AI Assistant to generate a commit message
    sys.argv = ["run_assistant.py", "commit", "--no-interactive", "--assistant", "commit"]
    ai_assistant.run_assistant.main()
    
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
