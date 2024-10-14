import git
import os
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

def find_git_root(start_path):
    """Find the closest git root directory from the start_path."""
    try:
        repo = git.Repo(start_path, search_parent_directories=True)
        return repo.git.rev_parse("--show-toplevel")
    except git.exc.InvalidGitRepositoryError:
        raise FileNotFoundError("No git repository found from the current directory upwards.")
    
def load_gitignore(git_root):
    """Load .gitignore patterns using pathspec."""
    gitignore_path = os.path.join(git_root, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            patterns = f.readlines()
            # add .git to the patterns
            patterns.append(".git/")
        spec = PathSpec.from_lines(GitWildMatchPattern, patterns)
        return spec
    else:
        return PathSpec.from_lines(GitWildMatchPattern, [])
    
def ensure_gitignore_entry(git_root, entry=".ai_assistant/"):
    """Ensure that the entry is present in .gitignore."""
    gitignore_path = os.path.join(git_root, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            lines = f.read().splitlines()
        if entry not in lines:
            with open(gitignore_path, 'a') as f:
                f.write(f"\n{entry}\n")
            print(f"Added '{entry}' to .gitignore.")
    else:
        with open(gitignore_path, 'w') as f:
            f.write(f"{entry}\n")
        print(f"Created .gitignore and added '{entry}'.")