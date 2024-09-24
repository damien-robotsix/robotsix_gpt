import argparse
import os
from openai import OpenAI
from utils import get_assistant_configuration
from assistant_functions import (
    execute_shell_command,
    write_file_content,
    ShellCommandInput,
    FileContentInput
)

def initialize_openai_client():
    """Initialize OpenAI client with API key."""
    api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
    return OpenAI(api_key=api_key)

def create_user_message(client, thread_id, user_message):
    """Create a new user message in the thread."""
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )

def handle_tool_calls(run):
    """Process tool calls and generate outputs."""
    tool_outputs = []

    for tool in run.required_action.submit_tool_outputs.tool_calls:
        print(tool)
        if tool.function.name == "ShellCommandInput":
            argument = ShellCommandInput.model_validate_json(tool.function.arguments)
            output = execute_shell_command(argument)
        elif tool.function.name == "FileContentInput":
            argument = FileContentInput.model_validate_json(tool.function.arguments)
            output = write_file_content(argument)

        tool_outputs.append({"tool_call_id": tool.id, "output": output.model_dump_json()})

    return tool_outputs

def submit_tool_outputs(client, thread_id, run_id, tool_outputs):
    """Submit collected tool outputs to the assistant."""
    try:
        run = client.beta.threads.runs.submit_tool_outputs_and_poll(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )
        print("Tool outputs submitted successfully.")
        return run
    except Exception as e:
        print("Failed to submit tool outputs:", e)
        return None

def prompt_next_action():
    """Prompt the user for the next action."""
    action = input("Enter next message or 'exit' to end: ")
    return action.strip().lower() != "exit", action.strip()

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run assistant with a custom user message.")
    parser.add_argument('user_message', type=str, help='The user message to send to the assistant.')
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode.")
    args = parser.parse_args()

    # Initialize OpenAI client
    client = initialize_openai_client()
    configurations = get_assistant_configuration()
    assistant_id = configurations['assistant_id']

    # Create a new thread
    thread = client.beta.threads.create()
    create_user_message(client, thread.id, args.user_message)

    # Start and poll the run
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Process the run status
    while True:
        if run.status == "completed":
            messages = list(client.beta.threads.messages.list(thread_id=thread.id))
            if messages:
                print(messages[0].content[0].text.value)
            
            if args.interactive:
                continue_with_interaction(client, thread.id, assistant_id)
            break

        if run.status == "requires_action":
            tool_outputs = handle_tool_calls(run)
            if tool_outputs:
                run = submit_tool_outputs(client, thread.id, run.id, tool_outputs)
            else:
                print("No tool outputs to submit.")

        # Check for unexpected run statuses
        elif run.status not in ["requires_action", "completed"]:
            print(f"Run status: {run.status}. Unexpected run status. Exiting.")
            break

def continue_with_interaction(client, thread_id, assistant_id):
    """Handle additional interaction with the user."""
    while True:
        interactive, new_message = prompt_next_action()
        if not interactive:
            break
        
        create_user_message(client, thread_id, new_message)
        run = client.beta.threads.runs.create_and_poll(thread_id=thread_id, assistant_id=assistant_id)

if __name__ == "__main__":
    main()