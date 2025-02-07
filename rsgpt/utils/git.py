import subprocess
from pathlib import Path


def get_repo_root() -> Path | None:
    try:
        return Path(
            subprocess.check_output(["git", "rev-parse", "--show-toplevel"])
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        return None
