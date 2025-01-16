import openai
from sklearn.metrics.pairwise import cosine_similarity
import os
import ast
import pandas as pd
from .context import RsgptContext
from tqdm import tqdm
from tenacity import retry, wait_random_exponential, stop_after_attempt
import logging

openai.api_key = os.getenv("OPENAI_API_KEY")


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
)

# Set OpenAI logging level to WARNING to ignore less severe logs
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)


def load_embeddings(context: RsgptContext):
    rsgpt_repo_dir = os.path.join(str(context.git_repo_root), ".rsgpt")
    embedding_df = pd.read_csv(os.path.join(rsgpt_repo_dir, "repo_chunks.csv"))
    return embedding_df


def search(code_query: str, n_results: int, context: RsgptContext):
    embedding_df = load_embeddings(context)
    if embedding_df.empty:
        print("No embeddings found.")
        return

    embedding_df["embedding"] = embedding_df.embedding.apply(ast.literal_eval)

    query_embedding = openai.OpenAI().embeddings.create(
        input=[code_query], model="text-embedding-3-large"
    )

    embedding_df["similarities"] = embedding_df.embedding.apply(
        lambda x: cosine_similarity([x], [query_embedding.data[0].embedding])[0][0]
    )
    res = embedding_df.sort_values("similarities", ascending=False)
    return res.head(n_results)


@retry(
    wait=wait_random_exponential(min=1, max=20),
    stop=stop_after_attempt(2),
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
    cleaned_text = text.replace("\n", " ")
    # Log first 50 chars
    logging.debug(f"Requesting embedding for text: {cleaned_text[:50]}...")
    response = openai.OpenAI().embeddings.create(input=cleaned_text, model=model)
    embedding = response.data[0].embedding
    logging.debug("Received embedding.")
    return embedding


def update_embeddings(context: RsgptContext):
    repo_chunks_path = os.path.join(
        str(context.git_repo_root), ".rsgpt", "repo_chunks.csv"
    )
    logging.info(f"Reading repo_chunks from {repo_chunks_path}")
    # Read the repo_chunks.csv file
    repo_chunks_df = pd.read_csv(repo_chunks_path)

    # Ensure the 'embedding' column exists, initialize with zeros if not
    if "embedding" not in repo_chunks_df.columns:
        # Use None instead of 0 for embeddings
        repo_chunks_df["embedding"] = None

    repo_chunks_df["embedding"] = repo_chunks_df["embedding"].astype("object")

    # Identify rows that need embeddings
    rows_to_update = repo_chunks_df[
        (repo_chunks_df["embedding"].isna()) | (repo_chunks_df["embedding"] == 0)
    ]

    total_rows = rows_to_update.shape[0]
    if total_rows == 0:
        logging.info("All embeddings are already up to date.")
        return

    logging.info(f"Total chunks to update: {total_rows}")

    # Initialize tqdm with total number of rows
    with tqdm(total=total_rows, desc="Updating embeddings") as pbar:
        for index, row in rows_to_update.iterrows():
            file_path = row["file_path"]
            start_line = row["line_start"]
            end_line = row["line_end"]

            try:
                # Read the file content for the specified lines
                with open(file_path, "r") as file:
                    lines = file.readlines()
                    chunk_content = "".join(lines[start_line - 1 : end_line]).strip()

                    # Add filename and line numbers to the chunk content
                    chunk_content_with_metadata = f"File: {file_path} | Lines: {start_line}-{end_line}\n{chunk_content}"

                    if chunk_content:
                        embedding = get_embedding(chunk_content_with_metadata)
                        repo_chunks_df.at[index, "embedding"] = embedding
                    else:
                        logging.warning(
                            f"Empty content for {file_path} lines {start_line}-{end_line}. Skipping."
                        )
            except Exception as e:
                logging.error(
                    f"Error processing file {file_path} lines {start_line}-{end_line}: {e}"
                )
                continue

            pbar.update(1)

            # Save the updated DataFrame back to the CSV
            repo_chunks_df.to_csv(repo_chunks_path, index=False)
            logging.info(
                f"Successfully updated embeddings and saved to {repo_chunks_path}"
            )
