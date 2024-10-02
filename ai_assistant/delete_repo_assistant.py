import os
import sys
import json
import openai

def clean_vector_store(vector_store_id: str):
    """
    Cleans (deletes) all files in the specified vector store.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    client = openai.Client(api_key=api_key)

    # Retrieve list of files in the vector store
    existing_file_list = client.beta.vector_stores.files.list(vector_store_id=vector_store_id)

    # Delete all files in the vector store
    for file in existing_file_list:
        try:
            client.files.delete(file.id)
            print(f"Deleted file: {file.id}")
        except Exception as e:
            print(f"Could not delete file {file.id}. Error: {e}")

def main(config_file='repo_assistant_config.json'):
    # Ensure the environment variable for API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
        sys.exit(1)

    client = openai.Client(api_key=api_key)

    # Path to the config file storing assistant and vector store IDs
    try:
        with open(config_file, 'r') as file:
            config_data = json.load(file)
            assistant_id = config_data.get('repo_assistant_id')
            vector_store_id = config_data.get('repo_vector_store_id')
    except FileNotFoundError:
        print(f"Config file {config_file} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the config file {config_file}.")
        sys.exit(1)

    # Delete all files in the vector store
    clean_vector_store(vector_store_id)

    # Delete the vector store
    client.beta.vector_stores.delete(vector_store_id=vector_store_id)

    # Delete the assistant
    client.beta.assistants.delete(assistant_id=assistant_id)

    print(f"Deleted assistant and vector store with IDs: {assistant_id}, {vector_store_id}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        main(config_file)
    else:
        main()
