#!/usr/bin/env python3

import argparse
from assistant_gpt import AssistantGpt

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run assistant with a custom user message.")
    parser.add_argument('user_message', type=str, help='The user message to send to the assistant.')
    parser.add_argument("--interactive", action="store_true", default=True, help="Run in interactive mode.")
    parser.add_argument("--no-interactive", dest='interactive', action="store_false", help="Run in non-interactive mode.")
    args = parser.parse_args()

    # Initialize the assistant
    assistant = AssistantGpt(interactive=args.interactive)
    assistant.init_from_file("assistant_config.json")
    assistant.create_user_message(args.user_message)

if __name__ == "__main__":
    main()