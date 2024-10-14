import os
import pandas as pd
import openai

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_embedding(text):
    """Get the embedding for the given text using OpenAI API."""
    try:
        text.replace('\n', ' ')  # Remove newlines
        return openai.OpenAI().embeddings.create(input = [text], model="text-embedding-3-large").data[0].embedding
    except Exception as e:
        print(f"Error obtaining embedding for text: {e}")
        return None

def update_embeddings(repo_chunks_path):
    """Update embeddings for files based on the repo_chunks.csv file."""
    # Read the repo_chunks.csv file
    repo_chunks_df = pd.read_csv(repo_chunks_path)
    updated_embeddings = []

    for _, row in repo_chunks_df.iterrows():
        if pd.notna(row.get('embedding')) and row['embedding'] != 0:
            continue

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
                })

    # Append the updated embeddings to the existing CSV file
    if updated_embeddings:
        embeddings_df = pd.DataFrame(updated_embeddings)
        embeddings_df.to_csv(repo_chunks_path, mode='a', header=False, index=False)


def main():
    # Path to the repo_chunks.csv file
    repo_chunks_path = '.ai_assistant/repo_chunks.csv'
    
    # Update embeddings based on the repo_chunks.csv file
    update_embeddings(repo_chunks_path)


if __name__ == '__main__':
    main()
