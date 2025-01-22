from langchain_core.tools import tool
from langchain_core.documents import Document
import uuid
import os
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.runnables import RunnableConfig
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_chroma import Chroma


@tool
def save_recall_memory(memory: str, config: RunnableConfig) -> str:
    """Save memory to vectorstore for later semantic retrieval."""
    document = Document(page_content=memory, id=str(uuid.uuid4()))
    try:
        recall_vector_store = InMemoryVectorStore.load(
            config["configurable"]["memory_store_path"], OpenAIEmbeddings()
        )
    except FileNotFoundError:
        recall_vector_store = InMemoryVectorStore(OpenAIEmbeddings())
    recall_vector_store.add_documents([document])
    recall_vector_store.dump(config["configurable"]["memory_store_path"])
    return memory


@tool
def search_recall_memories(query: str, config: RunnableConfig) -> list[str]:
    """Search for memories in vectorstore based on query."""
    try:
        recall_vector_store = InMemoryVectorStore.load(
            config["configurable"]["memory_store_path"], OpenAIEmbeddings()
        )
    except FileNotFoundError:
        print("No memories found.")
        recall_vector_store = InMemoryVectorStore(OpenAIEmbeddings())
    documents = recall_vector_store.similarity_search(query, k=3)
    if not documents:
        return ["NO MEMORIES FOUND"]
    return [document.page_content for document in documents]


@tool
def search_repo_content(query: str, config: RunnableConfig) -> list[str]:
    """Perform semantic search on repo content based on query."""
    vector_store = Chroma(
        collection_name="repo",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=os.path.join(
            config["configurable"]["repo_path"], ".rsgpt", "chroma_db"
        ),
    )
    search_results = vector_store.similarity_search(query, k=3)
    return [document.model_dump_json() for document in search_results]


@tool
def search_repo_by_path(
    path: str, chunk_number: int, config: RunnableConfig
) -> list[str]:
    """Search for file content by path and chunk number (starting from 0) in the repository."""
    vector_store = Chroma(
        collection_name="repo",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=os.path.join(
            config["configurable"]["repo_path"], ".rsgpt", "chroma_db"
        ),
    )
    documents = vector_store.get(where={"file_path": path})
    if len(documents["ids"]) == 0:
        return ["NO FILE FOUND"]
    if chunk_number > len(documents["ids"]):
        return [f"NO CHUNK FOUND, max chunk number is {len(documents['ids'])}"]
    for index in range(len(documents["ids"])):
        if (
            documents["metadatas"][index]["chunk_number"]
            == f"{chunk_number}/{len(documents['ids'])}"
        ):
            return [documents["documents"][index]]
    return ["NO CHUNK FOUND"]


@tool
def generate_repo_tree(config: RunnableConfig) -> str:
    """
    Generates a tree representation of a repository, ignoring files and folders starting with a dot.
    """
    root_path = config["configurable"]["repo_path"]

    def generate_repo_tree_rec(root_path_rec, prefix):
        tree = []
        entries = sorted(
            [e for e in os.listdir(root_path_rec) if not e.startswith(".")]
        )
        for index, entry in enumerate(entries):
            entry_path = os.path.join(root_path_rec, entry)
            connector = "└── " if index == len(entries) - 1 else "├── "
            tree.append(f"{prefix}{connector}{entry}")

            if os.path.isdir(entry_path):
                subtree_prefix = (
                    f"{prefix}    " if index == len(entries) - 1 else f"{prefix}│   "
                )
                tree.append(generate_repo_tree_rec(entry_path, subtree_prefix))
        return "\n".join(tree)

    return generate_repo_tree_rec(root_path, "")


@tool
def create_file(file_path: str, file_content: str, config: RunnableConfig) -> str:
    """Create a file in the repository."""
    full_path = os.path.join(config["configurable"]["repo_path"], file_path)
    try:
        with open(full_path, "w") as f:
            f.write(file_content)
    except Exception as e:
        return f"Error creating file: {e}"
    return f"File created at {full_path}"


@tool
def call_worker(worker: str, additional_prompt: str):
    """Call a worker agent."""
    return


web_search = TavilySearchResults(max_results=2)
