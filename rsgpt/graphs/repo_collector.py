from langgraph.graph import StateGraph, START, END
from .graphs_common import WorkerState
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
        super().__init__(WorkerState)
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
        self.add_node("handle_final_messages", self.handle_final_messages)
        self.add_conditional_edges(
            "agent", self.route_tools, ["tools", "handle_final_messages"]
        )
        self.add_edge("tools", "agent")
        self.add_edge(START, "load_repository")
        self.add_edge("load_repository", "agent")
        self.add_edge("handle_final_messages", END)

    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                " You are a helpful AI that collects repository elements necessary for tasks."
                " Your operations are strictly read-only and aimed at collecting information that would allow another agent to perform tasks."
                " You can use generate_repo_tree if you are looking for a file. "
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

    def load_repository(self, _: WorkerState, config: RunnableConfig) -> dict:
        return shared_load_repository(config["configurable"]["repo_path"])

    def agent(self, state: WorkerState) -> dict:
        bound = self.prompt | self.model_with_tools
        prediction = bound.invoke(
            {
                "messages": state["messages"],
            }
        )
        return {"messages": [prediction]}

    def route_tools(self, state: WorkerState):
        msg = state["messages"][-1]
        if msg.tool_calls:
            return "tools"
        return "handle_final_messages"

    def handle_final_messages(self, state: WorkerState):
        state["final_messages"] = state["messages"]
        return state
