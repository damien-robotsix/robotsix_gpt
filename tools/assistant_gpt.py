import os
import sys
import json
from typing_extensions import override
from openai import OpenAI, AssistantEventHandler
from assistant_functions import TaskInput
from pydantic import BaseModel


class StepByStepOutput(BaseModel):
    steps: list[str]

class AssistantGpt(AssistantEventHandler):
    def __init__(self, interactive = False):
        super().__init__()
        api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
        self.client = OpenAI(api_key=api_key)
        self.interactive = interactive
        self.assistant_id = ""
        self.completed = False

    def init_assistant(self, assistant_id, thread_id = None):
        self.assistant_id = assistant_id
        self.init_thread(thread_id)

    def init_from_file(self, config_file, reconnect_thread=False):
        """
        Reads the assistant configuration from a JSON file.
        """
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
                self.config_file = config_file
        except FileNotFoundError:
            print(f"Configuration file {config_file} not found.")
            sys.exit(1)
        except KeyError as e:
            print(f"{e} not found in {config_file}.")
            sys.exit(1)
        self.assistant_id = self.config['assistant_id']
        if reconnect_thread:
            self.init_thread(self.config['last_thread_id'])
        else:
            self.init_thread()

    def init_thread(self, thread_id = None):
        if thread_id:
            self.thread_id = thread_id
        else:
            thread = self.client.beta.threads.create()
            self.config['last_thread_id'] = thread.id
            self.thread_id = thread.id
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    @override
    def on_event(self, event):
        self.run_id = event.data.id
        if event.event == 'thread.run.requires_action':
            self.handle_requires_action(event.data)
        if event.event == 'thread.run.completed':
            self.handle_completed()

    def handle_requires_action(self, run):
        """Process tool calls and generate outputs."""
        self.tool_outputs = []
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            print(tool)
            task = TaskInput.model_construct(input_type=tool.function.name, parameters=tool.function.arguments)
            output = task.execute()
            print(output)
            self.tool_outputs.append({"tool_call_id": tool.id, "output": output.model_dump_json()})
        self.submit_tool_outputs()

    def submit_tool_outputs(self):
        with self.client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=self.tool_outputs,
            event_handler=self.create_event_handler(),
        ) as stream:
            stream.until_done()

    def handle_completed(self):
        messages = list(self.client.beta.threads.messages.list(thread_id=self.thread_id))
        if messages:
            print(messages[0].content[0].text.value)
        if self.interactive:
            self.continue_with_interaction()
        else:
            self.completed = True

    def create_user_message(self, user_message, response_format=None):
        message_data = {
            "thread_id": self.thread_id,
            "role": "user",
            "content": user_message,
        }
        if response_format:
            message_data["response_format"] = response_format
        self.client.beta.threads.messages.create(**message_data)
        self.run()

    def continue_with_interaction(self):
        new_message = input("Enter next message or 'exit' to end: ")
        if new_message.strip().lower() == "exit":
            self.interactive = False
            self.completed = True
            return
        else:
            self.create_user_message(new_message)

    def create_event_handler(self):
        new_handler = AssistantGpt(self.interactive)
        new_handler.init_assistant(self.assistant_id, self.thread_id)
        return new_handler

    def run(self):
        with self.client.beta.threads.runs.stream(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                event_handler=self.create_event_handler(),
            ) as stream:
            stream.until_done()