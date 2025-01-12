from pathlib import Path
from .agent import Agent
from rsgpt.utils.litellm_handler import LLMHandler
from pydantic import BaseModel, Field
from typing import override


class FileLoaderArgs(BaseModel):
    file_path: Path = Field(
        ...,
        description="The complete file path from which the file content will be loaded.",
    )


class FileLoader(Agent):
    def __init__(self, llm_handler: LLMHandler, args: FileLoaderArgs):
        super().__init__(llm_handler)
        self._file_path: Path = args.file_path

    @override
    @classmethod
    def agent_arguments(cls) -> None | type[BaseModel]:
        return FileLoaderArgs

    @override
    @classmethod
    def agent_description(cls) -> str:
        return "This agent loads the content of a file."

    @override
    def trigger(self) -> list[dict[str, str]]:
        try:
            with open(self._file_path, "r") as file:
                file_content = file.read()
            return [
                {
                    "role": "assistant",
                    "content": "File "
                    + str(self._file_path)
                    + " content: \n"
                    + file_content,
                }
            ]
        except FileNotFoundError:
            return [
                {
                    "role": "assistant",
                    "content": "File not found at path: " + str(self._file_path),
                }
            ]
