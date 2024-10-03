import os
import sys
import argparse
from openai import OpenAI
from ai_assistant.assistant_functions import master_function_tools


def main(assistant_id):
    """
    Main function to configure the assistant with specified tools.
    """
    # Set your OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: Please set the OpenAI API key as an environment variable.")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)

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
    parser = argparse.ArgumentParser(description="Configure an OpenAI Assistant with specified tools.")
    parser.add_argument("assistant_id", type=str, help="The ID of the assistant to configure.")
    args = parser.parse_args()
    main(args.assistant_id)
