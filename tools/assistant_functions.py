from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import subprocess
import os
import shutil
import openai

class ShellCommandInput(BaseModel):
    command: str = Field(..., description="The shell command to be executed in the repository root directory")

class CreateFileInput(BaseModel):
    path: str = Field(..., description="The path of the file to create")
    content: str = Field(..., description="The content to write to the file")

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
    input_type: str = Field(..., description="The type of input. E.g. ShellCommandInput, CreateFileInput")
    parameters: Dict[str, Any] = Field(..., description="Parameters needed for the task.")

    def execute(self) -> CommandFeedback:
        try:
            if self.input_type == 'ShellCommandInput':
                shell_input = ShellCommandInput.model_validate_json(self.parameters)
                return self.execute_shell_command(shell_input)
            elif self.input_type == 'CreateFileInput':
                file_input = CreateFileInput.model_validate_json(self.parameters)
                return self.create_file(file_input)
            else:
                return CommandFeedback(
                    return_code=-1,
                    stderr=f"Unsupported task type: {self.input_type}. Supported types are: ShellCommandInput, CreateFileInput"
                )
        except Exception as e:
            return CommandFeedback(return_code=-1, stderr=str(e))

    def backup_repository(self):
        backup_dir = '/tmp/backup_repo'
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree('.', backup_dir, dirs_exist_ok=True)

    def execute_shell_command(self, input_data: ShellCommandInput) -> CommandFeedback:
        print(f"Executing command: {input_data.command}")
        try:
            result = subprocess.run(input_data.command, shell=True, capture_output=True, text=True)
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

    def create_file(self, input_data: CreateFileInput) -> CommandFeedback:
        try:
            print(f"Creating file at path: {input_data.path}")
            # Ensure the directory exists
            os.makedirs(os.path.dirname(input_data.path), exist_ok=True)
            # Write the content to the file
            with open(input_data.path, 'w') as f:
                f.write(input_data.content)
            print(f"File created successfully at {input_data.path}")
            return CommandFeedback(return_code=0)
        except Exception as e:
            print(f"Failed to create file: {e}")
            return CommandFeedback(return_code=-1, stderr=str(e))

repository_function_tools = [
    openai.pydantic_function_tool(ShellCommandInput, description="Execute a shell command"),
    openai.pydantic_function_tool(CreateFileInput, description="Create a file at the specified path with the provided content."),
    openai.pydantic_function_tool(AskAssistant, description="Ask a question to the assistant with the specified ID")
]
