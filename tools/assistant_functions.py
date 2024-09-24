import subprocess
from typing import Optional
from pydantic import BaseModel, Field
import openai


class CommandFeedback(BaseModel):
    return_code: int
    stdout: Optional[str] = None
    stderr: Optional[str] = None

class ShellCommandInput(BaseModel):
    command: str = Field(..., description="The shell command to execute")


def execute_shell_command(input_data: ShellCommandInput) -> CommandFeedback:
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

class FileContentInput(BaseModel):
    file_path: str = Field(..., description="The path to the file to write the content to")
    content: str = Field(..., description="The content to write to the file")

def write_file_content(input_data: FileContentInput) -> CommandFeedback:
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


execute_shell_command_tool = openai.pydantic_function_tool(ShellCommandInput, description="Execute a shell command assuming the command is run in the repository root directory")
write_file_content_tool = openai.pydantic_function_tool(FileContentInput, description="Write content to a file, replacing the existing content if the file already exists")