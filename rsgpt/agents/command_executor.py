import subprocess
from .agent import Agent
from ..litellm_handler import LLMHandler
from pydantic import BaseModel, Field
from typing import override


class CommandExecutorArgs(BaseModel):
    command: str = Field(
        ..., description="The command to be executed in the Linux environment."
    )


class CommandExecutor(Agent):
    def __init__(self, llm_handler: LLMHandler, args: CommandExecutorArgs):
        super().__init__(llm_handler)
        self._command: str = args.command

    @override
    @classmethod
    def agent_arguments(cls) -> None | type[BaseModel]:
        return CommandExecutorArgs

    @override
    @classmethod
    def agent_description(cls) -> str:
        return "This agent executes a command in a Linux environment."

    @override
    def trigger(self) -> list[dict[str, str]]:
        try:
            result = subprocess.run(
                self._command, shell=True, capture_output=True, text=True
            )
            return [
                {
                    "role": "assistant",
                    "content": "Command executed. Output: " + result.stdout,
                }
            ]
        except Exception as e:
            return [
                {"role": "assistant", "content": "Error executing command: " + str(e)}
            ]

