import os
import sys
from openai import OpenAI
from utils import get_assistant_configuration
from assistant_functions import master_function_tools

def main():
    """
    Main function to configure the assistant with specified tools.
    """
    # Set your OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
    client = OpenAI(api_key=api_key)

    # Get the assistant configuration
    assistant_configuration = get_assistant_configuration()
    assistant_id = assistant_configuration['main']['assistant_id']

    # Update the assistant by adding tools
    response = client.beta.assistants.update(
        assistant_id=assistant_id,
        tools=[{"type": "code_interpreter"}] + master_function_tools,
    )

    # Optional: Handle the response as needed
    if response.id == assistant_id:
        print(f"Assistant {assistant_id} has been updated successfully.")
    else:
        print("Failed to update the assistant.")
        sys.exit(1)


if __name__ == "__main__":
    main()