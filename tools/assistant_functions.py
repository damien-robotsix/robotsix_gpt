import subprocess
from typing import Optional
from pydantic import BaseModel, Field
import openai

class ShellCommandInput(BaseModel):
    command: str = Field(..., description="The shell command to execute")

class ShellCommandResult(BaseModel):
    return_code: int = Field(..., description="The return code of the shell command")
    stdout: Optional[str] = Field(None, description="Standard output of the shell command")
    stderr: Optional[str] = Field(None, description="Standard error of the shell command")

def execute_shell_command(input_data: ShellCommandInput) -> ShellCommandResult:
    try:
        # Execute the shell command
        result = subprocess.run(input_data.command, shell=True, capture_output=True, text=True)
        # Create the structured output
        return ShellCommandResult(
            return_code=result.returncode,
            stdout=result.stdout if result.stdout else None,
            stderr=result.stderr if result.stderr else None
        )
    except Exception as e:
        return ShellCommandResult(
            return_code=-1,
            stderr=str(e)
        )

execute_shell_command_tool = openai.pydantic_function_tool(ShellCommandInput, description="Execute a shell command assuming the command is run in the repository root directory")