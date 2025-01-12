from pathlib import Path
from .agent import Agent
from rsgpt.utils.litellm_handler import LLMHandler
from pydantic import BaseModel, Field
from typing import override


class FileCreatorArgs(BaseModel):
    prompt: str = Field(description="The prompt to be sent to the agent")
    file_type: str = Field(
        ..., description="The type of file to be created, such as '.txt' or '.py'."
    )
    file_path: Path = Field(
        ..., description="The complete file path where the file will be created."
    )


class FileCreatorOutput(BaseModel):
    create_file: bool = Field(description="True if the file should be created")
    file_content: str = Field(description="The content of the file to be created")
    additional_info: str = Field(
        description="Additional information if the file should not be created"
    )


class FileCreator(Agent):
    def __init__(self, llm_handler: LLMHandler, args: FileCreatorArgs):
        super().__init__(llm_handler)
        self._system_prompt: str = (
            "You are a specialist in creating "
            + args.file_type
            + " files. Please provide the file content only."
            + " You MUST NOT include any markdown formatting."
            + " When asked to create a file, provide the file content.\n"
        )
        self._file_path: Path = args.file_path
        self._user_prompt: str = args.prompt
        print("FileCreator initialized with file path:", self._file_path)

    @override
    @classmethod
    def agent_arguments(cls) -> None | type[BaseModel]:
        """
        Return the Pydantic model for the FileCreateParams class.
        :return: The Pydantic model for the FileCreateParams class.
        """
        return FileCreatorArgs

    @override
    @classmethod
    def agent_description(cls) -> str:
        """
        Return a description of the agent.
        :return: A string describing the agent.
        """
        return "This agent creates a file with the provided content."

    @override
    def trigger(self) -> list[dict[str, str]] | None:
        """
        Trigger the file creation process based on the LLM's response.
        :param prompt: Prompt content for the LLM to process.
        :return: A string message indicating the outcome of the operation.
        """
        # Interacts with the LLM handler to get a response
        input_messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": self._user_prompt},
        ]
        response = self._llm_handler.get_answer(input_messages, FileCreatorOutput)
        assert response is not None
        response_pydantic = FileCreatorOutput.model_validate_json(response)
        if response_pydantic.create_file:
            # Write content to the provided file path
            try:
                with open(self._file_path, "w") as file:
                    success = file.write(response_pydantic.file_content)
            except Exception as e:
                return [
                    {
                        "role": "assistant",
                        "content": "Error occurred while writing to the file: "
                        + str(e),
                    }
                ]

            if not success:
                return [
                    {
                        "role": "assistant",
                        "content": "Error occurred while writing to the file.",
                    }
                ]
            print("File created successfully.")
            return None
        else:
            return [
                {
                    "role": "assistant",
                    "content": response_pydantic.additional_info,
                }
            ]
