import openai
import json
import os


api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
openai.api_key = api_key

# Assuming OpenAI library's default usage
client = openai.OpenAI(api_key=api_key)


# Load config file
with open('assistant_config.json', 'r') as f:
    config = json.load(f)
master_assistant_id = config["assistant_id"]


def get_assistant_configuration(assistant_id):
    try:
        # Retrieve the assistant configuration
        assistant = client.beta.assistants.retrieve(assistant_id)
        return assistant.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

master_config = get_assistant_configuration(master_assistant_id)

slave_configs = []
for slave in config["slave_assistants"]:
    slave_config = get_assistant_configuration(slave["assistant_id"])
    slave_configs.append(slave_config)

full_configuration = {"master": master_config, "slaves": slave_configs}

# Write full configuration to output.json
with open('output.json', 'w') as f:
    json.dump(full_configuration, f, indent=4)

print("Assistant configurations have been dumped into output.json")
