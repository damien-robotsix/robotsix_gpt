import argparse
import os
from openai import OpenAI
from utils import get_assistant_configuration
from assistant_functions import execute_shell_command, ShellCommandInput, FileContentInput, write_file_content

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run assistant with a custom user message.")
    parser.add_argument('user_message', type=str, help='The user message to send to the assistant.')
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode.")
    args = parser.parse_args()
    interactive = args.interactive

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
        content=args.user_message
    )
    status = "new_message"

    # Start and poll the run
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # Loop while the assistant asks for tool execution
    while status != "completed":
        if run.status != "requires_action" and run.status != "completed":
            print(f"Run status: {run.status}")
            print("Unexpected run status. Exiting.")
            break
        # Define the list to store tool outputs
        tool_outputs = []

        # Loop through each tool in the required action section
        if run.status == "requires_action":
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                print(tool)
                if tool.function.name == "ShellCommandInput":
                    argument = ShellCommandInput.model_validate_json(tool.function.arguments)
                    output = execute_shell_command(argument)
                    tool_outputs.append({"tool_call_id": tool.id, "output": output.model_dump_json()})
                if tool.function.name == "FileContentInput":
                    argument = FileContentInput.model_validate_json(tool.function.arguments)
                    output = write_file_content(argument)
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
        status = run.status
        if run.status == "completed":
            messages = list(client.beta.threads.messages.list(
                thread_id=thread.id
            ))
            # Print the last message
            if messages:
                print(messages[0].content[0].text.value)

            if interactive:
                interactive, new_message = prompt_next_action()
                if interactive:
                    status = "new_message"
                    client.beta.threads.messages.create(
                        thread_id=thread.id,
                        role="user",
                        content=new_message
                    )
                    run = client.beta.threads.runs.create_and_poll(
                        thread_id=thread.id,
                        assistant_id=assistant_id
                    )


def prompt_next_action():
    action = input("Enter next message or exit to end: ")
    if action.strip().lower() == "exit":
        return False, None
    else:
        return True, action.strip()

if __name__ == "__main__":
    main()
