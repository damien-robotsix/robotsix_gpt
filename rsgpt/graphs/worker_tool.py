from typing import Annotated
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState
from .specialist_with_memory import SpecialistWithMemory
from .repo_worker import RepoWorker

repo_worker_g = RepoWorker().compile()
specialist_on_langchain_g = SpecialistWithMemory("langchain").compile()


@tool
def call_worker(
    worker: str,
    config: RunnableConfig,
    messages: Annotated[list, InjectedState("messages")],
):
    """Call a worker agent. Will route the messages to the worker agent and return the response."""
    response = None
    input_messages = messages[:-1]
    if worker == "repo_worker":
        response = repo_worker_g.invoke({"messages": input_messages}, config)
    elif worker == "specialist_on_langchain":
        response = specialist_on_langchain_g.invoke(
            {"messages": input_messages}, config
        )
    else:
        return "Worker not found, please choose between 'repo_worker' and 'specialist_on_langchain'"
    return response["messages"][-1].content
