import os
import pandas as pd
import openai
from ai_assistant.utils import load_embeddings, save_embeddings
from ai_assistant.utils.git import find_git_root, load_gitignore, ensure_gitignore_entry
from ai_assistant.utils.files import compute_hash
from ai_assistant.utils.chunk import chunk_file

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')  # It's safer to use environment variables

def get_embedding(text):
    """Get the embedding for the given text using OpenAI API."""
    try:
        text.replace('\n', ' ')  # Remove newlines
        return openai.OpenAI().embeddings.create(input = [text], model="text-embedding-3-large").data[0].embedding
    except Exception as e:
        print(f"Error obtaining embedding for text: {e}")
        return None

def process_file(file_path):
    """Process a file to compute embeddings for each chunk and the overview, then return metadata."""
    # Use the chunking system based on file type
    file_chunks, file_overview = chunk_file(file_path)
    
    # If the file doesn't have chunks or is not a text file, skip it
    if not file_chunks:
        return None

    chunk_embeddings = []
    
    # Embed each chunk and save the content
    for chunk in file_chunks[file_path]:
        chunk_content = chunk['content'].strip()
        if chunk_content:  # Only process non-empty chunks
            embedding = get_embedding(chunk_content)
            if embedding:
                chunk_embeddings.append({
                    'file_path': file_path,
                    'start_line': chunk['start_line'],
                    'end_line': chunk['end_line'],
                    'embedding': embedding,
                    'content': chunk_content,  # Save the content of the chunk
                    'type': 'chunk'  # Mark it as a chunk
                })

    # Embed the overview and save the content if it exists
    if file_overview:
        overview_content = file_overview[file_path].strip()
        if overview_content:
            overview_embedding = get_embedding(overview_content)
            if overview_embedding:
                chunk_embeddings.append({
                    'file_path': file_path,
                    'start_line': 0,  # Overview doesn't correspond to specific lines
                    'end_line': 0,
                    'embedding': overview_embedding,
                    'content': overview_content,  # Save the overview content
                    'type': 'overview'  # Mark it as an overview
                })

    return chunk_embeddings if chunk_embeddings else None

def update_embeddings(git_root, spec, embedding_df, file_hashes):
    """Update embeddings for files by processing chunks and overviews if the file has changed."""
    updated_embeddings = []
    for root, _, files in os.walk(git_root):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, git_root)

            # Skip if matches .gitignore patterns
            if spec.match_file(rel_path):
                continue

            current_hash = compute_hash(file_path)
            if file_path not in file_hashes or current_hash != file_hashes[file_path]:
                print(f"Processing file: {file_path}")
                chunked_embeddings = process_file(file_path)
                if chunked_embeddings:
                    updated_embeddings.extend(chunked_embeddings)
                    file_hashes[file_path] = current_hash

    if updated_embeddings:
        new_df = pd.DataFrame(updated_embeddings)
        embedding_df = pd.concat([embedding_df, new_df], ignore_index=True)
    return embedding_df, file_hashes


def clean_up_missing_files(embedding_df):
    """Remove entries from the DataFrame where the file no longer exists."""
    valid_indices = []

    for idx, row in embedding_df.iterrows():
        if os.path.exists(row['file_path']):
            valid_indices.append(idx)  # Keep the row if the file exists
        else:
            print(f"File not found, removing from embeddings: {row['file_path']}")

    return embedding_df.loc[valid_indices].reset_index(drop=True)


def main():
    # Determine the current working directory
    start_path = os.getcwd()

    try:
        git_root = find_git_root(start_path)
        print(f"Git root found at: {git_root}")
    except FileNotFoundError as e:
        print(e)
        return

    # Ensure .robotsix_ai is in .gitignore
    ensure_gitignore_entry(git_root, entry=".robotsix_ai/")

    # Define the .robotsix_ai directory
    ai_dir = os.path.join(git_root, '.robotsix_ai')
    os.makedirs(ai_dir, exist_ok=True)

    # Load .gitignore patterns
    spec = load_gitignore(git_root)

    # Load existing data
    embedding_df, file_hashes = load_embeddings()

    # Clean up missing files
    embedding_df = clean_up_missing_files(embedding_df)

    # Update embeddings
    embedding_df, file_hashes = update_embeddings(git_root, spec, embedding_df, file_hashes)

    # Save updated data
    save_embeddings(embedding_df, file_hashes)

    print("Embedding process completed.")

if __name__ == '__main__':
    main()
