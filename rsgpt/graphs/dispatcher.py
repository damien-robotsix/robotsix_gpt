from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command
from langgraph.prebuilt import ToolNode
from ..tools import (
    call_worker,
)
from ..utils.llm import llm_base


class DispatcherState(MessagesState):
    pass


class DispatcherGraph(StateGraph):
    system_prompt: str = (
        "You are a supervisor agent tasked with managing a conversation the following workers agent:\n"
        "repo_collector: Can collect information from the current repository.\n"
        "repo_worker: Can operate in the current repository.\n"
        "deeper_think_worker: Can provide deeper insights on the conversation.\n"
        "specialist_on_langchain: Can provide help on langchain framework usage.\n"
        "Proceed step by step, ensuring that the workers are called in the correct order.\n"
        "To call a worker, use the call_worker tool.\n"
        "Each worker will perform a task and respond with their results and status."
        "You are responsible for anticipating the workers needs and routing the conversation accordingly.\n"
        "DO NOT ask for human input unless critical to the task.\n"
        "If the human initial querry is completed, make a short conclusion."
    )

    llm_with_tools = llm_base.bind_tools(
        [
            call_worker,
        ]
    )

    def __init__(self):
        super().__init__(DispatcherState)
        self.tools = [call_worker]
        self.add_node("tools", ToolNode(tools=self.tools))
        self.add_node(self.dispatcher_agent)
        self.add_edge(START, "dispatcher_agent")
        self.add_edge("tools", "dispatcher_agent")

    def dispatcher_agent(self, state: DispatcherState):
        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + state["messages"]
        response = self.llm_with_tools.invoke(messages)
        if response.tool_calls:
            return Command(goto="tools", update={"messages": response})
        return Command(goto=END, update={"messages": response})
