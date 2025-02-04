from langchain_openai import ChatOpenAI
from typing import Optional
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage, ToolCall, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json
from os import getenv


class MultiToolCall(BaseModel):
    tool_calls: list[ToolCall] = Field(description="The list of tool calls to make")


class ChatDeepSeek(ChatOpenAI):
    tools: list[BaseTool] = []
    tools_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You can use the following tools: {tool_names}\n"
                "Each tool will perform a task and respond with their results and status. "
                "To call tools, you should provide only the tool calls json schema in the message without any additional information. The schema is provided below.\n"
                "{tool_call_schema}\n"
                "The tool arguments schema for each tool is provided below.\n"
                "{tool_schemas}\n",
            ),
            ("placeholder", "{messages}"),
        ]
    )

    def __init__(self, model_name: str):
        super().__init__(
            openai_api_key=getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            model_name=model_name,
        )

    def bind_tools(self, tools: list[BaseTool]):
        self.tools = tools
        return self

    def invoke(self, input, config: Optional[RunnableConfig] = None):
        tool_schemas = ""
        for tool in self.tools:
            tool_schemas += json.dumps(tool.get_input_jsonschema())
            tool_schemas += "\n"

        messages = []
        try:
            messages = input.messages
        except:
            messages = input

        prompt = self.tools_prompt.invoke(
            {
                "messages": messages,
                "tool_names": [tool.name for tool in self.tools],
                "tool_call_schema": json.dumps(MultiToolCall.schema()),
                "tool_schemas": tool_schemas,
            }
        )
        response = super().invoke(prompt, config)
        response.pretty_print()
        parser = PydanticOutputParser(pydantic_object=MultiToolCall)
        try:
            parsed = parser.parse(response.content)
        except Exception as e:
            parsed = None
        if parsed:
            messages.append(response)
            for tool_call in parsed.tool_calls:
                for tool in self.tools:
                    if tool.name == tool_call["name"]:
                        tool._parse_input(tool_call["args"], tool_call["id"])
                        tool_args = tool_call["args"]
                        tool_response = tool.invoke(tool_args, config)
                        tool_message = ToolMessage(
                            content=tool_response,
                            tool_name=tool.name,
                            tool_call_id=tool_call["id"],
                        )
                        to_human_message = HumanMessage(
                            content=tool_message.model_dump_json(),
                        )
                        to_human_message.pretty_print()
                        messages.append(to_human_message)
            return self.invoke(messages, config)
        else:
            return response


llm_base = ChatDeepSeek(
    model_name="deepseek/deepseek-chat",
)

llm_think = ChatDeepSeek(
    model_name="deepseek/deepseek-r1",
)
