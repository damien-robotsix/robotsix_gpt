from .agent import Agent
from pydantic import BaseModel, Field
from ..litellm_handler import LLMHandler
from typing import override


class FinalUserOutputArgs(BaseModel):
    final_output: str = Field(
        description="The final output to be displayed to the user."
    )


class FinalUserOutput(Agent):
    def __init__(self, llm_handler: LLMHandler, args: FinalUserOutputArgs):
        super().__init__(llm_handler)
        self._final_output: str = args.final_output

    @override
    @classmethod
    def agent_arguments(cls) -> type[BaseModel]:
        return FinalUserOutputArgs

    @override
    @classmethod
    def agent_description(cls) -> str:
        return "This agent outputs the final response to the user."

    @override
    def trigger(self) -> None:
        print(self._final_output)
        return None
