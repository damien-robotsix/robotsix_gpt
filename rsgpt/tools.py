from langchain_core.tools import tool
from langchain_core.documents import Document
import uuid
import os
import subprocess
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.runnables import RunnableConfig
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_chroma import Chroma
from typing import Annotated
from langgraph.prebuilt import InjectedState


@tool
def save_recall_memory(memory: str, config: RunnableConfig) -> str:
    """Save memory to vectorstore for later semantic retrieval."""
    document = Document(page_content=memory, id=str(uuid.uuid4()))
    print(f"Saving memory in {config['configurable']['memory_store_path']}")
    try:
        recall_vector_store = InMemoryVectorStore.load(
            config["configurable"]["memory_store_path"],
            OllamaEmbeddings(model="bge-m3"),
        )
    except FileNotFoundError:
        recall_vector_store = InMemoryVectorStore(OllamaEmbeddings(model="bge-m3"))
    recall_vector_store.add_documents([document])
    recall_vector_store.dump(config["configurable"]["memory_store_path"])
    return memory


@tool
def execute_command_at_repo_root(command: str, config: RunnableConfig) -> str:
    """Execute a command from the repository's root directory and return its output."""
    try:
        repo_root = config["configurable"]["repo_path"]
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        return {"stdout": stdout, "stderr": stderr}
    except subprocess.CalledProcessError as e:
        return f"An error occurred: {e.stderr}"


@tool
def run_python_test_script(test_script_path: str, config: RunnableConfig) -> str:
    """
    Execute a Python test script from the test folder and return its output.
    Args:

    test_script_path (str): Path to the test script from the repository's root directory.
    """
    repo_root = config["configurable"]["repo_path"]
    test_script_path = os.path.join(repo_root, test_script_path)
    try:
        command = ["python", test_script_path]
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        return {"stdout": stdout, "stderr": stderr}

    except Exception as e:
        return f"An error occurred while running the test script: {str(e)}"


@tool
def search_recall_memories(query: str, config: RunnableConfig) -> list[str]:
    """Search for memories in vectorstore based on query."""
    try:
        recall_vector_store = InMemoryVectorStore.load(
            config["configurable"]["memory_store_path"],
            OllamaEmbeddings(model="bge-m3"),
        )
    except FileNotFoundError:
        print("No memories found.")
        recall_vector_store = InMemoryVectorStore(OllamaEmbeddings(model="bge-m3"))
    documents = recall_vector_store.similarity_search(query, k=3)
    if not documents:
        return ["NO MEMORIES FOUND"]
    return [document.page_content for document in documents]


@tool
def search_repo_content(query: str, config: RunnableConfig) -> list[str]:
    """Perform semantic search on repo content based on query."""
    vector_store = Chroma(
        collection_name="repo",
        embedding_function=OllamaEmbeddings(model="bge-m3"),
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
        embedding_function=OllamaEmbeddings(model="bge-m3"),
        persist_directory=os.path.join(
            config["configurable"]["repo_path"], ".rsgpt", "chroma_db"
        ),
    )
    documents = vector_store.get(where={"file_path": path})
    if len(documents["ids"]) == 0:
        return ["NO FILE FOUND"]
    chunk_max = len(documents["ids"]) - 1
    if chunk_number > chunk_max:
        return [f"NO CHUNK FOUND, last_chunk_number is {chunk_max}"]
    for index in range(len(documents["metadatas"])):
        if documents["metadatas"][index]["chunk_number"] == chunk_number:
            content = documents["documents"][index]
            return [
                f"{{'content': {content}, 'chunk_number': {chunk_number}, 'last_chunk_number': {chunk_max}}}"
            ]
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
def write_file(file_path: str, file_content: str, append: bool, config: RunnableConfig):
    """Write file content to a file, with the option to append or overwrite."""
    repo_path = config["configurable"]["repo_path"]
    full_path = os.path.join(repo_path, file_path)
    # If the file does not exist, switch to write mode
    if not os.path.exists(full_path):
        append = False
    # If we are in append mode, and the file does not end with a newline, add one
    current_content = ""
    if append:
        with open(full_path, "r") as f:
            current_content = f.read()
        if current_content and not current_content.endswith("\n"):
            file_content = "\n" + file_content
    mode = "a" if append else "w"
    try:
        with open(full_path, mode) as f:
            f.write(file_content)
    except Exception as e:
        return f"Error writing file: {e}"
    return f"File written successfully to {full_path} (appended: {append})"


@tool
def delete_file_chunk(file_path: str, chunk_number: int, config: RunnableConfig) -> str:
    """
    Delete a specific chunk of a file.
    Args:
        file_path (str): Path to the file containing the chunk
        chunk_number (int): Chunk number index to be deleted
    """
    try:
        vector_store = Chroma(
            collection_name="repo",
            embedding_function=OllamaEmbeddings(model="bge-m3"),
            persist_directory=os.path.join(
                config["configurable"]["repo_path"], ".rsgpt", "chroma_db"
            ),
        )
        # Retrieve all chunks for the file
        results = vector_store.get(where={"file_path": file_path})
        if not results["ids"]:
            return "File not found in vector store"

        # Order results by chunk number
        results["metadatas"] = sorted(
            results["metadatas"], key=lambda x: x["chunk_number"]
        )

        # Retrieve the selected chunk content
        deleted_content = results["documents"][chunk_number]

        # Find and remove the selected chunk content in the file
        with open(
            os.path.join(config["configurable"]["repo_path"], file_path), "r"
        ) as f:
            file_content = f.read()

        file_content = file_content.replace(deleted_content, "")

        with open(
            os.path.join(config["configurable"]["repo_path"], file_path), "w"
        ) as f:
            f.write(file_content)

        return "File chunk deleted successfully"
    except Exception as e:
        return f"Error deleting chunk: {str(e)}"


