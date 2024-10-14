import pickle
import os
import pandas as pd
from ai_assistant.utils.git import find_git_root


def load_embeddings_with_pickle(file_path):
    """Load the embeddings and content using Pickle."""
    if not os.path.exists(file_path):
        return pd.DataFrame(), {}
    with open(file_path, 'rb') as f:
        embedding_data, file_hashes = pickle.load(f)
    print(f"Data loaded from {file_path}")
    return embedding_data, file_hashes


def save_embeddings_with_pickle(embedding_data, file_hashes, file_path):
    """Save the embeddings and content using Pickle."""
    with open(file_path, 'wb') as f:
        pickle.dump([embedding_data, file_hashes], f)
    print(f"Data saved to {file_path}")


def load_embeddings():
    """Load the embeddings and content from the .robotsix_ai directory."""
    start_path = os.getcwd()
    try:
        git_root = find_git_root(start_path)
    except FileNotFoundError as e:
        print(e)
        return pd.DataFrame(), {}

    ai_dir = os.path.join(git_root, '.robotsix_ai')
    os.makedirs(ai_dir, exist_ok=True)

    embedding_df, file_hashes = load_embeddings_with_pickle(
        os.path.join(ai_dir, 'embeddings.pickle'))
    return embedding_df, file_hashes


def save_embeddings(embedding_df, file_hashes):
    """Save the embeddings and content to the .robotsix_ai directory."""
    start_path = os.getcwd()
    try:
        git_root = find_git_root(start_path)
    except FileNotFoundError as e:
        print(e)
        return

    ai_dir = os.path.join(git_root, '.robotsix_ai')
    os.makedirs(ai_dir, exist_ok=True)

    save_embeddings_with_pickle(
        embedding_df, file_hashes, os.path.join(ai_dir, 'embeddings.pickle'))
