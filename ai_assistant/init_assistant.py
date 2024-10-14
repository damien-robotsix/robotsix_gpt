import os
import json
from ai_assistant.git_utils import find_git_root, ensure_gitignore_entry

CONFIG_FILE_PATH = os.path.join('.ai_assistant', 'config.json')
DEFAULT_CONFIG = {
    'max_tokens': 500,
    'ignore_patterns': ['.git/']
}

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

    config_file_path = os.path.join(git_root, CONFIG_FILE_PATH)
    if not os.path.exists(config_file_path):
        with open(config_file_path, 'w') as config_file:
            json.dump(DEFAULT_CONFIG, config_file, indent=4)
        print(f"Created config file: {config_file_path}")
    else:
        print(f"Config file already exists: {config_file_path}")


def main():
    initialize_assistant()


if __name__ == "__main__":
    main()
