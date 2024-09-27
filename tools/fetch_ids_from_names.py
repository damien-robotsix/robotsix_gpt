import os
import openai

# Initialize OpenAI API client
openai.api_key = os.getenv('OPENAI_API_KEY')

repo_name = os.getenv('REPO_NAME')
branch_name = os.getenv('BRANCH_NAME')

# Construct names for assistant and vector store
assistant_name = f"{repo_name}-{branch_name}-assistant"
vector_store_name = f"{repo_name}-{branch_name}-vector"

# Function to fetch assistant_id using the assistant name
def get_assistant_id_by_name(name):
    # Example pattern to retrieve assistant by name
    assistants = openai.Assistant.list()
    for assistant in assistants['data']:
        if assistant['name'] == name:
            return assistant['id']
    return None

# Function to fetch vector_store_id using the vector store name
def get_vector_store_id_by_name(name):
    # Example pattern to retrieve vector store by name
    vector_stores = openai.Vector.list()
    for vector in vector_stores['data']:
        if vector['name'] == name:
            return vector['id']
    return None

assistant_id = get_assistant_id_by_name(assistant_name)
vector_store_id = get_vector_store_id_by_name(vector_store_name)

# Set IDs to environment variables or print them for use in GitHub Actions
env_file_path = os.getenv('GITHUB_ENV')
with open(env_file_path, 'a') as env_file:
    if assistant_id:
        env_file.write(f"assistant_id={assistant_id}\n")
    if vector_store_id:
        env_file.write(f"vector_store_id={vector_store_id}\n")
