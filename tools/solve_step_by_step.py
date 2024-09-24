import os
import sys
import json
from openai import OpenAI
from assistant_gpt import AssistantGpt

def convert_to_step_by_step(custom_message):
    # Set your OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
    client = OpenAI(api_key=api_key)

    thread_id = client.beta.threads.create().id
    assistant_id = "asst_UeiAkZ9spHYLHayGXAQy7r8S"
    client.beta.threads.messages.create(thread_id=thread_id, content=custom_message, role="user")
    client.beta.threads.runs.create_and_poll(thread_id=thread_id, assistant_id=assistant_id)

    messages = list(client.beta.threads.messages.list(thread_id=thread_id))
    if messages:
        return(messages[0].content[0].text.value)
    else:
        return None

def dump_issue_solver_step(data):
    with open('issue_solver_steps.json', 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <custom_message>")
        sys.exit(1)

    custom_message = sys.argv[1]
    assistant = AssistantGpt(interactive=False)
    assistant.init_from_file("assistant_config.json")
    assistant.create_user_message(custom_message)
    dump_issue_solver_step(convert_to_step_by_step(assistant.get_output()))