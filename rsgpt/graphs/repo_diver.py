from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain_core.documents import Document
import os
from datetime import datetime


class State(MessagesState):
    recall_memories: list[str]


class RepoDiverGraph(StateGraph):
    def __init__(self):
        super().__init__(State)
        self.add_node(self.load_repository)
        self.add_node(self.agent)
        tool_node = ToolNode(tools=[])
        self.add_node("tools", tool_node)
        self.add_edge(START, "load_repository")
        self.add_edge("load_repository", "agent")
        self.add_conditional_edges("agent", self.route_tools, ["tools", END])
        self.add_edge("tools", "agent")

    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                " \n\n",
            ),
            ("placeholder", "{messages}"),
        ]
    )

    model: ChatAnthropic = ChatAnthropic(model_name="claude-3-5-sonnet-20241022")
    model_with_tools = model.bind_tools([])

    def agent(self, state: State) -> dict:
        bound = self.prompt | self.model_with_tools
        prediction = bound.invoke(
            {
                "messages": state["messages"],
            }
        )
        return {"messages": [prediction]}

    def load_repository(self, _: State, config: RunnableConfig) -> dict:
        # Checks if .rsgpt directory exists in repo_path, if not, create it
        repo_path = config["configurable"]["repo_path"]
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
        # Last timestamp where repo was checked is stored in .rsgpt/.last_check
        last_check_path = os.path.join(repo_path, ".rsgpt", "chroma_db", "last_check")
        last_check_datetime: datetime = datetime.now()
        if os.path.exists(last_check_path):
            with open(last_check_path, "r") as f:
                last_check_datetime = datetime.fromisoformat(f.read())
        # Check recursively for all files that have been modified since last check
        modified_files = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_datetime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_datetime > last_check_datetime:
                    modified_files.append(file_path)
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
            document = Document.parse_file(file_path)
            print(text_splitter.split_documents([document]))
            vector_store.add_documents(text_splitter.split_documents([document]))

        # Update the last check timestamp
        with open(last_check_path, "w") as f:
            f.write(datetime.now().isoformat())

        return {}

    def route_tools(self, state: State):
        msg = state["messages"][-1]
        if msg.tool_calls:
            return "tools"

        return END
