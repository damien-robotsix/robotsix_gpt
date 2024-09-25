from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import subprocess
import openai
import os
import shutil

class ShellCommandInput(BaseModel):
    command: str

class FileContentInput(BaseModel):
    file_path: str = Field(..., description="The path to the file where the content should be written (absolute or relative to the repository root directory)")
    content: str = Field(..., description="The content to be written to the file")
    replace_existing: Optional[bool]

class InsertBlockInput(BaseModel):
    file_path: str = Field(..., description="The path to the file where the content should be written (absolute or relative to the repository root directory)")
    after_content: List[str] = Field(..., description="The block of text (without indentation) after which the new content should be inserted")
    content: str = Field(..., description="The content to be inserted (with indentation)")

class ReplaceBlockInput(BaseModel):
    file_path: str = Field(..., description="The path to the file where the content should be written (absolute or relative to the repository root directory)")
    replaced_block: List[str] = Field(..., description="The block of text (without indentation) to be replaced")
    new_content: str = Field(..., description="The new content to replace the block (with indentation)")

class CommandFeedback(BaseModel):
    return_code: int = Field(..., description="The return code of the command. 0 indicates success, non-zero indicates failure.")
    stdout: Optional[str] = None
    stderr: Optional[str] = None

class TaskInput(BaseModel):
    input_type: str = Field(..., description="The type of input. E.g. ShellCommandInput, FileContentInput, InsertBlockInput, ReplaceBlockInput")
    parameters: Dict[str, Any] = Field(..., description="Parameters needed for the task.")

    def execute(self) -> CommandFeedback:
        try:
            if self.input_type == 'ShellCommandInput':
                shell_input = ShellCommandInput.model_validate_json(self.parameters)
                return self.execute_shell_command(shell_input)
            elif self.input_type == 'FileContentInput':
                file_input = FileContentInput.model_validate_json(self.parameters)
                return self.write_file_content(file_input)
            elif self.input_type == "InsertBlockInput":
                insert_input = InsertBlockInput.model_validate_json(self.parameters)
                return self.insert_block_in_file(insert_input)
            elif self.input_type == 'ReplaceBlockInput':
                modify_input = ReplaceBlockInput.model_validate_json(self.parameters)
                return self.modify_block_in_file(modify_input)
            else:
                return CommandFeedback(
                    return_code=-1,
                    stderr=f"Unsupported task type: {self.input_type}, supported types are: ShellCommandInput, FileContentInput, InsertBlockInput, ReplaceBlockInput"
                )
        except Exception as e:
            return CommandFeedback(return_code=-1, stderr=str(e))

    def backup_file(self, file_path):
        backup_dir = '/tmp/backup'
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy(file_path, os.path.join(backup_dir, os.path.basename(file_path)))

    def get_block_start_end(self, lines, block):
        # All lines in the block should be present consecutively
        block_check = False
        i = 0
        while not block_check:
            block_start = None
            block_end = None
            while i < len(lines):
                if block[0] in lines[i]:
                    block_start = i
                    break
                i += 1
            if block_start is None:
                return None, None
            while i < len(lines):
                if block[-1] in lines[i]:
                    block_end = i
                    break
                i += 1
            if block_end is None:
                return None, None
            block_check = all([block[j] in lines[block_start + j] for j in range(len(block))])
            i += 1
        return block_start, block_end

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
            # Check if the file exists
            if not os.path.exists(input_data.file_path):
                # Create the file if it does not exist
                with open(input_data.file_path, 'w') as f:
                    pass  # Just create an empty file

            # Backup the file before writing content
            self.backup_file(input_data.file_path)

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

    def insert_block_in_file(self, input_data: InsertBlockInput) -> CommandFeedback:
        try:
            # Backup the file before inserting line
            self.backup_file(input_data.file_path)

            with open(input_data.file_path, 'r') as file:
                lines = file.readlines()

            # Find the line number after which the new line should be inserted
            block_start, block_end = self.get_block_start_end(lines, input_data.after_content)
            if block_start is None or block_end is None:
                return CommandFeedback(return_code=-1, stderr="Block not found in file.")
            lines.insert(block_end + 1, input_data.content + '\n')
            with open(input_data.file_path, 'w') as file:
                file.writelines(lines)

            return CommandFeedback(return_code=0, stdout="Line inserted successfully.")
        except Exception as e:
            return CommandFeedback(return_code=-1, stderr=str(e))

    def modify_block_in_file(self, input_data: ReplaceBlockInput) -> CommandFeedback:
        try:
            # Backup the file before modifying line
            self.backup_file(input_data.file_path)

            with open(input_data.file_path, 'r') as file:
                lines = file.readlines()

            block_start, block_end = self.get_block_start_end(lines, input_data.replaced_block)
            if block_start is None or block_end is None:
                return CommandFeedback(return_code=-1, stderr="Block not found in file.")
            lines[block_start:block_end + 1] = [input_data.new_content + '\n']
            with open(input_data.file_path, 'w') as file:
                file.writelines(lines)

            return CommandFeedback(return_code=0, stdout="Line modified successfully.")
        except Exception as e:
            return CommandFeedback(return_code=-1, stderr=str(e))

function_tools = [
    openai.pydantic_function_tool(ShellCommandInput, description="Execute a shell command assuming the command is run in the repository root directory"),
    openai.pydantic_function_tool(FileContentInput, description="Write content to a file. Appends to the file if replace_existing is False otherwise overwrites the file."),
    openai.pydantic_function_tool(InsertBlockInput, description="Insert a string into a file after the specified block of text."),
    openai.pydantic_function_tool(ReplaceBlockInput, description="Replace a consecutive block of text in a file with a new string.")
]
