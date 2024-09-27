import os
import json
import sys
from openai import OpenAI
from assistant_functions import repository_assistant_tools

# Get the repository name from command-line arguments
if len(sys.argv) > 1:
    repo_name = sys.argv[1]
    branch_name = sys.argv[2] if len(sys.argv) > 2 else "main"
else:
    print("Usage: python script.py <repo_name>")
    sys.exit(1)

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
    tools=[{"type": "file_search"}] + repository_assistant_tools,
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
