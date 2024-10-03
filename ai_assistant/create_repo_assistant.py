# Copyright 2024 Damien Six (six.damien@robotsix.net)
# SPDX-License-Identifier: Apache-2.0

import os
import json
from openai import OpenAI
import subprocess

# Function to ensure entries in .gitignore

def ensure_gitignore_entries(entries):
    """
    Ensure that the given entries are present in the .gitignore file.
    If .gitignore doesn't exist, create it with the provided entries.
    """
    gitignore_path = '.gitignore'
    
    # Read the current contents of .gitignore
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as file:
            gitignore_contents = file.read()
    else:
        gitignore_contents = ''

    # Convert contents to a list of lines
    gitignore_lines = gitignore_contents.split('\n')

    # Append missing entries to the list
    for entry in entries:
        if entry not in gitignore_lines:
            gitignore_lines.append(entry)

    # Write the updated lines back to .gitignore
    with open(gitignore_path, 'w') as file:
        file.write('\n'.join(gitignore_lines) + '\n')

# Function to determine current git branch

def get_current_branch():
    """
    Detects if the script is inside a Git repository and returns the current branch name.
    Raises an error if not inside a Git repository.
    """
    try:
        branch_name = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')
    except subprocess.CalledProcessError:
        raise RuntimeError('Not inside a Git repository')
    return branch_name

# Function to find the root of the git repository

def find_git_root(path):
    """
    Traverse upwards from the given path to find the root directory of the current Git repository.
    Raises an error if no .git directory is found.
    """
    previous, current = None, os.path.abspath(path)
    while current != previous:
        if os.path.isdir(os.path.join(current, '.git')):
            return current
        previous, current = current, os.path.abspath(os.path.join(current, os.pardir))
    raise RuntimeError('Not inside a Git repository')

# Main function to initialize the repo assistant

def main():
    """
    Main routine to set up the repository assistant. Ensures we're inside a Git repository,
    obtains the repository name and branch, sets the OpenAI API key, and creates both a vector store
    and an assistant. Saves the configuration to a JSON file and updates the .gitignore file.
    """
    # Ensure the script is being run inside a git repository
    repo_root = find_git_root(os.getcwd())
    os.chdir(repo_root)

    # Get the repository name from the directory name
    repo_name = os.path.basename(repo_root)

    # Automatically detect the current branch
    branch_name = get_current_branch()

    # Initialize OpenAI client with API key
    api_key = os.environ.get('OPENAI_API_KEY', '<your OpenAI API key if not set as env var>')
    client = OpenAI(api_key=api_key)

    # Create a vector store in OpenAI for repo files
    vector_store = client.beta.vector_stores.create(name=f'{repo_name}-{branch_name} files')

    # Extract the vector store ID
    vector_store_id = vector_store.id

    # Define the assistant's name and instructions
    name = f'{repo_name}-{branch_name} repository agent'

    # Create the assistant associated with the vector store
    response = client.beta.assistants.create(
        name=name,
        model='gpt-4o-mini-2024-07-18',
        tools=[{'type': 'file_search'}],
        tool_resources={'file_search': {'vector_store_ids': [vector_store_id]}}
    )

    # Extract the assistant ID
    assistant_id = response.id

    # Save the assistant ID to a configuration file
    config = {
        'repo_assistant_id': assistant_id,
        'repo_vector_store_id': vector_store_id,
    }

    with open('repo_assistant_config.json', 'w') as f:
        json.dump(config, f, indent=4)

    # Call scripts to update vector store and assistant
    subprocess.call(['ai_update_files', os.getcwd()])
    subprocess.call(['ai_update_assistant', os.getcwd()])

    # Ensure .gitignore contains required entries
    ensure_gitignore_entries(['assistant_gpt.log', 'repo_assistant_config.json'])

if __name__ == '__main__':
    main()
