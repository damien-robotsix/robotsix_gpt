import os
import sys
from openai import OpenAI
from utils import get_repo_assistant_configuration
from assistant_functions import repository_function_tools

def main():
    # Set your OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
    client = OpenAI(api_key=api_key)

    # Get the assistant configuration
    assistant_configuration = get_repo_assistant_configuration("repo_assistant_config.json")
    assistant_id = assistant_configuration['assistant_id']


    # Update the assistant by adding tools
    response = client.beta.assistants.update(
        assistant_id=assistant_id,
        tools=[{"type": "code_interpreter"}] + repository_function_tools,
    )

    # Optional: Handle the response as needed
    if response.id == assistant_id:
        print(f"Assistant {assistant_id} has been updated successfully.")
    else:
        print("Failed to update the assistant.")
        sys.exit(1)

if __name__ == "__main__":
    main()
