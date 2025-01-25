from typing import Annotated
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState
from .specialist_with_memory import SpecialistWithMemory

repo_worker_g = None  # Initialize as None
def initialize_repo_worker():
    global repo_worker_g
    if repo_worker_g is None:
        from .repo_worker import RepoWorker
        repo_worker_g = RepoWorker().compile()

specialist_on_langchain_g = SpecialistWithMemory("langchain").compile()


@tool
def call_worker(
    worker: str,
    fake_user_message: str,
    config: RunnableConfig,
    messages: Annotated[list, InjectedState("messages")],
):
    """Call a worker agent. Will route the messages to the worker agent and return the response.
    You can fake an additional user message to the worker agent by providing the fake_user_message parameter.
    The worker agent will receive the fake_user_message as the last message in the conversation.
    """
    response = None
    input_messages = messages[:-1]
    input_messages.append(("user", fake_user_message))
    if worker == "repo_worker":
        initialize_repo_worker()  # Ensure repo_worker_g is initialized
        response = repo_worker_g.invoke({"messages": input_messages}, config)
    elif worker == "specialist_on_langchain":
        response = specialist_on_langchain_g.invoke(
            {"messages": input_messages}, config
        )
    else:
        return "Worker not found, please choose between 'repo_worker' and 'specialist_on_langchain'"
    return response["messages"][-1].content
