import os
import json
import openai
import argparse

api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
openai.api_key = api_key
client = openai.OpenAI(api_key=api_key)

def get_assistant_configuration(assistant_id):
    """
    Fetches and returns the assistant configuration by ID.
    """
    try:
        assistant = client.beta.assistants.retrieve(assistant_id)
        return assistant.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def main(output_file):
    """
    Dumps the configuration of all assistants into a specified file.
    """
    with open('assistant_config.json', 'r') as f:
        config = json.load(f)

    assistants = []
    for key in config:
        item = config[key]
        if isinstance(item, dict) and "assistant_id" in item:
            assistants.append(item)
        elif isinstance(item, list):
            assistants.extend(a for a in item if "assistant_id" in a)

    all_assistant_configs = {}
    for assistant in assistants:
        assistant_id = assistant["assistant_id"]
        assistant_config = get_assistant_configuration(assistant_id)
        all_assistant_configs[assistant_id] = assistant_config

    with open(output_file, 'w') as f:
        json.dump(all_assistant_configs, f, indent=4)

    print(f"Assistant configurations have been dumped into {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dump assistant configurations to a file.')
    parser.add_argument('output_file', nargs='?', default='output.json', help='The file to write the assistant configurations to')
    args = parser.parse_args()
    main(args.output_file)