from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import get_buffer_string
from ..tools import save_recall_memory, search_recall_memories, web_search
from ..utils.llm import llm_base
from .custom_states import WorkerState


class SpecialistWithMemoryState(WorkerState):
    recall_memories: list[str]


class SpecialistWithMemory(StateGraph):
    def __init__(self, subject: str):
        super().__init__(SpecialistWithMemoryState)
        self.subject = subject
        self.add_node(self.load_memories)
        self.add_node(self.agent)
        tool_node = ToolNode(tools=[save_recall_memory, web_search]).with_config(
            {"memory_store_path": "/home/robotsix-docker/memory_store"}
        )
        self.add_node("tools", tool_node)
        self.add_node("process_output", self.process_output)
        # Defining edges and routes, ensuring proper ordering and cleanup termination
        self.add_edge(START, "load_memories")
        self.add_edge("load_memories", "agent")
        self.add_conditional_edges(
            "agent", self.route_tools, ["tools", "process_output"]
        )
        self.add_edge("tools", "agent")
        self.add_edge("process_output", END)

    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a specialist on {subject} with memory capabilities and access to"
                " web search. When prompted you can use the web_search tool to find "
                "additional information relative to the current conversation. If you find useful information, you must"
                ' use the "save_recall_memory" tool to store'
                " important details for future reference avoiding the need to"
                " search for the same information multiple times on the web."
                " You must store important details as code examples, definitions,"
                " documentation.\n"
                "## Recall Memories\n"
                "Recall memories are contextually retrieved based on the current"
                " conversation:\n{recall_memories}\n\n"
                "Usage Guidelines:\n"
                "1. Use the web search tool only if you don't have relevants "
                "recall memories\n"
                "2. Actively use memory tool save_recall_memory"
                " to build a comprehensive knowledge base.\n"
                "3. Cross-reference new information with existing memories for"
                " consistency.\n"
                "## Instructions\n"
                " There's no need to explicitly mention your memory capabilities."
                " Instead, seamlessly incorporate your understanding of the user"
                " into your responses. If you"
                " do call tools, all text preceding the tool call is an internal"
                " message. Respond AFTER all tool calling, once you have"
                " confirmation that all the tools you need completed successfully.\n\n",
            ),
            ("placeholder", "{messages}"),
        ]
    )

    model_with_tools = llm_base.bind_tools([save_recall_memory, web_search])

    def process_output(
        self, state: SpecialistWithMemoryState
    ) -> SpecialistWithMemoryState:
        state["final_messages"] = [state["messages"][-1]]
        return state

    def agent(self, state: SpecialistWithMemoryState) -> SpecialistWithMemoryState:
        bound = self.prompt | self.model_with_tools
        recall_memories = (
            "<recall_memories>\n"
            + "\n".join(state["recall_memories"])
            + "\n</recall_memories>"
        )
        prediction = bound.invoke(
            {
                "messages": state["messages"],
                "recall_memories": recall_memories,
                "subject": self.subject,
            }
        )
        return {"messages": [prediction]}

    def load_memories(self, state: SpecialistWithMemoryState, config: RunnableConfig):
        config["configurable"]["memory_store_path"] = (
            "/home/robotsix-docker/memory_store"
        )
        convo_str = get_buffer_string(state["messages"])
        recall_memories = search_recall_memories.invoke(convo_str, config)
        return {
            "recall_memories": recall_memories,
        }

    def route_tools(self, state: SpecialistWithMemoryState):
        msg = state["messages"][-1]
        if msg.tool_calls:
            return "tools"
        return "process_output"
