import os
import sys
import json
import logging
from typing_extensions import override
from openai import OpenAI, AssistantEventHandler
from assistant_functions import TaskInput, AskAssistant, AssistantResponse

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='assistant_gpt.log',
                    format='%(name)s: %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    OKPINK = '\033[95m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'  # End of color
class AssistantGpt(AssistantEventHandler):
    def __init__(self, interactive=False):
        super().__init__()
        api_key = os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
        self.client = OpenAI(api_key=api_key)
        self.interactive = interactive
        self.assistant_id = ""
        self.assistant_name = ""
        self.completed = False
        self.config_file = None
        self.slave_assistants = {}
        self.main_assistant = False

    def find_git_root(slef, path):
        """Traverse up the directory tree to find the .git folder."""
        previous, current = None, os.path.abspath(path)
        while current != previous:
            if os.path.isdir(os.path.join(current, ".git")):
                return current
            previous, current = current, os.path.abspath(os.path.join(current, os.pardir))
        return None

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
        Also checks if the current directory is a git repository and get the specific assistant for the repository.
        """
        git_root = self.find_git_root(os.getcwd())
        if git_root is None:
            print("Not inside a git repository.")
            sys.exit(1)

        # Check for repo_assistant_config.json in the git root
        repo_config_file = os.path.join(git_root, 'repo_assistant_config.json')

        if not os.path.exists(config_file):
            print(f"Configuration file {config_file} not found.")
            sys.exit(1)

        self.main_assistant = True
        with open(config_file, 'r') as f:
            self.config = json.load(f)
            self.config_file = config_file
        
        # If a repo_config_file exists, complete the slave assistants with the assistant in the file
        if os.path.exists(repo_config_file):
            with open(repo_config_file, 'r') as f:
                repo_config = json.load(f)
                self.config['slave_assistants'].append({'assistant_id':repo_config['repo_assistant_id']})

        self.assistant_id = self.config['assistant_id']
        self.get_assistant_name(self.assistant_id)
        self.init_thread()
        self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content="Current directory: " + os.getcwd()
        )

        logger.debug(f"Message to assistant {self.assistant_name}: Current directory: {os.getcwd()}")
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
            logger.debug(f"Message to assistant {self.assistant_name}: {json.dumps(self.config['slave_assistants'])}")
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
            print(f"{Colors.OKGREEN}Function {tool_call.function.name}{Colors.ENDC}\n", flush=True)

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
            logger.debug(f"Processing tool call: {tool.model_dump_json()}")
            if tool.function.name == "AskAssistant":
                request = AskAssistant.model_validate_json(tool.function.arguments)
                assistant_id = request.assistant_id
                message = request.message
                try:
                    slave_assistant = self.slave_assistants[assistant_id]
                    print(f"{Colors.OKBLUE}Message to {slave_assistant.assistant_name}:\n {message}{Colors.ENDC}")

                    slave_assistant.create_user_message(message)
                    response = AssistantResponse(response=slave_assistant.get_output())
                    print(f"{Colors.OKPINK}Response from {slave_assistant.assistant_name}:\n {response.response}{Colors.ENDC}")
                    self.tool_outputs.append({"tool_call_id": tool.id, "output": response.model_dump_json()})
                except KeyError:
                    error_message = f"Assistant {assistant_id} not found. Available assistants: {self.slave_assistants.keys()}"
                    print(f"{Colors.FAIL}{error_message}{Colors.ENDC}")
                    response = AssistantResponse(response=error_message)
                    self.tool_outputs.append({"tool_call_id": tool.id, "output": response.model_dump_json()})
            else:
                task = TaskInput.model_construct(input_type=tool.function.name, parameters=tool.function.arguments)
                output = task.execute()
                if output.return_code != 0:
                    logger.error(f"Failed to execute {tool.function.name} - Input: {tool.function.arguments}, Error: {output.stderr}")
                    print(f"{Colors.FAIL}Failed to execute {tool.function.name}{Colors.ENDC}")
                self.tool_outputs.append({"tool_call_id": tool.id, "output": output.model_dump_json()})
        logger.debug(f"Submitting tool outputs: {json.dumps(self.tool_outputs)}")
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
        if messages and self.main_assistant:
            print(f"Final Output:\n {messages[0].content[0].text.value}")
            logger.info(f"Final Output:\n {messages[0].content[0].text.value}")
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
        if self.main_assistant:
            logger.debug(f"Creating user message: {message_data}")
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
        new_handler.main_assistant = self.main_assistant
        return new_handler

    def create_slave_assistants(self):
        for assistant in self.config['slave_assistants']:
            new_handler = AssistantGpt(False)
            new_handler.init_assistant(assistant['assistant_id'])
            self.slave_assistants[assistant['assistant_id']] = new_handler

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
