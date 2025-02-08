from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.prebuilt import ToolNode
from ..utils.llm import llm_think

class DeeperThinkWorker(StateGraph):
    def __init__(self):
        super().__init__()
        self.add_node("tools", ToolNode(tools=[llm_think]))
        self.add_node(self.deeper_think_agent)
        self.add_edge(START, "deeper_think_agent")
        self.add_edge("tools", "deeper_think_agent")
        self.add_edge("deeper_think_agent", END)

    def deeper_think_agent(self, state):
        response = llm_think.invoke(state["messages"])
        return Command(goto=END, update={"messages": response})