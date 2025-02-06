from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from ..utils.repository_loader import (
    load_repository as shared_load_repository,
)  # New Import
from ..tools import (
    search_repo_content,
    search_repo_by_path,
    generate_repo_tree,
    execute_command_at_repo_root,
    run_python_test_script,
)
from ..utils.llm import llm_base


class RepoCollector(StateGraph):
    def __init__(self):
        super().__init__(MessagesState)
        self.add_node(self.agent)
        tool_node = ToolNode(
            tools=[
                search_repo_content,
                search_repo_by_path,
                generate_repo_tree,
                execute_command_at_repo_root,
                run_python_test_script,
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
                " You are a helpful AI that collects repository elements necessary for tasks."
                " Your operations are strictly read-only and aimed at collecting information that would allow another agent to perform tasks."
                " Ensure detailed and well-structured data collection without modifying any content.",
            ),
            ("placeholder", "{messages}"),
        ]
    )

    model_with_tools = llm_base.bind_tools(
        [
            search_repo_content,
            search_repo_by_path,
            generate_repo_tree,
            execute_command_at_repo_root,
            run_python_test_script,
        ]
    )

    def load_repository(self, _: MessagesState, config: RunnableConfig) -> dict:
        return shared_load_repository(config["configurable"]["repo_path"])

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
        return END
