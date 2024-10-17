# Copyright 2024 Damien Six (six.damien@robotsix.net)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import subprocess
import os
import openai
import re
from ai_assistant.git_utils import find_git_root

GIT_ROOT = find_git_root(os.getcwd())


class ShellCommandInput(BaseModel):
    """
    Represents a shell command input for execution.
    """
    command: str = Field(
        ..., description="The shell command to be executed in the repository root directory")


class LoadFileInput(BaseModel):
    """
    Represents a request to create a new file.
    """
    path: str = Field(..., description="The path of the file to create")
    content: str = Field(..., description="The content to write to the file")


class OverwriteFileInput(BaseModel):
    """
    Represents a request to overwrite an existing file with new content.
    """
    path: str = Field(..., description="The path of the file to overwrite")
    content: str = Field(..., description="The content to write to the file")


class CommandFeedback(BaseModel):
    """
    Represents feedback from executing a command.
    """
    return_code: int = Field(
        ..., description="The return code of the command. 0 indicates success, non-zero indicates failure.")
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class AskAssistant(BaseModel):
    """
    Represents a request to query an assistant.
    """
    assistant_id: str = Field(...,
                              description="The ID of the assistant to ask")
    instance: int = Field(...,
                          description="The instance of the assistant to ask. Default is 0.")
    message: str = Field(...,
                         description="The prompt to send to the assistant")
    additional_context: str = Field(
        None, description="Additional context to provide to the assistant (file content, etc.)")


class CreateNewInstance(BaseModel):
    """
    Represents a request to create a new instance of an assistant.
    """
    assistant_id: str = Field(...,
                              description="The ID of the assistant instance to create")


class AssistantResponse(BaseModel):
    """
    Represents a response from an assistant.
    """
    response: str = Field(..., description="The response from the assistant")


# New class to load file content
class LoadFileInput(BaseModel):
    """
    Represents a request to load the content of a file.
    """
    path: str = Field(..., description="The path of the file to load")


class ModifyChunk(BaseModel):
    """
    Represents a request to modify a chunk of code.
    """
    file_path: str = Field(...,
                           description="The path of the file containing the chunk to modify")
    line_start: int = Field(...,
                            description="The starting line number of the chunk to modify")
    line_end: int = Field(...,
                          description="The ending line number of the chunk to modify")
    content: str = Field(...,
                         description="The new content to replace the chunk with WITHOUT line numbers")


class TaskInput(BaseModel):
    """
    Represents a task input containing the input type and necessary parameters.
    """
    input_type: str = Field(
        ..., description="The type of input. E.g. ShellCommandInput, CreateFile, LoadFileInput")
    parameters: Dict[str, Any] = Field(...,
                                       description="Parameters needed for the task.")

    def execute(self) -> CommandFeedback:
        """
        Executes the task based on the input type.
        """
        try:
            if self.input_type == 'ShellCommandInput':
                # Print the parameters for shell command
                print(self.parameters)
                shell_input = ShellCommandInput.model_validate_json(
                    self.parameters)
                return self.execute_shell_command(shell_input)
            elif self.input_type == 'LoadFileInput':
                load_input = LoadFileInput.model_validate_json(self.parameters)
                return self.load_file(load_input)
            elif self.input_type == 'ModifyChunk':
                modify_input = ModifyChunk.model_validate_json(self.parameters)
                return self.modify_chunk(modify_input)
            else:
                return CommandFeedback(
                    return_code=-1,
                    stderr=f"Unsupported task type: {self.input_type}. Supported types are: ShellCommandInput, CreateFile, LoadFileInput, OverwriteFileInput"
                )
        except Exception as e:
            # Return feedback with error message
            return CommandFeedback(return_code=-1, stderr=str(e))

    def execute_shell_command(self, input_data: ShellCommandInput) -> CommandFeedback:
        """
        Executes a shell command and returns its feedback.
        """
        print(
            f"Executing command: {input_data.command}")  # Print the command to be executed
        try:
            result = subprocess.run(
                input_data.command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Command failed with return code: {result.returncode}")
            if result.stdout:
                print(f"Command output: {result.stdout}")
            if result.stderr:
                print(f"Command error: {result.stderr}")
            return CommandFeedback(
                return_code=result.returncode,
                stdout=result.stdout if result.stdout else None,
                stderr=result.stderr if result.stderr else None
            )
        except Exception as e:
            return CommandFeedback(
                return_code=-1,
                stderr=str(e)
            )

    def load_file(self, input_data: LoadFileInput) -> CommandFeedback:
        """
        Loads the content of a file.
        """
        try:
            # Inform of file loading operation
            print(f"Loading file content from path: {input_data.path}")
            if not os.path.exists(input_data.path):
                return CommandFeedback(return_code=-1, stderr=f"File not found: {input_data.path}")
            with open(input_data.path, 'r') as f:
                lines = f.readlines()
            content = ''.join(lines)
            # Confirm successful loading
            print(f"File content loaded successfully from {input_data.path}")
            return CommandFeedback(return_code=0, stdout=content)
        except Exception as e:
            # Print error if file loading fails
            print(f"Failed to load file: {e}")
            return CommandFeedback(return_code=-1, stderr=str(e))

    def modify_chunk(self, input_data: ModifyChunk) -> CommandFeedback:
        print(f"Modifying chunk in file: {input_data.file_path}")
        file_path = os.path.join(GIT_ROOT, input_data.file_path)
        line_start = input_data.line_start
        line_end = input_data.line_end

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return

        # Read the file content
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Ensure line indices are within bounds
        if line_start < 1 or line_end > len(lines) or line_start > line_end:
            print("Invalid line range specified.")
            return

        # Apply the modification function to the specified chunk
        modified_lines = re.split(r'(\n)', input_data.content)

        # Ensure the modified content ends with a newline
        if modified_lines[-1] != '\n':
            modified_lines.append('\n')

        # Update the file with modified lines
        lines[line_start - 1: line_end] = modified_lines

        # Write back to the file
        with open(file_path, 'w') as file:
            file.writelines(lines)


master_function_tools = [
    openai.pydantic_function_tool(
        ShellCommandInput, description="Execute a shell command"),
    openai.pydantic_function_tool(
        AskAssistant, description="Ask a question to the assistant with the specified ID"),
    openai.pydantic_function_tool(
        CreateNewInstance, description="Create a new instance of the assistant with the specified ID"),
    openai.pydantic_function_tool(
        LoadFileInput, description="Load the content of a file given its path."),
    openai.pydantic_function_tool(
        OverwriteFileInput, description="Overwrite a file at the specified path with the provided content.")
]

modify_chunk_tool = openai.pydantic_function_tool(
    ModifyChunk, description="Modify a chunk of code in a file.")
