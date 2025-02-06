from datetime import datetime
import os
from git import Repo
from langchain_chroma import Chroma
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain_core.documents import Document


def load_repository(repo_path: str):
    """
    A utility function to load a repository, check for modified files, update vector stores, and split documents into chunks.

    Args:
        repo_path (str): Path to the repository.

    Returns:
        dict: An empty dictionary as result.
    """
    if not os.path.exists(os.path.join(repo_path, ".rsgpt")):
        os.makedirs(os.path.join(repo_path, ".rsgpt", "chroma_db"), exist_ok=True)

    last_check_path = os.path.join(repo_path, ".rsgpt", "chroma_db", "last_check")
    last_check_datetime: datetime = datetime.fromisoformat("1970-01-01T00:00:00")
    if os.path.exists(last_check_path):
        with open(last_check_path, "r") as f:
            last_check_datetime = datetime.fromisoformat(f.read())

    repo = Repo(repo_path)
    repo.git.add(A=True)
    repo_file_list = repo.git.ls_files().split("\n")
    modified_files = []

    for file in repo_file_list:
        try:
            file_datetime = datetime.fromtimestamp(os.path.getmtime(file))
            if file_datetime > last_check_datetime:
                modified_files.append(file)
        except FileNotFoundError:
            pass

    vector_store = Chroma(
        collection_name="repo",
        embedding_function=OllamaEmbeddings(model="bge-m3"),
        persist_directory=os.path.join(repo_path, ".rsgpt", "chroma_db"),
    )

    extention_to_language = {
        ".py": Language.PYTHON,
        ".js": Language.JS,
        ".html": Language.HTML,
        ".md": Language.MARKDOWN,
        ".cpp": Language.CPP,
        ".hpp": Language.CPP,
    }

    old_documents = vector_store.get()
    for index in range(len(old_documents["ids"])):
        old_file_path = old_documents["metadatas"][index]["file_path"]
        if old_file_path in modified_files or old_file_path not in repo_file_list:
            vector_store.delete(old_documents["ids"][index])

    for file_path in modified_files:
        print(f"Processing file: {file_path}")
        extention = os.path.splitext(file_path)[1]
        language = extention_to_language.get(extention)
        text_splitter = None
        if language:
            text_splitter = RecursiveCharacterTextSplitter.from_language(
                language=language,
                chunk_size=2000,
                chunk_overlap=200,
            )
        else:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,
                chunk_overlap=200,
            )
        with open(file_path, "r") as f:
            document = Document(page_content=f.read(), id=file_path)

        chunks = text_splitter.split_documents([document])
        chunk_number = 0
        chunk_total = len(chunks) - 1
        for chunk in chunks:
            chunk.metadata = {
                "file_path": file_path,
                "chunk_number": f"{chunk_number}/{chunk_total}",
            }
            vector_store.add_documents([chunk])
            chunk_number += 1

    with open(last_check_path, "w") as f:
        f.write(datetime.now().isoformat())

    return {}
