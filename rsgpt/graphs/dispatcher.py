from langgraph.graph import MessagesState, StateGraph, START, END
from .repo_worker import RepoWorker
from .specialist_with_memory import SpecialistWithMemoryGraph
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode
from ..tools import (
    call_worker,
)


class DispatcherState(MessagesState):
    pass


class DispatcherGraph(StateGraph):
    system_prompt: str = (
        "You are a supervisor agent tasked with managing a conversation the following workers agent:\n"
        "repo_worker: Can operate in the current repository.\n"
        "specialist_on_langchain: A specialist on LangChain. Does not have access to the repository content. All context must be provided in the prompt.\n"
        "Consider that the workers don't have access to the full conversation history.\n"
        "Hence, you must provide the necessary context for each worker in the prompt.\n"
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

    repo_worker_g = RepoWorker().compile()
    specialist_on_langchain_g = SpecialistWithMemoryGraph("langchain").compile()

    def __init__(self):
        super().__init__(DispatcherState)
        self.tools = []
        self.add_node("tools", ToolNode(tools=self.tools))
        self.add_node(self.dispatcher_agent)
        self.add_node(self.repo_worker)
        self.add_node(self.specialist_on_langchain)
        self.add_edge(START, "dispatcher_agent")
        self.add_edge("tools", "dispatcher_agent")

    def dispatcher_agent(self, state: DispatcherState):
        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + state["messages"]
        print("DISPATCHER")
        for message in state["messages"]:
            message.pretty_print()
        response = self.llm_with_tools.invoke(messages)
        print("DISPATCHER RESPONSE")
        print(response)
        print("END DISPATCHER RESPONSE")
        if response.tool_calls:
            if response.tool_calls[0]["name"] == "call_worker":
                return Command(
                    goto=response.tool_calls[0]["args"]["worker"],
                    update={
                        "messages": [
                            (
                                "assistant",
                                "CALLING WORKER: "
                                + response.tool_calls[0]["args"]["worker"],
                            ),
                            (
                                "assistant",
                                response.tool_calls[0]["args"]["prompt"],
                            ),
                        ]
                    },
                )
            return Command(
                goto="tools",
                update={
                    "messages": response,
                },
            )
        return Command(goto=END, update={"messages": response})

    def repo_worker(self, state: DispatcherState, config: RunnableConfig):
        worker_prompt = state["messages"][-1].content
        response = self.repo_worker_g.invoke(
            {"messages": ("user", worker_prompt)}, config
        )
        response_message = response["messages"][-1].content
        response_message = str("REPO WORKER: \n") + response_message
        return Command(
            goto="dispatcher_agent",
            update={"messages": ("assistant", response_message)},
        )

    def specialist_on_langchain(self, state: DispatcherState, config: RunnableConfig):
        worker_prompt = state["messages"][-1].content
        response = self.specialist_on_langchain_g.invoke(
            {"messages": ("user", worker_prompt)}, config
        )
        response_message = response["messages"][-1].content
        response_message = str("SPECIALIST ON LANGCHAIN: \n") + response_message
        return Command(
            goto="dispatcher_agent",
            update={"messages": ("assistant", response_message)},
        )
