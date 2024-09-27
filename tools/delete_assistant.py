import os
import sys
from openai import OpenAI

def clean_vector_store(vector_store_id: str):
    """
    Cleans (deletes) all files in the specified vector store.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
    client = OpenAI(api_key=api_key)

    # Retrieve list of files in the vector store
    existing_file_list = client.beta.vector_stores.files.list(vector_store_id=vector_store_id)

    # Delete all files in the vector store
    for file in existing_file_list:
        try:
            client.files.delete(file.id)
            print(f"Deleted file: {file.id}")
        except Exception as e:
            print(f"Could not delete file {file.id}. Error: {e}")

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
clean_vector_store(vector_store_id)

# Delete the vector store
client.beta.vector_stores.delete(vector_store_id=vector_store_id)

# Delete the assistant
client.beta.assistants.delete(assistant_id=assistant_id)

print(f"Deleted assistant and vector store with IDs: {assistant_id}, {vector_store_id}")
