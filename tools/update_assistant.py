import os
import json
from openai import OpenAI
from generate_repo_structure import generate_structure_from_path

# Set up your OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Dynamically determine the repository path
repo_path = os.getcwd()

# Generate the repository structure
structure = generate_structure_from_path(repo_path)

# Load assistant ID from the assistant_config.json file
config_file = os.path.join(repo_path, "assistant_config.json")
with open(config_file) as f:
    config = json.load(f)
assistant_id = config.get("repo_assistant_id")

# Prepare the update for the assistant's instructions
new_instructions = f"Your role is to perform development and maintenance tasks for the repository ai_assistant. You have access to a set of repository tools that allow you to execute shell commands in the repository root and manage file contents.\nRepository structure :\n{structure}"

response = client.beta.assistants.update(
    assistant_id=assistant_id,
    instructions=new_instructions
)

if response.id == assistant_id:
    print("Assistant instructions updated successfully.")
else:
    print("Failed to update the assistant.")