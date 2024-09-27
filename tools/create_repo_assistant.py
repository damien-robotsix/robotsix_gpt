import os
import json
import sys
from openai import OpenAI

# Get the repository name from command-line arguments
if len(sys.argv) > 1:
    repo_name = sys.argv[1]
else:
    print("Usage: python script.py <repo_name>")
    sys.exit(1)

# Set your OpenAI API key
api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
client = OpenAI(api_key=api_key)

# Define the assistant's name and instructions
name = f"{repo_name} repository agent"
instructions = """
Your role is to perform development and maintenance tasks for the repository ai_assistant. You have access to a set of repository tools that allow you to execute shell commands in the repository root and manage file contents.
"""

# Create the assistant
response = client.beta.assistants.create(
    name=name,
    instructions=instructions,
    model="gpt-4o-mini-2024-07-18",
)

# Extract the assistant ID
assistant_id = response.id

# Create a vector store for the repository files
vector_store = client.beta.vector_stores.create(name=f"{repo_name} Files")

# Extract the vector store ID
vector_store_id = vector_store.id

# Save the assistant ID to a JSON configuration file
config = {
    "repo_assistant_id": assistant_id,
    "repo_vector_store_id": vector_store_id,
}

with open('repo_assistant_config.json', 'w') as f:
    json.dump(config, f, indent=4)
