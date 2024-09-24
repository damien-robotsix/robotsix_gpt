import os
import openai
from utils import get_assistant_configuration

def clean_vector_store(vector_store_id: str):
    """
    Cleans (deletes) all files in the specified vector store.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
    client = openai.OpenAI(api_key=api_key)

    # Retrieve list of files in the vector store
    existing_file_list = client.beta.vector_stores.files.list(vector_store_id=vector_store_id)

    # Delete all files in the vector store
    for file in existing_file_list:
        try:
            client.files.delete(file.id)
            print(f"Deleted file: {file.id}")
        except Exception as e:
            print(f"Could not delete file {file.id}. Error: {e}")

if __name__ == "__main__":
    # Load the configuration to get the vector_store_id
    config = get_assistant_configuration()
    vector_store_id = config['vector_store_id']
    clean_vector_store(vector_store_id)