@tool
def modify_file_chunk(
    file_path: str, chunks: list[int], new_content: str, config: RunnableConfig
) -> str:
    """
    Modify a series of consecutive chunks in a file. The full content of the chunks in the range will be replaced with the new content.
    Args:
        file_path: Path to the file containing the chunks
        chunks: list of the chunks to replace, must be consecutive chunks
        new_content: New content to replace the chunks
    """
    try:
        # Check that all chunks are consecutive
        if not all([chunks[i] + 1 == chunks[i + 1] for i in range(len(chunks) - 1)]):
            return "Chunks must be consecutive"

        vector_store = Chroma(
            collection_name="repo",
            embedding_function=OllamaEmbeddings(model="bge-m3"),
            persist_directory=os.path.join(
                config["configurable"]["repo_path"], ".rsgpt", "chroma_db"
            ),
        )

        # Retrieve all chunks for the file
        results = vector_store.get(where={"file_path": file_path})
        if not results["ids"]:
            return "File not found in vector store"
        ck_range = range(chunks[0], chunks[-1] + 1)
        if len(results["documents"]) <= ck_range[-1]:
            return (
                f"End of chunk range is over maximum chunk {len(results['documents'])}"
            )

        # Order results by chunk number
        results["metadatas"] = sorted(
            results["metadatas"], key=lambda x: x["chunk_number"]
        )

        # Modify the first chunk with the new content and delete the rest
        with open(
            os.path.join(config["configurable"]["repo_path"], file_path), "r"
        ) as f:
            file_content = f.read()
            old_chunk_content = ""
            old_chunk_content = results["documents"][ck_range[0]]
            file_content = file_content.replace(old_chunk_content, new_content)

        for chunk_index in ck_range[1:]:
            old_chunk_content = results["documents"][chunk_index]
            file_content = file_content.replace(old_chunk_content, "")

        with open(
            os.path.join(config["configurable"]["repo_path"], file_path), "w"
        ) as f:
            f.write(file_content)

        return "File chunks modified successfully"
    except Exception as e:
        return f"Error modifying chunks: {str(e)}"


repo_worker_g = None  # Initialize as None


def initialize_repo_worker():
    global repo_worker_g
    if repo_worker_g is None:
        from .graphs.repo_worker import RepoWorker

        repo_worker_g = RepoWorker().compile()


specialist_g = None  # Initialize as None


def initialize_specialist():
    global specialist_g
    if specialist_g is None:
        from .graphs.specialist_with_memory import SpecialistWithMemory

        specialist_g = SpecialistWithMemory().compile()


# Add initialization for deeper think worker
deeperthink_worker_g = None


def initialize_deeperthink_worker():
    global deeperthink_worker_g
    if deeperthink_worker_g is None:
        from .graphs.deeper_think_worker import DeeperThinkWorker

        deeperthink_worker_g = DeeperThinkWorker().compile()


def initialize_repo_collector():
    from .graphs.repo_collector import RepoCollector

    return RepoCollector().compile()


@tool
def call_worker(
    worker: str,
    fake_user_message: str,
    config: RunnableConfig,
    messages: Annotated[list, InjectedState("messages")],
):
    """Call a worker agent. Will route the messages to the worker agent and return the response.
    You can fake an additional user message to the worker agent by providing the fake_user_message parameter.
    The worker agent will receive the fake_user_message as the last message in the conversation.
    """
    response = None
    input_messages = []
    for message in messages[:-1]:
        system = False
        try:
            if message["role"] == "system":
                system = True
        except:
            pass
        try:
            if message.type == "system":
                system = True
        except:
            pass
        if not system:
            input_messages.append(message)

    input_messages.append(("user", fake_user_message))
    if worker == "repo_worker":
        initialize_repo_worker()  # Ensure repo_worker_g is initialized
        response = repo_worker_g.invoke(
            {"messages": input_messages, "final_messages": []}, config
        )
    elif worker == "specialist":
        initialize_specialist()
        response = specialist_g.invoke({"messages": input_messages}, config)
    elif worker == "repo_collector":
        repo_collector = initialize_repo_collector()
        response = repo_collector.invoke({"messages": input_messages}, config)
    elif worker == "deeper_think_worker":
        initialize_deeperthink_worker()
        response = deeperthink_worker_g.invoke({"messages": input_messages}, config)
    else:
        return "Worker not found, please choose between 'repo_worker', 'specialist', 'repo_collector', or 'deeper_think_worker'"
    return response["final_messages"]


web_search = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
)
