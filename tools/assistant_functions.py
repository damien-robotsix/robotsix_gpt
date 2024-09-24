from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import subprocess
import openai

class ShellCommandInput(BaseModel):
    command: str

class FileContentInput(BaseModel):
    file_path: str
    content: str
    replace_existing: Optional[bool]

class InsertLineInput(BaseModel):
    file_path: str
    line_number: int
    content: str

class ModifyLineInput(BaseModel):
    file_path: str
    line_number: int
    new_content: str

class CommandFeedback(BaseModel):
    return_code: int
    stdout: Optional[str] = None
    stderr: Optional[str] = None

class TaskInput(BaseModel):
    input_type: str = Field(..., description="The type of input. E.g. ShellCommandInput, FileContentInput, InsertLineInput, ModifyLineInput")
    parameters: Dict[str, Any] = Field(..., description="Parameters needed for the task.")

    def execute(self) -> CommandFeedback:
        try:
            if self.input_type == 'ShellCommandInput':
                shell_input = ShellCommandInput.model_validate_json(self.parameters)
                return self.execute_shell_command(shell_input)
            elif self.input_type == 'FileContentInput':
                file_input = FileContentInput.model_validate_json(self.parameters)
                return self.write_file_content(file_input)
            elif self.input_type == 'InsertLineInput':
                insert_input = InsertLineInput.model_validate_json(self.parameters)
                return self.insert_line_in_file(insert_input)
            elif self.input_type == 'ModifyLineInput':
                modify_input = ModifyLineInput.model_validate_json(self.parameters)
                return self.modify_line_in_file(modify_input)
            else:
                return CommandFeedback(
                    return_code=-1,
                    stderr=f"Unsupported task type: {self.input_type}"
                )
        except Exception as e:
            return CommandFeedback(return_code=-1, stderr=str(e))

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

    def write_file_content(self, input_data: FileContentInput) -> CommandFeedback:
        try:
            # If replace_existing is False, append to the file if it exists
            mode = 'a' if not input_data.replace_existing else 'w'

            # Open the file in the appropriate mode (append or write)
            with open(input_data.file_path, mode) as file:
                file.write(input_data.content)
            
            operation = "appended to" if mode == 'a' else "written to"
            return CommandFeedback(
                return_code=0,
                stdout=f"Content {operation} file: {input_data.file_path}"
            )
        except Exception as e:
            return CommandFeedback(
                return_code=-1,
                stderr=str(e)
            )

    def insert_line_in_file(self, input_data: InsertLineInput) -> CommandFeedback:
        try:
            with open(input_data.file_path, 'r') as file:
                lines = file.readlines()

            lines.insert(input_data.line_number - 1, input_data.content + '\n')
            
            with open(input_data.file_path, 'w') as file:
                file.writelines(lines)

            return CommandFeedback(return_code=0, stdout="Line inserted successfully.")
        except Exception as e:
            return CommandFeedback(return_code=-1, stderr=str(e))

    def modify_line_in_file(self, input_data: ModifyLineInput) -> CommandFeedback:
        try:
            with open(input_data.file_path, 'r') as file:
                lines = file.readlines()

            lines[input_data.line_number - 1] = input_data.new_content + '\n'
            
            with open(input_data.file_path, 'w') as file:
                file.writelines(lines)

            return CommandFeedback(return_code=0, stdout="Line modified successfully.")
        except Exception as e:
            return CommandFeedback(return_code=-1, stderr=str(e))

function_tools = [
    openai.pydantic_function_tool(ShellCommandInput, description="Execute a shell command assuming the command is run in the repository root directory"),
    openai.pydantic_function_tool(FileContentInput, description="Write content to a file. If the file exists, the content will be appended to the file unless replace_existing is set to True. You should check the appropriate file path from repo root in repo_structure.txt before using this function."),
    openai.pydantic_function_tool(InsertLineInput, description="Insert a line into a file at a specified line number. You should check the appropriate file path from repo root in repo_structure.txt before using this function."),
    openai.pydantic_function_tool(ModifyLineInput, description="Modify a line in a file at a specified line number. You should check the appropriate file path from repo root in repo_structure.txt before using this function.")
]
