import argparse
from pathlib import Path
from typing import List
from pydantic import BaseModel, DirectoryPath, ValidationError


class RepoConfigModel(BaseModel):
    repo_path: DirectoryPath


def generate_repo_structure(config: RepoConfigModel) -> str:
    """
    Generates the repository structure as a string.

    :param config: Pydantic model containing the repository path.
    :return: String representation of the repository structure.
    """

    repo_path = config.repo_path.resolve()
    lines = []

    def _traverse(current_path: Path, lines: List[str], prefix: str):
        """
        Recursively traverses the directory and appends to lines.

        :param current_path: Current directory path.
        :param lines: List to accumulate the structure lines.
        :param prefix: String prefix for the current level.
        """
        exclude_dirs = ['.git', 'venv', '__pycache__', 'env']
        try:
            entries = sorted(current_path.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
        except PermissionError:
            lines.append(f"{prefix}[Permission Denied]")
            return

        entries = [e for e in entries if e.name not in exclude_dirs]

        total = len(entries)
        for idx, entry in enumerate(entries):
            connector = "└── " if idx == total - 1 else "├── "
            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if idx == total - 1 else "│   "
                _traverse(entry, lines, prefix + extension)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    _traverse(repo_path, lines, prefix="")
    return "\n".join(lines)


def main():
    # Argument parser to handle command-line arguments
    parser = argparse.ArgumentParser(description="Generate repository structure.")
    parser.add_argument(
        "repo_path",
        type=str,
        help="Path to the repository directory"
    )

    args = parser.parse_args()

    try:
        # Create a RepoConfigModel with the argument passed from the command-line
        repo_config = RepoConfigModel(repo_path=args.repo_path)

        # Generate and print the repository structure
        structure = generate_repo_structure(repo_config)
        print(structure)

    except ValidationError as e:
        print(f"Invalid directory path: {e}")

if __name__ == "__main__":
    main()
