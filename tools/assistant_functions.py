from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import subprocess
import openai
import os
import shutil

class ShellCommandInput(BaseModel):
    command: str = Field(..., description="The shell command to be executed in the repository root directory")

class ReplaceFileContent(BaseModel):
    file_path: str = Field(..., description="The path to the file where the content should be written relative to the repository root directory")
    content: str = Field(..., description="The content to be written to the file")

class CommandFeedback(BaseModel):
    return_code: int = Field(..., description="The return code of the command. 0 indicates success, non-zero indicates failure.")
    stdout: Optional[str] = None
    stderr: Optional[str] = None

class AskAssistant(BaseModel):
    assistant_id: str = Field(..., description="The ID of the assistant to ask")
    message: str = Field(..., description="The prompt to send to the assistant")

class AssistantResponse(BaseModel):
    response: str = Field(..., description="The response from the assistant")

class TaskInput(BaseModel):
    input_type: str = Field(..., description="The type of input. E.g. ShellCommandInput, ReplaceFileContent")
    parameters: Dict[str, Any] = Field(..., description="Parameters needed for the task.")

    def execute(self) -> CommandFeedback:
        try:
            if self.input_type == 'ShellCommandInput':
                shell_input = ShellCommandInput.model_validate_json(self.parameters)
                return self.execute_shell_command(shell_input)
            elif self.input_type == 'ReplaceFileContent':
                file_input = ReplaceFileContent.model_validate_json(self.parameters)
                return self.write_file_content(file_input)
            else:
                return CommandFeedback(
                    return_code=-1,
                    stderr=f"Unsupported task type: {self.input_type}, supported types are: ShellCommandInput, ReplaceFileContent"
                )
        except Exception as e:
            return CommandFeedback(return_code=-1, stderr=str(e))

    def backup_file(self, file_path):
        backup_dir = '/tmp/backup'
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy(file_path, os.path.join(backup_dir, os.path.basename(file_path)))

    def execute_shell_command(self, input_data: ShellCommandInput) -> CommandFeedback:
        try:
            result = subprocess.run(input_data.command, shell=True, capture_output=True, text=True)
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

    def write_file_content(self, input_data: ReplaceFileContent) -> CommandFeedback:
        try:
            # Check if the file exists
            if not os.path.exists(input_data.file_path):
                # Create the file if it does not exist
                with open(input_data.file_path, 'w') as f:
                    pass  # Just create an empty file

            # Backup the file before writing content
            self.backup_file(input_data.file_path)

            # Open the file in the appropriate mode (append or write)
            with open(input_data.file_path, 'w') as file:
                file.write(input_data.content)

            return CommandFeedback(
                return_code=0,
                stdout=f"Content written to file: {input_data.file_path}"
            )
        except Exception as e:
            return CommandFeedback(
                return_code=-1,
                stderr=str(e)
            )

repository_function_tools = [
    openai.pydantic_function_tool(ShellCommandInput, description="Execute a shell command"),
    openai.pydantic_function_tool(ReplaceFileContent, description="Replace the content of a file. The file will be fully overwritten so you should provide the full file. You should check the path to the file before executing this tool."),
    openai.pydantic_function_tool(AskAssistant, description="Ask a question to the assistant with the specified ID")
]
