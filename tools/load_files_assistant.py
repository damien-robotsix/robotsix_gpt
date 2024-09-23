import os
import sys
import tempfile
import shutil
from typing import List
import openai  # Correct OpenAI import
from utils import get_assistant_configuration

def get_all_files(repo_path: str, exclude_dirs: List[str] = None) -> List[str]:
    """
    Traverses the repository directory and collects all file paths,
    excluding specified directories.
    """
    if exclude_dirs is None:
        exclude_dirs = ['.git', 'venv', '__pycache__', 'env']

    file_paths = []
    for root, dirs, files in os.walk(repo_path):
        # Modify dirs in-place to exclude certain directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            file_path = os.path.join(root, file)
            # Optionally, exclude certain file types
            if not file_path.endswith(('.gitignore')):
                file_paths.append(file_path)
    return file_paths

def load_files_assistant(repo_path: str):
    """
    Main function to load files into the assistant's vector store.
    """
    # Set your OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
    client = openai.OpenAI(api_key=api_key)

    # Get the assistant configuration
    assistant_configuration = get_assistant_configuration()
    vector_store_id = assistant_configuration['vector_store_id']

    # Get all files in the repository
    paths = get_all_files(repo_path)

    # Create a temporary directory for processing the files
    with tempfile.TemporaryDirectory() as temp_dir:
        updated_paths = []

        # Process each file path
        for path in paths:
            # Check for .yaml, .sh, or files without extensions
            if path.endswith(".yaml") or path.endswith(".sh") or "." not in os.path.basename(path):
                # Generate a new path with .txt extension in the temp directory
                new_path = os.path.join(temp_dir, os.path.basename(path) + ".txt")
                # Copy the original file to the new location with the updated extension
                shutil.copy(path, new_path)
                # Add the updated path to the list
                updated_paths.append(new_path)
            else:
                # If no extension change is needed, add the original path
                updated_paths.append(path)

        # Fetch the list of existing files in the vector store
        existing_file_list = client.beta.vector_stores.files.list(vector_store_id=vector_store_id)
        updated_files = [os.path.basename(path) for path in updated_paths]

        # Delete any existing files with the same names in updated_paths
        for file in existing_file_list:
            existing_file_name = client.files.retrieve(file.id).filename
            if existing_file_name in updated_files:
                client.files.delete(file.id)

        # Open file streams for each updated path
        file_streams = [open(path, "rb") for path in updated_paths]
        
        try:
            # Upload the files and handle the process with vector store
            client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id, files=file_streams
            )
        finally:
            # Close all file streams after uploading
            for stream in file_streams:
                stream.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: load_files_assistant <repo_path>")
        sys.exit(1)

    repo_path = sys.argv[1]
    load_files_assistant(repo_path)
