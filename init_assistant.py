import os

def initialize_assistant():
    """Create a .ai_assistant directory at the root of the repository."""
    git_root = find_git_root(os.getcwd())
    ai_assistant_dir = os.path.join(git_root, '.ai_assistant')

    if not os.path.exists(ai_assistant_dir):
        os.makedirs(ai_assistant_dir)
        print(f"Created directory: {ai_assistant_dir}")
    else:
        print(f"Directory already exists: {ai_assistant_dir}")

def find_git_root(start_path):
    """Find the root of the git repository."""
    current_path = start_path
    while current_path != os.path.dirname(current_path):
        if os.path.exists(os.path.join(current_path, '.git')):
            return current_path
        current_path = os.path.dirname(current_path)
    raise Exception("Git root not found.")

if __name__ == "__main__":
    initialize_assistant()
