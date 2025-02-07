from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from ..tools import execute_command_at_repo_root
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig


class CommitAssistantGraph(StateGraph):
    system_prompt: str = (
        "You are a helpful AI that assists users in committing their current work to a Git repository "
        "using the conventional commit convention. Collect the necessary details (type, scope, and "
        "description), format them appropriately, and execute the commit command."
    )

    def __init__(self):
        super().__init__(MessagesState)
        self.tools = [execute_command_at_repo_root]
        self.add_node("collect_commit_details", self.collect_commit_details)
        self.add_node("execute_git_commit", ToolNode(tools=self.tools))
        self.add_edge(START, "collect_commit_details")
        self.add_edge("collect_commit_details", "execute_git_commit")
        self.add_edge("execute_git_commit", END)

    def collect_commit_details(self, state: MessagesState) -> dict:
        """Simulates user input for commit details."""
        state["commit_type"] = "feat"  # e.g., "fix", "docs", etc.
        state["commit_scope"] = "utils"  # e.g., which module/file this affects.
        state["commit_description"] = "Add helper functions for data processing"
        return state

    def execute_git_commit(self, state: MessagesState, config: RunnableConfig):
        commit_type = state.get("commit_type", "").strip()
        commit_scope = state.get("commit_scope", "").strip()
        commit_description = state.get("commit_description", "").strip()

        if commit_scope:
            formatted_message = f"{commit_type}({commit_scope}): {commit_description}"
        else:
            formatted_message = f"{commit_type}: {commit_description}"

        command = f"git commit -m \"{formatted_message}\""
        return execute_command_at_repo_root({"command": command})