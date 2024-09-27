import os
import sys
from openai import OpenAI

# Ensure the environment variable for API key is set
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Repository root path
repo_path = os.getcwd()

# Path to the config file storing assistant and vector store IDs
if len(sys.argv) < 3:
    print("Usage: delete_assistant.py <repo_assistant_id> <repo_vector_store_id>")
    sys.exit(1)

assistant_id = sys.argv[1]
vector_store_id = sys.argv[2]

# Delete all files in the vector store
vector_store_files = client.beta.vector_stores.list_files(vector_store_id=vector_store_id)
for file in vector_store_files:
    client.beta.vector_stores.delete_file(file_id=file.id)

# Delete the vector store
client.beta.vector_stores.delete(vector_store_id=vector_store_id)

# Delete the assistant
client.beta.assistants.delete(assistant_id=assistant_id)

print(f"Deleted assistant and vector store with IDs: {assistant_id}, {vector_store_id}")
