from langgraph.graph import MessagesState


class WorkerState(MessagesState):
    final_output: list
