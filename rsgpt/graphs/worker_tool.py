from .repo_worker import RepoWorker
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from .specialist_with_memory import SpecialistWithMemoryGraph


repo_worker_g = RepoWorker().compile()
specialist_on_langchain_g = SpecialistWithMemoryGraph("langchain").compile()


@tool
def call_worker(worker: str, prompt: str, config: RunnableConfig):
    """Call a worker agent."""
    response = None
    if worker == "repo_worker":
        response = repo_worker_g.invoke({"messages": ("user", prompt)}, config)
    elif worker == "specialist_on_langchain":
        response = specialist_on_langchain_g.invoke(
            {"messages": ("user", prompt)}, config
        )
    else:
        return "Worker not found, please choose between 'repo_worker' and 'specialist_on_langchain'"
    return response["messages"][-1].content
