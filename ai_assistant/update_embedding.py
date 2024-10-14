import os
import pandas as pd
import openai
from ai_assistant.utils import save_embeddings

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

def update_embeddings(repo_chunks_path):
    """Update embeddings for files based on the repo_chunks.csv file."""
    # Read the repo_chunks.csv file
    repo_chunks_df = pd.read_csv(repo_chunks_path)
    updated_embeddings = []

    for _, row in repo_chunks_df.iterrows():
        file_path = row['file_path']
        start_line = row['line_start']
        end_line = row['line_end']
        
        # Read the file content for the specified lines
        with open(file_path, 'r') as file:
            lines = file.readlines()
            chunk_content = ''.join(lines[start_line-1:end_line]).strip()

        # Get embedding for the chunk
        if chunk_content:
            embedding = get_embedding(chunk_content)
            if embedding:
                updated_embeddings.append({
                    'file_path': file_path,
                    'start_line': start_line,
                    'end_line': end_line,
                    'embedding': embedding,
                    'content': chunk_content,
                    'type': 'chunk'
                })

    # Save the updated embeddings to a new CSV file
    if updated_embeddings:
        embeddings_df = pd.DataFrame(updated_embeddings)
        embeddings_df.to_csv('updated_embeddings.csv', index=False)


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
    # Path to the repo_chunks.csv file
    repo_chunks_path = 'ai_assistant/repo_chunks.csv'
    
    # Update embeddings based on the repo_chunks.csv file
    update_embeddings(repo_chunks_path)
    
    print("Embedding process completed and saved to updated_embeddings.csv.")

if __name__ == '__main__':
    main()
