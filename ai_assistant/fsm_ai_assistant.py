from openai import OpenAI
import os
from ai_assistant.assistant_functions_fsm import AssistantFSMFunctions
from transitions import Machine
from ai_assistant.assistant_tools import modify_chunk_tool, TaskInput, create_file_tool
import repo_chunker
import update_embedding

class AIAssistantFSM:
    states = ['init', 'waiting_for_user_input', 'processing', 'responding']

    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.assistant_functions = AssistantFSMFunctions(self.client)
        self.machine = Machine(
            model=self, states=AIAssistantFSM.states, initial='init')

        self.machine.add_transition(
            trigger='process_user_request', source='waiting_for_user_input', dest='processing')
        self.machine.add_transition(
            trigger='send_response', source='processing', dest='responding')

    def on_enter_waiting_for_user_input(self):
        user_input = input(">>>: ")
        self.user_input = user_input
        self.process_user_request()

    def on_enter_processing(self):
        response = self.assistant_functions.respond_to_prompt(self.user_input)
        if response.choices[0].finish_reason == 'tool_calls':
            for tool in response.choices[0].message.tool_calls:
                print(tool)
                task = TaskInput.model_construct(
                    input_type=tool.function.name, parameters=tool.function.arguments)
                output = task.execute()
        print(response.choices[0].message.content)

    def on_enter_idle(self):
        print("Returning to idle state.")


if __name__ == "__main__":
    repo_chunker.main()
    update_embedding.main()
    assistant = AIAssistantFSM()
    assistant.begin()
