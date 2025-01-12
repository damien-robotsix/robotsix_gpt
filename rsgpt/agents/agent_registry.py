from .agent import Agent
from .file_creator import FileCreator
from .file_loader import FileLoader
from .final_user_output import FinalUserOutput
from .command_executor import CommandExecutor

all_agents: dict[str, type[Agent]] = {
    "FileCreator": FileCreator,
    "FileLoader": FileLoader,
    "FinalUserOutput": FinalUserOutput,
    "CommandExecutor": CommandExecutor,
}

__all__ = ["FileCreator", "FileLoader", "FinalUserOutput", "CommandExecutor"]
