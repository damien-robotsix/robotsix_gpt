from langchain_openai import ChatOpenAI
from typing import Optional
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage, SystemMessage, ToolCall, ToolMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json
from os import getenv


class MultiToolCall(BaseModel):
    tool_calls: list[ToolCall] = Field(description="The list of tool calls to make")


class ChatDeepSeek(ChatOpenAI):
    tools: list[BaseTool] = []

    def __init__(self, model_name: str):
        super().__init__(
            openai_api_key=getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            model_name=model_name,
        )

    def bind_tools(self, tools: list[BaseTool]):
        self.tools = tools

    def invoke(self, input: list[BaseMessage], config: Optional[RunnableConfig] = None):
        tool_prompt = f"You can use the following tools: {', '.join([tool.name for tool in self.tools])} \n"
        tool_prompt += (
            "Each tool will perform a task and respond with their results and status. "
            "To call tools, you should provide only the tool calls json schema in the message without any additional information. The schema is provided below.\n"
        )
        tool_prompt += json.dumps(MultiToolCall.schema())
        tool_prompt += "\n"
        tool_prompt += "The tool arguments schema for each tool is provided below.\n"
        for tool in self.tools:
            tool_prompt += json.dumps(tool.get_input_jsonschema())
            tool_prompt += "\n"
        input.append(SystemMessage(content=tool_prompt))
        response = super().invoke(input, config)
        response.pretty_print()
        parser = PydanticOutputParser(pydantic_object=MultiToolCall)
        try:
            parsed = parser.parse(response.content)
        except Exception as e:
            parsed = None
        if parsed:
            input.append(response)
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
                        tool_message.pretty_print()
                        input.append(tool_message)
            self.invoke(input, config)
        else:
            return response


llm_base = ChatDeepSeek(
    model_name="deepseek/deepseek-chat",
)

llm_think = ChatDeepSeek(
    model_name="deepseek/deepseek-r1",
)
