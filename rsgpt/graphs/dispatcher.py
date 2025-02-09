from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode
from ..tools import call_worker, execute_command_at_repo_root
from ..utils.llm import llm_base


class DispatcherState(MessagesState):
    pass


class DispatcherGraph(StateGraph):
    system_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [
            (
                "You are a supervisor agent tasked with managing a conversation the following workers agent:\n"
                "repo_collector: Can collect information from the current repository.\n"
                "repo_worker: Can operate in the current repository.\n"
                "deeper_think_worker: Can provide deeper insights on the conversation.\n"
                "specialist: Can provide help on {specialist}.\n"
                "Proceed step by step, ensuring that the workers are called in the correct order.\n"
                "To call a worker, use the call_worker tool.\n"
                "Each worker will perform a task and respond with their results and status."
                "You are responsible for anticipating the workers needs and routing the conversation accordingly.\n"
                "DO NOT ask for human input unless critical to the task.\n"
                "If the human initial querry is completed, make a short conclusion."
            ),
            ("placeholder", "{messages}"),
        ]
    )

    llm_with_tools = llm_base.bind_tools([call_worker, execute_command_at_repo_root])

    def __init__(self):
        super().__init__(DispatcherState)
        self.tools = [call_worker]
        self.add_node("tools", ToolNode(tools=self.tools))
        self.add_node(self.dispatcher_agent)
        self.add_edge(START, "dispatcher_agent")
        self.add_edge("tools", "dispatcher_agent")

    def dispatcher_agent(self, state: DispatcherState, config: RunnableConfig):
        bound = self.system_prompt | self.llm_with_tools
        response = bound.invoke(
            {
                "messages": state["messages"],
                "specialist": config["configurable"]["specialist_subject"],
            }
        )
        if response.tool_calls:
            return Command(goto="tools", update={"messages": response})
        return Command(goto=END, update={"messages": response})
