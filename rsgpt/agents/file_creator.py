from pathlib import Path
from .agent import Agent
from ..litellm_handler import LLMHandler
from pydantic import BaseModel, Field
from typing import override


class FileCreatorArgs(BaseModel):
    """
    This Pydantic class contains configuration parameters for file creation.
    """

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
        """
        Initialize the FileCreator with specific parameters.
        :param llm_handler: An instance of the LLMHandler class.
        :param params: A validated instance of the FileCreateParams Pydantic model.
        """
        super().__init__(llm_handler, args)
        self._system_prompt: str = (
            "You are a specialist in creating "
            + args.file_type
            + " files. Please provide the file content only."
            + " You MUST NOT include any markdown formatting."
            + " When asked to create a file, provide the file content.\n"
        )
        self._file_path: Path = args.file_path

    @override
    @classmethod
    def agent_arguments(cls) -> None | type[BaseModel]:
        """
        Return the Pydantic model for the FileCreateParams class.
        :return: The Pydantic model for the FileCreateParams class.
        """
        return FileCreatorArgs

    @override
    def trigger(self, prompt: str) -> str:
        """
        Trigger the file creation process based on the LLM's response.
        :param prompt: Prompt content for the LLM to process.
        :return: A string message indicating the outcome of the operation.
        """
        # Interacts with the LLM handler to get a response
        response = self._llm_handler.get_answer(
            self._system_prompt + prompt, FileCreatorOutput
        )
        assert response is not None
        response_pydantic = FileCreatorOutput.model_validate_json(response)
        if response_pydantic.create_file:
            # Write content to the provided file path
            with open(self._file_path, "w") as file:
                success = file.write(response_pydantic.file_content)

            if not success:
                return "Failed to create file."
            return "File created successfully."
        else:
            return response_pydantic.additional_info
