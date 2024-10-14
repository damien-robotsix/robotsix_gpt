import os
from ai_assistant.git import find_git_root, ensure_gitignore_entry

def initialize_assistant():
    """Create a .ai_assistant directory at the root of the repository."""
    git_root = find_git_root(os.getcwd())
    ai_assistant_dir = os.path.join(git_root, '.ai_assistant')

    if not os.path.exists(ai_assistant_dir):
        os.makedirs(ai_assistant_dir)
        print(f"Created directory: {ai_assistant_dir}")
    else:
        print(f"Directory already exists: {ai_assistant_dir}")
    ensure_gitignore_entry(git_root, ".ai_assistant/")


def main():
    initialize_assistant()


if __name__ == "__main__":
    main()
