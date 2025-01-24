from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
import os
from datetime import datetime
from git import Repo
from ..tools import (
    search_repo_content,
    write_file,
    modify_file_chunk,
    search_repo_by_path,
    generate_repo_tree,
)


class RepoWorker(StateGraph):
    def __init__(self):
        super().__init__(MessagesState)
        self.add_node(self.agent)
        tool_node = ToolNode(
            tools=[
                search_repo_content,
                search_repo_by_path,
                generate_repo_tree,
                write_file,
                modify_file_chunk,
            ]
        )
        self.add_node("tools", tool_node)
        self.add_node(self.load_repository)
        self.add_conditional_edges("agent", self.route_tools, ["tools", END])
        self.add_edge("tools", "agent")
        self.add_edge(START, "load_repository")
        self.add_edge("load_repository", "agent")

    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                " You are a helpful AI that assists developers with the knowledge of the repository content."
                " You must use the tools provided to help the user with their queries."
                " You must solve as much as you can without asking for human input."
                " When you use a tool, only provide the tool call, do not provide other information."
                " When you have completed using the tools, make a comprehensive conclusion to provide "
                "proper feedback to the user.",
            ),
            ("placeholder", "{messages}"),
        ]
    )

    model: ChatOpenAI = ChatOpenAI(model_name="gpt-4o")
    model_with_tools = model.bind_tools(
        [
            search_repo_content,
            search_repo_by_path,
            generate_repo_tree,
            write_file,
            modify_file_chunk,
        ]
    )

    def load_repository(self, _: MessagesState, config: RunnableConfig) -> dict:
        # Checks if .rsgpt directory exists in repo_path, if not, create it
        repo_path = config["configurable"]["repo_path"]
        if not os.path.exists(os.path.join(repo_path, ".rsgpt")):
            os.makedirs(os.path.join(repo_path, ".rsgpt", "chroma_db"), exist_ok=True)
        # Last timestamp where repo was checked is stored in .rsgpt/.last_check
        last_check_path = os.path.join(repo_path, ".rsgpt", "chroma_db", "last_check")
        last_check_datetime: datetime = datetime.fromisoformat("1970-01-01T00:00:00")
        if os.path.exists(last_check_path):
            with open(last_check_path, "r") as f:
                last_check_datetime = datetime.fromisoformat(f.read())
        # Check recursively for all files that have been modified since last check
        repo = Repo(repo_path)
        repo_file_list = repo.git.ls_files().split("\n")
        modified_files = []
        for file in repo_file_list:
            try:
                file_datetime = datetime.fromtimestamp(os.path.getmtime(file))
                if file_datetime > last_check_datetime:
                    modified_files.append(file)
            except FileNotFoundError:
                pass

        # Get the vectorstore
        vector_store = Chroma(
            collection_name="repo",
            embedding_function=OpenAIEmbeddings(),
            persist_directory=os.path.join(repo_path, ".rsgpt", "chroma_db"),
        )

        # Process the modified files
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
            extention = os.path.splitext(file_path)[1]
            language = extention_to_language.get(extention)
            text_splitter = None
            if language:
                text_splitter = RecursiveCharacterTextSplitter.from_language(
                    language=language,
                    chunk_size=1000,
                    chunk_overlap=200,
                )
            else:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                )
            with open(file_path, "r") as f:
                document = Document(page_content=f.read(), id=file_path)

            chunks = text_splitter.split_documents([document])
            chunk_number = 0
            chunk_total = len(chunks)
            for chunk in chunks:
                chunk.metadata = {
                    "file_path": file_path,
                    "chunk_number": f"{chunk_number}/{chunk_total}",
                }
                vector_store.add_documents([chunk])
                chunk_number += 1

        # Update the last check timestamp
        with open(last_check_path, "w") as f:
            f.write(datetime.now().isoformat())

        return {}

    def agent(self, state: MessagesState) -> dict:
        bound = self.prompt | self.model_with_tools
        prediction = bound.invoke(
            {
                "messages": state["messages"],
            }
        )
        return {"messages": [prediction]}

    def route_tools(self, state: MessagesState):
        msg = state["messages"][-1]
        if msg.tool_calls:
            return "tools"

        print("************************************************ REPO WORKER")
        for message in state["messages"]:
            message.pretty_print()
        print("************************************************ END REPO WORKER")
        return END
