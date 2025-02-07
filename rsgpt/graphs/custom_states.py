from langgraph.graph import MessagesState
from langchain_core.messages import AnyMessage


class WorkerState(MessagesState):
    final_messages: list[AnyMessage]
