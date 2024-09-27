import os
import openai

# Initialize OpenAI API client
openai.api_key = os.getenv('OPENAI_API_KEY')

repo_name = os.getenv('REPO_NAME')
branch_name = os.getenv('BRANCH_NAME')

tag_to_find = f"{repo_name}-{branch_name}"

# Function to fetch assistant_id using the assistant name
def get_assistant_id_by_name():
    # Example pattern to retrieve assistant by name
    assistants = openai.beta.assistants.list()
    for assistant in assistants:
        if tag_to_find in assistant.name:
            print(assistant.name)
            print(assistant.id)
            return assistant.id
    print(f"Assistant not found for {tag_to_find}")
    return None

# Function to fetch vector_store_id using the vector store name
def get_vector_store_id_by_name():
    # Example pattern to retrieve vector store by name
    vector_stores = openai.beta.vector_stores.list()
    for vector_store in vector_stores:
        if tag_to_find in vector_store.name:
            print(vector_store.name)
            print(vector_store.id)
            return vector_store.id
    print(f"Vector store not found for {tag_to_find}")
    return None

assistant_id = get_assistant_id_by_name()
vector_store_id = get_vector_store_id_by_name()

# Set IDs to environment variables or print them for use in GitHub Actions
env_file_path = os.getenv('GITHUB_ENV')
with open(env_file_path, 'a') as env_file:
    if assistant_id:
        env_file.write(f"assistant_id={assistant_id}\n")
    if vector_store_id:
        env_file.write(f"vector_store_id={vector_store_id}\n")
