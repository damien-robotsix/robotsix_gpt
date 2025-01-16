import fnmatch
from pathlib import Path


# Check if a path should be ignored using .gitignore rules.
def is_path_ignored(repo_root: Path, path: Path, ignored_paths: list):
    checked_path = path.relative_to(repo_root)
    for ignored_path in ignored_paths:
        if fnmatch.fnmatch(str(checked_path), ignored_path):
            return True
    return False
