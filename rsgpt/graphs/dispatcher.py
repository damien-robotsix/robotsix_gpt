from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.prebuilt import ToolNode
from .worker_tool import (
    call_worker,
)


class DispatcherState(MessagesState):
    pass


class DispatcherGraph(StateGraph):
    system_prompt: str = (
        "You are a supervisor agent tasked with managing a conversation the following workers agent:\n"
        "repo_worker: Can operate in the current repository.\n"
        "To call a worker, use the call_worker tool.\n"
        "Each worker will perform a task and respond with their results and status."
        "You are responsible of anticipating the workers needs and routing the conversation accordingly.\n"
        "You can also use the other tools provided to help perform the initial query.\n"
        "DO NOT ask for human input unless critical to the task.\n"
        "If the human initial querry is completed, make a short conclusion."
    )

    llm = ChatOpenAI(model_name="gpt-4o")
    llm_with_tools = llm.bind_tools(
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
        print("DISPATCHER INPUT*********************************************")
        for message in state["messages"]:
            message.pretty_print()
        print("END DISPATCHER INPUT*****************************************")
        response = self.llm_with_tools.invoke(messages)
        print("DISPATCHER RESPONSE**************************************")
        response.pretty_print()
        print("END DISPATCHER RESPONSE**********************************")
        if response.tool_calls:
            return Command(goto="tools", update={"messages": response})
        return Command(goto=END, update={"messages": response})
