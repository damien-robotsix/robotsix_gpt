from pathlib import Path
from pydantic import BaseModel, Field
import subprocess


class RsgptContext(BaseModel):
    git_repo_root: Path | None = Field(
        description="The git repository root path", default=None
    )

    def generate_context(self):
        # Find the git repository root path if the code is run from a git repository
        try:
            self.git_repo_root = Path(
                subprocess.check_output(["git", "rev-parse", "--show-toplevel"])
                .decode("utf-8")
                .strip()
            )
        except subprocess.CalledProcessError:
            self.git_repo_root = None
