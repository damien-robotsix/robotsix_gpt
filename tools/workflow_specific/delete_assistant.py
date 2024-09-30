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
# Read assistant and vector store IDs from the output file
output_file = 'ids_output.txt'
try:
    with open(output_file, 'r') as file:
        for line in file:
            if 'repo_assistant_id' in line:
                assistant_id = line.strip().split('=')[1]
            elif 'repo_vector_store_id' in line:
                vector_store_id = line.strip().split('=')[1]
except FileNotFoundError:
    print(f"Output file {output_file} not found.")
    sys.exit(1)

# Delete all files in the vector store
clean_vector_store(vector_store_id)

# Delete the vector store
client.beta.vector_stores.delete(vector_store_id=vector_store_id)

# Delete the assistant
client.beta.assistants.delete(assistant_id=assistant_id)

print(f"Deleted assistant and vector store with IDs: {assistant_id}, {vector_store_id}")
