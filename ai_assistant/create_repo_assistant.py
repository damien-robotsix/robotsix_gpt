import os
import json
import sys
from openai import OpenAI

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

if __name__ == "__main__":
    main()