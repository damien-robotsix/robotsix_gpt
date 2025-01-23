from langgraph.graph import MessagesState, StateGraph, START, END
from .repo_diver import RepoDiverGraph
from .specialist_with_memory import SpecialistWithMemoryGraph
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode
from ..tools import (
    call_worker,
    write_file,
    modify_file_chunk,
    search_repo_by_path,
    generate_repo_tree,
)
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain_core.documents import Document
import os
from datetime import datetime
from git import Repo


class DispatcherState(MessagesState):
    pass


class DispatcherGraph(StateGraph):
    system_prompt: str = (
        "You are a supervisor agent tasked with managing a conversation the following workers agent:\n"
        "repo_diver: Analyze of the current repository\n"
        "specialist_on_langchain: A specialist on LangChain. Does not have access to the repository content. All context must be provided in the conversation.\n"
        "Each worker will perform a task and respond with their results and status."
        "You are responsible of anticipating the workers needs and routing the conversation accordingly.\n"
        "You can also use the other tools provided to help perform the initial query.\n"
        "DO NOT ask for human input unless critical to the task.\n"
        "If the human initial querry is completed, make a short conclusion."
    )

    llm = ChatOpenAI(model_name="gpt-4o")
    llm_with_tools = llm.bind_tools(
        [
            call_worker,
            write_file,
            modify_file_chunk,
            search_repo_by_path,
            generate_repo_tree,
        ]
    )

    repo_diver_g = RepoDiverGraph().compile()
    specialist_on_langchain_g = SpecialistWithMemoryGraph("langchain").compile()

    def __init__(self):
        super().__init__(DispatcherState)
        self.tools = [
            write_file,
            modify_file_chunk,
            search_repo_by_path,
            generate_repo_tree,
        ]
        self.add_node("tools", ToolNode(tools=self.tools))
        self.add_node(self.dispatcher_agent)
        self.add_node(self.repo_diver)
        self.add_node(self.specialist_on_langchain)
        self.add_node(self.load_repository)
        self.add_edge("tools", "dispatcher_agent")
        self.add_edge(START, "load_repository")
        self.add_edge("load_repository", "dispatcher_agent")

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

    def dispatcher_agent(self, state: DispatcherState):
        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + state["messages"]
        print("DISPATCHER")
        for message in state["messages"]:
            message.pretty_print()
        response = self.llm_with_tools.invoke(messages)
        print("DISPATCHER RESPONSE")
        print(response)
        print("END DISPATCHER RESPONSE")
        if response.tool_calls:
            if response.tool_calls[0]["name"] == "call_worker":
                return Command(
                    goto=response.tool_calls[0]["args"]["worker"],
                    update={
                        "messages": [
                            (
                                "assistant",
                                "Calling worker: "
                                + response.tool_calls[0]["args"]["worker"],
                            ),
                            (
                                "user",
                                response.tool_calls[0]["args"]["additional_prompt"],
                            ),
                        ]
                    },
                )
            return Command(
                goto="tools",
                update={
                    "messages": response,
                },
            )
        return Command(goto=END)

    def repo_diver(self, state: DispatcherState, config: RunnableConfig):
        response = self.repo_diver_g.invoke(state, config)
        return Command(
            goto="dispatcher_agent", update={"messages": response["messages"][-1]}
        )

    def specialist_on_langchain(self, state: DispatcherState, config: RunnableConfig):
        response = self.specialist_on_langchain_g.invoke(state, config)
        return Command(
            goto="dispatcher_agent", update={"messages": response["messages"][-1]}
        )
