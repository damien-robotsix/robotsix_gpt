import argparse
import os
from openai import OpenAI
from utils import get_assistant_configuration
from assistant_functions import execute_shell_command, ShellCommandInput

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run assistant with a custom user message.")
    parser.add_argument('user_message', type=str, help='The user message to send to the assistant.')
    args = parser.parse_args()

    # Set your OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
    client = OpenAI(api_key=api_key)

    configurations = get_assistant_configuration()
    assistant_id = configurations['assistant_id']

    # Create a new thread
    thread = client.beta.threads.create()

    # Create the initial user message using the command line input
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=args.user_message +
        """
        Use shell commands if possible to complete the task.
        """
    )

    # Start and poll the run
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # Loop while the assistant asks for tool execution
    while run.status != "completed":
        if run.status != "requires_action":
            print(run.status)
            break
        # Define the list to store tool outputs
        tool_outputs = []

        # Loop through each tool in the required action section
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            print(tool)
            if tool.function.name == "ShellCommandInput":
                argument = ShellCommandInput.model_validate_json(tool.function.arguments)
                output = execute_shell_command(argument)
                tool_outputs.append({"tool_call_id": tool.id, "output": output.model_dump_json()})

        # Submit all tool outputs after collecting them
        if tool_outputs:
            try:
                run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                print("Tool outputs submitted successfully.")
            except Exception as e:
                print("Failed to submit tool outputs:", e)
        else:
            print("No tool outputs to submit.")

    # If the run is completed, display the last message
    if run.status == "completed":
        messages = list(client.beta.threads.messages.list(
            thread_id=thread.id
        ))
        # Print the last message
        if messages:
            print(messages[0].content[0].text.value)
    else:
        print("Run did not complete successfully.")
        print("Run status:", run.status)


if __name__ == "__main__":
    main()
