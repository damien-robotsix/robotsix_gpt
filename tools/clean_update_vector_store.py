#!/usr/bin/env python3

import os
import sys
import tempfile
import shutil
from typing import List
import openai
from utils import get_repo_assistant_configuration

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
            if not file_path.endswith(('.gitignore')):
                file_paths.append(file_path)
    return file_paths

def load_files_assistant(repo_path: str):
    """
    Main function to load files into the assistant's vector store.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
    client = openai.OpenAI(api_key=api_key)

    assistant_configuration = get_repo_assistant_configuration('repo_assistant_config.json')
    vector_store_id = assistant_configuration['repo_vector_store_id']

    # Clean the vector store before loading new files
    clean_vector_store(vector_store_id)

    paths = get_all_files(repo_path)

    with tempfile.TemporaryDirectory() as temp_dir:
        for path in paths:
            try:
                with open(path, "rb") as file_stream:
                    client.beta.vector_stores.file_batches.upload_and_poll(
                        vector_store_id=vector_store_id, files=[file_stream]
                    )
            except Exception as e:
                if 'Invalid extensions typed' in str(e):
                    # We check that the file is not a binary file
                    with open(path, 'rb') as f:
                        if f.read(1024).find(b'\0') == -1:
                            print(f"Could not upload file {path}. Error: {e}")
                    new_path = os.path.join(temp_dir, os.path.basename(path) + ".txt")
                    shutil.copy(path, new_path)
                    with open(new_path, "rb") as file_stream:
                        try:
                            client.beta.vector_stores.file_batches.upload_and_poll(
                                vector_store_id=vector_store_id, files=[file_stream]
                            )
                        except Exception as e:
                            print(f"Could not upload file {path}. Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: update_vector_store <repo_path>")
        sys.exit(1)

    repo_path = sys.argv[1]
    load_files_assistant(repo_path)
