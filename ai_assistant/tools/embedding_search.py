import openai
from sklearn.metrics.pairwise import cosine_similarity
import os
from ai_assistant.utils.utils import load_embeddings

openai.api_key = os.getenv('OPENAI_API_KEY')


def search(code_query):
    embedding_df, _ = load_embeddings()
    if embedding_df.empty:
        print("No embeddings found.")
        return

    query_embedding = openai.OpenAI().embeddings.create(input = [code_query], model="text-embedding-3-large")

    embedding_df['similarities'] = embedding_df.embedding.apply(lambda x: cosine_similarity([x], [query_embedding.data[0].embedding])[0][0])
    res = embedding_df.sort_values('similarities', ascending=False)
    return res
