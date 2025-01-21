from typing import Literal, TypedDict
from langgraph.graph import MessagesState, StateGraph, START, END
from .repo_diver import RepoDiverGraph
from .specialist_with_memory import SpecialistWithMemoryGraph
from langchain_anthropic import ChatAnthropic
from langgraph.types import Command


class DispatcherState(MessagesState):
    next: str


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal["repo_diver", "specialist_on_langchain", "FINISH"]


class DispatcherGraph(StateGraph):
    system_prompt: str = (
        "You are a supervisor agent tasked with managing a conversation the following workers agent:\n"
        "repo_diver: Analyze the content of the current repository\n"
        "specialist_on_langchain: A specialist on LangChain\n"
        "Each worker will perform a task and respond with their results and status."
        "If the human initial querry is completed, respond with FINISH."
    )

    llm = ChatAnthropic(model="claude-3-5-sonnet-latest")

    repo_diver_g = RepoDiverGraph().compile()
    specialist_on_langchain_g = SpecialistWithMemoryGraph("langchain").compile()

    def __init__(self):
        super().__init__(DispatcherState)
        self.tools = [self.repo_diver]
        self.add_node(self.dispatcher_agent)
        self.add_node(self.repo_diver)
        self.add_node(self.specialist_on_langchain)
        self.add_edge(START, "dispatcher_agent")

    def dispatcher_agent(self, state: DispatcherState):
        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + state["messages"]
        print("DISPATCHER")
        for message in state["messages"]:
            message.pretty_print()
        response = self.llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END
        return Command(
            goto=goto,
            update={"next": goto, "messages": [("assistant", f"Calling {goto}")]},
        )

    def repo_diver(self, state: DispatcherState):
        response = self.repo_diver_g.invoke(state)
        return Command(
            goto="dispatcher_agent", update={"messages": response["messages"][-1]}
        )

    def specialist_on_langchain(self, state: DispatcherState):
        response = self.specialist_on_langchain_g.invoke(state)
        return Command(
            goto="dispatcher_agent", update={"messages": response["messages"][-1]}
        )
