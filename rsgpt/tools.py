from langchain_core.tools import tool
from langchain_core.documents import Document
import uuid
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.runnables import RunnableConfig
from langchain_community.tools.tavily_search import TavilySearchResults


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


web_search = TavilySearchResults(max_results=2)
