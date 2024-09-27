import json
import sys


def get_repo_assistant_configuration(config_path: str):
    """
    Loads the repository-specific assistant configuration from the specified JSON file
    """
    with open(config_path) as config_file:
        return json.load(config_file)

def get_assistant_configuration(config_file='assistant_config.json'):
    """
    Reads the assistant configuration from a JSON file.
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found.")
        sys.exit(1)
    except KeyError as e:
        print(f"{e} not found in {config_file}.")
        sys.exit(1)

def save_assistant_configuration(config, config_file='assistant_config.json'):
    """
    Saves the assistant configuration to a JSON file.
    """
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
