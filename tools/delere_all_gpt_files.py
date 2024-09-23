import os
import openai

def initialize_openai_client():
    """
    Initializes the OpenAI client using the API key provided in the environment variables.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    return openai.OpenAI(api_key=api_key)

def delete_all_files(client):
    """
    Deletes all files listed by the OpenAI API client.
    """
    try:
        files = client.files.list()
        for file in files:
            file_id = file.id
            try:
                client.files.delete(file_id)
                print(f"Deleted file: {file_id}")
            except Exception as exc:
                print(f"Failed to delete file {file_id}: {exc}")
    except Exception as e:
        print(f"Error while listing files: {e}")

def main():
    client = initialize_openai_client()
    delete_all_files(client)

if __name__ == "__main__":
    main()