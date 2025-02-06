from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command
from ..tools import (
    call_worker,
)
from ..utils.llm import llm_base
from pydantic import BaseModel, Field


class Steps(BaseModel):
    steps: list[str] = Field(description="Steps to follow to answer the user query")


class DispatcherState(MessagesState):
    steps: Steps


class DispatcherGraph(StateGraph):
    system_prompt: str = (
        "You are a supervisor agent tasked with managing a conversation the following workers agent:\n"
        "repo_worker: Can operate in the current repository.\n"
        "To call a worker, use the call_worker tool.\n"
        "Each worker will perform a task and respond with their results and status."
        "You are responsible for anticipating the workers needs and routing the conversation accordingly.\n"
        "You can also use the other tools provided to help perform the initial query.\n"
        "DO NOT ask for human input unless critical to the task.\n"
        "If the human initial querry is completed, make a short conclusion."
    )
    step_generator_prompt: str = (
        "You are an AI assistant. Your role is to generate a comprehensive step by step approach to the "
        "initial user query. The steps provided must ensure that the user request is fully completed. "
        "If you need additional information on the user request you can prompt the user for it. "
        "You can also use the tools at your disposal. You final output MUST be a json structure as follow:\n"
    )

    llm_with_tools = llm_base.bind_tools(
        [
            call_worker,
        ]
    )

    def __init__(self):
        super().__init__(DispatcherState)
        self.tools = [call_worker]
        self.add_node(self.dispatcher_agent)
        self.add_edge(START, "dispatcher_agent")
        self.add_edge("dispatcher_agent", END)

    def dispatcher_agent(self, state: DispatcherState):
        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + state["messages"]
        response = self.llm_with_tools.invoke(messages)
        return response
