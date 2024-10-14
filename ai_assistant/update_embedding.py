import os
import pandas as pd
import openai
from tqdm import tqdm
from tenacity import retry, wait_random_exponential, stop_after_attempt
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

if not openai.api_key:
    logging.error("OPENAI_API_KEY is not set. Please set the environment variable.")
    exit(1)

@retry(
    wait=wait_random_exponential(min=1, max=20),
    stop=stop_after_attempt(6),
)
def get_embedding(text: str, model="text-embedding-3-large") -> list[float]:
    """
    Get embedding for a single text using OpenAI API with retry logic.
    
    Args:
        text (str): The text string to embed.
        model (str): The embedding model to use.

    Returns:
        list[float]: The embedding corresponding to the input text.
    """
    cleaned_text = text.replace('\n', ' ')
    logging.debug(f"Requesting embedding for text: {cleaned_text[:50]}...")  # Log first 50 chars
    response = openai.OpenAI().embeddings.create(input=cleaned_text, model=model)
    embedding = response['data'][0]['embedding']
    logging.debug("Received embedding.")
    return embedding

def update_embeddings(repo_chunks_path):
    """
    Update embeddings for files based on the repo_chunks.csv file by processing each text individually.
    
    Args:
        repo_chunks_path (str): Path to the repo_chunks.csv file.
    """
    logging.info(f"Reading repo_chunks from {repo_chunks_path}")
    # Read the repo_chunks.csv file
    repo_chunks_df = pd.read_csv(repo_chunks_path)
    
    # Ensure the 'embedding' column exists, initialize with zeros if not
    if 'embedding' not in repo_chunks_df.columns:
        repo_chunks_df['embedding'] = None  # Use None instead of 0 for embeddings
    
    # Identify rows that need embeddings
    rows_to_update = repo_chunks_df[
        (repo_chunks_df['embedding'].isna()) | (repo_chunks_df['embedding'] == 0)
    ].copy()

    total_rows = rows_to_update.shape[0]
    if total_rows == 0:
        logging.info("All embeddings are already up to date.")
        return

    logging.info(f"Total chunks to update: {total_rows}")

    updated_embeddings = []

    # Initialize tqdm with total number of rows
    with tqdm(total=total_rows, desc="Updating embeddings") as pbar:
        for _, row in rows_to_update.iterrows():
            file_path = row['file_path']
            start_line = row['line_start']
            end_line = row['line_end']

            try:
                # Read the file content for the specified lines
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                    chunk_content = ''.join(lines[start_line-1:end_line]).strip()
                    if chunk_content:
                        embedding = get_embedding(chunk_content)
                        updated_embeddings.append({
                            'file_path': file_path,
                            'start_line': start_line,
                            'end_line': end_line,
                            'embedding': embedding
                        })
                    else:
                        logging.warning(f"Empty content for {file_path} lines {start_line}-{end_line}. Skipping.")
            except Exception as e:
                logging.error(f"Error processing file {file_path} lines {start_line}-{end_line}: {e}")
                continue

            pbar.update(1)

    # Update the DataFrame with new embeddings
    if updated_embeddings:
        logging.info(f"Updating embeddings in DataFrame for {len(updated_embeddings)} entries")
        for updated in updated_embeddings:
            repo_chunks_df.loc[
                (repo_chunks_df['file_path'] == updated['file_path']) &
                (repo_chunks_df['line_start'] == updated['start_line']) &
                (repo_chunks_df['line_end'] == updated['end_line']),
                'embedding'
            ] = [updated['embedding']]  # Assign as a list to ensure proper storage

        # Save the updated DataFrame back to the CSV
        repo_chunks_df.to_csv(repo_chunks_path, index=False)
        logging.info(f"Successfully updated embeddings and saved to {repo_chunks_path}")
    else:
        logging.info("No embeddings were updated.")

def main():
    # Path to the repo_chunks.csv file
    repo_chunks_path = '.ai_assistant/repo_chunks.csv'
    
    # Update embeddings based on the repo_chunks.csv file
    update_embeddings(repo_chunks_path)

if __name__ == '__main__':
    main()
