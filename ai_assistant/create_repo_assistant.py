import os
import json
from openai import OpenAI

# Function to ensure entries in .gitignore

def ensure_gitignore_entries(entries):
    gitignore_path = '.gitignore'
    # Read the current contents of .gitignore
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as file:
            gitignore_contents = file.read()
    else:
        gitignore_contents = ''

    # Split by lines
    gitignore_lines = gitignore_contents.split('\n')

    # Check and add missing entries
    for entry in entries:
        if entry not in gitignore_lines:
            gitignore_lines.append(entry)

    # Write back the updated contents
    with open(gitignore_path, 'w') as file:
        file.write('\n'.join(gitignore_lines) + '\n')

# Main function to initialize the repo assistant

def main():
    # Get the repository name from the current directory
    repo_name = os.path.basename(os.getcwd())
    branch_name = "main"

    # Set your OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
    client = OpenAI(api_key=api_key)

    # Create a vector store for the repository files
    vector_store = client.beta.vector_stores.create(name=f"{repo_name}-{branch_name} files")

    # Extract the vector store ID
    vector_store_id = vector_store.id

    # Define the assistant's name and instructions
    name = f"{repo_name}-{branch_name} repository agent"

    # Create the assistant
    response = client.beta.assistants.create(
        name=name,
        model="gpt-4o-mini-2024-07-18",
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
    )

    # Extract the assistant ID
    assistant_id = response.id

    # Save the assistant ID to a JSON configuration file
    config = {
        "repo_assistant_id": assistant_id,
        "repo_vector_store_id": vector_store_id,
    }

    with open('repo_assistant_config.json', 'w') as f:
        json.dump(config, f, indent=4)

    # Ensure .gitignore contains required entries
    ensure_gitignore_entries(['assistant_gpt.log', 'repo_assistant_config.json'])

if __name__ == "__main__":
    main()
