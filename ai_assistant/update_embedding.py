import os
import pandas as pd
import openai
from tqdm import tqdm
from tenacity import retry, wait_random_exponential, stop_after_attempt

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embedding(text: str, model="text-embedding-3-small") -> list[float]:
    """Get the embedding for the given text using OpenAI API with retry logic."""
    text = text.replace('\n', ' ')  # Remove newlines
    return openai.OpenAI().embeddings.create(input=[text], model=model).data[0].embedding

def update_embeddings(repo_chunks_path):
    """Update embeddings for files based on the repo_chunks.csv file."""
    # Read the repo_chunks.csv file
    repo_chunks_df = pd.read_csv(repo_chunks_path)
    # Ensure the 'embedding' column exists, initialize with zeros if not
    if 'embedding' not in repo_chunks_df.columns:
        repo_chunks_df['embedding'] = 0

    updated_embeddings = []

    for _, row in tqdm(repo_chunks_df.iterrows(), total=repo_chunks_df.shape[0], desc="Updating embeddings"):
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
                    'embedding': embedding
                })

    # Append the updated embeddings to the existing CSV file
    if updated_embeddings:
        # Update the existing DataFrame with new embeddings
        for updated in updated_embeddings:
            repo_chunks_df.loc[
                (repo_chunks_df['file_path'] == updated['file_path']) &
                (repo_chunks_df['line_start'] == updated['start_line']) &
                (repo_chunks_df['line_end'] == updated['end_line']),
                'embedding'
            ] = updated['embedding']

        # Save the updated DataFrame back to the CSV
        repo_chunks_df.to_csv(repo_chunks_path, index=False)


def main():
    # Path to the repo_chunks.csv file
    repo_chunks_path = '.ai_assistant/repo_chunks.csv'
    
    # Update embeddings based on the repo_chunks.csv file
    update_embeddings(repo_chunks_path)


if __name__ == '__main__':
    main()
