import os
import sys
import json
from typing_extensions import override
from openai import OpenAI, AssistantEventHandler
from assistant_functions import TaskInput, AskAssistant, AssistantResponse
from pydantic import BaseModel

class StepByStepOutput(BaseModel):
    steps: list[str]

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    OKPINK = '\033[95m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'  # End of color

class AssistantGpt(AssistantEventHandler):
    def __init__(self, interactive = False):
        super().__init__()
        api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
        self.client = OpenAI(api_key=api_key)
        self.interactive = interactive
        self.assistant_id = ""
        self.assistant_name = ""
        self.completed = False
        self.config_file = None
        self.slave_assistants = {}
        self.slave_names = {}

    def get_assistant_name(self, assistant_id):
        try:
            assistant_data = self.client.beta.assistants.retrieve(assistant_id)
            self.assistant_name = assistant_data.name
        except Exception as e:
            print(f"Error fetching assistant name: {e}")

    def init_assistant(self, assistant_id, thread_id = None):
        self.assistant_id = assistant_id
        self.get_assistant_name(assistant_id)
        self.init_thread(thread_id)

    def init_from_file(self, config_file):
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
        self.get_assistant_name(self.assistant_id)
        self.init_thread()
        if self.config['slave_assistants']:
            for assistant in self.config['slave_assistants']:
                assistant_data = self.client.beta.assistants.retrieve(assistant['assistant_id'])
                assistant['instructions'] = assistant_data.instructions
            message_data = {
            "thread_id": self.thread_id,
            "role": "user",
            "content": json.dumps(self.config['slave_assistants']),
            }
            self.client.beta.threads.messages.create(**message_data)
            self.create_slave_assistants()

    def init_thread(self, thread_id = None):
        if thread_id:
            self.thread_id = thread_id
        else:
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\n{Colors.OKGREEN}Assistant {self.assistant_name} > {tool_call.type}{Colors.ENDC}", flush=True)
        if tool_call.type == "function":
            print(f"{Colors.OKGREEN}{tool_call.function}{Colors.ENDC}\n", flush=True)

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
            print(f"{Colors.HEADER}Processing function call:{Colors.ENDC}")
            if tool.function.name == "AskAssistant":
                request = AskAssistant.model_validate_json(tool.function.arguments)
                assistant_id = request.assistant_id
                message = request.message
                print(f"{Colors.OKBLUE}Message to {self.slave_names[assistant_id]}:\n {message}{Colors.ENDC}")
                try:
                    slave_assistant = self.slave_assistants[assistant_id]
                    slave_assistant.create_user_message(message)
                    response = AssistantResponse(response=slave_assistant.get_output())
                    print(f"{Colors.OKPINK}Response from self.slave_names[assistant_id]:\n {response.response}{Colors.ENDC}")
                    self.tool_outputs.append({"tool_call_id": tool.id, "output": response.model_dump_json()})
                except KeyError:
                    error_message = f"Assistant {assistant_id} not found. Available assistants: {self.slave_assistants.keys()}"
                    print(f"{Colors.FAIL}{error_message}{Colors.ENDC}")
                    response = AssistantResponse(response=error_message)
                    self.tool_outputs.append({"tool_call_id": tool.id, "output": response.model_dump_json()})
            else:
                task = TaskInput.model_construct(input_type=tool.function.name, parameters=tool.function.arguments)
                output = task.execute()
                print(f"{Colors.OKBLUE}Output: {output.model_dump_json()}{Colors.ENDC}")
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
            print(f"{Colors.OKBLUE}Final Output: {messages[0].content[0].text.value}{Colors.ENDC}")
        if self.interactive:
            self.continue_with_interaction()
        else:
            self.completed = True

    def create_user_message(self, user_message):
        message_data = {
            "thread_id": self.thread_id,
            "role": "user",
            "content": user_message,
        }
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
        new_handler.slave_assistants = self.slave_assistants
        new_handler.slave_names = self.slave_names
        return new_handler

    def create_slave_assistants(self):
        for assistant in self.config['slave_assistants']:
            new_handler = AssistantGpt(False)
            new_handler.init_assistant(assistant['assistant_id'])
            self.slave_assistants[assistant['assistant_id']] = new_handler
            self.slave_names[assistant['assistant_id']] = self.get_assistant_name(assistant['assistant_id'])

    def get_output(self):
        messages = list(self.client.beta.threads.messages.list(thread_id=self.thread_id))
        if messages:
            return messages[0].content[0].text.value
        else:
            return None

    def run(self):
        with self.client.beta.threads.runs.stream(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                event_handler=self.create_event_handler(),
            ) as stream:
            stream.until_done()