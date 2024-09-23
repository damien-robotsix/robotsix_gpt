import json
import sys

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
