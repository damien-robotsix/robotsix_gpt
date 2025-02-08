from langgraph.graph import StateGraph, START, END
from .graphs_common import WorkerState
from langgraph.prebuilt import ToolNode
from ..utils.repository_loader import (
    load_repository as shared_load_repository,
)  # New Import
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from ..tools import (
    search_repo_content,
    write_file,
    modify_file_chunk,
    search_repo_by_path,
    generate_repo_tree,
    execute_command_at_repo_root,
    run_python_test_script,
    call_worker,
)
from ..utils.llm import llm_base


class RepoWorker(StateGraph):
    def __init__(self):
        super().__init__(WorkerState)
        self.add_node(self.agent)
        tool_node = ToolNode(
            tools=[
                search_repo_content,
                search_repo_by_path,
                generate_repo_tree,
                write_file,
                modify_file_chunk,
                execute_command_at_repo_root,
                run_python_test_script,
                call_worker,
            ]
        )
        self.add_node("tools", tool_node)
        self.add_node(self.load_repository)
        self.add_node("process_output", self.process_output)
        self.add_conditional_edges(
            "agent", self.route_tools, ["tools", "process_output"]
        )
        self.add_edge("tools", "agent")
        self.add_edge(START, "load_repository")
        self.add_edge("load_repository", "agent")
        self.add_edge("process_output", END)

    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                " You are a helpful AI that assists developers with the knowledge of the repository content."
                " You must solve the query in the context of the repository as much as you can without asking for human input."
                " When you have completed your task, make a comprehensive conclusion to provide "
                "proper feedback to the user. "
                "You can call the worker specialist_on_langchain to get help on langchain framework usage. ",
            ),
            ("placeholder", "{messages}"),
        ]
    )

    model_with_tools = llm_base.bind_tools(
        [
            search_repo_content,
            search_repo_by_path,
            generate_repo_tree,
            write_file,
            modify_file_chunk,
            execute_command_at_repo_root,
            run_python_test_script,
            call_worker,
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
        return "process_output"

    def process_output(self, state: WorkerState):
        state["final_messages"] = [state["messages"][-1]]
        return state
