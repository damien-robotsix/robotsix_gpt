import os
import sys
import json
from openai import OpenAI

# Ensure the environment variable for API key is set
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Repository root path
repo_path = os.getcwd()

# Path to the config file storing assistant and vector store IDs
config_file = os.path.join(repo_path, "repo_assistant_config.json")
if not os.path.exists(config_file):
    print(f"Missing configuration file: {config_file}")
    sys.exit(0)

with open(config_file) as f:
    config = json.load(f)

assistant_id = config.get("repo_assistant_id")
vector_store_id = config.get("repo_vector_store_id")

# Delete all files in the vector store
vector_store_files = client.beta.vector_stores.list_files(vector_store_id=vector_store_id)
for file in vector_store_files:
    client.beta.vector_stores.delete_file(file_id=file.id)

# Delete the vector store
client.beta.vector_stores.delete(vector_store_id=vector_store_id)

# Delete the assistant
client.beta.assistants.delete(assistant_id=assistant_id)

# Delete the configuration file
os.remove(config_file)

print(f"Deleted assistant and vector store for branch: {branch_name}")
