from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from ..tools import (
    search_repo_content,
    search_repo_by_path,
    generate_repo_tree,
)


class RepoDiverGraph(StateGraph):
    def __init__(self):
        super().__init__(MessagesState)
        self.add_node(self.agent)
        tool_node = ToolNode(
            tools=[
                search_repo_content,
                search_repo_by_path,
                generate_repo_tree,
            ]
        )
        self.add_node("tools", tool_node)
        self.add_conditional_edges("agent", self.route_tools, ["tools", END])
        self.add_edge("tools", "agent")
        self.add_edge(START, "agent")

    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                " You are a helpful AI that assists developers with the knowledge of the repository content."
                " You can analyze the repository content to help solving the user querry.",
            ),
            ("placeholder", "{messages}"),
        ]
    )

    model: ChatOpenAI = ChatOpenAI(model_name="gpt-4o")
    model_with_tools = model.bind_tools(
        [
            search_repo_content,
            search_repo_by_path,
            generate_repo_tree,
        ]
    )

    def agent(self, state: MessagesState) -> dict:
        bound = self.prompt | self.model_with_tools
        prediction = bound.invoke(
            {
                "messages": state["messages"],
            }
        )
        return {"messages": [prediction]}

    def route_tools(self, state: MessagesState):
        msg = state["messages"][-1]
        if msg.tool_calls:
            return "tools"

        print("REPO DIVER")
        for message in state["messages"]:
            message.pretty_print()
        return END
