import argparse
import json
import os

CONFIG_FILE = 'config.json'

def load_configuration():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_configuration(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Run assistant with a custom user message.")
    parser.add_argument('user_message', type=str, help='The user message to send to the assistant.')
    parser.add_argument("--interactive", action="store_true", default=True, help="Run in interactive mode.")
    parser.add_argument("--no-interactive", dest='interactive', action="store_false", help="Run in non-interactive mode.")
    parser.add_argument("--thread-id", type=str, help="The ID of the existing thread to reconnect to.")

    args = parser.parse_args()

    # Load configuration
    config = load_configuration()
    
    # Use thread ID from config if not provided as argument
    thread_id = args.thread_id or config.get('last_thread_id')

    # Initialize OpenAI client
    client = initialize_openai_client()
    configurations = get_assistant_configuration()
    assistant_id = configurations['assistant_id']

    # Check if we need to reconnect to an existing thread
    if thread_id:
        # Verify if the thread_id exists, if necessary
        # Reconnect to the thread
        pass
    else:
        # Create a new thread if no thread ID is provided
        thread = client.beta.threads.create()
        thread_id = thread.id
        create_user_message(client, thread_id, args.user_message)

    # Save the last thread ID to the configuration
    config['last_thread_id'] = thread_id
    save_configuration(config)

    # Start and poll the run
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Existing process continues from here...

if __name__ == "__main__":
    main()
