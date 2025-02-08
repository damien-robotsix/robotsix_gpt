from langgraph.graph import StateGraph, START, END
from .graphs_common import WorkerState
from ..utils.llm import llm_think


class DeeperThinkWorker(StateGraph):
    def __init__(self):
        super().__init__(WorkerState)
        self.add_node(self.deeper_think_agent)
        self.add_node(self.process_output)
        self.add_edge(START, "deeper_think_agent")
        self.add_edge("deeper_think_agent", "process_output")
        self.add_edge("process_output", END)

    def deeper_think_agent(self, state):
        response = llm_think.invoke(state["messages"])
        return {"messages": response}

    def process_output(self, state: WorkerState):
        state["final_messages"] = [state["messages"][-1]]
        return state
