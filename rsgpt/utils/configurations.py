import os
from pydantic import BaseModel, Field
from .context import RsgptContext


class LlmConfig(BaseModel):
    model: str = Field(description="Llm model to use.", default="gpt-4o")


class ChunckerConfig(BaseModel):
    max_chunk_size: int = Field(
        description="Maximum number of tokens in a chunk.", default=500
    )
    ignored_paths: list = Field(
        description="Paths to ignore while chunking.",
        default=[".git", ".rsgpt", ".gitignore"],
    )


class RsgptConfig(BaseModel):
    llm_config: LlmConfig = LlmConfig()
    chuncker_config: ChunckerConfig = ChunckerConfig()

    def load_config(self, context: RsgptContext):
        # Load from $HOME/.config/rsgpt/config.yaml if it exists
        # Then load from the git_repo_root/.rsgpt/config.yaml
        # Finally, load from the default values
        if os.path.exists(os.path.expanduser("~/.config/rsgpt/config.json")):
            input = open(os.path.expanduser("~/.config/rsgpt/config.json"))
            self.model_validate_json(input.read())
        if context.git_repo_root:
            if os.path.exists(f"{context.git_repo_root}/.rsgpt/config.json"):
                input = open(f"{context.git_repo_root}/.rsgpt/config.json")
                self.model_validate_json(input.read())
            # Append the ignored paths from .gitignore to the ChunckerConfig
            if os.path.exists(f"{context.git_repo_root}/.gitignore"):
                with open(f"{context.git_repo_root}/.gitignore") as f:
                    self.chuncker_config.ignored_paths.extend(f.readlines())
