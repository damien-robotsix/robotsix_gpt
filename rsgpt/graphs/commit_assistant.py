from langgraph.graph import StateGraph, START, END
from ..tools import execute_command_at_repo_root
from langchain.prompts import ChatPromptTemplate
from .graphs_common import WorkerState
from ..utils.llm import llm_base


class CommitState(WorkerState):
    git_diff: str
    commit_command: str


class CommitAssistantGraph(StateGraph):
    def __init__(self):
        super().__init__(CommitState)
        self.tools = [execute_command_at_repo_root]
        self.add_node("stage_files", self.stage_files)
        self.add_node("analyze_code_diff", self.analyze_code_diff)
        self.add_node("generate_commit_details", self.generate_commit_details)
        self.add_node("execute_git_commit", self.execute_git_commit)
        self.add_edge(START, "stage_files")
        self.add_edge("stage_files", "analyze_code_diff")
        self.add_edge("analyze_code_diff", "generate_commit_details")
        self.add_edge("generate_commit_details", "execute_git_commit")
        self.add_edge("execute_git_commit", END)

    def stage_files(self, state: CommitState):
        """Stages all changes using git add ."""
        execute_command_at_repo_root.invoke({"command": "git add ."})
        return state

    def analyze_code_diff(self, state: CommitState):
        """Fetches the difference of staged changes."""
        git_diff_output = execute_command_at_repo_root.invoke(
            {"command": "git diff --staged"}
        )
        state["git_diff"] = git_diff_output["stdout"]
        return state

    def generate_commit_details(self, state: CommitState):
        """Uses LangChain LLM to generate commit details from diff."""
        git_diff = state["git_diff"]

        # Set up the LLM and prompt
        llm = llm_base
        commit_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a developer assistant skilled in crafting conventional commit messages.",
                ),
                (
                    "user",
                    "Please generate a conventional commit message based on the following Git diff:\n---\n{git_diff}\n---\n"
                    "Just provide the commit command starting with git commit or nothing if you have nothing to commit. ",
                ),
            ]
        )

        chain = commit_prompt | llm
        state["commit_command"] = chain.invoke({"git_diff": git_diff}).content
        # Remove ```bahsh\n from the start of the command if it exists
        state["commit_command"] = state["commit_command"].replace("```bash\n", "")
        # Remove ``` from the end of the command if it exists
        state["commit_command"] = state["commit_command"].replace("```", "")
        return state

    def execute_git_commit(self, state: CommitState):
        output = execute_command_at_repo_root.invoke(
            {"command": state["commit_command"]}
        )
        print(f"stderr: {output['stderr']}")
        return state
