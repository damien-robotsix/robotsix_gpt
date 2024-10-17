import os
import pandas as pd
from git_utils import find_git_root


def load_embeddings():
    """Load the embeddings and content from the .ai_assistant directory."""
    start_path = os.getcwd()
    try:
        git_root = find_git_root(start_path)
    except FileNotFoundError as e:
        print(e)
        return pd.DataFrame(), {}

    ai_dir = os.path.join(git_root, '.ai_assistant')

    print(ai_dir)

    embedding_df = pd.read_csv(os.path.join(ai_dir, 'repo_chunks.csv'))
    return embedding_df
