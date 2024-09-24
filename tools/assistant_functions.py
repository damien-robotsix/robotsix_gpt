from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import subprocess
import openai

class ShellCommandInput(BaseModel):
    command: str

class FileContentInput(BaseModel):
    file_path: str
    content: str

class CommandFeedback(BaseModel):
    return_code: int
    stdout: Optional[str] = None
    stderr: Optional[str] = None

class TaskInput(BaseModel):
    input_type: str = Field(..., description="The type of input. E.g. ShellCommandInput, FileContentInput")
    parameters: Dict[str, Any] = Field(..., description="Parameters needed for the task.")

    def execute(self) -> CommandFeedback:
        if self.input_type == 'ShellCommandInput':
            try:
                shell_input = ShellCommandInput.model_validate_json(self.parameters)
                return self.execute_shell_command(shell_input)
            except Exception as e:
                return CommandFeedback(
                    return_code=-1,
                    stderr=str(e)
                )
        elif self.input_type == 'FileContentInput':
            try:
                file_input = FileContentInput.model_validate_json(self.parameters)
                return self.write_file_content(file_input)
            except Exception as e:
                return CommandFeedback(
                    return_code=-1,
                    stderr=str(e)
                )
        else:
            return CommandFeedback(
                return_code=-1,
                stderr=f"Unsupported task type: {self.task_type}"
            )

    def execute_shell_command(self, input_data: ShellCommandInput) -> CommandFeedback:
        try:
            # Execute the shell command
            result = subprocess.run(input_data.command, shell=True, capture_output=True, text=True)
            # Create the structured output
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

    def write_file_content(self, input_data: FileContentInput) -> CommandFeedback:
        try:
            # Write the content to the file
            with open(input_data.file_path, "w") as file:
                file.write(input_data.content)
            # Create the structured output
            return CommandFeedback(
                return_code=0,
                stdout=f"Content written to file: {input_data.file_path}"
            )
        except Exception as e:
            return CommandFeedback(
                return_code=-1,
                stderr=str(e)
            )

function_tools = [
    openai.pydantic_function_tool(ShellCommandInput, description="Execute a shell command assuming the command is run in the repository root directory"),
    openai.pydantic_function_tool(FileContentInput, description="Write content to a file, replacing the existing content if the file already exists")
]