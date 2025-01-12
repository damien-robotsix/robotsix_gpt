from pydantic import BaseModel, Field
import subprocess


class ContextVariables(BaseModel):
    git_repo_root: str | None = Field(
        description="The git repository root path", default=None
    )


def generate_context_variables() -> ContextVariables:
    context = ContextVariables()
    # Find the git repository root path if the code is run from a git repository
    try:
        context.git_repo_root = (
            subprocess.check_output(["git", "rev-parse", "--show-toplevel"])
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        context.git_repo_root = None
    return context
