#!/usr/bin/env python3

import argparse
from assistant_gpt import AssistantGpt


def main():
    """
    Main function to run the assistant with user-defined messages.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run assistant with a custom user message.")
    parser.add_argument('user_message', type=str, nargs='?', default='-', help='The user message to send to the assistant. Use - to read from stdin.')
    parser.add_argument("--interactive", action="store_true", default=True, help="Run in interactive mode.")
    parser.add_argument('--save-thread-id', type=str, help='Path to save the thread id.')
    parser.add_argument('--load-thread-id', type=str, help='Path to load the thread id.')
    parser.add_argument("--no-interactive", dest='interactive', action="store_false", help="Run in non-interactive mode.")
    parser.add_argument("--assistant", type=str, default="main", help="The assistant to use.")
    args = parser.parse_args()

    if args.user_message == '-':
        import sys
        args.user_message = sys.stdin.read().strip()
        args.interactive = False
    thread_id = None
    if args.load_thread_id:
        try:
            with open(args.load_thread_id, 'r') as f:
                thread_id = f.read().strip()
        except FileNotFoundError:
            print(f"File {args.load_thread_id} not found. Proceeding without loading thread id.")

    assistant = AssistantGpt(interactive=args.interactive)
    assistant.init_from_file("assistant_config.json", thread_id=thread_id, assistant_name=args.assistant)
    assistant.create_user_message(args.user_message)
    with open('/tmp/assistant_output.txt', 'w') as f:
        f.write(assistant.get_output() or "No output available")

    if args.save_thread_id:
        with open(args.save_thread_id, 'w') as f:
            f.write(assistant.thread_id)


if __name__ == "__main__":
    main()