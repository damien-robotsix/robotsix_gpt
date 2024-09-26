from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import subprocess
import openai
import os
import shutil
import tempfile

class ShellCommandInput(BaseModel):
    command: str = Field(..., description="The shell command to be executed in the repository root directory")

class ApplyGitDiff(BaseModel):
    diff_content: str = Field(..., description="The git diff content to be applied to the repository")

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
    input_type: str = Field(..., description="The type of input. E.g. ShellCommandInput, ApplyGitDiff")
    parameters: Dict[str, Any] = Field(..., description="Parameters needed for the task.")

    def execute(self) -> CommandFeedback:
        try:
            if self.input_type == 'ShellCommandInput':
                shell_input = ShellCommandInput.model_validate_json(self.parameters)
                return self.execute_shell_command(shell_input)
            elif self.input_type == 'ApplyGitDiff':
                diff_input = ApplyGitDiff.model_validate_json(self.parameters)
                return self.apply_git_diff(diff_input)
            else:
                return CommandFeedback(
                    return_code=-1,
                    stderr=f"Unsupported task type: {self.input_type}, supported types are: ShellCommandInput, ApplyGitDiff"
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

    def apply_git_diff(self, input_data: ApplyGitDiff) -> CommandFeedback:
        print("Applying git diff")
        try:
            # Backup the repository before applying the diff
            self.backup_repository()

            # Write the diff content to a temporary file
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_diff_file:
                temp_diff_file.write(input_data.diff_content)
                temp_diff_file_path = temp_diff_file.name

            # Apply the diff using git apply
            result = subprocess.run(['git', 'apply', temp_diff_file_path], capture_output=True, text=True)

            # Clean up the temporary diff file
            os.remove(temp_diff_file_path)

            if result.returncode != 0:
                print(f"git apply failed with return code: {result.returncode}")
                print(f"Error output: {result.stderr}")
            else:
                print("git diff applied successfully.")

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

repository_function_tools = [
    openai.pydantic_function_tool(ShellCommandInput, description="Execute a shell command"),
    openai.pydantic_function_tool(ApplyGitDiff, description="Apply a git diff to modify files in the repository. The diff should be in unified diff format."),
    openai.pydantic_function_tool(AskAssistant, description="Ask a question to the assistant with the specified ID")
]
