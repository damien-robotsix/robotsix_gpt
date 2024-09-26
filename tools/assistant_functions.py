from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Any
import subprocess
import os
import shutil
import openai

class ShellCommandInput(BaseModel):
    command: str = Field(..., description="The shell command to be executed in the repository root directory")

class CreateFileInput(BaseModel):
    path: str = Field(..., description="The path of the file to create")
    content: str = Field(..., description="The content to write to the file")

class ModificationInstruction(BaseModel):
    action: str = Field(..., description="The modification action to perform. Must be one of: insert, delete, replace")
    start_line: int = Field(..., description="The starting line number (1-based index)")
    end_line: Optional[int] = Field(None, description="The ending line number (inclusive) for delete and replace actions")
    content: Optional[str] = Field(None, description="The content to insert or replace")

class ModifyFileInput(BaseModel):
    path: str = Field(..., description="The path of the file to modify")
    modifications: List[ModificationInstruction] = Field(..., description="A list of modification instructions to apply to the file")

class CommandFeedback(BaseModel):
    return_code: int = Field(..., description="The return code of the command. 0 indicates success, non-zero indicates failure.")
    stdout: Optional[str] = None
    stderr: Optional[str] = None

class AskAssistant(BaseModel):
    assistant_id: str = Field(..., description="The ID of the assistant to ask")
    message: str = Field(..., description="The prompt to send to the assistant")

class AssistantResponse(BaseModel):
    response: str = Field(..., description="The response from the assistant")

# New class to load file content
class LoadFileInput(BaseModel):
    path: str = Field(..., description="The path of the file to load")

class TaskInput(BaseModel):
    input_type: str = Field(..., description="The type of input. E.g. ShellCommandInput, CreateFileInput, ModifyFileInput, LoadFileInput")
    parameters: Dict[str, Any] = Field(..., description="Parameters needed for the task.")

    def execute(self) -> CommandFeedback:
        try:
            if self.input_type == 'ShellCommandInput':
                print(self.parameters)
                shell_input = ShellCommandInput.model_validate_json(self.parameters)
                return self.execute_shell_command(shell_input)
            elif self.input_type == 'CreateFileInput':
                file_input = CreateFileInput.model_validate_json(self.parameters)
                return self.create_file(file_input)
            elif self.input_type == 'ModifyFileInput':
                modify_input = ModifyFileInput.model_validate_json(self.parameters)
                return self.modify_file(modify_input)
            elif self.input_type == 'LoadFileInput':
                load_input = LoadFileInput.model_validate_json(self.parameters)
                return self.load_file(load_input)
            else:
                return CommandFeedback(
                    return_code=-1,
                    stderr=f"Unsupported task type: {self.input_type}. Supported types are: ShellCommandInput, CreateFileInput, ModifyFileInput, LoadFileInput"
                )
        except Exception as e:
            return CommandFeedback(return_code=-1, stderr=str(e))

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

    def modify_file(self, input_data: ModifyFileInput) -> CommandFeedback:
        try:
            print(f"Modifying file at path: {input_data.path}")
            if not os.path.exists(input_data.path):
                return CommandFeedback(return_code=-1, stderr=f"File not found: {input_data.path}")

            # Read the file content
            with open(input_data.path, 'r') as f:
                lines = f.readlines()

            # Make a backup copy
            backup_path = input_data.path + '.bak'
            shutil.copyfile(input_data.path, backup_path)
            print(f"Backup created at {backup_path}")

            # Apply modifications in reverse order to avoid line number changes
            for instruction in reversed(input_data.modifications):
                action = instruction.action.lower()
                start_line = instruction.start_line - 1  # Convert to 0-based index

                if action == 'insert':
                    # For insert, end_line is not used
                    if start_line < 0 or start_line > len(lines):
                        return CommandFeedback(return_code=-1, stderr=f"Invalid start_line: {instruction.start_line}")
                    if instruction.content is None:
                        return CommandFeedback(return_code=-1, stderr="Content is required for insert action")
                    content_lines = instruction.content.splitlines(keepends=True)
                    lines[start_line:start_line] = content_lines
                    print(f"Inserted content at line {instruction.start_line}")
                elif action in ['delete', 'replace']:
                    if instruction.end_line is None:
                        return CommandFeedback(return_code=-1, stderr="end_line is required for delete and replace actions")
                    end_line = instruction.end_line - 1
                    if start_line < 0 or start_line >= len(lines):
                        return CommandFeedback(return_code=-1, stderr=f"Invalid start_line: {instruction.start_line}")
                    if end_line < start_line or end_line >= len(lines):
                        return CommandFeedback(return_code=-1, stderr=f"Invalid end_line: {instruction.end_line}")
                    if action == 'delete':
                        del lines[start_line:end_line+1]
                        print(f"Deleted lines from {instruction.start_line} to {instruction.end_line}")
                    elif action == 'replace':
                        if instruction.content is None:
                            return CommandFeedback(return_code=-1, stderr="Content is required for replace action")
                        content_lines = instruction.content.splitlines(keepends=True)
                        lines[start_line:end_line+1] = content_lines
                        print(f"Replaced lines from {instruction.start_line} to {instruction.end_line}")
                else:
                    print(f"Unknown action: {instruction.action}")
                    return CommandFeedback(return_code=-1, stderr=f"Unknown action: {instruction.action}")

            # Write back the modified content
            with open(input_data.path, 'w') as f:
                f.writelines(lines)
            print(f"File modified successfully at {input_data.path}")
            return CommandFeedback(return_code=0)
        except Exception as e:
            print(f"Failed to modify file: {e}")
            return CommandFeedback(return_code=-1, stderr=str(e))

    # New method to load file content
    def load_file(self, input_data: LoadFileInput) -> Any:
        try:
            print(f"Loading file content from path: {input_data.path}")
            if not os.path.exists(input_data.path):
                return CommandFeedback(return_code=-1, stderr=f"File not found: {input_data.path}")
            with open(input_data.path, 'r') as f:
                content = f.read()
            print(f"File content loaded successfully from {input_data.path}")
            return CommandFeedback(return_code=0, stdout=content)
        except Exception as e:
            print(f"Failed to load file: {e}")
            return CommandFeedback(return_code=-1, stderr=str(e))

# Updated repository_function_tools with the new function
repository_function_tools = [
    openai.pydantic_function_tool(ShellCommandInput, description="Execute a shell command"),
    openai.pydantic_function_tool(CreateFileInput, description="Create a file at the specified path with the provided content."),
    openai.pydantic_function_tool(ModifyFileInput, description="Modify a file at the specified path according to the provided instructions."),
    openai.pydantic_function_tool(AskAssistant, description="Ask a question to the assistant with the specified ID"),
    openai.pydantic_function_tool(LoadFileInput, description="Load the content of a file given its path.")
]
